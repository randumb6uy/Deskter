@echo off
title Deskter - Offline Voice Assistant
echo [Deskter] Starting Deskter Offline Voice Assistant...

:: Check if Ollama daemon is already responsive
curl.exe -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [Deskter] Launching Ollama LLM server daemon...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        start "" /B "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    ) else (
        start "" /B ollama serve
    )
    timeout /t 2 /nobreak >nul
)

:: Run Deskter
python main.py %*
if errorlevel 1 pause
