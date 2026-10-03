"""Lightweight source-specific sweep resume checks with real recorder envelopes."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import Mock, patch

from core.config import canonical_config_json, config_digest, load_toml
from core.provenance import SourceProvenance
from evaluation import phase2_cho_sweep as sweep
from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import CellIdentity, envelope
from evaluation.phase2_runner import CasePlan, CaseRecorder, method_configuration


class SweepResumeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
        self.protocol = load_toml("configs/phase2/protocol.toml")
        self.catalogs = tuple(
            TrialCatalog(
                "cho2017", f"subject_{number:02d}",
                tuple(f"subject_{number:02d}/trial_{index:02d}" for index in range(42)),
                ("left_hand", "right_hand") * 21,
                ("left_hand", "right_hand"), "4" * 64, "5" * 64,
            )
            for number in range(1, 53)
        )
        episode = envelope("episode_manifest", nested_episode(
            self.catalogs[0], shots=(1, 5, 10, 20),
            protocol_sha256=config_digest(self.protocol),
        ).payload())
        selection = envelope("source_selection", asdict(source_selection(
            self.catalogs, target=self.plan.target_subject,
        )))
        self.route = ChoFirstTrancheRoute(
            (self.plan,), self.catalogs, MappingProxyType({}),
            canonical_config_json(self.protocol),
            MappingProxyType({self.plan.target_subject: canonical_config_json(selection)}),
            MappingProxyType({self.plan.target_subject: canonical_config_json(episode)}),
        )
        self.method_configs = {
            method: {"method": method, "optimizer": "sgd", "steps": 1,
                     "fit_scope": "source", "preprocessing": "a"}
            for method in ("labram_linear", "labram_lora", "labram_full", "eegnet")
        }
        self.method = self.method_configs["eegnet"]
        self.source = SourceProvenance("1" * 40, "2" * 64, True)
        self.pins = {
            **asdict(self.source), "environment_sha256": "3" * 64,
            "method_config_sha256": {
                method: method_configuration(config)
                for method, config in self.method_configs.items()
            },
        }
        self.identity = CellIdentity(
            "cho2017", "subject_01", "eegnet", 5, 11, None, None,
            config_digest(self.protocol), episode["sha256"], selection["sha256"],
            method_configuration(self.method), self.catalogs[0].preprocessing_sha256,
            "6" * 64, self.source.source_sha256, "3" * 64, self.source.git_commit, True,
        )
        self.metrics = {
            "role": "outer_target", "selection_evidence_sha256": "7" * 64,
            "confusion_matrix": [[1, 0], [0, 1]], "balanced_accuracy": [1, 1],
            "query_count": 2,
        }
        self.recorder = CaseRecorder(self.root)

    def record(self, identity: CellIdentity | None = None) -> dict[str, Any]:
        return envelope("evaluation_cell", {
            "identity": asdict(identity or self.identity), "metrics": self.metrics,
        })

    def test_exact_current_identity_verifies(self) -> None:
        actual = sweep.verify_sweep_resume_cell(
            self.record(), plan=self.plan, route=self.route,
            method_config=self.method, pins=self.pins,
        )
        self.assertEqual(actual, self.identity)

    def test_each_conflicting_pin_refuses_even_when_envelope_is_resealed(self) -> None:
        changed: dict[str, Any] = {
            "dataset": "other", "target_subject": "subject_02", "method": "labram_linear",
            "shots_per_class": 1, "model_seed": 23,
            "support_draw_seed": 0, "montage_seed": 0, "git_dirty": False,
            "git_commit": "9" * 40,
        }
        changed.update({
            field: "9" * 64 for field in (
                "source_sha256", "environment_sha256", "protocol_sha256",
                "episode_sha256", "selection_sha256", "method_config_sha256",
                "preprocessing_sha256",
            )
        })
        for field, value in changed.items():
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(sweep.SweepResumeConflict, field),
            ):
                sweep.verify_sweep_resume_cell(
                    self.record(replace(self.identity, **{field: value})),
                    plan=self.plan, route=self.route, method_config=self.method, pins=self.pins,
                )

    def test_stale_envelope_and_missing_selector_evidence_refuse(self) -> None:
        changed = self.record()
        changed["payload"]["identity"]["source_sha256"] = "9" * 64
        with self.assertRaisesRegex(sweep.SweepResumeConflict, "envelope"):
            sweep.verify_sweep_resume_cell(
                changed, plan=self.plan, route=self.route,
                method_config=self.method, pins=self.pins,
            )
        self.metrics.pop("selection_evidence_sha256")
        with self.assertRaises(sweep.SweepResumeConflict):
            sweep.verify_sweep_resume_cell(
                self.record(), plan=self.plan, route=self.route,
                method_config=self.method, pins=self.pins,
            )

    def test_unfinished_recorder_cell_is_not_counted_complete(self) -> None:
        self.recorder.record_cell(self.identity, metrics=self.metrics)
        receipt = self.run_sweep()
        self.assertEqual(receipt["status"], "stopped")
        self.assertEqual(receipt["completed_cases"], 0)
        self.assertIn("no verified successful attempt", receipt["stop"]["reason"])

    def test_verified_success_is_skipped_and_conflicting_historical_success_refuses(self) -> None:
        self.publish_success()
        receipt = self.run_sweep()
        self.assertEqual(receipt["status"], "complete")
        self.assertEqual(receipt["already_completed_cases"], 1)
        self.assertEqual(receipt["attempted_cases"], 0)
        self.pins["source_sha256"] = "8" * 64
        self.source = replace(self.source, source_sha256="8" * 64)
        receipt = self.run_sweep(receipt_name="conflict.json")
        self.assertEqual(receipt["status"], "stopped")
        self.assertEqual(receipt["completed_cases"], 0)
        self.assertEqual(receipt["stop"]["kind"], "resume_conflict")

    def test_resealed_historical_claim_cannot_complete_a_current_cell(self) -> None:
        self.publish_success()
        claim_path = (
            self.recorder.output_root / "claims" / f"{self.plan.case_id}.attempt1.claim.json"
        )
        claim = json.loads(claim_path.read_text("utf-8"))
        claim["payload"]["source"]["source_sha256"] = "9" * 64
        claim_path.write_bytes((canonical_config_json(envelope(
            "engineering_smoke", claim["payload"],
        )) + "\n").encode("utf-8"))
        receipt = self.run_sweep()
        self.assertEqual(receipt["completed_cases"], 0)
        self.assertEqual(receipt["status"], "stopped")
        self.assertIn("final claim provenance", receipt["stop"]["reason"])

    def publish_success(self) -> None:
        with (
            patch("evaluation.phase2_runner.capture_source", return_value=self.source),
            patch("evaluation.phase2_runner.environment_digest", return_value="3" * 64),
        ):
            self.recorder.claim(self.plan, worker="resume-tests")
            self.recorder.record_cell(self.identity, plan=self.plan, metrics=self.metrics)

    def run_sweep(self, *, receipt_name: str = "receipt.json") -> dict[str, Any]:
        admission_path = self.root / "admission.json"
        admission_path.write_text(json.dumps({
            "schema": sweep.SWEEP_ADMISSION_SCHEMA, "operator": "resume-tests",
            "admitted": True, "timestamp_utc": datetime.now(UTC).isoformat(),
            "probe_cap_minutes": 10.0, "session_cap_minutes": 120.0,
        }), encoding="utf-8")
        case_runner = Mock(side_effect=AssertionError("resume must never perform selection"))
        with (
            patch.object(sweep, "capture_source", return_value=self.source),
            patch.object(sweep, "environment_digest", return_value="3" * 64),
            patch.object(sweep, "sweep_admission_snapshot",
                         return_value={"admission": {"admitted": True}}),
            patch.object(sweep, "_verify_resume_publication"),
            patch.object(sweep, "TargetCaseExecutor"),
        ):
            receipt = sweep.run_cho_first_tranche_sweep(
                root=self.root, recorder=self.recorder, route=self.route,
                admission_path=admission_path, method_configs=self.method_configs,
                case_runner=case_runner, worker="resume-tests",
                receipt_path=self.root / receipt_name,
            )
        case_runner.assert_not_called()
        return receipt


if __name__ == "__main__":
    unittest.main()
