"""Verify full control cohorts against their actual code, inputs and environment."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, cast

import numpy as np
from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]

from core.config import config_digest, load_toml
from core.provenance import source_fingerprint

CONTROL_NAMES = ("gate_a_shuffle.toml", "pre_cue_control.toml")


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def environment_identity() -> dict[str, Any]:
    # Editable metadata can be discovered twice when the repository is sys.path[0].
    # Deduplicate identical identities only; differing versions remain distinct.
    # Emit JSON-native lists: an in-memory tuple here can never equal the
    # parsed copy of its own published context, so audits that compare the
    # saved context byte-for-byte against a rebuild would always differ.
    packages = sorted(
        [name, version]
        for name, version in {
            (distribution.metadata["Name"].lower(), distribution.version)
            for distribution in importlib.metadata.distributions()
            if distribution.metadata["Name"]
        }
    )
    executable = shutil.which("nvidia-smi")
    if executable is None:
        raise ValueError("NVIDIA device/driver identity is unavailable for CUDA controls")
    result = subprocess.run(
        [executable, "--query-gpu=uuid,name,driver_version", "--format=csv,noheader"],
        capture_output=True, text=True, check=True, timeout=5,
    )
    devices = sorted(line.strip() for line in result.stdout.splitlines() if line.strip())
    if not devices:
        raise ValueError("CUDA control device inventory is empty")
    return {
        "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
        "packages": packages, "nvidia_devices_and_driver": devices,
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                        "CUDA_VISIBLE_DEVICES", "CUBLAS_WORKSPACE_CONFIG")
        },
    }


def build_context(root: Path) -> dict[str, Any]:
    config = load_toml(root / "configs/source_bound_controls.toml")
    if config != {
        "controls": {"configurations": list(CONTROL_NAMES),
                     "output_directory": "runs/source_bound_controls", "device": "cuda"},
        "runtime": {"minimum_free_memory_gib": 10.0, "stop_below_free_memory_gib": 4.0,
                    "minimum_free_disk_gib": 10.0},
    }:
        raise ValueError("source-bound controls must preserve their full protocol and guards")
    specifications = {name: cast(dict[str, Any], load_toml(root / "configs" / name))
                      for name in CONTROL_NAMES}
    for name, specification in specifications.items():
        gate = specification["gate_a"]
        expected_seeds = [11] if name == CONTROL_NAMES[0] else [11, 23, 37, 53]
        if gate["subjects"] != list(range(1, 10)) or gate["seeds"] != expected_seeds:
            raise ValueError("all original nine-subject control cohorts and seeds are required")
    raw = "data/raw/moabb/MNE-bnci-data/~bci/database/001-2014"
    names = [f"{raw}/A{subject:02d}{session}.mat"
             for subject in range(1, 10) for session in ("T", "E")]
    names.extend(f"data/processed/bci_iv_2a/pre_cue_control/subject_{subject:02d}.npz"
                 for subject in range(1, 10))
    return {
        "schema": 1, "source_sha256": source_fingerprint(root), "configuration": config,
        "model_configuration": load_toml(root / "configs/eegnet.toml"),
        "specifications": specifications,
        "inputs": {name: file_digest(root / name) for name in names},
        "environment": environment_identity(),
    }


def expected_units(context: dict[str, Any]) -> list[tuple[str, int, int]]:
    return [(name, subject, seed)
            for name in CONTROL_NAMES
            for subject in context["specifications"][name]["gate_a"]["subjects"]
            for seed in context["specifications"][name]["gate_a"]["seeds"]]


def unit_name(name: str, subject: int, seed: int) -> str:
    return f"{Path(name).stem}_subject_{subject:02d}_seed_{seed}.json"


def resolved_config(context: dict[str, Any], unit: tuple[str, int, int]) -> dict[str, Any]:
    name, subject, seed = unit
    return {"model_configuration": context["model_configuration"],
            "control": context["specifications"][name]["gate_a"],
            "context_sha256": config_digest(context), "subject": subject, "seed": seed,
            "device": context["configuration"]["controls"]["device"]}


def validate_unit(payload: dict[str, Any], context: dict[str, Any],
                  unit: tuple[str, int, int]) -> float:
    name, subject, seed = unit
    expected = resolved_config(context, unit)
    record = payload["record"]
    if (
        payload["schema"] != 1 or payload["context_sha256"] != config_digest(context)
        or payload["unit"] != {"configuration": name, "subject": subject, "seed": seed}
        or record["config"] != expected or record["config_sha256"] != config_digest(expected)
        or record["seed"] != seed or record["source_sha256"] != context["source_sha256"]
        or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", record["git_commit"]) is None
        or type(record["git_dirty"]) is not bool
        or record["dataset"] != "BNCI2014-001"
        or record["fold"] != f"{Path(name).stem}:subject-{subject}"
        or datetime.fromisoformat(record["timestamp_utc"]).tzinfo is None
    ):
        raise ValueError("control record identity, configuration or source differs")
    gate = expected["control"]
    base = context["model_configuration"]
    training = {**base["training"], **gate["training"]}
    labels = np.asarray(payload["input_labels"], dtype=str)
    sessions = np.asarray(payload["input_sessions"], dtype=str)
    classes = sorted(gate["included_labels"])
    if (labels.ndim != 1 or sessions.shape != labels.shape or set(labels) != set(classes)
            or Counter(labels.tolist()) != {label: 144 for label in classes}
            or set(sessions) != {base["data"]["train_session"], base["data"]["test_session"]}):
        raise ValueError("invalid control input label/session inventory")
    development = np.flatnonzero(sessions == base["data"]["train_session"])
    query = np.flatnonzero(sessions == base["data"]["test_session"])
    train, validation = train_test_split(
        development, test_size=training["validation_fraction"], random_state=seed,
        shuffle=True, stratify=labels[development],
    )
    split = {"train": sorted(train.tolist()), "validation": sorted(validation.tolist()),
             "test": query.tolist()}
    if payload["split"] != split:
        raise ValueError("control split does not match independent reconstruction")
    targets = np.asarray([classes.index(label) for label in labels], dtype=np.int64)
    if gate.get("shuffle_development_labels", False):
        development_order = np.asarray(split["train"] + split["validation"])
        shuffled = targets[development_order].copy()
        np.random.default_rng(seed).shuffle(shuffled)
        targets[development_order] = shuffled
    if payload["training_targets"] != targets.tolist():
        raise ValueError("training labels or untouched query labels differ")
    result = payload["result"]
    history = result["history"]
    count = result["epochs_completed"]
    if (type(count) is not int or not 1 <= count <= training["epochs"] or len(history) != count
            or any(row["epoch"] != index + 1 for index, row in enumerate(history))
            or any(not math.isfinite(row[key]) or row[key] < 0 for row in history
                   for key in ("train_loss", "validation_loss"))):
        raise ValueError("invalid full-protocol training history")
    best = min(range(count), key=lambda index: history[index]["validation_loss"])
    running_best = math.inf
    stale = 0
    for index, row in enumerate(history):
        if row["validation_loss"] < running_best:
            running_best, stale = row["validation_loss"], 0
        else:
            stale += 1
        if stale >= training["early_stopping_patience"] and index != count - 1:
            raise ValueError("training continued beyond its first early-stopping boundary")
    if (result["best_epoch"] != best + 1
            or result["best_validation_loss"] != history[best]["validation_loss"]
            or (count < training["epochs"]
                and count != best + 1 + training["early_stopping_patience"])
            or result["device"] != expected["device"]
            or result["split_counts"] != {key: len(value) for key, value in split.items()}):
        raise ValueError("control checkpoint, stopping rule or device differs")
    true = labels[query].tolist()
    predicted = payload["query_predictions"]
    if (payload["query_targets"] != true or not isinstance(predicted, list)
            or len(predicted) != len(true) or any(value not in classes for value in predicted)):
        raise ValueError("invalid or changed control query predictions/targets")
    counts = Counter(true)
    matrix = [[sum(a == left and b == right for a, b in zip(true, predicted, strict=True))
               for right in classes] for left in classes]
    if any(counts[label] != 72 for label in classes):
        raise ValueError("the full original query session must retain 72 trials per class")
    balanced = float(mean(matrix[index][index] / counts[label]
                          for index, label in enumerate(classes)))
    observed = sum(matrix[index][index] for index in range(len(classes))) / len(query)
    expected_chance = sum(counts[label] * sum(row[index] for row in matrix)
                          for index, label in enumerate(classes)) / len(query)**2
    kappa = (observed - expected_chance) / (1 - expected_chance)
    actual = result["metrics"]
    if (actual["labels"] != classes or actual["confusion_matrix"] != matrix
            or actual["class_support"] != dict(counts)):
        raise ValueError("control confusion/class counts differ from saved predictions")
    for key, value in (("balanced_accuracy", balanced), ("cohen_kappa", kappa)):
        if not all(math.isclose(container[key], value, rel_tol=1e-10, abs_tol=1e-10)
                   for container in (actual, record["metrics"])):
            raise ValueError("control metrics differ from independently counted predictions")
    resources = payload["resources"]
    if (resources["minimum_observed_free_memory_gib"] < 4.0
            or not math.isfinite(resources["minimum_observed_free_memory_gib"])
            or type(resources["model_call_checks"]) is not int
            or resources["model_call_checks"] < 1
            or not math.isfinite(resources["maximum_observed_process_rss_gib"])
            or resources["maximum_observed_process_rss_gib"] <= 0):
        raise ValueError("control resource guard evidence is incomplete")
    elapsed = record["metrics"]["training_and_prediction_seconds"]
    if not math.isfinite(elapsed) or elapsed <= 0:
        raise ValueError("invalid control elapsed time")
    identity = payload["signal_identity"]
    samples = 1001 if name == CONTROL_NAMES[0] else 128
    if (identity["shape"] != [len(labels), 22, samples]
            or identity["dtype"] != "float32"
            or re.fullmatch(r"[0-9a-f]{64}", identity["sha256"]) is None):
        raise ValueError("control signal identity is incomplete")
    return balanced


def audit_context(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    key = config_digest(context)
    directory = root / "runs/source_bound_controls" / key
    units = expected_units(context)
    expected_names = {unit_name(*unit) for unit in units}
    unexpected = sorted(path.name for path in directory.glob("*.json")
                        if path.name not in expected_names and path.name != "context.json")
    invalid: dict[str, str] = {}
    context_path = directory / "context.json"
    try:
        if config_digest(json.loads(context_path.read_text("utf-8"))) != key:
            raise ValueError("saved context differs from current source, inputs or environment")
    except FileNotFoundError:
        if directory.is_dir():
            invalid["context.json"] = "control directory has no context record"
    except (OSError, ValueError, TypeError) as error:
        invalid["context.json"] = str(error)
    missing = []
    files = {}
    scores: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for unit in units:
        path = directory / unit_name(*unit)
        if not path.is_file():
            missing.append(path.name)
            continue
        try:
            score = validate_unit(json.loads(path.read_text("utf-8")), context, unit)
            scores[unit[0]][unit[1]].append(score)
            files[path.name] = file_digest(path)
        except (OSError, ValueError, KeyError, TypeError, IndexError, ZeroDivisionError) as error:
            invalid[path.name] = str(error)
    controls = {}
    for name in CONTROL_NAMES:
        gate = context["specifications"][name]["gate_a"]
        means = {str(subject): mean(values) for subject, values in scores[name].items()}
        complete = (set(means) == {str(subject) for subject in gate["subjects"]}
                    and all(len(values) == len(gate["seeds"]) for values in scores[name].values()))
        limit = gate.get("negative_control_max_accuracy", gate.get("control_max_accuracy"))
        controls[name] = {"complete": complete, "subject_means": means,
                          "mean": mean(means.values()) if means else None, "limit": limit,
                          "passed": complete and mean(means.values()) <= limit}
    complete = not missing and not invalid and not unexpected and len(files) == 45
    return {"complete": complete,
            "passed": complete and all(c["passed"] for c in controls.values()),
            "context_sha256": key, "source_sha256": context["source_sha256"],
            "expected_records": 45, "valid_records": len(files), "invalid_records": invalid,
            "missing_records": missing, "unexpected_records": unexpected, "controls": controls,
            "record_snapshot_sha256": config_digest(files)}


def verify_current_controls(root: Path) -> dict[str, Any]:
    try:
        return audit_context(root, build_context(root))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        return {"complete": False, "passed": False, "error": str(error), "controls": {}}
