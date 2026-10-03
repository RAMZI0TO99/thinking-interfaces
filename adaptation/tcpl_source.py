"""Bounded BCI TCPL source fitting and complete source-only LOSO; engineering only.

Each fold owns a fresh trainer from the pinned caller template and takes
class-stratified episodic Adam steps over the permitted source subjects, then
validates through the audited manifest runner with the fitted trainer admitted
directly. Full-episode training is deliberately unsupported: the fixed common
query pool (~430 trials per subject) does not fit bounded CPU memory with
retained activations, so every step draws an explicit small episode instead.
No external scores, partial resume, target prediction or scientific publication.
"""

from __future__ import annotations

import platform
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import torch

from adaptation.source_selection import SelectionEvidence
from adaptation.tcpl_episodic import TCPLSourceTrainer
from adaptation.tcpl_manifest import TCPLManifestRunner, TCPLTrainerSettings
from core.config import canonical_config_json, config_digest, config_snapshot
from core.provenance import capture_source, source_fingerprint
from encoder.tcpl import TCPLClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_profile_a import load_cho_profile_a_subject
from evaluation.phase2_profile_binding import load_bci_profile_a_subject
from evaluation.phase2_protocol import (
    TrialCatalog,
    nested_episode,
    require_digest,
    require_names,
    source_selection,
)
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import validate_protocol


@dataclass(frozen=True, slots=True)
class TCPLSourceSettings:
    steps_per_subject: int
    support_shots_per_class: int
    query_shots_per_class: int
    optimizer: TCPLTrainerSettings

    def __post_init__(self) -> None:
        if any(
            type(v) is not int or v < 1
            for v in (
                self.steps_per_subject,
                self.support_shots_per_class,
                self.query_shots_per_class,
            )
        ):
            raise ValueError("positive integer source steps and class-balanced shots required")
        if not isinstance(self.optimizer, TCPLTrainerSettings):
            raise ValueError("explicit TCPL trainer optimizer settings required")


@dataclass(frozen=True, slots=True)
class TCPLSupportSettings:
    query_batch_size: int = 8

    def __post_init__(self) -> None:
        if type(self.query_batch_size) is not int or self.query_batch_size < 1:
            raise ValueError("positive integer query batch size required")


@dataclass(frozen=True, slots=True)
class TCPLSourceCandidate:
    name: str
    source: TCPLSourceSettings
    support: TCPLSupportSettings

    def __post_init__(self) -> None:
        require_names((self.name,), "candidate name")
        if not isinstance(self.source, TCPLSourceSettings) or not isinstance(
            self.support, TCPLSupportSettings
        ):
            raise ValueError("explicit TCPL source and support settings required")


@dataclass(frozen=True, slots=True)
class SelectedTCPL:
    runner: TCPLManifestRunner
    evidence: SelectionEvidence


class BCITCPLSourceSelector:
    """Fixed TCPL roster, pinned template and complete inner source-only selection.

    The caller supplies a pinned template; the selector never reinitializes it.
    Every fit builds a fresh trainer with the candidate's explicit Adam settings
    and draws class-stratified support/query episodes from each permitted source
    subject's retained Profile A trials, recording the exact trial IDs and state
    hash after every step. Episode size stays within the eight-trial ceiling.
    Dropout inside episodic training draws from a per-fold isolated seeded RNG,
    so fits repeat exactly and the caller's RNG is preserved. Validation binds
    the audited episode and predicts through the frozen support-conditioned
    session of the manifest runner with the fitted trainer admitted directly.
    Selection averages class recall within each fold, then weights folds equally;
    exact rational ties choose the first candidate in the declared roster.

    The hard gradient-step and batch ceilings limit this engineering executor;
    they are not the paper's schedule, scientific budgets or resource guards.
    """

    def __init__(
        self,
        root: Path,
        protocol_config: Mapping[str, Any],
        catalogs: tuple[TrialCatalog, ...],
        selection_record: Mapping[str, Any],
        source_template: TCPLClassifier,
        profile_a_manifests: Mapping[str, str],
        *,
        outer_target: str,
        channel_names: tuple[str, ...],
        candidates: tuple[TCPLSourceCandidate, ...],
        template_state_sha256: str,
        seed: int,
        shots_per_class: int,
        maximum_gradient_steps: int,
    ) -> None:
        require_digest(template_state_sha256, "template_state_sha256")
        if (
            not isinstance(candidates, tuple)
            or not candidates
            or any(not isinstance(c, TCPLSourceCandidate) for c in candidates)
        ):
            raise ValueError("explicit immutable TCPL candidate roster required")
        require_names(tuple(c.name for c in candidates), "candidate names")
        hashes = [
            config_digest({"source": asdict(c.source), "support": asdict(c.support)})
            for c in candidates
        ]
        if len(set(hashes)) != len(hashes):
            raise ValueError("duplicate candidate settings")
        if type(seed) is not int or not 0 <= seed < 2**63:
            raise ValueError("explicit nonnegative 63-bit seed required")
        if type(maximum_gradient_steps) is not int or not 1 <= maximum_gradient_steps <= 256:
            raise ValueError("engineering gradient-step ceiling must be between 1 and 256")
        if not isinstance(source_template, TCPLClassifier):
            raise ValueError("TCPL source template required")
        if state_digest(source_template) != template_state_sha256:
            raise ValueError("template differs from its pinned state")
        config: dict[str, Any] = config_snapshot(protocol_config)
        shots = validate_protocol(config)
        if type(shots_per_class) is not int or shots_per_class not in shots:
            raise ValueError("shots must belong to the audited protocol")
        classes = len(catalogs[0].classes)
        if any(
            classes
            * (c.source.support_shots_per_class + c.source.query_shots_per_class)
            > 8
            or c.support.query_batch_size > 32
            for c in candidates
        ):
            raise ValueError("class-balanced episodes must stay within the eight-trial ceiling")
        if catalogs[0].dataset in {"cho2017", "mmidb"}:
            # Cho/MMIDB Profile A identity is the audited catalog hash; no sidecars.
            if profile_a_manifests:
                raise ValueError(
                    "the Cho2017/MMIDB Profile A identity carries no sidecar manifests"
                )
        elif set(profile_a_manifests) != {c.subject for c in catalogs} or any(
            not isinstance(v, str) for v in profile_a_manifests.values()
        ):
            raise ValueError("complete Profile A manifest inventory required")
        # Validate the actual existing runner contract before any source fit.
        TCPLManifestRunner(
            root,
            config,
            catalogs,
            selection_record,
            source_template,
            outer_target=outer_target,
            channel_names=tuple(channel_names),
        )
        self._root = root.resolve()
        self._config = config
        self._catalogs = {c.subject: c for c in catalogs}
        self._selection = source_selection(catalogs, target=outer_target)
        self._record = config_snapshot(selection_record)
        self._assets = dict(profile_a_manifests)
        self._template = source_template
        self._template_sha = template_state_sha256
        self._channels = tuple(channel_names)
        self._candidates = candidates
        self._seed = seed
        self._shots = shots_per_class
        self._maximum = maximum_gradient_steps
        self._classes = classes
        self._episodes = {
            name: nested_episode(c, shots=shots, protocol_sha256=config_digest(config))
            for name, c in self._catalogs.items()
        }
        self._contract: dict[str, Any] = {
            "method": "tcpl_local",
            "dataset": self._selection.dataset,
            "selection": asdict(self._selection),
            "protocol_sha256": config_digest(config),
            "channel_names": list(self._channels),
            "profile_a_manifests": self._assets,
            "candidates": [asdict(c) for c in candidates],
            "template_state_sha256": template_state_sha256,
            "template_reinitialization": False,
            "fold_rng_seed": seed,
            "shots_per_class": shots_per_class,
            "source_episode_policy": (
                "class_stratified_bounded_episodes; eight-trial ceiling; "
                "full_query_pool_training_unsupported_after_measured_oom"
            ),
            "maximum_gradient_steps": maximum_gradient_steps,
            "source_policy": (
                "all_sources_minus_outer_target_minus_inner_validation"
            ),
            "score": "mean_subject_balanced_accuracy_exact_rational",
            "tie_break": "first_in_declared_candidate_order",
            "early_stopping": False,
            "engineering_only": True,
            "scientific_evaluation": False,
            "source": asdict(capture_source(self._root)),
            "runtime": {
                "python": platform.python_version(),
                "torch": torch.__version__,
                "numpy": np.__version__,
                "device": "cpu",
                "dtype": "float32",
                "torch_threads": torch.get_num_threads(),
            },
        }

    @property
    def contract(self) -> dict[str, Any]:
        return config_snapshot(self._contract)

    def _candidate(self, name: str) -> TCPLSourceCandidate:
        for candidate in self._candidates:
            if candidate.name == name:
                return candidate
        raise ValueError("candidate is outside the fixed roster")

    def _admit(self, steps: int) -> None:
        if steps > self._maximum:
            raise ValueError("requested work exceeds the declared gradient-step ceiling")

    def _fit(
        self, candidate: TCPLSourceCandidate, validation_subject: str | None
    ) -> tuple[TCPLManifestRunner, dict[str, Any]]:
        """Fresh trainer plus its complete bounded class-stratified source history.

        The whole fit runs under an isolated seeded RNG so train-mode dropout is
        deterministic and repeatable; validation afterwards reuses the fitted
        trainer through the audited runner instead of a second model copy.
        """
        settings = candidate.source
        take = settings.support_shots_per_class + settings.query_shots_per_class
        subjects = tuple(s for s in self._selection.source_subjects if s != validation_subject)
        with torch.random.fork_rng(devices=[]):
            torch.random.set_rng_state(
                torch.Generator(device="cpu").manual_seed(self._seed).get_state()
            )
            trainer = TCPLSourceTrainer(
                self._template,
                learning_rate=settings.optimizer.learning_rate,
                weight_decay=settings.optimizer.weight_decay,
                prompt_l2_weight=settings.optimizer.prompt_l2_weight,
            )
            initial_sha = state_digest(trainer.model)
            sampling = torch.Generator(device="cpu").manual_seed(self._seed)
            history: list[dict[str, Any]] = []
            identities: dict[str, Any] = {}
            for subject in subjects:
                catalog = self._catalogs[subject]
                if self._selection.dataset == "bci_iv_2a":
                    data = load_bci_profile_a_subject(
                        self._root,
                        self._config,
                        catalog,
                        profile_a_manifest_sha256=self._assets[subject],
                    )
                elif self._selection.dataset == "cho2017":
                    data = load_cho_profile_a_subject(self._root, self._config, catalog)
                else:
                    from evaluation.phase2_cho_profile_a import load_mmidb_profile_a_subject

                    data = load_mmidb_profile_a_subject(self._root, self._config, catalog)
                identities[subject] = {
                    "catalog_sha256": catalog.sha256,
                    "artifact_sha256": catalog.artifact_sha256,
                    "manifest_sha256": data.manifest_sha256,
                    "base_config_sha256": data.base_config_sha256,
                }
                label_of = {
                    name: int(label)
                    for name, label in zip(catalog.trial_ids, data.labels, strict=True)
                }
                by_class = {
                    c: [name for name in catalog.trial_ids if label_of[name] == c]
                    for c in range(self._classes)
                }
                if any(len(members) < take for members in by_class.values()):
                    raise ValueError("class-balanced episodes need enough retained trials")
                permutation = {
                    c: torch.randperm(len(by_class[c]), generator=sampling).tolist()
                    for c in range(self._classes)
                }
                row_of = {
                    name: i for i, name in enumerate(catalog.trial_ids)
                }
                for step in range(settings.steps_per_subject):
                    support_ids: list[str] = []
                    query_ids: list[str] = []
                    for c in range(self._classes):
                        members = [
                            by_class[c][permutation[c][(step * take + i) % len(permutation[c])]]
                            for i in range(take)
                        ]
                        support_ids.extend(members[: settings.support_shots_per_class])
                        query_ids.extend(members[settings.support_shots_per_class :])
                    support = torch.as_tensor(
                        data.signals[[row_of[n] for n in support_ids]].copy(),
                        dtype=torch.float32,
                    )[None]
                    queries = torch.as_tensor(
                        data.signals[[row_of[n] for n in query_ids]].copy(),
                        dtype=torch.float32,
                    )[None]
                    targets = torch.tensor(
                        [[label_of[n] for n in query_ids]], dtype=torch.long
                    )
                    loss = trainer.step(support, queries, targets)
                    history.append(
                        {
                            "step": len(history) + 1,
                            "subject": subject,
                            "subject_step": step + 1,
                            "support_trial_ids": tuple(support_ids),
                            "query_trial_ids": tuple(query_ids),
                            "loss": {
                                "total": loss.total,
                                "query_cross_entropy": loss.query_cross_entropy,
                                "prompt_penalty": loss.prompt_penalty,
                            },
                            "iterator_wraps": max(
                                ((step + 1) * take - 1) // len(by_class[c])
                                for c in range(self._classes)
                            ),
                            "state_sha256_after": state_digest(trainer.model),
                        }
                    )
                del data
            runner = TCPLManifestRunner(
                self._root,
                self._config,
                tuple(self._catalogs.values()),
                self._record,
                self._template,
                outer_target=self._selection.target_subject,
                channel_names=self._channels,
                validation_subject=validation_subject,
                source_trainer=trainer,
            )
            fitted_sha = runner.source_state_sha256
        if state_digest(self._template) != self._template_sha:
            raise ValueError("source fitting changed the caller template")
        return runner, {
            "training_subjects": list(subjects),
            "validation_subject": validation_subject,
            "settings": asdict(settings),
            "optimizer": {
                "name": "Adam",
                "betas": [0.9, 0.999],
                "eps": 1e-08,
                "amsgrad": False,
                "weight_decay": settings.optimizer.weight_decay,
                "fresh": True,
            },
            "normalization_and_dropout": "trainer_train_mode_during_steps_only",
            "input_identities": identities,
            "initial_state_sha256": initial_sha,
            "fitted_state_sha256": fitted_sha,
            "steps": history,
            "history_scope": "complete_for_this_bounded_fit_only",
            "engineering_only": True,
        }

    def _fold(self, candidate: TCPLSourceCandidate, subject: str) -> dict[str, Any]:
        runner, fit = self._fit(candidate, subject)
        prediction = runner.predict_validation(
            envelope("episode_manifest", self._episodes[subject].payload()),
            shots_per_class=self._shots,
            query_batch_size=candidate.support.query_batch_size,
        )
        if runner.source_state_sha256 != fit["fitted_state_sha256"]:
            raise ValueError("validation inference changed the fitted source state")
        predicted = prediction.logits.argmax(dim=1)
        confusion = np.zeros((self._classes, self._classes), dtype=np.int64)
        np.add.at(confusion, (prediction.targets.numpy(), predicted.numpy()), 1)
        score = (
            sum(
                (
                    Fraction(int(confusion[i, i]), int(confusion[i].sum()))
                    for i in range(self._classes)
                ),
                start=Fraction(),
            )
            / self._classes
        )
        return {
            "candidate": candidate.name,
            "validation_subject": subject,
            "source_fit": fit,
            "episode_sha256": prediction.episode_sha256,
            "query_trial_ids": prediction.query_trial_ids,
            "confusion_matrix": confusion.tolist(),
            "balanced_accuracy": [score.numerator, score.denominator],
        }

    def _evidence(self, payload: Mapping[str, Any]) -> SelectionEvidence:
        if source_fingerprint(self._root) != self._contract["source"]["source_sha256"]:
            raise ValueError("source/config identity changed during execution")
        return SelectionEvidence(
            canonical_config_json(
                envelope(
                    "engineering_smoke",
                    {
                        "purpose": "bounded_tcpl_source_selection",
                        "contract": self.contract,
                        "contract_sha256": config_digest(self._contract),
                        **payload,
                    },
                )
            )
        )

    def run_fold(self, *, candidate_name: str, validation_subject: str) -> SelectionEvidence:
        """One diagnostic fold; explicitly incomplete, never carries a winner."""
        candidate = self._candidate(candidate_name)
        if validation_subject not in self._selection.source_subjects:
            raise ValueError("validation must be a source subject, never the outer target")
        self._admit(
            (len(self._selection.source_subjects) - 1) * candidate.source.steps_per_subject
        )
        fold = self._fold(candidate, validation_subject)
        return self._evidence({"complete": False, "folds": [fold], "selected_candidate": None})

    def run_selection(self) -> SelectedTCPL:
        """Complete every candidate/fold, then fit the winner afresh on all sources.

        No partial-result import or resume exists. Failure returns no winner. The
        returned runner owns the final fitted trainer under its declared roles.
        """
        inner = len(self._selection.inner_folds)
        sources = len(self._selection.source_subjects)
        self._admit(
            sum(
                inner * (sources - 1) * c.source.steps_per_subject for c in self._candidates
            )
            + sources * max(c.source.steps_per_subject for c in self._candidates)
        )
        folds = [
            self._fold(c, fold.validation_subject)
            for c in self._candidates
            for fold in self._selection.inner_folds
        ]
        scores = []
        for candidate in self._candidates:
            scores.append(
                sum(
                    (
                        Fraction(*f["balanced_accuracy"])
                        for f in folds
                        if f["candidate"] == candidate.name
                    ),
                    start=Fraction(),
                )
                / inner
            )
        winner = self._candidates[max(range(len(scores)), key=lambda i: scores[i])]
        runner, final_fit = self._fit(winner, None)
        if runner.source_state_sha256 != final_fit["fitted_state_sha256"]:
            raise ValueError("final runner state differs from its recorded fit")
        return SelectedTCPL(
            runner,
            self._evidence(
                {
                    "complete": True,
                    "folds": folds,
                    "selected_candidate": winner.name,
                    "scores": [
                        {
                            "candidate": c.name,
                            "mean_balanced_accuracy": [s.numerator, s.denominator],
                        }
                        for c, s in zip(self._candidates, scores, strict=True)
                    ],
                    "final_source_fit": final_fit,
                    "outer_target_predictions_performed": False,
                }
            ),
        )
