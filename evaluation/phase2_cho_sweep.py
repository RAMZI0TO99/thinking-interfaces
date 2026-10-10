"""Cho first-tranche sweep orchestration: admission, per-case execution, receipts.

Engineering orchestration only. This module never weakens a guard and never
admits compute by itself: a sweep requires the operator's persisted
admission record plus the live machine admission, every case flows through
the existing source selectors, publication gate, admission-gated target
executor and recorder. Full tensor and target-attestation analysis remains
separate. A completed sweep under the engineering selector ceilings is
engineering evidence, not a ratified scientific result.
"""

from __future__ import annotations

import errno
import hashlib
import json
import math
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from core.provenance import SourceProvenance, capture_source
from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute
from evaluation.phase2_pilot import (
    PROBE_CAP_MINUTES,
    SESSION_CAP_MINUTES,
    TargetCaseExecutor,
    compute_admission,
)
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import CellIdentity, verify_envelope
from evaluation.phase2_runner import (
    CaseRecorder,
    environment_digest,
    method_configuration,
)

SWEEP_ADMISSION_SCHEMA = "cho_first_tranche_sweep_admission_v1"
SWEEP_RECEIPT_SCHEMA = "cho_first_tranche_sweep_receipt_v1"
MAXIMUM_ADMISSION_AGE_HOURS = 24.0

CaseRunner = Callable[..., Mapping[str, Any]]


class SweepStopped(RuntimeError):
    """A shared guard requires ending the session before another selection."""

    def __init__(self, reason: str, *, kind: str = "resource") -> None:
        super().__init__(reason)
        self.kind = kind


class SweepResumeConflict(SweepStopped):
    """An immutable historical cell cannot satisfy this sweep's input pins."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason, kind="resume_conflict")


def sweep_pin_snapshot(
    root: Path, method_configs: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Capture the source, environment and declared methods before any case."""
    source = capture_source(root)
    if type(source.git_dirty) is not bool or source.git_commit == "unversioned-workspace":
        raise ValueError("live Git commit and explicit dirty state are required for sweep pins")
    return {
        **asdict(source),
        "environment_sha256": environment_digest(),
        "method_config_sha256": {
            method: method_configuration(config)
            for method, config in method_configs.items()
        },
    }


def verify_sweep_resume_cell(
    record: Mapping[str, Any], *, plan: Any, route: ChoFirstTrancheRoute,
    method_config: Mapping[str, Any], pins: Mapping[str, Any],
) -> CellIdentity:
    """Bind a saved cell to this route; its five-field key alone is insufficient.

    This verifies execution identity, not historical fitting or scientific
    admission. The fitted checkpoint cannot be reconstructed before selection;
    its digest and the selector-evidence digest must still be well formed.
    """
    try:
        payload = record["payload"]
        if not verify_envelope(record, kind="evaluation_cell", expected_payload=payload):
            raise ValueError("evaluation-cell envelope differs")
        identity = CellIdentity(**payload["identity"])
        inputs = route.inputs_for(plan)
        targets = [catalog for catalog in inputs.catalogs if catalog.subject == plan.target_subject]
        if len(targets) != 1:
            raise ValueError("route requires exactly one target catalog")
        expected = {
            "dataset": plan.dataset, "target_subject": plan.target_subject,
            "method": plan.method, "shots_per_class": plan.shots_per_class,
            "model_seed": plan.model_seed, "support_draw_seed": None, "montage_seed": None,
            "protocol_sha256": config_digest_of(inputs.protocol_config),
            "episode_sha256": inputs.episode_record["sha256"],
            "selection_sha256": inputs.selection_record["sha256"],
            "preprocessing_sha256": targets[0].preprocessing_sha256,
            "method_config_sha256": method_configuration(method_config),
            "source_sha256": pins["source_sha256"],
            "environment_sha256": pins["environment_sha256"],
            "git_commit": pins["git_commit"], "git_dirty": pins["git_dirty"],
        }
        changed = [name for name, value in expected.items() if getattr(identity, name) != value]
        if changed:
            raise ValueError(f"saved cell differs from current pins: {', '.join(changed)}")
        require_digest(payload["metrics"]["selection_evidence_sha256"], "selector evidence")
        return identity
    except (KeyError, TypeError, ValueError) as error:
        raise SweepResumeConflict(f"{plan.case_id}: {error}") from error


def _measured_cell_records(recorder: CaseRecorder) -> dict[tuple[Any, ...], dict[str, Any]]:
    """Read the recorder's verified index once, retaining each complete envelope."""
    from evaluation.phase2_cell_aggregation_bridge import MAX_CELL_BYTES, _canonical_record

    records: dict[tuple[Any, ...], dict[str, Any]] = {}
    for path in sorted((recorder.output_root / "cells").glob("*.json")):
        record, _ = _canonical_record(path, maximum_bytes=MAX_CELL_BYTES)
        payload = record["payload"]
        if not verify_envelope(record, kind="evaluation_cell", expected_payload=payload):
            raise SweepResumeConflict("saved evaluation-cell envelope differs")
        recorder._validated_metrics(payload["metrics"])
        identity = CellIdentity(**record["payload"]["identity"])
        key = (identity.dataset, identity.target_subject, identity.method,
               identity.shots_per_class, identity.model_seed)
        if key in records or path.name != f"{identity.sha256}.json":
            raise SweepResumeConflict("duplicate saved cell or identity filename differs")
        records[key] = record
    return records


def _verify_resume_publication(
    root: Path, record: Mapping[str, Any], *, plan: Any,
    route: ChoFirstTrancheRoute, method_config: Mapping[str, Any],
    identity: CellIdentity, pins: Mapping[str, Any],
) -> None:
    """Reverify saved selection and publication without restoring model tensors."""
    from core.config import config_snapshot
    from evaluation.phase2_cho_execution_gate import _persisted_record
    from evaluation.phase2_cho_method_template import derive_cho_method_template
    from evaluation.phase2_cho_selected_manifest_bridge import (
        verify_cho_selected_manifest_files,
    )
    from evaluation.phase2_cho_selection_file_bridge import _evidence_path
    from evaluation.phase2_cho_source_restore import prepare_cho_source_restore
    from evaluation.phase2_selection_evidence_binding import verify_cho_selection_evidence

    try:
        metrics = record["payload"]["metrics"]
        inputs = route.inputs_for(plan)
        evidence_sha256 = metrics["selection_evidence_sha256"]
        evidence = _persisted_record(
            root, _evidence_path(root, metrics["selection_evidence_path"]), evidence_sha256,
        )
        payload = evidence["payload"]
        contract = payload["contract"]
        candidates = [candidate for candidate in contract["candidates"]
                      if candidate["name"] == payload["selected_candidate"]]
        if len(candidates) != 1 or config_snapshot(method_config) != config_snapshot(
            derive_cho_method_template(plan, contract, inputs.assets)
        ):
            raise ValueError("saved selection candidate or method configuration differs")
        verify_cho_selection_evidence(
            record=evidence, evidence_sha256=evidence_sha256, plan=plan,
            protocol_config=inputs.protocol_config, catalogs=inputs.catalogs,
            selection_record=inputs.selection_record, assets=inputs.assets, root=root,
            adapter_model_state_sha256=identity.checkpoint_sha256,
            adapter_source_settings=candidates[0]["source"],
            adapter_support_settings=candidates[0]["support"],
        )
        manifest_path = _evidence_path(root, metrics["selected_source_manifest_path"])
        prepared = prepare_cho_source_restore(
            root=root, plan=plan, method_config=method_config,
            expected_method_config_sha256=identity.method_config_sha256,
            selected_candidate=payload["selected_candidate"],
        )
        verify_cho_selected_manifest_files(
            root, manifest_path,
            manifest_sha256=metrics["selected_source_manifest_sha256"],
            evidence_sha256=evidence_sha256,
            selection_contract_sha256=payload["contract_sha256"],
            selected_candidate=payload["selected_candidate"],
            protocol_config_sha256=identity.protocol_sha256,
            expected_source=SourceProvenance(
                pins["git_commit"], pins["source_sha256"], pins["git_dirty"],
            ),
            model_recipe_sha256=config_digest_of(prepared.model_recipe),
            model_state_sha256=identity.checkpoint_sha256,
        )
        attestation = metrics["target_input_attestation"]
        expected = {
            "schema": "cho2017-target-input-v1", "method": plan.method,
            "subject": plan.target_subject, "episode_record_sha256": identity.episode_sha256,
            "profile": inputs.profile,
        }
        if not isinstance(attestation, Mapping) or any(
            attestation.get(name) != value for name, value in expected.items()
        ):
            raise ValueError("saved target attestation is missing or differs from the episode")
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise SweepResumeConflict(f"{plan.case_id}: saved publication differs: {error}") from error


def _verify_resume_success(
    recorder: CaseRecorder, record: Mapping[str, Any], *, plan: Any,
    identity: CellIdentity,
) -> None:
    """Bind bounded final claim provenance and success to the resumed cell."""
    from evaluation.phase2_cell_aggregation_bridge import (
        MAX_RECEIPT_BYTES,
        PinnedCaseCell,
        _canonical_record,
        _verified_claim,
        _verified_prior_failure,
    )
    from evaluation.phase2_subject_aggregation import ExpectedCell

    try:
        success, raw = _canonical_record(
            recorder.output_root / "successes" / f"{plan.case_id}.success.json",
            maximum_bytes=MAX_RECEIPT_BYTES,
        )
        attempt = success["payload"]["attempt"]
        if not verify_envelope(success, kind="engineering_smoke", expected_payload={
            "purpose": "pilot_case_success", "case": asdict(plan), "attempt": attempt,
            "cell_sha256": record["sha256"],
        }):
            raise ValueError("success receipt differs from resumed cell")
        pin = PinnedCaseCell(
            plan, ExpectedCell(*plan.identity_key), identity, attempt,
            record["sha256"], hashlib.sha256(raw).hexdigest(),
            record["payload"]["metrics"]["selection_evidence_sha256"],
        )
        _verified_claim(recorder.output_root, pin, attempt)
        if attempt == 2:
            _verified_claim(recorder.output_root, pin, 1)
            _verified_prior_failure(recorder.output_root, pin)
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise SweepResumeConflict(
            f"{plan.case_id}: saved successful attempt differs: {error}"
        ) from error


def _shared_refusal(error: Exception) -> bool:
    # TargetCaseExecutor predates the typed sweep stop. Its shared refusals
    # remain ValueErrors; isolated model/case errors must still advance normally.
    return isinstance(error, (SweepStopped, MemoryError)) or (
        isinstance(error, OSError) and error.errno == errno.ENOSPC
    ) or (
        isinstance(error, RuntimeError) and any(marker in str(error).lower() for marker in (
            "out of memory", "source execution resource admission refused",
        ))
    ) or (
        isinstance(error, ValueError) and any(marker in str(error).lower() for marker in (
            "session cap", "compute admission", "live machine guards",
            "source or environment changed", "live source or environment",
            "source, environment or model changed", "runtime identity changed",
            "source/config identity changed", "execution runtime differs from the pinned contract",
        ))
    )


@dataclass(frozen=True, slots=True)
class SweepAdmission:
    """The operator's persisted compute admission for one sweep."""

    operator: str
    admitted: bool
    timestamp_utc: str
    probe_cap_minutes: float
    session_cap_minutes: float
    file_sha256: str = ""

    @classmethod
    def load(cls, path: Path) -> SweepAdmission:
        # The pin covers the exact bytes parsed, rather than a second pathname
        # read that may observe a different record.
        raw = path.read_bytes()
        payload = json.loads(raw)
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != SWEEP_ADMISSION_SCHEMA
            or not isinstance(payload.get("operator"), str)
            or not payload.get("operator")
            or not isinstance(payload.get("admitted"), bool)
            or not isinstance(payload.get("timestamp_utc"), str)
            or not isinstance(payload.get("probe_cap_minutes"), (int, float))
            or not isinstance(payload.get("session_cap_minutes"), (int, float))
            or isinstance(payload["probe_cap_minutes"], bool)
            or isinstance(payload["session_cap_minutes"], bool)
            or not math.isfinite(payload["probe_cap_minutes"])
            or not math.isfinite(payload["session_cap_minutes"])
            or payload["probe_cap_minutes"] <= 0
            or payload["session_cap_minutes"] <= 0
            or payload["probe_cap_minutes"] > PROBE_CAP_MINUTES
            or payload["session_cap_minutes"] > SESSION_CAP_MINUTES
        ):
            raise ValueError("sweep admission record differs from the pinned schema")
        try:
            stamped = datetime.fromisoformat(payload["timestamp_utc"])
        except ValueError as error:
            raise ValueError("sweep admission timestamp is not ISO-8601") from error
        if stamped.tzinfo is None:
            raise ValueError("sweep admission timestamp requires a timezone")
        age = datetime.now(UTC) - stamped
        if age < timedelta(0) or age > timedelta(hours=MAXIMUM_ADMISSION_AGE_HOURS):
            raise ValueError("sweep admission record is future-dated or expired")
        return cls(
            payload["operator"], payload["admitted"], payload["timestamp_utc"],
            float(payload["probe_cap_minutes"]), float(payload["session_cap_minutes"]),
            hashlib.sha256(raw).hexdigest(),
        )


def sweep_admission_snapshot(
    root: Path, admission: SweepAdmission,
) -> dict[str, Any]:
    """Combine the operator record with live machine guards; both are required."""
    if not admission.admitted:
        raise ValueError("the persisted sweep admission is not affirmative")
    live = compute_admission(root, operator_admitted=True)
    if not live["admitted"]:
        raise ValueError("live machine guards refused the sweep admission")
    live["probe_cap_minutes"] = admission.probe_cap_minutes
    live["session_cap_minutes"] = admission.session_cap_minutes
    return {
        "operator": admission.operator,
        "timestamp_utc": admission.timestamp_utc,
        "admission": live,
    }


def sweep_cell_identity(
    *, root: Path, plan: Any, method_config: Mapping[str, Any],
    protocol_sha256: str, episode_sha256: str, selection_sha256: str,
    preprocessing_sha256: str, checkpoint_sha256: str,
) -> CellIdentity:
    """Build the cell identity from live provenance and pinned digests."""
    source = capture_source(root)
    if type(source.git_dirty) is not bool:
        raise ValueError("live Git dirty state is required for a sweep identity")
    return CellIdentity(
        dataset=plan.dataset, target_subject=plan.target_subject,
        method=plan.method, shots_per_class=plan.shots_per_class,
        model_seed=plan.model_seed, support_draw_seed=None, montage_seed=None,
        protocol_sha256=protocol_sha256, episode_sha256=episode_sha256,
        selection_sha256=selection_sha256,
        method_config_sha256=method_configuration(method_config),
        preprocessing_sha256=preprocessing_sha256,
        checkpoint_sha256=checkpoint_sha256,
        source_sha256=source.source_sha256,
        environment_sha256=environment_digest(),
        git_commit=source.git_commit, git_dirty=source.git_dirty,
    )


def run_cho_first_tranche_sweep(
    *, root: Path, recorder: CaseRecorder, route: ChoFirstTrancheRoute,
    admission_path: Path, method_configs: Mapping[str, Mapping[str, Any]],
    case_runner: CaseRunner, worker: str, receipt_path: Path,
) -> dict[str, Any]:
    """Execute incomplete cases under stable pins, stopping on shared refusals.

    Independent case failures may advance. Source/admission changes, conflicting
    historical cells and shared resource/session refusals end the sweep. The
    injectable runner remains responsible for supervising the entire expensive
    case; target-only timers cannot bound source selection.
    """
    root = root.resolve()
    if receipt_path.exists():
        raise RuntimeError("sweep receipt already exists")
    if set(method_configs) != {"labram_linear", "labram_lora", "labram_full", "eegnet"}:
        raise ValueError("sweep method configurations must cover the four Cho methods")
    if len({plan.identity_key for plan in route.plans}) != len(route.plans):
        raise ValueError("sweep route repeats a measured case identity")
    admission = SweepAdmission.load(admission_path)
    before = sweep_pin_snapshot(root, method_configs)
    admission_snapshot: dict[str, Any] | None = None
    outcomes: dict[str, dict[str, Any]] = {}
    completed: list[str] = []
    failed: dict[str, str] = {}
    attempted: list[str] = []
    skipped: list[str] = []
    stopped: dict[str, Any] | None = None
    started = time.monotonic()
    current_case: str | None = None

    def renew_execution_pins() -> None:
        if sweep_pin_snapshot(root, method_configs) != before:
            raise SweepStopped("source, environment or method pins changed", kind="provenance")
        renewed = SweepAdmission.load(admission_path)
        if renewed.file_sha256 != admission.file_sha256:
            raise SweepStopped("persisted admission bytes changed", kind="admission")
        sweep_admission_snapshot(root, renewed)
        if (time.monotonic() - started) / 60.0 >= admission.session_cap_minutes:
            raise SweepStopped("the sweep session cap is exhausted", kind="session")

    try:
        admission_snapshot = sweep_admission_snapshot(root, admission)
        executor = TargetCaseExecutor(
            root, recorder, admission=admission_snapshot["admission"], worker=worker,
        )
        measured = _measured_cell_records(recorder)
        resumed_identities: dict[tuple[Any, ...], CellIdentity] = {}
        # Refuse every known conflicting cell before selecting any new case.
        resumed_plans = [plan for plan in route.plans if plan.identity_key in measured]
        for plan in resumed_plans:
            current_case = plan.case_id
            identity = verify_sweep_resume_cell(
                measured[plan.identity_key], plan=plan, route=route,
                method_config=method_configs[plan.method], pins=before,
            )
            resumed_identities[plan.identity_key] = identity
            _verify_resume_publication(
                root, measured[plan.identity_key], plan=plan, route=route,
                method_config=method_configs[plan.method], identity=identity, pins=before,
            )
        if resumed_plans:
            completion = recorder.completion(resumed_plans)
            if completion["measured"] != len(resumed_plans):
                raise SweepResumeConflict("a resumed cell has no verified successful attempt")
            for plan in resumed_plans:
                current_case = plan.case_id
                _verify_resume_success(
                    recorder, measured[plan.identity_key], plan=plan,
                    identity=resumed_identities[plan.identity_key],
                )
        for plan in route.plans:
            case_id = plan.case_id
            current_case = case_id
            renew_execution_pins()
            if plan.identity_key in measured:
                outcomes[case_id] = {"status": "already_complete"}
                completed.append(case_id)
                skipped.append(case_id)
                continue
            attempted.append(case_id)
            case_started = time.monotonic()
            try:
                cell = case_runner(
                    plan=plan, executor=executor, route=route,
                    method_config=method_configs[plan.method],
                )
            except Exception as error:  # noqa: BLE001 - isolated case failures are evidence
                if _shared_refusal(error):
                    raise
                failed[case_id] = f"{type(error).__name__}: {error}"
                outcomes[case_id] = {"status": "failed", "reason": failed[case_id]}
                continue
            result = dict(cell)
            try:
                renew_execution_pins()
                if (time.monotonic() - case_started) / 60.0 >= admission.probe_cap_minutes:
                    raise SweepStopped("the whole-case probe cap is exceeded", kind="case_cap")
            except Exception as error:  # noqa: BLE001 - returned output is not accepted on drift
                outcomes[case_id] = {
                    "status": "stopped", "reason": f"{type(error).__name__}: {error}",
                    "quarantined_result": result,
                }
                raise
            outcomes[case_id] = {"status": "complete", "result": result}
            completed.append(case_id)
        current_case = None
    except (Exception, KeyboardInterrupt) as error:  # noqa: BLE001 - persist partial accounting
        stopped = {
            "reason": f"{type(error).__name__}: {error}",
            "kind": getattr(error, "kind", "interrupted" if isinstance(
                error, KeyboardInterrupt
            ) else "guard"),
            "case_id": current_case,
        }
        if current_case is not None and current_case not in outcomes:
            outcomes[current_case] = {"status": "stopped", "reason": stopped["reason"]}
    for plan in route.plans:
        outcomes.setdefault(plan.case_id, {"status": "not_attempted"})
    try:
        after = sweep_pin_snapshot(root, method_configs)
    except (TypeError, ValueError) as error:
        after = {
            **asdict(capture_source(root)), "environment_sha256": environment_digest(),
            "method_config_sha256": None,
        }
        if stopped is None:
            stopped = {"reason": f"final execution pins no longer verify: {error}",
                       "kind": "provenance", "case_id": None}
    try:
        admission_after_sha256: str | None = SweepAdmission.load(admission_path).file_sha256
    except (ValueError, OSError) as error:
        admission_after_sha256 = None
        if stopped is None:
            stopped = {"reason": f"final admission no longer verifies: {error}",
                       "kind": "admission", "case_id": None}
    admission_stable = admission_after_sha256 == admission.file_sha256
    if not admission_stable and stopped is None:
        stopped = {"reason": "persisted admission bytes changed during the sweep",
                   "kind": "admission", "case_id": None}
    if before != after and stopped is None:
        stopped = {"reason": "execution pins changed during the sweep",
                   "kind": "provenance", "case_id": None}
    source_fields = ("source_sha256", "git_commit", "git_dirty")
    receipt = {
        "schema": SWEEP_RECEIPT_SCHEMA,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "status": "stopped" if stopped else (
            "complete" if len(completed) == len(route.plans) else "partial"
        ),
        "source_sha256": before["source_sha256"],
        "source_before": {field: before[field] for field in source_fields},
        "source_after": {field: after[field] for field in source_fields},
        "source_stable": all(before[field] == after[field] for field in source_fields),
        "environment_before_sha256": before["environment_sha256"],
        "environment_after_sha256": after["environment_sha256"],
        "execution_pins_stable": before == after,
        "method_config_sha256": before["method_config_sha256"],
        "admission_file_sha256": admission.file_sha256,
        "admission_after_file_sha256": admission_after_sha256,
        "admission_file_stable": admission_stable,
        "admission": admission_snapshot,
        "worker": worker,
        "elapsed_seconds": time.monotonic() - started,
        "total_cases": len(route.plans),
        "completed_cases": len(completed),
        "newly_completed_cases": len(completed) - len(skipped),
        "already_completed_cases": len(skipped),
        "attempted_cases": len(attempted),
        "failed_cases": len(failed),
        "stopped_cases": sum(row["status"] == "stopped" for row in outcomes.values()),
        "not_attempted_cases": sum(row["status"] == "not_attempted" for row in outcomes.values()),
        "stop": stopped,
        "outcomes": outcomes,
        "resume_verification_scope": (
            "execution_identity,recorder_success,selection_and_publication_bytes; "
            "tensor_restore_and_full_target_attestation_analysis_required"
        ),
        "whole_case_supervision": "caller_responsibility",
        "scientific_claims_made": 0,
        "scientific_freeze_ratified": False,
        "gate_a_signed": False,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return receipt


def materialize_cho_candidates(
    method: str, method_config: Mapping[str, Any], seed: int,
) -> tuple[Any, ...]:
    """Build the selector's typed candidate roster from the method configuration."""
    from adaptation.anchor_manifest import EEGNetAnchorSettings
    from adaptation.labram_lora_trained import (
        LoRAContinuationSettings,
        LoRASourceCandidate,
        LoRASourceSettings,
    )
    from adaptation.labram_manifest import LaBraMTuningSettings
    from adaptation.labram_source import (
        LaBraMSourceCandidate,
        LaBraMSourceSettings,
    )
    from adaptation.source_selection import (
        EEGNetCandidate,
        EEGNetSourceSettings,
    )
    from evaluation.phase2_cho_source_restore import _candidate_settings

    rows = method_config.get("candidates")
    if not isinstance(rows, list) or not rows:
        raise ValueError("method configuration candidate roster is missing")
    candidates: list[Any] = []
    for row in rows:
        source, support, _materialized = _candidate_settings(method, row, seed)
        if method == "eegnet":
            if not isinstance(source, EEGNetSourceSettings) or not isinstance(
                support, EEGNetAnchorSettings
            ):
                raise ValueError("eegnet candidate settings differ from the roster")
            candidates.append(EEGNetCandidate(row["name"], source, support))
        elif method == "labram_lora":
            if not isinstance(source, LoRASourceSettings) or not isinstance(
                support, LoRAContinuationSettings
            ):
                raise ValueError("lora candidate settings differ from the roster")
            candidates.append(LoRASourceCandidate(row["name"], source, support))
        else:
            if not isinstance(source, LaBraMSourceSettings) or not isinstance(
                support, LaBraMTuningSettings
            ):
                raise ValueError("plain LaBraM candidate settings differ from the roster")
            candidates.append(LaBraMSourceCandidate(row["name"], source, support))
    return tuple(candidates)


class ProductionChoCaseRunner:
    """Per-case production wiring: selection, publication, execution, cell.

    Holds every cross-case input (protocol, catalogs, records, templates,
    ceilings) and runs one case at a time when called by the sweep
    orchestration. All heavy behaviour lives in the tested selectors, the
    publication gate and the admission-gated executor; this class only
    wires them in the order the analysis chain has verified.

    A supplied LaBraM selection runner wraps only source selection. Its returned
    evidence and model still pass the same publication and target checks.
    Without that explicit runner, every selector follows its original route.
    """

    def __init__(
        self, *, root: Path, recorder: CaseRecorder,
        protocol_config: Mapping[str, Any],
        catalogs: tuple[Any, ...],
        episode_records: Mapping[str, Mapping[str, Any]],
        selection_records: Mapping[str, Mapping[str, Any]],
        profile_assets: Mapping[str, Any],
        profile_a_manifests: Mapping[str, str],
        labram_template: Any | None,
        maximum_gradient_steps: int,
        labram_source_selection_runner: Callable[[Any], Any] | None = None,
    ) -> None:
        if type(maximum_gradient_steps) is not int or maximum_gradient_steps < 1:
            raise ValueError("a positive gradient-step ceiling is required")
        if labram_source_selection_runner is not None and not callable(
            labram_source_selection_runner
        ):
            raise ValueError("LaBraM source selection runner must be callable")
        # The selectors enforce their own hard engineering ceilings; this
        # runner only passes the configured value through.
        self.root = root.resolve()
        self.recorder = recorder
        self.protocol_config = protocol_config
        self.catalogs = catalogs
        self.episode_records = episode_records
        self.selection_records = selection_records
        self.profile_assets = profile_assets
        self.profile_a_manifests = profile_a_manifests
        self.labram_template = labram_template
        self.maximum_gradient_steps = maximum_gradient_steps
        self._labram_source_selection_runner = labram_source_selection_runner

    def __call__(
        self, *, plan: Any, executor: Any, route: Any,
        method_config: Mapping[str, Any],
    ) -> dict[str, Any]:
        from dataclasses import asdict as _asdict

        from adaptation.labram_source import BCILaBraMSourceSelector
        from adaptation.source_selection import BCIEEGNetSourceSelector
        from evaluation.labram_parity import state_digest
        from evaluation.phase2_cho_publication_gate import publish_verified_cho_source
        from evaluation.phase2_pilot import (
            AnchorAdapter,
            LaBraMTunedAdapter,
            TrainedLaBraMAdapter,
        )
        from evaluation.phase2_selection_evidence_binding import (
            verify_cho_selection_evidence,
        )

        episode_record = self.episode_records[plan.target_subject]
        selection_record = self.selection_records[plan.target_subject]
        candidates = materialize_cho_candidates(
            plan.method, method_config, plan.model_seed,
        )
        selector: Any
        if plan.method == "eegnet":
            selector = BCIEEGNetSourceSelector(
                self.root, self.protocol_config, self.catalogs, selection_record,
                self.profile_a_manifests,
                outer_target=plan.target_subject, candidates=candidates,
                seed=plan.model_seed, shots_per_class=plan.shots_per_class,
                maximum_gradient_steps=self.maximum_gradient_steps,
            )
        else:
            if self.labram_template is None:
                raise ValueError("a pinned LaBraM template is required for LaBraM cases")
            selector = BCILaBraMSourceSelector(
                self.root, self.protocol_config, self.catalogs, selection_record,
                self.labram_template, self.profile_assets,
                outer_target=plan.target_subject,
                template_state_sha256=state_digest(self.labram_template),
                candidates=candidates, seed=plan.model_seed,
                shots_per_class=plan.shots_per_class,
                maximum_gradient_steps=self.maximum_gradient_steps,
            )
        if plan.method != "eegnet" and self._labram_source_selection_runner is not None:
            selected = self._labram_source_selection_runner(selector)
        else:
            selected = selector.run_selection()
        evidence = selected.evidence
        evidence_sha256 = evidence.record["sha256"]
        evidence_path = self.root / "runs/phase2/selection_evidence" / f"{evidence_sha256}.json"
        if not evidence_path.exists():
            evidence.write(evidence_path, output_root=self.root / "runs/phase2")
        winner_name = evidence.record["payload"]["selected_candidate"]
        winner = next(c for c in candidates if c.name == winner_name)
        adapter: Any
        if plan.method == "eegnet":
            adapter = AnchorAdapter("eegnet", winner.support, selected.source)
        elif plan.method == "labram_lora":
            from encoder.labram import LaBraMClassifier

            if not isinstance(selected.source, LaBraMClassifier):
                raise ValueError("lora selection returned an unexpected model class")
            adapter = TrainedLaBraMAdapter(
                "labram_lora", selected.source, winner.source, winner.support,
            )
        else:
            from encoder.labram import LaBraMClassifier

            if not isinstance(selected.source, LaBraMClassifier):
                raise ValueError("plain LaBraM selection returned an unexpected model class")
            adapter = LaBraMTunedAdapter(plan.method, selected.source, winner.support)
        target_catalog = next(
            catalog for catalog in self.catalogs
            if catalog.subject == plan.target_subject
        )
        fitted = adapter._model
        if fitted is None:
            raise ValueError("the fitted adapter model is missing")
        assets = {} if plan.method == "eegnet" else self.profile_assets
        identity = sweep_cell_identity(
            root=self.root, plan=plan, method_config=method_config,
            protocol_sha256=config_digest_of(self.protocol_config),
            episode_sha256=episode_record["sha256"],
            selection_sha256=selection_record["sha256"],
            preprocessing_sha256=target_catalog.preprocessing_sha256,
            checkpoint_sha256=state_digest(fitted),
        )
        verified = verify_cho_selection_evidence(
            record=evidence.record, evidence_sha256=evidence_sha256, plan=plan,
            protocol_config=self.protocol_config, catalogs=self.catalogs,
            selection_record=selection_record,
            root=self.root, adapter_model_state_sha256=state_digest(fitted),
            adapter_source_settings=_asdict(winner.source),
            adapter_support_settings=_asdict(winner.support),
            assets=assets,
        )
        publication = publish_verified_cho_source(
            root=self.root, plan=plan, adapter=adapter, identity=identity,
            method_config=method_config, protocol_config=self.protocol_config,
            evidence_path=evidence_path, selection=verified,
        )
        published = publication.publication
        result = executor.run_case(
            plan, adapter=adapter, identity=identity,
            method_config=method_config,
            selection_evidence_sha256=evidence_sha256,
            selection_evidence_path=evidence_path,
            protocol_config=self.protocol_config, catalogs=self.catalogs,
            selection_record=selection_record, episode_record=episode_record,
            assets=assets,
        )
        return {
            "cell": str(result["cell"]),
            "selection_evidence_sha256": evidence_sha256,
            "selected_manifest_sha256": published.manifest_sha256,
            "selected_weights_sha256": published.weights_sha256,
        }


def config_digest_of(mapping: Mapping[str, Any]) -> str:
    from core.config import config_digest

    return config_digest(mapping)
