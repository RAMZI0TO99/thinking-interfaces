"""Create configured Profile A epoch artifacts for BCI IV 2a subjects."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from data.bci_iv_2a import download_subject
from data.profile_a import (
    ProfileAConfig,
    build_summary,
    preprocess_subject,
    save_epoch_artifact,
    write_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with (ROOT / "configs" / "base.toml").open("rb") as stream:
        base = tomllib.load(stream)
    with (ROOT / "configs" / "bci_iv_2a.toml").open("rb") as stream:
        dataset = tomllib.load(stream)["dataset"]

    profile = base["preprocessing"]["profile_a"]
    config = ProfileAConfig(
        bandpass_low_hz=float(profile["bandpass_low_hz"]),
        bandpass_high_hz=float(profile["bandpass_high_hz"]),
        resample_hz=float(profile["resample_hz"]),
        baseline_duration_s=float(profile["pre_cue_s"]),
        epoch_duration_s=float(profile["epoch_duration_s"]),
        reference=str(profile["reference"]),
    )
    raw_root = ROOT / dataset["raw_root"]
    for subject_value in dataset["subjects"]:
        subject = int(subject_value)
        signals, labels, sessions, runs, trial_indices, channel_names = preprocess_subject(
            subject,
            ROOT,
            raw_root,
            config,
        )
        output_dir = ROOT / "data" / "processed" / "bci_iv_2a" / "profile_a"
        artifact = save_epoch_artifact(
            output_dir / f"subject_{subject:02d}.npz",
            signals=signals,
            labels=labels,
            sessions=sessions,
            runs=runs,
            trial_indices=trial_indices,
            channel_names=channel_names,
        )
        source_files = download_subject(subject, raw_root)
        summary = build_summary(
            subject=subject,
            signals=signals,
            labels=labels,
            sessions=sessions,
            runs=runs,
            trial_indices=trial_indices,
            channel_names=channel_names,
            config=config,
            source_files=source_files,
        )
        manifest = write_manifest(output_dir / f"subject_{subject:02d}.manifest.json", summary)
        print(
            json.dumps(
                {
                    "artifact": str(artifact),
                    "manifest": str(manifest),
                    "summary": summary.as_dict(),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
