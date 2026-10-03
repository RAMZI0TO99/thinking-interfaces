"""Create Profile B artifacts for MMIDB subjects from the pinned local EDF runs."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

from data.profile_a import save_epoch_artifact, write_manifest
from data.profile_b import (
    ProfileBConfig,
    build_profile_b_summary,
    preprocess_profile_b_mmidb_subject,
)

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", nargs="+", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with (ROOT / "configs" / "base.toml").open("rb") as stream:
        base = tomllib.load(stream)
    profile = base["preprocessing"]["profile_b"]
    config = ProfileBConfig(
        bandpass_low_hz=float(profile["bandpass_low_hz"]),
        bandpass_high_hz=float(profile["bandpass_high_hz"]),
        notch_hz=float(profile["notch_hz"]),
        resample_hz=float(profile["resample_hz"]),
        reference=str(profile["reference"]),
        epoch_duration_s=float(profile["epoch_duration_s"]),
        amplitude_unit_mv=float(profile["amplitude_unit_mv"]),
        patch_duration_s=float(profile["patch_duration_s"]),
        maximum_patches=int(profile["maximum_patches"]),
    )
    raw_root = ROOT / "data" / "raw" / "mmidb"
    output_dir = ROOT / "data" / "processed" / "mmidb" / "profile_b"
    for subject_value in args.subjects:
        subject = int(subject_value)
        if not 1 <= subject <= 109:
            raise ValueError(f"subject {subject} is outside the MMIDB roster")
        signals, labels, sessions, runs, trial_indices, channel_names = (
            preprocess_profile_b_mmidb_subject(subject, ROOT, raw_root, config)
        )
        artifact = save_epoch_artifact(
            output_dir / f"subject_{subject:03d}.npz",
            signals=signals,
            labels=labels,
            sessions=sessions,
            runs=runs,
            trial_indices=trial_indices,
            channel_names=channel_names,
        )
        summary = build_profile_b_summary(
            subject=subject, signals=signals, channel_names=channel_names, config=config
        )
        manifest = write_manifest(output_dir / f"subject_{subject:03d}.manifest.json", summary)
        print(
            json.dumps(
                {"artifact": str(artifact), "manifest": str(manifest), **summary.as_dict()}
            ),
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
