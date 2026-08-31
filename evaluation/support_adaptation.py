"""Separate EEGNet source training and support-only fine-tuning readiness baseline."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import torch

from adaptation.episodic import adapt_torch_model, named_parameter_snapshot, parameters_unchanged
from core.metrics import classification_report
from core.splits import earliest_balanced_episode
from evaluation.baselines import BraindecodeClassifier, TorchTrainingConfig
from evaluation.benchmark import DatasetMatrix
from evaluation.falsification import array_digest


def source_then_support_fold(
    matrix: DatasetMatrix,
    *,
    target_subject: str,
    seed: int,
    shots_per_class: int,
    training: TorchTrainingConfig,
    adaptation_steps: int,
    adaptation_learning_rate: float,
) -> dict[str, Any]:
    source = np.flatnonzero(matrix.subjects != target_subject)
    target = np.flatnonzero(matrix.subjects == target_subject)
    if not source.size or not target.size:
        raise ValueError("source and target subjects are required")
    episode = earliest_balanced_episode(
        matrix.labels[target].tolist(), subject_id=target_subject, shots_per_class=shots_per_class
    )
    support = target[np.asarray(episode.support_indices, dtype=np.int64)]
    query = target[np.asarray(episode.query_indices, dtype=np.int64)]
    if np.intersect1d(source, target).size or np.intersect1d(support, query).size:
        raise ValueError("source/target or support/query overlap")
    names = tuple(sorted(set(matrix.labels.tolist())))
    lookup = {name: index for index, name in enumerate(names)}
    labels = np.asarray([lookup[name] for name in matrix.labels], dtype=np.int64)
    classifier = BraindecodeClassifier(
        "eegnet",
        channels=matrix.signals.shape[1],
        classes=len(names),
        samples=matrix.signals.shape[2],
        sampling_rate_hz=matrix.sampling_rate_hz,
        seed=seed,
        training=training,
    )
    started = time.perf_counter()
    classifier.fit(matrix.signals[source], labels[source])
    source_fit_seconds = time.perf_counter() - started
    if classifier.model is None:
        raise RuntimeError("source training returned no model")
    before = classifier.predict_proba(matrix.signals[query])
    base_model = classifier.model
    base_snapshot = named_parameter_snapshot(base_model)
    started = time.perf_counter()
    adapted = adapt_torch_model(
        base_model,
        torch.from_numpy(np.ascontiguousarray(matrix.signals[support] * training.input_scale)),
        torch.from_numpy(labels[support]),
        steps=adaptation_steps,
        learning_rate=adaptation_learning_rate,
        device=training.device or "cpu",
    )
    adaptation_seconds = time.perf_counter() - started
    if not parameters_unchanged(base_snapshot, base_model.named_parameters()):
        raise RuntimeError("adaptation changed the shared source model")
    changed = not parameters_unchanged(base_snapshot, adapted.model.named_parameters())
    classifier.model = adapted.model
    started = time.perf_counter()
    after = classifier.predict_proba(matrix.signals[query])
    prediction_seconds = time.perf_counter() - started
    for probabilities in (before, after):
        if not np.isfinite(probabilities).all():
            raise RuntimeError("nonfinite baseline predictions")
    before_report = classification_report(
        matrix.labels[query].tolist(),
        np.asarray(names)[before.argmax(axis=1)].tolist(),
        labels=names,
    )
    report = classification_report(
        matrix.labels[query].tolist(),
        np.asarray(names)[after.argmax(axis=1)].tolist(),
        labels=names,
    )
    metrics = {
        "support_adaptation_schema_version": 1.0,
        "balanced_accuracy": report.balanced_accuracy,
        "cohen_kappa": report.cohen_kappa,
        "before_balanced_accuracy": before_report.balanced_accuracy,
        "before_cohen_kappa": before_report.cohen_kappa,
        "source_fit_seconds": source_fit_seconds,
        "adaptation_seconds": adaptation_seconds,
        "prediction_seconds": prediction_seconds,
        "source_trials": float(len(source)),
        "support_trials": float(len(support)),
        "query_trials": float(len(query)),
        "adaptation_steps": float(len(adapted.losses)),
        "trainable_parameters": float(adapted.trainable_parameters),
        "parameters_changed": float(changed),
        "base_model_unchanged": 1.0,
        "maximum_probability_change": float(np.max(np.abs(after - before))),
        "source_target_disjoint": 1.0,
        "support_query_disjoint": 1.0,
    }
    for index, label in enumerate(names):
        metrics[f"class_support_{label}"] = float(report.class_support[label])
        for other, predicted in enumerate(names):
            metrics[f"confusion_true_{label}_pred_{predicted}"] = float(
                report.confusion_matrix[index][other]
            )
    return {
        "metrics": metrics,
        "split": {
            "source_indices_sha256": array_digest(source),
            "support_indices_sha256": array_digest(support),
            "query_indices_sha256": array_digest(query),
        },
    }
