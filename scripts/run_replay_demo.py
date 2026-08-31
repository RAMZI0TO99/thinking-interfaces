from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import numpy as np

from core.config import load_toml
from core.splits import earliest_balanced_episode
from evaluation.baselines import BraindecodeClassifier, TorchTrainingConfig
from evaluation.benchmark import load_dataset_matrix
from realtime.interface import GateDrivenInterface
from realtime.pipeline import print_frames, run_replay_pipeline
from realtime.streaming import ArrayReplayStream


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the configured held-out replay demo")
    parser.add_argument("--config", default="configs/demo.toml")
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(project_root / args.config))
    subject_config = cast(Mapping[str, Any], config["subject"])
    stream_config = cast(Mapping[str, Any], config["stream"])
    decoder_config = cast(Mapping[str, Any], config["decoder"])
    decision_config = cast(Mapping[str, Any], config["decision"])
    interface_config = cast(Mapping[str, Any], config["interface"])
    matrix = load_dataset_matrix(
        project_root / "data" / "processed" / "bci_iv_2a" / "profile_a",
        dataset="bci_iv_2a",
        sampling_rate_hz=128.0,
    )
    held_out = str(subject_config["held_out"])
    target_indices = np.flatnonzero(matrix.subjects == held_out)
    source_indices = np.flatnonzero(matrix.subjects != held_out)
    episode = earliest_balanced_episode(
        matrix.labels[target_indices].tolist(),
        subject_id=held_out,
        shots_per_class=int(subject_config["support_shots_per_class"]),
    )
    support = target_indices[np.asarray(episode.support_indices, dtype=np.int64)]
    query = target_indices[np.asarray(episode.query_indices, dtype=np.int64)]
    training_indices = np.concatenate((source_indices, support))
    class_names = tuple(sorted(set(matrix.labels.tolist())))
    class_to_index = {name: index for index, name in enumerate(class_names)}
    targets = np.asarray([class_to_index[label] for label in matrix.labels], dtype=np.int64)
    decoder = BraindecodeClassifier(
        str(decoder_config["model"]),
        channels=matrix.signals.shape[1],
        classes=len(class_names),
        samples=matrix.signals.shape[2],
        sampling_rate_hz=matrix.sampling_rate_hz,
        seed=11,
        training=TorchTrainingConfig(
            epochs=int(decoder_config["epochs"]),
            batch_size=int(decoder_config["batch_size"]),
            learning_rate=float(decoder_config["learning_rate"]),
            weight_decay=float(decoder_config["weight_decay"]),
            input_scale=float(decoder_config["input_scale"]),
            device=str(decoder_config["device"]),
        ),
    ).fit(matrix.signals[training_indices], targets[training_indices])
    repeat = int(subject_config["repeated_query_windows"])
    replay_signal = np.concatenate([matrix.signals[query[0]]] * repeat, axis=1)
    stream = ArrayReplayStream(replay_signal, matrix.channel_names, matrix.sampling_rate_hz)
    interface = GateDrivenInterface(
        target=str(interface_config["target"]),
        bar_width=int(interface_config["confidence_bar_width"]),
    )
    frames, latency = run_replay_pipeline(
        stream,
        decoder,
        class_names,
        interface,
        window_samples=round(float(stream_config["window_seconds"]) * matrix.sampling_rate_hz),
        stride_samples=round(float(stream_config["stride_seconds"]) * matrix.sampling_rate_hz),
        chunk_samples=round(float(stream_config["chunk_seconds"]) * matrix.sampling_rate_hz),
        confidence_threshold=float(decision_config["confidence_threshold"]),
        required_consecutive=int(decision_config["required_consecutive"]),
    )
    print_frames(frames)
    result = {
        "held_out_subject": held_out,
        "device": str(decoder_config["device"]),
        "support_trials": int(support.size),
        "query_trials": int(query.size),
        "latency": asdict(latency),
        "frames": [asdict(frame) for frame in frames],
    }
    output = (
        project_root
        / "runs"
        / f"replay_demo_{held_out}_{str(decoder_config['device']).lower()}.json"
    )
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
