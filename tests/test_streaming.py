from __future__ import annotations

import unittest

import numpy as np

from evaluation.latency import LatencyRecorder
from realtime.streaming import ArrayReplayStream, CausalRingBuffer, replay_windows


class StreamingTests(unittest.TestCase):
    def test_ring_buffer_keeps_only_past_samples(self) -> None:
        buffer = CausalRingBuffer(1, 4)
        buffer.append(np.asarray([[1, 2, 3]], dtype=np.float32))
        np.testing.assert_array_equal(buffer.latest(2), [[2, 3]])
        buffer.append(np.asarray([[4, 5, 6]], dtype=np.float32))
        np.testing.assert_array_equal(buffer.latest(4), [[3, 4, 5, 6]])

    def test_replay_emits_expected_windows(self) -> None:
        signal = np.arange(8, dtype=np.float32).reshape(1, 8)
        stream = ArrayReplayStream(signal, ("Cz",), 4.0)
        windows = list(replay_windows(stream, window_samples=4, stride_samples=2, chunk_samples=2))
        self.assertEqual([window.end_sample for window in windows], [4, 6, 8])
        np.testing.assert_array_equal(windows[-1].signal, [[4, 5, 6, 7]])

    def test_chunks_larger_than_stride_do_not_skip_window_boundaries(self) -> None:
        signal = np.arange(10, dtype=np.float32).reshape(1, 10)
        stream = ArrayReplayStream(signal, ("Cz",), 4.0)
        windows = list(replay_windows(stream, window_samples=4, stride_samples=2, chunk_samples=7))
        self.assertEqual([window.end_sample for window in windows], [4, 6, 8, 10])
        np.testing.assert_array_equal(windows[1].signal, [[2, 3, 4, 5]])

    def test_latency_summary(self) -> None:
        recorder = LatencyRecorder()
        recorder.add_seconds(0.001)
        recorder.add_seconds(0.003)
        self.assertAlmostEqual(recorder.summarize().mean_ms, 2.0)
