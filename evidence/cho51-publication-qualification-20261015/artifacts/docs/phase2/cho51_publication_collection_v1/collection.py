"""Compose adopted-51 input/selection and selected-publication file checks.

This stage authenticates bounded publication bytes through the unchanged
manifest verifier. It never decodes tensors, constructs models, fits a
selector, aggregates paired results, starts attempts or admits science.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from core.provenance import SourceProvenance
from docs.phase2.cho51_input_collection_v1.collection import (
    Cho51InputCollection,
    _bind_claims,
    _bind_rows,
    collect_cho51_input_selection,
)
from docs.phase2.cho51_selection_files_v1.selection_files import (
    Cho51SelectionFileWitness,
    verify_cho51_recorded_selection_files,
)
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell, verified_score_rows
from evaluation.phase2_cho_analysis_preparation import ChoSelectedSourcePin
from evaluation.phase2_cho_case_inputs import (
    SELECTED_METHODS,
    SELECTED_SEEDS,
    ChoCaseInputPins,
)
from evaluation.phase2_cho_selected_manifest_bridge import (
    ChoSelectedManifestWitness,
    verify_cho_selected_manifest_files,
)
from evaluation.phase2_cho_selection_file_bridge import ChoSelectionFileClaim, _evidence_path
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_runner import CasePlan, CaseRecorder
from evaluation.phase2_subject_aggregation import ScoreRow


@dataclass(frozen=True, slots=True)
class Cho51PublicationBinding:
    """Immutable external identities bound to one verified publication file set."""

    case_id: str
    manifest_sha256: str
    manifest_path: Path
    evidence_sha256: str
    selection_contract_sha256: str
    selected_candidate: str
    protocol_config_sha256: str
    method_config_sha256: str
    environment_sha256: str
    model_recipe_sha256: str
    model_state_sha256: str
    weights_sha256: str


@dataclass(frozen=True, slots=True)
class Cho51PublicationCollection:
    """File-byte engineering evidence; selected tensor state remains unverified."""

    rows: tuple[ScoreRow, ...]
    selection_claims: tuple[ChoSelectionFileClaim, ...]
    publications: tuple[Cho51PublicationBinding, ...]
    owner_decision_sha256: str
    selection_ceiling_config_sha256: str

    @property
    def selected_publication_file_bytes_verified(self) -> bool:
        return True

    @property
    def selected_publications_verified(self) -> bool:
        # Preserve the broader admission boundary used by the preceding stage.
        return False

    @property
    def selected_tensors_verified(self) -> bool:
        return False

    @property
    def full_selector_evidence_verified(self) -> bool:
        return False

    @property
    def selection_publication_tensor_verified(self) -> bool:
        return False

    @property
    def scientific_result_admitted(self) -> bool:
        return False


def _snapshot_and_check(
    route: Cho51WorkerRoute,
    pins: Sequence[PinnedCaseCell],
    selected_source_pins: Sequence[ChoSelectedSourcePin],
    methods: Mapping[str, str],
    expected_source: SourceProvenance,
) -> tuple[tuple[PinnedCaseCell, ...], tuple[ChoSelectedSourcePin, ...], Mapping[str, str]]:
    """Reject incomplete/untyped or digest-invalid metadata before any file I/O."""
    if (
        type(route) is not Cho51WorkerRoute
        or not isinstance(pins, Sequence) or isinstance(pins, (str, bytes))
        or not isinstance(selected_source_pins, Sequence)
        or isinstance(selected_source_pins, (str, bytes))
        or not isinstance(methods, Mapping)
    ):
        raise ValueError("adopted route, case/publication pin sequences and method map required")
    pinned, publications = tuple(pins), tuple(selected_source_pins)
    checked_methods = MappingProxyType(dict(methods))
    if (
        len(pinned) != 1020 or any(type(pin) is not PinnedCaseCell for pin in pinned)
        or len({pin.plan.case_id for pin in pinned}) != 1020
        or len({pin.key for pin in pinned}) != 1020
    ):
        raise ValueError("exact 1,020 distinct typed external case pins required")
    if (
        len(publications) != 1020
        or any(type(pin) is not ChoSelectedSourcePin for pin in publications)
        or any(not isinstance(pin.case_id, str) or not pin.case_id for pin in publications)
        or len({pin.case_id for pin in publications}) != 1020
        or {pin.case_id for pin in publications} != {pin.plan.case_id for pin in pinned}
    ):
        raise ValueError("independent selected-source pins must exactly cover all 1,020 cases")
    expected_plans = {
        CasePlan("cho2017", f"subject_{subject:02d}", method, 5, seed, 1)
        for subject in range(2, 53) for method in SELECTED_METHODS for seed in SELECTED_SEEDS
    }
    if (
        type(route.plans) is not tuple or len(route.plans) != 1020
        or any(type(plan) is not CasePlan for plan in route.plans)
        or set(route.plans) != expected_plans
        or {pin.plan for pin in pinned} != expected_plans
    ):
        raise ValueError("case pins and route must cover the exact adopted 51-target roster")
    if (
        set(checked_methods) != set(SELECTED_METHODS)
        or dict(checked_methods) != dict(route.contract.method_config_sha256)
    ):
        raise ValueError("unchanged adopted four-method digest map required")
    for method, digest in checked_methods.items():
        require_digest(digest, method + " method config")
    if (
        type(expected_source) is not SourceProvenance
        or type(expected_source.git_dirty) is not bool
        or not isinstance(expected_source.git_commit, str)
        or len(expected_source.git_commit) not in (40, 64)
        or any(char not in "0123456789abcdef" for char in expected_source.git_commit)
    ):
        raise ValueError("independently supplied source provenance required")
    require_digest(expected_source.source_sha256, "expected source")
    require_digest(route.contract.owner_decision_sha256, "adopted owner decision")
    publication_by_case = {pin.case_id: pin for pin in publications}
    for publication in publications:
        for field in ("manifest_sha256", "model_recipe_sha256", "environment_sha256"):
            require_digest(getattr(publication, field), "publication " + field)
    for pin in pinned:
        identity = pin.identity
        if (
            identity.method_config_sha256 != checked_methods[pin.plan.method]
            or identity.source_sha256 != expected_source.source_sha256
            or identity.git_commit != expected_source.git_commit
            or identity.git_dirty is not expected_source.git_dirty
            or identity.environment_sha256 != publication_by_case[pin.plan.case_id].environment_sha256
        ):
            raise ValueError("case method, source or publication environment differs from external pins")
    return pinned, publications, checked_methods


def collect_cho51_publication_files(
    project_root: Path,
    route: Cho51WorkerRoute,
    recorder: CaseRecorder,
    pins: Sequence[PinnedCaseCell],
    *,
    selected_source_pins: Sequence[ChoSelectedSourcePin],
    case_input_pins: ChoCaseInputPins,
    base_config_sha256: str,
    method_config_sha256: Mapping[str, str],
    expected_source: SourceProvenance,
    selection_ceiling_config_sha256: str,
) -> Cho51PublicationCollection:
    """Bind 1,020 selected publication file sets to the qualified input stage.

    All external metadata is snapshotted and rejected if incomplete before
    input/data or publication reads. The real-input stage retains all 52 source
    subjects and the exact 51 evaluation targets. Its immutable claims are
    compared with a freshly retained physical selection witness. Ledger and
    physical witness rereads bracket publication inspection; they provide no
    filesystem lock. Publication files can use either format supported by the
    unchanged byte verifier. No safetensors decode or tensor executor runs.
    """
    pinned, publications, methods = _snapshot_and_check(
        route, pins, selected_source_pins, method_config_sha256, expected_source,
    )
    if (
        not isinstance(project_root, Path) or not project_root.is_absolute()
        or type(recorder) is not CaseRecorder or type(case_input_pins) is not ChoCaseInputPins
    ):
        raise ValueError("absolute project root, typed existing recorder and input pins required")
    require_digest(base_config_sha256, "independent base config")
    require_digest(selection_ceiling_config_sha256, "independent selection ceiling")
    collected = collect_cho51_input_selection(
        project_root, route, recorder, pinned, case_input_pins=case_input_pins,
        base_config_sha256=base_config_sha256, method_config_sha256=methods,
        expected_source=expected_source,
        selection_ceiling_config_sha256=selection_ceiling_config_sha256,
    )
    if (
        type(collected) is not Cho51InputCollection
        or collected.owner_decision_sha256 != route.contract.owner_decision_sha256
        or collected.selection_ceiling_config_sha256 != selection_ceiling_config_sha256
    ):
        raise ValueError("input collection differs from the same owner or ceiling pin")
    _bind_rows(collected.rows, pinned)
    _bind_claims(collected.selection_claims, pinned)
    selection = verify_cho51_recorded_selection_files(
        route, recorder, pinned, project_root=project_root,
        expected_source=expected_source, method_config_sha256=methods,
        selection_ceiling_config_sha256=selection_ceiling_config_sha256,
    )
    if (
        type(selection) is not Cho51SelectionFileWitness
        or selection.owner_decision_sha256 != collected.owner_decision_sha256
        or selection.ceiling.expected_sha256 != selection_ceiling_config_sha256
        or selection.claims != collected.selection_claims
    ):
        raise ValueError("fresh selection witness differs from the input-stage claims or pins")
    _bind_claims(selection.claims, pinned)
    case_by_id = {pin.plan.case_id: pin for pin in pinned}
    publication_by_id = {pin.case_id: pin for pin in publications}
    # Check the complete manifest association before opening even the first one.
    for claim in selection.claims:
        publication = publication_by_id[claim.case_id]
        if (
            claim.manifest_sha256 != publication.manifest_sha256
            or not isinstance(claim.manifest_path, str) or not claim.manifest_path
            or not isinstance(claim.selected_candidate, str) or not claim.selected_candidate
        ):
            raise ValueError("selected publication claim differs from independent manifest pin")
        require_digest(claim.contract_sha256, "selection contract")
    selection.verify_stable()
    roster = tuple(pin.key for pin in pinned)

    def ledger_rows() -> tuple[ScoreRow, ...]:
        rows = verified_score_rows(recorder, roster, pinned)
        _bind_rows(rows, pinned)
        if rows != collected.rows:
            raise ValueError("recorder rows changed during publication collection")
        return rows

    ledger_rows()
    witnesses: list[ChoSelectedManifestWitness] = []
    bindings: list[Cho51PublicationBinding] = []
    for claim in selection.claims:
        pin, publication = case_by_id[claim.case_id], publication_by_id[claim.case_id]
        manifest_path = _evidence_path(project_root, claim.manifest_path)
        witness = verify_cho_selected_manifest_files(
            project_root, manifest_path, manifest_sha256=publication.manifest_sha256,
            evidence_sha256=claim.evidence_sha256,
            selection_contract_sha256=claim.contract_sha256,
            selected_candidate=claim.selected_candidate,
            protocol_config_sha256=pin.identity.protocol_sha256,
            expected_source=expected_source,
            model_recipe_sha256=publication.model_recipe_sha256,
            model_state_sha256=pin.identity.checkpoint_sha256,
        )
        if (
            type(witness) is not ChoSelectedManifestWitness
            or witness.project_root != project_root or witness.manifest_path != manifest_path
            or witness.manifest_sha256 != publication.manifest_sha256
        ):
            raise ValueError("publication byte witness differs from the requested manifest")
        require_digest(witness.weights_sha256, "verified publication weights")
        witnesses.append(witness)
        bindings.append(Cho51PublicationBinding(
            claim.case_id, publication.manifest_sha256, manifest_path,
            claim.evidence_sha256, claim.contract_sha256, claim.selected_candidate,
            pin.identity.protocol_sha256, methods[pin.plan.method],
            publication.environment_sha256, publication.model_recipe_sha256,
            pin.identity.checkpoint_sha256, witness.weights_sha256,
        ))
    selection.verify_stable()
    for witness in witnesses:
        witness.verify_stable()
    final_rows = ledger_rows()
    selection.verify_stable()
    for witness in witnesses:
        witness.verify_stable()
    return Cho51PublicationCollection(
        final_rows, selection.claims, tuple(bindings),
        collected.owner_decision_sha256, selection_ceiling_config_sha256,
    )
