"""Bounded Windows event decoding and local-template matching, without authority.

Pure functions only. Raw XML and template pins are checked before parsing. A
matching local manifest establishes this supported flat payload shape; it does
not establish event truth, historical host identity or full-restart semantics.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import io
import re
import uuid
import xml.etree.ElementTree as ET


MAX_XML_BYTES = 65536
MAX_DEPTH = 16
MAX_NODES = 1024
MAX_SCALAR = 4096
NS = "http://schemas.microsoft.com/win/2004/08/events"
WIN_NS = "http://manifests.microsoft.com/win/2004/08/windows/events"
TAG = "{" + NS + "}"
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]{0,127}\Z")
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_HEX = re.compile(r"0[xX][0-9A-Fa-f]{1,16}\Z")
_SIGNED = re.compile(r"(?:0|-?[1-9][0-9]*)\Z")
_UTC = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,9}))?Z\Z")
_EPOCH = datetime(1970, 1, 1)
_FALSE = {
    "boundary_qualified": False,
    "host_association_authenticated": False,
    "launch_authorized": False,
    "scientific_admission": False,
}


class DecodeError(ValueError):
    """Malformed, contradictory or unsupported bounded event representation."""


def utc_ns(text):
    """Calendar-valid UTC as integer Unix nanoseconds; never use a float clock."""
    if type(text) is not str:
        raise DecodeError("UTC string required")
    match = _UTC.fullmatch(text)
    if match is None:
        raise DecodeError("UTC syntax/precision unsupported")
    try:
        base = datetime(*(int(value) for value in match.groups()[:6]))
    except ValueError as exc:
        raise DecodeError("invalid UTC calendar value") from exc
    elapsed = base - _EPOCH
    return ((elapsed.days * 86400 + elapsed.seconds) * 10**9
            + int((match.group(7) or "").ljust(9, "0")))


def _unsigned(text, bits, *, hexadecimal=True):
    if type(text) is not str or not 1 <= len(text) <= 20:
        raise DecodeError("bounded unsigned integer string required")
    if hexadecimal and _HEX.fullmatch(text):
        value = int(text, 16)
    elif _DECIMAL.fullmatch(text):
        value = int(text, 10)
    else:
        raise DecodeError("noncanonical unsigned integer")
    if value >= 1 << bits:
        raise DecodeError("unsigned integer overflow")
    return value


def _guid(text):
    if type(text) is not str or re.fullmatch(
            r"(?:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|"
            r"\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\})", text) is None:
        raise DecodeError("canonical GUID spelling required")
    return str(uuid.UUID(text.strip("{}")))


def _sid(text):
    if type(text) is not str or len(text) > 184:
        raise DecodeError("bounded SID string required")
    parts = text.split("-")
    if not 4 <= len(parts) <= 18 or parts[:2] != ["S", "1"]:
        raise DecodeError("unsupported SID shape")
    _unsigned(parts[2], 48, hexadecimal=False)
    for value in parts[3:]:
        _unsigned(value, 32, hexadecimal=False)
    return text


def _pinned_xml(row):
    if type(row) is not dict or set(row) != {"xml", "bytes", "sha256"}:
        raise DecodeError("closed raw XML pin required")
    text, size, digest = (row[name] for name in ("xml", "bytes", "sha256"))
    if (type(text) is not str or len(text) > MAX_XML_BYTES or type(size) is not int
            or not 1 <= size <= MAX_XML_BYTES):
        raise DecodeError("raw XML type/byte bound")
    if type(digest) is not str or _HASH.fullmatch(digest) is None:
        raise DecodeError("lowercase XML SHA256 required")
    try:
        raw = text.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise DecodeError("invalid XML Unicode") from exc
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
        raise DecodeError("raw XML byte/hash mismatch")
    # EvtRender's event XML needs no declaration, DTD, entity declaration,
    # processing instruction, comment or CDATA. Refuse those representations.
    if "<!" in text or "<?" in text:
        raise DecodeError("XML declarations/directives unsupported")
    try:
        root = ET.fromstring(text)
    except (ET.ParseError, ValueError) as exc:
        raise DecodeError("malformed XML") from exc
    pending, nodes = [(root, 1)], 0
    while pending:
        element, depth = pending.pop()
        nodes += 1
        if depth > MAX_DEPTH or nodes > MAX_NODES or len(element.attrib) > 16:
            raise DecodeError("XML structural bound")
        if any(len(key) > 256 or len(value) > MAX_SCALAR for key, value in element.attrib.items()):
            raise DecodeError("XML attribute bound")
        if element.text is not None and len(element.text) > MAX_SCALAR:
            raise DecodeError("XML scalar bound")
        if element.tail is not None and element.tail.strip():
            raise DecodeError("mixed XML content unsupported")
        pending.extend((child, depth + 1) for child in element)
    return root


def _container(element, allowed_attributes=()):
    if set(element.attrib) - set(allowed_attributes):
        raise DecodeError("unsupported container attributes")
    if element.text is not None and element.text.strip():
        raise DecodeError("mixed container text unsupported")


def _scalar(element, allowed_attributes=(), *, empty=False):
    if len(element) or set(element.attrib) - set(allowed_attributes):
        raise DecodeError("nested scalar or unsupported scalar attributes")
    value = element.text or ""
    if not empty and not value:
        raise DecodeError("required scalar missing")
    return value


def _attributes_only(element, allowed_attributes):
    _scalar(element, allowed_attributes, empty=True)
    if element.text and element.text.strip():
        raise DecodeError("text in attribute-only event field")


def _query(query):
    required = {"key", "provider", "channel", "event_ids", "from_utc", "to_utc"}
    if type(query) is not dict or not required <= set(query):
        raise DecodeError("query metadata incomplete")
    for key in ("key", "provider", "channel"):
        if type(query[key]) is not str or not 1 <= len(query[key]) <= 256:
            raise DecodeError("query identity type/bound")
    values = query["event_ids"]
    if (type(values) is not list or not 1 <= len(values) <= 32
            or any(type(value) is not int or not 0 <= value <= 65535 for value in values)
            or len(set(values)) != len(values)):
        raise DecodeError("query event IDs malformed")
    start, end = utc_ns(query["from_utc"]), utc_ns(query["to_utc"])
    if start > end:
        raise DecodeError("query time bounds reversed")
    return start, end


def decode_event(row, query):
    """Decode one selected raw event; query membership is a checked constraint."""
    start, end = _query(query)
    root = _pinned_xml(row)
    if root.tag != TAG + "Event":
        raise DecodeError("wrong event root/namespace")
    _container(root)
    children = {}
    for child in root:
        if child.tag not in {TAG + "System", TAG + "EventData"} or child.tag in children:
            raise DecodeError("duplicate/unsupported event section")
        children[child.tag] = child
    system = children.get(TAG + "System")
    if system is None:
        raise DecodeError("System section missing")
    _container(system)
    names = {"Provider", "EventID", "Version", "Level", "Task", "Opcode", "Keywords",
             "TimeCreated", "EventRecordID", "Correlation", "Execution", "Channel", "Computer", "Security"}
    fields = {}
    for element in system:
        if not element.tag.startswith(TAG) or element.tag[len(TAG):] not in names:
            raise DecodeError("unsupported System field/namespace")
        name = element.tag[len(TAG):]
        if name in fields:
            raise DecodeError("duplicate System field")
        fields[name] = element
    if not {"Provider", "EventID", "Version", "TimeCreated", "EventRecordID", "Channel", "Computer"} <= set(fields):
        raise DecodeError("required System field missing")
    provider = fields["Provider"]
    _attributes_only(provider, ("Name", "Guid", "EventSourceName"))
    provider_name = provider.attrib.get("Name")
    if type(provider_name) is not str or not 1 <= len(provider_name) <= 256:
        raise DecodeError("provider name missing/bounded")
    provider_guid = _guid(provider.attrib["Guid"]) if "Guid" in provider.attrib else None
    event_id = _unsigned(_scalar(fields["EventID"], ("Qualifiers",)), 16, hexadecimal=False)
    if "Qualifiers" in fields["EventID"].attrib:
        _unsigned(fields["EventID"].attrib["Qualifiers"], 16, hexadecimal=False)
    version = _unsigned(_scalar(fields["Version"]), 8, hexadecimal=False)
    record_id = _unsigned(_scalar(fields["EventRecordID"]), 64, hexadecimal=False)
    channel, computer = (_scalar(fields[name]) for name in ("Channel", "Computer"))
    if not 1 <= len(computer) <= 256 or not 1 <= len(channel) <= 256:
        raise DecodeError("channel/computer label bound")
    time = fields["TimeCreated"]
    _attributes_only(time, ("SystemTime",))
    timestamp = time.attrib.get("SystemTime")
    timestamp_ns = utc_ns(timestamp)
    if provider_name != query["provider"] or channel != query["channel"] or event_id not in query["event_ids"]:
        raise DecodeError("event identity outside selected query")
    if not start <= timestamp_ns <= end:
        raise DecodeError("event UTC outside selected query")
    for name, bits in (("Level", 8), ("Task", 16), ("Opcode", 8), ("Keywords", 64)):
        if name in fields:
            _unsigned(_scalar(fields[name]), bits, hexadecimal=name == "Keywords")
    if "Correlation" in fields:
        element = fields["Correlation"]
        _attributes_only(element, ("ActivityID", "RelatedActivityID"))
        for value in element.attrib.values():
            _guid(value)
    if "Execution" in fields:
        element = fields["Execution"]
        _attributes_only(element, ("ProcessID", "ThreadID", "ProcessorID", "SessionID", "KernelTime", "UserTime", "ProcessorTime"))
        for name, value in element.attrib.items():
            _unsigned(value, 64 if name in {"KernelTime", "UserTime", "ProcessorTime"} else 32, hexadecimal=False)
    if "Security" in fields:
        element = fields["Security"]
        _attributes_only(element, ("UserID",))
        if "UserID" in element.attrib:
            _sid(element.attrib["UserID"])
    data, folded = {}, set()
    if TAG + "EventData" in children:
        payload = children[TAG + "EventData"]
        _container(payload)
        for element in payload:
            if element.tag != TAG + "Data" or set(element.attrib) != {"Name"}:
                raise DecodeError("unsupported/unnamed event payload field")
            name = element.attrib["Name"]
            if _NAME.fullmatch(name) is None or name.casefold() in folded:
                raise DecodeError("duplicate/aliased/invalid event data name")
            folded.add(name.casefold())
            data[name] = _scalar(element, ("Name",), empty=True)
    if "pid_hex_values" in query:
        values = query["pid_hex_values"]
        if (type(values) is not list or not 1 <= len(values) <= 8
                or any(type(value) is not str or _HEX.fullmatch(value) is None
                       or int(value, 16) != 302124 for value in values)):
            raise DecodeError("historical PID query spelling invalid")
        if provider_name != "Microsoft-Windows-Security-Auditing" or channel != "Security" or event_id != 4688:
            raise DecodeError("PID probe outside supported event family")
        value = data.get("NewProcessId")
        if value not in values or _unsigned(value, 64) != 302124:
            raise DecodeError("event PID does not match selected historical PID")
    return {
        "schema": "cho51_p3_event_decode_v4",
        "raw": {"bytes": row["bytes"], "sha256": row["sha256"]},
        "provider_name": provider_name, "provider_guid": provider_guid,
        "event_id": event_id, "version": version, "record_id": record_id,
        "timestamp_utc": timestamp, "timestamp_ns": timestamp_ns,
        "channel": channel, "computer_label_sha256": hashlib.sha256(computer.encode("utf-8")).hexdigest(),
        "data": data, **_FALSE,
    }


def _typed(text, kind):
    if kind == "win:UnicodeString":
        if type(text) is not str or len(text) > MAX_SCALAR:
            raise DecodeError("UnicodeString bound/type")
        return text
    unsigned = re.fullmatch(r"win:UInt(8|16|32|64)", kind)
    if unsigned:
        return _unsigned(text, int(unsigned.group(1)))
    signed = re.fullmatch(r"win:Int(8|16|32|64)", kind)
    if signed:
        if type(text) is not str or len(text) > 20 or _SIGNED.fullmatch(text) is None:
            raise DecodeError("noncanonical signed integer")
        value, bits = int(text), int(signed.group(1))
        if not -(1 << (bits - 1)) <= value < 1 << (bits - 1):
            raise DecodeError("signed integer overflow")
        return value
    if kind in {"win:HexInt32", "win:HexInt64", "win:Pointer"}:
        if type(text) is not str or _HEX.fullmatch(text) is None:
            raise DecodeError("hex scalar representation required")
        return _unsigned(text, 32 if kind == "win:HexInt32" else 64)
    if kind == "win:Boolean":
        if text not in {"true", "false", "1", "0"}:
            raise DecodeError("Boolean scalar representation")
        return text in {"true", "1"}
    if kind == "win:GUID":
        return _guid(text)
    if kind == "win:FILETIME":
        return utc_ns(text)
    if kind == "win:SID":
        return _sid(text)
    raise DecodeError("unsupported flat scalar input type")


def _template_xml(row):
    # Attribute values such as win:UInt32 are lexical QNames, which ElementTree
    # does not expand. Retain each element's actual in-scope namespace bindings
    # rather than trusting the literal prefix or a declaration elsewhere.
    _pinned_xml(row)
    scopes, stack, pending = {}, [], []
    parser = ET.iterparse(io.StringIO(row["xml"]), events=("start-ns", "start", "end"))
    for action, value in parser:
        if action == "start-ns":
            prefix, uri = value
            if len(pending) >= 16 or len(prefix) > 128 or len(uri) > MAX_SCALAR:
                raise DecodeError("template namespace declaration bound")
            pending.append((prefix, uri))
        elif action == "start":
            current = dict(stack[-1]) if stack else {}
            current.update(pending)
            pending.clear()
            if len(current) > 16:
                raise DecodeError("template namespace scope bound")
            scopes[id(value)] = current
            stack.append(current)
        else:
            stack.pop()
    return parser.root, scopes


def _template_qname(value, namespaces):
    if (type(value) is not str or re.fullmatch(r"win:[A-Za-z][A-Za-z0-9]*", value) is None
            or namespaces.get("win") != WIN_NS):
        raise DecodeError("unsupported or incorrectly bound template type QName")
    return value


def qualify_event(event, provider_record):
    """Match supported flat data to retained local metadata; never qualify a boot."""
    def unsupported(reason):
        return {"status": "UNSUPPORTED", "reason": reason, **_FALSE}

    try:
        if type(event) is not dict or type(provider_record) is not dict:
            raise DecodeError("event/provider record type")
        if any(event.get(key) is not False for key in _FALSE):
            raise DecodeError("event attempted authority upgrade")
        if event.get("schema") != "cho51_p3_event_decode_v4":
            raise DecodeError("unsupported decoded event schema")
        if event.get("provider_name") != provider_record.get("provider") or event.get("provider_guid") is None:
            raise DecodeError("provider identity unavailable/different")
        if _guid(event["provider_guid"]) != _guid(provider_record.get("guid")):
            raise DecodeError("provider GUID differs")
        event_id, version = event.get("event_id"), event.get("version")
        if type(event_id) is not int or not 0 <= event_id <= 65535 or type(version) is not int or not 0 <= version <= 255:
            raise DecodeError("decoded event identity type/range")
        definitions = provider_record.get("definitions")
        if type(definitions) is not list or len(definitions) > 256:
            raise DecodeError("bounded provider definitions required")
        selected, seen = None, set()
        for definition in definitions:
            if type(definition) is not dict or set(definition) != {"event_id", "version", "template"}:
                raise DecodeError("closed event definition required")
            identity = (definition["event_id"], definition["version"])
            if (type(identity[0]) is not int or not 0 <= identity[0] <= 65535
                    or type(identity[1]) is not int or not 0 <= identity[1] <= 255 or identity in seen):
                raise DecodeError("duplicate/malformed provider definition")
            seen.add(identity)
            if identity == (event_id, version):
                selected = definition
        if selected is None:
            raise DecodeError("event ID/version absent from local metadata")
        root, namespaces = _template_xml(selected["template"])
        if root.tag != TAG + "template":
            raise DecodeError("unsupported native template root/namespace")
        _container(root, ("tid",))
        data = event.get("data")
        if type(data) is not dict or len(data) > 256:
            raise DecodeError("decoded payload type/bound")
        fields, folded = [], set()
        for element in root:
            if (element.tag != TAG + "data" or set(element.attrib) - {"name", "inType", "outType"}
                    or not {"name", "inType"} <= set(element.attrib)):
                raise DecodeError("unsupported template struct/array/attributes")
            _attributes_only(element, ("name", "inType", "outType"))
            name = element.attrib["name"]
            if _NAME.fullmatch(name) is None or name.casefold() in folded:
                raise DecodeError("template duplicate/aliased/invalid field")
            folded.add(name.casefold())
            kind = _template_qname(element.attrib["inType"], namespaces[id(element)])
            if "outType" in element.attrib:
                # Output annotation identity is checked; its display semantics
                # are not interpreted as input conversion or restart evidence.
                _template_qname(element.attrib["outType"], namespaces[id(element)])
            fields.append((name, kind))
        if list(data) != [name for name, _ in fields]:
            raise DecodeError("payload names/order differ from exact template")
        typed = {name: _typed(data[name], kind) for name, kind in fields}
        return {"status": "MATCHED_LOCAL_TEMPLATE", "typed_data": typed,
                "template": {"bytes": selected["template"]["bytes"], "sha256": selected["template"]["sha256"]},
                "event_id": event_id, "version": version, **_FALSE}
    except (DecodeError, KeyError, TypeError, ValueError) as exc:
        return unsupported(str(exc)[:256])
