from __future__ import annotations

import gc
import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch

from core.config import config_digest, load_toml
from core.run_record import RunRecord
from evaluation.baselines import TorchTrainingConfig
from evaluation.benchmark import DatasetMatrix, load_dataset_matrix
from evaluation.support_adaptation import source_then_support_fold


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "eegnet_support_adaptation.toml"))
    benchmark = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    episode = config["episode"]
    dataset = str(episode["dataset"])
    settings = benchmark["datasets"][dataset]
    provenance = {"settings": config, "benchmark_config_sha256": config_digest(benchmark)}
    training = TorchTrainingConfig(**config["training"])
    if config["adaptation"]["weight_decay"] != 0.01:
        raise ValueError("adapt_torch_model currently fixes AdamW weight decay at 0.01")
    matrix = load_dataset_matrix(
        root / settings["artifact_directory"],
        dataset=dataset,
        sampling_rate_hz=settings["sampling_rate_hz"],
        absolute_peak_volts=settings["artifact_threshold_volts"],
    )
    keep = np.isin(matrix.labels, episode["included_labels"])
    matrix = DatasetMatrix(
        dataset,
        matrix.signals[keep],
        matrix.labels[keep],
        matrix.subjects[keep],
        matrix.channel_names,
        matrix.sampling_rate_hz,
    )
    subjects = sorted(set(matrix.subjects.tolist()))
    # Measured source-fit/adapter timings are persisted for every fold.
    print(
        json.dumps(
            {
                "protocol": episode["protocol"],
                "subjects": len(subjects),
                "planned_runs": len(subjects) * len(episode["seeds"]),
                "rough_instance_hours": len(subjects) * len(episode["seeds"]) * 30 / 3600,
                "estimate_basis": "30-second per-run planning fallback",
            }
        ),
        flush=True,
    )
    for seed in episode["seeds"]:
        for subject in subjects:
            path = (
                root / "runs" / "support_adaptation" / dataset / f"seed_{seed}" / f"{subject}.json"
            )
            if path.exists():
                saved = json.loads(path.read_text(encoding="utf-8"))
                if (
                    all(
                        saved.get("config", {}).get(key) == value
                        for key, value in provenance.items()
                    )
                    and saved.get("seed") == seed
                    and saved.get("fold") == subject
                    and saved.get("metrics", {}).get("support_adaptation_schema_version") == 1.0
                ):
                    continue
                raise ValueError(f"existing support-adaptation result needs review: {path}")
            result = source_then_support_fold(
                matrix,
                target_subject=subject,
                seed=seed,
                shots_per_class=episode["shots_per_class"],
                training=training,
                adaptation_steps=config["adaptation"]["steps"],
                adaptation_learning_rate=config["adaptation"]["learning_rate"],
            )
            RunRecord.create(
                config={**provenance, "split": result["split"]},
                seed=seed,
                git_commit="unversioned-workspace",
                dataset=dataset,
                fold=subject,
                metrics=result["metrics"],
            ).write_json(path)
            print(
                json.dumps(
                    {
                        "subject": subject,
                        "seed": seed,
                        "balanced_accuracy": result["metrics"]["balanced_accuracy"],
                    }
                ),
                flush=True,
            )
            gc.collect()
            if training.device == "cuda":
                torch.cuda.empty_cache()
                time.sleep(config["runtime"]["cooldown_seconds"])


if __name__ == "__main__":
    main()
