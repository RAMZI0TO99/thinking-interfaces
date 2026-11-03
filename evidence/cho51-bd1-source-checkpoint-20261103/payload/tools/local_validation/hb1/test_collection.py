"""Exact report mutations; these do not discover or execute the reported tests."""
import unittest

from .collection import LOADER, expected_ids, expected_modules, verify_collection
from .common import Refusal, bounded_bytes


def yes():
    return True


def report():
    tests = []
    for test_id in expected_ids():
        module, class_name, method_name = test_id.rsplit(".", 2)
        tests.append({"id": test_id, "module": module, "class_name": class_name,
                      "method_name": method_name, "source_module": module,
                      "source_qualname": class_name + "." + method_name,
                      "skipped": False, "deselected": False, "expected_failure": False, "xfail": False})
    return {"schema": "cho51_hb1_supplied_collection_v1", "complete": True,
            "modules": [{"module": n, "bytes": b, "sha256": s, "loader": LOADER,
                         "load_tests": False, "partial": False} for n, b, s in expected_modules()],
            "tests": tests}


def checked(value):
    return verify_collection(bounded_bytes(value, 1048576, yes), check=yes)


class ExactCollectionTests(unittest.TestCase):
    def test_complete_literal_roster_is_untrusted_data_only(self):
        result = checked(report())
        self.assertEqual(result.ids, expected_ids())
        self.assertEqual(result.evidence_kind, "UNAUTHENTICATED")
        self.assertFalse(result.authenticated)
        self.assertFalse(result.execution_accepted)

    def test_original_partitions_and_verifier_selection(self):
        result = checked(report()); partitions = dict(result.partitions)
        self.assertEqual([len(partitions[n]) for n in ("probe32", "mechanisms100", "inherited384",
                         "qd10", "sc_hash_ram19", "sc_publisher35")], [32, 100, 384, 10, 19, 35])
        self.assertEqual(len(result.verifier_selection), 64 + len(partitions["hb_new"]))

    def test_count_equivalent_substitution_refuses(self):
        value = report(); value["tests"][0]["id"] += "_substitute"
        with self.assertRaises(Refusal): checked(value)

    def test_duplicates_missing_extra_and_order_refuse(self):
        for action in ("duplicate", "missing", "extra", "order"):
            value = report()
            if action == "duplicate": value["tests"][-1] = dict(value["tests"][0])
            if action == "missing": value["tests"].pop()
            if action == "extra": value["tests"].append(dict(value["tests"][0]))
            if action == "order": value["tests"].reverse()
            with self.subTest(action=action), self.assertRaises(Refusal): checked(value)

    def test_alias_source_and_qualname_refuse(self):
        for key in ("module", "class_name", "method_name", "source_module", "source_qualname"):
            value = report(); value["tests"][0][key] += "_alias"
            with self.subTest(key=key), self.assertRaises(Refusal): checked(value)

    def test_skip_and_deselection_refuse(self):
        for key in ("skipped", "deselected", "expected_failure", "xfail"):
            for invalid in (True, 0, None):
                value = report(); value["tests"][0][key] = invalid
                with self.subTest(key=key, invalid=invalid), self.assertRaises(Refusal): checked(value)

    def test_incomplete_and_wrong_schema_refuse(self):
        for key, replacement in (("complete", False), ("complete", 1), ("schema", "other")):
            value = report(); value[key] = replacement
            with self.subTest(key=key), self.assertRaises(Refusal): checked(value)

    def test_module_pin_and_count_refuse(self):
        for key, replacement in (("sha256", "0" * 64), ("bytes", True), ("bytes", 1), ("module", "alias")):
            value = report(); value["modules"][0][key] = replacement
            with self.subTest(key=key), self.assertRaises(Refusal): checked(value)
        value = report(); value["modules"].pop()
        with self.assertRaises(Refusal): checked(value)

    def test_unknown_loader_hook_and_partial_module_refuse(self):
        for key, replacement in (("loader", "custom"), ("load_tests", True), ("partial", True)):
            value = report(); value["modules"][0][key] = replacement
            with self.subTest(key=key), self.assertRaises(Refusal): checked(value)

    def test_module_duplicate_and_order_refuse(self):
        value = report(); value["modules"][-1] = dict(value["modules"][0])
        with self.assertRaises(Refusal): checked(value)
        value = report(); value["modules"].reverse()
        with self.assertRaises(Refusal): checked(value)

    def test_caller_roster_or_unknown_fields_cannot_override(self):
        for location in ("root", "module", "test"):
            value = report()
            target = value if location == "root" else value["modules" if location == "module" else "tests"][0]
            target["expected_roster"] = []
            with self.subTest(location=location), self.assertRaises(Refusal): checked(value)

    def test_hb_omission_is_not_hidden_by_prefix_selection(self):
        value = report()
        value["tests"] = [r for r in value["tests"] if not r["id"].startswith("tools.local_validation.hb1.")]
        with self.assertRaises(Refusal): checked(value)

    def test_report_cap_duplicate_keys_and_guard(self):
        for raw in (b" " * 1048577, b'{"complete":true,"complete":true}'):
            with self.subTest(length=len(raw)), self.assertRaises(Refusal):
                verify_collection(raw, check=yes)
        with self.assertRaises(Refusal): verify_collection(b"{}", check=lambda: False)

    def test_result_defensive_immutable_and_no_projection(self):
        value = report(); result = checked(value); first = result.ids[0]
        value["tests"][0]["id"] = "mutated"
        self.assertEqual(result.ids[0], first)
        with self.assertRaises(AttributeError): result.ids = ()
        self.assertFalse(hasattr(result, "claim_operation"))
