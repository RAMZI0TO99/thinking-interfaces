"""Q protocol adversarial cases. In-memory only; no admissions are issued."""
import copy
import hashlib
import unittest
from . import protocol as p
from ..v1 import records as r


def request():
    digest = "1" * 64
    item = {"bytes": 1, "sha256": digest}
    return {"schema": "cho51_q_admission_v1", "stage": "Q",
      "operation_id": "11111111-1111-4111-8111-111111111111",
      "created_utc": "2026-10-29T00:00:00Z", "expires_utc": "2026-10-29T00:10:00Z",
      "root": "D:/Aenv/pro3", "python": "C:/Python/python.exe",
      "caller_runtime": {"path": "C:/PowerShell/pwsh.exe", "bytes": 1, "sha256": digest, "version": "7.6.5"},
      "runtime": {"root": "C:/Python", "files": {"C:/Python/python.exe": item.copy()},
      "recipe": "python.exe+root-dll+Lib-py-without-site-packages-or-pycache+DLLs-pyd-dll",
      "platform_trust": "reviewed-local-Windows-and-PowerShell-host-no-loaded-code-attestation"},
      "sources": {name: item.copy() for name in p.REQUIRED},
      "compiler": {"root":"C:/PowerShell", "files":{p:item.copy() for p in
          ('C:/PowerShell/Microsoft.CodeAnalysis.dll','C:/PowerShell/Microsoft.CodeAnalysis.CSharp.dll','C:/PowerShell/ref/System.Runtime.dll')}},
      "review": {"path": "source-review.json", **item},
      "adoption": {"path": "contract-adoption.json", **item},
      "predecessor": {"path": "runs/coordination/cho51_p3_q_qualification_20261029_q4/root-qualification.json", **item},
      "limits": p.LIMITS.copy(), "modes": list(p.MODES),
      "expected_tests": ["tools.local_validation.p2q2.test_protocol.ProtocolTests.test_complete_window"],
      "forbidden": p.FORBIDDEN.copy(), "scientific_admission": False}


def adoption(value):
    return {"schema": "cho51_q_contract_adoption_v2", "author": "project_root", "status": "ADOPTED_Q_ONLY",
      "created_utc": "2026-10-28T23:59:00Z", "contract_sha256": value["sources"][p.CONTRACT]["sha256"],
      "source_review_sha256": value["review"]["sha256"],
      "design_review_sha256": value["sources"][p.DESIGN_REVIEW]["sha256"],
      "supplement_sha256": value["sources"][p.SUPPLEMENT]["sha256"], **p.FALSES}


class ProtocolTests(unittest.TestCase):
    def validate(self, value):
        return p.validate_admission(value, "D:/Aenv/pro3", "2026-10-29T00:00:10Z")

    def test_complete_window(self):
        self.validate(request())
        p.window("2026-10-29T00:00:00Z", "2026-10-29T00:01:30Z", "2026-10-29T00:00:00Z")
        with self.assertRaises(ValueError):
            p.window("2026-10-29T00:00:00Z", "2026-10-29T00:01:29Z", "2026-10-29T00:00:00Z")

    def test_original_origin_not_reset_at_dispatch(self):
        with self.assertRaises(ValueError):
            p.window("2026-10-29T00:00:00Z", "2026-10-29T00:01:30Z", "2026-10-29T00:00:01Z")

    def test_closed_admission_and_wrong_stage(self):
        for key, value in (("unexpected", True), ("stage", "V"), ("scientific_admission", True),
                           ("operation_id", "11111111111141118111111111111111"), ("root", "D:/Aenv/pro3/sub")):
            item = request()
            item[key] = value
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_limits_exact_types_and_no_relaxation(self):
        for key, value in (("threads", True), ("gpu_visible", 0), ("work_seconds", 61), ("startup_ram_gib", 3)):
            item = request()
            item["limits"][key] = value
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_source_roster_missing_extra_or_boolean_pin(self):
        for mode in ("missing", "extra", "bool"):
            item = request()
            if mode == "missing":
                del item["sources"][p.REQUIRED[0]]
            elif mode == "extra":
                item["sources"]["outside.py"] = {"bytes": 1, "sha256": "1"*64}
            else:
                item["sources"][p.REQUIRED[0]]["bytes"] = True
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_runtime_path_alias_outside_recipe(self):
        for name in ("C:/Other/x.py", "C:/Python/../x.py", "c:/Python/x.py"):
            item = request()
            item["runtime"]["files"][name] = {"bytes": 1, "sha256": "1"*64}
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_runtime_executable_modes_and_effects(self):
        for key, value in (("python", "C:/Python/pythonw.exe"), ("modes", ["suite"]),
                           ("forbidden", []), ("expected_tests", ["other.test"])):
            item = request()
            item[key] = value
            with self.assertRaises(ValueError):
                self.validate(item)

    def test_duplicate_roster_and_changed_reference(self):
        item = request()
        item["expected_tests"] *= 2
        with self.assertRaises(ValueError):
            self.validate(item)
        item = request()
        item["adoption"]["path"] = "../grant.json"
        with self.assertRaises(ValueError):
            self.validate(item)

    def test_independent_review_exact_source_and_adoption_joins(self):
        item = request()
        review = {"status": "ACCEPTED_SOURCE_P2Q", "authors": ["author"], "reviewer": "reviewer", "sources": item["sources"]}
        p.validate_chain(item, review, adoption(item))
        for field, value in (("source_review_sha256", "2"*64), ("launch_authorized", True),
                             ("created_utc", "2026-10-29T00:01:00Z")):
            record = adoption(item)
            record[field] = value
            with self.assertRaises(ValueError):
                p.validate_chain(item, review, record)
        review["reviewer"] = "author"
        with self.assertRaises(ValueError):
            p.validate_chain(item, review, adoption(item))

    def test_report_omissions_failures_and_false_authority(self):
        expected = request()["expected_tests"]
        record = {"schema": "cho51_q_test_report_v1", "operation_id": "operation", "tests": expected,
          "tests_run": 1, "failures": 0, "errors": 0, "skipped": 0, "expected_failures": 0,
          "unexpected_successes": 0, "successful": True, "report": "ok",
          "fixture_files": 0, "fixture_bytes": 0, **p.FALSES}
        p.validate_report(record, expected, "operation")
        for key, value in (("tests_run", True), ("skipped", 1), ("errors", 1), ("tests", []),
                           ("launch_authorized", True), ("fixture_files", 241), ("successful", False)):
            changed = copy.deepcopy(record)
            changed[key] = value
            with self.assertRaises(ValueError):
                p.validate_report(changed, expected, "operation")

    def test_verified_bytes_exact_content_size_types(self):
        raw = b"fixture"
        pin = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        self.assertIs(p.verify_bytes(raw, pin), raw)
        for other in (raw + b"x", bytearray(raw), b"changed"):
            with self.assertRaises(ValueError):
                p.verify_bytes(other, pin)

    def test_nonfinite_duplicate_and_unknown_json_refuse(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":1e999}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                r.strict_loads(raw)

