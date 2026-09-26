"""Desktop assembly integrity without installing or launching Electron."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location("desktop", Path(__file__).resolve().parents[1] / "desktop.py")
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)


class DesktopArchiveTest(unittest.TestCase):
    def test_wrong_supplied_archive_is_not_copied(self):
        with tempfile.TemporaryDirectory() as folder:
            source, cache = Path(folder) / "input.zip", Path(folder) / "cache.zip"
            source.write_bytes(b"bad archive")
            with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                desktop.verified_archive({"sha256": "0" * 64}, cache, source)
            self.assertFalse(cache.exists())

    def test_verified_cache_needs_no_network(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder) / "cache.zip"
            cache.write_bytes(b"verified")
            with patch.object(desktop.urllib.request, "urlopen") as request:
                desktop.verified_archive({"sha256": desktop.file_hash(cache)}, cache)
                request.assert_not_called()

    def test_archive_traversal_and_windows_streams_are_rejected_before_extraction(self):
        for member in ("../escape", "C:/escape", "\\escape", "file:stream", "dir/../../escape"):
            with self.subTest(member=member), tempfile.TemporaryDirectory() as folder:
                archive, output = Path(folder) / "input.zip", Path(folder) / "output"
                with zipfile.ZipFile(archive, "w") as bundle:
                    bundle.writestr("safe", "safe")
                    bundle.writestr(member, "unsafe")
                with self.assertRaisesRegex(RuntimeError, "Unsafe"):
                    desktop.extract_archive(archive, output)
                self.assertFalse((output / "safe").exists())

    def test_packaging_allowlist_excludes_profiles_and_tests(self):
        self.assertNotIn("tests", desktop.APP_FILES)
        self.assertNotIn("node_modules", desktop.APP_FILES)
        self.assertIn("runtime.cjs", desktop.APP_FILES)

    def test_build_inputs_do_not_require_the_independent_client(self):
        # A server-only checkout without the submodule must still fingerprint.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in (*desktop.APP_FILES, "electron-runtime.json"):
                target = root / "client/desktop" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts/desktop.py").write_text("fixture", encoding="utf-8")
            (root / "LICENSE").write_text("fixture", encoding="utf-8")
            before = desktop.source_fingerprint(root)
            client = root / "client/frontend/recovered/app.js"
            client.parent.mkdir(parents=True)
            client.write_text("independently maintained", encoding="utf-8")
            self.assertEqual(before, desktop.source_fingerprint(root))
        self.assertNotIn("frontend-self-test.cjs", desktop.APP_FILES)


if __name__ == "__main__":
    unittest.main()
