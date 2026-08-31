from __future__ import annotations

import unittest

import numpy as np

from realtime.accumulated_evidence import AccumulatedEvidence
from realtime.confidence_gate import GateDecision, confidence_gate


def accepted(state: str, index: int = 0) -> GateDecision:
    return GateDecision(state=state, confidence=0.9, abstained=False, winning_index=index)


def neutral() -> GateDecision:
    return GateDecision(state="neutral", confidence=0.4, abstained=True, winning_index=None)


class AccumulatedEvidenceTests(unittest.TestCase):
    def test_emits_once_on_required_consecutive_decision(self) -> None:
        evidence = AccumulatedEvidence(required_consecutive=3)
        self.assertIsNone(evidence.update(accepted("left")).emitted_command)
        self.assertIsNone(evidence.update(accepted("left")).emitted_command)
        self.assertEqual(evidence.update(accepted("left")).emitted_command, "left")
        self.assertIsNone(evidence.update(accepted("left")).emitted_command)

    def test_class_change_restarts_count(self) -> None:
        evidence = AccumulatedEvidence(required_consecutive=2)
        evidence.update(accepted("left"))
        update = evidence.update(accepted("right", 1))
        self.assertEqual(update.candidate_state, "right")
        self.assertEqual(update.consecutive_count, 1)
        self.assertIsNone(update.emitted_command)
        self.assertEqual(evidence.update(accepted("right", 1)).emitted_command, "right")

    def test_neutral_resets_and_releases_latch(self) -> None:
        evidence = AccumulatedEvidence(required_consecutive=1)
        self.assertEqual(evidence.update(accepted("left")).emitted_command, "left")
        reset = evidence.update(neutral())
        self.assertEqual(reset.candidate_state, "neutral")
        self.assertEqual(reset.consecutive_count, 0)
        self.assertEqual(evidence.update(accepted("left")).emitted_command, "left")

    def test_inconsistent_gate_decision_is_rejected(self) -> None:
        evidence = AccumulatedEvidence(required_consecutive=2)
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            evidence.update(
                GateDecision(
                    state="left", confidence=0.2, abstained=True, winning_index=None
                )
            )

    def test_probability_to_command_integration(self) -> None:
        evidence = AccumulatedEvidence(required_consecutive=3)
        probabilities = np.asarray([0.8, 0.1, 0.05, 0.05])
        labels = ("left", "right", "feet", "tongue")
        commands = [
            evidence.update(
                confidence_gate(probabilities, labels, threshold=0.7)
            ).emitted_command
            for _ in range(3)
        ]
        self.assertEqual(commands, [None, None, "left"])
