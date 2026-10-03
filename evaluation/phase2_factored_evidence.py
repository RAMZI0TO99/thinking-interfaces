"""Opt-in, in-memory lossless factoring of completed source-selection evidence.

This codec does not publish evidence or admit a scientific case. A future store
must bind its physical bytes in a write-once manifest and call the public
selection verifier on the reconstructed logical record.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.config import canonical_config_json, config_digest
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import verify_envelope

SCHEMA = "phase2_factored_selection_evidence_v1"
MAXIMUM_PACKED_BYTES = 64 * 1024**2
MAXIMUM_LOGICAL_BYTES = 128 * 1024**2
MAXIMUM_SOURCE_SUBJECTS = 52
MAXIMUM_CANDIDATES = 2
_PURPOSES = frozenset({
    "bounded_eegnet_source_selection",
    "bounded_labram_source_selection",
    "bounded_tcpl_source_selection",
})
_PACKED_FIELDS = frozenset({
    "schema", "logical_envelope_sha256", "logical_file_sha256",
    "logical_file_bytes", "source_identities_by_subject",
    "validation_binding_by_subject", "bindings_factored", "compact_record",
})


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _rows(value: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{name} must be an array of objects")
    return value


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a SHA-256 digest")
    require_digest(value, name)
    return value


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (canonical_config_json(value) + "\n").encode("utf-8")


def _selection_shape(record: dict[str, Any]) -> tuple[
    dict[str, Any], list[str], list[str], list[dict[str, Any]]
]:
    payload = _mapping(record.get("payload"), "selection payload")
    contract = _mapping(payload.get("contract"), "selection contract")
    selection = _mapping(contract.get("selection"), "source cohort")
    raw_sources = selection.get("source_subjects")
    candidates = _rows(contract.get("candidates"), "selection candidates")
    if not isinstance(raw_sources, list):
        raise ValueError("selection source subjects must be an array")
    sources: list[str] = []
    for subject in raw_sources:
        if not isinstance(subject, str) or not subject:
            raise ValueError("selection source subject is invalid")
        sources.append(subject)
    names: list[str] = []
    for candidate in candidates:
        name = candidate.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("selection candidate name is invalid")
        names.append(name)
    folds = _rows(payload.get("folds"), "selection folds")
    if (
        not 2 <= len(sources) <= MAXIMUM_SOURCE_SUBJECTS
        or len(set(sources)) != len(sources)
        or selection.get("target_subject") in sources
        or not 1 <= len(names) <= MAXIMUM_CANDIDATES
        or len(set(names)) != len(names)
        or len(folds) != len(sources) * len(names)
        or payload.get("selected_candidate") not in names
        or payload.get("contract_sha256") != config_digest(contract)
    ):
        raise ValueError("complete candidate by source-subject selection is required")
    return payload, sources, names, folds


def _fit_members(
    fit: dict[str, Any], *, sources: list[str], candidate: str,
    validation: str | None, allow_missing_candidate: bool,
) -> list[str]:
    members = [subject for subject in sources if subject != validation]
    if (
        ("candidate" in fit and fit["candidate"] != candidate)
        or ("candidate" not in fit and not allow_missing_candidate)
        or fit.get("validation_subject") != validation
        or fit.get("training_subjects") != members
    ):
        raise ValueError("source fit differs from its candidate or training subjects")
    return members


def _validated_record(record: Mapping[str, Any]) -> tuple[dict[str, Any], bytes]:
    detached = copy.deepcopy(_mapping(dict(record), "selection record"))
    payload = _mapping(detached.get("payload"), "selection payload")
    if (
        payload.get("purpose") not in _PURPOSES
        or payload.get("complete") is not True
        or payload.get("outer_target_predictions_performed") is not False
        or not verify_envelope(
            detached, kind="engineering_smoke", expected_payload=payload,
        )
    ):
        raise ValueError("complete canonical engineering selection is required")
    logical = _canonical_bytes(detached)
    if len(logical) > MAXIMUM_LOGICAL_BYTES:
        raise ValueError("logical selection evidence exceeds the codec byte limit")
    return detached, logical


def _expansion_upper_bound(
    compact: dict[str, Any], sources: list[str], folds: list[dict[str, Any]],
    source_table: dict[str, Any], binding_table: dict[str, Any],
    factor_bindings: bool,
) -> int:
    """Bound repeated JSON values before allocating reconstructed fold maps."""

    fragments = {
        subject: len(canonical_config_json({subject: source_table[subject]}).encode("utf-8")) - 2
        for subject in sources
    }

    def map_size(members: list[str]) -> int:
        return 2 + sum(fragments[subject] for subject in members) + max(0, len(members) - 1)

    estimate = len(_canonical_bytes(compact)) + map_size(sources)
    for fold in folds:
        validation = fold.get("validation_subject")
        if not isinstance(validation, str) or validation not in source_table:
            raise ValueError("compact fold validation subject is unexpected")
        estimate += map_size([subject for subject in sources if subject != validation])
        if factor_bindings:
            estimate += len(canonical_config_json(binding_table[validation]).encode("utf-8"))
    # Each inserted field name, colon and comma adds less than 64 bytes.
    return estimate + 64 * (len(folds) + 1) * (2 if factor_bindings else 1)


def pack_factored_selection(record: Mapping[str, Any]) -> bytes:
    """Factor repeated values only after every omitted copy is checked exactly."""

    original, logical = _validated_record(record)
    payload, sources, names, folds = _selection_shape(original)
    allow_missing_candidate = payload["purpose"] == "bounded_tcpl_source_selection"
    final_fit = _mapping(payload.get("final_source_fit"), "final source fit")
    _fit_members(
        final_fit, sources=sources, candidate=payload["selected_candidate"],
        validation=None, allow_missing_candidate=allow_missing_candidate,
    )
    source_table = copy.deepcopy(_mapping(
        final_fit.get("input_identities"), "final source input identities",
    ))
    if set(source_table) != set(sources):
        raise ValueError("final source input table differs from its cohort")
    binding_table: dict[str, Any] = {}
    binding_presence = ["binding" in fold for fold in folds]
    if any(binding_presence) and not all(binding_presence):
        raise ValueError("validation bindings are present in only some folds")
    factor_bindings = all(binding_presence)
    seen: set[tuple[str, str]] = set()
    for fold in folds:
        candidate = fold.get("candidate")
        validation = fold.get("validation_subject")
        if (
            not isinstance(candidate, str) or candidate not in names
            or not isinstance(validation, str) or validation not in sources
            or (candidate, validation) in seen
        ):
            raise ValueError("candidate-validation fold is duplicated or unexpected")
        seen.add((candidate, validation))
        fit = _mapping(fold.get("source_fit"), "fold source fit")
        members = _fit_members(
            fit, sources=sources, candidate=candidate, validation=validation,
            allow_missing_candidate=allow_missing_candidate,
        )
        identities = _mapping(fit.get("input_identities"), "fold source identities")
        if set(identities) != set(members) or any(
            identities[subject] != source_table[subject] for subject in members
        ):
            raise ValueError("fold source identities differ from the shared table")
        if factor_bindings:
            binding = _mapping(fold["binding"], "fold validation binding")
            if binding.get("subject") != validation or (
                validation in binding_table and binding != binding_table[validation]
            ):
                raise ValueError("fold validation binding differs from the shared table")
            binding_table[validation] = copy.deepcopy(binding)
    if seen != {(candidate, subject) for candidate in names for subject in sources}:
        raise ValueError("candidate-validation fold grid is incomplete")
    if factor_bindings and set(binding_table) != set(sources):
        raise ValueError("validation binding table is incomplete")

    compact = copy.deepcopy(original)
    compact_payload = compact["payload"]
    compact_payload["final_source_fit"].pop("input_identities")
    for fold in compact_payload["folds"]:
        fold["source_fit"].pop("input_identities")
        if factor_bindings:
            fold.pop("binding")
    packed = {
        "schema": SCHEMA,
        "logical_envelope_sha256": original["sha256"],
        "logical_file_sha256": hashlib.sha256(logical).hexdigest(),
        "logical_file_bytes": len(logical),
        "source_identities_by_subject": source_table,
        "validation_binding_by_subject": binding_table,
        "bindings_factored": factor_bindings,
        "compact_record": compact,
    }
    encoded = _canonical_bytes(packed)
    if len(encoded) > MAXIMUM_PACKED_BYTES:
        raise ValueError("factored selection evidence exceeds the packed byte limit")
    if _canonical_bytes(unpack_factored_selection(
        encoded, expected_evidence_sha256=original["sha256"],
    )) != logical:
        raise ValueError("factored evidence did not round-trip exactly")
    return encoded


def unpack_factored_selection(
    encoded: bytes, *, expected_evidence_sha256: str,
) -> dict[str, Any]:
    """Reconstruct the exact logical envelope before any public verification."""

    _digest(expected_evidence_sha256, "expected evidence")
    if len(encoded) > MAXIMUM_PACKED_BYTES:
        raise ValueError("factored evidence exceeds the packed byte limit")
    try:
        parsed = json.loads(encoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("factored evidence is not JSON") from error
    packed = _mapping(parsed, "factored evidence")
    if set(packed) != _PACKED_FIELDS or packed.get("schema") != SCHEMA or (
        _canonical_bytes(packed) != encoded
    ):
        raise ValueError("factored evidence has a noncanonical or unknown schema")
    logical_sha = _digest(packed["logical_file_sha256"], "logical file")
    if packed["logical_envelope_sha256"] != expected_evidence_sha256:
        raise ValueError("factored evidence differs from the external envelope pin")
    logical_size = packed["logical_file_bytes"]
    if type(logical_size) is not int or not 0 < logical_size <= MAXIMUM_LOGICAL_BYTES:
        raise ValueError("declared logical evidence size exceeds the byte limit")
    compact_input = _mapping(packed["compact_record"], "compact record")
    payload, sources, names, folds = _selection_shape(compact_input)
    source_table = _mapping(
        packed["source_identities_by_subject"], "shared source identities",
    )
    binding_table = _mapping(
        packed["validation_binding_by_subject"], "shared validation bindings",
    )
    factor_bindings = packed["bindings_factored"]
    if (
        set(source_table) != set(sources)
        or type(factor_bindings) is not bool
        or set(binding_table) != (set(sources) if factor_bindings else set())
    ):
        raise ValueError("factored evidence subject tables differ from the cohort")
    if _expansion_upper_bound(
        compact_input, sources, folds, source_table, binding_table, factor_bindings,
    ) > MAXIMUM_LOGICAL_BYTES:
        raise ValueError("factored evidence expansion exceeds the logical byte limit")
    compact = copy.deepcopy(compact_input)
    payload = compact["payload"]
    allow_missing_candidate = payload["purpose"] == "bounded_tcpl_source_selection"
    folds = payload["folds"]
    final_fit = _mapping(payload.get("final_source_fit"), "compact final fit")
    if "input_identities" in final_fit:
        raise ValueError("compact final fit still carries repeated identities")
    _fit_members(
        final_fit, sources=sources, candidate=payload["selected_candidate"],
        validation=None, allow_missing_candidate=allow_missing_candidate,
    )
    final_fit["input_identities"] = copy.deepcopy(source_table)
    seen: set[tuple[str, str]] = set()
    for fold in folds:
        candidate = fold.get("candidate")
        validation = fold.get("validation_subject")
        if (
            not isinstance(candidate, str) or candidate not in names
            or not isinstance(validation, str) or validation not in sources
            or (candidate, validation) in seen
        ):
            raise ValueError("compact fold candidate or subject is unexpected")
        seen.add((candidate, validation))
        fit = _mapping(fold.get("source_fit"), "compact fold source fit")
        if "input_identities" in fit:
            raise ValueError("compact fold still carries repeated identities")
        members = _fit_members(
            fit, sources=sources, candidate=candidate, validation=validation,
            allow_missing_candidate=allow_missing_candidate,
        )
        fit["input_identities"] = {
            subject: copy.deepcopy(source_table[subject]) for subject in members
        }
        if factor_bindings:
            if "binding" in fold:
                raise ValueError("compact fold still carries a repeated binding")
            binding = _mapping(binding_table[validation], "shared validation binding")
            if binding.get("subject") != validation:
                raise ValueError("shared validation binding names another subject")
            fold["binding"] = copy.deepcopy(binding)
        elif "binding" in fold:
            raise ValueError("unfactored method unexpectedly has a validation binding")
    if seen != {(candidate, subject) for candidate in names for subject in sources}:
        raise ValueError("compact candidate-validation fold grid is incomplete")
    if payload.get("contract_sha256") != config_digest(payload["contract"]):
        raise ValueError("reconstructed selection contract differs")
    if not verify_envelope(
        compact, kind="engineering_smoke", expected_payload=payload,
    ) or compact.get("sha256") != expected_evidence_sha256:
        raise ValueError("reconstructed selection envelope differs")
    logical = _canonical_bytes(compact)
    if len(logical) != logical_size or hashlib.sha256(logical).hexdigest() != logical_sha:
        raise ValueError("reconstructed canonical selection bytes differ")
    return compact
