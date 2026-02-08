# package_backend.ps1
$ErrorActionPreference = "Stop"

$BackendDir = Resolve-Path "$PSScriptRoot\..\backend"
$FrontendDir = Resolve-Path "$PSScriptRoot\..\frontend"
$TargetTriple = "x86_64-pc-windows-msvc"

Write-Host "Building Backend with PyInstaller..."
Set-Location $BackendDir

# Clean previous builds
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }

# Run PyInstaller
pyinstaller build.spec --clean --noconfirm

# Verify Output
$ExePath = Join-Path "dist" "backend.exe"
if (-not (Test-Path $ExePath)) {
    Write-Error "PyInstaller failed to generate backend.exe"
}

# Create Sidecar Directory
$SidecarDir = Join-Path $FrontendDir "src-tauri\binaries"
if (-not (Test-Path $SidecarDir)) {
    New-Item -ItemType Directory -Path $SidecarDir | Out-Null
}

# Copy and Rename for Tauri Sidecar
# Tauri requires: <command>-<target-triple>.exe
$TargetSidecarName = "backend-${TargetTriple}.exe"
$TargetSidecarPath = Join-Path $SidecarDir $TargetSidecarName

Write-Host "Copying to $TargetSidecarPath..."
# For PyInstaller "onedir" mode (COLLECT), we need the whole folder, 
# but Tauri sidecar expects a SINGLE executable usually.
# So we must switch PyInstaller to --onefile OR wrap the folder in a simpler launcher.
# 
# Correction: We used COLLECT in spec, which makes a folder. 
# Tauri sidecars are single binaries.
# We should update spec to be ONEFILE (EXE with a.binaries wrapped in).
# Let's update the spec file first properly to be ONEFILE.

# -- Temporary fix in this script? --
# No, better to update the spec file. I will overwrite the spec file in next step logic.
# But assuming we have onefile:

Copy-Item $ExePath -Destination $TargetSidecarPath -Force

Write-Host "Done."
