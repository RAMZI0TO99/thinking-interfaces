"""Restore a selected Cho source into its exact first-tranche adapter.

The manifest supplies bytes, never an architecture recipe. This factory derives
the recipe from caller-pinned method settings and the audited local baseline,
then requires the complete Cho selector verifier before releasing an adapter.
It performs no fitting, target prediction, or scientific publication.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from adaptation.anchor_manifest import EEGNetAnchorSettings
from adaptation.labram_lora_trained import (
    LoRAContinuationSettings,
    LoRASourceSettings,
    initialize_source_lora,
    validate_trained_lora,
)
from adaptation.labram_manifest import LaBraMTuningSettings
from adaptation.labram_source import LaBraMSourceSettings
from adaptation.labram_tuning import configure_labram_tuning
from adaptation.source_selection import EEGNetSourceSettings
from core.config import config_digest, config_snapshot, load_toml
from core.provenance import capture_source
from encoder.labram import LaBraMClassifier, configure_pretrained_sequence
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_case_inputs import CHO_SUBJECTS
from evaluation.phase2_cho_execution_gate import _method_config
from evaluation.phase2_pilot import AnchorAdapter, LaBraMTunedAdapter, TrainedLaBraMAdapter
from evaluation.phase2_profile_binding import CHO_CHANNELS, CHO_CLASSES
from evaluation.phase2_protocol import TrialCatalog, require_digest
from evaluation.phase2_runner import CasePlan, method_configuration
from evaluation.phase2_selected_source_store import (
    RestoredSelectedSource,
    SelectedSourceStore,
    _read_bounded_regular,
)
from evaluation.phase2_selection_evidence_binding import (
    VerifiedChoSelection,
    verify_cho_selection_evidence,
)
from scripts.audit_phase2_protocol import file_digest

_FORWARD_PARITY = "configs/phase2/forward_parity.toml"
_CHECKPOINT_CONFIG = "configs/labram_checkpoint_audit.toml"
_MAXIMUM_LABRAM_WEIGHTS_BYTES = 64 * 1024**2
_MAXIMUM_LABRAM_CONFIG_BYTES = 1 * 1024**2
_MAXIMUM_EEGNET_WEIGHTS_BYTES = 1 * 1024**2

type SourceSettings = LaBraMSourceSettings | LoRASourceSettings | EEGNetSourceSettings
type SupportSettings = LaBraMTuningSettings | LoRAContinuationSettings | EEGNetAnchorSettings
type ChoSelectedAdapter = LaBraMTunedAdapter | TrainedLaBraMAdapter | AnchorAdapter


@dataclass(frozen=True, slots=True)
class ChoSourceRestorePreparation:
    """Caller-owned architecture declaration; no checkpoint has been restored."""

    plan: CasePlan
    selected_candidate: str
    model_recipe: dict[str, Any]
    source_settings: SourceSettings
    support_settings: SupportSettings
    model_config_path: Path | None
    baseline_weights_path: Path | None


@dataclass(frozen=True, slots=True)
class VerifiedRestoredChoSource:
    """An adapter released only after store and full selector evidence verification."""

    adapter: ChoSelectedAdapter
    restored: RestoredSelectedSource
    selection: VerifiedChoSelection
    model_recipe: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ChoSelectedSourceStateWitness:
    """Digest-only witness for one restored selected source, without an adapter."""

    manifest_sha256: str
    evidence_sha256: str
    selected_candidate: str
    model_recipe_sha256: str
    model_state_sha256: str
    weights_sha256: str


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed mapping")
    return value


def _pre_restore_evidence(
    store: SelectedSourceStore, manifest_sha256: str, evidence_sha256: str,
) -> tuple[dict[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    """Read the pinned selection claim before any selected weights enter a model.

    The store repeats full byte and context verification during restore. Requiring
    the same record after that read closes a concurrent replacement of this file.
    """
    require_digest(manifest_sha256, "selected source manifest")
    require_digest(evidence_sha256, "selection evidence")
    record, _ = store.read_persisted_evidence_for_manifest(
        manifest_sha256, evidence_sha256,
    )
    payload = _mapping(record.get("payload"), "selection evidence payload")
    contract = _mapping(payload.get("contract"), "selection contract")
    final_fit = _mapping(payload.get("final_source_fit"), "final source fit")
    if (
        record.get("sha256") != evidence_sha256
        or payload.get("contract_sha256") != config_digest(contract)
    ):
        raise ValueError("pinned selection evidence integrity differs")
    return record, contract, final_fit


def _runtime_dependencies(contract: Mapping[str, Any]) -> None:
    """Validate source runtime metadata and exact constructor dependencies.

    Source device and thread count describe the fit; a target restore may run
    on CPU after a CUDA source fit, so they are schema-checked, not matched.
    """
    runtime = _mapping(contract.get("runtime"), "source selection runtime")
    base = {
        "python", "torch", "numpy", "braindecode", "device", "dtype",
        "torch_threads", "deterministic_algorithms",
    }
    cuda = {
        "cuda", "cudnn", "gpu_name", "gpu_capability", "matmul_tf32",
        "cudnn_tf32", "cudnn_benchmark", "cudnn_deterministic",
    }
    device = runtime.get("device")
    if (
        device not in {"cpu", "cuda:0"}
        or set(runtime) != base | (cuda if device == "cuda:0" else set())
        or runtime.get("dtype") != "float32"
        or type(runtime.get("torch_threads")) is not int
        or runtime["torch_threads"] < 1
        or type(runtime.get("deterministic_algorithms")) is not bool
    ):
        raise ValueError("source selection runtime schema differs")
    if device == "cuda:0":
        capability = runtime["gpu_capability"]
        if (
            not isinstance(runtime["cuda"], str) or not runtime["cuda"]
            or runtime["cudnn"] is not None and (
                type(runtime["cudnn"]) is not int or runtime["cudnn"] < 1
            )
            or not isinstance(runtime["gpu_name"], str) or not runtime["gpu_name"]
            or not isinstance(capability, list) or len(capability) != 2
            or any(type(value) is not int or value < 0 for value in capability)
            or capability[0] < 1
            or any(type(runtime[name]) is not bool for name in (
                "matmul_tf32", "cudnn_tf32", "cudnn_benchmark", "cudnn_deterministic",
            ))
        ):
            raise ValueError("source selection CUDA runtime schema differs")
    current = {
        "python": platform.python_version(),
        "torch": str(torch.__version__),
        "numpy": np.__version__,
        "braindecode": version("braindecode"),
    }
    if any(runtime.get(name) != value for name, value in current.items()):
        raise ValueError("source selection dependency versions differ from the live runtime")


def _check_labram_baseline(prepared: ChoSourceRestorePreparation) -> None:
    """Rehash external baseline files, including at the final release boundary."""
    if prepared.plan.method == "eegnet":
        return
    model_config = prepared.model_config_path
    weights = prepared.baseline_weights_path
    architecture = _mapping(prepared.model_recipe.get("architecture"), "LaBraM recipe")
    if (
        model_config is None or weights is None
        or not model_config.is_file() or model_config.resolve() != model_config
        or not weights.is_file() or weights.resolve() != weights
        or file_digest(model_config) != architecture.get("backbone_config_sha256")
        or file_digest(weights) != architecture.get("baseline_weights_sha256")
    ):
        raise ValueError("pinned LaBraM baseline changed before adapter release")


def _pinned_file(root: Path, relative: str, sha256: str) -> Path:
    require_digest(sha256, "baseline file")
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("baseline file requires a project-relative path")
    lexical = (root / relative).absolute()
    resolved = lexical.resolve()
    if (
        not resolved.is_relative_to(root)
        or resolved != lexical
        or not resolved.is_file()
        or file_digest(resolved) != sha256
    ):
        raise ValueError("pinned baseline file differs or aliases another path")
    return resolved


def _read_pinned_baseline(
    path: Path, expected_sha256: str, maximum_bytes: int,
) -> tuple[bytes, tuple[int, int, int, int]]:
    """Hash bounded bytes from one stable direct file before they reach a decoder."""
    require_digest(expected_sha256, "LaBraM baseline")
    try:
        before = path.stat()
        blob = _read_bounded_regular(path, path.parent, maximum_bytes)
        after = path.stat()
    except (OSError, ValueError) as exc:
        raise ValueError("pinned LaBraM baseline changed or exceeds its byte limit") from exc
    if (
        not os.path.samestat(before, after)
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or hashlib.sha256(blob).hexdigest() != expected_sha256
    ):
        raise ValueError("pinned LaBraM baseline changed during bounded read")
    return blob, (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)


def _labram_baseline(root: Path) -> tuple[dict[str, Any], Path, Path]:
    parity_path = root / _FORWARD_PARITY
    checkpoint_path = root / _CHECKPOINT_CONFIG
    if (
        parity_path.resolve() != parity_path.absolute()
        or checkpoint_path.resolve() != checkpoint_path.absolute()
    ):
        raise ValueError("baseline configuration aliases another path")
    parity = _mapping(load_toml(parity_path).get("parity"), "forward parity baseline")
    if parity["checkpoint_config"] != _CHECKPOINT_CONFIG:
        raise ValueError("forward parity points to another checkpoint declaration")
    checkpoint = _mapping(
        load_toml(checkpoint_path).get("safe_conversion"), "safe baseline checkpoint",
    )
    model_path = _pinned_file(root, str(parity["model_config"]), str(parity["model_config_sha256"]))
    weights_path = _pinned_file(root, str(checkpoint["path"]), str(checkpoint["sha256"]))
    model_bytes, _ = _read_pinned_baseline(
        model_path, str(parity["model_config_sha256"]), _MAXIMUM_LABRAM_CONFIG_BYTES,
    )
    model_settings = json.loads(model_bytes.decode("utf-8"))
    if not isinstance(model_settings, dict) or model_settings.get("n_times") != 3000:
        raise ValueError("pinned LaBraM backbone metadata differs")
    model_settings.pop("braindecode_version", None)
    recipe = {
        "architecture": "braindecode_labram_pretrained_classifier",
        "forward_parity_config_sha256": file_digest(parity_path),
        "checkpoint_config_sha256": file_digest(checkpoint_path),
        "backbone_config_file": str(parity["model_config"]),
        "backbone_config_sha256": str(parity["model_config_sha256"]),
        "baseline_weights_file": str(checkpoint["path"]),
        "baseline_weights_sha256": str(checkpoint["sha256"]),
        "samples": 800,
        "sampling_rate_hz": 200,
        "channel_names": list(CHO_CHANNELS),
        "classes": len(CHO_CLASSES),
    }
    return recipe, model_path, weights_path


def _candidate_settings(
    method: str, candidate: Mapping[str, Any], seed: int,
) -> tuple[SourceSettings, SupportSettings, dict[str, Any]]:
    source: dict[str, Any] = dict(config_snapshot(candidate["source"]))
    support: dict[str, Any] = dict(config_snapshot(candidate["support"]))
    if method == "labram_lora":
        if source.get("seed") != "$case_model_seed":
            raise ValueError("LoRA source seed must be the static case template")
        source["seed"] = seed
        modules = source.get("target_modules")
        if not isinstance(modules, list) or any(not isinstance(name, str) for name in modules):
            raise ValueError("LoRA target modules must be explicit")
        source["target_modules"] = tuple(modules)
        typed_source: SourceSettings = LoRASourceSettings(**source)
        typed_support: SupportSettings = LoRAContinuationSettings(**support)
    elif method in {"labram_linear", "labram_full"}:
        typed_source = LaBraMSourceSettings(**source)
        typed_support = LaBraMTuningSettings(**support)
        tuning = method.removeprefix("labram_")
        if typed_source.method != tuning or typed_support.method != tuning:
            raise ValueError("plain LaBraM settings differ from the planned method")
    else:
        typed_source = EEGNetSourceSettings(**source)
        typed_support = EEGNetAnchorSettings(**support)
        if typed_source.input_scale != typed_support.input_scale:
            raise ValueError("EEGNet source and support scales differ")
    materialized = {
        "name": candidate["name"],
        "source": config_snapshot(asdict(typed_source)),
        "support": config_snapshot(asdict(typed_support)),
    }
    return typed_source, typed_support, materialized


def prepare_cho_source_restore(
    *, root: Path, plan: CasePlan, method_config: Mapping[str, Any],
    expected_method_config_sha256: str, selected_candidate: str,
) -> ChoSourceRestorePreparation:
    """Derive the model recipe without reading any selected-source manifest."""
    root = root.resolve()
    config = config_snapshot(method_config)
    require_digest(expected_method_config_sha256, "method configuration")
    if (
        plan.dataset != "cho2017"
        or plan.method not in {"labram_linear", "labram_lora", "labram_full", "eegnet"}
        or plan.target_subject not in CHO_SUBJECTS
        or plan.shots_per_class != 5
        or plan.repetition != 1
        or plan.model_seed not in {11, 23, 37, 53, 71}
    ):
        raise ValueError("plan is outside the Cho first-tranche scope")
    if (
        method_configuration(config) != expected_method_config_sha256
        or config.get("method") != plan.method
        or config.get("dataset") != plan.dataset
    ):
        raise ValueError("static method configuration differs from its caller pin or plan")
    candidate_rows = config.get("candidates")
    if not isinstance(candidate_rows, list):
        raise ValueError("static candidate roster is missing")
    candidates = [_mapping(row, "static candidate") for row in candidate_rows]
    selected = [
        _mapping(row, "static candidate") for row in candidates
        if isinstance(row, Mapping) and row.get("name") == selected_candidate
    ]
    if len(selected) != 1:
        raise ValueError("selected candidate is absent from the caller-pinned roster")
    source, support, materialized = _candidate_settings(
        plan.method, selected[0], plan.model_seed,
    )
    if plan.method == "eegnet":
        architecture = {
            "architecture": "braindecode_eegnet",
            "n_chans": len(CHO_CHANNELS),
            "n_outputs": len(CHO_CLASSES),
            "n_times": 512,
            "sfreq": 128,
            "final_layer_with_constraint": True,
            "channel_names": list(CHO_CHANNELS),
        }
        model_config_path = baseline_weights_path = None
    else:
        architecture, model_config_path, baseline_weights_path = _labram_baseline(root)
    recipe: dict[str, Any] = {
        "schema": "cho_selected_source_architecture_v1",
        "dataset": "cho2017",
        "method": plan.method,
        "input_profile": config["input_profile"],
        "variant_config_sha256": config["variant_config_sha256"],
        "selected_candidate": selected_candidate,
        "architecture": architecture,
    }
    if plan.method == "labram_lora":
        recipe["lora"] = {
            "target_modules": materialized["source"]["target_modules"],
            "rank": materialized["source"]["rank"],
            "alpha": materialized["source"]["alpha"],
            "seed": materialized["source"]["seed"],
            "train_head": materialized["source"]["train_head"],
        }
    return ChoSourceRestorePreparation(
        plan, selected_candidate, recipe, source, support,
        model_config_path, baseline_weights_path,
    )


def _new_model(
    prepared: ChoSourceRestorePreparation, *,
    contract: Mapping[str, Any] | None = None,
    final_fit: Mapping[str, Any] | None = None,
) -> nn.Module:
    """Rebuild and verify the source lineage before selected weights are loaded."""
    with torch.random.fork_rng(devices=[]):
        if prepared.plan.method == "eegnet":
            from braindecode.models import EEGNet  # type: ignore[import-untyped]

            torch.random.set_rng_state(
                torch.Generator(device="cpu").manual_seed(prepared.plan.model_seed).get_state()
            )
            model: nn.Module = EEGNet(
                n_chans=len(CHO_CHANNELS), n_outputs=len(CHO_CLASSES),
                n_times=512, sfreq=128, final_layer_with_constraint=True,
            ).cpu().float().eval()
            if final_fit is not None and (
                final_fit.get("initial_state_sha256") != state_digest(model)
            ):
                raise ValueError("seeded EEGNet initial state differs from the final source fit")
            return model
        from braindecode.models import Labram
        from safetensors.torch import load

        if prepared.model_config_path is None or prepared.baseline_weights_path is None:
            raise ValueError("pinned LaBraM baseline is missing")
        architecture = prepared.model_recipe["architecture"]
        model_bytes, model_identity = _read_pinned_baseline(
            prepared.model_config_path,
            architecture["backbone_config_sha256"], _MAXIMUM_LABRAM_CONFIG_BYTES,
        )
        weights_bytes, weights_identity = _read_pinned_baseline(
            prepared.baseline_weights_path,
            architecture["baseline_weights_sha256"], _MAXIMUM_LABRAM_WEIGHTS_BYTES,
        )
        settings = json.loads(model_bytes.decode("utf-8"))
        settings.pop("braindecode_version", None)
        backbone = Labram(**settings)
        backbone.load_state_dict(load(weights_bytes), strict=True)
        del weights_bytes
        configure_pretrained_sequence(backbone, samples=800)
        torch.random.set_rng_state(
            torch.Generator(device="cpu").manual_seed(prepared.plan.model_seed).get_state()
        )
        plain = LaBraMClassifier(
            backbone, classes=len(CHO_CLASSES), channel_names=CHO_CHANNELS,
        ).cpu().float().eval()
        _, final_model_identity = _read_pinned_baseline(
            prepared.model_config_path,
            architecture["backbone_config_sha256"], _MAXIMUM_LABRAM_CONFIG_BYTES,
        )
        _, final_weights_identity = _read_pinned_baseline(
            prepared.baseline_weights_path,
            architecture["baseline_weights_sha256"], _MAXIMUM_LABRAM_WEIGHTS_BYTES,
        )
        if model_identity != final_model_identity or weights_identity != final_weights_identity:
            raise ValueError("pinned LaBraM baseline changed during model construction")
        if contract is not None:
            if state_digest(plain) != contract.get("template_state_sha256"):
                raise ValueError("reconstructed LaBraM template differs from selection contract")
            torch.random.set_rng_state(
                torch.Generator(device="cpu").manual_seed(prepared.plan.model_seed).get_state()
            )
            plain.head.reset_parameters()
            if state_digest(plain) != contract.get("initial_state_sha256"):
                raise ValueError("seeded LaBraM initial state differs from selection contract")
        if prepared.plan.method == "labram_lora":
            if not isinstance(prepared.source_settings, LoRASourceSettings):
                raise ValueError("LoRA source settings differ")
            model, _ = initialize_source_lora(plain, prepared.source_settings)
            validate_trained_lora(model, prepared.source_settings)
        else:
            if not isinstance(prepared.source_settings, LaBraMSourceSettings):
                raise ValueError("plain LaBraM source settings differ")
            configure_labram_tuning(plain, method=prepared.source_settings.method)
            model = plain
        if final_fit is not None and final_fit.get("initial_state_sha256") != state_digest(model):
            raise ValueError("LaBraM fit initialization differs from the selected source fit")
        return model


def _available_host_ram_gib() -> float:
    return float(import_module("psutil").virtual_memory().available / 1024**3)


def _require_host_ram(minimum_gib: float) -> None:
    available = _available_host_ram_gib()
    if not math.isfinite(available) or available < minimum_gib:
        raise ValueError(
            f"Cho selected tensor restore requires {minimum_gib:g} GiB available RAM"
        )


def verify_cho_selected_source_state(
    *, root: Path, plan: CasePlan, method_config: Mapping[str, Any],
    expected_method_config_sha256: str, selected_candidate: str,
    manifest_sha256: str, evidence_sha256: str,
    protocol_config: Mapping[str, Any], expected_model_recipe_sha256: str,
    expected_model_state_sha256: str,
    store: SelectedSourceStore | None = None,
) -> ChoSelectedSourceStateWitness:
    """Verify one full_v1 Cho tensor state against independent caller pins.

    This is a read-only analysis check. It cannot release a target adapter or
    establish selector completeness or historical use. Callers must enforce
    their own process lifetime and peak-memory policy for a complete roster.
    """
    root = root.resolve()
    require_digest(expected_model_recipe_sha256, "expected model recipe")
    require_digest(expected_model_state_sha256, "expected model state")
    config = config_snapshot(method_config)
    prepared = prepare_cho_source_restore(
        root=root, plan=plan, method_config=config,
        expected_method_config_sha256=expected_method_config_sha256,
        selected_candidate=selected_candidate,
    )
    recipe_sha256 = config_digest(prepared.model_recipe)
    if recipe_sha256 != expected_model_recipe_sha256:
        raise ValueError("Cho selected model recipe differs from independent pin")
    _require_host_ram(6.0)
    selected_store = store if store is not None else SelectedSourceStore(root)
    if selected_store.root != root:
        raise ValueError("selected source store belongs to another project root")
    maximum_weights_bytes = (
        _MAXIMUM_EEGNET_WEIGHTS_BYTES
        if plan.method == "eegnet" else _MAXIMUM_LABRAM_WEIGHTS_BYTES
    )
    before_weights = selected_store.preflight_full_weights(
        manifest_sha256, maximum_bytes=maximum_weights_bytes,
    )
    prior_record, contract, final_fit = _pre_restore_evidence(
        selected_store, manifest_sha256, evidence_sha256,
    )
    candidates = config.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("Cho static method candidate roster is missing")
    materialized_candidates = [
        _candidate_settings(plan.method, _mapping(row, "static candidate"), plan.model_seed)[2]
        for row in candidates
    ]
    if (
        contract.get("dataset") != plan.dataset
        or contract.get("method") != plan.method
        or contract.get("candidates") != materialized_candidates
        or prior_record["payload"].get("selected_candidate") != selected_candidate
        or final_fit.get("candidate") != selected_candidate
        or final_fit.get("fitted_state_sha256") != expected_model_state_sha256
    ):
        raise ValueError("Cho selection contract differs from static method or state pin")
    selected = [
        _mapping(row, "static candidate") for row in materialized_candidates
        if isinstance(row, Mapping) and row.get("name") == selected_candidate
    ]
    if len(selected) != 1 or final_fit.get("candidate_sha256") != config_digest(selected[0]):
        raise ValueError("Cho final-fit candidate differs from static method configuration")
    _runtime_dependencies(contract)
    _require_host_ram(4.0)
    model = _new_model(prepared, contract=contract, final_fit=final_fit)
    _check_labram_baseline(prepared)
    _require_host_ram(4.0)
    if selected_store.preflight_full_weights(
        manifest_sha256, maximum_bytes=maximum_weights_bytes,
    ) != before_weights:
        raise ValueError("Cho selected weights changed before bounded restore")
    restored = selected_store.restore(
        manifest_sha256, model, expected_evidence_sha256=evidence_sha256,
        protocol_config=protocol_config, model_recipe=prepared.model_recipe,
        maximum_weights_bytes=maximum_weights_bytes,
    )
    _require_host_ram(4.0)
    publication = restored.publication
    if (
        restored.model is not model
        or restored.evidence_record != prior_record
        or publication.weights_format != "full_v1"
        or publication.manifest_sha256 != manifest_sha256
        or publication.evidence_sha256 != evidence_sha256
        or publication.selected_candidate != selected_candidate
        or publication.weights_sha256 != before_weights.sha256
        or publication.model_state_sha256 != expected_model_state_sha256
        or state_digest(model) != expected_model_state_sha256
    ):
        raise ValueError("restored Cho selected tensor state differs from external pins")
    if selected_store.preflight_full_weights(
        manifest_sha256, maximum_bytes=maximum_weights_bytes,
    ) != before_weights:
        raise ValueError("Cho selected weights changed during bounded restore")
    _runtime_dependencies(contract)
    if asdict(capture_source(root)) != contract.get("source"):
        raise ValueError("Cho selected source changed during tensor reconstruction")
    _check_labram_baseline(prepared)
    _require_host_ram(4.0)
    return ChoSelectedSourceStateWitness(
        manifest_sha256, evidence_sha256, selected_candidate,
        recipe_sha256, expected_model_state_sha256, publication.weights_sha256,
    )


def restore_cho_selected_source(
    *, root: Path, plan: CasePlan, method_config: Mapping[str, Any],
    expected_method_config_sha256: str, selected_candidate: str,
    manifest_sha256: str, evidence_sha256: str,
    protocol_config: Mapping[str, Any], catalogs: tuple[TrialCatalog, ...],
    selection_record: Mapping[str, Any], assets: Mapping[str, Any],
    store: SelectedSourceStore | None = None,
) -> VerifiedRestoredChoSource:
    """Release an adapter only after immutable storage and full Cho proof agree."""
    root = root.resolve()
    config = config_snapshot(method_config)
    prepared = prepare_cho_source_restore(
        root=root, plan=plan, method_config=config,
        expected_method_config_sha256=expected_method_config_sha256,
        selected_candidate=selected_candidate,
    )
    selected_store = store if store is not None else SelectedSourceStore(root)
    if selected_store.root != root:
        raise ValueError("selected source store belongs to another project root")
    prior_record, prior_contract, prior_final_fit = _pre_restore_evidence(
        selected_store, manifest_sha256, evidence_sha256,
    )
    _runtime_dependencies(prior_contract)
    model = _new_model(
        prepared, contract=prior_contract, final_fit=prior_final_fit,
    )
    restored = selected_store.restore(
        manifest_sha256, model, expected_evidence_sha256=evidence_sha256,
        protocol_config=protocol_config, model_recipe=prepared.model_recipe,
    )
    record = restored.evidence_record
    payload = record["payload"]
    contract = payload["contract"]
    if record != prior_record or contract != prior_contract:
        raise ValueError("selection evidence changed between lineage check and restore")
    if (
        restored.publication.selected_candidate != selected_candidate
        or payload["selected_candidate"] != selected_candidate
    ):
        raise ValueError("restored source winner differs from caller-pinned candidate")
    _method_config(plan, config, contract, assets)
    if plan.method == "labram_lora":
        if not isinstance(model, LaBraMClassifier) or not isinstance(
            prepared.source_settings, LoRASourceSettings
        ) or not isinstance(prepared.support_settings, LoRAContinuationSettings):
            raise ValueError("restored LoRA source architecture differs")
        validate_trained_lora(model, prepared.source_settings)
        adapter: ChoSelectedAdapter = TrainedLaBraMAdapter(
            plan.method, model, prepared.source_settings, prepared.support_settings,
        )
    elif plan.method in {"labram_linear", "labram_full"}:
        if not isinstance(model, LaBraMClassifier) or not isinstance(
            prepared.support_settings, LaBraMTuningSettings
        ):
            raise ValueError("restored plain LaBraM architecture differs")
        adapter = LaBraMTunedAdapter(plan.method, model, prepared.support_settings)
    else:
        if not isinstance(prepared.support_settings, EEGNetAnchorSettings):
            raise ValueError("restored EEGNet support settings differ")
        adapter = AnchorAdapter("eegnet", prepared.support_settings, model)
    verified = verify_cho_selection_evidence(
        record=record, evidence_sha256=evidence_sha256, plan=plan,
        protocol_config=protocol_config, catalogs=catalogs,
        selection_record=selection_record, assets=assets, root=root,
        adapter_model_state_sha256=state_digest(model),
        adapter_source_settings=asdict(prepared.source_settings),
        adapter_support_settings=asdict(prepared.support_settings),
    )
    _runtime_dependencies(contract)
    if (
        state_digest(model) != restored.publication.model_state_sha256
        or asdict(capture_source(root)) != contract["source"]
    ):
        raise ValueError("restored model or source changed before adapter release")
    if plan.method == "labram_lora":
        assert isinstance(model, LaBraMClassifier)
        assert isinstance(prepared.source_settings, LoRASourceSettings)
        validate_trained_lora(model, prepared.source_settings)
    _check_labram_baseline(prepared)
    return VerifiedRestoredChoSource(adapter, restored, verified, prepared.model_recipe)
