"""Architecture and explicit-refusal checks for Cho selected-source restoration."""

from __future__ import annotations

import hashlib
import json
import platform
import tempfile
import unittest
from copy import deepcopy
from dataclasses import asdict, replace
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar, cast
from unittest.mock import patch

import numpy as np
import torch
from safetensors.torch import load, save
from torch.nn.utils import parametrize

from adaptation.labram_lora_trained import LoRASourceSettings, validate_trained_lora
from core.config import canonical_config_json, config_digest
from core.provenance import SourceProvenance, capture_source
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_source_restore import (
    ChoSourceRestorePreparation,
    _new_model,
    _read_pinned_baseline,
    _runtime_dependencies,
    prepare_cho_source_restore,
    restore_cho_selected_source,
    verify_cho_selected_source_state,
)
from evaluation.phase2_profile_binding import CHO_CHANNELS
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_selected_source_store import (
    SelectedSourceStore,
    SelectedWeightsPreflight,
    _read_bounded_regular,
)
from evaluation.phase2_selection_evidence_binding import VerifiedChoSelection
from scripts.audit_phase2_protocol import file_digest

ROOT = Path(__file__).resolve().parents[1]
VARIANT = "6a3d5b9afca7bc0b82532276df1ef8f0a14db85da0eb609b5176ac967d04afb3"


def _method_config(method: str) -> dict[str, Any]:
    candidates = []
    for name, learning_rate in (("lr_1e-3", 0.001), ("lr_2e-3", 0.002)):
        source: dict[str, Any]
        support: dict[str, Any]
        if method == "labram_lora":
            source = {
                "target_modules": ["backbone.blocks.11.attn.qkv"],
                "rank": 4, "alpha": 1.0, "seed": "$case_model_seed",
                "train_head": True, "steps_per_subject": 1,
                "batch_size": 2, "learning_rate": learning_rate,
            }
            support = {
                "train_head": True, "steps": 1, "learning_rate": learning_rate,
                "query_batch_size": 8,
            }
        elif method == "eegnet":
            source = {
                "steps_per_subject": 1, "batch_size": 4,
                "learning_rate": learning_rate, "input_scale": 1_000_000.0,
            }
            support = {
                "steps": 1, "learning_rate": learning_rate,
                "input_scale": 1_000_000.0, "query_batch_size": 8,
            }
        else:
            tuning = method.removeprefix("labram_")
            source = {
                "method": tuning, "steps_per_subject": 1,
                "batch_size": 2, "learning_rate": learning_rate,
                "partial_depth": None,
            }
            support = {
                "method": tuning, "steps": 1, "learning_rate": learning_rate,
                "partial_depth": None, "query_batch_size": 8,
            }
        candidates.append({"name": name, "source": source, "support": support})
    return {
        "method": method, "dataset": "cho2017",
        "input_profile": "cho_profile_a" if method == "eegnet" else "cho_profile_b_60hz_v1",
        "variant_config_sha256": None if method == "eegnet" else VARIANT,
        "candidates": candidates,
        "source_seed_policy": "case_model_seed" if method == "labram_lora" else "none",
        "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
        "score": "mean_subject_balanced_accuracy_exact_rational",
        "tie_break": "first_in_declared_candidate_order",
        "early_stopping": False,
    }


class ChoSelectedSourceRestoreTests(unittest.TestCase):
    methods: ClassVar[dict[str, dict[str, Any]]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.methods = {
            method: _method_config(method)
            for method in ("labram_linear", "labram_lora", "labram_full", "eegnet")
        }

    def plan(self, method: str) -> CasePlan:
        return CasePlan("cho2017", "subject_01", method, 5, 11, 1)

    def prepare(self, method: str, *, root: Path = ROOT) -> ChoSourceRestorePreparation:
        config = self.methods[method]
        return prepare_cho_source_restore(
            root=root, plan=self.plan(method), method_config=config,
            expected_method_config_sha256=config_digest(config),
            selected_candidate="lr_1e-3",
        )

    def test_recipes_are_method_correct_and_do_not_read_a_manifest(self) -> None:
        for method in self.methods:
            with self.subTest(method=method):
                prepared = self.prepare(method)
                recipe = prepared.model_recipe
                self.assertEqual(recipe["method"], method)
                self.assertEqual(recipe["selected_candidate"], "lr_1e-3")
                self.assertEqual(recipe["architecture"]["classes"] if method != "eegnet"
                                 else recipe["architecture"]["n_outputs"], 2)
                self.assertEqual(recipe["architecture"]["channel_names"], list(CHO_CHANNELS))
                if method == "eegnet":
                    self.assertIsNone(prepared.baseline_weights_path)
                    self.assertEqual(recipe["input_profile"], "cho_profile_a")
                else:
                    self.assertIsNotNone(prepared.baseline_weights_path)
                    self.assertEqual(recipe["input_profile"], "cho_profile_b_60hz_v1")
                if method == "labram_lora":
                    self.assertEqual(recipe["lora"]["rank"], 4)
                    self.assertEqual(recipe["lora"]["alpha"], 1.0)
                    self.assertEqual(recipe["lora"]["seed"], 11)
                    self.assertEqual(recipe["lora"]["target_modules"],
                                     ["backbone.blocks.11.attn.qkv"])
                else:
                    self.assertNotIn("lora", recipe)

    def test_wrong_pins_candidate_scope_and_baseline_refuse(self) -> None:
        method = "labram_lora"
        config = self.methods[method]
        with self.assertRaisesRegex(ValueError, "caller pin"):
            prepare_cho_source_restore(
                root=ROOT, plan=self.plan(method), method_config=config,
                expected_method_config_sha256="0" * 64,
                selected_candidate="lr_1e-3",
            )
        with self.assertRaisesRegex(ValueError, "absent"):
            prepare_cho_source_restore(
                root=ROOT, plan=self.plan(method), method_config=config,
                expected_method_config_sha256=config_digest(config),
                selected_candidate="unselected",
            )
        wrong_plan = CasePlan("cho2017", "subject_01", method, 10, 11, 1)
        with self.assertRaisesRegex(ValueError, "outside"):
            prepare_cho_source_restore(
                root=ROOT, plan=wrong_plan, method_config=config,
                expected_method_config_sha256=config_digest(config),
                selected_candidate="lr_1e-3",
            )
        def wrong_baseline(path: Path) -> str:
            if path.suffix == ".safetensors":
                return "0" * 64
            return file_digest(path)

        with patch(
            "evaluation.phase2_cho_source_restore.file_digest", side_effect=wrong_baseline,
        ), self.assertRaisesRegex(ValueError, "pinned baseline"):
            self.prepare(method)

    def test_labram_baseline_limits_refuse_before_constructor_or_decode(self) -> None:
        prepared = self.prepare("labram_linear")
        for limit_name in (
            "_MAXIMUM_LABRAM_CONFIG_BYTES", "_MAXIMUM_LABRAM_WEIGHTS_BYTES",
        ):
            with self.subTest(limit_name=limit_name), patch(
                f"evaluation.phase2_cho_source_restore.{limit_name}", 1,
            ), patch("braindecode.models.Labram") as constructor, patch(
                "safetensors.torch.load",
            ) as decode, self.assertRaisesRegex(ValueError, "byte limit"):
                _new_model(prepared)
            constructor.assert_not_called()
            decode.assert_not_called()

    def test_labram_baseline_same_path_swap_refuses_before_decode(self) -> None:
        prepared = self.prepare("labram_linear")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            weights = root / "baseline.safetensors"
            weights.write_bytes(b"pinned")
            recipe = deepcopy(prepared.model_recipe)
            recipe["architecture"]["baseline_weights_sha256"] = hashlib.sha256(
                b"pinned",
            ).hexdigest()
            swapped = replace(
                prepared, model_recipe=recipe, baseline_weights_path=weights,
            )

            def swap_after_read(path: Path, parent: Path, maximum_bytes: int) -> bytes:
                blob = _read_bounded_regular(path, parent, maximum_bytes)
                if path == weights:
                    replacement = root / "replacement.safetensors"
                    replacement.write_bytes(b"altered")
                    replacement.replace(weights)
                return blob

            with patch(
                "evaluation.phase2_cho_source_restore._read_bounded_regular",
                side_effect=swap_after_read,
            ), patch("braindecode.models.Labram") as constructor, patch(
                "safetensors.torch.load",
            ) as decode, self.assertRaisesRegex(ValueError, "pinned LaBraM baseline changed"):
                _new_model(swapped)
            constructor.assert_not_called()
            decode.assert_not_called()

    def test_labram_bounded_helper_hashes_the_bytes_it_reads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            path.write_bytes(b"correct")
            with self.assertRaisesRegex(ValueError, "pinned LaBraM baseline changed"):
                _read_pinned_baseline(path, hashlib.sha256(b"other").hexdigest(), 64)

    def test_lora_architecture_has_exact_nontensor_scaling_and_seeded_structure(self) -> None:
        prepared = self.prepare("labram_lora")
        before = torch.random.get_rng_state().clone()
        model = _new_model(prepared)
        self.assertTrue(torch.equal(torch.random.get_rng_state(), before))
        self.assertIsInstance(model, LaBraMClassifier)
        assert isinstance(model, LaBraMClassifier)
        self.assertIsInstance(prepared.source_settings, LoRASourceSettings)
        assert isinstance(prepared.source_settings, LoRASourceSettings)
        validate_trained_lora(model, prepared.source_settings)
        module = model.get_submodule("backbone.blocks.11.attn.qkv")
        self.assertTrue(parametrize.is_parametrized(module))
        adapter = cast(Any, module).parametrizations.weight[0]
        self.assertEqual(adapter.scaling, 0.25)
        adapter.scaling = 0.5
        with self.assertRaisesRegex(ValueError, "scaling"):
            validate_trained_lora(model, prepared.source_settings)

    def test_labram_template_and_fit_initial_lineage_refuse_wrong_digests(self) -> None:
        prepared = self.prepare("labram_linear")
        baseline = state_digest(_new_model(prepared))
        self.assertEqual(
            state_digest(_new_model(
                prepared,
                contract={
                    "template_state_sha256": baseline,
                    "initial_state_sha256": baseline,
                },
                final_fit={"initial_state_sha256": baseline},
            )),
            baseline,
        )
        with self.assertRaisesRegex(ValueError, "template"):
            _new_model(
                prepared,
                contract={"template_state_sha256": "0" * 64},
                final_fit={"initial_state_sha256": baseline},
            )
        with self.assertRaisesRegex(ValueError, "initial state"):
            _new_model(
                prepared,
                contract={
                    "template_state_sha256": baseline,
                    "initial_state_sha256": "0" * 64,
                },
                final_fit={"initial_state_sha256": baseline},
            )
        with self.assertRaisesRegex(ValueError, "fit initialization"):
            _new_model(
                prepared,
                contract={
                    "template_state_sha256": baseline,
                    "initial_state_sha256": baseline,
                },
                final_fit={"initial_state_sha256": "0" * 64},
            )

    def test_source_runtime_schema_allows_cuda_fit_with_cpu_restore(self) -> None:
        base = {
            "python": platform.python_version(),
            "torch": str(torch.__version__),
            "numpy": np.__version__,
            "braindecode": version("braindecode"),
            "device": "cpu", "dtype": "float32", "torch_threads": 2,
            "deterministic_algorithms": False,
        }
        _runtime_dependencies({"runtime": base})
        cuda = {
            **base, "device": "cuda:0", "cuda": "12.8", "cudnn": 8907,
            "gpu_name": "recorded GPU", "gpu_capability": [8, 9],
            "matmul_tf32": False, "cudnn_tf32": True,
            "cudnn_benchmark": False, "cudnn_deterministic": True,
        }
        _runtime_dependencies({"runtime": cuda})
        for name, value in (
            ("dtype", "float64"), ("device", "cuda:1"),
            ("torch_threads", 0), ("deterministic_algorithms", 1),
        ):
            with self.subTest(name=name):
                wrong = {**base, name: value}
                with self.assertRaisesRegex(ValueError, "runtime schema"):
                    _runtime_dependencies({"runtime": wrong})
        for cuda_name, cuda_value in (("gpu_capability", [8]), ("cudnn_tf32", 1)):
            with self.subTest(name=cuda_name):
                wrong_cuda = {**cuda, cuda_name: cuda_value}
                with self.assertRaisesRegex(ValueError, "CUDA runtime schema"):
                    _runtime_dependencies({"runtime": wrong_cuda})

    def test_late_baseline_mutation_refuses_adapter_release(self) -> None:
        method = "labram_linear"
        config = self.methods[method]
        prepared = self.prepare(method)
        model = _new_model(prepared)
        assert prepared.model_config_path is not None
        with tempfile.TemporaryDirectory() as directory:
            copied_config = Path(directory) / "model_config.json"
            copied_config.write_bytes(prepared.model_config_path.read_bytes())
            copied = replace(prepared, model_config_path=copied_config)
            contract = {
                "runtime": {
                    "python": platform.python_version(),
                    "torch": str(torch.__version__),
                    "numpy": np.__version__,
                    "braindecode": version("braindecode"),
                    "device": "cuda:0", "dtype": "float32", "torch_threads": 2,
                    "deterministic_algorithms": False,
                    "cuda": "12.8", "cudnn": 8907, "gpu_name": "recorded GPU",
                    "gpu_capability": [8, 9], "matmul_tf32": False,
                    "cudnn_tf32": True, "cudnn_benchmark": False,
                    "cudnn_deterministic": True,
                },
                "source": asdict(capture_source(ROOT)),
            }
            record = {"payload": {
                "contract": contract, "selected_candidate": "lr_1e-3",
            }}
            selected_store = SelectedSourceStore(ROOT)
            restored = SimpleNamespace(
                evidence_record=record,
                publication=SimpleNamespace(
                    selected_candidate="lr_1e-3",
                    model_state_sha256=state_digest(model),
                ),
            )

            def mutate_after_verification(**kwargs: Any) -> VerifiedChoSelection:
                copied_config.write_bytes(copied_config.read_bytes() + b" ")
                return VerifiedChoSelection("lr_1e-3", "a" * 64)

            with patch(
                "evaluation.phase2_cho_source_restore.prepare_cho_source_restore",
                return_value=copied,
            ), patch(
                "evaluation.phase2_cho_source_restore._pre_restore_evidence",
                return_value=(record, contract, {}),
            ), patch(
                "evaluation.phase2_cho_source_restore._new_model", return_value=model,
            ), patch.object(
                selected_store, "restore", return_value=restored,
            ), patch(
                "evaluation.phase2_cho_source_restore._method_config",
            ), patch(
                "evaluation.phase2_cho_source_restore.verify_cho_selection_evidence",
                side_effect=mutate_after_verification,
            ), self.assertRaisesRegex(ValueError, "pinned LaBraM baseline changed"):
                restore_cho_selected_source(
                    root=ROOT, plan=self.plan(method), method_config=config,
                    expected_method_config_sha256=config_digest(config),
                    selected_candidate="lr_1e-3", manifest_sha256="a" * 64,
                    evidence_sha256="a" * 64, protocol_config={}, catalogs=(),
                    selection_record={}, assets={}, store=selected_store,
                )

    def test_real_store_round_trip_still_refuses_incomplete_cho_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "configs").mkdir()
            (root / "configs/base.toml").write_text(
                "[storage]\nminimum_free_gb = 0.0\n", encoding="utf-8",
            )
            method = "eegnet"
            method_config = self.methods[method]
            prepared = self.prepare(method, root=root)
            model = _new_model(prepared)
            protocol: dict[str, Any] = {
                "protocol": {"schema_version": 1}, "datasets": {"cho2017": {}},
            }
            candidates = method_config["candidates"]
            contract: dict[str, Any] = {
                "method": method, "dataset": "cho2017",
                "protocol_sha256": config_digest(protocol),
                "source": asdict(capture_source(root)),
                "candidates": candidates,
                "runtime": {
                    "python": platform.python_version(),
                    "torch": str(torch.__version__),
                    "numpy": np.__version__,
                    "braindecode": version("braindecode"),
                    "device": "cpu", "dtype": "float32", "torch_threads": 2,
                    "deterministic_algorithms": False,
                },
            }
            selected = candidates[0]
            evidence = envelope("engineering_smoke", {
                "purpose": "bounded_eegnet_source_selection",
                "contract": contract,
                "contract_sha256": config_digest(contract),
                "complete": True,
                "selected_candidate": selected["name"],
                "final_source_fit": {
                    "candidate": selected["name"],
                    "candidate_sha256": config_digest(selected),
                    "initial_state_sha256": state_digest(model),
                    "fitted_state_sha256": state_digest(model),
                },
                "outer_target_predictions_performed": False,
            })
            store = SelectedSourceStore(root)
            publication = store.publish(
                model, evidence, evidence_sha256=evidence["sha256"],
                protocol_config=protocol, model_recipe=prepared.model_recipe,
            )
            with self.assertRaisesRegex(ValueError, "complete typed 52-subject Cho catalog"):
                restore_cho_selected_source(
                    root=root, plan=self.plan(method), method_config=method_config,
                    expected_method_config_sha256=config_digest(method_config),
                    selected_candidate=selected["name"],
                    manifest_sha256=publication.manifest_sha256,
                    evidence_sha256=evidence["sha256"],
                    protocol_config=protocol, catalogs=(), selection_record={},
                    assets={}, store=store,
                )
            captured: dict[str, torch.nn.Module] = {}
            original_restore = store.restore

            def captured_restore(*args: Any, **kwargs: Any) -> Any:
                result = original_restore(*args, **kwargs)
                captured["model"] = result.model
                return result

            def mutate_after_verification(**kwargs: Any) -> VerifiedChoSelection:
                with torch.no_grad():
                    next(captured["model"].parameters()).add_(1)
                return VerifiedChoSelection(selected["name"], evidence["sha256"])

            with patch.object(store, "restore", side_effect=captured_restore), patch(
                "evaluation.phase2_cho_source_restore.verify_cho_selection_evidence",
                side_effect=mutate_after_verification,
            ), self.assertRaisesRegex(ValueError, "restored model or source changed"):
                restore_cho_selected_source(
                    root=root, plan=self.plan(method), method_config=method_config,
                    expected_method_config_sha256=config_digest(method_config),
                    selected_candidate=selected["name"],
                    manifest_sha256=publication.manifest_sha256,
                    evidence_sha256=evidence["sha256"],
                    protocol_config=protocol, catalogs=(), selection_record={},
                    assets={}, store=store,
                )
            for field, replacement, error in (
                ("braindecode", "0.0.0", "dependency versions"),
                ("python", "0.0.0", "dependency versions"),
                ("initial_state_sha256", "0" * 64, "seeded EEGNet initial state"),
            ):
                with self.subTest(field=field):
                    altered_contract = deepcopy(contract)
                    altered_final = deepcopy(evidence["payload"]["final_source_fit"])
                    if field == "initial_state_sha256":
                        altered_final[field] = replacement
                    else:
                        altered_contract["runtime"][field] = replacement
                    altered = envelope("engineering_smoke", {
                        **evidence["payload"],
                        "contract": altered_contract,
                        "contract_sha256": config_digest(altered_contract),
                        "final_source_fit": altered_final,
                    })
                    altered_publication = store.publish(
                        model, altered, evidence_sha256=altered["sha256"],
                        protocol_config=protocol, model_recipe=prepared.model_recipe,
                    )
                    with self.assertRaisesRegex(ValueError, error):
                        restore_cho_selected_source(
                            root=root, plan=self.plan(method), method_config=method_config,
                            expected_method_config_sha256=config_digest(method_config),
                            selected_candidate=selected["name"],
                            manifest_sha256=altered_publication.manifest_sha256,
                            evidence_sha256=altered["sha256"],
                            protocol_config=protocol, catalogs=(), selection_record={},
                            assets={}, store=store,
                        )
            self.assertTrue(publication.manifest_path.is_file())


class ChoSelectedSourceStateWitnessTests(unittest.TestCase):
    """Real safetensors decode, pinned lineage and allocation-bound refusals."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "configs").mkdir()
        (self.root / "configs/base.toml").write_text(
            "[storage]\nminimum_free_gb = 0.0\n", encoding="utf-8",
        )
        self.plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
        self.config = _method_config("eegnet")
        self.candidate = self.config["candidates"][0]
        self.prepared = prepare_cho_source_restore(
            root=self.root, plan=self.plan, method_config=self.config,
            expected_method_config_sha256=config_digest(self.config),
            selected_candidate=self.candidate["name"],
        )
        self.model = _new_model(self.prepared)
        self.initial_sha256 = state_digest(self.model)
        self.protocol: dict[str, Any] = {
            "protocol": {"schema_version": 1}, "datasets": {"cho2017": {}},
        }
        self.contract: dict[str, Any] = {
            "method": "eegnet", "dataset": "cho2017",
            "protocol_sha256": config_digest(self.protocol),
            "source": asdict(capture_source(self.root)),
            "candidates": self.config["candidates"],
            "runtime": {
                "python": platform.python_version(),
                "torch": str(torch.__version__), "numpy": np.__version__,
                "braindecode": version("braindecode"),
                "device": "cpu", "dtype": "float32", "torch_threads": 2,
                "deterministic_algorithms": False,
            },
        }
        self.evidence = self._evidence(self.contract, initial_sha256=self.initial_sha256)
        self.store = SelectedSourceStore(self.root)
        self.publication = self.store.publish(
            self.model, self.evidence, evidence_sha256=self.evidence["sha256"],
            protocol_config=self.protocol, model_recipe=self.prepared.model_recipe,
        )

    def _evidence(
        self, contract: dict[str, Any], *, initial_sha256: str,
    ) -> dict[str, Any]:
        return envelope("engineering_smoke", {
            "purpose": "bounded_eegnet_source_selection",
            "contract": contract, "contract_sha256": config_digest(contract),
            "complete": True, "selected_candidate": self.candidate["name"],
            "final_source_fit": {
                "candidate": self.candidate["name"],
                "candidate_sha256": config_digest(self.candidate),
                "initial_state_sha256": initial_sha256,
                "fitted_state_sha256": self.initial_sha256,
            },
            "outer_target_predictions_performed": False,
        })

    def verify(self, **changes: Any) -> Any:
        arguments: dict[str, Any] = {
            "root": self.root, "plan": self.plan, "method_config": self.config,
            "expected_method_config_sha256": config_digest(self.config),
            "selected_candidate": self.candidate["name"],
            "manifest_sha256": self.publication.manifest_sha256,
            "evidence_sha256": self.evidence["sha256"],
            "protocol_config": self.protocol,
            "expected_model_recipe_sha256": config_digest(self.prepared.model_recipe),
            "expected_model_state_sha256": self.initial_sha256,
            "store": self.store,
        }
        arguments.update(changes)
        with patch(
            "evaluation.phase2_cho_source_restore._available_host_ram_gib",
            return_value=8.0,
        ):
            return verify_cho_selected_source_state(**arguments)

    def test_real_eegnet_round_trip_returns_only_pinned_digests(self) -> None:
        witness = self.verify()
        self.assertEqual(witness.manifest_sha256, self.publication.manifest_sha256)
        self.assertEqual(witness.evidence_sha256, self.evidence["sha256"])
        self.assertEqual(witness.selected_candidate, self.candidate["name"])
        self.assertEqual(witness.model_recipe_sha256, config_digest(self.prepared.model_recipe))
        self.assertEqual(witness.model_state_sha256, self.initial_sha256)
        self.assertEqual(witness.weights_sha256, self.publication.weights_sha256)
        self.assertNotIn("model", witness.__slots__)
        self.assertNotIn("adapter", witness.__slots__)

    def test_static_config_winner_recipe_state_and_source_pins_refuse(self) -> None:
        with self.assertRaisesRegex(ValueError, "static method configuration"):
            self.verify(expected_method_config_sha256="0" * 64)
        changed = deepcopy(self.config)
        changed["candidates"][0]["source"]["learning_rate"] = 0.004
        with self.assertRaisesRegex(ValueError, "static method configuration"):
            self.verify(method_config=changed)
        with self.assertRaisesRegex(ValueError, "selected candidate"):
            self.verify(selected_candidate="other")
        with self.assertRaisesRegex(ValueError, "model recipe"):
            self.verify(expected_model_recipe_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "static method or state pin"):
            self.verify(expected_model_state_sha256="0" * 64)
        wrong = SourceProvenance("unversioned-workspace", "0" * 64, None)
        with patch(
            "evaluation.phase2_selected_source_store.capture_source", return_value=wrong,
        ), self.assertRaisesRegex(ValueError, "manifest differs"):
            self.verify()

    def test_wrong_seeded_initial_state_refuses_before_restore(self) -> None:
        altered = self._evidence(self.contract, initial_sha256="0" * 64)
        publication = self.store.publish(
            self.model, altered, evidence_sha256=altered["sha256"],
            protocol_config=self.protocol, model_recipe=self.prepared.model_recipe,
        )
        with self.assertRaisesRegex(ValueError, "seeded EEGNet initial state"):
            self.verify(
                manifest_sha256=publication.manifest_sha256,
                evidence_sha256=altered["sha256"],
            )

    def test_rehashed_wrong_tensor_refuses_without_model_release(self) -> None:
        tensors = load(self.publication.weights_path.read_bytes())
        first = next(iter(tensors))
        tensors[first] = tensors[first] + 1
        altered_blob = save(tensors)
        altered_sha = hashlib.sha256(altered_blob).hexdigest()
        weights_path = self.publication.weights_path.parent / f"{altered_sha}.safetensors"
        weights_path.write_bytes(altered_blob)
        manifest = json.loads(self.publication.manifest_path.read_bytes())
        payload = manifest["payload"]
        payload["weights_sha256"] = altered_sha
        payload["weights_file"] = f"weights/{altered_sha}.safetensors"
        altered_manifest = envelope("engineering_smoke", payload)
        path = self.publication.manifest_path.parent / f"{altered_manifest['sha256']}.json"
        path.write_bytes((canonical_config_json(altered_manifest) + "\n").encode())
        with self.assertRaisesRegex(ValueError, "tensor bytes differ"):
            self.verify(manifest_sha256=altered_manifest["sha256"])

    def test_oversize_and_low_ram_refuse_before_model_allocation(self) -> None:
        with patch(
            "evaluation.phase2_cho_source_restore._MAXIMUM_EEGNET_WEIGHTS_BYTES",
            self.publication.weights_path.stat().st_size - 1,
        ), patch(
            "evaluation.phase2_cho_source_restore._new_model",
        ) as new_model, self.assertRaisesRegex(ValueError, "byte limit"):
            self.verify()
        new_model.assert_not_called()
        with patch(
            "evaluation.phase2_cho_source_restore._available_host_ram_gib",
            return_value=5.9,
        ), patch(
            "evaluation.phase2_cho_source_restore._new_model",
        ) as new_model, self.assertRaisesRegex(ValueError, "6 GiB"):
            verify_cho_selected_source_state(
                root=self.root, plan=self.plan, method_config=self.config,
                expected_method_config_sha256=config_digest(self.config),
                selected_candidate=self.candidate["name"],
                manifest_sha256=self.publication.manifest_sha256,
                evidence_sha256=self.evidence["sha256"],
                protocol_config=self.protocol,
                expected_model_recipe_sha256=config_digest(self.prepared.model_recipe),
                expected_model_state_sha256=self.initial_sha256,
                store=self.store,
            )
        new_model.assert_not_called()

    def test_changed_weights_identity_refuses_before_store_restore(self) -> None:
        actual_preflight = self.store.preflight_full_weights
        calls = 0

        def replaced(*args: Any, **kwargs: Any) -> Any:
            nonlocal calls
            calls += 1
            if calls == 2:
                other = self.publication.weights_path.with_suffix(".replacement")
                other.write_bytes(self.publication.weights_path.read_bytes())
                other.replace(self.publication.weights_path)
            return actual_preflight(*args, **kwargs)

        with patch.object(
            self.store, "preflight_full_weights", side_effect=replaced,
        ), patch.object(self.store, "restore") as restore, self.assertRaisesRegex(
            ValueError, "changed before bounded restore",
        ):
            self.verify()
        restore.assert_not_called()

    def test_lora_static_seed_materializes_before_contract_and_final_fit_check(self) -> None:
        plan = CasePlan("cho2017", "subject_01", "labram_lora", 5, 11, 1)
        config = _method_config("labram_lora")
        candidates = deepcopy(config["candidates"])
        for row in candidates:
            row["source"]["seed"] = plan.model_seed
        contract = {
            "method": "labram_lora", "dataset": "cho2017",
            "source": asdict(capture_source(self.root)),
            "candidates": candidates,
        }
        fitted = torch.nn.Linear(1, 1).eval()
        model_sha256 = state_digest(fitted)
        final_fit = {
            "candidate": candidates[0]["name"],
            "candidate_sha256": config_digest(candidates[0]),
            "fitted_state_sha256": model_sha256,
            "initial_state_sha256": "0" * 64,
        }
        evidence = {"payload": {"selected_candidate": candidates[0]["name"]}}
        manifest_sha256, evidence_sha256 = "a" * 64, "b" * 64
        weight_sha256 = "c" * 64
        preflight = SelectedWeightsPreflight(
            self.root / "synthetic.safetensors", weight_sha256, (1, 2, 3, 4),
        )
        publication = SimpleNamespace(
            weights_format="full_v1", manifest_sha256=manifest_sha256,
            evidence_sha256=evidence_sha256,
            selected_candidate=candidates[0]["name"],
            weights_sha256=weight_sha256, model_state_sha256=model_sha256,
        )
        restored = SimpleNamespace(
            model=fitted, evidence_record=evidence, publication=publication,
        )
        recipe_architecture = {"architecture": "synthetic_labram"}
        with patch(
            "evaluation.phase2_cho_source_restore._labram_baseline",
            return_value=(recipe_architecture, self.root / "model", self.root / "weights"),
        ), patch(
            "evaluation.phase2_cho_source_restore._check_labram_baseline",
        ), patch(
            "evaluation.phase2_cho_source_restore._runtime_dependencies",
        ), patch(
            "evaluation.phase2_cho_source_restore._available_host_ram_gib",
            return_value=8.0,
        ), patch(
            "evaluation.phase2_cho_source_restore._new_model", return_value=fitted,
        ), patch(
            "evaluation.phase2_cho_source_restore._pre_restore_evidence",
            return_value=(evidence, contract, final_fit),
        ), patch.object(
            self.store, "preflight_full_weights", return_value=preflight,
        ), patch.object(
            self.store, "restore", return_value=restored,
        ):
            prepared = prepare_cho_source_restore(
                root=self.root, plan=plan, method_config=config,
                expected_method_config_sha256=config_digest(config),
                selected_candidate=candidates[0]["name"],
            )
            witness = verify_cho_selected_source_state(
                root=self.root, plan=plan, method_config=config,
                expected_method_config_sha256=config_digest(config),
                selected_candidate=candidates[0]["name"],
                manifest_sha256=manifest_sha256, evidence_sha256=evidence_sha256,
                protocol_config=self.protocol,
                expected_model_recipe_sha256=config_digest(prepared.model_recipe),
                expected_model_state_sha256=model_sha256, store=self.store,
            )
        self.assertEqual(witness.selected_candidate, candidates[0]["name"])
        self.assertEqual(witness.model_state_sha256, model_sha256)


if __name__ == "__main__":
    unittest.main()
