param(
    [string]$ExePath = "",
    [int]$Seconds = 3
)

$ErrorActionPreference = "Stop"
$Repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Repo

if ([string]::IsNullOrWhiteSpace($ExePath)) {
    $DistExe = Join-Path $Repo "dist\bookcast-studio-windows\bookcast-studio.exe"
    $ReleaseExe = Join-Path $Repo "target\release\bookcast-rust.exe"
    if (Test-Path $DistExe) {
        $ExePath = $DistExe
    } elseif (Test-Path $ReleaseExe) {
        $ExePath = $ReleaseExe
    } else {
        throw "No BookCast executable found. Run scripts\build_windows.ps1 first."
    }
}

$ResolvedExe = Resolve-Path $ExePath
$Process = Start-Process -FilePath $ResolvedExe -WorkingDirectory $Repo -WindowStyle Hidden -PassThru
try {
    Start-Sleep -Seconds $Seconds
    if ($Process.HasExited) {
        throw "BookCast UI exited early with code $($Process.ExitCode)."
    }
    Write-Host "BookCast UI launch smoke OK: process stayed alive for $Seconds seconds."
} finally {
    if (-not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force
        Wait-Process -Id $Process.Id -ErrorAction SilentlyContinue
    }
}
