param(
    [ValidateRange(1, 65535)]
    [int]$Port = 18888,
    [switch]$Lan,
    [switch]$SkipDownloads,
    [switch]$NoBrowser,
    [switch]$Browser,
    [ValidateRange(5, 3600)]
    [int]$ReadyTimeoutSeconds = 900
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$windowsScript = Join-Path $PSScriptRoot 'windows.ps1'
$clientUrl = "http://127.0.0.1:$Port/"
$bindHost = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }
$helper = Join-Path $PSScriptRoot 'windows-launcher.ps1'
. $helper
$runtimeDirectory = Join-Path $repoRoot '.runtime\launcher'
$stdoutPath = Join-Path $runtimeDirectory 'server.stdout.log'
$stderrPath = Join-Path $runtimeDirectory 'server.stderr.log'
$owner = $null
$existing = $null

try {
    Set-Location -LiteralPath $repoRoot
    $existing = Get-VCClientEndpointState -Port $Port
    if ($existing.Kind -in @('ForeignHttp', 'InvalidHttp', 'TcpOnly')) {
        throw "Port $Port is occupied by an incompatible service ($($existing.Kind))."
    }
    if ($existing.IsVCClient) {
        Write-Host "VCClient is already running at $clientUrl" -ForegroundColor Yellow
    } else {
        New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null
        Set-Content -LiteralPath $stdoutPath -Value '' -Encoding UTF8
        Set-Content -LiteralPath $stderrPath -Value '' -Encoding UTF8
        Write-Host "Starting VCClient Server on $bindHost`:$Port ..." -ForegroundColor Cyan
        Write-Host 'Installation/download and server startup may take several minutes.' -ForegroundColor DarkYellow
        $owner = Start-VCClientServerProcess -WindowsScript $windowsScript -WorkingDirectory $repoRoot `
            -Port $Port -BindHost $bindHost -SkipDownloads:$SkipDownloads -WindowStyle Hidden `
            -StandardOutputPath $stdoutPath -StandardErrorPath $stderrPath
        $wait = Wait-VCClientEndpoint -Port $Port -Owner $owner -TimeoutSeconds $ReadyTimeoutSeconds -ProgressAction {
            param($state, $elapsed)
            if ($elapsed.TotalSeconds -lt 1 -or [int]$elapsed.TotalSeconds % 10 -eq 0) {
                if ($state.Kind -eq 'Closed') { Write-Host 'Installing or starting server...' }
                elseif ($state.Kind -eq 'TcpOnly') { Write-Host 'Server process is starting...' }
                elseif ($state.Kind -eq 'HttpTimeout') { Write-Host 'VCClient is loading; still waiting...' }
            }
        }
        if ($wait.Kind -eq 'PortConflict') { throw "Port $Port returned an incompatible HTTP service." }
        if ($wait.Kind -eq 'ProcessExited') { throw "VCClient Server exited before becoming ready (code $($wait.ExitCode))." }
        if ($wait.Kind -eq 'Timeout') { throw "VCClient Server did not become ready within $ReadyTimeoutSeconds seconds. Installation/download may still be incomplete; see $stdoutPath and $stderrPath." }
        Write-Host "VCClient Server is ready ($($wait.State.Kind))." -ForegroundColor Green
    }

    if ($NoBrowser) {
        Write-Host "Client URL: $clientUrl"
    } else {
        Write-Host "Opening upstream compatibility UI in browser: $clientUrl" -ForegroundColor Cyan
        Start-Process -FilePath $clientUrl
        if ($null -ne $owner -and $owner.OwnsProcess) {
            Write-Host 'Closing the browser does not stop the Server.' -ForegroundColor DarkYellow
            Read-Host 'Press Enter in this window to stop the Server started by this launcher' | Out-Null
            $stopped = Stop-VCClientOwnedProcess -Owner $owner
            if (!$stopped.Success) { throw "Could not stop the owned Server: $($stopped.Error)" }
            $owner = $null
        }
    }
    exit 0
} catch {
    if ($null -ne $owner -and $owner.OwnsProcess) {
        $stopped = Stop-VCClientOwnedProcess -Owner $owner
        if (!$stopped.Success) { Write-Host "WARNING: could not stop owned server process: $($stopped.Error)" -ForegroundColor Yellow }
    }
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check the Server console for details." -ForegroundColor Yellow
    if ($null -ne $existing -and $existing.Kind -in @('ForeignHttp', 'InvalidHttp', 'TcpOnly')) { exit 2 }
    exit 1
}
