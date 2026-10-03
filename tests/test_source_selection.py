from __future__ import annotations

import copy
import unittest
from dataclasses import replace
from fractions import Fraction
from unittest.mock import patch

import test_labram_manifest as fixtures
import torch

from adaptation.anchor_manifest import EEGNetAnchorSettings
from adaptation.source_selection import (
    BCIEEGNetSourceSelector,
    EEGNetCandidate,
    EEGNetSourceSettings,
)
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import load_bci_profile_a_subject


class SourceSelectionTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.LaBraMManifestTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.LaBraMManifestTests.tearDownClass.__func__)

    def setUp(self):
        fixtures.LaBraMManifestTests.setUp(self)
        self.candidate = EEGNetCandidate(
            "a",
            EEGNetSourceSettings(1, 4, 0.001, 1e6),
            EEGNetAnchorSettings(1, 0.001, 1e6, 4),
        )
        self.manifests = {n: a.profile_a_manifest_sha256 for n, a in self.assets.items()}

    tearDown = fixtures.LaBraMManifestTests.tearDown

    def selector(self, **overrides):
        kwargs = dict(
            root=self.root,
            protocol_config=self.config,
            catalogs=self.catalogs,
            selection_record=self.selection_record,
            profile_a_manifests=self.manifests,
            outer_target="subject_01",
            candidates=(self.candidate,),
            seed=23,
            shots_per_class=1,
            maximum_gradient_steps=256,
        )
        kwargs.update(overrides)
        return BCIEEGNetSourceSelector(**kwargs)

    def test_recorded_source_batches_reproduce_fit_and_exclude_both_held_out_subjects(self):
        from braindecode.models import EEGNet

        selector = self.selector()
        rng = torch.random.get_rng_state()
        with patch(
            "adaptation.source_selection.load_bci_profile_a_subject",
            wraps=load_bci_profile_a_subject,
        ) as loader:
            model, fit = selector._fit(self.candidate, "subject_02")
        self.assertEqual(
            [c.args[2].subject for c in loader.call_args_list],
            [f"subject_{i:02d}" for i in range(3, 10)],
        )
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(23)
            reference = EEGNet(
                n_chans=22, n_outputs=4, n_times=512, sfreq=128, final_layer_with_constraint=True
            ).eval()
        buffers = copy.deepcopy(dict(reference.named_buffers()))
        self.assertEqual(state_digest(reference), fit["initial_state_sha256"])
        optimizer = torch.optim.SGD(reference.parameters(), lr=0.001)
        for step in fit["steps"]:
            catalog = next(c for c in self.catalogs if c.subject == step["subject"])
            data = load_bci_profile_a_subject(
                self.root,
                self.config,
                catalog,
                profile_a_manifest_sha256=self.manifests[catalog.subject],
            )
            indices = [catalog.trial_ids.index(n) for n in step["trial_ids"]]
            optimizer.zero_grad(set_to_none=True)
            loss = torch.nn.functional.cross_entropy(
                reference(torch.from_numpy(data.signals[indices]) * 1e6),
                torch.from_numpy(data.labels[indices]),
            )
            loss.backward()
            optimizer.step()
            self.assertEqual(state_digest(reference), step["state_sha256_after"])
        self.assertEqual(state_digest(reference), state_digest(model))
        self.assertNotEqual(fit["initial_state_sha256"], fit["fitted_state_sha256"])
        self.assertTrue(all(torch.equal(v, buffers[n]) for n, v in model.named_buffers()))
        self.assertTrue(all(p.grad is None for p in model.parameters()))
        repeat, repeated_fit = selector._fit(self.candidate, "subject_02")
        self.assertEqual(fit, repeated_fit)
        self.assertEqual(state_digest(model), state_digest(repeat))

    def test_real_complete_loso_and_fresh_final_fit_with_no_outer_data_reads(self):
        selector = self.selector()
        # An unreadable target artifact discriminates exclusion from merely declared exclusion.
        path = self.root / "data/processed/bci_iv_2a/profile_a/subject_01.npz"
        path.write_bytes(b"outer target must never be read")
        rng = torch.random.get_rng_state()
        result = selector.run_selection()
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        payload = result.evidence.record["payload"]
        self.assertTrue(payload["complete"])
        self.assertEqual(len(payload["folds"]), 8)
        self.assertEqual(payload["selected_candidate"], "a")
        final_fit = payload["final_source_fit"]
        self.assertEqual(final_fit["training_subjects"], list(self.selection.source_subjects))
        self.assertEqual(len(final_fit["steps"]), 8)
        self.assertEqual(final_fit["fitted_state_sha256"], state_digest(result.source))
        scores = []
        for fold in payload["folds"]:
            self.assertNotIn(fold["validation_subject"], fold["source_fit"]["training_subjects"])
            self.assertNotIn("subject_01", fold["source_fit"]["training_subjects"])
            self.assertEqual(
                fold["source_fit"]["initial_state_sha256"], final_fit["initial_state_sha256"]
            )
            cm = fold["confusion_matrix"]
            score = sum(Fraction(cm[i][i], sum(cm[i])) for i in range(4)) / 4
            self.assertEqual(score, Fraction(*fold["balanced_accuracy"]))
            scores.append(score)
            self.assertEqual(len(fold["query_trial_ids"]), 4)
        self.assertEqual(Fraction(*payload["scores"][0]["mean_balanced_accuracy"]), sum(scores) / 8)
        self.assertFalse(payload["outer_target_predictions_performed"])

    def test_roster_ties_order_and_failure_cannot_return_partial_winner(self):
        second = replace(
            self.candidate, name="b", source=replace(self.candidate.source, learning_rate=0.002)
        )
        selector = self.selector(candidates=(second, self.candidate))

        def fold(candidate, subject):
            return {
                "candidate": candidate.name,
                "validation_subject": subject,
                "balanced_accuracy": [1, 2],
            }

        with (
            patch.object(selector, "_fold", side_effect=fold) as folds,
            patch.object(selector, "_fit", return_value=(torch.nn.Linear(1, 1), {})) as fit,
        ):
            result = selector.run_selection()
            self.assertEqual(result.evidence.record["payload"]["selected_candidate"], "b")
            self.assertEqual(folds.call_count, 16)
            fit.assert_called_once_with(second, None)

        def unequal_fold(candidate, subject):
            result = fold(candidate, subject)
            result["balanced_accuracy"] = [3, 4] if candidate.name == "a" else [1, 2]
            return result

        with (
            patch.object(selector, "_fold", side_effect=unequal_fold),
            patch.object(selector, "_fit", return_value=(torch.nn.Linear(1, 1), {})) as fit,
        ):
            result = selector.run_selection()
            self.assertEqual(result.evidence.record["payload"]["selected_candidate"], "a")
            fit.assert_called_once_with(self.candidate, None)
        with (
            patch.object(selector, "_fold", side_effect=ValueError("incomplete fold")),
            patch.object(selector, "_fit") as fit,
        ):
            with self.assertRaisesRegex(ValueError, "incomplete"):
                selector.run_selection()
            fit.assert_not_called()

    def test_fold_evidence_is_immutable_incomplete_and_no_clobber(self):
        selector = self.selector()
        evidence = selector.run_fold(candidate_name="a", validation_subject="subject_02")
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

    def test_bad_contract_roles_and_step_admission_fail_before_fit(self):
        for kwargs in (
            {"seed": True},
            {"seed": -1},
            {"shots_per_class": True},
            {"maximum_gradient_steps": 5254},
            {"candidates": ()},
            {"candidates": (self.candidate, self.candidate)},
            {"candidates": (self.candidate, replace(self.candidate, name="duplicate"))},
            {
                "candidates": (
                    replace(self.candidate, source=replace(self.candidate.source, batch_size=33)),
                )
            },
            {"catalogs": self.catalogs[:-1]},
            {"selection_record": {}},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.selector(**kwargs)
        selector = self.selector(maximum_gradient_steps=7)
        with patch.object(selector, "_fit") as fit:
            for call in (
                lambda: selector.run_fold(candidate_name="a", validation_subject="subject_01"),
                lambda: selector.run_fold(
                    candidate_name="missing", validation_subject="subject_02"
                ),
                lambda: selector.run_fold(candidate_name="a", validation_subject="subject_02"),
                selector.run_selection,
            ):
                with self.assertRaises(ValueError):
                    call()
            fit.assert_not_called()
        with self.assertRaises(ValueError):
            replace(self.candidate, source=replace(self.candidate.source, input_scale=1.0))
        for bad in (True, float("nan"), float("inf"), 0, -1):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                replace(self.candidate.source, learning_rate=bad)

    def test_source_corruption_and_nonfinite_loss_fail(self):
        selector = self.selector()
        path = self.root / "data/processed/bci_iv_2a/profile_a/subject_03.npz"
        old = path.read_bytes()
        path.write_bytes(b"corrupt source")
        with self.assertRaises(ValueError):
            selector.run_fold(candidate_name="a", validation_subject="subject_02")
        path.write_bytes(old)
        with (
            patch("torch.nn.functional.cross_entropy", return_value=torch.tensor(float("nan"))),
            self.assertRaisesRegex(ValueError, "nonfinite source loss"),
        ):
            selector.run_fold(candidate_name="a", validation_subject="subject_02")

    def test_iterator_wrap_and_changed_seed_are_explicit(self):
        candidate = replace(
            self.candidate,
            source=replace(self.candidate.source, steps_per_subject=3, batch_size=32),
        )
        selector = self.selector(candidates=(candidate,))
        _, fit = selector._fit(candidate, "subject_02")
        self.assertEqual([s["iterator_wraps"] for s in fit["steps"][:3]], [0, 0, 1])
        trials = [t for s in fit["steps"][:3] for t in s["trial_ids"]]
        self.assertEqual(len(trials), 96)
        self.assertEqual(len(set(trials)), 84)
        other = self.selector(seed=24)
        _, other_fit = other._fit(self.candidate, "subject_02")
        self.assertNotEqual(other_fit["initial_state_sha256"], fit["initial_state_sha256"])
        self.assertNotEqual(other_fit["steps"][0]["trial_ids"], fit["steps"][0]["trial_ids"][:4])


if __name__ == "__main__":
    unittest.main()
