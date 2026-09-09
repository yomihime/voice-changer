"""Focused server GUI behavior tests using PowerShell fixtures, without WinForms or audio."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "scripts" / "server-gui.ps1"
POWERSHELL = Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def powershell(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        creationflags=HIDDEN,
    )


def quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


class WindowsGuiBehaviorTest(unittest.TestCase):
    def test_review_probe_blocks_foreign_open_and_keeps_window_on_stop_failure(self):
        command = f"""
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile({quote(GUI)},[ref]$tokens,[ref]$errors)
foreach($name in @('Open-Client','Stop-Server','Exit-Gui')) {{
  $fn=$ast.Find({{param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name}},$true)
  Invoke-Expression $fn.Extent.Text
}}
Add-Type @"
namespace System.Windows.Forms {{ public enum DialogResult {{ Yes, No, OK }} public enum MessageBoxButtons {{ YesNo, OK }} public enum MessageBoxIcon {{ Question, Error }} public static class MessageBox {{ public static int Calls=0; public static DialogResult Show(string m,string t,MessageBoxButtons b,MessageBoxIcon i) {{ Calls++; return DialogResult.Yes; }} }} }}
"@
$script:repoRoot={quote(ROOT)}; $script:portControl=[pscustomobject]@{{Value=18888}}; $script:opened=0; $script:probed=0
function Get-ClientUrl {{ 'http://127.0.0.1:18888/' }}
function Get-VCClientEndpointState {{ $script:probed++; [pscustomobject]@{{Kind='ForeignHttp';IsVCClient=$false}} }}
function Start-VCClientDesktop {{ $script:opened++ }}
Open-Client
$script:serverProcess=[pscustomobject]@{{HasExited=$false}}; $script:serverOwner=[pscustomobject]@{{OwnsProcess=$true}}
$script:allowExit=$false; $script:closed=$false; $script:disposed=$false
$script:notifyIcon=[pscustomobject]@{{Visible=$true}}; $script:notifyIcon | Add-Member ScriptMethod Dispose {{$script:disposed=$true}}
$script:form=[pscustomobject]@{{}}; $script:form | Add-Member ScriptMethod Close {{$script:closed=$true}}
function Save-GuiSettings {{}}; function Update-Controls {{}}
function Stop-VCClientOwnedProcess {{ [pscustomobject]@{{Success=$false;Error='fixture access denied'}} }}
Exit-Gui
[pscustomobject]@{{desktopCalls=$script:opened;identityProbes=$script:probed;closed=$script:closed;disposed=$script:disposed;allowExit=$script:allowExit;ownerStillLive=$script:serverOwner.OwnsProcess}} | ConvertTo-Json -Compress
"""
        result = powershell(command)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        outcome = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(outcome["desktopCalls"], 0)
        self.assertEqual(outcome["identityProbes"], 1)
        self.assertFalse(outcome["closed"])
        self.assertFalse(outcome["disposed"])
        self.assertFalse(outcome["allowExit"])
        self.assertTrue(outcome["ownerStillLive"])

    def test_timer_opens_when_first_sync_is_already_ready_and_only_once(self):
        command = f"""
$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile({quote(GUI)},[ref]$tokens,[ref]$errors)
$timerCall=$ast.Find({{param($n) $n -is [System.Management.Automation.Language.InvokeMemberExpressionAst] -and $n.Member.Value -eq 'Add_Tick'}},$true)
Add-Type @"
namespace System.Windows.Forms {{ public enum MessageBoxButtons {{ OK }} public enum MessageBoxIcon {{ Error }} public static class MessageBox {{ public static DialogResult Show(string m,string t,MessageBoxButtons b,MessageBoxIcon i) {{ return DialogResult.OK; }} }} public enum DialogResult {{ OK }} }}
"@
$script:statusValue=[pscustomobject]@{{Text='Starting'}}
$script:lastEndpointState=[pscustomobject]@{{IsHttpReady=$true}}
$script:startupOpenPending=$true
$script:opened=0
function Get-VCClientEndpointState {{ [pscustomobject]@{{Kind='VCClientNoModel';IsVCClient=$true;IsHttpReady=$true;ModelReady=$false}} }}
function Get-ClientUrl {{ 'http://127.0.0.1:18888/' }}
function Start-VCClientDesktop {{ $script:opened++ }}
function Open-Client {{ $script:opened++ }}
function Update-Controls {{ $script:statusValue.Text='Ready (no model)'; $script:lastEndpointState=[pscustomobject]@{{IsHttpReady=$true}} }}
& $timerCall.Arguments[0].ScriptBlock.GetScriptBlock()
& $timerCall.Arguments[0].ScriptBlock.GetScriptBlock()
[pscustomobject]@{{desktopCalls=$script:opened;pending=$script:startupOpenPending;state=$script:statusValue.Text}} | ConvertTo-Json -Compress
"""
        result = powershell(command)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        outcome = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(outcome["desktopCalls"], 1)
        self.assertFalse(outcome["pending"])
        self.assertEqual(outcome["state"], "Ready (no model)")


if __name__ == "__main__":
    unittest.main()
