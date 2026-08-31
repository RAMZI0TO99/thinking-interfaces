"""Reference-aligned MOABB input used only to diagnose Gate A."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from moabb.datasets import BNCI2014_001  # type: ignore[import-untyped]
from moabb.paradigms import MotorImagery  # type: ignore[import-untyped]

from data.bci_iv_2a import configure_local_cache


def apply_common_average_reference(
    signals: np.ndarray[Any, np.dtype[np.float32]],
) -> np.ndarray[Any, np.dtype[np.float32]]:
    """Apply trial-wise common-average reference across the channel axis."""

    if signals.ndim != 3 or signals.shape[1] < 2:
        raise ValueError("signals must have shape (trials, channels, samples)")
    return np.asarray(signals - signals.mean(axis=1, keepdims=True), dtype=np.float32)


def load_reference_subject(
    subject: int,
    *,
    project_root: Path,
    raw_root: Path,
    events: tuple[str, ...],
    bandpass_low_hz: float,
    bandpass_high_hz: float,
) -> tuple[
    np.ndarray[Any, np.dtype[np.float32]],
    np.ndarray[Any, np.dtype[np.str_]],
    np.ndarray[Any, np.dtype[np.str_]],
]:
    """Load exactly the preprocessing used by Braindecode's MOABB example."""

    if subject < 1 or not events:
        raise ValueError("subject must be positive and events must not be empty")
    configure_local_cache(project_root, raw_root)
    dataset = BNCI2014_001()
    paradigm = MotorImagery(
        events=list(events),
        n_classes=len(events),
        fmin=bandpass_low_hz,
        fmax=bandpass_high_hz,
        tmin=0.0,
        tmax=None,
    )
    signals, labels, metadata = paradigm.get_data(
        dataset=dataset,
        subjects=[subject],
        return_epochs=False,
        n_jobs=1,
    )
    sessions = metadata["session"].astype(str).to_numpy()
    output_signals = np.ascontiguousarray(signals, dtype=np.float32)
    output_labels = np.asarray(labels, dtype=np.str_)
    output_sessions = np.asarray(sessions, dtype=np.str_)
    if output_signals.ndim != 3 or output_signals.shape[0] != output_labels.size:
        raise ValueError("MOABB returned incompatible Gate A arrays")
    if output_labels.size != output_sessions.size or not np.isfinite(output_signals).all():
        raise ValueError("MOABB returned invalid Gate A metadata or signals")
    return output_signals, output_labels, output_sessions
