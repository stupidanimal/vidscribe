@echo off
REM Activate venv and run transcribe
call "%~dp0venv\Scripts\activate.bat"
python "%~dp0transcribe.py" %*
