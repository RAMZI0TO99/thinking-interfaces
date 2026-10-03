"""Cho2017 Profile A subject loading with catalog-hash identity; engineering only."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np

from core.config import config_digest, config_snapshot, load_toml
from evaluation.phase2_profile_binding import (
    CHO_CHANNELS,
    CHO_CLASSES,
    MMIDB_CHANNELS,
    MMIDB_CLASSES,
    BCIProfileASubject,
)
from evaluation.phase2_protocol import TrialCatalog
from scripts.audit_phase2_protocol import file_digest, read_catalog, validate_protocol


def load_cho_profile_a_subject(
    root: Path, protocol_config: Mapping[str, Any], catalog: TrialCatalog
) -> BCIProfileASubject:
    """Re-audit Cho Profile A bytes and return owned retained rows.

    Cho Profile A has no sidecar manifests: identity is the audited catalog's
    artifact hash plus the frozen threshold profile, both re-verified here
    against the bytes on disk. The returned mapping carries float32 signals in
    catalog order, integer labels, the retained row indices and the pinned
    base-config digest.
    """
    root = root.resolve()
    config: dict[str, Any] = config_snapshot(protocol_config)
    validate_protocol(config)
    settings: dict[str, Any] = config["datasets"]["cho2017"]
    if (
        catalog.dataset != "cho2017"
        or catalog.classes != CHO_CLASSES
        or tuple(settings["classes"]) != CHO_CLASSES
        or settings["artifact_directory"] != "data/processed/cho2017/profile_a"
    ):
        raise ValueError("loading requires the fixed Cho2017 two-class catalog and directory")
    path = root / "data/processed/cho2017/profile_a" / f"{catalog.subject}.npz"
    base_path = root / "configs/base.toml"
    threshold_path = root / config["preparation"]["threshold_config"]
    thresholds: dict[str, Any] = load_toml(threshold_path)
    threshold = thresholds["datasets"]["cho2017"]["artifact_threshold_volts"]
    preprocessing = config_digest({
        "profile_identity": config["preparation"]["profile_identity"],
        "threshold_config_sha256": file_digest(threshold_path),
        "dataset": "cho2017",
        "threshold": threshold,
    })
    actual, metadata = read_catalog(
        path, dataset="cho2017", classes=CHO_CLASSES,
        threshold=threshold, preprocessing_sha256=preprocessing,
    )
    if actual != catalog:
        raise ValueError("catalog differs from actual Profile A identities/labels/preprocessing")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != catalog.artifact_sha256:
        raise ValueError("Profile A parse buffer differs from the audited catalog bytes")
    with np.load(BytesIO(raw), allow_pickle=False) as data:
        signals = data["signals"]
        labels = [str(v) for v in data["labels"]]
        channels = tuple(str(v) for v in data["channel_names"])
    if (
        signals.ndim != 3
        or signals.shape[1:] != (len(CHO_CHANNELS), 512)
        or signals.dtype != np.float32
        or not np.isfinite(signals).all()
        or channels != CHO_CHANNELS
    ):
        raise ValueError("Profile A artifact differs from the supported input contract")
    rows = tuple(int(i) for i in metadata["retained_artifact_indices"])
    retained_labels = tuple(labels[row] for row in rows)
    if retained_labels != tuple(catalog.labels):
        raise ValueError("retained Profile A labels differ from the catalog")
    owned = signals[list(rows)].copy()
    integer_labels = np.asarray(
        [CHO_CLASSES.index(label) for label in retained_labels], dtype=np.int64
    )
    if file_digest(path) != catalog.artifact_sha256:
        raise ValueError("Profile A bytes changed while loading")
    return BCIProfileASubject(
        owned,
        integer_labels,
        rows,
        catalog.artifact_sha256,
        file_digest(base_path),
    )


def load_mmidb_profile_a_subject(
    root: Path, protocol_config: Mapping[str, Any], catalog: TrialCatalog
) -> BCIProfileASubject:
    """Re-audit MMIDB Profile A bytes and return owned retained rows.

    MMIDB mirrors the Cho convention: identity is the audited catalog's
    artifact hash (no sidecar manifests) plus the frozen threshold profile,
    both re-verified against the bytes on disk. The T9/T10 montage and
    two-class roster are enforced before owned rows are returned.
    """
    root = root.resolve()
    config: dict[str, Any] = config_snapshot(protocol_config)
    validate_protocol(config)
    settings: dict[str, Any] = config["datasets"]["mmidb"]
    if (
        catalog.dataset != "mmidb"
        or catalog.classes != MMIDB_CLASSES
        or tuple(settings["classes"]) != MMIDB_CLASSES
        or settings["artifact_directory"] != "data/processed/mmidb/profile_a"
    ):
        raise ValueError("loading requires the fixed MMIDB two-class catalog and directory")
    path = root / "data/processed/mmidb/profile_a" / f"{catalog.subject}.npz"
    base_path = root / "configs/base.toml"
    threshold_path = root / config["preparation"]["threshold_config"]
    thresholds: dict[str, Any] = load_toml(threshold_path)
    threshold = thresholds["datasets"]["mmidb"]["artifact_threshold_volts"]
    preprocessing = config_digest({
        "profile_identity": config["preparation"]["profile_identity"],
        "threshold_config_sha256": file_digest(threshold_path),
        "dataset": "mmidb",
        "threshold": threshold,
    })
    actual, metadata = read_catalog(
        path, dataset="mmidb", classes=MMIDB_CLASSES,
        threshold=threshold, preprocessing_sha256=preprocessing,
    )
    if actual != catalog:
        raise ValueError("catalog differs from actual Profile A identities/labels/preprocessing")
    with np.load(path, allow_pickle=False) as data:
        signals = data["signals"]
        labels = [str(v) for v in data["labels"]]
        channels = tuple(str(v) for v in data["channel_names"])
    if (
        signals.ndim != 3
        or signals.shape[1:] != (len(MMIDB_CHANNELS), 512)
        or signals.dtype != np.float32
        or not np.isfinite(signals).all()
        or channels != MMIDB_CHANNELS
    ):
        raise ValueError("Profile A artifact differs from the supported input contract")
    rows = tuple(int(i) for i in metadata["retained_artifact_indices"])
    retained_labels = tuple(labels[row] for row in rows)
    if retained_labels != tuple(catalog.labels):
        raise ValueError("retained Profile A labels differ from the catalog")
    owned = signals[list(rows)].copy()
    integer_labels = np.asarray(
        [MMIDB_CLASSES.index(label) for label in retained_labels], dtype=np.int64
    )
    if file_digest(path) != catalog.artifact_sha256:
        raise ValueError("Profile A bytes changed while loading")
    return BCIProfileASubject(
        owned,
        integer_labels,
        rows,
        catalog.artifact_sha256,
        file_digest(base_path),
    )
