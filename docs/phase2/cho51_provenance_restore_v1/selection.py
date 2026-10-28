"""Versioned complete-selection verifier with an explicit producer role.

The complete canonical structural checks and hard-cap calculation are retained;
canonical leaf validators remain shared. This file deliberately does not call
or modify the single-root canonical public verifier.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
from typing import Any

from core.config import config_digest, config_snapshot
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz, dataset_cohort
from evaluation.phase2_protocol import TrialCatalog, nested_episode, selection_gradient_ceiling, source_selection
from evaluation.phase2_records import verify_envelope
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_selection_evidence_binding import (
    CHO_METHODS, VerifiedChoSelection, _PAYLOAD_KEYS, _EEGNET_FOLD_KEYS,
    _LABRAM_FOLD_KEYS, _LORA_EXTRA_KEYS, _mapping, _rows, _digest, _fraction,
    _fit, _cho_binding, _mask, _finite_losses, _fold_score, _required_complete_selection_steps,
)
from scripts.audit_phase2_protocol import validate_protocol


def verify_historical_selection(
    *,
    record: Mapping[str, Any],
    evidence_sha256: str,
    plan: CasePlan,
    protocol_config: Mapping[str, Any],
    catalogs: tuple[TrialCatalog, ...],
    selection_record: Mapping[str, Any],
    assets: Mapping[str, Any],
    root: Path,
    producer_source: Mapping[str, Any],
    adapter_model_state_sha256: str,
    adapter_source_settings: Mapping[str, Any],
    adapter_support_settings: Mapping[str, Any],
) -> VerifiedChoSelection:
    """Revalidate complete historical metadata against its explicit producer.

    The current root supplies only the local execution hard ceiling. Historical
    Git is never recaptured from the executor or substituted into an envelope.
    """
    if (
        not isinstance(plan, CasePlan)
        or plan.dataset != "cho2017"
        or plan.method not in CHO_METHODS
    ):
        raise ValueError("the verifier covers the selected Cho four-method scope")
    _digest(evidence_sha256, "selection evidence digest")
    _digest(adapter_model_state_sha256, "adapter model state digest")
    if (
        not catalogs
        or any(not isinstance(catalog, TrialCatalog) for catalog in catalogs)
        or len(catalogs) != 52
    ):
        raise ValueError("the complete typed 52-subject Cho catalog is required")
    config = config_snapshot(protocol_config)
    shots = validate_protocol(config)
    protocol_settings = _mapping(config["protocol"], "protocol settings")
    if (
        plan.shots_per_class not in shots
        or plan.model_seed not in _rows(protocol_settings.get("model_seeds"), "model seeds")
    ):
        raise ValueError("planned shots or seed is outside the protocol")
    dataset, _, classes, subjects = dataset_cohort(config, catalogs)
    if (
        dataset != "cho2017"
        or len(subjects) != 52
        or any(catalog.classes != classes for catalog in catalogs)
    ):
        raise ValueError("the Cho catalog differs from the declared cohort or classes")
    selection = source_selection(catalogs, target=plan.target_subject)
    if not verify_envelope(
        selection_record, kind="source_selection", expected_payload=asdict(selection)
    ):
        raise ValueError("source selection differs from the complete catalogs")
    payload = _mapping(record.get("payload"), "selection evidence payload")
    if (
        not verify_envelope(record, kind="engineering_smoke", expected_payload=payload)
        or evidence_sha256 != record.get("sha256")
    ):
        raise ValueError("selection evidence envelope or caller digest differs")
    if set(payload) != _PAYLOAD_KEYS:
        raise ValueError("selection evidence has missing or unexpected fields")
    contract = _mapping(payload["contract"], "selection contract")
    expected_purpose = (
        "bounded_eegnet_source_selection"
        if plan.method == "eegnet" else "bounded_labram_source_selection"
    )
    if (
        payload["purpose"] != expected_purpose
        or payload["contract_sha256"] != config_digest(contract)
        or payload["complete"] is not True
        or payload["outer_target_predictions_performed"] is not False
    ):
        raise ValueError("selection contract digest, purpose or completion differs")
    source = dict(_mapping(producer_source, "independently authenticated producer source"))
    seed_field = "model_and_sampling_seed" if plan.method == "eegnet" else "head_and_sampling_seed"
    if (
        contract.get("method") != plan.method
        or contract.get("dataset") != plan.dataset
        or contract.get("selection") != config_snapshot(asdict(selection))
        or contract.get("protocol_sha256") != config_digest(config)
        or contract.get("shots_per_class") != plan.shots_per_class
        or contract.get(seed_field) != plan.model_seed
        or type(contract.get(seed_field)) is not int
        or contract.get("source") != source
        or contract.get("source_policy")
        != "all_non_target_subjects; inner_validation_also_excluded"
        or contract.get("score") != "mean_subject_balanced_accuracy_exact_rational"
        or contract.get("tie_break") != "first_in_declared_candidate_order"
        or contract.get("early_stopping") is not False
        or contract.get("engineering_only") is not True
        or contract.get("scientific_evaluation") is not False
    ):
        raise ValueError("selection contract differs from the live planned source case")
    maximum_steps = contract.get("maximum_gradient_steps")
    if type(maximum_steps) is not int or not 1 <= maximum_steps <= (
        selection_gradient_ceiling(root)
    ):
        raise ValueError("selection contract has no bounded engineering step ceiling")
    runtime = _mapping(contract.get("runtime"), "source selection runtime")
    if (
        runtime.get("device") not in ("cpu", "cuda:0")
        or runtime.get("dtype") != "float32"
        or type(runtime.get("torch_threads")) is not int
        or runtime["torch_threads"] < 1
        or type(runtime.get("deterministic_algorithms")) is not bool
        or any(not isinstance(runtime.get(name), str) or not runtime[name]
               for name in ("python", "torch", "numpy", "braindecode"))
    ):
        raise ValueError("source selection runtime is incomplete")
    if plan.method == "eegnet":
        if contract.get("outer_target") != plan.target_subject or assets or contract.get(
            "profile_a_manifests"
        ) != {} or runtime["device"] != "cpu" or "source_execution" in contract:
            raise ValueError("EEGNet Cho selection requires its empty Profile A sidecar map")
    else:
        if "source_execution" in contract:
            execution = _mapping(contract["source_execution"], "LaBraM source execution")
            if (
                execution.get("source_device") != runtime["device"]
                or execution.get("support_query_device") != "cpu"
                or execution.get("checkpoint_policy") not in {
                    "disabled", "immutable_every_gradient_step_all_generations_retained",
                }
                or execution.get("optimizer_resume") != "stateless_sgd_only"
            ):
                raise ValueError("LaBraM source execution differs from its runtime")
        elif runtime["device"] != "cpu":
            raise ValueError("CUDA LaBraM source execution metadata is missing")
        _digest(contract.get("template_state_sha256"), "LaBraM template state")
        _digest(contract.get("initial_state_sha256"), "LaBraM initial state")
        if (
            contract.get("prior_template_training_verified") is not False
            or contract.get("source_trial_pool")
            != "all_profile_a_retained_trials_joined_to_profile_b"
            or contract.get("sampling_rate_hz") != 200
            or contract.get("samples_per_trial") != 800
            or contract.get("stored_unit_volts") != 0.0001
            or contract.get("extra_input_scale") != 1.0
        ):
            raise ValueError("LaBraM source input contract differs")
        if set(assets) != subjects or any(
            not isinstance(value, ChoProfileAssets60Hz) for value in assets.values()
        ):
            raise ValueError("LaBraM requires the complete typed Cho 60 Hz asset map")
        expected_assets = {subject: asdict(assets[subject]) for subject in sorted(subjects)}
        if contract.get("profile_assets") != expected_assets:
            raise ValueError("selection assets differ from the actual 60 Hz map")
    candidates = _rows(contract.get("candidates"), "candidate roster")
    if len(candidates) != 2:
        raise ValueError("Cho selection requires two ordered candidates")
    candidates = [_mapping(candidate, "candidate") for candidate in candidates]
    names = [candidate.get("name") for candidate in candidates]
    if any(not isinstance(name, str) or not name.strip() for name in names) or len(
        set(names)
    ) != len(names):
        raise ValueError("selection candidate names are absent or duplicated")
    settings_hashes = []
    for candidate in candidates:
        if set(candidate) != {"name", "source", "support"}:
            raise ValueError("selection candidate fields differ from the selector schema")
        source_settings = _mapping(candidate.get("source"), "candidate source settings")
        support_settings = _mapping(candidate.get("support"), "candidate support settings")
        if plan.method in {"labram_linear", "labram_full"} and (
            source_settings.get("method") != plan.method.removeprefix("labram_")
            or support_settings.get("method") != plan.method.removeprefix("labram_")
        ):
            raise ValueError("plain LaBraM candidate method differs")
        settings_hashes.append(
            config_digest({"source": source_settings, "support": support_settings})
        )
    if len(set(settings_hashes)) != len(settings_hashes):
        raise ValueError("selection candidate settings are duplicated")
    catalog_by_subject = {catalog.subject: catalog for catalog in catalogs}
    protocol_sha256 = config_digest(config)
    episodes = {
        subject: nested_episode(catalog, shots=shots, protocol_sha256=protocol_sha256)
        for subject, catalog in catalog_by_subject.items()
    }
    folds = _rows(payload["folds"], "selection folds")
    expected_pairs = {
        (name, subject) for name in names for subject in selection.source_subjects
    }
    if len(folds) != len(expected_pairs):
        raise ValueError("candidate by source-subject fold coverage is incomplete")
    candidates_by_name = {candidate["name"]: candidate for candidate in candidates}
    observed_pairs: set[tuple[str, str]] = set()
    per_candidate: dict[str, list[Fraction]] = {name: [] for name in names}
    for raw_fold in folds:
        fold = _mapping(raw_fold, "selection fold")
        expected_fold_keys = (
            _EEGNET_FOLD_KEYS if plan.method == "eegnet"
            else _LABRAM_FOLD_KEYS | (_LORA_EXTRA_KEYS if plan.method == "labram_lora" else set())
        )
        if set(fold) != expected_fold_keys:
            raise ValueError("selection fold fields differ from the method schema")
        candidate_name = fold.get("candidate")
        validation_name = fold.get("validation_subject")
        if not isinstance(candidate_name, str) or not isinstance(validation_name, str):
            raise ValueError("selection fold needs candidate and source subject names")
        pair = (candidate_name, validation_name)
        if pair not in expected_pairs or pair in observed_pairs:
            raise ValueError("selection fold is unexpected or duplicated")
        observed_pairs.add(pair)
        name, validation_subject = pair
        candidate = candidates_by_name[name]
        permitted = tuple(s for s in selection.source_subjects if s != validation_subject)
        state = _fit(
            fold.get("source_fit"), candidate=candidate,
            validation_subject=validation_subject, training_subjects=permitted,
            catalog_by_subject=catalog_by_subject, episodes=episodes, assets=assets,
            seed=plan.model_seed, method=plan.method,
        )
        catalog = catalog_by_subject[validation_subject]
        episode = episodes[validation_subject]
        partition = episode.partition(plan.shots_per_class)
        query_ids = [catalog.trial_ids[index] for index in partition.query_indices]
        support_ids = [catalog.trial_ids[index] for index in partition.support_indices]
        _digest(fold.get("adapted_state_sha256"), "adapted validation state")
        if plan.method == "eegnet":
            if (
                fold.get("episode_sha256") != episode.sha256
                or fold.get("query_trial_ids") != query_ids
                or fold.get("support_trial_ids") != support_ids
            ):
                raise ValueError("EEGNet validation episode differs from the source fold")
            input_identities = _mapping(fold["input_identities"], "EEGNet validation inputs")
            identity = _mapping(
                input_identities.get(validation_subject), "EEGNet validation identity"
            )
            if (
                set(input_identities) != {validation_subject}
                or identity.get("catalog_sha256") != catalog.sha256
                or identity.get("artifact_sha256") != catalog.artifact_sha256
            ):
                raise ValueError("EEGNet validation input differs from the source catalog")
            _digest(identity.get("manifest_sha256"), "EEGNet validation manifest")
            _digest(identity.get("base_config_sha256"), "EEGNet validation base config")
            support_fit = _mapping(fold["support_fit"], "EEGNet validation support fit")
            support_steps = _mapping(candidate["support"], "candidate support settings").get(
                "steps"
            )
            if support_fit.get("source_fit_performed") is not False:
                raise ValueError("EEGNet validation support fit differs from settings")
            _finite_losses(
                support_fit.get("support_losses"), count=support_steps,
                name="EEGNet validation support losses",
            )
        else:
            asset = assets[validation_subject]
            _cho_binding(
                fold.get("binding"), catalog=catalog, episode=episode,
                shot=plan.shots_per_class, asset=asset,
            )
            _mask(
                fold["support_mask"], method=plan.method,
                source_settings=_mapping(candidate["source"], "candidate source settings"),
                support_settings=_mapping(candidate["support"], "candidate support settings"),
                support=True,
            )
            support_steps = _mapping(candidate["support"], "candidate support settings").get(
                "steps"
            )
            _finite_losses(
                fold["support_losses"], count=support_steps,
                name="LaBraM validation support losses",
            )
            if plan.method == "labram_lora" and (
                fold["component_policy"]
                != "continue_source_trained_lora_without_reinitialization"
                or
                fold["support_source_state_sha256"] != state
                or fold["source_settings_sha256"] != config_digest(candidate["source"])
            ):
                raise ValueError("LaBraM fold support source state or settings differ")
        score = _fold_score(
            fold.get("confusion_matrix"), classes=len(classes), query_count=len(query_ids)
        )
        if _fraction(fold.get("balanced_accuracy"), "fold score") != score:
            raise ValueError("fold rational score differs from the confusion matrix")
        per_candidate[name].append(score)
    if observed_pairs != expected_pairs:
        raise ValueError("candidate by source-subject fold coverage is incomplete")
    means = {
        name: sum(per_candidate[name], start=Fraction()) / len(selection.source_subjects)
        for name in names
    }
    scores = _rows(payload["scores"], "selection scores")
    if len(scores) != len(candidates):
        raise ValueError("selection scores differ from the candidate roster")
    for candidate, raw_score in zip(candidates, scores, strict=True):
        score_row = _mapping(raw_score, "selection score")
        name = candidate["name"]
        if score_row.get("candidate") != name or _fraction(
            score_row.get("mean_balanced_accuracy"), "mean source score"
        ) != means[name]:
            raise ValueError("selection mean score differs from the complete folds")
    winner = max(names, key=lambda name: means[name])
    if payload["selected_candidate"] != winner:
        raise ValueError("selected candidate differs from first-in-roster rational winner")
    selected = candidates_by_name[winner]
    if (
        selected["source"] != config_snapshot(adapter_source_settings)
        or selected["support"] != config_snapshot(adapter_support_settings)
    ):
        raise ValueError("selected candidate settings differ from the target adapter")
    final_state = _fit(
        payload["final_source_fit"], candidate=selected, validation_subject=None,
        training_subjects=selection.source_subjects,
        catalog_by_subject=catalog_by_subject, episodes=episodes, assets=assets,
        seed=plan.model_seed, method=plan.method,
    )
    if final_state != adapter_model_state_sha256:
        raise ValueError("final source checkpoint differs from the target adapter model")
    required = _required_complete_selection_steps(selection, candidates)
    if required > maximum_steps:
        raise ValueError(
            "complete Cho selector work exceeds the declared gradient-step ceiling: "
            f"{required} > {maximum_steps}"
        )
    return VerifiedChoSelection(winner, evidence_sha256)

