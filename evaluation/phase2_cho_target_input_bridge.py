"""Read-only checks of prospective Cho target-input cell attestations.

The caller first verifies the route, independent source and case identities.
These checks compare pinned cell bytes with the route's declared target assets.
They rely on the pinned executor source to establish that a published binding
was observed at prediction time; they do not independently replay inference
or admit a scientific result.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from core.config import config_digest
from evaluation.phase2_cell_aggregation_bridge import (
    MAX_CELL_BYTES,
    PinnedCaseCell,
    _canonical_record,
)
from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute
from evaluation.phase2_cho_persisted_target import ChoPersistedTargetDeclarations
from evaluation.phase2_profile_binding import CHO_CHANNELS, ChoProfileBinding60Hz
from evaluation.phase2_protocol import (
    TrialCatalog,
    nested_episode,
    require_digest,
    source_selection,
)
from evaluation.phase2_records import verify_envelope
from evaluation.phase2_runner import CaseRecorder
from scripts.audit_phase2_protocol import validate_protocol

_SCHEMA = "cho2017-target-input-v1"
_COMMON = frozenset({"schema", "method", "subject", "episode_record_sha256", "profile"})
_ANCHOR = frozenset({
    "method", "subject", "role", "episode_sha256", "selection_sha256",
    "support_trial_ids", "query_trial_ids", "source_subjects", "input_identities",
})
_A_IDENTITY = frozenset({
    "catalog_sha256", "artifact_sha256", "manifest_sha256", "base_config_sha256",
})
_B_BINDING = frozenset(field.name for field in fields(ChoProfileBinding60Hz))


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed mapping")
    return value


def _rows(value: Any, expected_count: int, input_trials: int) -> bool:
    return (
        isinstance(value, list) and len(value) == expected_count
        and all(type(row) is int and 0 <= row < input_trials for row in value)
    )


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a digest")
    require_digest(value, name)
    return value


def _query_metrics(
    metrics: Mapping[str, Any], catalog: TrialCatalog, query_indices: tuple[int, ...],
) -> None:
    """Bind the recorded confusion rows to the route's target query labels."""
    if type(metrics.get("query_count")) is not int or metrics["query_count"] != len(
        query_indices
    ):
        raise ValueError("Cho target query count differs from the planned episode")
    confusion = metrics.get("confusion_matrix")
    if (
        len(catalog.classes) != 2
        or not isinstance(confusion, list) or len(confusion) != 2
        or any(not isinstance(row, list) or len(row) != 2 for row in confusion)
        or any(type(entry) is not int or entry < 0
               for row in confusion for entry in row)
    ):
        raise ValueError("Cho target confusion matrix must have two nonnegative integer rows")
    expected = tuple(
        sum(catalog.labels[index] == label for index in query_indices)
        for label in catalog.classes
    )
    if tuple(sum(row) for row in confusion) != expected:
        raise ValueError("Cho target confusion row totals differ from query labels")


def _profile_b(
    attestation: Mapping[str, Any], route: ChoFirstTrancheRoute,
    declarations: ChoPersistedTargetDeclarations,
    pin: PinnedCaseCell, catalog: TrialCatalog,
    episode_sha256: str, support_ids: tuple[str, ...], query_ids: tuple[str, ...],
) -> None:
    if set(attestation) != _COMMON | {"binding_sha256", "binding"}:
        raise ValueError("Cho LaBraM target attestation fields differ")
    asset = route.labram_assets.get(pin.plan.target_subject)
    binding = _mapping(attestation.get("binding"), "Cho target binding")
    if asset is None or set(binding) != _B_BINDING:
        raise ValueError("Cho target binding or declared asset is incomplete")
    binding_sha256 = _digest(attestation.get("binding_sha256"), "Cho target binding")
    if config_digest(binding) != binding_sha256:
        raise ValueError("Cho target binding digest differs from published fields")
    input_trials = binding.get("input_trials")
    rejected = binding.get("profile_a_rejected_trials")
    support_rows = binding.get("support_profile_b_rows")
    query_rows = binding.get("query_profile_b_rows")
    if (
        type(input_trials) is not int or input_trials < len(catalog.trial_ids)
        or type(rejected) is not int or rejected < 0
        or input_trials - rejected != len(catalog.trial_ids)
        or not _rows(support_rows, len(support_ids), input_trials)
        or not _rows(query_rows, len(query_ids), input_trials)
    ):
        raise ValueError("Cho target binding row or retention counts differ")
    if not isinstance(support_rows, list) or not isinstance(query_rows, list):
        raise ValueError("Cho target binding rows are missing")
    if len(set([*support_rows, *query_rows])) != len(support_ids) + len(query_ids):
        raise ValueError("Cho target binding rows overlap")
    expected = {
        "dataset": "cho2017",
        "subject": pin.plan.target_subject,
        "shots_per_class": pin.plan.shots_per_class,
        "classes": list(catalog.classes),
        "channel_names": list(CHO_CHANNELS),
        "protocol_sha256": pin.identity.protocol_sha256,
        "episode_sha256": episode_sha256,
        "profile_a_artifact_sha256": catalog.artifact_sha256,
        "profile_b_artifact_sha256": asset.profile_b_artifact_sha256,
        "profile_b_manifest_sha256": asset.profile_b_manifest_sha256,
        "profile_a_preprocessing_sha256": catalog.preprocessing_sha256,
        "support_trial_ids": list(support_ids),
        "query_trial_ids": list(query_ids),
        "variant_config_sha256": asset.variant_config_sha256,
        "schema": "cho-a-to-b-episode-60hz-v1",
        "sampling_rate_hz": 200,
        "samples_per_trial": 800,
        "patch_samples": 200,
        "stored_unit_volts": 0.0001,
        "extra_input_scale": 1.0,
        "rejection_policy": "profile_a_frozen_threshold_only",
        "target_transform_fit": "none",
        "profile_a_sidecar_manifests":
            "absent_cho_identity_is_the_audited_catalog_hash",
    }
    if any(binding.get(name) != value for name, value in expected.items()):
        raise ValueError("Cho target binding differs from the planned 60 Hz inputs")
    if (
        binding.get("profile_b_config_sha256")
        != declarations.profile_b_config_sha256
        or binding.get("base_config_sha256") != declarations.base_config_sha256
    ):
        raise ValueError("Cho target configuration differs from pinned bytes")
    source_file = binding.get("source_file")
    if (
        not isinstance(source_file, str)
        or not source_file.startswith("data/raw/moabb/cho2017/")
        or "\\" in source_file or ".." in Path(source_file).parts
        or (source_file, binding.get("source_sha256"))
        != declarations.source_by_subject.get(pin.plan.target_subject)
    ):
        raise ValueError("Cho target raw source differs from pinned B manifest")


def _profile_a(
    attestation: Mapping[str, Any], declarations: ChoPersistedTargetDeclarations,
    pin: PinnedCaseCell,
    catalog: TrialCatalog, episode_sha256: str, selection_sha256: str,
    source_subjects: tuple[str, ...], support_ids: tuple[str, ...],
    query_ids: tuple[str, ...],
) -> None:
    if set(attestation) != _COMMON | {"anchor"}:
        raise ValueError("Cho EEGNet target attestation fields differ")
    anchor = _mapping(attestation.get("anchor"), "Cho EEGNet anchor")
    if set(anchor) != _ANCHOR:
        raise ValueError("Cho EEGNet anchor fields differ")
    expected = {
        "method": "eegnet",
        "subject": pin.plan.target_subject,
        "role": "outer_target",
        "episode_sha256": episode_sha256,
        "selection_sha256": selection_sha256,
        "support_trial_ids": list(support_ids),
        "query_trial_ids": list(query_ids),
        "source_subjects": list(source_subjects),
    }
    if any(anchor.get(name) != value for name, value in expected.items()):
        raise ValueError("Cho EEGNet anchor differs from the target episode")
    identities = _mapping(anchor.get("input_identities"), "Cho EEGNet input identities")
    if set(identities) != {pin.plan.target_subject}:
        raise ValueError("Cho EEGNet must claim only target Profile A")
    observed = _mapping(identities[pin.plan.target_subject], "Cho EEGNet target Profile A")
    if (
        set(observed) != _A_IDENTITY
        or observed.get("catalog_sha256") != catalog.sha256
        or observed.get("artifact_sha256") != catalog.artifact_sha256
        or observed.get("manifest_sha256") != catalog.artifact_sha256
    ):
        raise ValueError("Cho EEGNet target Profile A differs from the catalog")
    if observed.get("base_config_sha256") != declarations.base_config_sha256:
        raise ValueError("Cho EEGNet base config differs from pinned bytes")


def verify_cho_recorded_target_inputs(
    route: ChoFirstTrancheRoute, recorder: CaseRecorder,
    pins: Sequence[PinnedCaseCell],
    *, declarations: ChoPersistedTargetDeclarations,
) -> None:
    """Require a route-matched target attestation in every externally pinned cell.

    The caller must first run the independent-source identity binder. This
    function checks recorded declarations, not a fresh execution or scientific
    admission. ``verified_score_rows`` separately checks the complete recorder.
    """
    if (
        not isinstance(route, ChoFirstTrancheRoute)
        or not isinstance(recorder, CaseRecorder)
        or not isinstance(declarations, ChoPersistedTargetDeclarations)
        or len(route.plans) != 1040 or len(pins) != 1040
        or any(not isinstance(pin, PinnedCaseCell) for pin in pins)
    ):
        raise ValueError("complete typed Cho route, recorder and pins are required")
    config = json.loads(route.protocol_config_json)
    shots = validate_protocol(config)
    catalogs = {catalog.subject: catalog for catalog in route.catalogs}
    if len(catalogs) != 52 or len({pin.plan.case_id for pin in pins}) != 1040:
        raise ValueError("Cho target attestation roster is incomplete")
    for pin in pins:
        plan = pin.plan
        if plan not in route.plans or plan.target_subject not in catalogs:
            raise ValueError("Cho target attestation pin differs from the route")
        catalog = catalogs[plan.target_subject]
        episode = nested_episode(
            catalog, shots=shots, protocol_sha256=pin.identity.protocol_sha256,
        )
        partition = episode.partition(plan.shots_per_class)
        support_ids = tuple(catalog.trial_ids[index] for index in partition.support_indices)
        query_ids = tuple(catalog.trial_ids[index] for index in partition.query_indices)
        selection = source_selection(route.catalogs, target=plan.target_subject)
        path = recorder.output_root / "cells" / f"{pin.identity.sha256}.json"
        cell, _ = _canonical_record(path, maximum_bytes=MAX_CELL_BYTES)
        payload = _mapping(cell.get("payload"), "Cho target cell payload")
        if (
            cell.get("sha256") != pin.cell_sha256
            or set(payload) != {"identity", "metrics"}
            or payload["identity"] != asdict(pin.identity)
            or not verify_envelope(cell, kind="evaluation_cell", expected_payload=payload)
        ):
            raise ValueError("Cho target cell differs from external pin")
        metrics = _mapping(payload["metrics"], "Cho target cell metrics")
        _query_metrics(metrics, catalog, partition.query_indices)
        attestation = _mapping(
            metrics.get("target_input_attestation"), "Cho target input attestation",
        )
        if (
            attestation.get("schema") != _SCHEMA
            or attestation.get("method") != plan.method
            or attestation.get("subject") != plan.target_subject
            or attestation.get("episode_record_sha256") != pin.identity.episode_sha256
        ):
            raise ValueError("Cho target input attestation differs from case identity")
        if plan.method == "eegnet":
            if attestation.get("profile") != "cho_profile_a":
                raise ValueError("Cho EEGNet target input is not Profile A")
            _profile_a(
                attestation, declarations, pin, catalog,
                episode.sha256, selection.sha256,
                selection.source_subjects, support_ids, query_ids,
            )
        else:
            if attestation.get("profile") != "cho_profile_b_60hz_v1":
                raise ValueError("Cho LaBraM target input is not 60 Hz Profile B")
            _profile_b(attestation, route, declarations,
                       pin, catalog, episode.sha256,
                       support_ids, query_ids)
