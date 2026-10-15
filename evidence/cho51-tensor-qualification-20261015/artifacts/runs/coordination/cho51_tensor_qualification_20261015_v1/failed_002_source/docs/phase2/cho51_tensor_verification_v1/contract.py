"""Pure request and digest-witness admission for one adopted Cho-51 case.

These objects bind identities. They neither inspect publication bytes nor
authenticate a native Job receipt, tensor reconstruction or scientific result.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from core.config import canonical_config_json, config_digest, config_snapshot
from core.provenance import SourceProvenance
from docs.phase2.cho51_publication_collection_v1.collection import Cho51PublicationBinding
from evaluation.phase2_cho_case_inputs import SELECTED_METHODS, SELECTED_SEEDS
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_runner import CasePlan

INPUT_SCHEMA = "cho51_tensor_child_input_v1"
WITNESS_SCHEMA = "cho51_tensor_child_witness_v1"
_PUBLICATION_DIGEST_FIELDS = (
    "case_id", "manifest_sha256", "evidence_sha256", "selection_contract_sha256",
    "protocol_config_sha256", "method_config_sha256", "environment_sha256",
    "model_recipe_sha256", "model_state_sha256", "weights_sha256",
)
_MATCHED_WITNESS_FIELDS = (
    "manifest_sha256", "evidence_sha256", "selected_candidate",
    "model_recipe_sha256", "model_state_sha256", "weights_sha256",
)
_INPUT_FIELDS = frozenset({
    "schema", "project_root", "plan", "publication", "expected_source",
    "method_config", "protocol_config",
})
_WITNESS_FIELDS = frozenset({
    "schema", "request_sha256", "case_id", "training_performed",
    *_MATCHED_WITNESS_FIELDS,
})


def _digest(value: object, name: str) -> None:
    if type(value) is not str:
        raise ValueError(name + " must be a plain SHA-256 string")
    require_digest(value, name)


def _canonical_mapping(encoded: str, name: str) -> dict[str, Any]:
    if type(encoded) is not str:
        raise ValueError(name + " must be canonical JSON text")
    try:
        decoded = json.loads(encoded)
        if not isinstance(decoded, dict) or canonical_config_json(decoded) != encoded:
            raise ValueError(name + " must be a canonical JSON object")
    except (TypeError, ValueError) as error:
        raise ValueError(name + " must be finite canonical JSON object text") from error
    return decoded


def _validate_metadata(
    project_root: Path,
    plan: CasePlan,
    publication: Cho51PublicationBinding,
    expected_source: SourceProvenance,
) -> None:
    # Pure lexical checks only. The launcher must separately establish direct
    # physical paths and stable bytes; Path.resolve/stat/read are absent here.
    if (
        not isinstance(project_root, Path) or not project_root.is_absolute()
        or ".." in project_root.parts
    ):
        raise ValueError("a lexically direct absolute project root is required")
    if type(plan) is not CasePlan:
        raise ValueError("an exact typed adopted CasePlan is required")
    if (
        type(plan.dataset) is not str or plan.dataset != "cho2017"
        or type(plan.target_subject) is not str
        or plan.target_subject not in {f"subject_{subject:02d}" for subject in range(2, 53)}
        or type(plan.method) is not str or plan.method not in SELECTED_METHODS
        or type(plan.shots_per_class) is not int or plan.shots_per_class != 5
        or type(plan.model_seed) is not int or plan.model_seed not in SELECTED_SEEDS
        or type(plan.repetition) is not int or plan.repetition != 1
    ):
        raise ValueError("one exact adopted subject02-52, method, seed, five-shot case is required")
    if type(publication) is not Cho51PublicationBinding:
        raise ValueError("an exact typed publication binding is required")
    for name in _PUBLICATION_DIGEST_FIELDS:
        _digest(getattr(publication, name), "publication " + name)
    if publication.case_id != plan.case_id:
        raise ValueError("publication case identity differs from the adopted plan")
    if (
        type(publication.selected_candidate) is not str
        or not publication.selected_candidate
        or publication.selected_candidate.strip() != publication.selected_candidate
    ):
        raise ValueError("a nonempty selected candidate without surrounding whitespace is required")
    expected_path = (
        project_root / "runs" / "phase2" / "selected_sources" / "manifests"
        / (publication.manifest_sha256 + ".json")
    )
    if (
        not isinstance(publication.manifest_path, Path)
        or not publication.manifest_path.is_absolute()
        or ".." in publication.manifest_path.parts
        or publication.manifest_path != expected_path
        or str(publication.manifest_path) != str(expected_path)
    ):
        raise ValueError("manifest path must be the pinned digest path under this project root")
    if (
        type(expected_source) is not SourceProvenance
        or type(expected_source.git_commit) is not str
        or len(expected_source.git_commit) not in (40, 64)
        or any(character not in "0123456789abcdef" for character in expected_source.git_commit)
        or type(expected_source.git_dirty) is not bool
    ):
        raise ValueError("exact source commit, digest and literal dirty-state provenance is required")
    _digest(expected_source.source_sha256, "expected source")


@dataclass(frozen=True, slots=True)
class Cho51TensorRequest:
    """Detached immutable metadata for one finite, separately supervised child."""

    project_root: Path
    plan: CasePlan
    publication: Cho51PublicationBinding
    expected_source: SourceProvenance
    method_config_json: str
    protocol_config_json: str

    def __post_init__(self) -> None:
        _validate_metadata(self.project_root, self.plan, self.publication, self.expected_source)
        method = _canonical_mapping(self.method_config_json, "method config")
        protocol = _canonical_mapping(self.protocol_config_json, "protocol config")
        if method.get("dataset") != self.plan.dataset or method.get("method") != self.plan.method:
            raise ValueError("method configuration identity differs from the adopted case")
        if config_digest(method) != self.publication.method_config_sha256:
            raise ValueError("method configuration differs from the independent publication pin")
        if config_digest(protocol) != self.publication.protocol_config_sha256:
            raise ValueError("protocol configuration differs from the independent publication pin")

    def payload(self) -> dict[str, Any]:
        publication = asdict(self.publication)
        publication["manifest_path"] = str(self.publication.manifest_path)
        return {
            "schema": INPUT_SCHEMA,
            "project_root": str(self.project_root),
            "plan": asdict(self.plan),
            "publication": publication,
            "expected_source": asdict(self.expected_source),
            "method_config": _canonical_mapping(self.method_config_json, "method config"),
            "protocol_config": _canonical_mapping(self.protocol_config_json, "protocol config"),
        }

    @property
    def sha256(self) -> str:
        return config_digest(self.payload())

    @property
    def selected_tensors_verified(self) -> bool:
        return False

    @property
    def native_supervision_verified(self) -> bool:
        return False

    @property
    def scientific_result_admitted(self) -> bool:
        return False


def make_tensor_request(
    *,
    project_root: Path,
    plan: CasePlan,
    publication: Cho51PublicationBinding,
    expected_source: SourceProvenance,
    method_config: Mapping[str, Any],
    protocol_config: Mapping[str, Any],
) -> Cho51TensorRequest:
    """Bind one adopted case to detached config snapshots, without file I/O."""
    if not isinstance(method_config, Mapping) or not isinstance(protocol_config, Mapping):
        raise ValueError("method and protocol configurations must be mappings")
    return Cho51TensorRequest(
        project_root, plan, publication, expected_source,
        canonical_config_json(config_snapshot(method_config)),
        canonical_config_json(config_snapshot(protocol_config)),
    )


def load_tensor_request(payload: Mapping[str, Any]) -> Cho51TensorRequest:
    """Revalidate the exact serialized request shape in a fresh child."""
    if (
        not isinstance(payload, Mapping) or set(payload) != _INPUT_FIELDS
        or type(payload.get("schema")) is not str or payload["schema"] != INPUT_SCHEMA
        or type(payload.get("project_root")) is not str
    ):
        raise ValueError("tensor request schema or fields differ")
    for name, record in (
        ("plan", CasePlan), ("publication", Cho51PublicationBinding),
        ("expected_source", SourceProvenance),
    ):
        value = payload[name]
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(record)}:
            raise ValueError("tensor request " + name + " fields differ")
    publication = dict(payload["publication"])
    if type(publication["manifest_path"]) is not str:
        raise ValueError("serialized manifest path must be a string")
    publication["manifest_path"] = Path(publication["manifest_path"])
    request = make_tensor_request(
        project_root=Path(payload["project_root"]),
        plan=CasePlan(**dict(payload["plan"])),
        publication=Cho51PublicationBinding(**publication),
        expected_source=SourceProvenance(**dict(payload["expected_source"])),
        method_config=payload["method_config"], protocol_config=payload["protocol_config"],
    )
    if request.payload() != dict(payload):
        raise ValueError("serialized tensor request differs from its canonical reconstruction")
    return request


@dataclass(frozen=True, slots=True)
class Cho51TensorDigestWitness:
    """Validated digest agreement only; a fabricated callback can produce it."""

    request_sha256: str
    case_id: str
    manifest_sha256: str
    evidence_sha256: str
    selected_candidate: str
    model_recipe_sha256: str
    model_state_sha256: str
    weights_sha256: str
    training_performed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "request_sha256", "case_id", "manifest_sha256", "evidence_sha256",
            "model_recipe_sha256", "model_state_sha256", "weights_sha256",
        ):
            _digest(getattr(self, name), "tensor witness " + name)
        if (
            type(self.selected_candidate) is not str or not self.selected_candidate
            or self.selected_candidate.strip() != self.selected_candidate
            or self.training_performed is not False
        ):
            raise ValueError("tensor witness candidate or literal no-training declaration differs")

    @property
    def selected_tensors_verified(self) -> bool:
        return False

    @property
    def native_supervision_verified(self) -> bool:
        return False

    @property
    def full_selector_evidence_verified(self) -> bool:
        return False

    @property
    def scientific_result_admitted(self) -> bool:
        return False


def validate_tensor_witness(
    request: Cho51TensorRequest, witness: Mapping[str, Any],
) -> Cho51TensorDigestWitness:
    """Require exact schema, literal no-training and all bound identities.

    This deliberately cannot establish native supervision or actual tensor
    restoration. Those need the launcher's independently checked execution
    receipt and a real child using the unchanged tensor-state verifier.
    """
    if type(request) is not Cho51TensorRequest:
        raise ValueError("an exact typed tensor request is required")
    if not isinstance(witness, Mapping) or set(witness) != _WITNESS_FIELDS:
        raise ValueError("tensor digest witness fields differ")
    if (
        type(witness["schema"]) is not str or witness["schema"] != WITNESS_SCHEMA
        or type(witness["request_sha256"]) is not str or witness["request_sha256"] != request.sha256
        or type(witness["case_id"]) is not str or witness["case_id"] != request.plan.case_id
        or witness["training_performed"] is not False
        or any(
            type(witness[name]) is not str or witness[name] != getattr(request.publication, name)
            for name in _MATCHED_WITNESS_FIELDS
        )
    ):
        raise ValueError("tensor digest witness differs from the request or literal no-training contract")
    return Cho51TensorDigestWitness(**{key: value for key, value in witness.items() if key != "schema"})
