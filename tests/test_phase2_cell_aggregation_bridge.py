"""Recorder-to-aggregation checks use synthetic cells and never train a model."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from collections.abc import Iterator
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from core.config import canonical_config_json
from core.provenance import SourceProvenance
from evaluation.phase2_cell_aggregation_bridge import (
    MAX_CELL_BYTES,
    PinnedCaseCell,
    aggregate_recorder_cells,
    verified_score_rows,
)
from evaluation.phase2_records import CellIdentity, envelope
from evaluation.phase2_runner import CasePlan, CaseRecorder
from evaluation.phase2_subject_aggregation import ExpectedCell


def _identity(plan: CasePlan) -> CellIdentity:
    return CellIdentity(
        dataset=plan.dataset,
        target_subject=plan.target_subject,
        method=plan.method,
        shots_per_class=plan.shots_per_class,
        model_seed=plan.model_seed,
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
        git_commit="0" * 40,
        git_dirty=True,
    )


def _metrics(confusion: list[list[int]]) -> dict[str, object]:
    exact = sum(
        (Fraction(row[index], sum(row)) for index, row in enumerate(confusion)),
        Fraction(),
    ) / len(confusion)
    return {
        "role": "outer_target",
        "selection_evidence_sha256": "9" * 64,
        "confusion_matrix": confusion,
        "balanced_accuracy": [exact.numerator, exact.denominator],
        "query_count": sum(map(sum, confusion)),
    }


def _replace_payload(path: Path, **changes: object) -> None:
    record = json.loads(path.read_text("utf-8"))
    payload = record["payload"]
    payload.update(changes)
    revised = envelope("engineering_smoke", payload)
    path.write_bytes((canonical_config_json(revised) + "\n").encode("utf-8"))


class Phase2CellAggregationBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.recorder = CaseRecorder(self.root)

    def make_case(
        self, *, shots: int, seed: int, confusion: list[list[int]], attempt: int = 1,
    ) -> PinnedCaseCell:
        plan = CasePlan("synthetic", "subject_01", "method_a", shots, seed, 1)
        identity = _identity(plan)
        source = SourceProvenance(
            identity.git_commit, identity.source_sha256, identity.git_dirty,
        )
        with (
            patch("evaluation.phase2_runner.capture_source", return_value=source),
            patch(
                "evaluation.phase2_runner.environment_digest",
                return_value=identity.environment_sha256,
            ),
        ):
            self.recorder.claim(plan, worker="synthetic-test")
            if attempt == 2:
                self.recorder.record_failure(
                    plan, attempt=1, reason={"error": "synthetic first-attempt failure"},
                )
                self.recorder.claim(plan, worker="synthetic-test", attempt=2)
        cell_path = self.recorder.record_cell(identity, metrics=_metrics(confusion), plan=plan)
        cell = json.loads(cell_path.read_text("utf-8"))
        success_path = (
            self.recorder.output_root / "successes" / f"{plan.case_id}.success.json"
        )
        return PinnedCaseCell(
            plan=plan,
            key=ExpectedCell("synthetic", "subject_01", "method_a", shots, seed),
            identity=identity,
            attempt=attempt,
            cell_sha256=cell["sha256"],
            success_file_sha256=hashlib.sha256(success_path.read_bytes()).hexdigest(),
            selection_evidence_sha256="9" * 64,
        )

    def test_exact_roster_aggregates_seed_means_and_keeps_shots_separate(self) -> None:
        pins = (
            self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]]),
            self.make_case(shots=5, seed=23, confusion=[[1, 1], [1, 1]]),
            self.make_case(shots=10, seed=11, confusion=[[2, 1], [0, 3]]),
        )
        result = aggregate_recorder_cells(self.recorder, tuple(p.key for p in pins), pins)
        self.assertEqual(len(result.admitted_digests), 3)
        self.assertEqual(
            [(mean.shots, Fraction(mean.numerator, mean.denominator),
              mean.contributing_cells) for mean in result.means],
            [(5, Fraction(2, 3), 2), (10, Fraction(5, 6), 1)],
        )

    def test_missing_extra_or_duplicate_roster_never_aggregates(self) -> None:
        first = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
        second = self.make_case(shots=5, seed=23, confusion=[[1, 1], [1, 1]])
        roster = (first.key, second.key)
        with self.assertRaisesRegex(ValueError, "complete nonempty roster"):
            verified_score_rows(self.recorder, roster, (first,))
        with self.assertRaisesRegex(ValueError, "duplicate or incomplete"):
            verified_score_rows(self.recorder, (first.key, first.key), (first, second))
        self.make_case(shots=10, seed=11, confusion=[[2, 1], [0, 3]])
        with self.assertRaisesRegex(ValueError, "missing or extra records"):
            verified_score_rows(self.recorder, roster, (first, second))

    def test_orphan_cell_and_missing_intent_are_rejected(self) -> None:
        pin = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
        success = (
            self.recorder.output_root / "successes" / f"{pin.plan.case_id}.success.json"
        )
        success.unlink()
        with self.assertRaises(ValueError):
            verified_score_rows(self.recorder, (pin.key,), (pin,))

        # A success receipt without its publication intent is not sufficient.
        self.recorder = CaseRecorder(self.root, output_root=self.root / "runs/phase2/other")
        pin = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
        intent = (
            self.recorder.output_root / "publication_intents"
            / f"{pin.plan.case_id}.intent.json"
        )
        intent.unlink()
        with self.assertRaisesRegex(ValueError, "missing or extra records"):
            verified_score_rows(self.recorder, (pin.key,), (pin,))

    def test_linked_second_attempt_and_unlisted_claims(self) -> None:
        pin = self.make_case(
            shots=5, seed=11, confusion=[[2, 1], [0, 3]], attempt=2,
        )
        rows = verified_score_rows(self.recorder, (pin.key,), (pin,))
        self.assertEqual(len(rows), 1)
        with self.assertRaisesRegex(ValueError, "missing or extra records"):
            verified_score_rows(self.recorder, (pin.key,), (replace(pin, attempt=1),))
        failure = (
            self.recorder.output_root / "attempts"
            / f"{pin.plan.case_id}.attempt1.failure.json"
        )
        failure_bytes = failure.read_bytes()
        failure.unlink()
        with self.assertRaisesRegex(ValueError, "missing or extra records"):
            verified_score_rows(self.recorder, (pin.key,), (pin,))
        failure.write_bytes(failure_bytes)
        other = CasePlan("synthetic", "subject_02", "method_a", 5, 11, 1)
        self.recorder.claim(other, worker="unlisted-pending-case")
        with self.assertRaisesRegex(ValueError, "missing or extra records"):
            verified_score_rows(self.recorder, (pin.key,), (pin,))

    def test_directory_inventory_rejects_first_extra_without_scanning_remainder(self) -> None:
        pin = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
        claims = self.recorder.output_root / "claims"
        original_iterdir = Path.iterdir

        def guarded_iterdir(directory: Path) -> Iterator[Path]:
            if directory == claims:
                yield directory / "unexpected.record"
                raise AssertionError("scanned beyond first unexpected directory entry")
            yield from original_iterdir(directory)

        with (
            patch.object(Path, "iterdir", guarded_iterdir),
            self.assertRaisesRegex(ValueError, "missing or extra records"),
        ):
            verified_score_rows(self.recorder, (pin.key,), (pin,))

    def test_boolean_claim_and_failure_attempts_are_not_integers(self) -> None:
        pin = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
        claim = (
            self.recorder.output_root / "claims"
            / f"{pin.plan.case_id}.attempt1.claim.json"
        )
        _replace_payload(claim, attempt=True)
        with self.assertRaisesRegex(ValueError, "case claim differs"):
            verified_score_rows(self.recorder, (pin.key,), (pin,))

        other = CaseRecorder(self.root, output_root=self.root / "runs/phase2/boolean_failure")
        self.recorder = other
        retry = self.make_case(
            shots=5, seed=11, confusion=[[2, 1], [0, 3]], attempt=2,
        )
        failure = (
            self.recorder.output_root / "attempts"
            / f"{retry.plan.case_id}.attempt1.failure.json"
        )
        _replace_payload(failure, attempt=True)
        with self.assertRaisesRegex(ValueError, "prior failure does not justify"):
            verified_score_rows(self.recorder, (retry.key,), (retry,))

    def test_final_claim_provenance_must_match_pinned_identity(self) -> None:
        mutations: tuple[dict[str, object], ...] = (
            {"environment_sha256": "8" * 64},
            {"source": {"git_commit": "0" * 40, "git_dirty": True,
                        "source_sha256": "8" * 64}},
            {"source": {"git_commit": "f" * 40, "git_dirty": True,
                        "source_sha256": "1" * 64}},
            {"source": {"git_commit": "0" * 40, "git_dirty": False,
                        "source_sha256": "1" * 64}},
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self.recorder = CaseRecorder(
                    self.root, output_root=self.root / f"runs/phase2/provenance_{index}",
                )
                pin = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
                claim = (
                    self.recorder.output_root / "claims"
                    / f"{pin.plan.case_id}.attempt1.claim.json"
                )
                _replace_payload(claim, **mutation)
                with self.assertRaisesRegex(ValueError, "final claim provenance differs"):
                    verified_score_rows(self.recorder, (pin.key,), (pin,))

    def test_prior_attempt_can_have_different_valid_source_and_environment(self) -> None:
        pin = self.make_case(
            shots=5, seed=11, confusion=[[2, 1], [0, 3]], attempt=2,
        )
        first_claim = (
            self.recorder.output_root / "claims"
            / f"{pin.plan.case_id}.attempt1.claim.json"
        )
        _replace_payload(
            first_claim, environment_sha256="8" * 64,
            source={"git_commit": "unversioned-workspace", "git_dirty": None,
                    "source_sha256": "7" * 64},
        )
        first_failure = (
            self.recorder.output_root / "attempts"
            / f"{pin.plan.case_id}.attempt1.failure.json"
        )
        _replace_payload(first_failure, environment_sha256="6" * 64)
        self.assertEqual(len(verified_score_rows(self.recorder, (pin.key,), (pin,))), 1)

    def test_claim_source_provenance_schema_is_strict(self) -> None:
        bad_sources = (
            {"git_commit": "not-a-commit", "git_dirty": True,
             "source_sha256": "1" * 64},
            {"git_commit": "0" * 40, "git_dirty": 1,
             "source_sha256": "1" * 64},
            {"git_commit": "0" * 40, "git_dirty": "true",
             "source_sha256": "1" * 64},
        )
        for index, source in enumerate(bad_sources):
            with self.subTest(index=index):
                self.recorder = CaseRecorder(
                    self.root, output_root=self.root / f"runs/phase2/schema_{index}",
                )
                pin = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
                claim = (
                    self.recorder.output_root / "claims"
                    / f"{pin.plan.case_id}.attempt1.claim.json"
                )
                _replace_payload(claim, source=source)
                with self.assertRaisesRegex(ValueError, "case claim differs"):
                    verified_score_rows(self.recorder, (pin.key,), (pin,))

    def test_oversized_expected_cell_is_rejected_before_json_loading(self) -> None:
        pin = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
        cell_path = self.recorder.output_root / "cells" / f"{pin.identity.sha256}.json"
        cell_path.write_bytes(b" " * (MAX_CELL_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "size or link count"):
            verified_score_rows(self.recorder, (pin.key,), (pin,))

    def test_external_success_and_selection_pins_are_required(self) -> None:
        pin = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
        with self.assertRaisesRegex(ValueError, "case success differs"):
            verified_score_rows(
                self.recorder, (pin.key,),
                (replace(pin, success_file_sha256="f" * 64),),
            )
        with self.assertRaisesRegex(ValueError, "selection-evidence digest differs"):
            verified_score_rows(
                self.recorder, (pin.key,),
                (replace(pin, selection_evidence_sha256="8" * 64),),
            )

    def test_self_consistent_forgery_cannot_change_the_exact_score(self) -> None:
        pin = self.make_case(shots=5, seed=11, confusion=[[2, 1], [0, 3]])
        cell_path = self.recorder.output_root / "cells" / f"{pin.identity.sha256}.json"
        cell = json.loads(cell_path.read_text("utf-8"))
        cell["payload"]["metrics"]["balanced_accuracy"] = [1, 1]
        cell = envelope("evaluation_cell", cell["payload"])
        cell_path.write_bytes((canonical_config_json(cell) + "\n").encode("utf-8"))
        intent_path = (
            self.recorder.output_root / "publication_intents"
            / f"{pin.plan.case_id}.intent.json"
        )
        intent = json.loads(intent_path.read_text("utf-8"))
        intent["payload"]["cell"] = cell
        intent = envelope("engineering_smoke", intent["payload"])
        intent_path.write_bytes((canonical_config_json(intent) + "\n").encode("utf-8"))
        success_path = (
            self.recorder.output_root / "successes" / f"{pin.plan.case_id}.success.json"
        )
        success = json.loads(success_path.read_text("utf-8"))
        success["payload"]["cell_sha256"] = cell["sha256"]
        success = envelope("engineering_smoke", success["payload"])
        success_path.write_bytes((canonical_config_json(success) + "\n").encode("utf-8"))
        repinned = replace(
            pin,
            cell_sha256=cell["sha256"],
            success_file_sha256=hashlib.sha256(success_path.read_bytes()).hexdigest(),
        )
        with self.assertRaisesRegex(ValueError, "exact rational mean class recall"):
            verified_score_rows(self.recorder, (pin.key,), (repinned,))


if __name__ == "__main__":
    unittest.main()
