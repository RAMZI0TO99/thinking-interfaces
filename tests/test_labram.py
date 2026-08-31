from __future__ import annotations

import unittest

import numpy as np

from encoder.labram import electrode_embedding_indices, mask_electrodes_by_name


class LaBraMUtilityTests(unittest.TestCase):
    def test_electrode_mapping_is_name_based_and_cls_offset(self) -> None:
        indices = electrode_embedding_indices(("Fp1", "Cz", "POz"))
        self.assertEqual(len(indices), 3)
        self.assertTrue(all(index > 0 for index in indices))
        self.assertEqual(len(set(indices)), 3)

    def test_masking_uses_names_not_positions(self) -> None:
        values = np.ones((2, 3, 5), dtype=np.float32)
        masked = mask_electrodes_by_name(values, ("C3", "Cz", "C4"), ("Cz",))
        np.testing.assert_array_equal(masked[:, 1], 0.0)
        np.testing.assert_array_equal(masked[:, 0], 1.0)
