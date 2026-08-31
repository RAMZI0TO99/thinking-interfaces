from __future__ import annotations

import unittest

import numpy as np

from core.contracts import Epoch
from data.unified import UnifiedArtifact, artifact_epoch_records


class UnifiedArtifactTests(unittest.TestCase):
    def test_every_dataset_uses_the_same_epoch_record_type(self) -> None:
        artifact = UnifiedArtifact(
            np.zeros((2, 3, 8), dtype=np.float32),
            np.asarray(["left", "right"]),
            np.asarray(["0", "0"]),
            np.asarray(["0", "0"]),
            np.asarray([0, 1]),
            ("C3", "Cz", "C4"),
        )
        for dataset, subject in (("bci_iv_2a", "A01"), ("cho2017", "01"), ("mmidb", "S001")):
            records = artifact_epoch_records(
                artifact, dataset=dataset, subject_id=subject, sampling_rate_hz=128.0
            )
            self.assertTrue(all(isinstance(record, Epoch) for record in records))
            self.assertTrue(all(record.dataset == dataset for record in records))
