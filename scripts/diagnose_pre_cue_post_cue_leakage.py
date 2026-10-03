"""Measure post-cue influence on the current pre-cue control pipeline.

This uses a synthetic, otherwise silent EEG run. It does not read or rewrite
dataset artifacts and makes no claim about contamination in real recordings.
Run from the repository root with::

    python -m scripts.diagnose_pre_cue_post_cue_leakage
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

import mne  # type: ignore[import-untyped]
import numpy as np

from data.pre_cue import PreCueConfig, preprocess_pre_cue_run

ROOT = Path(__file__).resolve().parents[1]
RAW_SAMPLING_HZ = 250.0
CUE_S = 5.0
PULSE_AFTER_CUE_S = 0.04
PULSE_AMPLITUDE_UV = 100.0
RUN_DURATION_S = 12.0


def _profile_config() -> PreCueConfig:
    with (ROOT / "configs" / "base.toml").open("rb") as stream:
        profile = tomllib.load(stream)["preprocessing"]["profile_a"]
    return PreCueConfig(
        bandpass_low_hz=float(profile["bandpass_low_hz"]),
        bandpass_high_hz=float(profile["bandpass_high_hz"]),
        resample_hz=float(profile["resample_hz"]),
        window_duration_s=float(profile["pre_cue_s"]),
        reference=str(profile["reference"]),
    )


def _raw(*, pulse: bool) -> Any:
    samples = round(RUN_DURATION_S * RAW_SAMPLING_HZ)
    signal = np.zeros((2, samples), dtype=np.float64)
    if pulse:
        pulse_sample = round((CUE_S + PULSE_AFTER_CUE_S) * RAW_SAMPLING_HZ)
        signal[0, pulse_sample] = PULSE_AMPLITUDE_UV * 1e-6
    info = mne.create_info(["C3", "C4"], sfreq=RAW_SAMPLING_HZ, ch_types="eeg")
    raw = mne.io.RawArray(signal, info, verbose=False)
    raw.set_annotations(mne.Annotations(onset=[CUE_S], duration=[0.0], description=["cue"]))
    return raw


def _max_delta_uv(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.max(np.abs(left.astype(np.float64) - right.astype(np.float64))) * 1e6)


def diagnose() -> dict[str, object]:
    """Compare identical pre-cue inputs before and after production processing."""

    config = _profile_config()
    quiet = _raw(pulse=False)
    post_cue_pulse = _raw(pulse=True)
    cue_sample = round(CUE_S * RAW_SAMPLING_HZ)
    window_samples = round(config.window_duration_s * RAW_SAMPLING_HZ)

    raw_quiet_window = quiet.get_data()[:, cue_sample - window_samples : cue_sample]
    raw_pulse_window = post_cue_pulse.get_data()[:, cue_sample - window_samples : cue_sample]
    raw_pre_cue_delta_uv = _max_delta_uv(raw_quiet_window, raw_pulse_window)

    # Inspect the same production filter and reference before resampling. This
    # isolates their contribution from any additional resampling boundary effect.
    filtered = []
    for raw in (quiet, post_cue_pulse):
        processed = raw.copy().pick(picks="eeg")
        processed.filter(
            l_freq=config.bandpass_low_hz,
            h_freq=config.bandpass_high_hz,
            method="fir",
            phase="zero",
            n_jobs=1,
            verbose=False,
        )
        processed.set_eeg_reference(ref_channels="average", projection=False, verbose=False)
        filtered.append(processed.get_data()[:, cue_sample - window_samples : cue_sample])
    filtered_pre_cue_delta_uv = _max_delta_uv(filtered[0], filtered[1])

    quiet_trials, quiet_labels, quiet_channels = preprocess_pre_cue_run(
        quiet, {"cue": 1}, config
    )
    pulse_trials, pulse_labels, pulse_channels = preprocess_pre_cue_run(
        post_cue_pulse, {"cue": 1}, config
    )
    if quiet_labels != pulse_labels or quiet_channels != pulse_channels:
        raise AssertionError("paired synthetic runs returned different metadata")
    if quiet_trials.shape != pulse_trials.shape:
        raise AssertionError("paired synthetic runs returned different epoch shapes")
    final_pre_cue_delta_uv = _max_delta_uv(quiet_trials, pulse_trials)

    return {
        "diagnostic_kind": "synthetic_post_cue_to_pre_cue_influence",
        "source_sha256": hashlib.sha256((ROOT / "data" / "pre_cue.py").read_bytes()).hexdigest(),
        "base_config_sha256": hashlib.sha256(
            (ROOT / "configs" / "base.toml").read_bytes()
        ).hexdigest(),
        "mne_version": mne.__version__,
        "profile_a": {
            "bandpass_hz": [config.bandpass_low_hz, config.bandpass_high_hz],
            "resample_hz": config.resample_hz,
            "window_duration_s": config.window_duration_s,
            "reference": config.reference,
        },
        "synthetic_input": {
            "sampling_hz": RAW_SAMPLING_HZ,
            "cue_s": CUE_S,
            "pulse_after_cue_s": PULSE_AFTER_CUE_S,
            "pulse_amplitude_uv": PULSE_AMPLITUDE_UV,
            "channels": ["C3", "C4"],
            "run_duration_s": RUN_DURATION_S,
        },
        "raw_pre_cue_max_abs_delta_uv": raw_pre_cue_delta_uv,
        "filtered_pre_cue_max_abs_delta_uv": filtered_pre_cue_delta_uv,
        "final_pre_cue_max_abs_delta_uv": final_pre_cue_delta_uv,
        "final_epoch_shape": list(quiet_trials.shape),
        "interpretation": (
            "A nonzero filtered pre-cue delta proves influence from the post-cue pulse "
            "under the current continuous-run zero-phase filter; this synthetic result "
            "does not estimate the effect in real control data."
        ),
    }


def main() -> int:
    print(json.dumps(diagnose(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
