"""
iTantra Multi-Hop Disaster Mesh Relay Network Engine
-----------------------------------------------------
Simulates multi-hop radio mesh nodes (LoRa / 2G Control Channels / HF Ham Radio).
Manages packet transmission, configurable channel loss rates (15% default), jitter, and latency.
"""

import time
import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from protocol import iTantraPacket

class DisasterMeshNetwork:
    def __init__(self, loss_rate=0.15, base_latency_ms=100, jitter_ms=50):
        self.loss_rate = loss_rate
        self.base_latency_ms = base_latency_ms
        self.jitter_ms = jitter_ms
        self.logs = []
        self.packets_relayed = 0
        self.packets_dropped = 0

    def process_transmission(self, raw_69b_packet: bytes) -> dict:
        """
        Processes a 69-byte binary packet through simulated disaster RF links.
        """
        timestamp = time.strftime("%H:%M:%S")
        self.packets_relayed += 1

        # Simulate 15% random packet loss
        is_dropped = random.random() < self.loss_rate
        if is_dropped:
            self.packets_dropped += 1
            log_entry = {
                "timestamp": timestamp,
                "status": "DROPPED",
                "reason": "15% RF Channel Interference / Multi-path Fading",
                "bytes": 69,
                "delay_ms": 0
            }
            self.logs.append(log_entry)
            return {"success": False, "log": log_entry}

        # Simulate Latency & Jitter
        jitter = random.uniform(-self.jitter_ms, self.jitter_ms)
        effective_delay_ms = round(max(10, self.base_latency_ms + jitter), 1)

        # Unpack and verify CRC
        try:
            unpacked_pkt = iTantraPacket.unpack(raw_69b_packet)
            log_entry = {
                "timestamp": timestamp,
                "status": "DELIVERED",
                "bytes": len(raw_69b_packet),
                "delay_ms": effective_delay_ms,
                "text": unpacked_pkt.text,
                "urgency": unpacked_pkt.urgency,
                "lang_id": unpacked_pkt.lang_id,
                "pitch_shift": unpacked_pkt.pitch_shift,
                "tempo_mult": unpacked_pkt.tempo_mult
            }
            self.logs.append(log_entry)
            return {"success": True, "log": log_entry, "packet": unpacked_pkt}
        except Exception as e:
            log_entry = {
                "timestamp": timestamp,
                "status": "CORRUPTED",
                "reason": str(e),
                "bytes": 69,
                "delay_ms": effective_delay_ms
            }
            self.logs.append(log_entry)
            return {"success": False, "log": log_entry}


if __name__ == "__main__":
    mesh = DisasterMeshNetwork()
    pkt = iTantraPacket(text="Test burst", urgency=1, lang_id=1).pack()
    print(mesh.process_transmission(pkt))
