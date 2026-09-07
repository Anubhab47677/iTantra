import asyncio
import sys
import websockets
from packet import build_packet, parse_packet, PACKET_TYPE_AUDIO

NUM_PACKETS = 50

async def run_sender():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("A")
        print("[A] Connected. Sending 50 packets...")

        for seq in range(NUM_PACKETS):
            payload = bytes([seq % 256] * 10)  # fake 10-byte "audio code" payload
            packet = build_packet(PACKET_TYPE_AUDIO, seq, language="hi",
                                   payload_bytes=payload, n_codebooks=8)
            await websocket.send(packet)
            await asyncio.sleep(0.02)  # ~20ms between packets, roughly speech-frame rate

        print("[A] Done sending.")


async def run_receiver():
    uri = "ws://localhost:8765"
    received_seqs = []
    async with websockets.connect(uri) as websocket:
        await websocket.send("B")
        print("[B] Connected. Waiting for sender (you have 30s to start Terminal 3)...")

        first_packet_timeout = 30.0  # generous - covers time to switch windows and start A
        gap_timeout = 3.0            # once packets are flowing, a 3s gap really does mean "stream ended"

        try:
            while len(received_seqs) < NUM_PACKETS:
                timeout = first_packet_timeout if not received_seqs else gap_timeout
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                parsed = parse_packet(message)
                received_seqs.append(parsed["seq_num"])
        except asyncio.TimeoutError:
            print("[B] No more packets arriving (timeout) — treating as end of stream.")

        expected = set(range(NUM_PACKETS))
        received = set(received_seqs)
        missing = sorted(expected - received)

        print(f"\n[B] Received {len(received_seqs)} / {NUM_PACKETS} packets")
        print(f"[B] Missing sequence numbers: {missing}")
        print(f"[B] Observed packet loss rate: {len(missing)/NUM_PACKETS:.1%}")


if __name__ == "__main__":
    role = sys.argv[1]
    if role == "A":
        asyncio.run(run_sender())
    else:
        asyncio.run(run_receiver())