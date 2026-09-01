from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.finish_phase1_compute import (
    await_resources,
    exclusive_supervisor,
    next_batch,
    require_extension,
    require_integrity,
    run_grids,
    run_logged,
)


class CompletionSupervisorTests(unittest.TestCase):
    def test_preservation_and_bounded_progress_are_required(self):
        require_extension({"old": "a"}, {"old": "a", "new": "b"}, maximum=20)
        require_extension({"old": "a"}, {"old": "a"}, maximum=20, require_progress=False)
        for current, maximum in (
            ({"old": "changed"}, 20),
            ({}, 20),
            ({"old": "a"}, 20),
            ({"old": "a", "new": "b"}, 0),
        ):
            with self.subTest(current=current), self.assertRaises(ValueError):
                require_extension({"old": "a"}, current, maximum=maximum)

    def test_invalid_records_or_reference_locks_prevent_work(self):
        require_integrity({"invalid_records": {}, "unexpected_records": []})
        with self.assertRaises(ValueError):
            require_integrity({"invalid_records": {"bad": "reason"}, "unexpected_records": []})
        for key in ("invalid_units", "unexpected_files", "pending_locks"):
            report = {"invalid_units": {}, "unexpected_files": [], "pending_locks": []}
            report[key] = ["review"]
            with self.subTest(key=key), self.assertRaises(ValueError):
                require_integrity(report, reference=True)

    def test_scheduling_uses_configured_order_not_filename_order(self):
        config = {"benchmark": {"datasets": ["first", "second"], "methods": ["z", "a"]}}
        report = {
            "missing_records": [
                "second/z/seed_11/s.json",
                "first/a/seed_11/s.json",
                "first/z/seed_11/s.json",
            ]
        }
        self.assertEqual(next_batch(report, config), ("first", "z"))
        self.assertIsNone(next_batch({"missing_records": []}, config))
        with self.assertRaises(ValueError):
            next_batch({"missing_records": ["unknown/z/seed_11/s.json"]}, config)

    def test_resource_deferral_does_not_launch_a_worker(self):
        with (
            patch("scripts.finish_phase1_compute.resources", return_value={"ready": False}),
            patch("scripts.finish_phase1_compute.subprocess.run") as child,
            redirect_stdout(StringIO()),
        ):
            self.assertFalse(await_resources(Path("unused"), {}, timeout=0))
            child.assert_not_called()

    def test_resource_recovery_rechecks_instead_of_lowering_limits(self):
        with (
            patch(
                "scripts.finish_phase1_compute.resources",
                side_effect=[{"ready": False}, {"ready": True}],
            ) as observer,
            patch("scripts.finish_phase1_compute.time.sleep") as sleeper,
            redirect_stdout(StringIO()),
        ):
            self.assertTrue(await_resources(Path("unused"), {"unchanged": 10}))
            self.assertEqual(observer.call_count, 2)
            self.assertEqual(observer.call_args.args[1], {"unchanged": 10})
            sleeper.assert_called_once()

    def test_exclusive_lock_is_owned_and_stale_lock_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock = root / "runs/phase1_compute.lock"
            with exclusive_supervisor(root):
                self.assertIn("pid", json.loads(lock.read_text()))
                before = lock.read_bytes()
                with self.assertRaises(FileExistsError), exclusive_supervisor(root):
                    self.fail("duplicate supervisor entered")
                self.assertEqual(lock.read_bytes(), before)
            self.assertFalse(lock.exists())
            lock.write_text("stale", encoding="utf-8")
            with self.assertRaises(FileExistsError), exclusive_supervisor(root):
                self.fail("stale lock was ignored")
            self.assertEqual(lock.read_text(), "stale")

    def test_child_failure_is_logged_and_not_retried(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("scripts.finish_phase1_compute.subprocess.run") as child,
            redirect_stdout(StringIO()),
        ):
            child.return_value.returncode = 1073741845
            self.assertEqual(run_logged(Path(directory), ["python", "worker"], "test"), 1073741845)
            child.assert_called_once()
            self.assertEqual(len(list((Path(directory) / "runs/compute_logs").glob("*.log"))), 2)

    def exercise_grid(
        self,
        *,
        code=0,
        ready=True,
        already_complete=False,
        changed=False,
        progress=True,
        invalid=False,
        startup_memory=None,
    ):
        main_before = {
            "complete": already_complete,
            "valid_records": 1,
            "invalid_records": {},
            "unexpected_records": [],
            "missing_records": [] if already_complete else ["d/m/seed_11/s.json"],
            "record_files": {"old": "a"},
        }
        main_after = {
            **main_before,
            "complete": True,
            "valid_records": 2,
            "missing_records": [],
            "record_files": {"old": "a", "new": "b"},
        }
        ref_before = {
            "complete": already_complete,
            "valid_fits": 0,
            "record_files": {},
            "missing_units": [] if already_complete else ["unit"],
            "invalid_units": {"bad": "reason"} if invalid else {},
            "unexpected_files": [],
            "pending_locks": [],
        }
        ref_after = {
            **ref_before,
            "complete": True,
            "valid_fits": 1,
            "record_files": {"unit.json": "c"},
            "missing_units": [],
        }
        config = {"benchmark": {"datasets": ["d"], "methods": ["m"]}}
        source = SimpleNamespace(git_dirty=False, source_sha256="same")
        sources = [source] * 5
        if changed:
            sources[2] = SimpleNamespace(git_dirty=False, source_sha256="changed")
        with ExitStack() as stack:
            stack.enter_context(redirect_stdout(StringIO()))
            stack.enter_context(patch("scripts.finish_phase1_compute.atomic_json"))
            for name, options in {
                "capture_source": {"side_effect": sources},
                "load_toml": {"return_value": config},
                "resolve_config": {
                    "return_value": (
                        {},
                        SimpleNamespace(units=[SimpleNamespace(key="unit")]),
                        {
                            "environment": {"directory": "reference"},
                            "runtime": {
                                "minimum_free_memory_gib": 10.0,
                                "stop_below_free_memory_gib": 4.0,
                                "minimum_free_disk_gib": 10.0,
                            },
                        },
                        Path("output"),
                    )
                },
                "inspect_benchmark": {
                    "side_effect": [
                        main_before,
                        main_after if code == 0 and progress else main_before,
                    ]
                },
                "audit": {"side_effect": [ref_before, ref_after]},
                "await_resources": {"return_value": ready},
            }.items():
                stack.enter_context(patch("scripts.finish_phase1_compute." + name, **options))
            child = stack.enter_context(
                patch("scripts.finish_phase1_compute.run_logged", return_value=code)
            )
            if changed or not progress or invalid:
                with self.assertRaises((ValueError, RuntimeError)):
                    run_grids(
                        Path("fixture"),
                        reference_startup_minimum_free_memory_gib=startup_memory,
                    )
                return None, child.call_args_list
            return (
                run_grids(
                    Path("fixture"),
                    reference_startup_minimum_free_memory_gib=startup_memory,
                ),
                child.call_args_list,
            )

    def test_both_grids_run_sequentially_with_original_arguments(self):
        code, calls = self.exercise_grid()
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 2)
        first = calls[0].args[1]
        self.assertEqual(
            first[2:],
            ["scripts/run_benchmark.py", "--dataset", "d", "--method", "m", "--max-new-runs", "20"],
        )
        second = calls[1].args[1]
        self.assertEqual(second[1:4], ["-u", "-m", "scripts.run_moabb_reference"])
        self.assertEqual(second[-2:], ["--unit-index", "0"])

    def test_lower_memory_mode_is_forwarded_only_to_reference_child(self):
        code, calls = self.exercise_grid(startup_memory=8.0)
        self.assertEqual(code, 0)
        self.assertNotIn("--startup-minimum-free-memory-gib", calls[0].args[1])
        self.assertEqual(
            calls[1].args[1][-4:],
            ["--unit-index", "0", "--startup-minimum-free-memory-gib", "8.0"],
        )

    def test_grid_failure_stops_before_other_worker_without_retry(self):
        code, calls = self.exercise_grid(code=1073741845)
        self.assertEqual(code, 1073741845)
        self.assertEqual(len(calls), 1)

    def test_completed_grids_and_low_resources_do_not_start_workers(self):
        self.assertEqual(self.exercise_grid(already_complete=True), (0, []))
        self.assertEqual(self.exercise_grid(ready=False), (2, []))

    def test_changed_source_zero_progress_or_invalid_reference_fail_closed(self):
        for argument in ({"changed": True}, {"progress": False}, {"invalid": True}):
            with self.subTest(argument=argument):
                _, calls = self.exercise_grid(**argument)
                self.assertEqual(len(calls), 0 if argument.get("invalid") else 1)


if __name__ == "__main__":
    unittest.main()
