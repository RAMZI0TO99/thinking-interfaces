"""Private Cho whole-case child; only a pinned supervised contract admits work."""

from __future__ import annotations

import argparse
import contextlib
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from evaluation.phase2_cho_execution import (  # noqa: E402
    fresh_record,
    run_cho_execution_child,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--contract-sha256", required=True)
    arguments = parser.parse_args()
    contract_path = arguments.contract.absolute()
    if not contract_path.is_relative_to(ROOT / "runs/phase2/sweeps"):
        raise ValueError("child contract must belong to a bounded execution session")
    log_path = contract_path.parent / "child.log"
    with (
        log_path.open("x", encoding="utf-8", buffering=1) as log,
        contextlib.redirect_stdout(log),
        contextlib.redirect_stderr(log),
    ):
        try:
            run_cho_execution_child(ROOT, contract_path, arguments.contract_sha256)
        except Exception as error:  # noqa: BLE001 - preserve refusal without success proposal
            traceback.print_exc()
            fresh_record(
                contract_path.parent / "child_failure.json",
                {
                    "schema": "cho_engineering_child_failure_v1",
                    "contract_sha256": arguments.contract_sha256,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "scientific_claims_made": 0,
                },
            )
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
