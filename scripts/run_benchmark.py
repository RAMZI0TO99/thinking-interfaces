from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.compute_estimate import benchmark_work_report
from evaluation.process_eigh_runtime import process_eigh_enabled, process_eigh_startup_ready


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
    datasets = cast(Mapping[str, Any], config["datasets"])
    dataset = cast(Mapping[str, Any], datasets[args.dataset])
    methods = tuple(args.method or cast(list[str], benchmark["methods"]))
    runtime = load_toml(project_root / "configs/runtime_limits.toml")
    process_startup_ready = process_eigh_startup_ready(
        project_root,
        enabled=process_eigh_enabled(runtime),
        dataset=args.dataset,
        methods=methods,
        benchmark_sha256=config_digest(config),
    )
    print(json.dumps({"process_eigh_qualified_startup": process_startup_ready}), flush=True)
    # Spawned numerical workers must not import the heavy EEG/Torch stack.
    from evaluation.baselines import TorchTrainingConfig
    from evaluation.benchmark import load_dataset_matrix, run_benchmark

    matrix = load_dataset_matrix(
        project_root / str(dataset["artifact_directory"]),
        dataset=args.dataset,
        sampling_rate_hz=float(dataset["sampling_rate_hz"]),
        absolute_peak_volts=float(dataset["artifact_threshold_volts"]),
    )
    print(
        json.dumps(
            benchmark_work_report(project_root, config, datasets=(args.dataset,), methods=methods),
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
        process_eigh_startup_headroom=process_startup_ready,
    )
    print(json.dumps({"valid_records": len(outputs)}, sort_keys=True))


if __name__ == "__main__":
    main()
