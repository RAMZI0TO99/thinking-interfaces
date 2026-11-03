"""Declared CM1 supplied-data cases. No real import/discovery or execution claim."""
import unittest
from ..hb1.common import Refusal, bounded_bytes
from . import collection as c, registry


def yes():
    return True


def encoded(value):
    return bounded_bytes(value, 1_048_576, yes)


def report():
    rows = []
    for name in registry.expected_ids():
        module, cls, method = name.rsplit(".", 2)
        rows.append(dict(id=name, module=module, class_name=cls, method_name=method,
                         source_module=module, source_qualname=cls + "." + method,
                         skipped=False, deselected=False, expected_failure=False, xfail=False))
    return dict(schema="cho51_cm1_supplied_collection_v1", complete=True, tests=rows,
                modules=[dict(module=n, bytes=b, sha256=s, loader=c.LOADER,
                              load_tests=False, partial=False) for n, b, s in registry.expected_modules()])


def checked(value):
    return c.verify_collection(encoded(value), check=yes)


def bootstrap():
    return dict(schema="cho51_cm1_bootstrap_model_v1", stdlib_shadows=[],
                source_packages_preloaded=[], unknown_imports=[])


def restoration():
    return dict(schema="cho51_cm1_restoration_model_v1", namespace="a" * 64, importer="b" * 64,
                surfaces=[dict(surface=n, present=not n.endswith(".absent"),
                               identity=None if n.endswith(".absent") else "c" * 64)
                          for n in c.PATCH_SURFACES])


class CM1CollectionTests(unittest.TestCase):
    def test_exact_full_roster_before_selection(self):
        result = checked(report())
        self.assertEqual((len(result.ids), len(result.selection)), (732, 216))
        self.assertEqual(result.ids, registry.expected_ids())
        self.assertFalse(result.authenticated)
        self.assertFalse(result.execution_accepted)
        self.assertNotEqual(result.report_sha256, result.projection_sha256)
        for raw in (encoded(report())[:-1], b" " + encoded(report()), b"x" * 1_048_577):
            with self.assertRaises(Refusal): c.verify_collection(raw, check=yes)
        with self.assertRaises(Refusal): c.verify_collection(encoded(report()), check=lambda: False)

    def test_missing_extra_equal_count_refuse(self):
        for mode in ("missing", "extra", "substitute", "reverse"):
            value = report()
            if mode == "missing": value["tests"].pop()
            if mode == "extra": value["tests"].append(value["tests"][0])
            if mode == "substitute": value["tests"][-1]["id"] += "_alien"
            if mode == "reverse": value["tests"].reverse()
            with self.subTest(mode=mode), self.assertRaises(Refusal): checked(value)

    def test_duplicate_identity_refuse(self):
        value = report(); value["tests"][-1] = dict(value["tests"][0])
        with self.assertRaises(Refusal): checked(value)
        value = report(); value["modules"][-1] = dict(value["modules"][0])
        with self.assertRaises(Refusal): checked(value)

    def test_module_pin_drift_refuse(self):
        for key, replacement in (("bytes", 1), ("bytes", True), ("sha256", "0" * 64), ("module", "alias")):
            value = report(); value["modules"][0][key] = replacement
            with self.subTest(key=key), self.assertRaises(Refusal): checked(value)

    def test_class_method_alias_refuse(self):
        for key in ("class_name", "method_name", "source_module", "source_qualname", "module"):
            value = report(); value["tests"][0][key] += "_alias"
            with self.subTest(key=key), self.assertRaises(Refusal): checked(value)

    def test_dynamic_load_tests_refuse(self):
        value = report(); value["modules"][0]["load_tests"] = True
        with self.assertRaises(Refusal): checked(value)

    def test_unexpected_loader_refuse(self):
        for loader in ("custom", None, 1):
            value = report(); value["modules"][0]["loader"] = loader
            with self.subTest(loader=loader), self.assertRaises(Refusal): checked(value)

    def test_skip_xfail_deselection_refuse(self):
        for key in ("skipped", "xfail", "deselected", "expected_failure"):
            for replacement in (True, 0, None):
                value = report(); value["tests"][0][key] = replacement
                with self.subTest(key=key, replacement=replacement), self.assertRaises(Refusal): checked(value)

    def test_partial_module_refuse(self):
        value = report(); value["modules"][0]["partial"] = True
        with self.assertRaises(Refusal): checked(value)
        for key, replacement in (("complete", False), ("complete", 1), ("schema", "old")):
            value = report(); value[key] = replacement
            with self.assertRaises(Refusal): checked(value)

    def test_stdlib_shadow_refuse(self):
        value = bootstrap()
        self.assertEqual(c.verify_bootstrap(encoded(value), check=yes), ("SUPPLIED_MODEL_ONLY", False))
        value["stdlib_shadows"] = ["hashlib"]
        with self.assertRaises(Refusal): c.verify_bootstrap(encoded(value), check=yes)

    def test_source_package_preload_refuse(self):
        for key in ("source_packages_preloaded", "unknown_imports"):
            value = bootstrap(); value[key] = ["tools.local_validation.cm1"]
            with self.assertRaises(Refusal): c.verify_bootstrap(encoded(value), check=yes)

    def test_exact_namespace_bijection(self):
        value = dict(schema="cho51_cm1_namespace_model_v1",
                     bindings=[dict(source=n, target=n) for n in registry.expected_ids()])
        self.assertEqual(c.verify_namespace(encoded(value), check=yes), ("SUPPLIED_MODEL_ONLY", False))
        for mode in ("alias", "duplicate", "missing", "reorder"):
            rows = [dict(r) for r in value["bindings"]]
            if mode == "alias": rows[0]["target"] += "_alias"
            if mode == "duplicate": rows[-1] = rows[0]
            if mode == "missing": rows.pop()
            if mode == "reorder": rows.reverse()
            bad = dict(value, bindings=rows)
            with self.subTest(mode=mode), self.assertRaises(Refusal): c.verify_namespace(encoded(bad), check=yes)

    def test_all_runner_cases_join_roster(self):
        value = report()
        self.assertEqual(len(registry.CM_IDS), 32)
        self.assertTrue(set(registry.CM_IDS).issubset(checked(value).selection))
        value["tests"] = [r for r in value["tests"] if r["id"] not in registry.CM_IDS]
        with self.assertRaises(Refusal): checked(value)

    def test_mock_surface_restoration(self):
        before = encoded(restoration())
        self.assertEqual(c.verify_restoration(before, before, check=yes), ("SUPPLIED_MODEL_ONLY", False))
        for key in ("namespace", "importer"):
            after = restoration(); after[key] = "d" * 64
            with self.assertRaises(Refusal): c.verify_restoration(before, encoded(after), check=yes)
        after = restoration(); after["surfaces"][0]["identity"] = "d" * 64
        with self.assertRaises(Refusal): c.verify_restoration(before, encoded(after), check=yes)
        after = restoration(); after["surfaces"][5].update(present=True, identity="d" * 64)
        with self.assertRaises(Refusal): c.verify_restoration(before, encoded(after), check=yes)

    def test_unregistered_patch_refuse(self):
        for mode in ("extra", "rename", "omit"):
            value = restoration()
            if mode == "extra": value["surfaces"].append(dict(surface="os.remove", present=True, identity="d" * 64))
            if mode == "rename": value["surfaces"][0]["surface"] = "os.remove"
            if mode == "omit": value["surfaces"].pop()
            with self.assertRaises(Refusal): c.verify_restoration(encoded(restoration()), encoded(value), check=yes)

    def test_selection_never_discharges_cohorts(self):
        facts = checked(report())
        self.assertEqual(len(set(facts.ids) - set(facts.selection)), 516)
        self.assertFalse(facts.execution_accepted)
        with self.assertRaises(AttributeError): facts.ids = ()
        value = report(); value["expected_roster"] = []
        with self.assertRaises(Refusal): checked(value)
