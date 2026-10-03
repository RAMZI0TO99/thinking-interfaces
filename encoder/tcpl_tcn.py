"""TCPL's TCN dimensions under an explicit local length-preserving contract.

This component is not a verified author implementation or a complete TCPL model.
The reference inventory is configs/phase2/tcpl_reference.toml. Stride, activation
ordering, biases and initialization below are local reconstruction choices.
"""

from __future__ import annotations

from typing import cast

import torch
from torch import nn
from torch.nn import functional as F


class _CausalConv1d(nn.Conv1d):
    """Kernel-three convolution with left-only padding and unit stride."""

    def __init__(self, in_channels: int, out_channels: int, dilation: int) -> None:
        super().__init__(in_channels, out_channels, kernel_size=3, dilation=dilation)
        self.left_padding = 2 * dilation

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return super().forward(F.pad(inputs, (self.left_padding, 0)))


class _ResidualTCNBlock(nn.Module):
    """Two (causal conv -> ReLU -> dropout) stages, then ReLU(branch + skip)."""

    def __init__(self, in_channels: int, out_channels: int, dilation: int) -> None:
        super().__init__()
        self.conv1 = _CausalConv1d(in_channels, out_channels, dilation)
        self.conv2 = _CausalConv1d(out_channels, out_channels, dilation)
        self.relu = nn.ReLU()
        self.dropout1 = nn.Dropout(0.1)
        self.dropout2 = nn.Dropout(0.1)
        self.skip = (
            nn.Identity()
            if in_channels == out_channels
            else nn.Conv1d(in_channels, out_channels, kernel_size=1)
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        hidden = self.dropout1(self.relu(self.conv1(inputs)))
        hidden = self.dropout2(self.relu(self.conv2(hidden)))
        return cast(torch.Tensor, self.relu(hidden + self.skip(inputs)))


class TCPLCausalTCN(nn.Module):
    """Map floating [batch, channels, time] to [batch, time, 64].

    Four residual blocks use widths 64/64/128/128 and dilations 1/2/4/8.
    All convolutions have stride one and bias; zero padding is only on the left.
    There is no temporal pooling, normalization or persistent streaming state.
    The final Linear(128, 64) acts independently at each time point. The maximum
    receptive field is 61 samples (current sample plus 60 past samples).

    Local initialization: Conv1d defaults; Xavier-uniform output weight and zero
    output bias. Normal PyTorch train/eval behavior controls elementwise dropout.
    Calls represent independent complete sequences, not stateful stream chunks.
    """

    output_dim = 64
    receptive_field_samples = 61

    def __init__(self, input_channels: int) -> None:
        super().__init__()
        if type(input_channels) is not int or input_channels < 1:
            raise ValueError("input_channels must be a positive integer")
        self.input_channels = input_channels
        blocks = []
        width = input_channels
        for out_channels, dilation in zip((64, 64, 128, 128), (1, 2, 4, 8), strict=True):
            blocks.append(_ResidualTCNBlock(width, out_channels, dilation))
            width = out_channels
        self.blocks = nn.Sequential(*blocks)
        self.projection = nn.Linear(128, self.output_dim)
        nn.init.xavier_uniform_(self.projection.weight)
        nn.init.zeros_(self.projection.bias)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if (
            inputs.ndim != 3
            or inputs.shape[0] < 1
            or inputs.shape[1] != self.input_channels
            or inputs.shape[2] < 1
            or not inputs.is_floating_point()
        ):
            raise ValueError("expected nonempty floating [batch, input_channels, time]")
        hidden = self.blocks(inputs)
        return cast(torch.Tensor, self.projection(hidden.transpose(1, 2)))
