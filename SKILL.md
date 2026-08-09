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

## Step 3 — Narrate (optional)

Generate AI narration for the video. This is a **two-step process**:

### Step 3a: Generate LLM prompt

```bash
<skill_dir>/scripts/run_narrate.bat "video.mp4" --lang zh
```

This outputs a prompt file. **Agent must read it and call LLM** to generate narration text:
- Summarize key points (not word-for-word translation)
- Translate to target language
- Use professional anchor tone
- Remove filler words

Save the LLM output to a `.txt` file.

### Step 3b: Generate narration audio

```bash
<skill_dir>/scripts/run_narrate.bat "video.mp4" --narration-text <your-file.txt> --lang zh --voice zh-CN-YunyangNeural
```

This generates TTS audio and combines with video.

### Options

- `--lang zh`: Target language (zh/en/ja)
- `--style summary`: Summarize (default) or `--style full`: complete translation
- `--voice`: TTS voice (default: auto-detect)
- `--replace`: Replace original audio (default: mix at 20% original)
- `--rate +20%`: Speech rate

### Available voices

| Language | Voice | Style |
|----------|-------|-------|
| Chinese | `zh-CN-YunyangNeural` | Male, professional |
| Chinese | `zh-CN-XiaoxiaoNeural` | Female, friendly |
| English | `en-US-BrianNeural` | Male, professional |
| English | `en-US-AriaNeural` | Female, professional |

Output files:
- `<name>_narration.mp3` — narration audio
- `<name>_narrated.mp4` — video with narration mixed in

## Douyin Workflow

When user asks for a "Douyin video" or "抖音视频", generate a complete package:

### Step 1: Transcribe

```bash
<skill_dir>/scripts/run.bat "video.mp4" --no-srt
```

### Step 2: Narrate

Agent generates Chinese narration (summary, not translation). Then generate TTS:

```python
import asyncio, edge_tts
async def main():
    with open('narration.txt', 'r') as f: text = f.read()
    c = edge_tts.Communicate(text, 'zh-CN-YunyangNeural', rate='+10%')
    await c.save('narration.mp3')
asyncio.run(main())
```

### Step 3: Generate images

Split narration into 5-6 segments. For each, generate image with jimeng-cli:

```bash
npx jimeng-cli image generate \
  --prompt "内容描述, 中文文字标题, 高质量设计, no watermark no frame" \
  --model jimeng-4.5 --ratio 9:16 --resolution 2k --output-dir ./images/ --wait
```

**Prompt tips**: Include key text in prompt, dark backgrounds, add "no watermark no frame".

### Step 4: Combine video

```bash
ffmpeg -y -f concat -safe 0 -i concat.txt -i narration.mp3 \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" \
  -c:v libx264 -profile:v baseline -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart -shortest output.mp4
```

### Step 5: Generate Douyin metadata

After narration, generate:

1. **Title** (标题)
   - Max 30 characters
   - Hook + key insight
   - Example: "马斯克：2036年金钱将不再重要"

2. **Description** (简介)
   - 3-5 bullet points summarizing key insights
   - Include relevant hashtags
   - Example:
   ```
   马斯克最新专访核心观点：
   • 到2036年金钱将不再重要
   • AI和机器人将使商品极度丰富
   • 通缩只惠及一半经济
   • 真实生活成本继续上涨
   #马斯克 #AI #经济学人 #科技 #财经
   ```

3. **Save to file**: `<name>_douyin.txt`

### Step 3: Package output

```
<name>_narrated.mp4      ← 视频（可直接上传）
<name>_narration.mp3     ← 纯音频（备用）
<name>_douyin.txt         ← 标题+简介+标签
<name>_transcript.txt     ← 原始转录（留档）
```

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

## GPU & venv notes (agent guidance)

- `install.bat` creates an isolated venv with only faster-whisper + yt-dlp (**no torch**).
  Inside the venv, `detect_device()` falls back to CPU → `tiny`. That is expected, not an error.
- If the user's system Python has torch + CUDA (e.g. anaconda), running
  `<skill_dir>/scripts/transcribe.py` directly with the system interpreter enables GPU
  and auto-selects a bigger model. Verify with `--info` before assuming GPU.
- To enable GPU inside the venv: `pip install torch --index-url https://download.pytorch.org/whl/cu121` (large download; optional).
- Never assume GPU — always check `--info` output first.

## Troubleshooting

- **"ffmpeg not found"** — `winget install ffmpeg`
- **Garbled output** — specify `--language` explicitly
- **Too slow** — check GPU with `--info`, or use `tiny` model
- **Poor quality** — try `small` or `medium` model
- **GPU not detected** — needs CUDA toolkit + cuDNN; check `python -c "import torch; print(torch.cuda.is_available())"`
