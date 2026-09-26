"""Official RVC's continuous source clock and 16 kHz input frames.

The adapter recreates this state when rates or context change. Model buffers,
pitch caches, output windows, and stream generations belong to the adapter.
"""

import numpy as np
import resampy

from voice_changer.RVC.backend.exceptions import RvcInferenceError


class OfficialInputStream:
    def __init__(self):
        self.source_samples_total = 0
        self._resampled_samples_total = 0
        self._source_tail = np.empty(0, dtype=np.float32)
        self._pending_input_16k = np.empty(0, dtype=np.float32)

    def push(self, audio: np.ndarray, input_sample_rate: int) -> np.ndarray:
        """Normalize mono PCM and return complete 10 ms frames at 16 kHz.

        Caller validates the source rate and block geometry before pushing.
        Fractional frames stay buffered across arbitrary callback boundaries.
        """
        normalized = audio.astype(np.float32) / 32768.0
        audio_16k = self._resample_block(normalized, input_sample_rate)
        self._pending_input_16k = np.concatenate((self._pending_input_16k, audio_16k))
        process_length = len(self._pending_input_16k) // 160 * 160
        processed = self._pending_input_16k[:process_length]
        self._pending_input_16k = self._pending_input_16k[process_length:]
        return processed

    def _resample_block(self, normalized: np.ndarray, input_sample_rate: int) -> np.ndarray:
        source_start = self.source_samples_total - len(self._source_tail)
        source = np.concatenate((self._source_tail, normalized))
        self.source_samples_total += len(normalized)
        frame = input_sample_rate // 100
        # Retain filter context on the global 10 ms grid. A 10 ms lookahead
        # makes the resampling kernel independent of arbitrary host boundaries.
        keep = min(len(source), self.source_samples_total % frame + 4 * frame)
        self._source_tail = source[-keep:].copy()
        target_total = max(0, (self.source_samples_total - frame) * 16000 // input_sample_rate)
        offset = self._resampled_samples_total - source_start * 16000 // input_sample_rate
        count = target_total - self._resampled_samples_total
        if count <= 0:
            return np.empty(0, dtype=np.float32)
        resampled = resampy.resample(source, input_sample_rate, 16000, filter="kaiser_fast")
        result = resampled[offset:offset + count].astype(np.float32, copy=False)
        if len(result) != count:
            raise RvcInferenceError("Official input resampling timeline underflow")
        self._resampled_samples_total = target_total
        return result
