"""Write-once control record publication and retry behavior."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import refresh_source_bound_controls as refresh


class AtomicJsonTests(unittest.TestCase):
    def test_new_record_and_exact_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "nested" / "context.json"
            payload = {"z": [2, 1], "a": {"value": True}}
            refresh.atomic_json(path, payload)
            expected = (
                json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
            ).replace("\n", os.linesep).encode("utf-8")
            self.assertEqual(path.read_bytes(), expected)
            refresh.atomic_json(path, payload)
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual(sorted(item.name for item in path.parent.iterdir()), ["context.json"])

    def test_conflicting_record_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "unit.json"
            refresh.atomic_json(path, {"value": 1})
            original = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "existing control evidence differs"):
                refresh.atomic_json(path, {"value": 2})
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(sorted(item.name for item in path.parent.iterdir()), ["unit.json"])

    def test_retry_accepts_record_from_previous_text_writer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "context.json"
            payload = {"nested": {"subject": 1}, "seed": 11}
            with path.open("w", encoding="utf-8") as stream:
                json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write("\n")
            original = path.read_bytes()
            refresh.atomic_json(path, payload)
            self.assertEqual(path.read_bytes(), original)

    def test_other_writer_claiming_path_first_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "unit.json"

            def competing_claim(_source: Path, destination: Path) -> None:
                destination.write_bytes(b'{"other": true}\n')
                raise FileExistsError(destination)

            with (
                patch.object(refresh.os, "link", side_effect=competing_claim),
                self.assertRaisesRegex(ValueError, "existing control evidence differs"),
            ):
                refresh.atomic_json(path, {"value": 1})
            self.assertEqual(path.read_bytes(), b'{"other": true}\n')
            self.assertEqual(sorted(item.name for item in path.parent.iterdir()), ["unit.json"])


if __name__ == "__main__":
    unittest.main()
