from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.config import config_digest, load_toml
from evaluation.leakage_ci import verified_control_summary


class ControlSummaryTests(unittest.TestCase):
    def make_evidence(self, root):
        (root / "configs").mkdir()
        (root / "runs/control").mkdir(parents=True)
        (root / "configs/control.toml").write_text(
            "[gate_a]\nsubjects = [1, 2]\nseeds = [11]\nmaximum = 0.6\n"
            '[output]\nsummary = "runs/control/summary.json"\nruns_root = "runs/control"\n'
        )
        settings = load_toml(root / "configs/control.toml")["gate_a"]
        rows = []
        for subject in (1, 2):
            name = f"runs/control/subject_{subject}.json"
            embedded = {"gate_a": settings, "resolved": {"subject": subject, "seed": 11}}
            (root / name).write_text(
                json.dumps(
                    {
                        "config": embedded,
                        "config_sha256": config_digest(embedded),
                        "seed": 11,
                        "metrics": {"balanced_accuracy": 0.5},
                    }
                )
            )
            rows.append(
                {"subject": subject, "seed": 11, "run_record": name, "balanced_accuracy": 0.5}
            )
        summary = {
            "passed": True,
            "maximum": 0.6,
            "runs": rows,
            "balanced_accuracy": {
                "subject_count": 2,
                "subject_means": {"1": 0.5, "2": 0.5},
                "mean": 0.5,
            },
        }
        path = root / "runs/control/summary.json"
        path.write_text(json.dumps(summary))
        return path, summary

    def verify(self, root):
        return verified_control_summary(
            root, "control.toml", flag_key="passed", limit_key="maximum"
        )

    def test_verified_records_pass_but_a_boolean_alone_does_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _ = self.make_evidence(root)
            self.assertTrue(self.verify(root))
            path.write_text('{"passed": true}')
            self.assertFalse(self.verify(root))

    def test_missing_duplicate_and_tampered_results_fail(self):
        for fault in ("missing", "duplicate", "mean", "threshold", "config", "record"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path, summary = self.make_evidence(root)
                if fault == "missing":
                    summary["runs"].pop()
                elif fault == "duplicate":
                    summary["runs"].append(summary["runs"][0])
                elif fault == "mean":
                    summary["balanced_accuracy"]["mean"] = 0.4
                elif fault == "threshold":
                    summary["maximum"] = 1.0
                elif fault == "config":
                    source = root / "configs/control.toml"
                    source.write_text(source.read_text().replace("0.6", "0.9"))
                else:
                    source = root / "runs/control/subject_1.json"
                    record = json.loads(source.read_text())
                    record["metrics"]["balanced_accuracy"] = 0.4
                    source.write_text(json.dumps(record))
                path.write_text(json.dumps(summary))
                self.assertFalse(self.verify(root))
