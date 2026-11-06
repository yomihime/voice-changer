import base64
import numpy as np
import logging
import threading
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from voice_changer.VoiceChangerManager import VoiceChangerManager, AudioStreamBusyError
from pydantic import BaseModel, Field


class VoiceModel(BaseModel):
    timestamp: int
    buffer: str = Field(max_length=640000)
    stream_epoch: str | None = Field(default=None, max_length=64)
    sequence: int | None = Field(default=None, ge=0, le=9007199254740991)


class MMVC_Rest_VoiceChanger:
    def __init__(self, voiceChangerManager: VoiceChangerManager):
        self.voiceChangerManager = voiceChangerManager
        self.router = APIRouter()
        self.router.add_api_route("/test", self.test, methods=["POST"])
        self.router.add_api_route("/reset_audio", self.reset_audio, methods=["POST"])

        self.tlock = threading.Lock()
        self.stream_epoch = uuid4().hex
        self.last_sequence = -1

    @staticmethod
    def error(status, code, reason):
        return JSONResponse(status_code=status, content={"error": {"code": code, "reason": reason}})

    def server_device_running(self):
        device = self.voiceChangerManager.serverDevice
        return (device.settings.serverAudioStated == 1 or bool(device._active_streams)
            or bool(getattr(device, '_device_owns_audio', False)))

    def reset_audio(self):
        with self.tlock:
            if self.server_device_running():
                return self.error(409, 'busy', 'Server Device owns the audio stream')
            try:
                self.voiceChangerManager.reset_audio_stream(strict=True)
            except ValueError as error:
                return self.error(409, 'unsupported', str(error))
            except Exception:
                logging.getLogger(__name__).exception('Audio stream reset failed')
                return self.error(500, 'failed', 'Audio stream reset failed')
            self.stream_epoch = uuid4().hex
            self.last_sequence = -1
            return {"stream_epoch": self.stream_epoch}

    def test(self, voice: VoiceModel):
        try:
            wav = base64.b64decode(voice.buffer, validate=True)
            if not wav or len(wav) % 2 or len(wav) > 480000:
                return self.error(400, 'invalid_audio', 'Expected bounded mono little-endian Int16 PCM')
            samples = np.frombuffer(wav, dtype='<i2').copy()
        except (ValueError, TypeError):
            return self.error(400, 'invalid_audio', 'Invalid base64 audio')
        with self.tlock:
            if self.server_device_running():
                return self.error(409, 'busy', 'Server Device owns the audio stream')
            if voice.stream_epoch is not None:
                if voice.stream_epoch != self.stream_epoch or voice.sequence is None or voice.sequence <= self.last_sequence:
                    return self.error(409, 'stale_session', 'The audio epoch or sequence is stale')
                self.last_sequence = voice.sequence
            try:
                changed_voice, _performance = self.voiceChangerManager.changeVoice(samples)
                changed_voice = np.asarray(changed_voice, dtype='<i2')
                if changed_voice.ndim != 1 or changed_voice.size <= 1:
                    return self.error(409, 'model_unavailable', 'The engine did not emit a valid audio block')
                if changed_voice.size > 240000:
                    return self.error(500, 'invalid_audio_response', 'The engine emitted an oversized audio block')
                data = {"timestamp": voice.timestamp,
                    "changedVoiceBase64": base64.b64encode(changed_voice.tobytes()).decode('ascii')}
                if voice.stream_epoch is not None:
                    data.update(stream_epoch=self.stream_epoch, sequence=voice.sequence)
                return JSONResponse(content=data)
            except AudioStreamBusyError:
                return self.error(409, 'busy', 'Server Device owns the audio stream')
            except Exception:
                logging.getLogger(__name__).exception('Audio conversion failed')
                return self.error(500, 'failed', 'Audio conversion failed')
