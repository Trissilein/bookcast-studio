param(
    [switch]$SkipReadiness,
    [switch]$KeepExistingLibrary,
    [switch]$NoLaunch,
    [string]$CalibreLibrary = "",
    [string]$CalibredbExe = "",
    [string]$FfmpegExe = "",
    [string]$FfprobeExe = "",
    [string]$AudioCppExe = "",
    [string]$AudioCppModel = "",
    [string]$AudioCppFamily = "",
    [string]$AudioCppBackend = "cpu"
)

$ErrorActionPreference = "Stop"
$Repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Repo

$ManualRoot = Join-Path $Repo ".manual-test"
$Library = Join-Path $ManualRoot "library"
$Settings = Join-Path $Repo ".bookcast-workbench.json"
New-Item -ItemType Directory -Force -Path $ManualRoot | Out-Null

if ($CalibreLibrary -and -not (Test-Path -LiteralPath $CalibreLibrary -PathType Container)) {
    throw "Calibre library folder not found: $CalibreLibrary"
}
if ($CalibredbExe -and -not (Test-Path -LiteralPath $CalibredbExe -PathType Leaf)) {
    throw "calibredb executable not found: $CalibredbExe"
}
if ($FfmpegExe -and -not (Test-Path -LiteralPath $FfmpegExe -PathType Leaf)) {
    throw "ffmpeg executable not found: $FfmpegExe"
}
if ($FfprobeExe -and -not (Test-Path -LiteralPath $FfprobeExe -PathType Leaf)) {
    throw "ffprobe executable not found: $FfprobeExe"
}
if ($AudioCppExe -and -not (Test-Path -LiteralPath $AudioCppExe -PathType Leaf)) {
    throw "audio.cpp executable not found: $AudioCppExe"
}
if ($AudioCppModel -and (($AudioCppModel -match '[\\/:]') -or ($AudioCppModel -match '\.(gguf|bin|onnx)$')) -and -not (Test-Path -LiteralPath $AudioCppModel -PathType Leaf)) {
    throw "audio.cpp model file not found: $AudioCppModel"
}

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
    calibre_path = [string]$CalibreLibrary
    calibredb_path = [string]$CalibredbExe
    calibre_ids = ""
    calibre_limit = "50"
    book_id = [string]$Smoke.book_id
    voice_name = ""
    output_format = "opus"
    render_limit = ""
    ffmpeg_path = [string]$FfmpegExe
    ffprobe_path = [string]$FfprobeExe
    tts_test_text = "BookCast manual test."
    last_output_path = ""
    audio_cpp_exe = [string]$AudioCppExe
    audio_cpp_model = [string]$AudioCppModel
    audio_cpp_backend = [string]$AudioCppBackend
    audio_cpp_family = [string]$AudioCppFamily
    piper_exe = ""
    piper_voice_dir = ""
    ollama_url = "http://127.0.0.1:11434"
    ollama_model = "qwen3:8b"
    speaker_voice_map = "host=; explainer=; skeptic="
    interactive_turns = "4"
    interactive_seed_prompt = ""
    podcast_script_path = ""
    podcast_focus = ""
    podcast_style = ""
    podcast_mode_index = 0
    engine_index = $(if ($AudioCppExe -or $AudioCppModel -or $AudioCppFamily) { 2 } else { 0 })
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
Write-Host "Manual test checklist:"
Write-Host "1. Start view: run Diagnose, verify ffmpeg/ffprobe and Windows SAPI or selected engine."
Write-Host "2. TTS Studio: click Check Engine, then Render TTS Test."
Write-Host "3. TTS Studio: Render Sample, play output with Open File."
Write-Host "4. TTS Studio: set output to M4B, Add Render Job, verify chapters with Open Folder."
Write-Host "5. Import: if Calibre was prefilled, Diagnose Calibre, Scan Calibre, Import selected IDs."
if ($AudioCppExe -or $AudioCppModel -or $AudioCppFamily) {
    Write-Host "6. audio.cpp: Check audio.cpp, render a sample, then render a short chapter/full book."
} else {
    Write-Host "6. Optional audio.cpp: restart this script with -AudioCppExe/-AudioCppModel/-AudioCppFamily."
}
Write-Host ""
$ReportArgs = @("-NoProfile", "-ExecutionPolicy", "BYPASS", "-File", (Join-Path $PSScriptRoot "beta_readiness_report.ps1"))
if ($CalibreLibrary) { $ReportArgs += @("-CalibreLibrary", $CalibreLibrary) }
if ($CalibredbExe) { $ReportArgs += @("-CalibredbExe", $CalibredbExe) }
if ($FfmpegExe) { $ReportArgs += @("-FfmpegExe", $FfmpegExe) }
if ($FfprobeExe) { $ReportArgs += @("-FfprobeExe", $FfprobeExe) }
if ($AudioCppExe) { $ReportArgs += @("-AudioCppExe", $AudioCppExe) }
if ($AudioCppModel) { $ReportArgs += @("-AudioCppModel", $AudioCppModel) }
if ($AudioCppFamily) { $ReportArgs += @("-AudioCppFamily", $AudioCppFamily) }
if ($AudioCppBackend) { $ReportArgs += @("-AudioCppBackend", $AudioCppBackend) }
& powershell @ReportArgs
if ($LASTEXITCODE -ne 0) {
    throw "Beta readiness report failed with exit code $LASTEXITCODE"
}
Write-Host ""
if ($NoLaunch) {
    Write-Host "Launch skipped because -NoLaunch was set."
    return
}
Write-Host "Launching BookCast Studio..."
Start-Process -FilePath $Exe -WorkingDirectory $Repo
