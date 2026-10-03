"""Synthetic no-score checks for the complete Cho first-tranche identity binder."""

from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, ClassVar, cast

from core.config import canonical_config_json, config_digest, load_toml
from core.provenance import SourceProvenance
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell
from evaluation.phase2_cho_analysis_identity import verify_cho_case_identity_bindings
from evaluation.phase2_cho_case_inputs import (
    CHO_SUBJECTS,
    SELECTED_METHODS,
    SELECTED_SEEDS,
    ChoFirstTrancheRoute,
)
from evaluation.phase2_profile_binding import CHO_CLASSES, ChoProfileAssets60Hz
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import CellIdentity, envelope
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_subject_aggregation import ExpectedCell


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ChoAnalysisIdentityTests(unittest.TestCase):
    source: ClassVar[SourceProvenance]
    methods: ClassVar[dict[str, str]]
    route: ClassVar[ChoFirstTrancheRoute]
    pins: ClassVar[tuple[PinnedCaseCell, ...]]

    @classmethod
    def setUpClass(cls) -> None:
        config: dict[str, Any] = load_toml(
            Path(__file__).resolve().parents[1] / "configs/phase2/protocol.toml"
        )
        protocol_sha256 = config_digest(config)
        shots = tuple(config["protocol"]["shots_per_class"])
        cls.source = SourceProvenance("b" * 40, "c" * 64, False)
        cls.methods = {method: digest(f"reviewed-{method}") for method in SELECTED_METHODS}
        catalogs = tuple(
            TrialCatalog(
                "cho2017", subject,
                tuple(f"{subject}-{index:02d}" for index in range(42)),
                ("left_hand",) * 21 + ("right_hand",) * 21,
                CHO_CLASSES, digest(f"artifact-{subject}"), digest("preprocessing"),
            )
            for subject in CHO_SUBJECTS
        )
        selections = {
            subject: envelope(
                "source_selection", asdict(source_selection(catalogs, target=subject))
            )
            for subject in CHO_SUBJECTS
        }
        episodes = {
            catalog.subject: envelope(
                "episode_manifest",
                nested_episode(catalog, shots=shots, protocol_sha256=protocol_sha256).payload(),
            )
            for catalog in catalogs
        }
        plans = tuple(
            CasePlan("cho2017", subject, method, 5, seed, 1)
            for subject in CHO_SUBJECTS
            for method in SELECTED_METHODS
            for seed in SELECTED_SEEDS
        )
        cls.route = ChoFirstTrancheRoute(
            plans,
            catalogs,
            MappingProxyType({
                subject: ChoProfileAssets60Hz(
                    digest(f"profile-b-{subject}"), digest(f"manifest-{subject}"),
                    digest("variant"),
                )
                for subject in CHO_SUBJECTS
            }),
            canonical_config_json(config),
            MappingProxyType({
                subject: canonical_config_json(record) for subject, record in selections.items()
            }),
            MappingProxyType({
                subject: canonical_config_json(record) for subject, record in episodes.items()
            }),
        )
        cls.pins = tuple(
            PinnedCaseCell(
                plan,
                ExpectedCell(*plan.identity_key),
                CellIdentity(
                    plan.dataset, plan.target_subject, plan.method, plan.shots_per_class,
                    plan.model_seed, None, None, protocol_sha256,
                    episodes[plan.target_subject]["sha256"],
                    selections[plan.target_subject]["sha256"],
                    cls.methods[plan.method], catalogs[0].preprocessing_sha256,
                    digest(f"checkpoint-{index}"), cls.source.source_sha256,
                    digest("environment"), cls.source.git_commit, False,
                ),
                1,
                digest(f"cell-{index}"),
                digest(f"success-{index}"),
                digest(f"evidence-{index}"),
            )
            for index, plan in enumerate(plans)
        )

    def verify(
        self, *, route: ChoFirstTrancheRoute | None = None,
        pins: tuple[PinnedCaseCell, ...] | None = None,
        methods: dict[str, str] | None = None,
        source: SourceProvenance | None = None,
    ) -> None:
        verify_cho_case_identity_bindings(
            self.route if route is None else route,
            self.pins if pins is None else pins,
            method_config_sha256=self.methods if methods is None else methods,
            expected_source=self.source if source is None else source,
        )

    def altered(self, index: int = 0, **identity_fields: Any) -> tuple[PinnedCaseCell, ...]:
        pins = list(self.pins)
        pins[index] = replace(
            pins[index], identity=replace(pins[index].identity, **identity_fields)
        )
        return tuple(pins)

    def test_exact_synthetic_roster_passes_without_scores(self) -> None:
        self.assertEqual(len(self.pins), 52 * 4 * 5)
        self.verify()

    def test_swapped_route_records_and_target_are_rejected(self) -> None:
        first, second = CHO_SUBJECTS[:2]
        swapped = dict(self.route.selection_records_json)
        swapped[first] = self.route.selection_records_json[second]
        with self.assertRaisesRegex(ValueError, "reconstructed"):
            self.verify(route=replace(self.route, selection_records_json=swapped))

        copied = self.pins[20]
        changed = list(self.pins)
        changed[0] = copied
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.verify(pins=tuple(changed))

    def test_swapped_episode_selection_and_other_identity_hashes_refuse(self) -> None:
        second = self.pins[20].identity
        mutations: dict[str, Any] = {
            "episode_sha256": second.episode_sha256,
            "selection_sha256": second.selection_sha256,
            "preprocessing_sha256": digest("other-preprocessing"),
            "method_config_sha256": self.methods["eegnet"],
            "protocol_sha256": digest("other-protocol"),
            "support_draw_seed": 3,
            "montage_seed": 9,
        }
        for field, value in mutations.items():
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "identity differs"):
                self.verify(pins=self.altered(**{field: value}))

    def test_independent_source_pin_and_unpinned_source_behavior(self) -> None:
        with self.assertRaisesRegex(ValueError, "mixed source"):
            verify_cho_case_identity_bindings(
                self.route, self.altered(source_sha256=digest("other-source")),
                method_config_sha256=self.methods,
            )
        source_changed = tuple(
            replace(pin, identity=replace(pin.identity, source_sha256=digest("other-source")))
            for pin in self.pins
        )
        with self.assertRaisesRegex(ValueError, "source differs"):
            self.verify(pins=source_changed)
        for changed in (self.altered(git_dirty=True), self.altered(git_commit="d" * 40)):
            with self.assertRaisesRegex(ValueError, "mixed source"):
                verify_cho_case_identity_bindings(
                    self.route, changed, method_config_sha256=self.methods,
                )
        verify_cho_case_identity_bindings(
            self.route, source_changed, method_config_sha256=self.methods,
        )
        with self.assertRaisesRegex(ValueError, "known dirty"):
            self.verify(source=replace(self.source, git_dirty=None))

    def test_missing_extra_duplicate_and_wrong_method_map_refuse(self) -> None:
        with self.assertRaisesRegex(ValueError, "1040"):
            self.verify(pins=self.pins[:-1])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.verify(pins=self.pins[:-1] + (self.pins[0],))
        extra_plan = CasePlan("cho2017", "subject_01", "ea_tangent_lr", 5, 11, 1)
        extra = replace(
            self.pins[0],
            plan=extra_plan,
            key=ExpectedCell(*extra_plan.identity_key),
            identity=replace(self.pins[0].identity, method=extra_plan.method),
        )
        with self.assertRaisesRegex(ValueError, "1040"):
            self.verify(pins=self.pins + (extra,))
        with self.assertRaisesRegex(ValueError, "four-method"):
            self.verify(methods={"eegnet": self.methods["eegnet"]})

    def test_malformed_route_or_pins_refuse(self) -> None:
        with self.assertRaisesRegex(ValueError, "route"):
            self.verify(route=replace(self.route, plans=self.route.plans[:-1]))
        with self.assertRaisesRegex(ValueError, "route"):
            self.verify(route=replace(self.route, catalogs=self.route.catalogs[:-1]))
        with self.assertRaisesRegex(ValueError, "typed"):
            verify_cho_case_identity_bindings(
                self.route, cast("tuple[PinnedCaseCell, ...]", "invalid"),
                method_config_sha256=self.methods,
            )
        altered = dict(self.route.episode_records_json)
        altered[CHO_SUBJECTS[0]] = json.dumps({"sha256": digest("invented")})
        with self.assertRaisesRegex(ValueError, "reconstructed"):
            self.verify(route=replace(self.route, episode_records_json=altered))


if __name__ == "__main__":
    unittest.main()
