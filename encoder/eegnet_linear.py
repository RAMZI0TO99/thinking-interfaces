"""Exact EEGNet convolutional-classifier to linear-head conversion."""

from __future__ import annotations

from typing import Any, cast

import torch
from torch import nn


class EEGNetLinearHead(nn.Module):
    def __init__(self, feature_extractor: nn.Module, head: nn.Linear) -> None:
        super().__init__()
        self.feature_extractor = feature_extractor
        self.flatten = nn.Flatten(start_dim=1)
        self.head = head

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        features = cast(torch.Tensor, self.feature_extractor(inputs))
        return cast(torch.Tensor, self.head(self.flatten(features)))


def linearize_eegnet_classifier(model: nn.Module, example: torch.Tensor) -> EEGNetLinearHead:
    """Replace EEGNet's final full-window Conv2d with an equivalent Linear layer."""

    children = list(model.children())
    if len(children) < 2:
        raise ValueError("model does not expose an EEGNet-style final layer")
    final_layer: Any = getattr(model, "final_layer", None)
    convolution = getattr(final_layer, "conv_classifier", None)
    if not isinstance(convolution, nn.Conv2d):
        raise ValueError("EEGNet final convolution was not found")
    feature_extractor = nn.Sequential(*children[:-1])
    with torch.inference_mode():
        features = cast(torch.Tensor, feature_extractor(example))
    flattened = int(features[0].numel())
    if convolution.weight.numel() != convolution.out_channels * flattened:
        raise ValueError("final convolution is not equivalent to one full-window linear head")
    head = nn.Linear(
        flattened,
        convolution.out_channels,
        bias=convolution.bias is not None,
        device=convolution.weight.device,
        dtype=convolution.weight.dtype,
    )
    with torch.no_grad():
        head.weight.copy_(convolution.weight.reshape(convolution.out_channels, flattened))
        if head.bias is not None and convolution.bias is not None:
            head.bias.copy_(convolution.bias)
    return EEGNetLinearHead(feature_extractor, head)
