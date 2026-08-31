from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pylsl import StreamInfo

from realtime.lsl import LSLInletStream


class LSLMetadataTests(unittest.TestCase):
    def test_channel_metadata_comes_from_full_inlet_info_not_discovery(self):
        discovery = MagicMock()
        full = StreamInfo("test", "EEG", 2, 128, "float32", "local-test")
        channels = full.desc().append_child("channels")
        for name in ("C3", "C4"):
            channels.append_child("channel").append_child_value("label", name)
        inlet = MagicMock()
        inlet.info.return_value = full
        with (
            patch("realtime.lsl.resolve_byprop", return_value=[discovery]),
            patch("realtime.lsl.StreamInlet", return_value=inlet),
        ):
            stream = LSLInletStream.resolve("test")
            self.assertEqual(stream.channel_names, ("C3", "C4"))
            self.assertEqual(stream.sampling_rate_hz, 128)
            discovery.desc.assert_not_called()
            stream.close()
            inlet.close_stream.assert_called_once()

    def test_missing_channel_names_are_rejected(self):
        inlet = MagicMock()
        inlet.info.return_value = StreamInfo("test", "EEG", 2, 128, "float32", "local-test")
        with (
            patch("realtime.lsl.resolve_byprop", return_value=[MagicMock()]),
            patch("realtime.lsl.StreamInlet", return_value=inlet),
            self.assertRaises(ValueError),
        ):
            LSLInletStream.resolve("test")
        inlet.close_stream.assert_called_once()
