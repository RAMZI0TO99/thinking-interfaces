"""Bounded read-only checks for selected-source publication bytes and claims."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from torch import nn

from core.config import canonical_config_json, config_digest
from core.provenance import SourceProvenance, capture_source
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_selected_manifest_bridge import (
    ChoSelectedManifestWitness,
    verify_cho_selected_manifest_files,
)
from evaluation.phase2_factored_evidence import (
    SCHEMA,
    pack_factored_selection,
    unpack_factored_selection,
)
from evaluation.phase2_records import envelope
from evaluation.phase2_selected_source_store import SelectedSourceStore


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write(path: Path, record: dict[str, Any]) -> None:
    path.write_bytes((canonical_config_json(record) + "\n").encode())


@dataclass(frozen=True)
class Publication:
    root: Path
    manifest_path: Path
    evidence_path: Path
    weights_path: Path
    evidence_sha256: str
    contract_sha256: str
    protocol_sha256: str
    source: SourceProvenance
    recipe_sha256: str
    model_sha256: str
    winner: str

    def verify(
        self, *, path: Path | None = None, sha: str | None = None,
        evidence_sha: str | None = None,
    ) -> ChoSelectedManifestWitness:
        return verify_cho_selected_manifest_files(
            self.root, path or self.manifest_path,
            manifest_sha256=sha or self.manifest_path.stem,
            evidence_sha256=evidence_sha or self.evidence_sha256,
            selection_contract_sha256=self.contract_sha256,
            selected_candidate=self.winner,
            protocol_config_sha256=self.protocol_sha256,
            expected_source=self.source,
            model_recipe_sha256=self.recipe_sha256,
            model_state_sha256=self.model_sha256,
        )


def _publication(
    root: Path, *, sparse: bool = False, factored: bool = False,
) -> Publication:
    store = root / "runs" / "phase2" / "selected_sources"
    for name in ("weights", "evidence", "manifests"):
        (store / name).mkdir(parents=True)
    # The verifier deliberately hashes, but does not deserialize tensor bytes.
    blob = b"synthetic weights bytes for byte-binding only"
    weights_sha = _sha(blob)
    weights_path = store / "weights" / f"{weights_sha}.safetensors"
    weights_path.write_bytes(blob)
    protocol_sha = _sha(b"protocol")
    state_sha = _sha(b"state claim")
    source = SourceProvenance("a" * 40, _sha(b"source"), False)
    subjects = ["subject_01", "subject_02"]
    source_table = {
        subject: {"catalog_sha256": _sha(subject.encode())} for subject in subjects
    }
    contract = {
        "method": "eegnet", "dataset": "cho2017",
        "selection": {
            "target_subject": "subject_03", "source_subjects": subjects,
        },
        "protocol_sha256": protocol_sha, "source": asdict(source),
        "candidates": [{"name": "first"}],
    }
    contract_sha = config_digest(contract)
    folds = [
        {
            "candidate": "first", "validation_subject": validation,
            "source_fit": {
                "candidate": "first", "validation_subject": validation,
                "training_subjects": [subject for subject in subjects if subject != validation],
                "input_identities": {
                    subject: source_table[subject]
                    for subject in subjects if subject != validation
                },
            },
        }
        for validation in subjects
    ]
    evidence = envelope("engineering_smoke", {
        "purpose": "bounded_eegnet_source_selection", "complete": True,
        "outer_target_predictions_performed": False,
        "contract": contract, "contract_sha256": contract_sha,
        "selected_candidate": "first", "folds": folds,
        "final_source_fit": {
            "candidate": "first", "validation_subject": None,
            "training_subjects": subjects, "input_identities": source_table,
            "candidate_sha256": config_digest({"name": "first"}),
            "fitted_state_sha256": state_sha,
        },
    })
    evidence_sha = evidence["sha256"]
    if factored:
        evidence_blob = pack_factored_selection(evidence)
        physical_sha = _sha(evidence_blob)
        evidence_path = store / "evidence" / f"{physical_sha}.factored.json"
    else:
        evidence_blob = (canonical_config_json(evidence) + "\n").encode()
        evidence_path = store / "evidence" / f"{evidence_sha}.json"
    evidence_path.write_bytes(evidence_blob)
    recipe = {"architecture": "small synthetic", "method": "eegnet"}
    payload: dict[str, Any] = {
        "purpose": "selected_source_snapshot", "scope": "engineering_only",
        "scientific_evaluation": False, "evidence_sha256": evidence_sha,
        "selected_candidate": "first", "selection_contract_sha256": contract_sha,
        "protocol_config_sha256": protocol_sha, "source": asdict(source),
        "model_class": "synthetic.Model", "model_recipe": recipe,
        "model_recipe_sha256": config_digest(recipe), "model_state_sha256": state_sha,
        "tensor_schema": {"weight": {"shape": [2], "dtype": "torch.float32"}},
        "weights_sha256": weights_sha,
        "weights_file": f"weights/{weights_sha}.safetensors",
        "evidence_file": f"evidence/{evidence_sha}.json",
    }
    if sparse:
        payload.update({
            "weights_format": "sparse_frozen_init_v2",
            "initial_state_sha256": _sha(b"initial"),
            "final_fit_mask_sha256": _sha(b"mask"),
            "trainable_parameter_names": ["weight"],
            "stored_tensor_names": ["weight"],
            "omitted_tensor_names": [],
        })
    if factored:
        payload.update({
            "evidence_format": "factored_json_v1", "evidence_schema": SCHEMA,
            "evidence_physical_sha256": physical_sha,
            "evidence_physical_bytes": len(evidence_blob),
            "evidence_file": f"evidence/{physical_sha}.factored.json",
        })
    record = envelope("engineering_smoke", payload)
    manifest_path = store / "manifests" / f"{record['sha256']}.json"
    _write(manifest_path, record)
    return Publication(
        root, manifest_path, evidence_path, weights_path, evidence_sha, contract_sha,
        protocol_sha, source, config_digest(recipe), state_sha, "first",
    )


def _republish_evidence(
    publication: Publication, mutation: str, *, factored: bool,
) -> tuple[Path, str]:
    if factored:
        original = unpack_factored_selection(
            publication.evidence_path.read_bytes(),
            expected_evidence_sha256=publication.evidence_sha256,
        )
    else:
        original = json.loads(publication.evidence_path.read_bytes())
    evidence_payload = original["payload"]
    final_fit = evidence_payload["final_source_fit"]
    if mutation == "contract":
        contract = evidence_payload["contract"]
        contract["protocol_sha256"] = _sha(b"different protocol")
        evidence_payload["contract_sha256"] = config_digest(contract)
    elif mutation == "winner":
        evidence_payload["selected_candidate"] = "other"
    elif mutation == "state":
        final_fit["fitted_state_sha256"] = _sha(b"other state")
    elif mutation == "final_candidate":
        final_fit["candidate"] = "other"
    elif mutation == "missing_final_candidate":
        del final_fit["candidate"]
    elif mutation == "candidate_sha":
        final_fit["candidate_sha256"] = _sha(b"other candidate")
    elif mutation == "missing_candidate_sha":
        del final_fit["candidate_sha256"]
    else:
        raise AssertionError("unsupported test mutation")
    evidence = envelope("engineering_smoke", evidence_payload)
    manifest_payload = json.loads(publication.manifest_path.read_bytes())["payload"]
    manifest_payload["evidence_sha256"] = evidence["sha256"]
    if factored:
        blob = pack_factored_selection(evidence)
        physical_sha = _sha(blob)
        manifest_payload["evidence_physical_sha256"] = physical_sha
        manifest_payload["evidence_physical_bytes"] = len(blob)
        name = f"{physical_sha}.factored.json"
    else:
        blob = (canonical_config_json(evidence) + "\n").encode()
        name = f"{evidence['sha256']}.json"
    manifest_payload["evidence_file"] = f"evidence/{name}"
    (publication.evidence_path.parent / name).write_bytes(blob)
    manifest = envelope("engineering_smoke", manifest_payload)
    path = publication.manifest_path.parent / f"{manifest['sha256']}.json"
    _write(path, manifest)
    return path, evidence["sha256"]


@pytest.mark.parametrize("sparse,factored", [(False, False), (True, False), (True, True)])
def test_accepts_pinned_publication_bytes(
    tmp_path: Path, sparse: bool, factored: bool,
) -> None:
    publication = _publication(tmp_path.resolve(), sparse=sparse, factored=factored)
    witness = publication.verify()
    assert witness.weights_path == publication.weights_path
    witness.verify_stable()


def test_accepts_store_published_tiny_model(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    (root / "configs").mkdir()
    (root / "configs" / "base.toml").write_text(
        "[storage]\nminimum_free_gb = 0.0\n", encoding="utf-8",
    )
    source = capture_source(root)
    model = nn.Linear(3, 2)
    protocol = {"protocol": {"schema_version": 1}}
    recipe = {"architecture": "tiny_linear"}
    candidate = {"name": "first", "source": {"steps_per_subject": 1}}
    contract = {
        "method": "eegnet", "dataset": "cho2017",
        "protocol_sha256": config_digest(protocol), "source": asdict(source),
        "candidates": [candidate],
    }
    evidence = envelope("engineering_smoke", {
        "purpose": "bounded_eegnet_source_selection", "contract": contract,
        "contract_sha256": config_digest(contract), "complete": True,
        "selected_candidate": "first", "outer_target_predictions_performed": False,
        "final_source_fit": {
            "candidate": "first", "candidate_sha256": config_digest(candidate),
            "fitted_state_sha256": state_digest(model),
        },
    })
    publication = SelectedSourceStore(root).publish(
        model, evidence, evidence_sha256=evidence["sha256"],
        protocol_config=protocol, model_recipe=recipe,
    )
    witness = verify_cho_selected_manifest_files(
        root, publication.manifest_path,
        manifest_sha256=publication.manifest_sha256,
        evidence_sha256=publication.evidence_sha256,
        selection_contract_sha256=config_digest(contract),
        selected_candidate=publication.selected_candidate,
        protocol_config_sha256=config_digest(protocol),
        expected_source=source,
        model_recipe_sha256=config_digest(recipe),
        model_state_sha256=publication.model_state_sha256,
    )
    witness.verify_stable()


def test_rejects_manifest_outside_default_cho_store(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    copied = (
        publication.root / "runs/phase2/alternate/manifests"
        / publication.manifest_path.name
    )
    copied.parent.mkdir(parents=True)
    _write(copied, json.loads(publication.manifest_path.read_bytes()))
    with pytest.raises(ValueError, match="direct pinned file"):
        publication.verify(path=copied)


def test_rejects_external_context_and_rehashed_manifest_edits(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    with pytest.raises(ValueError, match="external pins"):
        verify_cho_selected_manifest_files(
            publication.root, publication.manifest_path,
            manifest_sha256=publication.manifest_path.stem,
            evidence_sha256=publication.evidence_sha256,
            selection_contract_sha256=_sha(b"other contract"),
            selected_candidate=publication.winner,
            protocol_config_sha256=publication.protocol_sha256,
            expected_source=publication.source,
            model_recipe_sha256=publication.recipe_sha256,
            model_state_sha256=publication.model_sha256,
        )
    record = envelope("engineering_smoke", {
        **json.loads(publication.manifest_path.read_bytes())["payload"],
        "unexpected": True,
    })
    path = publication.manifest_path.parent / f"{record['sha256']}.json"
    _write(path, record)
    with pytest.raises(ValueError, match="manifest fields"):
        publication.verify(path=path, sha=record["sha256"])


@pytest.mark.parametrize("mutation", ["stored", "outside", "overlap"])
def test_rejects_rehashed_sparse_name_partition(tmp_path: Path, mutation: str) -> None:
    publication = _publication(tmp_path.resolve(), sparse=True)
    payload = json.loads(publication.manifest_path.read_bytes())["payload"]
    if mutation == "stored":
        payload["stored_tensor_names"] = []
        payload["omitted_tensor_names"] = ["weight"]
    elif mutation == "outside":
        payload["trainable_parameter_names"] = ["ghost"]
        payload["stored_tensor_names"] = ["ghost"]
        payload["omitted_tensor_names"] = ["weight"]
    else:
        payload["omitted_tensor_names"] = ["weight"]
    manifest = envelope("engineering_smoke", payload)
    path = publication.manifest_path.parent / f"{manifest['sha256']}.json"
    _write(path, manifest)
    with pytest.raises(ValueError, match="partition"):
        publication.verify(path=path, sha=manifest["sha256"])


@pytest.mark.parametrize(
    "mutation", [
        "contract", "winner", "state", "final_candidate", "candidate_sha",
        "missing_final_candidate", "missing_candidate_sha",
    ],
)
def test_rejects_rehashed_evidence_claim_conflicts(tmp_path: Path, mutation: str) -> None:
    publication = _publication(tmp_path.resolve())
    path, evidence_sha = _republish_evidence(publication, mutation, factored=False)
    with pytest.raises(ValueError, match="claims|candidate digest"):
        publication.verify(
            path=path, sha=path.stem, evidence_sha=evidence_sha,
        )


def test_rejects_rehashed_factored_evidence_state_conflict(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve(), factored=True)
    path, evidence_sha = _republish_evidence(publication, "state", factored=True)
    with pytest.raises(ValueError, match="claims"):
        publication.verify(path=path, sha=path.stem, evidence_sha=evidence_sha)


def test_rejects_tampered_weights_and_bounded_files(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    publication.weights_path.write_bytes(b"tampered weights")
    with pytest.raises(ValueError, match="weights bytes"):
        publication.verify()
    with patch(
        "evaluation.phase2_cho_selected_manifest_bridge.MAXIMUM_WEIGHTS_BYTES", 1,
    ), pytest.raises(ValueError, match="size"):
        publication.verify()
    with patch(
        "evaluation.phase2_cho_selected_manifest_bridge.MAXIMUM_MANIFEST_BYTES", 1,
    ), pytest.raises(ValueError, match="size"):
        publication.verify()


@pytest.mark.parametrize("factored", [False, True])
def test_rejects_missing_or_tampered_store_evidence(tmp_path: Path, factored: bool) -> None:
    publication = _publication(tmp_path.resolve(), factored=factored)
    original = publication.evidence_path.read_bytes()
    publication.evidence_path.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="canonical|physical"):
        publication.verify()
    publication.evidence_path.unlink()
    with pytest.raises(ValueError, match="absent"):
        publication.verify()


def test_rejects_evidence_over_byte_limit(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    with patch(
        "evaluation.phase2_cho_selected_manifest_bridge.MAXIMUM_LOGICAL_BYTES", 1,
    ), pytest.raises(ValueError, match="size"):
        publication.verify()


def test_rejects_linked_weights_and_paths_outside_store(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    outside = publication.root / "outside.safetensors"
    os.link(publication.weights_path, outside)
    with pytest.raises(ValueError, match="link count"):
        publication.verify()
    outside.unlink()
    with pytest.raises(ValueError, match="direct pinned"):
        publication.verify(path=publication.weights_path)
    with pytest.raises(ValueError, match="escapes"):
        publication.verify(path=outside)


def test_witness_rejects_same_byte_replacement_after_verification(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    witness = publication.verify()
    alternate = publication.weights_path.with_suffix(".replacement")
    alternate.write_bytes(publication.weights_path.read_bytes())
    os.replace(alternate, publication.weights_path)
    with pytest.raises(ValueError, match="after verification"):
        witness.verify_stable()


def test_witness_rejects_manifest_edit_with_restored_timestamp(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    witness = publication.verify()
    stat = publication.manifest_path.stat()
    record = json.loads(publication.manifest_path.read_bytes())
    record["payload"]["selected_candidate"] = "other"
    _write(publication.manifest_path, record)
    os.utime(publication.manifest_path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert publication.manifest_path.stat().st_size == stat.st_size
    with pytest.raises(ValueError, match="after verification"):
        witness.verify_stable()


def test_witness_rejects_evidence_replacement_after_verification(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    witness = publication.verify()
    alternate = publication.evidence_path.with_suffix(".replacement")
    alternate.write_bytes(publication.evidence_path.read_bytes())
    os.replace(alternate, publication.evidence_path)
    with pytest.raises(ValueError, match="evidence changed after verification"):
        witness.verify_stable()


def test_rejects_aliasing_manifest(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    alias = publication.root / "other.json"
    os.link(publication.manifest_path, alias)
    with pytest.raises(ValueError, match="link count"):
        publication.verify()


def test_rejects_symlinked_weights_if_supported(tmp_path: Path) -> None:
    publication = _publication(tmp_path.resolve())
    outside = publication.root / "alternate.safetensors"
    outside.write_bytes(publication.weights_path.read_bytes())
    publication.weights_path.unlink()
    try:
        os.symlink(outside, publication.weights_path)
    except OSError:
        pytest.skip("symlink creation is unavailable on this Windows account")
    with pytest.raises(ValueError, match="aliases"):
        publication.verify()
