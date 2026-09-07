import os
import sys
import asyncio
import numpy as np
import torch
import websockets

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml", "encoder"))
from codec_service import CodecService

from packet import build_packet, parse_packet, PACKET_TYPE_AUDIO, PACKET_TYPE_FEC
from fec import xor_bytes, FEC_BLOCK_SIZE

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "datasets"))

CHUNK_TIMESTEPS = 25   # how many timesteps of codes go in ONE packet


async def run_sender():
    codec = CodecService(bandwidth_kbps=6.0)
    audio_path = os.path.join(DATASETS_DIR, "hindi_clip.wav")
    code_bytes, n_codebooks, codes_shape = codec.encode_file(audio_path)

    codes = torch.from_numpy(np.frombuffer(code_bytes, dtype=np.int16).reshape(codes_shape).copy())
    total_timesteps = codes.shape[2]
    print(f"[A] Total codes shape: {tuple(codes.shape)} ({total_timesteps} timesteps)")

    # Slice into chunks along the TIME axis - each chunk keeps shape (1, n_codebooks, CHUNK_TIMESTEPS)
    chunks = []
    for start in range(0, total_timesteps, CHUNK_TIMESTEPS):
        chunk = codes[:, :, start:start + CHUNK_TIMESTEPS]
        # Pad the last chunk (if shorter) to a full CHUNK_TIMESTEPS width with zeros,
        # so every chunk is the SAME byte size - required for FEC's XOR to work correctly.
        if chunk.shape[2] < CHUNK_TIMESTEPS:
            pad_width = CHUNK_TIMESTEPS - chunk.shape[2]
            chunk = torch.nn.functional.pad(chunk, (0, pad_width))
        chunks.append(chunk.numpy().astype(np.int16).tobytes())
    print(f"[A] Split into {len(chunks)} chunks of {CHUNK_TIMESTEPS} timesteps each")

    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("A")
        print("[A] Connected. Sending FEC-protected real audio codes...")

        seq = 0
        block_id = 0
        for i in range(0, len(chunks), FEC_BLOCK_SIZE):
            block_chunks = chunks[i:i + FEC_BLOCK_SIZE]
            while len(block_chunks) < FEC_BLOCK_SIZE:
                block_chunks.append(bytes(len(block_chunks[0])))

            for chunk_bytes in block_chunks:
                pkt = build_packet(PACKET_TYPE_AUDIO, seq, "hi", chunk_bytes, n_codebooks)
                await websocket.send(pkt)
                seq += 1

            parity = xor_bytes(block_chunks)
            parity_pkt = build_packet(PACKET_TYPE_FEC, block_id, "hi", parity, n_codebooks)
            await websocket.send(parity_pkt)

            block_id += 1
            await asyncio.sleep(0.03)

        print(f"[A] Done sending. {block_id} blocks, {seq} data packets.")

        # Send metadata 3x for redundancy - proven necessary earlier (single packet loss
        # of this one message broke reconstruction even though all audio data arrived).
        meta = f"{n_codebooks},{total_timesteps},{len(chunks)}".encode("utf-8")
        for _ in range(3):
            await websocket.send(build_packet(0x03, 9999, "hi", meta))
            await asyncio.sleep(0.02)


async def run_receiver():
    uri = "ws://localhost:8765"
    blocks = {}
    n_codebooks = None
    total_timesteps = None
    num_chunks = None

    async with websockets.connect(uri) as websocket:
        await websocket.send("B")
        print("[B] Connected. Waiting for sender (30s)...")

        first_timeout = 30.0
        gap_timeout = 2.0
        received_any = False

        try:
            while True:
                timeout = first_timeout if not received_any else gap_timeout
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                received_any = True
                parsed = parse_packet(message)

                if parsed["packet_type"] == 0x03:  # metadata message
                    n_codebooks, total_timesteps, num_chunks = map(int, parsed["payload"].decode().split(","))
                    print(f"[B] Metadata received: n_codebooks={n_codebooks}, total_timesteps={total_timesteps}, num_chunks={num_chunks}")
                    break

                if parsed["packet_type"] == PACKET_TYPE_AUDIO:
                    block_id = parsed["seq_num"] // FEC_BLOCK_SIZE
                    slot = parsed["seq_num"] % FEC_BLOCK_SIZE
                else:
                    block_id = parsed["seq_num"]
                    slot = "parity"

                blocks.setdefault(block_id, {})[slot] = parsed["payload"]

        except asyncio.TimeoutError:
            print("[B] Timed out waiting for metadata — proceeding with what we have.")

        if n_codebooks is None:
            print("[B] No metadata received, cannot reconstruct. Aborting.")
            return

        chunk_size_bytes = len(next(iter(blocks[0].values())))
        chunk_timesteps = chunk_size_bytes // (n_codebooks * 2)  # 2 bytes per int16 code
        print(f"[B] Each chunk covers {chunk_timesteps} timesteps ({chunk_size_bytes} bytes)")

        recovered_count = 0
        unrecoverable_count = 0
        all_chunks_bytes = []

        num_blocks = (num_chunks + FEC_BLOCK_SIZE - 1) // FEC_BLOCK_SIZE
        for block_id in range(num_blocks):
            slots = blocks.get(block_id, {})
            data_slots = [slots.get(i) for i in range(FEC_BLOCK_SIZE)]
            missing = [i for i, p in enumerate(data_slots) if p is None]

            if len(missing) == 1 and "parity" in slots:
                known = [p for p in data_slots if p is not None]
                recovered = xor_bytes(known + [slots["parity"]])
                data_slots[missing[0]] = recovered
                recovered_count += 1
            elif len(missing) > 0:
                unrecoverable_count += 1
                zero_chunk = bytes(chunk_size_bytes)
                for m in missing:
                    data_slots[m] = zero_chunk

            all_chunks_bytes.extend(data_slots)

        print(f"[B] Blocks: {num_blocks - recovered_count - unrecoverable_count} clean, "
              f"{recovered_count} FEC-recovered, {unrecoverable_count} unrecoverable (silence-filled)")

        # --- THE FIX: reconstruct each chunk as its own (1, n_codebooks, chunk_timesteps)
        # tensor, then torch.cat along the TIME axis (dim=2) - NOT a flat byte concatenation.
        # This preserves the codebook-major memory layout EnCodec actually expects.
        chunk_tensors = []
        for chunk_bytes in all_chunks_bytes[:num_chunks]:
            arr = np.frombuffer(chunk_bytes, dtype=np.int16).reshape(1, n_codebooks, chunk_timesteps)
            chunk_tensors.append(torch.from_numpy(arr.copy()))

        codes = torch.cat(chunk_tensors, dim=2).long()
        codes = codes[:, :, :total_timesteps]  # trim any end-padding back to the real length

        codec = CodecService(bandwidth_kbps=6.0)
        output_path = os.path.join(DATASETS_DIR, "hindi_clip_via_real_pipeline.wav")
        code_bytes = codes.to(torch.int16).numpy().tobytes()
        codec.decode_to_file(code_bytes, n_codebooks, codes.shape, output_path)
        print(f"[B] Reconstructed audio saved to: {output_path}")


if __name__ == "__main__":
    role = sys.argv[1]
    if role == "A":
        asyncio.run(run_sender())
    else:
        asyncio.run(run_receiver())