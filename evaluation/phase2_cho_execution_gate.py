"""Pre-claim Cho case gate for persisted selector evidence and live adapters.

This check binds an engineering selector record to its proposed method roster
and the model about to predict. It does not admit compute or freeze the study.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from adaptation.labram_lora_trained import LoRASourceSettings, validate_trained_lora
from core.config import config_snapshot
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_cell_aggregation_bridge import _canonical_record
from evaluation.phase2_cho_method_template import derive_cho_method_template
from evaluation.phase2_factored_evidence import MAXIMUM_LOGICAL_BYTES
from evaluation.phase2_pilot import (
    AnchorAdapter,
    CaseAdapter,
    LaBraMTunedAdapter,
    TrainedLaBraMAdapter,
)
from evaluation.phase2_protocol import TrialCatalog
from evaluation.phase2_records import CellIdentity, verify_envelope
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_selected_source_store import SelectedSourceStore
from evaluation.phase2_selection_evidence_binding import (
    VerifiedChoSelection,
    verify_cho_selection_evidence,
)

CHO_FIRST_TRANCHE = frozenset({"labram_linear", "labram_lora", "labram_full", "eegnet"})


def _persisted_record(
    root: Path, evidence_path: Path, expected_evidence_sha256: str,
) -> dict[str, Any]:
    allowed = (root / "runs/phase2").resolve()
    path = evidence_path.resolve()
    if (
        path == allowed or not path.is_relative_to(allowed)
        or evidence_path.is_symlink() or not path.is_file()
    ):
        raise ValueError("selection evidence must be a persisted file in runs/phase2")
    if path.name.endswith(".factored.json"):
        store = SelectedSourceStore(root, directory=path.parent.parent)
        return store.read_persisted_evidence(
            path, expected_evidence_sha256=expected_evidence_sha256,
        )
    record, _ = _canonical_record(path, maximum_bytes=MAXIMUM_LOGICAL_BYTES)
    payload = record.get("payload")
    if not isinstance(payload, Mapping) or not verify_envelope(
        record, kind="engineering_smoke", expected_payload=payload
    ) or record.get("sha256") != expected_evidence_sha256:
        raise ValueError("selection evidence envelope no longer verifies")
    return record


def _candidate(record: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("selection evidence payload is missing")
    contract = payload.get("contract")
    if not isinstance(contract, Mapping):
        raise ValueError("selection evidence contract is missing")
    candidates = contract.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("selection candidate roster is missing")
    winner = payload.get("selected_candidate")
    selected = [
        row for row in candidates
        if isinstance(row, Mapping) and row.get("name") == winner
    ]
    if len(selected) != 1:
        raise ValueError("selection winner is absent or duplicated")
    return contract, selected[0]


def _adapter_settings(
    adapter: CaseAdapter, plan: CasePlan, candidate: Mapping[str, Any]
) -> tuple[str, Mapping[str, Any], Mapping[str, Any]]:
    source = candidate.get("source")
    if not isinstance(source, Mapping):
        raise ValueError("selected source settings are missing")
    if plan.method in {"labram_linear", "labram_full"}:
        if type(adapter) is not LaBraMTunedAdapter or adapter.method != plan.method:
            raise ValueError("planned plain LaBraM adapter differs")
        model_sha256, support = state_digest(adapter._model), asdict(adapter._support)
    elif plan.method == "labram_lora":
        if type(adapter) is not TrainedLaBraMAdapter or adapter.method != plan.method:
            raise ValueError("planned LoRA adapter differs")
        model_sha256, support = state_digest(adapter._model), asdict(adapter._support)
        if config_snapshot(asdict(adapter._source_settings)) != config_snapshot(source):
            raise ValueError("LoRA adapter source settings differ from the selected candidate")
        validate_trained_lora(
            cast(LaBraMClassifier, adapter._model),
            cast(LoRASourceSettings, adapter._source_settings),
        )
    else:
        if type(adapter) is not AnchorAdapter or adapter.method != "eegnet":
            raise ValueError("planned EEGNet adapter differs")
        if adapter._model is None:
            raise ValueError("EEGNet fitted source model is missing")
        model_sha256, support = state_digest(adapter._model), asdict(adapter._settings)
    return model_sha256, source, support


def _method_config(
    plan: CasePlan,
    method_config: Mapping[str, Any],
    contract: Mapping[str, Any],
    assets: Mapping[str, Any],
) -> None:
    expected = derive_cho_method_template(plan, contract, assets)
    if config_snapshot(method_config) != config_snapshot(expected):
        raise ValueError("method configuration differs from selector and live inputs")


def verify_cho_case_preclaim(
    *,
    root: Path,
    plan: CasePlan,
    adapter: CaseAdapter,
    identity: CellIdentity,
    method_config: Mapping[str, Any],
    evidence_path: Path,
    evidence_sha256: str,
    protocol_config: Mapping[str, Any],
    catalogs: tuple[TrialCatalog, ...],
    selection_record: Mapping[str, Any],
    assets: Mapping[str, Any],
) -> VerifiedChoSelection:
    """Refuse incomplete/mismatched Cho evidence before claiming target work."""
    if plan.dataset != "cho2017" or plan.method not in CHO_FIRST_TRANCHE:
        raise ValueError("this gate covers the selected Cho four-method tranche")
    root = root.resolve()
    record = _persisted_record(root, evidence_path, evidence_sha256)
    contract, candidate = _candidate(record)
    model_sha256, source, support = _adapter_settings(adapter, plan, candidate)
    if identity.checkpoint_sha256 != model_sha256:
        raise ValueError("cell checkpoint differs from the fitted adapter model")
    _method_config(plan, method_config, contract, assets)
    return verify_cho_selection_evidence(
        record=record,
        evidence_sha256=evidence_sha256,
        plan=plan,
        protocol_config=protocol_config,
        catalogs=catalogs,
        selection_record=selection_record,
        assets=assets,
        root=root,
        adapter_model_state_sha256=model_sha256,
        adapter_source_settings=source,
        adapter_support_settings=support,
    )


def verify_cho_adapter_posttarget(
    *, plan: CasePlan, adapter: CaseAdapter, identity: CellIdentity,
    evidence_record: Mapping[str, Any],
) -> None:
    """Recheck the live selected source after target adaptation and prediction."""
    _, candidate = _candidate(evidence_record)
    model_sha256, source, support = _adapter_settings(adapter, plan, candidate)
    if model_sha256 != identity.checkpoint_sha256:
        raise ValueError("selected source model changed during Cho target work")
    if (
        config_snapshot(source) != config_snapshot(candidate["source"])
        or config_snapshot(support) != config_snapshot(candidate["support"])
    ):
        raise ValueError("selected source adapter settings changed during Cho target work")
