"""Bind complete Cho source-selection evidence to one intended target adapter.

This is a read-only engineering evidence check. It does not train, load signals,
admit compute, or turn an exploratory record into a scientific freeze decision.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import torch

from core.config import config_digest, config_snapshot
from core.provenance import capture_source
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz, dataset_cohort
from evaluation.phase2_protocol import (
    EpisodeManifest,
    SourceSelection,
    TrialCatalog,
    nested_episode,
    require_digest,
    selection_gradient_ceiling,
    source_selection,
)
from evaluation.phase2_records import verify_envelope
from evaluation.phase2_runner import CasePlan
from scripts.audit_phase2_protocol import validate_protocol

CHO_METHODS = frozenset({"labram_linear", "labram_lora", "labram_full", "eegnet"})
_PAYLOAD_KEYS = frozenset({
    "purpose", "contract", "contract_sha256", "complete", "folds",
    "selected_candidate", "scores", "final_source_fit",
    "outer_target_predictions_performed",
})
_EEGNET_FOLD_KEYS = frozenset({
    "candidate", "validation_subject", "source_fit", "episode_sha256",
    "support_trial_ids", "query_trial_ids", "input_identities", "support_fit",
    "adapted_state_sha256", "confusion_matrix", "balanced_accuracy",
})
_LABRAM_FOLD_KEYS = frozenset({
    "candidate", "validation_subject", "source_fit", "binding", "support_mask",
    "support_losses", "adapted_state_sha256", "confusion_matrix", "balanced_accuracy",
})
_LORA_EXTRA_KEYS = frozenset({
    "component_policy", "support_source_state_sha256", "source_settings_sha256",
})


@dataclass(frozen=True, slots=True)
class VerifiedChoSelection:
    selected_candidate: str
    evidence_sha256: str


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(k, str) for k in value):
        raise ValueError(f"{name} must be a string-keyed mapping")
    return value


def _rows(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a digest string")
    require_digest(value, name)
    return value


def _fraction(value: Any, name: str) -> Fraction:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(type(number) is not int for number in value)
        or value[1] < 1
        or not 0 <= value[0] <= value[1]
    ):
        raise ValueError(f"{name} must be a bounded rational pair")
    fraction = Fraction(value[0], value[1])
    if value != [fraction.numerator, fraction.denominator]:
        raise ValueError(f"{name} must be in lowest terms")
    return fraction


def _fold_score(value: Any, *, classes: int, query_count: int) -> Fraction:
    matrix = _rows(value, "fold confusion matrix")
    if len(matrix) != classes:
        raise ValueError("fold confusion matrix class count differs")
    rows: list[list[int]] = []
    for row in matrix:
        if (
            not isinstance(row, list)
            or len(row) != classes
            or any(type(number) is not int or number < 0 for number in row)
            or sum(row) < 1
        ):
            raise ValueError("fold confusion matrix requires observed nonnegative class rows")
        rows.append(row)
    if sum(map(sum, rows)) != query_count:
        raise ValueError("fold confusion matrix query count differs")
    return sum(
        (Fraction(rows[index][index], sum(rows[index])) for index in range(classes)),
        start=Fraction(),
    ) / classes


def _finite_losses(value: Any, *, count: Any, name: str) -> None:
    losses = _rows(value, name)
    if (
        type(count) is not int
        or count < 1
        or len(losses) != count
        or any(type(loss) not in (int, float) or not math.isfinite(loss)
               for loss in losses)
    ):
        raise ValueError(f"{name} must contain the declared finite steps")


def _cho_binding(
    raw: Any, *, catalog: TrialCatalog, episode: EpisodeManifest,
    shot: int, asset: ChoProfileAssets60Hz,
) -> None:
    binding = _mapping(raw, "Cho 60 Hz binding")
    partition = episode.partition(shot)
    support = [catalog.trial_ids[index] for index in partition.support_indices]
    query = [catalog.trial_ids[index] for index in partition.query_indices]
    if (
        binding.get("dataset") != "cho2017"
        or binding.get("subject") != catalog.subject
        or binding.get("shots_per_class") != shot
        or binding.get("protocol_sha256") != episode.protocol_sha256
        or binding.get("episode_sha256") != episode.sha256
        or binding.get("support_trial_ids") != support
        or binding.get("query_trial_ids") != query
        or binding.get("profile_a_artifact_sha256") != catalog.artifact_sha256
        or binding.get("profile_a_preprocessing_sha256") != catalog.preprocessing_sha256
        or binding.get("profile_b_artifact_sha256") != asset.profile_b_artifact_sha256
        or binding.get("profile_b_manifest_sha256") != asset.profile_b_manifest_sha256
        or binding.get("variant_config_sha256") != asset.variant_config_sha256
        or binding.get("schema") != "cho-a-to-b-episode-60hz-v1"
        or binding.get("sampling_rate_hz") != 200
        or binding.get("samples_per_trial") != 800
        or binding.get("stored_unit_volts") != 0.0001
    ):
        raise ValueError("Cho 60 Hz binding differs from catalog, episode or assets")
    _digest(binding.get("profile_b_config_sha256"), "Cho Profile B config")
    _digest(binding.get("base_config_sha256"), "Cho base config")
    _digest(binding.get("source_sha256"), "Cho raw source")
    source_file = binding.get("source_file")
    if not isinstance(source_file, str) or not source_file.startswith(
        "data/raw/moabb/cho2017/"
    ) or "\\" in source_file:
        raise ValueError("Cho 60 Hz raw source path differs")
    if shot == episode.partitions[-1].shots_per_class and (
        len(support) + len(query) != len(catalog.trial_ids)
        or set(support + query) != set(catalog.trial_ids)
    ):
        raise ValueError("maximum-shot source binding omits retained trials")


def _mask(
    raw: Any, *, method: str, source_settings: Mapping[str, Any],
    support_settings: Mapping[str, Any], support: bool,
) -> None:
    mask = _mapping(raw, "LaBraM trainable mask")
    names = _rows(mask.get("trainable_names"), "LaBraM trainable names")
    if (
        not names
        or any(not isinstance(name, str) or not name for name in names)
        or len(set(names)) != len(names)
        or type(mask.get("trainable_parameters")) is not int
        or mask["trainable_parameters"] < 1
    ):
        raise ValueError("LaBraM trainable mask is incomplete")
    if method == "labram_lora":
        head_policy = (
            support_settings.get("train_head") if support else source_settings.get("train_head")
        )
        if (
            mask.get("method") != "lora"
            or mask.get("target_modules") != source_settings.get("target_modules")
            or mask.get("rank") != source_settings.get("rank")
            or mask.get("alpha") != source_settings.get("alpha")
            or mask.get("train_head") is not head_policy
            or mask.get("support_normalization_policy")
            != "all_modules_eval_source_affine_and_buffers_frozen"
            or type(mask.get("adapter_parameters")) is not int
            or not 0 < mask["adapter_parameters"] <= mask["trainable_parameters"]
        ):
            raise ValueError("LoRA source or support mask differs from selected settings")
    else:
        tuning = method.removeprefix("labram_")
        blocks = mask.get("selected_blocks")
        valid_blocks = (
            isinstance(blocks, list)
            and (blocks == [] if tuning == "linear" else (
                bool(blocks) and blocks == list(range(len(blocks)))
            ))
        )
        if not valid_blocks:
            raise ValueError("plain LaBraM selected blocks differ")
        if (
            mask.get("method") != tuning
            or mask.get("depth") != (0 if tuning == "linear" else "all")
            or mask.get("head_policy") != "existing_head_always_trainable"
            or mask.get("support_normalization_policy")
            != "all_modules_eval_affine_follows_parameter_mask"
        ):
            raise ValueError("plain LaBraM source or support mask differs")


def _fit(
    raw: Any,
    *,
    candidate: Mapping[str, Any],
    validation_subject: str | None,
    training_subjects: tuple[str, ...],
    catalog_by_subject: Mapping[str, TrialCatalog],
    episodes: Mapping[str, EpisodeManifest],
    assets: Mapping[str, Any],
    seed: int,
    method: str,
) -> str:
    fit = _mapping(raw, "source fit")
    source_settings = _mapping(candidate["source"], "candidate source settings")
    if (
        fit.get("candidate") != candidate["name"]
        or fit.get("candidate_sha256") != config_digest(candidate)
        or fit.get("validation_subject") != validation_subject
        or fit.get("training_subjects") != list(training_subjects)
        or fit.get("settings") != source_settings
        or fit.get("engineering_only") is not True
        or fit.get("history_scope") != "complete_for_this_bounded_fit_only"
    ):
        raise ValueError("source fit differs from candidate or permitted subjects")
    seed_field = "model_and_sampling_seed" if method == "eegnet" else "head_and_sampling_seed"
    fit_seed_field = "seed" if method == "eegnet" else seed_field
    if fit.get(fit_seed_field) != seed or type(fit.get(fit_seed_field)) is not int:
        raise ValueError("source fit seed differs")
    identities = _mapping(fit.get("input_identities"), "source input identities")
    if set(identities) != set(training_subjects):
        raise ValueError("source fit input identities differ from permitted subjects")
    for subject in training_subjects:
        identity = _mapping(identities[subject], "source input identity")
        catalog = catalog_by_subject[subject]
        if identity.get("catalog_sha256") != catalog.sha256:
            raise ValueError("source fit input differs from catalog")
        if method == "eegnet":
            if identity.get("artifact_sha256") != catalog.artifact_sha256:
                raise ValueError("EEGNet source fit input differs from Profile A catalog")
            _digest(identity.get("manifest_sha256"), "EEGNet source manifest")
            _digest(identity.get("base_config_sha256"), "EEGNet base config")
        else:
            asset = assets[subject]
            if not isinstance(asset, ChoProfileAssets60Hz):
                raise ValueError("LaBraM source input requires typed 60 Hz assets")
            _cho_binding(
                identity.get("binding"), catalog=catalog, episode=episodes[subject],
                shot=episodes[subject].partitions[-1].shots_per_class, asset=asset,
            )
    if fit.get("optimizer") != {
        "name": "SGD", "momentum": 0, "weight_decay": 0, "fresh": True,
    }:
        raise ValueError("source fit optimizer differs from selector policy")
    _digest(fit.get("initial_state_sha256"), "initial source state")
    if method == "eegnet":
        if fit.get("normalization_and_dropout") != "all_modules_eval":
            raise ValueError("EEGNet source fit normalization differs")
    else:
        if fit.get("normalization_and_dropout") != "all_modules_eval_affine_follows_mask":
            raise ValueError("LaBraM source fit normalization differs")
        _mask(
            fit.get("mask"), method=method, source_settings=source_settings,
            support_settings=_mapping(candidate["support"], "candidate support settings"),
            support=False,
        )
    steps_per_subject = source_settings.get("steps_per_subject")
    if type(steps_per_subject) is not int or steps_per_subject < 1:
        raise ValueError("candidate source step count must be positive")
    batch_size = source_settings.get("batch_size")
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("candidate source batch size must be positive")
    history = _rows(fit.get("steps"), "source fit steps")
    if len(history) != len(training_subjects) * steps_per_subject:
        raise ValueError("source fit step history is incomplete")
    # Both Cho selectors reset this isolated CPU generator for each source fit,
    # then consume one randperm per permitted subject in source order. A wrap
    # cycles through that same permutation; it never draws a fresh one.
    sampling = torch.Generator(device="cpu").manual_seed(seed)
    permutation: list[int] = []
    for index, raw_step in enumerate(history):
        step = _mapping(raw_step, "source fit step")
        if (
            step.get("step") != index + 1
            or step.get("subject") != training_subjects[index // steps_per_subject]
            or step.get("subject_step") != index % steps_per_subject + 1
        ):
            raise ValueError("source fit step order differs")
        subject = training_subjects[index // steps_per_subject]
        trial_ids = _rows(step.get("trial_ids"), "source step trial identities")
        catalog_trial_ids = catalog_by_subject[subject].trial_ids
        if (
            len(trial_ids) != batch_size
            or any(not isinstance(trial, str) for trial in trial_ids)
            or len(set(trial_ids)) != len(trial_ids)
            or any(trial not in catalog_trial_ids for trial in trial_ids)
        ):
            raise ValueError("source fit step trials differ from its permitted subject")
        subject_step = index % steps_per_subject
        if subject_step == 0:
            permutation = torch.randperm(
                len(catalog_trial_ids), generator=sampling
            ).tolist()
        expected_trials = [
            catalog_trial_ids[permutation[position % len(permutation)]]
            for position in range(
                subject_step * batch_size, (subject_step + 1) * batch_size
            )
        ]
        if trial_ids != expected_trials:
            raise ValueError("source fit step sampling differs from the seeded iterator")
        expected_wraps = (
            ((subject_step + 1) * batch_size - 1)
            // len(catalog_trial_ids)
        )
        loss = step.get("loss")
        if (
            step.get("iterator_wraps") != expected_wraps
            or type(step.get("iterator_wraps")) is not int
            or not isinstance(loss, (int, float))
            or isinstance(loss, bool)
            or not math.isfinite(loss)
        ):
            raise ValueError("source fit step wrap or loss differs")
        _digest(step.get("state_sha256_after"), "source step state")
    fitted = _digest(fit.get("fitted_state_sha256"), "fitted source state")
    if history[-1]["state_sha256_after"] != fitted:
        raise ValueError("final source state differs from last training step")
    return fitted


def _required_complete_selection_steps(
    selection: SourceSelection, candidates: Sequence[Mapping[str, Any]],
) -> int:
    """Match both selectors' full-run admission bound, including the final fit."""
    sources = len(selection.source_subjects)
    if sources != len(selection.inner_folds) or not candidates:
        raise ValueError("complete source selection has invalid folds or candidates")
    counts = []
    for candidate in candidates:
        source = _mapping(candidate.get("source"), "candidate source settings")
        support = _mapping(candidate.get("support"), "candidate support settings")
        source_steps = source.get("steps_per_subject")
        support_steps = support.get("steps")
        if (
            type(source_steps) is not int or source_steps < 1
            or type(support_steps) is not int or support_steps < 1
        ):
            raise ValueError("complete selection requires positive source and support steps")
        counts.append((source_steps, support_steps))
    return sum(
        sources * ((sources - 1) * source_steps + support_steps)
        for source_steps, support_steps in counts
    ) + sources * max(source_steps for source_steps, _ in counts)


def _verify_cho_selection_structure(
    *,
    record: Mapping[str, Any],
    evidence_sha256: str,
    plan: CasePlan,
    protocol_config: Mapping[str, Any],
    catalogs: tuple[TrialCatalog, ...],
    selection_record: Mapping[str, Any],
    assets: Mapping[str, Any],
    root: Path,
    adapter_model_state_sha256: str,
    adapter_source_settings: Mapping[str, Any],
    adapter_support_settings: Mapping[str, Any],
) -> VerifiedChoSelection:
    """Check complete-record coherence without admitting its compute budget.

    This private seam preserves structural test coverage for a 52-subject record
    whose minimum complete run already exceeds the engineering step ceiling.
    Production target admission must call verify_cho_selection_evidence instead.
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
    source = asdict(capture_source(root.resolve()))
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
    return VerifiedChoSelection(winner, evidence_sha256)


def verify_cho_selection_evidence(
    *,
    record: Mapping[str, Any],
    evidence_sha256: str,
    plan: CasePlan,
    protocol_config: Mapping[str, Any],
    catalogs: tuple[TrialCatalog, ...],
    selection_record: Mapping[str, Any],
    assets: Mapping[str, Any],
    root: Path,
    adapter_model_state_sha256: str,
    adapter_source_settings: Mapping[str, Any],
    adapter_support_settings: Mapping[str, Any],
) -> VerifiedChoSelection:
    """Admit complete Cho evidence only if its full selector work fit the hard cap.

    The adapter digest must come from the actual fitted model. Settings must
    describe the adapter that will be called. Structural coherence alone is
    insufficient: both selectors pre-admit every fold and the final source fit.
    """
    verified = _verify_cho_selection_structure(
        record=record,
        evidence_sha256=evidence_sha256,
        plan=plan,
        protocol_config=protocol_config,
        catalogs=catalogs,
        selection_record=selection_record,
        assets=assets,
        root=root,
        adapter_model_state_sha256=adapter_model_state_sha256,
        adapter_source_settings=adapter_source_settings,
        adapter_support_settings=adapter_support_settings,
    )
    payload = _mapping(record["payload"], "selection evidence payload")
    contract = _mapping(payload["contract"], "selection contract")
    maximum_steps = contract["maximum_gradient_steps"]
    candidates = [
        _mapping(candidate, "candidate")
        for candidate in _rows(contract["candidates"], "candidate roster")
    ]
    selection = source_selection(catalogs, target=plan.target_subject)
    required = _required_complete_selection_steps(selection, candidates)
    if required > maximum_steps:
        raise ValueError(
            "complete Cho selector work exceeds the declared gradient-step ceiling: "
            f"{required} > {maximum_steps}"
        )
    return verified
