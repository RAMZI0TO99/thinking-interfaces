"""Supplied-data cases only; source-listed, not executed or admitted."""
import unittest

from .common import Refusal, bounded_bytes, digest, strict_json


def yes():
    return True


class CommonTests(unittest.TestCase):
    def test_round_trip_exact_types(self):
        value = {"a": [None, True, False, -(2**63), 2**63 - 1, "\U0001f642"]}
        self.assertEqual(strict_json(bounded_bytes(value, 4096, yes), 4096, yes), value)

    def test_duplicate_keys_refuse(self):
        with self.assertRaises(Refusal):
            strict_json(b'{"a":1,"a":2}', 4096, yes)

    def test_floats_and_nonfinite_refuse(self):
        for raw in (b"1.0", b"NaN", b"Infinity", b"1e2"):
            with self.subTest(raw=raw), self.assertRaises(Refusal):
                strict_json(raw, 4096, yes)

    def test_integer_overflow_refuses(self):
        for number in (2**63, -(2**63) - 1, 10**100):
            with self.subTest(number=number), self.assertRaises(Refusal):
                strict_json(str(number).encode(), 4096, yes)

    def test_unicode_surrogate_and_invalid_utf8_refuse(self):
        for raw in (b'"\\ud800"', b'"\xff"'):
            with self.subTest(raw=raw), self.assertRaises(Refusal):
                strict_json(raw, 4096, yes)

    def test_depth_boundary(self):
        self.assertEqual(len(strict_json(b"[" * 24 + b"0" + b"]" * 24, 4096, yes)), 1)
        with self.assertRaises(Refusal):
            strict_json(b"[" * 25 + b"0" + b"]" * 25, 4096, yes)

    def test_container_boundary(self):
        raw = b"[" + b",".join([b"0"] * 4096) + b"]"
        self.assertEqual(len(strict_json(raw, 16384, yes)), 4096)
        with self.assertRaises(Refusal):
            strict_json(raw[:-1] + b",0]", 16384, yes)

    def test_cycles_and_custom_types_refuse(self):
        cycle = []
        cycle.append(cycle)
        for value in (cycle, {1: "bad"}, object(), 0.1):
            with self.subTest(kind=type(value)), self.assertRaises(Refusal):
                bounded_bytes(value, 4096, yes)

    def test_encoding_cap_includes_escape_and_newline(self):
        self.assertEqual(bounded_bytes("\x00", 9, yes), b'"\\u0000"\n')
        with self.assertRaises(Refusal):
            bounded_bytes("\x00", 8, yes)

    def test_checkpoint_exact_true(self):
        for callback in (lambda: 1, lambda: False, None):
            with self.subTest(callback=callback), self.assertRaises(Refusal):
                bounded_bytes({}, 4096, callback)

    def test_mutation_during_encoding_stays_bounded(self):
        child = []
        supplied = [child]
        calls = 0
        def mutate():
            nonlocal calls
            calls += 1
            if calls == 2:
                child.append(child)
            return True
        with self.assertRaises(Refusal):
            bounded_bytes(supplied, 4096, mutate)

    def test_hash_checkpoints_and_immutable_input(self):
        calls = []
        self.assertEqual(len(digest(b"a" * 131072, lambda: calls.append(1) or True)), 64)
        self.assertGreaterEqual(len(calls), 6)
        with self.assertRaises(Refusal):
            digest(bytearray(b"a"), yes)

    def test_graph_node_bound(self):
        value = [[0] * 4096 for _ in range(25)]
        with self.assertRaises(Refusal):
            bounded_bytes(value, 1048576, yes)
