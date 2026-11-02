"""Bounded byte-only custody candidate inspection; never operational authority.

No filesystem reads, providers, child processes or network calls occur here.
Untrusted assertion fields cannot enable the deliberately absent positive path.
"""

import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re


MAX_RECORD_BYTES = 1048576
MAX_DEPTH = 16
MAX_NODES = 8192
MAX_STRING = 4096
MAX_ARTIFACT_BYTES = 16777216
MAX_ARTIFACTS = 64
MAX_TOTAL_ARTIFACT_BYTES = 67108864
MAX_QPC = 9007199254740991
TICKS_PER_SECOND = 10000000
OLD_RETURN_UTC = "2026-10-27T17:05:08.2987118Z"
HISTORICAL_HASHES = {
    "disposition": "1faf198894e0f210e5bb8692a8c0c4b35f10963a1e2c8c928d545eb808c335ec",
    "actual_audit": "365153e07d2f925d36168f0218404ae37c18962d0bbabb0598a284ff6740b75d",
    "failed_review": "df900ab63aaf0f4ef0febbe11c3db7fa23ff9a178f5d8f65f6233ff35948e098",
}
CONTRACT_HASHES = {
    "boundary-evidence": "01f58b20d05a19b8acf451ec8f591990c70be9491eb3ee7230923f7787a7ce2a",
    "disposition": "1078e7fc3ed1984b01a62f557a5b6691f2185b196dfcbfee0832949872f93e83",
    "local-admission": "21340d93976cff09b1eb43270d31ec7335d1ebe15cbb9c08b0733c93d77fbdb5",
}
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_UTC = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,7}))?Z\Z")
_PATH = re.compile(r"[A-Za-z0-9_./-]{1,384}\Z")
_RESERVED = {"CON", "PRN", "AUX", "NUL", "CLOCK$"}
_RESERVED.update("COM" + str(n) for n in range(1, 10))
_RESERVED.update("LPT" + str(n) for n in range(1, 10))
_KEYWORDS = frozenset((
    "$schema", "title", "$defs", "$ref", "type", "const", "enum",
    "properties", "required", "additionalProperties", "allOf", "anyOf",
    "if", "then", "else", "pattern", "format", "minLength", "maxLength",
    "minItems", "maxItems", "uniqueItems", "items", "minimum", "maximum",
))
_SCHEMA_PATTERNS = frozenset((
    r"^[0-9a-f]{64}$",
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,7})?Z$",
    r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9_./-]+$",
    r"^runs/coordination/cho51_p3_local_bootstrap_006/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
))


class VerificationError(ValueError):
    """A bounded, deterministic structural or semantic refusal."""


class OperationalReadUnavailable(VerificationError):
    """Retained Windows file identity is not implemented or qualified."""


class _WorkLimit(VerificationError):
    """A validation limit must not be mistaken for a failed schema branch."""


def _fail(message):
    raise VerificationError(message)


def _integer(token):
    if len(token) > 128:
        _fail("integer token exceeds bound")
    return int(token)


def _decimal(token):
    if len(token) > 128:
        _fail("number token exceeds bound")
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise VerificationError("invalid decimal") from exc
    if not value.is_finite() or abs(value.as_tuple().exponent) > 10000:
        _fail("decimal exponent or finiteness exceeds bound")
    return value


def _constant(token):
    _fail("nonfinite JSON constant")


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON property")
        result[key] = value
    return result


def _bounded_tree(value):
    pending = [(value, 0)]
    nodes = 0
    while pending:
        current, depth = pending.pop()
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            _fail("JSON node or depth bound exceeded")
        if isinstance(current, str):
            if len(current) > MAX_STRING or any(0xD800 <= ord(c) <= 0xDFFF for c in current):
                _fail("JSON string bound or Unicode scalar violation")
        elif type(current) is dict:
            for key, child in current.items():
                pending.append((key, depth + 1))
                pending.append((child, depth + 1))
        elif type(current) is list:
            pending.extend((child, depth + 1) for child in current)
        elif type(current) is int and current.bit_length() > 426:
            _fail("integer magnitude exceeds token bound")
        elif type(current) is Decimal:
            if not current.is_finite() or abs(current.as_tuple().exponent) > 10000 or len(current.as_tuple().digits) > 128:
                _fail("decimal value exceeds bound")
        elif current is not None and type(current) not in (bool, int, Decimal):
            _fail("unsupported JSON value")


def strict_json(data):
    """Decode UTF-8 JSON without BOM, duplicate keys, float loss or excess work."""
    if type(data) is not bytes or len(data) > MAX_RECORD_BYTES:
        _fail("record must be bytes within 1 MiB")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise VerificationError("record is not UTF-8") from exc
    # Scan nesting before json.loads, so malicious nesting cannot exhaust its stack.
    quoted = escaped = False
    depth = 0
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                _fail("JSON nesting exceeds bound")
        elif char in "]}":
            depth -= 1
    try:
        value = json.loads(text, object_pairs_hook=_object, parse_int=_integer,
                           parse_float=_decimal, parse_constant=_constant)
    except (ValueError, RecursionError) as exc:
        raise VerificationError("strict JSON parse refused") from exc
    _bounded_tree(value)
    return value


def utc_ticks(value):
    """Calendar-valid UTC expressed as exact 100 ns ticks, without float rounding."""
    if type(value) is not str:
        _fail("UTC timestamp must be a string")
    match = _UTC.fullmatch(value)
    if match is None:
        _fail("timestamp must use bounded UTC Z form")
    year, month, day, hour, minute, second = map(int, match.groups()[:6])
    try:
        date = datetime.datetime(year, month, day, hour, minute, second)
    except ValueError as exc:
        raise VerificationError("calendar-invalid UTC timestamp") from exc
    fraction = int((match.group(7) or "").ljust(7, "0"))
    return (((date.toordinal() * 24 + hour) * 60 + minute) * 60 + second) * TICKS_PER_SECOND + fraction


def normalized_path(value):
    """Only normalized portable project-relative names; no Windows aliases."""
    if type(value) is not str or _PATH.fullmatch(value) is None:
        _fail("artifact path syntax refused")
    for part in value.split("/"):
        if part in ("", ".", "..") or part.endswith("."):
            _fail("artifact path is not normalized")
        if part.split(".", 1)[0].upper() in _RESERVED:
            _fail("Windows device alias refused")
    return value


def read_operational_artifact(approved_root, reference):
    """Always fail closed: no stat/open/resolve pathname TOCTOU approximation.

    A future independently reviewed native collector must retain root/ancestor/
    file identities, reject reparse points, hard links and aliases, deny mutation
    during reads and prove containment. Supplying these arguments asserts none
    of those facts. The pure core accepts bytes for static inspection only.
    """
    raise OperationalReadUnavailable("retained Windows read identity is unimplemented and unqualified")


def _equal(left, right):
    # bool is an int subclass in Python; JSON booleans never equal JSON numbers.
    if type(left) is not type(right):
        if type(left) in (int, Decimal) and type(right) in (int, Decimal):
            return left == right
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_equal(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    return left == right


def _check_schema_source(schema):
    if type(schema) is not dict or set(schema) - _KEYWORDS:
        _fail("unsupported schema or keyword")
    if "$schema" in schema and schema["$schema"] != "https://json-schema.org/draft/2020-12/schema":
        _fail("unsupported schema dialect")
    if "$ref" in schema and (type(schema["$ref"]) is not str or re.fullmatch(r"#/\$defs/[A-Za-z0-9_-]+", schema["$ref"]) is None):
        _fail("nonlocal or unsupported schema reference")
    if "type" in schema and (type(schema["type"]) is not str or schema["type"] not in ("object", "array", "string", "integer", "boolean", "null")):
        _fail("unsupported schema type")
    if "pattern" in schema and (type(schema["pattern"]) is not str or schema["pattern"] not in _SCHEMA_PATTERNS):
        _fail("unsupported schema regular expression")
    for key in ("required", "enum"):
        if key in schema and (type(schema[key]) is not list or len(schema[key]) > 64):
            _fail("unsupported schema list")
    if "required" in schema and any(type(name) is not str for name in schema["required"]):
        _fail("required property names must be strings")
    for key in ("minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum"):
        if key in schema and type(schema[key]) is not int:
            _fail("unsupported schema numeric limit")
    if "uniqueItems" in schema and type(schema["uniqueItems"]) is not bool:
        _fail("unsupported uniqueness predicate")
    for key in ("properties", "$defs"):
        if key in schema:
            if type(schema[key]) is not dict:
                _fail("invalid schema property map")
            for child in schema[key].values():
                _check_schema_source(child)
    for key in ("allOf", "anyOf"):
        if key in schema:
            if type(schema[key]) is not list or not schema[key]:
                _fail("invalid schema alternatives")
            for child in schema[key]:
                _check_schema_source(child)
    for key in ("if", "then", "else", "items"):
        if key in schema:
            _check_schema_source(schema[key])
    if "additionalProperties" in schema and schema["additionalProperties"] is not False:
        _fail("unsupported open schema")
    if "format" in schema and schema["format"] != "date-time":
        _fail("unsupported schema format")


def _validate(value, schema, root, depth=0, budget=None):
    if budget is None:
        budget = [0]
    budget[0] += 1
    if budget[0] > 65536:
        raise _WorkLimit("schema work budget exceeded")
    if depth > 32:
        raise _WorkLimit("schema recursion bound")
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        if name not in root.get("$defs", {}):
            _fail("missing local definition")
        _validate(value, root["$defs"][name], root, depth + 1, budget)
    if "type" in schema:
        kind = schema["type"]
        types = {"object": dict, "array": list, "string": str, "integer": int,
                 "boolean": bool, "null": type(None)}
        if kind not in types or type(value) is not types[kind]:
            _fail("schema type mismatch")
    if "const" in schema and not _equal(value, schema["const"]):
        _fail("schema const mismatch")
    if "enum" in schema and not any(_equal(value, option) for option in schema["enum"]):
        _fail("schema enum mismatch")
    for child in schema.get("allOf", []):
        _validate(value, child, root, depth + 1, budget)
    if "anyOf" in schema:
        matches = 0
        for child in schema["anyOf"]:
            try:
                _validate(value, child, root, depth + 1, budget)
                matches += 1
            except _WorkLimit:
                raise
            except VerificationError:
                pass
        if not matches:
            _fail("no schema alternative matched")
    if "if" in schema:
        try:
            _validate(value, schema["if"], root, depth + 1, budget)
            branch = "then"
        except _WorkLimit:
            raise
        except VerificationError:
            branch = "else"
        if branch in schema:
            _validate(value, schema[branch], root, depth + 1, budget)
    if type(value) is dict:
        properties = schema.get("properties", {})
        if any(name not in value for name in schema.get("required", [])):
            _fail("required property missing")
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            _fail("unexpected property")
        for name in value.keys() & properties.keys():
            _validate(value[name], properties[name], root, depth + 1, budget)
    if type(value) is list:
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", MAX_NODES):
            _fail("array length out of bounds")
        if schema.get("uniqueItems") is True:
            if len(value) > 16:
                _fail("unique array exceeds supported contract bound")
            for index, item in enumerate(value):
                if any(_equal(item, prior) for prior in value[:index]):
                    _fail("duplicate array item")
        if "items" in schema:
            for item in value:
                _validate(item, schema["items"], root, depth + 1, budget)
    if type(value) is str:
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", MAX_STRING):
            _fail("string length out of bounds")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            _fail("schema pattern mismatch")
        if schema.get("format") == "date-time":
            utc_ticks(value)
    if type(value) in (int, Decimal):
        if "minimum" in schema and value < schema["minimum"]:
            _fail("number below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            _fail("number above maximum")


def validate_schema(value, schema):
    """Limited closed interpreter, not a general JSON Schema implementation."""
    _bounded_tree(value)
    _bounded_tree(schema)
    _check_schema_source(schema)
    _validate(value, schema, schema)


def validate_record(kind, data, contracts):
    """Validate against the exact immutable reviewed v1 contract bytes."""
    if kind not in CONTRACT_HASHES or type(contracts) is not dict:
        _fail("unknown contract")
    source = contracts.get(kind)
    if type(source) is not bytes or hashlib.sha256(source).hexdigest() != CONTRACT_HASHES[kind]:
        _fail("contract source pin mismatch")
    value = strict_json(data)
    validate_schema(value, strict_json(source))
    return value


def validate_sequence(sequence):
    """Pure chronology subset; provenance and provider truth are never inferred.

    Exactly these UTC points are required. Strict inequalities encode prior
    issuance/return/review; start/end may coincide only for an empty capture.
    """
    names = ("source_review_utc", "observation_admission_utc", "capture_start_utc",
             "capture_end_utc", "actual_tool_return_utc", "actual_review_utc",
             "disposition_utc", "bootstrap_admission_utc", "dispatch_utc")
    if type(sequence) is not dict or set(sequence) != set(names):
        _fail("chronology fields must be exact")
    points = [utc_ticks(sequence[name]) for name in names]
    for index, (before, after) in enumerate(zip(points, points[1:])):
        if before > after or (index != 2 and before == after):
            _fail("chronology reversed or non-strict")
    if points[7] - points[3] > 300 * TICKS_PER_SECOND:
        _fail("capture stale at bootstrap admission")
    return points


def validate_window(start, end, operation_start, operation_end):
    points = [utc_ticks(value) for value in (start, end, operation_start, operation_end)]
    if not points[0] <= points[2] <= points[3] <= points[1] or points[0] == points[1]:
        _fail("local window does not enclose operation")


def validate_qpc(packet, *, maximum_seconds=300):
    if type(maximum_seconds) is not int or not 1 <= maximum_seconds <= 300:
        _fail("capture cap is not bounded")
    frequency, start, end = (packet.get(name) for name in ("qpc_frequency", "qpc_start", "qpc_end"))
    if type(frequency) is not int or not 1 <= frequency <= 1000000000000:
        _fail("invalid QPC frequency")
    if any(type(value) is not int or not 0 <= value <= MAX_QPC for value in (start, end)):
        _fail("QPC value must be an exact bounded integer")
    utc_start = utc_ticks(packet.get("observed_start_utc"))
    utc_end = utc_ticks(packet.get("observed_end_utc"))
    if end < start or utc_end < utc_start:
        _fail("capture clock reversed")
    if end - start > maximum_seconds * frequency or utc_end - utc_start > maximum_seconds * TICKS_PER_SECOND:
        _fail("capture duration exceeds static cap")
    # Strict diagnostic comparison permits only one QPC tick + one UTC tick.
    # Agreement is a necessary check, never independent clock-order proof.
    if abs((end - start) * TICKS_PER_SECOND - (utc_end - utc_start) * frequency) > TICKS_PER_SECOND + frequency:
        _fail("capture UTC/QPC durations disagree")


def validate_artifact(reference, artifacts):
    if type(reference) is not dict or set(reference) != {"path", "bytes", "sha256"}:
        _fail("artifact reference must be closed")
    path = normalized_path(reference["path"])
    size, digest = reference["bytes"], reference["sha256"]
    if type(size) is not int or not 0 <= size <= MAX_ARTIFACT_BYTES:
        _fail("artifact byte count out of bounds")
    if type(digest) is not str or _HASH.fullmatch(digest) is None:
        _fail("artifact digest malformed")
    if path not in artifacts:
        _fail("artifact bytes missing")
    data = artifacts[path]
    if type(data) is not bytes or len(data) != size or hashlib.sha256(data).hexdigest() != digest:
        _fail("artifact bytes or digest mismatch")
    return data


def _artifact_map(artifacts):
    if type(artifacts) is not dict or len(artifacts) > MAX_ARTIFACTS:
        _fail("artifact map count bound")
    seen = set()
    total = 0
    for path, data in artifacts.items():
        normalized_path(path)
        folded = path.casefold()
        if folded in seen:
            _fail("case alias in artifact map")
        seen.add(folded)
        if type(data) is not bytes or len(data) > MAX_ARTIFACT_BYTES:
            _fail("artifact map byte bound")
        total += len(data)
        if total > MAX_TOTAL_ARTIFACT_BYTES:
            _fail("aggregate artifact byte bound")


def _references(value):
    if type(value) is dict:
        if set(value) == {"path", "bytes", "sha256"}:
            yield value
        else:
            for child in value.values():
                yield from _references(child)
    elif type(value) is list:
        for child in value:
            yield from _references(child)


def _assessment(status, codes, details, checked=0):
    return {
        "schema": "cho51_p3_boundary_static_assessment_v1",
        "status": status,
        "reason_codes": codes,
        "details": details,
        "artifacts_checked": checked,
        "operationally_qualified": False,
        "launch_authorized": False,
        "scientific_admission": False,
        "historical_status": "FAILED_UNRELEASED_CONSUMED",
        "historical_custody_closed": False,
        "historical_operation_released": False,
        "historical_retry_allowed": False,
    }


def assess_boundary(packet_bytes, artifacts, contracts, *, policy_bytes=None,
                    disposition_bytes=None, admission_bytes=None):
    """Static byte inspection only; output is REFUSED or UNRESOLVED, never eligible.

    Input byte maps have NO authenticated filesystem, process, host or reviewer
    identity. In particular no accepted/qualified caller boolean is consumed.
    Optional disposition/admission records add negative checks, not authority.
    """
    if packet_bytes is None:
        return _assessment("UNRESOLVED", ["RAW_OBSERVATION_INCOMPLETE"], ["No candidate evidence packet supplied."])
    checked = 0
    try:
        _artifact_map(artifacts)
        packet = validate_record("boundary-evidence", packet_bytes, contracts)
        historical = packet["historical"]
        # Explicit redundant checks make the historical invariant visible even
        # though the pinned schema also requires it.
        if historical["status"] != "FAILED_UNRELEASED_CONSUMED" or any(
            historical[name] is not False for name in ("custody_closed", "operation_released", "retry_allowed")
        ):
            return _assessment("REFUSED", ["HISTORICAL_STATE_UPGRADE"], ["Historical failure state changed."])
        old = {}
        for name, digest in HISTORICAL_HASHES.items():
            reference = historical[name]
            if reference["path"] not in artifacts:
                return _assessment("REFUSED", ["HISTORICAL_INPUT_MISSING"], ["Required old " + name + " bytes missing."])
            if reference["sha256"] != digest:
                return _assessment("REFUSED", ["HISTORICAL_HASH_MISMATCH"], ["Old input pin changed."])
            try:
                old[name] = strict_json(validate_artifact(reference, artifacts))
            except VerificationError as exc:
                return _assessment("REFUSED", ["HISTORICAL_HASH_MISMATCH"], [str(exc)])
        for name in ("disposition", "actual_audit"):
            if any(old[name].get(field) is not False for field in ("custody_closed", "operation_released")):
                return _assessment("REFUSED", ["HISTORICAL_STATE_UPGRADE"], ["Saved historical false flags changed."])
        if old["disposition"].get("same_attempt_retry_or_rearm_allowed") is not False:
            return _assessment("REFUSED", ["HISTORICAL_STATE_UPGRADE"], ["Historical retry is not false."])
        references = list(_references(packet))
        # Reusing a path under different byte identities is contradictory;
        # repeated references to the same immutable bytes are otherwise legal.
        identities = {}
        for reference in references:
            path = normalized_path(reference["path"])
            identity = (reference["bytes"], reference["sha256"])
            if path.casefold() in identities and identities[path.casefold()] != (path, identity):
                _fail("conflicting or case-aliased artifact references")
            identities[path.casefold()] = (path, identity)
            if path not in artifacts:
                return _assessment("UNRESOLVED", ["RAW_OBSERVATION_INCOMPLETE"], ["Candidate artifact bytes missing: " + path], checked)
            validate_artifact(reference, artifacts)
            checked += 1
        if type(policy_bytes) is not bytes or len(policy_bytes) > MAX_RECORD_BYTES:
            return _assessment("UNRESOLVED", ["SOURCE_OR_RUNTIME_UNPINNED"], ["Active policy bytes missing or oversized."], checked)
        if hashlib.sha256(policy_bytes).hexdigest() != packet["policy_sha256"]:
            _fail("active policy hash mismatch")
        validate_qpc(packet)
        if not utc_ticks(packet["observed_start_utc"]) > utc_ticks(OLD_RETURN_UTC):
            _fail("capture does not follow old caller-return bound")
        if utc_ticks(packet["created_utc"]) < utc_ticks(packet["observed_end_utc"]):
            _fail("packet creation precedes capture end")
        disposition = None
        if disposition_bytes is not None:
            disposition = validate_record("disposition", disposition_bytes, contracts)
            if not _equal(disposition["historical"], historical) or disposition["policy_sha256"] != packet["policy_sha256"]:
                _fail("disposition historical/policy join mismatch")
            if utc_ticks(disposition["created_utc"]) <= utc_ticks(packet["observed_end_utc"]):
                _fail("disposition does not follow capture")
            boundary = disposition["current_boundary"]
            if boundary is not None:
                evidence = validate_artifact(boundary["evidence"], artifacts)
                if evidence != packet_bytes:
                    _fail("disposition references another evidence packet")
                validate_artifact(boundary["independent_actual_review"], artifacts)
        if admission_bytes is not None:
            admission = validate_record("local-admission", admission_bytes, contracts)
            if admission["attempt_directory"].split("/")[-1] != admission["operation_id"]:
                _fail("attempt UUID does not equal operation_id")
            normalized_path(admission["attempt_directory"])
            if admission["policy_sha256"] != packet["policy_sha256"]:
                _fail("admission policy mismatch")
            created = utc_ticks(admission["created_utc"])
            capture_end = utc_ticks(packet["observed_end_utc"])
            if not 0 < created - capture_end <= 300 * TICKS_PER_SECOND:
                _fail("capture stale or future at admission")
            validate_window(admission["window_start_utc"], admission["window_end_utc"],
                            admission["created_utc"], admission["created_utc"])
            for reference in _references(admission):
                validate_artifact(reference, artifacts)
            if disposition is None:
                _fail("admission without candidate disposition")
            if validate_artifact(admission["custody_disposition"], artifacts) != disposition_bytes:
                _fail("admission disposition digest mismatch")
            if utc_ticks(disposition["created_utc"]) >= created:
                _fail("admission does not follow disposition")
            if disposition["current_boundary"] is None:
                _fail("admission references no qualified boundary")
            for field in ("host_identity_sha256", "boot_generation_sha256"):
                if admission["expected_" + field] != disposition["current_boundary"][field]:
                    _fail("admission host/generation join mismatch")
    except VerificationError as exc:
        return _assessment("REFUSED", ["EVIDENCE_CONTRADICTED"], [str(exc)], checked)
    # These are immutable implementation limitations, not fields read from a
    # candidate. Even a fully fabricated structurally conforming byte packet
    # reaches this same closed gate. No operational disposition is emitted.
    return _assessment("UNRESOLVED", [
        "PROVIDER_COVERAGE_UNQUALIFIED", "HOST_ASSOCIATION_UNESTABLISHED",
        "RESTART_KIND_UNESTABLISHED", "CLOCK_ORDER_UNESTABLISHED",
        "PERSISTED_DOMAIN_UNRESOLVED", "ACTUAL_REVIEW_MISSING",
        "SOURCE_OR_RUNTIME_UNPINNED",
    ], [
        "Pure bytes do not authenticate retained file identity, execution provenance, host or reviewer.",
        "No Windows provider/full-restart/old-event host-binding contract is qualified.",
        "Auxiliary review/admission/provider semantic contracts and cross-file source/runtime joins are not qualified.",
        "Atomic attempt claim, stop/resources, dispatch/post-operation generation and owned cleanup belong to a future controller.",
    ], checked)
