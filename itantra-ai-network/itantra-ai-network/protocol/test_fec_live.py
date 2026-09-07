import asyncio
import sys
import websockets
from packet import build_packet, parse_packet, PACKET_TYPE_AUDIO, PACKET_TYPE_FEC
from fec import xor_bytes, FEC_BLOCK_SIZE

NUM_BLOCKS = 10  # 10 blocks x 5 packets (4 data + 1 parity) = 50 packets total


async def run_sender():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("A")
        print("[A] Connected. Sending FEC-protected blocks...")

        for block_id in range(NUM_BLOCKS):
            payloads = [bytes([(block_id * 10 + i) % 256] * 8) for i in range(FEC_BLOCK_SIZE)]

            for i, payload in enumerate(payloads):
                seq_num = block_id * FEC_BLOCK_SIZE + i
                pkt = build_packet(PACKET_TYPE_AUDIO, seq_num, "hi", payload, n_codebooks=8)
                await websocket.send(pkt)

            parity = xor_bytes(payloads)
            parity_pkt = build_packet(PACKET_TYPE_FEC, block_id, "hi", parity, n_codebooks=8)
            await websocket.send(parity_pkt)

            await asyncio.sleep(0.05)

        print("[A] Done sending all blocks.")


async def run_receiver():
    uri = "ws://localhost:8765"
    blocks = {}
    async with websockets.connect(uri) as websocket:
        await websocket.send("B")
        print("[B] Connected. Waiting for sender (you have 30s to start Terminal 3)...")

        total_expected = NUM_BLOCKS * (FEC_BLOCK_SIZE + 1)
        received_count = 0

        first_packet_timeout = 30.0
        gap_timeout = 2.0

        try:
            while received_count < total_expected:
                timeout = first_packet_timeout if received_count == 0 else gap_timeout
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                received_count += 1
                parsed = parse_packet(message)

                if parsed["packet_type"] == PACKET_TYPE_AUDIO:
                    block_id = parsed["seq_num"] // FEC_BLOCK_SIZE
                    slot = parsed["seq_num"] % FEC_BLOCK_SIZE
                else:
                    block_id = parsed["seq_num"]
                    slot = "parity"

                blocks.setdefault(block_id, {})[slot] = parsed["payload"]

        except asyncio.TimeoutError:
            print("[B] No more packets arriving — treating as end of stream.\n")

        # --- Reconstruct every block, recovering losses where possible ---
        recovered_count = 0
        unrecoverable_count = 0

        for block_id in range(NUM_BLOCKS):
            slots = blocks.get(block_id, {})
            data_slots = [slots.get(i) for i in range(FEC_BLOCK_SIZE)]
            missing = [i for i, p in enumerate(data_slots) if p is None]

            if len(missing) == 0:
                status = "complete (no loss)"
            elif len(missing) == 1 and "parity" in slots:
                known = [p for p in data_slots if p is not None]
                recovered = xor_bytes(known + [slots["parity"]])
                data_slots[missing[0]] = recovered
                recovered_count += 1
                status = f"RECOVERED slot {missing[0]} via FEC"
            else:
                unrecoverable_count += 1
                status = f"UNRECOVERABLE - {len(missing)} data packets missing (parity {'present' if 'parity' in slots else 'also missing'})"

            print(f"Block {block_id}: {status}")

        print(f"\n[B] Summary: {NUM_BLOCKS - recovered_count - unrecoverable_count} clean, "
              f"{recovered_count} recovered via FEC, {unrecoverable_count} unrecoverable")


if __name__ == "__main__":
    role = sys.argv[1]
    if role == "A":
        asyncio.run(run_sender())
    else:
        asyncio.run(run_receiver())