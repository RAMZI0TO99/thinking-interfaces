"""Genuine canonical classes and current Git; fabricated signal metadata only."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tomllib
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path
from types import MappingProxyType

import pytest

from core.config import canonical_config_json, config_digest
from core.provenance import capture_source
from docs.phase2.cho51_canonical_boundary_v1 import boundary as Boundary
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute, from_verified_full_route
from evaluation.phase2_cho_case_inputs import ChoCaseInputPins, ChoFirstTrancheRoute
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan, environment_digest


ROOT = Path(__file__).resolve().parents[3]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def clone(value):
    return json.loads(json.dumps(value, allow_nan=False))


def request_for(payload):
    raw = canonical_config_json(payload)
    return Boundary.CanonicalBoundaryRequest(raw, digest(raw.encode("utf-8")))


def save_json(path, payload):
    raw = canonical_config_json(payload).encode("utf-8")
    path.write_bytes(raw)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(raw)}


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    directory = tmp_path_factory.mktemp("canonical-boundary")
    if not directory.is_relative_to(ROOT):
        raise ValueError("guarded pytest --basetemp must be a fresh directory inside the actual project")
    configurations = {
        name: {"path": relative, "sha256": digest((ROOT / relative).read_bytes())}
        for name, relative in Boundary.CONFIG_PATHS.items()
    }
    protocol = tomllib.loads((ROOT / Boundary.CONFIG_PATHS["protocol"]).read_text("utf-8"))
    threshold = tomllib.loads((ROOT / Boundary.CONFIG_PATHS["threshold"]).read_text("utf-8"))
    preprocessing = config_digest({
        "profile_identity": protocol["preparation"]["profile_identity"],
        "threshold_config_sha256": configurations["threshold"]["sha256"],
        "dataset": "cho2017",
        "threshold": threshold["datasets"]["cho2017"]["artifact_threshold_volts"],
    })
    catalogs = tuple(TrialCatalog(
        "cho2017", subject,
        tuple(f"unverified-metadata-trial-{index}" for index in range(42)),
        tuple("left_hand" if index < 21 else "right_hand" for index in range(42)),
        Boundary.CLASSES,
        digest(("fabricated-unverified-profile-a:" + subject).encode()), preprocessing,
    ) for subject in Boundary.SUBJECTS)
    assets = MappingProxyType({subject: ChoProfileAssets60Hz(
        digest(("fabricated-unverified-profile-b:" + subject).encode()),
        digest(("fabricated-unverified-manifest:" + subject).encode()),
        configurations["variant"]["sha256"],
    ) for subject in Boundary.SUBJECTS})
    metadata = {
        "schema": "cho51_canonical_route_metadata_v1",
        "scope": "fabricated_catalog_asset_metadata_unverified",
        "raw_input_bytes_verified": False,
        "weight_bytes_verified": False,
        "catalogs": [asdict(catalog) for catalog in catalogs],
        "assets": {subject: asdict(asset) for subject, asset in assets.items()},
    }
    metadata_pin = save_json(directory / "route-metadata.json", metadata)
    configurations["cohort"] = save_json(directory / "cohort-origin.json", {
        "schema": "cho51_canonical_metadata_cohort_origin_v1",
        "metadata_sha256": metadata_pin["sha256"],
        "available_subjects": list(Boundary.SUBJECTS),
        "raw_input_bytes_verified": False,
    })
    input_pins = ChoCaseInputPins(
        configurations["protocol"]["sha256"], configurations["threshold"]["sha256"],
        configurations["cohort"]["sha256"], configurations["variant"]["sha256"],
    )
    candidates = json.loads((ROOT / configurations["candidates"]["path"]).read_bytes())
    method_pins = {row["method"]: config_digest(row) for row in candidates["methods"]}
    source = asdict(capture_source(ROOT))
    if source["git_commit"] == "unversioned-workspace" or type(source["git_dirty"]) is not bool:
        raise ValueError("genuine current project Git identity required")
    pins = {
        "schema": "cho_engineering_execution_pins_v1",
        "source_sha256": source["source_sha256"],
        "environment_sha256": environment_digest(),
        "base_config_sha256": configurations["base"]["sha256"],
        "route": asdict(input_pins),
        "candidate_config_path": configurations["candidates"]["path"],
        "candidate_config_sha256": configurations["candidates"]["sha256"],
        "method_config_sha256": method_pins,
        "selection_ceiling_config_sha256": configurations["ceiling"]["sha256"],
        "sweep_config_sha256": configurations["sweep"]["sha256"],
    }
    execution_pin = save_json(directory / "execution-pins.json", pins)
    plans = tuple(CasePlan("cho2017", subject, method, 5, seed, 1) for subject in Boundary.SUBJECTS for method in Boundary.METHODS for seed in Boundary.SEEDS)
    selections = {subject: source_selection(catalogs, target=subject) for subject in Boundary.SUBJECTS}
    full_route = ChoFirstTrancheRoute(
        plans, catalogs, assets, canonical_config_json(protocol),
        MappingProxyType({subject: canonical_config_json(envelope("source_selection", asdict(value))) for subject, value in selections.items()}),
        MappingProxyType({catalog.subject: canonical_config_json(envelope("episode_manifest", nested_episode(catalog, shots=tuple(protocol["protocol"]["shots_per_class"]), protocol_sha256=config_digest(protocol)).payload())) for catalog in catalogs}),
    )
    adopted_route = from_verified_full_route(ROOT, full_route)
    evidence = {name: {"path": relative, "sha256": expected} for name, (relative, expected) in Boundary.ANCHORS.items()}
    origin = json.loads((ROOT / evidence["origin"]["path"]).read_bytes())["summary"]
    role_sources = {"producer": origin["historical_source"], "executor": source, "recorder": source}
    role_evidence = {"producer": evidence["origin"]["sha256"], "executor": execution_pin["sha256"], "recorder": evidence["worker_review"]["sha256"]}
    payload = {
        "schema": "cho51_canonical_boundary_request_v1", "root": str(ROOT),
        "execution_pins": execution_pin, "metadata": metadata_pin,
        "configuration": configurations, "evidence": evidence,
        "roles": {name: {"source": role_sources[name], "runtime_identity": {"role": name, "evidence_sha256": role_evidence[name], "fresh_runtime_verification_performed": False}} for name in role_sources},
        "prospective_numerical_budget": dict(Boundary.PROSPECTIVE_BUDGET),
    }
    return {"directory": directory, "payload": payload, "metadata": metadata, "pins": pins, "full": full_route, "adopted": adopted_route, "input_pins": input_pins}


def assess(fixture, payload=None, full=None, adopted=None, input_pins=None):
    return Boundary.assess_metadata(
        request_for(fixture["payload"] if payload is None else payload),
        full_route=fixture["full"] if full is None else full,
        adopted_route=fixture["adopted"] if adopted is None else adopted,
        input_pins=fixture["input_pins"] if input_pins is None else input_pins,
    )


def baseline(fixture):
    report = assess(fixture).report
    assert report["status"] == "metadata_contract_compatible"
    assert report["original_plan_count"] == 1040
    assert report["adopted_plan_count"] == 1020
    assert report["available_catalogs"] == report["available_labram_assets"] == 52
    assert all(value is False for value in report["authority"].values())
    assert all(type(value) is int and value == 0 for value in report["current_numerical_ledger"].values())
    return report


def test_genuine_current_source_and_complete_typed_routes(fixture):
    report = baseline(fixture)
    assert type(fixture["full"]) is ChoFirstTrancheRoute
    assert type(fixture["adopted"]) is Cho51WorkerRoute
    assert all(type(plan) is CasePlan for plan in fixture["full"].plans)
    assert all(type(catalog) is TrialCatalog for catalog in fixture["full"].catalogs)
    assert report["roles"]["executor"]["source"] == asdict(capture_source(ROOT))
    assert report["evaluation_targets"] == list(Boundary.TARGETS)
    assert report["prospective_engineering_case"] == asdict(fixture["adopted"].plans[0])


def test_stale_helper_contract_refused_and_fresh_epoch_accepted(fixture):
    baseline(fixture)
    another = from_verified_full_route(ROOT, fixture["full"])
    assert type(another.contract) is not type(fixture["adopted"].contract)
    with pytest.raises(ValueError, match="stale helper epoch"):
        assess(fixture)
    assert assess(fixture, adopted=another).report["status"] == "metadata_contract_compatible"
    fixture["adopted"] = another
    assert assess(fixture).report["status"] == "metadata_contract_compatible"


@pytest.mark.parametrize("accessor", ["getattribute", "property"])
def test_copied_method_shadow_contract_refused_before_accessors(fixture, accessor):
    baseline(fixture)
    actual = type(fixture["adopted"].contract)
    calls = []

    def forbidden(*arguments):
        calls.append(arguments)
        raise AssertionError("shadow contract accessor called")

    namespace = {"__module__": "_cho51_worker_planner", "__dataclass_fields__": actual.__dataclass_fields__, "plan_for": actual.plan_for}
    namespace["__getattribute__" if accessor == "getattribute" else "plans"] = forbidden if accessor == "getattribute" else property(forbidden)
    shadow_class = type("Cho51RouteContract", (), namespace)
    shadow = object.__new__(shadow_class)
    with pytest.raises(ValueError, match="actual reviewed adopted contract"):
        assess(fixture, adopted=Cho51WorkerRoute(shadow, fixture["full"]))
    assert calls == []


def test_request_and_report_are_immutable_defensive_finite_metadata(fixture):
    baseline(fixture)
    request = request_for(fixture["payload"])
    assessment = assess(fixture)
    request.payload["roles"]["producer"]["source"]["git_commit"] = "0" * 40
    assessment.report["authority"]["execution_admitted"] = True
    assert request.payload == fixture["payload"]
    assert assessment.report["authority"]["execution_admitted"] is False
    with pytest.raises(FrozenInstanceError):
        request.expected_sha256 = "0" * 64
    with pytest.raises(FrozenInstanceError):
        assessment._report_json = "{}"
    assert assessment.sha256 == digest(assessment.canonical_json.encode())


@pytest.mark.parametrize("role", ["producer", "executor", "recorder"])
def test_swapped_role_sources_refused_after_valid_baseline(fixture, role):
    baseline(fixture)
    payload = clone(fixture["payload"])
    other = "executor" if role == "producer" else "producer"
    payload["roles"][role]["source"] = payload["roles"][other]["source"]
    with pytest.raises(ValueError, match="role differs"):
        assess(fixture, payload=payload)


@pytest.mark.parametrize("role", ["producer", "executor", "recorder"])
def test_role_runtime_identity_cannot_be_flattened(fixture, role):
    baseline(fixture)
    payload = clone(fixture["payload"])
    payload["roles"][role]["runtime_identity"]["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="role differs"):
        assess(fixture, payload=payload)


@pytest.mark.parametrize("anchor", ["owner", "proposal", "roster", "origin", "factory_review", "worker_review"])
def test_owner_package_and_origin_anchors_cannot_be_replaced(fixture, anchor):
    baseline(fixture)
    payload = clone(fixture["payload"])
    payload["evidence"][anchor]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="anchor changed"):
        assess(fixture, payload=payload)


@pytest.mark.parametrize("configuration", ["base", "protocol", "threshold", "variant", "ceiling", "sweep", "candidates"])
def test_frozen_configuration_bytes_cannot_be_redefined(fixture, configuration):
    baseline(fixture)
    payload = clone(fixture["payload"])
    payload["configuration"][configuration]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="frozen bytes changed"):
        assess(fixture, payload=payload)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra", "target01", "wrong_seed", "wrong_shots", "wrong_repetition", "dict_plan"])
def test_full_and_adopted_identity_inventory_refused(fixture, mutation):
    baseline(fixture)
    plans = fixture["full"].plans
    contract = fixture["adopted"].contract
    if mutation == "missing":
        plans = plans[:-1]
    elif mutation == "duplicate":
        plans = plans[:-1] + plans[:1]
    elif mutation == "extra":
        plans = plans + plans[:1]
    elif mutation == "target01":
        contract = replace(contract, plans=fixture["full"].plans[:1020])
    elif mutation == "dict_plan":
        plans = (asdict(plans[0]),) + plans[1:]
    else:
        field = {"wrong_seed": "model_seed", "wrong_shots": "shots_per_class", "wrong_repetition": "repetition"}[mutation]
        plans = (replace(plans[0], **{field: 2}),) + plans[1:]
    full = replace(fixture["full"], plans=plans)
    adopted = Cho51WorkerRoute(contract, full)
    with pytest.raises(ValueError, match="identities required"):
        assess(fixture, full=full, adopted=adopted)


@pytest.mark.parametrize("field", ["catalogs", "labram_assets", "selection_records_json", "episode_records_json"])
def test_incomplete_catalog_asset_selection_episode_inventory(fixture, field):
    baseline(fixture)
    value = getattr(fixture["full"], field)
    value = value[:-1] if field == "catalogs" else {key: item for key, item in value.items() if key != "subject_52"}
    full = replace(fixture["full"], **{field: value})
    with pytest.raises(ValueError):
        assess(fixture, full=full, adopted=Cho51WorkerRoute(fixture["adopted"].contract, full))


@pytest.mark.parametrize("field", ["full", "adopted", "input_pins", "contract"])
def test_wrong_actual_canonical_type_refused(fixture, field):
    baseline(fixture)
    values = {"full_route": fixture["full"], "adopted_route": fixture["adopted"], "input_pins": fixture["input_pins"]}
    if field == "contract":
        values["adopted_route"] = Cho51WorkerRoute({}, fixture["full"])
    else:
        values[{"full": "full_route", "adopted": "adopted_route", "input_pins": "input_pins"}[field]] = {}
    with pytest.raises(ValueError, match="actual .*required"):
        Boundary.assess_metadata(request_for(fixture["payload"]), **values)


@pytest.mark.parametrize("field", ["source_updates", "restore_count", "query_count", "measured_cells"])
def test_boolean_and_changed_budget_counts_refused(fixture, field):
    baseline(fixture)
    payload = clone(fixture["payload"])
    payload["prospective_numerical_budget"][field] = bool(payload["prospective_numerical_budget"][field])
    with pytest.raises(ValueError, match="integer"):
        request_for(payload)


@pytest.mark.parametrize("raw", ['{"schema":1,"schema":1}', '{"value":NaN}', '{"value":Infinity}', '{"value":1e999}', '{"truncated":', '[1,2]'])
def test_malformed_nonfinite_duplicate_and_nonobject_request(fixture, raw):
    baseline(fixture)
    with pytest.raises(ValueError):
        Boundary.CanonicalBoundaryRequest(raw, digest(raw.encode()))


@pytest.mark.parametrize("mutation", ["extra_request", "extra_pin", "extra_role", "verified_runtime"])
def test_unknown_fields_and_inferred_runtime_authority_refused(fixture, mutation):
    baseline(fixture)
    payload = clone(fixture["payload"])
    if mutation == "extra_request":
        payload["execute"] = True
    elif mutation == "extra_pin":
        payload["execution_pins"]["verified"] = True
    elif mutation == "extra_role":
        payload["roles"]["producer"]["source"]["version"] = "same version"
    else:
        payload["roles"]["executor"]["runtime_identity"]["fresh_runtime_verification_performed"] = True
    with pytest.raises(ValueError):
        request_for(payload)


@pytest.mark.parametrize("relative", ["../escape.json", "a/../b.json", "a\\b.json", "C:/escape.json", "a//b.json", "a/./b.json", "a./b.json"])
def test_non_direct_metadata_paths_refused(fixture, relative):
    baseline(fixture)
    payload = clone(fixture["payload"])
    payload["metadata"]["path"] = relative
    with pytest.raises((ValueError, OSError)):
        assess(fixture, payload=payload)


@pytest.mark.parametrize("mutation", ["extra", "duplicate", "nonfinite", "boolean_schema", "route_extra", "wrong_method", "wrong_source"])
def test_canonical_pin_strict_read_precedes_genuine_loader(fixture, mutation, tmp_path):
    baseline(fixture)
    payload = clone(fixture["payload"])
    pins = clone(fixture["pins"])
    if mutation == "extra":
        pins["verified"] = True
    elif mutation == "boolean_schema":
        pins["schema"] = True
    elif mutation == "route_extra":
        pins["route"]["verified"] = True
    elif mutation == "wrong_method":
        pins["method_config_sha256"]["labram_linear"] = "0" * 64
    elif mutation == "wrong_source":
        pins["source_sha256"] = "0" * 64
    path = tmp_path / "pins.json"
    if mutation in ("duplicate", "nonfinite"):
        raw = canonical_config_json(pins).encode()
        raw = raw[:-1] + (b',"schema":"cho_engineering_execution_pins_v1"}' if mutation == "duplicate" else b',"invalid":NaN}')
        path.write_bytes(raw)
        pin = {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(raw)}
    else:
        pin = save_json(path, pins)
    payload["execution_pins"] = pin
    payload["roles"]["executor"]["runtime_identity"]["evidence_sha256"] = pin["sha256"]
    with pytest.raises(ValueError):
        assess(fixture, payload=payload)


@pytest.mark.parametrize("mutation", ["claim_verified", "missing_asset", "extra_catalog", "wrong_preprocessing", "wrong_variant", "catalog_extra", "catalog_bool"])
def test_external_metadata_is_reconstructed_not_a_verified_manifest_witness(fixture, mutation, tmp_path):
    baseline(fixture)
    payload = clone(fixture["payload"])
    metadata = clone(fixture["metadata"])
    if mutation == "claim_verified":
        metadata["raw_input_bytes_verified"] = True
    elif mutation == "missing_asset":
        metadata["assets"].pop("subject_52")
    elif mutation == "extra_catalog":
        metadata["catalogs"].append(metadata["catalogs"][0])
    elif mutation == "wrong_preprocessing":
        metadata["catalogs"][0]["preprocessing_sha256"] = "0" * 64
    elif mutation == "wrong_variant":
        metadata["assets"]["subject_01"]["variant_config_sha256"] = "0" * 64
    elif mutation == "catalog_extra":
        metadata["catalogs"][0]["physical_bytes_verified"] = True
    else:
        metadata["catalogs"][0]["trial_ids"][0] = True
    payload["metadata"] = save_json(tmp_path / "metadata.json", metadata)
    cohort = {"schema": "cho51_canonical_metadata_cohort_origin_v1", "metadata_sha256": payload["metadata"]["sha256"], "available_subjects": list(Boundary.SUBJECTS), "raw_input_bytes_verified": False}
    cohort_pin = save_json(tmp_path / "cohort.json", cohort)
    payload["configuration"]["cohort"] = cohort_pin
    pins = clone(fixture["pins"])
    pins["route"]["cohort_audit_sha256"] = cohort_pin["sha256"]
    payload["execution_pins"] = save_json(tmp_path / "pins.json", pins)
    payload["roles"]["executor"]["runtime_identity"]["evidence_sha256"] = payload["execution_pins"]["sha256"]
    with pytest.raises(ValueError):
        assess(fixture, payload=payload, input_pins=replace(fixture["input_pins"], cohort_audit_sha256=cohort_pin["sha256"]))


def test_same_byte_replacement_after_open_is_refused(fixture, tmp_path, monkeypatch):
    baseline(fixture)
    path = tmp_path / "stable.json"
    replacement = tmp_path / "replacement.json"
    raw = b'{"metadata":1}'
    path.write_bytes(raw)
    replacement.write_bytes(raw)
    assert Boundary.stable_metadata_bytes(path, digest(raw))[0] == raw
    original = Path.open

    class ReplacingStream:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def fileno(self):
            return self.stream.fileno()

        def read(self, maximum):
            return self.stream.read(maximum)

        def __exit__(self, *arguments):
            self.stream.close()
            os.replace(replacement, path)

    def open_replacing(self, *arguments, **keywords):
        stream = original(self, *arguments, **keywords)
        return ReplacingStream(stream) if self == path else stream

    monkeypatch.setattr(Path, "open", open_replacing)
    with pytest.raises((ValueError, OSError)):
        Boundary.stable_metadata_bytes(path, digest(raw))


def test_hardlink_metadata_refused(fixture, tmp_path):
    baseline(fixture)
    path = tmp_path / "metadata.json"
    alias = tmp_path / "alias.json"
    path.write_bytes(b'{"metadata":1}')
    assert Boundary.stable_metadata_bytes(path, digest(path.read_bytes()))[0] == path.read_bytes()
    os.link(path, alias)
    with pytest.raises(ValueError, match="one regular"):
        Boundary.stable_metadata_bytes(path, digest(path.read_bytes()))


@pytest.mark.parametrize("target", ["leaf", "ancestor"])
def test_controlled_reparse_flags_fail_closed(fixture, tmp_path, monkeypatch, target):
    baseline(fixture)
    path = tmp_path / "metadata.json"
    path.write_bytes(b"{}")
    expected = digest(b"{}")
    assert Boundary.stable_metadata_bytes(path, expected)[0] == b"{}"
    affected = path if target == "leaf" else path.parent
    original = Path.lstat

    class ReparseInfo:
        def __init__(self, actual):
            self.actual = actual
            self.st_file_attributes = getattr(actual, "st_file_attributes", 0) | 0x400

        def __getattr__(self, name):
            return getattr(self.actual, name)

    def marked_lstat(self):
        actual = original(self)
        return ReparseInfo(actual) if self == affected else actual

    monkeypatch.setattr(Path, "lstat", marked_lstat)
    with pytest.raises(ValueError, match="reparse"):
        Boundary.stable_metadata_bytes(path, expected)


def test_oversized_truncated_and_changed_file_hashes_refused(fixture, tmp_path):
    baseline(fixture)
    path = tmp_path / "metadata.json"
    path.write_bytes(b"{}")
    assert Boundary.stable_metadata_bytes(path, digest(b"{}"))[0] == b"{}"
    path.write_bytes(b"x" * (Boundary.MAX_METADATA_BYTES + 1))
    with pytest.raises(ValueError, match="byte limit"):
        Boundary.stable_metadata_bytes(path, "0" * 64)
    path.write_bytes(b"{}")
    with pytest.raises(ValueError, match="bytes or physical"):
        Boundary.stable_metadata_bytes(path, digest(b'{"different":1}'))


def test_callback_mapping_is_refused_without_invocation(fixture):
    baseline(fixture)
    calls = []

    class CallbackMapping:
        def __iter__(self):
            calls.append("called")
            raise AssertionError("mapping callback must not run")

    full = replace(fixture["full"], labram_assets=CallbackMapping())
    with pytest.raises(ValueError, match="without callbacks"):
        assess(fixture, full=full, adopted=Cho51WorkerRoute(fixture["adopted"].contract, full))
    assert calls == []


@pytest.mark.parametrize("location", [
    "plan_dataset", "plan_method", "plan_seed", "plan_shots", "plans_tuple",
    "catalogs_tuple", "asset_dictionary", "selection_dictionary", "protocol_text",
    "catalog_subject", "catalog_trial_tuple", "catalog_trial_leaf", "catalog_label_leaf",
    "asset_digest", "input_pin_digest", "method_digest", "contract_plans",
    "selection_target", "fold_validation", "selection_mapping_key", "asset_mapping_key",
    "asset_mapping_value", "selection_mapping_value",
])
def test_nested_callback_types_refused_before_any_callback(fixture, location):
    baseline(fixture)
    calls = []

    class CallbackString(str):
        def __eq__(self, other):
            calls.append("string equality")
            return str.__eq__(self, other)

        def __hash__(self):
            calls.append("string hash")
            return str.__hash__(self)

        def encode(self, *arguments, **keywords):
            calls.append("string encode")
            return str.encode(self, *arguments, **keywords)

        def __str__(self):
            calls.append("string conversion")
            return str.__str__(self)

    class CallbackInteger(int):
        def __eq__(self, other):
            calls.append("integer equality")
            return int.__eq__(self, other)

        def __hash__(self):
            calls.append("integer hash")
            return int.__hash__(self)

        def __int__(self):
            calls.append("integer conversion")
            return int.__int__(self)

    class CallbackTuple(tuple):
        def __iter__(self):
            calls.append("tuple iteration")
            return tuple.__iter__(self)

        def __len__(self):
            calls.append("tuple length")
            return tuple.__len__(self)

        def __eq__(self, other):
            calls.append("tuple equality")
            return tuple.__eq__(self, other)

    class CallbackDictionary(dict):
        def __iter__(self):
            calls.append("dictionary iteration")
            return dict.__iter__(self)

        def items(self):
            calls.append("dictionary items")
            return dict.items(self)

        def __getitem__(self, key):
            calls.append("dictionary lookup")
            return dict.__getitem__(self, key)

        def __eq__(self, other):
            calls.append("dictionary equality")
            return dict.__eq__(self, other)

    def changed(value, **updates):
        copied = object.__new__(type(value))
        for field in value.__dataclass_fields__:
            object.__setattr__(copied, field, object.__getattribute__(value, field))
        for field, child in updates.items():
            object.__setattr__(copied, field, child)
        return copied

    full = fixture["full"]
    contract = fixture["adopted"].contract
    input_pins = fixture["input_pins"]
    if location.startswith("plan_"):
        field = {"plan_dataset": "dataset", "plan_method": "method", "plan_seed": "model_seed", "plan_shots": "shots_per_class"}[location]
        original = getattr(full.plans[0], field)
        child = CallbackInteger(original) if type(original) is int else CallbackString(original)
        full = changed(full, plans=(changed(full.plans[0], **{field: child}),) + full.plans[1:])
    elif location in ("plans_tuple", "catalogs_tuple"):
        field = "plans" if location == "plans_tuple" else "catalogs"
        full = changed(full, **{field: CallbackTuple(getattr(full, field))})
    elif location in ("asset_dictionary", "selection_dictionary"):
        field = "labram_assets" if location == "asset_dictionary" else "selection_records_json"
        full = changed(full, **{field: CallbackDictionary(getattr(full, field))})
    elif location == "protocol_text":
        full = changed(full, protocol_config_json=CallbackString(full.protocol_config_json))
    elif location.startswith("catalog_"):
        catalog = full.catalogs[0]
        if location == "catalog_subject":
            catalog = changed(catalog, subject=CallbackString(catalog.subject))
        elif location == "catalog_trial_tuple":
            catalog = changed(catalog, trial_ids=CallbackTuple(catalog.trial_ids))
        else:
            field = "trial_ids" if location == "catalog_trial_leaf" else "labels"
            children = getattr(catalog, field)
            catalog = changed(catalog, **{field: (CallbackString(children[0]),) + children[1:]})
        full = changed(full, catalogs=(catalog,) + full.catalogs[1:])
    elif location == "asset_digest":
        assets = dict(full.labram_assets)
        asset = assets["subject_01"]
        assets["subject_01"] = changed(asset, profile_b_artifact_sha256=CallbackString(asset.profile_b_artifact_sha256))
        full = changed(full, labram_assets=assets)
    elif location == "input_pin_digest":
        input_pins = changed(input_pins, protocol_config_sha256=CallbackString(input_pins.protocol_config_sha256))
    elif location == "method_digest":
        methods = dict(contract.method_config_sha256)
        methods["labram_linear"] = CallbackString(methods["labram_linear"])
        contract = changed(contract, method_config_sha256=methods)
    elif location == "contract_plans":
        contract = changed(contract, plans=CallbackTuple(contract.plans))
    elif location in ("selection_target", "fold_validation", "selection_mapping_key"):
        selections = dict(contract.selections)
        selection = selections["subject_02"]
        if location == "selection_target":
            selections["subject_02"] = changed(selection, target_subject=CallbackString(selection.target_subject))
        elif location == "fold_validation":
            fold = selection.inner_folds[0]
            selections["subject_02"] = changed(selection, inner_folds=(changed(fold, validation_subject=CallbackString(fold.validation_subject)),) + selection.inner_folds[1:])
        else:
            selections[CallbackString("subject_02")] = selections.pop("subject_02")
        contract = changed(contract, selections=selections)
    elif location in ("asset_mapping_key", "asset_mapping_value"):
        assets = dict(full.labram_assets)
        if location == "asset_mapping_key":
            assets[CallbackString("subject_01")] = assets.pop("subject_01")
        else:
            assets["subject_01"] = CallbackDictionary()
        full = changed(full, labram_assets=assets)
    else:
        selections = dict(full.selection_records_json)
        selections["subject_01"] = CallbackString(selections["subject_01"])
        full = changed(full, selection_records_json=selections)
    adopted = Cho51WorkerRoute(contract, full)
    calls.clear()
    with pytest.raises(ValueError, match="typed graph.*without callbacks"):
        assess(fixture, full=full, adopted=adopted, input_pins=input_pins)
    assert calls == []


@pytest.mark.parametrize("backing", ["arbitrary_mapping", "dictionary_subclass"])
def test_mapping_proxy_backing_refused_without_callbacks(fixture, backing):
    baseline(fixture)
    calls = []

    class CallbackMapping:
        def __iter__(self):
            calls.append("proxy iteration")
            return iter(())

        def __getitem__(self, key):
            calls.append("proxy lookup")
            raise KeyError(key)

        def __len__(self):
            calls.append("proxy length")
            return 0

        def keys(self):
            calls.append("proxy keys")
            return ()

    class CallbackDictionary(dict):
        def items(self):
            calls.append("proxy dictionary items")
            return dict.items(self)

    supplied = CallbackMapping() if backing == "arbitrary_mapping" else CallbackDictionary(fixture["full"].labram_assets)
    full = replace(fixture["full"], labram_assets=MappingProxyType(supplied))
    calls.clear()
    with pytest.raises(ValueError, match="exact dict backing without callbacks"):
        assess(fixture, full=full, adopted=Cho51WorkerRoute(fixture["adopted"].contract, full))
    assert calls == []


def test_report_callback_text_refused_without_encode(fixture):
    baseline(fixture)
    calls = []

    class CallbackText(str):
        def encode(self, *arguments, **keywords):
            calls.append("report encode")
            return str.encode(self, *arguments, **keywords)

    report = CallbackText(assess(fixture).canonical_json)
    with pytest.raises(ValueError, match="exact immutable JSON text without callbacks"):
        Boundary.BoundaryAssessment(report)
    assert calls == []


def test_report_flags_cannot_be_turned_into_admission(fixture):
    baseline(fixture)
    report = assess(fixture).report
    report["authority"]["execution_admitted"] = True
    with pytest.raises(ValueError, match="cannot carry authority"):
        Boundary.BoundaryAssessment(canonical_config_json(report))
    assert not hasattr(assess(fixture), "execute")
    assert not hasattr(assess(fixture), "recover")


def test_assessment_never_calls_execution_or_creates_output(fixture, monkeypatch):
    baseline(fixture)
    from evaluation import phase2_cho_case_inputs, phase2_cho_execution, phase2_cho_selected_manifest_bridge, phase2_cho_source_restore, phase2_cho_sweep
    from docs.phase2.cho51_worker_bridge_v1 import worker_bridge

    def forbidden(*arguments, **keywords):
        raise AssertionError("unsafe production API invoked by metadata assessment")

    for module, name in (
        (phase2_cho_case_inputs, "prepare_cho_first_tranche"),
        (worker_bridge, "prepare_cho51_worker_route"),
        (phase2_cho_selected_manifest_bridge, "verify_cho_selected_manifest_files"),
        (phase2_cho_source_restore, "restore_cho_selected_source"),
        (phase2_cho_sweep, "run_cho_first_tranche_sweep"),
        (phase2_cho_execution, "execute_engineering_cases"),
        (phase2_cho_execution, "run_cho_execution_child"),
    ):
        monkeypatch.setattr(module, name, forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    report = assess(fixture).report
    assert report["metadata_scope"] == "fabricated_catalog_asset_metadata_unverified"
    assert not any(report["authority"].values())
    assert not {"execute", "recover", "backend", "lock", "claim", "capability"} & set(report)
    assert "torch" in sys.modules and "numpy" in sys.modules

@pytest.mark.parametrize("field", list(Boundary._authority()))
def test_report_authority_requires_exact_false_after_valid_baseline(fixture, field):
    baseline(fixture)
    report = assess(fixture).report
    report["authority"][field] = 0
    with pytest.raises(ValueError, match="cannot carry authority"):
        Boundary.BoundaryAssessment(canonical_config_json(report))


def test_windows_path_and_descriptor_ctime_are_independently_stable(fixture, tmp_path, monkeypatch):
    baseline(fixture)
    path = tmp_path / "windows-stat.json"
    raw = b'{"metadata":1}'
    path.write_bytes(raw)
    identity = path.stat()
    actual_fstat = os.fstat

    class DescriptorStat:
        def __init__(self, actual):
            self.actual = actual

        def __getattr__(self, name):
            if name == "st_ctime_ns":
                return self.actual.st_ctime_ns + 1
            return getattr(self.actual, name)

    def descriptor_stat(descriptor):
        observed = actual_fstat(descriptor)
        return DescriptorStat(observed) if observed.st_ino == identity.st_ino else observed

    monkeypatch.setattr(os, "fstat", descriptor_stat)
    assert Boundary.stable_metadata_bytes(path, digest(raw))[0] == raw
