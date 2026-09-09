param(
    [switch]$SelfTest,
    [switch]$AutomationTest,
    [ValidateRange(1, 65535)]
    [int]$AutomationPort = 18893
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$repoRoot = Split-Path -Parent $PSScriptRoot
$windowsScript = Join-Path $PSScriptRoot 'windows.ps1'
$launcherHelper = Join-Path $PSScriptRoot 'windows-launcher.ps1'
. $launcherHelper
$runtimeDirectory = Join-Path $repoRoot '.runtime\server-gui'
$settingsPath = Join-Path $runtimeDirectory 'settings.json'
$stdoutPath = Join-Path $runtimeDirectory 'server.stdout.log'
$stderrPath = Join-Path $runtimeDirectory 'server.stderr.log'
$powershellPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$taskkillPath = "$env:SystemRoot\System32\taskkill.exe"

$script:serverProcess = $null
$script:serverOwner = $null
$script:externalServer = $false
$script:allowExit = $false
$script:trayHintShown = $false
$script:lastLogSignature = ''

function Get-DefaultGuiSettings {
    return [pscustomobject]@{
        port = 18888
        bindLan = $false
        skipDownloads = $false
        openClient = $true
    }
}

function Get-GuiSettings {
    $settings = Get-DefaultGuiSettings
    if (!(Test-Path -LiteralPath $settingsPath)) {
        return $settings
    }
    try {
        $saved = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
        if ($saved.port -ge 1 -and $saved.port -le 65535) {
            $settings.port = [int]$saved.port
        }
        $settings.bindLan = [bool]$saved.bindLan
        $settings.skipDownloads = [bool]$saved.skipDownloads
        $settings.openClient = [bool]$saved.openClient
    } catch {
        # Invalid UI preferences never prevent the server shell from opening.
    }
    return $settings
}

function Save-GuiSettings {
    New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null
    $settings = [ordered]@{
        port = [int]$script:portControl.Value
        bindLan = $script:bindControl.SelectedIndex -eq 1
        skipDownloads = $script:skipDownloadsControl.Checked
        openClient = $script:openClientControl.Checked
    }
    $settings | ConvertTo-Json | Set-Content -LiteralPath $settingsPath -Encoding UTF8
}

function Get-ClientUrl {
    return "http://127.0.0.1:$([int]$script:portControl.Value)/"
}

function Test-ServerPort {
    param([int]$Port)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (!$connection.AsyncWaitHandle.WaitOne(100)) {
            return $false
        }
        $client.EndConnect($connection)
        return $true
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Set-ServerStatus {
    param(
        [string]$Text,
        [System.Drawing.Color]$Color
    )
    $script:statusValue.Text = $Text
    $script:statusValue.ForeColor = $Color
    $script:notifyIcon.Text = "VCClient Server - $Text"
}

function Refresh-LogView {
    $files = @($stdoutPath, $stderrPath)
    $signatureParts = foreach ($path in $files) {
        if (Test-Path -LiteralPath $path) {
            $item = Get-Item -LiteralPath $path
            "$($item.Length):$($item.LastWriteTimeUtc.Ticks)"
        } else {
            'missing'
        }
    }
    $signature = $signatureParts -join '|'
    if ($signature -eq $script:lastLogSignature) {
        return
    }
    $script:lastLogSignature = $signature
    $sections = @()
    if (Test-Path -LiteralPath $stdoutPath) {
        $stdout = Get-Content -LiteralPath $stdoutPath -Tail 160 -ErrorAction SilentlyContinue
        if ($stdout) {
            $sections += $stdout
        }
    }
    if (Test-Path -LiteralPath $stderrPath) {
        $stderr = Get-Content -LiteralPath $stderrPath -Tail 80 -ErrorAction SilentlyContinue
        if ($stderr) {
            $sections += '--- stderr ---'
            $sections += $stderr
        }
    }
    $script:logControl.Lines = [string[]]$sections
    $script:logControl.SelectionStart = $script:logControl.TextLength
    $script:logControl.ScrollToCaret()
}

function Update-Controls {
    $running = $null -ne $script:serverProcess -and !$script:serverProcess.HasExited
    $port = [int]$script:portControl.Value
    $state = Get-VCClientEndpointState -Port $port
    $script:lastEndpointState = $state
    $ready = $state.IsVCClient
    if ($ready -and ($running -or $script:externalServer)) {
        $label = if ($state.ModelReady) { 'Running' } else { 'Ready (no model)' }
        Set-ServerStatus -Text $label -Color ([System.Drawing.Color]::ForestGreen)
    } elseif ($state.Kind -in @('ForeignHttp', 'InvalidHttp', 'TcpOnly')) {
        Set-ServerStatus -Text "Port conflict ($($state.Kind))" -Color ([System.Drawing.Color]::Firebrick)
    } elseif ($running) {
        Set-ServerStatus -Text 'Starting' -Color ([System.Drawing.Color]::DarkOrange)
    } elseif ($null -ne $script:serverProcess -and $script:serverProcess.HasExited) {
        $exitCode = $script:serverProcess.ExitCode
        $script:serverProcess.Dispose()
        $script:serverProcess = $null
        $script:serverOwner = $null
        if ($exitCode -eq 0) {
            Set-ServerStatus -Text 'Stopped' -Color ([System.Drawing.Color]::DimGray)
        } else {
            Set-ServerStatus -Text "Exited ($exitCode)" -Color ([System.Drawing.Color]::Firebrick)
        }
    } else {
        Set-ServerStatus -Text 'Stopped' -Color ([System.Drawing.Color]::DimGray)
    }

    $running = $null -ne $script:serverProcess -and !$script:serverProcess.HasExited
    $script:startButton.Enabled = !$running
    $script:stopButton.Enabled = $running -and $null -ne $script:serverOwner -and $script:serverOwner.OwnsProcess
    $script:portControl.Enabled = !$running -and !$script:externalServer
    $script:bindControl.Enabled = !$running -and !$script:externalServer
    $script:skipDownloadsControl.Enabled = !$running -and !$script:externalServer
    $script:trayStartItem.Enabled = !$running -and !$script:externalServer
    $script:trayStopItem.Enabled = $running -and $null -ne $script:serverOwner -and $script:serverOwner.OwnsProcess
    Refresh-LogView
}

function Open-Client {
    $state = Get-VCClientEndpointState -Port ([int]$script:portControl.Value)
    if (!$state.IsVCClient) {
        $message = switch ($state.Kind) {
            'ForeignHttp' { [regex]::Unescape('\u6307\u5b9a\u30dd\u30fc\u30c8\u306fVCClient\u3067\u306f\u306a\u3044HTTP\u30b5\u30fc\u30d3\u30b9\u3067\u4f7f\u7528\u3055\u308c\u3066\u3044\u307e\u3059\u3002') }
            'InvalidHttp' { [regex]::Unescape('\u6307\u5b9a\u30dd\u30fc\u30c8\u306e\u5fdc\u7b54\u3092VCClient\u3068\u3057\u3066\u78ba\u8a8d\u3067\u304d\u307e\u305b\u3093\u3067\u3057\u305f\u3002') }
            'TcpOnly' { [regex]::Unescape('\u6307\u5b9a\u30dd\u30fc\u30c8\u306f\u958b\u3044\u3066\u3044\u307e\u3059\u304c\u3001VCClient\u306eHTTP\u5fdc\u7b54\u304c\u3042\u308a\u307e\u305b\u3093\u3002') }
            'HttpTimeout' { [regex]::Unescape('VCClient\u306e\u5fdc\u7b54\u304c\u30bf\u30a4\u30e0\u30a2\u30a6\u30c8\u3057\u307e\u3057\u305f\u3002') }
            default { [regex]::Unescape('VCClient\u304c\u8d77\u52d5\u3057\u3066\u3044\u306a\u3044\u305f\u3081\u3001Desktop Client\u3092\u958b\u3051\u307e\u305b\u3093\u3002') }
        }
        [System.Windows.Forms.MessageBox]::Show(
            $message,
            'VCClient Server',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
        return $false
    }
    try {
        [void](Start-VCClientDesktop -RepositoryRoot $repoRoot -Url (Get-ClientUrl))
        return $true
    } catch {
        [System.Windows.Forms.MessageBox]::Show(
            $_.Exception.Message,
            'Unable to open Desktop Client',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
        return $false
    }
}

function Start-Server {
    if ($null -ne $script:serverProcess -and !$script:serverProcess.HasExited) {
        return
    }
    $port = [int]$script:portControl.Value
    $existing = Get-VCClientEndpointState -Port $port
    if ($existing.IsVCClient) {
        $script:externalServer = $true
        Set-ServerStatus -Text $(if ($existing.ModelReady) { 'Running' } else { 'Ready (no model)' }) -Color ([System.Drawing.Color]::ForestGreen)
        return
    }
    if ($existing.Kind -in @('ForeignHttp', 'InvalidHttp', 'TcpOnly')) {
        [System.Windows.Forms.MessageBox]::Show(
            "Port $port is already in use. Choose another port or stop the other service.",
            'VCClient Server',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning
        ) | Out-Null
        return
    }

    Save-GuiSettings
    New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null
    Set-Content -LiteralPath $stdoutPath -Value '' -Encoding UTF8
    Set-Content -LiteralPath $stderrPath -Value '' -Encoding UTF8
    $script:lastLogSignature = ''

    $bindAddress = if ($script:bindControl.SelectedIndex -eq 1) {
        '0.0.0.0'
    } else {
        '127.0.0.1'
    }
    try {
        $script:serverOwner = Start-VCClientServerProcess -WindowsScript $windowsScript -WorkingDirectory $repoRoot `
            -Port $port -BindHost $bindAddress -SkipDownloads:$script:skipDownloadsControl.Checked `
            -WindowStyle Hidden -StandardOutputPath $stdoutPath -StandardErrorPath $stderrPath
        $script:serverProcess = $script:serverOwner.Process
        $script:externalServer = $false
        Set-ServerStatus -Text 'Starting' -Color ([System.Drawing.Color]::DarkOrange)
        $script:startupOpenPending = $script:openClientControl.Checked
    } catch {
        $script:serverProcess = $null
        $script:serverOwner = $null
        [System.Windows.Forms.MessageBox]::Show(
            $_.Exception.Message,
            'Unable to start VCClient Server',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
    }
    Update-Controls
}

function Stop-Server {
    if ($null -eq $script:serverProcess -or $script:serverProcess.HasExited) {
        return $true
    }
    try {
        $result = Stop-VCClientOwnedProcess -Owner $script:serverOwner
        if (!$result.Success) { throw $result.Error }
        $script:serverOwner = $null
        $script:serverProcess = $null
    } catch {
        [System.Windows.Forms.MessageBox]::Show(
            $_.Exception.Message,
            'Unable to stop VCClient Server',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
        Update-Controls
        return $false
    }
    $script:startupOpenPending = $false
    $script:externalServer = $false
    Update-Controls
    return $true
}

function Show-MainWindow {
    $script:form.Show()
    $script:form.WindowState = [System.Windows.Forms.FormWindowState]::Normal
    $script:form.Activate()
}

function Exit-Gui {
    $running = $null -ne $script:serverProcess -and !$script:serverProcess.HasExited
    if ($running) {
        $answer = [System.Windows.Forms.MessageBox]::Show(
            'Stop VCClient Server and exit?',
            'VCClient Server',
            [System.Windows.Forms.MessageBoxButtons]::YesNo,
            [System.Windows.Forms.MessageBoxIcon]::Question
        )
        if ($answer -ne [System.Windows.Forms.DialogResult]::Yes) {
            return
        }
        if (!(Stop-Server)) {
            return
        }
    }
    Save-GuiSettings
    $script:allowExit = $true
    $script:notifyIcon.Visible = $false
    $script:notifyIcon.Dispose()
    $script:form.Close()
}

if ($SelfTest) {
    $settings = Get-GuiSettings
    [ordered]@{
        status = 'ok'
        platform = [Environment]::OSVersion.Platform.ToString()
        windowsForms = $null -ne [System.Windows.Forms.Form]
        notifyIcon = $null -ne [System.Windows.Forms.NotifyIcon]
        defaultPort = $settings.port
        cliEntrypoint = Test-Path -LiteralPath $windowsScript
    } | ConvertTo-Json -Compress
    exit 0
}

$savedSettings = Get-GuiSettings
$script:startupOpenPending = $false

$script:form = [System.Windows.Forms.Form]::new()
$script:form.Text = 'VCClient Server'
$script:form.ClientSize = [System.Drawing.Size]::new(760, 520)
$script:form.MinimumSize = [System.Drawing.Size]::new(700, 480)
$script:form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$script:form.Icon = [System.Drawing.SystemIcons]::Application

$title = [System.Windows.Forms.Label]::new()
$title.Text = 'VCClient Server Control'
$title.Font = [System.Drawing.Font]::new('Segoe UI', 16, [System.Drawing.FontStyle]::Bold)
$title.AutoSize = $true
$title.Location = [System.Drawing.Point]::new(18, 14)
$script:form.Controls.Add($title)

$portLabel = [System.Windows.Forms.Label]::new()
$portLabel.Text = 'Port'
$portLabel.AutoSize = $true
$portLabel.Location = [System.Drawing.Point]::new(20, 64)
$script:form.Controls.Add($portLabel)

$script:portControl = [System.Windows.Forms.NumericUpDown]::new()
$script:portControl.Minimum = 1
$script:portControl.Maximum = 65535
$script:portControl.Value = $savedSettings.port
$script:portControl.Location = [System.Drawing.Point]::new(70, 60)
$script:portControl.Size = [System.Drawing.Size]::new(100, 25)
$script:form.Controls.Add($script:portControl)

$bindLabel = [System.Windows.Forms.Label]::new()
$bindLabel.Text = 'Bind'
$bindLabel.AutoSize = $true
$bindLabel.Location = [System.Drawing.Point]::new(195, 64)
$script:form.Controls.Add($bindLabel)

$script:bindControl = [System.Windows.Forms.ComboBox]::new()
$script:bindControl.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
$script:bindControl.Items.AddRange(@('Local only (127.0.0.1)', 'LAN (0.0.0.0)'))
$script:bindControl.SelectedIndex = if ($savedSettings.bindLan) { 1 } else { 0 }
$script:bindControl.Location = [System.Drawing.Point]::new(240, 60)
$script:bindControl.Size = [System.Drawing.Size]::new(190, 25)
$script:form.Controls.Add($script:bindControl)

$script:skipDownloadsControl = [System.Windows.Forms.CheckBox]::new()
$script:skipDownloadsControl.Text = 'Skip weight downloads'
$script:skipDownloadsControl.Checked = $savedSettings.skipDownloads
$script:skipDownloadsControl.AutoSize = $true
$script:skipDownloadsControl.Location = [System.Drawing.Point]::new(455, 62)
$script:form.Controls.Add($script:skipDownloadsControl)

$script:openClientControl = [System.Windows.Forms.CheckBox]::new()
$script:openClientControl.Text = 'Open Client when ready'
$script:openClientControl.Checked = $savedSettings.openClient
$script:openClientControl.AutoSize = $true
$script:openClientControl.Location = [System.Drawing.Point]::new(590, 62)
$script:form.Controls.Add($script:openClientControl)

$script:startButton = [System.Windows.Forms.Button]::new()
$script:startButton.Text = 'Start'
$script:startButton.Location = [System.Drawing.Point]::new(20, 102)
$script:startButton.Size = [System.Drawing.Size]::new(100, 34)
$script:startButton.Add_Click({ Start-Server })
$script:form.Controls.Add($script:startButton)

$script:stopButton = [System.Windows.Forms.Button]::new()
$script:stopButton.Text = 'Stop'
$script:stopButton.Location = [System.Drawing.Point]::new(130, 102)
$script:stopButton.Size = [System.Drawing.Size]::new(100, 34)
$script:stopButton.Add_Click({ Stop-Server })
$script:form.Controls.Add($script:stopButton)

$openButton = [System.Windows.Forms.Button]::new()
$openButton.Text = 'Open Client'
$openButton.Location = [System.Drawing.Point]::new(240, 102)
$openButton.Size = [System.Drawing.Size]::new(110, 34)
$openButton.Add_Click({ Open-Client })
$script:form.Controls.Add($openButton)

$copyButton = [System.Windows.Forms.Button]::new()
$copyButton.Text = 'Copy URL'
$copyButton.Location = [System.Drawing.Point]::new(360, 102)
$copyButton.Size = [System.Drawing.Size]::new(100, 34)
$copyButton.Add_Click({
    [System.Windows.Forms.Clipboard]::SetText((Get-ClientUrl))
})
$script:form.Controls.Add($copyButton)

$logsButton = [System.Windows.Forms.Button]::new()
$logsButton.Text = 'Open Logs'
$logsButton.Location = [System.Drawing.Point]::new(470, 102)
$logsButton.Size = [System.Drawing.Size]::new(100, 34)
$logsButton.Add_Click({
    New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null
    Start-Process -FilePath $runtimeDirectory
})
$script:form.Controls.Add($logsButton)

$statusLabel = [System.Windows.Forms.Label]::new()
$statusLabel.Text = 'Status:'
$statusLabel.AutoSize = $true
$statusLabel.Location = [System.Drawing.Point]::new(600, 111)
$script:form.Controls.Add($statusLabel)

$script:statusValue = [System.Windows.Forms.Label]::new()
$script:statusValue.Text = 'Stopped'
$script:statusValue.Font = [System.Drawing.Font]::new('Segoe UI', 9, [System.Drawing.FontStyle]::Bold)
$script:statusValue.AutoSize = $true
$script:statusValue.Location = [System.Drawing.Point]::new(650, 111)
$script:form.Controls.Add($script:statusValue)

$logLabel = [System.Windows.Forms.Label]::new()
$logLabel.Text = 'Server output (latest lines)'
$logLabel.AutoSize = $true
$logLabel.Location = [System.Drawing.Point]::new(20, 154)
$script:form.Controls.Add($logLabel)

$script:logControl = [System.Windows.Forms.TextBox]::new()
$script:logControl.Multiline = $true
$script:logControl.ReadOnly = $true
$script:logControl.ScrollBars = [System.Windows.Forms.ScrollBars]::Both
$script:logControl.WordWrap = $false
$script:logControl.Font = [System.Drawing.Font]::new('Consolas', 9)
$script:logControl.Anchor = [System.Windows.Forms.AnchorStyles]::Top -bor [System.Windows.Forms.AnchorStyles]::Bottom -bor [System.Windows.Forms.AnchorStyles]::Left -bor [System.Windows.Forms.AnchorStyles]::Right
$script:logControl.Location = [System.Drawing.Point]::new(20, 178)
$script:logControl.Size = [System.Drawing.Size]::new(720, 320)
$script:form.Controls.Add($script:logControl)

$trayMenu = [System.Windows.Forms.ContextMenuStrip]::new()
$script:trayShowItem = $trayMenu.Items.Add('Show')
$script:trayOpenItem = $trayMenu.Items.Add('Open Client')
$trayMenu.Items.Add([System.Windows.Forms.ToolStripSeparator]::new()) | Out-Null
$script:trayStartItem = $trayMenu.Items.Add('Start Server')
$script:trayStopItem = $trayMenu.Items.Add('Stop Server')
$trayMenu.Items.Add([System.Windows.Forms.ToolStripSeparator]::new()) | Out-Null
$script:trayExitItem = $trayMenu.Items.Add('Exit')

$script:notifyIcon = [System.Windows.Forms.NotifyIcon]::new()
$script:notifyIcon.Icon = [System.Drawing.SystemIcons]::Application
$script:notifyIcon.Text = 'VCClient Server - Stopped'
$script:notifyIcon.ContextMenuStrip = $trayMenu
$script:notifyIcon.Visible = $true
$script:notifyIcon.Add_DoubleClick({ Show-MainWindow })
$script:trayShowItem.Add_Click({ Show-MainWindow })
$script:trayOpenItem.Add_Click({ Open-Client })
$script:trayStartItem.Add_Click({ Start-Server })
$script:trayStopItem.Add_Click({ Stop-Server })
$script:trayExitItem.Add_Click({ Exit-Gui })

$timer = [System.Windows.Forms.Timer]::new()
$timer.Interval = 750
$timer.Add_Tick({
    Update-Controls
    $isReady = $null -ne $script:lastEndpointState -and $script:lastEndpointState.IsHttpReady
    if ($isReady -and $script:startupOpenPending) {
        $script:startupOpenPending = $false
        [void](Open-Client)
    }
})
$timer.Start()

$script:form.Add_Resize({
    if ($script:form.WindowState -eq [System.Windows.Forms.FormWindowState]::Minimized) {
        $script:form.Hide()
        if (!$script:trayHintShown) {
            $script:notifyIcon.ShowBalloonTip(
                2500,
                'VCClient Server',
                'The server control is still available in the system tray.',
                [System.Windows.Forms.ToolTipIcon]::Info
            )
            $script:trayHintShown = $true
        }
    }
})

$script:form.Add_FormClosing({
    param($sender, $eventArgs)
    if (!$script:allowExit) {
        $eventArgs.Cancel = $true
        $sender.Hide()
        $script:notifyIcon.ShowBalloonTip(
            2000,
            'VCClient Server',
            'Use the tray menu to exit and stop the server.',
            [System.Windows.Forms.ToolTipIcon]::Info
        )
    }
})

Update-Controls
if ($AutomationTest) {
    if (Test-ServerPort -Port $AutomationPort) {
        throw "Automation test port $AutomationPort is already in use."
    }
    $script:portControl.Value = $AutomationPort
    $script:skipDownloadsControl.Checked = $true
    $script:openClientControl.Checked = $false
    $ready = $false
    try {
        Start-Server
        $deadline = [DateTime]::UtcNow.AddSeconds(120)
        while ([DateTime]::UtcNow -lt $deadline) {
            [System.Windows.Forms.Application]::DoEvents()
            Update-Controls
            if ($script:statusValue.Text -in @('Running', 'Ready (no model)')) {
                $ready = $true
                break
            }
            if ($null -eq $script:serverProcess) {
                break
            }
            Start-Sleep -Milliseconds 250
        }
        if (!$ready) {
            throw "GUI-managed server did not become ready on port $AutomationPort."
        }
    } finally {
        Stop-Server
        $script:notifyIcon.Visible = $false
        $script:notifyIcon.Dispose()
        $script:form.Dispose()
    }
    $stopped = !(Test-ServerPort -Port $AutomationPort)
    if (!$stopped) {
        throw "GUI-managed server did not stop on port $AutomationPort."
    }
    [ordered]@{
        status = 'ok'
        port = $AutomationPort
        ready = $ready
        processTreeStopped = $stopped
        stdoutLog = Test-Path -LiteralPath $stdoutPath
        stderrLog = Test-Path -LiteralPath $stderrPath
    } | ConvertTo-Json -Compress
    exit 0
}
[System.Windows.Forms.Application]::Run($script:form)
