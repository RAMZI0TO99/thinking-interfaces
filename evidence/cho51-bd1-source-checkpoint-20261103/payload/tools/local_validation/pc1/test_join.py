"""Held source tests for state, join and refusal; not executed."""
import unittest
from unittest.mock import patch
from .common import Refusal, raw_pin
from .parsers import parse_ingress, parse_capture
from .joins import join, dispatch
from .refusal import classify
from .fixtures import binding, ingress, capture, encode, O, OTHER

class JoinTests(unittest.TestCase):
    def setUp(self):
        self.b = binding(); self.raw = encode(self.b); self.i = ingress(self.raw); self.c = capture(self.raw)
    def join(self): return join(self.raw, encode(self.i), encode(self.c), O, encode(self.b))
    def bad_i(self):
        with self.assertRaises(Refusal): parse_ingress(encode(self.i))
    def bad_c(self):
        with self.assertRaises(Refusal): parse_capture(encode(self.c))
    def test_join_flags(self):
        r = self.join(); self.assertEqual(r.consistent, "CONSISTENT_SUPPLIED"); self.assertFalse(r.native_authority or r.execution_authorized or r.debt_discharged); self.assertEqual(r.dispatch, "REFUSED")
    def test_result_frozen(self):
        with self.assertRaises(AttributeError): self.join().dispatch = "YES"
    def test_dispatch_refused(self): self.assertEqual(dispatch(), "REFUSED")
    def test_expected_operation(self):
        with self.assertRaises(Refusal): join(self.raw, encode(self.i), encode(self.c), OTHER, self.raw)
    def test_expected_binding(self):
        expected = dict(self.b); expected["acquired"] = 2
        with self.assertRaises(Refusal): join(self.raw, encode(self.i), encode(self.c), O, encode(expected))
    def test_ingress_operation(self):
        self.i["operation"] = OTHER
        with self.assertRaises(Refusal): self.join()
    def test_capture_operation(self):
        self.c["operation"] = OTHER
        with self.assertRaises(Refusal): self.join()
    def test_ingress_alternate_binding(self):
        self.i["binding"]["sha256"] = "b" * 64
        with self.assertRaises(Refusal): self.join()
    def test_capture_alternate_binding(self):
        self.c["binding"]["sha256"] = "b" * 64
        with self.assertRaises(Refusal): self.join()
    def test_pin_without_lf(self):
        self.i["binding"] = raw_pin(self.raw[:-1])
        with self.assertRaises(Refusal): self.join()
    def test_expected_noncanonical(self):
        with self.assertRaises(Refusal): join(self.raw, encode(self.i), encode(self.c), O, self.raw[:-1])
    def test_bound_fault_allowed(self): self.i["first_fault"] = "CUSTODY"; self.join()
    def test_bound_activity(self): self.i["entered"] = self.i["committed"] = 1; self.bad_i()
    def test_bound_events(self): self.i["event_records"] = 1; self.i["events"]["bytes"] = 1; self.bad_i()
    def test_algebra(self): self.i["state"] = "OPEN"; self.i["entered"] = 1; self.bad_i()
    def test_cutoff_independent(self): self.i.update(state="DRAINED", cutoff=42); self.join()
    def test_precutoff_late(self): self.i["late"] = 1; self.bad_i()
    def test_revoked_zero_cutoff(self): self.i["state"] = "REVOKED"; self.bad_i()
    def test_drained_pending(self): self.i.update(state="DRAINED", cutoff=1, entered=1, pending=1); self.bad_i()
    def test_refused_needs_fault(self): self.i.update(state="OPEN", entered=1, refused=1); self.bad_i()
    def test_empty_events_digest(self): self.i["events"]["sha256"] = "a" * 64; self.bad_i()
    def test_empty_stream_digest(self): self.c["stdout"]["sha256"] = "a" * 64; self.bad_c()
    def test_refusal_classification(self): self.assertEqual(classify(b"bad", encode(self.i), encode(self.c), O, self.raw).consistent, "REFUSED_SUPPLIED")
    def test_unexpected_propagates(self):
        with patch("tools.local_validation.pc1.refusal.join", side_effect=MemoryError):
            with self.assertRaises(MemoryError): classify(self.raw, encode(self.i), encode(self.c), O, self.raw)
    def test_complete_missing_eof(self): self.c["stdout_eof"] = False; self.bad_c()
    def test_eof_wrong_type(self): self.c["stderr_eof"] = 1; self.bad_c()
    def test_capture_counter_bool(self): self.c["stdout_chunks"] = True; self.bad_c()
    def test_refused_flags(self):
        r = classify(b"bad", encode(self.i), encode(self.c), O, self.raw)
        self.assertFalse(r.native_authority or r.execution_authorized or r.debt_discharged)
        self.assertEqual(r.dispatch, "REFUSED")
        self.assertEqual(r.consistent, "REFUSED_SUPPLIED")
        with self.assertRaises(AttributeError): r.execution_authorized = True
        with self.assertRaises(AttributeError): r.code = "OTHER"
    def test_result_constructor_rejects_flags(self):
        from .joins import SuppliedResult
        from .refusal import RefusedResult
        with self.assertRaises(TypeError): SuppliedResult(execution_authorized=True)
        with self.assertRaises(TypeError): RefusedResult("JSON", dispatch="YES")
        with self.assertRaises(ValueError): RefusedResult("invented")
    def test_unexpected_value_error_propagates(self):
        with patch("tools.local_validation.pc1.refusal.join", side_effect=ValueError("bug")):
            with self.assertRaises(ValueError): classify(self.raw, encode(self.i), encode(self.c), O, self.raw)
    def test_unexpected_interrupt_propagates(self):
        with patch("tools.local_validation.pc1.refusal.join", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt): classify(self.raw, encode(self.i), encode(self.c), O, self.raw)
    def test_frozen_empty_events_refused(self):
        self.i.update(state="FROZEN", cutoff=1)
        self.bad_i()
    def test_terminal_empty_events_refused(self):
        self.i.update(state="TERMINAL", cutoff=1)
        self.bad_i()
    def test_frozen_nonempty_reference_supplied_only(self):
        self.i.update(state="FROZEN", cutoff=1, event_records=1)
        self.i["events"] = {"bytes": 1, "sha256": "a" * 64}
        r = self.join()
        self.assertEqual(r.consistent, "CONSISTENT_SUPPLIED")
        self.assertFalse(r.native_authority or r.execution_authorized or r.debt_discharged)
        self.assertEqual(r.dispatch, "REFUSED")
    def test_terminal_nonempty_reference_supplied_only(self):
        self.i.update(state="TERMINAL", cutoff=1, event_records=1)
        self.i["events"] = {"bytes": 1, "sha256": "a" * 64}
        r = self.join()
        self.assertEqual(r.consistent, "CONSISTENT_SUPPLIED")
        self.assertFalse(r.native_authority or r.execution_authorized or r.debt_discharged)
        self.assertEqual(r.dispatch, "REFUSED")
