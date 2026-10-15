"""Read-only adopted-51 selection-file binding with a pinned 5,253-step policy.

This successor changes the old static ceiling and roster boundary only. It
does not establish complete fold evidence, numerical fitting, publications,
tensor identity, checkpoint cohort review or scientific execution authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.config import config_digest, config_snapshot
from core.provenance import SourceProvenance
from docs.phase2.cho51_execution_interfaces_v1.interfaces import (
    verify_case_identity_bindings,
)
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute
from evaluation.phase2_cell_aggregation_bridge import (
    MAX_CELL_BYTES,
    PinnedCaseCell,
    _canonical_record,
)
from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute
from evaluation.phase2_cho_method_template import (
    SCORE,
    SOURCE_POLICY,
    TIE_BREAK,
    derive_cho_method_template,
)
from evaluation.phase2_cho_selection_file_bridge import (
    ChoSelectionFileClaim,
    ChoSelectionFileWitness,
    _evidence_path,
    _logical_record,
    _mapping,
)
from evaluation.phase2_factored_evidence import MAXIMUM_LOGICAL_BYTES, MAXIMUM_PACKED_BYTES
from evaluation.phase2_protocol import require_digest, source_selection
from evaluation.phase2_records import verify_envelope
from evaluation.phase2_runner import CaseRecorder, method_configuration
from evaluation.phase2_selected_source_store import SelectedSourceStore


SELECTION_CEILING_RELATIVE = "configs/phase2/selection_ceiling.toml"
ADOPTED_SELECTION_CEILING = 5253
MAXIMUM_CEILING_BYTES = 16 * 1024


def _read_ceiling(path: Path, expected_sha256: str) -> tuple[int, int, int, int]:
    """Read bounded direct TOML bytes, binding both content and physical identity."""
    require_digest(expected_sha256, "independent selection ceiling config")
    try:
        if (
            path.is_symlink() or not path.is_file() or path.resolve() != path
            or path.parent.is_symlink() or path.parent.resolve() != path.parent
        ):
            raise ValueError("selection ceiling is absent or aliases another path")
        before = path.stat()
        if (
            not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
            or not 0 < before.st_size <= MAXIMUM_CEILING_BYTES
        ):
            raise ValueError("selection ceiling file size or link count differs")
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if not os.path.samestat(before, opened):
                raise ValueError("selection ceiling changed while opening")
            raw = stream.read(MAXIMUM_CEILING_BYTES + 1)
            closed = os.fstat(stream.fileno())
        after = path.stat()
        identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        if (
            not os.path.samestat(before, closed)
            or identity != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            or closed.st_size != before.st_size or closed.st_mtime_ns != before.st_mtime_ns
            or len(raw) != before.st_size or path.is_symlink() or path.resolve() != path
            or hashlib.sha256(raw).hexdigest() != expected_sha256
        ):
            raise ValueError("selection ceiling bytes or identity changed")
        document = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError("selection ceiling cannot be read as pinned TOML") from error
    if (
        set(document) != {"maximum_gradient_steps"}
        or type(document["maximum_gradient_steps"]) is not int
        or document["maximum_gradient_steps"] != ADOPTED_SELECTION_CEILING
    ):
        raise ValueError("selection ceiling must contain only integer maximum_gradient_steps = 5253")
    return identity


@dataclass(frozen=True, slots=True)
class Cho51SelectionCeilingWitness:
    path: Path
    expected_sha256: str
    file_identity: tuple[int, int, int, int]

    @property
    def maximum_gradient_steps(self) -> int:
        return ADOPTED_SELECTION_CEILING

    def verify_stable(self) -> None:
        if _read_ceiling(self.path, self.expected_sha256) != self.file_identity:
            raise ValueError("selection ceiling physical identity changed during verification")


def load_selection_ceiling(
    project_root: Path, *, expected_sha256: str,
) -> Cho51SelectionCeilingWitness:
    """Require an independent byte pin; never derive the expected hash from disk."""
    if (
        not isinstance(project_root, Path) or not project_root.is_absolute()
        or project_root.resolve() != project_root or not project_root.is_dir()
    ):
        raise ValueError("direct absolute project root required")
    path = project_root / SELECTION_CEILING_RELATIVE
    return Cho51SelectionCeilingWitness(path, expected_sha256, _read_ceiling(path, expected_sha256))


@dataclass(frozen=True, slots=True)
class Cho51SelectionFileWitness:
    """Legacy physical/claim witness plus the independently pinned policy file."""

    selection_files: ChoSelectionFileWitness
    ceiling: Cho51SelectionCeilingWitness
    owner_decision_sha256: str

    @property
    def claims(self) -> tuple[ChoSelectionFileClaim, ...]:
        return self.selection_files.claims

    @property
    def physical(self) -> tuple:
        return self.selection_files.physical

    @property
    def scientific_result_admitted(self) -> bool:
        return False

    def verify_stable(self) -> None:
        self.ceiling.verify_stable()
        self.selection_files.verify_stable()
        self.ceiling.verify_stable()


def _static_contract(
    contract: Mapping[str, Any], pin: PinnedCaseCell,
    route: ChoFirstTrancheRoute, *, ceiling: int,
) -> None:
    """Legacy static checks, with an explicit pinned-ceiling dependency only."""
    if type(ceiling) is not int or ceiling != ADOPTED_SELECTION_CEILING:
        raise ValueError("the adopted pinned selection ceiling is required")
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
        or not 1 <= maximum_steps <= ceiling
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
    method_config_sha256: Mapping[str, str], *, ceiling: int,
) -> ChoSelectionFileClaim:
    """Retain legacy claim derivation, injecting only the new static policy."""
    plan, identity = pin.plan, pin.identity
    contract = _mapping(payload.get("contract"), "Cho selection contract")
    final_fit = _mapping(payload.get("final_source_fit"), "Cho final source fit")
    _static_contract(contract, pin, route, ceiling=ceiling)
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


def _verify_selection_files(
    route: ChoFirstTrancheRoute, recorder: CaseRecorder,
    pins: tuple[PinnedCaseCell, ...], *, project_root: Path,
    expected_source: SourceProvenance, method_config_sha256: Mapping[str, str],
    ceiling: int,
) -> ChoSelectionFileWitness:
    """Private byte loop; public callers first require exact adopted coverage."""
    protocol_sha256 = config_digest(json.loads(route.protocol_config_json))
    plans = set(route.plans)
    seen_cases: set[str] = set()
    physical: dict[Path, tuple[int, str, tuple[int, int, int, int]]] = {}
    claims: list[ChoSelectionFileClaim] = []

    def read_physical(path: Path, limit: int) -> dict[str, Any]:
        record, raw = _canonical_record(path, maximum_bytes=limit)
        observed = path.stat()
        identity = (observed.st_dev, observed.st_ino, observed.st_size, observed.st_mtime_ns)
        digest = hashlib.sha256(raw).hexdigest()
        previous = physical.setdefault(path, (limit, digest, identity))
        if previous != (limit, digest, identity):
            raise ValueError("Cho selection physical file changed during verification")
        return record

    for pin in pins:
        plan, identity = pin.plan, pin.identity
        if plan not in plans or plan.target_subject == "subject_01" or plan.case_id in seen_cases:
            raise ValueError("Cho selection pin is duplicate or outside adopted targets")
        seen_cases.add(plan.case_id)
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
            or not verify_envelope(cell, kind="evaluation_cell", expected_payload=cell_payload)
        ):
            raise ValueError("Cho selection cell differs from its external pin")
        metrics = _mapping(cell_payload["metrics"], "Cho selection cell metrics")
        if metrics.get("selection_evidence_sha256") != pin.selection_evidence_sha256:
            raise ValueError("Cho cell selection digest differs from its external pin")
        path = _evidence_path(project_root, metrics.get("selection_evidence_path"))
        if path.name.endswith(".factored.json"):
            read_physical(path, MAXIMUM_PACKED_BYTES)
            store = SelectedSourceStore(project_root, directory=path.parent.parent)
            evidence = store.read_persisted_evidence(
                path, expected_evidence_sha256=pin.selection_evidence_sha256,
            )
            read_physical(path, MAXIMUM_PACKED_BYTES)
        else:
            evidence = read_physical(path, MAXIMUM_LOGICAL_BYTES)
        payload = _logical_record(evidence, pin)
        claims.append(_case_claims(
            payload, metrics, pin, route, protocol_sha256, expected_source,
            method_config_sha256, ceiling=ceiling,
        ))
    return ChoSelectionFileWitness(
        tuple((path, limit, digest, identity)
              for path, (limit, digest, identity) in physical.items()),
        tuple(claims),
    )


def verify_cho51_recorded_selection_files(
    route: Cho51WorkerRoute, recorder: CaseRecorder,
    pins: Sequence[PinnedCaseCell], *, project_root: Path,
    expected_source: SourceProvenance, method_config_sha256: Mapping[str, str],
    selection_ceiling_config_sha256: str,
) -> Cho51SelectionFileWitness:
    """Bind all 1,020 retained cells to selection claims without reading scores.

    Independent source/method/cell/ceiling pins must originate outside the
    writable recorder. The adopted scope is rederived with all 52 sources.
    Real assets, ledger completion, fold/step evidence, publications, tensors
    and scientific admission require their own checks. This function writes
    nothing and starts no model, child, worker, attempt or selection process.
    """
    if (
        not isinstance(project_root, Path) or not project_root.is_absolute()
        or project_root.resolve() != project_root or not project_root.is_dir()
        or type(route) is not Cho51WorkerRoute or type(recorder) is not CaseRecorder
        or not isinstance(pins, Sequence) or isinstance(pins, (str, bytes))
        or not isinstance(method_config_sha256, Mapping)
    ):
        raise ValueError("direct project, adopted route, recorder and independent pins required")
    output = recorder.output_root
    if (
        not isinstance(output, Path) or not output.is_absolute()
        or output.resolve() != output or output.is_symlink() or not output.is_dir()
        or not output.is_relative_to(project_root / "runs" / "phase2")
        or output == project_root / "runs" / "phase2"
    ):
        raise ValueError("existing direct project runs/phase2 recorder child required")
    pinned, methods = tuple(pins), dict(method_config_sha256)
    verify_case_identity_bindings(
        project_root, route, pinned,
        method_config_sha256=methods, expected_source=expected_source,
    )
    ceiling = load_selection_ceiling(
        project_root, expected_sha256=selection_ceiling_config_sha256,
    )
    selection_files = _verify_selection_files(
        route._full_route, recorder, pinned, project_root=project_root,
        expected_source=expected_source, method_config_sha256=methods,
        ceiling=ceiling.maximum_gradient_steps,
    )
    witness = Cho51SelectionFileWitness(
        selection_files, ceiling, route.contract.owner_decision_sha256,
    )
    witness.verify_stable()
    return witness
