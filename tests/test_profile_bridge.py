from __future__ import annotations

import copy
import unittest
from dataclasses import asdict

import numpy as np

from core.config import config_digest, load_toml
from core.metrics import classification_report
from core.run_record import RunRecord
from scripts.diagnose_profile_bridge import (
    NAMES,
    ROOT,
    array_identity,
    bridge_cooling_policy,
    independent_split,
    ordered_summary,
    reconstruct_condition,
    validate_config,
    validate_record,
)


class ProfileBridgeTests(unittest.TestCase):
    def test_real_cooling_configuration_path(self):
        policy = bridge_cooling_policy()
        self.assertEqual(policy.pause_at_celsius, 80)
        self.assertEqual(policy.resume_at_or_below_celsius, 76)
        self.assertEqual(policy.maximum_cooling_sleep_seconds, 60.0)

    def setUp(self):
        self.config = load_toml(ROOT / "configs/profile_bridge_diagnostic.toml")
        self.original = load_toml(ROOT / "configs/profile_comparison.toml")
        self.artifact = {
            "labels": np.tile(["feet", "left_hand", "right_hand", "tongue"], 144),
            "sessions": np.repeat(["0train", "1test"], 288),
        }
        self.split = independent_split(self.artifact)

    def test_fixed_recipe_and_complete_order(self):
        validate_config(self.config, self.original)
        for change in ("order", "missing", "scale", "output", "guard", "seed", "epochs"):
            config, original = copy.deepcopy(self.config), copy.deepcopy(self.original)
            if change == "order":
                config["conditions"].reverse()
            elif change == "missing":
                config["conditions"].pop()
            elif change == "scale":
                config["conditions"][2]["input_scale"] = 1.0
            elif change == "output":
                config["output_directory"] = "runs/benchmark"
            elif change == "guard":
                config["runtime"]["stop_below_free_memory_gib"] = 3.0
            elif change == "seed":
                original["comparison"]["seed"] = 23
            else:
                original["comparison"]["epochs"] = 2
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_config(config, original)

    def test_original_partition_and_class_inventory(self):
        self.assertEqual({key: len(value) for key, value in self.split.items()},
                         {"train": 230, "validation": 58, "test": 288})
        self.assertEqual(self.split["test"], list(range(288, 576)))
        self.assertEqual(independent_split(self.artifact), self.split)
        self.assertFalse(set(self.split["train"]) & set(self.split["validation"]))
        changed = copy.deepcopy(self.artifact)
        changed["labels"][0] = "tongue"
        with self.assertRaises(ValueError):
            independent_split(changed)

    def test_ordered_differences_not_winner_selection(self):
        scores = dict(zip(NAMES, (0.25, 0.36, 0.44, 0.4, 0.53, 0.57, 0.56), strict=True))
        result = ordered_summary(scores)
        self.assertFalse(result["scientific_gate_approved"])
        self.assertEqual(len(result["ordered_conditional_changes"]), 6)
        self.assertAlmostEqual(result["endpoint_gap_pp"], 31.0)
        self.assertAlmostEqual(sum(row["difference_pp"]
                                   for row in result["ordered_conditional_changes"]), 31.0)
        self.assertLess(result["ordered_conditional_changes"][2]["difference_pp"], 0)
        for bad in (dict(reversed(list(scores.items()))), {**scores, NAMES[2]: float("nan")},
                    {**scores, NAMES[3]: 1.01}, {key: value for key, value in scores.items()
                                               if key != NAMES[-1]}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ordered_summary(bad)

    def test_storage_units_and_input_hash_do_not_silently_change(self):
        signals = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
        artifacts = {"profile_b": {"signals": signals}}
        for condition in self.config["conditions"][:2]:
            actual = reconstruct_condition(condition, artifacts, {}, lambda: None)
            self.assertIs(actual, signals)
        self.assertEqual(array_identity(signals), array_identity(signals.copy(order="F")))
        self.assertNotEqual(array_identity(signals), array_identity(signals * 100))
        self.assertNotEqual(array_identity(signals), array_identity(signals.reshape(4, 3, 2)))

    def test_current_record_checks_reject_tampering(self):
        condition = self.config["conditions"][4]
        context = {"source_sha256": "b" * 64}
        resolved = {"context_sha256": config_digest(context), "condition": condition}
        targets = self.artifact["labels"][self.split["test"]].tolist()
        classes = sorted(set(targets))
        report = classification_report(targets, targets, labels=classes).as_dict()
        record = RunRecord.create(config=resolved, seed=11, dataset="bci_iv_2a",
                                  fold="profile_bridge:subject_01:a_rate", git_commit="a" * 40,
                                  source_sha256=context["source_sha256"], git_dirty=False,
                                  metrics={"balanced_accuracy": 1.0, "cohen_kappa": 1.0,
                                           "fit_seconds": 1.0})
        identity = {"shape": [576, 22, 512], "dtype": "float32", "sha256": "c" * 64}
        payload = {
            "record": asdict(record), "context_sha256": config_digest(context),
            "split": self.split, "signal_identity": identity, "query_targets": targets,
            "query_probabilities": [[float(label == target) for label in classes]
                                    for target in targets],
            "result": {"metrics": report, "epochs_completed": 20, "best_epoch": 20,
                       "best_validation_loss": 1.0, "device": "cuda",
                       "split_counts": {key: len(value) for key, value in self.split.items()},
                       "history": [{"epoch": i + 1, "train_loss": float(20 - i),
                                    "validation_loss": float(20 - i)} for i in range(20)]},
            "resource_observations": {"minimum_observed_free_memory_gib": 5.0,
                                      "model_call_checks": 200},
        }
        expected = {"context": context, "condition": condition, "split": self.split,
                    "targets": targets, "identity": identity}
        validate_record(payload, **expected)
        for change in ("source", "dirty", "input", "split", "history", "prediction", "memory"):
            bad = copy.deepcopy(payload)
            if change == "source":
                bad["record"]["source_sha256"] = "d" * 64
            elif change == "dirty":
                bad["record"]["git_dirty"] = True
            elif change == "input":
                bad["signal_identity"]["sha256"] = "d" * 64
            elif change == "split":
                bad["split"]["train"][0] = bad["split"]["test"][0]
            elif change == "history":
                bad["result"]["history"].pop()
            elif change == "prediction":
                bad["query_probabilities"][0] = [0.0, 1.0, 0.0, 0.0]
            else:
                bad["resource_observations"]["minimum_observed_free_memory_gib"] = 3.9
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_record(bad, **expected)


if __name__ == "__main__":
    unittest.main()
