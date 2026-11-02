"""P1 Q fixtures; execution only by separately admitted Root supervisor."""

import hashlib
import os
from pathlib import Path
import unittest

from . import preparation as p
from ..v1.records import Refusal, canonical_bytes

FIXTURE_ROOT = None
RAW = b'{"fixture":1}'


def recipe(root="D:/fixture"):
    return {"schema": p.SCHEMA, "scope_roots": [root], "groups": [
        {"label": role, "role": role, "kind": "tree", "root": root + "/" + role,
         "seeds": [root + "/" + role + "/input.json"], "suffixes": [".json"], "excluded_dirs": [],
         "pins": [{"path": root + "/" + role + "/input.json", "bytes": len(RAW),
                   "sha256": hashlib.sha256(RAW).hexdigest()}]}
        for role in ("source", "runtime", "package", "metadata")]}


class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.value = recipe()

    def refused(self):
        with self.assertRaises(Refusal):
            p.validate_recipe(self.value)

    def test_closed_recipe_roundtrip_and_defensive_copy(self):
        result = p.parse_recipe(canonical_bytes(self.value))
        result["groups"][0]["pins"][0]["bytes"] = 0
        self.assertEqual(self.value["groups"][0]["pins"][0]["bytes"], len(RAW))

    def test_schema_version(self):
        self.value["schema"] = "future"
        self.refused()

    def test_no_caller_success_flag(self):
        self.value["coverage_review_established"] = True
        self.refused()

    def test_no_caller_review_text(self):
        self.value["groups"][0]["review"] = "accepted"
        self.refused()

    def test_missing_role(self):
        self.value["groups"][0]["role"] = "runtime"
        self.refused()

    def test_alias_path(self):
        self.value["groups"][0]["pins"][0]["path"] = "D:/fixture/source/../input.json"
        self.refused()

    def test_overlapping_groups(self):
        self.value["groups"][1]["root"] = "D:/fixture/source/child"
        self.refused()

    def test_outside_scope(self):
        self.value["groups"][0]["root"] = "D:/outside"
        self.refused()

    def test_drive_scope(self):
        self.value["scope_roots"] = ["D:/"]
        self.refused()

    def test_scope_case_alias(self):
        self.value["scope_roots"].append("D:/FIXTURE")
        self.refused()

    def test_wildcard_suffix(self):
        self.value["groups"][0]["suffixes"] = [".*"]
        self.refused()

    def test_empty_suffix(self):
        self.value["groups"][0]["suffixes"] = []
        self.refused()

    def test_boolean_size(self):
        self.value["groups"][0]["pins"][0]["bytes"] = True
        self.refused()

    def test_file_byte_limit(self):
        self.value["groups"][0]["pins"][0]["bytes"] = 2 * 1024**3 + 1
        self.refused()

    def test_aggregate_byte_limit(self):
        for g in self.value["groups"]:
            g["pins"][0]["bytes"] = 2 * 1024**3
        self.refused()

    def test_excluded_expected_member(self):
        g = self.value["groups"][0]
        g["excluded_dirs"] = ["child"]
        g["pins"][0]["path"] = g["root"] + "/child/input.json"
        self.refused()

    def test_unpinned_seed(self):
        self.value["groups"][0]["seeds"] = ["D:/fixture/source/missing.json"]
        self.refused()

    def test_exact_file_recipe(self):
        g = self.value["groups"][3]
        g.update(kind="file", root=g["pins"][0]["path"], suffixes=[])
        self.assertEqual(p.validate_recipe(self.value)["groups"][3]["kind"], "file")

    def test_exact_file_no_expansion(self):
        g = self.value["groups"][3]
        g.update(kind="file", root=g["pins"][0]["path"])
        self.refused()

    def test_duplicate_and_nonfinite_json(self):
        for raw in (b'{"schema":1,"schema":2}', b'{"n":NaN}', b'{"n":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(Refusal):
                p.parse_recipe(raw)

    def test_json_depth_and_report_bounds(self):
        with self.assertRaises(Refusal):
            p.parse_recipe(b"[" * 33 + b"0" + b"]" * 33)
        with self.assertRaises(Refusal):
            p.parse_recipe(b" " * (8 * 1024**2 + 1))


class NativePreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not isinstance(FIXTURE_ROOT, Path) or not FIXTURE_ROOT.is_absolute():
            raise AssertionError("admitted runner must inject fresh attempt-owned FIXTURE_ROOT")
        with p.nr.RetainedReader(lambda: True) as reader:
            reader.retain_directory(FIXTURE_ROOT)

    def setUp(self):
        self.root = FIXTURE_ROOT / self._testMethodName
        self.root.mkdir()
        self.value = recipe(str(self.root).replace("\\", "/"))
        for g in self.value["groups"]:
            directory = Path(g["root"])
            directory.mkdir()
            with (directory / "input.json").open("xb") as stream:
                stream.write(RAW)
        self.session = p.PreparationSession(self.value, lambda: True)
        self.addCleanup(self.session.close)

    def file(self, role="source", name="input.json"):
        return self.root / role / name

    def add_file(self, role="source", name="extra.json"):
        with self.file(role, name).open("xb") as stream:
            stream.write(RAW)

    def test_real_all_roles_retained_no_authority(self):
        report = self.session.observe()
        self.assertEqual(report["proposal"]["file_count"], 4)
        self.assertFalse(report["coverage_review_established"])
        self.assertFalse(report["proposal"]["complete_manifest"])
        self.assertFalse(report["launch_authorized"])
        self.assertEqual(self.session.verify(), report)

    def test_real_missing_expected_input(self):
        self.file().unlink()
        with self.assertRaises(Refusal):
            self.session.observe()

    def test_real_extra_selected_input_before_observation(self):
        self.add_file()
        with self.assertRaises(Refusal):
            self.session.observe()

    def test_real_changed_pin(self):
        self.file().write_bytes(b'{"fixture":2}')
        with self.assertRaises(Refusal):
            self.session.observe()

    def test_real_added_member_after_initial_census(self):
        self.session.observe()
        self.add_file()
        with self.assertRaises(Refusal):
            self.session.verify()

    def test_real_added_unselected_directory_member(self):
        self.session.observe()
        (self.root / "source" / "new_directory").mkdir()
        with self.assertRaises(Refusal):
            self.session.verify()

    def test_real_missing_unselected_directory_member(self):
        directory = self.root / "source" / "empty_directory"
        directory.mkdir()
        self.session.observe()
        # Retained directory handle prevents ordinary removal; the final census
        # also guards membership without relying on this sharing denial alone.
        with self.assertRaises(OSError):
            directory.rmdir()
        self.session.verify()

    def test_failed_observation_cannot_be_retried(self):
        self.add_file()
        with self.assertRaises(Refusal):
            self.session.observe()
        self.file(name="extra.json").unlink()
        with self.assertRaises(Refusal):
            self.session.observe()

    def test_real_input_writer_and_delete_denied(self):
        self.session.observe()
        with self.assertRaises(OSError):
            with self.file().open("r+b"):
                self.fail("retained writer opened")
        with self.assertRaises(OSError):
            self.file().unlink()
        self.session.verify()

    def test_real_hardlink_refused(self):
        os.link(self.file(), self.file(name="alias.json"))
        with self.assertRaises(Refusal):
            self.session.observe()

    def test_injected_reparse_predicate_before_bytes(self):
        original = p.nr.os.stat
        target = str(self.file()).replace("\\", "/")
        class Reparse:
            st_file_attributes = 0x400
        def stat(path, *args, **kwargs):
            if str(path).replace("\\", "/") == target:
                return Reparse()
            return original(path, *args, **kwargs)
        p.nr.os.stat = stat
        try:
            with self.assertRaises(Refusal):
                self.session.observe()
        finally:
            p.nr.os.stat = original

    def test_real_exact_metadata_file_and_closed_session(self):
        self.session.close()
        g = self.value["groups"][3]
        g.update(kind="file", root=g["pins"][0]["path"], suffixes=[])
        self.session = p.PreparationSession(self.value, lambda: True)
        self.addCleanup(self.session.close)
        self.assertEqual(self.session.observe()["proposal"]["file_count"], 4)
        self.session.close()
        with self.assertRaises(Refusal):
            self.session.verify()

    def test_real_refused_checkpoint(self):
        self.session.reader.checkpoint = lambda: False
        with self.assertRaises(Refusal):
            self.session.observe()

    def test_recipe_and_report_defensive_views(self):
        view = self.session.recipe
        view["groups"].clear()
        report = self.session.observe()
        report["recipe"]["groups"].clear()
        self.assertEqual(len(self.session.verify()["recipe"]["groups"]), 4)
