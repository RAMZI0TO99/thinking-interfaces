"""Bounded BCI EA-tangent candidate selection over complete inner LOSO; engineering only.

The classical recipe has no separate trained-source artifact: every anchor
prediction refits permitted sources plus the held-out subject's support. This
selector fixes a candidate roster, runs all source-only inner folds per
candidate, ranks exact rational subject-averaged balanced accuracy and declares
one winner. No external scores, partial resume, target prediction or scientific
publication.
"""

from __future__ import annotations

import platform
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import torch

from adaptation.anchor_manifest import BCIAnchorManifestRunner, EATangentAnchorSettings
from adaptation.source_selection import SelectionEvidence
from core.config import canonical_config_json, config_digest, config_snapshot
from core.provenance import capture_source, source_fingerprint
from evaluation.phase2_protocol import TrialCatalog, nested_episode, require_names, source_selection
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import validate_protocol


@dataclass(frozen=True, slots=True)
class EATangentCandidate:
    name: str
    support: EATangentAnchorSettings

    def __post_init__(self) -> None:
        require_names((self.name,), "candidate name")
        if not isinstance(self.support, EATangentAnchorSettings):
            raise ValueError("explicit EA-tangent anchor settings required")


@dataclass(frozen=True, slots=True)
class SelectedEATangent:
    candidate: EATangentCandidate
    evidence: SelectionEvidence


class BCIEATangentSelector:
    """Fixed EA roster and complete source-subject LOSO selection without a persistent model.

    EA-tangent alignment, covariance and tangent-logistic fitting happen inside
    each audited anchor prediction over that fold's permitted sources plus the
    held-out subject's selected support. Candidates differ only in the classical
    recipe settings; there is no seed, no optimizer state and no final refit to
    persist, so selection declares the winning settings rather than weights.
    Selection averages class recall within each fold, then weights folds equally;
    exact rational ties choose the first candidate in the declared roster.

    The complete declared cohort is mandatory; ineligible sources are never
    silently pruned. The hard classical-fit ceiling limits this engineering executor; it
    is not a scientific budget or a replacement for resource guards.
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
        candidates: tuple[EATangentCandidate, ...],
        shots_per_class: int,
        maximum_classical_fits: int,
    ) -> None:
        if (
            not isinstance(candidates, tuple)
            or not candidates
            or any(not isinstance(c, EATangentCandidate) for c in candidates)
        ):
            raise ValueError("explicit immutable EA-tangent candidate roster required")
        require_names(tuple(c.name for c in candidates), "candidate names")
        settings_hashes = tuple(config_digest(asdict(c.support)) for c in candidates)
        if len(set(settings_hashes)) != len(settings_hashes):
            raise ValueError("duplicate candidate settings")
        if type(maximum_classical_fits) is not int or not 1 <= maximum_classical_fits <= 256:
            raise ValueError("engineering classical-fit ceiling must be between 1 and 256")
        config: dict[str, Any] = config_snapshot(protocol_config)
        shots = validate_protocol(config)
        if type(shots_per_class) is not int or shots_per_class not in shots:
            raise ValueError("shots must belong to the audited protocol")
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
        self._selection_record = config_snapshot(selection_record)
        self._assets = dict(profile_a_manifests)
        self._candidates = candidates
        self._shots = shots_per_class
        self._maximum = maximum_classical_fits
        self._episodes = {
            name: nested_episode(c, shots=shots, protocol_sha256=config_digest(config))
            for name, c in self._catalogs.items()
        }
        self._contract: dict[str, Any] = {
            "method": "ea_tangent_lr",
            "dataset": self._selection.dataset,
            "outer_target": outer_target,
            "selection": asdict(self._selection),
            "protocol_sha256": config_digest(config),
            "profile_a_manifests": self._assets,
            "candidates": [asdict(c) for c in candidates],
            "shots_per_class": shots_per_class,
            "maximum_classical_fits": maximum_classical_fits,
            "source_policy": (
                "classical_refit_inside_each_prediction; "
                "all_non_target_subjects_minus_inner_validation"
            ),
            "final_fit": "not_applicable_classical_recipe_declares_settings_not_weights",
            "seed": None,
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
                "scikit-learn": version("scikit-learn"),
                "device": "cpu",
                "dtype": "float64",
            },
        }

    @property
    def contract(self) -> dict[str, Any]:
        return config_snapshot(self._contract)

    def _candidate(self, name: str) -> EATangentCandidate:
        for candidate in self._candidates:
            if candidate.name == name:
                return candidate
        raise ValueError("candidate is outside the fixed roster")

    def _admit(self, fits: int) -> None:
        if fits > self._maximum:
            raise ValueError("requested work exceeds the declared classical-fit ceiling")

    def _fold(self, candidate: EATangentCandidate, subject: str) -> dict[str, Any]:
        runner = BCIAnchorManifestRunner(
            self._root,
            self._config,
            tuple(self._catalogs.values()),
            self._selection_record,
            self._assets,
            outer_target=self._selection.target_subject,
            validation_subject=subject,
        )
        prediction = runner.predict_validation(
            envelope("episode_manifest", self._episodes[subject].payload()),
            shots_per_class=self._shots,
            settings=candidate.support,
        )
        if prediction.method != "ea_tangent_lr" or prediction.source_state_sha256 is not None:
            raise ValueError("inner validation must use the classical EA-tangent recipe")
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
            "anchor_fit": prediction.fit,
            "episode_sha256": prediction.episode_sha256,
            "settings_sha256": config_digest(asdict(candidate.support)),
            "support_trial_ids": prediction.support_trial_ids,
            "query_trial_ids": prediction.query_trial_ids,
            "source_subjects": prediction.source_subjects,
            "input_identities": prediction.input_identities,
            "fitted_state_sha256": prediction.fitted_state_sha256,
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
                        "purpose": "bounded_ea_tangent_selection",
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
        self._admit(1)
        fold = self._fold(candidate, validation_subject)
        return self._evidence({"complete": False, "folds": [fold], "selected_candidate": None})

    def run_selection(self) -> SelectedEATangent:
        """Complete every candidate/fold and declare one winning settings roster.

        No partial-result import or resume exists. Failure returns no winner.
        The winner is declared settings, not fitted weights: every future
        prediction refits the classical recipe from its own permitted inputs.
        """
        self._admit(len(self._selection.inner_folds) * len(self._candidates))
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
        return SelectedEATangent(
            winner,
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
                    "final_fit_performed": False,
                    "outer_target_predictions_performed": False,
                }
            ),
        )
