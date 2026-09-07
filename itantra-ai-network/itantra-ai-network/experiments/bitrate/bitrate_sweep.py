import os
import sys
import csv
import torch
import soundfile as sf
from encodec import EncodecModel
from encodec.utils import convert_audio

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "datasets"))
RESULTS_CSV = os.path.join(SCRIPT_DIR, "bitrate_sweep_results.csv")

# EnCodec's supported bandwidths (kbps) - these correspond to specific RVQ depths
BANDWIDTHS = [1.5, 3.0, 6.0, 12.0, 24.0]

def load_wav_as_tensor(path):
    data, sr = sf.read(path, dtype="float32")
    if data.ndim == 1:
        data = data[:, None]
    return torch.from_numpy(data.T), sr

def save_tensor_as_wav(tensor, sr, path):
    data = tensor.squeeze(0).numpy().T
    sf.write(path, data, sr)

def run_sweep(input_filename):
    input_path = os.path.join(DATASETS_DIR, input_filename)
    base_name = os.path.splitext(input_filename)[0]

    results = []
    for bw in BANDWIDTHS:
        model = EncodecModel.encodec_model_24khz()
        model.set_target_bandwidth(bw)
        model.eval()

        wav, sr = load_wav_as_tensor(input_path)
        wav = convert_audio(wav, sr, model.sample_rate, model.channels).unsqueeze(0)

        with torch.no_grad():
            encoded_frames = model.encode(wav)
            codes = torch.cat([frame[0] for frame in encoded_frames], dim=-1)
            decoded = model.decode(encoded_frames)

        out_filename = f"{base_name}_recon_{bw}kbps.wav"
        out_path = os.path.join(DATASETS_DIR, out_filename)
        save_tensor_as_wav(decoded, model.sample_rate, out_path)

        n_codebooks = codes.shape[1]
        total_bits = codes.numel() * 10  # 10 bits per code (log2(1024))
        encoded_bytes = total_bits / 8
        original_bytes = os.path.getsize(input_path)
        duration_sec = wav.shape[-1] / model.sample_rate
        actual_kbps = total_bits / duration_sec / 1000

        row = {
            "target_kbps": bw,
            "actual_kbps": round(actual_kbps, 2),
            "codebooks": n_codebooks,
            "compression_ratio": round(original_bytes / encoded_bytes, 1),
            "encoded_bytes": round(encoded_bytes),
            "output_file": out_filename,
        }
        results.append(row)
        print(f"[{bw} kbps] codebooks={n_codebooks}  compression={row['compression_ratio']}x  -> {out_filename}")

    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResults saved to {RESULTS_CSV}")

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "hindi_clip.wav"
    run_sweep(filename)