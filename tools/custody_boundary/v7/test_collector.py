"""Fake-only focused tests; reviewed runner decides whether execution is admitted."""
import hashlib
import importlib.util
from pathlib import Path
import unittest
import ctypes
import time
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

c = load("sysmon_v7", HERE / "collector.py")
d = load("decoder_v5", ROOT / "v5" / "decoder.py")
frozen = load("native_v4", ROOT / "v4" / "collector.py")
G = "{12345678-1234-1234-1234-123456789ABC}"
CUTOFF = "2026-10-28T00:00:00Z"

def row(pid="302124", parent="1", process_guid=G, parent_guid=G, command="example", provider=c.PROVIDER, channel=c.CHANNEL, extra=""):
    xml = (f'<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event"><System>'
           f'<Provider Name="{provider}"/><EventID>1</EventID><Version>5</Version>'
           f'<TimeCreated SystemTime="2026-10-27T17:05:00Z"/><EventRecordID>1</EventRecordID>'
           f'<Channel>{channel}</Channel><Computer>host</Computer></System><EventData>'
           f'<Data Name="ProcessId">{pid}</Data><Data Name="ParentProcessId">{parent}</Data>'
           f'<Data Name="ProcessGuid">{process_guid}</Data><Data Name="ParentProcessGuid">{parent_guid}</Data>'
           f'<Data Name="CommandLine">{command}</Data>{extra}</EventData></Event>')
    data = xml.encode()
    return {"xml": xml, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

class Fake:
    def __init__(self, rows=None, error=None):
        self.rows, self.error, self.calls = rows or {}, error, []
    def query(self, info, xpath, cap, reverse):
        self.calls.append((info, xpath, cap, reverse))
        rows = self.rows.get(info["key"], [])
        return {"spec": info, "xpath": xpath, "reverse_direction": reverse, "events": rows[:cap],
                "selected_query_exhausted": not self.error and len(rows) <= cap,
                "truncated": len(rows) > cap, "errors": [self.error] if self.error else []}
    def health(self):
        return {"opened": 1, "closed": 0, "close_errors": ["EvtClose:5"], "closed_cleanly": False}

def run(fake):
    return c.run(None, d, native=fake, cutoff=CUTOFF)

class CollectorTests(unittest.TestCase):
    def test_empty_and_access_denied_preserved(self):
        for error in (None, "OSError:5"):
            out = run(Fake(error=error))
            self.assertEqual(out["status"], "UNRESOLVED")
            self.assertEqual(out["queries"][0]["errors"], [error] if error else [])
            self.assertFalse(out["native_health"]["closed_cleanly"])
            self.assertFalse(out["launch_authorized"])
    def test_candidate_and_guid_followup(self):
        raw = row(command=c.SCRIPT + " -RequestSha256 " + c.REQUEST)
        out = run(Fake({"seed": [raw], "guid": [raw]}))
        self.assertTrue(out["candidates"][0]["script_match"])
        self.assertTrue(out["candidates"][0]["request_hash_match"])
        self.assertEqual(out["followed_guids"], [G])
        self.assertFalse(out["historical_custody_closed"])
    def test_malformed_duplicate_and_scope_mismatch_refused(self):
        for raw in (row(extra='<Data Name="processid">1</Data>'), row(provider="other"), row(pid="2", parent="3"), row(process_guid="bad")):
            out = run(Fake({"seed": [raw]}))
            self.assertEqual(out["queries"][0]["decoded"][0]["status"], "REFUSED_DECODING")
            self.assertEqual(out["followed_guids"], [])
    def test_guid_link_mismatch_refused(self):
        other = "{AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA}"
        out = run(Fake({"seed": [row()], "guid": [row(process_guid=other, parent_guid=other)]}))
        self.assertEqual(out["queries"][1]["decoded"][0]["status"], "REFUSED_DECODING")
    def test_guid_xpath_preserves_observed_case(self):
        for observed in (G, G.lower()):
            fake = Fake({"seed": [row(process_guid=observed)]})
            run(fake)
            self.assertIn("='" + observed + "'", fake.calls[1][1])
    def test_injection_and_scope_refused(self):
        for bad in ("x' or 1=1", "{12345678-1234-1234-1234-123456789ABC}'"):
            with self.assertRaises(ValueError): c.spec("guid", [1, 5], c.START, CUTOFF, bad)
        with self.assertRaises(ValueError): c.spec("service", [4], c.START, CUTOFF + "' or 1=1")
        with self.assertRaises(ValueError): c.spec("service", [5], c.START, CUTOFF)
    def test_caps_sentinels_and_direction(self):
        fake = Fake({"seed": [row()] * 17})
        out = run(fake)
        self.assertTrue(out["queries"][0]["truncated"])
        self.assertEqual(fake.calls[0][2], 16)
        self.assertEqual([x[2] for x in fake.calls[-5:]], [4, 4, 4, 1, 1])
        self.assertFalse(fake.calls[-2][3])
        self.assertTrue(fake.calls[-1][3])
    def test_hash_pin_refused(self):
        raw = row(); raw["sha256"] = "0" * 64
        out = run(Fake({"seed": [raw]}))
        self.assertEqual(out["queries"][0]["decoded"][0]["status"], "REFUSED_DECODING")

    def test_matching_parent_guid_followed_and_case_deduplicated(self):
        parent = "{AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA}"
        out = run(Fake({"seed": [row(pid="42", parent=c.PID, parent_guid=parent), row(process_guid=G.lower())]}))
        self.assertEqual(set(out["followed_guids"]), {G, parent})

    def test_guid_budget_is_reported(self):
        rows = [row(process_guid="{%08x-1234-1234-1234-123456789abc}" % i) for i in range(10)]
        out = run(Fake({"seed": rows}))
        self.assertEqual(len(out["followed_guids"]), 8)
        self.assertTrue(out["guid_limit_hit"])


class NativeQueryTests(unittest.TestCase):
    def backend(self, count=0, *, next_error=259, query_error=False, failed_next=False, close_fail=None):
        n = frozen.Native.__new__(frozen.Native)
        n.deadline = time.monotonic() + 20
        n.close_errors = []
        n.opened = n.closed = n.event_bytes = n.template_bytes = 0
        closed, issued, flags_seen = [], [], []
        def query(session, channel, xpath, flags):
            self.assertIsNone(session)
            self.assertEqual(channel, c.CHANNEL)
            flags_seen.append(flags)
            if query_error:
                ctypes.set_last_error(5)
                return None
            return 100
        def next_event(query_handle, size, handles, timeout, flags, returned):
            self.assertEqual((query_handle, size, timeout, flags), (100, 1, 250, 0))
            if len(issued) < count:
                handle = 200 + len(issued)
                issued.append(handle)
                handles[0] = handle
                ctypes.cast(returned, ctypes.POINTER(frozen.w.DWORD)).contents.value = 1
                if failed_next:
                    ctypes.set_last_error(13)
                    return False
                return True
            ctypes.set_last_error(next_error)
            return False
        def close(handle):
            closed.append(handle)
            if handle == close_fail:
                ctypes.set_last_error(6)
                return False
            return True
        n.dll = types.SimpleNamespace(EvtQuery=query, EvtNext=next_event, EvtClose=close)
        n.render = lambda _: frozen.raw_record("<Event/>")
        backend = c.NativeQuery.__new__(c.NativeQuery)
        backend.n, backend.frozen = n, frozen
        return backend, closed, issued, flags_seen

    def call(self, backend, cap=16, reverse=True):
        info, xpath = c.spec("seed", [1], c.START, c.END)
        return backend.query(info, xpath, cap, reverse)

    def test_empty_and_direction_flags(self):
        for reverse, expected in ((True, 0x201), (False, 0x101)):
            backend, closed, _, flags = self.backend()
            result = self.call(backend, reverse=reverse)
            self.assertTrue(result["selected_query_exhausted"])
            self.assertEqual((closed, flags), ([100], [expected]))
            self.assertTrue(backend.health()["closed_cleanly"])

    def test_sentinel_closed_at_each_cap(self):
        for cap in (1, 4, 16):
            backend, closed, issued, _ = self.backend(cap + 1)
            result = self.call(backend, cap)
            self.assertEqual(len(result["events"]), cap)
            self.assertTrue(result["truncated"])
            self.assertFalse(result["selected_query_exhausted"])
            self.assertEqual(closed, issued + [100])

    def test_failed_next_with_handle_and_timeout_are_not_exhaustion(self):
        for options in ({"count": 1, "failed_next": True}, {"next_error": 1460}):
            backend, closed, issued, _ = self.backend(**options)
            result = self.call(backend)
            self.assertTrue(result["errors"])
            self.assertFalse(result["selected_query_exhausted"])
            self.assertEqual(closed, issued + [100])
            self.assertTrue(backend.health()["closed_cleanly"])

    def test_permission_denial_and_deadline_do_not_claim_absence(self):
        for denied in (True, False):
            backend, closed, _, _ = self.backend(query_error=denied)
            if not denied:
                backend.n.deadline = time.monotonic() - 1
            result = self.call(backend)
            self.assertTrue(result["errors"])
            self.assertFalse(result["selected_query_exhausted"])
            self.assertEqual(closed, [])

    def test_render_failure_and_byte_cap_close_event_and_query(self):
        for render_failure in (True, False):
            backend, closed, issued, _ = self.backend(1)
            if render_failure:
                backend.n.render = lambda _: (_ for _ in ()).throw(ValueError("allocation refused"))
            else:
                backend.n.event_bytes = c.MAX_BYTES
            result = self.call(backend)
            self.assertEqual(result["events"], [])
            self.assertEqual(bool(result["errors"]), render_failure)
            self.assertEqual(result["truncated"], not render_failure)
            self.assertEqual(closed, issued + [100])

    def test_close_failure_stays_sticky(self):
        for failed in (100, 200):
            backend, closed, _, _ = self.backend(1, close_fail=failed)
            self.call(backend)
            self.assertEqual(closed, [200, 100])
            self.assertFalse(backend.health()["closed_cleanly"])
            self.assertTrue(backend.health()["close_errors"])

if __name__ == "__main__":
    unittest.main()
