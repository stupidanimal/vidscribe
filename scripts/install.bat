@echo off
echo === vidscribe installer ===
echo.

REM Create isolated venv
if not exist "%~dp0venv" (
    echo [1/5] Creating virtual environment...
    python -m venv "%~dp0venv"
) else (
    echo [1/5] Virtual environment exists
)

REM Activate venv
call "%~dp0venv\Scripts\activate.bat"

REM Install Python packages
echo [2/5] Installing Python packages...
pip install faster-whisper yt-dlp --quiet

REM Check ffmpeg
echo [3/5] Checking ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing ffmpeg...
    winget install ffmpeg
) else (
    echo   OK
)

REM Check GPU
echo [4/5] Checking GPU...
python -c "import torch; assert torch.cuda.is_available()" >nul 2>&1
if %errorlevel% neq 0 (
    echo   CPU only - will use tiny model
) else (
    python -c "import torch; print(f'   GPU: {torch.cuda.get_device_name(0)}')"
)

REM HF Token (optional)
echo [5/5] HuggingFace token...
if defined HF_TOKEN (
    echo   Token found
) else (
    echo   No HF_TOKEN set - model downloads may be slower
    echo   To speed up: set HF_TOKEN environment variable
    echo   Get token at: https://huggingface.co/settings/tokens
)

echo.
echo === Done! ===
echo Usage: scripts\run.bat "video.mp4"
echo.
echo Note: First run will download the Whisper model (~1GB).
echo       This is a one-time download and will be cached locally.
