# FORZEN.md — Dimension FM

*How to build an AI radio station that sounds like it's been on the air for decades.*

---

## What Is This?

Dimension FM is a fake radio station. Three shows, fake hosts, fake news, fake ads — all voiced by a 1.6-billion-parameter AI model running on your MacBook. No cloud, no API keys, no cost per word. Just your laptop's neural engine pretending to be a radio tower broadcasting across interdimensional frequencies.

The magic isn't in any single piece. It's in how the pieces stack: scripted content flows into a local TTS model, the raw audio gets shaped by a broadcast-quality DSP chain, and a browser-based player stitches it all together with playlist logic, channel-switch static, and a piano lullaby. Each layer adds a little more "realness" until you forget an AI made it.

---

## The Pipeline (How Audio Goes From Text to Your Ears)

Think of it like a recording studio assembly line:

```
Scripts (Python dicts)
    ↓
Dia TTS (mlx-audio, local inference)
    ↓
Raw WAV files (quiet, unprocessed)
    ↓
Post-Processing (scipy DSP chain)
    ↓
Broadcast-ready WAV files
    ↓
Web Player (vanilla JS, playlist system)
    ↓
Your ears
```

Every step is offline and deterministic. No network calls during playback. The player just fetches local files over a Python HTTP server.

---

## The TTS Layer: Dia Does the Talking

### How Dia Works

Dia is a text-to-speech model from Nari Labs. The `mlx-audio` package runs it natively on Apple Silicon — no CUDA, no Docker, no GPU rental. Generation runs at roughly 4-5x real-time (55 seconds to produce 12 seconds of audio), which is slow for live radio but fine for batch generation.

The killer feature: **multi-speaker synthesis in a single call.** You write:

```
[S1] Good morning, I'm Rick. [S2] And I'm Zara. Let's get into it.
```

And Dia generates one continuous audio file with two distinct voices. No stitching, no alignment, no gap-filling. The voices breathe naturally around each other because they were generated together.

### The Speaker Tag Trick

Most TTS workflows generate each speaker separately and stitch the clips together. That creates unnatural silences and mismatched breath patterns. Dia's `[S1]`/`[S2]` tags let it handle the conversation as one unit, the way a real recording session works — two people in one room, one microphone rolling.

### Dia's Quirks (Lessons Learned the Hard Way)

- **`(laughs)` tags are dangerous.** Tell Dia to laugh and it might burn all 3,000 tokens on a single extended chuckle. Keep emotional tags minimal.
- **Shorter scripts produce better audio.** 2-3 exchanges per segment is the sweet spot. Long monologues drift in quality.
- **`--max_tokens 3000` is the ceiling.** Enough for ~12-15 seconds of speech. Push further and quality degrades or inference hangs.

### The Manifest System

Each show directory contains a `manifest.json`:

```json
{
  "show": "Morning Show",
  "hosts": {"S1": "Rick", "S2": "Zara"},
  "segments": [
    {"index": 0, "path": "/full/path/to/morning_000_000.wav", "text": "[S1] ..."}
  ]
}
```

The web player loads these at startup to know what audio exists, what order to play it, and what text to show in the transcript. This decouples generation from playback — you can regenerate any segment without touching the player code.

---

## The DSP Layer: Making Raw TTS Sound Like Radio

Raw Dia output is... fine. It's intelligible. But it's quiet, flat, and clinical. It sounds like a computer reading text in an empty void. Real radio sounds warm, punchy, and present because every station runs audio through a broadcast processing chain.

Here's ours:

### Stage 1: High-Pass Filter (80Hz)

```python
sos = butter(4, 80, btype="high", fs=44100, output="sos")
audio = sosfiltfilt(sos, audio)
```

**What it does:** Removes everything below 80Hz — rumble, DC offset, low-frequency noise that TTS models sometimes produce.

**Why `sosfiltfilt` instead of `sosfilt`?** Regular filtering (`sosfilt`) processes audio forward through time, which introduces *phase lag* — high frequencies arrive slightly later than low frequencies. `sosfiltfilt` applies the filter forward AND backward, canceling the phase shift. The result sounds identical to the original but without the low-frequency content. Zero phase distortion is critical for speech because our ears are very sensitive to timing misalignments in consonants.

**Analogy:** Imagine reading a book with a yellow highlighter that bleeds slightly to the right. Forward-only filtering is like that bleed — the color (filter effect) shifts everything a tiny bit. `sosfiltfilt` highlights forward, then highlights backward over the same page, and the bleeds cancel out. Perfect color, no shift.

### Stage 2: Presence Boost (4kHz, +3dB)

```python
# Biquad peaking EQ filter
w0 = 2 * pi * 4000 / sample_rate
A = 10^(3.0 / 40)  # Convert dB to amplitude
```

**What it does:** Adds 3 decibels of gain centered at 4,000 Hz — the "presence peak" of human speech. This is where consonants like T, S, K, and P live. Boosting here makes voices sound crisp and close-up, like the speaker is leaning into the microphone.

**Why this matters for AI voices:** TTS models tend to produce speech that sounds slightly recessed, like the speaker is across the room. A presence boost brings them forward. It's the difference between "that voice is playing from a speaker" and "someone is talking to me."

**Skipped for bedtime.** Luna's storytelling should sound distant and dreamy, not bright and punchy.

### Stage 3: Broadcast Compression

This is the most complex stage and the one that makes the biggest audible difference.

**What compression does:** It reduces the gap between the loudest and quietest parts of the audio. When someone whispers, the compressor pushes the volume up. When they shout, it pulls it down. The result is audio that sits at a consistent, listenable level.

**How our compressor works:**

```python
# Envelope follower (exponential moving average)
for each sample:
    if current_amplitude > envelope:
        envelope moves toward amplitude FAST (5ms attack)
    else:
        envelope moves toward amplitude SLOWLY (50ms release)

    if envelope > threshold:
        reduce gain by (ratio - 1) / ratio
```

The **envelope follower** is the brain. It tracks the "loudness shape" of the audio by chasing peaks quickly (attack) and releasing slowly (release). This asymmetry is key — fast attack catches transients before they clip, slow release prevents pumping (that nauseating surge you hear in bad podcast audio).

**Two compression profiles:**

| Parameter | Broadcast (Morning/News/Ads) | Soft (Bedtime) |
|-----------|-----|---------|
| Threshold | -20dB | -18dB |
| Ratio | 3:1 | 2:1 |
| Attack | 5ms | 10ms |
| Release | 50ms | 100ms |
| Character | Punchy, radio-loud | Gentle, natural |

**Analogy:** Compression is like an automatic hand on the volume knob. Broadcast compression has a fast, aggressive hand that clamps down hard (3:1 means for every 3dB over the threshold, only 1dB gets through). Bedtime compression is a gentle hand that nudges softly (2:1, half as aggressive) with slower reflexes.

### Stage 4: Loudness Normalization (-14 LUFS / -18 LUFS)

```python
meter = pyln.Meter(44100)
loudness = meter.integrated_loudness(audio)
audio = pyln.normalize.loudness(audio, loudness, target_lufs)
```

**Why LUFS instead of dBFS?** dBFS measures the peak amplitude of the digital signal. LUFS (Loudness Units relative to Full Scale) measures *perceived* loudness using a psychoacoustic model that accounts for how human ears work. Two audio files at -14 dBFS can sound wildly different in volume. Two files at -14 LUFS sound the same.

**The targets:**
- **-14 LUFS** for broadcast shows. This is the standard for streaming platforms (Spotify, YouTube). Loud enough to hear clearly, not so loud that it distorts.
- **-18 LUFS** for bedtime. Deliberately quieter. You're lying in bed with earbuds. The last thing you want is Luna suddenly shouting at you.

### The Backup System

Before processing, every original WAV gets copied to a `raw/` subdirectory. This means you can always re-process from scratch — change the compression ratio, tweak the EQ, try a different LUFS target — without needing to regenerate from Dia (which takes ~5 minutes per show).

---

## The SFX Layer: Small Sounds, Big Immersion

### Channel Switch Static (0.4 seconds)

```python
noise = np.random.randn(n_samples)      # White noise
crackle[sparse_indices] = randn() * 3.0  # Sparse loud pops
filtered = bandpass(200Hz, 8kHz)          # Shape the frequency range
```

This is 0.4 seconds of synthesized radio static that plays when you switch channels. It's built from three ingredients:

1. **Gaussian white noise** — every frequency at equal power, completely random
2. **Crackle impulses** — 0.3% of samples get random spikes at 3x amplitude, simulating vinyl pops
3. **Band-pass filter** — chops off frequencies below 200Hz (too rumbly) and above 8kHz (too hissy)

Add 20ms fades at each end to prevent clicks, normalize to -6dB so it doesn't blast your ears, done. The whole thing runs in under a second.

**Why it matters:** Channel switching in silence feels broken. Channel switching with a 200ms burst of static feels *physical*, like turning a real radio dial.

### Bedtime Piano Jingle (8.8 seconds)

This one's more interesting. It's a synthesized piano playing a descending C-major pentatonic lullaby:

```
C5 → B4 → A4 → G4 → [pause] → A4 → G4 → E4 → C4 → [pause] → G4 → E4 → C4 (long fade)
```

**The piano tone synthesis:**

A real piano string vibrates at a fundamental frequency plus overtones (harmonics). We approximate this with additive synthesis:

```python
tone = sin(freq * 1) * 1.00   # Fundamental
     + sin(freq * 2) * 0.50   # 2nd harmonic (octave)
     + sin(freq * 3) * 0.20   # 3rd harmonic (fifth)
     + sin(freq * 4) * 0.10   # 4th harmonic (double octave)
     + sin(freq * 5) * 0.05   # 5th harmonic (major third)
```

Each harmonic adds warmth and richness. A single sine wave sounds like a tuning fork. Five harmonics with decaying amplitudes sounds like a piano (well, a music box — close enough for a radio jingle).

**The envelope:** Real piano notes hit hard and decay exponentially. We simulate this with a 10ms linear attack and an `exp(-2.5 * t)` decay curve — fast enough to sound percussive, slow enough to sustain.

**Why pentatonic?** The pentatonic scale has no half-step intervals, which means every note sounds consonant with every other note. You literally cannot play a wrong note. Descending motion creates a feeling of resolution and rest — perfect for "time to sleep."

**Post-processing:** A 4kHz low-pass filter removes harmonic harshness, and the whole thing is normalized to -20dB peak (very quiet). This jingle should feel like it's playing from another room.

---

## The Web Player: A Radio in Your Browser

### Architecture

The entire player is one HTML file — 430 lines of CSS, 250 lines of JS, zero dependencies. No React, no build step, no npm. Just `<audio>` elements and event listeners.

**State is simple:**
```javascript
let currentShow = "morning";
let playlist = [];        // [{show, path, text, isAd, isJingle}, ...]
let playlistIdx = 0;
let isPlaying = false;
let audioEl = new Audio();        // Main playback
let staticEl = new Audio("static.wav");  // SFX (separate element)
```

Two `Audio` elements run independently. The main one plays show content; the static one fires during channel switches. They don't interfere because static only plays while main is paused.

### The Playlist System

This is the core architectural decision. Instead of pointing directly at manifest segments, the player builds a **playlist array** that interleaves show content with ads:

```
[show_seg_0, show_seg_1, AD, show_seg_2, show_seg_3, AD, show_seg_4, ...]
```

An ad gets inserted every 2 segments. Ads cycle through the available pool using modulo:

```javascript
const ad = adManifest.segments[adIdx % adManifest.segments.length];
```

Six ads, unlimited cycling. The badge changes to "AD BREAK" in warm yellow, then flips back to "ON AIR" when the show resumes.

**Bedtime gets special treatment:**
1. Piano jingle is prepended as the first playlist item
2. The old spoken intro segment (index 0) is skipped — the jingle replaces it

### Episode Merging

Morning has two episode directories: `morning/` (7 segments) and `morning_ep2/` (6 segments). At load time, the player merges them:

```javascript
const ep2Segs = manifests.morning_ep2.segments.map((seg, i) => ({
  ...seg,
  _show: "morning_ep2",  // Remember where the file actually lives
}));
manifests.morning.segments = [...manifests.morning.segments, ...ep2Segs];
```

The `_show` field is the key trick. When loading audio, the player uses `_show` to build the correct file path (`audio/morning_ep2/filename.wav` instead of `audio/morning/filename.wav`). From the user's perspective, it's one seamless 13-segment morning show.

This pattern scales. Add `morning_ep3/`, `morning_ep4/` — the player treats them all as one show. No UI changes needed.

### Time-Based Defaults

```javascript
const h = new Date().getHours();
if (h >= 6 && h < 12) return "morning";
else if (h >= 12 && h < 22) return "news";
else return "bedtime";
```

Open the player at 8 AM and you get the Morning Show. Open it at midnight and you get Bedtime Stories. It's a small detail, but it makes the station feel *alive* — like it's been running all day whether you're listening or not.

### Volume Persistence

Volume state survives page refreshes via `localStorage`. The mute button remembers your previous volume level. Static SFX plays at 50% of the main volume (it shouldn't compete with speech, just provide texture).

---

## Project Structure

```
dia-radio/
├── scripts/
│   ├── generate_shows.py       # 5 show dicts + Dia TTS invocation
│   ├── postprocess.py          # 4-stage DSP chain (soft mode for bedtime)
│   ├── generate_static.py      # Band-limited noise + crackle synthesis
│   └── generate_jingle.py      # Piano lullaby (additive synthesis)
├── audio/
│   ├── morning/                # 7 segments + manifest.json + raw/
│   ├── morning_ep2/            # 6 segments (merged into morning at runtime)
│   ├── news/                   # 6 segments
│   ├── bedtime/                # 6 segments (soft DSP profile)
│   ├── ads/                    # 6 fake interdimensional product ads
│   └── sfx/                    # static.wav, bedtime_jingle.wav
├── web/
│   └── index.html              # Complete player (single file, zero deps)
├── ROADMAP.md                  # 5-phase upgrade plan
└── README.md                   # Quick start + feature list
```

---

## Bugs We Hit and How We Fixed Them

### Bug: "Everything sounds echoey and hollow"

**Cause:** The original DSP chain included synthetic reverb (`wet=0.15`). Even at 15% mix, the reverb tail added a noticeable void/echo quality to all speech.

**Fix:** Removed reverb entirely. Voices should sound dry and close — like a podcast mic, not a cathedral.

**Lesson:** Reverb is almost never what you want on synthesized speech. Real radio stations add *room tone* (constant low-level background noise) for warmth, not reverb tails. Save reverb for music production.

### Bug: "Radio static plays between every segment"

**Cause:** The `ended` event handler played 300ms of static before loading the next segment. This made sense conceptually (radio transitions!) but felt annoying in practice.

**Fix:** Static only plays on channel switch (200ms). Segments within a show advance silently.

**Lesson:** Sound design is about restraint. An effect that's cool the first time becomes grating by the 10th. Channel switches are rare enough to feel special. Segment transitions happen every 12 seconds — static there is just noise.

### Bug: "Bedtime stories sound harsh and aggressive"

**Cause:** Bedtime was getting the same DSP chain as the morning show — 3:1 compression, 4kHz presence boost, -14 LUFS loudness. These are *broadcast* settings designed to make voices punch through car speakers and coffee shop chatter. Exactly wrong for a lullaby.

**Fix:** Created a "soft" DSP profile: no presence boost, gentler 2:1 compression, slower attack/release, and -18 LUFS target (4dB quieter than broadcast).

**Lesson:** One size doesn't fit all in audio processing. A podcast, a morning zoo show, and a bedtime story need fundamentally different dynamics. Always ask "what's the listening context?" before choosing DSP parameters.

### Bug: "The bedtime intro segment sounds terrible after the piano"

**Cause:** The synthesized piano jingle was gentle and atmospheric. Then Dia's spoken "Welcome to Dimension FM bedtime stories..." segment hit with a completely different energy. The contrast was jarring.

**Fix:** Skipped the first bedtime segment entirely. The piano jingle *is* the intro now.

**Lesson:** When you have a better version of something, don't play both. Replace, don't append.

---

## Things I'd Do Differently Next Time

1. **Generate multiple takes.** Dia's output varies between runs. Some takes are dramatically better than others. Generating 3 takes per segment and picking the best would significantly improve overall quality for minimal extra time.

2. **Room tone instead of reverb.** A constant low-level background hum (air conditioning, room ambience) under all speech makes it feel "placed" in a physical space without the echo of reverb. Record 30 seconds of your room's ambient noise, loop it, mix at -30dB under speech.

3. **Gapless playback from the start.** The HTML5 `<audio>` element has a small gap (~100ms) when switching sources. Web Audio API with pre-buffered segments would eliminate this. Not critical for radio format, but would make it feel more polished.

4. **Script generation with LLMs.** All show scripts are hand-written in Python dicts. A Claude API call could generate unlimited episodes with consistent character voices and running jokes. The infrastructure supports it — just add segments to the SHOWS dict and regenerate.

---

## How Good Engineers Think About This

### "Audio-First" Workflow

The temptation with a project like this is to build the player first and worry about content later. That's backwards. **Audio quality is the product.** If the TTS sounds robotic, no amount of UI polish saves it. If the DSP chain makes everything sound underwater, nobody will use the beautiful volume slider.

The right order: script good content → generate audio → listen critically → fix the audio → *then* build the player. We got the player working early (prototype), but every subsequent improvement was audio-focused: adding compression, fixing the bedtime profile, synthesizing jingles.

### The "Good Enough" Threshold

The piano jingle is not a real piano. The equalizer bars don't react to actual audio frequencies. The "radio static" is band-limited noise, not a recording of real static. None of these need to be perfect. They need to cross the *recognition threshold* — the point where your brain goes "oh, that's a piano" or "oh, that's radio static" and stops analyzing.

Once you cross that threshold, adding more realism has diminishing returns. A sample-accurate piano model would sound 5% better and take 100x more effort. Know where the threshold is and stop there.

### Separation of Concerns

The generation pipeline and the player are completely decoupled. `generate_shows.py` knows nothing about HTML. `index.html` knows nothing about Dia. They communicate through one interface: `manifest.json` files and WAV files in predictable directories.

This means you can:
- Swap Dia for a different TTS model without touching the player
- Rewrite the player in React without regenerating audio
- Add new shows by just creating a new directory with a manifest
- Re-process all audio without changing anything else

Each piece has one job. That's not accidental — it's the difference between a prototype that works and a prototype that can grow.

---

## Tech Stack Reference

| Component | Choice | Why |
|-----------|--------|-----|
| TTS | Dia 1.6B (mlx-audio) | Runs locally on Apple Silicon, multi-speaker, free |
| DSP | scipy + numpy | Butter filters, FFT convolution, standard DSP toolkit |
| Loudness | pyloudnorm | Industry-standard LUFS measurement |
| Audio I/O | soundfile | Fast WAV read/write, supports all sample rates |
| Frontend | Vanilla HTML/CSS/JS | Zero deps, full audio control, single file deploy |
| Player | HTML5 `<audio>` | Native, no polyfills, good enough for sequential playback |
| Server | `python3 -m http.server` | Dev only, ships pre-generated content |

---

*Built with Dia 1.6B on Apple Silicon. No cloud APIs were harmed in the making of this radio station.*
