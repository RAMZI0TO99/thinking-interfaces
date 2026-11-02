"""Unexecuted Q cases; Root injects one new owned JSON-only fixture directory."""

import hashlib
from pathlib import Path
import unittest

from . import manifest as m
from . import native_reader as nr
from ..v1.records import Refusal, canonical_bytes

FIXTURE_ROOT = None
RAW = b'{"fixture":1}'


def recipe(root="D:/fixture"):
    return {"schema": m.SCHEMA, "status": "PROPOSED", "limits": dict(m.LIMITS),
        "project_root": root, "selectors": [{"id": "json", "root": "project_root",
        "role": "fixture metadata", "trees": ["input"], "recursive_extensions": [".json"]}],
        "assertions": {k: False for k in ("historical_custody_repaired", "loader_abi_qualified",
        "launch_authorized", "physical_closure_established", "scientific_admission")}}


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.value = recipe()

    def refused(self):
        with self.assertRaises(Refusal):
            m.validate_recipe(self.value)

    def test_defensive_recipe_copy(self):
        result = m.validate_recipe(self.value)
        result["selectors"][0]["trees"].append("other")
        self.assertEqual(self.value["selectors"][0]["trees"], ["input"])

    def test_unknown_top_field(self):
        self.value["accepted"] = True
        self.refused()

    def test_unknown_selector_field(self):
        self.value["selectors"][0]["accept_missing"] = True
        self.refused()

    def test_schema(self):
        self.value["schema"] = "future"
        self.refused()

    def test_limit_cannot_increase(self):
        self.value["limits"]["files"] += 1
        self.refused()

    def test_limit_bool_not_int(self):
        self.value["limits"]["depth"] = True
        self.refused()

    def test_authority_false_exact(self):
        self.value["assertions"]["launch_authorized"] = 0
        self.refused()

    def test_duplicate_selector_id(self):
        self.value["selectors"] *= 2
        self.refused()

    def test_selector_root_known(self):
        self.value["selectors"][0]["root"] = "outside_root"
        self.refused()

    def test_relative_parent_alias(self):
        self.value["selectors"][0]["trees"] = ["input/../outside"]
        self.refused()

    def test_drive_wide_root(self):
        self.value["project_root"] = "D:/"
        self.refused()

    def test_optional_boolean_exact(self):
        self.value["selectors"][0]["optional_root"] = 1
        self.refused()

    def test_optional_alias_fields_refused(self):
        self.value["selectors"][0].update(optional_exact=[], exact_optional=[])
        self.refused()

    def test_case_alias_selector_list(self):
        self.value["selectors"][0]["trees"] = ["input", "INPUT"]
        self.refused()

    def test_exact_list_field_whitelist(self):
        self.value["selectors"][0]["exact_lists_from"] = ["plan.json:weights"]
        self.refused()

    def test_pin_bytes_boolean(self):
        with self.assertRaises(Refusal):
            m.validate_pins({"D:/fixture/a.json": {"bytes": True, "sha256": "a" * 64}})

    def test_pin_alias(self):
        with self.assertRaises(Refusal):
            m.validate_pins({p: {"bytes": 1, "sha256": "a" * 64}
                             for p in ("D:/fixture/a.json", "D:/fixture/A.json")})

    def test_pin_global_bytes(self):
        with self.assertRaises(Refusal):
            m.validate_pins({"D:/fixture/" + str(i) + ".json":
                {"bytes": 2147483648, "sha256": "a" * 64} for i in range(3)})

    def test_protected_data(self):
        with self.assertRaises(Refusal):
            m._forbidden("D:/fixture/data/raw/a.json")

    def test_executable_startup_and_weights(self):
        for suffix in (".pyc", ".pth", ".pt", ".ckpt", ".safetensors"):
            with self.subTest(suffix=suffix), self.assertRaises(Refusal):
                m._forbidden("D:/fixture/a" + suffix)

    def test_descriptor_sharding_boundary_without_disk_files(self):
        rows = [{"path": "D:/fixture/file" + str(i) + ".json", "bytes": 13,
                 "sha256": "a" * 64, "roles": ["metadata"]} for i in range(2049)]
        for count, lengths in ((0, []), (2048, [2048]), (2049, [2048, 1])):
            with self.subTest(count=count):
                pages = list(m.paginate(rows[:count]))
                self.assertEqual([len(page) for page in pages], lengths)
                self.assertEqual([row for page in pages for row in page], rows[:count])
                for page in pages:
                    self.assertLess(len(canonical_bytes({"rows": page})), 8 * 1024**2)

    def test_pagination_scalar_and_size_limits(self):
        for rows, size in (("rows", 2048), ([], True), ([], 0), ([], 2049)):
            with self.subTest(rows=rows, size=size), self.assertRaises(Refusal):
                list(m.paginate(rows, size))


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(FIXTURE_ROOT, "Root must inject owned fixture root")
        self.root = Path(FIXTURE_ROOT) / ('p2_' + self._testMethodName)
        self.root.mkdir()
        (self.root / "input").mkdir()
        (self.root / "outputs").mkdir()
        self.path = self.root / "input" / "a.json"
        self.path.write_bytes(RAW)
        self.value = recipe(self.root.as_posix())
        self.reader = nr.RetainedReader(lambda: True)
        self.addCleanup(self.reader.close)
        self.outputs = nr.RetainedOutputs(self.reader, (self.root / "outputs").as_posix())
        self.addCleanup(self.outputs.close)
        self.pins = {self.path.as_posix(): {"bytes": len(RAW), "sha256": hashlib.sha256(RAW).hexdigest()}}

    def test_real_prepare_pages_and_false_authority(self):
        prepared = m.prepare(self.reader, self.value, self.pins, self.outputs)
        self.assertEqual(prepared.index["files"], 1)
        self.assertEqual(prepared.index["status"], "PHYSICAL_MAP_OBSERVED_REVIEW_PENDING")
        self.assertFalse(prepared.index["launch_authorized"])
        self.assertTrue(prepared.verify())

    def test_real_extra_selected_before_prepare(self):
        (self.root / "input" / "b.json").write_bytes(RAW)
        with self.assertRaises(Refusal):
            m.prepare(self.reader, self.value, self.pins, self.outputs)

    def test_real_missing_pin_member(self):
        self.path.unlink()
        with self.assertRaises(Refusal):
            m.prepare(self.reader, self.value, self.pins, self.outputs)

    def test_real_changed_pin(self):
        self.path.write_bytes(b'{"fixture":2}')
        with self.assertRaises(Refusal):
            m.prepare(self.reader, self.value, self.pins, self.outputs)

    def test_real_added_unselected_file_detected(self):
        self.value["selectors"][0].pop("recursive_extensions")
        self.value["selectors"][0]["recursive_basenames"] = ["a.json"]
        selected = m.expand(self.value, self.reader)
        (self.root / "input" / "new.json").write_bytes(RAW)
        with self.assertRaises(Refusal):
            selected.verify()

    def test_real_excluded_directory_entry_detected(self):
        (self.root / "input" / "skip").mkdir()
        self.value["selectors"][0]["exclude_components"] = ["skip"]
        selected = m.expand(self.value, self.reader)
        (self.root / "input" / "skip").rmdir()
        with self.assertRaises(Refusal):
            selected.verify()

    def test_real_optional_absence_added_detected(self):
        self.value["selectors"][0]["optional_exact"] = ["absent/optional.json"]
        selected = m.expand(self.value, self.reader)
        (self.root / "absent").mkdir()
        (self.root / "absent" / "optional.json").write_bytes(RAW)
        with self.assertRaises(Refusal):
            selected.verify()

    def test_real_overlapping_selectors_merge_roles(self):
        self.value["selectors"].append({"id": "extra", "root": "project_root",
            "role": "second role", "exact": ["input/a.json"]})
        selected = m.expand(self.value, self.reader)
        self.assertEqual(len(selected.files), 1)
        self.assertEqual(len(selected.files[self.path.as_posix()]["roles"]), 2)

    def test_real_required_absence_refuses(self):
        self.value["required_absent_project_paths"] = ["input/a.json"]
        with self.assertRaises(Refusal):
            m.expand(self.value, self.reader)



