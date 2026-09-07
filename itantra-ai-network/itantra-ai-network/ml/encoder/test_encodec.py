import os
import torch
import soundfile as sf
from encodec import EncodecModel
from encodec.utils import convert_audio

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "datasets"))

TARGET_BANDWIDTH_KBPS = 6.0

def load_model(bandwidth=TARGET_BANDWIDTH_KBPS):
    model = EncodecModel.encodec_model_24khz()
    model.set_target_bandwidth(bandwidth)
    model.eval()
    return model

def load_wav_as_tensor(path):
    data, sr = sf.read(path, dtype="float32")   # (samples,) or (samples, channels)
    if data.ndim == 1:
        data = data[:, None]                     # -> (samples, 1)
    tensor = torch.from_numpy(data.T)            # -> (channels, samples)
    return tensor, sr

def save_tensor_as_wav(tensor, sr, path):
    data = tensor.squeeze(0).numpy().T           # (channels, samples) -> (samples, channels)
    sf.write(path, data, sr)

def encode_decode(model, input_filename, output_filename):
    input_path = os.path.join(DATASETS_DIR, input_filename)
    output_path = os.path.join(DATASETS_DIR, output_filename)

    wav, sr = load_wav_as_tensor(input_path)
    wav = convert_audio(wav, sr, model.sample_rate, model.channels)
    wav = wav.unsqueeze(0)  # add batch dimension: [1, channels, samples]

    with torch.no_grad():
        encoded_frames = model.encode(wav)
        codes = torch.cat([frame[0] for frame in encoded_frames], dim=-1)
        decoded = model.decode(encoded_frames)

    save_tensor_as_wav(decoded, model.sample_rate, output_path)

    n_codebooks = codes.shape[1]
    codebook_size = 1024
    bits_per_code = 10

    total_bits = codes.numel() * bits_per_code
    encoded_bytes = total_bits / 8

    original_bytes = os.path.getsize(input_path)
    duration_sec = wav.shape[-1] / model.sample_rate

    print(f"Waveform shape (encoder input) : {tuple(wav.shape)}")
    print(f"Quantized codes shape          : {tuple(codes.shape)}  (codebooks x timesteps)")
    print(f"Codebooks used (RVQ depth)     : {n_codebooks}")
    print(f"Audio duration                 : {duration_sec:.2f}s")
    print()
    print(f"Original file size             : {original_bytes:,} bytes")
    print(f"Encoded (codes) size           : {encoded_bytes:,.0f} bytes")
    print(f"Compression ratio              : {original_bytes / encoded_bytes:.1f}x")
    print(f"Actual bitrate                 : {total_bits / duration_sec / 1000:.2f} kbps  (target was {TARGET_BANDWIDTH_KBPS} kbps)")
    print()
    print(f"Reconstructed audio saved to   : {output_path}")

if __name__ == "__main__":
    model = load_model()
    encode_decode(model, "hindi_clip.wav", "hindi_clip_reconstructed.wav")