"""
iTantra Configuration Module
System parameters, audio settings, and network defaults.
"""
import os
import sys

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Audio Recording Defaults
SAMPLE_RATE = 16000  # 16 kHz Mono PCM
CHANNELS = 1
AUDIO_FORMAT_BITS = 16

# Network Transceiver Defaults
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9999
SIMULATED_BITRATE_BPS = 300  # 300 bps simulated narrowband link (e.g. ISRO SatCom / HF Radio)

# Model Settings
WHISPER_MODEL_SIZE = "tiny"  # 'tiny', 'base', 'small'
COMPUTE_TYPE = "int8"        # INT8 quantization for fast CPU execution
DEVICE = "cpu"

# Directory Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_AUDIO_DIR = os.path.join(BASE_DIR, "temp_audio")
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
