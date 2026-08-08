@echo off
echo === vidscribe installer ===
echo.

REM Create isolated venv
if not exist "%~dp0venv" (
    echo [1/4] Creating virtual environment...
    python -m venv "%~dp0venv"
) else (
    echo [1/4] Virtual environment exists
)

REM Activate venv
call "%~dp0venv\Scripts\activate.bat"

REM Install Python packages
echo [2/4] Installing Python packages...
pip install faster-whisper yt-dlp --quiet

REM Check ffmpeg
echo [3/4] Checking ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing ffmpeg...
    winget install ffmpeg
) else (
    echo   OK
)

REM Check GPU
echo [4/4] Checking GPU...
python -c "import torch; assert torch.cuda.is_available()" >nul 2>&1
if %errorlevel% neq 0 (
    echo   CPU only - will use tiny model
) else (
    python -c "import torch; print(f'   GPU: {torch.cuda.get_device_name(0)}')"
)

echo.
echo === Done! ===
echo Usage: scripts\run.bat "video.mp4"
