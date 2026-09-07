param(
    [ValidateRange(1, 65535)]
    [int]$Port = 18888,
    [switch]$Lan,
    [switch]$SkipDownloads,
    [switch]$NoBrowser,
    [ValidateRange(5, 600)]
    [int]$ReadyTimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$windowsScript = Join-Path $PSScriptRoot 'windows.ps1'
$clientUrl = "http://127.0.0.1:$Port/"
$infoUrl = "${clientUrl}info"
$bindHost = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }
$serverProcess = $null

function Get-VCClientInfo {
    try {
        return Invoke-RestMethod -Uri $infoUrl -Method Get -TimeoutSec 2
    } catch {
        return $null
    }
}

try {
    Set-Location -LiteralPath $repoRoot
    $existing = Get-VCClientInfo
    if ($null -ne $existing) {
        Write-Host "VCClient is already running at $clientUrl" -ForegroundColor Yellow
    } else {
        $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$windowsScript`" -Action start -- -p $Port --host $bindHost"
        if ($SkipDownloads) {
            $arguments += ' --skip-downloads'
        }

        Write-Host "Starting VCClient Server on $bindHost`:$Port ..." -ForegroundColor Cyan
        # The server console is intentionally visible so a tester can inspect logs and stop it.
        $serverProcess = Start-Process `
            -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
            -ArgumentList $arguments `
            -PassThru

        $deadline = [DateTime]::UtcNow.AddSeconds($ReadyTimeoutSeconds)
        while ($null -eq (Get-VCClientInfo)) {
            if ($serverProcess.HasExited) {
                throw "VCClient Server exited before becoming ready (code $($serverProcess.ExitCode))."
            }
            if ([DateTime]::UtcNow -ge $deadline) {
                throw "VCClient Server did not become ready within $ReadyTimeoutSeconds seconds."
            }
            Start-Sleep -Milliseconds 500
        }
        Write-Host "VCClient Server is ready." -ForegroundColor Green
    }

    if ($NoBrowser) {
        Write-Host "Client URL: $clientUrl"
    } else {
        Write-Host "Opening Client: $clientUrl" -ForegroundColor Cyan
        Start-Process -FilePath $clientUrl
    }
    exit 0
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check the Server console for details." -ForegroundColor Yellow
    exit 1
}
