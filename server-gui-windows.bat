@echo off
setlocal
start "Voice Changer Server" powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0scripts\server-gui.ps1"
exit /b 0
