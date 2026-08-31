from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from adaptation.episodic import adapt_torch_model
from core.run_record import RunRecord
from evaluation.baselines import BraindecodeClassifier, TorchTrainingConfig
from evaluation.benchmark import DatasetMatrix
from evaluation.support_adaptation import source_then_support_fold
from evaluation.support_adaptation_audit import audit_support_adaptation


class SupportAdaptationTests(unittest.TestCase):
    def test_source_fit_and_support_adaptation_receive_only_their_own_trials(self):
        rng = np.random.default_rng(3)
        signals = rng.normal(size=(36, 3, 256)).astype(np.float32)
        matrix = DatasetMatrix(
            "synthetic",
            signals,
            np.asarray(["left", "right"] * 18),
            np.asarray(["A"] * 12 + ["B"] * 12 + ["C"] * 12),
            ("C3", "Cz", "C4"),
            128.0,
        )
        seen = []
        original_fit = BraindecodeClassifier.fit

        def fit_spy(classifier, epochs, labels):
            seen.append((epochs.copy(), labels.copy()))
            return original_fit(classifier, epochs, labels)

        with (
            patch.object(BraindecodeClassifier, "fit", new=fit_spy),
            patch(
                "evaluation.support_adaptation.adapt_torch_model", wraps=adapt_torch_model
            ) as adaptation,
        ):
            result = source_then_support_fold(
                matrix,
                target_subject="C",
                seed=11,
                shots_per_class=2,
                training=TorchTrainingConfig(epochs=1, batch_size=8, device="cpu"),
                adaptation_steps=2,
                adaptation_learning_rate=0.001,
            )
        np.testing.assert_array_equal(seen[0][0], signals[:24])
        np.testing.assert_array_equal(adaptation.call_args.args[1].numpy(), signals[24:28])
        np.testing.assert_array_equal(adaptation.call_args.args[2].numpy(), [0, 1, 0, 1])
        self.assertEqual(len(seen), 1)
        metrics = result["metrics"]
        self.assertEqual(metrics["source_trials"], 24)
        self.assertEqual(metrics["support_trials"], 4)
        self.assertEqual(metrics["query_trials"], 8)
        self.assertEqual(metrics["parameters_changed"], 1)
        self.assertEqual(metrics["base_model_unchanged"], 1)
        self.assertEqual(metrics["adaptation_steps"], 2)
        self.assertGreater(metrics["maximum_probability_change"], 0)
        self.assertEqual(metrics["class_support_left"], 4)
        self.assertEqual(metrics["class_support_right"], 4)
        settings = {
            "episode": {
                "dataset": "synthetic",
                "seeds": [11],
                "included_labels": ["left", "right"],
                "shots_per_class": 2,
            },
            "adaptation": {"steps": 2},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "seed_11" / "C.json"
            RunRecord.create(
                config={
                    "settings": settings,
                    "benchmark_config_sha256": "benchmark",
                    "split": result["split"],
                },
                seed=11,
                git_commit="test",
                dataset="synthetic",
                fold="C",
                metrics=metrics,
            ).write_json(path)
            audit = audit_support_adaptation(
                root, settings=settings, subjects=("C",), benchmark_sha256="benchmark"
            )
            self.assertTrue(audit["complete"], audit)
            payload = json.loads(path.read_text())
            payload["metrics"]["balanced_accuracy"] = -0.1
            path.write_text(json.dumps(payload))
            audit = audit_support_adaptation(
                root, settings=settings, subjects=("C",), benchmark_sha256="benchmark"
            )
            self.assertFalse(audit["complete"])
            self.assertEqual(len(audit["invalid_records"]), 1)

    def test_unknown_target_fails_before_training(self):
        matrix = DatasetMatrix(
            "d",
            np.zeros((4, 3, 256), dtype=np.float32),
            np.asarray(["left", "right"] * 2),
            np.asarray(["A"] * 4),
            ("C3", "Cz", "C4"),
            128.0,
        )
        with self.assertRaises(ValueError):
            source_then_support_fold(
                matrix,
                target_subject="missing",
                seed=11,
                shots_per_class=1,
                training=TorchTrainingConfig(epochs=1, device="cpu"),
                adaptation_steps=1,
                adaptation_learning_rate=0.001,
            )
