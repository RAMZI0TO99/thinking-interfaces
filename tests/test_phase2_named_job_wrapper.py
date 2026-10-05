"""Named-Job dispatch regressions using instance-bound fakes; no native Jobs."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import pytest

from evaluation import phase2_cho_execution as execution
from evaluation import phase2_supervision_primitives as primitive
from evaluation.phase2_supervision_primitives import (
    GIB,
    ResourceFloor,
    ResourceSample,
    SupervisionError,
    SupervisionResult,
)


def _fake_api(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[type[Any], list[tuple[object, object]], object]:
    calls: list[tuple[object, object]] = []
    handle = object()

    class FakeApi:
        def __init__(self) -> None:
            # The native API assigns this callable per instance. A class-level
            # replacement cannot override this binding and must fail the test.
            def create_job(attributes: object, name: object) -> object:
                calls.append((attributes, name))
                return handle

            self.create_job = create_job

    monkeypatch.setattr(primitive, "_WinApi", FakeApi)
    return FakeApi, calls, handle


def _default_supervisor(
    monkeypatch: pytest.MonkeyPatch,
    supervisor: Callable[..., SupervisionResult],
) -> None:
    monkeypatch.setattr(execution, "run_supervised", supervisor)
    # Python captures defaults at definition time. Replace that captured
    # callable too so omitting `supervisor` exercises the real default branch
    # while every underlying process operation remains mocked.
    defaults = execution.supervise_attempt.__kwdefaults__
    assert defaults is not None
    monkeypatch.setattr(
        execution.supervise_attempt, "__kwdefaults__", {**defaults, "supervisor": supervisor}
    )


def _contract() -> dict[str, Any]:
    return {
        "schema": "cho_engineering_child_contract_v1",
        "job_name": "pro3_choexec_0123456789abcdef0123456789abcdef",
        "deadline_path": "lease.json",
        "source_sha256": "a" * 64,
        "limits": {"process_memory_limit_bytes": execution.INITIAL_PROBE_MAX_MEMORY_BYTES},
    }


def _ample_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        execution, "_resources", lambda root, launching: ResourceSample(21 * GIB, 11 * GIB)
    )


def test_named_wrapper_replaces_instance_binding_and_restores_after_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_api, calls, handle = _fake_api(monkeypatch)
    job_name = _contract()["job_name"]
    attributes = object()
    command = ["synthetic-child", "--contract", "contract.json"]
    forwarded: dict[str, Any] = {}
    expected = SupervisionResult(123, 0, "normal", 1024, 2048)

    def supervised(child_command: Sequence[str], **kwargs: Any) -> SupervisionResult:
        assert primitive._WinApi is not original_api
        assert issubclass(primitive._WinApi, original_api)
        first, second = primitive._WinApi(), primitive._WinApi()
        assert first is not second
        assert first.create_job(None, None) is handle
        assert second.create_job(attributes, "unselected-name") is handle
        forwarded.update(command=child_command, kwargs=kwargs)
        return expected

    monkeypatch.setattr(execution, "run_supervised", supervised)
    supervisor = execution._named_job_supervisor(job_name)
    assert primitive._WinApi is original_api
    assert supervisor(command, marker="preserved") is expected
    assert forwarded == {"command": command, "kwargs": {"marker": "preserved"}}
    assert calls == [(None, job_name), (attributes, job_name)]
    assert primitive._WinApi is original_api
    # A subsequent ordinary API instance must still receive its caller's name.
    original_api().create_job(None, "ordinary-name")
    assert calls[-1] == (None, "ordinary-name")


def test_named_wrapper_restores_original_class_when_supervision_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_api, calls, handle = _fake_api(monkeypatch)
    job_name = _contract()["job_name"]
    failure = SupervisionError("synthetic native supervision failure")

    def refuse(child_command: Sequence[str], **kwargs: Any) -> SupervisionResult:
        assert primitive._WinApi is not original_api
        assert primitive._WinApi().create_job(None, None) is handle
        raise failure

    monkeypatch.setattr(execution, "run_supervised", refuse)
    supervisor = execution._named_job_supervisor(job_name)
    with pytest.raises(SupervisionError) as caught:
        supervisor(["synthetic-child"])
    assert caught.value is failure
    assert calls == [(None, job_name)]
    assert primitive._WinApi is original_api


def test_default_attempt_dispatch_binds_contract_job_and_restores_before_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_api, calls, handle = _fake_api(monkeypatch)
    _ample_resources(monkeypatch)
    contract = _contract()
    expected = SupervisionResult(123, 0, "normal", 1024, 2048)
    command = ["synthetic-child", "--contract", "contract.json"]
    forwarded: dict[str, Any] = {}
    acceptance_calls: list[str] = []

    def supervised(child_command: Sequence[str], **kwargs: Any) -> SupervisionResult:
        assert primitive._WinApi is not original_api
        assert primitive._WinApi().create_job(None, None) is handle
        forwarded.update(command=child_command, kwargs=kwargs)
        return expected

    def accept() -> dict[str, Any]:
        assert primitive._WinApi is original_api
        acceptance_calls.append("parent-attestation")
        return {"verified": True}

    _default_supervisor(monkeypatch, supervised)
    receipt = execution.supervise_attempt(
        root=tmp_path,
        attempt_dir=tmp_path,
        contract=contract,
        contract_sha256="c" * 64,
        command=command,
        accept=accept,
    )
    assert calls == [(None, contract["job_name"])]
    assert forwarded == {
        "command": command,
        "kwargs": {
            "cwd": tmp_path,
            "deadline_path": tmp_path / "lease.json",
            "floor": ResourceFloor(),
            "process_memory_limit_bytes": contract["limits"]["process_memory_limit_bytes"],
        },
    }
    assert acceptance_calls == ["parent-attestation"]
    assert receipt["status"] == "complete"
    assert receipt["reason"] == "timely_parent_attestation"
    assert receipt["accepted"] == {"verified": True}
    assert receipt["engineering_cell_count"] == 1
    assert receipt["scientific_claims_made"] == 0
    assert receipt["gate_a_signed"] is False
    assert json.loads((tmp_path / "receipt.json").read_bytes()) == receipt
    assert primitive._WinApi is original_api


@pytest.mark.parametrize("job_name", [None, "", False])
def test_default_attempt_refuses_missing_job_before_resources_or_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    job_name: Any,
) -> None:
    original_api, calls, _ = _fake_api(monkeypatch)
    contract = _contract()
    if job_name is None:
        del contract["job_name"]
    else:
        contract["job_name"] = job_name

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("refusal must precede resources, launch and acceptance")

    _default_supervisor(monkeypatch, unexpected)
    monkeypatch.setattr(execution, "_resources", unexpected)
    with pytest.raises(SupervisionError, match="named engineering Job required"):
        execution.supervise_attempt(
            root=tmp_path,
            attempt_dir=tmp_path,
            contract=contract,
            contract_sha256="c" * 64,
            command=["synthetic-child"],
            accept=unexpected,
        )
    assert calls == []
    assert primitive._WinApi is original_api
    assert list(tmp_path.iterdir()) == []


def test_custom_supervisor_bypasses_named_dispatch_without_contract_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_api, calls, _ = _fake_api(monkeypatch)
    _ample_resources(monkeypatch)
    contract = _contract()
    del contract["job_name"]
    command = ["synthetic-child"]
    custom_calls: list[Sequence[str]] = []

    def unexpected(job_name: str) -> Any:
        raise AssertionError("custom supervision must not use the native named wrapper")

    def custom(child_command: Sequence[str], **kwargs: Any) -> SupervisionResult:
        assert primitive._WinApi is original_api
        custom_calls.append(child_command)
        return SupervisionResult(123, 0, "normal", 1024, 2048)

    monkeypatch.setattr(execution, "_named_job_supervisor", unexpected)
    receipt = execution.supervise_attempt(
        root=tmp_path,
        attempt_dir=tmp_path,
        contract=contract,
        contract_sha256="c" * 64,
        command=command,
        accept=lambda: {"custom": True},
        supervisor=custom,
    )
    assert custom_calls == [command]
    assert calls == []
    assert primitive._WinApi is original_api
    assert receipt["status"] == "complete"
    assert receipt["accepted"] == {"custom": True}
