"""Prepared boundary checks with fabricated metadata and mocked stage I/O.

No test below qualifies actual study inputs, recorder/publication bytes,
tensors or scientific outcomes. The two hybrid cases use tiny fabricated
publication files. Other checks replace stage dependencies and temporarily
patch reused witness class methods; pytest restores those methods afterward.
"""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, asdict, replace
from types import SimpleNamespace

import pytest

from core.provenance import SourceProvenance
from core.config import canonical_config_json, config_digest
from docs.phase2.cho51_publication_collection_v1 import collection as C
from docs.phase2.cho51_selection_files_v1.selection_files import Cho51SelectionCeilingWitness
from evaluation.phase2_cho_selection_file_bridge import ChoSelectionFileWitness
from evaluation.phase2_records import CellIdentity
from evaluation.phase2_records import envelope
from evaluation.phase2_cho_selected_manifest_bridge import (
    verify_cho_selected_manifest_files as _real_manifest_verifier,
)
from evaluation.phase2_cho_selection_file_bridge import _evidence_path as _real_evidence_path
from evaluation.phase2_subject_aggregation import ExpectedCell, ScoreRow

_REAL_MANIFEST_STABLE = C.ChoSelectedManifestWitness.verify_stable


def _digest(label):
    return hashlib.sha256(label.encode()).hexdigest()


@pytest.fixture(scope="module")
def fabricated_metadata():
    source = SourceProvenance("1" * 40, _digest("source"), True)
    methods = {method: _digest(method) for method in C.SELECTED_METHODS}
    plans = tuple(
        C.CasePlan("cho2017", f"subject_{subject:02d}", method, 5, seed, 1)
        for subject in range(2, 53) for method in methods for seed in C.SELECTED_SEEDS
    )
    pins = []
    for plan in plans:
        identity = CellIdentity(
            plan.dataset, plan.target_subject, plan.method, plan.shots_per_class,
            plan.model_seed, None, None, _digest("protocol"), _digest("episode"),
            _digest("source-selection"), methods[plan.method], _digest("preprocessing"),
            _digest("checkpoint:" + plan.case_id), source.source_sha256,
            _digest("environment"), source.git_commit, source.git_dirty,
        )
        pins.append(C.PinnedCaseCell(
            plan, ExpectedCell(*plan.identity_key), identity, 1,
            _digest("cell:" + plan.case_id), _digest("success:" + plan.case_id),
            _digest("evidence:" + plan.case_id),
        ))
    pins = tuple(pins)
    publications = tuple(C.ChoSelectedSourcePin(
        pin.plan.case_id, _digest("manifest:" + pin.plan.case_id),
        _digest("recipe:" + pin.plan.case_id), pin.identity.environment_sha256,
    ) for pin in pins)
    claims = tuple(C.ChoSelectionFileClaim(
        pin.plan.case_id, pin.selection_evidence_sha256,
        _digest("contract:" + pin.plan.case_id), "fabricated-candidate",
        publication.manifest_sha256,
        "runs/phase2/selected_sources/manifests/" + publication.manifest_sha256 + ".json",
    ) for pin, publication in zip(pins, publications, strict=True))
    return SimpleNamespace(
        source=source, methods=methods, plans=plans, pins=pins,
        publications=publications, claims=claims,
        rows=tuple(ScoreRow(pin.key, 1, 2, pin.cell_sha256) for pin in pins),
        owner=_digest("owner"), ceiling=_digest("ceiling"),
    )


@pytest.fixture
def boundary(fabricated_metadata, tmp_path, monkeypatch):
    f = fabricated_metadata
    root = tmp_path.resolve()
    route = C.Cho51WorkerRoute(SimpleNamespace(
        plans=f.plans, method_config_sha256=dict(f.methods), owner_decision_sha256=f.owner,
    ), None)
    # Avoid constructor writes. The real collector is replaced below, so this
    # exact typed placeholder is never asked to act as a persisted recorder.
    recorder = object.__new__(C.CaseRecorder)
    selection = C.Cho51SelectionFileWitness(
        ChoSelectionFileWitness((), f.claims),
        Cho51SelectionCeilingWitness(root / "fabricated.toml", f.ceiling, (0, 0, 0, 0)),
        f.owner,
    )
    state = SimpleNamespace(
        events=[], input=C.Cho51InputCollection(f.rows, f.claims, f.owner, f.ceiling),
        fixture_pins=f.pins,
        selection=selection, rows_before=f.rows, rows_after=f.rows,
        selected_pins=None, methods=None, mutation=None, fail=None,
        selection_checks=0, ledger_checks=0, manifest_checks={}, manifest_override=None,
    )

    def step(name):
        state.events.append(name)
        if state.fail == name:
            raise ValueError("fabricated failure: " + name)

    def input_stage(project_root, given_route, given_recorder, pins, **kwargs):
        step("input")
        assert (project_root, given_route, given_recorder) == (root, route, recorder)
        assert type(pins) is tuple and pins == state.fixture_pins
        assert dict(kwargs["method_config_sha256"]) == f.methods
        assert kwargs["expected_source"] is f.source
        assert kwargs["case_input_pins"] is args["case_input_pins"]
        assert kwargs["base_config_sha256"] == args["base_config_sha256"]
        assert kwargs["selection_ceiling_config_sha256"] == f.ceiling
        state.selected_pins, state.methods = pins, kwargs["method_config_sha256"]
        if state.mutation is not None:
            state.mutation()
        return state.input

    def selection_stage(given_route, given_recorder, pins, **kwargs):
        step("selection")
        assert (given_route, given_recorder) == (route, recorder)
        assert pins is state.selected_pins and kwargs["method_config_sha256"] is state.methods
        assert kwargs["project_root"] == root and kwargs["expected_source"] is f.source
        assert kwargs["selection_ceiling_config_sha256"] == f.ceiling
        return state.selection

    def stable_selection(witness):
        assert witness is state.selection
        state.selection_checks += 1
        step("selection_stable_" + str(state.selection_checks))

    def ledger(given_recorder, roster, pins):
        state.ledger_checks += 1
        step("ledger_" + str(state.ledger_checks))
        assert given_recorder is recorder and pins is state.selected_pins
        assert roster == tuple(pin.key for pin in f.pins)
        return state.rows_before if state.ledger_checks == 1 else state.rows_after

    by_manifest = {publication.manifest_sha256: publication for publication in f.publications}
    by_case = {pin.plan.case_id: pin for pin in f.pins}
    claims_by_case = {claim.case_id: claim for claim in f.claims}

    def path_for(given_root, value):
        assert given_root == root
        digest = value.rsplit("/", 1)[-1].removesuffix(".json")
        step("path:" + by_manifest[digest].case_id)
        return root.joinpath(*value.split("/"))

    def manifest(given_root, manifest_path, **kwargs):
        publication = by_manifest[kwargs["manifest_sha256"]]
        case_id = publication.case_id
        step("manifest:" + case_id)
        pin, claim = by_case[case_id], claims_by_case[case_id]
        assert given_root == root
        assert manifest_path == root.joinpath(*claim.manifest_path.split("/"))
        assert kwargs == dict(
            manifest_sha256=publication.manifest_sha256,
            evidence_sha256=pin.selection_evidence_sha256,
            selection_contract_sha256=claim.contract_sha256,
            selected_candidate=claim.selected_candidate,
            protocol_config_sha256=pin.identity.protocol_sha256,
            expected_source=f.source, model_recipe_sha256=publication.model_recipe_sha256,
            model_state_sha256=pin.identity.checkpoint_sha256,
        )
        witness = C.ChoSelectedManifestWitness(
            root, manifest_path, publication.manifest_sha256, _digest("manifest-file"),
            (0, 0, 0, 0), root / "fabricated-evidence", _digest("evidence-file"),
            (0, 0, 0, 0), 1, root / "fabricated-weights", _digest("weights:" + case_id),
            (0, 0, 0, 0),
        )
        return state.manifest_override(witness) if state.manifest_override else witness

    def stable_manifest(witness):
        case_id = by_manifest[witness.manifest_sha256].case_id
        count = state.manifest_checks.get(case_id, 0) + 1
        state.manifest_checks[case_id] = count
        step("manifest_stable_" + str(count) + ":" + case_id)

    monkeypatch.setattr(C, "collect_cho51_input_selection", input_stage)
    monkeypatch.setattr(C, "verify_cho51_recorded_selection_files", selection_stage)
    monkeypatch.setattr(C.Cho51SelectionFileWitness, "verify_stable", stable_selection)
    monkeypatch.setattr(C, "verified_score_rows", ledger)
    monkeypatch.setattr(C, "_evidence_path", path_for)
    monkeypatch.setattr(C, "verify_cho_selected_manifest_files", manifest)
    monkeypatch.setattr(C.ChoSelectedManifestWitness, "verify_stable", stable_manifest)
    args = dict(
        project_root=root, route=route, recorder=recorder, pins=f.pins,
        selected_source_pins=f.publications,
        case_input_pins=C.ChoCaseInputPins(*(_digest(label) for label in (
            "protocol-file", "threshold-file", "cohort-file", "variant-file",
        ))),
        base_config_sha256=_digest("base"), method_config_sha256=dict(f.methods),
        expected_source=f.source, selection_ceiling_config_sha256=f.ceiling,
    )
    return SimpleNamespace(
        f=f, state=state, args=args, route=route,
        invoke=lambda **changes: C.collect_cho51_publication_files(**(args | changes)),
    )


def test_complete_metadata_binding_is_immutable_and_only_bytes_admitted(boundary):
    b = boundary
    result = b.invoke()
    assert result.rows == b.f.rows and result.selection_claims == b.f.claims
    assert len(result.publications) == 1020
    for row, pin, publication, claim in zip(
        result.publications, b.f.pins, b.f.publications, b.f.claims, strict=True,
    ):
        assert row == C.Cho51PublicationBinding(
            pin.plan.case_id, publication.manifest_sha256,
            b.args["project_root"].joinpath(*claim.manifest_path.split("/")),
            claim.evidence_sha256, claim.contract_sha256, claim.selected_candidate,
            pin.identity.protocol_sha256, b.f.methods[pin.plan.method],
            publication.environment_sha256, publication.model_recipe_sha256,
            pin.identity.checkpoint_sha256, _digest("weights:" + pin.plan.case_id),
        )
    assert result.selected_publication_file_bytes_verified is True
    assert all(getattr(result, name) is False for name in (
        "selected_publications_verified", "selected_tensors_verified",
        "full_selector_evidence_verified", "selection_publication_tensor_verified",
        "scientific_result_admitted",
    ))
    assert b.state.events[:4] == ["input", "selection", "selection_stable_1", "ledger_1"]
    assert b.state.selection_checks == 3 and b.state.ledger_checks == 2
    assert set(b.state.manifest_checks.values()) == {2}
    first = b.f.pins[0].plan.case_id
    assert b.state.events.index("manifest:" + first) < b.state.events.index("ledger_2")
    assert b.state.events.index("manifest_stable_1:" + first) < b.state.events.index("ledger_2")
    assert b.state.events.index("manifest_stable_2:" + first) > b.state.events.index("ledger_2")
    with pytest.raises(FrozenInstanceError):
        result.owner_decision_sha256 = "0" * 64
    with pytest.raises(FrozenInstanceError):
        result.publications[0].weights_sha256 = "0" * 64


def test_mutable_external_containers_are_snapshotted_before_first_stage(boundary):
    b = boundary
    pins, publications, methods = list(b.f.pins), list(b.f.publications), dict(b.f.methods)
    b.state.mutation = lambda: (pins.clear(), publications.clear(), methods.clear())
    result = b.invoke(pins=pins, selected_source_pins=publications, method_config_sha256=methods)
    assert len(result.publications) == 1020
    with pytest.raises(TypeError):
        b.state.methods["eegnet"] = "0" * 64


def test_publication_sequence_can_be_reordered_without_rebinding_cases(boundary):
    result = boundary.invoke(selected_source_pins=tuple(reversed(boundary.f.publications)))
    assert tuple(row.case_id for row in result.publications) == tuple(
        pin.plan.case_id for pin in boundary.f.pins
    )


@pytest.mark.parametrize("change", ["missing", "duplicate", "untyped", "string"])
def test_bad_case_pin_roster_refused_before_any_io(boundary, change):
    pins = boundary.f.pins
    pins = {
        "missing": pins[:-1], "duplicate": pins[:-1] + (pins[0],),
        "untyped": (object(),) + pins[1:], "string": "fabricated",
    }[change]
    with pytest.raises(ValueError):
        boundary.invoke(pins=pins)
    assert boundary.state.events == []


@pytest.mark.parametrize("change", ["missing", "duplicate", "untyped", "outside", "empty_id", "string"])
def test_bad_publication_coverage_refused_before_any_io(boundary, change):
    pubs = boundary.f.publications
    pubs = {
        "missing": pubs[:-1], "duplicate": pubs[:-1] + (pubs[0],),
        "untyped": (object(),) + pubs[1:],
        "outside": (replace(pubs[0], case_id="outside"),) + pubs[1:],
        "empty_id": (replace(pubs[0], case_id=""),) + pubs[1:],
        "string": "fabricated",
    }[change]
    with pytest.raises(ValueError, match="selected-source|sequences"):
        boundary.invoke(selected_source_pins=pubs)
    assert boundary.state.events == []


@pytest.mark.parametrize("field", ["manifest_sha256", "model_recipe_sha256", "environment_sha256"])
def test_invalid_publication_digest_anywhere_refused_before_input_reads(boundary, field):
    pubs = boundary.f.publications
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        boundary.invoke(selected_source_pins=pubs[:-1] + (replace(pubs[-1], **{field: "bad"}),))
    assert boundary.state.events == []


@pytest.mark.parametrize("change", ["missing", "outside", "bad_digest", "route_digest"])
def test_method_map_refused_before_any_io(boundary, change):
    methods = dict(boundary.f.methods)
    if change == "missing":
        del methods["eegnet"]
    elif change == "outside":
        methods["outside"] = _digest("outside")
    elif change == "bad_digest":
        methods["eegnet"] = "bad"
        boundary.route.contract.method_config_sha256["eegnet"] = "bad"
    else:
        methods["eegnet"] = "0" * 64
    with pytest.raises(ValueError):
        boundary.invoke(method_config_sha256=methods)
    assert boundary.state.events == []


@pytest.mark.parametrize("change", ["route_scope", "pin_scope", "environment", "method", "source"])
def test_metadata_mismatches_refused_before_any_io(boundary, change):
    b = boundary
    kwargs = {}
    if change == "route_scope":
        b.route.contract.plans = b.f.plans[:-1] + (b.f.plans[0],)
    elif change == "pin_scope":
        # Same identities on each typed pin, but the roster contains subject01.
        first = b.f.pins[0]
        plan = replace(first.plan, target_subject="subject_01")
        identity = replace(first.identity, target_subject="subject_01")
        pin = replace(first, plan=plan, key=ExpectedCell(*plan.identity_key), identity=identity)
        kwargs["pins"] = (pin,) + b.f.pins[1:]
        kwargs["selected_source_pins"] = (
            replace(b.f.publications[0], case_id=plan.case_id),
        ) + b.f.publications[1:]
    elif change == "environment":
        kwargs["selected_source_pins"] = (
            replace(b.f.publications[0], environment_sha256="0" * 64),
        ) + b.f.publications[1:]
    else:
        identity = replace(b.f.pins[0].identity, **{
            "method_config_sha256" if change == "method" else "source_sha256": "0" * 64,
        })
        kwargs["pins"] = (replace(b.f.pins[0], identity=identity),) + b.f.pins[1:]
    with pytest.raises(ValueError):
        b.invoke(**kwargs)
    assert b.state.events == []


@pytest.mark.parametrize("change", ["owner", "ceiling", "rows", "claims", "untyped"])
def test_input_result_must_bind_same_pins_before_selection(boundary, change):
    b = boundary
    if change == "owner":
        b.state.input = replace(b.state.input, owner_decision_sha256="0" * 64)
    elif change == "ceiling":
        b.state.input = replace(b.state.input, selection_ceiling_config_sha256="0" * 64)
    elif change == "rows":
        b.state.input = replace(b.state.input, rows=b.f.rows[:-1])
    elif change == "claims":
        b.state.input = replace(b.state.input, selection_claims=b.f.claims[:-1])
    else:
        b.state.input = object()
    with pytest.raises(ValueError):
        b.invoke()
    assert b.state.events == ["input"]


@pytest.mark.parametrize("change", ["owner", "ceiling", "candidate", "manifest", "untyped"])
def test_fresh_selection_claims_must_equal_input_claims(boundary, change):
    b = boundary
    if change == "owner":
        b.state.selection = replace(b.state.selection, owner_decision_sha256="0" * 64)
    elif change == "ceiling":
        b.state.selection = replace(b.state.selection, ceiling=replace(
            b.state.selection.ceiling, expected_sha256="0" * 64,
        ))
    elif change == "untyped":
        b.state.selection = object()
    else:
        field = "selected_candidate" if change == "candidate" else "manifest_sha256"
        claims = (replace(b.f.claims[0], **{field: "changed"}),) + b.f.claims[1:]
        b.state.selection = replace(
            b.state.selection, selection_files=ChoSelectionFileWitness((), claims),
        )
    with pytest.raises(ValueError, match="fresh selection witness"):
        b.invoke()
    assert b.state.events == ["input", "selection"]


@pytest.mark.parametrize("change", ["manifest", "path", "contract", "candidate"])
def test_all_claim_associations_checked_before_any_manifest_read(boundary, change):
    b = boundary
    field, value = {
        "manifest": ("manifest_sha256", "0" * 64), "path": ("manifest_path", None),
        "contract": ("contract_sha256", "bad"), "candidate": ("selected_candidate", ""),
    }[change]
    claims = b.f.claims[:-1] + (replace(b.f.claims[-1], **{field: value}),)
    b.state.input = replace(b.state.input, selection_claims=claims)
    b.state.selection = replace(
        b.state.selection, selection_files=ChoSelectionFileWitness((), claims),
    )
    with pytest.raises(ValueError):
        b.invoke()
    assert b.state.events == ["input", "selection"]


@pytest.mark.parametrize("when", ["before", "after"])
@pytest.mark.parametrize("change", ["score", "digest", "missing"])
def test_ledger_drift_before_or_after_publications_is_refused(boundary, when, change):
    b = boundary
    rows = b.f.rows
    if change == "score":
        rows = (replace(rows[0], numerator=0),) + rows[1:]
    elif change == "digest":
        rows = (replace(rows[0], cell_sha256="0" * 64),) + rows[1:]
    else:
        rows = rows[:-1]
    setattr(b.state, "rows_" + when, rows)
    with pytest.raises(ValueError):
        b.invoke()
    if when == "before":
        assert b.state.events == ["input", "selection", "selection_stable_1", "ledger_1"]
    else:
        assert b.state.ledger_checks == 2 and b.state.selection_checks == 2


@pytest.mark.parametrize("change", ["untyped", "root", "path", "manifest", "weights"])
def test_manifest_verifier_result_must_bind_requested_publication(boundary, change):
    b = boundary
    def changed(witness):
        if change == "untyped":
            return object()
        field, value = {
            "root": ("project_root", b.args["project_root"] / "outside"),
            "path": ("manifest_path", b.args["project_root"] / "outside.json"),
            "manifest": ("manifest_sha256", "0" * 64),
            "weights": ("weights_sha256", "bad"),
        }[change]
        return replace(witness, **{field: value})
    b.state.manifest_override = changed
    with pytest.raises(ValueError):
        b.invoke()
    assert b.state.ledger_checks == 1 and b.state.selection_checks == 1
    assert b.state.manifest_checks == {}


@pytest.mark.parametrize("stage", [
    "input", "selection", "selection_stable_1", "ledger_1", "path", "manifest",
    "selection_stable_2", "manifest_stable_1", "ledger_2", "selection_stable_3",
    "manifest_stable_2",
])
def test_each_dependency_failure_stops_later_work(boundary, stage):
    b = boundary
    name = stage + (":" + b.f.pins[0].plan.case_id if stage in {
        "path", "manifest", "manifest_stable_1", "manifest_stable_2",
    } else "")
    b.state.fail = name
    with pytest.raises(ValueError, match="fabricated failure"):
        b.invoke()
    assert b.state.events[-1] == name


@pytest.mark.parametrize("field", ["base_config_sha256", "selection_ceiling_config_sha256"])
def test_invalid_independent_config_digest_refused_before_input_reads(boundary, field):
    with pytest.raises(ValueError):
        boundary.invoke(**{field: "bad"})
    assert boundary.state.events == []


@pytest.mark.parametrize("tamper", [False, True])
def test_one_real_byte_verifier_composes_with_mocked_input_and_selection(
    boundary, monkeypatch, tamper,
):
    """Actual byte I/O for one fabricated case; remaining 1,019 are mocked."""
    b = boundary
    first_pin, first_pub = b.f.pins[0], b.f.publications[0]
    store = b.args["project_root"] / "runs" / "phase2" / "selected_sources"
    for name in ("manifests", "evidence", "weights"):
        (store / name).mkdir(parents=True)
    blob = b"fabricated byte binding only; this is not a safetensors state"
    weights_sha = hashlib.sha256(blob).hexdigest()
    weights_path = store / "weights" / (weights_sha + ".safetensors")
    weights_path.write_bytes(blob)
    candidate = {"name": "fabricated-candidate"}
    contract = {
        "protocol_sha256": first_pin.identity.protocol_sha256,
        "source": asdict(b.f.source), "candidates": [candidate],
    }
    contract_sha = config_digest(contract)
    evidence = envelope("engineering_smoke", {
        "purpose": (
            "bounded_eegnet_source_selection" if first_pin.plan.method == "eegnet"
            else "bounded_labram_source_selection"
        ), "complete": True,
        "outer_target_predictions_performed": False,
        "contract": contract, "contract_sha256": contract_sha,
        "selected_candidate": candidate["name"],
        "final_source_fit": {
            "candidate": candidate["name"], "candidate_sha256": config_digest(candidate),
            "fitted_state_sha256": first_pin.identity.checkpoint_sha256,
        },
    })
    evidence_sha = evidence["sha256"]
    recipe = {"architecture": "fabricated-byte-only"}
    recipe_sha = config_digest(recipe)
    manifest = envelope("engineering_smoke", {
        "purpose": "selected_source_snapshot", "scope": "engineering_only",
        "scientific_evaluation": False, "evidence_sha256": evidence_sha,
        "selected_candidate": candidate["name"], "selection_contract_sha256": contract_sha,
        "protocol_config_sha256": first_pin.identity.protocol_sha256,
        "source": asdict(b.f.source), "model_class": "fabricated.ByteOnly",
        "model_recipe": recipe, "model_recipe_sha256": recipe_sha,
        "model_state_sha256": first_pin.identity.checkpoint_sha256,
        "tensor_schema": {"weight": {"shape": [1], "dtype": "torch.float32"}},
        "weights_sha256": weights_sha, "weights_file": "weights/" + weights_sha + ".safetensors",
        "evidence_file": "evidence/" + evidence_sha + ".json",
    })
    manifest_sha = manifest["sha256"]
    for path, record in (
        (store / "evidence" / (evidence_sha + ".json"), evidence),
        (store / "manifests" / (manifest_sha + ".json"), manifest),
    ):
        path.write_bytes((canonical_config_json(record) + "\n").encode())
    pins = (replace(first_pin, selection_evidence_sha256=evidence_sha),) + b.f.pins[1:]
    publications = (replace(
        first_pub, manifest_sha256=manifest_sha, model_recipe_sha256=recipe_sha,
    ),) + b.f.publications[1:]
    claims = (replace(
        b.f.claims[0], evidence_sha256=evidence_sha, contract_sha256=contract_sha,
        manifest_sha256=manifest_sha,
        manifest_path="runs/phase2/selected_sources/manifests/" + manifest_sha + ".json",
    ),) + b.f.claims[1:]
    b.state.fixture_pins = pins
    b.state.input = replace(b.state.input, selection_claims=claims)
    b.state.selection = replace(
        b.state.selection, selection_files=ChoSelectionFileWitness((), claims),
    )
    mocked_manifest, mocked_stable = C.verify_cho_selected_manifest_files, C.ChoSelectedManifestWitness.verify_stable
    actual_calls = []

    def dispatch_manifest(*args, **kwargs):
        if kwargs["manifest_sha256"] != manifest_sha:
            return mocked_manifest(*args, **kwargs)
        witness = _real_manifest_verifier(*args, **kwargs)
        actual_calls.append("verify")
        if tamper:
            weights_path.write_bytes(blob + b" changed")
        return witness

    def dispatch_stable(witness):
        if witness.manifest_sha256 == manifest_sha:
            actual_calls.append("stable")
            return _REAL_MANIFEST_STABLE(witness)
        return mocked_stable(witness)

    monkeypatch.setattr(C, "_evidence_path", _real_evidence_path)
    monkeypatch.setattr(C, "verify_cho_selected_manifest_files", dispatch_manifest)
    monkeypatch.setattr(C.ChoSelectedManifestWitness, "verify_stable", dispatch_stable)
    if tamper:
        with pytest.raises(ValueError, match="selected weights changed"):
            b.invoke(pins=pins, selected_source_pins=publications)
        assert b.state.ledger_checks == 1
    else:
        result = b.invoke(pins=pins, selected_source_pins=publications)
        assert result.publications[0].weights_sha256 == weights_sha
        assert result.selected_publication_file_bytes_verified is True
        assert result.selected_tensors_verified is False
    assert actual_calls.count("verify") == 1
    assert actual_calls.count("stable") == (2 if tamper else 3)
