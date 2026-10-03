"""Immutable, replay-verified TCPL engineering predictions and safe checkpoints.

This publisher only emits engineering_smoke records, never scientific evaluation
cells. Checkpoint training history and a caller-reported seed remain unverified.
"""

from __future__ import annotations

import copy
import hashlib
import os
import platform
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path, PurePath, PureWindowsPath
from typing import Any

import numpy as np
import safetensors
import torch
from safetensors.torch import load, save

from adaptation.tcpl_episodic import TCPLTargetSession
from adaptation.tcpl_manifest import TCPLManifestRunner
from core.config import config_digest, load_toml
from core.provenance import capture_source
from encoder.tcpl import TCPLClassifier
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import envelope, write_once
from scripts.audit_phase2_protocol import file_digest


def _checkpoint_bytes(model: TCPLClassifier) -> bytes:
    tensors = {}
    for name, value in sorted(model.state_dict().items()):
        if value.device.type != "cpu" or value.dtype not in (torch.float32, torch.float64):
            raise ValueError("engineering publication supports CPU float32/float64 checkpoints")
        if not torch.isfinite(value).all():
            raise ValueError("checkpoint contains nonfinite tensors")
        tensors[name] = value.detach().contiguous().clone()
    return save(tensors)


def _environment() -> dict[str, Any]:
    return {
        "python": platform.python_version(), "platform": platform.platform(),
        "machine": platform.machine(), "torch": torch.__version__, "numpy": np.__version__,
        "safetensors": safetensors.__version__, "device": "cpu",
        "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads(),
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "mkldnn_enabled": torch.backends.mkldnn.enabled,
        "mha_fastpath": torch.backends.mha.get_fastpath_enabled(),
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
    }


def _path_identity(path: Path) -> PurePath:
    """Compare resolved Windows paths in one namespace, retaining physical paths.

    Concurrent directory creation can make realpath return either D:\\... or
    the equivalent extended-length spelling. Normalize comparisons only; do not
    remove the extended prefix from paths used for filesystem operations.
    """
    if os.name != "nt":
        return path
    value = str(path)
    if not value.startswith("\\\\?\\"):
        value = "\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value
    return PureWindowsPath(value)


def _write_checkpoint(path: Path, content: bytes, root: Path) -> None:
    destination, admitted = path.resolve(), root.resolve()
    dest_id, root_id = _path_identity(destination), _path_identity(admitted)
    if dest_id == root_id or not dest_id.is_relative_to(root_id):
        raise ValueError("checkpoint path escapes the admitted output root")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != content:
            raise FileExistsError("conflicting immutable checkpoint")
        return
    descriptor, temporary = tempfile.mkstemp(prefix=".tcpl-", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if destination.read_bytes() != content:
                raise FileExistsError("conflicting immutable checkpoint") from None
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary)


@dataclass(frozen=True, slots=True)
class TCPLPublication:
    record_path: Path
    checkpoint_path: Path
    run_sha256: str
    checkpoint_sha256: str
    record_sha256: str
    resumed: bool


def publish_tcpl_engineering_prediction(
    runner: TCPLManifestRunner,
    episode_record: Mapping[str, Any],
    *,
    shots_per_class: int,
    query_batch_size: int = 8,
    reported_model_seed: int | None = None,
) -> TCPLPublication:
    """Verify and publish a complete outer-target engineering prediction.

    Uses the manifest runner's pinned context, never caller-supplied predictions.
    Snapshots the owned source to safe tensor bytes, strictly restores those bytes
    into an isolated copy, and predicts from that copy. Repeat calls revalidate
    artifacts and recompute logits before same-byte publication; this is verified
    reuse, not an inference cache. Checkpoint existence alone never marks a run done.

    Private runner fields form a package-internal integration contract. A snapshot
    digest identifies weights, not their prior training subjects or training seed.
    No optimizer state, source-training resume or scientific approval is published.
    """
    if runner._validation_subject is not None:
        raise ValueError("this engineering publisher only accepts final outer-target runners")
    if type(query_batch_size) is not int or query_batch_size < 1:
        raise ValueError("query_batch_size must be a positive integer")
    if reported_model_seed is not None and (
        type(reported_model_seed) is not int or reported_model_seed < 0
    ):
        raise ValueError("reported_model_seed must be a nonnegative integer or None")
    root = runner._root
    output = (root / "runs/phase2/tcpl_engineering_predictions").resolve()
    if not _path_identity(output).is_relative_to(_path_identity(root)):
        raise ValueError("engineering output directory escapes the project")
    source = capture_source(root)
    require_digest(source.source_sha256, "source_sha256")
    if (
        len(source.git_commit) not in (40, 64)
        or any(c not in "0123456789abcdef" for c in source.git_commit)
        or type(source.git_dirty) is not bool
    ):
        raise ValueError("real Git identity and explicit dirty state are required")
    method_path = root / "configs/phase2/tcpl_local_contract.toml"
    method_config = load_toml(method_path)
    method_sha = file_digest(method_path)
    environment = _environment()
    subject = runner._selection.target_subject
    episode = runner._episode(subject, episode_record, shots_per_class)
    catalog = runner._catalogs[subject]
    checkpoint = _checkpoint_bytes(runner._trainer.model)
    checkpoint_sha = hashlib.sha256(checkpoint).hexdigest()
    restored = copy.deepcopy(runner._trainer.model)
    restored.load_state_dict(load(checkpoint), strict=True)
    if _checkpoint_bytes(restored) != checkpoint:
        raise ValueError("checkpoint did not restore exactly")
    session = TCPLTargetSession(restored, episode.support)
    logits = session.predict(episode.queries, query_batch_size=query_batch_size)[0]
    identity = {
        "schema": "tcpl-engineering-prediction-v1", "dataset": catalog.dataset,
        "subject": subject, "role": "outer_target", "shots_per_class": shots_per_class,
        "query_batch_size": query_batch_size, "classes": catalog.classes,
        "channel_names": runner._channels, "dtype": str(logits.dtype),
        "reported_model_seed": reported_model_seed,
        "protocol_sha256": runner.protocol_sha256, "episode_sha256": episode.sha256,
        "selection_sha256": runner._selection.sha256,
        "artifact_sha256": catalog.artifact_sha256,
        "preprocessing_sha256": catalog.preprocessing_sha256,
        "method_config_sha256": method_sha,
        "checkpoint_sha256": checkpoint_sha, "source": asdict(source),
        "environment_sha256": config_digest(environment),
    }
    run_sha = config_digest(identity)
    checkpoint_path = output / "checkpoints" / f"{checkpoint_sha}.safetensors"
    record_path = output / "predictions" / f"{run_sha}.json"
    payload = {
        "record_type": "tcpl_prediction", "scope": "engineering_only",
        "scientific_evaluation": False, "author_parity_verified": False,
        "checkpoint_training_history_verified": False, "model_seed_verified": False,
        "identity": identity, "run_sha256": run_sha,
        "environment": environment, "method_config": method_config,
        "checkpoint_path": _path_identity(checkpoint_path).relative_to(
            _path_identity(root)
        ).as_posix(),
        "support_trial_ids": episode.support_ids, "query_trial_ids": episode.query_ids,
        "logits": logits.tolist(), "targets": episode.targets[0].tolist(),
    }
    record = envelope("engineering_smoke", payload)
    # No writes until source, input and runtime stability have been checked.
    if (
        capture_source(root) != source or _environment() != environment
        or file_digest(method_path) != method_sha
        or _checkpoint_bytes(runner._trainer.model) != checkpoint
        or file_digest(runner._threshold_path) != runner._threshold_sha256
        or file_digest(runner._directory / f"{subject}.npz") != catalog.artifact_sha256
    ):
        raise ValueError("publication context changed during inference")
    existed = record_path.exists()
    _write_checkpoint(checkpoint_path, checkpoint, output)
    # Validate actual persisted checkpoint bytes before creating a completion record.
    if file_digest(checkpoint_path) != checkpoint_sha:
        raise ValueError("persisted checkpoint hash mismatch")
    write_once(record_path, record, output_root=output)
    return TCPLPublication(
        record_path, checkpoint_path, run_sha, checkpoint_sha,
        file_digest(record_path), existed,
    )
