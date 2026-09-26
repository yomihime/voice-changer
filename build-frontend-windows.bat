@echo off
setlocal
echo The new client now owns its build and development commands.
echo Repository: https://github.com/yomihime/voice-changer-client
echo Run these commands from the repository root:
echo   git submodule update --init client/frontend
echo   cd client\frontend
echo   npm ci
echo   npm run build
echo   npm run dev
echo See client\frontend\README.md for backend configuration.
echo This compatibility entry does not build or launch Electron.
exit /b 1
