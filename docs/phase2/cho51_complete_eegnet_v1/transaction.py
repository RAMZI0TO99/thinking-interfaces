"""Real locked recorder transaction for a complete synthetic EEGNet selector.

Native execution and detached model verification are independently supplied
operational callbacks.  Their proof cannot be replaced by the old eight-update
WorkerRequest.  The terminal is always engineering-only, with zero study cells.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from core.config import config_digest
from docs.phase2.cho51_source_fold_probe_v1 import fixture as F
from docs.phase2.cho51_worker_lifecycle_v1 import lifecycle as L

ROOT = Path(__file__).resolve().parents[3]
WorkerContext = L.WorkerContext
CasePlan = L.CasePlan
CaseRecorder = L.CaseRecorder
RecoveryRequired = L.RecoveryRequired
_PATHS = ('fixture_root', 'recorder_root', 'workspace', 'pins_path', 'claim_path',
          'fixture_identity_path', 'method_config_path')
_BINDINGS = ('claim_file_sha256', 'execution_source_sha256', 'independent_pins_sha256',
             'owner_decision_sha256', 'environment_sha256')
_PROOF_PATHS = ('source_native_directory', 'source_qualification_path',
    'detached_native_directory', 'detached_qualification_path', 'source_result_path',
    'detached_result_path', 'manifest_path', 'evidence_path', 'weights_path')


def _only_plan(plan):
    L._plan(plan)
    if plan != CasePlan('cho2017', 'subject_02', 'eegnet', 5, 11, 1):
        raise ValueError('only the adopted subject02 EEGNet seed11 five-shot engineering case is admitted')


@dataclass(frozen=True, slots=True)
class CompleteRequest:
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
    fixture_identity_path: Path
    fixture_identity_file_sha256: str
    fixture_identity_sha256: str
    method_config_path: Path
    method_config_file_sha256: str
    method_config_sha256: str
    attempt: int = 1
    source_seconds: int = 420
    source_process_mib: int = 3072
    source_job_mib: int = 4096
    detached_seconds: int = 90
    detached_process_mib: int = 2048
    detached_job_mib: int = 3072
    actual_gradient_updates: int = 5253
    source_updates: int = 5151
    support_updates: int = 102
    fold_count: int = 102
    final_source_subjects: int = 51
    engineering_only: bool = True
    scientific_admission: bool = False
    original_case_attempts_remaining: int = 0

    def __post_init__(self):
        _only_plan(self.plan)
        for name in _PATHS:
            L._path(getattr(self, name), name)
        for field in fields(self):
            if field.name.endswith('sha256'):
                L._sha(getattr(self, field.name), field.name)
        exact = dict(attempt=1, source_seconds=420, source_process_mib=3072, source_job_mib=4096,
            detached_seconds=90, detached_process_mib=2048, detached_job_mib=3072,
            actual_gradient_updates=5253, source_updates=5151, support_updates=102,
            fold_count=102, final_source_subjects=51, original_case_attempts_remaining=0)
        if (any(type(getattr(self, key)) is not int or getattr(self, key) != value for key, value in exact.items())
                or self.engineering_only is not True or self.scientific_admission is not False
                or self.execution_source_sha256 != L.CANONICAL_SOURCE_SHA256
                or self.fixture_source_sha256 == self.execution_source_sha256
                or self.recorder_root != self.fixture_root / 'runs/phase2/lifecycle'
                or self.claim_path != self.recorder_root / 'claims' / (self.plan.case_id + '.attempt1.claim.json')
                or self.workspace.name != self.plan.case_id or self.workspace.is_relative_to(self.fixture_root)
                or self.fixture_identity_path != self.fixture_root / 'synthetic-input-identity.json'
                or self.pins_path.is_relative_to(self.fixture_root)
                or self.method_config_path.is_relative_to(self.fixture_root)):
            raise ValueError('complete selector request paths, workload, budgets or engineering scope differ')

    @property
    def selection_output(self):
        return self.workspace / 'source_output'

    @property
    def detached_output(self):
        return self.workspace / 'detached_output'

    def payload(self):
        value = asdict(self)
        for name in _PATHS:
            value[name] = str(getattr(self, name))
        return dict(schema='cho51_complete_eegnet_request_v1', case_id=self.plan.case_id,
            selection_output=str(self.selection_output), detached_output=str(self.detached_output), **value)

    @property
    def sha256(self):
        return hashlib.sha256(L._encoded(self.payload())).hexdigest()


def load_complete_request(payload):
    expected = {field.name for field in fields(CompleteRequest)} | {
        'schema', 'case_id', 'selection_output', 'detached_output'}
    if (type(payload) is not dict or set(payload) != expected
            or payload.get('schema') != 'cho51_complete_eegnet_request_v1'):
        raise ValueError('exact complete EEGNet request schema required')
    values = {key: payload[key] for key in expected - {'schema', 'case_id', 'selection_output', 'detached_output'}}
    if type(values['plan']) is not dict or set(values['plan']) != {f.name for f in fields(CasePlan)}:
        raise ValueError('exact serialized adopted plan required')
    values['plan'] = CasePlan(**values['plan'])
    for name in _PATHS:
        if type(values[name]) is not str:
            raise ValueError('serialized absolute path string required')
        values[name] = Path(values[name])
    result = CompleteRequest(**values)
    if result.payload() != payload:
        raise ValueError('complete request differs from exact typed reconstruction')
    return result


@dataclass(frozen=True, slots=True)
class VerifiedCompleteProof:
    request_sha256: str
    case_id: str
    claim_file_sha256: str
    execution_source_sha256: str
    independent_pins_sha256: str
    owner_decision_sha256: str
    environment_sha256: str
    source_native_directory: Path
    source_native_receipt_file_sha256: str
    source_qualification_path: Path
    source_qualification_file_sha256: str
    detached_native_directory: Path
    detached_native_receipt_file_sha256: str
    detached_qualification_path: Path
    detached_qualification_file_sha256: str
    source_result_path: Path
    source_result_file_sha256: str
    detached_result_path: Path
    detached_result_file_sha256: str
    manifest_path: Path
    manifest_file_sha256: str
    evidence_path: Path
    evidence_file_sha256: str
    evidence_sha256: str
    weights_path: Path
    weights_file_sha256: str
    selected_state_sha256: str
    source_peak_process_bytes: int
    source_peak_job_bytes: int
    detached_peak_process_bytes: int
    detached_peak_job_bytes: int
    actual_gradient_updates: int = 5253
    source_updates: int = 5151
    support_updates: int = 102
    fold_count: int = 102
    final_source_subjects: int = 51
    source_job_closed_empty_absent: bool = True
    detached_job_closed_empty_absent: bool = True
    engineering_only: bool = True
    scientific_admission: bool = False
    original_case_attempts_remaining: int = 0

    def __post_init__(self):
        for field in fields(self):
            if field.name.endswith('sha256') or field.name == 'case_id':
                L._sha(getattr(self, field.name), field.name)
        for name in _PROOF_PATHS:
            L._path(getattr(self, name), name)
        for prefix in ('source', 'detached'):
            process, job = getattr(self, prefix + '_peak_process_bytes'), getattr(self, prefix + '_peak_job_bytes')
            if type(process) is not int or type(job) is not int or not 0 < process <= job:
                raise ValueError('positive observed native process and aggregate peaks required')
        exact = dict(actual_gradient_updates=5253, source_updates=5151, support_updates=102,
            fold_count=102, final_source_subjects=51, original_case_attempts_remaining=0)
        if (any(type(getattr(self, key)) is not int or getattr(self, key) != value for key, value in exact.items())
                or self.source_job_closed_empty_absent is not True or self.detached_job_closed_empty_absent is not True
                or self.engineering_only is not True or self.scientific_admission is not False):
            raise ValueError('complete numerical selector and detached engineering proof required')


@dataclass(frozen=True, slots=True)
class CompleteCompletion:
    request: CompleteRequest
    proof: VerifiedCompleteProof
    request_path: Path
    attestation_path: Path
    attestation_file_sha256: str
    engineering_receipt: Path


def _proof_payload(proof):
    result = asdict(proof)
    for name in _PROOF_PATHS:
        result[name] = str(getattr(proof, name))
    return result


def _assets(request):
    identity_raw, identity_pin = L._read(request.fixture_identity_path, request.fixture_identity_file_sha256)
    identity = json.loads(identity_raw)
    if (type(identity) is not dict or identity_raw != L._encoded(identity)
            or identity.get('sha256') != request.fixture_identity_sha256
            or config_digest({key: value for key, value in identity.items() if key != 'sha256'}) != request.fixture_identity_sha256
            or identity.get('synthetic') is not True or identity.get('actual_study_data') is not False
            or identity.get('scientific_admission') is not False
            or type(identity.get('files')) is not dict or len(identity['files']) != 213):
        raise ValueError('independent synthetic fixture identity differs')
    config_raw, config_pin = L._read(request.method_config_path, request.method_config_file_sha256)
    config = json.loads(config_raw)
    if type(config) is not dict or config_digest(config) != request.method_config_sha256:
        raise ValueError('independently pinned method configuration differs')
    pins = json.loads(L._read(request.pins_path, request.independent_pins_sha256)[0])
    if (not request.method_config_path.is_relative_to(ROOT)
            or pins.get('files', {}).get(request.method_config_path.relative_to(ROOT).as_posix()) != request.method_config_file_sha256):
        raise ValueError('method configuration is absent from independent execution pins')
    return identity_pin, config_pin


def _verify_proof(request, proof):
    if type(proof) is not VerifiedCompleteProof:
        raise ValueError('exact immutable complete selector proof required')
    proof.__post_init__()
    if (proof.request_sha256 != request.sha256 or proof.case_id != request.plan.case_id
            or any(getattr(proof, key) != getattr(request, key) for key in _BINDINGS)
            or proof.source_native_directory.parent != ROOT / 'runs/migration'
            or proof.detached_native_directory.parent != ROOT / 'runs/migration'
            or proof.source_native_directory == proof.detached_native_directory
            or proof.source_qualification_path != request.selection_output / 'qualification.json'
            or proof.detached_qualification_path != request.detached_output / 'qualification.json'
            or proof.source_result_path != request.selection_output / 'source-result.json'
            or proof.detached_result_path != request.detached_output / 'detached-result.json'):
        raise ValueError('complete proof differs from case, source or independent native workspaces')
    for prefix in ('source', 'detached'):
        if (getattr(proof, prefix + '_peak_process_bytes') > getattr(request, prefix + '_process_mib') * 1024**2
                or getattr(proof, prefix + '_peak_job_bytes') > getattr(request, prefix + '_job_mib') * 1024**2):
            raise ValueError('observed native peak exceeds the exact complete request budget')
    publication_root = request.fixture_root / 'runs/phase2'
    for name in ('manifest_path', 'evidence_path', 'weights_path'):
        if not getattr(proof, name).is_relative_to(publication_root):
            raise ValueError('publication differs from the owned synthetic fixture namespace')
    if len({proof.manifest_path, proof.evidence_path, proof.weights_path}) != 3:
        raise ValueError('publication roles must be different physical files')
    pairs = (
        (proof.source_native_directory / 'receipt.json', proof.source_native_receipt_file_sha256),
        (proof.detached_native_directory / 'receipt.json', proof.detached_native_receipt_file_sha256),
        (proof.source_qualification_path, proof.source_qualification_file_sha256),
        (proof.detached_qualification_path, proof.detached_qualification_file_sha256),
        (proof.source_result_path, proof.source_result_file_sha256),
        (proof.detached_result_path, proof.detached_result_file_sha256),
        (proof.manifest_path, proof.manifest_file_sha256),
    )
    result = {path: L._read(path, digest)[1] for path, digest in pairs}
    # The complete canonical evidence can exceed the small JSON helper bound.
    # Use the frozen fixture's bounded streaming helper, preserving no array.
    for path, digest in ((proof.evidence_path, proof.evidence_file_sha256),
                         (proof.weights_path, proof.weights_file_sha256)):
        L._future_direct(path)
        before = F._status(path)
        pin = F._input_pin(path)
        if pin['sha256'] != digest or F._status(path) != before:
            raise ValueError('physical publication bytes differ from verified proof')
        result[path] = (*before, digest)
    return result


def _request_context(request, context):
    if (request.fixture_root != context.fixture_root or request.recorder_root != context.recorder_root
            or request.fixture_source_sha256 != context.fixture_source.source_sha256
            or request.environment_sha256 != context.environment_sha256
            or request.workspace != context.parent_output / 'cases' / request.plan.case_id
            or any(getattr(request, key) != getattr(context, key) for key in (
                'pins_path', 'independent_pins_sha256', 'execution_source_sha256', 'owner_decision_sha256'))):
        raise ValueError('complete request differs from independent current context')


def run_complete_case(recorder, plan, *, context, workspace, fixture_identity_path,
        fixture_identity_file_sha256, fixture_identity_sha256, method_config_path,
        method_config_file_sha256, method_config_sha256, backend, verifier):
    _only_plan(plan)
    pins_identity = L._context_check(context, recorder, plan)
    L._path(workspace, 'unused complete case workspace')
    L._future_direct(workspace)
    if (workspace != context.parent_output / 'cases' / plan.case_id or workspace.exists()
            or workspace.is_symlink() or not callable(backend) or not callable(verifier)):
        raise ValueError('unused complete case workspace and explicit native callbacks required')
    request_path, attestation = workspace / 'request.json', workspace / 'parent-attestation.json'
    with recorder.case_session(plan) as locked:
        claim_path = locked.claim_new(worker='cho51_synthetic_numerical_engineering', attempt=1)
        request = None
        try:
            claim_identity, fixture_source_sha = L._claim(claim_path, plan, context)
            request = CompleteRequest(plan, context.fixture_root, context.recorder_root, workspace,
                context.pins_path, context.independent_pins_sha256, context.execution_source_sha256,
                context.owner_decision_sha256, claim_path, claim_identity[-1], fixture_source_sha,
                context.environment_sha256, fixture_identity_path, fixture_identity_file_sha256,
                fixture_identity_sha256, method_config_path, method_config_file_sha256, method_config_sha256)
            asset_identity = _assets(request)
            workspace.mkdir(parents=True, exist_ok=False)
            if L._write_json_once(request_path, request.payload()) != request.sha256:
                raise ValueError('durable complete request differs')
            request_identity = L._read(request_path, request.sha256)[1]
            opaque = backend(request, request_path, request.sha256)
            proof = verifier(request, opaque)
            proof_identities = _verify_proof(request, proof)
            def stable():
                if (L._context_check(context, recorder, plan) != pins_identity
                        or L._claim(claim_path, plan, context)[0] != claim_identity
                        or L._read(request_path, request.sha256)[1] != request_identity
                        or _assets(request) != asset_identity):
                    raise ValueError('complete request, claim, pins or fixture assets changed')
            stable()
            if verifier(request, opaque) != proof or _verify_proof(request, proof) != proof_identities:
                raise ValueError('complete native proof changed before durable attestation')
            stable()
            attested_sha = L._write_json_once(attestation, dict(
                schema='cho51_complete_eegnet_parent_attestation_v1', request_sha256=request.sha256,
                case_id=plan.case_id, claim_file_sha256=request.claim_file_sha256,
                proof=_proof_payload(proof), engineering_only=True, scientific_admission=False,
                original_case_attempts_remaining=0))
            stable()
            if (L._read(attestation, attested_sha)[1][-1] != attested_sha
                    or _verify_proof(request, proof) != proof_identities):
                raise ValueError('durable complete proof changed before terminal publication')
            receipt = locked.record_engineering_success(attempt=1, attested_evidence_sha256=attested_sha)
            completion = recorder.completion((plan,))
            if completion['engineering_success'] != 1 or completion['measured'] != 0:
                raise ValueError('complete selector terminal must remain engineering-only')
            return CompleteCompletion(request, proof, request_path, attestation, attested_sha, receipt)
        except BaseException as error:
            if L._accepted_artifact_exists(recorder, plan, attestation):
                raise RecoveryRequired('durable complete artifact exists; explicit external-digest recovery required') from error
            locked.record_failure(attempt=1, reason=dict(purpose='cho51_complete_eegnet_failure',
                error=type(error).__name__ + ': ' + str(error),
                request_sha256=None if request is None else request.sha256,
                engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0))
            raise


def recover_complete_case(recorder, *, context, request_path,
        expected_request_sha256, expected_attestation_sha256):
    """Recover an existing engineering intent from external digests; never rerun."""
    L._sha(expected_request_sha256, 'external complete request pin')
    L._sha(expected_attestation_sha256, 'external complete attestation pin')
    raw, request_identity = L._read(request_path, expected_request_sha256)
    request = load_complete_request(json.loads(raw))
    if raw != L._encoded(request.payload()) or request_path != request.workspace / 'request.json':
        raise ValueError('externally pinned complete request is not canonical or correctly located')
    _request_context(request, context)
    pins_identity = L._context_check(context, recorder, request.plan)
    asset_identity = _assets(request)
    attestation = request.workspace / 'parent-attestation.json'
    raw_attestation, attestation_identity = L._read(attestation, expected_attestation_sha256)
    payload = json.loads(raw_attestation)
    expected = dict(schema='cho51_complete_eegnet_parent_attestation_v1', request_sha256=request.sha256,
        case_id=request.plan.case_id, claim_file_sha256=request.claim_file_sha256,
        engineering_only=True, scientific_admission=False, original_case_attempts_remaining=0)
    if (type(payload) is not dict or set(payload) != set(expected) | {'proof'}
            or config_digest({key: payload[key] for key in expected}) != config_digest(expected)
            or raw_attestation != L._encoded(payload) or type(payload['proof']) is not dict):
        raise ValueError('externally pinned complete parent attestation differs')
    values = dict(payload['proof'])
    for name in _PROOF_PATHS:
        values[name] = Path(values[name])
    proof = VerifiedCompleteProof(**values)
    proof_identities = _verify_proof(request, proof)
    with recorder.case_session(request.plan) as locked:
        claim_identity = L._claim(request.claim_path, request.plan, context)[0]
        if (claim_identity[-1] != request.claim_file_sha256
                or L._context_check(context, recorder, request.plan) != pins_identity
                or L._read(request_path, expected_request_sha256)[1] != request_identity
                or L._read(attestation, expected_attestation_sha256)[1] != attestation_identity
                or _assets(request) != asset_identity
                or _verify_proof(request, proof) != proof_identities):
            raise ValueError('complete recovery inputs changed before locked terminal replay')
        return locked.recover_engineering_success(expected_attested_evidence_sha256=expected_attestation_sha256)
