"""Data-only worker. Imports a private exact-source tree, never a model runner."""

from __future__ import annotations

import os
import runpy
import sys
import tomllib
from pathlib import Path


def build(root: Path, dataset: str, profile: str, subject: int):
    sys.path.insert(0, str(root))
    os.chdir(root)
    os.environ["GIT_CEILING_DIRECTORIES"] = str(root.parent)
    from data.runtime import configure_scientific_runtime

    configure_scientific_runtime(root)
    if dataset == "bci_iv_2a" and profile in {"profile_a", "pre_cue_control"}:
        from data.profile_a import ProfileAConfig, preprocess_subject, save_epoch_artifact

        with (root / "configs/base.toml").open("rb") as stream:
            values = tomllib.load(stream)["preprocessing"]["profile_a"]
        if profile == "profile_a":
            config = ProfileAConfig(
                bandpass_low_hz=float(values["bandpass_low_hz"]),
                bandpass_high_hz=float(values["bandpass_high_hz"]),
                resample_hz=float(values["resample_hz"]),
                baseline_duration_s=float(values["pre_cue_s"]),
                epoch_duration_s=float(values["epoch_duration_s"]),
                reference=str(values["reference"]),
            )
            arrays = preprocess_subject(subject, root, root / "data/raw/moabb", config)
        else:
            from data.pre_cue import PreCueConfig, preprocess_pre_cue_subject

            config = PreCueConfig(
                bandpass_low_hz=float(values["bandpass_low_hz"]),
                bandpass_high_hz=float(values["bandpass_high_hz"]),
                resample_hz=float(values["resample_hz"]),
                window_duration_s=float(values["pre_cue_s"]),
                reference=str(values["reference"]),
            )
            arrays = preprocess_pre_cue_subject(subject, root, root / "data/raw/moabb", config)
        signals, labels, sessions, runs, trial_indices, channel_names = arrays
        save_epoch_artifact(
            root / f"data/processed/bci_iv_2a/{profile}/subject_{subject:02d}.npz",
            signals=signals,
            labels=labels,
            sessions=sessions,
            runs=runs,
            trial_indices=trial_indices,
            channel_names=channel_names,
        )
    else:
        scripts = {
            ("bci_iv_2a", "profile_b"): "preprocess_profile_b_bci_iv_2a.py",
            ("bci_iv_2a", "pre_cue_no_future_v1"): "preprocess_pre_cue_no_future_v1.py",
            ("cho2017", "profile_b"): "preprocess_profile_b_cho2017.py",
            ("cho2017", "profile_b_60hz_v1"): "preprocess_cho_profile_b_60hz.py",
            ("mmidb", "profile_b"): "preprocess_profile_b_mmidb.py",
        }
        if profile == "profile_a" and dataset in {"cho2017", "mmidb"}:
            script = root / "scripts/preprocess_public_datasets.py"
            sys.argv = [str(script), dataset, str(subject)]
        else:
            script = root / "scripts" / scripts[(dataset, profile)]
            sys.argv = [str(script), "--subjects", str(subject)]
        runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    build(Path(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]))
