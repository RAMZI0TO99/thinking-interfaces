from __future__ import annotations

import copy
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import test_labram_source as fixtures
import torch

from adaptation.labram_lora_trained import (
    LoRAContinuationSettings,
    LoRASourceCandidate,
    LoRASourceSettings,
)
from adaptation.source_checkpoint import SourceFitCheckpoint, source_execution_guard
from evaluation.labram_parity import state_digest


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd() / "tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "runs/phase2/checkpoints"
        self.guard = patch("adaptation.source_checkpoint.source_execution_guard").start()
        self.addCleanup(patch.stopall)
        self.model = torch.nn.Linear(2, 2)
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=0.01)
        self.rng = torch.random.get_rng_state()
        self.addCleanup(torch.random.set_rng_state, self.rng)
        self.history = [
            {"step": 1, "trial_ids": ("one",), "state_sha256_after": state_digest(self.model)}
        ]

    def journal(self, **kwargs):
        return SourceFitCheckpoint(
            self.root, self.directory, kwargs.get("contract", {"seed": 1}), {"fold": 1}
        )

    def publish(self, journal):
        journal.publish(
            self.model, self.optimizer, self.history, {"subject": "identity"}, self.rng, cuda=False
        )

    def test_atomic_publication_ignores_uncommitted_blob_and_restores_committed_state(self):
        journal = self.journal()
        with journal.session():
            self.publish(journal)
            original = copy.deepcopy(self.model.state_dict())
            self.history.append(
                {"step": 2, "trial_ids": ("two",), "state_sha256_after": state_digest(self.model)}
            )
            with (
                patch("adaptation.source_checkpoint.write_once", side_effect=OSError("crash")),
                self.assertRaisesRegex(OSError, "crash"),
            ):
                self.publish(journal)
        self.assertEqual(len(list(journal.output.glob("*.safetensors"))), 2)
        self.assertEqual(len(list(journal.output.glob("*.json"))), 1)
        with torch.no_grad():
            self.model.weight.add_(1)
        resumed = self.journal()
        with resumed.session():
            history, identities, rng = resumed.restore(self.model, self.optimizer, cuda=False)
            self.assertEqual(history, self.history[:1])
            self.assertEqual(identities, {"subject": "identity"})
            self.assertTrue(torch.equal(rng, self.rng))
            self.assertTrue(
                all(torch.equal(v, original[n]) for n, v in self.model.state_dict().items())
            )
            self.publish(resumed)
        self.assertEqual(len(list(journal.output.glob("*.safetensors"))), 3)
        self.assertEqual(len(list(journal.output.glob("*.json"))), 2)

    def test_corruption_contract_optimizer_and_lock_refuse_without_replacing_evidence(self):
        journal = self.journal()
        with journal.session():
            self.publish(journal)
            with self.assertRaises(OSError), self.journal().session():
                self.fail("second writer acquired the lock")
        before = {p.name: p.read_bytes() for p in journal.output.iterdir()}
        with self.assertRaises(FileExistsError), self.journal(contract={"seed": 2}).session():
            self.fail("changed contract was accepted")
        with self.journal().session():
            pass  # The failed context must release its writer lock.
        changed_optimizer = torch.optim.SGD(self.model.parameters(), lr=0.02)
        with journal.session(), self.assertRaisesRegex(ValueError, "optimizer"):
            journal.restore(self.model, changed_optimizer, cuda=False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in journal.output.iterdir()})
        weights = next(journal.output.glob("*.safetensors"))
        weights.write_bytes(weights.read_bytes()[:-1] + b"x")
        with journal.session(), self.assertRaisesRegex(ValueError, "corrupted"):
            journal.restore(self.model, self.optimizer, cuda=False)

    def test_write_guard_prevents_blob_publication_and_rejects_unsafe_paths(self):
        for path in (self.root, self.root / "runs/phase2", self.root / "outside"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                SourceFitCheckpoint(self.root, path, {}, {})
        journal = self.journal()
        with journal.session():
            self.guard.side_effect = RuntimeError("disk floor")
            with self.assertRaisesRegex(RuntimeError, "disk floor"):
                self.publish(journal)
        self.assertEqual(list(journal.output.iterdir()), [])
        self.assertGreater(self.guard.call_args.kwargs["write_bytes"], 0)


class SourceCheckpointTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.LaBraMSourceTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.LaBraMSourceTests.tearDownClass.__func__)
    tearDown = fixtures.LaBraMSourceTests.tearDown
    selector = fixtures.LaBraMSourceTests.selector

    def setUp(self):
        fixtures.LaBraMSourceTests.setUp(self)
        self.directory = self.root / "runs/phase2/checkpoints"
        self.guards = [
            patch(name).start()
            for name in (
                "adaptation.labram_source.source_execution_guard",
                "adaptation.source_checkpoint.source_execution_guard",
            )
        ]
        self.addCleanup(patch.stopall)

    def checkpoint_selector(self, **overrides):
        return self.selector(
            checkpoint_directory=self.directory, operator_compute_admitted=True, **overrides
        )

    @staticmethod
    def fold(selector):
        return selector.run_fold(
            candidate_name=selector._candidates[0].name, validation_subject="subject_02"
        )

    def test_interrupted_plain_and_lora_resume_identically_without_repeating_source_steps(self):
        original = state_digest(self.model)
        for candidate in (
            replace(self.candidate, source=replace(self.candidate.source, steps_per_subject=2)),
            replace(self.candidate, name="full", source=replace(
                self.candidate.source, method="full", steps_per_subject=2)),
            LoRASourceCandidate(
                "lora",
                LoRASourceSettings(("backbone.blocks.1.attn.qkv",), 2, 4.0, 11, True, 2, 2, 0.001),
                LoRAContinuationSettings(True, 1, 0.001, 4),
            ),
        ):
            with self.subTest(candidate=candidate.name):
                self.directory = self.root / "runs/phase2" / candidate.name
                rng = torch.random.get_rng_state()
                reference = self.fold(self.selector(candidates=(candidate,))).record["payload"]
                publish = SourceFitCheckpoint.publish

                def crash(journal, *args, publish=publish, **kwargs):
                    publish(journal, *args, **kwargs)
                    if journal.previous["payload"]["step"] == 3:
                        raise RuntimeError("simulated crash after durable publication")

                with (
                    patch.object(SourceFitCheckpoint, "publish", crash),
                    self.assertRaisesRegex(RuntimeError, "simulated crash"),
                ):
                    self.fold(self.checkpoint_selector(candidates=(candidate,)))
                committed = {p: p.read_bytes() for p in self.directory.rglob("step-*.json")}
                step = torch.optim.SGD.step
                calls = []

                def counted(optimizer, *args, calls=calls, step=step, **kwargs):
                    calls.append(1)
                    return step(optimizer, *args, **kwargs)

                with patch.object(torch.optim.SGD, "step", counted):
                    resumed = self.fold(self.checkpoint_selector(candidates=(candidate,)))
                # 14 source steps, three already committed; one CPU support step.
                self.assertEqual(len(calls), 12)
                self.assertEqual(reference["folds"], resumed.record["payload"]["folds"])
                self.assertEqual(committed, {p: p.read_bytes() for p in committed})
                with patch.object(torch.optim.SGD, "step", counted):
                    repeated = self.fold(self.checkpoint_selector(candidates=(candidate,)))
                self.assertEqual(len(calls), 13)  # Completed source fit skips all its gradients.
                self.assertEqual(repeated.record_json, resumed.record_json)
                self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
                self.assertEqual(state_digest(self.model), original)

    def test_completed_checkpoint_still_reaudits_inputs_and_obeys_original_budget(self):
        self.fold(self.checkpoint_selector())
        with patch.object(torch.optim.SGD, "step") as step:
            with self.assertRaisesRegex(ValueError, "gradient-step ceiling"):
                self.fold(self.checkpoint_selector(maximum_gradient_steps=7))
            step.assert_not_called()
        path = self.root / "data/processed/bci_iv_2a/profile_b/subject_03.npz"
        path.write_bytes(b"changed source input")
        with patch.object(torch.optim.SGD, "step") as step:
            with self.assertRaises(ValueError):
                self.fold(self.checkpoint_selector())
            step.assert_not_called()

    def test_admission_device_and_context_changes_refuse_before_training(self):
        for overrides in (
            {"source_device": "cuda:1"},
            {"source_device": "cuda:0"},
            {"checkpoint_directory": self.directory},
            {"checkpoint_directory": self.root, "operator_compute_admitted": True},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.selector(**overrides)
        self.fold(self.checkpoint_selector())
        with patch.object(torch.optim.SGD, "step") as step:
            with self.assertRaises(FileExistsError):
                self.fold(self.checkpoint_selector(seed=24))
            step.assert_not_called()
        contract = json.loads((self.directory / "context.json").read_bytes())["payload"]
        self.assertEqual(contract["contract"]["source_execution"]["support_query_device"], "cpu")


class ExecutionGuardTests(unittest.TestCase):
    def test_real_guard_retains_machine_floor_and_reserves_pending_write(self):
        admission = {"admitted": True, "machine": {"minimum_free_disk_gib": 20}}
        with patch("evaluation.phase2_pilot.compute_admission", return_value=admission) as admit:
            with patch("adaptation.source_checkpoint.shutil.disk_usage") as disk:
                disk.return_value.free = 20 * 1024**3 + 100
                with self.assertRaisesRegex(RuntimeError, "disk floor"):
                    source_execution_guard(Path.cwd(), cuda=False, write_bytes=101)
                source_execution_guard(Path.cwd(), cuda=False, write_bytes=100)
            admit.assert_called_with(Path.cwd(), operator_admitted=True)
        with (
            patch("evaluation.phase2_pilot.compute_admission", return_value={"admitted": False}),
            self.assertRaisesRegex(RuntimeError, "admission refused"),
        ):
            source_execution_guard(Path.cwd(), cuda=False)


if __name__ == "__main__":
    unittest.main()
