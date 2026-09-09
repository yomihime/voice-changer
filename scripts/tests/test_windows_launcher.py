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


class ProcessOwnershipTest(unittest.TestCase):
    def test_desktop_urls_are_serialized_after_all_switches(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / ".runtime" / "desktop" / "vcclient-desktop.exe"
            executable.parent.mkdir(parents=True)
            executable.touch()
            command = (
                f"$script:captured = @(); "
                "function Start-Process { param([string]$FilePath,[string]$ArgumentList,"
                "[string]$WorkingDirectory,[switch]$PassThru,[string]$WindowStyle); "
                "$script:captured += $ArgumentList; return [pscustomobject]@{Id=1;"
                "StartTime=[datetime]::Now} }; "
                f". {ps_quote(HELPER)}; "
                f"Start-VCClientDesktop -RepositoryRoot {ps_quote(directory)} "
                f"-Url 'http://127.0.0.1:18888/' -WaitForWindow | Out-Null; "
                f"Open-VCClient -Uri ([uri]'http://127.0.0.1:18888/') -Mode Desktop "
                f"-DesktopExecutable {ps_quote(executable)} "
                "-AdditionalArguments @('--profile-root', 'C:\\tmp profile', '--deny-media', '--hidden') | Out-Null; "
                "$script:captured | ConvertTo-Json -Compress"
            )
            result = powershell(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = json.loads(result.stdout)
        self.assertEqual(captured[0], "--wait --url http://127.0.0.1:18888/")
        self.assertTrue(captured[1].startswith('--profile-root "C:\\tmp profile" --deny-media --hidden --url '))
        self.assertTrue(captured[1].endswith('http://127.0.0.1:18888/'))

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
