import asyncio
import sys
import time
import websockets
from packet import build_packet, parse_packet, PACKET_TYPE_CONTROL

NUM_PINGS = 20

async def run_pinger():
    uri = "ws://localhost:8765"
    rtts = []
    lost = 0
    async with websockets.connect(uri) as websocket:
        await websocket.send("A")
        print("[A] Connected. Sending pings...")

        for seq in range(NUM_PINGS):
            send_time = time.time()
            packet = build_packet(PACKET_TYPE_CONTROL, seq, language="en",
                                   payload_bytes=b"ping")
            await websocket.send(packet)

            try:
                # Reply should arrive well within ~1s even with configured latency/jitter.
                # If it doesn't, the ping (or its reply) was almost certainly dropped.
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                recv_time = time.time()
                rtt_ms = (recv_time - send_time) * 1000
                rtts.append(rtt_ms)
                print(f"  ping {seq}: {rtt_ms:.1f} ms")
            except asyncio.TimeoutError:
                lost += 1
                print(f"  ping {seq}: LOST (no reply within timeout)")

            await asyncio.sleep(0.1)

        print(f"\n[A] Replies received: {len(rtts)}/{NUM_PINGS}  (lost: {lost})")
        if rtts:
            avg_rtt = sum(rtts) / len(rtts)
            print(f"[A] Average RTT: {avg_rtt:.1f} ms")
            print(f"[A] Min: {min(rtts):.1f} ms, Max: {max(rtts):.1f} ms")
        else:
            print("[A] No successful pings — check relay is running and loss rate isn't too high.")


async def run_ponger():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("B")
        print("[B] Connected. Echoing pings back...")

        count = 0
        try:
            while count < NUM_PINGS:
                message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                parsed = parse_packet(message)
                reply = build_packet(PACKET_TYPE_CONTROL, parsed["seq_num"],
                                      language="en", payload_bytes=b"pong")
                await websocket.send(reply)
                count += 1
        except asyncio.TimeoutError:
            print("[B] Timed out waiting for pings.")

        print(f"[B] Echoed {count} pings.")


if __name__ == "__main__":
    role = sys.argv[1]
    if role == "A":
        asyncio.run(run_pinger())
    else:
        asyncio.run(run_ponger())