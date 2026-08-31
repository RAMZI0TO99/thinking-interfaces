"""Single-variable Profile B unit-conversion diagnostic, separate from frozen runs."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import tempfile
import time
import tomllib
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

from core.config import config_digest
from core.provenance import capture_source
from core.run_record import RunRecord

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = {
    "profile_a_microvolts": {"profile": "profile_a", "input_scale": 1000000.0},
    "profile_b_original_units": {"profile": "profile_b", "input_scale": 1.0},
    "profile_b_microvolts": {"profile": "profile_b", "input_scale": 100.0},
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".units-", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def resolve_config(path: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    config = tomllib.loads(path.read_text(encoding="utf-8"))
    if set(config) != {"diagnostic", "runtime", "conditions"} or config["conditions"] != CONDITIONS:
        raise ValueError("unit diagnostic must preserve all three declared conditions")
    if any(type(item["input_scale"]) is not float for item in config["conditions"].values()):
        raise ValueError("unit multipliers must be unambiguous floats")
    reference = (ROOT / config["diagnostic"]["comparison_config"]).resolve(strict=True)
    if reference != ROOT / "configs/profile_comparison.toml":
        raise ValueError("diagnostic must retain the original comparison configuration")
    original = tomllib.loads(reference.read_text(encoding="utf-8"))
    output = (
        ROOT
        / config["diagnostic"]["output_directory"]
        / config_digest({"diagnostic": config, "original_comparison": original})
    ).resolve()
    if not output.is_relative_to(ROOT / "runs/profile_units_diagnostic"):
        raise ValueError("diagnostic output must stay separate from original and benchmark records")
    return config, original, output


def validate_predictions(payload: dict[str, Any]) -> None:
    np = importlib.import_module("numpy")
    from core.metrics import classification_report

    result = payload["result"]
    count = result["epochs_completed"]
    history = result["history"]
    if (
        type(count) is not int
        or not 1 <= count <= 20
        or len(history) != count
        or any(row["epoch"] != index + 1 for index, row in enumerate(history))
        or any(
            not math.isfinite(row[key]) or row[key] < 0
            for row in history
            for key in ("train_loss", "validation_loss")
        )
    ):
        raise ValueError("invalid diagnostic learning history")
    best = min(range(count), key=lambda index: history[index]["validation_loss"])
    if (
        result["best_epoch"] != best + 1
        or result["best_validation_loss"] != history[best]["validation_loss"]
        or (count < 20 and count != best + 1 + 5)
    ):
        raise ValueError("diagnostic checkpoint/history mismatch")
    probabilities = np.asarray(payload["query_probabilities"], dtype=float)
    classes = result["metrics"]["labels"]
    targets = payload["query_targets"]
    if (
        probabilities.shape != (len(targets), len(classes))
        or not np.isfinite(probabilities).all()
        or np.any(probabilities < 0)
        or np.any(probabilities > 1)
        or not np.allclose(probabilities.sum(axis=1), 1, atol=1e-6)
    ):
        raise ValueError("invalid diagnostic query probabilities")
    prediction = [classes[index] for index in probabilities.argmax(axis=1)]
    actual = classification_report(targets, prediction, labels=classes).as_dict()
    if config_digest(actual) != config_digest(result["metrics"]):
        raise ValueError("diagnostic metrics do not match saved predictions")
    split = payload["split"]
    groups = [set(split[key]) for key in ("train", "validation", "test")]
    if (
        any(
            len(group) != len(split[key])
            for group, key in zip(groups, ("train", "validation", "test"), strict=True)
        )
        or groups[0] & groups[1]
        or groups[0] & groups[2]
        or groups[1] & groups[2]
        or set.union(*groups) != set(range(576))
        or len(split["test"]) != len(targets)
    ):
        raise ValueError("invalid diagnostic train/validation/test partition")
    for key in ("balanced_accuracy", "cohen_kappa"):
        if payload["record"]["metrics"][key] != actual[key]:
            raise ValueError("diagnostic RunRecord metrics differ")


def make_resource_guard(provider: Any, minimum: float) -> tuple[Any, dict[str, float]]:
    observations = {
        "minimum_observed_free_memory_gib": math.inf,
        "maximum_observed_process_rss_gib": 0.0,
        "model_call_checks": 0,
    }

    def before_model_call(*unused: Any) -> None:
        available = provider.virtual_memory().available / 1024**3
        resident = provider.Process().memory_info().rss / 1024**3
        observations["minimum_observed_free_memory_gib"] = min(
            observations["minimum_observed_free_memory_gib"], available
        )
        observations["maximum_observed_process_rss_gib"] = max(
            observations["maximum_observed_process_rss_gib"], resident
        )
        observations["model_call_checks"] += 1
        if available < minimum:
            raise RuntimeError("diagnostic stopped before a model call at low memory")

    return before_model_call, observations


def guarded_constructor(constructor: Any, guard: Any) -> Any:
    def build(*args: Any, **kwargs: Any) -> Any:
        model = constructor(*args, **kwargs)
        model.register_forward_pre_hook(guard)
        return model

    return build


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/profile_units_diagnostic.toml"
    )
    args = parser.parse_args()
    config, original, output = resolve_config(args.config)
    runtime = config["runtime"]
    psutil = importlib.import_module("psutil")
    if psutil.virtual_memory().available / 1024**3 < runtime["minimum_free_memory_gib"]:
        print(json.dumps({"deferred": "insufficient free memory", "training_performed": False}))
        return 2
    torch = importlib.import_module("torch")
    if runtime["device"] != "cuda" or not torch.cuda.is_available():
        raise ValueError("the declared bounded diagnostic requires the available GPU")
    if torch.cuda.mem_get_info()[0] / 1024**3 < runtime["minimum_free_gpu_gib"]:
        print(json.dumps({"deferred": "insufficient free GPU memory", "training_performed": False}))
        return 2
    torch.set_num_threads(runtime["cpu_threads"])
    np = importlib.import_module("numpy")
    from encoder.eegnet_baseline import make_session_split, train_eegnet

    source = capture_source(ROOT)
    if source.git_dirty is not False:
        raise ValueError("commit diagnostic settings before observing its results")
    legacy_path = (ROOT / config["diagnostic"]["legacy_result"]).resolve(strict=True)
    if legacy_path != ROOT / "runs/profile_comparison.json":
        raise ValueError("preserve the original comparison artifact")
    legacy_hash = digest(legacy_path)
    execution = config_digest(
        {"runner": digest(Path(__file__)), "trainer": digest(ROOT / "encoder/eegnet_baseline.py")}
    )
    artifacts = {}
    hashes = {}
    for profile in ("profile_a", "profile_b"):
        path = (ROOT / original[profile]["artifact"]).resolve(strict=True)
        if not path.is_relative_to(ROOT / f"data/processed/bci_iv_2a/{profile}"):
            raise ValueError("unexpected profile artifact path")
        hashes[profile] = digest(path)
        with np.load(path, allow_pickle=False) as archive:
            artifacts[profile] = {name: archive[name].copy() for name in archive.files}
    for field in ("labels", "sessions", "runs", "trial_indices", "channel_names"):
        if not np.array_equal(artifacts["profile_a"][field], artifacts["profile_b"][field]):
            raise ValueError(f"profile identity/order differs: {field}")
    shared = original["comparison"]
    split = make_session_split(
        artifacts["profile_a"]["labels"],
        artifacts["profile_a"]["sessions"],
        train_session=shared["train_session"],
        test_session=shared["test_session"],
        validation_fraction=shared["validation_fraction"],
        seed=shared["seed"],
    )
    split_dict = {key: getattr(split, key).tolist() for key in ("train", "validation", "test")}
    output.mkdir(parents=True, exist_ok=True)
    lock = output / "diagnostic.lock"
    with lock.open("x", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "source": asdict(source)}, stream)
    try:
        saved = {}
        for name, condition in config["conditions"].items():
            path = output / f"{name}.json"
            resolved = {"diagnostic": config, "original_comparison": original, "condition": name}
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                if (
                    payload["record"]["config_sha256"] != config_digest(resolved)
                    or payload["record"]["config"] != resolved
                    or payload["artifact_sha256"] != hashes
                    or payload["execution_sha256"] != execution
                    or payload["split"] != split_dict
                    or payload["legacy_result_sha256"] != legacy_hash
                    or payload["query_targets"]
                    != artifacts[condition["profile"]]["labels"][split.test].tolist()
                    or payload["record"]["seed"] != shared["seed"]
                    or payload["record"]["fold"] != f"profile_units:subject_01:{name}"
                ):
                    raise ValueError("saved diagnostic differs; preserve for review")
                validate_predictions(payload)
                saved[name] = payload
                print(json.dumps({"reused": name}), flush=True)
                continue
            if psutil.virtual_memory().available / 1024**3 < runtime["stop_below_free_memory_gib"]:
                print(json.dumps({"deferred": name}), flush=True)
                return 2
            profile = condition["profile"]
            artifact = artifacts[profile]
            signals = np.asarray(artifact["signals"], dtype=np.float32)
            print(
                json.dumps(
                    {
                        "training": name,
                        "epochs_max": shared["epochs"],
                        "estimated_fit_hours": None,
                        "estimate_limit": (
                            "No prior matched diagnostic timing; no cross-profile estimate."
                        ),
                        "instance_hourly_cost_usd": 0.0,
                    }
                ),
                flush=True,
            )
            started = time.perf_counter()
            before_model_call, resources = make_resource_guard(
                psutil, runtime["stop_below_free_memory_gib"]
            )
            baseline = importlib.import_module("encoder.eegnet_baseline")
            # Process-local resource hook only; model/optimizer numerical operations are unchanged.
            with patch.object(
                baseline,
                "EEGNet",
                side_effect=guarded_constructor(baseline.EEGNet, before_model_call),
            ):
                result, model = train_eegnet(
                    signals=signals,
                    labels=artifact["labels"],
                    sessions=artifact["sessions"],
                    sampling_rate_hz=original[profile]["sampling_rate_hz"],
                    input_scale=condition["input_scale"],
                    device_name=runtime["device"],
                    **{key: value for key, value in shared.items() if key != "subject"},
                )
            fit_seconds = time.perf_counter() - started
            values = np.ascontiguousarray(
                signals[split.test] * np.float32(condition["input_scale"])
            )
            probabilities = []
            model.eval()
            with torch.inference_mode():
                for offset in range(0, len(values), shared["batch_size"]):
                    batch = torch.from_numpy(values[offset : offset + shared["batch_size"]]).to(
                        "cuda"
                    )
                    probabilities.extend(torch.softmax(model(batch), dim=1).cpu().tolist())
            if capture_source(ROOT).source_sha256 != source.source_sha256:
                raise RuntimeError("diagnostic source changed during fit")
            record = RunRecord.create(
                config=resolved,
                seed=shared["seed"],
                dataset="bci_iv_2a",
                fold=f"profile_units:subject_01:{name}",
                git_commit=source.git_commit,
                source_sha256=source.source_sha256,
                git_dirty=source.git_dirty,
                metrics={**result.report.record_metrics(), "fit_seconds": fit_seconds},
            )
            payload = {
                "record": asdict(record),
                "result": result.as_dict(),
                "split": split_dict,
                "artifact_sha256": hashes,
                "execution_sha256": execution,
                "legacy_result_sha256": legacy_hash,
                "resource_observations": resources,
                "query_probabilities": probabilities,
                "query_targets": artifact["labels"][split.test].tolist(),
                "signal_shape": list(signals.shape),
                "input_standard_deviation": float((signals * condition["input_scale"]).std()),
                "scope": (
                    "One-subject one-seed post-hoc input-unit diagnostic; "
                    "not Gate A or benchmark replacement."
                ),
            }
            validate_predictions(payload)
            atomic_json(path, payload)
            saved[name] = payload
            print(
                json.dumps({"saved": name, "balanced_accuracy": result.report.balanced_accuracy}),
                flush=True,
            )
            del model
            torch.cuda.empty_cache()
        for profile in hashes:
            if digest(ROOT / original[profile]["artifact"]) != hashes[profile]:
                raise RuntimeError("profile artifact changed during diagnostic")
        if digest(legacy_path) != legacy_hash:
            raise RuntimeError("original comparison result changed")
        scores = {
            name: value["result"]["metrics"]["balanced_accuracy"] for name, value in saved.items()
        }
        summary = {
            "complete": len(saved) == 3,
            "scores": scores,
            "b_microvolts_minus_b_original": scores["profile_b_microvolts"]
            - scores["profile_b_original_units"],
            "b_microvolts_minus_a_microvolts": scores["profile_b_microvolts"]
            - scores["profile_a_microvolts"],
            "record_files": {name: digest(output / f"{name}.json") for name in saved},
            "legacy_result_unchanged": True,
            "scientific_gate_approved": False,
            "scope": (
                "Conditional effect of input scale with other B settings fixed; "
                "remaining A/B differences are not isolated."
            ),
        }
        atomic_json(output / "summary.json", summary)
        print(json.dumps({"output": str(output), **summary}), flush=True)
    finally:
        lock.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
