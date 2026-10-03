"""Derive the static Cho method template from a selector's recorded roster.

The derived template still needs an independently reviewed digest. Derivation
does not verify the selector's folds, fitted checkpoint, or scientific freeze.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from core.config import config_snapshot
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz
from evaluation.phase2_runner import CasePlan, method_configuration

SOURCE_POLICY = "all_non_target_subjects; inner_validation_also_excluded"
SCORE = "mean_subject_balanced_accuracy_exact_rational"
TIE_BREAK = "first_in_declared_candidate_order"
_CHO_METHODS = frozenset({"labram_linear", "labram_lora", "labram_full", "eegnet"})


def derive_cho_method_template(
    plan: CasePlan,
    contract: Mapping[str, Any],
    assets: Mapping[str, Any],
) -> dict[str, Any]:
    """Build and schema-check one case's static two-candidate method template."""
    if (
        not isinstance(plan, CasePlan)
        or plan.dataset != "cho2017" or plan.method not in _CHO_METHODS
        or not isinstance(contract, Mapping)
        or not isinstance(assets, Mapping)
    ):
        raise ValueError("a typed Cho plan, selector contract and assets are required")
    profile = "cho_profile_a" if plan.method == "eegnet" else "cho_profile_b_60hz_v1"
    variant: str | None = None
    if plan.method != "eegnet":
        if len(assets) != 52 or any(
            not isinstance(asset, ChoProfileAssets60Hz) for asset in assets.values()
        ):
            raise ValueError("complete typed 60 Hz assets are required")
        variants = {asset.variant_config_sha256 for asset in assets.values()}
        if len(variants) != 1:
            raise ValueError("60 Hz variant config differs within the cohort")
        variant = next(iter(variants))
    candidates = config_snapshot({"rows": contract.get("candidates")}).get("rows")
    if not isinstance(candidates, list):
        raise ValueError("selector candidate roster is missing")
    seed_policy = "none"
    if plan.method == "labram_lora":
        seed_policy = "case_model_seed"
        for candidate in candidates:
            if not isinstance(candidate, dict) or not isinstance(candidate.get("source"), dict):
                raise ValueError("LoRA candidate shape differs")
            source_settings = cast(dict[str, Any], candidate["source"])
            if source_settings.get("seed") != plan.model_seed:
                raise ValueError("LoRA source seed differs from the planned model seed")
            source_settings["seed"] = "$case_model_seed"
    expected: dict[str, Any] = {
        "method": plan.method,
        "dataset": "cho2017",
        "input_profile": profile,
        "variant_config_sha256": variant,
        "candidates": candidates,
        "source_seed_policy": seed_policy,
        "source_policy": SOURCE_POLICY,
        "score": SCORE,
        "tie_break": TIE_BREAK,
        "early_stopping": False,
    }
    method_configuration(expected)
    return expected
