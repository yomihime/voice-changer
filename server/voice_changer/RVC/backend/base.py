from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from data.ModelSlot import RVCModelSlot
from voice_changer.utils.VoiceChangerModel import AudioInOut
from voice_changer.utils.VoiceChangerParams import VoiceChangerParams


@dataclass(frozen=True)
class RvcBackendConfig:
    params: VoiceChangerParams
    slot: RVCModelSlot
    settings: Any


@dataclass(frozen=True)
class RvcInferenceRequest:
    audio: AudioInOut
    crossfade_frame: int
    sola_search_frame: int
    input_sample_rate: int
    output_sample_rate: int


class RvcBackend(Protocol):
    name: str

    def load_model(self) -> None: ...

    def warmup(self) -> None: ...

    def unload_model(self) -> None: ...

    def infer(self, request: RvcInferenceRequest) -> np.ndarray: ...

    def update_settings(self, key: str, value: int | float | str) -> None: ...

    def supports_setting(self, key: str) -> bool: ...

    def set_device(self, gpu: int) -> None: ...

    def set_sampling_rate(self, input_sample_rate: int, output_sample_rate: int) -> None: ...

    def get_model_info(self) -> dict[str, Any]: ...

    def reset_metrics(self) -> None: ...

    def close(self) -> None: ...
