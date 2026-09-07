from typing import Any, cast
from time import perf_counter

import numpy as np
import resampy
import torch

from Exceptions import (
    DeviceCannotSupportHalfPrecisionException,
    PipelineCreateException,
    PipelineNotInitializedException,
)
from mods.log_control import VoiceChangaerLogger
from voice_changer.RVC.backend.base import RvcBackendConfig, RvcInferenceRequest
from voice_changer.RVC.backend.metrics import (
    RollingInferenceMetrics,
    cuda_memory_snapshot,
)
from voice_changer.RVC.deviceManager.DeviceManager import DeviceManager
from voice_changer.RVC.embedder.EmbedderManager import EmbedderManager
from voice_changer.RVC.pitchExtractor.PitchExtractorManager import PitchExtractorManager
from voice_changer.RVC.pipeline.Pipeline import Pipeline
from voice_changer.RVC.pipeline.PipelineGenerator import createPipeline

logger = VoiceChangaerLogger.get_instance().getLogger()


class LegacyRvcBackend:
    """Thin wrapper around VCClient's existing RVC implementation."""

    name = "legacy"

    def __init__(self, config: RvcBackendConfig):
        self.config = config
        self.settings = config.settings
        self.pipeline: Pipeline | None = None
        self.input_sample_rate = 48000
        self.output_sample_rate = 48000
        self.audio_buffer = None
        self.pitchf_buffer = None
        self.feature_buffer = None
        self.prev_vol = 0.0
        self._ready = False
        self.metrics = RollingInferenceMetrics()
        self.device_manager = DeviceManager.get_instance()
        EmbedderManager.initialize(config.params)
        PitchExtractorManager.initialize(config.params)

    def load_model(self) -> None:
        logger.info("[Voice Changer][RVC Backend] Loading Legacy backend")
        self._ready = False
        try:
            self.pipeline = createPipeline(
                self.config.params,
                self.config.slot,
                self.settings.gpu,
                self.settings.f0Detector,
            )
        except PipelineCreateException:
            logger.exception("[Voice Changer][RVC Backend] Legacy pipeline creation failed")
            raise
        self._reset_stream_state()
        self.metrics.reset()
        logger.info("[Voice Changer][RVC Backend] Legacy backend ready")

    def unload_model(self) -> None:
        self._ready = False
        self.pipeline = None
        self._reset_stream_state()

    def warmup(self) -> None:
        # The legacy managers eagerly load their model components in createPipeline.
        if self.pipeline is None:
            raise PipelineNotInitializedException()
        self._ready = True

    def _reset_stream_state(self) -> None:
        self.audio_buffer = None
        self.pitchf_buffer = None
        self.feature_buffer = None
        self.prev_vol = 0.0

    def set_sampling_rate(self, input_sample_rate: int, output_sample_rate: int) -> None:
        self.input_sample_rate = input_sample_rate
        self.output_sample_rate = output_sample_rate

    def set_device(self, gpu: int) -> None:
        self.device_manager.setForceTensor(False)
        self.load_model()
        self.set_sampling_rate(self.input_sample_rate, self.output_sample_rate)
        self.warmup()

    def update_settings(self, key: str, value: int | float | str) -> None:
        if key == "gpu":
            self.set_device(int(value))
        elif key == "f0Detector" and self.pipeline is not None:
            pitch_extractor = PitchExtractorManager.getPitchExtractor(
                str(value), self.settings.gpu
            )
            self.pipeline.setPitchExtractor(pitch_extractor)

    def _generate_input(
        self,
        new_data: np.ndarray,
        crossfade_size: int,
        sola_search_frame: int,
        extra_frame: int,
    ):
        input_size = new_data.shape[0]
        new_data = new_data.astype(np.float32) / 32768.0
        new_feature_length = input_size // 160

        if self.audio_buffer is not None:
            self.audio_buffer = np.concatenate([self.audio_buffer, new_data], 0)
            if self.config.slot.f0:
                self.pitchf_buffer = np.concatenate(
                    [self.pitchf_buffer, np.zeros(new_feature_length)], 0
                )
            self.feature_buffer = np.concatenate(
                [
                    self.feature_buffer,
                    np.zeros(
                        [new_feature_length, self.config.slot.embChannels]
                    ),
                ],
                0,
            )
        else:
            self.audio_buffer = new_data
            if self.config.slot.f0:
                self.pitchf_buffer = np.zeros(new_feature_length)
            self.feature_buffer = np.zeros(
                [new_feature_length, self.config.slot.embChannels]
            )

        convert_size = input_size + crossfade_size + sola_search_frame + extra_frame
        if convert_size % 160 != 0:
            convert_size += 160 - (convert_size % 160)
        out_size = int(
            ((convert_size - extra_frame) / 16000)
            * self.config.slot.samplingRate
        )

        if self.audio_buffer.shape[0] < convert_size:
            self.audio_buffer = np.concatenate(
                [np.zeros([convert_size]), self.audio_buffer]
            )
            if self.config.slot.f0:
                self.pitchf_buffer = np.concatenate(
                    [np.zeros([convert_size // 160]), self.pitchf_buffer]
                )
            self.feature_buffer = np.concatenate(
                [
                    np.zeros(
                        [convert_size // 160, self.config.slot.embChannels]
                    ),
                    self.feature_buffer,
                ]
            )

        convert_offset = -convert_size
        feature_offset = convert_offset // 160
        self.audio_buffer = self.audio_buffer[convert_offset:]
        if self.config.slot.f0:
            self.pitchf_buffer = self.pitchf_buffer[feature_offset:]
        self.feature_buffer = self.feature_buffer[feature_offset:]

        crop_offset = -(input_size + crossfade_size)
        crop_end = -crossfade_size
        crop = self.audio_buffer[crop_offset:crop_end]
        vol = np.sqrt(np.square(crop).mean())
        self.prev_vol = max(vol, self.prev_vol * 0.0)
        return (
            self.audio_buffer,
            self.pitchf_buffer,
            self.feature_buffer,
            convert_size,
            self.prev_vol,
            out_size,
        )

    def infer(self, request: RvcInferenceRequest) -> np.ndarray:
        started = perf_counter()
        try:
            return self._infer(request)
        finally:
            self.metrics.record((perf_counter() - started) * 1000.0)

    def _infer(self, request: RvcInferenceRequest) -> np.ndarray:
        if not self._ready or self.pipeline is None:
            raise PipelineNotInitializedException()

        received_data = cast(
            np.ndarray,
            resampy.resample(
                request.audio,
                request.input_sample_rate,
                16000,
                filter="kaiser_fast",
            ),
        )
        crossfade_frame = int(
            request.crossfade_frame / request.input_sample_rate * 16000
        )
        sola_search_frame = int(
            request.sola_search_frame / request.input_sample_rate * 16000
        )
        extra_frame = int(
            self.settings.extraConvertSize
            / request.input_sample_rate
            * 16000
        )
        data = self._generate_input(
            received_data, crossfade_frame, sola_search_frame, extra_frame
        )
        audio, pitchf, feature, convert_size, vol, out_size = data
        if vol < self.settings.silentThreshold:
            return np.zeros(convert_size).astype(np.int16) * np.sqrt(vol)

        audio_tensor = torch.from_numpy(audio).to(
            device=self.pipeline.device, dtype=torch.float32
        )
        repeat = 1 if self.settings.rvcQuality else 0
        try:
            audio_out, self.pitchf_buffer, self.feature_buffer = self.pipeline.exec(
                self.settings.dstId,
                audio_tensor,
                pitchf,
                feature,
                self.settings.tran,
                self.settings.indexRatio,
                1 if self.config.slot.f0 else 0,
                (
                    self.settings.extraConvertSize
                    / request.input_sample_rate
                    if self.settings.silenceFront
                    else 0.0
                ),
                self.config.slot.embOutputLayer,
                self.config.slot.useFinalProj,
                repeat,
                self.settings.protect,
                out_size,
            )
            result = audio_out[-out_size:].detach().cpu().numpy() * np.sqrt(vol)
            return cast(
                np.ndarray,
                resampy.resample(
                    result,
                    self.config.slot.samplingRate,
                    request.output_sample_rate,
                    filter="kaiser_fast",
                ),
            )
        except DeviceCannotSupportHalfPrecisionException:
            logger.warning(
                "[Voice Changer][RVC Backend] Legacy half precision failed; retrying fp32"
            )
            self.device_manager.setForceTensor(True)
            self.load_model()
            return np.zeros(convert_size, dtype=np.int16)

    def get_model_info(self) -> dict[str, Any]:
        pipeline_info = (
            self.pipeline.getPipelineInfo() if self.pipeline is not None else {}
        )
        device = str(self.pipeline.device) if self.pipeline is not None else None
        return {
            **pipeline_info,
            **self.metrics.snapshot(),
            **(
                cuda_memory_snapshot(self.pipeline.device)
                if self.pipeline is not None
                else cuda_memory_snapshot(torch.device("cpu"))
            ),
            "backend": self.name,
            "ready": self._ready,
            "device": device,
        }

    def reset_metrics(self) -> None:
        self.metrics.reset()

    def close(self) -> None:
        self.unload_model()
