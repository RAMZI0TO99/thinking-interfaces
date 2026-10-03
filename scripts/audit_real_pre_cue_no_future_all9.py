"""Read-only signal audit of the proposed pre-cue path on all nine BCI subjects.

Run ``python -m scripts.audit_real_pre_cue_no_future_all9 --write-receipt``
from the project root. Only the versioned audit receipt is written; no EEG
artifact, classifier result, or Phase I record is created or replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import tomllib
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import mne  # type: ignore[import-untyped]
import moabb  # type: ignore[import-untyped]
import numpy as np
import psutil  # type: ignore[import-untyped]
import scipy  # type: ignore[import-untyped]
from moabb.datasets import BNCI2014_001  # type: ignore[import-untyped]

from data.bci_iv_2a import configure_local_cache
from data.pre_cue import PreCueConfig, preprocess_pre_cue_run
from data.pre_cue_no_future import (
    BCI_EVENT_ID,
    NoFuturePreCueConfig,
    load_no_future_config,
    no_future_window,
    preprocess_no_future_run,
)
from evaluation.phase2_records import envelope, write_once

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_DIR = ROOT / "runs/phase2/gate_a_diagnostics/20260923_no_future_all9"
RECEIPT_PATH = RECEIPT_DIR / "real_pre_cue_no_future_all9.json"
RAM_FLOOR_GIB = 4.0
SOURCE_PATHS = (
    "scripts/audit_real_pre_cue_no_future_all9.py",
    "data/pre_cue.py",
    "data/pre_cue_no_future.py",
    "data/bci_iv_2a.py",
    "data/runtime.py",
    "evaluation/phase2_records.py",
    "core/config.py",
    "configs/base.toml",
    "configs/bci_iv_2a.toml",
    "configs/pre_cue_no_future_v1.toml",
    "requirements-data.lock",
)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_hashes() -> dict[str, str]:
    return {relative: _digest(ROOT / relative) for relative in SOURCE_PATHS}


def _raw_file_identity(path: Path) -> dict[str, str | int]:
    if not path.is_file():
        raise FileNotFoundError(f"raw audit input disappeared: {path}")
    before = path.stat()
    digest = _digest(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f"raw audit input changed while hashing: {path}")
    return {"sha256": digest, "bytes": after.st_size}


def _require_raw_files_unchanged(
    raw_files: Mapping[str, Path],
    initial_hashes: Mapping[str, Mapping[str, str | int]],
) -> None:
    if raw_files.keys() != initial_hashes.keys():
        raise ValueError("raw audit input roster changed while running")
    for name, path in sorted(raw_files.items()):
        if _raw_file_identity(path) != initial_hashes[name]:
            raise ValueError(f"raw audit input changed while running: {name}")


def _guard(disk_floor_gib: float) -> dict[str, float]:
    disk = psutil.disk_usage(str(ROOT)).free / 1024**3
    ram = psutil.virtual_memory().available / 1024**3
    if disk < disk_floor_gib or ram < RAM_FLOOR_GIB:
        raise RuntimeError(
            f"audit resource guard failed: disk {disk:.2f}/{disk_floor_gib:.2f} GiB, "
            f"RAM {ram:.2f}/{RAM_FLOOR_GIB:.2f} GiB"
        )
    return {
        "free_disk_gib": round(disk, 3),
        "available_ram_gib": round(ram, 3),
        "process_rss_gib": round(psutil.Process().memory_info().rss / 1024**3, 3),
    }


def _legacy_config(base: dict[str, Any]) -> PreCueConfig:
    profile = base["preprocessing"]["profile_a"]
    return PreCueConfig(
        bandpass_low_hz=float(profile["bandpass_low_hz"]),
        bandpass_high_hz=float(profile["bandpass_high_hz"]),
        resample_hz=float(profile["resample_hz"]),
        window_duration_s=float(profile["pre_cue_s"]),
        reference=str(profile["reference"]),
    )


def _validate_matching_nominal_settings(
    old: PreCueConfig, new: NoFuturePreCueConfig
) -> None:
    if (
        old.bandpass_low_hz != new.bandpass_low_hz
        or old.bandpass_high_hz != new.bandpass_high_hz
        or old.resample_hz != new.resample_hz
        or old.window_duration_s != new.window_duration_s
        or old.reference != new.reference
    ):
        raise ValueError("legacy and proposed nominal signal settings differ")


def _summarize(values: list[float]) -> dict[str, float]:
    samples = np.asarray(values, dtype=np.float64)
    if samples.size == 0 or not np.isfinite(samples).all():
        raise ValueError("finite nonempty audit measurements are required")
    return {
        "minimum": float(samples.min()),
        "median": float(np.median(samples)),
        "p95": float(np.percentile(samples, 95)),
        "maximum": float(samples.max()),
    }


def _representative_future_check(
    raw: Any,
    first_new_window: np.ndarray,
    event_id: dict[str, int],
    new_config: NoFuturePreCueConfig,
    *,
    subject: int,
    session: str,
    run: str,
) -> dict[str, object]:
    """Alter one real cue and its entire future, preserving its raw prefix."""
    events, _ = mne.events_from_annotations(
        raw, event_id=event_id, regexp=None, verbose=False
    )
    cue = int(events[0, 0])
    eeg = raw.copy().pick(picks="eeg")
    before = eeg.get_data()
    altered = np.array(before, dtype=np.float64, copy=True)
    altered[:, cue:] = before[:, cue - 1 : cue]
    altered[:, cue] += 100e-6
    if not np.array_equal(altered[:, :cue], before[:, :cue]):
        raise ValueError("future counterfactual changed the pre-cue raw prefix")
    changed_max_uv = float(np.max(np.abs(altered[:, cue:] - before[:, cue:])) * 1e6)
    if changed_max_uv <= 0:
        raise ValueError("future counterfactual did not change raw data")
    counterfactual = mne.io.RawArray(altered, eeg.info.copy(), verbose=False)
    observed = no_future_window(
        counterfactual, cue_sample=cue, config=new_config
    )
    if not np.array_equal(observed, first_new_window):
        raise ValueError("proposed no-future window changed with post-cue input")
    return {
        "subject": subject,
        "session": session,
        "run": run,
        "event_index": 0,
        "cue_raw_sample": cue,
        "future_raw_samples_altered": int(before.shape[1] - cue),
        "maximum_future_raw_change_uv": changed_max_uv,
        "window_exactly_equal": True,
    }


def audit() -> dict[str, object]:
    """Compare every annotated cue in all nine cached subjects, without fitting."""
    start = time.monotonic()
    source_hashes = _source_hashes()
    with (ROOT / "configs/base.toml").open("rb") as stream:
        base = tomllib.load(stream)
    with (ROOT / "configs/bci_iv_2a.toml").open("rb") as stream:
        dataset_config = tomllib.load(stream)
    old_config = _legacy_config(base)
    new_config = load_no_future_config()
    _validate_matching_nominal_settings(old_config, new_config)
    disk_floor = float(base["storage"]["minimum_free_gb"])
    resources_before = _guard(disk_floor)

    dataset_section = dataset_config["dataset"]
    subjects = tuple(dataset_section["subjects"])
    if subjects != tuple(range(1, 10)):
        raise ValueError("expected BCI IV 2a subjects 1 through 9")
    raw_root = ROOT / dataset_section["raw_root"]
    raw_dir = raw_root / "MNE-bnci-data" / "~bci" / "database" / "001-2014"
    raw_files = {
        f"A{subject:02d}{session}.mat": raw_dir / f"A{subject:02d}{session}.mat"
        for subject in subjects
        for session in ("T", "E")
    }
    if any(not path.is_file() for path in raw_files.values()):
        raise FileNotFoundError("all 18 BCI IV 2a raw files must already be local")
    raw_hashes = {name: _raw_file_identity(path) for name, path in raw_files.items()}
    subject1_pin = dataset_config["verification"]["subject_1"]
    if (
        raw_hashes["A01T.mat"]["sha256"] != subject1_pin["training_sha256"]
        or raw_hashes["A01E.mat"]["sha256"] != subject1_pin["evaluation_sha256"]
    ):
        raise ValueError("subject 01 raw bytes differ from the reviewed config pin")

    configure_local_cache(ROOT, raw_root)
    dataset = BNCI2014_001()
    event_id = dict(dataset.event_id)
    if event_id != BCI_EVENT_ID:
        raise ValueError("MOABB event mapping differs from the proposed contract")

    subject_rows: list[dict[str, object]] = []
    cue_rows: list[dict[str, object]] = []
    invariance_rows: list[dict[str, object]] = []
    overall_maxima: list[float] = []
    overall_rms: list[float] = []
    overall_sumsq = np.zeros(len(new_config.channel_names), dtype=np.float64)
    overall_channel_max = np.zeros(len(new_config.channel_names), dtype=np.float64)
    overall_channel_samples = 0
    label_counts: Counter[str] = Counter()
    for subject in subjects:
        subject_start = time.monotonic()
        resources_subject_before = _guard(disk_floor)
        source_data = dataset.get_data(subjects=[subject], n_jobs=1)[subject]
        subject_sumsq = np.zeros(len(new_config.channel_names), dtype=np.float64)
        subject_channel_max = np.zeros(len(new_config.channel_names), dtype=np.float64)
        subject_channel_samples = 0
        subject_maxima: list[float] = []
        subject_rms: list[float] = []
        subject_cues = 0
        run_count = 0
        sessions_seen: list[str] = []
        for session, runs in sorted(source_data.items()):
            sessions_seen.append(str(session))
            for run, raw in sorted(runs.items()):
                old, old_labels, old_channels = preprocess_pre_cue_run(
                    raw, event_id, old_config
                )
                new, new_labels, new_channels = preprocess_no_future_run(
                    raw, event_id, new_config
                )
                if (
                    old.shape != new.shape
                    or old.shape[1:] != (len(new_config.channel_names), 128)
                    or old_labels != new_labels
                    or old_channels != new_channels
                    or new_channels != new_config.channel_names
                    or old.dtype != np.float32
                    or new.dtype != np.float32
                    or not np.isfinite(old).all()
                    or not np.isfinite(new).all()
                ):
                    raise ValueError(
                        f"subject {subject} {session}/{run}: shapes, labels, "
                        "channels or finite signal values differ"
                    )
                events, _ = mne.events_from_annotations(
                    raw, event_id=event_id, regexp=None, verbose=False
                )
                if len(events) != len(new_labels):
                    raise ValueError("raw cue and processed window counts differ")
                difference_uv = (old.astype(np.float64) - new.astype(np.float64)) * 1e6
                channel_max = np.max(np.abs(difference_uv), axis=(0, 2))
                channel_sumsq = np.sum(np.square(difference_uv), axis=(0, 2))
                samples_per_channel = int(new.shape[0] * new.shape[2])
                subject_channel_max = np.maximum(subject_channel_max, channel_max)
                subject_sumsq += channel_sumsq
                subject_channel_samples += samples_per_channel
                cue_max = np.max(np.abs(difference_uv), axis=(1, 2))
                cue_rms = np.sqrt(np.mean(np.square(difference_uv), axis=(1, 2)))
                cue_channel_max = np.max(np.abs(difference_uv), axis=2)
                cue_channel_rms = np.sqrt(np.mean(np.square(difference_uv), axis=2))
                for index, label in enumerate(new_labels):
                    maximum = float(cue_max[index])
                    rms = float(cue_rms[index])
                    cue_rows.append({
                        "subject": subject,
                        "session": str(session),
                        "run": str(run),
                        "event_index": index,
                        "cue_raw_sample": int(events[index, 0]),
                        "label": label,
                        "max_abs_difference_uv": maximum,
                        "rms_difference_uv": rms,
                        "channel_max_abs_difference_uv": [
                            float(value) for value in cue_channel_max[index]
                        ],
                        "channel_rms_difference_uv": [
                            float(value) for value in cue_channel_rms[index]
                        ],
                    })
                    subject_maxima.append(maximum)
                    subject_rms.append(rms)
                    label_counts[label] += 1
                subject_cues += len(new_labels)
                run_count += 1
                if str(run) == sorted(runs)[0]:
                    invariance_rows.append(_representative_future_check(
                        raw, new[0], event_id, new_config,
                        subject=subject, session=str(session), run=str(run),
                    ))
                _guard(disk_floor)
        if len(sessions_seen) != 2 or run_count != 12 or subject_cues != 576:
            raise ValueError(f"subject {subject}: unexpected session/run/cue count")
        overall_channel_max = np.maximum(overall_channel_max, subject_channel_max)
        overall_sumsq += subject_sumsq
        overall_channel_samples += subject_channel_samples
        overall_maxima.extend(subject_maxima)
        overall_rms.extend(subject_rms)
        subject_rows.append({
            "subject": subject,
            "sessions": sessions_seen,
            "runs": run_count,
            "cues": subject_cues,
            "shape_per_cue": [len(new_config.channel_names), 128],
            "cue_max_abs_difference_uv": _summarize(subject_maxima),
            "cue_rms_difference_uv": _summarize(subject_rms),
            "channels": [
                {
                    "name": channel,
                    "max_abs_difference_uv": float(subject_channel_max[index]),
                    "rms_difference_uv": float(math.sqrt(
                        subject_sumsq[index] / subject_channel_samples
                    )),
                }
                for index, channel in enumerate(new_config.channel_names)
            ],
            "elapsed_seconds": round(time.monotonic() - subject_start, 3),
            "resources_before": resources_subject_before,
            "resources_after": _guard(disk_floor),
        })
        print(f"audited subject {subject}/9: {subject_cues} cues", flush=True)
        del source_data

    if len(cue_rows) != 9 * 576 or len(invariance_rows) != 9 * 2:
        raise ValueError("nine-subject audit coverage differs")
    if set(label_counts) != set(BCI_EVENT_ID):
        raise ValueError("four-class label coverage differs")
    _require_raw_files_unchanged(raw_files, raw_hashes)
    if _source_hashes() != source_hashes:
        raise ValueError("audit source/config bytes changed while running")
    resources_after = _guard(disk_floor)
    return {
        "audit_kind": "real_pre_cue_no_future_all9_signal_comparison",
        "status": "preliminary_read_only_not_gate_a_signoff",
        "created_utc": datetime.now(UTC).isoformat(),
        "source_sha256": source_hashes,
        "raw_files": raw_hashes,
        "subject_01_raw_pin_verified": True,
        "subjects": list(subjects),
        "library_versions": {
            "mne": mne.__version__,
            "moabb": moabb.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "nominal_profile": {
            "bandpass_hz": [old_config.bandpass_low_hz, old_config.bandpass_high_hz],
            "resample_hz": old_config.resample_hz,
            "window_duration_s": old_config.window_duration_s,
            "reference": old_config.reference,
        },
        "total_runs": 108,
        "total_cues": len(cue_rows),
        "label_counts": dict(sorted(label_counts.items())),
        "shape_per_cue": [len(new_config.channel_names), 128],
        "overall_cue_max_abs_difference_uv": _summarize(overall_maxima),
        "overall_cue_rms_difference_uv": _summarize(overall_rms),
        "overall_channels": [
            {
                "name": channel,
                "max_abs_difference_uv": float(overall_channel_max[index]),
                "rms_difference_uv": float(math.sqrt(
                    overall_sumsq[index] / overall_channel_samples
                )),
            }
            for index, channel in enumerate(new_config.channel_names)
        ],
        "subjects_detail": subject_rows,
        "cues_detail": cue_rows,
        "representative_future_invariance": invariance_rows,
        "resources_before": resources_before,
        "resources_after": resources_after,
        "resource_delta_gib": {
            key: round(resources_after[key] - resources_before[key], 3)
            for key in resources_before
        },
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "scientific_cells_admitted": 0,
        "control_model_metric_computed": False,
        "processed_eeg_artifact_written": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args()
    result = audit()
    if args.write_receipt:
        if RECEIPT_PATH.exists():
            raise FileExistsError("audit receipt is write-once")
        record = envelope(
            "engineering_smoke",
            {"purpose": "real_no_future_all9_audit", "observed": result},
        )
        write_once(RECEIPT_PATH, record, output_root=RECEIPT_DIR)
        print(json.dumps({"receipt": str(RECEIPT_PATH), "sha256": record["sha256"]}))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
