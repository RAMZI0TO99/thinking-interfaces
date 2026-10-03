from __future__ import annotations

import copy
import json
import unittest
from dataclasses import replace
from fractions import Fraction
from unittest.mock import patch

import numpy as np
import test_labram_manifest as fixtures
import torch

from adaptation.labram_manifest import LaBraMTuningSettings
from adaptation.labram_source import (
    BCILaBraMSourceSelector,
    LaBraMSourceCandidate,
    LaBraMSourceSettings,
)
from adaptation.labram_tuning import configure_labram_tuning
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import BCI_CLASSES, load_bci_profile_b_episode


class LaBraMSourceTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.LaBraMManifestTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.LaBraMManifestTests.tearDownClass.__func__)

    def setUp(self):
        fixtures.LaBraMManifestTests.setUp(self)
        self.candidate = LaBraMSourceCandidate(
            "a",
            LaBraMSourceSettings("linear", 1, 2, 0.001),
            LaBraMTuningSettings("linear", 1, 0.001, query_batch_size=4),
        )

    tearDown = fixtures.LaBraMManifestTests.tearDown

    def selector(self, **overrides):
        kwargs = dict(
            root=self.root,
            protocol_config=self.config,
            catalogs=self.catalogs,
            selection_record=self.selection_record,
            source_template=self.model,
            profile_assets=self.assets,
            outer_target="subject_01",
            template_state_sha256=state_digest(self.model),
            candidates=(self.candidate,),
            seed=23,
            shots_per_class=1,
            maximum_gradient_steps=256,
        )
        kwargs.update(overrides)
        return BCILaBraMSourceSelector(**kwargs)

    def test_all_source_masks_replay_exact_recorded_profile_b_batches(self):
        original = copy.deepcopy(self.model.state_dict())
        original_modes = [m.training for m in self.model.modules()]
        original_flags = [p.requires_grad for p in self.model.parameters()]
        self.model.head.weight.grad = torch.ones_like(self.model.head.weight)
        rng = torch.random.get_rng_state()
        for method, depth in (("linear", None), ("partial", 1), ("full", None)):
            with self.subTest(method=method):
                candidate = replace(
                    self.candidate,
                    source=LaBraMSourceSettings(
                        method,
                        1,
                        2,
                        0.001,
                        partial_depth=depth,
                    ),
                )
                selector = self.selector(candidates=(candidate,))
                with patch(
                    "adaptation.labram_source.load_bci_profile_b_episode",
                    wraps=load_bci_profile_b_episode,
                ) as loader:
                    model, fit = selector._fit(candidate, "subject_02")
                self.assertEqual(
                    [c.args[2].subject for c in loader.call_args_list],
                    [f"subject_{i:02d}" for i in range(3, 10)],
                )
                reference = copy.deepcopy(self.model).eval()
                with torch.random.fork_rng(devices=[]):
                    torch.manual_seed(23)
                    reference.head.reset_parameters()
                mask = configure_labram_tuning(reference, method=method, partial_depth=depth)
                initial = copy.deepcopy(reference.state_dict())
                self.assertEqual(state_digest(reference), fit["initial_state_sha256"])
                optimizer = torch.optim.SGD(
                    [p for p in reference.parameters() if p.requires_grad], lr=0.001
                )
                for p in reference.parameters():
                    p.grad = None
                for step in fit["steps"]:
                    path = self.root / f"data/processed/bci_iv_2a/profile_b/{step['subject']}.npz"
                    with np.load(path, allow_pickle=False) as data:
                        indices = [json.loads(name)[2] for name in step["trial_ids"]]
                        inputs = torch.from_numpy(data["signals"][indices].copy())
                        labels = torch.tensor(
                            [BCI_CLASSES.index(str(v)) for v in data["labels"][indices]]
                        )
                    optimizer.zero_grad(set_to_none=True)
                    loss = torch.nn.functional.cross_entropy(reference(inputs), labels)
                    loss.backward()
                    optimizer.step()
                    self.assertEqual(state_digest(reference), step["state_sha256_after"])
                self.assertEqual(state_digest(reference), state_digest(model))
                changed = {
                    n for n, v in model.state_dict().items() if not torch.equal(v, initial[n])
                }
                self.assertTrue(changed)
                self.assertTrue(changed <= set(mask.trainable_names))
                self.assertEqual(fit["mask"]["trainable_names"], mask.trainable_names)
                if method != "linear":
                    self.assertTrue(any(n.startswith("backbone.") for n in changed))
                self.assertTrue(all(p.grad is None for p in model.parameters()))
                self.assertFalse(any(m.training for m in model.modules()))
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        self.assertTrue(
            all(torch.equal(v, original[n]) for n, v in self.model.state_dict().items())
        )
        self.assertEqual(original_modes, [m.training for m in self.model.modules()])
        self.assertEqual(original_flags, [p.requires_grad for p in self.model.parameters()])
        self.assertTrue(
            torch.equal(self.model.head.weight.grad, torch.ones_like(self.model.head.weight))
        )

    def test_complete_selection_does_not_read_outer_artifacts_and_refits_from_initialization(self):
        selector = self.selector()
        for profile in ("a", "b"):
            (self.root / f"data/processed/bci_iv_2a/profile_{profile}/subject_01.npz").write_bytes(
                b"unreadable outer target"
            )
        rng = torch.random.get_rng_state()
        result = selector.run_selection()
        payload = result.evidence.record["payload"]
        self.assertTrue(payload["complete"])
        self.assertEqual(len(payload["folds"]), 8)
        final = payload["final_source_fit"]
        self.assertEqual(final["training_subjects"], list(self.selection.source_subjects))
        self.assertEqual(len(final["steps"]), 8)
        self.assertEqual(final["fitted_state_sha256"], state_digest(result.source))
        scores = []
        for fold in payload["folds"]:
            fit = fold["source_fit"]
            self.assertNotIn("subject_01", fit["training_subjects"])
            self.assertNotIn(fold["validation_subject"], fit["training_subjects"])
            self.assertEqual(fit["initial_state_sha256"], final["initial_state_sha256"])
            cm = fold["confusion_matrix"]
            score = sum(Fraction(cm[i][i], sum(cm[i])) for i in range(4)) / 4
            self.assertEqual(score, Fraction(*fold["balanced_accuracy"]))
            scores.append(score)
            self.assertEqual(len(fold["binding"]["query_trial_ids"]), 4)
        self.assertEqual(sum(scores) / 8, Fraction(*payload["scores"][0]["mean_balanced_accuracy"]))
        self.assertFalse(payload["outer_target_predictions_performed"])
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))

    def test_ranking_exact_ties_and_failed_folds(self):
        second = replace(
            self.candidate, name="b", source=replace(self.candidate.source, learning_rate=0.002)
        )
        selector = self.selector(candidates=(second, self.candidate))
        for scores, winner in (
            ({"a": [1, 2], "b": [1, 2]}, second),
            ({"a": [3, 4], "b": [1, 2]}, self.candidate),
        ):

            def fold(candidate, subject, scores=scores):
                return {
                    "candidate": candidate.name,
                    "validation_subject": subject,
                    "balanced_accuracy": scores[candidate.name],
                }

            with (
                patch.object(selector, "_fold", side_effect=fold) as folds,
                patch.object(selector, "_fit", return_value=(self.model, {})) as fit,
            ):
                result = selector.run_selection()
                self.assertEqual(
                    result.evidence.record["payload"]["selected_candidate"], winner.name
                )
                self.assertEqual(folds.call_count, 16)
                fit.assert_called_once_with(winner, None)
        with (
            patch.object(selector, "_fold", side_effect=ValueError("failed fold")),
            patch.object(selector, "_fit") as fit,
            self.assertRaisesRegex(ValueError, "failed fold"),
        ):
            selector.run_selection()
        fit.assert_not_called()

    def test_fold_repeat_immutable_evidence_and_seed(self):
        selector = self.selector()
        first = selector.run_fold(candidate_name="a", validation_subject="subject_02")
        second = selector.run_fold(candidate_name="a", validation_subject="subject_02")
        self.assertEqual(first.record_json, second.record_json)
        payload = first.record["payload"]
        self.assertFalse(payload["complete"])
        self.assertIsNone(payload["selected_candidate"])
        payload["complete"] = True
        self.assertFalse(first.record["payload"]["complete"])
        output = self.root / "evidence"
        path = output / "fold.json"
        first.write(path, output_root=output)
        original = path.read_bytes()
        first.write(path, output_root=output)
        self.assertEqual(original, path.read_bytes())
        other = self.selector(seed=24)
        changed = other.run_fold(candidate_name="a", validation_subject="subject_02")
        with self.assertRaises(FileExistsError):
            changed.write(path, output_root=output)
        self.assertEqual(original, path.read_bytes())
        self.assertNotEqual(
            other.contract["initial_state_sha256"], selector.contract["initial_state_sha256"]
        )
        self.assertNotEqual(
            changed.record["payload"]["folds"][0]["source_fit"]["steps"][0]["trial_ids"],
            payload["folds"][0]["source_fit"]["steps"][0]["trial_ids"],
        )

    def test_bad_contract_roles_and_budget_fail_before_fit(self):
        for kwargs in (
            {"seed": True},
            {"shots_per_class": True},
            {"maximum_gradient_steps": 5254},
            {"template_state_sha256": "0" * 64},
            {"selection_record": {}},
            {"catalogs": self.catalogs[:-1]},
            {"candidates": ()},
            {"candidates": (self.candidate, self.candidate)},
            {"candidates": (self.candidate, replace(self.candidate, name="duplicate"))},
            {
                "candidates": (
                    replace(
                        self.candidate, source=LaBraMSourceSettings("partial", 1, 2, 0.001, 99)
                    ),
                )
            },
            {
                "candidates": (
                    replace(self.candidate, source=replace(self.candidate.source, batch_size=9)),
                )
            },
            {
                "candidates": (
                    self.candidate,
                    replace(
                        self.candidate,
                        name="other_method",
                        support=LaBraMTuningSettings("full", 1, 0.001),
                    ),
                )
            },
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
        for value in (True, float("nan"), float("inf"), 0, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(self.candidate.source, learning_rate=value)

    def test_tampered_assets_nonfinite_and_frozen_state_mutation_fail(self):
        selector = self.selector()
        path = self.root / "data/processed/bci_iv_2a/profile_b/subject_03.npz"
        original = path.read_bytes()
        path.write_bytes(b"corrupt source")
        with self.assertRaises(ValueError):
            selector.run_fold(candidate_name="a", validation_subject="subject_02")
        path.write_bytes(original)
        with (
            patch("torch.nn.CrossEntropyLoss.forward", return_value=torch.tensor(float("nan"))),
            self.assertRaisesRegex(ValueError, "nonfinite source loss"),
        ):
            selector.run_fold(candidate_name="a", validation_subject="subject_02")

        def mutate_frozen(module, inputs):
            with torch.no_grad():
                next(module.backbone.parameters()).add_(1e-3)

        selector._initial.register_forward_pre_hook(mutate_frozen)
        with self.assertRaisesRegex(ValueError, "frozen parameter or buffer"):
            selector.run_fold(candidate_name="a", validation_subject="subject_02")

    def test_source_iterator_wrap_is_recorded(self):
        candidate = replace(
            self.candidate,
            source=replace(self.candidate.source, steps_per_subject=11, batch_size=8),
        )
        selector = self.selector(candidates=(candidate,))
        _, fit = selector._fit(candidate, "subject_02")
        steps = fit["steps"][:11]
        self.assertEqual([s["iterator_wraps"] for s in steps], [0] * 10 + [1])
        ids = [n for step in steps for n in step["trial_ids"]]
        self.assertEqual(len(ids), 88)
        self.assertEqual(len(set(ids)), 84)
        self.assertEqual(ids[-4:], ids[:4])

    def test_context_change_rejected_before_fit(self):
        selector = self.selector()
        runtime = copy.deepcopy(selector.contract["runtime"])
        runtime["torch_threads"] += 1
        with (
            patch("adaptation.labram_source._runtime", return_value=runtime),
            patch.object(selector, "_fit") as fit,
            self.assertRaisesRegex(ValueError, "runtime"),
        ):
            selector.run_selection()
        fit.assert_not_called()
        with torch.no_grad():
            selector._initial.head.bias.add_(1)
        with (
            patch.object(selector, "_fit") as fit,
            self.assertRaisesRegex(ValueError, "initialization"),
        ):
            selector.run_selection()
        fit.assert_not_called()
        selector = self.selector()
        (self.root / "configs/new.toml").write_text("changed = true\n")
        with (
            patch.object(selector, "_fit") as fit,
            self.assertRaisesRegex(ValueError, "source/config"),
        ):
            selector.run_selection()
        fit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
