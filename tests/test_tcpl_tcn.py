from __future__ import annotations

import copy
import io
import tomllib
import unittest
from pathlib import Path

import torch
from torch import nn

from encoder.tcpl_tcn import TCPLCausalTCN


class TCPLCausalTCNTests(unittest.TestCase):
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
    def positive_weights(model):
        # Avoid dead ReLUs/cancellation so absent influence cannot look like causality.
        with torch.no_grad():
            for module in model.modules():
                if isinstance(module, (nn.Conv1d, nn.Linear)):
                    module.weight.fill_(0.005)
                    module.bias.fill_(0.1)

    def test_variable_channel_and_time_shapes(self):
        for channels, length in ((1, 1), (3, 17), (22, 512), (64, 512), (128, 61)):
            with self.subTest(channels=channels, length=length):
                model = TCPLCausalTCN(channels).eval()
                inputs = torch.randn(2, channels, length * 2)[:, :, ::2]
                original = inputs.clone()
                with torch.inference_mode():
                    output = model(inputs)
                self.assertEqual(output.shape, (2, length, 64))
                self.assertTrue(torch.isfinite(output).all())
                torch.testing.assert_close(inputs, original, rtol=0, atol=0)

    def test_reported_dimensions_and_explicit_local_contract(self):
        path = Path(__file__).resolve().parents[1] / "configs/phase2/tcpl_reference.toml"
        spec = tomllib.loads(path.read_text(encoding="utf-8"))
        reported = spec["reported"]["tcn"]
        model = TCPLCausalTCN(22)
        self.assertEqual(len(model.blocks), reported["blocks"])
        for block, width, dilation in zip(
            model.blocks, reported["channels"], reported["dilations"], strict=True
        ):
            for conv in (block.conv1, block.conv2):
                self.assertEqual(conv.out_channels, width)
                self.assertEqual(conv.kernel_size, (reported["kernel_size"],))
                self.assertEqual(conv.dilation, (dilation,))
                self.assertEqual(conv.stride, (1,))
                self.assertEqual(conv.padding, (0,))
            self.assertEqual(block.dropout1.p, reported["dropout"])
            self.assertEqual(block.dropout2.p, reported["dropout"])
        self.assertEqual((model.projection.in_features, model.projection.out_features), (128, 64))
        self.assertFalse(spec["architecture_reproduction_ready"])

    def test_future_perturbations_leave_prefix_equal_with_nonconstant_response(self):
        model = TCPLCausalTCN(3).double()
        self.positive_weights(model)
        inputs = torch.ones(2, 3, 96, dtype=torch.float64)
        for training in (False, True):
            model.train(training)
            for last_observed in (0, 19, 60):
                with self.subTest(training=training, last_observed=last_observed):
                    perturbed = inputs.clone()
                    perturbed[:, :, last_observed + 1:] += 10
                    # In train mode compare the same dropout realization.
                    with torch.no_grad():
                        torch.manual_seed(71)
                        original = model(inputs)
                        torch.manual_seed(71)
                        changed = model(perturbed)
                    torch.testing.assert_close(
                        original[:, :last_observed + 1], changed[:, :last_observed + 1],
                        rtol=0, atol=0,
                    )
                    self.assertGreater(
                        (original[:, last_observed + 1:] - changed[:, last_observed + 1:])
                        .abs().max().item(), 0,
                    )
        # Same perturbation detects a deliberately noncausal symmetric convolution.
        symmetric = nn.Conv1d(3, 1, 3, padding=1, bias=False).double()
        nn.init.ones_(symmetric.weight)
        self.assertNotEqual(symmetric(inputs)[0, 0, 60], symmetric(perturbed)[0, 0, 60])

    def test_each_block_has_the_declared_dilated_dependency(self):
        model = TCPLCausalTCN(1).double().eval()
        self.positive_weights(model)
        for block, dilation in zip(model.blocks, (1, 2, 4, 8), strict=True):
            with self.subTest(dilation=dilation):
                inputs = torch.ones(1, block.conv1.in_channels, 96, dtype=torch.float64)
                inputs.requires_grad_()
                gradient = torch.autograd.grad(block(inputs)[0, 0, 80], inputs)[0]
                influenced = torch.nonzero(gradient[0].abs().sum(0), as_tuple=True)[0].tolist()
                self.assertEqual(influenced, list(range(80 - 4 * dilation, 81, dilation)))

    def test_measured_full_receptive_field_is_exactly_61_samples(self):
        model = TCPLCausalTCN(1).double().eval()
        self.positive_weights(model)
        inputs = torch.ones(1, 1, 96, dtype=torch.float64, requires_grad=True)
        gradient = torch.autograd.grad(model(inputs)[0, 80, 0], inputs)[0][0, 0]
        influenced = torch.nonzero(gradient, as_tuple=True)[0].tolist()
        self.assertEqual(influenced, list(range(20, 81)))
        self.assertEqual(len(influenced), model.receptive_field_samples)
        self.assertTrue(torch.isfinite(gradient).all())

    def test_skip_paths_survive_a_zero_temporal_branch(self):
        model = TCPLCausalTCN(3).eval()
        for index, block in enumerate(model.blocks):
            with self.subTest(block=index), torch.no_grad():
                for conv in (block.conv1, block.conv2):
                    conv.weight.zero_()
                    conv.bias.zero_()
                inputs = torch.randn(2, block.conv1.in_channels, 17)
                torch.testing.assert_close(
                    block(inputs), torch.relu(block.skip(inputs)), rtol=0, atol=0
                )
                self.assertEqual(isinstance(block.skip, nn.Identity), index in (1, 3))

    def test_gradients_and_update_reach_all_parameter_groups(self):
        model = TCPLCausalTCN(3).double().eval()
        self.positive_weights(model)
        initial = copy.deepcopy(model.state_dict())
        inputs = torch.ones(2, 3, 80, dtype=torch.float64, requires_grad=True)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.001)
        model(inputs).square().mean().backward()
        self.assertTrue(torch.isfinite(inputs.grad).all())
        self.assertGreater(inputs.grad.abs().sum().item(), 0)
        for name, parameter in model.named_parameters():
            with self.subTest(parameter=name):
                self.assertIsNotNone(parameter.grad)
                self.assertTrue(torch.isfinite(parameter.grad).all())
                self.assertGreater(parameter.grad.abs().sum().item(), 0)
        optimizer.step()
        for name, parameter in model.named_parameters():
            self.assertFalse(torch.equal(parameter, initial[name]), name)

    def test_eval_state_round_trip_and_independent_sequences(self):
        model = TCPLCausalTCN(22).eval()
        inputs = torch.randn(2, 22, 128)
        state = copy.deepcopy(model.state_dict())
        with torch.inference_mode():
            expected = model(inputs)
            model(inputs * 50)
            torch.testing.assert_close(model(inputs), expected, rtol=0, atol=0)
            for name, value in model.state_dict().items():
                torch.testing.assert_close(value, state[name], rtol=0, atol=0)
        buffer = io.BytesIO()
        torch.save(model.state_dict(), buffer)
        buffer.seek(0)
        restored = TCPLCausalTCN(22).eval()
        restored.load_state_dict(torch.load(buffer, weights_only=True), strict=True)
        with torch.inference_mode():
            torch.testing.assert_close(restored(inputs), expected, rtol=0, atol=0)
        self.assertFalse(list(model.buffers()))

    def test_invalid_dimensions_and_nonfloating_inputs_are_rejected(self):
        for channels in (0, -1, True, 2.0):
            with self.subTest(channels=channels), self.assertRaises(ValueError):
                TCPLCausalTCN(channels)
        model = TCPLCausalTCN(3)
        for inputs in (
            torch.ones(3, 10), torch.ones(1, 2, 10), torch.ones(0, 3, 10),
            torch.ones(1, 3, 0), torch.ones(1, 3, 10, dtype=torch.long),
        ):
            with (
                self.subTest(shape=inputs.shape, dtype=inputs.dtype),
                self.assertRaises(ValueError),
            ):
                model(inputs)
