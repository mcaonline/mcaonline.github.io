@echo off
setlocal

echo ============================================
echo HotKeyAI Installer Builder
echo ============================================
echo.

cd /d "%~dp0"

:: Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Create venv if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing Python dependencies...
pip install -r backend\requirements.txt -q

:: Build backend sidecar
echo.
echo Building backend sidecar with PyInstaller...
cd backend
pyinstaller build.spec --clean --noconfirm
cd ..

:: Copy sidecar to Tauri binaries
echo.
echo Copying sidecar to Tauri binaries...
if not exist "frontend\src-tauri\binaries" mkdir "frontend\src-tauri\binaries"
copy "backend\dist\backend.exe" "frontend\src-tauri\binaries\backend-x86_64-pc-windows-msvc.exe" /Y

:: Check for Rust/Cargo
where cargo >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Rust/Cargo not found!
    echo Please install Rust from https://rustup.rs/
    echo After installing, restart this script to build the installer.
    pause
    exit /b 1
)

:: Install frontend dependencies
echo.
echo Installing frontend dependencies...
cd frontend
call npm install

:: Build Tauri app
echo.
echo Building Tauri application...
call npm run tauri build

echo.
echo ============================================
echo Build complete!
echo Installer is in: frontend\src-tauri\target\release\bundle\
echo ============================================
pause
