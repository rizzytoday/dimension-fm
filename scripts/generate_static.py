"""
Generate radio static/crackle SFX for channel transitions.
Synthesizes band-limited white noise with crackle texture.
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt
import soundfile as sf
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "audio" / "sfx"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100
DURATION = 0.4  # seconds


def generate_static():
    n_samples = int(SAMPLE_RATE * DURATION)

    # White noise base
    noise = np.random.randn(n_samples).astype(np.float32)

    # Add crackle: sparse impulses
    crackle = np.zeros(n_samples, dtype=np.float32)
    n_pops = int(n_samples * 0.003)  # ~0.3% density
    pop_indices = np.random.randint(0, n_samples, n_pops)
    crackle[pop_indices] = np.random.randn(n_pops) * 3.0
    noise += crackle

    # Band-pass 200Hz - 8kHz
    sos = butter(4, [200, 8000], btype="band", fs=SAMPLE_RATE, output="sos")
    filtered = sosfiltfilt(sos, noise).astype(np.float32)

    # Normalize to -6dB peak
    peak = np.max(np.abs(filtered))
    if peak > 0:
        filtered = filtered / peak * 0.5

    # Fade in/out (20ms each)
    fade_len = int(SAMPLE_RATE * 0.02)
    fade_in = np.linspace(0, 1, fade_len, dtype=np.float32)
    fade_out = np.linspace(1, 0, fade_len, dtype=np.float32)
    filtered[:fade_len] *= fade_in
    filtered[-fade_len:] *= fade_out

    out_path = OUTPUT_DIR / "static.wav"
    sf.write(str(out_path), filtered, SAMPLE_RATE)
    print(f"Generated: {out_path} ({DURATION}s, {SAMPLE_RATE}Hz)")
    return str(out_path)


if __name__ == "__main__":
    generate_static()
