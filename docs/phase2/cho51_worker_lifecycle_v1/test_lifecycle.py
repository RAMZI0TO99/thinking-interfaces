"""Real recorder transactions with mocked engineering backend/native verifier.

The fixture source capture is replaced only in these owned unit fixtures.
No numerical model, native child, study asset, selector or measured cell runs.
"""
from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from dataclasses import asdict, fields, replace
from types import SimpleNamespace

import pytest

from core.provenance import SourceProvenance
from docs.phase2.cho51_worker_lifecycle_v1 import lifecycle as L
from evaluation.phase2_records import envelope


def _sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


def _unchecked(value, **changes):
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


@pytest.fixture(scope='module')
def adopted():
    return tuple(L.CasePlan('cho2017', f'subject_{s:02d}', m, 5, seed, 1)
                 for s in range(2, 53) for m in L.METHODS for seed in L.SEEDS)


@pytest.fixture
def fixture(tmp_path, monkeypatch, adopted):
    parent = tmp_path / 'p'
    root = parent / 'f'
    root.mkdir(parents=True)
    source = SourceProvenance('a' * 40, _sha('owned-fabricated-fixture-source'), True)
    state = SimpleNamespace(events=[], source=source, drift_environment=False, fail=None, proof_change=None,
                            backend_change=None, verifier_change=None, verifier_calls=0)
    environment = L.recorder_module.environment_digest()
    original_environment = L.recorder_module.environment_digest
    def capture(path):
        assert path == root
        return state.source
    monkeypatch.setattr(L.recorder_module, 'capture_source', capture)
    monkeypatch.setattr(L.recorder_module, 'environment_digest', lambda: _sha('changed-environment') if state.drift_environment else original_environment())
    # Only the synthetic native-file anchor is redirected to owned temporary
    # files. No actual Job receipt or native execution is represented here.
    monkeypatch.setattr(L, 'ROOT', tmp_path)
    owner = _sha('owner')
    pins_path = tmp_path / 'pins.json'
    L._write_json_once(pins_path, dict(canonical_source_sha256=L.CANONICAL_SOURCE_SHA256, owner_decision_sha256=owner))
    context = L.WorkerContext(parent, root, root / 'runs/phase2/lifecycle', pins_path,
        hashlib.sha256(pins_path.read_bytes()).hexdigest(), L.CANONICAL_SOURCE_SHA256, owner, adopted, source, environment)
    recorder = L.CaseRecorder(root, output_root=context.recorder_root)
    plan = next(p for p in adopted if p.target_subject == 'subject_02' and p.method == 'eegnet' and p.model_seed == 11)

    def assert_locked(request):
        with pytest.raises(RuntimeError, match='lock|reacquir'):
            recorder.claim(request.plan, worker='illegal-reentrant-claim', attempt=1)

    def backend(request, request_path, request_sha):
        state.events.append('backend')
        assert_locked(request)
        assert request_path == request.workspace / 'request.json'
        assert hashlib.sha256(request_path.read_bytes()).hexdigest() == request_sha == request.sha256
        assert request.claim_path.is_file()
        if state.fail == 'backend':
            raise ValueError('injected backend failure')
        native = tmp_path / 'runs/migration' / ('fabricated_' + request.plan.case_id)
        native.mkdir(parents=True)
        receipt = native / 'receipt.json'
        L._write_json_once(receipt, dict(fabricated_native_receipt=True))
        qualification = request.workspace / 'child_output/qualification.json'
        qualification.parent.mkdir()
        L._write_json_once(qualification, dict(fabricated_numerical_qualification=True))
        proof = L.VerifiedWorkerProof(request.sha256, request.plan.case_id, request.claim_file_sha256,
            request.execution_source_sha256, request.independent_pins_sha256, request.owner_decision_sha256,
            request.environment_sha256, native, hashlib.sha256(receipt.read_bytes()).hexdigest(), qualification,
            hashlib.sha256(qualification.read_bytes()).hexdigest(), 128, 256)
        if state.backend_change:
            state.backend_change(request, proof)
        return proof

    def verifier(request, opaque):
        state.events.append('verifier')
        state.verifier_calls += 1
        assert_locked(request)
        if state.fail == 'verifier':
            raise ValueError('injected verifier failure')
        if state.verifier_change:
            state.verifier_change(request, opaque)
        return state.proof_change(opaque) if state.proof_change else opaque

    return SimpleNamespace(root=root, parent=parent, recorder=recorder, context=context, plan=plan,
                           state=state, backend=backend, verifier=verifier)


def run(f, **changes):
    args = dict(recorder=f.recorder, plan=f.plan, context=f.context,
                workspace=f.parent / 'cases' / f.plan.case_id, backend=f.backend, verifier=f.verifier)
    args.update(changes)
    return L.run_engineering_case(**args)


def assert_no_science(f):
    assert not (f.recorder.output_root / 'cells').exists()
    assert not (f.recorder.output_root / 'successes').exists()
    assert not (f.recorder.output_root / 'publication_intents').exists()


def failure_files(f):
    return list((f.recorder.output_root / 'attempts').glob('*.failure.json'))


@pytest.mark.parametrize('method', ['eegnet', 'labram_linear', 'labram_lora', 'labram_full'])
def test_real_recorder_engineering_success_holds_lock_and_never_measures(fixture, method):
    f = fixture
    plan = replace(f.plan, method=method)
    completion = run(f, plan=plan, workspace=f.parent / 'cases' / plan.case_id)
    assert f.state.events == ['backend', 'verifier', 'verifier']
    assert completion.engineering_receipt.is_file()
    assert hashlib.sha256(completion.attestation_path.read_bytes()).hexdigest() == completion.attestation_file_sha256
    assert completion.request.process_mib == (3072 if method == 'labram_full' else 2048)
    assert completion.request.job_mib == (4096 if method == 'labram_full' else 3072)
    assert completion.request.fixture_source_sha256 != completion.request.execution_source_sha256
    ledger = f.recorder.completion((plan,))
    assert ledger['engineering_success'] == 1 and ledger['measured'] == 0 and ledger['failed'] == 0
    assert completion.scientific_admission is False and completion.full_worker_verified is False
    assert completion.original_case_attempts_remaining == 0
    assert failure_files(f) == []
    assert_no_science(f)


@pytest.mark.parametrize('kind', ['subject01', 'seed', 'shots', 'repetition', 'owner', 'source', 'missing_roster', 'environment', 'pins', 'scope'])
def test_preclaim_metadata_refusals_leave_no_ledger(fixture, kind):
    f = fixture
    plan, context = f.plan, f.context
    if kind in {'subject01', 'seed', 'shots', 'repetition'}:
        field, value = {'subject01': ('target_subject', 'subject_01'), 'seed': ('model_seed', 12),
                        'shots': ('shots_per_class', 6), 'repetition': ('repetition', 2)}[kind]
        plan = replace(plan, **{field: value})
    else:
        changes = {'owner': dict(owner_decision_sha256='bad'), 'source': dict(execution_source_sha256=_sha('wrong-code')),
                   'missing_roster': dict(adopted_plans=context.adopted_plans[:-1]),
                   'environment': dict(environment_sha256=_sha('wrong-environment')),
                   'pins': dict(independent_pins_sha256=_sha('wrong-pins')),
                   'scope': dict(recorder_root=context.fixture_root / 'wrong-recorder')}[kind]
        context = _unchecked(context, **changes)
    with pytest.raises(ValueError):
        run(f, plan=plan, context=context, workspace=f.parent / 'cases' / plan.case_id)
    assert f.state.events == []
    assert not f.recorder.output_root.exists()


@pytest.mark.parametrize('stage', ['backend', 'verifier'])
def test_preacceptance_failure_records_one_linked_failure_and_no_retry(fixture, stage):
    f = fixture
    f.state.fail = stage
    with pytest.raises(ValueError, match='injected'):
        run(f)
    failures = failure_files(f)
    assert len(failures) == 1
    payload = json.loads(failures[0].read_bytes())['payload']
    assert payload['attempt'] == 1 and payload['reason']['scientific_admission'] is False
    events = list(f.state.events)
    with pytest.raises(ValueError):
        run(f)
    assert f.state.events == events and failure_files(f) == failures
    assert_no_science(f)


@pytest.mark.parametrize('field', ['request_sha256', 'case_id', 'claim_file_sha256', 'execution_source_sha256',
    'independent_pins_sha256', 'owner_decision_sha256', 'environment_sha256', 'native_directory', 'qualification_path'])
def test_cross_case_or_source_native_proof_binding_refused(fixture, field):
    f = fixture
    value = f.parent / 'wrong' if field in {'native_directory', 'qualification_path'} else _sha('wrong-proof-binding')
    f.state.proof_change = lambda proof: _unchecked(proof, **{field: value})
    with pytest.raises(ValueError):
        run(f)
    assert len(failure_files(f)) == 1
    assert not (f.recorder.output_root / 'engineering_intents').exists()
    assert_no_science(f)


@pytest.mark.parametrize('field,value', [('actual_gradient_updates', 0), ('actual_gradient_updates', True),
    ('scientific_admission', True), ('native_job_closed_empty_absent', False), ('peak_process_bytes', 0),
    ('peak_job_bytes', 3072 * 1024**2 + 1), ('peak_job_bytes', 127),
    ('engineering_only', False), ('original_case_attempts_remaining', 1)])
def test_unchecked_proof_scope_and_peak_limits_refused(fixture, field, value):
    f = fixture
    f.state.proof_change = lambda proof: _unchecked(proof, **{field: value})
    with pytest.raises(ValueError):
        run(f)
    assert len(failure_files(f)) == 1
    assert_no_science(f)


@pytest.mark.parametrize('field', ['worker', 'source', 'environment_sha256', 'engineering_only'])
def test_resealed_claim_metadata_tampering_refused_before_backend(fixture, monkeypatch, field):
    f = fixture
    original = f.recorder._write
    def tampered(directory, name, record):
        if directory.name == 'claims':
            payload = dict(record['payload'])
            payload[field] = {'git_commit': 'b' * 40, 'source_sha256': _sha('changed-fixture'), 'git_dirty': True} if field == 'source' else False if field == 'engineering_only' else 'wrong'
            record = envelope('engineering_smoke', payload)
        return original(directory, name, record)
    monkeypatch.setattr(f.recorder, '_write', tampered)
    with pytest.raises(ValueError):
        run(f)
    assert f.state.events == [] and len(failure_files(f)) == 1


@pytest.mark.parametrize('kind', ['claim', 'request', 'pins', 'live_source', 'live_environment', 'qualification', 'receipt'])
def test_late_work_drift_refused_before_parent_attestation(fixture, kind):
    f = fixture
    def change(request, proof):
        if kind == 'live_source':
            f.state.source = replace(f.context.fixture_source, source_sha256=_sha('late-source'))
        elif kind == 'live_environment':
            f.state.drift_environment = True
        else:
            path = {'claim': request.claim_path, 'request': request.workspace / 'request.json',
                    'pins': request.pins_path, 'qualification': proof.qualification_path,
                    'receipt': proof.native_directory / 'receipt.json'}[kind]
            raw = path.read_bytes()
            if kind == 'claim':
                value = json.loads(raw)
                payload = dict(value['payload'], worker='late-worker')
                raw = L._encoded(envelope('engineering_smoke', payload))
            elif kind in {'qualification', 'receipt'}:
                raw += b' '
            else:
                raw = b'{}\n'
            path.write_bytes(raw)
    f.state.backend_change = change
    with pytest.raises(ValueError):
        run(f)
    assert len(failure_files(f)) == 1
    assert not (f.parent / 'cases' / f.plan.case_id / 'parent-attestation.json').exists()
    assert_no_science(f)


@pytest.mark.parametrize('stage', ['attestation_after_write', 'intent_after_write', 'success_after_write'])
def test_durable_acceptance_interruption_quarantines_without_competing_failure(fixture, monkeypatch, stage):
    f = fixture
    if stage == 'attestation_after_write':
        original = L._write_json_once
        def interrupted(path, payload):
            result = original(path, payload)
            if path.name == 'parent-attestation.json':
                raise RuntimeError('interrupted after durable attestation')
            return result
        monkeypatch.setattr(L, '_write_json_once', interrupted)
    else:
        original = f.recorder._write
        directory_name = 'engineering_intents' if stage == 'intent_after_write' else 'engineering_successes'
        def interrupted(directory, name, record):
            result = original(directory, name, record)
            if directory.name == directory_name:
                raise RuntimeError('interrupted after engineering terminal write')
            return result
        monkeypatch.setattr(f.recorder, '_write', interrupted)
    with pytest.raises(L.RecoveryRequired):
        run(f)
    assert failure_files(f) == []
    assert (f.parent / 'cases' / f.plan.case_id / 'parent-attestation.json').exists()
    assert_no_science(f)


def test_explicit_exact_digest_recovery_is_idempotent_and_never_launches(fixture, monkeypatch):
    f = fixture
    original = f.recorder._write
    def interrupted(directory, name, record):
        if directory.name == 'engineering_successes':
            raise RuntimeError('receipt interrupted')
        return original(directory, name, record)
    monkeypatch.setattr(f.recorder, '_write', interrupted)
    with pytest.raises(L.RecoveryRequired):
        run(f)
    monkeypatch.setattr(f.recorder, '_write', original)
    workspace = f.parent / 'cases' / f.plan.case_id
    request_path = workspace / 'request.json'
    args = dict(recorder=f.recorder, context=f.context, request_path=request_path,
        expected_request_sha256=hashlib.sha256(request_path.read_bytes()).hexdigest(),
        expected_attestation_sha256=hashlib.sha256((workspace / 'parent-attestation.json').read_bytes()).hexdigest())
    events = list(f.state.events)
    first = L.recover_engineering_case(**args)
    assert L.recover_engineering_case(**args) == first
    assert f.state.events == events and failure_files(f) == []
    assert f.recorder.completion((f.plan,))['engineering_success'] == 1
    assert_no_science(f)


@pytest.mark.parametrize('field', ['expected_request_sha256', 'expected_attestation_sha256'])
def test_recovery_wrong_external_digest_refused(fixture, field):
    f = fixture
    done = run(f)
    args = dict(recorder=f.recorder, context=f.context, request_path=done.request_path,
                expected_request_sha256=done.request.sha256, expected_attestation_sha256=done.attestation_file_sha256)
    args[field] = _sha('wrong-external-pin')
    with pytest.raises(ValueError):
        L.recover_engineering_case(**args)
    assert f.recorder.completion((f.plan,))['engineering_success'] == 1


def test_success_replay_blocked_without_second_callback(fixture):
    f = fixture
    run(f)
    events = list(f.state.events)
    with pytest.raises(ValueError):
        run(f)
    assert f.state.events == events and failure_files(f) == []
    assert_no_science(f)


@pytest.mark.parametrize('field,value', [('schema', 'wrong'), ('attempt', 2), ('seconds', 301),
    ('engineering_only', False), ('scientific_admission', True), ('original_case_attempts_remaining', False)])
def test_exact_serialized_request_shape_and_scope(fixture, field, value):
    f = fixture
    done = run(f)
    payload = done.request.payload()
    assert L.load_worker_request(payload) == done.request
    payload[field] = value
    with pytest.raises(ValueError):
        L.load_worker_request(payload)


def test_second_verifier_cannot_change_proof_before_attestation(fixture):
    f = fixture
    def changed(proof):
        return replace(proof, peak_job_bytes=257) if f.state.verifier_calls == 2 else proof
    f.state.proof_change = changed
    with pytest.raises(ValueError, match='proof changed'):
        run(f)
    assert len(failure_files(f)) == 1
    assert not (f.parent / 'cases' / f.plan.case_id / 'parent-attestation.json').exists()


@pytest.mark.parametrize('kind', ['live_source', 'live_environment', 'pins'])
def test_second_verifier_context_drift_is_a_linked_failure_before_attestation(fixture, kind):
    f = fixture
    def change(request, proof):
        if f.state.verifier_calls != 2:
            return
        if kind == 'live_source':
            f.state.source = replace(f.context.fixture_source, source_sha256=_sha('second-verifier-source'))
        elif kind == 'live_environment':
            f.state.drift_environment = True
        else:
            request.pins_path.write_bytes(b'{}\n')
    f.state.verifier_change = change
    with pytest.raises(ValueError):
        run(f)
    assert f.state.verifier_calls == 2 and len(failure_files(f)) == 1
    assert not (f.parent / 'cases' / f.plan.case_id / 'parent-attestation.json').exists()
    assert_no_science(f)


@pytest.mark.parametrize('kind', ['live_source', 'live_environment'])
def test_live_context_drift_after_durable_attestation_quarantines(fixture, monkeypatch, kind):
    f = fixture
    original = L._write_json_once
    def changed(path, payload):
        result = original(path, payload)
        if path.name == 'parent-attestation.json':
            if kind == 'live_source':
                f.state.source = replace(f.context.fixture_source, source_sha256=_sha('post-attestation-source'))
            else:
                f.state.drift_environment = True
        return result
    monkeypatch.setattr(L, '_write_json_once', changed)
    with pytest.raises(L.RecoveryRequired):
        run(f)
    assert (f.parent / 'cases' / f.plan.case_id / 'parent-attestation.json').is_file()
    assert not (f.recorder.output_root / 'engineering_intents').exists()
    assert failure_files(f) == []
    assert_no_science(f)


def test_explicit_recovery_does_not_create_a_missing_engineering_intent(fixture, monkeypatch):
    f = fixture
    original = L._write_json_once
    def interrupted(path, payload):
        result = original(path, payload)
        if path.name == 'parent-attestation.json':
            raise RuntimeError('interrupted before any engineering intent')
        return result
    monkeypatch.setattr(L, '_write_json_once', interrupted)
    with pytest.raises(L.RecoveryRequired):
        run(f)
    monkeypatch.setattr(L, '_write_json_once', original)
    workspace = f.parent / 'cases' / f.plan.case_id
    events = list(f.state.events)
    with pytest.raises(ValueError, match='intent'):
        L.recover_engineering_case(f.recorder, context=f.context, request_path=workspace / 'request.json',
            expected_request_sha256=hashlib.sha256((workspace / 'request.json').read_bytes()).hexdigest(),
            expected_attestation_sha256=hashlib.sha256((workspace / 'parent-attestation.json').read_bytes()).hexdigest())
    assert f.state.events == events and failure_files(f) == []
    assert not (f.recorder.output_root / 'engineering_intents').exists()
    assert not (f.recorder.output_root / 'engineering_successes').exists()


@pytest.mark.parametrize('kind', ['proof', 'pins', 'request'])
def test_recovery_inputs_rechecked_after_identity_lock_acquisition(fixture, monkeypatch, kind):
    f = fixture
    done = run(f)
    original_session = f.recorder.case_session
    @contextmanager
    def changed_after_lock(plan):
        with original_session(plan) as locked:
            target = {'proof': done.proof.qualification_path, 'pins': f.context.pins_path,
                      'request': done.request_path}[kind]
            target.write_bytes(target.read_bytes() + b' ')
            yield locked
    monkeypatch.setattr(f.recorder, 'case_session', changed_after_lock)
    events = list(f.state.events)
    with pytest.raises(ValueError):
        L.recover_engineering_case(f.recorder, context=f.context, request_path=done.request_path,
            expected_request_sha256=done.request.sha256, expected_attestation_sha256=done.attestation_file_sha256)
    assert f.state.events == events and failure_files(f) == []
    assert_no_science(f)


def test_small_physical_helper_detects_same_byte_replacement(tmp_path):
    path = tmp_path / 'proof.json'
    path.write_bytes(b'{}\n')
    _, identity = L._read(path)
    replacement = tmp_path / 'replacement.json'
    replacement.write_bytes(path.read_bytes())
    replacement.replace(path)
    assert L._read(path)[1] != identity
