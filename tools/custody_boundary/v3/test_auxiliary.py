"""Closed-chain and retained-composition tests; all fixtures are synthetic.

Historical bytes and schemas are copied as exact static inputs; this never
establishes the provenance of their original host. Guarded admission required.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("_auxiliary_test_subject", HERE / "auxiliary.py")
aux = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = aux
spec.loader.exec_module(aux)


def encode(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode()


def ref(path, data):
    return {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class Fixture:
    def __init__(self):
        self.artifacts = {}
        def put(path, data):
            self.artifacts[path] = data
            return ref(path, data)
        self.put = put
        self.contracts = {kind: (ROOT / "docs/phase2/cho51_p3_local_custody_v1" / (kind + ".schema.json")).read_bytes()
                          for kind in aux.core.CONTRACT_HASHES}
        self.contract_refs = {kind: put("contracts/" + kind + ".schema.json", data) for kind, data in self.contracts.items()}
        self.policy = put("input/policy.txt", b"Synthetic policy identity; no execution authority")
        sources = [put("input/collector.py", b"synthetic collector source"),
                   put("input/protocol.md", b"synthetic protocol"), put("input/verifier.py", b"synthetic verifier source")]
        runtime = {"schema": aux.SCHEMAS["runtime"], "observed_utc": "2026-10-28T16:00:00Z",
                   "runtime_root_id": "a" * 64, "files": [ref("python.exe", b"synthetic runtime") ]}
        self.records = {"runtime": runtime,
            "source_review": {"schema": aux.SCHEMAS["source_review"], "reviewer": "source_reviewer",
                              "authors": ["project_root", "collector_author"], "reviewed_utc": "2026-10-28T16:00:01Z",
                              "sources": sources, "runtime_pins": None, "accepted": True},
            "admission": {"schema": aux.SCHEMAS["admission"], "capture_id": "00000000-0000-0000-0000-000000000001",
                          "author": "project_root", "issued_utc": "2026-10-28T16:00:02Z",
                          "window_start_utc": "2026-10-28T16:00:02Z", "window_end_utc": "2026-10-28T16:01:00Z",
                          "source_review": None, "sources": sources, "runtime_pins": None,
                          "policy_sha256": self.policy["sha256"], "scope": "boundary_observation", "accepted": True},
            "return": {"schema": aux.SCHEMAS["return"], "capture_id": "00000000-0000-0000-0000-000000000001",
                       "executor": "project_root", "source_review": None, "admission": None, "sources": sources,
                       "runtime_pins": None, "policy_sha256": self.policy["sha256"],
                       "observed_start_utc": "2026-10-28T16:00:03Z", "observed_end_utc": "2026-10-28T16:00:04Z",
                       "actual_return_utc": "2026-10-28T16:00:05Z", "tool_call_id": "SYNTHETIC-TEST-CALL", "exit_code": 0}}
        historical = {}
        old = ROOT / "runs/coordination/cho51_p3_contracts_20261027_v1"
        for key, filename in {"disposition": "bootstrap-disposition_004.json", "actual_audit": "bootstrap-external-audit_004.json",
                              "failed_review": "bootstrap-actual-review_004.json"}.items():
            historical[key] = put("history/" + filename, (old / filename).read_bytes())
        historical.update(status="FAILED_UNRELEASED_CONSUMED", custody_closed=False, operation_released=False, retry_allowed=False)
        self.packet = {"schema": "cho51_p3_local_boundary_evidence_v1", "capture_id": self.records["admission"]["capture_id"],
                       "created_utc": "2026-10-28T16:00:06Z", "boundary_kind": "complete_os_restart", "historical": historical,
                       "policy_sha256": self.policy["sha256"], "collector_source": sources[0], "collector_protocol": sources[1],
                       "observed_start_utc": "2026-10-28T16:00:03Z", "observed_end_utc": "2026-10-28T16:00:04Z",
                       "qpc_frequency": 10000000, "qpc_start": 10000000, "qpc_end": 20000000,
                       "launch_authorized": False, "scientific_admission": False}
        for field in ("event_to_host_binding", "current_host_identity", "restart_evidence", "clock_consistency_evidence", "persisted_domain_assessment"):
            self.packet[field] = put("input/" + field + ".json", encode({"asserted": True, "synthetic": True}))
        self.packet["raw_observations"] = [self.packet["restart_evidence"]]
        self.records["actual_review"] = {"schema": aux.SCHEMAS["actual_review"], "capture_id": self.packet["capture_id"],
                                         "reviewer": "actual_reviewer", "reviewed_utc": "2026-10-28T16:00:07Z",
                                         "packet": None, "actual_return": None, "source_review": None, "runtime_pins": None,
                                         "raw_observations": self.packet["raw_observations"],
                                         "event_to_host_binding": self.packet["event_to_host_binding"],
                                         "scope": "auxiliary_provenance_only", "accepted": True}
        self.rebuild()

    def rebuild(self, overrides=None):
        # Apply overrides AFTER computed joins for each record. Rehash downstream
        # references so mutations test semantic checking, not only stale hashes.
        changes = overrides or {}
        r = self.records
        r["runtime"].update(changes.get("runtime", {}))
        runtime_ref = self.put("input/runtime.json", encode(r["runtime"]))
        r["source_review"]["runtime_pins"] = runtime_ref
        r["source_review"].update(changes.get("source_review", {}))
        self.source_ref = self.put("input/source-review.json", encode(r["source_review"]))
        r["admission"].update(runtime_pins=runtime_ref, source_review=self.source_ref)
        r["admission"].update(changes.get("admission", {}))
        admission_ref = self.put("input/admission.json", encode(r["admission"]))
        r["return"].update(runtime_pins=runtime_ref, source_review=self.source_ref, admission=admission_ref)
        r["return"].update(changes.get("return", {}))
        return_ref = self.put("input/return.json", encode(r["return"]))
        self.packet.update(runtime_pins=runtime_ref, collector_source_review=self.source_ref,
                           observation_admission=admission_ref, actual_tool_return=return_ref)
        self.packet.update(changes.get("packet", {}))
        self.packet_ref = self.put("input/packet.json", encode(self.packet))
        r["actual_review"].update(packet=self.packet_ref, actual_return=return_ref,
                                   source_review=self.source_ref, runtime_pins=runtime_ref)
        r["actual_review"].update(changes.get("actual_review", {}))
        self.actual_ref = self.put("input/actual-review.json", encode(r["actual_review"]))

    def assess(self):
        return aux.assess_joins(self.packet_ref, self.source_ref, self.actual_ref, self.policy, self.artifacts, self.contracts)


class AuxiliaryTests(unittest.TestCase):
    def test_coherent_chain_still_cannot_authorize(self):
        result = Fixture().assess()
        self.assertTrue(result["auxiliary_joins_verified"])
        self.assertEqual(result["status"], "UNRESOLVED")
        for field in ("retained_reads_verified", "review_identity_authenticated", "loaded_runtime_attested",
                      "boundary_qualified", "launch_authorized", "scientific_admission", "historical_custody_closed"):
            self.assertIs(result[field], False)

    def test_closed_record_fields_and_versions(self):
        for kind in aux.FIELDS:
            for change in ({"extra": True}, {"schema": "unsupported"}):
                with self.subTest(kind=kind, change=change):
                    fixture = Fixture(); fixture.rebuild({kind: change})
                    self.assertEqual(fixture.assess()["status"], "REFUSED")

    def test_review_and_admission_boolean_types(self):
        for kind in ("source_review", "admission", "actual_review"):
            for value in (False, 1, "true", None):
                with self.subTest(kind=kind, value=value):
                    f = Fixture(); f.rebuild({kind: {"accepted": value}})
                    self.assertEqual(f.assess()["status"], "REFUSED")

    def test_self_review_and_malformed_actor_refused(self):
        mutations = [("source_review", {"reviewer": "project_root"}),
                     ("source_review", {"authors": ["project_root", "project_root"]}),
                     ("actual_review", {"reviewer": "collector_author"}),
                     ("actual_review", {"reviewer": "project_root"})]
        mutations += [("admission", {"author": value}) for value in ([], {}, None, True, "outside_root")]
        for kind, change in mutations:
            with self.subTest(kind=kind, change=change):
                f = Fixture(); f.rebuild({kind: change})
                self.assertEqual(f.assess()["status"], "REFUSED")

    def test_all_dependency_joins_cannot_be_replaced(self):
        f = Fixture(); wrong = f.policy
        mutations = [(kind, field) for kind, fields in {
            "source_review": ("runtime_pins",), "admission": ("source_review", "runtime_pins"),
            "return": ("source_review", "admission", "runtime_pins"),
            "actual_review": ("packet", "actual_return", "source_review", "runtime_pins", "event_to_host_binding")}.items()
                     for field in fields]
        for kind, field in mutations:
            with self.subTest(kind=kind, field=field):
                f = Fixture(); f.rebuild({kind: {field: wrong}})
                self.assertEqual(f.assess()["status"], "REFUSED")

    def test_runtime_inventory_alias_types_and_bounds(self):
        for files in ([], [{"path": "a", "bytes": True, "sha256": "0" * 64}],
                      [ref("Python.exe", b"x"), ref("python.exe", b"x")], [ref("../python.exe", b"x")]):
            with self.subTest(files=files):
                f = Fixture(); f.rebuild({"runtime": {"files": files}})
                self.assertEqual(f.assess()["status"], "REFUSED")

    def test_exact_source_inventory_not_subset(self):
        for kind in ("admission", "return"):
            f = Fixture(); f.rebuild({kind: {"sources": f.records[kind]["sources"][:1]}})
            self.assertEqual(f.assess()["status"], "REFUSED")
        f = Fixture(); f.rebuild({"source_review": {"sources": [f.records["source_review"]["sources"][2]]}})
        self.assertEqual(f.assess()["status"], "REFUSED")

    def test_policy_and_capture_identity_mismatch(self):
        for kind in ("admission", "return", "actual_review"):
            for value in ("bad", "00000000-0000-0000-0000-000000000002"):
                f = Fixture(); f.rebuild({kind: {"capture_id": value}})
                self.assertEqual(f.assess()["status"], "REFUSED")
        for kind in ("admission", "return"):
            f = Fixture(); f.rebuild({kind: {"policy_sha256": "0" * 64}})
            self.assertEqual(f.assess()["status"], "REFUSED")

    def test_actual_return_exit_id_and_capture_times(self):
        for change in ({"exit_code": 1}, {"exit_code": False}, {"tool_call_id": ""},
                       {"observed_start_utc": "2026-10-28T16:00:02Z"}):
            f = Fixture(); f.rebuild({"return": change})
            self.assertEqual(f.assess()["status"], "REFUSED")

    def test_exact_raw_set_and_scope(self):
        for kind, change in (("actual_review", {"raw_observations": []}),
                             ("actual_review", {"scope": "qualified_complete_restart"}),
                             ("admission", {"scope": "scientific_execution"})):
            f = Fixture(); f.rebuild({kind: change})
            self.assertEqual(f.assess()["status"], "REFUSED")

    def test_chronology_and_window(self):
        changes = [("runtime", {"observed_utc": "2026-10-28T16:00:02Z"}),
                   ("source_review", {"reviewed_utc": "2026-10-28T16:00:03Z"}),
                   ("admission", {"issued_utc": "2026-10-28T16:00:04Z"}),
                   ("return", {"actual_return_utc": "2026-10-28T16:00:03Z"}),
                   ("actual_review", {"reviewed_utc": "2026-10-28T16:00:05Z"}),
                   ("admission", {"window_end_utc": "2026-10-28T16:00:04Z"}),
                   ("admission", {"window_end_utc": "2026-10-28T17:00:00Z"})]
        for kind, change in changes:
            with self.subTest(kind=kind, change=change):
                f = Fixture(); f.rebuild({kind: change})
                self.assertEqual(f.assess()["status"], "REFUSED")

    def test_untrusted_pinned_reviewer_reference_not_interchangeable(self):
        f = Fixture()
        result = aux.assess_joins(f.packet_ref, f.policy, f.actual_ref, f.policy, f.artifacts, f.contracts)
        self.assertEqual(result["status"], "REFUSED")

    def test_omitted_or_changed_artifact_refused(self):
        for path in ("input/collector.py", "input/actual-review.json", "input/runtime.json"):
            f = Fixture(); del f.artifacts[path]
            self.assertEqual(f.assess()["status"], "REFUSED")
        f = Fixture(); f.artifacts["input/policy.txt"] += b"changed"
        self.assertEqual(f.assess()["status"], "REFUSED")


class RetainedCompositionTests(unittest.TestCase):
    def test_materialized_chain_uses_retained_files_and_stays_unresolved(self):
        root = Path(os.environ["CUSTODY_AUX_TEST_ROOT"])
        if not root.is_dir() or any(root.iterdir()):
            raise RuntimeError("separate fresh admitted auxiliary fixture root required")
        f = Fixture()
        # Keep all constructed fixtures for independent review, no deletion.
        for path, data in f.artifacts.items():
            target = root.joinpath(*path.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(data)
        result = aux.assess_retained(str(root), f.packet_ref, f.source_ref, f.actual_ref,
                                     f.policy, f.contract_refs)
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertTrue(result["auxiliary_joins_verified"])
        self.assertTrue(result["retained_reads_verified"])
        self.assertIs(result["boundary_qualified"], False)
        self.assertIs(result["launch_authorized"], False)
        self.assertGreater(len(result["retained_artifacts"]), 15)
        (root / "input/collector.py").write_bytes(b"changed after release")
        changed = aux.assess_retained(str(root), f.packet_ref, f.source_ref, f.actual_ref,
                                      f.policy, f.contract_refs)
        self.assertEqual(changed["status"], "REFUSED")


if __name__ == "__main__":
    unittest.main()
