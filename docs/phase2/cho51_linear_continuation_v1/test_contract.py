"""Fabricated metadata unit cases; no models, arrays, source SGD or study cells.

The guarded child is responsible for running these cases.  Passing them only
checks strict partial-record bookkeeping, never actual selector execution.
"""

from __future__ import annotations

import copy
import hashlib
import json
import unittest

from docs.phase2.cho51_linear_continuation_v1 import contract as C


def sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


def digest(value):
    raw = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def method_config():
    return {
        "method": "labram_linear", "dataset": "cho2017",
        "input_profile": "cho_profile_b_60hz_v1", "variant_config_sha256": C.VARIANT_SHA256,
        "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
        "source_seed_policy": "none", "score": "mean_subject_balanced_accuracy_exact_rational",
        "tie_break": "first_in_declared_candidate_order", "early_stopping": False,
        "candidates": [
            {
                "name": name,
                "source": {"method": "linear", "steps_per_subject": 1, "batch_size": 2,
                           "learning_rate": rate, "partial_depth": None},
                "support": {"method": "linear", "steps": 1, "learning_rate": rate,
                            "partial_depth": None, "query_batch_size": 8},
            }
            for name, rate in (("lr_1e-3", 0.001), ("lr_2e-3", 0.002))
        ],
    }


def catalog(subject):
    return {
        "dataset": "cho2017", "subject": subject, "trial_ids": list(C.TRIAL_IDS),
        "labels": ["left_hand", "right_hand"] * 21, "classes": ["left_hand", "right_hand"],
        "artifact_sha256": sha(subject + " profile A"), "preprocessing_sha256": sha("preprocessing"),
    }


def episode(subject):
    return {
        "schema_version": 1, "phase": 2, "catalog": catalog(subject),
        "protocol_sha256": sha("protocol"),
        "partitions": [
            {"shots_per_class": shots, "support_indices": list(range(shots * 2)),
             "query_indices": [40, 41], "unused_pool_indices": list(range(shots * 2, 40))}
            for shots in (1, 5, 10, 20)
        ],
    }


def binding(subject, shots):
    return {
        "dataset": "cho2017", "subject": subject, "shots_per_class": shots,
        "classes": ["left_hand", "right_hand"], "channel_names": list(C.CHANNELS),
        "protocol_sha256": sha("protocol"), "episode_sha256": digest(episode(subject)),
        "profile_a_artifact_sha256": sha(subject + " profile A"),
        "profile_b_artifact_sha256": sha(subject + " profile B"),
        "profile_b_manifest_sha256": sha(subject + " profile B manifest"),
        "profile_a_preprocessing_sha256": sha("preprocessing"),
        "profile_b_config_sha256": sha("profile B configuration"),
        "base_config_sha256": sha("base configuration"),
        "support_trial_ids": list(C.TRIAL_IDS[:shots * 2]), "query_trial_ids": list(C.TRIAL_IDS[40:]),
        "support_profile_b_rows": list(range(shots * 2)), "query_profile_b_rows": [40, 41],
        "input_trials": 42, "profile_a_rejected_trials": 0, "schema": "cho-a-to-b-episode-60hz-v1",
        "sampling_rate_hz": 200, "samples_per_trial": 800, "patch_samples": 200,
        "stored_unit_volts": 0.0001, "extra_input_scale": 1.0,
        "rejection_policy": "profile_a_frozen_threshold_only", "target_transform_fit": "none",
        "profile_a_sidecar_manifests": "absent_cho_identity_is_the_audited_catalog_hash",
        "variant_config_sha256": C.VARIANT_SHA256,
        "source_file": f"data/raw/moabb/cho2017/{subject}.mat", "source_sha256": sha(subject + " raw"),
    }


def mask():
    return {
        "method": "linear", "depth": 0, "selected_blocks": [],
        "trainable_names": ["head.weight", "head.bias"], "trainable_parameters": 402,
        "head_policy": "existing_head_always_trainable",
        "support_normalization_policy": "all_modules_eval_affine_follows_parameter_mask",
    }


def selector_contract(method):
    subjects = [f"subject_{number:02d}" for number in range(1, 53)]
    sources = [subject for subject in subjects if subject != "subject_02"]
    return {
        "method": "labram_linear", "dataset": "cho2017",
        "selection": {
            "dataset": "cho2017", "target_subject": "subject_02", "source_subjects": sources,
            "inner_folds": [
                {"training_subjects": [s for s in sources if s != val], "validation_subject": val}
                for val in sources
            ],
            "catalog_sha256": [[subject, digest(catalog(subject))] for subject in subjects],
        },
        "protocol_sha256": sha("protocol"),
        "profile_assets": {
            subject: {"profile_b_artifact_sha256": sha(subject + " profile B"),
                      "profile_b_manifest_sha256": sha(subject + " profile B manifest"),
                      "variant_config_sha256": C.VARIANT_SHA256}
            for subject in subjects
        },
        "candidates": copy.deepcopy(method["candidates"]), "head_and_sampling_seed": 11,
        "shots_per_class": 5, "maximum_gradient_steps": 5253,
        "template_state_sha256": sha("fabricated supplied template"),
        "initial_state_sha256": sha("fabricated freshly reset initial head"),
        "prior_template_training_verified": False,
        "initialization": "pinned_supplied_backbone_and_fresh_seeded_linear_head",
        "source_policy": method["source_policy"],
        "source_trial_pool": "all_profile_a_retained_trials_joined_to_profile_b",
        "extra_input_scale": 1.0, "sampling_rate_hz": 200, "samples_per_trial": 800,
        "stored_unit_volts": 0.0001, "score": method["score"], "tie_break": method["tie_break"],
        "early_stopping": False, "source": {
            "git_commit": "a" * 40, "source_sha256": sha("fabricated source fingerprint"), "git_dirty": True,
        },
        "runtime": {"python": "3.12.0", "torch": "2.0.0", "numpy": "2.0.0", "braindecode": "1.0.0",
                    "device": "cpu", "dtype": "float32", "torch_threads": 1,
                    "deterministic_algorithms": False},
        "engineering_only": True, "scientific_evaluation": False,
    }


def record(candidate, contract, validation="subject_01", confusion=None):
    training = [f"subject_{number:02d}" for number in range(1, 53)
                if f"subject_{number:02d}" not in ("subject_02", validation)]
    history = [
        {"step": i, "subject": subject, "subject_step": 1, "iterator_wraps": 0,
         # Random SGD is not class-stratified; two same-class retained trials are legal.
         "trial_ids": [C.TRIAL_IDS[0], C.TRIAL_IDS[2]], "loss": 0.75,
         "state_sha256_after": sha(candidate["name"] + validation + " fabricated SGD " + str(i))}
        for i, subject in enumerate(training, start=1)
    ]
    fold = {
        "candidate": candidate["name"], "validation_subject": validation,
        "source_fit": {
            "candidate": candidate["name"], "candidate_sha256": digest(candidate),
            "validation_subject": validation, "training_subjects": training,
            "input_identities": {
                subject: {"catalog_sha256": digest(catalog(subject)), "binding": binding(subject, 20)}
                for subject in training
            },
            "head_and_sampling_seed": 11, "settings": copy.deepcopy(candidate["source"]),
            "mask": mask(), "optimizer": {"name": "SGD", "momentum": 0, "weight_decay": 0, "fresh": True},
            "normalization_and_dropout": "all_modules_eval_affine_follows_mask",
            "initial_state_sha256": contract["initial_state_sha256"],
            "fitted_state_sha256": history[-1]["state_sha256_after"], "steps": history,
            "history_scope": "complete_for_this_bounded_fit_only", "engineering_only": True,
        },
        "binding": binding(validation, 5), "support_mask": mask(), "support_losses": [0.5],
        "adapted_state_sha256": sha(candidate["name"] + validation + " fabricated support"),
        "confusion_matrix": [[1, 0], [1, 0]], "balanced_accuracy": [1, 2],
    }
    if confusion is not None:
        from fractions import Fraction
        fold["confusion_matrix"] = copy.deepcopy(confusion)
        score = sum((Fraction(confusion[i][i], sum(confusion[i])) for i in range(2)), Fraction()) / 2
        fold["balanced_accuracy"] = [score.numerator, score.denominator]
    result = {
        "schema_version": 1, "phase": 2, "kind": "engineering_smoke", "payload": {
            "purpose": "bounded_labram_source_selection", "contract": copy.deepcopy(contract),
            "contract_sha256": digest(contract), "complete": False, "folds": [fold],
            "selected_candidate": None,
        },
    }
    result["sha256"] = digest(result)
    return result


class PartialContractTests(unittest.TestCase):
    def setUp(self):
        self.method = method_config()
        self.contract = selector_contract(self.method)
        self.records = [record(candidate, self.contract) for candidate in self.method["candidates"]]
        self.pins = {
            "input_identity_sha256": sha("fabricated input identity"),
            "template_state_sha256": self.contract["template_state_sha256"],
            "initial_state_sha256": self.contract["initial_state_sha256"],
            "lineage_recipe_sha256": sha("fabricated lineage recipe"),
        }

    def collect(self):
        return C.collect_partial(self.records, self.method, **self.pins)

    def resign(self):
        for item in self.records:
            item["payload"]["contract_sha256"] = digest(item["payload"]["contract"])
            item["sha256"] = digest({key: value for key, value in item.items() if key != "sha256"})

    def reject(self):
        self.resign()
        with self.assertRaises(ValueError):
            self.collect()

    @property
    def fold(self):
        return self.records[0]["payload"]["folds"][0]

    @property
    def fit(self):
        return self.fold["source_fit"]

    def test_valid_partial_counts_and_evidence_boundary(self):
        result = self.collect()
        self.assertEqual((result["accepted_folds"], result["pending_folds"], result["expected_folds"]), (2, 100, 102))
        self.assertEqual((result["executed_source_updates"], result["executed_support_updates"],
                          result["executed_gradient_updates"], result["full_gradient_updates"]), (100, 2, 102, 5253))
        self.assertEqual(len(result["full_roster"]), 102)
        self.assertEqual(len({(p["candidate"], p["validation_subject"]) for p in result["full_roster"]}), 102)
        self.assertIsNone(result["selected_candidate"])
        for key in ("complete", "full_selector_qualified", "final_fit_qualified", "publication_qualified",
                    "reuse_authorized", "origin_reuse_verified", "scientific_evaluation"):
            self.assertIs(result[key], False)
        self.assertIs(result["engineering_only"], True)
        self.assertEqual(result["original_case_attempts"], 0)
        self.assertEqual(result["sha256"], digest({key: value for key, value in result.items() if key != "sha256"}))
        result["full_roster"][0]["candidate"] = "mutated result"
        self.assertEqual(self.collect()["full_roster"][0]["candidate"], "lr_1e-3")

    def test_input_record_order_does_not_change_manifest(self):
        expected = self.collect()
        self.records.reverse()
        self.assertEqual(self.collect(), expected)

    def test_empty_oversized_and_implicit_rosters_refused(self):
        for records in ([], [self.records[0]] * 103, {"record": self.records[0]}):
            with self.subTest(count=len(records)), self.assertRaises(ValueError):
                C.collect_partial(records, self.method, **self.pins)

    def test_duplicate_requested_pair_refused(self):
        self.records[1] = copy.deepcopy(self.records[0])
        self.reject()

    def test_wrong_validation_subject_refused(self):
        self.fold["validation_subject"] = "subject_02"
        self.reject()

    def test_tampered_envelope_digest_refused(self):
        self.records[0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.collect()

    def test_wrong_envelope_kind_refused(self):
        self.records[0]["kind"] = "evaluation_cell"
        self.reject()

    def test_wrong_purpose_refused(self):
        self.records[0]["payload"]["purpose"] = "complete_source_selection"
        self.reject()

    def test_complete_record_refused(self):
        self.records[0]["payload"]["complete"] = True
        self.reject()

    def test_winner_and_score_injection_refused(self):
        for change in ({"selected_candidate": "lr_1e-3"}, {"scores": []}):
            original = copy.deepcopy(self.records)
            self.records[0]["payload"].update(change)
            self.reject()
            self.records = original

    def test_different_runtime_contracts_refused(self):
        self.records[1]["payload"]["contract"]["runtime"]["deterministic_algorithms"] = True
        self.reject()

    def test_tampered_contract_digest_refused(self):
        self.records[0]["payload"]["contract_sha256"] = "0" * 64
        self.records[0]["sha256"] = digest({k: v for k, v in self.records[0].items() if k != "sha256"})
        with self.assertRaises(ValueError):
            self.collect()

    def test_unadopted_method_configuration_refused(self):
        self.method["candidates"][0]["source"]["batch_size"] = 4
        self.reject()

    def test_candidate_learning_rate_crosswire_refused(self):
        self.fit["settings"]["learning_rate"] = 0.002
        self.reject()

    def test_outer_target_added_to_training_refused(self):
        self.fit["training_subjects"][0] = "subject_02"
        self.reject()

    def test_missing_source_step_refused(self):
        self.fit["steps"].pop()
        self.reject()

    def test_reordered_source_history_refused(self):
        self.fit["steps"][0], self.fit["steps"][1] = self.fit["steps"][1], self.fit["steps"][0]
        self.reject()

    def test_boolean_step_and_seed_refused(self):
        self.fit["steps"][0]["step"] = True
        self.reject()
        self.fit["steps"][0]["step"] = 1
        self.fit["head_and_sampling_seed"] = True
        self.reject()

    def test_nonfinite_and_boolean_losses_refused(self):
        for value in (float("nan"), float("inf"), 2**1024, True):
            with self.subTest(value=str(value)):
                self.fit["steps"][0]["loss"] = value
                if type(value) is bool:
                    self.reject()
                else:
                    with self.assertRaises(ValueError):
                        self.collect()

    def test_missing_or_boolean_support_loss_refused(self):
        self.fold["support_losses"] = []
        self.reject()
        self.fold["support_losses"] = [True]
        self.reject()

    def test_unchanged_source_state_refused(self):
        self.fit["steps"][1]["state_sha256_after"] = self.fit["steps"][0]["state_sha256_after"]
        self.reject()

    def test_final_source_state_must_match_history(self):
        self.fit["fitted_state_sha256"] = sha("unrelated state")
        self.reject()
        self.fit["steps"][-1]["state_sha256_after"] = self.fit["initial_state_sha256"]
        self.fit["fitted_state_sha256"] = self.fit["initial_state_sha256"]
        self.reject()

    def test_unchanged_support_state_refused(self):
        self.fold["adapted_state_sha256"] = self.fit["fitted_state_sha256"]
        self.reject()

    def test_tampered_or_unreduced_rational_refused(self):
        for value in ([1, 1], [2, 4], [True, 2]):
            self.fold["balanced_accuracy"] = value
            self.reject()

    def test_confusion_boolean_and_missing_class_refused(self):
        for value in ([[True, 0], [1, 0]], [[2, 0], [0, 0]], [[-1, 2], [0, 1]]):
            self.fold["confusion_matrix"] = value
            self.reject()

    def test_query_support_overlap_refused(self):
        self.fold["binding"]["query_trial_ids"][0] = C.TRIAL_IDS[0]
        self.reject()

    def test_backbone_mask_or_wrong_head_size_refused(self):
        self.fit["mask"]["trainable_names"].append("backbone.blocks.11.norm1.weight")
        self.reject()
        self.fit["mask"] = mask()
        self.fold["support_mask"]["trainable_parameters"] = 804
        self.reject()

    def test_missing_or_mismatched_catalog_refused(self):
        self.fit["input_identities"]["subject_03"]["catalog_sha256"] = sha("wrong catalog")
        self.reject()
        self.fit["input_identities"]["subject_03"]["catalog_sha256"] = digest(catalog("subject_03"))
        self.fit["input_identities"]["subject_03"]["binding"]["profile_b_artifact_sha256"] = sha("wrong source bytes")
        self.reject()
        self.fit["input_identities"]["subject_03"]["binding"]["profile_b_artifact_sha256"] = sha("subject_03 profile B")
        self.records[0]["payload"]["contract"]["selection"]["catalog_sha256"].pop()
        self.reject()

    def test_external_baseline_pin_mismatch_refused(self):
        for key in ("template_state_sha256", "initial_state_sha256"):
            original = self.pins[key]
            self.pins[key] = sha("different external pin")
            with self.assertRaises(ValueError):
                self.collect()
            self.pins[key] = original

    def test_non_sha_or_boolean_external_pins_refused(self):
        for key in self.pins:
            original = self.pins[key]
            for value in (True, "a" * 32, "A" * 64, None):
                self.pins[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.collect()
            self.pins[key] = original

    def test_unknown_fold_field_and_missing_source_identity_refused(self):
        self.fold["winner"] = "lr_1e-3"
        self.reject()
        del self.fold["winner"]
        del self.fit["input_identities"]["subject_03"]
        self.reject()

    def test_unbound_trial_duplicate_and_source_template_claim_refused(self):
        self.fit["steps"][0]["trial_ids"] = [C.TRIAL_IDS[0], C.TRIAL_IDS[0]]
        self.reject()
        self.fit["steps"][0]["trial_ids"] = [C.TRIAL_IDS[0], C.TRIAL_IDS[2]]
        self.records[0]["payload"]["contract"]["prior_template_training_verified"] = True
        self.reject()

    def test_arbitrary_single_nonfirst_fold_accepted(self):
        self.records = [record(self.method["candidates"][1], self.contract, "subject_52")]
        result = self.collect()
        self.assertEqual((result["accepted_folds"], result["pending_folds"]), (1, 101))
        self.assertEqual(result["completed_pairs"], [{"candidate": "lr_2e-3", "validation_subject": "subject_52"}])
        self.assertEqual((result["executed_source_updates"], result["executed_support_updates"]), (50, 1))
        training = self.records[0]["payload"]["folds"][0]["source_fit"]["training_subjects"]
        self.assertIn("subject_01", training)
        self.assertNotIn("subject_02", training)
        self.assertNotIn("subject_52", training)
        self.assertIs(result["final_fit_ready"], False)

    def test_old_two_plus_eight_new_folds_form_canonical_ten(self):
        additions = [record(candidate, self.contract, f"subject_{number:02d}")
                     for candidate in self.method["candidates"] for number in (3, 4, 5, 6)]
        self.records.extend(reversed(additions))
        result = self.collect()
        self.assertEqual((result["accepted_folds"], result["pending_folds"]), (10, 92))
        self.assertEqual((result["executed_source_updates"], result["executed_support_updates"],
                          result["executed_gradient_updates"]), (500, 10, 510))
        expected = [{"candidate": name, "validation_subject": f"subject_{number:02d}"}
                    for name in ("lr_1e-3", "lr_2e-3") for number in (1, 3, 4, 5, 6)]
        self.assertEqual(result["completed_pairs"], expected)
        self.assertEqual(len(result["pending_pairs"]), 92)
        self.assertEqual(set(result["record_sha256"]), {
            row["candidate"] + "/" + row["validation_subject"] for row in expected})
        self.assertIs(result["final_fit_ready"], False)
        with self.assertRaisesRegex(ValueError, "all 102 distinct canonical folds are required"):
            C.require_complete_folds(self.records, self.method, **self.pins)

    def test_dynamic_heldout_subject_cannot_enter_training(self):
        self.records = [record(self.method["candidates"][0], self.contract, "subject_03")]
        self.fit["training_subjects"][0] = "subject_03"
        self.reject()

    def test_complete_roster_tie_is_advisory_and_requires_fresh_final_fit(self):
        self.records = [record(candidate, self.contract, validation)
                        for candidate in self.method["candidates"] for validation in C.SOURCES]
        result = C.require_complete_folds(self.records, self.method, **self.pins)
        self.assertEqual(result["winner_candidate"], "lr_1e-3")
        self.assertEqual(result["candidate_scores"], [
            {"candidate": "lr_1e-3", "balanced_accuracy": [1, 2], "folds": 51},
            {"candidate": "lr_2e-3", "balanced_accuracy": [1, 2], "folds": 51}])
        self.assertEqual((result["accepted_folds"], result["pending_folds"],
                          result["executed_gradient_updates"], result["fresh_final_source_updates_required"]),
                         (102, 0, 5202, 51))
        self.assertIs(result["final_fit_ready"], True)
        self.assertIs(result["winner_is_advisory"], True)
        for key in ("complete", "final_fit_qualified", "full_selector_qualified", "reuse_authorized",
                    "scientific_evaluation"):
            self.assertIs(result[key], False)
        self.assertIsNone(result["selected_candidate"])
        self.assertEqual(result["sha256"], digest({k: v for k, v in result.items() if k != "sha256"}))

    def test_complete_roster_exact_means_can_select_second_candidate(self):
        self.records = [record(candidate, self.contract, validation,
                               confusion=([[1, 0], [0, 1]] if candidate["name"] == "lr_2e-3"
                                          and validation == "subject_52" else [[1, 0], [1, 0]]))
                        for candidate in self.method["candidates"] for validation in C.SOURCES]
        result = C.require_complete_folds(tuple(reversed(self.records)), self.method, **self.pins)
        self.assertEqual(result["winner_candidate"], "lr_2e-3")
        self.assertEqual(result["candidate_scores"], [
            {"candidate": "lr_1e-3", "balanced_accuracy": [1, 2], "folds": 51},
            {"candidate": "lr_2e-3", "balanced_accuracy": [26, 51], "folds": 51}])
        self.records.pop()
        with self.assertRaisesRegex(ValueError, "all 102 distinct canonical folds are required"):
            C.require_complete_folds(self.records, self.method, **self.pins)


if __name__ == "__main__":
    unittest.main()
