from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import torch

from adaptation.episodic import adapt_torch_model
from adaptation.prompt_standin import PromptedTransformerStandIn
from core.config import config_digest, load_toml
from core.provenance import capture_source


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "prompt_standin.toml"))
    settings = config["standin"]
    torch.set_num_threads(int(settings["cpu_threads"]))
    results = {}
    for mode in settings["modes"]:
        torch.manual_seed(int(settings["seed"]))
        support = torch.randn(
            settings["support_trials"], settings["sequence_tokens"], settings["embedding_dim"]
        )
        labels = torch.arange(settings["support_trials"]) % settings["classes"]
        query = torch.randn(
            settings["query_trials"], settings["sequence_tokens"], settings["embedding_dim"]
        )
        base = PromptedTransformerStandIn(
            embedding_dim=settings["embedding_dim"],
            classes=settings["classes"],
            prompt_tokens=settings["prompt_tokens"],
            hidden_dim=settings["hidden_dim"],
            layers=settings["layers"],
            heads=settings["heads"],
            mode=mode,
            support_embeddings=support.mean(dim=1).unsqueeze(0),
            support_labels=labels.unsqueeze(0),
        )
        before = {key: value.detach().clone() for key, value in base.state_dict().items()}
        query_before = base(query).detach()
        prompts_before = base.generated_prompts().detach().clone()
        started = time.perf_counter()
        result = adapt_torch_model(
            base,
            support,
            labels,
            steps=settings["steps"],
            learning_rate=settings["learning_rate"],
            trainable=lambda name, _: name.startswith("generator."),
        )
        elapsed = time.perf_counter() - started
        adapted = cast(PromptedTransformerStandIn, result.model.eval())
        frozen_unchanged = all(
            torch.equal(value, before[key])
            for key, value in adapted.state_dict().items()
            if not key.startswith("generator.")
        )
        base_unchanged = all(
            torch.equal(value, before[key]) for key, value in base.state_dict().items()
        )
        with torch.inference_mode():
            prompts_after = adapted.generated_prompts().clone()
            saved = {key: value.clone() for key, value in adapted.state_dict().items()}
            query_after = adapted(query)
            adapted(query * 2)
            query_did_not_update = all(
                torch.equal(value, saved[key]) for key, value in adapted.state_dict().items()
            ) and torch.equal(prompts_after, adapted.generated_prompts())
        row = {
            "adaptation_seconds": elapsed,
            "trainable_parameters": result.trainable_parameters,
            "query_output_maximum_change": float((query_before - query_after).abs().max()),
            "prompt_maximum_change": float((prompts_before - prompts_after).abs().max()),
            "frozen_backbone_unchanged": frozen_unchanged,
            "base_model_unchanged": base_unchanged,
            "query_did_not_update_state_or_prompts": query_did_not_update,
            "finite_query_logits": bool(torch.isfinite(query_after).all()),
        }
        row["passed"] = bool(
            frozen_unchanged
            and base_unchanged
            and query_did_not_update
            and row["finite_query_logits"]
            and row["query_output_maximum_change"] > 0
            and row["prompt_maximum_change"] > 0
        )
        results[mode] = row
    report = {
        "config": config,
        "config_sha256": config_digest(config),
        "source": asdict(capture_source(root)),
        "modes": results,
        "passed": all(row["passed"] for row in results.values()),
        "scope": "Synthetic CPU attention integration only; not TCPL reproduction or EEG accuracy.",
    }
    if not report["passed"]:
        raise RuntimeError("prompt attention integration failed")
    path = root / "runs" / "prompt_transformer_smoke.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", "utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
