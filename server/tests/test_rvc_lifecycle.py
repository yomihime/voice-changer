import hashlib
import inspect
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import numpy as np

from downloader import Downloader, WeightDownloader
from data.ModelSlot import RVCModelSlot
from voice_changer.RVC.RVCSettings import RVCSettings
from voice_changer.RVC.backend.base import RvcBackendConfig
from voice_changer.RVC.backend.exceptions import RvcModelLoadError
from voice_changer.RVC.backend.upstream import UpstreamRvcBackend
from voice_changer.VoiceChangerManager import (
    VoiceChangerManager,
    VoiceChangerManagerSettings,
)
from voice_changer.VoiceChangerV2 import VoiceChangerV2


class ResourceIsolationTest(unittest.TestCase):
    def test_official_missing_assets_respect_downloads_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            model_dir = Path(directory) / "0"
            model_dir.mkdir()
            (model_dir / "model.pth").write_bytes(b"checkpoint")
            params = SimpleNamespace(
                model_dir=directory,
                rvc_upstream_hubert=str(Path(directory) / "missing-hubert"),
                allow_downloads=False,
            )
            slot = RVCModelSlot(slotIndex=0, modelFile="model.pth")
            backend = UpstreamRvcBackend(
                RvcBackendConfig(params, slot, RVCSettings(f0Detector="rmvpe"))
            )
            with patch(
                "voice_changer.RVC.backend.upstream.ensureRvcUpstreamAssets"
            ) as ensure:
                with self.assertRaises(RvcModelLoadError):
                    backend.load_model()
            ensure.assert_not_called()

    def test_download_is_atomic_and_enforces_timeout_and_hash(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.headers = {}
        response.iter_content.return_value = [b"wrong"]
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "asset.bin"
            destination.write_bytes(b"previous")
            with patch.object(Downloader.requests, "get", return_value=response) as get:
                with self.assertRaises(ValueError):
                    Downloader.download(
                        {
                            "url": "https://example.invalid/asset.bin",
                            "saveTo": str(destination),
                            "position": 0,
                            "sha256": hashlib.sha256(b"expected").hexdigest(),
                        }
                    )

            self.assertEqual(destination.read_bytes(), b"previous")
            self.assertFalse(Path(f"{destination}.part").exists())
            self.assertEqual(get.call_args.kwargs["timeout"], (10, 120))

    def test_official_assets_are_downloaded_and_verified_on_demand(self):
        payloads = {
            "config.json": b"config",
            "preprocessor_config.json": b"preprocessor",
            "pytorch_model.bin": b"model",
        }
        hashes = {
            name: hashlib.sha256(content).hexdigest()
            for name, content in payloads.items()
        }
        with tempfile.TemporaryDirectory() as directory:
            params = SimpleNamespace(rvc_upstream_hubert=directory)

            def fake_download(item):
                name = Path(item["saveTo"]).name
                Path(item["saveTo"]).write_bytes(payloads[name])

            with (
                patch.object(WeightDownloader, "RVC_UPSTREAM_ASSETS", hashes),
                patch.object(WeightDownloader, "download", side_effect=fake_download),
            ):
                self.assertFalse(WeightDownloader.rvcUpstreamAssetsReady(params))
                WeightDownloader.ensureRvcUpstreamAssets(params)
                self.assertTrue(WeightDownloader.rvcUpstreamAssetsReady(params))

    def test_legacy_startup_weight_list_excludes_official_assets(self):
        startup_body = inspect.getsource(WeightDownloader.downloadWeight)
        self.assertNotIn("RVC_UPSTREAM_ASSET_BASE", startup_body)
        self.assertNotIn("ensureRvcUpstreamAssets", startup_body)


class OutputLifecycleTest(unittest.TestCase):
    def test_successful_backend_lifecycle_change_resets_sola_state(self):
        model = Mock()
        model.voiceChangerType = "RVC"
        model.update_settings.return_value = True
        model.get_info.return_value = {"gpu": 0}
        changer = VoiceChangerV2(SimpleNamespace())
        changer.setModel(model)
        changer.sola_buffer = np.ones(4)

        changer.update_settings("gpu", 0)

        self.assertFalse(hasattr(changer, "sola_buffer"))


class SettingPersistenceTest(unittest.TestCase):
    def test_failed_runtime_value_is_not_persisted(self):
        manager = VoiceChangerManager.__new__(VoiceChangerManager)
        manager.settings = VoiceChangerManagerSettings()
        manager.serverDevice = Mock()
        manager.voiceChanger = Mock()
        manager.voiceChanger.update_settings.return_value = {"gpu": 0}
        manager.store_setting = Mock()
        manager.get_info = Mock(return_value={})

        manager.update_settings("gpu", 9)

        manager.store_setting.assert_called_once_with("gpu", 0)


if __name__ == "__main__":
    unittest.main()
