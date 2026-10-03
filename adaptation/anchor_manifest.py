"""Audited BCI Profile A anchors with matched Phase II partitions; engineering only."""

from __future__ import annotations

import copy
import hashlib
import math
import pickle
import warnings
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from sklearn.exceptions import ConvergenceWarning  # type: ignore[import-untyped]
from torch import nn

from core.config import config_digest, config_snapshot
from evaluation.alignment import EuclideanAlignment
from evaluation.baselines import TangentSpaceLogistic
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_profile_a import load_cho_profile_a_subject
from evaluation.phase2_profile_binding import (
    BCI_CHANNELS,
    BCIProfileASubject,
    dataset_cohort,
    load_bci_profile_a_subject,
)
from evaluation.phase2_protocol import (
    TrialCatalog,
    nested_episode,
    require_digest,
    source_selection,
)
from evaluation.phase2_records import verify_envelope
from scripts.audit_phase2_protocol import inside, validate_protocol


def _positive(value: float) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value > 0


@dataclass(frozen=True, slots=True)
class EEGNetAnchorSettings:
    steps: int
    learning_rate: float
    input_scale: float
    query_batch_size: int = 8

    def __post_init__(self) -> None:
        if (
            type(self.steps) is not int
            or self.steps < 1
            or not _positive(self.learning_rate)
            or not _positive(self.input_scale)
            or type(self.query_batch_size) is not int
            or self.query_batch_size < 1
        ):
            raise ValueError("explicit positive EEGNet steps, rate, scale and batch size required")


@dataclass(frozen=True, slots=True)
class EATangentAnchorSettings:
    regularization: float
    c: float
    max_iterations: int
    query_batch_size: int = 8

    def __post_init__(self) -> None:
        if (
            not _positive(self.regularization)
            or not _positive(self.c)
            or type(self.max_iterations) is not int
            or self.max_iterations < 1
            or type(self.query_batch_size) is not int
            or self.query_batch_size < 1
        ):
            raise ValueError(
                "explicit positive EA regularization, C, iterations and batch required"
            )


@dataclass(frozen=True, slots=True)
class AnchorPrediction:
    method: str
    subject: str
    role: str
    episode_sha256: str
    selection_sha256: str
    settings_sha256: str
    settings: EEGNetAnchorSettings | EATangentAnchorSettings
    support_trial_ids: tuple[str, ...]
    query_trial_ids: tuple[str, ...]
    source_subjects: tuple[str, ...]
    input_identities: dict[str, Any]
    fit: dict[str, Any]
    source_state_sha256: str | None
    fitted_state_sha256: str
    probabilities: NDArray[np.float32]
    targets: NDArray[np.int64]
    classes: tuple[str, ...] | None = None
    channel_names: tuple[str, ...] = BCI_CHANNELS
    sampling_rate_hz: int = 128
    samples_per_trial: int = 512
    stored_unit_volts: float = 1.0
    engineering_only: bool = True
    source_training_history_verified: bool = False


def _classical_state(aligner: EuclideanAlignment, decoder: TangentSpaceLogistic) -> str:
    # Hash locally created estimator state only. Nothing is saved or unpickled.
    return hashlib.sha256(pickle.dumps((aligner, decoder), protocol=5)).hexdigest()


class BCIAnchorManifestRunner:
    """Fixed outer/inner permissions; no public tensor, query subset or source-list override.

    EEGNet owns a supplied source snapshot; its past training history is unverified.
    EA-tangent fits verified permitted source trials plus target support, matching
    the existing anchor recipe. Every source gets its own EA fit; target EA sees
    support only. OAS covariances are assembled one subject at a time to avoid a
    complete multi-subject signal copy. Neither method computes an accuracy score.
    """

    def __init__(
        self,
        root: Path,
        protocol_config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        profile_a_manifests: Mapping[str, str],
        *,
        outer_target: str,
        eegnet_source: nn.Module | None = None,
        validation_subject: str | None = None,
    ) -> None:
        self._root = root.resolve()
        config: dict[str, Any] = config_snapshot(protocol_config)
        self._config = config
        self._shots = validate_protocol(self._config)
        self._selection = source_selection(catalogs, target=outer_target)
        if not verify_envelope(
            selection_record, kind="source_selection", expected_payload=asdict(self._selection)
        ):
            raise ValueError("selection differs from reconstructed catalog cohort")
        dataset, channels, classes, subjects = dataset_cohort(self._config, catalogs)
        settings = self._config["datasets"][dataset]
        if (
            {c.subject for c in catalogs} != subjects
            or set(profile_a_manifests) != (subjects if dataset == "bci_iv_2a" else set())
            or tuple(settings["classes"]) != classes
            or settings["artifact_directory"] != f"data/processed/{dataset}/profile_a"
            or {
                p.stem
                for p in inside(self._root, settings["artifact_directory"]).glob("subject_*.npz")
            }
            != subjects
        ):
            raise ValueError(
                "complete declared Profile A cohort and matching manifest inventory required"
            )
        for sha in profile_a_manifests.values():
            require_digest(sha, "Profile A manifest")
        if (
            validation_subject is not None
            and validation_subject not in self._selection.source_subjects
        ):
            raise ValueError("inner validation must be a source subject, never outer target")
        self._catalogs = {c.subject: c for c in catalogs}
        self._assets = dict(profile_a_manifests)
        self._validation = validation_subject
        self._sources = tuple(s for s in self._selection.source_subjects if s != validation_subject)
        self._eegnet: nn.Module | None = None
        self._source_sha: str | None = None
        if eegnet_source is not None:
            from braindecode.models import EEGNet  # type: ignore[import-untyped]

            if not isinstance(eegnet_source, EEGNet) or (
                eegnet_source.n_chans,
                eegnet_source.n_outputs,
                eegnet_source.n_times,
                eegnet_source.sfreq,
            ) != (len(channels), len(classes), 512, 128):
                raise ValueError(
                    "source must be installed EEGNet matching the declared montage and head"
                )
            owned = copy.deepcopy(eegnet_source).eval()
            if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in owned.parameters()):
                raise ValueError("EEGNet source requires CPU float32 parameters")
            if any(not torch.isfinite(v).all() for v in owned.state_dict().values()):
                raise ValueError("nonfinite EEGNet source state")
            for p in owned.parameters():
                p.grad = None
            self._eegnet, self._source_sha = owned, state_digest(owned)

    @property
    def training_subjects(self) -> tuple[str, ...]:
        return self._sources

    def _load(self, subject: str) -> BCIProfileASubject:
        if self._selection.dataset == "bci_iv_2a":
            return load_bci_profile_a_subject(
                self._root,
                self._config,
                self._catalogs[subject],
                profile_a_manifest_sha256=self._assets[subject],
            )
        if self._selection.dataset == "cho2017":
            return load_cho_profile_a_subject(
                self._root, self._config, self._catalogs[subject]
            )
        from evaluation.phase2_cho_profile_a import load_mmidb_profile_a_subject

        return load_mmidb_profile_a_subject(
            self._root, self._config, self._catalogs[subject]
        )

    def _predict(
        self,
        subject: str,
        role: str,
        record: Mapping[str, Any],
        shots: int,
        settings: EEGNetAnchorSettings | EATangentAnchorSettings,
    ) -> AnchorPrediction:
        if not isinstance(settings, (EEGNetAnchorSettings, EATangentAnchorSettings)):
            raise ValueError("explicit anchor settings required")
        if isinstance(settings, EEGNetAnchorSettings) and self._eegnet is None:
            raise ValueError("EEGNet source template required")
        catalog = self._catalogs[subject]
        manifest = nested_episode(
            catalog, shots=self._shots, protocol_sha256=config_digest(self._config)
        )
        if not verify_envelope(
            record, kind="episode_manifest", expected_payload=manifest.payload()
        ):
            raise ValueError("episode differs from reconstructed target partition")
        partition = manifest.partition(shots)
        data = self._load(subject)
        support = data.signals[list(partition.support_indices)].copy()
        labels = data.labels[list(partition.support_indices)].copy()
        queries = data.signals[list(partition.query_indices)].copy()
        targets = data.labels[list(partition.query_indices)].copy()
        identities = {
            subject: {
                "catalog_sha256": catalog.sha256,
                "artifact_sha256": catalog.artifact_sha256,
                "manifest_sha256": data.manifest_sha256,
                "base_config_sha256": data.base_config_sha256,
            }
        }
        del data
        if isinstance(settings, EEGNetAnchorSettings):
            assert self._eegnet is not None
            if state_digest(self._eegnet) != self._source_sha:
                raise ValueError("owned EEGNet source changed")
            model = copy.deepcopy(self._eegnet).eval().requires_grad_(True)
            selected = list(model.parameters())
            inputs = torch.from_numpy(support).mul(settings.input_scale)
            optimizer = torch.optim.SGD(selected, lr=settings.learning_rate)
            losses = []
            for _ in range(settings.steps):
                optimizer.zero_grad(set_to_none=True)
                loss = nn.functional.cross_entropy(model(inputs), torch.from_numpy(labels))
                if not torch.isfinite(loss):
                    raise ValueError("nonfinite EEGNet support loss")
                loss.backward()  # type: ignore[no-untyped-call]
                if any(p.grad is None or not torch.isfinite(p.grad).all() for p in selected):
                    raise ValueError("missing or nonfinite EEGNet gradient")
                optimizer.step()
                if any(not torch.isfinite(p).all() for p in selected):
                    raise ValueError("nonfinite EEGNet parameter")
                losses.append(float(loss.detach()))
            optimizer.zero_grad(set_to_none=True)
            fitted_sha = state_digest(model)
            with torch.inference_mode():
                probabilities = (
                    torch.cat(
                        [
                            model(
                                torch.from_numpy(queries[i : i + settings.query_batch_size]).mul(
                                    settings.input_scale
                                )
                            ).softmax(1)
                            for i in range(0, len(queries), settings.query_batch_size)
                        ]
                    )
                    .numpy()
                    .copy()
                )
            if state_digest(model) != fitted_sha or state_digest(self._eegnet) != self._source_sha:
                raise ValueError("EEGNet query inference changed model state")
            fit = {
                "support_losses": losses,
                "trainable_names": [n for n, _ in model.named_parameters()],
                "trainable_parameters": sum(p.numel() for p in selected),
                "normalization": "all_modules_eval_affine_trainable_buffers_frozen",
                "source_fit_performed": False,
                "target_alignment": "none",
            }
            method = "eegnet"
            source_sha = self._source_sha
        else:
            decoder = TangentSpaceLogistic(c=settings.c, max_iterations=settings.max_iterations)
            covariances, fit_labels, source_ids = [], [], {}
            for name in self._sources:
                source = self._load(name)
                aligned = EuclideanAlignment(regularization=settings.regularization).fit_transform(
                    source.signals
                )
                covariances.append(decoder.covariances.transform(aligned))
                fit_labels.append(source.labels)
                source_ids[name] = self._catalogs[name].trial_ids
                identities[name] = {
                    "catalog_sha256": self._catalogs[name].sha256,
                    "artifact_sha256": self._catalogs[name].artifact_sha256,
                    "manifest_sha256": source.manifest_sha256,
                    "base_config_sha256": source.base_config_sha256,
                }
                del source, aligned
            aligner = EuclideanAlignment(regularization=settings.regularization).fit(support)
            covariances.append(decoder.covariances.transform(aligner.transform(support)))
            fit_labels.append(labels)
            with warnings.catch_warnings():
                warnings.simplefilter("error", ConvergenceWarning)
                features = decoder.tangent.fit_transform(np.concatenate(covariances))
                decoder.classifier.fit(features, np.concatenate(fit_labels))
            if not np.array_equal(
                decoder.classifier.classes_, np.arange(len(self._catalogs[subject].classes))
            ):
                raise ValueError("EA-tangent fitted class ordering changed")
            fitted_sha = _classical_state(aligner, decoder)
            probabilities = np.concatenate(
                [
                    decoder.predict_proba(
                        aligner.transform(queries[i : i + settings.query_batch_size])
                    )
                    for i in range(0, len(queries), settings.query_batch_size)
                ]
            )
            if _classical_state(aligner, decoder) != fitted_sha:
                raise ValueError("EA-tangent query inference changed fitted state")
            assert aligner.whitener_ is not None
            fit = {
                "source_fit_performed": True,
                "source_trial_ids": source_ids,
                "target_alignment": "support_only",
                "source_alignment": "each_permitted_subject_all_retained_trials",
                "classifier_fit": "all_permitted_sources_plus_selected_support",
                "covariance": "oas",
                "tangent": "riemann",
                "class_weight": "balanced",
                "target_whitener": aligner.whitener_.tolist(),
            }
            method, source_sha = "ea_tangent_lr", None
        if (
            probabilities.shape != (len(targets), len(self._catalogs[subject].classes))
            or not np.isfinite(probabilities).all()
            or np.any(probabilities < 0)
            or np.any(probabilities > 1)
            or not np.allclose(probabilities.sum(1), 1, atol=1e-6, rtol=1e-6)
        ):
            raise ValueError("invalid anchor probabilities")
        return AnchorPrediction(
            method,
            subject,
            role,
            manifest.sha256,
            self._selection.sha256,
            config_digest(asdict(settings)),
            settings,
            tuple(catalog.trial_ids[i] for i in partition.support_indices),
            tuple(catalog.trial_ids[i] for i in partition.query_indices),
            self._sources,
            identities,
            fit,
            source_sha,
            fitted_sha,
            np.asarray(probabilities, dtype=np.float32),
            targets,
            classes=catalog.classes,
        )

    def predict_target(
        self,
        episode_record: Mapping[str, Any],
        *,
        shots_per_class: int,
        settings: EEGNetAnchorSettings | EATangentAnchorSettings,
    ) -> AnchorPrediction:
        if self._validation is not None:
            raise ValueError("outer-target prediction is unavailable during inner validation")
        return self._predict(
            self._selection.target_subject,
            "outer_target",
            episode_record,
            shots_per_class,
            settings,
        )

    def predict_validation(
        self,
        episode_record: Mapping[str, Any],
        *,
        shots_per_class: int,
        settings: EEGNetAnchorSettings | EATangentAnchorSettings,
    ) -> AnchorPrediction:
        if self._validation is None:
            raise ValueError("this runner has no inner-validation subject")
        return self._predict(
            self._validation, "inner_validation", episode_record, shots_per_class, settings
        )
