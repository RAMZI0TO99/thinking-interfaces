"""Prepared synthetic collector regressions; no passing receipt exists yet.

The historical fixture fabricates catalogs, recorder records and a weight-like
blob. No real assets or tensors are loaded. Only the asset-loader boundary is
replaced; actual adopted identities, target and recorder checks remain active.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.config import config_digest
from docs.phase2.cho51_recorder_collection_v1 import collector as C
from docs.phase2.cho51_route_candidate_v1.route_contract import PINS
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import (
    PLANNER,
    from_verified_full_route,
)
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CaseRecorder
from evaluation.phase2_subject_aggregation import ExpectedCell

PROJECT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "_cho51_existing_synthetic_fixture",
    PROJECT / "tests/test_phase2_cho_analysis_preparation.py",
)
LEGACY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LEGACY
SPEC.loader.exec_module(LEGACY)
synthetic_inputs = LEGACY.synthetic_inputs


@pytest.fixture
def collect(synthetic_inputs, monkeypatch):
    f = synthetic_inputs
    root = f.project_root.resolve()
    for relative in (*PINS, PLANNER):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((PROJECT / relative).read_bytes())
    route = from_verified_full_route(root, f.route)
    methods = dict(route.contract.method_config_sha256)
    # The old fixture has arbitrary method templates. Bind the successor to
    # the unchanged adopted method digests while keeping every other identity.
    pins = tuple(replace(
        pin, identity=replace(pin.identity, method_config_sha256=methods[pin.plan.method]),
    ) for pin in f.pins if pin.plan.target_subject != "subject_01")
    recorder = CaseRecorder(root, output_root=root / "runs/phase2/fabricated_recorder")
    published, _ = LEGACY._publish_synthetic_recorder(
        recorder, f.route, pins, project_root=root,
        base_config_sha256=f.base_config_sha256,
        profile_b_config_sha256=f.profile_b_config_sha256,
    )
    calls = []

    def fabricated_loader(project_root, *, input_pins):
        # Explicit replacement: a passing synthetic test cannot qualify real I/O.
        assert project_root == root and input_pins == f.case_input_pins
        calls.append("fabricated_loader")
        return from_verified_full_route(root, f.route)

    monkeypatch.setattr(C, "prepare_cho51_worker_route", fabricated_loader)

    def invoke(**changes):
        args = dict(
            project_root=root, route=route, recorder=recorder, pins=published,
            case_input_pins=f.case_input_pins, base_config_sha256=f.base_config_sha256,
            method_config_sha256=methods, expected_source=f.source,
        )
        args.update(changes)
        return C.collect_recorder_rows(**args)

    return SimpleNamespace(invoke=invoke, calls=calls, f=f, pins=published,
                           recorder=recorder, root=root, methods=methods)


def test_complete_fabricated_recorder_rows_stay_explicitly_incomplete(collect):
    result = collect.invoke()
    assert len(result.rows) == 1020
    assert {r.key.subject for r in result.rows} == {f"subject_{i:02d}" for i in range(2, 53)}
    assert result.selection_publication_tensor_verified is False
    assert result.scientific_result_admitted is False
    assert collect.calls == ["fabricated_loader"]


@pytest.mark.parametrize("change", ["missing", "duplicate", "subject01", "untyped"])
def test_bad_identity_roster_refused_before_asset_reads(collect, change):
    pins = collect.pins
    if change == "missing":
        pins = pins[:-1]
    elif change == "duplicate":
        pins = pins[:-1] + (pins[0],)
    elif change == "untyped":
        pins = (object(),) + pins[1:]
    else:
        first = pins[0]
        plan = replace(first.plan, target_subject="subject_01")
        pins = (replace(first, plan=plan, key=ExpectedCell(*plan.identity_key),
                        identity=replace(first.identity, target_subject="subject_01")),) + pins[1:]
    with pytest.raises(ValueError):
        collect.invoke(pins=pins)
    assert collect.calls == []


def test_source_and_method_changes_refused_before_asset_reads(collect):
    with pytest.raises(ValueError):
        collect.invoke(expected_source=replace(collect.f.source, source_sha256="d" * 64))
    with pytest.raises(ValueError):
        collect.invoke(method_config_sha256=dict(collect.methods, eegnet="d" * 64))
    assert collect.calls == []


def test_real_input_failure_prevents_target_and_score_reads(collect, monkeypatch):
    def refuse(*args, **kwargs):
        raise ValueError("fabricated input byte mismatch")

    monkeypatch.setattr(C, "prepare_cho51_worker_route", refuse)
    def unexpected(*args, **kwargs):
        raise AssertionError("recorder must not be read after input refusal")

    monkeypatch.setattr(C, "_verify_target_inputs", unexpected)
    monkeypatch.setattr(C, "verified_score_rows", unexpected)
    with pytest.raises(ValueError, match="fabricated input byte mismatch"):
        collect.invoke()


@pytest.mark.parametrize("directory", ["claims", "cells", "successes", "publication_intents"])
def test_unlisted_historical_record_is_refused(collect, directory):
    path = collect.recorder.output_root / directory / "unlisted-subject01.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        collect.invoke()


def test_missing_success_receipt_is_refused(collect):
    pin = collect.pins[0]
    path = collect.recorder.output_root / "successes" / f"{pin.plan.case_id}.success.json"
    path.unlink()
    with pytest.raises(ValueError):
        collect.invoke()


@pytest.mark.parametrize("method,change", [
    ("eegnet", "query_count"), ("eegnet", "confusion_rows"),
    ("eegnet", "source_subjects"), ("labram_linear", "binding"),
    ("labram_lora", "profile"), ("labram_full", "episode"),
])
def test_self_consistent_bad_target_refused_before_scores(collect, monkeypatch, method, change):
    index = next(i for i, p in enumerate(collect.pins) if p.plan.method == method)
    pin = collect.pins[index]
    path = collect.recorder.output_root / "cells" / f"{pin.identity.sha256}.json"
    payload = json.loads(path.read_bytes())["payload"]
    metrics = payload["metrics"]
    attestation = metrics["target_input_attestation"]
    if change == "query_count":
        metrics["query_count"] += 1
    elif change == "confusion_rows":
        metrics["confusion_matrix"][0][0] += 1
    elif change == "source_subjects":
        attestation["anchor"]["source_subjects"].remove("subject_01")
    elif change == "binding":
        attestation["binding"]["source_sha256"] = "d" * 64
        attestation["binding_sha256"] = config_digest(attestation["binding"])
    elif change == "profile":
        attestation["profile"] = "cho_profile_a"
    else:
        attestation["episode_record_sha256"] = "d" * 64
    cell = envelope("evaluation_cell", payload)
    LEGACY._write_record(path, cell)
    pins = list(collect.pins)
    pins[index] = replace(pin, cell_sha256=cell["sha256"])
    def unexpected(*args, **kwargs):
        raise AssertionError("scores must not be read after target refusal")

    monkeypatch.setattr(C, "verified_score_rows", unexpected)
    with pytest.raises(ValueError, match="query|confusion|anchor|raw source|Profile|attestation"):
        collect.invoke(pins=tuple(pins))


def test_changed_source_only_subject_manifest_is_refused(collect):
    path = collect.root / "data/processed/cho2017/profile_b_60hz_v1/subject_01.manifest.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError):
        collect.invoke()


def test_outside_recorder_is_refused(collect, tmp_path):
    other = CaseRecorder((tmp_path / "outside").resolve())
    other.output_root.mkdir(parents=True)
    with pytest.raises(ValueError, match="recorder"):
        collect.invoke(recorder=other)
