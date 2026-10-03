from __future__ import annotations

import copy
import json
import unittest
from dataclasses import asdict, replace
from unittest.mock import patch

import numpy as np
import test_labram_manifest as fixtures
import torch

from adaptation.labram_lora import inject_labram_qkv_lora
from adaptation.labram_lora_trained import (
    LoRAContinuationSettings,
    LoRASourceCandidate,
    LoRASourceSettings,
    TrainedLoRAManifestRunner,
    continue_trained_lora_support,
    initialize_source_lora,
    validate_trained_lora,
)
from adaptation.labram_source import BCILaBraMSourceSelector
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import BCI_CLASSES, load_bci_profile_b_episode


class LoRASourceTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.LaBraMManifestTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.LaBraMManifestTests.tearDownClass.__func__)

    def setUp(self):
        fixtures.LaBraMManifestTests.setUp(self)
        self.candidate = LoRASourceCandidate(
            "lora_a",
            LoRASourceSettings(("backbone.blocks.1.attn.qkv",), 2, 4.0, 11, True, 1, 2, 0.01),
            LoRAContinuationSettings(True, 1, 0.01, 4),
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
        return TrainedLoRAManifestRunner(**kwargs)

    def episode(self, subject="subject_02", shots=1):
        return load_bci_profile_b_episode(
            self.root,
            self.config,
            next(c for c in self.catalogs if c.subject == subject),
            self.records[subject],
            shots_per_class=shots,
            **asdict(self.assets[subject]),
        )

    def test_source_batches_replay_effective_lora_and_preserve_plain_template(self):
        original = state_digest(self.model)
        rng = torch.random.get_rng_state()
        selector = self.selector()
        model, fit = selector._fit(self.candidate, "subject_02")
        reference = copy.deepcopy(selector._initial).eval().requires_grad_(False)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(11)
            inject_labram_qkv_lora(
                reference, target_modules=self.candidate.source.target_modules, rank=2, alpha=4.0
            )
        reference.head.requires_grad_(True)
        self.assertEqual(state_digest(reference), fit["initial_state_sha256"])
        initial = copy.deepcopy(reference.state_dict())
        optimizer = torch.optim.SGD([p for p in reference.parameters() if p.requires_grad], lr=0.01)
        for step in fit["steps"]:
            self.assertNotIn(step["subject"], ("subject_01", "subject_02"))
            with np.load(
                self.root / f"data/processed/bci_iv_2a/profile_b/{step['subject']}.npz",
                allow_pickle=False,
            ) as data:
                rows = [json.loads(name)[2] for name in step["trial_ids"]]
                inputs = torch.from_numpy(data["signals"][rows].copy())
                targets = torch.tensor([BCI_CLASSES.index(str(v)) for v in data["labels"][rows]])
            optimizer.zero_grad(set_to_none=True)
            loss = torch.nn.functional.cross_entropy(reference(inputs), targets)
            loss.backward()
            optimizer.step()
            self.assertEqual(state_digest(reference), step["state_sha256_after"])
        self.assertEqual(state_digest(reference), state_digest(model))
        changed = {n for n, v in model.state_dict().items() if not torch.equal(v, initial[n])}
        self.assertTrue(any(n.endswith("lora_a") for n in changed))
        self.assertTrue(any(n.endswith("lora_b") for n in changed))
        self.assertTrue(changed <= set(fit["mask"]["trainable_names"]))
        self.assertTrue(all(p.grad is None for p in model.parameters()))
        self.assertEqual(original, state_digest(self.model))
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))

    def test_continuation_keeps_learned_weights_and_never_reinjects_all_head_policies(self):
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
                    seen = []

                    def observe(module, args, seen=seen):
                        if torch.is_grad_enabled():
                            seen.append((state_digest(module), args[0].detach().clone()))

                    handle = source.register_forward_pre_hook(observe)
                    settings = replace(candidate.support, train_head=support_head)
                    with patch(
                        "adaptation.labram_lora_trained.inject_labram_qkv_lora",
                        side_effect=AssertionError("learned LoRA must not be reinitialized"),
                    ):
                        result = continue_trained_lora_support(
                            source,
                            torch.from_numpy(episode.support_signals),
                            torch.from_numpy(episode.support_labels),
                            source_settings=candidate.source,
                            settings=settings,
                        )
                    handle.remove()
                    self.assertEqual(seen[0][0], source_sha)
                    self.assertEqual(len(seen), 1)
                    np.testing.assert_array_equal(seen[0][1].numpy(), episode.support_signals)
                    self.assertEqual(state_digest(source), source_sha)
                    self.assertNotEqual(state_digest(result.model), source_sha)
                    changed = {
                        n
                        for n, v in result.model.state_dict().items()
                        if not torch.equal(v, state[n])
                    }
                    self.assertTrue(changed <= set(result.mask.trainable_names))
                    self.assertEqual(any(n.startswith("head.") for n in changed), support_head)
                    # Admission copies must not delete the trained QKV weight property.
                    with torch.inference_mode():
                        self.assertTrue(
                            torch.isfinite(source(torch.from_numpy(episode.query_signals))).all()
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
                fold["component_policy"], "continue_source_trained_lora_without_reinitialization"
            )
            self.assertEqual(
                fold["source_fit"]["initial_state_sha256"], final["initial_state_sha256"]
            )
            self.assertNotIn(fold["validation_subject"], fold["source_fit"]["training_subjects"])
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
            "adaptation.labram_lora_trained.load_bci_profile_b_episode", side_effect=changed
        ):
            second = runner.predict_validation(
                self.records["subject_02"], shots_per_class=1, settings=self.candidate.support
            )
        self.assertEqual(first.support_losses, second.support_losses)
        self.assertEqual(first.adapted_state_sha256, second.adapted_state_sha256)
        self.assertFalse(torch.equal(first.targets, second.targets))

    def test_scaling_tampering_and_query_state_mutation_are_rejected(self):
        selector = self.selector()
        source, _ = selector._fit(self.candidate, "subject_02")
        adapter = source.get_submodule(
            self.candidate.source.target_modules[0]
        ).parametrizations.weight[0]
        source_sha = state_digest(source)
        adapter.scaling += 1
        self.assertEqual(source_sha, state_digest(source))
        with self.assertRaisesRegex(ValueError, "scaling"):
            self.runner(source)
        adapter.scaling -= 1
        runner = self.runner(source, validation_subject="subject_02")
        original = continue_trained_lora_support
        for mutation in ("scaling", "tensor"):

            def altered(*args, mutation=mutation, **kwargs):
                result = original(*args, **kwargs)

                def query_hook(module, inputs):
                    if not torch.is_grad_enabled():
                        if mutation == "scaling":
                            module.get_submodule(
                                self.candidate.source.target_modules[0]
                            ).parametrizations.weight[0].scaling += 1
                        else:
                            module.head.bias.add_(1)

                result.model.register_forward_pre_hook(query_hook)
                return result

            with (
                self.subTest(mutation=mutation),
                patch(
                    "adaptation.labram_lora_trained.continue_trained_lora_support",
                    side_effect=altered,
                ),
                self.assertRaises(ValueError),
            ):
                runner.predict_validation(
                    self.records["subject_02"], shots_per_class=1, settings=self.candidate.support
                )

    def test_bad_contracts_roles_source_pins_and_nonfinite_loss(self):
        for source_settings in (
            replace(self.candidate.source, rank=999),
            replace(self.candidate.source, target_modules=("backbone.blocks.99.attn.qkv",)),
        ):
            with self.subTest(settings=source_settings), self.assertRaises(ValueError):
                self.selector(candidates=(replace(self.candidate, source=source_settings),))
        selector = self.selector(maximum_gradient_steps=7)
        with patch.object(selector, "_fit") as fit:
            for call in (
                selector.run_selection,
                lambda: selector.run_fold(candidate_name="lora_a", validation_subject="subject_01"),
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
            selector.run_fold(candidate_name="lora_a", validation_subject="subject_02")

    def test_safe_weight_reload_repeat_and_incomplete_evidence(self):
        from safetensors.torch import load, save

        selector = self.selector()
        source, _ = selector._fit(self.candidate, "subject_02")
        checkpoint = save(
            {n: v.detach().clone().contiguous() for n, v in source.state_dict().items()}
        )
        fresh, _ = initialize_source_lora(selector._initial, self.candidate.source)
        fresh.load_state_dict(load(checkpoint), strict=True)
        validate_trained_lora(fresh, self.candidate.source)
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
        evidence = selector.run_fold(candidate_name="lora_a", validation_subject="subject_02")
        self.assertFalse(evidence.record["payload"]["complete"])
        self.assertIsNone(evidence.record["payload"]["selected_candidate"])
        out = self.root / "evidence"
        path = out / "fold.json"
        evidence.write(path, output_root=out)
        saved = path.read_bytes()
        evidence.write(path, output_root=out)
        self.assertEqual(saved, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
