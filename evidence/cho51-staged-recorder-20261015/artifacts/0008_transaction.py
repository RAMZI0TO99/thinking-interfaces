"""Locked engineering recorder for explicitly reused source and restore evidence.

The supplied verifier must independently qualify the historical source and the
separately accepted staged restoration. This transaction performs no numerical
work and never upgrades the failed original parent transaction.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from core.config import config_digest
from docs.phase2.cho51_worker_lifecycle_v1 import lifecycle as L

WorkerContext = L.WorkerContext
CasePlan = L.CasePlan
CaseRecorder = L.CaseRecorder
RecoveryRequired = L.RecoveryRequired
WORKER = 'cho51_staged_source_restore_engineering'
_PATHS = ('fixture_root', 'recorder_root', 'workspace', 'pins_path', 'claim_path',
          'origin_contract_path')
_BINDINGS = ('claim_file_sha256', 'execution_source_sha256', 'independent_pins_sha256',
             'owner_decision_sha256', 'environment_sha256', 'origin_contract_file_sha256')
_INTS = dict(attempt=1, historical_gradient_updates=5253, current_gradient_updates=0,
    source_updates=5151, support_updates=102, fold_count=102, final_source_subjects=51,
    restored_tensors=21, measured_cells=0, original_case_attempts_remaining=0)
_FLAGS = dict(source_work_reused=True, restore_work_reused=True, engineering_only=True,
    scientific_admission=False, origin_parent_transaction_qualified=False)


def _only_plan(plan):
    L._plan(plan)
    if plan != CasePlan('cho2017', 'subject_02', 'eegnet', 5, 11, 1):
        raise ValueError('only adopted subject02 EEGNet seed11 five-shot engineering case admitted')


def _scope(value, *, attempt=False):
    integers = _INTS if attempt else {key: item for key, item in _INTS.items() if key != 'attempt'}
    if (any(type(getattr(value, key)) is not int or getattr(value, key) != item
            for key, item in integers.items())
            or any(getattr(value, key) is not item for key, item in _FLAGS.items())):
        raise ValueError('exact reused-source/restoration engineering scope required')


@dataclass(frozen=True, slots=True)
class StagedRequest:
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
    origin_contract_path: Path
    origin_contract_file_sha256: str
    attempt: int = 1
    historical_gradient_updates: int = 5253
    current_gradient_updates: int = 0
    source_updates: int = 5151
    support_updates: int = 102
    fold_count: int = 102
    final_source_subjects: int = 51
    restored_tensors: int = 21
    measured_cells: int = 0
    original_case_attempts_remaining: int = 0
    source_work_reused: bool = True
    restore_work_reused: bool = True
    engineering_only: bool = True
    scientific_admission: bool = False
    origin_parent_transaction_qualified: bool = False

    def __post_init__(self):
        _only_plan(self.plan)
        _scope(self, attempt=True)
        for name in _PATHS:
            L._path(getattr(self, name), name)
        for item in fields(self):
            if item.name.endswith('sha256'):
                L._sha(getattr(self, item.name), item.name)
        if (self.execution_source_sha256 != L.CANONICAL_SOURCE_SHA256
                or self.fixture_source_sha256 == self.execution_source_sha256
                or self.recorder_root != self.fixture_root / 'runs/phase2/lifecycle'
                or self.claim_path != self.recorder_root / 'claims' / (self.plan.case_id + '.attempt1.claim.json')
                or self.workspace.name != self.plan.case_id
                or self.workspace.is_relative_to(self.fixture_root)
                or self.pins_path.is_relative_to(self.fixture_root)
                or self.origin_contract_path.is_relative_to(self.fixture_root)
                or self.origin_contract_path.is_relative_to(self.workspace.parent.parent)):
            raise ValueError('fresh staged request paths and independently pinned origin differ')

    def payload(self):
        value = asdict(self)
        for name in _PATHS:
            value[name] = str(getattr(self, name))
        return dict(schema='cho51_staged_recorder_request_v1', case_id=self.plan.case_id, **value)

    @property
    def sha256(self):
        return hashlib.sha256(L._encoded(self.payload())).hexdigest()


def load_staged_request(payload):
    expected = {item.name for item in fields(StagedRequest)} | {'schema', 'case_id'}
    if (type(payload) is not dict or set(payload) != expected
            or payload.get('schema') != 'cho51_staged_recorder_request_v1'):
        raise ValueError('exact staged request schema required')
    values = {key: payload[key] for key in expected - {'schema', 'case_id'}}
    if type(values['plan']) is not dict or set(values['plan']) != {item.name for item in fields(CasePlan)}:
        raise ValueError('exact serialized adopted plan required')
    values['plan'] = CasePlan(**values['plan'])
    for name in _PATHS:
        if type(values[name]) is not str:
            raise ValueError('serialized absolute path string required')
        values[name] = Path(values[name])
    result = StagedRequest(**values)
    if result.payload() != payload:
        raise ValueError('staged request differs from exact typed reconstruction')
    return result


@dataclass(frozen=True, slots=True)
class VerifiedStagedProof:
    request_sha256: str
    case_id: str
    claim_file_sha256: str
    execution_source_sha256: str
    independent_pins_sha256: str
    owner_decision_sha256: str
    environment_sha256: str
    origin_contract_file_sha256: str
    verified_origin_files: int
    selected_state_sha256: str
    weights_file_sha256: str
    historical_gradient_updates: int = 5253
    current_gradient_updates: int = 0
    source_updates: int = 5151
    support_updates: int = 102
    fold_count: int = 102
    final_source_subjects: int = 51
    restored_tensors: int = 21
    measured_cells: int = 0
    original_case_attempts_remaining: int = 0
    source_work_reused: bool = True
    restore_work_reused: bool = True
    engineering_only: bool = True
    scientific_admission: bool = False
    origin_parent_transaction_qualified: bool = False

    def __post_init__(self):
        _scope(self)
        for item in fields(self):
            if item.name.endswith('sha256') or item.name == 'case_id':
                L._sha(getattr(self, item.name), item.name)
        if type(self.verified_origin_files) is not int or self.verified_origin_files <= 0:
            raise ValueError('positive physically verified origin file count required')


@dataclass(frozen=True, slots=True)
class StagedCompletion:
    request: StagedRequest
    proof: VerifiedStagedProof
    request_path: Path
    attestation_path: Path
    attestation_file_sha256: str
    engineering_receipt: Path


def _origin_assets(request):
    raw, identity = L._read(request.origin_contract_path, request.origin_contract_file_sha256)
    contract = json.loads(raw)
    if (type(contract) is not dict or set(contract) != {'schema', 'files', 'summary'}
            or contract.get('schema') != 'cho51_staged_recorder_origin_contract_v1'
            or raw != L._encoded(contract) or type(contract.get('files')) is not dict
            or not contract['files'] or type(contract.get('summary')) is not dict):
        raise ValueError('exact canonical pinned origin contract required')
    summary = contract['summary']
    for key, value in {**{k: v for k, v in _INTS.items() if k != 'attempt'}, **_FLAGS}.items():
        if type(summary.get(key)) is not type(value) or summary[key] != value:
            raise ValueError('origin summary differs from exact engineering reuse scope')
    if (type(summary.get('restore_limits')) is not list
            or len(summary['restore_limits']) != 2
            or any(type(value) is not int or value != 1048576 for value in summary['restore_limits'])):
        raise ValueError('both accepted historical restores must use explicit one-MiB bounds')
    for name in ('selected_state_sha256', 'weights_file_sha256'):
        L._sha(summary.get(name), name)
    result = {request.origin_contract_path: identity}
    for name, digest in contract['files'].items():
        if type(name) is not str:
            raise ValueError('absolute origin file strings required')
        path = Path(name)
        L._path(path, 'origin file')
        L._sha(digest, 'origin file pin')
        if (str(path) != name or path == request.origin_contract_path
                or path.is_relative_to(request.workspace.parent.parent)
                or path.is_relative_to(request.fixture_root)):
            raise ValueError('origin files must remain outside the fresh recorder output')
        result[path] = L._read(path, digest)[1]
    if summary['weights_file_sha256'] not in contract['files'].values():
        raise ValueError('selected weights are absent from physically pinned origin files')
    return contract, result


def _verify_proof(request, proof):
    if type(proof) is not VerifiedStagedProof:
        raise ValueError('exact immutable staged reuse proof required')
    proof.__post_init__()
    if (proof.request_sha256 != request.sha256 or proof.case_id != request.plan.case_id
            or any(getattr(proof, key) != getattr(request, key) for key in _BINDINGS)):
        raise ValueError('staged proof differs from fresh request, claim, pins or origin')
    contract, identities = _origin_assets(request)
    if (proof.verified_origin_files != len(contract['files'])
            or proof.selected_state_sha256 != contract['summary']['selected_state_sha256']
            or proof.weights_file_sha256 != contract['summary']['weights_file_sha256']):
        raise ValueError('staged proof differs from physical origin assets or selected state')
    return identities


def _claim(path, plan, context):
    raw, identity = L._read(path)
    claim = json.loads(raw)
    payload = claim.get('payload') if type(claim) is dict else None
    if (type(payload) is not dict or set(payload) != {
            'purpose', 'case', 'worker', 'attempt', 'environment_sha256', 'source', 'engineering_only'}
            or payload.get('purpose') != 'pilot_case_claim'
            or payload.get('case') != asdict(plan) or type(payload.get('attempt')) is not int or payload['attempt'] != 1
            or payload.get('worker') != WORKER or payload.get('source') != asdict(context.fixture_source)
            or payload.get('environment_sha256') != context.environment_sha256
            or payload.get('engineering_only') is not True
            or not L.verify_envelope(claim, kind='engineering_smoke', expected_payload=payload)
            or raw != L._encoded(claim)):
        raise ValueError('fresh staged engineering claim no longer verifies')
    source_sha = payload['source'].get('source_sha256')
    L._sha(source_sha, 'fixture claim source')
    return identity, source_sha


def _request_context(request, context):
    if (request.fixture_root != context.fixture_root or request.recorder_root != context.recorder_root
            or request.fixture_source_sha256 != context.fixture_source.source_sha256
            or request.workspace != context.parent_output / 'cases' / request.plan.case_id
            or any(getattr(request, key) != getattr(context, key) for key in (
                'pins_path', 'independent_pins_sha256', 'execution_source_sha256',
                'owner_decision_sha256', 'environment_sha256'))):
        raise ValueError('staged request differs from independently current context')


def _attestation(request, proof):
    return dict(schema='cho51_staged_recorder_attestation_v1', request_sha256=request.sha256,
        case_id=request.plan.case_id, claim_file_sha256=request.claim_file_sha256,
        proof=asdict(proof), source_work_reused=True, restore_work_reused=True,
        historical_gradient_updates=5253, current_gradient_updates=0,
        engineering_only=True, scientific_admission=False, measured_cells=0,
        origin_parent_transaction_qualified=False, original_case_attempts_remaining=0)


def run_staged_case(recorder, plan, *, context, workspace, origin_contract_path,
        origin_contract_file_sha256, backend, verifier):
    """Claim once and qualify metadata under the real identity lock; no fitting."""
    _only_plan(plan)
    pins_identity = L._context_check(context, recorder, plan)
    L._path(workspace, 'unused staged case workspace')
    L._future_direct(workspace)
    L._path(origin_contract_path, 'independent origin contract')
    L._sha(origin_contract_file_sha256, 'independent origin contract pin')
    if (workspace != context.parent_output / 'cases' / plan.case_id or workspace.exists()
            or workspace.is_symlink() or origin_contract_path.is_relative_to(context.parent_output)
            or not callable(backend) or not callable(verifier)):
        raise ValueError('unused staged workspace and independent metadata callbacks required')
    # Reject malformed/drifting origins before consuming a fresh claim.
    preview = StagedRequest(plan, context.fixture_root, context.recorder_root, workspace,
        context.pins_path, context.independent_pins_sha256, context.execution_source_sha256,
        context.owner_decision_sha256, context.recorder_root / 'claims' / (plan.case_id + '.attempt1.claim.json'),
        '0' * 64, context.fixture_source.source_sha256, context.environment_sha256,
        origin_contract_path, origin_contract_file_sha256)
    origin_identity = _origin_assets(preview)[1]
    request_path, attestation = workspace / 'request.json', workspace / 'parent-attestation.json'
    with recorder.case_session(plan) as locked:
        claim_path = locked.claim_new(worker=WORKER, attempt=1)
        request = None
        try:
            claim_identity, fixture_source_sha = _claim(claim_path, plan, context)
            request = StagedRequest(plan, context.fixture_root, context.recorder_root, workspace,
                context.pins_path, context.independent_pins_sha256, context.execution_source_sha256,
                context.owner_decision_sha256, claim_path, claim_identity[-1], fixture_source_sha,
                context.environment_sha256, origin_contract_path, origin_contract_file_sha256)
            if _origin_assets(request)[1] != origin_identity:
                raise ValueError('origin changed while obtaining fresh recorder claim')
            workspace.mkdir(parents=True, exist_ok=False)
            if L._write_json_once(request_path, request.payload()) != request.sha256:
                raise ValueError('durable staged request differs')
            request_identity = L._read(request_path, request.sha256)[1]
            opaque = backend(request, request_path, request.sha256)
            proof = verifier(request, opaque)
            proof_identities = _verify_proof(request, proof)

            def stable():
                if (L._context_check(context, recorder, plan) != pins_identity
                        or _claim(claim_path, plan, context)[0] != claim_identity
                        or L._read(request_path, request.sha256)[1] != request_identity
                        or _origin_assets(request)[1] != origin_identity):
                    raise ValueError('staged claim, request, context or origin changed')

            stable()
            if verifier(request, opaque) != proof or _verify_proof(request, proof) != proof_identities:
                raise ValueError('staged proof changed before durable attestation')
            stable()
            attested_sha = L._write_json_once(attestation, _attestation(request, proof))
            stable()
            if (L._read(attestation, attested_sha)[1][-1] != attested_sha
                    or _verify_proof(request, proof) != proof_identities):
                raise ValueError('durable staged proof changed before terminal publication')
            receipt = locked.record_engineering_success(attempt=1, attested_evidence_sha256=attested_sha)
            completion = recorder.completion((plan,))
            if completion['engineering_success'] != 1 or completion['measured'] != 0:
                raise ValueError('staged recorder terminal must remain engineering-only')
            return StagedCompletion(request, proof, request_path, attestation, attested_sha, receipt)
        except BaseException as error:
            if L._accepted_artifact_exists(recorder, plan, attestation):
                raise RecoveryRequired('durable staged artifact exists; explicit external-digest recovery required') from error
            locked.record_failure(attempt=1, reason=dict(purpose='cho51_staged_recorder_failure',
                error=type(error).__name__ + ': ' + str(error),
                request_sha256=None if request is None else request.sha256,
                current_gradient_updates=0, source_work_reused=True, restore_work_reused=True,
                engineering_only=True, scientific_admission=False,
                origin_parent_transaction_qualified=False, original_case_attempts_remaining=0))
            raise


def recover_staged_case(recorder, *, context, request_path, expected_request_sha256,
        expected_attestation_sha256, verifier):
    """Reverify origin and replay an existing engineering intent, without backend."""
    L._sha(expected_request_sha256, 'external staged request pin')
    L._sha(expected_attestation_sha256, 'external staged attestation pin')
    if not callable(verifier):
        raise ValueError('independent read-only origin verifier required')
    raw, request_identity = L._read(request_path, expected_request_sha256)
    request = load_staged_request(json.loads(raw))
    if raw != L._encoded(request.payload()) or request_path != request.workspace / 'request.json':
        raise ValueError('externally pinned staged request differs')
    _request_context(request, context)
    pins_identity = L._context_check(context, recorder, request.plan)
    origin_identity = _origin_assets(request)[1]
    attestation = request.workspace / 'parent-attestation.json'
    raw_attestation, attestation_identity = L._read(attestation, expected_attestation_sha256)
    payload = json.loads(raw_attestation)
    if type(payload) is not dict or type(payload.get('proof')) is not dict:
        raise ValueError('exact externally pinned staged attestation required')
    proof = VerifiedStagedProof(**payload['proof'])
    if (raw_attestation != L._encoded(payload)
            or config_digest(payload) != config_digest(_attestation(request, proof))):
        raise ValueError('externally pinned staged parent attestation differs')
    proof_identities = _verify_proof(request, proof)
    with recorder.case_session(request.plan) as locked:
        claim_identity = _claim(request.claim_path, request.plan, context)[0]
        if claim_identity[-1] != request.claim_file_sha256:
            raise ValueError('staged recovery claim differs from request')
        if verifier(request, proof) != proof:
            raise ValueError('independent origin reverification differs from durable staged proof')
        if (L._context_check(context, recorder, request.plan) != pins_identity
                or _claim(request.claim_path, request.plan, context)[0] != claim_identity
                or L._read(request_path, expected_request_sha256)[1] != request_identity
                or L._read(attestation, expected_attestation_sha256)[1] != attestation_identity
                or _origin_assets(request)[1] != origin_identity
                or _verify_proof(request, proof) != proof_identities):
            raise ValueError('staged recovery inputs changed before locked terminal replay')
        return locked.recover_engineering_success(expected_attested_evidence_sha256=expected_attestation_sha256)
