"""Proposed versioned BCI IV 2a pre-cue control with no post-cue input.

Each raw EEG prefix ends strictly before its cue. Only that prefix is
filtered, referenced and resampled. This module does not write artifacts or
replace the historical continuous-run pre-cue control.
"""

from __future__ import annotations

import hashlib
import re
import tomllib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import mne  # type: ignore[import-untyped]
import numpy as np
from numpy.typing import NDArray

from core.config import config_digest

FloatArray = NDArray[np.float32]
CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "pre_cue_no_future_v1.toml"
BCI_EEG_CHANNELS = (
    "Fz", "FC3", "FC1", "FCz", "FC2", "FC4", "C5", "C3", "C1", "Cz", "C2",
    "C4", "C6", "CP3", "CP1", "CPz", "CP2", "CP4", "P1", "Pz", "P2", "POz",
)
BCI_EVENT_ID: Mapping[str, int] = MappingProxyType(
    {"left_hand": 1, "right_hand": 2, "feet": 3, "tongue": 4}
)
CONTROL_ID = "pre_cue_no_future_v1"
ARTIFACT_KIND = "pre_cue_no_future_control_v1"
MANIFEST_KIND = "pre_cue_no_future_manifest_v1"
OUTPUT_NAMESPACE = "data/processed/bci_iv_2a/pre_cue_no_future_v1"


@dataclass(frozen=True, slots=True)
class NoFuturePreCueConfig:
    schema_version: int
    dataset: str
    control_id: str
    artifact_kind: str
    manifest_kind: str
    status: str
    output_namespace: str
    raw_sampling_rate_hz: float
    channel_names: tuple[str, ...]
    bandpass_low_hz: float
    bandpass_high_hz: float
    filter_method: str
    filter_phase: str
    reference: str
    resample_hz: float
    window_duration_s: float
    prefix_policy: str
    minimum_prefix_policy: str
    window_policy: str
    config_file_sha256: str

    def __post_init__(self) -> None:
        expected = {
            "schema_version": 1,
            "dataset": "bci_iv_2a",
            "control_id": CONTROL_ID,
            "artifact_kind": ARTIFACT_KIND,
            "manifest_kind": MANIFEST_KIND,
            "status": "proposed_unratified",
            "output_namespace": OUTPUT_NAMESPACE,
            "raw_sampling_rate_hz": 250.0,
            "channel_names": BCI_EEG_CHANNELS,
            "bandpass_low_hz": 8.0,
            "bandpass_high_hz": 30.0,
            "filter_method": "fir",
            "filter_phase": "zero",
            "reference": "common_average",
            "resample_hz": 128.0,
            "window_duration_s": 1.0,
            "prefix_policy": "raw_eeg_strictly_before_cue_before_filter_and_resample",
            "minimum_prefix_policy": "at_least_one_raw_window_and_full_fir_kernel",
            "window_policy": "last_resampled_second_mean_center_each_channel",
        }
        actual = asdict(self)
        actual.pop("config_file_sha256")
        numeric_fields = (
            "raw_sampling_rate_hz", "bandpass_low_hz", "bandpass_high_hz",
            "resample_hz", "window_duration_s",
        )
        if (
            actual != expected
            or type(self.schema_version) is not int
            or type(self.channel_names) is not tuple
            or any(type(getattr(self, name)) is not float for name in numeric_fields)
            or any(
                type(value) is not str
                for name, value in actual.items()
                if name not in (*numeric_fields, "schema_version", "channel_names")
            )
        ):
            raise ValueError("no-future pre-cue config differs from version 1 contract")
        if (
            type(self.config_file_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", self.config_file_sha256) is None
        ):
            raise ValueError("config file SHA-256 is required")


@dataclass(frozen=True, slots=True)
class NoFuturePreCueSummary:
    artifact_schema_version: int
    artifact_kind: str
    manifest_kind: str
    control_id: str
    status: str
    subject: int
    shape: tuple[int, int, int]
    channel_names: tuple[str, ...]
    sampling_rate_hz: float
    window_duration_s: float
    minimum_prefix_samples: int
    prefix_policy: str
    filter_phase: str
    mne_version: str
    output_namespace: str
    config_file_sha256: str
    config_sha256: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def load_no_future_config(path: Path = CONFIG_PATH) -> NoFuturePreCueConfig:
    """Load and pin the distinct proposal, rejecting extra or changed fields."""

    config_bytes = path.read_bytes()
    document = tomllib.loads(config_bytes.decode("utf-8"))
    if set(document) != {"identity", "preprocessing"}:
        raise ValueError("no-future pre-cue config sections differ")
    identity = document["identity"]
    preprocessing = document["preprocessing"]
    if not isinstance(identity, dict) or not isinstance(preprocessing, dict):
        raise ValueError("no-future pre-cue config sections must be mappings")
    expected_identity = {
        "schema_version", "dataset", "control_id", "artifact_kind", "manifest_kind",
        "status", "output_namespace",
    }
    expected_preprocessing = {
        "raw_sampling_rate_hz", "channel_names", "bandpass_low_hz", "bandpass_high_hz",
        "filter_method", "filter_phase", "reference", "resample_hz", "window_duration_s",
        "prefix_policy", "minimum_prefix_policy", "window_policy",
    }
    if set(identity) != expected_identity or set(preprocessing) != expected_preprocessing:
        raise ValueError("no-future pre-cue config fields differ")
    channels = preprocessing["channel_names"]
    if type(channels) is not list or any(type(name) is not str for name in channels):
        raise ValueError("explicit ordered EEG channels are required")
    return NoFuturePreCueConfig(
        **identity,
        **{**preprocessing, "channel_names": tuple(channels)},
        config_file_sha256=hashlib.sha256(config_bytes).hexdigest(),
    )


def minimum_prefix_samples(config: NoFuturePreCueConfig) -> int:
    """Require a complete raw window and enough history for the full FIR kernel."""

    if not isinstance(config, NoFuturePreCueConfig):
        raise TypeError("NoFuturePreCueConfig is required")
    kernel = mne.filter.create_filter(
        None,
        sfreq=config.raw_sampling_rate_hz,
        l_freq=config.bandpass_low_hz,
        h_freq=config.bandpass_high_hz,
        method=config.filter_method,
        phase=config.filter_phase,
        verbose=False,
    )
    return max(round(config.window_duration_s * config.raw_sampling_rate_hz), len(kernel))


def no_future_window(
    eeg_raw: Any,
    *,
    cue_sample: int,
    config: NoFuturePreCueConfig,
) -> FloatArray:
    """Process only raw EEG samples [0, cue), then take the last second."""

    if not isinstance(config, NoFuturePreCueConfig):
        raise TypeError("NoFuturePreCueConfig is required")
    if (
        eeg_raw.first_samp != 0
        or float(eeg_raw.info["sfreq"]) != config.raw_sampling_rate_hz
        or tuple(eeg_raw.ch_names) != config.channel_names
        or any(kind != "eeg" for kind in eeg_raw.get_channel_types())
    ):
        raise ValueError("raw EEG sampling, first sample or canonical 22 channels differ")
    if type(cue_sample) is not int or cue_sample > eeg_raw.n_times:
        raise ValueError("cue sample is invalid")
    floor = minimum_prefix_samples(config)
    if cue_sample < floor:
        raise ValueError("cue has a short raw EEG prefix for the full FIR and pre-cue window")
    # Data at cue_sample and every later sample are excluded before any signal
    # processing. Force an owned array because RawArray may otherwise alias it.
    prefix = np.array(
        eeg_raw.get_data(start=0, stop=cue_sample), dtype=np.float64, copy=True
    )
    if prefix.shape != (len(config.channel_names), cue_sample):
        raise ValueError("raw EEG prefix has unexpected dimensions")
    processed = mne.io.RawArray(prefix, eeg_raw.info.copy(), verbose=False)
    processed.filter(
        l_freq=config.bandpass_low_hz,
        h_freq=config.bandpass_high_hz,
        method=config.filter_method,
        phase=config.filter_phase,
        n_jobs=1,
        verbose=False,
    )
    processed.set_eeg_reference(ref_channels="average", projection=False, verbose=False)
    processed.resample(config.resample_hz, npad="auto", n_jobs=1, verbose=False)
    expected_length = round(cue_sample * config.resample_hz / config.raw_sampling_rate_hz)
    if processed.n_times != expected_length:
        raise ValueError("prefix resampling endpoint differs from cue time")
    window_samples = round(config.window_duration_s * config.resample_hz)
    if processed.n_times < window_samples:
        raise ValueError("resampled prefix has no complete one-second window")
    window = processed.get_data(
        start=processed.n_times - window_samples, stop=processed.n_times
    )
    return np.asarray(window - window.mean(axis=1, keepdims=True), dtype=np.float32)


def preprocess_no_future_run(
    raw: Any,
    event_id: Mapping[str, int],
    config: NoFuturePreCueConfig,
) -> tuple[FloatArray, tuple[str, ...], tuple[str, ...]]:
    """Return one no-future pre-cue window for each annotated BCI cue."""

    if raw.first_samp != 0 or float(raw.info["sfreq"]) != config.raw_sampling_rate_hz:
        raise ValueError("BCI raw start or sampling rate differs")
    if (
        dict(event_id) != BCI_EVENT_ID
        or any(type(code) is not int for code in event_id.values())
    ):
        raise ValueError("canonical four-class BCI event mapping is required")
    events, _ = mne.events_from_annotations(
        raw, event_id=dict(event_id), regexp=None, verbose=False
    )
    if len(events) == 0:
        raise ValueError("no annotated BCI cue events were available")
    eeg = raw.copy().pick(picks="eeg")
    if tuple(eeg.ch_names) != config.channel_names:
        raise ValueError("canonical BCI EEG channel order differs")
    labels_by_code = {code: label for label, code in event_id.items()}
    windows: list[FloatArray] = []
    labels: list[str] = []
    for event in events:
        code = int(event[2])
        if code not in labels_by_code:
            raise ValueError("annotated event code is not declared")
        windows.append(no_future_window(eeg, cue_sample=int(event[0]), config=config))
        labels.append(labels_by_code[code])
    return np.stack(windows), tuple(labels), tuple(eeg.ch_names)


def build_no_future_summary(
    *,
    subject: int,
    signals: FloatArray,
    channel_names: tuple[str, ...],
    config: NoFuturePreCueConfig,
) -> NoFuturePreCueSummary:
    """Describe a future artifact under a separate manifest identity; write nothing."""

    expected_samples = round(config.window_duration_s * config.resample_hz)
    if (
        type(subject) is not int or not 1 <= subject <= 9
        or signals.ndim != 3
        or signals.shape[0] < 1
        or signals.shape[1:] != (len(config.channel_names), expected_samples)
        or signals.dtype != np.float32
        or not np.isfinite(signals).all()
        or channel_names != config.channel_names
    ):
        raise ValueError("no-future artifact shape, channel order or signal values differ")
    return NoFuturePreCueSummary(
        artifact_schema_version=1,
        artifact_kind=config.artifact_kind,
        manifest_kind=config.manifest_kind,
        control_id=config.control_id,
        status=config.status,
        subject=subject,
        shape=(int(signals.shape[0]), int(signals.shape[1]), int(signals.shape[2])),
        channel_names=channel_names,
        sampling_rate_hz=config.resample_hz,
        window_duration_s=config.window_duration_s,
        minimum_prefix_samples=minimum_prefix_samples(config),
        prefix_policy=config.prefix_policy,
        filter_phase=config.filter_phase,
        mne_version=mne.__version__,
        output_namespace=config.output_namespace,
        config_file_sha256=config.config_file_sha256,
        config_sha256=config_digest(asdict(config)),
    )
