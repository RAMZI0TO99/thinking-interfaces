"""Bounded offline checks for class-conditioned prompts on the safe LaBraM checkpoint."""

from __future__ import annotations

import argparse
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

from adaptation.labram_prompt import (  # noqa: E402
    ClassPrototypePromptGenerator,
    SupportPromptedLaBraM,
    adapt_labram_prompt_support,
    prompted_labram_logits,
)
from encoder.labram import LaBraMClassifier, configure_pretrained_sequence  # noqa: E402
from evaluation.labram_parity import state_digest, verified_bytes  # noqa: E402
from evaluation.phase2_records import envelope, write_once  # noqa: E402
from scripts.audit_phase2_protocol import file_digest, inside  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/phase2/prompt_smoke.toml"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config: dict[str, Any] = load_toml(args.config)
    settings = config["smoke"]
    if (
        settings["purpose"] != "bounded_cpu_engineering_smoke_not_scientific_experiment"
        or settings["device"] != "cpu"
        or settings["optimizer"] != "sgd"
        or settings["normalization_policy"] != "all_eval_generator_and_optional_head_only"
        or settings["placement"]
        != "after_cls_after_position_time_before_first_block_persist_all_blocks"
        or settings["conditioning"] != "unprompted_frozen_source_cls_class_means_in_label_order"
        or not 1 <= settings["threads"] <= 2
        or not 1 <= settings["steps"] <= 3
        or settings["classes"] != 2
        or settings["support_examples"] != 2
        or settings["query_examples"] != 2
        or settings["samples"] != 800
        or len(settings["channel_names"]) != 3
        or settings["prompt_tokens"] != 4
        or settings["hidden_dim"] != 32
        or settings["support_feature_batch_size"] != 1
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
    generator = ClassPrototypePromptGenerator(
        embedding_dim=200,
        classes=2,
        prompt_tokens=settings["prompt_tokens"],
        hidden_dim=settings["hidden_dim"],
    )
    base_hash, generator_hash = state_digest(base), state_digest(generator)
    support = torch.randn(2, 3, 800) * settings["synthetic_input_scale"]
    labels = torch.tensor([0, 1])
    query = torch.randn(2, 3, 800) * settings["synthetic_input_scale"]
    inputs_before = [t.clone() for t in (support, labels, query)]
    initial = SupportPromptedLaBraM(base, generator, support, labels)
    initial_state = {n: p.detach().clone() for n, p in initial.state_dict().items()}
    lengths = []

    def observe(module: torch.nn.Module, inputs: Any) -> None:
        lengths.append(int(inputs[0].shape[1]))

    handles = [b.register_forward_pre_hook(observe) for b in initial.classifier.backbone.blocks]
    try:
        with torch.inference_mode():
            before = initial(query)
    finally:
        for handle in handles:
            handle.remove()
    if lengths != [17] * 12:  # CLS + four prompts + 3 channels * 4 patches
        raise ValueError("prompt placement or sequence length differs from declaration")
    with torch.inference_mode():
        torch.testing.assert_close(
            prompted_labram_logits(base, query, torch.empty(1, 0, 200)), base(query), rtol=0, atol=0
        )
        initial_prompts = initial.generated_prompts().clone()
    swapped = SupportPromptedLaBraM(base, generator, support, labels.flip(0))
    reordered = SupportPromptedLaBraM(base, generator, support.flip(0), labels.flip(0))
    changed_signals = SupportPromptedLaBraM(
        base, generator, support + 0.1 * torch.randn_like(support), labels
    )
    with torch.inference_mode():
        label_prompt_delta = float((swapped.generated_prompts() - initial_prompts).abs().max())
        label_logit_delta = float((swapped(query) - before).abs().max())
        signal_prompt_delta = float(
            (changed_signals.generated_prompts() - initial_prompts).abs().max()
        )
        if any(
            delta <= 1e-5 for delta in (label_prompt_delta, label_logit_delta, signal_prompt_delta)
        ):
            raise ValueError("prompts do not respond to support signal/label associations")
        torch.testing.assert_close(
            reordered.generated_prompts(), initial_prompts, rtol=1e-5, atol=1e-6
        )
    results = []
    for train_head in (False, True):
        result = adapt_labram_prompt_support(
            base,
            generator,
            support,
            labels,
            steps=settings["steps"],
            learning_rate=settings["learning_rate"],
            train_head=train_head,
        )
        adapted = result.model
        changed = {
            n for n, p in adapted.state_dict().items() if not torch.equal(p, initial_state[n])
        }
        expected = {
            n
            for n, _ in adapted.named_parameters()
            if n.startswith("generator.") or (train_head and n.startswith("classifier.head."))
        }
        if set(result.trainable_names) != expected or not changed <= expected:
            raise ValueError("support changed state outside the declared generator/head mask")
        if not {"generator.network.0.weight", "generator.network.2.weight"} <= changed or (
            ("classifier.head.weight" in changed) != train_head
        ):
            raise ValueError("support updates did not reach the declared parameter groups")
        before_query = state_digest(adapted)
        with torch.inference_mode():
            after = adapted(query)
            prompts_after = adapted.generated_prompts().clone()
            adapted(query * 100)
            torch.testing.assert_close(adapted.generated_prompts(), prompts_after, rtol=0, atol=0)
        if state_digest(adapted) != before_query:
            raise ValueError("query mutated model or support context")
        delta = float((after - before).abs().max())
        prompt_delta = float((prompts_after - initial_prompts).abs().max())
        if not torch.isfinite(after).all() or delta <= 0 or prompt_delta <= 0:
            raise ValueError("no finite effective prompt/query update")
        repeated = adapt_labram_prompt_support(
            base,
            generator,
            support,
            labels,
            steps=settings["steps"],
            learning_rate=settings["learning_rate"],
            train_head=train_head,
        )
        if state_digest(repeated.model) != before_query or repeated.losses != result.losses:
            raise ValueError("episode reset is not exact")
        restored = SupportPromptedLaBraM(base, generator, support, labels)
        restored.load_state_dict(adapted.state_dict(), strict=True)
        with torch.inference_mode():
            torch.testing.assert_close(restored(query), after, rtol=0, atol=0)
        if any(m.training for m in adapted.modules()) or any(
            p.grad is not None for p in adapted.parameters()
        ):
            raise ValueError("evaluation mode or cleared-gradient policy failed")
        for target, original in ((adapted.classifier, base), (adapted.generator, generator)):
            if any(
                p.data_ptr() == dict(original.named_parameters())[n].data_ptr()
                for n, p in target.named_parameters()
            ):
                raise ValueError("source and episode share parameter storage")
        results.append(
            {
                "train_head": train_head,
                "trainable_names": result.trainable_names,
                "trainable_parameters": result.trainable_parameters,
                "changed_state_names": sorted(changed),
                "support_losses": result.losses,
                "query_maximum_logit_change": delta,
                "maximum_prompt_change": prompt_delta,
                "query_and_context_unchanged": True,
                "episode_reset_exact": True,
                "state_round_trip_exact": True,
                "source_storage_isolated": True,
                "all_modules_eval": True,
            }
        )
    if state_digest(base) != base_hash or state_digest(generator) != generator_hash:
        raise ValueError("source model/generator state changed")
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
        "generator_parameters": sum(p.numel() for p in generator.parameters()),
        "empty_prefix_identity_exact": True,
        "block_token_lengths": lengths,
        "label_swap_prompt_delta": label_prompt_delta,
        "label_swap_logit_delta": label_logit_delta,
        "support_signal_prompt_delta": signal_prompt_delta,
        "joint_support_order_check_passed": True,
        "source_and_generator_unchanged": True,
        "inputs_unchanged": True,
        "input_sha256": {
            name: hashlib.sha256(t.numpy().tobytes()).hexdigest()
            for name, t in (("support", support), ("labels", labels), ("query", query))
        },
        "episodes": results,
        "synthetic_data_only": True,
        "trained_source_fit_used": False,
        "tcpl_reproduction": False,
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
                "generator_parameters": payload["generator_parameters"],
                "label_swap_logit_delta": label_logit_delta,
                "query_logit_changes": [r["query_maximum_logit_change"] for r in results],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
