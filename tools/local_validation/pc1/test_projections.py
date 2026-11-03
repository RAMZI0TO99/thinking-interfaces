"""Held source tests for projection grammar; not executed by this change."""
import unittest
from .common import Refusal
from .parsers import parse_binding, parse_ingress, parse_capture
from .fixtures import binding, ingress, capture, encode

class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.b = binding(); self.raw = encode(self.b); self.i = ingress(self.raw); self.c = capture(self.raw)
    def bad(self, parser, obj):
        with self.assertRaises(Refusal): parser(encode(obj))
    def test_valid_binding(self): self.assertIsInstance(parse_binding(self.raw), tuple)
    def test_valid_ingress(self): self.assertIsInstance(parse_ingress(encode(self.i)), tuple)
    def test_valid_capture(self): self.assertIsInstance(parse_capture(encode(self.c)), tuple)
    def test_bytes_exact_type(self):
        with self.assertRaises(Refusal): parse_binding(bytearray(self.raw))
    def test_cap(self):
        with self.assertRaises(Refusal): parse_binding(b" " * 8193)
    def test_ascii(self):
        with self.assertRaises(Refusal): parse_binding(b"\xff")
    def test_missing_lf(self):
        with self.assertRaises(Refusal): parse_binding(self.raw[:-1])
    def test_extra_lf(self):
        with self.assertRaises(Refusal): parse_binding(self.raw + b"\n")
    def test_duplicate(self):
        with self.assertRaises(Refusal): parse_binding(b'{"a":1,"a":2}\n')
    def test_noncanonical_spaces(self):
        with self.assertRaises(Refusal): parse_binding(b'{ "a":1}\n')
    def test_float(self):
        with self.assertRaises(Refusal): parse_binding(b'{"a":1.0}\n')
    def test_nan(self):
        with self.assertRaises(Refusal): parse_binding(b'{"a":NaN}\n')
    def test_depth(self):
        with self.assertRaises(Refusal): parse_binding(b"[" * 25 + b"0" + b"]" * 25 + b"\n")
    def test_extra_field(self): self.b["x"] = 0; self.bad(parse_binding, self.b)
    def test_missing_field(self): del self.b["source"]; self.bad(parse_binding, self.b)
    def test_zero_uuid(self): self.b["operation"] = "00000000-0000-0000-0000-000000000000"; self.bad(parse_binding, self.b)
    def test_uuid_case(self): self.b["operation"] = "AAAAAAAA-1111-1111-1111-111111111111"; self.bad(parse_binding, self.b)
    def test_boolean_ordinal(self): self.b["acquired"] = True; self.bad(parse_binding, self.b)
    def test_ordinal_overflow(self): self.b["acquired"] = 65536; self.bad(parse_binding, self.b)
    def test_input_pin_zero(self): self.b["basis"]["bytes"] = 0; self.bad(parse_binding, self.b)
    def test_digest_case(self): self.b["basis"]["sha256"] = "A" * 64; self.bad(parse_binding, self.b)
    def test_witness_cap(self): self.b["native_witness"]["bytes"] = 131073; self.bad(parse_binding, self.b)
    def test_immutable_nested(self):
        facts = parse_binding(self.raw)
        with self.assertRaises(TypeError): facts[0] = ("x", 1)
    def test_wrong_schema(self): self.b["schema"] = "other"; self.bad(parse_binding, self.b)
    def test_bytes_subclass_no_callbacks(self):
        class Hostile(bytes):
            def __repr__(self): raise AssertionError("repr called")
            def __str__(self): raise AssertionError("str called")
            def __len__(self): raise AssertionError("len called")
        with self.assertRaises(Refusal): parse_binding(Hostile(self.raw))
    def test_bounded_integer_token(self):
        with self.assertRaises(Refusal) as caught: parse_binding(b'{"x":12345678}\n')
        self.assertEqual(caught.exception.code, "NUMBER")
    def test_unexpected_json_value_error(self):
        from unittest.mock import patch
        with patch("tools.local_validation.pc1.common.json.loads", side_effect=ValueError("bug")):
            with self.assertRaises(ValueError): parse_binding(self.raw)
    def test_unexpected_json_interrupt(self):
        from unittest.mock import patch
        with patch("tools.local_validation.pc1.common.json.loads", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt): parse_binding(self.raw)
