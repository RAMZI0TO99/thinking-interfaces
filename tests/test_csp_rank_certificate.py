from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from evaluation.baselines import FilterBankCSP
from evaluation.csp_rank_certificate import full_rank_certificate


class RankCertificateTests(unittest.TestCase):
    def test_certificate_agrees_with_original_mne_rank_across_scales(self) -> None:
        from mne import create_info
        from mne.cov import _compute_rank_raw_array

        rng = np.random.default_rng(25)
        for scale in (1e-12, 1.0, 1e6):
            with self.subTest(scale=scale):
                epochs = rng.normal(size=(20, 4, 128)) * scale
                certificate = full_rank_certificate(epochs, sample_columns=128, chunk_trials=3)
                actual = _compute_rank_raw_array(
                    np.hstack(epochs),
                    create_info(4, 1000, "mag"),
                    rank=None,
                    scalings=None,
                    verbose="ERROR",
                )
                self.assertTrue(certificate.certified)
                self.assertEqual(certificate.mne_rank, actual)

    def test_rank_deficiency_zero_and_unsampled_direction_are_inconclusive(self) -> None:
        rng = np.random.default_rng(26)
        epochs = rng.normal(size=(10, 4, 64))
        epochs[:, 3] = epochs[:, 0] + epochs[:, 1]
        self.assertIsNone(full_rank_certificate(epochs).mne_rank)
        self.assertIsNone(full_rank_certificate(np.zeros_like(epochs)).mne_rank)
        sparse = np.zeros((1, 2, 10))
        sparse[0, 0] = 1
        sparse[0, 1, 4] = 1
        self.assertIsNone(full_rank_certificate(sparse, sample_columns=2).mne_rank)
        self.assertTrue(full_rank_certificate(sparse, sample_columns=10).certified)

    def test_mean_reference_in_float64_does_not_force_full_rank(self) -> None:
        rng = np.random.default_rng(27)
        epochs = rng.normal(size=(20, 8, 128))
        epochs -= epochs.mean(axis=1, keepdims=True)
        self.assertFalse(full_rank_certificate(epochs).certified)

    def test_csp_probabilities_match_exactly_with_and_without_certification(self) -> None:
        rng = np.random.default_rng(28)
        epochs = rng.normal(size=(20, 4, 128)).astype(np.float32)
        labels = np.asarray([0, 1] * 10)
        settings = {"sampling_rate_hz": 128.0, "bands_hz": ((8.0, 12.0), (12.0, 20.0))}
        reference = FilterBankCSP(**settings).fit(epochs, labels)
        candidate = FilterBankCSP(**settings, certify_rank=True).fit(epochs, labels)
        self.assertTrue(all(row.certified for row in candidate.rank_certificates))
        np.testing.assert_array_equal(
            candidate.predict_proba(epochs), reference.predict_proba(epochs)
        )

    def test_invalid_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            full_rank_certificate(np.full((2, 4, 64), np.nan))
        with self.assertRaises(ValueError):
            full_rank_certificate(np.zeros((2, 4, 64)), sample_columns=0)

    def test_unreviewed_mne_version_uses_original_rank_calculation(self) -> None:
        rng = np.random.default_rng(29)
        epochs = rng.normal(size=(20, 4, 128)).astype(np.float32)
        labels = np.asarray([0, 1] * 10)
        settings = {"sampling_rate_hz": 128.0, "bands_hz": ((8.0, 12.0),)}
        reference = FilterBankCSP(**settings).fit(epochs, labels)
        with patch("evaluation.baselines.version", return_value="unreviewed"):
            candidate = FilterBankCSP(**settings, certify_rank=True).fit(epochs, labels)
        self.assertEqual(candidate.rank_certificates, [])
        np.testing.assert_array_equal(
            candidate.predict_proba(epochs), reference.predict_proba(epochs)
        )
