"""TCPL support conditioning under configs/phase2/tcpl_local_contract.toml.

Local reconstruction choices remain separate from author-verified reproduction.
Unlike the LaBraM prompt variant, this path consumes no support-label embeddings.
"""

from __future__ import annotations

from typing import cast

import torch
from torch import nn


class TCPLSupportEncoder(nn.Module):
    """Encode floating [trials, channels, time] into [trials, 64].

    Local choices: two biased width-64 Conv1d/ReLU stages, symmetric zero
    padding, no normalization or dropout. Temporal mean precedes Linear(64,64).
    Conv1d keeps its installed PyTorch initialization; the linear layer uses
    Xavier-uniform weight and zero bias. Whole support trials are available,
    so this encoder is intentionally noncausal. No input preprocessing is done.
    """

    embedding_dim = 64

    def __init__(self, input_channels: int) -> None:
        super().__init__()
        if type(input_channels) is not int or input_channels < 1:
            raise ValueError("input_channels must be a positive integer")
        self.input_channels = input_channels
        self.features = nn.Sequential(
            nn.Conv1d(input_channels, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(),
        )
        self.projection = nn.Linear(64, self.embedding_dim)
        nn.init.xavier_uniform_(self.projection.weight)
        nn.init.zeros_(self.projection.bias)

    def forward(self, trials: torch.Tensor) -> torch.Tensor:
        if (
            trials.ndim != 3
            or trials.shape[0] < 1
            or trials.shape[1] != self.input_channels
            or trials.shape[2] < 1
            or not trials.is_floating_point()
            or not torch.isfinite(trials).all()
        ):
            raise ValueError("expected finite nonempty floating [trials, input_channels, time]")
        return cast(torch.Tensor, self.projection(self.features(trials).mean(dim=-1)))


class TCPLSupportPromptGenerator(nn.Module):
    """Map [episodes, shots, channels, time] to [episodes, 10, 64].

    Encode each support trial, mean its embedding over shots within its episode,
    then apply Linear(64,64)/ReLU/Linear(64,640) and reshape. All supplied shots
    are real trials; padded or ragged batches need separate calls. The shot axis
    counts the total support trials, not the number of trials per class.

    Generated tokens are differentiable outputs, never independent parameters.
    There are no label/query inputs, detach operations, optimizers or mutable
    episode caches. The caller owns source-training versus fixed-target modes.
    Class-balanced sampling and query exclusion belong to the episode runner.
    """

    prompt_count = 10
    prompt_dim = 64

    def __init__(self, input_channels: int) -> None:
        super().__init__()
        self.encoder = TCPLSupportEncoder(input_channels)
        self.generator = nn.Sequential(nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 640))
        for module in self.generator:
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, support: torch.Tensor) -> torch.Tensor:
        if support.ndim != 4 or support.shape[0] < 1 or support.shape[1] < 1:
            raise ValueError("expected nonempty [episodes, shots, channels, time]")
        episodes, shots, channels, samples = support.shape
        embeddings = self.encoder(support.reshape(episodes * shots, channels, samples))
        summary = embeddings.reshape(episodes, shots, self.prompt_dim).mean(dim=1)
        return cast(
            torch.Tensor,
            self.generator(summary).reshape(episodes, self.prompt_count, self.prompt_dim),
        )
