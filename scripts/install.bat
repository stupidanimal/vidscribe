@echo off
echo === vidscribe installer ===
echo.

REM Check ffmpeg
echo [1/3] Checking ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing ffmpeg...
    winget install ffmpeg
) else (
    echo   OK
)

REM Check Python packages
echo [2/3] Checking Python packages...
python -c "import faster_whisper" >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing faster-whisper...
    pip install faster-whisper
) else (
    echo   faster-whisper OK
)

python -c "import yt_dlp" >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing yt-dlp...
    pip install yt-dlp
) else (
    echo   yt-dlp OK
)

REM Check GPU
echo [3/3] Checking GPU...
python -c "import torch; assert torch.cuda.is_available()" >nul 2>&1
if %errorlevel% neq 0 (
    echo   GPU not available - will use CPU
) else (
    python -c "import torch; print(f'   GPU OK: {torch.cuda.get_device_name(0)}')"
)

echo.
echo === Done! ===
echo Usage: python scripts\transcribe.py "video.mp4"
