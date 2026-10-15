"""Locked CaseRecorder lifecycle for explicitly synthetic numerical engineering.

Backend and verifier callbacks do not qualify selectors, study execution or
scientific results. They run while the real case identity lock remains held.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from core.config import canonical_config_json
from core.provenance import SourceProvenance
from evaluation.phase2_protocol import require_digest
from evaluation.phase2_records import verify_envelope
from evaluation.phase2_runner import CasePlan, CaseRecorder
import evaluation.phase2_runner as recorder_module

ROOT = Path(__file__).resolve().parents[3]
CANONICAL_SOURCE_SHA256 = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
METHODS = ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
SEEDS = (11, 23, 37, 53, 71)


def _sha(value, label):
    if type(value) is not str:
        raise ValueError(label + ' must be a plain SHA256 string')
    require_digest(value, label)


def _path(value, label):
    if not isinstance(value, Path) or not value.is_absolute() or '..' in value.parts:
        raise ValueError(label + ' must be a direct absolute path')


def _future_direct(path):
    if path.resolve(strict=False) != path:
        raise ValueError('owned path aliases another location')
    for candidate in (path, *path.parents):
        if candidate.exists() or candidate.is_symlink():
            info = candidate.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                raise ValueError('owned path has a linked/reparse ancestor')


def _plan(plan):
    if type(plan) is not CasePlan:
        raise ValueError('exact adopted CasePlan required')
    rebuilt = CasePlan(**asdict(plan))
    if (rebuilt != plan or plan.dataset != 'cho2017'
            or plan.target_subject not in {f'subject_{s:02d}' for s in range(2, 53)}
            or plan.method not in METHODS or plan.model_seed not in SEEDS
            or plan.shots_per_class != 5 or plan.repetition != 1):
        raise ValueError('exact adopted02-52 method/seed/five-shot/repetition-one plan required')


@dataclass(frozen=True, slots=True)
class WorkerContext:
    parent_output: Path
    fixture_root: Path
    recorder_root: Path
    pins_path: Path
    independent_pins_sha256: str
    execution_source_sha256: str
    owner_decision_sha256: str
    adopted_plans: tuple[CasePlan, ...]
    fixture_source: SourceProvenance
    environment_sha256: str

    def __post_init__(self):
        for name in ('parent_output', 'fixture_root', 'recorder_root', 'pins_path'):
            _path(getattr(self, name), name)
        for name in ('independent_pins_sha256', 'execution_source_sha256', 'owner_decision_sha256', 'environment_sha256'):
            _sha(getattr(self, name), name)
        if (type(self.fixture_source) is not SourceProvenance
                or type(self.fixture_source.git_commit) is not str or len(self.fixture_source.git_commit) not in (40, 64)
                or any(c not in '0123456789abcdef' for c in self.fixture_source.git_commit)
                or type(self.fixture_source.git_dirty) is not bool):
            raise ValueError('independent complete fixture source provenance required')
        _sha(self.fixture_source.source_sha256, 'fixture source')
        if (self.execution_source_sha256 != CANONICAL_SOURCE_SHA256
                or self.fixture_source.source_sha256 == self.execution_source_sha256
                or self.fixture_root == self.parent_output or not self.fixture_root.is_relative_to(self.parent_output)
                or self.recorder_root != self.fixture_root / 'runs/phase2/lifecycle'
                or self.pins_path.is_relative_to(self.fixture_root)):
            raise ValueError('isolated fixture/recorder and independent canonical execution pins required')
        expected = {CasePlan('cho2017', f'subject_{s:02d}', m, 5, seed, 1)
                    for s in range(2, 53) for m in METHODS for seed in SEEDS}
        if (type(self.adopted_plans) is not tuple or len(self.adopted_plans) != 1020
                or any(type(p) is not CasePlan for p in self.adopted_plans)):
            raise ValueError('immutable exact1020 adopted plan context required')
        for plan in self.adopted_plans:
            _plan(plan)
        if set(self.adopted_plans) != expected:
            raise ValueError('context differs from exact1020 adopted roster')


@dataclass(frozen=True, slots=True)
class WorkerRequest:
    plan: CasePlan
    fixture_root: Path
    recorder_root: Path
    workspace: Path
    pins_path: Path
    independent_pins_sha256: str
    execution_source_sha256: str
    owner_decision_sha256: str
    claim_path: Path
    claim_file_sha256: str
    fixture_source_sha256: str
    environment_sha256: str
    attempt: int = 1
    seconds: int = 300
    process_mib: int = 2048
    job_mib: int = 3072
    engineering_only: bool = True
    scientific_admission: bool = False
    original_case_attempts_remaining: int = 0

    def __post_init__(self):
        _plan(self.plan)
        for name in ('fixture_root', 'recorder_root', 'workspace', 'pins_path', 'claim_path'):
            _path(getattr(self, name), name)
        for name in ('independent_pins_sha256', 'execution_source_sha256', 'owner_decision_sha256',
                     'claim_file_sha256', 'fixture_source_sha256', 'environment_sha256'):
            _sha(getattr(self, name), name)
        caps = (3072, 4096) if self.plan.method == 'labram_full' else (2048, 3072)
        if (self.execution_source_sha256 != CANONICAL_SOURCE_SHA256
                or self.fixture_source_sha256 == self.execution_source_sha256
                or self.recorder_root != self.fixture_root / 'runs/phase2/lifecycle'
                or self.claim_path != self.recorder_root / 'claims' / (self.plan.case_id + '.attempt1.claim.json')
                or self.workspace.name != self.plan.case_id or self.workspace.is_relative_to(self.fixture_root)
                or self.pins_path.is_relative_to(self.fixture_root)
                or type(self.attempt) is not int or self.attempt != 1
                or type(self.seconds) is not int or self.seconds != 300
                or type(self.process_mib) is not int or type(self.job_mib) is not int
                or (self.process_mib, self.job_mib) != caps
                or self.engineering_only is not True or self.scientific_admission is not False
                or type(self.original_case_attempts_remaining) is not int or self.original_case_attempts_remaining != 0):
            raise ValueError('fresh attempt-one synthetic request paths/limits/scope differ')

    def payload(self):
        result = asdict(self)
        for name in ('fixture_root', 'recorder_root', 'workspace', 'pins_path', 'claim_path'):
            result[name] = str(getattr(self, name))
        return dict(schema='cho51_worker_request_v1', case_id=self.plan.case_id, **result)

    @property
    def sha256(self):
        return hashlib.sha256(_encoded(self.payload())).hexdigest()


def load_worker_request(payload):
    expected = {field.name for field in fields(WorkerRequest)} | {'schema', 'case_id'}
    if type(payload) is not dict or set(payload) != expected or payload['schema'] != 'cho51_worker_request_v1':
        raise ValueError('exact worker request schema required')
    values = {key: value for key, value in payload.items() if key not in {'schema', 'case_id'}}
    if type(values['plan']) is not dict or set(values['plan']) != {field.name for field in fields(CasePlan)}:
        raise ValueError('exact serialized adopted plan required')
    values['plan'] = CasePlan(**values['plan'])
    for name in ('fixture_root', 'recorder_root', 'workspace', 'pins_path', 'claim_path'):
        if type(values[name]) is not str:
            raise ValueError('serialized absolute path string required')
        values[name] = Path(values[name])
    request = WorkerRequest(**values)
    if request.payload() != payload:
        raise ValueError('request differs from exact typed reconstruction')
    return request


@dataclass(frozen=True, slots=True)
class VerifiedWorkerProof:
    request_sha256: str
    case_id: str
    claim_file_sha256: str
    execution_source_sha256: str
    independent_pins_sha256: str
    owner_decision_sha256: str
    environment_sha256: str
    native_directory: Path
    native_receipt_file_sha256: str
    qualification_path: Path
    qualification_file_sha256: str
    peak_process_bytes: int
    peak_job_bytes: int
    actual_gradient_updates: int = 8
    native_job_closed_empty_absent: bool = True
    engineering_only: bool = True
    scientific_admission: bool = False
    original_case_attempts_remaining: int = 0

    def __post_init__(self):
        for name in ('request_sha256', 'case_id', 'claim_file_sha256', 'execution_source_sha256',
                     'independent_pins_sha256', 'owner_decision_sha256', 'environment_sha256',
                     'native_receipt_file_sha256', 'qualification_file_sha256'):
            _sha(getattr(self, name), name)
        _path(self.native_directory, 'native directory')
        _path(self.qualification_path, 'qualification path')
        if (type(self.peak_process_bytes) is not int or self.peak_process_bytes <= 0
                or type(self.peak_job_bytes) is not int or self.peak_job_bytes <= 0
                or self.peak_job_bytes < self.peak_process_bytes
                or type(self.actual_gradient_updates) is not int or self.actual_gradient_updates != 8
                or self.native_job_closed_empty_absent is not True or self.engineering_only is not True
                or self.scientific_admission is not False
                or type(self.original_case_attempts_remaining) is not int or self.original_case_attempts_remaining != 0):
            raise ValueError('exact finite engineering proof scope and observed peaks required')


@dataclass(frozen=True, slots=True)
class WorkerCompletion:
    request: WorkerRequest
    proof: VerifiedWorkerProof
    request_path: Path
    attestation_path: Path
    attestation_file_sha256: str
    engineering_receipt: Path

    @property
    def scientific_admission(self):
        return False

    @property
    def full_worker_verified(self):
        return False

    @property
    def original_case_attempts_remaining(self):
        return 0


class RecoveryRequired(RuntimeError):
    """An accepted durable artifact exists; no competing failure is published."""


def _encoded(value):
    return (canonical_config_json(value) + '\n').encode('utf-8')


def _read(path, expected=None):
    _path(path, 'proof file')
    if path.resolve(strict=True) != path:
        raise ValueError('proof file aliases another path')
    for parent in (path, *path.parents):
        info = parent.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
            raise ValueError('linked/reparse proof path refused')
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= 8 * 1024**2:
        raise ValueError('bounded single-linked proof file required')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(8 * 1024**2 + 1)
        closed = os.fstat(stream.fileno())
    after = path.stat()
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    handle_identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    digest = hashlib.sha256(raw).hexdigest()
    if (identity(before) != identity(after) or len(raw) != before.st_size
            or handle_identity(before) != handle_identity(opened) or handle_identity(before) != handle_identity(closed)
            or expected is not None and digest != expected):
        raise ValueError('physical proof changed or differs from independent digest')
    return raw, (*identity(before), digest)


def _write_json_once(path, payload):
    raw = _encoded(payload)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def _context_check(context, recorder, plan):
    if type(context) is not WorkerContext or type(recorder) is not CaseRecorder:
        raise ValueError('exact context and real CaseRecorder required')
    context.__post_init__()
    _plan(plan)
    if (plan not in context.adopted_plans or recorder.output_root != context.recorder_root
            or recorder._root != context.fixture_root):
        raise ValueError('case/fixture/recorder differs from independent context')
    if (context.parent_output.resolve(strict=True) != context.parent_output
            or context.fixture_root.resolve(strict=True) != context.fixture_root):
        raise ValueError('direct existing owned parent and fixture roots required')
    _future_direct(context.parent_output)
    _future_direct(context.fixture_root)
    _future_direct(context.recorder_root)
    raw, identity = _read(context.pins_path, context.independent_pins_sha256)
    pins = json.loads(raw)
    if (type(pins) is not dict or pins.get('canonical_source_sha256') != context.execution_source_sha256
            or pins.get('owner_decision_sha256') != context.owner_decision_sha256):
        raise ValueError('independent execution source/owner pins differ')
    if (recorder_module.capture_source(context.fixture_root) != context.fixture_source
            or recorder_module.environment_digest() != context.environment_sha256):
        raise ValueError('live fixture source or execution environment differs from independent context')
    return identity


def _claim(path, plan, context):
    raw, identity = _read(path)
    claim = json.loads(raw)
    payload = claim.get('payload') if type(claim) is dict else None
    if (type(payload) is not dict or set(payload) != {
            'purpose', 'case', 'worker', 'attempt', 'environment_sha256', 'source', 'engineering_only'}
            or payload.get('purpose') != 'pilot_case_claim'
            or payload.get('case') != asdict(plan) or type(payload.get('attempt')) is not int or payload['attempt'] != 1
            or payload.get('worker') != 'cho51_synthetic_numerical_engineering'
            or payload.get('source') != asdict(context.fixture_source)
            or payload.get('environment_sha256') != context.environment_sha256
            or payload.get('engineering_only') is not True
            or not verify_envelope(claim, kind='engineering_smoke', expected_payload=payload)
            or raw != _encoded(claim) or type(payload.get('source')) is not dict):
        raise ValueError('fresh physical engineering claim no longer verifies')
    source_sha = payload['source'].get('source_sha256')
    _sha(source_sha, 'fixture claim source')
    return identity, source_sha


def _verify_proof(request, proof):
    if type(proof) is not VerifiedWorkerProof:
        raise ValueError('exact immutable verified engineering proof required')
    proof.__post_init__()
    if (proof.request_sha256 != request.sha256 or proof.case_id != request.plan.case_id
            or any(getattr(proof, key) != getattr(request, key) for key in (
                'claim_file_sha256', 'execution_source_sha256', 'independent_pins_sha256', 'owner_decision_sha256', 'environment_sha256'))
            or proof.native_directory.parent != ROOT / 'runs/migration'
            or proof.qualification_path != request.workspace / 'child_output/qualification.json'
            or proof.peak_process_bytes > request.process_mib * 1024**2
            or proof.peak_job_bytes > request.job_mib * 1024**2):
        raise ValueError('verified native proof differs from exact request/source/owner/limits')
    return {path: _read(path, digest)[1] for path, digest in (
        (proof.native_directory / 'receipt.json', proof.native_receipt_file_sha256),
        (proof.qualification_path, proof.qualification_file_sha256),
    )}


def _accepted_artifact_exists(recorder, plan, attestation):
    return any(path.exists() or path.is_symlink() for path in (
        attestation, recorder.output_root / 'engineering_intents' / (plan.case_id + '.intent.json'),
        recorder.output_root / 'engineering_successes' / (plan.case_id + '.success.json'),
    ))


def run_engineering_case(recorder, plan, *, context, workspace, backend, verifier):
    """Claim once, execute/verify while locked, attest durably, engineering-only.

    Callbacks are explicit engineering integration seams. Their production
    implementation must verify actual native admission and numerical proof.
    This interface never writes measured cells or invokes a scientific selector.
    """
    pins_identity = _context_check(context, recorder, plan)
    _path(workspace, 'unused case workspace')
    _future_direct(workspace)
    if (workspace != context.parent_output / 'cases' / plan.case_id
            or workspace.exists() or workspace.is_symlink()
            or not callable(backend) or not callable(verifier)):
        raise ValueError('unused case workspace and explicit engineering callbacks required')
    request_path, attestation = workspace / 'request.json', workspace / 'parent-attestation.json'
    with recorder.case_session(plan) as locked:
        # A refused fresh claim is outside the failure handler: never overwrite
        # or append a failure to a preexisting active/terminal case.
        claim_path = locked.claim_new(worker='cho51_synthetic_numerical_engineering', attempt=1)
        request = None
        try:
            claim_identity, fixture_source_sha = _claim(claim_path, plan, context)
            workspace.mkdir(parents=True, exist_ok=False)
            caps = (3072, 4096) if plan.method == 'labram_full' else (2048, 3072)
            request = WorkerRequest(plan, context.fixture_root, context.recorder_root, workspace, context.pins_path,
                context.independent_pins_sha256, context.execution_source_sha256, context.owner_decision_sha256,
                claim_path, claim_identity[-1], fixture_source_sha, context.environment_sha256,
                process_mib=caps[0], job_mib=caps[1])
            request_sha = _write_json_once(request_path, request.payload())
            request_identity = _read(request_path, request.sha256)[1]
            if request_sha != request.sha256:
                raise ValueError('durable request digest differs')
            opaque = backend(request, request_path, request.sha256)
            proof = verifier(request, opaque)
            proof_identities = _verify_proof(request, proof)
            if (_context_check(context, recorder, plan) != pins_identity
                    or _claim(claim_path, plan, context)[0] != claim_identity
                    or _read(request_path, request.sha256)[1] != request_identity):
                raise ValueError('claim/request/execution pins drifted during engineering work')
            if verifier(request, opaque) != proof or _verify_proof(request, proof) != proof_identities:
                raise ValueError('native engineering proof changed before durable parent attestation')
            if (_context_check(context, recorder, plan) != pins_identity
                    or _claim(claim_path, plan, context)[0] != claim_identity
                    or _read(request_path, request.sha256)[1] != request_identity):
                raise ValueError('claim/request/execution pins drifted before durable parent attestation')
            proof_payload = asdict(proof)
            proof_payload['native_directory'] = str(proof.native_directory)
            proof_payload['qualification_path'] = str(proof.qualification_path)
            attested_sha = _write_json_once(attestation, dict(schema='cho51_worker_parent_attestation_v1',
                request_sha256=request.sha256, case_id=plan.case_id, claim_file_sha256=request.claim_file_sha256,
                proof=proof_payload, engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0))
            # Any later exception must quarantine; accepted durable bytes may
            # already be the digest of a partially published recorder intent.
            if (_read(attestation, attested_sha)[1][-1] != attested_sha
                    or _context_check(context, recorder, plan) != pins_identity
                    or _claim(claim_path, plan, context)[0] != claim_identity
                    or _read(request_path, request.sha256)[1] != request_identity
                    or _verify_proof(request, proof) != proof_identities):
                raise ValueError('accepted engineering inputs drifted before terminal publication')
            receipt = locked.record_engineering_success(attempt=1, attested_evidence_sha256=attested_sha)
            completion = recorder.completion((plan,))
            if completion['engineering_success'] != 1 or completion['measured'] != 0:
                raise ValueError('engineering-only completion accounting differs')
            return WorkerCompletion(request, proof, request_path, attestation, attested_sha, receipt)
        except BaseException as error:
            if _accepted_artifact_exists(recorder, plan, attestation):
                raise RecoveryRequired('engineering artifact exists; explicit digest recovery required') from error
            locked.record_failure(attempt=1, reason=dict(purpose='cho51_engineering_lifecycle_failure',
                error=type(error).__name__ + ': ' + str(error), request_sha256=None if request is None else request.sha256,
                engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0))
            raise


def recover_engineering_case(recorder, *, context, request_path, expected_request_sha256, expected_attestation_sha256):
    """Explicitly replay an existing canonical intent from independently pinned bytes.

    This never launches work, creates a new claim or creates a missing intent.
    A durable attestation without a recorder intent remains quarantined.
    """
    _sha(expected_request_sha256, 'external request pin')
    _sha(expected_attestation_sha256, 'external attestation pin')
    raw, request_identity = _read(request_path, expected_request_sha256)
    request = load_worker_request(json.loads(raw))
    if raw != _encoded(request.payload()) or request_path != request.workspace / 'request.json':
        raise ValueError('external request file is not canonical or correctly located')
    pins_identity = _context_check(context, recorder, request.plan)
    if (request.fixture_root != context.fixture_root or request.recorder_root != context.recorder_root
            or request.fixture_source_sha256 != context.fixture_source.source_sha256
            or request.environment_sha256 != context.environment_sha256
            or request.workspace != context.parent_output / 'cases' / request.plan.case_id
            or any(getattr(request, key) != getattr(context, key) for key in (
                'pins_path', 'independent_pins_sha256', 'execution_source_sha256', 'owner_decision_sha256'))):
        raise ValueError('recovery request differs from independent context')
    attestation = request.workspace / 'parent-attestation.json'
    raw_attestation, attestation_identity = _read(attestation, expected_attestation_sha256)
    payload = json.loads(raw_attestation)
    if (type(payload) is not dict or payload.get('schema') != 'cho51_worker_parent_attestation_v1'
            or payload.get('request_sha256') != request.sha256 or payload.get('case_id') != request.plan.case_id
            or payload.get('claim_file_sha256') != request.claim_file_sha256 or payload.get('engineering_only') is not True
            or payload.get('scientific_admission') is not False
            or type(payload.get('original_case_attempts_remaining')) is not int or payload['original_case_attempts_remaining'] != 0
            or set(payload) != {'schema', 'request_sha256', 'case_id', 'claim_file_sha256', 'proof',
                                'engineering_only', 'scientific_admission', 'original_case_attempts_remaining'}
            or raw_attestation != _encoded(payload)):
        raise ValueError('externally pinned parent attestation differs')
    values = dict(payload['proof'])
    values['native_directory'] = Path(values['native_directory'])
    values['qualification_path'] = Path(values['qualification_path'])
    proof = VerifiedWorkerProof(**values)
    proof_identities = _verify_proof(request, proof)
    with recorder.case_session(request.plan) as locked:
        if _claim(request.claim_path, request.plan, context)[0][-1] != request.claim_file_sha256:
            raise ValueError('recovery claim differs')
        if _read(attestation, expected_attestation_sha256)[1] != attestation_identity:
            raise ValueError('parent attestation changed during recovery')
        if (_context_check(context, recorder, request.plan) != pins_identity
                or _read(request_path, expected_request_sha256)[1] != request_identity
                or _verify_proof(request, proof) != proof_identities):
            raise ValueError('recovery inputs changed before locked terminal replay')
        return locked.recover_engineering_success(expected_attested_evidence_sha256=expected_attestation_sha256)
