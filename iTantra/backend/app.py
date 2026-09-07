"""
iTantra Full-Stack HTTP & API Server
------------------------------------
Standard library Python Web Server serving:
1. Interactive Web Walkie-Talkie UI (Frontend)
2. Real-time 69-Byte Binary Protocol Encoding & Decoding APIs
3. Simulated Disaster Mesh Network Relay & Multilingual Neural Speech Models
"""

import http.server
import socketserver
import json
import os
import sys
import urllib.parse

# Set UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from protocol import iTantraPacket, LANGUAGES
from backend.relay_network import DisasterMeshNetwork
from models.neural_codec import NeuralAcousticCodec
from models.urgency_classifier import UrgencyEmotionClassifier
from models.multilingual_tts import MultilingualSynthesizer

PORT = 8080
mesh_network = DisasterMeshNetwork(loss_rate=0.15, base_latency_ms=100, jitter_ms=50)
codec = NeuralAcousticCodec()
classifier = UrgencyEmotionClassifier()
tts = MultilingualSynthesizer()

class iTantraHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        directory = os.path.join(PROJECT_ROOT, "frontend")
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = {
                "total_relayed": mesh_network.packets_relayed,
                "total_dropped": mesh_network.packets_dropped,
                "loss_rate_setting": f"{mesh_network.loss_rate * 100:.0f}%",
                "legacy_bandwidth": "128,000 bps (150,000 Bytes/sec)",
                "itantra_bandwidth": "72 bps (69 Bytes / 5sec)",
                "bandwidth_reduction": "99.9%",
                "supported_languages": list(LANGUAGES.values()),
                "huggingface_datasets": ["ai4bharat/indic-superb", "ai4bharat/mucs", "facebook/mms-tts", "google/fleurs"]
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return
        elif parsed.path == "/api/logs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(mesh_network.logs[-20:]).encode('utf-8'))
            return
            
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/transmit":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                payload = json.loads(body.decode('utf-8'))
                text = payload.get("text", "Emergency water rising!")
                user_urgency = int(payload.get("urgency", 1))
                lang_id = int(payload.get("lang_id", 1))
                
                # 1. On-Device Urgency & Multilingual Distress Keyword Analysis
                urgency_meta = classifier.analyze_audio_frame(text)
                urgency_flag = max(user_urgency, urgency_meta["urgency_level"])
                pitch_shift = urgency_meta["pitch_shift_hz"]
                tempo_mult = urgency_meta["tempo_multiplier"]

                # 2. Encode into 69-Byte Binary Protocol
                pkt = iTantraPacket(
                    text=text,
                    urgency=urgency_flag,
                    lang_id=lang_id,
                    pitch_shift=pitch_shift,
                    tempo_mult=tempo_mult
                )
                packed_69b = pkt.pack()

                # 3. Transmit across Disaster Mesh Relay
                result = mesh_network.process_transmission(packed_69b)

                if result["success"]:
                    unpacked = result["packet"]
                    # 4. Synthesize Multilingual & Code-Mixed Voice Payload
                    synth_output = tts.synthesize(unpacked.text, unpacked.lang_id, unpacked.urgency)
                    
                    response_data = {
                        "status": "SUCCESS",
                        "hex_payload": packed_69b.hex(),
                        "payload_bytes": len(packed_69b),
                        "delay_ms": result["log"]["delay_ms"],
                        "urgency_meta": urgency_meta,
                        "decoded_packet": {
                            "text": unpacked.text,
                            "urgency": unpacked.urgency,
                            "language": LANGUAGES.get(unpacked.lang_id, "Code-Mixed Auto"),
                            "pitch_shift_hz": unpacked.pitch_shift,
                            "tempo_multiplier": unpacked.tempo_mult
                        },
                        "synthesis": synth_output
                    }
                else:
                    response_data = {
                        "status": "DROPPED",
                        "reason": result["log"].get("reason", "RF Interference"),
                        "hex_payload": packed_69b.hex(),
                        "payload_bytes": len(packed_69b)
                    }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))

            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return


def start_server():
    print(f"===========================================================")
    print(f"  iTantra Full-Stack Server Running at http://localhost:{PORT}")
    print(f"===========================================================")
    print(f" Serving Frontend UI : {os.path.join(PROJECT_ROOT, 'frontend')}")
    print(f" API Endpoints       : /api/transmit, /api/stats, /api/logs\n")

    with socketserver.TCPServer(("", PORT), iTantraHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down iTantra server...")

if __name__ == "__main__":
    start_server()
