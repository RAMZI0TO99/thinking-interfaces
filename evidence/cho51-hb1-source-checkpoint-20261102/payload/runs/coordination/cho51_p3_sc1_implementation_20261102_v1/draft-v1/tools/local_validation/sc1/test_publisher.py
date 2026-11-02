"""Unexecuted SC1 pure/fake-backend scenarios. These are not native evidence.

O01-O12 coverage describes assertions in source, not a qualified result. No
production host, Windows API, real output path or runtime launcher is used here.
"""

import copy
import ctypes
import hashlib
import json
import unittest
from unittest import mock

from . import native_backend
from .publisher import (CONFIRMATION_BYTES, FALSES, PHASE, RESERVED_BYTES, ROOT,
                        SLOT_SPECS, SOURCE_REQUIRED, FixedSlotPublisher,
                        PublicationRefusal, digest, encode)


OPERATION = "95a5e3ee-cc9b-4698-9224-28d890707de1"


def checkpoint():
    return True


def packed(value):
    return encode(value, 1048576, checkpoint)


def pin(raw):
    return {"bytes": len(raw), "sha256": digest(raw)}


def identity(index=1):
    return {"schema": "cho51_lv_native_identity_v1", "volume_serial": "0000000000000001",
            "file_id": format(index, "032x"), "volume_kind": "local_fixed", "filesystem": "NTFS"}


class FakeBackend:
    """Trace model only: no claim that simulated facts establish native custody."""

    def __init__(self):
        self.events, self.files, self.identities = [], {}, {}
        self.fail = None
        self.closed = False

    def prepare(self, sources, phase):
        self.events.append(("prepare", phase, copy.deepcopy(sources)))
        if self.fail == "prepare":
            raise RuntimeError("injected preparation failure")

    def require_absent(self, path):
        self.events.append(("absent", path))
        if path in self.files:
            raise ValueError("occupied")

    def verify_inputs(self):
        self.events.append(("inputs",))
        if self.fail == "inputs":
            raise ValueError("changed source")

    def verify_publication(self, reference):
        path = reference["path"]
        self.events.append(("verify", path))
        if pin(self.files[path]) != {key: reference[key] for key in ("bytes", "sha256")}:
            raise ValueError("changed publication bytes")
        if self.identities[path] != reference["native_identity"]:
            raise ValueError("changed native identity")

    def write_new(self, path, raw):
        self.events.append(("create", path))
        if path in self.files:
            raise ValueError("exclusive create occupied")
        self.files[path] = b""
        self.identities[path] = identity(len(self.files))
        self.events.append(("postcreate_facts", path))
        if self.fail == "postcreate":
            raise ValueError("injected postcreate refusal before write")
        self.events.append(("write", path))
        self.files[path] = raw[:1] if self.fail == "short_write" else raw
        if self.fail == "short_write":
            raise ValueError("short write")
        self.events.append(("readback", path))
        if self.fail == "readback":
            raise ValueError("readback mismatch")
        self.events.append(("close_original", path))
        if self.fail == "file_close":
            raise ValueError("original close unknown")
        self.events.append(("close_ancestry", path))
        if self.fail == "ancestry_close":
            raise ValueError("ancestry close unknown")
        return {"path": path, **pin(raw), "native_identity": copy.deepcopy(self.identities[path]),
                "original_file_closed": True, "original_ancestry_closed": True}

    def close(self):
        self.events.append(("close_backend",))
        self.closed = True
        if self.fail in ("cleanup", "file_close", "ancestry_close"):
            raise ValueError("injected cleanup unknown")


class FakeHost:
    """Explicit test capability; never a production identity/admission provider."""

    def __init__(self, backend):
        self.backend = backend
        self.messages, self.claimed, self.extra = {}, set(), []
        self.events = []

    def claim_operation(self, operation, authority_pin):
        self.events.append(("claim", operation))
        if operation in self.claimed:
            raise ValueError("UUID already consumed")
        self.claimed.add(operation)
        return {"operation_id": operation, "authority_sha256": authority_pin["sha256"],
                "publisher": "project_root", "claim": "CONSUMED_METADATA_ONLY"}

    def peer_message(self, reviewer, message_id):
        self.events.append(("peer", reviewer, message_id))
        return self.messages[(reviewer, message_id)]

    def operation_artifacts(self, operation):
        self.events.append(("census", operation))
        return {"operation_id": operation, "paths": sorted(self.backend.files) + list(self.extra)}


def fixture(*, initialize=True, mutate=None, backend=None, host=None, guard=checkpoint):
    backend = backend or FakeBackend()
    host = host or FakeHost(backend)
    sources = {path: pin(("source:" + path).encode("utf-8")) for path in SOURCE_REQUIRED}
    proof = ROOT + "/docs/phase2/cho51_p3_startup_cost_v1/qualification.md"
    authority = {"schema": "cho51_sc1_publication_authority_v1", "operation_id": OPERATION,
                 "publisher": "project_root", "phase": PHASE, "sources": sources,
                 "source_reviewer": "source_peer", "source_message_id": "source_authority",
                 "capture": {"transport": "exact_tool_chunks_utf8_v1", "raw_max_encoded_bytes": 1048576,
                             "external_max_encoded_bytes": 65536, "proof": {"path": proof, **sources[proof]}}}
    if mutate is not None:
        mutate(authority)
    host.messages[(authority["source_reviewer"], "source_authority")] = packed({
        "schema": "cho51_sc1_source_authorization_v1", "reviewer": authority["source_reviewer"],
        "message_id": "source_authority", "authors": ["project_root", "source_worker"],
        "status": "ACCEPTED_SOURCE_ONLY", "sources": authority["sources"],
        "capture": authority["capture"], "phase": authority["phase"]})
    raw = packed(authority)
    publisher = FixedSlotPublisher(raw, pin(raw), host=host, backend=backend, checkpoint=guard)
    if initialize:
        publisher.initialize()
    return publisher, host, backend


def review(publisher, host, role="source_review", reviewer="source_peer", decision=None, text="reviewed text"):
    value = {"schema": "cho51_sc1_peer_review_v1", "operation_id": publisher.operation,
             "role": role, "reviewer": reviewer, "message_id": role + "_message",
             "decision": decision or ("ACCEPTED_SOURCE_ONLY" if role == "source_review" else "ACCEPTED_METADATA_ONLY"),
             "text": text, "text_sha256": digest(text.encode("utf-8"))}
    host.messages[(reviewer, value["message_id"])] = packed(value)
    return publisher.publish_review(role, reviewer, value["message_id"]), value


def confirmation(publisher, host, reference, value, *, confirmed=True, text="exact bytes confirmed", mutate=None):
    message = {"schema": "cho51_sc1_peer_confirmation_v1", "operation_id": publisher.operation,
               "reviewer": value["reviewer"], "message_id": value["role"] + "_confirmation",
               "review_pin": {key: reference[key] for key in ("path", "bytes", "sha256")},
               "review_text_sha256": value["text_sha256"], "confirmed": confirmed, "text": text}
    if mutate is not None:
        mutate(message)
    host.messages[(message["reviewer"], message["message_id"])] = packed(message)
    return message


class PublisherContractTests(unittest.TestCase):
    def assert_consumed(self, publisher, backend):
        state = publisher.snapshot()
        self.assertEqual(state["status"], "FAILED_CONSUMED")
        self.assertEqual((state["reserved_files"], state["reserved_bytes"]), (16, RESERVED_BYTES))
        self.assertIs(state["failed_reservations_released"], False)
        count = len(backend.files)
        with self.assertRaises(PublicationRefusal):
            publisher.publish_record("scope", "no recovery")
        self.assertEqual(len(backend.files), count)

    def test_o01_whole_ledger_and_all_absences_precede_allocation(self):
        publisher, _, backend = fixture()
        first = next(index for index, event in enumerate(backend.events) if event[0] == "create")
        absent = {event[1] for event in backend.events[:first] if event[0] == "absent"}
        self.assertEqual(len(absent), 16)
        path = backend.events[first][1]
        self.assertIn("/allocation_", path)
        ledger = json.loads(backend.files[path])["body"]
        self.assertEqual(ledger["reserved_files"], 16)
        self.assertEqual(ledger["reserved_bytes"], 3293184)
        self.assertEqual({role: item["reserved_bytes"] for role, item in ledger["slots"].items()}, dict(SLOT_SPECS))
        self.assertEqual(len({item["path"] for item in ledger["slots"].values()}), 16)
        self.assertEqual(publisher.snapshot()["status"], "READY")

    def test_o01_bootstrap_faults_consume_full_charge_and_preserve_partial(self):
        for stage in ("prepare", "inputs", "postcreate", "short_write", "readback", "file_close", "ancestry_close"):
            with self.subTest(stage=stage):
                publisher, host, backend = fixture(initialize=False)
                backend.fail = stage
                with self.assertRaises(PublicationRefusal):
                    publisher.initialize()
                self.assertIn(OPERATION, host.claimed)
                self.assertLessEqual(len(backend.files), 1)
                self.assert_consumed(publisher, backend)

    def test_o01_every_later_role_verifies_immutable_ledger(self):
        publisher, _, backend = fixture()
        allocation = next(iter(backend.files))
        backend.events.clear()
        publisher.publish_record("scope", "scoped")
        kinds = [event[0] for event in backend.events]
        self.assertLess(kinds.index("verify"), kinds.index("create"))
        self.assertEqual(next(event[1] for event in backend.events if event[0] == "verify"), allocation)
        backend.files[allocation] += b"changed"
        with self.assertRaises(PublicationRefusal):
            publisher.publish_record("timing_join", "must refuse")
        self.assertEqual(len(backend.files), 2)
        self.assert_consumed(publisher, backend)

    def test_o01_uuid_claim_is_one_use_across_instances(self):
        publisher, host, backend = fixture()
        publisher.close()
        replacement, _, _ = fixture(initialize=False, backend=backend, host=host)
        with self.assertRaises(PublicationRefusal):
            replacement.initialize()
        self.assertEqual(len(backend.files), 1)

    def test_o02_missing_host_capability_refuses_before_create(self):
        class NoCensusHost(FakeHost):
            operation_artifacts = None
        backend = FakeBackend()
        with self.assertRaises(PublicationRefusal):
            fixture(initialize=False, backend=backend, host=NoCensusHost(backend))
        self.assertEqual(backend.files, {})

    def test_o02_exact_authority_peer_message_is_required(self):
        for fault in ("identity", "sources", "self_review", "extra_field"):
            with self.subTest(fault=fault):
                publisher, host, backend = fixture(initialize=False)
                key = ("source_peer", "source_authority")
                message = json.loads(host.messages[key])
                if fault == "identity":
                    message["reviewer"] = "other_peer"
                elif fault == "sources":
                    message["sources"].pop(next(iter(message["sources"])))
                elif fault == "self_review":
                    message["authors"].append("source_peer")
                else:
                    message["runtime_admission"] = True
                host.messages[key] = packed(message)
                with self.assertRaises(PublicationRefusal):
                    publisher.initialize()
                self.assertEqual(backend.files, {})
                self.assert_consumed(publisher, backend)

    def test_o02_author_cannot_review_and_actual_peer_is_distinct(self):
        for role, reviewer in (("source_review", "project_root"), ("source_review", "source_worker"),
                               ("actual_review", "source_peer"), ("actual_review", "source_worker")):
            with self.subTest(role=role, reviewer=reviewer):
                publisher, host, backend = fixture()
                with self.assertRaises(PublicationRefusal):
                    review(publisher, host, role, reviewer)
                self.assertEqual(len(backend.files), 1)
                self.assert_consumed(publisher, backend)

    def test_o03_confirmations_persist_only_in_designated_slots(self):
        publisher, host, backend = fixture()
        reference, value = review(publisher, host)
        message = confirmation(publisher, host, reference, value)
        adoption = publisher.confirm_review("source_review", message["message_id"])
        self.assertIn("/contract_adoption_", adoption["path"])
        self.assertEqual(json.loads(backend.files[adoption["path"]])["body"]["confirmation"], message)
        publisher.publish_record("admission", "metadata-only record")
        actual, actual_value = review(publisher, host, "actual_review", "actual_peer")
        actual_message = confirmation(publisher, host, actual, actual_value)
        disposition = publisher.confirm_review("actual_review", actual_message["message_id"])
        self.assertIn("/root_disposition_", disposition["path"])
        self.assertNotEqual(actual["path"], disposition["path"])
        self.assertLessEqual(len(packed(message)), CONFIRMATION_BYTES)

    def test_o03_missing_mismatched_and_oversize_confirmation_consumes(self):
        for fault in ("missing", "hash", "path", "text_hash", "overflow"):
            with self.subTest(fault=fault):
                publisher, host, backend = fixture()
                reference, value = review(publisher, host)
                message = confirmation(publisher, host, reference, value,
                                       text="x" * 8192 if fault == "overflow" else "ok")
                if fault == "missing":
                    host.messages.pop(("source_peer", message["message_id"]))
                else:
                    if fault == "hash":
                        message["review_pin"]["sha256"] = "0" * 64
                    elif fault == "path":
                        message["review_pin"]["path"] += ".copy"
                    elif fault == "text_hash":
                        message["review_text_sha256"] = "0" * 64
                    host.messages[("source_peer", message["message_id"])] = packed(message)
                with self.assertRaises(PublicationRefusal):
                    publisher.confirm_review("source_review", message["message_id"])
                self.assertEqual(len(backend.files), 2)
                self.assert_consumed(publisher, backend)

    def test_o03_negative_confirmation_is_preserved_without_adoption(self):
        publisher, host, backend = fixture()
        reference, value = review(publisher, host)
        message = confirmation(publisher, host, reference, value, confirmed=False, text="bytes differ")
        result = publisher.confirm_review("source_review", message["message_id"])
        body = json.loads(backend.files[result["path"]])["body"]
        self.assertEqual(body["status"], "INCOMPLETE_REFUSED")
        self.assertEqual(body["confirmation"]["text"], "bytes differ")
        with self.assertRaises(PublicationRefusal):
            publisher.publish_record("admission", "must refuse")
        self.assert_consumed(publisher, backend)

    def test_o04_unknown_sidecar_and_off_directory_file_refuse(self):
        for path in (PHASE + "/extra.json", ROOT + "/unrelated/operation-copy.json"):
            with self.subTest(path=path):
                publisher, host, backend = fixture()
                host.extra.append(path)
                with self.assertRaises(PublicationRefusal):
                    publisher.publish_record("scope", "refused")
                self.assertEqual(len(backend.files), 1)
                self.assert_consumed(publisher, backend)

    def test_o04_late_sidecar_refuses_close(self):
        publisher, host, backend = fixture()
        host.extra.append(ROOT + "/outside.txt")
        with self.assertRaises(PublicationRefusal):
            publisher.close()
        self.assert_consumed(publisher, backend)

    def test_o05_occupied_slot_refuses_before_any_create(self):
        publisher, _, backend = fixture(initialize=False)
        path = PHASE + "/scope_" + OPERATION + ".json"
        backend.files[path] = b"original"
        with self.assertRaises(PublicationRefusal):
            publisher.initialize()
        self.assertFalse(any(event[0] == "create" for event in backend.events))
        self.assertEqual(backend.files[path], b"original")

    def test_o05_postcreate_fact_refusal_prevents_payload_write(self):
        publisher, _, backend = fixture()
        backend.events.clear()
        backend.fail = "postcreate"
        with self.assertRaises(PublicationRefusal):
            publisher.publish_record("scope", "never written")
        self.assertIn("postcreate_facts", [event[0] for event in backend.events])
        self.assertNotIn("write", [event[0] for event in backend.events])
        self.assertEqual(backend.files[PHASE + "/scope_" + OPERATION + ".json"], b"")
        self.assert_consumed(publisher, backend)

    def test_o06_escaping_and_complete_envelopes_are_charged_before_create(self):
        for chunks, external in ((["\U0001f642" * 90000], "ok"), (["ok"], "\u0001" * 11000),
                                 (["ok"], "x" * 65536)):
            with self.subTest(raw_length=len(chunks[0]), external_length=len(external)):
                publisher, _, backend = fixture()
                with self.assertRaises(PublicationRefusal):
                    publisher.publish_capture(chunks, external)
                self.assertEqual(len(backend.files), 1)
                self.assert_consumed(publisher, backend)

    def test_o06_independently_reviewed_capture_bound_can_be_tighter(self):
        publisher, _, backend = fixture(mutate=lambda value: value["capture"].update(raw_max_encoded_bytes=512))
        with self.assertRaises(PublicationRefusal):
            publisher.publish_capture(["x" * 512], "ok")
        self.assertEqual(len(backend.files), 1)

    def test_o06_bounded_encoder_exact_boundary_and_invalid_values(self):
        raw = packed({"text": "\u0000\U0001f642\"\\"})
        self.assertEqual(encode({"text": "\u0000\U0001f642\"\\"}, len(raw), checkpoint), raw)
        with self.assertRaises(PublicationRefusal):
            encode({"text": "\u0000\U0001f642\"\\"}, len(raw) - 1, checkpoint)
        for value in (1.0, float("nan"), 2**63, {"bad": object()}, ["\ud800"]):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises((PublicationRefusal, UnicodeError)):
                    packed(value)

    def test_o07_role_faults_preserve_partial_and_unknown_cleanup(self):
        for fault in ("short_write", "readback", "file_close", "ancestry_close"):
            with self.subTest(fault=fault):
                publisher, _, backend = fixture()
                backend.fail = fault
                with self.assertRaises(PublicationRefusal):
                    publisher.publish_record("scope", "payload")
                self.assertEqual(len(backend.files), 2)
                self.assertEqual(publisher.snapshot()["states"]["scope"], "FAILED_CONSUMED")
                if fault in ("file_close", "ancestry_close"):
                    self.assertIsNotNone(publisher.snapshot()["cleanup_error"])
                self.assert_consumed(publisher, backend)

    def test_o07_second_capture_failure_preserves_first_capture(self):
        publisher, _, backend = fixture()
        original = backend.write_new
        def second_failure(path, raw):
            if "/external_return_" in path:
                backend.fail = "short_write"
            return original(path, raw)
        backend.write_new = second_failure
        with self.assertRaises(PublicationRefusal):
            publisher.publish_capture(["full native tool text"], "external")
        self.assertEqual(len(backend.files), 3)
        raw_path = PHASE + "/raw_tool_return_" + OPERATION + ".json"
        self.assertEqual(json.loads(backend.files[raw_path])["body"]["chunks"], ["full native tool text"])
        self.assert_consumed(publisher, backend)

    def test_o08_invalid_public_mutations_poison_active_transaction(self):
        for action in (lambda p: p.publish_record("extra", "x"), lambda p: p.publish_record("scope", True),
                       lambda p: p.publish_record("admission", "premature"), lambda p: p.initialize()):
            with self.subTest(action=action):
                publisher, _, backend = fixture()
                with self.assertRaises(PublicationRefusal):
                    action(publisher)
                self.assert_consumed(publisher, backend)

    def test_o08_seventeenth_accounting_unit_refuses_with_spare_bytes(self):
        publisher, host, backend = fixture()
        host.extra = [ROOT + "/extra_" + str(index) for index in range(16)]
        with self.assertRaises(PublicationRefusal):
            publisher.publish_record("scope", "small")
        self.assertEqual(len(backend.files), 1)
        self.assert_consumed(publisher, backend)

    def test_o09_transport_refusal_precedes_claim_or_create(self):
        backend = FakeBackend()
        with self.assertRaises(PublicationRefusal):
            fixture(backend=backend, mutate=lambda value: value["capture"].update(transport="stdout_only"))
        self.assertEqual(backend.events, [])

    def test_o10_correction_cannot_replace_published_review(self):
        publisher, host, backend = fixture()
        reference, _ = review(publisher, host, text="original review")
        original = backend.files[reference["path"]]
        with self.assertRaises(PublicationRefusal):
            review(publisher, host, text="corrected review")
        self.assertEqual(backend.files[reference["path"]], original)
        self.assertEqual(len(backend.files), 2)
        self.assert_consumed(publisher, backend)

    def test_o10_consumed_confirmation_destination_has_no_fallback(self):
        publisher, host, backend = fixture()
        reference, value = review(publisher, host)
        message = confirmation(publisher, host, reference, value)
        result = publisher.confirm_review("source_review", message["message_id"])
        original = backend.files[result["path"]]
        with self.assertRaises(PublicationRefusal):
            publisher.confirm_review("source_review", message["message_id"])
        self.assertEqual(len(backend.files), 3)
        self.assertEqual(backend.files[result["path"]], original)

    def test_o11_raw_chunks_and_large_native_integers_remain_exact_text(self):
        publisher, _, backend = fixture()
        chunks = ['{"filetime":18446744073709551615,"id":9007199254740993}\r\n', "stderr\t\u03bb\U0001f642\n"]
        refs = publisher.publish_capture(chunks, "exact external return text")
        body = json.loads(backend.files[refs[0]["path"]])["body"]
        self.assertEqual(body["chunks"], chunks)
        self.assertIsInstance(body["chunks"][0], str)
        for key in FALSES:
            self.assertIs(json.loads(backend.files[refs[0]["path"]])[key], False)

    def test_o11_returned_pin_cannot_mutate_retained_native_authority(self):
        publisher, _, backend = fixture(initialize=False)
        reference = publisher.initialize()
        reference["native_identity"]["file_id"] = "f" * 32
        reference["sha256"] = "0" * 64
        publisher.publish_record("scope", "still verifies original ledger")
        self.assertEqual(len(backend.files), 2)
        with self.assertRaises(AttributeError):
            publisher.operation = "replacement"

    def test_o12_refused_actual_review_is_separate_from_root_disposition(self):
        publisher, host, backend = fixture()
        reference, value = review(publisher, host, "actual_review", "actual_peer", "INCOMPLETE_REFUSED")
        message = confirmation(publisher, host, reference, value)
        result = publisher.confirm_review("actual_review", message["message_id"])
        self.assertNotEqual(reference["path"], result["path"])
        record = json.loads(backend.files[result["path"]])
        self.assertEqual(record["body"]["status"], "INCOMPLETE_REFUSED")
        for key in FALSES:
            self.assertIs(record[key], False)
        self.assertEqual(json.loads(backend.files[reference["path"]])["body"]["decision"], "INCOMPLETE_REFUSED")

    def test_guard_failure_consumes_and_cannot_publish(self):
        active = [True]
        publisher, host, backend = fixture(guard=lambda: active[0])
        active[0] = False
        with self.assertRaises(PublicationRefusal):
            publisher.publish_record("scope", "guard refused")
        self.assertIn(OPERATION, host.claimed)
        self.assert_consumed(publisher, backend)

    def test_closed_publisher_cannot_restart(self):
        publisher, _, backend = fixture()
        publisher.close()
        count = len(backend.files)
        with self.assertRaises(PublicationRefusal):
            publisher.publish_record("scope", "late")
        self.assertEqual(publisher.snapshot()["status"], "CLOSED")
        self.assertEqual(len(backend.files), count)


class NativeReaderDouble:
    """Exercises the backend algorithm, not Windows facts or actual handles."""

    def __init__(self, events, fault=None, label="owner"):
        self.events, self.fault, self.label = events, fault, label
        self.raw, self._directories = bytearray(), {}
        self.cleanup_errors = []
        self.api = self

    def _check(self):
        self.events.append((self.label, "guard"))

    def retain_directory(self, path):
        self.events.append((self.label, "retain_ancestry"))
        self._directories[path] = (90, {"native_identity": identity(99)})

    def _facts(self, handle, path, directory):
        self.events.append((self.label, "directory_facts" if directory else "file_facts"))
        if directory:
            return identity(99), 0, 1, 16
        return identity(2 if self.fault == "identity" else 1), len(self.raw), 1, 0

    def _open(self, path, create=False):
        self.events.append((self.label, "exclusive_create"))
        if create is not True:
            raise AssertionError("exclusive creation required")
        self.events.append((self.label, "immediate_original_facts"))
        if self.fault == "postcreate":
            self._close_handle(41)
            raise ValueError("original facts refused")
        return 41, (identity(1), 0, 1, 0)

    def WriteFile(self, handle, buffer, length, written, overlap):
        self.events.append((self.label, "write"))
        if self.fault == "write_error":
            return 0
        count = length - 1 if self.fault == "short_write" else length
        self.raw.extend(ctypes.string_at(buffer, count))
        ctypes.cast(written, ctypes.POINTER(ctypes.c_uint32))[0] = count
        return 1

    def FlushFileBuffers(self, handle):
        self.events.append((self.label, "flush"))
        return 0 if self.fault == "flush" else 1

    def _hash(self, handle, length):
        self.events.append((self.label, "full_readback"))
        return {"bytes": len(self.raw), "sha256": "0" * 64 if self.fault == "readback" else
                hashlib.sha256(self.raw).hexdigest()}, None

    def verify(self):
        self.events.append((self.label, "verify_inputs"))

    def _close_handle(self, handle):
        self.events.append((self.label, "close_original"))
        if self.fault == "file_close":
            self.cleanup_errors.append("unknown original close")
            raise OSError("unknown original close")

    def close(self):
        self.events.append((self.label, "close_ancestry"))
        if self.cleanup_errors or self.fault == "ancestry_close":
            raise OSError("unknown retained ancestry/original closure")

    @staticmethod
    def _error(message):
        return OSError(message)


class NativeBackendOrderingTests(unittest.TestCase):
    def make_backend(self, fault=None):
        events = []
        backend = native_backend.NativeBackend(checkpoint)
        backend.reader = NativeReaderDouble(events, label="inputs")
        backend.reader.retain_directory(PHASE)
        backend._prepared = True
        owner = NativeReaderDouble(events, fault)
        return backend, owner, events

    def test_native_model_original_facts_precede_write_readback_precedes_close(self):
        backend, owner, events = self.make_backend()
        path = PHASE + "/scope_" + OPERATION + ".json"
        raw = b"a" * 65537
        with mock.patch.object(native_backend, "RetainedReader", return_value=owner), \
                mock.patch.object(native_backend.os, "lstat", side_effect=FileNotFoundError):
            result = backend.write_new(path, raw)
        names = [name for label, name in events if label == "owner"]
        self.assertLess(names.index("exclusive_create"), names.index("immediate_original_facts"))
        self.assertLess(names.index("immediate_original_facts"), names.index("write"))
        self.assertLess(names.index("full_readback"), names.index("close_original"))
        self.assertLess(names.index("close_original"), names.index("close_ancestry"))
        self.assertEqual(names.count("write"), 2)
        self.assertEqual(bytes(owner.raw), raw)
        self.assertEqual({key: result[key] for key in ("bytes", "sha256")}, pin(raw))
        self.assertIs(result["original_file_closed"], True)
        self.assertIs(result["original_ancestry_closed"], True)
        backend.close()

    def test_native_model_postcreate_failure_never_writes_and_closes_once(self):
        backend, owner, events = self.make_backend("postcreate")
        with mock.patch.object(native_backend, "RetainedReader", return_value=owner), \
                mock.patch.object(native_backend.os, "lstat", side_effect=FileNotFoundError):
            with self.assertRaises(RuntimeError):
                backend.write_new(PHASE + "/scope_" + OPERATION + ".json", b"payload")
        names = [name for label, name in events if label == "owner"]
        self.assertNotIn("write", names)
        self.assertEqual(names.count("close_original"), 1)
        self.assertEqual(names.count("close_ancestry"), 1)
        backend.close()

    def test_native_model_faults_refuse_without_retry_or_unknown_close_success(self):
        for fault in ("write_error", "short_write", "flush", "identity", "readback", "file_close", "ancestry_close"):
            with self.subTest(fault=fault):
                backend, owner, events = self.make_backend(fault)
                with mock.patch.object(native_backend, "RetainedReader", return_value=owner), \
                        mock.patch.object(native_backend.os, "lstat", side_effect=FileNotFoundError):
                    with self.assertRaises(RuntimeError):
                        backend.write_new(PHASE + "/scope_" + OPERATION + ".json", b"payload")
                names = [name for label, name in events if label == "owner"]
                self.assertEqual(names.count("exclusive_create"), 1)
                self.assertEqual(names.count("close_original"), 1)
                self.assertEqual(names.count("close_ancestry"), 1)
                if fault in ("file_close", "ancestry_close"):
                    with self.assertRaises(PublicationRefusal):
                        backend.close()
                    self.assertTrue(backend.cleanup_errors)
                else:
                    backend.close()

    def test_native_model_constructor_failure_has_no_invented_original_handle(self):
        backend, _, events = self.make_backend()
        with mock.patch.object(native_backend, "RetainedReader", side_effect=MemoryError("constructor")):
            with self.assertRaises(RuntimeError):
                backend.write_new(PHASE + "/scope_" + OPERATION + ".json", b"payload")
        self.assertFalse(any(label == "owner" for label, _ in events))
        backend.close()

