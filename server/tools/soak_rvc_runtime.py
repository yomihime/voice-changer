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
    pipeline = info.get("pipelineInfo")
    host = info.get("hostRuntimeInfo")
    device = info.get("serverDeviceRuntimeInfo")
    pipeline = pipeline if isinstance(pipeline, dict) else {}
    host = host if isinstance(host, dict) else {}
    device = device if isinstance(device, dict) else {}
    return {
        "elapsedSeconds": round(elapsed, 3),
        "serverAudioStated": info.get("serverAudioStated"),
        "serverInputDeviceId": info.get("serverInputDeviceId"),
        "serverOutputDeviceId": info.get("serverOutputDeviceId"),
        "serverReadChunkSize": info.get("serverReadChunkSize"),
        "inputSampleRate": info.get("inputSampleRate"),
        "outputSampleRate": info.get("outputSampleRate"),
        "backendError": info.get("backendError"),
        "backend": pipeline.get("backend"),
        "ready": pipeline.get("ready"),
        "streamGeneration": pipeline.get("streamGeneration"),
        "inferenceMetricsEpoch": pipeline.get("inferenceMetricsEpoch"),
        "inferenceCount": pipeline.get("inferenceCount"),
        "inferenceSuccessCount": pipeline.get("inferenceSuccessCount"),
        "inferenceFailureCount": pipeline.get("inferenceFailureCount"),
        "inferenceInputSamples": pipeline.get("inferenceInputSamples"),
        # Backend output may include the Official overlap/search context.
        "inferenceOutputSamples": pipeline.get("inferenceOutputSamples"),
        "meanInferenceMs": pipeline.get("meanInferenceMs"),
        "p50InferenceMs": pipeline.get("p50InferenceMs"),
        "p95InferenceMs": pipeline.get("p95InferenceMs"),
        "cudaAllocatedMiB": pipeline.get("processCudaAllocatedMiB"),
        "cudaReservedMiB": pipeline.get("processCudaReservedMiB"),
        "cudaPeakAllocatedMiB": pipeline.get("processCudaPeakAllocatedMiB"),
        "hostMetricsEpoch": host.get("metricsEpoch"),
        "hostRequestCount": host.get("requestCount"),
        "hostSuccessCount": host.get("successCount"),
        "hostFailureCount": host.get("failureCount"),
        "hostInputSamples": host.get("inputSamples"),
        "hostOutputSamples": host.get("outputSamples"),
        "hostFallbackSamples": host.get("fallbackSamples"),
        "hostLastFailure": host.get("lastFailure"),
        "deviceEpoch": device.get("epoch"),
        "deviceState": device.get("state"),
        "deviceActive": device.get("active"),
        "deviceInputCallbackCount": device.get("inputCallbackCount"),
        "deviceInputSamples": device.get("inputSamples"),
        "deviceProcessedBlockCount": device.get("processedBlockCount"),
        "deviceProcessedOutputSamples": device.get("processedOutputSamples"),
        "deviceOutputCallbackCount": device.get("outputCallbackCount"),
        "deviceOutputWriteCount": device.get("outputWriteCount"),
        "deviceOutputSamples": device.get("outputSamples"),
        "deviceCallbackErrorCount": device.get("callbackErrorCount"),
        "deviceCallbackStatusCount": device.get("callbackStatusCount"),
        "deviceCallbackStatus": device.get("callbackStatus"),
        "deviceQueueDropCount": device.get("queueDropCount"),
        "deviceLoopErrorCount": device.get("loopErrorCount"),
        "deviceLastCallbackError": device.get("lastCallbackError"),
        "deviceLastLoopError": device.get("lastLoopError"),
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _add_error(errors: list[str], message: str) -> None:
    if message not in errors:
        errors.append(message)


def _error_type(message: str) -> str:
    """Return a stable, machine-readable class for a human error message."""
    lowered = message.lower()
    if "http" in lowered or "urlopen" in lowered or "connection" in lowered:
        return "http"
    if "length" in lowered or "samples" in lowered and "mismatch" in lowered:
        return "output_length"
    if "reset" in lowered or "epoch" in lowered or "generation" in lowered:
        return "counter_reset"
    if "stalled" in lowered or "no .* progress" in lowered or "no " in lowered and "progress" in lowered:
        return "stalled"
    if "unknown" in lowered or "required metrics" in lowered:
        return "unknown_metric"
    if "callback" in lowered or "queue" in lowered or "underflow" in lowered or "overflow" in lowered:
        return "device_callback"
    if "backend" in lowered or "inference" in lowered or "host" in lowered:
        return "runtime"
    return "acceptance"


def _error_types(errors: list[str]) -> list[str]:
    return sorted({_error_type(message) for message in errors})


def _is_counter(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _counter_delta(
    first: dict[str, Any], last: dict[str, Any], key: str
) -> int | None:
    before = first.get(key)
    after = last.get(key)
    if not _is_counter(before) or not _is_counter(after):
        return None
    return after - before


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


_BASE_REQUIRED = (
    "backend",
    "ready",
    "streamGeneration",
    "inferenceMetricsEpoch",
    "inferenceCount",
    "inferenceSuccessCount",
    "inferenceFailureCount",
    "inferenceInputSamples",
    "inferenceOutputSamples",
    "hostMetricsEpoch",
    "hostRequestCount",
    "hostSuccessCount",
    "hostFailureCount",
    "hostInputSamples",
    "hostOutputSamples",
    "hostFallbackSamples",
)

_DEVICE_REQUIRED = _BASE_REQUIRED + (
    "deviceEpoch",
    "deviceState",
    "deviceActive",
    "deviceInputCallbackCount",
    "deviceInputSamples",
    "deviceProcessedBlockCount",
    "deviceProcessedOutputSamples",
    "deviceOutputCallbackCount",
    "deviceOutputWriteCount",
    "deviceOutputSamples",
    "deviceCallbackErrorCount",
    "deviceCallbackStatusCount",
    "deviceQueueDropCount",
    "deviceLoopErrorCount",
    "deviceCallbackStatus",
)

_EPOCH_FIELDS = {"inferenceMetricsEpoch", "hostMetricsEpoch"}
_COUNTER_FIELDS = {
    key
    for key in _BASE_REQUIRED + _DEVICE_REQUIRED
    if key not in _EPOCH_FIELDS
    and key not in {"backend", "ready", "deviceState", "deviceActive", "deviceCallbackStatus"}
}


def _check_required(
    snapshots: list[dict[str, Any]], required: tuple[str, ...], errors: list[str]
) -> None:
    for snapshot in snapshots:
        missing = [key for key in required if snapshot.get(key) is None]
        if missing:
            _add_error(
                errors,
                f"required metrics unknown at {snapshot['elapsedSeconds']}s: "
                + ", ".join(missing),
            )
        for key in required:
            value = snapshot.get(key)
            invalid = False
            if key in _EPOCH_FIELDS:
                invalid = not isinstance(value, str) or not value.strip()
            elif key in _COUNTER_FIELDS:
                invalid = not _is_counter(value)
            elif key == "backend" or key == "deviceState":
                invalid = not isinstance(value, str) or not value.strip()
            elif key in {"ready", "deviceActive"}:
                invalid = not isinstance(value, bool)
            elif key == "deviceCallbackStatus":
                invalid = not isinstance(value, dict) or any(
                    not isinstance(name, str) or not _is_counter(count)
                    for name, count in value.items()
                )
            if invalid:
                _add_error(
                    errors,
                    f"required metric unknown or invalid at {snapshot['elapsedSeconds']}s: {key}",
                )


def _check_counter_invariants(
    snapshots: list[dict[str, Any]], errors: list[str]
) -> None:
    for snapshot in snapshots:
        attempt = snapshot.get("inferenceCount")
        success = snapshot.get("inferenceSuccessCount")
        failure = snapshot.get("inferenceFailureCount")
        if all(_is_counter(value) for value in (attempt, success, failure)):
            if attempt != success + failure:
                _add_error(
                    errors,
                    f"inference counter invariant failed at {snapshot['elapsedSeconds']}s",
                )
        request = snapshot.get("hostRequestCount")
        host_success = snapshot.get("hostSuccessCount")
        host_failure = snapshot.get("hostFailureCount")
        if all(
            _is_counter(value)
            for value in (request, host_success, host_failure)
        ) and request != host_success + host_failure:
            _add_error(
                errors,
                f"host counter invariant failed at {snapshot['elapsedSeconds']}s",
            )


def _check_counter_rollbacks(
    snapshots: list[dict[str, Any]],
    required: tuple[str, ...],
    errors: list[str],
) -> None:
    """Reject any cumulative required counter that decreases between polls."""
    counter_fields = {
        key
        for key in required
        if key in _COUNTER_FIELDS and key not in {"streamGeneration", "deviceEpoch"}
    }
    for previous, current in zip(snapshots, snapshots[1:]):
        for key in counter_fields:
            before = previous.get(key)
            after = current.get(key)
            if _is_counter(before) and _is_counter(after) and after < before:
                _add_error(
                    errors,
                    f"{key} reset between {previous['elapsedSeconds']}s and "
                    f"{current['elapsedSeconds']}s",
                )
        if "deviceCallbackStatus" in required:
            before_status = previous.get("deviceCallbackStatus")
            after_status = current.get("deviceCallbackStatus")
            if isinstance(before_status, dict) and isinstance(after_status, dict):
                for name in set(before_status) | set(after_status):
                    before = before_status.get(name)
                    after = after_status.get(name)
                    if _is_counter(before) and _is_counter(after) and after < before:
                        _add_error(
                            errors,
                            f"deviceCallbackStatus.{name} reset between "
                            f"{previous['elapsedSeconds']}s and {current['elapsedSeconds']}s",
                        )


def _check_error_delta(
    first: dict[str, Any],
    last: dict[str, Any],
    key: str,
    maximum: int,
    errors: list[str],
) -> None:
    delta = _counter_delta(first, last, key)
    if delta is None:
        return
    if delta < 0:
        _add_error(errors, f"{key} reset during acceptance")
    elif delta > maximum:
        _add_error(errors, f"{key} increased by {delta}, allowed {maximum}")


def _evaluate_device(
    snapshots: list[dict[str, Any]],
    *,
    startup_grace: float,
    switch_elapsed: float | None,
    switch_grace: float,
    stall_timeout: float,
    max_inference_failures: int,
    max_host_failures: int,
    max_callback_errors: int,
    max_status_events: int,
    max_loop_errors: int,
    max_queue_drops: int,
) -> list[str]:
    errors: list[str] = []
    if not snapshots:
        return ["no runtime snapshots were observed"]
    _check_required(snapshots, _DEVICE_REQUIRED, errors)
    _check_counter_invariants(snapshots, errors)
    _check_counter_rollbacks(snapshots, _DEVICE_REQUIRED, errors)
    first, last = snapshots[0], snapshots[-1]

    def in_grace(elapsed: float) -> bool:
        if elapsed <= startup_grace:
            return True
        return (
            switch_elapsed is not None
            and switch_elapsed <= elapsed <= switch_elapsed + switch_grace
        )

    metrics_epoch = first.get("inferenceMetricsEpoch")
    host_epoch = first.get("hostMetricsEpoch")
    stream_generation = first.get("streamGeneration")
    device_epoch = first.get("deviceEpoch")
    progress_keys = (
        "inferenceSuccessCount",
        "inferenceInputSamples",
        "inferenceOutputSamples",
        "hostSuccessCount",
        "hostInputSamples",
        "hostOutputSamples",
        "deviceInputCallbackCount",
        "deviceInputSamples",
        "deviceProcessedBlockCount",
        "deviceProcessedOutputSamples",
        "deviceOutputWriteCount",
        "deviceOutputSamples",
    )
    last_values = {key: first.get(key) for key in progress_keys}
    last_progress = {key: 0.0 for key in progress_keys}

    for snapshot in snapshots:
        elapsed = float(snapshot["elapsedSeconds"])
        grace = in_grace(elapsed)
        if snapshot.get("backend") != "official" or snapshot.get("ready") is not True:
            _add_error(
                errors,
                f"backend unhealthy at {elapsed}s: "
                f"{snapshot.get('backend')}/{snapshot.get('ready')}",
            )
        if snapshot.get("backendError") is not None:
            _add_error(errors, f"backendError at {elapsed}s: {snapshot['backendError']}")
        statuses = snapshot.get("deviceCallbackStatus")
        baseline_statuses = first.get("deviceCallbackStatus")
        if isinstance(statuses, dict) and isinstance(baseline_statuses, dict):
            for name, count in statuses.items():
                baseline = baseline_statuses.get(name, 0)
                if not _is_counter(count) or not _is_counter(baseline):
                    continue
                delta = count - baseline
                if delta > 0 and (name == "unknown" or delta > max_status_events):
                    _add_error(errors, f"device callback status {name} increased by {delta} at {elapsed}s")
        if snapshot.get("serverAudioStated") != 1:
            _add_error(errors, f"server audio intent is not running at {elapsed}s")
        if not grace and (
            snapshot.get("deviceActive") is not True
            or snapshot.get("deviceState") != "active"
        ):
            _add_error(
                errors,
                f"device stream inactive at {elapsed}s: "
                f"{snapshot.get('deviceState')}/{snapshot.get('deviceActive')}",
            )
        if snapshot.get("inferenceMetricsEpoch") != metrics_epoch:
            _add_error(errors, "inference metrics epoch changed during acceptance")
        if snapshot.get("hostMetricsEpoch") != host_epoch:
            _add_error(errors, "host metrics epoch changed during acceptance")
        if snapshot.get("streamGeneration") != stream_generation:
            generation_rollback = (
                _is_counter(snapshot.get("streamGeneration"))
                and _is_counter(stream_generation)
                and snapshot["streamGeneration"] < stream_generation
            )
            if grace and not generation_rollback:
                stream_generation = snapshot.get("streamGeneration")
            else:
                _add_error(errors, f"stream generation changed at {elapsed}s")
        if snapshot.get("deviceEpoch") != device_epoch:
            epoch_rollback = (
                _is_counter(snapshot.get("deviceEpoch"))
                and _is_counter(device_epoch)
                and snapshot["deviceEpoch"] < device_epoch
            )
            if grace and not epoch_rollback:
                device_epoch = snapshot.get("deviceEpoch")
            else:
                _add_error(errors, f"device epoch changed at {elapsed}s")

        for key in progress_keys:
            value = snapshot.get(key)
            previous = last_values[key]
            if not _is_counter(value) or not _is_counter(previous):
                continue
            if value < previous:
                _add_error(errors, f"{key} reset during acceptance")
            elif value > previous:
                last_progress[key] = elapsed
            elif grace:
                last_progress[key] = elapsed
            elif elapsed - last_progress[key] > stall_timeout:
                _add_error(
                    errors,
                    f"{key} stalled for more than {stall_timeout}s at {elapsed}s",
                )
            last_values[key] = value

        for key, maximum in (
            ("inferenceFailureCount", max_inference_failures),
            ("hostFailureCount", max_host_failures),
            ("deviceCallbackErrorCount", max_callback_errors),
            ("deviceCallbackStatusCount", max_status_events),
            ("deviceLoopErrorCount", max_loop_errors),
            ("deviceQueueDropCount", max_queue_drops),
        ):
            current = snapshot.get(key)
            baseline = first.get(key)
            if _is_counter(current) and _is_counter(baseline) and current - baseline > maximum:
                _add_error(errors, f"{key} increased above allowed {maximum} at {elapsed}s")

    for key in progress_keys:
        delta = _counter_delta(first, last, key)
        if delta is not None and delta <= 0:
            _add_error(errors, f"no {key} progress was observed")
    _check_error_delta(first, last, "inferenceFailureCount", max_inference_failures, errors)
    _check_error_delta(first, last, "hostFailureCount", max_host_failures, errors)
    _check_error_delta(first, last, "deviceCallbackErrorCount", max_callback_errors, errors)
    _check_error_delta(first, last, "deviceCallbackStatusCount", max_status_events, errors)
    _check_error_delta(first, last, "deviceLoopErrorCount", max_loop_errors, errors)
    _check_error_delta(first, last, "deviceQueueDropCount", max_queue_drops, errors)
    return errors


def _evaluate_lan(
    snapshots: list[dict[str, Any]],
    *,
    successful_responses: int,
    response_output_samples: int,
    max_inference_failures: int,
    max_host_failures: int,
    stall_timeout: float = 60.0,
) -> list[str]:
    errors: list[str] = []
    if not snapshots:
        return ["no runtime snapshots were observed"]
    _check_required(snapshots, _BASE_REQUIRED, errors)
    _check_counter_invariants(snapshots, errors)
    _check_counter_rollbacks(snapshots, _BASE_REQUIRED, errors)
    first, last = snapshots[0], snapshots[-1]
    for snapshot in snapshots:
        elapsed = snapshot["elapsedSeconds"]
        if snapshot.get("backend") != "official" or snapshot.get("ready") is not True:
            _add_error(
                errors,
                f"backend unhealthy at {elapsed}s: "
                f"{snapshot.get('backend')}/{snapshot.get('ready')}",
            )
        if snapshot.get("backendError") is not None:
            _add_error(errors, f"backendError at {elapsed}s: {snapshot['backendError']}")
        if snapshot.get("inferenceMetricsEpoch") != first.get("inferenceMetricsEpoch"):
            _add_error(errors, "inference metrics epoch changed during acceptance")
        if snapshot.get("hostMetricsEpoch") != first.get("hostMetricsEpoch"):
            _add_error(errors, "host metrics epoch changed during acceptance")
        if snapshot.get("streamGeneration") != first.get("streamGeneration"):
            _add_error(errors, "stream generation changed during acceptance")

    # LAN has no device callback counters, so use backend/host counters
    # as its progress signal. A healthy HTTP transport alone is insufficient.
    lan_progress_keys = (
        "inferenceSuccessCount",
        "inferenceInputSamples",
        "inferenceOutputSamples",
        "hostSuccessCount",
        "hostInputSamples",
        "hostOutputSamples",
    )
    last_values = {key: first.get(key) for key in lan_progress_keys}
    last_growth = {key: float(first["elapsedSeconds"]) for key in lan_progress_keys}
    for current in snapshots[1:]:
        elapsed = float(current["elapsedSeconds"])
        for key in lan_progress_keys:
            before, after = last_values[key], current.get(key)
            if not _is_counter(before) or not _is_counter(after):
                continue
            if after > before:
                last_growth[key] = elapsed
            elif elapsed - last_growth[key] >= stall_timeout:
                _add_error(errors, f"{key} stalled for more than {stall_timeout}s at {current['elapsedSeconds']}s")
            elif after < before:
                _add_error(errors, f"{key} reset during acceptance")
            last_values[key] = after

    inference_success = _counter_delta(first, last, "inferenceSuccessCount")
    host_success = _counter_delta(first, last, "hostSuccessCount")
    host_output = _counter_delta(first, last, "hostOutputSamples")
    if inference_success is not None and inference_success < successful_responses:
        _add_error(
            errors,
            "HTTP responses exceeded successful backend inference results: "
            f"{successful_responses}>{inference_success}",
        )
    if host_success is not None and host_success < successful_responses:
        _add_error(
            errors,
            "HTTP responses exceeded successful host results: "
            f"{successful_responses}>{host_success}",
        )
    if host_output is not None and host_output < response_output_samples:
        _add_error(
            errors,
            "REST output samples exceeded observed host output samples: "
            f"{response_output_samples}>{host_output}",
        )
    _check_error_delta(first, last, "inferenceFailureCount", max_inference_failures, errors)
    _check_error_delta(first, last, "hostFailureCount", max_host_failures, errors)
    return errors


def _device_policy(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "startupGraceSeconds": args.startup_grace,
        "switchGraceSeconds": args.switch_grace,
        "stallTimeoutSeconds": args.stall_timeout,
        "maxInferenceFailures": args.max_inference_failures,
        "maxHostFailures": args.max_host_failures,
        "maxCallbackErrors": args.max_callback_errors,
        "maxStatusEvents": args.max_status_events,
        "maxLoopErrors": args.max_loop_errors,
        "maxQueueDrops": args.max_queue_drops,
    }


def run_device(args: argparse.Namespace) -> int:
    started = time.monotonic()
    snapshots: list[dict[str, Any]] = []
    errors: list[str] = []
    events: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "mode": "device",
        "url": args.url,
        "requestedDurationSeconds": args.duration,
        "policy": _device_policy(args),
        "events": events,
        "snapshots": snapshots,
        "errors": errors,
    }
    original_chunk_size: int | None = None
    switched = False
    switch_elapsed: float | None = None
    interrupted = False

    try:
        initial = _request_json(f"{args.url}/info")
        if not isinstance(initial, dict):
            raise TypeError("initial /info response is not an object")
        snapshots.append(_snapshot(initial, 0))
        raw_chunk_size = initial.get("serverReadChunkSize")
        if not _is_counter(raw_chunk_size):
            raise ValueError("initial serverReadChunkSize is unknown")
        original_chunk_size = raw_chunk_size

        while True:
            elapsed = time.monotonic() - started
            if elapsed >= args.duration:
                break
            if not switched and elapsed >= args.duration * args.switch_fraction:
                _update_setting(args.url, "serverReadChunkSize", args.switch_chunk_size)
                switch_elapsed = elapsed
                events.append(
                    {
                        "elapsedSeconds": round(elapsed, 3),
                        "event": "chunk-size-switch",
                        "from": original_chunk_size,
                        "to": args.switch_chunk_size,
                    }
                )
                switched = True
            initial_success = snapshots[0].get("inferenceSuccessCount")
            have_success = any(
                _is_counter(item.get("inferenceSuccessCount"))
                and _is_counter(initial_success)
                and item["inferenceSuccessCount"] > initial_success
                for item in snapshots
            )
            interval = (
                min(args.first_packet_poll_interval, args.poll_interval)
                if not have_success
                else args.poll_interval
            )
            time.sleep(min(interval, max(0.0, args.duration - elapsed)))
            poll_elapsed = time.monotonic() - started
            try:
                info = _request_json(f"{args.url}/info")
                if not isinstance(info, dict):
                    raise TypeError("/info response is not an object")
                snapshot = _snapshot(info, poll_elapsed)
                snapshots.append(snapshot)
                print(
                    f"device elapsed={snapshot['elapsedSeconds']}s "
                    f"success={snapshot.get('inferenceSuccessCount')} "
                    f"written={snapshot.get('deviceOutputWriteCount')} "
                    f"p95={snapshot.get('p95InferenceMs')}ms",
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001 - preserve soak evidence
                _add_error(errors, f"poll failed at {poll_elapsed:.3f}s: {exc!r}")
    except KeyboardInterrupt:
        interrupted = True
        _add_error(errors, "acceptance interrupted by user")
    except Exception as exc:  # noqa: BLE001 - preserve partial report
        _add_error(errors, f"device acceptance failed: {exc!r}")
    finally:
        if switched and original_chunk_size is not None:
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
                _add_error(errors, f"chunk-size restore failed: {exc!r}")

        for message in _evaluate_device(
            snapshots,
            startup_grace=args.startup_grace,
            switch_elapsed=switch_elapsed,
            switch_grace=args.switch_grace,
            stall_timeout=args.stall_timeout,
            max_inference_failures=args.max_inference_failures,
            max_host_failures=args.max_host_failures,
            max_callback_errors=args.max_callback_errors,
            max_status_events=args.max_status_events,
            max_loop_errors=args.max_loop_errors,
            max_queue_drops=args.max_queue_drops,
        ):
            _add_error(errors, message)
        first = snapshots[0] if snapshots else {}
        last = snapshots[-1] if snapshots else {}
        first_packet = next(
            (
                item["elapsedSeconds"] * 1000
                for item in snapshots[1:]
                if (_counter_delta(first, item, "inferenceSuccessCount") or 0) > 0
                and (_counter_delta(first, item, "deviceOutputWriteCount") or 0) > 0
            ),
            None,
        )
        report.update(
            {
                "observedDurationSeconds": round(time.monotonic() - started, 3),
                "firstPacketObservedMs": first_packet,
                "inferenceAttemptDelta": _counter_delta(first, last, "inferenceCount"),
                "inferenceSuccessDelta": _counter_delta(first, last, "inferenceSuccessCount"),
                "inferenceFailureDelta": _counter_delta(first, last, "inferenceFailureCount"),
                "hostSuccessDelta": _counter_delta(first, last, "hostSuccessCount"),
                "hostFailureDelta": _counter_delta(first, last, "hostFailureCount"),
                "deviceOutputSamplesDelta": _counter_delta(first, last, "deviceOutputSamples"),
                "vram": _vram_summary(snapshots),
                "errorTypes": _error_types(errors),
                "status": "interrupted" if interrupted else ("ok" if not errors else "failed"),
            }
        )
        _write_report(args.json, report)

    keys = (
        "status",
        "inferenceSuccessDelta",
        "inferenceFailureDelta",
        "deviceOutputSamplesDelta",
        "firstPacketObservedMs",
        "vram",
        "errors",
    )
    print(json.dumps({key: report.get(key) for key in keys}, ensure_ascii=False))
    return 130 if interrupted else (0 if not errors else 1)


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
    started = time.monotonic()
    snapshots: list[dict[str, Any]] = []
    errors: list[str] = []
    mismatches: list[dict[str, int]] = []
    latencies: list[float] = []
    shape_events: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "mode": "lan",
        "url": args.url,
        "sameHostLanInterface": args.same_host_lan_interface,
        "requestedDurationSeconds": args.duration,
        "policy": {
            "maxInferenceFailures": args.max_inference_failures,
            "maxHostFailures": args.max_host_failures,
            "stallTimeoutSeconds": args.stall_timeout,
        },
        "shapeEvents": shape_events,
        "lengthMismatches": mismatches,
        "snapshots": snapshots,
        "errors": errors,
    }
    sequence = 0
    successful_responses = 0
    response_output_samples = 0
    first_packet_ms: float | None = None
    interrupted = False
    sample_rate: int | None = None

    try:
        source = _load_pcm16(args.wav)
        info = _request_json(f"{args.url}/info")
        if not isinstance(info, dict):
            raise TypeError("initial /info response is not an object")
        snapshots.append(_snapshot(info, 0))
        raw_sample_rate = info.get("inputSampleRate")
        if not _is_counter(raw_sample_rate) or raw_sample_rate <= 0:
            raise ValueError("inputSampleRate is unknown")
        sample_rate = raw_sample_rate
        chunk_sizes = [int(value) for value in args.chunk_sizes.split(",")]
        if not chunk_sizes or any(size <= 0 for size in chunk_sizes):
            raise ValueError("chunk sizes must contain positive integers")

        deadline = started
        source_offset = 0
        next_poll = started + args.poll_interval
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
                if not isinstance(response, dict):
                    raise TypeError("/test response is not an object")
                encoded = response.get("changedVoiceBase64")
                if not isinstance(encoded, str):
                    raise ValueError("changedVoiceBase64 is missing")
                output = base64.b64decode(encoded, validate=True)
                if len(output) % 2:
                    raise ValueError("response PCM16 byte length is odd")
                output_samples = len(output) // 2
                latency_ms = (time.monotonic() - request_started) * 1000
                latencies.append(latency_ms)
                successful_responses += 1
                response_output_samples += output_samples
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
                _add_error(errors, f"request {sequence}: {exc!r}")

            sequence += 1
            deadline += chunk_size / sample_rate
            now = time.monotonic()
            if now >= next_poll:
                try:
                    current = _request_json(f"{args.url}/info")
                    if not isinstance(current, dict):
                        raise TypeError("/info response is not an object")
                    snapshot = _snapshot(current, now - started)
                    snapshots.append(snapshot)
                    print(
                        f"lan elapsed={snapshot['elapsedSeconds']}s "
                        f"requests={sequence} responses={successful_responses} "
                        f"errors={len(errors)} p95={_percentile(latencies, 0.95)}ms",
                        flush=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    _add_error(errors, f"info poll {sequence}: {exc!r}")
                next_poll += args.poll_interval
            time.sleep(max(0.0, deadline - time.monotonic()))
    except KeyboardInterrupt:
        interrupted = True
        _add_error(errors, "acceptance interrupted by user")
    except Exception as exc:  # noqa: BLE001 - preserve partial report
        _add_error(errors, f"LAN acceptance failed: {exc!r}")
    finally:
        try:
            final_info = _request_json(f"{args.url}/info")
            if not isinstance(final_info, dict):
                raise TypeError("final /info response is not an object")
            snapshots.append(_snapshot(final_info, time.monotonic() - started))
        except Exception as exc:  # noqa: BLE001
            _add_error(errors, f"final info poll: {exc!r}")
        if mismatches:
            _add_error(errors, f"{len(mismatches)} response length mismatches")
        if first_packet_ms is None:
            _add_error(errors, "no successful response packet was observed")
        if len(shape_events) < 2:
            _add_error(errors, "no request-shape switch was observed")
        for message in _evaluate_lan(
            snapshots,
            successful_responses=successful_responses,
            response_output_samples=response_output_samples,
            max_inference_failures=args.max_inference_failures,
            max_host_failures=args.max_host_failures,
            stall_timeout=args.stall_timeout,
        ):
            _add_error(errors, message)
        latency_summary = {
            "count": len(latencies),
            "meanMs": statistics.fmean(latencies) if latencies else None,
            "p50Ms": _percentile(latencies, 0.50),
            "p95Ms": _percentile(latencies, 0.95),
            "maxMs": max(latencies) if latencies else None,
        }
        first = snapshots[0] if snapshots else {}
        last = snapshots[-1] if snapshots else {}
        report.update(
            {
                "observedDurationSeconds": round(time.monotonic() - started, 3),
                "sampleRate": sample_rate,
                "requestCount": sequence,
                "successfulResponseCount": successful_responses,
                "responseOutputSamples": response_output_samples,
                "inferenceSuccessDelta": _counter_delta(first, last, "inferenceSuccessCount"),
                "inferenceFailureDelta": _counter_delta(first, last, "inferenceFailureCount"),
                "hostSuccessDelta": _counter_delta(first, last, "hostSuccessCount"),
                "hostFailureDelta": _counter_delta(first, last, "hostFailureCount"),
                "firstPacketMs": first_packet_ms,
                "latency": latency_summary,
                "vram": _vram_summary(snapshots),
                "errorTypes": _error_types(errors),
                "status": "interrupted" if interrupted else ("ok" if not errors else "failed"),
            }
        )
        _write_report(args.json, report)

    keys = (
        "status",
        "requestCount",
        "successfulResponseCount",
        "inferenceSuccessDelta",
        "inferenceFailureDelta",
        "firstPacketMs",
        "latency",
        "vram",
        "errors",
    )
    print(json.dumps({key: report.get(key) for key in keys}, ensure_ascii=False))
    return 130 if interrupted else (0 if not errors else 1)


def _add_nonnegative_int(parser: argparse.ArgumentParser, name: str) -> None:
    parser.add_argument(name, type=int, default=0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:18889")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    device = subparsers.add_parser("device", help="observe the server audio device loop")
    # Keep accepting the handoff form: ``device --url ...`` as well as the
    # argparse-global form ``--url ... device``.
    device.add_argument("--url", dest="url", default=argparse.SUPPRESS)
    device.add_argument("--duration", type=float, default=600)
    device.add_argument("--poll-interval", type=float, default=30)
    device.add_argument("--first-packet-poll-interval", type=float, default=0.1)
    device.add_argument("--startup-grace", type=float, default=10)
    device.add_argument("--switch-grace", type=float, default=10)
    device.add_argument("--stall-timeout", type=float, default=60)
    device.add_argument("--switch-fraction", type=float, default=0.5)
    device.add_argument("--switch-chunk-size", type=int, default=40)
    for option in (
        "--max-inference-failures",
        "--max-host-failures",
        "--max-callback-errors",
        "--max-status-events",
        "--max-loop-errors",
        "--max-queue-drops",
    ):
        _add_nonnegative_int(device, option)
    device.add_argument("--json", type=Path, required=True)
    device.set_defaults(run=run_device)

    lan = subparsers.add_parser("lan", help="send paced PCM16 chunks over a LAN URL")
    lan.add_argument("--url", dest="url", default=argparse.SUPPRESS)
    lan.add_argument("--wav", type=Path, required=True)
    lan.add_argument("--duration", type=float, default=600)
    lan.add_argument("--poll-interval", type=float, default=30)
    lan.add_argument("--chunk-sizes", default="12000,4097,16000")
    lan.add_argument("--shape-every", type=int, default=120)
    lan.add_argument("--stall-timeout", type=float, default=60)
    _add_nonnegative_int(lan, "--max-inference-failures")
    _add_nonnegative_int(lan, "--max-host-failures")
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
