"""Read-only plan and explicit execution admission tests; no training."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts import run_cho_first_tranche as cli


def _arguments(tmp_path: Path) -> list[str]:
    return [
        "--pins",
        str(tmp_path / "pins.json"),
        "--pins-sha256",
        "a" * 64,
        "--method",
        "eegnet",
        "--subject",
        "subject_01",
        "--seed",
        "11",
    ]


def test_plan_is_default_and_never_calls_executor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "load_execution_pins", lambda *args: {"source_sha256": "b" * 64})

    def forbidden(**kwargs: Any) -> dict[str, Any]:
        raise AssertionError("read-only planning must not launch a child")

    monkeypatch.setattr(cli, "execute_engineering_cases", forbidden)
    assert cli.main(_arguments(tmp_path)) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["case_count"] == 1
    assert plan["training_performed"] is False and plan["compute_admitted"] is False
    assert plan["analysis_executed"] is False


def test_dry_run_overrides_execute_without_implicit_limits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "load_execution_pins", lambda *args: {"source_sha256": "b" * 64})
    assert cli.main(_arguments(tmp_path) + ["--mode", "execute", "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["compute_admitted"] is False


def test_execute_requires_every_explicit_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "load_execution_pins", lambda *args: {"source_sha256": "b" * 64})
    with pytest.raises(ValueError, match="every explicit"):
        cli.main(_arguments(tmp_path) + ["--mode", "execute"])


def test_analysis_is_honestly_unwired(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="analysis is not wired"):
        cli.main(_arguments(tmp_path) + ["--mode", "analysis"])


def test_execute_passes_explicit_bounded_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "load_execution_pins", lambda *args: {"source_sha256": "b" * 64})
    captured: dict[str, Any] = {}

    def execute(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"completed_cases": 1, "planned_cases": 1}

    monkeypatch.setattr(cli, "execute_engineering_cases", execute)
    assert (
        cli.main(
            _arguments(tmp_path)
            + [
                "--mode",
                "execute",
                "--admission",
                str(tmp_path / "admission.json"),
                "--receipt",
                str(tmp_path / "receipt.json"),
                "--execution-memory-limit-bytes",
                "6442450944",
                "--attempt-seconds",
                "600",
                "--session-seconds",
                "7200",
                "--torch-threads",
                "1",
            ]
        )
        == 0
    )
    assert captured["limits"].process_memory_limit_bytes == 6442450944
    assert captured["limits"].attempt_seconds == 600
    assert len(captured["cases"]) == 1
