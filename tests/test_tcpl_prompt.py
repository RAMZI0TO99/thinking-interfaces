from __future__ import annotations

import copy
import io
import tomllib
import unittest
from pathlib import Path

import torch
from torch import nn

from adaptation.tcpl_prompt import TCPLSupportEncoder, TCPLSupportPromptGenerator


class TCPLSupportPromptTests(unittest.TestCase):
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

    @staticmethod
    def positive_weights(model, bias=0.1):
        with torch.no_grad():
            for module in model.modules():
                if isinstance(module, (nn.Conv1d, nn.Linear)):
                    module.weight.fill_(0.005)
                    module.bias.fill_(bias)

    def test_variable_shapes_and_single_shot_support(self):
        for channels, shots, length in ((1, 1, 1), (3, 5, 17), (22, 20, 512), (64, 2, 512)):
            with self.subTest(channels=channels, shots=shots, length=length):
                model = TCPLSupportPromptGenerator(channels).eval()
                support = torch.randn(2, shots, channels, length * 2)[..., ::2]
                original = support.clone()
                with torch.no_grad():
                    prompts = model(support)
                self.assertEqual(prompts.shape, (2, 10, 64))
                self.assertTrue(torch.isfinite(prompts).all())
                torch.testing.assert_close(support, original, rtol=0, atol=0)

    def test_per_trial_encoding_then_support_mean_matches_independent_reference(self):
        model = TCPLSupportPromptGenerator(3).double().eval()
        support = torch.randn(2, 5, 3, 17, dtype=torch.float64)
        with torch.no_grad():
            expected = []
            for episode in support:
                embeddings = torch.stack([model.encoder(trial[None])[0] for trial in episode])
                expected.append(model.generator(embeddings.sum(0) / len(episode)).reshape(10, 64))
            torch.testing.assert_close(
                model(support), torch.stack(expected), rtol=1e-12, atol=1e-12
            )
        # Averaging raw trials first erases this opposing-sign support's rectified features.
        self.positive_weights(model, bias=0)
        support = torch.stack((-torch.ones(3, 17), torch.ones(3, 17)))[None].double()
        with torch.no_grad():
            correct = model(support)
            wrong = model.generator(model.encoder(support.mean(1))).reshape(1, 10, 64)
        self.assertGreater((correct - wrong).abs().max().item(), 0)

    def test_order_and_uniform_replication_leave_prompts_unchanged(self):
        for dtype, tolerance in ((torch.float32, 1e-6), (torch.float64, 1e-12)):
            with self.subTest(dtype=dtype):
                model = TCPLSupportPromptGenerator(3).to(dtype=dtype).eval()
                support = torch.randn(2, 5, 3, 17, dtype=dtype)
                with torch.no_grad():
                    expected = model(support)
                    for altered in (support[:, [4, 1, 3, 0, 2]], support.repeat(1, 2, 1, 1)):
                        torch.testing.assert_close(
                            model(altered), expected, rtol=tolerance, atol=tolerance
                        )

    def test_signal_sensitivity_and_episode_isolation(self):
        model = TCPLSupportPromptGenerator(3).double().eval()
        self.positive_weights(model)
        support = torch.ones(2, 4, 3, 17, dtype=torch.float64)
        changed = support.clone()
        changed[1, 0] *= 10
        with torch.no_grad():
            expected = model(support)
            actual = model(changed)
            torch.testing.assert_close(actual[0], expected[0], rtol=0, atol=0)
            self.assertGreater((actual[1] - expected[1]).abs().max().item(), 0)
            torch.testing.assert_close(model(changed.flip(0)), actual.flip(0), rtol=0, atol=0)
        support.requires_grad_()
        grad = torch.autograd.grad(model(support)[0].sum(), support)[0]
        self.assertGreater(grad[0].abs().sum().item(), 0)
        self.assertEqual(grad[1].abs().sum().item(), 0)

    def test_gradients_and_effective_updates_reach_encoder_and_generator(self):
        model = TCPLSupportPromptGenerator(3).double()
        self.positive_weights(model)
        before = copy.deepcopy(model.state_dict())
        support = torch.ones(2, 4, 3, 17, dtype=torch.float64, requires_grad=True)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.001)
        initial = model(support)
        initial.square().sum(dim=(1, 2)).mean().backward()
        self.assertTrue(torch.isfinite(support.grad).all())
        self.assertTrue((support.grad.abs().sum(dim=(2, 3)) > 0).all())
        for name, parameter in model.named_parameters():
            with self.subTest(parameter=name):
                self.assertIsNotNone(parameter.grad)
                self.assertTrue(torch.isfinite(parameter.grad).all())
                self.assertGreater(parameter.grad.abs().sum().item(), 0)
        optimizer.step()
        for name, parameter in model.named_parameters():
            self.assertFalse(torch.equal(parameter, before[name]), name)
        self.assertGreater((model(support) - initial).abs().max().item(), 0)

    def test_fixed_target_mode_state_and_safe_round_trip(self):
        model = TCPLSupportPromptGenerator(22).eval().requires_grad_(False)
        support = torch.randn(2, 4, 22, 33)
        state = copy.deepcopy(model.state_dict())
        with torch.inference_mode():
            expected = model(support)
            model(support * 50)
            torch.testing.assert_close(model(support), expected, rtol=0, atol=0)
        for name, value in model.state_dict().items():
            torch.testing.assert_close(value, state[name], rtol=0, atol=0)
        self.assertFalse(list(model.buffers()))
        self.assertTrue(all(p.grad is None for p in model.parameters()))
        buffer = io.BytesIO()
        torch.save(state, buffer)
        buffer.seek(0)
        restored = TCPLSupportPromptGenerator(22).eval().requires_grad_(False)
        restored.load_state_dict(torch.load(buffer, weights_only=True), strict=True)
        with torch.inference_mode():
            torch.testing.assert_close(restored(support), expected, rtol=0, atol=0)
        restored.train()
        with torch.no_grad():
            torch.testing.assert_close(restored(support), expected, rtol=0, atol=0)

    def test_contract_and_parameter_inventory_exclude_independent_prompts_and_labels(self):
        root = Path(__file__).resolve().parents[1]
        local = tomllib.loads((root / "configs/phase2/tcpl_local_contract.toml").read_text())
        reference = tomllib.loads((root / local["reference_inventory"]).read_text())
        model = TCPLSupportPromptGenerator(22)
        convs = [m for m in model.encoder.modules() if isinstance(m, nn.Conv1d)]
        self.assertEqual([m.out_channels for m in convs], local["support"]["conv_widths"])
        for conv in convs:
            self.assertEqual(
                conv.kernel_size, (reference["reported"]["support_encoder"]["kernel_size"],)
            )
            self.assertEqual((conv.stride, conv.padding), ((1,), (1,)))
        self.assertEqual(model.generator[0].out_features, local["generator"]["hidden_dim"])
        self.assertEqual(model.prompt_count, reference["reported"]["generator"]["prompt_count"])
        self.assertEqual(model.prompt_dim, reference["reported"]["generator"]["prompt_dim"])
        names = {name for name, _ in model.named_parameters()}
        expected = {
            f"{module}.{field}" for module in (
                "encoder.features.0", "encoder.features.2", "encoder.projection",
                "generator.0", "generator.2",
            ) for field in ("weight", "bias")
        }
        self.assertEqual(names, expected)
        self.assertFalse(local["author_parity_verified"])
        self.assertFalse(local["numerical_reproduction_ready"])
        self.assertFalse(reference["architecture_reproduction_ready"])
        self.assertFalse(local["support"]["labels_used"])

    def test_invalid_support_and_constructor_inputs_are_rejected(self):
        for channels in (0, -1, True, 2.0):
            with self.subTest(channels=channels), self.assertRaises(ValueError):
                TCPLSupportEncoder(channels)
        model = TCPLSupportPromptGenerator(3)
        for support in (
            torch.ones(2, 3, 17), torch.ones(0, 2, 3, 17), torch.ones(1, 0, 3, 17),
            torch.ones(1, 2, 2, 17), torch.ones(1, 2, 3, 0),
            torch.ones(1, 2, 3, 17, dtype=torch.long),
            torch.full((1, 2, 3, 17), float("nan")),
            torch.full((1, 2, 3, 17), float("inf")),
        ):
            with (
                self.subTest(shape=support.shape, dtype=support.dtype),
                self.assertRaises(ValueError),
            ):
                model(support)
        with self.assertRaises(TypeError):
            model(torch.ones(1, 2, 3, 17), torch.zeros(1, 2, dtype=torch.long))
