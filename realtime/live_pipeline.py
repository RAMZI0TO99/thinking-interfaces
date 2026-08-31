"""Finite live streams: temporary empty reads are not end-of-recording markers."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from core.contracts import Stream
from evaluation.latency import LatencyRecorder, LatencySummary
from realtime.accumulated_evidence import AccumulatedEvidence
from realtime.confidence_gate import confidence_gate
from realtime.interface import GateDrivenInterface, InterfaceFrame
from realtime.pipeline import ProbabilityDecoder
from realtime.streaming import CausalRingBuffer


@dataclass(frozen=True, slots=True)
class LivePipelineResult:
    frames: tuple[InterfaceFrame, ...]
    received_samples: int
    received_sample_sha256: str
    wall_seconds: float
    processing_latency: LatencySummary


def run_live_pipeline(
    stream: Stream,
    decoder: ProbabilityDecoder,
    class_labels: tuple[str, ...],
    interface: GateDrivenInterface,
    *,
    total_samples: int,
    window_samples: int,
    stride_samples: int,
    chunk_samples: int,
    confidence_threshold: float,
    required_consecutive: int,
    timeout_s: float,
    on_frame: Callable[[int, int, InterfaceFrame], None],
) -> LivePipelineResult:
    if min(total_samples, window_samples, stride_samples, chunk_samples) < 1:
        raise ValueError("stream and window sizes must be positive")
    if total_samples < window_samples or timeout_s <= 0:
        raise ValueError("one complete window and a positive timeout are required")
    buffer = CausalRingBuffer(len(stream.channel_names), window_samples)
    accumulator = AccumulatedEvidence(required_consecutive=required_consecutive)
    latency = LatencyRecorder()
    digest = hashlib.sha256()
    frames: list[InterfaceFrame] = []
    received, next_end = 0, window_samples
    started = time.perf_counter()
    while received < total_samples:
        if time.perf_counter() - started > timeout_s:
            raise TimeoutError(f"live replay stopped at {received}/{total_samples} samples")
        request = min(chunk_samples, next_end - received, total_samples - received)
        chunk = np.asarray(stream.read(request), dtype=np.float32)
        if chunk.ndim != 2 or chunk.shape[0] != len(stream.channel_names):
            raise ValueError("live stream returned an invalid channel shape")
        if chunk.shape[1] > request or not np.isfinite(chunk).all():
            raise ValueError("live stream returned excess or non-finite samples")
        if chunk.shape[1] == 0:
            continue
        digest.update(np.ascontiguousarray(chunk.T).tobytes())
        buffer.append(chunk)
        received += chunk.shape[1]
        if received == next_end:
            processing_started = time.perf_counter()
            probabilities = np.asarray(decoder.predict_proba(buffer.latest(window_samples)[None]))
            if probabilities.shape != (1, len(class_labels)):
                raise ValueError("decoder returned an invalid probability shape")
            decision = confidence_gate(
                probabilities[0], class_labels, threshold=confidence_threshold
            )
            evidence = accumulator.update(decision)
            elapsed = time.perf_counter() - processing_started
            frame = interface.update(decision, evidence, latency_ms=elapsed * 1000)
            latency.add_seconds(elapsed)
            frames.append(frame)
            on_frame(len(frames) - 1, received, frame)
            next_end += stride_samples
    return LivePipelineResult(
        tuple(frames),
        received,
        digest.hexdigest(),
        time.perf_counter() - started,
        latency.summarize(),
    )
