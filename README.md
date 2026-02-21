# Dimension FM

AI-powered radio station that generates shows with different formats throughout the day. Built with Dia TTS (Nari Labs) running locally on Apple Silicon via MLX.

## Quick Start

```bash
# Activate the Python environment
source ~/dia-radio/bin/activate

# Start local server
cd ~/dia-radio && python3 -m http.server 8888

# Open player
open http://localhost:8888/web/
```

## Generate New Audio

```bash
source ~/dia-radio/bin/activate

# Generate a specific show
python scripts/generate_shows.py morning
python scripts/generate_shows.py news
python scripts/generate_shows.py bedtime

# Generate all shows
python scripts/generate_shows.py all
```

## Project Structure

```
dia-radio/
├── web/
│   └── index.html          # Radio player UI
├── scripts/
│   └── generate_shows.py   # Show script definitions + Dia TTS generation
├── audio/
│   ├── morning/             # 7 segments + manifest.json
│   ├── news/                # 6 segments + manifest.json
│   └── bedtime/             # 6 segments + manifest.json
├── bin/lib/                  # Python venv (Dia + MLX)
└── ROADMAP.md               # Upgrade plan
```

## Tech Stack

- **TTS**: Dia 1.6B via mlx-audio (local, zero cost)
- **Frontend**: Vanilla HTML/CSS/JS
- **Server**: Python http.server (dev only)
- **Model**: mlx-community/Dia-1.6B-fp16

## Controls

- `Space` — play/pause
- `←` `→` — prev/next segment
- `1` `2` `3` — switch channels
