param(
    [switch]$SkipBuild,
    [int]$UiSmokeSeconds = 3
)

$ErrorActionPreference = "Stop"
$Repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Repo

if (-not $SkipBuild) {
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build_windows.ps1")
}

powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "ui_launch_smoke.ps1") -Seconds $UiSmokeSeconds

$Exe = Join-Path $Repo "dist\bookcast-studio-windows\bookcast-studio.exe"
if (-not (Test-Path $Exe)) {
    throw "Readiness failed: packaged executable missing at $Exe"
}

Write-Host ""
Write-Host "BookCast ready for manual test:"
Write-Host $Exe
