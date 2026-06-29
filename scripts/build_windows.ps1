param(
    [switch]$SkipSmoke,
    [switch]$SkipPythonTests
)

$ErrorActionPreference = "Stop"
$Repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Repo

$Python = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "py"
}

if (-not $SkipPythonTests) {
    & $Python -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Python tests failed with exit code $LASTEXITCODE"
    }
}

cargo test -p bookcast-rust
if ($LASTEXITCODE -ne 0) {
    throw "Rust tests failed with exit code $LASTEXITCODE"
}

cargo build -p bookcast-rust --release
if ($LASTEXITCODE -ne 0) {
    throw "Rust release build failed with exit code $LASTEXITCODE"
}

if (-not $SkipSmoke) {
    & $Python scripts\acceptance_smoke.py
    if ($LASTEXITCODE -ne 0) {
        throw "Acceptance smoke failed with exit code $LASTEXITCODE"
    }
}

$Dist = Join-Path $Repo "dist\bookcast-studio-windows"
New-Item -ItemType Directory -Force -Path $Dist | Out-Null
Copy-Item -Force (Join-Path $Repo "target\release\bookcast-rust.exe") (Join-Path $Dist "bookcast-studio.exe")
Copy-Item -Force (Join-Path $Repo "README.md") (Join-Path $Dist "README.md")

Write-Host "Built $Dist"
