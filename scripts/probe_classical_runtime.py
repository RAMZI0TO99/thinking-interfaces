"""Isolated CPU-thread probe; never rewrites or contributes benchmark records."""

from __future__ import annotations

import argparse
import cProfile
import json
import pstats
from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits  # type: ignore[import-untyped]

from core.config import config_digest, load_toml
from core.provenance import capture_source
from evaluation.benchmark_audit import inspect_record
from evaluation.corpus_duplicates import verify_corpus_snapshot
from evaluation.process_eigh_probe import ProcessEighProbe, available_memory_gib


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Isolated classical runtime and exact-metric probe"
    )
    parser.add_argument("--config", default="configs/classical_runtime_probe.toml")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    probe_config = cast(Mapping[str, Any], load_toml(root / args.config))
    probe = probe_config["probe"]
    process_workers = probe.get("eigh_processes")
    initial_source = capture_source(root)
    if process_workers is not None:
        runtime = probe_config["runtime"]
        if (
            process_workers != 2
            or type(process_workers) is not int
            or probe.get("eigh_chunk_matrices") != 64
            or runtime.get("minimum_free_memory_gib") != 10.0
            or runtime.get("stop_below_free_memory_gib") != 4.0
            or probe["blas_threads"] != 24
            or probe.get("eigh_blas_threads") is not None
            or probe["method"] not in {"tangent_lr", "ea_tangent_lr"}
        ):
            raise ValueError("isolated process probe settings do not match its bounded protocol")
        if initial_source.git_dirty is not False:
            raise ValueError("commit the process-probe source before measuring real folds")
        if available_memory_gib() < runtime["minimum_free_memory_gib"]:
            raise SystemExit(
                "Process probe deferred: insufficient free memory before model imports"
            )
    # Keep spawned numerical workers lightweight; do not import the EEG stack in them.
    from evaluation.baselines import FilterBankCSP, FloatArray, TorchTrainingConfig
    from evaluation.benchmark import _decoder, load_dataset_matrix, run_fold

    method = str(probe["method"])
    if method not in {"fbcsp", "tangent_lr", "ea_tangent_lr"} or (
        probe["require_exact_non_timing_metrics"] is not True
    ):
        raise ValueError("this probe only verifies exact-metric FBCSP/tangent runtime parity")
    if method != "fbcsp" and probe.get("certify_csp_rank", False):
        raise ValueError("CSP rank certification cannot apply to a tangent-space probe")
    if type(probe["blas_threads"]) is not int or probe["blas_threads"] < 1:
        raise ValueError("a positive CPU BLAS thread bound is required")
    if type(probe.get("profile_calls", False)) is not bool:
        raise ValueError("call profiling must be an explicit boolean")
    eigh_threads = probe.get("eigh_blas_threads")
    if eigh_threads is not None and (
        type(eigh_threads) is not int or eigh_threads < 1 or method != "tangent_lr"
    ):
        raise ValueError("selective eigensolver limits require a positive tangent-only bound")
    dataset = str(probe["dataset"])
    settings = config["datasets"][dataset]
    subjects = {
        name: tuple(
            path.stem
            for path in sorted(
                (root / config["datasets"][name]["artifact_directory"]).glob("subject_*.npz")
            )
        )
        for name in config["benchmark"]["datasets"]
    }
    corpus = json.loads((root / "runs" / "corpus_duplicate_audit.json").read_text("utf-8"))
    if not verify_corpus_snapshot(root, corpus, config=config, subjects=subjects):
        raise ValueError("current input snapshot does not match the independent corpus audit")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = root / "runs" / "runtime_probe" / stamp / "result.json"
    output.parent.mkdir(parents=True)
    matrix = load_dataset_matrix(
        root / settings["artifact_directory"],
        dataset=dataset,
        sampling_rate_hz=settings["sampling_rate_hz"],
        absolute_peak_volts=settings["artifact_threshold_volts"],
    )
    training = TorchTrainingConfig(**config["training"])
    bands: tuple[FloatArray, ...] | None = None
    if method == "fbcsp":
        filtering = _decoder(
            "fbcsp",
            matrix,
            classes=len(set(matrix.labels.tolist())),
            seed=probe["seed"],
            torch_config=training,
        )
        if not isinstance(filtering, FilterBankCSP):
            raise TypeError("FBCSP factory returned a different decoder")
        bands = filtering.filtered_bands_memmap(
            matrix.signals,
            root / "runs" / "benchmark" / ".cache" / dataset / config_digest(config) / "fbcsp",
        )
    result: dict[str, Any] = {
        "passed": False,
        "scope": "isolated runtime probe, not benchmark evidence",
        "probe_config": probe_config,
        "probe_config_sha256": config_digest(probe_config),
        "benchmark_config_sha256": config_digest(config),
        "artifact_snapshot_sha256": corpus["artifact_snapshot_sha256"],
        "source": asdict(capture_source(root)),
        "default_threadpools": threadpool_info(),
        "rows": [],
        "limitations": [
            f"{len(probe['subjects'])} existing folds only; parity here does not prove all folds.",
            "Historical timings used different machine loads, not a paired speed trial.",
            "Input/cache preparation time is excluded from fit/prediction timing in both cases.",
            "Call profiling, when enabled, adds overhead; times are not production measurements.",
        ],
    }
    with threadpool_limits(limits=probe["blas_threads"], user_api="blas"):
        result["limited_threadpools"] = threadpool_info()
        blas = [row for row in result["limited_threadpools"] if row["user_api"] == "blas"]
        if not blas or any(row["num_threads"] != probe["blas_threads"] for row in blas):
            raise RuntimeError("the requested BLAS thread limit was not applied")
        original_eigh = np.linalg.eigh
        for subject in probe["subjects"]:
            reference_path = (
                root
                / "runs"
                / "benchmark"
                / dataset
                / method
                / f"seed_{probe['seed']}"
                / f"{subject}.json"
            )
            reference = inspect_record(reference_path, expected_config_sha256=config_digest(config))
            if "reused_from_seed" in reference.metrics:
                raise ValueError("probe reference must contain a real fitted timing")
            print(f"Probing {subject} with {probe['blas_threads']} BLAS threads...", flush=True)
            eigh_calls = 0

            def limited_eigh(*arguments: Any, **keywords: Any) -> Any:
                nonlocal eigh_calls
                eigh_calls += 1
                with threadpool_limits(limits=eigh_threads, user_api="blas"):
                    observed = [p for p in threadpool_info() if p["user_api"] == "blas"]
                    if not observed or any(p["num_threads"] != eigh_threads for p in observed):
                        raise RuntimeError("the selective eigensolver thread limit was not applied")
                    return original_eigh(*arguments, **keywords)

            process_eigensolver = (
                ProcessEighProbe(workers=process_workers, chunk_matrices=64, minimum_memory_gib=4.0)
                if process_workers is not None
                else None
            )
            eigensolver_context: Any = (
                process_eigensolver
                if process_eigensolver is not None
                else (
                    patch("numpy.linalg.eigh", new=limited_eigh)
                    if eigh_threads is not None
                    else nullcontext()
                )
            )
            profiler = cProfile.Profile() if probe.get("profile_calls", False) else None
            if profiler is not None:
                profiler.enable()
            try:
                with eigensolver_context:
                    fold_result = run_fold(
                        matrix,
                        target_subject=subject,
                        method=method,
                        seed=probe["seed"],
                        shots_per_class=config["benchmark"]["shots_per_class"],
                        confidence_threshold=config["benchmark"]["confidence_threshold"],
                        torch_config=training,
                        prefiltered_fbcsp=bands,
                        certify_csp_rank=bool(probe.get("certify_csp_rank", False)),
                    )
            finally:
                if profiler is not None:
                    profiler.disable()
                    profiler.dump_stats(str(output.with_name(f"{subject}_profile.prof")))
                    pstats.Stats(profiler).strip_dirs().sort_stats("cumulative").print_stats(30)
            if eigh_threads is not None and not eigh_calls:
                raise RuntimeError("the selective eigensolver hook was never used")
            if process_eigensolver is not None and not process_eigensolver.stats["parallel_calls"]:
                raise RuntimeError("the isolated process eigensolver was never used")
            if process_workers is not None and (
                capture_source(root).source_sha256 != initial_source.source_sha256
            ):
                raise RuntimeError("process-probe source changed during qualification")
            measured = fold_result.scalar_metrics()
            names = (set(measured) | set(reference.metrics)) - {"fit_seconds", "prediction_seconds"}
            differences = {
                name: {"reference": reference.metrics.get(name), "probe": measured.get(name)}
                for name in sorted(names)
                if measured.get(name) != reference.metrics.get(name)
            }
            row = {
                "subject": subject,
                "reference_record": reference_path.relative_to(root).as_posix(),
                "reference_sha256": reference.sha256,
                "reference_metrics": reference.metrics,
                "probe_metrics": measured,
                "exact_non_timing_metrics_equal": not differences,
                "differences": differences,
                "rank_certificates": [asdict(item) for item in fold_result.csp_rank_certificates],
                "selective_eigh_calls": eigh_calls,
                "isolated_process_eigh": (
                    process_eigensolver.stats if process_eigensolver is not None else None
                ),
                "call_profile": (
                    output.with_name(f"{subject}_profile.prof").relative_to(root).as_posix()
                    if profiler is not None
                    else None
                ),
            }
            result["rows"].append(row)
            result["passed"] = len(result["rows"]) == len(probe["subjects"]) and all(
                item["exact_non_timing_metrics_equal"] for item in result["rows"]
            )
            output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps(row, sort_keys=True), flush=True)
            if differences:
                raise SystemExit("Exact metric parity failed; no benchmark settings were changed.")
    print(f"Probe complete: {output}", flush=True)


if __name__ == "__main__":
    main()
