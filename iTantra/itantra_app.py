"""
iTantra Unified Core Application
Integrates STT, Transceiver, and TTS into one single unified class & CLI tool.
"""
import os
import sys
import time
import argparse
import config
from stt_engine import STTEngine
from transceiver_engine import PacketEncoder, TransceiverServer, TransceiverClient
from tts_engine import TTSEngine

class iTantraSystem:
    def __init__(self, start_server=True):
        print("\n========================================================")
        print("🚀 Launching iTantra Neural Transceiver Radio Access System")
        print("========================================================")
        self.stt = STTEngine()
        self.tts = TTSEngine()
        self.server = None

        if start_server:
            self.server = TransceiverServer(on_packet_received=self._on_packet_received)
            self.server.start()

    def _on_packet_received(self, packet_info):
        text = packet_info['text']
        lang = packet_info['lang']
        print(f"\n[RECEIVER NODE] Received text: '{text}' (Language: {lang})")
        self.tts.speak(text)

    def process_and_transmit(self, audio_filepath=None, duration_sec=4):
        """Full Pipeline: Audio Input -> STT -> Low-Bitrate Packet -> Radio Transmit."""
        if audio_filepath and os.path.exists(audio_filepath):
            stt_result = self.stt.transcribe_file(audio_filepath)
            raw_bytes = os.path.getsize(audio_filepath)
        else:
            stt_result, wav_path = self.stt.process_mic_input(duration_sec=duration_sec)
            raw_bytes = stt_result.get("raw_audio_bytes", 128000)

        text = stt_result['text']
        lang = stt_result['language']

        print(f"\n📝 [SENDER NODE] Speech Transcribed: '{text}' ({lang.upper()})")

        if not text:
            print("⚠️ No speech recognized.")
            return None

        # 1. Encode into ultra-compact payload
        packet_bytes = PacketEncoder.encode(text=text, lang=lang)

        # 2. Calculate savings metrics
        metrics = PacketEncoder.calculate_metrics(raw_bytes, packet_bytes)
        print(f"📊 [METRICS] Raw Audio: {metrics['raw_bytes']} Bytes | iTantra Packet: {metrics['packet_bytes']} Bytes")
        print(f"⚡ [SAVINGS] Bandwidth Reduction: {metrics['bandwidth_savings_pct']}%")
        print(f"⏱️ [SPEED] Transmit Time @ {config.SIMULATED_BITRATE_BPS} bps: {metrics['tx_time_sec']}s (vs {metrics['raw_tx_time_sec']}s raw audio)")

        # 3. Transmit over radio access link
        TransceiverClient.send_packet(packet_bytes, simulate_narrowband=True)

        return {
            "stt": stt_result,
            "metrics": metrics,
            "packet_bytes": packet_bytes
        }

    def close(self):
        if self.server:
            self.server.stop()

def main():
    parser = argparse.ArgumentParser(description="iTantra Multilingual Neural Transceiver System")
    parser.add_argument("--file", type=str, help="Path to input .wav file (optional)")
    parser.add_argument("--mic", action="store_true", help="Record directly from microphone")
    parser.add_argument("--duration", type=int, default=4, help="Mic recording duration in seconds")
    args = parser.parse_args()

    system = iTantraSystem(start_server=True)

    try:
        if args.file:
            system.process_and_transmit(audio_filepath=args.file)
        else:
            print("\n👉 Interactive Mode: Press Enter to record voice, or Ctrl+C to exit.")
            while True:
                input("\n[PRESS ENTER TO RECORD]")
                system.process_and_transmit(duration_sec=args.duration)
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping iTantra System...")
    finally:
        system.close()

if __name__ == "__main__":
    main()
