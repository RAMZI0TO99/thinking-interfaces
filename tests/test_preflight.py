from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.preflight import ROOT, dataset_status


class DatasetPreflightTests(unittest.TestCase):
    def test_current_registry_can_start_without_private_data(self) -> None:
        report = dataset_status(ROOT / "configs" / "datasets.toml")
        self.assertEqual(report["enabled_access_blockers"], [])
        self.assertEqual(
            set(report["pending_agreements"]),
            {"TUH Abnormal EEG Corpus", "TUH EEG Events Corpus"},
        )

    def test_enabled_unconfirmed_agreement_is_a_blocker(self) -> None:
        content = """
[datasets.private]
display_name = "Private EEG"
enabled = true
access = "agreement_required"
status = "agreement_not_confirmed"
needed_by_week = 6
""".strip()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datasets.toml"
            path.write_text(content, encoding="utf-8")
            report = dataset_status(path)
        self.assertEqual(report["enabled_access_blockers"], ["Private EEG"])

    def test_invalid_status_is_rejected(self) -> None:
        content = """
[datasets.bad]
display_name = "Bad"
enabled = true
access = "public"
status = "unknown"
needed_by_week = 1
""".strip()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datasets.toml"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid status"):
                dataset_status(path)


if __name__ == "__main__":
    unittest.main()

