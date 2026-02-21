"""
Generate a soft piano lullaby jingle for Bedtime Stories.
Synthesizes a gentle melodic phrase using piano-like tones.
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt
import soundfile as sf
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "audio" / "sfx"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100


def piano_note(freq, duration, velocity=0.4):
    """Synthesize a piano-like tone with harmonics and natural decay."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), dtype=np.float32)

    # Fundamental + harmonics (piano timbre)
    tone = np.zeros_like(t)
    harmonics = [
        (1.0, 1.0),    # fundamental
        (2.0, 0.5),    # 2nd harmonic
        (3.0, 0.2),    # 3rd
        (4.0, 0.1),    # 4th
        (5.0, 0.05),   # 5th
    ]
    for mult, amp in harmonics:
        tone += amp * np.sin(2 * np.pi * freq * mult * t)

    # Natural piano envelope: quick attack, exponential decay
    attack = int(SAMPLE_RATE * 0.01)
    envelope = np.exp(-t * 2.5)  # gentle decay
    envelope[:attack] *= np.linspace(0, 1, attack)

    tone *= envelope * velocity

    return tone


def generate_bedtime_jingle():
    """A gentle descending lullaby phrase — like a music box winding down."""

    # Notes: a gentle pentatonic lullaby melody
    # Using C major pentatonic in octave 4-5 for warmth
    notes = [
        # (frequency Hz, duration s, velocity)
        # Gentle opening phrase
        (523.25, 0.6, 0.35),   # C5
        (493.88, 0.6, 0.30),   # B4
        (440.00, 0.8, 0.32),   # A4
        (392.00, 0.5, 0.28),   # G4

        # Pause
        (0, 0.3, 0),

        # Descending resolution
        (440.00, 0.5, 0.30),   # A4
        (392.00, 0.5, 0.28),   # G4
        (329.63, 0.7, 0.30),   # E4
        (261.63, 1.2, 0.25),   # C4 — long, fading root

        # Pause
        (0, 0.4, 0),

        # Final gentle tag
        (392.00, 0.4, 0.22),   # G4
        (329.63, 0.5, 0.20),   # E4
        (261.63, 1.8, 0.22),   # C4 — long fade out
    ]

    segments = []
    for freq, dur, vel in notes:
        if freq == 0:
            segments.append(np.zeros(int(SAMPLE_RATE * dur), dtype=np.float32))
        else:
            segments.append(piano_note(freq, dur, vel))

    audio = np.concatenate(segments)

    # Soft low-pass to remove harshness
    sos = butter(4, 4000, btype="low", fs=SAMPLE_RATE, output="sos")
    audio = sosfiltfilt(sos, audio).astype(np.float32)

    # Gentle fade out on last 0.5s
    fade_len = int(SAMPLE_RATE * 0.5)
    audio[-fade_len:] *= np.linspace(1, 0, fade_len).astype(np.float32)

    # Normalize to -20dB peak (keep it soft)
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.1  # very soft

    out_path = OUTPUT_DIR / "bedtime_jingle.wav"
    sf.write(str(out_path), audio, SAMPLE_RATE)
    duration = len(audio) / SAMPLE_RATE
    print(f"Generated: {out_path} ({duration:.1f}s)")
    return str(out_path)


if __name__ == "__main__":
    generate_bedtime_jingle()
