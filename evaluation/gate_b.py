"""Fail-closed Gate B completeness and power-freeze evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from evaluation.benchmark_audit import audit_benchmark
from evaluation.gate_evidence import verify_gate_evidence
from evaluation.reporting import (
    aggregate_observations,
    collect_observations,
)
from evaluation.statistics import (
    normal_approximation_equivalence_power,
    variance_derived_equivalence_margin,
)


@dataclass(frozen=True, slots=True)
class GateBResult:
    passed: bool
    local_deliverables_complete: bool
    upstream_gate_a_signed: bool
    missing_records: int
    invalid_records: int
    unexpected_records: int
    benchmark_integrity_passed: bool
    record_snapshot_sha256: str
    preprocessing_frozen: bool
    artifact_audit_passed: bool
    demonstrator_passed: bool
    reporting_bundle_complete: bool
    plausibility_review_complete: bool
    equivalence_margin_frozen: bool
    corpus_duplicate_audit_current: bool
    no_exact_train_query_copies: bool
    margin_source_dataset: str
    margin_source_method: str
    source_standard_deviation: float
    subject_count: int
    equivalence_margin: float
    achieved_power: float
    target_power: float
    alpha: float

    def as_dict(self) -> dict[str, str | int | float | bool]:
        return asdict(self)


def evaluate_gate_b(
    run_root: Path,
    *,
    project_root: Path,
    dataset_subjects: dict[str, tuple[str, ...]],
    methods: tuple[str, ...],
    seeds: tuple[int, ...],
    preprocessing_frozen: bool,
    margin_source_dataset: str,
    margin_source_method: str,
    target_power: float,
    alpha: float,
    expected_config_sha256: str,
    artifact_audit_passed: bool = False,
    demonstrator_passed: bool = False,
    upstream_gate_a_signed: bool = False,
) -> GateBResult:
    integrity = audit_benchmark(
        run_root,
        datasets_subjects=dataset_subjects,
        methods=methods,
        seeds=seeds,
        expected_config_sha256=expected_config_sha256,
    )
    rows = (
        aggregate_observations(
            collect_observations(run_root, expected_config_sha256=expected_config_sha256)
        )
        if integrity["existing_records_arithmetic_passed"]
        else []
    )
    source = next(
        (
            row
            for row in rows
            if row.dataset == margin_source_dataset and row.method == margin_source_method
        ),
        None,
    )
    expected_subjects = len(dataset_subjects[margin_source_dataset])
    source_complete = bool(
        source is not None
        and source.subject_count == expected_subjects
        and source.record_count == expected_subjects * len(seeds)
        and source.standard_deviation > 0.0
    )
    standard_deviation = source.standard_deviation if source_complete and source else 0.0
    margin = (
        variance_derived_equivalence_margin(
            standard_deviation,
            subjects=expected_subjects,
            target_power=target_power,
            alpha=alpha,
        )
        if source_complete
        else 0.0
    )
    achieved_power = (
        normal_approximation_equivalence_power(
            margin,
            standard_deviation=standard_deviation,
            subjects=expected_subjects,
            alpha=alpha,
        )
        if source_complete
        else 0.0
    )
    evidence = verify_gate_evidence(
        project_root,
        run_root,
        integrity=integrity,
        dataset_subjects=dataset_subjects,
        seeds=seeds,
        expected_config_sha256=expected_config_sha256,
        margin_source_dataset=margin_source_dataset,
        margin_source_method=margin_source_method,
        target_power=target_power,
        alpha=alpha,
    )
    local_complete = bool(
        integrity["complete"]
        and preprocessing_frozen
        and source_complete
        and artifact_audit_passed
        and demonstrator_passed
        and evidence.complete
    )
    return GateBResult(
        passed=local_complete and upstream_gate_a_signed is True,
        local_deliverables_complete=local_complete,
        upstream_gate_a_signed=upstream_gate_a_signed is True,
        missing_records=len(integrity["missing_records"]),
        invalid_records=len(integrity["invalid_records"]),
        unexpected_records=len(integrity["unexpected_records"]),
        benchmark_integrity_passed=bool(integrity["complete"]),
        record_snapshot_sha256=str(integrity["record_snapshot_sha256"]),
        preprocessing_frozen=preprocessing_frozen,
        artifact_audit_passed=artifact_audit_passed,
        demonstrator_passed=demonstrator_passed,
        reporting_bundle_complete=evidence.reporting_bundle_complete,
        plausibility_review_complete=evidence.plausibility_review_complete,
        equivalence_margin_frozen=evidence.equivalence_margin_frozen,
        corpus_duplicate_audit_current=evidence.corpus_duplicate_audit_current,
        no_exact_train_query_copies=evidence.no_exact_train_query_copies,
        margin_source_dataset=margin_source_dataset,
        margin_source_method=margin_source_method,
        source_standard_deviation=standard_deviation,
        subject_count=expected_subjects,
        equivalence_margin=margin,
        achieved_power=achieved_power,
        target_power=target_power,
        alpha=alpha,
    )
