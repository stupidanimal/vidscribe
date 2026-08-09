# vidscribe

An AI Agent Skill that transcribes video/audio to text, generates subtitles, and summarizes content. Works with Claude Code, Codex, Gemini CLI, and other agent CLIs that support the Agent Skills standard.

The heavy lifting is done by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (local Whisper implementation). The skill wraps it into an agent-friendly workflow with smart caching and structured output.

## What it does

```
Video/Audio → ffmpeg extracts audio → faster-whisper transcribes → SRT subtitles → LLM summarizes
```

## Features

- **Isolated environment** — venv auto-created, no conflicts with user's Python
- **100% local transcription** — no cloud, no API keys, no data leaves your machine
- **99+ languages** — English, Chinese, Japanese, etc.
- **Auto model selection** — picks best model based on GPU/CPU
- **Smart caching** — skips transcription if transcript exists
- **URL download** — YouTube, Bilibili, etc. via yt-dlp
- **Batch mode** — process entire folder
- **Subtitles** — generate SRT files or burn subtitles into video
- **AI narration** — Chinese/English TTS via edge-tts (free, no API key)
- **Douyin video pipeline** — transcription + narration + jimeng image generation + slideshow

## Quick Start

```bash
# One-click install (creates isolated venv)
scripts/install.bat

# Transcribe + generate SRT subtitles (default)
scripts/run.bat "video.mp4"

# Transcribe only (no SRT)
scripts/run.bat "video.mp4" --no-srt

# Burn subtitles into video
scripts/run.bat "video.mp4" --burn

# Download from URL
scripts/run.bat "https://youtube.com/watch?v=..."

# Batch process
scripts/run.bat "./videos/" --batch
```

## Output

For each video:
- `<name>_transcript.txt` — timestamped raw text
- `<name>.srt` — subtitle file (SRT format)
- `<name>_subtitled.mp4` — video with hardcoded subtitles
- `<name>_summary.md` — LLM-generated summary

## License

MIT
