"""RVC model host for VoiceChangerV2.

The host owns VCClient-facing settings while inference details live behind the
RVC backend boundary.
"""

from dataclasses import asdict, replace
from threading import RLock
from data.ModelSlot import RVCModelSlot
from mods.log_control import VoiceChangaerLogger
from voice_changer.RVC.RVCSettings import RVCSettings
from voice_changer.RVC.backend.base import RvcBackendConfig, RvcInferenceRequest
from voice_changer.RVC.backend.exceptions import RvcBackendError
from voice_changer.RVC.backend.factory import create_rvc_backend
from voice_changer.utils.VoiceChangerModel import AudioInOut, VoiceChangerModel
from voice_changer.utils.VoiceChangerParams import VoiceChangerParams

logger = VoiceChangaerLogger.get_instance().getLogger()


class RVCr2(VoiceChangerModel):
    def __init__(self, params: VoiceChangerParams, slotInfo: RVCModelSlot):
        logger.info("[Voice Changer][RVC] Creating backend host")
        self.voiceChangerType = "RVC"
        self.params = params
        self.slotInfo = slotInfo
        self.settings = RVCSettings()
        self.settings.tran = slotInfo.defaultTune
        self.settings.indexRatio = slotInfo.defaultIndexRatio
        self.settings.protect = slotInfo.defaultProtect
        self.inputSampleRate = 48000
        self.outputSampleRate = 48000
        self._lifecycle_lock = RLock()
        self.backend = self._create_backend(self.settings.rvcBackend)
        self.lastBackendError: str | None = None

    def _create_backend(self, kind: str, settings: RVCSettings | None = None):
        return create_rvc_backend(
            kind,
            RvcBackendConfig(
                params=self.params,
                slot=self.slotInfo,
                settings=settings or self.settings,
            ),
        )

    def _prepare_backend(self, backend) -> None:
        backend.load_model()
        backend.set_sampling_rate(self.inputSampleRate, self.outputSampleRate)
        backend.warmup()

    def initialize(self) -> bool:
        with self._lifecycle_lock:
            return self._initialize_locked()

    def _initialize_locked(self) -> bool:
        logger.info(
            "[Voice Changer][RVC] Initializing backend=%s",
            self.settings.rvcBackend,
        )
        try:
            self._prepare_backend(self.backend)
            self.lastBackendError = None
            return True
        except Exception as exc:
            self.backend.close()
            self.lastBackendError = str(exc)
            logger.exception(
                "[Voice Changer][RVC] Backend initialization failed: %s", exc
            )
            return False

    @staticmethod
    def _map_f0_for_backend(settings: RVCSettings, kind: str) -> None:
        if kind == "official" and settings.f0Detector not in {
            "rmvpe",
            "fcpe",
            "pm",
        }:
            logger.info(
                "[Voice Changer][RVC] f0Detector %s is unavailable in Official; using rmvpe",
                settings.f0Detector,
            )
            settings.f0Detector = "rmvpe"
        elif kind == "legacy" and settings.f0Detector == "pm":
            logger.info(
                "[Voice Changer][RVC] f0Detector pm is unavailable in Legacy; using rmvpe"
            )
            settings.f0Detector = "rmvpe"

    def _replace_backend(self, kind: str, settings: RVCSettings) -> bool:
        previous = self.backend
        previous_kind = self.settings.rvcBackend
        previous_settings = self.settings
        previous_was_ready = previous.get_model_info().get("ready") is True
        previous.close()
        candidate = self._create_backend(kind, settings)
        try:
            self._prepare_backend(candidate)
        except Exception as exc:
            candidate.close()
            logger.exception(
                "[Voice Changer][RVC] Backend replacement failed: %s", exc
            )
            if previous_was_ready:
                recovery = self._create_backend(previous_kind, previous_settings)
                try:
                    self._prepare_backend(recovery)
                    self.backend = recovery
                except Exception as recovery_exc:
                    recovery.close()
                    self.backend = recovery
                    self.lastBackendError = (
                        f"{exc}; previous backend recovery failed: {recovery_exc}"
                    )
                    logger.exception(
                        "[Voice Changer][RVC] Previous backend recovery failed: %s",
                        recovery_exc,
                    )
                    return False
            else:
                self.backend = previous
            self.lastBackendError = str(exc)
            return False

        self.backend = candidate
        self.settings = settings
        self.lastBackendError = None
        return True

    def _switch_backend(self, kind: str) -> bool:
        if kind == self.settings.rvcBackend and self.backend.name == kind:
            if self.backend.get_model_info().get("ready"):
                return True
            return self._initialize_locked()
        candidate_settings = replace(self.settings, rvcBackend=kind)
        self._map_f0_for_backend(candidate_settings, kind)
        return self._replace_backend(kind, candidate_settings)

    def setSamplingRate(self, inputSampleRate, outputSampleRate):
        with self._lifecycle_lock:
            self.inputSampleRate = inputSampleRate
            self.outputSampleRate = outputSampleRate
            self.backend.set_sampling_rate(inputSampleRate, outputSampleRate)

    def update_settings(self, key: str, val: int | float | str):
        with self._lifecycle_lock:
            logger.info("[Voice Changer][RVC] update_settings %s:%s", key, val)
            if key == "resetRvcBackendMetrics":
                self.backend.reset_metrics()
                return True
            if key == "rvcBackend":
                kind = str(val).lower()
                if kind not in {"legacy", "official"}:
                    return False
                return self._switch_backend(kind)

            if key in self.settings.intData:
                value: int | float | str = int(val)
            elif key in self.settings.floatData:
                value = float(val)
            elif key in self.settings.strData:
                value = str(val)
            else:
                return False

            if not self.backend.supports_setting(key):
                self.lastBackendError = (
                    f"{self.backend.name} backend does not support setting {key}"
                )
                return False

            old_value = getattr(self.settings, key)
            if key == "gpu":
                if value == old_value and self.backend.get_model_info().get("ready"):
                    return True
                candidate_settings = replace(self.settings, gpu=int(value))
                return self._replace_backend(
                    self.settings.rvcBackend, candidate_settings
                )

            setattr(self.settings, key, value)
            try:
                self.backend.update_settings(key, value)
                self.lastBackendError = None
            except RvcBackendError as exc:
                setattr(self.settings, key, old_value)
                try:
                    self.backend.update_settings(key, old_value)
                except Exception:
                    self.backend.close()
                    logger.exception(
                        "[Voice Changer][RVC] Setting rollback failed"
                    )
                self.lastBackendError = str(exc)
                logger.exception("[Voice Changer][RVC] Setting update failed: %s", exc)
                return False
            return True

    def get_info(self):
        with self._lifecycle_lock:
            data = asdict(self.settings)
            data["pipelineInfo"] = self.backend.get_model_info()
            data["backendError"] = self.lastBackendError
            return data

    def get_processing_sampling_rate(self):
        return self.slotInfo.samplingRate

    def inference(
        self,
        receivedData: AudioInOut,
        crossfade_frame: int,
        sola_search_frame: int,
    ):
        with self._lifecycle_lock:
            return self.backend.infer(
                RvcInferenceRequest(
                    audio=receivedData,
                    crossfade_frame=crossfade_frame,
                    sola_search_frame=sola_search_frame,
                    input_sample_rate=self.inputSampleRate,
                    output_sample_rate=self.outputSampleRate,
                )
            )

    def __del__(self):
        backend = getattr(self, "backend", None)
        if backend is not None:
            backend.close()

    def export2onnx(self):
        with self._lifecycle_lock:
            if self.settings.rvcBackend != "legacy":
                return {
                    "status": "ng",
                    "path": "",
                    "msg": "ONNX export is available only with the Legacy backend",
                }
            if self.slotInfo.isONNX:
                logger.warning("[Voice Changer][RVC] No PyTorch model for export")
                return {"status": "ng", "path": ""}

            self.backend.unload_model()
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self._initialize_locked()
            from voice_changer.RVC.onnxExporter.export2onnx import export2onnx

            output_file_simple = export2onnx(self.settings.gpu, self.slotInfo)
            return {
                "status": "ok",
                "path": f"/tmp/{output_file_simple}",
                "filename": output_file_simple,
            }

    def get_model_current(self):
        return [
            {"key": "defaultTune", "val": self.settings.tran},
            {"key": "defaultIndexRatio", "val": self.settings.indexRatio},
            {"key": "defaultProtect", "val": self.settings.protect},
        ]
