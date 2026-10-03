"""Isolated Cho tensor-case child and executor checks; no scientific runner."""

from __future__ import annotations

import json
import platform
import subprocess
import tempfile
import unittest
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import torch

from core.config import config_digest
from core.provenance import capture_source
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_analysis_preparation import run_cho_tensor_case_child
from evaluation.phase2_cho_source_restore import (
    _new_model,
    prepare_cho_source_restore,
)
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_selected_source_store import SelectedSourceStore

ROOT = Path(__file__).resolve().parents[1]
CHILD = ROOT / "scripts" / "run_cho_tensor_case_child.py"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


def _eegnet_method_config() -> dict[str, Any]:
    candidates = []
    for name, learning_rate in (("lr_1e-3", 0.001), ("lr_2e-3", 0.002)):
        candidates.append({
            "name": name,
            "source": {
                "steps_per_subject": 1, "batch_size": 4,
                "learning_rate": learning_rate, "input_scale": 1_000_000.0,
            },
            "support": {
                "steps": 1, "learning_rate": learning_rate,
                "input_scale": 1_000_000.0, "query_batch_size": 8,
            },
        })
    return {
        "method": "eegnet", "dataset": "cho2017",
        "input_profile": "cho_profile_a",
        "variant_config_sha256": None,
        "candidates": candidates,
        "source_seed_policy": "none",
        "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
        "score": "mean_subject_balanced_accuracy_exact_rational",
        "tie_break": "first_in_declared_candidate_order",
        "early_stopping": False,
    }


class TensorCaseChildRefusalTests(unittest.TestCase):
    """Child refusals that need no publication tree."""

    def _run_child(self, input_path: Path, witness_path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(PYTHON), "-B", str(CHILD),
             "--input", str(input_path), "--witness", str(witness_path)],
            capture_output=True, text=True, timeout=180,
        )

    def test_child_refuses_unknown_input_schema(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            input_path = directory / "case.input.json"
            witness_path = directory / "case.witness.json"
            input_path.write_text(json.dumps({
                "schema": "something-else", "case_id": "case-x", "plan": {
                    "dataset": "cho2017", "target_subject": "subject_01",
                    "method": "eegnet", "shots_per_class": 5,
                    "model_seed": 11, "repetition": 1,
                },
            }), encoding="utf-8")
            process = self._run_child(input_path, witness_path)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("pinned schema", process.stderr)
            self.assertFalse(witness_path.exists())

    def test_child_refuses_existing_witness_without_touching_it(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            input_path = directory / "case.input.json"
            witness_path = directory / "taken.witness.json"
            witness_path.write_text("taken", encoding="utf-8")
            process = self._run_child(input_path, witness_path)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("already exists", process.stderr)
            self.assertEqual(witness_path.read_text(encoding="utf-8"), "taken")


class TensorCaseExecutorTests(unittest.TestCase):
    """One real supervised child verifies a synthetic EEGNet publication."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "configs").mkdir()
        (self.root / "configs/base.toml").write_text(
            "[storage]\nminimum_free_gb = 0.0\n", encoding="utf-8",
        )
        self.workspace = self.root / "case-workspace"
        self.workspace.mkdir()
        self.plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
        self.config = _eegnet_method_config()
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
        contract = {
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
        evidence = envelope("engineering_smoke", {
            "purpose": "bounded_eegnet_source_selection",
            "contract": contract, "contract_sha256": config_digest(contract),
            "complete": True, "selected_candidate": self.candidate["name"],
            "final_source_fit": {
                "candidate": self.candidate["name"],
                "candidate_sha256": config_digest(self.candidate),
                "initial_state_sha256": self.initial_sha256,
                "fitted_state_sha256": self.initial_sha256,
            },
            "outer_target_predictions_performed": False,
        })
        store = SelectedSourceStore(self.root)
        self.publication = store.publish(
            self.model, evidence, evidence_sha256=evidence["sha256"],
            protocol_config=self.protocol, model_recipe=self.prepared.model_recipe,
        )
        self.kwargs: dict[str, Any] = {
            "root": self.root, "workspace": self.workspace,
            "case_id": "case-e2e", "plan": self.plan,
            "method_config": self.config,
            "expected_method_config_sha256": config_digest(self.config),
            "selected_candidate": self.candidate["name"],
            "manifest_sha256": self.publication.manifest_sha256,
            "evidence_sha256": evidence["sha256"],
            "protocol_config": self.protocol,
            "expected_model_recipe_sha256": config_digest(self.prepared.model_recipe),
            "expected_model_state_sha256": self.initial_sha256,
        }

    def test_real_supervised_child_returns_pinned_witness(self) -> None:
        witness = run_cho_tensor_case_child(
            **self.kwargs, memory_limit_bytes=4 * 1024**3, attempt_seconds=240.0,
        )
        self.assertEqual(witness["schema"], "cho_tensor_case_child_witness_v1")
        self.assertEqual(witness["case_id"], "case-e2e")
        self.assertEqual(witness["manifest_sha256"], self.publication.manifest_sha256)
        self.assertEqual(witness["model_state_sha256"], self.initial_sha256)
        self.assertEqual(witness["weights_sha256"], self.publication.weights_sha256)
        witness_path = self.workspace / "case_case_e2e.witness.json"
        self.assertTrue(witness_path.is_file())

    def test_executor_refuses_reused_workspace_for_same_case(self) -> None:
        run_cho_tensor_case_child(
            **self.kwargs, memory_limit_bytes=4 * 1024**3, attempt_seconds=240.0,
        )
        with self.assertRaisesRegex(ValueError, "already holds this case"):
            run_cho_tensor_case_child(
                **self.kwargs, memory_limit_bytes=4 * 1024**3,
                attempt_seconds=240.0,
            )

    def test_executor_surfaces_child_digest_failure(self) -> None:
        wrong = dict(self.kwargs)
        wrong["case_id"] = "case-bad"
        wrong["expected_model_state_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "tensor case child for case-bad failed"):
            run_cho_tensor_case_child(
                **wrong, memory_limit_bytes=4 * 1024**3, attempt_seconds=240.0,
            )
        self.assertFalse((self.workspace / "case_case_bad.witness.json").exists())
