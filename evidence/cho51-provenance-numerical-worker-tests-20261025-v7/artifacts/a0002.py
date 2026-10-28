"""Locked engineering composition of accepted restoration and fresh target work."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

from core.provenance import capture_source
from docs.phase2.cho51_linear_numerical_worker_v1 import numerical_worker as LegacyNumerical
from docs.phase2.cho51_provenance_restore_v1 import factory as Factory

WorkerRoute, Lifecycle = LegacyNumerical.W, LegacyNumerical.L
WORKER = 'cho51_provenance_numerical_worker_engineering_v2'
EXPECTED_BUDGET = dict(LegacyNumerical.EXPECTED_BUDGET)
OBSERVER_COUNTS = dict(model_constructions=1, constructor_dummy_forward_calls=1,
    classifier_forward_calls=2, backbone_forward_calls=2, profile_a_loads=4,
    profile_b_loads=2, npz_loads=6, clone_reinitializations=4, empty_mask_containers=2,
    factory_restore_calls=1, factory_restore_returns=1)
RecoveryRequired = Lifecycle.RecoveryRequired


def _exact(value, expected, label):
    if not WorkerRoute._same_json(value, expected):
        raise ValueError(label + ' differs from exact bound metadata')


def _counts(value, expected, label):
    if (type(value) is not dict or set(value) != set(expected)
            or any(type(value[name]) is not int or value[name] != count for name, count in expected.items())):
        raise ValueError(label + ' requires exact integer counts')


def validate_observer(value, *, zero=False):
    expected = {name: 0 if zero else count for name, count in OBSERVER_COUNTS.items()}
    if type(value) is not dict or set(value) != set(expected) | {'numerical_calls'}:
        raise ValueError('exact independent numerical observer schema required')
    _counts({name: value[name] for name in expected}, expected, 'independent numerical observer')
    calls = value['numerical_calls']
    if (type(calls) is not dict or any(type(name) is not str or type(count) is not int or count < 0
            for name, count in calls.items())):
        raise ValueError('independent numerical calls require plain nonnegative integer counts')
    if zero:
        if any(calls.values()):
            raise ValueError('numerical work preceded the fresh backend')
    else:
        if set(calls) != {'module_load_state_dict', 'safetensors_load', 'optimizer_init',
                'sgd_step', 'tensor_backward', 'autograd_backward', 'model_module_init'}:
            raise ValueError('unexpected independent numerical operation observed')
        for name, expected_count in dict(module_load_state_dict=2, safetensors_load=2,
                optimizer_init=1, sgd_step=1, tensor_backward=1, autograd_backward=1).items():
            if calls.get(name) != expected_count or type(calls.get(name)) is not int:
                raise ValueError('independent runtime numerical call count differs: ' + name)
        if calls.get('model_module_init', 0) <= 0:
            raise ValueError('independently observed model construction required')
    return json.loads(Factory.canonical(value))


@dataclass(frozen=True, slots=True)
class NumericalWorkerRequest:
    historical_binding: WorkerRoute.WorkerRequest
    factory_request: Factory.RestoreRequest

    def __post_init__(self):
        if type(self.historical_binding) is not WorkerRoute.WorkerRequest or type(self.factory_request) is not Factory.RestoreRequest:
            raise ValueError('exact historical route and independently typed factory requests required')
        historical, factory = self.historical_binding, self.factory_request
        historical.__post_init__()
        factory.__post_init__()
        _exact(Factory._json_field(factory.plan_json), asdict(historical.plan), 'factory/worker case')
        if (Path(factory.workspace) != historical.workspace / 'factory'
                or Path(factory.claim_path) != historical.claim_path
                or factory.claim_sha256 != historical.claim_file_sha256
                or Path(factory.pins_path) != historical.pins_path
                or factory.pins_sha256 != historical.independent_pins_sha256
                or factory.producer.model_state_sha256 != historical.target_source_state_sha256):
            raise ValueError('factory subrequest must bind the same current claim, pins and selected state')
        _exact(Factory._source(factory.producer.source_json), WorkerRoute.HISTORICAL_SOURCE, 'historical producer source')
        current = Factory._source(factory.executor.source_json)
        if current['git_commit'] != historical.fixture_git_commit or current['git_dirty'] is not historical.fixture_git_dirty:
            raise ValueError('independent current executor and recorder Git roles differ')

    @property
    def plan(self):
        return self.historical_binding.plan

    @property
    def workspace(self):
        return self.historical_binding.workspace

    @property
    def fixture_root(self):
        return self.historical_binding.fixture_root

    @property
    def factory_request_path(self):
        return Path(self.factory_request.workspace) / 'request.json'

    def payload(self):
        return dict(schema='cho51_provenance_numerical_worker_request_v1',
            historical_binding=self.historical_binding.payload(), factory_request=self.factory_request.payload(),
            factory_request_sha256=self.factory_request.sha256, expected_numerical_budget=dict(EXPECTED_BUDGET),
            expected_observer_counts=dict(OBSERVER_COUNTS), engineering_only=True, scientific_admission=False,
            native_closeout_status='pending_external_post_job')

    @property
    def sha256(self):
        return hashlib.sha256(Lifecycle._encoded(self.payload())).hexdigest()


def load_worker_request(value):
    if type(value) is not dict or value.get('schema') != 'cho51_provenance_numerical_worker_request_v1':
        raise ValueError('exact provenance numerical worker schema required')
    result = NumericalWorkerRequest(WorkerRoute.load_worker_request(value['historical_binding']), Factory.load_request(value['factory_request']))
    _exact(value, result.payload(), 'immutable reconstructed outer request')
    return result


def build_current_binding(request):
    request.__post_init__()
    historical = request.historical_binding
    return dict(request_sha256=request.sha256, factory_request_sha256=request.factory_request.sha256,
        claim_sha256=historical.claim_file_sha256, pins_sha256=historical.independent_pins_sha256,
        workspace=str(request.workspace))


def _request_files(request):
    request.__post_init__()
    raw, outer = Lifecycle._read(request.workspace / 'request.json', request.sha256)
    if raw != Lifecycle._encoded(request.payload()):
        raise ValueError('physical outer worker request differs')
    factory_raw, factory_identity = Lifecycle._read(request.factory_request_path, request.factory_request.sha256)
    if factory_raw != Factory.canonical(request.factory_request.payload()).encode():
        raise ValueError('physical compact factory subrequest differs')
    historical = request.historical_binding
    claim_raw, claim_identity = Lifecycle._read(historical.claim_path, historical.claim_file_sha256)
    claim = json.loads(claim_raw)
    expected_claim = dict(purpose='pilot_case_claim', case=asdict(request.plan), worker=WORKER, attempt=1,
        environment_sha256=historical.environment_sha256,
        source=dict(git_commit=historical.fixture_git_commit, source_sha256=historical.fixture_source_sha256,
            git_dirty=historical.fixture_git_dirty), engineering_only=True)
    if claim_raw != Lifecycle._encoded(claim) or not Lifecycle.verify_envelope(claim,
            kind='engineering_smoke', expected_payload=expected_claim):
        raise ValueError('physical current claim does not bind the composed requests')
    return outer, factory_identity, claim_identity


def verify_executor_files(request):
    """Read-only current checks also work after factory consumption and terminalization."""
    factory = request.factory_request
    raw, pins_identity = Lifecycle._read(Path(factory.pins_path), factory.pins_sha256)
    pins = json.loads(raw)
    _exact(pins.get('factory_producer'), asdict(factory.producer), 'independently pinned producer')
    _exact(pins.get('factory_executor'), asdict(factory.executor), 'independently pinned executor')
    _exact(pins.get('method_config_sha256'), factory.method_config_sha256, 'independently pinned method settings')
    _exact(pins.get('store_root'), factory.store_root, 'independently pinned historical store')
    _exact(asdict(capture_source(Path(factory.executor.root))), Factory._source(factory.executor.source_json), 'actual current executor')
    current_runtime = dict(python_full=Factory.sys.version, python=Factory.platform.python_version(),
        executable=str(Path(Factory.sys.executable).resolve()),
        **{name: Factory.version(name) for name in ('torch', 'numpy', 'braindecode')})
    _exact(Factory._json_field(factory.executor.runtime_json), current_runtime, 'actual current executor runtime')
    identities = {'pins': pins_identity}
    for name, maximum, runtime_binary in (('source_files_json', Factory.MAXIMUM_JSON, False),
            ('runtime_files_json', Factory.MAXIMUM_RUNTIME, True)):
        for path, digest in Factory._json_field(getattr(factory.executor, name)).items():
            _, identity = Factory.read_pinned(Path(path), digest, maximum, retain=False, runtime_binary=runtime_binary)
            identities[path] = identity
    sources = Factory._json_field(factory.executor.source_files_json)
    for filename in ('numerical_worker.py', 'backend.py', 'pipeline.py'):
        if str(Path(__file__).with_name(filename).absolute()) not in sources:
            raise ValueError('current composed factory/worker/pipeline sources must be independently pinned')
    binaries = Factory._json_field(factory.executor.runtime_files_json)
    if any(str(Path(executable).resolve()) not in binaries for executable in (Factory.sys.executable, Factory.sys._base_executable)):
        raise ValueError('current effective interpreter binaries must remain independently pinned')
    return identities


@dataclass(frozen=True, slots=True)
class VerifiedNumericalProof:
    request_sha256: str
    factory_request_sha256: str
    case_id: str
    claim_sha256: str
    pins_sha256: str
    execution_file_sha256: str
    target_witness_file_sha256: str
    restore_witness_file_sha256: str
    factory_attempt_file_sha256: str
    backend_attempt_file_sha256: str
    adapted_state_sha256: str
    metrics_json: str
    observed_counts_json: str
    observer_json: str
    verified_origin_files: int
    native_closeout_status: str = 'pending_external_post_job'
    engineering_only: bool = True
    scientific_admission: bool = False
    measured_cells: int = 0

    def __post_init__(self):
        for field in fields(self):
            if field.name.endswith('sha256') or field.name == 'case_id':
                Lifecycle._sha(getattr(self, field.name), field.name)
        for name in ('metrics_json', 'observed_counts_json', 'observer_json'):
            Factory._json_field(getattr(self, name))
        _counts(json.loads(self.observed_counts_json), EXPECTED_BUDGET, 'aggregate numerical ledger')
        validate_observer(json.loads(self.observer_json))
        if (type(self.verified_origin_files) is not int or self.verified_origin_files <= 0
                or self.native_closeout_status != 'pending_external_post_job'
                or self.engineering_only is not True or self.scientific_admission is not False
                or type(self.measured_cells) is not int or self.measured_cells != 0):
            raise ValueError('engineering-only proof with external native closure required')


def _verify_factory_witness(request, restore):
    factory, producer = request.factory_request, request.factory_request.producer
    if (restore.get('schema') != 'cho51_provenance_restored_source_v1' or restore.get('passed') is not True
            or restore.get('complete_metadata_verified') is not True or restore.get('engineering_only') is not True
            or restore.get('scientific_admission') is not False or restore.get('unchanged_single_root_factory_verified') is not False
            or restore.get('native_closeout_status') != 'pending_external_post_job'):
        raise ValueError('accepted provenance-aware factory witness required')
    for name, expected in dict(request_sha256=factory.sha256, claim_sha256=factory.claim_sha256,
            pins_sha256=factory.pins_sha256, workspace=factory.workspace, store_root=factory.store_root,
            historical_source=Factory._source(producer.source_json),
            current_executor_source=Factory._source(factory.executor.source_json),
            current_executor_runtime=Factory._json_field(factory.executor.runtime_json),
            historical_publication_file_sha256=producer.publication_file_sha256,
            manifest_sha256=producer.manifest_sha256, manifest_file_sha256=producer.manifest_file_sha256,
            complete_evidence_sha256=producer.evidence_sha256, complete_evidence_file_sha256=producer.evidence_file_sha256,
            selection_contract_sha256=producer.selection_contract_sha256, model_recipe_sha256=producer.model_recipe_sha256,
            model_state_sha256=producer.model_state_sha256, weights_sha256=producer.weights_sha256,
            adapter_class='evaluation.phase2_pilot.LaBraMTunedAdapter').items():
        _exact(restore.get(name), expected, 'factory witness ' + name)
    local = dict(selected_restores=1, model_constructions=1, safe_decodes=2, strict_state_loads=2,
        tensor_count=223, elements=5818138, source_updates=0, support_updates=0,
        query_calls=0, measured_cells=0, maximum_weights_bytes=67108864, weights_bytes=23294624)
    _counts({name: restore.get(name) for name in local}, local, 'factory-local counts')
    attempt_sha = restore.get('restore_attempt_sha256')
    Lifecycle._sha(attempt_sha, 'consumed factory attempt')
    raw, identity = Lifecycle._read(Path(factory.workspace) / 'restore-attempt.json', attempt_sha)
    expected = dict(schema='cho51_provenance_restore_attempt_v1', request_sha256=factory.sha256,
        claim_sha256=factory.claim_sha256, pins_sha256=factory.pins_sha256, scientific_admission=False)
    if raw != Lifecycle._encoded(expected):
        raise ValueError('durable consumed factory marker differs')
    return attempt_sha, identity


def verify_current_execution(request, opaque):
    """Physically rederive a proof; never reenter the factory or numerical backend."""
    if type(request) is not NumericalWorkerRequest:
        raise ValueError('exact composed numerical request required')
    _request_files(request)
    verify_executor_files(request)
    expected = opaque.execution_file_sha256 if type(opaque) is VerifiedNumericalProof else opaque
    Lifecycle._sha(expected, 'external physical execution pin')
    raw, _ = Lifecycle._read(request.workspace / 'current-execution.json', expected)
    record = json.loads(raw)
    payload = record.get('payload') if type(record) is dict else None
    if (type(payload) is not dict or raw != Lifecycle._encoded(record)
            or not Lifecycle.verify_envelope(record, kind='engineering_smoke', expected_payload=payload)
            or payload.get('schema') != 'cho51_provenance_numerical_execution_v1'):
        raise ValueError('canonical physical composed execution envelope required')
    binding = build_current_binding(request)
    for name, value in binding.items():
        _exact(payload.get(name), value, 'current execution binding ' + name)
    if (payload.get('engineering_only') is not True or payload.get('scientific_admission') is not False
            or type(payload.get('measured_cells')) is not int or payload['measured_cells'] != 0
            or payload.get('native_closeout_status') != 'pending_external_post_job'):
        raise ValueError('running process cannot self-attest native closeout or scientific admission')
    _counts(payload.get('expected_numerical_budget'), EXPECTED_BUDGET, 'expected aggregate budget')
    _counts(payload.get('current_counter_ledger'), EXPECTED_BUDGET, 'observed aggregate budget')
    observer = validate_observer(payload.get('independent_observer'))
    historical = request.historical_binding
    current = dict(git_commit=historical.fixture_git_commit, source_sha256=historical.fixture_source_sha256,
        git_dirty=historical.fixture_git_dirty)
    _exact(payload.get('current_control_source'), current, 'current recorder/target source')
    _exact(payload.get('historical_source'), WorkerRoute.HISTORICAL_SOURCE, 'historical producer source')
    _exact(payload.get('current_executor_source'), Factory._source(request.factory_request.executor.source_json), 'current factory executor source')
    audit = dict(bytes=734579463, files=213,
        fixture_root=str(Lifecycle.ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture'),
        input_identity_file_sha256='34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
    _exact(payload.get('input_audit_before'), audit, 'complete original input audit')
    _exact(payload.get('input_audit_after'), audit, 'preserved original input audit')
    _exact(payload.get('source_fixture'), audit['fixture_root'], 'preserved source fixture')
    outputs = payload.get('physical_outputs')
    if type(outputs) is not dict or set(outputs) != {'restore-witness.json', 'target-witness.json'}:
        raise ValueError('exact physical factory and target witnesses required')
    witnesses = {}
    for filename, embedded in (('restore-witness.json', 'restore_witness'), ('target-witness.json', 'target_route_witness')):
        entry = outputs[filename]
        if (type(entry) is not dict or set(entry) != {'sha256', 'bytes'}
                or type(entry.get('bytes')) is not int or not 0 < entry['bytes'] <= Factory.MAXIMUM_JSON):
            raise ValueError('explicit physical witness byte bound required')
        witness_raw, _ = Lifecycle._read(request.workspace / filename, entry['sha256'])
        witness = json.loads(witness_raw)
        if type(witness) is not dict or witness_raw != Lifecycle._encoded(witness) or len(witness_raw) != entry['bytes']:
            raise ValueError('canonical physical witness bytes differ')
        _exact(witness, payload.get(embedded), 'embedded/physical composed witness')
        _exact(witness.get('current_worker_binding'), binding, 'outer binding on composed witness')
        witnesses[filename] = witness
    contract, _ = WorkerRoute._origin_assets(historical)
    summary = contract['summary']
    producer = request.factory_request.producer
    for name, expected_pin in dict(manifest_sha256=producer.manifest_sha256,
            complete_evidence_sha256=producer.evidence_sha256, recipe_sha256=producer.model_recipe_sha256,
            weights_file_sha256=producer.weights_sha256, selected_state_sha256=producer.model_state_sha256).items():
        _exact(summary.get(name), expected_pin, 'independent historical artifact ' + name)
    _exact(request.factory_request.protocol_config_sha256, summary['target_contract']['protocol_sha256'],
        'independent target/factory protocol')
    target, restore = witnesses['target-witness.json'], witnesses['restore-witness.json']
    if (target.get('schema') != 'cho51-linear-target-route-engineering-v1' or target.get('accepted') is not True
            or target.get('engineering_only') is not True or target.get('scientific_admission') is not False
            or target.get('source_state_sha256') != historical.target_source_state_sha256
            or target.get('profile_binding_sha256') != historical.target_profile_binding_sha256
            or target.get('caller_source_runner_source_and_adapted_storage_disjoint') is not True):
        raise ValueError('fresh genuine target witness required')
    _exact(target.get('contract'), summary['target_contract'], 'fresh target contract')
    _exact(target.get('profile_binding'), summary['target_profile_binding'], 'fresh profile binding')
    _exact(target.get('provenance'), dict(current=current, historical=WorkerRoute.HISTORICAL_SOURCE), 'target provenance roles')
    target_counts = dict(source_updates=0, support_updates=1, gradient_updates=1,
        current_restore_callback_calls=1, target_inference_calls=1, record_cell_calls=0,
        measured_cells=0, original_case_attempts_remaining=0)
    _counts({name: target.get(name) for name in target_counts}, target_counts, 'target counts')
    prior_path = Path(summary['target_proof_paths']['target_witness_file_sha256'])
    prior = json.loads(Lifecycle._read(prior_path, historical.target_witness_file_sha256)[0])
    adapted = LegacyNumerical.validate_state_witness(target, prior)
    metrics = LegacyNumerical.derive_current_metrics(target, summary['target_contract'])
    attempt_sha, _ = _verify_factory_witness(request, restore)
    backend_attempt_sha = payload.get('backend_attempt_file_sha256')
    Lifecycle._sha(backend_attempt_sha, 'consumed numerical backend attempt')
    backend_attempt_raw, _ = Lifecycle._read(request.workspace / 'backend-attempt.json', backend_attempt_sha)
    if backend_attempt_raw != Lifecycle._encoded(dict(schema='cho51_provenance_numerical_backend_attempt_v1',
            **binding, engineering_only=True, scientific_admission=False)):
        raise ValueError('durable consumed numerical backend marker differs')
    proof = VerifiedNumericalProof(request.sha256, request.factory_request.sha256, request.plan.case_id,
        historical.claim_file_sha256, historical.independent_pins_sha256, expected,
        outputs['target-witness.json']['sha256'], outputs['restore-witness.json']['sha256'], attempt_sha,
        backend_attempt_sha, adapted, Factory.canonical(metrics), Factory.canonical(payload['current_counter_ledger']),
        Factory.canonical(observer), len(contract['files']))
    if type(opaque) is VerifiedNumericalProof and opaque != proof:
        raise ValueError('supplied proof differs from fresh physical revalidation')
    return proof


def _claim(path, plan, context):
    raw, identity = Lifecycle._read(path)
    record = json.loads(raw)
    expected = dict(purpose='pilot_case_claim', case=asdict(plan), worker=WORKER, attempt=1,
        environment_sha256=context.environment_sha256, source=asdict(context.fixture_source), engineering_only=True)
    if (raw != Lifecycle._encoded(record) or not Lifecycle.verify_envelope(record, kind='engineering_smoke', expected_payload=expected)
            or not WorkerRoute._same_json(record.get('payload'), expected)):
        raise ValueError('fresh composed worker claim differs')
    return identity


def _proof_files(request, proof):
    if type(proof) is not VerifiedNumericalProof:
        raise ValueError('exact immutable composed numerical proof required')
    proof.__post_init__()
    if verify_current_execution(request, proof) != proof:
        raise ValueError('composed proof differs from independently revalidated physical evidence')
    paths = ((request.workspace / 'current-execution.json', proof.execution_file_sha256),
        (request.workspace / 'target-witness.json', proof.target_witness_file_sha256),
        (request.workspace / 'restore-witness.json', proof.restore_witness_file_sha256),
        (request.workspace / 'backend-attempt.json', proof.backend_attempt_file_sha256),
        (Path(request.factory_request.workspace) / 'restore-attempt.json', proof.factory_attempt_file_sha256))
    return {str(path): Lifecycle._read(path, digest)[1] for path, digest in paths}


def _attestation(request, proof):
    return dict(schema='cho51_provenance_numerical_attestation_v1', request_sha256=request.sha256,
        factory_request_sha256=request.factory_request.sha256, case_id=request.plan.case_id,
        proof=asdict(proof), expected_numerical_budget=EXPECTED_BUDGET,
        engineering_only=True, scientific_admission=False, measured_cells=0,
        unchanged_canonical_worker_verified=False, full_worker_verified=False,
        native_closeout_status='pending_external_post_job')


@dataclass(frozen=True, slots=True)
class WorkerCompletion:
    request: NumericalWorkerRequest
    proof: VerifiedNumericalProof
    request_path: Path
    attestation_path: Path
    attestation_file_sha256: str
    engineering_receipt: Path


def _write_factory_request(path, request):
    raw = Factory.canonical(request.payload()).encode()
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if hashlib.sha256(raw).hexdigest() != request.sha256:
        raise ValueError('durable compact factory request differs')


def run_worker_case(recorder, plan, *, context, route, workspace, origin_contract_path,
        origin_contract_file_sha256, factory_template, backend, verifier):
    """One live-lock backend, two read-only verifiers, one outer engineering terminal."""
    WorkerRoute._only_plan(plan)
    pins_identity = Lifecycle._context_check(context, recorder, plan)
    Lifecycle._path(workspace, 'composed worker workspace')
    Lifecycle._future_direct(workspace)
    if (workspace != context.parent_output / 'cases' / plan.case_id or workspace.exists()
            or workspace.is_symlink() or not callable(backend) or not callable(verifier)
            or type(factory_template) is not Factory.RestoreRequest):
        raise ValueError('unused composed workspace and explicit factory/backend/verifier required')
    Lifecycle._path(origin_contract_path, 'independent historical origin')
    if origin_contract_path.is_relative_to(context.parent_output):
        raise ValueError('historical origin must remain outside writable parent output')
    initial = json.loads(Lifecycle._read(origin_contract_path, origin_contract_file_sha256)[0])
    preview = WorkerRoute.WorkerRequest(**WorkerRoute._request_values(plan, context, workspace, origin_contract_path,
        origin_contract_file_sha256, initial['summary']))
    origin, origin_identity = WorkerRoute._origin_assets(preview)
    WorkerRoute._check_route(route, preview, context, origin)
    NumericalWorkerRequest(preview, replace(factory_template, claim_sha256=preview.claim_file_sha256))
    request_path, attestation = workspace / 'request.json', workspace / 'parent-attestation.json'
    with recorder.case_session(plan) as locked:
        claim_path = locked.claim_new(worker=WORKER, attempt=1)
        request, backend_started = None, False
        try:
            claim_identity = _claim(claim_path, plan, context)
            historical = WorkerRoute.WorkerRequest(**WorkerRoute._request_values(plan, context, workspace, origin_contract_path,
                origin_contract_file_sha256, initial['summary'], claim_identity[-1]))
            request = NumericalWorkerRequest(historical, replace(factory_template, claim_sha256=claim_identity[-1]))
            if WorkerRoute._origin_assets(historical)[1] != origin_identity:
                raise ValueError('historical origin changed during fresh claim')
            workspace.mkdir(parents=True, exist_ok=False)
            Path(request.factory_request.workspace).mkdir(exist_ok=False)
            _write_factory_request(request.factory_request_path, request.factory_request)
            if Lifecycle._write_json_once(request_path, request.payload()) != request.sha256:
                raise ValueError('durable outer request differs')
            request_identities = _request_files(request)
            executor_identities = verify_executor_files(request)

            def stable():
                locked._require_active()
                if (Lifecycle._context_check(context, recorder, plan) != pins_identity
                        or _claim(claim_path, plan, context) != claim_identity
                        or _request_files(request) != request_identities
                        or verify_executor_files(request) != executor_identities
                        or WorkerRoute._origin_assets(historical)[1] != origin_identity):
                    raise ValueError('composed request/claim/context/origin changed')
                WorkerRoute._check_route(route, historical, context, origin)

            stable()
            backend_started = True
            opaque = backend(request, request_path, request.sha256, locked._require_active)
            proof = verifier(request, opaque)
            physical = _proof_files(request, proof)
            stable()
            if verifier(request, opaque) != proof or _proof_files(request, proof) != physical:
                raise ValueError('composed proof changed before outer attestation')
            stable()
            attested_sha = Lifecycle._write_json_once(attestation, _attestation(request, proof))
            stable()
            if Lifecycle._read(attestation, attested_sha)[1][-1] != attested_sha or _proof_files(request, proof) != physical:
                raise ValueError('composed proof changed before engineering terminal')
            receipt = locked.record_engineering_success(attempt=1, attested_evidence_sha256=attested_sha)
            completed = recorder.completion((plan,))
            if completed['engineering_success'] != 1 or completed['measured'] != 0:
                raise ValueError('composed worker terminal must remain engineering-only')
            return WorkerCompletion(request, proof, request_path, attestation, attested_sha, receipt)
        except BaseException as error:
            if Lifecycle._accepted_artifact_exists(recorder, plan, attestation):
                raise RecoveryRequired('outer attestation exists; externally pinned read-only recovery required') from error
            locked.record_failure(attempt=1, reason=dict(purpose='cho51_provenance_numerical_failure',
                error=type(error).__name__ + ': ' + str(error),
                request_sha256=None if request is None else request.sha256, backend_started=backend_started,
                numerical_execution_status='incomplete_unknown' if backend_started else 'not_started',
                observed_numerical_counts=None if backend_started else {name: 0 for name in EXPECTED_BUDGET},
                expected_numerical_budget=EXPECTED_BUDGET, replay_permitted=False,
                engineering_only=True, scientific_admission=False, measured_cells=0,
                native_closeout_status='pending_external_post_job'))
            raise


def recover_worker_case(recorder, *, context, route, request_path, expected_request_sha256,
        expected_attestation_sha256, verifier):
    """Revalidate physical evidence and replay only an existing outer intent."""
    Lifecycle._sha(expected_request_sha256, 'external composed request pin')
    Lifecycle._sha(expected_attestation_sha256, 'external outer attestation pin')
    if not callable(verifier):
        raise ValueError('independent read-only verifier required for recovery')
    raw, request_identity = Lifecycle._read(request_path, expected_request_sha256)
    request = load_worker_request(json.loads(raw))
    if raw != Lifecycle._encoded(request.payload()) or request_path != request.workspace / 'request.json':
        raise ValueError('externally pinned composed request differs')
    historical = request.historical_binding
    WorkerRoute._request_context(historical, context)
    pins_identity = Lifecycle._context_check(context, recorder, request.plan)
    pair_identity = _request_files(request)
    executor_identity = verify_executor_files(request)
    origin, origin_identity = WorkerRoute._origin_assets(historical)
    WorkerRoute._check_route(route, historical, context, origin)
    attestation = request.workspace / 'parent-attestation.json'
    raw_attestation, attestation_identity = Lifecycle._read(attestation, expected_attestation_sha256)
    payload = json.loads(raw_attestation)
    proof = VerifiedNumericalProof(**payload['proof'])
    _exact(payload, _attestation(request, proof), 'externally pinned composed attestation')
    if raw_attestation != Lifecycle._encoded(payload):
        raise ValueError('canonical composed attestation required')
    physical = _proof_files(request, proof)
    with recorder.case_session(request.plan) as locked:
        claim_identity = _claim(historical.claim_path, request.plan, context)
        if claim_identity[-1] != historical.claim_file_sha256 or verifier(request, proof) != proof:
            raise ValueError('read-only recovery claim/proof differs')
        if (Lifecycle._context_check(context, recorder, request.plan) != pins_identity
                or _claim(historical.claim_path, request.plan, context) != claim_identity
                or _request_files(request) != pair_identity or verify_executor_files(request) != executor_identity
                or Lifecycle._read(request_path, expected_request_sha256)[1] != request_identity
                or Lifecycle._read(attestation, expected_attestation_sha256)[1] != attestation_identity
                or WorkerRoute._origin_assets(historical)[1] != origin_identity or _proof_files(request, proof) != physical):
            raise ValueError('physical recovery inputs changed before existing intent replay')
        WorkerRoute._check_route(route, historical, context, origin)
        return locked.recover_engineering_success(expected_attested_evidence_sha256=expected_attestation_sha256)
