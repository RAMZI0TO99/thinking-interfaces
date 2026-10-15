"""Prepared synthetic checks; this file is not a runtime passing receipt.

All catalogs, input assets, selection claims and cell records are fabricated.
No arrays, weights, predictors, selected-state restore or scientific fits are
read or created. Public acceptance retains the actual adopted scope checks.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, replace
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from uuid import uuid4

import pytest

from core.config import canonical_config_json, config_digest, config_snapshot, load_toml
from core.provenance import SourceProvenance
from docs.phase2.cho51_route_candidate_v1.route_contract import PINS
from docs.phase2.cho51_selection_files_v1 import selection_files as S
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import PLANNER, from_verified_full_route
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell
from evaluation.phase2_cho_case_inputs import (
    CHO_SUBJECTS,
    SELECTED_METHODS,
    SELECTED_SEEDS,
    ChoFirstTrancheRoute,
)
from evaluation.phase2_factored_evidence import pack_factored_selection
from evaluation.phase2_profile_binding import CHO_CLASSES, ChoProfileAssets60Hz
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import CellIdentity, envelope
from evaluation.phase2_runner import CasePlan, CaseRecorder
from evaluation.phase2_subject_aggregation import ExpectedCell


PROJECT = Path(__file__).resolve().parents[3]
CANDIDATES = (
    "runs/phase2/freeze_readiness/20260923_cho60hz_scope/"
    "proposed_four_method_candidates.json"
)
CANDIDATES_SHA256 = "f3dba0643cba2807fbc6e0421c271f260c8cf357a8bc67a19f7456931ca892ef"


def _digest(label):
    return hashlib.sha256(label.encode()).hexdigest()


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((canonical_config_json(value) + "\n").encode())


def _policy(root, raw=b"maximum_gradient_steps = 5253\n"):
    root = root.resolve()
    path = root / S.SELECTION_CEILING_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


def test_policy_accepts_exact_committed_file_with_independent_pin(tmp_path):
    path, digest = _policy(tmp_path, (PROJECT / S.SELECTION_CEILING_RELATIVE).read_bytes())
    witness = S.load_selection_ceiling(tmp_path.resolve(), expected_sha256=digest)
    assert witness.path == path
    assert witness.maximum_gradient_steps == 5253
    witness.verify_stable()
    with pytest.raises(ValueError):
        S.load_selection_ceiling(tmp_path.resolve(), expected_sha256="0" * 64)


@pytest.mark.parametrize("raw", [
    b"maximum_gradient_steps = true\n", b"maximum_gradient_steps = 0\n",
    b"maximum_gradient_steps = -1\n", b"maximum_gradient_steps = 5254\n",
    b"maximum_gradient_steps = 5253.0\n", b"maximum_gradient_steps = 256\n",
    b"maximum_gradient_steps = 5253\nextra = 1\n", b"other = 5253\n",
    b"maximum_gradient_steps = 5253\nmaximum_gradient_steps = 5253\n", b"",
])
def test_policy_refuses_bad_value_shape_and_duplicate_key_even_when_repinned(tmp_path, raw):
    _, digest = _policy(tmp_path, raw)
    with pytest.raises(ValueError):
        S.load_selection_ceiling(tmp_path.resolve(), expected_sha256=digest)


@pytest.mark.parametrize("change", ["missing", "bytes", "replacement"])
def test_policy_witness_refuses_missing_changed_or_replaced_file(tmp_path, change):
    path, digest = _policy(tmp_path)
    witness = S.load_selection_ceiling(tmp_path.resolve(), expected_sha256=digest)
    if change == "missing":
        path.unlink()
    elif change == "bytes":
        path.write_bytes(b"maximum_gradient_steps = 5254\n")
    else:
        replacement = path.with_suffix(".replacement")
        replacement.write_bytes(path.read_bytes())
        os.replace(replacement, path)
    with pytest.raises(ValueError):
        witness.verify_stable()


def test_policy_refuses_hardlink_alias_and_oversize(tmp_path):
    path, digest = _policy(tmp_path)
    alias = path.with_suffix(".alias")
    os.link(path, alias)
    with pytest.raises(ValueError, match="link count"):
        S.load_selection_ceiling(tmp_path.resolve(), expected_sha256=digest)
    alias.unlink()
    oversized = b"#" * (S.MAXIMUM_CEILING_BYTES + 1)
    path.write_bytes(oversized)
    with pytest.raises(ValueError, match="size or link count"):
        S.load_selection_ceiling(
            tmp_path.resolve(), expected_sha256=hashlib.sha256(oversized).hexdigest(),
        )


@pytest.fixture(scope="module")
def context(tmp_path_factory):
    """Construct only metadata and small records; keep the pinned owner evidence."""
    root = tmp_path_factory.mktemp("fabricated_cho51_selection").resolve()
    for relative in (*PINS, PLANNER):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((PROJECT / relative).read_bytes())
    _, ceiling_sha = _policy(root, (PROJECT / S.SELECTION_CEILING_RELATIVE).read_bytes())
    config = load_toml(PROJECT / "configs/phase2/protocol.toml")
    protocol_sha = config_digest(config)
    catalogs = tuple(TrialCatalog(
        "cho2017", subject,
        tuple(f"fabricated-{subject}-{i}" for i in range(72)),
        ("left_hand",) * 36 + ("right_hand",) * 36, CHO_CLASSES,
        _digest("fabricated-catalog-" + subject), _digest("fabricated-preprocessing"),
    ) for subject in CHO_SUBJECTS)
    variant_sha = hashlib.sha256(
        (PROJECT / "configs/phase2/cho_profile_b_60hz.toml").read_bytes(),
    ).hexdigest()
    assets = MappingProxyType({subject: ChoProfileAssets60Hz(
        _digest("fabricated-b-" + subject), _digest("fabricated-sidecar-" + subject),
        variant_sha,
    ) for subject in CHO_SUBJECTS})
    selections = {subject: source_selection(catalogs, target=subject) for subject in CHO_SUBJECTS}
    selection_records = {subject: envelope("source_selection", asdict(selection))
                         for subject, selection in selections.items()}
    episode_records = {catalog.subject: envelope("episode_manifest", nested_episode(
        catalog, shots=tuple(config["protocol"]["shots_per_class"]),
        protocol_sha256=protocol_sha,
    ).payload()) for catalog in catalogs}
    full = ChoFirstTrancheRoute(
        tuple(CasePlan("cho2017", subject, method, 5, seed, 1)
              for subject in CHO_SUBJECTS for method in SELECTED_METHODS for seed in SELECTED_SEEDS),
        catalogs, assets, canonical_config_json(config),
        MappingProxyType({subject: canonical_config_json(value)
                          for subject, value in selection_records.items()}),
        MappingProxyType({subject: canonical_config_json(value)
                          for subject, value in episode_records.items()}),
    )
    route = from_verified_full_route(root, full)
    candidate_raw = (PROJECT / CANDIDATES).read_bytes()
    assert hashlib.sha256(candidate_raw).hexdigest() == CANDIDATES_SHA256
    templates = {row["method"]: row for row in json.loads(candidate_raw)["methods"]}
    methods = dict(route.contract.method_config_sha256)
    assert {method: config_digest(value) for method, value in templates.items()} == methods
    source = SourceProvenance("a" * 40, _digest("fabricated-independent-source"), False)
    pins = tuple(PinnedCaseCell(
        plan, ExpectedCell(*plan.identity_key), CellIdentity(
            *plan.identity_key, None, None, protocol_sha,
            episode_records[plan.target_subject]["sha256"],
            selection_records[plan.target_subject]["sha256"],
            methods[plan.method], catalogs[0].preprocessing_sha256,
            _digest("fabricated-checkpoint-" + plan.case_id), source.source_sha256,
            _digest("fabricated-environment"), source.git_commit, False,
        ), 1, _digest("unpublished-cell"), _digest("unpublished-success"),
        _digest("unpublished-selection"),
    ) for plan in route.plans)
    return SimpleNamespace(
        root=root, route=route, full=full, templates=templates, methods=methods,
        selections=selections, source=source, pins=pins, ceiling_sha=ceiling_sha,
        protocol_sha=protocol_sha,
    )


def _publish(context, pins, *, factored=False):
    recorder = CaseRecorder(
        context.root, output_root=context.root / "runs/phase2" / ("fabricated-" + uuid4().hex),
    )
    published, entries = [], []
    for pin in pins:
        plan = pin.plan
        candidates = config_snapshot(context.templates[plan.method])["candidates"]
        if plan.method == "labram_lora":
            for candidate in candidates:
                candidate["source"]["seed"] = plan.model_seed
        contract = dict(
            method=plan.method, dataset=plan.dataset,
            selection=config_snapshot(asdict(context.selections[plan.target_subject])),
            protocol_sha256=context.protocol_sha, shots_per_class=plan.shots_per_class,
            source=asdict(context.source), candidates=candidates,
            outer_target=plan.target_subject, source_policy=S.SOURCE_POLICY,
            score=S.SCORE, tie_break=S.TIE_BREAK, early_stopping=False,
            engineering_only=True, scientific_evaluation=False, maximum_gradient_steps=5253,
            runtime=dict(device="cpu", dtype="float32", torch_threads=1,
                         deterministic_algorithms=True, python="fabricated", torch="fabricated",
                         numpy="fabricated", braindecode="fabricated"),
        )
        contract["model_and_sampling_seed" if plan.method == "eegnet" else "head_and_sampling_seed"] = plan.model_seed
        if plan.method == "eegnet":
            contract["profile_a_manifests"] = {}
        else:
            contract.update(
                template_state_sha256=_digest("fabricated-template"),
                initial_state_sha256=_digest("fabricated-initial"),
                prior_template_training_verified=False,
                source_trial_pool="all_profile_a_retained_trials_joined_to_profile_b",
                sampling_rate_hz=200, samples_per_trial=800,
                stored_unit_volts=0.0001, extra_input_scale=1.0,
                profile_assets={subject: asdict(asset)
                                for subject, asset in context.route.labram_assets.items()},
            )
        selected = candidates[0]["name"]
        payload = dict(
            purpose="bounded_eegnet_source_selection" if plan.method == "eegnet" else "bounded_labram_source_selection",
            complete=True, outer_target_predictions_performed=False,
            contract=contract, contract_sha256=config_digest(contract),
            selected_candidate=selected, folds=[], scores=[],
            final_source_fit=dict(candidate=selected,
                                  candidate_sha256=config_digest(candidates[0]),
                                  fitted_state_sha256=pin.identity.checkpoint_sha256),
        )
        if factored:
            sources = contract["selection"]["source_subjects"]
            identities = {subject: {"catalog_sha256": _digest(subject),
                                    "trial_ids": ["fabricated-trial"]} for subject in sources}
            payload["final_source_fit"].update(
                validation_subject=None, training_subjects=sources, input_identities=identities,
            )
            payload["folds"] = [dict(
                candidate=candidate["name"], validation_subject=validation,
                source_fit=dict(candidate=candidate["name"], validation_subject=validation,
                                training_subjects=[s for s in sources if s != validation],
                                input_identities={s: identities[s] for s in sources if s != validation}),
            ) for candidate in candidates for validation in sources]
        evidence = envelope("engineering_smoke", payload)
        if factored:
            raw = pack_factored_selection(evidence)
            directory = context.root / "runs/phase2" / ("fabricated-store-" + uuid4().hex)
            for name in ("weights", "manifests", "evidence"):
                (directory / name).mkdir(parents=True, exist_ok=True)
            evidence_path = directory / "evidence" / (hashlib.sha256(raw).hexdigest() + ".factored.json")
            evidence_path.write_bytes(raw)
        else:
            evidence_path = recorder.output_root / "selection" / (evidence["sha256"] + ".json")
            _write(evidence_path, evidence)
        cell = envelope("evaluation_cell", dict(identity=asdict(pin.identity), metrics=dict(
            selection_evidence_sha256=evidence["sha256"],
            selection_evidence_path=evidence_path.relative_to(context.root).as_posix(),
        )))
        cell_path = recorder.output_root / "cells" / (pin.identity.sha256 + ".json")
        _write(cell_path, cell)
        published.append(replace(pin, cell_sha256=cell["sha256"], selection_evidence_sha256=evidence["sha256"]))
        entries.append(SimpleNamespace(payload=payload, evidence_path=evidence_path, cell_path=cell_path))
    return SimpleNamespace(recorder=recorder, pins=tuple(published), entries=tuple(entries))


def _verify_subset(context, case):
    return S._verify_selection_files(
        context.full, case.recorder, case.pins, project_root=context.root,
        expected_source=context.source, method_config_sha256=context.methods, ceiling=5253,
    )


def _republish(context, case, payload):
    """Repin malformed claims so a passing hash cannot hide a policy mutation."""
    entry = case.entries[0]
    evidence = envelope("engineering_smoke", payload)
    _write(entry.evidence_path, evidence)
    cell = json.loads(entry.cell_path.read_bytes())
    cell["payload"]["metrics"]["selection_evidence_sha256"] = evidence["sha256"]
    cell = envelope("evaluation_cell", cell["payload"])
    _write(entry.cell_path, cell)
    case.pins = (replace(case.pins[0], cell_sha256=cell["sha256"],
                         selection_evidence_sha256=evidence["sha256"]),)


@pytest.mark.parametrize("method", SELECTED_METHODS)
def test_each_method_binds_5253_without_mutating_contract(context, method):
    pin = next(pin for pin in context.pins if pin.plan.method == method)
    case = _publish(context, (pin,))
    before = case.entries[0].evidence_path.read_bytes()
    witness = _verify_subset(context, case)
    assert witness.claims[0].case_id == pin.plan.case_id
    assert case.entries[0].evidence_path.read_bytes() == before
    assert case.entries[0].payload["contract"]["maximum_gradient_steps"] == 5253
    witness.verify_stable()


def test_factored_file_preserves_physical_and_logical_binding(context):
    pin = next(pin for pin in context.pins if pin.plan.method == "eegnet")
    case = _publish(context, (pin,), factored=True)
    witness = _verify_subset(context, case)
    assert witness.claims[0].evidence_sha256 == case.pins[0].selection_evidence_sha256
    assert case.entries[0].evidence_path in {row[0] for row in witness.physical}
    witness.verify_stable()


@pytest.mark.parametrize("maximum", [1, 256, 257, 5252])
def test_static_contract_uses_pinned_ceiling_across_the_old256_boundary(context, maximum):
    pin = next(pin for pin in context.pins if pin.plan.method == "eegnet")
    case = _publish(context, (pin,))
    contract = case.entries[0].payload["contract"]
    contract["maximum_gradient_steps"] = maximum
    before = canonical_config_json(contract)
    S._static_contract(contract, pin, context.full, ceiling=5253)
    assert canonical_config_json(contract) == before


@pytest.mark.parametrize("maximum", [True, False, 0, -1, 5254, 5253.0])
def test_repinned_contract_step_policy_refused(context, maximum):
    case = _publish(context, (next(pin for pin in context.pins if pin.plan.method == "eegnet"),))
    payload = case.entries[0].payload
    payload["contract"]["maximum_gradient_steps"] = maximum
    payload["contract_sha256"] = config_digest(payload["contract"])
    _republish(context, case, payload)
    with pytest.raises(ValueError, match="static policy"):
        _verify_subset(context, case)


def test_repinned_candidate_mutation_refused_by_independent_method_digest(context):
    case = _publish(context, (context.pins[0],))
    payload = case.entries[0].payload
    payload["contract"]["candidates"][0]["source"]["learning_rate"] = 0.003
    payload["contract_sha256"] = config_digest(payload["contract"])
    _republish(context, case, payload)
    with pytest.raises(ValueError, match="reviewed method digest"):
        _verify_subset(context, case)


@pytest.mark.parametrize("bad_path", ["runs/phase2/../outside.json", "C:/outside.json", "runs\\phase2\\outside.json"])
def test_repinned_path_escape_refused(context, bad_path):
    case = _publish(context, (context.pins[0],))
    entry = case.entries[0]
    cell = json.loads(entry.cell_path.read_bytes())
    cell["payload"]["metrics"]["selection_evidence_path"] = bad_path
    cell = envelope("evaluation_cell", cell["payload"])
    _write(entry.cell_path, cell)
    case.pins = (replace(case.pins[0], cell_sha256=cell["sha256"]),)
    with pytest.raises(ValueError, match="path"):
        _verify_subset(context, case)


def test_selection_witness_refuses_evidence_change(context):
    case = _publish(context, (context.pins[0],))
    witness = _verify_subset(context, case)
    case.entries[0].payload["complete"] = False
    _write(case.entries[0].evidence_path, envelope("engineering_smoke", case.entries[0].payload))
    with pytest.raises(ValueError, match="physical file changed"):
        witness.verify_stable()


def _public(context, case, **changes):
    options = dict(
        route=context.route, recorder=case.recorder, pins=case.pins,
        project_root=context.root, expected_source=context.source,
        method_config_sha256=context.methods,
        selection_ceiling_config_sha256=context.ceiling_sha,
    )
    options.update(changes)
    return S.verify_cho51_recorded_selection_files(**options)


def test_public_complete_fabricated_roster_retains52_sources_and_exact51_targets(context):
    case = _publish(context, context.pins)
    witness = _public(context, case)
    assert len(witness.claims) == 1020
    assert {p.plan.target_subject for p in case.pins} == {f"subject_{i:02d}" for i in range(2, 53)}
    assert len(context.route.catalogs) == len(context.route.labram_assets) == 52
    assert all("subject_01" in context.selections[pin.plan.target_subject].source_subjects for pin in case.pins)
    assert witness.scientific_result_admitted is False
    assert witness.ceiling.expected_sha256 == context.ceiling_sha
    witness.verify_stable()


@pytest.mark.parametrize("change", ["missing", "duplicate", "source01", "legacy_route", "source", "method", "missing_source_catalog"])
def test_public_bad_scope_or_independent_pins_refused_before_selection_reads(context, monkeypatch, change):
    case = _publish(context, (context.pins[0],))
    case.pins = context.pins
    changes = {}
    if change == "missing":
        case.pins = case.pins[:-1]
    elif change == "duplicate":
        case.pins = case.pins[:-1] + (case.pins[0],)
    elif change == "source01":
        first = case.pins[0]
        plan = replace(first.plan, target_subject="subject_01")
        case.pins = (replace(first, plan=plan, key=ExpectedCell(*plan.identity_key),
                             identity=replace(first.identity, target_subject="subject_01")),) + case.pins[1:]
    elif change == "legacy_route":
        changes["route"] = context.full
    elif change == "source":
        changes["expected_source"] = replace(context.source, source_sha256="d" * 64)
    elif change == "method":
        changes["method_config_sha256"] = dict(context.methods, eegnet="d" * 64)
    else:
        changes["route"] = replace(context.route, _full_route=replace(
            context.full, catalogs=context.full.catalogs[1:],
        ))

    def refuse(*args, **kwargs):
        raise AssertionError("selection bytes must not be read after bad scope/pins")

    monkeypatch.setattr(S, "_verify_selection_files", refuse)
    with pytest.raises(ValueError):
        _public(context, case, **changes)
