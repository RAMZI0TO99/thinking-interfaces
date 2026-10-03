from __future__ import annotations

import copy
import io
import tomllib
import unittest
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

from encoder.tcpl import TCPLClassifier


class TCPLClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(2)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.threads)

    def setUp(self):
        self.rng = torch.random.get_rng_state()
        torch.manual_seed(23)

    def tearDown(self):
        torch.random.set_rng_state(self.rng)

    def test_full_model_shapes_and_variable_lengths(self):
        for channels, classes, length in ((3, 2, 1), (22, 4, 512), (64, 2, 128)):
            with self.subTest(channels=channels, classes=classes, length=length):
                model = TCPLClassifier(channels, classes).eval()
                support = torch.randn(1, 4, channels, 33)
                queries = torch.randn(1, 2, channels, length * 2)[..., ::2]
                with torch.inference_mode():
                    logits = model(support, queries)
                self.assertEqual(logits.shape, (1, 2, classes))
                self.assertTrue(torch.isfinite(logits).all())

    def test_prefix_inserted_once_after_tcn_and_readout_excludes_it(self):
        model = TCPLClassifier(3, 2).double().eval()
        support = torch.randn(2, 4, 3, 19, dtype=torch.float64)
        queries = torch.randn(2, 3, 3, 17, dtype=torch.float64)
        starts, ends, head_inputs, tcn_inputs = [], [], [], []

        def before_layer(module, args):
            starts.append(args[0].detach().clone())

        def after_layer(module, args, output):
            ends.append(output.detach().clone())

        hooks = [model.tcn.register_forward_pre_hook(
            lambda module, args: tcn_inputs.append(args[0].detach().clone())
        ), model.head.register_forward_pre_hook(
            lambda module, args: head_inputs.append(args[0].detach().clone())
        )]
        for layer in model.transformer:
            hooks.extend((layer.register_forward_pre_hook(before_layer),
                          layer.register_forward_hook(after_layer)))
        try:
            with torch.no_grad():
                actual = model(support, queries)
        finally:
            for hook in hooks:
                hook.remove()
        self.assertEqual(len(starts), 4)
        self.assertTrue(all(x.shape == (6, 27, 64) for x in starts + ends))
        torch.testing.assert_close(tcn_inputs[0], queries.reshape(6, 3, 17), rtol=0, atol=0)
        with torch.no_grad():
            prompts = model.support_prompt(support)
            expected_prefix = prompts[:, None].expand(-1, 3, -1, -1).reshape(6, 10, 64)
            eeg = model.tcn(queries.reshape(6, 3, 17))
        torch.testing.assert_close(starts[0][:, :10], expected_prefix, rtol=0, atol=0)
        torch.testing.assert_close(starts[0][:, 10:], eeg, rtol=0, atol=0)
        for i in range(1, 4):
            torch.testing.assert_close(starts[i], ends[i - 1], rtol=0, atol=0)
        expected_pool = ends[-1][:, 10:].mean(1)
        torch.testing.assert_close(head_inputs[0], expected_pool, rtol=0, atol=0)
        self.assertGreater((expected_pool - ends[-1].mean(1)).abs().max().item(), 1e-6)
        with torch.no_grad():
            expected_logits = model.head(expected_pool).reshape(2, 3, 2)
        torch.testing.assert_close(actual, expected_logits, rtol=0, atol=0)

    def test_support_conditioning_reaches_logits_and_query_loss(self):
        model = TCPLClassifier(3, 2).double().eval()
        support = torch.randn(2, 4, 3, 17, dtype=torch.float64, requires_grad=True)
        queries = torch.randn(2, 2, 3, 19, dtype=torch.float64)
        prompts = model.support_prompt(support)
        prompts.retain_grad()
        logits = model.forward_with_prompts(queries, prompts)
        loss = F.cross_entropy(logits.reshape(-1, 2), torch.tensor([0, 1, 1, 0]))
        # No prompt penalty: the query loss itself must reach support conditioning.
        loss.backward()
        self.assertGreater(prompts.grad.abs().sum().item(), 0)
        self.assertTrue(torch.isfinite(support.grad).all())
        self.assertGreater(support.grad.abs().sum().item(), 0)
        with torch.no_grad():
            changed = model(support * 5 + 2, queries)
            zero_prefix = model.forward_with_prompts(queries, torch.zeros_like(prompts))
        self.assertGreater((changed - logits).abs().max().item(), 1e-6)
        self.assertGreater((zero_prefix - logits).abs().max().item(), 1e-6)

    def test_joint_gradients_and_updates_reach_all_components(self):
        model = TCPLClassifier(3, 2).double().train()
        support = torch.randn(2, 4, 3, 17, dtype=torch.float64)
        queries = torch.randn(2, 2, 3, 19, dtype=torch.float64)
        initial = copy.deepcopy(model.state_dict())
        optimizer = torch.optim.SGD(model.parameters(), lr=0.001)
        logits = model(support, queries)
        F.cross_entropy(logits.reshape(-1, 2), torch.tensor([0, 1, 1, 0])).backward()
        for name, parameter in model.named_parameters():
            self.assertIsNotNone(parameter.grad, name)
            self.assertTrue(torch.isfinite(parameter.grad).all(), name)
        groups = [model.tcn, model.support_prompt.encoder, model.support_prompt.generator,
                  *model.transformer, model.head]
        for i, group in enumerate(groups):
            with self.subTest(group=i):
                self.assertGreater(sum(p.grad.abs().sum().item() for p in group.parameters()), 0)
        optimizer.step()
        for prefix in ("tcn", "support_prompt.encoder", "support_prompt.generator",
                       "transformer.0", "transformer.1", "transformer.2", "transformer.3", "head"):
            self.assertTrue(any(
                not torch.equal(value, initial[name])
                for name, value in model.state_dict().items() if name.startswith(prefix + ".")
            ), prefix)

    def test_episode_isolation_support_order_and_query_batching(self):
        model = TCPLClassifier(3, 2).double().eval()
        support = torch.randn(2, 4, 3, 17, dtype=torch.float64)
        queries = torch.randn(2, 3, 3, 19, dtype=torch.float64)
        with torch.no_grad():
            expected = model(support, queries)
            altered = support.clone()
            altered[1] = altered[1] * 5 + 2
            changed = model(altered, queries)
            torch.testing.assert_close(changed[0], expected[0], rtol=0, atol=0)
            self.assertGreater((changed[1] - expected[1]).abs().max().item(), 1e-6)
            reordered = model(support[:, [3, 0, 2, 1]], queries)
            torch.testing.assert_close(reordered, expected, rtol=1e-12, atol=1e-12)
            prompts = model.support_prompt(support)
            parts = torch.cat([
                model.forward_with_prompts(queries[:, i:i + 1], prompts) for i in range(3)
            ], dim=1)
            torch.testing.assert_close(parts, expected, rtol=1e-12, atol=1e-12)
            altered_queries = queries.clone()
            altered_queries[0, 1:] *= 50
            changed = model.forward_with_prompts(altered_queries, prompts)
            torch.testing.assert_close(changed[0, 0], expected[0, 0], rtol=0, atol=0)
            torch.testing.assert_close(changed[1], expected[1], rtol=0, atol=0)

    def test_fixed_target_state_reset_and_safe_round_trip(self):
        model = TCPLClassifier(22, 4).eval().requires_grad_(False)
        support = torch.randn(1, 4, 22, 33)
        queries = torch.randn(1, 2, 22, 65)
        saved_support, saved_queries = support.clone(), queries.clone()
        state = copy.deepcopy(model.state_dict())
        with torch.inference_mode():
            prompts = model.support_prompt(support)
            saved_prompts = prompts.clone()
            expected = model.forward_with_prompts(queries, prompts)
            separated = torch.cat([
                model.forward_with_prompts(queries[:, i:i + 1], prompts) for i in range(2)
            ], dim=1)
            torch.testing.assert_close(separated, expected, rtol=1e-5, atol=1e-6)
            model(support * 50, queries * 20)
            torch.testing.assert_close(model(support, queries), expected, rtol=0, atol=0)
            torch.testing.assert_close(prompts, saved_prompts, rtol=0, atol=0)
        for name, value in model.state_dict().items():
            torch.testing.assert_close(value, state[name], rtol=0, atol=0)
        torch.testing.assert_close(support, saved_support, rtol=0, atol=0)
        torch.testing.assert_close(queries, saved_queries, rtol=0, atol=0)
        self.assertTrue(all(p.grad is None and not p.requires_grad for p in model.parameters()))
        self.assertFalse(any(m.training for m in model.modules()))
        buffer = io.BytesIO()
        torch.save(state, buffer)
        buffer.seek(0)
        restored = TCPLClassifier(22, 4).eval().requires_grad_(False)
        restored.load_state_dict(torch.load(buffer, weights_only=True), strict=True)
        with torch.inference_mode():
            torch.testing.assert_close(restored(support, queries), expected, rtol=0, atol=0)

    def test_transformer_contract_and_independent_initialization(self):
        root = Path(__file__).resolve().parents[1]
        spec = tomllib.loads((root / "configs/phase2/tcpl_local_contract.toml").read_text())
        contract = spec["transformer_candidate"]
        model = TCPLClassifier(3, 4)
        self.assertEqual(len(model.transformer), contract["layers"])
        for layer in model.transformer:
            self.assertEqual(layer.self_attn.embed_dim, contract["model_dim"])
            self.assertEqual(layer.self_attn.num_heads, contract["heads"])
            self.assertTrue(layer.self_attn.batch_first)
            self.assertEqual(layer.linear1.out_features, contract["ffn_dim"])
            self.assertEqual(layer.norm_first, contract["norm_first"])
            self.assertEqual(layer.norm1.eps, contract["layer_norm_epsilon"])
            self.assertEqual(layer.norm2.eps, contract["layer_norm_epsilon"])
            self.assertEqual(layer.self_attn.dropout, contract["dropout"])
            self.assertEqual(layer.dropout.p, contract["dropout"])
            self.assertEqual(layer.activation, F.relu)
            for module in layer.modules():
                if isinstance(module, nn.Linear):
                    self.assertEqual(torch.count_nonzero(module.bias).item(), 0)
                elif isinstance(module, nn.LayerNorm):
                    torch.testing.assert_close(module.weight, torch.ones_like(module.weight))
                    self.assertEqual(torch.count_nonzero(module.bias).item(), 0)
        for left, right in zip(model.transformer[:-1], model.transformer[1:], strict=True):
            self.assertNotEqual(left.self_attn.in_proj_weight.data_ptr(),
                                right.self_attn.in_proj_weight.data_ptr())
            self.assertFalse(torch.equal(left.self_attn.in_proj_weight,
                                         right.self_attn.in_proj_weight))
        self.assertEqual(model.head.out_features, 4)
        self.assertFalse(spec["author_parity_verified"])

    def test_invalid_shapes_nonfinite_inputs_and_class_counts_are_rejected(self):
        for classes in (1, True, 2.0):
            with self.subTest(classes=classes), self.assertRaises(ValueError):
                TCPLClassifier(3, classes)
        model = TCPLClassifier(3, 2)
        support = torch.ones(1, 2, 3, 17)
        queries = torch.ones(1, 2, 3, 19)
        for invalid in (torch.ones(2, 3, 19), torch.ones(0, 2, 3, 19),
                        torch.ones(1, 0, 3, 19), torch.ones(1, 2, 2, 19),
                        queries.long(), queries * float("nan")):
            with self.subTest(shape=invalid.shape), self.assertRaises(ValueError):
                model(support, invalid)
        for invalid in (support.repeat(2, 1, 1, 1), support.double(), support[:, :0],
                        support * float("inf")):
            with self.subTest(shape=invalid.shape), self.assertRaises(ValueError):
                model(invalid, queries)
        for prompts in (torch.ones(1, 9, 64), torch.ones(2, 10, 64),
                        torch.ones(1, 10, 64, dtype=torch.float64),
                        torch.full((1, 10, 64), float("nan"))):
            with self.subTest(shape=prompts.shape), self.assertRaises(ValueError):
                model.forward_with_prompts(queries, prompts)
