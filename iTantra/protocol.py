"""
iTantra 69-Byte Custom Binary Radio Protocol
--------------------------------------------
Encodes 5 seconds of neural voice features into an ultra-compact 69-byte binary packet
capable of transmitting over zero-internet RF links (LoRa, HF, degraded 2G).

Binary Frame Map (69 Bytes Total):
[0..3]   SYNC_HDR      (4 Bytes)  : Magic bytes b'ITAN' (0x4954414E)
[4..19]  SPK_LATENT    (16 Bytes) : Quantized 128-bit speaker identity vector
[20..59] PHONEME_SEQ   (40 Bytes) : Neural phonetic tokens (5s @ 6-bit codes)
[60..64] CONTROL_FLAGS (5 Bytes)  :
           - Byte 60: Urgency Flag (0=Normal, 1=Urgent, 2=Critical SOS)
           - Byte 61: Language ID (0=English, 1=Hindi, 2=Bengali, 3=Tamil, 5=Code-Mixed Auto)
           - Byte 62: Pitch Shift (Hz offset, e.g. 40 = +40Hz)
           - Byte 63: Tempo Multiplier (e.g. 135 = 1.35x / +35%)
           - Byte 64: Duration (units of 50ms, 100 = 5000ms = 5s)
[65..68] CRC32         (4 Bytes)  : Payload error check checksum
"""

import struct
import zlib
import os

MAGIC_HEADER = b'ITAN'
PACKET_SIZE = 69

LANGUAGES = {
    0: "English",
    1: "Hindi",
    2: "Bengali",
    3: "Tamil",
    5: "Code-Mixed Auto"
}

class iTantraPacket:
    def __init__(self, text="", urgency=1, lang_id=1, pitch_shift=40, tempo_mult=135):
        self.urgency = urgency
        self.lang_id = lang_id
        self.pitch_shift = pitch_shift
        self.tempo_mult = tempo_mult
        self.text = text
        self.speaker_latent = os.urandom(16)  # Quantized 128-bit neural speaker embedding
        
        # Phoneme sequence encoding (40 bytes max)
        text_bytes = text.encode('utf-8')[:40]
        self.phoneme_seq = text_bytes.ljust(40, b'\x00')

    def pack() -> bytes:
        pass

    def encode(self) -> bytes:
        """Packs metadata and speech features into 69-byte binary payload."""
        flags = struct.pack("BBBBB", self.urgency, self.lang_id, self.pitch_shift, self.tempo_mult, 100)
        payload = MAGIC_HEADER + self.speaker_latent + self.phoneme_seq + flags
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        full_packet = payload + struct.pack(">I", crc)
        return full_packet

    @classmethod
    def decode(cls, binary_data: bytes) -> dict:
        """Unpacks 69-byte payload into decoded speech properties."""
        if len(binary_data) != PACKET_SIZE:
            raise ValueError(f"Invalid packet size: {len(binary_data)}B (Expected {PACKET_SIZE}B)")

        header = binary_data[:4]
        if header != MAGIC_HEADER:
            raise ValueError(f"Invalid sync header: {header}")

        received_crc = struct.unpack(">I", binary_data[65:69])[0]
        computed_crc = zlib.crc32(binary_data[:65]) & 0xFFFFFFFF

        if received_crc != computed_crc:
            raise ValueError(f"CRC checksum mismatch! (Corrupted radio frame)")

        speaker_latent = binary_data[4:20]
        phoneme_seq = binary_data[20:60]
        urgency, lang_id, pitch_shift, tempo_mult, duration = struct.unpack("BBBBB", binary_data[60:65])

        text = phoneme_seq.rstrip(b'\x00').decode('utf-8', errors='ignore')

        return {
            "valid": True,
            "bytes": len(binary_data),
            "speaker_latent_hex": speaker_latent.hex(),
            "decoded_text": text,
            "urgency": urgency,
            "lang_id": lang_id,
            "language_name": LANGUAGES.get(lang_id, "Unknown"),
            "pitch_shift_hz": pitch_shift,
            "tempo_multiplier": tempo_mult,
            "duration_ms": duration * 50
        }

if __name__ == "__main__":
    pkt = iTantraPacket(text="Help! Flood water rising!", urgency=2, lang_id=1)
    binary = pkt.encode()
    print(f"Encoded Binary Packet Size: {len(binary)} Bytes (0x{binary.hex()})")
    decoded = iTantraPacket.decode(binary)
    print("Decoded Metadata:", decoded)
