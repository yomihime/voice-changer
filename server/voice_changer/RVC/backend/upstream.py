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
        self.input_buffer: torch.Tensor | None = None
        self._stream_rates: tuple[int, int] | None = None
        self._source_tail = np.empty(0, dtype=np.float32)
        self._pending_input_16k = np.empty(0, dtype=np.float32)
        self._pending_output = np.empty(0, dtype=np.float32)
        self._output_history = np.empty(0, dtype=np.float32)
        self._source_samples_total = 0
        self._resampled_samples_total = 0
        self._output_samples_total = 0
        self._max_context_output = 0
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
        self.input_buffer = None
        self._stream_rates = None
        self._source_tail = np.empty(0, dtype=np.float32)
        self._pending_input_16k = np.empty(0, dtype=np.float32)
        self._pending_output = np.empty(0, dtype=np.float32)
        self._output_history = np.empty(0, dtype=np.float32)
        self._source_samples_total = 0
        self._resampled_samples_total = 0
        self._output_samples_total = 0
        self._max_context_output = 0
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
    def _fit_tail(audio: np.ndarray, length: int) -> np.ndarray:
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if length <= 0:
            return np.empty(0, dtype=np.float32)
        if len(audio) >= length:
            return audio[-length:]
        return np.pad(audio, (length - len(audio), 0))

    def _ensure_stream(self, input_sample_rate: int, output_sample_rate: int) -> None:
        rates = (input_sample_rate, output_sample_rate)
        if self._stream_rates == rates:
            return
        self._reset_stream_state()
        self._stream_rates = rates
        self._pending_output = np.zeros(
            max(1, output_sample_rate // 100), dtype=np.float32
        )

    def _resample_input_block(
        self, normalized: np.ndarray, input_sample_rate: int
    ) -> np.ndarray:
        self._source_samples_total += len(normalized)
        target_total = self._source_samples_total * 16000 // input_sample_rate
        target_length = target_total - self._resampled_samples_total
        self._resampled_samples_total = target_total

        overlap = max(1, input_sample_rate // 50)
        source = np.concatenate((self._source_tail, normalized))
        self._source_tail = source[-overlap:].copy()
        if source.size == 0 or target_length == 0:
            return np.empty(0, dtype=np.float32)
        resampled = resampy.resample(
            source,
            input_sample_rate,
            16000,
            filter="kaiser_fast",
        ).astype(np.float32, copy=False)
        return self._fit_tail(resampled, target_length)

    def _append_engine_output(
        self, processed_input_16k: np.ndarray, extra_16k: int, output_sample_rate: int
    ) -> None:
        if self.engine is None or processed_input_16k.size == 0:
            return
        block_frame_16k = len(processed_input_16k)
        required_length = extra_16k + block_frame_16k
        if self.input_buffer is None or len(self.input_buffer) < required_length:
            grown = torch.zeros(
                required_length, device=self.device, dtype=torch.float32
            )
            if self.input_buffer is not None:
                keep = min(len(self.input_buffer), required_length)
                grown[-keep:] = self.input_buffer[-keep:]
            self.input_buffer = grown

        incoming = torch.from_numpy(processed_input_16k).to(self.device)
        if block_frame_16k >= len(self.input_buffer):
            self.input_buffer.copy_(incoming[-len(self.input_buffer) :])
        else:
            self.input_buffer[:-block_frame_16k] = self.input_buffer[
                block_frame_16k:
            ].clone()
            self.input_buffer[-block_frame_16k:] = incoming

        output = self.engine.infer(
            self.input_buffer,
            block_frame_16k,
            (len(self.input_buffer) - block_frame_16k) // 160,
            block_frame_16k // 160,
            self.settings.f0Detector,
        )
        converted = output.detach().float().cpu().numpy().reshape(-1)
        if self.engine.tgt_sr != output_sample_rate:
            converted = resampy.resample(
                converted,
                self.engine.tgt_sr,
                output_sample_rate,
                filter="kaiser_fast",
            )
        converted = converted.astype(np.float32, copy=False) * 32767.5
        expected = int(round(block_frame_16k * output_sample_rate / 16000))
        converted = self._fit_tail(converted, expected)
        self._pending_output = np.concatenate((self._pending_output, converted))

    def _emit_host_block(self, block_length: int, context_length: int) -> np.ndarray:
        if len(self._pending_output) < block_length:
            self._pending_output = np.pad(
                self._pending_output, (0, block_length - len(self._pending_output))
            )
        emitted = self._pending_output[:block_length]
        self._pending_output = self._pending_output[block_length:]
        context = self._fit_tail(self._output_history, context_length)
        self._max_context_output = max(self._max_context_output, context_length)
        if self._max_context_output:
            self._output_history = np.concatenate(
                (self._output_history, emitted)
            )[-self._max_context_output :]
        else:
            self._output_history = np.empty(0, dtype=np.float32)
        return np.concatenate((context, emitted))

    def infer(self, request: RvcInferenceRequest) -> np.ndarray:
        started = perf_counter()
        try:
            return self._infer(request)
        finally:
            self.metrics.record((perf_counter() - started) * 1000.0)

    def _infer(self, request: RvcInferenceRequest) -> np.ndarray:
        if not self._ready or self.engine is None:
            raise RvcInferenceError("Official RVC backend is not ready")
        self._validate_f0_method(self.settings.f0Detector)
        self._ensure_stream(request.input_sample_rate, request.output_sample_rate)

        normalized = request.audio.astype(np.float32) / 32768.0
        audio_16k = self._resample_input_block(
            normalized, request.input_sample_rate
        )
        self._pending_input_16k = np.concatenate(
            (self._pending_input_16k, audio_16k)
        )
        process_length = len(self._pending_input_16k) // 160 * 160
        processed = self._pending_input_16k[:process_length]
        self._pending_input_16k = self._pending_input_16k[process_length:]
        extra_16k = self._round_to_10ms_16k(
            self.settings.extraConvertSize, request.input_sample_rate
        )

        try:
            self._append_engine_output(
                processed,
                extra_16k,
                request.output_sample_rate,
            )
        except Exception as exc:
            raise RvcInferenceError(f"Official RVC inference failed: {exc}") from exc

        target_output_total = (
            self._source_samples_total
            * request.output_sample_rate
            // request.input_sample_rate
        )
        output_length = target_output_total - self._output_samples_total
        self._output_samples_total = target_output_total
        context_length = int(
            round(
                (request.crossfade_frame + request.sola_search_frame)
                * request.output_sample_rate
                / request.input_sample_rate
            )
        )
        return self._emit_host_block(output_length, context_length)

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
