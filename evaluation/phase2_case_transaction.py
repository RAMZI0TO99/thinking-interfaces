"""Synthetic, non-scientific child proposal and parent attestation transaction.

This boundary deliberately cannot claim a Phase II case or publish a cell. A
future Cho caller must still prove the complete public selection route, own the
case lock, and validate actual predictions and metrics before publication.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import struct
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.config import canonical_config_json, config_digest
from evaluation.phase2_records import write_once
from evaluation.phase2_supervision_primitives import (
    DeadlineLease,
    ResourceFloor,
    ResourceSample,
    SupervisionError,
    live_resources,
    run_supervised,
    run_supervised_with_frame,
)

_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_TOKEN = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
_ATTEMPT = re.compile(r"[0-9a-f]{32}\Z")
_MAX_RECORD_BYTES = 16 * 1024


def _digest(value: object, name: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _root(path: Path) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise ValueError("transaction root must be an ordinary directory")
    return path.resolve(strict=True)


def _inside(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative:
        raise ValueError("invalid transaction relative path")
    parts = relative.split("/")
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        raise ValueError("transaction path must be simple and relative")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("transaction path cannot contain a link")
    if not current.resolve().is_relative_to(root):
        raise ValueError("transaction path escapes its root")
    return current


def _file(path: Path, *, limit: int = _MAX_RECORD_BYTES) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("transaction file is missing or linked")
    before = path.stat()
    if before.st_size > limit:
        raise ValueError("transaction file exceeds its byte cap")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(limit + 1)
    after = path.stat()
    def identity(stat: os.stat_result) -> tuple[int, int, int, int]:
        return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns

    if (
        len(raw) > limit or len(raw) != before.st_size
        or identity(before) != identity(opened) or identity(opened) != identity(after)
        or path.is_symlink()
    ):
        raise ValueError("transaction file changed while read or exceeds its byte cap")
    return raw


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _record(schema: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    base = {"schema": schema, "payload": json.loads(canonical_config_json(payload))}
    return {**base, "sha256": config_digest(base)}


def _read(root: Path, relative: str, *, schema: str, expected_sha256: str) -> dict[str, Any]:
    raw = _file(_inside(root, relative))
    try:
        record = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("transaction record is unreadable") from exc
    if (
        not isinstance(record, dict)
        or set(record) != {"schema", "payload", "sha256"}
        or record.get("schema") != schema
        or not isinstance(record.get("payload"), dict)
        or record.get("sha256") != expected_sha256
        or record != _record(schema, record["payload"])
        or raw != (canonical_config_json(record) + "\n").encode("utf-8")
    ):
        raise ValueError("transaction record differs from its external pin or schema")
    return record


def _publish(root: Path, relative: str, record: Mapping[str, Any]) -> Path:
    path = _inside(root, relative)
    write_once(path, record, output_root=root)
    if _file(path) != (canonical_config_json(record) + "\n").encode("utf-8"):
        raise ValueError("published transaction bytes changed")
    return path


def _publish_fresh(root: Path, relative: str, record: Mapping[str, Any]) -> Path:
    """Require this parent to win a new, complete no-clobber publication."""
    path = _inside(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path = _inside(root, relative)
    encoded = (canonical_config_json(record) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=".phase2-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ValueError("proposal appeared before parent publication") from exc
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary)
    if _file(path) != encoded:
        raise ValueError("freshly published proposal changed")
    return path


def _source(root: Path, payload: Mapping[str, Any]) -> None:
    relative = payload.get("source_relpath")
    if not isinstance(relative, str):
        raise ValueError("source path is absent")
    path = _inside(root, relative)
    expected = _digest(payload.get("source_sha256"), "source")
    if _sha(_file(path, limit=1024 * 1024)) != expected:
        raise ValueError("synthetic source changed")


def _lease(root: Path, payload: Mapping[str, Any]) -> DeadlineLease:
    expected = _digest(payload.get("deadline_sha256"), "deadline")
    path = _inside(root, "deadline.json")
    if _sha(_file(path)) != expected:
        raise ValueError("persisted deadline differs from the contract")
    return DeadlineLease.load(path)


def _contract(root: Path, expected_contract_sha256: str) -> dict[str, Any]:
    digest = _digest(expected_contract_sha256, "external contract")
    record = _read(root, f"contracts/{digest}.json", schema="synthetic_case_contract_v1",
                   expected_sha256=digest)
    payload = record["payload"]
    if (
        set(payload) != {"case_id", "attempt_id", "source_relpath", "source_sha256",
                         "deadline_sha256", "expected_value"}
        or not isinstance(payload["case_id"], str)
        or _TOKEN.fullmatch(payload["case_id"]) is None
        or not isinstance(payload["attempt_id"], str)
        or _ATTEMPT.fullmatch(payload["attempt_id"]) is None
        or type(payload["expected_value"]) is not int
        or not -(2**31) <= payload["expected_value"] < 2**31
    ):
        raise ValueError("synthetic contract fields are invalid")
    _source(root, payload)
    _lease(root, payload)
    return record


def prepare_synthetic_contract(
    root: Path, *, case_id: str, attempt_id: str, source_relpath: str,
    expected_source_sha256: str, expected_value: int,
) -> str:
    """Publish a write-once challenge and return its digest for external pinning."""
    admitted = _root(root)
    if not isinstance(case_id, str) or _TOKEN.fullmatch(case_id) is None:
        raise ValueError("invalid synthetic case ID")
    if not isinstance(attempt_id, str) or _ATTEMPT.fullmatch(attempt_id) is None:
        raise ValueError("invalid synthetic attempt ID")
    if type(expected_value) is not int or not -(2**31) <= expected_value < 2**31:
        raise ValueError("synthetic value must be a signed 32-bit integer")
    expected = _digest(expected_source_sha256, "external source")
    payload = {
        "case_id": case_id, "attempt_id": attempt_id, "source_relpath": source_relpath,
        "source_sha256": expected,
        "deadline_sha256": _sha(_file(_inside(admitted, "deadline.json"))),
        "expected_value": expected_value,
    }
    _source(admitted, payload)
    _lease(admitted, payload)
    record = _record("synthetic_case_contract_v1", payload)
    _publish(admitted, f"contracts/{record['sha256']}.json", record)
    _contract(admitted, record["sha256"])
    return str(record["sha256"])


def _expected_proposal(contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = contract["payload"]
    return _record("synthetic_case_proposal_v1", {
        "contract_sha256": contract["sha256"], "case_id": payload["case_id"],
        "attempt_id": payload["attempt_id"], "source_sha256": payload["source_sha256"],
        "deadline_sha256": payload["deadline_sha256"], "value": payload["expected_value"],
    })


def write_synthetic_proposal(root: Path, expected_contract_sha256: str) -> str:
    """Child-only challenge response; no scientific result or cell is created."""
    admitted = _root(root)
    contract = _contract(admitted, expected_contract_sha256)
    lease = _lease(admitted, contract["payload"])
    now = datetime.now(UTC)
    if now >= lease.attempt_deadline_utc or now >= lease.session_deadline_utc:
        raise ValueError("synthetic child deadline expired")
    proposal = _expected_proposal(contract)
    _source(admitted, contract["payload"])
    _publish(admitted, f"proposals/{contract['sha256']}.json", proposal)
    return str(proposal["sha256"])


def write_synthetic_frame(
    root: Path, expected_contract_sha256: str, inherited_write_handle: int,
) -> None:
    """Return one canonical synthetic proposal through the inherited child handle."""
    if (
        sys.platform != "win32" or type(inherited_write_handle) is not int
        or inherited_write_handle <= 0
    ):
        raise ValueError("Windows inherited result handle required")
    admitted = _root(root)
    contract = _contract(admitted, expected_contract_sha256)
    lease = _lease(admitted, contract["payload"])
    now = datetime.now(UTC)
    if now >= lease.attempt_deadline_utc or now >= lease.session_deadline_utc:
        raise ValueError("synthetic child deadline expired")
    _source(admitted, contract["payload"])
    raw = (canonical_config_json(_expected_proposal(contract)) + "\n").encode("utf-8")
    if len(raw) > _MAX_RECORD_BYTES:
        raise ValueError("synthetic proposal exceeds frame cap")
    # The child may launch descendants in future probes. Keep this private
    # capability out of any later child handle inheritance.
    os.set_handle_inheritable(inherited_write_handle, False)
    import msvcrt  # noqa: PLC0415

    descriptor = msvcrt.open_osfhandle(inherited_write_handle, os.O_WRONLY | os.O_BINARY)
    with os.fdopen(descriptor, "wb", buffering=0) as stream:
        framed = struct.pack("<I", len(raw)) + raw
        written = 0
        while written < len(framed):
            count = stream.write(framed[written:])
            if count is None or count <= 0:
                raise OSError("synthetic frame write made no progress")
            written += count


def _proposal(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    expected = _expected_proposal(contract)
    return _read(root, f"proposals/{contract['sha256']}.json",
                 schema="synthetic_case_proposal_v1", expected_sha256=expected["sha256"])


def _guard(root: Path, floor: ResourceFloor, sensor: Callable[[Path], ResourceSample]) -> None:
    try:
        sample = sensor(root)
    except Exception as exc:
        raise SupervisionError("transaction resource sensor failed") from exc
    if (
        type(sample.free_disk_bytes) is not int or type(sample.available_ram_bytes) is not int
        or sample.free_disk_bytes < floor.disk_bytes or sample.available_ram_bytes < floor.ram_bytes
    ):
        raise SupervisionError("transaction disk/RAM floor failed")


@dataclass(frozen=True, slots=True)
class SyntheticAttestation:
    contract_sha256: str
    proposal_sha256: str
    attestation_sha256: str
    child_pid: int


def _start(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    relative = f"starts/{contract['sha256']}.json"
    path = _inside(root, relative)
    if path.exists() or path.is_symlink():
        raise ValueError("a case attempt has already started")
    lease = _lease(root, contract["payload"])
    now = datetime.now(UTC)
    if now >= lease.attempt_deadline_utc or now >= lease.session_deadline_utc:
        raise SupervisionError("synthetic attempt deadline expired before start")
    start = _record("synthetic_case_start_v1", {
        "contract_sha256": contract["sha256"],
        "deadline_sha256": contract["payload"]["deadline_sha256"],
        "source_sha256": contract["payload"]["source_sha256"],
        "owner_nonce": secrets.token_hex(16), "parent_pid": os.getpid(),
        "started_utc": now.isoformat(),
    })
    _publish(root, relative, start)
    return start


def _verify_start(root: Path, contract: Mapping[str, Any], expected_sha256: str) -> None:
    record = _read(root, f"starts/{contract['sha256']}.json",
                   schema="synthetic_case_start_v1", expected_sha256=expected_sha256)
    payload = record["payload"]
    try:
        started = datetime.fromisoformat(payload["started_utc"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid synthetic start time") from exc
    lease = _lease(root, contract["payload"])
    offset = started.utcoffset()
    if (
        set(payload) != {"contract_sha256", "deadline_sha256", "source_sha256",
                         "owner_nonce", "parent_pid", "started_utc"}
        or payload["contract_sha256"] != contract["sha256"]
        or payload["deadline_sha256"] != contract["payload"]["deadline_sha256"]
        or payload["source_sha256"] != contract["payload"]["source_sha256"]
        or not isinstance(payload["owner_nonce"], str)
        or _ATTEMPT.fullmatch(payload["owner_nonce"]) is None
        or type(payload["parent_pid"]) is not int or payload["parent_pid"] <= 0
        or offset is None or offset.total_seconds() != 0
        or started >= lease.attempt_deadline_utc or started >= lease.session_deadline_utc
    ):
        raise ValueError("synthetic start record differs from its pinned attempt")


def run_synthetic_transaction(
    root: Path, *, expected_contract_sha256: str, cwd: Path,
    command: Sequence[str] | None = None, floor: ResourceFloor | None = None,
    sensor: Callable[[Path], ResourceSample] = live_resources,
) -> SyntheticAttestation:
    """Attest exact proposal bytes observed after timely supervised completion.

    File publication does not prove child authorship. The deadline covers the
    child and proposal validation, not the final filesystem write duration.
    """
    admitted = _root(root)
    contract = _contract(admitted, expected_contract_sha256)
    contract_sha = str(contract["sha256"])
    if _inside(admitted, f"proposals/{contract_sha}.json").exists():
        raise ValueError("a preexisting proposal cannot be freshly attested")
    if _inside(admitted, f"attestations/{contract_sha}.json").exists():
        raise ValueError("a case attempt cannot be run twice")
    start = _start(admitted, contract)
    active_floor = ResourceFloor() if floor is None else floor
    args = list(command) if command is not None else [
        sys.executable, "-B", "-m", "evaluation.phase2_case_transaction", "child",
        str(admitted), contract_sha,
    ]

    def transaction_sensor(_cwd: Path) -> ResourceSample:
        return sensor(admitted)

    result = run_supervised(
        args, cwd=cwd, deadline_path=_inside(admitted, "deadline.json"),
        floor=active_floor, sensor=transaction_sensor,
    )
    if result.reason != "normal" or result.exit_code != 0 or result.pid <= 0:
        raise SupervisionError("synthetic child did not complete normally")
    # The external contract is reloaded after the child and before attestation.
    if _contract(admitted, contract_sha) != contract:
        raise ValueError("synthetic contract changed during execution")
    _verify_start(admitted, contract, str(start["sha256"]))
    proposal = _proposal(admitted, contract)
    lease = _lease(admitted, contract["payload"])
    _source(admitted, contract["payload"])
    _guard(admitted, active_floor, sensor)
    now = datetime.now(UTC)
    if now >= lease.attempt_deadline_utc or now >= lease.session_deadline_utc:
        raise SupervisionError("synthetic attestation missed its durable deadline")
    receipt = _record("synthetic_case_attestation_v1", {
        "contract_sha256": contract_sha, "proposal_sha256": proposal["sha256"],
        "start_sha256": start["sha256"],
        "deadline_sha256": contract["payload"]["deadline_sha256"],
        "source_sha256": contract["payload"]["source_sha256"],
        "child_pid": result.pid, "child_exit_code": 0, "reason": "normal",
        "proposal_validated_utc": now.isoformat(),
    })
    _publish(admitted, f"attestations/{contract_sha}.json", receipt)
    return SyntheticAttestation(contract_sha, str(proposal["sha256"]),
                                str(receipt["sha256"]), result.pid)


def run_synthetic_transaction_channel(
    root: Path, *, expected_contract_sha256: str, cwd: Path,
    command: Sequence[str] | None = None, floor: ResourceFloor | None = None,
    sensor: Callable[[Path], ResourceSample] = live_resources,
) -> SyntheticAttestation:
    """Accept a proposal only from the owned Job's inherited result channel.

    This remains a synthetic engineering rehearsal. The frame is a capability
    of the supervised process tree, and the parent publishes its bytes only
    after normal whole-Job completion and durable guard checks.
    """
    admitted = _root(root)
    contract = _contract(admitted, expected_contract_sha256)
    contract_sha = str(contract["sha256"])
    proposal_path = _inside(admitted, f"proposals/{contract_sha}.json")
    attestation_path = _inside(admitted, f"attestations/{contract_sha}.json")
    if proposal_path.exists() or proposal_path.is_symlink():
        raise ValueError("a preexisting proposal cannot be freshly attested")
    if attestation_path.exists() or attestation_path.is_symlink():
        raise ValueError("a case attempt cannot be run twice")
    start = _start(admitted, contract)
    active_floor = ResourceFloor() if floor is None else floor
    args = list(command) if command is not None else [
        sys.executable, "-B", "-m", "evaluation.phase2_case_transaction",
        "child-channel", str(admitted), contract_sha, "{result_handle}",
    ]

    def transaction_sensor(_cwd: Path) -> ResourceSample:
        return sensor(admitted)

    outcome = run_supervised_with_frame(
        args, cwd=cwd, deadline_path=_inside(admitted, "deadline.json"),
        floor=active_floor, sensor=transaction_sensor, max_frame_bytes=_MAX_RECORD_BYTES,
    )
    result, frame = outcome.result, outcome.frame
    if result.reason != "normal" or result.exit_code != 0 or result.pid <= 0:
        raise SupervisionError("synthetic child did not complete normally")
    if _contract(admitted, contract_sha) != contract:
        raise ValueError("synthetic contract changed during execution")
    _verify_start(admitted, contract, str(start["sha256"]))
    expected = _expected_proposal(contract)
    if frame != (canonical_config_json(expected) + "\n").encode("utf-8"):
        raise ValueError("synthetic child frame differs from expected proposal")
    lease = _lease(admitted, contract["payload"])
    _source(admitted, contract["payload"])
    _guard(admitted, active_floor, sensor)
    now = datetime.now(UTC)
    if now >= lease.attempt_deadline_utc or now >= lease.session_deadline_utc:
        raise SupervisionError("synthetic attestation missed its durable deadline")
    _publish_fresh(admitted, f"proposals/{contract_sha}.json", expected)
    proposal = _proposal(admitted, contract)
    if frame != _file(proposal_path):
        raise ValueError("parent-published synthetic proposal differs from child frame")
    receipt = _record("synthetic_case_attestation_channel_v1", {
        "contract_sha256": contract_sha, "proposal_sha256": proposal["sha256"],
        "frame_sha256": _sha(frame), "start_sha256": start["sha256"],
        "deadline_sha256": contract["payload"]["deadline_sha256"],
        "source_sha256": contract["payload"]["source_sha256"],
        "child_pid": result.pid, "child_exit_code": 0, "reason": "normal",
        "proposal_validated_utc": now.isoformat(),
    })
    _publish(admitted, f"attestations/{contract_sha}.json", receipt)
    return SyntheticAttestation(contract_sha, str(proposal["sha256"]),
                                str(receipt["sha256"]), result.pid)


def verify_synthetic_attestation_channel(
    root: Path, *, expected_contract_sha256: str, expected_attestation_sha256: str,
) -> SyntheticAttestation:
    """Replay a channel attestation using its caller-held external digest."""
    admitted = _root(root)
    contract = _contract(admitted, expected_contract_sha256)
    proposal = _proposal(admitted, contract)
    receipt = _read(
        admitted, f"attestations/{contract['sha256']}.json",
        schema="synthetic_case_attestation_channel_v1",
        expected_sha256=_digest(expected_attestation_sha256, "external attestation"),
    )
    payload = receipt["payload"]
    lease = _lease(admitted, contract["payload"])
    _verify_start(admitted, contract, _digest(payload.get("start_sha256"), "external start"))
    try:
        validated = datetime.fromisoformat(payload["proposal_validated_utc"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid attested completion time") from exc
    offset = validated.utcoffset()
    if (
        set(payload) != {"contract_sha256", "proposal_sha256", "frame_sha256",
                         "start_sha256", "deadline_sha256", "source_sha256",
                         "child_pid", "child_exit_code", "reason", "proposal_validated_utc"}
        or payload["contract_sha256"] != contract["sha256"]
        or payload["proposal_sha256"] != proposal["sha256"]
        or payload["frame_sha256"] != _sha(_file(_inside(
            admitted, f"proposals/{contract['sha256']}.json")))
        or payload["deadline_sha256"] != contract["payload"]["deadline_sha256"]
        or payload["source_sha256"] != contract["payload"]["source_sha256"]
        or type(payload["child_pid"]) is not int or payload["child_pid"] <= 0
        or type(payload["child_exit_code"]) is not int or payload["child_exit_code"] != 0
        or payload["reason"] != "normal" or offset is None or offset.total_seconds() != 0
        or validated >= lease.attempt_deadline_utc
        or validated >= lease.session_deadline_utc
    ):
        raise ValueError("synthetic channel attestation does not prove pinned attempt")
    return SyntheticAttestation(str(contract["sha256"]), str(proposal["sha256"]),
                                str(receipt["sha256"]), int(payload["child_pid"]))


def verify_synthetic_attestation(
    root: Path, *, expected_contract_sha256: str, expected_attestation_sha256: str,
) -> SyntheticAttestation:
    """Replay verification requires an attestation digest held outside the root."""
    admitted = _root(root)
    contract = _contract(admitted, expected_contract_sha256)
    proposal = _proposal(admitted, contract)
    receipt = _read(
        admitted, f"attestations/{contract['sha256']}.json",
        schema="synthetic_case_attestation_v1",
        expected_sha256=_digest(expected_attestation_sha256, "external attestation"),
    )
    payload = receipt["payload"]
    lease = _lease(admitted, contract["payload"])
    _verify_start(admitted, contract, _digest(payload.get("start_sha256"), "external start"))
    try:
        validated = datetime.fromisoformat(payload["proposal_validated_utc"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid attested completion time") from exc
    if (
        set(payload) != {"contract_sha256", "proposal_sha256", "start_sha256", "deadline_sha256",
                         "source_sha256", "child_pid", "child_exit_code", "reason",
                         "proposal_validated_utc"}
        or payload["contract_sha256"] != contract["sha256"]
        or payload["proposal_sha256"] != proposal["sha256"]
        or payload["deadline_sha256"] != contract["payload"]["deadline_sha256"]
        or payload["source_sha256"] != contract["payload"]["source_sha256"]
        or type(payload["child_pid"]) is not int or payload["child_pid"] <= 0
        or type(payload["child_exit_code"]) is not int or payload["child_exit_code"] != 0
        or payload["reason"] != "normal" or validated.tzinfo is None
        or (offset := validated.utcoffset()) is None or offset.total_seconds() != 0
        or validated >= lease.attempt_deadline_utc
        or validated >= lease.session_deadline_utc
    ):
        raise ValueError("synthetic attestation does not prove its pinned attempt")
    return SyntheticAttestation(str(contract["sha256"]), str(proposal["sha256"]),
                                str(receipt["sha256"]), int(payload["child_pid"]))


def _main() -> int:
    if len(sys.argv) == 5 and sys.argv[1] == "child-channel":
        write_synthetic_frame(Path(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
        return 0
    if len(sys.argv) != 4 or sys.argv[1] != "child":
        raise SystemExit(
            "usage: python -m evaluation.phase2_case_transaction child ROOT CONTRACT_SHA"
        )
    write_synthetic_proposal(Path(sys.argv[2]), sys.argv[3])
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
