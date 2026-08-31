from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, patch

from core.gpu_cooling import CoolingPolicy, cool_gpu, read_gpu_temperature


class CoolingTests(unittest.TestCase):
    policy = CoolingPolicy(80, 76, 5, 5, 15)

    def test_cool_device_has_no_unnecessary_pause(self):
        pause = Mock()
        self.assertEqual(cool_gpu(self.policy, temperature_reader=lambda: 74, sleep=pause), 0)
        pause.assert_not_called()

    def test_hot_device_must_reach_resume_temperature(self):
        pause = Mock()
        self.assertEqual(
            cool_gpu(self.policy, temperature_reader=Mock(side_effect=[82, 78, 76]), sleep=pause),
            10,
        )
        self.assertEqual(pause.call_count, 2)

    def test_missing_sensor_keeps_the_previous_five_second_delay(self):
        pause = Mock()
        self.assertEqual(cool_gpu(self.policy, temperature_reader=lambda: None, sleep=pause), 5)
        pause.assert_called_once_with(5)

    def test_known_hot_sensor_failure_and_no_cooling_stop_the_batch(self):
        with self.assertRaisesRegex(RuntimeError, "sensor failed"):
            cool_gpu(self.policy, temperature_reader=Mock(side_effect=[81, None]), sleep=Mock())
        with self.assertRaisesRegex(RuntimeError, "did not cool"):
            cool_gpu(self.policy, temperature_reader=lambda: 81, sleep=Mock())

    def test_malformed_or_failed_temperature_reads_are_not_trusted(self):
        with patch("core.gpu_cooling.shutil.which", return_value="nvidia-smi"):
            for output, code in (("N/A", 0), ("79", 1), ("", 0), ("999", 0)):
                with (
                    self.subTest(output=output, code=code),
                    patch(
                        "core.gpu_cooling.subprocess.run",
                        return_value=subprocess.CompletedProcess([], code, output, ""),
                    ),
                ):
                    self.assertIsNone(read_gpu_temperature())
            with patch(
                "core.gpu_cooling.subprocess.run",
                return_value=subprocess.CompletedProcess([], 0, "74\n79\n", ""),
            ):
                self.assertEqual(read_gpu_temperature(), 79)
