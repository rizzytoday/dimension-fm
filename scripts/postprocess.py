"""
Dimension FM — Post-Processing Pipeline
DSP chain for broadcast-quality audio:
  1. High-pass filter 80Hz
  2. Presence boost 4kHz +3dB
  3. Broadcast compression (3:1, -20dB threshold)
  4. Subtle room reverb (synthetic IR, wet=0.15)
  5. Loudness normalize to -14 LUFS
"""

import sys
import shutil
import numpy as np
from scipy.signal import butter, sosfiltfilt, fftconvolve
import soundfile as sf
import pyloudnorm as pyln
from pathlib import Path

AUDIO_DIR = Path(__file__).parent.parent / "audio"
SAMPLE_RATE = 44100


def highpass(audio, cutoff=80):
    """Remove rumble below cutoff Hz."""
    sos = butter(4, cutoff, btype="high", fs=SAMPLE_RATE, output="sos")
    return sosfiltfilt(sos, audio).astype(np.float32)


def presence_boost(audio, center=4000, gain_db=3.0, q=1.0):
    """Peaking EQ boost at center frequency."""
    w0 = 2 * np.pi * center / SAMPLE_RATE
    A = 10 ** (gain_db / 40)
    alpha = np.sin(w0) / (2 * q)

    b0 = 1 + alpha * A
    b1 = -2 * np.cos(w0)
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha / A

    # Normalize
    b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float64)
    a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float64)

    from scipy.signal import lfilter
    return lfilter(b, a, audio).astype(np.float32)


def compress(audio, threshold_db=-20, ratio=3.0, attack_ms=5, release_ms=50):
    """Simple broadcast compressor."""
    threshold = 10 ** (threshold_db / 20)
    attack_coeff = np.exp(-1.0 / (SAMPLE_RATE * attack_ms / 1000))
    release_coeff = np.exp(-1.0 / (SAMPLE_RATE * release_ms / 1000))

    envelope = np.zeros(len(audio), dtype=np.float32)
    env = 0.0

    abs_audio = np.abs(audio)
    for i in range(len(audio)):
        if abs_audio[i] > env:
            env = attack_coeff * env + (1 - attack_coeff) * abs_audio[i]
        else:
            env = release_coeff * env + (1 - release_coeff) * abs_audio[i]
        envelope[i] = env

    # Calculate gain reduction
    gain = np.ones(len(audio), dtype=np.float32)
    above = envelope > threshold
    if np.any(above):
        db_over = 20 * np.log10(envelope[above] / threshold + 1e-10)
        db_reduction = db_over * (1 - 1 / ratio)
        gain[above] = 10 ** (-db_reduction / 20)

    # Makeup gain: compensate for average reduction
    avg_gain = np.mean(gain)
    if avg_gain > 0:
        makeup = 1.0 / avg_gain
        # Limit makeup to prevent clipping
        makeup = min(makeup, 10 ** (12 / 20))
        gain *= makeup

    return (audio * gain).astype(np.float32)


def reverb(audio, wet=0.15, decay=0.3):
    """Subtle room reverb using synthetic impulse response."""
    ir_len = int(SAMPLE_RATE * decay)
    ir = np.random.randn(ir_len).astype(np.float32)

    # Exponential decay envelope
    t = np.linspace(0, 1, ir_len)
    ir *= np.exp(-6 * t)

    # Band-limit the IR
    sos = butter(2, [300, 6000], btype="band", fs=SAMPLE_RATE, output="sos")
    ir = sosfiltfilt(sos, ir).astype(np.float32)

    # Normalize IR
    ir_peak = np.max(np.abs(ir))
    if ir_peak > 0:
        ir /= ir_peak

    # Convolve
    wet_signal = fftconvolve(audio, ir, mode="full")[:len(audio)].astype(np.float32)

    return ((1 - wet) * audio + wet * wet_signal).astype(np.float32)


def normalize_lufs(audio, target=-14.0):
    """Loudness normalize to target LUFS."""
    meter = pyln.Meter(SAMPLE_RATE)
    loudness = meter.integrated_loudness(audio)

    if np.isinf(loudness) or np.isnan(loudness):
        print("  Warning: could not measure loudness, skipping normalize")
        return audio

    return pyln.normalize.loudness(audio, loudness, target).astype(np.float32)


# Soft shows get gentle processing (no presence boost, light compression, quieter)
SOFT_SHOWS = {"bedtime"}


def process_file(wav_path, soft=False):
    """Apply full DSP chain to a single WAV file."""
    audio, sr = sf.read(str(wav_path), dtype="float32")

    # Handle stereo by processing as mono then restoring
    was_stereo = audio.ndim > 1
    if was_stereo:
        channels = []
        for ch in range(audio.shape[1]):
            channels.append(process_mono(audio[:, ch], soft))
        return np.column_stack(channels)
    else:
        return process_mono(audio, soft)


def process_mono(audio, soft=False):
    """DSP chain for a single mono signal."""
    audio = highpass(audio, 80)

    if soft:
        # Bedtime: gentle — no presence boost, light compression, quieter target
        audio = compress(audio, -18, 2.0, 10, 100)
        audio = normalize_lufs(audio, -18.0)
    else:
        # Broadcast: punchy and present
        audio = presence_boost(audio, 4000, 3.0)
        audio = compress(audio, -20, 3.0, 5, 50)
        audio = normalize_lufs(audio, -14.0)

    # Final clip protection
    audio = np.clip(audio, -1.0, 1.0)
    return audio


def postprocess_show(show_dir):
    """Process all WAVs in a show directory, backing up originals."""
    show_path = AUDIO_DIR / show_dir
    if not show_path.exists():
        print(f"Skipping {show_dir}: directory not found")
        return 0

    wav_files = sorted(show_path.glob("*.wav"))
    if not wav_files:
        print(f"Skipping {show_dir}: no WAV files")
        return 0

    # Backup originals
    raw_dir = show_path / "raw"
    raw_dir.mkdir(exist_ok=True)

    count = 0
    for wav in wav_files:
        backup = raw_dir / wav.name
        if not backup.exists():
            shutil.copy2(str(wav), str(backup))

        soft = show_dir in SOFT_SHOWS
        print(f"  Processing: {wav.name}{'  [soft]' if soft else ''}...", end=" ", flush=True)
        try:
            processed = process_file(wav, soft=soft)
            sf.write(str(wav), processed, SAMPLE_RATE)
            print("done")
            count += 1
        except Exception as e:
            print(f"ERROR: {e}")

    return count


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target == "all":
        # Process all show directories (skip sfx)
        show_dirs = [d.name for d in AUDIO_DIR.iterdir()
                     if d.is_dir() and d.name != "sfx"
                     and not d.name.startswith(".")]
    else:
        show_dirs = [target]

    total = 0
    for show_dir in sorted(show_dirs):
        print(f"\n{'='*50}")
        print(f"Post-processing: {show_dir}")
        print(f"{'='*50}")
        count = postprocess_show(show_dir)
        total += count

    print(f"\nDone! Processed {total} files total.")


if __name__ == "__main__":
    main()
