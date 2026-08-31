from __future__ import annotations

import tempfile
import unittest
from gc import collect as collect_garbage
from pathlib import Path

import numpy as np

from evaluation.baselines import FilterBankCSP, TangentSpaceLogistic


class ClassicalBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(3)
        self.epochs = rng.normal(size=(20, 4, 128)).astype(np.float32)
        self.labels = np.asarray([0, 1] * 10)
        self.epochs[self.labels == 1, 0] *= 2

    def test_tangent_space_probability_shape(self) -> None:
        model = TangentSpaceLogistic().fit(self.epochs, self.labels)
        probabilities = model.predict_proba(self.epochs[:3])
        self.assertEqual(probabilities.shape, (3, 2))
        np.testing.assert_allclose(probabilities.sum(axis=1), 1.0, atol=1e-6)

    def test_filter_bank_csp_probability_shape(self) -> None:
        model = FilterBankCSP(
            sampling_rate_hz=128.0,
            bands_hz=((8.0, 12.0), (12.0, 20.0)),
        )
        bands = model.filtered_bands(self.epochs)
        model.fit_prefiltered(bands, self.labels)
        probabilities = model.predict_proba_prefiltered(
            tuple(band[:3] for band in bands)
        )
        self.assertEqual(probabilities.shape, (3, 2))

    def test_filter_bank_csp_handles_regularized_multiclass_covariance(self) -> None:
        rng = np.random.default_rng(4)
        epochs = rng.normal(size=(40, 4, 128)).astype(np.float32)
        labels = np.asarray([0, 1, 2, 3] * 10)
        model = FilterBankCSP(
            sampling_rate_hz=128.0,
            bands_hz=((8.0, 12.0),),
        ).fit(epochs, labels)
        self.assertEqual(model.predict_proba(epochs[:2]).shape, (2, 4))

    def test_filter_bank_memmap_matches_in_memory_filtering(self) -> None:
        model = FilterBankCSP(
            sampling_rate_hz=128.0,
            bands_hz=((8.0, 12.0),),
        )
        expected = model.filtered_bands(self.epochs)[0]
        with tempfile.TemporaryDirectory() as directory:
            actual = model.filtered_bands_memmap(
                self.epochs, Path(directory), chunk_trials=3
            )[0]
            copied = actual.copy()
            del actual
            collect_garbage()
            np.testing.assert_allclose(copied, expected, rtol=1e-6, atol=1e-7)
