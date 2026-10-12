"""Compute declared identifier matches without authenticating cohort evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKAGE_SHA256 = "b9ea3dfefed137a2264313bed1b7b3c392a1be799fbd767583500f44024bfc69"
INSPECTOR_SHA256 = "9221d82a8035b851e56e76dcd50124846050dded5727755f2f939bfa0f04ba3b"
MAX_BYTES = 1024**2
P = Path(__file__).resolve().parent
inspector_path = P / "inspect_cohort.py"
if not inspector_path.exists():
    inspector_path = P.parent / "provenance_intake_candidate/inspect_cohort.py"
if hashlib.sha256(inspector_path.read_bytes()).hexdigest() != INSPECTOR_SHA256:
    raise ValueError("qualified_intake_helper_hash_mismatch")
spec = importlib.util.spec_from_file_location("_pro3_overlap_qualified_intake", inspector_path)
intake = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = intake
spec.loader.exec_module(intake)


class OverlapError(ValueError):
    """Stable errors never echo submitted identities or evidence references."""


def _mapping(rows, declared, evaluation, dataset):
    result = {}
    for row in rows:
        training = row["training_identifier"]
        target = row["evaluation_identifier"]
        if training in result:
            raise OverlapError("duplicate_mapping_training_identifier")
        if training not in declared:
            raise OverlapError("mapping_training_identifier_not_declared")
        if target not in evaluation:
            raise OverlapError("unknown_evaluation_identifier")
        if evaluation[target]["dataset"] != dataset:
            raise OverlapError("cross_dataset_evaluation_mapping")
        result[training] = target
    return result


def compare_bytes(submission_raw, package_raw):
    """Compare mapped declarations; every evidence/admission boundary stays false."""
    if type(package_raw) is not bytes or not 0 < len(package_raw) <= MAX_BYTES:
        raise OverlapError("evaluation_package_size_or_type")
    if hashlib.sha256(package_raw).hexdigest() != PACKAGE_SHA256:
        raise OverlapError("evaluation_package_hash_mismatch")
    inspection = intake.inspect_bytes(submission_raw)
    submission = intake._decode(submission_raw)
    package = json.loads(package_raw)
    subjects = {row["project_subject_id"]: row for row in package["subjects"]}
    recordings = {row["recording_id"]: row for row in package["recordings"]}
    subject_by_recording = {recording: row["project_subject_id"] for row in package["subjects"] for recording in row["recording_ids"]}
    results = {}
    for target in submission["evaluation_intersections"]:
        dataset = target["dataset"]
        entries = [row for row in submission["training_inventory"]["dataset_entries"] if row["dataset"] == dataset]
        if target["evaluation_inventory_sha256"] is not None and target["evaluation_inventory_sha256"] != PACKAGE_SHA256:
            raise OverlapError("declared_evaluation_package_binding_mismatch")
        mappings_present = bool(target["subject_identifier_mapping"] or target["recording_identifier_mapping"])
        bound = target["evaluation_inventory_sha256"] == PACKAGE_SHA256 and target["evaluation_inventory_reference"] is not None
        if mappings_present and not bound:
            raise OverlapError("evaluation_binding_required_for_mapping")
        if not entries:
            if mappings_present:
                raise OverlapError("mapping_training_identifier_not_declared")
            results[dataset] = {"status": "no_declared_training_inventory", "subject_intersection": None, "recording_intersection": None,
                "unmapped_training_subject_identifiers": None, "unmapped_training_recording_identifiers": None}
            continue
        if not bound:
            results[dataset] = {"status": "unbound_declarations_not_compared", "subject_intersection": None, "recording_intersection": None,
                "unmapped_training_subject_identifiers": None, "unmapped_training_recording_identifiers": None}
            continue
        versions = {row["version"] for row in entries}
        namespaces = {row["identifier_namespace"] for row in entries}
        if len(versions) != 1 or len(namespaces) != 1:
            raise OverlapError("ambiguous_declared_version_or_namespace")
        version, namespace = next(iter(versions)), next(iter(namespaces))
        if target["dataset_versions"] != [version] or (dataset == "mmidb" and version != "1.0.0"):
            raise OverlapError("declared_dataset_version_mismatch")
        definitions = [row for row in submission["training_inventory"]["identifier_namespaces"]
                       if row["dataset"] == dataset and row["version"] == version and row["name"] == namespace]
        if len(definitions) != 1:
            raise OverlapError("ambiguous_or_missing_namespace_definition")
        training_subjects = {item for row in entries for item in row["subject_identifiers"]}
        training_recordings = {item for row in entries for item in row["recording_identifiers"]}
        subject_map = _mapping(target["subject_identifier_mapping"], training_subjects, subjects, dataset)
        recording_map = _mapping(target["recording_identifier_mapping"], training_recordings, recordings, dataset)
        matched_recordings = set(recording_map.values())
        subjects_from_recordings = {subject_by_recording[identifier] for identifier in matched_recordings}
        matched_subjects = set(subject_map.values()) | subjects_from_recordings
        for key, computed in (("subject_intersection", matched_subjects), ("recording_intersection", matched_recordings)):
            if target[key] is not None and set(target[key]) != computed:
                raise OverlapError("supplied_declared_intersection_mismatch")
        results[dataset] = {"status": "mapped_declarations_computed_unverified", "subject_intersection": sorted(matched_subjects),
            "recording_intersection": sorted(matched_recordings), "explicit_subject_mapping_matches": len(set(subject_map.values())),
            "subjects_identified_from_recording_matches": len(subjects_from_recordings),
            "unmapped_training_subject_identifiers": len(training_subjects - subject_map.keys()),
            "unmapped_training_recording_identifiers": len(training_recordings - recording_map.keys()),
            "declared_training_subject_identifiers": len(training_subjects), "declared_training_recording_identifiers": len(training_recordings)}
    return {"schema": "pro3_declared_cohort_overlap_comparison_candidate_v1", "format_valid": True,
        "status": "declared_identifier_comparison_only_unverified", "input_sha256": inspection["input_sha256"],
        "evaluation_package_sha256": PACKAGE_SHA256, "intake_status": inspection["status"],
        "missing_declaration_fields": inspection["missing_declaration_fields"], "computed_declared_intersections": results,
        "evaluation_findings": inspection["evaluation_findings"], "claimant_authenticated": False, "training_run_link_verified": False,
        "cohort_coverage_verified": False, "mapping_evidence_verified": False, "label_exposure_verified": False,
        "actual_checkpoint_target_overlap_verified": False, "scientifically_eligible_roster_or_query_freeze": False,
        "zero_declared_matches_prove_exclusion_or_independence": False, "referenced_artifacts_fetched_or_opened": False,
        "scientific_gate_a_signed": False, "experiment_freeze_signed": False, "training_or_case_admitted": False,
        "original_case_attempts_remaining": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--evaluation-package", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = compare_bytes(intake.read_metadata(args.input), intake.read_metadata(args.evaluation_package))
    except (OverlapError, intake.IntakeError) as error:
        print(json.dumps({"format_valid": False, "error_code": str(error), "training_or_case_admitted": False}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
