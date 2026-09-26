"""Position-sensitive regressions for the Official host/backend boundary."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import torch

from data.ModelSlot import RVCModelSlot
from voice_changer.RVC.RVCSettings import RVCSettings
from voice_changer.RVC.RVCr2 import RVCr2
from voice_changer.RVC.backend.base import RvcBackendConfig, RvcInferenceRequest
from voice_changer.RVC.backend.exceptions import RvcDeviceError, RvcModelLoadError
from voice_changer.RVC.backend.upstream import UpstreamRvcBackend
from voice_changer.VoiceChangerV2 import VoiceChangerV2


def make_backend(rate=48000, model_rate=48000):
    backend = UpstreamRvcBackend(RvcBackendConfig(
        SimpleNamespace(model_dir="models"), RVCModelSlot(samplingRate=model_rate),
        RVCSettings(f0Detector="rmvpe", extraConvertSize=rate // 10),
    ))
    backend.engine = Mock(tgt_sr=model_rate)
    backend.engine.cache_pitch = torch.zeros(1024)
    backend.engine.cache_pitchf = torch.zeros(1024)
    backend._ready = True
    return backend


class OfficialTimelineTest(unittest.TestCase):
    def test_overlap_is_regenerated_by_current_inference(self):
        backend = make_backend()
        call = [0]

        def predict(_audio, block, skip, frames, _f0):
            call[0] += 1
            self.assertGreater(frames * 160, block)
            return torch.full((frames * 480,), call[0] / 10)

        backend.engine.infer.side_effect = predict
        request = RvcInferenceRequest(np.zeros(4097, np.int16), 480, 576, 48000, 48000)
        backend.infer(request)
        second = backend.infer(request)
        np.testing.assert_allclose(second[:1056], 0.2 * 32767.5, atol=0.02)

    def test_position_markers_follow_cumulative_time_at_all_rates(self):
        for rate, out_rate, model_rate in ((48000, 48000, 48000), (44100, 44100, 40000),
                                           (44100, 48000, 32000), (48000, 24000, 40000)):
            with self.subTest(rate=rate, out_rate=out_rate, model_rate=model_rate):
                backend = make_backend(rate, model_rate)
                consumed = [0]

                def predict(_audio, block, skip, frames, _f0):
                    consumed[0] += block
                    start = consumed[0] * model_rate // 16000 - frames * model_rate // 100
                    positions = np.arange(start, start + frames * model_rate // 100)
                    return torch.from_numpy((positions / model_rate / 10).astype(np.float32))

                backend.engine.infer.side_effect = predict
                total = 0
                for chunk in (4097, 4001, 6003, 4097, 4001, 6003):
                    cf, search = rate // 100, rate * 12 // 1000
                    before = total * out_rate // rate
                    total += chunk
                    output = backend.infer(RvcInferenceRequest(
                        np.zeros(chunk, np.int16), cf, search, rate, out_rate))
                    count = total * out_rate // rate - before
                    context = cf * out_rate // rate + search * out_rate // rate
                    self.assertEqual(len(output), count + context)
                    delay = context + out_rate // 50
                    positions = np.arange(before - delay, before - delay + len(output))
                    valid = positions > 100
                    # Ignore the finite resampling filter's window edges.
                    valid[:100] = False
                    valid[-100:] = False
                    np.testing.assert_allclose(output[valid], positions[valid] / out_rate / 10 * 32767.5,
                                               atol=0.03, rtol=0.0004)


    def test_invalid_geometry_does_not_advance_stream(self):
        backend = make_backend()
        for rate, audio in ((12345, np.zeros(4097)), (48000, np.zeros((4097, 2))),
                            (48000, np.zeros(100))):
            before = backend.stream_generation
            with self.assertRaises(RuntimeError):
                backend.infer(RvcInferenceRequest(audio, 480, 576, rate, 48000))
            self.assertEqual(backend.stream_generation, before)
            self.assertEqual(backend._input_stream.source_samples_total, 0)
        backend.engine.infer.return_value = torch.zeros(1)
        with self.assertRaisesRegex(RuntimeError, "invalid window"):
            backend.infer(RvcInferenceRequest(np.zeros(4097), 480, 576, 48000, 48000))
        self.assertEqual(backend._input_stream.source_samples_total, 0)

    @staticmethod
    def host(backend, rate=48000, output_rate=48000, overlap=480):
        with patch("voice_changer.RVC.RVCr2.create_rvc_backend", return_value=backend):
            model = RVCr2(SimpleNamespace(model_dir="models"), RVCModelSlot(samplingRate=backend.engine.tgt_sr))
        model.settings = backend.settings
        model.settings.rvcBackend = "official"
        changer = VoiceChangerV2(SimpleNamespace())
        changer.settings.inputSampleRate = rate
        changer.settings.outputSampleRate = output_rate
        changer.settings.crossFadeOverlapSize = overlap
        changer.setModel(model)
        return changer

    def test_host_mixes_adjacent_predictions_once_and_preserves_first_packet_length(self):
        backend = make_backend()
        call = [0]
        def predict(_audio, block, skip, frames, _f0):
            call[0] += 1
            return torch.full((frames * 480,), 0.1 if call[0] % 2 else -0.1)
        backend.engine.infer.side_effect = predict
        changer = self.host(backend)
        results = [changer.on_request(np.zeros(n, np.int16))[0] for n in (4097, 4001, 4097)]
        self.assertEqual([len(x) for x in results], [4097, 4001, 4097])
        np.testing.assert_array_equal(results[0][:2016], 0)
        self.assertEqual(results[0][2016], 3276)
        expected = (3276.75 * changer.np_prev_strength - 3276.75 * changer.np_cur_strength).astype(np.int16)
        np.testing.assert_array_equal(results[1][:480], expected)
        self.assertLess(np.max(np.abs(np.diff(np.concatenate(results)[2500:].astype(int)))), 50)

    def test_host_zero_overlap_has_fixed_latency_at_distinct_output_rate(self):
        backend = make_backend(44100)
        consumed = [0]
        def predict(_audio, block, skip, frames, _f0):
            consumed[0] += block
            start = consumed[0] * 3 - frames * 480
            return torch.from_numpy((np.arange(start, start + frames * 480) / 480000).astype(np.float32))
        backend.engine.infer.side_effect = predict
        changer = self.host(backend, 44100, 48000, overlap=0)
        sizes = [4097, 4001, 6003] * 3
        results = [changer.on_request(np.zeros(n, np.int16))[0] for n in sizes]
        joined = np.concatenate(results)
        self.assertEqual(len(joined), sum(sizes) * 48000 // 44100)
        np.testing.assert_array_equal(joined[:960], 0)
        positions = np.arange(len(joined)) - 960
        np.testing.assert_allclose(joined[1000:], positions[1000:] / 480000 * 32767.5, atol=1.01, rtol=0)

    def test_host_stable_offset_includes_only_fixed_delay_and_measured_sola_search(self):
        for rate in (44100, 48000):
            backend = make_backend(rate)
            consumed = [0]
            def predict(_audio, block, skip, frames, _f0):
                consumed[0] += block
                start = consumed[0] * 3 - frames * 480
                # Slow ramp identifies absolute time independently of block size.
                return torch.from_numpy((np.arange(start, start + frames * 480) / 4800000).astype(np.float32))
            backend.engine.infer.side_effect = predict
            changer = self.host(backend, rate, rate, overlap=rate // 100)
            total = 0
            cf, search = rate // 100, int(0.012 * rate)
            delay = cf + search + rate // 50
            real_argmax = np.argmax
            for size in [4097, 4001, 6003] * 12:
                offsets = []
                def argmax(values):
                    result = real_argmax(values)
                    offsets.append(int(result))
                    return result
                with patch("voice_changer.VoiceChangerV2.np.argmax", side_effect=argmax):
                    output, _ = changer.on_request(np.zeros(size, np.int16))
                offset = offsets[0] if offsets else 0
                self.assertTrue(0 <= offset <= search)
                positions = np.arange(size) + total - delay + offset
                valid = (np.arange(size) > cf + 100) & (positions > 100)
                np.testing.assert_allclose(output[valid], positions[valid] / rate / 100 * 32767.5,
                                           atol=1.02, rtol=0.0004)
                total += size

    def test_full_chunk_crossfade_at_different_rates_never_exceeds_output_block(self):
        backend = make_backend(44100)
        backend.engine.infer.side_effect = lambda _x, _b, _s, frames, _f: torch.zeros(frames * 480)
        changer = self.host(backend, 44100, 48000, overlap=4096)
        total = 0
        for size in (4001, 4001, 4097):
            previous = total
            total += size
            output, _ = changer.on_request(np.zeros(size, np.int16))
            self.assertEqual(len(output), total * 48000 // 44100 - previous * 48000 // 44100)


class RecoveredStreamTest(unittest.TestCase):
    def test_rebuild_outcomes_keep_acceptance_readiness_and_generation_separate(self):
        for failure in (None, "gpu", "resources", "warmup", "recovery"):
            with self.subTest(failure=failure):
                previous, candidate, recovery = Mock(), Mock(), Mock()
                for backend in (previous, candidate, recovery):
                    backend.name = "legacy"
                    backend.get_model_info.return_value = {"ready": True}
                if failure == "gpu":
                    candidate.load_model.side_effect = RvcDeviceError("invalid GPU")
                elif failure == "resources":
                    candidate.load_model.side_effect = RvcModelLoadError("missing assets")
                elif failure:
                    candidate.warmup.side_effect = RvcModelLoadError("warmup failed")
                if failure == "recovery":
                    recovery.warmup.side_effect = RvcModelLoadError("recovery failed")
                    recovery.get_model_info.return_value = {"ready": False}
                with patch("voice_changer.RVC.RVCr2.create_rvc_backend", side_effect=[previous, candidate, recovery]):
                    model = RVCr2(SimpleNamespace(model_dir="models"), RVCModelSlot())
                    changer = VoiceChangerV2(SimpleNamespace())
                    changer.setModel(model)
                    changer.sola_buffer = np.ones(480)
                    before = model.get_stream_generation()
                    with patch.object(model, "update_settings", wraps=model.update_settings) as update:
                        info = changer.update_settings("gpu", 9)
                    self.assertEqual(update.call_count, 1)
                self.assertNotEqual(model.get_stream_generation(), before)
                self.assertFalse(hasattr(changer, "sola_buffer"))
                self.assertEqual(info["gpu"], 9 if failure is None else -9999)
                self.assertEqual(info["pipelineInfo"]["ready"], failure != "recovery")
                self.assertEqual(info["backendError"] is None, failure is None)
                if failure == "recovery":
                    self.assertIn("previous backend recovery failed", info["backendError"])

    def test_settings_rejection_and_noop_preserve_cache_but_context_changes_reset(self):
        backend = make_backend()
        backend.engine.infer.side_effect = lambda _x, _b, _s, frames, _f: torch.zeros(frames * 480)
        changer = OfficialTimelineTest.host(backend)
        changer.on_request(np.zeros(4097, np.int16))
        model = changer.voiceChanger
        for key, value in (("extraConvertSize", -1), ("f0Detector", "invalid"),
                           ("rvcBackend", "hybrid"), ("gpu", model.settings.gpu),
                           ("extraConvertSize", model.settings.extraConvertSize),
                           ("inputSampleRate", 12345), ("outputSampleRate", 48000)):
            with self.subTest(key=key, value=value):
                changer.sola_buffer = np.full(480, 1234.0)
                before = model.get_stream_generation()
                changer.update_settings(key, value)
                self.assertEqual(model.get_stream_generation(), before)
                np.testing.assert_array_equal(changer.sola_buffer, 1234)
        changer.update_settings("extraConvertSize", 9600)
        self.assertFalse(hasattr(changer, "sola_buffer"))
        self.assertEqual(backend._input_stream.source_samples_total, 0)
        changer.on_request(np.zeros(4097, np.int16))
        changer.update_settings("inputSampleRate", 44100)
        self.assertFalse(hasattr(changer, "sola_buffer"))
        self.assertEqual(backend._input_stream.source_samples_total, 0)
        self.assertEqual(changer.settings.inputSampleRate, model.inputSampleRate)

    def test_context_geometry_rebuilds_on_next_inference_but_chunk_length_does_not(self):
        backend = make_backend()
        backend.engine.infer.side_effect = lambda _x, _b, _s, frames, _f: torch.zeros(frames * 480)
        changer = OfficialTimelineTest.host(backend)
        changer.on_request(np.zeros(4097, np.int16))
        before = changer.voiceChanger.get_stream_generation()
        changer.on_request(np.zeros(4001, np.int16))
        self.assertEqual(changer.voiceChanger.get_stream_generation(), before)
        changer.settings.crossFadeOverlapSize = 960
        output, _ = changer.on_request(np.zeros(4097, np.int16))
        self.assertEqual(len(output), 4097)
        self.assertNotEqual(changer.voiceChanger.get_stream_generation(), before)
        self.assertEqual(backend._input_stream.source_samples_total, 4097)

    def test_failed_rebuild_invalidates_host_overlap(self):
        previous, candidate, recovery = Mock(), Mock(), Mock()
        for backend in (previous, candidate, recovery):
            backend.name = "legacy"
            backend.get_model_info.return_value = {"ready": True}
        candidate.warmup.side_effect = RvcModelLoadError("warmup failed")
        with patch("voice_changer.RVC.RVCr2.create_rvc_backend", side_effect=[previous, candidate, recovery]):
            model = RVCr2(SimpleNamespace(model_dir="models"), RVCModelSlot())
            changer = VoiceChangerV2(SimpleNamespace())
            changer.setModel(model)
            changer.sola_buffer = np.full(480, 1234.0)
            info = changer.update_settings("gpu", 9)
        self.assertFalse(hasattr(changer, "sola_buffer"))
        self.assertEqual(info["gpu"], -9999)
        self.assertEqual(info["backendError"], "warmup failed")
        self.assertTrue(info["pipelineInfo"]["ready"])


if __name__ == "__main__":
    unittest.main()
