"""Experimental isolated eigensolver scheduling; not enabled in the benchmark."""

from __future__ import annotations

import importlib
import multiprocessing
import os
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np
from threadpoolctl import threadpool_info  # type: ignore[import-untyped]

_WORKER_MINIMUM_MEMORY = 4.0


def available_memory_gib() -> float:
    return float(importlib.import_module("psutil").virtual_memory().available / 1024**3)


def numpy_backend() -> dict[str, Any]:
    rows = [
        row
        for row in threadpool_info()
        if row["user_api"] == "blas"
        and "/numpy.libs/" in row["filepath"].replace("\\", "/").lower()
    ]
    if len(rows) != 1:
        raise RuntimeError("one identifiable NumPy BLAS backend is required")
    keys = ("filepath", "num_threads", "version", "architecture", "threading_layer")
    return {"numpy_version": np.__version__, **{key: rows[0][key] for key in keys}}


def _initialize_worker(expected_backend: dict[str, Any], minimum_memory: float) -> None:
    global _WORKER_MINIMUM_MEMORY
    if numpy_backend() != expected_backend:
        raise RuntimeError("worker NumPy/backend/thread settings differ from the parent")
    _WORKER_MINIMUM_MEMORY = minimum_memory


def _eigh_block(block: Any) -> tuple[Any, Any, int, float]:
    before = available_memory_gib()
    if before < _WORKER_MINIMUM_MEMORY:
        raise RuntimeError("isolated eigensolver stopped at memory guard")
    values, vectors = np.linalg.eigh(block)
    after = available_memory_gib()
    if after < _WORKER_MINIMUM_MEMORY:
        raise RuntimeError("isolated eigensolver stopped at memory guard")
    return values, vectors, os.getpid(), min(before, after)


class ProcessEighProbe:
    """Bound pending blocks; preserve original operations and fail on backend drift.

    Patches only the Array API NumPy facade, never numpy.linalg.eigh itself,
    so spawned workers call the unmodified, importable NumPy implementation.
    """

    def __init__(self, *, workers: int, chunk_matrices: int, minimum_memory_gib: float) -> None:
        if workers != 2 or type(workers) is not int:
            raise ValueError("this bounded probe requires exactly two worker processes")
        if chunk_matrices != 64 or type(chunk_matrices) is not int:
            raise ValueError("this bounded probe requires 64 matrices per block")
        if minimum_memory_gib != 4.0 or isinstance(minimum_memory_gib, bool):
            raise ValueError("the existing 4-GiB memory stop must be retained")
        self.workers = workers
        self.chunk_matrices = chunk_matrices
        self.minimum_memory_gib = minimum_memory_gib
        self.pool: Any = None
        self.original: Any = None
        self.result_type: Any = None
        self.patch: Any = None
        self.stats: dict[str, Any] = {
            "parallel_calls": 0,
            "fallback_calls": 0,
            "blocks": 0,
            "worker_pids": [],
            "maximum_pending_blocks": 0,
            "minimum_observed_free_memory_gib": None,
        }

    def __enter__(self) -> ProcessEighProbe:
        from unittest.mock import patch

        import array_api_compat.numpy as facade  # type: ignore[import-untyped]

        if self.pool is not None or facade.linalg is np.linalg:
            raise RuntimeError("a separate, unused Array API facade is required")
        backend = numpy_backend()
        if backend["num_threads"] != 24:
            raise RuntimeError("the original 24-thread NumPy backend must be preserved")
        if available_memory_gib() < self.minimum_memory_gib:
            raise RuntimeError("process probe deferred at memory guard")
        self.stats["verified_backend"] = backend
        self.original = facade.linalg.eigh
        self.result_type = type(self.original(np.eye(1)))
        self.pool = ProcessPoolExecutor(
            max_workers=self.workers,
            mp_context=multiprocessing.get_context("spawn"),
            initializer=_initialize_worker,
            initargs=(backend, self.minimum_memory_gib),
        )
        self.patch = patch.object(facade.linalg, "eigh", new=self)
        self.patch.start()
        return self

    def __exit__(self, *unused: Any) -> None:
        try:
            if self.patch is not None:
                self.patch.stop()
        finally:
            if self.pool is not None:
                self.pool.shutdown(wait=True, cancel_futures=True)
            self.pool = None

    def __call__(self, value: Any, **keywords: Any) -> Any:
        if self.pool is None:
            raise RuntimeError("the process probe is not active")
        available = available_memory_gib()
        if available < self.minimum_memory_gib:
            raise RuntimeError("process probe stopped at memory guard")
        observed = self.stats["minimum_observed_free_memory_gib"]
        self.stats["minimum_observed_free_memory_gib"] = (
            available if observed is None else min(observed, available)
        )
        if (
            type(value) is not np.ndarray
            or value.dtype != np.float64
            or value.ndim != 3
            or value.shape[1:] != (64, 64)
            or len(value) < self.chunk_matrices
            or not value.flags.c_contiguous
            or keywords
        ):
            self.stats["fallback_calls"] += 1
            return self.original(value, **keywords)
        self.stats["parallel_calls"] += 1
        values = np.empty(value.shape[:2], dtype=value.dtype)
        vectors = np.empty(value.shape, dtype=value.dtype)
        starts = iter(range(0, len(value), self.chunk_matrices))
        pending: deque[Any] = deque()

        def submit() -> None:
            start = next(starts, None)
            if start is not None:
                stop = min(start + self.chunk_matrices, len(value))
                pending.append((start, stop, self.pool.submit(_eigh_block, value[start:stop])))
                self.stats["maximum_pending_blocks"] = max(
                    self.stats["maximum_pending_blocks"], len(pending)
                )

        for _ in range(self.workers):
            submit()
        while pending:
            start, stop, future = pending.popleft()
            eigenvalues, eigenvectors, pid, memory = future.result()
            values[start:stop] = eigenvalues
            vectors[start:stop] = eigenvectors
            self.stats["blocks"] += 1
            if pid not in self.stats["worker_pids"]:
                self.stats["worker_pids"].append(pid)
            self.stats["minimum_observed_free_memory_gib"] = min(
                self.stats["minimum_observed_free_memory_gib"], memory
            )
            del eigenvalues, eigenvectors, future
            submit()
        return self.result_type(values, vectors)
