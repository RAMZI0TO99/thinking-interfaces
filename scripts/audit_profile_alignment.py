"""Independently reconstruct both A01 profiles from MAT signals and trial markers."""

from __future__ import annotations

import importlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from core.config import load_toml
from core.provenance import capture_source
from evaluation.source_bound_controls import file_digest
from scripts.diagnose_profile_units import atomic_json

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = (
    "Fz", "FC3", "FC1", "FCz", "FC2", "FC4", "C5", "C3", "C1", "Cz", "C2",
    "C4", "C6", "CP3", "CP1", "CPz", "CP2", "CP4", "P1", "Pz", "P2", "POz",
)
LABELS = {1: "left_hand", 2: "right_hand", 3: "feet", 4: "tongue"}


def cue_indices(trials: NDArray[Any], target_hz: float) -> NDArray[np.int64]:
    """MAT trial positions are one-based; the visual cue begins two seconds later."""
    positions = np.asarray(trials)
    if (positions.ndim != 1 or positions.size == 0 or not np.isfinite(positions).all()
            or np.any(positions < 1) or np.any(positions != np.floor(positions))
            or np.any(np.diff(positions) <= 0) or target_hz not in (128.0, 200.0)):
        raise ValueError("invalid native trial markers or profile sampling rate")
    return np.rint((positions.astype(np.float64) - 1 + 500) * target_hz / 250).astype(
        np.int64
    )


def reconstruct_epochs(
    continuous: NDArray[np.float64], indices: NDArray[np.int64], *,
    samples: int, baseline_samples: int, stored_unit_volts: float,
) -> NDArray[np.float32]:
    """Manual extraction, independent of the project's production epoch helpers."""
    if (continuous.ndim != 2 or not np.isfinite(continuous).all() or samples < 1
            or baseline_samples < 0 or stored_unit_volts <= 0
            or not np.isfinite(stored_unit_volts) or indices.ndim != 1
            or indices.size == 0):
        raise ValueError("invalid independent extraction inputs")
    output = []
    for cue in indices:
        start = int(cue)
        if start < baseline_samples or start + samples > continuous.shape[1]:
            raise ValueError("cue lacks its full baseline or four-second epoch")
        segment = continuous[:, start:start + samples]
        if baseline_samples:
            segment = segment - continuous[:, start - baseline_samples:start].mean(
                axis=1, keepdims=True
            )
        # Production B quantizes the voltage epoch before conversion to 0.1-mV units.
        epoch = np.asarray(segment, dtype=np.float32)
        output.append(np.asarray(epoch / stored_unit_volts, dtype=np.float32))
    return np.stack(output)


def compare_epochs(
    reconstructed: NDArray[np.float32], saved: NDArray[np.float32], *, unit_volts: float,
) -> dict[str, Any]:
    if not np.isfinite(unit_volts) or unit_volts <= 0:
        raise ValueError("comparison requires a finite positive voltage unit")
    if reconstructed.shape != saved.shape or reconstructed.dtype != saved.dtype:
        raise ValueError("independent/saved profile shape or dtype differs")
    actual_volts = reconstructed.astype(np.float64) * unit_volts
    saved_volts = saved.astype(np.float64) * unit_volts
    if not np.isfinite(actual_volts).all() or not np.isfinite(saved_volts).all():
        raise ValueError("nonfinite reconstructed or saved epochs")
    return {
        "within_declared_float32_tolerance": bool(np.allclose(
            actual_volts, saved_volts, rtol=1e-6, atol=1e-12,
        )),
        "exact_float32_values_equal": bool(np.array_equal(reconstructed, saved)),
        "maximum_absolute_difference_volts": float(np.max(np.abs(actual_volts - saved_volts))),
        "compared_epochs": len(saved),
    }


def main() -> int:
    provider = importlib.import_module("psutil")
    available = provider.virtual_memory().available / 1024**3
    if available < 6.0:
        print(json.dumps({"deferred": "startup memory below 6 GiB", "available_gib": available,
                          "processing_performed": False}))
        return 2
    observations = {"minimum_available_memory_gib": available, "stage_checks": 0}

    def guard() -> None:
        free = provider.virtual_memory().available / 1024**3
        observations["minimum_available_memory_gib"] = min(
            observations["minimum_available_memory_gib"], free
        )
        observations["stage_checks"] += 1
        if free < 4.0:
            raise RuntimeError("independent reconstruction stopped below 4 GiB free memory")

    from data.runtime import configure_scientific_runtime

    configure_scientific_runtime(ROOT)
    mne = importlib.import_module("mne")
    scipy_io = importlib.import_module("scipy.io")
    source = capture_source(ROOT)
    config: Any = load_toml(ROOT / "configs/base.toml")
    settings = config["preprocessing"]
    paths = {
        **{f"raw_{part}": ROOT / (
            f"data/raw/moabb/MNE-bnci-data/~bci/database/001-2014/A01{part}.mat"
        ) for part in ("T", "E")},
        **{profile: ROOT / f"data/processed/bci_iv_2a/{profile}/subject_01.npz"
           for profile in ("profile_a", "profile_b")},
    }
    hashes = {key: file_digest(path) for key, path in paths.items()}
    artifacts = {}
    for profile in ("profile_a", "profile_b"):
        guard()
        with np.load(paths[profile], allow_pickle=False) as artifact:
            artifacts[profile] = {name: artifact[name] for name in artifact.files}
        if (artifacts[profile]["signals"].shape[0] != 576
                or tuple(artifacts[profile]["channel_names"].tolist()) != CHANNELS):
            raise ValueError("the full original A01 cohort/canonical channels are required")
    rows = []
    for part, session in (("T", "0train"), ("E", "1test")):
        guard()
        raw_runs = scipy_io.loadmat(paths[f"raw_{part}"], simplify_cells=True)["data"]
        active_runs = [run for run in raw_runs if np.asarray(run["trial"]).size]
        if len(active_runs) != 6:
            raise ValueError("expected six task runs in each original A01 session")
        for run_index, run in enumerate(active_runs):
            guard()
            trials = np.asarray(run["trial"]).reshape(-1)
            targets = np.asarray(run["y"]).reshape(-1)
            if (float(run["fs"]) != 250.0 or len(trials) != 48 or len(targets) != 48
                    or run["X"].ndim != 2 or run["X"].shape[1] != 25
                    or any(value not in LABELS for value in targets)):
                raise ValueError("unexpected native sampling rate, channels, trials or classes")
            # No MOABB dataset, production profile function or annotation parser is used.
            volts = np.asarray(run["X"][:, :22].T * 1e-6, dtype=np.float64)
            for profile in ("profile_a", "profile_b"):
                guard()
                cfg = settings[profile]
                raw = mne.io.RawArray(volts.copy(), mne.create_info(CHANNELS, 250.0, "eeg"),
                                      verbose=False)
                raw.filter(l_freq=cfg["bandpass_low_hz"], h_freq=cfg["bandpass_high_hz"],
                           method="fir", phase="zero", n_jobs=1, verbose=False)
                if profile == "profile_a":
                    raw.set_eeg_reference(ref_channels="average", projection=False, verbose=False)
                    baseline, unit = round(cfg["pre_cue_s"] * cfg["resample_hz"]), 1.0
                else:
                    raw.notch_filter(freqs=[cfg["notch_hz"]], method="fir", phase="zero",
                                     n_jobs=1, verbose=False)
                    baseline, unit = 0, cfg["amplitude_unit_mv"] * 1e-3
                raw.resample(cfg["resample_hz"], npad="auto", n_jobs=1, verbose=False)
                indices = cue_indices(trials, cfg["resample_hz"])
                reconstructed = reconstruct_epochs(
                    raw.get_data(), indices, samples=round(4.0 * cfg["resample_hz"]),
                    baseline_samples=baseline, stored_unit_volts=unit,
                )
                artifact = artifacts[profile]
                selected = np.flatnonzero((artifact["sessions"] == session)
                                          & (artifact["runs"] == str(run_index)))
                if (len(selected) != 48
                        or artifact["trial_indices"][selected].tolist() != list(range(48))
                        or artifact["labels"][selected].tolist()
                        != [LABELS[int(value)] for value in targets]):
                    raise ValueError("raw and saved trial identities or label order differ")
                result = compare_epochs(reconstructed, artifact["signals"][selected],
                                        unit_volts=unit)
                rows.append({"profile": profile, "session": session, "run": str(run_index),
                             "native_trial_positions_one_based": trials.tolist(),
                             "cue_samples_at_profile_rate": indices.tolist(), **result})
                del raw, reconstructed
            print(json.dumps({"checked_session": session, "checked_run": run_index}), flush=True)
        del raw_runs, active_runs, volts
    unchanged = hashes == {key: file_digest(path) for key, path in paths.items()}
    current = capture_source(ROOT)
    passed = (unchanged and source.source_sha256 == current.source_sha256
              and len(rows) == 24
              and all(row["within_declared_float32_tolerance"] for row in rows))
    report = {
        "passed": passed, "source": asdict(source), "inputs": hashes, "input_files_unchanged":
        unchanged, "execution_sha256": file_digest(Path(__file__)), "preprocessing": settings,
        "cue_rule": "(MAT trial - 1 + 500 native samples) / 250 Hz; nearest output sample",
        "tolerance": {"relative": 1e-6, "absolute_volts": 1e-12}, "rows": rows,
        "resources": observations, "model_training_performed": False,
        "scope": "A01 raw-event/epoch reconstruction only; not accuracy-gap attribution or a gate.",
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "runs/profile_alignment_review" / f"{stamp}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(output, report)
    print(json.dumps({"report": str(output), "sha256": file_digest(output), "passed": passed,
                      "profile_run_comparisons": len(rows)}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
