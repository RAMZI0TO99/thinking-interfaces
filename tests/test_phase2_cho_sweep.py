"""Cho first-tranche sweep orchestration and production-wiring tests.

Two layers: the orchestration (persisted operator admission, roster resume,
failure advance, write-once receipt) tested with injected fake runners and
recorders, and one real production wiring test at the full 52-subject
cohort whose every verification layer now runs for real under the
committed 5,253-step selection ceiling.
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import patch

import numpy as np
import torch
from braindecode.models import Labram

from core.config import config_digest, load_toml
from core.provenance import SourceProvenance
from evaluation import phase2_cho_sweep as sweep
from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute
from evaluation.phase2_profile_binding import CHO_CHANNELS as MONTAGE
from evaluation.phase2_profile_binding import (
    CHO_CLASSES,
    ChoProfileAssets,
)
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan, CaseRecorder
from scripts.audit_phase2_protocol import file_digest, read_catalog

CHO_CLASSES_TUPLE = CHO_CLASSES
TRIALS_PER_CLASS = 24


def _admission_record(**overrides: Any) -> dict[str, Any]:
    record = {
        "schema": sweep.SWEEP_ADMISSION_SCHEMA,
        "operator": "owner",
        "admitted": True,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "probe_cap_minutes": 10.0,
        "session_cap_minutes": 120.0,
    }
    record.update(overrides)
    return record


def _route(plans: list[CasePlan]) -> ChoFirstTrancheRoute:
    return ChoFirstTrancheRoute(
        tuple(plans), (),
        MappingProxyType({}), "{}",
        MappingProxyType({}), MappingProxyType({}),
    )


class FakeRecorder:
    def __init__(self, root: Path) -> None:
        self.output_root = root / "runs/phase2/recorder"

    def completion(self, plans: list[Any]) -> dict[str, int]:
        return {"measured": len(plans)}


class SweepAdmissionTests(unittest.TestCase):
    def test_load_accepts_fresh_affirmative_record(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "admission.json"
            path.write_text(json.dumps(_admission_record()), encoding="utf-8")
            admission = sweep.SweepAdmission.load(path)
            self.assertEqual(admission.operator, "owner")
            self.assertTrue(admission.admitted)

    def test_load_refuses_bad_records(self) -> None:
        import tempfile

        cases = (
            _admission_record(schema="other"),
            _admission_record(timestamp_utc="not-a-time"),
            _admission_record(timestamp_utc=datetime.now(UTC).replace(tzinfo=None).isoformat()),
            _admission_record(timestamp_utc=(datetime.now(UTC) + timedelta(hours=1)).isoformat()),
            _admission_record(
                timestamp_utc=(datetime.now(UTC) - timedelta(hours=25)).isoformat()
            ),
            _admission_record(probe_cap_minutes=0),
            _admission_record(probe_cap_minutes=float("nan")),
            _admission_record(session_cap_minutes=float("inf")),
            _admission_record(probe_cap_minutes=True),
            _admission_record(probe_cap_minutes=11),
            _admission_record(session_cap_minutes=121),
            _admission_record(operator=""),
        )
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "admission.json"
            for record in cases:
                path.write_text(json.dumps(record), encoding="utf-8")
                with self.assertRaises(ValueError):
                    sweep.SweepAdmission.load(path)

    def test_snapshot_requires_affirmative_record_and_live_guards(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            path = root / "admission.json"
            path.write_text(json.dumps(_admission_record()), encoding="utf-8")
            with (
                patch.object(sweep, "compute_admission", return_value={"admitted": False}),
                self.assertRaisesRegex(ValueError, "live machine guards"),
            ):
                sweep.sweep_admission_snapshot(root, sweep.SweepAdmission.load(path))
            live = {
                "admitted": True, "probe_cap_minutes": 10.0, "session_cap_minutes": 120.0,
            }

            def fake_admission(_root: Path, *, operator_admitted: bool) -> dict[str, Any]:
                self.assertTrue(operator_admitted)
                return dict(live)

            with patch.object(sweep, "compute_admission", side_effect=fake_admission):
                snapshot = sweep.sweep_admission_snapshot(root, sweep.SweepAdmission.load(path))
            self.assertEqual(snapshot["admission"]["probe_cap_minutes"], 10.0)
            self.assertEqual(snapshot["operator"], "owner")
            non_affirmative = sweep.SweepAdmission(
                "owner", False, datetime.now(UTC).isoformat(), 10.0, 120.0,
            )
            with self.assertRaisesRegex(ValueError, "not affirmative"):
                sweep.sweep_admission_snapshot(root, non_affirmative)


class SweepOrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.admission_path = self.root / "admission.json"
        self.admission_path.write_text(
            json.dumps(_admission_record()), encoding="utf-8",
        )
        self.receipt_path = self.root / "sweep" / "receipt.json"
        self.plans = [
            CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1),
            CasePlan("cho2017", "subject_01", "labram_linear", 5, 11, 1),
            CasePlan("cho2017", "subject_02", "eegnet", 5, 23, 1),
        ]
        self.route = _route(self.plans)
        self.method_configs = {
            method: {"method": method, "optimizer": "sgd", "steps": 1,
                     "fit_scope": "source", "preprocessing": "a"}
            for method in ("labram_linear", "labram_lora", "labram_full", "eegnet")
        }
        snapshot = {
            "operator": "owner", "timestamp_utc": datetime.now(UTC).isoformat(),
            "admission": {"admitted": True, "probe_cap_minutes": 10.0,
                          "session_cap_minutes": 120.0},
        }

        def fake_snapshot(_root: Path, _admission: Any) -> dict[str, Any]:
            return dict(snapshot)

        snapshot_patcher = patch.object(
            sweep, "sweep_admission_snapshot", side_effect=fake_snapshot,
        )
        snapshot_patcher.start()
        self.addCleanup(snapshot_patcher.stop)
        executor_patcher = patch.object(
            sweep, "TargetCaseExecutor",
            return_value=object(),
        )
        executor_patcher.start()
        self.addCleanup(executor_patcher.stop)
        source_patcher = patch.object(
            sweep, "capture_source",
            return_value=SourceProvenance("1" * 40, "2" * 64, True),
        )
        self.source_mock = source_patcher.start()
        self.addCleanup(source_patcher.stop)

    def test_sweep_runs_every_case_and_writes_receipt(self) -> None:
        calls: list[str] = []

        def case_runner(**kwargs: Any) -> dict[str, str]:
            plan = kwargs["plan"]
            calls.append(plan.case_id)
            return {"cell": f"cell/{plan.case_id}"}

        receipt = sweep.run_cho_first_tranche_sweep(
            root=self.root, recorder=FakeRecorder(self.root), route=self.route,
            admission_path=self.admission_path,
            method_configs=self.method_configs,
            case_runner=case_runner, worker="draft-tests",
            receipt_path=self.receipt_path,
        )
        self.assertEqual(calls, [plan.case_id for plan in self.plans])
        self.assertEqual(receipt["completed_cases"], 3)
        self.assertEqual(receipt["failed_cases"], 0)
        self.assertEqual(receipt["not_attempted_cases"], 0)
        self.assertEqual(receipt["status"], "complete")
        self.assertTrue(receipt["source_stable"])
        self.assertEqual(receipt["admission_file_sha256"],
                         sweep.SweepAdmission.load(self.admission_path).file_sha256)
        self.assertEqual(receipt["scientific_claims_made"], 0)
        self.assertTrue(self.receipt_path.is_file())

    def test_sweep_skips_measured_cases_and_advances_past_failures(self) -> None:
        measured = {self.plans[0].identity_key: {}}
        calls: list[str] = []

        def case_runner(**kwargs: Any) -> dict[str, str]:
            plan = kwargs["plan"]
            calls.append(plan.case_id)
            if plan is self.plans[1]:
                raise RuntimeError("synthetic case failure")
            return {"cell": f"cell/{plan.case_id}"}

        with (
            patch.object(sweep, "_measured_cell_records", return_value=measured),
            patch.object(sweep, "verify_sweep_resume_cell"),
            patch.object(sweep, "_verify_resume_publication"),
            patch.object(sweep, "_verify_resume_success"),
        ):
            receipt = sweep.run_cho_first_tranche_sweep(
                root=self.root, recorder=FakeRecorder(self.root), route=self.route,
                admission_path=self.admission_path,
                method_configs=self.method_configs,
                case_runner=case_runner, worker="draft-tests",
                receipt_path=self.receipt_path,
            )
        self.assertEqual(calls, [self.plans[1].case_id, self.plans[2].case_id])
        self.assertEqual(receipt["completed_cases"], 2)
        self.assertEqual(receipt["failed_cases"], 1)
        self.assertIn("RuntimeError: synthetic case failure",
                      receipt["outcomes"][self.plans[1].case_id]["reason"])
        self.assertEqual(
            receipt["outcomes"][self.plans[0].case_id]["status"], "already_complete",
        )

    def test_sweep_receipt_is_write_once(self) -> None:
        def case_runner(**kwargs: Any) -> dict[str, str]:
            return {"cell": "cell"}

        sweep.run_cho_first_tranche_sweep(
            root=self.root, recorder=FakeRecorder(self.root), route=self.route,
            admission_path=self.admission_path,
            method_configs=self.method_configs,
            case_runner=case_runner, worker="draft-tests",
            receipt_path=self.receipt_path,
        )
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            sweep.run_cho_first_tranche_sweep(
                root=self.root, recorder=FakeRecorder(self.root), route=self.route,
                admission_path=self.admission_path,
                method_configs=self.method_configs,
                case_runner=case_runner, worker="draft-tests",
                receipt_path=self.receipt_path,
            )

    def test_shared_resource_refusal_stops_before_another_selection(self) -> None:
        for index, error in enumerate((
            sweep.SweepStopped("RAM guard", kind="resource"),
            ValueError("the pilot session cap is exhausted"),
            ValueError("live Cho compute admission failed before claim"),
            MemoryError("allocation failed"),
            RuntimeError("CUDA out of memory"),
            ValueError("source/config identity changed during execution"),
            RuntimeError("source execution resource admission refused: RAM"),
            ValueError("execution runtime differs from the pinned contract"),
        )):
            with self.subTest(error=str(error)):
                calls: list[str] = []

                def case_runner(
                    *, _calls: list[str] = calls, _error: Exception = error, **kwargs: Any,
                ) -> dict[str, str]:
                    _calls.append(kwargs["plan"].case_id)
                    raise _error

                receipt = sweep.run_cho_first_tranche_sweep(
                    root=self.root, recorder=FakeRecorder(self.root), route=self.route,
                    admission_path=self.admission_path, method_configs=self.method_configs,
                    case_runner=case_runner, worker="draft-tests",
                    receipt_path=self.receipt_path.with_name(f"stop-{index}.json"),
                )
                self.assertEqual(calls, [self.plans[0].case_id])
                self.assertEqual(receipt["status"], "stopped")
                self.assertEqual(receipt["stopped_cases"], 1)
                self.assertEqual(receipt["not_attempted_cases"], 2)
                self.assertEqual(receipt["failed_cases"], 0)

    def test_source_mutation_stops_with_honest_partial_receipt(self) -> None:
        source = SourceProvenance("1" * 40, "3" * 64, True)
        calls: list[str] = []

        def case_runner(**kwargs: Any) -> dict[str, str]:
            calls.append(kwargs["plan"].case_id)
            self.source_mock.return_value = source
            return {"cell": "cell"}

        receipt = sweep.run_cho_first_tranche_sweep(
            root=self.root, recorder=FakeRecorder(self.root), route=self.route,
            admission_path=self.admission_path, method_configs=self.method_configs,
            case_runner=case_runner, worker="draft-tests", receipt_path=self.receipt_path,
        )
        self.assertEqual(calls, [self.plans[0].case_id])
        self.assertEqual(receipt["completed_cases"], 0)
        self.assertEqual(receipt["not_attempted_cases"], 2)
        self.assertIn("quarantined_result", receipt["outcomes"][self.plans[0].case_id])
        self.assertFalse(receipt["source_stable"])
        self.assertEqual(receipt["source_before"]["source_sha256"], "2" * 64)
        self.assertEqual(receipt["source_after"]["source_sha256"], "3" * 64)

    def test_rechecks_live_admission_before_each_selection(self) -> None:
        calls: list[str] = []
        snapshots = [
            {"admission": {"admitted": True}},
            {"admission": {"admitted": True}},
            {"admission": {"admitted": True}},
            ValueError("live machine guards refused the sweep admission"),
        ]

        def case_runner(**kwargs: Any) -> dict[str, str]:
            calls.append(kwargs["plan"].case_id)
            return {"cell": "cell"}

        with patch.object(sweep, "sweep_admission_snapshot", side_effect=snapshots):
            receipt = sweep.run_cho_first_tranche_sweep(
                root=self.root, recorder=FakeRecorder(self.root), route=self.route,
                admission_path=self.admission_path, method_configs=self.method_configs,
                case_runner=case_runner, worker="draft-tests", receipt_path=self.receipt_path,
            )
        self.assertEqual(calls, [self.plans[0].case_id])
        self.assertEqual(receipt["completed_cases"], 1)
        self.assertEqual(receipt["stopped_cases"], 1)
        self.assertEqual(receipt["not_attempted_cases"], 1)

    def test_changed_admission_bytes_stop_before_another_selection(self) -> None:
        calls: list[str] = []

        def case_runner(**kwargs: Any) -> dict[str, str]:
            calls.append(kwargs["plan"].case_id)
            self.admission_path.write_text(json.dumps(_admission_record(operator="other")))
            return {"cell": "cell"}

        receipt = sweep.run_cho_first_tranche_sweep(
            root=self.root, recorder=FakeRecorder(self.root), route=self.route,
            admission_path=self.admission_path, method_configs=self.method_configs,
            case_runner=case_runner, worker="draft-tests", receipt_path=self.receipt_path,
        )
        self.assertEqual(calls, [self.plans[0].case_id])
        self.assertEqual(receipt["stop"]["kind"], "admission")

    def test_single_case_drift_is_quarantined_before_complete_counting(self) -> None:
        def case_runner(**kwargs: Any) -> dict[str, str]:
            self.source_mock.return_value = SourceProvenance("1" * 40, "3" * 64, True)
            return {"cell": "unaccepted-cell"}

        receipt = sweep.run_cho_first_tranche_sweep(
            root=self.root, recorder=FakeRecorder(self.root), route=_route(self.plans[:1]),
            admission_path=self.admission_path, method_configs=self.method_configs,
            case_runner=case_runner, worker="draft-tests", receipt_path=self.receipt_path,
        )
        self.assertEqual(receipt["status"], "stopped")
        self.assertEqual(receipt["completed_cases"], 0)
        self.assertEqual(receipt["newly_completed_cases"], 0)
        self.assertEqual(receipt["stopped_cases"], 1)
        self.assertEqual(receipt["not_attempted_cases"], 0)

    def test_whole_case_and_session_deadlines_quarantine_returned_results(self) -> None:
        for elapsed, expected_kind in ((601.0, "case_cap"), (7201.0, "session")):
            with self.subTest(elapsed=elapsed):
                now = [0.0]
                calls: list[str] = []

                def case_runner(
                    *, _elapsed: float = elapsed, _calls: list[str] = calls,
                    _now: list[float] = now, **kwargs: Any,
                ) -> dict[str, str]:
                    _calls.append(kwargs["plan"].case_id)
                    _now[0] = _elapsed
                    return {"cell": "unaccepted-cell"}

                with patch.object(
                    sweep.time, "monotonic", side_effect=lambda clock=now: clock[0],
                ):
                    receipt = sweep.run_cho_first_tranche_sweep(
                        root=self.root, recorder=FakeRecorder(self.root), route=self.route,
                        admission_path=self.admission_path, method_configs=self.method_configs,
                        case_runner=case_runner, worker="draft-tests",
                        receipt_path=self.receipt_path.with_name(f"cap-{int(elapsed)}.json"),
                    )
                self.assertEqual(calls, [self.plans[0].case_id])
                self.assertEqual(receipt["status"], "stopped")
                self.assertEqual(receipt["stop"]["kind"], expected_kind)
                self.assertEqual(receipt["completed_cases"], 0)
                self.assertEqual(receipt["not_attempted_cases"], 2)


class ProductionChoCaseRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd() / "tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "configs").mkdir()
        for name in ("base.toml", "benchmark.toml"):
            (self.root / "configs" / name).write_bytes(
                (Path.cwd() / "configs" / name).read_bytes()
            )
        ceiling = self.root / "configs/phase2"
        ceiling.mkdir(parents=True)
        (ceiling / "selection_ceiling.toml").write_bytes(
            Path("configs/phase2/selection_ceiling.toml").read_bytes()
        )
        self.config = json.loads(json.dumps(load_toml("configs/phase2/protocol.toml")))
        base = load_toml(self.root / "configs/base.toml")["preprocessing"]
        self.catalogs: list[Any] = []
        self.assets: dict[str, ChoProfileAssets] = {}
        self.records: dict[str, dict[str, Any]] = {}
        generator = np.random.default_rng(23)
        for subject in range(1, 53):
            name = f"subject_{subject:02d}"
            total = 2 * TRIALS_PER_CLASS
            for profile, samples in (("a", 512), ("b", 800)):
                directory = self.root / f"data/processed/cho2017/profile_{profile}"
                directory.mkdir(parents=True, exist_ok=True)
                signals = generator.normal(size=(total, 64, samples)).astype(np.float32)
                signals *= 1e-8 if profile == "a" else 0.1
                if profile == "a":
                    signals[0] = 1
                np.savez(
                    directory / f"{name}.npz",
                    signals=signals,
                    labels=np.array(CHO_CLASSES_TUPLE * TRIALS_PER_CLASS),
                    sessions=np.array(["s"] * total),
                    runs=np.array(["r"] * total),
                    trial_indices=np.arange(total),
                    channel_names=np.array(MONTAGE),
                )
                if profile == "b":
                    cfg = copy.deepcopy(base["profile_b"])
                    (directory / f"{name}.manifest.json").write_text(json.dumps(dict(
                        artifact_schema_version=1, artifact_kind="profile_b",
                        subject=subject, shape=[total, 64, samples],
                        channel_names=list(MONTAGE), epoch_duration_s=4.0,
                        sampling_rate_hz=200.0, config_sha256=config_digest(cfg),
                        reference="original", amplitude_unit_mv=0.1,
                        patch_samples=200, patches_per_epoch=4,
                    )))
        threshold = load_toml(self.root / "configs/benchmark.toml")["datasets"]["cho2017"][
            "artifact_threshold_volts"
        ]
        preprocessing = config_digest({
            "profile_identity": self.config["preparation"]["profile_identity"],
            "threshold_config_sha256": file_digest(self.root / "configs/benchmark.toml"),
            "dataset": "cho2017", "threshold": threshold,
        })
        for subject in range(1, 53):
            name = f"subject_{subject:02d}"
            a = self.root / f"data/processed/cho2017/profile_a/{name}.npz"
            b = self.root / f"data/processed/cho2017/profile_b/{name}.npz"
            catalog, _ = read_catalog(
                a, dataset="cho2017", classes=CHO_CLASSES_TUPLE,
                threshold=threshold, preprocessing_sha256=preprocessing,
            )
            self.catalogs.append(catalog)
            self.assets[name] = ChoProfileAssets(
                file_digest(b), file_digest(b.with_suffix(".manifest.json")),
            )
            self.records[name] = envelope(
                "episode_manifest",
                nested_episode(
                    catalog, shots=(1, 5, 10, 20),
                    protocol_sha256=config_digest(self.config),
                ).payload(),
            )
        self.catalogs = tuple(self.catalogs)
        self.selection_records = {}
        for target in self.records:
            selection = source_selection(self.catalogs, target=target)
            self.selection_records[target] = envelope(
                "source_selection", asdict(selection),
            )
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(23)
            backbone = Labram(
                n_times=800, n_chans=64, n_outputs=0, num_layers=2,
                drop_prob=0.2, attn_drop_prob=0.2,
            )
        from encoder.labram import LaBraMClassifier

        self.template = LaBraMClassifier(backbone, classes=2, channel_names=MONTAGE)
        self.template.eval()
        self.recorder = CaseRecorder(
            self.root, output_root=self.root / "runs/phase2/recorder",
        )
        from evaluation.phase2_pilot import compute_admission

        self.admission = compute_admission(
            self.root, operator_admitted=True, disk_free_bytes=100 * 1024**3,
            gpu_memory_mib=12288, free_host_ram_gib=16.0,
        )
        self.method_config = {
            "method": "eegnet", "dataset": "cho2017",
            "input_profile": "cho_profile_a", "variant_config_sha256": None,
            "candidates": [
                {"name": "eeg_a",
                 "source": {"steps_per_subject": 1, "batch_size": 4,
                            "learning_rate": 0.001, "input_scale": 1_000_000.0},
                 "support": {"steps": 1, "learning_rate": 0.001,
                             "input_scale": 1_000_000.0}},
                {"name": "eeg_b",
                 "source": {"steps_per_subject": 1, "batch_size": 4,
                            "learning_rate": 0.002, "input_scale": 1_000_000.0},
                 "support": {"steps": 1, "learning_rate": 0.002,
                             "input_scale": 1_000_000.0}},
            ],
            "source_seed_policy": "none",
            "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
            "score": "mean_subject_balanced_accuracy_exact_rational",
            "tie_break": "first_in_declared_candidate_order",
            "early_stopping": False,
        }

    def test_eegnet_case_full_real_wiring_and_ceiling_boundaries(self) -> None:
        from evaluation.phase2_pilot import TargetCaseExecutor
        from evaluation.phase2_selection_evidence_binding import (
            VerifiedChoSelection,
            verify_cho_selection_evidence,
        )

        executor = TargetCaseExecutor(
            self.root, self.recorder, admission=self.admission,
            worker="sweep-tests",
        )
        runner = sweep.ProductionChoCaseRunner(
            root=self.root, recorder=self.recorder, protocol_config=self.config,
            catalogs=self.catalogs, episode_records=self.records,
            selection_records=self.selection_records, profile_assets=self.assets,
            profile_a_manifests={}, labram_template=None,
            maximum_gradient_steps=5253,
        )
        plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 23, 1)

        # Execute the real preclaim gate using the runner's actual handoff.
        # This catches the former EEGNet/B-assets mismatch before any claim,
        # while target prediction remains outside this wiring test.
        recorded: dict[str, Any] = {}

        def fake_run_case(runner_self: Any, run_plan: Any, **kwargs: Any) -> dict[str, Any]:
            from evaluation.phase2_cho_execution_gate import verify_cho_case_preclaim

            arguments = dict(
                root=self.root, plan=run_plan, adapter=kwargs["adapter"],
                identity=kwargs["identity"], method_config=kwargs["method_config"],
                evidence_path=kwargs["selection_evidence_path"],
                evidence_sha256=kwargs["selection_evidence_sha256"],
                protocol_config=kwargs["protocol_config"], catalogs=kwargs["catalogs"],
                selection_record=kwargs["selection_record"], assets=kwargs["assets"],
            )
            verified = verify_cho_case_preclaim(**arguments)
            self.assertIsInstance(verified, VerifiedChoSelection)
            with self.assertRaisesRegex(ValueError, "empty Profile A sidecar map"):
                verify_cho_case_preclaim(**{**arguments, "assets": self.assets})
            recorded["plan"] = run_plan
            recorded.update(kwargs)
            cell = self.recorder.output_root / "wiring-cell.json"
            cell.parent.mkdir(parents=True, exist_ok=True)
            cell.write_text("{}", encoding="utf-8")
            return {"cell": str(cell)}

        from evaluation.phase2_pilot import AnchorAdapter
        from evaluation.phase2_pilot import TargetCaseExecutor as Executor

        with patch.object(Executor, "run_case", autospec=True, side_effect=fake_run_case):
            result = runner(
                plan=plan, executor=executor, route=None,
                method_config=self.method_config,
            )
        self.assertTrue(Path(result["cell"]).is_file())
        self.assertIs(recorded["plan"], plan)
        self.assertIsInstance(recorded["adapter"], AnchorAdapter)
        self.assertEqual(
            recorded["selection_evidence_sha256"], result["selection_evidence_sha256"],
        )
        self.assertEqual(recorded["identity"].episode_sha256,
                         self.records["subject_01"]["sha256"])
        self.assertIs(recorded["catalogs"], self.catalogs)
        self.assertEqual(recorded["assets"], {})
        evidence_path = (
            self.root / "runs/phase2/selection_evidence"
            / f"{result['selection_evidence_sha256']}.json"
        )
        self.assertTrue(evidence_path.is_file())
        weights_path = (
            self.root / "runs/phase2/selected_sources/weights"
            / f"{result['selected_weights_sha256']}.safetensors"
        )
        self.assertTrue(weights_path.is_file())

        # The real binder now ADMITS the runner's own persisted evidence at
        # the committed 5,253 ceiling, and refuses anything above it.
        persisted = json.loads(evidence_path.read_text("utf-8"))
        materialized = sweep.materialize_cho_candidates(
            "eegnet", self.method_config, plan.model_seed,
        )
        winner = next(
            c for c in materialized
            if c.name == persisted["payload"]["selected_candidate"]
        )
        arguments = dict(
            record=persisted, evidence_sha256=result["selection_evidence_sha256"],
            plan=plan, protocol_config=self.config, catalogs=self.catalogs,
            selection_record=self.selection_records["subject_01"],
            assets={}, root=self.root,
            adapter_model_state_sha256=persisted["payload"]["final_source_fit"][
                "fitted_state_sha256"
            ],
            adapter_source_settings=asdict(winner.source),
            adapter_support_settings=asdict(winner.support),
        )
        verified = verify_cho_selection_evidence(**arguments)
        self.assertIsInstance(verified, VerifiedChoSelection)
        self.assertEqual(
            verified.selected_candidate, persisted["payload"]["selected_candidate"],
        )
if __name__ == "__main__":
    unittest.main()
