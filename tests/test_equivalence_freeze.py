from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.run_record import RunRecord
from evaluation.equivalence_freeze import source_margin_record, write_margin_once


class MarginFreezeTests(unittest.TestCase):
    def record(self, snapshot="original", margin=0.05):
        return RunRecord.create(
            config={"source_record_snapshot_sha256": snapshot, "frozen": True},
            seed=0,
            git_commit="test",
            dataset="d",
            fold="freeze",
            metrics={"margin": margin},
        )

    def test_idempotent_freeze_does_not_change_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "freeze.json"
            self.assertTrue(write_margin_once(self.record(), path))
            original = path.read_bytes()
            self.assertFalse(write_margin_once(self.record(), path))
            self.assertEqual(path.read_bytes(), original)

    def test_changed_source_or_result_requires_amendment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "freeze.json"
            write_margin_once(self.record(), path)
            original = path.read_bytes()
            for record in (self.record(snapshot="changed"), self.record(margin=0.06)):
                with self.assertRaises(ValueError):
                    write_margin_once(record, path)
                self.assertEqual(path.read_bytes(), original)

    def test_incomplete_source_cannot_freeze(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            source_margin_record(
                Path(directory),
                dataset="d",
                method="eegnet",
                subjects=("A", "B"),
                seeds=(11,),
                expected_config_sha256="hash",
                target_power=0.8,
                alpha=0.05,
            )
