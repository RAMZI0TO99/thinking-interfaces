"""Pure boundaries for the explicitly staged two-root source-artifact bridge.

This checks requested metadata only.  It neither authenticates on-disk origin
proofs nor qualifies publication, restoration, the original single-root factory
or scientific work.  The guarded bridge and independent metadata verifier own
those separate checks.  There is no filesystem or project import here.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any


SCHEMA = "cho51_linear_staged_publication_contract_v1"
ARCHITECTURE_ROOT = r"D:\Aenv\pro3"
RUN_ROOT = ARCHITECTURE_ROOT + r"\runs\coordination\cho51_linear_publication_20261015_v1"
PUBLICATION_OUTPUT = RUN_ROOT + r"\publication_001"
DETACHED_OUTPUT = RUN_ROOT + r"\restoration_001"
EVIDENCE_ROOT = PUBLICATION_OUTPUT + r"\project"
ORIGIN_PATH = RUN_ROOT + r"\origin-contract.json"
ORIGIN_FIXTURE_ROOT = ARCHITECTURE_ROOT + (
    r"\runs\coordination\cho51_linear_lineage_20261015_v2\validation_001\fixture"
)
CHAIN_ROOT = ARCHITECTURE_ROOT + r"\runs\coordination\cho51_linear_chain_20261015_v1"
FINAL_OUTPUT = CHAIN_ROOT + r"\fragments\fragment_007"
CANONICAL_SOURCE_SHA256 = "3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529"
EVIDENCE_SOURCE_SHA256 = "9c2e6ad444c44309f9d4becda2909fba0d2fe315f047560f9adbce56397c9299"
ORDINARY_JSON_BYTES = 8 * 1024**2
COMPLETE_EVIDENCE_JSON_BYTES = 32 * 1024**2
CHECKPOINT_BYTES = 64 * 1024**2


def _canonical(value: Any) -> str:
    def check(item: Any) -> None:
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                raise ValueError("plain JSON object keys must be strings")
            for member in item.values():
                check(member)
        elif type(item) is list:
            for member in item:
                check(member)
        elif item is None or type(item) in (str, bool, int):
            return
        elif type(item) is float and math.isfinite(item):
            return
        else:
            raise ValueError("only finite plain JSON values are accepted")
    check(value)
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _same(value: Any, expected: Any, label: str) -> None:
    if _canonical(value) != _canonical(expected):
        raise ValueError(label + " differs from the fixed staged contract")


def _artifact(path: str, sha256: str, size: int) -> dict[str, Any]:
    return {"path": path, "file_sha256": sha256, "size_bytes": size}


def _source_artifacts() -> dict[str, dict[str, Any]]:
    return {
        "checkpoint": _artifact(FINAL_OUTPUT + r"\selected-source.safetensors",
            "3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048", 23294624),
        "evidence": _artifact(FINAL_OUTPUT + r"\selection-evidence.json",
            "e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3", 23087023),
        "state_schema": _artifact(FINAL_OUTPUT + r"\selected-state-schema.json",
            "d9a276bb86322512fa87f90e06351c6f8552d63490b25f85968ebcbe1cbc68b4", 20594),
        "method_config": _artifact(CHAIN_ROOT + r"\method-config.json",
            "37b07825274a45d0703bba56387aa75c42e612d84066996d4a3a8bf44cdd42af", 886),
        "final_review": _artifact(CHAIN_ROOT + r"\final-review.json",
            "cc1917e786e81092443d6a90c2be9708ea5ef034deb3bcb43572b23e6a887b8a", 186353),
        "pins": _artifact(CHAIN_ROOT + r"\pins.json",
            "1e3776fd84c22fdba9d36c97113ca1fb90ec5912018cfdcdd0c4cfcaa264be2e", 235853),
        "chain7": _artifact(CHAIN_ROOT + r"\chains\chain_007.json",
            "20375fcf55818d9f2ec4f57a29f2ce6490dff35029896189e56ca251d306c1d7", 14616),
    }


def _five_tomls() -> dict[str, str]:
    return {
        "configs/base.toml": "02c8e3011abfcafe170f791ec688c791b2187d8e547dd3b2655bae2b5eedf2c4",
        "configs/benchmark.toml": "2dba370f37039cbee73726c407b7377ad9933385a1acab30f21cceca7bd369b5",
        "configs/phase2/cho_profile_b_60hz.toml": "6a3d5b9afca7bc0b82532276df1ef8f0a14db85da0eb609b5176ac967d04afb3",
        "configs/phase2/protocol.toml": "d8b56cdb28c7cbf3999e9fc65f089535930bff23373ddf46b903695cf095fa95",
        "configs/phase2/selection_ceiling.toml": "a7db3ba233c71ff73c5599baa2f48ffb7616deb1c239b7bbfc41b6ac8e466548",
    }


def validate_stage_contract(contract: dict[str, Any]) -> None:
    """Fail closed on root-role, immutable-source, scope or authority substitution.

    ``origin_file_sha256`` is an external physical pin: its syntax is checked
    here, and the caller must authenticate the actual independently pinned file.
    The seven accepted historical source pins are fixed, rather than supplied
    as their own authority.  All current numerical fitting is forbidden.
    """
    _canonical(contract)
    fixed = {
        "schema": SCHEMA, "architecture_root": ARCHITECTURE_ROOT,
        "evidence_root": EVIDENCE_ROOT, "origin_fixture_root": ORIGIN_FIXTURE_ROOT,
        "publication_output": PUBLICATION_OUTPUT, "detached_output": DETACHED_OUTPUT,
        "origin_path": ORIGIN_PATH,
        "source_artifacts": _source_artifacts(),
        "case": {"dataset": "cho2017", "target_subject": "subject_02", "method": "labram_linear",
                 "shots_per_class": 5, "model_seed": 11, "repetition": 1},
        "selected_candidate": "lr_1e-3", "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "evidence_source_sha256": EVIDENCE_SOURCE_SHA256,
        "five_tomls": _five_tomls(), "historical_gradient_updates": 5253,
        "current_gradient_updates": 0, "complete_folds": 102,
        "source_policy": "two_root_staged_bridge",
        "public_single_root_factory_qualified": False,
        "publication_stage_qualified": False, "detached_stage_qualified": False,
        "scientific_admission": False, "original_case_attempts": 0,
        "limits": {"ordinary_json_bytes": ORDINARY_JSON_BYTES,
                   "complete_evidence_json_bytes": COMPLETE_EVIDENCE_JSON_BYTES,
                   "checkpoint_bytes": CHECKPOINT_BYTES},
    }
    if type(contract) is not dict or set(contract) != set(fixed) | {"origin_file_sha256"}:
        raise ValueError("the staged contract requires its exact plain JSON object fields")
    value = contract["origin_file_sha256"]
    if type(value) is not str or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        raise ValueError("origin_file_sha256 must be an external lowercase physical SHA-256 pin")
    _same({key: contract[key] for key in fixed}, fixed, "staged publication and restoration scope")
