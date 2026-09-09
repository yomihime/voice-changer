import base64
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"


def _load_tool(name: str):
    path = TOOLS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeDiagnosticToolTest(unittest.TestCase):
    def test_import_timeout_is_reported_instead_of_raised(self):
        tool = _load_tool("check_rvc_runtime")
        timeout = subprocess.TimeoutExpired(["python"], 60)
        with patch.object(tool.subprocess, "run", side_effect=timeout):
            result = tool._probe_import("torch")
        self.assertFalse(result["ok"])
        self.assertTrue(result["timedOut"])


class OfficialSmokeToolTest(unittest.TestCase):
    def test_help_works_when_invoked_by_file_path(self):
        process = subprocess.run(
            [sys.executable, TOOLS_DIR / "smoke_rvc_official.py", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("--model", process.stdout)


class BackendBenchmarkToolTest(unittest.TestCase):
    def test_backend_report_uses_public_rest_results(self):
        tool = _load_tool("benchmark_rvc_backends")
        output = b"\x01\x00\x02\x00"

        def request(url, **_kwargs):
            if url.endswith("/test"):
                return {"changedVoiceBase64": base64.b64encode(output).decode()}
            if url.endswith("/performance"):
                return [1, 2, 3, 4]
            if url.endswith("/info"):
                return {
                    "pipelineInfo": {
                        "backend": "official",
                        "meanInferenceMs": 5.0,
                    },
                    "f0Detector": "rmvpe",
                    "indexRatio": 0.5,
                    "protect": 0.3,
                    "inputSampleRate": 48000,
                    "outputSampleRate": 48000,
                }
            raise AssertionError(url)

        with (
            patch.object(tool, "_set_backend"),
            patch.object(tool, "_reset_backend_metrics"),
            patch.object(tool, "_request_json", side_effect=request),
        ):
            report, rendered_audio = tool._benchmark_backend(
                "http://localhost:18888",
                "official",
                [b"\x00\x00"],
                warmup=1,
                requests=2,
            )

        self.assertEqual(report["restRoundTrip"]["count"], 2)
        self.assertEqual(report["backendMetrics"]["meanInferenceMs"], 5.0)
        self.assertEqual(report["outputSamples"], 4)
        self.assertEqual(rendered_audio, output * 2)


class RuntimeSoakToolTest(unittest.TestCase):
    def test_snapshot_keeps_only_replayable_runtime_evidence(self):
        tool = _load_tool("soak_rvc_runtime")
        snapshot = tool._snapshot(
            {
                "serverAudioStated": 1,
                "serverInputDeviceId": 5,
                "serverOutputDeviceId": 9,
                "serverReadChunkSize": 32,
                "inputSampleRate": 44100,
                "outputSampleRate": 44100,
                "pipelineInfo": {
                    "backend": "official",
                    "ready": True,
                    "inferenceCount": 123,
                    "p95InferenceMs": 22.5,
                    "processCudaAllocatedMiB": 1024,
                },
                "serverAudioInputDevices": ["intentionally omitted"],
            },
            30.0,
        )
        self.assertEqual(snapshot["backend"], "official")
        self.assertEqual(snapshot["inferenceCount"], 123)
        self.assertEqual(snapshot["cudaAllocatedMiB"], 1024)
        self.assertNotIn("serverAudioInputDevices", snapshot)

    def test_vram_summary_reports_growth(self):
        tool = _load_tool("soak_rvc_runtime")
        summary = tool._vram_summary(
            [
                {"cudaAllocatedMiB": 100.0},
                {"cudaAllocatedMiB": None},
                {"cudaAllocatedMiB": 103.5},
            ]
        )
        self.assertEqual(summary["samples"], 2)
        self.assertEqual(summary["deltaAllocatedMiB"], 3.5)
        self.assertEqual(summary["maxAllocatedMiB"], 103.5)

    def _device_snapshot(self, **overrides):
        snapshot = {
            "elapsedSeconds": 0.0,
            "serverAudioStated": 1,
            "backend": "official",
            "ready": True,
            "backendError": None,
            "streamGeneration": 1,
            "inferenceMetricsEpoch": "i1",
            "inferenceCount": 1,
            "inferenceSuccessCount": 1,
            "inferenceFailureCount": 0,
            "inferenceInputSamples": 256,
            "inferenceOutputSamples": 256,
            "hostMetricsEpoch": "h1",
            "hostRequestCount": 1,
            "hostSuccessCount": 1,
            "hostFailureCount": 0,
            "hostInputSamples": 256,
            "hostOutputSamples": 256,
            "hostFallbackSamples": 0,
            "deviceEpoch": 1,
            "deviceState": "active",
            "deviceActive": True,
            "deviceInputCallbackCount": 1,
            "deviceInputSamples": 256,
            "deviceProcessedBlockCount": 1,
            "deviceProcessedOutputSamples": 256,
            "deviceOutputCallbackCount": 1,
            "deviceOutputWriteCount": 1,
            "deviceOutputSamples": 256,
            "deviceCallbackErrorCount": 0,
            "deviceCallbackStatusCount": 0,
            "deviceCallbackStatus": {
                "inputUnderflow": 0,
                "inputOverflow": 0,
                "outputUnderflow": 0,
                "outputOverflow": 0,
                "primingOutput": 0,
                "unknown": 0,
            },
            "deviceQueueDropCount": 0,
            "deviceLoopErrorCount": 0,
        }
        snapshot.update(overrides)
        return snapshot

    def test_device_healthy_progress_passes(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot()
        last = self._device_snapshot(
            elapsedSeconds=2.0,
            inferenceCount=2,
            inferenceSuccessCount=2,
            inferenceInputSamples=512,
            inferenceOutputSamples=512,
            hostRequestCount=2,
            hostSuccessCount=2,
            hostInputSamples=512,
            hostOutputSamples=512,
            deviceInputCallbackCount=2,
            deviceInputSamples=512,
            deviceProcessedBlockCount=2,
            deviceProcessedOutputSamples=512,
            deviceOutputCallbackCount=2,
            deviceOutputWriteCount=2,
            deviceOutputSamples=512,
        )
        self.assertEqual(
            tool._evaluate_device(
                [first, last],
                startup_grace=0,
                switch_elapsed=None,
                switch_grace=0,
                stall_timeout=10,
                max_inference_failures=0,
                max_host_failures=0,
                max_callback_errors=0,
                max_status_events=0,
                max_loop_errors=0,
                max_queue_drops=0,
            ),
            [],
        )

    def test_device_failure_stall_reset_and_unknown_status_fail(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot()
        stalled = self._device_snapshot(
            elapsedSeconds=3.0,
            inferenceCount=2,
            inferenceSuccessCount=1,
            inferenceFailureCount=1,
            hostRequestCount=2,
            hostSuccessCount=1,
            hostFailureCount=1,
            deviceCallbackStatusCount=1,
            deviceCallbackStatus={"unknown": 1},
        )
        reset = self._device_snapshot(
            elapsedSeconds=6.0,
            inferenceCount=0,
            inferenceSuccessCount=0,
            inferenceFailureCount=0,
            hostRequestCount=0,
            hostSuccessCount=0,
            hostFailureCount=0,
            deviceInputCallbackCount=0,
            deviceProcessedBlockCount=0,
            deviceOutputWriteCount=0,
            deviceOutputSamples=0,
        )
        errors = tool._evaluate_device(
            [first, stalled, reset],
            startup_grace=0,
            switch_elapsed=None,
            switch_grace=0,
            stall_timeout=1,
            max_inference_failures=0,
            max_host_failures=0,
            max_callback_errors=0,
            max_status_events=0,
            max_loop_errors=0,
            max_queue_drops=0,
        )
        self.assertTrue(any("inferenceFailureCount" in error for error in errors))
        self.assertTrue(any("stalled" in error for error in errors))
        self.assertTrue(any("reset" in error for error in errors))
        self.assertTrue(any("unknown" in error for error in errors))

    def test_lan_rejects_http_only_and_wrong_length_success(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot()
        last = self._device_snapshot(
            elapsedSeconds=1.0,
            inferenceCount=1,
            inferenceSuccessCount=1,
            hostRequestCount=1,
            hostSuccessCount=1,
        )
        errors = tool._evaluate_lan(
            [first, last],
            successful_responses=2,
            response_output_samples=512,
            max_inference_failures=0,
            max_host_failures=0,
        )
        self.assertTrue(any("exceeded" in error for error in errors))
        self.assertIn("output_length", tool._error_types(["response length mismatches"]))
        self.assertIn("http", tool._error_types(["request failed: HTTP Error 503"]))

    def test_lan_detects_success_counter_stall(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot()
        last = self._device_snapshot(elapsedSeconds=3.0)
        errors = tool._evaluate_lan(
            [first, last],
            successful_responses=1,
            response_output_samples=256,
            max_inference_failures=0,
            max_host_failures=0,
            stall_timeout=1,
        )
        self.assertTrue(any("stalled" in error for error in errors))

    def test_required_string_counter_is_unknown_and_fails(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot()
        last = self._device_snapshot(
            elapsedSeconds=2.0,
            inferenceCount="unknown",
            inferenceSuccessCount=2,
            hostRequestCount=2,
            hostSuccessCount=2,
            deviceInputCallbackCount=2,
            deviceInputSamples=512,
            deviceProcessedBlockCount=2,
            deviceProcessedOutputSamples=512,
            deviceOutputCallbackCount=2,
            deviceOutputWriteCount=2,
            deviceOutputSamples=512,
        )
        errors = tool._evaluate_device(
            [first, last],
            startup_grace=0,
            switch_elapsed=None,
            switch_grace=0,
            stall_timeout=10,
            max_inference_failures=0,
            max_host_failures=0,
            max_callback_errors=0,
            max_status_events=0,
            max_loop_errors=0,
            max_queue_drops=0,
        )
        self.assertTrue(any("unknown" in error for error in errors))

    def test_frozen_required_samples_fail_even_when_counts_grow(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot()
        last = self._device_snapshot(
            elapsedSeconds=2.0,
            inferenceCount=2,
            inferenceSuccessCount=2,
            hostRequestCount=2,
            hostSuccessCount=2,
            deviceInputCallbackCount=2,
            deviceProcessedBlockCount=2,
            deviceOutputCallbackCount=2,
            deviceOutputWriteCount=2,
        )
        errors = tool._evaluate_device(
            [first, last],
            startup_grace=0,
            switch_elapsed=None,
            switch_grace=0,
            stall_timeout=1,
            max_inference_failures=0,
            max_host_failures=0,
            max_callback_errors=0,
            max_status_events=0,
            max_loop_errors=0,
            max_queue_drops=0,
        )
        self.assertTrue(any("Samples" in error or "samples" in error for error in errors))

    def test_lan_stall_accumulates_across_multiple_polls(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot()
        snapshots = [
            first,
            self._device_snapshot(elapsedSeconds=30.0),
            self._device_snapshot(elapsedSeconds=60.0),
            self._device_snapshot(elapsedSeconds=90.0),
            self._device_snapshot(elapsedSeconds=120.0),
        ]
        errors = tool._evaluate_lan(
            snapshots,
            successful_responses=1,
            response_output_samples=256,
            max_inference_failures=0,
            max_host_failures=0,
            stall_timeout=60,
        )
        self.assertTrue(any("stalled" in error for error in errors))

    def test_lan_stream_generation_change_fails(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot()
        last = self._device_snapshot(elapsedSeconds=2.0, streamGeneration=2)
        errors = tool._evaluate_lan(
            [first, last],
            successful_responses=1,
            response_output_samples=256,
            max_inference_failures=0,
            max_host_failures=0,
        )
        self.assertTrue(any("generation" in error for error in errors))

    def test_handoff_cli_accepts_url_after_subcommand(self):
        tool = _load_tool("soak_rvc_runtime")
        parser = tool.build_parser()
        args = parser.parse_args(
            ["device", "--url", "http://lan-host:18889", "--json", "report.json"]
        )
        self.assertEqual(args.url, "http://lan-host:18889")

    def test_generation_and_epoch_rollback_fail_during_startup_grace(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot(streamGeneration=8, deviceEpoch=8)
        second = self._device_snapshot(
            elapsedSeconds=1.0,
            streamGeneration=1,
            deviceEpoch=1,
            inferenceCount=2,
            inferenceSuccessCount=2,
            inferenceInputSamples=512,
            inferenceOutputSamples=512,
            hostRequestCount=2,
            hostSuccessCount=2,
            hostInputSamples=512,
            hostOutputSamples=512,
            deviceInputCallbackCount=2,
            deviceInputSamples=512,
            deviceProcessedBlockCount=2,
            deviceProcessedOutputSamples=512,
            deviceOutputCallbackCount=2,
            deviceOutputWriteCount=2,
            deviceOutputSamples=512,
        )
        errors = tool._evaluate_device(
            [first, second],
            startup_grace=10,
            switch_elapsed=None,
            switch_grace=0,
            stall_timeout=30,
            max_inference_failures=0,
            max_host_failures=0,
            max_callback_errors=0,
            max_status_events=0,
            max_loop_errors=0,
            max_queue_drops=0,
        )
        self.assertTrue(any("generation" in error for error in errors))
        self.assertTrue(any("device epoch" in error for error in errors))

    def test_all_required_counters_reject_adjacent_rollbacks(self):
        tool = _load_tool("soak_rvc_runtime")
        for key in (
            "inferenceFailureCount",
            "hostFailureCount",
            "deviceCallbackErrorCount",
            "deviceCallbackStatusCount",
            "deviceQueueDropCount",
            "deviceLoopErrorCount",
            "hostFallbackSamples",
        ):
            with self.subTest(key=key):
                snapshots = [
                    self._device_snapshot(elapsedSeconds=elapsed, **{key: value})
                    for elapsed, value in ((0.0, 5), (1.0, 3), (2.0, 5))
                ]
                snapshots[0].update(
                    inferenceCount=6,
                    inferenceSuccessCount=1,
                    inferenceFailureCount=5,
                    hostRequestCount=6,
                    hostSuccessCount=1,
                    hostFailureCount=5,
                )
                snapshots[1].update(
                    inferenceCount=4,
                    inferenceSuccessCount=1,
                    inferenceFailureCount=3,
                    hostRequestCount=4,
                    hostSuccessCount=1,
                    hostFailureCount=3,
                )
                snapshots[2].update(
                    inferenceCount=6,
                    inferenceSuccessCount=1,
                    inferenceFailureCount=5,
                    hostRequestCount=6,
                    hostSuccessCount=1,
                    hostFailureCount=5,
                )
                errors = tool._evaluate_device(
                    snapshots,
                    startup_grace=0,
                    switch_elapsed=None,
                    switch_grace=0,
                    stall_timeout=60,
                    max_inference_failures=0,
                    max_host_failures=0,
                    max_callback_errors=0,
                    max_status_events=0,
                    max_loop_errors=0,
                    max_queue_drops=0,
                )
                self.assertTrue(any(key + " reset" in error for error in errors))

    def test_nested_device_status_rejects_adjacent_rollbacks(self):
        tool = _load_tool("soak_rvc_runtime")
        snapshots = [
            self._device_snapshot(
                elapsedSeconds=elapsed,
                inferenceCount=index,
                inferenceSuccessCount=index,
                hostRequestCount=index,
                hostSuccessCount=index,
                deviceInputCallbackCount=index,
                deviceInputSamples=index * 256,
                deviceProcessedBlockCount=index,
                deviceProcessedOutputSamples=index * 256,
                deviceOutputCallbackCount=index,
                deviceOutputWriteCount=index,
                deviceOutputSamples=index * 256,
                deviceCallbackStatus={"outputUnderflow": value, "unknown": 0},
            )
            for index, (elapsed, value) in enumerate(((0.0, 5), (1.0, 3), (2.0, 5)), 1)
        ]
        errors = tool._evaluate_device(
            snapshots,
            startup_grace=0,
            switch_elapsed=None,
            switch_grace=0,
            stall_timeout=60,
            max_inference_failures=0,
            max_host_failures=0,
            max_callback_errors=0,
            max_status_events=99,
            max_loop_errors=0,
            max_queue_drops=0,
        )
        self.assertTrue(any("deviceCallbackStatus.outputUnderflow reset" in error for error in errors))

    def test_lan_ignores_unrelated_device_counter_rollbacks(self):
        tool = _load_tool("soak_rvc_runtime")
        snapshots = [
            self._device_snapshot(
                elapsedSeconds=elapsed,
                inferenceCount=index,
                inferenceSuccessCount=index,
                inferenceInputSamples=index * 256,
                inferenceOutputSamples=index * 256,
                hostRequestCount=index,
                hostSuccessCount=index,
                hostInputSamples=index * 256,
                hostOutputSamples=index * 256,
                deviceCallbackErrorCount=value,
            )
            for index, (elapsed, value) in enumerate(
                ((0.0, 5), (1.0, 3), (2.0, 5)), 1
            )
        ]
        errors = tool._evaluate_lan(
            snapshots,
            successful_responses=2,
            response_output_samples=512,
            max_inference_failures=0,
            max_host_failures=0,
        )
        self.assertEqual(errors, [])

    def test_historical_known_status_does_not_pollute_device_acceptance(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot(
            deviceCallbackStatusCount=2,
            deviceCallbackStatus={"outputUnderflow": 2, "unknown": 0},
        )
        last = self._device_snapshot(
            elapsedSeconds=2.0,
            inferenceCount=2,
            inferenceSuccessCount=2,
            hostRequestCount=2,
            hostSuccessCount=2,
            deviceInputCallbackCount=2,
            deviceInputSamples=512,
            deviceProcessedBlockCount=2,
            deviceProcessedOutputSamples=512,
            deviceOutputCallbackCount=2,
            deviceOutputWriteCount=2,
            deviceOutputSamples=512,
            deviceCallbackStatusCount=2,
            deviceCallbackStatus={"outputUnderflow": 2, "unknown": 0},
        )
        errors = tool._evaluate_device(
            [first, last], startup_grace=0, switch_elapsed=None, switch_grace=0,
            stall_timeout=10, max_inference_failures=0, max_host_failures=0,
            max_callback_errors=0, max_status_events=0, max_loop_errors=0,
            max_queue_drops=0,
        )
        self.assertFalse(any("callback status" in error for error in errors))

    def test_new_unknown_status_fails_even_when_status_limit_allows_known(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot()
        last = self._device_snapshot(
            elapsedSeconds=2.0,
            inferenceCount=2,
            inferenceSuccessCount=2,
            hostRequestCount=2,
            hostSuccessCount=2,
            deviceInputCallbackCount=2,
            deviceInputSamples=512,
            deviceProcessedBlockCount=2,
            deviceProcessedOutputSamples=512,
            deviceOutputCallbackCount=2,
            deviceOutputWriteCount=2,
            deviceOutputSamples=512,
            deviceCallbackStatusCount=1,
            deviceCallbackStatus={"unknown": 1},
        )
        errors = tool._evaluate_device(
            [first, last], startup_grace=0, switch_elapsed=None, switch_grace=0,
            stall_timeout=10, max_inference_failures=0, max_host_failures=0,
            max_callback_errors=0, max_status_events=99, max_loop_errors=0,
            max_queue_drops=0,
        )
        self.assertTrue(any("unknown" in error for error in errors))

    def test_lan_ignores_device_status_history(self):
        tool = _load_tool("soak_rvc_runtime")
        first = self._device_snapshot(
            deviceCallbackStatusCount=2,
            deviceCallbackStatus={"unknown": 2},
        )
        last = self._device_snapshot(
            elapsedSeconds=2.0,
            inferenceCount=2,
            inferenceSuccessCount=2,
            inferenceInputSamples=512,
            inferenceOutputSamples=512,
            hostRequestCount=2,
            hostSuccessCount=2,
            hostInputSamples=512,
            hostOutputSamples=512,
        )
        errors = tool._evaluate_lan(
            [first, last], successful_responses=1, response_output_samples=256,
            max_inference_failures=0, max_host_failures=0,
        )
        self.assertFalse(any("callback status" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
