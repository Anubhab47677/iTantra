import random
from fec import build_block_with_parity, recover_missing_payload, FEC_BLOCK_SIZE
from packet import parse_packet

original_payloads = [
    bytes([10, 20, 30, 40]),
    bytes([1, 2, 3, 4]),
    bytes([99, 98, 97, 96]),
    bytes([255, 0, 128, 64]),
]

packets = build_block_with_parity(block_id=0, payloads=original_payloads)
print(f"Built {len(packets)} packets for this block (4 data + 1 parity)")

lost_index = random.randint(0, 4)
print(f"Simulating loss of packet index {lost_index}")

received_raw = [pkt if i != lost_index else None for i, pkt in enumerate(packets)]
parsed = [parse_packet(pkt) if pkt is not None else None for pkt in received_raw]

if lost_index < FEC_BLOCK_SIZE:
    # Only look at the first FEC_BLOCK_SIZE entries — those are the DATA packets.
    # The parity packet (index FEC_BLOCK_SIZE) is handled separately below.
    data_parsed = parsed[:FEC_BLOCK_SIZE]
    data_payloads = [p["payload"] if p is not None else None for p in data_parsed]

    parity_payload = parsed[FEC_BLOCK_SIZE]["payload"]

    recovered = recover_missing_payload(data_payloads, parity_payload)
    original = original_payloads[lost_index]

    print(f"Original payload  : {list(original)}")
    print(f"Recovered payload : {list(recovered[:len(original)])}")
    print(f"Recovery correct  : {recovered[:len(original)] == original}")
else:
    print("The PARITY packet itself was lost — no recovery needed, all data packets arrived intact.")