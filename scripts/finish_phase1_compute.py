"""Alternate bounded benchmark batches and isolated reference fits, without blind retries."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from core.provenance import capture_source
from evaluation.benchmark_audit import audit_benchmark
from evaluation.reference_environment import resource_gate, startup_runtime
from evaluation.source_bound_controls import verify_current_controls
from scripts.run_moabb_reference import atomic_json, audit, resolve_config

BATCH_SIZE = 20


def inspect_benchmark(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    gate = cast(dict[str, Any], load_toml(root / "configs/gate_b.toml"))
    subjects = {}
    for dataset in config["benchmark"]["datasets"]:
        directory = root / config["datasets"][dataset]["artifact_directory"]
        subjects[dataset] = tuple(path.stem for path in sorted(directory.glob("subject_*.npz")))
        if len(subjects[dataset]) != gate["subjects"][dataset]:
            raise ValueError(f"incomplete processed subject inventory: {dataset}")
    return audit_benchmark(
        root / "runs/benchmark",
        datasets_subjects=subjects,
        methods=config["benchmark"]["methods"],
        seeds=config["benchmark"]["seeds"],
        expected_config_sha256=config_digest(config),
    )


def require_integrity(report: dict[str, Any], *, reference: bool = False) -> None:
    fields = (
        ("invalid_units", "unexpected_files", "pending_locks")
        if reference
        else ("invalid_records", "unexpected_records")
    )
    if any(report[field] for field in fields):
        raise ValueError("existing evidence requires review; no automatic retry or overwrite")


def require_extension(
    previous: dict[str, str],
    current: dict[str, str],
    *,
    maximum: int,
    require_progress: bool = True,
) -> None:
    if any(current.get(name) != digest for name, digest in previous.items()):
        raise ValueError("a previously saved record changed or disappeared")
    added = len(current) - len(previous)
    if added > maximum or (require_progress and added < 1):
        raise ValueError("batch progress differs from the requested bound")


def next_batch(report: dict[str, Any], config: dict[str, Any]) -> tuple[str, str] | None:
    pending = {tuple(path.split("/")[:2]) for path in report["missing_records"]}
    for dataset in config["benchmark"]["datasets"]:
        for method in config["benchmark"]["methods"]:
            if (dataset, method) in pending:
                return dataset, method
    if pending:
        raise ValueError("pending records are outside the configured benchmark")
    return None


def resources(root: Path, runtime: dict[str, Any]) -> dict[str, object]:
    return resource_gate(
        runtime,
        free_memory_gib=importlib.import_module("psutil").virtual_memory().available / 1024**3,
        free_disk_gib=shutil.disk_usage(root).free / 1024**3,
    )


def await_resources(root: Path, runtime: dict[str, Any], *, timeout: float = 300.0) -> bool:
    deadline = time.monotonic() + timeout
    announced = False
    while True:
        state = resources(root, runtime)
        if state["ready"]:
            print(json.dumps({"resource_ready": state}), flush=True)
            return True
        if not announced:
            print(json.dumps({"waiting_for_resources": state}), flush=True)
            announced = True
        if time.monotonic() >= deadline:
            print(
                json.dumps({"deferred": "startup resource guard", "resources": state}), flush=True
            )
            return False
        time.sleep(min(5.0, max(0.0, deadline - time.monotonic())))


@contextmanager
def exclusive_supervisor(root: Path) -> Iterator[None]:
    lock = root / "runs/phase1_compute.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    identity = json.dumps({"pid": os.getpid(), "started_utc": datetime.now(UTC).isoformat()})
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(identity)
    try:
        yield
    finally:
        # A stale/foreign lock is never removed by a subsequent launch.
        if lock.read_text(encoding="utf-8") != identity:
            raise RuntimeError("supervisor lock ownership changed; preserve it for review")
        lock.unlink()


def run_logged(root: Path, arguments: list[str], label: str) -> int:
    directory = root / "runs/compute_logs"
    directory.mkdir(parents=True, exist_ok=True)
    stem = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "." + label
    stdout, stderr = directory / f"{stem}.stdout.log", directory / f"{stem}.stderr.log"
    print(
        json.dumps(
            {
                "starting": label,
                "arguments": arguments,
                "stdout": str(stdout),
                "stderr": str(stderr),
            }
        ),
        flush=True,
    )
    with stdout.open("x", encoding="utf-8") as out, stderr.open("x", encoding="utf-8") as err:
        result = subprocess.run(arguments, cwd=root, stdout=out, stderr=err, check=False)
    print(json.dumps({"finished": label, "exit_code": result.returncode}), flush=True)
    return result.returncode


def require_source(root: Path, expected: str) -> None:
    observed = capture_source(root)
    if observed.git_dirty is not False or observed.source_sha256 != expected:
        raise RuntimeError("source changed between/during batches; stop before the next fit")


def run_grids(
    root: Path, *, reference_startup_minimum_free_memory_gib: float | None = None
) -> int:
    source = capture_source(root)
    if source.git_dirty is not False:
        raise ValueError("commit source changes before starting unattended compute")
    config = load_toml(root / "configs/benchmark.toml")
    reference_path = root / "configs/moabb_reference_evaluation.toml"
    ref_config, plan, environment, output = resolve_config(reference_path)
    reference_runtime = startup_runtime(
        environment["runtime"], reference_startup_minimum_free_memory_gib
    )
    reference_python = root / environment["environment"]["directory"] / "Scripts/python.exe"
    main_report = inspect_benchmark(root, config)
    reference = audit(ref_config, plan, environment, output)
    require_integrity(main_report)
    require_integrity(reference, reference=True)
    atomic_json(root / "runs/benchmark_integrity_audit.json", main_report)
    atomic_json(output / "integrity.json", reference)
    while not main_report["complete"] or not reference["complete"]:
        for kind in ("benchmark", "reference"):
            if (main_report if kind == "benchmark" else reference)["complete"]:
                continue
            if not await_resources(root, reference_runtime):
                return 2
            require_source(root, source.source_sha256)
            if kind == "benchmark":
                selected = next_batch(main_report, config)
                if selected is None:
                    raise ValueError("incomplete benchmark has no scheduled work")
                dataset, method = selected
                code = run_logged(
                    root,
                    [
                        sys.executable,
                        "-u",
                        "scripts/run_benchmark.py",
                        "--dataset",
                        dataset,
                        "--method",
                        method,
                        "--max-new-runs",
                        str(BATCH_SIZE),
                    ],
                    f"{dataset}_{method}_bounded",
                )
                updated = inspect_benchmark(root, config)
                require_integrity(updated)
                require_extension(
                    main_report["record_files"],
                    updated["record_files"],
                    maximum=BATCH_SIZE,
                    require_progress=code == 0,
                )
                main_report = updated
            else:
                index = next(
                    i for i, unit in enumerate(plan.units) if unit.key in reference["missing_units"]
                )
                code = run_logged(
                    root,
                    [
                        str(reference_python),
                        "-u",
                        "-m",
                        "scripts.run_moabb_reference",
                        "--config",
                        str(reference_path),
                        "--unit-index",
                        str(index),
                        *(
                            [
                                "--startup-minimum-free-memory-gib",
                                str(reference_startup_minimum_free_memory_gib),
                            ]
                            if reference_startup_minimum_free_memory_gib is not None
                            else []
                        ),
                    ],
                    "reference_unit",
                )
                updated = audit(ref_config, plan, environment, output)
                require_integrity(updated, reference=True)
                require_extension(
                    reference["record_files"],
                    updated["record_files"],
                    maximum=1,
                    require_progress=code == 0,
                )
                reference = updated
            require_source(root, source.source_sha256)
            atomic_json(root / "runs/benchmark_integrity_audit.json", main_report)
            atomic_json(output / "integrity.json", reference)
            print(
                json.dumps(
                    {
                        "benchmark_valid": main_report["valid_records"],
                        "reference_valid": reference["valid_fits"],
                        "scientific_gate_approved": False,
                    }
                ),
                flush=True,
            )
            if code:
                # Resource deferrals and native failures both require a fresh reviewed launch.
                # Never repeat a failed fit in a hidden retry loop.
                return code
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reference-startup-minimum-free-memory-gib",
        type=float,
        help="Operational reference admission threshold; preserves the 4-GiB emergency stop",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    with exclusive_supervisor(root):
        if verify_current_controls(root).get("passed") is not True:
            raise ValueError("current-source controls must pass before unattended compute")
        for script in (
            "run_support_adaptation.py",
            "audit_support_adaptation.py",
            "audit_subject_falsification.py",
        ):
            code = run_logged(
                root, [sys.executable, "scripts/" + script], script.removesuffix(".py")
            )
            if code:
                return code
        code = run_grids(
            root,
            reference_startup_minimum_free_memory_gib=(
                args.reference_startup_minimum_free_memory_gib
            ),
        )
        if code:
            return code
        subprocess.run([sys.executable, "scripts/audit_benchmark.py"], cwd=root, check=True)
    print("Both compute grids audited complete; scientific review and sign-off remain.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
