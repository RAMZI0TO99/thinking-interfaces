"""Read pinned Cho target configuration and manifest declarations without EEG I/O.

The output describes persisted declarations only. The source bytes, Profile B
artifacts, prediction-time observation, and scientific admission are separate.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from core.config import config_digest
from evaluation.phase2_cho_case_inputs import CHO_SUBJECTS, ChoFirstTrancheRoute
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz
from evaluation.phase2_protocol import require_digest

_BASE = Path("configs/base.toml")
_VARIANT = Path("configs/phase2/cho_profile_b_60hz.toml")
_B_DIRECTORY = Path("data/processed/cho2017/profile_b_60hz_v1")
_SOURCE_DIRECTORY = PurePosixPath("data/raw/moabb/cho2017")
_CONFIG_LIMIT = 1024 * 1024
_MANIFEST_LIMIT = 1024 * 1024

_PROFILE_A = {
    "bandpass_low_hz": 8.0, "bandpass_high_hz": 30.0, "resample_hz": 128.0,
    "reference": "common_average", "epoch_duration_s": 4.0, "pre_cue_s": 1.0,
}
_PROFILE_B = {
    "bandpass_low_hz": 0.1, "bandpass_high_hz": 75.0, "notch_hz": 50.0,
    "resample_hz": 200.0, "reference": "original", "epoch_duration_s": 4.0,
    "amplitude_unit_mv": 0.1, "patch_duration_s": 1.0, "maximum_patches": 256,
}
_PROFILE_B_60HZ = {**_PROFILE_B, "notch_hz": 60.0}
_VARIANT_IDENTITY = {
    "schema_version": 1, "dataset": "cho2017", "name": "profile_b_60hz_v1",
    "output_directory": _B_DIRECTORY.as_posix(),
}


@dataclass(frozen=True, slots=True)
class ChoPersistedTargetDeclarations:
    """Pinned configuration digests and per-subject raw source declarations."""

    base_config_sha256: str
    profile_b_config_sha256: str
    source_by_subject: Mapping[str, tuple[str, str]]


def _direct_path(path: Path) -> None:
    """Disallow symlinks, junctions, hardlinks, and namespace aliases."""
    if not path.is_file() or path.resolve(strict=True) != path:
        raise ValueError(f"Cho target declaration is missing or aliases: {path}")
    if path.stat().st_nlink != 1:
        raise ValueError(f"Cho target declaration aliases another file: {path}")


def _pinned_bytes(path: Path, digest: str, limit: int, name: str) -> bytes:
    """Pin the exact bounded buffer later parsed and detect concurrent changes."""
    require_digest(digest, name)
    _direct_path(path)
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError(f"{name} is not a bounded regular file")
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if (
        len(raw) > limit or len(raw) != before.st_size
        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        or hashlib.sha256(raw).hexdigest() != digest
    ):
        raise ValueError(f"{name} changed while reading or differs from its pin")
    _direct_path(path)
    current = path.stat()
    if (
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns)
    ):
        raise ValueError(f"{name} changed while reading")
    return raw


def _toml(raw: bytes, name: str) -> dict[str, Any]:
    try:
        document = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"{name} is not valid UTF-8 TOML") from error
    if not isinstance(document, dict):
        raise ValueError(f"{name} must be a TOML document")
    return document


def _manifest(raw: bytes, subject: str) -> Mapping[str, Any]:
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cho B manifest for {subject} is not valid UTF-8 JSON") from error
    if not isinstance(document, dict):
        raise ValueError(f"Cho B manifest for {subject} must be a JSON object")
    return document


def _source_path(root: Path, value: Any) -> str:
    if not isinstance(value, str) or "\\" in value or ":" in value:
        raise ValueError("Cho B source path is invalid")
    relative = PurePosixPath(value)
    if (
        relative.is_absolute() or relative.parts[:len(_SOURCE_DIRECTORY.parts)]
        != _SOURCE_DIRECTORY.parts or len(relative.parts) <= len(_SOURCE_DIRECTORY.parts)
        or any(part in ("", ".", "..") for part in relative.parts)
        or relative.as_posix() != value
    ):
        raise ValueError("Cho B source path escapes the raw Cho namespace")
    lexical = root.joinpath(*relative.parts)
    if lexical.resolve(strict=False) != lexical:
        raise ValueError("Cho B source path aliases another namespace")
    return value


def verify_cho_persisted_target_declarations(
    root: Path, route: ChoFirstTrancheRoute, *, base_config_sha256: str,
) -> ChoPersistedTargetDeclarations:
    """Verify all 52 pinned B manifest declarations against exact persisted bytes.

    This reads only small config and manifest files. It does not hash or decode
    the B artifact or raw source, and it does not verify a reported fit.
    """
    if not isinstance(route, ChoFirstTrancheRoute):
        raise ValueError("a typed Cho first-tranche route is required")
    require_digest(base_config_sha256, "Cho base config")
    if (
        set(route.labram_assets) != set(CHO_SUBJECTS)
        or len(route.catalogs) != 52
        or {catalog.subject for catalog in route.catalogs} != set(CHO_SUBJECTS)
        or any(not isinstance(asset, ChoProfileAssets60Hz)
               for asset in route.labram_assets.values())
    ):
        raise ValueError("complete typed Cho 52-subject assets and catalogs are required")
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Cho root must be a directory")
    variant_hashes = {asset.variant_config_sha256 for asset in route.labram_assets.values()}
    if len(variant_hashes) != 1:
        raise ValueError("Cho 60 Hz variant asset pins disagree")
    variant_sha256 = next(iter(variant_hashes))
    require_digest(variant_sha256, "Cho 60 Hz variant config")
    base_path = root / _BASE
    variant_path = root / _VARIANT
    base = _toml(_pinned_bytes(base_path, base_config_sha256, _CONFIG_LIMIT, "Cho base config"),
                 "Cho base config")
    if base.get("preprocessing") != {
        "profile_a": _PROFILE_A, "profile_b": _PROFILE_B,
    }:
        raise ValueError("Cho base preprocessing differs from the supported profiles")
    variant = _toml(_pinned_bytes(
        variant_path, variant_sha256, _CONFIG_LIMIT, "Cho 60 Hz variant config",
    ), "Cho 60 Hz variant config")
    if variant != {"variant": _VARIANT_IDENTITY, "preprocessing": _PROFILE_B_60HZ}:
        raise ValueError("Cho 60 Hz variant identity or preprocessing differs")
    preprocessing_sha256 = config_digest(_PROFILE_B_60HZ)
    source_by_subject: dict[str, tuple[str, str]] = {}
    manifest_pins: list[tuple[Path, str, str]] = []
    for subject in CHO_SUBJECTS:
        asset = route.labram_assets[subject]
        require_digest(asset.profile_b_manifest_sha256, f"Cho B manifest {subject}")
        require_digest(asset.profile_b_artifact_sha256, f"Cho B artifact {subject}")
        manifest_path = root / _B_DIRECTORY / f"{subject}.manifest.json"
        manifest_pins.append((manifest_path, asset.profile_b_manifest_sha256, subject))
        manifest = _manifest(_pinned_bytes(
            manifest_path, asset.profile_b_manifest_sha256,
            _MANIFEST_LIMIT, f"Cho B manifest {subject}",
        ), subject)
        if (
            type(manifest.get("subject")) is not int
            or manifest.get("subject") != int(subject[-2:])
            or manifest.get("variant") != _VARIANT_IDENTITY
            or manifest.get("variant_config_sha256") != variant_sha256
            or manifest.get("config_sha256") != preprocessing_sha256
        ):
            raise ValueError(f"Cho B manifest variant or config differs for {subject}")
        source_file = _source_path(root, manifest.get("source_file"))
        source_sha256 = manifest.get("source_sha256")
        if not isinstance(source_sha256, str):
            raise ValueError(f"Cho B manifest source digest is missing for {subject}")
        require_digest(source_sha256, f"Cho B manifest source {subject}")
        source_by_subject[subject] = (source_file, source_sha256)
    # Catch path replacement during the 52-manifest read without re-reading EEG.
    _pinned_bytes(base_path, base_config_sha256, _CONFIG_LIMIT, "Cho base config")
    _pinned_bytes(variant_path, variant_sha256, _CONFIG_LIMIT, "Cho 60 Hz variant config")
    for manifest_path, manifest_sha256, subject in manifest_pins:
        _pinned_bytes(
            manifest_path, manifest_sha256, _MANIFEST_LIMIT, f"Cho B manifest {subject}",
        )
    return ChoPersistedTargetDeclarations(
        base_config_sha256, preprocessing_sha256, MappingProxyType(source_by_subject),
    )
