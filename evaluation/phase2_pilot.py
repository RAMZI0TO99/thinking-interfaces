"""Bounded Phase II target-case executor: admission, staged timing and cells.

This module completes one pilot case at a time: it refuses execution without an
explicit operator compute admission backed by live machine guards, verifies the
supplied cell identity against the live environment, claims the case, predicts
the outer target's fixed common queries through the existing audited runners,
derives exact-rational metrics and publishes an evaluation cell through the run
recorder. Source selection is separately charged work whose evidence the caller
    pins by digest; the executor never selects, tunes on queries or weakens a guard.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, NoReturn, Protocol

import numpy as np
import torch
from torch import nn

from adaptation.anchor_manifest import (
    AnchorPrediction,
    BCIAnchorManifestRunner,
    EATangentAnchorSettings,
    EEGNetAnchorSettings,
)
from adaptation.labram_adapter_trained import AdapterSourceSettings
from adaptation.labram_lora_trained import LoRASourceSettings
from adaptation.labram_manifest import (
    LaBraMTuningManifestRunner,
    LaBraMTuningSettings,
)
from adaptation.labram_prompt_trained import PromptSourceSettings, TrainedPromptSourceModel
from adaptation.tcpl_manifest import TCPLManifestRunner
from core.config import config_digest, config_snapshot, load_toml
from core.provenance import capture_source
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import (
    CHO_CHANNELS,
    BCIProfileAssets,
    ChoProfileAssets,
    ChoProfileAssets60Hz,
    ChoProfileBinding60Hz,
)
from evaluation.phase2_protocol import (
    TrialCatalog,
    nested_episode,
    require_digest,
    source_selection,
)
from evaluation.phase2_records import CellIdentity, verify_envelope
from evaluation.phase2_runner import (
    CasePlan,
    CaseRecorder,
    environment_digest,
    method_configuration,
)
from scripts.audit_phase2_protocol import file_digest, validate_protocol

PROBE_CAP_MINUTES = 10.0
SESSION_CAP_MINUTES = 120.0
MINIMUM_FREE_HOST_RAM_GIB = 4.0


def machine_snapshot(
    root: Path, *, disk_free_bytes: float | None = None, gpu_memory_mib: int | None = None,
    free_host_ram_gib: float | None = None,
) -> dict[str, Any]:
    """Live machine guards; injectable reads keep the fail-closed logic testable."""
    import importlib
    import tomllib

    with (root / "configs" / "base.toml").open("rb") as stream:
        base = tomllib.load(stream)
    disk_floor = float(base["storage"]["minimum_free_gb"])
    minimum_gpu = int(base["hardware"]["minimum_gpu_vram_mib"])
    try:
        psutil = importlib.import_module("psutil")
    except ImportError:
        return {"machine_ok": False, "ram_ok": False, "error": "psutil unavailable"}
    free_bytes = (
        float(psutil.disk_usage(str(root)).free) if disk_free_bytes is None else disk_free_bytes
    )
    free_ram = (
        psutil.virtual_memory().available / 1024**3
        if free_host_ram_gib is None
        else float(free_host_ram_gib)
    )
    if gpu_memory_mib is None:
        from scripts.preflight import gpu_status

        gpu = gpu_status()
        observed_gpu = gpu["memory_mib"] if gpu["available"] else None
        if not isinstance(observed_gpu, int):
            observed_gpu = None
    else:
        observed_gpu = gpu_memory_mib
    storage_ok = free_bytes / 1024**3 >= disk_floor
    ram_ok = free_ram >= MINIMUM_FREE_HOST_RAM_GIB
    gpu_ok = observed_gpu is not None and observed_gpu >= minimum_gpu
    return {
        "free_disk_gib": round(free_bytes / 1024**3, 2),
        "minimum_free_disk_gib": disk_floor,
        "storage_ok": storage_ok,
        "gpu_memory_mib": observed_gpu,
        "minimum_gpu_vram_mib": minimum_gpu,
        "gpu_ok": gpu_ok,
        "free_host_ram_gib": round(free_ram, 2),
        "minimum_free_host_ram_gib": MINIMUM_FREE_HOST_RAM_GIB,
        "ram_ok": ram_ok,
        "machine_ok": storage_ok and ram_ok and gpu_ok,
    }


def compute_admission(
    root: Path, *, operator_admitted: bool, disk_free_bytes: float | None = None,
    gpu_memory_mib: int | None = None, free_host_ram_gib: float | None = None,
) -> dict[str, Any]:
    """Explicit operator decision plus live guards; both are required."""
    machine = machine_snapshot(
        root, disk_free_bytes=disk_free_bytes, gpu_memory_mib=gpu_memory_mib,
        free_host_ram_gib=free_host_ram_gib,
    )
    return {
        "operator_compute_admitted": bool(operator_admitted),
        "machine": machine,
        "probe_cap_minutes": PROBE_CAP_MINUTES,
        "session_cap_minutes": SESSION_CAP_MINUTES,
        "admitted": bool(operator_admitted) and bool(machine.get("machine_ok")),
    }


@dataclass(frozen=True, slots=True)
class CaseOutcome:
    logits: torch.Tensor
    targets: torch.Tensor
    support_trial_ids: tuple[str, ...]
    query_trial_ids: tuple[str, ...]
    episode_sha256: str
    checkpoint_sha256: str
    stage_timings_s: tuple[float, ...]
    cho_profile_binding: ChoProfileBinding60Hz | None = None
    anchor_prediction: AnchorPrediction | None = None


class CaseAdapter(Protocol):
    """The executor's method-facing surface; adapters wrap audited runners."""

    method: str

    def predict_target(
        self,
        root: Path,
        config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        assets: Mapping[str, Any],
        episode_record: Mapping[str, Any],
        *,
        outer_target: str,
        shots_per_class: int,
    ) -> CaseOutcome: ...


def _episode_sha(record: Mapping[str, Any]) -> str:
    return str(record.get("sha256", ""))


def _episode_payload_sha(record: Mapping[str, Any]) -> str:
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("episode payload is required")
    return config_digest(payload)


class LaBraMTunedAdapter:
    """Target prediction for plain linear/partial/full selected LaBraM fits.

    The checkpoint digest is the audited runner's owned source state; reaching
    the private snapshot follows the established package-internal contract.
    """

    def __init__(
        self, method: str, model: LaBraMClassifier, support: LaBraMTuningSettings
    ) -> None:
        if method not in ("labram_linear", "labram_partial", "labram_full"):
            raise ValueError("plain adapter covers the linear/partial/full methods")
        self.method = method
        self._model = model
        self._support = support

    def predict_target(
        self,
        root: Path,
        config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        assets: Mapping[str, BCIProfileAssets | ChoProfileAssets],
        episode_record: Mapping[str, Any],
        *,
        outer_target: str,
        shots_per_class: int,
    ) -> CaseOutcome:
        started = time.perf_counter()
        runner = LaBraMTuningManifestRunner(
            root, config, catalogs, selection_record, self._model, assets,
            outer_target=outer_target,
        )
        prediction = runner.predict_target(
            episode_record, shots_per_class=shots_per_class, settings=self._support
        )
        return CaseOutcome(
            prediction.logits,
            prediction.targets,
            prediction.binding.support_trial_ids,
            prediction.binding.query_trial_ids,
            _episode_sha(episode_record),
            state_digest(runner._source),
            (time.perf_counter() - started,),
            cho_profile_binding=(
                prediction.binding
                if isinstance(prediction.binding, ChoProfileBinding60Hz) else None
            ),
        )


class TrainedLaBraMAdapter:
    """Target prediction for source-trained LoRA/adapter/prompt LaBraM fits."""

    def __init__(
        self,
        method: str,
        model: LaBraMClassifier | TrainedPromptSourceModel,
        source_settings: LoRASourceSettings | AdapterSourceSettings | PromptSourceSettings,
        support: Any,
    ) -> None:
        pairs = {
            "labram_lora": LoRASourceSettings,
            "labram_adapter": AdapterSourceSettings,
            "labram_support_prompt": PromptSourceSettings,
        }
        if method not in pairs:
            raise ValueError("trained adapter covers LoRA, adapter and prompt methods")
        self.method = method
        self._model = model
        self._source_settings = source_settings
        self._support = support

    def predict_target(
        self,
        root: Path,
        config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        assets: Mapping[str, BCIProfileAssets | ChoProfileAssets],
        episode_record: Mapping[str, Any],
        *,
        outer_target: str,
        shots_per_class: int,
    ) -> CaseOutcome:
        started = time.perf_counter()
        checkpoint = state_digest(self._model)
        episode_sha = _episode_sha(episode_record)
        prediction: Any
        if self.method == "labram_lora":
            from adaptation.labram_lora_trained import TrainedLoRAManifestRunner

            assert isinstance(self._source_settings, LoRASourceSettings)
            assert isinstance(self._model, LaBraMClassifier)
            prediction = TrainedLoRAManifestRunner(
                root, config, catalogs, selection_record, self._model, assets,
                source_settings=self._source_settings,
                source_state_sha256=checkpoint,
                outer_target=outer_target,
            ).predict_target(
                episode_record, shots_per_class=shots_per_class, settings=self._support
            )
        elif self.method == "labram_adapter":
            from adaptation.labram_adapter_trained import TrainedAdapterManifestRunner

            assert isinstance(self._source_settings, AdapterSourceSettings)
            assert isinstance(self._model, LaBraMClassifier)
            prediction = TrainedAdapterManifestRunner(
                root, config, catalogs, selection_record, self._model, assets,
                source_settings=self._source_settings,
                source_state_sha256=checkpoint,
                outer_target=outer_target,
            ).predict_target(
                episode_record, shots_per_class=shots_per_class, settings=self._support
            )
        else:
            from adaptation.labram_prompt_trained import TrainedPromptManifestRunner

            assert isinstance(self._source_settings, PromptSourceSettings)
            assert isinstance(self._model, TrainedPromptSourceModel)
            prediction = TrainedPromptManifestRunner(
                root, config, catalogs, selection_record, self._model, assets,
                source_settings=self._source_settings,
                source_state_sha256=checkpoint,
                outer_target=outer_target,
            ).predict_target(
                episode_record, shots_per_class=shots_per_class, settings=self._support
            )
        return CaseOutcome(
            prediction.logits,
            prediction.targets,
            prediction.binding.support_trial_ids,
            prediction.binding.query_trial_ids,
            episode_sha,
            checkpoint,
            (time.perf_counter() - started,),
            cho_profile_binding=(
                prediction.binding
                if isinstance(prediction.binding, ChoProfileBinding60Hz) else None
            ),
        )


class TCPLAdapter:
    """Target prediction through a final fitted TCPL manifest runner."""

    def __init__(self, runner: TCPLManifestRunner, *, query_batch_size: int = 8) -> None:
        if runner._validation_subject is not None:  # Final runners have no inner subject.
            raise ValueError("the TCPL runner must be a final outer-role fit")
        self.method = "tcpl"
        self._runner = runner
        self._query_batch_size = query_batch_size

    def predict_target(
        self,
        root: Path,
        config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        assets: Mapping[str, Any],
        episode_record: Mapping[str, Any],
        *,
        outer_target: str,
        shots_per_class: int,
    ) -> CaseOutcome:
        del root, config, catalogs, selection_record, assets, outer_target
        started = time.perf_counter()
        prediction = self._runner.predict_target(
            episode_record, shots_per_class=shots_per_class,
            query_batch_size=self._query_batch_size,
        )
        if prediction.episode_sha256 != _episode_payload_sha(episode_record):
            raise ValueError("TCPL prediction differs from the bound episode payload")
        return CaseOutcome(
            prediction.logits,
            prediction.targets,
            (),
            prediction.query_trial_ids,
            _episode_sha(episode_record),
            self._runner.source_state_sha256,
            (time.perf_counter() - started,),
        )


class AnchorAdapter:
    """Target prediction for the matched EEGNet and EA-tangent anchors."""

    def __init__(
        self, method: str, settings: EEGNetAnchorSettings | EATangentAnchorSettings,
        model: nn.Module | None = None,
    ) -> None:
        if method not in ("eegnet", "ea_tangent_lr"):
            raise ValueError("anchor adapter covers EEGNet and EA-tangent")
        if method == "eegnet" and model is None:
            raise ValueError("the EEGNet anchor requires its fitted source model")
        if method == "ea_tangent_lr" and not isinstance(settings, EATangentAnchorSettings):
            raise ValueError("the EA-tangent anchor requires classical anchor settings")
        self.method = method
        self._settings = settings
        self._model = model

    def predict_target(
        self,
        root: Path,
        config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        assets: Mapping[str, Any],
        episode_record: Mapping[str, Any],
        *,
        outer_target: str,
        shots_per_class: int,
    ) -> CaseOutcome:
        started = time.perf_counter()
        runner = BCIAnchorManifestRunner(
            root, config, catalogs, selection_record, assets,
            outer_target=outer_target,
            eegnet_source=self._model,
        )
        prediction = runner.predict_target(
            episode_record, shots_per_class=shots_per_class, settings=self._settings
        )
        if prediction.episode_sha256 != _episode_payload_sha(episode_record):
            raise ValueError("anchor prediction differs from the bound episode payload")
        checkpoint = (
            state_digest(self._model) if self._model is not None
            else prediction.fitted_state_sha256
        )
        return CaseOutcome(
            torch.from_numpy(prediction.probabilities),
            torch.from_numpy(prediction.targets),
            tuple(prediction.support_trial_ids),
            tuple(prediction.query_trial_ids),
            _episode_sha(episode_record),
            checkpoint,
            (time.perf_counter() - started,),
            anchor_prediction=prediction if prediction.method == "eegnet" else None,
        )


def _cho_target_input_attestation(
    *,
    root: Path,
    plan: CasePlan,
    identity: CellIdentity,
    outcome: CaseOutcome,
    target_catalog: TrialCatalog,
    episode_sha256: str,
    selection_sha256: str,
    expected_source_subjects: tuple[str, ...],
    expected_support_ids: tuple[str, ...],
    expected_query_ids: tuple[str, ...],
    assets: Mapping[str, Any],
    target_asset: ChoProfileAssets60Hz | None,
) -> dict[str, Any]:
    """Bind observed target-loader evidence to one selected Cho case before publication."""
    common = {
        "schema": "cho2017-target-input-v1",
        "method": plan.method,
        "subject": plan.target_subject,
        "episode_record_sha256": identity.episode_sha256,
    }
    base_sha256 = file_digest(root / "configs/base.toml")
    if plan.method == "eegnet":
        prediction = outcome.anchor_prediction
        if (
            outcome.cho_profile_binding is not None
            or assets
            or target_asset is not None
            or not isinstance(prediction, AnchorPrediction)
            or prediction.method != "eegnet"
            or prediction.subject != plan.target_subject
            or prediction.role != "outer_target"
            or prediction.episode_sha256 != episode_sha256
            or prediction.selection_sha256 != selection_sha256
            or prediction.support_trial_ids != expected_support_ids
            or prediction.query_trial_ids != expected_query_ids
            or prediction.source_subjects != expected_source_subjects
            or prediction.classes != target_catalog.classes
            or prediction.source_state_sha256 != identity.checkpoint_sha256
            or not isinstance(prediction.settings, EEGNetAnchorSettings)
            or prediction.settings_sha256 != config_digest(asdict(prediction.settings))
            or not torch.equal(torch.from_numpy(prediction.targets), outcome.targets)
            or not torch.equal(torch.from_numpy(prediction.probabilities), outcome.logits)
        ):
            raise ValueError("Cho EEGNet target Profile A observation differs from the case")
        target_inputs = prediction.input_identities
        if not isinstance(target_inputs, Mapping) or set(target_inputs) != {
            plan.target_subject
        }:
            raise ValueError("Cho EEGNet target inputs must contain only target Profile A")
        observed = target_inputs[plan.target_subject]
        expected = {
            "catalog_sha256": target_catalog.sha256,
            "artifact_sha256": target_catalog.artifact_sha256,
            "manifest_sha256": target_catalog.artifact_sha256,
            "base_config_sha256": base_sha256,
        }
        if not isinstance(observed, Mapping) or dict(observed) != expected:
            raise ValueError("Cho EEGNet target Profile A identity differs from the catalog")
        anchor = {
            "method": prediction.method,
            "subject": prediction.subject,
            "role": prediction.role,
            "episode_sha256": prediction.episode_sha256,
            "selection_sha256": prediction.selection_sha256,
            "support_trial_ids": prediction.support_trial_ids,
            "query_trial_ids": prediction.query_trial_ids,
            "source_subjects": prediction.source_subjects,
            "input_identities": {plan.target_subject: dict(observed)},
        }
        return {**common, "profile": "cho_profile_a", "anchor": anchor}

    binding = outcome.cho_profile_binding
    if (
        outcome.anchor_prediction is not None
        or not isinstance(binding, ChoProfileBinding60Hz)
        or not isinstance(target_asset, ChoProfileAssets60Hz)
        or assets.get(plan.target_subject) != target_asset
    ):
        raise ValueError("Cho LaBraM target 60 Hz binding or asset pin is missing")
    variant_path = root / "configs/phase2/cho_profile_b_60hz.toml"
    manifest_path = (
        root / "data/processed/cho2017/profile_b_60hz_v1"
        / f"{plan.target_subject}.manifest.json"
    )
    if (
        file_digest(variant_path) != target_asset.variant_config_sha256
        or file_digest(manifest_path) != target_asset.profile_b_manifest_sha256
    ):
        raise ValueError("Cho target 60 Hz variant or manifest bytes differ from asset pins")
    variant = load_toml(variant_path)
    manifest = json.loads(manifest_path.read_text("utf-8"))
    if (
        file_digest(variant_path) != target_asset.variant_config_sha256
        or file_digest(manifest_path) != target_asset.profile_b_manifest_sha256
    ):
        raise ValueError("Cho target 60 Hz variant or manifest changed while attesting")
    preprocessing = variant.get("preprocessing")
    if not isinstance(preprocessing, Mapping) or not isinstance(manifest, Mapping):
        raise ValueError("Cho target 60 Hz variant or manifest structure differs")
    if (
        binding.dataset != "cho2017"
        or binding.subject != plan.target_subject
        or binding.shots_per_class != plan.shots_per_class
        or binding.classes != target_catalog.classes
        or binding.channel_names != CHO_CHANNELS
        or binding.protocol_sha256 != identity.protocol_sha256
        or binding.episode_sha256 != episode_sha256
        or binding.profile_a_artifact_sha256 != target_catalog.artifact_sha256
        or binding.profile_a_preprocessing_sha256 != target_catalog.preprocessing_sha256
        or binding.profile_b_artifact_sha256 != target_asset.profile_b_artifact_sha256
        or binding.profile_b_manifest_sha256 != target_asset.profile_b_manifest_sha256
        or binding.variant_config_sha256 != target_asset.variant_config_sha256
        or binding.base_config_sha256 != base_sha256
        or binding.profile_b_config_sha256 != config_digest(preprocessing)
        or binding.source_file != manifest.get("source_file")
        or binding.source_sha256 != manifest.get("source_sha256")
        or binding.support_trial_ids != expected_support_ids
        or binding.query_trial_ids != expected_query_ids
        or binding.schema != "cho-a-to-b-episode-60hz-v1"
        or binding.sampling_rate_hz != 200
        or binding.samples_per_trial != 800
        or binding.patch_samples != 200
        or binding.stored_unit_volts != 0.0001
        or binding.extra_input_scale != 1.0
        or binding.rejection_policy != "profile_a_frozen_threshold_only"
        or binding.target_transform_fit != "none"
        or binding.profile_a_sidecar_manifests
        != "absent_cho_identity_is_the_audited_catalog_hash"
        or not binding.source_file.startswith("data/raw/moabb/cho2017/")
        or binding.input_trials < 0
        or binding.profile_a_rejected_trials < 0
        or binding.input_trials - binding.profile_a_rejected_trials
        != len(target_catalog.trial_ids)
        or len(binding.support_profile_b_rows) != len(expected_support_ids)
        or len(binding.query_profile_b_rows) != len(expected_query_ids)
        or len(set(binding.support_profile_b_rows + binding.query_profile_b_rows))
        != len(expected_support_ids) + len(expected_query_ids)
        or any(row < 0 or row >= binding.input_trials for row in (
            binding.support_profile_b_rows + binding.query_profile_b_rows
        ))
    ):
        raise ValueError("Cho LaBraM target 60 Hz binding differs from the planned inputs")
    require_digest(binding.source_sha256, "Cho target raw source")
    return {
        **common,
        "profile": "cho_profile_b_60hz_v1",
        "binding_sha256": binding.sha256,
        "binding": asdict(binding),
    }


class TargetCaseExecutor:
    """One claimed, timed, verified pilot target case ending in a cell or failure."""

    def __init__(
        self, root: Path, recorder: CaseRecorder, *, admission: Mapping[str, Any], worker: str
    ) -> None:
        admitted = admission.get("admitted")
        if not isinstance(admitted, bool):
            raise ValueError("an explicit boolean compute admission is required")
        probe_cap = admission.get("probe_cap_minutes", PROBE_CAP_MINUTES)
        session_cap = admission.get("session_cap_minutes", SESSION_CAP_MINUTES)
        for name, cap in (("probe_cap_minutes", probe_cap), ("session_cap_minutes", session_cap)):
            if not isinstance(cap, (int, float)) or cap <= 0:
                raise ValueError(f"{name} must be a positive number")
        self._root = root.resolve()
        self._recorder = recorder
        self._admission = dict(admission)
        self._admitted = admitted
        self._probe_cap = float(probe_cap)
        self._session_cap = float(session_cap)
        self._worker = worker
        self._session_started = time.perf_counter()

    def _refused(self, message: str) -> NoReturn:
        raise ValueError(message)

    def run_case(
        self,
        plan: CasePlan,
        *,
        adapter: CaseAdapter,
        identity: CellIdentity,
        method_config: Mapping[str, Any],
        selection_evidence_sha256: str,
        selection_evidence_path: Path | None = None,
        protocol_config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        episode_record: Mapping[str, Any],
        assets: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not self._admitted:
            self._refused("compute admission is required before executing a pilot case")
        elapsed = (time.perf_counter() - self._session_started) / 60.0
        if elapsed > self._session_cap:
            self._refused("the pilot session cap is exhausted")
        if adapter.method != plan.method or identity.method != plan.method:
            self._refused("adapter and cell identity must match the planned method")
        if identity.dataset != plan.dataset:
            self._refused("cell identity must match the planned dataset")
        if identity.target_subject != plan.target_subject:
            self._refused("cell identity must match the planned target subject")
        if identity.shots_per_class != plan.shots_per_class:
            self._refused("cell identity must match the planned shot level")
        if identity.model_seed != plan.model_seed:
            self._refused("cell identity must match the planned model seed")
        if method_configuration(method_config) != identity.method_config_sha256:
            self._refused("the method configuration digest differs from the cell identity")
        if config_digest(protocol_config) != identity.protocol_sha256:
            self._refused("the protocol configuration digest differs from the cell identity")
        if not catalogs or any(not isinstance(catalog, TrialCatalog) for catalog in catalogs):
            self._refused("typed trial catalogs are required for the planned dataset")
        if any(catalog.dataset != identity.dataset for catalog in catalogs):
            self._refused("trial catalog dataset differs from the cell identity")
        target_catalogs = [
            catalog for catalog in catalogs if catalog.subject == plan.target_subject
        ]
        if len(target_catalogs) != 1:
            self._refused("the planned target must have exactly one trial catalog")
        if identity.preprocessing_sha256 != target_catalogs[0].preprocessing_sha256:
            self._refused("target catalog preprocessing differs from the cell identity")
        selection = source_selection(catalogs, target=plan.target_subject)
        if not verify_envelope(
            selection_record, kind="source_selection", expected_payload=asdict(selection)
        ) or identity.selection_sha256 != selection_record.get("sha256"):
            self._refused("source selection differs from the catalogs or cell identity")
        episode = nested_episode(
            target_catalogs[0],
            shots=validate_protocol(config_snapshot(protocol_config)),
            protocol_sha256=identity.protocol_sha256,
        )
        if not verify_envelope(
            episode_record, kind="episode_manifest", expected_payload=episode.payload()
        ):
            self._refused("target episode differs from the catalog and protocol")
        partition = episode.partition(plan.shots_per_class)
        if identity.episode_sha256 != str(episode_record.get("sha256", "")):
            self._refused("the declared episode differs from the cell identity")
        source = capture_source(self._root)
        if (
            identity.source_sha256 != source.source_sha256
            or identity.git_commit != source.git_commit
            or identity.git_dirty != source.git_dirty
            or identity.environment_sha256 != environment_digest()
        ):
            self._refused("cell identity does not match the live source or environment")
        cho_case = plan.dataset == "cho2017" and plan.method in {
            "labram_linear", "labram_lora", "labram_full", "eegnet",
        }
        selected_source_manifest_sha256: str | None = None
        selected_source_manifest_path: str | None = None
        selected_manifest_witness = None
        if cho_case:
            if selection_evidence_path is None:
                self._refused("persisted Cho selection evidence is required before claim")
            from evaluation.phase2_cho_execution_gate import verify_cho_case_preclaim

            verified_selection = verify_cho_case_preclaim(
                root=self._root,
                plan=plan,
                adapter=adapter,
                identity=identity,
                method_config=method_config,
                evidence_path=selection_evidence_path,
                evidence_sha256=selection_evidence_sha256,
                protocol_config=protocol_config,
                catalogs=catalogs,
                selection_record=selection_record,
                assets=assets,
            )
            renewed = compute_admission(
                self._root,
                operator_admitted=self._admission.get("operator_compute_admitted") is True,
            )
            if not renewed["admitted"]:
                self._refused("live Cho compute admission failed before claim")
            from evaluation.phase2_cho_publication_gate import (
                _selected_model,
                publish_verified_cho_source,
            )

            verified_publication = publish_verified_cho_source(
                root=self._root, plan=plan, adapter=adapter, identity=identity,
                method_config=method_config, protocol_config=protocol_config,
                evidence_path=selection_evidence_path, selection=verified_selection,
            )
            publication = verified_publication.publication
            selected_manifest_witness = verified_publication.witness
            selected_source_manifest_sha256 = publication.manifest_sha256
            selected_source_manifest_path = publication.manifest_path.resolve().relative_to(
                self._root
            ).as_posix()
            if (
                capture_source(self._root) != source
                or environment_digest() != identity.environment_sha256
                or state_digest(_selected_model(adapter, plan.method))
                != identity.checkpoint_sha256
            ):
                self._refused("live Cho source, environment or model changed after publication")
            renewed = compute_admission(
                self._root,
                operator_admitted=self._admission.get("operator_compute_admitted") is True,
            )
            if not renewed["admitted"]:
                self._refused("live Cho compute admission failed after source publication")
            if (time.perf_counter() - self._session_started) / 60.0 > self._session_cap:
                self._refused("the pilot session cap is exhausted after source publication")
        target_asset = assets.get(plan.target_subject)
        attestation: dict[str, Any] | None = None
        claim_started = time.perf_counter()
        self._recorder.claim(plan, worker=self._worker)
        claim_seconds = time.perf_counter() - claim_started
        case_started = time.perf_counter()
        try:
            outcome = adapter.predict_target(
                self._root,
                protocol_config,
                catalogs,
                selection_record,
                assets,
                episode_record,
                outer_target=plan.target_subject,
                shots_per_class=plan.shots_per_class,
            )
            if identity.episode_sha256 != outcome.episode_sha256:
                raise ValueError("the bound episode differs from the cell identity")
            if identity.checkpoint_sha256 != outcome.checkpoint_sha256:
                raise ValueError("the predicted checkpoint differs from the cell identity")
            target_catalog = target_catalogs[0]
            expected_query_ids = tuple(
                target_catalog.trial_ids[index] for index in partition.query_indices
            )
            expected_support_ids = tuple(
                target_catalog.trial_ids[index] for index in partition.support_indices
            )
            if outcome.query_trial_ids != expected_query_ids:
                raise ValueError("predicted query identities differ from the target episode")
            if plan.method != "tcpl" and outcome.support_trial_ids != expected_support_ids:
                raise ValueError("predicted support identities differ from the target episode")
            expected_targets = tuple(
                target_catalog.classes.index(target_catalog.labels[index])
                for index in partition.query_indices
            )
            if (
                outcome.logits.shape[0] != len(expected_query_ids)
                or tuple(outcome.targets.tolist()) != expected_targets
            ):
                raise ValueError("predicted target rows differ from the target episode")
            if cho_case:
                attestation = _cho_target_input_attestation(
                    root=self._root,
                    plan=plan,
                    identity=identity,
                    outcome=outcome,
                    target_catalog=target_catalog,
                    episode_sha256=episode.sha256,
                    selection_sha256=selection.sha256,
                    expected_source_subjects=selection.source_subjects,
                    expected_support_ids=expected_support_ids,
                    expected_query_ids=expected_query_ids,
                    assets=assets,
                    target_asset=(
                        target_asset if isinstance(target_asset, ChoProfileAssets60Hz) else None
                    ),
                )
            confusion, rational, query_count = _metrics(outcome)
            if cho_case:
                assert selection_evidence_path is not None
                from evaluation.phase2_cho_execution_gate import (
                    _persisted_record,
                    verify_cho_adapter_posttarget,
                )

                post_record = _persisted_record(
                    self._root, selection_evidence_path, selection_evidence_sha256,
                )
                if post_record.get("sha256") != selection_evidence_sha256:
                    raise ValueError("persisted Cho selection evidence changed during target work")
                verify_cho_adapter_posttarget(
                    plan=plan, adapter=adapter, identity=identity,
                    evidence_record=post_record,
                )
                if (
                    capture_source(self._root) != source
                    or environment_digest() != identity.environment_sha256
                ):
                    raise ValueError("live source or environment changed during Cho target work")
                assert selected_manifest_witness is not None
                selected_manifest_witness.verify_stable()
                renewed = compute_admission(
                    self._root,
                    operator_admitted=self._admission.get("operator_compute_admitted") is True,
                )
                if not renewed["admitted"]:
                    raise ValueError("live Cho compute admission failed after target work")
        except Exception as error:  # Failures are evidence, never silent skips.
            self._recorder.record_failure(
                plan, attempt=1, reason={"error": str(error), "stage": "target_case"}
            )
            raise
        case_seconds = time.perf_counter() - case_started
        if case_seconds / 60.0 > self._probe_cap:
            self._recorder.record_failure(
                plan, attempt=1, reason={"error": "probe cap exceeded", "stage": "cap"}
            )
            self._refused("the per-case probe cap is exceeded; no cell was published")
        persist_started = time.perf_counter()
        cell = self._recorder.record_cell(
            identity,
            plan=plan,
            metrics={
                "role": "outer_target",
                "selection_evidence_sha256": selection_evidence_sha256,
                "confusion_matrix": confusion,
                "balanced_accuracy": [rational.numerator, rational.denominator],
                "query_count": query_count,
                **({"target_input_attestation": attestation} if attestation is not None else {}),
                **({
                    "selection_evidence_path": selection_evidence_path.resolve().relative_to(
                        self._root
                    ).as_posix(),
                } if cho_case and selection_evidence_path is not None else {}),
                **({
                    "selected_source_manifest_sha256": selected_source_manifest_sha256,
                    "selected_source_manifest_path": selected_source_manifest_path,
                } if cho_case else {}),
                "stage_timings_s": [
                    claim_seconds,
                    *outcome.stage_timings_s,
                    time.perf_counter() - persist_started,
                ],
            },
        )
        return {
            "case_id": plan.case_id,
            "cell": str(cell),
            "cell_sha256": identity.sha256,
            "stage_timings_s": [claim_seconds, *outcome.stage_timings_s],
            "confusion_matrix": confusion,
            "balanced_accuracy": [rational.numerator, rational.denominator],
        }

def _metrics(outcome: CaseOutcome) -> tuple[list[list[int]], Fraction, int]:
    logits, targets = outcome.logits, outcome.targets
    if (
        logits.ndim != 2
        or logits.shape[0] != targets.shape[0]
        or logits.shape[1] < 2
        or not torch.isfinite(logits).all()
        or targets.dtype != torch.long
        or torch.any(targets < 0)
        or torch.any(targets >= logits.shape[1])
    ):
        raise ValueError("invalid target-case logits or targets")
    classes = int(logits.shape[1])
    confusion = np.zeros((classes, classes), dtype=np.int64)
    np.add.at(confusion, (targets.numpy(), logits.argmax(dim=1).numpy()), 1)
    rows = confusion.tolist()
    rational = (
        sum(
            (Fraction(int(row[i]), int(sum(row))) for i, row in enumerate(rows)),
            start=Fraction(),
        )
        / classes
    )
    return rows, rational, int(confusion.sum())
