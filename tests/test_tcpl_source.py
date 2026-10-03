from __future__ import annotations

import unittest
from dataclasses import replace
from fractions import Fraction
from unittest.mock import patch

import test_labram_manifest as fixtures
import torch

from adaptation.tcpl_episodic import TCPLSourceTrainer
from adaptation.tcpl_manifest import TCPLTrainerSettings
from adaptation.tcpl_source import (
    BCITCPLSourceSelector,
    TCPLSourceCandidate,
    TCPLSourceSettings,
    TCPLSupportSettings,
)
from encoder.tcpl import TCPLClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import BCI_CHANNELS


class TCPLSourceTests(unittest.TestCase):
    # Reuse the complete nine-subject BCI fixture with Profile A manifests.
    setUpClass = classmethod(fixtures.LaBraMManifestTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.LaBraMManifestTests.tearDownClass.__func__)

    def setUp(self):
        fixtures.LaBraMManifestTests.setUp(self)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(23)
            self.model = TCPLClassifier(len(BCI_CHANNELS), 4).eval()
        self.candidate = TCPLSourceCandidate(
            "tcpl_a",
            TCPLSourceSettings(1, 1, 1, TCPLTrainerSettings(1e-3, 1e-4, 1e-4)),
            TCPLSupportSettings(4),
        )
        self.manifests = {n: a.profile_a_manifest_sha256 for n, a in self.assets.items()}

    tearDown = fixtures.LaBraMManifestTests.tearDown

    def selector(self, **overrides):
        kwargs = dict(
            root=self.root,
            protocol_config=self.config,
            catalogs=self.catalogs,
            selection_record=self.selection_record,
            source_template=self.model,
            profile_a_manifests=self.manifests,
            outer_target="subject_01",
            channel_names=BCI_CHANNELS,
            candidates=(self.candidate,),
            template_state_sha256=state_digest(self.model),
            seed=23,
            shots_per_class=1,
            maximum_gradient_steps=256,
        )
        kwargs.update(overrides)
        return BCITCPLSourceSelector(**kwargs)

    def test_fit_uses_class_balanced_episodes_and_excludes_both_held_out(self):
        template_sha = state_digest(self.model)
        rng = torch.random.get_rng_state()
        selector = self.selector()
        runner, fit = selector._fit(self.candidate, "subject_02")
        self.assertEqual(
            fit["training_subjects"], [f"subject_{i:02d}" for i in range(3, 10)]
        )
        self.assertEqual(len(fit["steps"]), 7)
        self.assertNotEqual(fit["initial_state_sha256"], fit["fitted_state_sha256"])
        states = [s["state_sha256_after"] for s in fit["steps"]]
        self.assertEqual(states[-1], fit["fitted_state_sha256"])
        self.assertEqual(len(set(states + [fit["initial_state_sha256"]])), 8)
        for step in fit["steps"]:
            self.assertEqual(len(step["support_trial_ids"]), 4)
            self.assertEqual(len(step["query_trial_ids"]), 4)
            self.assertFalse(set(step["support_trial_ids"]) & set(step["query_trial_ids"]))
            self.assertEqual(step["loss"]["total"] > 0, True)
        self.assertEqual(runner.training_subjects, tuple(fit["training_subjects"]))
        self.assertEqual(runner.source_state_sha256, fit["fitted_state_sha256"])
        self.assertEqual(state_digest(self.model), template_sha)
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))

    def test_fit_episodes_cover_every_class_per_step(self):
        selector = self.selector()
        _, fit = selector._fit(self.candidate, "subject_02")
        catalog = next(c for c in self.catalogs if c.subject == "subject_03")
        labels = dict(zip(catalog.trial_ids, catalog.labels, strict=True))
        for step in fit["steps"]:
            for group in ("support_trial_ids", "query_trial_ids"):
                classes = sorted(labels[name] for name in step[group])
                self.assertEqual(classes, sorted(catalog.classes))

    def test_exact_repeat_and_seed_isolation(self):
        selector = self.selector()
        first = selector.run_fold(candidate_name="tcpl_a", validation_subject="subject_02")
        second = selector.run_fold(candidate_name="tcpl_a", validation_subject="subject_02")
        self.assertEqual(
            first.record["payload"]["folds"][0],
            second.record["payload"]["folds"][0],
        )
        other = self.selector(seed=24).run_fold(
            candidate_name="tcpl_a", validation_subject="subject_02"
        )
        self.assertNotEqual(
            first.record["payload"]["folds"][0]["source_fit"]["fitted_state_sha256"],
            other.record["payload"]["folds"][0]["source_fit"]["fitted_state_sha256"],
        )

    def test_complete_selection_ranks_winner_and_fits_afresh(self):
        second = TCPLSourceCandidate(
            "tcpl_b",
            TCPLSourceSettings(1, 1, 1, TCPLTrainerSettings(5e-4, 1e-4, 1e-4)),
            TCPLSupportSettings(8),
        )
        selector = self.selector(candidates=(self.candidate, second))
        result = selector.run_selection()
        payload = result.evidence.record["payload"]
        self.assertTrue(payload["complete"])
        self.assertEqual(len(payload["folds"]), 16)
        self.assertIn(payload["selected_candidate"], ("tcpl_a", "tcpl_b"))
        self.assertFalse(payload["outer_target_predictions_performed"])
        means = []
        for candidate in (self.candidate, second):
            scores = [
                Fraction(*f["balanced_accuracy"])
                for f in payload["folds"]
                if f["candidate"] == candidate.name
            ]
            self.assertEqual(len(scores), 8)
            means.append(sum(scores, start=Fraction()) / 8)
        self.assertEqual(
            [Fraction(*r["mean_balanced_accuracy"]) for r in payload["scores"]], means
        )
        winner = (self.candidate, second)[means.index(max(means))]
        self.assertEqual(payload["selected_candidate"], winner.name)
        final = payload["final_source_fit"]
        self.assertEqual(final["training_subjects"], list(self.selection.source_subjects))
        self.assertEqual(len(final["steps"]), 8)
        self.assertEqual(result.runner.source_state_sha256, final["fitted_state_sha256"])
        self.assertEqual(result.runner.training_subjects, tuple(final["training_subjects"]))
        for fold in payload["folds"]:
            cm = fold["confusion_matrix"]
            score = sum(Fraction(cm[i][i], sum(cm[i])) for i in range(4)) / 4
            self.assertEqual(score, Fraction(*fold["balanced_accuracy"]))
            self.assertEqual(sum(map(sum, cm)), len(fold["query_trial_ids"]))
            self.assertEqual(len(fold["query_trial_ids"]), 4)

    def test_tie_break_order_and_failure_return_no_winner(self):
        second = replace(self.candidate, name="tcpl_b", support=TCPLSupportSettings(8))
        selector = self.selector(candidates=(second, self.candidate))

        def fold(candidate, subject):
            return {
                "candidate": candidate.name,
                "validation_subject": subject,
                "balanced_accuracy": [1, 2],
            }

        with patch.object(selector, "_fold", side_effect=fold) as folds:
            result = selector.run_selection()
            self.assertEqual(result.evidence.record["payload"]["selected_candidate"], "tcpl_b")
            self.assertEqual(folds.call_count, 16)

        def unequal(candidate, subject):
            entry = fold(candidate, subject)
            entry["balanced_accuracy"] = [3, 4] if candidate.name == "tcpl_a" else [1, 2]
            return entry

        with patch.object(selector, "_fold", side_effect=unequal):
            result = selector.run_selection()
            self.assertEqual(result.evidence.record["payload"]["selected_candidate"], "tcpl_a")
        with (
            patch.object(selector, "_fold", side_effect=ValueError("incomplete fold")),
            self.assertRaisesRegex(ValueError, "incomplete"),
        ):
            selector.run_selection()

    def test_optimizer_settings_reach_the_owned_trainer(self):
        candidate = TCPLSourceCandidate(
            "tcpl_lr",
            TCPLSourceSettings(1, 1, 1, TCPLTrainerSettings(0.005, 0.0, 1e-4)),
            TCPLSupportSettings(4),
        )
        captured = []
        original = TCPLSourceTrainer

        def observed(template, **kwargs):
            trainer = original(template, **kwargs)
            captured.append(kwargs)
            return trainer

        selector = self.selector(candidates=(candidate,))
        with patch("adaptation.tcpl_source.TCPLSourceTrainer", side_effect=observed):
            selector.run_fold(candidate_name="tcpl_lr", validation_subject="subject_02")
        self.assertEqual(
            captured,
            [
                {
                    "learning_rate": 0.005,
                    "weight_decay": 0.0,
                    "prompt_l2_weight": 1e-4,
                }
            ],
        )

    def test_bad_contracts_roles_and_admission_fail_before_fit(self):
        for kwargs in (
            {"candidates": ()},
            {"candidates": (self.candidate, self.candidate)},
            {"candidates": (self.candidate, replace(self.candidate, name="duplicate"))},
            {"seed": -1},
            {"seed": True},
            {"shots_per_class": 2},
            {"maximum_gradient_steps": 0},
            {"maximum_gradient_steps": 257},
            {"template_state_sha256": "0" * 64},
            {"profile_a_manifests": {}},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.selector(**kwargs)
        for settings_kwargs in (
            {"steps_per_subject": 0},
            {"support_shots_per_class": 0},
            {"support_shots_per_class": 2},  # batch 12 exceeds the eight-trial ceiling
        ):
            with self.subTest(settings_kwargs=settings_kwargs), self.assertRaises(ValueError):
                self.selector(
                    candidates=(
                        replace(
                            self.candidate,
                            source=replace(self.candidate.source, **settings_kwargs),
                        ),
                    )
                )
        with self.subTest(learning_rate=0), self.assertRaises(ValueError):
            self.selector(
                candidates=(
                    replace(
                        self.candidate,
                        source=TCPLSourceSettings(
                            1, 1, 1, TCPLTrainerSettings(0, 1e-4, 1e-4)
                        ),
                    ),
                )
            )
        selector = self.selector(maximum_gradient_steps=1)
        with patch.object(selector, "_fit") as fit:
            for call in (
                lambda: selector.run_fold(
                    candidate_name="tcpl_a", validation_subject="subject_01"
                ),
                lambda: selector.run_fold(
                    candidate_name="missing", validation_subject="subject_02"
                ),
                lambda: selector.run_fold(
                    candidate_name="tcpl_a", validation_subject="subject_02"
                ),  # Seven source steps exceed the one-step ceiling.
                selector.run_selection,
            ):
                with self.assertRaises(ValueError):
                    call()
            fit.assert_not_called()
        selector = self.selector()
        with self.assertRaises(ValueError):
            selector.run_fold(candidate_name="tcpl_a", validation_subject="subject_01")

    def test_fold_evidence_is_immutable_incomplete_and_no_clobber(self):
        selector = self.selector()
        evidence = selector.run_fold(candidate_name="tcpl_a", validation_subject="subject_02")
        payload = evidence.record["payload"]
        self.assertFalse(payload["complete"])
        self.assertIsNone(payload["selected_candidate"])
        payload["complete"] = True
        self.assertFalse(evidence.record["payload"]["complete"])
        output = self.root / "evidence"
        path = output / "fold.json"
        evidence.write(path, output_root=output)
        before = path.read_bytes()
        evidence.write(path, output_root=output)
        self.assertEqual(path.read_bytes(), before)
        path.write_text("existing unrelated evidence")
        with self.assertRaises(FileExistsError):
            evidence.write(path, output_root=output)
        self.assertEqual(path.read_text(), "existing unrelated evidence")


if __name__ == "__main__":
    unittest.main()
