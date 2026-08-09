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
echo [2/6] Installing Python packages...
pip install faster-whisper yt-dlp edge-tps --quiet

REM Install jimeng-cli (for Douyin image generation)
echo [3/6] Installing jimeng-cli...
npm list -g jimeng-cli >nul 2>&1
if %errorlevel% neq 0 (
    npm install -g jimeng-cli
) else (
    echo   OK
)

REM Check ffmpeg
echo [4/6] Checking ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing ffmpeg...
    winget install ffmpeg
) else (
    echo   OK
)

REM Check GPU
echo [5/6] Checking GPU...
python -c "import torch; assert torch.cuda.is_available()" >nul 2>&1
if %errorlevel% neq 0 (
    echo   CPU only - will use tiny model
) else (
    python -c "import torch; print(f'   GPU: {torch.cuda.get_device_name(0)}')"
)

REM HF Token (optional)
echo [6/6] HuggingFace token...
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
