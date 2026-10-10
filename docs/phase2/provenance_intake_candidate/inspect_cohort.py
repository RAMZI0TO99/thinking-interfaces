"""Bounded metadata inspection candidate; no evidence authentication or admission."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import stat

MAX_BYTES = 1024 * 1024
MAX_DEPTH = 16
MAX_NODES = 10000
MAX_TEXT = 4096
# The trusted template is pinned separately from the submitted bytes.
TEMPLATE_SHA256 = "d62cb5450578fa8ea0e90856cb314eb183db93f401a64e1aae5d28f4f536ceab"
TEMPLATE_PATH = Path(__file__).resolve().parent / "reference_template.json"


class IntakeError(ValueError):
    """A stable error code; never echo submitted values or URLs."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise IntakeError("duplicate_json_key")
        result[key] = value
    return result


def _nonfinite(value):
    raise IntakeError("nonfinite_json_number")


def _decode(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise IntakeError("metadata_size_or_type")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_nonfinite)
    except IntakeError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError):
        raise IntakeError("invalid_json_or_utf8") from None
    count = 0
    pending = [(value, 0)]
    while pending:
        node, depth = pending.pop()
        count += 1
        if depth > MAX_DEPTH or count > MAX_NODES:
            raise IntakeError("metadata_structure_bound")
        if type(node) is dict:
            pending.extend((x, depth + 1) for x in node.values())
        elif type(node) is list:
            pending.extend((x, depth + 1) for x in node)
        elif type(node) is str and len(node) > MAX_TEXT:
            raise IntakeError("metadata_text_bound")
        elif type(node) is float:
            # Includes numeric overflow such as 1e999, even though it is valid JSON syntax.
            raise IntakeError("floating_number_not_in_schema")
    return value


def read_metadata(path):
    """Read one regular metadata file; no reference traversal or network access."""
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or getattr(before, "st_file_attributes", 0) & 0x400:
            raise IntakeError("nonregular_metadata_file")
        if not 0 < before.st_size <= MAX_BYTES:
            raise IntakeError("metadata_size_or_type")
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        after = path.lstat()
    except IntakeError:
        raise
    except OSError:
        raise IntakeError("metadata_read_failed") from None
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino) or len(raw) != before.st_size:
        raise IntakeError("metadata_changed_during_read")
    return raw


def _text(value, *, nullable=False):
    if nullable and value is None:
        return
    if type(value) is not str or not value.strip() or len(value) > MAX_TEXT:
        raise IntakeError("invalid_text_field")


def _strings(value):
    if type(value) is not list:
        raise IntakeError("invalid_identifier_list")
    for item in value:
        _text(item)
    if len(value) != len(set(value)):
        raise IntakeError("duplicate_identifier")


def _shape(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise IntakeError("missing_or_unexpected_field")


def _same(value, reference):
    if type(value) is not type(reference):
        return False
    if type(reference) is dict:
        return set(value) == set(reference) and all(_same(value[key], item) for key, item in reference.items())
    if type(reference) is list:
        return len(value) == len(reference) and all(_same(x, y) for x, y in zip(value, reference))
    return value == reference


def _items(value, keys, *, list_keys=(), nullable_keys=()):
    if type(value) is not list:
        raise IntakeError("invalid_record_list")
    for item in value:
        _shape(item, keys)
        for key, content in item.items():
            if key in list_keys:
                _strings(content)
            else:
                _text(content, nullable=key in nullable_keys)
            if key == "sha256" and content is not None and (len(content) != 64 or any(c not in "0123456789abcdef" for c in content)):
                raise IntakeError("invalid_sha256")


def inspect_bytes(raw):
    """Validate declarations; every scientific verification flag remains false."""
    trusted = read_metadata(TEMPLATE_PATH)
    if hashlib.sha256(trusted).hexdigest() != TEMPLATE_SHA256:
        raise IntakeError("trusted_template_hash_mismatch")
    reference = _decode(trusted)
    value = _decode(raw)
    _shape(value, reference)
    mutable = {"claimant", "checkpoint_training_link", "training_inventory", "evaluation_intersections", "evidence_items"}
    for key in set(reference) - mutable:
        # JSON type equality is explicit: false must not masquerade as integer zero.
        if not _same(value[key], reference[key]):
            raise IntakeError("read_only_template_field_changed")
    for section in ("claimant", "checkpoint_training_link"):
        _shape(value[section], reference[section])
        for item in value[section].values():
            _text(item, nullable=True)
    declared_sha = value["checkpoint_training_link"]["supplied_execution_record_sha256"]
    if declared_sha is not None and (len(declared_sha) != 64 or any(c not in "0123456789abcdef" for c in declared_sha)):
        raise IntakeError("invalid_sha256")
    date = value["claimant"]["statement_date_utc"]
    if date is not None:
        try:
            parsed = datetime.fromisoformat(date.replace("Z", "+00:00"))
            if parsed.utcoffset() != timedelta(0):
                raise ValueError
        except ValueError:
            raise IntakeError("statement_date_must_be_utc") from None
    training = value["training_inventory"]
    _shape(training, reference["training_inventory"])
    if training["coverage_complete_attestation"] is not None and type(training["coverage_complete_attestation"]) is not bool:
        raise IntakeError("invalid_coverage_declaration")
    _text(training["known_omissions"], nullable=True)
    _items(training["dataset_entries"], ("dataset", "version", "identifier_namespace", "subject_identifiers", "recording_identifiers", "coverage_statement"),
           list_keys=("subject_identifiers", "recording_identifiers"))
    _items(training["identifier_namespaces"], ("name", "dataset", "version", "definition"))
    _items(training["split_definitions"], ("dataset", "version", "name", "definition"))
    _items(training["exclusion_statements"], ("dataset", "version", "scope", "statement", "evidence_reference"))
    targets = value["evaluation_intersections"]
    if type(targets) is not list or len(targets) != 3:
        raise IntakeError("target_question_roster_changed")
    for item, expected in zip(targets, reference["evaluation_intersections"]):
        _shape(item, expected)
        if item["dataset"] != expected["dataset"] or item["current_finding"] != "unknown":
            raise IntakeError("target_question_or_review_finding_changed")
        for key in ("dataset_versions",):
            _strings(item[key])
        for key in ("subject_identifier_mapping", "recording_identifier_mapping"):
            _items(item[key], ("training_identifier", "evaluation_identifier", "mapping_evidence_reference"))
        for key in ("subject_intersection", "recording_intersection"):
            if item[key] is not None:
                _strings(item[key])
        for key in ("evaluation_inventory_reference", "evaluation_inventory_sha256", "label_exposure_statement", "training_inclusion_statement", "coverage_basis"):
            _text(item[key], nullable=True)
        declared = item["evaluation_inventory_sha256"]
        if declared is not None and (len(declared) != 64 or any(c not in "0123456789abcdef" for c in declared)):
            raise IntakeError("invalid_sha256")
    _items(value["evidence_items"], ("reference", "description", "source_date_utc", "sha256", "supported_claims"),
           list_keys=("supported_claims",), nullable_keys=("sha256",))
    missing = [f"{section}.{key}" for section in ("claimant", "checkpoint_training_link")
               for key, content in value[section].items() if content is None]
    for key in ("dataset_entries", "identifier_namespaces", "split_definitions"):
        if not training[key]:
            missing.append("training_inventory." + key)
    if training["coverage_complete_attestation"] is not True:
        missing.append("training_inventory.complete_coverage_claim")
    if not value["evidence_items"]:
        missing.append("evidence_items")
    for item in targets:
        for key in ("evaluation_inventory_reference", "evaluation_inventory_sha256", "dataset_versions", "coverage_basis"):
            if not item[key]:
                missing.append("evaluation_intersections." + item["dataset"] + "." + key)
    return {"schema": "pro3_cohort_metadata_inspection_candidate_report_v1", "format_valid": True,
            "status": "incomplete_declarations" if missing else "declarations_present_unverified",
            "input_sha256": hashlib.sha256(raw).hexdigest(), "input_bytes": len(raw), "trusted_template_sha256": TEMPLATE_SHA256,
            "missing_declaration_fields": sorted(missing), "declared_dataset_entries": len(training["dataset_entries"]),
            "declared_evidence_items": len(value["evidence_items"]),
            "evaluation_findings": {item["dataset"]: "unknown" for item in targets},
            "claimant_authenticated": False, "training_run_link_verified": False, "cohort_coverage_verified": False,
            "referenced_artifacts_fetched_or_opened": False, "scientific_gate_a_signed": False,
            "experiment_freeze_signed": False, "training_or_case_admitted": False, "original_case_attempts_remaining": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = inspect_bytes(read_metadata(args.input))
    except IntakeError as error:
        print(json.dumps({"format_valid": False, "error_code": str(error), "training_or_case_admitted": False}))
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
