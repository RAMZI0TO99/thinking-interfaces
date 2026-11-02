"""Injected native-surface controls; these tests query no Windows provider."""
import ctypes
import importlib.util
import json
from pathlib import Path
import time
import types
import unittest
from unittest import mock
import uuid

HERE = Path(__file__).parent
def load(name):
    spec = importlib.util.spec_from_file_location("_v4_control_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
collector, decoder = load("collector"), load("decoder")


class CollectorControls(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((HERE / "provider-plan.json").read_bytes())
        self.spec, self.xpath = collector.query_spec(self.plan["families"][0], self.plan, "2026-10-28T20:00:00Z", decoder)

    def native(self, count=0, *, error=259, query_error=False, next_bad=False, close_fail=None):
        native = collector.Native.__new__(collector.Native)
        native.deadline = time.monotonic() + 20
        native.close_errors = []
        native.opened = native.closed = native.event_bytes = native.template_bytes = 0
        closed, issued = [], []
        def query(*_):
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
                ctypes.cast(returned, ctypes.POINTER(collector.w.DWORD)).contents.value = 1
                if next_bad:
                    ctypes.set_last_error(13)
                    return False
                return True
            ctypes.set_last_error(error)
            return False
        def close(handle):
            closed.append(handle)
            if handle == close_fail:
                ctypes.set_last_error(6)
                return False
            return True
        native.dll = types.SimpleNamespace(EvtQuery=query, EvtNext=next_event, EvtClose=close)
        native.render = lambda _: collector.raw_record("<Event/>")
        return native, closed, issued

    def test_provider_queries_are_partitioned_and_exclude_hive_noise(self):
        queries = [collector.query_spec(f, self.plan, "2026-10-28T20:00:00Z", decoder) for f in self.plan["families"]]
        self.assertEqual(len({q[0]["key"] for q in queries}), 7)
        general = next(x for s, x in queries if s["key"] == "clock_lifecycle")
        for event_id in (1, 12, 13):
            self.assertIn("EventID=" + str(event_id), general)
        for event_id in (15, 16, 24):
            self.assertNotIn("EventID=" + str(event_id), general)

    def test_historical_query_uses_saved_bounds_and_only_saved_pid(self):
        spec, xpath = collector.query_spec(self.plan["families"][-1], self.plan, "2026-10-28T20:00:00Z", decoder)
        self.assertEqual((spec["from_utc"], spec["to_utc"]), (self.plan["old_entry_utc"], self.plan["old_return_utc"]))
        self.assertIn("EventID=4688", xpath)
        self.assertIn("NewProcessId", xpath)
        self.assertTrue(all(int(x, 16) == 302124 for x in spec["pid_hex_values"]))

    def test_query_refuses_injection_missing_fields_and_wrong_types(self):
        family = self.plan["families"][0]
        samples = [None, [], dict(family, provider="x'] or *["), dict(family, event_ids=[True]),
                   dict(family, event_ids=[]), dict(family, event_ids=[27, 27]), dict(family, extra=True),
                   {k: v for k, v in family.items() if k != "provider"}]
        for sample in samples:
            with self.subTest(sample=sample), self.assertRaises(collector.CaptureError):
                collector.query_spec(sample, self.plan, "2026-10-28T20:00:00Z", decoder)

    def test_query_refuses_clock_reversal_and_wrong_pid(self):
        with self.assertRaises(collector.CaptureError):
            collector.query_spec(self.plan["families"][0], self.plan, "2026-10-26T00:00:00Z", decoder)
        with self.assertRaises(collector.CaptureError):
            collector.query_spec(dict(self.plan["families"][-1], pid_hex_values=["0x1"]), self.plan, "2026-10-28T20:00:00Z", decoder)

    def test_empty_query_exhaustion_closes_only_owned_query(self):
        native, closed, _ = self.native()
        result = native.events(self.spec, self.xpath)
        self.assertTrue(result["selected_query_exhausted"])
        self.assertFalse(result["truncated"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(closed, [100])
        self.assertEqual(native.opened, native.closed)

    def test_cap_consumes_and_closes_sentinel_without_claiming_exhaustion(self):
        native, closed, issued = self.native(17)
        result = native.events(self.spec, self.xpath)
        self.assertEqual(len(result["events"]), 16)
        self.assertEqual(len(issued), 17)
        self.assertTrue(result["truncated"])
        self.assertFalse(result["selected_query_exhausted"])
        self.assertEqual(closed, issued + [100])
        self.assertEqual(native.opened, native.closed)

    def test_security_has_separate_four_row_cap(self):
        native, closed, issued = self.native(5)
        spec, xpath = collector.query_spec(self.plan["families"][-1], self.plan, "2026-10-28T20:00:00Z", decoder)
        result = native.events(spec, xpath)
        self.assertEqual(len(result["events"]), 4)
        self.assertTrue(result["truncated"])
        self.assertEqual(closed, issued + [100])

    def test_timeout_is_visible_and_not_exhaustion(self):
        native, closed, _ = self.native(error=1460)
        result = native.events(self.spec, self.xpath)
        self.assertTrue(result["errors"])
        self.assertFalse(result["selected_query_exhausted"])
        self.assertEqual(closed, [100])

    def test_permission_denial_never_becomes_empty_success(self):
        native, closed, _ = self.native(query_error=True)
        result = native.events(self.spec, self.xpath)
        self.assertTrue(result["errors"])
        self.assertFalse(result["selected_query_exhausted"])
        self.assertEqual(closed, [])

    def test_failed_enumeration_with_returned_handle_still_closes_it(self):
        native, closed, issued = self.native(1, next_bad=True)
        result = native.events(self.spec, self.xpath)
        self.assertTrue(result["errors"])
        self.assertEqual(closed, issued + [100])
        self.assertEqual(native.opened, native.closed)

    def test_render_failure_closes_event_and_query(self):
        native, closed, issued = self.native(1)
        native.render = mock.Mock(side_effect=collector.CaptureError("injected render failure"))
        result = native.events(self.spec, self.xpath)
        self.assertTrue(result["errors"])
        self.assertEqual(closed, issued + [100])

    def test_aggregate_byte_cap_closes_unretained_event(self):
        native, closed, issued = self.native(1)
        native.event_bytes = collector.MAX_EVENT_BYTES
        result = native.events(self.spec, self.xpath)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["events"], [])
        self.assertEqual(closed, issued + [100])

    def test_native_close_failure_stays_visible(self):
        native, closed, _ = self.native(1, close_fail=200)
        result = native.events(self.spec, self.xpath)
        self.assertEqual(closed, [200, 100])
        self.assertTrue(native.close_errors)
        self.assertNotEqual(native.opened, native.closed)
        self.assertTrue(result["selected_query_exhausted"])

    def test_deadline_refuses_before_native_query(self):
        native, closed, _ = self.native()
        native.deadline = time.monotonic() - 1
        result = native.events(self.spec, self.xpath)
        self.assertIn("capture deadline", result["errors"][0])
        self.assertEqual(closed, [])
        self.assertEqual(native.opened, 0)

    def variant(self, kind, payload=b""):
        size = ctypes.sizeof(collector._Variant)
        buffer = ctypes.create_string_buffer(size + len(payload))
        value = collector._Variant.from_buffer(buffer)
        value.type = kind
        if payload:
            value.pointer = ctypes.addressof(buffer) + size
            ctypes.memmove(value.pointer, payload, len(payload))
        return buffer, value

    def test_native_variant_uint32_guid_and_string(self):
        buffer, value = self.variant(8)
        value.unsigned32 = 0xffffffff
        self.assertEqual(collector.decode_variant(buffer, len(buffer), 8), 0xffffffff)
        identity = uuid.UUID("11111111-2222-4333-8444-555555555555")
        buffer, _ = self.variant(15, identity.bytes_le)
        self.assertEqual(collector.decode_variant(buffer, len(buffer), 15), str(identity))
        buffer, _ = self.variant(1, "template\0".encode("utf-16-le"))
        self.assertEqual(collector.decode_variant(buffer, len(buffer), 1), "template")

    def test_native_variant_type_array_and_size_refusal(self):
        buffer, value = self.variant(8)
        for used, kind, count in [(0, 8, 0), (len(buffer)+1, 8, 0), (len(buffer), 129, 0), (len(buffer), 8, 1)]:
            value.type, value.count = kind, count
            with self.subTest(used=used, kind=kind, count=count), self.assertRaises(collector.CaptureError):
                collector.decode_variant(buffer, used, 8)

    def test_native_variant_pointer_refused_before_dereference(self):
        buffer, value = self.variant(1, b"\0\0")
        for pointer in (None, 1, ctypes.addressof(buffer), ctypes.addressof(buffer)+len(buffer)):
            value.pointer = pointer
            with self.subTest(pointer=pointer), self.assertRaises(collector.CaptureError):
                collector.decode_variant(buffer, len(buffer), 1)

    def test_native_variant_unterminated_string_and_short_guid(self):
        for kind, payload in [(1, "x".encode("utf-16-le")), (15, b"x"*14)]:
            buffer, _ = self.variant(kind, payload)
            with self.assertRaises(collector.CaptureError):
                collector.decode_variant(buffer, len(buffer), kind)

    def test_raw_record_utf8_bound_is_not_character_count(self):
        with self.assertRaises(collector.CaptureError):
            collector.raw_record("\u20ac" * (collector.MAX_XML_BYTES // 3 + 1))
        result = collector.raw_record("\u20ac")
        self.assertEqual(result["bytes"], 3)

    def test_metadata_mid_failure_closes_all_acquired_handles(self):
        native, closed, _ = self.native()
        native.dll.EvtOpenPublisherMetadata = lambda *_: 300
        native.dll.EvtOpenEventMetadataEnum = lambda *_: 301
        native.dll.EvtNextEventMetadata = lambda *_: 302
        native.property = lambda handle, index, expected, publisher=False: "11111111-2222-4333-8444-555555555555" if publisher else (_ for _ in ()).throw(collector.CaptureError("injected property failure"))
        result = native.metadata(self.spec)
        self.assertTrue(result["errors"])
        self.assertEqual(closed, [302, 301, 300])
        self.assertEqual(native.opened, native.closed)
