"""Bounded, no-training audit of real Phase II partition eligibility and immutable manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from core.config import config_digest, load_toml
from core.provenance import capture_source
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import envelope, write_once


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("configuration path escapes the project")
    return path


def read_catalog(
    path: Path,
    *,
    dataset: str,
    classes: tuple[str, ...],
    threshold: float,
    preprocessing_sha256: str,
) -> tuple[TrialCatalog, dict[str, Any]]:
    """Read one artifact at a time; apply the unchanged frozen amplitude rule."""
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("artifact threshold must be positive and finite")
    before = file_digest(path)
    with np.load(path, allow_pickle=False) as data:
        labels = np.asarray(data["labels"])
        sessions = np.asarray(data["sessions"])
        runs = np.asarray(data["runs"])
        indices = np.asarray(data["trial_indices"])
        signals = np.asarray(data["signals"])
        channels = tuple(str(x) for x in data["channel_names"])
        size = len(labels)
        if (
            labels.shape != (size,)
            or sessions.shape != (size,)
            or runs.shape != (size,)
            or indices.shape != (size,)
            or not np.issubdtype(indices.dtype, np.integer)
            or signals.ndim != 3
            or signals.shape[:2] != (size, len(channels))
            or signals.shape[2] < 1
            or len(set(channels)) != len(channels)
            or not channels
            or not np.isfinite(signals).all()
        ):
            raise ValueError("invalid artifact signal/provenance dimensions or values")
        retained = np.max(np.abs(signals), axis=(1, 2)) <= threshold
        kept = np.flatnonzero(retained)
        # JSON tuple encoding avoids collisions from separator-containing session/run names.
        ids = tuple(
            json.dumps([str(sessions[i]), str(runs[i]), int(indices[i])], separators=(",", ":"))
            for i in kept
        )
        selected_labels = tuple(str(labels[i]) for i in kept)
        metadata: dict[str, Any] = {
            "input_trials": size,
            "retained_trials": len(kept),
            "rejected_trials": size - len(kept),
            "retained_class_counts": dict(Counter(selected_labels)),
            "channel_names": channels,
            "samples_per_trial": signals.shape[2],
            "retained_artifact_indices": kept.tolist(),
            "artifact_sha256": before,
        }
    if file_digest(path) != before:
        raise ValueError("input artifact changed while being audited")
    return TrialCatalog(
        dataset,
        path.stem,
        ids,
        selected_labels,
        classes,
        before,
        preprocessing_sha256,
    ), metadata


def validate_protocol(config: dict[str, Any]) -> tuple[int, ...]:
    settings = config["protocol"]
    if (
        type(settings["schema_version"]) is not int
        or settings["schema_version"] != 1
        or type(settings["phase"]) is not int
        or settings["phase"] != 2
        or settings["scientific_mode"] != "exploratory"
        or settings["support_policy"] != "nested_fixed_earliest"
        or settings["query_policy"] != "all_retained_after_maximum_support"
        or settings["inner_validation"] != "source_subject_loso"
        or settings["support_draw_seed"] != "not_applicable_fixed_order"
        or settings["experiment_frozen"] is not False
    ):
        raise ValueError("this preparation audit requires the unfrozen exploratory v2 protocol")
    raw = settings["shots_per_class"]
    if not isinstance(raw, list) or not raw or any(type(n) is not int or n < 1 for n in raw):
        raise ValueError("shot levels must be positive integers")
    shots = tuple(raw)
    maximum = settings["maximum_support_per_class"]
    if tuple(sorted(set(shots))) != shots or type(maximum) is not int or maximum != shots[-1]:
        raise ValueError("shot levels must increase to the declared maximum support")
    seeds = settings["model_seeds"]
    if (
        not isinstance(seeds, list)
        or not seeds
        or any(type(n) is not int or n < 0 for n in seeds)
        or len(set(seeds)) != len(seeds)
    ):
        raise ValueError("model seeds must be unique nonnegative integers")
    return shots


def audit(root: Path, config_path: Path, *, verify_only: bool = False) -> dict[str, Any]:
    config: dict[str, Any] = load_toml(config_path)
    shots = validate_protocol(config)
    config_sha = config_digest(config)
    threshold_path = inside(root, config["preparation"]["threshold_config"])
    thresholds: dict[str, Any] = load_toml(threshold_path)
    threshold_sha = file_digest(threshold_path)
    source = capture_source(root)
    destination = inside(root, config["preparation"]["output_root"])
    if not destination.is_relative_to((root / "runs" / "phase2").resolve()):
        raise ValueError("Phase II output must remain under runs/phase2")
    output = destination / config_sha / source.source_sha256
    report: dict[str, Any] = {
        "purpose": "partition_preparation_not_encoder_readiness_or_experiment_result",
        "experiment_frozen": False,
        "scientific_mode": "exploratory",
        "gate_a_signed": False,
        "config": config,
        "config_sha256": config_sha,
        "threshold_config_sha256": threshold_sha,
        "source": asdict(source),
        "datasets": {},
    }

    def publish(path: Path, payload: dict[str, Any], kind: str) -> None:
        record = envelope(kind, payload)
        if verify_only:
            if json.loads(path.read_text("utf-8")) != record:
                raise ValueError(f"saved manifest differs from reconstructed inputs: {path}")
        else:
            write_once(path, record, output_root=destination)

    for dataset, settings in config["datasets"].items():
        directory = inside(root, settings["artifact_directory"])
        paths = tuple(sorted(directory.glob("subject_*.npz")))
        expected_count = settings["expected_subjects"]
        if type(expected_count) is not int or expected_count < 3 or len(paths) != expected_count:
            raise ValueError(f"{dataset}: expected {expected_count} artifacts, found {len(paths)}")
        classes = tuple(settings["classes"])
        threshold = thresholds["datasets"][dataset]["artifact_threshold_volts"]
        preprocessing_sha = config_digest(
            {
                "profile_identity": config["preparation"]["profile_identity"],
                "threshold_config_sha256": threshold_sha,
                "dataset": dataset,
                "threshold": threshold,
            }
        )
        catalogs = []
        details: dict[str, Any] = {}
        for path in paths:
            catalog, metadata = read_catalog(
                path,
                dataset=dataset,
                classes=classes,
                threshold=threshold,
                preprocessing_sha256=preprocessing_sha,
            )
            catalogs.append(catalog)
            details[catalog.subject] = metadata
        eligible: dict[str, Any] = {}
        excluded: dict[str, str] = {}
        for catalog in catalogs:
            try:
                episode = nested_episode(catalog, shots=shots, protocol_sha256=config_sha)
            except ValueError as error:
                excluded[catalog.subject] = str(error)
                continue
            selection = source_selection(catalogs, target=catalog.subject)
            first = episode.partitions[0]
            eligible[catalog.subject] = {
                "episode_sha256": episode.sha256,
                "selection_sha256": selection.sha256,
                "query_trials": len(first.query_indices),
                "query_class_counts": dict(Counter(catalog.labels[i] for i in first.query_indices)),
                "maximum_support_trials": len(episode.partitions[-1].support_indices),
            }
            publish(
                output / dataset / f"{catalog.subject}.episode.json",
                episode.payload(),
                "episode_manifest",
            )
            publish(
                output / dataset / f"{catalog.subject}.selection.json",
                asdict(selection),
                "source_selection",
            )
        report["datasets"][dataset] = {
            "input_subjects": len(catalogs),
            "eligible_subjects": len(eligible),
            "excluded_subjects": excluded,
            "eligible": eligible,
            "artifacts": details,
            "source_cohort_policy": "all_declared_subjects_except_outer_target",
            "note": "support-ineligible targets remain source subjects; query labels never tune",
        }
    if source.source_sha256 != capture_source(root).source_sha256:
        raise ValueError("source changed during preparation audit")
    publish(output / "summary.json", report, "protocol_audit")
    return {
        "report": str(output / "summary.json"),
        "verified_only": verify_only,
        "datasets": {
            name: {
                key: row[key]
                for key in ("input_subjects", "eligible_subjects", "excluded_subjects")
            }
            for name, row in report["datasets"].items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/phase2/protocol.toml"))
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(audit(root, args.config, verify_only=args.verify_only), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
