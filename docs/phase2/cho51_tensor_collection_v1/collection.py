"""Collect an exact adopted roster of independently pinned native tensor proofs.

This read-only bridge consumes existing finite execution receipts. It never
launches a child, creates a recorder, starts an attempt, or admits science.
"""
from __future__ import annotations

import stat
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from core.provenance import SourceProvenance
from docs.phase2.cho51_publication_collection_v1.collection import (
    Cho51PublicationBinding, Cho51PublicationCollection,
)
from docs.phase2.cho51_tensor_verification_v1 import launcher as tensor_launcher
from docs.phase2.cho51_tensor_verification_v1.contract import (
    Cho51TensorRequest, load_tensor_request, validate_tensor_witness,
)
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import Cho51WorkerRoute
from evaluation.phase2_cho_case_inputs import SELECTED_METHODS, SELECTED_SEEDS
from evaluation.phase2_cho_selection_file_bridge import ChoSelectionFileClaim
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_subject_aggregation import ExpectedCell, ScoreRow


def _digest(value: object, label: str) -> None:
    if type(value) is not str:
        raise ValueError(label + " must be a plain SHA-256 string")
    require_digest(value, label)


def _path(value: object, label: str) -> None:
    # Pure lexical validation: metadata rejection precedes all file I/O.
    if not isinstance(value, Path) or not value.is_absolute() or ".." in value.parts:
        raise ValueError(label + " must be a direct absolute path")


@dataclass(frozen=True, slots=True)
class Cho51TensorReceiptPin:
    """Independent case/request and execution-file digests, supplied externally."""

    case_id: str
    request_sha256: str
    bundle_sha256: str
    bundle_path: Path
    native_directory: Path
    native_receipt_file_sha256: str
    witness_file_sha256: str

    def __post_init__(self) -> None:
        for name in ("case_id", "request_sha256", "bundle_sha256",
                     "native_receipt_file_sha256", "witness_file_sha256"):
            _digest(getattr(self, name), "receipt pin " + name)
        _path(self.bundle_path, "receipt bundle")
        _path(self.native_directory, "native receipt directory")


@dataclass(frozen=True, slots=True)
class Cho51TensorReceiptBinding:
    case_id: str
    request_sha256: str
    bundle_sha256: str
    bundle_path: Path
    native_directory: Path
    native_receipt_file_sha256: str
    witness_file_sha256: str
    peak_process_bytes: int
    peak_job_bytes: int


@dataclass(frozen=True, slots=True)
class Cho51TensorCollection:
    """Exact native tensor-receipt roster; selector and science remain pending."""

    rows: tuple[ScoreRow, ...]
    selection_claims: tuple[ChoSelectionFileClaim, ...]
    publications: tuple[Cho51PublicationBinding, ...]
    receipts: tuple[Cho51TensorReceiptBinding, ...]
    owner_decision_sha256: str
    selection_ceiling_config_sha256: str

    @property
    def complete_tensor_receipt_roster_verified(self) -> bool:
        return True

    @property
    def native_supervision_verified(self) -> bool:
        return True

    @property
    def selected_tensors_verified(self) -> bool:
        return True

    @property
    def full_selector_evidence_verified(self) -> bool:
        return False

    @property
    def selected_publications_verified(self) -> bool:
        return False

    @property
    def selection_publication_tensor_verified(self) -> bool:
        return False

    @property
    def scientific_result_admitted(self) -> bool:
        return False


def _snapshot_and_check(project_root, route, collection, requests, receipt_pins, expected_source):
    if type(route) is not Cho51WorkerRoute or type(collection) is not Cho51PublicationCollection:
        raise ValueError("exact adopted route and prior publication collection required")
    _path(project_root, "project root")
    if (type(expected_source) is not SourceProvenance
            or type(expected_source.git_commit) is not str
            or len(expected_source.git_commit) not in (40, 64)
            or any(c not in "0123456789abcdef" for c in expected_source.git_commit)
            or type(expected_source.git_dirty) is not bool):
        raise ValueError("independent exact source provenance required")
    _digest(expected_source.source_sha256, "source")
    for value, label in ((collection.owner_decision_sha256, "owner"),
                         (collection.selection_ceiling_config_sha256, "selection ceiling")):
        _digest(value, label)
    if collection.owner_decision_sha256 != route.contract.owner_decision_sha256:
        raise ValueError("publication owner differs from adopted route")
    expected_plans = {
        CasePlan("cho2017", f"subject_{subject:02d}", method, 5, seed, 1)
        for subject in range(2, 53) for method in SELECTED_METHODS for seed in SELECTED_SEEDS
    }
    if (type(route.plans) is not tuple or len(route.plans) != 1020
            or any(type(plan) is not CasePlan for plan in route.plans)
            or set(route.plans) != expected_plans):
        raise ValueError("exact adopted 1,020-case subject02-52 route required")
    methods = dict(route.contract.method_config_sha256)
    if set(methods) != set(SELECTED_METHODS):
        raise ValueError("exact four-method configuration map required")
    for method, digest in methods.items():
        _digest(digest, "method " + method)
    if (not isinstance(requests, Sequence) or isinstance(requests, (str, bytes))
            or not isinstance(receipt_pins, Sequence) or isinstance(receipt_pins, (str, bytes))):
        raise ValueError("request and independent receipt-pin sequences required")
    requests, pins = tuple(requests), tuple(receipt_pins)
    cases = {plan.case_id for plan in route.plans}
    if (len(requests) != 1020 or any(type(r) is not Cho51TensorRequest for r in requests)
            or {r.plan.case_id for r in requests} != cases):
        raise ValueError("exact 1,020 distinct adopted tensor requests required")
    if (len(pins) != 1020 or any(type(p) is not Cho51TensorReceiptPin for p in pins)
            or {p.case_id for p in pins} != cases):
        raise ValueError("exact 1,020 distinct adopted independent receipt pins required")
    if any(len({getattr(p, name) for p in pins}) != 1020
           for name in ("bundle_path", "native_directory", "request_sha256")):
        raise ValueError("each case requires its own bundle, native execution and request")
    publications, claims, rows = collection.publications, collection.selection_claims, collection.rows
    for values, cls, label in ((publications, Cho51PublicationBinding, "publications"),
                                (claims, ChoSelectionFileClaim, "selection claims")):
        if (type(values) is not tuple or len(values) != 1020
                or any(type(v) is not cls for v in values)
                or {v.case_id for v in values} != cases):
            raise ValueError("exact immutable adopted " + label + " required")
    keys = {ExpectedCell(*plan.identity_key) for plan in route.plans}
    if (type(rows) is not tuple or len(rows) != 1020
            or any(type(row) is not ScoreRow or type(row.key) is not ExpectedCell for row in rows)):
        raise ValueError("exact immutable adopted publication score rows required")
    # Exact types can still be fabricated without dataclass constructors. Check
    # each key and rational score before hashing keys or opening any proof file.
    for row in rows:
        key = ExpectedCell(row.key.dataset, row.key.subject, row.key.method, row.key.shots, row.key.seed)
        reconstructed = ScoreRow(key, row.numerator, row.denominator, row.cell_sha256)
        if reconstructed != row:
            raise ValueError("publication score row differs from its validated reconstruction")
    if {row.key for row in rows} != keys:
        raise ValueError("exact immutable adopted publication score rows required")
    pub_by_id = {p.case_id: p for p in publications}
    claims_by_id = {c.case_id: c for c in claims}
    requests_by_id, pins_by_id = {r.plan.case_id: r for r in requests}, {p.case_id: p for p in pins}
    for plan in route.plans:
        request, pin, publication = requests_by_id[plan.case_id], pins_by_id[plan.case_id], pub_by_id[plan.case_id]
        # Reconstruct every typed request: frozen dataclasses do not validate a
        # caller's object.__new__/object.__setattr__ fabrication by themselves.
        reconstructed = load_tensor_request(request.payload())
        if reconstructed != request:
            raise ValueError("tensor request is not its exact canonical reconstruction")
        if (request.plan != plan or request.project_root != project_root
                or str(request.project_root) != str(project_root)
                or request.expected_source != expected_source or request.publication != publication
                or publication.method_config_sha256 != methods[plan.method]
                or request.protocol_config_json != route.protocol_config_json
                or request.sha256 != pin.request_sha256):
            raise ValueError("tensor request differs from publication, route, source or independent pin")
        pin.__post_init__()
        if (pin.bundle_path.name != "bundle.json"
                or not pin.bundle_path.is_relative_to(tensor_launcher.ROOT / "runs/coordination")
                or pin.bundle_path.parent == tensor_launcher.ROOT / "runs/coordination"
                or pin.native_directory.parent != tensor_launcher.ROOT / "runs/migration"):
            raise ValueError("receipt bundle or native output lies outside qualified launcher paths")
        claim = claims_by_id[plan.case_id]
        relative = publication.manifest_path.relative_to(project_root).as_posix()
        if (claim.evidence_sha256 != publication.evidence_sha256
                or claim.contract_sha256 != publication.selection_contract_sha256
                or claim.selected_candidate != publication.selected_candidate
                or claim.manifest_sha256 != publication.manifest_sha256 or claim.manifest_path != relative):
            raise ValueError("publication selection claim differs from tensor request")
    # Public result order always follows the immutable adopted route.
    return tuple(requests_by_id[p.case_id] for p in route.plans), tuple(pins_by_id[p.case_id] for p in route.plans)


def _physical(path: Path, expected: str | None = None):
    tensor_launcher._direct(path)
    before = path.stat()
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
            or not 0 < before.st_size <= 1024**2):
        raise ValueError("bounded single-linked regular execution proof required")
    digest = tensor_launcher.digest(path)
    after = path.stat()
    identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    if identity(before) != identity(after) or (expected is not None and digest != expected):
        raise ValueError("execution proof changed or differs from independent file digest")
    return (*identity(before), digest)


def _admit(request, pin):
    bundle = tensor_launcher.load_bundle(pin.bundle_path, pin.bundle_sha256)
    if (bundle["request_sha256"] != pin.request_sha256
            or bundle["request_root"] != str(request.project_root)
            or bundle["workspace"] != str(pin.bundle_path.parent)):
        raise ValueError("loaded native bundle differs from independently bound request")
    payload = tensor_launcher.read_json(Path(bundle["input_path"]), expected_sha256=bundle["input_file_sha256"])
    if payload != request.payload() or load_tensor_request(payload) != request:
        raise ValueError("native input payload differs from the complete external tensor request")
    paths = {
        pin.bundle_path: pin.bundle_sha256,
        Path(bundle["input_path"]): bundle["input_file_sha256"],
        pin.native_directory / "receipt.json": pin.native_receipt_file_sha256,
        Path(bundle["witness_path"]): pin.witness_file_sha256,
        pin.native_directory / "admission.json": None,
        pin.bundle_path.parent / "child-scope.json": None,
    }
    before = {path: _physical(path, digest) for path, digest in paths.items()}
    admitted = tensor_launcher.admit_native_receipt(bundle, pin.bundle_sha256, pin.native_directory)
    expected = dict(
        schema="cho51_tensor_native_result_v1", request_sha256=pin.request_sha256,
        case_id=pin.case_id, native_directory=str(pin.native_directory),
        receipt_file_sha256=pin.native_receipt_file_sha256, witness_file_sha256=pin.witness_file_sha256,
        bundle_sha256=pin.bundle_sha256, native_supervision_verified=True,
        one_case_tensor_digest_verified=True, full_roster_verified=False,
        full_selector_evidence_verified=False, scientific_admission=False,
    )
    if (type(admitted) is not dict or set(admitted) != {*expected, "peak_process_bytes", "peak_job_bytes"}
            or any(type(admitted[k]) is not type(v) or admitted[k] != v for k, v in expected.items())
            or any(type(admitted[k]) is not int or not 0 < admitted[k] <= cap for k, cap in (
                ("peak_process_bytes", 2048 * 1024**2), ("peak_job_bytes", 3072 * 1024**2)))):
        raise ValueError("qualified native admission differs from independent receipt bindings")
    witness = tensor_launcher.read_json(Path(bundle["witness_path"]), expected_sha256=pin.witness_file_sha256)
    validate_tensor_witness(request, witness)
    if any(_physical(path, paths[path]) != identity for path, identity in before.items()):
        raise ValueError("execution proof changed during tensor receipt collection")
    return admitted, before


def collect_cho51_tensor_receipts(
    project_root: Path,
    route: Cho51WorkerRoute,
    publication_collection: Cho51PublicationCollection,
    requests: Sequence[Cho51TensorRequest],
    receipt_pins: Sequence[Cho51TensorReceiptPin],
    *,
    expected_source: SourceProvenance,
) -> Cho51TensorCollection:
    """Read existing native proofs for all 1,020 adopted cases, twice.

    Caller supplies independent file digests, never a native-result.json claim.
    Every actual admission includes the launcher's current native Job absence
    query and source/runtime/publication pin checks. Final physical rereads
    detect same-byte file replacement and earlier-case drift, without claiming
    a filesystem lock or authenticating full selection/fitting history.
    """
    requested, pinned = _snapshot_and_check(project_root, route, publication_collection, requests, receipt_pins, expected_source)
    first = tuple(_admit(request, pin) for request, pin in zip(requested, pinned, strict=True))
    for request, pin, (prior, identities) in zip(requested, pinned, first, strict=True):
        current, final_identities = _admit(request, pin)
        if current != prior or final_identities != identities:
            raise ValueError("earlier native tensor proof changed before final roster admission")
    bindings = tuple(Cho51TensorReceiptBinding(
        pin.case_id, pin.request_sha256, pin.bundle_sha256, pin.bundle_path, pin.native_directory,
        pin.native_receipt_file_sha256, pin.witness_file_sha256,
        result["peak_process_bytes"], result["peak_job_bytes"],
    ) for pin, (result, _) in zip(pinned, first, strict=True))
    return Cho51TensorCollection(
        publication_collection.rows, publication_collection.selection_claims,
        publication_collection.publications, bindings,
        publication_collection.owner_decision_sha256, publication_collection.selection_ceiling_config_sha256,
    )
