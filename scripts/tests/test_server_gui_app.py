"""Event-loop tests with mocked processes, endpoints, preferences and tray."""

import os
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QCoreApplication, QEvent
    from PyQt6.QtTest import QTest
    from scripts.server_gui import app as gui
    from scripts.server_gui.runtime import EndpointState, Settings
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False


@unittest.skipUnless(QT_AVAILABLE, "Install requirements/windows-gui.lock to test the optional GUI")
class ServerUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    @classmethod
    def tearDownClass(cls):
        # Destroy the Windows Qt application before Python finalizes extension modules.
        if cls.qt is not None:
            from PyQt6 import sip
            sip.delete(cls.qt)
        cls.qt = None

    def setUp(self):
        self.windows = []

    def tearDown(self):
        for window in self.windows:
            window._quitting = True
            if window.refresh_timer:
                window.refresh_timer.stop()
            self.wait_for(lambda: not window._workers)
            window._allow_close = True
            window.close()
            window.deleteLater()
        if self.qt is not None:
            self.qt.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.windows.clear()

    def wait_for(self, predicate, timeout=3):
        until = time.monotonic() + timeout
        while not predicate() and time.monotonic() < until:
            QTest.qWait(10)
        self.assertTrue(predicate(), "Qt task failed to settle")

    def window(self, controller=None):
        controller = controller or Mock(running=False)
        controller.read_logs.return_value = "fixture log"
        with patch.object(gui, "ServerController", return_value=controller), \
             patch.object(gui, "read_settings", return_value=Settings()), \
             patch.object(gui.ServerWindow, "_create_tray"):
            window = gui.ServerWindow(Path.cwd())
        window.refresh_timer.stop()
        self.windows.append(window)
        return window

    def test_preview_does_not_touch_runtime_or_preferences(self):
        with patch.object(gui, "ServerController", side_effect=AssertionError("process access")), \
             patch.object(gui, "read_settings", side_effect=AssertionError("settings read")), \
             patch.object(gui, "save_settings", side_effect=AssertionError("settings write")), \
             patch.object(gui, "probe_endpoint", side_effect=AssertionError("network access")):
            window = gui.ServerWindow(Path.cwd(), preview=True)
            self.windows.append(window)
            self.qt.processEvents()
            self.assertIsNone(window.controller)
            self.assertIsNone(window.refresh_timer)
            self.assertIsNone(window.tray)
            self.assertEqual(window.windowTitle(), "Voice Changer Server")

    def test_failed_server_exit_shows_code_and_allows_restart(self):
        controller = Mock(running=False, exit_code=7)
        with patch.object(gui, "probe_endpoint", return_value=EndpointState("Closed", 18888)):
            window = self.window(controller)
            window._show_state(EndpointState("Closed", 18888))
            self.assertIn("7", window.status_title.text())
            self.assertIn("已退出", window.status_badge.text())
            self.assertTrue(window.start_button.isEnabled())
            self.assertFalse(window.stop_button.isEnabled())

    def test_probe_is_nonblocking_and_never_overlaps(self):
        release = threading.Event()
        started = threading.Event()

        def probe(*_args, **_kwargs):
            started.set()
            release.wait(2)
            return EndpointState("Closed", 18888)

        with patch.object(gui, "probe_endpoint", side_effect=probe) as probe_mock:
            window = self.window()
            try:
                window.refresh()
                self.wait_for(started.is_set)
                for _ in range(5):
                    window.refresh()
                self.assertEqual(probe_mock.call_count, 1)
                self.assertTrue(window._probing)
            finally:
                release.set()
            self.wait_for(lambda: not window._workers)
            self.assertFalse(window._probing)

    def test_auto_open_happens_once_and_on_worker_thread(self):
        called_threads = []
        controller = Mock(running=True)
        controller.open_client.side_effect = lambda _port: called_threads.append(threading.current_thread())
        state = EndpointState("VCClientReady", 18888, True)
        with patch.object(gui, "probe_endpoint", return_value=state):
            window = self.window(controller)
            window._auto_open = True
            window._show_state(state)
            window._show_state(state)
            self.wait_for(lambda: not window._workers)
            self.assertEqual(controller.open_client.call_count, 1)
            self.assertNotEqual(called_threads[0], threading.main_thread())

    def test_external_service_cannot_enable_stop(self):
        with patch.object(gui, "probe_endpoint", return_value=EndpointState("Closed", 18888)):
            window = self.window()
            window._show_state(EndpointState("VCClientReady", 18888, True))
            self.assertFalse(window.stop_button.isEnabled())
            self.assertTrue(window.client_button.isEnabled())
            self.assertEqual(window.owner_value.text(), "外部进程")
            self.wait_for(lambda: not window._workers)

    def test_failed_shutdown_keeps_the_window_and_event_loop(self):
        controller = Mock(running=True)
        controller.stop.side_effect = RuntimeError("fixture stop failure")
        with patch.object(gui, "probe_endpoint", return_value=EndpointState("Closed", 18888)), \
             patch.object(gui, "MessageBox") as dialog, \
             patch.object(gui.ServerWindow, "_notify") as notify, \
             patch.object(gui.ServerWindow, "_finish_quit") as quit_window:
            dialog.return_value.exec.return_value = True
            window = self.window(controller)
            window.request_exit()
            self.wait_for(lambda: not window._workers)
            self.assertFalse(window._quitting)
            self.assertFalse(window._allow_close)
            notify.assert_called_once()
            quit_window.assert_not_called()


if __name__ == "__main__":
    unittest.main()
