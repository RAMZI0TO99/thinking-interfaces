"""Real recorder locks/terminals with fabricated complete/native proof callbacks.

No selector, model, array fixture, native Job or scientific case executes here.
Only fixture source capture and native verification are mocked explicitly.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest

from core.config import config_digest
from core.provenance import SourceProvenance
from docs.phase2.cho51_complete_eegnet_v1 import transaction as T

L = T.L


def sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


def unchecked(value, **changes):
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
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
    monkeypatch.setattr(T, 'ROOT', tmp_path)
    monkeypatch.setattr(L, 'ROOT', tmp_path)
    source = SourceProvenance('a' * 40, sha('fabricated-owned-configured-fixture'), True)
    monkeypatch.setattr(L.recorder_module, 'capture_source', lambda path: source)
    environment = L.recorder_module.environment_digest()
    method_config = tmp_path / 'method.json'
    method = dict(synthetic=True, learning_rates=[0.001, 0.002], source_epochs=1)
    method_file_sha = L._write_json_once(method_config, method)
    owner = sha('owner-decision')
    pins_path = tmp_path / 'pins.json'
    pins_sha = L._write_json_once(pins_path, dict(canonical_source_sha256=L.CANONICAL_SOURCE_SHA256,
        owner_decision_sha256=owner, files={'method.json': method_file_sha}))
    context = T.WorkerContext(parent, root, root / 'runs/phase2/lifecycle', pins_path,
        pins_sha, L.CANONICAL_SOURCE_SHA256, owner, adopted, source, environment)
    identity = dict(synthetic=True, actual_study_data=False, scientific_admission=False,
        files={f'fabricated-input-{number}': dict(sha256=sha(str(number)), size_bytes=1)
            for number in range(213)})
    identity['sha256'] = config_digest(identity)
    identity_path = root / 'synthetic-input-identity.json'
    identity_file_sha = L._write_json_once(identity_path, identity)
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
        assert T.load_complete_request(json.loads(request_path.read_bytes())) == request
        if state.fail == 'backend':
            raise ValueError('injected backend failure')
        source_native = tmp_path / 'runs/migration/source_fabricated'
        detached_native = tmp_path / 'runs/migration/detached_fabricated'
        source_native.mkdir(parents=True)
        detached_native.mkdir(parents=True)
        request.selection_output.mkdir()
        request.detached_output.mkdir()
        publication = root / 'runs/phase2/selected_sources'
        publication.mkdir(parents=True)
        physical = {
            'source_native_receipt_file_sha256': source_native / 'receipt.json',
            'detached_native_receipt_file_sha256': detached_native / 'receipt.json',
            'source_qualification_file_sha256': request.selection_output / 'qualification.json',
            'detached_qualification_file_sha256': request.detached_output / 'qualification.json',
            'source_result_file_sha256': request.selection_output / 'source-result.json',
            'detached_result_file_sha256': request.detached_output / 'detached-result.json',
            'manifest_file_sha256': publication / 'manifest.json',
            'evidence_file_sha256': publication / 'evidence.json',
            'weights_file_sha256': publication / 'fabricated-weights.bin',
        }
        values = {name: L._write_json_once(path, dict(fabricated_proof=True, role=name))
            for name, path in physical.items()}
        values.update(request_sha256=request.sha256, case_id=request.plan.case_id,
            source_native_directory=source_native, detached_native_directory=detached_native,
            source_qualification_path=physical['source_qualification_file_sha256'],
            detached_qualification_path=physical['detached_qualification_file_sha256'],
            source_result_path=physical['source_result_file_sha256'],
            detached_result_path=physical['detached_result_file_sha256'],
            manifest_path=physical['manifest_file_sha256'], evidence_path=physical['evidence_file_sha256'],
            weights_path=physical['weights_file_sha256'], evidence_sha256=sha('fabricated-logical-evidence'),
            selected_state_sha256=sha('fabricated-selected-state'),
            source_peak_process_bytes=128, source_peak_job_bytes=256,
            detached_peak_process_bytes=128, detached_peak_job_bytes=256)
        values.update({name: getattr(request, name) for name in T._BINDINGS})
        proof = T.VerifiedCompleteProof(**values)
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
        plan=plan, state=state, backend=backend, verifier=verifier,
        fixture_identity_path=identity_path, fixture_identity_file_sha256=identity_file_sha,
        fixture_identity_sha256=identity['sha256'], method_config_path=method_config,
        method_config_file_sha256=method_file_sha, method_config_sha256=config_digest(method))


def run(f, **changes):
    args = dict(recorder=f.recorder, plan=f.plan, context=f.context,
        workspace=f.parent / 'cases' / f.plan.case_id, backend=f.backend, verifier=f.verifier)
    args.update({name: getattr(f, name) for name in ('fixture_identity_path', 'fixture_identity_file_sha256',
        'fixture_identity_sha256', 'method_config_path', 'method_config_file_sha256', 'method_config_sha256')})
    args.update(changes)
    return T.run_complete_case(**args)


def failures(f):
    return list((f.recorder.output_root / 'attempts').glob('*.failure.json'))


def no_science(f):
    assert not (f.recorder.output_root / 'cells').exists()
    assert not (f.recorder.output_root / 'successes').exists()
    assert not (f.recorder.output_root / 'publication_intents').exists()


def test_complete_recorder_success_holds_real_lock_and_zero_measured_cells(fixture):
    f = fixture
    done = run(f)
    assert f.state.events == ['backend', 'verifier', 'verifier']
    assert done.request.actual_gradient_updates == 5253 and done.proof.source_updates == 5151
    assert done.proof.support_updates == 102 and done.proof.fold_count == 102
    assert done.proof.final_source_subjects == 51
    assert done.engineering_receipt.is_file() and failures(f) == []
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


@pytest.mark.parametrize('stage', ['backend', 'verifier'])
def test_preacceptance_failure_records_one_linked_failure_without_retry(fixture, stage):
    f = fixture
    f.state.fail = stage
    with pytest.raises(ValueError, match='injected'):
        run(f)
    assert len(failures(f)) == 1
    payload = json.loads(failures(f)[0].read_bytes())['payload']
    assert payload['attempt'] == 1 and payload['reason']['scientific_admission'] is False
    events = list(f.state.events)
    with pytest.raises(ValueError):
        run(f)
    assert f.state.events == events and len(failures(f)) == 1
    no_science(f)


@pytest.mark.parametrize('field,value', [('source_seconds', 421), ('detached_job_mib', 4096),
    ('actual_gradient_updates', 8), ('source_updates', 5100), ('engineering_only', False), ('scientific_admission', True)])
def test_exact_complete_request_rejects_changed_budget_and_old_probe_scope(fixture, field, value):
    done = run(fixture)
    payload = done.request.payload()
    payload[field] = value
    with pytest.raises(ValueError):
        T.load_complete_request(payload)


@pytest.mark.parametrize('field', ['request_sha256', 'claim_file_sha256', 'independent_pins_sha256',
    'manifest_path', 'source_native_directory'])
def test_cross_case_or_publication_proof_is_refused(fixture, field):
    f = fixture
    value = f.parent / 'wrong' if field.endswith('path') or field.endswith('directory') else sha('wrong-proof')
    f.state.proof_change = lambda proof: unchecked(proof, **{field: value})
    with pytest.raises(ValueError):
        run(f)
    assert len(failures(f)) == 1 and not (f.recorder.output_root / 'engineering_intents').exists()
    no_science(f)


@pytest.mark.parametrize('field,value', [('actual_gradient_updates', 8), ('fold_count', 101),
    ('final_source_subjects', 50), ('source_peak_job_bytes', 4294967297),
    ('detached_job_closed_empty_absent', False)])
def test_incomplete_workload_or_unclosed_native_work_is_refused(fixture, field, value):
    f = fixture
    f.state.proof_change = lambda proof: unchecked(proof, **{field: value})
    with pytest.raises(ValueError):
        run(f)
    assert len(failures(f)) == 1
    no_science(f)


@pytest.mark.parametrize('kind', ['qualification', 'publication', 'request'])
def test_physical_drift_after_first_native_verification_blocks_attestation(fixture, kind):
    f = fixture
    def changed(request, proof):
        if f.state.verifier_calls != 2:
            return
        target = {'qualification': proof.detached_qualification_path,
            'publication': proof.weights_path, 'request': request.workspace / 'request.json'}[kind]
        target.write_bytes(target.read_bytes() + b' ')
    f.state.verifier_change = changed
    with pytest.raises(ValueError):
        run(f)
    assert len(failures(f)) == 1
    assert not (f.parent / 'cases' / f.plan.case_id / 'parent-attestation.json').exists()
    no_science(f)


@pytest.mark.parametrize('stage', ['attestation', 'intent', 'success'])
def test_durable_acceptance_interruption_quarantines_without_competing_failure(fixture, monkeypatch, stage):
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
    assert (f.parent / 'cases' / f.plan.case_id / 'parent-attestation.json').is_file()
    no_science(f)


def test_explicit_external_digest_recovery_is_idempotent_and_never_launches(fixture, monkeypatch):
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
    workspace = f.parent / 'cases' / f.plan.case_id
    args = dict(recorder=f.recorder, context=f.context, request_path=workspace / 'request.json',
        expected_request_sha256=hashlib.sha256((workspace / 'request.json').read_bytes()).hexdigest(),
        expected_attestation_sha256=hashlib.sha256((workspace / 'parent-attestation.json').read_bytes()).hexdigest())
    events = list(f.state.events)
    receipt = T.recover_complete_case(**args)
    assert T.recover_complete_case(**args) == receipt
    assert events == f.state.events and failures(f) == []
    no_science(f)


@pytest.mark.parametrize('field', ['expected_request_sha256', 'expected_attestation_sha256'])
def test_wrong_external_recovery_digest_is_refused(fixture, field):
    f = fixture
    done = run(f)
    args = dict(recorder=f.recorder, context=f.context, request_path=done.request_path,
        expected_request_sha256=done.request.sha256, expected_attestation_sha256=done.attestation_file_sha256)
    args[field] = sha('wrong-external')
    with pytest.raises(ValueError):
        T.recover_complete_case(**args)
    assert f.recorder.completion((f.plan,))['engineering_success'] == 1


def test_second_verifier_cannot_rewrite_accepted_complete_proof(fixture):
    f = fixture
    f.state.proof_change = lambda proof: replace(proof, source_peak_job_bytes=257) if f.state.verifier_calls == 2 else proof
    with pytest.raises(ValueError, match='proof changed'):
        run(f)
    assert len(failures(f)) == 1


def test_recovery_does_not_create_a_missing_engineering_intent(fixture, monkeypatch):
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
    workspace = f.parent / 'cases' / f.plan.case_id
    events = list(f.state.events)
    with pytest.raises(ValueError, match='intent'):
        T.recover_complete_case(f.recorder, context=f.context, request_path=workspace / 'request.json',
            expected_request_sha256=hashlib.sha256((workspace / 'request.json').read_bytes()).hexdigest(),
            expected_attestation_sha256=hashlib.sha256((workspace / 'parent-attestation.json').read_bytes()).hexdigest())
    assert events == f.state.events and failures(f) == []
    assert not (f.recorder.output_root / 'engineering_intents').exists()
