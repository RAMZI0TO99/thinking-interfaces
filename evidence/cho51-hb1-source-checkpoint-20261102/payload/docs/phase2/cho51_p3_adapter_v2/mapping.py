"""Independent synthetic-profile metadata joins, never numerical admission."""

from __future__ import annotations

import tomllib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from docs.phase2.cho51_canonical_boundary_v1 import boundary as Boundary
from .contracts import (
    AUTHORITY, LEDGER, OBLIGATIONS, PLAN, PROFILE, AdapterCompatibility, AdapterIntent,
    canonical_json, decode_json, exact_fields, exact_int, relative_path,
)

ORIGIN_PATH = "runs/coordination/cho51_provenance_numerical_worker_20261025_v7/origin-contract.json"
ORIGIN_SHA256 = "f1318c2f05dbf55a1808e621f05f4574ee695ff5ec15187b5ce2932650eaa781"
MANIFEST_PATH = "runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture/synthetic-input-identity.json"
MANIFEST_SHA256 = "34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c"
MAX_MAPPING_FILES = 12
MAX_MAPPING_BYTES = 16 * 1024 * 1024


def assess_adapter_intent(intent: AdapterIntent, *, boundary_request: Any,
                          full_route: Any, adopted_route: Any, input_pins: Any) -> AdapterCompatibility:
    """Call the genuine boundary, then join independently pinned historical metadata."""
    if type(intent) is not AdapterIntent or type(boundary_request) is not Boundary.CanonicalBoundaryRequest:
        raise ValueError("actual immutable intent and boundary request required, not a supplied assessment")
    assessment = Boundary.assess_metadata(boundary_request, full_route=full_route, adopted_route=adopted_route, input_pins=input_pins)
    payload = intent.payload
    if (payload["boundary_request_sha256"] != boundary_request.expected_sha256
            or payload["origin_contract_sha256"] != ORIGIN_SHA256
            or payload["input_manifest_sha256"] != MANIFEST_SHA256):
        raise ValueError("independent request/origin/manifest pins differ")
    if assessment.sha256 != payload["boundary_assessment_sha256"]:
        raise ValueError("fresh genuine boundary assessment differs from independent intent pin")
    request = boundary_request.payload
    root = Path(request["root"])
    retained: dict[Path, tuple[bytes, Any, str]] = {}

    def read(relative: str, expected: str) -> bytes:
        relative_path(relative)
        path = root.joinpath(*relative.split("/"))
        if path.suffix not in (".json", ".toml"):
            raise ValueError("mapping only reads explicit JSON/TOML metadata")
        if path in retained:
            if retained[path][2] != expected:
                raise ValueError("conflicting mapping metadata pin")
            return retained[path][0]
        raw, identity = Boundary.stable_metadata_bytes(path, expected)
        if len(retained) >= MAX_MAPPING_FILES or len(raw) + sum(len(value[0]) for value in retained.values()) > MAX_MAPPING_BYTES:
            raise ValueError("mapping metadata aggregate bound exceeded")
        retained[path] = raw, identity, expected
        return raw

    origin = decode_json(read(ORIGIN_PATH, ORIGIN_SHA256))["summary"]
    manifest = decode_json(read(MANIFEST_PATH, MANIFEST_SHA256))
    exact_fields(manifest, {
        "actual_study_data", "adopted_case_plan_count", "adopted_evaluation_targets",
        "canonical_shot_levels", "files", "inner_validation_subject", "original_case_attempts_remaining",
        "outer_target", "profile_a_shape", "profile_b_shape", "protocol_sha256", "schema",
        "scientific_admission", "sha256", "shots_per_class", "source_selection_sha256",
        "source_subjects_available", "synthetic", "training_subjects", "trials_per_class", "trials_per_subject",
    }, "original synthetic input manifest")
    if (manifest["schema"] != "cho51_owned_synthetic_fold_inputs_v1" or manifest["synthetic"] is not True
            or manifest["actual_study_data"] is not False or manifest["scientific_admission"] is not False):
        raise ValueError("original manifest must remain declared synthetic engineering metadata")
    for name, count in {"adopted_case_plan_count": 1020, "adopted_evaluation_targets": 51,
                        "original_case_attempts_remaining": 0, "shots_per_class": 5,
                        "source_subjects_available": 52, "trials_per_class": 21, "trials_per_subject": 42}.items():
        if exact_int(manifest[name]) != count:
            raise ValueError("synthetic manifest exact integer claim differs")
    files = manifest["files"]
    if type(files) is not dict or len(files) != 213:
        raise ValueError("exact213 historical input metadata rows required")
    total = 0
    for relative, row in files.items():
        relative_path(relative)
        exact_fields(row, {"sha256", "size_bytes"}, "historical input row")
        Boundary._sha(row["sha256"])
        total += exact_int(row["size_bytes"], 1)
    if total != 734579463 or canonical_json(origin["input_audit"]) != canonical_json({
        "files": 213, "bytes": total,
        "fixture_root": str(root.joinpath(*MANIFEST_PATH.split("/")[:-1])),
        "input_identity_file_sha256": MANIFEST_SHA256,
    }):
        raise ValueError("original213-input historical audit claims differ")
    if manifest["outer_target"] != "subject_02" or manifest["inner_validation_subject"] != "subject_01" or manifest["training_subjects"] != list(Boundary.SUBJECTS[2:]):
        raise ValueError("historical source/validation/target metadata domains differ")
    for name, expected in {"profile_a_shape": [42, 64, 512], "profile_b_shape": [42, 64, 800],
                           "canonical_shot_levels": [1, 5, 10, 20]}.items():
        if canonical_json(manifest[name]) != canonical_json(expected):
            raise ValueError("historical shape/shot metadata differs")
    metadata_pin = request["metadata"]
    metadata = decode_json(read(metadata_pin["path"], metadata_pin["sha256"]))
    if metadata.get("scope") != "externally_supplied_catalog_asset_metadata_unverified":
        raise ValueError("fixed numerical profile requires original synthetic lineage, not arbitrary fabricated catalog IDs")
    configs = {}
    for name in ("base", "protocol", "threshold", "variant", "ceiling", "candidates"):
        pin = request["configuration"][name]
        raw = read(pin["path"], pin["sha256"])
        configs[name] = tomllib.loads(raw.decode("utf-8")) if pin["path"].endswith(".toml") else decode_json(raw)
        if name != "candidates" and files[pin["path"]]["sha256"] != pin["sha256"]:
            raise ValueError("canonical configuration bytes differ from copied historical fixture configuration")
    from core.config import canonical_config_json, config_digest
    from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
    from evaluation.phase2_records import envelope
    from evaluation.phase2_runner import CasePlan

    protocol_digest = config_digest(configs["protocol"])
    if protocol_digest != manifest["protocol_sha256"]:
        raise ValueError("logical protocol differs from original synthetic manifest")
    preprocessing = config_digest({
        "profile_identity": configs["protocol"]["preparation"]["profile_identity"],
        "threshold_config_sha256": request["configuration"]["threshold"]["sha256"],
        "dataset": "cho2017", "threshold": configs["threshold"]["datasets"]["cho2017"]["artifact_threshold_volts"],
    })
    trials = tuple(canonical_json(["synthetic_session", "synthetic_run", index]) for index in range(42))
    catalogs = tuple(TrialCatalog("cho2017", subject, trials, Boundary.CLASSES * 21,
                                 Boundary.CLASSES, files[f"data/processed/cho2017/profile_a/{subject}.npz"]["sha256"], preprocessing)
                     for subject in Boundary.SUBJECTS)
    assets = {subject: {
        "profile_b_artifact_sha256": files[f"data/processed/cho2017/profile_b_60hz_v1/{subject}.npz"]["sha256"],
        "profile_b_manifest_sha256": files[f"data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json"]["sha256"],
        "variant_config_sha256": request["configuration"]["variant"]["sha256"],
    } for subject in Boundary.SUBJECTS}
    expected_catalogs = decode_json(canonical_config_json([asdict(catalog) for catalog in catalogs]))
    if (canonical_json(metadata["catalogs"]) != canonical_json(expected_catalogs)
            or canonical_json(metadata["assets"]) != canonical_json(assets)
            or canonical_json(origin["target_assets"]) != canonical_json(assets)):
        raise ValueError("all52 synthetic catalogs/assets must independently match original manifest metadata")
    selected = source_selection(catalogs, target="subject_02")
    episode = nested_episode(catalogs[1], shots=(1, 5, 10, 20), protocol_sha256=protocol_digest)
    partition = episode.partition(5)
    if (len(partition.support_indices) != 10 or len(partition.query_indices) != 2
            or len(partition.unused_pool_indices) != 30
            or set(partition.support_indices + partition.query_indices + partition.unused_pool_indices) != set(range(42))):
        raise ValueError("fixed synthetic episode must partition ten support/two query/thirty unused trials")
    settings = configs["candidates"]["methods"][0]["candidates"][0]["support"]
    selected_plan = CasePlan(**PLAN)
    target = catalogs[1]
    target_contract = {
        "plan": dict(PLAN), "case_id": selected_plan.case_id,
        "protocol_sha256": protocol_digest, "selection_sha256": selected.sha256,
        "selection_record_sha256": envelope("source_selection", asdict(selected))["sha256"],
        "episode_sha256": episode.sha256, "episode_record_sha256": envelope("episode_manifest", episode.payload())["sha256"],
        "target_catalog_sha256": target.sha256, "source_subjects": list(selected.source_subjects),
        "support_indices": list(partition.support_indices), "query_indices": list(partition.query_indices),
        "unused_pool_indices": list(partition.unused_pool_indices),
        "support_trial_ids": [target.trial_ids[index] for index in partition.support_indices],
        "query_trial_ids": [target.trial_ids[index] for index in partition.query_indices],
        "unused_trial_ids": [target.trial_ids[index] for index in partition.unused_pool_indices],
        "support_labels": [target.classes.index(target.labels[index]) for index in partition.support_indices],
        "query_labels": [target.classes.index(target.labels[index]) for index in partition.query_indices],
        "settings": settings, "settings_sha256": config_digest(settings),
    }
    if (canonical_json(origin["target_contract"]) != canonical_json(target_contract)
            or origin["target_contract_sha256"] != config_digest(target_contract)
            or manifest["source_selection_sha256"] != selected.sha256):
        raise ValueError("selected plan/settings/selection/episode lineage differs from historical contract")
    report = assessment.report
    expected_roles = {
        "producer": origin["historical_source"], "canonical_executor": report["roles"]["executor"]["source"],
        "boundary_recorder": report["roles"]["recorder"]["source"], "historical_recorder": origin["recorder_control_source"],
    }
    if canonical_json(payload["roles"]) != canonical_json(expected_roles):
        raise ValueError("producer/executor/boundary-recorder/historical-recorder domains differ")
    for path, (raw, identity, expected) in retained.items():
        checked_raw, checked_identity = Boundary.stable_metadata_bytes(path, expected)
        if checked_raw != raw or checked_identity != identity:
            raise ValueError("mapping metadata replaced during assessment")
    result = {
        "schema": "cho51_p3_adapter_compatibility_v1", "status": "metadata_profile_compatible",
        "profile": PROFILE, "intent_sha256": intent.expected_sha256,
        "boundary_request_sha256": boundary_request.expected_sha256, "boundary_assessment_sha256": assessment.sha256,
        "origin_contract_sha256": ORIGIN_SHA256, "input_manifest_sha256": MANIFEST_SHA256,
        "selected_plan": dict(PLAN), "selected_contract_sha256": config_digest(target_contract),
        "full_route_ids_sha256": report["all_original_case_ids_sha256"],
        "adopted_route_ids_sha256": report["all_adopted_case_ids_sha256"],
        "original_plan_count": 1040, "adopted_plan_count": 1020, "catalog_count": 52, "asset_count": 52,
        "historical_input_claim": {"files": 213, "bytes": total, "freshly_physically_verified": False},
        "metadata_cohort_origin_sha256": report["configuration"]["cohort"]["sha256"],
        "roles": expected_roles, "future_recorder": payload["future_recorder"],
        "outstanding_obligations": list(OBLIGATIONS), "authority": dict(AUTHORITY),
        "current_numerical_ledger": dict(LEDGER), "scientific_admission": False,
        "metadata_files_read": len(retained), "metadata_bytes_read": sum(len(value[0]) for value in retained.values()),
    }
    return AdapterCompatibility(canonical_json(result))
