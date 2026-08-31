from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.run_record import RunRecord


class RunRecordTests(unittest.TestCase):
    def test_complete_record_is_written(self) -> None:
        record = RunRecord.create(
            config={"model": "eegnet"},
            seed=11,
            git_commit="abc123",
            dataset="bci_iv_2a",
            fold="A01",
            metrics={"balanced_accuracy": 0.5},
            source_sha256="a" * 64,
            git_dirty=False,
        )
        with tempfile.TemporaryDirectory() as directory:
            output = record.write_json(Path(directory) / "record.json")
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["git_commit"], "abc123")
        self.assertEqual(payload["source_sha256"], "a" * 64)
        self.assertFalse(payload["git_dirty"])
        self.assertEqual(len(payload["config_sha256"]), 64)
        self.assertEqual(payload["metrics"]["balanced_accuracy"], 0.5)
        self.assertTrue(payload["timestamp_utc"].endswith("+00:00"))

    def test_record_config_is_detached_from_caller(self) -> None:
        config = {"model": {"name": "eegnet"}}
        record = RunRecord.create(
            config=config,
            seed=11,
            git_commit="abc123",
            dataset="bci_iv_2a",
            fold="A01",
            metrics={"balanced_accuracy": 0.5},
        )
        config["model"]["name"] = "changed"
        self.assertEqual(record.config["model"], {"name": "eegnet"})


if __name__ == "__main__":
    unittest.main()
