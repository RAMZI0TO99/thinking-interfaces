"""Support-set-conditioned prompt token generator."""

from __future__ import annotations

from typing import cast

import torch
from torch import nn

PROMPT_INJECTION_MODES = ("temporal_prefix", "per_block_prefix")


class SupportPromptGenerator(nn.Module):
    """Map support embeddings and labels to a fixed sequence of prompt tokens."""

    def __init__(
        self,
        *,
        embedding_dim: int,
        classes: int,
        prompt_tokens: int,
        hidden_dim: int,
    ) -> None:
        super().__init__()
        if min(embedding_dim, classes, prompt_tokens, hidden_dim) < 1:
            raise ValueError("prompt dimensions must be positive")
        self.embedding_dim = embedding_dim
        self.classes = classes
        self.prompt_tokens = prompt_tokens
        self.label_embedding = nn.Embedding(classes, embedding_dim)
        self.generator = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, prompt_tokens * embedding_dim),
        )

    def forward(
        self, support_embeddings: torch.Tensor, support_labels: torch.Tensor
    ) -> torch.Tensor:
        if support_embeddings.ndim != 3:
            raise ValueError("support_embeddings must have shape (batch, shots, embedding)")
        if support_labels.shape != support_embeddings.shape[:2]:
            raise ValueError("support_labels must match the batch and shot dimensions")
        if support_embeddings.shape[2] != self.embedding_dim:
            raise ValueError("support embedding dimension does not match the generator")
        if support_labels.min().item() < 0 or support_labels.max().item() >= self.classes:
            raise ValueError("support label is outside the configured class range")
        label_features = self.label_embedding(support_labels)
        pooled = torch.cat((support_embeddings, label_features), dim=-1).mean(dim=1)
        generated = self.generator(pooled)
        return cast(
            torch.Tensor,
            generated.reshape(-1, self.prompt_tokens, self.embedding_dim),
        )


def prepend_prompt_tokens(sequence: torch.Tensor, prompts: torch.Tensor) -> torch.Tensor:
    if sequence.ndim != 3 or prompts.ndim != 3:
        raise ValueError("sequences and prompts must be three-dimensional")
    if sequence.shape[0] != prompts.shape[0] or sequence.shape[2] != prompts.shape[2]:
        raise ValueError("prompt and sequence batch/embedding dimensions must match")
    return torch.cat((prompts, sequence), dim=1)


class PromptInjector:
    """Apply support-generated prompts at the configured transformer location."""

    def __init__(self, mode: str) -> None:
        if mode not in PROMPT_INJECTION_MODES:
            raise ValueError(f"unknown prompt injection mode: {mode}")
        self.mode = mode

    def for_block(
        self,
        sequence: torch.Tensor,
        prompts: torch.Tensor,
        *,
        block_index: int,
    ) -> torch.Tensor:
        if block_index < 0:
            raise ValueError("block_index must be non-negative")
        if self.mode == "temporal_prefix" and block_index > 0:
            return sequence
        return prepend_prompt_tokens(sequence, prompts)
