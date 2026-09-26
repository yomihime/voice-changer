"""Input clock regressions independent of RVC model loading and Torch."""

import unittest

import numpy as np
import resampy

from voice_changer.RVC.backend.input_stream import OfficialInputStream


class OfficialInputStreamTest(unittest.TestCase):
    def test_input_resampling_matches_one_continuous_waveform(self):
        for rate in (44100, 48000):
            with self.subTest(rate=rate):
                stream = OfficialInputStream()
                count = 50000
                t = np.arange(count) / rate
                waveform = (0.3 * np.sin(2 * np.pi * (117 * t + 300 * t * t))).astype(np.float32)
                waveform[15000:25000] = 0
                expected = resampy.resample(waveform, rate, 16000, filter="kaiser_fast")
                pieces, start = [], 0
                for size in (4097, 4001, 6003, 4999, 4097, 4001, 6003, 10000, 6799):
                    part = waveform[start:start + size]
                    pieces.append(stream.push(part * 32768.0, rate))
                    self.assertEqual(len(pieces[-1]) % 160, 0)
                    start += len(part)
                actual = np.concatenate(pieces)
                available = (count - rate // 100) * 16000 // rate
                self.assertEqual(len(actual), available // 160 * 160)
                self.assertEqual(stream.source_samples_total, count)
                np.testing.assert_allclose(actual, expected[:len(actual)], atol=2e-6, rtol=0)

    def test_one_frame_lookahead_at_every_supported_rate(self):
        for rate in (16000, 24000, 32000, 40000, 44100, 48000, 88200, 96000):
            with self.subTest(rate=rate):
                stream = OfficialInputStream()
                block = np.zeros(rate // 100, np.int16)
                self.assertEqual(len(stream.push(block, rate)), 0)
                self.assertEqual(len(stream.push(block, rate)), 160)
                self.assertEqual(len(stream.push(block, rate)), 160)
                self.assertEqual(stream.source_samples_total, 3 * len(block))


if __name__ == "__main__":
    unittest.main()
