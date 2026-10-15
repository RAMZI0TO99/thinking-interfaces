"""Deterministic metadata planning for six remaining-fold chunks and one final fit.

No I/O, model import, numerical execution or reuse admission occurs here.  A
chain's leaf digests must be authenticated separately by the origin verifier.
The unchanged continuation collector remains the validator for actual raw folds.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

from docs.phase2.cho51_linear_continuation_v1 import contract as PARTIAL


CHAIN_SCHEMA = "cho51_linear_chain_metadata_v1"
REQUEST_SCHEMA = "cho51_linear_chain_request_v1"
RUN_RELATIVE = "runs/coordination/cho51_linear_chain_20261015_v1"
BASELINE_SHA256 = "53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8"
TEMPLATE_SHA256 = "90a9d34ecba2aa96a942f7bd70724f63c2071042141935dbbcd78e0b373b89a7"
CONTRACT_SHA256 = "8397d34ee0a2280b406071e045988f98b1b73ce21fcecc0b9834518cd21993b1"
CANONICAL_SOURCE_SHA256 = "3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529"
FULL_ROSTER = PARTIAL.FULL_ROSTER
BASE_ROSTER = tuple(pair for pair in FULL_ROSTER if pair[1] in (
    "subject_01", "subject_03", "subject_04", "subject_05", "subject_06",
))
REMAINING_ROSTER = tuple(pair for pair in FULL_ROSTER if pair not in BASE_ROSTER)
CHUNK_SIZES = (16, 16, 16, 16, 16, 12)
LIMITS = {
    "seconds": 600, "process_mib": 4096, "job_mib": 5120,
    "startup_ram_gib": 10, "active_ram_gib": 4, "disk_gib": 20,
    "torch_threads": 1, "torch_interop_threads": 1, "gpu_hidden": True,
}
CHAIN_KEYS = {
    "schema", "root_origin_sha256", "pins_sha256", "chain_index", "leaves",
    "accepted_pairs", "head_sha256", "complete",
}
DESCRIPTOR_KEYS = {
    "index", "path", "sha256", "request_sha256", "parent_head_sha256", "mode", "pairs",
    "accepted_folds_before", "accepted_folds_after",
}
REQUEST_KEYS = {
    "schema", "index", "mode", "pairs", "prior_folds", "parent_head_sha256", "chain_sha256",
    "pins_sha256", "root_origin_sha256", "output_relative", "chain_relative", "limits",
    "required_full_gradient_updates", "canonical_source_sha256", "engineering_only",
    "scientific_admission", "original_case_attempts",
}


def _canonical(value: Any) -> str:
    def check(item: Any) -> None:
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                raise ValueError("JSON object keys must be strings")
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
    return json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True)


def logical(value: Any) -> str:
    """SHA-256 of canonical UTF-8 JSON without a trailing newline."""
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _physical_request_sha256(request: dict[str, Any]) -> str:
    # Reviewed writers publish exactly canonical JSON followed by one newline.
    return hashlib.sha256((_canonical(request) + "\n").encode("utf-8")).hexdigest()


def _same(value: Any, expected: Any, label: str) -> None:
    if _canonical(value) != _canonical(expected):
        raise ValueError(label + " differs from the fixed chain contract")


def _object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(label + " requires its exact JSON object fields")
    return value


def _digest(value: Any, label: str) -> str:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(label + " must be a lowercase SHA-256 digest")
    return value


def _index(value: Any, *, minimum: int, maximum: int, label: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(label + " must be an explicit bounded integer")
    return value


def _rows(pairs: tuple[tuple[str, str], ...]) -> list[dict[str, str]]:
    return [{"candidate": name, "validation_subject": subject} for name, subject in pairs]


def _chunk(index: int) -> tuple[tuple[str, str], ...]:
    if index == 7:
        return ()
    return REMAINING_ROSTER[(index - 1) * 16: index * 16]


def _accepted(index: int) -> list[dict[str, str]]:
    permitted = set(BASE_ROSTER + REMAINING_ROSTER[:min(index, 6) * 16])
    return _rows(tuple(pair for pair in FULL_ROSTER if pair in permitted))


def _request_for_chain(chain: dict[str, Any]) -> dict[str, Any]:
    index = chain["chain_index"] + 1
    if index > 7:
        raise ValueError("the seven-request chain is exhausted")
    return {
        "schema": REQUEST_SCHEMA, "index": index,
        "mode": "folds" if index <= 6 else "final", "pairs": _rows(_chunk(index)),
        "prior_folds": len(_accepted(index - 1)), "parent_head_sha256": chain["head_sha256"],
        "chain_sha256": logical(chain), "pins_sha256": chain["pins_sha256"],
        "root_origin_sha256": chain["root_origin_sha256"],
        "output_relative": f"fragments/fragment_{index:03d}",
        "chain_relative": f"chains/chain_{index - 1:03d}.json",
        "limits": dict(LIMITS), "required_full_gradient_updates": 5253,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "engineering_only": True, "scientific_admission": False, "original_case_attempts": 0,
    }


def validate_chain_metadata(chain: dict[str, Any]) -> None:
    """Validate deterministic metadata, without authenticating any leaf file."""
    _canonical(chain)
    _object(chain, CHAIN_KEYS, "chain")
    _same(chain["schema"], CHAIN_SCHEMA, "chain schema")
    root_sha = _digest(chain["root_origin_sha256"], "root origin")
    _digest(chain["pins_sha256"], "fixed pins")
    _digest(chain["head_sha256"], "chain head")
    index = _index(chain["chain_index"], minimum=0, maximum=7, label="chain index")
    _same(chain["complete"], False, "metadata completion boundary")
    leaves = chain["leaves"]
    if type(leaves) is not list or len(leaves) != index:
        raise ValueError("chain index must equal the number of contiguous leaf descriptors")
    prior_head = root_sha
    seen_leaves: set[str] = set()
    seen_requests: set[str] = set()
    for expected_index, value in enumerate(leaves, 1):
        descriptor = _object(value, DESCRIPTOR_KEYS, "leaf descriptor")
        _index(descriptor["index"], minimum=1, maximum=7, label="leaf index")
        _same(descriptor["index"], expected_index, "contiguous leaf index")
        leaf_sha = _digest(descriptor["sha256"], "leaf physical SHA-256")
        request_sha = _digest(descriptor["request_sha256"], "request physical SHA-256")
        _digest(descriptor["parent_head_sha256"], "leaf parent head")
        if leaf_sha == root_sha or leaf_sha in seen_leaves or request_sha in seen_requests:
            raise ValueError("root, request or leaf digest replay is forbidden")
        prefix = {
            "schema": CHAIN_SCHEMA, "root_origin_sha256": root_sha,
            "pins_sha256": chain["pins_sha256"], "chain_index": expected_index - 1,
            "leaves": leaves[:expected_index - 1], "accepted_pairs": _accepted(expected_index - 1),
            "head_sha256": prior_head, "complete": False,
        }
        request = _request_for_chain(prefix)
        _same(descriptor["path"], RUN_RELATIVE + f"/fragments/fragment_{expected_index:03d}/leaf.json",
              "root-relative leaf path")
        _same(descriptor["parent_head_sha256"], prior_head, "leaf parent")
        _same(descriptor["mode"], request["mode"], "leaf mode")
        _same(descriptor["pairs"], request["pairs"], "canonical next leaf pairs")
        _same(descriptor["accepted_folds_before"], request["prior_folds"], "prior coverage")
        _same(descriptor["accepted_folds_after"], len(_accepted(expected_index)), "result coverage")
        _same(request_sha, _physical_request_sha256(request), "historical request physical SHA-256")
        seen_leaves.add(leaf_sha)
        seen_requests.add(request_sha)
        prior_head = leaf_sha
    _same(chain["head_sha256"], prior_head, "current chain head")
    _same(chain["accepted_pairs"], _accepted(index), "canonical accepted pair roster")


def next_request(
    chain: dict[str, Any], *, pins_sha256: str, root_origin_sha256: str,
) -> dict[str, Any]:
    """Plan exactly the next unused request; admission belongs to external tools."""
    validate_chain_metadata(chain)
    _digest(pins_sha256, "external pins")
    _digest(root_origin_sha256, "external root origin")
    _same(chain["pins_sha256"], pins_sha256, "external chain pins")
    _same(chain["root_origin_sha256"], root_origin_sha256, "external root origin")
    return json.loads(_canonical(_request_for_chain(chain)))


def validate_request(
    request: dict[str, Any], chain: dict[str, Any], *, pins_sha256: str, root_origin_sha256: str,
) -> None:
    """Require exact equality with the one deterministic next request."""
    _object(request, REQUEST_KEYS, "request")
    expected = next_request(chain, pins_sha256=pins_sha256, root_origin_sha256=root_origin_sha256)
    _same(request, expected, "next request")


def budget(request: dict[str, Any]) -> dict[str, int]:
    """Return exact current-job counts after checking the request's static scope.

    This cannot authenticate the parent chain.  Call ``validate_request`` first
    at the execution boundary with independently authenticated origin and pins.
    """
    _canonical(request)
    _object(request, REQUEST_KEYS, "request")
    _same(request["schema"], REQUEST_SCHEMA, "request schema")
    index = _index(request["index"], minimum=1, maximum=7, label="request index")
    for key in ("pins_sha256", "root_origin_sha256", "parent_head_sha256", "chain_sha256"):
        _digest(request[key], key)
    fixed = {
        "mode": "folds" if index <= 6 else "final", "pairs": _rows(_chunk(index)),
        "prior_folds": len(_accepted(index - 1)),
        "output_relative": f"fragments/fragment_{index:03d}",
        "chain_relative": f"chains/chain_{index - 1:03d}.json", "limits": LIMITS,
        "required_full_gradient_updates": 5253, "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "engineering_only": True, "scientific_admission": False, "original_case_attempts": 0,
    }
    _same({key: request[key] for key in fixed}, fixed, "static request scope")
    count = len(_chunk(index))
    return {
        "source_updates": 50 * count if index <= 6 else 51,
        "support_updates": count, "gradient_updates": 51 * count if index <= 6 else 51,
        "optimizer_init": 2 * count if index <= 6 else 1,
        "safetensors_load": 2 if index <= 6 else 3, "module_load_state_dict": 2,
        "safetensors_save": 0 if index <= 6 else 1,
    }


def advance_chain(chain: dict[str, Any], descriptor: dict[str, Any]) -> dict[str, Any]:
    """Append authenticated-by-caller leaf metadata; never authenticate a file."""
    validate_chain_metadata(chain)
    if chain["chain_index"] == 7:
        raise ValueError("the seven-request chain is exhausted")
    _object(descriptor, DESCRIPTOR_KEYS, "leaf descriptor")
    index = chain["chain_index"] + 1
    result = {
        "schema": CHAIN_SCHEMA, "root_origin_sha256": chain["root_origin_sha256"],
        "pins_sha256": chain["pins_sha256"], "chain_index": index,
        "leaves": chain["leaves"] + [descriptor], "accepted_pairs": _accepted(index),
        "head_sha256": descriptor["sha256"], "complete": False,
    }
    validate_chain_metadata(result)
    return json.loads(_canonical(result))
