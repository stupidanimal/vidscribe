---
name: vidscribe
description: "Transcribe video/audio to text, generate subtitles, and summarize content. Use when user wants to 'extract text from video', 'transcribe audio', 'summarize a video', 'what does this video say', 'convert speech to text', 'add subtitles to video', or provides a video/audio file for analysis. Supports MP4, MKV, WebM, MP3, WAV, M4A and other formats. Also supports URL download (YouTube, etc.) via yt-dlp."
---

# vidscribe

Transcribe video/audio to text, generate subtitles, and summarize content. Runs 100% locally via faster-whisper (no API keys, no cloud).

## Setup (run once)

```bash
<skill_dir>/scripts/install.bat
```

Creates isolated venv at `<skill_dir>/venv/`. No conflicts with user's Python.

**Note**: First run downloads the Whisper model (~1GB, one-time). HuggingFace token is optional — without it, downloads are slower but still work. Set `HF_TOKEN` env var to speed up.

## Quick Reference

```bash
# Transcribe + generate SRT (default)
<skill_dir>/scripts/run.bat "video.mp4"

# Transcribe only (no SRT)
<skill_dir>/scripts/run.bat "video.mp4" --no-srt

# Transcribe + burn subtitles into video
<skill_dir>/scripts/run.bat "video.mp4" --burn

# Download from URL and transcribe
<skill_dir>/scripts/run.bat "https://youtube.com/watch?v=..."

# Batch process folder
<skill_dir>/scripts/run.bat "./videos/" --batch

# Check hardware (GPU/CPU, recommended model)
<skill_dir>/scripts/run.bat --info
```

## Output Files

For each video, generated alongside it:
```
video.mp4                ← source
video_transcript.txt     ← timestamped raw text
video.srt                ← subtitle file (--srt flag)
video_subtitled.mp4      ← video with hardcoded subtitles (--burn flag)
video_summary.md         ← LLM-generated summary (Step 2)
```

**Smart caching**: If `_transcript.txt` exists, transcription is skipped. If `_summary.md` exists, just read it.

## Step 1 — Transcribe

### Model selection

Model is auto-selected based on hardware. Override only if user specifies:

| User says | Model | Notes |
|-----------|-------|-------|
| "quick" / "fast" | `tiny` | Speed first |
| (default) | `auto` | Script decides based on GPU |
| "accurate" / "better quality" | `small` or `medium` | Non-English needs at least `small` |
| "best" / "highest quality" | `large-v3` | Slowest but most accurate |

Hardware auto-selection:
| Hardware | Auto Model | 30min video |
|----------|-----------|-------------|
| GPU 16GB+ | `medium` | ~1 min |
| GPU 4-8GB | `small` | ~30s |
| GPU <4GB | `base` | ~20s |
| CPU only | `tiny` | ~5 min |

### All options

- `--model`: `auto`, `tiny`, `base`, `small`, `medium`, `large-v3`
- `--language`: force language code (`en`, `zh`, `ja`, etc.)
- `--output`: custom output path
- `--batch`: process all media in folder
- `--srt`: generate SRT subtitle file (default: on)
- `--no-srt`: skip SRT generation
- `--burn`: burn subtitles permanently into video (user must explicitly request this)
- `--device`: `auto`, `cuda`, `cpu`
- `--info`: print hardware info and exit

## Step 2 — Summarize

**Language rule**: Summarize in the user's language, NOT the video's language.

Read the transcript, then produce:

### News / interview content:
- **Key Points** — main topics discussed
- **Notable Quotes** — exact quotes with speaker attribution if identifiable
- **Action Items** — decisions, announcements, next steps
- **TL;DR** — 2-3 sentence summary

### Technical / educational content:
- **Main Topic** — what is being taught/discussed
- **Key Concepts** — definitions and explanations
- **Code/Commands** — any technical details mentioned
- **TL;DR** — 2-3 sentence summary

## Troubleshooting

- **"ffmpeg not found"** — `winget install ffmpeg`
- **Garbled output** — specify `--language` explicitly
- **Too slow** — check GPU with `--info`, or use `tiny` model
- **Poor quality** — try `small` or `medium` model
- **GPU not detected** — needs CUDA toolkit + cuDNN; check `python -c "import torch; print(torch.cuda.is_available())"`
