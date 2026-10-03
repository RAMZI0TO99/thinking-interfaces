"""Plan or run an explicitly bounded, externally pinned Cho engineering session.

The default plan is read-only and imports no tensor runtime. Execution is
Windows-only and needs operator admission and explicit engineering probe
limits. Phase B analysis is separate and is not implemented by this command.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from evaluation.phase2_cho_execution import (  # noqa: E402
    METHODS,
    SEEDS,
    ExecutionLimits,
    execute_engineering_cases,
    load_execution_pins,
    select_cases,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--mode", choices=("plan", "execute", "analysis"), default="plan")
    result.add_argument("--dry-run", action="store_true", help="force the read-only plan mode")
    result.add_argument("--pins", required=True, type=Path, help="reviewed execution pin record")
    result.add_argument(
        "--pins-sha256", required=True, help="independently retained pin-file byte SHA"
    )
    result.add_argument("--method", choices=METHODS)
    result.add_argument("--subject")
    result.add_argument("--seed", type=int, choices=SEEDS)
    result.add_argument(
        "--case-limit", type=int, help="mandatory bound unless all three selectors supplied"
    )
    result.add_argument("--admission", type=Path, help="fresh persisted operator admission")
    result.add_argument("--receipt", type=Path, help="new write-once path under runs/phase2/sweeps")
    result.add_argument("--worker", default="cho-engineering")
    result.add_argument(
        "--execution-memory-limit-bytes",
        type=int,
        help="explicit initial engineering probe cap; maximum 6442450944",
    )
    result.add_argument("--attempt-seconds", type=float, help="whole-case bound; maximum 600")
    result.add_argument("--session-seconds", type=float, help="session bound; maximum 7200")
    result.add_argument(
        "--torch-threads", type=int, help="explicit runtime setting matching environment pin"
    )
    result.add_argument(
        "--attempt",
        choices=(1, 2),
        type=int,
        default=1,
        help="retry 2 requires a recorded failure of attempt 1",
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.mode == "analysis" and not arguments.dry_run:
        raise ValueError("analysis is not wired by this CLI; use the separately verified composer")
    cases = select_cases(
        method=arguments.method,
        subject=arguments.subject,
        seed=arguments.seed,
        case_limit=arguments.case_limit,
    )
    pins_path = arguments.pins.absolute()
    pins = load_execution_pins(ROOT, pins_path, arguments.pins_sha256)
    if arguments.dry_run or arguments.mode == "plan":
        print(
            json.dumps(
                {
                    "schema": "cho_engineering_read_only_plan_v1",
                    "source_sha256": pins["source_sha256"],
                    "pins_sha256": arguments.pins_sha256,
                    "cases": [asdict(case) for case in cases],
                    "case_count": len(cases),
                    "training_performed": False,
                    "compute_admitted": False,
                    "route_tensor_validation_deferred_to_supervised_child": True,
                    "runtime_environment_validation_deferred_to_execution": True,
                    "analysis_executed": False,
                    "scientific_claims_made": 0,
                    "scientific_freeze_ratified": False,
                    "gate_a_signed": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    required = (
        "admission",
        "receipt",
        "execution_memory_limit_bytes",
        "attempt_seconds",
        "session_seconds",
        "torch_threads",
    )
    if any(getattr(arguments, name) is None for name in required):
        raise ValueError(
            "execute requires admission, receipt and every explicit runtime/resource/time limit"
        )
    limits = ExecutionLimits(
        arguments.execution_memory_limit_bytes,
        arguments.attempt_seconds,
        arguments.session_seconds,
        arguments.torch_threads,
    )
    receipt = execute_engineering_cases(
        root=ROOT,
        pins_path=pins_path,
        pins_sha256=arguments.pins_sha256,
        admission_path=arguments.admission.absolute(),
        receipt_path=arguments.receipt.absolute(),
        cases=cases,
        limits=limits,
        worker=arguments.worker,
        attempt=arguments.attempt,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["completed_cases"] == receipt["planned_cases"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError) as error:
        print(f"Cho engineering execution refused: {error}", file=sys.stderr)
        raise SystemExit(2) from error
