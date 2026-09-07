"""Run reproducible RVC device and LAN soak checks through public boundaries."""

from __future__ import annotations

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


_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _request_json(
    url: str,
    *,
    json_body: dict[str, Any] | None = None,
    form_body: dict[str, Any] | None = None,
    timeout: float = 120,
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
    with _OPENER.open(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _update_setting(base_url: str, key: str, value: int | float | str) -> Any:
    return _request_json(
        f"{base_url}/update_settings",
        form_body={"key": key, "val": value},
    )


def _snapshot(info: dict[str, Any], elapsed: float) -> dict[str, Any]:
    pipeline = info.get("pipelineInfo") or {}
    return {
        "elapsedSeconds": round(elapsed, 3),
        "serverAudioStated": info.get("serverAudioStated"),
        "serverInputDeviceId": info.get("serverInputDeviceId"),
        "serverOutputDeviceId": info.get("serverOutputDeviceId"),
        "serverReadChunkSize": info.get("serverReadChunkSize"),
        "inputSampleRate": info.get("inputSampleRate"),
        "outputSampleRate": info.get("outputSampleRate"),
        "backend": pipeline.get("backend"),
        "ready": pipeline.get("ready"),
        "inferenceCount": pipeline.get("inferenceCount"),
        "meanInferenceMs": pipeline.get("meanInferenceMs"),
        "p50InferenceMs": pipeline.get("p50InferenceMs"),
        "p95InferenceMs": pipeline.get("p95InferenceMs"),
        "cudaAllocatedMiB": pipeline.get("processCudaAllocatedMiB"),
        "cudaReservedMiB": pipeline.get("processCudaReservedMiB"),
        "cudaPeakAllocatedMiB": pipeline.get("processCudaPeakAllocatedMiB"),
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _vram_summary(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    allocated = [
        float(item["cudaAllocatedMiB"])
        for item in snapshots
        if item.get("cudaAllocatedMiB") is not None
    ]
    if not allocated:
        return {"samples": 0}
    return {
        "samples": len(allocated),
        "startAllocatedMiB": allocated[0],
        "endAllocatedMiB": allocated[-1],
        "deltaAllocatedMiB": allocated[-1] - allocated[0],
        "minAllocatedMiB": min(allocated),
        "maxAllocatedMiB": max(allocated),
    }


def run_device(args: argparse.Namespace) -> int:
    started = time.monotonic()
    initial = _request_json(f"{args.url}/info")
    original_chunk_size = int(initial.get("serverReadChunkSize", 0))
    snapshots: list[dict[str, Any]] = [_snapshot(initial, 0)]
    errors: list[str] = []
    events: list[dict[str, Any]] = []
    first_packet_ms: float | None = None
    initial_count = int(
        (initial.get("pipelineInfo") or {}).get("inferenceCount") or 0
    )
    switched = False

    if initial.get("serverAudioStated") != 1:
        errors.append("server audio is not running")

    try:
        while True:
            elapsed = time.monotonic() - started
            if elapsed >= args.duration:
                break
            if not switched and elapsed >= args.duration * args.switch_fraction:
                _update_setting(args.url, "serverReadChunkSize", args.switch_chunk_size)
                events.append(
                    {
                        "elapsedSeconds": round(elapsed, 3),
                        "event": "chunk-size-switch",
                        "from": original_chunk_size,
                        "to": args.switch_chunk_size,
                    }
                )
                switched = True
            interval = (
                min(args.first_packet_poll_interval, args.poll_interval)
                if first_packet_ms is None
                else args.poll_interval
            )
            time.sleep(min(interval, max(0.0, args.duration - elapsed)))
            try:
                info = _request_json(f"{args.url}/info")
                snapshot = _snapshot(info, time.monotonic() - started)
                snapshots.append(snapshot)
                count = int(snapshot.get("inferenceCount") or 0)
                if first_packet_ms is None and count > initial_count:
                    first_packet_ms = snapshot["elapsedSeconds"] * 1000
                if (
                    snapshot.get("backend") != "official"
                    or snapshot.get("ready") is not True
                ):
                    errors.append(
                        f"backend unhealthy at {snapshot['elapsedSeconds']}s: "
                        f"{snapshot.get('backend')}/{snapshot.get('ready')}"
                    )
                print(
                    f"device elapsed={snapshot['elapsedSeconds']}s "
                    f"count={snapshot.get('inferenceCount')} "
                    f"p95={snapshot.get('p95InferenceMs')}ms",
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001 - preserve soak evidence
                errors.append(f"poll failed at {elapsed:.3f}s: {exc!r}")
    finally:
        if switched:
            try:
                _update_setting(args.url, "serverReadChunkSize", original_chunk_size)
                events.append(
                    {
                        "elapsedSeconds": round(time.monotonic() - started, 3),
                        "event": "chunk-size-restore",
                        "to": original_chunk_size,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"chunk-size restore failed: {exc!r}")

    final_count = int(snapshots[-1].get("inferenceCount") or 0)
    if final_count <= initial_count:
        errors.append("no audio callback inference was observed")
    report = {
        "mode": "device",
        "url": args.url,
        "requestedDurationSeconds": args.duration,
        "observedDurationSeconds": round(time.monotonic() - started, 3),
        "firstPacketObservedMs": first_packet_ms,
        "initialInferenceCount": initial_count,
        "finalInferenceCount": final_count,
        "inferenceCountDelta": final_count - initial_count,
        "events": events,
        "vram": _vram_summary(snapshots),
        "snapshots": snapshots,
        "errors": errors,
        "status": "ok" if not errors else "failed",
    }
    _write_report(args.json, report)
    keys = ("status", "inferenceCountDelta", "firstPacketObservedMs", "vram", "errors")
    print(json.dumps({key: report[key] for key in keys}, ensure_ascii=False))
    return 0 if not errors else 1


def _load_pcm16(path: Path) -> array:
    with wave.open(str(path), "rb") as wav_file:
        if wav_file.getsampwidth() != 2:
            raise ValueError("input WAV must use signed 16-bit PCM")
        channels = wav_file.getnchannels()
        samples = array("h")
        samples.frombytes(wav_file.readframes(wav_file.getnframes()))
    if not samples:
        raise ValueError("input WAV contains no samples")
    if channels == 1:
        return samples
    return array(
        "h",
        (
            sum(samples[offset : offset + channels]) // channels
            for offset in range(0, len(samples), channels)
        ),
    )


def _percentile(samples: list[float], fraction: float) -> float | None:
    if not samples:
        return None
    ordered = sorted(samples)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def run_lan(args: argparse.Namespace) -> int:
    source = _load_pcm16(args.wav)
    info = _request_json(f"{args.url}/info")
    sample_rate = int(info.get("inputSampleRate") or 48000)
    chunk_sizes = [int(value) for value in args.chunk_sizes.split(",")]
    if not chunk_sizes or any(size <= 0 for size in chunk_sizes):
        raise ValueError("chunk sizes must contain positive integers")

    started = time.monotonic()
    deadline = started
    source_offset = 0
    sequence = 0
    errors: list[str] = []
    mismatches: list[dict[str, int]] = []
    latencies: list[float] = []
    snapshots: list[dict[str, Any]] = [_snapshot(info, 0)]
    shape_events: list[dict[str, Any]] = []
    first_packet_ms: float | None = None
    next_poll = started + args.poll_interval
    initial_pipeline = info.get("pipelineInfo") or {}
    initial_count = int(initial_pipeline.get("inferenceCount") or 0)
    if (
        initial_pipeline.get("backend") != "official"
        or initial_pipeline.get("ready") is not True
    ):
        errors.append(
            "Official backend is not ready at start: "
            f"{initial_pipeline.get('backend')}/{initial_pipeline.get('ready')}"
        )

    while time.monotonic() - started < args.duration:
        shape_index = (sequence // args.shape_every) % len(chunk_sizes)
        chunk_size = chunk_sizes[shape_index]
        if sequence == 0 or sequence % args.shape_every == 0:
            shape_events.append(
                {
                    "elapsedSeconds": round(time.monotonic() - started, 3),
                    "sequence": sequence,
                    "chunkSamples": chunk_size,
                }
            )
        chunk = array("h")
        while len(chunk) < chunk_size:
            take = min(chunk_size - len(chunk), len(source) - source_offset)
            chunk.extend(source[source_offset : source_offset + take])
            source_offset += take
            if source_offset >= len(source):
                source_offset = 0
        request_started = time.monotonic()
        try:
            response = _request_json(
                f"{args.url}/test",
                json_body={
                    "timestamp": sequence,
                    "buffer": base64.b64encode(chunk.tobytes()).decode("ascii"),
                },
            )
            latency_ms = (time.monotonic() - request_started) * 1000
            latencies.append(latency_ms)
            output_samples = len(base64.b64decode(response["changedVoiceBase64"])) // 2
            if output_samples != chunk_size:
                mismatches.append(
                    {
                        "sequence": sequence,
                        "inputSamples": chunk_size,
                        "outputSamples": output_samples,
                    }
                )
            if first_packet_ms is None:
                first_packet_ms = (time.monotonic() - started) * 1000
        except Exception as exc:  # noqa: BLE001 - preserve soak evidence
            errors.append(f"request {sequence}: {exc!r}")

        sequence += 1
        deadline += chunk_size / sample_rate
        now = time.monotonic()
        if now >= next_poll:
            try:
                snapshot = _snapshot(_request_json(f"{args.url}/info"), now - started)
                snapshots.append(snapshot)
                if (
                    snapshot.get("backend") != "official"
                    or snapshot.get("ready") is not True
                ):
                    errors.append(
                        f"backend unhealthy at {snapshot['elapsedSeconds']}s: "
                        f"{snapshot.get('backend')}/{snapshot.get('ready')}"
                    )
                print(
                    f"lan elapsed={snapshot['elapsedSeconds']}s requests={sequence} "
                    f"errors={len(errors)} p95={_percentile(latencies, 0.95)}ms",
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"info poll {sequence}: {exc!r}")
            next_poll += args.poll_interval
        time.sleep(max(0.0, deadline - time.monotonic()))

    try:
        snapshots.append(
            _snapshot(_request_json(f"{args.url}/info"), time.monotonic() - started)
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"final info poll: {exc!r}")
    if mismatches:
        errors.append(f"{len(mismatches)} response length mismatches")
    if first_packet_ms is None:
        errors.append("no successful response packet was observed")
    if len(shape_events) < 2:
        errors.append("no request-shape switch was observed")
    latency_summary = {
        "count": len(latencies),
        "meanMs": statistics.fmean(latencies) if latencies else None,
        "p50Ms": _percentile(latencies, 0.50),
        "p95Ms": _percentile(latencies, 0.95),
        "maxMs": max(latencies) if latencies else None,
    }
    report = {
        "mode": "lan",
        "url": args.url,
        "sameHostLanInterface": args.same_host_lan_interface,
        "requestedDurationSeconds": args.duration,
        "observedDurationSeconds": round(time.monotonic() - started, 3),
        "sampleRate": sample_rate,
        "requestCount": sequence,
        "initialInferenceCount": initial_count,
        "finalInferenceCount": int(snapshots[-1].get("inferenceCount") or 0),
        "firstPacketMs": first_packet_ms,
        "latency": latency_summary,
        "shapeEvents": shape_events,
        "lengthMismatches": mismatches,
        "vram": _vram_summary(snapshots),
        "snapshots": snapshots,
        "errors": errors,
        "status": "ok" if not errors else "failed",
    }
    _write_report(args.json, report)
    keys = ("status", "requestCount", "firstPacketMs", "latency", "vram", "errors")
    print(json.dumps({key: report[key] for key in keys}, ensure_ascii=False))
    return 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:18889")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    device = subparsers.add_parser("device", help="observe the server audio device loop")
    device.add_argument("--duration", type=float, default=600)
    device.add_argument("--poll-interval", type=float, default=30)
    device.add_argument("--first-packet-poll-interval", type=float, default=0.1)
    device.add_argument("--switch-fraction", type=float, default=0.5)
    device.add_argument("--switch-chunk-size", type=int, default=40)
    device.add_argument("--json", type=Path, required=True)
    device.set_defaults(run=run_device)

    lan = subparsers.add_parser("lan", help="send paced PCM16 chunks over a LAN URL")
    lan.add_argument("--wav", type=Path, required=True)
    lan.add_argument("--duration", type=float, default=600)
    lan.add_argument("--poll-interval", type=float, default=30)
    lan.add_argument("--chunk-sizes", default="12000,4097,16000")
    lan.add_argument("--shape-every", type=int, default=120)
    lan.add_argument(
        "--same-host-lan-interface",
        action="store_true",
        help="record that the client uses this machine's LAN address",
    )
    lan.add_argument("--json", type=Path, required=True)
    lan.set_defaults(run=run_lan)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
