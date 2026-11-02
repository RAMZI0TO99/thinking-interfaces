"""I/O-free preparation and supplied-stream primitives, never a supervisor."""

import hashlib

from .records import (MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES, ROLES,
                      Refusal, canonical_bytes, closed, defensive_copy,
                      exact_int, exact_string, path_key, require,
                      validate_file_descriptor, validate_snapshot, windows_path)

HASH_CHUNK_BYTES = 65_536
def _false_authority():
    # Fresh values: callers cannot mutate an exported shared policy dictionary.
    return {"complete_manifest": False, "runtime_qualified": False,
            "launch_authorized": False, "scientific_admission": False}


def _digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def hash_supplied_stream(stream, expected_bytes, checkpoint):
    """Hash from current position without opening/seeking/closing the stream.

    The trusted adapter supplies read(n) and an exact-True checkpoint (stop,
    clocks/resources/identity in a later supervisor). This function bounds each
    request but cannot prevent a hostile adapter from blocking or allocating.
    A one-byte EOF probe detects content beyond the declared length.
    """
    exact_int(expected_bytes, upper=MAX_FILE_BYTES)
    require(callable(checkpoint), "checkpoint required")
    digest = hashlib.sha256()
    count = 0
    while True:
        require(checkpoint() is True, "checkpoint refusal before read")
        amount = min(HASH_CHUNK_BYTES, expected_bytes - count + 1)
        chunk = stream.read(amount)
        require(checkpoint() is True, "checkpoint refusal after read")
        require(type(chunk) is bytes and len(chunk) <= amount, "bounded exact read bytes required")
        if not chunk:
            require(count == expected_bytes, "short supplied stream")
            return {"schema": "cho51_lv_stream_digest_v1", "bytes": count,
                    "sha256": digest.hexdigest()}
        count += len(chunk)
        require(count <= expected_bytes, "long supplied stream")
        digest.update(chunk)


def compare_census(initial, final):
    """Refuse any membership/content/identity/fact drift in supplied censuses."""
    initial, final = validate_snapshot(initial), validate_snapshot(final)
    for field in ("label", "role", "root"):
        require(initial[field] == final[field], "snapshot context drift")
    for field in ("directories", "files"):
        before = {entry["path"]: entry for entry in initial[field]}
        after = {entry["path"]: entry for entry in final[field]}
        require(set(before) == set(after), "added/missing census member")
        require(before == after, "census content/identity/fact drift")
    return {"schema": "cho51_lv_census_comparison_v1", "label": initial["label"],
            "supplied_censuses_equal": True, **_false_authority()}


def _snapshot_set(snapshots):
    require(type(snapshots) is list and 1 <= len(snapshots) <= 256, "bounded snapshot list required")
    # Bound the whole supplied set before allocating per-snapshot copies. The
    # 25k/4GiB limits concern declared files, not permission for huge JSON inputs.
    snapshots = defensive_copy(snapshots)
    result = {}
    for item in snapshots:
        item = validate_snapshot(item)
        require(item["label"] not in result, "duplicate snapshot label")
        result[item["label"]] = item
    return result


def assemble_proposal(initial_snapshots, final_snapshots, required_inputs):
    """Join explicitly supplied observations and pins, without closure inference.

    Each of the four roles must have a nonempty supplied snapshot. Required
    inputs are exact {path, role, bytes, sha256} pins. Their coverage says nothing
    about missing imports, loader configuration, metadata queries or DLLs.
    """
    initial = _snapshot_set(initial_snapshots)
    final = _snapshot_set(final_snapshots)
    require(set(initial) == set(final), "snapshot roster drift")
    files, paths, identities, roles = [], set(), set(), set()
    all_paths, all_identities = {}, {}
    total = 0
    for label in sorted(initial):
        item = initial[label]
        compare_census(item, final[label])
        require(item["files"], "empty role snapshot")
        roles.add(item["role"])
        for entry in item["directories"] + item["files"]:
            key = path_key(entry["path"])
            native = entry["native_identity"]
            identity = (native["volume_serial"], native["file_id"])
            require(key not in all_paths or all_paths[key] == entry, "cross-snapshot path facts/spelling drift")
            require(identity not in all_identities or all_identities[identity] == entry["path"],
                    "cross-snapshot native alias")
            all_paths[key] = entry
            all_identities[identity] = entry["path"]
        for entry in item["files"]:
            key = path_key(entry["path"])
            identity = (entry["native_identity"]["volume_serial"], entry["native_identity"]["file_id"])
            require(key not in paths and identity not in identities, "cross-snapshot alias/duplicate")
            paths.add(key)
            identities.add(identity)
            total += entry["bytes"]
            require(len(files) < MAX_FILES and total <= MAX_TOTAL_BYTES, "proposal aggregate limit")
            files.append({"role": item["role"], "snapshot_label": label, "descriptor": entry})
    require(roles == ROLES, "all four explicitly supplied closure roles required")
    require(type(required_inputs) is list and 1 <= len(required_inputs) <= MAX_FILES,
            "bounded nonempty required inputs")
    required_inputs = defensive_copy(required_inputs)
    by_path = {entry["descriptor"]["path"]: entry for entry in files}
    seen = set()
    for pin in required_inputs:
        closed(pin, ("path", "role", "bytes", "sha256"))
        windows_path(pin["path"], absolute=True)
        require(type(pin["role"]) is str and pin["role"] in ROLES, "pin role")
        exact_int(pin["bytes"], upper=MAX_FILE_BYTES)
        # Validate the digest and scalar field types using the same descriptor
        # validator; identity here is taken only from the supplied observation.
        require(pin["path"] in by_path and path_key(pin["path"]) not in seen, "missing/duplicate required pin")
        seen.add(path_key(pin["path"]))
        observed = by_path[pin["path"]]
        checked = validate_file_descriptor({**observed["descriptor"], "bytes": pin["bytes"], "sha256": pin["sha256"]})
        require(observed["role"] == pin["role"] and observed["descriptor"] == checked, "required input pin drift")
    files.sort(key=lambda entry: entry["descriptor"]["path"])
    proposal = {"schema": "cho51_lv_preparation_proposal_v1", "status": "SUPPLIED_DATA_ONLY_UNQUALIFIED",
                "file_count": len(files), "total_bytes": total, "files": files,
                "required_inputs": required_inputs,
                "snapshot_digests": [{"label": label, "initial_sha256": _digest(initial[label]),
                                      "final_sha256": _digest(final[label])} for label in sorted(initial)],
                **_false_authority()}
    return defensive_copy(proposal)


_MAPPING = "docs/phase2/cho51_p3_adapter_v1/test_mapping.py"
_TELEMETRY = "docs/phase2/cho51_p3_adapter_v1/test_telemetry.py"
EXPECTED_FUNCTIONS = (
    (_MAPPING, "test_boundary_path_refusal_precedes_adapter_reads", 2),
    (_MAPPING, "test_callback_objects_refused_without_access", 2),
    (_MAPPING, "test_changed_pinned_metadata_refused", 1),
    (_MAPPING, "test_changed_role_domain_refused", 4),
    (_MAPPING, "test_duplicate_or_nonfinite_json_refused", 3),
    (_MAPPING, "test_fabricated_scope_refused_after_genuine_boundary", 1),
    (_MAPPING, "test_finite_graph_and_encoded_byte_limits_refuse_before_serialization", 6),
    (_MAPPING, "test_fixed_intent_scope_refused", 9),
    (_MAPPING, "test_future_execution_obligations_cannot_be_prepared", 2),
    (_MAPPING, "test_genuine_historical_profile_and_complete_routes", 1),
    (_MAPPING, "test_intent_and_report_are_immutable_defensive_values", 1),
    (_MAPPING, "test_public_policy_views_cannot_mutate_authority", 1),
    (_MAPPING, "test_report_cannot_promote_authority_or_numerical_counts", 5),
    (_MAPPING, "test_stale_expected_boundary_assessment_refused", 1),
    (_TELEMETRY, "test_assessment_is_output_only_and_cannot_be_deserialized", 1),
    (_TELEMETRY, "test_complete_nested_metadata_and_defensive_views", 1),
    (_TELEMETRY, "test_equal_monotonic_ticks_are_not_a_missing_duration", 1),
    (_TELEMETRY, "test_explicit_qpc_domain_is_metadata_only", 1),
    (_TELEMETRY, "test_external_pins_and_exact_types_are_required", 4),
    (_TELEMETRY, "test_false_completion_or_abort_status_is_refused", 4),
    (_TELEMETRY, "test_join_rejects_cross_domain_and_order_errors", 19),
    (_TELEMETRY, "test_partial_timing_never_fabricates_missing_duration", 4),
    (_TELEMETRY, "test_segment_rejects_malformed_contract", 34),
    (_TELEMETRY, "test_segment_requires_exact_bounded_json_bytes", 5),
    (_TELEMETRY, "test_whole_trace_limits_are_not_reset_at_prefix_cut", 4),
)
EXPECTED_CONTROLS = (
    "finite_json", "duplicate_json", "nan_json", "overflow_json", "nested_json",
    "zero_budget", "boolean_budget", "owned_path", "escaped_path", "first_create",
    "duplicate_create", "bounded_tail", "local_full_window", "local_short_window",
    "junit_baseline", "junit_duplicate", "junit_failure", "junit_class",
    "reports_baseline", "reports_missing", "reports_duplicate", "git_actual_spelling_list",
    "git_actual_spelling_cmdline", "git_status_tail", "git_explicit_case_spelling",
    "git_alternate_executable", "git_alternate_argument_executable", "git_invalid_tail",
    "git_explicit_environment", "git_descendant_cwd", "git_relative_cwd",
    "pytest_alias_owned_paths", "pytest_alias_outside_paths", "pytest_alias_outside_destination",
)


def verify_collection_tallies(node_ids, expected_order=None):
    """Check supplied IDs, never collect tests or assert their execution/pass."""
    require(type(node_ids) is list and len(node_ids) == 117, "exact 117 supplied node IDs")
    node_ids = defensive_copy(node_ids)
    expected = {module + "::" + name: count for module, name, count in EXPECTED_FUNCTIONS}
    counts = {key: 0 for key in expected}
    seen = set()
    for node in node_ids:
        exact_string(node, 4096)
        require(not any(ord(c) < 32 for c in node), "node control character")
        require(node not in seen, "duplicate node ID")
        seen.add(node)
        prefix, separator, suffix = node.partition("[")
        require(prefix in expected, "unexpected module/function")
        require(not separator or (suffix.endswith("]") and len(suffix) > 1), "malformed parameter ID")
        counts[prefix] += 1
    require(counts == expected, "per-function collection tally mismatch")
    if expected_order is not None:
        require(type(expected_order) is list and node_ids == defensive_copy(expected_order), "ordered roster drift")
    return {"schema": "cho51_lv_supplied_roster_check_v1", "node_ids": node_ids,
            "ordered_sha256": _digest(node_ids), "function_count": 25,
            "mapping_count": 39, "telemetry_count": 78, "case_count": 117,
            "execution_established": False, **_false_authority()}


def verify_control_values(values):
    """Validate supplied 34 true values; their producer/execution is unverified."""
    values = defensive_copy(values)
    closed(values, EXPECTED_CONTROLS)
    require(all(value is True for value in values.values()), "exact Boolean true control values required")
    return {"schema": "cho51_lv_supplied_control_check_v1", "control_count": 34,
            "controls": values, "execution_established": False, **_false_authority()}
