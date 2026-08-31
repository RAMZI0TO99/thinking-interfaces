from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from core.config import load_toml
from evaluation.moabb_reference_plan import ReferencePlan
from scripts.run_moabb_reference import ROOT, audit, execute_unit, resolve_config


class MoabbReferenceRunnerTests(unittest.TestCase):
    def setUp(self):
        self.config_path = ROOT / "configs/moabb_reference_evaluation.toml"
        self.config = load_toml(self.config_path)
        self.plan = ReferencePlan.from_config(self.config)
        self.environment = load_toml(ROOT / self.config["paths"]["environment_config"])

    def test_empty_grid_is_not_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            report = audit(self.config, self.plan, self.environment, Path(directory))
        self.assertFalse(report["complete"])
        self.assertEqual(report["expected_fits"], 450)
        self.assertEqual(len(report["missing_units"]), 450)
        self.assertEqual(report["valid_fits"], 0)
        self.assertFalse(report["scientific_gate_approved"])
        self.assertNotIn("summary", report)

    def test_stray_results_and_locks_are_visible_not_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "stray.json").write_text("{}", encoding="utf-8")
            (output / "pending.lock").write_text("fixture", encoding="utf-8")
            report = audit(self.config, self.plan, self.environment, output)
            self.assertEqual(report["unexpected_files"], ["stray.json"])
            self.assertEqual(report["pending_locks"], ["pending.lock"])
            self.assertFalse(report["complete"])

    def test_corrupt_record_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            path = output / f"{self.plan.units[0].key}.json"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"{incomplete")
            report = audit(self.config, self.plan, self.environment, output)
            self.assertIn(self.plan.units[0].key, report["invalid_units"])
            self.assertEqual(path.read_bytes(), b"{incomplete")

    def test_reference_outputs_cannot_enter_main_benchmark(self):
        config = copy.deepcopy(self.config)
        config["paths"]["output_directory"] = "runs/benchmark"
        with (
            patch(
                "scripts.run_moabb_reference.tomllib.loads", side_effect=[config, self.environment]
            ),
            self.assertRaisesRegex(ValueError, "separate"),
        ):
            resolve_config(self.config_path)

    def test_invalid_unit_selector_fails_before_training(self):
        for index in (-1, 450):
            with self.subTest(index=index), self.assertRaises(ValueError):
                execute_unit(
                    self.config_path, self.config, self.plan, self.environment, ROOT, index
                )

    def test_low_resources_defer_without_importing_training_path(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            receipt = output / "receipt.json"
            receipt.write_text(
                json.dumps({"training_ready": False, "resources": {"ready": False}}),
                encoding="utf-8",
            )
            completed = subprocess.CompletedProcess(
                [], 0, stdout=json.dumps({"report": str(receipt)})
            )
            expected_prefix = str(ROOT / self.environment["environment"]["directory"])
            with (
                patch("scripts.run_moabb_reference.sys.prefix", expected_prefix),
                patch("scripts.run_moabb_reference.require_smoke"),
                patch("scripts.run_moabb_reference.subprocess.run", return_value=completed),
                patch("scripts.smoke_moabb_reference.run_reference_fold") as trainer,
                redirect_stdout(StringIO()),
            ):
                self.assertEqual(
                    execute_unit(
                        self.config_path,
                        self.config,
                        self.plan,
                        self.environment,
                        output / "results",
                        0,
                    ),
                    2,
                )
                trainer.assert_not_called()
            self.assertFalse((output / "results").exists())


if __name__ == "__main__":
    unittest.main()
