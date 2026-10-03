"""Small exact-byte checks for the append-only selected-source store."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from threading import Event
from time import sleep
from typing import Any
from unittest.mock import patch

import torch
from safetensors.torch import load, save
from torch import nn

from core.config import canonical_config_json, config_digest
from core.provenance import capture_source
from evaluation.labram_parity import state_digest
from evaluation.phase2_records import envelope, write_once
from evaluation.phase2_selected_source_store import (
    RestoredSelectedSource,
    SelectedSourcePublication,
    SelectedSourceStore,
)


def _model() -> nn.Sequential:
    return nn.Sequential(nn.Linear(3, 2), nn.BatchNorm1d(2))


class _SparseModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.backbone = nn.BatchNorm1d(3)
        self.adapter = nn.Linear(3, 3, bias=False)
        self.head = nn.Linear(3, 2)


def _masked_model(method: str) -> _SparseModel:
    model = _SparseModel().eval()
    model.requires_grad_(False)
    model.head.requires_grad_(True)
    if method == "labram_lora":
        model.adapter.requires_grad_(True)
    return model


class SelectedSourceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name).resolve()
        (self.root / "configs").mkdir()
        (self.root / "configs" / "base.toml").write_text(
            "[storage]\nminimum_free_gb = 0.0\n", encoding="utf-8"
        )
        self.store = SelectedSourceStore(self.root)
        self.model = _model()
        self.protocol = {"protocol": {"schema_version": 1}, "datasets": {"cho2017": {}}}
        self.recipe = {
            "architecture": "small_synthetic_sequential",
            "declared_non_tensor_settings": {"scaling": 1.0},
        }
        self.source = asdict(capture_source(self.root))
        candidate = {
            "name": "first", "source": {"steps_per_subject": 1},
            "support": {"steps": 1},
        }
        contract = {
            "method": "eegnet", "dataset": "cho2017",
            "protocol_sha256": config_digest(self.protocol),
            "source": self.source, "candidates": [candidate],
        }
        self.evidence = envelope(
            "engineering_smoke",
            {
                "purpose": "bounded_eegnet_source_selection",
                "contract": contract,
                "contract_sha256": config_digest(contract),
                "complete": True,
                "selected_candidate": "first",
                "final_source_fit": {
                    "candidate": "first",
                    "candidate_sha256": config_digest(candidate),
                    "fitted_state_sha256": state_digest(self.model),
                },
                "outer_target_predictions_performed": False,
            },
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def publish(self) -> SelectedSourcePublication:
        return self.store.publish(
            self.model, self.evidence, evidence_sha256=self.evidence["sha256"],
            protocol_config=self.protocol, model_recipe=self.recipe,
        )

    def restore(
        self, manifest_sha256: str, model: nn.Module | None = None
    ) -> RestoredSelectedSource:
        return self.store.restore(
            manifest_sha256, model if model is not None else _model(),
            expected_evidence_sha256=self.evidence["sha256"],
            protocol_config=self.protocol, model_recipe=self.recipe,
        )

    def test_restore_bounds_manifest_evidence_and_weights_before_decode(self) -> None:
        publication = self.publish()
        target = _model()
        before = state_digest(target)
        with patch(
            "evaluation.phase2_selected_source_store._MAXIMUM_MANIFEST_BYTES",
            publication.manifest_path.stat().st_size - 1,
        ), self.assertRaisesRegex(ValueError, "byte limit"):
            self.restore(publication.manifest_sha256, target)
        with patch(
            "evaluation.phase2_selected_source_store._MAXIMUM_MANIFEST_BYTES",
            publication.manifest_path.stat().st_size - 1,
        ), self.assertRaisesRegex(ValueError, "byte limit"):
            self.store.read_persisted_evidence_for_manifest(
                publication.manifest_sha256, self.evidence["sha256"],
            )
        with patch(
            "evaluation.phase2_selected_source_store.MAXIMUM_LOGICAL_BYTES",
            publication.evidence_path.stat().st_size - 1,
        ), self.assertRaisesRegex(ValueError, "byte limit"):
            self.restore(publication.manifest_sha256, target)
        with patch(
            "evaluation.phase2_selected_source_store.MAXIMUM_LOGICAL_BYTES",
            publication.evidence_path.stat().st_size - 1,
        ), self.assertRaisesRegex(ValueError, "byte limit"):
            self.store.read_persisted_evidence_for_manifest(
                publication.manifest_sha256, self.evidence["sha256"],
            )
        with patch(
            "evaluation.phase2_selected_source_store.load",
        ) as decode, self.assertRaisesRegex(ValueError, "byte limit"):
            self.store.restore(
                publication.manifest_sha256, target,
                expected_evidence_sha256=self.evidence["sha256"],
                protocol_config=self.protocol, model_recipe=self.recipe,
                maximum_weights_bytes=publication.weights_path.stat().st_size - 1,
            )
        decode.assert_not_called()
        self.assertEqual(state_digest(target), before)

    def test_bounded_weights_read_refuses_growth_and_replacement_before_decode(self) -> None:
        for change in ("growth", "replacement"):
            with self.subTest(change=change):
                publication = self.publish()
                original_weights = publication.weights_path.read_bytes()
                target = _model()
                before = state_digest(target)
                original_open = Path.open
                changed = False

                def change_before_open(
                    path: Path, *args: Any,
                    watched: Path = publication.weights_path,
                    variant: str = change, opener: Any = original_open,
                    **kwargs: Any,
                ) -> Any:
                    nonlocal changed
                    if path == watched and not changed:
                        changed = True
                        if variant == "growth":
                            with opener(path, "ab") as stream:
                                stream.write(b"extra")
                        else:
                            other = path.with_suffix(".replacement")
                            other.write_bytes(path.read_bytes())
                            other.replace(path)
                    return opener(path, *args, **kwargs)

                with patch.object(
                    Path, "open", new=change_before_open,
                ), patch(
                    "evaluation.phase2_selected_source_store.load",
                ) as decode, self.assertRaisesRegex(ValueError, "identity changed"):
                    self.store.restore(
                        publication.manifest_sha256, target,
                        expected_evidence_sha256=self.evidence["sha256"],
                        protocol_config=self.protocol, model_recipe=self.recipe,
                        maximum_weights_bytes=publication.weights_path.stat().st_size,
                    )
                decode.assert_not_called()
                self.assertEqual(state_digest(target), before)
                publication.weights_path.write_bytes(original_weights)

    def sparse_pair(
        self, method: str = "labram_linear"
    ) -> tuple[_SparseModel, _SparseModel, dict[str, Any], dict[str, Any]]:
        initial = _masked_model(method)
        fitted = deepcopy(initial)
        with torch.no_grad():
            for parameter in fitted.parameters():
                if parameter.requires_grad:
                    parameter.add_(0.25)
        names = [name for name, parameter in fitted.named_parameters() if parameter.requires_grad]
        count = sum(
            parameter.numel() for parameter in fitted.parameters() if parameter.requires_grad
        )
        mask: dict[str, Any] = {
            "method": method.removeprefix("labram_"),
            "trainable_names": names,
            "trainable_parameters": count,
        }
        if method == "labram_linear":
            mask.update({
                "depth": 0, "selected_blocks": [],
                "head_policy": "existing_head_always_trainable",
                "support_normalization_policy":
                "all_modules_eval_affine_follows_parameter_mask",
            })
        elif method == "labram_lora":
            mask.update({
                "target_modules": ["adapter"], "rank": 1, "alpha": 1,
                "train_head": True,
                "adapter_parameters": fitted.adapter.weight.numel(),
                "support_normalization_policy":
                "all_modules_eval_source_affine_and_buffers_frozen",
            })
        candidate = {
            "name": "first", "source": {
                "steps_per_subject": 1,
                **({"method": "linear"} if method == "labram_linear" else {
                    "target_modules": ["adapter"], "rank": 1, "alpha": 1,
                    "train_head": True,
                }),
            },
            "support": {"steps": 1},
        }
        contract = {
            "method": method, "dataset": "cho2017",
            "protocol_sha256": config_digest(self.protocol),
            "source": self.source, "candidates": [candidate],
        }
        evidence = envelope("engineering_smoke", {
            "purpose": "bounded_labram_source_selection",
            "contract": contract, "contract_sha256": config_digest(contract),
            "complete": True, "selected_candidate": "first",
            "final_source_fit": {
                "candidate": "first", "candidate_sha256": config_digest(candidate),
                "initial_state_sha256": state_digest(initial),
                "fitted_state_sha256": state_digest(fitted), "mask": mask,
            },
            "outer_target_predictions_performed": False,
        })
        recipe = {
            "schema": "cho_selected_source_architecture_v1",
            "method": method, "dataset": "cho2017", "architecture": "tiny_sparse_test",
        }
        return initial, fitted, evidence, recipe

    def publish_sparse(
        self, initial: _SparseModel, fitted: _SparseModel,
        evidence: Mapping[str, Any], recipe: Mapping[str, Any],
    ) -> SelectedSourcePublication:
        return self.store.publish(
            fitted, evidence, evidence_sha256=evidence["sha256"],
            protocol_config=self.protocol, model_recipe=recipe,
            weights_format="sparse_frozen_init_v2", initial_model=initial,
        )

    def restore_sparse(
        self, publication: SelectedSourcePublication, initial: _SparseModel,
        evidence: Mapping[str, Any], recipe: Mapping[str, Any],
    ) -> RestoredSelectedSource:
        return self.store.restore(
            publication.manifest_sha256, initial,
            expected_evidence_sha256=evidence["sha256"],
            protocol_config=self.protocol, model_recipe=recipe,
        )

    def complete_factored_record(
        self, base: Mapping[str, Any], *, bindings: bool,
    ) -> dict[str, Any]:
        subjects = ["subject_01", "subject_02", "subject_03"]
        identities = {
            subject: {
                "catalog_sha256": hashlib.sha256(subject.encode()).hexdigest(),
                "trial_ids": [f"{subject}-trial-{index:03d}" for index in range(120)],
            }
            for subject in subjects
        }
        payload = deepcopy(base["payload"])
        contract = payload["contract"]
        contract["selection"] = {
            "target_subject": "subject_04", "source_subjects": subjects,
        }
        payload["contract_sha256"] = config_digest(contract)
        final_fit = payload["final_source_fit"]
        final_fit.update({
            "validation_subject": None, "training_subjects": subjects,
            "input_identities": deepcopy(identities),
        })
        folds = []
        for candidate in contract["candidates"]:
            for subject in subjects:
                members = [member for member in subjects if member != subject]
                fold: dict[str, Any] = {
                    "candidate": candidate["name"],
                    "validation_subject": subject,
                    "source_fit": {
                        "candidate": candidate["name"],
                        "validation_subject": subject,
                        "training_subjects": members,
                        "input_identities": {
                            member: deepcopy(identities[member]) for member in members
                        },
                    },
                }
                if bindings:
                    fold["binding"] = {
                        "subject": subject,
                        "episode_sha256": hashlib.sha256(
                            f"episode-{subject}".encode()
                        ).hexdigest(),
                    }
                folds.append(fold)
        payload["folds"] = folds
        return envelope("engineering_smoke", payload)

    def test_round_trip_and_exact_byte_resume(self) -> None:
        first = self.publish()
        self.assertFalse(first.resumed)
        self.assertEqual(first.weights_path.name, first.weights_sha256 + ".safetensors")
        self.assertEqual(first.evidence_path.name, first.evidence_sha256 + ".json")
        self.assertEqual(first.manifest_path.name, first.manifest_sha256 + ".json")
        restored = self.restore(first.manifest_sha256)
        self.assertEqual(state_digest(restored.model), state_digest(self.model))
        self.assertEqual(restored.evidence_record, self.evidence)
        self.assertEqual(restored.publication.selected_candidate, "first")
        second = self.publish()
        self.assertTrue(second.resumed)
        self.assertEqual(second.manifest_path.read_bytes(), first.manifest_path.read_bytes())
        self.assertEqual(len(list(self.store.output.rglob("*.safetensors"))), 1)
        self.assertEqual(len(list(self.store.output.rglob("*.json"))), 2)
        changed_payload = json.loads(first.manifest_path.read_bytes())["payload"]
        changed_payload["unsupported_format_field"] = True
        changed_manifest = envelope("engineering_smoke", changed_payload)
        (first.manifest_path.parent / f"{changed_manifest['sha256']}.json").write_bytes(
            (canonical_config_json(changed_manifest) + "\n").encode("utf-8")
        )
        with self.assertRaisesRegex(ValueError, "manifest fields"):
            self.restore(changed_manifest["sha256"])

    def test_wrong_architecture_recipe_and_protocol_refuse_without_mutation(self) -> None:
        publication = self.publish()
        fresh = _model().double()
        before = state_digest(fresh)
        with self.assertRaisesRegex(ValueError, "tensor schema"):
            self.restore(publication.manifest_sha256, fresh)
        self.assertEqual(state_digest(fresh), before)
        other = nn.Sequential(nn.Linear(3, 4), nn.BatchNorm1d(4))
        before = state_digest(other)
        with self.assertRaisesRegex(ValueError, "tensor schema"):
            self.restore(publication.manifest_sha256, other)
        self.assertEqual(state_digest(other), before)
        with self.assertRaisesRegex(ValueError, "expected context"):
            self.store.restore(
                publication.manifest_sha256, _model(),
                expected_evidence_sha256=self.evidence["sha256"],
                protocol_config=self.protocol,
                model_recipe={"architecture": "wrong"},
            )
        with self.assertRaisesRegex(ValueError, "expected context"):
            self.store.restore(
                publication.manifest_sha256, _model(),
                expected_evidence_sha256=self.evidence["sha256"],
                protocol_config={"protocol": {"schema_version": 2}},
                model_recipe=self.recipe,
            )

    def test_tampered_weights_evidence_and_manifest_refuse(self) -> None:
        publication = self.publish()
        weights = publication.weights_path.read_bytes()
        publication.weights_path.write_bytes(bytes([weights[0] ^ 1]) + weights[1:])
        with self.assertRaisesRegex(ValueError, "file hash"):
            self.restore(publication.manifest_sha256)
        with self.assertRaisesRegex(FileExistsError, "damaged immutable"):
            self.publish()
        publication.weights_path.write_bytes(weights)
        evidence = publication.evidence_path.read_bytes()
        changed = envelope("engineering_smoke", {
            **self.evidence["payload"], "selected_candidate": "second",
        })
        publication.evidence_path.write_bytes(
            (canonical_config_json(changed) + "\n").encode("utf-8")
        )
        with self.assertRaisesRegex(ValueError, "canonical selected evidence"):
            self.restore(publication.manifest_sha256)
        publication.evidence_path.write_bytes(evidence)
        manifest = publication.manifest_path.read_bytes()
        changed_manifest = json.loads(manifest)
        changed_manifest["payload"]["model_recipe"]["architecture"] = "changed"
        publication.manifest_path.write_bytes(
            (canonical_config_json(changed_manifest) + "\n").encode("utf-8")
        )
        with self.assertRaisesRegex(ValueError, "manifest differs"):
            self.restore(publication.manifest_sha256)

    def test_rehashed_wrong_tensor_state_refuses_before_model_mutation(self) -> None:
        publication = self.publish()
        tensors = load(publication.weights_path.read_bytes())
        tensors["0.bias"] = tensors["0.bias"] + 1
        blob = save(tensors)
        digest = hashlib.sha256(blob).hexdigest()
        (publication.weights_path.parent / f"{digest}.safetensors").write_bytes(blob)
        manifest = json.loads(publication.manifest_path.read_bytes())
        payload = manifest["payload"]
        payload["weights_sha256"] = digest
        payload["weights_file"] = f"weights/{digest}.safetensors"
        changed = envelope("engineering_smoke", payload)
        (publication.manifest_path.parent / f"{changed['sha256']}.json").write_bytes(
            (canonical_config_json(changed) + "\n").encode("utf-8")
        )
        target = _model()
        before = state_digest(target)
        with self.assertRaisesRegex(ValueError, "tensor bytes differ"):
            self.restore(changed["sha256"], target)
        self.assertEqual(state_digest(target), before)

    def test_incomplete_evidence_nonfinite_state_and_context_drift_refuse(self) -> None:
        incomplete = envelope(
            "engineering_smoke", {**self.evidence["payload"], "complete": False}
        )
        with self.assertRaisesRegex(ValueError, "complete canonical"):
            self.store.publish(
                self.model, incomplete, evidence_sha256=incomplete["sha256"],
                protocol_config=self.protocol, model_recipe=self.recipe,
            )
        linear = self.model[0]
        assert isinstance(linear, nn.Linear)
        assert linear.bias is not None
        with torch.no_grad():
            linear.bias.fill_(float("inf"))
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            self.publish()
        self.assertFalse(self.store.output.exists())
        with torch.no_grad():
            linear.bias.fill_(0.0)
        changed = replace(capture_source(self.root), source_sha256="c" * 64)
        with patch(
            "evaluation.phase2_selected_source_store.capture_source", return_value=changed
        ), self.assertRaisesRegex(ValueError, "model, source or protocol"):
            self.publish()
        self.assertFalse(self.store.output.exists())

    def test_interrupted_manifest_write_leaves_no_completed_publication(self) -> None:
        def interrupt(
            path: Path, payload: Mapping[str, Any], *, output_root: Path
        ) -> Path:
            if path.parent.name == "manifests":
                raise OSError("simulated interruption")
            return write_once(path, payload, output_root=output_root)

        with patch(
            "evaluation.phase2_selected_source_store.write_once", side_effect=interrupt
        ), self.assertRaisesRegex(OSError, "interruption"):
            self.publish()
        self.assertEqual(len(list(self.store.output.rglob("*.safetensors"))), 1)
        self.assertEqual(len(list(self.store.output.rglob("*.json"))), 1)
        result = self.publish()
        self.assertFalse(result.resumed)
        self.assertTrue(result.manifest_path.is_file())

    def test_concurrent_same_content_publication_and_output_boundary(self) -> None:
        with ThreadPoolExecutor(max_workers=3) as workers:
            results = list(workers.map(lambda _: self.publish(), range(3)))
        self.assertEqual(len({result.manifest_sha256 for result in results}), 1)
        self.assertEqual(len(list(self.store.output.rglob("*.safetensors"))), 1)
        self.assertEqual(len(list(self.store.output.rglob("*.json"))), 2)
        with self.assertRaisesRegex(ValueError, "Phase II directory"):
            SelectedSourceStore(self.root, self.root / "outside")

    def test_distinct_output_publications_cannot_overcommit_disk_floor(self) -> None:
        other_model = deepcopy(self.model)
        other_linear = other_model[0]
        assert isinstance(other_linear, nn.Linear) and other_linear.bias is not None
        with torch.no_grad():
            other_linear.bias.add_(1)
        altered = deepcopy(self.evidence["payload"])
        altered["final_source_fit"]["fitted_state_sha256"] = state_digest(other_model)
        other_evidence = envelope("engineering_smoke", altered)
        phase2 = self.root / "runs" / "phase2"
        other_store = SelectedSourceStore(self.root, phase2 / "other_selected_sources")
        first_guard = Event()
        second_started = Event()
        budget: int | None = None

        def guarded_budget(root: Path, new_bytes: int) -> None:
            nonlocal budget
            self.assertEqual(root, self.root)
            used = sum(
                path.stat().st_size for path in phase2.rglob("*")
                if path.is_file() and path.name != ".selected-source-publication.lock"
            )
            if budget is None:
                budget = new_bytes + 1
                first_guard.set()
                self.assertTrue(second_started.wait(5))
                sleep(0.5)
            if used + new_bytes > budget:
                raise RuntimeError("synthetic disk floor refuses second publication")

        def publish_other() -> SelectedSourcePublication:
            second_started.set()
            return other_store.publish(
                other_model, other_evidence,
                evidence_sha256=other_evidence["sha256"],
                protocol_config=self.protocol, model_recipe=self.recipe,
            )

        with (
            patch(
                "evaluation.phase2_selected_source_store._storage_guard",
                side_effect=guarded_budget,
            ),
            ThreadPoolExecutor(max_workers=2) as workers,
        ):
            first = workers.submit(self.publish)
            self.assertTrue(first_guard.wait(5))
            second = workers.submit(publish_other)
            completed = first.result(timeout=10)
            with self.assertRaisesRegex(RuntimeError, "synthetic disk floor"):
                second.result(timeout=10)
        self.assertIsNotNone(budget)
        self.assertTrue(completed.manifest_path.is_file())
        self.assertEqual(len(list(phase2.rglob("manifests/*.json"))), 1)
        used = sum(
            path.stat().st_size for path in phase2.rglob("*")
            if path.is_file() and path.name != ".selected-source-publication.lock"
        )
        assert budget is not None
        self.assertLessEqual(used, budget)

    def test_publication_lock_hardlink_alias_refuses(self) -> None:
        self.store._directories(create=True)
        external = self.root / "outside-lock"
        external.write_bytes(b"0")
        (self.root / "runs/phase2/.selected-source-publication.lock").hardlink_to(external)
        with self.assertRaisesRegex(ValueError, "lock aliases"):
            self.publish()
        self.assertEqual(len(list(self.store.output.rglob("*.json"))), 0)

    def test_sparse_linear_and_lora_round_trip_and_resume(self) -> None:
        for method in ("labram_linear", "labram_lora"):
            with self.subTest(method=method):
                initial, fitted, evidence, recipe = self.sparse_pair(method)
                first = self.publish_sparse(initial, fitted, evidence, recipe)
                self.assertEqual(first.weights_format, "sparse_frozen_init_v2")
                stored = load(first.weights_path.read_bytes())
                names = evidence["payload"]["final_source_fit"]["mask"]["trainable_names"]
                self.assertEqual(set(stored), set(names))
                self.assertLess(
                    len(first.weights_path.read_bytes()), len(save(fitted.state_dict()))
                )
                target = deepcopy(initial)
                restored = self.restore_sparse(first, target, evidence, recipe)
                self.assertIs(restored.model, target)
                self.assertEqual(state_digest(target), state_digest(fitted))
                self.assertEqual(restored.publication.weights_format, "sparse_frozen_init_v2")
                second = self.publish_sparse(initial, fitted, evidence, recipe)
                self.assertTrue(second.resumed)
                self.assertEqual(second.manifest_sha256, first.manifest_sha256)

    def test_sparse_wrong_initial_seed_and_live_mask_refuse_without_mutation(self) -> None:
        initial, fitted, evidence, recipe = self.sparse_pair()
        publication = self.publish_sparse(initial, fitted, evidence, recipe)
        wrong_seed = deepcopy(initial)
        with torch.no_grad():
            wrong_seed.head.weight.add_(0.01)
        before = state_digest(wrong_seed)
        with self.assertRaisesRegex(ValueError, "initialization or mask"):
            self.restore_sparse(publication, wrong_seed, evidence, recipe)
        self.assertEqual(state_digest(wrong_seed), before)
        wrong_mask = deepcopy(initial)
        wrong_mask.backbone.weight.requires_grad_(True)
        before = state_digest(wrong_mask)
        with self.assertRaisesRegex(ValueError, "live mask"):
            self.restore_sparse(publication, wrong_mask, evidence, recipe)
        self.assertEqual(state_digest(wrong_mask), before)
        with self.assertRaisesRegex(ValueError, "independently reconstructed"):
            self.publish_sparse(fitted, fitted, evidence, recipe)

    def test_sparse_frozen_parameter_and_buffer_changes_refuse_publication(self) -> None:
        for name in ("backbone.weight", "backbone.running_mean"):
            with self.subTest(name=name):
                initial, fitted, evidence, recipe = self.sparse_pair()
                with torch.no_grad():
                    fitted.state_dict()[name].add_(0.125)
                changed = deepcopy(evidence["payload"])
                changed["final_source_fit"]["fitted_state_sha256"] = state_digest(fitted)
                evidence = envelope("engineering_smoke", changed)
                with self.assertRaisesRegex(ValueError, "frozen tensor or buffer"):
                    self.publish_sparse(initial, fitted, evidence, recipe)
                self.assertFalse(self.store.output.exists())

    def test_sparse_bad_final_fit_mask_and_initial_digest_refuse(self) -> None:
        for field, value in (
            ("trainable_names", ["head.weight"]),
            ("trainable_parameters", 1),
        ):
            with self.subTest(field=field):
                initial, fitted, evidence, recipe = self.sparse_pair()
                changed = deepcopy(evidence["payload"])
                changed["final_source_fit"]["mask"][field] = value
                altered = envelope("engineering_smoke", changed)
                with self.assertRaisesRegex(ValueError, "trainable names"):
                    self.publish_sparse(initial, fitted, altered, recipe)
        initial, fitted, evidence, recipe = self.sparse_pair()
        changed = deepcopy(evidence["payload"])
        changed["final_source_fit"]["initial_state_sha256"] = "0" * 64
        altered = envelope("engineering_smoke", changed)
        with self.assertRaisesRegex(ValueError, "reconstructed initial model"):
            self.publish_sparse(initial, fitted, altered, recipe)

    def test_sparse_corruption_and_rehashed_wrong_tensor_refuse_without_mutation(self) -> None:
        initial, fitted, evidence, recipe = self.sparse_pair()
        publication = self.publish_sparse(initial, fitted, evidence, recipe)
        original = publication.weights_path.read_bytes()
        publication.weights_path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
        target = deepcopy(initial)
        before = state_digest(target)
        with self.assertRaisesRegex(ValueError, "file hash"):
            self.restore_sparse(publication, target, evidence, recipe)
        self.assertEqual(state_digest(target), before)
        publication.weights_path.write_bytes(original)
        tensors = load(original)
        tensors["head.bias"] = tensors["head.bias"] + 1
        altered_blob = save(tensors)
        altered_sha = hashlib.sha256(altered_blob).hexdigest()
        (publication.weights_path.parent / f"{altered_sha}.safetensors").write_bytes(
            altered_blob
        )
        manifest = json.loads(publication.manifest_path.read_bytes())
        payload = manifest["payload"]
        payload["weights_sha256"] = altered_sha
        payload["weights_file"] = f"weights/{altered_sha}.safetensors"
        altered_manifest = envelope("engineering_smoke", payload)
        (publication.manifest_path.parent / f"{altered_manifest['sha256']}.json").write_bytes(
            (canonical_config_json(altered_manifest) + "\n").encode("utf-8")
        )
        altered_publication = replace(
            publication, manifest_sha256=altered_manifest["sha256"],
        )
        with self.assertRaisesRegex(ValueError, "complete tensor digest"):
            self.restore_sparse(altered_publication, target, evidence, recipe)
        self.assertEqual(state_digest(target), before)

    def test_sparse_manifest_mask_tamper_and_interrupted_resume(self) -> None:
        initial, fitted, evidence, recipe = self.sparse_pair()

        def interrupt(
            path: Path, payload: Mapping[str, Any], *, output_root: Path
        ) -> Path:
            if path.parent.name == "manifests":
                raise OSError("simulated sparse interruption")
            return write_once(path, payload, output_root=output_root)

        with patch(
            "evaluation.phase2_selected_source_store.write_once", side_effect=interrupt
        ), self.assertRaisesRegex(OSError, "sparse interruption"):
            self.publish_sparse(initial, fitted, evidence, recipe)
        self.assertEqual(len(list(self.store.output.rglob("*.safetensors"))), 1)
        self.assertEqual(len(list(self.store.output.rglob("*.json"))), 1)
        publication = self.publish_sparse(initial, fitted, evidence, recipe)
        self.assertFalse(publication.resumed)
        changed = json.loads(publication.manifest_path.read_bytes())["payload"]
        changed["stored_tensor_names"] = ["head.weight"]
        altered = envelope("engineering_smoke", changed)
        (publication.manifest_path.parent / f"{altered['sha256']}.json").write_bytes(
            (canonical_config_json(altered) + "\n").encode("utf-8")
        )
        target = deepcopy(initial)
        before = state_digest(target)
        with self.assertRaisesRegex(ValueError, "initialization or mask"):
            self.restore_sparse(
                replace(publication, manifest_sha256=altered["sha256"]),
                target, evidence, recipe,
            )
        self.assertEqual(state_digest(target), before)

    def test_sparse_postload_failure_rolls_back_initial_model(self) -> None:
        initial, fitted, evidence, recipe = self.sparse_pair()
        publication = self.publish_sparse(initial, fitted, evidence, recipe)
        target = deepcopy(initial)
        before = state_digest(target)
        original_load = target.load_state_dict
        calls = 0

        def interrupted_load(
            state: Mapping[str, torch.Tensor], *, strict: bool
        ) -> Any:
            nonlocal calls
            calls += 1
            result = original_load(state, strict=strict)
            if calls == 1:
                raise ValueError("simulated postload failure")
            return result

        with (
            patch.object(target, "load_state_dict", side_effect=interrupted_load),
            self.assertRaisesRegex(ValueError, "simulated postload failure"),
        ):
            self.restore_sparse(publication, target, evidence, recipe)
        self.assertEqual(calls, 2)
        self.assertEqual(state_digest(target), before)

    def test_sparse_refuses_other_methods_and_unrecognized_format(self) -> None:
        initial, fitted, evidence, recipe = self.sparse_pair()
        with self.assertRaisesRegex(ValueError, "weights format"):
            self.store.publish(
                fitted, evidence, evidence_sha256=evidence["sha256"],
                protocol_config=self.protocol, model_recipe=recipe,
                weights_format="other",  # type: ignore[arg-type]
            )
        for method in ("labram_full", "eegnet"):
            with self.subTest(method=method):
                changed = deepcopy(evidence["payload"])
                changed["contract"]["method"] = method
                changed["contract_sha256"] = config_digest(changed["contract"])
                altered = envelope("engineering_smoke", changed)
                altered_recipe = {**recipe, "method": method}
                with self.assertRaisesRegex(ValueError, "limited to Cho linear and LoRA"):
                    self.publish_sparse(initial, fitted, altered, altered_recipe)

    def test_factored_bci_and_cho_migrate_without_changing_logical_evidence(self) -> None:
        for method in ("eegnet", "labram_linear"):
            with self.subTest(method=method):
                model: nn.Module
                initial: _SparseModel | None
                if method == "eegnet":
                    model = self.model
                    base = self.evidence
                    recipe = self.recipe
                    initial = None
                else:
                    initial, fitted, base, recipe = self.sparse_pair()
                    model = fitted
                evidence = self.complete_factored_record(
                    base, bindings=method == "labram_linear",
                )
                canonical = self.store.publish(
                    model, evidence, evidence_sha256=evidence["sha256"],
                    protocol_config=self.protocol, model_recipe=recipe,
                )
                factored = self.store.publish(
                    model, evidence, evidence_sha256=evidence["sha256"],
                    protocol_config=self.protocol, model_recipe=recipe,
                    weights_format=(
                        "full_v1" if method == "eegnet" else "sparse_frozen_init_v2"
                    ),
                    initial_model=initial,
                    evidence_format="factored_json_v1",
                )
                self.assertEqual(canonical.evidence_format, "canonical_json_v1")
                self.assertEqual(factored.evidence_format, "factored_json_v1")
                self.assertEqual(canonical.evidence_sha256, factored.evidence_sha256)
                self.assertLess(
                    factored.evidence_path.stat().st_size,
                    canonical.evidence_path.stat().st_size,
                )
                self.assertNotEqual(canonical.evidence_path, factored.evidence_path)
                for publication in (canonical, factored):
                    read, path = self.store.read_persisted_evidence_for_manifest(
                        publication.manifest_sha256, evidence["sha256"],
                    )
                    self.assertEqual(read, evidence)
                    self.assertEqual(path, publication.evidence_path)
                    self.assertEqual(self.store.read_persisted_evidence(
                        path, expected_evidence_sha256=evidence["sha256"],
                    ), evidence)
                    target = _model() if initial is None else deepcopy(initial)
                    restored = self.store.restore(
                        publication.manifest_sha256, target,
                        expected_evidence_sha256=evidence["sha256"],
                        protocol_config=self.protocol, model_recipe=recipe,
                    )
                    self.assertEqual(state_digest(restored.model), state_digest(model))
                    self.assertEqual(restored.evidence_record, evidence)
                    self.assertEqual(restored.publication.evidence_path, path)
                canonical_payload = json.loads(canonical.manifest_path.read_bytes())["payload"]
                factored_payload = json.loads(factored.manifest_path.read_bytes())["payload"]
                self.assertNotIn("evidence_format", canonical_payload)
                self.assertEqual(factored_payload["evidence_format"], "factored_json_v1")
                self.assertEqual(
                    factored_payload["evidence_physical_sha256"],
                    hashlib.sha256(factored.evidence_path.read_bytes()).hexdigest(),
                )
                self.assertEqual(
                    factored_payload["evidence_physical_bytes"],
                    factored.evidence_path.stat().st_size,
                )

    def test_factored_physical_tamper_manifest_tamper_and_alias_refuse(self) -> None:
        evidence = self.complete_factored_record(self.evidence, bindings=False)
        publication = self.store.publish(
            self.model, evidence, evidence_sha256=evidence["sha256"],
            protocol_config=self.protocol, model_recipe=self.recipe,
            evidence_format="factored_json_v1",
        )
        target = _model()
        before = state_digest(target)
        original = publication.evidence_path.read_bytes()
        with patch(
            "evaluation.phase2_selected_source_store.MAXIMUM_PACKED_BYTES",
            len(original) - 1,
        ):
            with self.assertRaisesRegex(ValueError, "byte count"):
                self.store.read_persisted_evidence_for_manifest(
                    publication.manifest_sha256, evidence["sha256"],
                )
            with self.assertRaisesRegex(ValueError, "byte limit"):
                self.store.read_persisted_evidence(
                    publication.evidence_path,
                    expected_evidence_sha256=evidence["sha256"],
                )
        real_fstat = os.fstat
        calls = 0

        def growing_size(descriptor: int) -> os.stat_result:
            nonlocal calls
            calls += 1
            result = real_fstat(descriptor)
            if calls == 2:
                fields = list(result)
                fields[6] += 1
                return os.stat_result(fields)
            return result

        with (
            patch("evaluation.phase2_selected_source_store.os.fstat", growing_size),
            self.assertRaisesRegex(ValueError, "grew, shrank"),
        ):
            self.store.read_persisted_evidence(
                publication.evidence_path,
                expected_evidence_sha256=evidence["sha256"],
            )
        publication.evidence_path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
        with self.assertRaisesRegex(ValueError, "file hash"):
            self.store.restore(
                publication.manifest_sha256, target,
                expected_evidence_sha256=evidence["sha256"],
                protocol_config=self.protocol, model_recipe=self.recipe,
            )
        self.assertEqual(state_digest(target), before)
        publication.evidence_path.write_bytes(original)
        packed = json.loads(original)
        packed["source_identities_by_subject"]["subject_01"]["catalog_sha256"] = "0" * 64
        altered_bytes = (canonical_config_json(packed) + "\n").encode("utf-8")
        altered_sha = hashlib.sha256(altered_bytes).hexdigest()
        (publication.evidence_path.parent / f"{altered_sha}.factored.json").write_bytes(
            altered_bytes
        )
        altered_payload = json.loads(publication.manifest_path.read_bytes())["payload"]
        altered_payload["evidence_physical_sha256"] = altered_sha
        altered_payload["evidence_physical_bytes"] = len(altered_bytes)
        altered_payload["evidence_file"] = f"evidence/{altered_sha}.factored.json"
        altered_manifest = envelope("engineering_smoke", altered_payload)
        (
            publication.manifest_path.parent / f"{altered_manifest['sha256']}.json"
        ).write_bytes((canonical_config_json(altered_manifest) + "\n").encode("utf-8"))
        with self.assertRaisesRegex(ValueError, "envelope|canonical"):
            self.store.read_persisted_evidence_for_manifest(
                altered_manifest["sha256"], evidence["sha256"],
            )
        payload = json.loads(publication.manifest_path.read_bytes())["payload"]
        payload["evidence_schema"] = "wrong"
        changed = envelope("engineering_smoke", payload)
        (publication.manifest_path.parent / f"{changed['sha256']}.json").write_bytes(
            (canonical_config_json(changed) + "\n").encode("utf-8")
        )
        with self.assertRaisesRegex(ValueError, "schema differs"):
            self.store.read_persisted_evidence_for_manifest(
                changed["sha256"], evidence["sha256"],
            )
        for change, expected in (
            ({"unexpected_field": True}, "manifest fields"),
            ({"evidence_physical_bytes": len(original) + 1}, "byte count"),
        ):
            with self.subTest(change=change):
                altered_payload = {
                    **json.loads(publication.manifest_path.read_bytes())["payload"],
                    **change,
                }
                altered = envelope("engineering_smoke", altered_payload)
                (publication.manifest_path.parent / f"{altered['sha256']}.json").write_bytes(
                    (canonical_config_json(altered) + "\n").encode("utf-8")
                )
                with self.assertRaisesRegex(ValueError, expected):
                    self.store.read_persisted_evidence_for_manifest(
                        altered["sha256"], evidence["sha256"],
                    )
        with self.assertRaisesRegex(ValueError, "path aliases"):
            self.store.read_persisted_evidence(
                self.root / "outside", expected_evidence_sha256=evidence["sha256"],
            )
        outside = self.root / "evidence-hardlink"
        outside.hardlink_to(publication.evidence_path)
        with self.assertRaisesRegex(ValueError, "path aliases"):
            self.store.read_persisted_evidence(
                publication.evidence_path, expected_evidence_sha256=evidence["sha256"],
            )

    def test_factored_manifest_interruption_resumes_without_duplicate_physical_bytes(
        self,
    ) -> None:
        evidence = self.complete_factored_record(self.evidence, bindings=False)

        def interrupt(
            path: Path, payload: Mapping[str, Any], *, output_root: Path
        ) -> Path:
            if path.parent.name == "manifests":
                raise OSError("factored manifest interruption")
            return write_once(path, payload, output_root=output_root)

        with patch(
            "evaluation.phase2_selected_source_store.write_once", side_effect=interrupt
        ), self.assertRaisesRegex(OSError, "factored manifest interruption"):
            self.store.publish(
                self.model, evidence, evidence_sha256=evidence["sha256"],
                protocol_config=self.protocol, model_recipe=self.recipe,
                evidence_format="factored_json_v1",
            )
        self.assertEqual(len(list((self.store.output / "manifests").glob("*.json"))), 0)
        self.assertEqual(
            len(list((self.store.output / "evidence").glob("*.factored.json"))), 1,
        )
        publication = self.store.publish(
            self.model, evidence, evidence_sha256=evidence["sha256"],
            protocol_config=self.protocol, model_recipe=self.recipe,
            evidence_format="factored_json_v1",
        )
        self.assertFalse(publication.resumed)
        self.assertEqual(
            len(list((self.store.output / "evidence").glob("*.factored.json"))), 1,
        )


if __name__ == "__main__":
    unittest.main()
