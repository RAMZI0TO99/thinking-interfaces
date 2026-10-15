"""Compose adopted-51 recorder/real-input and selection-file checks read-only.

This returns intermediate engineering evidence only. No paired aggregation,
selected-state publication, tensor restore or numerical selector is performed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from core.provenance import SourceProvenance
from docs.phase2.cho51_recorder_collection_v1.collector import (
    Cho51RecorderCollection,
    collect_recorder_rows,
)
from docs.phase2.cho51_selection_files_v1.selection_files import (
    Cho51SelectionFileWitness,
    verify_cho51_recorded_selection_files,
)
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell, verified_score_rows
from evaluation.phase2_cho_case_inputs import ChoCaseInputPins
from evaluation.phase2_cho_selection_file_bridge import ChoSelectionFileClaim
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_runner import CaseRecorder
from evaluation.phase2_subject_aggregation import ScoreRow


@dataclass(frozen=True, slots=True)
class Cho51InputCollection:
    """Immutable intermediate rows and claims, with no scientific admission."""

    rows: tuple[ScoreRow, ...]
    selection_claims: tuple[ChoSelectionFileClaim, ...]
    owner_decision_sha256: str
    selection_ceiling_config_sha256: str

    @property
    def selected_publications_verified(self) -> bool:
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


def _bind_rows(rows: tuple[ScoreRow, ...], pins: tuple[PinnedCaseCell, ...]) -> None:
    expected = {pin.key: pin.cell_sha256 for pin in pins}
    if (
        type(rows) is not tuple
        or len(rows) != len(pins)
        or any(type(row) is not ScoreRow for row in rows)
        or len({row.key for row in rows}) != len(pins)
        or {row.key: row.cell_sha256 for row in rows} != expected
    ):
        raise ValueError("recorder rows differ from the same complete external pins")


def _bind_claims(
    claims: tuple[ChoSelectionFileClaim, ...], pins: tuple[PinnedCaseCell, ...],
) -> None:
    expected = {pin.plan.case_id: pin.selection_evidence_sha256 for pin in pins}
    if (
        type(claims) is not tuple
        or len(claims) != len(pins)
        or any(type(claim) is not ChoSelectionFileClaim for claim in claims)
        or len({claim.case_id for claim in claims}) != len(pins)
        or {claim.case_id: claim.evidence_sha256 for claim in claims} != expected
    ):
        raise ValueError("selection claims differ from the same complete external pins")


def collect_cho51_input_selection(
    project_root: Path,
    route: Cho51WorkerRoute,
    recorder: CaseRecorder,
    pins: Sequence[PinnedCaseCell],
    *,
    case_input_pins: ChoCaseInputPins,
    base_config_sha256: str,
    method_config_sha256: Mapping[str, str],
    expected_source: SourceProvenance,
    selection_ceiling_config_sha256: str,
) -> Cho51InputCollection:
    """Verify the same 1,020 external pins across the two qualified stages.

    The recorder stage freshly rederives all 52 real source inputs and retains
    subjects 02-52 as the 51 targets. The selection stage checks persisted file
    claims using the independently pinned 5,253 ceiling. Both consume the same
    immutable snapshots. Final recorder reread and selection-witness rechecks
    cover the composition interval; they do not provide a filesystem lock.

    A caller must supply an already existing recorder and independent pins.
    This function never constructs a recorder, starts an attempt or writes data.
    """
    if (
        not isinstance(pins, Sequence) or isinstance(pins, (str, bytes))
        or not isinstance(method_config_sha256, Mapping)
    ):
        raise ValueError("complete independent pins and method mapping required")
    pinned = tuple(pins)
    methods = MappingProxyType(dict(method_config_sha256))
    if (
        len(pinned) != 1020 or any(type(pin) is not PinnedCaseCell for pin in pinned)
        or len({pin.plan.case_id for pin in pinned}) != 1020
        or len({pin.key for pin in pinned}) != 1020
    ):
        raise ValueError("exact 1,020 distinct typed external case pins required")
    require_digest(selection_ceiling_config_sha256, "independent selection ceiling")
    collected = collect_recorder_rows(
        project_root, route, recorder, pinned,
        case_input_pins=case_input_pins,
        base_config_sha256=base_config_sha256,
        method_config_sha256=methods,
        expected_source=expected_source,
    )
    if (
        type(collected) is not Cho51RecorderCollection
        or collected.owner_decision_sha256 != route.contract.owner_decision_sha256
    ):
        raise ValueError("recorder collection differs from adopted owner decision")
    _bind_rows(collected.rows, pinned)
    selection = verify_cho51_recorded_selection_files(
        route, recorder, pinned, project_root=project_root,
        expected_source=expected_source,
        method_config_sha256=methods,
        selection_ceiling_config_sha256=selection_ceiling_config_sha256,
    )
    if (
        type(selection) is not Cho51SelectionFileWitness
        or selection.owner_decision_sha256 != collected.owner_decision_sha256
        or selection.ceiling.expected_sha256 != selection_ceiling_config_sha256
    ):
        raise ValueError("selection witness differs from the same owner or ceiling pin")
    _bind_claims(selection.claims, pinned)
    selection.verify_stable()
    # Re-read the exact ledger and success receipts after selection inspection.
    # No second real-input load or score aggregation is needed for this check.
    final_rows = verified_score_rows(recorder, tuple(pin.key for pin in pinned), pinned)
    _bind_rows(final_rows, pinned)
    if final_rows != collected.rows:
        raise ValueError("recorder rows changed during input/selection collection")
    selection.verify_stable()
    return Cho51InputCollection(
        final_rows, selection.claims, collected.owner_decision_sha256,
        selection_ceiling_config_sha256,
    )
