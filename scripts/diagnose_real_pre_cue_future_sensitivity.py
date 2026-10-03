"""Bounded, read-only post-cue sensitivity on one real BCI IV 2a run.

Run from the project root with ``python -m scripts.diagnose_real_pre_cue_future_sensitivity``.
No control artifact, checkpoint or result file is written.
"""

from __future__ import annotations

import hashlib
import json
import math
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

import mne  # type: ignore[import-untyped]
import numpy as np
import psutil  # type: ignore[import-untyped]
from moabb.datasets import BNCI2014_001  # type: ignore[import-untyped]

from data.bci_iv_2a import configure_local_cache
from data.pre_cue import PreCueConfig, preprocess_pre_cue_run

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = 1
MAX_EVENTS = 8
PER_CLASS = 2
RAM_FLOOR_GIB = 4.0


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _guard() -> dict[str, float]:
    with (ROOT / "configs" / "base.toml").open("rb") as stream:
        base = tomllib.load(stream)
    disk_gib = psutil.disk_usage(str(ROOT)).free / 1024**3
    ram_gib = psutil.virtual_memory().available / 1024**3
    disk_floor = float(base["storage"]["minimum_free_gb"])
    if disk_gib < disk_floor or ram_gib < RAM_FLOOR_GIB:
        raise RuntimeError(
            f"resource guard failed: free disk {disk_gib:.2f}/{disk_floor:.2f} GiB, "
            f"available RAM {ram_gib:.2f}/{RAM_FLOOR_GIB:.2f} GiB"
        )
    return {"free_disk_gib": round(disk_gib, 2), "available_ram_gib": round(ram_gib, 2)}


def _config() -> PreCueConfig:
    with (ROOT / "configs" / "base.toml").open("rb") as stream:
        profile = tomllib.load(stream)["preprocessing"]["profile_a"]
    return PreCueConfig(
        bandpass_low_hz=float(profile["bandpass_low_hz"]),
        bandpass_high_hz=float(profile["bandpass_high_hz"]),
        resample_hz=float(profile["resample_hz"]),
        window_duration_s=float(profile["pre_cue_s"]),
        reference=str(profile["reference"]),
    )


def _processed_signal(signal: np.ndarray, info: Any, config: PreCueConfig) -> np.ndarray:
    # MNE may reuse an already-float64 input buffer. Keep every counterfactual
    # independent and preserve the original raw samples for later comparisons.
    raw = mne.io.RawArray(np.array(signal, dtype=np.float64, copy=True), info.copy(), verbose=False)
    raw.filter(
        l_freq=config.bandpass_low_hz,
        h_freq=config.bandpass_high_hz,
        method="fir",
        phase="zero",
        n_jobs=1,
        verbose=False,
    )
    raw.set_eeg_reference(ref_channels="average", projection=False, verbose=False)
    raw.resample(config.resample_hz, npad="auto", n_jobs=1, verbose=False)
    return np.asarray(raw.get_data(), dtype=np.float64)


def _window(processed: np.ndarray, cue: int, samples: int) -> np.ndarray:
    if cue < samples or cue > processed.shape[1]:
        raise ValueError("pre-cue interval is incomplete after resampling")
    segment = processed[:, cue - samples : cue]
    return np.asarray(segment - segment.mean(axis=1, keepdims=True), dtype=np.float32)


def _stats(reference: np.ndarray, comparison: np.ndarray) -> dict[str, float]:
    difference_uv = (reference.astype(np.float64) - comparison.astype(np.float64)) * 1e6
    return {
        "max_abs_uv": float(np.max(np.abs(difference_uv))),
        "rms_uv": float(np.sqrt(np.mean(np.square(difference_uv)))),
    }


def _summary(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    maxima = np.asarray([row[key]["max_abs_uv"] for row in rows], dtype=np.float64)
    rms = np.asarray([row[key]["rms_uv"] for row in rows], dtype=np.float64)
    return {
        "median_max_abs_uv": float(np.median(maxima)),
        "maximum_max_abs_uv": float(maxima.max()),
        "median_rms_uv": float(np.median(rms)),
        "maximum_rms_uv": float(rms.max()),
    }


def diagnose() -> dict[str, object]:
    """Read one local run and compare current versus two no-future variants."""

    guard_before = _guard()
    config = _config()
    with (ROOT / "configs" / "bci_iv_2a.toml").open("rb") as stream:
        dataset_document = tomllib.load(stream)
    dataset_config = dataset_document["dataset"]
    raw_root = ROOT / dataset_config["raw_root"]
    raw_file = raw_root / "MNE-bnci-data" / "~bci" / "database" / "001-2014" / "A01T.mat"
    if not raw_file.is_file() or not raw_file.resolve().is_file():
        raise FileNotFoundError("local BCI IV 2a subject 01 training raw file is unavailable")
    raw_sha256 = _hash(raw_file)
    if raw_sha256 != dataset_document["verification"]["subject_1"]["training_sha256"]:
        raise ValueError("local BCI IV 2a training raw bytes differ from the reviewed pin")

    configure_local_cache(ROOT, raw_root)
    dataset = BNCI2014_001()
    subject_data = dataset.get_data(subjects=[SUBJECT], n_jobs=1)[SUBJECT]
    session = sorted(subject_data)[0]
    run = sorted(subject_data[session])[0]
    raw = subject_data[session][run]
    del subject_data
    guard_loaded = _guard()
    if raw.first_samp != 0 or float(raw.info["sfreq"]) != 250.0:
        raise ValueError("unexpected first sample or BCI IV 2a raw sampling rate")
    events, _ = mne.events_from_annotations(
        raw, event_id=dict(dataset.event_id), regexp=None, verbose=False
    )
    if len(events) < MAX_EVENTS:
        raise ValueError("selected BCI task run has too few cue annotations")
    counts: Counter[int] = Counter()
    selected: list[int] = []
    for index, event in enumerate(events):
        code = int(event[2])
        if counts[code] < PER_CLASS:
            selected.append(index)
            counts[code] += 1
        if len(selected) == MAX_EVENTS:
            break
    if len(selected) != MAX_EVENTS or len(counts) != 4:
        raise ValueError("selected run lacks two cues from each of four classes")
    current, labels, channels = preprocess_pre_cue_run(raw, dataset.event_id, config)
    if len(labels) != len(events) or len(channels) != 22:
        raise ValueError("production pre-cue extraction differs from raw events/channels")
    eeg = raw.copy().pick(picks="eeg")
    signal = eeg.get_data()
    info = eeg.info
    raw_sfreq = float(raw.info["sfreq"])
    window_samples = round(config.window_duration_s * config.resample_hz)
    # The production call above uses annotations after resampling. Recreate its
    # windows directly once to confirm the manual cue mapping before comparisons.
    same_processing = _processed_signal(signal, info, config)
    rows: list[dict[str, Any]] = []
    for index in selected:
        cue_sample = int(events[index, 0])
        cue_resampled = round(cue_sample * config.resample_hz / raw_sfreq)
        expected = _window(same_processing, cue_resampled, window_samples)
        if not np.allclose(expected, current[index], rtol=0, atol=1e-9):
            raise ValueError("manual cue mapping does not match production extraction")
        if cue_sample < round(config.window_duration_s * raw_sfreq):
            raise ValueError("real cue has no complete raw pre-cue interval")

        # No samples at or after the cue enter this zero-phase prefix filter.
        prefix = _processed_signal(signal[:, :cue_sample], info, config)
        if prefix.shape[1] != cue_resampled:
            raise ValueError("prefix resampling did not end at the production cue index")
        prefix_window = _window(prefix, prefix.shape[1], window_samples)

        # Same-length counterfactual: replace all future samples by the last
        # observed sample, then apply the exact current filter/reference/resampler.
        held = signal.copy()
        held[:, cue_sample:] = signal[:, cue_sample - 1 : cue_sample]
        held_processed = _processed_signal(held, info, config)
        held_window = _window(held_processed, cue_resampled, window_samples)
        row = {
            "event_index": index,
            "cue_sample": cue_sample,
            "label": labels[index],
            "prefix_only": _stats(current[index], prefix_window),
            "flat_future": _stats(current[index], held_window),
            "current_epoch_rms_uv": float(
                math.sqrt(float(np.mean(np.square(current[index].astype(np.float64))))) * 1e6
            ),
        }
        rows.append(row)
        _guard()

    return {
        "diagnostic_kind": "real_run_pre_cue_future_sensitivity",
        "status": "preliminary_read_only_not_gate_a_signoff",
        "subject": SUBJECT,
        "session": session,
        "run": run,
        "raw_file_sha256": raw_sha256,
        "raw_file_bytes": raw_file.stat().st_size,
        "pre_cue_source_sha256": _hash(ROOT / "data" / "pre_cue.py"),
        "base_config_sha256": _hash(ROOT / "configs" / "base.toml"),
        "mne_version": mne.__version__,
        "cue_count_in_run": len(events),
        "selected_cue_count": len(rows),
        "selected_labels": dict(Counter(row["label"] for row in rows)),
        "epoch_shape": list(current.shape[1:]),
        "profile_a": {
            "bandpass_hz": [config.bandpass_low_hz, config.bandpass_high_hz],
            "resample_hz": config.resample_hz,
            "window_duration_s": config.window_duration_s,
            "reference": config.reference,
        },
        "resource_guard_before": guard_before,
        "resource_guard_after_loading": guard_loaded,
        "prefix_only_summary": _summary(rows, "prefix_only"),
        "flat_future_summary": _summary(rows, "flat_future"),
        "rows": rows,
        "scientific_cells_admitted": 0,
        "control_model_metric_computed": False,
    }


def main() -> int:
    print(json.dumps(diagnose(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
