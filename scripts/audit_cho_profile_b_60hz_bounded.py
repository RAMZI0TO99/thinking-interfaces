"""Read-only, predeclared Cho subject-01 60 Hz Profile B signal diagnostic.

All input hashes come from an independent asset inventory. A spectral pass is
engineering evidence for the rebuild, not scientific-cell admission.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from core.config import load_toml
from evaluation.phase2_profile_binding import (
    _CHO_60HZ_VARIANT,
    _CHO_PROFILE_B_60HZ,
    CHO_CHANNELS,
    CHO_CLASSES,
    _check_manifest,
    _read_artifact,
)
from evaluation.phase2_protocol import require_digest
from scripts.audit_phase2_protocol import file_digest, inside

ROOT = Path(__file__).resolve().parents[1]
VARIANT_CONFIG = "configs/phase2/cho_profile_b_60hz.toml"
MINIMUM_60HZ_ATTENUATION_DB = 6.0


def _pinned(path: Path, expected: str, name: str) -> None:
    require_digest(expected, name)
    if file_digest(path) != expected:
        raise ValueError(f"pinned {name} bytes changed")


def _line_ratio(signals: NDArray[np.float32], frequency_hz: int) -> float:
    """Median line-bin power divided by the 2–4 Hz sideband median."""
    samples = signals.shape[-1]
    frequencies = np.fft.rfftfreq(samples, d=1 / 200.0)
    line = np.flatnonzero(np.isclose(frequencies, float(frequency_hz)))
    sidebands = np.flatnonzero(
        ((frequency_hz - 4 <= frequencies) & (frequencies <= frequency_hz - 2))
        | ((frequency_hz + 2 <= frequencies) & (frequencies <= frequency_hz + 4))
    )
    if len(line) != 1 or len(sidebands) < 4:
        raise ValueError("line-frequency bins are unavailable")
    centered = signals.astype(np.float64) - signals.mean(axis=-1, keepdims=True)
    power = np.abs(np.fft.rfft(centered * np.hanning(samples), axis=-1)) ** 2
    background = float(np.median(power[..., sidebands]))
    if not math.isfinite(background) or background <= 0:
        raise ValueError("line-noise sideband power is invalid")
    at_line = float(np.median(power[..., int(line[0])]))
    floor = max(np.finfo(float).tiny, background * 1e-12)
    return (at_line + floor) / background


def audit_subject_01(root: Path, pins: dict[str, str]) -> dict[str, Any]:
    """Check exact input identities and report a fixed 60 Hz spectral comparison."""
    root = root.resolve()
    required = {
        "profile_a", "legacy_artifact", "legacy_manifest", "variant_artifact",
        "variant_manifest", "variant_config", "raw_source",
    }
    if set(pins) != required:
        raise ValueError("all seven independent input digests are required")
    variant_directory = root / str(_CHO_60HZ_VARIANT["output_directory"])
    if variant_directory.resolve() != variant_directory:
        raise ValueError("Cho 60 Hz output aliases another namespace")
    paths = {
        "profile_a": inside(root, "data/processed/cho2017/profile_a/subject_01.npz"),
        "legacy_artifact": inside(root, "data/processed/cho2017/profile_b/subject_01.npz"),
        "legacy_manifest": inside(
            root, "data/processed/cho2017/profile_b/subject_01.manifest.json"
        ),
        "variant_artifact": inside(root, f"{_CHO_60HZ_VARIANT['output_directory']}/subject_01.npz"),
        "variant_manifest": inside(
            root, f"{_CHO_60HZ_VARIANT['output_directory']}/subject_01.manifest.json"
        ),
        "variant_config": inside(root, VARIANT_CONFIG),
    }
    if (
        paths["variant_artifact"] != variant_directory / "subject_01.npz"
        or paths["variant_manifest"] != variant_directory / "subject_01.manifest.json"
    ):
        raise ValueError("Cho 60 Hz subject file aliases another namespace")
    for name, path in paths.items():
        _pinned(path, pins[name], name)
    config = load_toml(paths["variant_config"])
    if config != {"variant": _CHO_60HZ_VARIANT, "preprocessing": _CHO_PROFILE_B_60HZ}:
        raise ValueError("Cho 60 Hz variant config differs from supported contract")
    a = _read_artifact(paths["profile_a"], 512, CHO_CHANNELS, CHO_CLASSES)
    legacy = _read_artifact(paths["legacy_artifact"], 800, CHO_CHANNELS, CHO_CLASSES)
    variant = _read_artifact(paths["variant_artifact"], 800, CHO_CHANNELS, CHO_CLASSES)
    old_manifest = json.loads(paths["legacy_manifest"].read_text("utf-8"))
    new_manifest = json.loads(paths["variant_manifest"].read_text("utf-8"))
    _check_manifest(old_manifest, legacy, subject=1, profile_b=True, channels=CHO_CHANNELS)
    _check_manifest(
        new_manifest, variant, subject=1, profile_b=True, channels=CHO_CHANNELS,
        profile_b_config=_CHO_PROFILE_B_60HZ,
    )
    if any(key in old_manifest for key in ("variant", "variant_config_sha256")):
        raise ValueError("historical 50 Hz manifest declares a versioned variant")
    source_file = new_manifest.get("source_file")
    source_sha256 = new_manifest.get("source_sha256")
    if (
        new_manifest.get("variant") != _CHO_60HZ_VARIANT
        or new_manifest.get("variant_config_sha256") != pins["variant_config"]
        or source_sha256 != pins["raw_source"]
        or not isinstance(source_file, str)
        or not source_file.startswith("data/raw/moabb/cho2017/")
        or "\\" in source_file
    ):
        raise ValueError("Cho 60 Hz manifest provenance differs from pinned inputs")
    raw_root = inside(root, "data/raw/moabb/cho2017")
    raw_file = inside(root, source_file)
    if not raw_file.is_relative_to(raw_root) or not raw_file.is_file():
        raise ValueError("Cho raw source is missing or outside its namespace")
    _pinned(raw_file, pins["raw_source"], "raw_source")
    a_labels = dict(zip(a.ids, a.labels, strict=True))
    if (
        a_labels != dict(zip(legacy.ids, legacy.labels, strict=True))
        or a_labels != dict(zip(variant.ids, variant.labels, strict=True))
    ):
        raise ValueError("Profile A, 50 Hz and 60 Hz trial identities or labels differ")
    old_rows = {trial: row for row, trial in enumerate(legacy.ids)}
    new_rows = {trial: row for row, trial in enumerate(variant.ids)}
    old_signals = legacy.signals[[old_rows[trial] for trial in a.ids]]
    new_signals = variant.signals[[new_rows[trial] for trial in a.ids]]
    old_50 = _line_ratio(old_signals, 50)
    new_50 = _line_ratio(new_signals, 50)
    old_60 = _line_ratio(old_signals, 60)
    new_60 = _line_ratio(new_signals, 60)
    attenuation_db = 10.0 * math.log10(old_60 / new_60)
    if not math.isfinite(attenuation_db):
        raise ValueError("60 Hz attenuation is nonfinite")
    if any(file_digest(paths[name]) != pins[name] for name in paths):
        raise ValueError("Cho input changed during bounded signal audit")
    if file_digest(raw_file) != pins["raw_source"]:
        raise ValueError("Cho raw source changed during bounded signal audit")
    return {
        "schema": "cho-profile-b-60hz-bounded-diagnostic-v1",
        "subject": "subject_01",
        "trials": len(a.ids),
        "channels": len(CHO_CHANNELS),
        "samples_per_profile_b_trial": 800,
        "sampling_rate_hz": 200,
        "profile_a_trial_join": "complete",
        "pinned_sha256": dict(pins),
        "source_file": source_file,
        "legacy_50hz_line_to_sideband_ratio": old_50,
        "variant_50hz_line_to_sideband_ratio": new_50,
        "legacy_60hz_line_to_sideband_ratio": old_60,
        "variant_60hz_line_to_sideband_ratio": new_60,
        "variant_60hz_attenuation_db_vs_legacy": attenuation_db,
        "minimum_diagnostic_attenuation_db": MINIMUM_60HZ_ATTENUATION_DB,
        "passed": attenuation_db >= MINIMUM_60HZ_ATTENUATION_DB,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    for name in (
        "profile_a", "legacy_artifact", "legacy_manifest", "variant_artifact",
        "variant_manifest", "variant_config", "raw_source",
    ):
        parser.add_argument(f"--{name.replace('_', '-')}-sha256", required=True)
    args = parser.parse_args(argv)
    pins = {
        name: getattr(args, f"{name}_sha256") for name in (
            "profile_a", "legacy_artifact", "legacy_manifest", "variant_artifact",
            "variant_manifest", "variant_config", "raw_source",
        )
    }
    report = audit_subject_01(args.root, pins)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
