"""Isolated CPU-thread probe; never rewrites or contributes benchmark records."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from threadpoolctl import threadpool_info, threadpool_limits  # type: ignore[import-untyped]

from core.config import config_digest, load_toml
from core.provenance import capture_source
from evaluation.baselines import FilterBankCSP, TorchTrainingConfig
from evaluation.benchmark import _decoder, load_dataset_matrix, run_fold
from evaluation.benchmark_audit import inspect_record
from evaluation.corpus_duplicates import verify_corpus_snapshot


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
    if probe["method"] != "fbcsp" or probe["require_exact_non_timing_metrics"] is not True:
        raise ValueError("this probe only verifies exact-metric FBCSP runtime parity")
    if type(probe["blas_threads"]) is not int or probe["blas_threads"] < 1:
        raise ValueError("a positive CPU BLAS thread bound is required")
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
            "Two existing folds only; matching metrics do not prove every fold is identical.",
            "Historical timings used different machine loads, not a paired speed trial.",
            "Input/cache preparation time is excluded from fit/prediction timing in both cases.",
        ],
    }
    with threadpool_limits(limits=probe["blas_threads"], user_api="blas"):
        result["limited_threadpools"] = threadpool_info()
        blas = [row for row in result["limited_threadpools"] if row["user_api"] == "blas"]
        if not blas or any(row["num_threads"] != probe["blas_threads"] for row in blas):
            raise RuntimeError("the requested BLAS thread limit was not applied")
        for subject in probe["subjects"]:
            reference_path = (
                root
                / "runs"
                / "benchmark"
                / dataset
                / "fbcsp"
                / f"seed_{probe['seed']}"
                / f"{subject}.json"
            )
            reference = inspect_record(reference_path, expected_config_sha256=config_digest(config))
            if "reused_from_seed" in reference.metrics:
                raise ValueError("probe reference must contain a real fitted timing")
            print(f"Probing {subject} with {probe['blas_threads']} BLAS threads...", flush=True)
            fold_result = run_fold(
                matrix,
                target_subject=subject,
                method="fbcsp",
                seed=probe["seed"],
                shots_per_class=config["benchmark"]["shots_per_class"],
                confidence_threshold=config["benchmark"]["confidence_threshold"],
                torch_config=training,
                prefiltered_fbcsp=bands,
                certify_csp_rank=bool(probe.get("certify_csp_rank", False)),
            )
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
