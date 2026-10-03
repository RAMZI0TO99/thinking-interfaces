"""Build proposed BCI IV 2a no-future pre-cue artifacts from pinned local raw files.

No network download, historical artifact, Gate A record, or model fit is permitted.
The all-nine-subject signal audit is an input pin, not a scientific approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import tomllib
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import mne  # type: ignore[import-untyped]
import moabb  # type: ignore[import-untyped]
import numpy as np
import psutil  # type: ignore[import-untyped]
import scipy  # type: ignore[import-untyped]
from moabb.datasets import BNCI2014_001  # type: ignore[import-untyped]
from moabb.datasets.bnci import bnci_2014  # type: ignore[import-untyped]
from numpy.typing import NDArray

from core.config import canonical_config_json
from data.pre_cue_no_future import (
    BCI_EVENT_ID,
    NoFuturePreCueConfig,
    build_no_future_summary,
    load_no_future_config,
    preprocess_no_future_run,
)
from evaluation.phase2_records import verify_envelope

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_RELATIVE = Path(
    "runs/phase2/gate_a_diagnostics/20260923_no_future_all9_posthash/"
    "real_pre_cue_no_future_all9_posthash.json"
)
RECEIPT_SHA256 = "14accc31cb041b17cda1a670bbaae635a1fee53500d3ebbce95608a12ae69be5"
RECEIPT_ENVELOPE_SHA256 = "3327faa236306f6a83ce28a53be541bebd934fcad53023ca6f468e80436c6770"
WRITER_RELATIVE = "scripts/preprocess_pre_cue_no_future_v1.py"
REQUIRED_AUDIT_PATHS = (
    "configs/base.toml",
    "configs/bci_iv_2a.toml",
    "configs/pre_cue_no_future_v1.toml",
    "core/config.py",
    "data/bci_iv_2a.py",
    "data/pre_cue.py",
    "data/pre_cue_no_future.py",
    "data/runtime.py",
    "evaluation/phase2_records.py",
    "requirements-data.lock",
    "scripts/audit_real_pre_cue_no_future_all9.py",
)
GIB = 1024**3
MIN_FREE_DISK_GIB = 20.0
MIN_AVAILABLE_RAM_GIB = 4.0
SUBJECTS = tuple(range(1, 10))
SESSIONS = ("0train", "1test")
RUNS = tuple(str(index) for index in range(6))
RunRows = dict[tuple[str, str], tuple[tuple[int, str], ...]]


@dataclass(frozen=True, slots=True)
class Plan:
    root: Path
    raw_dir: Path
    output_dir: Path
    config: NoFuturePreCueConfig
    observed: dict[str, Any]
    source_sha256: dict[str, str]
    expected_runs: dict[int, RunRows]


@dataclass(frozen=True, slots=True)
class SubjectComputation:
    signals: NDArray[np.float32]
    labels: NDArray[np.str_]
    sessions: NDArray[np.str_]
    runs: NDArray[np.str_]
    trial_indices: NDArray[np.int64]
    channel_names: tuple[str, ...]
    summary: dict[str, Any]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _unaliased_file(path: Path) -> bool:
    return not path.is_symlink() and path.resolve() == path.absolute()


def guard_resources(root: Path, *, reserve_bytes: int = 0) -> dict[str, float]:
    if type(reserve_bytes) is not int or reserve_bytes < 0:
        raise ValueError("nonnegative publication reserve bytes are required")
    disk = shutil.disk_usage(root).free / GIB
    ram = psutil.virtual_memory().available / GIB
    required_disk = MIN_FREE_DISK_GIB + reserve_bytes / GIB
    if disk < required_disk or ram < MIN_AVAILABLE_RAM_GIB:
        raise RuntimeError(
            f"no-future artifact resource guard failed: disk {disk:.3f}/"
            f"{required_disk:.3f} GiB, RAM {ram:.3f}/{MIN_AVAILABLE_RAM_GIB:.3f} GiB"
        )
    return {"free_disk_gib": round(disk, 3), "available_ram_gib": round(ram, 3)}


def _source_hashes(root: Path, pinned: Mapping[str, str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in REQUIRED_AUDIT_PATHS:
        expected = pinned[relative]
        path = root / relative
        if not _unaliased_file(path) or not path.is_file():
            raise ValueError(f"audit source path aliases or is missing: {relative}")
        actual = file_sha256(path)
        if actual != expected:
            raise ValueError(f"audit source/config differs from pinned receipt: {relative}")
        hashes[relative] = actual
    hashes[WRITER_RELATIVE] = file_sha256(root / WRITER_RELATIVE)
    return hashes


def _expected_runs(observed: Mapping[str, Any]) -> dict[int, RunRows]:
    if (
        observed.get("subjects") != list(SUBJECTS)
        or observed.get("total_runs") != 108
        or observed.get("total_cues") != 5184
        or observed.get("shape_per_cue") != [22, 128]
        or len(observed.get("cues_detail", [])) != 5184
    ):
        raise ValueError("all-nine-subject audit coverage differs")
    rows: dict[int, dict[tuple[str, str], list[tuple[int, str]]]] = {
        subject: {(session, run): [] for session in SESSIONS for run in RUNS}
        for subject in SUBJECTS
    }
    for entry in observed["cues_detail"]:
        subject = entry["subject"]
        key = (entry["session"], entry["run"])
        if subject not in rows or key not in rows[subject]:
            raise ValueError("audit cue has an unexpected subject, session or run")
        current = rows[subject][key]
        if entry["event_index"] != len(current):
            raise ValueError("audit cue order differs")
        cue = entry["cue_raw_sample"]
        label = entry["label"]
        if type(cue) is not int or cue < 1 or label not in BCI_EVENT_ID:
            raise ValueError("audit cue sample or label differs")
        current.append((cue, label))
    result: dict[int, RunRows] = {}
    for subject, subject_rows in rows.items():
        if any(len(cues) != 48 for cues in subject_rows.values()):
            raise ValueError(f"subject {subject} audit does not have 48 cues per run")
        counts = Counter(label for cues in subject_rows.values() for _, label in cues)
        if counts != {label: 144 for label in BCI_EVENT_ID}:
            raise ValueError(f"subject {subject} audit class counts differ")
        result[subject] = {key: tuple(value) for key, value in subject_rows.items()}
    return result


def load_plan(root: Path) -> Plan:
    root = root.resolve()
    with (root / "configs/base.toml").open("rb") as stream:
        base = tomllib.load(stream)
    with (root / "configs/bci_iv_2a.toml").open("rb") as stream:
        dataset = tomllib.load(stream)["dataset"]
    config = load_no_future_config(root / "configs/pre_cue_no_future_v1.toml")
    if (
        base["storage"]["minimum_free_gb"] != MIN_FREE_DISK_GIB
        or dataset["key"] != "bci_iv_2a"
        or dataset["subjects"] != list(SUBJECTS)
        or dataset["raw_root"] != "data/raw/moabb"
    ):
        raise ValueError("BCI IV 2a subject or storage contract differs")
    raw_dir = root / "data/raw/moabb/MNE-bnci-data/~bci/database/001-2014"
    output_dir = root / config.output_namespace
    if raw_dir.resolve() != raw_dir or output_dir.resolve() != output_dir:
        raise ValueError("raw or output namespace aliases another location")
    receipt_path = root / RECEIPT_RELATIVE
    if file_sha256(receipt_path) != RECEIPT_SHA256:
        raise ValueError("all-nine-subject signal audit receipt bytes differ")
    record = json.loads(receipt_path.read_bytes())
    if (
        record.get("sha256") != RECEIPT_ENVELOPE_SHA256
        or not verify_envelope(record, kind="engineering_smoke", expected_payload=record["payload"])
    ):
        raise ValueError("all-nine-subject signal audit envelope differs")
    observed: dict[str, Any] = record["payload"]["observed"]
    if (
        observed.get("audit_kind") != "real_pre_cue_no_future_all9_signal_comparison"
        or observed.get("processed_eeg_artifact_written") is not False
        or observed.get("control_model_metric_computed") is not False
        or observed.get("scientific_cells_admitted") != 0
    ):
        raise ValueError("unexpected all-nine-subject audit purpose")
    raw_pins = observed["raw_files"]
    expected_raw_names = {
        f"A{subject:02d}{part}.mat" for subject in SUBJECTS for part in ("T", "E")
    }
    if set(raw_pins) != expected_raw_names:
        raise ValueError("all-nine-subject raw pin roster differs")
    versions = observed["library_versions"]
    if versions != {
        "mne": mne.__version__, "moabb": moabb.__version__,
        "numpy": np.__version__, "scipy": scipy.__version__,
    }:
        raise ValueError("scientific runtime differs from the signal audit")
    source_sha256 = _source_hashes(root, observed["source_sha256"])
    if source_sha256["configs/pre_cue_no_future_v1.toml"] != config.config_file_sha256:
        raise ValueError("proposal config differs from the signal audit")
    return Plan(
        root=root, raw_dir=raw_dir, output_dir=output_dir, config=config,
        observed=observed, source_sha256=source_sha256,
        expected_runs=_expected_runs(observed),
    )


def verify_raw_subject(plan: Plan, subject: int) -> dict[str, dict[str, str | int]]:
    identities: dict[str, dict[str, str | int]] = {}
    for part in ("T", "E"):
        name = f"A{subject:02d}{part}.mat"
        path = plan.raw_dir / name
        if not _unaliased_file(path) or not path.is_file():
            raise FileNotFoundError(f"pinned local raw file missing or aliased: {name}")
        before = path.stat()
        digest = file_sha256(path)
        after = path.stat()
        identity: dict[str, str | int] = {"sha256": digest, "bytes": after.st_size}
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError(f"raw file changed while hashing: {name}")
        if identity != plan.observed["raw_files"][name]:
            raise ValueError(f"raw file differs from the all-nine-subject receipt: {name}")
        identities[name] = identity
    return identities


def _local_subject_data(plan: Plan, subject: int) -> tuple[dict[str, Any], dict[str, int]]:
    """Let MOABB decode only the two already verified files; block its downloader."""

    dataset = BNCI2014_001()
    event_id = dict(dataset.event_id)
    if event_id != BCI_EVENT_ID:
        raise ValueError("MOABB event mapping differs from the audited four classes")
    files = {
        f"A{subject:02d}{part}.mat": plan.raw_dir / f"A{subject:02d}{part}.mat"
        for part in ("T", "E")
    }
    requested: set[str] = set()

    def local_path(
        url: str, path: Any, force_update: bool, update_path: Any
    ) -> list[str]:
        name = url.rsplit("/", 1)[-1]
        if (
            name not in files or path is not None or force_update is not False
            or update_path is not None
        ):
            raise ValueError("MOABB requested an unpinned or downloadable BCI file")
        requested.add(name)
        return [str(files[name])]

    with patch.object(bnci_2014, "data_path", side_effect=local_path):
        subject_data = dataset.get_data(subjects=[subject], n_jobs=1)[subject]
    if requested != set(files):
        raise ValueError("MOABB did not decode both pinned local BCI files")
    return subject_data, event_id


def validate_arrays(
    *,
    subject: int,
    signals: NDArray[np.float32],
    labels: NDArray[np.str_],
    sessions: NDArray[np.str_],
    runs: NDArray[np.str_],
    trial_indices: NDArray[np.int64],
    channel_names: tuple[str, ...],
    config: NoFuturePreCueConfig,
    expected_runs: RunRows,
) -> dict[str, Any]:
    expected = [
        (session, run, index, label)
        for session in SESSIONS for run in RUNS
        for index, (_, label) in enumerate(expected_runs[(session, run)])
    ]
    if (
        type(subject) is not int or subject not in SUBJECTS
        or signals.shape != (576, 22, 128) or signals.dtype != np.float32
        or not np.isfinite(signals).all()
        or channel_names != config.channel_names
        or any(values.shape != (576,) for values in (labels, sessions, runs, trial_indices))
        or any(values.dtype.kind != "U" for values in (labels, sessions, runs))
        or trial_indices.dtype != np.int64
        or list(zip(sessions, runs, trial_indices, labels, strict=True)) != expected
    ):
        raise ValueError("no-future subject signal shape, class or audited cue roster differs")
    return build_no_future_summary(
        subject=subject, signals=signals, channel_names=channel_names, config=config
    ).as_dict()


def _publish_npz(
    path: Path, *, root: Path, signals: NDArray[np.float32], labels: NDArray[np.str_],
    sessions: NDArray[np.str_], runs: NDArray[np.str_],
    trial_indices: NDArray[np.int64], channel_names: tuple[str, ...],
) -> tuple[str, str, int]:
    channel_array = np.asarray(channel_names)
    uncompressed_bytes = sum(
        value.nbytes for value in (
            signals, labels, sessions, runs, trial_indices, channel_array
        )
    )
    # Deflate framing and ZIP records fit comfortably under this doubled
    # uncompressed allowance; reserve before creating the temporary.
    reserve_bytes = 2 * uncompressed_bytes + 1024 * 1024
    guard_resources(root, reserve_bytes=reserve_bytes)
    if not _unaliased_file(path):
        raise ValueError("no-future artifact path aliases another location")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not _unaliased_file(path):
        raise ValueError("no-future artifact parent changed before publication")
    guard_resources(root, reserve_bytes=reserve_bytes)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".npz")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            np.savez_compressed(
                stream, signals=signals, labels=labels, sessions=sessions, runs=runs,
                trial_indices=trial_indices, channel_names=channel_array,
            )
            stream.flush()
            os.fsync(stream.fileno())
        digest = file_sha256(temporary)
        size = temporary.stat().st_size
        if size > reserve_bytes:
            raise RuntimeError("NPZ exceeded its publication disk reserve")
        guard_resources(root, reserve_bytes=4096)
        if not _unaliased_file(path):
            raise ValueError("no-future artifact parent changed before linking")
        try:
            os.link(temporary, path)
            status = "created"
        except FileExistsError:
            if (
                not _unaliased_file(path) or path.stat().st_size != size
                or file_sha256(path) != digest
            ):
                raise FileExistsError(f"existing no-future artifact differs: {path}") from None
            status = "reused_orphan"
        return status, digest, size
    finally:
        temporary.unlink(missing_ok=True)


def _publish_manifest(path: Path, payload: Mapping[str, Any], *, root: Path) -> str:
    encoded = (canonical_config_json(payload) + "\n").encode("utf-8")
    guard_resources(root, reserve_bytes=len(encoded) + 4096)
    if not _unaliased_file(path):
        raise ValueError("no-future manifest path aliases another location")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not _unaliased_file(path):
        raise ValueError("no-future manifest parent changed before publication")
    guard_resources(root, reserve_bytes=len(encoded) + 4096)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        guard_resources(root, reserve_bytes=4096)
        if not _unaliased_file(path):
            raise ValueError("no-future manifest parent changed before linking")
        try:
            os.link(temporary, path)
            return "created"
        except FileExistsError:
            if not _unaliased_file(path) or path.read_bytes() != encoded:
                raise FileExistsError(f"existing no-future manifest differs: {path}") from None
            return "reused"
    finally:
        temporary.unlink(missing_ok=True)


def _manifest(
    plan: Plan, subject: int, summary: Mapping[str, Any],
    raw_files: Mapping[str, Any], artifact: Path, artifact_sha256: str, artifact_bytes: int,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "manifest_kind": plan.config.manifest_kind,
        "artifact_kind": plan.config.artifact_kind,
        "control_id": plan.config.control_id,
        "status": plan.config.status,
        "subject": subject,
        "artifact": artifact.name,
        "artifact_sha256": artifact_sha256,
        "artifact_bytes": artifact_bytes,
        "summary": dict(summary),
        "raw_files": dict(raw_files),
        "signal_audit_receipt_sha256": RECEIPT_SHA256,
        "signal_audit_envelope_sha256": RECEIPT_ENVELOPE_SHA256,
        "source_sha256": plan.source_sha256,
    }


def _compute_subject(
    plan: Plan, subject: int, raw_files: Mapping[str, Any]
) -> SubjectComputation:
    """Rebuild all 576 windows from pinned local raw for writes and verification."""

    guard_resources(plan.root)
    if verify_raw_subject(plan, subject) != raw_files:
        raise ValueError("raw files changed before no-future preprocessing")
    if _source_hashes(plan.root, plan.observed["source_sha256"]) != plan.source_sha256:
        raise ValueError("writer or audited source changed before no-future preprocessing")
    subject_data, event_id = _local_subject_data(plan, subject)
    if set(subject_data) != set(SESSIONS):
        raise ValueError("subject session roster differs from the signal audit")
    batches: list[NDArray[np.float32]] = []
    labels: list[str] = []
    sessions: list[str] = []
    runs: list[str] = []
    indices: list[int] = []
    channel_names: tuple[str, ...] | None = None
    for session in SESSIONS:
        session_runs = subject_data[session]
        if set(session_runs) != set(RUNS):
            raise ValueError("subject run roster differs from the signal audit")
        for run in RUNS:
            guard_resources(plan.root)
            raw = session_runs[run]
            batch, run_labels, channels = preprocess_no_future_run(raw, event_id, plan.config)
            events, _ = mne.events_from_annotations(
                raw, event_id=event_id, regexp=None, verbose=False
            )
            actual = tuple(
                (int(row[0]), label) for row, label in zip(events, run_labels, strict=True)
            )
            if (
                batch.shape != (48, 22, 128)
                or actual != plan.expected_runs[subject][(session, run)]
                or channels != plan.config.channel_names
            ):
                raise ValueError(f"subject {subject} {session}/{run} differs from the signal audit")
            if channel_names is None:
                channel_names = channels
            elif channels != channel_names:
                raise ValueError("canonical channel order changed between runs")
            batches.append(batch)
            labels.extend(run_labels)
            sessions.extend([session] * 48)
            runs.extend([run] * 48)
            indices.extend(range(48))
            guard_resources(plan.root)
    if channel_names is None:
        raise ValueError("subject contains no processed runs")
    signal_array = np.concatenate(batches, axis=0)
    label_array = np.asarray(labels)
    session_array = np.asarray(sessions)
    run_array = np.asarray(runs)
    index_array = np.asarray(indices, dtype=np.int64)
    summary = validate_arrays(
        subject=subject, signals=signal_array, labels=label_array,
        sessions=session_array, runs=run_array, trial_indices=index_array,
        channel_names=channel_names, config=plan.config,
        expected_runs=plan.expected_runs[subject],
    )
    if verify_raw_subject(plan, subject) != raw_files:
        raise ValueError("raw files changed during no-future preprocessing")
    if _source_hashes(plan.root, plan.observed["source_sha256"]) != plan.source_sha256:
        raise ValueError("writer or audited source changed during no-future preprocessing")
    return SubjectComputation(
        signals=signal_array, labels=label_array, sessions=session_array,
        runs=run_array, trial_indices=index_array, channel_names=channel_names,
        summary=summary,
    )


def _verify_complete_pair(
    plan: Plan, subject: int, artifact: Path, manifest: Path,
    raw_files: Mapping[str, Any], computed: SubjectComputation,
) -> dict[str, Any]:
    if not _unaliased_file(artifact) or not _unaliased_file(manifest):
        raise ValueError("no-future subject output aliases another location")
    with np.load(artifact, allow_pickle=False) as stored:
        if set(stored.files) != {
            "signals", "labels", "sessions", "runs", "trial_indices", "channel_names"
        }:
            raise ValueError("existing no-future NPZ fields differ")
        signals = stored["signals"]
        labels = stored["labels"]
        sessions = stored["sessions"]
        runs = stored["runs"]
        indices = stored["trial_indices"]
        stored_channels = stored["channel_names"]
        channels = tuple(str(value) for value in stored_channels.tolist())
    summary = validate_arrays(
        subject=subject, signals=signals, labels=labels, sessions=sessions,
        runs=runs, trial_indices=indices, channel_names=channels,
        config=plan.config, expected_runs=plan.expected_runs[subject],
    )
    if (
        not np.array_equal(signals, computed.signals)
        or not np.array_equal(labels, computed.labels)
        or labels.dtype != computed.labels.dtype
        or not np.array_equal(sessions, computed.sessions)
        or sessions.dtype != computed.sessions.dtype
        or not np.array_equal(runs, computed.runs)
        or runs.dtype != computed.runs.dtype
        or not np.array_equal(indices, computed.trial_indices)
        or channels != computed.channel_names
        or stored_channels.dtype != np.asarray(computed.channel_names).dtype
        or summary != computed.summary
    ):
        raise ValueError("existing no-future artifact differs from recomputed pinned raw windows")
    expected = _manifest(
        plan, subject, summary, raw_files, artifact, file_sha256(artifact),
        artifact.stat().st_size,
    )
    encoded = (canonical_config_json(expected) + "\n").encode("utf-8")
    if manifest.read_bytes() != encoded:
        raise ValueError("existing no-future manifest differs from verified artifact/context")
    return {"subject": subject, "status": "verified_existing", "artifact": str(artifact),
            "manifest": str(manifest), "artifact_sha256": expected["artifact_sha256"]}


def check_subject(plan: Plan, subject: int) -> dict[str, Any]:
    """Verify one completed pair against the audit without writing or fitting."""

    if subject not in SUBJECTS:
        raise ValueError("subject must be one of 1 through 9")
    guard_resources(plan.root)
    if _source_hashes(plan.root, plan.observed["source_sha256"]) != plan.source_sha256:
        raise ValueError("writer or audited source changed before artifact verification")
    raw_files = verify_raw_subject(plan, subject)
    artifact = plan.output_dir / f"subject_{subject:02d}.npz"
    manifest = plan.output_dir / f"subject_{subject:02d}.manifest.json"
    if not _unaliased_file(artifact) or not _unaliased_file(manifest):
        raise ValueError("no-future subject output aliases another location")
    if not artifact.is_file() or not manifest.is_file():
        raise FileNotFoundError("completed no-future artifact and manifest pair is required")
    computed = _compute_subject(plan, subject, raw_files)
    if not _unaliased_file(artifact) or not _unaliased_file(manifest):
        raise ValueError("no-future subject output parent changed during verification")
    result = _verify_complete_pair(plan, subject, artifact, manifest, raw_files, computed)
    if verify_raw_subject(plan, subject) != raw_files:
        raise ValueError("raw files changed during no-future artifact verification")
    if _source_hashes(plan.root, plan.observed["source_sha256"]) != plan.source_sha256:
        raise ValueError("writer or audited source changed during artifact verification")
    return result


def process_subject(plan: Plan, subject: int) -> dict[str, Any]:
    if subject not in SUBJECTS:
        raise ValueError("subject must be one of 1 through 9")
    guard_resources(plan.root)
    if _source_hashes(plan.root, plan.observed["source_sha256"]) != plan.source_sha256:
        raise ValueError("writer or audited source changed before subject processing")
    raw_files = verify_raw_subject(plan, subject)
    artifact = plan.output_dir / f"subject_{subject:02d}.npz"
    manifest = plan.output_dir / f"subject_{subject:02d}.manifest.json"
    if not _unaliased_file(artifact) or not _unaliased_file(manifest):
        raise ValueError("no-future subject output aliases another location")
    if manifest.exists() and not artifact.is_file():
        raise FileExistsError("manifest exists without its no-future artifact")
    if artifact.exists() and not artifact.is_file():
        raise FileExistsError("no-future artifact path is not a regular file")
    if artifact.is_file() and manifest.is_file():
        return check_subject(plan, subject)
    computed = _compute_subject(plan, subject, raw_files)
    if not _unaliased_file(artifact) or not _unaliased_file(manifest):
        raise ValueError("no-future subject output parent changed during preprocessing")
    guard_resources(plan.root)
    artifact_status, artifact_sha256, artifact_bytes = _publish_npz(
        artifact, root=plan.root, signals=computed.signals, labels=computed.labels,
        sessions=computed.sessions, runs=computed.runs,
        trial_indices=computed.trial_indices, channel_names=computed.channel_names,
    )
    payload = _manifest(
        plan, subject, computed.summary, raw_files, artifact, artifact_sha256, artifact_bytes
    )
    guard_resources(plan.root)
    if verify_raw_subject(plan, subject) != raw_files:
        raise ValueError("raw files changed before no-future manifest publication")
    if _source_hashes(plan.root, plan.observed["source_sha256"]) != plan.source_sha256:
        raise ValueError("writer or audited source changed before no-future manifest publication")
    manifest_status = _publish_manifest(manifest, payload, root=plan.root)
    return {
        "subject": subject, "status": "complete", "artifact_status": artifact_status,
        "manifest_status": manifest_status, "artifact": str(artifact),
        "artifact_sha256": artifact_sha256, "manifest": str(manifest),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subjects", nargs="+", type=int, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    subjects = args.subjects
    if len(subjects) != len(set(subjects)) or any(subject not in SUBJECTS for subject in subjects):
        raise ValueError("subjects must be unique members of the nine-subject roster")
    plan = load_plan(ROOT)
    for subject in subjects:
        if args.dry_run:
            guard_resources(plan.root)
            raw_files = verify_raw_subject(plan, subject)
            print(json.dumps({
                "subject": subject, "dry_run": True, "raw_files": raw_files,
                "artifact": str(plan.output_dir / f"subject_{subject:02d}.npz"),
                "manifest": str(plan.output_dir / f"subject_{subject:02d}.manifest.json"),
                "signal_audit_receipt_sha256": RECEIPT_SHA256,
                "signal_audit_envelope_sha256": RECEIPT_ENVELOPE_SHA256,
                "status": plan.config.status,
            }, sort_keys=True), flush=True)
        elif args.check_only:
            print(json.dumps(check_subject(plan, subject), sort_keys=True), flush=True)
        else:
            print(json.dumps(process_subject(plan, subject), sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
