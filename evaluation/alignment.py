"""Euclidean Alignment fitted only from the permitted domain data."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float32]


def covariance(epoch: NDArray[np.floating]) -> NDArray[np.float64]:
    values = np.asarray(epoch, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] < 2:
        raise ValueError("epoch must have shape (channels, at least two samples)")
    centered = values - values.mean(axis=1, keepdims=True)
    return np.asarray(centered @ centered.T / (values.shape[1] - 1), dtype=np.float64)


class EuclideanAlignment:
    """Whiten epochs by the inverse square root of their domain mean covariance."""

    def __init__(self, *, regularization: float = 1e-6) -> None:
        if regularization <= 0:
            raise ValueError("regularization must be positive")
        self.regularization = regularization
        self.whitener_: NDArray[np.float64] | None = None

    def fit(self, reference_epochs: NDArray[np.floating]) -> EuclideanAlignment:
        values = np.asarray(reference_epochs, dtype=np.float64)
        if values.ndim != 3 or values.shape[0] < 1:
            raise ValueError("reference epochs must have shape (trials, channels, samples)")
        mean_covariance = np.mean([covariance(epoch) for epoch in values], axis=0)
        scale = float(np.trace(mean_covariance) / mean_covariance.shape[0])
        stabilized = mean_covariance + np.eye(mean_covariance.shape[0]) * (
            self.regularization * max(scale, np.finfo(float).eps)
        )
        eigenvalues, eigenvectors = np.linalg.eigh(stabilized)
        inverse_sqrt = np.diag(1.0 / np.sqrt(np.maximum(eigenvalues, np.finfo(float).eps)))
        self.whitener_ = eigenvectors @ inverse_sqrt @ eigenvectors.T
        return self

    def transform(self, epochs: NDArray[np.floating]) -> FloatArray:
        if self.whitener_ is None:
            raise RuntimeError("EuclideanAlignment must be fitted before transform")
        values = np.asarray(epochs, dtype=np.float64)
        if values.ndim != 3 or values.shape[1] != self.whitener_.shape[0]:
            raise ValueError("epoch channel count does not match the fitted reference")
        return np.asarray(np.einsum("ij,tjs->tis", self.whitener_, values), dtype=np.float32)

    def fit_transform(self, epochs: NDArray[np.floating]) -> FloatArray:
        return self.fit(epochs).transform(epochs)


def align_training_subjects(
    epochs: NDArray[np.floating], subject_ids: NDArray[np.str_]
) -> FloatArray:
    """Fit one alignment matrix per source subject and preserve trial order."""

    values = np.asarray(epochs)
    subjects = np.asarray(subject_ids)
    if values.ndim != 3 or subjects.shape != (values.shape[0],):
        raise ValueError("epochs and subject_ids have incompatible shapes")
    aligned = np.empty(values.shape, dtype=np.float32)
    for subject in sorted(set(subjects.tolist())):
        mask = subjects == subject
        aligned[mask] = EuclideanAlignment().fit_transform(values[mask])
    return aligned
