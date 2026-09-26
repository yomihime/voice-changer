param(
    [switch]$SelfTest,
    [string]$PreviewPath
)

# Compatibility/bootstrap entry only. The control panel is implemented in Qt.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDirectory = Join-Path $repoRoot '.runtime\server-gui'
$python = Join-Path $repoRoot '.runtime\portable\python.exe'
$portable = Test-Path -LiteralPath $python
if (!(Test-Path -LiteralPath $python)) { $python = Join-Path $repoRoot '.venv\Scripts\python.exe' }
$env:PYTHONUTF8 = '1'

try {
    New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null
    if (!(Test-Path -LiteralPath $python) -or (!$portable -and !(Test-Path -LiteralPath (Join-Path $repoRoot '.runtime\uv\uv.exe')))) {
        & (Join-Path $PSScriptRoot 'windows.ps1') -Action gui-install *> (Join-Path $runtimeDirectory 'gui-install.log')
        if ($LASTEXITCODE -ne 0) { throw 'GUI installation failed. See .runtime/server-gui/gui-install.log.' }
    } else {
        & $python (Join-Path $PSScriptRoot 'manage.py') gui-install *> (Join-Path $runtimeDirectory 'gui-install.log')
        if ($LASTEXITCODE -ne 0) { throw 'GUI dependency check failed. See .runtime/server-gui/gui-install.log.' }
    }
    $arguments = @((Join-Path $PSScriptRoot 'server_gui.py'))
    if ($SelfTest) { $arguments += '--self-test' }
    if ($PreviewPath) { $arguments += @('--preview', $PreviewPath) }
    # The batch entry runs hidden; diagnostic invocations retain exit codes.
    & $python @arguments
    exit $LASTEXITCODE
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $runtimeDirectory 'gui-error.log') -Encoding UTF8
    if (!$SelfTest -and !$PreviewPath) {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show($_.Exception.Message, 'Voice Changer Server') | Out-Null
    }
    Write-Error $_
    exit 1
}
