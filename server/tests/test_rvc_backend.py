import sys
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import torch

from data.ModelSlot import RVCModelSlot
from voice_changer.RVC.backend.base import RvcInferenceRequest
from voice_changer.RVC.backend.config_mapping import (
    apply_upstream_runtime_setting,
    validate_upstream_f0,
)
from voice_changer.RVC.backend.device import resolve_torch_device
from voice_changer.RVC.backend.exceptions import (
    RvcBackendConfigError,
    RvcDeviceError,
    RvcModelLoadError,
)
from voice_changer.RVC.backend.model_info import model_info_from_checkpoint
from voice_changer.RVC.backend.metrics import RollingInferenceMetrics
from voice_changer.RVC.backend.upstream_loader import load_upstream_module


class RvcHostBoundaryTest(unittest.TestCase):
    def test_host_delegates_audio_and_settings_to_backend(self):
        backend = Mock()
        backend.name = "legacy"
        backend.infer.return_value = np.arange(4, dtype=np.int16)
        backend.get_model_info.return_value = {"backend": "legacy"}
        params = SimpleNamespace(model_dir="models")
        slot = RVCModelSlot(samplingRate=48000)

        with patch(
            "voice_changer.RVC.RVCr2.create_rvc_backend", return_value=backend
        ):
            from voice_changer.RVC.RVCr2 import RVCr2

            host = RVCr2(params, slot)
            host.setSamplingRate(48000, 48000)
            host.initialize()
            result = host.inference(np.ones(480, dtype=np.int16), 96, 48)
            self.assertEqual(result.tolist(), [0, 1, 2, 3])
            request = backend.infer.call_args.args[0]
            self.assertIsInstance(request, RvcInferenceRequest)
            self.assertEqual(request.input_sample_rate, 48000)
            self.assertEqual(request.crossfade_frame, 96)

            self.assertTrue(host.update_settings("tran", 7))
            backend.update_settings.assert_called_with("tran", 7)
            self.assertTrue(host.update_settings("resetRvcBackendMetrics", 1))
            backend.reset_metrics.assert_called_once()

    def test_switch_to_official_maps_legacy_only_f0_to_rmvpe(self):
        legacy = Mock(name="legacy")
        legacy.name = "legacy"
        official = Mock(name="official")
        official.name = "official"
        official.get_model_info.return_value = {"backend": "official"}
        params = SimpleNamespace(model_dir="models")
        slot = RVCModelSlot(samplingRate=48000)

        with patch(
            "voice_changer.RVC.RVCr2.create_rvc_backend",
            side_effect=[legacy, official],
        ):
            from voice_changer.RVC.RVCr2 import RVCr2

            host = RVCr2(params, slot)
            host.settings.f0Detector = "rmvpe_onnx"
            self.assertTrue(host.update_settings("rvcBackend", "official"))
            legacy.close.assert_called_once()
            official.load_model.assert_called_once()
            self.assertEqual(host.settings.rvcBackend, "official")
            self.assertEqual(host.settings.f0Detector, "rmvpe")

    def test_failed_backend_switch_keeps_previous_ready_backend(self):
        legacy = Mock(name="legacy")
        legacy.name = "legacy"
        legacy.get_model_info.return_value = {"ready": True}
        official = Mock(name="official")
        official.name = "official"
        official.load_model.side_effect = RvcModelLoadError("missing asset")
        recovered = Mock(name="recovered")
        recovered.name = "legacy"
        recovered.get_model_info.return_value = {"ready": True}
        params = SimpleNamespace(model_dir="models")
        slot = RVCModelSlot(samplingRate=48000)

        with patch(
            "voice_changer.RVC.RVCr2.create_rvc_backend",
            side_effect=[legacy, official, recovered],
        ):
            from voice_changer.RVC.RVCr2 import RVCr2

            host = RVCr2(params, slot)
            self.assertFalse(host.update_settings("rvcBackend", "official"))

        self.assertIs(host.backend, recovered)
        self.assertEqual(host.settings.rvcBackend, "legacy")
        self.assertEqual(host.lastBackendError, "missing asset")
        legacy.close.assert_called_once()
        official.close.assert_called_once()
        recovered.warmup.assert_called_once()

    def test_failed_gpu_rebuild_can_be_retried(self):
        current = Mock(name="current")
        current.name = "legacy"
        current.get_model_info.return_value = {"ready": True}
        failed = Mock(name="failed")
        failed.name = "legacy"
        failed.load_model.side_effect = RvcDeviceError("invalid gpu")
        rollback = Mock(name="rollback")
        rollback.name = "legacy"
        rollback.get_model_info.return_value = {"ready": True}
        recovered = Mock(name="recovered")
        recovered.name = "legacy"
        recovered.get_model_info.return_value = {"ready": True}
        params = SimpleNamespace(model_dir="models")
        slot = RVCModelSlot(samplingRate=48000)

        with patch(
            "voice_changer.RVC.RVCr2.create_rvc_backend",
            side_effect=[current, failed, rollback, recovered],
        ):
            from voice_changer.RVC.RVCr2 import RVCr2

            host = RVCr2(params, slot)
            self.assertFalse(host.update_settings("gpu", 0))
            self.assertIs(host.backend, rollback)
            self.assertEqual(host.settings.gpu, -9999)
            self.assertTrue(host.update_settings("gpu", 0))

        self.assertIs(host.backend, recovered)
        self.assertEqual(host.settings.gpu, 0)
        recovered.warmup.assert_called_once()
        current.close.assert_called_once()
        rollback.close.assert_called_once()

    def test_warmup_failure_is_not_reported_ready(self):
        backend = Mock()
        backend.name = "legacy"
        backend.warmup.side_effect = RvcModelLoadError("warmup failed")
        backend.get_model_info.return_value = {"ready": False}
        params = SimpleNamespace(model_dir="models")
        slot = RVCModelSlot(samplingRate=48000)

        with patch(
            "voice_changer.RVC.RVCr2.create_rvc_backend", return_value=backend
        ):
            from voice_changer.RVC.RVCr2 import RVCr2

            host = RVCr2(params, slot)
            self.assertFalse(host.initialize())

        backend.close.assert_called_once()
        self.assertFalse(host.get_info()["pipelineInfo"]["ready"])
        self.assertEqual(host.lastBackendError, "warmup failed")

    def test_backend_switch_waits_for_inflight_inference(self):
        entered = threading.Event()
        release = threading.Event()
        replacement_started = threading.Event()
        current = Mock(name="current")
        current.name = "legacy"
        current.get_model_info.return_value = {"ready": True}
        current.infer.side_effect = lambda _request: (
            entered.set(),
            release.wait(2),
            np.zeros(480, dtype=np.int16),
        )[-1]
        replacement = Mock(name="replacement")
        replacement.name = "official"
        replacement.load_model.side_effect = replacement_started.set
        params = SimpleNamespace(model_dir="models")
        slot = RVCModelSlot(samplingRate=48000)

        with patch(
            "voice_changer.RVC.RVCr2.create_rvc_backend",
            side_effect=[current, replacement],
        ):
            from voice_changer.RVC.RVCr2 import RVCr2

            host = RVCr2(params, slot)
            inference = threading.Thread(
                target=host.inference,
                args=(np.zeros(480, dtype=np.int16), 0, 0),
            )
            switching = threading.Thread(
                target=host.update_settings,
                args=("rvcBackend", "official"),
            )
            inference.start()
            self.assertTrue(entered.wait(1))
            switching.start()
            self.assertFalse(replacement_started.wait(0.1))
            release.set()
            inference.join(2)
            switching.join(2)

        self.assertFalse(inference.is_alive())
        self.assertFalse(switching.is_alive())
        self.assertTrue(replacement_started.is_set())


class ConfigMappingTest(unittest.TestCase):
    def test_official_runtime_updates_are_local_to_engine(self):
        engine = Mock()
        apply_upstream_runtime_setting(engine, "tran", 4)
        apply_upstream_runtime_setting(engine, "indexRatio", 0.75)
        apply_upstream_runtime_setting(engine, "protect", 0.25)
        apply_upstream_runtime_setting(engine, "dstId", 2)
        engine.change_key.assert_called_with(4)
        engine.change_index_rate.assert_called_with(0.75)
        engine.change_protect.assert_called_with(0.25)
        engine.change_speaker_id.assert_called_with(2)

    def test_official_f0_mapping_rejects_legacy_only_detectors(self):
        for detector in ("rmvpe", "fcpe", "pm"):
            validate_upstream_f0(detector)
        with self.assertRaises(RvcBackendConfigError):
            validate_upstream_f0("rmvpe_onnx")


class DeviceSelectionTest(unittest.TestCase):
    def test_explicit_devices(self):
        self.assertEqual(str(resolve_torch_device(-1, cuda_count=2)), "cpu")
        self.assertEqual(str(resolve_torch_device(0, cuda_count=2)), "cuda:0")
        self.assertEqual(str(resolve_torch_device(1, cuda_count=2)), "cuda:1")

    def test_invalid_gpu_does_not_silently_select_another_gpu(self):
        with self.assertRaises(RvcDeviceError):
            resolve_torch_device(2, cuda_count=2)


class InferenceMetricsTest(unittest.TestCase):
    def test_rolling_summary_reports_mean_and_percentiles(self):
        metrics = RollingInferenceMetrics(capacity=3)
        for elapsed_ms in (10, 20, 30, 40):
            metrics.record(elapsed_ms)

        summary = metrics.snapshot()
        self.assertEqual(summary["inferenceCount"], 4)
        self.assertEqual(summary["inferenceWindowSize"], 3)
        self.assertEqual(summary["meanInferenceMs"], 30)
        self.assertEqual(summary["p50InferenceMs"], 30)
        self.assertEqual(summary["p95InferenceMs"], 39)


class ModelMetadataTest(unittest.TestCase):
    def test_v1_f0_single_speaker(self):
        weight = SimpleNamespace(shape=(1, 256))
        info = model_info_from_checkpoint(
            {
                "config": [1, 2, 48000],
                "weight": {"emb_g.weight": weight},
                "f0": 1,
            }
        )
        self.assertEqual(info["version"], "v1")
        self.assertTrue(info["f0"])
        self.assertEqual(info["sampleRate"], 48000)
        self.assertEqual(info["speakerCount"], 1)

    def test_v2_non_f0(self):
        info = model_info_from_checkpoint(
            {"config": [1, 32000], "weight": {}, "f0": 0, "version": "v2"}
        )
        self.assertEqual(info["version"], "v2")
        self.assertFalse(info["f0"])
        self.assertEqual(info["sampleRate"], 32000)


class VendorIsolationTest(unittest.TestCase):
    def test_vendor_i18n_does_not_depend_on_process_working_directory(self):
        module = load_upstream_module("i18n.i18n")
        messages = module.load_language_list("en_US")
        self.assertIsInstance(messages, dict)
        self.assertTrue(messages)

    def test_vendor_loads_without_generic_top_level_packages(self):
        module = load_upstream_module("tools.cuda_graph")
        self.assertEqual(module.__name__, "vcclient_official_rvc.tools.cuda_graph")
        self.assertNotIn("infer", sys.modules)
        self.assertNotIn("tools", sys.modules)

    def test_cuda_graph_replay_failure_falls_back_to_eager(self):
        module = load_upstream_module("tools.cuda_graph")
        cache = module._GraphCache()
        input_tensor = torch.tensor([1.0])
        key = ("test",)
        signature = key + (module._tensor_signature(input_tensor),)
        broken_entry = Mock()
        broken_entry.replay.side_effect = RuntimeError("replay failed")
        cache.entries[signature] = broken_entry

        output = cache.run(key, lambda value: value + 1, (input_tensor,))

        self.assertEqual(output.item(), 2.0)
        self.assertEqual(cache.fallback_count, 1)
        self.assertIn(signature, cache.failures)


if __name__ == "__main__":
    unittest.main()
