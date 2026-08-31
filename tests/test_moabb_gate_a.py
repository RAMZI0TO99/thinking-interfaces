from __future__ import annotations

import unittest

import numpy as np

from data.moabb_gate_a import apply_common_average_reference


class CommonAverageReferenceTests(unittest.TestCase):
    def test_channel_mean_is_zero_after_reference(self) -> None:
        signals = np.asarray([[[1.0, 2.0], [3.0, 6.0]]], dtype=np.float32)
        referenced = apply_common_average_reference(signals)
        np.testing.assert_allclose(referenced.mean(axis=1), 0.0)
        self.assertEqual(referenced.dtype, np.float32)

    def test_invalid_shape_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "shape"):
            apply_common_average_reference(np.zeros((2, 4), dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
