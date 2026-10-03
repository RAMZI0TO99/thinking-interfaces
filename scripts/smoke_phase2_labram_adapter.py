"""Bounded offline one-shot adapter checks using the pinned safe LaBraM checkpoint."""

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

from adaptation.labram_adapter import (  # noqa: E402
    adapt_labram_adapter_support,
    inject_labram_adapters,
)
from encoder.labram import LaBraMClassifier, configure_pretrained_sequence  # noqa: E402
from evaluation.labram_parity import state_digest, verified_bytes  # noqa: E402
from evaluation.phase2_records import envelope, write_once  # noqa: E402
from scripts.audit_phase2_protocol import file_digest, inside  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/phase2/adapter_smoke.toml"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config: dict[str, Any] = load_toml(args.config)
    settings = config["smoke"]
    if (
        settings["purpose"] != "bounded_cpu_engineering_smoke_not_scientific_experiment"
        or settings["device"] != "cpu"
        or settings["optimizer"] != "sgd"
        or settings["normalization_policy"]
        != "all_eval_support_gradients_only_adapter_and_optional_head"
        or not 1 <= settings["threads"] <= 2
        or not 2 <= settings["steps"] <= 5
        or settings["support_examples"] != settings["classes"]
        or settings["classes"] != 2
        or settings["query_examples"] != 2
        or settings["samples"] != 800
        or len(settings["channel_names"]) != 3
        or len(settings["target_modules"]) > 2
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
    base = LaBraMClassifier(
        backbone, classes=settings["classes"], channel_names=tuple(settings["channel_names"])
    )
    base.eval().requires_grad_(False)
    base_hash = state_digest(base)
    template = copy.deepcopy(base)
    report = inject_labram_adapters(
        template,
        target_modules=tuple(settings["target_modules"]),
        bottleneck_dim=settings["bottleneck_dim"],
    )
    template_hash = state_digest(template)
    template_state = {n: p.detach().clone() for n, p in template.state_dict().items()}
    support = torch.randn(2, 3, 800) * settings["synthetic_input_scale"]
    labels = torch.tensor([0, 1])
    query = torch.randn(2, 3, 800) * settings["synthetic_input_scale"]
    inputs_before = [value.clone() for value in (support, labels, query)]
    with torch.inference_mode():
        baseline = base(query)
        torch.testing.assert_close(template(query), baseline, rtol=0, atol=0)
    results = []
    for train_head in (False, True):
        result = adapt_labram_adapter_support(
            template,
            support,
            labels,
            steps=settings["steps"],
            learning_rate=settings["learning_rate"],
            train_head=train_head,
        )
        adapted = result.model
        changed = []
        for name, value in adapted.state_dict().items():
            if not torch.equal(value, template_state[name]):
                changed.append(name)
                if name not in result.trainable_names:
                    raise ValueError(f"frozen source state changed: {name}")
        expected = {
            name
            for name, _ in adapted.named_parameters()
            if ".adapter." in name or (train_head and name.startswith("head."))
        }
        if set(result.trainable_names) != expected:
            raise ValueError("trainable adapter/head mask differs from declared policy")
        if (
            not any(".adapter.down.weight" in n for n in changed)
            or not any(".adapter.up.weight" in n for n in changed)
            or (("head.weight" in changed) != train_head)
        ):
            raise ValueError("support updates did not reach the declared parameter groups")
        before_query = state_digest(adapted)
        with torch.inference_mode():
            after = adapted(query)
            adapted(query * 10)
        if state_digest(adapted) != before_query:
            raise ValueError("query mutated model state")
        delta = float((after - baseline).abs().max())
        if not torch.isfinite(after).all() or delta <= 0:
            raise ValueError("no finite effective adapter query change")
        repeated = adapt_labram_adapter_support(
            template,
            support,
            labels,
            steps=settings["steps"],
            learning_rate=settings["learning_rate"],
            train_head=train_head,
        )
        if state_digest(repeated.model) != before_query or repeated.losses != result.losses:
            raise ValueError("fresh support episode did not reset exactly")
        restored = copy.deepcopy(template)
        restored.load_state_dict(adapted.state_dict(), strict=True)
        with torch.inference_mode():
            torch.testing.assert_close(restored(query), after, rtol=0, atol=0)
        if any(m.training for m in adapted.modules()) or any(
            p.grad is not None for p in adapted.parameters()
        ):
            raise ValueError("adapted evaluation mode or cleared gradient policy failed")
        if any(
            p.data_ptr() == dict(template.named_parameters())[n].data_ptr()
            for n, p in adapted.named_parameters()
        ):
            raise ValueError("episode shares parameter storage with source")
        results.append(
            {
                "train_head": train_head,
                "trainable_names": result.trainable_names,
                "trainable_parameters": result.trainable_parameters,
                "changed_state_names": changed,
                "support_losses": result.losses,
                "query_maximum_logit_change": delta,
                "query_state_unchanged": True,
                "episode_reset_exact": True,
                "state_round_trip_exact": True,
                "source_storage_isolated": True,
                "all_modules_eval": True,
            }
        )
    if state_digest(base) != base_hash or state_digest(template) != template_hash:
        raise ValueError("source model or source template mutated")
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
        "injection": asdict(report),
        "checkpoint_sha256": safe["sha256"],
        "model_config_sha256": settings["model_config_sha256"],
        "torch_version": torch.__version__,
        "braindecode_source_sha256": file_digest(Path(inspect.getfile(Labram))),
        "initial_exact_identity": True,
        "base_and_template_unchanged": True,
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
                "adapter_parameters": report.adapter_parameters,
                "query_logit_changes": [r["query_maximum_logit_change"] for r in results],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
