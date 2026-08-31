"""Render reliability and selective-accuracy diagnostics from actual probabilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from data.runtime import configure_scientific_runtime
from evaluation.realtime_metrics import accuracy_coverage_curve, calibration_report

configure_scientific_runtime()

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


def save_calibration_diagnostics(
    probabilities: NDArray[np.floating],
    targets: NDArray[np.integer],
    path: Path,
    *,
    title: str,
    bins: int = 10,
    thresholds: tuple[float, ...] = (0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
) -> None:
    """Empty bins and zero-coverage accuracies are omitted, not plotted as zero."""
    report = calibration_report(probabilities, targets, bins=bins)
    curve = accuracy_coverage_curve(probabilities, targets, thresholds=thresholds)
    if not thresholds or tuple(sorted(set(thresholds))) != thresholds:
        raise ValueError("plot thresholds must be nonempty, sorted and distinct")
    occupied = [row for row in report.bins if row.count]
    covered = [point for point in curve if point.accuracy is not None]
    figure, (reliability, selective) = plt.subplots(1, 2, figsize=(10.5, 4.7))
    try:
        reliability.plot([0, 1], [0, 1], "--", color="#87919c", label="Perfect calibration")
        reliability.scatter(
            [row.mean_confidence for row in occupied],
            [row.accuracy for row in occupied],
            s=[35 + 130 * row.count / len(targets) for row in occupied],
            color="#186899", zorder=3, label="Occupied bins (size = count)",
        )
        reliability.vlines(
            [row.mean_confidence for row in occupied],
            [row.mean_confidence for row in occupied],
            [row.accuracy for row in occupied],
            color="#bd5848", linewidth=2,
        )
        reliability.set(
            xlabel="Mean predicted confidence", ylabel="Observed accuracy",
            title=f"Reliability | ECE = {report.expected_calibration_error:.3f}",
        )
        reliability.legend(loc="upper left", fontsize=8)
        selective.plot(
            [point.coverage for point in covered],
            [point.accuracy for point in covered], "o-", color="#186899",
        )
        for point in covered:
            assert point.accuracy is not None
            selective.annotate(
                f"{point.threshold:g}", (point.coverage, float(point.accuracy)),
                xytext=(4, 5), textcoords="offset points", fontsize=8,
            )
        selective.set(
            xlabel="Fraction of samples retained", ylabel="Accuracy among retained samples",
            title="Accuracy–coverage | labels = thresholds",
        )
        for axis in (reliability, selective):
            axis.set_xlim(-0.025, 1.09)
            axis.set_ylim(-0.025, 1.09)
            axis.grid(alpha=0.18)
        figure.suptitle(title, fontsize=12)
        figure.text(
            0.02, 0.02,
            f"n={len(targets)}; {bins} fixed-width bins. Empty bins and empty selections omitted. "
            "No calibration is fitted here.", fontsize=8,
        )
        figure.tight_layout(rect=(0, 0.06, 1, 0.97))
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=150)
    finally:
        plt.close(figure)
