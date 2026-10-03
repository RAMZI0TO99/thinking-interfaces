"""Read-only evidence checks for the proposed 36-fit no-future EEGNet control.

This diagnostic is separate from the historical Gate A controls. Its effective
training gate is derived only from the byte-pinned pre-cue preset.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any, cast

import numpy as np

from core.config import canonical_config_json, config_digest, load_toml
from core.provenance import source_fingerprint
from data.pre_cue_no_future import load_no_future_config
from evaluation.phase2_records import verify_envelope
from evaluation.quality_audit import verify_quality_bundle
from evaluation.source_bound_controls import (
    environment_identity,
    file_digest,
    resolved_config,
    unit_name,
    validate_unit,
)

PRESET_RELATIVE = "configs/pre_cue_control.toml"
PRESET_SHA256 = "e157a9632d79ad47387f4356e3ecd3dc35637425965adced28c336c269cad28f"
AUDIT_RELATIVE = (
    "runs/phase2/gate_a_diagnostics/20260923_no_future_all9_posthash/"
    "real_pre_cue_no_future_all9_posthash.json"
)
AUDIT_SHA256 = "14accc31cb041b17cda1a670bbaae635a1fee53500d3ebbce95608a12ae69be5"
AUDIT_ENVELOPE_SHA256 = "3327faa236306f6a83ce28a53be541bebd934fcad53023ca6f468e80436c6770"
WRITER_RELATIVE = "scripts/preprocess_pre_cue_no_future_v1.py"
WRAPPER_RELATIVE = "scripts/run_no_future_matched_control.py"
DIAGNOSTIC_NAME = "pre_cue_no_future_v1_matched.toml"
DIAGNOSTIC_ID = "pre_cue_no_future_v1_matched_36"
ARTIFACT_PATTERN = "data/processed/bci_iv_2a/pre_cue_no_future_v1/subject_{subject:02d}.npz"
RUNS_RELATIVE = "runs/no_future_matched_control"
RAW_RELATIVE = "data/raw/moabb/MNE-bnci-data/~bci/database/001-2014"
QUALITY_RELATIVE = "runs/quality_status.json"
SUBJECTS = tuple(range(1, 10))
SEEDS = (11, 23, 37, 53)
SESSIONS = ("0train", "1test")
RUNS = tuple(str(index) for index in range(6))
RUNTIME = {
    "minimum_free_memory_gib": 10.0,
    "stop_below_free_memory_gib": 4.0,
    "minimum_free_disk_gib": 20.0,
    "maximum_wall_seconds": 7200,
}
MANIFEST_KEYS = {
    "schema_version", "manifest_kind", "artifact_kind", "control_id", "status",
    "subject", "artifact", "artifact_sha256", "artifact_bytes", "summary",
    "raw_files", "signal_audit_receipt_sha256", "signal_audit_envelope_sha256",
    "source_sha256",
}
NPZ_KEYS = {"signals", "labels", "sessions", "runs", "trial_indices", "channel_names"}
UNIT_KEYS = {
    "schema", "context_sha256", "unit", "record", "result", "resources",
    "signal_identity", "input_labels", "input_sessions", "split",
    "training_targets", "query_targets", "query_predictions", "diagnostic",
}


def _regular_unaliased(path: Path) -> bool:
    return path.is_file() and not path.is_symlink() and path.resolve() == path.absolute()


def _directory_unaliased(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink() and path.resolve() == path.absolute()


def ensure_run_namespace(root: Path, key: str | None = None, *, create: bool = False) -> Path:
    """Reject output aliases, including a Windows junction, before evidence I/O."""

    root = root.absolute()
    if not _directory_unaliased(root):
        raise ValueError("matched-control project root aliases another location")
    parts = [root / "runs", root / RUNS_RELATIVE]
    if key is not None:
        if re.fullmatch(r"[0-9a-f]{64}", key) is None:
            raise ValueError("matched-control context key is invalid")
        parts.append(parts[-1] / key)
    for path in parts:
        if create and not path.exists() and not path.is_symlink():
            path.mkdir()
        if path.exists() or path.is_symlink():
            if not _directory_unaliased(path):
                raise ValueError(
                    f"matched-control output directory aliases another location: {path}"
                )
        elif create:
            raise ValueError("matched-control output directory was not created")
    return parts[-1]


def quality_identity(root: Path) -> dict[str, str]:
    """Require the completed full-quality receipt for this exact source."""

    path = root / QUALITY_RELATIVE
    if not _regular_unaliased(path):
        raise ValueError("current-source quality status is missing or aliased")
    status_bytes = path.read_bytes()
    status = json.loads(status_bytes)
    if not isinstance(status, dict) or not verify_quality_bundle(root, status):
        raise ValueError("current-source full-quality bundle is stale or invalid")
    source = source_fingerprint(root)
    if (
        status.get("source_sha256_after") != source
        or not isinstance(status.get("source"), dict)
        or status["source"].get("source_sha256") != source
        or file_digest(path) != hashlib.sha256(status_bytes).hexdigest()
    ):
        raise ValueError("quality status changed while binding the current source")
    return {
        "status_relative": QUALITY_RELATIVE,
        "status_sha256": hashlib.sha256(status_bytes).hexdigest(),
        "source_sha256": source,
    }


def verify_quality_identity(root: Path, context: dict[str, Any]) -> None:
    if quality_identity(root) != context["quality_bundle"]:
        raise ValueError("current-source quality receipt differs from matched-control context")


def _raw_pins(observed: dict[str, Any]) -> dict[str, dict[str, str | int]]:
    expected_names = {
        f"A{subject:02d}{part}.mat" for subject in SUBJECTS for part in ("T", "E")
    }
    pins = observed["raw_files"]
    if set(pins) != expected_names:
        raise ValueError("all-nine-subject raw MAT roster differs")
    result: dict[str, dict[str, str | int]] = {}
    for name in sorted(expected_names):
        identity = pins[name]
        if (
            set(identity) != {"bytes", "sha256"}
            or type(identity["bytes"]) is not int or identity["bytes"] <= 0
            or type(identity["sha256"]) is not str
            or re.fullmatch(r"[0-9a-f]{64}", identity["sha256"]) is None
        ):
            raise ValueError(f"raw MAT pin differs: {name}")
        result[name] = {"bytes": identity["bytes"], "sha256": identity["sha256"]}
    return result


def verify_subject_raw(root: Path, context: dict[str, Any], subject: int) -> None:
    if type(subject) is not int or subject not in SUBJECTS:
        raise ValueError("subject must be one of 1 through 9")
    pins = context["raw_inputs"]
    for part in ("T", "E"):
        name = f"A{subject:02d}{part}.mat"
        path = root / RAW_RELATIVE / name
        if not _regular_unaliased(path):
            raise ValueError(f"raw MAT file is missing or aliased: {name}")
        before = path.stat()
        digest = file_digest(path)
        after = path.stat()
        if (
            (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
            or pins[name] != {"bytes": after.st_size, "sha256": digest}
        ):
            raise ValueError(f"raw MAT file differs from sealed audit: {name}")


def verify_all_raw(root: Path, context: dict[str, Any]) -> None:
    for subject in SUBJECTS:
        verify_subject_raw(root, context, subject)


def effective_gate(preset: dict[str, Any]) -> dict[str, Any]:
    """Make the only authorized proposal delta explicit and reviewable."""

    if set(preset) != {"gate_a", "output"} or not isinstance(preset["gate_a"], dict):
        raise ValueError("pre-cue preset structure differs")
    original = cast(dict[str, Any], preset["gate_a"])
    if (
        original.get("gate_name") != "pre_cue_control"
        or original.get("attempt") != "one_second_pre_cue_control"
        or original.get("artifact_pattern")
        != "data/processed/bci_iv_2a/pre_cue_control/subject_{subject:02d}.npz"
        or original.get("source") != "artifact"
        or original.get("subjects") != list(SUBJECTS)
        or original.get("seeds") != list(SEEDS)
        or original.get("control_max_accuracy") != 0.35
    ):
        raise ValueError("pre-cue preset identity, cohort or limit differs")
    gate = json.loads(json.dumps(original, allow_nan=False))
    gate["gate_name"] = DIAGNOSTIC_ID
    gate["attempt"] = DIAGNOSTIC_ID
    gate["artifact_pattern"] = ARTIFACT_PATTERN
    changed = {key for key in original if gate[key] != original[key]}
    if changed != {"gate_name", "attempt", "artifact_pattern"}:
        raise ValueError("matched gate changed outside its diagnostic identity and input path")
    return cast(dict[str, Any], gate)


def _audit_observed(root: Path) -> dict[str, Any]:
    path = root / AUDIT_RELATIVE
    if not _regular_unaliased(path) or file_digest(path) != AUDIT_SHA256:
        raise ValueError("pinned all-nine-subject signal audit bytes differ")
    record = json.loads(path.read_bytes())
    if (
        record.get("sha256") != AUDIT_ENVELOPE_SHA256
        or not verify_envelope(
            record, kind="engineering_smoke", expected_payload=record["payload"]
        )
    ):
        raise ValueError("all-nine-subject signal audit envelope differs")
    observed = cast(dict[str, Any], record["payload"]["observed"])
    if (
        observed.get("subjects") != list(SUBJECTS)
        or observed.get("total_runs") != 108
        or observed.get("total_cues") != 5184
        or observed.get("shape_per_cue") != [22, 128]
        or len(observed.get("cues_detail", [])) != 5184
        or observed.get("scientific_cells_admitted") != 0
        or observed.get("control_model_metric_computed") is not False
    ):
        raise ValueError("all-nine-subject audit coverage or purpose differs")
    return observed


def _expected_rows(observed: dict[str, Any], subject: int) -> list[tuple[str, str, int, str]]:
    by_run: dict[tuple[str, str], list[str]] = {
        (session, run): [] for session in SESSIONS for run in RUNS
    }
    for entry in observed["cues_detail"]:
        if entry["subject"] != subject:
            continue
        key = (entry["session"], entry["run"])
        if key not in by_run or entry["event_index"] != len(by_run[key]):
            raise ValueError("no-future audit cue order differs")
        by_run[key].append(entry["label"])
    if any(len(labels) != 48 for labels in by_run.values()):
        raise ValueError("no-future audit subject/run coverage differs")
    return [
        (session, run, index, label)
        for session in SESSIONS for run in RUNS
        for index, label in enumerate(by_run[(session, run)])
    ]


def inspect_artifact(root: Path, subject: int, observed: dict[str, Any]) -> dict[str, Any]:
    """Independently bind NPZ signal bytes and full manifest to the pinned audit."""

    if type(subject) is not int or subject not in SUBJECTS:
        raise ValueError("subject must be one of 1 through 9")
    artifact_relative = ARTIFACT_PATTERN.format(subject=subject)
    artifact = root / artifact_relative
    manifest_relative = artifact_relative.removesuffix(".npz") + ".manifest.json"
    manifest_path = root / manifest_relative
    if not _regular_unaliased(artifact) or not _regular_unaliased(manifest_path):
        raise FileNotFoundError("complete unaliased no-future NPZ/manifest pair is required")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if set(manifest) != MANIFEST_KEYS:
        raise ValueError("no-future manifest fields differ")
    if manifest_bytes != (canonical_config_json(manifest) + "\n").encode("utf-8"):
        raise ValueError("no-future manifest serialization differs")
    config = load_no_future_config(root / "configs/pre_cue_no_future_v1.toml")
    raw_names = (f"A{subject:02d}T.mat", f"A{subject:02d}E.mat")
    expected_raw = {name: observed["raw_files"][name] for name in raw_names}
    source = cast(dict[str, str], manifest["source_sha256"])
    expected_source = {
        **observed["source_sha256"],
        WRITER_RELATIVE: file_digest(root / WRITER_RELATIVE),
    }
    if (
        manifest["schema_version"] != 1
        or manifest["manifest_kind"] != config.manifest_kind
        or manifest["artifact_kind"] != config.artifact_kind
        or manifest["control_id"] != config.control_id
        or manifest["status"] != "proposed_unratified"
        or manifest["subject"] != subject
        or manifest["artifact"] != artifact.name
        or manifest["signal_audit_receipt_sha256"] != AUDIT_SHA256
        or manifest["signal_audit_envelope_sha256"] != AUDIT_ENVELOPE_SHA256
        or manifest["raw_files"] != expected_raw
        or source != expected_source
    ):
        raise ValueError("no-future manifest identity, raw or source pins differ")
    if any(
        not _regular_unaliased(root / name) or file_digest(root / name) != digest
        for name, digest in expected_source.items()
    ):
        raise ValueError("audited source bytes changed since no-future artifact publication")
    before = artifact.stat()
    artifact_sha256 = file_digest(artifact)
    after = artifact.stat()
    if (
        (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
        or manifest["artifact_bytes"] != after.st_size
        or manifest["artifact_sha256"] != artifact_sha256
    ):
        raise ValueError("no-future artifact bytes differ from manifest")
    with np.load(artifact, allow_pickle=False) as data:
        if set(data.files) != NPZ_KEYS:
            raise ValueError("no-future NPZ schema differs")
        signals = data["signals"]
        labels = data["labels"]
        sessions = data["sessions"]
        runs = data["runs"]
        indices = data["trial_indices"]
        channels = data["channel_names"]
    expected_rows = _expected_rows(observed, subject)
    if (
        signals.shape != (576, 22, 128)
        or signals.dtype != np.float32
        or not np.isfinite(signals).all()
        or any(value.shape != (576,) for value in (labels, sessions, runs, indices))
        or any(value.dtype.kind != "U" for value in (labels, sessions, runs, channels))
        or indices.dtype != np.int64
        or channels.ndim != 1
        or tuple(channels.tolist()) != config.channel_names
        or list(zip(sessions, runs, indices, labels, strict=True)) != expected_rows
        or Counter(labels.tolist()) != {label: 144 for label in config_labels()}
    ):
        raise ValueError("no-future NPZ signal, channel, cue or label roster differs")
    expected_summary = {
        "artifact_schema_version": 1,
        "artifact_kind": config.artifact_kind,
        "manifest_kind": config.manifest_kind,
        "control_id": config.control_id,
        "status": config.status,
        "subject": subject,
        "shape": [576, 22, 128],
        "channel_names": list(config.channel_names),
        "sampling_rate_hz": config.resample_hz,
        "window_duration_s": config.window_duration_s,
        "minimum_prefix_samples": 413,
        "prefix_policy": config.prefix_policy,
        "filter_phase": config.filter_phase,
        "mne_version": importlib.metadata.version("mne"),
        "output_namespace": config.output_namespace,
        "config_file_sha256": config.config_file_sha256,
        "config_sha256": config_digest(asdict(config)),
    }
    if manifest["summary"] != expected_summary:
        raise ValueError("no-future manifest summary differs from verified NPZ/config")
    if not _regular_unaliased(artifact) or file_digest(artifact) != artifact_sha256:
        raise ValueError("no-future artifact changed while validating its signal bytes")
    return {
        "artifact_relative": artifact_relative,
        "artifact_sha256": artifact_sha256,
        "manifest_relative": manifest_relative,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "signal_sha256": hashlib.sha256(signals.tobytes(order="C")).hexdigest(),
        "signal_shape": [576, 22, 128],
        "signal_dtype": "float32",
        "labels": labels.tolist(),
        "sessions": sessions.tolist(),
    }


def config_labels() -> tuple[str, ...]:
    return ("left_hand", "right_hand", "feet", "tongue")


def build_context(root: Path, writer_check_sha256: str) -> dict[str, Any]:
    root = root.resolve()
    if len(writer_check_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in writer_check_sha256
    ):
        raise ValueError("a full raw recomputation check digest is required")
    preset_path = root / PRESET_RELATIVE
    if not _regular_unaliased(preset_path) or file_digest(preset_path) != PRESET_SHA256:
        raise ValueError("historical pre-cue preset bytes changed")
    preset = cast(dict[str, Any], load_toml(preset_path))
    gate = effective_gate(preset)
    observed = _audit_observed(root)
    raw_inputs = _raw_pins(observed)
    subjects = {str(subject): inspect_artifact(root, subject, observed) for subject in SUBJECTS}
    inputs = {
        item[relative_key]: item[digest_key]
        for item in subjects.values()
        for relative_key, digest_key in (
            ("artifact_relative", "artifact_sha256"),
            ("manifest_relative", "manifest_sha256"),
        )
    }
    inputs[AUDIT_RELATIVE] = AUDIT_SHA256
    quality_bundle = quality_identity(root)
    context = {
        "schema": 1,
        "diagnostic_kind": DIAGNOSTIC_ID,
        "status": "proposed_engineering_diagnostic_gate_a_unsigned",
        "scientific_cells_admitted": 0,
        "source_sha256": source_fingerprint(root),
        "wrapper_sha256": file_digest(root / WRAPPER_RELATIVE),
        "writer_sha256": file_digest(root / WRITER_RELATIVE),
        "preset_sha256": PRESET_SHA256,
        "preset": preset,
        "quality_bundle": quality_bundle,
        "writer_check": {
            "command": (
                "python -m scripts.preprocess_pre_cue_no_future_v1 "
                "--subjects 1 2 3 4 5 6 7 8 9 --check-only"
            ),
            "stdout_sha256": writer_check_sha256,
            "subjects": list(SUBJECTS),
        },
        "configuration": {"controls": {"device": "cuda"}, "runtime": RUNTIME},
        "model_configuration": load_toml(root / "configs/eegnet.toml"),
        "specifications": {DIAGNOSTIC_NAME: {"gate_a": gate}},
        "inputs": inputs,
        "raw_inputs": raw_inputs,
        "subject_inputs": subjects,
        "environment": environment_identity(),
    }
    verify_all_raw(root, context)
    return context


def prove_effective_gate(context: dict[str, Any]) -> None:
    if (
        context["preset_sha256"] != PRESET_SHA256
        or context["specifications"] != {
            DIAGNOSTIC_NAME: {"gate_a": effective_gate(context["preset"])}
        }
        or context["configuration"] != {"controls": {"device": "cuda"}, "runtime": RUNTIME}
    ):
        raise ValueError("effective matched gate does not derive exactly from the preset")


def expected_units(context: dict[str, Any]) -> list[tuple[str, int, int]]:
    prove_effective_gate(context)
    gate = context["specifications"][DIAGNOSTIC_NAME]["gate_a"]
    return [
        (DIAGNOSTIC_NAME, subject, seed)
        for subject in gate["subjects"] for seed in gate["seeds"]
    ]


def validate_matched_unit(payload: dict[str, Any], context: dict[str, Any],
                          unit: tuple[str, int, int]) -> float:
    prove_effective_gate(context)
    if set(payload) != UNIT_KEYS or payload["diagnostic"] != {
        "kind": DIAGNOSTIC_ID, "status": "proposed_engineering_diagnostic",
        "gate_a_signed": False, "scientific_cell": False,
    }:
        raise ValueError("matched unit diagnostic status or schema differs")
    score = validate_unit(payload, context, unit)
    identity = context["subject_inputs"][str(unit[1])]
    if (
        payload["signal_identity"] != {
            "shape": identity["signal_shape"], "dtype": identity["signal_dtype"],
            "sha256": identity["signal_sha256"],
        }
        or payload["input_labels"] != identity["labels"]
        or payload["input_sessions"] != identity["sessions"]
        or payload["record"]["config"] != resolved_config(context, unit)
    ):
        raise ValueError("matched unit inputs differ from the pinned no-future NPZ")
    return score


def audit_context(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    prove_effective_gate(context)
    key = config_digest(context)
    directory = ensure_run_namespace(root, key)
    units = expected_units(context)
    expected_names = {unit_name(*unit) for unit in units}
    unexpected = sorted(
        path.name for path in directory.glob("*.json")
        if path.name not in expected_names and path.name != "context.json"
    )
    invalid: dict[str, str] = {}
    context_path = directory / "context.json"
    if directory.is_dir():
        try:
            if (
                not _regular_unaliased(context_path)
                or json.loads(context_path.read_bytes()) != context
            ):
                raise ValueError("saved matched context differs")
        except (OSError, ValueError, TypeError) as error:
            invalid["context.json"] = str(error)
    missing: list[str] = []
    files: dict[str, str] = {}
    scores: dict[int, list[float]] = defaultdict(list)
    for unit in units:
        path = directory / unit_name(*unit)
        if not path.is_file():
            missing.append(path.name)
            continue
        try:
            if not _regular_unaliased(path):
                raise ValueError("matched unit path aliases another file")
            score = validate_matched_unit(json.loads(path.read_bytes()), context, unit)
            scores[unit[1]].append(score)
            files[path.name] = file_digest(path)
        except (OSError, ValueError, KeyError, TypeError, IndexError, ZeroDivisionError) as error:
            invalid[path.name] = str(error)
    means = {str(subject): mean(values) for subject, values in scores.items()}
    complete = (
        not missing and not invalid and not unexpected and len(files) == 36
        and set(means) == {str(subject) for subject in SUBJECTS}
        and all(len(scores[subject]) == 4 for subject in SUBJECTS)
    )
    raw_files_verified = False
    if complete:
        try:
            verify_all_raw(root, context)
            verify_quality_identity(root, context)
            raw_files_verified = True
        except (OSError, ValueError, KeyError, TypeError) as error:
            invalid["raw_files"] = str(error)
            complete = False
    overall = mean(means.values()) if means else None
    limit = context["specifications"][DIAGNOSTIC_NAME]["gate_a"]["control_max_accuracy"]
    return {
        "diagnostic_kind": DIAGNOSTIC_ID,
        "status": "proposed_engineering_diagnostic_gate_a_unsigned",
        "scientific_cells_admitted": 0,
        "complete": complete,
        "passed": complete and overall is not None and math.isfinite(overall) and overall <= limit,
        "context_sha256": key,
        "source_sha256": context["source_sha256"],
        "expected_records": 36,
        "valid_records": len(files),
        "raw_files_verified": raw_files_verified,
        "invalid_records": invalid,
        "missing_records": missing,
        "unexpected_records": unexpected,
        "subject_means": means,
        "mean": overall,
        "limit": limit,
        "record_snapshot_sha256": config_digest(files),
    }
