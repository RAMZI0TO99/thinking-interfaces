"""Offline CPU one-shot checks for linear, partial and full LaBraM tuning."""

from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.config import config_digest, load_toml
from core.provenance import capture_source
from data.runtime import configure_scientific_runtime

configure_scientific_runtime()

import torch  # noqa: E402
from braindecode.models import Labram  # type: ignore[import-untyped]  # noqa: E402
from safetensors.torch import load_file  # noqa: E402

from adaptation.labram_tuning import (  # noqa: E402
    TuningMethod,
    adapt_labram_tuning_support,
    configure_labram_tuning,
)
from encoder.labram import LaBraMClassifier, configure_pretrained_sequence  # noqa: E402
from evaluation.labram_parity import state_digest, verified_bytes  # noqa: E402
from evaluation.phase2_records import envelope, write_once  # noqa: E402
from scripts.audit_phase2_protocol import file_digest, inside  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/phase2/tuning_smoke.toml"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config: dict[str, Any] = load_toml(args.config)
    settings = config["smoke"]
    if (
        settings["purpose"] != "bounded_cpu_engineering_smoke_not_scientific_experiment"
        or settings["device"] != "cpu"
        or settings["optimizer"] != "sgd"
        or settings["normalization_policy"] != "all_modules_eval_affine_follows_parameter_mask"
        or not 1 <= settings["threads"] <= 2
        or not 1 <= settings["steps"] <= 3
        or settings["support_examples"] != 2
        or settings["classes"] != 2
        or settings["query_examples"] != 2
        or settings["samples"] != 800
        or len(settings["channel_names"]) != 3
        or settings["partial_depths"] != [2, 12]
    ):
        raise ValueError("this command is restricted to the bounded CPU one-shot protocol")
    output_root = inside(root, settings["output_root"])
    if not output_root.is_relative_to((root / "runs/phase2").resolve()):
        raise ValueError("output must stay inside runs/phase2")
    torch.set_num_threads(settings["threads"])
    torch.manual_seed(settings["seed"])
    torch.use_deterministic_algorithms(True)
    source = capture_source(root)
    checkpoint: dict[str, Any] = load_toml(inside(root, settings["checkpoint_config"]))
    safe = checkpoint["safe_conversion"]
    weights_path, model_path = inside(root, safe["path"]), inside(root, settings["model_config"])
    verified_bytes(weights_path, safe["sha256"])
    model_settings = json.loads(verified_bytes(model_path, settings["model_config_sha256"]))
    model_settings.pop("braindecode_version", None)
    backbone = Labram(**model_settings)
    backbone.load_state_dict(load_file(str(weights_path), device="cpu"), strict=True)
    configure_pretrained_sequence(backbone, samples=settings["samples"])
    base = LaBraMClassifier(backbone, classes=2, channel_names=tuple(settings["channel_names"]))
    base.eval().requires_grad_(False)
    base_hash = state_digest(base)
    before = {n: p.detach().clone() for n, p in base.state_dict().items()}
    support = torch.randn(2, 3, 800) * settings["synthetic_input_scale"]
    labels = torch.tensor([0, 1])
    query = torch.randn(2, 3, 800) * settings["synthetic_input_scale"]
    inputs_before = [t.clone() for t in (support, labels, query)]
    with torch.inference_mode():
        baseline = base(query)
    # Exhaustive depth-mask checks do no fitting and cannot select an optimal depth.
    configured = copy.deepcopy(base)
    masks = []
    policies: list[tuple[TuningMethod, int | None]] = [
        ("linear", None),
        *(("partial", i) for i in range(1, 13)),
        ("full", None),
    ]
    for method, depth in policies:
        mask = configure_labram_tuning(configured, method=method, partial_depth=depth)
        if state_digest(configured) != base_hash:
            raise ValueError("mask configuration changed source values or reinitialized the head")
        with torch.inference_mode():
            torch.testing.assert_close(configured(query), baseline, rtol=0, atol=0)
        masks.append(asdict(mask))
    results: list[dict[str, Any]] = []
    episode_policies: list[tuple[TuningMethod, int | None]] = [
        ("linear", None),
        ("partial", 2),
        ("partial", 12),
        ("full", None),
    ]
    for method, depth in episode_policies:
        result = adapt_labram_tuning_support(
            base,
            support,
            labels,
            method=method,
            partial_depth=depth,
            steps=settings["steps"],
            learning_rate=settings["learning_rate"],
        )
        adapted = result.model
        changed = {n for n, p in adapted.state_dict().items() if not torch.equal(p, before[n])}
        if not changed <= set(result.mask.trainable_names) or "head.weight" not in changed:
            raise ValueError("frozen parameters changed or head update was ineffective")
        selected_blocks = result.mask.selected_blocks
        for i in selected_blocks:
            if f"backbone.blocks.{i}.attn.qkv.weight" not in changed:
                raise ValueError(f"selected block {i} has no effective QKV update")
        for name in (
            "backbone.position_embedding",
            "backbone.temporal_embedding",
            "backbone.norm.weight",
            "backbone.patch_embed.temporal_conv.conv1.weight",
        ):
            if (name in changed) != (method == "full"):
                raise ValueError(f"non-block update differs from method policy: {name}")
        before_query = state_digest(adapted)
        with torch.inference_mode():
            after = adapted(query)
            adapted(query * 10)
        if state_digest(adapted) != before_query:
            raise ValueError("query mutated model state")
        delta = float((after - baseline).abs().max())
        if not torch.isfinite(after).all() or delta <= 0:
            raise ValueError("no finite effective query output change")
        repeated = adapt_labram_tuning_support(
            base,
            support,
            labels,
            method=method,
            partial_depth=depth,
            steps=settings["steps"],
            learning_rate=settings["learning_rate"],
        )
        if state_digest(repeated.model) != before_query or repeated.losses != result.losses:
            raise ValueError("episode reset is not exact")
        restored = copy.deepcopy(base)
        restored.load_state_dict(adapted.state_dict(), strict=True)
        with torch.inference_mode():
            torch.testing.assert_close(restored(query), after, rtol=0, atol=0)
        if any(m.training for m in adapted.modules()) or any(
            p.grad is not None for p in adapted.parameters()
        ):
            raise ValueError("evaluation mode or cleared gradient policy failed")
        if any(
            p.data_ptr() == dict(base.named_parameters())[n].data_ptr()
            for n, p in adapted.named_parameters()
        ):
            raise ValueError("source and episode share parameter storage")
        results.append(
            {
                "mask": asdict(result.mask),
                "changed_state_names": sorted(changed),
                "support_losses": result.losses,
                "query_maximum_logit_change": delta,
                "frozen_state_unchanged": True,
                "query_state_unchanged": True,
                "episode_reset_exact": True,
                "state_round_trip_exact": True,
                "source_storage_isolated": True,
                "all_modules_eval": True,
            }
        )
    if state_digest(base) != base_hash or any(p.requires_grad for p in base.parameters()):
        raise ValueError("source values or trainable mask mutated")
    if not all(
        torch.equal(a, b) for a, b in zip(inputs_before, (support, labels, query), strict=True)
    ):
        raise ValueError("input tensors mutated")
    if (
        capture_source(root).source_sha256 != source.source_sha256
        or file_digest(weights_path) != safe["sha256"]
        or file_digest(model_path) != settings["model_config_sha256"]
    ):
        raise ValueError("source or checkpoint inputs changed during smoke")
    payload = {
        "config": config,
        "source": asdict(source),
        "checkpoint_sha256": safe["sha256"],
        "model_config_sha256": settings["model_config_sha256"],
        "torch_version": torch.__version__,
        "braindecode_source_sha256": file_digest(Path(inspect.getfile(Labram))),
        "mask_checks": masks,
        "mask_initial_identity_exact": True,
        "source_unchanged": True,
        "inputs_unchanged": True,
        "one_shot_per_class": True,
        "input_sha256": {
            name: hashlib.sha256(t.numpy().tobytes()).hexdigest()
            for name, t in (("support", support), ("labels", labels), ("query", query))
        },
        "episodes": results,
        "synthetic_data_only": True,
        "trained_source_fit_used": False,
        "scientific_gate_approval": False,
        "passed": True,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = output_root / config_digest(config) / source.source_sha256 / stamp / "receipt.json"
    write_once(output, envelope("engineering_smoke", payload), output_root=output_root)
    print(
        json.dumps(
            {
                "receipt": str(output),
                "passed": True,
                "masks": len(masks),
                "episodes": [
                    {
                        "method": r["mask"]["method"],
                        "depth": r["mask"]["depth"],
                        "trainable_parameters": r["mask"]["trainable_parameters"],
                        "logit_change": r["query_maximum_logit_change"],
                    }
                    for r in results
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
