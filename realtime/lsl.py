"""Lab Streaming Layer adapters for the project Stream contract."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from threading import Thread

import numpy as np
from numpy.typing import NDArray
from pylsl import (  # type: ignore[import-untyped]
    StreamInfo,
    StreamInlet,
    StreamOutlet,
    cf_float32,
    local_clock,
    resolve_byprop,
)

FloatArray = NDArray[np.float32]


def make_eeg_outlet(
    channel_names: tuple[str, ...],
    sampling_rate_hz: float,
    *,
    name: str = "ThinkingInterfacesReplay",
) -> StreamOutlet:
    if not channel_names or sampling_rate_hz <= 0:
        raise ValueError("channel names and a positive sampling rate are required")
    info = StreamInfo(
        name,
        "EEG",
        len(channel_names),
        sampling_rate_hz,
        cf_float32,
        f"thinking-interfaces-{uuid.uuid4()}",
    )
    channels = info.desc().append_child("channels")
    for label in channel_names:
        channel = channels.append_child("channel")
        channel.append_child_value("label", label)
        channel.append_child_value("unit", "volts")
        channel.append_child_value("type", "EEG")
    return StreamOutlet(info, chunk_size=0, max_buffered=60)


class LSLInletStream:
    def __init__(self, inlet: StreamInlet, channel_names: tuple[str, ...], rate: float) -> None:
        self._inlet = inlet
        self._channel_names = channel_names
        self._sampling_rate_hz = rate

    @classmethod
    def resolve(cls, name: str, *, timeout_s: float = 5.0) -> LSLInletStream:
        streams = resolve_byprop("name", name, minimum=1, timeout=timeout_s)
        if not streams:
            raise TimeoutError(f"no LSL stream named {name!r} was found")
        info = streams[0]
        inlet = StreamInlet(info, max_buflen=60, max_chunklen=0, recover=True)
        # Discovery responses can omit the extended channel description.
        info = inlet.info(timeout=timeout_s)
        labels: list[str] = []
        channel = info.desc().child("channels").child("channel")
        for _ in range(info.channel_count()):
            labels.append(channel.child_value("label"))
            channel = channel.next_sibling()
        if not all(labels) or len(set(labels)) != len(labels):
            inlet.close_stream()
            raise ValueError("LSL stream is missing unique named-channel metadata")
        return cls(inlet, tuple(labels), float(info.nominal_srate()))

    @property
    def sampling_rate_hz(self) -> float:
        return self._sampling_rate_hz

    @property
    def channel_names(self) -> tuple[str, ...]:
        return self._channel_names

    def read(self, max_samples: int) -> FloatArray:
        if max_samples < 1:
            raise ValueError("max_samples must be positive")
        samples, _ = self._inlet.pull_chunk(timeout=1.0, max_samples=max_samples)
        if not samples:
            return np.empty((len(self.channel_names), 0), dtype=np.float32)
        return np.asarray(samples, dtype=np.float32).T

    def close(self) -> None:
        self._inlet.close_stream()


@dataclass(frozen=True, slots=True)
class LSLLoopbackResult:
    sent_samples: int
    received_samples: int
    expected_duration_s: float
    wall_duration_s: float
    drift_s: float


def _replay_worker(outlet: StreamOutlet, signal: FloatArray, rate: float) -> None:
    start = local_clock() + 0.25
    for index in range(signal.shape[1]):
        deadline = start + index / rate
        remaining = deadline - local_clock()
        if remaining > 0:
            time.sleep(remaining)
        outlet.push_sample(signal[:, index].tolist(), deadline, pushthrough=True)


def run_lsl_loopback(
    signal: FloatArray,
    channel_names: tuple[str, ...],
    sampling_rate_hz: float,
    *,
    timeout_s: float = 10.0,
) -> LSLLoopbackResult:
    """Replay a complete array at nominal rate and verify no samples are lost."""

    if signal.ndim != 2 or signal.shape[0] != len(channel_names):
        raise ValueError("signal and channel names are incompatible")
    name = f"ThinkingInterfaces-{uuid.uuid4()}"
    outlet = make_eeg_outlet(channel_names, sampling_rate_hz, name=name)
    inlet = LSLInletStream.resolve(name, timeout_s=timeout_s)
    received: list[FloatArray] = []
    worker = Thread(target=_replay_worker, args=(outlet, signal, sampling_rate_hz), daemon=True)
    started = time.perf_counter()
    worker.start()
    deadline = started + timeout_s + signal.shape[1] / sampling_rate_hz
    count = 0
    while count < signal.shape[1] and time.perf_counter() < deadline:
        chunk = inlet.read(signal.shape[1] - count)
        if chunk.shape[1]:
            received.append(chunk)
            count += chunk.shape[1]
    worker.join(timeout=1.0)
    wall = time.perf_counter() - started
    if count != signal.shape[1]:
        raise RuntimeError(f"LSL sample loss: sent {signal.shape[1]}, received {count}")
    reconstructed = np.concatenate(received, axis=1)
    if not np.allclose(reconstructed, signal, rtol=0.0, atol=1e-6):
        raise RuntimeError("LSL loopback altered sample values")
    expected = (signal.shape[1] - 1) / sampling_rate_hz
    return LSLLoopbackResult(signal.shape[1], count, expected, wall, wall - expected)
