import sounddevice as sd

print("Available audio devices:")
print(sd.query_devices())
print()
print("Default input device:", sd.default.device[0])