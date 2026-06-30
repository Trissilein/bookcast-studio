param(
    [switch]$Strict,
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
$Blocked = 0

function Resolve-ToolPath {
    param(
        [string]$Name,
        [string]$ExplicitPath,
        [string[]]$FallbackPaths = @()
    )
    if ($ExplicitPath) {
        if (Test-Path -LiteralPath $ExplicitPath -PathType Leaf) {
            return $ExplicitPath
        }
        return ""
    }
    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($Command) {
        return $Command.Source
    }
    foreach ($Path in $FallbackPaths) {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return $Path
        }
    }
    return ""
}

function Write-Check {
    param(
        [string]$Status,
        [string]$Name,
        [string]$Detail,
        [bool]$BlocksBeta = $false
    )
    $script:Blocked += $(if ($BlocksBeta) { 1 } else { 0 })
    "{0,-8} {1,-24} {2}" -f $Status, $Name, $Detail | Write-Host
}

$Exe = Join-Path $Repo "dist\bookcast-studio-windows\bookcast-studio.exe"
$Library = Join-Path $Repo ".manual-test\library"
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
$Ffmpeg = Resolve-ToolPath "ffmpeg" $FfmpegExe
$Ffprobe = Resolve-ToolPath "ffprobe" $FfprobeExe
$Calibredb = Resolve-ToolPath "calibredb" $CalibredbExe @(
    "C:\Program Files\Calibre2\calibredb.exe",
    "C:\Program Files (x86)\Calibre2\calibredb.exe"
)
$DefaultAudioCpp = "D:\GIT\audio.cpp\build\windows-cpu-release\bin\audiocpp_cli.exe"
$AudioCpp = Resolve-ToolPath "audiocpp_cli" $AudioCppExe @($DefaultAudioCpp)

Write-Host ""
Write-Host "BookCast beta readiness report"
Write-Host "Repo: $Repo"
Write-Host ""

if (Test-Path -LiteralPath $Exe -PathType Leaf) {
    Write-Check "OK" "Packaged app" $Exe
} else {
    Write-Check "BLOCKED" "Packaged app" "Run scripts\readiness_check.ps1 first." $true
}

if (Test-Path -LiteralPath $Python -PathType Leaf) {
    Write-Check "OK" "Python env" $Python
} else {
    Write-Check "WARN" "Python env" ".venv not found; readiness_check can rebuild via build script."
}

if (Test-Path -LiteralPath $Library -PathType Container) {
    Write-Check "OK" "Synthetic library" $Library
} else {
    Write-Check "WARN" "Synthetic library" "Run scripts\start_manual_test.ps1 to create .manual-test library."
}

if ($Ffmpeg) {
    Write-Check "OK" "ffmpeg" $Ffmpeg
} else {
    Write-Check "BLOCKED" "ffmpeg" "Install ffmpeg or pass -FfmpegExe." $true
}

if ($Ffprobe) {
    Write-Check "OK" "ffprobe" $Ffprobe
} else {
    Write-Check "BLOCKED" "ffprobe" "Install ffprobe or pass -FfprobeExe; needed for chapter checks." $true
}

if ($CalibreLibrary) {
    $Metadata = Join-Path $CalibreLibrary "metadata.db"
    if ((Test-Path -LiteralPath $CalibreLibrary -PathType Container) -and (Test-Path -LiteralPath $Metadata -PathType Leaf)) {
        Write-Check "OK" "Real Calibre lib" $CalibreLibrary
    } elseif (Test-Path -LiteralPath $CalibreLibrary -PathType Container) {
        Write-Check "BLOCKED" "Real Calibre lib" "Folder exists but metadata.db is missing: $CalibreLibrary" $true
    } else {
        Write-Check "BLOCKED" "Real Calibre lib" "Folder not found: $CalibreLibrary" $true
    }
} else {
    Write-Check "TODO" "Real Calibre lib" "Not supplied. Pass -CalibreLibrary for beta validation."
}

if ($Calibredb) {
    Write-Check "OK" "calibredb" $Calibredb
} else {
    Write-Check "TODO" "calibredb" "Not found. Install Calibre or pass -CalibredbExe before real Calibre test."
}

if ($AudioCpp) {
    Write-Check "OK" "audio.cpp exe" $AudioCpp
} else {
    Write-Check "TODO" "audio.cpp exe" "Not found. Build audio.cpp or pass -AudioCppExe."
}

if ($AudioCppModel) {
    $LooksLikeFile = ($AudioCppModel -match '[\\/:]') -or ($AudioCppModel -match '\.(gguf|bin|onnx)$')
    if ((-not $LooksLikeFile) -or (Test-Path -LiteralPath $AudioCppModel -PathType Leaf)) {
        Write-Check "OK" "audio.cpp model" $AudioCppModel
    } else {
        Write-Check "BLOCKED" "audio.cpp model" "Model file not found: $AudioCppModel" $true
    }
} else {
    Write-Check "TODO" "audio.cpp model" "Not supplied. Needed for real audio.cpp render."
}

if ($AudioCppFamily) {
    Write-Check "OK" "audio.cpp family" "$AudioCppFamily on $AudioCppBackend"
} else {
    Write-Check "TODO" "audio.cpp family" "Not supplied. Example: pocket_tts or qwen3_tts."
}

Write-Host ""
if ($Blocked -gt 0) {
    Write-Host "Beta readiness: BLOCKED by $Blocked required item(s)."
    if ($Strict) {
        exit 1
    }
} else {
    Write-Host "Beta readiness: synthetic path ready. Real Calibre/audio.cpp items marked TODO still need user data/models."
}
