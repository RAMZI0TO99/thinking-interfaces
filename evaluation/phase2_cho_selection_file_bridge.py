"""Read-only binding of recorded Cho cells to persisted selection files.

This checks bounded file bytes and case claims before score extraction. A
record's completion flag is not proof of a complete scientific selection.
The caller must verify selection evidence and scientific admission separately.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from core.config import canonical_config_json, config_digest, config_snapshot
from core.provenance import SourceProvenance
from evaluation.phase2_cell_aggregation_bridge import (
    MAX_CELL_BYTES,
    PinnedCaseCell,
    _canonical_record,
)
from evaluation.phase2_cho_case_inputs import SELECTED_METHODS, ChoFirstTrancheRoute
from evaluation.phase2_cho_method_template import (
    SCORE,
    SOURCE_POLICY,
    TIE_BREAK,
    derive_cho_method_template,
)
from evaluation.phase2_factored_evidence import MAXIMUM_LOGICAL_BYTES, MAXIMUM_PACKED_BYTES
from evaluation.phase2_protocol import require_digest, source_selection
from evaluation.phase2_records import verify_envelope
from evaluation.phase2_runner import CaseRecorder, method_configuration
from evaluation.phase2_selected_source_store import SelectedSourceStore


@dataclass(frozen=True, slots=True)
class ChoSelectionFileClaim:
    """Case fields read from a pinned, checked logical selection envelope."""

    case_id: str
    evidence_sha256: str
    contract_sha256: str
    selected_candidate: str
    manifest_sha256: str | None
    manifest_path: str | None


@dataclass(frozen=True, slots=True)
class ChoSelectionFileWitness:
    """Physical selection bytes checked again after paired score extraction."""

    physical: tuple[tuple[Path, int, str, tuple[int, int, int, int]], ...]
    claims: tuple[ChoSelectionFileClaim, ...]

    def verify_stable(self) -> None:
        """Refuse a file replaced after its selection claims were inspected."""
        for path, limit, digest, file_identity in self.physical:
            _, raw = _canonical_record(path, maximum_bytes=limit)
            stat = path.stat()
            current = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
            if hashlib.sha256(raw).hexdigest() != digest or current != file_identity:
                raise ValueError("Cho selection physical file changed during verification")


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed mapping")
    return value


def _evidence_path(root: Path, value: Any) -> Path:
    if (
        not isinstance(value, str) or not value
        or "\\" in value or ":" in value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        raise ValueError("Cho selection evidence path is not canonical POSIX relative")
    relative = PurePosixPath(value)
    if (
        relative.is_absolute() or relative.as_posix() != value
        or relative.parts[:2] != ("runs", "phase2")
        or len(relative.parts) < 4
    ):
        raise ValueError("Cho selection evidence path must stay inside runs/phase2")
    path = root.joinpath(*relative.parts)
    if path.resolve(strict=False) != path or path.is_symlink():
        raise ValueError("Cho selection evidence path aliases another file")
    return path


def _logical_record(record: Mapping[str, Any], pin: PinnedCaseCell) -> Mapping[str, Any]:
    payload = _mapping(record.get("payload"), "Cho selection evidence payload")
    if (
        not verify_envelope(record, kind="engineering_smoke", expected_payload=payload)
        or record.get("sha256") != pin.selection_evidence_sha256
    ):
        raise ValueError("Cho selection evidence envelope differs from its external pin")
    return payload


def _static_contract(
    contract: Mapping[str, Any], pin: PinnedCaseCell,
    route: ChoFirstTrancheRoute,
) -> None:
    """Bind declared source policy, runtime and inputs without fold admission."""
    plan = pin.plan
    maximum_steps = contract.get("maximum_gradient_steps")
    runtime = _mapping(contract.get("runtime"), "Cho selection runtime")
    if (
        contract.get("outer_target") != plan.target_subject
        or contract.get("source_policy") != SOURCE_POLICY
        or contract.get("score") != SCORE
        or contract.get("tie_break") != TIE_BREAK
        or contract.get("early_stopping") is not False
        or contract.get("engineering_only") is not True
        or contract.get("scientific_evaluation") is not False
        or type(maximum_steps) is not int
        or not 1 <= maximum_steps <= 256
        or runtime.get("device") not in ("cpu", "cuda:0")
        or runtime.get("dtype") != "float32"
        or type(runtime.get("torch_threads")) is not int
        or runtime["torch_threads"] < 1
        or type(runtime.get("deterministic_algorithms")) is not bool
        or any(not isinstance(runtime.get(name), str) or not runtime[name]
               for name in ("python", "torch", "numpy", "braindecode"))
    ):
        raise ValueError("Cho selection static policy or runtime differs")
    if plan.method == "eegnet":
        if (
            contract.get("profile_a_manifests") != {}
            or runtime["device"] != "cpu"
            or "source_execution" in contract
        ):
            raise ValueError("Cho EEGNet source input declarations differ")
        return
    template_state = contract.get("template_state_sha256")
    initial_state = contract.get("initial_state_sha256")
    if not isinstance(template_state, str) or not isinstance(initial_state, str):
        raise ValueError("Cho LaBraM state digests are missing")
    require_digest(template_state, "LaBraM template state")
    require_digest(initial_state, "LaBraM initial state")
    if (
        contract.get("prior_template_training_verified") is not False
        or contract.get("source_trial_pool")
        != "all_profile_a_retained_trials_joined_to_profile_b"
        or contract.get("sampling_rate_hz") != 200
        or contract.get("samples_per_trial") != 800
        or contract.get("stored_unit_volts") != 0.0001
        or contract.get("extra_input_scale") != 1.0
    ):
        raise ValueError("Cho LaBraM source input declarations differ")
    subjects = {catalog.subject for catalog in route.catalogs}
    if (
        set(route.labram_assets) != subjects
        or contract.get("profile_assets") != {
            subject: asdict(route.labram_assets[subject]) for subject in sorted(subjects)
        }
    ):
        raise ValueError("Cho selection Profile B assets differ from route")
    if "source_execution" in contract:
        execution = _mapping(contract["source_execution"], "Cho source execution")
        if (
            execution.get("source_device") != runtime["device"]
            or execution.get("support_query_device") != "cpu"
            or execution.get("checkpoint_policy") not in {
                "disabled", "immutable_every_gradient_step_all_generations_retained",
            }
            or execution.get("optimizer_resume") != "stateless_sgd_only"
        ):
            raise ValueError("Cho source execution differs from runtime")
    elif runtime["device"] != "cpu":
        raise ValueError("Cho CUDA source execution metadata is missing")


def _case_claims(
    payload: Mapping[str, Any], metrics: Mapping[str, Any], pin: PinnedCaseCell,
    route: ChoFirstTrancheRoute, protocol_sha256: str,
    expected_source: SourceProvenance,
    method_config_sha256: Mapping[str, str],
) -> ChoSelectionFileClaim:
    plan, identity = pin.plan, pin.identity
    contract = _mapping(payload.get("contract"), "Cho selection contract")
    final_fit = _mapping(payload.get("final_source_fit"), "Cho final source fit")
    _static_contract(contract, pin, route)
    assets = {} if plan.method == "eegnet" else route.labram_assets
    template = derive_cho_method_template(plan, contract, assets)
    derived_digest = method_configuration(template)
    if (
        derived_digest != method_config_sha256[plan.method]
        or identity.method_config_sha256 != derived_digest
    ):
        raise ValueError("Cho selection candidate settings differ from the reviewed method digest")
    candidates = contract["candidates"]
    selected = payload.get("selected_candidate")
    if (
        not isinstance(selected, str)
        or sum(candidate["name"] == selected for candidate in candidates) != 1
    ):
        raise ValueError("Cho selected candidate is absent or duplicated in method roster")
    purpose = (
        "bounded_eegnet_source_selection" if plan.method == "eegnet"
        else "bounded_labram_source_selection"
    )
    seed_field = (
        "model_and_sampling_seed" if plan.method == "eegnet"
        else "head_and_sampling_seed"
    )
    expected_selection = config_snapshot(asdict(source_selection(
        route.catalogs, target=plan.target_subject,
    )))
    if (
        payload.get("purpose") != purpose
        or payload.get("complete") is not True
        or payload.get("outer_target_predictions_performed") is not False
        or payload.get("contract_sha256") != config_digest(contract)
        or contract.get("method") != plan.method
        or contract.get("dataset") != plan.dataset
        or contract.get("selection") != expected_selection
        or contract.get("protocol_sha256") != protocol_sha256
        or type(contract.get("shots_per_class")) is not int
        or contract["shots_per_class"] != plan.shots_per_class
        or type(contract.get(seed_field)) is not int
        or contract[seed_field] != plan.model_seed
        or contract.get("source") != asdict(expected_source)
        or final_fit.get("candidate") != selected
        or final_fit.get("candidate_sha256") != config_digest(next(
            candidate for candidate in candidates if candidate["name"] == selected
        ))
        or final_fit.get("fitted_state_sha256") != identity.checkpoint_sha256
    ):
        raise ValueError("Cho selection evidence case claims differ from the route")
    manifest_sha256 = metrics.get("selected_source_manifest_sha256")
    manifest_path = metrics.get("selected_source_manifest_path")
    if (
        manifest_sha256 is not None and not isinstance(manifest_sha256, str)
        or manifest_path is not None and not isinstance(manifest_path, str)
    ):
        raise ValueError("Cho selected-source manifest metrics are not strings")
    return ChoSelectionFileClaim(
        plan.case_id, pin.selection_evidence_sha256,
        config_digest(contract), selected,
        manifest_sha256, manifest_path,
    )


def verify_cho_recorded_selection_files(
    route: ChoFirstTrancheRoute,
    recorder: CaseRecorder,
    pins: Sequence[PinnedCaseCell],
    *,
    project_root: Path,
    expected_source: SourceProvenance,
    method_config_sha256: Mapping[str, str],
) -> ChoSelectionFileWitness:
    """Check an externally pinned nonempty Cho subset without reading scores.

    The complete first-tranche composer supplies all 1,040 pins after its
    independent identity check. This helper permits subsets for focused tests.
    It binds file bytes, recorded case claims, and candidate settings to the
    independently reviewed method digests. It does not verify the selector's
    complete fold ledger, gradient cap, source fit or scientific freeze.
    """
    if (
        not isinstance(route, ChoFirstTrancheRoute)
        or not isinstance(recorder, CaseRecorder)
        or not isinstance(project_root, Path)
        or not isinstance(expected_source, SourceProvenance)
        or not isinstance(pins, Sequence) or isinstance(pins, (str, bytes))
        or not pins or any(not isinstance(pin, PinnedCaseCell) for pin in pins)
        or not isinstance(method_config_sha256, Mapping)
        or set(method_config_sha256) != set(SELECTED_METHODS)
    ):
        raise ValueError(
            "typed Cho route, recorder, source, method digests and nonempty pins are required"
        )
    for method in SELECTED_METHODS:
        require_digest(method_config_sha256[method], f"{method} configuration")
    root = project_root.resolve(strict=True)
    if (
        root != project_root or not root.is_dir()
        or not recorder.output_root.is_relative_to(root / "runs/phase2")
        or recorder.output_root.resolve(strict=False) != recorder.output_root
    ):
        raise ValueError("Cho recorder and project root must use direct Phase II paths")
    protocol = json.loads(route.protocol_config_json)
    if (
        not isinstance(protocol, dict)
        or canonical_config_json(protocol) != route.protocol_config_json
    ):
        raise ValueError("Cho route protocol is not canonical JSON")
    protocol_sha256 = config_digest(protocol)
    plans = set(route.plans)
    seen_cases: set[str] = set()
    # Retain both bytes and filesystem identity until the final reread.
    physical: dict[Path, tuple[int, str, tuple[int, int, int, int]]] = {}
    claims: list[ChoSelectionFileClaim] = []

    def read_physical(path: Path, limit: int) -> dict[str, Any]:
        record, raw = _canonical_record(path, maximum_bytes=limit)
        stat = path.stat()
        identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
        digest = hashlib.sha256(raw).hexdigest()
        previous = physical.setdefault(path, (limit, digest, identity))
        if previous != (limit, digest, identity):
            raise ValueError("Cho selection physical file changed during verification")
        return record

    for pin in pins:
        plan = pin.plan
        if plan not in plans or plan.case_id in seen_cases:
            raise ValueError("Cho selection pin is duplicate or outside the route")
        seen_cases.add(plan.case_id)
        identity = pin.identity
        if (
            identity.source_sha256 != expected_source.source_sha256
            or identity.git_commit != expected_source.git_commit
            or identity.git_dirty is not expected_source.git_dirty
        ):
            raise ValueError("Cho selection cell source differs from external source")
        cell_path = recorder.output_root / "cells" / f"{identity.sha256}.json"
        cell = read_physical(cell_path, MAX_CELL_BYTES)
        cell_payload = _mapping(cell.get("payload"), "Cho selection cell payload")
        if (
            cell.get("sha256") != pin.cell_sha256
            or set(cell_payload) != {"identity", "metrics"}
            or cell_payload["identity"] != asdict(identity)
            or not verify_envelope(
                cell, kind="evaluation_cell", expected_payload=cell_payload,
            )
        ):
            raise ValueError("Cho selection cell differs from its external pin")
        metrics = _mapping(cell_payload["metrics"], "Cho selection cell metrics")
        if metrics.get("selection_evidence_sha256") != pin.selection_evidence_sha256:
            raise ValueError("Cho cell selection digest differs from its external pin")
        path = _evidence_path(root, metrics.get("selection_evidence_path"))
        if path.name.endswith(".factored.json"):
            read_physical(path, MAXIMUM_PACKED_BYTES)
            store = SelectedSourceStore(root, directory=path.parent.parent)
            evidence = store.read_persisted_evidence(
                path, expected_evidence_sha256=pin.selection_evidence_sha256,
            )
            read_physical(path, MAXIMUM_PACKED_BYTES)
        else:
            evidence = read_physical(path, MAXIMUM_LOGICAL_BYTES)
        payload = _logical_record(evidence, pin)
        claims.append(_case_claims(
            payload, metrics, pin, route, protocol_sha256, expected_source,
            method_config_sha256,
        ))

    return ChoSelectionFileWitness(
        tuple((path, limit, digest, file_identity)
              for path, (limit, digest, file_identity) in physical.items()),
        tuple(claims),
    )
