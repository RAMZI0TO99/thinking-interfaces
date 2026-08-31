"""Safe LaBraM loading, sequence adaptation, and downstream classification."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

from data.runtime import configure_scientific_runtime

configure_scientific_runtime()

import torch  # noqa: E402
from braindecode.models import Labram  # type: ignore[import-untyped]  # noqa: E402
from braindecode.models.labram import (  # type: ignore[import-untyped]  # noqa: E402
    LABRAM_CHANNEL_ORDER,
)
from torch import nn  # noqa: E402


@dataclass(frozen=True, slots=True)
class LaBraMLoadReport:
    hub_model: str
    source_checkpoint_sha256: str | None
    source_checkpoint_bytes: int | None
    loaded_parameters: int
    configured_parameters: int
    expected_plan_parameters: int
    parameter_count_matches_plan: bool
    channels: int
    samples: int
    patches: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def electrode_embedding_indices(channel_names: tuple[str, ...]) -> tuple[int, ...]:
    """Map names to LaBraM positions; zero is reserved for the CLS token."""

    lookup = {str(name).upper(): index + 1 for index, name in enumerate(LABRAM_CHANNEL_ORDER)}
    try:
        indices = tuple(lookup[name.upper()] for name in channel_names)
    except KeyError as error:
        raise ValueError(
            f"channel is absent from LaBraM's canonical montage: {error.args[0]}"
        ) from error
    if len(set(indices)) != len(indices):
        raise ValueError("channel mapping must be one-to-one")
    return indices


def configure_pretrained_sequence(model: Labram, *, samples: int) -> Labram:
    """Crop only temporal embeddings so a pretrained model accepts shorter epochs."""

    segment = model.patch_embed[0]
    patch_size = int(segment.patch_size)
    if samples < patch_size or samples % patch_size:
        raise ValueError("samples must be a positive multiple of the pretrained patch size")
    patches = samples // patch_size
    available = int(model.temporal_embedding.shape[1] - 1)
    if patches > available:
        raise ValueError(f"requested {patches} patches but checkpoint provides only {available}")
    segment.n_times = samples
    segment.n_patchs = patches
    segment.patch_shape = (1, patches)
    model.temporal_embedding = nn.Parameter(
        model.temporal_embedding[:, : patches + 1].detach().clone()
    )
    return model


def load_pretrained_labram(
    *,
    samples: int,
    channels: int,
    hub_model: str = "braindecode/labram-pretrained",
    source_checkpoint: Path | None = None,
    expected_plan_parameters: int = 5_822_770,
) -> tuple[Labram, LaBraMLoadReport]:
    """Load the safe Braindecode checkpoint and adapt its temporal sequence."""

    model = cast(Labram, Labram.from_pretrained(hub_model))
    loaded_parameters = sum(value.numel() for value in model.parameters())
    configure_pretrained_sequence(model, samples=samples)
    configured_parameters = sum(value.numel() for value in model.parameters())
    source_hash = file_sha256(source_checkpoint) if source_checkpoint is not None else None
    source_bytes = source_checkpoint.stat().st_size if source_checkpoint is not None else None
    report = LaBraMLoadReport(
        hub_model,
        source_hash,
        source_bytes,
        loaded_parameters,
        configured_parameters,
        expected_plan_parameters,
        loaded_parameters == expected_plan_parameters,
        channels,
        samples,
        samples // int(model.patch_embed[0].patch_size),
    )
    return model, report


class LaBraMClassifier(nn.Module):
    def __init__(self, backbone: Labram, *, classes: int, channel_names: tuple[str, ...]) -> None:
        super().__init__()
        if classes < 2:
            raise ValueError("classes must be at least two")
        electrode_embedding_indices(channel_names)
        self.backbone = backbone
        self.channel_names = channel_names
        self.head = nn.Linear(int(backbone.embed_dim), classes)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        outputs: dict[str, torch.Tensor] = self.backbone(
            inputs,
            ch_names=list(self.channel_names),
            return_features=True,
        )
        return cast(torch.Tensor, self.head(outputs["cls_token"]))


def configure_trainable_depth(model: LaBraMClassifier, depth: int | str) -> int:
    """Freeze the backbone except the final N blocks; always train the head."""

    blocks = model.backbone.blocks
    if depth == "all":
        selected = len(blocks)
        include_non_blocks = True
    elif isinstance(depth, int) and 0 <= depth <= len(blocks):
        selected = depth
        include_non_blocks = False
    else:
        raise ValueError("depth must be 0..number of blocks or 'all'")
    model.backbone.requires_grad_(include_non_blocks)
    if not include_non_blocks:
        for block in blocks[len(blocks) - selected :]:
            block.requires_grad_(True)
    model.head.requires_grad_(True)
    return sum(value.numel() for value in model.parameters() if value.requires_grad)


def mask_electrodes_by_name(
    signals: NDArray[np.floating],
    channel_names: tuple[str, ...],
    masked_names: tuple[str, ...],
) -> NDArray[np.float32]:
    """Zero named electrodes without relying on dataset-specific indices."""

    values = np.asarray(signals, dtype=np.float32)
    if values.ndim < 2 or values.shape[-2] != len(channel_names):
        raise ValueError("channel_names must match the penultimate signal dimension")
    unknown = set(masked_names) - set(channel_names)
    if unknown:
        raise ValueError(f"cannot mask unknown electrodes: {sorted(unknown)}")
    result = values.copy()
    for name in masked_names:
        result[..., channel_names.index(name), :] = 0.0
    return result
