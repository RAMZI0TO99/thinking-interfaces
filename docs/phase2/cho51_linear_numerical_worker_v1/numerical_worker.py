"""Fresh numerical engineering transaction, separate from frozen metadata reuse.

The backend executes under an independently admitted native guard. This module
checks metadata and physical witnesses; it does not construct or execute models.
Native closeout can only be qualified externally after this process has exited.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, fields
from fractions import Fraction
from pathlib import Path

from core.config import config_digest
from docs.phase2.cho51_linear_worker_route_v3 import worker_route as W

L = W.L
WorkerContext = W.WorkerContext
CaseRecorder = W.CaseRecorder
CasePlan = W.CasePlan
RecoveryRequired = W.RecoveryRequired
WORKER = 'cho51_linear_numerical_worker_engineering_v1'
HEAD_NAMES = ('head.weight', 'head.bias')
EXPECTED_BUDGET = dict(source_updates=0, restore_count=1, support_updates=1,
    gradient_updates=1, target_inference_calls=1, query_count=2,
    model_constructions=1, measured_cells=0)


def _exact(value, expected, label):
    if not W._same_json(value, expected):
        raise ValueError(label + ' differs from the exact bound metadata')


@dataclass(frozen=True, slots=True)
class NumericalWorkerRequest:
    """Frozen W binding is historical metadata; expected counts are permissions."""
    historical_binding: W.WorkerRequest
    expected_budget_json: str = json.dumps(EXPECTED_BUDGET, sort_keys=True, separators=(',', ':'))
    engineering_only: bool = True
    scientific_admission: bool = False
    native_closeout_status: str = 'pending_external_post_job'

    def __post_init__(self):
        if type(self.historical_binding) is not W.WorkerRequest:
            raise ValueError('exact frozen historical binding required')
        self.historical_binding.__post_init__()
        if (type(self.expected_budget_json) is not str
                or self.expected_budget_json != json.dumps(EXPECTED_BUDGET, sort_keys=True, separators=(',', ':'))
                or self.engineering_only is not True or self.scientific_admission is not False
                or self.native_closeout_status != 'pending_external_post_job'):
            raise ValueError('exact fresh numerical engineering budget and external closeout boundary required')

    @property
    def plan(self):
        return self.historical_binding.plan

    @property
    def workspace(self):
        return self.historical_binding.workspace

    @property
    def fixture_root(self):
        return self.historical_binding.fixture_root

    def payload(self):
        return dict(schema='cho51_linear_numerical_worker_request_v1',
            historical_binding=self.historical_binding.payload(),
            expected_numerical_budget=json.loads(self.expected_budget_json),
            engineering_only=True, scientific_admission=False,
            native_closeout_status='pending_external_post_job')

    @property
    def sha256(self):
        return hashlib.sha256(L._encoded(self.payload())).hexdigest()


def load_worker_request(payload):
    if (type(payload) is not dict or set(payload) != {'schema', 'historical_binding',
            'expected_numerical_budget', 'engineering_only', 'scientific_admission', 'native_closeout_status'}
            or payload.get('schema') != 'cho51_linear_numerical_worker_request_v1'):
        raise ValueError('exact fresh numerical worker request schema required')
    _exact(payload['expected_numerical_budget'], EXPECTED_BUDGET, 'expected numerical budget')
    request = NumericalWorkerRequest(W.load_worker_request(payload['historical_binding']),
        engineering_only=payload['engineering_only'], scientific_admission=payload['scientific_admission'],
        native_closeout_status=payload['native_closeout_status'])
    _exact(request.payload(), payload, 'typed numerical request reconstruction')
    return request


def build_current_binding(request):
    request.__post_init__()
    h = request.historical_binding
    return dict(request_sha256=request.sha256, claim_sha256=h.claim_file_sha256,
        pins_sha256=h.independent_pins_sha256, workspace=str(request.workspace))


def derive_current_metrics(value, target_contract):
    """Derive any finite two-query result; no historical prediction is imposed."""
    logits, labels = value.get('query_logits'), value.get('query_targets')
    if (type(logits) is not list or len(logits) != 2
            or any(type(row) is not list or len(row) != 2 for row in logits)
            or any(type(v) not in (int, float) or not math.isfinite(v) for row in logits for v in row)
            or type(labels) is not list or any(type(v) is not int or v not in (0, 1) for v in labels)
            or labels != target_contract['query_labels'] or sorted(labels) != [0, 1]):
        raise ValueError('finite two-row logits and route-derived query labels required')
    predictions = [0 if row[0] >= row[1] else 1 for row in logits]
    confusion = [[0, 0], [0, 0]]
    for label, prediction in zip(labels, predictions, strict=True):
        confusion[label][prediction] += 1
    score = sum((Fraction(confusion[i][i], sum(confusion[i])) for i in range(2)), Fraction()) / 2
    result = dict(query_logits=logits, query_targets=labels, query_predictions=predictions,
        confusion_matrix=confusion, balanced_accuracy=[score.numerator, score.denominator],
        query_count=2, correct_query_predictions=sum(a == b for a, b in zip(labels, predictions, strict=True)),
        scientific_predictive_performance_qualified=False)
    for key in ('confusion_matrix', 'balanced_accuracy', 'query_count'):
        _exact(value.get(key), result[key], 'fresh ' + key)
    return result


def validate_state_witness(target, historical_target):
    """Check full inventory/head transition; aggregate raw digest is observer data."""
    source, observed = target.get('source_state_tensors'), target.get('witnesses')
    if type(source) is not dict or type(observed) is not dict:
        raise ValueError('complete physical source and adaptation witness required')
    before, after = observed.get('before_state_tensors'), observed.get('after_state_tensors')
    if (type(before) is not dict or type(after) is not dict or len(before) != 223
            or set(source) != set(before) or set(after) != set(before)
            or not set(HEAD_NAMES).issubset(before)):
        raise ValueError('complete matching223 source/before/after tensor inventory required')
    for mapping in (source, before, after):
        for name, digest in mapping.items():
            if type(name) is not str:
                raise ValueError('plain tensor names required')
            L._sha(digest, 'tensor witness')
    _exact(before, source, 'restored source/before tensor map')
    if historical_target is not None:
        _exact(source, historical_target['source_state_tensors'], 'authenticated selected source tensor map')
    changed = [name for name in before if before[name] != after[name]]
    if set(changed) != set(HEAD_NAMES):
        raise ValueError('both head tensors must change and all221 backbone/buffer tensors remain frozen')
    reported = observed.get('changed_state_names')
    if type(reported) is not list or len(reported) != 2 or any(type(v) is not str for v in reported) or set(reported) != set(HEAD_NAMES):
        raise ValueError('exact two observed head changes required')
    _exact(observed.get('calls'), dict(adaptation=1, support_forward=1, backward=1,
        sgd_step=1, query_forward=1, runner_prediction=1), 'canonical observer calls')
    mask = observed.get('mask')
    if (type(mask) is not dict or mask.get('method') != 'linear'
            or type(mask.get('trainable_parameters')) is not int or mask['trainable_parameters'] != 402
            or mask.get('trainable_names') != list(HEAD_NAMES)
            or type(mask.get('depth')) is not int or mask['depth'] != 0
            or mask.get('selected_blocks') != []):
        raise ValueError('exact402-parameter head-only mask required')
    for key in ('finite_gradients', 'query_inference_mode', 'all_modules_eval', 'source_unchanged',
            'backbone_and_buffers_unchanged', 'owned_source_and_adapted_storage_disjoint'):
        if observed.get(key) is not True:
            raise ValueError('fresh true observer boundary required: ' + key)
    for key in ('query_labels_used_for_adaptation', 'unused_pool_used_for_adaptation'):
        if observed.get(key) is not False:
            raise ValueError('query and unused rows must remain excluded from adaptation')
    gradients, norms = observed.get('gradient_sha256'), observed.get('gradient_norms')
    if type(gradients) is not dict or set(gradients) != set(HEAD_NAMES) or type(norms) is not dict or set(norms) != set(HEAD_NAMES):
        raise ValueError('both head gradient hashes/norms required')
    for name in HEAD_NAMES:
        L._sha(gradients[name], 'head gradient')
        if type(norms[name]) not in (int, float) or not math.isfinite(norms[name]) or norms[name] <= 0:
            raise ValueError('finite positive observed head gradient norm required')
    losses = observed.get('support_losses')
    if type(losses) is not list or len(losses) != 1 or type(losses[0]) not in (int, float) or not math.isfinite(losses[0]):
        raise ValueError('one finite support loss required')
    _exact(observed.get('classifier_input_shapes'), [[10, 64, 800], [2, 64, 800]],
        'support/query classifier input shapes')
    L._sha(observed.get('adapted_state_sha256'), 'observer raw aggregate adapted state')
    # state_digest hashes raw tensors, not these per-tensor digests. Its observed
    # aggregate is authenticated by the physical target witness and source pins.
    return observed['adapted_state_sha256']


@dataclass(frozen=True, slots=True)
class VerifiedNumericalProof:
    request_sha256: str
    case_id: str
    claim_sha256: str
    pins_sha256: str
    execution_file_sha256: str
    target_witness_file_sha256: str
    restore_witness_file_sha256: str
    adapted_state_sha256: str
    metrics_json: str
    observed_counts_json: str
    verified_origin_files: int
    native_closeout_status: str = 'pending_external_post_job'
    engineering_only: bool = True
    scientific_admission: bool = False
    measured_cells: int = 0

    def __post_init__(self):
        for item in fields(self):
            if item.name.endswith('sha256') or item.name == 'case_id':
                L._sha(getattr(self, item.name), item.name)
        for name in ('metrics_json', 'observed_counts_json'):
            value = getattr(self, name)
            if type(value) is not str or type(json.loads(value)) is not dict or json.dumps(json.loads(value), sort_keys=True, separators=(',', ':'), allow_nan=False) != value:
                raise ValueError('immutable canonical finite JSON proof maps required')
        _exact(json.loads(self.observed_counts_json), EXPECTED_BUDGET, 'observed numerical counts')
        if (type(self.verified_origin_files) is not int or self.verified_origin_files <= 0
                or self.native_closeout_status != 'pending_external_post_job'
                or self.engineering_only is not True or self.scientific_admission is not False
                or type(self.measured_cells) is not int or self.measured_cells != 0):
            raise ValueError('engineering-only proof with pending external native closure required')


def _json_text(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def verify_current_execution(request, opaque):
    """Read-only independent validation of a request-bound physical fresh witness."""
    if type(request) is not NumericalWorkerRequest:
        raise ValueError('exact numerical request required')
    request.__post_init__()
    expected = opaque.execution_file_sha256 if type(opaque) is VerifiedNumericalProof else opaque
    L._sha(expected, 'external current execution digest')
    h = request.historical_binding
    raw, _ = L._read(request.workspace / 'current-execution.json', expected)
    envelope = json.loads(raw)
    payload = envelope.get('payload') if type(envelope) is dict else None
    if (type(payload) is not dict or raw != L._encoded(envelope)
            or not L.verify_envelope(envelope, kind='engineering_smoke', expected_payload=payload)
            or payload.get('schema') != 'cho51_linear_numerical_execution_v1'):
        raise ValueError('canonical physical current execution envelope required')
    binding = build_current_binding(request)
    for name, value in binding.items():
        _exact(payload.get(name), value, 'fresh envelope ' + name)
    if (payload.get('engineering_only') is not True or payload.get('scientific_admission') is not False
            or type(payload.get('measured_cells')) is not int or payload['measured_cells'] != 0
            or payload.get('native_closeout_status') != 'pending_external_post_job'):
        raise ValueError('current process cannot self-attest native cleanup or scientific admission')
    _exact(payload.get('expected_numerical_budget'), EXPECTED_BUDGET, 'expected budget')
    _exact(payload.get('current_counter_ledger'), EXPECTED_BUDGET, 'complete observed current ledger')
    calls = payload.get('observed_numerical_calls')
    if type(calls) is not dict or not calls or any(type(k) is not str or type(v) is not int or v < 0 for k, v in calls.items()):
        raise ValueError('independent observed nonnegative numerical call map required')
    for key, count in dict(module_load_state_dict=2, safetensors_load=2, optimizer_init=1,
            sgd_step=1, tensor_backward=1, autograd_backward=1).items():
        if calls.get(key) != count:
            raise ValueError('independent runtime numerical call count differs: ' + key)
    if calls.get('model_module_init', 0) <= 0:
        raise ValueError('actual model module construction observation required')
    _exact(payload.get('current_control_source'), dict(git_commit=h.fixture_git_commit,
        source_sha256=h.fixture_source_sha256, git_dirty=h.fixture_git_dirty), 'fresh fixture source')
    _exact(payload.get('historical_source'), W.HISTORICAL_SOURCE, 'historical source')
    audit = payload.get('input_audit_before')
    expected_audit = dict(bytes=734579463, files=213,
        fixture_root=str(L.ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture'),
        input_identity_file_sha256='34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
    _exact(audit, expected_audit, 'complete original numerical input audit')
    if payload.get('source_fixture') != expected_audit['fixture_root']:
        raise ValueError('preserved independent numerical source fixture required')
    _exact(payload.get('input_audit_after'), audit, 'preserved numerical input audit')
    outputs = payload.get('physical_outputs')
    if type(outputs) is not dict or set(outputs) != {'restore-witness.json', 'target-witness.json'}:
        raise ValueError('exact two fresh physical numerical outputs required')
    witnesses = {}
    for filename, embedded in (('restore-witness.json', 'restore_witness'), ('target-witness.json', 'target_route_witness')):
        entry = outputs[filename]
        if type(entry) is not dict or set(entry) != {'sha256', 'bytes'} or type(entry.get('bytes')) is not int:
            raise ValueError('exact physical output digest/size required')
        L._sha(entry.get('sha256'), 'physical numerical witness digest')
        witness_raw, _ = L._read(request.workspace / filename, entry['sha256'])
        witness = json.loads(witness_raw)
        if witness_raw != L._encoded(witness) or len(witness_raw) != entry['bytes'] or type(witness) is not dict:
            raise ValueError('canonical stable physical numerical witness required')
        _exact(witness, payload.get(embedded), 'embedded/physical fresh witness')
        _exact(witness.get('current_worker_binding'), binding, 'fresh numerical witness request binding')
        witnesses[filename] = witness
    contract, _ = W._origin_assets(h)
    summary = contract['summary']
    target, restore = witnesses['target-witness.json'], witnesses['restore-witness.json']
    if (target.get('schema') != 'cho51-linear-target-route-engineering-v1' or target.get('accepted') is not True
            or target.get('engineering_only') is not True or target.get('scientific_admission') is not False
            or target.get('source_state_sha256') != h.target_source_state_sha256
            or target.get('profile_binding_sha256') != h.target_profile_binding_sha256):
        raise ValueError('fresh accepted target witness with exact selected source/profile required')
    _exact(target.get('contract'), summary['target_contract'], 'fresh target contract')
    _exact(target.get('profile_binding'), summary['target_profile_binding'], 'fresh target profile binding')
    _exact(target.get('provenance'), dict(current=payload['current_control_source'],
        historical=W.HISTORICAL_SOURCE), 'fresh target source provenance')
    for key, value in dict(source_updates=0, support_updates=1, gradient_updates=1,
            current_restore_callback_calls=1, target_inference_calls=1, record_cell_calls=0,
            measured_cells=0, original_case_attempts_remaining=0).items():
        if type(target.get(key)) is not int or target[key] != value:
            raise ValueError('fresh target numerical count differs: ' + key)
    if target.get('caller_source_runner_source_and_adapted_storage_disjoint') is not True:
        raise ValueError('fresh caller/runner/adapted storage disjointness required')
    prior = json.loads(L._read(Path(summary['target_proof_paths']['target_witness_file_sha256']),
        h.target_witness_file_sha256)[0])
    adapted = validate_state_witness(target, prior)
    metrics = derive_current_metrics(target, summary['target_contract'])
    if (restore.get('schema') != 'cho51_linear_target_staged_restore_v1' or restore.get('passed') is not True
            or restore.get('scientific_admission') is not False
            or restore.get('selected_state_sha256') != h.target_source_state_sha256
            or restore.get('weights_file_sha256') != summary['weights_file_sha256']
            or restore.get('new_explicit_two_root_staged_restore_verified') is not True
            or restore.get('source_backbone_unchanged') is not True
            or restore.get('unchanged_canonical_store_restore_verified') is not False
            or restore.get('unchanged_single_root_factory_verified') is not False):
        raise ValueError('fresh explicit staged restore witness required')
    for key, value in dict(current_restore_count=1, baseline_decodes=1, selected_decodes=1,
            strict_state_loads=2, tensor_count=223, elements=5818138, head_parameters=402,
            weights_limit_bytes=67108864, weights_bytes=23294624, measured_cells=0).items():
        if type(restore.get(key)) is not int or restore[key] != value:
            raise ValueError('fresh restore numerical witness differs: ' + key)
    _exact(restore.get('current_control_source'), payload['current_control_source'], 'restore current source')
    _exact(restore.get('historical_source'), W.HISTORICAL_SOURCE, 'restore historical source')
    if restore.get('complete_evidence_file_sha256') != W._ROLE_SPECS['complete_evidence'][2]:
        raise ValueError('fresh restore must authenticate exact historical complete evidence file')
    proof = VerifiedNumericalProof(request.sha256, request.plan.case_id, h.claim_file_sha256,
        h.independent_pins_sha256, expected, outputs['target-witness.json']['sha256'],
        outputs['restore-witness.json']['sha256'], adapted, _json_text(metrics),
        _json_text(payload['current_counter_ledger']), len(contract['files']))
    if type(opaque) is VerifiedNumericalProof and opaque != proof:
        raise ValueError('recovery proof differs from fresh physical reverification')
    return proof


def _claim(path, plan, context):
    raw, identity = L._read(path)
    claim = json.loads(raw)
    payload = claim.get('payload') if type(claim) is dict else None
    expected = dict(purpose='pilot_case_claim', case=asdict(plan), worker=WORKER, attempt=1,
        environment_sha256=context.environment_sha256, source=asdict(context.fixture_source), engineering_only=True)
    if raw != L._encoded(claim) or not L.verify_envelope(claim, kind='engineering_smoke', expected_payload=expected) or not W._same_json(payload, expected):
        raise ValueError('fresh numerical worker claim differs')
    return identity


def _verify_proof(request, proof):
    if type(proof) is not VerifiedNumericalProof:
        raise ValueError('exact immutable numerical proof required')
    proof.__post_init__()
    if verify_current_execution(request, proof) != proof:
        raise ValueError('numerical proof differs from physical evidence')
    return {path: L._read(path, expected)[1] for path, expected in (
        (request.workspace / 'current-execution.json', proof.execution_file_sha256),
        (request.workspace / 'target-witness.json', proof.target_witness_file_sha256),
        (request.workspace / 'restore-witness.json', proof.restore_witness_file_sha256))}


def _attestation(request, proof):
    return dict(schema='cho51_linear_numerical_worker_attestation_v1',
        request_sha256=request.sha256, case_id=request.plan.case_id,
        historical_binding_sha256=request.historical_binding.sha256,
        proof=asdict(proof), expected_numerical_budget=EXPECTED_BUDGET,
        observed_numerical_counts=json.loads(proof.observed_counts_json),
        engineering_only=True, scientific_admission=False, measured_cells=0,
        native_closeout_status='pending_external_post_job', unchanged_canonical_worker_verified=False,
        unchanged_single_root_factory_verified=False, full_worker_verified=False)


@dataclass(frozen=True, slots=True)
class WorkerCompletion:
    request: NumericalWorkerRequest
    proof: VerifiedNumericalProof
    request_path: Path
    attestation_path: Path
    attestation_file_sha256: str
    engineering_receipt: Path


def run_worker_case(recorder, plan, *, context, route, workspace, origin_contract_path,
        origin_contract_file_sha256, backend, verifier):
    """One fresh claimed numerical backend and two read-only verifications."""
    W._only_plan(plan)
    pins_identity = L._context_check(context, recorder, plan)
    L._path(workspace, 'fresh numerical worker workspace')
    L._future_direct(workspace)
    L._path(origin_contract_path, 'independent historical origin')
    L._sha(origin_contract_file_sha256, 'independent historical origin pin')
    if (workspace != context.parent_output / 'cases' / plan.case_id or workspace.exists()
            or workspace.is_symlink() or origin_contract_path.is_relative_to(context.parent_output)
            or not callable(backend) or not callable(verifier)):
        raise ValueError('unused numerical workspace and explicit backend/verifier required')
    initial = json.loads(L._read(origin_contract_path, origin_contract_file_sha256)[0])
    if type(initial) is not dict or type(initial.get('summary')) is not dict:
        raise ValueError('independently pinned historical origin summary required')
    preview = W.WorkerRequest(**W._request_values(plan, context, workspace, origin_contract_path,
        origin_contract_file_sha256, initial['summary']))
    origin, origin_identity = W._origin_assets(preview)
    W._check_route(route, preview, context, origin)
    request_path, attestation = workspace / 'request.json', workspace / 'parent-attestation.json'
    with recorder.case_session(plan) as locked:
        claim_path = locked.claim_new(worker=WORKER, attempt=1)
        request, backend_started = None, False
        try:
            claim_identity = _claim(claim_path, plan, context)
            historical = W.WorkerRequest(**W._request_values(plan, context, workspace, origin_contract_path,
                origin_contract_file_sha256, initial['summary'], claim_identity[-1]))
            request = NumericalWorkerRequest(historical)
            if W._origin_assets(historical)[1] != origin_identity:
                raise ValueError('historical origin changed during numerical claim')
            workspace.mkdir(parents=True, exist_ok=False)
            if L._write_json_once(request_path, request.payload()) != request.sha256:
                raise ValueError('fresh durable numerical request differs')
            request_identity = L._read(request_path, request.sha256)[1]

            def stable():
                if (L._context_check(context, recorder, plan) != pins_identity
                        or _claim(claim_path, plan, context) != claim_identity
                        or L._read(request_path, request.sha256)[1] != request_identity
                        or W._origin_assets(historical)[1] != origin_identity):
                    raise ValueError('numerical request/claim/context/origin changed')
                W._check_route(route, historical, context, origin)

            backend_started = True
            opaque = backend(request, request_path, request.sha256)
            proof = verifier(request, opaque)
            proof_identities = _verify_proof(request, proof)
            stable()
            if verifier(request, opaque) != proof or _verify_proof(request, proof) != proof_identities:
                raise ValueError('fresh numerical proof changed before durable attestation')
            stable()
            attested_sha = L._write_json_once(attestation, _attestation(request, proof))
            stable()
            if L._read(attestation, attested_sha)[1][-1] != attested_sha or _verify_proof(request, proof) != proof_identities:
                raise ValueError('fresh numerical proof changed before engineering terminal')
            receipt = locked.record_engineering_success(attempt=1, attested_evidence_sha256=attested_sha)
            completion = recorder.completion((plan,))
            if completion['engineering_success'] != 1 or completion['measured'] != 0:
                raise ValueError('numerical worker terminal must remain engineering-only')
            return WorkerCompletion(request, proof, request_path, attestation, attested_sha, receipt)
        except BaseException as error:
            if L._accepted_artifact_exists(recorder, plan, attestation):
                raise RecoveryRequired('durable numerical attestation exists; externally pinned read-only recovery required') from error
            locked.record_failure(attempt=1, reason=dict(purpose='cho51_linear_numerical_worker_failure',
                error=type(error).__name__ + ': ' + str(error),
                request_sha256=None if request is None else request.sha256,
                backend_started=backend_started, numerical_execution_status='incomplete_unknown' if backend_started else 'not_started',
                observed_numerical_counts=None if backend_started else {key: 0 for key in EXPECTED_BUDGET},
                expected_numerical_budget=EXPECTED_BUDGET, replay_permitted=False,
                engineering_only=True, scientific_admission=False, measured_cells=0,
                native_closeout_status='pending_external_post_job'))
            raise


def recover_worker_case(recorder, *, context, route, request_path, expected_request_sha256,
        expected_attestation_sha256, verifier):
    """Reverify externally pinned evidence and existing intent; never call backend."""
    L._sha(expected_request_sha256, 'external numerical request pin')
    L._sha(expected_attestation_sha256, 'external numerical attestation pin')
    if not callable(verifier):
        raise ValueError('independent read-only numerical verifier required')
    raw, request_identity = L._read(request_path, expected_request_sha256)
    request = load_worker_request(json.loads(raw))
    h = request.historical_binding
    if raw != L._encoded(request.payload()) or request_path != request.workspace / 'request.json':
        raise ValueError('externally pinned numerical request differs')
    W._request_context(h, context)
    pins_identity = L._context_check(context, recorder, request.plan)
    origin, origin_identity = W._origin_assets(h)
    W._check_route(route, h, context, origin)
    attestation = request.workspace / 'parent-attestation.json'
    raw_attestation, attestation_identity = L._read(attestation, expected_attestation_sha256)
    payload = json.loads(raw_attestation)
    if type(payload) is not dict or type(payload.get('proof')) is not dict:
        raise ValueError('exact numerical attestation required')
    proof = VerifiedNumericalProof(**payload['proof'])
    if raw_attestation != L._encoded(payload):
        raise ValueError('canonical numerical attestation required')
    _exact(payload, _attestation(request, proof), 'externally pinned numerical attestation')
    proof_identities = _verify_proof(request, proof)
    with recorder.case_session(request.plan) as locked:
        claim_identity = _claim(h.claim_path, request.plan, context)
        if claim_identity[-1] != h.claim_file_sha256 or verifier(request, proof) != proof:
            raise ValueError('fresh numerical recovery claim/proof differs')
        W._check_route(route, h, context, origin)
        if (L._context_check(context, recorder, request.plan) != pins_identity
                or _claim(h.claim_path, request.plan, context) != claim_identity
                or L._read(request_path, expected_request_sha256)[1] != request_identity
                or L._read(attestation, expected_attestation_sha256)[1] != attestation_identity
                or W._origin_assets(h)[1] != origin_identity
                or _verify_proof(request, proof) != proof_identities):
            raise ValueError('numerical recovery evidence changed before engineering intent replay')
        return locked.recover_engineering_success(expected_attested_evidence_sha256=expected_attestation_sha256)
