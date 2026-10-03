"""Read-only Cho recorder verification and paired-input preparation.

The caller supplies independently reviewed case-input, method and source
pins. This composition rederives the route from pinned inputs, verifies case
identities, then checks each recorded target input attestation before score
extraction and paired-input construction. Each selected-source tensor state
is verified in an isolated supervised child process under an explicit
memory cap, one case at a time; any child failure refuses the whole roster.
It does not admit a scientific freeze, run inference, or publish a report.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from core.config import config_snapshot
from core.provenance import SourceProvenance
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell, verified_score_rows
from evaluation.phase2_cho_analysis_identity import verify_cho_case_identity_bindings
from evaluation.phase2_cho_case_inputs import (
    SELECTED_METHODS,
    ChoCaseInputPins,
    ChoFirstTrancheRoute,
    prepare_cho_first_tranche,
)
from evaluation.phase2_cho_paired_inputs import ChoPairedInputs, build_cho_paired_inputs
from evaluation.phase2_cho_persisted_target import verify_cho_persisted_target_declarations
from evaluation.phase2_cho_selected_manifest_bridge import verify_cho_selected_manifest_files
from evaluation.phase2_cho_selection_file_bridge import (
    _evidence_path,
    verify_cho_recorded_selection_files,
)
from evaluation.phase2_cho_target_input_bridge import verify_cho_recorded_target_inputs
from evaluation.phase2_runner import CasePlan, CaseRecorder, method_configuration
from evaluation.phase2_subject_aggregation import ExpectedCell
from evaluation.phase2_supervision_primitives import (
    MAX_ATTEMPT_SECONDS,
    DeadlineLease,
    ResourceFloor,
    run_supervised,
)

TENSOR_CASE_CHILD_SCRIPT = "scripts/run_cho_tensor_case_child.py"
TENSOR_CASE_INPUT_SCHEMA = "cho_tensor_case_child_input_v1"
TENSOR_CASE_WITNESS_SCHEMA = "cho_tensor_case_child_witness_v1"

TensorCaseExecutor = Callable[..., Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class ChoSelectedSourcePin:
    """Independent per-case publication, recipe and target environment pins."""

    case_id: str
    manifest_sha256: str
    model_recipe_sha256: str
    environment_sha256: str


def run_cho_tensor_case_child(
    *, root: Path, workspace: Path, case_id: str, plan: CasePlan,
    method_config: Mapping[str, Any], expected_method_config_sha256: str,
    selected_candidate: str, manifest_sha256: str, evidence_sha256: str,
    protocol_config: Mapping[str, Any], expected_model_recipe_sha256: str,
    expected_model_state_sha256: str, memory_limit_bytes: int,
    attempt_seconds: float,
) -> dict[str, Any]:
    """Verify one tensor case in an owned supervised child process.

    Writes the pinned child input and a fresh deadline lease into the
    caller-owned workspace, runs ``scripts/run_cho_tensor_case_child.py``
    under a kill-on-close Job Object with a query-back-verified commit cap,
    and returns the child's exclusive-create digest witness. Any child
    failure, cap breach or lease expiry raises; a partial roster is never
    returned to the caller.
    """
    root = root.resolve()
    workspace = workspace.resolve()
    project = Path(__file__).resolve().parents[1]
    child_script = project / TENSOR_CASE_CHILD_SCRIPT
    python = project / ".venv" / "Scripts" / "python.exe"
    if not child_script.is_file() or not python.is_file():
        raise ValueError("tensor case child entrypoint or project Python is missing")
    stem = "".join(character if character.isalnum() else "_" for character in case_id)
    input_path = workspace / f"case_{stem}.input.json"
    witness_path = workspace / f"case_{stem}.witness.json"
    lease_path = workspace / f"case_{stem}.lease.json"
    if input_path.exists() or witness_path.exists():
        raise ValueError("tensor case workspace already holds this case")
    payload = {
        "schema": TENSOR_CASE_INPUT_SCHEMA,
        "case_id": case_id,
        "root": str(root),
        "plan": asdict(plan),
        "method_config": dict(method_config),
        "expected_method_config_sha256": expected_method_config_sha256,
        "selected_candidate": selected_candidate,
        "manifest_sha256": manifest_sha256,
        "evidence_sha256": evidence_sha256,
        "protocol_config": dict(protocol_config),
        "expected_model_recipe_sha256": expected_model_recipe_sha256,
        "expected_model_state_sha256": expected_model_state_sha256,
    }
    with input_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    now = datetime.now(UTC)
    DeadlineLease.open_or_create(
        lease_path,
        attempt_deadline_utc=now + timedelta(seconds=attempt_seconds),
        session_deadline_utc=now + timedelta(seconds=min(2 * MAX_ATTEMPT_SECONDS, 900.0)),
    )
    result = run_supervised(
        [str(python), "-B", str(child_script),
         "--input", str(input_path), "--witness", str(witness_path)],
        cwd=project, deadline_path=lease_path, floor=ResourceFloor(),
        process_memory_limit_bytes=memory_limit_bytes,
    )
    if result.reason != "normal" or result.exit_code != 0:
        raise ValueError(
            f"tensor case child for {case_id} failed: {result.reason} exit {result.exit_code}"
        )
    if result.peak_process_memory_bytes is None or result.peak_process_memory_bytes <= 0:
        raise ValueError("tensor case child did not report a measured peak")
    if result.peak_process_memory_bytes > memory_limit_bytes:
        raise ValueError("tensor case child exceeded its verified memory cap")
    witness = json.loads(witness_path.read_text("utf-8"))
    if (
        not isinstance(witness, dict)
        or witness.get("schema") != TENSOR_CASE_WITNESS_SCHEMA
        or witness.get("case_id") != case_id
    ):
        raise ValueError("tensor case witness differs from the pinned schema")
    return witness


def prepare_cho_paired_inputs_from_recorder(
    route: ChoFirstTrancheRoute,
    recorder: CaseRecorder,
    pins: Sequence[PinnedCaseCell],
    *,
    project_root: Path,
    case_input_pins: ChoCaseInputPins,
    base_config_sha256: str,
    method_config_sha256: Mapping[str, str],
    method_configs: Mapping[str, Mapping[str, Any]],
    selected_source_pins: Sequence[ChoSelectedSourcePin],
    expected_source: SourceProvenance,
    case_workspace: Path,
    case_memory_limit_bytes: int,
    case_attempt_seconds: float = 480.0,
    case_executor: TensorCaseExecutor | None = None,
) -> ChoPairedInputs:
    """Return paired inputs only after complete identity and recorder checks.

    ``case_input_pins`` and ``expected_source`` must be supplied independently
    of the route and cell pins. Route preparation rechecks all 52 Profile A
    catalogs and B artifact/manifest hashes, plus pinned protocol, threshold,
    cohort and variant bytes. This function also verifies bounded base,
    variant and B manifest declarations and binds each recorded selection file.
    It checks externally pinned selected-source publication bytes, reconstructed
    checkpoint state and target environment claims, verifying every selected
    tensor state in an isolated supervised child under the caller's explicit
    memory cap, one case at a time. It does not verify raw source bytes,
    complete selector work, actual past environment or freeze.
    """
    if not isinstance(expected_source, SourceProvenance):
        raise ValueError("independently supplied expected source is required")
    if not isinstance(case_input_pins, ChoCaseInputPins):
        raise ValueError("independently supplied typed Cho case input pins are required")
    if (
        not isinstance(case_workspace, Path)
        or not case_workspace.is_absolute()
        or not case_workspace.is_dir()
        or recorder.output_root.is_relative_to(case_workspace)
        or case_workspace.is_relative_to(recorder.output_root)
    ):
        raise ValueError("an independent absolute tensor-case workspace is required")
    if type(case_memory_limit_bytes) is not int or case_memory_limit_bytes <= 0:
        raise ValueError("a positive tensor-case memory cap is required")
    if not 0 < case_attempt_seconds <= MAX_ATTEMPT_SECONDS:
        raise ValueError("tensor-case attempt seconds exceed the supervision cap")
    if (
        not isinstance(project_root, Path)
        or not isinstance(recorder, CaseRecorder)
        or not recorder.output_root.is_relative_to(project_root.resolve() / "runs/phase2")
    ):
        raise ValueError("Cho recorder must belong to the reviewed project root")
    if not isinstance(route, ChoFirstTrancheRoute):
        raise ValueError("a typed Cho first-tranche route is required")
    rederived_route = prepare_cho_first_tranche(project_root, pins=case_input_pins)
    if route != rederived_route:
        raise ValueError("supplied Cho route differs from the pinned rederived route")
    if (
        not isinstance(method_config_sha256, Mapping)
        or set(method_config_sha256) != set(SELECTED_METHODS)
        or not isinstance(method_configs, Mapping)
        or set(method_configs) != set(SELECTED_METHODS)
    ):
        raise ValueError("independent static method configs and digests require four Cho methods")
    checked_configs: dict[str, dict[str, Any]] = {}
    checked_digests = {method: method_config_sha256[method] for method in SELECTED_METHODS}
    for method in SELECTED_METHODS:
        proposed = method_configs[method]
        if not isinstance(proposed, Mapping) or any(
            not isinstance(key, str) for key in proposed
        ):
            raise ValueError(f"{method} static method config must be a string-keyed mapping")
        config = config_snapshot(proposed)
        if (
            config.get("method") != method
            or config.get("dataset") != "cho2017"
            or method_configuration(config) != checked_digests[method]
        ):
            raise ValueError(f"{method} static method config differs from independent digest")
        checked_configs[method] = config
    verify_cho_case_identity_bindings(
        route, pins,
        method_config_sha256=checked_digests,
        expected_source=expected_source,
    )
    declarations = verify_cho_persisted_target_declarations(
        project_root, route, base_config_sha256=base_config_sha256,
    )
    verify_cho_recorded_target_inputs(
        route, recorder, pins, declarations=declarations,
    )
    selection_witness = verify_cho_recorded_selection_files(
        route, recorder, pins,
        project_root=project_root, expected_source=expected_source,
        method_config_sha256=checked_digests,
    )
    if (
        not isinstance(selected_source_pins, Sequence)
        or isinstance(selected_source_pins, (str, bytes))
        or len(selected_source_pins) != len(pins)
        or any(not isinstance(pin, ChoSelectedSourcePin) for pin in selected_source_pins)
    ):
        raise ValueError("independent selected-source pins must cover the Cho roster")
    publication_pins = {pin.case_id: pin for pin in selected_source_pins}
    case_pins = {pin.plan.case_id: pin for pin in pins}
    if len(publication_pins) != len(pins) or set(publication_pins) != set(case_pins):
        raise ValueError("selected-source pins are missing, duplicate or outside Cho roster")
    manifest_witnesses = []
    for claim in selection_witness.claims:
        pin = case_pins[claim.case_id]
        publication = publication_pins[claim.case_id]
        if (
            claim.manifest_sha256 != publication.manifest_sha256
            or claim.manifest_path is None
            or pin.identity.environment_sha256 != publication.environment_sha256
        ):
            raise ValueError("Cho selected-source or target environment pin differs")
        manifest_witnesses.append(verify_cho_selected_manifest_files(
            project_root,
            _evidence_path(project_root, claim.manifest_path),
            manifest_sha256=publication.manifest_sha256,
            evidence_sha256=claim.evidence_sha256,
            selection_contract_sha256=claim.contract_sha256,
            selected_candidate=claim.selected_candidate,
            protocol_config_sha256=pin.identity.protocol_sha256,
            expected_source=expected_source,
            model_recipe_sha256=publication.model_recipe_sha256,
            model_state_sha256=pin.identity.checkpoint_sha256,
        ))
    protocol_config: dict[str, Any] = json.loads(rederived_route.protocol_config_json)
    executor = case_executor if case_executor is not None else run_cho_tensor_case_child
    for claim, manifest_witness in zip(selection_witness.claims, manifest_witnesses, strict=True):
        pin = case_pins[claim.case_id]
        publication = publication_pins[claim.case_id]
        if claim.manifest_sha256 is None:
            raise ValueError("Cho selected-source manifest digest is missing")
        case_witness = executor(
            root=project_root, workspace=case_workspace, case_id=claim.case_id,
            plan=pin.plan,
            method_config=checked_configs[pin.plan.method],
            expected_method_config_sha256=checked_digests[pin.plan.method],
            selected_candidate=claim.selected_candidate,
            manifest_sha256=claim.manifest_sha256,
            evidence_sha256=claim.evidence_sha256,
            protocol_config=protocol_config,
            expected_model_recipe_sha256=publication.model_recipe_sha256,
            expected_model_state_sha256=pin.identity.checkpoint_sha256,
            memory_limit_bytes=case_memory_limit_bytes,
            attempt_seconds=case_attempt_seconds,
        )
        if (
            case_witness["manifest_sha256"] != claim.manifest_sha256
            or case_witness["evidence_sha256"] != claim.evidence_sha256
            or case_witness["selected_candidate"] != claim.selected_candidate
            or case_witness["model_recipe_sha256"] != publication.model_recipe_sha256
            or case_witness["model_state_sha256"] != pin.identity.checkpoint_sha256
            or case_witness["weights_sha256"] != manifest_witness.weights_sha256
        ):
            raise ValueError("restored Cho selected source differs from independent pins")
    expected_roster = tuple(ExpectedCell(*plan.identity_key) for plan in route.plans)
    rows = verified_score_rows(recorder, expected_roster, pins)
    paired = build_cho_paired_inputs(rows)
    selection_witness.verify_stable()
    for witness in manifest_witnesses:
        witness.verify_stable()
    return paired
