"""Real recorder/locks with explicitly fabricated metadata verifier callbacks.

No selector, model, restoration, array fixture, native Job or study case runs.
Only fixture source capture and substantive stage verification are mocked.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest

from core.provenance import SourceProvenance
from docs.phase2.cho51_staged_recorder_v1 import transaction as T

L = T.L


def sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


def unchecked(value, **changes):
    result = object.__new__(type(value))
    for item in fields(value):
        object.__setattr__(result, item.name, changes.get(item.name, getattr(value, item.name)))
    return result


@pytest.fixture(scope='module')
def adopted():
    return tuple(T.CasePlan('cho2017', f'subject_{s:02d}', method, 5, seed, 1)
        for s in range(2, 53) for method in L.METHODS for seed in L.SEEDS)


@pytest.fixture
def fixture(tmp_path, monkeypatch, adopted):
    parent = tmp_path / 'p'
    root = parent / 'fixture'
    root.mkdir(parents=True)
    source = SourceProvenance('a' * 40, sha('fabricated-fresh-five-config-fixture'), True)
    monkeypatch.setattr(L.recorder_module, 'capture_source', lambda path: source)
    environment = L.recorder_module.environment_digest()
    owner = sha('owner-decision')
    pins_path = tmp_path / 'pins.json'
    pins_sha = L._write_json_once(pins_path, dict(canonical_source_sha256=L.CANONICAL_SOURCE_SHA256,
        owner_decision_sha256=owner))
    context = T.WorkerContext(parent, root, root / 'runs/phase2/lifecycle', pins_path,
        pins_sha, L.CANONICAL_SOURCE_SHA256, owner, adopted, source, environment)
    origin = tmp_path / 'origin'
    origin.mkdir()
    origin_ledger = origin / 'failed-original-ledger.json'
    L._write_json_once(origin_ledger, dict(original_parent_failed=True, attempts=1))
    ledger_bytes = origin_ledger.read_bytes()
    weights = origin / 'fabricated-weights.bin'
    weights.write_bytes(b'fabricated test bytes; no tensors')
    weights_sha = hashlib.sha256(weights.read_bytes()).hexdigest()
    receipt = origin / 'fabricated-stage-receipt.json'
    receipt_sha = L._write_json_once(receipt, dict(fabricated=True, accepted=True))
    summary = dict(**{key: value for key, value in T._INTS.items() if key != 'attempt'},
        **T._FLAGS, restore_limits=[1048576, 1048576],
        selected_state_sha256=sha('fabricated-selected-state'), weights_file_sha256=weights_sha)
    contract_path = origin / 'contract.json'
    contract = dict(schema='cho51_staged_recorder_origin_contract_v1',
        files={str(weights): weights_sha, str(receipt): receipt_sha}, summary=summary)
    contract_sha = L._write_json_once(contract_path, contract)
    recorder = T.CaseRecorder(root, output_root=context.recorder_root)
    plan = T.CasePlan('cho2017', 'subject_02', 'eegnet', 5, 11, 1)
    state = SimpleNamespace(events=[], fail=None, proof_change=None, backend_change=None,
        verifier_calls=0, verifier_change=None)

    def assert_locked(request):
        with pytest.raises(RuntimeError, match='lock|reacquir'):
            recorder.claim(request.plan, worker='reentrant-forbidden', attempt=1)

    def backend(request, request_path, request_sha):
        state.events.append('backend')
        assert_locked(request)
        assert request_sha == request.sha256 == hashlib.sha256(request_path.read_bytes()).hexdigest()
        assert T.load_staged_request(json.loads(request_path.read_bytes())) == request
        if state.fail == 'backend':
            raise ValueError('injected backend failure')
        values = dict(request_sha256=request.sha256, case_id=request.plan.case_id,
            verified_origin_files=len(contract['files']), selected_state_sha256=summary['selected_state_sha256'],
            weights_file_sha256=summary['weights_file_sha256'])
        values.update({name: getattr(request, name) for name in T._BINDINGS})
        proof = T.VerifiedStagedProof(**values)
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

    return SimpleNamespace(parent=parent, root=root, context=context, recorder=recorder,
        plan=plan, state=state, backend=backend, verifier=verifier, weights=weights,
        receipt=receipt, contract=contract, origin_contract_path=contract_path,
        origin_contract_file_sha256=contract_sha, origin_ledger=origin_ledger, ledger_bytes=ledger_bytes)


def run(f, **changes):
    args = dict(recorder=f.recorder, plan=f.plan, context=f.context,
        workspace=f.parent / 'cases' / f.plan.case_id, backend=f.backend, verifier=f.verifier,
        origin_contract_path=f.origin_contract_path,
        origin_contract_file_sha256=f.origin_contract_file_sha256)
    args.update(changes)
    return T.run_staged_case(**args)


def failures(f):
    return list((f.recorder.output_root / 'attempts').glob('*.failure.json'))


def no_science(f):
    assert not (f.recorder.output_root / 'cells').exists()
    assert not (f.recorder.output_root / 'successes').exists()
    assert not (f.recorder.output_root / 'publication_intents').exists()
    assert f.origin_ledger.read_bytes() == f.ledger_bytes


def recovery_args(f):
    workspace = f.parent / 'cases' / f.plan.case_id
    return dict(recorder=f.recorder, context=f.context, request_path=workspace / 'request.json',
        expected_request_sha256=hashlib.sha256((workspace / 'request.json').read_bytes()).hexdigest(),
        expected_attestation_sha256=hashlib.sha256((workspace / 'parent-attestation.json').read_bytes()).hexdigest(),
        verifier=f.verifier)


def test_staged_success_holds_real_lock_preserves_origin_and_zero_measured(fixture):
    f = fixture
    done = run(f)
    assert f.state.events == ['backend', 'verifier', 'verifier']
    assert done.request.historical_gradient_updates == 5253 and done.proof.current_gradient_updates == 0
    assert done.request.source_work_reused is done.proof.restore_work_reused is True
    assert done.proof.origin_parent_transaction_qualified is False
    assert done.engineering_receipt.is_file() and failures(f) == []
    claim = json.loads(done.request.claim_path.read_bytes())['payload']
    assert claim['worker'] == T.WORKER
    assert f.recorder.completion((f.plan,))['engineering_success'] == 1
    assert f.recorder.completion((f.plan,))['measured'] == 0
    no_science(f)


@pytest.mark.parametrize('field,value', [('target_subject', 'subject_01'), ('method', 'labram_linear'), ('model_seed', 23)])
def test_other_case_scope_refuses_before_claim(fixture, field, value):
    f = fixture
    plan = replace(f.plan, **{field: value})
    with pytest.raises(ValueError):
        run(f, plan=plan, workspace=f.parent / 'cases' / plan.case_id)
    assert f.state.events == [] and not f.recorder.output_root.exists()


@pytest.mark.parametrize('field,value', [('current_gradient_updates', 1), ('historical_gradient_updates', 8),
    ('source_work_reused', False), ('current_gradient_updates', False), ('origin_parent_transaction_qualified', True)])
def test_request_rejects_old_or_numerical_scope_and_bool_counts(fixture, field, value):
    payload = run(fixture).request.payload()
    payload[field] = value
    with pytest.raises(ValueError):
        T.load_staged_request(payload)


@pytest.mark.parametrize('kind', ['summary', 'contract_pin', 'inside_output'])
def test_malformed_or_unbound_origin_refuses_before_claim(fixture, kind):
    f = fixture
    args = {}
    if kind == 'summary':
        f.contract['summary']['restore_limits'] = [1048576, 4294967296]
        f.origin_contract_path.write_bytes(L._encoded(f.contract))
        args['origin_contract_file_sha256'] = hashlib.sha256(f.origin_contract_path.read_bytes()).hexdigest()
    elif kind == 'contract_pin':
        args['origin_contract_file_sha256'] = sha('wrong-origin')
    else:
        path = f.parent / 'contract.json'
        path.write_bytes(f.origin_contract_path.read_bytes())
        args['origin_contract_path'] = path
    with pytest.raises(ValueError):
        run(f, **args)
    assert f.state.events == [] and not f.recorder.output_root.exists()


@pytest.mark.parametrize('stage', ['backend', 'verifier'])
def test_preacceptance_failure_is_one_linked_failure_without_replay(fixture, stage):
    f = fixture
    f.state.fail = stage
    with pytest.raises(ValueError, match='injected'):
        run(f)
    assert len(failures(f)) == 1
    payload = json.loads(failures(f)[0].read_bytes())['payload']
    assert payload['attempt'] == 1 and payload['reason']['current_gradient_updates'] == 0
    assert payload['reason']['origin_parent_transaction_qualified'] is False
    events = list(f.state.events)
    with pytest.raises(ValueError):
        run(f)
    assert f.state.events == events and len(failures(f)) == 1
    no_science(f)


@pytest.mark.parametrize('field', ['request_sha256', 'claim_file_sha256', 'origin_contract_file_sha256', 'selected_state_sha256'])
def test_cross_request_or_origin_proof_refused(fixture, field):
    f = fixture
    f.state.proof_change = lambda proof: unchecked(proof, **{field: sha('wrong-proof')})
    with pytest.raises(ValueError):
        run(f)
    assert len(failures(f)) == 1 and not (f.recorder.output_root / 'engineering_intents').exists()
    no_science(f)


@pytest.mark.parametrize('kind', ['weights', 'receipt', 'request', 'same_byte_replacement'])
def test_physical_drift_after_first_verifier_blocks_attestation(fixture, kind):
    f = fixture
    def changed(request, proof):
        if f.state.verifier_calls != 2:
            return
        target = request.workspace / 'request.json' if kind == 'request' else f.receipt if kind == 'receipt' else f.weights
        if kind == 'same_byte_replacement':
            raw = target.read_bytes()
            replacement = target.with_suffix('.replacement')
            replacement.write_bytes(raw)
            replacement.replace(target)
        else:
            target.write_bytes(target.read_bytes() + b' ')
    f.state.verifier_change = changed
    with pytest.raises(ValueError):
        run(f)
    assert len(failures(f)) == 1
    assert not (f.parent / 'cases' / f.plan.case_id / 'parent-attestation.json').exists()
    no_science(f)


@pytest.mark.parametrize('stage', ['attestation', 'intent', 'success'])
def test_durable_acceptance_interruption_quarantines_without_failure(fixture, monkeypatch, stage):
    f = fixture
    if stage == 'attestation':
        original = L._write_json_once
        def interrupted(path, payload):
            result = original(path, payload)
            if path.name == 'parent-attestation.json':
                raise RuntimeError('interrupted durable attestation')
            return result
        monkeypatch.setattr(L, '_write_json_once', interrupted)
    else:
        original = f.recorder._write
        selected = 'engineering_intents' if stage == 'intent' else 'engineering_successes'
        def interrupted(directory, name, record):
            result = original(directory, name, record)
            if directory.name == selected:
                raise RuntimeError('interrupted durable recorder terminal')
            return result
        monkeypatch.setattr(f.recorder, '_write', interrupted)
    with pytest.raises(T.RecoveryRequired):
        run(f)
    assert failures(f) == []
    no_science(f)


def test_explicit_recovery_reverifies_origin_is_idempotent_and_no_backend(fixture, monkeypatch):
    f = fixture
    original = f.recorder._write
    def interrupted(directory, name, record):
        if directory.name == 'engineering_successes':
            raise RuntimeError('receipt interrupted')
        return original(directory, name, record)
    monkeypatch.setattr(f.recorder, '_write', interrupted)
    with pytest.raises(T.RecoveryRequired):
        run(f)
    monkeypatch.setattr(f.recorder, '_write', original)
    args = recovery_args(f)
    backend_calls = f.state.events.count('backend')
    verifier_calls = f.state.events.count('verifier')
    receipt = T.recover_staged_case(**args)
    assert T.recover_staged_case(**args) == receipt
    assert f.state.events.count('backend') == backend_calls == 1
    assert f.state.events.count('verifier') == verifier_calls + 2
    assert failures(f) == []
    no_science(f)


@pytest.mark.parametrize('field', ['expected_request_sha256', 'expected_attestation_sha256'])
def test_wrong_external_recovery_digest_refused(fixture, field):
    f = fixture
    run(f)
    args = recovery_args(f)
    args[field] = sha('wrong-external')
    with pytest.raises(ValueError):
        T.recover_staged_case(**args)
    assert f.recorder.completion((f.plan,))['engineering_success'] == 1


def test_second_verifier_cannot_rewrite_accepted_staged_proof(fixture):
    f = fixture
    f.state.proof_change = lambda proof: unchecked(proof, selected_state_sha256=sha('second-state')) if f.state.verifier_calls == 2 else proof
    with pytest.raises(ValueError, match='proof changed'):
        run(f)
    assert len(failures(f)) == 1


@pytest.mark.parametrize('worker', ['cho51_synthetic_numerical_engineering', 'different-staged-worker'])
def test_resealed_claim_worker_cannot_mix_old_or_unrelated_scope(fixture, worker):
    f = fixture
    def changed(request, proof):
        if f.state.verifier_calls != 1:
            return
        claim = json.loads(request.claim_path.read_bytes())
        claim['payload']['worker'] = worker
        request.claim_path.write_bytes(L._encoded(L.recorder_module.envelope('engineering_smoke', claim['payload'])))
    f.state.verifier_change = changed
    with pytest.raises(ValueError, match='claim'):
        run(f)
    assert len(failures(f)) == 1
    no_science(f)


def test_current_execution_pins_drift_before_attestation_is_refused(fixture):
    f = fixture
    def changed(request, proof):
        if f.state.verifier_calls == 2:
            request.pins_path.write_bytes(request.pins_path.read_bytes() + b' ')
    f.state.verifier_change = changed
    with pytest.raises(ValueError):
        run(f)
    assert len(failures(f)) == 1
    assert not (f.parent / 'cases' / f.plan.case_id / 'parent-attestation.json').exists()


def test_proof_cannot_claim_current_training_or_qualified_original_parent(fixture):
    f = fixture
    f.state.proof_change = lambda proof: unchecked(proof, current_gradient_updates=True,
        origin_parent_transaction_qualified=True)
    with pytest.raises(ValueError):
        run(f)
    assert len(failures(f)) == 1
    no_science(f)


def test_recovery_refuses_origin_drift_before_reverifier(fixture):
    f = fixture
    run(f)
    args = recovery_args(f)
    events = list(f.state.events)
    f.weights.write_bytes(b'changed origin weights')
    with pytest.raises(ValueError):
        T.recover_staged_case(**args)
    assert f.state.events == events


def test_recovery_does_not_create_missing_engineering_intent(fixture, monkeypatch):
    f = fixture
    original = L._write_json_once
    def interrupted(path, payload):
        result = original(path, payload)
        if path.name == 'parent-attestation.json':
            raise RuntimeError('before recorder intent')
        return result
    monkeypatch.setattr(L, '_write_json_once', interrupted)
    with pytest.raises(T.RecoveryRequired):
        run(f)
    monkeypatch.setattr(L, '_write_json_once', original)
    with pytest.raises(ValueError, match='intent'):
        T.recover_staged_case(**recovery_args(f))
    assert failures(f) == [] and not (f.recorder.output_root / 'engineering_intents').exists()
