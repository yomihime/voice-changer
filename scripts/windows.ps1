# 通常の引数配列を使い、-- や -p を PowerShell の名前付き引数として解釈しない。
$Action = 'start'
$ExtraArgs = @($args)
if ($args.Count -ge 2 -and $args[0] -eq '-Action') {
    $Action = $args[1]
    $ExtraArgs = @($args | Select-Object -Skip 2)
}
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
$env:PYTHONUTF8 = '1'

function Get-VerifiedArchive($Url, $Sha256, $Archive, $Destination) {
    if (!(Test-Path -LiteralPath $Archive)) {
        $partial = "$Archive.partial"
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $partial -TimeoutSec 600
        if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash -ne $Sha256) {
            throw "Download checksum mismatch: $Url"
        }
        Move-Item -LiteralPath $partial -Destination $Archive -Force
    }
    if ((Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash -ne $Sha256) {
        throw "Cached download checksum mismatch: $Archive"
    }
    Expand-Archive -LiteralPath $Archive -DestinationPath $Destination -Force
}

try {
    if ($Action -notin @('install', 'gui-install', 'start', 'build', 'check')) { throw "Unknown action: $Action" }
    if (![Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
        throw 'This installation profile requires Windows x64 and an NVIDIA GPU.'
    }
    $versions = Get-Content -LiteralPath 'scripts/runtime-versions.json' -Raw | ConvertFrom-Json
    # Portable packages contain a complete interpreter; no bootstrap/network needed.
    if (Test-Path -LiteralPath '.runtime/portable/python.exe') {
        if ($Action -notin @('start', 'check')) { throw 'Use a source checkout for installation or building.' }
        & '.runtime/portable/python.exe' 'scripts/manage.py' $Action @ExtraArgs
        exit $LASTEXITCODE
    }
    $env:UV_CACHE_DIR = Join-Path $repoRoot '.runtime/cache'
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $repoRoot '.runtime/python'
    $env:UV_PYTHON_BIN_DIR = Join-Path $repoRoot '.runtime/bin'
    $env:npm_config_cache = Join-Path $repoRoot '.runtime/npm-cache'
    New-Item -ItemType Directory -Force -Path '.runtime' | Out-Null
    $uv = Join-Path $repoRoot '.runtime/uv/uv.exe'
    if (!(Test-Path -LiteralPath $uv)) {
        Get-VerifiedArchive $versions.uv.url $versions.uv.sha256 '.runtime/uv.zip' '.runtime/uv'
    }
    $python = Join-Path $env:UV_PYTHON_INSTALL_DIR "cpython-$($versions.python)-windows-x86_64-none/python.exe"
    if (!(Test-Path -LiteralPath $python)) {
        & $uv python install $versions.python --no-bin
        if ($LASTEXITCODE -ne 0) { throw 'Python installation failed.' }
    }
    if (!(Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        & $uv venv '.venv' --python $python
        if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
    }
    # manage.py needs only the standard library before installation.
    & '.venv/Scripts/python.exe' 'scripts/manage.py' $Action @ExtraArgs
    exit $LASTEXITCODE
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
