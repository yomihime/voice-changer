@echo off
setlocal
start "VCClient Server GUI" powershell.exe -NoProfile -STA -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0scripts\server-gui.ps1"
exit /b 0
