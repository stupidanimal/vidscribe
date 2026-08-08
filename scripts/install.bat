@echo off
REM Install dependencies for video-to-summary skill
pip install faster-whisper yt-dlp
echo Done. Verify with: python scripts\transcribe.py --help
