"""Actual Windows synthetic child plus locked engineering recorder tests."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from core.config import canonical_config_json
from evaluation import phase2_case_engineering as engineering
from evaluation import phase2_case_transaction as transaction
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan, CaseRecorder
from evaluation.phase2_supervision_primitives import (
    GIB,
    DeadlineLease,
    ResourceSample,
    SupervisionError,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Objects only")
_PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def root(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    def ample_resources(_root: Path) -> ResourceSample:
        return ResourceSample(21 * GIB, 5 * GIB)

    monkeypatch.setattr(
        transaction,
        "run_synthetic_transaction_channel",
        partial(transaction.run_synthetic_transaction_channel, sensor=ample_resources),
    )
    base = _PROJECT_ROOT / "tmp"
    base.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="case-engineering-", dir=base) as directory:
        yield Path(directory)


def _plan(*, repetition: int = 1) -> CasePlan:
    return CasePlan("synthetic_engineering", "unit", "synthetic_echo", 1, 23, repetition)


def _prepare(
    root: Path, plan: CasePlan, attempt: int = 1, *, suffix: str = "",
    source_bytes: bytes = b"fixed synthetic input\n", expected_value: int = 7,
) -> tuple[Path, str]:
    transaction_root = root / "runs" / "phase2" / f"synthetic-attempt{attempt}{suffix}"
    transaction_root.mkdir(parents=True)
    now = datetime.now(UTC)
    DeadlineLease.open_or_create(
        transaction_root / "deadline.json",
        attempt_deadline_utc=now + timedelta(seconds=5),
        session_deadline_utc=now + timedelta(seconds=6),
    )
    source = transaction_root / "source.bin"
    source.write_bytes(source_bytes)
    digest = transaction.prepare_synthetic_contract(
        transaction_root, case_id=plan.case_id,
        attempt_id=engineering.engineering_attempt_id(plan, attempt),
        source_relpath="source.bin",
        expected_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        expected_value=expected_value,
    )
    return transaction_root, digest


def _recorder(root: Path) -> CaseRecorder:
    return CaseRecorder(root, output_root=root / "runs" / "phase2" / "recorder")


def _binding_pin(recorder: CaseRecorder, plan: CasePlan, root: Path, contract: str) -> str:
    return engineering.preview_case_binding_sha256(
        recorder, plan, transaction_root=root,
        expected_contract_sha256=contract, cwd=_PROJECT_ROOT,
    )


def _assert_no_scientific_cell(recorder: CaseRecorder) -> None:
    assert not (recorder.output_root / "cells").exists()
    assert not (recorder.output_root / "successes").exists()


def test_synthetic_success_and_external_recovery_publish_no_cell(root: Path) -> None:
    plan = _plan()
    recorder = _recorder(root)
    transaction_root, contract_sha = _prepare(root, plan)
    binding_sha = _binding_pin(recorder, plan, transaction_root, contract_sha)
    assert not (recorder.output_root / "engineering_bindings").exists()
    with pytest.raises(ValueError, match="external pin"):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256="a" * 64, cwd=_PROJECT_ROOT,
        )
    assert not (recorder.output_root / "claims").exists()
    result = engineering.run_engineering_case(
        recorder, plan, attempt=1, transaction_root=transaction_root,
        expected_contract_sha256=contract_sha,
        expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
    )
    receipt = json.loads(result.engineering_receipt.read_text(encoding="utf-8"))
    assert receipt["kind"] == "engineering_smoke"
    assert receipt["payload"]["purpose"] == "pilot_case_engineering_success"
    assert receipt["payload"]["attested_evidence_sha256"] == result.attestation_sha256
    assert receipt["payload"]["engineering_only"] is True
    assert engineering.recover_engineering_case(
        recorder, plan, attempt=1, transaction_root=transaction_root,
        expected_contract_sha256=contract_sha,
        expected_attestation_sha256=result.attestation_sha256,
        expected_case_binding_sha256=binding_sha,
    ) == result.engineering_receipt
    with pytest.raises(ValueError, match="external pin"):
        engineering.recover_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_attestation_sha256=result.attestation_sha256,
            expected_case_binding_sha256="a" * 64,
        )
    with pytest.raises(ValueError, match="engineering-completed"):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
        )
    _assert_no_scientific_cell(recorder)


def test_contract_case_and_attempt_mismatch_leave_no_claim(root: Path) -> None:
    plan = _plan()
    recorder = _recorder(root)
    transaction_root, contract_sha = _prepare(root, plan, attempt=2)
    with pytest.raises(ValueError, match="case or attempt"):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256="a" * 64, cwd=_PROJECT_ROOT,
        )
    with pytest.raises(ValueError, match="case or attempt"):
        engineering.run_engineering_case(
            recorder, _plan(repetition=2), attempt=2,
            transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256="a" * 64, cwd=_PROJECT_ROOT,
        )
    assert not (recorder.output_root / "claims").exists()
    assert not (recorder.output_root / "attempts").exists()
    _assert_no_scientific_cell(recorder)


def test_shadow_package_cwd_is_rejected_before_claim(root: Path) -> None:
    plan = _plan()
    recorder = _recorder(root)
    transaction_root, contract_sha = _prepare(root, plan)
    binding_sha = _binding_pin(recorder, plan, transaction_root, contract_sha)
    shadow = root / "shadow"
    (shadow / "evaluation").mkdir(parents=True)
    (shadow / "evaluation" / "__init__.py").write_text("# shadow\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exact project root"):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256=binding_sha, cwd=shadow,
        )
    assert not (recorder.output_root / "claims").exists()
    assert not (transaction_root / "starts").exists()
    _assert_no_scientific_cell(recorder)


def test_failure_blocks_fresh_attempt1_launch_then_allows_attempt2(root: Path) -> None:
    plan = _plan()
    recorder = _recorder(root)
    transaction_root, contract_sha = _prepare(root, plan)
    binding_sha = _binding_pin(recorder, plan, transaction_root, contract_sha)
    actual = transaction.run_synthetic_transaction_channel

    def failing_child(
        selected_root: Path, *, expected_contract_sha256: str, cwd: Path,
    ) -> transaction.SyntheticAttestation:
        return actual(
            selected_root, expected_contract_sha256=expected_contract_sha256, cwd=cwd,
            command=[sys.executable, "-c", "raise SystemExit(3)", "{result_handle}"],
        )

    with (
        patch.object(transaction, "run_synthetic_transaction_channel", failing_child),
        pytest.raises(SupervisionError, match="frame|result|did not complete normally"),
    ):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
        )
    failure_path = recorder.output_root / "attempts" / f"{plan.case_id}.attempt1.failure.json"
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    assert failure["payload"]["engineering_only"] is True
    assert "SupervisionError" in failure["payload"]["reason"]["error"]
    replay_root, replay_contract = _prepare(root, plan, suffix="-fresh-replay")
    assert replay_contract != contract_sha
    with (
        patch.object(transaction, "run_synthetic_transaction_channel",
                     side_effect=AssertionError("a failed attempt launched another child")),
        pytest.raises(ValueError, match="external pin|already claimed|failed"),
    ):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=replay_root,
            expected_contract_sha256=replay_contract,
            expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
        )
    assert not (replay_root / "starts").exists()
    assert not (replay_root / "proposals").exists()
    assert not (replay_root / "attestations").exists()
    for suffix, source_bytes, value in (
        ("-changed-source", b"different input\n", 7),
        ("-changed-value", b"fixed synthetic input\n", 8),
    ):
        changed_root, changed_contract = _prepare(
            root, plan, attempt=2, suffix=suffix,
            source_bytes=source_bytes, expected_value=value,
        )
        with pytest.raises(ValueError, match="retry input differs"):
            engineering.run_engineering_case(
                recorder, plan, attempt=2, transaction_root=changed_root,
                expected_contract_sha256=changed_contract,
                expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
            )
        assert not (changed_root / "starts").exists()
    assert not (recorder.output_root / "claims" /
                f"{plan.case_id}.attempt2.claim.json").exists()
    retry_root, retry_contract = _prepare(root, plan, attempt=2)
    result = engineering.run_engineering_case(
        recorder, plan, attempt=2, transaction_root=retry_root,
        expected_contract_sha256=retry_contract,
        expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
    )
    assert result.engineering_receipt.is_file()
    assert recorder.completion((plan,))["engineering_success"] == 1
    _assert_no_scientific_cell(recorder)


def test_active_claim_cannot_launch_fresh_synthetic_root(root: Path) -> None:
    plan = _plan()
    recorder = _recorder(root)
    transaction_root, contract_sha = _prepare(root, plan)
    binding_sha = _binding_pin(recorder, plan, transaction_root, contract_sha)
    recorder.claim(plan, worker="synthetic_case_engineering", attempt=1)
    with (
        patch.object(transaction, "run_synthetic_transaction_channel",
                     side_effect=AssertionError("active claim launched a child")),
        pytest.raises(ValueError, match="already claimed"),
    ):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
        )
    assert not (transaction_root / "starts").exists()
    assert not (transaction_root / "proposals").exists()
    assert not (recorder.output_root / "attempts").exists()
    _assert_no_scientific_cell(recorder)


def test_coordinated_binding_and_failure_rewrite_cannot_change_retry_input(root: Path) -> None:
    plan = _plan()
    recorder = _recorder(root)
    transaction_root, contract_sha = _prepare(root, plan)
    external_binding_sha = _binding_pin(recorder, plan, transaction_root, contract_sha)
    actual = transaction.run_synthetic_transaction_channel

    def failing_child(
        selected_root: Path, *, expected_contract_sha256: str, cwd: Path,
    ) -> transaction.SyntheticAttestation:
        return actual(
            selected_root, expected_contract_sha256=expected_contract_sha256, cwd=cwd,
            command=[sys.executable, "-c", "raise SystemExit(3)", "{result_handle}"],
        )

    with (
        patch.object(transaction, "run_synthetic_transaction_channel", failing_child),
        pytest.raises(SupervisionError, match="frame|result|did not complete normally"),
    ):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256=external_binding_sha, cwd=_PROJECT_ROOT,
        )

    altered_source = b"coordinated changed source\n"
    binding_path = (recorder.output_root / "engineering_bindings" /
                    f"{plan.case_id}.json")
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    altered_binding_payload = dict(binding["payload"])
    altered_binding_payload["source_sha256"] = hashlib.sha256(altered_source).hexdigest()
    altered_binding_payload["expected_value"] = 8
    altered_binding = envelope("engineering_smoke", altered_binding_payload)
    assert altered_binding["sha256"] != external_binding_sha
    binding_path.write_bytes((canonical_config_json(altered_binding) + "\n").encode("utf-8"))

    failure_path = recorder.output_root / "attempts" / f"{plan.case_id}.attempt1.failure.json"
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    altered_failure_payload = dict(failure["payload"])
    altered_failure_payload["reason"] = {
        **altered_failure_payload["reason"],
        "case_binding_sha256": altered_binding["sha256"],
    }
    altered_failure = envelope("engineering_smoke", altered_failure_payload)
    failure_path.write_bytes((canonical_config_json(altered_failure) + "\n").encode("utf-8"))

    retry_root, retry_contract = _prepare(
        root, plan, attempt=2, source_bytes=altered_source, expected_value=8,
    )
    with pytest.raises(ValueError, match="external pin"):
        engineering.run_engineering_case(
            recorder, plan, attempt=2, transaction_root=retry_root,
            expected_contract_sha256=retry_contract,
            expected_case_binding_sha256=external_binding_sha, cwd=_PROJECT_ROOT,
        )
    assert not (retry_root / "starts").exists()
    assert not (recorder.output_root / "claims" /
                f"{plan.case_id}.attempt2.claim.json").exists()
    _assert_no_scientific_cell(recorder)


def test_post_attestation_verification_drift_quarantines_attempt(root: Path) -> None:
    plan = _plan()
    recorder = _recorder(root)
    transaction_root, contract_sha = _prepare(root, plan)
    binding_sha = _binding_pin(recorder, plan, transaction_root, contract_sha)
    with (
        patch.object(transaction, "verify_synthetic_attestation_channel",
                     side_effect=ValueError("injected post-attestation drift")),
        pytest.raises(ValueError, match="post-attestation drift"),
    ):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
        )
    assert (transaction_root / "attestations" / f"{contract_sha}.json").is_file()
    assert (recorder.output_root / "claims" /
            f"{plan.case_id}.attempt1.claim.json").is_file()
    assert not (recorder.output_root / "attempts").exists()
    assert not (recorder.output_root / "engineering_intents").exists()
    with pytest.raises(ValueError, match="retry must be linked"):
        recorder.claim(plan, worker="synthetic_case_engineering", attempt=2)
    _assert_no_scientific_cell(recorder)


def test_preexisting_proposal_cannot_be_attested_as_child_output(root: Path) -> None:
    plan = _plan()
    recorder = _recorder(root)
    transaction_root, contract_sha = _prepare(root, plan)
    binding_sha = _binding_pin(recorder, plan, transaction_root, contract_sha)
    transaction.write_synthetic_proposal(transaction_root, contract_sha)
    with pytest.raises(ValueError, match="preexisting proposal"):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
        )
    assert (recorder.output_root / "attempts" /
            f"{plan.case_id}.attempt1.failure.json").is_file()
    assert not (recorder.output_root / "engineering_successes").exists()
    _assert_no_scientific_cell(recorder)


def test_interrupted_receipt_recovers_only_with_external_attestation_pin(root: Path) -> None:
    plan = _plan()
    recorder = _recorder(root)
    transaction_root, contract_sha = _prepare(root, plan)
    binding_sha = _binding_pin(recorder, plan, transaction_root, contract_sha)
    actual_run = transaction.run_synthetic_transaction_channel
    actual_write = recorder._write
    external_attestations: list[str] = []

    def capture_attestation(
        selected_root: Path, *, expected_contract_sha256: str, cwd: Path,
    ) -> transaction.SyntheticAttestation:
        result = actual_run(
            selected_root, expected_contract_sha256=expected_contract_sha256, cwd=cwd,
        )
        external_attestations.append(result.attestation_sha256)
        return result

    def interrupt_receipt(directory: Path, name: str, record: Mapping[str, Any]) -> Path:
        if directory.name == "engineering_successes":
            raise RuntimeError("synthetic receipt interruption")
        return actual_write(directory, name, record)

    with (
        patch.object(transaction, "run_synthetic_transaction_channel", capture_attestation),
        patch.object(recorder, "_write", interrupt_receipt),
        pytest.raises(RuntimeError, match="receipt interruption"),
    ):
        engineering.run_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_case_binding_sha256=binding_sha, cwd=_PROJECT_ROOT,
        )
    assert len(external_attestations) == 1
    assert not (recorder.output_root / "attempts").exists()
    assert (recorder.output_root / "engineering_intents" /
            f"{plan.case_id}.intent.json").is_file()
    with pytest.raises(ValueError, match="external pin"):
        engineering.recover_engineering_case(
            recorder, plan, attempt=1, transaction_root=transaction_root,
            expected_contract_sha256=contract_sha,
            expected_attestation_sha256="b" * 64,
            expected_case_binding_sha256=binding_sha,
        )
    receipt = engineering.recover_engineering_case(
        recorder, plan, attempt=1, transaction_root=transaction_root,
        expected_contract_sha256=contract_sha,
        expected_attestation_sha256=external_attestations[0],
        expected_case_binding_sha256=binding_sha,
    )
    assert receipt.is_file()
    _assert_no_scientific_cell(recorder)
