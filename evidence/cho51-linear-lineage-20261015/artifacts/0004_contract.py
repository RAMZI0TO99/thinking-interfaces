"""Pure metadata validation for two genuine, incomplete linear selector folds.

This module imports no project or model code and performs no I/O.  Its output
describes an incomplete lineage; it never authorizes reusing folds in a public
selector, declares a winner, or creates a recorder/publication success.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Sequence
from fractions import Fraction
from typing import Any


SCHEMA = "cho51_linear_partial_continuation_v1"
SUBJECTS = tuple(f"subject_{number:02d}" for number in range(1, 53))
SOURCES = tuple(subject for subject in SUBJECTS if subject != "subject_02")
TRAINING = tuple(subject for subject in SOURCES if subject != "subject_01")
CANDIDATES = ("lr_1e-3", "lr_2e-3")
COMPLETED = tuple((name, "subject_01") for name in CANDIDATES)
FULL_ROSTER = tuple((name, subject) for name in CANDIDATES for subject in SOURCES)
VARIANT_SHA256 = "6a3d5b9afca7bc0b82532276df1ef8f0a14db85da0eb609b5176ac967d04afb3"
CHANNELS = (
    "Fp1", "AF7", "AF3", "F1", "F3", "F5", "F7", "FT7", "FC5", "FC3", "FC1",
    "C1", "C3", "C5", "T7", "TP7", "CP5", "CP3", "CP1", "P1", "P3", "P5",
    "P7", "P9", "PO7", "PO3", "O1", "Iz", "Oz", "POz", "Pz", "CPz", "Fpz",
    "Fp2", "AF8", "AF4", "AFz", "Fz", "F2", "F4", "F6", "F8", "FT8", "FC6",
    "FC4", "FC2", "FCz", "Cz", "C2", "C4", "C6", "T8", "TP8", "CP6",
    "CP4", "CP2", "P2", "P4", "P6", "P8", "P10", "PO8", "PO4", "O2",
)
TRIAL_IDS = tuple(
    json.dumps(["synthetic_session", "synthetic_run", i], separators=(",", ":"))
    for i in range(42)
)


def _json(value: Any) -> str:
    """Use the public configuration digest's JSON encoding, rejecting aliases."""
    def visit(item: Any) -> None:
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                raise ValueError("JSON object keys must be strings")
            for member in item.values():
                visit(member)
        elif type(item) in (list, tuple):
            for member in item:
                visit(member)
        elif item is None or type(item) in (str, bool, int):
            return
        elif type(item) is float and math.isfinite(item):
            return
        else:
            raise ValueError("only finite JSON values are accepted")
    visit(value)
    return json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True)


def _sha(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _same(value: Any, expected: Any, label: str) -> None:
    if _json(value) != _json(expected):
        raise ValueError(label + " differs from the adopted contract")


def _object(value: Any, label: str, keys: set[str] | None = None) -> dict[str, Any]:
    if type(value) is not dict or (keys is not None and set(value) != keys):
        raise ValueError(label + " must have the exact object fields")
    return value


def _digest(value: Any, label: str) -> str:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(label + " must be a lowercase SHA-256 digest")
    return value


def _finite(value: Any, label: str) -> None:
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError(label + " must be finite and numeric")


def _expected_candidates() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "source": {
                "method": "linear", "steps_per_subject": 1, "batch_size": 2,
                "learning_rate": rate, "partial_depth": None,
            },
            "support": {
                "method": "linear", "steps": 1, "learning_rate": rate,
                "partial_depth": None, "query_batch_size": 8,
            },
        }
        for name, rate in zip(CANDIDATES, (0.001, 0.002), strict=True)
    ]


def _method_config(value: Any) -> dict[str, Any]:
    expected = {
        "method": "labram_linear", "dataset": "cho2017",
        "input_profile": "cho_profile_b_60hz_v1", "variant_config_sha256": VARIANT_SHA256,
        "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
        "source_seed_policy": "none", "score": "mean_subject_balanced_accuracy_exact_rational",
        "tie_break": "first_in_declared_candidate_order", "early_stopping": False,
        "candidates": _expected_candidates(),
    }
    _same(value, expected, "method configuration")
    return json.loads(_json(value))


def _mask(value: Any, label: str) -> None:
    _same(value, {
        "method": "linear", "depth": 0, "selected_blocks": [],
        "trainable_names": ["head.weight", "head.bias"],
        "trainable_parameters": 402, "head_policy": "existing_head_always_trainable",
        "support_normalization_policy": "all_modules_eval_affine_follows_parameter_mask",
    }, label)


def _catalog(binding: dict[str, Any], subject: str) -> dict[str, Any]:
    return {
        "dataset": "cho2017", "subject": subject, "trial_ids": list(TRIAL_IDS),
        "labels": ["left_hand", "right_hand"] * 21,
        "classes": ["left_hand", "right_hand"],
        "artifact_sha256": binding["profile_a_artifact_sha256"],
        "preprocessing_sha256": binding["profile_a_preprocessing_sha256"],
    }


def _episode_sha256(catalog: dict[str, Any], protocol_sha256: str) -> str:
    return _sha({
        "schema_version": 1, "phase": 2, "catalog": catalog,
        "protocol_sha256": protocol_sha256,
        "partitions": [
            {
                "shots_per_class": shots,
                "support_indices": list(range(shots * 2)), "query_indices": [40, 41],
                "unused_pool_indices": list(range(shots * 2, 40)),
            }
            for shots in (1, 5, 10, 20)
        ],
    })


def _binding(
    value: Any, *, subject: str, shots: int, contract: dict[str, Any], catalog_sha256: str,
) -> dict[str, Any]:
    keys = {
        "dataset", "subject", "shots_per_class", "classes", "channel_names",
        "protocol_sha256", "episode_sha256", "profile_a_artifact_sha256",
        "profile_b_artifact_sha256", "profile_b_manifest_sha256",
        "profile_a_preprocessing_sha256", "profile_b_config_sha256", "base_config_sha256",
        "support_trial_ids", "query_trial_ids", "support_profile_b_rows", "query_profile_b_rows",
        "input_trials", "profile_a_rejected_trials", "schema", "sampling_rate_hz",
        "samples_per_trial", "patch_samples", "stored_unit_volts", "extra_input_scale",
        "rejection_policy", "target_transform_fit", "profile_a_sidecar_manifests",
        "variant_config_sha256", "source_file", "source_sha256",
    }
    binding = _object(value, "profile binding", keys)
    fixed = {
        "dataset": "cho2017", "subject": subject, "shots_per_class": shots,
        "classes": ["left_hand", "right_hand"], "channel_names": list(CHANNELS),
        "protocol_sha256": contract["protocol_sha256"],
        "support_trial_ids": list(TRIAL_IDS[: shots * 2]), "query_trial_ids": list(TRIAL_IDS[40:]),
        "support_profile_b_rows": list(range(shots * 2)), "query_profile_b_rows": [40, 41],
        "input_trials": 42, "profile_a_rejected_trials": 0,
        "schema": "cho-a-to-b-episode-60hz-v1", "sampling_rate_hz": 200,
        "samples_per_trial": 800, "patch_samples": 200,
        "stored_unit_volts": 0.0001, "extra_input_scale": 1.0,
        "rejection_policy": "profile_a_frozen_threshold_only", "target_transform_fit": "none",
        "profile_a_sidecar_manifests": "absent_cho_identity_is_the_audited_catalog_hash",
        "variant_config_sha256": VARIANT_SHA256,
        "source_file": f"data/raw/moabb/cho2017/{subject}.mat",
    }
    _same({key: binding[key] for key in fixed}, fixed, "profile binding policy")
    for key, member in binding.items():
        if key.endswith("sha256"):
            _digest(member, key)
    assets = contract["profile_assets"][subject]
    _same({key: binding[key] for key in assets}, assets, "bound profile assets")
    catalog = _catalog(binding, subject)
    _same(_sha(catalog), catalog_sha256, "bound trial catalog")
    _same(binding["episode_sha256"], _episode_sha256(catalog, contract["protocol_sha256"]),
          "bound nested episode")
    return binding


def _contract(
    value: Any, method: dict[str, Any], template_sha256: str, initial_sha256: str,
) -> dict[str, Any]:
    keys = {
        "method", "dataset", "selection", "protocol_sha256", "profile_assets", "candidates",
        "head_and_sampling_seed", "shots_per_class", "maximum_gradient_steps",
        "template_state_sha256", "initial_state_sha256", "prior_template_training_verified",
        "initialization", "source_policy", "source_trial_pool", "extra_input_scale",
        "sampling_rate_hz", "samples_per_trial", "stored_unit_volts", "score", "tie_break",
        "early_stopping", "source", "runtime", "engineering_only", "scientific_evaluation",
    }
    contract = _object(value, "selector contract", keys)
    fixed = {
        "method": "labram_linear", "dataset": "cho2017", "candidates": method["candidates"],
        "head_and_sampling_seed": 11, "shots_per_class": 5, "maximum_gradient_steps": 5253,
        "template_state_sha256": template_sha256, "initial_state_sha256": initial_sha256,
        "prior_template_training_verified": False,
        "initialization": "pinned_supplied_backbone_and_fresh_seeded_linear_head",
        "source_policy": method["source_policy"],
        "source_trial_pool": "all_profile_a_retained_trials_joined_to_profile_b",
        "extra_input_scale": 1.0, "sampling_rate_hz": 200, "samples_per_trial": 800,
        "stored_unit_volts": 0.0001, "score": method["score"], "tie_break": method["tie_break"],
        "early_stopping": False, "engineering_only": True, "scientific_evaluation": False,
    }
    _same({key: contract[key] for key in fixed}, fixed, "selector policy")
    _digest(contract["protocol_sha256"], "protocol_sha256")
    selection = _object(contract["selection"], "source selection", {
        "dataset", "target_subject", "source_subjects", "inner_folds", "catalog_sha256",
    })
    fixed_selection = {
        "dataset": "cho2017", "target_subject": "subject_02", "source_subjects": list(SOURCES),
        "inner_folds": [
            {"training_subjects": [s for s in SOURCES if s != val], "validation_subject": val}
            for val in SOURCES
        ],
    }
    _same({key: selection[key] for key in fixed_selection}, fixed_selection, "full source selection")
    catalogs = selection["catalog_sha256"]
    if type(catalogs) is not list or len(catalogs) != 52:
        raise ValueError("all 52 catalog digests are required")
    for subject, row in zip(SUBJECTS, catalogs, strict=True):
        if type(row) is not list or len(row) != 2 or row[0] != subject:
            raise ValueError("catalog roster must retain all 52 ordered subjects")
        _digest(row[1], "catalog_sha256")
    assets = _object(contract["profile_assets"], "profile assets", set(SUBJECTS))
    for subject in SUBJECTS:
        asset = _object(assets[subject], "subject profile assets", {
            "profile_b_artifact_sha256", "profile_b_manifest_sha256", "variant_config_sha256",
        })
        for key, member in asset.items():
            _digest(member, key)
        _same(asset["variant_config_sha256"], VARIANT_SHA256, "profile variant")
    source = _object(contract["source"], "source provenance", {
        "git_commit", "source_sha256", "git_dirty",
    })
    _digest(source["source_sha256"], "source fingerprint")
    if (
        type(source["git_commit"]) is not str
        or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", source["git_commit"]) is None
        or type(source["git_dirty"]) is not bool
    ):
        raise ValueError("real explicit Git source identity required")
    runtime = _object(contract["runtime"], "CPU runtime", {
        "python", "torch", "numpy", "braindecode", "device", "dtype", "torch_threads",
        "deterministic_algorithms",
    })
    _same({key: runtime[key] for key in ("device", "dtype", "torch_threads")}, {
        "device": "cpu", "dtype": "float32", "torch_threads": 1,
    }, "CPU runtime")
    if type(runtime["deterministic_algorithms"]) is not bool or any(
        type(runtime[key]) is not str or not runtime[key].strip()
        for key in ("python", "torch", "numpy", "braindecode")
    ):
        raise ValueError("explicit runtime versions and deterministic flag required")
    return contract


def _fold(value: Any, candidate: dict[str, Any], contract: dict[str, Any]) -> None:
    fold = _object(value, "fold", {
        "candidate", "validation_subject", "source_fit", "binding", "support_mask",
        "support_losses", "adapted_state_sha256", "confusion_matrix", "balanced_accuracy",
    })
    _same([fold["candidate"], fold["validation_subject"]], [candidate["name"], "subject_01"],
          "requested fold pair")
    fit = _object(fold["source_fit"], "source fit", {
        "candidate", "candidate_sha256", "validation_subject", "training_subjects",
        "input_identities", "head_and_sampling_seed", "settings", "mask", "optimizer",
        "normalization_and_dropout", "initial_state_sha256", "fitted_state_sha256", "steps",
        "history_scope", "engineering_only",
    })
    fixed = {
        "candidate": candidate["name"], "candidate_sha256": _sha(candidate),
        "validation_subject": "subject_01", "training_subjects": list(TRAINING),
        "head_and_sampling_seed": 11, "settings": candidate["source"],
        "optimizer": {"name": "SGD", "momentum": 0, "weight_decay": 0, "fresh": True},
        "normalization_and_dropout": "all_modules_eval_affine_follows_mask",
        "initial_state_sha256": contract["initial_state_sha256"],
        "history_scope": "complete_for_this_bounded_fit_only", "engineering_only": True,
    }
    _same({key: fit[key] for key in fixed}, fixed, "source fit contract")
    _mask(fit["mask"], "source mask")
    _mask(fold["support_mask"], "support mask")
    catalogs = dict(contract["selection"]["catalog_sha256"])
    identities = _object(fit["input_identities"], "source input identities", set(TRAINING))
    for subject in TRAINING:
        identity = _object(identities[subject], "source input identity", {"catalog_sha256", "binding"})
        _same(identity["catalog_sha256"], catalogs[subject], "source catalog")
        _binding(identity["binding"], subject=subject, shots=20,
                 contract=contract, catalog_sha256=catalogs[subject])
    history = fit["steps"]
    if type(history) is not list or len(history) != 50:
        raise ValueError("each bounded fold must have all 50 source SGD steps")
    previous = fit["initial_state_sha256"]
    for step, (subject, value) in enumerate(zip(TRAINING, history, strict=True), start=1):
        row = _object(value, "source step", {
            "step", "subject", "trial_ids", "subject_step", "iterator_wraps", "loss",
            "state_sha256_after",
        })
        _same({key: row[key] for key in ("step", "subject", "subject_step", "iterator_wraps")},
              {"step": step, "subject": subject, "subject_step": 1, "iterator_wraps": 0},
              "ordered source history")
        ids = row["trial_ids"]
        if (
            type(ids) is not list or len(ids) != 2 or any(type(member) is not str for member in ids)
            or len(set(ids)) != 2 or any(member not in TRIAL_IDS for member in ids)
        ):
            raise ValueError("source SGD must name two distinct bound retained trials")
        _finite(row["loss"], "source loss")
        current = _digest(row["state_sha256_after"], "source step state")
        if current == previous:
            raise ValueError("every recorded source SGD step must change the state digest")
        previous = current
    _same(fit["fitted_state_sha256"], previous, "final source history state")
    if previous == fit["initial_state_sha256"]:
        raise ValueError("the completed source fit must change its initial state digest")
    losses = fold["support_losses"]
    if type(losses) is not list or len(losses) != 1:
        raise ValueError("exactly one support SGD loss is required")
    _finite(losses[0], "support loss")
    adapted = _digest(fold["adapted_state_sha256"], "adapted state")
    if adapted == previous:
        raise ValueError("support SGD must change its fitted source state")
    _binding(fold["binding"], subject="subject_01", shots=5,
             contract=contract, catalog_sha256=catalogs["subject_01"])
    confusion = fold["confusion_matrix"]
    if (
        type(confusion) is not list or len(confusion) != 2
        or any(type(row) is not list or len(row) != 2 for row in confusion)
        or any(type(n) is not int or n < 0 for row in confusion for n in row)
        or any(sum(row) != 1 for row in confusion)
    ):
        raise ValueError("two held-out queries must produce one entry per class")
    score = sum((Fraction(confusion[i][i], sum(confusion[i])) for i in range(2)), Fraction()) / 2
    _same(fold["balanced_accuracy"], [score.numerator, score.denominator],
          "exact reduced rational balanced accuracy")


def collect_partial(
    records: Sequence[dict[str, Any]], method_config: dict[str, Any], *,
    input_identity_sha256: str, template_state_sha256: str, initial_state_sha256: str,
    lineage_recipe_sha256: str,
) -> dict[str, Any]:
    """Validate two raw public ``run_fold`` envelopes, returning a detached manifest.

    The four keyword pins must come from the caller's independently verified
    input/template/recipe records.  Self-consistent metadata alone is never
    model execution, restoration, scientific evidence, or continuation authority.
    """
    for label, value in (
        ("input_identity_sha256", input_identity_sha256),
        ("template_state_sha256", template_state_sha256),
        ("initial_state_sha256", initial_state_sha256),
        ("lineage_recipe_sha256", lineage_recipe_sha256),
    ):
        _digest(value, label)
    method = _method_config(method_config)
    if type(records) not in (tuple, list) or len(records) != 2:
        raise ValueError("exactly two raw fold records are required")
    # JSON snapshot prevents return aliases and rejects nonfinite/unsupported input.
    records = json.loads(_json(records))
    accepted: dict[tuple[str, str], dict[str, Any]] = {}
    common_contract: dict[str, Any] | None = None
    contract_sha256: str | None = None
    for record in records:
        _object(record, "engineering envelope", {"schema_version", "phase", "kind", "payload", "sha256"})
        _same({key: record[key] for key in ("schema_version", "phase", "kind")},
              {"schema_version": 1, "phase": 2, "kind": "engineering_smoke"}, "engineering envelope")
        content = {key: value for key, value in record.items() if key != "sha256"}
        _same(record["sha256"], _sha(content), "engineering envelope SHA-256")
        payload = _object(record["payload"], "partial fold payload", {
            "purpose", "contract", "contract_sha256", "complete", "folds", "selected_candidate",
        })
        _same({key: payload[key] for key in ("purpose", "complete", "selected_candidate")}, {
            "purpose": "bounded_labram_source_selection", "complete": False, "selected_candidate": None,
        }, "partial evidence boundary")
        contract = _contract(payload["contract"], method, template_state_sha256, initial_state_sha256)
        _same(payload["contract_sha256"], _sha(contract), "selector contract SHA-256")
        if common_contract is None:
            common_contract, contract_sha256 = contract, payload["contract_sha256"]
        else:
            _same(contract, common_contract, "shared selector contract")
        folds = payload["folds"]
        if type(folds) is not list or len(folds) != 1:
            raise ValueError("a raw run_fold record must contain exactly one fold")
        fold = _object(folds[0], "raw fold")
        pair = (fold.get("candidate"), fold.get("validation_subject"))
        if any(type(member) is not str for member in pair) or pair not in COMPLETED or pair in accepted:
            raise ValueError("unexpected, missing or duplicate requested fold pair")
        candidate = next(item for item in method["candidates"] if item["name"] == pair[0])
        _fold(fold, candidate, contract)
        accepted[pair] = record
    if set(accepted) != set(COMPLETED):
        raise ValueError("both declared candidate/subject_01 folds are required")
    assert common_contract is not None and contract_sha256 is not None
    result = {
        "schema": SCHEMA, "method": "labram_linear", "dataset": "cho2017",
        "outer_target": "subject_02", "model_seed": 11, "shots_per_class": 5, "repetition": 1,
        "method_config_sha256": _sha(method), "contract_sha256": contract_sha256,
        "source_sha256": common_contract["source"]["source_sha256"],
        "runtime_sha256": _sha(common_contract["runtime"]),
        "input_identity_sha256": input_identity_sha256, "template_state_sha256": template_state_sha256,
        "initial_state_sha256": initial_state_sha256, "lineage_recipe_sha256": lineage_recipe_sha256,
        "prior_template_training_verified": False,
        "expected_folds": 102, "accepted_folds": 2, "pending_folds": 100,
        "full_gradient_updates": 5253, "full_source_updates": 5151, "full_support_updates": 102,
        "executed_source_updates": 100, "executed_support_updates": 2, "executed_gradient_updates": 102,
        "fresh_final_source_updates_required": 51,
        "completed_pairs": [{"candidate": name, "validation_subject": subject} for name, subject in COMPLETED],
        "full_roster": [{"candidate": name, "validation_subject": subject} for name, subject in FULL_ROSTER],
        "record_sha256": {
            name + "/" + subject: accepted[(name, subject)]["sha256"] for name, subject in COMPLETED
        },
        "complete": False, "selected_candidate": None, "full_selector_qualified": False,
        "final_fit_qualified": False, "publication_qualified": False,
        "source_work_reused": False, "reuse_authorized": False,
        "engineering_only": True, "scientific_evaluation": False,
        "original_case_attempts": 0,
    }
    return json.loads(_json({**result, "sha256": _sha(result)}))
