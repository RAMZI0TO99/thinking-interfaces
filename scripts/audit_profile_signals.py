"""Descriptive source-session signal energy; no fitting or artifact modification."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tomllib
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.config import config_digest
from core.provenance import capture_source

ROOT = Path(__file__).resolve().parents[1]


def signal_energy(signals: Any, sampling_rate: float, low: float, high: float) -> dict[str, Any]:
    import numpy as np

    values = np.asarray(signals, dtype=np.float64)
    if (
        values.ndim != 3
        or min(values.shape) < 1
        or not np.isfinite(values).all()
        or not 0 < low < high < sampling_rate / 2
    ):
        raise ValueError("finite channel-first epochs and valid frequency bounds required")
    count = values.shape[-1]
    frequencies = np.fft.rfftfreq(count, 1 / sampling_rate)
    power = np.abs(np.fft.rfft(values, axis=-1)) ** 2 / count**2
    power[..., 1:] *= 2
    if count % 2 == 0:
        power[..., -1] /= 2
    spectrum = power.mean(axis=(0, 1))
    mean_square = float(np.mean(values**2))
    if mean_square <= 0 or not math.isclose(float(spectrum.sum()), mean_square, rel_tol=1e-12):
        raise ValueError("zero energy or Parseval energy check failed")
    bands = {
        "dc": frequencies == 0,
        "above_dc_below_profile_a_band": (frequencies > 0) & (frequencies < low),
        "profile_a_band_inclusive": (frequencies >= low) & (frequencies <= high),
        "above_profile_a_band": frequencies > high,
    }
    fractions = {key: float(spectrum[mask].sum()) / mean_square for key, mask in bands.items()}
    common_fraction = float(np.mean(np.mean(values, axis=1) ** 2)) / mean_square
    return {
        "trials": values.shape[0],
        "channels": values.shape[1],
        "samples": count,
        "duration_seconds": count / sampling_rate,
        "frequency_resolution_hz": sampling_rate / count,
        "rms_microvolts": math.sqrt(mean_square) * 1e6,
        "energy_fractions": fractions,
        "spatial_common_mean_energy_fraction": common_fraction,
        "parseval_verified": True,
    }


def main() -> int:
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[variable] = "1"
    import numpy as np

    comparison = tomllib.loads((ROOT / "configs/profile_comparison.toml").read_text())
    base = tomllib.loads((ROOT / "configs/base.toml").read_text())
    source = capture_source(ROOT)
    if source.git_dirty is not False:
        raise ValueError("commit the descriptive audit before recording its evidence")
    profile_a = base["preprocessing"]["profile_a"]
    report: dict[str, Any] = {
        "source": asdict(source),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "config": {"comparison": comparison, "preprocessing": base["preprocessing"]},
        "scope": "Source-session descriptive energy only; no accuracy attribution or fitting.",
        "method": (
            "One-sided rectangular-window DFT energy, no detrending; DC separate, "
            "Parseval checked. Finite-window bin allocation includes spectral leakage, "
            "not ideal band-isolated power."
        ),
        "profiles": {},
        "artifact_sha256": {},
        "training_performed": False,
    }
    reference_indices = None
    for name in ("profile_a", "profile_b"):
        settings = comparison[name]
        path = ROOT / settings["artifact"]
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        with np.load(path, allow_pickle=False) as archive:
            indices = np.flatnonzero(
                archive["sessions"] == comparison["comparison"]["train_session"]
            )
            if len(indices) != 288:
                raise ValueError("expected the original 288-trial source session")
            if reference_indices is not None and not np.array_equal(indices, reference_indices):
                raise ValueError("source trial selection differs between profiles")
            reference_indices = indices
            unit = (
                1.0
                if name == "profile_a"
                else (base["preprocessing"]["profile_b"]["amplitude_unit_mv"] * 1e-3)
            )
            volts = np.asarray(archive["signals"][indices], dtype=np.float64) * unit
            report["profiles"][name] = signal_energy(
                volts,
                settings["sampling_rate_hz"],
                profile_a["bandpass_low_hz"],
                profile_a["bandpass_high_hz"],
            )
        if hashlib.sha256(path.read_bytes()).hexdigest() != before:
            raise RuntimeError("profile input changed during descriptive audit")
        report["artifact_sha256"][name] = before
    if reference_indices is None:
        raise ValueError("no source-session inputs were inspected")
    report["source_indices"] = reference_indices.tolist()
    report["config_sha256"] = config_digest(report["config"])
    if capture_source(ROOT).source_sha256 != source.source_sha256:
        raise RuntimeError("audit source changed")
    output = ROOT / "runs/profile_signal_review"
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = output / f"{stamp}.json"
    with target.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"report": str(target), "profiles": report["profiles"]}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
