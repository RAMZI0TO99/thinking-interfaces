"""Owned synthetic physical inputs for one real public Cho source-selection fold.

This module does not replace a loader, selector, or cohort setting.  Its only
dataset is a newly created, explicitly synthetic 52-subject fixture.  Call it
only after the caller's fresh source/runtime/resource admission.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from core.config import canonical_config_json, config_digest, load_toml
from evaluation.phase2_profile_binding import (
    CHO_CHANNELS,
    CHO_CLASSES,
    ChoProfileAssets60Hz,
)
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import read_catalog, validate_protocol


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SUBJECTS = tuple(f"subject_{number:02d}" for number in range(1, 53))
METHODS = ("eegnet", "labram_linear", "labram_lora", "labram_full")
CONFIGURATIONS = (
    "configs/base.toml",
    "configs/benchmark.toml",
    "configs/phase2/protocol.toml",
    "configs/phase2/selection_ceiling.toml",
    "configs/phase2/cho_profile_b_60hz.toml",
)
OUTER_TARGET = "subject_02"
INNER_VALIDATION = "subject_01"
TRAINING_SUBJECTS = SUBJECTS[2:]
_MAXIMUM_INPUT_BYTES = 16 * 1024**2


def _status(path: Path) -> tuple[int, int, int, int, int]:
    info = path.stat(follow_symlinks=False)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or path.resolve(strict=True) != path
    ):
        raise ValueError("fixture inputs must be ordinary unaliased single-link files")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _input_pin(path: Path) -> dict[str, Any]:
    """Hash a bounded ordinary file, checking path and descriptor independently.

    Python 3.12 Windows path-stat and descriptor-stat ctime have different
    semantics.  Cross comparisons use dev/inode/size/mtime; each identity's own
    before/after comparison also includes ctime.
    """
    before = _status(path)
    if not 0 <= before[2] <= _MAXIMUM_INPUT_BYTES:
        raise ValueError("fixture input exceeds its fixed per-file bound")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        opened_info = os.fstat(stream.fileno())
        opened = (
            opened_info.st_dev, opened_info.st_ino, opened_info.st_size,
            opened_info.st_mtime_ns, opened_info.st_ctime_ns,
        )
        if opened[:4] != before[:4] or not stat.S_ISREG(opened_info.st_mode):
            raise ValueError("fixture input changed while opening")
        remaining = _MAXIMUM_INPUT_BYTES + 1
        total = 0
        while remaining:
            chunk = stream.read(min(1024**2, remaining))
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
            remaining -= len(chunk)
        closed_info = os.fstat(stream.fileno())
        closed = (
            closed_info.st_dev, closed_info.st_ino, closed_info.st_size,
            closed_info.st_mtime_ns, closed_info.st_ctime_ns,
        )
        if closed != opened:
            raise ValueError("fixture input descriptor changed while hashing")
    if total != before[2] or total > _MAXIMUM_INPUT_BYTES or _status(path) != before:
        raise ValueError("fixture input path or bytes changed while hashing")
    return {"sha256": digest.hexdigest(), "size_bytes": total}


def _write_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _write_bytes(path, (canonical_config_json(payload) + "\n").encode("utf-8"))


def _write_artifact(path: Path, signals: np.ndarray) -> None:
    """Write canonical-reader-compatible NPZ with deterministic ZIP metadata.

    Only the current subject/profile signal array exists here.  NumPy writes
    each .npy member to the ZIP stream; no complete archive buffer is retained.
    """
    if (
        signals.dtype != np.float32 or signals.shape[:2] != (42, 64)
        or signals.shape[2] not in (512, 800)
        or not signals.flags.c_contiguous or not np.isfinite(signals).all()
    ):
        raise ValueError("synthetic artifact shape or numeric contract differs")
    path.parent.mkdir(parents=True, exist_ok=True)
    members = {
        "signals": signals,
        "labels": np.asarray(CHO_CLASSES * 21),
        "sessions": np.asarray(["synthetic_session"] * 42),
        "runs": np.asarray(["synthetic_run"] * 42),
        "trial_indices": np.arange(42, dtype=np.int64),
        "channel_names": np.asarray(CHO_CHANNELS),
    }
    with path.open("xb") as raw_stream:
        with zipfile.ZipFile(raw_stream, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, values in members.items():
                information = zipfile.ZipInfo(f"{name}.npy", (1980, 1, 1, 0, 0, 0))
                information.compress_type = zipfile.ZIP_STORED
                information.create_system = 0
                information.external_attr = 0o600 << 16
                with archive.open(information, "w", force_zip64=True) as member:
                    np.lib.format.write_array(member, values, allow_pickle=False)
        raw_stream.flush()
        os.fsync(raw_stream.fileno())


def _subject_paths(root: Path, subject: str) -> tuple[Path, ...]:
    return (
        root / f"data/processed/cho2017/profile_a/{subject}.npz",
        root / f"data/processed/cho2017/profile_b_60hz_v1/{subject}.npz",
        root / f"data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json",
        root / f"data/raw/moabb/cho2017/{subject}.mat",
    )


@dataclass(frozen=True, slots=True)
class Fixture:
    root: Path
    protocol: dict[str, Any]
    catalogs: tuple[TrialCatalog, ...]
    selection_record: dict[str, Any]
    assets: dict[str, ChoProfileAssets60Hz]
    episode_records: dict[str, dict[str, Any]]
    input_identity: dict[str, Any]
    input_paths: tuple[Path, ...]
    protected_outer_paths: tuple[Path, ...]
    method: str
    profile: str
    identity_path: Path
    identity_file_sha256: str

    @property
    def physical_inputs(self) -> dict[str, str]:
        return {path.relative_to(self.root).as_posix(): str(path) for path in self.input_paths}

    def verify_inputs(self) -> dict[str, Any]:
        """Rehash immutable inputs, excluding later source-capture/run outputs."""
        expected_paths = {path.relative_to(self.root).as_posix() for path in self.input_paths}
        actual_paths = {
            path.relative_to(self.root).as_posix()
            for directory in (self.root / "configs", self.root / "data")
            for path in directory.rglob("*")
            if path.is_file() or path.is_symlink()
        }
        if actual_paths != expected_paths:
            raise ValueError("synthetic fixture input inventory changed")
        pins = {
            path.relative_to(self.root).as_posix(): _input_pin(path)
            for path in self.input_paths
        }
        if pins != self.input_identity["files"]:
            raise ValueError("synthetic fixture input bytes changed")
        content = {key: value for key, value in self.input_identity.items() if key != "sha256"}
        if config_digest(content) != self.input_identity["sha256"]:
            raise ValueError("synthetic fixture identity changed")
        expected_raw = (canonical_config_json(self.input_identity) + "\n").encode("utf-8")
        pin = _input_pin(self.identity_path)
        if pin != {
            "sha256": self.identity_file_sha256, "size_bytes": len(expected_raw),
        } or hashlib.sha256(expected_raw).hexdigest() != self.identity_file_sha256:
            raise ValueError("synthetic fixture identity record changed")
        # Return detached JSON, never arrays or mutable references to the fixture.
        return json.loads(canonical_config_json(self.input_identity))


def build_fixture(output: Path, method: str) -> Fixture:
    """Create 52 owned synthetic paired subjects under ``output/fixture`` once.

    No raw study .mat file, checkpoint, or pretrained weights are read.  The
    small .mat-named provenance files are deliberate marker bytes; canonical
    60 Hz binding hashes them and does not decode them.  Outer-target catalogs
    are prepared here, before the caller installs its fold-only outer-read
    denial.  No outer-target episode arrays are loaded for training/inference.
    """
    if type(method) is not str or method not in METHODS:
        raise ValueError("fixture method must be an adopted four-method ID")
    output = Path(output).absolute()
    if not output.is_dir() or output.resolve(strict=True) != output:
        raise ValueError("fixture output must be an existing ordinary unaliased directory")
    root = output / "fixture"
    root.mkdir(exist_ok=False)
    for relative in CONFIGURATIONS:
        source = PROJECT_ROOT / relative
        source_pin = _input_pin(source)
        # Small configuration bytes only, bounded before and after the read.
        with source.open("rb") as stream:
            raw = stream.read(1024**2 + 1)
        if len(raw) > 1024**2 or hashlib.sha256(raw).hexdigest() != source_pin["sha256"]:
            raise ValueError("source fixture configuration changed while copying")
        if _input_pin(source) != source_pin:
            raise ValueError("source fixture configuration changed after copying")
        _write_bytes(root / relative, raw)

    protocol: dict[str, Any] = load_toml(root / "configs/phase2/protocol.toml")
    shots = validate_protocol(protocol)
    if (
        protocol["datasets"]["cho2017"]["expected_subjects"] != 52
        or tuple(protocol["datasets"]["cho2017"]["classes"]) != CHO_CLASSES
        or shots != (1, 5, 10, 20)
        or protocol["protocol"]["maximum_support_per_class"] != 20
        or protocol["protocol"]["model_seeds"] != [11, 23, 37, 53, 71]
    ):
        raise ValueError("fixture must retain the canonical 52-subject protocol")
    threshold_path = root / "configs/benchmark.toml"
    threshold = load_toml(threshold_path)["datasets"]["cho2017"]["artifact_threshold_volts"]
    preprocessing_sha256 = config_digest({
        "profile_identity": protocol["preparation"]["profile_identity"],
        "threshold_config_sha256": _input_pin(threshold_path)["sha256"],
        "dataset": "cho2017", "threshold": threshold,
    })
    variant_path = root / "configs/phase2/cho_profile_b_60hz.toml"
    variant = load_toml(variant_path)
    variant_sha256 = _input_pin(variant_path)["sha256"]
    catalogs: list[TrialCatalog] = []
    assets: dict[str, ChoProfileAssets60Hz] = {}
    episodes: dict[str, dict[str, Any]] = {}
    for number, subject in enumerate(SUBJECTS, start=1):
        a_path, b_path, manifest_path, raw_path = _subject_paths(root, subject)
        # Independent per-subject/profile seeds retain deterministic physical
        # bytes without changing the caller's global NumPy or Torch RNG.
        for profile, samples, scale, path in (
            (0, 512, 1e-8, a_path), (1, 800, 0.1, b_path),
        ):
            generator = np.random.default_rng(np.random.SeedSequence((20261015, number, profile)))
            signals = generator.standard_normal((42, 64, samples), dtype=np.float32)
            signals *= np.float32(scale)
            _write_artifact(path, signals)
            del signals, generator
        _write_bytes(raw_path, (
            f"SYNTHETIC ENGINEERING PROVENANCE ONLY\n{subject}\n"
            "not a MATLAB recording; never decode as study data\n"
        ).encode("ascii"))
        _write_json(manifest_path, {
            "artifact_schema_version": 1, "artifact_kind": "profile_b", "subject": number,
            "shape": [42, 64, 800], "channel_names": list(CHO_CHANNELS),
            "epoch_duration_s": 4.0, "sampling_rate_hz": 200.0,
            "config_sha256": config_digest(variant["preprocessing"]),
            "reference": "original", "amplitude_unit_mv": 0.1,
            "patch_samples": 200, "patches_per_epoch": 4,
            "variant": variant["variant"], "variant_config_sha256": variant_sha256,
            "source_file": raw_path.relative_to(root).as_posix(),
            "source_sha256": _input_pin(raw_path)["sha256"],
        })
        catalog, metadata = read_catalog(
            a_path, dataset="cho2017", classes=CHO_CLASSES, threshold=threshold,
            preprocessing_sha256=preprocessing_sha256,
        )
        if (
            metadata["input_trials"] != 42 or metadata["retained_trials"] != 42
            or metadata["rejected_trials"] != 0
            or metadata["retained_class_counts"] != {label: 21 for label in CHO_CLASSES}
            or catalog.subject != subject
        ):
            raise ValueError("synthetic fixture unexpectedly changed the retained cohort")
        catalogs.append(catalog)
        assets[subject] = ChoProfileAssets60Hz(
            _input_pin(b_path)["sha256"], _input_pin(manifest_path)["sha256"], variant_sha256,
        )
        episodes[subject] = envelope("episode_manifest", nested_episode(
            catalog, shots=shots, protocol_sha256=config_digest(protocol),
        ).payload())

    selection = source_selection(tuple(catalogs), target=OUTER_TARGET)
    first_fold = next(fold for fold in selection.inner_folds if fold.validation_subject == INNER_VALIDATION)
    if (
        selection.source_subjects != ("subject_01", *SUBJECTS[2:])
        or first_fold.training_subjects != TRAINING_SUBJECTS
        or len(first_fold.training_subjects) != 50
    ):
        raise ValueError("synthetic source fold must retain 50 sources and subject01 validation")
    paths = tuple(sorted(
        [root / relative for relative in CONFIGURATIONS]
        + [path for subject in SUBJECTS for path in _subject_paths(root, subject)],
        key=lambda path: path.relative_to(root).as_posix(),
    ))
    identity: dict[str, Any] = {
        "schema": "cho51_owned_synthetic_fold_inputs_v1",
        "synthetic": True, "actual_study_data": False, "scientific_admission": False,
        "original_case_attempts_remaining": 0,
        "source_subjects_available": 52, "adopted_evaluation_targets": 51,
        "adopted_case_plan_count": 1020, "outer_target": OUTER_TARGET,
        "inner_validation_subject": INNER_VALIDATION,
        "training_subjects": list(TRAINING_SUBJECTS),
        "shots_per_class": 5, "canonical_shot_levels": list(shots),
        "trials_per_subject": 42, "trials_per_class": 21,
        "profile_a_shape": [42, 64, 512], "profile_b_shape": [42, 64, 800],
        "protocol_sha256": config_digest(protocol),
        "source_selection_sha256": selection.sha256,
        "files": {path.relative_to(root).as_posix(): _input_pin(path) for path in paths},
    }
    identity["sha256"] = config_digest(identity)
    identity_path = root / "synthetic-input-identity.json"
    _write_json(identity_path, identity)
    fixture = Fixture(
        root=root, protocol=protocol, catalogs=tuple(catalogs),
        selection_record=envelope("source_selection", asdict(selection)),
        assets=assets, episode_records=episodes, input_identity=identity,
        input_paths=paths, protected_outer_paths=_subject_paths(root, OUTER_TARGET),
        method=method,
        profile="cho_profile_a" if method == "eegnet" else "cho_profile_b_60hz_v1",
        identity_path=identity_path,
        identity_file_sha256=_input_pin(identity_path)["sha256"],
    )
    fixture.verify_inputs()
    return fixture
