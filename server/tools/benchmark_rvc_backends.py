"""Benchmark Legacy and Official RVC through VCClient's public REST boundary.

Start VCClient with an RVC model selected, then run this script with the same
mono PCM16 input for each backend. The script restores the original backend.
"""

import argparse
import base64
import json
import statistics
import time
import urllib.parse
import urllib.request
import wave
from array import array
from pathlib import Path
from typing import Any


def _request_json(
    url: str,
    *,
    json_body: dict[str, Any] | None = None,
    form_body: dict[str, Any] | None = None,
) -> Any:
    headers: dict[str, str] = {}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif form_body is not None:
        data = urllib.parse.urlencode(form_body).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def _percentile(samples: list[float], fraction: float) -> float:
    ordered = sorted(samples)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _summary(samples: list[float]) -> dict[str, float | int]:
    return {
        "count": len(samples),
        "meanMs": statistics.fmean(samples),
        "p50Ms": _percentile(samples, 0.50),
        "p95Ms": _percentile(samples, 0.95),
    }


def _load_mono_pcm16(path: Path) -> tuple[int, array]:
    with wave.open(str(path), "rb") as wav_file:
        if wav_file.getsampwidth() != 2:
            raise ValueError("Input WAV must use signed 16-bit PCM")
        channels = wav_file.getnchannels()
        sample_rate = wav_file.getframerate()
        samples = array("h")
        samples.frombytes(wav_file.readframes(wav_file.getnframes()))
    if channels == 1:
        return sample_rate, samples
    mono = array(
        "h",
        (
            sum(samples[offset : offset + channels]) // channels
            for offset in range(0, len(samples), channels)
        ),
    )
    return sample_rate, mono


def _chunks(samples: array, chunk_size: int) -> list[bytes]:
    chunks = []
    for offset in range(0, len(samples), chunk_size):
        chunk = array("h", samples[offset : offset + chunk_size])
        if len(chunk) < chunk_size:
            chunk.extend([0] * (chunk_size - len(chunk)))
        chunks.append(chunk.tobytes())
    if not chunks:
        raise ValueError("Input WAV contains no samples")
    return chunks


def _set_backend(base_url: str, backend: str) -> dict[str, Any]:
    info = _request_json(
        f"{base_url}/update_settings",
        form_body={"key": "rvcBackend", "val": backend},
    )
    error = info.get("backendError")
    if error:
        raise RuntimeError(f"{backend} backend failed to initialize: {error}")
    if info.get("rvcBackend") != backend:
        raise RuntimeError(f"Server did not select requested backend {backend!r}")
    return info


def _reset_backend_metrics(base_url: str) -> None:
    _request_json(
        f"{base_url}/update_settings",
        form_body={"key": "resetRvcBackendMetrics", "val": 1},
    )


def _benchmark_backend(
    base_url: str,
    backend: str,
    chunks: list[bytes],
    warmup: int,
    requests: int,
) -> tuple[dict[str, Any], bytes]:
    _set_backend(base_url, backend)
    round_trip_ms: list[float] = []
    output = bytearray()
    for sequence in range(warmup + requests):
        if sequence == warmup:
            _reset_backend_metrics(base_url)
        chunk = chunks[sequence % len(chunks)]
        started = time.perf_counter()
        response = _request_json(
            f"{base_url}/test",
            json_body={
                "timestamp": sequence,
                "buffer": base64.b64encode(chunk).decode("ascii"),
            },
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        if not isinstance(response, dict) or "changedVoiceBase64" not in response:
            raise RuntimeError(f"Inference request failed: {response!r}")
        if sequence >= warmup:
            round_trip_ms.append(elapsed_ms)
            output.extend(base64.b64decode(response["changedVoiceBase64"]))

    final_info = _request_json(f"{base_url}/info")
    return (
        {
            "backend": backend,
            "device": final_info.get("pipelineInfo", {}).get("device"),
            "gpuName": final_info.get("pipelineInfo", {}).get("gpuName"),
            "f0Detector": final_info.get("f0Detector"),
            "indexRatio": final_info.get("indexRatio"),
            "protect": final_info.get("protect"),
            "inputSampleRate": final_info.get("inputSampleRate"),
            "outputSampleRate": final_info.get("outputSampleRate"),
            "restRoundTrip": _summary(round_trip_ms),
            "backendMetrics": final_info.get("pipelineInfo", {}),
            "voiceChangerPerformance": _request_json(f"{base_url}/performance"),
            "outputSamples": len(output) // 2,
        },
        bytes(output),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:18888")
    parser.add_argument("--wav", type=Path, default=Path("test.wav"))
    parser.add_argument("--backends", nargs="+", choices=("legacy", "official"), default=("legacy", "official"))
    parser.add_argument("--chunk-size", type=int, default=4096)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    if args.chunk_size <= 0 or args.warmup < 0 or args.requests <= 0:
        parser.error("chunk-size and requests must be positive; warmup cannot be negative")

    base_url = args.url.rstrip("/")
    input_sample_rate, samples = _load_mono_pcm16(args.wav)
    chunks = _chunks(samples, args.chunk_size)
    original_info = _request_json(f"{base_url}/info")
    original_backend = original_info.get("rvcBackend", "legacy")
    server_input_sample_rate = original_info.get("inputSampleRate")
    if (
        isinstance(server_input_sample_rate, int)
        and server_input_sample_rate != input_sample_rate
    ):
        raise ValueError(
            f"Input WAV is {input_sample_rate} Hz but server expects "
            f"{server_input_sample_rate} Hz"
        )
    report: dict[str, Any] = {
        "source": str(args.wav.resolve()),
        "sourceSampleRate": input_sample_rate,
        "chunkSize": args.chunk_size,
        "warmupRequests": args.warmup,
        "measuredRequests": args.requests,
        "results": [],
    }
    try:
        for backend in args.backends:
            result, output = _benchmark_backend(
                base_url,
                backend,
                chunks,
                args.warmup,
                args.requests,
            )
            report["results"].append(result)
            if args.output_dir:
                args.output_dir.mkdir(parents=True, exist_ok=True)
                output_path = args.output_dir / f"{backend}.wav"
                with wave.open(str(output_path), "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(result["outputSampleRate"] or input_sample_rate)
                    wav_file.writeframes(output)
    finally:
        if original_backend in {"legacy", "official"}:
            _set_backend(base_url, original_backend)

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
