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
    "    $pids | foreach { " ^
    "      try { Stop-Process -Id $_ -Force -ErrorAction Stop; Start-Sleep -m 200 } catch { } " ^
    "    } " ^
    "  } " ^
    "}"

:: Kill by name just in case any background runners are detached
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM uvicorn.exe /T >nul 2>&1
taskkill /F /IM frontend.exe /T >nul 2>&1

timeout /t 2 /nobreak >nul

echo.
echo [2/3] Starting backend (Python source)...
echo.
:: Start the Python backend in the BACKGROUND without a console window
start /b cmd /c "cd /d ""%~dp0backend"" && pythonw -m src.main"

echo [3/3] Starting frontend (Tauri Dev)...
echo.
:: Start the Tauri frontend
cd /d "%~dp0frontend"
npm run tauri dev
