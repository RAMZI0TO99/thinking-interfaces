"""Consecutive-decision evidence accumulation for real-time commands."""

from __future__ import annotations

from dataclasses import dataclass

from realtime.confidence_gate import GateDecision


@dataclass(frozen=True, slots=True)
class EvidenceUpdate:
    observed_state: str
    candidate_state: str
    consecutive_count: int
    emitted_command: str | None


class AccumulatedEvidence:
    """Emit once after N identical, consecutive, non-neutral decisions."""

    def __init__(self, *, required_consecutive: int, neutral_state: str = "neutral") -> None:
        if required_consecutive < 1:
            raise ValueError("required_consecutive must be positive")
        if not neutral_state:
            raise ValueError("neutral_state must be non-empty")
        self.required_consecutive = required_consecutive
        self.neutral_state = neutral_state
        self._candidate_state = neutral_state
        self._consecutive_count = 0
        self._latched = False

    def reset(self) -> None:
        self._candidate_state = self.neutral_state
        self._consecutive_count = 0
        self._latched = False

    def update(self, decision: GateDecision) -> EvidenceUpdate:
        if decision.abstained != (decision.state == self.neutral_state):
            raise ValueError("gate abstention and neutral state are inconsistent")
        if decision.abstained:
            self.reset()
            return EvidenceUpdate(
                observed_state=decision.state,
                candidate_state=self.neutral_state,
                consecutive_count=0,
                emitted_command=None,
            )

        if decision.state != self._candidate_state:
            self._candidate_state = decision.state
            self._consecutive_count = 1
            self._latched = False
        else:
            self._consecutive_count += 1

        emitted: str | None = None
        if self._consecutive_count >= self.required_consecutive and not self._latched:
            emitted = self._candidate_state
            self._latched = True
        return EvidenceUpdate(
            observed_state=decision.state,
            candidate_state=self._candidate_state,
            consecutive_count=self._consecutive_count,
            emitted_command=emitted,
        )
