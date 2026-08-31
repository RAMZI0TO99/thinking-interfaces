from __future__ import annotations

import unittest

import torch

from data.runtime import configure_scientific_runtime
from encoder.eegnet_linear import linearize_eegnet_classifier

configure_scientific_runtime()

from braindecode.models import EEGNet  # type: ignore[import-untyped]  # noqa: E402


class EEGNetLinearHeadTests(unittest.TestCase):
    def test_conversion_preserves_logits_exactly(self) -> None:
        torch.manual_seed(5)
        model = EEGNet(n_chans=3, n_outputs=2, n_times=128, sfreq=128)
        model.eval()
        inputs = torch.randn(4, 3, 128)
        expected = model(inputs).detach()
        converted = linearize_eegnet_classifier(model, inputs[:1])
        converted.eval()
        torch.testing.assert_close(converted(inputs), expected, rtol=0.0, atol=1e-6)
