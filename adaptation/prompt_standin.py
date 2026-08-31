"""Small attention backbone for testing support-conditioned prompt integration."""

from __future__ import annotations

from typing import cast

import torch
from torch import nn

from adaptation.prompt import PromptInjector, SupportPromptGenerator


class PromptedTransformerStandIn(nn.Module):
    """Frozen attention model with one support-only context and a trainable generator.

    This is an integration test model, not TCPL or LaBraM. Inputs are precomputed
    token features. The same detached support context conditions every query.
    """

    def __init__(
        self,
        *,
        embedding_dim: int,
        classes: int,
        prompt_tokens: int,
        hidden_dim: int,
        layers: int,
        heads: int,
        mode: str,
        support_embeddings: torch.Tensor,
        support_labels: torch.Tensor,
    ) -> None:
        super().__init__()
        if layers < 1 or heads < 1 or embedding_dim % heads:
            raise ValueError("valid attention dimensions and at least one block are required")
        if (
            support_embeddings.ndim != 3
            or support_embeddings.shape[0] != 1
            or support_embeddings.shape[1] < 1
            or support_embeddings.shape[2] != embedding_dim
            or support_labels.shape != support_embeddings.shape[:2]
            or support_labels.dtype != torch.long
            or not torch.isfinite(support_embeddings).all()
            or support_labels.min().item() < 0
            or support_labels.max().item() >= classes
        ):
            raise ValueError("one finite, nonempty support episode with valid labels is required")
        self.embedding_dim = embedding_dim
        self.prompt_tokens = prompt_tokens
        self.mode = mode
        self.injector = PromptInjector(mode)
        self.register_buffer("support_embeddings", support_embeddings.detach().clone())
        self.register_buffer("support_labels", support_labels.detach().clone())
        self.generator = SupportPromptGenerator(
            embedding_dim=embedding_dim,
            classes=classes,
            prompt_tokens=prompt_tokens,
            hidden_dim=hidden_dim,
        )
        self.blocks = nn.ModuleList(
            nn.TransformerEncoderLayer(
                d_model=embedding_dim,
                nhead=heads,
                dim_feedforward=embedding_dim * 2,
                dropout=0.0,
                batch_first=True,
            )
            for _ in range(layers)
        )
        self.head = nn.Linear(embedding_dim, classes)
        self.blocks.requires_grad_(False)
        self.head.requires_grad_(False)

    def generated_prompts(self) -> torch.Tensor:
        return cast(torch.Tensor, self.generator(self.support_embeddings, self.support_labels))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if (
            inputs.ndim != 3
            or inputs.shape[0] < 1
            or inputs.shape[1] < 1
            or inputs.shape[2] != self.embedding_dim
            or not torch.isfinite(inputs).all()
        ):
            raise ValueError(
                "finite nonempty token sequences with the configured width are required"
            )
        prompts = self.generated_prompts().expand(inputs.shape[0], -1, -1)
        sequence = inputs
        for index, block in enumerate(self.blocks):
            sequence = self.injector.for_block(sequence, prompts, block_index=index)
            sequence = block(sequence)
            if self.mode == "per_block_prefix":
                # Replace prefixes at each block; never accumulate extra prompt tokens.
                sequence = sequence[:, self.prompt_tokens :]
        if self.mode == "temporal_prefix":
            sequence = sequence[:, self.prompt_tokens :]
        # Read only EEG-token representations, after attention to the prompt context.
        return cast(torch.Tensor, self.head(sequence.mean(dim=1)))
