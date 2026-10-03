"""Complete local TCPL reconstruction; author and score parity are unverified.

Implements the constructor choices in configs/phase2/tcpl_local_contract.toml.
The episode runner, preprocessing and scientific training budget are separate.
"""

from __future__ import annotations

from typing import cast

import torch
from torch import nn

from adaptation.tcpl_prompt import TCPLSupportPromptGenerator
from encoder.tcpl_tcn import TCPLCausalTCN


class TCPLClassifier(nn.Module):
    """Classify complete query trials conditioned on each episode's support.

    Support: [episodes, shots, channels, time]. Queries: [episodes, queries,
    channels, time]. Output: [episodes, queries, classes] unnormalized logits.
    Each tensor has uniform trial lengths; support/query lengths may differ.
    There is no padding mask, positional encoding, CLS token or episode cache.

    Source gradients reach the TCN, support encoder, generator, Transformer and
    head. For target inference the caller must use eval(), requires_grad_(False)
    and inference_mode(). No target optimization or trial-permission inference
    occurs here. Ordinary train mode activates TCN/Transformer dropout.
    Attention is bidirectional within each complete trial, not across queries.
    """

    def __init__(self, input_channels: int, classes: int) -> None:
        super().__init__()
        if type(classes) is not int or classes < 2:
            raise ValueError("classes must be an integer of at least two")
        self.tcn = TCPLCausalTCN(input_channels)
        self.support_prompt = TCPLSupportPromptGenerator(input_channels)
        self.input_channels = input_channels
        self.classes = classes
        # Construct separately: no shared parameters or cloned initial weights.
        self.transformer = nn.ModuleList(
            nn.TransformerEncoderLayer(
                d_model=64, nhead=8, dim_feedforward=256, dropout=0.1,
                activation="relu", layer_norm_eps=1e-5, batch_first=True,
                norm_first=False, bias=True,
            )
            for _ in range(4)
        )
        self.head = nn.Linear(64, classes)
        # Do not reinitialize the existing TCN/support components.
        for block in self.transformer:
            layer = cast(nn.TransformerEncoderLayer, block)
            nn.init.xavier_uniform_(layer.self_attn.in_proj_weight)
            nn.init.zeros_(layer.self_attn.in_proj_bias)
            for module in layer.modules():
                if isinstance(module, nn.Linear):
                    nn.init.xavier_uniform_(module.weight)
                    nn.init.zeros_(module.bias)
                elif isinstance(module, nn.LayerNorm):
                    nn.init.ones_(module.weight)
                    nn.init.zeros_(module.bias)
        nn.init.xavier_uniform_(self.head.weight)
        nn.init.zeros_(self.head.bias)

    def _validate_queries(self, queries: torch.Tensor) -> None:
        if (
            queries.ndim != 4
            or queries.shape[0] < 1
            or queries.shape[1] < 1
            or queries.shape[2] != self.input_channels
            or queries.shape[3] < 1
            or not queries.is_floating_point()
            or not torch.isfinite(queries).all()
        ):
            raise ValueError("expected finite nonempty [episodes, queries, input_channels, time]")

    def forward(self, support: torch.Tensor, queries: torch.Tensor) -> torch.Tensor:
        self._validate_queries(queries)
        if (
            support.ndim != 4
            or support.shape[0] != queries.shape[0]
            or support.device != queries.device
            or support.dtype != queries.dtype
        ):
            raise ValueError("support/query episode counts, devices and dtypes must match")
        return self.forward_with_prompts(queries, self.support_prompt(support))

    def forward_with_prompts(
        self, queries: torch.Tensor, prompts: torch.Tensor
    ) -> torch.Tensor:
        """Reuse [episodes,10,64] support prompts across query batches.

        This path neither copies nor detaches prompts: source meta-training can
        compute them once and use them in both query loss and regularization.
        Fixed-target callers may precompute them under inference_mode().
        Inputs require a common floating dtype/device; mixed precision is unverified.
        """
        self._validate_queries(queries)
        episodes, query_count, channels, samples = queries.shape
        prompt_count = self.support_prompt.prompt_count
        if (
            prompts.shape != (episodes, prompt_count, 64)
            or prompts.dtype != queries.dtype
            or prompts.device != queries.device
            or not torch.isfinite(prompts).all()
        ):
            raise ValueError("expected finite [episodes,10,64] prompts matching query dtype/device")
        eeg = self.tcn(queries.reshape(episodes * query_count, channels, samples))
        prefix = prompts[:, None].expand(-1, query_count, -1, -1)
        hidden = torch.cat((prefix.reshape(episodes * query_count, prompt_count, 64), eeg), dim=1)
        for layer in self.transformer:
            hidden = layer(hidden)
        # Exclude only the prefix positions, after all four attention layers.
        pooled = hidden[:, prompt_count:].mean(dim=1)
        return cast(torch.Tensor, self.head(pooled).reshape(episodes, query_count, self.classes))
