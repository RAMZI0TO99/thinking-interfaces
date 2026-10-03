from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from core.config import canonical_config_json
from evaluation.phase2_records import CellIdentity, envelope, verify_envelope
from evaluation.phase2_runner import (
    CasePlan,
    CaseRecorder,
    environment_digest,
    method_configuration,
    pilot_case_plans,
)

COMMIT = "e378dfd5f65e53b7ae7da62c778e829b60c61b98"


def identity(**overrides) -> CellIdentity:
    base = dict(
        dataset="bci_iv_2a",
        target_subject="subject_01",
        method="labram_lora",
        shots_per_class=1,
        model_seed=23,
        support_draw_seed=None,
        montage_seed=None,
        protocol_sha256="a" * 64,
        episode_sha256="b" * 64,
        selection_sha256="c" * 64,
        method_config_sha256="d" * 64,
        preprocessing_sha256="e" * 64,
        checkpoint_sha256="f" * 64,
        source_sha256="1" * 64,
        environment_sha256="2" * 64,
        git_commit=COMMIT,
        git_dirty=True,
    )
    base.update(overrides)
    return CellIdentity(**base)


def metrics(**overrides) -> dict:
    confusion = [[49, 3], [2, 44]]
    rational = (Fraction(49, 52) + Fraction(44, 46)) / 2
    base = dict(
        role="outer_target",
        selection_evidence_sha256="9" * 64,
        confusion_matrix=confusion,
        balanced_accuracy=[rational.numerator, rational.denominator],
        query_count=98,
        support_losses=[1.5, 1.25],
    )
    base.update(overrides)
    return base


class Phase2RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd() / "tmp")
        self.root = Path(self.temp.name)
        self.output = self.root / "runs" / "phase2" / "recorder"
        self.recorder = CaseRecorder(self.root, output_root=self.output)
        self.plans = pilot_case_plans(
            methods=("labram_lora", "eegnet"),
            datasets=("bci_iv_2a",),
            targets={"bci_iv_2a": "subject_01"},
            shots=(1, 20),
            model_seed=23,
            repetitions=2,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_environment_and_method_configuration_digests(self):
        first = environment_digest()
        self.assertEqual(first, environment_digest())
        self.assertEqual(len(first), 64)
        complete = {
            "optimizer": "sgd",
            "steps": 1,
            "fit_scope": "lora",
            "preprocessing": "profile_b_800_200",
        }
        self.assertEqual(method_configuration(complete), method_configuration(complete))
        self.assertNotEqual(
            method_configuration(complete),
            method_configuration({**complete, "steps": 2}),
        )
        for bad in (
            {**complete, "optimizer": None},
            {"steps": 1, "fit_scope": "x", "preprocessing": "y"},
            {},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                method_configuration(bad)

    def test_case_plan_ordering_ids_and_validation(self):
        self.assertEqual(len(self.plans), 8)
        self.assertEqual(
            [(p.method, p.shots_per_class, p.repetition) for p in self.plans],
            [("labram_lora", 1, 1), ("labram_lora", 1, 2), ("labram_lora", 20, 1),
             ("labram_lora", 20, 2), ("eegnet", 1, 1), ("eegnet", 1, 2),
             ("eegnet", 20, 1), ("eegnet", 20, 2)],
        )
        self.assertEqual(len({p.case_id for p in self.plans}), 8)
        self.assertEqual(len({p.identity_key for p in self.plans}), 4)
        again = pilot_case_plans(
            methods=("labram_lora", "eegnet"),
            datasets=("bci_iv_2a",),
            targets={"bci_iv_2a": "subject_01"},
            shots=(20, 1),
            model_seed=23,
            repetitions=2,
        )
        self.assertEqual(self.plans, again)
        for kwargs in (
            {"methods": ()},
            {"methods": ("a", "a"), "datasets": ("d",), "targets": {"d": "s"}, "shots": (1,)},
            {"datasets": ("d", "d"), "methods": ("a",), "targets": {"d": "s"}, "shots": (1,)},
            {"targets": {}, "methods": ("a",), "datasets": ("d",), "shots": (1,)},
            {"shots": (1, 1), "methods": ("a",), "datasets": ("d",), "targets": {"d": "s"}},
            {"shots": (0,), "methods": ("a",), "datasets": ("d",), "targets": {"d": "s"}},
            {"repetitions": 0, "methods": ("a",), "datasets": ("d",), "targets": {"d": "s"},
             "shots": (1,)},
        ):
            arguments = dict(
                methods=("a",), datasets=("d",), targets={"d": "s"}, shots=(1,),
                model_seed=23, repetitions=1,
            )
            arguments.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                pilot_case_plans(**arguments)
        with self.assertRaises(ValueError):
            CasePlan("d", "s", "m", 0, 0, 1)
        with self.assertRaises(ValueError):
            CasePlan("d", "s", "m", 1, -1, 1)
        with self.assertRaises(ValueError):
            CasePlan("d", "s", "m", 1, 23, 0)

    def test_claim_lifecycle_is_atomic_with_one_linked_retry(self):
        plan = self.plans[0]
        first = self.recorder.claim(plan, worker="worker-a")
        self.assertTrue(first.is_file())
        self.recorder.claim(plan, worker="worker-a")  # Same bytes resume is a no-op.
        with self.assertRaises(FileExistsError):
            self.recorder.claim(plan, worker="worker-b")
        with self.assertRaisesRegex(ValueError, "linked to a recorded failure"):
            self.recorder.claim(plan, worker="worker-a", attempt=2)
        with self.assertRaises(ValueError):
            self.recorder.claim(plan, worker="worker-a", attempt=3)
        with self.assertRaises(ValueError):
            self.recorder.claim(plan, worker="worker-a", attempt=0)
        self.recorder.record_failure(plan, attempt=1, reason={"error": "guard stopped work"})
        second = self.recorder.claim(plan, worker="worker-a", attempt=2)
        self.assertTrue(second.is_file())
        self.recorder.record_failure(plan, attempt=2, reason={"error": "cap reached"})
        with self.assertRaises(ValueError):
            self.recorder.claim(plan, worker="worker-a", attempt=3)
        completion = self.recorder.completion(self.plans)
        entry = next(row for row in completion["cases"] if row["case_id"] == plan.case_id)
        self.assertEqual(len(entry["claims"]), 2)
        self.assertEqual(len(entry["failures"]), 2)

    def test_failure_records_require_an_error_description(self):
        plan = self.plans[1]
        for bad in ({}, {"error": ""}, {"error": 5}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.recorder.record_failure(plan, attempt=1, reason=bad)
        with self.assertRaisesRegex(ValueError, "recorded claim"):
            self.recorder.record_failure(plan, attempt=1, reason={"error": "timeout"})
        self.recorder.claim(plan, worker="w")
        path = self.recorder.record_failure(plan, attempt=1, reason={"error": "timeout"})
        record = json.loads(path.read_text("utf-8"))
        self.assertEqual(record["payload"]["purpose"], "pilot_case_failure")
        self.recorder.record_failure(plan, attempt=1, reason={"error": "timeout"})
        with self.assertRaises(FileExistsError):
            self.recorder.record_failure(plan, attempt=1, reason={"error": "different"})

    def test_success_and_failure_are_exclusive_terminal_states(self):
        successful = self.plans[0]
        failed = self.plans[2]
        self.recorder.claim(successful, worker="w")
        self.recorder.record_cell(
            identity(method=successful.method, shots_per_class=successful.shots_per_class),
            metrics=metrics(),
            plan=successful,
        )
        with self.assertRaisesRegex(ValueError, "cannot also record a failure"):
            self.recorder.record_failure(
                successful, attempt=1, reason={"error": "late failure"}
            )
        with self.assertRaisesRegex(ValueError, "completed case"):
            self.recorder.claim(successful, worker="w", attempt=2)
        self.assertFalse((self.output / "attempts").exists())

        self.recorder.claim(failed, worker="w")
        self.recorder.record_failure(failed, attempt=1, reason={"error": "guard"})
        with self.assertRaisesRegex(ValueError, "failed attempt"):
            self.recorder.record_cell(
                identity(method=failed.method, shots_per_class=failed.shots_per_class),
                metrics=metrics(),
                plan=failed,
            )
        self.assertFalse(
            (self.output / "successes" / f"{failed.case_id}.success.json").exists()
        )

    def test_orphan_cell_refuses_failure_before_success_recovery(self):
        plan = self.plans[0]
        self.recorder.claim(plan, worker="w")
        original_write = self.recorder._write

        def interrupt_after_cell(directory, name, record):
            if directory == self.recorder._successes:
                raise RuntimeError("simulated interruption before success receipt")
            return original_write(directory, name, record)

        with (
            patch.object(self.recorder, "_write", side_effect=interrupt_after_cell),
            self.assertRaisesRegex(RuntimeError, "simulated interruption"),
        ):
            self.recorder.record_cell(identity(), metrics=metrics(), plan=plan)
        self.assertTrue((self.output / "cells" / f"{identity().sha256}.json").is_file())
        self.assertFalse((self.output / "successes" / f"{plan.case_id}.success.json").exists())
        intent_path = self.output / "publication_intents" / f"{plan.case_id}.intent.json"
        self.assertTrue(intent_path.is_file())
        cell_sha256 = json.loads(intent_path.read_text("utf-8"))["payload"]["cell"]["sha256"]
        with self.assertRaisesRegex(ValueError, "published cell"):
            self.recorder.record_failure(
                plan, attempt=1, reason={"error": "late worker failure"},
            )
        self.recorder.recover_cell_from_intent(plan, expected_cell_sha256=cell_sha256)
        self.assertTrue((self.output / "successes" / f"{plan.case_id}.success.json").is_file())

    def test_intent_recovers_exact_cell_without_recomputing_runtime_metrics(self):
        plan = self.plans[0]
        self.recorder.claim(plan, worker="w")
        original_write = self.recorder._write

        def interrupt_before_cell(directory, name, record):
            if directory == self.recorder._cells:
                raise RuntimeError("simulated interruption before cell")
            return original_write(directory, name, record)

        first_metrics = metrics(stage_timings_s=[1.234567])
        with (
            patch.object(self.recorder, "_write", side_effect=interrupt_before_cell),
            self.assertRaisesRegex(RuntimeError, "simulated interruption"),
        ):
            self.recorder.record_cell(identity(), metrics=first_metrics, plan=plan)
        self.assertFalse((self.output / "cells" / f"{identity().sha256}.json").exists())
        with self.assertRaisesRegex(ValueError, "publication intent"):
            self.recorder.record_failure(plan, attempt=1, reason={"error": "late timeout"})
        with self.assertRaisesRegex(ValueError, "publication intent"):
            self.recorder.claim(plan, worker="w", attempt=2)
        with self.assertRaises(FileExistsError):
            self.recorder.record_cell(
                identity(), metrics=metrics(stage_timings_s=[1.234568]), plan=plan,
            )
        intent = self.output / "publication_intents" / f"{plan.case_id}.intent.json"
        cell_sha256 = json.loads(intent.read_text("utf-8"))["payload"]["cell"]["sha256"]
        cell = self.recorder.recover_cell_from_intent(
            plan, expected_cell_sha256=cell_sha256,
        )
        self.assertEqual(json.loads(cell.read_text("utf-8"))["payload"]["metrics"], first_metrics)
        self.recorder.recover_cell_from_intent(plan, expected_cell_sha256=cell_sha256)
        self.assertEqual(self.recorder.completion((plan,))["measured"], 1)

    def test_tampered_publication_intent_refuses_recovery(self):
        plan = self.plans[0]
        self.recorder.claim(plan, worker="w")
        self.recorder.record_cell(identity(), metrics=metrics(), plan=plan)
        intent = self.output / "publication_intents" / f"{plan.case_id}.intent.json"
        cell_sha256 = json.loads(intent.read_text("utf-8"))["payload"]["cell"]["sha256"]
        intent.write_text(intent.read_text("utf-8").replace("outer_target", "inner_target"),
                          encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "intent no longer verifies"):
            self.recorder.recover_cell_from_intent(
                plan, expected_cell_sha256=cell_sha256,
            )
        with self.assertRaisesRegex(ValueError, "intent no longer verifies"):
            self.recorder.completion((plan,))

    def test_recomputed_intent_cannot_override_attested_cell_digest(self):
        plan = self.plans[0]
        self.recorder.claim(plan, worker="w")
        original_write = self.recorder._write

        def interrupt_before_cell(directory, name, record):
            if directory == self.recorder._cells:
                raise RuntimeError("simulated interruption before cell")
            return original_write(directory, name, record)

        with (
            patch.object(self.recorder, "_write", side_effect=interrupt_before_cell),
            self.assertRaisesRegex(RuntimeError, "simulated interruption"),
        ):
            self.recorder.record_cell(identity(), metrics=metrics(), plan=plan)
        path = self.output / "publication_intents" / f"{plan.case_id}.intent.json"
        original = json.loads(path.read_text("utf-8"))
        attested_sha256 = original["payload"]["cell"]["sha256"]
        changed_cell = envelope("evaluation_cell", {
            "identity": original["payload"]["identity"],
            "metrics": metrics(stage_timings_s=[1.234568]),
        })
        changed_intent = envelope("engineering_smoke", {
            **original["payload"], "cell": changed_cell,
        })
        path.write_bytes((canonical_config_json(changed_intent) + "\n").encode("utf-8"))
        with self.assertRaisesRegex(ValueError, "intent cell no longer verifies"):
            self.recorder.recover_cell_from_intent(
                plan, expected_cell_sha256=attested_sha256,
            )

    def test_later_repetition_can_fail_after_earlier_repetition_succeeds(self):
        first, second = self.plans[:2]
        self.assertEqual(first.identity_key, second.identity_key)
        self.recorder.claim(first, worker="w")
        self.recorder.record_cell(identity(), metrics=metrics(), plan=first)
        self.recorder.claim(second, worker="w")
        failure = self.recorder.record_failure(
            second, attempt=1, reason={"error": "second repetition timed out"},
        )
        self.assertTrue(failure.is_file())
        completion = self.recorder.completion((first, second))
        self.assertEqual(completion["measured"], 1)
        self.assertEqual(completion["failed"], 1)

    def test_unreceipted_other_repetition_cell_blocks_failure(self):
        first, second = self.plans[:2]
        self.recorder.claim(first, worker="w")
        original_write = self.recorder._write

        def interrupt_before_success(directory, name, record):
            if directory == self.recorder._successes:
                raise RuntimeError("simulated interruption before success")
            return original_write(directory, name, record)

        with (
            patch.object(self.recorder, "_write", side_effect=interrupt_before_success),
            self.assertRaisesRegex(RuntimeError, "simulated interruption"),
        ):
            self.recorder.record_cell(identity(), metrics=metrics(), plan=first)
        self.recorder.claim(second, worker="w")
        with self.assertRaisesRegex(ValueError, "published cell"):
            self.recorder.record_failure(
                second, attempt=1, reason={"error": "second repetition timed out"},
            )

    def test_retry_and_completion_reject_invalid_failure_evidence(self):
        plan = self.plans[0]
        self.recorder.claim(plan, worker="w")
        failure = self.recorder.record_failure(
            plan, attempt=1, reason={"error": "guard"}
        )
        original = failure.read_text("utf-8")
        failure.write_text(original.replace("guard", "other"), "utf-8")
        with self.assertRaisesRegex(ValueError, "failure no longer verifies"):
            self.recorder.claim(plan, worker="w", attempt=2)
        with self.assertRaisesRegex(ValueError, "failure no longer verifies"):
            self.recorder.completion((plan,))
        self.assertFalse(
            (self.output / "claims" / f"{plan.case_id}.attempt2.claim.json").exists()
        )

    def test_completion_rejects_failure_without_matching_claim(self):
        plan = self.plans[0]
        claim = self.recorder.claim(plan, worker="w")
        self.recorder.record_failure(plan, attempt=1, reason={"error": "guard"})
        claim.unlink()
        with self.assertRaisesRegex(ValueError, "failure no longer verifies"):
            self.recorder.completion((plan,))

    def test_cell_publication_and_metrics_invariants(self):
        cell_identity = identity()
        path = self.recorder.record_cell(cell_identity, metrics=metrics())
        self.assertEqual(path.name, f"{cell_identity.sha256}.json")
        record = json.loads(path.read_text("utf-8"))
        self.assertTrue(
            verify_envelope(
                record,
                kind="evaluation_cell",
                expected_payload={"identity": record["payload"]["identity"],
                                  "metrics": record["payload"]["metrics"]},
            )
        )
        self.recorder.record_cell(cell_identity, metrics=metrics())  # Byte-identical no-op.
        with self.assertRaises(FileExistsError):
            self.recorder.record_cell(
                cell_identity, metrics=metrics(support_losses=[1.0, 1.0])
            )
        bad_confusions = (
            [[10, 0], [0, 10], [0, 1]],
            [[10, 0], [0]],
            [[10, -1], [0, 10]],
            [[10, 0], [0, 0]],
            "matrix",
        )
        for confusion in bad_confusions:
            with self.subTest(confusion=confusion), self.assertRaises(ValueError):
                self.recorder.record_cell(
                    identity(), metrics=metrics(confusion_matrix=confusion)
                )
        for kwargs in (
            {"balanced_accuracy": [1, 2]},
            {"balanced_accuracy": [7, 8]},
            {"query_count": 97},
            {"query_count": True},
            {"role": "inner_validation"},
            {"selection_evidence_sha256": "short"},
            {"support_losses": [1.0, float("nan")]},
            {"stage_timings_s": "fast"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.recorder.record_cell(identity(), metrics=metrics(**kwargs))

    def test_measured_index_reverifies_published_bytes(self):
        plan = self.plans[0]
        self.recorder.record_cell(
            identity(method=plan.method, shots_per_class=plan.shots_per_class),
            metrics=metrics(),
        )
        index = self.recorder.measured_identities()
        self.assertIn(plan.identity_key, index)
        completion = self.recorder.completion(self.plans)
        self.assertEqual(completion["measured"], 0)
        self.recorder.claim(plan, worker="w")
        self.recorder.record_cell(
            identity(method=plan.method, shots_per_class=plan.shots_per_class),
            metrics=metrics(),
            plan=plan,
        )
        completion = self.recorder.completion(self.plans)
        self.assertEqual(completion["measured"], 1)
        self.assertTrue(completion["cases"][0]["measured"])
        self.assertFalse(completion["cases"][1]["measured"])
        cell = next(self.output.glob("cells/*.json"))
        cell.write_text(cell.read_text("utf-8").replace("49,3", "48,4"))
        with self.assertRaisesRegex(ValueError, "no longer verifies"):
            self.recorder.measured_identities()

    def test_case_success_receipt_requires_matching_claim_and_verified_cell(self):
        first, second = self.plans[:2]
        cell_identity = identity(
            method=first.method, shots_per_class=first.shots_per_class
        )
        with self.assertRaisesRegex(ValueError, "must match"):
            self.recorder.record_cell(
                cell_identity, metrics=metrics(), plan=self.plans[2]
            )
        with self.assertRaisesRegex(ValueError, "recorded claim"):
            self.recorder.record_cell(cell_identity, metrics=metrics(), plan=first)
        self.assertFalse((self.output / "cells").exists())
        self.recorder.claim(first, worker="w")
        self.recorder.record_cell(cell_identity, metrics=metrics(), plan=first)
        receipt = self.output / "successes" / f"{first.case_id}.success.json"
        self.assertTrue(receipt.is_file())
        self.recorder.record_cell(cell_identity, metrics=metrics(), plan=first)
        completion = self.recorder.completion((first, second))
        self.assertEqual(completion["measured"], 1)
        self.assertEqual(completion["pending"], 1)
        self.recorder.claim(second, worker="w")
        completion = self.recorder.completion((first, second))
        self.assertEqual(completion["measured"], 1)
        self.assertEqual(completion["claimed_unmeasured"], 1)
        with self.assertRaisesRegex(FileExistsError, "different cell"):
            self.recorder.record_cell(
                identity(
                    method=second.method,
                    shots_per_class=second.shots_per_class,
                    checkpoint_sha256="3" * 64,
                ),
                metrics=metrics(),
                plan=second,
            )
        self.assertEqual(len(tuple((self.output / "cells").glob("*.json"))), 1)
        original = receipt.read_text("utf-8")
        receipt.write_text(original.replace("pilot_case_success", "pilot_case_failure"), "utf-8")
        with self.assertRaisesRegex(ValueError, "success no longer verifies"):
            self.recorder.completion((first, second))

    def test_completion_accounting_across_states(self):
        measured_plans, claimed_plans, failed_plans, _pending = (
            self.plans[0:2],
            self.plans[2:4],
            self.plans[4:6],
            self.plans[6:8],
        )
        for plan in measured_plans:
            self.recorder.claim(plan, worker="w")
            self.recorder.record_cell(
                identity(
                    method=plan.method, shots_per_class=plan.shots_per_class
                ),
                metrics=metrics(),
                plan=plan,
            )
        for plan in claimed_plans:
            self.recorder.claim(plan, worker="w")
        for plan in failed_plans:
            self.recorder.claim(plan, worker="w")
            self.recorder.record_failure(plan, attempt=1, reason={"error": "guard"})
        completion = self.recorder.completion(self.plans)
        self.assertEqual(completion["planned"], 8)
        self.assertEqual(completion["measured"], 2)
        self.assertEqual(completion["claimed_unmeasured"], 2)
        self.assertEqual(completion["failed"], 2)
        self.assertEqual(completion["pending"], 2)

    def test_case_session_spans_external_work_and_rejects_misuse(self):
        plan = self.plans[0]
        started = self.root / "lock-started.txt"
        entered = self.root / "lock-entered.txt"
        child_code = "\n".join((
            "import json, sys",
            "from pathlib import Path",
            "from evaluation.phase2_runner import CasePlan, CaseRecorder",
            "root, output, plan_json, started, entered = sys.argv[1:]",
            "Path(started).write_text('ready')",
            "recorder = CaseRecorder(Path(root), output_root=Path(output))",
            "plan = CasePlan(**json.loads(plan_json))",
            "with recorder.case_session(plan):",
            "    Path(entered).write_text('entered')",
        ))
        child = None
        with self.recorder.case_session(plan) as session:
            session.claim(worker="parent")
            with self.assertRaisesRegex(RuntimeError, "already held"):
                self.recorder.claim(plan, worker="parent")
            errors = []

            def cross_thread():
                try:
                    session.claim(worker="parent")
                except RuntimeError as error:
                    errors.append(str(error))

            thread = threading.Thread(target=cross_thread)
            thread.start()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertIn("another thread", errors[0])
            child = subprocess.Popen(
                [
                    sys.executable, "-c", child_code, str(self.root), str(self.output),
                    json.dumps(asdict(plan)), str(started), str(entered),
                ],
                cwd=Path(__file__).resolve().parents[1],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            until = time.monotonic() + 10
            while not started.is_file() and time.monotonic() < until:
                time.sleep(0.02)
            self.assertTrue(started.is_file())
            time.sleep(0.2)
            self.assertFalse(entered.exists())
            session.record_engineering_success(
                attempt=1, attested_evidence_sha256="a" * 64,
            )
            direct_done = threading.Event()
            direct_errors = []

            def direct_short_lock():
                try:
                    self.recorder.claim(plan, worker="parent")
                except ValueError as error:
                    direct_errors.append(str(error))
                finally:
                    direct_done.set()

            competing_thread = threading.Thread(target=direct_short_lock, daemon=True)
            competing_thread.start()
            time.sleep(0.2)
            self.assertFalse(direct_done.is_set())
        assert child is not None
        try:
            stdout, stderr = child.communicate(timeout=10)
            self.assertEqual(child.returncode, 0, (stdout, stderr))
            self.assertEqual(entered.read_text("utf-8"), "entered")
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=3)
        competing_thread.join(timeout=3)
        self.assertTrue(direct_done.is_set())
        self.assertIn("engineering-completed", direct_errors[0])
        with self.assertRaisesRegex(RuntimeError, "closed"):
            session.claim(worker="parent")

    def test_engineering_success_intent_recovers_without_scientific_cell(self):
        plan = self.plans[0]
        evidence = "a" * 64
        self.recorder.claim(plan, worker="w")
        original_write = self.recorder._write

        def interrupt_before_receipt(directory, name, record):
            if directory == self.recorder._engineering_successes:
                raise RuntimeError("simulated engineering receipt interruption")
            return original_write(directory, name, record)

        with (
            patch.object(self.recorder, "_write", side_effect=interrupt_before_receipt),
            self.assertRaisesRegex(RuntimeError, "receipt interruption"),
        ):
            self.recorder.record_engineering_success(
                plan, attempt=1, attested_evidence_sha256=evidence,
            )
        incomplete = self.recorder.completion((plan,))
        self.assertEqual(incomplete["engineering_pending_recovery"], 1)
        self.assertEqual(incomplete["measured"], 0)
        self.assertFalse((self.output / "cells").exists())
        with self.assertRaisesRegex(ValueError, "engineering success intent"):
            self.recorder.record_failure(plan, attempt=1, reason={"error": "late failure"})
        with self.assertRaisesRegex(ValueError, "engineering success intent"):
            self.recorder.claim(plan, worker="w", attempt=2)
        with self.assertRaisesRegex(ValueError, "engineering terminal"):
            self.recorder.record_cell(identity(), metrics=metrics(), plan=plan)
        resumed = CaseRecorder(self.root, output_root=self.output)
        with self.assertRaisesRegex(ValueError, "intent no longer verifies"):
            resumed.recover_engineering_success(
                plan, expected_attested_evidence_sha256="b" * 64,
            )
        receipt = resumed.recover_engineering_success(
            plan, expected_attested_evidence_sha256=evidence,
        )
        resumed.recover_engineering_success(
            plan, expected_attested_evidence_sha256=evidence,
        )
        record = json.loads(receipt.read_text("utf-8"))
        self.assertEqual(record["kind"], "engineering_smoke")
        self.assertEqual(record["payload"]["purpose"], "pilot_case_engineering_success")
        self.assertTrue(record["payload"]["engineering_only"])
        self.assertFalse((self.output / "cells").exists())
        self.assertFalse((self.output / "successes").exists())
        complete = resumed.completion((plan,))
        self.assertEqual(complete["engineering_success"], 1)
        self.assertEqual(complete["engineering_pending_recovery"], 0)
        self.assertEqual(complete["measured"], 0)
        self.assertEqual(complete["pending"], 0)
        with self.assertRaises(FileExistsError):
            resumed.record_engineering_success(
                plan, attempt=1, attested_evidence_sha256="b" * 64,
            )
        with self.assertRaisesRegex(ValueError, "engineering-completed"):
            resumed.claim(plan, worker="w", attempt=2)
        with self.assertRaisesRegex(ValueError, "engineering-completed"):
            resumed.record_failure(plan, attempt=1, reason={"error": "late"})
        with self.assertRaisesRegex(ValueError, "engineering terminal"):
            resumed.record_cell(identity(), metrics=metrics(), plan=plan)

    def test_engineering_intent_rewrite_cannot_override_external_digest(self):
        plan = self.plans[0]
        original_digest = "a" * 64
        self.recorder.claim(plan, worker="w")
        original_write = self.recorder._write

        def interrupt_before_receipt(directory, name, record):
            if directory == self.recorder._engineering_successes:
                raise RuntimeError("simulated interruption")
            return original_write(directory, name, record)

        with (
            patch.object(self.recorder, "_write", side_effect=interrupt_before_receipt),
            self.assertRaisesRegex(RuntimeError, "simulated interruption"),
        ):
            self.recorder.record_engineering_success(
                plan, attempt=1, attested_evidence_sha256=original_digest,
            )
        intent_path = self.output / "engineering_intents" / f"{plan.case_id}.intent.json"
        original = json.loads(intent_path.read_text("utf-8"))
        changed = envelope("engineering_smoke", {
            **original["payload"], "attested_evidence_sha256": "b" * 64,
        })
        intent_path.write_bytes((canonical_config_json(changed) + "\n").encode("utf-8"))
        with self.assertRaisesRegex(ValueError, "intent no longer verifies"):
            self.recorder.recover_engineering_success(
                plan, expected_attested_evidence_sha256=original_digest,
            )
        self.assertFalse((self.output / "engineering_successes").exists())
        self.assertFalse((self.output / "cells").exists())

    def test_engineering_and_scientific_terminals_conflict_per_repetition(self):
        first, second = self.plans[:2]
        self.recorder.claim(first, worker="w")
        self.recorder.record_cell(identity(), metrics=metrics(), plan=first)
        with self.assertRaisesRegex(ValueError, "scientific publication conflicts"):
            self.recorder.record_engineering_success(
                first, attempt=1, attested_evidence_sha256="a" * 64,
            )
        self.recorder.claim(second, worker="w")
        self.recorder.record_engineering_success(
            second, attempt=1, attested_evidence_sha256="b" * 64,
        )
        completion = self.recorder.completion((first, second))
        self.assertEqual(completion["measured"], 1)
        self.assertEqual(completion["engineering_success"], 1)
        self.assertEqual(completion["failed"], 0)
        self.assertEqual(len(tuple((self.output / "cells").glob("*.json"))), 1)

    def test_direct_cell_refuses_engineering_intent_and_success_same_identity(self):
        first, second = self.plans[:2]
        self.recorder.claim(first, worker="w")
        original_write = self.recorder._write

        def interrupt_before_receipt(directory, name, record):
            if directory == self.recorder._engineering_successes:
                raise RuntimeError("simulated receipt crash")
            return original_write(directory, name, record)

        with (
            patch.object(self.recorder, "_write", side_effect=interrupt_before_receipt),
            self.assertRaisesRegex(RuntimeError, "receipt crash"),
        ):
            self.recorder.record_engineering_success(
                first, attempt=1, attested_evidence_sha256="a" * 64,
            )
        with self.assertRaisesRegex(ValueError, "direct scientific cell conflicts"):
            self.recorder.record_cell(identity(), metrics=metrics())
        self.assertFalse((self.output / "cells").exists())
        self.recorder.recover_engineering_success(
            first, expected_attested_evidence_sha256="a" * 64,
        )
        with self.assertRaisesRegex(ValueError, "direct scientific cell conflicts"):
            self.recorder.record_cell(identity(), metrics=metrics())
        self.recorder.claim(second, worker="w")
        self.recorder.record_cell(identity(), metrics=metrics(), plan=second)
        completion = self.recorder.completion((first, second))
        self.assertEqual(completion["engineering_success"], 1)
        self.assertEqual(completion["measured"], 1)

    def test_retry_completion_uses_latest_claim_and_separate_recovery_state(self):
        plan = self.plans[0]
        self.recorder.claim(plan, worker="w")
        self.recorder.record_failure(plan, attempt=1, reason={"error": "guard"})
        self.assertEqual(self.recorder.completion((plan,))["failed"], 1)
        with self.recorder.case_session(plan) as session:
            session.claim_new(worker="w", attempt=2)
        active = self.recorder.completion((plan,))
        self.assertEqual(active["failed"], 0)
        self.assertEqual(active["claimed_unmeasured"], 1)
        original_write = self.recorder._write

        def interrupt_before_receipt(directory, name, record):
            if directory == self.recorder._engineering_successes:
                raise RuntimeError("simulated receipt crash")
            return original_write(directory, name, record)

        with (
            patch.object(self.recorder, "_write", side_effect=interrupt_before_receipt),
            self.assertRaisesRegex(RuntimeError, "receipt crash"),
        ):
            self.recorder.record_engineering_success(
                plan, attempt=2, attested_evidence_sha256="a" * 64,
            )
        recovering = self.recorder.completion((plan,))
        self.assertEqual(recovering["failed"], 0)
        self.assertEqual(recovering["claimed_unmeasured"], 0)
        self.assertEqual(recovering["engineering_pending_recovery"], 1)

    def test_claim_new_refuses_active_replay_and_claim_refuses_failed_replay(self):
        plan = self.plans[0]
        with self.recorder.case_session(plan) as session:
            session.claim_new(worker="w", attempt=1)
            session.claim(worker="w", attempt=1)  # Existing replay API stays idempotent.
            with self.assertRaisesRegex(ValueError, "already claimed"):
                session.claim_new(worker="w", attempt=1)
        with self.recorder.case_session(plan) as session:
            with self.assertRaisesRegex(ValueError, "already claimed"):
                session.claim_new(worker="w", attempt=1)
            session.record_failure(attempt=1, reason={"error": "stopped"})
            with self.assertRaisesRegex(ValueError, "failed attempt cannot be claimed"):
                session.claim(worker="w", attempt=1)
            with self.assertRaisesRegex(ValueError, "already claimed"):
                session.claim_new(worker="w", attempt=1)
            session.claim_new(worker="w", attempt=2)
            with self.assertRaisesRegex(ValueError, "already claimed"):
                session.claim_new(worker="w", attempt=2)

    def test_output_root_must_stay_inside_runs(self):
        with self.assertRaises(ValueError):
            CaseRecorder(self.root, output_root=self.root / "elsewhere")
        with self.assertRaises(ValueError):
            CaseRecorder(self.root, output_root=self.root / "runs" / "phase2")
        recorder = CaseRecorder(self.root)
        self.assertEqual(recorder.output_root, (self.root / "runs/phase2/recorder").resolve())


if __name__ == "__main__":
    unittest.main()
