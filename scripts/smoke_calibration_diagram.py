"""Hand-worked synthetic rendering check, never a benchmark calibration result."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from core.provenance import capture_source
from evaluation.calibration_plot import save_calibration_diagnostics
from evaluation.realtime_metrics import accuracy_coverage_curve, calibration_report


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    probabilities = np.asarray([
        [0.9, 0.1], [0.8, 0.2], [0.7, 0.3], [0.6, 0.4],
        [0.4, 0.6], [0.3, 0.7], [0.2, 0.8], [0.1, 0.9],
    ])
    targets = np.asarray([0, 1, 0, 1, 1, 0, 1, 1], dtype=np.int64)
    thresholds = (0.0, 0.7, 0.8, 0.9, 1.0)
    report = calibration_report(probabilities, targets, bins=5)
    curve = accuracy_coverage_curve(probabilities, targets, thresholds=thresholds)
    np.testing.assert_allclose(report.expected_calibration_error, 0.125, atol=1e-12)
    assert curve[0].accuracy == 0.625 and curve[0].coverage == 1.0
    assert curve[-1].accuracy is None and curve[-1].coverage == 0.0
    output = root / "runs" / "calibration_smoke" / "reliability_and_coverage.png"
    save_calibration_diagnostics(
        probabilities, targets, output,
        title="Synthetic utility check — not EEG benchmark results", bins=5,
        thresholds=thresholds,
    )
    result = {
        "passed": True, "synthetic_only": True,
        "source": asdict(capture_source(root)),
        "probabilities": probabilities.tolist(), "targets": targets.tolist(),
        "calibration": asdict(report), "coverage": [asdict(point) for point in curve],
        "figure": output.relative_to(root).as_posix(),
        "figure_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    (output.parent / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
