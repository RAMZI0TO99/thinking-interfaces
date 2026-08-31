"""Temperature-aware inter-fold pauses without changing GPU power or clock settings."""

from __future__ import annotations

import math
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from core.config import load_toml


@dataclass(frozen=True, slots=True)
class CoolingPolicy:
    pause_at_celsius: int
    resume_at_or_below_celsius: int
    poll_seconds: float
    fallback_delay_seconds: float
    maximum_cooling_sleep_seconds: float

    def __post_init__(self) -> None:
        if not 0 < self.resume_at_or_below_celsius < self.pause_at_celsius <= 85:
            raise ValueError("invalid conservative GPU temperature limits")
        if (
            any(
                not math.isfinite(value) or value <= 0
                for value in (
                    self.poll_seconds,
                    self.fallback_delay_seconds,
                    self.maximum_cooling_sleep_seconds,
                )
            )
            or self.poll_seconds > self.maximum_cooling_sleep_seconds
        ):
            raise ValueError("cooling delays must be positive, finite and bounded")


def load_cooling_policy(path: Path) -> CoolingPolicy:
    config = cast(Mapping[str, Any], load_toml(path)["gpu"])
    return CoolingPolicy(**config)


def read_gpu_temperature() -> int | None:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return None
    try:
        result = subprocess.run(
            [executable, "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        temperatures = [int(line.strip()) for line in result.stdout.splitlines()]
        if (
            result.returncode
            or not temperatures
            or any(not 0 <= value <= 120 for value in temperatures)
        ):
            return None
        return max(temperatures)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def cool_gpu(
    policy: CoolingPolicy,
    *,
    temperature_reader: Callable[[], int | None] = read_gpu_temperature,
    sleep: Callable[[float], None] = time.sleep,
) -> float:
    """Return scheduled pause seconds; fail closed if a known-hot GPU cannot cool."""
    temperature = temperature_reader()
    if temperature is None:
        sleep(policy.fallback_delay_seconds)
        return policy.fallback_delay_seconds
    if temperature < policy.pause_at_celsius:
        return 0.0
    print(
        f"GPU temperature {temperature} C; waiting for <= "
        f"{policy.resume_at_or_below_celsius} C before the next fold.",
        flush=True,
    )
    slept = 0.0
    while temperature > policy.resume_at_or_below_celsius:
        if slept >= policy.maximum_cooling_sleep_seconds:
            raise RuntimeError(
                "GPU did not cool within the pause budget; completed records are safe"
            )
        pause = min(policy.poll_seconds, policy.maximum_cooling_sleep_seconds - slept)
        sleep(pause)
        slept += pause
        temperature = temperature_reader()
        if temperature is None:
            raise RuntimeError("GPU sensor failed while cooling a known-hot device; batch stopped")
    return slept
