"""Causal in-memory replay, ring buffering, and window scheduling."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float32]


class ArrayReplayStream:
    """Expose a fixed channel-first recording through the Stream contract."""

    def __init__(
        self, signal: FloatArray, channel_names: tuple[str, ...], sampling_rate_hz: float
    ) -> None:
        if signal.ndim != 2 or signal.shape[0] != len(channel_names):
            raise ValueError("signal and channel_names are incompatible")
        if sampling_rate_hz <= 0:
            raise ValueError("sampling_rate_hz must be positive")
        self._signal = signal
        self._channel_names = channel_names
        self._sampling_rate_hz = sampling_rate_hz
        self._cursor = 0

    @property
    def sampling_rate_hz(self) -> float:
        return self._sampling_rate_hz

    @property
    def channel_names(self) -> tuple[str, ...]:
        return self._channel_names

    def read(self, max_samples: int) -> FloatArray:
        if max_samples < 1:
            raise ValueError("max_samples must be positive")
        stop = min(self._cursor + max_samples, self._signal.shape[1])
        chunk = self._signal[:, self._cursor:stop].copy()
        self._cursor = stop
        return chunk


class CausalRingBuffer:
    """Fixed-capacity buffer whose API cannot access unwritten future samples."""

    def __init__(self, channels: int, capacity_samples: int) -> None:
        if channels < 1 or capacity_samples < 1:
            raise ValueError("channels and capacity_samples must be positive")
        self._data = np.zeros((channels, capacity_samples), dtype=np.float32)
        self._capacity = capacity_samples
        self._written = 0

    @property
    def available_samples(self) -> int:
        return min(self._written, self._capacity)

    def append(self, chunk: FloatArray) -> None:
        if chunk.ndim != 2 or chunk.shape[0] != self._data.shape[0]:
            raise ValueError("chunk must have shape (configured channels, samples)")
        count = chunk.shape[1]
        if count == 0:
            return
        if count >= self._capacity:
            self._data[:] = chunk[:, -self._capacity :]
        else:
            retained = min(self.available_samples, self._capacity - count)
            if retained:
                start = self.available_samples - retained
                self._data[:, :retained] = self._data[:, start : self.available_samples].copy()
            self._data[:, retained : retained + count] = chunk
        self._written += count

    def latest(self, samples: int) -> FloatArray:
        if samples < 1 or samples > self.available_samples:
            raise ValueError("requested window is not currently available")
        return self._data[:, self.available_samples - samples : self.available_samples].copy()


@dataclass(frozen=True, slots=True)
class TimedWindow:
    sequence: int
    end_sample: int
    signal: FloatArray
    emitted_at_s: float


def replay_windows(
    stream: ArrayReplayStream,
    *,
    window_samples: int,
    stride_samples: int,
    chunk_samples: int,
) -> Iterator[TimedWindow]:
    """Yield each causal window exactly when enough samples have arrived."""

    if min(window_samples, stride_samples, chunk_samples) < 1:
        raise ValueError("window, stride, and chunk sizes must be positive")
    buffer = CausalRingBuffer(len(stream.channel_names), window_samples)
    received = 0
    next_end = window_samples
    sequence = 0
    while True:
        read_size = min(chunk_samples, next_end - received)
        chunk = stream.read(read_size)
        if chunk.shape[1] == 0:
            break
        buffer.append(chunk)
        received += chunk.shape[1]
        while received >= next_end:
            yield TimedWindow(
                sequence,
                next_end,
                buffer.latest(window_samples),
                time.perf_counter(),
            )
            sequence += 1
            next_end += stride_samples
