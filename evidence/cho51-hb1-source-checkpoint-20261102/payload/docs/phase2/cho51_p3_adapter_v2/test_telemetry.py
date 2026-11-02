"""Fabricated timing metadata only: no clock, profiler or numerical execution."""

from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from .contracts import CONTROLLER, PROFILE, canonical_json, sha256
from .telemetry import PHASES, TimingAssessment, TimingSegment, assess_timing_trace


def record(sequence, span_id, parent_id, phase, event, timestamp, occurrence=1):
    return {
        "sequence": sequence, "span_id": span_id, "parent_id": parent_id,
        "phase": phase, "occurrence": occurrence, "event": event, "time_ns": timestamp,
        "outcome": "incomplete" if event == "begin" else "completed", "reason": "none",
    }


def coverage(**observations):
    return [
        {"phase": phase, "outcome": observations.get(phase, "not_observed"),
         "reason": "none" if observations.get(phase) == "completed" else
                   "missing_endpoint" if observations.get(phase) == "incomplete" else "not_instrumented"}
        for phase in PHASES
    ]


def segment(payload):
    encoded = canonical_json(payload)
    return TimingSegment(encoded, sha256(encoded.encode("utf-8")))


def counted(payload):
    payload["event_count"] = len(payload["records"])
    payload["normal_record_count"] = sum(row["event"] in ("begin", "end") for row in payload["records"])
    payload["reserved_record_count"] = len(payload["records"]) - payload["normal_record_count"]
    return payload


def pair():
    first = {
        "schema": "cho51_p3_timing_trace_v1", "controller": CONTROLLER, "profile": PROFILE,
        "role": "prefix", "process": {"pid": 101, "creation_identity": "fixture-generation-1", "thread_id": 7},
        "clock": {"name": "perf_counter_ns", "domain_id": "fixture-clock-1", "resolution_ns": 1, "frequency_hz": None},
        "pins": {"operations_sha256": "a" * 64, "controller_source_sha256": "b" * 64,
                 "command_sha256": "c" * 64, "native_directory": "runs/migration/fabricated"},
        "buffer_start_ns": 0, "buffer_end_ns": 40, "start_stack": [], "end_stack": ["controller.1"],
        "prefix_sha256": None,
        "records": [record(0, "controller.1", None, "controller", "begin", 0),
                    record(1, "route.1", "controller.1", "route_profile_preflight", "begin", 10),
                    record(2, "route.1", "controller.1", "route_profile_preflight", "end", 30)],
        "required_phases": ["controller", "route_profile_preflight", "outer_attestation"],
        "coverage": coverage(controller="incomplete", route_profile_preflight="completed"),
        "status": "incomplete", "truncated": False,
    }
    counted(first)
    second = deepcopy(first)
    second.update({
        "role": "finalization_tail", "buffer_start_ns": 40, "buffer_end_ns": 100,
        "start_stack": ["controller.1"], "end_stack": [], "prefix_sha256": segment(first).expected_sha256,
        "records": [record(3, "attest.1", "controller.1", "outer_attestation", "begin", 50),
                    record(4, "attest.1", "controller.1", "outer_attestation", "end", 60),
                    record(5, "controller.1", None, "controller", "end", 90)],
        "coverage": coverage(controller="completed", route_profile_preflight="completed", outer_attestation="completed"),
        "status": "completed",
    })
    return first, counted(second)


def assess(first, second):
    prefix = segment(first)
    tail = segment(second)
    return assess_timing_trace(prefix, tail, external_result_sha256="d" * 64,
                               expected_prefix_sha256=prefix.expected_sha256, expected_tail_sha256=tail.expected_sha256)


def valid_pair():
    first, second = pair()
    assert assess(first, second).report["requested_coverage_complete"] is True
    return first, second


def test_complete_nested_metadata_and_defensive_views():
    first, second = valid_pair()
    result = assess(first, second)
    report = result.report
    spans = {row["span_id"]: row for row in report["spans"]}
    assert spans["controller.1"]["inclusive_wall_ns"] == 90
    assert spans["controller.1"]["unattributed_wall_residual_ns"] == 60
    assert spans["route.1"]["inclusive_wall_ns"] == 20
    assert spans["attest.1"]["inclusive_wall_ns"] == 10
    assert report["normal_records"] == 6 and report["reserved_records"] == 0
    for name in ("execution_admitted", "scientific_admission", "physical_trace_files_verified", "whole_process_lifetime_covered"):
        assert report[name] is False
    assert report["unobserved_finalization"] == ["tail_file_persistence", "final_process_exit"]
    report["spans"].clear()
    assert len(result.report["spans"]) == 3
    prefix = segment(first)
    prefix.payload["process"]["pid"] = 999
    assert prefix.payload["process"]["pid"] == 101
    with pytest.raises(FrozenInstanceError):
        prefix.payload_json = "{}"
    assert len(result.sha256) == 64


@pytest.mark.parametrize("case", [
    "unknown_field", "schema", "profile", "controller", "pid_bool", "thread_zero", "creation_identity",
    "clock", "resolution_bool", "frequency", "qpc_no_frequency", "native_absolute", "pin_digest",
    "reverse_endpoints", "unhashable_stack", "duplicate_stack", "self_prefix", "required_duplicate",
    "coverage_missing", "coverage_order", "coverage_false_reason", "status", "truncated_integer",
    "count_bool", "count_mismatch", "record_unknown", "record_time_bool", "record_occurrence_zero",
    "record_phase", "record_outcome", "record_event", "record_outside", "begin_completed", "end_incomplete",
])
def test_segment_rejects_malformed_contract(case):
    first, second = valid_pair()
    if case == "unknown_field": first["authority"] = True
    elif case in ("schema", "profile", "controller"): first[case] = "unrecognized"
    elif case == "pid_bool": first["process"]["pid"] = True
    elif case == "thread_zero": first["process"]["thread_id"] = 0
    elif case == "creation_identity": first["process"]["creation_identity"] = ""
    elif case == "clock": first["clock"]["name"] = "wall_clock"
    elif case == "resolution_bool": first["clock"]["resolution_ns"] = True
    elif case == "frequency": first["clock"]["frequency_hz"] = 1000
    elif case == "qpc_no_frequency": first["clock"]["name"] = "qpc"
    elif case == "native_absolute": first["pins"]["native_directory"] = "C:/fixture"
    elif case == "pin_digest": first["pins"]["command_sha256"] = "x" * 64
    elif case == "reverse_endpoints": first["buffer_end_ns"] = -1
    elif case == "unhashable_stack": first["end_stack"] = [{}]
    elif case == "duplicate_stack": first["end_stack"] *= 2
    elif case == "self_prefix": first["prefix_sha256"] = "a" * 64
    elif case == "required_duplicate": first["required_phases"] *= 2
    elif case == "coverage_missing": first["coverage"].pop()
    elif case == "coverage_order": first["coverage"].reverse()
    elif case == "coverage_false_reason": first["coverage"][0]["reason"] = "none"
    elif case == "status": first["status"] = "completed"
    elif case == "truncated_integer": first["truncated"] = 1
    elif case == "count_bool": first["event_count"] = True
    elif case == "count_mismatch": first["event_count"] += 1
    elif case == "record_unknown": first["records"][0]["extra"] = None
    elif case == "record_time_bool": first["records"][0]["time_ns"] = False
    elif case == "record_occurrence_zero": first["records"][0]["occurrence"] = 0
    elif case == "record_phase": first["records"][0]["phase"] = "train"
    elif case == "record_outcome": first["records"][0]["outcome"] = "success"
    elif case == "record_event": first["records"][0]["event"] = "instant"
    elif case == "record_outside": first["records"][0]["time_ns"] = 41
    elif case == "begin_completed": first["records"][0]["outcome"] = "completed"
    elif case == "end_incomplete": first["records"][2]["outcome"] = "incomplete"
    with pytest.raises(ValueError):
        segment(first)


@pytest.mark.parametrize("case", [
    "pid", "generation", "thread", "clock_domain", "clock_resolution", "source_pin", "required_phases",
    "cut_time", "cut_stack", "prefix_pin", "sequence", "clock_regression", "parent", "occurrence",
    "duplicate_span", "unknown_closure", "closure_phase", "coverage_contradiction", "unclosed",
])
def test_join_rejects_cross_domain_and_order_errors(case):
    first, second = valid_pair()
    if case == "pid": second["process"]["pid"] += 1
    elif case == "generation": second["process"]["creation_identity"] += "-new"
    elif case == "thread": second["process"]["thread_id"] += 1
    elif case == "clock_domain": second["clock"]["domain_id"] += "-new"
    elif case == "clock_resolution": second["clock"]["resolution_ns"] += 1
    elif case == "source_pin": second["pins"]["operations_sha256"] = "e" * 64
    elif case == "required_phases": second["required_phases"] = ["controller"]
    elif case == "cut_time": second["buffer_start_ns"] += 1
    elif case == "cut_stack": second["start_stack"] = []
    elif case == "prefix_pin": second["prefix_sha256"] = "e" * 64
    elif case == "sequence": second["records"][0]["sequence"] += 1
    elif case == "clock_regression": second["records"][1]["time_ns"] = 49
    elif case == "parent": second["records"][0]["parent_id"] = None
    elif case == "occurrence": second["records"][0]["occurrence"] = 2
    elif case == "duplicate_span": second["records"][0]["span_id"] = "route.1"
    elif case == "unknown_closure": second["records"][1]["span_id"] = "unknown.1"
    elif case == "closure_phase": second["records"][1]["phase"] = "restore"
    elif case == "coverage_contradiction": second["coverage"] = first["coverage"]
    elif case == "unclosed": second["records"].pop(); counted(second)
    with pytest.raises(ValueError):
        assess(first, second)


@pytest.mark.parametrize("case", ["wrong_expected", "duplicate_json", "nan_json", "oversized", "bytes_json"])
def test_segment_requires_exact_bounded_json_bytes(case):
    first, second = valid_pair()
    encoded = segment(first).payload_json
    expected = sha256(encoded.encode("utf-8"))
    if case == "wrong_expected": expected = "0" * 64
    elif case == "duplicate_json": encoded = '{"schema":1,"schema":2}'
    elif case == "nan_json": encoded = '{"value":NaN}'
    elif case == "oversized": encoded = '"' + "x" * (512 * 1024) + '"'
    elif case == "bytes_json": encoded = encoded.encode("utf-8")
    if type(encoded) is str and case != "wrong_expected": expected = sha256(encoded.encode("utf-8"))
    with pytest.raises(ValueError):
        TimingSegment(encoded, expected)


@pytest.mark.parametrize("case", ["prefix", "tail", "external", "mutable_input"])
def test_external_pins_and_exact_types_are_required(case):
    first, second = valid_pair()
    prefix, tail = segment(first), segment(second)
    arguments = {"external_result_sha256": "d" * 64, "expected_prefix_sha256": prefix.expected_sha256,
                 "expected_tail_sha256": tail.expected_sha256}
    if case == "prefix": arguments["expected_prefix_sha256"] = "e" * 64
    elif case == "tail": arguments["expected_tail_sha256"] = "e" * 64
    elif case == "external": arguments["external_result_sha256"] = True
    elif case == "mutable_input": prefix = first
    with pytest.raises(ValueError):
        assess_timing_trace(prefix, tail, **arguments)


@pytest.mark.parametrize("case", ["incomplete", "abort", "truncated", "gap"])
def test_partial_timing_never_fabricates_missing_duration(case):
    first, second = valid_pair()
    second["status"] = "incomplete"
    if case == "incomplete":
        second["records"] = second["records"][:1]
        second["end_stack"] = ["controller.1", "attest.1"]
        second["coverage"] = coverage(controller="incomplete", route_profile_preflight="completed", outer_attestation="incomplete")
    elif case == "abort":
        second["records"][1].update(event="abort", outcome="aborted", reason="exception")
        second["coverage"] = coverage(controller="completed", route_profile_preflight="completed", outer_attestation="aborted")
        second["status"] = "aborted"
    elif case == "truncated": second["truncated"] = True
    elif case == "gap":
        second["records"].append({"sequence": 6, "span_id": "gap.1", "parent_id": None, "phase": "result_write",
                                   "occurrence": 1, "event": "coverage", "time_ns": 95,
                                   "outcome": "not_observed", "reason": "not_instrumented"})
    counted(second)
    report = assess(first, second).report
    assert report["requested_coverage_complete"] is False
    assert report["execution_admitted"] is False
    if case in ("incomplete", "abort"):
        spans = {row["span_id"]: row for row in report["spans"]}
        assert spans["attest.1"]["inclusive_wall_ns"] is None
        assert spans["controller.1"]["unattributed_wall_residual_ns"] is None


@pytest.mark.parametrize("case", ["reserved", "depth", "normal", "span"])
def test_whole_trace_limits_are_not_reset_at_prefix_cut(case):
    first, second = valid_pair()
    if case == "reserved":
        for payload, start_sequence, timestamp in ((first, 3, 35), (second, 15, 95)):
            records = payload["records"]
            if payload is second:
                for row in records: row["sequence"] += 12
            for index in range(12):
                records.append({"sequence": start_sequence + index if payload is first else 18 + index,
                                "span_id": f"gap.{timestamp}.{index}", "parent_id": None, "phase": "result_write",
                                "occurrence": 1, "event": "coverage", "time_ns": timestamp,
                                "outcome": "not_observed", "reason": "not_instrumented"})
            counted(payload)
        second["status"] = "incomplete"
    else:
        records = []
        stack = []
        total = 17 if case == "depth" else 257
        for index in range(total):
            parent = stack[-1] if case == "depth" and stack else None
            identifier = f"fixture.{index}"
            phase = "controller" if case == "depth" or index % 2 == 0 else "route_profile_preflight"
            occurrence = index + 1 if case == "depth" else index // 2 + 1
            records.append(record(len(records), identifier, parent, phase, "begin", 0, occurrence))
            if case == "depth": stack.append(identifier)
            else:
                closure = record(len(records), identifier, None, phase, "end", 0, occurrence)
                if case == "span" and index < 2:
                    closure.update(event="abort", outcome="aborted", reason="exception")
                records.append(closure)
        if case == "depth":
            first["records"] = records
            first["end_stack"] = stack[:16]
        else:
            first["records"] = records[:256]
            second["records"] = records[256:]
            second["buffer_start_ns"] = 40
            for row in second["records"]: row["time_ns"] = 50
            first["end_stack"] = []
            second["start_stack"] = []
            observed = "aborted" if case == "span" else "completed"
            first["coverage"] = coverage(controller=observed, route_profile_preflight=observed)
            second["coverage"] = deepcopy(first["coverage"])
            second["status"] = "incomplete"
        counted(first); counted(second)
    second["prefix_sha256"] = segment(first).expected_sha256
    with pytest.raises(ValueError):
        assess(first, second)


def test_assessment_is_output_only_and_cannot_be_deserialized():
    first, second = valid_pair()
    result = assess(first, second)
    with pytest.raises(ValueError, match="output only"):
        TimingAssessment(result.canonical_json)
    with pytest.raises(FrozenInstanceError):
        result.canonical_json = "{}"


@pytest.mark.parametrize("case", ["incomplete", "abort", "truncated", "false_abort"])
def test_false_completion_or_abort_status_is_refused(case):
    first, second = valid_pair()
    if case == "incomplete":
        second["records"] = second["records"][:1]
        second["end_stack"] = ["controller.1", "attest.1"]
        second["coverage"] = coverage(controller="incomplete", route_profile_preflight="completed", outer_attestation="incomplete")
    elif case == "abort":
        second["records"][1].update(event="abort", outcome="aborted", reason="hard_stop")
        second["coverage"] = coverage(controller="completed", route_profile_preflight="completed", outer_attestation="aborted")
    elif case == "truncated": second["truncated"] = True
    elif case == "false_abort": second["status"] = "aborted"
    counted(second)
    with pytest.raises(ValueError):
        assess(first, second)


def test_explicit_qpc_domain_is_metadata_only():
    first, second = valid_pair()
    for payload in (first, second):
        payload["clock"].update(name="qpc", frequency_hz=10000000)
    second["prefix_sha256"] = segment(first).expected_sha256
    report = assess(first, second).report
    assert report["clock"]["frequency_hz"] == 10000000
    assert report["physical_trace_files_verified"] is False


def test_equal_monotonic_ticks_are_not_a_missing_duration():
    first, second = valid_pair()
    first["records"][2]["time_ns"] = first["records"][1]["time_ns"]
    second["prefix_sha256"] = segment(first).expected_sha256
    spans = {row["span_id"]: row for row in assess(first, second).report["spans"]}
    assert spans["route.1"]["inclusive_wall_ns"] == 0
    assert spans["route.1"]["unattributed_wall_residual_ns"] == 0
