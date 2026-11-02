"""Bounded Windows diagnostic collection; never establishes a custody boundary.

Invoked only by the reviewed child_entry under a new local observation admission.
No process enumeration, restart, service modification, network, or child launch.
"""
from __future__ import annotations

import ctypes
import hashlib
import os
import time
from ctypes import wintypes as w
from datetime import UTC, datetime

MAX_EVENTS = 32
MAX_XML_BYTES = 65536
MAX_TOTAL_XML_BYTES = 524288
MAX_SECONDS = 15
QUERY = ("*[System[(Provider[@Name='Microsoft-Windows-Kernel-Boot'] or "
         "Provider[@Name='Microsoft-Windows-Kernel-General'] or "
         "Provider[@Name='Microsoft-Windows-Power-Troubleshooter'] or "
         "Provider[@Name='EventLog']) and "
         "TimeCreated[@SystemTime>='2026-10-27T17:05:08.2987118Z']]]")


def collect() -> dict:
    if os.name != "nt":
        raise RuntimeError("Windows required")
    # LOAD_LIBRARY_SEARCH_SYSTEM32; do not search the working directory.
    kernel = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
    event = ctypes.WinDLL("wevtapi.dll", use_last_error=True, winmode=0x800)
    kernel.QueryPerformanceCounter.argtypes = [ctypes.POINTER(ctypes.c_longlong)]
    kernel.QueryPerformanceCounter.restype = w.BOOL
    kernel.QueryPerformanceFrequency.argtypes = [ctypes.POINTER(ctypes.c_longlong)]
    kernel.QueryPerformanceFrequency.restype = w.BOOL
    kernel.GetComputerNameExW.argtypes = [ctypes.c_int, w.LPWSTR, ctypes.POINTER(w.DWORD)]
    kernel.GetComputerNameExW.restype = w.BOOL
    kernel.GetTickCount64.argtypes = []
    kernel.GetTickCount64.restype = ctypes.c_ulonglong
    event.EvtQuery.argtypes = [w.HANDLE, w.LPCWSTR, w.LPCWSTR, w.DWORD]
    event.EvtQuery.restype = w.HANDLE
    event.EvtNext.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE), w.DWORD,
                             w.DWORD, ctypes.POINTER(w.DWORD)]
    event.EvtNext.restype = w.BOOL
    event.EvtRender.argtypes = [w.HANDLE, w.HANDLE, w.DWORD, w.DWORD, w.LPVOID,
                               ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD)]
    event.EvtRender.restype = w.BOOL
    event.EvtClose.argtypes = [w.HANDLE]
    event.EvtClose.restype = w.BOOL
    errors: list[str] = []

    def tick() -> int:
        value = ctypes.c_longlong()
        if not kernel.QueryPerformanceCounter(ctypes.byref(value)):
            raise OSError(ctypes.get_last_error(), "QueryPerformanceCounter")
        if not 0 <= value.value <= 9007199254740991:
            raise ValueError("QPC outside lossless contract")
        return value.value

    def close(handle) -> None:
        if handle and not event.EvtClose(handle):
            errors.append("EvtClose:" + str(ctypes.get_last_error()))

    frequency = ctypes.c_longlong()
    if not kernel.QueryPerformanceFrequency(ctypes.byref(frequency)) or not 0 < frequency.value <= 10**12:
        raise RuntimeError("QPC frequency unavailable")
    start_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    start = tick()
    deadline = time.monotonic() + MAX_SECONDS
    name = ctypes.create_unicode_buffer(256)
    size = w.DWORD(256)
    name_sha = None
    if kernel.GetComputerNameExW(4, name, ctypes.byref(size)):  # PhysicalNetBIOS label only
        name_sha = hashlib.sha256(name.value.encode("utf-8")).hexdigest()
    else:
        errors.append("GetComputerNameExW:" + str(ctypes.get_last_error()))
    rows: list[dict] = []
    total = 0
    exhausted = False
    truncated = False
    query = event.EvtQuery(None, "System", QUERY, 0x201)  # channel + reverse direction
    if not query:
        errors.append("EvtQuery:" + str(ctypes.get_last_error()))
    else:
        try:
            for _ in range(MAX_EVENTS + 1):
                if time.monotonic() >= deadline:
                    truncated = True
                    errors.append("collection_deadline")
                    break
                handles = (w.HANDLE * 1)()
                returned = w.DWORD()
                ok = event.EvtNext(query, 1, handles, 250, 0, ctypes.byref(returned))
                if not ok:
                    code = ctypes.get_last_error()
                    exhausted = code == 259  # ERROR_NO_MORE_ITEMS
                    if not exhausted:
                        errors.append("EvtNext:" + str(code))
                    break
                handle = handles[0]
                try:
                    if returned.value != 1 or not handle:
                        raise RuntimeError("EvtNext count/handle mismatch")
                    if len(rows) >= MAX_EVENTS:
                        truncated = True
                        break
                    used, count = w.DWORD(), w.DWORD()
                    ok = event.EvtRender(None, handle, 1, 0, None, ctypes.byref(used), ctypes.byref(count))
                    if ok or ctypes.get_last_error() != 122 or not 2 <= used.value <= MAX_XML_BYTES or used.value % 2:
                        raise RuntimeError("EvtRender required size refused")
                    allocation = used.value
                    xml = ctypes.create_unicode_buffer(allocation // 2)
                    if not event.EvtRender(None, handle, 1, allocation, xml, ctypes.byref(used), ctypes.byref(count)):
                        raise OSError(ctypes.get_last_error(), "EvtRender")
                    if not 2 <= used.value <= allocation or used.value % 2:
                        raise RuntimeError("EvtRender changed size")
                    raw = xml.value.encode("utf-8", errors="strict")
                    if len(raw) > MAX_XML_BYTES or total + len(raw) > MAX_TOTAL_XML_BYTES:
                        truncated = True
                        break
                    rows.append({"xml": raw.decode("utf-8"), "bytes": len(raw),
                                 "sha256": hashlib.sha256(raw).hexdigest()})
                    total += len(raw)
                finally:
                    close(handle)
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(type(exc).__name__ + ":" + str(exc)[:256])
        finally:
            close(query)
    end = tick()
    if end < start:
        raise RuntimeError("QPC reversed")
    return {
        "schema": "cho51_p3_windows_boundary_diagnostic_v1",
        "status": "UNRESOLVED", "boundary_qualified": False,
        "launch_authorized": False, "scientific_admission": False,
        "historical_custody_closed": False, "historical_retry_allowed": False,
        "observed_start_utc": start_utc,
        "observed_end_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "qpc_frequency": frequency.value, "qpc_start": start, "qpc_end": end,
        "tick_count64_ms": kernel.GetTickCount64(),
        "computer_label_sha256": name_sha,
        "provider": "Windows Event Log: EvtQuery/EvtNext/EvtRender",
        "channel": "System", "query": QUERY, "reverse_direction": True,
        "events": rows, "selected_query_exhausted": exhausted,
        "truncated": truncated, "errors": errors,
        "reason_codes": ["HOST_ASSOCIATION_UNESTABLISHED", "PROVIDER_COVERAGE_UNQUALIFIED",
                         "RESTART_KIND_UNESTABLISHED", "CLOCK_ORDER_UNESTABLISHED",
                         "PERSISTED_DOMAIN_UNRESOLVED"],
        "limitations": [
            "Computer label is not host authentication or a boot identity.",
            "Event XML is untrusted diagnostic data, not a full-restart predicate.",
            "Exhausting a selected query does not prove complete retained event history.",
            "No historical event-to-host association or persistent-domain exclusion is supplied.",
            "No cross-boot QPC comparison or historical cleanup inference is permitted.",
        ],
    }
