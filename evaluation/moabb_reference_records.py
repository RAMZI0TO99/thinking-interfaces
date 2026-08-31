"""Independent arithmetic and split checks for full reference fold records."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import asdict
from datetime import datetime
from typing import Any

from core.config import config_digest
from evaluation.moabb_reference_plan import ReferenceUnit


def _indices(value: Any, *, count: int) -> list[int]:
    if (
        not isinstance(value, list)
        or not value
        or any(type(item) is not int or not 0 <= item < count for item in value)
        or sorted(set(value)) != value
    ):
        raise ValueError("reference indices must be sorted, unique and in range")
    return value


def binary_auc(targets: list[int], probabilities: list[list[float]]) -> float:
    """Pairwise definition, independent of the training library's metric call."""
    if (
        len(targets) != len(probabilities)
        or set(targets) != {0, 1}
        or any(type(target) is not int for target in targets)
    ):
        raise ValueError("binary reference score needs both classes and aligned predictions")
    for row in probabilities:
        if (
            not isinstance(row, list)
            or len(row) != 2
            or any(
                type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1 for p in row
            )
            or not math.isclose(sum(row), 1.0, abs_tol=1e-6)
        ):
            raise ValueError("invalid reference probability row")
    positive = [row[1] for target, row in zip(targets, probabilities, strict=True) if target == 1]
    negative = [row[1] for target, row in zip(targets, probabilities, strict=True) if target == 0]
    wins = sum(float(p > n) + 0.5 * float(p == n) for p in positive for n in negative)
    return wins / (len(positive) * len(negative))


def validate_reference_record(
    payload: Mapping[str, Any],
    *,
    unit: ReferenceUnit,
    resolved_config: Mapping[str, Any],
    execution_sha256: str,
    raw_hashes: Mapping[str, str],
) -> float:
    """Validate a full fit, not just the presence of a score or success flag."""
    identity = ReferenceUnit(**payload["unit"])
    if identity != unit or payload["unit"] != asdict(unit):
        raise ValueError("reference fold identity mismatch")
    if payload["execution_sha256"] != execution_sha256:
        raise ValueError("reference execution code changed; preserve and review old records")
    record, result = payload["record"], payload["result"]
    if record["config"] != resolved_config or record["config_sha256"] != config_digest(
        resolved_config
    ):
        raise ValueError("reference RunRecord configuration mismatch")
    if (
        type(record["seed"]) is not int
        or record["seed"] != unit.model_seed
        or record["fold"] != unit.key
        or record["dataset"] != "bci_iv_2a"
    ):
        raise ValueError("reference RunRecord identity mismatch")
    if (
        re.fullmatch(r"[0-9a-f]{40}", record["git_commit"]) is None
        or re.fullmatch(r"[0-9a-f]{64}", record["source_sha256"]) is None
        or record["git_dirty"] is not False
        or datetime.fromisoformat(record["timestamp_utc"]).utcoffset() is None
    ):
        raise ValueError("reference fit requires committed, timestamped source provenance")
    if (
        result["fold_executed"] is not True
        or result["reference_reproduction_passed"] is not False
        or result["resource_stop"] is not False
        or result["restore_best_weights"] is not False
        or result["raw_path_redirect_only"] is not True
    ):
        raise ValueError("reference fit status or protocol mismatch")
    if result["raw_file_sha256"] != raw_hashes:
        raise ValueError("reference raw input hashes changed")
    targets = result["session_targets"]
    if (
        not isinstance(targets, list)
        or len(targets) != 144
        or any(type(value) is not int or value not in (0, 1) for value in targets)
        or targets.count(0) != 72
        or targets.count(1) != 72
        or result["classes"] != ["left_hand", "right_hand"]
    ):
        raise ValueError("reference session labels/class counts mismatch")
    if (
        type(result["session_trials"]) is not int
        or result["session_trials"] != 144
        or result["native_epoch_shape"] != [144, 22, 1001]
        or len(result["channel_names"]) != 22
        or len(set(result["channel_names"])) != 22
    ):
        raise ValueError("reference epoch/channel inventory mismatch")
    offset = 0 if unit.session == "0train" else 144
    original = _indices(result["session_original_indices"], count=288)
    if original != list(range(offset, offset + 144)):
        raise ValueError("reference session selection mismatch")
    query = _indices(result["query_indices"], count=144)
    optimization = _indices(result["optimization_indices"], count=144)
    validation = _indices(result["validation_indices"], count=144)
    from sklearn.model_selection import StratifiedKFold  # type: ignore[import-untyped]

    splits = StratifiedKFold(5, shuffle=True, random_state=42).split(range(144), targets)
    train_expected, query_expected = list(splits)[unit.fold_index]
    split_at = math.floor(len(train_expected) * 0.8)
    if (
        query != query_expected.tolist()
        or optimization != train_expected[:split_at].tolist()
        or validation != train_expected[split_at:].tolist()
    ):
        raise ValueError("reference outer CV or final-20-percent validation split mismatch")
    if result["query_targets"] != [targets[index] for index in query]:
        raise ValueError("reference query targets do not match the session labels")
    if result["transformed_query_shape"] != [len(query), 22, 513]:
        raise ValueError("reference resampling/inclusive endpoint mismatch")
    if re.fullmatch(r"[0-9a-f]{64}", result["transformed_query_sha256"]) is None:
        raise ValueError("reference transformed input hash missing")
    epochs = result["epochs_completed"]
    stopped = result["early_stopping_epoch"]
    if (
        type(epochs) is not int
        or not 76 <= epochs <= 300
        or type(stopped) is not int
        or not 0 <= stopped < 300
        or (epochs < 300 and stopped != epochs - 1)
        or (epochs == 300 and stopped not in (0, 299))
    ):
        raise ValueError("incomplete or incorrectly stopped full reference training")
    history = result["history"]
    if not isinstance(history, Mapping) or not {"loss", "val_loss"} <= set(history):
        raise ValueError("reference training history missing")
    for values in history.values():
        if (
            not isinstance(values, list)
            or len(values) != epochs
            or any(
                type(value) not in (int, float) or not math.isfinite(value) or value < 0
                for value in values
            )
        ):
            raise ValueError("invalid reference training history")
    best, waiting, expected_stop = math.inf, 0, None
    for epoch, loss in enumerate(history["val_loss"]):
        waiting += 1
        if loss < best:
            best, waiting = loss, 0
        elif waiting >= 75 and epoch > 0:
            expected_stop = epoch
            break
    if expected_stop is None:
        if epochs != 300 or stopped != 0:
            raise ValueError("reference history does not justify early stopping")
    elif expected_stop != epochs - 1 or stopped != expected_stop:
        raise ValueError("reference history violates the configured early-stopping rule")
    auc = binary_auc(result["query_targets"], result["query_probabilities"])
    for score in (result["roc_auc"], record["metrics"]["roc_auc"]):
        if type(score) not in (int, float) or not math.isclose(
            score, auc, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("reference ROC-AUC does not match saved predictions")
    for timing in ("fit_seconds", "prediction_seconds"):
        value = result[timing]
        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or value <= 0
            or record["metrics"][timing] != value
        ):
            raise ValueError("reference timing evidence mismatch")
    return auc
