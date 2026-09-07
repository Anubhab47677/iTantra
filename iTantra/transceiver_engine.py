"""
Module 2: Low-Bitrate Transceiver & Packetization Engine for iTantra
Handles ultra-compact framing, simulated rate-limiting, and socket transmission.
"""
import socket
import json
import time
import threading
import config

class PacketEncoder:
    """Encodes text & metadata into ultra-compact JSON/Binary payloads."""
    @staticmethod
    def encode(text, lang="hi", gender="m", speaker_id=1):
        payload = {
            "l": lang,        # 2-letter language code
            "g": gender,      # 'm' or 'f'
            "s": speaker_id,  # speaker embedding id
            "t": text         # transcribed Unicode text
        }
        return json.dumps(payload, ensure_ascii=False).encode('utf-8')

    @staticmethod
    def decode(packet_bytes):
        payload = json.loads(packet_bytes.decode('utf-8'))
        return {
            "lang": payload.get("l", "hi"),
            "gender": payload.get("g", "m"),
            "speaker_id": payload.get("s", 1),
            "text": payload.get("t", "")
        }

    @staticmethod
    def calculate_metrics(raw_audio_bytes, packet_bytes):
        packet_len = len(packet_bytes)
        savings_pct = (1.0 - (packet_len / max(raw_audio_bytes, 1))) * 100.0
        # Calculate simulated transmission time over 300 bps link
        tx_time_sec = (packet_len * 8) / config.SIMULATED_BITRATE_BPS
        raw_tx_time_sec = (raw_audio_bytes * 8) / config.SIMULATED_BITRATE_BPS
        return {
            "raw_bytes": raw_audio_bytes,
            "packet_bytes": packet_len,
            "bandwidth_savings_pct": round(savings_pct, 2),
            "tx_time_sec": round(tx_time_sec, 3),
            "raw_tx_time_sec": round(raw_tx_time_sec, 2),
            "effective_bitrate_bps": round((packet_len * 8) / max(tx_time_sec, 0.001), 1)
        }

class TransceiverServer:
    """Receiving Node Socket Server."""
    def __init__(self, host=config.DEFAULT_HOST, port=config.DEFAULT_PORT, on_packet_received=None):
        self.host = host
        self.port = port
        self.on_packet_received = on_packet_received
        self.running = False
        self.server_socket = None

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"📡 Transceiver Server listening on {self.host}:{self.port}...")

        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()

    def _listen_loop(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                data = conn.recv(2048)
                if data:
                    packet_info = PacketEncoder.decode(data)
                    packet_info["received_bytes"] = len(data)
                    print(f"\n📩 [TRANSCEIVER] Received Packet ({len(data)} B) from {addr}")
                    if self.on_packet_received:
                        self.on_packet_received(packet_info)
                conn.close()
            except Exception as e:
                if self.running:
                    print(f"⚠️ Transceiver Server Error: {e}")

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

class TransceiverClient:
    """Sender Node Socket Client with simulated low bitrate throttling."""
    @staticmethod
    def send_packet(packet_bytes, host=config.DEFAULT_HOST, port=config.DEFAULT_PORT, simulate_narrowband=True):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))

        if simulate_narrowband:
            # Simulate 300 bps transmission rate byte-by-byte
            bytes_per_sec = config.SIMULATED_BITRATE_BPS / 8.0
            delay_per_byte = 1.0 / max(bytes_per_sec, 1.0)
            for b in packet_bytes:
                client.sendall(bytes([b]))
                time.sleep(delay_per_byte * 0.05)  # Accelerated 20x for responsive demo
        else:
            client.sendall(packet_bytes)

        client.close()
        print(f"📡 [TRANSCEIVER] Packet ({len(packet_bytes)} Bytes) transmitted successfully!")

if __name__ == "__main__":
    def dummy_callback(data):
        print(f"Received: {data}")
    
    server = TransceiverServer(on_packet_received=dummy_callback)
    server.start()
    time.sleep(0.5)
    
    pkt = PacketEncoder.encode("नमस्ते भारत", lang="hi")
    TransceiverClient.send_packet(pkt, simulate_narrowband=False)
    time.sleep(0.5)
    server.stop()
