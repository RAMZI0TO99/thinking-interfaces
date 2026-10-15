"""Prepared composition boundary checks using explicitly mocked stage I/O.

All case identities, rows and claims are fabricated metadata. These tests do
not qualify real assets, persisted recorder construction or selection evidence.
The root-owned guarded integration check exercises actual stage boundaries.
"""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.provenance import SourceProvenance
from docs.phase2.cho51_input_collection_v1 import collection as C
from docs.phase2.cho51_selection_files_v1.selection_files import (
    Cho51SelectionCeilingWitness,
)
from evaluation.phase2_cho_case_inputs import ChoCaseInputPins
from evaluation.phase2_cho_selection_file_bridge import (
    ChoSelectionFileClaim,
    ChoSelectionFileWitness,
)
from evaluation.phase2_records import CellIdentity
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_subject_aggregation import ExpectedCell, ScoreRow


def _digest(label):
    return hashlib.sha256(label.encode()).hexdigest()


@pytest.fixture(scope="module")
def fabricated_metadata():
    source = SourceProvenance("1" * 40, _digest("source"), True)
    methods = {method: _digest(method) for method in (
        "eegnet", "labram_linear", "labram_lora", "labram_full",
    )}
    plans = tuple(
        CasePlan("cho2017", f"subject_{subject:02d}", method, 5, seed, 1)
        for subject in range(2, 53) for method in methods for seed in range(5)
    )
    pins = []
    for plan in plans:
        identity = CellIdentity(
            plan.dataset, plan.target_subject, plan.method, plan.shots_per_class,
            plan.model_seed, None, None, _digest("protocol"), _digest("episode"),
            _digest("source-selection"), methods[plan.method], _digest("preprocessing"),
            _digest("checkpoint"), source.source_sha256, _digest("environment"),
            source.git_commit, source.git_dirty,
        )
        pins.append(C.PinnedCaseCell(
            plan, ExpectedCell(*plan.identity_key), identity, 1,
            _digest("cell:" + plan.case_id), _digest("success:" + plan.case_id),
            _digest("evidence:" + plan.case_id),
        ))
    pins = tuple(pins)
    rows = tuple(ScoreRow(pin.key, 1, 2, pin.cell_sha256) for pin in pins)
    claims = tuple(ChoSelectionFileClaim(
        pin.plan.case_id, pin.selection_evidence_sha256, _digest("contract"),
        "fabricated-candidate", None, None,
    ) for pin in pins)
    return SimpleNamespace(
        pins=pins, rows=rows, claims=claims, methods=methods, source=source,
        owner=_digest("owner"), ceiling=_digest("ceiling"), plans=plans,
    )


@pytest.fixture
def boundary(fabricated_metadata, tmp_path, monkeypatch):
    f = fabricated_metadata
    root = tmp_path.resolve()
    # These collaborators are intentionally mocked. No route, real input,
    # recorder tree or physical selection file is qualified by this suite.
    route = SimpleNamespace(contract=SimpleNamespace(owner_decision_sha256=f.owner))
    recorder = object()
    ceiling = Cho51SelectionCeilingWitness(
        root / "fabricated-ceiling.toml", f.ceiling, (0, 0, 0, 0),
    )
    witness = C.Cho51SelectionFileWitness(
        ChoSelectionFileWitness((), f.claims), ceiling, f.owner,
    )
    state = SimpleNamespace(
        calls=[], collected=C.Cho51RecorderCollection(f.rows, f.owner),
        witness=witness, final_rows=f.rows, fail=None, mutate=None,
        shared_pins=None, shared_methods=None,
    )

    def step(name):
        state.calls.append(name)
        if state.fail == name:
            raise ValueError("fabricated failure: " + name)

    def recorder_stage(project_root, given_route, given_recorder, pins, **kwargs):
        step("recorder")
        assert (project_root, given_route, given_recorder) == (root, route, recorder)
        assert type(pins) is tuple and pins == f.pins
        assert dict(kwargs["method_config_sha256"]) == f.methods
        assert kwargs["expected_source"] is f.source
        assert kwargs["case_input_pins"] is args["case_input_pins"]
        assert kwargs["base_config_sha256"] == args["base_config_sha256"]
        state.shared_pins = pins
        state.shared_methods = kwargs["method_config_sha256"]
        if state.mutate is not None:
            state.mutate()
        return state.collected

    def selection_stage(given_route, given_recorder, pins, **kwargs):
        step("selection")
        assert (given_route, given_recorder) == (route, recorder)
        assert pins is state.shared_pins
        assert kwargs["project_root"] == root
        assert kwargs["expected_source"] is f.source
        assert kwargs["method_config_sha256"] is state.shared_methods
        assert dict(kwargs["method_config_sha256"]) == f.methods
        assert kwargs["selection_ceiling_config_sha256"] == f.ceiling
        return state.witness

    def stable(given_witness):
        assert given_witness is state.witness
        name = "witness_after" if "reread" in state.calls else "witness_before"
        step(name)

    def reread(given_recorder, roster, pins):
        step("reread")
        assert given_recorder is recorder and pins is state.shared_pins
        assert roster == tuple(pin.key for pin in f.pins)
        return state.final_rows

    monkeypatch.setattr(C, "collect_recorder_rows", recorder_stage)
    monkeypatch.setattr(C, "verify_cho51_recorded_selection_files", selection_stage)
    monkeypatch.setattr(C.Cho51SelectionFileWitness, "verify_stable", stable)
    monkeypatch.setattr(C, "verified_score_rows", reread)
    args = dict(
        project_root=root, route=route, recorder=recorder, pins=f.pins,
        case_input_pins=ChoCaseInputPins(*(_digest(name) for name in (
            "protocol", "threshold", "cohort", "variant",
        ))),
        base_config_sha256=_digest("base"), method_config_sha256=dict(f.methods),
        expected_source=f.source, selection_ceiling_config_sha256=f.ceiling,
    )

    def invoke(**changes):
        return C.collect_cho51_input_selection(**(args | changes))

    return SimpleNamespace(state=state, f=f, args=args, invoke=invoke)


ORDER = ["recorder", "selection", "witness_before", "reread", "witness_after"]


def test_ordered_same_pin_composition_is_immutable_and_still_incomplete(boundary):
    b = boundary
    result = b.invoke()
    assert b.state.calls == ORDER
    assert result.rows == b.f.rows and result.selection_claims == b.f.claims
    assert result.owner_decision_sha256 == b.f.owner
    assert result.selection_ceiling_config_sha256 == b.f.ceiling
    assert all(getattr(result, name) is False for name in (
        "selected_publications_verified", "selected_tensors_verified",
        "full_selector_evidence_verified", "selection_publication_tensor_verified",
        "scientific_result_admitted",
    ))
    with pytest.raises(FrozenInstanceError):
        result.owner_decision_sha256 = "0" * 64


def test_callers_mutable_pin_and_method_containers_are_snapshotted_once(boundary):
    b = boundary
    original_pins, original_methods = list(b.f.pins), dict(b.f.methods)

    def mutate_originals():
        original_pins.clear()
        original_methods.clear()

    b.state.mutate = mutate_originals
    result = b.invoke(pins=original_pins, method_config_sha256=original_methods)
    assert result.rows == b.f.rows and b.state.calls == ORDER
    with pytest.raises(TypeError):
        b.state.shared_methods["eegnet"] = "0" * 64


@pytest.mark.parametrize("change", ["missing", "duplicate", "untyped"])
def test_bad_pin_roster_stops_before_any_stage(boundary, change):
    pins = boundary.f.pins
    if change == "missing":
        pins = pins[:-1]
    elif change == "duplicate":
        pins = pins[:-1] + (pins[0],)
    else:
        pins = (object(),) + pins[1:]
    with pytest.raises(ValueError, match="typed external case pins"):
        boundary.invoke(pins=pins)
    assert boundary.state.calls == []


@pytest.mark.parametrize("digest", ["bad", None])
def test_missing_or_malformed_ceiling_pin_stops_before_any_stage(boundary, digest):
    with pytest.raises(ValueError):
        boundary.invoke(selection_ceiling_config_sha256=digest)
    assert boundary.state.calls == []


@pytest.mark.parametrize("change", ["missing", "duplicate", "digest"])
def test_initial_row_binding_refuses_stage_output_drift(boundary, change):
    b = boundary
    rows = b.f.rows
    if change == "missing":
        rows = rows[:-1]
    elif change == "duplicate":
        rows = rows[:-1] + (rows[0],)
    else:
        rows = (replace(rows[0], cell_sha256="0" * 64),) + rows[1:]
    b.state.collected = replace(b.state.collected, rows=rows)
    with pytest.raises(ValueError, match="recorder rows differ"):
        b.invoke()
    assert b.state.calls == ["recorder"]


@pytest.mark.parametrize("change", ["missing", "duplicate", "id", "evidence"])
def test_claim_binding_refuses_stage_output_drift(boundary, change):
    b = boundary
    claims = b.f.claims
    if change == "missing":
        claims = claims[:-1]
    elif change == "duplicate":
        claims = claims[:-1] + (claims[0],)
    elif change == "id":
        claims = (replace(claims[0], case_id="0" * 64),) + claims[1:]
    else:
        claims = (replace(claims[0], evidence_sha256="0" * 64),) + claims[1:]
    b.state.witness = replace(
        b.state.witness, selection_files=ChoSelectionFileWitness((), claims),
    )
    with pytest.raises(ValueError, match="selection claims differ"):
        b.invoke()
    assert b.state.calls == ["recorder", "selection"]


@pytest.mark.parametrize("stage", ORDER)
def test_each_stage_failure_stops_all_later_work(boundary, stage):
    b = boundary
    b.state.fail = stage
    with pytest.raises(ValueError, match="fabricated failure: " + stage):
        b.invoke()
    assert b.state.calls == ORDER[:ORDER.index(stage) + 1]


@pytest.mark.parametrize("change", ["recorder", "selection", "ceiling"])
def test_owner_and_ceiling_binding_refuses_mixed_stage_evidence(boundary, change):
    b = boundary
    if change == "recorder":
        b.state.collected = replace(b.state.collected, owner_decision_sha256="0" * 64)
    elif change == "selection":
        b.state.witness = replace(b.state.witness, owner_decision_sha256="0" * 64)
    else:
        b.state.witness = replace(
            b.state.witness,
            ceiling=replace(b.state.witness.ceiling, expected_sha256="0" * 64),
        )
    with pytest.raises(ValueError, match="differs from"):
        b.invoke()
    assert b.state.calls == (["recorder"] if change == "recorder" else ["recorder", "selection"])


def test_same_cell_digest_with_different_final_score_is_refused(boundary):
    b = boundary
    b.state.final_rows = (replace(b.f.rows[0], numerator=0),) + b.f.rows[1:]
    with pytest.raises(ValueError, match="recorder rows changed"):
        b.invoke()
    assert b.state.calls == ORDER[:-1]


def test_final_reread_must_still_bind_to_external_pins(boundary):
    b = boundary
    b.state.final_rows = (
        replace(b.f.rows[0], cell_sha256="0" * 64),
    ) + b.f.rows[1:]
    with pytest.raises(ValueError, match="recorder rows differ"):
        b.invoke()
    assert b.state.calls == ORDER[:-1]
