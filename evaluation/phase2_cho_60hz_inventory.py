"""Build a complete, pinned Cho 60 Hz asset map before LaBraM execution."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any

from core.config import config_digest, load_toml
from evaluation.phase2_profile_binding import CHO_CLASSES, ChoProfileAssets60Hz
from evaluation.phase2_protocol import TrialCatalog, require_digest

_AUDIT = Path("runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json")
_CONFIG = Path("configs/phase2/cho_profile_b_60hz.toml")
_OUTPUT = Path("data/processed/cho2017/profile_b_60hz_v1")
_SUBJECTS = frozenset(f"subject_{index:02d}" for index in range(1, 53))
_VARIANT = {
    "schema_version": 1,
    "dataset": "cho2017",
    "name": "profile_b_60hz_v1",
    "output_directory": _OUTPUT.as_posix(),
}


def _digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def _direct_file(path: Path) -> None:
    if not path.is_file() or path.resolve() != path:
        raise ValueError(f"Cho 60 Hz input is missing or aliases another path: {path}")


def load_cho_60hz_assets(
    root: Path,
    catalogs: Sequence[TrialCatalog],
    *,
    cohort_audit_sha256: str,
    variant_config_sha256: str,
) -> Mapping[str, ChoProfileAssets60Hz]:
    """Rehash all 52 versioned pairs and return immutable binder input pins.

    This reads the audit, config and artifact bytes, but never decodes EEG or
    admits compute. The caller must obtain expected hashes from a reviewed,
    committed scientific configuration before using this in an experiment.
    """
    require_digest(cohort_audit_sha256, "cohort_audit_sha256")
    require_digest(variant_config_sha256, "variant_config_sha256")
    root = root.resolve()
    audit_file = root / _AUDIT
    config_file = root / _CONFIG
    output = root / _OUTPUT
    _direct_file(audit_file)
    _direct_file(config_file)
    if not output.is_dir() or output.resolve() != output:
        raise ValueError("Cho 60 Hz output directory is missing or aliases another path")
    if _digest(audit_file) != cohort_audit_sha256:
        raise ValueError("Cho 60 Hz cohort audit bytes differ from their pin")
    if _digest(config_file) != variant_config_sha256:
        raise ValueError("Cho 60 Hz variant config bytes differ from their pin")
    document: dict[str, Any] = load_toml(config_file)
    if document.get("variant") != _VARIANT:
        raise ValueError("Cho 60 Hz variant identity or output namespace differs")
    preprocessing = document.get("preprocessing")
    if (not isinstance(preprocessing, dict)
            or preprocessing.get("notch_hz") != 60.0
            or preprocessing.get("resample_hz") != 200.0):
        raise ValueError("Cho 60 Hz preprocessing configuration differs")
    preprocessing_sha256 = config_digest(preprocessing)
    audit = json.loads(audit_file.read_text("utf-8"))
    if not isinstance(audit, dict) or any(
        audit.get(key) is not True for key in (
            "passed", "all_52_versioned_pairs_pinned",
            "all_52_legacy_artifact_hashes_preserved",
            "all_52_profile_a_variant_trial_joins_verified",
            "all_52_raw_sources_verified_by_binding",
        )
    ):
        raise ValueError("Cho 60 Hz cohort audit did not pass its input checks")
    if (audit.get("schema_version") != 1 or audit.get("subject_count") != 52
            or audit.get("five_shot_episode_bindings_verified") != 52
            or audit.get("scientific_cells_admitted") != 0):
        raise ValueError("Cho 60 Hz cohort audit scope differs")
    rows = audit.get("rows")
    if not isinstance(rows, list) or len(rows) != 52:
        raise ValueError("Cho 60 Hz cohort audit must contain 52 rows")
    by_subject: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("subject"), str):
            raise ValueError("Cho 60 Hz cohort audit has an invalid subject")
        subject = row["subject"]
        if subject not in _SUBJECTS:
            raise ValueError("Cho 60 Hz cohort audit has an invalid subject")
        if subject in by_subject:
            raise ValueError("Cho 60 Hz cohort audit repeats a subject")
        for key in (
            "profile_a_sha256", "variant_artifact_sha256",
            "variant_manifest_sha256", "raw_source_sha256", "binding_sha256",
        ):
            value = row.get(key)
            if not isinstance(value, str):
                raise ValueError(f"Cho 60 Hz cohort audit lacks {key}")
            require_digest(value, key)
        by_subject[subject] = row
    if set(by_subject) != _SUBJECTS:
        raise ValueError("Cho 60 Hz cohort audit subject roster differs")
    if (len(catalogs) != 52
            or any(not isinstance(catalog, TrialCatalog) for catalog in catalogs)
            or {catalog.subject for catalog in catalogs} != _SUBJECTS
            or any(catalog.dataset != "cho2017" for catalog in catalogs)):
        raise ValueError("complete Cho Profile A catalogs are required")
    if (any(catalog.classes != CHO_CLASSES for catalog in catalogs)
            or len({catalog.preprocessing_sha256 for catalog in catalogs}) != 1):
        raise ValueError("Cho Profile A catalogs disagree on classes or preprocessing")
    for catalog in catalogs:
        if catalog.artifact_sha256 != by_subject[catalog.subject]["profile_a_sha256"]:
            raise ValueError("Cho Profile A catalog differs from the cohort audit")
    expected_files = {
        f"{subject}{suffix}" for subject in _SUBJECTS
        for suffix in (".npz", ".manifest.json")
    }
    if {path.name for path in output.iterdir()} != expected_files:
        raise ValueError("Cho 60 Hz output directory has missing or unexpected files")
    assets: dict[str, ChoProfileAssets60Hz] = {}
    for subject in sorted(_SUBJECTS):
        row = by_subject[subject]
        artifact = output / f"{subject}.npz"
        manifest_file = output / f"{subject}.manifest.json"
        _direct_file(artifact)
        _direct_file(manifest_file)
        if (_digest(artifact) != row["variant_artifact_sha256"]
                or _digest(manifest_file) != row["variant_manifest_sha256"]):
            raise ValueError(f"Cho 60 Hz artifact or manifest changed for {subject}")
        manifest = json.loads(manifest_file.read_text("utf-8"))
        if (not isinstance(manifest, dict)
                or manifest.get("variant") != _VARIANT
                or manifest.get("variant_config_sha256") != variant_config_sha256
                or manifest.get("config_sha256") != preprocessing_sha256
                or manifest.get("source_sha256") != row["raw_source_sha256"]):
            raise ValueError(f"Cho 60 Hz manifest provenance differs for {subject}")
        assets[subject] = ChoProfileAssets60Hz(
            profile_b_artifact_sha256=row["variant_artifact_sha256"],
            profile_b_manifest_sha256=row["variant_manifest_sha256"],
            variant_config_sha256=variant_config_sha256,
        )
    if _digest(audit_file) != cohort_audit_sha256 or _digest(config_file) != variant_config_sha256:
        raise ValueError("Cho 60 Hz inventory pins changed while loading")
    return MappingProxyType(assets)
