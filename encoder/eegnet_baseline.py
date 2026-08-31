"""Deterministic EEGNet baseline with a session-held-out final evaluation."""

from __future__ import annotations

import json
import os
import random
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]

from core.metrics import ClassificationReport, classification_report
from data.runtime import configure_scientific_runtime

configure_scientific_runtime()

import torch  # noqa: E402
from braindecode.models import EEGNet  # type: ignore[import-untyped]  # noqa: E402
from torch import nn  # noqa: E402
from torch.utils.data import DataLoader, Dataset, TensorDataset  # noqa: E402


@dataclass(frozen=True, slots=True)
class SessionSplit:
    train: np.ndarray[Any, np.dtype[np.int64]]
    validation: np.ndarray[Any, np.dtype[np.int64]]
    test: np.ndarray[Any, np.dtype[np.int64]]

    def __post_init__(self) -> None:
        groups = [set(values.tolist()) for values in (self.train, self.validation, self.test)]
        if any(not group for group in groups):
            raise ValueError("train, validation, and test splits must be non-empty")
        if groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]:
            raise ValueError("train, validation, and test splits must be disjoint")


@dataclass(frozen=True, slots=True)
class BaselineResult:
    report: ClassificationReport
    best_epoch: int
    epochs_completed: int
    best_validation_loss: float
    split_counts: Mapping[str, int]
    device: str
    history: tuple[Mapping[str, float], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "metrics": self.report.as_dict(),
            "best_epoch": self.best_epoch,
            "epochs_completed": self.epochs_completed,
            "best_validation_loss": self.best_validation_loss,
            "split_counts": dict(self.split_counts),
            "device": self.device,
            "history": [dict(row) for row in self.history],
        }


def make_session_split(
    labels: np.ndarray[Any, np.dtype[np.str_]],
    sessions: np.ndarray[Any, np.dtype[np.str_]],
    *,
    train_session: str,
    test_session: str,
    validation_fraction: float,
    seed: int,
) -> SessionSplit:
    """Split only the training session; preserve the test session untouched."""

    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between zero and one")
    if train_session == test_session:
        raise ValueError("train_session and test_session must differ")

    development = np.flatnonzero(sessions == train_session).astype(np.int64)
    test = np.flatnonzero(sessions == test_session).astype(np.int64)
    if development.size == 0 or test.size == 0:
        raise ValueError("configured train or test session is absent from the artifact")

    train, validation = train_test_split(
        development,
        test_size=validation_fraction,
        random_state=seed,
        shuffle=True,
        stratify=labels[development],
    )
    return SessionSplit(
        train=np.sort(train).astype(np.int64),
        validation=np.sort(validation).astype(np.int64),
        test=np.sort(test).astype(np.int64),
    )


def set_deterministic_seed(seed: int) -> None:
    if seed < 0:
        raise ValueError("seed must be non-negative")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True, warn_only=True)


def shuffle_development_targets(
    targets: np.ndarray[Any, np.dtype[np.int64]],
    split: SessionSplit,
    *,
    seed: int,
) -> np.ndarray[Any, np.dtype[np.int64]]:
    """Shuffle train/validation labels while leaving final test labels untouched."""

    shuffled = targets.copy()
    development = np.concatenate((split.train, split.validation))
    development_targets = shuffled[development].copy()
    np.random.default_rng(seed).shuffle(development_targets)
    shuffled[development] = development_targets
    return shuffled


def _loader(
    signals: np.ndarray[Any, np.dtype[np.float32]],
    targets: np.ndarray[Any, np.dtype[np.int64]],
    indices: np.ndarray[Any, np.dtype[np.int64]],
    *,
    batch_size: int,
    shuffle: bool,
    seed: int,
) -> DataLoader[tuple[torch.Tensor, torch.Tensor]]:
    dataset = cast(
        Dataset[tuple[torch.Tensor, torch.Tensor]],
        TensorDataset(
            torch.from_numpy(signals[indices]),
            torch.from_numpy(targets[indices]),
        ),
    )
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )


def _mean_loss(
    model: nn.Module,
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor]],
    criterion: nn.Module,
    device: torch.device,
) -> float:
    model.eval()
    total = 0.0
    count = 0
    with torch.inference_mode():
        for batch, targets in loader:
            batch = batch.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)
            total += float(criterion(model(batch), targets).item()) * targets.shape[0]
            count += targets.shape[0]
    return total / count


def _predict(
    model: nn.Module,
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor]],
    device: torch.device,
) -> np.ndarray[Any, np.dtype[np.int64]]:
    model.eval()
    predictions: list[np.ndarray[Any, np.dtype[np.int64]]] = []
    with torch.inference_mode():
        for batch, _ in loader:
            logits = model(batch.to(device, non_blocking=True))
            predictions.append(logits.argmax(dim=1).cpu().numpy().astype(np.int64))
    return np.concatenate(predictions)


def train_eegnet(
    *,
    signals: np.ndarray[Any, np.dtype[np.float32]],
    labels: np.ndarray[Any, np.dtype[np.str_]],
    sessions: np.ndarray[Any, np.dtype[np.str_]],
    train_session: str,
    test_session: str,
    sampling_rate_hz: float,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    validation_fraction: float,
    early_stopping_patience: int,
    input_scale: float,
    seed: int,
    model_options: Mapping[str, Any] | None = None,
    device_name: str | None = None,
    shuffle_labels: bool = False,
) -> tuple[BaselineResult, nn.Module]:
    """Train on one session, tune on its subset, and score the held-out session."""

    if signals.ndim != 3 or signals.shape[0] != labels.size or labels.size != sessions.size:
        raise ValueError("artifact arrays have incompatible shapes")
    if epochs < 1 or batch_size < 1 or early_stopping_patience < 1:
        raise ValueError("epochs, batch_size, and patience must be positive")
    if not np.isfinite(signals).all() or input_scale <= 0:
        raise ValueError("signals must be finite and input_scale must be positive")

    set_deterministic_seed(seed)
    class_names = tuple(sorted(np.unique(labels).tolist()))
    class_to_index = {label: index for index, label in enumerate(class_names)}
    targets = np.asarray([class_to_index[label] for label in labels], dtype=np.int64)
    split = make_session_split(
        labels,
        sessions,
        train_session=train_session,
        test_session=test_session,
        validation_fraction=validation_fraction,
        seed=seed,
    )
    if shuffle_labels:
        targets = shuffle_development_targets(targets, split, seed=seed)
    scaled = np.ascontiguousarray(signals * np.float32(input_scale), dtype=np.float32)
    device = torch.device(
        device_name if device_name is not None else ("cuda" if torch.cuda.is_available() else "cpu")
    )
    options = dict(model_options or {})
    model = EEGNet(
        n_chans=signals.shape[1],
        n_outputs=len(class_names),
        n_times=signals.shape[2],
        sfreq=sampling_rate_hz,
        **options,
    ).to(device)

    train_loader = _loader(
        scaled, targets, split.train, batch_size=batch_size, shuffle=True, seed=seed
    )
    validation_loader = _loader(
        scaled, targets, split.validation, batch_size=batch_size, shuffle=False, seed=seed
    )
    test_loader = _loader(
        scaled, targets, split.test, batch_size=batch_size, shuffle=False, seed=seed
    )
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(), learning_rate, weight_decay=weight_decay
    )

    best_state: dict[str, torch.Tensor] | None = None
    best_validation_loss = float("inf")
    best_epoch = 0
    stale_epochs = 0
    history: list[Mapping[str, float]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        count = 0
        for batch, target in train_loader:
            batch = batch.to(device, non_blocking=True)
            target = target.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(batch), target)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * target.shape[0]
            count += target.shape[0]
        validation_loss = _mean_loss(model, validation_loader, criterion, device)
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": total_loss / count,
                "validation_loss": validation_loss,
            }
        )
        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            best_epoch = epoch
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= early_stopping_patience:
            break

    if best_state is None:
        raise RuntimeError("training did not produce a model state")
    model.load_state_dict(best_state)
    predictions = _predict(model, test_loader, device)
    y_true = [class_names[index] for index in targets[split.test].tolist()]
    y_pred = [class_names[index] for index in predictions.tolist()]
    report = classification_report(y_true, y_pred, labels=class_names)
    result = BaselineResult(
        report=report,
        best_epoch=best_epoch,
        epochs_completed=len(history),
        best_validation_loss=best_validation_loss,
        split_counts={
            "train": int(split.train.size),
            "validation": int(split.validation.size),
            "test": int(split.test.size),
        },
        device=str(device),
        history=tuple(history),
    )
    return result, model


def write_checkpoint_atomic(
    model: nn.Module,
    path: str | Path,
    *,
    metadata: Mapping[str, Any],
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        dir=output.parent, prefix=f".{output.name}.", suffix=".tmp"
    )
    os.close(handle)
    try:
        torch.save({"state_dict": model.state_dict(), "metadata": dict(metadata)}, temporary_name)
        os.replace(temporary_name, output)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return output


def write_result_json(result: BaselineResult, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output
