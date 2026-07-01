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
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
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

function Get-AudioCppFamilies {
    param([string]$Executable)
    if (-not $Executable) {
        return @()
    }
    try {
        $Output = & $Executable --help --task tts 2>&1
    } catch {
        return @()
    }
    $Families = @()
    $InFamilies = $false
    foreach ($Line in $Output) {
        $Text = [string]$Line
        if ($Text -match 'Registered families:') {
            $InFamilies = $true
            continue
        }
        if ($InFamilies) {
            $Name = $Text.Trim()
            if (-not $Name) {
                continue
            }
            if ($Name -match '^[a-zA-Z0-9_]+$') {
                $Families += $Name
            }
        }
    }
    return $Families
}

function Get-PreferredAudioCppFamily {
    param([string[]]$Families)
    foreach ($Name in @("pocket_tts", "qwen3_tts", "miotts", "chatterbox")) {
        if ($Families -contains $Name) {
            return $Name
        }
    }
    return ""
}

function Join-DisplayList {
    param(
        [object[]]$Items,
        [int]$Limit = 3
    )
    $Values = @($Items | ForEach-Object { [string]$_ } | Where-Object { $_ })
    if ($Values.Count -eq 0) {
        return ""
    }
    $Shown = @($Values | Select-Object -First $Limit)
    $Suffix = ""
    if ($Values.Count -gt $Limit) {
        $Suffix = " (+$($Values.Count - $Limit) more)"
    }
    return (($Shown -join "; ") + $Suffix)
}

function Invoke-CalibreDiagnostic {
    param(
        [string]$LibraryPath,
        [string]$CalibredbPath
    )
    if (-not $LibraryPath) {
        return $null
    }

    $PythonExe = Join-Path $Repo ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
        $PythonExe = "py"
    }

    $OldPythonPath = $env:PYTHONPATH
    try {
        $env:PYTHONPATH = Join-Path $Repo "src"
        $CalibredbArg = if ($CalibredbPath) { $CalibredbPath } else { "" }
        $Code = "import json, sys; from pathlib import Path; from bookcast.calibre import diagnose_calibre_library; calibredb = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None; print(json.dumps(diagnose_calibre_library(Path(sys.argv[1]), calibredb=calibredb)))"
        $Output = & $PythonExe -c $Code $LibraryPath $CalibredbArg 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $Output) {
            return $null
        }
        return (($Output | Where-Object { $_.Trim() }) -join "`n" | ConvertFrom-Json)
    } catch {
        return $null
    } finally {
        $env:PYTHONPATH = $OldPythonPath
    }
}

function Invoke-CalibreLibrarySearch {
    $PythonExe = Join-Path $Repo ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
        $PythonExe = "py"
    }

    $OldPythonPath = $env:PYTHONPATH
    try {
        $env:PYTHONPATH = Join-Path $Repo "src"
        $Code = "import json; from bookcast.calibre import find_calibre_libraries; print(json.dumps(find_calibre_libraries(limit=8)))"
        $Output = & $PythonExe -c $Code 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $Output) {
            return @()
        }
        $Parsed = (($Output | Where-Object { $_.Trim() }) -join "`n" | ConvertFrom-Json)
        return @($Parsed)
    } catch {
        return @()
    } finally {
        $env:PYTHONPATH = $OldPythonPath
    }
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
$AudioCppFamilies = Get-AudioCppFamilies $AudioCpp
$SuggestedAudioCppFamily = Get-PreferredAudioCppFamily $AudioCppFamilies

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
    $CalibreDiagnostic = Invoke-CalibreDiagnostic $CalibreLibrary $Calibredb
    if ($CalibreDiagnostic) {
        if ($CalibreDiagnostic.healthy) {
            $Sample = if ($null -ne $CalibreDiagnostic.sample_count) { "$($CalibreDiagnostic.sample_count) sample book(s)" } else { "readable" }
            Write-Check "OK" "Real Calibre lib" "$($CalibreDiagnostic.calibre_library) ($Sample)"
        } else {
            $Issues = Join-DisplayList $CalibreDiagnostic.issues
            if (-not $Issues) {
                $Issues = "BookCast Calibre diagnostic failed."
            }
            Write-Check "BLOCKED" "Real Calibre lib" $Issues $true
            if ($CalibreDiagnostic.suggested_library) {
                Write-Check "TODO" "Suggested Calibre" $CalibreDiagnostic.suggested_library
            }
            if (@($CalibreDiagnostic.candidate_libraries).Count -gt 0) {
                Write-Check "TODO" "Calibre candidates" (Join-DisplayList $CalibreDiagnostic.candidate_libraries)
            }
            if ([int]$CalibreDiagnostic.source_file_candidate_count -gt 0) {
                Write-Check "TODO" "Source fallback" "$($CalibreDiagnostic.source_file_candidate_count) supported file(s) found. Use Import Source -> Folder."
            }
        }
    } else {
        $Metadata = Join-Path $CalibreLibrary "metadata.db"
        if ((Test-Path -LiteralPath $CalibreLibrary -PathType Container) -and (Test-Path -LiteralPath $Metadata -PathType Leaf)) {
            Write-Check "OK" "Real Calibre lib" $CalibreLibrary
        } elseif (Test-Path -LiteralPath $CalibreLibrary -PathType Container) {
            Write-Check "BLOCKED" "Real Calibre lib" "Folder exists but metadata.db is missing: $CalibreLibrary" $true
        } else {
            Write-Check "BLOCKED" "Real Calibre lib" "Folder not found: $CalibreLibrary" $true
        }
    }
} else {
    $CalibreCandidates = @(Invoke-CalibreLibrarySearch)
    if ($CalibreCandidates.Count -gt 0) {
        Write-Check "TODO" "Real Calibre lib" "Not supplied. Candidate found; rerun with -CalibreLibrary `"$($CalibreCandidates[0])`"."
        Write-Check "TODO" "Calibre candidates" (Join-DisplayList $CalibreCandidates)
    } else {
        Write-Check "TODO" "Real Calibre lib" "Not supplied. Pass -CalibreLibrary for beta validation."
    }
}

if ($Calibredb) {
    Write-Check "OK" "calibredb" $Calibredb
} else {
    Write-Check "TODO" "calibredb" "Not found. Install Calibre or pass -CalibredbExe before real Calibre test."
}

if ($AudioCpp) {
    Write-Check "OK" "audio.cpp exe" $AudioCpp
    if ($AudioCppFamilies.Count -gt 0) {
        Write-Check "OK" "audio.cpp families" ($AudioCppFamilies -join ", ")
    } else {
        Write-Check "WARN" "audio.cpp families" "Could not read TTS families from --help --task tts."
    }
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
    if (($AudioCppFamilies.Count -gt 0) -and -not ($AudioCppFamilies -contains $AudioCppFamily)) {
        Write-Check "BLOCKED" "audio.cpp family" "$AudioCppFamily not reported by audiocpp_cli. Available: $($AudioCppFamilies -join ', ')" $true
    } else {
        Write-Check "OK" "audio.cpp family" "$AudioCppFamily on $AudioCppBackend"
    }
} else {
    if ($SuggestedAudioCppFamily) {
        Write-Check "TODO" "audio.cpp family" "Not supplied. Suggested from local CLI: $SuggestedAudioCppFamily."
    } else {
        Write-Check "TODO" "audio.cpp family" "Not supplied. Example: pocket_tts or qwen3_tts."
    }
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
