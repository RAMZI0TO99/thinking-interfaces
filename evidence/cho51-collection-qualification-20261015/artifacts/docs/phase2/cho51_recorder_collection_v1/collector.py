"""Read-only recorder and target-declaration checks for the adopted 51 targets.

This is the first collection stage. Selection files, selected publications and
restored tensors must still be verified before paired analysis is admitted.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from core.provenance import SourceProvenance
from docs.phase2.cho51_execution_interfaces_v1.interfaces import (
    verify_case_identity_bindings,
    verify_route,
)
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import (
    Cho51WorkerRoute,
    prepare_cho51_worker_route,
)
from evaluation.phase2_cell_aggregation_bridge import (
    MAX_CELL_BYTES,
    PinnedCaseCell,
    _canonical_record,
    verified_score_rows,
)
from evaluation.phase2_cho_case_inputs import ChoCaseInputPins
from evaluation.phase2_cho_persisted_target import (
    ChoPersistedTargetDeclarations,
    verify_cho_persisted_target_declarations,
)
from evaluation.phase2_cho_target_input_bridge import (
    _mapping,
    _profile_a,
    _profile_b,
    _query_metrics,
)
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import verify_envelope
from evaluation.phase2_runner import CaseRecorder
from evaluation.phase2_subject_aggregation import ExpectedCell, ScoreRow
from scripts.audit_phase2_protocol import validate_protocol


@dataclass(frozen=True, slots=True)
class Cho51RecorderCollection:
    """Checked recorder rows; this type is deliberately not paired-analysis input."""

    rows: tuple[ScoreRow, ...]
    owner_decision_sha256: str

    @property
    def selection_publication_tensor_verified(self) -> bool:
        return False

    @property
    def scientific_result_admitted(self) -> bool:
        return False


def _verify_target_inputs(
    route: Cho51WorkerRoute,
    recorder: CaseRecorder,
    pins: tuple[PinnedCaseCell, ...],
    declarations: ChoPersistedTargetDeclarations,
) -> None:
    """Bind every retained cell to its planned query and target declarations.

    The public entrypoint has already checked the complete independent identity
    pins. The unchanged profile checkers retain all 52 available source assets.
    This loop replaces only the legacy outer 1,040-cell roster requirement.
    """
    full = route._full_route
    shots = validate_protocol(json.loads(full.protocol_config_json))
    catalogs = {catalog.subject: catalog for catalog in route.catalogs}
    plans = {plan.case_id: plan for plan in route.plans}
    if (
        len(catalogs) != 52
        or len(plans) != 1020
        or len(pins) != 1020
        or {pin.plan.case_id for pin in pins} != set(plans)
    ):
        raise ValueError("complete 51-target pins and 52 available catalogs required")

    # Cache only immutable, rederived metadata, never cell attestations.
    episodes = {}
    selections = {}
    for pin in pins:
        plan = pin.plan
        if plan != plans[plan.case_id] or plan.target_subject == "subject_01":
            raise ValueError("target pin differs from the adopted 51-target route")
        catalog = catalogs[plan.target_subject]
        if plan.target_subject not in episodes:
            episodes[plan.target_subject] = nested_episode(
                catalog, shots=shots, protocol_sha256=pin.identity.protocol_sha256,
            )
            selections[plan.target_subject] = source_selection(
                route.catalogs, target=plan.target_subject,
            )
        episode = episodes[plan.target_subject]
        selection = selections[plan.target_subject]
        partition = episode.partition(plan.shots_per_class)
        support_ids = tuple(catalog.trial_ids[i] for i in partition.support_indices)
        query_ids = tuple(catalog.trial_ids[i] for i in partition.query_indices)
        path = recorder.output_root / "cells" / f"{pin.identity.sha256}.json"
        cell, _ = _canonical_record(path, maximum_bytes=MAX_CELL_BYTES)
        payload = _mapping(cell.get("payload"), "Cho51 target cell payload")
        if (
            cell.get("sha256") != pin.cell_sha256
            or set(payload) != {"identity", "metrics"}
            or payload["identity"] != asdict(pin.identity)
            or not verify_envelope(cell, kind="evaluation_cell", expected_payload=payload)
        ):
            raise ValueError("Cho51 target cell differs from external pin")
        metrics = _mapping(payload["metrics"], "Cho51 target cell metrics")
        _query_metrics(metrics, catalog, partition.query_indices)
        attestation = _mapping(
            metrics.get("target_input_attestation"), "Cho51 target input attestation",
        )
        if (
            attestation.get("schema") != "cho2017-target-input-v1"
            or attestation.get("method") != plan.method
            or attestation.get("subject") != plan.target_subject
            or attestation.get("episode_record_sha256") != pin.identity.episode_sha256
        ):
            raise ValueError("Cho51 target attestation differs from case identity")
        if plan.method == "eegnet":
            if attestation.get("profile") != "cho_profile_a":
                raise ValueError("Cho51 EEGNet target must use Profile A")
            _profile_a(
                attestation, declarations, pin, catalog,
                episode.sha256, selection.sha256, selection.source_subjects,
                support_ids, query_ids,
            )
        else:
            if attestation.get("profile") != "cho_profile_b_60hz_v1":
                raise ValueError("Cho51 LaBraM target must use 60 Hz Profile B")
            _profile_b(
                attestation, full, declarations, pin, catalog,
                episode.sha256, support_ids, query_ids,
            )


def collect_recorder_rows(
    project_root: Path,
    route: Cho51WorkerRoute,
    recorder: CaseRecorder,
    pins: Sequence[PinnedCaseCell],
    *,
    case_input_pins: ChoCaseInputPins,
    base_config_sha256: str,
    method_config_sha256: Mapping[str, str],
    expected_source: SourceProvenance,
) -> Cho51RecorderCollection:
    """Verify all 1,020 ledger cells and target declarations, without model I/O.

    Independent pins must come from outside the writable recorder tree. The
    original all-52 input loader is invoked afresh and hashes/reads its real
    assets; a metadata-only caller route cannot stand in for that verification.
    No recorder is constructed and no cell, claim or attempt is written here.
    """
    if (
        not isinstance(project_root, Path)
        or not project_root.is_absolute()
        or project_root.resolve() != project_root
        or not project_root.is_dir()
        or type(route) is not Cho51WorkerRoute
        or type(recorder) is not CaseRecorder
        or not isinstance(case_input_pins, ChoCaseInputPins)
        or not isinstance(expected_source, SourceProvenance)
    ):
        raise ValueError("direct absolute project and typed independent inputs required")
    output = recorder.output_root
    if (
        not isinstance(output, Path)
        or not output.is_absolute()
        or output.resolve() != output
        or output.is_symlink()
        or not output.is_dir()
        or not output.is_relative_to(project_root / "runs" / "phase2")
        or output == project_root / "runs" / "phase2"
    ):
        raise ValueError("recorder must be an existing direct project runs/phase2 child")
    if not isinstance(pins, Sequence) or isinstance(pins, (str, bytes)):
        raise ValueError("complete independent case pin sequence required")
    pinned = tuple(pins)
    if not isinstance(method_config_sha256, Mapping):
        raise ValueError("independent method digest mapping required")
    methods = dict(method_config_sha256)
    # Refuse bad identities before any recorder-cell or real asset read.
    verify_case_identity_bindings(
        project_root, route, pinned,
        method_config_sha256=methods, expected_source=expected_source,
    )
    rederived = prepare_cho51_worker_route(project_root, input_pins=case_input_pins)
    verify_route(project_root, rederived)
    # Private planner reloads create different contract dataclass types.
    # Compare their complete values, including the immutable full input route.
    contract_fields = (
        "plans", "catalogs", "selections", "method_config_sha256", "owner_decision_sha256",
    )
    if (
        route._full_route != rederived._full_route
        or any(getattr(route.contract, name) != getattr(rederived.contract, name)
               for name in contract_fields)
    ):
        raise ValueError("route differs from independently pinned real inputs")
    declarations = verify_cho_persisted_target_declarations(
        project_root, rederived._full_route, base_config_sha256=base_config_sha256,
    )
    _verify_target_inputs(rederived, recorder, pinned, declarations)
    roster = tuple(ExpectedCell(*plan.identity_key) for plan in rederived.plans)
    rows = verified_score_rows(recorder, roster, pinned)
    # The cell pin fixes the bytes inspected by both target and ledger checks.
    # Recheck small persisted declarations across the whole collection interval.
    if declarations != verify_cho_persisted_target_declarations(
        project_root, rederived._full_route, base_config_sha256=base_config_sha256,
    ):
        raise ValueError("target declarations changed during collection")
    return Cho51RecorderCollection(rows, rederived.contract.owner_decision_sha256)
