"""Fixed, ordered A01 preprocessing bridge; never changes the frozen benchmark."""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
from numpy.typing import NDArray
from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]

from core.config import config_digest, load_toml
from core.gpu_cooling import CoolingPolicy, load_cooling_policy
from core.provenance import capture_source
from core.run_record import RunRecord
from evaluation.source_bound_controls import environment_identity, file_digest
from scripts.audit_profile_alignment import CHANNELS, LABELS, cue_indices, reconstruct_epochs
from scripts.diagnose_profile_units import (
    atomic_json,
    guarded_constructor,
    make_resource_guard,
    validate_predictions,
)

ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "profile_b_original_units", "profile_b_microvolts", "a_band", "a_reference",
    "a_rate", "a_baseline", "profile_a_microvolts",
)
REFERENCE = "runs/profile_units_diagnostic/" + (
    "db1103e8d1a58205468e9565f2843790639b2fd10ad4493888d17451c0987b03"
)
REFERENCE_HASHES = {
    NAMES[0]: "c5390bf791045ebfc11494cdf794b4f252e7781b2740c045ff1508fd710688d1",
    NAMES[1]: "eb25fb982479057e6bd89f0635e1b45e0afb8c21ed62ad968ca304b6629e3395",
    NAMES[-1]: "d408d6b6d1e3a56e28bbbf65c4ee81772ef99c48db8602f6f165cbe7d44b3229",
}


def bridge_cooling_policy() -> CoolingPolicy:
    return load_cooling_policy(ROOT / "configs/runtime_limits.toml")


def validate_config(config: dict[str, Any], original: dict[str, Any]) -> None:
    expected = [
        {"name": name, "hz": 200.0 if i < 4 else 128.0, "car": i >= 3,
         "baseline": i >= 5, "unit_volts": 1.0 if i == 6 else 0.0001,
         "input_scale": 1.0 if i == 0 else (1000000.0 if i == 6 else 100.0),
         "saved_b": i < 2}
        for i, name in enumerate(NAMES)
    ]
    if config != {
        "comparison_config": "configs/profile_comparison.toml",
        "output_directory": "runs/profile_bridge_diagnostic", "conditions": expected,
        "runtime": {"device": "cuda", "cpu_threads": 2, "minimum_free_memory_gib": 6.0,
                    "stop_below_free_memory_gib": 4.0, "minimum_free_gpu_gib": 1.0},
    }:
        raise ValueError("preserve all seven ordered conditions, separate output and guards")
    if original != {
        "comparison": {"subject": 1, "seed": 11, "train_session": "0train",
                       "test_session": "1test", "epochs": 20, "batch_size": 64,
                       "learning_rate": 0.001, "weight_decay": 0.0,
                       "validation_fraction": 0.2, "early_stopping_patience": 5},
        "profile_a": {"artifact": "data/processed/bci_iv_2a/profile_a/subject_01.npz",
                      "sampling_rate_hz": 128.0, "input_scale": 1000000.0},
        "profile_b": {"artifact": "data/processed/bci_iv_2a/profile_b/subject_01.npz",
                      "sampling_rate_hz": 200.0, "input_scale": 1.0},
    }:
        raise ValueError("preserve the original A01 seed-11 comparison recipe")


def array_identity(signals: NDArray[np.float32]) -> dict[str, Any]:
    value = hashlib.sha256(memoryview(np.ascontiguousarray(signals)).cast("B")).hexdigest()
    return {"shape": list(signals.shape), "dtype": str(signals.dtype),
            "sha256": value}


def independent_split(artifact: dict[str, Any]) -> dict[str, list[int]]:
    labels, sessions = artifact["labels"], artifact["sessions"]
    development = np.flatnonzero(sessions == "0train")
    query = np.flatnonzero(sessions == "1test")
    if (len(labels) != 576 or len(development) != 288 or len(query) != 288
            or sorted(set(labels)) != sorted(LABELS.values())):
        raise ValueError("the complete balanced two-session A01 cohort is required")
    for indices in (development, query):
        if any(np.count_nonzero(labels[indices] == label) != 72 for label in LABELS.values()):
            raise ValueError("every original session must retain 72 trials per class")
    train, validation = train_test_split(development, test_size=0.2, random_state=11,
                                         shuffle=True, stratify=labels[development])
    return {"train": sorted(train.tolist()), "validation": sorted(validation.tolist()),
            "test": query.tolist()}


def reconstruct_condition(
    condition: dict[str, Any], artifacts: dict[str, Any], paths: dict[str, Path], guard: Any,
) -> NDArray[np.float32]:
    if condition["saved_b"]:
        return np.asarray(artifacts["profile_b"]["signals"], dtype=np.float32)
    mne = importlib.import_module("mne")
    scipy_io = importlib.import_module("scipy.io")
    hz = condition["hz"]
    artifact = artifacts["profile_a"]
    output = np.empty((576, 22, round(4 * hz)), dtype=np.float32)
    covered = np.zeros(576, dtype=bool)
    for part, session in (("T", "0train"), ("E", "1test")):
        guard()
        runs = scipy_io.loadmat(paths[f"raw_{part}"], simplify_cells=True)["data"]
        active = [run for run in runs if np.asarray(run["trial"]).size]
        if len(active) != 6:
            raise ValueError("six original task runs required per session")
        for run_index, run in enumerate(active):
            guard()
            selected = np.flatnonzero((artifact["sessions"] == session)
                                      & (artifact["runs"] == str(run_index)))
            trials = np.asarray(run["trial"]).reshape(-1)
            targets = np.asarray(run["y"]).reshape(-1)
            if (float(run["fs"]) != 250.0 or run["X"].shape[1] != 25
                    or len(trials) != 48 or len(selected) != 48 or covered[selected].any()
                    or artifact["trial_indices"][selected].tolist() != list(range(48))
                    or artifact["labels"][selected].tolist()
                    != [LABELS[int(value)] for value in targets]):
                raise ValueError("native and saved trial identities differ")
            volts = np.asarray(run["X"][:, :22].T * 1e-6, dtype=np.float64)
            raw = mne.io.RawArray(volts, mne.create_info(CHANNELS, 250.0, "eeg"), verbose=False)
            raw.filter(l_freq=8.0, h_freq=30.0, method="fir", phase="zero", n_jobs=1,
                       verbose=False)
            if condition["car"]:
                raw.set_eeg_reference(ref_channels="average", projection=False, verbose=False)
            raw.resample(hz, npad="auto", n_jobs=1, verbose=False)
            output[selected] = reconstruct_epochs(
                raw.get_data(), cue_indices(trials, hz), samples=round(4 * hz),
                baseline_samples=round(hz) if condition["baseline"] else 0,
                stored_unit_volts=condition["unit_volts"],
            )
            covered[selected] = True
            del raw, volts
        del runs, active
    if not covered.all() or not np.isfinite(output).all():
        raise ValueError("incomplete or nonfinite reconstructed condition")
    if condition["name"] == NAMES[-1] and not np.array_equal(output, artifact["signals"]):
        raise ValueError("final raw-reconstructed endpoint does not exactly match saved A")
    return output


def validate_record(
    payload: dict[str, Any], *, context: dict[str, Any], condition: dict[str, Any],
    split: dict[str, list[int]], targets: list[str], identity: dict[str, Any],
) -> None:
    record = payload["record"]
    resolved = {"context_sha256": config_digest(context), "condition": condition}
    if (record["config"] != resolved or record["config_sha256"] != config_digest(resolved)
            or record["source_sha256"] != context["source_sha256"]
            or record["git_dirty"] is not False or record["seed"] != 11
            or record["dataset"] != "bci_iv_2a"
            or record["fold"] != f"profile_bridge:subject_01:{condition['name']}"
            or payload["split"] != split or payload["query_targets"] != targets
            or payload["signal_identity"] != identity
            or payload["context_sha256"] != config_digest(context)):
        raise ValueError("bridge configuration, provenance, input or split differs")
    resources = payload["resource_observations"]
    if (not math.isfinite(resources["minimum_observed_free_memory_gib"])
            or resources["minimum_observed_free_memory_gib"] < 4.0
            or resources["model_call_checks"] < 1
            or not math.isfinite(record["metrics"]["fit_seconds"])
            or record["metrics"]["fit_seconds"] <= 0
            or payload["result"]["device"] != "cuda"
            or payload["result"]["split_counts"]
            != {key: len(value) for key, value in split.items()}):
        raise ValueError("bridge resource, device, elapsed time or full split checks failed")
    validate_predictions(payload)


def ordered_summary(scores: dict[str, float]) -> dict[str, Any]:
    if list(scores) != list(NAMES) or any(not 0 <= score <= 1 for score in scores.values()):
        raise ValueError("all seven ordered finite scores are required")
    changes: list[dict[str, Any]] = [
        {"from": left, "to": right, "difference_pp": 100 * (scores[right] - scores[left])}
        for left, right in zip(NAMES[:-1], NAMES[1:], strict=True)
    ]
    gap = 100 * (scores[NAMES[-1]] - scores[NAMES[0]])
    if not math.isclose(sum(row["difference_pp"] for row in changes), gap, abs_tol=1e-10):
        raise ValueError("ordered changes do not reconstruct the endpoint gap")
    return {"scores": scores, "ordered_conditional_changes": changes, "endpoint_gap_pp": gap,
            "scientific_gate_approved": False,
            "scope": ("Post-hoc one-subject/one-seed ordered conditional differences; "
                      "not independent additive causal effects or profile superiority.")}


def endpoint_compatibility(actual: dict[str, Any], reference: dict[str, Any]) -> dict[str, bool]:
    # ClassificationReport contains tuples in memory and lists after JSON loading.
    # Compare exact canonical serialized values; no numeric tolerance or fields omitted.
    return {
        "exact_result_equal": config_digest(actual["result"]) == config_digest(reference["result"]),
        "exact_probabilities_equal": actual["query_probabilities"]
        == reference["query_probabilities"],
        "exact_split_and_targets_equal": actual["split"] == reference["split"]
        and actual["query_targets"] == reference["query_targets"],
    }


def main() -> int:
    config: Any = load_toml(ROOT / "configs/profile_bridge_diagnostic.toml")
    original: Any = load_toml(ROOT / "configs/profile_comparison.toml")
    validate_config(config, original)
    provider = importlib.import_module("psutil")
    runtime = config["runtime"]
    if provider.virtual_memory().available / 1024**3 < runtime["minimum_free_memory_gib"]:
        print(json.dumps({"deferred": "startup below 6 GiB", "training_performed": False}))
        return 2
    source = capture_source(ROOT)
    if source.git_dirty is not False:
        raise ValueError("commit the declared bridge before observing intermediate scores")
    paths = {profile: ROOT / original[profile]["artifact"]
             for profile in ("profile_a", "profile_b")}
    paths.update({f"raw_{part}": ROOT / (
        f"data/raw/moabb/MNE-bnci-data/~bci/database/001-2014/A01{part}.mat"
    ) for part in ("T", "E")})
    paths.update({name: ROOT / REFERENCE / f"{name}.json" for name in REFERENCE_HASHES})
    hashes = {key: file_digest(path) for key, path in paths.items()}
    if any(hashes[name] != expected for name, expected in REFERENCE_HASHES.items()):
        raise ValueError("the pinned preceding unit diagnostic changed")
    context = {"source_sha256": source.source_sha256, "configuration": config,
               "original_comparison": original, "inputs": hashes,
               "environment": environment_identity()}
    key = config_digest(context)
    output = ROOT / config["output_directory"] / key
    output.mkdir(parents=True, exist_ok=True)
    lock = output.parent / ".bridge.lock"
    with lock.open("x", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "source": asdict(source)}, stream)
    try:
        from core.gpu_cooling import cool_gpu
        from encoder import eegnet_baseline as baseline

        torch = importlib.import_module("torch")
        if not torch.cuda.is_available():
            raise ValueError("declared diagnostic requires CUDA")
        if torch.cuda.mem_get_info()[0] / 1024**3 < runtime["minimum_free_gpu_gib"]:
            print(json.dumps({"deferred": "GPU headroom", "training_performed": False}))
            return 2
        torch.set_num_threads(runtime["cpu_threads"])
        context_path = output / "context.json"
        if context_path.exists():
            if config_digest(json.loads(context_path.read_text("utf-8"))) != key:
                raise ValueError("existing bridge context differs; preserve for review")
        else:
            atomic_json(context_path, context)
        expected_names = {f"{name}.json" for name in NAMES} | {"context.json", "summary.json"}
        if any(path.name not in expected_names for path in output.glob("*.json")):
            raise ValueError("unexpected bridge record; preserve for review")
        artifacts = {}
        for profile in ("profile_a", "profile_b"):
            if provider.virtual_memory().available / 1024**3 < 4.0:
                raise RuntimeError("bridge stopped below 4 GiB before loading profile data")
            with np.load(paths[profile], allow_pickle=False) as archive:
                artifacts[profile] = {name: archive[name] for name in archive.files}
        for field in ("labels", "sessions", "runs", "trial_indices", "channel_names"):
            if not np.array_equal(artifacts["profile_a"][field], artifacts["profile_b"][field]):
                raise ValueError(f"saved profile metadata differs: {field}")
        if tuple(artifacts["profile_a"]["channel_names"].tolist()) != CHANNELS:
            raise ValueError("canonical A01 channels required")
        split = independent_split(artifacts["profile_a"])
        targets = artifacts["profile_a"]["labels"][split["test"]].tolist()
        saved: dict[str, Any] = {}
        for condition in config["conditions"]:
            name = condition["name"]
            guard, resources = make_resource_guard(provider, runtime["stop_below_free_memory_gib"])
            guard()
            print(json.dumps({"preparing": name, "epochs_max": 20}), flush=True)
            signals = reconstruct_condition(condition, artifacts, paths, guard)
            identity = array_identity(signals)
            path = output / f"{name}.json"
            check = {"context": context, "condition": condition, "split": split,
                     "targets": targets, "identity": identity}
            if path.exists():
                payload = json.loads(path.read_text("utf-8"))
                validate_record(payload, **check)
            else:
                cool_gpu(bridge_cooling_policy())
                started = time.perf_counter()
                with patch.object(baseline, "EEGNet",
                                  side_effect=guarded_constructor(vars(baseline)["EEGNet"], guard)):
                    result, model = baseline.train_eegnet(
                        signals=signals, labels=artifacts["profile_a"]["labels"],
                        sessions=artifacts["profile_a"]["sessions"],
                        sampling_rate_hz=condition["hz"], input_scale=condition["input_scale"],
                        device_name="cuda",
                        **{k: v for k, v in original["comparison"].items() if k != "subject"},
                    )
                elapsed = time.perf_counter() - started
                values = np.ascontiguousarray(signals[split["test"]]
                                              * np.float32(condition["input_scale"]))
                probabilities = []
                model.eval()
                with torch.inference_mode():
                    for offset in range(0, len(values), 64):
                        batch = torch.from_numpy(values[offset:offset + 64]).to("cuda")
                        probabilities.extend(torch.softmax(model(batch), dim=1).cpu().tolist())
                resolved = {"context_sha256": key, "condition": condition}
                record = RunRecord.create(
                    config=resolved, seed=11, dataset="bci_iv_2a",
                    fold=f"profile_bridge:subject_01:{name}", git_commit=source.git_commit,
                    git_dirty=source.git_dirty, source_sha256=source.source_sha256,
                    metrics={**result.report.record_metrics(), "fit_seconds": elapsed},
                )
                payload = {"record": asdict(record), "result": result.as_dict(), "split": split,
                           "context_sha256": key, "signal_identity": identity,
                           "query_targets": targets, "query_probabilities": probabilities,
                           "resource_observations": resources}
                validate_record(payload, **check)
                if capture_source(ROOT).source_sha256 != source.source_sha256:
                    raise RuntimeError("bridge source changed during execution")
                atomic_json(path, payload)
                del model, values, batch
                torch.cuda.empty_cache()
            saved[name] = payload
            score = payload["result"]["metrics"]["balanced_accuracy"]
            print(json.dumps({"saved_or_verified": name, "balanced_accuracy": score}), flush=True)
            del signals
        endpoints = {}
        for name in REFERENCE_HASHES:
            reference = json.loads(paths[name].read_text("utf-8"))
            endpoints[name] = endpoint_compatibility(saved[name], reference)
        if (capture_source(ROOT).source_sha256 != source.source_sha256
                or config_digest(environment_identity()) != config_digest(context["environment"])
                or any(file_digest(paths[name]) != value for name, value in hashes.items())):
            raise RuntimeError("bridge inputs, source or environment changed")
        scores = {name: saved[name]["result"]["metrics"]["balanced_accuracy"] for name in NAMES}
        summary = {**ordered_summary(scores), "context_sha256": key,
                   "complete": len(saved) == 7,
                   "endpoint_checks": endpoints,
                   "endpoint_checks_passed": all(all(row.values()) for row in endpoints.values()),
                   "record_files": {name: file_digest(output / f"{name}.json") for name in NAMES}}
        atomic_json(output / "summary.json", summary)
        print(json.dumps({"output": str(output), **summary}, indent=2), flush=True)
        return 0 if summary["endpoint_checks_passed"] else 1
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
