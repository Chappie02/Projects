# Real-Time Speaker Isolation & Identification (CLI + Web)

Python 3.11+ CLI and simple Flask web app to separate speakers, label tracks, and transcribe an input MP3.

## Setup

1. Ensure FFmpeg is installed and on PATH.
2. Create a virtual environment (Python 3.11+), then install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## CLI Usage

```bash
python main.py input.mp3 --output /path/to/output --num-speakers 2 --whisper-model base
```

- `--num-speakers`: 2 or 3 (selects SepFormer model wsj02mix/wsj03mix)
- `--whisper-model`: tiny|base|small|medium|large (default: base)

Outputs are written to the output directory:
- `speaker_1.wav`, `speaker_2.wav`, ...
- `transcript.json` and `transcript.txt`

## Web App

Run the Flask server:

```bash
export FLASK_APP=web/app.py
python web/app.py
# then open http://localhost:5000
```

- Upload an MP3/WAV, choose number of speakers and Whisper model.
- Results page shows download links for separated tracks and transcripts.
- A ZIP of all outputs is also available.

## Notes
- First run downloads pretrained models (SepFormer, Whisper).
- For best results, provide relatively clean two or three-speaker audio.
