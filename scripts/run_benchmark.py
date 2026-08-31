from __future__ import annotations

import argparse
import json
import statistics
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import load_toml
from evaluation.baselines import TorchTrainingConfig
from evaluation.benchmark import (
    estimated_instance_hours,
    load_dataset_matrix,
    run_benchmark,
)
from evaluation.reporting import collect_observations


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or resume the Phase I benchmark")
    parser.add_argument("--dataset", choices=("bci_iv_2a", "cho2017", "mmidb"), required=True)
    parser.add_argument("--method", action="append")
    parser.add_argument("--max-new-runs", type=int)
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(project_root / "configs" / "benchmark.toml"))
    benchmark = cast(Mapping[str, Any], config["benchmark"])
    training = cast(Mapping[str, Any], config["training"])
    cost = cast(Mapping[str, Any], config["cost"])
    datasets = cast(Mapping[str, Any], config["datasets"])
    dataset = cast(Mapping[str, Any], datasets[args.dataset])
    matrix = load_dataset_matrix(
        project_root / str(dataset["artifact_directory"]),
        dataset=args.dataset,
        sampling_rate_hz=float(dataset["sampling_rate_hz"]),
        absolute_peak_volts=float(dataset["artifact_threshold_volts"]),
    )
    methods = tuple(args.method or cast(list[str], benchmark["methods"]))
    observations = collect_observations(project_root / "runs" / "benchmark")
    completed_durations: list[float] = []
    for observation in observations:
        if observation.dataset != args.dataset:
            continue
        path = (
            project_root
            / "runs"
            / "benchmark"
            / observation.dataset
            / observation.method
            / f"seed_{observation.seed}"
            / f"{observation.subject}.json"
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        metrics = cast(Mapping[str, Any], payload["metrics"])
        completed_durations.append(
            float(metrics["fit_seconds"]) + float(metrics["prediction_seconds"])
        )
    seconds_per_run = (
        statistics.median(completed_durations)
        if completed_durations
        else float(cost["fallback_seconds_per_run"])
    )
    estimate = estimated_instance_hours(
        completed_run_seconds=seconds_per_run,
        methods=len(methods),
        datasets_and_folds={args.dataset: len(set(matrix.subjects.tolist()))},
        seeds=len(cast(list[int], benchmark["seeds"])),
    )
    print(
        json.dumps(
            {
                "cost_basis": str(cost["cost_basis"]),
                "estimated_instance_hours": estimate,
                "seconds_per_run_basis": seconds_per_run,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    outputs = run_benchmark(
        matrix,
        methods=methods,
        seeds=cast(list[int], benchmark["seeds"]),
        shots_per_class=int(benchmark["shots_per_class"]),
        confidence_threshold=float(benchmark["confidence_threshold"]),
        torch_config=TorchTrainingConfig(
            epochs=int(training["epochs"]),
            batch_size=int(training["batch_size"]),
            learning_rate=float(training["learning_rate"]),
            weight_decay=float(training["weight_decay"]),
            input_scale=float(training["input_scale"]),
            device=str(training["device"]),
        ),
        output_root=project_root / "runs" / "benchmark",
        config=config,
        max_new_runs=args.max_new_runs,
    )
    print(json.dumps({"valid_records": len(outputs)}, sort_keys=True))


if __name__ == "__main__":
    main()
