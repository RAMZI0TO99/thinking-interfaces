from __future__ import annotations

import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import nn

from adaptation.episodic import adapt_torch_model
from adaptation.lora import inject_lora
from core.config import load_toml
from core.metrics import classification_report
from core.splits import earliest_balanced_episode
from encoder.eegnet_linear import linearize_eegnet_classifier
from evaluation.baselines import BraindecodeClassifier, TorchTrainingConfig
from evaluation.benchmark import load_dataset_matrix


def probabilities(model: nn.Module, signals: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    with torch.inference_mode():
        logits = model(torch.from_numpy(signals).to(device))
        return torch.softmax(logits, dim=1).cpu().numpy()


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = cast(
        Mapping[str, Any], load_toml(project_root / "configs" / "episodic_lora.toml")
    )
    episode_config = cast(Mapping[str, Any], config["episode"])
    training = cast(Mapping[str, Any], config["base_training"])
    lora = cast(Mapping[str, Any], config["lora"])
    matrix = load_dataset_matrix(
        project_root / "data" / "processed" / "bci_iv_2a" / "profile_a",
        dataset="bci_iv_2a",
        sampling_rate_hz=128.0,
    )
    included = cast(list[str], episode_config["included_labels"])
    keep = np.isin(matrix.labels, included)
    signals = matrix.signals[keep]
    labels = matrix.labels[keep]
    subjects = matrix.subjects[keep]
    class_names = tuple(sorted(included))
    class_to_index = {label: index for index, label in enumerate(class_names)}
    targets = np.asarray([class_to_index[label] for label in labels], dtype=np.int64)
    target_subject = str(episode_config["target_subject"])
    source = np.flatnonzero(subjects != target_subject)
    target = np.flatnonzero(subjects == target_subject)
    episode = earliest_balanced_episode(
        labels[target].tolist(),
        subject_id=target_subject,
        shots_per_class=int(episode_config["shots_per_class"]),
    )
    support = target[np.asarray(episode.support_indices, dtype=np.int64)]
    query = target[np.asarray(episode.query_indices, dtype=np.int64)]
    device = torch.device(str(training["device"]))
    classifier = BraindecodeClassifier(
        "eegnet",
        channels=signals.shape[1],
        classes=len(class_names),
        samples=signals.shape[2],
        sampling_rate_hz=matrix.sampling_rate_hz,
        seed=int(episode_config["seed"]),
        training=TorchTrainingConfig(
            epochs=int(training["epochs"]),
            batch_size=int(training["batch_size"]),
            learning_rate=float(training["learning_rate"]),
            weight_decay=float(training["weight_decay"]),
            input_scale=float(training["input_scale"]),
            device=str(training["device"]),
        ),
    ).fit(signals[source], targets[source])
    assert classifier.model is not None
    scaled_example = torch.from_numpy(
        np.ascontiguousarray(
            signals[source[:1]] * float(training["input_scale"]), dtype=np.float32
        )
    ).to(device)
    classifier.model = linearize_eegnet_classifier(classifier.model, scaled_example).to(
        device
    )
    injection = inject_lora(
        classifier.model,
        rank=int(lora["rank"]),
        alpha=float(lora["alpha"]),
        dropout=float(lora["dropout"]),
    )
    if not injection.replaced_modules:
        raise RuntimeError("linearized EEGNet exposed no LoRA target")
    scaled_support = torch.from_numpy(
        np.ascontiguousarray(signals[support] * float(training["input_scale"]), dtype=np.float32)
    )
    before = probabilities(
        classifier.model,
        np.ascontiguousarray(signals[query] * float(training["input_scale"]), dtype=np.float32),
        device,
    )
    adaptation_started = time.perf_counter()
    adapted = adapt_torch_model(
        classifier.model,
        scaled_support,
        torch.from_numpy(targets[support]),
        steps=int(lora["steps"]),
        learning_rate=float(lora["learning_rate"]),
        trainable=lambda name, _: "lora_" in name,
        device=device,
    )
    adaptation_seconds = time.perf_counter() - adaptation_started
    after = probabilities(
        adapted.model,
        np.ascontiguousarray(signals[query] * float(training["input_scale"]), dtype=np.float32),
        device,
    )
    truth = [class_names[index] for index in targets[query]]
    before_report = classification_report(
        truth, [class_names[index] for index in before.argmax(axis=1)], labels=class_names
    )
    after_report = classification_report(
        truth, [class_names[index] for index in after.argmax(axis=1)], labels=class_names
    )
    result = {
        "target_subject": target_subject,
        "support_trials": int(support.size),
        "query_trials": int(query.size),
        "adapter_parameters": injection.trainable_adapter_parameters,
        "adaptation_steps": len(adapted.losses),
        "adaptation_seconds": adaptation_seconds,
        "before_balanced_accuracy": before_report.balanced_accuracy,
        "after_balanced_accuracy": after_report.balanced_accuracy,
        "probability_maximum_change": float(np.max(np.abs(after - before))),
    }
    output = project_root / "runs" / "episodic_lora_eegnet.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
