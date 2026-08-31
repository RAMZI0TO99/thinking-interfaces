"""Gate-driven interface state and optional desktop renderer."""

from __future__ import annotations

from dataclasses import dataclass

from realtime.accumulated_evidence import EvidenceUpdate
from realtime.confidence_gate import GateDecision


@dataclass(frozen=True, slots=True)
class InterfaceFrame:
    target: str
    decision_state: str
    confidence: float
    confidence_bar: str
    emitted_command: str | None
    latency_ms: float


class GateDrivenInterface:
    """State model that accepts gate decisions, never raw probabilities."""

    def __init__(self, *, target: str, bar_width: int = 20) -> None:
        if not target or bar_width < 1:
            raise ValueError("target and a positive bar width are required")
        self.target = target
        self.bar_width = bar_width
        self.frames: list[InterfaceFrame] = []

    def update(
        self,
        decision: GateDecision,
        evidence: EvidenceUpdate,
        *,
        latency_ms: float,
    ) -> InterfaceFrame:
        filled = min(self.bar_width, round(decision.confidence * self.bar_width))
        bar = "#" * filled + "-" * (self.bar_width - filled)
        frame = InterfaceFrame(
            self.target,
            decision.state,
            decision.confidence,
            bar,
            evidence.emitted_command,
            latency_ms,
        )
        self.frames.append(frame)
        return frame

    @staticmethod
    def render_text(frame: InterfaceFrame) -> str:
        emitted = frame.emitted_command or "none"
        return (
            f"target={frame.target} state={frame.decision_state} "
            f"confidence=[{frame.confidence_bar}] {frame.confidence:.1%} "
            f"command={emitted} latency={frame.latency_ms:.2f}ms"
        )
