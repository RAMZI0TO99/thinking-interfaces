"""Pure first-tranche Cho identity checks before recorder or analysis admission.

The route's catalogs and externally reviewed method digest map are inputs, not
proof of their own origin. This module reads no scores, recorder files, signals,
selection evidence, checkpoints, or runtime environment. Callers must verify
those, the persisted protocol/asset bytes, and the scientific analysis freeze
separately before admitting any cell or reporting a scientific result.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any

from core.config import canonical_config_json, config_digest
from core.provenance import SourceProvenance
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell
from evaluation.phase2_cho_case_inputs import (
    CHO_SUBJECTS,
    SELECTED_METHODS,
    SELECTED_SEEDS,
    SELECTED_SHOTS,
    ChoFirstTrancheRoute,
)
from evaluation.phase2_profile_binding import CHO_CLASSES, ChoProfileAssets60Hz
from evaluation.phase2_protocol import (
    TrialCatalog,
    nested_episode,
    require_digest,
    source_selection,
)
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_subject_aggregation import ExpectedCell
from scripts.audit_phase2_protocol import validate_protocol


def _protocol(route: ChoFirstTrancheRoute) -> tuple[dict[str, Any], tuple[int, ...]]:
    if not isinstance(route.protocol_config_json, str):
        raise ValueError("route protocol must be canonical JSON")
    try:
        config = json.loads(route.protocol_config_json)
        if (
            not isinstance(config, dict)
            or canonical_config_json(config) != route.protocol_config_json
        ):
            raise ValueError("route protocol must be canonical JSON")
        shots = validate_protocol(config)
        cho = config["datasets"]["cho2017"]
        if (
            cho.get("artifact_directory") != "data/processed/cho2017/profile_a"
            or tuple(cho.get("classes", ())) != CHO_CLASSES
            or type(cho.get("expected_subjects")) is not int
            or cho["expected_subjects"] != len(CHO_SUBJECTS)
            or tuple(config["protocol"].get("model_seeds", ())) != SELECTED_SEEDS
            or SELECTED_SHOTS not in shots
        ):
            raise ValueError("route protocol differs from the Cho first tranche")
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
        raise ValueError("route protocol differs from the Cho first tranche") from error
    return config, shots


def _source(source: SourceProvenance) -> None:
    if not isinstance(source, SourceProvenance):
        raise ValueError("expected source must be independently supplied provenance")
    require_digest(source.source_sha256, "expected source")
    if (
        not isinstance(source.git_commit, str)
        or len(source.git_commit) not in (40, 64)
        or any(character not in "0123456789abcdef" for character in source.git_commit)
        or type(source.git_dirty) is not bool
    ):
        raise ValueError("expected source needs a real commit and known dirty state")


def verify_cho_case_identity_bindings(
    route: ChoFirstTrancheRoute,
    pins: Sequence[PinnedCaseCell],
    *,
    method_config_sha256: Mapping[str, str],
    expected_source: SourceProvenance | None = None,
) -> None:
    """Require exact proposed 52 x 4 x 5 identity coverage and reconstructed hashes.

    ``method_config_sha256`` must be an independently reviewed four-method map.
    All pins must agree on source identity, but omitting ``expected_source``
    leaves that common source unverified. When supplied, it must be independently
    captured and pinned; no historical authority is inferred from the cells.
    This check does not bind per-subject Profile B artifact or manifest bytes or
    prove that cells used those assets. The caller separately verifies route
    preparation, persisted selection evidence, chosen source checkpoints,
    environment, recorder publication and scientific analysis freeze. No cell
    score is read and no scientific admission is made.
    """
    if not isinstance(route, ChoFirstTrancheRoute):
        raise ValueError("a typed Cho first-tranche route is required")
    if (
        not isinstance(pins, Sequence)
        or isinstance(pins, (str, bytes))
        or not isinstance(method_config_sha256, Mapping)
        or set(method_config_sha256) != set(SELECTED_METHODS)
    ):
        raise ValueError("typed pins and exact four-method digest map are required")
    for method in SELECTED_METHODS:
        require_digest(method_config_sha256[method], f"{method} configuration")
    if expected_source is not None:
        _source(expected_source)

    config, shots = _protocol(route)
    protocol_sha256 = config_digest(config)
    expected_plans = tuple(
        CasePlan("cho2017", subject, method, SELECTED_SHOTS, seed, 1)
        for subject in CHO_SUBJECTS
        for method in SELECTED_METHODS
        for seed in SELECTED_SEEDS
    )
    if (
        not isinstance(route.plans, tuple)
        or route.plans != expected_plans
        or len(route.plans) != 1040
        or not isinstance(route.catalogs, tuple)
        or len(route.catalogs) != len(CHO_SUBJECTS)
        or any(not isinstance(catalog, TrialCatalog) for catalog in route.catalogs)
        or tuple(catalog.subject for catalog in route.catalogs) != CHO_SUBJECTS
        or any(catalog.dataset != "cho2017" or catalog.classes != CHO_CLASSES
               for catalog in route.catalogs)
        or not isinstance(route.labram_assets, Mapping)
        or set(route.labram_assets) != set(CHO_SUBJECTS)
        or any(not isinstance(asset, ChoProfileAssets60Hz)
               for asset in route.labram_assets.values())
        or not isinstance(route.selection_records_json, Mapping)
        or set(route.selection_records_json) != set(CHO_SUBJECTS)
        or not isinstance(route.episode_records_json, Mapping)
        or set(route.episode_records_json) != set(CHO_SUBJECTS)
    ):
        raise ValueError("route is not the complete typed Cho first tranche")
    if (
        len({catalog.preprocessing_sha256 for catalog in route.catalogs}) != 1
        or len({asset.variant_config_sha256 for asset in route.labram_assets.values()}) != 1
    ):
        raise ValueError("route catalog preprocessing or Profile B variant differs")

    expected_selection: dict[str, str] = {}
    expected_episode: dict[str, str] = {}
    catalogs = {catalog.subject: catalog for catalog in route.catalogs}
    for subject in CHO_SUBJECTS:
        selection = envelope(
            "source_selection", asdict(source_selection(route.catalogs, target=subject))
        )
        episode = envelope(
            "episode_manifest",
            nested_episode(
                catalogs[subject], shots=shots, protocol_sha256=protocol_sha256,
            ).payload(),
        )
        if (
            route.selection_records_json[subject] != canonical_config_json(selection)
            or route.episode_records_json[subject] != canonical_config_json(episode)
        ):
            raise ValueError(f"route records differ from reconstructed {subject} records")
        expected_selection[subject] = selection["sha256"]
        expected_episode[subject] = episode["sha256"]

    if len(pins) != len(expected_plans) or any(not isinstance(pin, PinnedCaseCell) for pin in pins):
        raise ValueError("pins must contain exactly 1040 typed case cells")
    plans_by_id = {plan.case_id: plan for plan in expected_plans}
    seen: set[str] = set()
    common_source: tuple[str, str, bool] | None = None
    for pin in pins:
        plan = pin.plan
        case_id = plan.case_id
        if case_id not in plans_by_id or case_id in seen or plan != plans_by_id[case_id]:
            raise ValueError("pinned cases are missing, duplicate or outside the Cho roster")
        seen.add(case_id)
        identity = pin.identity
        if (
            pin.key != ExpectedCell(*plan.identity_key)
            or (
                identity.dataset, identity.target_subject, identity.method,
                identity.shots_per_class, identity.model_seed,
            ) != plan.identity_key
            or identity.support_draw_seed is not None
            or identity.montage_seed is not None
            or identity.protocol_sha256 != protocol_sha256
            or identity.episode_sha256 != expected_episode[plan.target_subject]
            or identity.selection_sha256 != expected_selection[plan.target_subject]
            or identity.preprocessing_sha256 != catalogs[plan.target_subject].preprocessing_sha256
            or identity.method_config_sha256 != method_config_sha256[plan.method]
        ):
            raise ValueError(f"pinned case identity differs from reconstructed {case_id}")
        source_identity = (
            identity.source_sha256, identity.git_commit, identity.git_dirty,
        )
        if common_source is None:
            common_source = source_identity
        elif common_source != source_identity:
            raise ValueError("pinned cases have mixed source identities")
        if expected_source is not None and (
            identity.source_sha256 != expected_source.source_sha256
            or identity.git_commit != expected_source.git_commit
            or identity.git_dirty is not expected_source.git_dirty
        ):
            raise ValueError(f"pinned case source differs from expected source: {case_id}")
    if len(seen) != len(expected_plans):
        raise ValueError("pinned cases do not cover the Cho first tranche")
