"""Synthetic checks for the proposed no-future matched-control evidence path."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import time
import unittest
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import numpy as np

from core.config import canonical_config_json, config_digest, load_toml
from core.provenance import source_fingerprint
from data.pre_cue_no_future import build_no_future_summary, load_no_future_config
from evaluation import no_future_matched_control as matched
from evaluation.quality_audit import QUALITY_COMMANDS
from evaluation.source_bound_controls import file_digest, resolved_config, unit_name
from scripts import run_no_future_matched_control as runner

ROOT = Path(__file__).resolve().parents[1]


def fixture_context() -> dict[str, Any]:
    preset = load_toml(ROOT / matched.PRESET_RELATIVE)
    gate = matched.effective_gate(preset)
    subject_inputs = {
        str(subject): {
            "signal_shape": [576, 22, 128], "signal_dtype": "float32",
            "signal_sha256": "a" * 64,
            "labels": ["left_hand", "right_hand", "feet", "tongue"] * 144,
            "sessions": ["0train"] * 288 + ["1test"] * 288,
        }
        for subject in matched.SUBJECTS
    }
    return {
        "preset_sha256": matched.PRESET_SHA256,
        "preset": preset,
        "configuration": {"controls": {"device": "cuda"}, "runtime": matched.RUNTIME},
        "specifications": {matched.DIAGNOSTIC_NAME: {"gate_a": gate}},
        "model_configuration": load_toml(ROOT / "configs/eegnet.toml"),
        "subject_inputs": subject_inputs,
        "source_sha256": "b" * 64,
        "quality_bundle": {"status_relative": matched.QUALITY_RELATIVE,
                           "status_sha256": "c" * 64, "source_sha256": "b" * 64},
        "raw_inputs": {},
    }


def fixture_artifact(root: Path) -> tuple[dict[str, Any], Path, Path]:
    config_path = root / "configs/pre_cue_no_future_v1.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_bytes((ROOT / "configs/pre_cue_no_future_v1.toml").read_bytes())
    config = load_no_future_config(config_path)
    writer_path = root / matched.WRITER_RELATIVE
    writer_path.parent.mkdir(parents=True)
    writer_path.write_bytes(b"writer fixture\n")
    source_path = root / "data/pre_cue_no_future.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(b"source fixture\n")
    observed: dict[str, Any] = {
        "source_sha256": {"data/pre_cue_no_future.py": file_digest(source_path)},
        "raw_files": {
            "A01T.mat": {"sha256": "a" * 64, "bytes": 10},
            "A01E.mat": {"sha256": "b" * 64, "bytes": 10},
        },
        "cues_detail": [
            {"subject": 1, "session": session, "run": run,
             "event_index": index, "label": matched.config_labels()[index % 4]}
            for session in matched.SESSIONS for run in matched.RUNS
            for index in range(48)
        ],
    }
    rows = observed["cues_detail"]
    assert isinstance(rows, list)
    signals = np.zeros((576, 22, 128), dtype=np.float32)
    artifact = root / matched.ARTIFACT_PATTERN.format(subject=1)
    artifact.parent.mkdir(parents=True)
    np.savez_compressed(
        artifact, signals=signals,
        labels=np.asarray([row["label"] for row in rows]),
        sessions=np.asarray([row["session"] for row in rows]),
        runs=np.asarray([row["run"] for row in rows]),
        trial_indices=np.asarray([row["event_index"] for row in rows], dtype=np.int64),
        channel_names=np.asarray(config.channel_names),
    )
    summary = asdict(build_no_future_summary(
        subject=1, signals=signals, channel_names=config.channel_names, config=config,
    ))
    manifest_data = {
        "schema_version": 1,
        "manifest_kind": config.manifest_kind,
        "artifact_kind": config.artifact_kind,
        "control_id": config.control_id,
        "status": config.status,
        "subject": 1,
        "artifact": artifact.name,
        "artifact_sha256": file_digest(artifact),
        "artifact_bytes": artifact.stat().st_size,
        "summary": summary,
        "raw_files": observed["raw_files"],
        "signal_audit_receipt_sha256": matched.AUDIT_SHA256,
        "signal_audit_envelope_sha256": matched.AUDIT_ENVELOPE_SHA256,
        "source_sha256": {
            **observed["source_sha256"], matched.WRITER_RELATIVE: file_digest(writer_path),
        },
    }
    manifest = artifact.with_suffix(".manifest.json")
    manifest.write_bytes((canonical_config_json(manifest_data) + "\n").encode())
    return observed, artifact, manifest


class MatchedControlTests(unittest.TestCase):
    def test_effective_gate_changes_only_diagnostic_identity_and_artifact(self) -> None:
        preset = cast(dict[str, Any], load_toml(ROOT / matched.PRESET_RELATIVE))
        before = copy.deepcopy(preset)
        gate = matched.effective_gate(preset)
        self.assertEqual(preset, before)
        self.assertEqual(
            {key for key, value in gate.items() if value != preset["gate_a"][key]},
            {"gate_name", "attempt", "artifact_pattern"},
        )
        self.assertEqual(gate["control_max_accuracy"], 0.35)
        self.assertEqual(gate["training"], preset["gate_a"]["training"])
        self.assertEqual(gate["seeds"], [11, 23, 37, 53])
        context = fixture_context()
        self.assertEqual(len(matched.expected_units(context)), 36)
        changed = copy.deepcopy(context)
        changed["specifications"][matched.DIAGNOSTIC_NAME]["gate_a"]["training"]["epochs"] = 1
        with self.assertRaisesRegex(ValueError, "exactly from the preset"):
            matched.prove_effective_gate(changed)

    def test_independent_npz_manifest_and_signal_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            observed, artifact, manifest = fixture_artifact(root)
            identity = matched.inspect_artifact(root, 1, observed)
            self.assertEqual(identity["artifact_sha256"], file_digest(artifact))
            self.assertEqual(identity["signal_sha256"], hashlib.sha256(
                np.zeros((576, 22, 128), dtype=np.float32).tobytes()
            ).hexdigest())
            changed = json.loads(manifest.read_bytes())
            changed["artifact_sha256"] = "f" * 64
            manifest.write_bytes((canonical_config_json(changed) + "\n").encode())
            with self.assertRaisesRegex(ValueError, "artifact bytes differ"):
                matched.inspect_artifact(root, 1, observed)
            changed["artifact_sha256"] = file_digest(artifact)
            changed["summary"]["filter_phase"] = "minimum"
            manifest.write_bytes((canonical_config_json(changed) + "\n").encode())
            with self.assertRaisesRegex(ValueError, "summary differs"):
                matched.inspect_artifact(root, 1, observed)

    def test_unit_binding_adds_exact_npz_proof_to_shared_validator(self) -> None:
        context = fixture_context()
        unit = (matched.DIAGNOSTIC_NAME, 1, 11)
        payload: dict[str, Any] = {
            key: {} for key in matched.UNIT_KEYS
        }
        payload["diagnostic"] = {
            "kind": matched.DIAGNOSTIC_ID, "status": "proposed_engineering_diagnostic",
            "gate_a_signed": False, "scientific_cell": False,
        }
        payload["signal_identity"] = {
            "shape": [576, 22, 128], "dtype": "float32", "sha256": "a" * 64,
        }
        payload["input_labels"] = context["subject_inputs"]["1"]["labels"]
        payload["input_sessions"] = context["subject_inputs"]["1"]["sessions"]
        payload["record"] = {"config": resolved_config(context, unit)}
        with patch.object(matched, "validate_unit", return_value=0.25) as shared:
            self.assertEqual(matched.validate_matched_unit(payload, context, unit), 0.25)
            shared.assert_called_once()
            forged = copy.deepcopy(payload)
            forged["signal_identity"]["sha256"] = "f" * 64
            with self.assertRaisesRegex(ValueError, "pinned no-future NPZ"):
                matched.validate_matched_unit(forged, context, unit)
            forged = copy.deepcopy(payload)
            forged["diagnostic"]["gate_a_signed"] = True
            with self.assertRaisesRegex(ValueError, "status or schema"):
                matched.validate_matched_unit(forged, context, unit)

    def test_custom_36_unit_audit_and_subject_mean_limit(self) -> None:
        context = fixture_context()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            directory = root / matched.RUNS_RELATIVE / config_digest(context)
            directory.mkdir(parents=True)
            (directory / "context.json").write_text(json.dumps(context), encoding="utf-8")
            for unit in matched.expected_units(context):
                (directory / unit_name(*unit)).write_text("{}", encoding="utf-8")
            with (
                patch.object(matched, "validate_matched_unit", return_value=0.25),
                patch.object(matched, "verify_all_raw"),
                patch.object(matched, "verify_quality_identity"),
            ):
                report = matched.audit_context(root, context)
                self.assertTrue(report["complete"])
                self.assertTrue(report["passed"])
                self.assertEqual(report["valid_records"], 36)
                self.assertEqual(len(report["subject_means"]), 9)
            with (
                patch.object(matched, "validate_matched_unit", return_value=0.36),
                patch.object(matched, "verify_all_raw"),
                patch.object(matched, "verify_quality_identity"),
            ):
                report = matched.audit_context(root, context)
                self.assertTrue(report["complete"])
                self.assertFalse(report["passed"])
            with (
                patch.object(matched, "validate_matched_unit", return_value=0.25),
                patch.object(matched, "verify_all_raw", side_effect=ValueError("raw changed")),
                patch.object(matched, "verify_quality_identity"),
            ):
                report = matched.audit_context(root, context)
                self.assertFalse(report["passed"])
                self.assertIn("raw_files", report["invalid_records"])
            (directory / unit_name(matched.DIAGNOSTIC_NAME, 9, 53)).unlink()
            with patch.object(matched, "validate_matched_unit", return_value=0.25):
                report = matched.audit_context(root, context)
                self.assertFalse(report["complete"])
                self.assertEqual(len(report["missing_records"]), 1)

    def test_sealed_quality_bundle_required_and_bound_to_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            quality_dir = root / "runs/quality/check"
            quality_dir.mkdir(parents=True)
            checks = {}
            for name, command in QUALITY_COMMANDS.items():
                log = quality_dir / f"{name}.txt"
                log.write_text(f"{name} passed\n", encoding="utf-8")
                checks[name] = {
                    "arguments": list(command), "exit_code": 0,
                    "log": log.relative_to(root).as_posix(),
                    "log_sha256": file_digest(log),
                }
            source = source_fingerprint(root)
            status = {
                "passed": True, "checks": checks,
                "source_sha256_before": source, "source_sha256_after": source,
                "source": {"source_sha256": source},
            }
            status_path = root / matched.QUALITY_RELATIVE
            status_path.write_text(json.dumps(status), encoding="utf-8")
            identity = matched.quality_identity(root)
            self.assertEqual(identity["source_sha256"], source)
            self.assertEqual(identity["status_sha256"], file_digest(status_path))
            with self.assertRaisesRegex(ValueError, "differs from matched-control context"):
                matched.verify_quality_identity(
                    root, {"quality_bundle": {**identity, "status_sha256": "f" * 64}}
                )
            (quality_dir / "tests.txt").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale or invalid"):
                matched.quality_identity(root)

    def test_raw_mat_pins_reject_same_size_mutation_and_all18_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            raw_dir = root / matched.RAW_RELATIVE
            raw_dir.mkdir(parents=True)
            pins = {}
            for subject in matched.SUBJECTS:
                for part in ("T", "E"):
                    name = f"A{subject:02d}{part}.mat"
                    path = raw_dir / name
                    path.write_bytes(bytes([subject]) * 16)
                    pins[name] = {"bytes": 16, "sha256": file_digest(path)}
            context = {"raw_inputs": pins}
            matched.verify_all_raw(root, context)
            (raw_dir / "A01E.mat").write_bytes(b"x" * 16)
            with self.assertRaisesRegex(ValueError, "A01E.mat"):
                matched.verify_subject_raw(root, context, 1)
            (raw_dir / "A01E.mat").write_bytes(bytes([1]) * 16)
            (raw_dir / "A09T.mat").write_bytes(b"y" * 16)
            with self.assertRaisesRegex(ValueError, "A09T.mat"):
                matched.verify_all_raw(root, context)

    def test_output_alias_and_prelink_recheck_refuse_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            key = "a" * 64
            directory = matched.ensure_run_namespace(root, key, create=True)
            target = directory / "context.json"
            with (
                patch.object(runner, "_safe_output_path",
                             side_effect=[None, ValueError("parent swapped before link")]),
                patch("scripts.run_no_future_matched_control.os.link") as link,
                self.assertRaisesRegex(ValueError, "parent swapped before link"),
            ):
                runner.publish_json(root, target, {"safe": True})
            link.assert_not_called()
            self.assertFalse(target.exists())
            outside = root / "outside"
            outside.mkdir()
            alias_key = "b" * 64
            alias = root / matched.RUNS_RELATIVE / alias_key
            try:
                os.symlink(outside, alias, target_is_directory=True)
            except OSError:
                # The path-resolution guard itself is tested even if this
                # Windows account lacks symlink creation privilege.
                with (
                    patch.object(matched, "_directory_unaliased", return_value=False),
                    self.assertRaisesRegex(ValueError, "aliases"),
                ):
                    matched.ensure_run_namespace(root)
            else:
                with self.assertRaisesRegex(ValueError, "aliases"):
                    matched.ensure_run_namespace(root, alias_key)

    def test_quality_failure_blocks_supervisor_before_worker_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with (
                patch.object(runner, "startup_guard"),
                patch.object(runner, "verify_quality_identity",
                             side_effect=ValueError("stale quality")),
                patch("scripts.run_no_future_matched_control.subprocess.Popen") as launch,
                self.assertRaisesRegex(ValueError, "stale quality"),
            ):
                runner.supervise(
                    root, fixture_context(), "d" * 64, started_at=time.monotonic()
                )
            launch.assert_not_called()

    def test_stale_quality_blocks_raw_check_in_check_only_mode(self) -> None:
        with (
            patch.object(runner, "quality_identity", side_effect=ValueError("stale quality")),
            patch.object(runner, "run_writer_check") as raw_check,
            self.assertRaisesRegex(ValueError, "stale quality"),
        ):
            runner.main(["--check-only"])
        raw_check.assert_not_called()

    def test_quality_failure_blocks_worker_before_model_preparation(self) -> None:
        context = fixture_context()
        key = config_digest(context)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            namespace = matched.ensure_run_namespace(root, create=True)
            (namespace / ".run.lock").write_text(json.dumps({
                "kind": matched.DIAGNOSTIC_ID,
                "parent_pid": os.getppid(),
                "context_sha256": key,
                "writer_check_stdout_sha256": "d" * 64,
                "source_sha256": "b" * 64,
                "quality_status_sha256": "c" * 64,
            }), encoding="utf-8")
            with (
                patch.object(runner, "source_fingerprint", return_value="b" * 64),
                patch.object(runner, "quality_identity",
                             return_value={"status_sha256": "c" * 64}),
                patch.object(runner, "startup_guard"),
                patch.object(runner, "build_context", return_value=context),
                patch.object(runner, "verify_quality_identity",
                             side_effect=ValueError("stale quality")),
                patch.object(runner, "audit_context") as audit,
                self.assertRaisesRegex(ValueError, "stale quality"),
            ):
                runner.execute_worker(root, key, "d" * 64)
            audit.assert_not_called()

    def test_supervisor_stops_owned_worker_on_active_resource_guard(self) -> None:
        context = fixture_context()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()

            class Worker:
                returncode: int | None = None

                def poll(self) -> int | None:
                    return self.returncode

            worker = Worker()

            def stop_owned(_worker: object) -> None:
                self.assertIs(_worker, worker)
                worker.returncode = -9

            with (
                patch.object(runner, "startup_guard"),
                patch.object(runner, "verify_quality_identity"),
                patch.object(runner, "quality_identity",
                             return_value={"status_sha256": "c" * 64}),
                patch.object(runner, "source_fingerprint", return_value="b" * 64),
                patch("scripts.run_no_future_matched_control.subprocess.Popen",
                      return_value=worker),
                patch.object(runner, "active_guard", side_effect=RuntimeError("low RAM")),
                patch.object(runner, "_stop_owned_worker", side_effect=stop_owned) as stopped,
                self.assertRaisesRegex(RuntimeError, "low RAM"),
            ):
                runner.supervise(root, context, "d" * 64, started_at=time.monotonic())
            stopped.assert_called_once()
            self.assertFalse((root / runner.LOCK_RELATIVE).exists())

    def test_writer_raw_check_requires_all_nine_exact_verified_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            script = root / "scripts/preprocess_pre_cue_no_future_v1.py"
            script.parent.mkdir(parents=True)
            script.write_text("# fixture\n", encoding="utf-8")
            rows = []
            for subject in matched.SUBJECTS:
                artifact = root / matched.ARTIFACT_PATTERN.format(subject=subject)
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_bytes(bytes([subject]))
                rows.append({
                    "subject": subject, "status": "verified_existing",
                    "artifact": str(artifact),
                    "manifest": str(artifact.with_suffix(".manifest.json")),
                    "artifact_sha256": file_digest(artifact),
                })
            stdout = b"".join((json.dumps(row) + "\n").encode() for row in rows)
            result = SimpleNamespace(returncode=0, stdout=stdout, stderr=b"")
            with (
                patch.object(runner, "source_fingerprint", return_value="s" * 64),
                patch("scripts.run_no_future_matched_control.subprocess.run",
                      return_value=result) as executed,
            ):
                self.assertEqual(runner.run_writer_check(root), hashlib.sha256(stdout).hexdigest())
                self.assertIn("--check-only", executed.call_args.args[0])
                result.stdout = b"".join((json.dumps(row) + "\n").encode() for row in rows[:-1])
                with self.assertRaisesRegex(ValueError, "all nine"):
                    runner.run_writer_check(root)

    def test_low_startup_memory_defers_before_raw_check_or_fit(self) -> None:
        with (
            patch.object(runner, "startup_guard", side_effect=RuntimeError("low RAM")),
            patch.object(runner, "run_writer_check") as check,
        ):
            self.assertEqual(runner.main([]), 2)
            check.assert_not_called()

    def test_worker_ownership_accepts_ancestor_supervisor_pid(self) -> None:
        provider = cast(Any, __import__("psutil"))
        chain = []
        process: Any = None
        try:
            process = provider.Process()
            while process is not None and process.pid not in chain:
                chain.append(process.pid)
                process = process.parent()
        except provider.Error:
            pass
        self.assertIn(os.getpid(), chain)
        # A launcher trampoline sits between real supervisors and workers on
        # this host, so any genuine ancestor must satisfy worker ownership.
        ancestor = next(pid for pid in reversed(chain) if pid != os.getpid())
        context = fixture_context()
        key = config_digest(context)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            namespace = matched.ensure_run_namespace(root, create=True)
            (namespace / ".run.lock").write_text(json.dumps({
                "kind": matched.DIAGNOSTIC_ID,
                "parent_pid": ancestor,
                "context_sha256": key,
                "writer_check_stdout_sha256": "d" * 64,
                "source_sha256": "b" * 64,
                "quality_status_sha256": "c" * 64,
            }), encoding="utf-8")
            with (
                patch.object(runner, "source_fingerprint", return_value="b" * 64),
                patch.object(runner, "quality_identity",
                             return_value={"status_sha256": "c" * 64}),
                patch.object(runner, "startup_guard"),
                patch.object(runner, "build_context", return_value=context),
                patch.object(runner, "verify_quality_identity",
                             side_effect=ValueError("stale quality")),
                self.assertRaisesRegex(ValueError, "stale quality"),
            ):
                runner.execute_worker(root, key, "d" * 64)

    def test_worker_ownership_refuses_unrelated_supervisor_pid(self) -> None:
        context = fixture_context()
        key = config_digest(context)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            namespace = matched.ensure_run_namespace(root, create=True)
            (namespace / ".run.lock").write_text(json.dumps({
                "kind": matched.DIAGNOSTIC_ID,
                "parent_pid": 0x7FFFFFF0,
                "context_sha256": key,
                "writer_check_stdout_sha256": "d" * 64,
                "source_sha256": "b" * 64,
                "quality_status_sha256": "c" * 64,
            }), encoding="utf-8")
            with (
                patch.object(runner, "source_fingerprint", return_value="b" * 64),
                patch.object(runner, "quality_identity",
                             return_value={"status_sha256": "c" * 64}),
                patch.object(runner, "startup_guard"),
                patch.object(runner, "build_context", return_value=context),
                self.assertRaisesRegex(
                    ValueError, "matched-control worker does not belong"),
            ):
                runner.execute_worker(root, key, "d" * 64)


if __name__ == "__main__":
    unittest.main()
