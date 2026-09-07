"""
Module 4: Acoustic Radio Modem (FSK Modulation) for iTantra
Transceives text packets over radio/acoustic audio signals without Wi-Fi, Bluetooth, or Internet.
"""
import time
import json
import numpy as np
import sounddevice as sd
from transceiver_engine import PacketEncoder
import config

# Radio FSK Audio Frequency Parameters
SAMPLERATE = 16000
MARK_FREQ = 1200   # Frequency for '1' bit (Hz)
SPACE_FREQ = 2200  # Frequency for '0' bit (Hz)
PREAMBLE_FREQ = 1800 # Start preamble frequency (Hz)
BIT_DURATION = 0.015 # 15 ms per bit (~66 bps acoustic radio modulation)

class RadioAudioModem:
    """Acoustic Radio Modem: Converts text packets into audio frequencies and decodes them."""
    
    @staticmethod
    def bytes_to_bits(data_bytes):
        bits = []
        for byte in data_bytes:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits

    @staticmethod
    def bits_to_bytes(bits):
        byte_list = []
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            if len(byte_bits) == 8:
                byte_val = 0
                for b in byte_bits:
                    byte_val = (byte_val << 1) | b
                byte_list.append(byte_val)
        return bytes(byte_list)

    @classmethod
    def modulate(cls, data_bytes):
        """Convert binary packet into acoustic radio audio tones (FSK)."""
        bits = cls.bytes_to_bits(data_bytes)
        audio_samples = []

        # 1. Preamble sync signal (100 ms)
        t_pre = np.linspace(0, 0.1, int(SAMPLERATE * 0.1), False)
        audio_samples.append(np.sin(2 * np.pi * PREAMBLE_FREQ * t_pre))

        # 2. FSK Bit Tones
        t_bit = np.linspace(0, BIT_DURATION, int(SAMPLERATE * BIT_DURATION), False)
        for bit in bits:
            freq = MARK_FREQ if bit == 1 else SPACE_FREQ
            tone = np.sin(2 * np.pi * freq * t_bit)
            audio_samples.append(tone)

        audio_signal = np.concatenate(audio_samples).astype(np.float32)
        return audio_signal

    @classmethod
    def transmit_radio_sound(cls, payload_dict, play_audio=False, *args, **kwargs):
        """Modulate text packet into radio payload. Optionally play chirp if requested."""
        packet_bytes = PacketEncoder.encode(
            text=payload_dict.get('text', ''),
            lang=payload_dict.get('lang', 'hi'),
            gender=payload_dict.get('gender', 'm')
        )
        print(f"📡 [RADIO MODEM] Encoded {len(packet_bytes)} bytes into Narrowband Radio Packet Payload")
        
        if play_audio:
            print("📡 Broadcasting Acoustic Radio Chirp Tone...")
            audio_signal = cls.modulate(packet_bytes)
            sd.play(audio_signal, samplerate=SAMPLERATE)
            sd.wait()
            sd.stop()
            time.sleep(0.2)
        
        return packet_bytes

if __name__ == "__main__":
    test_payload = {"text": "नमस्ते रेडियो टेस्ट", "lang": "hi"}
    RadioAudioModem.transmit_radio_sound(test_payload, play_audio=False)
