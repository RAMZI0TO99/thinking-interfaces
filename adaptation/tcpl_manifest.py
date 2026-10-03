"""Bind local TCPL tensor helpers to reconstructed Phase II audit identities.

This bounded Profile A integration is not a scientific preprocessing/training
runner. Callers supply trusted catalogs and protocol configuration; saved record
hashes alone are not treated as evidence. No public API accepts arbitrary tensors.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from adaptation.tcpl_episodic import TCPLMetaStep, TCPLSourceTrainer, TCPLTargetSession
from core.config import config_digest, config_snapshot, load_toml
from encoder.tcpl import TCPLClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import verify_envelope
from scripts.audit_phase2_protocol import file_digest, inside, read_catalog, validate_protocol


@dataclass(frozen=True, slots=True)
class TCPLTrainerSettings:
    """Explicit optimizer contract for the owned source trainer; None keeps defaults."""

    learning_rate: float
    weight_decay: float
    prompt_l2_weight: float

    def __post_init__(self) -> None:
        for name in ("learning_rate", "prompt_l2_weight"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"explicit positive finite {name} required")
        if (
            type(self.weight_decay) not in (int, float)
            or not math.isfinite(self.weight_decay)
            or self.weight_decay < 0
        ):
            raise ValueError("explicit finite nonnegative weight_decay required")


@dataclass(frozen=True, slots=True)
class ManifestStep:
    subject: str
    episode_sha256: str
    support_trial_ids: tuple[str, ...]
    query_trial_ids: tuple[str, ...]
    loss: TCPLMetaStep


@dataclass(frozen=True, slots=True)
class ManifestPrediction:
    subject: str
    role: str
    episode_sha256: str
    selection_sha256: str
    classes: tuple[str, ...]
    query_trial_ids: tuple[str, ...]
    logits: torch.Tensor
    targets: torch.Tensor


@dataclass(frozen=True, slots=True)
class _BoundEpisode:
    sha256: str
    support_ids: tuple[str, ...]
    query_ids: tuple[str, ...]
    support: torch.Tensor
    queries: torch.Tensor
    targets: torch.Tensor


class TCPLManifestRunner:
    """One outer target and optional source-only inner-validation fold.

    Reconstruct selection from trusted catalogs before cloning a model. Each call
    reconstructs an episode, verifies its saved envelope, re-audits artifact bytes,
    then maps retained indices back into the original NPZ. Caller-selected trial
    indices, labels, query subsets and preprocessing overrides are not accepted.

    The source template's prior training provenance is trusted input, not inferred
    from weights. Each source call is one subject episode/Adam step, an explicit
    bounded engineering policy, not the paper's 16-episode scientific schedule.
    The optimizer stays at the trainer defaults unless explicit TCPLTrainerSettings
    are supplied, or a caller-owned TCPLSourceTrainer is admitted directly for
    external bounded fits; `source_state_sha256` exposes the owned model's state.
    """

    def __init__(
        self,
        root: Path,
        protocol_config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        source_template: TCPLClassifier,
        *,
        outer_target: str,
        channel_names: tuple[str, ...],
        validation_subject: str | None = None,
        optimizer: TCPLTrainerSettings | None = None,
        source_trainer: TCPLSourceTrainer | None = None,
    ) -> None:
        self._root = root.resolve()
        config: dict[str, Any] = config_snapshot(protocol_config)
        self._shots = validate_protocol(config)
        self.protocol_sha256 = config_digest(config)
        selection = source_selection(catalogs, target=outer_target)
        if not verify_envelope(
            selection_record, kind="source_selection", expected_payload=asdict(selection)
        ):
            raise ValueError("selection record differs from reconstructed catalog cohort")
        settings = config["datasets"][selection.dataset]
        if (
            type(settings["expected_subjects"]) is not int
            or settings["expected_subjects"] != len(catalogs)
            or tuple(settings["classes"]) != catalogs[0].classes
        ):
            raise ValueError("catalog cohort/count/classes differ from the protocol")
        self._directory = inside(self._root, settings["artifact_directory"])
        actual_subjects = tuple(sorted(p.stem for p in self._directory.glob("subject_*.npz")))
        if actual_subjects != tuple(sorted(c.subject for c in catalogs)):
            raise ValueError("artifact directory does not match the complete catalog cohort")
        self._threshold_path = inside(self._root, config["preparation"]["threshold_config"])
        self._threshold_sha256 = file_digest(self._threshold_path)
        thresholds: dict[str, Any] = load_toml(self._threshold_path)
        self._threshold: float = thresholds["datasets"][selection.dataset][
            "artifact_threshold_volts"
        ]
        preprocessing_sha = config_digest({
            "profile_identity": config["preparation"]["profile_identity"],
            "threshold_config_sha256": self._threshold_sha256,
            "dataset": selection.dataset,
            "threshold": self._threshold,
        })
        if any(c.preprocessing_sha256 != preprocessing_sha for c in catalogs):
            raise ValueError("catalog preprocessing differs from the pinned threshold/profile")
        if (
            not channel_names or len(set(channel_names)) != len(channel_names)
            or source_template.input_channels != len(channel_names)
            or source_template.classes != len(catalogs[0].classes)
        ):
            raise ValueError("model dimensions and declared montage/classes must match")
        if validation_subject is not None and validation_subject not in selection.source_subjects:
            raise ValueError("inner validation must be a source subject, never the outer target")
        if optimizer is not None and not isinstance(optimizer, TCPLTrainerSettings):
            raise ValueError("explicit trainer settings must be TCPLTrainerSettings")
        if source_trainer is not None and not isinstance(source_trainer, TCPLSourceTrainer):
            raise ValueError("owned trainer must be a TCPLSourceTrainer")
        if optimizer is not None and source_trainer is not None:
            raise ValueError("pass explicit optimizer settings or an owned trainer, not both")
        if source_trainer is not None and (
            not isinstance(source_trainer.model, TCPLClassifier)
            or any(
                p.device.type != "cpu" or p.dtype != torch.float32
                for p in source_trainer.model.parameters()
            )
            or any(not torch.isfinite(v).all() for v in source_trainer.model.state_dict().values())
        ):
            raise ValueError("owned trainer requires a finite CPU float32 TCPL model")
        self._catalogs = {c.subject: c for c in catalogs}
        self._selection = selection
        self._validation_subject = validation_subject
        self._channels = tuple(channel_names)
        self._training_subjects = tuple(
            s for s in selection.source_subjects if s != validation_subject
        )
        if source_trainer is not None:
            self._trainer = source_trainer
        elif optimizer is None:
            self._trainer = TCPLSourceTrainer(source_template)
        else:
            self._trainer = TCPLSourceTrainer(
                source_template,
                learning_rate=optimizer.learning_rate,
                weight_decay=optimizer.weight_decay,
                prompt_l2_weight=optimizer.prompt_l2_weight,
            )

    @property
    def training_subjects(self) -> tuple[str, ...]:
        return self._training_subjects

    @property
    def source_state_sha256(self) -> str:
        """Digest of the owned trainable model; changes with every source step."""
        return state_digest(self._trainer.model)

    def _episode(
        self, subject: str, record: Mapping[str, Any], shots_per_class: int
    ) -> _BoundEpisode:
        catalog = self._catalogs[subject]
        manifest = nested_episode(
            catalog, shots=self._shots, protocol_sha256=self.protocol_sha256
        )
        if not verify_envelope(
            record, kind="episode_manifest", expected_payload=manifest.payload()
        ):
            raise ValueError("episode record differs from reconstructed trusted partition")
        partition = manifest.partition(shots_per_class)
        path = (self._directory / f"{subject}.npz").resolve()
        if path.parent != self._directory:
            raise ValueError("subject artifact path escapes its directory")
        if file_digest(self._threshold_path) != self._threshold_sha256:
            raise ValueError("threshold configuration changed")
        if file_digest(path) != catalog.artifact_sha256:
            raise ValueError("artifact bytes differ from the pinned catalog")
        actual, metadata = read_catalog(
            path, dataset=catalog.dataset, classes=catalog.classes,
            threshold=self._threshold, preprocessing_sha256=catalog.preprocessing_sha256,
        )
        if actual != catalog or tuple(metadata["channel_names"]) != self._channels:
            raise ValueError("artifact trial identities/labels/montage differ from the catalog")
        retained = np.asarray(metadata["retained_artifact_indices"], dtype=np.int64)
        with np.load(path, allow_pickle=False) as data:
            signals = np.asarray(data["signals"])
            support_array = signals[retained[list(partition.support_indices)]].copy()
            query_array = signals[retained[list(partition.query_indices)]].copy()
        if file_digest(path) != catalog.artifact_sha256:
            raise ValueError("artifact changed while binding tensors")
        if file_digest(self._threshold_path) != self._threshold_sha256:
            raise ValueError("threshold configuration changed while binding tensors")
        parameter = next(self._trainer.model.parameters())
        support = torch.as_tensor(
            support_array, device=parameter.device, dtype=parameter.dtype
        )[None]
        queries = torch.as_tensor(query_array, device=parameter.device, dtype=parameter.dtype)[None]
        targets = torch.tensor([
            catalog.classes.index(catalog.labels[i]) for i in partition.query_indices
        ], dtype=torch.long, device=parameter.device)[None]
        return _BoundEpisode(
            manifest.sha256,
            tuple(catalog.trial_ids[i] for i in partition.support_indices),
            tuple(catalog.trial_ids[i] for i in partition.query_indices),
            support, queries, targets,
        )

    def source_step(
        self, subject: str, episode_record: Mapping[str, Any], *, shots_per_class: int
    ) -> ManifestStep:
        if subject not in self.training_subjects:
            raise ValueError("subject is not admitted for source training in this fold")
        episode = self._episode(subject, episode_record, shots_per_class)
        loss = self._trainer.step(episode.support, episode.queries, episode.targets)
        return ManifestStep(subject, episode.sha256, episode.support_ids, episode.query_ids, loss)

    def _predict(
        self, subject: str, role: str, record: Mapping[str, Any], shots: int, batch_size: int
    ) -> ManifestPrediction:
        if type(batch_size) is not int or batch_size < 1:
            raise ValueError("query_batch_size must be a positive integer")
        episode = self._episode(subject, record, shots)
        session = TCPLTargetSession(self._trainer.model, episode.support)
        logits = session.predict(episode.queries, query_batch_size=batch_size)[0]
        # Query labels are returned for later scoring, never passed to target inference.
        return ManifestPrediction(
            subject, role, episode.sha256, self._selection.sha256,
            self._catalogs[subject].classes, episode.query_ids, logits, episode.targets[0].clone(),
        )

    def predict_target(
        self, episode_record: Mapping[str, Any], *, shots_per_class: int, query_batch_size: int = 8
    ) -> ManifestPrediction:
        if self._validation_subject is not None:
            raise ValueError("outer-target prediction is unavailable during inner validation")
        return self._predict(
            self._selection.target_subject, "outer_target", episode_record,
            shots_per_class, query_batch_size,
        )

    def predict_validation(
        self, episode_record: Mapping[str, Any], *, shots_per_class: int, query_batch_size: int = 8
    ) -> ManifestPrediction:
        if self._validation_subject is None:
            raise ValueError("this runner has no inner-validation subject")
        return self._predict(
            self._validation_subject, "inner_validation", episode_record,
            shots_per_class, query_batch_size,
        )
