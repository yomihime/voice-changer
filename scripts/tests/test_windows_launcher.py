"""Windows launcher identity and ownership tests without browser or audio access."""

from __future__ import annotations

import http.server
import json
from pathlib import Path
import socket
import subprocess
import threading
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/windows-launcher.ps1"
CLIENT = ROOT / "scripts/start-client.ps1"
POWERSHELL = Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def vc_info(*, model_ready=None):
    info = {
        "status": "OK",
        "modelSlots": [],
        "sampleModels": [],
        "gpus": [],
        "python": "3.12 fixture",
        "voiceChangerParams": {
            "model_dir": "model_dir",
            "sample_mode": "production",
            "allow_downloads": True,
        },
        "serverAudioStated": 0,
    }
    if model_ready is not None:
        info["pipelineInfo"] = {"ready": model_ready}
    return info


class JsonServer:
    def __init__(self, payload, *, delay=0):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if delay:
                    time.sleep(delay)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *_args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def port(self):
        return self.server.server_port

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def powershell(command, *, timeout=15):
    return subprocess.run(
        [str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=HIDDEN,
    )


def endpoint_state(port, timeout_seconds=2):
    command = (
        f". {ps_quote(HELPER)}; "
        f"Get-VCClientEndpointState -Port {port} -TimeoutSeconds {timeout_seconds} | "
        "ConvertTo-Json -Depth 8 -Compress"
    )
    result = powershell(command, timeout=timeout_seconds + 10)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class EndpointIdentityTest(unittest.TestCase):
    def test_closed_port_is_not_ready(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        listener.close()
        self.assertEqual(endpoint_state(port)["Kind"], "Closed")

    def test_unrelated_json_is_rejected(self):
        with JsonServer({"service": "unrelated-application"}) as server:
            self.assertEqual(endpoint_state(server.port)["Kind"], "ForeignHttp")

    def test_invalid_json_is_rejected(self):
        with JsonServer(b"{not-json") as server:
            self.assertEqual(endpoint_state(server.port)["Kind"], "InvalidHttp")

    def test_http_timeout_is_reported(self):
        with JsonServer(vc_info(), delay=2) as server:
            self.assertEqual(endpoint_state(server.port, 1)["Kind"], "HttpTimeout")

    def test_http_ready_without_pipeline_is_not_model_ready(self):
        with JsonServer(vc_info()) as server:
            state = endpoint_state(server.port)
        self.assertEqual(state["Kind"], "VCClientNoModel")
        self.assertTrue(state["IsHttpReady"])
        self.assertFalse(state["ModelReady"])

    def test_pipeline_ready_must_be_real_boolean_true(self):
        for value, expected in ((False, "VCClientNoModel"), ("true", "VCClientNoModel"), (True, "VCClientReady")):
            with self.subTest(value=value), JsonServer(vc_info(model_ready=value)) as server:
                self.assertEqual(endpoint_state(server.port)["Kind"], expected)

    def test_client_launcher_rejects_foreign_service(self):
        with JsonServer({"service": "unrelated-application"}) as server:
            result = subprocess.run(
                [
                    str(POWERSHELL),
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(CLIENT),
                    "-Port",
                    str(server.port),
                    "-NoBrowser",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=HIDDEN,
            )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("Client URL:", result.stdout)

    def test_client_launcher_accepts_vcclient_without_model(self):
        with JsonServer(vc_info()) as server:
            result = subprocess.run(
                [str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(CLIENT),
                 "-Port", str(server.port), "-NoBrowser"],
                cwd=ROOT, capture_output=True, text=True, timeout=15, creationflags=HIDDEN)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Client URL:", result.stdout)

    def test_default_and_compatibility_switch_open_browser_without_starting_a_server(self):
        for option, opens in (("", True), ("-Browser", True), ("-NoBrowser", False)):
            with self.subTest(option=option), JsonServer(vc_info()) as server:
                command = (
                    "function Start-Process { param([string]$FilePath); "
                    'if ($FilePath -notlike "http://127.0.0.1:*") { throw "Unexpected process launch" }; '
                    'Write-Output ("BROWSER:" + $FilePath) }; '
                    f"& {ps_quote(CLIENT)} -Port {server.port} {option}"
                )
                result = powershell(command)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(f"BROWSER:http://127.0.0.1:{server.port}/" in result.stdout, opens)
                self.assertTrue(endpoint_state(server.port)["IsHttpReady"])


class ProcessOwnershipTest(unittest.TestCase):
    def test_browser_opener_passes_the_exact_compatibility_url(self):
        command = (
            "function Start-Process { param([string]$FilePath,[switch]$PassThru); "
            "return $FilePath }; "
            f". {ps_quote(HELPER)}; "
            "Open-VCClient -Uri ([uri]'http://127.0.0.1:18888/')"
        )
        result = powershell(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "http://127.0.0.1:18888/")

    def test_browser_launcher_waits_and_stops_only_its_new_server(self):
        for option, stops in (("", True), ("-Browser", True), ("-NoBrowser", False)):
            with self.subTest(option=option), tempfile.TemporaryDirectory() as directory:
                scripts = Path(directory) / "scripts"
                scripts.mkdir()
                launcher = scripts / "start-client.ps1"
                launcher.write_bytes(CLIENT.read_bytes())
                (scripts / "windows-launcher.ps1").write_text(
                    "function Get-VCClientEndpointState { [pscustomobject]@{Kind='Closed'; IsVCClient=$false} }\n"
                    "function Start-VCClientServerProcess { Write-Host 'OWNED-START'; "
                    "[pscustomobject]@{OwnsProcess=$true} }\n"
                    "function Wait-VCClientEndpoint { [pscustomobject]@{Kind='Ready'; "
                    "State=[pscustomobject]@{Kind='VCClientNoModel'}} }\n"
                    "function Stop-VCClientOwnedProcess { param($Owner); "
                    "if (!$Owner.OwnsProcess) { throw 'Unknown owner' }; "
                    "Write-Host 'OWNED-STOP'; [pscustomobject]@{Success=$true} }\n",
                    encoding="utf-8",
                )
                result = powershell(
                    "function Start-Process { Write-Host 'BROWSER-OPEN' }; "
                    "function Read-Host { Write-Host 'STOP-PROMPT'; return '' }; "
                    f"& {ps_quote(launcher)} -Port 18888 {option}"
                )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("OWNED-START", result.stdout)
            self.assertEqual("OWNED-STOP" in result.stdout, stops)
            self.assertEqual("STOP-PROMPT" in result.stdout, stops)
            if stops:
                self.assertLess(result.stdout.index("BROWSER-OPEN"), result.stdout.index("STOP-PROMPT"))
                self.assertLess(result.stdout.index("STOP-PROMPT"), result.stdout.index("OWNED-STOP"))

    def test_unowned_process_is_never_stopped(self):
        command = (
            f". {ps_quote(HELPER)}; "
            "$result = Stop-VCClientOwnedProcess -Owner ([pscustomobject]@{ OwnsProcess = $false }); "
            "$result | ConvertTo-Json -Compress"
        )
        result = powershell(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["Success"])

    def test_owned_hidden_process_is_stopped(self):
        command = (
            f". {ps_quote(HELPER)}; "
            "$process = Start-Process -FilePath $env:SystemRoot\\System32\\WindowsPowerShell\\v1.0\\powershell.exe "
            "-ArgumentList '-NoProfile -Command Start-Sleep -Seconds 60' -WindowStyle Hidden -PassThru; "
            "$owner = [pscustomobject]@{ Process=$process; ProcessId=$process.Id; "
            "ProcessStartTimeUtc=$process.StartTime.ToUniversalTime(); OwnsProcess=$true }; "
            "$result = Stop-VCClientOwnedProcess -Owner $owner; "
            "[pscustomobject]@{Success=$result.Success;Exited=$process.HasExited} | ConvertTo-Json -Compress"
        )
        result = powershell(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        outcome = json.loads(result.stdout)
        self.assertTrue(outcome["Success"])
        self.assertTrue(outcome["Exited"])


if __name__ == "__main__":
    unittest.main()
