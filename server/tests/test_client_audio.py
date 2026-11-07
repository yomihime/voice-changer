import base64
import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from restapi.MMVC_Rest_VoiceChanger import MMVC_Rest_VoiceChanger, VoiceModel
from voice_changer.Local.ServerDevice import ServerDevice
from voice_changer.VoiceChangerV2 import VoiceChangerV2
from voice_changer.RVC.RVCr2 import RVCr2
from voice_changer.RVC.backend.legacy import LegacyRvcBackend
from voice_changer.VoiceChangerManager import VoiceChangerManager, VoiceChangerManagerSettings, AudioStreamBusyError


class AudioEpochTest(unittest.TestCase):
    def setUp(self):
        self.manager = SimpleNamespace(serverDevice=SimpleNamespace(
            settings=SimpleNamespace(serverAudioStated=0), _active_streams=()),
            reset_audio_stream=Mock(), changeVoice=Mock(side_effect=lambda samples: (samples, [])))
        self.api = MMVC_Rest_VoiceChanger(self.manager)
        self.pcm = base64.b64encode(np.arange(128, dtype='<i2').tobytes()).decode('ascii')

    def frame(self, epoch=None, sequence=None, buffer=None):
        return VoiceModel(timestamp=7, buffer=self.pcm if buffer is None else buffer,
            stream_epoch=epoch, sequence=sequence)

    def test_reset_and_sequence_reject_old_frames_without_inference(self):
        old_epoch = self.api.stream_epoch
        epoch = self.api.reset_audio()['stream_epoch']
        self.assertNotEqual(epoch, old_epoch)
        self.assertEqual(self.api.test(self.frame(old_epoch, 0)).status_code, 409)
        self.manager.changeVoice.assert_not_called()
        result = self.api.test(self.frame(epoch, 0))
        data = json.loads(result.body)
        self.assertEqual(data['stream_epoch'], epoch)
        self.assertEqual(data['sequence'], 0)
        self.assertEqual(data['changedVoiceBase64'], self.pcm)
        self.assertEqual(self.api.test(self.frame(epoch, 0)).status_code, 409)
        self.assertEqual(self.manager.changeVoice.call_count, 1)

    def test_invalid_audio_and_engine_sentinel_are_errors_without_poisoning_lock(self):
        self.assertEqual(self.api.test(self.frame(buffer='bad!')).status_code, 400)
        self.assertEqual(self.api.test(self.frame()).status_code, 200)
        self.manager.changeVoice.return_value = (np.zeros(1, dtype=np.int16), [])
        self.manager.changeVoice.side_effect = None
        result = self.api.test(self.frame())
        self.assertEqual(json.loads(result.body)['error']['code'], 'model_unavailable')
        self.manager.changeVoice.side_effect = RuntimeError('owned fixture')
        self.assertEqual(self.api.test(self.frame()).status_code, 500)
        self.assertTrue(self.api.tlock.acquire(blocking=False))
        self.api.tlock.release()

    def test_server_device_owns_its_stream_and_cannot_be_reset_by_client(self):
        self.manager.serverDevice.settings.serverAudioStated = 1
        self.assertEqual(self.api.reset_audio().status_code, 409)
        self.assertEqual(self.api.test(self.frame(self.api.stream_epoch, 0)).status_code, 409)
        self.assertEqual(self.api.test(self.frame()).status_code, 409)
        self.manager.reset_audio_stream.assert_not_called()
        self.manager.changeVoice.assert_not_called()

    def test_reset_waits_for_inflight_frame_and_clears_after_it(self):
        entered, release = threading.Event(), threading.Event()
        def convert(samples):
            entered.set()
            self.assertTrue(release.wait(2))
            return samples, []
        self.manager.changeVoice.side_effect = convert
        with ThreadPoolExecutor(max_workers=2) as pool:
            frame = pool.submit(self.api.test, self.frame(self.api.stream_epoch, 0))
            self.assertTrue(entered.wait(2))
            reset = pool.submit(self.api.reset_audio)
            self.assertFalse(reset.done())
            release.set()
            self.assertEqual(frame.result(timeout=2).status_code, 200)
            self.assertIn('stream_epoch', reset.result(timeout=2))
        self.manager.reset_audio_stream.assert_called_once()


class ServerQueueTest(unittest.TestCase):
    def setUp(self):
        self.callbacks = SimpleNamespace(reset_audio_stream=Mock())
        self.device = ServerDevice(self.callbacks)

    def test_queues_are_bounded_and_play_the_latest_block(self):
        for value in range(100):
            self.device._queue_latest(self.device.outQueue, np.full(128, value, dtype=np.int16))
        self.assertLessEqual(self.device.outQueue.qsize(), 2)
        self.assertEqual(self.device._queue_drop_count, 98)
        output = np.ones((128, 2), dtype=np.float32)
        self.device.audioOutput_callback(output, 128, None, None)
        np.testing.assert_array_equal(output, np.full((128, 2), 99 / 32768, dtype=np.float32))
        self.device.audioOutput_callback(output, 128, None, None)
        self.assertFalse(np.any(output))

    def test_restart_clears_both_outputs_and_resets_model_history(self):
        self.device._queue_latest(self.device.outQueue, np.ones(128))
        self.device._queue_latest(self.device.monQueue, np.ones(128))
        self.device._prepare_streams()
        self.assertTrue(self.device.outQueue.empty())
        self.assertTrue(self.device.monQueue.empty())
        self.callbacks.reset_audio_stream.assert_called_once()

    def test_reset_discards_host_and_legacy_model_context(self):
        backend = LegacyRvcBackend.__new__(LegacyRvcBackend)
        backend.audio_buffer = backend.pitchf_buffer = backend.feature_buffer = np.ones(128)
        backend.prev_vol = 1
        model = RVCr2.__new__(RVCr2)
        model._lifecycle_lock = threading.RLock()
        model._stream_generation = 0
        model.backend = backend
        host = VoiceChangerV2.__new__(VoiceChangerV2)
        host._processing_lock = threading.RLock()
        host.voiceChanger = model
        host.sola_buffer = host.np_prev_audio1 = np.ones(128)
        host.reset_stream()
        self.assertIsNone(backend.audio_buffer)
        self.assertIsNone(backend.pitchf_buffer)
        self.assertIsNone(backend.feature_buffer)
        self.assertFalse(hasattr(host, 'sola_buffer'))
        self.assertFalse(hasattr(host, 'np_prev_audio1'))
        self.assertEqual(model._stream_generation, 1)

    def test_device_owner_remains_held_until_every_stream_context_exits(self):
        for method, arguments in [
            ('runNoMonitorSeparate', (128, 1, 2, None, None)),
            ('runWithMonitorStandard', (128, 1, 2, 2, None, None, None)),
            ('runWithMonitorAllSeparate', (128, 1, 2, 2, None, None, None)),
        ]:
            with self.subTest(method=method):
                device = ServerDevice(self.callbacks)
                device.settings.serverAudioStated = 1
                manager = SimpleNamespace(serverDevice=device, reset_audio_stream=Mock(), changeVoice=Mock())
                api = MMVC_Rest_VoiceChanger(manager)
                test = self
                class Stream:
                    active = False
                    def __enter__(self):
                        self.active = True
                        return self
                    def __exit__(self, *error):
                        self.active = False
                        test.assertTrue(device._device_owns_audio)
                        test.assertEqual(api.reset_audio().status_code, 409)
                def setting_changed():
                    device.settings.serverAudioStated = 0
                    return True
                device.checkSettingChanged = setting_changed
                with patch('voice_changer.Local.ServerDevice.sd.InputStream', side_effect=lambda **kwargs: Stream()), \
                     patch('voice_changer.Local.ServerDevice.sd.OutputStream', side_effect=lambda **kwargs: Stream()), \
                     patch('voice_changer.Local.ServerDevice.sd.Stream', side_effect=lambda **kwargs: Stream()):
                    getattr(device, method)(*arguments)
                self.assertFalse(device._device_owns_audio)
                self.assertIn('stream_epoch', api.reset_audio())

    def test_inactive_server_stream_exits_without_automatically_reopening_devices(self):
        device = self.device
        device.settings.serverAudioStated = 1
        self.callbacks.get_processing_sampling_rate = Mock(return_value=device.currentModelSamplingRate)
        device.currentInputChunkNum = device.settings.serverReadChunkSize
        device.currentAudioSampleRate = device.settings.serverAudioSampleRate
        input_stream = Mock(active=True)
        output_stream = Mock(active=False)

        with patch('voice_changer.Local.ServerDevice.sd.InputStream', return_value=nullcontext(input_stream)), \
             patch('voice_changer.Local.ServerDevice.sd.OutputStream', return_value=nullcontext(output_stream)):
            with self.assertRaisesRegex(RuntimeError, 'stopped unexpectedly'):
                device.runNoMonitorSeparate(128, 1, 2, None, None)
        self.assertEqual(device.settings.serverAudioStated, 0)
        self.assertFalse(device._device_owns_audio)
        self.assertEqual(device._active_streams, ())

    def test_missing_selected_device_stops_before_opening_any_stream(self):
        for missing in ('input', 'output', 'monitor'):
            with self.subTest(missing=missing):
                device = ServerDevice(self.callbacks)
                device.settings.serverAudioStated = 1
                device.settings.serverInputDeviceId = 11
                device.settings.serverOutputDeviceId = 12
                device.settings.serverMonitorDeviceId = 13
                device.settings.exclusiveMode = True
                present = SimpleNamespace(hostAPI='Windows WASAPI')
                device.getServerInputAudioDevice = Mock(return_value=None if missing == 'input' else present)
                device.getServerOutputAudioDevice = Mock(side_effect=[
                    None if missing == 'output' else present, None if missing == 'monitor' else present,
                ])
                with patch('voice_changer.Local.ServerDevice.sd') as audio, \
                     patch('voice_changer.Local.ServerDevice.time.sleep', side_effect=InterruptedError):
                    with self.assertRaises(InterruptedError):
                        device.start()
                audio.InputStream.assert_not_called()
                audio.OutputStream.assert_not_called()
                audio.Stream.assert_not_called()
                self.assertEqual(device.settings.serverAudioStated, 0)
                self.assertEqual(device._device_state, 'error')
                self.assertFalse(device._device_owns_audio)

    def test_older_hosts_keep_server_device_preparation_without_claiming_epoch_support(self):
        manager = VoiceChangerManager.__new__(VoiceChangerManager)
        for host in [SimpleNamespace(), SimpleNamespace(voiceChanger=SimpleNamespace(), reset_stream=Mock())]:
            manager.voiceChanger = host
            manager.reset_audio_stream()
            with self.assertRaises(ValueError):
                manager.reset_audio_stream(strict=True)
            device = ServerDevice(manager)
            device._prepare_streams()
            device._deactivate_streams()

    def test_manager_keeps_socketio_and_http_clients_out_of_server_owned_audio(self):
        manager = VoiceChangerManager.__new__(VoiceChangerManager)
        manager.serverDevice = SimpleNamespace(settings=SimpleNamespace(serverAudioStated=1), _active_streams=())
        manager.settings = VoiceChangerManagerSettings(passThrough=True)
        samples = np.zeros(128, dtype=np.int16)
        with self.assertRaises(AudioStreamBusyError):
            manager.changeVoice(samples)
        self.assertIs(manager.on_request(samples)[0], samples)


if __name__ == '__main__':
    unittest.main()
