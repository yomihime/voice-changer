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

    def test_frontend_is_self_contained_and_included_in_source_fingerprint(self):
        root = desktop.ROOT
        sources = desktop.frontend_files(root)
        self.assertTrue(any(p.name == "app.js" for p in sources))
        self.assertFalse(any("reverse_engineering" in p.parts or "dist" in p.parts for p in sources))
        before = desktop.source_fingerprint()
        with patch.object(desktop, "frontend_files", return_value=[]):
            self.assertNotEqual(before, desktop.source_fingerprint())
        with tempfile.TemporaryDirectory() as folder:
            desktop.copy_frontend(Path(folder))
            self.assertTrue((Path(folder) / "frontend/server.cjs").is_file())
            dist = Path(folder) / "frontend/dist"
            self.assertTrue((dist / "src/app.js").is_file())
            self.assertTrue((dist / "assets/i18n/zh/translation.json").is_file())
            self.assertTrue((dist / "licenses-js.json").is_file())


if __name__ == "__main__":
    unittest.main()
