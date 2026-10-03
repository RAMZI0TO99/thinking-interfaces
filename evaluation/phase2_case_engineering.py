"""Synthetic CaseRecorder integration; never a Cho fit or scientific cell.

This internal adapter uses the transaction module's validated `_contract` reader
and the recorder's locked intent verifier. A production case runner requires a
separate public contract, selection admission, and metric validation.
The parent receives the proposal through an inherited, bounded child result
channel and publishes its exact bytes after normal whole-Job completion. The
binding compares module and interpreter bytes across retries, but does not
prove executable bytes at the instant of launch. This is synthetic
containment evidence only.
The caller must retain the previewed case-binding SHA outside the writable
recorder and transaction directories and supply it for run and recovery.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.config import canonical_config_json, config_digest
from evaluation import phase2_case_transaction as transaction
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import envelope, verify_envelope, write_once
from evaluation.phase2_runner import MAXIMUM_ATTEMPTS, CasePlan, CaseRecorder


@dataclass(frozen=True, slots=True)
class EngineeringCaseResult:
    attestation_sha256: str
    engineering_receipt: Path


def engineering_attempt_id(plan: CasePlan, attempt: int) -> str:
    """Derive the synthetic contract's attempt ID from the entire recorder plan."""
    if not isinstance(plan, CasePlan):
        raise ValueError("explicit synthetic CasePlan required")
    if plan.dataset != "synthetic_engineering" or plan.method != "synthetic_echo":
        raise ValueError("only synthetic engineering plans are admitted")
    if type(attempt) is not int or not 1 <= attempt <= MAXIMUM_ATTEMPTS:
        raise ValueError("synthetic engineering attempt is out of range")
    return config_digest({
        "purpose": "synthetic_engineering_attempt_v1",
        "case": asdict(plan), "attempt": attempt,
    })[:32]


def _transaction_root(recorder: CaseRecorder, root: Path) -> Path:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("synthetic transaction root must be an ordinary directory")
    admitted = root.resolve(strict=True)
    base = recorder.output_root.parent.resolve()
    if admitted == base or not admitted.is_relative_to(base):
        raise ValueError("synthetic transaction must stay inside recorder Phase II output")
    if admitted == recorder.output_root or admitted.is_relative_to(recorder.output_root):
        raise ValueError("synthetic transaction cannot occupy the recorder directory")
    return admitted


def _child_cwd(cwd: Path) -> Path:
    expected = Path(__file__).resolve().parents[1]
    if (
        not cwd.is_absolute() or cwd != expected or cwd.is_symlink()
        or not cwd.is_dir() or cwd.resolve(strict=True) != expected
    ):
        raise ValueError("synthetic child cwd must be the exact project root")
    return expected


def _bound_contract(
    recorder: CaseRecorder, plan: CasePlan, attempt: int, root: Path,
    expected_contract_sha256: str,
) -> Path:
    expected_attempt_id = engineering_attempt_id(plan, attempt)
    admitted = _transaction_root(recorder, root)
    # The private reader verifies canonical bytes, external digest, source and
    # durable deadline before returning any contract fields.
    contract = transaction._contract(admitted, expected_contract_sha256)
    payload = contract["payload"]
    if payload["case_id"] != plan.case_id or payload["attempt_id"] != expected_attempt_id:
        raise ValueError("synthetic contract differs from recorder case or attempt")
    return admitted


def _file_sha256(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("synthetic worker file is missing or linked")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding_path(recorder: CaseRecorder, plan: CasePlan) -> Path:
    return recorder.output_root / "engineering_bindings" / f"{plan.case_id}.json"


def _binding_payload(
    plan: CasePlan, contract: dict[str, Any], *, initial_contract_sha256: str,
) -> dict[str, Any]:
    payload = contract["payload"]
    module = Path(transaction.__file__).resolve(strict=True)
    executable = Path(sys.executable).resolve(strict=True)
    return {
        "purpose": "synthetic_case_input_binding_v1", "case": asdict(plan),
        "initial_contract_sha256": initial_contract_sha256,
        "source_relpath": payload["source_relpath"],
        "source_sha256": payload["source_sha256"],
        "expected_value": payload["expected_value"],
        "child_cwd": str(Path(__file__).resolve().parents[1]),
        "child_module_sha256": _file_sha256(module),
        "python_executable": str(executable),
        "python_executable_sha256": _file_sha256(executable),
        "engineering_only": True,
    }


def _read_binding(recorder: CaseRecorder, plan: CasePlan) -> dict[str, Any]:
    path = _binding_path(recorder, plan)
    if (
        path.parent.is_symlink() or not path.parent.is_dir()
        or path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1
        or not path.resolve().is_relative_to(recorder.output_root)
        or path.stat().st_size > 16 * 1024
    ):
        raise ValueError("synthetic case input binding is missing or aliased")
    raw = path.read_bytes()
    if len(raw) > 16 * 1024:
        raise ValueError("synthetic case input binding exceeds its byte cap")
    try:
        record = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("synthetic case input binding is unreadable") from exc
    if not isinstance(record, dict) or not isinstance(record.get("payload"), dict):
        raise ValueError("synthetic case input binding has invalid schema")
    payload = record["payload"]
    if (
        record.get("kind") != "engineering_smoke"
        or not verify_envelope(record, kind="engineering_smoke", expected_payload=payload)
        or raw != (canonical_config_json(record) + "\n").encode("utf-8")
        or payload.get("purpose") != "synthetic_case_input_binding_v1"
        or payload.get("case") != asdict(plan)
    ):
        raise ValueError("synthetic case input binding no longer verifies")
    return record


def _publish_binding(
    recorder: CaseRecorder, plan: CasePlan, contract: dict[str, Any],
    *, expected_case_binding_sha256: str,
) -> str:
    payload = _binding_payload(
        plan, contract, initial_contract_sha256=str(contract["sha256"]),
    )
    record = envelope("engineering_smoke", payload)
    if record["sha256"] != expected_case_binding_sha256:
        raise ValueError("synthetic case binding differs from external pin")
    write_once(_binding_path(recorder, plan), record, output_root=recorder.output_root)
    if _read_binding(recorder, plan) != record:
        raise ValueError("published synthetic case binding changed")
    return str(record["sha256"])


def _verify_binding(
    recorder: CaseRecorder, plan: CasePlan, contract: dict[str, Any],
    *, attempt: int, expected_case_binding_sha256: str,
) -> str:
    record = _read_binding(recorder, plan)
    if record["sha256"] != expected_case_binding_sha256:
        raise ValueError("synthetic case binding differs from external pin")
    payload = record["payload"]
    initial = payload.get("initial_contract_sha256")
    if not isinstance(initial, str):
        raise ValueError("synthetic case input binding lacks initial contract")
    expected = _binding_payload(plan, contract, initial_contract_sha256=initial)
    if payload != expected or (attempt == 1 and initial != contract["sha256"]):
        raise ValueError("synthetic retry input differs from case binding")
    if attempt == 2:
        failure_path = (recorder.output_root / "attempts" /
                        f"{plan.case_id}.attempt1.failure.json")
        if (
            failure_path.is_symlink() or not failure_path.is_file()
            or failure_path.stat().st_nlink != 1 or failure_path.stat().st_size > 16 * 1024
        ):
            raise ValueError("initial failed attempt does not pin synthetic input")
        raw = failure_path.read_bytes()
        if len(raw) > 16 * 1024:
            raise ValueError("initial failed attempt exceeds its byte cap")
        try:
            failure = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("initial failed attempt is unreadable") from exc
        if not isinstance(failure, dict) or not isinstance(failure.get("payload"), dict):
            raise ValueError("initial failed attempt has invalid schema")
        failed = failure["payload"]
        if (
            raw != (canonical_config_json(failure) + "\n").encode("utf-8")
            or not verify_envelope(failure, kind="engineering_smoke", expected_payload=failed)
            or failed.get("purpose") != "pilot_case_failure"
            or failed.get("case") != asdict(plan) or failed.get("attempt") != 1
            or not isinstance(failed.get("reason"), dict)
            or failed["reason"].get("case_binding_sha256") != record["sha256"]
        ):
            raise ValueError("initial failed attempt has different synthetic input binding")
    return str(record["sha256"])


def preview_case_binding_sha256(
    recorder: CaseRecorder, plan: CasePlan, *, transaction_root: Path,
    expected_contract_sha256: str, cwd: Path,
) -> str:
    """Read-only initial binding digest for the caller to retain outside writable runs."""
    if not isinstance(recorder, CaseRecorder):
        raise ValueError("CaseRecorder required")
    _child_cwd(cwd)
    admitted = _bound_contract(recorder, plan, 1, transaction_root,
                               expected_contract_sha256)
    contract = transaction._contract(admitted, expected_contract_sha256)
    payload = _binding_payload(
        plan, contract, initial_contract_sha256=expected_contract_sha256,
    )
    return str(envelope("engineering_smoke", payload)["sha256"])


def run_engineering_case(
    recorder: CaseRecorder, plan: CasePlan, *, attempt: int,
    transaction_root: Path, expected_contract_sha256: str,
    expected_case_binding_sha256: str, cwd: Path,
) -> EngineeringCaseResult:
    """Claim, supervise and record one engineering-only outcome under one lock.

    A verified child/guard stop records a failed attempt and propagates the
    error. Once the attestation verifies, a recorder publication interruption
    leaves its write-once engineering intent for externally pinned recovery.
    """
    if not isinstance(recorder, CaseRecorder):
        raise ValueError("CaseRecorder required")
    require_digest(expected_case_binding_sha256, "external case binding")
    admitted_cwd = _child_cwd(cwd)
    admitted = _bound_contract(
        recorder, plan, attempt, transaction_root, expected_contract_sha256,
    )
    if attempt == 1 and preview_case_binding_sha256(
        recorder, plan, transaction_root=admitted,
        expected_contract_sha256=expected_contract_sha256, cwd=admitted_cwd,
    ) != expected_case_binding_sha256:
        raise ValueError("synthetic case binding differs from external pin")
    with recorder.case_session(plan) as case:
        # Recheck under the full-lifetime OS lock before writing the claim.
        _bound_contract(recorder, plan, attempt, admitted, expected_contract_sha256)
        contract = transaction._contract(admitted, expected_contract_sha256)
        if attempt == 2:
            binding_sha = _verify_binding(
                recorder, plan, contract, attempt=attempt,
                expected_case_binding_sha256=expected_case_binding_sha256,
            )
        elif str(envelope("engineering_smoke", _binding_payload(
            plan, contract, initial_contract_sha256=expected_contract_sha256,
        ))["sha256"]) != expected_case_binding_sha256:
            raise ValueError("synthetic case binding differs from external pin")
        case.claim_new(worker="synthetic_case_engineering", attempt=attempt)
        if attempt == 1:
            binding_sha = _publish_binding(
                recorder, plan, contract,
                expected_case_binding_sha256=expected_case_binding_sha256,
            )
        try:
            attested = transaction.run_synthetic_transaction_channel(
                admitted, expected_contract_sha256=expected_contract_sha256,
                cwd=admitted_cwd,
            )
        except Exception as exc:
            # A child may have published an attestation before a later I/O error.
            # An existing attestation, even malformed, requires review instead
            # of converting this attempt into a retryable failure.
            attestation_path = admitted / "attestations" / f"{expected_contract_sha256}.json"
            if attestation_path.exists() or attestation_path.is_symlink():
                raise
            case.record_failure(attempt=attempt, reason={
                "error": f"synthetic transaction stopped: {type(exc).__name__}: {exc}",
                "case_binding_sha256": binding_sha,
            })
            raise
        # Once a durable attestation exists, later drift is quarantine-needed.
        # No failure may be written because that would admit a second attempt.
        verified = transaction.verify_synthetic_attestation_channel(
            admitted, expected_contract_sha256=expected_contract_sha256,
            expected_attestation_sha256=attested.attestation_sha256,
        )
        if verified != attested:
            raise ValueError("synthetic attestation changed before recorder publication")
        _bound_contract(recorder, plan, attempt, admitted, expected_contract_sha256)
        _verify_binding(
            recorder, plan, contract, attempt=attempt,
            expected_case_binding_sha256=expected_case_binding_sha256,
        )
        receipt = case.record_engineering_success(
            attempt=attempt, attested_evidence_sha256=attested.attestation_sha256,
        )
        return EngineeringCaseResult(attested.attestation_sha256, receipt)


def recover_engineering_case(
    recorder: CaseRecorder, plan: CasePlan, *, attempt: int,
    transaction_root: Path, expected_contract_sha256: str,
    expected_attestation_sha256: str, expected_case_binding_sha256: str,
) -> Path:
    """Recover only a matching engineering receipt using an external SHA pin."""
    if not isinstance(recorder, CaseRecorder):
        raise ValueError("CaseRecorder required")
    require_digest(expected_case_binding_sha256, "external case binding")
    admitted = _bound_contract(
        recorder, plan, attempt, transaction_root, expected_contract_sha256,
    )
    with recorder.case_session(plan) as case:
        _bound_contract(recorder, plan, attempt, admitted, expected_contract_sha256)
        contract = transaction._contract(admitted, expected_contract_sha256)
        _verify_binding(
            recorder, plan, contract, attempt=attempt,
            expected_case_binding_sha256=expected_case_binding_sha256,
        )
        transaction.verify_synthetic_attestation_channel(
            admitted, expected_contract_sha256=expected_contract_sha256,
            expected_attestation_sha256=expected_attestation_sha256,
        )
        # Verify the intent's attempt before the facade may replay a receipt.
        intended_attempt = recorder._verified_engineering_intent(
            plan, expected_attested_evidence_sha256=expected_attestation_sha256,
        )
        if intended_attempt != attempt:
            raise ValueError("engineering intent attempt differs from synthetic contract")
        return case.recover_engineering_success(
            expected_attested_evidence_sha256=expected_attestation_sha256,
        )
