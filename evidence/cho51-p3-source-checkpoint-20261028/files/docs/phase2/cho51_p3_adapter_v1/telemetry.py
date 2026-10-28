"""Pure validation of caller-supplied timing metadata; no instrumentation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .contracts import (
    CONTROLLER, PROFILE, canonical_json, decode_json, digest_text, exact_fields,
    exact_int, relative_path, sha256,
)

MAX_SPANS = 256
MAX_NORMAL_RECORDS = 512
MAX_RESERVED_RECORDS = 16
MAX_TRACE_BYTES = 512 * 1024
RESERVED_BYTES = 16 * 1024
MAX_RECORD_BYTES = 1024
MAX_DEPTH = 16
PHASES = (
    "imports_guard", "pins_source", "historical_origin", "physical_input_audit",
    "route_profile_preflight", "target_route", "restore", "support_adaptation",
    "query_forward_only", "verifier", "prefix_seal", "outer_attestation",
    "engineering_terminal", "module_finish", "result_write", "controller",
)
REASONS = ("none", "not_instrumented", "exception", "hard_stop", "record_limit", "byte_limit", "missing_endpoint", "coverage_gap")
OUTCOMES = ("completed", "aborted", "incomplete", "not_observed")
_RECORD_FIELDS = {"sequence", "span_id", "parent_id", "phase", "occurrence", "event", "time_ns", "outcome", "reason"}
_SEGMENT_FIELDS = {
    "schema", "controller", "profile", "role", "process", "clock", "pins",
    "buffer_start_ns", "buffer_end_ns", "start_stack", "end_stack", "prefix_sha256",
    "records", "required_phases", "coverage", "status", "truncated",
    "event_count", "normal_record_count", "reserved_record_count",
}


def _identifier(value: Any) -> str:
    if type(value) is not str or re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,95}", value) is None:
        raise ValueError("bounded scalar identifier required")
    return value


def _stack(value: Any) -> None:
    if type(value) is not list or len(value) > MAX_DEPTH:
        raise ValueError("bounded unique open-stack identifiers required")
    for identifier in value:
        _identifier(identifier)
    if len(set(value)) != len(value):
        raise ValueError("bounded unique open-stack identifiers required")


def _record(row: Any) -> None:
    exact_fields(row, _RECORD_FIELDS, "trace record")
    if len(canonical_json(row).encode("utf-8")) > MAX_RECORD_BYTES:
        raise ValueError("record byte bound exceeded")
    for name in ("sequence", "time_ns"):
        exact_int(row[name])
    exact_int(row["occurrence"], 1, MAX_SPANS)
    _identifier(row["span_id"])
    if row["parent_id"] is not None:
        _identifier(row["parent_id"])
    if row["phase"] not in PHASES or row["reason"] not in REASONS or row["outcome"] not in OUTCOMES:
        raise ValueError("unknown phase/outcome/reason enum")
    event = row["event"]
    if event not in ("begin", "end", "abort", "coverage"):
        raise ValueError("unknown trace event")
    if event == "begin" and (row["outcome"] != "incomplete" or row["reason"] != "none"):
        raise ValueError("begin cannot claim a completed outcome")
    if event == "end" and (row["outcome"] != "completed" or row["reason"] != "none"):
        raise ValueError("end requires actual completed metadata")
    if event == "abort" and (row["outcome"] != "aborted" or row["reason"] == "none"):
        raise ValueError("abort requires an explicit failure reason")
    if event == "coverage" and (row["outcome"] not in ("incomplete", "not_observed") or row["reason"] == "none" or row["parent_id"] is not None):
        raise ValueError("coverage requires a gap and never claims a duration")


def _segment(payload: Any) -> None:
    exact_fields(payload, _SEGMENT_FIELDS, "timing segment")
    if (payload["schema"] != "cho51_p3_timing_trace_v1" or payload["controller"] != CONTROLLER
            or payload["profile"] != PROFILE or payload["role"] not in ("prefix", "finalization_tail")):
        raise ValueError("unknown versioned timing domain")
    process = exact_fields(payload["process"], {"pid", "creation_identity", "thread_id"}, "process generation")
    exact_int(process["pid"], 1)
    exact_int(process["thread_id"], 1)
    _identifier(process["creation_identity"])
    clock = exact_fields(payload["clock"], {"name", "domain_id", "resolution_ns", "frequency_hz"}, "clock domain")
    if clock["name"] not in ("perf_counter_ns", "monotonic_ns", "qpc"):
        raise ValueError("unknown monotonic clock")
    _identifier(clock["domain_id"])
    exact_int(clock["resolution_ns"], 1)
    if clock["name"] == "qpc":
        exact_int(clock["frequency_hz"], 1)
    elif clock["frequency_hz"] is not None:
        raise ValueError("raw frequency belongs only to the QPC domain")
    pins = exact_fields(payload["pins"], {"operations_sha256", "controller_source_sha256", "command_sha256", "native_directory"}, "trace pins")
    for name in ("operations_sha256", "controller_source_sha256", "command_sha256"):
        digest_text(pins[name])
    relative_path(pins["native_directory"])
    start = exact_int(payload["buffer_start_ns"])
    finish = exact_int(payload["buffer_end_ns"])
    if finish < start:
        raise ValueError("clock regressed across segment endpoints")
    for name in ("start_stack", "end_stack"):
        _stack(payload[name])
    if payload["role"] == "prefix":
        if payload["prefix_sha256"] is not None or payload["start_stack"]:
            raise ValueError("prefix cannot bind itself, a future tail, or an unknown initial stack")
    else:
        digest_text(payload["prefix_sha256"])
    records = payload["records"]
    if type(records) is not list or len(records) > MAX_NORMAL_RECORDS + MAX_RESERVED_RECORDS:
        raise ValueError("record count exceeds the whole-trace bound")
    for row in records:
        _record(row)
        if not start <= row["time_ns"] <= finish:
            raise ValueError("record lies outside its declared segment")
    normal = sum(row["event"] in ("begin", "end") for row in records)
    reserved = len(records) - normal
    for name, expected in (("event_count", len(records)), ("normal_record_count", normal), ("reserved_record_count", reserved)):
        if exact_int(payload[name]) != expected:
            raise ValueError("declared exact record counts differ")
    required = payload["required_phases"]
    if type(required) is not list or not required or any(type(phase) is not str or phase not in PHASES for phase in required) or len(set(required)) != len(required):
        raise ValueError("explicit unique finite requested phase inventory required")
    coverage = payload["coverage"]
    if type(coverage) is not list or len(coverage) != len(PHASES):
        raise ValueError("complete finite phase coverage inventory required")
    for phase, row in zip(PHASES, coverage):
        exact_fields(row, {"phase", "outcome", "reason"}, "phase coverage")
        if row["phase"] != phase or row["outcome"] not in OUTCOMES or row["reason"] not in REASONS:
            raise ValueError("ordered coverage inventory or enum differs")
        if (row["outcome"] == "completed") != (row["reason"] == "none"):
            raise ValueError("coverage failure cannot have an empty reason")
    if payload["status"] not in ("incomplete", "aborted", "completed") or type(payload["truncated"]) is not bool:
        raise ValueError("explicit trace status and truncation Boolean required")
    if payload["role"] == "prefix" and payload["status"] != "incomplete":
        raise ValueError("prefix cannot claim whole requested timing completion")
    if payload["truncated"] and payload["status"] == "completed":
        raise ValueError("truncated timing cannot claim completion")


@dataclass(frozen=True, slots=True)
class TimingSegment:
    payload_json: str
    expected_sha256: str

    def __post_init__(self) -> None:
        if type(self.payload_json) is not str:
            raise ValueError("exact immutable timing JSON text required")
        digest_text(self.expected_sha256)
        payload = decode_json(self.payload_json, maximum=MAX_TRACE_BYTES)
        if sha256(self.payload_json.encode("utf-8")) != self.expected_sha256:
            raise ValueError("timing segment differs from independent byte pin")
        _segment(payload)

    @property
    def payload(self) -> dict[str, Any]:
        return decode_json(self.payload_json, maximum=MAX_TRACE_BYTES)


@dataclass(frozen=True, slots=True, init=False)
class TimingAssessment:
    """Output of trace assessment, never a caller-deserializable validity claim."""

    canonical_json: str

    def __init__(self, *arguments: Any, **keywords: Any) -> None:
        raise ValueError("TimingAssessment is output only; reassess the pinned trace segments")

    @property
    def report(self) -> dict[str, Any]:
        return decode_json(self.canonical_json, maximum=MAX_TRACE_BYTES)

    @property
    def sha256(self) -> str:
        return sha256(self.canonical_json.encode("utf-8"))


def _union(intervals: list[tuple[int, int]]) -> int:
    total = 0
    end = 0
    for start, finish in sorted(intervals):
        total += max(0, finish - max(start, end))
        end = max(end, finish)
    return total


def assess_timing_trace(prefix: TimingSegment, tail: TimingSegment, *, external_result_sha256: str,
                        expected_prefix_sha256: str, expected_tail_sha256: str) -> TimingAssessment:
    """Join two immutable metadata segments; physical/external validation remains separate."""
    if type(prefix) is not TimingSegment or type(tail) is not TimingSegment:
        raise ValueError("exact immutable timing segment types required")
    for digest in (external_result_sha256, expected_prefix_sha256, expected_tail_sha256):
        digest_text(digest)
    if prefix.expected_sha256 != expected_prefix_sha256 or tail.expected_sha256 != expected_tail_sha256:
        raise ValueError("external segment byte pins differ")
    first, second = prefix.payload, tail.payload
    if first["role"] != "prefix" or second["role"] != "finalization_tail" or second["prefix_sha256"] != expected_prefix_sha256:
        raise ValueError("acyclic prefix-to-tail join differs")
    for name in ("process", "clock", "pins", "required_phases"):
        if canonical_json(first[name]) != canonical_json(second[name]):
            raise ValueError("mixed process generation/thread/clock/source domain refused")
    if first["buffer_end_ns"] != second["buffer_start_ns"] or first["end_stack"] != second["start_stack"]:
        raise ValueError("finalization tail must start exactly when prefix freezes with the same open stack")
    total_bytes = len(prefix.payload_json.encode("utf-8")) + len(tail.payload_json.encode("utf-8"))
    records = first["records"] + second["records"]
    normal = first["normal_record_count"] + second["normal_record_count"]
    reserved = first["reserved_record_count"] + second["reserved_record_count"]
    reserved_bytes = sum(len(canonical_json(row).encode("utf-8")) for row in records if row["event"] in ("abort", "coverage"))
    if (normal > MAX_NORMAL_RECORDS or reserved > MAX_RESERVED_RECORDS or total_bytes > MAX_TRACE_BYTES
            or reserved_bytes > RESERVED_BYTES or total_bytes - reserved_bytes > MAX_TRACE_BYTES - RESERVED_BYTES):
        raise ValueError("combined two-segment record/byte/reserve bound exceeded")
    spans: dict[str, dict[str, Any]] = {}
    stack: list[str] = []
    occurrence_counts: dict[str, int] = {}
    coverage_ids: set[str] = set()
    gaps: dict[str, str] = {}
    last_time = first["buffer_start_ns"]
    offset = 0
    for segment in (first, second):
        if stack != segment["start_stack"]:
            raise ValueError("declared cut stack differs from actual trace stack")
        for row in segment["records"]:
            if row["sequence"] != offset or row["time_ns"] < last_time:
                raise ValueError("nonconsecutive sequence or regressing same-domain clock")
            offset += 1
            last_time = row["time_ns"]
            identifier = row["span_id"]
            event = row["event"]
            if event == "coverage":
                if identifier in spans or identifier in coverage_ids:
                    raise ValueError("duplicate record identity refused")
                coverage_ids.add(identifier)
                gaps[row["phase"]] = row["outcome"]
                continue
            if event == "begin":
                if identifier in spans or identifier in coverage_ids or len(spans) >= MAX_SPANS:
                    raise ValueError("duplicate span identity or whole-trace span limit exceeded")
                expected_parent = stack[-1] if stack else None
                expected_occurrence = occurrence_counts.get(row["phase"], 0) + 1
                if row["parent_id"] != expected_parent or row["occurrence"] != expected_occurrence or len(stack) >= MAX_DEPTH:
                    raise ValueError("span parent/occurrence/depth violates genuine nested order")
                occurrence_counts[row["phase"]] = expected_occurrence
                spans[identifier] = {"span_id": identifier, "parent_id": row["parent_id"], "phase": row["phase"],
                                     "occurrence": row["occurrence"], "start_ns": row["time_ns"], "end_ns": None,
                                     "outcome": "incomplete", "inclusive_wall_ns": None, "unattributed_wall_residual_ns": None}
                stack.append(identifier)
            else:
                if not stack or stack[-1] != identifier:
                    raise ValueError("unbalanced, overlapping or unknown span closure")
                span = spans[identifier]
                if any(row[name] != span[name] for name in ("parent_id", "phase", "occurrence")):
                    raise ValueError("span closure metadata differs from its begin")
                stack.pop()
                span["end_ns"] = row["time_ns"]
                span["outcome"] = row["outcome"]
                if event == "end":
                    span["inclusive_wall_ns"] = row["time_ns"] - span["start_ns"]
        if stack != segment["end_stack"]:
            raise ValueError("declared frozen open stack differs from actual span stack")
        derived = {}
        for phase in PHASES:
            phase_spans = [span for span in spans.values() if span["phase"] == phase]
            if phase in gaps:
                derived[phase] = gaps[phase]
            elif not phase_spans:
                derived[phase] = "not_observed"
            elif any(span["outcome"] == "aborted" for span in phase_spans):
                derived[phase] = "aborted"
            elif any(span["outcome"] != "completed" for span in phase_spans):
                derived[phase] = "incomplete"
            else:
                derived[phase] = "completed"
        if any(row["outcome"] != derived[row["phase"]] for row in segment["coverage"]):
            raise ValueError("coverage inventory contradicts actual observed/aborted/incomplete spans")
    for span in spans.values():
        children = [child for child in spans.values() if child["parent_id"] == span["span_id"]]
        if span["outcome"] == "completed" and all(child["outcome"] == "completed" for child in children):
            span["unattributed_wall_residual_ns"] = span["inclusive_wall_ns"] - _union([
                (child["start_ns"], child["end_ns"]) for child in children
            ])
    requested_complete = all(derived[phase] == "completed" for phase in second["required_phases"])
    aborted = any(span["outcome"] == "aborted" for span in spans.values())
    truncated = first["truncated"] or second["truncated"]
    complete = requested_complete and not stack and not aborted and not truncated and not gaps
    if second["status"] == "completed" and not complete:
        raise ValueError("missing/aborted/truncated timing cannot be declared complete")
    if second["status"] == "aborted" and not aborted:
        raise ValueError("aborted trace status requires an actual abort record")
    result = {
        "schema": "cho51_p3_timing_assessment_v1", "profile": PROFILE,
        "prefix_sha256": expected_prefix_sha256, "tail_sha256": expected_tail_sha256,
        "external_result_sha256": external_result_sha256,
        "metadata_contract_valid": True, "requested_coverage_complete": complete and second["status"] == "completed",
        "status": second["status"], "truncated": truncated,
        "process": first["process"], "clock": first["clock"], "pins": first["pins"],
        "normal_records": normal, "reserved_records": reserved, "encoded_segment_bytes": total_bytes,
        "spans": list(spans.values()), "coverage": second["coverage"],
        "unobserved_finalization": ["tail_file_persistence", "final_process_exit"],
        "whole_process_lifetime_covered": False, "residual_interpretation": "unattributed_wall_time_not_cpu_self_time",
        "execution_admitted": False, "scientific_admission": False, "physical_trace_files_verified": False,
    }
    assessment = object.__new__(TimingAssessment)
    object.__setattr__(assessment, "canonical_json", canonical_json(result, maximum=MAX_TRACE_BYTES))
    return assessment
