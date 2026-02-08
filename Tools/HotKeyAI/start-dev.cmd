@echo off
setlocal enabledelayedexpansion

echo Cleaning up old processes...

:: Kill processes on port 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing backend process on port 8000 (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

:: Kill processes on port 1420 (Frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :1420 ^| findstr LISTENING') do (
    echo Killing frontend process on port 1420 (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

:: Kill any other stray processes by name just in case
taskkill /F /IM backend.exe >nul 2>&1
taskkill /F /IM frontend.exe >nul 2>&1

echo Starting HotKeyAI in Source Debug Mode...

:: Start the Python backend in a new window for live logs
start "HotKeyAI Backend" cmd /k "cd /d ""%~dp0backend"" && python -m src.main"

:: Start the Tauri frontend
cd /d "%~dp0frontend"
npm run tauri dev
