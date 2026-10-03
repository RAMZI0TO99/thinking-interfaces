"""Synthetic file-boundary tests; no Cho data, model, or cell is produced."""

from __future__ import annotations

import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event
from unittest.mock import patch

import pytest

from evaluation import phase2_case_transaction as transaction
from evaluation import phase2_supervision_primitives as supervision

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Objects only")

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _ample(_root: Path) -> supervision.ResourceSample:
    return supervision.ResourceSample(21 * supervision.GIB, 5 * supervision.GIB)


def _prepare(tmp_path: Path, *, attempt_seconds: float = 5.0) -> str:
    now = datetime.now(UTC)
    supervision.DeadlineLease.open_or_create(
        tmp_path / "deadline.json",
        attempt_deadline_utc=now + timedelta(seconds=attempt_seconds),
        session_deadline_utc=now + timedelta(seconds=6),
    )
    source = tmp_path / "source.bin"
    source.write_bytes(b"synthetic fixed source\n")
    return transaction.prepare_synthetic_contract(
        tmp_path, case_id="synthetic_case", attempt_id="a" * 32,
        source_relpath="source.bin",
        expected_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        expected_value=7,
    )


def _run(tmp_path: Path, digest: str) -> transaction.SyntheticAttestation:
    return transaction.run_synthetic_transaction(
        tmp_path, expected_contract_sha256=digest,
        cwd=_PROJECT_ROOT, sensor=_ample,
    )


def test_normal_child_proposal_and_external_attestation_replay(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    attested = _run(tmp_path, digest)
    assert attested.contract_sha256 == digest
    assert attested.child_pid > 0
    assert transaction.verify_synthetic_attestation(
        tmp_path, expected_contract_sha256=digest,
        expected_attestation_sha256=attested.attestation_sha256,
    ) == attested
    with pytest.raises(ValueError, match="preexisting proposal"):
        _run(tmp_path, digest)
    assert not (tmp_path / "cells").exists()


def test_competing_parent_cannot_start_same_attempt(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    entered = Event()
    release = Event()
    original = supervision.run_supervised

    def held_supervisor(*args: object, **kwargs: object) -> supervision.SupervisionResult:
        entered.set()
        assert release.wait(3)
        return original(*args, **kwargs)  # type: ignore[arg-type]

    with (
        patch.object(transaction, "run_supervised", held_supervisor),
        ThreadPoolExecutor(max_workers=1) as pool,
    ):
        first = pool.submit(_run, tmp_path, digest)
        assert entered.wait(2)
        with pytest.raises(ValueError, match="already started"):
            _run(tmp_path, digest)
        release.set()
        assert first.result().contract_sha256 == digest


def test_resource_samples_use_transaction_root(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    observed: list[Path] = []

    def sensor(path: Path) -> supervision.ResourceSample:
        observed.append(path)
        return _ample(path)

    transaction.run_synthetic_transaction(
        tmp_path, expected_contract_sha256=digest, cwd=_PROJECT_ROOT, sensor=sensor,
    )
    assert len(observed) >= 3
    assert set(observed) == {tmp_path.resolve()}


def test_wrong_external_contract_and_attestation_digests_fail(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    with pytest.raises(ValueError, match="missing|pin"):
        _run(tmp_path, "b" * 64)
    attested = _run(tmp_path, digest)
    with pytest.raises(ValueError, match="pin"):
        transaction.verify_synthetic_attestation(
            tmp_path, expected_contract_sha256=digest,
            expected_attestation_sha256="b" * 64,
        )
    with pytest.raises(ValueError, match="missing|pin"):
        transaction.verify_synthetic_attestation(
            tmp_path, expected_contract_sha256="b" * 64,
            expected_attestation_sha256=attested.attestation_sha256,
        )


def test_proposal_tamper_after_normal_child_exit_is_not_attested(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    original = supervision.run_supervised

    def tampering_supervisor(*args: object, **kwargs: object) -> supervision.SupervisionResult:
        result = original(*args, **kwargs)  # type: ignore[arg-type]
        proposal_path = tmp_path / "proposals" / f"{digest}.json"
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        proposal["payload"]["value"] = 8
        proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
        return result

    with (
        patch.object(transaction, "run_supervised", tampering_supervisor),
        pytest.raises(ValueError, match="external pin|schema"),
    ):
        _run(tmp_path, digest)
    assert not (tmp_path / "attestations" / f"{digest}.json").exists()


def test_source_change_after_child_exit_is_not_attested(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    original = supervision.run_supervised

    def changing_supervisor(*args: object, **kwargs: object) -> supervision.SupervisionResult:
        result = original(*args, **kwargs)  # type: ignore[arg-type]
        (tmp_path / "source.bin").write_bytes(b"changed source\n")
        return result

    with (
        patch.object(transaction, "run_supervised", changing_supervisor),
        pytest.raises(ValueError, match="source changed"),
    ):
        _run(tmp_path, digest)
    assert not (tmp_path / "attestations" / f"{digest}.json").exists()


def test_child_failure_and_deadline_never_attest(tmp_path: Path) -> None:
    failed_root = tmp_path / "failed"
    failed_root.mkdir()
    failed_digest = _prepare(failed_root)
    with pytest.raises(supervision.SupervisionError, match="did not complete normally"):
        transaction.run_synthetic_transaction(
            failed_root, expected_contract_sha256=failed_digest, cwd=_PROJECT_ROOT,
            command=[sys.executable, "-c", "raise SystemExit(3)"], sensor=_ample,
        )
    assert not (failed_root / "attestations").exists()
    with pytest.raises(ValueError, match="already started"):
        _run(failed_root, failed_digest)

    expired_root = tmp_path / "expired"
    expired_root.mkdir()
    expired_digest = _prepare(expired_root, attempt_seconds=0.35)
    with pytest.raises(supervision.SupervisionError, match="did not complete normally"):
        transaction.run_synthetic_transaction(
            expired_root, expected_contract_sha256=expired_digest, cwd=_PROJECT_ROOT,
            command=[sys.executable, "-c", "import time; time.sleep(2)"], sensor=_ample,
        )
    assert not (expired_root / "attestations").exists()


def test_deadline_change_after_exit_fails_closed(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    original = supervision.run_supervised

    def tampering_supervisor(*args: object, **kwargs: object) -> supervision.SupervisionResult:
        result = original(*args, **kwargs)  # type: ignore[arg-type]
        (tmp_path / "deadline.json").write_bytes(b"{}\n")
        return result

    with (
        patch.object(transaction, "run_supervised", tampering_supervisor),
        pytest.raises(ValueError, match="deadline differs"),
    ):
        _run(tmp_path, digest)
    assert not (tmp_path / "attestations" / f"{digest}.json").exists()


def test_resource_drop_after_exit_fails_closed(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    original = supervision.run_supervised
    child_finished = False

    def supervisor(*args: object, **kwargs: object) -> supervision.SupervisionResult:
        nonlocal child_finished
        result = original(*args, **kwargs)  # type: ignore[arg-type]
        child_finished = True
        return result

    def sensor(root: Path) -> supervision.ResourceSample:
        if child_finished:
            return supervision.ResourceSample(19 * supervision.GIB, 5 * supervision.GIB)
        return _ample(root)

    with (
        patch.object(transaction, "run_supervised", supervisor),
        pytest.raises(supervision.SupervisionError, match="floor failed"),
    ):
        transaction.run_synthetic_transaction(
            tmp_path, expected_contract_sha256=digest, cwd=_PROJECT_ROOT, sensor=sensor,
        )
    assert not (tmp_path / "attestations" / f"{digest}.json").exists()


def test_channel_resource_drop_after_exit_fails_closed(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    original = supervision.run_supervised_with_frame
    child_finished = False

    def supervisor(*args: object, **kwargs: object) -> supervision.FramedSupervisionResult:
        nonlocal child_finished
        outcome = original(*args, **kwargs)  # type: ignore[arg-type]
        child_finished = True
        return outcome

    def sensor(root: Path) -> supervision.ResourceSample:
        if child_finished:
            return supervision.ResourceSample(19 * supervision.GIB, 5 * supervision.GIB)
        return _ample(root)

    with (
        patch.object(transaction, "run_supervised_with_frame", supervisor),
        pytest.raises(supervision.SupervisionError, match="floor failed"),
    ):
        transaction.run_synthetic_transaction_channel(
            tmp_path, expected_contract_sha256=digest, cwd=_PROJECT_ROOT, sensor=sensor,
        )
    assert child_finished
    assert not (tmp_path / "proposals" / f"{digest}.json").exists()
    assert not (tmp_path / "attestations" / f"{digest}.json").exists()
    assert not (tmp_path / "cells").exists()


def test_path_escape_is_rejected(tmp_path: Path) -> None:
    _prepare(tmp_path)
    source_sha = hashlib.sha256((tmp_path / "source.bin").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="relative"):
        transaction.prepare_synthetic_contract(
            tmp_path, case_id="escape", attempt_id="b" * 32,
            source_relpath="../outside.bin", expected_source_sha256=source_sha,
            expected_value=1,
        )
    with pytest.raises(ValueError, match="relative"):
        transaction.prepare_synthetic_contract(
            tmp_path, case_id="escape", attempt_id="b" * 32,
            source_relpath="C:/outside.bin", expected_source_sha256=source_sha,
            expected_value=1,
        )


def test_linked_source_is_rejected_when_symlinks_are_available(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    source = tmp_path / "source.bin"
    source.unlink()
    try:
        source.symlink_to(tmp_path / "elsewhere.bin")
    except OSError:
        pytest.skip("Windows symlink privilege is unavailable")
    with pytest.raises(ValueError, match="link"):
        _run(tmp_path, digest)


def test_attestation_replay_detects_source_or_receipt_rewrite(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    attested = _run(tmp_path, digest)
    receipt_path = tmp_path / "attestations" / f"{digest}.json"
    original = receipt_path.read_bytes()
    receipt_path.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="pin|schema"):
        transaction.verify_synthetic_attestation(
            tmp_path, expected_contract_sha256=digest,
            expected_attestation_sha256=attested.attestation_sha256,
        )
    receipt_path.write_bytes(original)
    (tmp_path / "source.bin").write_bytes(b"changed\n")
    with pytest.raises(ValueError, match="source changed"):
        transaction.verify_synthetic_attestation(
            tmp_path, expected_contract_sha256=digest,
            expected_attestation_sha256=attested.attestation_sha256,
        )


def test_channel_child_frame_is_parent_published_and_externally_replayed(
    tmp_path: Path,
) -> None:
    digest = _prepare(tmp_path)
    attested = transaction.run_synthetic_transaction_channel(
        tmp_path, expected_contract_sha256=digest, cwd=_PROJECT_ROOT, sensor=_ample,
    )
    proposal_path = tmp_path / "proposals" / f"{digest}.json"
    receipt_path = tmp_path / "attestations" / f"{digest}.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["schema"] == "synthetic_case_attestation_channel_v1"
    assert receipt["payload"]["frame_sha256"] == hashlib.sha256(
        proposal_path.read_bytes()
    ).hexdigest()
    assert transaction.verify_synthetic_attestation_channel(
        tmp_path, expected_contract_sha256=digest,
        expected_attestation_sha256=attested.attestation_sha256,
    ) == attested
    with pytest.raises(ValueError, match="external pin"):
        transaction.verify_synthetic_attestation_channel(
            tmp_path, expected_contract_sha256=digest,
            expected_attestation_sha256="b" * 64,
        )
    assert not (tmp_path / "cells").exists()


def test_shared_exact_proposal_without_child_frame_cannot_be_attested(
    tmp_path: Path,
) -> None:
    digest = _prepare(tmp_path)
    child = (
        "from pathlib import Path; import sys; "
        "from evaluation.phase2_case_transaction import write_synthetic_proposal; "
        "write_synthetic_proposal(Path(sys.argv[1]), sys.argv[2])"
    )
    with pytest.raises(supervision.SupervisionError, match="frame|result"):
        transaction.run_synthetic_transaction_channel(
            tmp_path, expected_contract_sha256=digest, cwd=_PROJECT_ROOT,
            command=[sys.executable, "-B", "-c", child, str(tmp_path), digest,
                     "{result_handle}"],
            sensor=_ample,
        )
    assert (tmp_path / "proposals" / f"{digest}.json").is_file()
    assert not (tmp_path / "attestations" / f"{digest}.json").exists()


def test_channel_rejects_competing_same_byte_file_before_parent_publication(
    tmp_path: Path,
) -> None:
    digest = _prepare(tmp_path)
    original = supervision.run_supervised_with_frame

    def racing_writer(*args: object, **kwargs: object) -> supervision.FramedSupervisionResult:
        outcome = original(*args, **kwargs)  # type: ignore[arg-type]
        contract = transaction._contract(tmp_path, digest)
        transaction._publish(
            tmp_path, f"proposals/{digest}.json", transaction._expected_proposal(contract),
        )
        return outcome

    with (
        patch.object(transaction, "run_supervised_with_frame", racing_writer),
        pytest.raises(ValueError, match="before parent publication"),
    ):
        transaction.run_synthetic_transaction_channel(
            tmp_path, expected_contract_sha256=digest, cwd=_PROJECT_ROOT, sensor=_ample,
        )
    assert not (tmp_path / "attestations" / f"{digest}.json").exists()


def test_channel_attestation_rejects_later_proposal_rewrite(tmp_path: Path) -> None:
    digest = _prepare(tmp_path)
    attested = transaction.run_synthetic_transaction_channel(
        tmp_path, expected_contract_sha256=digest, cwd=_PROJECT_ROOT, sensor=_ample,
    )
    proposal_path = tmp_path / "proposals" / f"{digest}.json"
    proposal_path.write_bytes(proposal_path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="external pin|schema|changed"):
        transaction.verify_synthetic_attestation_channel(
            tmp_path, expected_contract_sha256=digest,
            expected_attestation_sha256=attested.attestation_sha256,
        )
