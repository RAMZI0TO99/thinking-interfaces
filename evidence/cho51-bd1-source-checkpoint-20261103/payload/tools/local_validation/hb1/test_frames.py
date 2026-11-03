"""Unexecuted supplied-data cases. None establish provider or native evidence."""

from dataclasses import FrozenInstanceError
import hashlib
import json
import struct
import unittest

from .common import Refusal
from .frames import parse_request, parse_response, qpc_text


SESSION = "11111111-1111-4111-8111-111111111111"
OPERATION = "22222222-2222-4222-8222-222222222222"
REQUEST = "33333333-3333-4333-8333-333333333333"
OTHER = "44444444-4444-4444-8444-444444444444"
AUTHORITY = "a" * 64


def guard():
    return True


def encode(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def frame(*, method="claim_operation", direction="request", status=None,
          header_change=None, body=None, raw_payload=None, padded_header=None):
    if raw_payload is None:
        if body is None:
            body = ({"operation_id": OPERATION,
                     "authority_pin": {"bytes": 10, "sha256": AUTHORITY}}
                    if method == "claim_operation" else
                    {"reviewer": "independent_peer", "message_id": "message_1"}
                    if method == "peer_message" else {"operation_id": OPERATION})
        raw_payload = encode(body)
    header = {
        "schema": "cho51_hb1_exchange_v1", "session_id": SESSION,
        "provider_epoch": "epoch_1", "operation_id": OPERATION,
        "authority_sha256": AUTHORITY, "request_id": REQUEST, "sequence": 1,
        "method": method, "direction": direction,
        "status": status or ("REQUEST" if direction == "request" else "OK"),
        "payload_bytes": len(raw_payload),
        "payload_sha256": hashlib.sha256(raw_payload).hexdigest(),
        "clock_domain": "clock_1", "deadline_qpc": "200",
    }
    if header_change:
        header.update(header_change)
    raw_header = encode(header)
    if padded_header is not None:
        raw_header = raw_header + b" " * (padded_header - len(raw_header))
    return struct.pack("<II", len(raw_header), len(raw_payload)) + raw_header + raw_payload


def rewritten_header(raw, transform):
    length, payload_length = struct.unpack("<II", raw[:8])
    changed = transform(raw[8:8 + length])
    return struct.pack("<II", len(changed), payload_length) + changed + raw[8 + length:]


class HB1FrameTests(unittest.TestCase):
    def request(self, raw, **kwargs):
        options = {"check": guard, "now_qpc": "100", "clock_domain": "clock_1"}
        options.update(kwargs)
        return parse_request(raw, **options)

    def response(self, raw, request=None, **kwargs):
        options = {"check": guard, "now_qpc": "100", "clock_domain": "clock_1"}
        options.update(kwargs)
        return parse_response(raw, frame() if request is None else request, **options)

    def test_three_closed_request_shapes(self):
        for method in ("claim_operation", "peer_message", "operation_artifacts"):
            result = self.request(frame(method=method))
            self.assertEqual(result.header["method"], method)
            self.assertEqual(result.authentication, "UNAUTHENTICATED")
            self.assertFalse(result.authenticated)

    def test_exact_maximum_request_little_endian(self):
        payload = encode({"operation_id": OPERATION})
        payload += b" " * (4096 - len(payload))
        raw = frame(method="operation_artifacts", raw_payload=payload, padded_header=4088)
        self.assertEqual(raw[:8], b"\xf8\x0f\x00\x00\x00\x10\x00\x00")
        self.assertEqual(len(raw), 8192)
        self.assertEqual(self.request(raw).payload, payload)

    def test_exact_maximum_response(self):
        request = frame(method="peer_message")
        raw = frame(method="peer_message", direction="response", raw_payload=b"x" * 131072,
                    padded_header=4088)
        self.assertEqual(len(raw), 135168)
        self.assertEqual(len(self.response(raw, request).payload), 131072)

    def test_torn_prefix_all_lengths(self):
        for length in range(8):
            with self.assertRaises(Refusal):
                self.request(frame()[:length])

    def test_zero_header_refuses(self):
        with self.assertRaises(Refusal):
            self.request(struct.pack("<II", 0, 0))

    def test_header_cap_refuses(self):
        raw = frame(padded_header=4089)
        with self.assertRaises(Refusal):
            self.request(raw)

    def test_request_payload_cap_refuses(self):
        with self.assertRaises(Refusal):
            self.request(frame(raw_payload=b" " * 4097))

    def test_response_payload_cap_refuses(self):
        with self.assertRaises(Refusal):
            self.response(frame(direction="response", raw_payload=b" " * 131073))

    def test_unchecked_uint32_lengths_refuse(self):
        for h, p in ((4294967295, 0), (1, 4294967295), (4294967295, 4294967295)):
            with self.assertRaises(Refusal):
                self.request(struct.pack("<II", h, p))

    def test_truncated_body_and_extra_tail_refuse(self):
        raw = frame()
        for broken in (raw[:-1], raw + b"\x00", raw + raw):
            with self.assertRaises(Refusal):
                self.request(broken)

    def test_prefix_and_header_payload_length_agree(self):
        for value in (0, True, "10", -1):
            with self.assertRaises(Refusal):
                self.request(frame(header_change={"payload_bytes": value}))

    def test_checksum_covers_exact_payload(self):
        raw = frame()
        with self.assertRaises(Refusal):
            self.request(raw[:-1] + b" ")

    def test_duplicate_header_key_refuses(self):
        raw = rewritten_header(frame(), lambda h: h[:-1] + b',"sequence":1}')
        with self.assertRaises(Refusal):
            self.request(raw)

    def test_unknown_and_missing_header_fields_refuse(self):
        for mutation in (lambda h: h[:-1] + b',"trusted":true}',
                         lambda h: h.replace(b'"sequence":1,', b"")):
            with self.assertRaises(Refusal):
                self.request(rewritten_header(frame(), mutation))

    def test_invalid_header_utf8_refuses(self):
        with self.assertRaises(Refusal):
            self.request(rewritten_header(frame(), lambda h: h.replace(b"epoch_1", b"\xffpoch_1")))

    def test_header_surrogate_refuses(self):
        with self.assertRaises(Refusal):
            self.request(frame(header_change={"provider_epoch": "\ud800"}))

    def test_header_json_root_and_trailing_data_refuse(self):
        for changed in (b"[]", b"null", b"{} {}", b"{"):
            with self.assertRaises(Refusal):
                self.request(rewritten_header(frame(), lambda h, changed=changed: changed))

    def test_sequence_exact_integer_range(self):
        for value in (True, False, 0, 4097, 1.0, "1"):
            with self.assertRaises(Refusal):
                self.request(frame(header_change={"sequence": value}))
        self.assertEqual(self.request(frame(header_change={"sequence": 4096})).header["sequence"], 4096)

    def test_uuid_canonical_nonzero(self):
        bad_values = ("00000000-0000-0000-0000-000000000000",
                      "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA", "not_uuid", 1)
        for field in ("session_id", "operation_id", "request_id"):
            for value in bad_values:
                with self.assertRaises(Refusal):
                    self.request(frame(header_change={field: value}))

    def test_opaque_tokens_are_bounded_ascii(self):
        for field in ("provider_epoch", "clock_domain"):
            for value in ("", "x" * 129, "with space", "\u00e9", True):
                with self.assertRaises(Refusal):
                    self.request(frame(header_change={field: value}))

    def test_hash_fields_are_exact_lower_hex(self):
        for field in ("authority_sha256", "payload_sha256"):
            for value in ("A" * 64, "g" * 64, "a" * 63, 0):
                with self.assertRaises(Refusal):
                    self.request(frame(header_change={field: value}))

    def test_method_direction_status_are_closed(self):
        for field, value in (("schema", "other"), ("method", "connect"),
                             ("direction", "response"), ("status", "OK"), ("status", True)):
            with self.assertRaises(Refusal):
                self.request(frame(header_change={field: value}))

    def test_qpc_is_canonical_unsigned64_text(self):
        self.assertEqual(qpc_text("18446744073709551615"), 18446744073709551615)
        for value in ("", "00", "01", "+1", "-1", "1.0", "\u0661", "18446744073709551616", 1, True):
            with self.assertRaises(Refusal):
                qpc_text(value)

    def test_supplied_clock_equality_and_domain_refuse(self):
        for options in ({"now_qpc": "200"}, {"now_qpc": "201"}, {"clock_domain": "other_clock"}):
            with self.assertRaises(Refusal):
                self.request(frame(), **options)

    def test_method_request_shapes_reject_unknown_fields(self):
        for method in ("claim_operation", "peer_message", "operation_artifacts"):
            with self.assertRaises(Refusal):
                self.request(frame(method=method, body={"operation_id": OPERATION, "trusted": True}))

    def test_claim_pin_and_operation_joins(self):
        for pin in ({"bytes": True, "sha256": AUTHORITY}, {"bytes": 0, "sha256": AUTHORITY},
                    {"bytes": 1048577, "sha256": AUTHORITY}, {"bytes": 10, "sha256": "b" * 64},
                    {"bytes": 10, "sha256": AUTHORITY, "trusted": True}):
            with self.assertRaises(Refusal):
                self.request(frame(body={"operation_id": OPERATION, "authority_pin": pin}))
        with self.assertRaises(Refusal):
            self.request(frame(body={"operation_id": OTHER,
                                     "authority_pin": {"bytes": 10, "sha256": AUTHORITY}}))

    def test_census_operation_and_peer_tokens(self):
        with self.assertRaises(Refusal):
            self.request(frame(method="operation_artifacts", body={"operation_id": OTHER}))
        for body in ({"reviewer": "x", "message_id": ""}, {"reviewer": "x" * 129, "message_id": "m"}):
            with self.assertRaises(Refusal):
                self.request(frame(method="peer_message", body=body))

    def test_request_json_bounds_and_duplicate_keys(self):
        for raw in (b'{"operation_id":"x","operation_id":"y"}', b"NaN", b"[]", b"\xff",
                    b"[" * 25 + b"0" + b"]" * 25):
            with self.assertRaises(Refusal):
                self.request(frame(raw_payload=raw))

    def test_every_response_join_is_exact(self):
        changed = {"session_id": OTHER, "provider_epoch": "other_epoch", "operation_id": OTHER,
                   "authority_sha256": "b" * 64, "request_id": OTHER, "sequence": 2,
                   "method": "operation_artifacts", "clock_domain": "other_clock", "deadline_qpc": "201"}
        for key, value in changed.items():
            with self.assertRaises(Refusal):
                self.response(frame(direction="response", body={}, header_change={key: value}))

    def test_refusal_payload_is_closed_and_preserved(self):
        payload = {"reason": "CLAIM_UNKNOWN", "detail": "No durable witness."}
        result = self.response(frame(direction="response", status="REFUSED", body=payload))
        self.assertEqual(result.body_kind, "REFUSED_DATA")
        self.assertEqual(result.payload, encode(payload))
        self.assertEqual(result.header["status"], "REFUSED")
        for bad in ({"reason": "SUCCESS", "detail": ""}, {"reason": "UNAVAILABLE", "detail": "x" * 513},
                    {"reason": "UNAVAILABLE", "detail": "", "trusted": True}, {"reason": "UNAVAILABLE"}):
            with self.assertRaises(Refusal):
                self.response(frame(direction="response", status="REFUSED", body=bad))

    def test_forged_positive_evidence_never_authenticates(self):
        result = self.response(frame(direction="response", body={"trusted": True, "claim": "CONSUMED_METADATA_ONLY"}))
        self.assertEqual(result.authentication, "UNAUTHENTICATED")
        self.assertEqual(result.provider_schema, "UNAVAILABLE")
        self.assertEqual(result.body_kind, "PROVIDER_SCHEMA_UNAVAILABLE")
        self.assertFalse(result.authenticated)
        self.assertFalse(hasattr(result, "claim_operation"))

    def test_peer_original_bytes_are_not_reencoded(self):
        payload = b' { "message" : "e\xcc\x81\\u00e9" }\r\n'
        request = frame(method="peer_message")
        result = self.response(frame(method="peer_message", direction="response", raw_payload=payload), request)
        self.assertEqual(result.payload, payload)
        self.assertEqual(result.body_kind, "ORIGINAL_UNAUTHENTICATED_PEER_BYTES")

    def test_peer_invalid_utf8_refuses(self):
        for payload in (b"", b"\xed\xa0\x80"):
            with self.assertRaises(Refusal):
                self.response(frame(method="peer_message", direction="response", raw_payload=payload),
                              frame(method="peer_message"))

    def test_results_are_frozen_and_header_is_defensive(self):
        result = self.request(frame())
        changed = result.header
        changed["status"] = "OK"
        self.assertEqual(result.header["status"], "REQUEST")
        with self.assertRaises(FrozenInstanceError):
            result.payload = b"changed"
        with self.assertRaises(FrozenInstanceError):
            result._header_items = ()

    def test_exact_bytes_and_explicit_guard_required(self):
        for raw in (bytearray(frame()), memoryview(frame()), "text"):
            with self.assertRaises(Refusal):
                self.request(raw)
        for check in (None, lambda: 1, lambda: False):
            with self.assertRaises(Refusal):
                self.request(frame(), check=check)

    def test_checkpoint_refusal_never_returns_partial_result(self):
        calls = []
        def stopping():
            calls.append(True)
            return len(calls) < 5
        with self.assertRaises(Refusal):
            self.request(frame(), check=stopping)
        self.assertEqual(len(calls), 5)

    def test_response_never_trusts_a_parsed_request_object(self):
        with self.assertRaises(Refusal):
            self.response(frame(direction="response", body={}), self.request(frame()))

    def test_claim_and_census_positive_json_stays_schema_unavailable(self):
        for method in ("claim_operation", "operation_artifacts"):
            request = frame(method=method)
            result = self.response(frame(method=method, direction="response", body={}), request)
            self.assertEqual(result.body_kind, "PROVIDER_SCHEMA_UNAVAILABLE")
            for raw in (b"[]", b"null", b'{"x":1,"x":2}', b'{"x":1.0}'):
                with self.assertRaises(Refusal):
                    self.response(frame(method=method, direction="response", raw_payload=raw), request)
