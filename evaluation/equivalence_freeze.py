"""One-time H2 planning-margin freeze backed by independently audited source files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.provenance import capture_source
from core.run_record import RunRecord
from evaluation.benchmark_audit import inspect_record
from evaluation.reporting import RecordObservation, aggregate_observations
from evaluation.statistics import (
    normal_approximation_equivalence_power,
    variance_derived_equivalence_margin,
)


def source_margin_record(
    run_root: Path,
    *,
    dataset: str,
    method: str,
    subjects: tuple[str, ...],
    seeds: tuple[int, ...],
    expected_config_sha256: str,
    target_power: float,
    alpha: float,
) -> RunRecord:
    if len(subjects) < 2 or len(subjects) != len(set(subjects)) or not seeds:
        raise ValueError("unique subjects and nonempty seeds are required")
    if len(seeds) != len(set(seeds)):
        raise ValueError("duplicate source seeds")
    directory = run_root / dataset / method
    expected = {
        directory / f"seed_{seed}" / f"{subject}.json" for seed in seeds for subject in subjects
    }
    actual = set(directory.glob("seed_*/*.json"))
    if actual != expected:
        raise ValueError("margin source grid is incomplete or contains unexpected records")
    inspected = [
        inspect_record(path, expected_config_sha256=expected_config_sha256)
        for path in sorted(expected)
    ]
    observations = tuple(
        RecordObservation(
            record.dataset,
            record.method,
            record.subject,
            record.seed,
            record.metrics["balanced_accuracy"],
        )
        for record in inspected
    )
    row = aggregate_observations(observations)[0]
    margin = variance_derived_equivalence_margin(
        row.standard_deviation,
        subjects=row.subject_count,
        target_power=target_power,
        alpha=alpha,
    )
    fingerprint = "\n".join(
        f"{record.subject}:{record.seed}:{record.sha256}" for record in inspected
    )
    config = {
        "frozen": True,
        "source_dataset": dataset,
        "source_method": method,
        "source_subjects": sorted(subjects),
        "source_seeds": sorted(seeds),
        "benchmark_config_sha256": expected_config_sha256,
        "source_record_snapshot_sha256": hashlib.sha256(fingerprint.encode()).hexdigest(),
        "target_power": target_power,
        "alpha": alpha,
        "formula": "margin=(z(1-alpha)+z((1+target_power)/2))*subject_sd/sqrt(subjects)",
        "assumptions": (
            "zero true difference; known variance normal approximation; baseline SD proxy"
        ),
        "scientific_gate_approval": False,
        "limitations": (
            "Gate A unsigned; Cho loader-order confounds unresolved; actual H2 power unknown"
        ),
    }
    source_provenance = capture_source(Path(__file__).resolve().parents[1])
    return RunRecord.create(
        config=config,
        seed=0,
        git_commit=source_provenance.git_commit,
        source_sha256=source_provenance.source_sha256,
        git_dirty=source_provenance.git_dirty,
        dataset=dataset,
        fold="h2_design_margin_freeze",
        metrics={
            "equivalence_margin": margin,
            "equivalence_margin_percentage_points": margin * 100,
            "source_standard_deviation": row.standard_deviation,
            "source_balanced_accuracy_mean": row.mean,
            "subject_count": float(row.subject_count),
            "source_record_count": float(row.record_count),
            "approximate_design_power": normal_approximation_equivalence_power(
                margin,
                standard_deviation=row.standard_deviation,
                subjects=row.subject_count,
                alpha=alpha,
            ),
        },
    )


def write_margin_once(record: RunRecord, output: Path) -> bool:
    """Never silently re-freeze if a source record, policy, or result has changed."""
    if output.exists():
        saved = json.loads(output.read_text(encoding="utf-8"))
        if saved.get("config") != record.config or saved.get("metrics") != record.metrics:
            raise ValueError("existing margin freeze differs; explicit protocol amendment required")
        if saved.get("config_sha256") != record.config_sha256:
            raise ValueError("existing margin freeze has inconsistent provenance")
        return False
    record.write_json(output)
    return True
