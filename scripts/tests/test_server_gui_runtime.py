"""Launcher tests use synthetic HTTP endpoints and fake processes only."""

from __future__ import annotations

import http.server
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from scripts.server_gui import runtime


def server_info(ready=False):
    return {"status": "OK", "python": "3.12 fixture", "modelSlots": [], "sampleModels": [], "gpus": [],
            "voiceChangerParams": {"model_dir": "models", "sample_mode": "production", "allow_downloads": False},
            "serverAudioStated": 0, "pipelineInfo": {"ready": ready}}


class Endpoint:
    def __init__(self, payload, status=200):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(status)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class SettingsTests(unittest.TestCase):
    def test_settings_roundtrip_and_old_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = runtime.Settings(19000, True, True, False)
            runtime.save_settings(root, settings)
            self.assertEqual(runtime.read_settings(root), settings)
            path = root / ".runtime/server-gui/settings.json"
            contents = path.read_text()
            self.assertIn('"bindLan": true', contents)
            path.write_text(contents, encoding="utf-8-sig")
            self.assertEqual(runtime.read_settings(root), settings)

    def test_partial_invalid_preferences_keep_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(runtime.read_settings(root), runtime.Settings())
            runtime.save_settings(root, runtime.Settings())
            path = root / ".runtime/server-gui/settings.json"
            for body in ("not JSON", "[]", '{"port": 0, "bindLan": "false"}', '{"port": true}'):
                path.write_text(body)
                self.assertEqual(runtime.read_settings(root), runtime.Settings())

    def test_invalid_port_rejected(self):
        for port in (0, 65536, True, "18888"):
            with self.assertRaises(ValueError):
                runtime.Settings(port=port)


class EndpointTests(unittest.TestCase):
    def test_identity_and_model_state_are_independent(self):
        for ready in (False, True, "true"):
            with Endpoint(server_info(ready)) as endpoint:
                state = runtime.probe_endpoint(endpoint.port)
            self.assertTrue(state.ready)
            self.assertEqual(state.model_ready, ready is True)
            self.assertEqual(state.url, f"http://127.0.0.1:{endpoint.port}/")

    def test_foreign_invalid_http_and_redirects_are_not_server(self):
        cases = [({"status": "OK"}, 200, "ForeignHttp"), (b"<html>hi</html>", 200, "InvalidHttp"),
                 (server_info(), 302, "ForeignHttp"), (server_info(), 503, "ForeignHttp")]
        for payload, status, expected in cases:
            with Endpoint(payload, status) as endpoint:
                result = runtime.probe_endpoint(endpoint.port)
            self.assertEqual(result.kind, expected)
            self.assertFalse(result.ready)

    def test_rejects_schema_lookalikes(self):
        for key, value in (("modelSlots", {}), ("python", ""), ("voiceChangerParams", {}), ("serverAudioStated", None)):
            info = server_info()
            info[key] = value
            self.assertFalse(runtime._is_server_info(info))

    def test_closed_and_occupied_timeouts_differ(self):
        with patch.object(runtime.http.client, "HTTPConnection") as connection, patch.object(runtime, "_tcp_open") as tcp:
            connection.return_value.request.side_effect = TimeoutError("fixture")
            tcp.return_value = False
            self.assertEqual(runtime.probe_endpoint(18888).kind, "Closed")
            tcp.return_value = True
            self.assertEqual(runtime.probe_endpoint(18888).kind, "HttpTimeout")


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "scripts").mkdir()
        (self.root / "scripts/windows.ps1").touch()
        self.controller = runtime.ServerController(self.root)

    def test_external_server_never_becomes_owned(self):
        with patch.object(runtime, "probe_endpoint", return_value=runtime.EndpointState("VCClientReady", 18888)), \
                patch.object(runtime.subprocess, "Popen") as launch:
            self.assertTrue(self.controller.start(runtime.Settings()).ready)
            self.assertFalse(self.controller.running)
            self.assertFalse(self.controller.stop())
            launch.assert_not_called()

    def test_running_does_not_wait_for_start_stop_operation_lock(self):
        process = Mock(pid=4321)
        process.poll.return_value = None
        self.controller._process = process
        observed = threading.Event()

        def read_running():
            if self.controller.running:
                observed.set()

        with self.controller._mutation_lock:
            reader = threading.Thread(target=read_running, daemon=True)
            reader.start()
            responsive = observed.wait(0.5)
        reader.join(timeout=1)
        self.assertTrue(responsive, "GUI status reads must not wait for process/network operations")

    def test_conflicting_ports_never_launch(self):
        for kind in ("ForeignHttp", "InvalidHttp", "TcpOnly", "HttpTimeout"):
            with patch.object(runtime, "probe_endpoint", return_value=runtime.EndpointState(kind, 18888)), \
                    patch.object(runtime.subprocess, "Popen") as launch:
                with self.assertRaises(RuntimeError):
                    self.controller.start(runtime.Settings())
                launch.assert_not_called()

    def test_start_uses_hidden_owned_process_and_explicit_arguments(self):
        process = Mock(pid=4321)
        process.poll.return_value = None
        library = Mock()
        with patch.object(runtime, "probe_endpoint", return_value=runtime.EndpointState("Closed", 18888)), \
                patch.object(runtime, "_process_library", return_value=library), \
                patch.object(runtime.subprocess, "Popen", return_value=process) as launch:
            state = self.controller.start(runtime.Settings(18888, True, True, False))
        self.assertEqual(state.kind, "Starting")
        self.assertTrue(self.controller.running)
        arguments, options = launch.call_args
        self.assertEqual(arguments[0][-5:], ["-p", "18888", "--host", "0.0.0.0", "--skip-downloads"])
        self.assertEqual(options["creationflags"], getattr(runtime.subprocess, "CREATE_NO_WINDOW", 0))
        self.assertEqual(options["env"]["PYTHONUNBUFFERED"], "1")
        with patch.object(runtime, "_process_library", return_value=library), patch.object(runtime, "_stop_tree") as stop:
            self.assertTrue(self.controller.stop())
            stop.assert_called_once_with(library.Process.return_value, library)
        self.assertFalse(self.controller.running)

    def test_open_client_requires_identity_and_uses_browser(self):
        with patch.object(runtime, "probe_endpoint", return_value=runtime.EndpointState("ForeignHttp", 18888)), \
                patch.object(runtime.webbrowser, "open") as launch:
            with self.assertRaises(RuntimeError):
                self.controller.open_client(18888)
            launch.assert_not_called()
        with patch.object(runtime, "probe_endpoint", return_value=runtime.EndpointState("VCClientNoModel", 18888)), \
                patch.object(runtime.webbrowser, "open", return_value=True) as launch:
            self.controller.open_client(18888)
            launch.assert_called_once_with("http://127.0.0.1:18888/")
        with patch.object(runtime, "probe_endpoint", return_value=runtime.EndpointState("VCClientNoModel", 18888)), \
                patch.object(runtime.webbrowser, "open", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "手动访问"):
                self.controller.open_client(18888)

    def test_log_tail_is_bounded_and_tolerates_missing_files(self):
        self.assertEqual(self.controller.read_logs(), "")
        self.controller.runtime_directory.mkdir(parents=True)
        path = self.controller.runtime_directory / "server.stdout.log"
        path.write_bytes(b"old line\n" * 50000 + "末尾一行\nlast line\n".encode())
        self.assertEqual(self.controller.read_logs(2), "[server.stdout.log]\n末尾一行\nlast line")


class ProcessTreeTests(unittest.TestCase):
    def test_freezes_parent_before_collecting_and_kills_children_first(self):
        events = []

        class Gone(Exception):
            pass

        def process(pid, children):
            item = Mock(pid=pid)
            item.create_time.return_value = pid * 10
            item.suspend.side_effect = lambda: events.append(("suspend", pid))
            item.children.side_effect = lambda: events.append(("children", pid)) or children
            item.kill.side_effect = lambda: events.append(("kill", pid))
            return item

        child = process(2, [])
        owner = process(1, [child])
        library = Mock(NoSuchProcess=Gone)
        library.wait_procs.return_value = ([], [])
        runtime._stop_tree(owner, library)
        self.assertEqual(events, [("suspend", 1), ("children", 1), ("suspend", 2), ("children", 2), ("kill", 2), ("kill", 1)])

    def test_failed_stop_resumes_frozen_processes(self):
        class Gone(Exception):
            pass

        owner = Mock(pid=1)
        owner.create_time.return_value = 10
        owner.children.return_value = []
        owner.kill.side_effect = PermissionError("fixture")
        library = Mock(NoSuchProcess=Gone)
        with self.assertRaises(PermissionError):
            runtime._stop_tree(owner, library)
        owner.resume.assert_called_once()

    def test_resume_failure_does_not_skip_survivors_or_replace_stop_error(self):
        class Gone(Exception):
            pass

        owner, child = Mock(pid=1), Mock(pid=2)
        owner.create_time.return_value = 10
        child.create_time.return_value = 20
        owner.children.return_value = [child]
        child.children.return_value = []
        stop_error = PermissionError("original stop failure")
        child.kill.side_effect = stop_error
        owner.resume.side_effect = PermissionError("parent resume denied")
        child.resume.side_effect = PermissionError("child resume denied")
        library = Mock(NoSuchProcess=Gone)
        with self.assertRaises(PermissionError) as raised:
            runtime._stop_tree(owner, library)
        self.assertIs(raised.exception, stop_error)
        owner.resume.assert_called_once()
        child.resume.assert_called_once()
        notes = "\n".join(raised.exception.__notes__)
        self.assertIn("PID 1: parent resume denied", notes)
        self.assertIn("PID 2: child resume denied", notes)

    def test_resume_failures_are_reported_when_stop_has_no_prior_error(self):
        class Gone(Exception):
            pass

        owner = Mock(pid=1)
        owner.create_time.return_value = 10
        owner.children.return_value = []
        owner.resume.side_effect = PermissionError("resume denied")
        library = Mock(NoSuchProcess=Gone)
        library.wait_procs.return_value = ([], [])
        with self.assertRaisesRegex(RuntimeError, "PID 1: resume denied"):
            runtime._stop_tree(owner, library)


if __name__ == "__main__":
    unittest.main()
