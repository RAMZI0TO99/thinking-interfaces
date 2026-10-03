from __future__ import annotations

import json
import unittest
from dataclasses import asdict, replace

from core.config import config_digest, load_toml
from evaluation.phase2_protocol import (
    EpisodePartition,
    TrialCatalog,
    nested_episode,
    source_selection,
    verify_episode_payload,
)
from scripts.audit_phase2_protocol import validate_protocol


def catalog(subject: str = "A", trials_per_class: int = 24) -> TrialCatalog:
    labels = ("left", "right") * trials_per_class
    return TrialCatalog(
        "synthetic",
        subject,
        tuple(f"trial-{i}" for i in range(len(labels))),
        labels,
        ("left", "right"),
        "a" * 64,
        "b" * 64,
    )


class Phase2ProtocolTests(unittest.TestCase):
    def test_direct_construction_cannot_bypass_partition_invariants(self) -> None:
        manifest = nested_episode(catalog(), shots=(1, 20), protocol_sha256="c" * 64)
        with self.assertRaises(ValueError):
            EpisodePartition(1, (0, 1), (1, 2), ())
        with self.assertRaises(ValueError):
            replace(
                manifest,
                partitions=(
                    replace(
                        manifest.partitions[0],
                        support_indices=(2, 3),
                        unused_pool_indices=(0, 1) + tuple(range(4, 40)),
                    ),
                    manifest.partitions[1],
                ),
            )

    def test_common_query_nested_support_and_unavailable_pool(self) -> None:
        item = catalog()
        manifest = nested_episode(item, shots=(1, 5, 10, 20), protocol_sha256="c" * 64)
        previous: set[int] = set()
        for row in manifest.partitions:
            with self.subTest(shots=row.shots_per_class):
                self.assertEqual(row.query_indices, tuple(range(40, 48)))
                support, query, unused = map(
                    set, (row.support_indices, row.query_indices, row.unused_pool_indices)
                )
                self.assertTrue(previous <= support)
                self.assertFalse(support & query or unused & query or support & unused)
                self.assertEqual(support | query | unused, set(range(48)))
                self.assertEqual(len(support), 2 * row.shots_per_class)
                previous = support
        # The same immutable manifest is consumed by every method/model seed.
        self.assertEqual(manifest.partition(5), manifest.partitions[1])
        for invalid in (True, 2, -1):
            with self.assertRaises(ValueError):
                manifest.partition(invalid)

    def test_outer_target_never_reaches_source_validation(self) -> None:
        catalogs = [catalog(s) for s in "ABCD"]
        selection = source_selection(catalogs, target="C")
        self.assertEqual(selection.source_subjects, ("A", "B", "D"))
        for fold in selection.inner_folds:
            self.assertNotIn("C", fold.training_subjects)
            self.assertNotEqual(fold.validation_subject, "C")
            self.assertNotIn(fold.validation_subject, fold.training_subjects)
            self.assertEqual(
                set(fold.training_subjects) | {fold.validation_subject}, {"A", "B", "D"}
            )
        self.assertEqual(selection.sha256, source_selection(catalogs[::-1], target="C").sha256)

    def test_self_rehashed_tampering_is_rejected_against_trusted_catalog(self) -> None:
        item = catalog()
        manifest = nested_episode(item, shots=(1, 20), protocol_sha256="c" * 64)
        saved = json.loads(json.dumps(manifest.payload()))
        arguments = dict(catalog=item, shots=(1, 20), protocol_sha256="c" * 64)
        self.assertTrue(verify_episode_payload(saved, expected_sha256=manifest.sha256, **arguments))
        saved["partitions"][0]["support_indices"][0] = 40
        self.assertFalse(
            verify_episode_payload(saved, expected_sha256=config_digest(saved), **arguments)
        )
        changed = replace(item, labels=("right", "left") + item.labels[2:])
        tampered = nested_episode(changed, shots=(1, 20), protocol_sha256="c" * 64)
        self.assertFalse(
            verify_episode_payload(tampered.payload(), expected_sha256=tampered.sha256, **arguments)
        )

    def test_changed_artifact_and_preprocessing_change_identity(self) -> None:
        item = catalog()
        self.assertNotEqual(item.sha256, replace(item, artifact_sha256="d" * 64).sha256)
        self.assertNotEqual(item.sha256, replace(item, preprocessing_sha256="d" * 64).sha256)
        first = source_selection([item, catalog("B"), catalog("C")], target="C")
        second = source_selection(
            [replace(item, artifact_sha256="d" * 64), catalog("B"), catalog("C")], target="C"
        )
        self.assertNotEqual(first.sha256, second.sha256)

    def test_malformed_cohorts_and_shots_fail_closed(self) -> None:
        for subjects, target in [
            ([catalog(), catalog()], "A"),
            ([catalog(), catalog(), catalog("C")], "A"),
            ([catalog(), catalog("B"), catalog("C")], "D"),
        ]:
            with self.subTest(target=target), self.assertRaises(ValueError):
                source_selection(subjects, target=target)
        for shots in ((True, 20), (0, 20), (20, 1), (1, 1), ()):
            with self.subTest(shots=shots), self.assertRaises(ValueError):
                nested_episode(catalog(), shots=shots, protocol_sha256="c" * 64)
        for item in (catalog(trials_per_class=20), replace(catalog(), labels=("left",) * 48)):
            with self.assertRaises(ValueError):
                nested_episode(item, shots=(1, 20), protocol_sha256="c" * 64)
        malformed = asdict(catalog())
        malformed["trial_ids"] = ("duplicate",) * 48
        with self.assertRaises(ValueError):
            TrialCatalog(**malformed)

    def test_committed_config_and_ambiguous_config_are_checked(self) -> None:
        config = load_toml("configs/phase2/protocol.toml")
        self.assertEqual(validate_protocol(config), (1, 5, 10, 20))
        for key, value in [
            ("maximum_support_per_class", True),
            ("shots_per_class", [1, 20, 5]),
            ("model_seeds", [1, 1]),
            ("experiment_frozen", "false"),
            ("query_policy", "all_remaining"),
        ]:
            changed = json.loads(json.dumps(config))
            changed["protocol"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_protocol(changed)
