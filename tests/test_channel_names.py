from __future__ import annotations

import unittest

from data.channel_names import canonicalize_channel_names


class ChannelNameTests(unittest.TestCase):
    def test_mmidb_dot_padding_and_case_are_canonicalized(self) -> None:
        self.assertEqual(
            canonicalize_channel_names(("Fc3.", "C3..", "FP1", "CZ")),
            ("FC3", "C3", "Fp1", "Cz"),
        )

    def test_collisions_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unique"):
            canonicalize_channel_names(("C3.", "C3.."))
