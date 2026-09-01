from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from evaluation.reference_environment import resource_gate, startup_runtime, verify_reference_files


class ReferenceEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.runtime = {"minimum_free_memory_gib": 10.0,
                        "stop_below_free_memory_gib": 4.0,
                        "minimum_free_disk_gib": 10.0}

    def test_resource_gate_defers_at_actual_limit(self):
        for memory, disk, expected in ((10, 10, True), (9.9, 30, False), (12, 9.9, False)):
            with self.subTest(memory=memory, disk=disk):
                result = resource_gate(self.runtime, free_memory_gib=memory, free_disk_gib=disk)
                self.assertEqual(result["ready"], expected)

    def test_nonfinite_or_invalid_resources_rejected(self):
        for invalid in (float("nan"), float("inf"), -1):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                resource_gate(self.runtime, free_memory_gib=invalid, free_disk_gib=30)
        for stop in (0, 10, 11):
            with self.subTest(stop=stop), self.assertRaises(ValueError):
                resource_gate({**self.runtime, "stop_below_free_memory_gib": stop},
                              free_memory_gib=11, free_disk_gib=30)

    def test_operational_startup_override_preserves_other_limits(self):
        self.assertEqual(startup_runtime(self.runtime), self.runtime)
        lowered = startup_runtime(self.runtime, 8.0)
        self.assertEqual(lowered["minimum_free_memory_gib"], 8.0)
        self.assertEqual(lowered["stop_below_free_memory_gib"], 4.0)
        self.assertEqual(lowered["minimum_free_disk_gib"], 10.0)
        self.assertEqual(self.runtime["minimum_free_memory_gib"], 10.0)
        for invalid in (4.0, 3.9, 10.1, float("nan"), float("inf")):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                startup_runtime(self.runtime, invalid)

    def test_source_verification_checks_bytes_and_containment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = root / "site"
            site.mkdir()
            (site / "model.py").write_bytes(b"# reference\n")
            (root / "outside.py").write_bytes(b"# reference\n")
            digest = hashlib.sha256(b"# reference\n").hexdigest()
            self.assertEqual(verify_reference_files(site, {"model.py": digest}),
                             {"model.py": digest})
            for manifest in ({}, {"model.py": "0" * 64}, {"../outside.py": digest}):
                with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                    verify_reference_files(site, manifest)


if __name__ == "__main__":
    unittest.main()
