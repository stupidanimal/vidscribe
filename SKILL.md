---
name: video-to-summary
description: "Transcribe audio/video files to text and summarize content. Use when user wants to 'extract text from video', 'transcribe audio', 'summarize a video', 'what does this video say', 'convert speech to text', or provides a video/audio file for analysis. Supports MP4, MKV, WebM, MP3, WAV, M4A, and other common formats."
---

# Video-to-Summary

Extract text from video/audio, then summarize the content.

## Preflight Check (run once)

Before first use, check dependencies. Run these commands and install if missing:

```bash
# Check ffmpeg
ffmpeg -version 2>$null || winget install ffmpeg

# Check Python packages
python -c "import faster_whisper" 2>$null || pip install faster-whisper
python -c "import yt_dlp" 2>$null || pip install yt-dlp

# Check GPU (optional, for speed)
python -c "import torch; assert torch.cuda.is_available()" 2>$null && echo "GPU OK" || echo "CPU only"
```

If `<skill_dir>/scripts/install.bat` exists, run it for one-click setup.

## Pipeline

1. **Extract audio** — ffmpeg pulls audio track from video
2. **Transcribe** — faster-whisper converts speech to timestamped text
3. **Save** — transcript.txt + summary.md saved next to source video
4. **Summarize** — LLM reads transcript and produces summary

## Output Structure

For each video, two files are generated alongside it:
```
video.mp4
video_transcript.txt    ← timestamped raw text (reuse on next visit)
video_summary.md        ← structured summary (reuse on next visit)
```

Check for existing files before re-running. If `_summary.md` exists, just read it.

## Step 1 — Transcribe

### Check hardware first

```bash
python <skill_dir>/scripts/transcribe.py --info
```

This prints GPU/CPU and recommended model. Use this to decide which model to use.

### Model selection guide

| User intent | Model | When to use |
|-------------|-------|-------------|
| "just need it fast" / "quick draft" | `tiny` | Speed first, quality doesn't matter |
| No preference / default | `auto` | Let script decide based on hardware |
| "better quality" / "accurate" | `small` or `medium` | Non-English needs at least `small` |
| "best quality" / "highest accuracy" | `large-v3` | Not urgent, need best results |

### Run transcription

```bash
# Local file (auto model)
python <skill_dir>/scripts/transcribe.py "<input_file>"

# Force specific model
python <skill_dir>/scripts/transcribe.py "<input_file>" --model small

# URL (auto-download via yt-dlp)
python <skill_dir>/scripts/transcribe.py "https://youtube.com/watch?v=..."

# Batch (all media in folder)
python <skill_dir>/scripts/transcribe.py "<folder>" --batch
```

Options:
- `--model`: `auto` (default, hardware-based), `tiny`, `base`, `small`, `medium`, `large-v3`
- `--language`: force language code (`en`, `zh`, `ja`, etc.) — skip auto-detect if known
- `--output`: output file path
- `--batch`: process all media files in a folder
- `--info`: print hardware info and exit (no transcription)

The script auto-detects video vs audio input. Video files get audio extracted via ffmpeg first. If transcript already exists, it skips (no re-processing).

Output format — one line per segment with timestamp:
```
[00:15] Hello and welcome to the show.
[00:22] Today we're talking about AI.
```

## Step 2 — Summarize

**Language rule**: Output the summary in the same language the user is writing in, NOT the language of the video. If the user asks in Chinese, summarize in Chinese. If they ask in English, summarize in English. The transcript stays in the original language.

**Save outputs**: Always save both files alongside the source video:
- `<video_name>_transcript.txt` — raw transcript with timestamps
- `<video_name>_summary.md` — structured summary

If both files already exist, skip transcription and just read the summary. If only transcript exists, skip transcription and go straight to summarizing. This avoids re-consuming tokens on repeat visits.

Read the transcript file, then produce:

### For news/interview content:
- **Key Points** — bullet list of main topics discussed
- **Notable Quotes** — exact quotes with speaker attribution if identifiable
- **Action Items** — any decisions, announcements, or next steps mentioned
- **TL;DR** — 2-3 sentence summary

### For technical/educational content:
- **Main Topic** — what is being taught/discussed
- **Key Concepts** — definitions and explanations
- **Code/Commands** — any technical details mentioned
- **TL;DR** — 2-3 sentence summary

## Model Selection Guide

Model and device are auto-detected. No need to specify unless you want to override.

| Hardware | Auto Model | Speed (30min video) | Quality |
|----------|-----------|---------------------|---------|
| GPU (16GB+) | `medium` | ~1 min | High |
| GPU (4-8GB) | `small` | ~30s | Good |
| GPU (<4GB) | `base` | ~20s | OK |
| CPU only | `tiny` | ~5 min | Draft |

Options:
- `--model auto` — auto-select based on GPU (default)
- `--model small` — force specific model
- `--device auto` — auto-detect GPU (default)
- `--device cuda` — force GPU
- `--device cpu` — force CPU

## Troubleshooting

- **"ffmpeg not found"** — install: `winget install ffmpeg`
- **Garbled output** — try specifying `--language` explicitly
- **Too slow** — use `--device cuda` for GPU, or `tiny` model for CPU
- **Poor quality** — try `small` or `medium` model
- **GPU not detected** — ensure CUDA toolkit + cuDNN installed; check `python -c "import torch; print(torch.cuda.is_available())"`
