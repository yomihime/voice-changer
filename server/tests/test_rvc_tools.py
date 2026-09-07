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


if __name__ == "__main__":
    unittest.main()
