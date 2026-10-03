from __future__ import annotations

import copy
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from sklearn.model_selection import train_test_split

from core.config import config_digest, load_toml
from core.metrics import classification_report
from core.run_record import RunRecord
from evaluation import source_bound_controls as controls
from evaluation.leakage_ci import run_leakage_ci
from scripts import refresh_source_bound_controls as refresh

ROOT = Path(__file__).resolve().parents[1]


def fixture_context():
    return {
        "schema": 1, "source_sha256": "a" * 64,
        "configuration": load_toml(ROOT / "configs/source_bound_controls.toml"),
        "model_configuration": load_toml(ROOT / "configs/eegnet.toml"),
        "specifications": {name: load_toml(ROOT / "configs" / name)
                           for name in controls.CONTROL_NAMES},
        "inputs": {"example.mat": "b" * 64}, "environment": {"test_only": True},
    }


def fixture_record(context, unit):
    name, subject, seed = unit
    gate = context["specifications"][name]["gate_a"]
    classes = sorted(gate["included_labels"])
    labels = np.array(classes * 72 * 2)
    sessions = np.array(["0train"] * (72 * len(classes)) + ["1test"] * (72 * len(classes)))
    development = np.flatnonzero(sessions == "0train")
    query = np.flatnonzero(sessions == "1test")
    train, validation = train_test_split(
        development, test_size=0.2, random_state=seed, stratify=labels[development],
    )
    split = {"train": sorted(train.tolist()), "validation": sorted(validation.tolist()),
             "test": query.tolist()}
    targets = np.array([classes.index(label) for label in labels])
    if gate.get("shuffle_development_labels", False):
        indices = split["train"] + split["validation"]
        shuffled = targets[indices].copy()
        np.random.default_rng(seed).shuffle(shuffled)
        targets[indices] = shuffled
    predictions = [classes[0]] * len(query)
    report = classification_report(labels[query].tolist(), predictions, labels=classes)
    count = gate["training"]["epochs"]
    history = [{"epoch": index + 1, "train_loss": 1 / (index + 1),
                "validation_loss": 1 / (index + 1)} for index in range(count)]
    record = RunRecord.create(
        config=controls.resolved_config(context, unit), seed=seed,
        git_commit="c" * 40, source_sha256=context["source_sha256"], git_dirty=True,
        dataset="BNCI2014-001", fold=f"{Path(name).stem}:subject-{subject}",
        metrics={**report.record_metrics(), "training_and_prediction_seconds": 3.0},
    )
    payload = {
        "schema": 1, "context_sha256": config_digest(context),
        "unit": {"configuration": name, "subject": subject, "seed": seed},
        "record": asdict(record),
        "result": {"metrics": report.as_dict(), "epochs_completed": count,
                   "best_epoch": count, "best_validation_loss": history[-1]["validation_loss"],
                   "history": history, "device": "cuda",
                   "split_counts": {key: len(value) for key, value in split.items()}},
        "resources": {"minimum_observed_free_memory_gib": 8.0, "model_call_checks": 15,
                      "maximum_observed_process_rss_gib": 2.0},
        "signal_identity": {"shape": [len(labels), 22, 1001 if len(classes) == 2 else 128],
                            "dtype": "float32", "sha256": "d" * 64},
        "input_labels": labels.tolist(), "input_sessions": sessions.tolist(), "split": split,
        "training_targets": targets.tolist(), "query_targets": labels[query].tolist(),
        "query_predictions": predictions,
    }
    return json.loads(json.dumps(payload))


class SourceBoundControlTests(unittest.TestCase):
    def setUp(self):
        self.context = fixture_context()
        self.units = controls.expected_units(self.context)

    def test_exact_full_grid_and_both_prediction_protocols(self):
        self.assertEqual(len(self.units), 45)
        for unit in self.units:
            with self.subTest(unit=unit):
                expected = 0.5 if unit[0] == controls.CONTROL_NAMES[0] else 0.25
                self.assertEqual(controls.validate_unit(
                    fixture_record(self.context, unit), self.context, unit), expected)

    def test_duplicate_distribution_discovery_is_not_an_environment_change(self):
        first = SimpleNamespace(metadata={"Name": "Example"}, version="1.0")
        other = SimpleNamespace(metadata={"Name": "Example"}, version="2.0")
        with (
            patch.object(controls.importlib.metadata, "distributions", return_value=[first]),
            patch.object(controls.shutil, "which", return_value="nvidia-smi"),
            patch.object(controls.subprocess, "run", return_value=SimpleNamespace(
                stdout="GPU-example, Test Device, 1.0\n")),
        ):
            expected = controls.environment_identity()
            with patch.object(controls.importlib.metadata, "distributions",
                              return_value=[first, first]):
                self.assertEqual(controls.environment_identity(), expected)
            with patch.object(controls.importlib.metadata, "distributions",
                              return_value=[first, other]):
                self.assertNotEqual(controls.environment_identity(), expected)

    def test_tampered_identity_split_predictions_history_and_guards_fail(self):
        cases = [
            (("context_sha256",), "e" * 64),
            (("record", "source_sha256"), "e" * 64),
            (("record", "git_commit"), "unversioned-workspace"),
            (("record", "git_dirty"), None),
            (("record", "seed"), 53),
            (("record", "config_sha256"), "e" * 64),
            (("record", "timestamp_utc"), "2026-08-31T00:00:00"),
            (("record", "metrics", "training_and_prediction_seconds"), float("nan")),
            (("split", "test", 0), 0),
            (("training_targets", 0), 99),
            (("query_targets", 0), "unknown"),
            (("query_predictions", 0), "right_hand"),
            (("result", "metrics", "balanced_accuracy"), 0.7),
            (("result", "metrics", "confusion_matrix", 0, 0), 99),
            (("result", "device"), "cpu"),
            (("result", "epochs_completed"), 2),
            (("result", "best_epoch"), 1),
            (("result", "history", 0, "validation_loss"), float("nan")),
            (("resources", "minimum_observed_free_memory_gib"), 3.9),
            (("resources", "model_call_checks"), 0),
            (("resources", "model_call_checks"), float("inf")),
            (("resources", "maximum_observed_process_rss_gib"), float("nan")),
            (("signal_identity", "shape", 2), 1),
            (("signal_identity", "dtype"), "float64"),
            (("signal_identity", "sha256"), "not a digest"),
        ]
        for keys, replacement in cases:
            with self.subTest(keys=keys, replacement=replacement):
                payload = fixture_record(self.context, self.units[0])
                target = payload
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = replacement
                with self.assertRaises(ValueError):
                    controls.validate_unit(payload, self.context, self.units[0])

    def test_early_stop_first_boundary_and_untouched_query(self):
        unit = self.units[-1]
        payload = fixture_record(self.context, unit)
        patience = self.context["specifications"][unit[0]]["gate_a"]["training"][
            "early_stopping_patience"]
        count = patience + 1
        result = payload["result"]
        result.update(epochs_completed=count, best_epoch=1, best_validation_loss=1.0,
                      history=[{"epoch": i + 1, "train_loss": 1.0, "validation_loss": 1.0}
                               for i in range(count)])
        self.assertEqual(controls.validate_unit(payload, self.context, unit), 0.25)
        result["history"].append({"epoch": count + 1, "train_loss": 0.1, "validation_loss": 0.1})
        result.update(epochs_completed=count + 1, best_epoch=count + 1, best_validation_loss=0.1)
        with self.assertRaisesRegex(ValueError, "first early-stopping"):
            controls.validate_unit(payload, self.context, unit)

    def test_current_context_cohort_and_input_identity(self):
        with (
            patch.object(controls, "file_digest", return_value="b" * 64) as digest,
            patch.object(controls, "source_fingerprint", return_value="a" * 64),
            patch.object(controls, "environment_identity", return_value={"test_only": True}),
        ):
            context = controls.build_context(ROOT)
            self.assertEqual(len(context["inputs"]), 27)
            self.assertEqual(digest.call_count, 27)
            original = controls.load_toml

            def narrowed(path):
                data = copy.deepcopy(original(path))
                if path.name == "gate_a_shuffle.toml":
                    data["gate_a"]["subjects"] = [1]
                return data

            with (
                patch.object(controls, "load_toml", side_effect=narrowed),
                self.assertRaisesRegex(ValueError, "all original"),
            ):
                controls.build_context(ROOT)

    def test_complete_bundle_resume_staleness_and_context_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            context = self.context
            directory = root / "runs/source_bound_controls" / config_digest(context)
            self.assertFalse(controls.audit_context(root, context)["passed"])
            refresh.atomic_json(directory / "context.json", context)
            for unit in self.units:
                refresh.atomic_json(directory / controls.unit_name(*unit),
                                    fixture_record(context, unit))
            report = controls.audit_context(root, context)
            self.assertTrue(report["passed"])
            self.assertEqual(report["valid_records"], 45)
            for field in ("source_sha256", "inputs", "environment"):
                changed = copy.deepcopy(context)
                changed[field] = "changed"
                self.assertFalse(controls.audit_context(root, changed)["passed"])
            with patch.object(refresh, "ROOT", root), patch.object(
                refresh, "build_context", return_value=context
            ), patch("sys.argv", ["refresh"]), patch("builtins.print"):
                self.assertEqual(refresh.main(), 0)
            with self.assertRaisesRegex(ValueError, "existing control evidence differs"):
                refresh.atomic_json(directory / "context.json", {"changed": True})
            (directory / "context.json").write_text('{"changed": true}\n', encoding="utf-8")
            self.assertIn("context.json", controls.audit_context(root, context)["invalid_records"])

    def test_resource_deferral_precedes_training_and_capture_is_pass_through(self):
        provider = SimpleNamespace(virtual_memory=lambda: SimpleNamespace(available=3 * 1024**3))
        with (
            patch.object(refresh, "build_context", return_value=self.context),
            patch.object(refresh, "audit_context", return_value={
                "passed": False, "invalid_records": {}, "unexpected_records": []}),
            patch("sys.argv", ["refresh"]), patch("builtins.print"),
            patch.object(refresh.importlib, "import_module", return_value=provider),
        ):
            self.assertEqual(refresh.main(), 2)
        predicted = np.array([0, 1, 0])
        capture, saved = refresh.prediction_capture(lambda: predicted)
        self.assertIs(capture(), predicted)
        predicted[0] = 1
        self.assertEqual(saved[0].tolist(), [0, 1, 0])

    def test_merge_check_rejects_stale_bundle_even_with_passing_group_means(self):
        evidence = {"passed": False, "controls": {
            name: {"passed": True} for name in controls.CONTROL_NAMES}}
        with patch("evaluation.leakage_ci.verify_current_controls", return_value=evidence):
            self.assertFalse(run_leakage_ci(ROOT).passed)
        evidence["passed"] = True
        with patch("evaluation.leakage_ci.verify_current_controls", return_value=evidence):
            self.assertTrue(run_leakage_ci(ROOT).passed)
