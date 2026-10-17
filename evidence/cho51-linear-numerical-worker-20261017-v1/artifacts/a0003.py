"""Metadata-only fabricated numerical witnesses under real recorder identity locks.

These tests execute no restore, tensor, optimizer or prediction. Tiny historical
origin artifacts are explicitly fabricated by the frozen metadata fixture.
Every mutation first passes a valid physical current proof through the verifier.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from evaluation.phase2_records import envelope
from docs.phase2.cho51_linear_worker_route_v3.test_worker_route import adopted, fixture as historical_fixture
from docs.phase2.cho51_linear_numerical_worker_v1 import numerical_worker as N

W, L = N.W, N.L


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def clone(value):
    return json.loads(json.dumps(value))


@pytest.fixture
def fixture(historical_fixture):
    f = historical_fixture
    summary = f.contract['summary']
    historical_path = Path(summary['target_proof_paths']['target_witness_file_sha256'])
    historical = json.loads(historical_path.read_bytes())
    source = {'head.weight': sha('source-head-weight'), 'head.bias': sha('source-head-bias')}
    source.update({f'backbone_{i:03d}': sha('source-' + str(i)) for i in range(221)})
    historical['source_state_tensors'] = source
    historical_path.write_bytes(L._encoded(historical))
    summary['target_witness_file_sha256'] = hashlib.sha256(historical_path.read_bytes()).hexdigest()
    f.contract['files'][str(historical_path)] = summary['target_witness_file_sha256']
    f.origin_contract_path.write_bytes(L._encoded(f.contract))
    f.origin_contract_file_sha256 = hashlib.sha256(f.origin_contract_path.read_bytes()).hexdigest()
    target = clone(historical)
    # A different valid fresh result proves accuracy is not fixed to old0/2.
    target.update(query_logits=[[2.5, -1.0], [-0.5, 3.0]], confusion_matrix=[[1, 0], [0, 1]],
        balanced_accuracy=[1, 1], query_count=2, original_case_attempts_remaining=0,
        caller_source_runner_source_and_adapted_storage_disjoint=True)
    after = dict(source, **{'head.weight': sha('fresh-head-weight'), 'head.bias': sha('fresh-head-bias')})
    target['witnesses'] = dict(before_state_tensors=dict(source), after_state_tensors=after,
        adapted_state_sha256=sha('fresh-raw-aggregate'), changed_state_names=['head.weight', 'head.bias'],
        calls=dict(adaptation=1, support_forward=1, backward=1, sgd_step=1, query_forward=1, runner_prediction=1),
        mask=dict(method='linear', trainable_parameters=402, trainable_names=list(N.HEAD_NAMES), depth=0, selected_blocks=[]),
        finite_gradients=True, query_inference_mode=True, all_modules_eval=True, source_unchanged=True,
        backbone_and_buffers_unchanged=True, owned_source_and_adapted_storage_disjoint=True,
        query_labels_used_for_adaptation=False, unused_pool_used_for_adaptation=False,
        gradient_sha256={name: sha('gradient-' + name) for name in N.HEAD_NAMES},
        gradient_norms={name: 0.5 for name in N.HEAD_NAMES}, support_losses=[0.7],
        classifier_input_shapes=[[10, 64, 800], [2, 64, 800]])
    restore = dict(schema='cho51_linear_target_staged_restore_v1', passed=True, scientific_admission=False,
        selected_state_sha256=summary['selected_state_sha256'], weights_file_sha256=summary['weights_file_sha256'],
        complete_evidence_file_sha256=W._ROLE_SPECS['complete_evidence'][2],
        new_explicit_two_root_staged_restore_verified=True, source_backbone_unchanged=True,
        unchanged_canonical_store_restore_verified=False, unchanged_single_root_factory_verified=False,
        current_restore_count=1, baseline_decodes=1, selected_decodes=1, strict_state_loads=2,
        tensor_count=223, elements=5818138, head_parameters=402, weights_limit_bytes=67108864,
        weights_bytes=23294624, measured_cells=0, historical_source=dict(W.HISTORICAL_SOURCE))
    N.validate_state_witness(target, historical)
    assert N.derive_current_metrics(target, summary['target_contract'])['correct_query_predictions'] == 2
    f.current_target, f.current_restore = target, restore
    f.state.events, f.state.verifier_calls = [], 0
    f.state.mutate, f.state.second_change = None, None

    def assert_locked(request):
        with pytest.raises(RuntimeError, match='lock|reacquir'):
            f.recorder.claim(request.plan, worker='forbidden-reentrant-worker', attempt=1)

    def write_current(request, payload, current_target, current_restore):
        for name, witness in (('target-witness.json', current_target), ('restore-witness.json', current_restore)):
            raw = L._encoded(witness)
            (request.workspace / name).write_bytes(raw)
            payload['physical_outputs'][name] = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        payload['target_route_witness'], payload['restore_witness'] = current_target, current_restore
        raw = L._encoded(envelope('engineering_smoke', payload))
        (request.workspace / 'current-execution.json').write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def backend(request, request_path, request_sha):
        f.state.events.append('backend')
        assert_locked(request)
        assert request_sha == request.sha256 == hashlib.sha256(request_path.read_bytes()).hexdigest()
        assert N.load_worker_request(json.loads(request_path.read_bytes())) == request
        if f.state.fail == 'backend':
            raise ValueError('injected after numerical backend started')
        binding = N.build_current_binding(request)
        current = dict(git_commit=request.historical_binding.fixture_git_commit,
            source_sha256=request.historical_binding.fixture_source_sha256,
            git_dirty=request.historical_binding.fixture_git_dirty)
        current_target, current_restore = clone(f.current_target), clone(f.current_restore)
        current_target.update(current_worker_binding=binding, provenance=dict(current=current, historical=dict(W.HISTORICAL_SOURCE)))
        current_restore.update(current_worker_binding=binding, current_control_source=current)
        audit = dict(bytes=734579463, files=213,
            fixture_root=str(L.ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture'),
            input_identity_file_sha256='34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
        payload = dict(schema='cho51_linear_numerical_execution_v1', **binding,
            expected_numerical_budget=dict(N.EXPECTED_BUDGET), current_counter_ledger=dict(N.EXPECTED_BUDGET),
            observed_numerical_calls=dict(module_load_state_dict=2, safetensors_load=2, optimizer_init=1,
                sgd_step=1, tensor_backward=1, autograd_backward=1, model_module_init=200),
            current_control_source=current, historical_source=dict(W.HISTORICAL_SOURCE),
            source_fixture=audit['fixture_root'], input_audit_before=clone(audit), input_audit_after=clone(audit),
            physical_outputs={}, native_closeout_status='pending_external_post_job',
            engineering_only=True, scientific_admission=False, measured_cells=0)
        opaque = write_current(request, payload, current_target, current_restore)
        # Physical baseline must verify before every negative mutation below.
        N.verify_current_execution(request, opaque)
        if f.state.mutate:
            f.state.mutate(payload, current_target, current_restore, request)
            opaque = write_current(request, payload, current_target, current_restore)
        return opaque

    def verifier(request, opaque):
        f.state.events.append('verifier')
        f.state.verifier_calls += 1
        assert_locked(request)
        if f.state.fail == 'verifier':
            raise ValueError('injected independent verifier failure')
        if f.state.second_change and f.state.verifier_calls == 2:
            f.state.second_change(request, opaque)
        return N.verify_current_execution(request, opaque)

    f.backend, f.verifier, f.write_current = backend, verifier, write_current
    return f


def run(f, **changes):
    args = dict(recorder=f.recorder, plan=f.plan, context=f.context, route=f.route,
        workspace=f.parent / 'cases' / f.plan.case_id, backend=f.backend, verifier=f.verifier,
        origin_contract_path=f.origin_contract_path, origin_contract_file_sha256=f.origin_contract_file_sha256)
    args.update(changes)
    return N.run_worker_case(**args)


def failures(f):
    return list((f.recorder.output_root / 'attempts').glob('*.failure.json'))


def recovery_args(f):
    workspace = f.parent / 'cases' / f.plan.case_id
    return dict(recorder=f.recorder, context=f.context, route=f.route, request_path=workspace / 'request.json',
        expected_request_sha256=hashlib.sha256((workspace / 'request.json').read_bytes()).hexdigest(),
        expected_attestation_sha256=hashlib.sha256((workspace / 'parent-attestation.json').read_bytes()).hexdigest(),
        verifier=f.verifier)


def test_current_numerical_transaction_locks_all_callbacks_and_records_only_engineering(fixture):
    f = fixture
    done = run(f)
    assert f.state.events == ['backend', 'verifier', 'verifier']
    assert done.request.historical_binding.current_gradient_updates == 0
    assert json.loads(done.proof.observed_counts_json) == N.EXPECTED_BUDGET
    assert json.loads(done.proof.metrics_json)['correct_query_predictions'] == 2
    assert done.proof.native_closeout_status == 'pending_external_post_job'
    assert f.recorder.completion((f.plan,))['engineering_success'] == 1
    assert f.recorder.completion((f.plan,))['measured'] == 0
    assert failures(f) == []
    assert not (f.recorder.output_root / 'cells').exists()
    assert json.loads(done.request.historical_binding.claim_path.read_bytes())['payload']['worker'] == N.WORKER


@pytest.mark.parametrize('field,value', [('source_updates', 1), ('restore_count', 2), ('support_updates', 0),
    ('gradient_updates', True), ('target_inference_calls', 2), ('query_count', 3), ('model_constructions', 0), ('measured_cells', 1)])
def test_false_observed_budget_refused_after_valid_physical_baseline(fixture, field, value):
    fixture.state.mutate = lambda p, t, r, q: p['current_counter_ledger'].__setitem__(field, value)
    with pytest.raises(ValueError):
        run(fixture)
    reason = json.loads(failures(fixture)[0].read_bytes())['payload']['reason']
    assert reason['observed_numerical_counts'] is None and reason['numerical_execution_status'] == 'incomplete_unknown'


@pytest.mark.parametrize('where', ['envelope', 'target', 'restore'])
def test_old_request_bound_witness_cannot_replay_under_fresh_claim(fixture, where):
    def mutate(p, t, r, q):
        (p if where == 'envelope' else (t if where == 'target' else r)['current_worker_binding'])['request_sha256'] = 'f' * 64
    fixture.state.mutate = mutate
    with pytest.raises(ValueError, match='bound metadata'):
        run(fixture)


@pytest.mark.parametrize('kind', ['foreign_source', 'backbone_changed', 'head_unchanged', 'missing_tensor', 'false_observer'])
def test_full223_expected_state_and_head_only_changes_are_required(fixture, kind):
    def mutate(p, t, r, q):
        w = t['witnesses']
        if kind == 'foreign_source':
            for m in (t['source_state_tensors'], w['before_state_tensors'], w['after_state_tensors']):
                m['foreign_tensor'] = m.pop('backbone_000')
        elif kind == 'backbone_changed':
            w['after_state_tensors']['backbone_000'] = sha('unauthorized-change')
        elif kind == 'head_unchanged':
            w['after_state_tensors']['head.bias'] = w['before_state_tensors']['head.bias']
        elif kind == 'missing_tensor':
            del w['after_state_tensors']['backbone_000']
        else:
            w['calls']['query_forward'] = 2
    fixture.state.mutate = mutate
    with pytest.raises(ValueError):
        run(fixture)


@pytest.mark.parametrize('kind', ['nan', 'wrong_label', 'wrong_score', 'wrong_confusion'])
def test_current_metrics_rederived_and_nonfinite_or_false_values_rejected(fixture, kind):
    def mutate(p, t, r, q):
        if kind == 'nan':
            # Valid JSON containing nonfinite text is refused by canonical encoder.
            t['query_logits'][0][0] = float('nan')
        elif kind == 'wrong_label':
            t['query_targets'] = [1, 0]
        elif kind == 'wrong_score':
            t['balanced_accuracy'] = [0, 1]
        else:
            t['confusion_matrix'] = [[0, 1], [1, 0]]
    fixture.state.mutate = mutate
    with pytest.raises(ValueError):
        run(fixture)


def test_fresh_wrong_predictions_are_honestly_accepted_as_engineering_only(fixture):
    def mutate(p, t, r, q):
        t.update(query_logits=[[0, 1], [1, 0]], confusion_matrix=[[0, 1], [1, 0]], balanced_accuracy=[0, 1])
    fixture.state.mutate = mutate
    proof = run(fixture).proof
    assert json.loads(proof.metrics_json)['correct_query_predictions'] == 0
    assert proof.scientific_admission is False


@pytest.mark.parametrize('field', ['sgd_step', 'safetensors_load', 'tensor_backward'])
def test_counter_claim_cannot_replace_independent_runtime_observation(fixture, field):
    fixture.state.mutate = lambda p, t, r, q: p['observed_numerical_calls'].__setitem__(field, 0)
    with pytest.raises(ValueError, match='runtime numerical'):
        run(fixture)


@pytest.mark.parametrize('which', ['backend', 'verifier'])
def test_partial_execution_failure_records_unknown_and_never_retries(fixture, which):
    fixture.state.fail = which
    with pytest.raises(ValueError, match='injected'):
        run(fixture)
    reason = json.loads(failures(fixture)[0].read_bytes())['payload']['reason']
    assert reason['backend_started'] is True
    assert reason['observed_numerical_counts'] is None
    assert reason['numerical_execution_status'] == 'incomplete_unknown'
    assert reason['replay_permitted'] is False
    with pytest.raises((ValueError, FileExistsError)):
        run(fixture)
    assert fixture.state.events.count('backend') == 1


@pytest.mark.parametrize('filename', ['target-witness.json', 'restore-witness.json', 'request.json'])
def test_physical_proof_drift_before_second_verifier_is_rejected(fixture, filename):
    fixture.state.second_change = lambda q, opaque: (q.workspace / filename).write_bytes((q.workspace / filename).read_bytes() + b' ')
    with pytest.raises(ValueError):
        run(fixture)
    assert failures(fixture)


def test_native_cleanup_cannot_be_self_attested_inside_running_job(fixture):
    fixture.state.mutate = lambda p, t, r, q: p.__setitem__('native_closeout_status', 'accepted_closed_empty_absent')
    with pytest.raises(ValueError, match='self-attest'):
        run(fixture)


def test_current_input_mutation_is_refused_even_when_numerical_counts_match(fixture):
    fixture.state.mutate = lambda p, t, r, q: p['input_audit_after'].__setitem__('bytes', 1)
    with pytest.raises(ValueError, match='input audit'):
        run(fixture)


def test_frozen_historical_zero_binding_and_new_budget_are_not_interchangeable(fixture):
    done = run(fixture)
    payload = done.request.payload()
    assert payload['historical_binding']['current_restore_count'] == 0
    assert payload['expected_numerical_budget']['restore_count'] == 1
    payload['historical_binding']['current_restore_count'] = 1
    with pytest.raises(ValueError):
        N.load_worker_request(payload)


def test_recovery_reverifies_without_backend_and_cannot_create_missing_intent(fixture, monkeypatch):
    original = L._write_json_once
    def interrupted(path, payload):
        result = original(path, payload)
        if path.name == 'parent-attestation.json':
            raise RuntimeError('interrupted before engineering intent')
        return result
    monkeypatch.setattr(L, '_write_json_once', interrupted)
    with pytest.raises(N.RecoveryRequired):
        run(fixture)
    monkeypatch.setattr(L, '_write_json_once', original)
    before = fixture.state.events.count('backend')
    with pytest.raises(ValueError, match='intent'):
        N.recover_worker_case(**recovery_args(fixture))
    assert fixture.state.events.count('backend') == before == 1


def test_existing_terminal_recovery_is_idempotent_and_read_only(fixture):
    done = run(fixture)
    count = fixture.state.events.count('backend')
    N.recover_worker_case(**recovery_args(fixture))
    assert fixture.state.events.count('backend') == count == 1
    assert done.engineering_receipt.is_file()
    assert fixture.recorder.completion((fixture.plan,))['engineering_success'] == 1
    assert fixture.recorder.completion((fixture.plan,))['measured'] == 0


def test_recovery_external_attestation_digest_refuses_tampering_before_callback(fixture):
    run(fixture)
    args = recovery_args(fixture)
    before = list(fixture.state.events)
    path = fixture.parent / 'cases' / fixture.plan.case_id / 'parent-attestation.json'
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError):
        N.recover_worker_case(**args)
    assert fixture.state.events == before


def test_context_pins_drift_under_second_verifier_is_rejected(fixture):
    fixture.state.second_change = lambda q, opaque: q.historical_binding.pins_path.write_bytes(q.historical_binding.pins_path.read_bytes() + b' ')
    with pytest.raises(ValueError):
        run(fixture)
    assert failures(fixture)


def test_unused_scope_rejects_before_backend_or_claim(fixture):
    plan = replace(fixture.plan, model_seed=23)
    with pytest.raises(ValueError):
        run(fixture, plan=plan, workspace=fixture.parent / 'cases' / plan.case_id)
    assert fixture.state.events == []
    assert not fixture.recorder.output_root.exists()
