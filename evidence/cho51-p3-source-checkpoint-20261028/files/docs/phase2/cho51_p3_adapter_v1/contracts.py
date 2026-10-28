"""Strict metadata-only P3 intent and defensive compatibility values."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

PROFILE = "cho51_p3_synthetic_linear_v1"
CONTROLLER = "cho51_canonical_adapter_controller_v1"
NUMERICAL_WORKER = "cho51_provenance_numerical_worker_engineering_v2"
MAX_INTENT_BYTES = 64 * 1024
MAX_REPORT_BYTES = 1024 * 1024
MAX_METADATA_BYTES = 8 * 1024 * 1024
MAX_GRAPH_NODES = 100000
MAX_GRAPH_DEPTH = 32
_PLAN_ITEMS = (
    ("dataset", "cho2017"), ("target_subject", "subject_02"), ("method", "labram_linear"),
    ("shots_per_class", 5), ("model_seed", 11), ("repetition", 1),
)
_LEDGER_FIELDS = (
    "source_updates", "restore_count", "support_updates", "gradient_updates",
    "target_inference_calls", "query_count", "model_constructions", "measured_cells",
)
_AUTHORITY_FIELDS = (
    "execution_admitted", "scientific_admission", "measured_publication_allowed",
    "raw_input_verification_performed", "weight_verification_performed",
    "fresh_runtime_verification_performed", "claim_created", "recorder_lock_acquired",
    "backend_called", "output_tree_created", "execution_capability_returned",
    "physical_source_selection_performed", "recovery_performed", "experiment_freeze_signed",
)
PLAN = MappingProxyType(dict(_PLAN_ITEMS))
LEDGER = MappingProxyType(dict.fromkeys(_LEDGER_FIELDS, 0))
AUTHORITY = MappingProxyType(dict.fromkeys(_AUTHORITY_FIELDS, False))
OBLIGATIONS = (
    "fresh_physical_original_input_audit", "fresh_selected_weight_and_tensor_audit",
    "fresh_executor_runtime_and_compute_admission", "fresh_isolated_recorder_preparation",
    "full_historical_physical_selector_verification", "controller_transaction_qualification",
    "timing_observer_and_native_custody_qualification", "checkpoint_cohort_overlap_review",
    "owner_scientific_freeze",
)


def sha256(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise ValueError("exact immutable bytes required")
    return hashlib.sha256(raw).hexdigest()


def digest_text(value: Any) -> str:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("lowercase SHA-256 required")
    return value


def exact_fields(value: Any, names: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != names:
        raise ValueError(label + " fields differ from the versioned schema")
    return value


def exact_int(value: Any, minimum: int = 0, maximum: int = 2**63 - 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("bounded exact integer required; Boolean is not an integer")
    return value


def relative_path(value: Any) -> str:
    if type(value) is not str or not 0 < len(value) <= 1024 or "\\" in value:
        raise ValueError("bounded direct relative POSIX metadata path required")
    parts = value.split("/")
    if any(part in ("", ".", "..") or ":" in part or part.endswith((".", " "))
           or any(ord(character) < 32 for character in part) for part in parts):
        raise ValueError("metadata path alias or escape refused")
    return value


def _maximum(value: Any) -> int:
    return exact_int(value, 1, MAX_METADATA_BYTES)


def _finite(value: Any, maximum: int) -> None:
    active: set[int] = set()
    nodes = 0
    encoded_bytes = 0

    def consume(count: int) -> None:
        nonlocal encoded_bytes
        encoded_bytes += count
        if encoded_bytes > maximum:
            raise ValueError("aggregate encoded JSON byte bound exceeded")

    def visit(child: Any, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > MAX_GRAPH_NODES or depth > MAX_GRAPH_DEPTH:
            raise ValueError("finite JSON graph bound exceeded")
        kind = type(child)
        if child is None or kind is bool:
            consume(4 if child is None or child is True else 5)
            return
        if kind is int:
            if child.bit_length() > 64:
                raise ValueError("JSON integer bound exceeded")
            consume(len(str(child)))
            return
        if kind is float:
            if not math.isfinite(child):
                raise ValueError("nonfinite JSON refused")
            consume(len(repr(child)))
            return
        if kind is str:
            if len(child) > maximum:
                raise ValueError("JSON text bound exceeded")
            consume(2)
            for character in child:
                codepoint = ord(character)
                if character in ('"', "\\", "\b", "\t", "\n", "\f", "\r"):
                    consume(2)
                elif codepoint < 32 or 127 <= codepoint <= 65535:
                    consume(6)
                elif codepoint > 65535:
                    consume(12)
                else:
                    consume(1)
            return
        if kind not in (dict, list):
            raise ValueError("only exact builtin JSON types are accepted without callbacks")
        identity = id(child)
        if identity in active:
            raise ValueError("cyclic JSON graph refused")
        active.add(identity)
        consume(2 + max(0, len(child) - 1))
        if kind is dict:
            for key, item in dict.items(child):
                if type(key) is not str:
                    raise ValueError("JSON object keys must be exact strings")
                consume(1)
                visit(key, depth + 1)
                visit(item, depth + 1)
        else:
            for item in list.__iter__(child):
                visit(item, depth + 1)
        active.remove(identity)

    visit(value, 0)


def canonical_json(value: Any, *, maximum: int = MAX_METADATA_BYTES) -> str:
    _finite(value, _maximum(maximum))
    try:
        result = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if len(result.encode("utf-8")) > maximum:
            raise ValueError("encoded JSON byte bound exceeded")
        return result
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid bounded JSON") from error


def decode_json(raw: str | bytes, *, maximum: int = MAX_METADATA_BYTES) -> Any:
    _maximum(maximum)
    if type(raw) not in (str, bytes):
        raise ValueError("exact JSON text or bytes required")
    if not 0 < len(raw) <= maximum:
        raise ValueError("input JSON byte bound exceeded")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, child in items:
            if key in result:
                raise ValueError("duplicate JSON key refused")
            result[key] = child
        return result

    def constant(value: str) -> None:
        raise ValueError("nonfinite JSON constant refused: " + value)

    try:
        encoded = raw.encode("utf-8") if type(raw) is str else raw
        if not 0 < len(encoded) <= maximum:
            raise ValueError("input JSON byte bound exceeded")
        text = encoded.decode("utf-8")
        result = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
        _finite(result, maximum)
        return result
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid bounded UTF-8 JSON") from error


def _plan(value: Any) -> None:
    expected = dict(_PLAN_ITEMS)
    exact_fields(value, set(expected), "plan")
    for name in ("shots_per_class", "model_seed", "repetition"):
        exact_int(value[name])
    if canonical_json(value) != canonical_json(expected):
        raise ValueError("only subject02/linear/five-shot/seed11/repetition1 is compatible")


@dataclass(frozen=True, slots=True)
class AdapterIntent:
    payload_json: str
    expected_sha256: str

    def __post_init__(self) -> None:
        if type(self.payload_json) is not str:
            raise ValueError("intent requires immutable exact JSON text")
        digest_text(self.expected_sha256)
        payload = exact_fields(decode_json(self.payload_json, maximum=MAX_INTENT_BYTES), {
            "schema", "controller", "numerical_worker", "profile", "plan",
            "boundary_request_sha256", "boundary_assessment_sha256", "origin_contract_sha256",
            "input_manifest_sha256", "roles", "future_recorder", "outstanding_obligations",
            "engineering_only", "scientific_admission",
        }, "adapter intent")
        if sha256(self.payload_json.encode("utf-8")) != self.expected_sha256:
            raise ValueError("intent differs from independent byte pin")
        if (payload["schema"] != "cho51_p3_adapter_intent_v1"
                or payload["controller"] != CONTROLLER or payload["numerical_worker"] != NUMERICAL_WORKER
                or payload["profile"] != PROFILE or payload["engineering_only"] is not True
                or payload["scientific_admission"] is not False):
            raise ValueError("fixed engineering-only adapter intent required")
        _plan(payload["plan"])
        for name in ("boundary_request_sha256", "boundary_assessment_sha256", "origin_contract_sha256", "input_manifest_sha256"):
            digest_text(payload[name])
        exact_fields(payload["roles"], {"producer", "canonical_executor", "boundary_recorder", "historical_recorder"}, "role domains")
        for role in payload["roles"].values():
            exact_fields(role, {"git_commit", "git_dirty", "source_sha256"}, "source role")
            digest_text(role["source_sha256"])
            if (type(role["git_commit"]) is not str or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", role["git_commit"]) is None
                    or type(role["git_dirty"]) is not bool):
                raise ValueError("explicit Git source role required")
        if canonical_json(payload["future_recorder"]) != canonical_json({
            "status": "unprepared", "relative_root": "fixture/runs/phase2/lifecycle", "source": None,
        }):
            raise ValueError("future isolated recorder must remain explicitly unprepared")
        if payload["outstanding_obligations"] != list(OBLIGATIONS):
            raise ValueError("unperformed execution obligations cannot be removed")

    @property
    def payload(self) -> dict[str, Any]:
        return decode_json(self.payload_json, maximum=MAX_INTENT_BYTES)


@dataclass(frozen=True, slots=True)
class AdapterCompatibility:
    canonical_json: str

    def __post_init__(self) -> None:
        if type(self.canonical_json) is not str:
            raise ValueError("compatibility requires immutable exact JSON text")
        payload = exact_fields(decode_json(self.canonical_json, maximum=MAX_REPORT_BYTES), {
            "schema", "status", "profile", "intent_sha256", "boundary_request_sha256",
            "boundary_assessment_sha256", "origin_contract_sha256", "input_manifest_sha256",
            "selected_plan", "selected_contract_sha256", "full_route_ids_sha256",
            "adopted_route_ids_sha256", "original_plan_count", "adopted_plan_count",
            "catalog_count", "asset_count", "historical_input_claim", "metadata_cohort_origin_sha256",
            "roles", "future_recorder", "outstanding_obligations", "authority",
            "current_numerical_ledger", "scientific_admission", "metadata_files_read", "metadata_bytes_read",
        }, "compatibility report")
        authority = exact_fields(payload["authority"], set(_AUTHORITY_FIELDS), "authority")
        ledger = exact_fields(payload["current_numerical_ledger"], set(_LEDGER_FIELDS), "current ledger")
        if (payload.get("schema") != "cho51_p3_adapter_compatibility_v1"
                or payload.get("status") != "metadata_profile_compatible"
                or payload.get("profile") != PROFILE
                or any(value is not False for value in authority.values())
                or any(type(value) is not int or value != 0 for value in ledger.values())
                or payload.get("scientific_admission") is not False):
            raise ValueError("compatibility metadata cannot carry execution or science authority")
        _plan(payload["selected_plan"])
        historical = exact_fields(payload["historical_input_claim"], {"files", "bytes", "freshly_physically_verified"}, "historical input claim")
        if (exact_int(historical["files"]) != 213 or exact_int(historical["bytes"]) != 734579463
                or historical["freshly_physically_verified"] is not False):
            raise ValueError("historical input claim cannot assert fresh physical verification")
        for name, count in {"original_plan_count": 1040, "adopted_plan_count": 1020, "catalog_count": 52, "asset_count": 52}.items():
            if exact_int(payload[name]) != count:
                raise ValueError("compatibility exact metadata count differs")
        exact_int(payload["metadata_files_read"], 1, 12)
        exact_int(payload["metadata_bytes_read"], 1, 16 * 1024 * 1024)
        for name in ("intent_sha256", "boundary_request_sha256", "boundary_assessment_sha256", "origin_contract_sha256", "input_manifest_sha256", "selected_contract_sha256", "full_route_ids_sha256", "adopted_route_ids_sha256", "metadata_cohort_origin_sha256"):
            digest_text(payload[name])
        roles = exact_fields(payload["roles"], {"producer", "canonical_executor", "boundary_recorder", "historical_recorder"}, "compatibility role domains")
        for role in roles.values():
            exact_fields(role, {"git_commit", "git_dirty", "source_sha256"}, "compatibility source role")
            digest_text(role["source_sha256"])
            if (type(role["git_commit"]) is not str or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", role["git_commit"]) is None
                    or type(role["git_dirty"]) is not bool):
                raise ValueError("explicit compatibility Git source role required")
        if payload["outstanding_obligations"] != list(OBLIGATIONS) or payload["future_recorder"] != {"status": "unprepared", "relative_root": "fixture/runs/phase2/lifecycle", "source": None}:
            raise ValueError("compatibility cannot prepare execution obligations or a future recorder")

    @property
    def report(self) -> dict[str, Any]:
        return decode_json(self.canonical_json, maximum=MAX_REPORT_BYTES)

    @property
    def sha256(self) -> str:
        return sha256(self.canonical_json.encode("utf-8"))
