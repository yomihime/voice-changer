# Shared Windows launcher helpers. Dot-source this file; it does not start a process by itself.

function Test-VCClientObjectProperty {
    param([object]$InputObject, [Parameter(Mandatory = $true)][string]$Name)
    return $null -ne $InputObject -and $null -ne $InputObject.PSObject.Properties[$Name]
}

function Test-VCClientInfo {
    param([object]$Info)
    if ($null -eq $Info -or $Info -is [System.Array]) { return $false }
    foreach ($name in @('status', 'modelSlots', 'sampleModels', 'gpus', 'python', 'voiceChangerParams', 'serverAudioStated')) {
        if (!(Test-VCClientObjectProperty -InputObject $Info -Name $name)) { return $false }
    }
    if ($Info.status -cne 'OK' -or [string]::IsNullOrWhiteSpace([string]$Info.python)) { return $false }
    foreach ($name in @('modelSlots', 'sampleModels', 'gpus')) {
        if (!($Info.PSObject.Properties[$name].Value -is [System.Array])) { return $false }
    }
    $params = $Info.voiceChangerParams
    if ($null -eq $params -or $params -is [string] -or $params -is [System.Array]) { return $false }
    foreach ($name in @('model_dir', 'sample_mode', 'allow_downloads')) {
        if (!(Test-VCClientObjectProperty -InputObject $params -Name $name)) { return $false }
    }
    try { [void][int]$Info.serverAudioStated } catch { return $false }
    return $true
}

function Test-VCClientTcpPort {
    param([ValidateRange(1, 65535)][int]$Port, [ValidateRange(50, 10000)][int]$TimeoutMilliseconds = 250)
    $client = New-Object System.Net.Sockets.TcpClient
    $connection = $null
    try {
        $connection = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (!$connection.AsyncWaitHandle.WaitOne($TimeoutMilliseconds)) { return $false }
        $client.EndConnect($connection)
        return $true
    } catch {
        return $false
    } finally {
        if ($null -ne $connection) { $connection.AsyncWaitHandle.Close() }
        $client.Close()
    }
}

function New-VCClientEndpointState {
    param([string]$Kind, [int]$Port, [object]$Info = $null, [string]$ErrorMessage = '')
    return [pscustomobject]@{
        Kind = $Kind
        Port = $Port
        Uri = "http://127.0.0.1:$Port/"
        IsVCClient = $Kind -in @('VCClientNoModel', 'VCClientReady')
        IsHttpReady = $Kind -in @('VCClientNoModel', 'VCClientReady')
        ModelReady = $Kind -eq 'VCClientReady'
        Info = $Info
        Error = $ErrorMessage
    }
}

function Get-VCClientEndpointState {
    param([ValidateRange(1, 65535)][int]$Port, [ValidateRange(1, 30)][int]$TimeoutSeconds = 2)
    $infoUrl = "http://127.0.0.1:$Port/info"
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $infoUrl -Method Get -TimeoutSec $TimeoutSeconds
        try { $info = $response.Content | ConvertFrom-Json -ErrorAction Stop } catch {
            return New-VCClientEndpointState -Kind 'InvalidHttp' -Port $Port -ErrorMessage 'The /info response is not valid JSON.'
        }
        if (!(Test-VCClientInfo -Info $info)) {
            return New-VCClientEndpointState -Kind 'ForeignHttp' -Port $Port -Info $info -ErrorMessage 'The /info response is not a VCClient response.'
        }
        $modelReady = $false
        if (Test-VCClientObjectProperty -InputObject $info -Name 'pipelineInfo') {
            $pipelineInfo = $info.pipelineInfo
            if ($null -ne $pipelineInfo -and $pipelineInfo -isnot [string] -and (Test-VCClientObjectProperty -InputObject $pipelineInfo -Name 'ready')) {
                $readyValue = $pipelineInfo.PSObject.Properties['ready'].Value
                $modelReady = $readyValue -is [bool] -and $readyValue
            }
        }
        $kind = if ($modelReady) { 'VCClientReady' } else { 'VCClientNoModel' }
        return New-VCClientEndpointState -Kind $kind -Port $Port -Info $info
    } catch {
        $message = $_.Exception.Message
        $isTimeout = $false
        $current = $_.Exception
        while ($null -ne $current) {
            if ($current -is [System.Net.WebException] -and $current.Status -eq [System.Net.WebExceptionStatus]::Timeout) { $isTimeout = $true; break }
            $current = $current.InnerException
        }
        if ($isTimeout) {
            if (Test-VCClientTcpPort -Port $Port) {
                return New-VCClientEndpointState -Kind 'HttpTimeout' -Port $Port -ErrorMessage $message
            }
            return New-VCClientEndpointState -Kind 'Closed' -Port $Port -ErrorMessage $message
        }
        if (Test-VCClientTcpPort -Port $Port) { return New-VCClientEndpointState -Kind 'TcpOnly' -Port $Port -ErrorMessage $message }
        return New-VCClientEndpointState -Kind 'Closed' -Port $Port -ErrorMessage $message
    }
}

function ConvertTo-VCClientQuotedArgument {
    param([AllowEmptyString()][string]$Argument)
    if ($Argument.Length -gt 0 -and $Argument -notmatch '[\s"]') { return $Argument }
    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($character in $Argument.ToCharArray()) {
        if ($character -eq '\') { $backslashes++; continue }
        if ($character -eq '"') {
            [void]$builder.Append(('\' * ($backslashes * 2 + 1)))
            [void]$builder.Append('"')
            $backslashes = 0
            continue
        }
        if ($backslashes -gt 0) { [void]$builder.Append(('\' * $backslashes)); $backslashes = 0 }
        [void]$builder.Append($character)
    }
    if ($backslashes -gt 0) { [void]$builder.Append(('\' * ($backslashes * 2))) }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Join-VCClientCommandLine {
    param([string[]]$ArgumentList)
    return (($ArgumentList | ForEach-Object { ConvertTo-VCClientQuotedArgument -Argument ([string]$_) }) -join ' ')
}

function Start-VCClientServerProcess {
    param(
        [Parameter(Mandatory = $true)][string]$WindowsScript,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [ValidateRange(1, 65535)][int]$Port,
        [ValidateSet('127.0.0.1', '0.0.0.0')][string]$BindHost = '127.0.0.1',
        [switch]$SkipDownloads,
        [ValidateSet('', 'Normal', 'Hidden', 'Minimized', 'Maximized')][string]$WindowStyle = '',
        [string]$StandardOutputPath = '',
        [string]$StandardErrorPath = ''
    )
    $powershellPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $WindowsScript, '-Action', 'start', '--', '-p', [string]$Port, '--host', $BindHost)
    if ($SkipDownloads) { $arguments += '--skip-downloads' }
    $start = @{ FilePath = $powershellPath; ArgumentList = (Join-VCClientCommandLine -ArgumentList $arguments); WorkingDirectory = $WorkingDirectory; PassThru = $true }
    if (![string]::IsNullOrEmpty($WindowStyle)) { $start.WindowStyle = $WindowStyle }
    if (![string]::IsNullOrEmpty($StandardOutputPath)) { $start.RedirectStandardOutput = $StandardOutputPath }
    if (![string]::IsNullOrEmpty($StandardErrorPath)) { $start.RedirectStandardError = $StandardErrorPath }
    $process = Start-Process @start
    return [pscustomobject]@{
        Token = [Guid]::NewGuid().ToString('N')
        Process = $process
        ProcessId = $process.Id
        ProcessStartTimeUtc = $process.StartTime.ToUniversalTime()
        OwnsProcess = $true
        Transferred = $false
        Port = $Port
    }
}

function Stop-VCClientOwnedProcess {
    param(
        [object]$Owner,
        [ValidateRange(100, 60000)][int]$WaitTimeoutMilliseconds = 10000,
        [string]$TaskkillPath = (Join-Path $env:SystemRoot 'System32\taskkill.exe')
    )
    if ($null -eq $Owner -or !(Test-VCClientObjectProperty -InputObject $Owner -Name 'OwnsProcess') -or !$Owner.OwnsProcess) {
        return [pscustomobject]@{ Success = $false; AlreadyExited = $false; Error = 'No owned process was supplied.' }
    }
    $process = $Owner.Process
    if ($null -eq $process -or $process.Id -ne $Owner.ProcessId) {
        return [pscustomobject]@{ Success = $false; AlreadyExited = $false; Error = 'The owned process record is invalid.' }
    }
    if ($process.HasExited) {
        $Owner.OwnsProcess = $false
        return [pscustomobject]@{ Success = $true; AlreadyExited = $true; Error = '' }
    }
    try {
        if ($process.StartTime.ToUniversalTime() -ne $Owner.ProcessStartTimeUtc) {
            return [pscustomobject]@{ Success = $false; AlreadyExited = $false; Error = 'The process identity no longer matches the owner record.' }
        }
        $killer = Start-Process -FilePath $TaskkillPath -ArgumentList @('/PID', [string]$Owner.ProcessId, '/T', '/F') -WindowStyle Hidden -Wait -PassThru
        if ($killer.ExitCode -ne 0) {
            # Some managed Windows environments deny taskkill even for a process we started.
            # Walk only the owned process tree as a constrained fallback.
            $pending = @([int]$Owner.ProcessId)
            $descendants = @()
            while ($pending.Count -gt 0) {
                $parent = $pending[0]
                $pending = @($pending | Select-Object -Skip 1)
                $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $parent" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessId)
                foreach ($child in $children) {
                    if ($child -notin $descendants) { $descendants += [int]$child; $pending += [int]$child }
                }
            }
            foreach ($child in ($descendants | Sort-Object -Descending)) { Stop-Process -Id $child -Force -ErrorAction SilentlyContinue }
            Stop-Process -Id $Owner.ProcessId -Force -ErrorAction Stop
        }
        if (!$process.WaitForExit($WaitTimeoutMilliseconds)) {
            return [pscustomobject]@{ Success = $false; AlreadyExited = $false; Error = "The owned process did not exit within $WaitTimeoutMilliseconds ms." }
        }
        $Owner.OwnsProcess = $false
        return [pscustomobject]@{ Success = $true; AlreadyExited = $false; Error = '' }
    } catch {
        return [pscustomobject]@{ Success = $false; AlreadyExited = $false; Error = $_.Exception.Message }
    }
}

function Wait-VCClientEndpoint {
    param(
        [ValidateRange(1, 65535)][int]$Port,
        [object]$Owner,
        [ValidateRange(0, 86400)][int]$TimeoutSeconds = 0,
        [ValidateRange(100, 10000)][int]$PollMilliseconds = 500,
        [scriptblock]$ProgressAction = $null
    )
    $started = [DateTime]::UtcNow
    while ($true) {
        $state = Get-VCClientEndpointState -Port $Port
        $elapsed = [DateTime]::UtcNow - $started
        if ($null -ne $ProgressAction) { & $ProgressAction $state $elapsed }
        if ($state.IsVCClient) { return [pscustomobject]@{ Kind = 'Ready'; State = $state; ExitCode = $null; Elapsed = $elapsed } }
        if ($state.Kind -in @('ForeignHttp', 'InvalidHttp')) { return [pscustomobject]@{ Kind = 'PortConflict'; State = $state; ExitCode = $null; Elapsed = $elapsed } }
        if ($null -ne $Owner -and $Owner.Process.HasExited) { return [pscustomobject]@{ Kind = 'ProcessExited'; State = $state; ExitCode = $Owner.Process.ExitCode; Elapsed = $elapsed } }
        if ($TimeoutSeconds -gt 0 -and $elapsed.TotalSeconds -ge $TimeoutSeconds) { return [pscustomobject]@{ Kind = 'Timeout'; State = $state; ExitCode = $null; Elapsed = $elapsed } }
        Start-Sleep -Milliseconds $PollMilliseconds
    }
}

function Open-VCClient {
    param([Parameter(Mandatory = $true)][uri]$Uri)
    return Start-Process -FilePath $Uri.AbsoluteUri -PassThru
}
