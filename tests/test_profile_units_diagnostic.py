from __future__ import annotations

import copy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core.metrics import classification_report
from scripts.diagnose_profile_units import (
    ROOT,
    guarded_constructor,
    make_resource_guard,
    resolve_config,
    validate_predictions,
)


class ProfileUnitsDiagnosticTests(unittest.TestCase):
    def setUp(self):
        classes = ["a", "b", "c", "d"]
        targets = classes * 72
        report = classification_report(targets, targets, labels=classes).as_dict()
        self.payload = {
            "result": {
                "metrics": report,
                "epochs_completed": 20,
                "best_epoch": 20,
                "best_validation_loss": 1.0,
                "history": [
                    {
                        "epoch": float(i + 1),
                        "train_loss": float(20 - i),
                        "validation_loss": float(20 - i),
                    }
                    for i in range(20)
                ],
            },
            "query_targets": targets,
            "query_probabilities": [
                [float(label == target) for label in classes] for target in targets
            ],
            "split": {
                "train": list(range(230)),
                "validation": list(range(230, 288)),
                "test": list(range(288, 576)),
            },
            "record": {"metrics": {"balanced_accuracy": 1.0, "cohen_kappa": 1.0}},
        }

    def test_exact_predictions_and_history(self):
        validate_predictions(self.payload)

    def test_resource_hook_records_and_stops_before_forward(self):
        memory = SimpleNamespace(available=5 * 1024**3)
        process = SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=1024**3))
        provider = SimpleNamespace(virtual_memory=lambda: memory, Process=lambda: process)
        guard, observations = make_resource_guard(provider, 4.0)
        callbacks = []
        model = SimpleNamespace(register_forward_pre_hook=callbacks.append)
        wrapped = guarded_constructor(lambda: model, guard)
        self.assertIs(wrapped(), model)
        self.assertIsNone(callbacks[0](model, ()))
        self.assertEqual(observations["minimum_observed_free_memory_gib"], 5.0)
        self.assertEqual(observations["maximum_observed_process_rss_gib"], 1.0)
        memory.available = 3 * 1024**3
        with self.assertRaisesRegex(RuntimeError, "before a model call"):
            callbacks[0](model, ())
        self.assertEqual(observations["model_call_checks"], 2)

    def test_prediction_or_split_tampering_is_rejected(self):
        for key, value in (
            ("query_probabilities", [[float("nan")] * 4] * 288),
            ("query_targets", ["b"] * 288),
            (
                "split",
                {
                    "train": list(range(230)),
                    "validation": list(range(230, 288)),
                    "test": list(range(288)),
                },
            ),
        ):
            payload = copy.deepcopy(self.payload)
            payload[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_predictions(payload)

    def test_truncated_history_is_not_a_complete_fit(self):
        payload = copy.deepcopy(self.payload)
        payload["result"]["history"] = payload["result"]["history"][:2]
        with self.assertRaisesRegex(ValueError, "history"):
            validate_predictions(payload)

    def test_preserves_three_conditions_and_separate_output(self):
        path = ROOT / "configs/profile_units_diagnostic.toml"
        config, original, output = resolve_config(path)
        self.assertTrue(output.is_relative_to(ROOT / "runs/profile_units_diagnostic"))
        self.assertEqual(config["conditions"]["profile_b_microvolts"]["input_scale"], 100.0)
        for change in ("condition", "output"):
            changed = copy.deepcopy(config)
            if change == "condition":
                changed["conditions"]["profile_b_microvolts"]["input_scale"] = 10.0
            else:
                changed["diagnostic"]["output_directory"] = "runs/benchmark"
            with (
                patch(
                    "scripts.diagnose_profile_units.tomllib.loads", side_effect=[changed, original]
                ),
                self.subTest(change=change),
                self.assertRaises(ValueError),
            ):
                resolve_config(Path(path))


if __name__ == "__main__":
    unittest.main()
