"""Installation integrity and distribution data boundaries."""

import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("vcclient_manage", Path(__file__).resolve().parents[1] / "manage.py")
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)


class DownloadIntegrityTest(unittest.TestCase):
    def test_corrupt_download_is_never_promoted_to_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "tool.zip"
            with patch.object(manage.urllib.request, "urlopen", return_value=io.BytesIO(b"corrupted")):
                with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                    manage.verified_download("https://example.invalid/tool.zip", "0" * 64, target)
            self.assertFalse(target.exists())

    def test_existing_archive_is_checked_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "tool.zip"
            target.write_bytes(b"verified archive")
            with patch.object(manage.urllib.request, "urlopen") as request:
                manage.verified_download("https://example.invalid/tool.zip", manage.file_hash(target), target)
                request.assert_not_called()


class DistributionBoundaryTest(unittest.TestCase):
    def test_client_launcher_is_packaged(self):
        self.assertIn("start-client-windows.bat", manage.PACKAGE_SUPPORT_FILES)
        self.assertIn("scripts/start-client.ps1", manage.PACKAGE_SUPPORT_FILES)

    def test_server_gui_is_packaged(self):
        self.assertIn("server-gui-windows.bat", manage.PACKAGE_SUPPORT_FILES)
        self.assertIn("scripts/server-gui.ps1", manage.PACKAGE_SUPPORT_FILES)

    def test_portable_prune_removes_only_build_and_test_payloads(self):
        with tempfile.TemporaryDirectory() as directory:
            portable = Path(directory) / "portable"
            runtime = portable / "Lib/site-packages/torch/torch_cuda.dll"
            runtime.parent.mkdir(parents=True)
            runtime.write_text("runtime", encoding="utf-8")
            for relative in (
                "Lib/site-packages/onnx/backend/test/data/case.pb",
                "Lib/site-packages/pkg_resources/tests/data/case.txt",
                "Lib/site-packages/torch/include/header.h",
            ):
                target = portable / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture", encoding="utf-8")
            manage.prune_portable_runtime(portable)
            self.assertTrue(runtime.is_file())
            self.assertFalse((portable / "Lib/site-packages/onnx/backend/test").exists())
            self.assertFalse((portable / "Lib/site-packages/torch/include").exists())

    def test_personal_data_is_excluded_from_application_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            keep = {
                "server/MMVCServerSIO.py",
                "server/voice_changer/RVC/backend/hybrid.py",
                "third_party/rvc/LICENSE",
                "third_party/rvc/patches/runtime.patch",
            }
            private = {"server/stored_setting.json", "server/model_dir/0/mia.pth", "server/pretrain/hubert.pt",
                       "server/keys/private.key", "server/upload_dir/input.wav", ".architecture-refactor/notes.md",
                       "Codex任务书.md", "server/voice_changer/RVC/__pycache__/module.pyc"}
            for name in keep | private:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture", encoding="utf-8")
            with patch.object(manage, "ROOT", root):
                actual = {p.relative_to(root).as_posix() for p in manage.application_files()}
            self.assertEqual(actual, keep)

    def test_installation_stamp_is_not_written_on_build_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (patch.object(manage, "ROOT", root), patch.object(manage, "RUNTIME", root / ".runtime"),
                  patch.object(manage.sys, "prefix", str(root / ".venv")),
                  patch.object(manage.sys, "version_info", (3, 12)), patch.object(manage, "run"),
                  patch.object(manage, "build_frontend", side_effect=RuntimeError("build failed"))):
                with self.assertRaisesRegex(RuntimeError, "build failed"):
                    manage.install()
            self.assertFalse((root / ".runtime/installed.sha256").exists())


if __name__ == "__main__":
    unittest.main()
