"""Bounded offline intake of retained byte maps; no positive authority path.

The caller owns retained reads and pins this module and the frozen v1 verifier.
Actor names, labels, PID observations and boot rows are never authentication.
Only module loading reads source files; assessment and candidate building are pure.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re


_spec = importlib.util.spec_from_file_location(
    "_custody_intake_frozen_v1", Path(__file__).parents[1] / "v1" / "verifier.py")
v1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v1)
Error = v1.VerificationError
ROLES = (
    "historical_disposition", "historical_audit", "historical_review",
    "provider_capture", "decoded_capture", "provider_actual_review",
    "provider_root_qualification", "policy", "disposition_schema",
)
HISTORY = dict(zip(ROLES[:3], (
    "1faf198894e0f210e5bb8692a8c0c4b35f10963a1e2c8c928d545eb808c335ec",
    "365153e07d2f925d36168f0218404ae37c18962d0bbabb0598a284ff6740b75d",
    "df900ab63aaf0f4ef0febbe11c3db7fa23ff9a178f5d8f65f6233ff35948e098",
)))
FALSE_FIELDS = frozenset((
    "historical_custody_closed", "historical_operation_released",
    "historical_retry_allowed", "host_association_authenticated",
    "restart_qualified", "clock_order_qualified", "persisted_domain_excluded",
    "boundary_qualified", "launch_authorized", "scientific_admission",
    "custody_closed", "operation_released", "retry_allowed",
    "same_attempt_retry_or_rearm_allowed", "new_operation_authorized",
    "automatic_retry_permitted", "bootstrap_passed", "freeze_signed",
))
TOP_FALSE = tuple(sorted(FALSE_FIELDS & {
    "historical_custody_closed", "historical_operation_released",
    "historical_retry_allowed", "host_association_authenticated",
    "restart_qualified", "clock_order_qualified", "persisted_domain_excluded",
    "boundary_qualified", "launch_authorized", "scientific_admission",
}))
GAPS = (
    "HOST_ASSOCIATION_UNESTABLISHED", "PROVIDER_COVERAGE_UNQUALIFIED",
    "RESTART_KIND_UNESTABLISHED", "CLOCK_ORDER_UNESTABLISHED",
    "PERSISTED_DOMAIN_UNRESOLVED", "RAW_OBSERVATION_INCOMPLETE",
)
CODES = frozenset(GAPS + (
    "HISTORICAL_INPUT_MISSING", "HISTORICAL_HASH_MISMATCH",
    "HISTORICAL_STATE_UPGRADE", "EVIDENCE_CONTRADICTED",
))
LIMITATIONS = (
    "Offline byte joins do not authenticate retained file identity, actors, or the historical host.",
    "The historical refused process row and original cleanup remain unknown; bootstrap004 stays consumed and unreleased.",
    "Four native fragment matches from six rows do not qualify provider coverage or a complete restart.",
    "Security EvtQuery error 5 and classic EventLog metadata error 2 remain explicit gaps.",
    "Restart kind, clock ordering and persisted-domain exclusion remain unestablished.",
    "Root must separately review this candidate; it grants no boundary, launch or scientific authority.",
)
QUERY_KEYS = ("boot", "clock_lifecycle", "power", "resume", "eventlog_service",
              "log_clear", "historical_creation")
QUERY_FAMILIES = (
    ("Microsoft-Windows-Kernel-Boot", "System", [27]),
    ("Microsoft-Windows-Kernel-General", "System", [1, 12, 13]),
    ("Microsoft-Windows-Kernel-Power", "System", [41, 42, 107]),
    ("Microsoft-Windows-Power-Troubleshooter", "System", [1]),
    ("EventLog", "System", [6005, 6006, 6008]),
    ("Microsoft-Windows-Eventlog", "System", [104]),
    ("Microsoft-Windows-Security-Auditing", "Security", [4688]),
)
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


def _require(predicate, message):
    if not predicate:
        raise Error(message)


def _same(left, right, message):
    _require(v1._equal(left, right), message)


def _closed(value, keys, label):
    _require(type(value) is dict and set(value) == set(keys), label + " fields must be exact")


def _reference(ref):
    _closed(ref, ("path", "bytes", "sha256"), "artifact reference")
    v1.normalized_path(ref["path"])
    _require(type(ref["bytes"]) is int and 0 <= ref["bytes"] <= v1.MAX_RECORD_BYTES,
             "artifact size must be an exact integer within 1 MiB")
    _require(type(ref["sha256"]) is str and v1._HASH.fullmatch(ref["sha256"]),
             "artifact digest must be canonical SHA256")


def _plan(plan):
    if type(plan) is bytes:
        plan = v1.strict_json(plan)
    v1._bounded_tree(plan)
    _closed(plan, ("schema", "artifacts", "launch_authorized", "scientific_admission"), "plan")
    _same(plan["schema"], "cho51_p3_custody_intake_plan_v6", "wrong intake plan schema")
    _require(plan["launch_authorized"] is False and plan["scientific_admission"] is False,
             "plan authority must remain false")
    _closed(plan["artifacts"], ROLES, "plan roles")
    seen = set()
    for role in ROLES:
        ref = plan["artifacts"][role]
        _reference(ref)
        folded = ref["path"].casefold()
        _require(folded not in seen, "duplicate or aliased role path: " + role)
        seen.add(folded)
        if role in HISTORY:
            _same(ref["sha256"], HISTORY[role], "historical fixed hash changed: " + role)
    _same(plan["artifacts"]["disposition_schema"]["sha256"],
          v1.CONTRACT_HASHES["disposition"], "frozen disposition schema pin changed")
    return copy.deepcopy(plan)


def _false_flags(value, label):
    """Check known authority fields wherever present; invent no unknown flags."""
    if type(value) is dict:
        for key, child in value.items():
            if key in FALSE_FIELDS:
                _require(child is False, label + "/" + key + " attempted authority upgrade")
            _false_flags(child, label + "/" + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            _false_flags(child, label + "/" + str(index))


def _top_false(value, fields, label):
    for field in fields:
        _require(value.get(field) is False, label + "/" + field + " must remain false")


def _blob(blob, label):
    _closed(blob, ("xml", "bytes", "sha256"), label)
    _require(type(blob["xml"]) is str, label + " XML must be text")
    raw = blob["xml"].encode("utf-8")
    _require(type(blob["bytes"]) is int and len(raw) == blob["bytes"], label + " raw length mismatch")
    _same(hashlib.sha256(raw).hexdigest(), blob["sha256"], label + " raw hash mismatch")


def _provider_joins(docs, refs):
    capture, decoded, review, root = (docs[role] for role in ROLES[3:7])
    _same(capture.get("schema"), "cho51_p3_provider_capture_v4", "provider_capture schema")
    _same(decoded.get("schema"), "cho51_p3_provider_redecode_v5", "decoded_capture schema")
    _same(review.get("schema"), "cho51_p3_provider_actual_review_v5", "provider_actual_review schema")
    _same(root.get("schema"), "cho51_p3_provider_root_qualification_v5", "provider_root_qualification schema")
    for role, value in (("provider_capture", capture), ("decoded_capture", decoded)):
        _same(value.get("status"), "UNRESOLVED", role + " status must remain unresolved")
        _top_false(value, TOP_FALSE, role)
    _top_false(root, ("historical_custody_closed", "boundary_qualified", "persisted_domain_excluded",
                      "restart_qualified", "clock_order_qualified", "launch_authorized",
                      "host_association_authenticated", "scientific_admission"), "provider_root_qualification")
    _same(decoded.get("input"), refs["provider_capture"], "decoded_capture/input does not join provider_capture")
    _require(decoded.get("fresh_provider_observation") is False, "offline decode claims fresh observation")
    accepted = "ACCEPTED_ENGINEERING_OBSERVATION_WITH_GAPS"
    _same(review.get("status"), accepted, "provider_actual_review status")
    _same(root.get("status"), accepted, "provider_root_qualification status")
    _same(root.get("actual_review"), refs["provider_actual_review"], "Root actual-review ref mismatch")
    _same(root.get("author"), "project_root", "Root qualification author label mismatch")
    _require(root.get("v4_namespace_defect_preserved") is True, "v4 defect preservation missing")
    reviewer, authors, source_reviewer = (review.get(k) for k in ("reviewer", "source_authors", "source_reviewer"))
    _require(type(reviewer) is str and bool(reviewer) and type(source_reviewer) is str and bool(source_reviewer)
             and type(authors) is list and bool(authors) and all(type(a) is str and a for a in authors)
             and reviewer not in authors and reviewer != source_reviewer,
             "actual review role labels do not show a distinct reviewer")
    pins = review.get("artifact_pins")
    _require(type(pins) is dict, "actual review artifact_pins missing")
    for role in ("provider_capture", "decoded_capture"):
        ref = refs[role]
        _same(pins.get(ref["path"]), {"bytes": ref["bytes"], "sha256": ref["sha256"]},
              "actual review artifact pin does not join " + role)
    checks = review.get("checks")
    _require(type(checks) is dict, "actual review checks missing")
    _same(root.get("source_review_sha256"), checks.get("source_review_sha256"), "source review digest join mismatch")
    _require(type(root.get("source_review_sha256")) is str and v1._HASH.fullmatch(root["source_review_sha256"]),
             "source review digest malformed")
    for role_count, review_count in (("sources", "source_files_checked"), ("runtime", "runtime_files_checked"),
                                      ("preserved", "preserved_files_checked")):
        _same(root.get("rechecked", {}).get(role_count), checks.get(review_count), "Root/review count join mismatch: " + role_count)
    _same(checks.get("pin_mismatches"), 0, "actual review reports pin mismatches")
    cq, dq = capture.get("queries"), decoded.get("queries")
    _require(type(cq) is list and len(cq) == 7 and type(dq) is list and len(dq) == 7,
             "provider_capture and decoded_capture require seven queries")
    originals, v4_refused, template_bytes = [], 0, 0
    for key, family, original, projection in zip(QUERY_KEYS, QUERY_FAMILIES, cq, dq):
        label = "provider_capture/queries/" + key
        _require(type(original) is dict and type(original.get("spec")) is dict, label + " spec missing")
        _same(original["spec"].get("key"), key, label + " order/key mismatch")
        provider, channel, event_ids = family
        expected_spec = {"key": key, "provider": provider, "channel": channel, "event_ids": event_ids,
                         "from_utc": v1.OLD_RETURN_UTC, "to_utc": capture.get("observed_start_utc")}
        if key == "historical_creation":
            expected_spec.update(from_utc="2026-10-27T17:04:57.1375077Z", to_utc=v1.OLD_RETURN_UTC,
                                 pid_hex_values=["0x49c2c", "0x49C2C", "0X49C2C"])
        _same(original["spec"], expected_spec, label + " saved query spec changed")
        metadata = original.get("metadata")
        _require(type(metadata) is dict, label + " metadata missing")
        expected = {"key": key, "spec": original["spec"]}
        for field in ("selected_query_exhausted", "truncated", "errors"):
            expected[field] = original.get(field)
        for field in ("exhausted", "truncated", "errors"):
            expected["metadata_" + field] = metadata.get(field)
        _same(projection, expected, "decoded_capture query status/spec projection mismatch: " + key)
        _require(type(expected["selected_query_exhausted"]) is bool and type(expected["truncated"]) is bool
                 and type(metadata.get("exhausted")) is bool and type(metadata.get("truncated")) is bool,
                 label + " projection flags must be booleans")
        _same(expected["truncated"], False, label + " saved truncation changed")
        _same(metadata["truncated"], False, label + " saved metadata truncation changed")
        _same(expected["selected_query_exhausted"], key != "historical_creation", label + " exhaustion changed")
        _same(metadata["exhausted"], key != "eventlog_service", label + " metadata exhaustion changed")
        _same(expected["errors"], ["OSError:[Errno 5] EvtQuery"] if key == "historical_creation" else [],
              label + " Security/error gap changed")
        _same(metadata["errors"], ["FileNotFoundError:[Errno 2] EvtOpenEventMetadataEnum"]
              if key == "eventlog_service" else [], label + " classic metadata/error gap changed")
        events, oldrows = original.get("events"), original.get("decoded")
        _require(type(events) is list and type(oldrows) is list and len(events) == len(oldrows), label + " v4 row count mismatch")
        for event, oldrow in zip(events, oldrows):
            _blob(event, label + "/events")
            _same(oldrow.get("raw_sha256"), event["sha256"], label + " v4 raw join mismatch")
            _same(oldrow.get("status"), "REFUSED_DECODING", label + " v4 namespace refusal changed")
            _same(oldrow.get("reason"), "DecodeError:wrong event root/namespace", label + " v4 namespace defect changed")
            originals.append((key, event, metadata))
            v4_refused += 1
        for definition in metadata.get("definitions", []):
            _blob(definition["template"], label + "/metadata/template")
            template_bytes += definition["template"]["bytes"]
    _require(len(originals) == 6 and len({e[1]["sha256"] for e in originals}) == 6,
             "provider_capture requires six unique original events")
    rows = decoded.get("rows")
    _require(type(rows) is list and len(rows) == 6, "decoded_capture requires six rows")
    decoded_count = matched = refused = 0
    for row, (key, raw, metadata) in zip(rows, originals):
        _require(type(row) is dict, "decoded_capture row is not an object")
        _same(row.get("query_key"), key, "decoded_capture row query join mismatch")
        _same(row.get("raw_sha256"), raw["sha256"], "decoded_capture row raw hash join mismatch")
        if key == "eventlog_service":
            _closed(row, ("query_key", "raw_sha256", "status", "reason"), "classic refused row")
            _same(row["status"], "REFUSED_DECODING", "classic unsupported payload was upgraded")
            _same(row["reason"], "unsupported/unnamed event payload field", "classic refusal reason changed")
            refused += 1
            continue
        _same(row.get("status"), "DECODED", "supported row status mismatch")
        event, generic, native = (row.get(k) for k in ("event", "generic_qualification", "native_qualification"))
        _require(all(type(item) is dict for item in (event, generic, native)), "supported qualification object missing")
        _same(event.get("raw"), {"bytes": raw["bytes"], "sha256": raw["sha256"]}, "decoded event raw bytes/hash mismatch")
        _same(event.get("provider_name"), metadata.get("provider"), "event/provider metadata join mismatch")
        _same(event.get("provider_guid"), metadata.get("guid"), "event/provider GUID join mismatch")
        _same(generic.get("status"), "UNSUPPORTED", "generic provider coverage was upgraded")
        _same(native.get("status"), "MATCHED_NATIVE_TEMPLATE_FRAGMENT", "native match status mismatch")
        _same(native.get("source_format"), "EvtGetEventMetadataProperty/EventMetadataEventTemplate", "native source format changed")
        for field in ("event_id", "version"):
            _require(type(event.get(field)) is int, "event identity must use exact integers")
            _same(native.get(field), event[field], "native/event identity mismatch")
        definitions = [d for d in metadata["definitions"]
                       if v1._equal(d.get("event_id"), event["event_id"]) and v1._equal(d.get("version"), event["version"])]
        _require(len(definitions) == 1, "native metadata definition identity ambiguous/missing")
        template = definitions[0]["template"]
        _same(native.get("template"), {"bytes": template["bytes"], "sha256": template["sha256"]}, "native template pin mismatch")
        for item in (event, generic, native):
            _top_false(item, ("boundary_qualified", "host_association_authenticated", "launch_authorized", "scientific_admission"), "decoded_capture/row")
        decoded_count += 1
        matched += 1
    _same((decoded_count, matched, refused), (4, 4, 2), "saved decode counts changed")
    for name, count in (("decoded_count", decoded_count), ("matched_native_count", matched)):
        _same(decoded.get(name), count, "decoded_capture/" + name + " count mismatch")
    for name in ("native_handles_opened", "native_handles_closed"):
        _same(capture.get(name), 1315, "provider_capture/" + name + " mismatch")
    _same(capture.get("native_close_errors"), [], "native close errors present")
    _require(capture.get("native_handles_closed_cleanly") is True, "native closure report not clean")
    _same(capture.get("event_xml_bytes"), sum(item[1]["bytes"] for item in originals), "captured event byte total mismatch")
    _same(capture.get("template_xml_bytes"), template_bytes, "captured template byte total mismatch")
    start, end = (v1.utc_ticks(capture.get(k)) for k in ("observed_start_utc", "observed_end_utc"))
    _require(end >= start > v1.utc_ticks(v1.OLD_RETURN_UTC), "capture report UTC ordering contradicted")
    for name in ("qpc_start", "qpc_end", "qpc_frequency"):
        _require(type(capture.get(name)) is int and 0 < capture[name] <= v1.MAX_QPC, "capture report QPC value malformed")
    _require(capture["qpc_end"] >= capture["qpc_start"], "capture report QPC ordering contradicted")
    obs = review.get("observations")
    _require(type(obs) is dict, "actual review observations missing")
    expectations = {"v4_handles_opened": 1315, "v4_handles_closed": 1315, "v4_rows": 6,
                    "v4_namespace_refusals": v4_refused, "offline_input_bytes": refs["provider_capture"]["bytes"],
                    "offline_input_sha256": refs["provider_capture"]["sha256"], "fresh_provider_observation": False,
                    "rows": 6, "decoded": decoded_count, "native_fragment_matches": matched,
                    "classic_binary_refused": refused, "generic_qualification": "UNSUPPORTED",
                    "queries": 7, "capture_status": "UNRESOLVED", "v5_tests": 73,
                    "failures": 0, "errors": 0, "skipped": 0}
    for name, expected in expectations.items():
        _same(obs.get(name), expected, "provider_actual_review/observations/" + name + " mismatch")
    return {"queries": 7, "raw_rows": 6, "decoded_rows": 4, "native_fragment_matches": 4,
            "unsupported_classic_rows": 2, "native_handles_closed": 1315,
            "security_query_error": 5, "classic_metadata_error": 2}


def _assessment(status, codes, details, evidence=None, facts=None):
    result = {"schema": "cho51_p3_custody_intake_assessment_v6", "status": status,
              "reason_codes": list(codes), "details": list(details),
              "evidence": copy.deepcopy(evidence or {}), "facts": dict(facts or {}),
              "historical_status": "FAILED_UNRELEASED_CONSUMED"}
    result.update({field: False for field in TOP_FALSE})
    return result


def assess(plan, artifacts):
    """Return REFUSED or UNRESOLVED; supplied byte provenance is never asserted."""
    evidence, docs, missing = {}, {}, []
    try:
        plan = _plan(plan)
        refs = plan["artifacts"]
        _require(type(artifacts) is dict and len(artifacts) <= 9, "byte map requires at most nine planned artifacts")
        v1._artifact_map(artifacts)
        _require(set(artifacts) <= {ref["path"] for ref in refs.values()}, "byte map contains unplanned paths")
        for role in ROLES:
            ref = refs[role]
            if ref["path"] not in artifacts:
                missing.append(role)
                continue
            try:
                data = v1.validate_artifact(ref, artifacts)
            except Error as exc:
                return _assessment("REFUSED", ["HISTORICAL_HASH_MISMATCH" if role in HISTORY else "EVIDENCE_CONTRADICTED"],
                                   [role + " [" + ref["path"] + "]: " + str(exc)], evidence)
            evidence[role] = ref
            if role != "policy":
                docs[role] = v1.strict_json(data)
                _require(type(docs[role]) is dict, role + " must contain a JSON object")
                if role != "disposition_schema":
                    _false_flags(docs[role], role + " [" + ref["path"] + "]")
            else:
                data.decode("utf-8", errors="strict")
        historical_missing = [role for role in missing if role in HISTORY]
        if historical_missing:
            return _assessment("REFUSED", ["HISTORICAL_INPUT_MISSING"],
                               [role + " [" + refs[role]["path"] + "]: missing required historical bytes" for role in historical_missing], evidence)
        if missing:
            return _assessment("UNRESOLVED", GAPS,
                               [role + " [" + refs[role]["path"] + "]: bytes missing; joins not completed" for role in missing], evidence)
        _same(docs["historical_disposition"].get("disposition"), "FAILED_UNRELEASED_CONSUMED", "historical disposition changed")
        facts = _provider_joins(docs, refs)
        return _assessment("UNRESOLVED", GAPS, LIMITATIONS, evidence, facts)
    except (Error, UnicodeError, KeyError, TypeError, AttributeError) as exc:
        return _assessment("REFUSED", ["EVIDENCE_CONTRADICTED"], [str(exc)[:512] or "Malformed evidence refused"], evidence)


def build_disposition(assessment, plan, disposition_id, created_utc, schema_bytes):
    """Build a negative candidate for separate Root adoption, never admission.

    Closed output validation prevents caller-added positive flags, statuses,
    boundary evidence or reason-code removal from becoming a candidate.
    """
    plan = _plan(plan)
    v1._bounded_tree(assessment)
    _closed(assessment, set(_assessment("REFUSED", [], [])), "assessment")
    _same(assessment["schema"], "cho51_p3_custody_intake_assessment_v6", "assessment schema")
    _same(assessment["historical_status"], "FAILED_UNRELEASED_CONSUMED", "assessment historical status")
    _top_false(assessment, TOP_FALSE, "assessment")
    _require(assessment["status"] in ("REFUSED", "UNRESOLVED"), "positive disposition is unavailable")
    codes, details = assessment["reason_codes"], assessment["details"]
    _require(type(codes) is list and 1 <= len(codes) <= 16 and all(type(c) is str and c in CODES for c in codes)
             and len(set(codes)) == len(codes), "assessment reason codes malformed")
    if assessment["status"] == "UNRESOLVED":
        _same(codes, list(GAPS), "unresolved assessment must preserve all six gaps")
    else:
        _require(len(codes) == 1 and codes[0] in CODES - set(GAPS), "refusal reason inconsistent")
    _require(type(details) is list and 1 <= len(details) <= 9
             and all(type(d) is str and 1 <= len(d) <= 512 for d in details), "assessment details malformed")
    _require(type(assessment["evidence"]) is dict and set(assessment["evidence"]) <= set(ROLES), "assessment evidence roles malformed")
    for role, ref in assessment["evidence"].items():
        _same(ref, plan["artifacts"][role], "assessment evidence pin mismatch: " + role)
    _require(type(assessment["facts"]) is dict, "assessment facts malformed")
    allowed_facts = {"queries": 7, "raw_rows": 6, "decoded_rows": 4, "native_fragment_matches": 4,
                     "unsupported_classic_rows": 2, "native_handles_closed": 1315,
                     "security_query_error": 5, "classic_metadata_error": 2}
    _require(not assessment["facts"] or v1._equal(assessment["facts"], allowed_facts), "assessment facts changed")
    if assessment["facts"]:
        _same(set(assessment["evidence"]), set(ROLES), "complete facts require all nine evidence pins")
    _require(type(disposition_id) is str and _UUID.fullmatch(disposition_id), "disposition id must be canonical UUID")
    v1.utc_ticks(created_utc)
    refs = plan["artifacts"]
    v1.validate_artifact(refs["disposition_schema"], {refs["disposition_schema"]["path"]: schema_bytes})
    historical = {"disposition": refs["historical_disposition"], "actual_audit": refs["historical_audit"],
                  "failed_review": refs["historical_review"], "status": "FAILED_UNRELEASED_CONSUMED",
                  "custody_closed": False, "operation_released": False, "retry_allowed": False}
    candidate = {"schema": "cho51_p3_local_custody_disposition_v1", "disposition_id": disposition_id,
            "created_utc": created_utc, "author": "project_root", "policy_sha256": refs["policy"]["sha256"],
            "historical": copy.deepcopy(historical), "status": assessment["status"], "current_boundary": None,
            "reason_codes": list(codes), "limitations": list(LIMITATIONS),
            "launch_authorized": False, "scientific_admission": False}
    v1.validate_record("disposition", json.dumps(candidate, ensure_ascii=True, allow_nan=False).encode("utf-8"),
                       {"disposition": schema_bytes})
    return candidate
