"""Fixed local passive provider capture; no restart or historical authority.

Only invoked under a fresh reviewed v4 admission. No policy/audit configuration,
privilege change, process enumeration, remote session or subprocess is performed.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
from datetime import UTC, datetime
import hashlib
import re
import time
import uuid

MAX_EVENTS = 16  # per family; separate sentinel, never borrowed from another
MAX_XML_BYTES = 65536
MAX_EVENT_BYTES = 384 * 1024
MAX_TEMPLATE_BYTES = 192 * 1024
MAX_DEFINITIONS = 64
MAX_ENUMERATED = 2048  # per registered publisher
MAX_SECONDS = 20


class CaptureError(ValueError):
    pass


def raw_record(text):
    raw = text.encode("utf-8", errors="strict")
    if len(raw) > MAX_XML_BYTES:
        raise CaptureError("XML byte cap")
    return {"xml": text, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def query_spec(family, plan, cutoff, decoder):
    allowed = {"key", "provider", "channel", "event_ids", "pid_hex_values"}
    if (type(family) is not dict or set(family) - allowed
            or not allowed - {"pid_hex_values"} <= set(family)
            or type(family["key"]) is not str or not re.fullmatch(r"[a-z_]{1,40}", family["key"])
            or type(family["provider"]) is not str or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", family["provider"])
            or family["channel"] not in {"System", "Security"}
            or type(family["event_ids"]) is not list or not 1 <= len(family["event_ids"]) <= 4
            or any(type(x) is not int or not 0 <= x <= 65535 for x in family["event_ids"])
            or len(set(family["event_ids"])) != len(family["event_ids"])):
        raise CaptureError("fixed family shape refused")
    spec = dict(family)
    historical = family["key"] == "historical_creation"
    spec["from_utc"] = plan["old_entry_utc"] if historical else plan["old_return_utc"]
    spec["to_utc"] = plan["old_return_utc"] if historical else cutoff
    if decoder.utc_ns(spec["from_utc"]) > decoder.utc_ns(spec["to_utc"]):
        raise CaptureError("query chronology reversed")
    pid_values = spec.get("pid_hex_values")
    if historical:
        if (family["channel"] != "Security" or family["event_ids"] != [4688]
                or plan["historical_pid"] != 302124 or type(pid_values) is not list
                or not 1 <= len(pid_values) <= 3
                or any(type(x) is not str or re.fullmatch(r"0[xX][0-9a-fA-F]{1,8}", x) is None
                       or int(x, 16) != 302124 for x in pid_values)):
            raise CaptureError("historical PID selection refused")
    elif pid_values is not None or family["channel"] != "System":
        raise CaptureError("unexpected PID or channel filter")
    ids = " or ".join("EventID=" + str(x) for x in spec["event_ids"])
    system = ("System[Provider[@Name='" + spec["provider"] + "'] and (" + ids + ") and "
              "TimeCreated[@SystemTime>='" + spec["from_utc"] + "' and @SystemTime<='" + spec["to_utc"] + "']]")
    condition = system
    if historical:
        condition += " and EventData[" + " or ".join("Data[@Name='NewProcessId']='" + x + "'" for x in pid_values) + "]"
    return spec, "*[" + condition + "]"


class _Value(ctypes.Union):
    _fields_ = [("unsigned32", w.DWORD), ("unsigned64", ctypes.c_ulonglong), ("pointer", ctypes.c_void_p)]


class _Variant(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = [("value", _Value), ("count", w.DWORD), ("type", w.DWORD)]


def decode_variant(buffer, used, expected):
    """Bounds-check every pointer before reading a returned native variant."""
    if type(used) is not int or not ctypes.sizeof(_Variant) <= used <= ctypes.sizeof(buffer):
        raise CaptureError("variant size")
    value = _Variant.from_buffer(buffer)
    if value.type != expected or value.count != 0:
        raise CaptureError("variant type/array refused")
    if expected == 8:  # EvtVarTypeUInt32
        return int(value.unsigned32)
    if expected not in (1, 15):  # String, Guid
        raise CaptureError("unsupported variant")
    pointer = value.pointer
    low, high = ctypes.addressof(buffer) + ctypes.sizeof(_Variant), ctypes.addressof(buffer) + used
    if pointer is None or not low <= pointer < high:
        raise CaptureError("variant pointer outside buffer")
    if expected == 15:
        if pointer + 16 > high:
            raise CaptureError("GUID pointer bound")
        return str(uuid.UUID(bytes_le=ctypes.string_at(pointer, 16)))
    if pointer % 2 or (high - pointer) % 2:
        raise CaptureError("wide string alignment")
    raw = ctypes.string_at(pointer, high - pointer)
    for index in range(0, len(raw), 2):
        if raw[index:index + 2] == b"\0\0":
            return raw[:index].decode("utf-16-le", errors="strict")
    raise CaptureError("unterminated wide string")


class Native:
    def __init__(self):
        self.dll = ctypes.WinDLL("wevtapi.dll", use_last_error=True, winmode=0x800)
        signatures = {
            "EvtQuery": ([w.HANDLE, w.LPCWSTR, w.LPCWSTR, w.DWORD], w.HANDLE),
            "EvtNext": ([w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE), w.DWORD, w.DWORD, ctypes.POINTER(w.DWORD)], w.BOOL),
            "EvtRender": ([w.HANDLE, w.HANDLE, w.DWORD, w.DWORD, w.LPVOID, ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD)], w.BOOL),
            "EvtClose": ([w.HANDLE], w.BOOL),
            "EvtOpenPublisherMetadata": ([w.HANDLE, w.LPCWSTR, w.LPCWSTR, w.DWORD, w.DWORD], w.HANDLE),
            "EvtGetPublisherMetadataProperty": ([w.HANDLE, w.DWORD, w.DWORD, w.DWORD, w.LPVOID, ctypes.POINTER(w.DWORD)], w.BOOL),
            "EvtOpenEventMetadataEnum": ([w.HANDLE, w.DWORD], w.HANDLE),
            "EvtNextEventMetadata": ([w.HANDLE, w.DWORD], w.HANDLE),
            "EvtGetEventMetadataProperty": ([w.HANDLE, w.DWORD, w.DWORD, w.DWORD, w.LPVOID, ctypes.POINTER(w.DWORD)], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.dll, name)
            function.argtypes, function.restype = args, result
        self.deadline = time.monotonic() + MAX_SECONDS
        self.close_errors = []
        self.opened = self.closed = 0
        self.event_bytes = self.template_bytes = 0

    def check(self):
        if time.monotonic() >= self.deadline:
            raise CaptureError("capture deadline")

    def adopt(self, handle, operation):
        if not handle:
            raise OSError(ctypes.get_last_error(), operation)
        self.opened += 1
        return handle

    def close(self, handle):
        if handle:
            if self.dll.EvtClose(handle):
                self.closed += 1
            else:
                self.close_errors.append("EvtClose:" + str(ctypes.get_last_error()))

    def property(self, handle, index, expected, publisher=False):
        self.check()
        call = self.dll.EvtGetPublisherMetadataProperty if publisher else self.dll.EvtGetEventMetadataProperty
        used = w.DWORD()
        ok = call(handle, index, 0, 0, None, ctypes.byref(used))
        if ok or ctypes.get_last_error() != 122 or not 16 <= used.value <= MAX_XML_BYTES:
            raise CaptureError("metadata property allocation refused")
        buffer = ctypes.create_string_buffer(used.value)
        if not call(handle, index, 0, len(buffer), buffer, ctypes.byref(used)):
            raise OSError(ctypes.get_last_error(), "metadata property")
        return decode_variant(buffer, int(used.value), expected)

    def metadata(self, spec):
        result = {"provider": spec["provider"], "guid": None, "definitions": [], "enumerated": 0,
                  "exhausted": False, "truncated": False, "errors": []}
        publisher = enumeration = None
        try:
            self.check()
            publisher = self.adopt(self.dll.EvtOpenPublisherMetadata(None, spec["provider"], None, 0, 0), "EvtOpenPublisherMetadata")
            result["guid"] = self.property(publisher, 0, 15, publisher=True)
            enumeration = self.adopt(self.dll.EvtOpenEventMetadataEnum(publisher, 0), "EvtOpenEventMetadataEnum")
            for _ in range(MAX_ENUMERATED + 1):
                self.check()
                definition = self.dll.EvtNextEventMetadata(enumeration, 0)
                if not definition:
                    code = ctypes.get_last_error()
                    if code == 259:
                        result["exhausted"] = True
                        break
                    raise OSError(code, "EvtNextEventMetadata")
                self.adopt(definition, "EvtNextEventMetadata")
                try:
                    if result["enumerated"] >= MAX_ENUMERATED:
                        result["truncated"] = True
                        break
                    result["enumerated"] += 1
                    event_id = self.property(definition, 0, 8)
                    if event_id not in spec["event_ids"]:
                        continue
                    version = self.property(definition, 1, 8)
                    template = raw_record(self.property(definition, 8, 1))
                    if (len(result["definitions"]) >= MAX_DEFINITIONS
                            or self.template_bytes + template["bytes"] > MAX_TEMPLATE_BYTES):
                        result["truncated"] = True
                        break
                    self.template_bytes += template["bytes"]
                    result["definitions"].append({"event_id": event_id, "version": version, "template": template})
                finally:
                    self.close(definition)
        except (OSError, ValueError) as exc:
            result["errors"].append(type(exc).__name__ + ":" + str(exc)[:256])
        finally:
            self.close(enumeration)
            self.close(publisher)
        return result

    def render(self, handle):
        used, count = w.DWORD(), w.DWORD()
        ok = self.dll.EvtRender(None, handle, 1, 0, None, ctypes.byref(used), ctypes.byref(count))
        if ok or ctypes.get_last_error() != 122 or not 2 <= used.value <= MAX_XML_BYTES or used.value % 2:
            raise CaptureError("event allocation refused")
        allocation = used.value
        buffer = ctypes.create_string_buffer(allocation)
        if not self.dll.EvtRender(None, handle, 1, allocation, buffer, ctypes.byref(used), ctypes.byref(count)):
            raise OSError(ctypes.get_last_error(), "EvtRender")
        if not 2 <= used.value <= allocation or used.value % 2:
            raise CaptureError("event returned size refused")
        raw = bytes(buffer[:used.value])
        if not raw.endswith(b"\0\0") or any(raw[i:i+2] == b"\0\0" for i in range(0, len(raw)-2, 2)):
            raise CaptureError("event termination refused")
        return raw_record(raw[:-2].decode("utf-16-le", errors="strict"))

    def events(self, spec, xpath):
        result = {"spec": spec, "xpath": xpath, "reverse_direction": True, "events": [],
                  "selected_query_exhausted": False, "truncated": False, "errors": []}
        query = None
        try:
            self.check()
            query = self.adopt(self.dll.EvtQuery(None, spec["channel"], xpath, 0x201), "EvtQuery")
            cap = 4 if spec["key"] == "historical_creation" else MAX_EVENTS
            for _ in range(cap + 1):
                self.check()
                handles, returned = (w.HANDLE * 1)(), w.DWORD()
                ok = self.dll.EvtNext(query, 1, handles, 250, 0, ctypes.byref(returned))
                # Adopt any nonzero returned handle before inspecting success/count.
                handle = handles[0]
                if handle:
                    self.adopt(handle, "EvtNext")
                try:
                    if not ok:
                        code = ctypes.get_last_error()
                        if code == 259 and not handle and returned.value == 0:
                            result["selected_query_exhausted"] = True
                            break
                        raise OSError(code, "EvtNext")
                    if returned.value != 1 or not handle:
                        raise CaptureError("EvtNext count/handle mismatch")
                    if len(result["events"]) >= cap:
                        result["truncated"] = True
                        break
                    row = self.render(handle)
                    if self.event_bytes + row["bytes"] > MAX_EVENT_BYTES:
                        result["truncated"] = True
                        break
                    self.event_bytes += row["bytes"]
                    result["events"].append(row)
                finally:
                    self.close(handle)
        except (OSError, ValueError) as exc:
            result["errors"].append(type(exc).__name__ + ":" + str(exc)[:256])
        finally:
            self.close(query)
        return result


def collect(plan, decoder):
    if (plan.get("schema") != "cho51_p3_provider_plan_v4" or len(plan["families"]) != 7
            or any(plan.get(key) is not False for key in
                   ("boundary_qualified", "host_association_authenticated", "launch_authorized", "scientific_admission"))):
        raise CaptureError("plan kind or authority")
    kernel = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
    for name in ("QueryPerformanceCounter", "QueryPerformanceFrequency"):
        call = getattr(kernel, name)
        call.argtypes, call.restype = [ctypes.POINTER(ctypes.c_longlong)], w.BOOL
    def qpc(name):
        value = ctypes.c_longlong()
        if not getattr(kernel, name)(ctypes.byref(value)) or not 0 <= value.value <= 9007199254740991:
            raise CaptureError("QPC unavailable or outside bound")
        return value.value
    frequency = qpc("QueryPerformanceFrequency")
    if not frequency:
        raise CaptureError("zero QPC frequency")
    start_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    start = qpc("QueryPerformanceCounter")
    native, queries = Native(), []
    for family in plan["families"]:
        spec, xpath = query_spec(family, plan, start_utc, decoder)
        provider = native.metadata(spec)
        query = native.events(spec, xpath)
        query["metadata"] = provider
        query["decoded"] = []
        seen = set()
        for row in query["events"]:
            try:
                event = decoder.decode_event(row, spec)
                identity = (event["channel"], event["record_id"])
                if identity in seen:
                    raise CaptureError("duplicate selected record identity")
                seen.add(identity)
                qualification = decoder.qualify_event(event, provider)
                query["decoded"].append({"raw_sha256": row["sha256"], "event": event, "qualification": qualification})
            except (ValueError, TypeError) as exc:
                query["decoded"].append({"raw_sha256": row["sha256"], "status": "REFUSED_DECODING",
                                         "reason": type(exc).__name__ + ":" + str(exc)[:256]})
        queries.append(query)
    end = qpc("QueryPerformanceCounter")
    if end < start:
        raise CaptureError("QPC reversed")
    return {"schema": "cho51_p3_provider_capture_v4", "status": "UNRESOLVED", "queries": queries,
            "observed_start_utc": start_utc, "observed_end_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "qpc_start": start, "qpc_end": end, "qpc_frequency": frequency,
            "native_handles_opened": native.opened, "native_handles_closed": native.closed,
            "native_close_errors": native.close_errors, "native_handles_closed_cleanly": native.opened == native.closed and not native.close_errors,
            "event_xml_bytes": native.event_bytes, "template_xml_bytes": native.template_bytes,
            "historical_custody_closed": False, "historical_operation_released": False, "historical_retry_allowed": False,
            "host_association_authenticated": False, "restart_qualified": False, "clock_order_qualified": False,
            "persisted_domain_excluded": False, "boundary_qualified": False, "launch_authorized": False, "scientific_admission": False,
            "limitations": ["Local labels/PID/time/template matches are candidates, not historical host authentication",
                            "Event IDs/BootType values do not independently qualify full restart semantics",
                            "Selected query exhaustion is not complete or untampered log history",
                            "Permission failures and missing audit records are unknowns, not negative process proof",
                            "No cross-boot QPC, persisted-domain or old cleanup inference"]}
