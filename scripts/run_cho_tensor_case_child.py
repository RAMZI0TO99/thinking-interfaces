"""Verify exactly one Cho selected-source tensor state in an owned child.

Engineering entrypoint for the isolated per-case analysis sweep: reads one
pinned input JSON, calls ``verify_cho_selected_source_state`` unchanged (so
its RAM checks and bounded reads still apply), and publishes a digest-only
witness through an exclusive-create write. It never releases an adapter,
never reads score rows, and performs no training.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

INPUT_SCHEMA = "cho_tensor_case_child_input_v1"
WITNESS_SCHEMA = "cho_tensor_case_child_witness_v1"
_PLAN_FIELDS = (
    "dataset", "target_subject", "method", "shots_per_class", "model_seed", "repetition",
)


def _load_input(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text("utf-8"))
    if (
        not isinstance(payload, dict)
        or payload.get("schema") != INPUT_SCHEMA
        or not isinstance(payload.get("case_id"), str)
        or not isinstance(payload.get("plan"), dict)
        or any(field not in payload["plan"] for field in _PLAN_FIELDS)
    ):
        raise ValueError("tensor case child input differs from the pinned schema")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--witness", required=True)
    arguments = parser.parse_args()
    input_path = Path(arguments.input)
    witness_path = Path(arguments.witness)
    if witness_path.exists():
        raise RuntimeError("tensor case witness already exists")
    payload = _load_input(input_path)
    # The production executor always passes the reviewed project root; the
    # optional input field exists so the supervised-child tests can verify a
    # synthetic publication tree.
    root = Path(payload["root"]) if payload.get("root") is not None else ROOT

    from evaluation.phase2_cho_source_restore import verify_cho_selected_source_state
    from evaluation.phase2_runner import CasePlan

    state = verify_cho_selected_source_state(
        root=root,
        plan=CasePlan(**payload["plan"]),
        method_config=payload["method_config"],
        expected_method_config_sha256=payload["expected_method_config_sha256"],
        selected_candidate=payload["selected_candidate"],
        manifest_sha256=payload["manifest_sha256"],
        evidence_sha256=payload["evidence_sha256"],
        protocol_config=payload["protocol_config"],
        expected_model_recipe_sha256=payload["expected_model_recipe_sha256"],
        expected_model_state_sha256=payload["expected_model_state_sha256"],
    )
    witness = {
        "schema": WITNESS_SCHEMA,
        "case_id": payload["case_id"],
        "manifest_sha256": state.manifest_sha256,
        "evidence_sha256": state.evidence_sha256,
        "selected_candidate": state.selected_candidate,
        "model_recipe_sha256": state.model_recipe_sha256,
        "model_state_sha256": state.model_state_sha256,
        "weights_sha256": state.weights_sha256,
        "training_performed": False,
    }
    with witness_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(witness, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"case_id": payload["case_id"], "verified": True}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
