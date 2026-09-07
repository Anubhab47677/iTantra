# Shared configuration - all modules import from here instead of hardcoding values.

# Audio
SAMPLE_RATE = 16000          # STT/recording sample rate
ENCODEC_SAMPLE_RATE = 24000  # EnCodec's native sample rate

# Codec
DEFAULT_BANDWIDTH_KBPS = 6.0
EMERGENCY_BANDWIDTH_KBPS = 1.5

# Network
RELAY_HOST = "localhost"
RELAY_PORT = 8765
FEC_BLOCK_SIZE = 4

# Channel simulation defaults (for demo controls)
DEFAULT_LOSS_RATE = 0.15
DEFAULT_LATENCY_MS = 100
DEFAULT_JITTER_MS = 50

# Languages
LANGUAGE_CODES = {"en": 0, "hi": 1, "bn": 2, "ta": 3}
LANGUAGE_NAMES = {v: k for k, v in LANGUAGE_CODES.items()}

TTS_MODELS = {
    "hi": "facebook/mms-tts-hin",
    "bn": "facebook/mms-tts-ben",
    "ta": "facebook/mms-tts-tam",
    "en": "facebook/mms-tts-eng",
}