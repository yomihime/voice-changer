import gc
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from typing import Any

import numpy as np
import resampy
import torch

from mods.log_control import VoiceChangaerLogger
from downloader.WeightDownloader import (
    ensureRvcUpstreamAssets,
    rvcUpstreamAssetsPresent,
)
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
from voice_changer.RVC.backend.input_stream import OfficialInputStream
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

    Host adaptation is explicit below; vendored feature, retrieval, and model
    inference behavior otherwise follows the pinned upstream source.
    """

    name = "official"

    def __init__(self, config: RvcBackendConfig):
        self.config = config
        self.settings = config.settings
        self.engine = None
        self.device = torch.device("cpu")
        self.input_sample_rate = 48000
        self.output_sample_rate = 48000
        self._reset_stream_state()
        self._ready = False
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
        self._ready = False
        if self.config.slot.isONNX:
            raise RvcBackendConfigError(
                "Official backend supports PyTorch .pth RVC models only"
            )
        self._validate_f0_method(self.settings.f0Detector)
        model_path = self._model_path
        if not model_path.is_file():
            raise RvcModelLoadError(f"RVC model not found: {model_path}")
        hubert_path = self._hubert_path()
        if not rvcUpstreamAssetsPresent(self.config.params):
            if not getattr(self.config.params, "allow_downloads", True):
                raise RvcModelLoadError(
                    "Official Transformers HuBERT assets are missing and downloads "
                    f"are disabled: {hubert_path}"
                )
            try:
                ensureRvcUpstreamAssets(self.config.params)
            except Exception as exc:
                raise RvcModelLoadError(
                    "Unable to prepare Official Transformers HuBERT assets: "
                    f"{exc}"
                ) from exc

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
            "f0=%s indexRate=%s cudaGraph=%s",
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
            cuda_graph_enabled,
        )

    def warmup(self) -> None:
        self._ready = False
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
        self._ready = True

    def _reset_stream_state(self) -> None:
        self.input_buffer: torch.Tensor | None = None
        self._stream_rates: tuple[int, int] | None = None
        self._input_stream = OfficialInputStream()
        self._output_samples_total = 0
        self._processed_samples_16k = 0
        self._stream_context = None
        self.stream_generation = getattr(self, "stream_generation", 0) + 1
        if self.engine is not None:
            self.engine.cache_pitch.zero_()
            self.engine.cache_pitchf.zero_()

    def unload_model(self) -> None:
        self._ready = False
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
        self.validate_sampling_rates(input_sample_rate, output_sample_rate)
        if (self.input_sample_rate, self.output_sample_rate) == (input_sample_rate, output_sample_rate):
            return
        self.input_sample_rate = input_sample_rate
        self.output_sample_rate = output_sample_rate
        self._reset_stream_state()

    def set_device(self, gpu: int) -> None:
        previous = self.device
        self.unload_model()
        self.load_model()
        self.set_sampling_rate(self.input_sample_rate, self.output_sample_rate)
        self.warmup()
        logger.info(
            "[Voice Changer][RVC Backend] Official moved: %s -> %s",
            previous,
            self.device,
        )

    def update_settings(self, key: str, value: int | float | str) -> None:
        if not self._ready or self.engine is None:
            raise RvcBackendConfigError("Official RVC backend is not ready")
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
        elif key == "extraConvertSize":
            if int(value) < 0:
                raise RvcBackendConfigError("extraConvertSize must be non-negative")
            self._reset_stream_state()
        else:
            try:
                applied = apply_upstream_runtime_setting(self.engine, key, value)
                if not applied:
                    raise RvcBackendConfigError(
                        f"Official RVC does not support setting {key}"
                    )
            except Exception as exc:
                if isinstance(exc, RvcBackendConfigError):
                    raise
                raise RvcBackendConfigError(
                    f"Invalid Official RVC setting {key}={value!r}: {exc}"
                ) from exc

    def supports_setting(self, key: str) -> bool:
        return key in {
            "gpu",
            "dstId",
            "f0Detector",
            "tran",
            "extraConvertSize",
            "indexRatio",
        }

    @staticmethod
    def _round_to_10ms_16k(samples: int, sample_rate: int) -> int:
        return max(0, int(np.round(samples / sample_rate * 100))) * 160

    @staticmethod
    def validate_sampling_rates(input_sample_rate: int, output_sample_rate: int) -> None:
        # Integer 10 ms boundaries are shared by the source, 16 kHz pitch and
        # output clocks. Other rates are rejected rather than rounded per block.
        supported = {16000, 24000, 32000, 40000, 44100, 48000, 88200, 96000}
        if input_sample_rate not in supported or output_sample_rate not in supported:
            raise RvcBackendConfigError("Official sample rates must be one of " + str(sorted(supported)))

    def _ensure_stream(self, request: RvcInferenceRequest) -> None:
        rates = (request.input_sample_rate, request.output_sample_rate)
        context = (request.crossfade_frame, request.sola_search_frame)
        if self._stream_rates == rates and self._stream_context == context:
            return
        self._reset_stream_state()
        self._stream_rates = rates
        self._stream_context = context

    def _infer_window(self, processed: np.ndarray, extra_16k: int,
                      start: int, length: int, output_rate: int) -> np.ndarray:
        block = len(processed)
        if block == 0:
            if start + length > 0:
                raise RvcInferenceError("Official requires at least one complete 10 ms input frame")
            return np.zeros(length, dtype=np.float32)  # explicit pre-stream time only
        self._processed_samples_16k += block
        frame_out = output_rate // 100
        end = self._processed_samples_16k // 160 * frame_out
        frames = (end - start + frame_out - 1) // frame_out
        required = extra_16k + frames * 160
        if required // 160 > 1024:
            raise RvcInferenceError("Official context and chunk exceed the upstream 1024-frame pitch cache")
        if self.input_buffer is None or len(self.input_buffer) != required:
            resized = torch.zeros(required, device=self.device, dtype=torch.float32)
            if self.input_buffer is not None:
                keep = min(len(self.input_buffer), required)
                resized[-keep:] = self.input_buffer[-keep:]
            self.input_buffer = resized
        if block >= required:
            self.input_buffer.copy_(torch.from_numpy(processed[-required:]).to(self.device))
        else:
            self.input_buffer[:-block] = self.input_buffer[block:].clone()
            self.input_buffer[-block:] = torch.from_numpy(processed).to(self.device)
        output = self.engine.infer(self.input_buffer, block, extra_16k // 160,
                                   frames, self.settings.f0Detector)
        converted = output.detach().float().cpu().numpy().reshape(-1)
        expected = frames * self.engine.tgt_sr // 100
        if len(converted) != expected or not np.isfinite(converted).all():
            raise RvcInferenceError(f"Official engine returned invalid window: {len(converted)} samples, expected {expected}")
        if self.engine.tgt_sr != output_rate:
            converted = resampy.resample(converted, self.engine.tgt_sr, output_rate, filter="kaiser_fast")
        window_start = end - frames * frame_out
        offset = start - window_start
        result = converted[offset:offset + length].astype(np.float32, copy=True) * 32767.5
        if len(result) != length:
            raise RvcInferenceError("Official output window does not cover requested host timeline")
        # Negative source positions are the documented fixed startup latency,
        # never replacement audio for a short/failed model result.
        result[:min(length, max(0, -start))] = 0
        return result

    def infer(self, request: RvcInferenceRequest) -> np.ndarray:
        started = perf_counter()
        try:
            result = self._infer(request)
        except Exception:
            self.metrics.record_failure(
                (perf_counter() - started) * 1000.0, len(request.audio)
            )
            raise
        self.metrics.record_success(
            (perf_counter() - started) * 1000.0,
            len(request.audio),
            len(result),
        )
        return result

    def _infer(self, request: RvcInferenceRequest) -> np.ndarray:
        if not self._ready or self.engine is None:
            raise RvcInferenceError("Official RVC backend is not ready")
        self._validate_f0_method(self.settings.f0Detector)
        self.validate_sampling_rates(request.input_sample_rate, request.output_sample_rate)
        if (request.audio.ndim != 1 or len(request.audio) < request.input_sample_rate // 100
                or request.crossfade_frame < 0 or request.sola_search_frame < 0
                or self.settings.extraConvertSize < 0):
            raise RvcBackendConfigError("Official expects mono PCM chunks of at least 10 ms and non-negative context")
        if self.engine.tgt_sr not in {32000, 40000, 48000}:
            raise RvcBackendConfigError("Official model sample rate must be 32000, 40000 or 48000")
        self._ensure_stream(request)
        processed = self._input_stream.push(request.audio, request.input_sample_rate)
        extra_16k = self._round_to_10ms_16k(self.settings.extraConvertSize, request.input_sample_rate)
        target_total = self._input_stream.source_samples_total * request.output_sample_rate // request.input_sample_rate
        block_length = target_total - self._output_samples_total
        context = sum(samples * request.output_sample_rate // request.input_sample_rate
                      for samples in (request.crossfade_frame, request.sola_search_frame))
        # Fixed latency: overlap + search + 10 ms resampler lookahead + up to
        # one 10 ms pitch frame. Every returned sample has an absolute position.
        delay = context + request.output_sample_rate // 50
        start = self._output_samples_total - delay
        try:
            result = self._infer_window(processed, extra_16k, start, block_length + context,
                                        request.output_sample_rate)
        except Exception as exc:
            self._reset_stream_state()
            raise RvcInferenceError(f"Official RVC inference failed: {exc}") from exc
        self._output_samples_total = target_total
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
            "streamGeneration": self.stream_generation,
            "ready": self._ready,
            "upstreamCommit": UPSTREAM_COMMIT,
            "device": str(self.device),
            "gpuName": gpu_name,
            "version": getattr(self.engine, "version", None),
            "sampleRate": getattr(self.engine, "tgt_sr", None),
            "f0": bool(getattr(self.engine, "if_f0", self.config.slot.f0)),
            "speaker": self.settings.dstId,
            "supportedSettings": sorted(
                key
                for key in self.settings.intData
                + self.settings.floatData
                + self.settings.strData
                if self.supports_setting(key)
            ),
        }

    def reset_metrics(self) -> None:
        self.metrics.reset()

    def close(self) -> None:
        self.unload_model()
