import numpy as np
import torch
import soundfile as sf
from encodec import EncodecModel
from encodec.utils import convert_audio


class CodecService:
    """
    Loads EnCodec ONCE, then can encode/decode many times.
    This is what Backend will instantiate once at server startup.
    """

    def __init__(self, bandwidth_kbps=6.0):
        print(f"[Codec] Loading EnCodec (target {bandwidth_kbps} kbps)...")
        self.model = EncodecModel.encodec_model_24khz()
        self.model.set_target_bandwidth(bandwidth_kbps)
        self.model.eval()
        print("[Codec] Model loaded.")

    def set_bandwidth(self, bandwidth_kbps):
        """Change bitrate on the fly - this is your adaptive-bitrate control."""
        self.model.set_target_bandwidth(bandwidth_kbps)

    def _load_wav(self, path):
        data, sr = sf.read(path, dtype="float32")
        if data.ndim == 1:
            data = data[:, None]
        tensor = torch.from_numpy(data.T)
        return convert_audio(tensor, sr, self.model.sample_rate, self.model.channels).unsqueeze(0)

    def encode_file(self, audio_path):
        """
        Returns raw code bytes ready for packet payloads, plus metadata
        needed to decode them again (n_codebooks, codes_shape).

        NOTE: uses int16 (not uint8) because EnCodec's codebook has 1024
        entries (values 0-1023), which does not fit in a uint8 (0-255).
        This costs 2 bytes/code instead of the theoretical 10 bits/code -
        a known, acceptable simplification for the hackathon MVP.
        """
        wav = self._load_wav(audio_path)
        with torch.no_grad():
            encoded_frames = self.model.encode(wav)
            codes = torch.cat([frame[0] for frame in encoded_frames], dim=-1)

        n_codebooks = codes.shape[1]
        code_bytes = codes.to(torch.int16).numpy().tobytes()
        return code_bytes, n_codebooks, codes.shape

    def decode_to_file(self, code_bytes, n_codebooks, codes_shape, output_path):
        """Reconstruct audio from received code bytes and save to a wav file."""
        codes_flat = np.frombuffer(code_bytes, dtype=np.int16)
        codes = torch.from_numpy(codes_flat.reshape(codes_shape).copy()).long()

        # EnCodec's decode() expects the same "frames" structure encode() produced
        frame = (codes, None)
        with torch.no_grad():
            decoded = self.model.decode([frame])

        audio = decoded.squeeze(0).numpy().T
        sf.write(output_path, audio, self.model.sample_rate)


if __name__ == "__main__":
    # Quick self-test when run directly
    service = CodecService(bandwidth_kbps=6.0)

    code_bytes, n_cb, shape = service.encode_file("../../datasets/hindi_clip.wav")
    print(f"Encoded to {len(code_bytes)} bytes, {n_cb} codebooks, shape {shape}")

    service.decode_to_file(code_bytes, n_cb, shape, "../../datasets/hindi_clip_service_test.wav")
    print("Decoded and saved successfully.")