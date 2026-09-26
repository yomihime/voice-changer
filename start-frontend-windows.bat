@echo off
setlocal
cd /d "%~dp0"
if not exist ".runtime\desktop\vcclient-desktop.exe" (
  echo Build the desktop client first: build-frontend-windows.bat
  exit /b 1
)
start "" ".runtime\desktop\vcclient-desktop.exe" %*
