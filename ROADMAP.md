# Dimension FM — Upgrade Roadmap

## Current State (v0.1 Prototype)
- 3 shows: Morning Show, Interdimensional News, Bedtime Stories
- 19 pre-generated audio segments via Dia 1.6B (local MLX)
- Web player with channel switching, visualizer, transport controls
- ~55s generation time per ~12s segment (4-5x real-time on Apple Silicon)

---

## Phase 1: Make It Sound Alive
**Goal:** Audio quality that doesn't feel like AI

### 1.1 Post-Processing Pipeline
- [ ] Add broadcast compression (radio loudness, ~-14 LUFS)
- [ ] Apply subtle room reverb (small studio feel)
- [ ] Layer room tone / studio ambience under all speech
- [ ] EQ processing (high-pass filter, presence boost around 3-5kHz)
- [ ] Use `pyloudnorm` (already installed) + `pedalboard` for effects chain
- Tool: Write a `scripts/postprocess.py` that takes raw Dia output → broadcast-ready WAV

### 1.2 Sound Design Between Segments
- [ ] Channel static / white noise transition (0.5s between segments)
- [ ] Per-show jingle/bumper (generate with Suno/Udio free tier, or synthesize)
- [ ] Background music beds (low volume, ducked under speech)
- [ ] Sound effects: paper rustling, coffee mug, chair creak (freesound.org)

### 1.3 Better Voice Direction
- [ ] Experiment with Dia's `(laughs)` `(sighs)` `(whispers)` tags — use sparingly
- [ ] Try different text pacing: em dashes for pauses, ellipsis for trailing off
- [ ] Generate multiple takes per segment, pick the best one
- [ ] Test CSM (Sesame) as alternative — may handle emotion better for bedtime stories

---

## Phase 2: More Content, More Shows
**Goal:** Enough variety to listen for 30+ minutes without repeats

### 2.1 More Show Formats
- [ ] **Interdimensional Ads** — 15-30 second fake product commercials (insert between segments)
- [ ] **Phone-In Show** — "callers" asking weird questions, host answers
- [ ] **Cooking Show** — step-by-step instructions that slowly go wrong
- [ ] **Court TV** — two parties arguing absurd cases
- [ ] **Late Night Monologue** — solo host, stand-up style
- [ ] **Music Hour** — AI-generated jingles + host commentary (Suno integration)
- [ ] **Weather Report** — standalone 30s weather from weird dimensions

### 2.2 LLM-Generated Scripts (Dynamic Content)
- [ ] Use Claude API (or local Llama) to generate new scripts on demand
- [ ] Prompt templates per show format with tone/style guides
- [ ] "Topic of the day" system — scripts reference current date, trending topics
- [ ] Character bible: consistent personality traits per host across episodes

### 2.3 Episode System
- [ ] Generate full "episodes" (5-10 segments = 2-5 min continuous show)
- [ ] Episode numbering and archives
- [ ] "Previously on Dimension FM" callbacks

---

## Phase 3: Continuous Playback Engine
**Goal:** Open it, something's always playing. Come back later, different content.

### 3.1 Pre-Buffer Architecture
- [ ] Background generation: always stay 2-3 segments ahead
- [ ] Segment queue with crossfade between clips
- [ ] Show scheduler: auto-switch shows based on time of day
- [ ] Shuffle mode within a show (randomize segment order)
- [ ] "Endless" mode: when show runs out, generate more on the fly

### 3.2 Audio Stitching
- [ ] Seamless concatenation with crossfade (avoid pops/clicks between segments)
- [ ] Web Audio API for gapless playback (instead of basic `<audio>` element)
- [ ] Pre-load next segment while current one plays

---

## Phase 4: Real-Time Generation (The Dream)
**Goal:** Fully live, never-repeating radio

### 4.1 Pipeline
```
LLM (script) → Dia (voice) → PostFX → Web Audio API → Speaker
     ~2s          ~55s         ~1s        instant
```
- Current bottleneck: Dia generation at 4-5x real-time
- Need: ~1x real-time or faster for true live generation
- Options:
  - [ ] Dia2 (streaming variant) — investigate if faster on MLX
  - [ ] Quantized model (Dia-1.6B-4bit) — trade quality for speed
  - [ ] Shorter segments (5-8 seconds) — faster to generate, stitch more often
  - [ ] GPU server option — Replicate/Modal free tier for faster inference

### 4.2 Dia2 Streaming
- [ ] Test nari-labs/dia2 — designed for streaming generation
- [ ] Can start playing audio while still generating the rest
- [ ] Would fundamentally change architecture from pre-gen to real-time

---

## Phase 5: Polish & Ship
**Goal:** Something people actually want to use

### 5.1 UI Upgrades
- [ ] Time-of-day ambient lighting (warm morning → cool night → dark bedtime)
- [ ] Animated character portraits per host (AI-generated, swap expressions)
- [ ] Show schedule sidebar (what's on, what's coming up)
- [ ] Volume control + mute
- [ ] Mobile responsive layout
- [ ] PWA support (installable, works offline with cached episodes)
- [ ] Keyboard shortcut overlay (? to show)

### 5.2 CRT / Retro Mode (Optional)
- [ ] Toggle: modern clean vs CRT scanline aesthetic
- [ ] CRT screen curvature via CSS filter
- [ ] VHS tracking glitch on channel switch
- [ ] Pixel font mode

### 5.3 Deploy
- [ ] Static export (pre-generated audio + player) → Vercel/Netlify
- [ ] Or: Next.js app with API routes for on-demand generation
- [ ] Custom domain: dimensionfm.com or similar
- [ ] OG image + meta tags for social sharing
- [ ] RSS feed (podcast format) — distribute as actual podcast

### 5.4 Community / Viral Features
- [ ] "Submit a topic" — listeners suggest show topics
- [ ] Share clip feature — select 15s of a show, generate shareable link
- [ ] Channel surfing animation (like flipping through real radio stations)
- [ ] Easter egg channels (hidden shows at certain times)

---

## Tech Debt / Improvements
- [ ] Replace Python http.server with proper dev server (Vite or similar)
- [ ] Git init + push to GitHub
- [ ] Separate show scripts from generation logic
- [ ] Add a `--dry-run` flag to preview scripts without generating
- [ ] Batch generation with progress tracking
- [ ] Audio file cleanup (delete old generations)
- [ ] Error recovery if generation fails mid-show

---

## Quick Wins (Do Next Session)
1. **Post-processing pipeline** — biggest bang for buck on audio quality
2. **Fake ads between segments** — easiest new content, high comedy value
3. **Channel switch static sound** — tiny detail, huge feel improvement
4. **Volume control** — basic UX
5. **Generate more morning show episodes** — different topics, same hosts
