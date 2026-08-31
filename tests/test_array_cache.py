from __future__ import annotations

import tempfile
import unittest
from gc import collect as collect_garbage
from pathlib import Path
from unittest.mock import patch

import numpy as np

from data.array_cache import verified_float32_cache
from evaluation.baselines import FilterBankCSP


class ArrayCacheTests(unittest.TestCase):
    def test_unsealed_or_corrupt_array_is_rebuilt_and_verified_array_is_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.npy"
            np.save(path, np.zeros((2, 3), dtype=np.float32))
            fills = []

            def fill(target):
                fills.append(1)
                target[:] = 7

            for iteration in range(3):
                result = verified_float32_cache(path, shape=(2, 3), key="input-a", fill=fill)
                np.testing.assert_array_equal(result, np.full((2, 3), 7))
                del result
                collect_garbage()
                if iteration == 1:
                    np.save(path, np.zeros((2, 3), dtype=np.float32))
            self.assertEqual(len(fills), 2)

    def test_interrupted_fill_does_not_publish_a_complete_looking_array(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.npy"

            def interrupted(target):
                target[0] = 1
                raise RuntimeError("simulated interruption")

            with self.assertRaisesRegex(RuntimeError, "interruption"):
                verified_float32_cache(path, shape=(2, 3), key="input-a", fill=interrupted)
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_filter_cache_reuse_requires_matching_signal_content(self):
        rng = np.random.default_rng(12)
        epochs = rng.normal(size=(6, 2, 128)).astype(np.float32)
        model = FilterBankCSP(sampling_rate_hz=128, bands_hz=((8, 12),))
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            first = model.filtered_bands_memmap(epochs, cache, chunk_trials=2)[0]
            expected = first.copy()
            del first
            collect_garbage()
            with patch.object(
                model, "_filtered", side_effect=AssertionError("valid cache must be reused")
            ):
                reused = model.filtered_bands_memmap(epochs, cache)[0]
                np.testing.assert_array_equal(reused, expected)
                del reused
                collect_garbage()
            changed = model.filtered_bands_memmap(epochs * 2, cache, chunk_trials=3)[0]
            np.testing.assert_array_equal(changed, expected * 2)
            del changed
            collect_garbage()
