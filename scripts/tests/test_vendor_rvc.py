"""Replayable Official RVC vendor import tests."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "vendor_rvc",
    Path(__file__).resolve().parents[1] / "vendor_rvc.py",
)
vendor_rvc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vendor_rvc)


class VendorManifestTest(unittest.TestCase):
    def test_checked_in_manifest_pins_every_source_mapping(self):
        manifest = json.loads(vendor_rvc.MANIFEST.read_text(encoding="utf-8"))
        mapped = {
            entry["source"]: entry["destination"] for entry in manifest["files"]
        }
        self.assertEqual(mapped, vendor_rvc.SOURCE_MAPPINGS)
        self.assertEqual(len(manifest["upstreamCommit"]), 40)
        self.assertTrue(all(len(entry["sha256"]) == 64 for entry in manifest["files"]))
        self.assertEqual(
            manifest["patch"], "patches/0001-vcclient-runtime-adapter.patch"
        )

    def test_compare_runtime_accepts_line_ending_only_difference(self):
        manifest = {
            "files": [{"destination": "infer/example.py"}],
            "localPackageFiles": [],
        }
        with (
            tempfile.TemporaryDirectory() as actual_directory,
            tempfile.TemporaryDirectory() as rebuilt_directory,
        ):
            actual = Path(actual_directory)
            rebuilt = Path(rebuilt_directory)
            (actual / "infer").mkdir()
            (rebuilt / "infer").mkdir()
            (actual / "infer/example.py").write_bytes(b"one\r\ntwo\r\n")
            (rebuilt / "infer/example.py").write_bytes(b"one\ntwo\n")
            with patch.object(vendor_rvc, "VENDOR", actual):
                vendor_rvc.compare_runtime(rebuilt, manifest)


if __name__ == "__main__":
    unittest.main()
