"""Synthetic input-pin and whole-child supervision tests; no model fitting."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any

import pytest

from core.config import canonical_config_json, config_digest
from core.provenance import SourceProvenance
from evaluation import phase2_cho_execution as execution
from evaluation.phase2_supervision_primitives import (
    GIB,
    DeadlineLease,
    ResourceSample,
    SupervisionError,
    SupervisionResult,
    run_supervised,
)


def _pins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    config = tmp_path / "configs/phase2"
    config.mkdir(parents=True)
    base = tmp_path / "configs/base.toml"
    base.write_text("version = 1\n", encoding="utf-8")
    protocol = config / "protocol.toml"
    protocol.write_text("version = 1\n", encoding="utf-8")
    ceiling = config / "selection_ceiling.toml"
    ceiling.write_text("maximum_gradient_steps = 5253\n", encoding="utf-8")
    sweep = config / "cho_sweep.toml"
    sweep.write_text("[analysis]\nmemory_limit_bytes = 5905580032\n", encoding="utf-8")
    candidates = tmp_path / "candidates.json"
    rows = [{"method": method, "candidate": "synthetic"} for method in execution.METHODS]
    candidates.write_text(json.dumps({"methods": rows}), encoding="utf-8")

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    record = {
        "schema": execution.PIN_SCHEMA,
        "source_sha256": "a" * 64,
        "environment_sha256": "b" * 64,
        "base_config_sha256": digest(base),
        "route": {
            "protocol_config_sha256": digest(protocol),
            "threshold_config_sha256": "c" * 64,
            "cohort_audit_sha256": "d" * 64,
            "variant_config_sha256": "e" * 64,
        },
        "candidate_config_path": "candidates.json",
        "candidate_config_sha256": digest(candidates),
        "method_config_sha256": {row["method"]: config_digest(row) for row in rows},
        "selection_ceiling_config_sha256": digest(ceiling),
        "sweep_config_sha256": digest(sweep),
    }
    path = tmp_path / "pins.json"
    path.write_text(canonical_config_json(record), encoding="utf-8")
    monkeypatch.setattr(
        execution,
        "capture_source",
        lambda root: SourceProvenance(
            "1" * 40,
            "a" * 64,
            False,
        ),
    )
    return path, digest(path)


def test_explicit_triplet_selects_exactly_one_case() -> None:
    assert execution.select_cases(
        method="eegnet", subject="subject_01", seed=11, case_limit=None
    ) == (execution.EngineeringCase("eegnet", "subject_01", 11),)


def test_broader_roster_requires_explicit_bound_and_has_canonical_order() -> None:
    with pytest.raises(ValueError, match="explicit --case-limit"):
        execution.select_cases(method="eegnet", subject=None, seed=None, case_limit=None)
    selected = execution.select_cases(method="eegnet", subject=None, seed=None, case_limit=6)
    assert [(case.subject, case.seed) for case in selected] == [
        ("subject_01", seed) for seed in execution.SEEDS
    ] + [("subject_02", 11)]


@pytest.mark.parametrize("limit", [0, -1, 1041, True])
def test_case_limit_cannot_be_implicit_or_invalid(limit: Any) -> None:
    with pytest.raises(ValueError):
        execution.select_cases(method=None, subject=None, seed=None, case_limit=limit)


@pytest.mark.parametrize(
    "overrides",
    [
        {"process_memory_limit_bytes": execution.INITIAL_PROBE_MAX_MEMORY_BYTES + 1},
        {"attempt_seconds": 601},
        {"session_seconds": 7201},
        {"attempt_seconds": float("nan")},
        {"torch_threads": 0},
        {"attempt_seconds": True},
        {"process_memory_limit_bytes": False},
    ],
)
def test_probe_limits_refuse_increases_and_nonfinite_values(overrides: dict[str, Any]) -> None:
    arguments = {
        "process_memory_limit_bytes": execution.INITIAL_PROBE_MAX_MEMORY_BYTES,
        "attempt_seconds": 600.0,
        "session_seconds": 7200.0,
        "torch_threads": 1,
    }
    with pytest.raises(ValueError):
        execution.ExecutionLimits(**{**arguments, **overrides})


def test_initial_launch_ram_floor_is_stronger_than_active_floor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(execution, "live_resources", lambda root: ResourceSample(21 * GIB, 9 * GIB))
    with pytest.raises(SupervisionError, match="10 GiB launch"):
        execution._resources(tmp_path, launching=True)
    assert execution._resources(tmp_path, launching=False).available_ram_bytes == 9 * GIB
    monkeypatch.setattr(execution, "live_resources", lambda root: ResourceSample(21 * GIB, 3 * GIB))
    with pytest.raises(SupervisionError):
        execution._resources(tmp_path, launching=False)


def test_external_pins_are_checked_without_tensor_import(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, digest = _pins(tmp_path, monkeypatch)
    pins = execution.load_execution_pins(tmp_path, path, digest)
    assert pins["source_sha256"] == "a" * 64
    with pytest.raises(ValueError, match="bytes differ"):
        execution.load_execution_pins(tmp_path, path, "f" * 64)


def test_candidate_self_hash_cannot_replace_an_independent_method_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, _ = _pins(tmp_path, monkeypatch)
    record = json.loads(path.read_bytes())
    record["method_config_sha256"]["eegnet"] = "f" * 64
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="independently supplied digests"):
        execution.load_execution_pins(tmp_path, path, hashlib.sha256(path.read_bytes()).hexdigest())


def test_source_drift_refuses_existing_pins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, digest = _pins(tmp_path, monkeypatch)
    monkeypatch.setattr(
        execution,
        "capture_source",
        lambda root: SourceProvenance(
            "1" * 40,
            "f" * 64,
            False,
        ),
    )
    with pytest.raises(ValueError, match="live source differs"):
        execution.load_execution_pins(tmp_path, path, digest)


def test_receipt_is_atomic_and_never_clobbered(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    execution.fresh_record(path, {"status": "stopped"})
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        execution.fresh_record(path, {"status": "stopped"})
    with pytest.raises(FileExistsError):
        execution.fresh_record(path, {"status": "complete"})
    assert path.read_bytes() == before


def test_pinned_read_refuses_hardlink(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text("{}", encoding="utf-8")
    alias = tmp_path / "alias.json"
    os.link(source, alias)
    with pytest.raises(ValueError, match="link count"):
        execution.stable_bytes(source)


def _contract(tmp_path: Path) -> dict[str, Any]:
    return {
        "deadline_path": "lease.json",
        "source_sha256": "a" * 64,
        "limits": {"process_memory_limit_bytes": 256 * 1024**2},
    }


def test_stopped_child_never_calls_parent_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        execution,
        "_resources",
        lambda root, launching: ResourceSample(
            21 * GIB,
            11 * GIB,
        ),
    )
    staged = tmp_path / "staged_cell.json"
    staged.write_text("synthetic staged output", encoding="utf-8")

    def accept() -> dict[str, Any]:
        raise AssertionError("a stopped child must never publish the staged cell")

    result = SupervisionResult(123, 1, "ram_floor", 32 * 1024**2, 32 * 1024**2)
    receipt = execution.supervise_attempt(
        root=tmp_path,
        attempt_dir=tmp_path,
        contract=_contract(tmp_path),
        contract_sha256="c" * 64,
        command=[sys.executable],
        accept=accept,
        supervisor=lambda *args, **kwargs: result,
    )
    assert receipt["engineering_cell_count"] == 0
    assert receipt["staged_outputs_quarantined"] is True
    assert receipt["supervision"] == asdict(result)
    assert staged.is_file()


def test_sensor_or_windows_error_receipt_marks_peak_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        execution,
        "_resources",
        lambda root, launching: ResourceSample(
            21 * GIB,
            11 * GIB,
        ),
    )

    def fail(*args: Any, **kwargs: Any) -> SupervisionResult:
        raise SupervisionError("synthetic sensor failure")

    receipt = execution.supervise_attempt(
        root=tmp_path,
        attempt_dir=tmp_path,
        contract=_contract(tmp_path),
        contract_sha256="c" * 64,
        command=[sys.executable],
        accept=lambda: {},
        supervisor=fail,
    )
    assert receipt["status"] == "stopped"
    assert receipt["peak_measurement_available"] is False
    assert receipt["supervision"] is None
    assert "synthetic sensor failure" in receipt["error"]


def test_successful_process_with_failed_attestation_never_counts_a_cell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        execution,
        "_resources",
        lambda root, launching: ResourceSample(
            21 * GIB,
            11 * GIB,
        ),
    )

    def refuse() -> dict[str, Any]:
        raise ValueError("independent source pin changed")

    receipt = execution.supervise_attempt(
        root=tmp_path,
        attempt_dir=tmp_path,
        contract=_contract(tmp_path),
        contract_sha256="c" * 64,
        command=[sys.executable],
        accept=refuse,
        supervisor=lambda *args, **kwargs: SupervisionResult(123, 0, "normal", 1024, 1024),
    )
    assert receipt["engineering_cell_count"] == 0
    assert receipt["status"] == "stopped"


def _ample(root: Path) -> ResourceSample:
    return ResourceSample(21 * GIB, 11 * GIB)


def test_stopped_attempt_links_real_recorder_failure_and_permits_only_one_retry(
    tmp_path: Path,
) -> None:
    from evaluation.phase2_runner import CasePlan, CaseRecorder

    recorder = CaseRecorder(tmp_path)
    plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
    receipt = {
        "status": "stopped",
        "reason": "ram_floor",
        "error": None,
        "recovery_or_quarantine_required": False,
    }
    with recorder.case_session(plan) as locked:
        locked.claim_new(worker="synthetic-probe", attempt=1)
        assert execution.record_stopped_attempt(
            locked,
            receipt,
            attempt=1,
            receipt_relative="runs/phase2/sweeps/synthetic/receipt.json",
        )
    assert recorder.completion((plan,))["failed"] == 1
    with recorder.case_session(plan) as locked:
        locked.claim_new(worker="synthetic-retry", attempt=2)
    with (
        recorder.case_session(plan) as locked,
        pytest.raises(ValueError, match="already claimed"),
    ):
        locked.claim_new(worker="synthetic-duplicate", attempt=2)


def test_durable_attestation_does_not_become_a_retryable_failure(tmp_path: Path) -> None:
    from evaluation.phase2_runner import CasePlan, CaseRecorder

    recorder = CaseRecorder(tmp_path)
    plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
    receipt = {
        "status": "stopped",
        "reason": "publication_error",
        "error": "synthetic failure",
        "recovery_or_quarantine_required": True,
    }
    with recorder.case_session(plan) as locked:
        locked.claim_new(worker="synthetic-attested", attempt=1)
        assert (
            execution.record_stopped_attempt(
                locked,
                receipt,
                attempt=1,
                receipt_relative="runs/phase2/sweeps/synthetic/receipt.json",
            )
            is False
        )
    completion = recorder.completion((plan,))
    assert completion["failed"] == 0 and completion["claimed_unmeasured"] == 1
    with (
        recorder.case_session(plan) as locked,
        pytest.raises(ValueError, match="linked to a recorded failure"),
    ):
        locked.claim_new(worker="unsafe-retry", attempt=2)


def test_parent_claim_rehash_cannot_hide_git_provenance_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from evaluation import phase2_runner
    from evaluation.phase2_records import envelope

    source = SourceProvenance("1" * 40, "a" * 64, False)
    monkeypatch.setattr(phase2_runner, "capture_source", lambda root: source)
    monkeypatch.setattr(phase2_runner, "environment_digest", lambda: "b" * 64)
    recorder = phase2_runner.CaseRecorder(tmp_path)
    plan = phase2_runner.CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
    identity = SimpleNamespace(
        git_commit=source.git_commit,
        git_dirty=source.git_dirty,
        source_sha256=source.source_sha256,
        environment_sha256="b" * 64,
    )
    with recorder.case_session(plan) as locked:
        claim = locked.claim_new(worker="synthetic-parent", attempt=1)
        execution.verify_parent_claim(
            recorder, plan, identity, attempt=1, expected_source=asdict(source)
        )
        record = json.loads(claim.read_bytes())
        record["payload"]["source"]["git_commit"] = "2" * 40
        forged = envelope("engineering_smoke", record["payload"])
        claim.write_bytes((canonical_config_json(forged) + "\n").encode("utf-8"))
        with pytest.raises(ValueError, match="parent final claim provenance"):
            execution.verify_parent_claim(
                recorder, plan, identity, attempt=1, expected_source=asdict(source)
            )


def _lease(tmp_path: Path, attempt_seconds: float) -> None:
    now = datetime.now(UTC)
    DeadlineLease.open_or_create(
        tmp_path / "lease.json",
        attempt_deadline_utc=now + timedelta(seconds=attempt_seconds),
        session_deadline_utc=now + timedelta(seconds=20),
    )


def _execution_harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Keep actual parent closure/recorder; replace tensor verification and owned child only."""
    from evaluation import phase2_cho_sweep, phase2_runner
    from evaluation.phase2_records import CellIdentity

    pins_path, pins_sha = _pins(tmp_path, monkeypatch)
    admission_path = tmp_path / "admission.json"
    admission_path.write_text(json.dumps({
        "schema": "cho_first_tranche_sweep_admission_v1", "operator": "synthetic-owner",
        "admitted": True, "timestamp_utc": datetime.now(UTC).isoformat(),
        "probe_cap_minutes": 10, "session_cap_minutes": 120,
    }), encoding="utf-8")
    source = SourceProvenance("1" * 40, "a" * 64, False)
    monkeypatch.setattr(phase2_runner, "capture_source", lambda root: source)
    monkeypatch.setattr(phase2_runner, "environment_digest", lambda: "b" * 64)
    monkeypatch.setattr(execution, "_runtime", lambda threads, expected: None)
    monkeypatch.setattr(execution, "_resources", lambda root, launching: _ample(root))
    monkeypatch.setattr(phase2_cho_sweep, "sweep_admission_snapshot", lambda root, admission: {
        "admission": {"admitted": True},
    })
    identity = CellIdentity(
        "cho2017", "subject_01", "eegnet", 5, 11, None, None,
        "c" * 64, "d" * 64, "e" * 64, "f" * 64, "c" * 64, "d" * 64,
        source.source_sha256, "b" * 64, source.git_commit, False,
    )
    metrics = {"role": "outer_target", "selection_evidence_sha256": "e" * 64,
               "confusion_matrix": [[1, 0], [0, 1]], "balanced_accuracy": [1, 1],
               "query_count": 2}
    witness = execution.VerifiedStagedProposal(identity, metrics, "c" * 64, "d" * 64)
    hooks: dict[str, Any] = {}

    def verify(root: Path, contract: Any, digest: str) -> execution.VerifiedStagedProposal:
        if "during_verify" in hooks:
            hooks["during_verify"](root, contract)
        return witness

    monkeypatch.setattr(execution, "verify_staged_proposal", verify)
    original_supervise = execution.supervise_attempt

    def fake_child(*args: Any, **kwargs: Any) -> SupervisionResult:
        if "after_child" in hooks:
            hooks["after_child"]()
        return SupervisionResult(123, 0, "normal", 32 * 1024**2, 32 * 1024**2)

    def supervise(**kwargs: Any) -> dict[str, Any]:
        return original_supervise(**kwargs, supervisor=fake_child)

    monkeypatch.setattr(execution, "supervise_attempt", supervise)
    return {
        "arguments": {
            "root": tmp_path, "pins_path": pins_path, "pins_sha256": pins_sha,
            "admission_path": admission_path,
            "receipt_path": tmp_path / "runs/phase2/sweeps/synthetic/receipt.json",
            "cases": (execution.EngineeringCase("eegnet", "subject_01", 11),),
            "limits": execution.ExecutionLimits(6 * GIB, 2.0, 10.0, 1),
            "worker": "synthetic-execution", "attempt": 1,
        },
        "recorder": phase2_runner.CaseRecorder(tmp_path),
        "plan": phase2_runner.CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1),
        "hooks": hooks, "source": source,
    }


def test_production_parent_closure_promotes_after_real_claim_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _execution_harness(tmp_path, monkeypatch)
    receipt = execution.execute_engineering_cases(**harness["arguments"])
    assert receipt["engineering_cell_count"] == 1
    assert harness["recorder"].completion((harness["plan"],))["measured"] == 1
    attestation_path = next(tmp_path.rglob("accepted.json"))
    attestation = json.loads(attestation_path.read_bytes())
    assert attestation["proposal_file_sha256"] == "c" * 64
    assert attestation["staged_cell_file_sha256"] == "d" * 64


def test_parent_verification_deadline_blocks_canonical_promotion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _execution_harness(tmp_path, monkeypatch)
    clock = {"value": 1000.0}
    monkeypatch.setattr(execution.time, "monotonic", lambda: clock["value"])
    harness["hooks"]["during_verify"] = lambda root, contract: clock.update(value=1003.0)
    receipt = execution.execute_engineering_cases(**harness["arguments"])
    assert receipt["engineering_cell_count"] == 0
    assert not list(tmp_path.rglob("accepted.json"))
    assert harness["recorder"].completion((harness["plan"],))["failed"] == 1


@pytest.mark.parametrize("drift", ["git", "admission"])
def test_postchild_source_or_admission_drift_blocks_canonical_promotion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, drift: str,
) -> None:
    harness = _execution_harness(tmp_path, monkeypatch)

    def mutate() -> None:
        if drift == "git":
            monkeypatch.setattr(execution, "capture_source", lambda root: SourceProvenance(
                "2" * 40, "a" * 64, False,
            ))
        else:
            harness["arguments"]["admission_path"].write_text("{}", encoding="utf-8")

    harness["hooks"]["after_child"] = mutate
    receipt = execution.execute_engineering_cases(**harness["arguments"])
    assert receipt["engineering_cell_count"] == 0
    assert not list(tmp_path.rglob("accepted.json"))
    assert harness["recorder"].completion((harness["plan"],))["failed"] == 1


def test_parent_attestation_uses_retained_witness_after_proposal_path_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _execution_harness(tmp_path, monkeypatch)

    def change_path(root: Path, contract: Any) -> None:
        path = root / contract["proposal_path"]
        path.write_text("this is a later changed pathname buffer", encoding="utf-8")

    harness["hooks"]["during_verify"] = change_path
    receipt = execution.execute_engineering_cases(**harness["arguments"])
    assert receipt["engineering_cell_count"] == 1
    attestation = json.loads(next(tmp_path.rglob("accepted.json")).read_bytes())
    assert attestation["proposal_file_sha256"] == "c" * 64
    changed = next(tmp_path.rglob("proposal.json"))
    assert hashlib.sha256(changed.read_bytes()).hexdigest() != attestation["proposal_file_sha256"]


def test_durable_parent_attestation_then_publication_error_requires_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evaluation.phase2_runner import LockedCase

    harness = _execution_harness(tmp_path, monkeypatch)

    def fail(self: Any, *args: Any, **kwargs: Any) -> Path:
        raise OSError("synthetic canonical publication failure")

    monkeypatch.setattr(LockedCase, "record_cell", fail)
    receipt = execution.execute_engineering_cases(**harness["arguments"])
    assert receipt["engineering_cell_count"] == 0
    assert list(tmp_path.rglob("accepted.json"))
    completion = harness["recorder"].completion((harness["plan"],))
    assert completion["failed"] == 0 and completion["claimed_unmeasured"] == 1
    attempt_receipt = json.loads(next(tmp_path.rglob("case_0001/receipt.json")).read_bytes())
    assert attempt_receipt["recovery_or_quarantine_required"] is True


def test_attempt_setup_error_persists_session_without_claiming_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _execution_harness(tmp_path, monkeypatch)

    def fail(**kwargs: Any) -> Any:
        raise OSError("synthetic setup failure")

    monkeypatch.setattr(execution, "prepare_attempt", fail)
    receipt = execution.execute_engineering_cases(**harness["arguments"])
    assert receipt["attempted_cases"] == 0 and receipt["not_attempted_cases"] == 1
    assert "synthetic setup failure" in receipt["stop_reason"]
    assert harness["arguments"]["receipt_path"].is_file()
    assert harness["recorder"].completion((harness["plan"],))["pending"] == 1


def test_exception_escaping_supervisor_links_failure_before_explicit_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _execution_harness(tmp_path, monkeypatch)

    def fail(**kwargs: Any) -> dict[str, Any]:
        raise OSError("synthetic terminal receipt write failed")

    monkeypatch.setattr(execution, "supervise_attempt", fail)
    receipt = execution.execute_engineering_cases(**harness["arguments"])
    assert receipt["engineering_cell_count"] == 0
    assert harness["recorder"].completion((harness["plan"],))["failed"] == 1
    with harness["recorder"].case_session(harness["plan"]) as locked:
        locked.claim_new(worker="synthetic-explicit-retry", attempt=2)


def test_admission_revoke_during_final_resource_read_prevents_promotion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _execution_harness(tmp_path, monkeypatch)

    def resources(root: Path, launching: bool) -> ResourceSample:
        if not launching and list(root.rglob("accepted.json")):
            harness["arguments"]["admission_path"].write_text("{}", encoding="utf-8")
        return _ample(root)

    monkeypatch.setattr(execution, "_resources", resources)
    receipt = execution.execute_engineering_cases(**harness["arguments"])
    assert receipt["engineering_cell_count"] == 0
    assert list(tmp_path.rglob("accepted.json"))
    completion = harness["recorder"].completion((harness["plan"],))
    assert completion["measured"] == 0 and completion["claimed_unmeasured"] == 1


def test_expired_session_never_creates_another_attempt_or_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _execution_harness(tmp_path, monkeypatch)
    clock = {"value": 1000.0}
    monkeypatch.setattr(execution.time, "monotonic", lambda: clock["value"])
    original_fresh = execution.fresh_record

    def publish(path: Path, payload: Any) -> None:
        original_fresh(path, payload)
        if path.name == "session.json":
            clock["value"] = 1020.0

    monkeypatch.setattr(execution, "fresh_record", publish)
    receipt = execution.execute_engineering_cases(**harness["arguments"])
    assert receipt["not_attempted_cases"] == 1 and receipt["attempted_cases"] == 0
    assert receipt["stop_reason"] == "session_deadline_before_next_case"
    assert not list(tmp_path.rglob("case_0001"))
    assert harness["recorder"].completion((harness["plan"],))["pending"] == 1


@pytest.mark.parametrize("age_hours", [24.001, -0.001])
def test_fresh_admission_cannot_expire_or_be_future_dated(age_hours: float) -> None:
    raw = json.dumps({
        "schema": "cho_first_tranche_sweep_admission_v1", "operator": "synthetic-owner",
        "admitted": True,
        "timestamp_utc": (datetime.now(UTC) - timedelta(hours=age_hours)).isoformat(),
        "probe_cap_minutes": 10, "session_cap_minutes": 120,
    }).encode()
    with pytest.raises(ValueError, match="expired or is future-dated"):
        execution.verify_fresh_admission(
            raw, limits={"attempt_seconds": 600, "session_seconds": 7200}
        )


def _target_attestation_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str,
) -> dict[str, Any]:
    from core.config import load_toml
    from evaluation import phase2_cho_persisted_target, phase2_runner
    from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute
    from evaluation.phase2_cho_persisted_target import ChoPersistedTargetDeclarations
    from evaluation.phase2_profile_binding import (
        CHO_CHANNELS,
        ChoProfileAssets60Hz,
        ChoProfileBinding60Hz,
    )
    from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
    from evaluation.phase2_records import CellIdentity, envelope
    from scripts.audit_phase2_protocol import validate_protocol

    config = load_toml(Path(__file__).resolve().parents[1] / "configs/phase2/protocol.toml")
    catalogs = tuple(TrialCatalog(
        "cho2017", f"subject_{number:02d}",
        tuple(f"subject_{number:02d}/trial_{index:02d}" for index in range(42)),
        ("left_hand", "right_hand") * 21, ("left_hand", "right_hand"), "a" * 64, "b" * 64,
    ) for number in range(1, 53))
    catalog = catalogs[0]
    plan = phase2_runner.CasePlan("cho2017", "subject_01", method, 5, 11, 1)
    protocol_sha = config_digest(config)
    episode = nested_episode(catalog, shots=validate_protocol(config), protocol_sha256=protocol_sha)
    episode_record = envelope("episode_manifest", episode.payload())
    selection = source_selection(catalogs, target="subject_01")
    selection_record = envelope("source_selection", asdict(selection))
    source = SourceProvenance("1" * 40, "a" * 64, False)
    monkeypatch.setattr(phase2_runner, "capture_source", lambda root: source)
    monkeypatch.setattr(phase2_runner, "environment_digest", lambda: "b" * 64)
    identity = CellIdentity(
        "cho2017", "subject_01", method, 5, 11, None, None,
        protocol_sha, episode_record["sha256"], selection_record["sha256"], "c" * 64,
        catalog.preprocessing_sha256, "d" * 64, source.source_sha256, "b" * 64,
        source.git_commit, False,
    )
    partition = episode.partition(5)
    support = tuple(catalog.trial_ids[index] for index in partition.support_indices)
    query = tuple(catalog.trial_ids[index] for index in partition.query_indices)
    asset = ChoProfileAssets60Hz("e" * 64, "f" * 64, "a" * 64)
    route = ChoFirstTrancheRoute(
        (plan,), catalogs, {catalog.subject: asset for catalog in catalogs},
        canonical_config_json(config), {}, {},
    )
    declarations = ChoPersistedTargetDeclarations(
        "b" * 64, "c" * 64, {catalog.subject: (
            f"data/raw/moabb/cho2017/{catalog.subject}.gdf", "d" * 64,
        ) for catalog in catalogs},
    )
    monkeypatch.setattr(phase2_cho_persisted_target, "verify_cho_persisted_target_declarations",
                        lambda root, route, base_config_sha256: declarations)
    common = {"schema": "cho2017-target-input-v1", "method": method,
              "subject": "subject_01", "episode_record_sha256": identity.episode_sha256}
    if method == "eegnet":
        attestation = {**common, "profile": "cho_profile_a", "anchor": {
            "method": "eegnet", "subject": "subject_01", "role": "outer_target",
            "episode_sha256": episode.sha256, "selection_sha256": selection.sha256,
            "support_trial_ids": support, "query_trial_ids": query,
            "source_subjects": selection.source_subjects, "input_identities": {"subject_01": {
                "catalog_sha256": catalog.sha256, "artifact_sha256": catalog.artifact_sha256,
                "manifest_sha256": catalog.artifact_sha256, "base_config_sha256": "b" * 64,
            }},
        }}
    else:
        binding = ChoProfileBinding60Hz(
            "cho2017", "subject_01", 5, catalog.classes, CHO_CHANNELS, protocol_sha,
            episode.sha256, catalog.artifact_sha256, asset.profile_b_artifact_sha256,
            asset.profile_b_manifest_sha256, catalog.preprocessing_sha256, "c" * 64,
            "b" * 64, support, query, tuple(range(len(support))),
            tuple(range(len(support), len(support) + len(query))), 42, 0,
            variant_config_sha256=asset.variant_config_sha256,
            source_file="data/raw/moabb/cho2017/subject_01.gdf", source_sha256="d" * 64,
        )
        attestation = {**common, "profile": "cho_profile_b_60hz_v1",
                       "binding_sha256": config_digest(asdict(binding)), "binding": asdict(binding)}
    metrics = {"role": "outer_target", "selection_evidence_sha256": "e" * 64,
               "confusion_matrix": [[1, 0], [0, 1]], "balanced_accuracy": [1, 1],
               "query_count": 2, "target_input_attestation": attestation}
    recorder = phase2_runner.CaseRecorder(tmp_path)
    recorder.claim(plan, worker="synthetic-target")
    cell = recorder.record_cell(identity, metrics=metrics, plan=plan)
    return {"root": tmp_path, "route": route, "recorder": recorder,
            "record": json.loads(cell.read_bytes()), "plan": plan, "identity": identity,
            "base_config_sha256": "b" * 64}


@pytest.mark.parametrize("method", ["eegnet", "labram_linear"])
def test_single_staged_target_check_accepts_full_route_matched_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str,
) -> None:
    execution.verify_case_target_inputs(**_target_attestation_case(tmp_path, monkeypatch, method))


@pytest.mark.parametrize("method, damage", [
    ("eegnet", "query_ids"), ("eegnet", "input_identity"), ("eegnet", "query_rows"),
    ("labram_linear", "raw_source"), ("labram_linear", "binding_config"),
])
def test_resealed_target_attestation_cannot_replace_parent_route_pins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, method: str, damage: str,
) -> None:
    from evaluation.phase2_records import envelope

    arguments = _target_attestation_case(tmp_path, monkeypatch, method)
    record = arguments["record"]
    metrics = record["payload"]["metrics"]
    attestation = metrics["target_input_attestation"]
    if damage == "query_ids":
        attestation["anchor"]["query_trial_ids"][0] = "invented/query/trial"
    elif damage == "input_identity":
        attestation["anchor"]["input_identities"]["subject_01"]["catalog_sha256"] = "f" * 64
    elif damage == "query_rows":
        metrics["confusion_matrix"] = [[2, 0], [0, 0]]
    elif damage == "raw_source":
        attestation["binding"]["source_sha256"] = "f" * 64
        attestation["binding_sha256"] = config_digest(attestation["binding"])
    else:
        attestation["binding"]["profile_b_config_sha256"] = "f" * 64
        attestation["binding_sha256"] = config_digest(attestation["binding"])
    arguments["record"] = envelope("evaluation_cell", record["payload"])
    with pytest.raises(ValueError):
        execution.verify_case_target_inputs(**arguments)


@pytest.mark.skipif(sys.platform != "win32", reason="requires real Windows Job Objects")
def test_synthetic_child_deadline_quarantines_already_written_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(execution, "_resources", lambda root, launching: _ample(root))
    staged = tmp_path / "staged_cell.json"
    promoted = tmp_path / "canonical_cell.json"
    _lease(tmp_path, 1.5)
    command = [
        sys.executable,
        "-B",
        "-c",
        (
            "from pathlib import Path; import sys,time; "
            "Path(sys.argv[1]).write_text('synthetic'); time.sleep(60)"
        ),
        str(staged),
    ]

    def accept() -> dict[str, Any]:
        promoted.write_bytes(staged.read_bytes())
        return {"cell": str(promoted)}

    receipt = execution.supervise_attempt(
        root=tmp_path,
        attempt_dir=tmp_path,
        contract=_contract(tmp_path),
        contract_sha256="c" * 64,
        command=command,
        accept=accept,
        supervisor=partial(run_supervised, sensor=_ample, poll_seconds=0.02),
    )
    assert receipt["reason"] == "attempt_deadline"
    assert receipt["engineering_cell_count"] == 0
    assert staged.is_file() and not promoted.exists()
    assert receipt["peak_measurement_available"] is True


@pytest.mark.skipif(sys.platform != "win32", reason="requires real Windows Job Objects")
def test_synthetic_child_measures_peak_and_only_then_accepts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(execution, "_resources", lambda root, launching: _ample(root))
    marker = tmp_path / "child_finished.txt"
    promoted = tmp_path / "parent_accepted.txt"
    _lease(tmp_path, 8)
    command = [
        sys.executable,
        "-B",
        "-c",
        (
            "from pathlib import Path; import sys,time; "
            "allocation=bytearray(32*1024**2); time.sleep(0.15); "
            "Path(sys.argv[1]).write_text('ok')"
        ),
        str(marker),
    ]

    def accept() -> dict[str, Any]:
        assert marker.read_text("utf-8") == "ok"
        promoted.write_text("parent accepted after Job completion", encoding="utf-8")
        return {"cell": str(promoted)}

    receipt = execution.supervise_attempt(
        root=tmp_path,
        attempt_dir=tmp_path,
        contract=_contract(tmp_path),
        contract_sha256="c" * 64,
        command=command,
        accept=accept,
        supervisor=partial(run_supervised, sensor=_ample, poll_seconds=0.02),
    )
    assert receipt["status"] == "complete" and promoted.is_file()
    assert receipt["supervision"]["peak_process_memory_bytes"] >= 32 * 1024**2
    assert receipt["scientific_claims_made"] == 0
