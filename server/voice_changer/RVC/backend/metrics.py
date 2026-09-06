from collections import deque
from typing import Iterable

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

    def reset(self) -> None:
        self.samples_ms.clear()
        self.total_count = 0

    def record(self, elapsed_ms: float) -> None:
        self.samples_ms.append(float(elapsed_ms))
        self.total_count += 1

    def snapshot(self) -> dict[str, int | float | None]:
        samples = list(self.samples_ms)
        return {
            "inferenceCount": self.total_count,
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
