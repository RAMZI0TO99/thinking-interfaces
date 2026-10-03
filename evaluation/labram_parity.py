"""Strict, stagewise numerical checks for the separately loaded LaBraM reference."""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

import torch
from torch import nn

from scripts.audit_labram_checkpoint import original_key


def load_reference(source: bytes, filename: str) -> ModuleType:
    """Adapt only timm imports/registration, preserving every forward definition.

    The pinned model uses timm's trunc_normal_ for initialization, after which
    strict loading replaces every tensor. Its drop_path and to_2tuple are never
    needed by our zero-drop-path temporal-convolution configuration; fail if used.
    No global packages or import state are patched.
    """
    tree = ast.parse(source, filename=filename)
    expected = {
        "timm.models.layers": ["drop_path", "to_2tuple", "trunc_normal_"],
        "timm.models.registry": ["register_model"],
    }
    seen = {}
    body = []
    factories = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in expected:
            if node.module in seen or any(alias.asname is not None for alias in node.names):
                raise ValueError("unexpected timm import")
            seen[node.module] = [alias.name for alias in node.names]
            continue
        if isinstance(node, ast.FunctionDef) and node.name.startswith("labram_"):
            if len(node.decorator_list) != 1 or not isinstance(node.decorator_list[0], ast.Name):
                raise ValueError("unexpected factory decorators")
            if node.decorator_list[0].id != "register_model":
                raise ValueError("unexpected factory registration")
            node.decorator_list = []
            factories.append(node.name)
        body.append(node)
    if seen != expected or factories != [
        f"labram_{s}_patch200_200" for s in ("base", "large", "huge")
    ]:
        raise ValueError("reference compatibility assumptions changed")
    tree.body = body
    module = ModuleType("phase2_pinned_labram_reference")
    module.__file__ = filename

    def unused(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("unsupported timm helper reached in bounded parity forward")

    module.__dict__.update(trunc_normal_=nn.init.trunc_normal_, drop_path=unused, to_2tuple=unused)
    exec(compile(tree, filename, "exec"), module.__dict__)
    return module


def verified_bytes(path: Path, expected_sha256: str) -> bytes:
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError(f"pinned file hash mismatch: {path.name}")
    return payload


def reference_channel_order(source: bytes) -> tuple[str, ...]:
    """Read the upstream literal table without importing its data loaders/utilities."""
    candidates = [
        node.value
        for node in ast.parse(source).body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "standard_1020" for target in node.targets
        )
    ]
    if len(candidates) != 1:
        raise ValueError("expected exactly one upstream channel table")
    names = ast.literal_eval(candidates[0])
    if (
        not isinstance(names, list)
        or len(names) != 136
        or any(not isinstance(name, str) for name in names)
        or len({name.upper() for name in names}) != 136
    ):
        raise ValueError("invalid upstream channel table")
    return tuple(names)


def reference_state(
    safe: Mapping[str, torch.Tensor], expected: Mapping[str, torch.Tensor]
) -> dict[str, torch.Tensor]:
    """Require a bijection with matching shapes/dtypes before strict reference loading."""
    mapped = {}
    for name, tensor in safe.items():
        target = original_key(name).removeprefix("student.")
        if target in mapped:
            raise ValueError(f"duplicate reference tensor: {target}")
        mapped[target] = tensor
    if set(mapped) != set(expected):
        raise ValueError("safe/reference tensor names are not a bijection")
    for name, tensor in mapped.items():
        if tensor.shape != expected[name].shape or tensor.dtype != expected[name].dtype:
            raise ValueError(f"safe/reference shape or dtype mismatch: {name}")
    return mapped


def tensor_check(
    actual: torch.Tensor, expected: torch.Tensor, *, atol: float, rtol: float
) -> dict[str, Any]:
    if atol < 0 or rtol < 0:
        raise ValueError("tolerances must be nonnegative")
    same_shape = actual.shape == expected.shape
    finite = bool(torch.isfinite(actual).all() and torch.isfinite(expected).all())
    comparable = same_shape and actual.dtype == expected.dtype and actual.numel() > 0
    delta = (actual - expected).abs() if comparable and finite else None
    return {
        "actual_shape": list(actual.shape),
        "reference_shape": list(expected.shape),
        "finite": finite,
        "maximum_absolute_error": float(delta.max()) if delta is not None else None,
        "exact": comparable and finite and torch.equal(actual, expected),
        "passed": comparable and finite and torch.allclose(actual, expected, atol=atol, rtol=rtol),
    }


def compare_stages(
    actual: Mapping[str, torch.Tensor],
    expected: Mapping[str, torch.Tensor],
    *,
    atol: float,
    rtol: float,
) -> dict[str, dict[str, Any]]:
    if not actual or set(actual) != set(expected):
        raise ValueError("missing, extra or empty forward stages")
    return {
        name: tensor_check(value, expected[name], atol=atol, rtol=rtol)
        for name, value in actual.items()
    }


def capture_stages(model: nn.Module, forward: Callable[[], Any]) -> dict[str, torch.Tensor]:
    """Observe actual public forwards; always remove hooks, including on failure."""
    stages: dict[str, torch.Tensor] = {}
    modules = dict(model.named_modules())
    names = ["patch_embed", "pos_drop", *(f"blocks.{i}" for i in range(12)), "norm"]
    if any(name not in modules for name in names):
        raise ValueError("expected the complete 12-block base encoder")

    def hook(name: str) -> Callable[..., None]:
        def record(module: nn.Module, inputs: Any, output: torch.Tensor) -> None:
            if name in stages:
                raise ValueError(f"forward stage executed twice: {name}")
            stages[name] = output.detach().clone()

        return record

    handles = [modules[name].register_forward_hook(hook(name)) for name in names]
    try:
        with torch.inference_mode():
            output = forward()
            if isinstance(output, dict):
                stages["cls"] = output["cls_token"].detach().clone()
                stages["patch_tokens"] = output["features"].detach().clone()
            else:
                stages["cls"] = output[:, 0].detach().clone()
                stages["patch_tokens"] = output[:, 1:].detach().clone()
    finally:
        for handle in handles:
            handle.remove()
    if set(stages) != {*names, "cls", "patch_tokens"}:
        raise ValueError("forward did not execute all expected stages")
    return stages


def state_digest(model: nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(name.encode())
        digest.update(str((tuple(value.shape), value.dtype)).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()
