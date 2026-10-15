"""Prepared synthetic boundary tests; all native and public verifier I/O mocked.

These tests cannot establish that real selectors ran or native tensor receipts
exist. Separate guarded integration checks must exercise the public verifier.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from core.config import canonical_config_json, config_digest
from core.provenance import SourceProvenance
from docs.phase2.cho51_selector_collection_v1 import collection as C
from docs.phase2.cho51_tensor_verification_v1.contract import make_tensor_request
from evaluation.phase2_cho_case_inputs import SELECTED_METHODS, SELECTED_SEEDS
from evaluation.phase2_cho_selection_file_bridge import ChoSelectionFileClaim
from evaluation.phase2_protocol import TrialCatalog
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_subject_aggregation import ExpectedCell, ScoreRow


def _digest(label):
    return hashlib.sha256(label.encode()).hexdigest()


@pytest.fixture(scope="module")
def fabricated(tmp_path_factory):
    root = tmp_path_factory.mktemp("selector-metadata").resolve()
    source = SourceProvenance("1" * 40, _digest("fabricated-source"), True)
    methods = {method: {"dataset": "cho2017", "method": method} for method in SELECTED_METHODS}
    method_digests = {method: config_digest(config) for method, config in methods.items()}
    protocol = {"fabricated_protocol_only": True}
    plans = tuple(
        CasePlan("cho2017", f"subject_{subject:02d}", method, 5, seed, 1)
        for subject in range(2, 53) for method in SELECTED_METHODS for seed in SELECTED_SEEDS
    )
    catalogs = tuple(TrialCatalog(
        "cho2017", f"subject_{subject:02d}", tuple(f"trial_{n}" for n in range(12)),
        ("left",) * 6 + ("right",) * 6, ("left", "right"),
        _digest(f"artifact:{subject}"), _digest("preprocessing"),
    ) for subject in range(1, 53))
    full_route = SimpleNamespace(
        catalogs=catalogs, labram_assets={c.subject: object() for c in catalogs},
        protocol_config_json=canonical_config_json(protocol),
        selection_records_json={c.subject: canonical_config_json({"target": c.subject}) for c in catalogs},
    )
    owner, ceiling = _digest("owner"), _digest("ceiling")
    route = C.Cho51WorkerRoute(SimpleNamespace(
        plans=plans, method_config_sha256=method_digests, owner_decision_sha256=owner,
    ), full_route)
    publications, requests, pins, records, claims, receipts = [], [], [], {}, [], []
    for plan in plans:
        contract = {"maximum_gradient_steps": 5253, "candidates": [
            {"name": "first", "source": {"steps": 1}, "support": {"steps": 1}},
            {"name": "second", "source": {"steps": 2}, "support": {"steps": 2}},
        ]}
        manifest = _digest("manifest:" + plan.case_id)
        publication = C.Cho51PublicationBinding(
            plan.case_id, manifest,
            root / "runs/phase2/selected_sources/manifests" / (manifest + ".json"),
            _digest("evidence:" + plan.case_id), config_digest(contract), "first",
            config_digest(protocol), method_digests[plan.method], _digest("environment"),
            _digest("recipe:" + plan.case_id), _digest("state:" + plan.case_id),
            _digest("weights:" + plan.case_id),
        )
        request = make_tensor_request(
            project_root=root, plan=plan, publication=publication, expected_source=source,
            method_config=methods[plan.method], protocol_config=protocol,
        )
        pin = C.Cho51TensorReceiptPin(
            plan.case_id, request.sha256, _digest("bundle:" + plan.case_id),
            root / "fabricated-bundles" / plan.case_id / "bundle.json",
            root / "fabricated-native" / plan.case_id,
            _digest("native-receipt:" + plan.case_id), _digest("witness:" + plan.case_id),
        )
        publications.append(publication)
        requests.append(request)
        pins.append(pin)
        records[manifest] = {"payload": {
            "contract": contract, "contract_sha256": config_digest(contract),
            "selected_candidate": "first",
        }}
        claims.append(ChoSelectionFileClaim(
            plan.case_id, publication.evidence_sha256, publication.selection_contract_sha256,
            publication.selected_candidate, publication.manifest_sha256,
            publication.manifest_path.relative_to(root).as_posix(),
        ))
        receipts.append(C.Cho51TensorReceiptBinding(
            pin.case_id, pin.request_sha256, pin.bundle_sha256, pin.bundle_path,
            pin.native_directory, pin.native_receipt_file_sha256, pin.witness_file_sha256,
            1024, 2048,
        ))
    rows = tuple(ScoreRow(ExpectedCell(*plan.identity_key), 1, 2, _digest("cell:" + plan.case_id)) for plan in plans)
    publication_collection = C.Cho51PublicationCollection(
        rows, tuple(claims), tuple(publications), owner, ceiling,
    )
    tensor_collection = C.Cho51TensorCollection(
        rows, tuple(claims), tuple(publications), tuple(receipts), owner, ceiling,
    )
    return SimpleNamespace(
        root=root, source=source, methods=methods, method_digests=method_digests,
        protocol=protocol, plans=plans, route=route, publications=tuple(publications),
        requests=tuple(requests), pins=tuple(pins), records=records,
        publication_collection=publication_collection, tensor_collection=tensor_collection,
        owner=owner, ceiling=ceiling,
    )


@pytest.fixture
def boundary(fabricated, monkeypatch):
    f = fabricated
    state = SimpleNamespace(
        events=[], tensor_calls=0, ceiling_calls=0, stable_calls={},
        before=f.tensor_collection, after=f.tensor_collection,
        mutation=None, fail=None, manifest_override=None, record_override=None,
        verified_override=None, method_override=None,
    )
    pubs_by_manifest = {p.manifest_sha256: p for p in f.publications}
    requests_by_case = {r.plan.case_id: r for r in f.requests}

    def step(event):
        state.events.append(event)
        if state.fail == event:
            raise ValueError("fabricated failure: " + event)

    def tensor(root, route, publication, requests, pins, **kwargs):
        state.tensor_calls += 1
        step("tensor_" + str(state.tensor_calls))
        assert root == f.root and route is f.route and publication is f.publication_collection
        assert type(requests) is tuple and requests == f.requests
        assert type(pins) is tuple and pins == f.pins
        assert kwargs == {"expected_source": f.source}
        if state.tensor_calls == 1 and state.mutation:
            state.mutation()
        return state.before if state.tensor_calls == 1 else state.after

    def ceiling(root, **kwargs):
        step("ceiling_load")
        assert root == f.root and kwargs == {"expected_sha256": f.ceiling}
        return C.Cho51SelectionCeilingWitness(
            f.root / "configs/phase2/selection_ceiling.toml", f.ceiling, (0, 0, 0, 0),
        )

    def stable_ceiling(witness):
        state.ceiling_calls += 1
        step("ceiling_" + str(state.ceiling_calls))

    def manifest(root, path, **kwargs):
        pub = pubs_by_manifest[kwargs["manifest_sha256"]]
        step("manifest:" + pub.case_id)
        assert root == f.root and path == pub.manifest_path
        assert kwargs == {
            "manifest_sha256": pub.manifest_sha256, "evidence_sha256": pub.evidence_sha256,
            "selection_contract_sha256": pub.selection_contract_sha256,
            "selected_candidate": pub.selected_candidate,
            "protocol_config_sha256": pub.protocol_config_sha256, "expected_source": f.source,
            "model_recipe_sha256": pub.model_recipe_sha256, "model_state_sha256": pub.model_state_sha256,
        }
        witness = C.ChoSelectedManifestWitness(
            root, path, pub.manifest_sha256, _digest("manifest-file"), (0, 0, 0, 0),
            root / "fabricated-evidence" / (pub.evidence_sha256 + ".json"),
            _digest("evidence-file"), (0, 0, 0, 0), 1,
            root / "fabricated-weights", pub.weights_sha256, (0, 0, 0, 0),
        )
        return state.manifest_override(witness) if state.manifest_override else witness

    class Store:
        def __init__(self, root):
            assert root == f.root

        def read_persisted_evidence_for_manifest(self, manifest_sha256, evidence_sha256):
            pub = pubs_by_manifest[manifest_sha256]
            step("store:" + pub.case_id)
            assert evidence_sha256 == pub.evidence_sha256
            # Detach to prevent a mutation test from altering the module fixture.
            record = json.loads(json.dumps(f.records[manifest_sha256]))
            if state.record_override:
                record = state.record_override(record)
            return record, f.root / "fabricated-evidence" / (evidence_sha256 + ".json")

    def derive(plan, contract, assets):
        step("derive:" + plan.case_id)
        assert assets == ({} if plan.method == "eegnet" else f.route.labram_assets)
        assert contract["candidates"][0]["name"] == "first"
        return f.methods[plan.method]

    def configuration(template):
        return state.method_override if state.method_override else config_digest(template)

    def public(**kwargs):
        plan = kwargs["plan"]
        step("public:" + plan.case_id)
        req = requests_by_case[plan.case_id]
        assert kwargs == {
            "record": f.records[req.publication.manifest_sha256],
            "evidence_sha256": req.publication.evidence_sha256, "plan": plan,
            "protocol_config": f.protocol, "catalogs": f.route.catalogs,
            "selection_record": {"target": plan.target_subject},
            "assets": {} if plan.method == "eegnet" else f.route.labram_assets,
            "root": f.root, "adapter_model_state_sha256": req.publication.model_state_sha256,
            "adapter_source_settings": {"steps": 1}, "adapter_support_settings": {"steps": 1},
        }
        verified = C.VerifiedChoSelection("first", req.publication.evidence_sha256)
        return state.verified_override(verified) if state.verified_override else verified

    def stable_manifest(witness):
        case_id = pubs_by_manifest[witness.manifest_sha256].case_id
        count = state.stable_calls.get(case_id, 0) + 1
        state.stable_calls[case_id] = count
        step("stable_" + str(count) + ":" + case_id)

    monkeypatch.setattr(C, "collect_cho51_tensor_receipts", tensor)
    monkeypatch.setattr(C, "load_selection_ceiling", ceiling)
    monkeypatch.setattr(C.Cho51SelectionCeilingWitness, "verify_stable", stable_ceiling)
    monkeypatch.setattr(C, "verify_cho_selected_manifest_files", manifest)
    monkeypatch.setattr(C, "SelectedSourceStore", Store)
    monkeypatch.setattr(C, "derive_cho_method_template", derive)
    monkeypatch.setattr(C, "method_configuration", configuration)
    monkeypatch.setattr(C, "verify_cho_selection_evidence", public)
    monkeypatch.setattr(C.ChoSelectedManifestWitness, "verify_stable", stable_manifest)
    args = dict(
        project_root=f.root, route=f.route, publication_collection=f.publication_collection,
        requests=f.requests, receipt_pins=f.pins, expected_source=f.source,
    )
    return SimpleNamespace(
        f=f, state=state, args=args,
        invoke=lambda **changes: C.collect_cho51_selector_evidence(**(args | changes)),
    )


def test_complete_roster_delegates_public_checks_and_preserves_false_gates(boundary):
    b = boundary
    result = b.invoke()
    assert result.rows == b.f.publication_collection.rows
    assert result.selection_claims == b.f.publication_collection.selection_claims
    assert result.publications == b.f.publications and result.receipts == b.f.tensor_collection.receipts
    assert result.owner_decision_sha256 == b.f.owner
    assert result.selection_ceiling_config_sha256 == b.f.ceiling
    assert len(result.selector_claims) == 1020
    for claim, request in zip(result.selector_claims, b.f.requests, strict=True):
        pub = request.publication
        assert claim == C.Cho51SelectorClaim(
            request.plan.case_id, pub.selected_candidate, pub.evidence_sha256,
            pub.selection_contract_sha256, pub.model_state_sha256, pub.method_config_sha256,
        )
    for name in ("full_selector_record_consistency_verified", "complete_tensor_receipt_roster_verified", "native_supervision_verified"):
        assert getattr(result, name) is True
    for name in (
        "full_selector_training_history_verified", "full_selector_evidence_verified",
        "paired_analysis_verified", "selected_publications_verified",
        "selection_publication_tensor_verified", "scientific_result_admitted",
    ):
        assert getattr(result, name) is False
    assert b.state.tensor_calls == 2 and b.state.ceiling_calls == 3
    assert len([e for e in b.state.events if e.startswith("public:")]) == 1020
    assert set(b.state.stable_calls.values()) == {2}
    first = b.f.plans[0].case_id
    assert b.state.events[:3] == ["tensor_1", "ceiling_load", "ceiling_1"]
    assert b.state.events.index("stable_1:" + first) < b.state.events.index("tensor_2")
    assert b.state.events.index("stable_2:" + first) > b.state.events.index("tensor_2")
    with pytest.raises(FrozenInstanceError):
        result.owner_decision_sha256 = "0" * 64
    with pytest.raises(FrozenInstanceError):
        result.selector_claims[0].selected_candidate = "second"


def test_external_sequences_are_snapshotted_before_first_dependency(boundary):
    b = boundary
    requests, pins = list(b.f.requests), list(b.f.pins)
    b.state.mutation = lambda: (requests.clear(), pins.clear())
    assert len(b.invoke(requests=requests, receipt_pins=pins).selector_claims) == 1020
    assert requests == [] and pins == []


@pytest.mark.parametrize("field,value", [
    ("requests", "invalid"), ("requests", ()), ("requests", [object()] * 1020),
    ("receipt_pins", "invalid"), ("receipt_pins", ()), ("receipt_pins", [object()] * 1020),
    ("route", object()), ("publication_collection", object()),
])
def test_malformed_rosters_refused_before_dependencies(boundary, field, value):
    with pytest.raises(ValueError):
        boundary.invoke(**{field: value})
    assert boundary.state.events == []


@pytest.mark.parametrize("field", ["requests", "receipt_pins"])
def test_duplicate_rosters_refused_before_dependencies(boundary, field):
    values = list(boundary.args[field])
    values[-1] = values[0]
    with pytest.raises(ValueError):
        boundary.invoke(**{field: values})
    assert boundary.state.events == []


@pytest.mark.parametrize("kind", ["missing", "duplicate", "untyped", "list"])
def test_all_52_typed_source_catalogs_required(boundary, kind):
    f = boundary.f
    catalogs = f.route.catalogs
    if kind == "missing": catalogs = catalogs[1:]
    if kind == "duplicate": catalogs = catalogs[:-1] + catalogs[:1]
    if kind == "untyped": catalogs = (object(),) + catalogs[1:]
    if kind == "list": catalogs = list(catalogs)
    full = SimpleNamespace(**vars(f.route._full_route))
    full.catalogs = catalogs
    route = C.Cho51WorkerRoute(f.route.contract, full)
    with pytest.raises(ValueError):
        boundary.invoke(route=route)
    assert boundary.state.events == []


@pytest.mark.parametrize("stage", [
    "tensor_1", "ceiling_load", "ceiling_1", "manifest", "store", "public",
    "ceiling_2", "stable_1", "tensor_2", "stable_2", "ceiling_3",
])
def test_dependency_refusals_propagate_without_result(boundary, stage):
    b = boundary
    b.state.fail = (stage + ":" + b.f.plans[0].case_id
                    if stage in {"manifest", "store", "public", "stable_1", "stable_2"} else stage)
    with pytest.raises(ValueError, match="fabricated failure"):
        b.invoke()


@pytest.mark.parametrize("field", ["rows", "selection_claims", "publications", "receipts"])
def test_tensor_result_roster_drift_is_refused(boundary, field):
    boundary.state.before = replace(boundary.f.tensor_collection, **{field: ()})
    with pytest.raises(ValueError, match="tensor receipt collection"):
        boundary.invoke()
    assert boundary.state.events == ["tensor_1"]


@pytest.mark.parametrize("field", ["owner_decision_sha256", "selection_ceiling_config_sha256"])
def test_tensor_result_context_drift_is_refused(boundary, field):
    boundary.state.before = replace(boundary.f.tensor_collection, **{field: _digest("changed")})
    with pytest.raises(ValueError, match="tensor receipt collection"):
        boundary.invoke()


@pytest.mark.parametrize("field,value", [
    ("bundle_sha256", "0" * 64), ("request_sha256", "0" * 64),
    ("native_receipt_file_sha256", "0" * 64), ("witness_file_sha256", "0" * 64),
    ("peak_process_bytes", 0), ("peak_process_bytes", True),
    ("peak_job_bytes", 1), ("peak_job_bytes", True),
])
def test_tensor_binding_drift_or_nonphysical_peaks_refused(boundary, field, value):
    tensor = boundary.f.tensor_collection
    receipts = (replace(tensor.receipts[0], **{field: value}),) + tensor.receipts[1:]
    boundary.state.before = replace(tensor, receipts=receipts)
    with pytest.raises(ValueError, match="tensor receipt binding"):
        boundary.invoke()


def test_late_coherent_tensor_peak_change_is_refused(boundary):
    tensor = boundary.f.tensor_collection
    receipts = (replace(tensor.receipts[0], peak_job_bytes=4096),) + tensor.receipts[1:]
    boundary.state.after = replace(tensor, receipts=receipts)
    with pytest.raises(ValueError, match="changed across"):
        boundary.invoke()


@pytest.mark.parametrize("field,value", [
    ("weights_sha256", "0" * 64), ("manifest_sha256", "0" * 64),
    ("project_root", None), ("manifest_path", None),
])
def test_manifest_witness_must_bind_independent_publication(boundary, field, value):
    boundary.state.manifest_override = lambda w: replace(w, **{field: value})
    with pytest.raises(ValueError, match="manifest witness differs"):
        boundary.invoke()


@pytest.mark.parametrize("mutation", ["contract_pin", "winner", "ceiling_bool", "ceiling_high", "ceiling_zero", "no_contract"])
def test_record_context_and_budget_are_bound_before_public_verifier(boundary, mutation):
    def change(record):
        payload = record["payload"]
        if mutation == "contract_pin": payload["contract_sha256"] = "0" * 64
        if mutation == "winner": payload["selected_candidate"] = "second"
        if mutation == "no_contract": payload["contract"] = []
        if mutation.startswith("ceiling_"):
            payload["contract"]["maximum_gradient_steps"] = {"ceiling_bool": True, "ceiling_high": 5254, "ceiling_zero": 0}[mutation]
        return record
    boundary.state.record_override = change
    with pytest.raises(ValueError):
        boundary.invoke()
    assert not any(event.startswith("public:") for event in boundary.state.events)


def test_derived_static_method_must_match_independent_digest(boundary):
    boundary.state.method_override = _digest("other-method")
    with pytest.raises(ValueError, match="reviewed method configuration"):
        boundary.invoke()


@pytest.mark.parametrize("field,value", [("selected_candidate", "second"), ("evidence_sha256", "0" * 64)])
def test_public_verifier_result_must_match_external_pins(boundary, field, value):
    boundary.state.verified_override = lambda v: replace(v, **{field: value})
    with pytest.raises(ValueError, match="public selector verification"):
        boundary.invoke()


def test_public_verifier_result_requires_exact_type(boundary):
    boundary.state.verified_override = lambda v: SimpleNamespace(
        selected_candidate=v.selected_candidate, evidence_sha256=v.evidence_sha256,
    )
    with pytest.raises(ValueError, match="public selector verification"):
        boundary.invoke()
