"""Fresh guard predicates and deferred final verification; Q4 fixtures only."""
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest

from . import supervisor as s
from . import manifest as m
from . import native_reader as nr
from .test_manifest import recipe
from ..v1.records import Refusal

FIXTURE_ROOT = None
RAW = b'{"fixture":1}'


class FreshAbsenceTests(unittest.TestCase):
    def fake(self):
        leaf = str(Path("D:/fixture/stop.json"))
        state = {"leaf": "absent", "ancestor": 0x10, "calls": []}
        def query(path, *, follow_symlinks):
            self.assertIs(follow_symlinks, False)
            state["calls"].append(path)
            if path == leaf:
                if state["leaf"] == "absent":
                    raise FileNotFoundError(path)
                if state["leaf"] == "unknown":
                    raise PermissionError(path)
                return SimpleNamespace(st_file_attributes=0)
            return SimpleNamespace(st_file_attributes=state["ancestor"])
        return leaf, state, query

    def test_cached_lexical_tuple_still_resamples_every_ancestor_and_leaf(self):
        leaf, state, query = self.fake()
        expected = (*s.lexical_ancestors(leaf), leaf)
        s.absent(leaf, query)
        s.absent(leaf, query)
        self.assertEqual(tuple(state["calls"]), expected + expected)

    def test_changed_ancestor_reparse_or_nondirectory_refuses_after_cache_hit(self):
        leaf, state, query = self.fake()
        s.absent(leaf, query)
        for attributes in (0x410, 0, 0x50):
            with self.subTest(attributes=attributes):
                state["ancestor"] = attributes
                with self.assertRaises(ValueError):
                    s.absent(leaf, query)

    def test_unknown_leaf_never_becomes_cached_absence(self):
        leaf, state, query = self.fake()
        s.absent(leaf, query)
        state["leaf"] = "unknown"
        with self.assertRaises(PermissionError):
            s.absent(leaf, query)

    def test_present_leaf_refuses_after_previous_true_absence(self):
        leaf, state, query = self.fake()
        s.absent(leaf, query)
        state["leaf"] = "present"
        with self.assertRaisesRegex(ValueError, "required absent path exists"):
            s.absent(leaf, query)


class ProvisionalPreparationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(FIXTURE_ROOT)
        self.root = Path(FIXTURE_ROOT) / self._testMethodName
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

    def prepared(self):
        prepared = m.prepare(self.reader, self.value, self.pins, self.outputs)
        self.assertFalse(prepared.index["final_input_verification_established"])
        self.assertFalse(prepared.index["launch_authorized"])
        return prepared

    def test_added_selected_member_after_provisional_publication_refuses_final_verify(self):
        prepared = self.prepared()
        (self.root / "input" / "b.json").write_bytes(RAW)
        with self.assertRaises(Refusal):
            prepared.verify()
        self.assertFalse(prepared.index["final_input_verification_established"])

    def test_added_unselected_member_after_provisional_publication_refuses_final_verify(self):
        self.value["selectors"][0].pop("recursive_extensions")
        self.value["selectors"][0]["recursive_basenames"] = ["a.json"]
        prepared = self.prepared()
        (self.root / "input" / "unselected.json").write_bytes(RAW)
        with self.assertRaises(Refusal):
            prepared.verify()

    def test_optional_absence_changed_after_provisional_publication_refuses_final_verify(self):
        self.value["selectors"][0]["optional_exact"] = ["optional.json"]
        prepared = self.prepared()
        (self.root / "optional.json").write_bytes(RAW)
        with self.assertRaises(Refusal):
            prepared.verify()




