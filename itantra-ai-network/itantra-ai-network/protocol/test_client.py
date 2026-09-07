import asyncio
import sys
import websockets
from packet import build_packet, parse_packet, PACKET_TYPE_TEXT

async def run_client(role):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send(role)  # identify ourselves
        print(f"[{role}] Connected and identified.")

        if role == "A":
            text = "Hello from A"
            packet = build_packet(PACKET_TYPE_TEXT, seq_num=1, language="en",
                                   payload_bytes=text.encode("utf-8"))
            await websocket.send(packet)
            print(f"[A] Sent: '{text}'")

            response = await websocket.recv()
            parsed = parse_packet(response)
            print(f"[A] Received: '{parsed['payload'].decode('utf-8')}'")

        elif role == "B":
            message = await websocket.recv()
            parsed = parse_packet(message)
            received_text = parsed["payload"].decode("utf-8")
            print(f"[B] Received: '{received_text}'")

            reply_text = f"Got it: {received_text}"
            packet = build_packet(PACKET_TYPE_TEXT, seq_num=2, language="en",
                                   payload_bytes=reply_text.encode("utf-8"))
            await websocket.send(packet)
            print(f"[B] Sent: '{reply_text}'")

if __name__ == "__main__":
    role = sys.argv[1]
    asyncio.run(run_client(role))