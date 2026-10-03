"""Bounded Cho engineering execution, with staged child output and parent release.

Plan mode never imports a tensor runtime or admits compute. Execution requires
external byte pins, fresh operator admission, and an explicitly supplied probe
memory cap. Source selection, publication and target prediction all occur in one
supervised Windows Job. Only a timely, independently verified child proposal may
be promoted into the canonical recorder. Analysis is a separate, unwired phase.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import tempfile
import time
import tomllib
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from core.config import canonical_config_json, config_digest
from core.provenance import capture_source
from evaluation.phase2_supervision_primitives import (
    GIB,
    MAX_ATTEMPT_SECONDS,
    MAX_SESSION_SECONDS,
    DeadlineLease,
    ResourceFloor,
    ResourceSample,
    SupervisionError,
    SupervisionResult,
    live_resources,
    run_supervised,
)

PIN_SCHEMA = "cho_engineering_execution_pins_v1"
METHODS = ("labram_linear", "labram_lora", "labram_full", "eegnet")
SEEDS = (11, 23, 37, 53, 71)
SUBJECTS = tuple(f"subject_{index:02d}" for index in range(1, 53))
INITIAL_PROBE_MAX_MEMORY_BYTES = 6 * GIB
LAUNCH_RAM_BYTES = 10 * GIB
ANALYSIS_MEMORY_BYTES = 5905580032
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_MAX_JSON_BYTES = 16 * 1024**2


def require_sha(value: object, name: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ValueError(f"{name} requires an independently provided lowercase SHA-256")
    return value


def direct_path(root: Path, relative: str) -> Path:
    """Resolve a simple project-relative path without following any link."""
    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative:
        raise ValueError("path must be a simple project-relative POSIX path")
    parts = relative.split("/")
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        raise ValueError("path must stay inside its root")
    current = root
    for part in parts:
        current /= part
        if current.is_symlink():
            raise ValueError("execution path cannot contain links")
    if current.resolve() != current or not current.is_relative_to(root):
        raise ValueError("execution path aliases or escapes its root")
    return current


def stable_bytes(path: Path, *, maximum: int = _MAX_JSON_BYTES) -> bytes:
    """Read one bounded regular file and compare path/descriptor identities."""
    if path.is_symlink() or not path.is_file() or path.resolve() != path:
        raise ValueError("pinned file is absent or aliases another path")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= maximum:
        raise ValueError("pinned file link count or byte size differs")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(maximum + 1)
        finished = os.fstat(stream.fileno())
    after = path.stat()

    def identity(stat: os.stat_result) -> tuple[int, int, int, int]:
        return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns

    if (
        len(raw) != before.st_size
        or len(raw) > maximum
        or identity(before) != identity(opened)
        or identity(opened) != identity(finished)
        or identity(finished) != identity(after)
        or path.is_symlink()
        or after.st_nlink != 1
    ):
        raise ValueError("pinned file changed during its bounded descriptor read")
    return raw


def pinned_bytes(path: Path, expected: str) -> bytes:
    require_sha(expected, "file pin")
    raw = stable_bytes(path)
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"pinned file bytes differ: {path.name}")
    return raw


def fresh_record(path: Path, payload: Mapping[str, Any]) -> None:
    """Publish complete canonical bytes atomically; even same-byte reuse refuses."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.resolve() != path.parent or path.is_symlink():
        raise ValueError("receipt path aliases another path")
    raw = (canonical_config_json(payload) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=".cho-execution-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary)


@dataclass(frozen=True, slots=True)
class EngineeringCase:
    method: str
    subject: str
    seed: int

    def __post_init__(self) -> None:
        if self.method not in METHODS or self.subject not in SUBJECTS or self.seed not in SEEDS:
            raise ValueError("case is outside the pinned Cho five-shot first tranche")


@dataclass(frozen=True, slots=True)
class ExecutionLimits:
    """Initial probe cap is explicit and uncalibrated; it never auto-increases."""

    process_memory_limit_bytes: int
    attempt_seconds: float
    session_seconds: float
    torch_threads: int

    def __post_init__(self) -> None:
        if (
            type(self.process_memory_limit_bytes) is not int
            or not 0 < self.process_memory_limit_bytes <= INITIAL_PROBE_MAX_MEMORY_BYTES
            or type(self.torch_threads) is not int
            or not 1 <= self.torch_threads <= 32
            or isinstance(self.attempt_seconds, bool)
            or isinstance(self.session_seconds, bool)
            or not math.isfinite(self.attempt_seconds)
            or not math.isfinite(self.session_seconds)
            or not 0 < self.attempt_seconds <= MAX_ATTEMPT_SECONDS
            or not self.attempt_seconds <= self.session_seconds <= MAX_SESSION_SECONDS
        ):
            raise ValueError(
                "execution limits exceed the explicit initial engineering probe policy"
            )


@dataclass(frozen=True, slots=True)
class VerifiedStagedProposal:
    identity: Any
    metrics: Mapping[str, Any]
    proposal_file_sha256: str
    cell_file_sha256: str


def select_cases(
    *,
    method: str | None,
    subject: str | None,
    seed: int | None,
    case_limit: int | None,
) -> tuple[EngineeringCase, ...]:
    """A complete triplet selects one case; every broader roster needs a bound."""
    if method is not None and method not in METHODS:
        raise ValueError("unknown Cho method")
    if subject is not None and subject not in SUBJECTS:
        raise ValueError("unknown Cho subject")
    if seed is not None and seed not in SEEDS:
        raise ValueError("unknown Cho seed")
    complete = all(value is not None for value in (method, subject, seed))
    if not complete and case_limit is None:
        raise ValueError("supply --method --subject --seed together or an explicit --case-limit")
    if case_limit is not None and (type(case_limit) is not int or not 1 <= case_limit <= 1040):
        raise ValueError("case limit must be an integer from 1 to 1040")
    plans = tuple(
        EngineeringCase(m, s, n)
        for s in SUBJECTS
        for m in METHODS
        for n in SEEDS
        if (method is None or m == method)
        and (subject is None or s == subject)
        and (seed is None or n == seed)
    )
    return plans if case_limit is None else plans[:case_limit]


def load_execution_pins(root: Path, pins_path: Path, expected_sha256: str) -> dict[str, Any]:
    """Verify caller-reviewed byte/config pins without importing torch or models."""
    root = root.resolve(strict=True)
    if pins_path.resolve() != pins_path or not pins_path.is_relative_to(root):
        raise ValueError("pins file must be a direct project file")
    pins = json.loads(pinned_bytes(pins_path, expected_sha256))
    expected_fields = {
        "schema",
        "source_sha256",
        "environment_sha256",
        "base_config_sha256",
        "route",
        "candidate_config_path",
        "candidate_config_sha256",
        "method_config_sha256",
        "selection_ceiling_config_sha256",
        "sweep_config_sha256",
    }
    if not isinstance(pins, dict) or set(pins) != expected_fields or pins["schema"] != PIN_SCHEMA:
        raise ValueError("execution pin record differs from its explicit schema")
    for field in expected_fields - {
        "schema",
        "route",
        "candidate_config_path",
        "method_config_sha256",
    }:
        require_sha(pins[field], field)
    route_fields = {
        "protocol_config_sha256",
        "threshold_config_sha256",
        "cohort_audit_sha256",
        "variant_config_sha256",
    }
    if not isinstance(pins["route"], dict) or set(pins["route"]) != route_fields:
        raise ValueError("complete externally pinned route digests are required")
    for field, value in pins["route"].items():
        require_sha(value, field)
    method_pins = pins["method_config_sha256"]
    if not isinstance(method_pins, dict) or set(method_pins) != set(METHODS):
        raise ValueError("all four independently reviewed method digests are required")
    for field, value in method_pins.items():
        require_sha(value, field)
    candidates = json.loads(
        pinned_bytes(
            direct_path(root, pins["candidate_config_path"]),
            pins["candidate_config_sha256"],
        )
    )
    rows = candidates.get("methods") if isinstance(candidates, dict) else None
    if not isinstance(rows, list) or len(rows) != 4:
        raise ValueError("candidate file must declare the four static method objects")
    methods = {row.get("method"): row for row in rows if isinstance(row, dict)}
    if set(methods) != set(METHODS) or any(
        config_digest(methods[method]) != method_pins[method] for method in METHODS
    ):
        raise ValueError("static method objects differ from independently supplied digests")
    pinned_bytes(root / "configs/phase2/protocol.toml", pins["route"]["protocol_config_sha256"])
    pinned_bytes(root / "configs/base.toml", pins["base_config_sha256"])
    ceiling_bytes = pinned_bytes(
        root / "configs/phase2/selection_ceiling.toml", pins["selection_ceiling_config_sha256"]
    )
    sweep_bytes = pinned_bytes(root / "configs/phase2/cho_sweep.toml", pins["sweep_config_sha256"])
    ceiling = tomllib.loads(ceiling_bytes.decode("utf-8"))
    if (
        type(ceiling.get("maximum_gradient_steps")) is not int
        or ceiling["maximum_gradient_steps"] != 5253
    ):
        raise ValueError("execution must preserve the 5,253-step engineering ceiling")
    sweep = tomllib.loads(sweep_bytes.decode("utf-8"))
    analysis = sweep.get("analysis")
    if (
        not isinstance(analysis, dict)
        or analysis.get("memory_limit_bytes") != ANALYSIS_MEMORY_BYTES
    ):
        raise ValueError("execution cannot alter the separate 5.5 GiB analysis cap")
    if capture_source(root).source_sha256 != pins["source_sha256"]:
        raise ValueError("live source differs from the independently reviewed execution source")
    return pins


def method_configs(root: Path, pins: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    raw = json.loads(
        pinned_bytes(
            direct_path(root, pins["candidate_config_path"]),
            pins["candidate_config_sha256"],
        )
    )
    return {row["method"]: row for row in raw["methods"]}


def _resources(root: Path, *, launching: bool) -> ResourceSample:
    sample = live_resources(root)
    floor = ResourceFloor()
    minimum_ram = LAUNCH_RAM_BYTES if launching else floor.ram_bytes
    if sample.free_disk_bytes < floor.disk_bytes or sample.available_ram_bytes < minimum_ram:
        raise SupervisionError("10 GiB launch / 4 GiB active RAM or 20 GiB disk floor refused")
    return sample


def _runtime(threads: int, expected_environment: str) -> None:
    import torch

    from evaluation.phase2_runner import environment_digest

    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)
    if environment_digest() != expected_environment:
        raise ValueError("configured runtime differs from the external environment pin")


def _require_capped_job(memory_limit: int) -> None:
    """Refuse direct unsupervised invocation before importing a training runtime."""
    import ctypes
    from ctypes import wintypes

    from evaluation.phase2_supervision_primitives import (
        JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
        JOB_OBJECT_LIMIT_PROCESS_MEMORY,
        _ExtendedLimit,
    )

    if sys.platform != "win32":
        raise SupervisionError("child requires a capped Windows Job Object")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    query = kernel.QueryInformationJobObject
    query.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    query.restype = wintypes.BOOL
    limits = _ExtendedLimit()
    if (
        not query(
            None,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
            None,
        )
        or limits.BasicLimitInformation.LimitFlags
        != JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_PROCESS_MEMORY
        or limits.ProcessMemoryLimit != memory_limit
    ):
        raise SupervisionError("child is not inside the exact capped kill-on-close Job")


def _contract_guard(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    lease = DeadlineLease.load(direct_path(root, contract["deadline_path"]))
    if datetime.now(UTC) >= min(lease.attempt_deadline_utc, lease.session_deadline_utc):
        raise SupervisionError("whole-case attempt/session deadline expired")
    pins = load_execution_pins(
        root, direct_path(root, contract["pins_path"]), contract["pins_sha256"]
    )
    if (
        contract.get("source_sha256") != pins["source_sha256"]
        or contract.get("environment_sha256") != pins["environment_sha256"]
        or contract.get("source") != asdict(capture_source(root))
    ):
        raise ValueError("whole-case contract source/environment differs from external pins")
    admission_raw = pinned_bytes(
        direct_path(root, contract["admission_path"]), contract["admission_sha256"],
    )
    verify_fresh_admission(admission_raw, limits=contract["limits"])
    _resources(root, launching=False)
    refreshed_admission = pinned_bytes(
        direct_path(root, contract["admission_path"]), contract["admission_sha256"],
    )
    if refreshed_admission != admission_raw:
        raise ValueError("whole-case admission bytes changed during the final resource read")
    refreshed_pins = load_execution_pins(
        root, direct_path(root, contract["pins_path"]), contract["pins_sha256"],
    )
    if refreshed_pins != pins or asdict(capture_source(root)) != contract["source"]:
        raise ValueError("whole-case source/config pins changed during final resource read")
    verify_fresh_admission(refreshed_admission, limits=contract["limits"])
    if (
        datetime.now(UTC) >= min(lease.attempt_deadline_utc, lease.session_deadline_utc)
        or DeadlineLease.load(direct_path(root, contract["deadline_path"])) != lease
    ):
        raise SupervisionError("whole-case deadline expired or changed during guard verification")
    return pins


def verify_fresh_admission(raw: bytes, *, limits: Mapping[str, Any]) -> None:
    """Repeat affirmation and 24h freshness without importing a tensor runtime."""
    admission = json.loads(raw)
    if (
        not isinstance(admission, dict)
        or admission.get("schema") != "cho_first_tranche_sweep_admission_v1"
        or admission.get("admitted") is not True
        or not isinstance(admission.get("operator"), str) or not admission["operator"].strip()
        or not isinstance(admission.get("timestamp_utc"), str)
    ):
        raise ValueError("whole-case admission is not explicitly affirmative")
    timestamp = datetime.fromisoformat(admission["timestamp_utc"])
    if timestamp.tzinfo is None:
        raise ValueError("whole-case admission requires a timezone-aware timestamp")
    age = datetime.now(UTC) - timestamp
    if not timedelta(0) <= age <= timedelta(hours=24):
        raise ValueError("whole-case admission expired or is future-dated")
    for field, proposed, cap in (
        ("probe_cap_minutes", limits["attempt_seconds"] / 60, 10),
        ("session_cap_minutes", limits["session_seconds"] / 60, 120),
    ):
        admitted = admission.get(field)
        if (
            not isinstance(admitted, (int, float))
            or type(admitted) not in (int, float) or not math.isfinite(admitted)
            or not 0 < admitted <= cap or proposed > admitted
        ):
            raise ValueError("whole-case limits differ from the fresh operator admission")


def run_cho_execution_child(
    root: Path, contract_path: Path, contract_sha256: str
) -> dict[str, Any]:
    """Child-only production path. Its recorder is an unaccepted staging area."""
    contract = json.loads(pinned_bytes(contract_path, contract_sha256))
    if (
        not isinstance(contract, dict)
        or contract.get("schema") != "cho_engineering_child_contract_v1"
    ):
        raise ValueError("child contract schema differs")
    limits = ExecutionLimits(**contract["limits"])
    if (
        direct_path(root, contract["staged_recorder_path"])
        != contract_path.parent / "staged_recorder"
        or direct_path(root, contract["proposal_path"]) != contract_path.parent / "proposal.json"
        or direct_path(root, contract["deadline_path"]) != contract_path.parent / "deadline.json"
    ):
        raise ValueError("child output or deadline is outside this attempt's quarantine")
    _require_capped_job(limits.process_memory_limit_bytes)
    pins = _contract_guard(root, contract)
    _runtime(limits.torch_threads, pins["environment_sha256"])
    from evaluation.phase2_cho_case_inputs import ChoCaseInputPins, prepare_cho_first_tranche
    from evaluation.phase2_cho_sweep import (
        ProductionChoCaseRunner,
        SweepAdmission,
        sweep_admission_snapshot,
    )
    from evaluation.phase2_pilot import TargetCaseExecutor
    from evaluation.phase2_runner import CaseRecorder, method_configuration

    admission = SweepAdmission.load(direct_path(root, contract["admission_path"]))
    if admission.file_sha256 != contract["admission_sha256"]:
        raise ValueError("child admission parsed bytes differ from the parent pin")
    admitted = sweep_admission_snapshot(root, admission)
    route = prepare_cho_first_tranche(root, pins=ChoCaseInputPins(**pins["route"]))
    case = EngineeringCase(**contract["case"])
    plan = next(
        p
        for p in route.plans
        if (p.method, p.target_subject, p.model_seed) == (case.method, case.subject, case.seed)
    )
    methods = method_configs(root, pins)
    for method, config in methods.items():
        if method_configuration(config) != pins["method_config_sha256"][method]:
            raise ValueError("method runtime schema differs from its external pin")
    recorder = CaseRecorder(root, output_root=direct_path(root, contract["staged_recorder_path"]))
    template = None
    if case.method != "eegnet":
        from evaluation.phase2_cho_source_restore import _new_model, prepare_cho_source_restore

        # A selector consumes a plain template. Constructing its LoRA adapter
        # here would inject LoRA twice and change the declared initialization.
        template_plan = replace(plan, method="labram_linear")
        template_config = methods["labram_linear"]
        prepared = prepare_cho_source_restore(
            root=root,
            plan=template_plan,
            method_config=template_config,
            expected_method_config_sha256=pins["method_config_sha256"]["labram_linear"],
            selected_candidate=template_config["candidates"][0]["name"],
        )
        template = _new_model(prepared)
    runner = ProductionChoCaseRunner(
        root=root,
        recorder=recorder,
        protocol_config=json.loads(route.protocol_config_json),
        catalogs=route.catalogs,
        episode_records={
            key: json.loads(value) for key, value in route.episode_records_json.items()
        },
        selection_records={
            key: json.loads(value) for key, value in route.selection_records_json.items()
        },
        profile_assets=route.labram_assets,
        profile_a_manifests={},
        labram_template=template,
        maximum_gradient_steps=5253,
    )
    _contract_guard(root, contract)
    result = runner(
        plan=plan,
        executor=TargetCaseExecutor(
            root,
            recorder,
            admission=admitted["admission"],
            worker=contract["worker"],
        ),
        route=route,
        method_config=methods[case.method],
    )
    _contract_guard(root, contract)
    proposal = {
        "schema": "cho_engineering_child_proposal_v1",
        "contract_sha256": contract_sha256,
        "case": asdict(case),
        "result": dict(result),
        "scientific_claims_made": 0,
        "scientific_freeze_ratified": False,
        "gate_a_signed": False,
    }
    fresh_record(direct_path(root, contract["proposal_path"]), proposal)
    return proposal


def verify_staged_proposal(
    root: Path,
    contract: Mapping[str, Any],
    contract_sha256: str,
) -> VerifiedStagedProposal:
    """Rebuild route and selector/manifest context before accepting staged metrics."""
    pins = _contract_guard(root, contract)
    proposal_path = direct_path(root, contract["proposal_path"])
    proposal_raw = stable_bytes(proposal_path)
    proposal = json.loads(proposal_raw)
    if (
        not isinstance(proposal, dict)
        or proposal.get("schema") != "cho_engineering_child_proposal_v1"
        or proposal.get("contract_sha256") != contract_sha256
        or proposal.get("case") != contract["case"]
        or proposal.get("scientific_claims_made") != 0
        or proposal.get("scientific_freeze_ratified") is not False
        or proposal.get("gate_a_signed") is not False
        or not isinstance(proposal.get("result"), dict)
    ):
        raise ValueError("staged child proposal differs from the parent contract")
    from evaluation.phase2_cho_case_inputs import ChoCaseInputPins, prepare_cho_first_tranche
    from evaluation.phase2_cho_selected_manifest_bridge import verify_cho_selected_manifest_files
    from evaluation.phase2_cho_source_restore import prepare_cho_source_restore
    from evaluation.phase2_cho_sweep import materialize_cho_candidates
    from evaluation.phase2_records import CellIdentity, verify_envelope
    from evaluation.phase2_runner import CaseRecorder, environment_digest
    from evaluation.phase2_selection_evidence_binding import verify_cho_selection_evidence

    route = prepare_cho_first_tranche(root, pins=ChoCaseInputPins(**pins["route"]))
    case = EngineeringCase(**contract["case"])
    plan = next(
        p
        for p in route.plans
        if (p.method, p.target_subject, p.model_seed) == (case.method, case.subject, case.seed)
    )
    inputs = route.inputs_for(plan)
    staging = direct_path(root, contract["staged_recorder_path"])
    recorder = CaseRecorder(root, output_root=staging)
    completed = recorder.completion((plan,))
    if completed["measured"] != 1:
        raise ValueError("staged child case has no fully verified recorder completion")
    cell_path = Path(proposal["result"].get("cell", ""))
    if cell_path.parent != staging / "cells" or cell_path.resolve() != cell_path:
        raise ValueError("proposed cell does not belong to this attempt's staged recorder")
    cell_raw = stable_bytes(cell_path)
    record = json.loads(cell_raw)
    payload = record.get("payload") if isinstance(record, dict) else None
    if not isinstance(payload, dict) or not verify_envelope(
        record,
        kind="evaluation_cell",
        expected_payload=payload,
    ):
        raise ValueError("staged cell envelope no longer verifies")
    identity = CellIdentity(**payload["identity"])
    source = capture_source(root)
    target = next(c for c in route.catalogs if c.subject == case.subject)
    method_config = method_configs(root, pins)[case.method]
    expected_identity = {
        "dataset": "cho2017",
        "method": case.method,
        "target_subject": case.subject,
        "shots_per_class": 5,
        "model_seed": case.seed,
        "support_draw_seed": None,
        "montage_seed": None,
        "source_sha256": pins["source_sha256"],
        "environment_sha256": pins["environment_sha256"],
        "git_commit": source.git_commit,
        "git_dirty": source.git_dirty,
        "protocol_sha256": config_digest(inputs.protocol_config),
        "episode_sha256": inputs.episode_record["sha256"],
        "selection_sha256": inputs.selection_record["sha256"],
        "preprocessing_sha256": target.preprocessing_sha256,
        "method_config_sha256": pins["method_config_sha256"][case.method],
    }
    if (
        any(getattr(identity, key) != value for key, value in expected_identity.items())
        or cell_path.name != f"{identity.sha256}.json"
        or environment_digest() != pins["environment_sha256"]
    ):
        raise ValueError("staged cell identity differs from independent parent context")
    metrics = payload["metrics"]
    from evaluation.phase2_cho_sweep import _verify_resume_publication, _verify_resume_success

    _verify_resume_success(recorder, record, plan=plan, identity=identity)
    verify_case_target_inputs(
        root=root, route=route, recorder=recorder, record=record,
        plan=plan, identity=identity, base_config_sha256=pins["base_config_sha256"],
    )

    _verify_resume_publication(
        root,
        record,
        plan=plan,
        route=route,
        method_config=method_config,
        identity=identity,
        pins={**asdict(source), "environment_sha256": pins["environment_sha256"]},
    )
    evidence_sha = require_sha(metrics.get("selection_evidence_sha256"), "selection evidence")
    evidence_path = direct_path(root, metrics["selection_evidence_path"])
    evidence = json.loads(stable_bytes(evidence_path, maximum=256 * 1024**2))
    selected = evidence.get("payload", {}).get("selected_candidate")
    candidates = materialize_cho_candidates(case.method, method_config, case.seed)
    winner = next(c for c in candidates if c.name == selected)
    verified = verify_cho_selection_evidence(
        record=evidence,
        evidence_sha256=evidence_sha,
        plan=plan,
        protocol_config=inputs.protocol_config,
        catalogs=route.catalogs,
        selection_record=inputs.selection_record,
        root=root,
        adapter_model_state_sha256=identity.checkpoint_sha256,
        adapter_source_settings=asdict(winner.source),
        adapter_support_settings=asdict(winner.support),
        assets=inputs.assets,
    )
    prepared = prepare_cho_source_restore(
        root=root,
        plan=plan,
        method_config=method_config,
        expected_method_config_sha256=identity.method_config_sha256,
        selected_candidate=verified.selected_candidate,
    )
    manifest_sha = require_sha(metrics.get("selected_source_manifest_sha256"), "source manifest")
    manifest_path = direct_path(root, metrics["selected_source_manifest_path"])
    witness = verify_cho_selected_manifest_files(
        root,
        manifest_path,
        manifest_sha256=manifest_sha,
        evidence_sha256=evidence_sha,
        selection_contract_sha256=config_digest(evidence["payload"]["contract"]),
        selected_candidate=verified.selected_candidate,
        protocol_config_sha256=identity.protocol_sha256,
        expected_source=source,
        model_recipe_sha256=config_digest(prepared.model_recipe),
        model_state_sha256=identity.checkpoint_sha256,
    )
    if (
        proposal["result"].get("selection_evidence_sha256") != evidence_sha
        or proposal["result"].get("selected_manifest_sha256") != manifest_sha
        or proposal["result"].get("selected_weights_sha256") != witness.weights_sha256
    ):
        raise ValueError("child proposal selected-source pins differ from verified physical files")
    witness.verify_stable()
    if stable_bytes(proposal_path) != proposal_raw or stable_bytes(cell_path) != cell_raw:
        raise ValueError("staged proposal or cell bytes changed during parent verification")
    _contract_guard(root, contract)
    return VerifiedStagedProposal(
        identity, metrics, hashlib.sha256(proposal_raw).hexdigest(),
        hashlib.sha256(cell_raw).hexdigest(),
    )


def supervise_attempt(
    *,
    root: Path,
    attempt_dir: Path,
    contract: Mapping[str, Any],
    contract_sha256: str,
    command: Sequence[str],
    accept: Callable[[], Mapping[str, Any]],
    supervisor: Callable[..., SupervisionResult] = run_supervised,
) -> dict[str, Any]:
    """Persist all terminal paths; invoke parent acceptance only on normal exit."""
    started = time.monotonic()
    result: SupervisionResult | None = None
    accepted: Mapping[str, Any] | None = None
    status = "stopped"
    reason = "supervision_not_started"
    error_text: str | None = None
    try:
        _resources(root, launching=True)
        fresh_record(
            attempt_dir / "started.json",
            {
                "schema": "cho_engineering_execution_attempt_start_v1",
                "contract_sha256": contract_sha256,
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "source_sha256": contract.get("source_sha256"),
            },
        )
        result = supervisor(
            command,
            cwd=root,
            deadline_path=direct_path(root, contract["deadline_path"]),
            floor=ResourceFloor(),
            process_memory_limit_bytes=contract["limits"]["process_memory_limit_bytes"],
        )
        reason = result.reason
        if result.reason == "normal" and result.exit_code == 0:
            if result.peak_process_memory_bytes is None or result.peak_job_memory_bytes is None:
                raise SupervisionError("bounded child peak measurements are unavailable")
            accepted = accept()
            status, reason = "complete", "timely_parent_attestation"
        elif result.reason == "normal":
            status, reason = "failed", "child_nonzero_exit"
    except Exception as error:  # noqa: BLE001 - terminal evidence must survive every refusal
        error_text = f"{type(error).__name__}: {error}"
        reason = "supervision_or_attestation_refused"
    child_failure: dict[str, Any] | None = None
    failure_path = attempt_dir / "child_failure.json"
    if failure_path.exists():
        try:
            failure_raw = stable_bytes(failure_path, maximum=64 * 1024)
            parsed = json.loads(failure_raw)
            if isinstance(parsed, dict) and parsed.get("contract_sha256") == contract_sha256:
                child_failure = {
                    "record": parsed,
                    "file_sha256": hashlib.sha256(failure_raw).hexdigest(),
                }
        except (OSError, ValueError):
            child_failure = {"error": "child failure record does not verify"}
    receipt = {
        "schema": "cho_engineering_execution_attempt_v1",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "contract_sha256": contract_sha256,
        "contract_config_sha256": config_digest(contract),
        "contract": dict(contract),
        "status": status,
        "reason": reason,
        "error": error_text,
        "elapsed_seconds": time.monotonic() - started,
        "supervision": None if result is None else asdict(result),
        "child_failure": child_failure,
        "accepted": None if accepted is None else dict(accepted),
        "peak_measurement_available": result is not None
        and result.peak_process_memory_bytes is not None,
        "execution_cap_calibration": (
            "initial_unmeasured_engineering_probe; no production cap ratified"
        ),
        "memory_limit_scope": "per_process_commit; job peak measured separately",
        "staged_outputs_accepted": status == "complete",
        "staged_outputs_quarantined": status != "complete",
        "durable_parent_attestation_present": (attempt_dir / "accepted.json").is_file(),
        "recovery_or_quarantine_required": (
            status != "complete" and (attempt_dir / "accepted.json").is_file()
        ),
        "engineering_cell_count": int(status == "complete"),
        "analysis_memory_limit_bytes": ANALYSIS_MEMORY_BYTES,
        "scientific_claims_made": 0,
        "scientific_freeze_ratified": False,
        "gate_a_signed": False,
    }
    fresh_record(attempt_dir / "receipt.json", receipt)
    return receipt


def prepare_attempt(
    *, root: Path, attempt_dir: Path, context: Mapping[str, Any], case: EngineeringCase,
    limits: ExecutionLimits, session_deadline: datetime, session_monotonic_deadline: float,
) -> tuple[dict[str, Any], str, list[str], float]:
    """Create immutable attempt inputs inside the caller's terminal-handled path."""
    now = datetime.now(UTC)
    if now >= session_deadline or time.monotonic() >= session_monotonic_deadline:
        raise SupervisionError("session expired before attempt setup")
    deadline_path = attempt_dir / "deadline.json"
    lease = DeadlineLease.open_or_create(
        deadline_path,
        attempt_deadline_utc=min(now + timedelta(seconds=limits.attempt_seconds), session_deadline),
        session_deadline_utc=session_deadline,
    )
    monotonic_deadline = min(
        session_monotonic_deadline,
        time.monotonic() + (lease.attempt_deadline_utc - datetime.now(UTC)).total_seconds(),
    )
    contract = {
        **dict(context), "schema": "cho_engineering_child_contract_v1",
        "case": asdict(case), "limits": asdict(limits),
        "deadline_path": deadline_path.relative_to(root).as_posix(),
        "staged_recorder_path": (attempt_dir / "staged_recorder").relative_to(root).as_posix(),
        "proposal_path": (attempt_dir / "proposal.json").relative_to(root).as_posix(),
    }
    contract_path = attempt_dir / "contract.json"
    fresh_record(contract_path, contract)
    contract_sha = hashlib.sha256(stable_bytes(contract_path)).hexdigest()
    command = [sys.executable, "-B", str(root / "scripts/run_cho_execution_child.py"),
               "--contract", str(contract_path), "--contract-sha256", contract_sha]
    return contract, contract_sha, command, monotonic_deadline


def execute_engineering_cases(
    *,
    root: Path,
    pins_path: Path,
    pins_sha256: str,
    admission_path: Path,
    receipt_path: Path,
    cases: tuple[EngineeringCase, ...],
    limits: ExecutionLimits,
    worker: str,
    attempt: int = 1,
) -> dict[str, Any]:
    """Run a bounded sequential session; a shared stop never starts another case."""
    if sys.platform != "win32":
        raise SupervisionError("engineering execution requires Windows Job supervision")
    if attempt not in (1, 2) or not worker.strip() or not cases:
        raise ValueError("one initial attempt or one explicitly requested retry is required")
    root = root.resolve(strict=True)
    if receipt_path.resolve() != receipt_path or not receipt_path.is_relative_to(
        root / "runs/phase2/sweeps"
    ):
        raise ValueError("session receipt must be a direct path under runs/phase2/sweeps")
    if receipt_path.exists():
        raise FileExistsError("session receipt already exists")
    pins = load_execution_pins(root, pins_path, pins_sha256)
    if admission_path.resolve() != admission_path or not admission_path.is_relative_to(root):
        raise ValueError("operator admission must be a direct project file")
    admission_raw = stable_bytes(admission_path)
    admission_sha = hashlib.sha256(admission_raw).hexdigest()
    _resources(root, launching=True)
    _runtime(limits.torch_threads, pins["environment_sha256"])
    from evaluation.phase2_cho_sweep import SweepAdmission, sweep_admission_snapshot
    from evaluation.phase2_runner import CasePlan, CaseRecorder

    admission = SweepAdmission.load(admission_path)
    if admission.file_sha256 != admission_sha:
        raise ValueError("parent admission parsed bytes changed since the bounded read")
    if (
        limits.attempt_seconds > admission.probe_cap_minutes * 60
        or limits.session_seconds > admission.session_cap_minutes * 60
    ):
        raise ValueError("CLI limits exceed persisted operator admission")
    sweep_admission_snapshot(root, admission)
    source_snapshot = asdict(capture_source(root))
    if source_snapshot["source_sha256"] != pins["source_sha256"]:
        raise ValueError("source changed before creating the bounded session")
    if (
        type(source_snapshot["git_dirty"]) is not bool
        or not isinstance(source_snapshot["git_commit"], str)
        or len(source_snapshot["git_commit"]) not in (40, 64)
    ):
        raise ValueError(
            "engineering execution requires a real Git identity and explicit dirty state"
        )
    session_dir = receipt_path.parent / f"{receipt_path.stem}.session"
    session_dir.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    session_deadline = datetime.now(UTC) + timedelta(seconds=limits.session_seconds)
    session_monotonic_deadline = started + limits.session_seconds
    session = {
        "schema": "cho_engineering_execution_session_v1",
        "pins_sha256": pins_sha256,
        "source": source_snapshot,
        "environment_sha256": pins["environment_sha256"],
        "admission_sha256": admission_sha,
        "limits": asdict(limits),
        "session_deadline_utc": session_deadline.isoformat(),
        "cases": [asdict(case) for case in cases],
        "worker": worker,
        "attempt": attempt,
        "scientific_claims_made": 0,
    }
    fresh_record(session_dir / "session.json", session)
    recorder = CaseRecorder(root)
    outcomes: list[dict[str, Any]] = []
    stop_reason: str | None = None
    context = {
        "pins_path": pins_path.relative_to(root).as_posix(), "pins_sha256": pins_sha256,
        "source_sha256": pins["source_sha256"], "source": source_snapshot,
        "environment_sha256": pins["environment_sha256"],
        "admission_path": admission_path.relative_to(root).as_posix(),
        "admission_sha256": admission_sha, "worker": worker,
    }
    for index, case in enumerate(cases):
        if datetime.now(UTC) >= session_deadline or time.monotonic() >= session_monotonic_deadline:
            stop_reason = "session_deadline_before_next_case"
            break
        plan = CasePlan("cho2017", case.subject, case.method, 5, case.seed, 1)
        attempt_dir = session_dir / f"case_{index + 1:04d}"
        contract: dict[str, Any] = {**context, "case": asdict(case)}
        contract_sha: str | None = None
        claim_started = False
        try:
            attempt_dir.mkdir()
            contract, prepared_contract_sha, command, attempt_monotonic_deadline = prepare_attempt(
                root=root, attempt_dir=attempt_dir, context=context, case=case, limits=limits,
                session_deadline=session_deadline,
                session_monotonic_deadline=session_monotonic_deadline,
            )
            contract_sha = prepared_contract_sha
            with recorder.case_session(plan) as locked:
                # This driver deliberately refuses implicit resume/reuse. The
                # recorder's fresh claim and one-retry discipline remain the authority.
                _contract_guard(root, contract)
                locked.claim_new(worker=worker, attempt=attempt)
                claim_started = True

                def accept(
                    pinned_contract: Mapping[str, Any] = contract,
                    pinned_contract_sha: str = prepared_contract_sha,
                    owned_attempt_dir: Path = attempt_dir,
                    owned_locked: Any = locked,
                    owned_plan: Any = plan,
                    owned_monotonic_deadline: float = attempt_monotonic_deadline,
                ) -> Mapping[str, Any]:
                    if time.monotonic() >= owned_monotonic_deadline:
                        raise SupervisionError("parent whole-case monotonic deadline expired")
                    verified_proposal = verify_staged_proposal(
                        root,
                        pinned_contract,
                        pinned_contract_sha,
                    )
                    identity, metrics = verified_proposal.identity, verified_proposal.metrics
                    _contract_guard(root, pinned_contract)
                    verify_parent_claim(
                        recorder,
                        owned_plan,
                        identity,
                        attempt=attempt,
                        expected_source=pinned_contract["source"],
                    )
                    if time.monotonic() >= owned_monotonic_deadline:
                        raise SupervisionError("parent verification crossed whole-case deadline")
                    attestation = {
                        "schema": "cho_engineering_parent_attestation_v1",
                        "contract_sha256": pinned_contract_sha,
                        "identity": asdict(identity),
                        "metrics_sha256": config_digest(metrics),
                        "proposal_file_sha256": verified_proposal.proposal_file_sha256,
                        "staged_cell_file_sha256": verified_proposal.cell_file_sha256,
                        "timestamp_utc": datetime.now(UTC).isoformat(),
                        "scientific_claims_made": 0,
                    }
                    fresh_record(owned_attempt_dir / "accepted.json", attestation)
                    _contract_guard(root, pinned_contract)
                    if time.monotonic() >= owned_monotonic_deadline:
                        raise SupervisionError("parent attestation crossed whole-case deadline")
                    cell = owned_locked.record_cell(identity, metrics=metrics)
                    return {
                        "cell": str(cell),
                        "parent_attestation_sha256": config_digest(attestation),
                    }

                receipt = supervise_attempt(
                    root=root,
                    attempt_dir=attempt_dir,
                    contract=contract,
                    contract_sha256=contract_sha,
                    command=command,
                    accept=accept,
                )
                record_stopped_attempt(
                    locked,
                    receipt,
                    attempt=attempt,
                    receipt_relative=(attempt_dir / "receipt.json").relative_to(root).as_posix(),
                )
        except Exception as error:  # noqa: BLE001 - claim/receipt conflict also stops the session
            durable = has_durable_publication(recorder, plan, attempt_dir)
            failure_link_error: str | None = None
            if claim_started and not durable:
                try:
                    with recorder.case_session(plan) as recovery_locked:
                        durable = has_durable_publication(recorder, plan, attempt_dir)
                        if not durable:
                            recovery_locked.record_failure(attempt=attempt, reason={
                                "stage": "whole_case_terminal_handling",
                                "error": f"{type(error).__name__}: {error}",
                                "attempt_receipt": (attempt_dir / "receipt.json")
                                .relative_to(root)
                                .as_posix(),
                            })
                except Exception as link_error:  # noqa: BLE001 - never hide failed failure persistence
                    failure_link_error = f"{type(link_error).__name__}: {link_error}"
            if attempt_dir.is_dir() and not (attempt_dir / "receipt.json").exists():
                fresh_record(
                    attempt_dir / "receipt.json",
                    {
                        "schema": "cho_engineering_execution_attempt_v1",
                        "status": "stopped" if claim_started else "not_attempted",
                        "reason": f"{type(error).__name__}: {error}",
                        "contract": contract,
                        "contract_sha256": contract_sha,
                        "engineering_cell_count": 0,
                        "staged_outputs_accepted": False,
                        "staged_outputs_quarantined": True,
                        "durable_parent_attestation_present": (
                            attempt_dir / "accepted.json"
                        ).is_file(),
                        "recovery_or_quarantine_required": (
                            durable or failure_link_error is not None
                        ),
                        "canonical_failure_link_error": failure_link_error,
                        "peak_measurement_available": False,
                        "supervision": None,
                        "scientific_claims_made": 0,
                        "scientific_freeze_ratified": False,
                        "gate_a_signed": False,
                    },
                )
            outcomes.append(
                {
                    "case": asdict(case),
                    "status": "stopped" if claim_started else "not_attempted",
                    "reason": f"{type(error).__name__}: {error}",
                }
            )
            stop_reason = f"{type(error).__name__}: {error}"
            break
        outcomes.append(
            {
                "case": asdict(case),
                "status": receipt["status"],
                "receipt": (attempt_dir / "receipt.json").relative_to(root).as_posix(),
            }
        )
        if receipt["status"] != "complete":
            stop_reason = receipt["reason"]
            break
    receipt = {
        "schema": "cho_engineering_bounded_session_receipt_v1",
        "session": session,
        "elapsed_seconds": time.monotonic() - started,
        "outcomes": outcomes,
        "planned_cases": len(cases),
        "completed_cases": sum(o["status"] == "complete" for o in outcomes),
        "not_attempted_cases": len(cases) - sum(o["status"] != "not_attempted" for o in outcomes),
        "attempted_cases": sum(o["status"] != "not_attempted" for o in outcomes),
        "stop_reason": stop_reason,
        "analysis_executed": False,
        "engineering_cell_count": sum(o["status"] == "complete" for o in outcomes),
        "scientific_claims_made": 0,
        "scientific_freeze_ratified": False,
        "gate_a_signed": False,
    }
    fresh_record(receipt_path, receipt)
    return receipt


def has_durable_publication(recorder: Any, plan: Any, attempt_dir: Path) -> bool:
    """Any durable parent attestation or canonical intent/success prevents blind retry."""
    return any(path.exists() or path.is_symlink() for path in (
        attempt_dir / "accepted.json",
        recorder.output_root / "publication_intents" / f"{plan.case_id}.intent.json",
        recorder.output_root / "successes" / f"{plan.case_id}.success.json",
    ))


def record_stopped_attempt(
    locked: Any,
    receipt: Mapping[str, Any],
    *,
    attempt: int,
    receipt_relative: str,
) -> bool:
    """Link a plain failure; durable parent attestations require deliberate recovery."""
    if receipt["status"] == "complete" or receipt["recovery_or_quarantine_required"]:
        return False
    locked.record_failure(
        attempt=attempt,
        reason={
            "stage": "whole_case_supervision",
            "error": receipt["error"] or receipt["reason"],
            "reason": receipt["reason"],
            "attempt_receipt": receipt_relative,
        },
    )
    return True


def verify_parent_claim(
    recorder: Any,
    plan: Any,
    identity: Any,
    *,
    attempt: int,
    expected_source: Mapping[str, Any],
) -> None:
    """Verify the parent's bounded final claim against accepted cell provenance."""
    from evaluation.phase2_cell_aggregation_bridge import MAX_RECEIPT_BYTES, _canonical_record
    from evaluation.phase2_records import verify_envelope

    record, _ = _canonical_record(
        recorder.output_root / "claims" / f"{plan.case_id}.attempt{attempt}.claim.json",
        maximum_bytes=MAX_RECEIPT_BYTES,
    )
    payload = record.get("payload")
    if (
        not isinstance(payload, dict)
        or set(payload)
        != {
            "purpose",
            "case",
            "worker",
            "attempt",
            "environment_sha256",
            "source",
            "engineering_only",
        }
        or payload.get("purpose") != "pilot_case_claim"
        or not isinstance(payload.get("worker"), str) or not payload["worker"].strip()
        or payload.get("case") != asdict(plan)
        or type(payload.get("attempt")) is not int
        or payload.get("attempt") != attempt
        or payload.get("engineering_only") is not True
        or payload.get("source") != dict(expected_source)
        or not isinstance(payload.get("source"), dict)
        or payload["source"].get("git_dirty") is not identity.git_dirty
        or payload.get("source")
        != {
            "git_commit": identity.git_commit,
            "git_dirty": identity.git_dirty,
            "source_sha256": identity.source_sha256,
        }
        or payload.get("environment_sha256") != identity.environment_sha256
        or not verify_envelope(record, kind="engineering_smoke", expected_payload=payload)
    ):
        raise ValueError("parent final claim provenance differs from the accepted cell identity")


def verify_case_target_inputs(
    *, root: Path, route: Any, recorder: Any, record: Mapping[str, Any],
    plan: Any, identity: Any, base_config_sha256: str,
) -> None:
    """Apply the typed analysis bridge's route-derived checks to one staged cell."""
    from evaluation.phase2_cell_aggregation_bridge import MAX_RECEIPT_BYTES, PinnedCaseCell
    from evaluation.phase2_cho_persisted_target import verify_cho_persisted_target_declarations
    from evaluation.phase2_cho_target_input_bridge import _profile_a, _profile_b, _query_metrics
    from evaluation.phase2_protocol import nested_episode, source_selection
    from evaluation.phase2_subject_aggregation import ExpectedCell
    from scripts.audit_phase2_protocol import validate_protocol

    metrics = record["payload"]["metrics"]
    success_raw = stable_bytes(
        recorder.output_root / "successes" / f"{plan.case_id}.success.json",
        maximum=MAX_RECEIPT_BYTES,
    )
    success = json.loads(success_raw)
    pin = PinnedCaseCell(
        plan, ExpectedCell(*plan.identity_key), identity, success["payload"]["attempt"],
        record["sha256"], hashlib.sha256(success_raw).hexdigest(),
        metrics["selection_evidence_sha256"],
    )
    declarations = verify_cho_persisted_target_declarations(
        root, route, base_config_sha256=base_config_sha256,
    )
    config = json.loads(route.protocol_config_json)
    catalog = next(c for c in route.catalogs if c.subject == plan.target_subject)
    episode = nested_episode(catalog, shots=validate_protocol(config),
                             protocol_sha256=identity.protocol_sha256)
    partition = episode.partition(plan.shots_per_class)
    selection = source_selection(route.catalogs, target=plan.target_subject)
    support_ids = tuple(catalog.trial_ids[index] for index in partition.support_indices)
    query_ids = tuple(catalog.trial_ids[index] for index in partition.query_indices)
    _query_metrics(metrics, catalog, partition.query_indices)
    attestation = metrics.get("target_input_attestation")
    if not isinstance(attestation, Mapping) or any(
        attestation.get(field) != value for field, value in {
            "schema": "cho2017-target-input-v1", "method": plan.method,
            "subject": plan.target_subject, "episode_record_sha256": identity.episode_sha256,
            "profile": "cho_profile_a" if plan.method == "eegnet" else "cho_profile_b_60hz_v1",
        }.items()
    ):
        raise ValueError("staged target attestation differs from the parent case")
    if plan.method == "eegnet":
        _profile_a(attestation, declarations, pin, catalog, episode.sha256, selection.sha256,
                   selection.source_subjects, support_ids, query_ids)
    else:
        _profile_b(attestation, route, declarations, pin, catalog, episode.sha256,
                   support_ids, query_ids)
