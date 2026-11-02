"""Read-only, bounded Sysmon candidate capture. No custody or launch authority.

The caller supplies the pinned v4 collector and v5 decoder modules. NativeQuery
uses their native adapter; tests supply a fake with the same query interface.
"""
from datetime import UTC, datetime
import ctypes
import re
import uuid

CHANNEL = "Microsoft-Windows-Sysmon/Operational"
PROVIDER = "Microsoft-Windows-Sysmon"
START = "2026-10-27T17:04:50Z"
END = "2026-10-27T17:05:15Z"
PID = "302124"
REQUEST = "4cab7e95a2aa4d48f6b3b4c1946c910883cc88ab559c57394d3cdb8463cc0b79"
SCRIPT = "bootstrap-observation_004.ps1"
MAX_BYTES = 384 * 1024
MAX_GUIDS = 8


def guid(value):
    if type(value) is not str or re.fullmatch(r"\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}", value) is None:
        raise ValueError("invalid Sysmon GUID")
    uuid.UUID(value[1:-1])
    # XPath string equality is case-sensitive. Reuse the exact observed spelling.
    return value


def spec(key, ids, start, end, selector=None):
    if any(type(t) is not str or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?Z", t) is None for t in (start, end)):
        raise ValueError("UTC XPath syntax")
    if key not in {"seed", "guid", "service", "config", "error", "oldest", "newest"}:
        raise ValueError("query key")
    if key == "seed":
        if ids != [1] or start != START or end != END or selector is not None:
            raise ValueError("seed scope")
        predicate = "(Data[@Name='ProcessId']='302124' or Data[@Name='ParentProcessId']='302124')"
    elif key == "guid":
        if ids != [1, 5] or start != START:
            raise ValueError("GUID scope")
        selector = guid(selector)
        predicate = "(Data[@Name='ProcessGuid']='%s' or Data[@Name='ParentProcessGuid']='%s')" % (selector, selector)
    else:
        expected = {"service": [4], "config": [16], "error": [255], "oldest": [1, 4, 5, 16, 255], "newest": [1, 4, 5, 16, 255]}
        if ids != expected[key] or selector is not None:
            raise ValueError("fixed query scope")
        predicate = None
    info = {"key": key, "provider": PROVIDER, "channel": CHANNEL, "event_ids": ids,
            "from_utc": start, "to_utc": end, "selector": selector}
    ids_clause = " or ".join("EventID=" + str(x) for x in ids)
    system = "System[Provider[@Name='%s'] and (%s) and TimeCreated[@SystemTime>='%s' and @SystemTime<='%s']]" % (PROVIDER, ids_clause, start, end)
    xpath = "*[" + system + (" and EventData[" + predicate + "]" if predicate else "") + "]"
    return info, xpath


class NativeQuery:
    def __init__(self, frozen):
        self.n = frozen.Native()
        self.frozen = frozen

    def query(self, info, xpath, cap, reverse=True):
        n = self.n
        result = {"spec": info, "xpath": xpath, "reverse_direction": reverse, "events": [],
                  "selected_query_exhausted": False, "truncated": False, "errors": []}
        query = None
        try:
            n.check()
            query = n.adopt(n.dll.EvtQuery(None, CHANNEL, xpath, 0x201 if reverse else 0x101), "EvtQuery")
            for _ in range(cap + 1):
                n.check()
                handles, returned = (self.frozen.w.HANDLE * 1)(), self.frozen.w.DWORD()
                ok = n.dll.EvtNext(query, 1, handles, 250, 0, ctypes.byref(returned))
                handle = handles[0]
                if handle:
                    n.adopt(handle, "EvtNext")
                try:
                    if not ok:
                        code = ctypes.get_last_error()
                        if code == 259 and not handle and returned.value == 0:
                            result["selected_query_exhausted"] = True
                            break
                        raise OSError(code, "EvtNext")
                    if returned.value != 1 or not handle:
                        raise ValueError("EvtNext count/handle mismatch")
                    if len(result["events"]) == cap:
                        result["truncated"] = True
                        break
                    row = n.render(handle)
                    if n.event_bytes + row["bytes"] > MAX_BYTES:
                        result["truncated"] = True
                        break
                    n.event_bytes += row["bytes"]
                    result["events"].append(row)
                finally:
                    n.close(handle)
        except (OSError, ValueError) as exc:
            result["errors"].append(type(exc).__name__ + ":" + str(exc)[:256])
        finally:
            n.close(query)
        return result

    def health(self):
        n = self.n
        return {"opened": n.opened, "closed": n.closed, "close_errors": list(n.close_errors),
                "closed_cleanly": n.opened == n.closed and not n.close_errors, "raw_bytes": n.event_bytes}


def run(frozen, decoder, *, native=None, cutoff=None):
    """Capture once. cutoff is injectable only for a deterministic test harness."""
    cutoff = cutoff or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    if decoder.utc_ns(cutoff) < decoder.utc_ns(END):
        raise ValueError("capture cutoff before historical window")
    backend = native if native is not None else NativeQuery(frozen)
    queries, seen_guids, pending, queued = [], {}, [], set()
    total_bytes = 0
    guid_limit_hit = False

    def enqueue(value):
        nonlocal guid_limit_hit
        spelling = guid(value)
        identity = spelling.casefold()
        if identity not in queued:
            if len(queued) < MAX_GUIDS:
                queued.add(identity)
                pending.append(spelling)
            else:
                guid_limit_hit = True

    def capture(key, ids, start, end, selector=None, cap=16, reverse=True):
        nonlocal total_bytes, guid_limit_hit
        info, xpath = spec(key, ids, start, end, selector)
        result = backend.query(info, xpath, cap, reverse)
        result["decoded"] = []
        if len(result["events"]) > cap:
            raise ValueError("backend exceeded row cap")
        for raw in result["events"]:
            total_bytes += raw["bytes"]
            if total_bytes > MAX_BYTES:
                raise ValueError("backend exceeded total raw cap")
            try:
                event = decoder.decode_event(raw, info)
                data = event["data"]
                if key == "seed" and PID not in (data.get("ProcessId"), data.get("ParentProcessId")):
                    raise ValueError("seed PID filter mismatch")
                if key == "guid":
                    values = [guid(data[name]) for name in ("ProcessGuid", "ParentProcessGuid") if data.get(name)]
                    if info["selector"].casefold() not in [value.casefold() for value in values]:
                        raise ValueError("GUID filter mismatch")
                if key in {"seed", "guid"} and event["event_id"] == 1:
                    child = guid(data["ProcessGuid"])
                    parent = guid(data["ParentProcessGuid"])
                    enqueue(child)
                    if key == "seed" and data.get("ParentProcessId") == PID:
                        enqueue(parent)
                result["decoded"].append({"raw_sha256": raw["sha256"], "event": event})
            except (ValueError, TypeError, KeyError) as exc:
                result["decoded"].append({"raw_sha256": raw.get("sha256"), "status": "REFUSED_DECODING", "reason": str(exc)[:256]})
        queries.append(result)
        return result

    seed = capture("seed", [1], START, END)
    while pending and len(seen_guids) < MAX_GUIDS:
        current = pending.pop(0)
        seen_guids[current.casefold()] = current
        capture("guid", [1, 5], START, cutoff, current)
    for key, event_id in (("service", 4), ("config", 16), ("error", 255)):
        capture(key, [event_id], START, cutoff, cap=4)
    for key, reverse in (("oldest", False), ("newest", True)):
        capture(key, [1, 4, 5, 16, 255], "1970-01-01T00:00:00Z", cutoff, cap=1, reverse=reverse)
    candidates = []
    for row in seed["decoded"]:
        event = row.get("event")
        if event:
            command = event["data"].get("CommandLine", "")
            candidates.append({"raw_sha256": row["raw_sha256"], "pid_match": event["data"].get("ProcessId") == PID,
                               "parent_pid_match": event["data"].get("ParentProcessId") == PID,
                               "script_match": SCRIPT.casefold() in command.casefold(),
                               "request_hash_match": REQUEST.casefold() in command.casefold()})
    return {"schema": "cho51_p3_sysmon_candidate_capture_v7", "status": "UNRESOLVED", "cutoff_utc": cutoff,
            "queries": queries, "candidates": candidates, "followed_guids": sorted(seen_guids.values()), "raw_bytes": total_bytes,
            "guid_limit_hit": guid_limit_hit, "native_health": backend.health(), "historical_custody_closed": False, "historical_operation_released": False,
            "historical_retry_allowed": False, "host_association_authenticated": False, "restart_qualified": False,
            "boundary_qualified": False, "launch_authorized": False, "scientific_admission": False,
            "limitations": ["PID and command matches are candidates, not process-generation or host proof",
                            "Selected query exhaustion does not establish complete descendant coverage or log integrity",
                            "Absence, truncation, errors and service records do not prove cleanup or a restart"]}


