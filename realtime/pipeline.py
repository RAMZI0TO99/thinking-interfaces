"""Replay-to-decision pipeline shared by console and desktop interfaces."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any, Protocol

import numpy as np

from evaluation.latency import LatencyRecorder, LatencySummary
from realtime.accumulated_evidence import AccumulatedEvidence
from realtime.confidence_gate import confidence_gate
from realtime.interface import GateDrivenInterface, InterfaceFrame
from realtime.streaming import ArrayReplayStream, replay_windows


class ProbabilityDecoder(Protocol):
    def predict_proba(self, epochs: Any) -> Any: ...


def run_replay_pipeline(
    stream: ArrayReplayStream,
    decoder: ProbabilityDecoder,
    class_labels: tuple[str, ...],
    interface: GateDrivenInterface,
    *,
    window_samples: int,
    stride_samples: int,
    chunk_samples: int,
    confidence_threshold: float,
    required_consecutive: int,
) -> tuple[tuple[InterfaceFrame, ...], LatencySummary]:
    """Causally window, classify, gate, accumulate, and update the interface."""

    accumulator = AccumulatedEvidence(required_consecutive=required_consecutive)
    latency = LatencyRecorder()
    frames: list[InterfaceFrame] = []
    for window in replay_windows(
        stream,
        window_samples=window_samples,
        stride_samples=stride_samples,
        chunk_samples=chunk_samples,
    ):
        started = time.perf_counter()
        probabilities = np.asarray(decoder.predict_proba(window.signal[None, ...]))
        elapsed = time.perf_counter() - started
        if probabilities.shape != (1, len(class_labels)):
            raise ValueError("decoder returned an invalid probability shape")
        decision = confidence_gate(
            probabilities[0], class_labels, threshold=confidence_threshold
        )
        evidence = accumulator.update(decision)
        latency.add_seconds(elapsed)
        frames.append(interface.update(decision, evidence, latency_ms=elapsed * 1000.0))
    if not frames:
        raise ValueError("replay produced no complete windows")
    return tuple(frames), latency.summarize()


def print_frames(frames: Sequence[InterfaceFrame]) -> None:
    for frame in frames:
        print(GateDrivenInterface.render_text(frame), flush=True)
