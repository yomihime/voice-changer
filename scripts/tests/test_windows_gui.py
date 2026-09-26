"""Exercise the Qt entry and the retained PowerShell wrapper without inference."""
from pathlib import Path
import importlib.util
import os
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "scripts/server_gui.py"
POWERSHELL = Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
HAS_QT = importlib.util.find_spec("qfluentwidgets") is not None


@unittest.skipUnless(os.name == "nt", "Windows bootstrap")
class ServerGuiBootstrapTest(unittest.TestCase):
    def test_missing_uv_bootstraps_even_with_an_existing_interpreter(self):
        for has_interpreter in (False, True):
            with self.subTest(has_interpreter=has_interpreter), tempfile.TemporaryDirectory(prefix="gui bootstrap ") as folder:
                root = Path(folder)
                scripts = root / "scripts"
                scripts.mkdir()
                wrapper = scripts / "server-gui.ps1"
                wrapper.write_bytes((ROOT / "scripts/server-gui.ps1").read_bytes())
                # Stop at the bootstrap boundary; no downloads or installations in this test.
                (scripts / "windows.ps1").write_text(
                    "Set-Content -LiteralPath (Join-Path $PSScriptRoot 'bootstrap-reached.txt') -Value $args[1]\n"
                    "throw 'BOOTSTRAP_FIXTURE_STOP'\n", encoding="utf-8")
                if has_interpreter:
                    python = root / ".venv/Scripts/python.exe"
                    python.parent.mkdir(parents=True)
                    python.touch()
                result = subprocess.run([str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass",
                                         "-File", str(wrapper), "-SelfTest"], cwd=root, capture_output=True,
                                        text=True, timeout=15, creationflags=HIDDEN)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("BOOTSTRAP_FIXTURE_STOP", result.stdout + result.stderr)
                self.assertEqual((scripts / "bootstrap-reached.txt").read_text().strip(), "gui-install")


@unittest.skipUnless(HAS_QT, "Install server/requirements/windows-gui.lock to test the GUI")
class ServerGuiEntryTest(unittest.TestCase):
    def test_preview_is_offline_and_does_not_create_settings(self):
        with tempfile.TemporaryDirectory(prefix="server gui ") as folder:
            root = Path(folder)
            preview = root / "preview.png"
            result = subprocess.run([sys.executable, str(GUI), "--root", str(root), "--preview", str(preview)],
                                    cwd=ROOT, capture_output=True, text=True, timeout=30, creationflags=HIDDEN)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Voice Changer Server UI self-test passed", result.stdout)
            content = preview.read_bytes()
            self.assertEqual(content[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", content[16:24])
            self.assertGreaterEqual(width, 900)
            self.assertGreaterEqual(height, 720)
            self.assertFalse((root / ".runtime").exists())

    @unittest.skipUnless(os.name == "nt", "Windows bootstrap")
    def test_compatibility_wrapper_runs_qt_self_test(self):
        result = subprocess.run([str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass",
                                 "-File", str(ROOT / "scripts/server-gui.ps1"), "-SelfTest"],
                                cwd=ROOT, capture_output=True, text=True, timeout=30, creationflags=HIDDEN)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Voice Changer Server UI self-test passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
