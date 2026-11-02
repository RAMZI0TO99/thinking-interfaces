"""Nonnumerical profile contracts; run only under fresh guarded admission."""

from __future__ import annotations

import tomllib
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path
from types import MappingProxyType

import pytest

from core.config import canonical_config_json, config_digest
from core.provenance import capture_source
from docs.phase2.cho51_canonical_boundary_v1 import boundary as Boundary
from docs.phase2.cho51_p3_adapter_v2 import contracts as Contracts
from docs.phase2.cho51_p3_adapter_v2 import mapping as Mapping
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute, from_verified_full_route
from evaluation.phase2_cho_case_inputs import ChoCaseInputPins, ChoFirstTrancheRoute
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan, environment_digest


ROOT = Path(__file__).resolve().parents[3]


def clone(value):
    return Contracts.decode_json(canonical_config_json(value))


def save_json(path, payload):
    if not path.is_relative_to(ROOT):
        raise ValueError("test metadata must remain beneath the actual guarded project root")
    raw = canonical_config_json(payload).encode("utf-8")
    if len(raw) > Contracts.MAX_METADATA_BYTES:
        raise ValueError("test metadata exceeds its bounded file contract")
    path.write_bytes(raw)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": Contracts.sha256(raw)}


def request_for(payload):
    raw = canonical_config_json(payload)
    return Boundary.CanonicalBoundaryRequest(raw, Contracts.sha256(raw.encode("utf-8")))


def intent_for(payload):
    raw = Contracts.canonical_json(payload, maximum=Contracts.MAX_INTENT_BYTES)
    return Contracts.AdapterIntent(raw, Contracts.sha256(raw.encode("utf-8")))


def assess(fixture, intent=None, request=None, full=None, adopted=None):
    return Mapping.assess_adapter_intent(
        fixture["intent"] if intent is None else intent,
        boundary_request=fixture["request"] if request is None else request,
        full_route=fixture["full"] if full is None else full,
        adopted_route=fixture["adopted"] if adopted is None else adopted,
        input_pins=fixture["input_pins"],
    )


@pytest.fixture(scope="module")
def mapping_fixture(tmp_path_factory):
    directory = tmp_path_factory.mktemp("p3-profile-metadata")
    if directory.resolve(strict=True) != directory or not directory.is_relative_to(ROOT):
        raise ValueError("fresh guarded pytest basetemp must be direct and inside the actual project")
    configurations = {
        name: {"path": relative, "sha256": Boundary.CONFIG_SHA256[name]}
        for name, relative in Boundary.CONFIG_PATHS.items()
    }
    config_bytes = {
        name: Boundary.stable_metadata_bytes(ROOT / pin["path"], pin["sha256"])[0]
        for name, pin in configurations.items()
    }
    protocol = tomllib.loads(config_bytes["protocol"].decode("utf-8"))
    threshold = tomllib.loads(config_bytes["threshold"].decode("utf-8"))
    manifest = Contracts.decode_json(Boundary.stable_metadata_bytes(ROOT / Mapping.MANIFEST_PATH, Mapping.MANIFEST_SHA256)[0])
    origin = Contracts.decode_json(Boundary.stable_metadata_bytes(ROOT / Mapping.ORIGIN_PATH, Mapping.ORIGIN_SHA256)[0])["summary"]
    files = manifest["files"]
    preprocessing = config_digest({
        "profile_identity": protocol["preparation"]["profile_identity"],
        "threshold_config_sha256": configurations["threshold"]["sha256"],
        "dataset": "cho2017", "threshold": threshold["datasets"]["cho2017"]["artifact_threshold_volts"],
    })
    trials = tuple(canonical_config_json(["synthetic_session", "synthetic_run", index]) for index in range(manifest["trials_per_subject"]))
    catalogs = tuple(TrialCatalog(
        "cho2017", subject, trials, Boundary.CLASSES * manifest["trials_per_class"],
        Boundary.CLASSES, files[f"data/processed/cho2017/profile_a/{subject}.npz"]["sha256"], preprocessing,
    ) for subject in Boundary.SUBJECTS)
    assets = MappingProxyType({subject: ChoProfileAssets60Hz(
        files[f"data/processed/cho2017/profile_b_60hz_v1/{subject}.npz"]["sha256"],
        files[f"data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json"]["sha256"],
        configurations["variant"]["sha256"],
    ) for subject in Boundary.SUBJECTS})
    metadata = {
        "schema": "cho51_canonical_route_metadata_v1",
        "scope": "externally_supplied_catalog_asset_metadata_unverified",
        "raw_input_bytes_verified": False, "weight_bytes_verified": False,
        "catalogs": [asdict(catalog) for catalog in catalogs],
        "assets": {subject: asdict(asset) for subject, asset in assets.items()},
    }
    metadata_pin = save_json(directory / "route-metadata.json", metadata)
    configurations["cohort"] = save_json(directory / "cohort-origin.json", {
        "schema": "cho51_canonical_metadata_cohort_origin_v1", "metadata_sha256": metadata_pin["sha256"],
        "available_subjects": list(Boundary.SUBJECTS), "raw_input_bytes_verified": False,
    })
    input_pins = ChoCaseInputPins(
        configurations["protocol"]["sha256"], configurations["threshold"]["sha256"],
        configurations["cohort"]["sha256"], configurations["variant"]["sha256"],
    )
    source = asdict(capture_source(ROOT))
    if source["git_commit"] == "unversioned-workspace" or type(source["git_dirty"]) is not bool:
        raise ValueError("genuine current source identity required")
    candidates = Contracts.decode_json(config_bytes["candidates"])
    pins = {
        "schema": "cho_engineering_execution_pins_v1", "source_sha256": source["source_sha256"],
        "environment_sha256": environment_digest(), "base_config_sha256": configurations["base"]["sha256"],
        "route": asdict(input_pins), "candidate_config_path": configurations["candidates"]["path"],
        "candidate_config_sha256": configurations["candidates"]["sha256"],
        "method_config_sha256": {row["method"]: config_digest(row) for row in candidates["methods"]},
        "selection_ceiling_config_sha256": configurations["ceiling"]["sha256"],
        "sweep_config_sha256": configurations["sweep"]["sha256"],
    }
    execution_pin = save_json(directory / "execution-pins.json", pins)
    plans = tuple(CasePlan("cho2017", subject, method, 5, seed, 1) for subject in Boundary.SUBJECTS for method in Boundary.METHODS for seed in Boundary.SEEDS)
    selections = {subject: source_selection(catalogs, target=subject) for subject in Boundary.SUBJECTS}
    full = ChoFirstTrancheRoute(
        plans, catalogs, assets, canonical_config_json(protocol),
        MappingProxyType({subject: canonical_config_json(envelope("source_selection", asdict(selected))) for subject, selected in selections.items()}),
        MappingProxyType({catalog.subject: canonical_config_json(envelope("episode_manifest", nested_episode(catalog, shots=tuple(protocol["protocol"]["shots_per_class"]), protocol_sha256=config_digest(protocol)).payload())) for catalog in catalogs}),
    )
    adopted = from_verified_full_route(ROOT, full)
    evidence = {name: {"path": relative, "sha256": expected} for name, (relative, expected) in Boundary.ANCHORS.items()}
    role_sources = {"producer": origin["historical_source"], "executor": source, "recorder": source}
    role_evidence = {"producer": Mapping.ORIGIN_SHA256, "executor": execution_pin["sha256"], "recorder": evidence["worker_review"]["sha256"]}
    request_payload = {
        "schema": "cho51_canonical_boundary_request_v1", "root": str(ROOT), "execution_pins": execution_pin,
        "metadata": metadata_pin, "configuration": configurations, "evidence": evidence,
        "roles": {name: {"source": role_sources[name], "runtime_identity": {"role": name, "evidence_sha256": role_evidence[name], "fresh_runtime_verification_performed": False}} for name in role_sources},
        "prospective_numerical_budget": dict(Boundary.PROSPECTIVE_BUDGET),
    }
    request = request_for(request_payload)
    boundary_assessment = Boundary.assess_metadata(request, full_route=full, adopted_route=adopted, input_pins=input_pins)
    intent_payload = {
        "schema": "cho51_p3_adapter_intent_v1", "controller": Contracts.CONTROLLER,
        "numerical_worker": Contracts.NUMERICAL_WORKER, "profile": Contracts.PROFILE, "plan": dict(Contracts.PLAN),
        "boundary_request_sha256": request.expected_sha256, "boundary_assessment_sha256": boundary_assessment.sha256,
        "origin_contract_sha256": Mapping.ORIGIN_SHA256, "input_manifest_sha256": Mapping.MANIFEST_SHA256,
        "roles": {"producer": origin["historical_source"], "canonical_executor": source,
                  "boundary_recorder": source, "historical_recorder": origin["recorder_control_source"]},
        "future_recorder": {"status": "unprepared", "relative_root": "fixture/runs/phase2/lifecycle", "source": None},
        "outstanding_obligations": list(Contracts.OBLIGATIONS), "engineering_only": True, "scientific_admission": False,
    }
    fixture = {"directory": directory, "request": request, "request_payload": request_payload,
               "intent": intent_for(intent_payload), "intent_payload": intent_payload, "full": full,
               "adopted": adopted, "input_pins": input_pins, "metadata": clone(metadata), "pins": pins,
               "origin": origin, "manifest": manifest}
    fixture["compatibility"] = assess(fixture)
    return fixture


def test_genuine_historical_profile_and_complete_routes(mapping_fixture):
    report = mapping_fixture["compatibility"].report
    assert type(mapping_fixture["full"]) is ChoFirstTrancheRoute
    assert type(mapping_fixture["adopted"]) is Cho51WorkerRoute
    assert report["original_plan_count"] == 1040 and report["adopted_plan_count"] == 1020
    assert report["catalog_count"] == report["asset_count"] == 52
    assert {plan.target_subject for plan in mapping_fixture["adopted"].plans} == set(Boundary.TARGETS)
    assert all(value is False for value in report["authority"].values())
    assert all(type(value) is int and value == 0 for value in report["current_numerical_ledger"].values())
    assert report["historical_input_claim"] == {"files": 213, "bytes": 734579463, "freshly_physically_verified": False}
    selected = mapping_fixture["origin"]["target_contract"]
    assert [len(selected[name]) for name in ("support_indices", "query_indices", "unused_pool_indices")] == [10, 2, 30]
    assert mapping_fixture["full"].catalogs[1].labels == Boundary.CLASSES * 21
    assert report["selected_contract_sha256"] == mapping_fixture["origin"]["target_contract_sha256"]
    assert report["metadata_cohort_origin_sha256"] == mapping_fixture["input_pins"].cohort_audit_sha256
    assert report["future_recorder"]["status"] == "unprepared"


def test_intent_and_report_are_immutable_defensive_values(mapping_fixture):
    intent = mapping_fixture["intent"]
    compatibility = mapping_fixture["compatibility"]
    intent.payload["plan"]["target_subject"] = "subject_01"
    compatibility.report["authority"]["execution_admitted"] = True
    assert intent.payload == mapping_fixture["intent_payload"]
    assert compatibility.report["authority"]["execution_admitted"] is False
    assert compatibility.sha256 == Contracts.sha256(compatibility.canonical_json.encode("utf-8"))
    with pytest.raises(FrozenInstanceError):
        intent.expected_sha256 = "0" * 64
    with pytest.raises(FrozenInstanceError):
        compatibility.canonical_json = "{}"


@pytest.mark.parametrize("role", ["producer", "canonical_executor", "boundary_recorder", "historical_recorder"])
def test_changed_role_domain_refused(mapping_fixture, role):
    payload = clone(mapping_fixture["intent_payload"])
    payload["roles"][role]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="domains differ"):
        assess(mapping_fixture, intent=intent_for(payload))


@pytest.mark.parametrize("change", ["profile", "controller", "numerical_worker", "method", "target01", "shots_bool", "seed", "repetition", "science"])
def test_fixed_intent_scope_refused(mapping_fixture, change):
    payload = clone(mapping_fixture["intent_payload"])
    if change in ("profile", "controller", "numerical_worker"):
        payload[change] = "different-contract"
    elif change == "science":
        payload["scientific_admission"] = True
    else:
        field, value = {"method": ("method", "labram_lora"), "target01": ("target_subject", "subject_01"),
                        "shots_bool": ("shots_per_class", True), "seed": ("model_seed", 23),
                        "repetition": ("repetition", 2)}[change]
        payload["plan"][field] = value
    with pytest.raises(ValueError):
        intent_for(payload)


@pytest.mark.parametrize("change", ["authority_integer", "authority_true", "ledger_bool", "ledger_positive", "physical_true"])
def test_report_cannot_promote_authority_or_numerical_counts(mapping_fixture, change):
    payload = mapping_fixture["compatibility"].report
    if change.startswith("authority"):
        payload["authority"]["execution_admitted"] = 0 if change == "authority_integer" else True
    elif change.startswith("ledger"):
        payload["current_numerical_ledger"]["measured_cells"] = False if change == "ledger_bool" else 1
    else:
        payload["historical_input_claim"]["freshly_physically_verified"] = True
    with pytest.raises(ValueError):
        Contracts.AdapterCompatibility(Contracts.canonical_json(payload))


@pytest.mark.parametrize("change", ["prepared_recorder", "removed_obligation"])
def test_future_execution_obligations_cannot_be_prepared(mapping_fixture, change):
    payload = clone(mapping_fixture["intent_payload"])
    if change == "prepared_recorder":
        payload["future_recorder"]["status"] = "prepared"
    else:
        payload["outstanding_obligations"].pop()
    with pytest.raises(ValueError):
        intent_for(payload)


@pytest.mark.parametrize("raw", ['{"value":1,"value":2}', '{"value":NaN}', '{"value":Infinity}'])
def test_duplicate_or_nonfinite_json_refused(raw):
    with pytest.raises(ValueError):
        Contracts.decode_json(raw)


@pytest.mark.parametrize("bound", ["boolean_maximum", "oversized_maximum", "aggregate_text", "depth", "nodes", "intent_bytes"])
def test_finite_graph_and_encoded_byte_limits_refuse_before_serialization(bound, monkeypatch):
    if bound == "boolean_maximum":
        with pytest.raises(ValueError):
            Contracts.canonical_json({}, maximum=True)
    elif bound == "oversized_maximum":
        with pytest.raises(ValueError):
            Contracts.decode_json("{}", maximum=Contracts.MAX_METADATA_BYTES + 1)
    elif bound == "intent_bytes":
        raw = " " * (Contracts.MAX_INTENT_BYTES + 1)
        with pytest.raises(ValueError, match="byte bound"):
            Contracts.AdapterIntent(raw, Contracts.sha256(raw.encode("utf-8")))
    else:
        if bound == "aggregate_text":
            value = ["\u007f" * 6000, "\u007f" * 6000]
            maximum = Contracts.MAX_INTENT_BYTES
        elif bound == "nodes":
            value = [None] * Contracts.MAX_GRAPH_NODES
            maximum = Contracts.MAX_METADATA_BYTES
        else:
            value = None
            for depth in range(Contracts.MAX_GRAPH_DEPTH + 2):
                value = [value]
            maximum = Contracts.MAX_METADATA_BYTES

        def forbidden_serialization(*arguments, **keywords):
            raise AssertionError("oversized graph reached json.dumps")

        with monkeypatch.context() as patch:
            patch.setattr(Contracts.json, "dumps", forbidden_serialization)
            with pytest.raises(ValueError):
                Contracts.canonical_json(value, maximum=maximum)


def test_stale_expected_boundary_assessment_refused(mapping_fixture):
    payload = clone(mapping_fixture["intent_payload"])
    payload["boundary_assessment_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="fresh genuine boundary assessment"):
        assess(mapping_fixture, intent=intent_for(payload))


def test_changed_pinned_metadata_refused(mapping_fixture):
    path = ROOT / mapping_fixture["request_payload"]["metadata"]["path"]
    original = path.read_bytes()
    try:
        path.write_bytes(original + b" ")
        with pytest.raises(ValueError, match="bytes or physical"):
            assess(mapping_fixture)
    finally:
        path.write_bytes(original)


def test_fabricated_scope_refused_after_genuine_boundary(mapping_fixture):
    directory = mapping_fixture["directory"]
    metadata = clone(mapping_fixture["metadata"])
    metadata["scope"] = "fabricated_catalog_asset_metadata_unverified"
    payload = clone(mapping_fixture["request_payload"])
    payload["metadata"] = save_json(directory / "fabricated-route-metadata.json", metadata)
    payload["configuration"]["cohort"] = save_json(directory / "fabricated-cohort-origin.json", {
        "schema": "cho51_canonical_metadata_cohort_origin_v1", "metadata_sha256": payload["metadata"]["sha256"],
        "available_subjects": list(Boundary.SUBJECTS), "raw_input_bytes_verified": False,
    })
    input_pins = replace(mapping_fixture["input_pins"], cohort_audit_sha256=payload["configuration"]["cohort"]["sha256"])
    pins = clone(mapping_fixture["pins"])
    pins["route"] = asdict(input_pins)
    payload["execution_pins"] = save_json(directory / "fabricated-execution-pins.json", pins)
    payload["roles"]["executor"]["runtime_identity"]["evidence_sha256"] = payload["execution_pins"]["sha256"]
    request = request_for(payload)
    assessment = Boundary.assess_metadata(request, full_route=mapping_fixture["full"], adopted_route=mapping_fixture["adopted"], input_pins=input_pins)
    assert assessment.report["status"] == "metadata_contract_compatible"
    intent_payload = clone(mapping_fixture["intent_payload"])
    intent_payload["boundary_request_sha256"] = request.expected_sha256
    intent_payload["boundary_assessment_sha256"] = assessment.sha256
    with pytest.raises(ValueError, match="original synthetic lineage"):
        Mapping.assess_adapter_intent(intent_for(intent_payload), boundary_request=request,
                                      full_route=mapping_fixture["full"], adopted_route=mapping_fixture["adopted"], input_pins=input_pins)


@pytest.mark.parametrize("alias", ["root", "metadata"])
def test_boundary_path_refusal_precedes_adapter_reads(mapping_fixture, alias, monkeypatch):
    payload = clone(mapping_fixture["request_payload"])
    if alias == "root":
        payload["root"] = str(ROOT) + "\\..\\pro3"
    else:
        payload["metadata"]["path"] = "../route-metadata.json"

    def forbidden_adapter_read(*arguments, **keywords):
        raise AssertionError("adapter attempted its own decode before genuine boundary validation")

    monkeypatch.setattr(Mapping, "decode_json", forbidden_adapter_read)
    with pytest.raises(ValueError, match="root|path"):
        assess(mapping_fixture, request=request_for(payload))


@pytest.mark.parametrize("location", ["intent", "catalog"])
def test_callback_objects_refused_without_access(mapping_fixture, location):
    calls = []

    class CallbackProbe:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("caller callback executed")

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("caller equality executed")

    if location == "intent":
        with pytest.raises(ValueError, match="actual immutable"):
            assess(mapping_fixture, intent=CallbackProbe())
    else:
        full = replace(mapping_fixture["full"], catalogs=(CallbackProbe(),) + mapping_fixture["full"].catalogs[1:])
        adopted = Cho51WorkerRoute(mapping_fixture["adopted"].contract, full)
        with pytest.raises(ValueError, match="exact approved metadata types"):
            assess(mapping_fixture, full=full, adopted=adopted)
    assert calls == []


def test_public_policy_views_cannot_mutate_authority():
    for policy, key, value in ((Contracts.PLAN, "target_subject", "subject_01"),
                               (Contracts.AUTHORITY, "execution_admitted", True),
                               (Contracts.LEDGER, "measured_cells", 1)):
        with pytest.raises(TypeError):
            policy[key] = value
