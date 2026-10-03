"""Bounded offline CPU check using the exact safe LaBraM checkpoint and synthetic inputs."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.config import config_digest, load_toml
from core.provenance import capture_source
from data.runtime import configure_scientific_runtime

configure_scientific_runtime()

import torch  # noqa: E402
from braindecode.models import Labram  # type: ignore[import-untyped]  # noqa: E402
from safetensors.torch import load_file  # noqa: E402
from torch import nn  # noqa: E402

from adaptation.labram_lora import inject_labram_qkv_lora  # noqa: E402
from encoder.labram import LaBraMClassifier, configure_pretrained_sequence  # noqa: E402
from evaluation.phase2_records import envelope, write_once  # noqa: E402
from scripts.audit_phase2_protocol import file_digest, inside  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/phase2/lora_smoke.toml"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config: dict[str, Any] = load_toml(args.config)
    settings = config["smoke"]
    if (
        settings["device"] != "cpu"
        or settings["optimizer"] != "sgd"
        or settings["normalization_policy"] != "eval_mode_all_source_state_frozen_except_lora"
        or settings["purpose"] != "bounded_cpu_engineering_smoke_not_scientific_experiment"
    ):
        raise ValueError("this command is restricted to the declared CPU engineering protocol")
    torch.set_num_threads(settings["threads"])
    torch.manual_seed(settings["seed"])
    checkpoint_config: dict[str, Any] = load_toml(inside(root, settings["checkpoint_config"]))
    safe = checkpoint_config["safe_conversion"]
    weights_path = inside(root, safe["path"])
    if file_digest(weights_path) != safe["sha256"]:
        raise ValueError("safe checkpoint hash mismatch")
    model_path = inside(root, settings["model_config"])
    model_settings = json.loads(model_path.read_text("utf-8"))
    # This is Hub metadata, stripped by Braindecode's own from_pretrained path.
    checkpoint_braindecode_version = model_settings.pop("braindecode_version", None)
    source = capture_source(root)
    backbone = Labram(**model_settings)
    backbone.load_state_dict(load_file(str(weights_path), device="cpu"), strict=True)
    configure_pretrained_sequence(backbone, samples=settings["samples"])
    base = LaBraMClassifier(
        backbone, classes=settings["classes"], channel_names=tuple(settings["channel_names"])
    )
    base.eval().requires_grad_(False)
    original = {name: tensor.detach().clone() for name, tensor in base.state_dict().items()}
    adapted = copy.deepcopy(base)
    report = inject_labram_qkv_lora(
        adapted,
        target_modules=tuple(settings["target_modules"]),
        rank=settings["rank"],
        alpha=settings["alpha"],
    )
    support = (
        torch.randn(
            settings["support_examples"], len(settings["channel_names"]), settings["samples"]
        )
        * settings["synthetic_input_scale"]
    )
    query = (
        torch.randn(settings["query_examples"], len(settings["channel_names"]), settings["samples"])
        * settings["synthetic_input_scale"]
    )
    labels = torch.arange(settings["support_examples"]) % settings["classes"]
    with torch.inference_mode():
        before = base(query).clone()
        initial = adapted(query).clone()
    torch.testing.assert_close(before, initial, rtol=0, atol=0)
    optimizer = torch.optim.SGD(
        [p for p in adapted.parameters() if p.requires_grad], lr=settings["learning_rate"]
    )
    losses = []
    criterion = nn.CrossEntropyLoss()
    for _ in range(settings["steps"]):
        optimizer.zero_grad()
        loss = criterion(adapted(support), labels)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    state_before_query = {
        name: value.detach().clone() for name, value in adapted.state_dict().items()
    }
    with torch.inference_mode():
        after = adapted(query)
    for name, value in base.state_dict().items():
        torch.testing.assert_close(value, original[name], rtol=0, atol=0)
    for name, value in adapted.state_dict().items():
        torch.testing.assert_close(value, state_before_query[name], rtol=0, atol=0)
        if ".lora_" not in name:
            canonical = name.replace(".parametrizations.weight.original", ".weight")
            torch.testing.assert_close(value, original[canonical], rtol=0, atol=0)
    delta = float((after - before).abs().max())
    if not torch.isfinite(after).all() or delta <= 0:
        raise ValueError("support updates did not produce finite changed query outputs")
    if capture_source(root).source_sha256 != source.source_sha256:
        raise ValueError("source changed during smoke")
    payload = {
        "config": config,
        "source": asdict(source),
        "checkpoint_sha256": safe["sha256"],
        "model_config_sha256": file_digest(model_path),
        "checkpoint_braindecode_version": checkpoint_braindecode_version,
        "torch_version": torch.__version__,
        "braindecode_source_sha256": file_digest(
            root / ".venv/Lib/site-packages/braindecode/models/labram.py"
        ),
        "injection": asdict(report),
        "support_losses": losses,
        "query_maximum_logit_change": delta,
        "initial_exact_identity": True,
        "source_state_unchanged": True,
        "frozen_adapted_state_unchanged": True,
        "query_state_unchanged": True,
        "synthetic_data_only": True,
        "external_forward_parity_verified": False,
        "scientific_gate_approval": False,
        "query_input_sha256": hashlib.sha256(query.numpy().tobytes()).hexdigest(),
    }
    output_root = inside(root, settings["output_root"])
    if not output_root.is_relative_to((root / "runs/phase2").resolve()):
        raise ValueError("smoke output must stay inside runs/phase2")
    output = output_root / config_digest(config) / source.source_sha256 / "receipt.json"
    write_once(output, envelope("engineering_smoke", payload), output_root=output_root)
    print(
        json.dumps(
            {
                "receipt": str(output),
                "maximum_logit_change": delta,
                "passed": True,
                "scientific_result": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
