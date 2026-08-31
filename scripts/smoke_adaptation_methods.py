from __future__ import annotations

import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import torch
from torch import nn

from adaptation.adapter import inject_adapters
from adaptation.episodic import adapt_torch_model
from adaptation.lora import inject_lora
from adaptation.prompt import SupportPromptGenerator
from core.config import load_toml


class VectorStandIn(nn.Module):
    def __init__(self, embedding: int, classes: int) -> None:
        super().__init__()
        self.block = nn.Sequential(nn.Linear(embedding, embedding), nn.GELU())
        self.head = nn.Linear(embedding, classes)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.head(self.block(inputs)))


class PromptStandIn(nn.Module):
    def __init__(
        self,
        *,
        embedding: int,
        classes: int,
        tokens: int,
        hidden: int,
    ) -> None:
        super().__init__()
        self.embedding = embedding
        self.generator = SupportPromptGenerator(
            embedding_dim=embedding,
            classes=classes,
            prompt_tokens=tokens,
            hidden_dim=hidden,
        )
        self.head = nn.Linear(embedding, classes)
        self.head.requires_grad_(False)

    def forward(self, packed_support: torch.Tensor) -> torch.Tensor:
        embeddings = packed_support[..., : self.embedding]
        labels = packed_support[..., self.embedding].to(torch.long)
        prompts = self.generator(embeddings, labels)
        return cast(torch.Tensor, self.head(prompts.mean(dim=1)))


def adapt_and_measure(
    model: nn.Module,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    *,
    steps: int,
    learning_rate: float,
    trainable_prefix: str,
) -> dict[str, float | int]:
    before = model(inputs).detach().clone()
    started = time.perf_counter()
    result = adapt_torch_model(
        model,
        inputs,
        targets,
        steps=steps,
        learning_rate=learning_rate,
        trainable=lambda name, _: trainable_prefix in name,
    )
    elapsed = time.perf_counter() - started
    after = result.model(inputs).detach()
    return {
        "trainable_parameters": result.trainable_parameters,
        "steps": len(result.losses),
        "seconds": elapsed,
        "maximum_output_change": float((after - before).abs().max()),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "adaptation.toml"))
    smoke = cast(Mapping[str, Any], config["standin_smoke"])
    lora = cast(Mapping[str, Any], config["lora"])
    adapter = cast(Mapping[str, Any], config["adapter"])
    prompt = cast(Mapping[str, Any], config["prompt"])
    seed = int(smoke["seed"])
    embedding = int(smoke["embedding_dimension"])
    classes = int(smoke["classes"])
    batch = int(smoke["batch_size"])
    shots = int(smoke["shots"])
    steps = int(smoke["steps"])
    learning_rate = float(smoke["learning_rate"])
    torch.manual_seed(seed)
    inputs = torch.randn(batch, embedding)
    targets = torch.arange(batch) % classes

    lora_model = VectorStandIn(embedding, classes)
    rank = int(cast(list[int], lora["ranks"])[0])
    inject_lora(
        lora_model,
        rank=rank,
        alpha=rank * float(lora["alpha_multiplier"]),
        dropout=float(lora["dropout"]),
        target_names={"block.0"},
    )
    lora_result = adapt_and_measure(
        lora_model,
        inputs,
        targets,
        steps=steps,
        learning_rate=learning_rate,
        trainable_prefix="lora_",
    )

    adapter_model = VectorStandIn(embedding, classes)
    inject_adapters(
        adapter_model,
        embedding_dim=embedding,
        bottleneck_dim=int(cast(list[int], adapter["bottleneck_dimensions"])[0]),
        target_names={"block"},
        dropout=float(adapter["dropout"]),
    )
    adapter_result = adapt_and_measure(
        adapter_model,
        inputs,
        targets,
        steps=steps,
        learning_rate=learning_rate,
        trainable_prefix="adapter.",
    )

    prompt_model = PromptStandIn(
        embedding=embedding,
        classes=classes,
        tokens=int(prompt["tokens"]),
        hidden=int(prompt["hidden_dimension"]),
    )
    support_embeddings = torch.randn(batch, shots, embedding)
    support_labels = torch.randint(0, classes, (batch, shots)).to(torch.float32)
    packed = torch.cat((support_embeddings, support_labels.unsqueeze(-1)), dim=-1)
    prompt_result = adapt_and_measure(
        prompt_model,
        packed,
        targets,
        steps=steps,
        learning_rate=learning_rate,
        trainable_prefix="generator.",
    )
    result = {"lora": lora_result, "adapter": adapter_result, "prompt": prompt_result}
    if any(float(value["maximum_output_change"]) <= 0.0 for value in result.values()):
        raise RuntimeError("an adaptation method did not change the stand-in output")
    output = root / "runs" / "adaptation_standin_smoke.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
