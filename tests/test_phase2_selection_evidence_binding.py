"""Synthetic complete-cohort checks for Cho selector evidence admission."""

from __future__ import annotations

import copy
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from typing import Any, ClassVar

import torch

from core.config import config_digest, load_toml
from core.provenance import capture_source
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz
from evaluation.phase2_protocol import (
    EpisodeManifest,
    SourceSelection,
    TrialCatalog,
    nested_episode,
    source_selection,
)
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_selection_evidence_binding import (
    _fit,
    _required_complete_selection_steps,
    _verify_cho_selection_structure,
    verify_cho_selection_evidence,
)


class ChoSelectionEvidenceBindingTests(unittest.TestCase):
    directory: ClassVar[Any]
    root: ClassVar[Path]
    config: ClassVar[Any]
    catalogs: ClassVar[tuple[TrialCatalog, ...]]
    by_subject: ClassVar[dict[str, TrialCatalog]]
    selection: ClassVar[SourceSelection]
    selection_record: ClassVar[dict[str, Any]]
    assets: ClassVar[dict[str, ChoProfileAssets60Hz]]
    source: ClassVar[dict[str, Any]]
    protocol_sha256: ClassVar[str]
    catalog_sha256: ClassVar[dict[str, str]]
    episodes: ClassVar[dict[str, EpisodeManifest]]
    binding_cache: ClassVar[dict[tuple[str, int], dict[str, Any]]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls.directory.name)
        ceiling = cls.root / "configs/phase2"
        ceiling.mkdir(parents=True)
        (ceiling / "selection_ceiling.toml").write_bytes(
            Path("configs/phase2/selection_ceiling.toml").read_bytes()
        )
        cls.config = load_toml("configs/phase2/protocol.toml")
        cls.catalogs = tuple(
            TrialCatalog(
                "cho2017", f"subject_{number:02d}",
                tuple(f"subject_{number:02d}/trial_{index:02d}" for index in range(42)),
                ("left_hand", "right_hand") * 21,
                ("left_hand", "right_hand"), "1" * 64, "2" * 64,
            )
            for number in range(1, 53)
        )
        cls.by_subject = {catalog.subject: catalog for catalog in cls.catalogs}
        cls.catalog_sha256 = {
            catalog.subject: catalog.sha256 for catalog in cls.catalogs
        }
        cls.protocol_sha256 = config_digest(cls.config)
        cls.episodes = {
            catalog.subject: nested_episode(
                catalog, shots=(1, 5, 10, 20),
                protocol_sha256=cls.protocol_sha256,
            )
            for catalog in cls.catalogs
        }
        cls.binding_cache = {}
        cls.selection = source_selection(cls.catalogs, target="subject_01")
        cls.selection_record = envelope("source_selection", asdict(cls.selection))
        cls.assets = {
            catalog.subject: ChoProfileAssets60Hz("3" * 64, "4" * 64, "5" * 64)
            for catalog in cls.catalogs
        }
        cls.source = asdict(capture_source(cls.root))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.directory.cleanup()

    def candidates(self, method: str) -> list[dict[str, Any]]:
        if method == "eegnet":
            return [
                {
                    "name": name,
                    "source": {
                        "steps_per_subject": 1, "batch_size": 2,
                        "learning_rate": rate, "input_scale": 1000000.0,
                    },
                    "support": {
                        "steps": 1, "learning_rate": rate,
                        "input_scale": 1000000.0, "query_batch_size": 8,
                    },
                }
                for name, rate in (("first", 0.001), ("second", 0.002))
            ]
        if method == "labram_lora":
            return [
                {
                    "name": name,
                    "source": {
                        "target_modules": ["blocks.0.attn.qkv"], "rank": 2,
                        "alpha": 2.0, "seed": 11, "train_head": True,
                        "steps_per_subject": 1, "batch_size": 2, "learning_rate": rate,
                    },
                    "support": {
                        "train_head": True, "steps": 1,
                        "learning_rate": rate, "query_batch_size": 8,
                    },
                }
                for name, rate in (("first", 0.001), ("second", 0.002))
            ]
        tuning = method.removeprefix("labram_")
        return [
            {
                "name": name,
                "source": {
                    "method": tuning, "steps_per_subject": 1, "batch_size": 2,
                    "learning_rate": rate, "partial_depth": None,
                },
                "support": {
                    "method": tuning, "steps": 1, "learning_rate": rate,
                    "partial_depth": None, "query_batch_size": 8,
                },
            }
            for name, rate in (("first", 0.001), ("second", 0.002))
        ]

    def binding(self, subject: str, shot: int) -> dict[str, Any]:
        key = (subject, shot)
        if key in self.binding_cache:
            return self.binding_cache[key]
        catalog = self.by_subject[subject]
        episode = self.episodes[subject]
        partition = episode.partition(shot)
        asset = self.assets[subject]
        binding = {
            "dataset": "cho2017", "subject": subject, "shots_per_class": shot,
            "protocol_sha256": self.protocol_sha256,
            "episode_sha256": episode.sha256,
            "support_trial_ids": [catalog.trial_ids[i] for i in partition.support_indices],
            "query_trial_ids": [catalog.trial_ids[i] for i in partition.query_indices],
            "profile_a_artifact_sha256": catalog.artifact_sha256,
            "profile_a_preprocessing_sha256": catalog.preprocessing_sha256,
            "profile_b_artifact_sha256": asset.profile_b_artifact_sha256,
            "profile_b_manifest_sha256": asset.profile_b_manifest_sha256,
            "variant_config_sha256": asset.variant_config_sha256,
            "profile_b_config_sha256": "6" * 64,
            "base_config_sha256": "7" * 64,
            "source_sha256": "8" * 64,
            "source_file": f"data/raw/moabb/cho2017/{subject}.mat",
            "schema": "cho-a-to-b-episode-60hz-v1",
            "sampling_rate_hz": 200,
            "samples_per_trial": 800,
            "stored_unit_volts": 0.0001,
        }
        self.binding_cache[key] = binding
        return binding

    @staticmethod
    def mask(method: str, candidate: dict[str, Any], *, support: bool) -> dict[str, Any]:
        if method == "labram_lora":
            source = candidate["source"]
            return {
                "method": "lora", "target_modules": source["target_modules"],
                "rank": source["rank"], "alpha": source["alpha"],
                "train_head": (
                    candidate["support"]["train_head"] if support else source["train_head"]
                ),
                "trainable_names": ["backbone.blocks.0.attn.qkv.parametrizations.weight.0.lora_a"],
                "trainable_parameters": 100, "adapter_parameters": 50,
                "support_normalization_policy": (
                    "all_modules_eval_source_affine_and_buffers_frozen"
                ),
            }
        tuning = method.removeprefix("labram_")
        return {
            "method": tuning, "depth": 0 if tuning == "linear" else "all",
            "selected_blocks": [] if tuning == "linear" else list(range(12)),
            "trainable_names": ["head.weight"], "trainable_parameters": 100,
            "head_policy": "existing_head_always_trainable",
            "support_normalization_policy": (
                "all_modules_eval_affine_follows_parameter_mask"
            ),
        }

    def fit(
        self, method: str, candidate: dict[str, Any], validation: str | None,
        subjects: tuple[str, ...], state: str,
    ) -> dict[str, Any]:
        source = candidate["source"]
        sampling = torch.Generator(device="cpu").manual_seed(11)
        steps: list[dict[str, Any]] = []
        for subject in subjects:
            catalog = self.by_subject[subject]
            permutation = torch.randperm(
                len(catalog.trial_ids), generator=sampling
            ).tolist()
            for subject_step in range(source["steps_per_subject"]):
                positions = range(
                    subject_step * source["batch_size"],
                    (subject_step + 1) * source["batch_size"],
                )
                steps.append({
                    "step": len(steps) + 1, "subject": subject,
                    "subject_step": subject_step + 1, "state_sha256_after": state,
                    "trial_ids": [
                        catalog.trial_ids[permutation[position % len(permutation)]]
                        for position in positions
                    ],
                    "iterator_wraps": (
                        ((subject_step + 1) * source["batch_size"] - 1)
                        // len(permutation)
                    ),
                    "loss": 0.1,
                })
        fit: dict[str, Any] = {
            "candidate": candidate["name"],
            "candidate_sha256": config_digest(candidate),
            "validation_subject": validation,
            "training_subjects": list(subjects),
            "input_identities": {
                subject: (
                    {
                        "catalog_sha256": self.catalog_sha256[subject],
                        "artifact_sha256": self.by_subject[subject].artifact_sha256,
                        "manifest_sha256": "9" * 64,
                        "base_config_sha256": "7" * 64,
                    }
                    if method == "eegnet" else {
                        "catalog_sha256": self.catalog_sha256[subject],
                        "binding": self.binding(subject, 20),
                    }
                )
                for subject in subjects
            },
            "settings": source,
            "steps": steps,
            "fitted_state_sha256": state,
            "history_scope": "complete_for_this_bounded_fit_only",
            "engineering_only": True,
            "optimizer": {"name": "SGD", "momentum": 0, "weight_decay": 0, "fresh": True},
            "initial_state_sha256": "f" * 64,
            "normalization_and_dropout": (
                "all_modules_eval" if method == "eegnet"
                else "all_modules_eval_affine_follows_mask"
            ),
        }
        fit["seed" if method == "eegnet" else "head_and_sampling_seed"] = 11
        if method != "eegnet":
            fit["mask"] = self.mask(method, candidate, support=False)
        return fit

    def world(self, method: str) -> tuple[dict[str, Any], dict[str, Any]]:
        plan = CasePlan("cho2017", "subject_01", method, 5, 11, 1)
        candidates = self.candidates(method)
        contract: dict[str, Any] = {
            "method": method, "dataset": "cho2017",
            "selection": asdict(self.selection),
            "protocol_sha256": self.protocol_sha256,
            "candidates": candidates, "shots_per_class": 5,
            "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
            "score": "mean_subject_balanced_accuracy_exact_rational",
            "tie_break": "first_in_declared_candidate_order",
            "early_stopping": False, "engineering_only": True,
            "scientific_evaluation": False, "source": self.source,
            "maximum_gradient_steps": 256,
            "runtime": {
                "python": "3.12", "torch": "2.0", "numpy": "2.0", "braindecode": "0.9",
                "device": "cpu", "dtype": "float32", "torch_threads": 1,
                "deterministic_algorithms": True,
            },
        }
        if method == "eegnet":
            contract.update(
                outer_target="subject_01", profile_a_manifests={},
                model_and_sampling_seed=11,
            )
            assets: dict[str, Any] = {}
        else:
            contract.update(
                profile_assets={s: asdict(v) for s, v in self.assets.items()},
                head_and_sampling_seed=11,
                template_state_sha256="7" * 64,
                initial_state_sha256="8" * 64,
                prior_template_training_verified=False,
                source_trial_pool="all_profile_a_retained_trials_joined_to_profile_b",
                sampling_rate_hz=200, samples_per_trial=800,
                stored_unit_volts=0.0001, extra_input_scale=1.0,
            )
            assets = self.assets
        folds = []
        for candidate in candidates:
            for subject in self.selection.source_subjects:
                catalog = self.by_subject[subject]
                episode = self.episodes[subject]
                partition = episode.partition(5)
                permitted = tuple(s for s in self.selection.source_subjects if s != subject)
                state = "a" * 64
                first = candidate["name"] == "first"
                fold: dict[str, Any] = {
                    "candidate": candidate["name"],
                    "validation_subject": subject,
                    "source_fit": self.fit(method, candidate, subject, permitted, state),
                    "adapted_state_sha256": "d" * 64,
                    "confusion_matrix": [[1, 0], [0, 1]] if first else [[1, 0], [1, 0]],
                    "balanced_accuracy": [1, 1] if first else [1, 2],
                }
                if method == "eegnet":
                    fold.update(
                        episode_sha256=episode.sha256,
                        support_trial_ids=[catalog.trial_ids[i] for i in partition.support_indices],
                        query_trial_ids=[catalog.trial_ids[i] for i in partition.query_indices],
                        input_identities={
                            subject: {
                                "catalog_sha256": self.catalog_sha256[subject],
                                "artifact_sha256": catalog.artifact_sha256,
                                "manifest_sha256": "9" * 64,
                                "base_config_sha256": "7" * 64,
                            }
                        },
                        support_fit={"source_fit_performed": False, "support_losses": [0.1]},
                    )
                else:
                    fold["support_mask"] = self.mask(method, candidate, support=True)
                    fold["support_losses"] = [0.1]
                    fold["binding"] = self.binding(subject, 5)
                    if method == "labram_lora":
                        fold["component_policy"] = (
                            "continue_source_trained_lora_without_reinitialization"
                        )
                        fold["support_source_state_sha256"] = state
                        fold["source_settings_sha256"] = config_digest(candidate["source"])
                folds.append(fold)
        payload = {
            "purpose": (
                "bounded_eegnet_source_selection" if method == "eegnet"
                else "bounded_labram_source_selection"
            ),
            "contract": contract,
            "contract_sha256": config_digest(contract),
            "complete": True, "folds": folds,
            "selected_candidate": "first",
            "scores": [
                {"candidate": "first", "mean_balanced_accuracy": [1, 1]},
                {"candidate": "second", "mean_balanced_accuracy": [1, 2]},
            ],
            "final_source_fit": self.fit(
                method, candidates[0], None, self.selection.source_subjects, "b" * 64
            ),
            "outer_target_predictions_performed": False,
        }
        record = envelope("engineering_smoke", payload)
        arguments = {
            "record": record, "evidence_sha256": record["sha256"],
            "plan": plan, "protocol_config": self.config,
            "catalogs": self.catalogs, "selection_record": self.selection_record,
            "assets": assets, "root": self.root,
            "adapter_model_state_sha256": "b" * 64,
            "adapter_source_settings": candidates[0]["source"],
            "adapter_support_settings": candidates[0]["support"],
        }
        return record, arguments

    @staticmethod
    def reseal(arguments: dict[str, Any], record: dict[str, Any]) -> None:
        record = envelope("engineering_smoke", record["payload"])
        arguments["record"] = record
        arguments["evidence_sha256"] = record["sha256"]

    def test_complete_four_method_records_are_structurally_bound(self) -> None:
        for method in ("labram_linear", "labram_lora", "labram_full", "eegnet"):
            with self.subTest(method=method):
                _, arguments = self.world(method)
                verified = _verify_cho_selection_structure(**arguments)
                self.assertEqual(verified.selected_candidate, "first")
                self.assertEqual(verified.evidence_sha256, arguments["evidence_sha256"])

    def test_complete_cho_records_exceed_the_unchanged_engineering_cap(self) -> None:
        for method in ("labram_linear", "labram_lora", "labram_full", "eegnet"):
            with self.subTest(method=method):
                record, arguments = self.world(method)
                candidates = record["payload"]["contract"]["candidates"]
                self.assertEqual(
                    _required_complete_selection_steps(self.selection, candidates), 5253
                )
                with self.assertRaisesRegex(
                    ValueError, "5253 > 256"
                ):
                    verify_cho_selection_evidence(**arguments)

    def test_budget_counts_every_source_support_and_final_fit_step(self) -> None:
        candidates = self.candidates("eegnet")
        candidates[1]["source"]["steps_per_subject"] = 3
        candidates[1]["support"]["steps"] = 2
        # 51*(50*1+1) + 51*(50*3+2) + 51*max(1, 3).
        self.assertEqual(
            _required_complete_selection_steps(self.selection, candidates), 10506
        )
        candidates[1]["support"]["steps"] = 0
        with self.assertRaisesRegex(ValueError, "positive source and support"):
            _required_complete_selection_steps(self.selection, candidates)

    def test_resealed_higher_cap_cannot_admit_complete_cho(self) -> None:
        record, arguments = self.world("eegnet")
        contract = record["payload"]["contract"]
        contract["maximum_gradient_steps"] = 5254
        record["payload"]["contract_sha256"] = config_digest(contract)
        self.reseal(arguments, record)
        with self.assertRaisesRegex(ValueError, "bounded engineering step ceiling"):
            verify_cho_selection_evidence(**arguments)

    def test_committed_ceiling_admits_the_declared_complete_cho_work(self) -> None:
        record, arguments = self.world("eegnet")
        contract = record["payload"]["contract"]
        contract["maximum_gradient_steps"] = 5253
        record["payload"]["contract_sha256"] = config_digest(contract)
        self.reseal(arguments, record)
        verified = verify_cho_selection_evidence(**arguments)
        self.assertEqual(verified.selected_candidate, "first")
        self.assertEqual(verified.evidence_sha256, arguments["evidence_sha256"])

    def test_tampered_envelope_and_caller_digest_refuse(self) -> None:
        record, arguments = self.world("eegnet")
        record["payload"]["selected_candidate"] = "second"
        with self.assertRaisesRegex(ValueError, "envelope"):
            _verify_cho_selection_structure(**arguments)
        self.reseal(arguments, record)
        arguments["evidence_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "caller digest"):
            _verify_cho_selection_structure(**arguments)

    def test_missing_fold_and_wrong_winner_refuse_even_if_resealed(self) -> None:
        record, arguments = self.world("labram_linear")
        record["payload"]["folds"].pop()
        self.reseal(arguments, record)
        with self.assertRaisesRegex(ValueError, "coverage"):
            _verify_cho_selection_structure(**arguments)
        record, arguments = self.world("eegnet")
        record["payload"]["selected_candidate"] = "second"
        self.reseal(arguments, record)
        with self.assertRaisesRegex(ValueError, "winner"):
            _verify_cho_selection_structure(**arguments)

    def test_wrong_assets_checkpoint_and_settings_refuse(self) -> None:
        _, arguments = self.world("labram_lora")
        altered = copy.copy(arguments["assets"])
        altered["subject_02"] = ChoProfileAssets60Hz("6" * 64, "4" * 64, "5" * 64)
        arguments["assets"] = altered
        with self.assertRaisesRegex(ValueError, "assets"):
            _verify_cho_selection_structure(**arguments)
        _, arguments = self.world("labram_lora")
        arguments["adapter_model_state_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "checkpoint"):
            _verify_cho_selection_structure(**arguments)
        _, arguments = self.world("labram_lora")
        arguments["adapter_support_settings"] = {"steps": 999}
        with self.assertRaisesRegex(ValueError, "settings"):
            _verify_cho_selection_structure(**arguments)

    def test_resealed_contract_and_final_fit_tampering_refuse(self) -> None:
        record, arguments = self.world("labram_full")
        record["payload"]["contract"]["source"]["source_sha256"] = "9" * 64
        record["payload"]["contract_sha256"] = config_digest(record["payload"]["contract"])
        self.reseal(arguments, record)
        with self.assertRaisesRegex(ValueError, "live planned source"):
            _verify_cho_selection_structure(**arguments)
        record, arguments = self.world("labram_full")
        record["payload"]["final_source_fit"]["candidate_sha256"] = "9" * 64
        self.reseal(arguments, record)
        with self.assertRaisesRegex(ValueError, "source fit"):
            _verify_cho_selection_structure(**arguments)

    def test_resealed_score_and_incomplete_evidence_refuse(self) -> None:
        record, arguments = self.world("eegnet")
        record["payload"]["folds"][0]["balanced_accuracy"] = [1, 2]
        self.reseal(arguments, record)
        with self.assertRaisesRegex(ValueError, "fold rational score"):
            _verify_cho_selection_structure(**arguments)
        record, arguments = self.world("eegnet")
        record["payload"]["complete"] = False
        self.reseal(arguments, record)
        with self.assertRaisesRegex(ValueError, "completion"):
            _verify_cho_selection_structure(**arguments)

    def test_first_declared_candidate_wins_a_rational_tie(self) -> None:
        record, arguments = self.world("eegnet")
        payload = record["payload"]
        for fold in payload["folds"]:
            fold["confusion_matrix"] = [[1, 0], [0, 1]]
            fold["balanced_accuracy"] = [1, 1]
        payload["scores"][1]["mean_balanced_accuracy"] = [1, 1]
        self.reseal(arguments, record)
        self.assertEqual(_verify_cho_selection_structure(**arguments).selected_candidate, "first")
        payload["selected_candidate"] = "second"
        self.reseal(arguments, record)
        with self.assertRaisesRegex(ValueError, "winner"):
            _verify_cho_selection_structure(**arguments)

    def test_nested_source_bindings_lora_mask_and_policy_are_verified(self) -> None:
        original, arguments = self.world("labram_lora")
        for field, replacement, message in (
            ("variant_config_sha256", "9" * 64, "Cho 60 Hz binding"),
            ("support_trial_ids", [], "Cho 60 Hz binding"),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                identity = changed["payload"]["folds"][0]["source_fit"]["input_identities"]
                subject = next(iter(identity))
                identity[subject]["binding"][field] = replacement
                self.reseal(arguments, changed)
                with self.assertRaisesRegex(ValueError, message):
                    _verify_cho_selection_structure(**arguments)
        changed = copy.deepcopy(original)
        changed["payload"]["folds"][0]["component_policy"] = "reset_lora"
        self.reseal(arguments, changed)
        with self.assertRaisesRegex(ValueError, "support source state or settings"):
            _verify_cho_selection_structure(**arguments)
        changed = copy.deepcopy(original)
        changed["payload"]["folds"][0]["support_mask"]["train_head"] = False
        self.reseal(arguments, changed)
        with self.assertRaisesRegex(ValueError, "LoRA source or support mask"):
            _verify_cho_selection_structure(**arguments)

    def test_fit_wrap_loss_and_execution_metadata_are_verified(self) -> None:
        original, arguments = self.world("eegnet")
        for field, replacement, message in (
            ("iterator_wraps", 1, "wrap or loss"),
            ("loss", "0.1", "wrap or loss"),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed["payload"]["folds"][0]["source_fit"]["steps"][0][field] = replacement
                self.reseal(arguments, changed)
                with self.assertRaisesRegex(ValueError, message):
                    _verify_cho_selection_structure(**arguments)
        original, arguments = self.world("labram_linear")
        changed = copy.deepcopy(original)
        contract = changed["payload"]["contract"]
        contract["source_execution"] = {
            "source_device": "cpu", "support_query_device": "cpu",
            "checkpoint_policy": "immutable_every_gradient_step_all_generations_retained",
            "optimizer_resume": "stateless_sgd_only",
        }
        changed["payload"]["contract_sha256"] = config_digest(contract)
        self.reseal(arguments, changed)
        self.assertEqual(_verify_cho_selection_structure(**arguments).selected_candidate, "first")
        contract["source_execution"]["source_device"] = "cuda:0"
        changed["payload"]["contract_sha256"] = config_digest(contract)
        self.reseal(arguments, changed)
        with self.assertRaisesRegex(ValueError, "source execution"):
            _verify_cho_selection_structure(**arguments)

    def test_resealed_shifted_source_batches_refuse_in_folds_and_final_fit(self) -> None:
        for method in ("labram_linear", "labram_lora", "labram_full", "eegnet"):
            original, arguments = self.world(method)
            for fit_location in ("fold", "final"):
                with self.subTest(method=method, fit_location=fit_location):
                    changed = copy.deepcopy(original)
                    fit = (
                        changed["payload"]["folds"][0]["source_fit"]
                        if fit_location == "fold"
                        else changed["payload"]["final_source_fit"]
                    )
                    # The same allowed subject and unique trials pass the old
                    # membership check, but reverse the seeded batch order.
                    fit["steps"][0]["trial_ids"].reverse()
                    self.reseal(arguments, changed)
                    with self.assertRaisesRegex(ValueError, "seeded iterator"):
                        _verify_cho_selection_structure(**arguments)

    def test_resealed_per_subject_rng_reset_refuses(self) -> None:
        original, arguments = self.world("eegnet")
        changed = copy.deepcopy(original)
        steps = changed["payload"]["final_source_fit"]["steps"]
        first = steps[0]["trial_ids"]
        second = steps[1]["trial_ids"]
        second_subject = steps[1]["subject"]
        independently_reset = [
            f"{second_subject}/{trial.rsplit('/', 1)[1]}" for trial in first
        ]
        self.assertNotEqual(independently_reset, second)
        steps[1]["trial_ids"] = independently_reset
        self.reseal(arguments, changed)
        with self.assertRaisesRegex(ValueError, "seeded iterator"):
            _verify_cho_selection_structure(**arguments)

    def test_cyclic_batch_wrap_replays_the_same_permutation(self) -> None:
        candidate = self.candidates("eegnet")[0]
        candidate["source"].update(steps_per_subject=2, batch_size=30)
        subject = "subject_02"
        fit = self.fit("eegnet", candidate, "subject_03", (subject,), "a" * 64)
        def verify_fit(raw: dict[str, Any]) -> str:
            return _fit(
                raw, candidate=candidate, validation_subject="subject_03",
                training_subjects=(subject,), catalog_by_subject=self.by_subject,
                episodes=self.episodes, assets={}, seed=11, method="eegnet",
            )

        self.assertEqual(fit["steps"][1]["iterator_wraps"], 1)
        self.assertEqual(verify_fit(fit), "a" * 64)
        changed = copy.deepcopy(fit)
        changed["steps"][1]["trial_ids"] = changed["steps"][1]["trial_ids"][1:] + [
            changed["steps"][1]["trial_ids"][0]
        ]
        with self.assertRaisesRegex(ValueError, "seeded iterator"):
            verify_fit(changed)


if __name__ == "__main__":
    unittest.main()
