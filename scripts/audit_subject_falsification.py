from __future__ import annotations

import argparse
import gc
import json
import os
import tempfile
import time
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.baselines import TorchTrainingConfig
from evaluation.benchmark import _decoder, load_dataset_matrix
from evaluation.falsification import shuffled_training_control, signal_audit


def write_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        os.replace(temporary, path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Independent fixed-episode shuffled-label controls"
    )
    parser.add_argument("--dataset", default="cho2017", choices=("bci_iv_2a", "cho2017", "mmidb"))
    parser.add_argument("--subject", default="subject_43")
    parser.add_argument("--method", action="append", choices=("eegnet", "shallow", "deep"))
    parser.add_argument("--seed", action="append", type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    settings = config["datasets"][args.dataset]
    training = TorchTrainingConfig(**config["training"])
    matrix = load_dataset_matrix(
        root / settings["artifact_directory"],
        dataset=args.dataset,
        sampling_rate_hz=settings["sampling_rate_hz"],
        absolute_peak_volts=settings["artifact_threshold_volts"],
    )
    output = root / "runs" / "falsification" / args.dataset / args.subject
    shots = int(config["benchmark"]["shots_per_class"])
    provenance = {
        "benchmark_config_sha256": config_digest(config),
        "dataset": args.dataset,
        "target_subject": args.subject,
        "training": asdict(training),
        "shots_per_class": shots,
        "control_schema_version": 1,
        "scientific_leakage_clearance": False,
    }
    audit = signal_audit(matrix, target_subject=args.subject, shots_per_class=shots)
    write_report(output / "signal_audit.json", {**provenance, **audit})
    print(
        json.dumps(
            {
                "signal_audit": str(output / "signal_audit.json"),
                "duplicate_checks_passed": audit["exact_duplicate_checks_passed"],
            }
        ),
        flush=True,
    )
    for method in args.method or ("eegnet", "shallow"):
        for seed in args.seed or (11, 23, 37):
            path = output / f"{method}_shuffled_seed_{seed}.json"
            if path.exists():
                saved = json.loads(path.read_text(encoding="utf-8"))
                if all(saved.get(key) == value for key, value in provenance.items()):
                    print(f"Reusing control: {path.name}", flush=True)
                    continue
                raise ValueError(f"control provenance changed; preserve and review {path}")
            decoder = _decoder(
                method,
                matrix,
                classes=len(set(matrix.labels.tolist())),
                seed=seed,
                torch_config=training,
            )
            result = shuffled_training_control(
                matrix,
                decoder,
                target_subject=args.subject,
                shots_per_class=shots,
                shuffle_seed=seed,
            )
            write_report(
                path,
                {
                    **provenance,
                    **result,
                    "method": method,
                    "timestamp_utc": datetime.now(UTC).isoformat(),
                },
            )
            print(
                json.dumps(
                    {
                        "control": path.name,
                        "balanced_accuracy": result["metrics"]["balanced_accuracy"],
                    }
                ),
                flush=True,
            )
            del decoder
            gc.collect()
            if training.device == "cuda":
                import torch

                torch.cuda.empty_cache()
                time.sleep(5.0)


if __name__ == "__main__":
    main()
