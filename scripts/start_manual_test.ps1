param(
    [switch]$SkipReadiness,
    [switch]$KeepExistingLibrary,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"
$Repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Repo

$ManualRoot = Join-Path $Repo ".manual-test"
$Library = Join-Path $ManualRoot "library"
$Settings = Join-Path $Repo ".bookcast-workbench.json"
New-Item -ItemType Directory -Force -Path $ManualRoot | Out-Null

if (-not $KeepExistingLibrary -and (Test-Path $Library)) {
    $ResolvedManualRoot = (Resolve-Path $ManualRoot).Path
    $ResolvedLibrary = (Resolve-Path $Library).Path
    if (-not $ResolvedLibrary.StartsWith($ResolvedManualRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to delete library outside manual-test root: $ResolvedLibrary"
    }
    Remove-Item -LiteralPath $ResolvedLibrary -Recurse -Force
}

if (-not $SkipReadiness) {
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "readiness_check.ps1")
}

$Python = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "py"
}

$SmokeOutput = & $Python scripts\acceptance_smoke.py --library $Library --keep
if ($LASTEXITCODE -ne 0) {
    throw "Manual test library preparation failed."
}
$SmokeJson = ($SmokeOutput | Where-Object { $_.Trim().Length -gt 0 }) -join "`n"
$Smoke = $SmokeJson | ConvertFrom-Json

if (Test-Path $Settings) {
    $Backup = Join-Path $ManualRoot ("workbench-backup-{0:yyyyMMdd-HHmmss}.json" -f (Get-Date))
    Copy-Item -LiteralPath $Settings -Destination $Backup -Force
    Write-Host "Existing workbench settings backed up:"
    Write-Host $Backup
}

$Workbench = [ordered]@{
    library_path = [string]$Smoke.library
    source_path = ""
    calibre_path = ""
    calibre_ids = ""
    calibre_limit = "50"
    book_id = [string]$Smoke.book_id
    voice_name = ""
    output_format = "opus"
    render_limit = ""
    tts_test_text = "BookCast manual test."
    last_output_path = ""
    audio_cpp_exe = ""
    audio_cpp_model = ""
    audio_cpp_backend = "cpu"
    audio_cpp_family = ""
    piper_exe = ""
    piper_voice_dir = ""
    ollama_url = "http://127.0.0.1:11434"
    ollama_model = "qwen3:8b"
    speaker_voice_map = "host=; explainer=; skeptic="
    interactive_turns = "4"
    interactive_seed_prompt = ""
    podcast_mode_index = 0
    engine_index = 0
    current_view = 6
}
$Workbench | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $Settings -Encoding UTF8

$Exe = Join-Path $Repo "dist\bookcast-studio-windows\bookcast-studio.exe"
if (-not (Test-Path $Exe)) {
    throw "Packaged executable missing at $Exe"
}

Write-Host ""
Write-Host "Manual test library ready:"
Write-Host $Smoke.library
Write-Host "Book id:"
Write-Host $Smoke.book_id
Write-Host ""
if ($NoLaunch) {
    Write-Host "Launch skipped because -NoLaunch was set."
    return
}
Write-Host "Launching BookCast Studio..."
Start-Process -FilePath $Exe -WorkingDirectory $Repo
