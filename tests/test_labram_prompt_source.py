from __future__ import annotations

import copy
import json
import unittest
from dataclasses import asdict, replace
from unittest.mock import patch

import numpy as np
import test_labram_manifest as fixtures
import torch
from torch.nn import functional as F

from adaptation.labram_adapter import inject_labram_adapters
from adaptation.labram_adapter_trained import (
    AdapterContinuationSettings,
    AdapterSourceCandidate,
    AdapterSourceSettings,
)
from adaptation.labram_prompt import adapt_labram_prompt_support, prompted_labram_logits
from adaptation.labram_prompt_trained import (
    PromptContinuationSettings,
    PromptSourceCandidate,
    PromptSourceSettings,
    TrainedPromptManifestRunner,
    TrainedPromptSourceModel,
    continue_trained_prompt_support,
    initialize_source_prompt,
    validate_trained_prompt,
)
from adaptation.labram_source import BCILaBraMSourceSelector
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import BCI_CLASSES, load_bci_profile_b_episode


class PromptSourceTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.LaBraMManifestTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.LaBraMManifestTests.tearDownClass.__func__)

    def setUp(self):
        fixtures.LaBraMManifestTests.setUp(self)
        self.candidate = PromptSourceCandidate(
            "prompt_a",
            PromptSourceSettings(2, 8, 11, True, 1, 1, 1, 0.01),
            PromptContinuationSettings(True, 1, 0.01, 4),
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

    def runner(self, source, source_settings=None, **overrides):
        kwargs = dict(
            root=self.root,
            protocol_config=self.config,
            catalogs=self.catalogs,
            selection_record=self.selection_record,
            source=source,
            profile_assets=self.assets,
            source_settings=source_settings or self.candidate.source,
            source_state_sha256=state_digest(source),
            outer_target="subject_01",
        )
        kwargs.update(overrides)
        return TrainedPromptManifestRunner(**kwargs)

    def episode(self, subject="subject_02", shots=1):
        return load_bci_profile_b_episode(
            self.root,
            self.config,
            next(c for c in self.catalogs if c.subject == subject),
            self.records[subject],
            shots_per_class=shots,
            **asdict(self.assets[subject]),
        )

    def rows(self, subject: str, trial_ids: tuple[str, ...]):
        with np.load(
            self.root / f"data/processed/bci_iv_2a/profile_b/{subject}.npz", allow_pickle=False
        ) as data:
            rows = [json.loads(name)[2] for name in trial_ids]
            return (
                torch.from_numpy(data["signals"][rows].copy()),
                torch.tensor([BCI_CLASSES.index(str(v)) for v in data["labels"][rows]]),
            )

    def test_source_episodes_replay_learned_generator_and_preserve_plain_template(self):
        original = state_digest(self.model)
        rng = torch.random.get_rng_state()
        selector = self.selector()
        model, fit = selector._fit(self.candidate, "subject_02")
        reference, mask = initialize_source_prompt(selector._initial, self.candidate.source)
        self.assertEqual(state_digest(reference), fit["initial_state_sha256"])
        initial = copy.deepcopy(reference.state_dict())
        optimizer = torch.optim.SGD(
            [p for p in reference.parameters() if p.requires_grad],
            lr=self.candidate.source.learning_rate,
        )
        for step in fit["steps"]:
            self.assertNotIn(step["subject"], ("subject_01", "subject_02"))
            support_inputs, support_labels = self.rows(
                step["subject"], step["support_trial_ids"]
            )
            query_inputs, query_labels = self.rows(step["subject"], step["query_trial_ids"])
            with torch.no_grad():
                features = torch.cat(
                    [
                        reference.classifier.backbone(
                            trial.unsqueeze(0),
                            ch_names=list(reference.classifier.channel_names),
                            return_features=True,
                        )["cls_token"]
                        for trial in support_inputs
                    ]
                )
            optimizer.zero_grad(set_to_none=True)
            prompts = reference.generator(features, support_labels)
            loss = F.cross_entropy(
                prompted_labram_logits(reference.classifier, query_inputs, prompts), query_labels
            )
            loss.backward()
            optimizer.step()
            self.assertEqual(state_digest(reference), step["state_sha256_after"])
        self.assertEqual(state_digest(reference), state_digest(model))
        self.assertEqual(state_digest(reference), fit["fitted_state_sha256"])
        changed = {n for n, v in model.state_dict().items() if not torch.equal(v, initial[n])}
        self.assertTrue(any(n.startswith("generator.") for n in changed))
        self.assertTrue(any(n.startswith("classifier.head.") for n in changed))
        self.assertTrue(changed <= set(mask.trainable_names))
        self.assertTrue(all(p.grad is None for p in model.parameters()))
        self.assertEqual(original, state_digest(self.model))
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))

    def test_continuation_keeps_learned_generator_and_never_reinitializes(self):
        episode = self.episode()
        rng = torch.random.get_rng_state()
        for source_head in (True, False):
            candidate = replace(
                self.candidate, source=replace(self.candidate.source, train_head=source_head)
            )
            selector = self.selector(candidates=(candidate,))
            source, _ = selector._fit(candidate, "subject_02")
            source_sha = state_digest(source)
            state = copy.deepcopy(source.state_dict())
            for support_head in (True, False):
                with self.subTest(source_head=source_head, support_head=support_head):
                    settings = replace(candidate.support, train_head=support_head)
                    with patch(
                        "adaptation.labram_prompt_trained.adapt_labram_prompt_support",
                        wraps=adapt_labram_prompt_support,
                    ) as adapt:
                        result = continue_trained_prompt_support(
                            source,
                            torch.from_numpy(episode.support_signals),
                            torch.from_numpy(episode.support_labels),
                            source_settings=candidate.source,
                            settings=settings,
                        )
                    self.assertIs(adapt.call_args.args[0], source.classifier)
                    self.assertIs(adapt.call_args.args[1], source.generator)
                    self.assertEqual(state_digest(source), source_sha)
                    self.assertNotEqual(state_digest(result.model), source_sha)
                    episode_state = result.model.state_dict()
                    changed = {
                        n for n, v in state.items() if not torch.equal(episode_state[n], v)
                    }
                    self.assertTrue(changed <= set(result.trainable_names))
                    self.assertEqual(
                        any(n.startswith("classifier.head.") for n in changed), support_head
                    )
                    self.assertTrue(
                        any(
                            not torch.equal(episode_state[n], state[n])
                            for n in ("generator.network.0.weight", "generator.network.2.weight")
                        )
                    )
                    with torch.inference_mode():
                        self.assertTrue(
                            torch.isfinite(
                                result.model(torch.from_numpy(episode.query_signals))
                            ).all()
                        )
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))

    def test_complete_selection_excludes_outer_and_carries_fitted_source_state(self):
        selector = self.selector()
        for profile in ("a", "b"):
            (self.root / f"data/processed/bci_iv_2a/profile_{profile}/subject_01.npz").write_bytes(
                b"unreadable outer"
            )
        result = selector.run_selection()
        payload = result.evidence.record["payload"]
        self.assertTrue(payload["complete"])
        self.assertEqual(len(payload["folds"]), 8)
        final = payload["final_source_fit"]
        self.assertEqual(len(final["steps"]), 8)
        self.assertEqual(final["training_subjects"], list(self.selection.source_subjects))
        self.assertEqual(state_digest(result.source), final["fitted_state_sha256"])
        for fold in payload["folds"]:
            self.assertEqual(
                fold["support_source_state_sha256"], fold["source_fit"]["fitted_state_sha256"]
            )
            self.assertEqual(
                fold["component_policy"],
                "continue_source_trained_prompt_generator_without_reinitialization",
            )
            self.assertEqual(
                fold["source_fit"]["initial_state_sha256"], final["initial_state_sha256"]
            )
            self.assertNotIn(fold["validation_subject"], fold["source_fit"]["training_subjects"])
            step = fold["source_fit"]["steps"][0]
            self.assertEqual(
                tuple(step["trial_ids"]),
                tuple(step["support_trial_ids"]) + tuple(step["query_trial_ids"]),
            )
            self.assertEqual(len(step["support_trial_ids"]), 4)
            self.assertEqual(len(step["query_trial_ids"]), 4)
        self.assertFalse(payload["outer_target_predictions_performed"])

    def test_both_runner_roles_all_shots_and_query_changes_do_not_change_fit(self):
        selector = self.selector()
        source, _ = selector._fit(self.candidate, "subject_02")
        # Supplied history is not certified: these constructors test role permissions only.
        for inner in (False, True):
            runner = self.runner(source, **({"validation_subject": "subject_02"} if inner else {}))
            subject = "subject_02" if inner else "subject_01"
            predict = runner.predict_validation if inner else runner.predict_target
            for shots in (1, 5, 10, 20):
                with self.subTest(inner=inner, shots=shots):
                    result = predict(
                        self.records[subject],
                        shots_per_class=shots,
                        settings=self.candidate.support,
                    )
                    self.assertEqual(result.source_state_sha256, state_digest(source))
                    self.assertEqual(
                        result.binding.support_trial_ids,
                        self.episode(subject, shots).binding.support_trial_ids,
                    )
                    self.assertEqual(len(result.binding.query_trial_ids), 4)
                    self.assertFalse(result.source_training_history_verified)
        runner = self.runner(source, validation_subject="subject_02")
        first = runner.predict_validation(
            self.records["subject_02"], shots_per_class=1, settings=self.candidate.support
        )

        def changed(*args, **kwargs):
            episode = load_bci_profile_b_episode(*args, **kwargs)
            return replace(
                episode,
                query_labels=(episode.query_labels + 1) % 4,
                query_signals=episode.query_signals * 2,
            )

        with patch(
            "adaptation.labram_prompt_trained.load_bci_profile_b_episode", side_effect=changed
        ):
            second = runner.predict_validation(
                self.records["subject_02"], shots_per_class=1, settings=self.candidate.support
            )
        self.assertEqual(first.support_losses, second.support_losses)
        self.assertEqual(first.adapted_state_sha256, second.adapted_state_sha256)
        self.assertFalse(torch.equal(first.targets, second.targets))

    def test_generator_structure_and_encoder_tampering_are_rejected(self):
        selector = self.selector()
        source, _ = selector._fit(self.candidate, "subject_02")
        for mutation in ("activation", "network", "width", "classes", "hybrid_classifier"):
            changed = copy.deepcopy(source)
            if mutation == "activation":
                changed.generator.network[1].approximate = "tanh"
            elif mutation == "network":
                changed.generator.network[1] = torch.nn.ReLU()
            elif mutation == "width":
                changed.generator.network[2].weight = torch.nn.Parameter(torch.zeros(199, 8))
            elif mutation == "classes":
                changed.generator.classes = 3
            else:
                inject_labram_adapters(
                    changed.classifier, target_modules=("backbone.blocks.1",), bottleneck_dim=4
                )
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.runner(changed)

    def test_bad_contracts_roles_source_pins_and_nonfinite_loss(self):
        for kwargs in ({"support_shots_per_class": 0}, {"support_shots_per_class": 2}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                candidate = replace(
                    self.candidate, source=replace(self.candidate.source, **kwargs)
                )
                self.selector(candidates=(candidate,))
        mixed = (
            self.candidate,
            AdapterSourceCandidate(
                "adapter_a",
                AdapterSourceSettings(("backbone.blocks.1",), 4, 11, True, 1, 2, 0.01),
                AdapterContinuationSettings(True, 1, 0.01, 4),
            ),
        )
        with self.assertRaisesRegex(ValueError, "one fixed support method"):
            self.selector(candidates=mixed)
        with self.assertRaisesRegex(ValueError, "duplicate candidate settings"):
            self.selector(
                candidates=(self.candidate, replace(self.candidate, name="prompt_b"))
            )
        selector = self.selector(maximum_gradient_steps=7)
        with patch.object(selector, "_fit") as fit:
            for call in (
                selector.run_selection,
                lambda: selector.run_fold(
                    candidate_name="prompt_a", validation_subject="subject_02"
                ),
            ):
                with self.assertRaises(ValueError):
                    call()
            fit.assert_not_called()
        selector = self.selector()
        source, _ = selector._fit(self.candidate, "subject_02")
        with self.assertRaises(ValueError):
            self.runner(source, source_state_sha256="0" * 64)
        inner = self.runner(source, validation_subject="subject_02")
        with self.assertRaises(ValueError):
            inner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=self.candidate.support
            )
        with self.assertRaises(ValueError):
            inner.predict_validation(
                self.records["subject_01"], shots_per_class=1, settings=self.candidate.support
            )
        with (
            patch("torch.nn.CrossEntropyLoss.forward", return_value=torch.tensor(float("nan"))),
            self.assertRaisesRegex(ValueError, "nonfinite"),
        ):
            selector.run_fold(candidate_name="prompt_a", validation_subject="subject_02")

    def test_safe_weight_reload_repeat_and_incomplete_evidence(self):
        from safetensors.torch import load, save

        selector = self.selector()
        source, _ = selector._fit(self.candidate, "subject_02")
        checkpoint = save(
            {n: v.detach().clone().contiguous() for n, v in source.state_dict().items()}
        )
        fresh, _ = initialize_source_prompt(selector._initial, self.candidate.source)
        fresh.load_state_dict(load(checkpoint), strict=True)
        validate_trained_prompt(fresh, self.candidate.source)
        self.assertEqual(state_digest(source), state_digest(fresh))
        source_runner = self.runner(source, validation_subject="subject_02")
        fresh_runner = self.runner(fresh, validation_subject="subject_02")
        first = source_runner.predict_validation(
            self.records["subject_02"], shots_per_class=1, settings=self.candidate.support
        )
        second = fresh_runner.predict_validation(
            self.records["subject_02"], shots_per_class=1, settings=self.candidate.support
        )
        self.assertEqual(first.adapted_state_sha256, second.adapted_state_sha256)
        self.assertTrue(torch.equal(first.logits, second.logits))
        evidence = selector.run_fold(candidate_name="prompt_a", validation_subject="subject_02")
        self.assertFalse(evidence.record["payload"]["complete"])
        self.assertIsNone(evidence.record["payload"]["selected_candidate"])
        out = self.root / "evidence"
        path = out / "fold.json"
        evidence.write(path, output_root=out)
        saved = path.read_bytes()
        evidence.write(path, output_root=out)
        self.assertEqual(saved, path.read_bytes())

    def test_prompt_contract_and_class_balanced_histories(self):
        self.assertEqual(self.candidate.source.batch_size, 8)
        selector = self.selector()
        self.assertEqual(selector.contract["method"], "labram_support_prompt")
        self.assertEqual(selector.contract["candidates"], [asdict(self.candidate)])
        model, fit = selector._fit(self.candidate, "subject_02")
        self.assertIsInstance(model, TrainedPromptSourceModel)
        self.assertEqual(fit["mask"]["method"], "support_prompt")
        self.assertEqual(fit["mask"]["generator_parameters"], 10008)
        self.assertEqual(fit["mask"]["trainable_parameters"], 10812)
        for step in fit["steps"]:
            support_classes = sorted(
                self.rows(step["subject"], step["support_trial_ids"])[1].tolist()
            )
            query_classes = sorted(self.rows(step["subject"], step["query_trial_ids"])[1].tolist())
            self.assertEqual(support_classes, [0, 1, 2, 3])
            self.assertEqual(query_classes, [0, 1, 2, 3])
            self.assertFalse(set(step["support_trial_ids"]) & set(step["query_trial_ids"]))
            self.assertEqual(step["iterator_wraps"], 0)


if __name__ == "__main__":
    unittest.main()
