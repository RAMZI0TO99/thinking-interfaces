from __future__ import annotations

import unittest

import numpy as np

from evaluation.alignment import EuclideanAlignment, align_training_subjects, covariance


class EuclideanAlignmentTests(unittest.TestCase):
    def test_fitted_mean_covariance_is_identity(self) -> None:
        rng = np.random.default_rng(1)
        epochs = rng.normal(size=(20, 3, 100)).astype(np.float32)
        epochs[:, 0] *= 3
        aligned = EuclideanAlignment(regularization=1e-9).fit_transform(epochs)
        mean_covariance = np.mean([covariance(epoch) for epoch in aligned], axis=0)
        np.testing.assert_allclose(mean_covariance, np.eye(3), atol=1e-5)

    def test_training_domains_are_aligned_separately(self) -> None:
        rng = np.random.default_rng(2)
        epochs = rng.normal(size=(8, 2, 40)).astype(np.float32)
        epochs[4:] *= 5
        result = align_training_subjects(epochs, np.asarray(["A"] * 4 + ["B"] * 4))
        self.assertEqual(result.shape, epochs.shape)
