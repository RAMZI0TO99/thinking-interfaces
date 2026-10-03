"""Synthetic file and case-claim checks before Cho score extraction."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from core.config import canonical_config_json, config_digest, config_snapshot
from core.provenance import SourceProvenance
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell
from evaluation.phase2_cho_case_inputs import SELECTED_METHODS, ChoFirstTrancheRoute
from evaluation.phase2_cho_method_template import derive_cho_method_template
from evaluation.phase2_cho_selection_file_bridge import verify_cho_recorded_selection_files
from evaluation.phase2_factored_evidence import pack_factored_selection
from evaluation.phase2_protocol import TrialCatalog, source_selection
from evaluation.phase2_records import CellIdentity, envelope
from evaluation.phase2_runner import CasePlan, CaseRecorder, method_configuration
from evaluation.phase2_subject_aggregation import ExpectedCell


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _write(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((canonical_config_json(record) + "\n").encode())


@dataclass(frozen=True)
class CaseFiles:
    root: Path
    route: ChoFirstTrancheRoute
    recorder: CaseRecorder
    pin: PinnedCaseCell
    source: SourceProvenance
    evidence: dict[str, Any]
    evidence_path: Path
    method_digests: dict[str, str]

    def verify(self, pin: PinnedCaseCell | None = None) -> None:
        witness = verify_cho_recorded_selection_files(
            self.route, self.recorder, (pin or self.pin,),
            project_root=self.root, expected_source=self.source,
            method_config_sha256=self.method_digests,
        )
        witness.verify_stable()

    def republish_cell(
        self, *, path: str | None = None, digest: str | None = None,
    ) -> PinnedCaseCell:
        cell_path = self.recorder.output_root / "cells" / f"{self.pin.identity.sha256}.json"
        cell = json.loads(cell_path.read_bytes())
        metrics = cell["payload"]["metrics"]
        if path is not None:
            metrics["selection_evidence_path"] = path
        if digest is not None:
            metrics["selection_evidence_sha256"] = digest
        republished = envelope("evaluation_cell", cell["payload"])
        _write(cell_path, republished)
        return replace(
            self.pin, cell_sha256=republished["sha256"],
            selection_evidence_sha256=metrics["selection_evidence_sha256"],
        )


def _fixture(root: Path, *, factored: bool = False) -> CaseFiles:
    subjects = ("subject_01", "subject_02", "subject_03")
    catalogs = tuple(
        TrialCatalog(
            "cho2017", subject,
            tuple(f"{subject}-{index}" for index in range(4)),
            ("left_hand", "left_hand", "right_hand", "right_hand"),
            ("left_hand", "right_hand"), _digest(subject), _digest("preprocessing"),
        )
        for subject in subjects
    )
    plan = CasePlan("cho2017", subjects[0], "eegnet", 5, 11, 1)
    protocol_json = canonical_config_json({"protocol": {"scope": "synthetic"}})
    protocol_sha = config_digest(json.loads(protocol_json))
    route = ChoFirstTrancheRoute((plan,), catalogs, {}, protocol_json, {}, {})
    selection = source_selection(catalogs, target=plan.target_subject)
    source = SourceProvenance("a" * 40, _digest("source"), False)
    checkpoint = _digest("checkpoint")
    contract: dict[str, Any] = {
        "method": plan.method, "dataset": plan.dataset,
        "selection": config_snapshot(asdict(selection)),
        "protocol_sha256": protocol_sha,
        "shots_per_class": plan.shots_per_class,
        "model_and_sampling_seed": plan.model_seed,
        "source": asdict(source),
        "candidates": [
            {
                "name": "first",
                "source": {"steps_per_subject": 1, "learning_rate": 0.001},
                "support": {"steps": 1, "learning_rate": 0.001},
            },
            {
                "name": "second",
                "source": {"steps_per_subject": 1, "learning_rate": 0.002},
                "support": {"steps": 1, "learning_rate": 0.002},
            },
        ],
        "outer_target": plan.target_subject,
        "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
        "score": "mean_subject_balanced_accuracy_exact_rational",
        "tie_break": "first_in_declared_candidate_order",
        "early_stopping": False,
        "engineering_only": True,
        "scientific_evaluation": False,
        "maximum_gradient_steps": 256,
        "runtime": {
            "device": "cpu", "dtype": "float32", "torch_threads": 1,
            "deterministic_algorithms": True,
            "python": "synthetic", "torch": "synthetic",
            "numpy": "synthetic", "braindecode": "synthetic",
        },
        "profile_a_manifests": {},
    }
    method_digest = method_configuration(derive_cho_method_template(plan, contract, {}))
    method_digests = {method: _digest(method) for method in SELECTED_METHODS}
    method_digests[plan.method] = method_digest
    identity = CellIdentity(
        plan.dataset, plan.target_subject, plan.method, plan.shots_per_class,
        plan.model_seed, None, None, protocol_sha, _digest("episode"),
        config_digest(asdict(selection)), method_digest, _digest("preprocessing"),
        checkpoint, source.source_sha256, _digest("environment"),
        source.git_commit, False,
    )
    identities = {
        subject: {"catalog_sha256": _digest(subject), "trial_ids": [f"{subject}-trial"]}
        for subject in selection.source_subjects
    }
    folds = []
    for candidate in ("first", "second"):
        for validation in selection.source_subjects:
            members = [
                subject for subject in selection.source_subjects if subject != validation
            ]
            folds.append({
                "candidate": candidate, "validation_subject": validation,
                "source_fit": {
                    "candidate": candidate, "validation_subject": validation,
                    "training_subjects": members,
                    "input_identities": {subject: identities[subject] for subject in members},
                },
                "input_identities": {validation: identities[validation]},
            })
    payload = {
        "purpose": "bounded_eegnet_source_selection", "complete": True,
        "outer_target_predictions_performed": False,
        "contract": contract, "contract_sha256": config_digest(contract),
        "selected_candidate": "first", "folds": folds, "scores": [],
        "final_source_fit": {
            "candidate": "first", "validation_subject": None,
            "candidate_sha256": config_digest(contract["candidates"][0]),
            "training_subjects": list(selection.source_subjects),
            "input_identities": identities, "fitted_state_sha256": checkpoint,
        },
    }
    evidence = envelope("engineering_smoke", payload)
    if factored:
        packed = pack_factored_selection(evidence)
        directory = root / "runs/phase2/selected_sources"
        for name in ("evidence", "weights", "manifests"):
            (directory / name).mkdir(parents=True, exist_ok=True)
        evidence_path = directory / "evidence" / (
            f"{hashlib.sha256(packed).hexdigest()}.factored.json"
        )
        evidence_path.write_bytes(packed)
    else:
        evidence_path = root / "runs/phase2/selection_evidence" / f"{evidence['sha256']}.json"
        _write(evidence_path, evidence)
    recorder = CaseRecorder(root)
    cell = envelope("evaluation_cell", {
        "identity": asdict(identity),
        "metrics": {
            "selection_evidence_sha256": evidence["sha256"],
            "selection_evidence_path": evidence_path.relative_to(root).as_posix(),
            "balanced_accuracy": [1, 1],
        },
    })
    _write(recorder.output_root / "cells" / f"{identity.sha256}.json", cell)
    pin = PinnedCaseCell(
        plan, ExpectedCell(*plan.identity_key), identity, 1, cell["sha256"],
        _digest("success"), evidence["sha256"],
    )
    return CaseFiles(
        root, route, recorder, pin, source, evidence, evidence_path, method_digests,
    )


@pytest.mark.parametrize("factored", [False, True])
def test_canonical_and_factored_evidence_bind_case(tmp_path: Path, factored: bool) -> None:
    case = _fixture(tmp_path, factored=factored)
    witness = verify_cho_recorded_selection_files(
        case.route, case.recorder, (case.pin,),
        project_root=case.root, expected_source=case.source,
        method_config_sha256=case.method_digests,
    )
    assert len(witness.claims) == 1
    claim = witness.claims[0]
    assert claim.case_id == case.pin.plan.case_id
    assert claim.evidence_sha256 == case.pin.selection_evidence_sha256
    assert claim.contract_sha256 == case.evidence["payload"]["contract_sha256"]
    assert claim.selected_candidate == case.evidence["payload"]["selected_candidate"]
    witness.verify_stable()


@pytest.mark.parametrize("bad_path", [
    "runs/phase2/selection_evidence/missing.json",
    "/runs/phase2/selection_evidence/absolute.json",
    "runs/phase2/../selection_evidence/traversal.json",
    "runs\\phase2\\selection_evidence\\backslash.json",
    "C:/runs/phase2/selection_evidence/drive.json",
])
def test_missing_or_noncanonical_path_fails(tmp_path: Path, bad_path: str) -> None:
    case = _fixture(tmp_path)
    with pytest.raises(ValueError):
        case.verify(case.republish_cell(path=bad_path))


def test_hardlink_and_oversize_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    case = _fixture(tmp_path)
    alias = case.evidence_path.with_name("linked.json")
    os.link(case.evidence_path, alias)
    with pytest.raises(ValueError, match="link count"):
        case.verify(case.republish_cell(path=alias.relative_to(tmp_path).as_posix()))
    pin = case.republish_cell(path=case.evidence_path.relative_to(tmp_path).as_posix())
    monkeypatch.setattr(
        "evaluation.phase2_cho_selection_file_bridge.MAXIMUM_LOGICAL_BYTES",
        case.evidence_path.stat().st_size - 1,
    )
    with pytest.raises(ValueError, match="size or link count"):
        case.verify(pin)


def test_wrong_digest_and_case_mismatch_fail(tmp_path: Path) -> None:
    case = _fixture(tmp_path)
    wrong = _digest("wrong evidence")
    with pytest.raises(ValueError, match="external pin"):
        case.verify(case.republish_cell(digest=wrong))

    payload = json.loads(canonical_config_json(case.evidence["payload"]))
    payload["contract"]["shots_per_class"] = 10
    payload["contract_sha256"] = config_digest(payload["contract"])
    altered = envelope("engineering_smoke", payload)
    altered_path = case.evidence_path.with_name(f"{altered['sha256']}.json")
    _write(altered_path, altered)
    repinned = case.republish_cell(
        path=altered_path.relative_to(tmp_path).as_posix(), digest=altered["sha256"],
    )
    with pytest.raises(ValueError, match="case claims differ"):
        case.verify(repinned)


def test_repinned_candidate_settings_fail_reviewed_method_digest(tmp_path: Path) -> None:
    case = _fixture(tmp_path)
    payload = json.loads(canonical_config_json(case.evidence["payload"]))
    payload["contract"]["candidates"][0]["source"]["learning_rate"] = 0.003
    payload["contract_sha256"] = config_digest(payload["contract"])
    altered = envelope("engineering_smoke", payload)
    altered_path = case.evidence_path.with_name(f"{altered['sha256']}.json")
    _write(altered_path, altered)
    repinned = case.republish_cell(
        path=altered_path.relative_to(tmp_path).as_posix(), digest=altered["sha256"],
    )
    with pytest.raises(ValueError, match="reviewed method digest"):
        case.verify(repinned)


def test_republished_undeclared_winner_fails(tmp_path: Path) -> None:
    case = _fixture(tmp_path)
    payload = json.loads(canonical_config_json(case.evidence["payload"]))
    payload["selected_candidate"] = "missing"
    altered = envelope("engineering_smoke", payload)
    altered_path = case.evidence_path.with_name(f"{altered['sha256']}.json")
    _write(altered_path, altered)
    repinned = case.republish_cell(
        path=altered_path.relative_to(tmp_path).as_posix(), digest=altered["sha256"],
    )
    with pytest.raises(ValueError, match="selected candidate is absent"):
        case.verify(repinned)


@pytest.mark.parametrize(("field", "value", "error"), [
    ("outer_target", "subject_02", "static policy"),
    ("source_policy", "target_included", "static policy"),
    ("score", "unbalanced", "static policy"),
    ("maximum_gradient_steps", 257, "static policy"),
    ("profile_a_manifests", {"unexpected": "artifact"}, "source input"),
    ("final_candidate", "second", "case claims differ"),
    ("final_candidate_sha256", "0" * 64, "case claims differ"),
])
def test_republished_static_or_final_claim_fails(
    tmp_path: Path, field: str, value: Any, error: str,
) -> None:
    case = _fixture(tmp_path)
    payload = json.loads(canonical_config_json(case.evidence["payload"]))
    if field == "final_candidate":
        payload["final_source_fit"]["candidate"] = value
    elif field == "final_candidate_sha256":
        payload["final_source_fit"]["candidate_sha256"] = value
    else:
        payload["contract"][field] = value
        payload["contract_sha256"] = config_digest(payload["contract"])
    altered = envelope("engineering_smoke", payload)
    altered_path = case.evidence_path.with_name(f"{altered['sha256']}.json")
    _write(altered_path, altered)
    repinned = case.republish_cell(
        path=altered_path.relative_to(tmp_path).as_posix(), digest=altered["sha256"],
    )
    with pytest.raises(ValueError, match=error):
        case.verify(repinned)


def test_witness_detects_mutation_after_initial_claim_check(tmp_path: Path) -> None:
    case = _fixture(tmp_path)
    witness = verify_cho_recorded_selection_files(
        case.route, case.recorder, (case.pin,),
        project_root=case.root, expected_source=case.source,
        method_config_sha256=case.method_digests,
    )
    payload = json.loads(canonical_config_json(case.evidence["payload"]))
    payload["complete"] = False
    _write(case.evidence_path, envelope("engineering_smoke", payload))
    with pytest.raises(ValueError, match="physical file changed"):
        witness.verify_stable()


def test_physical_mutation_after_first_read_fails(tmp_path: Path) -> None:
    case = _fixture(tmp_path)
    payload = json.loads(canonical_config_json(case.evidence["payload"]))
    payload["complete"] = False
    replacement = envelope("engineering_smoke", payload)
    from evaluation import phase2_cho_selection_file_bridge as bridge

    original = bridge._case_claims

    def mutate_after_claims(*args: Any, **kwargs: Any) -> None:
        original(*args, **kwargs)
        _write(case.evidence_path, replacement)

    with (
        patch.object(bridge, "_case_claims", side_effect=mutate_after_claims),
        pytest.raises(ValueError, match="physical file changed"),
    ):
        case.verify()
