from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / ".cache" / "huggingface"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from encoder.labram import (  # noqa: E402
    LaBraMClassifier,
    configure_trainable_depth,
    electrode_embedding_indices,
    load_pretrained_labram,
)


def main() -> None:
    artifact = np.load(
        PROJECT_ROOT / "data" / "processed" / "bci_iv_2a" / "profile_b" / "subject_01.npz"
    )
    signals = np.asarray(artifact["signals"][:2], dtype=np.float32)
    channel_names = tuple(str(value) for value in artifact["channel_names"])
    backbone, report = load_pretrained_labram(
        samples=signals.shape[2],
        channels=signals.shape[1],
        source_checkpoint=PROJECT_ROOT / "checkpoints" / "labram-base.pth",
    )
    model = LaBraMClassifier(
        backbone,
        classes=len(set(artifact["labels"].tolist())),
        channel_names=channel_names,
    )
    model.eval()
    with torch.inference_mode():
        logits = model(torch.from_numpy(signals))
    output = asdict(report)
    output["real_epoch_input_shape"] = list(signals.shape)
    output["logit_shape"] = list(logits.shape)
    output["finite_logits"] = bool(torch.isfinite(logits).all())
    indices = electrode_embedding_indices(channel_names)
    if backbone.position_embedding is None:
        raise RuntimeError("pretrained LaBraM has no spatial position embedding")
    embedding_norms = backbone.position_embedding[0, list(indices)].detach().norm(dim=1)
    output["electrode_embedding_norm_min"] = float(embedding_norms.min())
    output["electrode_embedding_norm_max"] = float(embedding_norms.max())
    output["finite_electrode_embedding_norms"] = bool(torch.isfinite(embedding_norms).all())
    output["trainable_parameters_by_depth"] = {
        str(depth): configure_trainable_depth(model, depth)
        for depth in (0, 4, 8, 12, "all")
    }
    result = PROJECT_ROOT / "runs" / "labram_ready_state.json"
    result.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
