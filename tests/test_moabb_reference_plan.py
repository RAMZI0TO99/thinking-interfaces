from __future__ import annotations

import copy
import math
import unittest
from pathlib import Path

from core.config import load_toml
from evaluation.moabb_reference_plan import ReferencePlan, ReferenceUnit, summarize_reference_scores


class MoabbReferencePlanTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.config = load_toml(root / "configs/moabb_reference_evaluation.toml")
        self.plan = ReferencePlan.from_config(self.config)

    def test_reference_anchor_is_separate_from_four_repeats(self):
        self.assertEqual(len(self.plan.units), 450)
        self.assertEqual(len(set(self.plan.units)), 450)
        self.assertEqual(sum(unit.model_seed == 42 for unit in self.plan.units), 90)
        self.assertEqual(self.plan.units[0].key, "seed_42/subject_01/0train/fold_0")
        self.assertEqual(self.plan.units[-1].key, "seed_53/subject_09/1test/fold_4")

    def test_incomplete_or_changed_protocol_cannot_appear_as_full_reference(self):
        changes = {
            "reference": {"subjects": [1], "sessions": ["0train"], "split_seed": 11,
                          "repeat_model_seeds": [42, 11, 23, 37], "fold_count": 5.0,
                          "published_roc_auc": 0.74},
            "training": {"epochs": 2, "restore_best_weights": True, "batch_size": 16},
            "preprocessing": {"fmax": 30.0, "common_average_reference": True},
        }
        for section, fields in changes.items():
            for key, value in fields.items():
                config = copy.deepcopy(self.config)
                config[section][key] = value
                with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                    ReferencePlan.from_config(config)

    def test_unknown_acceptance_threshold_is_rejected(self):
        config = copy.deepcopy(self.config)
        config["reference"]["pass_tolerance"] = 0.1
        with self.assertRaises(ValueError):
            ReferencePlan.from_config(config)

    def test_fold_identity_rejects_ambiguous_numeric_types_and_paths(self):
        for values in ((42.0, 1, "0train", 0), (42, True, "0train", 0),
                       (42, 1, "../0train", 0), (42, 1, "0train", True),
                       (-1, 1, "0train", 0)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                ReferenceUnit(*values)

    def test_fold_and_seed_scores_do_not_inflate_subject_count(self):
        observations = [(unit, 0.9 if unit.model_seed == 42 else 0.5 + unit.subject / 100)
                        for unit in self.plan.units]
        result = summarize_reference_scores(self.plan, observations)
        self.assertAlmostEqual(result["per_seed"]["42"]["mean_roc_auc"], 0.9)
        self.assertAlmostEqual(result["four_seed_subject_interval"]["mean"], 0.55)
        self.assertEqual(result["four_seed_subject_interval"]["subject_count"], 9)
        self.assertEqual(result["per_seed"]["42"]["subject_session_count"], 18)
        self.assertEqual(result["four_seed_sd_of_seed_means"], 0)
        self.assertFalse(result["scientific_gate_approved"])
        self.assertFalse(result["underlying_run_integrity_verified"])

    def test_missing_duplicate_unknown_or_nonfinite_folds_fail(self):
        valid = [(unit, 0.6) for unit in self.plan.units]
        invalid = [valid[:-1], valid + valid[:1],
                   [(ReferenceUnit(42, 10, "0train", 0), 0.6), *valid[1:]]]
        invalid += [[(valid[0][0], score), *valid[1:]]
                    for score in (math.nan, math.inf, -0.01, 1.01, True, "0.6", None)]
        for index, observations in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(ValueError):
                summarize_reference_scores(self.plan, observations)


if __name__ == "__main__":
    unittest.main()
