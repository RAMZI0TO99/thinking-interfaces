"""Append-only, pickle-free storage for a completed Phase II selected source.

The caller must separately verify scientific selection and construct the exact
architecture on restore. This store preserves bytes and checks their identity.
"""

from __future__ import annotations

import errno
import hashlib
import json
import math
import os
import re
import shutil
import stat
import sys
import tempfile
import time
import tomllib
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Literal

import torch
from safetensors.torch import load, save
from torch import nn

from core.config import canonical_config_json, config_digest, config_snapshot
from core.provenance import capture_source
from evaluation.labram_parity import state_digest
from evaluation.phase2_factored_evidence import (
    MAXIMUM_LOGICAL_BYTES,
    MAXIMUM_PACKED_BYTES,
    pack_factored_selection,
    unpack_factored_selection,
)
from evaluation.phase2_factored_evidence import (
    SCHEMA as FACTORED_EVIDENCE_SCHEMA,
)
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import envelope, verify_envelope, write_once

_PURPOSES = frozenset({
    "bounded_eegnet_source_selection", "bounded_labram_source_selection",
    "bounded_tcpl_source_selection",
})
_STORE_PURPOSE = "selected_source_snapshot"
_FULL_FORMAT: Final[Literal["full_v1"]] = "full_v1"
_SPARSE_FORMAT: Final[Literal["sparse_frozen_init_v2"]] = "sparse_frozen_init_v2"
SelectedWeightsFormat = Literal["full_v1", "sparse_frozen_init_v2"]
_CANONICAL_EVIDENCE_FORMAT: Final[Literal["canonical_json_v1"]] = "canonical_json_v1"
_FACTORED_EVIDENCE_FORMAT: Final[Literal["factored_json_v1"]] = "factored_json_v1"
SelectedEvidenceFormat = Literal["canonical_json_v1", "factored_json_v1"]
_BASE_MANIFEST_FIELDS = frozenset({
    "purpose", "scope", "scientific_evaluation", "evidence_sha256",
    "selected_candidate", "selection_contract_sha256", "protocol_config_sha256",
    "source", "model_class", "model_recipe", "model_recipe_sha256",
    "model_state_sha256", "tensor_schema", "weights_sha256", "weights_file",
    "evidence_file",
})
_SPARSE_MANIFEST_FIELDS = frozenset({
    "weights_format", "initial_state_sha256", "final_fit_mask_sha256",
    "trainable_parameter_names", "stored_tensor_names", "omitted_tensor_names",
})
_FACTORED_MANIFEST_FIELDS = frozenset({
    "evidence_format", "evidence_schema", "evidence_physical_sha256",
    "evidence_physical_bytes",
})
_MAXIMUM_MANIFEST_BYTES = 4 * 1024**2
_MAXIMUM_CHO_WEIGHTS_BYTES = 64 * 1024**2
_MAXIMUM_GENERIC_WEIGHTS_BYTES = 4 * 1024**3


@dataclass(frozen=True, slots=True)
class SelectedSourcePublication:
    manifest_sha256: str
    evidence_sha256: str
    selected_candidate: str
    model_state_sha256: str
    weights_sha256: str
    manifest_path: Path
    evidence_path: Path
    weights_path: Path
    resumed: bool
    weights_format: SelectedWeightsFormat = _FULL_FORMAT
    evidence_format: SelectedEvidenceFormat = _CANONICAL_EVIDENCE_FORMAT


@dataclass(frozen=True, slots=True)
class RestoredSelectedSource:
    model: nn.Module
    evidence_record: dict[str, Any]
    publication: SelectedSourcePublication


@dataclass(frozen=True, slots=True)
class SelectedWeightsPreflight:
    """Identity of a direct, bounded full-state file before model allocation."""

    path: Path
    sha256: str
    identity: tuple[int, int, int, int]


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(k, str) for k in value):
        raise ValueError(f"{name} must be a string-keyed mapping")
    return value


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a SHA-256 digest")
    require_digest(value, name)
    return value


def _json_bytes(record: Mapping[str, Any]) -> bytes:
    return (canonical_config_json(record) + "\n").encode("utf-8")


def _path(path: Path, parent: Path) -> Path:
    if path.is_symlink() or path.resolve() != path or path.resolve().parent != parent:
        raise ValueError("selected source path aliases or escapes its output directory")
    return path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _existing_exact(path: Path, parent: Path, expected_sha256: str, size: int) -> bool:
    _path(path, parent)
    if not path.exists():
        return False
    if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != expected_sha256:
        raise FileExistsError(f"conflicting or damaged immutable selected source: {path.name}")
    return True


def _write_blob(path: Path, parent: Path, blob: bytes, digest: str) -> bool:
    """Atomically link one fsynced content-addressed blob, never replacing a file."""
    if _existing_exact(path, parent, digest, len(blob)):
        return False
    descriptor, temporary = tempfile.mkstemp(prefix=".selected-source-", dir=parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            _existing_exact(path, parent, digest, len(blob))
            return False
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary)
    return True


def _read_exact(
    path: Path, parent: Path, expected_sha256: str, *, maximum_bytes: int,
) -> bytes:
    blob = _read_file(path, parent, maximum_bytes=maximum_bytes)
    if hashlib.sha256(blob).hexdigest() != expected_sha256:
        raise ValueError(f"selected source file hash differs: {path.name}")
    return blob


def _read_file(path: Path, parent: Path, *, maximum_bytes: int) -> bytes:
    if not path.is_file():
        raise ValueError(f"selected source file is absent: {path.name}")
    return _read_bounded_regular(path, parent, maximum_bytes)


def _read_bounded_factored(path: Path, parent: Path, expected_sha256: str) -> bytes:
    """Bound allocations before and during a packed read, then verify identity."""
    _path(path, parent)
    if not path.is_file():
        raise ValueError("factored selected evidence is absent")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= MAXIMUM_PACKED_BYTES:
        raise ValueError("factored selected evidence exceeds its byte limit or aliases")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if not os.path.samestat(before, opened) or before.st_size != opened.st_size:
            raise ValueError("factored selected evidence identity changed before read")
        blob = stream.read(MAXIMUM_PACKED_BYTES + 1)
        finished = os.fstat(stream.fileno())
    _path(path, parent)
    after = path.stat()
    if (
        len(blob) > MAXIMUM_PACKED_BYTES
        or len(blob) != before.st_size
        or len(blob) != opened.st_size
        or len(blob) != finished.st_size
        or len(blob) != after.st_size
        or not os.path.samestat(opened, after)
        or after.st_nlink != 1
    ):
        raise ValueError("factored selected evidence grew, shrank or changed identity")
    if hashlib.sha256(blob).hexdigest() != expected_sha256:
        raise ValueError(f"selected source file hash differs: {path.name}")
    return blob


def _read_bounded_regular(path: Path, parent: Path, maximum_bytes: int) -> bytes:
    """Keep the path, descriptor and size bound tied through a binary read."""
    _path(path, parent)
    before = path.stat()
    if (
        not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
        or not 0 < before.st_size <= maximum_bytes
    ):
        raise ValueError("selected source file exceeds its byte limit or aliases")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if not os.path.samestat(before, opened) or before.st_mtime_ns != opened.st_mtime_ns:
            raise ValueError("selected source file identity changed before read")
        blob = stream.read(maximum_bytes + 1)
        finished = os.fstat(stream.fileno())
    _path(path, parent)
    after = path.stat()
    if (
        len(blob) != before.st_size or len(blob) > maximum_bytes
        or not os.path.samestat(before, finished)
        or not os.path.samestat(before, after)
        or before.st_mtime_ns != finished.st_mtime_ns
        or before.st_mtime_ns != after.st_mtime_ns
        or after.st_nlink != 1
    ):
        raise ValueError("selected source file grew, shrank or changed identity")
    return blob


def _storage_guard(root: Path, new_bytes: int) -> None:
    with (root / "configs" / "base.toml").open("rb") as stream:
        base = tomllib.load(stream)
    floor = base["storage"]["minimum_free_gb"]
    if type(floor) not in (int, float) or not math.isfinite(floor) or floor < 0:
        raise ValueError("invalid project disk floor")
    if shutil.disk_usage(root).free - new_bytes < floor * 1024**3:
        raise RuntimeError("selected source publication would cross the project disk floor")


def _state(model: nn.Module) -> tuple[dict[str, torch.Tensor], dict[str, Any], str]:
    if not isinstance(model, nn.Module):
        raise ValueError("a caller-owned PyTorch source model is required")
    before = state_digest(model)
    tensors: dict[str, torch.Tensor] = {}
    schema: dict[str, Any] = {}
    for name, value in sorted(model.state_dict().items()):
        if not isinstance(value, torch.Tensor) or not bool(torch.isfinite(value).all()):
            raise ValueError("selected source contains a non-tensor or nonfinite state")
        tensors[name] = value.detach().cpu().contiguous().clone()
        schema[name] = {"shape": list(value.shape), "dtype": str(value.dtype)}
    if (
        not tensors
        or before != _tensor_state_digest(tensors)
        or before != state_digest(model)
    ):
        raise ValueError("selected source has no stable tensor state")
    return tensors, schema, before


def _tensor_state_digest(tensors: Mapping[str, torch.Tensor]) -> str:
    """Use the exact state_digest byte protocol without mutating a target model."""
    digest = hashlib.sha256()
    for name, value in sorted(tensors.items()):
        digest.update(name.encode())
        digest.update(str((tuple(value.shape), value.dtype)).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _tensor_bytes(value: torch.Tensor) -> bytes:
    return value.detach().cpu().contiguous().numpy().tobytes()


def _sparse_mask(
    record: Mapping[str, Any], model: nn.Module, recipe: Mapping[str, Any],
) -> tuple[str, tuple[str, ...], str, str]:
    """Bind the live parameter mask to the completed final fit and Cho method."""
    payload = _mapping(record.get("payload"), "selection evidence payload")
    contract = _mapping(payload.get("contract"), "source selection contract")
    method = contract.get("method")
    if (
        method not in {"labram_linear", "labram_lora"}
        or payload.get("purpose") != "bounded_labram_source_selection"
        or contract.get("dataset") != "cho2017"
        or recipe.get("method") != method
        or recipe.get("dataset") != "cho2017"
    ):
        raise ValueError("sparse selected source is limited to Cho linear and LoRA")
    final_fit = _mapping(payload.get("final_source_fit"), "selected final source fit")
    mask = _mapping(final_fit.get("mask"), "selected final source trainable mask")
    names = mask.get("trainable_names")
    if (
        mask.get("method") != method.removeprefix("labram_")
        or not isinstance(names, list)
        or not names
        or any(not isinstance(name, str) or not name for name in names)
        or len(set(names)) != len(names)
    ):
        raise ValueError("selected final source trainable mask differs")
    live = tuple(name for name, parameter in model.named_parameters() if parameter.requires_grad)
    all_parameters = dict(model.named_parameters())
    if (
        tuple(names) != live
        or not set(live).issubset(model.state_dict())
        or type(mask.get("trainable_parameters")) is not int
        or mask["trainable_parameters"]
        != sum(all_parameters[name].numel() for name in live)
    ):
        raise ValueError("selected final source trainable names differ from live mask")
    roster = contract.get("candidates")
    if not isinstance(roster, list):
        raise ValueError("selected source candidate roster differs")
    selected = [
        row for row in roster if isinstance(row, Mapping)
        and row.get("name") == payload.get("selected_candidate")
    ]
    if len(selected) != 1:
        raise ValueError("selected source candidate roster differs")
    source_settings = _mapping(selected[0].get("source"), "selected source settings")
    if method == "labram_linear":
        if (
            source_settings.get("method") != "linear"
            or type(mask.get("depth")) is not int
            or mask["depth"] != 0
            or mask.get("selected_blocks") != []
            or mask.get("head_policy") != "existing_head_always_trainable"
            or mask.get("support_normalization_policy")
            != "all_modules_eval_affine_follows_parameter_mask"
            or any(not name.startswith("head.") for name in live)
        ):
            raise ValueError("linear final source mask policy differs")
    elif (
        not isinstance(source_settings.get("target_modules"), list)
        or not source_settings["target_modules"]
        or any(not isinstance(name, str) or not name for name in source_settings["target_modules"])
        or len(set(source_settings["target_modules"])) != len(source_settings["target_modules"])
        or type(source_settings.get("rank")) is not int
        or source_settings["rank"] < 1
        or type(source_settings.get("alpha")) not in (int, float)
        or not math.isfinite(source_settings["alpha"])
        or source_settings["alpha"] <= 0
        or type(source_settings.get("train_head")) is not bool
        or mask.get("target_modules") != source_settings.get("target_modules")
        or mask.get("rank") != source_settings.get("rank")
        or mask.get("alpha") != source_settings.get("alpha")
        or mask.get("train_head") is not source_settings.get("train_head")
        or mask.get("support_normalization_policy")
        != "all_modules_eval_source_affine_and_buffers_frozen"
        or type(mask.get("adapter_parameters")) is not int
        or not 0 < mask["adapter_parameters"] <= mask["trainable_parameters"]
    ):
        raise ValueError("LoRA final source mask policy differs")
    initial_sha = _digest(final_fit.get("initial_state_sha256"), "initial source state")
    return method, live, initial_sha, config_digest(mask)


def _independent_initial(fitted: nn.Module, initial: nn.Module) -> None:
    """Reject a caller reusing the fitted object or any of its tensor storage."""
    if initial is fitted or type(initial) is not type(fitted):
        raise ValueError("an independently reconstructed initial model is required")
    fitted_storage = {
        (tensor.device, tensor.untyped_storage().data_ptr())
        for tensor in fitted.state_dict().values() if tensor.numel()
    }
    if any(
        tensor.numel()
        and (tensor.device, tensor.untyped_storage().data_ptr()) in fitted_storage
        for tensor in initial.state_dict().values()
    ):
        raise ValueError("initial model shares storage with the fitted model")


def _selection(
    record: Mapping[str, Any], *, evidence_sha256: str, model_sha256: str,
    protocol_sha256: str, source: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any]]:
    payload = _mapping(record.get("payload"), "selection evidence payload")
    if (
        not verify_envelope(record, kind="engineering_smoke", expected_payload=payload)
        or record.get("sha256") != evidence_sha256
        or payload.get("purpose") not in _PURPOSES
        or payload.get("complete") is not True
        or payload.get("outer_target_predictions_performed") is not False
    ):
        raise ValueError("complete canonical source selection evidence is required")
    contract = _mapping(payload.get("contract"), "source selection contract")
    winner = payload.get("selected_candidate")
    final_fit = _mapping(payload.get("final_source_fit"), "selected final source fit")
    roster = contract.get("candidates")
    if (
        not isinstance(winner, str) or not winner
        or not isinstance(roster, list) or not roster
        or any(not isinstance(row, dict) or not isinstance(row.get("name"), str)
               for row in roster)
        or len({row["name"] for row in roster}) != len(roster)
        or winner not in {row["name"] for row in roster}
        or payload.get("contract_sha256") != config_digest(contract)
        or contract.get("protocol_sha256") != protocol_sha256
        or contract.get("source") != source
        or final_fit.get("candidate") != winner
        or final_fit.get("fitted_state_sha256") != model_sha256
        or final_fit.get("candidate_sha256")
        != config_digest(next(row for row in roster if row["name"] == winner))
    ):
        raise ValueError("selected source evidence differs from model, source or protocol")
    return winner, contract


class SelectedSourceStore:
    """Content-addressed selected weights, evidence and completion manifests."""

    def __init__(self, root: Path, directory: Path | None = None) -> None:
        self.root = root.resolve()
        allowed = self.root / "runs" / "phase2"
        raw = directory if directory is not None else allowed / "selected_sources"
        path = raw if raw.is_absolute() else self.root / raw
        self.output = path.absolute()
        if self.output.resolve() != self.output or not self.output.is_relative_to(allowed):
            raise ValueError("selected source output must be a direct Phase II directory")
        if self.output == allowed:
            raise ValueError("selected sources require a dedicated Phase II directory")

    def _directories(self, *, create: bool) -> tuple[Path, Path, Path]:
        if create:
            self.output.mkdir(parents=True, exist_ok=True)
        if not self.output.is_dir() or self.output.resolve() != self.output:
            raise ValueError("selected source output identity changed")
        paths = (
            self.output / "weights", self.output / "evidence", self.output / "manifests",
        )
        for directory in paths:
            if create:
                directory.mkdir(exist_ok=True)
            if not directory.is_dir() or directory.resolve() != directory or directory.is_symlink():
                raise ValueError("selected source subdirectory aliases another path")
        return paths

    def preflight_full_weights(
        self, manifest_sha256: str, *, maximum_bytes: int,
    ) -> SelectedWeightsPreflight:
        """Inspect a pinned full-state file before constructing the caller model.

        Restore repeats the bounded read on the opened handle. The caller may
        compare this identity again after restore to detect file replacement.
        """
        _digest(manifest_sha256, "selected source manifest")
        if (
            type(maximum_bytes) is not int
            or not 0 < maximum_bytes <= _MAXIMUM_CHO_WEIGHTS_BYTES
        ):
            raise ValueError("selected weights preflight byte limit differs")
        weights_dir, _, manifest_dir = self._directories(create=False)
        manifest_path = manifest_dir / f"{manifest_sha256}.json"
        raw = _read_file(
            manifest_path, manifest_dir, maximum_bytes=_MAXIMUM_MANIFEST_BYTES,
        )
        manifest = json.loads(raw)
        payload = _mapping(manifest.get("payload"), "selected source manifest payload")
        if (
            raw != _json_bytes(manifest)
            or not verify_envelope(manifest, kind="engineering_smoke", expected_payload=payload)
            or manifest.get("sha256") != manifest_sha256
            or payload.get("purpose") != _STORE_PURPOSE
            or payload.get("source") != asdict(capture_source(self.root))
        ):
            raise ValueError("selected source manifest differs before weights preflight")
        if payload.get("weights_format", _FULL_FORMAT) != _FULL_FORMAT:
            raise ValueError("Cho selected source requires full_v1 weights")
        weights_sha = _digest(payload.get("weights_sha256"), "selected weights")
        if payload.get("weights_file") != f"weights/{weights_sha}.safetensors":
            raise ValueError("selected source weights path differs")
        weights_path = weights_dir / f"{weights_sha}.safetensors"
        _path(weights_path, weights_dir)
        if not weights_path.is_file():
            raise ValueError("selected source weights file is absent")
        observed = weights_path.stat()
        if (
            not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1
            or not 0 < observed.st_size <= maximum_bytes
        ):
            raise ValueError("selected source weights exceed byte limit or alias")
        return SelectedWeightsPreflight(
            weights_path, weights_sha,
            (observed.st_dev, observed.st_ino, observed.st_size, observed.st_mtime_ns),
        )

    @contextmanager
    def _publication_lock(self) -> Iterator[None]:
        """Serialize all selected-source disk admission on the project volume."""
        self._directories(create=True)
        parent = self.root / "runs" / "phase2"
        if not parent.is_dir() or parent.is_symlink() or parent.resolve() != parent:
            raise ValueError("selected source publication lock parent aliases another path")
        path = parent / ".selected-source-publication.lock"
        _path(path, parent)
        if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
            raise ValueError("selected source publication lock aliases another path")
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "r+b") as handle:
            _path(path, parent)
            opened = os.fstat(handle.fileno())
            if (
                not path.is_file()
                or not os.path.samestat(opened, path.stat())
                or opened.st_nlink != 1
                or opened.st_size not in (0, 1)
            ):
                raise ValueError("selected source publication lock identity changed")
            if opened.st_size == 0:
                handle.write(b"0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            deadline = time.monotonic() + 120.0
            while True:
                try:
                    if sys.platform == "win32":
                        import msvcrt

                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as error:
                    if error.errno not in {errno.EACCES, errno.EAGAIN}:
                        raise
                    if time.monotonic() >= deadline:
                        raise TimeoutError("selected source publication lock is busy") from error
                    time.sleep(0.05)
            try:
                _path(path, parent)
                if not os.path.samestat(os.fstat(handle.fileno()), path.stat()):
                    raise ValueError("selected source publication lock identity changed")
                handle.seek(0)
                if handle.read(1) != b"0":
                    raise ValueError("selected source publication lock bytes differ")
                yield
            finally:
                handle.seek(0)
                if sys.platform == "win32":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _evidence_location(
        payload: Mapping[str, Any], evidence_dir: Path, expected_sha256: str,
    ) -> tuple[Path, SelectedEvidenceFormat]:
        weights_format = payload.get("weights_format", _FULL_FORMAT)
        if weights_format not in {_FULL_FORMAT, _SPARSE_FORMAT}:
            raise ValueError("selected source weights format differs")
        if "evidence_format" not in payload:
            name = f"{expected_sha256}.json"
            format_name: SelectedEvidenceFormat = _CANONICAL_EVIDENCE_FORMAT
        elif payload.get("evidence_format") == _FACTORED_EVIDENCE_FORMAT:
            physical_sha = _digest(
                payload.get("evidence_physical_sha256"), "physical selected evidence",
            )
            if payload.get("evidence_schema") != FACTORED_EVIDENCE_SCHEMA:
                raise ValueError("factored selected evidence schema differs")
            size = payload.get("evidence_physical_bytes")
            if type(size) is not int or not 0 < size <= MAXIMUM_PACKED_BYTES:
                raise ValueError("factored selected evidence byte count differs")
            name = f"{physical_sha}.factored.json"
            format_name = _FACTORED_EVIDENCE_FORMAT
        else:
            raise ValueError("selected evidence format is unsupported")
        fields = _BASE_MANIFEST_FIELDS
        if weights_format == _SPARSE_FORMAT:
            fields |= _SPARSE_MANIFEST_FIELDS
        if format_name == _FACTORED_EVIDENCE_FORMAT:
            fields |= _FACTORED_MANIFEST_FIELDS
        if set(payload) != fields:
            raise ValueError("selected source manifest fields differ from its format")
        if payload.get("evidence_file") != f"evidence/{name}":
            raise ValueError("selected evidence manifest path differs")
        path = evidence_dir / name
        if format_name == _FACTORED_EVIDENCE_FORMAT:
            _path(path, evidence_dir)
            if not path.is_file() or path.stat().st_size != size:
                raise ValueError("factored selected evidence byte count differs")
        return path, format_name

    def read_persisted_evidence(
        self, path: Path, *, expected_evidence_sha256: str,
    ) -> dict[str, Any]:
        """Read one physical evidence file under this store with its logical pin."""
        _digest(expected_evidence_sha256, "expected selection evidence")
        _, evidence_dir, _ = self._directories(create=False)
        if not isinstance(path, Path):
            raise ValueError("selected evidence path must be a Path")
        _path(path, evidence_dir)
        if not path.is_file() or path.stat().st_nlink != 1:
            raise ValueError("selected evidence path aliases or is absent")
        if path.name == f"{expected_evidence_sha256}.json":
            raw = _read_file(
                path, evidence_dir, maximum_bytes=MAXIMUM_LOGICAL_BYTES,
            )
            record: dict[str, Any] = json.loads(raw)
            if not isinstance(record, dict):
                raise ValueError("selected evidence must be a canonical envelope")
            payload = _mapping(record.get("payload"), "selection evidence payload")
            if (
                raw != _json_bytes(record)
                or not verify_envelope(record, kind="engineering_smoke", expected_payload=payload)
                or record.get("sha256") != expected_evidence_sha256
            ):
                raise ValueError("canonical selected evidence differs from logical pin")
            return record
        match = re.fullmatch(r"([0-9a-f]{64})\.factored\.json", path.name)
        if match is None:
            raise ValueError("selected evidence path has an unsupported format")
        raw = _read_bounded_factored(path, evidence_dir, match.group(1))
        return unpack_factored_selection(
            raw, expected_evidence_sha256=expected_evidence_sha256,
        )

    def read_persisted_evidence_for_manifest(
        self, manifest_sha256: str, expected_evidence_sha256: str,
    ) -> tuple[dict[str, Any], Path]:
        """Resolve a physical evidence path only through its pinned manifest."""
        _digest(manifest_sha256, "selected source manifest")
        _digest(expected_evidence_sha256, "expected selection evidence")
        _, evidence_dir, manifest_dir = self._directories(create=False)
        manifest_path = manifest_dir / f"{manifest_sha256}.json"
        if not manifest_path.is_file() or manifest_path.stat().st_nlink != 1:
            raise ValueError("selected source manifest path aliases or is absent")
        raw = _read_file(
            manifest_path, manifest_dir, maximum_bytes=_MAXIMUM_MANIFEST_BYTES,
        )
        manifest: dict[str, Any] = json.loads(raw)
        if not isinstance(manifest, dict):
            raise ValueError("selected source manifest must be a canonical envelope")
        payload = _mapping(manifest.get("payload"), "selected source manifest payload")
        if (
            raw != _json_bytes(manifest)
            or not verify_envelope(manifest, kind="engineering_smoke", expected_payload=payload)
            or manifest.get("sha256") != manifest_sha256
            or payload.get("purpose") != _STORE_PURPOSE
            or payload.get("scope") != "engineering_only"
            or payload.get("scientific_evaluation") is not False
            or payload.get("evidence_sha256") != expected_evidence_sha256
            or payload.get("source") != asdict(capture_source(self.root))
        ):
            raise ValueError("selected source manifest differs from expected evidence context")
        evidence_path, _ = self._evidence_location(
            payload, evidence_dir, expected_evidence_sha256,
        )
        return self.read_persisted_evidence(
            evidence_path, expected_evidence_sha256=expected_evidence_sha256,
        ), evidence_path

    def publish(
        self,
        model: nn.Module,
        evidence_record: Mapping[str, Any],
        *,
        evidence_sha256: str,
        protocol_config: Mapping[str, Any],
        model_recipe: Mapping[str, Any],
        weights_format: SelectedWeightsFormat = _FULL_FORMAT,
        initial_model: nn.Module | None = None,
        evidence_format: SelectedEvidenceFormat = _CANONICAL_EVIDENCE_FORMAT,
    ) -> SelectedSourcePublication:
        """Persist a completed selected source; the manifest is the last write."""
        _digest(evidence_sha256, "selection evidence")
        config = config_snapshot(protocol_config)
        recipe = config_snapshot(model_recipe)
        if not recipe:
            raise ValueError("explicit model architecture recipe is required")
        source = asdict(capture_source(self.root))
        tensors, schema, model_sha = _state(model)
        winner, contract = _selection(
            evidence_record, evidence_sha256=evidence_sha256,
            model_sha256=model_sha, protocol_sha256=config_digest(config), source=source,
        )
        sparse_fields: dict[str, Any] = {}
        expected_initial_sha: str | None = None
        stored = tensors
        if weights_format == _SPARSE_FORMAT:
            if initial_model is None:
                raise ValueError("sparse selected source requires a reconstructed initial model")
            _independent_initial(model, initial_model)
            _, names, expected_initial_sha, mask_sha = _sparse_mask(
                evidence_record, model, recipe,
            )
            _, initial_names, _, _ = _sparse_mask(evidence_record, initial_model, recipe)
            if initial_names != names:
                raise ValueError("initial and fitted model trainable masks differ")
            initial_tensors, initial_schema, initial_sha = _state(initial_model)
            if initial_sha != expected_initial_sha or initial_schema != schema:
                raise ValueError("reconstructed initial model differs from final source fit")
            if any(
                _tensor_bytes(tensor) != _tensor_bytes(initial_tensors[name])
                for name, tensor in tensors.items() if name not in names
            ):
                raise ValueError("selected source changed a frozen tensor or buffer")
            stored = {name: tensors[name] for name in names}
            sparse_fields = {
                "weights_format": _SPARSE_FORMAT,
                "initial_state_sha256": initial_sha,
                "final_fit_mask_sha256": mask_sha,
                "trainable_parameter_names": list(names),
                "stored_tensor_names": sorted(stored),
                "omitted_tensor_names": sorted(set(tensors) - set(stored)),
            }
        elif weights_format != _FULL_FORMAT or initial_model is not None:
            raise ValueError("selected source weights format or initial model differs")
        try:
            blob = save(stored)
        except (RuntimeError, ValueError) as error:
            raise ValueError("selected source tensor state cannot be stored safely") from error
        decoded = load(blob)
        if set(decoded) != set(stored) or any(
            _tensor_bytes(decoded[name]) != _tensor_bytes(tensor)
            for name, tensor in stored.items()
        ):
            raise ValueError("selected source safetensors round trip differs")
        weights_sha = hashlib.sha256(blob).hexdigest()
        evidence_fields: dict[str, Any] = {}
        if evidence_format == _CANONICAL_EVIDENCE_FORMAT:
            evidence_bytes = _json_bytes(evidence_record)
            evidence_name = f"{evidence_sha256}.json"
        elif evidence_format == _FACTORED_EVIDENCE_FORMAT:
            evidence_bytes = pack_factored_selection(evidence_record)
            physical_sha = hashlib.sha256(evidence_bytes).hexdigest()
            evidence_name = f"{physical_sha}.factored.json"
            evidence_fields = {
                "evidence_format": _FACTORED_EVIDENCE_FORMAT,
                "evidence_schema": FACTORED_EVIDENCE_SCHEMA,
                "evidence_physical_sha256": physical_sha,
                "evidence_physical_bytes": len(evidence_bytes),
            }
        else:
            raise ValueError("selected evidence format is unsupported")
        physical_sha = hashlib.sha256(evidence_bytes).hexdigest()
        payload = {
            "purpose": _STORE_PURPOSE,
            "scope": "engineering_only",
            "scientific_evaluation": False,
            "evidence_sha256": evidence_sha256,
            "selected_candidate": winner,
            "selection_contract_sha256": config_digest(contract),
            "protocol_config_sha256": config_digest(config),
            "source": source,
            "model_class": f"{type(model).__module__}.{type(model).__qualname__}",
            "model_recipe": recipe,
            "model_recipe_sha256": config_digest(recipe),
            "model_state_sha256": model_sha,
            "tensor_schema": schema,
            "weights_sha256": weights_sha,
            "weights_file": f"weights/{weights_sha}.safetensors",
            "evidence_file": f"evidence/{evidence_name}",
            **sparse_fields,
            **evidence_fields,
        }
        manifest = envelope("engineering_smoke", payload)
        manifest_sha = manifest["sha256"]
        manifest_bytes = _json_bytes(manifest)
        if (
            state_digest(model) != model_sha
            or asdict(capture_source(self.root)) != source
            or (initial_model is not None and state_digest(initial_model) != expected_initial_sha)
        ):
            raise ValueError("selected source model or source changed before publication")
        with self._publication_lock():
            weights_dir, evidence_dir, manifest_dir = self._directories(create=False)
            weights_path = weights_dir / f"{weights_sha}.safetensors"
            evidence_path = evidence_dir / evidence_name
            manifest_path = manifest_dir / f"{manifest_sha}.json"
            pending = sum(
                size for path, parent, sha, size in (
                    (weights_path, weights_dir, weights_sha, len(blob)),
                    (evidence_path, evidence_dir, physical_sha, len(evidence_bytes)),
                    (manifest_path, manifest_dir,
                     hashlib.sha256(manifest_bytes).hexdigest(), len(manifest_bytes)),
                ) if not _existing_exact(path, parent, sha, size)
            )
            if pending:
                _storage_guard(self.root, pending)
            resumed = manifest_path.exists()
            _write_blob(weights_path, weights_dir, blob, weights_sha)
            if evidence_format == _CANONICAL_EVIDENCE_FORMAT:
                write_once(evidence_path, evidence_record, output_root=self.output)
            else:
                _write_blob(evidence_path, evidence_dir, evidence_bytes, physical_sha)
            if self.read_persisted_evidence(
                evidence_path, expected_evidence_sha256=evidence_sha256,
            ) != evidence_record:
                raise ValueError("persisted selected evidence differs before manifest publication")
            if (
                asdict(capture_source(self.root)) != source
                or state_digest(model) != model_sha
                or (
                    initial_model is not None
                    and state_digest(initial_model) != expected_initial_sha
                )
            ):
                raise ValueError("selected source context changed before manifest publication")
            if _file_sha256(weights_path) != weights_sha:
                raise ValueError("persisted selected source weights differ")
            write_once(manifest_path, manifest, output_root=self.output)
            return SelectedSourcePublication(
                manifest_sha, evidence_sha256, winner, model_sha, weights_sha,
                manifest_path, evidence_path, weights_path, resumed, weights_format,
                evidence_format,
            )

    def restore(
        self,
        manifest_sha256: str,
        model: nn.Module,
        *,
        expected_evidence_sha256: str,
        protocol_config: Mapping[str, Any],
        model_recipe: Mapping[str, Any],
        maximum_weights_bytes: int = _MAXIMUM_GENERIC_WEIGHTS_BYTES,
    ) -> RestoredSelectedSource:
        """Verify every pinned byte and tensor schema before loading a fresh model."""
        _digest(manifest_sha256, "selected source manifest")
        _digest(expected_evidence_sha256, "expected selection evidence")
        if (
            type(maximum_weights_bytes) is not int
            or not 0 < maximum_weights_bytes <= _MAXIMUM_GENERIC_WEIGHTS_BYTES
        ):
            raise ValueError("selected weights byte limit differs")
        config = config_snapshot(protocol_config)
        recipe = config_snapshot(model_recipe)
        source = asdict(capture_source(self.root))
        weights_dir, evidence_dir, manifest_dir = self._directories(create=False)
        manifest_path = manifest_dir / f"{manifest_sha256}.json"
        raw_manifest = _read_file(
            manifest_path, manifest_dir, maximum_bytes=_MAXIMUM_MANIFEST_BYTES,
        )
        manifest = json.loads(raw_manifest)
        payload = _mapping(manifest.get("payload"), "selected source manifest payload")
        if (
            not verify_envelope(manifest, kind="engineering_smoke", expected_payload=payload)
            or manifest.get("sha256") != manifest_sha256
            or raw_manifest != _json_bytes(manifest)
            or payload.get("purpose") != _STORE_PURPOSE
            or payload.get("scope") != "engineering_only"
            or payload.get("scientific_evaluation") is not False
            or payload.get("evidence_sha256") != expected_evidence_sha256
            or payload.get("protocol_config_sha256") != config_digest(config)
            or payload.get("source") != source
            or payload.get("model_recipe") != recipe
            or payload.get("model_recipe_sha256") != config_digest(recipe)
            or payload.get("model_class")
            != f"{type(model).__module__}.{type(model).__qualname__}"
        ):
            raise ValueError("selected source manifest differs from expected context")
        weights_format = payload.get("weights_format", _FULL_FORMAT)
        if weights_format not in {_FULL_FORMAT, _SPARSE_FORMAT}:
            raise ValueError("selected source weights format differs")
        weights_sha = _digest(payload.get("weights_sha256"), "selected weights")
        model_sha = _digest(payload.get("model_state_sha256"), "selected model state")
        if payload.get("weights_file") != f"weights/{weights_sha}.safetensors":
            raise ValueError("selected source manifest file names differ")
        evidence_path, evidence_format = self._evidence_location(
            payload, evidence_dir, expected_evidence_sha256,
        )
        evidence = self.read_persisted_evidence(
            evidence_path, expected_evidence_sha256=expected_evidence_sha256,
        )
        winner, contract = _selection(
            evidence, evidence_sha256=expected_evidence_sha256,
            model_sha256=model_sha, protocol_sha256=config_digest(config), source=source,
        )
        if (
            payload.get("selected_candidate") != winner
            or payload.get("selection_contract_sha256") != config_digest(contract)
        ):
            raise ValueError("selected source manifest differs from evidence winner")
        weights_path = weights_dir / f"{weights_sha}.safetensors"
        tensor_blob = _read_exact(
            weights_path, weights_dir, weights_sha,
            maximum_bytes=maximum_weights_bytes,
        )
        try:
            tensors = load(tensor_blob)
        except (RuntimeError, ValueError) as error:
            raise ValueError("selected source safetensors bytes are invalid") from error
        expected = model.state_dict()
        schema = _mapping(payload.get("tensor_schema"), "selected source tensor schema")
        if set(schema) != set(expected):
            raise ValueError("selected source tensor names differ from caller architecture")
        if weights_format == _SPARSE_FORMAT:
            _, names, evidence_initial_sha, mask_sha = _sparse_mask(evidence, model, recipe)
            initial_sha = _digest(payload.get("initial_state_sha256"), "initial source state")
            initial_tensors, initial_schema, caller_initial_sha = _state(model)
            if (
                initial_sha != evidence_initial_sha
                or caller_initial_sha != initial_sha
                or payload.get("final_fit_mask_sha256") != mask_sha
                or payload.get("trainable_parameter_names") != list(names)
                or payload.get("stored_tensor_names") != sorted(names)
                or payload.get("omitted_tensor_names") != sorted(set(expected) - set(names))
                or initial_schema != schema
                or set(tensors) != set(names)
            ):
                raise ValueError("sparse selected source initialization or mask differs")
        elif set(tensors) != set(expected):
            raise ValueError("selected source tensor names differ from caller architecture")
        for name, tensor in tensors.items():
            declared = _mapping(schema[name], "selected tensor declaration")
            if (
                list(tensor.shape) != declared.get("shape")
                or str(tensor.dtype) != declared.get("dtype")
                or tensor.shape != expected[name].shape
                or tensor.dtype != expected[name].dtype
                or not bool(torch.isfinite(tensor).all())
            ):
                raise ValueError("selected source tensor schema differs from caller architecture")
        if weights_format == _SPARSE_FORMAT:
            complete = dict(initial_tensors)
            complete.update(tensors)
            if _tensor_state_digest(complete) != model_sha:
                raise ValueError("sparse selected source complete tensor digest differs")
        elif _tensor_state_digest(tensors) != model_sha:
            raise ValueError("selected source tensor bytes differ from the model digest")
        if asdict(capture_source(self.root)) != source:
            raise ValueError("selected source context changed before model restore")
        if weights_format == _SPARSE_FORMAT:
            if state_digest(model) != initial_sha:
                raise ValueError("sparse selected source initial model changed before restore")
            try:
                model.load_state_dict(complete, strict=True)
                if state_digest(model) != model_sha:
                    raise ValueError("restored selected source model digest differs")
                if asdict(capture_source(self.root)) != source:
                    raise ValueError("selected source context changed during model restore")
            except Exception:
                model.load_state_dict(initial_tensors, strict=True)
                raise
        else:
            model.load_state_dict(tensors, strict=True)
            if state_digest(model) != model_sha:
                raise ValueError("restored selected source model digest differs")
        publication = SelectedSourcePublication(
            manifest_sha256, expected_evidence_sha256, winner, model_sha, weights_sha,
            manifest_path, evidence_path, weights_path, True, weights_format,
            evidence_format,
        )
        return RestoredSelectedSource(model, evidence, publication)
