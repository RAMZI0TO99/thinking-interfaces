"""Resource-guarded real-epoch integration test of the linked MOABB EEGNet pipeline."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
import time
import tomllib
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch
from urllib.parse import urlsplit

from core.provenance import capture_source
from core.run_record import RunRecord
from data.runtime import configure_scientific_runtime

ROOT = Path(__file__).resolve().parents[1]


def run_reference_fold(settings: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    """Called only after the lightweight checker permits a training start."""
    runtime = environment["config"]["runtime"]
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["OMP_NUM_THREADS"] = str(runtime["intra_op_threads"])
    os.environ["OPENBLAS_NUM_THREADS"] = str(runtime["intra_op_threads"])
    os.environ["MKL_NUM_THREADS"] = str(runtime["intra_op_threads"])
    configure_scientific_runtime(ROOT)
    tf = importlib.import_module("tensorflow")
    tf.config.threading.set_intra_op_parallelism_threads(runtime["intra_op_threads"])
    tf.config.threading.set_inter_op_parallelism_threads(runtime["inter_op_threads"])
    np = importlib.import_module("numpy")
    psutil = importlib.import_module("psutil")
    bnci = importlib.import_module("moabb.datasets.bnci")
    paradigms = importlib.import_module("moabb.paradigms")
    features = importlib.import_module("moabb.pipelines.features")
    deep = importlib.import_module("moabb.pipelines.deep_learning")
    sklearn_pipeline = importlib.import_module("sklearn.pipeline")
    sklearn_model_selection = importlib.import_module("sklearn.model_selection")
    sklearn_preprocessing = importlib.import_module("sklearn.preprocessing")
    sklearn_metrics = importlib.import_module("sklearn.metrics")
    importlib.import_module("moabb.utils").setup_seed(settings["model_seed"])
    importlib.import_module("mne").set_log_level("ERROR")
    if tf.config.list_physical_devices("GPU"):
        raise RuntimeError("the isolated reference must use CPU only")

    subject = settings["subject"]
    raw_root = (ROOT / settings["raw_directory"]).resolve(strict=True)
    if not raw_root.is_relative_to(ROOT / "data/raw"):
        raise ValueError("reference input directory must stay inside project raw data")
    raw_files = {
        f"A{subject:02d}{suffix}.mat": raw_root / f"A{subject:02d}{suffix}.mat"
        for suffix in ("T", "E")
    }
    raw_hashes = {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in raw_files.items()
    }
    requests = []

    def local_data_path(url: str, *args: Any, **kwargs: Any) -> list[str]:
        name = Path(urlsplit(url).path).name
        if name not in raw_files:
            raise ValueError(f"reference loader requested an unexpected input: {name}")
        requests.append(name)
        return [str(raw_files[name])]

    dataset = bnci.BNCI2014_001()
    paradigm = paradigms.LeftRightImagery(fmin=settings["fmin"], fmax=settings["fmax"])
    # Only the download resolver changes; the verified loader and preprocessing remain intact.
    with patch.object(bnci, "data_path", local_data_path):
        epochs, labels, metadata = paradigm.get_data(
            dataset=dataset,
            subjects=[subject],
            return_epochs=True,
        )
    if set(requests) != set(raw_files):
        raise RuntimeError("reference did not load the two expected subject files")
    indices = np.flatnonzero(metadata["session"].astype(str).to_numpy() == settings["session"])
    if indices.size == 0:
        raise ValueError("configured reference session is absent")
    session_epochs = epochs[indices]
    label_encoder = sklearn_preprocessing.LabelEncoder()
    targets = label_encoder.fit_transform(labels[indices])
    if list(label_encoder.classes_) != ["left_hand", "right_hand"]:
        raise ValueError("reference requires left/right classes only")
    cv = sklearn_model_selection.StratifiedKFold(
        settings["fold_count"], shuffle=True, random_state=settings["split_seed"]
    )
    train, query = list(cv.split(np.zeros(len(targets)), targets))[settings["fold_index"]]
    split_at = math.floor(len(train) * (1.0 - settings["validation_split"]))
    optimization, validation = train[:split_at], train[split_at:]
    if not len(optimization) or not len(validation) or np.intersect1d(train, query).size:
        raise RuntimeError("invalid or overlapping reference split")

    checks = {"resource_stop": False}

    def guard_resources(epoch: int, logs: Any = None) -> None:
        if psutil.virtual_memory().available / 1024**3 < runtime["stop_below_free_memory_gib"]:
            checks["resource_stop"] = True
            raise RuntimeError("reference fold aborted at the low-memory stop threshold")

    guard_resources(0)
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=settings["patience"]
    )
    if early_stopping.restore_best_weights:
        raise RuntimeError("unexpected best-weight restoration in reference callback")
    classifier = deep.KerasEEGNet_8_2(
        loss="sparse_categorical_crossentropy",
        optimizer=tf.keras.optimizers.Adam(learning_rate=settings["learning_rate"]),
        epochs=settings["epochs"],
        batch_size=settings["batch_size"],
        verbose=0,
        random_state=settings["model_seed"],
        validation_split=settings["validation_split"],
        drop_rate=settings["drop_rate"],
        callbacks=[
            early_stopping,
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                patience=settings["patience"],
                factor=settings["learning_rate_factor"],
            ),
            tf.keras.callbacks.LambdaCallback(on_epoch_begin=guard_resources),
        ],
    )
    pipeline = sklearn_pipeline.make_pipeline(
        features.Resampler_Epoch(sfreq=settings["resample_hz"]),
        features.Convert_Epoch_Array(),
        features.StandardScaler_Epoch(),
        classifier,
    )
    started = time.perf_counter()
    pipeline.fit(session_epochs[train], targets[train])
    fit_seconds = time.perf_counter() - started
    prediction_started = time.perf_counter()
    probabilities = np.asarray(pipeline.predict_proba(session_epochs[query]))
    prediction_seconds = time.perf_counter() - prediction_started
    if (
        probabilities.shape != (len(query), 2)
        or not np.isfinite(probabilities).all()
        or np.any(probabilities < 0)
        or np.any(probabilities > 1)
        or not np.allclose(probabilities.sum(axis=1), 1.0)
    ):
        raise RuntimeError("reference returned invalid probabilities")
    epochs_completed = len(classifier.history_["loss"])
    if list(classifier.classes_) != [0, 1] or not 1 <= epochs_completed <= settings["epochs"]:
        raise RuntimeError("reference class order or epoch count is unexpected")
    if not all(np.isfinite(value) for values in classifier.history_.values() for value in values):
        raise RuntimeError("nonfinite reference training history")
    transformed = pipeline[:-1].transform(session_epochs[query])
    if not np.allclose(transformed.mean(axis=1), 0.0, atol=1e-9):
        raise RuntimeError("reference per-time-point spatial centering did not hold")
    auc = float(sklearn_metrics.roc_auc_score(targets[query], probabilities[:, 1]))
    return {
        "fold_executed": True,
        "reference_reproduction_passed": False,
        "scope": "One real within-session fold; no scientific gate approval.",
        "raw_file_sha256": raw_hashes,
        "raw_path_redirect_only": True,
        "dataset_code": dataset.code,
        "classes": label_encoder.classes_.tolist(),
        "session_original_indices": indices.tolist(),
        "session_targets": targets.tolist(),
        "channel_names": list(session_epochs.ch_names),
        "optimization_indices": optimization.tolist(),
        "validation_indices": validation.tolist(),
        "query_indices": query.tolist(),
        "query_targets": targets[query].tolist(),
        "query_probabilities": probabilities.tolist(),
        "roc_auc": auc,
        "fit_seconds": fit_seconds,
        "prediction_seconds": prediction_seconds,
        "epochs_completed": epochs_completed,
        "early_stopping_epoch": int(early_stopping.stopped_epoch),
        "history": dict(classifier.history_),
        "session_trials": len(targets),
        "native_epoch_shape": list(session_epochs.get_data().shape),
        "transformed_query_shape": list(transformed.shape),
        "transformed_query_sha256": hashlib.sha256(transformed.tobytes()).hexdigest(),
        "restore_best_weights": early_stopping.restore_best_weights,
        "resource_stop": checks["resource_stop"],
    }


def run_smoke(settings: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    result = run_reference_fold(settings, environment)
    if result["epochs_completed"] != 2:
        raise RuntimeError("the bounded smoke must complete exactly two epochs")
    result.update(
        {
            "smoke_passed": True,
            "scope": "One real within-session fold, two-epoch integration only; not Gate A.",
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs/moabb_reference_smoke.toml")
    args = parser.parse_args()
    config = tomllib.loads(args.config.read_text(encoding="utf-8"))
    settings = config["smoke"]
    # Fail closed if a future edit accidentally expands this bounded smoke into a full experiment.
    if (
        type(settings["subject"]) is not int
        or not 1 <= settings["subject"] <= 9
        or type(settings["epochs"]) is not int
        or settings["epochs"] != 2
        or type(settings["fold_count"]) is not int
        or settings["fold_count"] != 5
        or type(settings["fold_index"]) is not int
        or not 0 <= settings["fold_index"] < 5
    ):
        raise ValueError("smoke must be one five-fold-CV split and exactly two epochs")
    preflight = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.check_moabb_reference_environment",
            "--config",
            str(ROOT / settings["environment_config"]),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=45,
    )
    receipt = json.loads(preflight.stdout)
    environment = json.loads(Path(receipt["report"]).read_text(encoding="utf-8"))
    if not environment["training_ready"]:
        print(
            json.dumps(
                {
                    "deferred": True,
                    "reason": environment["resources"],
                    "environment_receipt": receipt["report"],
                    "training_performed": False,
                }
            )
        )
        return 2
    source = capture_source(ROOT)
    result = run_smoke(settings, environment)
    if capture_source(ROOT).source_sha256 != source.source_sha256:
        raise RuntimeError("project source changed during the reference smoke")
    resolved = {"smoke": settings, "environment": environment["config"]}
    record = RunRecord.create(
        config=resolved,
        seed=settings["model_seed"],
        git_commit=source.git_commit,
        source_sha256=source.source_sha256,
        git_dirty=source.git_dirty,
        dataset="bci_iv_2a",
        fold=f"smoke:subject-{settings['subject']}:{settings['session']}",
        metrics={"roc_auc": result["roc_auc"], "fit_seconds": result["fit_seconds"]},
    )
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = (ROOT / settings["output_directory"] / stamp).resolve()
    if not output.is_relative_to(ROOT / "runs/moabb_reference/smoke"):
        raise ValueError("smoke outputs must stay in the separate reference smoke directory")
    output.mkdir(parents=True)
    record.write_json(output / "run_record.json")
    result.update(
        {
            "environment_receipt": receipt["report"],
            "config": resolved,
            "source": asdict(source),
            "run_record": str(output / "run_record.json"),
        }
    )
    (output / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "report": str(output / "result.json"),
                "smoke_passed": True,
                "reference_reproduction_passed": False,
                "roc_auc": result["roc_auc"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
