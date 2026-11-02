"""Offline intake controls; execute only under a separately reviewed admission.

The parent must retain the nine input files against mutation before loading this
suite. Tests read these exact fixtures; they never write fixtures or query native
state. Repinned variants exist solely as in-memory adversarial inputs.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


_spec = importlib.util.spec_from_file_location("_custody_intake_v6_tests", Path(__file__).with_name("assessor.py"))
assessor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(assessor)
ROOT = Path(__file__).resolve().parents[3]
IDENTITY = "dc857ad2-5788-47e2-aa2a-9182b9c91c72"
STAMP = "2026-10-28T19:00:00.1234567Z"


def encode(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False).encode("utf-8")


class IntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan_bytes = (ROOT / "tools/custody_boundary/v6/intake-plan.json").read_bytes()
        cls.baseline_plan = json.loads(cls.plan_bytes)
        cls.baseline_bytes = {ref["path"]: (ROOT / ref["path"]).read_bytes()
                              for ref in cls.baseline_plan["artifacts"].values()}

    def setUp(self):
        self.plan = copy.deepcopy(self.baseline_plan)
        self.artifacts = dict(self.baseline_bytes)

    def data(self, role):
        return json.loads(self.artifacts[self.plan["artifacts"][role]["path"]])

    def replace(self, role, value):
        self.raw_replace(role, encode(value))

    def raw_replace(self, role, raw):
        ref = self.plan["artifacts"][role]
        self.artifacts[ref["path"]] = raw
        ref.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def join_changed_pins(self):
        """Keep documentary pins coherent so semantic tampering reaches joins."""
        decoded = self.data("decoded_capture")
        decoded["input"] = copy.deepcopy(self.plan["artifacts"]["provider_capture"])
        self.replace("decoded_capture", decoded)
        review = self.data("provider_actual_review")
        for role in ("provider_capture", "decoded_capture"):
            ref = self.plan["artifacts"][role]
            review["artifact_pins"][ref["path"]] = {"bytes": ref["bytes"], "sha256": ref["sha256"]}
        ref = self.plan["artifacts"]["provider_capture"]
        review["observations"].update(offline_input_bytes=ref["bytes"], offline_input_sha256=ref["sha256"])
        self.replace("provider_actual_review", review)
        root = self.data("provider_root_qualification")
        root["actual_review"] = copy.deepcopy(self.plan["artifacts"]["provider_actual_review"])
        self.replace("provider_root_qualification", root)

    def result(self):
        return assessor.assess(self.plan, self.artifacts)

    def refused(self):
        result = self.result()
        self.assertEqual(result["status"], "REFUSED", result)
        self.assertTrue(result["reason_codes"])
        for field in assessor.TOP_FALSE:
            self.assertIs(result[field], False)
        return result

    def candidate(self, result=None, **changes):
        args = {"assessment": self.result() if result is None else result, "plan": self.plan,
                "disposition_id": IDENTITY, "created_utc": STAMP,
                "schema_bytes": self.artifacts[self.plan["artifacts"]["disposition_schema"]["path"]]}
        args.update(changes)
        return assessor.build_disposition(**args)

    def test_exact_retained_nine_inputs_remain_unresolved(self):
        self.assertEqual(len(self.artifacts), 9)
        for ref in self.plan["artifacts"].values():
            raw = self.artifacts[ref["path"]]
            self.assertEqual(len(raw), ref["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), ref["sha256"])
        result = assessor.assess(self.plan_bytes, self.artifacts)
        self.assertEqual(result["status"], "UNRESOLVED", result)
        self.assertEqual(result["reason_codes"], list(assessor.GAPS))
        self.assertEqual(result["evidence"], self.plan["artifacts"])
        self.assertEqual(result["facts"]["raw_rows"], 6)
        self.assertEqual(result["facts"]["decoded_rows"], 4)
        self.assertEqual(result["facts"]["unsupported_classic_rows"], 2)
        for field in assessor.TOP_FALSE:
            self.assertIs(result[field], False)

    def test_all_historical_inputs_are_critical(self):
        for role in assessor.ROLES[:3]:
            with self.subTest(role=role):
                self.setUp()
                del self.artifacts[self.plan["artifacts"][role]["path"]]
                result = self.refused()
                self.assertEqual(result["reason_codes"], ["HISTORICAL_INPUT_MISSING"])
                self.assertIn(role, result["details"][0])

    def test_each_remaining_missing_input_is_unresolved(self):
        for role in assessor.ROLES[3:]:
            with self.subTest(role=role):
                self.setUp()
                del self.artifacts[self.plan["artifacts"][role]["path"]]
                result = self.result()
                self.assertEqual(result["status"], "UNRESOLVED", result)
                self.assertEqual(result["facts"], {})
                self.assertIn(role, result["details"][0])
                self.assertIn(self.plan["artifacts"][role]["path"], result["details"][0])

    def test_all_byte_tampers_refuse_without_repin(self):
        for role in assessor.ROLES:
            with self.subTest(role=role):
                self.setUp()
                path = self.plan["artifacts"][role]["path"]
                self.artifacts[path] += b" "
                self.refused()

    def test_repin_cannot_replace_frozen_history(self):
        for role in assessor.ROLES[:3]:
            with self.subTest(role=role):
                self.setUp()
                value = self.data(role)
                value["custody_closed"] = True
                self.replace(role, value)
                self.refused()

    def test_plan_closed_fields_roles_and_false_flags(self):
        for kind in ("extra", "role_extra", "role_missing", "launch_true", "science_zero", "size_bool", "bad_hash"):
            with self.subTest(kind=kind):
                self.setUp()
                if kind == "extra":
                    self.plan["host_authenticated"] = True
                elif kind == "role_extra":
                    self.plan["artifacts"]["host"] = self.plan["artifacts"]["policy"]
                elif kind == "role_missing":
                    del self.plan["artifacts"]["policy"]
                elif kind == "launch_true":
                    self.plan["launch_authorized"] = True
                elif kind == "science_zero":
                    self.plan["scientific_admission"] = 0
                elif kind == "size_bool":
                    self.plan["artifacts"]["policy"]["bytes"] = True
                else:
                    self.plan["artifacts"]["policy"]["sha256"] = "A" * 64
                self.refused()

    def test_duplicate_and_nonfinite_json_refuse(self):
        for raw in (b'{"schema":1,"schema":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}'):
            with self.subTest(raw=raw):
                self.assertEqual(assessor.assess(raw, self.artifacts)["status"], "REFUSED")
                self.setUp()
                self.raw_replace("decoded_capture", raw)
                self.refused()

    def test_record_and_tree_bounds_refuse(self):
        for raw in (b" " * (assessor.v1.MAX_RECORD_BYTES + 1), b"[" * 20 + b"0" + b"]" * 20,
                    encode({"x": "a" * 4097}), b'{"x":1e10001}'):
            with self.subTest(length=len(raw)):
                self.setUp()
                self.raw_replace("decoded_capture", raw)
                self.refused()

    def test_paths_aliases_and_duplicate_roles_refuse(self):
        paths = ("/absolute", "../escape", "a/../b", "a//b", "a/./b", "a/NUL.txt", "C:/absolute", "a/end.")
        for path in paths:
            with self.subTest(path=path):
                self.setUp()
                self.plan["artifacts"]["policy"]["path"] = path
                self.refused()
        for aliased in (False, True):
            self.setUp()
            other = copy.deepcopy(self.plan["artifacts"]["decoded_capture"])
            if aliased:
                other["path"] = other["path"].upper()
            self.plan["artifacts"]["policy"] = other
            self.refused()

    def test_unplanned_or_nonbyte_map_refuses(self):
        self.artifacts["extra.json"] = b"{}"
        self.refused()
        self.setUp()
        self.artifacts[self.plan["artifacts"]["policy"]["path"]] = "text"
        self.refused()
        self.assertEqual(assessor.assess(self.plan, [])["status"], "REFUSED")

    def test_numeric_booleans_and_nested_authority_upgrades_refuse(self):
        for role, path, value in (("provider_capture", ("boundary_qualified",), True),
                                  ("decoded_capture", ("host_association_authenticated",), 0),
                                  ("decoded_capture", ("rows", 0, "event", "launch_authorized"), True),
                                  ("provider_root_qualification", ("scientific_admission",), True)):
            with self.subTest(role=role, path=path):
                self.setUp()
                data = self.data(role)
                target = data
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = value
                self.replace(role, data)
                self.join_changed_pins()
                self.refused()

    def test_missing_original_authority_flag_refuses(self):
        data = self.data("decoded_capture")
        del data["host_association_authenticated"]
        self.replace("decoded_capture", data)
        self.join_changed_pins()
        self.refused()

    def test_decoded_input_wrong_ref_refuses(self):
        data = self.data("decoded_capture")
        data["input"] = copy.deepcopy(self.plan["artifacts"]["historical_audit"])
        self.replace("decoded_capture", data)
        self.refused()

    def test_raw_row_hash_length_and_template_joins_refuse(self):
        for kind in ("row_hash", "event_length", "template_hash", "event_guid", "event_bool_id", "duplicate_row"):
            with self.subTest(kind=kind):
                self.setUp()
                data = self.data("decoded_capture")
                row = data["rows"][0]
                if kind == "row_hash":
                    row["raw_sha256"] = "0" * 64
                elif kind == "event_length":
                    row["event"]["raw"]["bytes"] += 1
                elif kind == "template_hash":
                    row["native_qualification"]["template"]["sha256"] = "0" * 64
                elif kind == "event_guid":
                    row["event"]["provider_guid"] = "0" * 36
                elif kind == "event_bool_id":
                    row["event"]["event_id"] = True
                else:
                    data["rows"][1] = copy.deepcopy(row)
                self.replace("decoded_capture", data)
                self.join_changed_pins()
                self.refused()

    def test_native_capture_hash_and_closure_refuse(self):
        for kind in ("raw", "closed", "errors", "clean_numeric"):
            with self.subTest(kind=kind):
                self.setUp()
                data = self.data("provider_capture")
                if kind == "raw":
                    data["queries"][0]["events"][0]["xml"] += " "
                elif kind == "closed":
                    data["native_handles_closed"] -= 1
                elif kind == "errors":
                    data["native_close_errors"] = ["error"]
                else:
                    data["native_handles_closed_cleanly"] = 1
                self.replace("provider_capture", data)
                self.join_changed_pins()
                self.refused()

    def test_query_projection_spec_and_gap_changes_refuse(self):
        for index, field, value in ((0, "spec", {}), (0, "selected_query_exhausted", 1),
                                     (4, "metadata_errors", []), (6, "errors", []), (0, "truncated", True)):
            with self.subTest(index=index, field=field):
                self.setUp()
                data = self.data("decoded_capture")
                data["queries"][index][field] = value
                self.replace("decoded_capture", data)
                self.join_changed_pins()
                self.refused()

    def test_repinning_both_query_gap_projections_cannot_erase_unknown(self):
        capture, decoded = self.data("provider_capture"), self.data("decoded_capture")
        capture["queries"][6]["errors"] = []
        decoded["queries"][6]["errors"] = []
        self.replace("provider_capture", capture)
        self.replace("decoded_capture", decoded)
        self.join_changed_pins()
        self.refused()

    def test_review_pins_roles_status_counts_and_root_ref_refuse(self):
        for kind in ("pin", "reviewer_author", "reviewer_source", "status", "count", "root_ref", "root_status"):
            with self.subTest(kind=kind):
                self.setUp()
                review, root = self.data("provider_actual_review"), self.data("provider_root_qualification")
                if kind == "pin":
                    review["artifact_pins"][self.plan["artifacts"]["provider_capture"]["path"]]["sha256"] = "0" * 64
                elif kind == "reviewer_author":
                    review["reviewer"] = review["source_authors"][0]
                elif kind == "reviewer_source":
                    review["reviewer"] = review["source_reviewer"]
                elif kind == "status":
                    review["status"] = "ACCEPTED"
                elif kind == "count":
                    review["observations"]["decoded"] = 5
                elif kind == "root_ref":
                    root["actual_review"] = copy.deepcopy(self.plan["artifacts"]["decoded_capture"])
                else:
                    root["status"] = "ELIGIBLE_FOR_LOCAL_ADMISSION_REVIEW"
                self.replace("provider_actual_review", review)
                if kind != "root_ref":
                    root["actual_review"] = copy.deepcopy(self.plan["artifacts"]["provider_actual_review"])
                self.replace("provider_root_qualification", root)
                self.refused()

    def test_decode_counts_classic_upgrade_and_generic_upgrade_refuse(self):
        for kind in ("decoded_count", "matched_count", "classic", "generic", "fresh"):
            with self.subTest(kind=kind):
                self.setUp()
                data = self.data("decoded_capture")
                if kind == "decoded_count":
                    data["decoded_count"] = True
                elif kind == "matched_count":
                    data["matched_native_count"] = 6
                elif kind == "classic":
                    data["rows"][4]["status"] = "DECODED"
                elif kind == "generic":
                    data["rows"][0]["generic_qualification"]["status"] = "QUALIFIED"
                else:
                    data["fresh_provider_observation"] = True
                self.replace("decoded_capture", data)
                self.join_changed_pins()
                self.refused()

    def test_boot_row_label_pid_and_template_never_close_host_gap(self):
        result = self.result()
        self.assertEqual(result["status"], "UNRESOLVED", result)
        self.assertIn("HOST_ASSOCIATION_UNESTABLISHED", result["reason_codes"])
        self.assertIn("RESTART_KIND_UNESTABLISHED", result["reason_codes"])
        self.assertIs(result["host_association_authenticated"], False)

    def test_candidate_validates_exact_frozen_schema_and_false_authority(self):
        candidate = self.candidate()
        schema = self.artifacts[self.plan["artifacts"]["disposition_schema"]["path"]]
        self.assertEqual(assessor.v1.validate_record("disposition", encode(candidate), {"disposition": schema}), candidate)
        self.assertEqual(candidate["status"], "UNRESOLVED")
        self.assertIsNone(candidate["current_boundary"])
        self.assertEqual(candidate["author"], "project_root")
        self.assertEqual(candidate["historical"]["status"], "FAILED_UNRELEASED_CONSUMED")
        self.assertTrue(1 <= len(candidate["limitations"]) <= 8)
        self.assertTrue(all(len(s) <= 512 for s in candidate["limitations"]))
        for field in ("custody_closed", "operation_released", "retry_allowed"):
            self.assertIs(candidate["historical"][field], False)
        self.assertIs(candidate["launch_authorized"], False)
        self.assertIs(candidate["scientific_admission"], False)

    def test_candidate_negative_refusal_remains_refused(self):
        del self.artifacts[self.plan["artifacts"]["historical_audit"]["path"]]
        self.assertEqual(self.candidate()["status"], "REFUSED")

    def test_candidate_invalid_uuid_or_calendar_timestamp_refuses(self):
        for identity in (IDENTITY.upper(), "../escape", "123", 7):
            with self.subTest(identity=identity), self.assertRaises(assessor.Error):
                self.candidate(disposition_id=identity)
        for stamp in ("2026-02-29T00:00:00Z", "2026-10-28T25:00:00Z", "2026-10-28T19:00:00.12345678Z",
                      "2026-10-28T19:00:00+00:00", "2026-10-28T19:00:60Z", 0):
            with self.subTest(stamp=stamp), self.assertRaises(assessor.Error):
                self.candidate(created_utc=stamp)
        for stamp in ("2026-10-28T19:00:00Z", "2026-10-28T19:00:00.1Z", STAMP):
            self.assertEqual(self.candidate(created_utc=stamp)["created_utc"], stamp)

    def test_candidate_schema_pin_or_bytes_changed_refuses(self):
        with self.assertRaises(assessor.Error):
            self.candidate(schema_bytes=b"{}")
        self.plan["artifacts"]["disposition_schema"]["sha256"] = hashlib.sha256(b"{}").hexdigest()
        self.plan["artifacts"]["disposition_schema"]["bytes"] = 2
        with self.assertRaises(assessor.Error):
            self.candidate(schema_bytes=b"{}")

    def test_candidate_rejects_forged_positive_or_open_assessment(self):
        for kind in ("positive", "boundary", "flag", "numeric_flag", "empty_codes", "remove_gap", "unknown_code",
                     "facts", "evidence", "extra", "long_detail", "history"):
            with self.subTest(kind=kind):
                result = self.result()
                if kind == "positive":
                    result["status"] = "ELIGIBLE_FOR_LOCAL_ADMISSION_REVIEW"
                elif kind == "boundary":
                    result["current_boundary"] = {"kind": "verified_complete_os_restart"}
                elif kind == "flag":
                    result["launch_authorized"] = True
                elif kind == "numeric_flag":
                    result["scientific_admission"] = 0
                elif kind == "empty_codes":
                    result["reason_codes"] = []
                elif kind == "remove_gap":
                    result["reason_codes"].pop()
                elif kind == "unknown_code":
                    result["reason_codes"] = ["HOST_AUTHENTICATED"]
                elif kind == "facts":
                    result["facts"]["decoded_rows"] = 6
                elif kind == "evidence":
                    result["evidence"]["provider_capture"]["sha256"] = "0" * 64
                elif kind == "extra":
                    result["authenticated"] = True
                elif kind == "long_detail":
                    result["details"] = ["x" * 513]
                else:
                    result["historical_status"] = "CLOSED"
                with self.assertRaises(assessor.Error):
                    self.candidate(result)


if __name__ == "__main__":
    unittest.main()
