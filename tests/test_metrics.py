from __future__ import annotations

import unittest

from core.metrics import classification_report


class ClassificationReportTests(unittest.TestCase):
    def test_fixed_metric_set_and_class_balance(self) -> None:
        report = classification_report(
            ["left", "left", "right", "right"],
            ["left", "right", "right", "right"],
        )
        self.assertAlmostEqual(report.balanced_accuracy, 0.75)
        self.assertEqual(report.labels, ("left", "right"))
        self.assertEqual(report.confusion_matrix, ((1, 1), (0, 2)))
        self.assertEqual(report.class_support, {"left": 2, "right": 2})
        self.assertEqual(
            set(report.record_metrics()),
            {"balanced_accuracy", "cohen_kappa"},
        )

    def test_unknown_observed_label_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing"):
            classification_report(["left"], ["right"], labels=["left"])

    def test_empty_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            classification_report([], [])


if __name__ == "__main__":
    unittest.main()

