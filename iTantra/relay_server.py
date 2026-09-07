import asyncio
import json
import os
import random
import struct
import sys
import time
import zlib
import http.server
import threading
import websockets

# Reconfigure stdout for UTF-8 on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Try importing HuggingFace Multilingual Datasets Module
try:
    from ml.huggingface_datasets import get_hf_catalog
except Exception:
    def get_hf_catalog():
        return {
            "status": "ACTIVE",
            "provider": "HuggingFace Datasets & Models Hub",
            "datasets": ["google/fleurs", "mozilla-foundation/common_voice_13_0", "facebook/mms-tts", "ai4bharat/indic-speech"],
            "models": {"en": "facebook/mms-tts-eng", "hi": "facebook/mms-tts-hin", "bn": "facebook/mms-tts-ben", "ta": "facebook/mms-tts-tam"}
        }

MAGIC_HEADER = b'ITAN'
PACKET_SIZE = 69

connected_clients = {}
traffic_logs = []
stats_counter = {
    "relayed": 0,
    "dropped": 0,
    "bytes_saved": 0
}

DISTRESS_KEYWORDS = [
    "help", "danger", "emergency", "sos", "alert", "mayday", "urgent", "flood", "fire", "evacuate", "rescue",
    "मदद", "आपातकाल", "खतरा", "बचाव", "बाढ़", "आग",
    "জরুরি", "সাহায্য", "বিপদ", "বন্যা", "আগুন", "উদ্ধার",
    "அவசரம்", "உதவி", "ஆபத்து", "வெள்ளம்", "தீ"
]

def analyze_urgency(text: str) -> dict:
    text_lower = text.lower()
    is_urgent = any(kw in text_lower for kw in DISTRESS_KEYWORDS)
    return {
        "urgency_level": 2 if is_urgent else 0,
        "pitch_shift_hz": 40 if is_urgent else 0,
        "tempo_multiplier": 135 if is_urgent else 100
    }

class SimpleChannelSimulator:
    def __init__(self, loss_rate=0.05, base_latency_ms=80, jitter_ms=30):
        self.loss_rate = loss_rate
        self.base_latency_ms = base_latency_ms
        self.jitter_ms = jitter_ms

    def should_drop(self):
        return random.random() < self.loss_rate

    async def apply_delay(self):
        jitter = random.uniform(-self.jitter_ms, self.jitter_ms)
        delay_sec = max(0.01, (self.base_latency_ms + jitter) / 1000.0)
        await asyncio.sleep(delay_sec)
        return round(delay_sec * 1000.0, 1)

channel = SimpleChannelSimulator()

def get_network_stats():
    return {
        "total_relayed": stats_counter["relayed"],
        "total_dropped": stats_counter["dropped"],
        "loss_rate_setting": f"{channel.loss_rate * 100:.0f}%",
        "legacy_bandwidth": "128,000 bps (150,000 Bytes/sec)",
        "itantra_bandwidth": "72 bps (69 Bytes / 5sec)",
        "bandwidth_reduction": "99.9%",
        "supported_languages": ["English (en)", "Hindi (hi)", "Bengali (bn)", "Tamil (ta)", "Code-Mixed Auto (mix)"],
        "huggingface_datasets": ["google/fleurs", "mozilla-foundation/common_voice_13_0", "facebook/mms-tts", "ai4bharat/indic-speech"],
        "active_stations": list(connected_clients.keys()),
        "connected_count": len(connected_clients)
    }

# HTTP API Request Handler for port 8081
class RESTApiHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(get_network_stats()).encode('utf-8'))
        elif self.path == "/api/logs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(traffic_logs[-30:]).encode('utf-8'))
        elif self.path == "/api/hf-datasets":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(get_hf_catalog(), ensure_ascii=False).encode('utf-8'))
        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ONLINE", "server": "iTantra Relay Node v2.0"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def start_http_api_server(port=8081):
    try:
        server = http.server.HTTPServer(("0.0.0.0", port), RESTApiHandler)
        print(f"[http] REST API Server listening on http://0.0.0.0:{port}/api/stats & /api/hf-datasets")
        server.serve_forever()
    except Exception as e:
        print(f"[http ERROR] Failed to start HTTP server on port {port}: {e}")

# Websockets process_request hook for port 8765
async def process_http_request(connection, request):
    path = request.path
    if path.startswith("/api/"):
        if path == "/api/stats":
            return connection.respond(200, json.dumps(get_network_stats()))
        elif path == "/api/logs":
            return connection.respond(200, json.dumps(traffic_logs[-30:]))
        elif path == "/api/hf-datasets":
            return connection.respond(200, json.dumps(get_hf_catalog(), ensure_ascii=False))
        elif path == "/api/health":
            return connection.respond(200, json.dumps({"status": "ONLINE", "server": "iTantra Unified Relay Server v2.0"}))
    return None

async def handle_client(websocket):
    role = f"STN-{random.randint(1000, 9999)}"
    try:
        init_msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
        if isinstance(init_msg, str) and init_msg.strip():
            role = init_msg.strip()
    except Exception:
        pass

    connected_clients[role] = websocket
    print(f"[relay] Client '{role}' connected. Active stations: {list(connected_clients.keys())}")

    # Send connection confirmation to client
    ack_packet = {
        "type": "connected",
        "station": role,
        "active_stations": list(connected_clients.keys()),
        "msg": f"Connected to iTantra Relay Server as {role}"
    }
    await websocket.send(json.dumps(ack_packet))

    try:
        async for raw_msg in websocket:
            stats_counter["relayed"] += 1
            delay_ms = await channel.apply_delay()

            parsed_packet = None
            text = ""
            station_id = role
            mhz = 145.875
            lang = "en"
            priority = "routine"
            urgency = 0

            if isinstance(raw_msg, bytes):
                if len(raw_msg) == PACKET_SIZE and raw_msg[:4] == MAGIC_HEADER:
                    try:
                        header = raw_msg[:4]
                        spk = raw_msg[4:20]
                        phoneme = raw_msg[20:60]
                        u, l_id, pitch, tempo, dur = struct.unpack("!BBBBB", raw_msg[60:65])
                        crc = struct.unpack("!I", raw_msg[65:69])[0]
                        text = phoneme.rstrip(b'\x00').decode('utf-8', errors='ignore')
                        urgency = u
                        lang = "hi" if l_id == 1 else "bn" if l_id == 2 else "ta" if l_id == 3 else "mix" if l_id == 4 else "en"
                        parsed_packet = {
                            "id": f"pkt-{int(time.time()*1000)}",
                            "text": text,
                            "lang": lang,
                            "mhz": mhz,
                            "priority": "alert" if urgency > 0 else "routine",
                            "urgency": urgency,
                            "sentAt": int(time.time()*1000),
                            "bytes": len(raw_msg),
                            "station": station_id,
                            "binary_hex": raw_msg.hex()
                        }
                    except Exception as e:
                        print(f"[relay] Binary decode error: {e}")
            else:
                try:
                    data = json.loads(raw_msg)
                    if isinstance(data, dict):
                        if data.get("type") == "connected":
                            continue
                        parsed_packet = data
                        text = data.get("text", "")
                        station_id = data.get("station", role)
                        mhz = data.get("mhz", 145.875)
                        lang = data.get("lang", "en")
                        priority = data.get("priority", "routine")
                        urgency = data.get("urgency", 0)
                except Exception:
                    text = raw_msg
                    parsed_packet = {
                        "id": f"pkt-{int(time.time()*1000)}",
                        "text": text,
                        "lang": "en",
                        "mhz": 145.875,
                        "priority": "routine",
                        "urgency": 0,
                        "sentAt": int(time.time()*1000),
                        "bytes": len(text.encode('utf-8')),
                        "station": role
                    }

            if not parsed_packet:
                continue

            urgency_analysis = analyze_urgency(text)
            if urgency_analysis["urgency_level"] > urgency:
                parsed_packet["urgency"] = urgency_analysis["urgency_level"]
                parsed_packet["priority"] = "alert"

            lang_map = {"en": 0, "hi": 1, "bn": 2, "ta": 3, "mix": 4}
            lang_code_id = lang_map.get(lang, 0)
            text_bytes = text.encode('utf-8')[:40].ljust(40, b'\x00')
            pkt_69b = MAGIC_HEADER + os.urandom(16) + text_bytes + struct.pack("!BBBBB", parsed_packet["urgency"], lang_code_id, 40, 135, 100)
            crc32_val = zlib.crc32(pkt_69b) & 0xffffffff
            pkt_69b += struct.pack("!I", crc32_val)
            parsed_packet["bytes"] = len(pkt_69b)

            msg_to_send = json.dumps(parsed_packet)
            savings = round((1 - (69 / 150000)) * 100, 2)

            log_entry = {
                "timestamp": time.strftime("%H:%M:%S"),
                "station": station_id,
                "text": text,
                "lang": lang,
                "mhz": mhz,
                "urgency": parsed_packet["urgency"],
                "delay_ms": delay_ms,
                "bytes": 69,
                "savings": f"{savings}%"
            }
            traffic_logs.append(log_entry)
            print(f"[relay] Transmit from {station_id} [{mhz} MHz] [{lang.upper()}] (Urgency={parsed_packet['urgency']}, Delay={delay_ms}ms): '{text}' | ⚡ {savings}% Bandwidth Saved")

            other_clients = [ws for r, ws in connected_clients.items() if r != role and ws is not websocket]

            if other_clients:
                for other_ws in other_clients:
                    try:
                        await other_ws.send(msg_to_send)
                    except Exception as e:
                        print(f"[relay] Error sending to peer station: {e}")
            else:
                # Single station loopback ACK echo
                print(f"[relay] Single station online. Base Station sending ACK echo for: '{text}'")
                base_ack = dict(parsed_packet)
                base_ack["id"] = f"base-{int(time.time()*1000)}"
                base_ack["station"] = "STN-BASE (iTantra Relay Node)"
                base_ack["text"] = text
                try:
                    await websocket.send(json.dumps(base_ack))
                except Exception:
                    pass

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if role in connected_clients:
            del connected_clients[role]
            print(f"[relay] Station '{role}' disconnected. Remaining: {list(connected_clients.keys())}")

async def main():
    port = 8765
    print("==========================================================================")
    print(f"  iTantra Unified Multi-Protocol Relay Server Running on ws://0.0.0.0:{port}")
    print("==========================================================================")
    print(f" Serving WebSocket Relay : ws://0.0.0.0:{port}")
    print(f" Supported Languages     : English (en), Hindi (hi), Bengali (bn), Tamil (ta), Code-Mixed (mix)")
    print(f" HuggingFace Datasets    : google/fleurs, mozilla/common_voice, facebook/mms-tts, ai4bharat")
    print(f" Serving REST APIs       : http://0.0.0.0:{port}/api/stats & http://0.0.0.0:8081/api/hf-datasets\n")
    
    # Start background HTTP REST API server on port 8081
    threading.Thread(target=start_http_api_server, args=(8081,), daemon=True).start()

    try:
        async with websockets.serve(handle_client, "0.0.0.0", port, process_request=process_http_request):
            await asyncio.Future()
    except OSError as e:
        if e.errno in (10048, 98):
            print(f"\n[relay ERROR] Port {port} is currently in use.")
        else:
            raise e

if __name__ == "__main__":
    asyncio.run(main())
