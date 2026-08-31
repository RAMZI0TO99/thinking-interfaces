from __future__ import annotations

import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from core.config import load_toml
from evaluation.falsification import SubjectControlPlan, saved_control_matches
from scripts.audit_subject_falsification import main


class SubjectControlPlanTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            "dataset": "mmidb", "subject": "subject_085",
            "methods": ["eegnet"], "seeds": [11, 23, 37],
        }

    def test_valid_file_plan_preserves_order(self):
        plan = SubjectControlPlan.from_config({"control": self.settings})
        self.assertEqual(plan.dataset, "mmidb")
        self.assertEqual(plan.subject, "subject_085")
        self.assertEqual(plan.methods, ("eegnet",))
        self.assertEqual(plan.seeds, (11, 23, 37))

    def test_invalid_or_ambiguous_settings_fail_closed(self):
        invalid = {
            "dataset": ["unknown", None, []],
            "subject": ["../subject_085", "subject_85", "subject_000", "subject_110", None],
            "methods": [[], "eegnet", ["eegnet", "eegnet"], ["unknown"], [1], [[]]],
            "seeds": [[], 11, [11, 11], [True], [-1], [2**32], [11.0], ["11"], [[]]],
        }
        for key, values in invalid.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    SubjectControlPlan.from_config({"control": {**self.settings, key: value}})

    def test_missing_and_unknown_fields_are_rejected(self):
        candidates = [{}, {"control": {}}, {"control": self.settings, "extra": 1}]
        candidates.extend(
            {"control": {key: value for key, value in self.settings.items() if key != missing}}
            for missing in self.settings
        )
        candidates.append({"control": {**self.settings, "seed": 11}})
        for config in candidates:
            with self.subTest(config=config), self.assertRaises(ValueError):
                SubjectControlPlan.from_config(config)

    def test_committed_plans_match_historical_grids(self):
        root = Path(__file__).resolve().parents[1]
        for filename, dataset, subject, methods in (
            ("subject_control_cho43.toml", "cho2017", "subject_43", ("eegnet", "shallow")),
            ("subject_control_mmidb85.toml", "mmidb", "subject_085", ("eegnet",)),
        ):
            plan = SubjectControlPlan.from_config(load_toml(root / "configs" / filename))
            self.assertEqual(
                (plan.dataset, plan.subject, plan.methods), (dataset, subject, methods)
            )
            self.assertEqual(plan.seeds, (11, 23, 37))

    def test_resume_requires_record_identity_not_just_filename(self):
        provenance = {"dataset": "mmidb", "target_subject": "subject_085"}
        saved = {**provenance, "method": "eegnet", "shuffle_seed": 11}
        self.assertTrue(saved_control_matches(saved, provenance, method="eegnet", seed=11))
        for changed in (
            {"method": "deep"}, {"shuffle_seed": 23}, {"shuffle_seed": True},
            {"target_subject": "subject_007"}, {"dataset": "cho2017"},
        ):
            with self.subTest(changed=changed):
                self.assertFalse(saved_control_matches(
                    {**saved, **changed}, provenance, method="eegnet", seed=11
                ))

    def test_seed_cannot_override_the_configuration_on_the_command_line(self):
        with (
            patch("sys.argv", ["audit_subject_falsification.py", "--seed", "11"]),
            redirect_stderr(StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            main()
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
