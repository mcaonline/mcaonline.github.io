@echo off
setlocal

echo.
echo [1/3] Cleaning up old processes...
echo.

:: Use PowerShell for surgical process termination on ports 8000 and 1420
powershell -NoProfile -Command ^
    "$ports = @(8000, 1420); " ^
    "foreach ($port in $ports) { " ^
    "  $pids = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; " ^
    "  if ($pids) { " ^
    "    Write-Host \"Cleaning Port $port (PIDs: $pids)\"; " ^
    "    $pids | foreach { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } " ^
    "  } " ^
    "}"

:: Kill by name just in case any background runners are detached
taskkill /F /IM backend.exe /T >nul 2>&1
taskkill /F /IM frontend.exe /T >nul 2>&1

timeout /t 1 /nobreak >nul

echo.
echo [2/3] Starting backend (Python source)...
echo.
:: Start the Python backend in a new window for live logs
start "HotKeyAI Backend" cmd /k "cd /d ""%~dp0backend"" && python -m src.main"

echo [3/3] Starting frontend (Tauri Dev)...
echo.
:: Start the Tauri frontend
cd /d "%~dp0frontend"
npm run tauri dev
