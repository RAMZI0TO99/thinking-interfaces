from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch

import torch
from torch import nn

from evaluation.labram_parity import (
    capture_stages,
    compare_stages,
    load_reference,
    reference_channel_order,
    reference_state,
    tensor_check,
    verified_bytes,
)


class ForwardParityTests(unittest.TestCase):
    def test_comparison_rejects_corruption_nonfinite_and_broadcasting(self) -> None:
        values = torch.arange(6, dtype=torch.float32).reshape(2, 3)
        self.assertTrue(tensor_check(values, values.clone(), atol=1e-5, rtol=1e-4)["exact"])
        for bad in (
            values + 1,
            values[:1],
            values.double(),
            values * float("nan"),
            values * float("inf"),
            torch.empty(0),
        ):
            with self.subTest(shape=bad.shape, dtype=bad.dtype):
                self.assertFalse(tensor_check(bad, values, atol=1e-5, rtol=1e-4)["passed"])
        for actual, expected in (
            ({}, {}),
            ({"cls": values}, {}),
            ({"cls": values}, {"patch": values}),
        ):
            with (
                self.subTest(actual=list(actual), expected=list(expected)),
                self.assertRaises(ValueError),
            ):
                compare_stages(actual, expected, atol=1e-5, rtol=1e-4)

    def test_weight_mapping_is_bijective_and_never_reshapes(self) -> None:
        tensor = torch.ones(1, 2)
        safe = {"position_embedding": tensor, "blocks.0.mlp.0.weight": tensor}
        expected = {"pos_embed": tensor, "blocks.0.mlp.fc1.weight": tensor}
        mapped = reference_state(safe, expected)
        self.assertIs(mapped["pos_embed"], tensor)
        for bad in (
            {**safe, "pos_embed": tensor},
            {"unknown": tensor},
            {**safe, "position_embedding": tensor.reshape(2, 1)},
            {**safe, "position_embedding": tensor.double()},
        ):
            with self.subTest(keys=list(bad)), self.assertRaises(ValueError):
                reference_state(bad, expected)

    def test_reference_bytes_and_literal_table_fail_closed(self) -> None:
        payload = b"reference"
        with patch.object(Path, "read_bytes", return_value=payload):
            self.assertEqual(
                verified_bytes(Path("reference.py"), hashlib.sha256(payload).hexdigest()), payload
            )
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verified_bytes(Path("reference.py"), "0" * 64)
        names = [f"C{i}" for i in range(136)]
        self.assertEqual(
            reference_channel_order(f"standard_1020 = {names!r}".encode()), tuple(names)
        )
        for code in (
            "standard_1020 = []",
            "standard_1020 = ['C3'] * 136",
            "standard_1020 = dangerous_function()",
            "unrelated = []",
            f"standard_1020 = {names!r}\nstandard_1020 = {names!r}",
        ):
            with self.subTest(code=code[:50]), self.assertRaises(ValueError):
                reference_channel_order(code.encode())

    def test_loader_preserves_forward_and_fails_on_unexpected_helpers(self) -> None:
        source = (
            "from timm.models.layers import drop_path, to_2tuple, trunc_normal_\n"
            "from timm.models.registry import register_model\n"
            "class Probe:\n"
            "    def forward(self, x): return x + 7\n"
        )
        for size in ("base", "large", "huge"):
            source += f"@register_model\ndef labram_{size}_patch200_200(): return Probe()\n"
        reference = load_reference(source.encode(), "fixture.py")
        self.assertEqual(reference.labram_base_patch200_200().forward(2), 9)
        with self.assertRaises(RuntimeError):
            reference.drop_path(torch.ones(2), 0.1, True)
        with self.assertRaises(ValueError):
            load_reference(source.replace("to_2tuple, ", "").encode(), "bad.py")

    def test_hooks_capture_real_calls_and_are_removed_on_failure(self) -> None:
        model = nn.Module()
        model.patch_embed = nn.Identity()
        model.pos_drop = nn.Identity()
        model.blocks = nn.ModuleList([nn.Identity() for _ in range(12)])
        model.norm = nn.Identity()

        def forward():
            x = model.pos_drop(model.patch_embed(torch.ones(2, 4, 3)))
            for block in model.blocks:
                x = block(x)
            return model.norm(x)

        stages = capture_stages(model, forward)
        self.assertEqual(len(stages), 17)
        torch.testing.assert_close(stages["cls"], torch.ones(2, 3))

        def broken():
            model.patch_embed(torch.ones(2, 3))
            raise RuntimeError("forward failed")

        with self.assertRaisesRegex(RuntimeError, "forward failed"):
            capture_stages(model, broken)
        self.assertTrue(all(not module._forward_hooks for module in model.modules()))
        with self.assertRaises(ValueError):
            capture_stages(model, lambda: torch.ones(2, 4, 3))
        self.assertTrue(all(not module._forward_hooks for module in model.modules()))
