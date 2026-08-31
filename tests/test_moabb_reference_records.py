from __future__ import annotations

import copy
import unittest
from dataclasses import asdict

from sklearn.model_selection import StratifiedKFold

from core.run_record import RunRecord
from evaluation.moabb_reference_plan import ReferenceUnit
from evaluation.moabb_reference_records import binary_auc, validate_reference_record


class MoabbReferenceRecordTests(unittest.TestCase):
    def setUp(self):
        # Synthetic full-record fixture; no test fixture is written as a scientific run.
        self.unit = ReferenceUnit(42, 1, "0train", 0)
        self.config = {"fixture": "synthetic"}
        self.raw = {"A01T.mat": "a" * 64, "A01E.mat": "b" * 64}
        targets = [0, 1] * 72
        train, query = next(
            StratifiedKFold(5, shuffle=True, random_state=42).split(range(144), targets)
        )
        split_at = int(len(train) * 0.8)
        query_targets = [targets[index] for index in query]
        probabilities = [[0.8, 0.2] if target == 0 else [0.2, 0.8] for target in query_targets]
        record = RunRecord.create(
            config=self.config,
            seed=42,
            git_commit="1" * 40,
            dataset="bci_iv_2a",
            fold=self.unit.key,
            source_sha256="2" * 64,
            git_dirty=False,
            metrics={"roc_auc": 1.0, "fit_seconds": 20.0, "prediction_seconds": 0.1},
        )
        self.payload = {
            "unit": asdict(self.unit),
            "execution_sha256": "3" * 64,
            "record": asdict(record),
            "result": {
                "fold_executed": True,
                "reference_reproduction_passed": False,
                "resource_stop": False,
                "restore_best_weights": False,
                "raw_path_redirect_only": True,
                "raw_file_sha256": self.raw,
                "session_targets": targets,
                "classes": ["left_hand", "right_hand"],
                "session_trials": 144,
                "native_epoch_shape": [144, 22, 1001],
                "channel_names": [f"channel{i}" for i in range(22)],
                "session_original_indices": list(range(144)),
                "query_indices": query.tolist(),
                "optimization_indices": train[:split_at].tolist(),
                "validation_indices": train[split_at:].tolist(),
                "query_targets": query_targets,
                "query_probabilities": probabilities,
                "transformed_query_shape": [len(query), 22, 513],
                "transformed_query_sha256": "4" * 64,
                "epochs_completed": 300,
                "early_stopping_epoch": 0,
                "history": {
                    "loss": [0.7] * 300,
                    "val_loss": [0.7 - 0.0001 * epoch for epoch in range(300)],
                },
                "roc_auc": 1.0,
                "fit_seconds": 20.0,
                "prediction_seconds": 0.1,
            },
        }

    def validate(self, payload):
        return validate_reference_record(
            payload,
            unit=self.unit,
            resolved_config=self.config,
            execution_sha256="3" * 64,
            raw_hashes=self.raw,
        )

    def test_complete_full_record_and_early_stop_are_validated(self):
        self.assertEqual(self.validate(self.payload), 1.0)
        early = copy.deepcopy(self.payload)
        early["result"].update(
            epochs_completed=76,
            early_stopping_epoch=75,
            history={"loss": [0.7] * 76, "val_loss": [0.7] * 76},
        )
        self.assertEqual(self.validate(early), 1.0)

    def test_smoke_truncation_and_protocol_drift_are_rejected(self):
        changes = {
            "epochs_completed": 2,
            "early_stopping_epoch": 17,
            "resource_stop": True,
            "restore_best_weights": True,
            "fold_executed": False,
            "transformed_query_shape": [29, 22, 512],
            "roc_auc": 0.99,
            "history": {"loss": [0.7] * 300},
            "raw_file_sha256": {},
        }
        for key, value in changes.items():
            payload = copy.deepcopy(self.payload)
            payload["result"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(payload)

    def test_split_label_and_probability_tampering_is_rejected(self):
        for key, value in (
            ("query_indices", list(reversed(self.payload["result"]["query_indices"]))),
            ("optimization_indices", self.payload["result"]["validation_indices"]),
            ("query_targets", [False] * 29),
            ("query_probabilities", [[float("nan"), 0.0]] * 29),
            ("session_targets", [0] * 144),
            ("session_original_indices", list(range(144, 288))),
        ):
            payload = copy.deepcopy(self.payload)
            payload["result"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(payload)

    def test_record_and_execution_identity_tampering_is_rejected(self):
        for key, value in (
            ("git_dirty", True),
            ("seed", 42.0),
            ("fold", "different"),
            ("config_sha256", "0" * 64),
            ("git_commit", "unversioned"),
        ):
            payload = copy.deepcopy(self.payload)
            payload["record"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(payload)
        payload = copy.deepcopy(self.payload)
        payload["execution_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.validate(payload)

    def test_auc_definition_handles_ties(self):
        self.assertEqual(binary_auc([0, 1], [[0.5, 0.5], [0.5, 0.5]]), 0.5)
        self.assertEqual(binary_auc([0, 1], [[0.2, 0.8], [0.8, 0.2]]), 0)
        with self.assertRaises(ValueError):
            binary_auc([False, True], [[0.5, 0.5], [0.5, 0.5]])

    def test_history_must_obey_the_actual_patience_rule(self):
        payload = copy.deepcopy(self.payload)
        payload["result"]["history"]["val_loss"] = [0.7] * 300
        with self.assertRaisesRegex(ValueError, "early-stopping rule"):
            self.validate(payload)
        payload = copy.deepcopy(self.payload)
        payload["result"].update(
            epochs_completed=76,
            early_stopping_epoch=75,
            history={"loss": [0.7] * 76, "val_loss": [0.7 - 0.0001 * i for i in range(76)]},
        )
        with self.assertRaisesRegex(ValueError, "does not justify"):
            self.validate(payload)


if __name__ == "__main__":
    unittest.main()
