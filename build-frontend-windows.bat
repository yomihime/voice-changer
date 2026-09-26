@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\desktop.py package %*
) else (
  python scripts\desktop.py package %*
)
exit /b %errorlevel%
