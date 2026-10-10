"""LaBraM opt-in selection dispatch preserves the production evidence boundary."""

from __future__ import annotations

import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, patch

import torch
from braindecode.models import Labram
from torch import nn

from adaptation.anchor_manifest import EEGNetAnchorSettings
from adaptation.labram_manifest import LaBraMTuningSettings
from adaptation.labram_source import LaBraMSourceSettings
from adaptation.source_selection import EEGNetSourceSettings
from encoder.labram import LaBraMClassifier
from evaluation import phase2_cho_sweep as sweep


class _EvidenceRejected(ValueError):
    pass


class _Backbone(nn.Module):
    embed_dim = 2


class ChoCachedSelectionHookTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(11)
            self.model = LaBraMClassifier(
                cast(Labram, _Backbone()), classes=2, channel_names=("C3", "C4"),
            ).eval()
        self.evidence = SimpleNamespace(
            record={"sha256": "a" * 64, "payload": {"selected_candidate": "picked"}},
            write=Mock(),
        )
        self.selected = SimpleNamespace(evidence=self.evidence, source=self.model)
        self.selector = SimpleNamespace(run_selection=Mock(return_value=self.selected))
        self.executor = SimpleNamespace(run_case=Mock())

    def runner(self, hook: Callable[[Any], Any] | None = None) -> sweep.ProductionChoCaseRunner:
        return sweep.ProductionChoCaseRunner(
            root=self.root, recorder=Mock(), protocol_config={},
            catalogs=(SimpleNamespace(subject="subject_01", preprocessing_sha256="b" * 64),),
            episode_records={"subject_01": {"sha256": "c" * 64}},
            selection_records={"subject_01": {"sha256": "d" * 64}},
            profile_assets={}, profile_a_manifests={}, labram_template=self.model,
            maximum_gradient_steps=64, labram_source_selection_runner=hook,
        )

    def dispatch(
        self, runner: sweep.ProductionChoCaseRunner, method: str = "labram_linear",
    ) -> Any:
        plan = SimpleNamespace(method=method, target_subject="subject_01", model_seed=11,
                               shots_per_class=5)
        if method == "eegnet":
            candidate = SimpleNamespace(
                name="picked", source=EEGNetSourceSettings(1, 2, 0.01, 1e6),
                support=EEGNetAnchorSettings(1, 0.01, 1e6),
            )
        else:
            candidate = SimpleNamespace(
                name="picked", source=LaBraMSourceSettings("linear", 1, 2, 0.01),
                support=LaBraMTuningSettings("linear", 1, 0.01),
            )
        with (
            patch.object(sweep, "materialize_cho_candidates", return_value=(candidate,)),
            patch.object(sweep, "sweep_cell_identity", return_value=SimpleNamespace()),
            patch("adaptation.labram_source.BCILaBraMSourceSelector", return_value=self.selector),
            patch("adaptation.source_selection.BCIEEGNetSourceSelector", return_value=self.selector),
            patch(
                "evaluation.phase2_selection_evidence_binding.verify_cho_selection_evidence",
                side_effect=_EvidenceRejected("unchanged publication boundary"),
            ) as verify,
            patch("evaluation.phase2_cho_publication_gate.publish_verified_cho_source") as publish,
        ):
            with self.assertRaisesRegex(_EvidenceRejected, "unchanged publication boundary"):
                runner(plan=plan, executor=self.executor, route=None, method_config={})
        verify.assert_called_once()
        self.assertIs(verify.call_args.kwargs["record"], self.evidence.record)
        publish.assert_not_called()
        self.executor.run_case.assert_not_called()
        return verify

    def test_default_labram_selection_keeps_original_route_and_evidence_checks(self) -> None:
        self.dispatch(self.runner())
        self.selector.run_selection.assert_called_once_with()

    def test_supplied_hook_keeps_selector_and_evidence_boundary(self) -> None:
        hook = Mock(return_value=self.selected)
        self.dispatch(self.runner(hook))
        hook.assert_called_once_with(self.selector)
        self.selector.run_selection.assert_not_called()

    def test_eegnet_does_not_enter_labram_hook(self) -> None:
        hook = Mock(side_effect=AssertionError("LaBraM hook must not receive EEGNet"))
        self.dispatch(self.runner(hook), "eegnet")
        hook.assert_not_called()
        self.selector.run_selection.assert_called_once_with()

    def test_falsy_callable_is_an_explicit_hook(self) -> None:
        callback = Mock(return_value=self.selected)

        class FalsyHook:
            def __bool__(self) -> bool:
                return False

            def __call__(self, selector: Any) -> Any:
                return callback(selector)

        self.dispatch(self.runner(FalsyHook()))
        callback.assert_called_once_with(self.selector)
        self.selector.run_selection.assert_not_called()

    def test_hook_error_propagates_before_evidence_publication_or_target_execution(self) -> None:
        hook = Mock(side_effect=RuntimeError("owned cache scope failed"))
        runner = self.runner(hook)
        plan = SimpleNamespace(method="labram_linear", target_subject="subject_01",
                               model_seed=11, shots_per_class=5)
        with (
            patch.object(sweep, "materialize_cho_candidates", return_value=()),
            patch("adaptation.labram_source.BCILaBraMSourceSelector", return_value=self.selector),
            patch("evaluation.phase2_cho_publication_gate.publish_verified_cho_source") as publish,
        ):
            with self.assertRaisesRegex(RuntimeError, "owned cache scope failed"):
                runner(plan=plan, executor=self.executor, route=None, method_config={})
        hook.assert_called_once_with(self.selector)
        self.evidence.write.assert_not_called()
        self.selector.run_selection.assert_not_called()
        publish.assert_not_called()
        self.executor.run_case.assert_not_called()

    def test_noncallable_hook_is_refused_at_construction(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be callable"):
            self.runner(cast(Any, True))


if __name__ == "__main__":
    unittest.main()
