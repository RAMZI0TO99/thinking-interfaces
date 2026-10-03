"""Read-only recorder bridge for externally pinned Phase II analysis inputs.

This verifies recorder publication and exact metrics for an explicit roster.
The caller must separately verify and retain the scientific source, cohort,
episode, selection-evidence and configuration pins before using its output.
No result here constitutes scientific freeze or report admission.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.config import canonical_config_json
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import CellIdentity, verify_envelope
from evaluation.phase2_runner import MAXIMUM_ATTEMPTS, CasePlan, CaseRecorder
from evaluation.phase2_subject_aggregation import (
    ExpectedCell,
    ScoreRow,
    SubjectAggregation,
    aggregate_subject_methods,
)

MAX_CELL_BYTES = 8 * 1024 * 1024
MAX_RECEIPT_BYTES = 128 * 1024


@dataclass(frozen=True, slots=True)
class PinnedCaseCell:
    """One case with digests retained outside the writable recorder tree."""

    plan: CasePlan
    key: ExpectedCell
    identity: CellIdentity
    attempt: int
    cell_sha256: str
    success_file_sha256: str
    selection_evidence_sha256: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.plan, CasePlan)
            or not isinstance(self.key, ExpectedCell)
            or not isinstance(self.identity, CellIdentity)
        ):
            raise ValueError("typed plan, roster key and cell identity are required")
        if type(self.attempt) is not int or not 1 <= self.attempt <= MAXIMUM_ATTEMPTS:
            raise ValueError("attempt is outside the recorder's permitted attempts")
        for name in (
            "cell_sha256", "success_file_sha256", "selection_evidence_sha256"
        ):
            require_digest(getattr(self, name), name)
        key = (
            self.key.dataset, self.key.subject, self.key.method,
            self.key.shots, self.key.seed,
        )
        if self.plan.identity_key != key or self.plan.identity_key != (
            self.identity.dataset, self.identity.target_subject,
            self.identity.method, self.identity.shots_per_class,
            self.identity.model_seed,
        ):
            raise ValueError("plan, roster key and cell identity differ")


def _canonical_record(path: Path, *, maximum_bytes: int) -> tuple[dict[str, Any], bytes]:
    """Bound a local recorder read and reject links, aliases and changed bytes."""
    parent = path.parent
    if (
        parent.is_symlink() or not parent.is_dir() or parent.resolve() != parent
        or path.is_symlink() or path.resolve() != path or not path.is_file()
    ):
        raise ValueError(f"record path is absent or aliases another path: {path}")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= maximum_bytes:
        raise ValueError(f"record size or link count differs: {path}")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if not os.path.samestat(before, opened):
            raise ValueError(f"record identity changed while opening: {path}")
        raw = stream.read(maximum_bytes + 1)
        closed = os.fstat(stream.fileno())
    after = path.stat()
    if (
        len(raw) != before.st_size or len(raw) > maximum_bytes
        or not os.path.samestat(before, closed)
        or not os.path.samestat(before, after)
        or before.st_mtime_ns != after.st_mtime_ns
        or before.st_size != after.st_size
        or path.is_symlink() or path.resolve() != path
    ):
        raise ValueError(f"record changed while reading: {path}")
    try:
        record = json.loads(raw)
        if (
            not isinstance(record, dict)
            or raw != (canonical_config_json(record) + "\n").encode("utf-8")
        ):
            raise ValueError("record bytes are not canonical")
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
        raise ValueError(f"record JSON is invalid: {path}") from error
    return record, raw


def _exact_directory(directory: Path, names: set[str]) -> None:
    if not names and not directory.exists() and not directory.is_symlink():
        return
    if directory.is_symlink() or not directory.is_dir() or directory.resolve() != directory:
        raise ValueError(f"recorder directory is absent or aliases another path: {directory}")
    observed_count = 0
    for path in directory.iterdir():
        if path.name not in names:
            raise ValueError(f"recorder directory has missing or extra records: {directory}")
        observed_count += 1
        if observed_count > len(names):
            raise ValueError(f"recorder directory has missing or extra records: {directory}")
    if observed_count != len(names):
        raise ValueError(f"recorder directory has missing or extra records: {directory}")


def _valid_recorded_source(source: dict[str, Any]) -> bool:
    commit = source["git_commit"]
    dirty = source["git_dirty"]
    return (
        isinstance(commit, str)
        and (
            commit == "unversioned-workspace"
            or (
                len(commit) in (40, 64)
                and all(character in "0123456789abcdef" for character in commit)
            )
        )
        and (type(dirty) is bool or dirty is None)
    )


def _verified_claim(output: Path, pin: PinnedCaseCell, attempt: int) -> tuple[Path, str]:
    path = output / "claims" / f"{pin.plan.case_id}.attempt{attempt}.claim.json"
    record, raw = _canonical_record(path, maximum_bytes=MAX_RECEIPT_BYTES)
    payload = record.get("payload")
    if not isinstance(payload, dict) or set(payload) != {
        "purpose", "case", "worker", "attempt", "environment_sha256",
        "source", "engineering_only",
    }:
        raise ValueError("case claim fields differ from the recorder schema")
    source = payload["source"]
    if (
        payload["purpose"] != "pilot_case_claim"
        or payload["case"] != asdict(pin.plan)
        or type(payload["attempt"]) is not int or payload["attempt"] != attempt
        or not isinstance(payload["worker"], str) or not payload["worker"].strip()
        or payload["engineering_only"] is not True
        or not isinstance(source, dict)
        or set(source) != {"git_commit", "git_dirty", "source_sha256"}
        or not _valid_recorded_source(source)
        or not verify_envelope(record, kind="engineering_smoke", expected_payload=payload)
    ):
        raise ValueError("case claim differs from the pinned case")
    require_digest(payload["environment_sha256"], "claim environment")
    require_digest(source["source_sha256"], "claim source")
    if attempt == pin.attempt and (
        payload["environment_sha256"] != pin.identity.environment_sha256
        or source["source_sha256"] != pin.identity.source_sha256
        or source["git_commit"] != pin.identity.git_commit
        or source["git_dirty"] is not pin.identity.git_dirty
    ):
        raise ValueError("final claim provenance differs from the pinned cell identity")
    return path, hashlib.sha256(raw).hexdigest()


def _verified_prior_failure(output: Path, pin: PinnedCaseCell) -> tuple[Path, str]:
    path = output / "attempts" / f"{pin.plan.case_id}.attempt1.failure.json"
    record, raw = _canonical_record(path, maximum_bytes=MAX_RECEIPT_BYTES)
    payload = record.get("payload")
    if not isinstance(payload, dict) or set(payload) != {
        "purpose", "case", "attempt", "reason", "environment_sha256",
        "engineering_only",
    }:
        raise ValueError("prior failure fields differ from the recorder schema")
    reason = payload["reason"]
    if (
        payload["purpose"] != "pilot_case_failure"
        or payload["case"] != asdict(pin.plan)
        or type(payload["attempt"]) is not int or payload["attempt"] != 1
        or not isinstance(reason, dict)
        or not isinstance(reason.get("error"), str) or not reason["error"].strip()
        or payload["engineering_only"] is not True
        or not verify_envelope(record, kind="engineering_smoke", expected_payload=payload)
    ):
        raise ValueError("prior failure does not justify the retry")
    require_digest(payload["environment_sha256"], "failure environment")
    return path, hashlib.sha256(raw).hexdigest()


def verified_score_rows(
    recorder: CaseRecorder,
    expected_roster: Sequence[ExpectedCell],
    pins: Sequence[PinnedCaseCell],
) -> tuple[ScoreRow, ...]:
    """Verify exact recorder cells and success receipts against external pins."""
    if not isinstance(recorder, CaseRecorder):
        raise ValueError("a Phase II CaseRecorder is required")
    if not expected_roster or not pins or len(expected_roster) != len(pins):
        raise ValueError("a complete nonempty roster and matching pins are required")
    if (
        any(not isinstance(key, ExpectedCell) for key in expected_roster)
        or any(not isinstance(pin, PinnedCaseCell) for pin in pins)
    ):
        raise ValueError("roster and pins require typed entries")
    roster = tuple(expected_roster)
    pinned = tuple(pins)
    if (
        len(set(roster)) != len(roster)
        or {pin.key for pin in pinned} != set(roster)
        or len({pin.plan.case_id for pin in pinned}) != len(pinned)
        or len({pin.plan.identity_key for pin in pinned}) != len(pinned)
        or len({pin.cell_sha256 for pin in pinned}) != len(pinned)
        or len({pin.success_file_sha256 for pin in pinned}) != len(pinned)
    ):
        raise ValueError("roster and external pins are duplicate or incomplete")

    output = recorder.output_root
    if output.is_symlink() or not output.is_dir() or output.resolve() != output:
        raise ValueError("recorder output directory is absent or aliases another path")
    inventories = {
        "cells": {f"{pin.identity.sha256}.json" for pin in pinned},
        "successes": {f"{pin.plan.case_id}.success.json" for pin in pinned},
        "publication_intents": {
            f"{pin.plan.case_id}.intent.json" for pin in pinned
        },
        "claims": {
            f"{pin.plan.case_id}.attempt{attempt}.claim.json"
            for pin in pinned for attempt in range(1, pin.attempt + 1)
        },
        "attempts": {
            f"{pin.plan.case_id}.attempt1.failure.json"
            for pin in pinned if pin.attempt == 2
        },
        "engineering_intents": set(),
        "engineering_successes": set(),
    }
    for directory, names in inventories.items():
        _exact_directory(output / directory, names)

    rows: list[ScoreRow] = []
    read_records: list[tuple[Path, int, str]] = []
    for pin in pinned:
        for attempt in range(1, pin.attempt + 1):
            path, digest = _verified_claim(output, pin, attempt)
            read_records.append((path, MAX_RECEIPT_BYTES, digest))
        if pin.attempt == 2:
            path, digest = _verified_prior_failure(output, pin)
            read_records.append((path, MAX_RECEIPT_BYTES, digest))
        cell_path = output / "cells" / f"{pin.identity.sha256}.json"
        cell, cell_raw = _canonical_record(cell_path, maximum_bytes=MAX_CELL_BYTES)
        read_records.append((cell_path, MAX_CELL_BYTES, hashlib.sha256(cell_raw).hexdigest()))
        payload = cell.get("payload")
        if not isinstance(payload, dict) or set(payload) != {"identity", "metrics"}:
            raise ValueError("cell payload differs from the recorder schema")
        if payload["identity"] != asdict(pin.identity) or not isinstance(payload["metrics"], dict):
            raise ValueError("cell identity or metrics differ from the external pin")
        metrics = payload["metrics"]
        if (
            cell.get("sha256") != pin.cell_sha256
            or not verify_envelope(cell, kind="evaluation_cell", expected_payload=payload)
            or metrics.get("selection_evidence_sha256") != pin.selection_evidence_sha256
        ):
            raise ValueError("cell or selection-evidence digest differs")
        recorder._validated_metrics(metrics)

        intent_path = output / "publication_intents" / f"{pin.plan.case_id}.intent.json"
        intent, intent_raw = _canonical_record(intent_path, maximum_bytes=MAX_CELL_BYTES)
        read_records.append((
            intent_path, MAX_CELL_BYTES, hashlib.sha256(intent_raw).hexdigest(),
        ))
        if not verify_envelope(intent, kind="engineering_smoke", expected_payload={
            "purpose": "pilot_case_publication_intent", "case": asdict(pin.plan),
            "attempt": pin.attempt, "identity": asdict(pin.identity), "cell": cell,
        }):
            raise ValueError("publication intent differs from the pinned cell")

        success_path = output / "successes" / f"{pin.plan.case_id}.success.json"
        success, success_raw = _canonical_record(
            success_path, maximum_bytes=MAX_RECEIPT_BYTES,
        )
        read_records.append((
            success_path, MAX_RECEIPT_BYTES, hashlib.sha256(success_raw).hexdigest(),
        ))
        if (
            hashlib.sha256(success_raw).hexdigest() != pin.success_file_sha256
            or not verify_envelope(success, kind="engineering_smoke", expected_payload={
                "purpose": "pilot_case_success", "case": asdict(pin.plan),
                "attempt": pin.attempt, "cell_sha256": pin.cell_sha256,
            })
        ):
            raise ValueError("case success differs from its external pin")
        numerator, denominator = metrics["balanced_accuracy"]
        rows.append(ScoreRow(pin.key, numerator, denominator, pin.cell_sha256))

    for directory, names in inventories.items():
        _exact_directory(output / directory, names)
    for path, maximum_bytes, digest in read_records:
        _, raw = _canonical_record(path, maximum_bytes=maximum_bytes)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f"recorder record changed during aggregation: {path}")
    return tuple(sorted(rows, key=lambda row: row.key))


def aggregate_recorder_cells(
    recorder: CaseRecorder,
    expected_roster: Sequence[ExpectedCell],
    pins: Sequence[PinnedCaseCell],
) -> SubjectAggregation:
    """Aggregate pinned recorder cells without inferential analysis or a report."""
    return aggregate_subject_methods(
        expected_roster, verified_score_rows(recorder, expected_roster, pins),
    )
