"""Prepared fabricated-roster checks, with native admission deliberately mocked.

Passing these tests establishes no actual 1,020-case tensor execution. Only
the small physical-file helper checks below use real temporary file bytes.
"""
from __future__ import annotations

import hashlib
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from types import SimpleNamespace

import pytest

from core.config import canonical_config_json, config_digest
from docs.phase2.cho51_tensor_collection_v1 import collection as C
from docs.phase2.cho51_tensor_verification_v1.contract import make_tensor_request


def _sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _unchecked(original, **changes):
    result = object.__new__(type(original))
    for field in fields(original):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(original, field.name)))
    return result


@pytest.fixture(scope="module")
def fabricated():
    root = C.tensor_launcher.ROOT / "runs/phase2/fabricated_tensor_receipt_roster_v1"
    source = C.SourceProvenance("a" * 40, _sha("fabricated-source"), True)
    protocol = {"fabricated": True}
    method_configs = {m: {"dataset": "cho2017", "method": m} for m in C.SELECTED_METHODS}
    methods = {m: config_digest(value) for m, value in method_configs.items()}
    plans = tuple(C.CasePlan("cho2017", f"subject_{s:02d}", m, 5, seed, 1)
                  for s in range(2, 53) for m in C.SELECTED_METHODS for seed in C.SELECTED_SEEDS)
    owner, ceiling = _sha("fabricated-owner"), _sha("fabricated-ceiling")
    publications, claims, requests, pins, rows = [], [], [], [], []
    for plan in plans:
        manifest = _sha("manifest:" + plan.case_id)
        publication = C.Cho51PublicationBinding(
            plan.case_id, manifest, root / "runs/phase2/selected_sources/manifests" / (manifest + ".json"),
            _sha("evidence:" + plan.case_id), _sha("contract:" + plan.case_id), "fabricated-candidate",
            config_digest(protocol), methods[plan.method], _sha("environment"),
            _sha("recipe:" + plan.case_id), _sha("checkpoint:" + plan.case_id), _sha("weights:" + plan.case_id),
        )
        request = make_tensor_request(project_root=root, plan=plan, publication=publication,
                                      expected_source=source, method_config=method_configs[plan.method], protocol_config=protocol)
        directory = C.tensor_launcher.ROOT / "runs/coordination" / ("fabricated_tensor_" + plan.case_id)
        pin = C.Cho51TensorReceiptPin(
            plan.case_id, request.sha256, _sha("bundle:" + plan.case_id), directory / "bundle.json",
            C.tensor_launcher.ROOT / "runs/migration" / ("fabricated_native_" + plan.case_id),
            _sha("native-receipt:" + plan.case_id), _sha("witness:" + plan.case_id),
        )
        publications.append(publication)
        claims.append(C.ChoSelectionFileClaim(
            plan.case_id, publication.evidence_sha256, publication.selection_contract_sha256,
            publication.selected_candidate, manifest, publication.manifest_path.relative_to(root).as_posix(),
        ))
        requests.append(request)
        pins.append(pin)
        rows.append(C.ScoreRow(C.ExpectedCell(*plan.identity_key), 1, 2, _sha("cell:" + plan.case_id)))
    route = C.Cho51WorkerRoute(SimpleNamespace(plans=plans, method_config_sha256=methods, owner_decision_sha256=owner),
                              SimpleNamespace(protocol_config_json=canonical_config_json(protocol)))
    collection = C.Cho51PublicationCollection(tuple(rows), tuple(claims), tuple(publications), owner, ceiling)
    return SimpleNamespace(root=root, source=source, route=route, collection=collection,
                           requests=tuple(requests), pins=tuple(pins), plans=plans)


@pytest.fixture
def boundary(fabricated, monkeypatch):
    f = fabricated
    args = dict(project_root=f.root, route=f.route, publication_collection=f.collection,
                requests=f.requests, receipt_pins=f.pins, expected_source=f.source)
    state = SimpleNamespace(events=[], admissions=0, bundle_override=None, payload_override=None,
                            result_override=None, witness_override=None, physical_override=None, fail=None)
    by_bundle = {p.bundle_path: (r, p) for r, p in zip(f.requests, f.pins, strict=True)}
    by_input = {p.bundle_path.parent / "input.json": (r, p) for r, p in zip(f.requests, f.pins, strict=True)}
    by_witness = {p.bundle_path.parent / "witness.json": (r, p) for r, p in zip(f.requests, f.pins, strict=True)}
    true_digests = {}
    for request, pin in zip(f.requests, f.pins, strict=True):
        true_digests.update({pin.bundle_path: pin.bundle_sha256,
                            pin.bundle_path.parent / "input.json": _sha("input:" + pin.case_id),
                            pin.native_directory / "receipt.json": pin.native_receipt_file_sha256,
                            pin.bundle_path.parent / "witness.json": pin.witness_file_sha256,
                            pin.native_directory / "admission.json": _sha("admission:" + pin.case_id),
                            pin.bundle_path.parent / "child-scope.json": _sha("scope:" + pin.case_id)})

    def load(path, expected):
        state.events.append("bundle")
        if state.fail == "bundle":
            raise ValueError("fabricated bundle refusal")
        request, pin = by_bundle[path]
        if expected != pin.bundle_sha256:
            raise ValueError("fabricated independent bundle digest differs")
        bundle = dict(request_sha256=pin.request_sha256, request_root=str(request.project_root),
                      workspace=str(path.parent), input_path=str(path.parent / "input.json"),
                      input_file_sha256=_sha("input:" + pin.case_id), witness_path=str(path.parent / "witness.json"))
        return state.bundle_override(bundle) if state.bundle_override else bundle

    def read(path, *, expected_sha256):
        state.events.append("read")
        if state.fail == "read" or expected_sha256 != true_digests[path]:
            raise ValueError("fabricated independently pinned read refused")
        if path in by_input:
            request, _ = by_input[path]
            value = request.payload()
            return state.payload_override(value) if state.payload_override else value
        request, pin = by_witness[path]
        pub = request.publication
        value = dict(schema="cho51_tensor_child_witness_v1", request_sha256=pin.request_sha256,
                     case_id=pin.case_id, training_performed=False,
                     **{k: getattr(pub, k) for k in ("manifest_sha256", "evidence_sha256", "selected_candidate",
                                                   "model_recipe_sha256", "model_state_sha256", "weights_sha256")})
        return state.witness_override(value) if state.witness_override else value

    def physical(path, expected=None):
        state.events.append("physical")
        if state.fail == "physical" or expected is not None and expected != true_digests[path]:
            raise ValueError("fabricated physical proof differs")
        value = (0, str(path), 1, 2, 3, true_digests[path])
        return state.physical_override(path, value) if state.physical_override else value

    def admit(bundle, sha, native):
        state.events.append("native")
        state.admissions += 1
        if state.fail == "native":
            raise ValueError("fabricated native refusal")
        request, pin = by_bundle[C.Path(bundle["workspace"]) / "bundle.json"]
        assert native == pin.native_directory and sha == pin.bundle_sha256
        value = dict(schema="cho51_tensor_native_result_v1", request_sha256=pin.request_sha256,
                     case_id=pin.case_id, native_directory=str(native),
                     receipt_file_sha256=pin.native_receipt_file_sha256, witness_file_sha256=pin.witness_file_sha256,
                     bundle_sha256=sha, native_supervision_verified=True, one_case_tensor_digest_verified=True,
                     full_roster_verified=False, full_selector_evidence_verified=False, scientific_admission=False,
                     peak_process_bytes=128, peak_job_bytes=256)
        return state.result_override(value) if state.result_override else value

    monkeypatch.setattr(C.tensor_launcher, "load_bundle", load)
    monkeypatch.setattr(C.tensor_launcher, "read_json", read)
    monkeypatch.setattr(C.tensor_launcher, "admit_native_receipt", admit)
    monkeypatch.setattr(C, "_physical", physical)
    return f, args, state


def test_exact_roster_twice_immutable_and_science_flags(boundary):
    f, args, state = boundary
    result = C.collect_cho51_tensor_receipts(**args)
    assert state.admissions == 2040
    assert tuple(r.case_id for r in result.receipts) == tuple(p.case_id for p in f.plans)
    assert result.rows is f.collection.rows and result.selection_claims is f.collection.selection_claims
    assert result.publications is f.collection.publications
    assert result.complete_tensor_receipt_roster_verified is True
    assert result.native_supervision_verified is True and result.selected_tensors_verified is True
    for name in ("full_selector_evidence_verified", "selected_publications_verified",
                 "selection_publication_tensor_verified", "scientific_result_admitted"):
        assert getattr(result, name) is False
    with pytest.raises(FrozenInstanceError):
        result.receipts = ()
    with pytest.raises(FrozenInstanceError):
        result.receipts[0].case_id = "0" * 64


def test_input_order_normalized_and_lists_snapshotted(boundary):
    f, args, _ = boundary
    args["requests"] = list(reversed(f.requests))
    args["receipt_pins"] = list(reversed(f.pins))
    result = C.collect_cho51_tensor_receipts(**args)
    assert tuple(r.case_id for r in result.receipts) == tuple(p.case_id for p in f.plans)


@pytest.mark.parametrize("field", ["requests", "receipt_pins"])
@pytest.mark.parametrize("kind", ["missing", "duplicate", "extra", "string", "untyped"])
def test_bad_roster_rejected_before_io(boundary, field, kind):
    f, args, state = boundary
    original = args[field]
    args[field] = {"missing": original[:-1], "duplicate": (*original[:-1], original[0]),
                   "extra": (*original, original[0]), "string": "bad", "untyped": (object(), *original[1:])}[kind]
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)
    assert state.events == []


@pytest.mark.parametrize("field", ["bundle_path", "native_directory", "request_sha256"])
def test_each_case_needs_distinct_native_proof(boundary, field):
    f, args, state = boundary
    changed = replace(f.pins[1], **{field: getattr(f.pins[0], field)})
    args["receipt_pins"] = (f.pins[0], changed, *f.pins[2:])
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)
    assert state.events == []


@pytest.mark.parametrize("kind", ["subject01", "seed", "repetition", "shots", "source", "root", "method_json", "protocol_json", "publication"])
def test_request_metadata_drift_rejected_before_io(boundary, kind):
    f, args, state = boundary
    r = f.requests[0]
    changes = {
        "subject01": dict(plan=replace(r.plan, target_subject="subject_01")),
        "seed": dict(plan=replace(r.plan, model_seed=12)),
        "repetition": dict(plan=replace(r.plan, repetition=2)),
        "shots": dict(plan=replace(r.plan, shots_per_class=6)),
        "source": dict(expected_source=replace(r.expected_source, git_dirty=False)),
        "root": dict(project_root=r.project_root / "other"),
        "method_json": dict(method_config_json=canonical_config_json({"dataset": "cho2017", "method": r.plan.method, "drift": True})),
        "protocol_json": dict(protocol_config_json=canonical_config_json({"drift": True})),
        "publication": dict(publication=replace(r.publication, weights_sha256=_sha("drift"))),
    }[kind]
    args["requests"] = (_unchecked(r, **changes), *f.requests[1:])
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)
    assert state.events == []


@pytest.mark.parametrize("field", ["owner_decision_sha256", "selection_ceiling_config_sha256", "rows", "selection_claims", "publications"])
def test_publication_collection_metadata_rejected_before_io(boundary, field):
    f, args, state = boundary
    value = "bad" if field in {"owner_decision_sha256", "selection_ceiling_config_sha256"} else getattr(f.collection, field)[:-1]
    args["publication_collection"] = replace(f.collection, **{field: value})
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)
    assert state.events == []


@pytest.mark.parametrize("field,value", [
    ("numerator", -1), ("numerator", 3), ("numerator", True), ("numerator", 0.5),
    ("denominator", 0), ("denominator", -1), ("denominator", True), ("denominator", 2.0),
    ("cell_sha256", "bad"), ("cell_sha256", 123),
])
def test_unchecked_score_scalars_rejected_before_io(boundary, field, value):
    f, args, state = boundary
    invalid = _unchecked(f.collection.rows[0], **{field: value})
    args["publication_collection"] = replace(f.collection, rows=(invalid, *f.collection.rows[1:]))
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)
    assert state.events == []


@pytest.mark.parametrize("field,value", [
    ("dataset", ""), ("dataset", []), ("subject", " subject_02"), ("method", None),
    ("shots", True), ("shots", 0), ("seed", -1), ("seed", 11.0),
])
def test_unchecked_score_key_fields_rejected_before_io(boundary, field, value):
    f, args, state = boundary
    key = _unchecked(f.collection.rows[0].key, **{field: value})
    invalid = _unchecked(f.collection.rows[0], key=key)
    args["publication_collection"] = replace(f.collection, rows=(invalid, *f.collection.rows[1:]))
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)
    assert state.events == []


@pytest.mark.parametrize("field", ["evidence_sha256", "contract_sha256", "selected_candidate", "manifest_sha256", "manifest_path"])
def test_claim_drift_rejected_before_io(boundary, field):
    f, args, state = boundary
    claim = replace(f.collection.selection_claims[0], **{field: "drift"})
    args["publication_collection"] = replace(f.collection, selection_claims=(claim, *f.collection.selection_claims[1:]))
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)
    assert state.events == []


@pytest.mark.parametrize("field", ["case_id", "request_sha256", "bundle_sha256", "native_receipt_file_sha256", "witness_file_sha256"])
def test_malformed_pin_digest_rejected_before_io(boundary, field):
    f, args, state = boundary
    args["receipt_pins"] = (_unchecked(f.pins[0], **{field: "bad"}), *f.pins[1:])
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)
    assert state.events == []


@pytest.mark.parametrize("field", ["bundle_sha256", "native_receipt_file_sha256", "witness_file_sha256"])
def test_independent_pin_mismatch_refused(boundary, field):
    f, args, _ = boundary
    args["receipt_pins"] = (replace(f.pins[0], **{field: _sha("drift")}), *f.pins[1:])
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)


@pytest.mark.parametrize("field", ["request_sha256", "request_root", "workspace"])
def test_loaded_bundle_binding_drift_refused(boundary, field):
    _, args, state = boundary
    state.bundle_override = lambda value: {**value, field: "drift"}
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)


@pytest.mark.parametrize("field", ["schema", "project_root", "plan", "publication", "expected_source", "method_config", "protocol_config"])
def test_complete_input_payload_equality_required(boundary, field):
    _, args, state = boundary
    state.payload_override = lambda value: {**value, field: "drift"}
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)


@pytest.mark.parametrize("field", ["schema", "request_sha256", "case_id", "native_directory", "receipt_file_sha256", "witness_file_sha256", "bundle_sha256"])
def test_native_result_binding_drift_refused(boundary, field):
    _, args, state = boundary
    state.result_override = lambda value: {**value, field: "drift"}
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)


@pytest.mark.parametrize("field,value", [("native_supervision_verified", False), ("native_supervision_verified", 1),
    ("one_case_tensor_digest_verified", False), ("full_roster_verified", True),
    ("full_selector_evidence_verified", True), ("scientific_admission", True),
    ("peak_process_bytes", 0), ("peak_process_bytes", True), ("peak_process_bytes", 2048 * 1024**2 + 1),
    ("peak_job_bytes", 0), ("peak_job_bytes", 3072 * 1024**2 + 1)])
def test_native_result_flags_and_measured_limits(boundary, field, value):
    _, args, state = boundary
    state.result_override = lambda original: {**original, field: value}
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)


@pytest.mark.parametrize("kind", ["extra", "missing", "not_plain_dict"])
def test_native_result_exact_fields(boundary, kind):
    _, args, state = boundary
    def changed(value):
        if kind == "extra":
            return {**value, "unreviewed": True}
        if kind == "missing":
            return {key: item for key, item in value.items() if key != "peak_job_bytes"}
        class Derived(dict):
            pass
        return Derived(value)
    state.result_override = changed
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)


@pytest.mark.parametrize("field", ["schema", "request_sha256", "case_id", "manifest_sha256", "evidence_sha256", "selected_candidate", "model_recipe_sha256", "model_state_sha256", "weights_sha256", "training_performed"])
def test_witness_bound_to_exact_request(boundary, field):
    _, args, state = boundary
    state.witness_override = lambda value: {**value, field: "drift"}
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)


@pytest.mark.parametrize("stage", ["bundle", "read", "physical", "native"])
def test_dependency_failure_propagates(boundary, stage):
    _, args, state = boundary
    state.fail = stage
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)


@pytest.mark.parametrize("filename", ["bundle.json", "input.json", "receipt.json", "witness.json", "admission.json", "child-scope.json"])
def test_first_case_same_byte_replacement_during_later_case_refused(boundary, filename):
    f, args, state = boundary
    pin = f.pins[0]
    path = (pin.native_directory if filename in {"receipt.json", "admission.json"} else pin.bundle_path.parent) / filename
    state.physical_override = lambda current, value: (value[0], "replaced", *value[2:]) if current == path and state.admissions >= 1020 else value
    with pytest.raises(ValueError, match="earlier native tensor proof"):
        C.collect_cho51_tensor_receipts(**args)


def test_late_native_admission_drift_refused(boundary):
    _, args, state = boundary
    state.result_override = lambda value: {**value, "peak_job_bytes": 257} if state.admissions > 1020 else value
    with pytest.raises(ValueError, match="earlier native tensor proof"):
        C.collect_cho51_tensor_receipts(**args)


def test_no_public_executor_or_launch_hook():
    parameters = inspect.signature(C.collect_cho51_tensor_receipts).parameters
    assert set(parameters) == {"project_root", "route", "publication_collection", "requests", "receipt_pins", "expected_source"}


@pytest.mark.parametrize("kind", ["relative_bundle", "relative_native", "coordination_root", "wrong_native_parent", "wrong_bundle_name"])
def test_bad_receipt_paths_rejected_before_io(boundary, kind):
    f, args, state = boundary
    pin = f.pins[0]
    changes = {
        "relative_bundle": dict(bundle_path=C.Path("relative/bundle.json")),
        "relative_native": dict(native_directory=C.Path("relative/native")),
        "coordination_root": dict(bundle_path=C.tensor_launcher.ROOT / "runs/coordination/bundle.json"),
        "wrong_native_parent": dict(native_directory=C.tensor_launcher.ROOT / "runs/coordination/native"),
        "wrong_bundle_name": dict(bundle_path=pin.bundle_path.with_name("other.json")),
    }[kind]
    args["receipt_pins"] = (_unchecked(pin, **changes), *f.pins[1:])
    with pytest.raises(ValueError):
        C.collect_cho51_tensor_receipts(**args)
    assert state.events == []


@pytest.mark.parametrize("kind", ["empty", "oversized", "directory"])
def test_real_small_proof_helper_refuses_unbounded_or_nonregular(tmp_path, kind):
    path = tmp_path / "proof.json"
    if kind == "directory":
        path.mkdir()
    else:
        path.write_bytes(b"" if kind == "empty" else b"x" * (1024**2 + 1))
    with pytest.raises(ValueError, match="bounded single-linked"):
        C._physical(path)


def test_real_small_physical_file_identity_and_external_digest(tmp_path):
    path = tmp_path / "proof.json"
    path.write_bytes(b"fabricated-small-proof")
    before = C._physical(path, hashlib.sha256(path.read_bytes()).hexdigest())
    assert C._physical(path) == before
    successor = tmp_path / "successor.json"
    successor.write_bytes(path.read_bytes())
    successor.replace(path)
    assert C._physical(path) != before
    with pytest.raises(ValueError):
        C._physical(path, "0" * 64)
