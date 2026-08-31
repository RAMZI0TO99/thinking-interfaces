from __future__ import annotations

import tempfile
import unittest
from gc import collect as collect_garbage
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from evaluation.baselines import CSP, FilterBankCSP, TangentSpaceLogistic, _csp_input


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

    def test_csp_selection_is_exact_writable_contiguous_and_bounded(self) -> None:
        class BoundedIndexing(np.ndarray):
            def __getitem__(self, key: object) -> np.ndarray:
                if isinstance(key, np.ndarray) and key.size > 3:
                    raise AssertionError("full-size float32 advanced-index copy")
                return super().__getitem__(key)

        indices = np.asarray([19, 1, 5, 2, 1, 13, 0], dtype=np.int64)
        actual = _csp_input(self.epochs.view(BoundedIndexing), indices, chunk_trials=3)
        np.testing.assert_array_equal(actual, self.epochs[indices].astype(np.float64))
        self.assertEqual(actual.dtype, np.float64)
        self.assertTrue(actual.flags.c_contiguous and actual.flags.writeable)
        readonly = actual.copy()
        readonly.setflags(write=False)
        writable = _csp_input(readonly, None)
        np.testing.assert_array_equal(writable, readonly)
        self.assertTrue(writable.flags.writeable)
        with self.assertRaises(ValueError):
            _csp_input(self.epochs, indices, chunk_trials=0)

    def test_csp_float64_selection_matches_original_mne_path_exactly(self) -> None:
        model = FilterBankCSP(
            sampling_rate_hz=128.0, bands_hz=((8.0, 12.0), (12.0, 20.0))
        )
        bands = model.filtered_bands(self.epochs)
        train = np.arange(16)
        query = np.arange(16, 20)
        reference_csps = []
        features = []
        for band in bands:
            csp = CSP(
                n_components=2, reg="oas", log=True, cov_est="concat",
                norm_trace=False, component_order="mutual_info",
            )
            features.append(csp.fit_transform(band[train], self.labels[train]))
            reference_csps.append(csp)
        classifier = LogisticRegression(max_iter=1000, class_weight="balanced").fit(
            np.concatenate(features, axis=1), self.labels[train]
        )
        expected = classifier.predict_proba(np.concatenate([
            csp.transform(band[query])
            for csp, band in zip(reference_csps, bands, strict=True)
        ], axis=1)).astype(np.float32)
        model.fit_prefiltered(bands, self.labels[train], indices=train)
        np.testing.assert_array_equal(
            model.predict_proba_prefiltered(bands, indices=query), expected
        )
