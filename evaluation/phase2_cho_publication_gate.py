"""Persist a preclaim-verified Cho source before any target prediction.

This is an engineering snapshot. The store's existing disk guard and write-once
manifest policy apply; publication does not admit a scientific cell or fit.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from torch import nn

from core.config import config_digest
from core.provenance import capture_source
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_execution_gate import _persisted_record
from evaluation.phase2_cho_selected_manifest_bridge import (
    ChoSelectedManifestWitness,
    verify_cho_selected_manifest_files,
)
from evaluation.phase2_cho_source_restore import prepare_cho_source_restore
from evaluation.phase2_pilot import (
    AnchorAdapter,
    CaseAdapter,
    LaBraMTunedAdapter,
    TrainedLaBraMAdapter,
)
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import CellIdentity
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_selected_source_store import (
    SelectedEvidenceFormat,
    SelectedSourcePublication,
    SelectedSourceStore,
)
from evaluation.phase2_selection_evidence_binding import VerifiedChoSelection


@dataclass(frozen=True, slots=True)
class VerifiedChoSourcePublication:
    """A published snapshot and its independently checked physical-file witness."""

    publication: SelectedSourcePublication
    witness: ChoSelectedManifestWitness


def _selected_model(adapter: CaseAdapter, method: str) -> nn.Module:
    """Accept only the live source model shape checked by the Cho preclaim gate."""
    model: Any
    if method in {"labram_linear", "labram_full"}:
        if type(adapter) is not LaBraMTunedAdapter or adapter.method != method:
            raise ValueError("Cho plain source adapter differs before publication")
        model = adapter._model
    elif method == "labram_lora":
        if type(adapter) is not TrainedLaBraMAdapter or adapter.method != method:
            raise ValueError("Cho LoRA source adapter differs before publication")
        model = adapter._model
    elif method == "eegnet":
        if type(adapter) is not AnchorAdapter or adapter.method != method:
            raise ValueError("Cho EEGNet source adapter differs before publication")
        model = adapter._model
    else:
        raise ValueError("Cho selected source publication method differs")
    if not isinstance(model, nn.Module):
        raise ValueError("Cho selected fitted source model is missing")
    return model


def _require_selected_model_class(
    model: nn.Module, method: str, recipe: Mapping[str, Any],
) -> None:
    """Match the live architecture family and key independent recipe claims."""
    architecture = recipe.get("architecture")
    if not isinstance(architecture, Mapping):
        raise ValueError("Cho fitted source model architecture recipe is missing")
    if method == "eegnet":
        from braindecode.models import EEGNet  # type: ignore[import-untyped]
        from braindecode.modules import LinearWithConstraint  # type: ignore[import-untyped]

        final_layer = model.final_layer if type(model) is EEGNet else None
        if (
            type(model) is not EEGNet
            or model.n_chans != architecture.get("n_chans")
            or model.n_outputs != architecture.get("n_outputs")
            or model.n_times != architecture.get("n_times")
            or model.sfreq != architecture.get("sfreq")
            or architecture.get("final_layer_with_constraint") is not True
            or not isinstance(final_layer, nn.Sequential)
            or not isinstance(
                final_layer._modules.get("linearconstraint"), LinearWithConstraint
            )
            or "conv_classifier" in final_layer._modules
        ):
            raise ValueError("Cho EEGNet fitted source model class differs")
    elif method in {"labram_linear", "labram_lora", "labram_full"}:
        if (
            type(model) is not LaBraMClassifier
            or model.channel_names != tuple(architecture.get("channel_names", ()))
            or type(model.head) is not nn.Linear
            or model.head.out_features != architecture.get("classes")
        ):
            raise ValueError("Cho LaBraM fitted source model class differs")
    else:
        raise ValueError("Cho fitted source model method differs")


def publish_verified_cho_source(
    *, root: Path, plan: CasePlan, adapter: CaseAdapter,
    identity: CellIdentity, method_config: Mapping[str, Any],
    protocol_config: Mapping[str, Any], evidence_path: Path,
    selection: VerifiedChoSelection,
) -> VerifiedChoSourcePublication:
    """Publish one verified live source, with an independently derived recipe."""
    root = root.resolve()
    if identity.method != plan.method or identity.dataset != "cho2017":
        raise ValueError("Cho selected source identity differs from the plan")
    model = _selected_model(adapter, plan.method)
    model_sha256 = state_digest(model)
    if model_sha256 != identity.checkpoint_sha256:
        raise ValueError("Cho fitted source state differs before publication")
    source = capture_source(root)
    if (
        source.source_sha256 != identity.source_sha256
        or source.git_commit != identity.git_commit
        or source.git_dirty != identity.git_dirty
        or config_digest(protocol_config) != identity.protocol_sha256
    ):
        raise ValueError("Cho source or protocol differs before publication")
    prepared = prepare_cho_source_restore(
        root=root, plan=plan, method_config=method_config,
        expected_method_config_sha256=identity.method_config_sha256,
        selected_candidate=selection.selected_candidate,
    )
    _require_selected_model_class(model, plan.method, prepared.model_recipe)
    record = _persisted_record(root, evidence_path, selection.evidence_sha256)
    payload = record.get("payload")
    contract = payload.get("contract") if isinstance(payload, Mapping) else None
    if (
        not isinstance(payload, Mapping)
        or not isinstance(contract, Mapping)
        or any(not isinstance(key, str) for key in contract)
        or payload.get("contract_sha256") != config_digest(contract)
        or contract.get("source") != asdict(source)
        or payload.get("selected_candidate") != selection.selected_candidate
        or record.get("sha256") != selection.evidence_sha256
    ):
        raise ValueError("Cho selected evidence changed after preclaim verification")
    evidence_format: SelectedEvidenceFormat = (
        "factored_json_v1" if evidence_path.name.endswith(".factored.json")
        else "canonical_json_v1"
    )
    publication = SelectedSourceStore(root).publish(
        model, record, evidence_sha256=selection.evidence_sha256,
        protocol_config=protocol_config, model_recipe=prepared.model_recipe,
        evidence_format=evidence_format,
    )
    require_digest(publication.manifest_sha256, "Cho selected source manifest")
    expected_manifest = (
        root / "runs/phase2/selected_sources/manifests"
        / f"{publication.manifest_sha256}.json"
    )
    if (
        publication.evidence_sha256 != selection.evidence_sha256
        or publication.selected_candidate != selection.selected_candidate
        or publication.model_state_sha256 != identity.checkpoint_sha256
        or publication.evidence_format != evidence_format
        or publication.weights_format != "full_v1"
        or publication.manifest_path != expected_manifest
        or publication.manifest_path.resolve() != expected_manifest
    ):
        raise ValueError("Cho published source differs from verified preclaim pins")
    witness = verify_cho_selected_manifest_files(
        root, publication.manifest_path,
        manifest_sha256=publication.manifest_sha256,
        evidence_sha256=selection.evidence_sha256,
        selection_contract_sha256=config_digest(contract),
        selected_candidate=selection.selected_candidate,
        protocol_config_sha256=identity.protocol_sha256,
        expected_source=source,
        model_recipe_sha256=config_digest(prepared.model_recipe),
        model_state_sha256=identity.checkpoint_sha256,
    )
    if (
        publication.weights_path != witness.weights_path
        or publication.weights_sha256 != witness.weights_sha256
        or publication.evidence_path != witness.evidence_path
    ):
        raise ValueError("Cho published files differ from verified physical file identities")
    return VerifiedChoSourcePublication(publication, witness)
