from __future__ import annotations

import copy
import json
import time
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch

from core.config import load_toml
from evaluation.baselines import BraindecodeClassifier, TorchTrainingConfig
from evaluation.latency import LatencyRecorder


def measure(
    classifier: BraindecodeClassifier, window: np.ndarray, *, iterations: int
) -> dict[str, int | float]:
    classifier.predict_proba(window)
    recorder = LatencyRecorder()
    for _ in range(iterations):
        started = time.perf_counter()
        classifier.predict_proba(window)
        recorder.add_seconds(time.perf_counter() - started)
    return asdict(recorder.summarize())


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    root = cast(Mapping[str, Any], load_toml(project_root / "configs" / "latency.toml"))
    config = cast(Mapping[str, Any], root["benchmark"])
    with np.load(project_root / str(config["artifact"])) as artifact:
        signals = np.asarray(artifact["signals"], dtype=np.float32)
        labels = np.asarray(artifact["labels"])
    class_names = tuple(sorted(set(labels.tolist())))
    target_map = {label: index for index, label in enumerate(class_names)}
    targets = np.asarray([target_map[label] for label in labels], dtype=np.int64)
    training_trials = int(config["training_trials"])
    classifier = BraindecodeClassifier(
        "eegnet",
        channels=signals.shape[1],
        classes=len(class_names),
        samples=signals.shape[2],
        sampling_rate_hz=float(config["sampling_rate_hz"]),
        seed=int(config["seed"]),
        training=TorchTrainingConfig(
            epochs=int(config["training_epochs"]),
            batch_size=int(config["batch_size"]),
            input_scale=float(config["input_scale"]),
            device="cuda" if torch.cuda.is_available() else "cpu",
        ),
    ).fit(signals[:training_trials], targets[:training_trials])
    assert classifier.model is not None
    window = signals[training_trials : training_trials + 1]
    iterations = int(config["iterations"])
    results: dict[str, object] = {}
    if torch.cuda.is_available():
        results["gpu"] = measure(classifier, window, iterations=iterations)
    cpu_classifier = copy.deepcopy(classifier)
    assert cpu_classifier.model is not None
    cpu_classifier.model.to("cpu")
    results["cpu"] = measure(cpu_classifier, window, iterations=iterations)
    output = project_root / "runs" / "latency_cpu_gpu.json"
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
