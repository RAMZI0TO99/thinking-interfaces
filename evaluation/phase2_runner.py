"""Phase II run recording: pilot case manifests, atomic claims and immutable cells.

This module never executes a method, touches target signals or computes scores.
It binds audited case identities, refuses incomplete method configurations,
records attempts and failures, and publishes evaluation cells or distinct
engineering-only terminal receipts atomically under an admitted output root.
A published cell must cite its selection evidence
and carry exact-rational metrics consistent with its confusion matrix; the
scientific freeze, compute admission and gate sign-off remain separate work.
"""

from __future__ import annotations

import errno
import json
import math
import os
import platform
import sys
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from fractions import Fraction
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np
import torch

from core.config import canonical_config_json, config_digest
from core.provenance import capture_source
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import CellIdentity, envelope, verify_envelope, write_once

REQUIRED_METHOD_FIELDS = ("optimizer", "steps", "fit_scope", "preprocessing")
CHO_METHOD_FIELDS = (
    "method", "dataset", "input_profile", "variant_config_sha256", "candidates",
    "source_seed_policy", "source_policy", "score", "tie_break", "early_stopping",
)
CHO_FIRST_TRANCHE = frozenset({"labram_linear", "labram_lora", "labram_full", "eegnet"})
MAXIMUM_ATTEMPTS = 2  # One initial attempt plus the single permitted retry.
_LOCK_OWNERS = threading.local()


def _package(name: str) -> str:
    try:
        return str(version(name))
    except PackageNotFoundError:
        return "absent"


def environment_digest() -> str:
    """Deterministic local execution-environment descriptor digest."""
    return config_digest(
        {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "braindecode": _package("braindecode"),
            "scikit-learn": _package("scikit-learn"),
            "safetensors": _package("safetensors"),
            "device": "cpu",
            "torch_threads": torch.get_num_threads(),
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        }
    )


def method_configuration(mapping: Mapping[str, Any]) -> str:
    """Digest an explicit method configuration; missing declared fields refuse.

    The selected Cho tranche uses a static two-candidate roster. Other pilot
    methods retain their explicit optimizer/steps/scope/preprocessing fields.
    Existing smoke settings are never implicit defaults.
    """
    raw = dict(mapping)
    if raw.get("dataset") == "cho2017" and raw.get("method") in CHO_FIRST_TRANCHE:
        if set(raw) != set(CHO_METHOD_FIELDS):
            raise ValueError("Cho method configuration fields differ from static schema")
        method = raw["method"]
        profile = "cho_profile_a" if method == "eegnet" else "cho_profile_b_60hz_v1"
        if raw["input_profile"] != profile:
            raise ValueError("Cho method input profile differs")
        variant = raw["variant_config_sha256"]
        if method == "eegnet":
            if variant is not None:
                raise ValueError("EEGNet cannot claim a Cho Profile B variant")
        else:
            require_digest(variant, "Cho Profile B variant config")
        if (
            raw["source_policy"] != "all_non_target_subjects; inner_validation_also_excluded"
            or raw["score"] != "mean_subject_balanced_accuracy_exact_rational"
            or raw["tie_break"] != "first_in_declared_candidate_order"
            or raw["early_stopping"] is not False
            or raw["source_seed_policy"]
            != ("case_model_seed" if method == "labram_lora" else "none")
        ):
            raise ValueError("Cho static selection policy differs")
        candidates = raw["candidates"]
        if not isinstance(candidates, (list, tuple)) or len(candidates) != 2:
            raise ValueError("Cho method requires two ordered candidates")
        names = []
        for candidate in candidates:
            if not isinstance(candidate, Mapping) or set(candidate) != {
                "name", "source", "support"
            }:
                raise ValueError("Cho candidate fields differ")
            name, source, support = (
                candidate["name"], candidate["source"], candidate["support"]
            )
            if (
                not isinstance(name, str) or not name.strip()
                or not isinstance(source, Mapping) or not isinstance(support, Mapping)
            ):
                raise ValueError("Cho candidate name or settings are missing")
            names.append(name)
            if method == "labram_lora":
                if source.get("seed") != "$case_model_seed":
                    raise ValueError("LoRA source seed must use the static case template")
            elif "seed" in source:
                raise ValueError("unexpected candidate-level source seed")
            for count in (source.get("steps_per_subject"), support.get("steps")):
                if type(count) is not int or count < 1:
                    raise ValueError("Cho candidate step counts must be positive integers")
            for rate in (source.get("learning_rate"), support.get("learning_rate")):
                if (
                    not isinstance(rate, (int, float)) or isinstance(rate, bool)
                    or not math.isfinite(rate) or rate <= 0
                ):
                    raise ValueError("Cho candidate learning rates must be finite and positive")
        if len(set(names)) != 2:
            raise ValueError("Cho candidate names must be distinct")
        return config_digest(raw)
    missing = [name for name in REQUIRED_METHOD_FIELDS if name not in raw]
    if missing or any(raw[name] is None for name in REQUIRED_METHOD_FIELDS):
        raise ValueError(f"method configuration must declare {REQUIRED_METHOD_FIELDS}")
    return config_digest(raw)


@dataclass(frozen=True, slots=True)
class CasePlan:
    """One planned pilot target case; repetitions share identity, not attempts."""

    dataset: str
    target_subject: str
    method: str
    shots_per_class: int
    model_seed: int
    repetition: int

    def __post_init__(self) -> None:
        for name in ("dataset", "target_subject", "method"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if type(self.shots_per_class) is not int or self.shots_per_class < 1:
            raise ValueError("shots_per_class must be a positive integer")
        if type(self.model_seed) is not int or self.model_seed < 0:
            raise ValueError("model_seed must be a nonnegative integer")
        if type(self.repetition) is not int or self.repetition < 1:
            raise ValueError("repetition must be a positive integer")

    @property
    def case_id(self) -> str:
        return config_digest(asdict(self))

    @property
    def identity_key(self) -> tuple[str, str, str, int, int]:
        """Cell-index key; repetitions and attempts intentionally excluded."""
        return (
            self.dataset,
            self.target_subject,
            self.method,
            self.shots_per_class,
            self.model_seed,
        )


def pilot_case_plans(
    *,
    methods: Sequence[str],
    datasets: Sequence[str],
    targets: Mapping[str, str],
    shots: Sequence[int],
    model_seed: int,
    repetitions: int,
) -> tuple[CasePlan, ...]:
    """Deterministic pilot matrix in dataset, method, shots, repetition order."""
    if not methods or not datasets or not shots:
        raise ValueError("explicit method, dataset and shot rosters required")
    if len(set(methods)) != len(methods) or len(set(datasets)) != len(datasets):
        raise ValueError("duplicate roster entries are not allowed")
    if any(type(s) is not int or s < 1 for s in shots) or len(set(shots)) != len(shots):
        raise ValueError("distinct positive integer shot levels required")
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError("at least one repetition is required")
    if set(datasets) - set(targets):
        raise ValueError("every dataset needs an explicit development target")
    if type(model_seed) is not int or model_seed < 0:
        raise ValueError("model_seed must be a nonnegative integer")
    return tuple(
        CasePlan(dataset, targets[dataset], method, level, model_seed, repetition)
        for dataset in sorted(datasets)
        for method in methods
        for level in sorted(shots)
        for repetition in range(1, repetitions + 1)
    )


def _finite_floats(value: Any) -> bool:
    return isinstance(value, list) and all(
        type(entry) in (int, float) and np.isfinite(entry) for entry in value
    )


def _confusion_rows(value: Any) -> list[list[int]] | None:
    if not isinstance(value, list) or len(value) < 2:
        return None
    rows: list[list[int]] = []
    for row in value:
        if not isinstance(row, list) or len(row) != len(value):
            return None
        entries: list[int] = []
        for entry in row:
            if type(entry) is not int or entry < 0:
                return None
            entries.append(entry)
        if sum(entries) < 1:
            return None
        rows.append(entries)
    return rows


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


class CaseRecorder:
    """Atomic claim/attempt/cell or engineering lifecycle over an output root.

    Claims and failures are deterministic engineering envelopes: replaying a
    claim with different bytes is a conflict, never a silent replacement. A
    case admits at most one initial attempt and one linked retry, and every
    published cell cites its selection evidence with exact-rational metrics.
    """

    def __init__(self, root: Path, *, output_root: Path | None = None) -> None:
        self._root = root.resolve()
        base = self._root / "runs" / "phase2"
        self._output = (output_root or base / "recorder").resolve()
        if self._output == base or not self._output.is_relative_to(base):
            raise ValueError("recorder output root must stay inside runs/phase2")
        self._claims = self._output / "claims"
        self._attempts = self._output / "attempts"
        self._cells = self._output / "cells"
        self._successes = self._output / "successes"
        self._intents = self._output / "publication_intents"
        self._engineering_intents = self._output / "engineering_intents"
        self._engineering_successes = self._output / "engineering_successes"
        self._locks = self._output / "case_locks"

    @property
    def output_root(self) -> Path:
        return self._output

    def _write(self, directory: Path, name: str, record: Mapping[str, Any]) -> Path:
        return write_once(directory / name, record, output_root=self._output)

    @contextmanager
    def case_session(self, plan: CasePlan) -> Iterator[LockedCase]:
        """Hold one identity lock across claim, external work, and terminal record.

        Use the yielded facade's methods while the context is open. Calling the
        recorder's short-lock methods inside the same thread would reacquire the
        Windows byte lock and is explicitly rejected.
        """
        if not isinstance(plan, CasePlan):
            raise ValueError("explicit case plan required")
        with self._identity_lock(plan.identity_key):
            session = LockedCase(self, plan, threading.get_ident())
            try:
                yield session
            finally:
                session._closed = True

    @contextmanager
    def _identity_lock(self, key: tuple[str, str, str, int, int]) -> Iterator[None]:
        """Hold a crash-releasing lock across one shared cell identity's lifecycle."""
        self._locks.mkdir(parents=True, exist_ok=True)
        if self._locks.is_symlink() or self._locks.resolve() != self._locks:
            raise ValueError("case lock directory aliases another path")
        path = self._locks / f"{config_digest({'cell_identity_key': key})}.lock"
        held: set[str] = getattr(_LOCK_OWNERS, "paths", set())
        if str(path) in held:
            raise RuntimeError("case identity lock is already held; use the locked case session")
        if path.is_symlink() or (path.exists() and (
            not path.is_file() or path.stat().st_nlink != 1
        )):
            raise ValueError("case lock path aliases another file")
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "r+b") as handle:
            opened = os.fstat(handle.fileno())
            if (
                path.is_symlink() or not path.is_file()
                or not os.path.samestat(opened, path.stat())
                or opened.st_nlink != 1 or opened.st_size not in (0, 1)
            ):
                raise ValueError("case lock identity changed")
            if opened.st_size == 0:
                handle.write(b"0")
                handle.flush()
                os.fsync(handle.fileno())
            deadline = time.monotonic() + 120.0
            while True:
                try:
                    handle.seek(0)
                    if sys.platform == "win32":
                        import msvcrt

                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as error:
                    if error.errno not in {errno.EACCES, errno.EAGAIN}:
                        raise
                    if time.monotonic() >= deadline:
                        raise TimeoutError("case identity publication lock is busy") from error
                    time.sleep(0.05)
            try:
                if (
                    path.is_symlink()
                    or not os.path.samestat(os.fstat(handle.fileno()), path.stat())
                ):
                    raise ValueError("case lock identity changed during acquisition")
                handle.seek(0)
                if handle.read(1) != b"0":
                    raise ValueError("case lock bytes differ")
                held.add(str(path))
                _LOCK_OWNERS.paths = held
                yield
            finally:
                held.discard(str(path))
                handle.seek(0)
                if sys.platform == "win32":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def claim(self, plan: CasePlan, *, worker: str, attempt: int = 1) -> Path:
        if not isinstance(plan, CasePlan):
            raise ValueError("explicit case plan required")
        with self._identity_lock(plan.identity_key):
            return self._claim_locked(plan, worker=worker, attempt=attempt)

    def _claim_locked(
        self, plan: CasePlan, *, worker: str, attempt: int, require_new: bool = False,
    ) -> Path:
        if not isinstance(worker, str) or not worker.strip():
            raise ValueError("explicit worker identity required")
        if type(attempt) is not int or not 1 <= attempt <= MAXIMUM_ATTEMPTS:
            raise ValueError("at most one initial attempt and one retry are admitted")
        if (self._successes / f"{plan.case_id}.success.json").exists():
            raise ValueError("a completed case cannot be claimed again")
        if _present(self._engineering_successes / f"{plan.case_id}.success.json"):
            raise ValueError("an engineering-completed case cannot be claimed again")
        if (self._intents / f"{plan.case_id}.intent.json").exists():
            raise ValueError("a case publication intent must be recovered before a new claim")
        if _present(self._engineering_intents / f"{plan.case_id}.intent.json"):
            raise ValueError("an engineering success intent must be recovered before a new claim")
        claim_path = self._claims / f"{plan.case_id}.attempt{attempt}.claim.json"
        if require_new and _present(claim_path):
            raise ValueError("attempt already claimed; recover before relaunch")
        claims = self._claimed_attempts(plan)
        failures = self._failed_attempts(plan, claims)
        if attempt in failures:
            raise ValueError("a failed attempt cannot be claimed again")
        if attempt > 1 and attempt - 1 not in failures:
            raise ValueError(
                "a retry must be linked to a recorded failure of the prior attempt"
            )
        record = envelope(
            "engineering_smoke",
            {
                "purpose": "pilot_case_claim",
                "case": asdict(plan),
                "worker": worker,
                "attempt": attempt,
                "environment_sha256": environment_digest(),
                "source": asdict(capture_source(self._root)),
                "engineering_only": True,
            },
        )
        return self._write(self._claims, f"{plan.case_id}.attempt{attempt}.claim.json", record)

    def record_failure(self, plan: CasePlan, *, attempt: int, reason: Mapping[str, Any]) -> Path:
        if not isinstance(plan, CasePlan):
            raise ValueError("explicit case plan required")
        with self._identity_lock(plan.identity_key):
            return self._record_failure_locked(plan, attempt=attempt, reason=reason)

    def _record_failure_locked(
        self, plan: CasePlan, *, attempt: int, reason: Mapping[str, Any],
    ) -> Path:
        if type(attempt) is not int or not 1 <= attempt <= MAXIMUM_ATTEMPTS:
            raise ValueError("attempt out of the admitted range")
        error = reason.get("error")
        if not isinstance(error, str) or not error.strip():
            raise ValueError("an explicit error description is required")
        if attempt not in self._claimed_attempts(plan):
            raise ValueError("a failure requires a recorded claim for its attempt")
        if (self._successes / f"{plan.case_id}.success.json").exists():
            raise ValueError("a measured case cannot also record a failure")
        if _present(self._engineering_successes / f"{plan.case_id}.success.json"):
            raise ValueError("an engineering-completed case cannot also record a failure")
        measured = self.measured_identities().get(plan.identity_key)
        if measured is not None and not self._cell_has_other_success(plan, measured):
            raise ValueError("a published cell cannot also record a failure")
        if (self._intents / f"{plan.case_id}.intent.json").exists():
            raise ValueError("a case with a publication intent cannot record a failure")
        if _present(self._engineering_intents / f"{plan.case_id}.intent.json"):
            raise ValueError("a case with an engineering success intent cannot record a failure")
        record = envelope(
            "engineering_smoke",
            {
                "purpose": "pilot_case_failure",
                "case": asdict(plan),
                "attempt": attempt,
                "reason": dict(reason),
                "environment_sha256": environment_digest(),
                "engineering_only": True,
            },
        )
        return self._write(self._attempts, f"{plan.case_id}.attempt{attempt}.failure.json", record)

    def _cell_has_other_success(self, plan: CasePlan, cell_sha256: str) -> bool:
        """Allow a later repetition to fail if an earlier success owns the cell."""
        if not self._successes.is_dir():
            return False
        found = False
        for path in self._successes.glob("*.success.json"):
            if path.is_symlink() or not path.is_file():
                raise ValueError("case success path aliases or is absent")
            raw = path.read_bytes()
            receipt = json.loads(raw)
            if raw != (canonical_config_json(receipt) + "\n").encode("utf-8"):
                raise ValueError(f"case success no longer verifies: {path.name}")
            payload = receipt.get("payload")
            if not isinstance(payload, dict) or not isinstance(payload.get("case"), dict):
                raise ValueError(f"case success no longer verifies: {path.name}")
            other = CasePlan(**payload["case"])
            if other.identity_key != plan.identity_key:
                continue
            other_claims = self._claimed_attempts(other)
            other_failures = self._failed_attempts(other, other_claims)
            other_attempt = payload.get("attempt")
            if (
                path.name != f"{other.case_id}.success.json"
                or type(other_attempt) is not int
                or not other_claims or other_attempt != other_claims[-1]
                or other_attempt in other_failures
                or not verify_envelope(receipt, kind="engineering_smoke", expected_payload={
                    "purpose": "pilot_case_success",
                    "case": asdict(other),
                    "attempt": other_attempt,
                    "cell_sha256": cell_sha256,
                })
            ):
                raise ValueError(f"case success no longer verifies: {path.name}")
            if other.case_id != plan.case_id:
                found = True
        return found

    def _claimed_attempts(self, plan: CasePlan) -> list[int]:
        """Read and verify the immutable claims for one case."""
        attempts = []
        for attempt in range(1, MAXIMUM_ATTEMPTS + 1):
            path = self._claims / f"{plan.case_id}.attempt{attempt}.claim.json"
            if not path.is_file():
                continue
            record = json.loads(path.read_text("utf-8"))
            payload = record.get("payload")
            if (
                not isinstance(payload, dict)
                or payload.get("purpose") != "pilot_case_claim"
                or payload.get("case") != asdict(plan)
                or payload.get("attempt") != attempt
                or not verify_envelope(
                    record, kind="engineering_smoke", expected_payload=payload
                )
            ):
                raise ValueError(f"case claim no longer verifies: {path.name}")
            attempts.append(attempt)
        return attempts

    def _failed_attempts(self, plan: CasePlan, claims: Sequence[int]) -> list[int]:
        """Verify each failure and its matching claim before using it as evidence."""
        failures = []
        for attempt in range(1, MAXIMUM_ATTEMPTS + 1):
            path = self._attempts / f"{plan.case_id}.attempt{attempt}.failure.json"
            if not path.is_file():
                continue
            record = json.loads(path.read_text("utf-8"))
            payload = record.get("payload")
            if (
                attempt not in claims
                or not isinstance(payload, dict)
                or set(payload) != {
                    "purpose", "case", "attempt", "reason",
                    "environment_sha256", "engineering_only",
                }
                or payload.get("purpose") != "pilot_case_failure"
                or payload.get("case") != asdict(plan)
                or payload.get("attempt") != attempt
                or payload.get("engineering_only") is not True
                or not isinstance(payload.get("reason"), dict)
                or not isinstance(payload["reason"].get("error"), str)
                or not payload["reason"]["error"].strip()
                or not verify_envelope(
                    record, kind="engineering_smoke", expected_payload=payload
                )
            ):
                raise ValueError(f"case failure no longer verifies: {path.name}")
            require_digest(payload["environment_sha256"], "failure environment")
            failures.append(attempt)
        return failures

    def record_cell(
        self,
        identity: CellIdentity,
        *,
        metrics: Mapping[str, Any],
        plan: CasePlan | None = None,
    ) -> Path:
        """Publish a cell, then optionally receipt one measured case repetition."""
        if plan is not None:
            if not isinstance(plan, CasePlan):
                raise ValueError("explicit case plan required")
            with self._identity_lock(plan.identity_key):
                return self._record_cell_locked(identity, metrics=metrics, plan=plan)
        key = (
            identity.dataset, identity.target_subject, identity.method,
            identity.shots_per_class, identity.model_seed,
        )
        with self._identity_lock(key):
            return self._record_cell_locked(identity, metrics=metrics, plan=None)

    def _record_cell_locked(
        self,
        identity: CellIdentity,
        *,
        metrics: Mapping[str, Any],
        plan: CasePlan | None,
    ) -> Path:
        key = (
            identity.dataset, identity.target_subject, identity.method,
            identity.shots_per_class, identity.model_seed,
        )
        attempt = None
        if plan is not None:
            if not isinstance(plan, CasePlan) or plan.identity_key != key:
                raise ValueError("case plan must match the published cell identity")
            if (
                _present(self._engineering_intents / f"{plan.case_id}.intent.json")
                or _present(self._engineering_successes / f"{plan.case_id}.success.json")
            ):
                raise ValueError("an engineering terminal case cannot publish a scientific cell")
            claims = self._claimed_attempts(plan)
            if not claims:
                raise ValueError("a measured case requires a recorded claim")
            failures = self._failed_attempts(plan, claims)
            attempt = claims[-1]
            if attempt in failures:
                raise ValueError("a failed attempt cannot be recorded as measured")
        elif self._engineering_identity_in_use(key):
            raise ValueError(
                "a direct scientific cell conflicts with an engineering intent or success"
            )
        snapshot = self._validated_metrics(metrics)
        record = envelope(
            "evaluation_cell",
            {"identity": asdict(identity), "metrics": snapshot},
        )
        previous = self.measured_identities().get(key)
        if previous is not None and previous != record["sha256"]:
            raise FileExistsError("a different cell already measures this case identity")
        if plan is not None:
            assert attempt is not None
            intent = envelope("engineering_smoke", {
                "purpose": "pilot_case_publication_intent",
                "case": asdict(plan),
                "attempt": attempt,
                "identity": asdict(identity),
                "cell": record,
            })
            self._write(self._intents, f"{plan.case_id}.intent.json", intent)
            return self._replay_intent_locked(
                plan, identity=identity, expected_cell_sha256=record["sha256"],
            )
        cell = self._write(self._cells, f"{identity.sha256}.json", record)
        return cell

    def recover_cell_from_intent(
        self, plan: CasePlan, *, expected_cell_sha256: str,
    ) -> Path:
        """Replay a cell pinned outside the writable intent, such as an attestation."""
        if not isinstance(plan, CasePlan):
            raise ValueError("explicit case plan required")
        require_digest(expected_cell_sha256, "expected attested cell")
        with self._identity_lock(plan.identity_key):
            return self._replay_intent_locked(
                plan, expected_cell_sha256=expected_cell_sha256,
            )

    def _replay_intent_locked(
        self, plan: CasePlan, *, expected_cell_sha256: str,
        identity: CellIdentity | None = None,
    ) -> Path:
        if (
            _present(self._engineering_intents / f"{plan.case_id}.intent.json")
            or _present(self._engineering_successes / f"{plan.case_id}.success.json")
        ):
            raise ValueError("an engineering terminal case cannot publish a scientific cell")
        attempt, actual_identity, cell = self._verified_intent(
            plan, expected_cell_sha256=expected_cell_sha256, identity=identity,
        )
        previous = self.measured_identities().get(plan.identity_key)
        if previous is not None and previous != cell["sha256"]:
            raise FileExistsError("a different cell already measures this case identity")
        success_path = self._successes / f"{plan.case_id}.success.json"
        success = envelope("engineering_smoke", {
            "purpose": "pilot_case_success",
            "case": asdict(plan),
            "attempt": attempt,
            "cell_sha256": cell["sha256"],
        })
        if success_path.is_file():
            existing = json.loads(success_path.read_text("utf-8"))
            if not verify_envelope(
                existing, kind="engineering_smoke", expected_payload=success["payload"],
            ):
                raise ValueError(f"case success no longer verifies: {plan.case_id}")
        cell_path = self._write(self._cells, f"{actual_identity.sha256}.json", cell)
        self._write(self._successes, f"{plan.case_id}.success.json", success)
        return cell_path

    def _verified_intent(
        self, plan: CasePlan, *, expected_cell_sha256: str,
        identity: CellIdentity | None = None,
    ) -> tuple[int, CellIdentity, dict[str, Any]]:
        if (
            not self._intents.is_dir() or self._intents.is_symlink()
            or self._intents.resolve() != self._intents
        ):
            raise ValueError("case publication intent directory aliases or is absent")
        path = self._intents / f"{plan.case_id}.intent.json"
        if (
            path.is_symlink() or path.resolve() != path or not path.is_file()
            or path.stat().st_nlink != 1
        ):
            raise ValueError("case publication intent is absent or aliases another path")
        raw = path.read_bytes()
        intent = json.loads(raw)
        if not isinstance(intent, dict):
            raise ValueError("case publication intent no longer verifies")
        payload = intent.get("payload")
        if (
            not isinstance(payload, dict)
            or set(payload) != {"purpose", "case", "attempt", "identity", "cell"}
            or payload.get("purpose") != "pilot_case_publication_intent"
            or payload.get("case") != asdict(plan)
            or not verify_envelope(
                intent, kind="engineering_smoke", expected_payload=payload,
            )
            or raw != (canonical_config_json(intent) + "\n").encode("utf-8")
        ):
            raise ValueError("case publication intent no longer verifies")
        attempt = payload["attempt"]
        claims = self._claimed_attempts(plan)
        failures = self._failed_attempts(plan, claims)
        if (
            type(attempt) is not int or not claims or attempt != claims[-1]
            or attempt in failures
        ):
            raise ValueError("case publication intent has no active claimed attempt")
        declared_identity = payload["identity"]
        if not isinstance(declared_identity, dict):
            raise ValueError("case publication intent identity differs")
        actual_identity = CellIdentity(**declared_identity)
        if (
            plan.identity_key != (
                actual_identity.dataset, actual_identity.target_subject,
                actual_identity.method, actual_identity.shots_per_class,
                actual_identity.model_seed,
            )
            or (identity is not None and identity != actual_identity)
        ):
            raise ValueError("case publication intent identity differs")
        cell = payload["cell"]
        if not isinstance(cell, dict) or not isinstance(cell.get("payload"), dict):
            raise ValueError("case publication intent cell differs")
        cell_payload = cell["payload"]
        if (
            set(cell_payload) != {"identity", "metrics"}
            or cell_payload.get("identity") != declared_identity
            or not isinstance(cell_payload.get("metrics"), dict)
            or cell.get("sha256") != expected_cell_sha256
            or not verify_envelope(
                cell, kind="evaluation_cell", expected_payload=cell_payload,
            )
        ):
            raise ValueError("case publication intent cell no longer verifies")
        self._validated_metrics(cell_payload["metrics"])
        return attempt, actual_identity, cell

    def record_engineering_success(
        self, plan: CasePlan, *, attempt: int, attested_evidence_sha256: str,
    ) -> Path:
        """Write a non-scientific terminal intent, then its engineering receipt.

        The caller must independently verify and pin the evidence digest. No
        evaluation cell, scientific success, or metric is written by this API.
        """
        if not isinstance(plan, CasePlan):
            raise ValueError("explicit case plan required")
        with self._identity_lock(plan.identity_key):
            return self._record_engineering_success_locked(
                plan, attempt=attempt,
                attested_evidence_sha256=attested_evidence_sha256,
            )

    def _record_engineering_success_locked(
        self, plan: CasePlan, *, attempt: int, attested_evidence_sha256: str,
    ) -> Path:
        require_digest(attested_evidence_sha256, "attested engineering evidence")
        if type(attempt) is not int or not 1 <= attempt <= MAXIMUM_ATTEMPTS:
            raise ValueError("engineering success attempt is out of range")
        claims = self._claimed_attempts(plan)
        failures = self._failed_attempts(plan, claims)
        if not claims or attempt != claims[-1] or attempt in failures:
            raise ValueError("engineering success requires the active, nonfailed claim")
        self._assert_no_scientific_terminal(plan)
        intent = envelope("engineering_smoke", {
            "purpose": "pilot_case_engineering_success_intent",
            "case": asdict(plan),
            "attempt": attempt,
            "attested_evidence_sha256": attested_evidence_sha256,
            "engineering_only": True,
        })
        self._write(self._engineering_intents, f"{plan.case_id}.intent.json", intent)
        return self._replay_engineering_success_locked(
            plan, expected_attested_evidence_sha256=attested_evidence_sha256,
        )

    def recover_engineering_success(
        self, plan: CasePlan, *, expected_attested_evidence_sha256: str,
    ) -> Path:
        """Recover only the engineering receipt from an externally pinned digest."""
        if not isinstance(plan, CasePlan):
            raise ValueError("explicit case plan required")
        require_digest(expected_attested_evidence_sha256, "expected attested evidence")
        with self._identity_lock(plan.identity_key):
            return self._replay_engineering_success_locked(
                plan, expected_attested_evidence_sha256=expected_attested_evidence_sha256,
            )

    def _replay_engineering_success_locked(
        self, plan: CasePlan, *, expected_attested_evidence_sha256: str,
    ) -> Path:
        attempt = self._verified_engineering_intent(
            plan, expected_attested_evidence_sha256=expected_attested_evidence_sha256,
        )
        success = envelope("engineering_smoke", {
            "purpose": "pilot_case_engineering_success",
            "case": asdict(plan),
            "attempt": attempt,
            "attested_evidence_sha256": expected_attested_evidence_sha256,
            "engineering_only": True,
        })
        path = self._write(
            self._engineering_successes, f"{plan.case_id}.success.json", success,
        )
        self._verified_engineering_success(
            plan, expected_attested_evidence_sha256=expected_attested_evidence_sha256,
        )
        return path

    def _assert_no_scientific_terminal(self, plan: CasePlan) -> None:
        if (
            _present(self._successes / f"{plan.case_id}.success.json")
            or _present(self._intents / f"{plan.case_id}.intent.json")
        ):
            raise ValueError("scientific publication conflicts with engineering success")
        measured = self.measured_identities().get(plan.identity_key)
        if measured is not None and not self._cell_has_other_success(plan, measured):
            raise ValueError("unreceipted scientific cell conflicts with engineering success")

    def _engineering_identity_in_use(
        self, key: tuple[str, str, str, int, int],
    ) -> bool:
        """Verify engineering records before a no-plan scientific cell is written."""
        for directory, suffix in (
            (self._engineering_intents, ".intent.json"),
            (self._engineering_successes, ".success.json"),
        ):
            if not _present(directory):
                continue
            if not directory.is_dir() or directory.is_symlink() or directory.resolve() != directory:
                raise ValueError("engineering terminal directory aliases another path")
            for path in directory.glob("*.json"):
                if (
                    path.is_symlink() or not path.is_file() or path.resolve() != path
                    or path.stat().st_nlink != 1
                ):
                    raise ValueError("engineering terminal path aliases another file")
                record = json.loads(path.read_bytes())
                if not isinstance(record, dict):
                    raise ValueError("engineering terminal record no longer verifies")
                payload = record.get("payload")
                if not isinstance(payload, dict) or not isinstance(payload.get("case"), dict):
                    raise ValueError("engineering terminal record no longer verifies")
                try:
                    plan = CasePlan(**payload["case"])
                except (TypeError, ValueError) as error:
                    raise ValueError("engineering terminal case no longer verifies") from error
                if path.name != f"{plan.case_id}{suffix}":
                    raise ValueError("engineering terminal filename differs from case")
                evidence = payload.get("attested_evidence_sha256")
                if not isinstance(evidence, str):
                    raise ValueError("engineering terminal evidence is missing")
                if suffix == ".intent.json":
                    self._verified_engineering_intent(
                        plan, expected_attested_evidence_sha256=evidence,
                    )
                else:
                    self._verified_engineering_success(
                        plan, expected_attested_evidence_sha256=evidence,
                    )
                if plan.identity_key == key:
                    return True
        return False

    def _verified_engineering_intent(
        self, plan: CasePlan, *, expected_attested_evidence_sha256: str,
    ) -> int:
        require_digest(expected_attested_evidence_sha256, "expected attested evidence")
        path = self._engineering_intents / f"{plan.case_id}.intent.json"
        if (
            not self._engineering_intents.is_dir()
            or self._engineering_intents.is_symlink()
            or self._engineering_intents.resolve() != self._engineering_intents
            or path.is_symlink() or path.resolve() != path or not path.is_file()
            or path.stat().st_nlink != 1
        ):
            raise ValueError("engineering success intent is absent or aliases another path")
        raw = path.read_bytes()
        intent = json.loads(raw)
        if not isinstance(intent, dict):
            raise ValueError("engineering success intent no longer verifies")
        payload = intent.get("payload")
        if (
            not isinstance(payload, dict)
            or set(payload) != {
                "purpose", "case", "attempt", "attested_evidence_sha256", "engineering_only",
            }
            or payload.get("purpose") != "pilot_case_engineering_success_intent"
            or payload.get("case") != asdict(plan)
            or payload.get("attested_evidence_sha256") != expected_attested_evidence_sha256
            or payload.get("engineering_only") is not True
            or not verify_envelope(
                intent, kind="engineering_smoke", expected_payload=payload,
            )
            or raw != (canonical_config_json(intent) + "\n").encode("utf-8")
        ):
            raise ValueError("engineering success intent no longer verifies")
        attempt = payload["attempt"]
        claims = self._claimed_attempts(plan)
        failures = self._failed_attempts(plan, claims)
        if (
            type(attempt) is not int or not claims or attempt != claims[-1]
            or attempt in failures
        ):
            raise ValueError("engineering success intent has no active claimed attempt")
        self._assert_no_scientific_terminal(plan)
        return attempt

    def _verified_engineering_success(
        self, plan: CasePlan, *, expected_attested_evidence_sha256: str,
    ) -> int:
        attempt = self._verified_engineering_intent(
            plan, expected_attested_evidence_sha256=expected_attested_evidence_sha256,
        )
        path = self._engineering_successes / f"{plan.case_id}.success.json"
        if (
            not self._engineering_successes.is_dir()
            or self._engineering_successes.is_symlink()
            or self._engineering_successes.resolve() != self._engineering_successes
            or path.is_symlink() or path.resolve() != path or not path.is_file()
            or path.stat().st_nlink != 1
        ):
            raise ValueError("engineering success receipt is absent or aliases another path")
        raw = path.read_bytes()
        receipt = json.loads(raw)
        if not isinstance(receipt, dict):
            raise ValueError("engineering success receipt no longer verifies")
        payload = receipt.get("payload")
        if (
            not isinstance(payload, dict)
            or set(payload) != {
                "purpose", "case", "attempt", "attested_evidence_sha256", "engineering_only",
            }
            or payload.get("purpose") != "pilot_case_engineering_success"
            or payload.get("case") != asdict(plan)
            or payload.get("attempt") != attempt
            or payload.get("attested_evidence_sha256") != expected_attested_evidence_sha256
            or payload.get("engineering_only") is not True
            or not verify_envelope(
                receipt, kind="engineering_smoke", expected_payload=payload,
            )
            or raw != (canonical_config_json(receipt) + "\n").encode("utf-8")
        ):
            raise ValueError("engineering success receipt no longer verifies")
        return attempt

    def _validated_metrics(self, metrics: Mapping[str, Any]) -> dict[str, Any]:
        raw = dict(metrics)
        if raw.get("role") != "outer_target":
            raise ValueError("published cells measure outer-target cases only")
        selection = raw.get("selection_evidence_sha256")
        if not isinstance(selection, str):
            raise ValueError("selection_evidence_sha256 must be a hex digest string")
        require_digest(selection, "selection_evidence_sha256")
        rows = _confusion_rows(raw.get("confusion_matrix"))
        if rows is None:
            raise ValueError(
                "a square nonnegative integer confusion matrix with measured rows is required"
            )
        classes = len(rows)
        expected = (
            sum(
                (Fraction(row[i], sum(row)) for i, row in enumerate(rows)),
                start=Fraction(),
            )
            / classes
        )
        rational = raw.get("balanced_accuracy")
        if (
            not isinstance(rational, list)
            or len(rational) != 2
            or any(type(part) is not int for part in rational)
            or rational[1] <= 0
            or Fraction(rational[0], rational[1]) != expected
        ):
            raise ValueError("balanced accuracy must be the exact rational mean class recall")
        query_count = raw.get("query_count")
        total = sum(sum(row) for row in rows)
        if type(query_count) is not int or query_count != total:
            raise ValueError("query_count must equal the positive confusion total")
        for name in ("support_losses", "stage_timings_s"):
            if name in raw and not _finite_floats(raw[name]):
                raise ValueError(f"{name} must be a list of finite numbers")
        return raw

    def measured_identities(self) -> dict[tuple[str, str, str, int, int], str]:
        """Index published cells by their case identity key."""
        index: dict[tuple[str, str, str, int, int], str] = {}
        if not self._cells.is_dir():
            return index
        for path in sorted(self._cells.glob("*.json")):
            record = json.loads(path.read_text("utf-8"))
            identity = record["payload"]["identity"]
            key = (
                identity["dataset"],
                identity["target_subject"],
                identity["method"],
                int(identity["shots_per_class"]),
                int(identity["model_seed"]),
            )
            expected = envelope(
                "evaluation_cell",
                {"identity": identity, "metrics": record["payload"]["metrics"]},
            )
            if canonical_config_json(record) != canonical_config_json(expected):
                raise ValueError(f"published cell no longer verifies: {path.name}")
            if path.name != f"{CellIdentity(**identity).sha256}.json":
                raise ValueError(f"published cell filename differs from its identity: {path.name}")
            if key in index:
                raise ValueError(f"duplicate cells share one identity key: {key}")
            index[key] = record["sha256"]
        return index

    def completion(self, plans: Sequence[CasePlan]) -> dict[str, Any]:
        """Separate scientific and engineering accounting from immutable records."""
        measured = self.measured_identities()
        rows = []
        for plan in plans:
            verified_claims = self._claimed_attempts(plan)
            verified_failures = self._failed_attempts(plan, verified_claims)
            if 2 in verified_claims and 1 not in verified_failures:
                raise ValueError(f"case retry has no verified prior failure: {plan.case_id}")
            claims = sorted(
                p.name for p in self._claims.glob(f"{plan.case_id}.attempt*.claim.json")
            ) if self._claims.is_dir() else []
            failures = sorted(
                p.name for p in self._attempts.glob(f"{plan.case_id}.attempt*.failure.json")
            ) if self._attempts.is_dir() else []
            success_path = self._successes / f"{plan.case_id}.success.json"
            case_measured = False
            if success_path.is_file():
                receipt = json.loads(success_path.read_text("utf-8"))
                payload = receipt.get("payload")
                cell_sha256 = measured.get(plan.identity_key)
                if cell_sha256 is None:
                    raise ValueError(f"measured case has no verified cell: {plan.case_id}")
                if not isinstance(payload, dict):
                    raise ValueError(f"case success no longer verifies: {plan.case_id}")
                attempt = payload.get("attempt")
                if (
                    type(attempt) is not int
                    or attempt not in verified_claims
                    or attempt != verified_claims[-1]
                    or attempt in verified_failures
                    or not verify_envelope(
                        receipt,
                        kind="engineering_smoke",
                        expected_payload={
                            "purpose": "pilot_case_success",
                            "case": asdict(plan),
                            "attempt": attempt,
                            "cell_sha256": cell_sha256,
                        },
                    )
                ):
                    raise ValueError(f"case success no longer verifies: {plan.case_id}")
                intent_path = self._intents / f"{plan.case_id}.intent.json"
                if intent_path.exists() or intent_path.is_symlink():
                    intent_attempt, _, _ = self._verified_intent(
                        plan, expected_cell_sha256=cell_sha256,
                    )
                    if intent_attempt != attempt:
                        raise ValueError(
                            f"case publication intent attempt differs: {plan.case_id}"
                        )
                case_measured = True
            engineering_intent_path = (
                self._engineering_intents / f"{plan.case_id}.intent.json"
            )
            engineering_success_path = (
                self._engineering_successes / f"{plan.case_id}.success.json"
            )
            engineering_recovery_pending = _present(engineering_intent_path)
            case_engineering_success = False
            evidence_sha256: str | None = None
            if engineering_recovery_pending:
                if (
                    engineering_intent_path.is_symlink()
                    or engineering_intent_path.resolve() != engineering_intent_path
                    or not engineering_intent_path.is_file()
                    or engineering_intent_path.stat().st_nlink != 1
                ):
                    raise ValueError("engineering success intent aliases another path")
                intent_record = json.loads(engineering_intent_path.read_text("utf-8"))
                if not isinstance(intent_record, dict):
                    raise ValueError("engineering success intent no longer verifies")
                intent_payload = intent_record.get("payload")
                if not isinstance(intent_payload, dict):
                    raise ValueError("engineering success intent no longer verifies")
                evidence_sha256 = intent_payload.get("attested_evidence_sha256")
                if not isinstance(evidence_sha256, str):
                    raise ValueError("engineering success intent evidence differs")
                require_digest(evidence_sha256, "engineering success evidence")
                self._verified_engineering_intent(
                    plan, expected_attested_evidence_sha256=evidence_sha256,
                )
            if _present(engineering_success_path):
                if not engineering_recovery_pending or evidence_sha256 is None:
                    raise ValueError("engineering success has no write-once intent")
                self._verified_engineering_success(
                    plan, expected_attested_evidence_sha256=evidence_sha256,
                )
                case_engineering_success = True
                engineering_recovery_pending = False
            if case_engineering_success and case_measured:
                raise ValueError("one case cannot be both scientific and engineering success")
            latest_attempt_failed = bool(
                verified_claims and verified_claims[-1] in verified_failures
            )
            rows.append(
                {
                    "case": asdict(plan),
                    "case_id": plan.case_id,
                    "measured": case_measured,
                    "engineering_success": case_engineering_success,
                    "engineering_recovery_pending": engineering_recovery_pending,
                    "latest_attempt_failed": latest_attempt_failed,
                    "claims": claims,
                    "failures": failures,
                }
            )
        return {
            "planned": len(plans),
            "measured": sum(1 for r in rows if r["measured"]),
            "engineering_success": sum(1 for r in rows if r["engineering_success"]),
            "engineering_pending_recovery": sum(
                1 for r in rows if r["engineering_recovery_pending"]
            ),
            "claimed_unmeasured": sum(
                1 for r in rows if r["claims"] and not r["measured"]
                and not r["engineering_success"] and not r["engineering_recovery_pending"]
                and not r["latest_attempt_failed"]
            ),
            "failed": sum(
                1 for r in rows if r["latest_attempt_failed"] and not r["measured"]
                and not r["engineering_success"] and not r["engineering_recovery_pending"]
            ),
            "pending": sum(
                1 for r in rows if not r["claims"] and not r["measured"]
                and not r["engineering_success"]
            ),
            "cases": rows,
        }


class LockedCase:
    """Operations allowed while one CaseRecorder.case_session holds its OS lock."""

    __slots__ = ("_recorder", "_plan", "_thread_id", "_closed")

    def __init__(self, recorder: CaseRecorder, plan: CasePlan, thread_id: int) -> None:
        self._recorder = recorder
        self._plan = plan
        self._thread_id = thread_id
        self._closed = False

    @property
    def plan(self) -> CasePlan:
        return self._plan

    def _require_active(self) -> None:
        if self._closed:
            raise RuntimeError("case session is closed")
        if threading.get_ident() != self._thread_id:
            raise RuntimeError("case session cannot be used from another thread")
        digest = config_digest({"cell_identity_key": self.plan.identity_key})
        path = self._recorder._locks / f"{digest}.lock"
        if str(path) not in getattr(_LOCK_OWNERS, "paths", set()):
            raise RuntimeError("case session no longer owns its identity lock")

    def claim(self, *, worker: str, attempt: int = 1) -> Path:
        self._require_active()
        return self._recorder._claim_locked(self.plan, worker=worker, attempt=attempt)

    def claim_new(self, *, worker: str, attempt: int = 1) -> Path:
        """Require a fresh claim before launching work under this full-life lock."""
        self._require_active()
        return self._recorder._claim_locked(
            self.plan, worker=worker, attempt=attempt, require_new=True,
        )

    def record_failure(self, *, attempt: int, reason: Mapping[str, Any]) -> Path:
        self._require_active()
        return self._recorder._record_failure_locked(
            self.plan, attempt=attempt, reason=reason,
        )

    def record_cell(self, identity: CellIdentity, *, metrics: Mapping[str, Any]) -> Path:
        self._require_active()
        return self._recorder._record_cell_locked(identity, metrics=metrics, plan=self.plan)

    def recover_cell_from_intent(self, *, expected_cell_sha256: str) -> Path:
        self._require_active()
        require_digest(expected_cell_sha256, "expected attested cell")
        return self._recorder._replay_intent_locked(
            self.plan, expected_cell_sha256=expected_cell_sha256,
        )

    def record_engineering_success(
        self, *, attempt: int, attested_evidence_sha256: str,
    ) -> Path:
        self._require_active()
        return self._recorder._record_engineering_success_locked(
            self.plan, attempt=attempt,
            attested_evidence_sha256=attested_evidence_sha256,
        )

    def recover_engineering_success(
        self, *, expected_attested_evidence_sha256: str,
    ) -> Path:
        self._require_active()
        return self._recorder._replay_engineering_success_locked(
            self.plan, expected_attested_evidence_sha256=expected_attested_evidence_sha256,
        )
