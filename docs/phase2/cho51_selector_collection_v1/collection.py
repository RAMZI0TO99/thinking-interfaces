"""Compose complete selector-record consistency with adopted tensor receipts.

The unchanged public selector verifier checks the complete recorded work and
its declared budget. Matching records and tensor receipts do not establish
that historical gradient work occurred or admit a scientific result.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from core.config import config_digest
from core.provenance import SourceProvenance
from docs.phase2.cho51_publication_collection_v1.collection import (
    Cho51PublicationBinding, Cho51PublicationCollection,
)
from docs.phase2.cho51_selection_files_v1.selection_files import (
    ADOPTED_SELECTION_CEILING, Cho51SelectionCeilingWitness, load_selection_ceiling,
)
from docs.phase2.cho51_tensor_collection_v1.collection import (
    Cho51TensorCollection, Cho51TensorReceiptBinding, Cho51TensorReceiptPin,
    collect_cho51_tensor_receipts,
)
from docs.phase2.cho51_tensor_verification_v1.contract import Cho51TensorRequest
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute
from evaluation.phase2_cho_method_template import derive_cho_method_template
from evaluation.phase2_cho_selected_manifest_bridge import (
    ChoSelectedManifestWitness, verify_cho_selected_manifest_files,
)
from evaluation.phase2_cho_selection_file_bridge import ChoSelectionFileClaim
from evaluation.phase2_protocol import TrialCatalog
from evaluation.phase2_runner import method_configuration
from evaluation.phase2_selected_source_store import SelectedSourceStore
from evaluation.phase2_selection_evidence_binding import (
    VerifiedChoSelection, verify_cho_selection_evidence,
)
from evaluation.phase2_subject_aggregation import ScoreRow


@dataclass(frozen=True, slots=True)
class Cho51SelectorClaim:
    """One public verifier's result bound to the independent publication pins."""

    case_id: str
    selected_candidate: str
    evidence_sha256: str
    selection_contract_sha256: str
    model_state_sha256: str
    method_config_sha256: str


@dataclass(frozen=True, slots=True)
class Cho51SelectorCollection:
    rows: tuple[ScoreRow, ...]
    selection_claims: tuple[ChoSelectionFileClaim, ...]
    publications: tuple[Cho51PublicationBinding, ...]
    receipts: tuple[Cho51TensorReceiptBinding, ...]
    selector_claims: tuple[Cho51SelectorClaim, ...]
    owner_decision_sha256: str
    selection_ceiling_config_sha256: str

    @property
    def full_selector_record_consistency_verified(self) -> bool:
        return True

    @property
    def complete_tensor_receipt_roster_verified(self) -> bool:
        return True

    @property
    def native_supervision_verified(self) -> bool:
        return True

    @property
    def full_selector_training_history_verified(self) -> bool:
        return False

    @property
    def full_selector_evidence_verified(self) -> bool:
        return False

    @property
    def paired_analysis_verified(self) -> bool:
        return False

    @property
    def selected_publications_verified(self) -> bool:
        return False

    @property
    def selection_publication_tensor_verified(self) -> bool:
        return False

    @property
    def scientific_result_admitted(self) -> bool:
        return False


def _verify_selector_case(
    project_root: Path,
    route: Cho51WorkerRoute,
    request: Cho51TensorRequest,
    *,
    expected_source: SourceProvenance,
) -> tuple[Cho51SelectorClaim, ChoSelectedManifestWitness]:
    """Verify one record and retain its physical witness; no native proof here.

    The complete collector establishes the exact adopted request roster and
    native tensor proofs before calling this helper. A direct helper call is
    useful for bounded record tests but cannot authenticate tensor execution.
    """
    if type(route) is not Cho51WorkerRoute or type(request) is not Cho51TensorRequest:
        raise ValueError("exact adopted route and tensor request required")
    if (
        request.project_root != project_root or request.expected_source != expected_source
        or request.plan not in route.plans
        or request.protocol_config_json != route.protocol_config_json
    ):
        raise ValueError("selector request differs from project, source or adopted route")
    plan, publication = request.plan, request.publication
    witness = verify_cho_selected_manifest_files(
        project_root, publication.manifest_path,
        manifest_sha256=publication.manifest_sha256,
        evidence_sha256=publication.evidence_sha256,
        selection_contract_sha256=publication.selection_contract_sha256,
        selected_candidate=publication.selected_candidate,
        protocol_config_sha256=publication.protocol_config_sha256,
        expected_source=expected_source,
        model_recipe_sha256=publication.model_recipe_sha256,
        model_state_sha256=publication.model_state_sha256,
    )
    if (
        type(witness) is not ChoSelectedManifestWitness
        or witness.project_root != project_root
        or witness.manifest_path != publication.manifest_path
        or witness.manifest_sha256 != publication.manifest_sha256
        or witness.weights_sha256 != publication.weights_sha256
    ):
        raise ValueError("selector manifest witness differs from the independent publication")
    record, evidence_path = SelectedSourceStore(project_root).read_persisted_evidence_for_manifest(
        publication.manifest_sha256, publication.evidence_sha256,
    )
    if evidence_path != witness.evidence_path:
        raise ValueError("resolved selector evidence path differs from manifest byte witness")
    if not isinstance(record, Mapping) or not isinstance(record.get("payload"), Mapping):
        raise ValueError("persisted selector evidence requires an object payload")
    payload = record["payload"]
    contract = payload.get("contract")
    if not isinstance(contract, Mapping):
        raise ValueError("persisted selector contract must be a mapping")
    if (
        payload.get("contract_sha256") != publication.selection_contract_sha256
        or config_digest(contract) != publication.selection_contract_sha256
        or payload.get("selected_candidate") != publication.selected_candidate
        or type(contract.get("maximum_gradient_steps")) is not int
        or not 1 <= contract["maximum_gradient_steps"] <= ADOPTED_SELECTION_CEILING
    ):
        raise ValueError("selector contract, candidate or budget differs from publication pins")
    assets = {} if plan.method == "eegnet" else route.labram_assets
    template = derive_cho_method_template(plan, contract, assets)
    derived_digest = method_configuration(template)
    if (
        derived_digest != publication.method_config_sha256
        or derived_digest != route.contract.method_config_sha256[plan.method]
        or config_digest(json.loads(request.method_config_json)) != derived_digest
    ):
        raise ValueError("selector candidate settings differ from reviewed method configuration")
    candidates = contract.get("candidates")
    if not isinstance(candidates, list) or any(not isinstance(c, Mapping) for c in candidates):
        raise ValueError("selector candidates must be a recorded list of mappings")
    selected = [c for c in candidates if c.get("name") == publication.selected_candidate]
    if (
        len(selected) != 1 or not isinstance(selected[0].get("source"), Mapping)
        or not isinstance(selected[0].get("support"), Mapping)
    ):
        raise ValueError("selected candidate must have unique recorded source/support settings")
    protocol = json.loads(request.protocol_config_json)
    if (
        not isinstance(protocol, dict)
        or config_digest(protocol) != publication.protocol_config_sha256
    ):
        raise ValueError("selector protocol differs from independent request publication pin")
    selection_record = json.loads(route._full_route.selection_records_json[plan.target_subject])
    if not isinstance(selection_record, dict):
        raise ValueError("adopted source-selection record must be a JSON object")
    verified = verify_cho_selection_evidence(
        record=record, evidence_sha256=publication.evidence_sha256, plan=plan,
        protocol_config=protocol, catalogs=route.catalogs,
        selection_record=selection_record, assets=assets, root=project_root,
        adapter_model_state_sha256=publication.model_state_sha256,
        adapter_source_settings=selected[0]["source"],
        adapter_support_settings=selected[0]["support"],
    )
    if (
        type(verified) is not VerifiedChoSelection
        or verified.selected_candidate != publication.selected_candidate
        or verified.evidence_sha256 != publication.evidence_sha256
    ):
        raise ValueError("public selector verification differs from publication evidence or winner")
    return Cho51SelectorClaim(
        plan.case_id, verified.selected_candidate, verified.evidence_sha256,
        publication.selection_contract_sha256, publication.model_state_sha256,
        derived_digest,
    ), witness


def _bind_tensor_result(
    result: Cho51TensorCollection,
    publication: Cho51PublicationCollection,
    pins: tuple[Cho51TensorReceiptPin, ...],
) -> None:
    if (
        type(result) is not Cho51TensorCollection
        or result.rows != publication.rows
        or result.selection_claims != publication.selection_claims
        or result.publications != publication.publications
        or result.owner_decision_sha256 != publication.owner_decision_sha256
        or result.selection_ceiling_config_sha256 != publication.selection_ceiling_config_sha256
        or type(result.receipts) is not tuple or len(result.receipts) != 1020
        or any(type(receipt) is not Cho51TensorReceiptBinding for receipt in result.receipts)
        or {receipt.case_id for receipt in result.receipts} != {pin.case_id for pin in pins}
    ):
        raise ValueError("tensor receipt collection differs from the same complete publication roster")
    by_case = {pin.case_id: pin for pin in pins}
    for receipt in result.receipts:
        pin = by_case[receipt.case_id]
        if (
            any(getattr(receipt, name) != getattr(pin, name) for name in (
                "case_id", "request_sha256", "bundle_sha256", "bundle_path",
                "native_directory", "native_receipt_file_sha256", "witness_file_sha256",
            ))
            or type(receipt.peak_process_bytes) is not int or receipt.peak_process_bytes < 1
            or type(receipt.peak_job_bytes) is not int
            or receipt.peak_job_bytes < receipt.peak_process_bytes
        ):
            raise ValueError("tensor receipt binding differs from independent execution pin")


def collect_cho51_selector_evidence(
    project_root: Path,
    route: Cho51WorkerRoute,
    publication_collection: Cho51PublicationCollection,
    requests: Sequence[Cho51TensorRequest],
    receipt_pins: Sequence[Cho51TensorReceiptPin],
    *,
    expected_source: SourceProvenance,
) -> Cho51SelectorCollection:
    """Check complete recorded selectors, bracketed by full native proof checks.

    Snapshots precede dependency calls. The tensor collector first validates
    all 1,020 plans, publications, requests and independent receipt pins before
    its physical reads. All 52 source catalogs remain available. The public
    verifier checks every recorded candidate/source fold, deterministic work,
    rational winner and complete declared budget against the pinned 5,253-step
    ceiling. Stable rereads detect changes; they do not provide a file lock.
    """
    if (
        not isinstance(requests, Sequence) or isinstance(requests, (str, bytes))
        or not isinstance(receipt_pins, Sequence) or isinstance(receipt_pins, (str, bytes))
    ):
        raise ValueError("request and independent receipt-pin sequences required")
    requested, pinned = tuple(requests), tuple(receipt_pins)
    if (
        type(route) is not Cho51WorkerRoute
        or type(publication_collection) is not Cho51PublicationCollection
        or len(requested) != 1020 or any(type(r) is not Cho51TensorRequest for r in requested)
        or len({r.plan.case_id for r in requested}) != 1020
        or len(pinned) != 1020 or any(type(p) is not Cho51TensorReceiptPin for p in pinned)
        or len({p.case_id for p in pinned}) != 1020
    ):
        raise ValueError("exact adopted route, publication and distinct 1,020 request/pin rosters required")
    if (
        type(route.catalogs) is not tuple or len(route.catalogs) != 52
        or any(type(catalog) is not TrialCatalog for catalog in route.catalogs)
        or {catalog.subject for catalog in route.catalogs}
        != {f"subject_{subject:02d}" for subject in range(1, 53)}
    ):
        raise ValueError("complete typed 52-subject source catalog pool required")
    before = collect_cho51_tensor_receipts(
        project_root, route, publication_collection, requested, pinned,
        expected_source=expected_source,
    )
    _bind_tensor_result(before, publication_collection, pinned)
    ceiling = load_selection_ceiling(
        project_root, expected_sha256=publication_collection.selection_ceiling_config_sha256,
    )
    if (
        type(ceiling) is not Cho51SelectionCeilingWitness
        or ceiling.path != project_root / "configs/phase2/selection_ceiling.toml"
        or ceiling.expected_sha256 != publication_collection.selection_ceiling_config_sha256
        or ceiling.maximum_gradient_steps != ADOPTED_SELECTION_CEILING
    ):
        raise ValueError("selector ceiling witness differs from the independent 5,253 policy pin")
    ceiling.verify_stable()
    by_case = {request.plan.case_id: request for request in requested}
    claims: list[Cho51SelectorClaim] = []
    witnesses: list[ChoSelectedManifestWitness] = []
    for plan in route.plans:
        claim, witness = _verify_selector_case(
            project_root, route, by_case[plan.case_id], expected_source=expected_source,
        )
        claims.append(claim)
        witnesses.append(witness)
    ceiling.verify_stable()
    for witness in witnesses:
        witness.verify_stable()
    after = collect_cho51_tensor_receipts(
        project_root, route, publication_collection, requested, pinned,
        expected_source=expected_source,
    )
    _bind_tensor_result(after, publication_collection, pinned)
    if after != before:
        raise ValueError("native tensor proof roster changed across full selector verification")
    for witness in witnesses:
        witness.verify_stable()
    ceiling.verify_stable()
    return Cho51SelectorCollection(
        after.rows, after.selection_claims, after.publications, after.receipts,
        tuple(claims), after.owner_decision_sha256, after.selection_ceiling_config_sha256,
    )
