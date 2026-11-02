"""Source-only adversarial subset; execution requires separate local admission.

The local reads below load static test fixtures, not authenticated operational
evidence. No Windows providers or numerical libraries are imported or invoked.
"""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("custody_boundary_verifier_v1", HERE / "verifier.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def encoded(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


def reference(path, data):
    return {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class StrictJsonTests(unittest.TestCase):
    def test_duplicate_properties_at_nested_level(self):
        with self.assertRaises(verifier.VerificationError):
            verifier.strict_json(b'{"outer":{"a":1,"a":2}}')

    def test_nonfinite_constants_and_extreme_decimal_tokens(self):
        for token in (b"NaN", b"Infinity", b"-Infinity", b"1e10001", b"1" * 129):
            with self.subTest(token=token[:20]), self.assertRaises(verifier.VerificationError):
                verifier.strict_json(token)

    def test_lossless_decimal_and_integer(self):
        value = verifier.strict_json(b'[9007199254740991,0.123456789012345678901]')
        self.assertEqual(value[0], 9007199254740991)
        self.assertEqual(str(value[1]), "0.123456789012345678901")

    def test_record_depth_node_and_string_bounds(self):
        samples = (
            b" " * (verifier.MAX_RECORD_BYTES + 1),
            b"[" * 17 + b"0" + b"]" * 17,
            encoded([None] * verifier.MAX_NODES),
            encoded("x" * (verifier.MAX_STRING + 1)),
            b'{"' + b"x" * (verifier.MAX_STRING + 1) + b'":0}',
        )
        for sample in samples:
            with self.subTest(size=len(sample)), self.assertRaises(verifier.VerificationError):
                verifier.strict_json(sample)

    def test_unicode_encoding_bom_surrogate_and_trailing_data(self):
        for sample in (b'"\xff"', b'\xef\xbb\xbf{}', b'"\\ud800"', b"{}{}", b"[1,]"):
            with self.subTest(sample=sample), self.assertRaises(verifier.VerificationError):
                verifier.strict_json(sample)

    def test_escaped_braces_do_not_create_false_nesting(self):
        text = '[{"escaped":"\\\"[{]"}]'
        self.assertEqual(verifier.strict_json(text.encode())[0]["escaped"], '"[{]')


class TimePathArtifactTests(unittest.TestCase):
    def test_calendar_validity_and_strict_utc(self):
        for date in ("2026-02-29T00:00:00Z", "2026-13-01T00:00:00Z", "0000-01-01T00:00:00Z",
                     "2026-10-28T24:00:00Z", "2026-10-28T00:00:60Z", "2026-10-28T00:00:00+00:00",
                     "2026-10-28T00:00:00.00000001Z"):
            with self.subTest(date=date), self.assertRaises(verifier.VerificationError):
                verifier.utc_ticks(date)

    def test_timestamp_seventh_digit_is_preserved(self):
        first = verifier.utc_ticks("2024-02-29T00:00:00.0000001Z")
        second = verifier.utc_ticks("2024-02-29T00:00:00.0000002Z")
        self.assertEqual(second - first, 1)

    def test_windows_alias_and_traversal_paths(self):
        for path in ("/absolute", "a//b", "a/./b", "a/../b", "a/", "a.", "CON", "a/nul.txt",
                     "COM1.txt", "LPT9", "C:/a", "\\\\host\\share", "a\\b", "a:stream", "PROGRA~1/x", "a /b"):
            with self.subTest(path=path), self.assertRaises(verifier.VerificationError):
                verifier.normalized_path(path)
        self.assertEqual(verifier.normalized_path("runs/coordination/new-identity/raw_1.json"),
                         "runs/coordination/new-identity/raw_1.json")

    def test_artifact_length_digest_and_type(self):
        data = b"retained test bytes"
        ref = reference("test/source.txt", data)
        self.assertEqual(verifier.validate_artifact(ref, {ref["path"]: data}), data)
        for field, replacement in (("bytes", True), ("bytes", len(data) + 1), ("sha256", "0" * 64),
                                   ("sha256", "A" * 64), ("path", "test/../source.txt")):
            changed = dict(ref, **{field: replacement})
            with self.subTest(field=field, replacement=replacement), self.assertRaises(verifier.VerificationError):
                verifier.validate_artifact(changed, {ref["path"]: data})

    def test_operational_read_is_unconditionally_disabled(self):
        with self.assertRaises(verifier.OperationalReadUnavailable):
            verifier.read_operational_artifact("D:/Aenv/pro3", reference("test.txt", b""))

    def test_qpc_exact_bounds_order_and_duration(self):
        valid = {"qpc_frequency": 10000000, "qpc_start": 9007199244740991,
                 "qpc_end": 9007199254740991, "observed_start_utc": "2026-10-28T16:00:00Z",
                 "observed_end_utc": "2026-10-28T16:00:01Z"}
        verifier.validate_qpc(valid)
        mutations = (("qpc_start", True), ("qpc_start", 1.0), ("qpc_start", -1),
                     ("qpc_end", 9007199254740992), ("qpc_frequency", 0),
                     ("qpc_frequency", 1000000000001), ("qpc_end", 0),
                     ("observed_end_utc", "2026-10-28T16:00:02Z"))
        for field, replacement in mutations:
            with self.subTest(field=field, replacement=replacement), self.assertRaises(verifier.VerificationError):
                verifier.validate_qpc(dict(valid, **{field: replacement}))
        too_long = dict(valid, qpc_start=0, qpc_end=3010000000,
                        observed_end_utc="2026-10-28T16:05:01Z")
        with self.assertRaises(verifier.VerificationError):
            verifier.validate_qpc(too_long)

    def test_sequence_order_freshness_and_enclosing_window(self):
        names = ("source_review_utc", "observation_admission_utc", "capture_start_utc",
                 "capture_end_utc", "actual_tool_return_utc", "actual_review_utc", "disposition_utc",
                 "bootstrap_admission_utc", "dispatch_utc")
        valid = {name: "2026-10-28T16:00:%02dZ" % index for index, name in enumerate(names)}
        verifier.validate_sequence(valid)
        for field in names[1:]:
            with self.subTest(field=field), self.assertRaises(verifier.VerificationError):
                verifier.validate_sequence(dict(valid, **{field: valid[names[0]]}))
        with self.assertRaises(verifier.VerificationError):
            verifier.validate_sequence(dict(valid, bootstrap_admission_utc="2026-10-28T16:06:00Z",
                                            dispatch_utc="2026-10-28T16:06:01Z"))
        verifier.validate_window("2026-10-28T16:00:00Z", "2026-10-28T16:00:10Z",
                                 "2026-10-28T16:00:01Z", "2026-10-28T16:00:09Z")
        with self.assertRaises(verifier.VerificationError):
            verifier.validate_window("2026-10-28T16:00:00Z", "2026-10-28T16:00:10Z",
                                     "2026-10-28T16:00:01Z", "2026-10-28T16:00:11Z")


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = ROOT / "docs/phase2/cho51_p3_local_custody_v1"
        cls.contracts = {kind: (directory / (kind + ".schema.json")).read_bytes()
                         for kind in verifier.CONTRACT_HASHES}
        cls.policy = (ROOT / "docs/PROJECT_EXECUTION_POLICY.md").read_bytes()
        old_dir = "runs/coordination/cho51_p3_contracts_20261027_v1/"
        files = {"disposition": "bootstrap-disposition_004.json", "actual_audit": "bootstrap-external-audit_004.json",
                 "failed_review": "bootstrap-actual-review_004.json"}
        cls.old_artifacts = {old_dir + name: (ROOT / (old_dir + name)).read_bytes() for name in files.values()}
        cls.historical = {name: reference(old_dir + filename, cls.old_artifacts[old_dir + filename])
                          for name, filename in files.items()}
        cls.historical.update(status="FAILED_UNRELEASED_CONSUMED", custody_closed=False,
                              operation_released=False, retry_allowed=False)

    def candidate(self):
        artifacts = dict(self.old_artifacts)
        packet = {"schema": "cho51_p3_local_boundary_evidence_v1",
                  "capture_id": "00000000-0000-0000-0000-000000000001",
                  "created_utc": "2026-10-28T16:00:02Z", "boundary_kind": "complete_os_restart",
                  "historical": copy.deepcopy(self.historical), "policy_sha256": hashlib.sha256(self.policy).hexdigest(),
                  "observed_start_utc": "2026-10-28T16:00:00Z", "observed_end_utc": "2026-10-28T16:00:01Z",
                  "qpc_frequency": 10000000, "qpc_start": 0, "qpc_end": 10000000,
                  "launch_authorized": False, "scientific_admission": False}
        fields = ("collector_source", "collector_protocol", "collector_source_review", "runtime_pins",
                  "observation_admission", "event_to_host_binding", "current_host_identity", "restart_evidence",
                  "clock_consistency_evidence", "persisted_domain_assessment", "actual_tool_return")
        for field in fields:
            path = "test_only/" + field + ".json"
            # Deliberately forged self-assertions are never provider qualification.
            data = encoded({"accepted": True, "provider_qualified": True, "host_binding_established": True})
            artifacts[path] = data
            packet[field] = reference(path, data)
        packet["raw_observations"] = [packet["restart_evidence"]]
        return packet, artifacts

    def assess(self, packet, artifacts, **kwargs):
        return verifier.assess_boundary(encoded(packet), artifacts, self.contracts, policy_bytes=self.policy, **kwargs)

    def forged_admission(self, packet, artifacts):
        packet_data = encoded(packet)
        artifacts["test_only/packet.json"] = packet_data
        actual_review = packet["collector_source_review"]
        disposition = {"schema": "cho51_p3_local_custody_disposition_v1",
                       "disposition_id": packet["capture_id"], "created_utc": "2026-10-28T16:00:03Z",
                       "author": "project_root", "policy_sha256": packet["policy_sha256"],
                       "historical": packet["historical"], "status": "ELIGIBLE_FOR_LOCAL_ADMISSION_REVIEW",
                       "current_boundary": {"kind": "verified_complete_os_restart", "host_identity_sha256": "a" * 64,
                                            "boot_generation_sha256": "b" * 64,
                                            "evidence": reference("test_only/packet.json", packet_data),
                                            "independent_actual_review": actual_review},
                       "reason_codes": [], "limitations": ["Fabricated metadata is not machine evidence"],
                       "launch_authorized": False, "scientific_admission": False}
        disposition_data = encoded(disposition)
        artifacts["test_only/disposition.json"] = disposition_data
        operation_id = "00000000-0000-0000-0000-000000000002"
        admission = {"schema": "cho51_p3_local_bootstrap_admission_v1", "operation_id": operation_id,
                     "scope": "cho51_p3_local_bootstrap_006", "created_utc": "2026-10-28T16:00:04Z",
                     "window_start_utc": "2026-10-28T16:00:04Z", "window_end_utc": "2026-10-28T16:01:00Z",
                     "author": "project_root", "accepted": True, "policy_sha256": packet["policy_sha256"],
                     "request": packet["observation_admission"],
                     "custody_disposition": reference("test_only/disposition.json", disposition_data),
                     "source_review": packet["collector_source_review"],
                     "sources": {name: packet["collector_source"] for name in ("controller", "helper", "protocol", "boundary_verifier")},
                     "runtime_pins": packet["runtime_pins"], "expected_host_identity_sha256": "a" * 64,
                     "expected_boot_generation_sha256": "b" * 64,
                     "attempt_directory": "runs/coordination/cho51_p3_local_bootstrap_006/" + operation_id,
                     "local_stop_path": "runs/coordination/PROJECT_STOP.json",
                     "limits": {"whole_caller_seconds": 90, "helper_seconds": 45, "outer_start_seconds": 15,
                                "outer_work_seconds": 65, "outer_cleanup_seconds": 80, "outer_effect_seconds": 85,
                                "output_bytes": 1048576, "process_mib": 4096, "job_mib": 5120,
                                "startup_ram_gib": 10, "active_ram_gib": 4, "free_disk_gib": 20,
                                "helpers": 1, "threads": 1, "gpu_hidden": True},
                     "automatic_retry_permitted": False, "historical_retry_allowed": False,
                     "scientific_admission": False}
        return disposition_data, admission

    def test_conforming_forged_positive_packet_stays_unresolved(self):
        packet, artifacts = self.candidate()
        verifier.validate_record("boundary-evidence", encoded(packet), self.contracts)
        result = self.assess(packet, artifacts)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIn("PROVIDER_COVERAGE_UNQUALIFIED", result["reason_codes"])
        self.assertIn("HOST_ASSOCIATION_UNESTABLISHED", result["reason_codes"])
        self.assertIs(result["launch_authorized"], False)
        self.assertIs(result["operationally_qualified"], False)
        self.assertIs(result["historical_custody_closed"], False)
        self.assertIs(result["historical_operation_released"], False)
        self.assertIs(result["historical_retry_allowed"], False)

    def test_no_packet_returns_unresolved_without_reading_anything(self):
        result = verifier.assess_boundary(None, {}, {})
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIs(result["launch_authorized"], False)

    def test_exact_schema_pin_and_unknown_keyword_fail_closed(self):
        packet, _ = self.candidate()
        changed = dict(self.contracts, **{"boundary-evidence": self.contracts["boundary-evidence"] + b" "})
        with self.assertRaises(verifier.VerificationError):
            verifier.validate_record("boundary-evidence", encoded(packet), changed)
        for schema in ({"type": "object", "not": {}}, {"anyOf": [{"const": 1}, {"unevaluatedProperties": False}]},
                       {"$ref": "https://example.invalid/schema"}):
            with self.subTest(schema=schema), self.assertRaises(verifier.VerificationError):
                verifier.validate_schema(1, schema)

    def test_closed_fields_bad_dates_integer_types_and_uniqueness(self):
        packet, _ = self.candidate()
        mutations = (("extra", 1), ("qpc_start", True), ("qpc_start", 1.0),
                     ("qpc_start", 9007199254740992), ("created_utc", "2026-02-29T00:00:00Z"),
                     ("raw_observations", packet["raw_observations"] * 2), ("launch_authorized", 0))
        for field, replacement in mutations:
            changed = dict(packet, **{field: replacement})
            with self.subTest(field=field, replacement=replacement), self.assertRaises(verifier.VerificationError):
                verifier.validate_record("boundary-evidence", encoded(changed), self.contracts)

    def test_missing_and_tampered_historical_bytes_refused(self):
        packet, artifacts = self.candidate()
        path = packet["historical"]["disposition"]["path"]
        for data in (None, artifacts[path] + b" "):
            changed = dict(artifacts)
            if data is None:
                del changed[path]
            else:
                changed[path] = data
            with self.subTest(missing=data is None):
                result = self.assess(packet, changed)
                self.assertEqual(result["status"], "REFUSED")

    def test_historical_flags_and_hash_cannot_be_upgraded(self):
        packet, artifacts = self.candidate()
        for field in ("custody_closed", "operation_released", "retry_allowed"):
            changed = copy.deepcopy(packet)
            changed["historical"][field] = True
            with self.subTest(field=field):
                self.assertEqual(self.assess(changed, artifacts)["status"], "REFUSED")
        packet["historical"]["disposition"]["sha256"] = "0" * 64
        self.assertEqual(self.assess(packet, artifacts)["status"], "REFUSED")

    def test_missing_candidate_artifact_and_policy_are_unresolved(self):
        packet, artifacts = self.candidate()
        del artifacts[packet["collector_source"]["path"]]
        self.assertEqual(self.assess(packet, artifacts)["status"], "UNRESOLVED")
        packet, artifacts = self.candidate()
        result = verifier.assess_boundary(encoded(packet), artifacts, self.contracts)
        self.assertEqual(result["status"], "UNRESOLVED")

    def test_artifact_tampering_alias_and_policy_mismatch_refused(self):
        packet, artifacts = self.candidate()
        path = packet["collector_source"]["path"]
        changed = dict(artifacts, **{path: b"changed"})
        self.assertEqual(self.assess(packet, changed)["status"], "REFUSED")
        changed = dict(artifacts, **{path.upper(): artifacts[path]})
        self.assertEqual(self.assess(packet, changed)["status"], "REFUSED")
        packet["policy_sha256"] = "0" * 64
        self.assertEqual(self.assess(packet, artifacts)["status"], "REFUSED")

    def test_old_or_reversed_capture_refused(self):
        packet, artifacts = self.candidate()
        packet.update(observed_start_utc="2026-10-26T16:00:00Z", observed_end_utc="2026-10-26T16:00:01Z")
        self.assertEqual(self.assess(packet, artifacts)["status"], "REFUSED")
        packet, artifacts = self.candidate()
        packet["created_utc"] = "2026-10-28T15:59:59Z"
        self.assertEqual(self.assess(packet, artifacts)["status"], "REFUSED")

    def test_disposition_conditional_and_boolean_number_distinction(self):
        packet, _ = self.candidate()
        disposition = {"schema": "cho51_p3_local_custody_disposition_v1",
                       "disposition_id": packet["capture_id"], "created_utc": packet["created_utc"],
                       "author": "project_root", "policy_sha256": packet["policy_sha256"],
                       "historical": packet["historical"], "status": "UNRESOLVED", "current_boundary": None,
                       "reason_codes": ["PROVIDER_COVERAGE_UNQUALIFIED"], "limitations": ["Test fixture only"],
                       "launch_authorized": False, "scientific_admission": False}
        verifier.validate_record("disposition", encoded(disposition), self.contracts)
        disposition["status"] = "ELIGIBLE_FOR_LOCAL_ADMISSION_REVIEW"
        with self.assertRaises(verifier.VerificationError):
            verifier.validate_record("disposition", encoded(disposition), self.contracts)
        with self.assertRaises(verifier.VerificationError):
            verifier.validate_schema(0, {"const": False})

    def test_forged_eligible_disposition_and_accepted_admission_cannot_unlock(self):
        packet, artifacts = self.candidate()
        disposition_data, admission = self.forged_admission(packet, artifacts)
        verifier.validate_record("disposition", disposition_data, self.contracts)
        verifier.validate_record("local-admission", encoded(admission), self.contracts)
        result = self.assess(packet, artifacts, disposition_bytes=disposition_data, admission_bytes=encoded(admission))
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertIs(result["launch_authorized"], False)
        self.assertIs(result["operationally_qualified"], False)

    def test_admission_uuid_stale_policy_generation_and_limit_tampering(self):
        packet, artifacts = self.candidate()
        disposition_data, admission = self.forged_admission(packet, artifacts)
        mutations = (("operation_id", packet["capture_id"]), ("policy_sha256", "0" * 64),
                     ("expected_boot_generation_sha256", "c" * 64),
                     ("created_utc", "2026-10-28T16:06:05Z"), ("accepted", 1))
        for field, replacement in mutations:
            changed = dict(admission, **{field: replacement})
            with self.subTest(field=field):
                result = self.assess(packet, artifacts, disposition_bytes=disposition_data, admission_bytes=encoded(changed))
                self.assertEqual(result["status"], "REFUSED")
        changed = copy.deepcopy(admission)
        changed["limits"]["job_mib"] = 8192
        with self.assertRaises(verifier.VerificationError):
            verifier.validate_record("local-admission", encoded(changed), self.contracts)


if __name__ == "__main__":
    unittest.main()
