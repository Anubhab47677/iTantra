from packet import build_packet, parse_packet, PACKET_TYPE_AUDIO, PACKET_TYPE_FEC

FEC_BLOCK_SIZE = 4  # 4 data packets + 1 parity packet per block


def xor_bytes(byte_strings):
    """XOR a list of equal-length byte strings together, byte by byte."""
    max_len = max(len(b) for b in byte_strings)
    # Pad shorter payloads with zero bytes so XOR is well-defined across all of them
    padded = [b.ljust(max_len, b"\x00") for b in byte_strings]

    result = bytearray(max_len)
    for b in padded:
        for i in range(max_len):
            result[i] ^= b[i]
    return bytes(result)


def build_block_with_parity(block_id, payloads, language="hi", n_codebooks=8):
    """
    Given a list of data payloads (one block), build the data packets
    plus one parity packet, ready to transmit.
    Returns a list of raw packet bytes: [data_0, data_1, ..., data_N, parity]
    """
    packets = []
    for i, payload in enumerate(payloads):
        seq_num = block_id * FEC_BLOCK_SIZE + i
        pkt = build_packet(PACKET_TYPE_AUDIO, seq_num, language, payload, n_codebooks)
        packets.append(pkt)

    parity_payload = xor_bytes(payloads)
    # Parity packets use their own seq_num scheme: block_id directly,
    # and packet_type=FEC distinguishes them from real data.
    parity_pkt = build_packet(PACKET_TYPE_FEC, block_id, language, parity_payload, n_codebooks)
    packets.append(parity_pkt)

    return packets


def recover_missing_payload(received_payloads, parity_payload):
    """
    received_payloads: list where exactly ONE entry is None (the missing packet),
                        all others are the correctly-received payload bytes.
    Returns the recovered payload for the missing slot.
    """
    known = [p for p in received_payloads if p is not None]
    if len(known) != len(received_payloads) - 1:
        raise ValueError("Recovery only works with exactly one missing packet per block")

    recovered = xor_bytes(known + [parity_payload])
    return recovered