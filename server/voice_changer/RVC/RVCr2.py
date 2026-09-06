"""RVC model host for VoiceChangerV2.

The host owns VCClient-facing settings while inference details live behind the
RVC backend boundary.
"""

from dataclasses import asdict
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
        self.backend = self._create_backend(self.settings.rvcBackend)
        self.lastBackendError: str | None = None

    def _create_backend(self, kind: str):
        return create_rvc_backend(
            kind,
            RvcBackendConfig(
                params=self.params,
                slot=self.slotInfo,
                settings=self.settings,
            ),
        )

    def initialize(self):
        logger.info(
            "[Voice Changer][RVC] Initializing backend=%s",
            self.settings.rvcBackend,
        )
        try:
            self.backend.load_model()
            self.backend.set_sampling_rate(
                self.inputSampleRate, self.outputSampleRate
            )
            self.backend.warmup()
            self.lastBackendError = None
        except Exception as exc:
            self.lastBackendError = str(exc)
            logger.exception(
                "[Voice Changer][RVC] Backend initialization failed: %s", exc
            )

    def _switch_backend(self, kind: str) -> None:
        if kind == self.settings.rvcBackend and self.backend.name == kind:
            return
        previous = self.backend
        previous.close()
        self.settings.rvcBackend = kind
        if kind == "official" and self.settings.f0Detector not in {
            "rmvpe",
            "fcpe",
            "pm",
        }:
            logger.info(
                "[Voice Changer][RVC] f0Detector %s is unavailable in Official; using rmvpe",
                self.settings.f0Detector,
            )
            self.settings.f0Detector = "rmvpe"
        elif kind == "legacy" and self.settings.f0Detector == "pm":
            logger.info(
                "[Voice Changer][RVC] f0Detector pm is unavailable in Legacy; using rmvpe"
            )
            self.settings.f0Detector = "rmvpe"
        self.backend = self._create_backend(kind)
        self.initialize()

    def setSamplingRate(self, inputSampleRate, outputSampleRate):
        self.inputSampleRate = inputSampleRate
        self.outputSampleRate = outputSampleRate
        self.backend.set_sampling_rate(inputSampleRate, outputSampleRate)

    def update_settings(self, key: str, val: int | float | str):
        logger.info("[Voice Changer][RVC] update_settings %s:%s", key, val)
        if key == "resetRvcBackendMetrics":
            self.backend.reset_metrics()
            return True
        if key == "rvcBackend":
            kind = str(val).lower()
            if kind not in {"legacy", "official"}:
                return False
            self._switch_backend(kind)
            return True

        if key in self.settings.intData:
            value: int | float | str = int(val)
        elif key in self.settings.floatData:
            value = float(val)
        elif key in self.settings.strData:
            value = str(val)
        else:
            return False

        old_value = getattr(self.settings, key)
        setattr(self.settings, key, value)
        try:
            self.backend.update_settings(key, value)
            self.lastBackendError = None
        except RvcBackendError as exc:
            setattr(self.settings, key, old_value)
            self.lastBackendError = str(exc)
            logger.exception("[Voice Changer][RVC] Setting update failed: %s", exc)
            return False
        return True

    def get_info(self):
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
        self.initialize()
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
