"""Owned synthetic qualification of declared overlap; no actual cohort intake."""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import threading
import unittest

P = Path(__file__).resolve().parent
ROOT = Path("D:/Aenv/pro3")
PACKAGE = ROOT / "docs/phase2/evaluation_recording_provenance_package_20261011.json"
spec = importlib.util.spec_from_file_location("_qualified_declared_overlap", P / "declared_overlap.py")
candidate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate
spec.loader.exec_module(candidate)
package_bytes = candidate.intake.read_metadata(PACKAGE)
template = json.loads(candidate.intake.read_metadata(candidate.intake.TEMPLATE_PATH))


def encoded(value):
    return json.dumps(value, allow_nan=False).encode("utf-8")


def target(value, dataset="cho2017"):
    return next(row for row in value["evaluation_intersections"] if row["dataset"] == dataset)


def fixture(dataset="cho2017"):
    value = copy.deepcopy(template)
    version = "1.0.0" if dataset == "mmidb" else "SYNTHETIC_VERSION_ONLY"
    value["training_inventory"]["dataset_entries"] = [{"dataset": dataset, "version": version, "identifier_namespace": "SYNTHETIC_NAMESPACE_ONLY",
        "subject_identifiers": ["SYNTHETIC_SUBJECT_ONLY"], "recording_identifiers": ["SYNTHETIC_RECORDING_ONLY"], "coverage_statement": "SYNTHETIC_DECLARATION_ONLY"}]
    value["training_inventory"]["identifier_namespaces"] = [{"dataset": dataset, "version": version, "name": "SYNTHETIC_NAMESPACE_ONLY", "definition": "SYNTHETIC_DEFINITION_ONLY"}]
    item = target(value, dataset)
    item["evaluation_inventory_reference"] = "docs/phase2/evaluation_recording_provenance_package_20261011.json"
    item["evaluation_inventory_sha256"] = candidate.PACKAGE_SHA256
    item["dataset_versions"] = [version]
    subject = {"cho2017": "cho2017/subject_01", "bci_iv_2a": "bci_iv_2a/subject_01", "mmidb": "mmidb/subject_001"}[dataset]
    recording = {"cho2017": "cho2017/s01.mat", "bci_iv_2a": "bci_iv_2a/A01T.mat", "mmidb": "mmidb/S001R04.edf"}[dataset]
    item["subject_identifier_mapping"] = [{"training_identifier": "SYNTHETIC_SUBJECT_ONLY", "evaluation_identifier": subject, "mapping_evidence_reference": "synthetic:no-reference-read"}]
    item["recording_identifier_mapping"] = [{"training_identifier": "SYNTHETIC_RECORDING_ONLY", "evaluation_identifier": recording, "mapping_evidence_reference": "synthetic:no-reference-read"}]
    return value


def run(value):
    report = candidate.compare_bytes(encoded(value), package_bytes)
    assert set(report["evaluation_findings"].values()) == {"unknown"}
    for key in ("claimant_authenticated", "training_run_link_verified", "cohort_coverage_verified", "mapping_evidence_verified", "label_exposure_verified",
                "actual_checkpoint_target_overlap_verified", "scientifically_eligible_roster_or_query_freeze", "zero_declared_matches_prove_exclusion_or_independence",
                "referenced_artifacts_fetched_or_opened", "scientific_gate_a_signed", "experiment_freeze_signed", "training_or_case_admitted"):
        assert report[key] is False, key
    assert report["original_case_attempts_remaining"] == 0
    return report


def rejected(value, expected, *, raw=None, package=None):
    try:
        candidate.compare_bytes(encoded(value) if raw is None else raw, package_bytes if package is None else package)
    except (candidate.OverlapError, candidate.intake.IntakeError) as error:
        assert str(error) == expected, (str(error), expected)
    else:
        raise AssertionError("required refusal missing")


def singleton():
    result = run(fixture())["computed_declared_intersections"]["cho2017"]
    assert result["subject_intersection"] == ["cho2017/subject_01"] and result["recording_intersection"] == ["cho2017/s01.mat"]


def blank():
    report = run(template)
    assert all(row["subject_intersection"] is None and row["recording_intersection"] is None for row in report["computed_declared_intersections"].values())


def unbound():
    value = fixture()
    item = target(value)
    item.update(evaluation_inventory_reference=None, evaluation_inventory_sha256=None, subject_identifier_mapping=[], recording_identifier_mapping=[])
    result = run(value)["computed_declared_intersections"]["cho2017"]
    assert result["status"] == "unbound_declarations_not_compared" and result["subject_intersection"] is None


def recording_only():
    value = fixture()
    target(value)["subject_identifier_mapping"] = []
    result = run(value)["computed_declared_intersections"]["cho2017"]
    assert result["subject_intersection"] == ["cho2017/subject_01"] and result["explicit_subject_mapping_matches"] == 0


def subject_only():
    value = fixture()
    target(value)["recording_identifier_mapping"] = []
    result = run(value)["computed_declared_intersections"]["cho2017"]
    assert result["subject_intersection"] == ["cho2017/subject_01"] and result["recording_intersection"] == [] and result["unmapped_training_recording_identifiers"] == 1


def alias_union():
    value = fixture()
    value["training_inventory"]["dataset_entries"][0]["subject_identifiers"].append("SYNTHETIC_ALIAS_ONLY")
    target(value)["subject_identifier_mapping"].append({"training_identifier": "SYNTHETIC_ALIAS_ONLY", "evaluation_identifier": "cho2017/subject_01", "mapping_evidence_reference": "synthetic:no-read"})
    result = run(value)["computed_declared_intersections"]["cho2017"]
    assert result["declared_training_subject_identifiers"] == 2 and result["subject_intersection"] == ["cho2017/subject_01"]


def same_namespace_entries_union():
    value = fixture()
    value["training_inventory"]["dataset_entries"].append(copy.deepcopy(value["training_inventory"]["dataset_entries"][0]))
    result = run(value)["computed_declared_intersections"]["cho2017"]
    assert result["declared_training_subject_identifiers"] == result["declared_training_recording_identifiers"] == 1


def zero_not_exclusion():
    value = fixture()
    target(value).update(subject_identifier_mapping=[], recording_identifier_mapping=[], subject_intersection=[], recording_intersection=[])
    result = run(value)["computed_declared_intersections"]["cho2017"]
    assert result["subject_intersection"] == result["recording_intersection"] == []
    assert result["unmapped_training_subject_identifiers"] == result["unmapped_training_recording_identifiers"] == 1


def partial_mapping():
    value = fixture()
    entry = value["training_inventory"]["dataset_entries"][0]
    entry["subject_identifiers"].append("SYNTHETIC_UNMAPPED_SUBJECT")
    entry["recording_identifiers"].append("SYNTHETIC_UNMAPPED_RECORDING")
    result = run(value)["computed_declared_intersections"]["cho2017"]
    assert result["unmapped_training_subject_identifiers"] == result["unmapped_training_recording_identifiers"] == 1


def all_datasets():
    value = copy.deepcopy(template)
    for dataset in ("cho2017", "bci_iv_2a", "mmidb"):
        one = fixture(dataset)
        for key in ("dataset_entries", "identifier_namespaces"):
            value["training_inventory"][key].extend(one["training_inventory"][key])
        value["evaluation_intersections"] = [target(one, dataset) if row["dataset"] == dataset else row for row in value["evaluation_intersections"]]
    report = run(value)
    assert all(len(row["subject_intersection"]) == len(row["recording_intersection"]) == 1 for row in report["computed_declared_intersections"].values())


def supplied_matching_sets():
    value = fixture()
    target(value).update(subject_intersection=["cho2017/subject_01"], recording_intersection=["cho2017/s01.mat"])
    run(value)


def refs_not_echoed():
    value = fixture()
    value["claimant"]["source_or_channel_reference"] = "SYNTHETIC_PRIVATE_SENTINEL"
    for key in ("subject_identifier_mapping", "recording_identifier_mapping"):
        target(value)[key][0]["mapping_evidence_reference"] = "SYNTHETIC_PRIVATE_SENTINEL"
    assert "SYNTHETIC_PRIVATE_SENTINEL" not in json.dumps(run(value))


def edit_and_reject(path, content, code, dataset="cho2017"):
    value = fixture(dataset)
    item = value
    for key in path[:-1]:
        item = item[key]
    item[path[-1]] = content
    rejected(value, code)


def ambiguous(field):
    value = fixture()
    extra = copy.deepcopy(value["training_inventory"]["dataset_entries"][0])
    extra[field] = "SYNTHETIC_DIFFERENT_ONLY"
    value["training_inventory"]["dataset_entries"].append(extra)
    rejected(value, "ambiguous_declared_version_or_namespace")


def duplicate_mapping(conflict):
    value = fixture()
    extra = copy.deepcopy(target(value)["subject_identifier_mapping"][0])
    if conflict:
        extra["evaluation_identifier"] = "cho2017/subject_02"
    target(value)["subject_identifier_mapping"].append(extra)
    rejected(value, "duplicate_mapping_training_identifier")


def duplicate_namespace():
    value = fixture()
    value["training_inventory"]["identifier_namespaces"].append(copy.deepcopy(value["training_inventory"]["identifier_namespaces"][0]))
    rejected(value, "ambiguous_or_missing_namespace_definition")


def mmidb_version():
    value = fixture("mmidb")
    value["training_inventory"]["dataset_entries"][0]["version"] = "SYNTHETIC_WRONG_ONLY"
    value["training_inventory"]["identifier_namespaces"][0]["version"] = "SYNTHETIC_WRONG_ONLY"
    target(value, "mmidb")["dataset_versions"] = ["SYNTHETIC_WRONG_ONLY"]
    rejected(value, "declared_dataset_version_mismatch")


def other_dataset_ignored():
    value = fixture()
    extra = copy.deepcopy(value["training_inventory"]["dataset_entries"][0])
    extra["dataset"] = "SYNTHETIC_NON_EVALUATION_ONLY"
    value["training_inventory"]["dataset_entries"].append(extra)
    report = run(value)
    assert set(report["computed_declared_intersections"]) == {"cho2017", "bci_iv_2a", "mmidb"}


CASES = [(name, function) for name, function in (
    ("blank_inventory_unknown", blank), ("unbound_declarations_unknown", unbound), ("singleton_explicit_overlap", singleton),
    ("recording_match_identifies_subject", recording_only), ("subject_only_match", subject_only), ("many_aliases_one_subject", alias_union),
    ("same_namespace_entries_union", same_namespace_entries_union), ("zero_matches_not_exclusion", zero_not_exclusion),
    ("partial_unmapped_counts", partial_mapping), ("three_dataset_roster", all_datasets), ("supplied_matching_intersections", supplied_matching_sets),
    ("untrusted_references_not_echoed", refs_not_echoed), ("non_evaluation_dataset_ignored", other_dataset_ignored),
    ("duplicate_mapping_same", lambda: duplicate_mapping(False)), ("duplicate_mapping_conflict", lambda: duplicate_mapping(True)),
    ("ambiguous_versions", lambda: ambiguous("version")), ("ambiguous_namespaces", lambda: ambiguous("identifier_namespace")),
    ("duplicate_namespace_definition", duplicate_namespace), ("mmidb_version_drift", mmidb_version),
    ("wrong_package_hash", lambda: rejected(fixture(), "evaluation_package_hash_mismatch", package=package_bytes+b" ")),
    ("oversized_package", lambda: rejected(fixture(), "evaluation_package_size_or_type", package=b" "*(1024**2+1))),
    ("wrong_package_type", lambda: rejected(fixture(), "evaluation_package_size_or_type", package="not_bytes")),
    ("oversized_submission", lambda: rejected(fixture(), "metadata_size_or_type", raw=b" "*(1024**2+1))),
    ("duplicate_json_key", lambda: rejected(fixture(), "duplicate_json_key", raw=b'{"schema":"x","schema":"y"}')),
    ("case_reset", lambda: edit_and_reject(("original_case_attempts_remaining",), 1, "read_only_template_field_changed")),
    ("gate_signature", lambda: edit_and_reject(("scientific_gate_a_signed",), True, "read_only_template_field_changed")),
    ("freeze_signature", lambda: edit_and_reject(("experiment_freeze_signed",), True, "read_only_template_field_changed")),
    ("checkpoint_drift", lambda: edit_and_reject(("known_checkpoint_identity", "original_sha256"), "f"*64, "read_only_template_field_changed")),
    ("missing_namespace_definition", lambda: edit_and_reject(("training_inventory", "identifier_namespaces"), [], "ambiguous_or_missing_namespace_definition")),
    ("wrong_target_binding", lambda: edit_and_reject(("evaluation_intersections", 0, "evaluation_inventory_sha256"), "f"*64, "declared_evaluation_package_binding_mismatch")),
    ("missing_reference_binding", lambda: edit_and_reject(("evaluation_intersections", 0, "evaluation_inventory_reference"), None, "evaluation_binding_required_for_mapping")),
    ("unknown_subject_mapping", lambda: edit_and_reject(("evaluation_intersections", 0, "subject_identifier_mapping", 0, "evaluation_identifier"), "cho2017/subject_999", "unknown_evaluation_identifier")),
    ("unknown_recording_mapping", lambda: edit_and_reject(("evaluation_intersections", 0, "recording_identifier_mapping", 0, "evaluation_identifier"), "cho2017/unknown.mat", "unknown_evaluation_identifier")),
    ("cross_dataset_subject_mapping", lambda: edit_and_reject(("evaluation_intersections", 0, "subject_identifier_mapping", 0, "evaluation_identifier"), "mmidb/subject_001", "cross_dataset_evaluation_mapping")),
    ("cross_dataset_recording_mapping", lambda: edit_and_reject(("evaluation_intersections", 0, "recording_identifier_mapping", 0, "evaluation_identifier"), "mmidb/S001R04.edf", "cross_dataset_evaluation_mapping")),
    ("undeclared_training_subject", lambda: edit_and_reject(("evaluation_intersections", 0, "subject_identifier_mapping", 0, "training_identifier"), "SYNTHETIC_UNDECLARED", "mapping_training_identifier_not_declared")),
    ("undeclared_training_recording", lambda: edit_and_reject(("evaluation_intersections", 0, "recording_identifier_mapping", 0, "training_identifier"), "SYNTHETIC_UNDECLARED", "mapping_training_identifier_not_declared")),
    ("contradictory_subject_intersection", lambda: edit_and_reject(("evaluation_intersections", 0, "subject_intersection"), [], "supplied_declared_intersection_mismatch")),
    ("contradictory_recording_intersection", lambda: edit_and_reject(("evaluation_intersections", 0, "recording_intersection"), [], "supplied_declared_intersection_mismatch")),
    ("target_version_mismatch", lambda: edit_and_reject(("evaluation_intersections", 0, "dataset_versions"), ["SYNTHETIC_DIFFERENT"], "declared_dataset_version_mismatch")),
    ("empty_mapping_evidence", lambda: edit_and_reject(("evaluation_intersections", 0, "recording_identifier_mapping", 0, "mapping_evidence_reference"), "", "invalid_text_field")),
    ("forged_review_finding", lambda: edit_and_reject(("evaluation_intersections", 0, "current_finding"), "verified_excluded", "target_question_or_review_finding_changed")),
)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(strict=True)
    assert out.parent == P and out.name == "attempt_001" and not (out / "tests.json").exists()
    denied = {"network": 0, "subprocess": 0, "outside_write": 0}

    def audit(event, values):
        if event.startswith("socket."):
            denied["network"] += 1
            raise PermissionError("network_denied")
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.exec", "os.spawn"}:
            denied["subprocess"] += 1
            raise PermissionError("subprocess_denied")
        if event == "open" and not isinstance(values[0], int):
            mode, flags = values[1], values[2]
            writes = (isinstance(mode, str) and any(x in mode for x in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
            if writes and not Path(values[0]).resolve().is_relative_to(out):
                denied["outside_write"] += 1
                raise PermissionError("outside_write_denied")

    sys.addaudithook(audit)
    suite = unittest.TestSuite(unittest.FunctionTestCase(fn, description=name) for name, fn in CASES)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
    cli_pass = True
    for valid in (True, False):
        data = fixture()
        if not valid:
            target(data)["evaluation_inventory_sha256"] = "f"*64
        path = out / ("synthetic_cli_success.json" if valid else "synthetic_cli_error.json")
        with path.open("xb") as stream:
            stream.write(encoded(data))
        saved = sys.argv
        sys.argv = ["declared_overlap.py", "--input", str(path), "--evaluation-package", str(PACKAGE)]
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured):
                code = candidate.main()
        finally:
            sys.argv = saved
        report = json.loads(captured.getvalue())
        cli_pass &= code == (0 if valid else 2) and report["format_valid"] is valid and report["training_or_case_admitted"] is False
    scientific = any(name.split('.')[0] in {"numpy", "torch", "scipy", "mne", "moabb", "safetensors"} for name in sys.modules)
    passed = result.wasSuccessful() and cli_pass and not scientific and denied == {"network": 0, "subprocess": 0, "outside_write": 0} and threading.active_count() == 1
    record = {"schema": "pro3_declared_overlap_owned_synthetic_qualification_v1", "passed": passed, "tests_run": result.testsRun,
        "test_names": [name for name, _ in CASES], "failures": len(result.failures), "errors": len(result.errors),
        "cli_success_and_error_paths_executed": cli_pass, "evaluation_package_sha256": hashlib.sha256(package_bytes).hexdigest(),
        "boundary_denials": denied, "scientific_libraries_imported": scientific, "active_python_threads": threading.active_count(),
        "actual_cohort_submission_processed": False, "checkpoint_model_raw_cache_or_recorder_opened": False,
        "scientific_or_case_admission": False, "original_case_attempts_remaining": 0}
    with (out / "tests.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"passed": passed, "tests_run": result.testsRun, "cli_paths": 2, "scientific_or_case_admission": False}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
