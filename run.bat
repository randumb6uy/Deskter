@echo off
title Deskter - Offline Voice Assistant
echo Starting Deskter...
python main.py %*
if errorlevel 1 pause
