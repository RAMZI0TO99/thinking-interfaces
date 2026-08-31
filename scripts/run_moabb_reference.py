"""Resume the complete, separate MOABB reference grid with one isolated process per fit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.config import config_digest
from core.provenance import capture_source
from core.run_record import RunRecord
from evaluation.moabb_reference_plan import ReferencePlan, ReferenceUnit, summarize_reference_scores
from evaluation.moabb_reference_records import validate_reference_record

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected an object: {path}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(output: Path, payload: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent, prefix=".reference-", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def execution_digest() -> str:
    # Code-only identity for the numerical execution path, separate from later documentation.
    return digest(ROOT / "scripts/smoke_moabb_reference.py")


def resolve_config(path: Path) -> tuple[dict[str, Any], ReferencePlan, dict[str, Any], Path]:
    config = tomllib.loads(path.read_text(encoding="utf-8"))
    plan = ReferencePlan.from_config(config)
    environment_path = (ROOT / config["paths"]["environment_config"]).resolve(strict=True)
    if not environment_path.is_relative_to(ROOT / "configs"):
        raise ValueError("reference environment configuration must stay inside configs")
    environment = tomllib.loads(environment_path.read_text(encoding="utf-8"))
    output = (
        ROOT
        / config["paths"]["output_directory"]
        / config_digest({"evaluation": config, "environment": environment})
    ).resolve()
    if not output.is_relative_to(ROOT / "runs/moabb_reference/evaluation"):
        raise ValueError("full reference outputs must remain separate from the main benchmark")
    return config, plan, environment, output


def resolved_unit(
    config: dict[str, Any], environment: dict[str, Any], unit: ReferenceUnit
) -> dict[str, Any]:
    return {"evaluation": config, "environment": environment, "unit": asdict(unit)}


def raw_hashes(config: dict[str, Any], unit: ReferenceUnit) -> dict[str, str]:
    directory = (ROOT / config["paths"]["raw_directory"]).resolve(strict=True)
    if not directory.is_relative_to(ROOT / "data/raw"):
        raise ValueError("reference raw inputs must stay inside project data")
    return {
        f"A{unit.subject:02d}{suffix}.mat": digest(directory / f"A{unit.subject:02d}{suffix}.mat")
        for suffix in ("T", "E")
    }


def require_smoke(config: dict[str, Any], environment: dict[str, Any]) -> None:
    path = (ROOT / config["paths"]["prerequisite_smoke_result"]).resolve(strict=True)
    if not path.is_relative_to(ROOT / "runs/moabb_reference/smoke"):
        raise ValueError("reference prerequisite must be a separate local smoke result")
    if digest(path) != config["paths"]["prerequisite_smoke_sha256"]:
        raise ValueError("prerequisite smoke artifact changed")
    smoke = read_json(path)
    if (
        smoke.get("smoke_passed") is not True
        or smoke.get("reference_reproduction_passed") is not False
        or smoke["config"]["environment"] != environment
        or smoke["config"]["smoke"]["epochs"] != 2
    ):
        raise ValueError("matching real-data reference smoke required")
    shared = (
        "batch_size",
        "learning_rate",
        "validation_split",
        "drop_rate",
        "patience",
        "learning_rate_factor",
        "fmin",
        "fmax",
        "resample_hz",
    )
    settings = {**config["training"], **config["preprocessing"]}
    if any(smoke["config"]["smoke"][key] != settings[key] for key in shared):
        raise ValueError("reference training/preprocessing differs from the qualified smoke")


def check_saved(
    path: Path, *, config: dict[str, Any], environment: dict[str, Any], unit: ReferenceUnit
) -> float:
    payload = read_json(path)
    receipt = Path(payload["environment_receipt"]).resolve(strict=True)
    if not receipt.is_relative_to(ROOT / "runs/moabb_reference"):
        raise ValueError("reference environment receipt is outside its scope")
    if digest(receipt) != payload["environment_receipt_sha256"]:
        raise ValueError("reference environment receipt changed")
    proof = read_json(receipt)
    if (
        proof["config"] != environment
        or proof["environment_verified"] is not True
        or proof["training_ready"] is not True
    ):
        raise ValueError("reference fit did not have a verified, resource-ready environment")
    return validate_reference_record(
        payload,
        unit=unit,
        resolved_config=resolved_unit(config, environment, unit),
        execution_sha256=execution_digest(),
        raw_hashes=raw_hashes(config, unit),
    )


def execute_unit(
    config_path: Path,
    config: dict[str, Any],
    plan: ReferencePlan,
    environment: dict[str, Any],
    output: Path,
    index: int,
) -> int:
    if not 0 <= index < len(plan.units):
        raise ValueError("unit selector is outside the configuration's declared grid")
    unit = plan.units[index]
    target = output / f"{unit.key}.json"
    if target.exists():
        check_saved(target, config=config, environment=environment, unit=unit)
        print(json.dumps({"reused": unit.key}), flush=True)
        return 0
    expected_prefix = (ROOT / environment["environment"]["directory"]).resolve()
    if Path(sys.prefix).resolve() != expected_prefix:
        raise ValueError("full reference fits require the isolated reference interpreter")
    require_smoke(config, environment)
    preflight = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.check_moabb_reference_environment",
            "--config",
            str(ROOT / config["paths"]["environment_config"]),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=45,
    )
    receipt_path = Path(json.loads(preflight.stdout)["report"])
    receipt = read_json(receipt_path)
    if not receipt["training_ready"]:
        print(json.dumps({"deferred": unit.key, "resources": receipt["resources"]}), flush=True)
        return 2
    source = capture_source(ROOT)
    if source.git_dirty is not False:
        raise ValueError("commit reference source/configuration changes before full training")
    target.parent.mkdir(parents=True, exist_ok=True)
    lock = target.with_suffix(".lock")
    # A stale lock is preserved for explicit process-identity review, never auto-deleted.
    with lock.open("x", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "unit": unit.key, "config": str(config_path)}, stream)
    try:
        if target.exists():
            raise ValueError("reference result appeared concurrently; preserve it")
        before_raw = raw_hashes(config, unit)
        execution = execution_digest()
        settings = {
            **config["training"],
            **config["preprocessing"],
            **asdict(unit),
            "fold_count": plan.fold_count,
            "split_seed": plan.split_seed,
            "raw_directory": config["paths"]["raw_directory"],
        }
        from scripts.smoke_moabb_reference import run_reference_fold

        result = run_reference_fold(settings, receipt)
        if (
            capture_source(ROOT).source_sha256 != source.source_sha256
            or raw_hashes(config, unit) != before_raw
            or execution_digest() != execution
        ):
            raise RuntimeError("reference source or raw inputs changed during fit")
        record = RunRecord.create(
            config=resolved_unit(config, environment, unit),
            seed=unit.model_seed,
            git_commit=source.git_commit,
            source_sha256=source.source_sha256,
            git_dirty=source.git_dirty,
            dataset="bci_iv_2a",
            fold=unit.key,
            metrics={
                name: result[name] for name in ("roc_auc", "fit_seconds", "prediction_seconds")
            },
        )
        payload = {
            "unit": asdict(unit),
            "record": asdict(record),
            "result": result,
            "execution_sha256": execution,
            "environment_receipt": str(receipt_path),
            "environment_receipt_sha256": digest(receipt_path),
        }
        validate_reference_record(
            payload,
            unit=unit,
            resolved_config=resolved_unit(config, environment, unit),
            execution_sha256=execution,
            raw_hashes=before_raw,
        )
        atomic_json(target, payload)
        print(
            json.dumps(
                {
                    "saved": unit.key,
                    "roc_auc": result["roc_auc"],
                    "epochs": result["epochs_completed"],
                }
            ),
            flush=True,
        )
    finally:
        lock.unlink(missing_ok=True)
    return 0


def audit(
    config: dict[str, Any], plan: ReferencePlan, environment: dict[str, Any], output: Path
) -> dict[str, Any]:
    observations = []
    files, invalid, missing = {}, {}, []
    expected = {f"{unit.key}.json" for unit in plan.units}
    for unit in plan.units:
        path = output / f"{unit.key}.json"
        if not path.exists():
            missing.append(unit.key)
            continue
        try:
            score = check_saved(path, config=config, environment=environment, unit=unit)
            observations.append((unit, score))
            files[f"{unit.key}.json"] = digest(path)
        except (ValueError, KeyError, TypeError, OSError) as error:
            invalid[unit.key] = str(error)
    unexpected = sorted(
        path.relative_to(output).as_posix()
        for path in output.rglob("*.json")
        if path.relative_to(output).as_posix() not in expected | {"integrity.json"}
    )
    locks = sorted(path.relative_to(output).as_posix() for path in output.rglob("*.lock"))
    complete = not missing and not invalid and not unexpected and not locks
    report = {
        "complete": complete,
        "expected_fits": len(plan.units),
        "valid_fits": len(observations),
        "missing_units": missing,
        "invalid_units": invalid,
        "unexpected_files": unexpected,
        "pending_locks": locks,
        "record_files": files,
        "record_snapshot_sha256": config_digest(files),
        "scientific_gate_approved": False,
        "acceptance_tolerance_adopted": False,
        "scope": "Record identity/split/metric checks; not independent raw-epoch reproduction.",
    }
    if complete:
        report["summary"] = summarize_reference_scores(plan, observations)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/moabb_reference_evaluation.toml"
    )
    parser.add_argument("--unit-index", type=int, help="Internal selector into the committed grid")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.check_only and args.unit_index is not None:
        raise ValueError("choose either a grid audit or a single declared unit")
    config, plan, environment, output = resolve_config(args.config)
    if args.unit_index is not None:
        return execute_unit(args.config, config, plan, environment, output, args.unit_index)
    report = audit(config, plan, environment, output)
    atomic_json(output / "integrity.json", report)
    if args.check_only or report["complete"]:
        print(
            json.dumps(
                {
                    key: report[key]
                    for key in ("complete", "expected_fits", "valid_fits", "invalid_units")
                }
            ),
            flush=True,
        )
        return 0 if report["complete"] else 2
    if report["invalid_units"] or report["unexpected_files"] or report["pending_locks"]:
        raise ValueError("existing reference evidence needs review; no records overwritten")
    require_smoke(config, environment)
    python = ROOT / environment["environment"]["directory"] / "Scripts/python.exe"
    logs = output / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    for index, unit in enumerate(plan.units):
        target = output / f"{unit.key}.json"
        if target.exists():
            check_saved(target, config=config, environment=environment, unit=unit)
            continue
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        stem = f"{stamp}_{unit.key.replace('/', '_')}"
        print(
            json.dumps(
                {"starting": unit.key, "grid_position": index + 1, "expected_fits": len(plan.units)}
            ),
            flush=True,
        )
        with (
            (logs / f"{stem}.stdout.log").open("x", encoding="utf-8") as stdout,
            (logs / f"{stem}.stderr.log").open("x", encoding="utf-8") as stderr,
        ):
            child = subprocess.run(
                [
                    str(python),
                    "-m",
                    "scripts.run_moabb_reference",
                    "--config",
                    str(args.config.resolve()),
                    "--unit-index",
                    str(index),
                ],
                cwd=ROOT,
                stdout=stdout,
                stderr=stderr,
                check=False,
            )
        if child.returncode:
            print(
                json.dumps(
                    {
                        "stopped_at": unit.key,
                        "exit_code": child.returncode,
                        "stdout": str(logs / f"{stem}.stdout.log"),
                        "stderr": str(logs / f"{stem}.stderr.log"),
                    }
                ),
                flush=True,
            )
            return child.returncode
        check_saved(target, config=config, environment=environment, unit=unit)
    report = audit(config, plan, environment, output)
    atomic_json(output / "integrity.json", report)
    print(
        json.dumps(
            {
                "complete": report["complete"],
                "valid_fits": report["valid_fits"],
                "scientific_gate_approved": False,
            }
        ),
        flush=True,
    )
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
