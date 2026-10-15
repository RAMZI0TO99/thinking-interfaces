"""Pure fabricated-metadata checks; no publication, tensor or native receipt proof."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.config import canonical_config_json, config_digest
from core.provenance import SourceProvenance
from docs.phase2.cho51_tensor_verification_v1 import contract as C


def digest(label):
    return hashlib.sha256(label.encode()).hexdigest()


@pytest.fixture
def metadata(tmp_path):
    plan = C.CasePlan("cho2017", "subject_02", "eegnet", 5, 11, 1)
    method = {"dataset": "cho2017", "method": "eegnet", "fixture": {"values": [1, 2]}}
    protocol = {"fixture_only": True, "model_seeds": [11, 23, 37, 53, 71]}
    root = tmp_path.absolute()
    manifest_sha = digest("fabricated manifest")
    publication = C.Cho51PublicationBinding(
        plan.case_id, manifest_sha,
        root / "runs" / "phase2" / "selected_sources" / "manifests" / (manifest_sha + ".json"),
        digest("evidence"), digest("selection contract"), "fixture-candidate",
        config_digest(protocol), config_digest(method), digest("environment"),
        digest("recipe"), digest("state"), digest("weights"),
    )
    return dict(
        project_root=root, plan=plan, publication=publication,
        expected_source=SourceProvenance("a" * 40, digest("source"), False),
        method_config=method, protocol_config=protocol,
    )


def witness_payload(request):
    return {
        "schema": C.WITNESS_SCHEMA, "request_sha256": request.sha256,
        "case_id": request.plan.case_id, "training_performed": False,
        **{name: getattr(request.publication, name) for name in C._MATCHED_WITNESS_FIELDS},
    }


def test_request_round_trip_and_detached_payload(metadata):
    request = C.make_tensor_request(**metadata)
    payload = request.payload()
    assert C.load_tensor_request(payload) == request
    assert request.sha256 == config_digest(payload)
    payload["method_config"]["fixture"]["values"].append(99)
    payload["publication"]["selected_candidate"] = "changed"
    metadata["method_config"]["fixture"]["values"].append(100)
    assert request.payload()["method_config"]["fixture"]["values"] == [1, 2]
    assert request.publication.selected_candidate == "fixture-candidate"
    with pytest.raises(FrozenInstanceError):
        request.method_config_json = "{}"


@pytest.mark.parametrize("subject,method,seed", [
    ("subject_02", "labram_linear", 11), ("subject_52", "labram_lora", 23),
    ("subject_11", "labram_full", 37), ("subject_31", "eegnet", 53),
    ("subject_51", "eegnet", 71),
])
def test_adopted_roster_boundary_cases(metadata, subject, method, seed):
    metadata["plan"] = replace(metadata["plan"], target_subject=subject, method=method, model_seed=seed)
    metadata["method_config"]["method"] = method
    metadata["publication"] = replace(
        metadata["publication"], case_id=metadata["plan"].case_id,
        method_config_sha256=config_digest(metadata["method_config"]),
    )
    assert C.make_tensor_request(**metadata).plan == metadata["plan"]


@pytest.mark.parametrize("field,value", [
    ("dataset", "bnci2014"), ("target_subject", "subject_01"),
    ("target_subject", "subject_53"), ("target_subject", "subject_2"),
    ("method", "unknown"), ("shots_per_class", 1), ("model_seed", 12),
    ("repetition", 2),
])
def test_non_adopted_cases_refused(metadata, field, value):
    metadata["plan"] = replace(metadata["plan"], **{field: value})
    with pytest.raises(ValueError):
        C.make_tensor_request(**metadata)


@pytest.mark.parametrize("field", C._PUBLICATION_DIGEST_FIELDS)
@pytest.mark.parametrize("bad_digest", ["g" * 64, "A" * 64, None])
def test_every_publication_digest_is_independently_checked(metadata, field, bad_digest):
    metadata["publication"] = replace(metadata["publication"], **{field: bad_digest})
    with pytest.raises(ValueError):
        C.make_tensor_request(**metadata)


@pytest.mark.parametrize("field,value", [
    ("case_id", digest("different case")), ("selected_candidate", ""),
    ("selected_candidate", " fixture"), ("selected_candidate", "fixture "),
    ("selected_candidate", 1),
])
def test_publication_case_and_candidate_refused(metadata, field, value):
    metadata["publication"] = replace(metadata["publication"], **{field: value})
    with pytest.raises(ValueError):
        C.make_tensor_request(**metadata)


@pytest.mark.parametrize("path_kind", ["relative", "outside", "other_digest", "dotdot", "string"])
def test_manifest_path_requires_exact_absolute_digest_location(metadata, path_kind):
    root = metadata["project_root"]
    path = metadata["publication"].manifest_path
    replacement = {
        "relative": Path("runs/phase2/selected_sources/manifests/x.json"),
        "outside": root.parent / path.name,
        "other_digest": path.with_name(digest("other") + ".json"),
        "dotdot": path.parent / ".." / "manifests" / path.name,
        "string": str(path),
    }[path_kind]
    metadata["publication"] = replace(metadata["publication"], manifest_path=replacement)
    with pytest.raises(ValueError):
        C.make_tensor_request(**metadata)


@pytest.mark.parametrize("field,value", [
    ("project_root", Path("relative")), ("project_root", "D:/not-a-Path"),
    ("plan", None), ("publication", None), ("expected_source", None),
    ("method_config", []), ("protocol_config", []),
])
def test_required_metadata_types(metadata, field, value):
    metadata[field] = value
    with pytest.raises(ValueError):
        C.make_tensor_request(**metadata)


@pytest.mark.parametrize("field,value", [
    ("git_commit", "unversioned-workspace"), ("git_commit", "A" * 40),
    ("git_commit", "a" * 41), ("git_commit", None),
    ("source_sha256", "bad"), ("git_dirty", None), ("git_dirty", 0),
])
def test_source_provenance_is_exact(metadata, field, value):
    metadata["expected_source"] = replace(metadata["expected_source"], **{field: value})
    with pytest.raises(ValueError):
        C.make_tensor_request(**metadata)


@pytest.mark.parametrize("field", ["method_config", "protocol_config"])
def test_config_pin_changes_refused(metadata, field):
    metadata[field]["changed"] = True
    with pytest.raises(ValueError):
        C.make_tensor_request(**metadata)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), object()])
def test_nonfinite_or_nonjson_config_refused(metadata, value):
    metadata["method_config"]["bad"] = value
    with pytest.raises(ValueError):
        C.make_tensor_request(**metadata)


def test_method_identity_is_checked_even_if_its_digest_is_rebound(metadata):
    metadata["method_config"]["method"] = "labram_full"
    metadata["publication"] = replace(
        metadata["publication"], method_config_sha256=config_digest(metadata["method_config"]),
    )
    with pytest.raises(ValueError):
        C.make_tensor_request(**metadata)


def test_direct_request_constructor_cannot_bypass_canonical_json(metadata):
    request = C.make_tensor_request(**metadata)
    with pytest.raises(ValueError):
        replace(request, method_config_json='{"fixture": NaN}')
    with pytest.raises(ValueError):
        replace(request, protocol_config_json='[1,2]')
    with pytest.raises(ValueError):
        replace(request, method_config_json='{"dataset": "cho2017"}')


@pytest.mark.parametrize("field", sorted(C._INPUT_FIELDS))
def test_serialized_request_missing_fields_refused(metadata, field):
    payload = C.make_tensor_request(**metadata).payload()
    payload.pop(field)
    with pytest.raises(ValueError):
        C.load_tensor_request(payload)


@pytest.mark.parametrize("field", ["plan", "publication", "expected_source"])
def test_serialized_nested_schema_is_exact(metadata, field):
    payload = C.make_tensor_request(**metadata).payload()
    payload[field]["extra"] = "refuse"
    with pytest.raises(ValueError):
        C.load_tensor_request(payload)


@pytest.mark.parametrize("kind", ["extra", "schema", "root_type", "path_type", "method_type"])
def test_serialized_request_shape_and_schema_refused(metadata, kind):
    payload = C.make_tensor_request(**metadata).payload()
    if kind == "extra":
        payload["extra"] = True
    elif kind == "schema":
        payload["schema"] = "cho_tensor_case_child_input_v1"
    elif kind == "root_type":
        payload["project_root"] = metadata["project_root"]
    elif kind == "path_type":
        payload["publication"]["manifest_path"] = metadata["publication"].manifest_path
    else:
        payload["method_config"] = []
    with pytest.raises(ValueError):
        C.load_tensor_request(payload)


def test_pure_request_and_witness_admission_performs_no_filesystem_io(metadata, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("pure metadata admission attempted filesystem I/O")

    for name in ("resolve", "stat", "lstat", "read_bytes", "read_text", "open", "exists"):
        monkeypatch.setattr(Path, name, denied)
    request = C.make_tensor_request(**metadata)
    restored = C.load_tensor_request(request.payload())
    assert C.validate_tensor_witness(restored, witness_payload(restored)).case_id == request.plan.case_id


def test_fabricated_digest_witness_never_claims_tensor_or_native_proof(metadata):
    request = C.make_tensor_request(**metadata)
    result = C.validate_tensor_witness(request, witness_payload(request))
    assert result.request_sha256 == request.sha256
    assert result.training_performed is False
    assert result.selected_tensors_verified is False
    assert result.native_supervision_verified is False
    assert result.full_selector_evidence_verified is False
    assert result.scientific_result_admitted is False
    assert request.selected_tensors_verified is False
    assert request.native_supervision_verified is False
    assert request.scientific_result_admitted is False
    with pytest.raises(FrozenInstanceError):
        result.weights_sha256 = digest("changed")


@pytest.mark.parametrize("field", sorted(C._WITNESS_FIELDS))
def test_every_missing_witness_field_refused(metadata, field):
    request = C.make_tensor_request(**metadata)
    payload = witness_payload(request)
    payload.pop(field)
    with pytest.raises(ValueError):
        C.validate_tensor_witness(request, payload)


@pytest.mark.parametrize("field", [
    "schema", "request_sha256", "case_id", *C._MATCHED_WITNESS_FIELDS,
])
def test_every_witness_identity_is_bound(metadata, field):
    request = C.make_tensor_request(**metadata)
    payload = witness_payload(request)
    payload[field] = "other" if field in {"schema", "selected_candidate"} else digest("other")
    with pytest.raises(ValueError):
        C.validate_tensor_witness(request, payload)


@pytest.mark.parametrize("training", [True, 0, None, "false"])
def test_witness_requires_literal_false_training(metadata, training):
    request = C.make_tensor_request(**metadata)
    payload = witness_payload(request)
    payload["training_performed"] = training
    with pytest.raises(ValueError):
        C.validate_tensor_witness(request, payload)


@pytest.mark.parametrize("kind", ["extra", "not_mapping", "untyped_request", "digest_type"])
def test_witness_shape_and_exact_request_required(metadata, kind):
    request = C.make_tensor_request(**metadata)
    payload = witness_payload(request)
    if kind == "extra":
        payload["native_supervision_verified"] = True
    elif kind == "not_mapping":
        payload = []
    elif kind == "untyped_request":
        request = request.payload()
    else:
        payload["weights_sha256"] = 0
    with pytest.raises(ValueError):
        C.validate_tensor_witness(request, payload)


def test_request_digest_binds_source_and_exact_config_snapshots(metadata):
    original = C.make_tensor_request(**metadata)
    changed = deepcopy(metadata)
    changed["expected_source"] = replace(changed["expected_source"], git_dirty=True)
    updated = C.make_tensor_request(**changed)
    assert updated.sha256 != original.sha256
    assert original.method_config_json == canonical_config_json(metadata["method_config"])
    with pytest.raises(ValueError):
        C.validate_tensor_witness(updated, witness_payload(original))
