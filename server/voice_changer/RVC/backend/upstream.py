import gc
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from typing import Any

import numpy as np
import resampy
import torch

from mods.log_control import VoiceChangaerLogger
from voice_changer.RVC.backend.base import RvcBackendConfig, RvcInferenceRequest
from voice_changer.RVC.backend.device import resolve_torch_device
from voice_changer.RVC.backend.config_mapping import (
    apply_upstream_runtime_setting,
    validate_upstream_f0,
)
from voice_changer.RVC.backend.exceptions import (
    RvcBackendConfigError,
    RvcIndexLoadError,
    RvcInferenceError,
    RvcModelLoadError,
)
from voice_changer.RVC.backend.metrics import (
    RollingInferenceMetrics,
    cuda_memory_snapshot,
)
from voice_changer.RVC.backend.upstream_loader import load_upstream_module
from voice_changer.RVC.deviceManager.DeviceManager import DeviceManager

logger = VoiceChangaerLogger.get_instance().getLogger()

UPSTREAM_COMMIT = "81eed5e8f68b6bed1789f682fe78cdd324495afc"


class UpstreamRvcBackend:
    """VCClient adapter for official RVC's realtime inference core.

    Integration policy: prefer upstream's supported entry points and preserve
    its inference flow. Keep adaptation limited to host I/O, stream geometry,
    settings, resources, and device/lifecycle requirements. This adapter must
    not depend on Hybrid or acquire custom audio-enhancement algorithms.

    Existing downstream processing and vendor patches still require a separate
    convergence review; this policy does not assert upstream parity today.
    """

    name = "official"

    def __init__(self, config: RvcBackendConfig):
        self.config = config
        self.settings = config.settings
        self.engine = None
        self.device = torch.device("cpu")
        self.input_sample_rate = 48000
        self.output_sample_rate = 48000
        self.input_buffer: torch.Tensor | None = None
        self._buffer_shape: tuple[int, int] | None = None
        self.metrics = RollingInferenceMetrics()

    @property
    def _model_path(self) -> Path:
        return Path(self.config.params.model_dir) / str(
            self.config.slot.slotIndex
        ) / Path(self.config.slot.modelFile).name

    @property
    def _index_path(self) -> Path:
        return Path(self.config.params.model_dir) / str(
            self.config.slot.slotIndex
        ) / Path(self.config.slot.indexFile).name

    def _hubert_path(self) -> Path:
        configured = getattr(self.config.params, "rvc_upstream_hubert", "")
        return Path(configured or "pretrain/rvc-upstream-hubert-base")

    def _validate_f0_method(self, method: str) -> None:
        validate_upstream_f0(method, self.config.slot.f0)

    def load_model(self) -> None:
        if self.config.slot.isONNX:
            raise RvcBackendConfigError(
                "Official backend supports PyTorch .pth RVC models only"
            )
        self._validate_f0_method(self.settings.f0Detector)
        model_path = self._model_path
        if not model_path.is_file():
            raise RvcModelLoadError(f"RVC model not found: {model_path}")
        hubert_path = self._hubert_path()
        if not (hubert_path / "config.json").is_file():
            raise RvcModelLoadError(
                "Official Transformers HuBERT assets are missing: "
                f"{hubert_path}. See docs/rvc-upstream-integration.md"
            )

        self.device = resolve_torch_device(self.settings.gpu)
        gpu_name = (
            torch.cuda.get_device_name(self.device)
            if self.device.type == "cuda"
            else "CPU"
        )
        is_half = DeviceManager.get_instance().halfPrecisionAvailable(
            self.settings.gpu
        )
        index_path = self._index_path
        if self.settings.indexRatio and not index_path.is_file():
            raise RvcIndexLoadError(f"RVC index not found: {index_path}")

        try:
            cuda_graph = load_upstream_module("tools.cuda_graph")
            cuda_graph_enabled = cuda_graph.configure_cuda_graph(self.device)
            realtime = load_upstream_module("infer.rtrvc")
            runtime_config = SimpleNamespace(
                device=self.device,
                is_half=is_half,
                cuda_graph=cuda_graph_enabled,
            )
            logger.info("[Voice Changer][RVC Backend] Loading Official backend")
            self.engine = realtime.RVC(
                self.settings.tran,
                0,
                str(model_path),
                str(index_path) if index_path.is_file() else "",
                self.settings.indexRatio,
                runtime_config,
                hubert_path=str(hubert_path),
                rmvpe_path=self.config.params.rmvpe,
                speaker_id=self.settings.dstId,
                protect=self.settings.protect,
            )
            self.engine.change_speaker_id(self.settings.dstId)
        except (RvcModelLoadError, RvcIndexLoadError):
            raise
        except Exception as exc:
            self.engine = None
            raise RvcModelLoadError(
                f"Official RVC model initialization failed: {exc}"
            ) from exc

        self._reset_stream_state()
        self.metrics.reset()
        logger.info(
            "[Voice Changer][RVC Backend] Official loaded: commit=%s model=%s "
            "index=%s version=%s sr=%s speaker=%s device=%s gpu=%s precision=%s "
            "f0=%s indexRate=%s protect=%s cudaGraph=%s",
            UPSTREAM_COMMIT[:12],
            model_path,
            index_path if index_path.is_file() else "disabled",
            self.engine.version,
            self.engine.tgt_sr,
            self.settings.dstId,
            self.device,
            gpu_name,
            "fp16" if is_half else "fp32",
            self.settings.f0Detector,
            self.settings.indexRatio,
            self.settings.protect,
            cuda_graph_enabled,
        )

    def warmup(self) -> None:
        if self.engine is None:
            raise RvcModelLoadError("Official RVC backend is not loaded")
        logger.info("[Voice Changer][RVC Backend] Official warming up")
        try:
            probe = torch.zeros(16000, device=self.device, dtype=torch.float32)
            self.engine.infer(
                probe,
                block_frame_16k=1600,
                skip_head=80,
                return_length=20,
                f0method=self.settings.f0Detector,
            )
            self.engine.cache_pitch.zero_()
            self.engine.cache_pitchf.zero_()
        except Exception as exc:
            if self.settings.indexRatio:
                raise RvcIndexLoadError(
                    f"Official RVC index warmup failed: {exc}"
                ) from exc
            raise RvcModelLoadError(
                f"Official RVC warmup failed: {exc}"
            ) from exc
        logger.info(
            "[Voice Changer][RVC Backend] Official Ready: commit=%s device=%s",
            UPSTREAM_COMMIT[:12],
            self.device,
        )

    def _reset_stream_state(self) -> None:
        self.input_buffer = None
        self._buffer_shape = None
        if self.engine is not None:
            self.engine.cache_pitch.zero_()
            self.engine.cache_pitchf.zero_()

    def unload_model(self) -> None:
        engine = self.engine
        self.engine = None
        self._reset_stream_state()
        if engine is not None:
            try:
                cuda_graph = load_upstream_module("tools.cuda_graph")
                for attribute in ("model", "net_g", "model_rmvpe", "model_fcpe"):
                    owner = getattr(engine, attribute, None)
                    if owner is not None:
                        cuda_graph.clear_cuda_graph_cache(owner)
            except Exception:
                logger.exception(
                    "[Voice Changer][RVC Backend] Official cleanup failed"
                )
            del engine
            gc.collect()

    def set_sampling_rate(self, input_sample_rate: int, output_sample_rate: int) -> None:
        self.input_sample_rate = input_sample_rate
        self.output_sample_rate = output_sample_rate
        self._reset_stream_state()

    def set_device(self, gpu: int) -> None:
        previous = self.device
        self.unload_model()
        self.load_model()
        logger.info(
            "[Voice Changer][RVC Backend] Official moved: %s -> %s",
            previous,
            self.device,
        )

    def update_settings(self, key: str, value: int | float | str) -> None:
        if self.engine is None:
            return
        if key == "gpu":
            self.set_device(int(value))
        elif key == "indexRatio":
            try:
                apply_upstream_runtime_setting(self.engine, key, value)
            except Exception as exc:
                raise RvcIndexLoadError(
                    f"Unable to enable official RVC index: {exc}"
                ) from exc
        elif key == "f0Detector":
            self._validate_f0_method(str(value))
        else:
            try:
                apply_upstream_runtime_setting(self.engine, key, value)
            except Exception as exc:
                raise RvcBackendConfigError(
                    f"Invalid Official RVC setting {key}={value!r}: {exc}"
                ) from exc

    @staticmethod
    def _seconds_to_16k_frames(samples: int, sample_rate: int) -> int:
        return max(0, int(samples / sample_rate * 16000))

    def infer(self, request: RvcInferenceRequest) -> np.ndarray:
        started = perf_counter()
        try:
            return self._infer(request)
        finally:
            self.metrics.record((perf_counter() - started) * 1000.0)

    def _infer(self, request: RvcInferenceRequest) -> np.ndarray:
        if self.engine is None:
            raise RvcInferenceError("Official RVC backend is not ready")
        self._validate_f0_method(self.settings.f0Detector)

        normalized = request.audio.astype(np.float32) / 32768.0
        audio_16k = resampy.resample(
            normalized,
            request.input_sample_rate,
            16000,
            filter="kaiser_fast",
        ).astype(np.float32, copy=False)
        block_frame_16k = len(audio_16k)
        crossfade_16k = self._seconds_to_16k_frames(
            request.crossfade_frame, request.input_sample_rate
        )
        sola_16k = self._seconds_to_16k_frames(
            request.sola_search_frame, request.input_sample_rate
        )
        extra_16k = self._seconds_to_16k_frames(
            self.settings.extraConvertSize, request.input_sample_rate
        )
        buffer_length = max(
            160,
            extra_16k + crossfade_16k + sola_16k + block_frame_16k,
        )
        shape = (buffer_length, block_frame_16k)
        if self.input_buffer is None or self._buffer_shape != shape:
            self.input_buffer = torch.zeros(
                buffer_length, device=self.device, dtype=torch.float32
            )
            self._buffer_shape = shape
            self.engine.cache_pitch.zero_()
            self.engine.cache_pitchf.zero_()

        incoming = torch.from_numpy(audio_16k).to(self.device)
        if block_frame_16k >= buffer_length:
            self.input_buffer.copy_(incoming[-buffer_length:])
        else:
            self.input_buffer[:-block_frame_16k] = self.input_buffer[
                block_frame_16k:
            ].clone()
            self.input_buffer[-block_frame_16k:] = incoming

        volume = float(np.sqrt(np.square(normalized).mean()))
        return_length = max(
            1,
            int(np.ceil((block_frame_16k + crossfade_16k + sola_16k) / 160)),
        )
        skip_head = extra_16k // 160
        if volume < self.settings.silentThreshold:
            output_length = return_length * int(request.output_sample_rate // 100)
            return np.zeros(output_length, dtype=np.int16)

        try:
            output = self.engine.infer(
                self.input_buffer,
                block_frame_16k,
                skip_head,
                return_length,
                self.settings.f0Detector,
            )
            result = output.detach().float().cpu().numpy()
        except Exception as exc:
            raise RvcInferenceError(f"Official RVC inference failed: {exc}") from exc
        result = result * 32767.5 * np.sqrt(volume)
        if self.engine.tgt_sr != request.output_sample_rate:
            result = resampy.resample(
                result,
                self.engine.tgt_sr,
                request.output_sample_rate,
                filter="kaiser_fast",
            )
        return result

    def get_model_info(self) -> dict[str, Any]:
        gpu_name = (
            torch.cuda.get_device_name(self.device)
            if self.device.type == "cuda"
            else "CPU"
        )
        return {
            **self.metrics.snapshot(),
            **cuda_memory_snapshot(self.device),
            "backend": self.name,
            "ready": self.engine is not None,
            "upstreamCommit": UPSTREAM_COMMIT,
            "device": str(self.device),
            "gpuName": gpu_name,
            "version": getattr(self.engine, "version", None),
            "sampleRate": getattr(self.engine, "tgt_sr", None),
            "f0": bool(getattr(self.engine, "if_f0", self.config.slot.f0)),
            "speaker": self.settings.dstId,
        }

    def reset_metrics(self) -> None:
        self.metrics.reset()

    def close(self) -> None:
        self.unload_model()
