from collections import deque
from typing import Iterable
from uuid import uuid4

import torch


def _percentile(values: Iterable[float], fraction: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


class RollingInferenceMetrics:
    def __init__(self, capacity: int = 512):
        self.samples_ms: deque[float] = deque(maxlen=capacity)
        self.total_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.input_samples = 0
        self.output_samples = 0
        self.epoch = uuid4().hex

    def reset(self) -> None:
        self.samples_ms.clear()
        self.total_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.input_samples = 0
        self.output_samples = 0
        self.epoch = uuid4().hex

    def _record_attempt(self, elapsed_ms: float, input_samples: int) -> None:
        self.samples_ms.append(float(elapsed_ms))
        self.total_count += 1
        self.input_samples += int(input_samples)

    def record_success(
        self, elapsed_ms: float, input_samples: int, output_samples: int
    ) -> None:
        self._record_attempt(elapsed_ms, input_samples)
        self.success_count += 1
        self.output_samples += int(output_samples)

    def record_failure(self, elapsed_ms: float, input_samples: int) -> None:
        self._record_attempt(elapsed_ms, input_samples)
        self.failure_count += 1

    def record(self, elapsed_ms: float) -> None:
        """Record a successful attempt without sample totals for old callers."""
        self.record_success(elapsed_ms, 0, 0)

    def snapshot(self) -> dict[str, int | float | str | None]:
        samples = list(self.samples_ms)
        return {
            "inferenceCount": self.total_count,
            "inferenceSuccessCount": self.success_count,
            "inferenceFailureCount": self.failure_count,
            "inferenceInputSamples": self.input_samples,
            # Official output includes the fresh overlap/search context requested
            # by the host. This is not a played or REST-returned sample count.
            "inferenceOutputSamples": self.output_samples,
            "inferenceMetricsEpoch": self.epoch,
            "inferenceWindowSize": len(samples),
            "meanInferenceMs": sum(samples) / len(samples) if samples else None,
            "p50InferenceMs": _percentile(samples, 0.50),
            "p95InferenceMs": _percentile(samples, 0.95),
        }


def cuda_memory_snapshot(device: torch.device | str) -> dict[str, float | None]:
    empty = {
        "processCudaAllocatedMiB": None,
        "processCudaReservedMiB": None,
        "processCudaPeakAllocatedMiB": None,
    }
    resolved_device = torch.device(device)
    if resolved_device.type != "cuda" or not torch.cuda.is_available():
        return empty
    try:
        divisor = 1024 * 1024
        return {
            "processCudaAllocatedMiB": torch.cuda.memory_allocated(resolved_device)
            / divisor,
            "processCudaReservedMiB": torch.cuda.memory_reserved(resolved_device)
            / divisor,
            "processCudaPeakAllocatedMiB": torch.cuda.max_memory_allocated(
                resolved_device
            )
            / divisor,
        }
    except Exception:
        return empty
