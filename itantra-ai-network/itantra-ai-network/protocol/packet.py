import struct

MAGIC = 0xABCD
VERSION = 1

PACKET_TYPE_AUDIO = 0x01
PACKET_TYPE_TEXT = 0x02
PACKET_TYPE_CONTROL = 0x03
PACKET_TYPE_FEC = 0x04

LANGUAGE_CODES = {"en": 0, "hi": 1, "bn": 2, "ta": 3}
LANGUAGE_NAMES = {v: k for k, v in LANGUAGE_CODES.items()}

# Struct format string for the 12-byte header:
# > = big-endian (network byte order, standard for protocols)
# H = unsigned short (2 bytes)  -> magic
# B = unsigned char  (1 byte)   -> version
# B = unsigned char  (1 byte)   -> packet_type
# I = unsigned int   (4 bytes)  -> seq_num
# B = unsigned char  (1 byte)   -> language
# B = unsigned char  (1 byte)   -> n_codebooks
# H = unsigned short (2 bytes)  -> payload_length
HEADER_FORMAT = ">HBBIBBH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # should be 12


def build_packet(packet_type, seq_num, language, payload_bytes, n_codebooks=0):
    """Pack a header + payload into raw bytes ready to transmit."""
    lang_code = LANGUAGE_CODES.get(language, 0)
    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        VERSION,
        packet_type,
        seq_num,
        lang_code,
        n_codebooks,
        len(payload_bytes),
    )
    return header + payload_bytes


def parse_packet(raw_bytes):
    """Unpack raw bytes back into a header dict + payload bytes."""
    if len(raw_bytes) < HEADER_SIZE:
        raise ValueError(f"Packet too short: {len(raw_bytes)} bytes, need at least {HEADER_SIZE}")

    header_bytes = raw_bytes[:HEADER_SIZE]
    payload_bytes = raw_bytes[HEADER_SIZE:]

    magic, version, packet_type, seq_num, lang_code, n_codebooks, payload_length = struct.unpack(
        HEADER_FORMAT, header_bytes
    )

    if magic != MAGIC:
        raise ValueError(f"Invalid magic bytes: got {hex(magic)}, expected {hex(MAGIC)} — corrupted or non-iTantra packet")

    if len(payload_bytes) != payload_length:
        raise ValueError(f"Payload length mismatch: header says {payload_length}, got {len(payload_bytes)}")

    return {
        "version": version,
        "packet_type": packet_type,
        "seq_num": seq_num,
        "language": LANGUAGE_NAMES.get(lang_code, "unknown"),
        "n_codebooks": n_codebooks,
        "payload": payload_bytes,
    }