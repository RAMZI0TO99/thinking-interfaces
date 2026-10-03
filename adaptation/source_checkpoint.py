"""Immutable, pickle-free checkpoints for one bounded stateless-SGD source fit."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import torch
from safetensors.torch import load, save
from torch import nn

from core.config import config_digest, config_snapshot
from evaluation.labram_parity import state_digest
from evaluation.phase2_records import envelope, write_once


def source_execution_guard(root: Path, *, cuda: bool, write_bytes: int = 0) -> None:
    """Fresh unchanged machine admission, plus space for the pending checkpoint."""
    from core.gpu_cooling import cool_gpu, load_cooling_policy, read_gpu_temperature
    from evaluation.phase2_pilot import compute_admission

    admission = compute_admission(root, operator_admitted=True)
    if not admission["admitted"]:
        raise RuntimeError(f"source execution resource admission refused: {admission}")
    floor = float(admission["machine"]["minimum_free_disk_gib"]) * 1024**3
    if shutil.disk_usage(root).free - write_bytes < floor:
        raise RuntimeError("checkpoint write would cross the unchanged disk floor")
    if cuda:
        if read_gpu_temperature() is None:
            raise RuntimeError("GPU temperature sensor is unavailable")
        cool_gpu(load_cooling_policy(root / "configs/runtime_limits.toml"))
        if torch.cuda.mem_get_info(0)[0] < 1024**3:
            raise RuntimeError("GPU source execution requires 1 GiB free headroom")


class SourceFitCheckpoint:
    """A single-writer journal; only fsynced weights with a committed manifest resume.

    Generations are retained, never replaced or pruned. Partial weight files are
    ignored because their manifest was not published; corrupt committed records
    fail closed. OS byte locks release on process death, without deleting stale
    PID files. Storage admission includes every new blob and manifest.
    """

    def __init__(
        self, root: Path, directory: Path, contract: Mapping[str, Any], fit: Mapping[str, Any]
    ) -> None:
        self.root = root.resolve()
        self.directory = directory.resolve()
        allowed = self.root / "runs" / "phase2"
        if self.directory == allowed or not self.directory.is_relative_to(allowed):
            raise ValueError("checkpoints require a dedicated directory inside runs/phase2")
        self.contract = config_snapshot(contract)
        self.contract_sha = config_digest(self.contract)
        self.fit = config_snapshot(fit)
        self.fit_sha = config_digest(self.fit)
        self.output = self.directory / self.fit_sha
        self.previous: dict[str, Any] | None = None
        self.active = False

    @contextmanager
    def session(self) -> Iterator[None]:
        self.directory.mkdir(parents=True, exist_ok=True)
        if self.directory.resolve() != self.directory:
            raise ValueError("checkpoint directory identity changed")
        if (self.directory / ".writer.lock").is_symlink():
            raise ValueError("checkpoint lock cannot be a symbolic link")
        with (self.directory / ".writer.lock").open("a+b") as handle:
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.active = True
            try:
                write_once(
                    self.directory / "context.json",
                    envelope(
                        "engineering_smoke",
                        {
                            "purpose": "source_checkpoint_context",
                            "contract": self.contract,
                            "contract_sha256": self.contract_sha,
                        },
                    ),
                    output_root=self.directory,
                )
                self.output.mkdir(exist_ok=True)
                if self.output.resolve() != self.output:
                    raise ValueError("checkpoint fit directory identity changed")
                yield
            finally:
                self.active = False
                handle.seek(0)
                if sys.platform == "win32":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def restore(
        self, model: nn.Module, optimizer: torch.optim.SGD, *, cuda: bool
    ) -> tuple[list[dict[str, Any]], dict[str, Any], torch.Tensor | None]:
        if not self.active:
            raise RuntimeError("checkpoint access requires its writer lock")
        previous: dict[str, Any] | None = None
        last_blob: bytes | None = None
        for path in sorted(self.output.glob("*.json")):
            if path.resolve().parent != self.output or path.is_symlink():
                raise ValueError("checkpoint record escaped the admitted directory")
            if re.fullmatch(r"step-\d{6}-[0-9a-f]{32}\.json", path.name) is None:
                raise ValueError("unrecognized committed checkpoint record")
            record = json.loads(path.read_bytes())
            payload = record["payload"]
            step = payload["step"]
            if (
                record != envelope("engineering_smoke", payload)
                or payload["contract_sha256"] != self.contract_sha
                or payload["fit"] != self.fit
                or type(step) is not int
                or step != (1 if previous is None else previous["payload"]["step"] + 1)
                or payload["previous_sha256"] != (None if previous is None else previous["sha256"])
                or not path.name.startswith(f"step-{step:06d}-")
                or payload["weights_file"] != path.with_suffix(".safetensors").name
            ):
                raise ValueError("checkpoint identity or contiguous history differs")
            weights = path.with_suffix(".safetensors")
            if weights.resolve().parent != self.output or weights.is_symlink():
                raise ValueError("checkpoint weights escaped the admitted directory")
            blob = weights.read_bytes()
            if hashlib.sha256(blob).hexdigest() != payload["weights_sha256"]:
                raise ValueError("committed checkpoint weights are corrupted")
            previous, last_blob = record, blob
        self.previous = previous
        if previous is None:
            return [], {}, None
        assert last_blob is not None
        payload = previous["payload"]
        history = payload["history"]
        if not isinstance(history, list) or len(history) != payload["step"]:
            raise ValueError("checkpoint cursor differs from its history")
        if history[-1]["state_sha256_after"] != payload["model_sha256"]:
            raise ValueError("checkpoint model differs from its recorded final step")
        # This executor intentionally supports only the existing momentum-free SGD.
        if optimizer.state or payload["optimizer"] != config_snapshot(optimizer.state_dict()):
            raise ValueError("checkpoint optimizer differs from stateless SGD")
        tensors = load(last_blob)
        model_state = {
            name[6:]: tensor for name, tensor in tensors.items() if name.startswith("model.")
        }
        expected = model.state_dict()
        if model_state.keys() != expected.keys() or any(
            value.shape != expected[name].shape
            or value.dtype != expected[name].dtype
            or not torch.isfinite(value).all()
            for name, value in model_state.items()
        ):
            raise ValueError("checkpoint tensor schema differs from the model")
        model.load_state_dict(model_state, strict=True)
        if state_digest(model) != payload["model_sha256"]:
            raise ValueError("checkpoint model state digest differs")
        optimizer.load_state_dict(payload["optimizer"])
        torch.random.set_rng_state(tensors["rng.cpu"])
        if cuda:
            torch.cuda.set_rng_state(tensors["rng.cuda"], 0)
        for row in history:
            row["trial_ids"] = tuple(row["trial_ids"])
        return history, payload["input_identities"], tensors["rng.sampling"]

    def publish(
        self,
        model: nn.Module,
        optimizer: torch.optim.SGD,
        history: list[dict[str, Any]],
        identities: Mapping[str, Any],
        sampling_state: torch.Tensor,
        *,
        cuda: bool,
    ) -> None:
        if not self.active or optimizer.state:
            raise RuntimeError("locked stateless-SGD checkpoint publication required")
        step = len(history)
        expected = 1 if self.previous is None else self.previous["payload"]["step"] + 1
        if step != expected:
            raise ValueError("checkpoint steps must advance exactly once")
        tensors = {
            f"model.{name}": value.detach().cpu().contiguous().clone()
            for name, value in model.state_dict().items()
        }
        tensors["rng.cpu"] = torch.random.get_rng_state()
        tensors["rng.sampling"] = sampling_state.clone()
        if cuda:
            tensors["rng.cuda"] = torch.cuda.get_rng_state(0)
        blob = save(tensors)
        name = f"step-{step:06d}-{uuid.uuid4().hex}"
        weights = self.output / f"{name}.safetensors"
        record = envelope(
            "engineering_smoke",
            {
                "purpose": "bounded_source_fit_checkpoint",
                "contract_sha256": self.contract_sha,
                "fit": self.fit,
                "step": step,
                "history": history,
                "input_identities": dict(identities),
                "optimizer": optimizer.state_dict(),
                "model_sha256": state_digest(model),
                "weights_file": weights.name,
                "weights_sha256": hashlib.sha256(blob).hexdigest(),
                "previous_sha256": None if self.previous is None else self.previous["sha256"],
            },
        )
        source_execution_guard(
            self.root, cuda=cuda, write_bytes=len(blob) + len(json.dumps(record).encode()) * 2
        )
        with weights.open("xb") as stream:
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        write_once(self.output / f"{name}.json", record, output_root=self.directory)
        self.previous = record
