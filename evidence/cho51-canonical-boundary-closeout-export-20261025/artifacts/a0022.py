"""Read-only canonical metadata compatibility; never an execution capability."""

from __future__ import annotations

import hashlib
import gc
import json
import math
import os
import re
import stat
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from importlib.machinery import ModuleSpec
from types import MappingProxyType, MemberDescriptorType, ModuleType
from typing import Any

MAX_METADATA_BYTES = 8 * 1024**2
MAX_TOTAL_BYTES = 32 * 1024**2
MAX_METADATA_FILES = 32
MAX_TRIALS_PER_CATALOG = 10000
MAX_REPORT_BYTES = 1024 * 1024
MAX_TYPED_GRAPH_NODES = 500000
MAX_TYPED_GRAPH_TEXT_BYTES = 32 * 1024**2
MAX_TYPED_GRAPH_DEPTH = 40
SUBJECTS = tuple(f"subject_{index:02d}" for index in range(1, 53))
TARGETS = SUBJECTS[1:]
METHODS = ("labram_linear", "labram_lora", "labram_full", "eegnet")
SEEDS = (11, 23, 37, 53, 71)
CLASSES = ("left_hand", "right_hand")
PROSPECTIVE_BUDGET = {
    "source_updates": 0,
    "restore_count": 1,
    "support_updates": 1,
    "gradient_updates": 1,
    "target_inference_calls": 1,
    "query_count": 2,
    "model_constructions": 1,
    "measured_cells": 0,
}
ANCHORS = {
    "owner": (
        "evidence/cho51-adoption-route-20261013/owner/adoption.json",
        "ae3295c2aa5acdfad2c9b2d7ffb602ec8b0daddb07b3d433d15dcaf9fd002709",
    ),
    "proposal": (
        "evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json",
        "26edbf77961af89fdc31941cbf0425c97ebd81ed263dff706a21aac933e9b965",
    ),
    "roster": (
        "evidence/phase2-readiness-20261012/worker/roster.json",
        "ab5b4c3f11abab8cc5f91c0d36cfc88e0c857f306f6f7a0510a4214e658b1b16",
    ),
    "origin": (
        "runs/coordination/cho51_provenance_numerical_worker_20261025_v7/origin-contract.json",
        "f1318c2f05dbf55a1808e621f05f4574ee695ff5ec15187b5ce2932650eaa781",
    ),
    "factory_review": (
        "runs/coordination/cho51_provenance_restore_20261025_v2/final-review.json",
        "72b6f232d39b5b73e39ee8d56e77c0cba958a03a51854ae73e6863223e9ce627",
    ),
    "worker_review": (
        "runs/coordination/cho51_provenance_numerical_worker_20261025_v7/final-review.json",
        "0773288c76842602f42ea8e79eb60e973ae5dee7d681c0bee18f23a764a91e18",
    ),
}
CONFIG_PATHS = {
    "base": "configs/base.toml",
    "protocol": "configs/phase2/protocol.toml",
    "threshold": "configs/benchmark.toml",
    "variant": "configs/phase2/cho_profile_b_60hz.toml",
    "ceiling": "configs/phase2/selection_ceiling.toml",
    "sweep": "configs/phase2/cho_sweep.toml",
    "candidates": "runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json",
}
CONFIG_SHA256 = {
    "base": "02c8e3011abfcafe170f791ec688c791b2187d8e547dd3b2655bae2b5eedf2c4",
    "protocol": "d8b56cdb28c7cbf3999e9fc65f089535930bff23373ddf46b903695cf095fa95",
    "threshold": "2dba370f37039cbee73726c407b7377ad9933385a1acab30f21cceca7bd369b5",
    "variant": "6a3d5b9afca7bc0b82532276df1ef8f0a14db85da0eb609b5176ac967d04afb3",
    "ceiling": "a7db3ba233c71ff73c5599baa2f48ffb7616deb1c239b7bbfc41b6ac8e466548",
    "sweep": "54318bcb8cbaa5a72b6df0d981860c880a7919d40c7a26eca94848e7fbdc2dc1",
    "candidates": "f3dba0643cba2807fbc6e0421c271f260c8cf357a8bc67a19f7456931ca892ef",
}
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_REQUEST_FIELDS = {
    "schema", "root", "execution_pins", "metadata", "configuration", "evidence",
    "roles", "prospective_numerical_budget",
}


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha(value: Any) -> str:
    if type(value) is not str or _SHA.fullmatch(value) is None:
        raise ValueError("an external lowercase SHA-256 is required")
    return value


def _finite(value: Any, depth: int = 0) -> None:
    if depth > 80:
        raise ValueError("metadata nesting exceeds its bound")
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise ValueError("JSON object keys must be strings")
        for child in value.values():
            _finite(child, depth + 1)
    elif type(value) is list:
        for child in value:
            _finite(child, depth + 1)
    elif type(value) is float:
        if not math.isfinite(value):
            raise ValueError("nonfinite metadata")
    elif value is not None and type(value) not in (str, int, bool):
        raise ValueError("metadata is not finite JSON")


def _json(raw: bytes | str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def constant(value: str) -> None:
        raise ValueError("nonfinite JSON constant: " + value)

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
        _finite(value)
        return value
    except (UnicodeError, RecursionError) as error:
        raise ValueError("invalid bounded JSON") from error


def _canonical(value: Any) -> str:
    _finite(value)
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _fields(value: Any, names: set[str], name: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != names:
        raise ValueError(name + " fields differ from their explicit schema")
    return value


def _integers(value: Any, expected: dict[str, int], name: str) -> None:
    _fields(value, set(expected), name)
    if any(type(value[key]) is not int or value[key] != count for key, count in expected.items()):
        raise ValueError(name + " exact integer values differ")


def _slot_value(value: Any, field: str) -> Any:
    kind = type(value)
    for base in type.__getattribute__(kind, "__mro__"):
        namespace = type.__getattribute__(base, "__dict__")
        if field in namespace:
            descriptor = namespace[field]
            if type(descriptor) is not MemberDescriptorType:
                raise ValueError("typed graph requires genuine dataclass slot descriptors without callbacks")
            try:
                return MemberDescriptorType.__get__(descriptor, value, kind)
            except AttributeError as error:
                raise ValueError("typed graph has an uninitialized metadata slot") from error
    raise ValueError("typed graph is missing a genuine metadata slot")


def _snapshot_typed_graph(roots: tuple[Any, ...], schemas: tuple[tuple[type, tuple[str, ...]], ...]) -> tuple[Any, ...]:
    visited: dict[int, Any] = {}
    active: set[int] = set()
    nodes = 0
    text_bytes = 0

    def snapshot(value: Any, depth: int) -> Any:
        nonlocal nodes, text_bytes
        nodes += 1
        if nodes > MAX_TYPED_GRAPH_NODES or depth > MAX_TYPED_GRAPH_DEPTH:
            raise ValueError("typed graph exceeds its structural bounds")
        kind = type(value)
        if kind is str:
            if len(value) > MAX_TYPED_GRAPH_TEXT_BYTES:
                raise ValueError("typed graph text exceeds its byte bound")
            text_bytes += len(value.encode("utf-8"))
            if text_bytes > MAX_TYPED_GRAPH_TEXT_BYTES:
                raise ValueError("typed graph text exceeds its aggregate byte bound")
            return value
        if value is None or kind is bool:
            return value
        if kind is int:
            if value.bit_length() > 64:
                raise ValueError("typed graph integer exceeds its exact bound")
            return value
        if kind is float:
            if not math.isfinite(value):
                raise ValueError("typed graph contains nonfinite metadata")
            return value
        fields = None
        for approved, approved_fields in schemas:
            if kind is approved:
                fields = approved_fields
                break
        if fields is None and kind is not tuple and kind is not dict and kind is not MappingProxyType:
            raise ValueError("typed graph requires exact approved metadata types without callbacks")
        identity = id(value)
        if identity in active:
            raise ValueError("typed graph cannot contain reference cycles")
        if identity in visited:
            return visited[identity]
        active.add(identity)
        if fields is not None:
            values = {field: snapshot(_slot_value(value, field), depth + 1) for field in fields}
            try:
                copied = kind(**values)
            except (TypeError, AttributeError) as error:
                raise ValueError("typed graph dataclass metadata fields differ") from error
        elif kind is tuple:
            copied = tuple(snapshot(child, depth + 1) for child in value)
        else:
            backing = value
            if kind is MappingProxyType:
                referents = gc.get_referents(value)
                if type(referents) is not list or len(referents) != 1 or type(referents[0]) is not dict:
                    raise ValueError("typed graph mapping proxy requires an exact dict backing without callbacks")
                backing = referents[0]
            copied = {}
            for key, child in dict.items(backing):
                if type(key) is not str:
                    raise ValueError("typed graph mapping keys require exact strings without callbacks")
                copied[snapshot(key, depth + 1)] = snapshot(child, depth + 1)
            if kind is MappingProxyType:
                copied = MappingProxyType(copied)
        active.remove(identity)
        visited[identity] = copied
        return copied

    return tuple(snapshot(value, 0) for value in roots)


def _direct_root(value: Any) -> Path:
    if type(value) is not str:
        raise ValueError("root must be an absolute direct path")
    root = Path(value)
    if not root.is_absolute() or str(root) != value or root.resolve(strict=True) != root:
        raise ValueError("root is not normalized and direct")
    _ancestors(root, include_leaf=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    return root


def _ancestors(path: Path, *, include_leaf: bool = False) -> tuple[tuple[Any, ...], ...]:
    paths = tuple(reversed(path.parents)) + ((path,) if include_leaf else ())
    rows = []
    for parent in paths:
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or parent.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("metadata ancestor is not a direct non-reparse directory")
        rows.append((str(parent), info.st_dev, info.st_ino, info.st_ctime_ns))
    return tuple(rows)


def _relative(root: Path, value: Any) -> Path:
    if type(value) is not str or not value or "\\" in value or "\x00" in value:
        raise ValueError("metadata path must be project-relative POSIX syntax")
    parts = value.split("/")
    if any(part in ("", ".", "..") or ":" in part or part.endswith((".", " ")) for part in parts):
        raise ValueError("metadata path aliases or escapes its root")
    path = root.joinpath(*parts)
    if path.resolve(strict=True) != path or not path.is_relative_to(root):
        raise ValueError("metadata path is not direct")
    return path


def _identity(info: os.stat_result) -> tuple[int, ...]:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink


def stable_metadata_bytes(path: Path, expected_sha256: str) -> tuple[bytes, tuple[Any, ...]]:
    """Bound one direct metadata file, retaining path and descriptor identities."""
    _sha(expected_sha256)
    if not path.is_absolute() or path.resolve(strict=True) != path:
        raise ValueError("metadata file must be direct and absolute")
    ancestors = _ancestors(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or path.is_symlink() or getattr(before, "st_file_attributes", 0) & 0x400:
        raise ValueError("metadata requires one regular non-reparse link")
    if not 0 < before.st_size <= MAX_METADATA_BYTES:
        raise ValueError("metadata byte limit exceeded")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(MAX_METADATA_BYTES + 1)
        finished = os.fstat(stream.fileno())
    after = path.lstat()
    signature = _identity(before)
    if (
        signature[:4] != _identity(opened)[:4] or _identity(opened) != _identity(finished)
        or opened.st_nlink != before.st_nlink or finished.st_nlink != before.st_nlink
        or not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(finished.st_mode)
        or signature != _identity(after) or len(raw) != before.st_size
        or _digest(raw) != expected_sha256 or _ancestors(path) != ancestors
        or path.resolve(strict=True) != path or path.is_symlink()
        or getattr(after, "st_file_attributes", 0) & 0x400
    ):
        raise ValueError("metadata bytes or physical identity changed")
    return raw, (signature, ancestors)


@dataclass(frozen=True, slots=True)
class CanonicalBoundaryRequest:
    payload_json: str
    expected_sha256: str

    def __post_init__(self) -> None:
        if type(self.payload_json) is not str or not 0 < len(self.payload_json.encode("utf-8")) <= MAX_METADATA_BYTES:
            raise ValueError("request must be bounded UTF-8 JSON")
        _sha(self.expected_sha256)
        if _digest(self.payload_json.encode("utf-8")) != self.expected_sha256:
            raise ValueError("request differs from external pin")
        payload = _fields(_json(self.payload_json), _REQUEST_FIELDS, "request")
        if payload["schema"] != "cho51_canonical_boundary_request_v1":
            raise ValueError("unknown canonical boundary request schema")
        _integers(payload["prospective_numerical_budget"], PROSPECTIVE_BUDGET, "prospective budget")
        for field in ("execution_pins", "metadata"):
            _file_pin(payload[field])
        _fields(payload["configuration"], set(CONFIG_PATHS) | {"cohort"}, "configuration")
        _fields(payload["evidence"], set(ANCHORS), "evidence")
        _fields(payload["roles"], {"producer", "executor", "recorder"}, "roles")
        for value in (*payload["configuration"].values(), *payload["evidence"].values()):
            _file_pin(value)
        for role in payload["roles"].values():
            _fields(role, {"source", "runtime_identity"}, "role")
            _source(role["source"])
            runtime = _fields(role["runtime_identity"], {"role", "evidence_sha256", "fresh_runtime_verification_performed"}, "runtime identity")
            _sha(runtime["evidence_sha256"])
            if runtime["fresh_runtime_verification_performed"] is not False:
                raise ValueError("preflight cannot claim fresh runtime qualification")

    @property
    def payload(self) -> dict[str, Any]:
        return _json(self.payload_json)


@dataclass(frozen=True, slots=True)
class BoundaryAssessment:
    _report_json: str

    def __post_init__(self) -> None:
        if type(self._report_json) is not str:
            raise ValueError("report requires exact immutable JSON text without callbacks")
        raw = self._report_json.encode("utf-8")
        if not 0 < len(raw) <= MAX_REPORT_BYTES:
            raise ValueError("report bound exceeded")
        report = _json(raw)
        if report.get("schema") != "cho51_canonical_boundary_assessment_v1" or report.get("status") != "metadata_contract_compatible":
            raise ValueError("assessment is not the compatibility-only schema")
        authority = report.get("authority")
        if type(authority) is not dict or set(authority) != set(_authority()) or any(value is not False for value in authority.values()):
            raise ValueError("assessment cannot carry authority")
        _integers(report.get("current_numerical_ledger"), {key: 0 for key in PROSPECTIVE_BUDGET}, "current ledger")

    @property
    def report(self) -> dict[str, Any]:
        return _json(self._report_json)

    @property
    def canonical_json(self) -> str:
        return self._report_json

    @property
    def sha256(self) -> str:
        return _digest(self._report_json.encode("utf-8"))


def _authority() -> dict[str, bool]:
    return dict.fromkeys((
        "execution_admitted", "measured_publication_allowed", "scientific_admission",
        "raw_input_verification_performed", "weight_verification_performed",
        "fresh_runtime_verification_performed", "unchanged_canonical_worker_qualified",
        "unchanged_canonical_parent_qualified", "single_root_factory_qualified",
        "claim_created", "recorder_lock_acquired", "physical_source_selection_performed",
        "backend_called", "model_constructed", "array_decoded", "source_fit_performed",
        "support_update_performed", "query_performed", "publication_performed",
        "recovery_performed", "output_tree_created", "execution_capability_returned",
        "experiment_freeze_signed",
    ), False)


def _file_pin(value: Any) -> dict[str, Any]:
    value = _fields(value, {"path", "sha256"}, "file pin")
    if type(value["path"]) is not str:
        raise ValueError("file pin path must be a string")
    _sha(value["sha256"])
    return value


def _source(value: Any) -> dict[str, Any]:
    value = _fields(value, {"git_commit", "source_sha256", "git_dirty"}, "source role")
    _sha(value["source_sha256"])
    if type(value["git_commit"]) is not str or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value["git_commit"]) is None or type(value["git_dirty"]) is not bool:
        raise ValueError("genuine explicit Git source role is required")
    return value


def _contract_module(contract_class: type, reference_class: type, planner_path: Path) -> ModuleType:
    names = (reference_class.__module__, "_cho51_worker_planner")
    for name in names:
        module = sys.modules.get(name)
        if type(module) is not ModuleType:
            continue
        namespace = module.__dict__
        specification = namespace.get("__spec__")
        if (namespace.get("Cho51RouteContract") is contract_class
                and (contract_class is reference_class or name == "_cho51_worker_planner")
                and namespace.get("__file__") == str(planner_path)
                and type(specification) is ModuleSpec and specification.origin == str(planner_path)):
            return module
    raise ValueError("actual reviewed adopted contract class required; stale helper epoch refused")


def _execution_schema(pins: Any) -> dict[str, Any]:
    pins = _fields(pins, {"schema", "source_sha256", "environment_sha256", "base_config_sha256", "route", "candidate_config_path", "candidate_config_sha256", "method_config_sha256", "selection_ceiling_config_sha256", "sweep_config_sha256"}, "canonical execution pins")
    if pins["schema"] != "cho_engineering_execution_pins_v1":
        raise ValueError("canonical pin schema differs")
    for key in ("source_sha256", "environment_sha256", "base_config_sha256", "candidate_config_sha256", "selection_ceiling_config_sha256", "sweep_config_sha256"):
        _sha(pins[key])
    _fields(pins["route"], {"protocol_config_sha256", "threshold_config_sha256", "cohort_audit_sha256", "variant_config_sha256"}, "route pins")
    _fields(pins["method_config_sha256"], set(METHODS), "method pins")
    for value in (*pins["route"].values(), *pins["method_config_sha256"].values()):
        _sha(value)
    if pins["candidate_config_path"] != CONFIG_PATHS["candidates"]:
        raise ValueError("canonical candidate path differs")
    return pins


def assess_metadata(request: CanonicalBoundaryRequest, *, full_route: Any, adopted_route: Any, input_pins: Any) -> BoundaryAssessment:
    """Reconstruct metadata joins; return no lock, callback, backend or admission."""
    if type(request) is not CanonicalBoundaryRequest:
        raise ValueError("actual immutable boundary request required")
    payload = request.payload
    root = _direct_root(payload["root"])
    retained: dict[Path, tuple[bytes, tuple[Any, ...], str]] = {}

    def read(pin: dict[str, Any]) -> bytes:
        path = _relative(root, _file_pin(pin)["path"])
        if path.suffix not in (".json", ".toml"):
            raise ValueError("only explicit JSON/TOML metadata files are admitted")
        if path in retained:
            if retained[path][2] != pin["sha256"]:
                raise ValueError("conflicting metadata pins")
            return retained[path][0]
        if len(retained) >= MAX_METADATA_FILES:
            raise ValueError("metadata file-count bound exceeded")
        raw, identity = stable_metadata_bytes(path, pin["sha256"])
        if len(raw) + sum(len(item[0]) for item in retained.values()) > MAX_TOTAL_BYTES:
            raise ValueError("metadata aggregate byte limit exceeded")
        retained[path] = raw, identity, pin["sha256"]
        return raw

    evidence = {}
    for name, (relative, expected) in ANCHORS.items():
        if payload["evidence"][name] != {"path": relative, "sha256": expected}:
            raise ValueError("accepted owner/package/origin anchor changed")
        evidence[name] = _json(read(payload["evidence"][name]))
    pins = _execution_schema(_json(read(payload["execution_pins"])))
    configs = {}
    for name, pin in payload["configuration"].items():
        if name in CONFIG_PATHS and pin != {"path": CONFIG_PATHS[name], "sha256": CONFIG_SHA256[name]}:
            raise ValueError("canonical configuration path or frozen bytes changed")
        if name == "cohort" and not pin["path"].endswith(".json"):
            raise ValueError("metadata cohort origin requires JSON")
        raw = read(pin)
        configs[name] = _json(raw) if pin["path"].endswith(".json") else tomllib.loads(raw.decode("utf-8"))
        _finite(configs[name])
    metadata = _fields(_json(read(payload["metadata"])), {"schema", "scope", "raw_input_bytes_verified", "weight_bytes_verified", "catalogs", "assets"}, "route metadata")
    if metadata["schema"] != "cho51_canonical_route_metadata_v1" or metadata["scope"] not in ("fabricated_catalog_asset_metadata_unverified", "externally_supplied_catalog_asset_metadata_unverified") or metadata["raw_input_bytes_verified"] is not False or metadata["weight_bytes_verified"] is not False:
        raise ValueError("metadata cannot masquerade as verified raw inputs or weights")

    from core.config import canonical_config_json, config_digest
    from core.provenance import capture_source
    from docs.phase2.cho51_route_candidate_v1.route_contract import Cho51RouteContract, validate_decision
    from docs.phase2.cho51_worker_bridge_v1 import worker_bridge
    from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute
    from evaluation.phase2_cho_case_inputs import ChoCaseInputPins, ChoFirstTrancheRoute
    from evaluation.phase2_cho_execution import load_execution_pins
    from evaluation.phase2_profile_binding import ChoProfileAssets60Hz
    from evaluation.phase2_protocol import InnerFold, SourceSelection, TrialCatalog, nested_episode, source_selection
    from evaluation.phase2_records import envelope
    from evaluation.phase2_runner import CasePlan
    from scripts.audit_phase2_protocol import validate_protocol

    if type(full_route) is not ChoFirstTrancheRoute or type(adopted_route) is not Cho51WorkerRoute or type(input_pins) is not ChoCaseInputPins:
        raise ValueError("actual complete canonical and adopted route classes required")
    planner_path = _relative(root, worker_bridge.PLANNER)
    planner_raw, planner_identity = stable_metadata_bytes(planner_path, worker_bridge.PLANNER_SHA)
    retained[planner_path] = planner_raw, planner_identity, worker_bridge.PLANNER_SHA
    if len(retained) > MAX_METADATA_FILES or sum(len(item[0]) for item in retained.values()) > MAX_TOTAL_BYTES:
        raise ValueError("metadata and reviewed source exceed aggregate bounds")
    supplied_contract = _slot_value(adopted_route, "contract")
    contract_class = type(supplied_contract)
    contract_module = _contract_module(contract_class, Cho51RouteContract, planner_path)
    full_route, adopted_route, input_pins = _snapshot_typed_graph((full_route, adopted_route, input_pins), (
        (ChoFirstTrancheRoute, ("plans", "catalogs", "labram_assets", "protocol_config_json", "selection_records_json", "episode_records_json")),
        (Cho51WorkerRoute, ("contract", "_full_route")),
        (ChoCaseInputPins, ("protocol_config_sha256", "threshold_config_sha256", "cohort_audit_sha256", "variant_config_sha256")),
        (contract_class, ("plans", "catalogs", "selections", "method_config_sha256", "owner_decision_sha256")),
        (CasePlan, ("dataset", "target_subject", "method", "shots_per_class", "model_seed", "repetition")),
        (TrialCatalog, ("dataset", "subject", "trial_ids", "labels", "classes", "artifact_sha256", "preprocessing_sha256")),
        (ChoProfileAssets60Hz, ("profile_b_artifact_sha256", "profile_b_manifest_sha256", "variant_config_sha256")),
        (SourceSelection, ("dataset", "target_subject", "source_subjects", "inner_folds", "catalog_sha256")),
        (InnerFold, ("training_subjects", "validation_subject")),
    ))
    if type(full_route.protocol_config_json) is not str:
        raise ValueError("route protocol requires immutable JSON text")
    validate_decision(evidence["owner"], evidence["proposal"], evidence["roster"])
    if evidence["factory_review"].get("passed") is not True or evidence["worker_review"].get("passed") is not True or evidence["worker_review"].get("scientific_admission") is not False:
        raise ValueError("accepted historical engineering reviews differ")
    origin = evidence["origin"]["summary"]
    current_source = asdict(capture_source(root))
    expected_roles = {
        "producer": (origin["historical_source"], ANCHORS["origin"][1]),
        "executor": (current_source, payload["execution_pins"]["sha256"]),
        "recorder": (current_source, ANCHORS["worker_review"][1]),
    }
    for name, (source, runtime_evidence) in expected_roles.items():
        expected_role = {"source": source, "runtime_identity": {"role": name, "evidence_sha256": runtime_evidence, "fresh_runtime_verification_performed": False}}
        if payload["roles"][name] != expected_role:
            raise ValueError("independently derived provenance/runtime role differs: " + name)
    if payload["roles"]["producer"]["source"] == payload["roles"]["executor"]["source"]:
        raise ValueError("historical producer cannot be replaced by current source")
    joins = {
        "base": pins["base_config_sha256"], "protocol": pins["route"]["protocol_config_sha256"],
        "threshold": pins["route"]["threshold_config_sha256"], "variant": pins["route"]["variant_config_sha256"],
        "cohort": pins["route"]["cohort_audit_sha256"], "ceiling": pins["selection_ceiling_config_sha256"],
        "sweep": pins["sweep_config_sha256"], "candidates": pins["candidate_config_sha256"],
    }
    if any(payload["configuration"][name]["sha256"] != digest for name, digest in joins.items()) or asdict(input_pins) != pins["route"]:
        raise ValueError("canonical configuration and route input pin joins differ")
    cohort = _fields(configs["cohort"], {"schema", "metadata_sha256", "available_subjects", "raw_input_bytes_verified"}, "metadata cohort origin")
    if cohort["schema"] != "cho51_canonical_metadata_cohort_origin_v1" or cohort["metadata_sha256"] != payload["metadata"]["sha256"] or cohort["available_subjects"] != list(SUBJECTS) or cohort["raw_input_bytes_verified"] is not False:
        raise ValueError("independently pinned metadata cohort origin differs")
    candidates = _fields(configs["candidates"], {"schema_version", "status", "purpose", "shots_per_class", "model_seeds", "methods"}, "candidate configuration")
    if type(candidates["schema_version"]) is not int or candidates["schema_version"] != 1 or type(candidates["shots_per_class"]) is not int or candidates["shots_per_class"] != 5 or candidates["model_seeds"] != list(SEEDS) or any(type(seed) is not int for seed in candidates["model_seeds"]) or type(candidates["methods"]) is not list or len(candidates["methods"]) != 4:
        raise ValueError("canonical candidate roster differs")
    method_rows = {}
    for row in candidates["methods"]:
        _fields(row, {"method", "dataset", "input_profile", "variant_config_sha256", "source_policy", "score", "tie_break", "early_stopping", "source_seed_policy", "candidates"}, "method configuration")
        if row["method"] in method_rows or row["method"] not in METHODS or row["dataset"] != "cho2017" or type(row["early_stopping"]) is not bool or row["early_stopping"] is not False:
            raise ValueError("canonical method inventory or typed settings differ")
        method_rows[row["method"]] = row
    if set(method_rows) != set(METHODS) or any(config_digest(method_rows[method]) != pins["method_config_sha256"][method] for method in METHODS):
        raise ValueError("method settings differ from independent canonical pins")
    loaded = load_execution_pins(root, _relative(root, payload["execution_pins"]["path"]), payload["execution_pins"]["sha256"])
    if loaded != pins or pins["source_sha256"] != expected_roles["executor"][0]["source_sha256"]:
        raise ValueError("genuine canonical execution pin verification differs")
    protocol = configs["protocol"]
    shots = validate_protocol(protocol)
    if tuple(protocol["protocol"]["model_seeds"]) != SEEDS or any(type(seed) is not int for seed in protocol["protocol"]["model_seeds"]) or protocol["datasets"]["cho2017"]["expected_subjects"] != 52 or type(protocol["datasets"]["cho2017"]["expected_subjects"]) is not int or protocol["protocol"]["experiment_frozen"] is not False or tuple(protocol["datasets"]["cho2017"]["classes"]) != CLASSES:
        raise ValueError("canonical protocol roster or freeze flags differ")
    if canonical_config_json(protocol) != full_route.protocol_config_json:
        raise ValueError("route protocol differs from independently pinned configuration")
    catalogs_data = metadata["catalogs"]
    if type(catalogs_data) is not list or len(catalogs_data) != 52:
        raise ValueError("exact52 catalog metadata rows required")
    preprocessing = config_digest({"profile_identity": protocol["preparation"]["profile_identity"], "threshold_config_sha256": input_pins.threshold_config_sha256, "dataset": "cho2017", "threshold": configs["threshold"]["datasets"]["cho2017"]["artifact_threshold_volts"]})
    catalogs = []
    for row in catalogs_data:
        _fields(row, {"dataset", "subject", "trial_ids", "labels", "classes", "artifact_sha256", "preprocessing_sha256"}, "catalog metadata")
        if any(type(row[key]) is not list for key in ("trial_ids", "labels", "classes")) or not 1 <= len(row["trial_ids"]) <= MAX_TRIALS_PER_CATALOG:
            raise ValueError("catalog trial metadata bound or types differ")
        catalog = TrialCatalog(row["dataset"], row["subject"], tuple(row["trial_ids"]), tuple(row["labels"]), tuple(row["classes"]), row["artifact_sha256"], row["preprocessing_sha256"])
        if catalog.dataset != "cho2017" or catalog.classes != CLASSES or catalog.preprocessing_sha256 != preprocessing:
            raise ValueError("catalog profile/preprocessing join differs")
        catalogs.append(catalog)
    catalogs_tuple = tuple(catalogs)
    if tuple(catalog.subject for catalog in catalogs_tuple) != SUBJECTS or type(full_route.catalogs) is not tuple or any(type(catalog) is not TrialCatalog for catalog in full_route.catalogs) or full_route.catalogs != catalogs_tuple:
        raise ValueError("complete ordered52 actual catalog inventory differs")
    asset_rows = _fields(metadata["assets"], set(SUBJECTS), "asset inventory")
    expected_assets = {}
    for subject, row in asset_rows.items():
        _fields(row, {"profile_b_artifact_sha256", "profile_b_manifest_sha256", "variant_config_sha256"}, "asset metadata")
        if row["variant_config_sha256"] != input_pins.variant_config_sha256:
            raise ValueError("asset variant pin differs")
        expected_assets[subject] = ChoProfileAssets60Hz(**row)
    if set(full_route.labram_assets) != set(SUBJECTS) or any(type(value) is not ChoProfileAssets60Hz for value in full_route.labram_assets.values()) or dict(full_route.labram_assets) != expected_assets:
        raise ValueError("complete52 actual asset inventory differs")
    original_plans = tuple(CasePlan("cho2017", subject, method, 5, seed, 1) for subject in SUBJECTS for method in METHODS for seed in SEEDS)
    adopted_plans = tuple(plan for plan in original_plans if plan.target_subject in TARGETS)
    if type(full_route.plans) is not tuple or any(type(plan) is not CasePlan for plan in full_route.plans) or full_route.plans != original_plans or type(adopted_route.plans) is not tuple or adopted_route.plans != adopted_plans or any(type(plan) is not CasePlan for plan in adopted_route.plans) or adopted_route._full_route is not full_route:
        raise ValueError("exact original1040/adopted1020 actual identities required")
    roster_rows = [{**asdict(plan), "case_id": plan.case_id, "method_config_sha256": pins["method_config_sha256"][plan.method]} for plan in original_plans]
    if evidence["roster"]["cases"] != roster_rows or evidence["proposal"]["proposed_case_rows"] != roster_rows[20:] or evidence["proposal"]["excluded_case_rows"] != roster_rows[:20]:
        raise ValueError("independently rederived original/adopted owner identity mappings differ")
    selections = {subject: source_selection(catalogs_tuple, target=subject) for subject in SUBJECTS}
    selection_records = {subject: canonical_config_json(envelope("source_selection", asdict(selection))) for subject, selection in selections.items()}
    episodes = {catalog.subject: canonical_config_json(envelope("episode_manifest", nested_episode(catalog, shots=shots, protocol_sha256=config_digest(protocol)).payload())) for catalog in catalogs_tuple}
    if dict(full_route.selection_records_json) != selection_records or dict(full_route.episode_records_json) != episodes:
        raise ValueError("complete52 source-selection/episode metadata joins differ")
    contract = adopted_route.contract
    if contract.catalogs != catalogs_tuple or dict(contract.selections) != {subject: selections[subject] for subject in TARGETS} or dict(contract.method_config_sha256) != pins["method_config_sha256"] or contract.owner_decision_sha256 != ANCHORS["owner"][1]:
        raise ValueError("adopted contract catalog/selection/method/owner joins differ")
    for path, (raw, identity, expected) in retained.items():
        current_raw, current_identity = stable_metadata_bytes(path, expected)
        if current_raw != raw or current_identity != identity:
            raise ValueError("metadata replaced during compatibility assessment")
    if asdict(capture_source(root)) != expected_roles["executor"][0]:
        raise ValueError("current canonical source changed during assessment")
    if sys.modules.get(contract_module.__name__) is not contract_module or contract_module.__dict__.get("Cho51RouteContract") is not contract_class:
        raise ValueError("reviewed contract module or class epoch changed during assessment")
    report = {
        "schema": "cho51_canonical_boundary_assessment_v1",
        "status": "metadata_contract_compatible",
        "request_sha256": request.expected_sha256,
        "execution_pins_sha256": payload["execution_pins"]["sha256"],
        "route_metadata_sha256": payload["metadata"]["sha256"],
        "metadata_scope": metadata["scope"],
        "roles": payload["roles"],
        "historical_recorder_source": origin["recorder_control_source"],
        "accepted_evidence": payload["evidence"],
        "configuration": payload["configuration"],
        "available_catalogs": 52,
        "available_labram_assets": 52,
        "original_plan_count": 1040,
        "adopted_plan_count": 1020,
        "evaluation_targets": list(TARGETS),
        "source_selection_records_rederived": 52,
        "episode_records_rederived": 52,
        "all_original_case_ids_sha256": config_digest({"case_ids": [plan.case_id for plan in original_plans]}),
        "all_adopted_case_ids_sha256": config_digest({"case_ids": [plan.case_id for plan in adopted_plans]}),
        "prospective_engineering_case": asdict(adopted_plans[0]),
        "prospective_numerical_budget": payload["prospective_numerical_budget"],
        "current_numerical_ledger": {key: 0 for key in PROSPECTIVE_BUDGET},
        "authority": _authority(),
        "original_case_attempts_remaining": 0,
        "metadata_files_read": len(retained),
        "metadata_bytes_read": sum(len(item[0]) for item in retained.values()),
        "outstanding_obligations": ["fresh physical raw-input authentication", "fresh selected-weight and tensor authentication", "fresh runtime/compute admission", "full historical physical selector verification", "canonical engineering terminal successor", "timing readiness", "remaining method-chain qualification", "checkpoint cohort/overlap lineage", "owner scientific freeze"],
    }
    return BoundaryAssessment(_canonical(report))
