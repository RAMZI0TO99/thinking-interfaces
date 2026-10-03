"""Synthetic recorder tests for read-only Cho paired-input preparation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast
from unittest.mock import patch

import pytest

from core.config import canonical_config_json, config_digest, load_toml
from core.provenance import SourceProvenance
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell
from evaluation.phase2_cho_analysis_preparation import (
    ChoSelectedSourcePin,
    prepare_cho_paired_inputs_from_recorder,
)
from evaluation.phase2_cho_case_inputs import (
    CHO_SUBJECTS,
    SELECTED_METHODS,
    SELECTED_SEEDS,
    ChoCaseInputPins,
    ChoFirstTrancheRoute,
)
from evaluation.phase2_cho_method_template import derive_cho_method_template
from evaluation.phase2_cho_paired_inputs import (
    build_cho_paired_inputs as real_build_cho_paired_inputs,
)
from evaluation.phase2_profile_binding import (
    CHO_CHANNELS,
    CHO_CLASSES,
    ChoProfileAssets60Hz,
    ChoProfileBinding60Hz,
)
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import CellIdentity, envelope
from evaluation.phase2_runner import CasePlan, CaseRecorder, method_configuration
from evaluation.phase2_subject_aggregation import ExpectedCell


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _synthetic_candidates(method: str, seed: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = [
        {
            "name": f"synthetic-{index}",
            "source": {
                "steps_per_subject": index,
                "learning_rate": 0.001 * index,
            },
            "support": {"steps": index, "learning_rate": 0.002 * index},
        }
        for index in (1, 2)
    ]
    if method == "labram_lora":
        for candidate in candidates:
            candidate["source"]["seed"] = seed
    return candidates


@dataclass(frozen=True)
class SyntheticInputs:
    project_root: Path
    base_config_sha256: str
    profile_b_config_sha256: str
    case_input_pins: ChoCaseInputPins
    route: ChoFirstTrancheRoute
    pins: tuple[PinnedCaseCell, ...]
    methods: dict[str, str]
    method_configs: dict[str, dict[str, Any]]
    source: SourceProvenance
    state_calls: list[dict[str, Any]]
    case_workspace: Path


@pytest.fixture
def synthetic_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SyntheticInputs:
    (tmp_path / "configs/phase2").mkdir(parents=True)
    base_path = tmp_path / "configs/base.toml"
    base_path.write_bytes((
        Path(__file__).resolve().parents[1] / "configs/base.toml"
    ).read_bytes())
    base_config_sha256 = hashlib.sha256(base_path.read_bytes()).hexdigest()
    variant_path = tmp_path / "configs/phase2/cho_profile_b_60hz.toml"
    variant_path.write_bytes((
        Path(__file__).resolve().parents[1]
        / "configs/phase2/cho_profile_b_60hz.toml"
    ).read_bytes())
    variant_config = cast(dict[str, Any], load_toml(variant_path))
    variant_config_sha256 = hashlib.sha256(variant_path.read_bytes()).hexdigest()
    profile_b_config_sha256 = config_digest(variant_config["preprocessing"])
    config: dict[str, Any] = load_toml(
        Path(__file__).resolve().parents[1] / "configs/phase2/protocol.toml"
    )
    protocol_sha256 = config_digest(config)
    shots = tuple(config["protocol"]["shots_per_class"])
    source = SourceProvenance("b" * 40, "c" * 64, False)
    catalogs = tuple(
        TrialCatalog(
            "cho2017", subject,
            tuple(f"{subject}-{index:02d}" for index in range(72)),
            ("left_hand",) * 36 + ("right_hand",) * 36,
            CHO_CLASSES, _digest(f"artifact-{subject}"), _digest("preprocessing"),
        )
        for subject in CHO_SUBJECTS
    )
    selections = {
        subject: envelope(
            "source_selection", asdict(source_selection(catalogs, target=subject))
        )
        for subject in CHO_SUBJECTS
    }
    episodes = {
        catalog.subject: envelope(
            "episode_manifest",
            nested_episode(catalog, shots=shots, protocol_sha256=protocol_sha256).payload(),
        )
        for catalog in catalogs
    }
    plans = tuple(
        CasePlan("cho2017", subject, method, 5, seed, 1)
        for subject in CHO_SUBJECTS
        for method in SELECTED_METHODS
        for seed in SELECTED_SEEDS
    )
    b_dir = tmp_path / "data/processed/cho2017/profile_b_60hz_v1"
    b_dir.mkdir(parents=True)
    b_assets: dict[str, ChoProfileAssets60Hz] = {}
    for subject in CHO_SUBJECTS:
        manifest_path = b_dir / f"{subject}.manifest.json"
        manifest = {
            "subject": int(subject[-2:]),
            "config_sha256": profile_b_config_sha256,
            "variant": variant_config["variant"],
            "variant_config_sha256": variant_config_sha256,
            "source_file": f"data/raw/moabb/cho2017/{subject}.gdf",
            "source_sha256": _digest(f"raw-{subject}"),
        }
        manifest_path.write_text(canonical_config_json(manifest), "utf-8")
        b_assets[subject] = ChoProfileAssets60Hz(
            _digest(f"profile-b-{subject}"),
            hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            variant_config_sha256,
        )
    route = ChoFirstTrancheRoute(
        plans,
        catalogs,
        MappingProxyType(b_assets),
        canonical_config_json(config),
        MappingProxyType({
            subject: canonical_config_json(record) for subject, record in selections.items()
        }),
        MappingProxyType({
            subject: canonical_config_json(record) for subject, record in episodes.items()
        }),
    )
    method_configs = {
        method: derive_cho_method_template(
            next(plan for plan in plans if plan.method == method),
            {"candidates": _synthetic_candidates(method, SELECTED_SEEDS[0])},
            route.labram_assets,
        )
        for method in SELECTED_METHODS
    }
    methods = {
        method: method_configuration(config)
        for method, config in method_configs.items()
    }
    case_input_pins = ChoCaseInputPins(
        _digest("synthetic-protocol-bytes"),
        _digest("synthetic-threshold-bytes"),
        _digest("synthetic-cohort-audit-bytes"),
        variant_config_sha256,
    )

    def synthetic_rederived_route(
        root: Path, *, pins: ChoCaseInputPins,
    ) -> ChoFirstTrancheRoute:
        assert root == tmp_path
        assert pins is case_input_pins
        return route

    monkeypatch.setattr(
        "evaluation.phase2_cho_analysis_preparation.prepare_cho_first_tranche",
        synthetic_rederived_route,
    )
    state_calls: list[dict[str, Any]] = []

    def synthetic_tensor_case_child(**kwargs: Any) -> dict[str, Any]:
        # The fixture's synthetic weights and runtime cannot restore a real
        # model; only this child-invocation boundary is replaced.
        state_calls.append(kwargs)
        return {
            "schema": "cho_tensor_case_child_witness_v1",
            "case_id": kwargs["case_id"],
            "manifest_sha256": kwargs["manifest_sha256"],
            "evidence_sha256": kwargs["evidence_sha256"],
            "selected_candidate": kwargs["selected_candidate"],
            "model_recipe_sha256": kwargs["expected_model_recipe_sha256"],
            "model_state_sha256": kwargs["expected_model_state_sha256"],
            "weights_sha256": _digest("synthetic-selected-source-weights-v1"),
        }

    monkeypatch.setattr(
        "evaluation.phase2_cho_analysis_preparation.run_cho_tensor_case_child",
        synthetic_tensor_case_child,
    )
    pins = tuple(
        PinnedCaseCell(
            plan,
            ExpectedCell(*plan.identity_key),
            CellIdentity(
                plan.dataset, plan.target_subject, plan.method, plan.shots_per_class,
                plan.model_seed, None, None, protocol_sha256,
                episodes[plan.target_subject]["sha256"],
                selections[plan.target_subject]["sha256"],
                methods[plan.method], catalogs[0].preprocessing_sha256,
                _digest(f"checkpoint-{index}"), source.source_sha256,
                _digest("environment"), source.git_commit, False,
            ),
            1,
            _digest(f"unpublished-cell-{index}"),
            _digest(f"unpublished-success-{index}"),
            _digest(f"selection-evidence-{index}"),
        )
        for index, plan in enumerate(plans)
    )
    case_workspace = tmp_path / "tensor-case-workspace"
    case_workspace.mkdir()
    return SyntheticInputs(
        tmp_path, base_config_sha256, profile_b_config_sha256,
        case_input_pins, route, pins, methods, method_configs,
        source, state_calls, case_workspace,
    )


def _write_record(path: Path, record: dict[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (canonical_config_json(record) + "\n").encode("utf-8")
    path.write_bytes(raw)
    return raw


def _publish_synthetic_recorder(
    recorder: CaseRecorder, route: ChoFirstTrancheRoute,
    pins: tuple[PinnedCaseCell, ...], *,
    project_root: Path,
    base_config_sha256: str, profile_b_config_sha256: str,
) -> tuple[tuple[PinnedCaseCell, ...], tuple[ChoSelectedSourcePin, ...]]:
    output = recorder.output_root
    published: list[PinnedCaseCell] = []
    source_pins: list[ChoSelectedSourcePin] = []
    weights_bytes = b"synthetic-selected-source-weights-v1"
    weights_sha256 = hashlib.sha256(weights_bytes).hexdigest()
    weights_path = (
        project_root / "runs/phase2/selected_sources/weights"
        / f"{weights_sha256}.safetensors"
    )
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    weights_path.write_bytes(weights_bytes)
    catalogs = {catalog.subject: catalog for catalog in route.catalogs}
    config = cast(dict[str, Any], load_toml(
        Path(__file__).resolve().parents[1] / "configs/phase2/protocol.toml"
    ))
    shots = tuple(config["protocol"]["shots_per_class"])
    episodes = {
        subject: nested_episode(catalog, shots=shots,
                                protocol_sha256=pins[0].identity.protocol_sha256)
        for subject, catalog in catalogs.items()
    }
    selections = {
        subject: source_selection(route.catalogs, target=subject)
        for subject in catalogs
    }
    for pin in pins:
        plan, identity = pin.plan, pin.identity
        catalog = catalogs[plan.target_subject]
        episode = episodes[plan.target_subject]
        selection = selections[plan.target_subject]
        partition = episode.partition(plan.shots_per_class)
        support_ids = tuple(catalog.trial_ids[index]
                            for index in partition.support_indices)
        query_ids = tuple(catalog.trial_ids[index]
                          for index in partition.query_indices)
        attestation: dict[str, Any] = {
            "schema": "cho2017-target-input-v1", "method": plan.method,
            "subject": plan.target_subject,
            "episode_record_sha256": identity.episode_sha256,
        }
        if plan.method == "eegnet":
            attestation.update({
                "profile": "cho_profile_a",
                "anchor": {
                    "method": "eegnet", "subject": plan.target_subject,
                    "role": "outer_target", "episode_sha256": episode.sha256,
                    "selection_sha256": selection.sha256,
                    "support_trial_ids": support_ids,
                    "query_trial_ids": query_ids,
                    "source_subjects": selection.source_subjects,
                    "input_identities": {plan.target_subject: {
                        "catalog_sha256": catalog.sha256,
                        "artifact_sha256": catalog.artifact_sha256,
                        "manifest_sha256": catalog.artifact_sha256,
                        "base_config_sha256": base_config_sha256,
                    }},
                },
            })
        else:
            asset = route.labram_assets[plan.target_subject]
            binding = ChoProfileBinding60Hz(
                "cho2017", plan.target_subject, plan.shots_per_class,
                catalog.classes, CHO_CHANNELS, identity.protocol_sha256,
                episode.sha256, catalog.artifact_sha256,
                asset.profile_b_artifact_sha256,
                asset.profile_b_manifest_sha256,
                catalog.preprocessing_sha256, profile_b_config_sha256,
                base_config_sha256, support_ids, query_ids,
                partition.support_indices, partition.query_indices,
                len(catalog.trial_ids), 0,
                variant_config_sha256=asset.variant_config_sha256,
                source_file=f"data/raw/moabb/cho2017/{plan.target_subject}.gdf",
                source_sha256=_digest(f"raw-{plan.target_subject}"),
            )
            attestation.update({
                "profile": "cho_profile_b_60hz_v1",
                "binding_sha256": binding.sha256,
                "binding": asdict(binding),
            })
        case = asdict(plan)
        source = asdict(SourceProvenance(
            identity.git_commit, identity.source_sha256, identity.git_dirty,
        ))
        claim = envelope("engineering_smoke", {
            "purpose": "pilot_case_claim", "case": case, "worker": "synthetic-test",
            "attempt": 1, "environment_sha256": identity.environment_sha256,
            "source": source,
            "engineering_only": True,
        })
        _write_record(
            output / "claims" / f"{plan.case_id}.attempt1.claim.json", claim,
        )
        seed_field = (
            "model_and_sampling_seed" if plan.method == "eegnet"
            else "head_and_sampling_seed"
        )
        contract: dict[str, Any] = {
            "method": plan.method,
            "dataset": plan.dataset,
            "selection": asdict(selection),
            "protocol_sha256": identity.protocol_sha256,
            "shots_per_class": plan.shots_per_class,
            seed_field: plan.model_seed,
            "source": source,
            "candidates": _synthetic_candidates(plan.method, plan.model_seed),
            "outer_target": plan.target_subject,
            "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
            "score": "mean_subject_balanced_accuracy_exact_rational",
            "tie_break": "first_in_declared_candidate_order",
            "early_stopping": False,
            "engineering_only": True,
            "scientific_evaluation": False,
            "maximum_gradient_steps": 256,
            "runtime": {
                "device": "cpu", "dtype": "float32", "torch_threads": 1,
                "deterministic_algorithms": True,
                "python": "synthetic", "torch": "synthetic",
                "numpy": "synthetic", "braindecode": "synthetic",
            },
        }
        if plan.method == "eegnet":
            contract["profile_a_manifests"] = {}
        else:
            contract.update({
                "template_state_sha256": _digest("synthetic-template"),
                "initial_state_sha256": _digest("synthetic-initial"),
                "prior_template_training_verified": False,
                "source_trial_pool": "all_profile_a_retained_trials_joined_to_profile_b",
                "sampling_rate_hz": 200,
                "samples_per_trial": 800,
                "stored_unit_volts": 0.0001,
                "extra_input_scale": 1.0,
                "profile_assets": {
                    subject: asdict(route.labram_assets[subject])
                    for subject in sorted(route.labram_assets)
                },
            })
        evidence = envelope("engineering_smoke", {
            "purpose": (
                "bounded_eegnet_source_selection" if plan.method == "eegnet"
                else "bounded_labram_source_selection"
            ),
            "complete": True,
            "outer_target_predictions_performed": False,
            "contract": contract,
            "contract_sha256": config_digest(contract),
            "selected_candidate": "synthetic-1",
            "folds": [],
            "scores": [],
            "final_source_fit": {
                "candidate": "synthetic-1",
                "candidate_sha256": config_digest(contract["candidates"][0]),
                "fitted_state_sha256": identity.checkpoint_sha256,
            },
        })
        evidence_relative = (
            Path("runs/phase2/selection_evidence")
            / f"{evidence['sha256']}.json"
        )
        _write_record(project_root / evidence_relative, evidence)
        store_evidence = (
            Path("runs/phase2/selected_sources/evidence")
            / f"{evidence['sha256']}.json"
        )
        _write_record(project_root / store_evidence, evidence)
        recipe = {"schema": "synthetic-selected-source-recipe-v1", "method": plan.method}
        recipe_sha256 = config_digest(recipe)
        manifest = envelope("engineering_smoke", {
            "purpose": "selected_source_snapshot",
            "scope": "engineering_only",
            "scientific_evaluation": False,
            "evidence_sha256": evidence["sha256"],
            "selected_candidate": "synthetic-1",
            "selection_contract_sha256": config_digest(contract),
            "protocol_config_sha256": identity.protocol_sha256,
            "source": source,
            "model_class": "synthetic.SelectedSource",
            "model_recipe": recipe,
            "model_recipe_sha256": recipe_sha256,
            "model_state_sha256": identity.checkpoint_sha256,
            "tensor_schema": {"weight": {"shape": [1], "dtype": "torch.float32"}},
            "weights_sha256": weights_sha256,
            "weights_file": f"weights/{weights_sha256}.safetensors",
            "evidence_file": f"evidence/{evidence['sha256']}.json",
        })
        manifest_relative = (
            Path("runs/phase2/selected_sources/manifests")
            / f"{manifest['sha256']}.json"
        )
        _write_record(project_root / manifest_relative, manifest)
        source_pins.append(ChoSelectedSourcePin(
            plan.case_id, manifest["sha256"], recipe_sha256,
            identity.environment_sha256,
        ))
        confusion = (
            [[8, 8], [0, 16]] if plan.method == "labram_linear"
            else [[16, 0], [0, 16]]
        )
        score = [3, 4] if plan.method == "labram_linear" else [1, 1]
        cell = envelope("evaluation_cell", {
            "identity": asdict(identity),
            "metrics": {
                "role": "outer_target",
                "selection_evidence_sha256": evidence["sha256"],
                "selection_evidence_path": evidence_relative.as_posix(),
                "selected_source_manifest_sha256": manifest["sha256"],
                "selected_source_manifest_path": manifest_relative.as_posix(),
                "confusion_matrix": confusion,
                "balanced_accuracy": score,
                "query_count": 32,
                "target_input_attestation": attestation,
            },
        })
        _write_record(output / "cells" / f"{identity.sha256}.json", cell)
        intent = envelope("engineering_smoke", {
            "purpose": "pilot_case_publication_intent", "case": case,
            "attempt": 1, "identity": asdict(identity), "cell": cell,
        })
        _write_record(output / "publication_intents" / f"{plan.case_id}.intent.json", intent)
        success = envelope("engineering_smoke", {
            "purpose": "pilot_case_success", "case": case,
            "attempt": 1, "cell_sha256": cell["sha256"],
        })
        success_raw = _write_record(
            output / "successes" / f"{plan.case_id}.success.json", success,
        )
        published.append(replace(
            pin,
            cell_sha256=cell["sha256"],
            success_file_sha256=hashlib.sha256(success_raw).hexdigest(),
            selection_evidence_sha256=evidence["sha256"],
        ))
    return tuple(published), tuple(source_pins)


def test_bad_identity_or_missing_source_prevents_recorder_read(
    synthetic_inputs: SyntheticInputs, tmp_path: Path,
) -> None:
    data = synthetic_inputs
    recorder = CaseRecorder(tmp_path)
    first, second = CHO_SUBJECTS[:2]
    swapped = dict(data.route.selection_records_json)
    swapped[first] = data.route.selection_records_json[second]
    bad_route = replace(data.route, selection_records_json=swapped)
    bad_pins = (replace(
        data.pins[0],
        identity=replace(
            data.pins[0].identity,
            episode_sha256=data.pins[20].identity.episode_sha256,
        ),
    ), *data.pins[1:])
    cases = (
        (data.route, data.pins, data.methods, cast(SourceProvenance, None)),
        (data.route, data.pins, data.methods, replace(data.source, source_sha256="a" * 64)),
        (bad_route, data.pins, data.methods, data.source),
        (data.route, bad_pins, data.methods, data.source),
        (data.route, data.pins, {"eegnet": data.methods["eegnet"]}, data.source),
    )
    with patch(
        "evaluation.phase2_cho_analysis_preparation.verified_score_rows",
        side_effect=AssertionError("recorder was read before identity verification"),
    ) as reader:
        for route, pins, methods, source in cases:
            with pytest.raises(ValueError):
                prepare_cho_paired_inputs_from_recorder(
                    route, recorder, pins,
                    project_root=data.project_root,
                    case_input_pins=data.case_input_pins,
                    base_config_sha256=data.base_config_sha256,
                    method_config_sha256=methods,
                    method_configs=data.method_configs,
                    selected_source_pins=(),
                    expected_source=source,
                    case_workspace=data.case_workspace,
                    case_memory_limit_bytes=8 * 1024**3,
                )
        reader.assert_not_called()


def test_case_input_pins_and_exact_rederived_route_required_before_cell_read(
    synthetic_inputs: SyntheticInputs, tmp_path: Path,
) -> None:
    data = synthetic_inputs
    recorder = CaseRecorder(tmp_path)
    # Whitespace leaves the parsed protocol unchanged, but supplied route
    # bytes still have to equal the route freshly derived from input pins.
    forged = replace(
        data.route, protocol_config_json=data.route.protocol_config_json + " ",
    )
    cases: tuple[tuple[ChoFirstTrancheRoute, ChoCaseInputPins, str], ...] = (
        (data.route, cast(ChoCaseInputPins, None), "case input pins are required"),
        (forged, data.case_input_pins, "route differs from the pinned rederived route"),
    )
    with (
        patch(
            "evaluation.phase2_cho_analysis_preparation.verify_cho_case_identity_bindings",
            side_effect=AssertionError("route identity was checked before origin"),
        ) as identity_checker,
        patch(
            "evaluation.phase2_cho_analysis_preparation.verify_cho_recorded_target_inputs",
            side_effect=AssertionError("cells were read before route origin"),
        ) as target_reader,
        patch(
            "evaluation.phase2_cho_analysis_preparation.verified_score_rows",
            side_effect=AssertionError("scores were read before route origin"),
        ) as score_reader,
    ):
        for route, case_input_pins, error in cases:
            with pytest.raises(ValueError, match=error):
                prepare_cho_paired_inputs_from_recorder(
                    route, recorder, data.pins,
                    project_root=data.project_root,
                    case_input_pins=case_input_pins,
                    base_config_sha256=data.base_config_sha256,
                    method_config_sha256=data.methods, method_configs=data.method_configs,
                    selected_source_pins=(),
                    expected_source=data.source,
                    case_workspace=data.case_workspace,
                    case_memory_limit_bytes=8 * 1024**3,
                )
        identity_checker.assert_not_called()
        target_reader.assert_not_called()
        score_reader.assert_not_called()


def test_static_method_config_objects_match_independent_digests_before_recorder_read(
    synthetic_inputs: SyntheticInputs, tmp_path: Path,
) -> None:
    data = synthetic_inputs
    recorder = CaseRecorder(tmp_path)
    mismatched = {
        method: json.loads(canonical_config_json(config))
        for method, config in data.method_configs.items()
    }
    mismatched["eegnet"]["candidates"][0]["support"]["steps"] += 1
    with (
        patch(
            "evaluation.phase2_cho_analysis_preparation.verify_cho_recorded_target_inputs",
            side_effect=AssertionError("recorder was read before static method checks"),
        ) as target_reader,
        patch(
            "evaluation.phase2_cho_analysis_preparation.verified_score_rows",
            side_effect=AssertionError("scores were read before static method checks"),
        ) as score_reader,
    ):
        for configs in (mismatched, {"eegnet": data.method_configs["eegnet"]}):
            with pytest.raises(ValueError, match="method config"):
                prepare_cho_paired_inputs_from_recorder(
                    data.route, recorder, data.pins,
                    project_root=data.project_root,
                    case_input_pins=data.case_input_pins,
                    base_config_sha256=data.base_config_sha256,
                    method_config_sha256=data.methods,
                    method_configs=configs,
                    selected_source_pins=(), expected_source=data.source,
 case_workspace=data.case_workspace,
 case_memory_limit_bytes=8 * 1024**3,
                )
        target_reader.assert_not_called()
        score_reader.assert_not_called()


def test_verified_recorder_yields_pairs_and_missing_or_corrupt_records_fail(
    synthetic_inputs: SyntheticInputs, tmp_path: Path,
) -> None:
    data = synthetic_inputs
    recorder = CaseRecorder(tmp_path)
    pins, source_pins = _publish_synthetic_recorder(
        recorder, data.route, data.pins,
        project_root=data.project_root,
        base_config_sha256=data.base_config_sha256,
        profile_b_config_sha256=data.profile_b_config_sha256,
    )
    result = prepare_cho_paired_inputs_from_recorder(
        data.route, recorder, pins,
        project_root=data.project_root,
        case_input_pins=data.case_input_pins,
        base_config_sha256=data.base_config_sha256,
        method_config_sha256=data.methods, method_configs=data.method_configs,
        selected_source_pins=source_pins, expected_source=data.source,
 case_workspace=data.case_workspace,
 case_memory_limit_bytes=8 * 1024**3,
    )
    assert len(result.aggregation.admitted_digests) == 1040
    assert len(result.aggregation.means) == 208
    assert len(data.state_calls) == 1040
    assert {call["plan"].case_id for call in data.state_calls} == {
        plan.case_id for plan in data.route.plans
    }
    assert all(
        call["root"] == data.project_root
        and call["expected_method_config_sha256"] == data.methods[call["plan"].method]
        and call["method_config"] == data.method_configs[call["plan"].method]
        and call["protocol_config"] == json.loads(data.route.protocol_config_json)
        for call in data.state_calls
    )
    assert result.paired_differences == tuple(
        (subject, Fraction(1, 4)) for subject in CHO_SUBJECTS
    )

    with (
        patch(
            "evaluation.phase2_cho_analysis_preparation.run_cho_tensor_case_child",
            side_effect=ValueError("synthetic restored state differs"),
        ) as state_checker,
        patch(
            "evaluation.phase2_cho_analysis_preparation.verified_score_rows",
            side_effect=AssertionError("scores were read before source state verification"),
        ) as score_reader,
        pytest.raises(ValueError, match="synthetic restored state differs"),
    ):
        prepare_cho_paired_inputs_from_recorder(
            data.route, recorder, pins,
            project_root=data.project_root,
            case_input_pins=data.case_input_pins,
            base_config_sha256=data.base_config_sha256,
            method_config_sha256=data.methods,
            method_configs=data.method_configs,
            selected_source_pins=source_pins, expected_source=data.source,
 case_workspace=data.case_workspace,
 case_memory_limit_bytes=8 * 1024**3,
        )
    state_checker.assert_called_once()
    score_reader.assert_not_called()

    output = recorder.output_root
    success_path = output / "successes" / f"{pins[0].plan.case_id}.success.json"
    success_raw = success_path.read_bytes()
    success_path.unlink()
    with pytest.raises(ValueError, match="missing or extra records"):
        prepare_cho_paired_inputs_from_recorder(
            data.route, recorder, pins,
            project_root=data.project_root,
            case_input_pins=data.case_input_pins,
            base_config_sha256=data.base_config_sha256,
            method_config_sha256=data.methods, method_configs=data.method_configs,
            selected_source_pins=source_pins, expected_source=data.source,
 case_workspace=data.case_workspace,
 case_memory_limit_bytes=8 * 1024**3,
        )
    success_path.write_bytes(success_raw)

    evidence_path = (
        data.project_root / "runs/phase2/selection_evidence"
        / f"{pins[0].selection_evidence_sha256}.json"
    )
    evidence_raw = evidence_path.read_bytes()
    evidence_path.unlink()
    with patch(
        "evaluation.phase2_cho_analysis_preparation.verified_score_rows",
        side_effect=AssertionError("scores were read before selection file verification"),
    ) as reader:
        with pytest.raises(ValueError):
            prepare_cho_paired_inputs_from_recorder(
                data.route, recorder, pins,
                project_root=data.project_root,
                case_input_pins=data.case_input_pins,
                base_config_sha256=data.base_config_sha256,
                method_config_sha256=data.methods, method_configs=data.method_configs,
                selected_source_pins=source_pins, expected_source=data.source,
 case_workspace=data.case_workspace,
 case_memory_limit_bytes=8 * 1024**3,
            )
        reader.assert_not_called()
    evidence_path.write_bytes(evidence_raw)

    def remove_evidence_after_rows(rows: Any) -> Any:
        paired = real_build_cho_paired_inputs(rows)
        evidence_path.unlink()
        return paired

    with patch(
        "evaluation.phase2_cho_analysis_preparation.build_cho_paired_inputs",
        side_effect=remove_evidence_after_rows,
    ), pytest.raises(ValueError):
        prepare_cho_paired_inputs_from_recorder(
            data.route, recorder, pins,
            project_root=data.project_root,
            case_input_pins=data.case_input_pins,
            base_config_sha256=data.base_config_sha256,
            method_config_sha256=data.methods, method_configs=data.method_configs,
            selected_source_pins=source_pins, expected_source=data.source,
 case_workspace=data.case_workspace,
 case_memory_limit_bytes=8 * 1024**3,
        )
    evidence_path.write_bytes(evidence_raw)

    with patch(
        "evaluation.phase2_cho_analysis_preparation.verified_score_rows",
        side_effect=AssertionError("scores were read before target attestation"),
    ) as reader:
        for index, field, wrong_value in (
            (0, "profile_b_artifact_sha256", "0" * 64),
            (0, "source_sha256", "0" * 64),
            (0, "source_file", "data/raw/moabb/cho2017/subject_02.gdf"),
            (15, "artifact_sha256", "0" * 64),
            (15, "base_config_sha256", "0" * 64),
        ):
            pin = pins[index]
            target_path = output / "cells" / f"{pin.identity.sha256}.json"
            original = target_path.read_bytes()
            record = cast(dict[str, Any], json.loads(original))
            payload = record["payload"]
            attestation = payload["metrics"]["target_input_attestation"]
            if pin.plan.method == "eegnet":
                attestation["anchor"]["input_identities"][pin.plan.target_subject][
                    field
                ] = wrong_value
            else:
                binding = attestation["binding"]
                binding[field] = wrong_value
                attestation["binding_sha256"] = config_digest(binding)
            tampered = envelope("evaluation_cell", payload)
            _write_record(target_path, tampered)
            repinned = (
                *pins[:index], replace(pin, cell_sha256=tampered["sha256"]),
                *pins[index + 1:],
            )
            with pytest.raises(ValueError, match="differs"):
                prepare_cho_paired_inputs_from_recorder(
                    data.route, recorder, repinned,
                    project_root=data.project_root,
                    case_input_pins=data.case_input_pins,
                    base_config_sha256=data.base_config_sha256,
                    method_config_sha256=data.methods, method_configs=data.method_configs,
                    selected_source_pins=source_pins, expected_source=data.source,
 case_workspace=data.case_workspace,
 case_memory_limit_bytes=8 * 1024**3,
                )
            target_path.write_bytes(original)
        reader.assert_not_called()

    cell_path = output / "cells" / f"{pins[0].identity.sha256}.json"
    cell_path.write_bytes(b"corrupt recorder cell\n")
    with pytest.raises(ValueError, match="record JSON is invalid"):
        prepare_cho_paired_inputs_from_recorder(
            data.route, recorder, pins,
            project_root=data.project_root,
            case_input_pins=data.case_input_pins,
            base_config_sha256=data.base_config_sha256,
            method_config_sha256=data.methods, method_configs=data.method_configs,
            selected_source_pins=source_pins, expected_source=data.source,
 case_workspace=data.case_workspace,
 case_memory_limit_bytes=8 * 1024**3,
        )


def test_republished_wrong_query_metrics_fail_before_score_extraction(
    synthetic_inputs: SyntheticInputs, tmp_path: Path,
) -> None:
    data = synthetic_inputs
    recorder = CaseRecorder(tmp_path)
    pins, source_pins = _publish_synthetic_recorder(
        recorder, data.route, data.pins,
        project_root=data.project_root,
        base_config_sha256=data.base_config_sha256,
        profile_b_config_sha256=data.profile_b_config_sha256,
    )
    pin = pins[0]
    output = recorder.output_root
    cell_path = output / "cells" / f"{pin.identity.sha256}.json"
    intent_path = output / "publication_intents" / f"{pin.plan.case_id}.intent.json"
    success_path = output / "successes" / f"{pin.plan.case_id}.success.json"
    original_cell = cell_path.read_bytes()
    original_intent = intent_path.read_bytes()
    original_success = success_path.read_bytes()

    # Both metrics agree with their own confusion matrix. The first omits a
    # query trial; the second keeps 32 trials but shifts one true-class count.
    for confusion, error in (
        ([[8, 7], [0, 16]], "query count differs"),
        ([[9, 8], [0, 15]], "confusion row totals differ"),
    ):
        try:
            cell = cast(dict[str, Any], json.loads(original_cell))
            metrics = cell["payload"]["metrics"]
            metrics["confusion_matrix"] = confusion
            metrics["query_count"] = sum(sum(row) for row in confusion)
            score = (
                Fraction(confusion[0][0], sum(confusion[0]))
                + Fraction(confusion[1][1], sum(confusion[1]))
            ) / 2
            metrics["balanced_accuracy"] = [score.numerator, score.denominator]
            recorder._validated_metrics(metrics)
            republished_cell = envelope("evaluation_cell", cell["payload"])
            _write_record(cell_path, republished_cell)

            intent = cast(dict[str, Any], json.loads(original_intent))
            intent["payload"]["cell"] = republished_cell
            _write_record(intent_path, envelope("engineering_smoke", intent["payload"]))
            success = cast(dict[str, Any], json.loads(original_success))
            success["payload"]["cell_sha256"] = republished_cell["sha256"]
            success_raw = _write_record(
                success_path, envelope("engineering_smoke", success["payload"]),
            )
            repinned = (
                replace(
                    pin, cell_sha256=republished_cell["sha256"],
                    success_file_sha256=hashlib.sha256(success_raw).hexdigest(),
                ),
                *pins[1:],
            )
            with patch(
                "evaluation.phase2_cho_analysis_preparation.verified_score_rows",
                side_effect=AssertionError("scores were read before route query checks"),
            ) as reader:
                with pytest.raises(ValueError, match=error):
                    prepare_cho_paired_inputs_from_recorder(
                        data.route, recorder, repinned,
                        project_root=data.project_root,
                        case_input_pins=data.case_input_pins,
                        base_config_sha256=data.base_config_sha256,
                        method_config_sha256=data.methods, method_configs=data.method_configs,
                        selected_source_pins=source_pins,
                        expected_source=data.source,
                        case_workspace=data.case_workspace,
                        case_memory_limit_bytes=8 * 1024**3,
                    )
                reader.assert_not_called()
        finally:
            cell_path.write_bytes(original_cell)
            intent_path.write_bytes(original_intent)
            success_path.write_bytes(original_success)
