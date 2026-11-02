"""Closed auxiliary provenance joins and retained local-byte composition.

Joins establish record consistency against separately supplied pinned references.
They do not authenticate a person's identity, attest execution, or qualify a boot.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


core = _load("_custody_frozen_byte_core", HERE.parent / "v1/verifier.py")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")
ACTOR = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
FIELDS = {
    "source_review": {"schema", "reviewer", "authors", "reviewed_utc", "sources", "runtime_pins", "accepted"},
    "runtime": {"schema", "observed_utc", "runtime_root_id", "files"},
    "admission": {"schema", "capture_id", "author", "issued_utc", "window_start_utc", "window_end_utc",
                  "source_review", "sources", "runtime_pins", "policy_sha256", "scope", "accepted"},
    "return": {"schema", "capture_id", "executor", "source_review", "admission", "sources", "runtime_pins",
               "policy_sha256", "observed_start_utc", "observed_end_utc", "actual_return_utc", "tool_call_id", "exit_code"},
    "actual_review": {"schema", "capture_id", "reviewer", "reviewed_utc", "packet", "actual_return", "source_review",
                      "runtime_pins", "raw_observations", "event_to_host_binding", "scope", "accepted"},
}
SCHEMAS = {kind: "cho51_p3_aux_" + kind + "_v2" for kind in FIELDS}


def fail(message):
    raise core.VerificationError(message)


def closed(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        fail("auxiliary record fields are not closed")


def ref(value):
    closed(value, ("path", "bytes", "sha256"))
    core.normalized_path(value["path"])
    if type(value["bytes"]) is not int or not 0 <= value["bytes"] <= core.MAX_ARTIFACT_BYTES:
        fail("artifact byte bound/type")
    if type(value["sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is None:
        fail("artifact digest syntax")
    return value


def refs(values, maximum=16):
    if type(values) is not list or not 1 <= len(values) <= maximum:
        fail("reference inventory size/type")
    result = {}
    for value in values:
        ref(value)
        folded = value["path"].casefold()
        if folded in result:
            fail("reference inventory alias/duplicate")
        result[folded] = value
    return result


def same(a, b, label):
    if not core._equal(a, b):
        fail(label + " join differs")


def actor(value):
    if type(value) is not str or ACTOR.fullmatch(value) is None:
        fail("actor identifier syntax")
    return value


def record(kind, reference, artifacts):
    value = core.strict_json(core.validate_artifact(ref(reference), artifacts))
    closed(value, FIELDS[kind])
    if value["schema"] != SCHEMAS[kind]:
        fail("auxiliary record version")
    return value


def outcome(status, joined=False, message=None):
    return {"schema": "cho51_p3_auxiliary_assessment_v2", "status": status,
            "auxiliary_joins_verified": joined, "retained_reads_verified": False,
            "review_identity_authenticated": False, "loaded_runtime_attested": False,
            "boundary_qualified": False, "launch_authorized": False, "scientific_admission": False,
            "historical_custody_closed": False, "historical_operation_released": False,
            "historical_retry_allowed": False, "details": [] if message is None else [message[:512]],
            "remaining": ["old_event_host_association", "qualified_restart_provider", "cross_boot_clock_order",
                          "persisted_domain_exclusion", "actual_execution_and_review_authority"]}


def assess_joins(packet_ref, source_review_ref, actual_review_ref, policy_ref, artifacts, contracts):
    """Pure byte-map checks; independently supplied reference pins are inputs.

    A coherent fixture can pass joins but still cannot produce eligibility.
    Runtime inventory entries are joined metadata, not newly observed DLL loads.
    """
    try:
        core._artifact_map(artifacts)
        packet_bytes = core.validate_artifact(ref(packet_ref), artifacts)
        policy = core.validate_artifact(ref(policy_ref), artifacts)
        packet = core.validate_record("boundary-evidence", packet_bytes, contracts)
        base = core.assess_boundary(packet_bytes, artifacts, contracts, policy_bytes=policy)
        if base["status"] == "REFUSED":
            fail("boundary base: " + "; ".join(base["details"]))
        # Unlike the partial byte inspector, this entry requires the entire
        # declared artifact set before it can report coherent auxiliary joins.
        for reference in core._references(packet):
            core.validate_artifact(reference, artifacts)
        same(packet["collector_source_review"], ref(source_review_ref), "pinned source review")
        same(packet["policy_sha256"], policy_ref["sha256"], "policy")
        source = record("source_review", source_review_ref, artifacts)
        runtime = record("runtime", packet["runtime_pins"], artifacts)
        admission = record("admission", packet["observation_admission"], artifacts)
        returned = record("return", packet["actual_tool_return"], artifacts)
        review = record("actual_review", actual_review_ref, artifacts)
        source_reviewer = actor(source["reviewer"])
        if type(source["authors"]) is not list or not 1 <= len(source["authors"]) <= 8:
            fail("source author inventory")
        authors = [actor(item) for item in source["authors"]]
        if len(set(authors)) != len(authors) or source_reviewer in authors:
            fail("source self-review/duplicate authors")
        executor = actor(returned["executor"])
        admitter = actor(admission["author"])
        actual_reviewer = actor(review["reviewer"])
        if actual_reviewer in set(authors + [executor, admitter]):
            fail("actual self-review")
        for value in (source, admission, review):
            if value["accepted"] is not True:
                fail("source/admission/actual review rejected or mistyped")
        if admission["author"] != "project_root" or admission["scope"] != "boundary_observation":
            fail("observation admission authority/scope")
        if review["scope"] != "auxiliary_provenance_only":
            fail("actual review scope cannot claim provider qualification")
        expected_sources = refs(source["sources"])
        for reference in expected_sources.values():
            core.validate_artifact(reference, artifacts)
        for field in ("collector_source", "collector_protocol"):
            reference = packet[field]
            same(expected_sources.get(reference["path"].casefold()), reference, field)
        for value in (source, admission, returned, review):
            same(value["runtime_pins"], packet["runtime_pins"], "runtime inventory")
        for value in (admission, returned):
            same(refs(value["sources"]), expected_sources, "source inventory")
            same(value["source_review"], source_review_ref, "source review")
            same(value["policy_sha256"], policy_ref["sha256"], "policy")
        runtime_files = refs(runtime["files"], maximum=1024)
        if type(runtime["runtime_root_id"]) is not str or re.fullmatch(r"[0-9a-f]{64}", runtime["runtime_root_id"]) is None:
            fail("runtime root identifier")
        for value in (admission, returned, review):
            if type(value["capture_id"]) is not str or UUID.fullmatch(value["capture_id"]) is None:
                fail("capture identity syntax")
            same(value["capture_id"], packet["capture_id"], "capture identity")
        same(returned["admission"], packet["observation_admission"], "returned admission")
        same(review["packet"], packet_ref, "actual review packet")
        same(review["source_review"], source_review_ref, "actual/source review")
        same(review["actual_return"], packet["actual_tool_return"], "actual caller return")
        same(refs(review["raw_observations"]), refs(packet["raw_observations"]), "raw observation set")
        same(review["event_to_host_binding"], packet["event_to_host_binding"], "host-binding bytes")
        if type(returned["exit_code"]) is not int or returned["exit_code"] != 0:
            fail("actual caller exit is not zero integer")
        if type(returned["tool_call_id"]) is not str or re.fullmatch(r"[A-Za-z0-9_.:/-]{1,160}", returned["tool_call_id"]) is None:
            fail("actual tool-call identifier")
        for field in ("observed_start_utc", "observed_end_utc"):
            same(returned[field], packet[field], "actual capture time")
        t = core.utc_ticks
        runtime_time = t(runtime["observed_utc"])
        source_time = t(source["reviewed_utc"])
        admission_time = t(admission["issued_utc"])
        capture_start, capture_end = (t(packet[k]) for k in ("observed_start_utc", "observed_end_utc"))
        return_time, packet_time, review_time = t(returned["actual_return_utc"]), t(packet["created_utc"]), t(review["reviewed_utc"])
        if not runtime_time <= source_time < admission_time <= capture_start <= capture_end <= return_time <= packet_time < review_time:
            fail("runtime/review/admission/capture/return/packet chronology")
        core.validate_window(admission["window_start_utc"], admission["window_end_utc"],
                             admission["issued_utc"], returned["actual_return_utc"])
        if t(admission["window_end_utc"]) - t(admission["window_start_utc"]) > 900 * core.TICKS_PER_SECOND:
            fail("observation window exceeds15minutes")
        result = outcome("UNRESOLVED", joined=True)
        result.update(source_entries=len(expected_sources), runtime_inventory_entries=len(runtime_files),
                      raw_observation_entries=len(packet["raw_observations"]))
        return result
    except core.VerificationError as exc:
        return outcome("REFUSED", message=str(exc))


def assess_retained(approved_root, packet_ref, source_review_ref, actual_review_ref, policy_ref, contract_refs):
    """Read the finite graph under retained local handles, then run joins.

    No runtime-inventory dependency is executed or mistaken for a loaded module.
    The runtime inventory itself and all packet/source-review artifacts are read.
    A caller must separately admit this operation; this API never launches work.
    """
    reader_module = _load("_custody_retained_reader_v2", HERE / "retained_reader.py")
    try:
        if type(contract_refs) is not dict or set(contract_refs) != set(core.CONTRACT_HASHES):
            fail("complete immutable contract references required")
        artifacts = {}
        with reader_module.RetainedArtifactSet(approved_root) as reader:
            def get(reference):
                ref(reference)
                data = reader.read(reference)
                artifacts[reference["path"]] = data
                return data
            packet_bytes = get(packet_ref)
            get(policy_ref)
            get(source_review_ref)
            get(actual_review_ref)
            contracts = {}
            for kind, reference in contract_refs.items():
                same(ref(reference)["sha256"], core.CONTRACT_HASHES[kind], "contract source pin")
                contracts[kind] = get(reference)
            packet = core.validate_record("boundary-evidence", packet_bytes, contracts)
            for reference in core._references(packet):
                get(reference)
            source = record("source_review", source_review_ref, artifacts)
            for reference in refs(source["sources"]).values():
                get(reference)
            result = assess_joins(packet_ref, source_review_ref, actual_review_ref, policy_ref, artifacts, contracts)
            reader.verify()
            witnesses = reader.witnesses
        result["retained_reads_verified"] = True
        result["retained_artifacts"] = list(witnesses)
        return result
    except (core.VerificationError, reader_module.RetainedArtifactError) as exc:
        return outcome("REFUSED", message=str(exc))
