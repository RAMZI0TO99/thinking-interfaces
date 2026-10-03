from __future__ import annotations

import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

import torch

from adaptation.anchor_manifest import EATangentAnchorSettings, EEGNetAnchorSettings
from adaptation.ea_selection import BCIEATangentSelector, EATangentCandidate
from adaptation.source_selection import (
    BCIEEGNetSourceSelector,
    EEGNetCandidate,
    EEGNetSourceSettings,
)
from core.config import load_toml
from evaluation.phase2_protocol import TrialCatalog, source_selection
from evaluation.phase2_records import envelope


class SelectorCohortAdmissionTests(unittest.TestCase):
    """Exercise real admission with unreadable synthetic artifact placeholders."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd() / "tmp")
        self.root = Path(self.temp.name)
        ceiling = self.root / "configs/phase2"
        ceiling.mkdir(parents=True, exist_ok=True)
        (ceiling / "selection_ceiling.toml").write_bytes(
            Path("configs/phase2/selection_ceiling.toml").read_bytes()
        )
        self.config = load_toml("configs/phase2/protocol.toml")
        self.eeg_candidates = (
            EEGNetCandidate("first", EEGNetSourceSettings(1, 4, 0.001, 1e6),
                            EEGNetAnchorSettings(1, 0.001, 1e6, 8)),
            EEGNetCandidate("second", EEGNetSourceSettings(2, 4, 0.002, 1e6),
                            EEGNetAnchorSettings(2, 0.002, 1e6, 8)),
        )
        self.ea_candidates = (
            EATangentCandidate("first", EATangentAnchorSettings(1e-6, 1.0, 1000, 8)),
            EATangentCandidate("second", EATangentAnchorSettings(1e-6, 2.0, 1000, 8)),
        )

    def tearDown(self):
        self.temp.cleanup()

    def world(self, count, dataset="cho2017"):
        config = self.config["datasets"][dataset]
        config["expected_subjects"] = count
        classes = tuple(config["classes"])
        directory = self.root / config["artifact_directory"]
        directory.mkdir(parents=True)
        catalogs = []
        for index in range(1, count + 1):
            subject = f"subject_{index:02d}"
            # An attempted data load must fail; these tests admit/count no training.
            (directory / f"{subject}.npz").write_bytes(b"unreadable admission sentinel")
            labels = classes * 21
            catalogs.append(TrialCatalog(
                dataset, subject, tuple(f"{subject}/{i}" for i in range(len(labels))),
                labels, classes, "1" * 64, "2" * 64,
            ))
        self.catalogs = tuple(catalogs)
        self.selection = source_selection(self.catalogs, target="subject_01")
        self.record = envelope("source_selection", asdict(self.selection))
        self.assets = {c.subject: "3" * 64 for c in catalogs} if dataset == "bci_iv_2a" else {}

    def eegnet(self, maximum, candidates=None):
        return BCIEEGNetSourceSelector(
            self.root, self.config, self.catalogs, self.record, self.assets,
            outer_target="subject_01", candidates=candidates or self.eeg_candidates,
            seed=23, shots_per_class=5, maximum_gradient_steps=maximum,
        )

    def ea(self, maximum, candidates=None):
        return BCIEATangentSelector(
            self.root, self.config, self.catalogs, self.record, self.assets,
            outer_target="subject_01", candidates=candidates or self.ea_candidates,
            shots_per_class=5, maximum_classical_fits=maximum,
        )

    @staticmethod
    def fold(candidate, subject):
        return {"candidate": candidate.name, "validation_subject": subject,
                "balanced_accuracy": [1, 2]}

    def test_full_cho_eegnet_refuses_before_any_fold_or_final_fit(self):
        self.world(52)
        first, second = self.eeg_candidates
        second = replace(second, source=replace(second.source, steps_per_subject=1),
                         support=replace(second.support, steps=1))
        selector = self.eegnet(256, (first, second))
        with (
            patch.object(selector, "_fold", side_effect=AssertionError("fold reached")) as fold,
            patch.object(selector, "_fit", side_effect=AssertionError("fit reached")) as fit,
            self.assertRaisesRegex(ValueError, "gradient-step ceiling"),
        ):
            selector.run_selection()
        fold.assert_not_called()
        fit.assert_not_called()

    def test_cho_single_fold_budget_boundary_and_incomplete_evidence(self):
        self.world(52)
        candidate = self.eeg_candidates[0]
        refused = self.eegnet(50, (candidate,))
        with patch.object(refused, "_fold") as fold:
            with self.assertRaisesRegex(ValueError, "gradient-step ceiling"):
                refused.run_fold(candidate_name="first", validation_subject="subject_02")
            fold.assert_not_called()
        admitted = self.eegnet(51, (candidate,))
        with patch.object(admitted, "_fold", side_effect=self.fold) as fold:
            result = admitted.run_fold(candidate_name="first", validation_subject="subject_02")
        fold.assert_called_once()
        self.assertFalse(result.record["payload"]["complete"])
        self.assertIsNone(result.record["payload"]["selected_candidate"])

    def test_small_cohort_mixed_candidate_budget_includes_final_worst_case(self):
        self.world(3)
        refused = self.eegnet(15)
        with patch.object(refused, "_fold") as fold, patch.object(refused, "_fit") as fit:
            with self.assertRaisesRegex(ValueError, "gradient-step ceiling"):
                refused.run_selection()
            fold.assert_not_called()
            fit.assert_not_called()
        admitted = self.eegnet(16)
        work = []

        def counted_fold(candidate, subject):
            inner = next(f for f in self.selection.inner_folds if f.validation_subject == subject)
            work.extend((source, step) for source in inner.training_subjects
                        for step in range(candidate.source.steps_per_subject))
            work.extend((subject, step) for step in range(candidate.support.steps))
            result = self.fold(candidate, subject)
            result["balanced_accuracy"] = [3, 4] if candidate.name == "second" else [1, 2]
            return result

        def final_fit(candidate, subject):
            self.assertIsNone(subject)
            work.extend((source, step) for source in self.selection.source_subjects
                        for step in range(candidate.source.steps_per_subject))
            return torch.nn.Linear(1, 1), {"training_subjects": self.selection.source_subjects}

        with patch.object(admitted, "_fold", side_effect=counted_fold), patch.object(
            admitted, "_fit", side_effect=final_fit
        ) as fit:
            result = admitted.run_selection()
        self.assertEqual(len(work), 16)
        fit.assert_called_once()
        self.assertEqual(result.evidence.record["payload"]["selected_candidate"], "second")

    def test_ea_cho_exact_fit_boundary_and_tie_order(self):
        self.world(52)
        refused = self.ea(101)
        with patch.object(refused, "_fold") as fold:
            with self.assertRaisesRegex(ValueError, "classical-fit ceiling"):
                refused.run_selection()
            fold.assert_not_called()
        admitted = self.ea(102)
        with patch.object(admitted, "_fold", side_effect=self.fold) as fold:
            result = admitted.run_selection()
        self.assertEqual(fold.call_count, 102)
        self.assertIs(result.candidate, self.ea_candidates[0])
        self.assertFalse(result.evidence.record["payload"]["final_fit_performed"])
        self.assertEqual(
            [row["mean_balanced_accuracy"] for row in result.evidence.record["payload"]["scores"]],
            [[1, 2], [1, 2]],
        )

    def test_bci_budgets_unchanged(self):
        self.world(9, "bci_iv_2a")
        first = self.eeg_candidates[0]
        second = replace(first, name="second", source=replace(first.source, learning_rate=0.002))
        for maximum, fails in ((135, True), (136, False)):
            with self.subTest(maximum=maximum):
                selector = self.eegnet(maximum, (first, second))
                with patch.object(selector, "_fold", side_effect=self.fold) as folds, patch.object(
                    selector, "_fit", return_value=(torch.nn.Linear(1, 1), {})
                ) as fit:
                    if fails:
                        with self.assertRaisesRegex(ValueError, "gradient-step ceiling"):
                            selector.run_selection()
                        folds.assert_not_called()
                        fit.assert_not_called()
                    else:
                        selector.run_selection()
                        self.assertEqual(folds.call_count, 16)
                        fit.assert_called_once()
        ea = self.ea(16)
        with patch.object(ea, "_fold", side_effect=self.fold) as folds:
            ea.run_selection()
        self.assertEqual(folds.call_count, 16)

    def test_cohort_metadata_and_hard_ceilings_remain_explicit(self):
        self.world(52)
        for factory in (self.eegnet, self.ea):
            with self.subTest(factory=factory.__name__):
                contract = factory(256).contract
                self.assertEqual(contract["dataset"], "cho2017")
                self.assertNotIn("eight", contract["source_policy"])
                self.assertEqual(len(contract["selection"]["source_subjects"]), 51)
                for maximum in (0, 5254, True):
                    with self.assertRaises(ValueError):
                        factory(maximum)


if __name__ == "__main__":
    unittest.main()
