from __future__ import annotations

import unittest
from dataclasses import replace
from fractions import Fraction
from unittest.mock import patch

import test_labram_manifest as fixtures

from adaptation.anchor_manifest import EATangentAnchorSettings
from adaptation.ea_selection import BCIEATangentSelector, EATangentCandidate


class EASelectionTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.LaBraMManifestTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.LaBraMManifestTests.tearDownClass.__func__)

    def setUp(self):
        fixtures.LaBraMManifestTests.setUp(self)
        self.candidate = EATangentCandidate("ea_c1", EATangentAnchorSettings(1e-6, 1.0, 1000, 2))
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
            shots_per_class=1,
            maximum_classical_fits=256,
        )
        kwargs.update(overrides)
        return BCIEATangentSelector(**kwargs)

    def test_fold_excludes_both_held_out_subjects_and_repeats_exactly(self):
        selector = self.selector()
        evidence = selector.run_fold(candidate_name="ea_c1", validation_subject="subject_02")
        fold = evidence.record["payload"]["folds"][0]
        self.assertEqual(fold["candidate"], "ea_c1")
        self.assertEqual(
            fold["source_subjects"], [f"subject_{i:02d}" for i in range(3, 10)]
        )
        self.assertEqual(len(fold["query_trial_ids"]), 4)
        self.assertEqual(fold["anchor_fit"]["covariance"], "oas")
        self.assertEqual(fold["anchor_fit"]["tangent"], "riemann")
        self.assertEqual(fold["anchor_fit"]["class_weight"], "balanced")
        self.assertEqual(fold["anchor_fit"]["target_alignment"], "support_only")
        self.assertTrue(fold["anchor_fit"]["source_fit_performed"])
        self.assertEqual(
            set(fold["anchor_fit"]["source_trial_ids"]),
            {f"subject_{i:02d}" for i in range(3, 10)},
        )
        cm = fold["confusion_matrix"]
        score = sum(Fraction(cm[i][i], sum(cm[i])) for i in range(4)) / 4
        self.assertEqual(score, Fraction(*fold["balanced_accuracy"]))
        self.assertEqual(sum(map(sum, cm)), 4)
        repeat = selector.run_fold(candidate_name="ea_c1", validation_subject="subject_02")
        self.assertEqual(fold, repeat.record["payload"]["folds"][0])

    def test_complete_selection_two_candidates_with_no_outer_data_reads(self):
        second = EATangentCandidate(
            "ea_c2", EATangentAnchorSettings(1e-6, 2.0, 1000, 2)
        )
        selector = self.selector(candidates=(self.candidate, second))
        # An unreadable target artifact discriminates exclusion from declared exclusion.
        path = self.root / "data/processed/bci_iv_2a/profile_a/subject_01.npz"
        path.write_bytes(b"outer target must never be read")
        result = selector.run_selection()
        payload = result.evidence.record["payload"]
        self.assertTrue(payload["complete"])
        self.assertEqual(len(payload["folds"]), 16)
        self.assertIn(payload["selected_candidate"], ("ea_c1", "ea_c2"))
        self.assertIs(result.candidate, selector._candidate(payload["selected_candidate"]))
        self.assertFalse(payload["final_fit_performed"])
        self.assertFalse(payload["outer_target_predictions_performed"])
        self.assertEqual(payload["contract"]["method"], "ea_tangent_lr")
        self.assertIsNone(payload["contract"]["seed"])
        scores = {c.name: [] for c in (self.candidate, second)}
        for fold in payload["folds"]:
            self.assertNotIn(fold["validation_subject"], fold["source_subjects"])
            self.assertNotIn("subject_01", fold["source_subjects"])
            cm = fold["confusion_matrix"]
            score = sum(Fraction(cm[i][i], sum(cm[i])) for i in range(4)) / 4
            self.assertEqual(score, Fraction(*fold["balanced_accuracy"]))
            scores[fold["candidate"]].append(score)
        means = [
            sum(scores[c.name], start=Fraction()) / 8 for c in (self.candidate, second)
        ]
        self.assertEqual(
            [Fraction(*r["mean_balanced_accuracy"]) for r in payload["scores"]], means
        )
        self.assertEqual(payload["selected_candidate"], ("ea_c1", "ea_c2")[means.index(max(means))])
        settings_hashes = {f["settings_sha256"] for f in payload["folds"]}
        self.assertEqual(len(settings_hashes), 2)

    def test_roster_ties_order_and_failure_cannot_return_partial_winner(self):
        second = EATangentCandidate(
            "ea_c2", EATangentAnchorSettings(1e-6, 2.0, 1000, 2)
        )
        selector = self.selector(candidates=(second, self.candidate))

        def fold(candidate, subject):
            return {
                "candidate": candidate.name,
                "validation_subject": subject,
                "balanced_accuracy": [1, 2],
            }

        with patch.object(selector, "_fold", side_effect=fold) as folds:
            result = selector.run_selection()
            self.assertEqual(result.evidence.record["payload"]["selected_candidate"], "ea_c2")
            self.assertEqual(folds.call_count, 16)

        def unequal_fold(candidate, subject):
            result = fold(candidate, subject)
            result["balanced_accuracy"] = [3, 4] if candidate.name == "ea_c1" else [1, 2]
            return result

        with patch.object(selector, "_fold", side_effect=unequal_fold):
            result = selector.run_selection()
            self.assertEqual(result.evidence.record["payload"]["selected_candidate"], "ea_c1")
        with (
            patch.object(selector, "_fold", side_effect=ValueError("incomplete fold")),
            self.assertRaisesRegex(ValueError, "incomplete"),
        ):
            selector.run_selection()

    def test_fold_evidence_is_immutable_incomplete_and_no_clobber(self):
        selector = self.selector()
        evidence = selector.run_fold(candidate_name="ea_c1", validation_subject="subject_02")
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

    def test_bad_contracts_roles_and_fit_admission_fail_before_execution(self):
        for kwargs in (
            {"candidates": ()},
            {"candidates": (self.candidate, self.candidate)},
            {"candidates": (self.candidate, replace(self.candidate, name="duplicate"))},
            {"shots_per_class": True},
            {"shots_per_class": 2},
            {"maximum_classical_fits": 0},
            {"maximum_classical_fits": 257},
            {"maximum_classical_fits": True},
            {"catalogs": self.catalogs[:-1]},
            {"selection_record": {}},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.selector(**kwargs)
        with self.assertRaises(ValueError):
            self.selector(
                candidates=(
                    EATangentCandidate("bad", EATangentAnchorSettings(1e-6, 0, 1000, 2)),
                )
            )
        selector = self.selector(maximum_classical_fits=7)
        with patch.object(selector, "_fold") as fold:
            for call in (
                lambda: selector.run_fold(
                    candidate_name="ea_c1", validation_subject="subject_01"
                ),
                lambda: selector.run_fold(
                    candidate_name="missing", validation_subject="subject_02"
                ),
                selector.run_selection,  # Eight folds exceed the seven-fit ceiling.
            ):
                with self.assertRaises(ValueError):
                    call()
            fold.assert_not_called()
        selector = self.selector(maximum_classical_fits=16)

        def stub(candidate, subject):
            return {
                "candidate": candidate.name,
                "validation_subject": subject,
                "balanced_accuracy": [1, 2],
            }

        with patch.object(selector, "_fold", side_effect=stub) as fold:
            selector.run_selection()
            self.assertEqual(fold.call_count, 8)

    def test_source_corruption_fails_closed(self):
        selector = self.selector()
        path = self.root / "data/processed/bci_iv_2a/profile_a/subject_03.npz"
        old = path.read_bytes()
        path.write_bytes(b"corrupt source")
        with self.assertRaises(ValueError):
            selector.run_fold(candidate_name="ea_c1", validation_subject="subject_02")
        path.write_bytes(old)


if __name__ == "__main__":
    unittest.main()
