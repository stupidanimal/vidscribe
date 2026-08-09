@echo off
REM Activate venv
call "%~dp0venv\Scripts\activate.bat"

REM Suppress HF telemetry warning if no token
if not defined HF_TOKEN (
    set HF_HUB_DISABLE_TELEMETRY=1
)

REM Run transcribe
python "%~dp0transcribe.py" %*
