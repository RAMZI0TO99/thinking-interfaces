"""Bounded BCI EEGNet source fitting and complete inner LOSO; engineering only.

No external scores, target prediction, early stopping, or scientific publication.
Every invocation starts from seeded random weights and fresh SGD state.
"""

from __future__ import annotations

import json
import math
import platform
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from adaptation.anchor_manifest import BCIAnchorManifestRunner, EEGNetAnchorSettings
from core.config import canonical_config_json, config_digest, config_snapshot
from core.provenance import capture_source, source_fingerprint
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_input_snapshot import _ChoInputSnapshot
from evaluation.phase2_cho_profile_a import load_cho_profile_a_subject
from evaluation.phase2_profile_binding import (
    DATASET_CHANNELS,
    BCIProfileASubject,
    load_bci_profile_a_subject,
)
from evaluation.phase2_protocol import (
    TrialCatalog,
    nested_episode,
    require_names,
    selection_gradient_ceiling,
    source_selection,
)
from evaluation.phase2_records import envelope, write_once
from scripts.audit_phase2_protocol import validate_protocol


@dataclass(frozen=True, slots=True)
class EEGNetSourceSettings:
    steps_per_subject: int
    batch_size: int
    learning_rate: float
    input_scale: float

    def __post_init__(self) -> None:
        if any(type(v) is not int or v < 1 for v in (self.steps_per_subject, self.batch_size)):
            raise ValueError("positive source steps and batch size required")
        if any(
            type(v) not in (int, float) or not math.isfinite(v) or v <= 0
            for v in (self.learning_rate, self.input_scale)
        ):
            raise ValueError("positive finite source learning rate and input scale required")


@dataclass(frozen=True, slots=True)
class EEGNetCandidate:
    name: str
    source: EEGNetSourceSettings
    support: EEGNetAnchorSettings

    def __post_init__(self) -> None:
        require_names((self.name,), "candidate name")
        if not isinstance(self.source, EEGNetSourceSettings) or not isinstance(
            self.support, EEGNetAnchorSettings
        ):
            raise ValueError("explicit EEGNet source and support settings required")
        if self.source.input_scale != self.support.input_scale:
            raise ValueError("source and support must use identical units")


@dataclass(frozen=True, slots=True)
class SelectionEvidence:
    """Canonical immutable bytes; decoded dictionaries are independent copies."""

    record_json: str

    @property
    def record(self) -> dict[str, Any]:
        result: dict[str, Any] = json.loads(self.record_json)
        return result

    def write(self, path: Path, *, output_root: Path) -> Path:
        return write_once(path, self.record, output_root=output_root)


@dataclass(frozen=True, slots=True)
class SelectedEEGNet:
    source: nn.Module
    evidence: SelectionEvidence


class BCIEEGNetSourceSelector:
    """Small CPU executor with a fixed candidate roster and complete source-subject LOSO selection.

    Source fit: all parameters, eval-mode normalization/dropout, SGD without
    momentum/decay, canonical subject order, seeded per-subject permutation,
    fixed steps, no query stopping. Source trials can be reused on iterator wrap.
    Seeds initialize both the random EEGNet and an independent sampling generator.
    Selection averages class recall within each fold, then weights folds equally;
    exact rational ties choose the first candidate in the declared roster.

    The complete declared cohort is mandatory. Ineligible sources are never
    silently pruned.
    The hard 256-step and 32-trial batch ceilings limit this engineering executor;
    they are not scientific training budgets or replacements for resource guards.
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
        candidates: tuple[EEGNetCandidate, ...],
        seed: int,
        shots_per_class: int,
        maximum_gradient_steps: int,
    ) -> None:
        if (
            not isinstance(candidates, tuple)
            or not candidates
            or any(not isinstance(c, EEGNetCandidate) for c in candidates)
        ):
            raise ValueError("explicit immutable candidate roster required")
        require_names(tuple(c.name for c in candidates), "candidate names")
        settings_hashes = tuple(
            config_digest({"source": asdict(c.source), "support": asdict(c.support)})
            for c in candidates
        )
        if len(set(settings_hashes)) != len(settings_hashes):
            raise ValueError("duplicate candidate settings")
        if type(seed) is not int or not 0 <= seed < 2**63:
            raise ValueError("explicit nonnegative 63-bit seed required")
        if type(maximum_gradient_steps) is not int or not 1 <= maximum_gradient_steps <= (
            selection_gradient_ceiling(root)
        ):
            raise ValueError("engineering gradient-step ceiling must be between 1 and 256")
        config: dict[str, Any] = config_snapshot(protocol_config)
        shots = validate_protocol(config)
        if type(shots_per_class) is not int or shots_per_class not in shots:
            raise ValueError("shots must belong to the audited protocol")
        if any(c.source.batch_size > 32 or c.support.query_batch_size > 32 for c in candidates):
            raise ValueError("engineering batch ceiling is 32 trials")
        cho_world = catalogs[0].dataset == "cho2017"
        if cho_world and profile_a_manifests:
            raise ValueError("the Cho2017 Profile A identity carries no sidecar manifests")
        # Reuse the actual anchor's complete-cohort and envelope admission contract.
        BCIAnchorManifestRunner(
            root,
            config,
            catalogs,
            selection_record,
            profile_a_manifests,
            outer_target=outer_target,
        )
        self._root = root.resolve()
        self._config = config
        self._catalogs = {c.subject: c for c in catalogs}
        self._selection = source_selection(catalogs, target=outer_target)
        self._cho_inputs = (
            _ChoInputSnapshot(
                self._root, config,
                tuple(self._catalogs[s] for s in self._selection.source_subjects),
            )
            if cho_world else None
        )
        self._selection_record = config_snapshot(selection_record)
        self._assets = dict(profile_a_manifests)
        self._candidates = candidates
        self._seed = seed
        self._shots = shots_per_class
        self._maximum = maximum_gradient_steps
        # Eligibility is checked before the first gradient step, including all folds.
        self._episodes = {
            name: nested_episode(c, shots=shots, protocol_sha256=config_digest(config))
            for name, c in self._catalogs.items()
        }
        for c in candidates:
            if any(len(v.trial_ids) < c.source.batch_size for v in catalogs):
                raise ValueError("source batch exceeds a retained subject's trial count")
        self._contract: dict[str, Any] = {
            "method": "eegnet",
            "dataset": self._selection.dataset,
            "outer_target": outer_target,
            "selection": asdict(self._selection),
            "protocol_sha256": config_digest(config),
            "profile_a_manifests": self._assets,
            "candidates": [asdict(c) for c in candidates],
            "model_and_sampling_seed": seed,
            "shots_per_class": shots_per_class,
            "maximum_gradient_steps": maximum_gradient_steps,
            "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
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
                "braindecode": version("braindecode"),
                "device": "cpu",
                "dtype": "float32",
                "torch_threads": torch.get_num_threads(),
                "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            },
        }

    @property
    def contract(self) -> dict[str, Any]:
        return config_snapshot(self._contract)

    def _candidate(self, name: str) -> EEGNetCandidate:
        for candidate in self._candidates:
            if candidate.name == name:
                return candidate
        raise ValueError("candidate is outside the fixed roster")

    def _admit(self, steps: int) -> None:
        if steps > self._maximum:
            raise ValueError("requested work exceeds the declared gradient-step ceiling")

    def _fit(
        self, candidate: EEGNetCandidate, validation_subject: str | None
    ) -> tuple[nn.Module, dict[str, Any]]:
        from braindecode.models import EEGNet  # type: ignore[import-untyped]

        subjects = tuple(s for s in self._selection.source_subjects if s != validation_subject)
        settings = candidate.source
        # No global CPU/CUDA seed changes leak to the caller.
        with torch.random.fork_rng(devices=[]):
            torch.random.set_rng_state(
                torch.Generator(device="cpu").manual_seed(self._seed).get_state()
            )
            model: nn.Module = (
                EEGNet(
                    n_chans=len(DATASET_CHANNELS[self._selection.dataset]),
                    n_outputs=len(next(iter(self._catalogs.values())).classes),
                    n_times=512,
                    sfreq=128,
                    final_layer_with_constraint=True,
                )
                .cpu()
                .float()
                .eval()
            )
        initial_sha = state_digest(model)
        buffers = {n: v.clone() for n, v in model.named_buffers()}
        optimizer = torch.optim.SGD(model.parameters(), lr=settings.learning_rate)
        generator = torch.Generator(device="cpu").manual_seed(self._seed)
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
                data = self._load_cho(catalog)
            else:
                from evaluation.phase2_cho_profile_a import load_mmidb_profile_a_subject

                data = load_mmidb_profile_a_subject(self._root, self._config, catalog)
            identities[subject] = {
                "catalog_sha256": catalog.sha256,
                "artifact_sha256": catalog.artifact_sha256,
                "manifest_sha256": data.manifest_sha256,
                "base_config_sha256": data.base_config_sha256,
            }
            permutation = torch.randperm(len(catalog.trial_ids), generator=generator).tolist()
            for step in range(settings.steps_per_subject):
                positions = range(step * settings.batch_size, (step + 1) * settings.batch_size)
                indices = [permutation[i % len(permutation)] for i in positions]
                x = torch.from_numpy(data.signals[indices].copy()) * settings.input_scale
                y = torch.from_numpy(data.labels[indices].copy())
                optimizer.zero_grad(set_to_none=True)
                loss = nn.functional.cross_entropy(model(x), y)
                if not torch.isfinite(loss):
                    raise ValueError("nonfinite source loss")
                loss.backward()  # type: ignore[no-untyped-call]
                if any(
                    p.grad is None or not torch.isfinite(p.grad).all() for p in model.parameters()
                ):
                    raise ValueError("missing or nonfinite source gradient")
                optimizer.step()
                if any(not torch.isfinite(v).all() for v in model.state_dict().values()):
                    raise ValueError("nonfinite source model state")
                history.append(
                    {
                        "step": len(history) + 1,
                        "subject": subject,
                        "trial_ids": [catalog.trial_ids[i] for i in indices],
                        "subject_step": step + 1,
                        "iterator_wraps": ((step + 1) * settings.batch_size - 1)
                        // len(permutation),
                        "loss": float(loss.detach()),
                        "state_sha256_after": state_digest(model),
                    }
                )
            del data
        optimizer.zero_grad(set_to_none=True)
        if any(not torch.equal(v, buffers[n]) for n, v in model.named_buffers()):
            raise ValueError("source fitting changed fixed normalization buffers")
        return model, {
            "candidate": candidate.name,
            "candidate_sha256": config_digest(asdict(candidate)),
            "validation_subject": validation_subject,
            "training_subjects": subjects,
            "input_identities": identities,
            "seed": self._seed,
            "initialization": "seeded_random_installed_EEGNet_22_4_512_128_constrained_linear",
            "optimizer": {"name": "SGD", "momentum": 0, "weight_decay": 0, "fresh": True},
            "settings": asdict(settings),
            "trainable_parameters": "all",
            "normalization_and_dropout": "all_modules_eval",
            "steps": history,
            "initial_state_sha256": initial_sha,
            "fitted_state_sha256": state_digest(model),
            "history_scope": "complete_for_this_bounded_fit_only",
            "engineering_only": True,
        }

    def _fold(self, candidate: EEGNetCandidate, subject: str) -> dict[str, Any]:
        model, fit = self._fit(candidate, subject)
        selector = self

        class _SelectionAnchorRunner(BCIAnchorManifestRunner):
            def _load(self, name: str) -> BCIProfileASubject:
                if self._selection.dataset == "cho2017":
                    return selector._load_cho(self._catalogs[name])
                return super()._load(name)

        runner = _SelectionAnchorRunner(
            self._root,
            self._config,
            tuple(self._catalogs.values()),
            self._selection_record,
            self._assets,
            outer_target=self._selection.target_subject,
            validation_subject=subject,
            eegnet_source=model,
        )
        prediction = runner.predict_validation(
            envelope("episode_manifest", self._episodes[subject].payload()),
            shots_per_class=self._shots,
            settings=candidate.support,
        )
        if prediction.source_state_sha256 != fit["fitted_state_sha256"]:
            raise ValueError("inner validation source state differs from its fit history")
        predicted = prediction.probabilities.argmax(axis=1)
        classes = prediction.probabilities.shape[1]
        confusion = np.zeros((classes, classes), dtype=np.int64)
        np.add.at(confusion, (prediction.targets, predicted), 1)
        score = (
            sum(
                (
                    Fraction(int(confusion[i, i]), int(confusion[i].sum()))
                    for i in range(classes)
                    if confusion[i].sum() > 0
                ),
                start=Fraction(),
            )
            / classes
        )
        return {
            "candidate": candidate.name,
            "validation_subject": subject,
            "source_fit": fit,
            "episode_sha256": prediction.episode_sha256,
            "support_trial_ids": prediction.support_trial_ids,
            "query_trial_ids": prediction.query_trial_ids,
            "input_identities": prediction.input_identities,
            "support_fit": prediction.fit,
            "adapted_state_sha256": prediction.fitted_state_sha256,
            "confusion_matrix": confusion.tolist(),
            "balanced_accuracy": [score.numerator, score.denominator],
        }

    def _evidence(self, payload: Mapping[str, Any]) -> SelectionEvidence:
        if self._cho_inputs is not None:
            self._cho_inputs.verify(self._config)
        if source_fingerprint(self._root) != self._contract["source"]["source_sha256"]:
            raise ValueError("source/config identity changed during execution")
        return SelectionEvidence(
            canonical_config_json(
                envelope(
                    "engineering_smoke",
                    {
                        "purpose": "bounded_eegnet_source_selection",
                        "contract": self.contract,
                        "contract_sha256": config_digest(self._contract),
                        **payload,
                    },
                )
            )
        )

    def _load_cho(self, catalog: TrialCatalog) -> BCIProfileASubject:
        if self._cho_inputs is None:
            return load_cho_profile_a_subject(self._root, self._config, catalog)
        return self._cho_inputs.load(self._config, catalog)

    def run_fold(self, *, candidate_name: str, validation_subject: str) -> SelectionEvidence:
        """One diagnostic fold; explicitly incomplete, never carries a selected candidate."""
        candidate = self._candidate(candidate_name)
        if validation_subject not in self._selection.source_subjects:
            raise ValueError("validation must be a source subject, never the outer target")
        sources = len(self._selection.source_subjects)
        self._admit(
            (sources - 1) * candidate.source.steps_per_subject + candidate.support.steps
        )
        fold = self._fold(candidate, validation_subject)
        return self._evidence({"complete": False, "folds": [fold], "selected_candidate": None})

    def run_selection(self) -> SelectedEEGNet:
        """Complete every candidate/fold, then fit the winner afresh on all sources.

        No partial-result import or resume exists. Failure returns no winner or final
        fit. Returned evidence can be persisted atomically without overwriting history.
        The returned model is mutable; its recorded state digest must be checked on reuse.
        """
        sources = len(self._selection.source_subjects)
        inner = len(self._selection.inner_folds)
        upper_bound = sum(
            inner * ((sources - 1) * c.source.steps_per_subject + c.support.steps)
            for c in self._candidates
        ) + sources * max(c.source.steps_per_subject for c in self._candidates)
        self._admit(upper_bound)
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
                / len(self._selection.inner_folds)
            )
        winner = self._candidates[max(range(len(scores)), key=lambda i: scores[i])]
        model, final_fit = self._fit(winner, None)
        return SelectedEEGNet(
            model,
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
