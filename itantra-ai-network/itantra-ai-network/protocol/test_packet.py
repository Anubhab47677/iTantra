from packet import build_packet, parse_packet, PACKET_TYPE_TEXT, HEADER_SIZE

# Simulate a text-fallback packet (Emergency Mode)
text = "नमस्कार मैं अनुभव हूँ"
payload = text.encode("utf-8")

packet = build_packet(
    packet_type=PACKET_TYPE_TEXT,
    seq_num=42,
    language="hi",
    payload_bytes=payload,
)

print(f"Header size       : {HEADER_SIZE} bytes")
print(f"Total packet size : {len(packet)} bytes")
print(f"Raw header bytes  : {packet[:HEADER_SIZE].hex()}")
print()

parsed = parse_packet(packet)
print("Parsed packet:")
for k, v in parsed.items():
    if k == "payload":
        print(f"  {k}: {v.decode('utf-8')}")
    else:
        print(f"  {k}: {v}")