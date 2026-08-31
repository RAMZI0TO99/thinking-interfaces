from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evaluation.leakage_ci import run_leakage_ci


class LeakageCITests(unittest.TestCase):
    def test_missing_evidence_fails_without_weakening_disjointness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = run_leakage_ci(Path(directory))
            self.assertTrue(report.subject_disjointness_passed)
            self.assertFalse(report.shuffled_label_passed)
            self.assertFalse(report.pre_cue_passed)
