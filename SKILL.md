---
name: video-to-summary
description: "Transcribe audio/video files to text and summarize content. Use when user wants to 'extract text from video', 'transcribe audio', 'summarize a video', 'what does this video say', 'convert speech to text', or provides a video/audio file for analysis. Supports MP4, MKV, WebM, MP3, WAV, M4A, and other common formats."
---

# Video-to-Summary

Extract text from video/audio, then summarize the content.

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

Run the bundled script:

```bash
# Local file
python <skill_dir>/scripts/transcribe.py "<input_file>" --model base

# URL (auto-download via yt-dlp)
python <skill_dir>/scripts/transcribe.py "https://youtube.com/watch?v=..." --model base

# Batch (all media in folder)
python <skill_dir>/scripts/transcribe.py "<folder>" --batch --model tiny
```

Options:
- `--model`: `tiny` (fastest, ~1GB RAM), `base` (default, good balance), `small` (better quality), `medium` (high quality, slow), `large-v3` (best, very slow on CPU)
- `--language`: force language code (`en`, `zh`, `ja`, etc.) — skip auto-detect if known
- `--output`: output file path
- `--batch`: process all media files in a folder

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

| Use case | Model | Time (10min audio) | RAM |
|----------|-------|-------------------|-----|
| Quick draft | `tiny` | ~30s | ~1GB |
| General use | `base` | ~1min | ~1GB |
| Good quality | `small` | ~3min | ~2GB |
| High quality | `medium` | ~10min | ~5GB |
| Best (English) | `large-v3` | ~30min | ~10GB |

For non-English content, use at least `small` model for decent quality.

## Troubleshooting

- **"ffmpeg not found"** — install: `winget install ffmpeg`
- **Garbled output** — try specifying `--language` explicitly
- **Too slow** — use `tiny` model, or `base` for balance
- **Poor quality** — try `small` or `medium` model
- **GPU acceleration** — requires CUDA; CPU works fine for short files
