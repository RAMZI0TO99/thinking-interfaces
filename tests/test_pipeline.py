from __future__ import annotations

import unittest

import numpy as np

from realtime.interface import GateDrivenInterface
from realtime.pipeline import run_replay_pipeline
from realtime.streaming import ArrayReplayStream


class FixedDecoder:
    def predict_proba(self, epochs: np.ndarray) -> np.ndarray:
        return np.tile(np.asarray([[0.1, 0.9]]), (epochs.shape[0], 1))


class ReplayPipelineTests(unittest.TestCase):
    def test_interface_receives_gate_and_evidence_outputs(self) -> None:
        signal = np.arange(12, dtype=np.float32).reshape(1, 12)
        stream = ArrayReplayStream(signal, ("Cz",), 4.0)
        interface = GateDrivenInterface(target="right")
        frames, latency = run_replay_pipeline(
            stream,
            FixedDecoder(),
            ("left", "right"),
            interface,
            window_samples=4,
            stride_samples=4,
            chunk_samples=2,
            confidence_threshold=0.7,
            required_consecutive=3,
        )
        self.assertEqual([frame.decision_state for frame in frames], ["right"] * 3)
        self.assertEqual(frames[-1].emitted_command, "right")
        self.assertEqual(latency.count, 3)
