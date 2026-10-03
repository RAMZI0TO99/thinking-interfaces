from __future__ import annotations

import copy
import unittest

import torch
from torch import nn
from torch.nn.utils import parametrize

from adaptation.labram_lora import inject_labram_qkv_lora
from data.runtime import configure_scientific_runtime


class AttentionFixture(nn.Module):
    """The installed attention implementation, not a substitute Linear forward."""

    def __init__(self) -> None:
        configure_scientific_runtime()
        from braindecode.models.labram import _Attention

        super().__init__()
        block = nn.Module()
        block.attn = _Attention(dim=12, num_heads=3, qkv_bias=True, qk_norm=nn.LayerNorm)
        self.blocks = nn.ModuleList([block])

    def forward(self, inputs):
        return self.blocks[0].attn(inputs)


class LaBraMQKVLoRATests(unittest.TestCase):
    def test_actual_attention_has_initial_identity_and_support_changes_effective_weight(
        self,
    ) -> None:
        torch.manual_seed(9)
        base = AttentionFixture().eval().requires_grad_(False)
        source_state = {n: x.clone() for n, x in base.state_dict().items()}
        adapted = copy.deepcopy(base)
        support, query = torch.randn(2, 5, 12), torch.randn(2, 5, 12)
        before = base(query).detach().clone()
        report = inject_labram_qkv_lora(
            adapted, target_modules=("blocks.0.attn.qkv",), rank=3, alpha=6
        )
        self.assertEqual(report.adapter_parameters, 3 * (12 + 36))
        torch.testing.assert_close(adapted(query), before, rtol=0, atol=0)
        layer = adapted.blocks[0].attn.qkv
        original = layer.parametrizations.weight.original.detach().clone()
        optimizer = torch.optim.SGD([p for p in adapted.parameters() if p.requires_grad], lr=0.2)
        adapter = layer.parametrizations.weight[0]
        for _ in range(3):
            optimizer.zero_grad()
            loss = (adapted(support) - 1).square().mean()
            loss.backward()
            self.assertIsNotNone(adapter.lora_b.grad)
            self.assertGreater(adapter.lora_b.grad.abs().sum().item(), 0)
            optimizer.step()
        self.assertGreater(adapter.lora_a.grad.abs().sum().item(), 0)
        torch.testing.assert_close(layer.parametrizations.weight.original, original, rtol=0, atol=0)
        self.assertFalse(torch.equal(layer.weight, original))
        self.assertFalse(torch.equal(adapted(query), before))
        query_state = {n: x.clone() for n, x in adapted.state_dict().items()}
        with torch.inference_mode():
            adapted(query)
        for name, value in source_state.items():
            torch.testing.assert_close(base.state_dict()[name], value, rtol=0, atol=0)
        for name, value in query_state.items():
            torch.testing.assert_close(adapted.state_dict()[name], value, rtol=0, atol=0)
        # Every original tensor remains frozen, including q/v biases and norm buffers.
        mapped = {
            n.replace(".parametrizations.weight.original", ".weight"): p
            for n, p in adapted.named_parameters()
            if "lora_" not in n
        }
        for name, value in mapped.items():
            self.assertFalse(value.requires_grad)
            torch.testing.assert_close(value, source_state[name], rtol=0, atol=0)

    def test_state_dict_round_trip_reconstructs_parametrization_before_loading(self) -> None:
        first, second = AttentionFixture(), AttentionFixture()
        for model in (first, second):
            inject_labram_qkv_lora(model, target_modules=("blocks.0.attn.qkv",), rank=3, alpha=6)
        first.blocks[0].attn.qkv.parametrizations.weight[0].lora_b.data.fill_(0.1)
        second.load_state_dict(first.state_dict(), strict=True)
        inputs = torch.randn(2, 5, 12)
        torch.testing.assert_close(first(inputs), second(inputs), rtol=0, atol=0)

    def test_unknown_duplicate_and_already_wrapped_targets_fail_before_mutation(self) -> None:
        model = AttentionFixture()
        for names in (
            (),
            ("blocks.0.attn.qkv",) * 2,
            ("blocks.0.attn.qkv", "blocks.1.attn.qkv"),
            ("blocks.0.attn.proj",),
        ):
            with self.subTest(names=names), self.assertRaises(ValueError):
                inject_labram_qkv_lora(model, target_modules=names, rank=3, alpha=6)
            self.assertFalse(parametrize.is_parametrized(model.blocks[0].attn.qkv))
        inject_labram_qkv_lora(model, target_modules=("blocks.0.attn.qkv",), rank=3, alpha=6)
        with self.assertRaises(ValueError):
            inject_labram_qkv_lora(model, target_modules=("blocks.0.attn.qkv",), rank=3, alpha=6)
