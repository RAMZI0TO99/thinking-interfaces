"""Synthetic guard tests: no dataset loads, model imports or scientific fits."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import psutil  # type: ignore[import-untyped]

from core.provenance import source_fingerprint
from evaluation.quality_audit import QUALITY_COMMANDS
from scripts import run_guarded_quality as runner
from scripts import verify_phase1_quality as quality


def quality_payload(root: Path, source: str, attempt_id: str) -> dict[str, Any]:
    logs = root / "runs/quality" / attempt_id
    logs.mkdir(parents=True)
    checks = {}
    for name, command in QUALITY_COMMANDS.items():
        log = logs / f"{name}.txt"
        log.write_text("passed\n", encoding="utf-8")
        checks[name] = {
            "arguments": list(command),
            "exit_code": 0,
            "log": log.relative_to(root).as_posix(),
            "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        }
    return {
        "passed": True,
        "attempt_id": attempt_id,
        "source_sha256_before": source,
        "source_sha256_after": source,
        "checks": checks,
    }


class FakeChild:
    def __init__(self, *, finished: bool = True) -> None:
        self.returncode: int | None = 0 if finished else None

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        return int(self.returncode or 0)


class FakeTree:
    instances: list[FakeTree] = []

    def __init__(self, child: FakeChild) -> None:
        self.child = child
        self.stopped = False
        self.instances.append(self)

    def refresh(self) -> None:
        pass

    def living(self) -> list[FakeChild]:
        return [] if self.child.returncode is not None else [self.child]

    def stop(self) -> None:
        self.stopped = True
        self.child.returncode = -15


def resources(ram: float = 12.0, disk: float = 20.0) -> dict[str, float | str]:
    return {"timestamp_utc": "synthetic", "available_ram_gib": ram, "free_disk_gib": disk}


class GuardedQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "core").mkdir()
        (self.root / "core/source.py").write_text("value = 1\n", encoding="utf-8")
        self.source = source_fingerprint(self.root)
        self.attempt = runner.ATTEMPT_DIRECTORY / "synthetic"
        self.archive = self.root / runner.ARCHIVE_DIRECTORY / "synthetic.json"
        FakeTree.instances = []

    def run_synthetic(
        self, *, emit_status: bool = True, foreign_status: bool = False,
        finished: bool = True, resource_points: list[dict[str, float | str]] | None = None,
        fingerprints: list[str] | None = None, deadline: bool = False,
        interrupt: bool = False, corrupt_logs: bool = False,
        publish: bool = False, mutate_status_before_archive: bool = False,
        final_event: str | None = None,
        max_wall_seconds: float | None = None,
        monotonic_points: list[float] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        def launch(command: list[str], **kwargs: Any) -> FakeChild:
            if emit_status:
                token = command[command.index("--attempt-id") + 1]
                payload = quality_payload(
                    self.root, self.source, "f" * 32 if foreign_status else token,
                )
                if corrupt_logs:
                    (self.root / payload["checks"]["tests"]["log"]).write_text("corrupted")
                output = Path(command[command.index("--status-output") + 1])
                runner.write_once(output, payload)
            return FakeChild(finished=finished)

        with ExitStack() as stack:
            stack.enter_context(patch.object(runner.subprocess, "Popen", side_effect=launch))
            stack.enter_context(patch.object(runner, "OwnedProcessTree", FakeTree))
            stack.enter_context(patch.object(runner.time, "sleep"))
            if interrupt:
                samples: list[Any] = [resources(), resources(), KeyboardInterrupt(), resources()]
            else:
                samples = resource_points or [resources()] * 8
            stack.enter_context(patch.object(runner, "sample_resources", side_effect=samples))
            if fingerprints is not None:
                stack.enter_context(
                    patch.object(runner, "source_fingerprint", side_effect=fingerprints)
                )
            if mutate_status_before_archive or final_event is not None:
                original_verifier = runner.verify_quality_bundle
                calls = 0

                def verify_and_mutate(root: Path, payload: dict[str, Any]) -> bool:
                    nonlocal calls
                    calls += 1
                    if calls == 2 and mutate_status_before_archive:
                        path = self.root / self.attempt / "quality_status.json"
                        changed = json.loads(path.read_text("utf-8"))
                        changed["changed"] = True
                        path.write_text(json.dumps(changed), encoding="utf-8")
                    if calls == 4:
                        if final_event == "corrupt_log_after_archive":
                            (root / payload["checks"]["tests"]["log"]).write_text("corrupted")
                        elif final_event == "source_drift_after_archive":
                            (root / "core/source.py").write_text("value = 2\n")
                        elif final_event == "cancel_after_archive":
                            raise KeyboardInterrupt("synthetic finalization cancellation")
                    if calls == 5:
                        if final_event == "cancel_after_pointer":
                            raise KeyboardInterrupt("synthetic post-publication cancellation")
                        if final_event == "other_writer_after_pointer":
                            (root / "runs/quality_status.json").write_text(
                                '{"other_writer": true}\n'
                            )
                            raise RuntimeError("synthetic later finalization failure")
                    return original_verifier(root, payload)

                stack.enter_context(patch.object(
                    runner, "verify_quality_bundle", side_effect=verify_and_mutate,
                ))
            if deadline:
                if max_wall_seconds is None:
                    max_wall_seconds = 3.5
                monotonic_points = monotonic_points or [0, 1, 4, 5]
            if monotonic_points is not None:
                stack.enter_context(
                    patch.object(runner.time, "monotonic", side_effect=monotonic_points)
                )
            stack.enter_context(redirect_stdout(StringIO()))
            arguments: dict[str, Any] = {"publish_current_status": publish}
            if max_wall_seconds is not None:
                arguments["max_wall_seconds"] = max_wall_seconds
            result = runner.run_attempt(
                self.root, self.source, self.attempt, **arguments,
            )
        receipt = json.loads((self.root / self.attempt / "receipt.json").read_text("utf-8"))
        return result, receipt

    def test_current_attempt_passes_and_archives_a_verified_bundle(self) -> None:
        result, receipt = self.run_synthetic()
        self.assertEqual(result, 0)
        self.assertTrue(receipt["quality_bundle_verified"])
        self.assertTrue(self.archive.exists())
        self.assertEqual(receipt["scientific_fit_count"], 0)
        self.assertFalse(receipt["scientific_admission"])
        self.assertEqual(receipt["maximum_wall_seconds"], 4200.0)
        self.assertEqual(receipt["policy_maximum_wall_seconds"], 4200.0)

    def test_short_wall_expiry_stops_owned_work_without_pass_archive(self) -> None:
        result, receipt = self.run_synthetic(
            finished=False, deadline=True, max_wall_seconds=3.5,
        )
        self.assertEqual(result, 1)
        self.assertEqual(receipt["stop_reason"], "quality-only wall limit")
        self.assertTrue(FakeTree.instances[0].stopped)
        self.assertEqual(receipt["maximum_wall_seconds"], 3.5)
        self.assertEqual(receipt["policy_maximum_wall_seconds"], 4200.0)
        self.assertFalse(self.archive.exists())
        before = json.loads((self.root / self.attempt / "before.json").read_text("utf-8"))
        self.assertEqual(before["maximum_wall_seconds"], 3.5)

    def test_short_wall_expiry_during_startup_never_launches_verifier(self) -> None:
        result, receipt = self.run_synthetic(
            max_wall_seconds=0.5, monotonic_points=[0, 1, 2],
        )
        self.assertEqual(result, 1)
        self.assertEqual(receipt["stop_reason"], "quality-only wall limit")
        self.assertEqual(FakeTree.instances, [])
        self.assertFalse(self.archive.exists())
        self.assertIsNone(receipt["exit_code"])

    def test_short_wall_expiry_during_final_commit_quarantines_the_new_archive(self) -> None:
        for scenario, publish, prior in (
            ("unpublished", False, None),
            ("published_without_prior", True, None),
            ("published_with_prior", True, b'{"previous": true}\n'),
        ):
            with self.subTest(scenario=scenario):
                self.attempt = runner.ATTEMPT_DIRECTORY / scenario
                self.archive = self.root / runner.ARCHIVE_DIRECTORY / f"{scenario}.json"
                current = self.root / "runs/quality_status.json"
                if prior is not None:
                    current.parent.mkdir(parents=True, exist_ok=True)
                    current.write_bytes(prior)
                result, receipt = self.run_synthetic(
                    publish=publish, max_wall_seconds=3.5, monotonic_points=[0, 1, 2, 4, 5],
                )
                self.assertEqual(result, 1)
                self.assertIn("wall limit during final commit", receipt["error"])
                self.assertIsNone(receipt["pass_archive"])
                self.assertFalse(self.archive.exists())
                self.assertTrue((self.root / receipt["quarantined_quality_archive"]).exists())
                self.assertEqual(receipt["current_status_publication_occurred"], publish)
                self.assertEqual(receipt["current_status_restored"], publish)
                self.assertFalse(receipt["current_status_published"])
                if prior is None:
                    self.assertFalse(current.exists())
                else:
                    self.assertEqual(current.read_bytes(), prior)

    def test_invalid_wall_caps_are_rejected_before_claiming_an_attempt(self) -> None:
        for cap in (0.0, -1.0, float("nan"), float("inf"), float("-inf"), 4200.01):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                runner.run_attempt(self.root, self.source, self.attempt, max_wall_seconds=cap)
            self.assertFalse((self.root / self.attempt).exists())

    def test_cli_forwards_short_wall_cap_and_preserves_4200_default(self) -> None:
        python = self.root / (
            ".venv/Scripts/python.exe" if runner.os.name == "nt" else ".venv/bin/python"
        )
        with ExitStack() as stack:
            stack.enter_context(patch.object(runner, "ROOT", self.root))
            stack.enter_context(patch.object(runner.sys, "executable", str(python)))
            stack.enter_context(patch.object(runner.signal, "signal"))
            run = stack.enter_context(patch.object(runner, "run_attempt", return_value=0))
            common = ["--expect-source", self.source, "--attempt-directory", str(self.attempt)]
            self.assertEqual(runner.main(common), 0)
            self.assertEqual(run.call_args.kwargs["max_wall_seconds"], 4200.0)
            self.assertEqual(runner.main([*common, "--max-wall-seconds", "123.75"]), 0)
            self.assertEqual(run.call_args.kwargs["max_wall_seconds"], 123.75)

    def test_old_global_pass_cannot_pass_an_attempt_without_fresh_status(self) -> None:
        old = quality_payload(self.root, self.source, "a" * 32)
        global_status = self.root / "runs/quality_status.json"
        runner.write_once(global_status, old)
        original = global_status.read_bytes()
        result, receipt = self.run_synthetic(emit_status=False)
        self.assertEqual(result, 1)
        self.assertIn("attempt-scoped", receipt["stop_reason"])
        self.assertEqual(global_status.read_bytes(), original)
        self.assertFalse(self.archive.exists())

    def test_requested_publication_replaces_current_with_exact_verified_bytes(self) -> None:
        current = self.root / "runs/quality_status.json"
        current.parent.mkdir()
        current.write_text('{"previous": true}\n', encoding="utf-8")
        previous_digest = runner.digest(current)
        result, receipt = self.run_synthetic(publish=True)
        self.assertEqual(result, 0)
        self.assertTrue(receipt["current_status_published"])
        self.assertEqual(receipt["previous_current_status_sha256"], previous_digest)
        self.assertEqual(receipt["current_status_sha256"], runner.digest(current))
        self.assertEqual(current.read_bytes(), self.archive.read_bytes())
        self.assertEqual(current.read_bytes(), (self.root / self.attempt / "quality_status.json")
                         .read_bytes())

    def test_failed_attempt_preserves_previous_current_pointer(self) -> None:
        current = self.root / "runs/quality_status.json"
        current.parent.mkdir()
        current.write_text('{"previous": true}\n', encoding="utf-8")
        original = current.read_bytes()
        result, receipt = self.run_synthetic(emit_status=False, publish=True)
        self.assertEqual(result, 1)
        self.assertFalse(receipt["current_status_published"])
        self.assertEqual(current.read_bytes(), original)
        self.assertFalse(self.archive.exists())

    def test_failed_finalization_quarantines_only_the_new_archive(self) -> None:
        for event in (
            "corrupt_log_after_archive", "source_drift_after_archive", "cancel_after_archive",
        ):
            with self.subTest(event=event):
                # Each event gets an independent source, attempt and history.
                self.attempt = runner.ATTEMPT_DIRECTORY / event
                self.archive = self.root / runner.ARCHIVE_DIRECTORY / f"{event}.json"
                (self.root / "core/source.py").write_text("value = 1\n")
                current = self.root / "runs/quality_status.json"
                current.parent.mkdir(exist_ok=True)
                current.write_text('{"previous": true}\n', encoding="utf-8")
                original = current.read_bytes()
                history = self.root / runner.ARCHIVE_DIRECTORY / "historical.json"
                history.parent.mkdir(parents=True, exist_ok=True)
                if not history.exists():
                    history.write_text("historical evidence\n")
                result, receipt = self.run_synthetic(publish=True, final_event=event)
                self.assertEqual(result, 1)
                self.assertFalse(self.archive.exists())
                self.assertIsNone(receipt["pass_archive"])
                quarantine = self.root / receipt["quarantined_quality_archive"]
                self.assertTrue(quarantine.is_file())
                self.assertEqual(quarantine.read_bytes(),
                                 (self.root / self.attempt / "quality_candidate.json").read_bytes())
                self.assertEqual(current.read_bytes(), original)
                self.assertEqual(history.read_text(), "historical evidence\n")
                self.assertIsNone(receipt["publication_cleanup_error"])

    def test_cancellation_after_publication_restores_previous_current_pointer(self) -> None:
        current = self.root / "runs/quality_status.json"
        current.parent.mkdir()
        current.write_text('{"previous": true}\n', encoding="utf-8")
        original = current.read_bytes()
        result, receipt = self.run_synthetic(publish=True, final_event="cancel_after_pointer")
        self.assertEqual(result, 1)
        self.assertTrue(receipt["current_status_publication_occurred"])
        self.assertTrue(receipt["current_status_restored"])
        self.assertFalse(receipt["current_status_published"])
        self.assertEqual(current.read_bytes(), original)
        self.assertFalse(self.archive.exists())

    def test_cancellation_removes_only_own_new_pointer_when_prior_absent(self) -> None:
        current = self.root / "runs/quality_status.json"
        result, receipt = self.run_synthetic(publish=True, final_event="cancel_after_pointer")
        self.assertEqual(result, 1)
        self.assertTrue(receipt["current_status_restored"])
        self.assertFalse(current.exists())
        self.assertFalse(self.archive.exists())

    def test_late_failure_never_reverts_a_different_writers_current_pointer(self) -> None:
        current = self.root / "runs/quality_status.json"
        current.parent.mkdir()
        current.write_text('{"previous": true}\n', encoding="utf-8")
        result, receipt = self.run_synthetic(publish=True, final_event="other_writer_after_pointer")
        self.assertEqual(result, 1)
        self.assertTrue(receipt["current_status_rollback_skipped"])
        self.assertFalse(receipt["current_status_restored"])
        self.assertEqual(json.loads(current.read_text("utf-8")), {"other_writer": True})
        self.assertFalse(self.archive.exists())

    def test_foreign_attempt_status_and_corrupted_logs_never_archive(self) -> None:
        result, receipt = self.run_synthetic(foreign_status=True)
        self.assertEqual(result, 1)
        self.assertIsNone(receipt["quality_status_copy"])
        self.assertFalse(self.archive.exists())

    def test_changed_quality_log_fails_bundle_verification(self) -> None:
        result, receipt = self.run_synthetic(corrupt_logs=True)
        self.assertEqual(result, 1)
        self.assertEqual(receipt["stop_reason"], "quality bundle verification failed")
        self.assertFalse(self.archive.exists())

    def test_status_replaced_between_verification_and_archive_is_rejected(self) -> None:
        result, receipt = self.run_synthetic(mutate_status_before_archive=True)
        self.assertEqual(result, 1)
        self.assertIn("changed before archive", receipt["error"])
        self.assertFalse(self.archive.exists())

    def test_source_drift_stops_owned_work_and_never_archives(self) -> None:
        different = "b" * 64
        result, receipt = self.run_synthetic(
            finished=False,
            fingerprints=[self.source, self.source, different, different, different],
        )
        self.assertEqual(result, 1)
        self.assertIn("source drift", receipt["stop_reason"])
        self.assertTrue(FakeTree.instances[0].stopped)
        self.assertFalse(self.archive.exists())

    def test_RAM_deadline_and_cancellation_stop_only_owned_work(self) -> None:
        for scenario in ("ram", "disk", "deadline", "cancellation"):
            with self.subTest(scenario=scenario):
                self.attempt = runner.ATTEMPT_DIRECTORY / scenario
                if scenario in ("ram", "disk"):
                    kwargs: dict[str, Any] = {
                        "resource_points": [resources(), resources(),
                                            resources(3.9) if scenario == "ram"
                                            else resources(disk=7.9), resources()],
                    }
                else:
                    kwargs = {"deadline" if scenario == "deadline" else "interrupt": True}
                result, receipt = self.run_synthetic(finished=False, **kwargs)
                self.assertEqual(result, 1)
                self.assertTrue(FakeTree.instances[-1].stopped)
                self.assertIsNone(receipt["pass_archive"])
                self.assertFalse(receipt["quality_bundle_verified"])

    def test_both_startup_samples_must_pass(self) -> None:
        result, receipt = self.run_synthetic(
            resource_points=[resources(), resources(5.9), resources()],
        )
        self.assertEqual(result, 1)
        self.assertEqual(receipt["stop_reason"], "quality-only startup RAM floor")
        self.assertEqual(FakeTree.instances, [])

    def test_final_resource_floor_cannot_be_bypassed_by_clean_child_exit(self) -> None:
        result, receipt = self.run_synthetic(
            resource_points=[resources(), resources(), resources(), resources(3.9)],
        )
        self.assertEqual(result, 1)
        self.assertEqual(receipt["stop_reason"], "quality-only active RAM floor")
        self.assertFalse(self.archive.exists())

    def test_duplicate_attempt_refuses_and_preserves_original_receipt(self) -> None:
        self.run_synthetic()
        path = self.root / self.attempt / "receipt.json"
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            runner.run_attempt(self.root, self.source, self.attempt)
        self.assertEqual(path.read_bytes(), original)

    def test_paths_and_weakened_startup_guard_are_rejected(self) -> None:
        for path in (Path("outside"), runner.ATTEMPT_DIRECTORY / "nested/attempt"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                runner.run_attempt(self.root, self.source, path)
        for ram in (5.9, float("nan"), float("inf")):
            with self.subTest(ram=ram), self.assertRaises(ValueError):
                runner.run_attempt(self.root, self.source, self.attempt, startup_ram_gib=ram)

    def test_owned_descendant_is_stopped_after_launcher_exits_and_peer_survives(self) -> None:
        # Two tiny stdlib processes establish that process cleanup does not use
        # global Python-name matching. No other project's processes are touched.
        peer = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        child: subprocess.Popen[bytes] | None = None
        tree: runner.OwnedProcessTree | None = None
        try:
            script = (
                "import subprocess,sys,time; "
                "subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                "time.sleep(1)"
            )
            child = subprocess.Popen([sys.executable, "-c", script])
            tree = runner.OwnedProcessTree(child)
            deadline = time.monotonic() + 10
            while len(tree.living()) < 2 and time.monotonic() < deadline:
                time.sleep(0.02)
            descendants = [process for process in tree.living() if process.pid != child.pid]
            self.assertTrue(descendants)
            child.wait(timeout=10)
            tree.stop()
            self.assertEqual(tree.living(), [])
            self.assertIsNone(peer.poll())
            for process in descendants:
                self.assertFalse(process.is_running() and process.status() != psutil.STATUS_ZOMBIE)
        finally:
            if tree is not None:
                tree.stop()
            elif child is not None:
                child.terminate()
                child.wait(timeout=10)
            peer.terminate()
            peer.wait(timeout=10)

    def test_quality_verifier_default_status_and_scoped_write_once_are_compatible(self) -> None:
        from core.provenance import SourceProvenance

        def launch(command: list[str], **kwargs: Any) -> FakeChild:
            kwargs["stdout"].write("synthetic passed\n")
            return FakeChild()

        scoped = self.root / "runs/scoped/quality_status.json"
        with ExitStack() as stack:
            stack.enter_context(patch.object(
                quality, "__file__", str(self.root / "scripts/verify.py"),
            ))
            stack.enter_context(patch.object(
                quality, "capture_source",
                return_value=SourceProvenance("synthetic", self.source, True),
            ))
            stack.enter_context(patch.object(quality.subprocess, "Popen", side_effect=launch))
            stack.enter_context(patch.object(quality, "OwnedProcessTree", FakeTree))
            stack.enter_context(redirect_stdout(StringIO()))
            self.assertEqual(quality.main([]), 0)
            current = self.root / "runs/quality_status.json"
            original = current.read_bytes()
            arguments = ["--status-output", str(scoped), "--attempt-id", "1" * 32]
            self.assertEqual(quality.main(arguments), 0)
            self.assertEqual(current.read_bytes(), original)
            self.assertEqual(json.loads(scoped.read_text("utf-8"))["attempt_id"], "1" * 32)
            with self.assertRaises(SystemExit), redirect_stderr(StringIO()):
                quality.main(arguments)

    def test_standalone_verifier_rejects_parent_exit_zero_with_live_owned_descendant(self) -> None:
        from core.provenance import SourceProvenance

        pid_path = self.root / "runs/descendant.pid"
        pid_path.parent.mkdir()
        program = (
            "import subprocess,sys,time; "
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
            f"open({str(pid_path)!r},'w').write(str(child.pid)); "
            "time.sleep(0.5)"
        )
        try:
            with ExitStack() as stack:
                stack.enter_context(patch.object(
                    quality, "__file__", str(self.root / "scripts/verify.py"),
                ))
                stack.enter_context(patch.object(
                    quality, "capture_source",
                    return_value=SourceProvenance("synthetic", self.source, True),
                ))
                stack.enter_context(patch.object(
                    quality, "QUALITY_COMMANDS", {"orphan_command": ("-c", program)},
                ))
                stack.enter_context(redirect_stdout(StringIO()))
                self.assertEqual(quality.main([]), 1)
            report = json.loads((self.root / "runs/quality_status.json").read_text("utf-8"))
            self.assertFalse(report["passed"])
            self.assertEqual(report["checks"]["orphan_command"]["exit_code"], -1)
            pid = int(pid_path.read_text())
            self.assertFalse(psutil.pid_exists(pid))
        finally:
            # This PID was emitted by our newly launched synthetic command;
            # leave no test descendant alive even if the regression fails.
            if pid_path.exists():
                pid = int(pid_path.read_text())
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
