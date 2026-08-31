from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from data.runtime import configure_scientific_runtime

configure_scientific_runtime()

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from evaluation.benchmark_audit import audit_benchmark  # noqa: E402
from evaluation.benchmark_diagnostics import (  # noqa: E402
    aggregate_diagnostics,
    read_audited_snapshot,
)
from evaluation.reporting import RecordObservation, aggregate_observations  # noqa: E402


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(project_root / "configs" / "benchmark.toml"))
    subjects = {
        name: tuple(
            path.stem
            for path in sorted(
                (project_root / config["datasets"][name]["artifact_directory"]).glob(
                    "subject_*.npz"
                )
            )
        )
        for name in config["benchmark"]["datasets"]
    }
    integrity = audit_benchmark(
        project_root / "runs" / "benchmark",
        datasets_subjects=subjects,
        methods=config["benchmark"]["methods"],
        seeds=config["benchmark"]["seeds"],
        expected_config_sha256=config_digest(config),
    )
    if integrity["invalid_records"] or integrity["unexpected_records"]:
        raise ValueError("record integrity failed; no benchmark figures were overwritten")
    records = read_audited_snapshot(
        project_root / "runs" / "benchmark",
        integrity["record_files"],
        expected_config_sha256=config_digest(config),
    )
    rows = aggregate_observations(
        tuple(
            RecordObservation(
                record.dataset,
                record.method,
                record.subject,
                record.seed,
                record.metrics["balanced_accuracy"],
            )
            for record in records
        ),
        confidence_level=float(config["benchmark"]["confidence_level"]),
    )
    diagnostics = {
        (row.dataset, row.method): row
        for row in aggregate_diagnostics(
            records, confidence_threshold=config["benchmark"]["confidence_threshold"]
        )
    }
    if not rows:
        raise ValueError("no benchmark records exist; nothing can be plotted")
    output_root = project_root / "runs" / "figures"
    output_root.mkdir(parents=True, exist_ok=True)
    figure_hashes = {}
    for dataset in sorted({row.dataset for row in rows}):
        selected = [row for row in rows if row.dataset == dataset]
        means = [row.mean for row in selected]
        lower = [row.mean - row.confidence_low for row in selected]
        upper = [row.confidence_high - row.mean for row in selected]
        class_labels = json.loads(diagnostics[(dataset, selected[0].method)].class_labels_json)
        tick_labels = []
        for row in selected:
            diagnostic = diagnostics[(dataset, row.method)]
            counts = json.loads(diagnostic.query_class_counts_including_seed_repeats_json)
            percentages = "/".join(
                f"{100 * counts[label] / sum(counts.values()):.1f}" for label in class_labels
            )
            tick_labels.append(
                f"{row.method}\nn={row.subject_count}, runs={row.record_count}"
                f"\nclass %={percentages}"
            )
        figure, axis = plt.subplots(figsize=(10.8, 6.2))
        axis.bar(
            tick_labels,
            means,
            yerr=[lower, upper],
            capsize=4,
        )
        axis.set_ylim(0.0, 1.0)
        axis.set_ylabel("Balanced accuracy")
        interval_label = f"{100 * float(config['benchmark']['confidence_level']):g}%"
        axis.set_title(f"{dataset}: subject-level mean and {interval_label} interval (exploratory)")
        figure.text(
            0.01,
            0.01,
            "Gate A unsigned. "
            + (
                "This dataset's grid is complete."
                if (
                    len(selected) == len(config["benchmark"]["methods"])
                    and all(
                        row.record_count
                        == len(subjects[dataset]) * len(config["benchmark"]["seeds"])
                        for row in selected
                    )
                )
                else "This dataset's grid is partial."
            ),
            fontsize=8,
        )
        figure.text(
            0.01,
            0.045,
            "Class order: "
            + " / ".join(class_labels)
            + ". Pooled query counts include repeated seeds.",
            fontsize=8,
        )
        axis.tick_params(axis="x", rotation=25, labelsize=9)
        for label in axis.get_xticklabels():
            label.set_horizontalalignment("right")
        figure.tight_layout(rect=(0, 0.10, 1, 1))
        output = output_root / f"{dataset}_benchmark.png"
        temporary = output.with_suffix(".png.tmp")
        figure.savefig(temporary, dpi=160, format="png")
        os.replace(temporary, output)
        figure_hashes[output.name] = hashlib.sha256(output.read_bytes()).hexdigest()
        plt.close(figure)
    manifest = {
        "complete": integrity["complete"],
        "config_sha256": config_digest(config),
        "record_snapshot_sha256": integrity["record_snapshot_sha256"],
        "files": figure_hashes,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
