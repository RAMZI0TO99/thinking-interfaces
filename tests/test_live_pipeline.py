from __future__ import annotations

import hashlib
import unittest

import numpy as np

from realtime.interface import GateDrivenInterface
from realtime.live_pipeline import run_live_pipeline
from realtime.streaming import ArrayReplayStream


class IntermittentStream(ArrayReplayStream):
    empty_next = True

    def read(self, max_samples):
        self.empty_next = not self.empty_next
        if not self.empty_next:
            return np.empty((len(self.channel_names), 0), dtype=np.float32)
        return super().read(max_samples)


class RecordingDecoder:
    def __init__(self):
        self.windows = []

    def predict_proba(self, epochs):
        self.windows.append(epochs.copy())
        return np.asarray([[0.1, 0.9]], dtype=np.float32)


class LivePipelineTests(unittest.TestCase):
    def test_empty_reads_are_temporary_and_every_window_is_causal(self):
        signal = np.arange(20, dtype=np.float32).reshape(2, 10)
        stream = IntermittentStream(signal, ("C3", "C4"), 4.0)
        decoder = RecordingDecoder()
        updates = []
        result = run_live_pipeline(
            stream,
            decoder,
            ("left", "right"),
            GateDrivenInterface(target="right"),
            total_samples=10,
            window_samples=4,
            stride_samples=2,
            chunk_samples=7,
            confidence_threshold=0.7,
            required_consecutive=3,
            timeout_s=2,
            on_frame=lambda index, count, frame: updates.append((index, count, frame)),
        )
        self.assertEqual([count for _, count, _ in updates], [4, 6, 8, 10])
        self.assertEqual(result.received_samples, 10)
        self.assertEqual(
            result.received_sample_sha256, hashlib.sha256(signal.T.copy().tobytes()).hexdigest()
        )
        np.testing.assert_array_equal(decoder.windows[1][0], signal[:, 2:6])
        self.assertEqual(result.frames[2].emitted_command, "right")
        self.assertIsNone(result.frames[3].emitted_command)

    def test_missing_samples_fail_instead_of_claiming_complete(self):
        with self.assertRaises(TimeoutError):
            run_live_pipeline(
                ArrayReplayStream(np.zeros((1, 3), dtype=np.float32), ("Cz",), 4),
                RecordingDecoder(),
                ("left", "right"),
                GateDrivenInterface(target="right"),
                total_samples=4,
                window_samples=4,
                stride_samples=4,
                chunk_samples=4,
                confidence_threshold=0.7,
                required_consecutive=1,
                timeout_s=0.02,
                on_frame=lambda *_: None,
            )
