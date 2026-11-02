"""Q3-only JSON fixtures; no registry/global path or os/Path monkeypatch."""
import hashlib
import os
from pathlib import Path
import unittest

from . import native_reader as nr
from . import manifest as m
from .test_manifest import recipe
from ..v1.records import Refusal

FIXTURE_ROOT = None
RAW = b'{"long_path_fixture":1}'


class TransportTests(unittest.TestCase):
    def test_transport_preserves_canonical_spelling(self):
        path = "D:/fixture/" + "a" * 200 + "/" + "b" * 80 + ".json"
        self.assertGreater(len(path), 260)
        self.assertEqual(nr.transport(path), "\\\\?\\" + path.replace("/", "\\"))

    def test_transport_rejects_device_unc_and_aliases(self):
        for path in ("\\\\?\\D:\\fixture\\a.json", "//server/share/a.json", "D:/fixture/../a.json",
                     "D:/fixture/CON.json", "d:/fixture/a.json", "D:/fixture/a.json."):
            with self.subTest(path=path), self.assertRaises(Refusal):
                nr.transport(path)


class NativeLongPathTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(FIXTURE_ROOT, "Root injects owned fixture directory")
        self.root = Path(FIXTURE_ROOT).as_posix() + "/" + self._testMethodName
        os.mkdir(nr.transport(self.root))
        self.reader = nr.RetainedReader(lambda: True)
        self.addCleanup(self.reader.close)

    def write(self, path):
        with open(nr.transport(path), "xb") as stream:
            stream.write(RAW)
        return {"bytes": len(RAW), "sha256": hashlib.sha256(RAW).hexdigest()}

    def deep(self):
        current = self.root
        for index in range(3):
            current += "/" + str(index) + "d" * 65
            os.mkdir(nr.transport(current))
        self.assertGreater(len(current), 260)
        return current

    def test_long_leaf_retains_canonical_descriptor(self):
        path = self.root + "/" + "leaf" + "x" * 170 + ".json"
        self.assertGreater(len(path), 260)
        pin = self.write(path)
        descriptor = self.reader.retain(path, pin)
        self.assertEqual(descriptor["path"], path)
        self.assertFalse(descriptor["path"].startswith("\\\\?\\"))
        self.assertEqual(self.reader.read_small(path, pin), RAW)
        self.reader.verify()

    def test_long_directory_enumeration_and_original_retention(self):
        directory = self.deep()
        path = directory + "/input.json"
        pin = self.write(path)
        snapshot = self.reader.observe_tree(self.root, "long", "metadata")
        self.assertEqual([f["path"] for f in snapshot["files"]], [path])
        with self.assertRaises(OSError):
            with open(nr.transport(path), "r+b"):
                pass
        self.assertEqual(self.reader.read_small(path, pin), RAW)

    def test_long_census_detects_added_unselected_json(self):
        directory = self.deep()
        self.write(directory + "/selected.json")
        value = recipe(self.root)
        value["selectors"][0].pop("trees")
        value["selectors"][0].pop("recursive_extensions")
        value["selectors"][0]["recursive_basenames"] = ["selected.json"]
        selected = m.expand(value, self.reader)
        self.write(directory + "/unselected.json")
        with self.assertRaises(Refusal):
            selected.verify()

    def test_long_optional_absence_is_resampled(self):
        directory = self.deep()
        value = recipe(self.root)
        value["selectors"] = [{"id": "optional", "root": "project_root", "role": "metadata",
                                "optional_exact": [directory[len(self.root)+1:] + "/absent.json"]}]
        selected = m.expand(value, self.reader)
        self.write(directory + "/absent.json")
        with self.assertRaises(Refusal):
            selected.verify()

    def test_long_output_keeps_original_canonical_identity(self):
        directory = self.deep()
        outputs = nr.RetainedOutputs(self.reader, directory)
        self.addCleanup(outputs.close)
        descriptor = outputs.write("output.json", RAW)
        self.assertEqual(descriptor["path"], directory + "/output.json")
        self.assertGreater(len(descriptor["path"]), 260)
        self.assertEqual(outputs.verify(), [descriptor])

    def test_long_exact_reader_refuses_prefixed_caller_spelling(self):
        directory = self.deep()
        path = directory + "/input.json"
        pin = self.write(path)
        with self.assertRaises(Refusal):
            self.reader.retain(nr.transport(path), pin)
        self.reader.retain(path, pin)




