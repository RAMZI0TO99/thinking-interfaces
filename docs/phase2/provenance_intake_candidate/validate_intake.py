"""Synthetic metadata tests only; the guard supplies the owned output directory."""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pro3_cohort_intake_candidate", P / "inspect_cohort.py")
candidate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate
spec.loader.exec_module(candidate)
template_bytes = candidate.read_metadata(P / "reference_template.json")
template = json.loads(template_bytes)


def encoded(value):
    return json.dumps(value, allow_nan=False).encode("utf-8")


def changed(path, content):
    value = copy.deepcopy(template)
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = content
    return encoded(value)


def assert_unverified(result):
    assert result["format_valid"]
    assert set(result["evaluation_findings"].values()) == {"unknown"}
    for key in ("claimant_authenticated", "training_run_link_verified", "cohort_coverage_verified",
                "referenced_artifacts_fetched_or_opened", "scientific_gate_a_signed", "experiment_freeze_signed",
                "training_or_case_admitted"):
        assert result[key] is False, key
    assert result["original_case_attempts_remaining"] == 0


def blank_unknown():
    result = candidate.inspect_bytes(template_bytes)
    assert_unverified(result)
    assert result["status"] == "incomplete_declarations"
    assert result["missing_declaration_fields"]
    assert result["input_sha256"] == hashlib.sha256(template_bytes).hexdigest()


def populated_still_unverified():
    value = copy.deepcopy(template)
    value["claimant"] = {"identity_or_public_handle": "SYNTHETIC_TEST_ONLY", "role": "synthetic",
                         "statement_date_utc": "2026-10-10T00:00:00Z", "source_or_channel_reference": "synthetic:no-network"}
    value["checkpoint_training_link"] = {"training_run_identifier": "SYNTHETIC_RUN_ONLY",
        "execution_record_reference": "synthetic:no-file-read", "supplied_execution_record_sha256": "a" * 64,
        "checkpoint_mapping_explanation": "Synthetic declaration; no actual author or execution evidence."}
    inventory = value["training_inventory"]
    inventory["coverage_complete_attestation"] = True
    inventory["dataset_entries"] = [{"dataset": "SYNTHETIC_DATASET_ONLY", "version": "synthetic_v1",
        "identifier_namespace": "synthetic", "subject_identifiers": ["synthetic_person"],
        "recording_identifiers": ["synthetic_record"], "coverage_statement": "synthetic claim only"}]
    inventory["identifier_namespaces"] = [{"name": "synthetic", "dataset": "SYNTHETIC_DATASET_ONLY",
        "version": "synthetic_v1", "definition": "synthetic identity namespace"}]
    inventory["split_definitions"] = [{"dataset": "SYNTHETIC_DATASET_ONLY", "version": "synthetic_v1",
        "name": "synthetic_training", "definition": "synthetic only"}]
    value["evidence_items"] = [{"reference": "synthetic:no-file-read", "description": "synthetic artifact only",
        "source_date_utc": "2026-10-10T00:00:00Z", "sha256": "a" * 64, "supported_claims": ["synthetic_only"]}]
    for item in value["evaluation_intersections"]:
        item["evaluation_inventory_reference"] = "synthetic:no-file-read"
        item["evaluation_inventory_sha256"] = "b" * 64
        item["dataset_versions"] = ["synthetic_v1"]
        item["coverage_basis"] = "synthetic assertion, not accepted evidence"
    result = candidate.inspect_bytes(encoded(value))
    assert_unverified(result)
    assert result["status"] == "declarations_present_unverified"
    assert result["missing_declaration_fields"] == []


def partial_list_no_exclusion():
    value = copy.deepcopy(template)
    value["evaluation_intersections"][0]["subject_intersection"] = []
    value["evaluation_intersections"][0]["recording_intersection"] = []
    result = candidate.inspect_bytes(encoded(value))
    assert_unverified(result)
    assert result["evaluation_findings"]["cho2017"] == "unknown"


def rejection(raw, expected):
    try:
        candidate.inspect_bytes(raw)
    except candidate.IntakeError as error:
        assert str(error) == expected, (str(error), expected)
    else:
        raise AssertionError("malformed or authority-changing input accepted")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert args.output.is_dir()
    cases = [("blank_unknown", blank_unknown), ("all_declarations_unverified", populated_still_unverified),
             ("partial_empty_intersection_unknown", partial_list_no_exclusion)]
    negatives = [
        ("duplicate_top_key", b'{"x":1,"x":2}', "duplicate_json_key"),
        ("duplicate_nested_key", b'{"x":{"y":1,"y":2}}', "duplicate_json_key"),
        ("nan", b'{"x":NaN}', "nonfinite_json_number"),
        ("infinity", b'{"x":Infinity}', "nonfinite_json_number"),
        ("numeric_overflow", b'{"x":1e999}', "floating_number_not_in_schema"),
        ("invalid_utf8", b'\xff', "invalid_json_or_utf8"),
        ("oversized", b' ' * (candidate.MAX_BYTES + 1), "metadata_size_or_type"),
        ("deep_structure", b'[' * 30 + b'0' + b']' * 30, "metadata_structure_bound"),
        ("long_string", encoded({"x": "a" * (candidate.MAX_TEXT + 1)}), "metadata_text_bound"),
        ("extra_top_field", encoded({**template, "run_command": "synthetic_do_not_execute"}), "missing_or_unexpected_field"),
        ("checkpoint_drift", changed(["known_checkpoint_identity", "original_sha256"], "0" * 64), "read_only_template_field_changed"),
        ("gate_signature", changed(["scientific_gate_a_signed"], True), "read_only_template_field_changed"),
        ("nested_bool_integer_alias", changed(["review_boundary", "cohort_coverage_verified"], 0), "read_only_template_field_changed"),
        ("case_reset", changed(["original_case_attempts_remaining"], 1), "read_only_template_field_changed"),
        ("target_substitution", changed(["evaluation_intersections", 0, "dataset"], "synthetic_other"), "target_question_or_review_finding_changed"),
        ("claimed_verified_exclusion", changed(["evaluation_intersections", 0, "current_finding"], "verified_exclusion"), "target_question_or_review_finding_changed"),
        ("duplicate_identifiers", changed(["evaluation_intersections", 0, "dataset_versions"], ["synthetic_v1", "synthetic_v1"]), "duplicate_identifier"),
        ("missing_timezone", changed(["claimant", "statement_date_utc"], "2026-10-10T00:00:00"), "statement_date_must_be_utc"),
        ("coverage_integer_alias", changed(["training_inventory", "coverage_complete_attestation"], 1), "invalid_coverage_declaration"),
        ("bad_declared_checksum", changed(["checkpoint_training_link", "supplied_execution_record_sha256"], "not-a-checksum"), "invalid_sha256")]
    for name, raw, error in negatives:
        cases.append((name, lambda raw=raw, error=error: rejection(raw, error)))
    suite = unittest.TestSuite(unittest.FunctionTestCase(test, description=name) for name, test in cases)
    captured = io.StringIO()
    result = unittest.TextTestRunner(stream=captured, verbosity=2).run(suite)
    # Exercise the real CLI in the same owned Job, retaining only synthetic metadata.
    bad_path = args.output / "synthetic_bad_input.json"
    with bad_path.open("xb") as stream:
        stream.write(b'{"duplicate":1,"duplicate":2}')
    cli_valid = subprocess.run([sys.executable, "-I", "-S", "-B", str(P / "inspect_cohort.py"), "--input", str(P / "reference_template.json")],
                               check=False, capture_output=True, timeout=10)
    cli_bad = subprocess.run([sys.executable, "-I", "-S", "-B", str(P / "inspect_cohort.py"), "--input", str(bad_path)],
                             check=False, capture_output=True, timeout=10)
    assert cli_valid.returncode == 0 and not cli_valid.stderr
    assert_unverified(json.loads(cli_valid.stdout))
    assert cli_bad.returncode == 2 and not cli_bad.stderr and json.loads(cli_bad.stdout)["error_code"] == "duplicate_json_key"
    assert not any(name in sys.modules for name in ("numpy", "torch", "scipy", "safetensors"))
    report = {"schema": "pro3_guarded_synthetic_cohort_intake_tests_v1", "passed": result.wasSuccessful(),
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "test_names": [name for name, _ in cases], "cli_success_and_error_paths_executed": True,
              "unittest_output": captured.getvalue(), "template_sha256": hashlib.sha256(template_bytes).hexdigest(),
              "actual_cohort_evidence_received": False, "scientific_or_case_admission": False,
              "scientific_libraries_imported": False}
    with (args.output / "tests.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"passed": report["passed"], "tests_run": result.testsRun, "cli_paths": 2,
                      "scientific_or_case_admission": False}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
