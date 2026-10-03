"""Read-only byte binding for one externally pinned Cho selected-source manifest.

This verifies publication file identities and the manifest's engineering claims.
It does not decode safetensors, reconstruct tensor state, verify historical model
use, admit a complete source selector, or authorize scientific evaluation.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.config import config_digest
from core.provenance import SourceProvenance
from evaluation.phase2_cell_aggregation_bridge import _canonical_record
from evaluation.phase2_factored_evidence import (
    MAXIMUM_LOGICAL_BYTES,
    MAXIMUM_PACKED_BYTES,
    SCHEMA,
    unpack_factored_selection,
)
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import verify_envelope

MAXIMUM_MANIFEST_BYTES = 4 * 1024**2
MAXIMUM_WEIGHTS_BYTES = 4 * 1024**3
_BASE_FIELDS = frozenset({
    "purpose", "scope", "scientific_evaluation", "evidence_sha256",
    "selected_candidate", "selection_contract_sha256", "protocol_config_sha256",
    "source", "model_class", "model_recipe", "model_recipe_sha256",
    "model_state_sha256", "tensor_schema", "weights_sha256", "weights_file",
    "evidence_file",
})
_SPARSE_FIELDS = frozenset({
    "weights_format", "initial_state_sha256", "final_fit_mask_sha256",
    "trainable_parameter_names", "stored_tensor_names", "omitted_tensor_names",
})
_FACTORED_FIELDS = frozenset({
    "evidence_format", "evidence_schema", "evidence_physical_sha256",
    "evidence_physical_bytes",
})
_FileIdentity = tuple[int, int, int, int]


def _identity(path: Path) -> _FileIdentity:
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def _direct_directory(path: Path, root: Path) -> None:
    if not path.is_relative_to(root):
        raise ValueError("selected source directory escapes project root")
    current = root
    if current.is_symlink() or not current.is_dir() or current.resolve(strict=True) != current:
        raise ValueError("project root aliases another path")
    for part in path.relative_to(root).parts:
        current = current / part
        if (
            current.is_symlink() or not current.is_dir()
            or current.resolve(strict=True) != current
        ):
            raise ValueError("selected source directory aliases another path")


def _direct_file(path: Path, root: Path) -> None:
    _direct_directory(path.parent, root)
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise ValueError("selected source file is absent or aliases another path")


def _streamed_file_sha256(path: Path, root: Path) -> tuple[str, _FileIdentity]:
    """Hash bounded weights with stable path/handle identity and constant memory."""
    _direct_file(path, root)
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= MAXIMUM_WEIGHTS_BYTES:
        raise ValueError("selected weights size or link count differs")
    digest = hashlib.sha256()
    observed = 0
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if not os.path.samestat(before, opened):
            raise ValueError("selected weights identity changed before read")
        while chunk := stream.read(1024 * 1024):
            observed += len(chunk)
            if observed > before.st_size or observed > MAXIMUM_WEIGHTS_BYTES:
                raise ValueError("selected weights grew during read")
            digest.update(chunk)
        finished = os.fstat(stream.fileno())
    _direct_file(path, root)
    after = path.stat()
    if (
        observed != before.st_size or not os.path.samestat(before, finished)
        or not os.path.samestat(before, after)
        or before.st_mtime_ns != opened.st_mtime_ns
        or before.st_mtime_ns != finished.st_mtime_ns
        or before.st_mtime_ns != after.st_mtime_ns
        or after.st_nlink != 1
    ):
        raise ValueError("selected weights identity changed during read")
    return digest.hexdigest(), _identity(path)


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _manifest_fields(payload: Mapping[str, Any], evidence_sha256: str) -> None:
    sparse = payload.get("weights_format", "full_v1")
    if sparse not in {"full_v1", "sparse_frozen_init_v2"}:
        raise ValueError("selected source weights format is unsupported")
    factored = payload.get("evidence_format", "canonical_json_v1")
    if factored not in {"canonical_json_v1", "factored_json_v1"}:
        raise ValueError("selected source evidence format is unsupported")
    fields = _BASE_FIELDS
    if sparse == "sparse_frozen_init_v2":
        fields |= _SPARSE_FIELDS
    if factored == "factored_json_v1":
        fields |= _FACTORED_FIELDS
    if set(payload) != fields:
        raise ValueError("selected source manifest fields differ from its published format")
    if sparse == "sparse_frozen_init_v2":
        for name in ("initial_state_sha256", "final_fit_mask_sha256"):
            require_digest(payload[name], name)
        for name in (
            "trainable_parameter_names", "stored_tensor_names", "omitted_tensor_names",
        ):
            values = payload[name]
            if (
                not isinstance(values, list)
                or any(not isinstance(item, str) or not item for item in values)
                or len(set(values)) != len(values)
            ):
                raise ValueError(f"selected source {name} is invalid")
    if factored == "factored_json_v1":
        physical_sha = payload["evidence_physical_sha256"]
        require_digest(physical_sha, "physical evidence")
        size = payload["evidence_physical_bytes"]
        if (
            payload["evidence_schema"] != SCHEMA
            or type(size) is not int or not 0 < size <= MAXIMUM_PACKED_BYTES
            or payload["evidence_file"] != f"evidence/{physical_sha}.factored.json"
        ):
            raise ValueError("factored selected evidence declaration differs")
    elif payload["evidence_file"] != f"evidence/{evidence_sha256}.json":
        raise ValueError("selected evidence path differs from external pin")


def _read_evidence(
    path: Path, root: Path, *, evidence_sha256: str,
    physical_sha256: str | None, physical_bytes: int | None,
    selection_contract_sha256: str, selected_candidate: str,
    protocol_config_sha256: str, expected_source: SourceProvenance,
    model_state_sha256: str,
) -> tuple[str, _FileIdentity, int]:
    """Bind bounded evidence bytes and recorded claims to external pins."""
    _direct_file(path, root)
    limit = MAXIMUM_PACKED_BYTES if physical_sha256 is not None else MAXIMUM_LOGICAL_BYTES
    record, raw = _canonical_record(path, maximum_bytes=limit)
    observed = hashlib.sha256(raw).hexdigest()
    if physical_sha256 is not None:
        if observed != physical_sha256 or len(raw) != physical_bytes:
            raise ValueError("factored selected evidence physical bytes differ")
        logical = unpack_factored_selection(raw, expected_evidence_sha256=evidence_sha256)
    else:
        logical = record
    payload = _mapping(logical.get("payload"), "selected evidence payload")
    if (
        logical.get("sha256") != evidence_sha256
        or not verify_envelope(logical, kind="engineering_smoke", expected_payload=payload)
    ):
        raise ValueError("selected evidence differs from external logical pin")
    contract = _mapping(payload.get("contract"), "selected evidence contract")
    final_fit = _mapping(payload.get("final_source_fit"), "selected final source fit")
    if (
        payload.get("purpose") not in {
            "bounded_eegnet_source_selection", "bounded_labram_source_selection",
            "bounded_tcpl_source_selection",
        }
        or payload.get("complete") is not True
        or payload.get("outer_target_predictions_performed") is not False
        or payload.get("contract_sha256") != selection_contract_sha256
        or config_digest(contract) != selection_contract_sha256
        or payload.get("selected_candidate") != selected_candidate
        or contract.get("protocol_sha256") != protocol_config_sha256
        or contract.get("source") != asdict(expected_source)
        or final_fit.get("fitted_state_sha256") != model_state_sha256
        or final_fit.get("candidate") != selected_candidate
    ):
        raise ValueError("selected evidence claims differ from external publication pins")
    roster = contract.get("candidates")
    if not isinstance(roster, list):
        raise ValueError("selected evidence winner roster is absent")
    winners = [
        row for row in roster
        if isinstance(row, dict) and row.get("name") == selected_candidate
    ]
    if (
        len(winners) != 1
        or final_fit.get("candidate_sha256") != config_digest(winners[0])
    ):
        raise ValueError("selected evidence final candidate digest differs")
    return observed, _identity(path), limit


@dataclass(frozen=True, slots=True)
class ChoSelectedManifestWitness:
    """Pinned file identities to recheck after caller's score extraction."""

    project_root: Path
    manifest_path: Path
    manifest_sha256: str
    manifest_file_sha256: str
    manifest_identity: _FileIdentity
    evidence_path: Path
    evidence_file_sha256: str
    evidence_identity: _FileIdentity
    evidence_limit: int
    weights_path: Path
    weights_sha256: str
    weights_identity: _FileIdentity

    def verify_stable(self) -> None:
        """Refuse post-verification byte edits or same-byte file replacement."""
        _direct_file(self.manifest_path, self.project_root)
        manifest, raw = _canonical_record(
            self.manifest_path, maximum_bytes=MAXIMUM_MANIFEST_BYTES,
        )
        if (
            manifest.get("sha256") != self.manifest_sha256
            or hashlib.sha256(raw).hexdigest() != self.manifest_file_sha256
            or _identity(self.manifest_path) != self.manifest_identity
        ):
            raise ValueError("selected source manifest changed after verification")
        _direct_file(self.evidence_path, self.project_root)
        _, evidence_raw = _canonical_record(
            self.evidence_path, maximum_bytes=self.evidence_limit,
        )
        if (
            hashlib.sha256(evidence_raw).hexdigest() != self.evidence_file_sha256
            or _identity(self.evidence_path) != self.evidence_identity
        ):
            raise ValueError("selected evidence changed after verification")
        weight_sha, identity = _streamed_file_sha256(self.weights_path, self.project_root)
        if weight_sha != self.weights_sha256 or identity != self.weights_identity:
            raise ValueError("selected weights changed after verification")


def verify_cho_selected_manifest_files(
    project_root: Path,
    manifest_path: Path,
    *,
    manifest_sha256: str,
    evidence_sha256: str,
    selection_contract_sha256: str,
    selected_candidate: str,
    protocol_config_sha256: str,
    expected_source: SourceProvenance,
    model_recipe_sha256: str,
    model_state_sha256: str,
) -> ChoSelectedManifestWitness:
    """Bind one publication to external claims without restoring tensors or fitting.

    The caller must supply the pins independently of the manifest. A matching
    weight-file hash does not prove reconstructed tensor state or historical use.
    """
    if (
        not isinstance(project_root, Path) or not isinstance(manifest_path, Path)
        or not isinstance(expected_source, SourceProvenance)
        or not isinstance(selected_candidate, str) or not selected_candidate
    ):
        raise ValueError("typed root, manifest, source and winner are required")
    for name, value in (
        ("manifest", manifest_sha256), ("evidence", evidence_sha256),
        ("selection contract", selection_contract_sha256),
        ("protocol", protocol_config_sha256),
        ("model recipe", model_recipe_sha256), ("model state", model_state_sha256),
    ):
        require_digest(value, name)
    root = project_root.resolve(strict=True)
    if root != project_root:
        raise ValueError("project root must be a direct absolute directory")
    base = root / "runs" / "phase2"
    if not manifest_path.is_relative_to(base):
        raise ValueError("selected source manifest escapes runs/phase2")
    expected_manifest = (
        base / "selected_sources" / "manifests"
        / f"{manifest_sha256}.json"
    )
    if manifest_path != expected_manifest:
        raise ValueError("selected source manifest path is not a direct pinned file")
    _direct_file(manifest_path, root)
    record, raw = _canonical_record(manifest_path, maximum_bytes=MAXIMUM_MANIFEST_BYTES)
    payload = _mapping(record.get("payload"), "selected source manifest payload")
    _manifest_fields(payload, evidence_sha256)
    recipe = _mapping(payload.get("model_recipe"), "selected model recipe")
    schema = _mapping(payload.get("tensor_schema"), "selected tensor schema")
    if any(
        not name or not isinstance(row, dict) or set(row) != {"shape", "dtype"}
        or not isinstance(row["shape"], list)
        or any(type(size) is not int or size < 0 for size in row["shape"])
        or not isinstance(row["dtype"], str) or not row["dtype"]
        for name, row in schema.items()
    ):
        raise ValueError("selected tensor schema declaration differs")
    if payload.get("weights_format") == "sparse_frozen_init_v2":
        trainable = payload["trainable_parameter_names"]
        stored = payload["stored_tensor_names"]
        omitted = payload["omitted_tensor_names"]
        if (
            not trainable or stored != sorted(trainable)
            or not set(stored).issubset(schema)
            or omitted != sorted(set(schema) - set(stored))
        ):
            raise ValueError("sparse selected tensor names do not partition the state")
    weights_sha = payload.get("weights_sha256")
    if not isinstance(weights_sha, str):
        raise ValueError("selected weights digest is missing")
    require_digest(weights_sha, "selected weights")
    if (
        record.get("sha256") != manifest_sha256
        or not verify_envelope(record, kind="engineering_smoke", expected_payload=payload)
        or payload.get("purpose") != "selected_source_snapshot"
        or payload.get("scope") != "engineering_only"
        or payload.get("scientific_evaluation") is not False
        or payload.get("evidence_sha256") != evidence_sha256
        or payload.get("selected_candidate") != selected_candidate
        or payload.get("selection_contract_sha256") != selection_contract_sha256
        or payload.get("protocol_config_sha256") != protocol_config_sha256
        or payload.get("source") != asdict(expected_source)
        or not isinstance(payload.get("model_class"), str)
        or not payload["model_class"]
        or not recipe or not schema
        or payload.get("model_recipe_sha256") != model_recipe_sha256
        or config_digest(recipe) != model_recipe_sha256
        or payload.get("model_state_sha256") != model_state_sha256
        or payload.get("weights_file") != f"weights/{weights_sha}.safetensors"
    ):
        raise ValueError("selected source manifest differs from external pins or schema")
    weights_path = manifest_path.parent.parent / "weights" / f"{weights_sha}.safetensors"
    evidence_path = manifest_path.parent.parent.joinpath(*payload["evidence_file"].split("/"))
    physical_sha = (
        payload["evidence_physical_sha256"]
        if payload.get("evidence_format") == "factored_json_v1" else None
    )
    physical_size = (
        payload["evidence_physical_bytes"]
        if payload.get("evidence_format") == "factored_json_v1" else None
    )
    evidence_file_sha, evidence_identity, evidence_limit = _read_evidence(
        evidence_path, root, evidence_sha256=evidence_sha256,
        physical_sha256=physical_sha, physical_bytes=physical_size,
        selection_contract_sha256=selection_contract_sha256,
        selected_candidate=selected_candidate,
        protocol_config_sha256=protocol_config_sha256,
        expected_source=expected_source, model_state_sha256=model_state_sha256,
    )
    observed, weights_identity = _streamed_file_sha256(weights_path, root)
    if observed != weights_sha:
        raise ValueError("selected weights bytes differ from manifest hash")
    witness = ChoSelectedManifestWitness(
        root, manifest_path, manifest_sha256, hashlib.sha256(raw).hexdigest(),
        _identity(manifest_path),
        evidence_path, evidence_file_sha, evidence_identity, evidence_limit,
        weights_path, weights_sha, weights_identity,
    )
    witness.verify_stable()
    return witness
