"""Bind audited BCI Profile A episodes to unchanged Profile B encoder inputs.

Hashes and the catalog are trusted inputs. Matching metadata cannot independently
prove the original filtering or physical units; no raw-signal reconstruction,
normalization, fitting, prediction or scientific approval occurs here.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from core.config import config_digest, config_snapshot, load_toml
from evaluation.phase2_protocol import TrialCatalog, nested_episode, require_digest
from evaluation.phase2_records import verify_envelope
from scripts.audit_phase2_protocol import file_digest, inside, read_catalog, validate_protocol

BCI_CHANNELS = (
    "Fz", "FC3", "FC1", "FCz", "FC2", "FC4", "C5", "C3", "C1", "Cz", "C2",
    "C4", "C6", "CP3", "CP1", "CPz", "CP2", "CP4", "P1", "Pz", "P2", "POz",
)
BCI_CLASSES = ("feet", "left_hand", "right_hand", "tongue")
CHO_CLASSES = ("left_hand", "right_hand")
CHO_CHANNELS = (
    "Fp1", "AF7", "AF3", "F1", "F3", "F5", "F7", "FT7", "FC5", "FC3", "FC1",
    "C1", "C3", "C5", "T7", "TP7", "CP5", "CP3", "CP1", "P1", "P3", "P5",
    "P7", "P9", "PO7", "PO3", "O1", "Iz", "Oz", "POz", "Pz", "CPz", "Fpz",
    "Fp2", "AF8", "AF4", "AFz", "Fz", "F2", "F4", "F6", "F8", "FT8", "FC6",
    "FC4", "FC2", "FCz", "Cz", "C2", "C4", "C6", "T8", "TP8", "CP6", "CP4",
    "CP2", "P2", "P4", "P6", "P8", "P10", "PO8", "PO4", "O2",
)
_PROFILE_A = {
    "bandpass_low_hz": 8.0, "bandpass_high_hz": 30.0, "resample_hz": 128.0,
    "reference": "common_average", "epoch_duration_s": 4.0, "pre_cue_s": 1.0,
}
_PROFILE_B = {
    "bandpass_low_hz": 0.1, "bandpass_high_hz": 75.0, "notch_hz": 50.0,
    "resample_hz": 200.0, "reference": "original", "epoch_duration_s": 4.0,
    "amplitude_unit_mv": 0.1, "patch_duration_s": 1.0, "maximum_patches": 256,
}
_CHO_PROFILE_B_60HZ = {**_PROFILE_B, "notch_hz": 60.0}
_CHO_60HZ_VARIANT = {
    "schema_version": 1,
    "dataset": "cho2017",
    "name": "profile_b_60hz_v1",
    "output_directory": "data/processed/cho2017/profile_b_60hz_v1",
}
_CHO_60HZ_CONFIG = "configs/phase2/cho_profile_b_60hz.toml"


@dataclass(frozen=True, slots=True)
class BCIProfileBinding:
    dataset: str
    subject: str
    shots_per_class: int
    classes: tuple[str, ...]
    channel_names: tuple[str, ...]
    protocol_sha256: str
    episode_sha256: str
    profile_a_artifact_sha256: str
    profile_a_manifest_sha256: str
    profile_b_artifact_sha256: str
    profile_b_manifest_sha256: str
    profile_a_preprocessing_sha256: str
    profile_b_config_sha256: str
    base_config_sha256: str
    support_trial_ids: tuple[str, ...]
    query_trial_ids: tuple[str, ...]
    support_profile_b_rows: tuple[int, ...]
    query_profile_b_rows: tuple[int, ...]
    input_trials: int
    profile_a_rejected_trials: int
    schema: str = "bci-a-to-b-episode-v1"
    sampling_rate_hz: int = 200
    samples_per_trial: int = 800
    patch_samples: int = 200
    stored_unit_volts: float = 0.0001
    extra_input_scale: float = 1.0
    rejection_policy: str = "profile_a_frozen_threshold_only"
    target_transform_fit: str = "none"

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class BCIProfileEpisode:
    binding: BCIProfileBinding
    support_signals: NDArray[np.float32]
    query_signals: NDArray[np.float32]
    support_labels: NDArray[np.int64]
    query_labels: NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class _Artifact:
    signals: NDArray[np.float32]
    ids: tuple[str, ...]
    labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BCIProfileASubject:
    """Verified retained Profile A rows, in catalog order; no role permission implied."""

    signals: NDArray[np.float32]
    labels: NDArray[np.int64]
    artifact_rows: tuple[int, ...]
    manifest_sha256: str
    base_config_sha256: str


def load_bci_profile_a_subject(
    root: Path, protocol_config: Mapping[str, Any], catalog: TrialCatalog,
    *, profile_a_manifest_sha256: str,
) -> BCIProfileASubject:
    """Re-audit A bytes, metadata and frozen preprocessing before returning owned rows."""
    root = root.resolve()
    config: dict[str, Any] = config_snapshot(protocol_config)
    validate_protocol(config)
    if (
        catalog.dataset != "bci_iv_2a"
        or re.fullmatch(r"subject_0[1-9]", catalog.subject) is None
        or catalog.classes != BCI_CLASSES
        or tuple(config["datasets"]["bci_iv_2a"]["classes"]) != BCI_CLASSES
        or config["datasets"]["bci_iv_2a"]["artifact_directory"]
        != "data/processed/bci_iv_2a/profile_a"
    ):
        raise ValueError("binding requires the fixed BCI Profile A catalog and directory")
    directory = inside(root, "data/processed/bci_iv_2a/profile_a")
    paths = {
        "a": directory / f"{catalog.subject}.npz",
        "am": directory / f"{catalog.subject}.manifest.json",
        "base": inside(root, "configs/base.toml"),
        "threshold": inside(root, config["preparation"]["threshold_config"]),
    }
    hashes = {
        "a": catalog.artifact_sha256, "am": profile_a_manifest_sha256,
        "base": file_digest(paths["base"]), "threshold": file_digest(paths["threshold"]),
    }
    for name, sha in hashes.items():
        require_digest(sha, name)
        if file_digest(paths[name]) != sha:
            raise ValueError(f"pinned {name} bytes changed")
    base: dict[str, Any] = load_toml(paths["base"])
    if config_digest(base["preprocessing"]["profile_a"]) != config_digest(
        _PROFILE_A
    ):
        raise ValueError("base Profile A differs from the supported input contract")
    thresholds: dict[str, Any] = load_toml(paths["threshold"])
    threshold = thresholds["datasets"]["bci_iv_2a"]["artifact_threshold_volts"]
    preprocessing = config_digest({
        "profile_identity": config["preparation"]["profile_identity"],
        "threshold_config_sha256": hashes["threshold"], "dataset": "bci_iv_2a",
        "threshold": threshold,
    })
    actual, metadata = read_catalog(
        paths["a"], dataset="bci_iv_2a", classes=BCI_CLASSES,
        threshold=threshold, preprocessing_sha256=preprocessing,
    )
    if actual != catalog:
        raise ValueError("catalog differs from actual Profile A identities/labels/preprocessing")
    artifact = _read_artifact(paths["a"], 512, BCI_CHANNELS, BCI_CLASSES)
    _check_manifest(json.loads(paths["am"].read_text("utf-8")), artifact,
                    subject=int(catalog.subject[-2:]), profile_b=False)
    rows = tuple(int(i) for i in metadata["retained_artifact_indices"])
    if tuple(artifact.ids[i] for i in rows) != catalog.trial_ids:
        raise ValueError("retained Profile A row identities differ from catalog")
    signals = artifact.signals[list(rows)].copy()
    labels = np.asarray([BCI_CLASSES.index(v) for v in catalog.labels], dtype=np.int64)
    if any(file_digest(paths[name]) != sha for name, sha in hashes.items()):
        raise ValueError("Profile A input changed while binding")
    return BCIProfileASubject(signals, labels, rows, hashes["am"], hashes["base"])


def _read_artifact(
    path: Path, samples: int, channels: tuple[str, ...], classes: tuple[str, ...],
    *, expected_sha256: str | None = None,
) -> _Artifact:
    source = (
        BytesIO(_pinned_bytes(path, expected_sha256, "artifact"))
        if expected_sha256 is not None else path
    )
    with np.load(source, allow_pickle=False) as data:
        values = data["signals"]
        labels, sessions, runs = (data[key] for key in ("labels", "sessions", "runs"))
        indices, artifact_channels = data["trial_indices"], data["channel_names"]
    if (
        values.ndim != 3 or values.shape[0] < 1
        or values.shape[1:] != (len(channels), samples)
        or values.dtype != np.float32 or not np.isfinite(values).all()
        or artifact_channels.shape != (len(channels),)
        or tuple(artifact_channels.tolist()) != channels
        or indices.shape != (len(values),) or indices.dtype.kind not in "iu"
        or np.any(indices < 0)
        or any(a.shape != (len(values),) or a.dtype.kind != "U"
               for a in (labels, sessions, runs))
    ):
        raise ValueError("invalid profile shape, dtype, montage or trial metadata")
    if (
        any(str(v) not in classes for v in labels)
        or any(not str(v).strip() for a in (sessions, runs) for v in a)
    ):
        raise ValueError("invalid class, session or run")
    ids = tuple(json.dumps([str(s), str(r), int(i)], separators=(",", ":"))
                for s, r, i in zip(sessions, runs, indices, strict=True))
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate original trial identity")
    return _Artifact(values, ids, tuple(str(v) for v in labels))


def _pinned_bytes(path: Path, expected_sha256: str, name: str) -> bytes:
    """Hash the exact buffer that a loader will parse, not a separate path read."""
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError(f"pinned {name} bytes changed during load")
    return raw


def _check_manifest(
    manifest: Mapping[str, Any], artifact: _Artifact, *, subject: int, profile_b: bool,
    channels: tuple[str, ...] = BCI_CHANNELS,
    profile_b_config: Mapping[str, Any] | None = None,
) -> None:
    profile_a = dict(_PROFILE_A)
    profile_a["baseline_duration_s"] = profile_a.pop("pre_cue_s")
    expected = {
        "artifact_schema_version": 1, "subject": subject,
        "shape": list(artifact.signals.shape), "channel_names": list(channels),
        "epoch_duration_s": 4.0, "sampling_rate_hz": 200.0 if profile_b else 128.0,
        "config_sha256": config_digest(
            (_PROFILE_B if profile_b_config is None else profile_b_config)
            if profile_b else profile_a
        ),
    }
    if profile_b:
        expected.update({"artifact_kind": "profile_b", "reference": "original",
                         "amplitude_unit_mv": 0.1, "patch_samples": 200,
                         "patches_per_epoch": 4})
    else:
        expected.update({"baseline_duration_s": 1.0})
    # Canonical comparison distinguishes JSON true from integer 1.
    if config_digest({key: manifest.get(key) for key in expected}) != config_digest(expected):
        raise ValueError("profile manifest differs from the supported input contract")


def load_bci_profile_b_episode(
    root: Path,
    protocol_config: Mapping[str, Any],
    catalog: TrialCatalog,
    episode_record: Mapping[str, Any],
    *,
    shots_per_class: int,
    profile_a_manifest_sha256: str,
    profile_b_artifact_sha256: str,
    profile_b_manifest_sha256: str,
) -> BCIProfileEpisode:
    """Return owned float32 B arrays in the audited A episode's canonical order.

    Join every original A/B trial by session/run/index within the pinned BCI
    subject, requiring a bijection and equal labels even for rejected A trials.
    Reconstruct A rejection and the entire saved episode before selecting B rows.
    No query subset, tensor override, additional rejection, scaling or fit is allowed.
    Caller-provided hashes must come from an independently admitted asset inventory.
    This API binds data only; the future runner must enforce source/target roles.
    """
    root = root.resolve()
    config: dict[str, Any] = config_snapshot(protocol_config)
    shots = validate_protocol(config)
    if (catalog.dataset != "bci_iv_2a" or re.fullmatch(r"subject_0[1-9]", catalog.subject) is None
            or catalog.classes != BCI_CLASSES
            or tuple(config["datasets"]["bci_iv_2a"]["classes"]) != BCI_CLASSES):
        raise ValueError("binding requires a BCI 01..09 four-class catalog")
    manifest = nested_episode(catalog, shots=shots, protocol_sha256=config_digest(config))
    if not verify_envelope(record=episode_record, kind="episode_manifest",
                           expected_payload=manifest.payload()):
        raise ValueError("episode differs from the reconstructed audited partition")
    partition = manifest.partition(shots_per_class)
    a_dir = config["datasets"]["bci_iv_2a"]["artifact_directory"]
    if a_dir != "data/processed/bci_iv_2a/profile_a":
        raise ValueError("binding requires the declared BCI Profile A directory")
    paths = {
        "a": inside(root, f"{a_dir}/{catalog.subject}.npz"),
        "am": inside(root, f"{a_dir}/{catalog.subject}.manifest.json"),
        "b": inside(root, f"data/processed/bci_iv_2a/profile_b/{catalog.subject}.npz"),
        "bm": inside(root, f"data/processed/bci_iv_2a/profile_b/{catalog.subject}.manifest.json"),
        "base": inside(root, "configs/base.toml"),
        "threshold": inside(root, config["preparation"]["threshold_config"]),
    }
    hashes = {"a": catalog.artifact_sha256, "am": profile_a_manifest_sha256,
              "b": profile_b_artifact_sha256, "bm": profile_b_manifest_sha256,
              "base": file_digest(paths["base"]), "threshold": file_digest(paths["threshold"])}
    for name, sha in hashes.items():
        require_digest(sha, name)
        if file_digest(paths[name]) != sha:
            raise ValueError(f"pinned {name} bytes changed")
    base: dict[str, Any] = load_toml(paths["base"])
    if (config_digest(base["preprocessing"]["profile_a"]) != config_digest(_PROFILE_A)
            or config_digest(base["preprocessing"]["profile_b"]) != config_digest(_PROFILE_B)):
        raise ValueError("base profiles differ from this version's supported input contract")
    thresholds: dict[str, Any] = load_toml(paths["threshold"])
    threshold: float = thresholds["datasets"]["bci_iv_2a"]["artifact_threshold_volts"]
    preprocessing_sha = config_digest({
        "profile_identity": config["preparation"]["profile_identity"],
        "threshold_config_sha256": hashes["threshold"], "dataset": "bci_iv_2a",
        "threshold": threshold,
    })
    actual, metadata = read_catalog(paths["a"], dataset="bci_iv_2a", classes=BCI_CLASSES,
                                    threshold=threshold, preprocessing_sha256=preprocessing_sha)
    if actual != catalog:
        raise ValueError("catalog differs from actual Profile A identities/labels/preprocessing")
    a, b = (
        _read_artifact(paths["a"], 512, BCI_CHANNELS, BCI_CLASSES),
        _read_artifact(paths["b"], 800, BCI_CHANNELS, BCI_CLASSES),
    )
    subject = int(catalog.subject[-2:])
    for name, artifact, is_b in (("am", a, False), ("bm", b, True)):
        _check_manifest(json.loads(paths[name].read_text("utf-8")), artifact,
                        subject=subject, profile_b=is_b)
    if dict(zip(a.ids, a.labels, strict=True)) != dict(zip(b.ids, b.labels, strict=True)):
        raise ValueError("original A/B trial identities or labels differ")
    lookup = {trial: row for row, trial in enumerate(b.ids)}
    support_ids = tuple(catalog.trial_ids[i] for i in partition.support_indices)
    query_ids = tuple(catalog.trial_ids[i] for i in partition.query_indices)
    support_rows = tuple(lookup[trial] for trial in support_ids)
    query_rows = tuple(lookup[trial] for trial in query_ids)
    support = b.signals[list(support_rows)].copy()
    query = b.signals[list(query_rows)].copy()
    support_labels = np.asarray([BCI_CLASSES.index(catalog.labels[i])
                                 for i in partition.support_indices], dtype=np.int64)
    query_labels = np.asarray([BCI_CLASSES.index(catalog.labels[i])
                               for i in partition.query_indices], dtype=np.int64)
    if any(file_digest(paths[name]) != sha for name, sha in hashes.items()):
        raise ValueError("profile binding input changed while loading")
    binding = BCIProfileBinding(
        catalog.dataset, catalog.subject, shots_per_class, BCI_CLASSES, BCI_CHANNELS,
        manifest.protocol_sha256, manifest.sha256, hashes["a"], hashes["am"], hashes["b"],
        hashes["bm"], preprocessing_sha, config_digest(_PROFILE_B), hashes["base"],
        support_ids, query_ids, support_rows, query_rows, len(a.ids), metadata["rejected_trials"],
    )
    return BCIProfileEpisode(binding, support, query, support_labels, query_labels)


@dataclass(frozen=True, slots=True)
class ChoProfileBinding:
    dataset: str
    subject: str
    shots_per_class: int
    classes: tuple[str, ...]
    channel_names: tuple[str, ...]
    protocol_sha256: str
    episode_sha256: str
    profile_a_artifact_sha256: str
    profile_b_artifact_sha256: str
    profile_b_manifest_sha256: str
    profile_a_preprocessing_sha256: str
    profile_b_config_sha256: str
    base_config_sha256: str
    support_trial_ids: tuple[str, ...]
    query_trial_ids: tuple[str, ...]
    support_profile_b_rows: tuple[int, ...]
    query_profile_b_rows: tuple[int, ...]
    input_trials: int
    profile_a_rejected_trials: int
    schema: str = "cho-a-to-b-episode-v1"
    sampling_rate_hz: int = 200
    samples_per_trial: int = 800
    patch_samples: int = 200
    stored_unit_volts: float = 0.0001
    extra_input_scale: float = 1.0
    rejection_policy: str = "profile_a_frozen_threshold_only"
    target_transform_fit: str = "none"
    profile_a_sidecar_manifests: str = "absent_cho_identity_is_the_audited_catalog_hash"

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class ChoProfileBinding60Hz(ChoProfileBinding):
    """Versioned Cho binding with explicit 60 Hz config and raw source provenance."""

    variant_config_sha256: str = field(kw_only=True)
    source_file: str = field(kw_only=True)
    source_sha256: str = field(kw_only=True)
    schema: str = "cho-a-to-b-episode-60hz-v1"


@dataclass(frozen=True, slots=True)
class ChoProfileEpisode:
    binding: ChoProfileBinding
    support_signals: NDArray[np.float32]
    query_signals: NDArray[np.float32]
    support_labels: NDArray[np.int64]
    query_labels: NDArray[np.int64]


def load_cho_profile_b_episode(
    root: Path,
    protocol_config: Mapping[str, Any],
    catalog: TrialCatalog,
    episode_record: Mapping[str, Any],
    *,
    shots_per_class: int,
    profile_b_artifact_sha256: str,
    profile_b_manifest_sha256: str,
    variant_config_sha256: str | None = None,
) -> ChoProfileEpisode:
    """Return owned float32 Cho Profile B arrays in the audited episode's order.

    Cho Profile A carries no sidecar manifests: its identity is the audited
    catalog's artifact hash plus the frozen threshold profile, both re-verified
    here against the bytes on disk. Every original A/B trial joins by
    session/run/index with equal labels; the saved episode is reconstructed
    before any Profile B row is selected. No subset override, scaling or fit.
    """
    root = root.resolve()
    config: dict[str, Any] = config_snapshot(protocol_config)
    shots = validate_protocol(config)
    if (
        catalog.dataset != "cho2017"
        or re.fullmatch(r"subject_(0[1-9]|[1-4][0-9]|5[0-2])", catalog.subject) is None
        or catalog.classes != CHO_CLASSES
        or tuple(config["datasets"]["cho2017"]["classes"]) != CHO_CLASSES
        or config["datasets"]["cho2017"]["artifact_directory"]
        != "data/processed/cho2017/profile_a"
    ):
        raise ValueError("binding requires the fixed Cho2017 two-class catalog and directory")
    manifest = nested_episode(catalog, shots=shots, protocol_sha256=config_digest(config))
    if not verify_envelope(record=episode_record, kind="episode_manifest",
                           expected_payload=manifest.payload()):
        raise ValueError("episode differs from the reconstructed audited partition")
    partition = manifest.partition(shots_per_class)
    versioned = variant_config_sha256 is not None
    b_directory: str = (
        str(_CHO_60HZ_VARIANT["output_directory"])
        if versioned else "data/processed/cho2017/profile_b"
    )
    if versioned:
        lexical_directory = root / b_directory
        if lexical_directory.resolve() != lexical_directory:
            raise ValueError("Cho 60 Hz output aliases or escapes its versioned namespace")
    paths = {
        "a": inside(root, f"data/processed/cho2017/profile_a/{catalog.subject}.npz"),
        "b": inside(root, f"{b_directory}/{catalog.subject}.npz"),
        "bm": inside(root, f"{b_directory}/{catalog.subject}.manifest.json"),
        "base": inside(root, "configs/base.toml"),
        "threshold": inside(root, config["preparation"]["threshold_config"]),
    }
    if versioned:
        for name, suffix in (("b", ".npz"), ("bm", ".manifest.json")):
            if paths[name] != lexical_directory / f"{catalog.subject}{suffix}":
                raise ValueError("Cho 60 Hz subject file aliases another namespace")
        paths["variant"] = inside(root, _CHO_60HZ_CONFIG)
    hashes = {"a": catalog.artifact_sha256,
              "b": profile_b_artifact_sha256, "bm": profile_b_manifest_sha256,
              "base": file_digest(paths["base"]), "threshold": file_digest(paths["threshold"])}
    if variant_config_sha256 is not None:
        hashes["variant"] = variant_config_sha256
    for name, sha in hashes.items():
        require_digest(sha, name)
        if file_digest(paths[name]) != sha:
            raise ValueError(f"pinned {name} bytes changed")
    base: dict[str, Any] = load_toml(paths["base"])
    if (config_digest(base["preprocessing"]["profile_a"]) != config_digest(_PROFILE_A)
            or config_digest(base["preprocessing"]["profile_b"]) != config_digest(_PROFILE_B)):
        raise ValueError("base profiles differ from this version's supported input contract")
    profile_b_config = _PROFILE_B
    if versioned:
        variant_document: dict[str, Any] = load_toml(paths["variant"])
        if variant_document != {
            "variant": _CHO_60HZ_VARIANT, "preprocessing": _CHO_PROFILE_B_60HZ
        }:
            raise ValueError("Cho 60 Hz variant config differs from the supported contract")
        profile_b_config = _CHO_PROFILE_B_60HZ
    thresholds: dict[str, Any] = load_toml(paths["threshold"])
    threshold: float = thresholds["datasets"]["cho2017"]["artifact_threshold_volts"]
    preprocessing_sha = config_digest({
        "profile_identity": config["preparation"]["profile_identity"],
        "threshold_config_sha256": hashes["threshold"], "dataset": "cho2017",
        "threshold": threshold,
    })
    actual, metadata = read_catalog(paths["a"], dataset="cho2017", classes=CHO_CLASSES,
                                    threshold=threshold, preprocessing_sha256=preprocessing_sha)
    if actual != catalog:
        raise ValueError("catalog differs from actual Profile A identities/labels/preprocessing")
    a, b = (
        _read_artifact(
            paths["a"], 512, CHO_CHANNELS, CHO_CLASSES,
            expected_sha256=hashes["a"],
        ),
        _read_artifact(
            paths["b"], 800, CHO_CHANNELS, CHO_CLASSES,
            expected_sha256=hashes["b"],
        ),
    )
    b_manifest = json.loads(_pinned_bytes(paths["bm"], hashes["bm"], "bm").decode("utf-8"))
    _check_manifest(b_manifest, b, subject=int(catalog.subject[-2:]),
                    profile_b=True, channels=CHO_CHANNELS,
                    profile_b_config=profile_b_config)
    source_file = ""
    source_sha256 = ""
    if versioned:
        source_file = b_manifest.get("source_file")
        source_sha256 = b_manifest.get("source_sha256")
        if (
            b_manifest.get("variant") != _CHO_60HZ_VARIANT
            or b_manifest.get("variant_config_sha256") != variant_config_sha256
            or not isinstance(source_file, str)
            or not source_file.startswith("data/raw/moabb/cho2017/")
            or "\\" in source_file
            or not isinstance(source_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None
        ):
            raise ValueError("Cho 60 Hz manifest variant or source provenance differs")
        raw_file = inside(root, source_file)
        raw_root = inside(root, "data/raw/moabb/cho2017")
        if not raw_file.is_relative_to(raw_root) or not raw_file.is_file():
            raise ValueError("Cho 60 Hz manifest source file is missing or outside raw root")
        if file_digest(raw_file) != source_sha256:
            raise ValueError("Cho 60 Hz raw source bytes changed")
        paths["source"] = raw_file
        hashes["source"] = source_sha256
    if dict(zip(a.ids, a.labels, strict=True)) != dict(zip(b.ids, b.labels, strict=True)):
        raise ValueError("original A/B trial identities or labels differ")
    lookup = {trial: row for row, trial in enumerate(b.ids)}
    support_ids = tuple(catalog.trial_ids[i] for i in partition.support_indices)
    query_ids = tuple(catalog.trial_ids[i] for i in partition.query_indices)
    support_rows = tuple(lookup[trial] for trial in support_ids)
    query_rows = tuple(lookup[trial] for trial in query_ids)
    support = b.signals[list(support_rows)].copy()
    query = b.signals[list(query_rows)].copy()
    support_labels = np.asarray([CHO_CLASSES.index(catalog.labels[i])
                                 for i in partition.support_indices], dtype=np.int64)
    query_labels = np.asarray([CHO_CLASSES.index(catalog.labels[i])
                               for i in partition.query_indices], dtype=np.int64)
    if any(file_digest(paths[name]) != sha for name, sha in hashes.items()):
        raise ValueError("profile binding input changed while loading")
    binding_args = (
        catalog.dataset, catalog.subject, shots_per_class, CHO_CLASSES, CHO_CHANNELS,
        manifest.protocol_sha256, manifest.sha256, hashes["a"], hashes["b"],
        hashes["bm"], preprocessing_sha, config_digest(profile_b_config), hashes["base"],
        support_ids, query_ids, support_rows, query_rows, len(a.ids),
        metadata["rejected_trials"],
    )
    binding: ChoProfileBinding
    if versioned:
        assert variant_config_sha256 is not None
        binding = ChoProfileBinding60Hz(
            *binding_args, variant_config_sha256=variant_config_sha256,
            source_file=source_file, source_sha256=source_sha256,
        )
    else:
        binding = ChoProfileBinding(*binding_args)
    return ChoProfileEpisode(binding, support, query, support_labels, query_labels)


@dataclass(frozen=True, slots=True)
class BCIProfileAssets:
    profile_a_manifest_sha256: str
    profile_b_artifact_sha256: str
    profile_b_manifest_sha256: str

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            require_digest(value, name)


@dataclass(frozen=True, slots=True)
class ChoProfileAssets:
    """Pinned Profile B digests for Cho subjects; Profile A has no sidecars."""

    profile_b_artifact_sha256: str
    profile_b_manifest_sha256: str

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            require_digest(value, name)


@dataclass(frozen=True, slots=True)
class ChoProfileAssets60Hz(ChoProfileAssets):
    """Pins an entire subject to the isolated Cho 60 Hz artifact namespace."""

    variant_config_sha256: str


DATASET_CHANNELS = {"bci_iv_2a": BCI_CHANNELS, "cho2017": CHO_CHANNELS}
DATASET_CLASSES = {"bci_iv_2a": BCI_CLASSES, "cho2017": CHO_CLASSES}


def dataset_cohort(
    protocol_config: Mapping[str, Any], catalogs: tuple[TrialCatalog, ...]
) -> tuple[str, tuple[str, ...], tuple[str, ...], frozenset[str]]:
    """Declared dataset montage, classes and complete subject cohort."""
    config: dict[str, Any] = config_snapshot(protocol_config)
    dataset = catalogs[0].dataset
    datasets: dict[str, Any] = config["datasets"]
    if dataset not in DATASET_CHANNELS or dataset not in datasets:
        raise ValueError(f"unsupported dataset for Profile B episodes: {dataset}")
    settings: dict[str, Any] = datasets[dataset]
    expected = int(settings["expected_subjects"])
    width = 3 if expected > 99 else 2  # MMIDB uses three-digit subject names.
    subjects = frozenset(f"subject_{i:0{width}d}" for i in range(1, expected + 1))
    if {c.subject for c in catalogs} != subjects:
        raise ValueError(
            f"complete {dataset} cohort of {expected} subjects is required, never silently pruned"
        )
    return dataset, DATASET_CHANNELS[dataset], DATASET_CLASSES[dataset], subjects


MMIDB_CLASSES = ("left_fist", "right_fist")
MMIDB_CHANNELS = (
    "FC5", "FC3", "FC1", "FCz", "FC2", "FC4", "FC6", "C5",
    "C3", "C1", "Cz", "C2", "C4", "C6", "CP5", "CP3",
    "CP1", "CPz", "CP2", "CP4", "CP6", "Fp1", "Fpz", "Fp2",
    "AF7", "AF3", "AFz", "AF4", "AF8", "F7", "F5", "F3",
    "F1", "Fz", "F2", "F4", "F6", "F8", "FT7", "FT8",
    "T7", "T8", "T9", "T10", "TP7", "TP8", "P7", "P5",
    "P3", "P1", "Pz", "P2", "P4", "P6", "P8", "PO7",
    "PO3", "POz", "PO4", "PO8", "O1", "Oz", "O2", "Iz",
)
DATASET_CHANNELS["mmidb"] = MMIDB_CHANNELS
DATASET_CLASSES["mmidb"] = MMIDB_CLASSES


@dataclass(frozen=True, slots=True)
class MMIDBProfileAssets:
    """Pinned Profile B digests for MMIDB subjects; Profile A has no sidecars."""

    profile_b_artifact_sha256: str
    profile_b_manifest_sha256: str

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            require_digest(value, name)


@dataclass(frozen=True, slots=True)
class MMIDBProfileBinding:
    dataset: str
    subject: str
    shots_per_class: int
    classes: tuple[str, ...]
    channel_names: tuple[str, ...]
    protocol_sha256: str
    episode_sha256: str
    profile_a_artifact_sha256: str
    profile_b_artifact_sha256: str
    profile_b_manifest_sha256: str
    profile_a_preprocessing_sha256: str
    profile_b_config_sha256: str
    base_config_sha256: str
    support_trial_ids: tuple[str, ...]
    query_trial_ids: tuple[str, ...]
    support_profile_b_rows: tuple[int, ...]
    query_profile_b_rows: tuple[int, ...]
    input_trials: int
    profile_a_rejected_trials: int
    schema: str = "mmidb-a-to-b-episode-v1"
    sampling_rate_hz: int = 200
    samples_per_trial: int = 800
    patch_samples: int = 200
    stored_unit_volts: float = 0.0001
    extra_input_scale: float = 1.0
    rejection_policy: str = "profile_a_frozen_threshold_only"
    target_transform_fit: str = "none"
    profile_a_sidecar_manifests: str = "absent_mmidb_identity_is_the_audited_catalog_hash"
    profile_b_resample_policy: str = "upsample_to_target_before_filter_documented"

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class MMIDBProfileEpisode:
    binding: MMIDBProfileBinding
    support_signals: NDArray[np.float32]
    query_signals: NDArray[np.float32]
    support_labels: NDArray[np.int64]
    query_labels: NDArray[np.int64]


def load_mmidb_profile_b_episode(
    root: Path,
    protocol_config: Mapping[str, Any],
    catalog: TrialCatalog,
    episode_record: Mapping[str, Any],
    *,
    shots_per_class: int,
    profile_b_artifact_sha256: str,
    profile_b_manifest_sha256: str,
) -> MMIDBProfileEpisode:
    """Return owned float32 MMIDB Profile B arrays in the audited episode's order.

    MMIDB mirrors the Cho convention: Profile A identity is the audited catalog
    hash (no sidecar manifests), every original A/B trial joins by
    session/run/index with equal labels, and the saved episode is reconstructed
    before any row is selected. Two audited-ineligible subjects (079, 100) have
    no episode records and cannot bind.
    """
    root = root.resolve()
    config: dict[str, Any] = config_snapshot(protocol_config)
    shots = validate_protocol(config)
    if (
        catalog.dataset != "mmidb"
        or re.fullmatch(r"subject_0(?:0[1-9]|[1-9][0-9])|subject_10[0-9]", catalog.subject) is None
        or catalog.subject in {"subject_079", "subject_100"}
        or catalog.classes != MMIDB_CLASSES
        or tuple(config["datasets"]["mmidb"]["classes"]) != MMIDB_CLASSES
        or config["datasets"]["mmidb"]["artifact_directory"]
        != "data/processed/mmidb/profile_a"
    ):
        raise ValueError(
            "binding requires an eligible MMIDB catalog; subjects 079 and 100 "
            "have no audited episodes"
        )
    manifest = nested_episode(catalog, shots=shots, protocol_sha256=config_digest(config))
    if not verify_envelope(record=episode_record, kind="episode_manifest",
                           expected_payload=manifest.payload()):
        raise ValueError("episode differs from the reconstructed audited partition")
    partition = manifest.partition(shots_per_class)
    paths = {
        "a": inside(root, f"data/processed/mmidb/profile_a/{catalog.subject}.npz"),
        "b": inside(root, f"data/processed/mmidb/profile_b/{catalog.subject}.npz"),
        "bm": inside(root, f"data/processed/mmidb/profile_b/{catalog.subject}.manifest.json"),
        "base": inside(root, "configs/base.toml"),
        "threshold": inside(root, config["preparation"]["threshold_config"]),
    }
    hashes = {"a": catalog.artifact_sha256,
              "b": profile_b_artifact_sha256, "bm": profile_b_manifest_sha256,
              "base": file_digest(paths["base"]), "threshold": file_digest(paths["threshold"])}
    for name, sha in hashes.items():
        require_digest(sha, name)
        if file_digest(paths[name]) != sha:
            raise ValueError(f"pinned {name} bytes changed")
    base: dict[str, Any] = load_toml(paths["base"])
    if (config_digest(base["preprocessing"]["profile_a"]) != config_digest(_PROFILE_A)
            or config_digest(base["preprocessing"]["profile_b"]) != config_digest(_PROFILE_B)):
        raise ValueError("base profiles differ from this version's supported input contract")
    thresholds: dict[str, Any] = load_toml(paths["threshold"])
    threshold: float = thresholds["datasets"]["mmidb"]["artifact_threshold_volts"]
    preprocessing_sha = config_digest({
        "profile_identity": config["preparation"]["profile_identity"],
        "threshold_config_sha256": hashes["threshold"], "dataset": "mmidb",
        "threshold": threshold,
    })
    actual, metadata = read_catalog(paths["a"], dataset="mmidb", classes=MMIDB_CLASSES,
                                    threshold=threshold, preprocessing_sha256=preprocessing_sha)
    if actual != catalog:
        raise ValueError("catalog differs from actual Profile A identities/labels/preprocessing")
    a, b = (
        _read_artifact(paths["a"], 512, MMIDB_CHANNELS, MMIDB_CLASSES),
        _read_artifact(paths["b"], 800, MMIDB_CHANNELS, MMIDB_CLASSES),
    )
    _check_manifest(json.loads(paths["bm"].read_text("utf-8")), b,
                    subject=int(catalog.subject[-3:]), profile_b=True, channels=MMIDB_CHANNELS)
    if dict(zip(a.ids, a.labels, strict=True)) != dict(zip(b.ids, b.labels, strict=True)):
        raise ValueError("original A/B trial identities or labels differ")
    lookup = {trial: row for row, trial in enumerate(b.ids)}
    support_ids = tuple(catalog.trial_ids[i] for i in partition.support_indices)
    query_ids = tuple(catalog.trial_ids[i] for i in partition.query_indices)
    support_rows = tuple(lookup[trial] for trial in support_ids)
    query_rows = tuple(lookup[trial] for trial in query_ids)
    support = b.signals[list(support_rows)].copy()
    query = b.signals[list(query_rows)].copy()
    support_labels = np.asarray([MMIDB_CLASSES.index(catalog.labels[i])
                                 for i in partition.support_indices], dtype=np.int64)
    query_labels = np.asarray([MMIDB_CLASSES.index(catalog.labels[i])
                               for i in partition.query_indices], dtype=np.int64)
    if any(file_digest(paths[name]) != sha for name, sha in hashes.items()):
        raise ValueError("profile binding input changed while loading")
    binding = MMIDBProfileBinding(
        catalog.dataset, catalog.subject, shots_per_class, MMIDB_CLASSES, MMIDB_CHANNELS,
        manifest.protocol_sha256, manifest.sha256, hashes["a"], hashes["b"],
        hashes["bm"], preprocessing_sha, config_digest(_PROFILE_B), hashes["base"],
        support_ids, query_ids, support_rows, query_rows, len(a.ids),
        metadata["rejected_trials"],
    )
    
    return MMIDBProfileEpisode(binding, support, query, support_labels, query_labels)
