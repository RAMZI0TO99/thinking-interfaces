"""Offline, bounded CPU parity against pinned official LaBraM source and safe weights."""

from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
import platform
from dataclasses import asdict
from datetime import UTC, datetime
from functools import partial
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

from core.config import config_digest, load_toml
from core.provenance import capture_source
from data.runtime import configure_scientific_runtime

configure_scientific_runtime()

import torch  # noqa: E402
from braindecode.models import Labram  # type: ignore[import-untyped]  # noqa: E402
from braindecode.models.labram import (  # type: ignore[import-untyped]  # noqa: E402
    LABRAM_CHANNEL_ORDER,
)
from safetensors.torch import load_file  # noqa: E402

from encoder.labram import configure_pretrained_sequence, electrode_embedding_indices  # noqa: E402
from evaluation.labram_parity import (  # noqa: E402
    capture_stages,
    compare_stages,
    load_reference,
    reference_channel_order,
    reference_state,
    state_digest,
    tensor_check,
    verified_bytes,
)
from evaluation.phase2_records import envelope, write_once  # noqa: E402
from scripts.audit_phase2_protocol import file_digest, inside  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/phase2/forward_parity.toml"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config: dict[str, Any] = load_toml(args.config)
    settings, pinned = config["parity"], config["reference"]
    if (
        settings["purpose"] != "bounded_cpu_reference_forward_parity_not_downstream_reproduction"
        or settings["device"] != "cpu"
        or not 1 <= settings["threads"] <= 2
        or settings["synthetic_samples"] != [200, 400, 800, 3000]
        or len(settings["synthetic_channels"]) != 3
    ):
        raise ValueError("this command is restricted to the bounded engineering protocol")
    output_root = inside(root, settings["output_root"])
    if not output_root.is_relative_to((root / "runs/phase2").resolve()):
        raise ValueError("output must stay inside runs/phase2")
    torch.set_num_threads(settings["threads"])
    torch.manual_seed(settings["seed"])
    torch.use_deterministic_algorithms(True)
    source = capture_source(root)
    ref_dir = inside(root, pinned["directory"])
    ref_bytes = {
        name: verified_bytes(inside(ref_dir, name), digest)
        for name, digest in pinned["files"].items()
    }
    # Only the reviewed, hash-verified model file is executed. Upstream utils is
    # parsed as data; its pickle/data-loader/distributed-runtime code is never imported.
    module = load_reference(
        ref_bytes["modeling_finetune.py"], str(ref_dir / "modeling_finetune.py")
    )
    channel_order = reference_channel_order(ref_bytes["utils.py"])
    # The upstream utility lists 136 names, but this checkpoint has only 128
    # electrode positions. Its eight trailing bipolar names are unsupported.
    canonical_equal = tuple(n.upper() for n in channel_order[:128]) == tuple(
        n.upper() for n in LABRAM_CHANNEL_ORDER
    )
    if not canonical_equal:
        raise ValueError("installed/reference canonical channel tables differ")
    channel_lookup = {name.upper(): i + 1 for i, name in enumerate(channel_order[:128])}
    checkpoint_config: dict[str, Any] = load_toml(inside(root, settings["checkpoint_config"]))
    safe = checkpoint_config["safe_conversion"]
    weights_path = inside(root, safe["path"])
    verified_bytes(weights_path, safe["sha256"])
    model_path = inside(root, settings["model_config"])
    model_config = json.loads(verified_bytes(model_path, settings["model_config_sha256"]))
    model_config.pop("braindecode_version", None)
    base = Labram(**model_config).eval().requires_grad_(False)
    weights = load_file(str(weights_path), device="cpu")
    base.load_state_dict(weights, strict=True)
    reference = (
        module.labram_base_patch200_200(
            num_classes=0, EEG_size=800, init_values=0.1, use_mean_pooling=False, qkv_bias=False
        )
        .eval()
        .requires_grad_(False)
    )
    mapped = reference_state(weights, reference.state_dict())
    reference.load_state_dict(mapped, strict=True)
    reference_before, base_before = state_digest(reference), state_digest(base)
    tolerances = {"atol": settings["atol"], "rtol": settings["rtol"]}
    cases: list[dict[str, Any]] = []

    def run_case(
        name: str, values: torch.Tensor, names: tuple[str, ...]
    ) -> dict[str, torch.Tensor]:
        indices = [0, *(channel_lookup[n.upper()] for n in names)]
        if tuple(indices[1:]) != electrode_embedding_indices(names):
            raise ValueError("installed/reference named-channel indices differ")
        local = configure_pretrained_sequence(copy.deepcopy(base), samples=values.shape[-1])
        local.eval().requires_grad_(False)
        before = state_digest(local)
        values_before = values.clone()
        local_stages = capture_stages(
            local, lambda: local(values, ch_names=list(names), return_features=True)
        )
        upstream_stages = capture_stages(
            reference,
            lambda: reference(
                values.reshape(values.shape[0], values.shape[1], -1, 200),
                input_chans=indices,
                return_all_tokens=True,
            ),
        )
        checks = compare_stages(local_stages, upstream_stages, **tolerances)
        unchanged = before == state_digest(local) and torch.equal(values, values_before)
        cases.append(
            {
                "name": name,
                "input_shape": list(values.shape),
                "channel_names": names,
                "reference_indices_including_cls": indices,
                "input_sha256": hashlib.sha256(values.numpy().tobytes()).hexdigest(),
                "stages": checks,
                "model_and_input_unchanged": unchanged,
                "passed": unchanged and all(check["passed"] for check in checks.values()),
            }
        )
        return local_stages

    for samples in settings["synthetic_samples"]:
        run_case(
            f"synthetic_{samples}",
            torch.randn(2, 3, samples) * 0.1,
            tuple(settings["synthetic_channels"]),
        )
    real_path, manifest_path = (
        inside(root, settings[key]) for key in ("real_input", "real_manifest")
    )
    real_hash, manifest_hash = file_digest(real_path), file_digest(manifest_path)
    manifest = json.loads(manifest_path.read_text("utf-8"))
    with np.load(real_path, allow_pickle=False) as archive:
        # Only signals/names are used. Labels, scores and target adaptation are excluded.
        values = torch.from_numpy(archive["signals"][:2].copy())
        names = tuple(str(name) for name in archive["channel_names"])
    if (
        values.shape != (2, 22, 800)
        or values.dtype != torch.float32
        or not torch.isfinite(values).all()
        or list(names) != manifest["channel_names"]
        or manifest["sampling_rate_hz"] != 200
        or manifest["artifact_kind"] != "profile_b"
    ):
        raise ValueError("unexpected real-input artifact contract")
    real_stages = run_case("real_bci_subject01_first_two_unlabelled", values, names)
    order = torch.arange(len(names) - 1, -1, -1)
    permuted = run_case(
        "real_joint_channel_permutation",
        values[:, order].contiguous(),
        tuple(names[i] for i in order.tolist()),
    )
    invariance = {
        "cls": tensor_check(permuted["cls"], real_stages["cls"], **tolerances),
        "patch_tokens": tensor_check(
            permuted["patch_tokens"].reshape(2, 22, 4, 200)[:, order].reshape(2, 88, 200),
            real_stages["patch_tokens"],
            **tolerances,
        ),
    }
    # Negative controls: a mapping error and a deliberately corrupted output must
    # be detected with the SAME tolerances used for parity acceptance.
    wrong_names = run_case(
        "negative_control_names_only_permutation", values, tuple(names[i] for i in order.tolist())
    )
    negative_controls = {
        "wrong_channel_mapping_detected": not tensor_check(
            wrong_names["cls"], real_stages["cls"], **tolerances
        )["passed"],
        "perturbed_output_detected": not tensor_check(
            real_stages["cls"] + 1, real_stages["cls"], **tolerances
        )["passed"],
    }
    # Supplemental precision diagnosis, not a replacement for the recorded
    # float32 criterion. All float32 tolerances and failed checks are retained.
    local64 = configure_pretrained_sequence(copy.deepcopy(base).double(), samples=800)
    upstream64 = copy.deepcopy(reference).double()
    local64.eval().requires_grad_(False)
    before64 = (state_digest(local64), state_digest(upstream64))
    double_stages = []
    double_parity = []
    tolerance64 = {
        "atol": settings["float64_diagnostic_atol"],
        "rtol": settings["float64_diagnostic_rtol"],
    }
    for signals64, names64 in (
        (values.double(), names),
        (values[:, order].contiguous().double(), tuple(names[i] for i in order.tolist())),
    ):
        local_outputs = capture_stages(
            local64, partial(local64, signals64, ch_names=list(names64), return_features=True)
        )
        ref_outputs = capture_stages(
            upstream64,
            partial(
                upstream64,
                signals64.reshape(2, 22, 4, 200),
                input_chans=[0, *(channel_lookup[n.upper()] for n in names64)],
                return_all_tokens=True,
            ),
        )
        double_stages.append(local_outputs)
        double_parity.append(compare_stages(local_outputs, ref_outputs, **tolerance64))
    double_invariance = {}
    for name, output in double_stages[1].items():
        if name == "cls":
            reordered = output
        elif name in ("patch_embed", "patch_tokens"):
            reordered = output.reshape(2, 22, 4, 200)[:, order].reshape(2, 88, 200)
        else:
            reordered = torch.cat(
                (output[:, :1], output[:, 1:].reshape(2, 22, 4, 200)[:, order].reshape(2, 88, 200)),
                dim=1,
            )
        double_invariance[name] = tensor_check(reordered, double_stages[0][name], **tolerance64)
    diagnostic64 = {
        "tolerances": tolerance64,
        "local_reference_parity": double_parity,
        "joint_permutation_invariance": double_invariance,
        "state_unchanged": before64 == (state_digest(local64), state_digest(upstream64)),
        "passed": all(check["passed"] for check in double_invariance.values())
        and all(check["passed"] for stages in double_parity for check in stages.values()),
    }
    unchanged = (
        state_digest(reference) == reference_before
        and state_digest(base) == base_before
        and file_digest(real_path) == real_hash
        and file_digest(manifest_path) == manifest_hash
        and file_digest(weights_path) == safe["sha256"]
        and file_digest(model_path) == settings["model_config_sha256"]
        and capture_source(root).source_sha256 == source.source_sha256
        and all(file_digest(ref_dir / name) == digest for name, digest in pinned["files"].items())
        and diagnostic64["state_unchanged"]
    )
    reference_parity = (
        unchanged and all(case["passed"] for case in cases) and all(negative_controls.values())
    )
    permutation32 = all(check["passed"] for check in invariance.values())
    all_checks = reference_parity and permutation32 and diagnostic64["passed"]
    installed_files = {
        inspect.getfile(type(obj))
        for obj in (base, base.blocks[0], base.blocks[0].attn, base.patch_embed[1])
    }
    payload = {
        "purpose": settings["purpose"],
        "config": config,
        "source": asdict(source),
        "checkpoint_sha256": safe["sha256"],
        "mapped_tensors": len(mapped),
        "mapped_elements": sum(t.numel() for t in mapped.values()),
        "reference_forward_settings": {
            "use_mean_pooling": False,
            "qkv_bias": False,
            "num_classes": 0,
            "init_values": 0.1,
        },
        "reference_loader_adjustments": {
            "forward_definitions_changed": False,
            "timm_factory_registration_removed": True,
            "initializer": "torch.nn.init.trunc_normal_; all tensors then strictly loaded",
            "unused_timm_helpers": "drop_path/to_2tuple raise if called",
            "upstream_training_environment_reproduced": False,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {p: version(p) for p in ("torch", "braindecode", "einops", "safetensors")},
            "installed_source_hashes": {p: file_digest(Path(p)) for p in sorted(installed_files)},
        },
        "real_input": {
            "path": settings["real_input"],
            "sha256": real_hash,
            "manifest_sha256": manifest_hash,
            "rows": [0, 1],
            "labels_used": False,
        },
        "canonical_128_channel_order_equal": canonical_equal,
        "upstream_names_without_checkpoint_positions": channel_order[128:],
        "cases": cases,
        "joint_permutation_invariance": invariance,
        "float32_joint_permutation_invariance_verified": permutation32,
        "float64_precision_diagnostic": diagnostic64,
        "all_checks_passed": all_checks,
        "negative_controls": negative_controls,
        "source_and_inputs_unchanged": unchanged,
        "reference_forward_parity_verified": reference_parity,
        "external_downstream_reproduction_verified": False,
        "scientific_gate_approval": False,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    receipt_path = (
        output_root / config_digest(config) / source.source_sha256 / stamp / "receipt.json"
    )
    write_once(receipt_path, envelope("engineering_smoke", payload), output_root=output_root)
    print(
        json.dumps(
            {
                "receipt": str(receipt_path),
                "reference_forward_parity_verified": reference_parity,
                "float32_joint_permutation_invariance_verified": permutation32,
                "float64_diagnostic_passed": diagnostic64["passed"],
                "all_checks_passed": all_checks,
                "cases": len(cases),
                "scientific_result": False,
            },
            indent=2,
        )
    )
    return 0 if all_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
