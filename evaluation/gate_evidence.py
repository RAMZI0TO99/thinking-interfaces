"""Read-only, snapshot-bound local deliverables shared by both completion checkers."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import config_digest, load_toml
from evaluation.corpus_duplicates import verify_corpus_snapshot
from evaluation.equivalence_freeze import source_margin_record


def read_json(path: Path) -> dict[str, Any]:
    """Missing, malformed and non-object evidence is never a passing receipt."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def hash_matches(path: Path, expected: object) -> bool:
    try:
        return bool(
            isinstance(expected, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected)
            and hashlib.sha256(path.read_bytes()).hexdigest() == expected
        )
    except OSError:
        return False


@dataclass(frozen=True, slots=True)
class GateEvidence:
    reporting_bundle_complete: bool = False
    plausibility_review_complete: bool = False
    equivalence_margin_frozen: bool = False
    corpus_duplicate_audit_current: bool = False
    no_exact_train_query_copies: bool = False

    @property
    def complete(self) -> bool:
        return bool(
            self.reporting_bundle_complete
            and self.plausibility_review_complete
            and self.equivalence_margin_frozen
            and self.corpus_duplicate_audit_current
            and self.no_exact_train_query_copies
        )


def verify_gate_evidence(
    root: Path,
    run_root: Path,
    *,
    integrity: Mapping[str, Any],
    dataset_subjects: dict[str, tuple[str, ...]],
    seeds: tuple[int, ...],
    expected_config_sha256: str,
    margin_source_dataset: str,
    margin_source_method: str,
    target_power: float,
    alpha: float,
) -> GateEvidence:
    """Check existing outputs only; never generate reports, reviews or a new freeze."""
    try:
        config = load_toml(root / "configs" / "benchmark.toml")
        snapshot = integrity["record_snapshot_sha256"]
        if not (
            config_digest(config) == expected_config_sha256
            and integrity.get("config_sha256") == expected_config_sha256
            and isinstance(snapshot, str)
            and re.fullmatch(r"[0-9a-f]{64}", snapshot)
        ):
            return GateEvidence()
    except (OSError, ValueError, KeyError, TypeError):
        return GateEvidence()

    def matches_snapshot(report: Mapping[str, Any]) -> bool:
        return bool(
            report.get("record_snapshot_sha256") == snapshot
            and report.get("config_sha256") == expected_config_sha256
        )

    table = read_json(root / "runs" / "benchmark_status.json")
    figures = read_json(root / "runs" / "figures" / "manifest.json")
    files = figures.get("files")
    reporting_complete = bool(
        integrity.get("complete") is True
        and table.get("complete") is True
        and figures.get("complete") is True
        and matches_snapshot(table)
        and matches_snapshot(figures)
        and hash_matches(root / "runs" / "benchmark_table.csv", table.get("table_sha256"))
        and hash_matches(
            root / "runs" / "benchmark_diagnostics.csv", table.get("diagnostics_sha256")
        )
        and isinstance(files, dict)
        and set(files) == {f"{dataset}_benchmark.png" for dataset in dataset_subjects}
        and all(
            hash_matches(root / "runs" / "figures" / name, value) for name, value in files.items()
        )
    )
    corpus = read_json(root / "runs" / "corpus_duplicate_audit.json")
    corpus_current = verify_corpus_snapshot(root, corpus, config=config, subjects=dataset_subjects)
    no_copies = bool(corpus_current and corpus.get("no_exact_train_query_copies") is True)
    review = read_json(root / "runs" / "plausibility_review.json")
    review_complete = bool(
        integrity.get("complete") is True
        and review.get("local_review_complete") is True
        and matches_snapshot(review)
        and corpus_current
        and review.get("artifact_snapshot_sha256") == corpus.get("artifact_snapshot_sha256")
    )

    margin_frozen = False
    freeze = read_json(root / "runs" / "equivalence_margin_freeze.json")
    if freeze:
        try:
            expected = source_margin_record(
                run_root,
                dataset=margin_source_dataset,
                method=margin_source_method,
                subjects=dataset_subjects[margin_source_dataset],
                seeds=seeds,
                expected_config_sha256=expected_config_sha256,
                target_power=target_power,
                alpha=alpha,
            )
            margin_frozen = bool(
                freeze.get("config") == expected.config
                and freeze.get("metrics") == expected.metrics
                and freeze.get("config_sha256") == expected.config_sha256
                and config_digest(freeze["config"]) == expected.config_sha256
            )
        except (OSError, ValueError, KeyError, TypeError):
            margin_frozen = False
    return GateEvidence(
        reporting_complete, review_complete, margin_frozen, corpus_current, no_copies
    )
