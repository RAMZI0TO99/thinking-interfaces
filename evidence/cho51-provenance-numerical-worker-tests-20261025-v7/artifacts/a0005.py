"""Fabricated physical witnesses through actual parent/recorder identity locks.

Historical byte-role plumbing and source capture use the frozen metadata test
fixture. No factory restore, model, safe decoder, array load or target runs.
Every negative witness mutation first passes the valid composed proof verifier.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from core.provenance import SourceProvenance
from evaluation.phase2_records import envelope
from docs.phase2.cho51_linear_numerical_worker_v1.test_numerical_worker import (
    adopted, historical_fixture, fixture as historical_numerical_fixture,
)
from docs.phase2.cho51_provenance_numerical_worker_v2 import numerical_worker as Worker
from docs.phase2.cho51_provenance_numerical_worker_v2 import pipeline

Lifecycle, WorkerRoute, Factory = Worker.Lifecycle, Worker.WorkerRoute, Worker.Factory


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def clone(value):
    return json.loads(Factory.canonical(value))


@pytest.fixture
def fixture(historical_numerical_fixture, monkeypatch):
    given = historical_numerical_fixture
    summary = given.contract['summary']
    workspace = given.parent / 'cases' / given.plan.case_id
    publication = given.parent.parent / 'fabricated-publication.json'
    publication.write_bytes(b'{"fabricated":true}')
    producer = Factory.HistoricalProducer(Factory.canonical(WorkerRoute.HISTORICAL_SOURCE), summary['manifest_sha256'],
        '2' * 64, summary['complete_evidence_sha256'], WorkerRoute._ROLE_SPECS['complete_evidence'][2],
        summary['weights_file_sha256'], summary['selected_state_sha256'], summary['recipe_sha256'],
        '3' * 64, 'lr_1e-3', str(publication), digest(publication.read_bytes()))
    source = dict(git_commit=given.context.fixture_source.git_commit,
        git_dirty=given.context.fixture_source.git_dirty, source_sha256=Lifecycle.CANONICAL_SOURCE_SHA256)
    monkeypatch.setattr(Worker, 'capture_source', lambda root: SourceProvenance(**source))
    runtime = dict(python_full=Factory.sys.version, python=Factory.platform.python_version(),
        executable=str(Path(Factory.sys.executable).resolve()),
        **{name: Factory.version(name) for name in ('torch', 'numpy', 'braindecode')})
    sources = {str(Path(Worker.__file__).with_name(filename)): digest(Path(Worker.__file__).with_name(filename).read_bytes())
        for filename in ('numerical_worker.py', 'backend.py', 'pipeline.py')}
    extra_source = given.parent.parent / 'fabricated-executor-source.txt'
    extra_source.write_bytes(b'current executor bytes')
    sources[str(extra_source)] = digest(extra_source.read_bytes())
    binaries = {str(Path(executable).resolve()): digest(Path(executable).resolve().read_bytes())
        for executable in (Factory.sys.executable, Factory.sys._base_executable)}
    executor = Factory.ExecutorContext(str(Lifecycle.ROOT), Factory.canonical(source), Factory.canonical(runtime),
        Factory.canonical(sources), Factory.canonical(binaries))
    pins = json.loads(given.context.pins_path.read_bytes())
    pins.update(factory_producer=asdict(producer), factory_executor=asdict(executor),
        method_config_sha256='4' * 64, store_root=str(given.parent.parent / 'fabricated-store'))
    pins_sha = Lifecycle._write_json_once(given.context.pins_path.with_name('new-pins.json'), pins)
    given.context = replace(given.context, pins_path=given.context.pins_path.with_name('new-pins.json'),
        independent_pins_sha256=pins_sha)
    given.factory_template = Factory.RestoreRequest(producer, executor, Factory.canonical(asdict(given.plan)),
        str(given.parent.parent / 'fabricated-store'), str(workspace / 'factory'),
        str(given.recorder.output_root / 'claims' / (given.plan.case_id + '.attempt1.claim.json')),
        '0' * 64, str(given.context.pins_path), pins_sha, '4' * 64,
        summary['target_contract']['protocol_sha256'])
    given.state.events, given.state.verifier_calls = [], 0
    given.state.mutate, given.state.second_change = None, None
    given.state.force_valid_proof = False

    def write_current(request, payload, target, restore):
        for filename, value in (('target-witness.json', target), ('restore-witness.json', restore)):
            raw = Lifecycle._encoded(value)
            (request.workspace / filename).write_bytes(raw)
            payload['physical_outputs'][filename] = dict(sha256=digest(raw), bytes=len(raw))
        payload.update(target_route_witness=target, restore_witness=restore)
        raw = Lifecycle._encoded(envelope('engineering_smoke', payload))
        (request.workspace / 'current-execution.json').write_bytes(raw)
        return digest(raw)

    def backend(request, request_path, request_sha, live_lock):
        given.state.events.append('backend')
        assert type(live_lock.__self__) is Lifecycle.recorder_module.LockedCase
        assert live_lock.__func__ is Lifecycle.recorder_module.LockedCase._require_active
        live_lock()
        with pytest.raises(RuntimeError, match='lock|reacquir'):
            given.recorder.claim(request.plan, worker='forbidden-reentry')
        assert request_sha == request.sha256 == digest(request_path.read_bytes())
        assert request.factory_request.sha256 == digest(request.factory_request_path.read_bytes())
        assert Worker.load_worker_request(json.loads(request_path.read_bytes())) == request
        if given.state.fail == 'backend':
            raise ValueError('injected after composed backend entered')
        binding = Worker.build_current_binding(request)
        backend_attempt = Lifecycle._write_json_once(request.workspace / 'backend-attempt.json',
            dict(schema='cho51_provenance_numerical_backend_attempt_v1', **binding,
                engineering_only=True, scientific_admission=False))
        factory = request.factory_request
        attempt_sha = Lifecycle._write_json_once(Path(factory.workspace) / 'restore-attempt.json',
            dict(schema='cho51_provenance_restore_attempt_v1', request_sha256=factory.sha256,
                claim_sha256=factory.claim_sha256, pins_sha256=factory.pins_sha256, scientific_admission=False))
        current = dict(git_commit=request.historical_binding.fixture_git_commit,
            source_sha256=request.historical_binding.fixture_source_sha256,
            git_dirty=request.historical_binding.fixture_git_dirty)
        target = clone(given.current_target)
        target.update(current_worker_binding=binding, provenance=dict(current=current, historical=WorkerRoute.HISTORICAL_SOURCE))
        restore = dict(schema='cho51_provenance_restored_source_v1', passed=True,
            current_worker_binding=binding, request_sha256=factory.sha256, claim_sha256=factory.claim_sha256,
            pins_sha256=factory.pins_sha256, restore_attempt_sha256=attempt_sha,
            workspace=factory.workspace, store_root=factory.store_root, historical_source=WorkerRoute.HISTORICAL_SOURCE,
            current_executor_source=source, current_executor_runtime=runtime,
            historical_runtime=dict(python='fabricated-history'),
            historical_publication_file_sha256=producer.publication_file_sha256,
            manifest_sha256=producer.manifest_sha256, manifest_file_sha256=producer.manifest_file_sha256,
            complete_evidence_sha256=producer.evidence_sha256, complete_evidence_file_sha256=producer.evidence_file_sha256,
            selection_contract_sha256=producer.selection_contract_sha256, model_recipe_sha256=producer.model_recipe_sha256,
            model_state_sha256=producer.model_state_sha256, weights_sha256=producer.weights_sha256,
            adapter_class='evaluation.phase2_pilot.LaBraMTunedAdapter', complete_metadata_verified=True,
            selected_restores=1, model_constructions=1, safe_decodes=2, strict_state_loads=2,
            tensor_count=223, elements=5818138, source_updates=0, support_updates=0, query_calls=0,
            measured_cells=0, maximum_weights_bytes=67108864, weights_bytes=23294624,
            engineering_only=True, scientific_admission=False, unchanged_single_root_factory_verified=False,
            native_closeout_status='pending_external_post_job')
        observer = dict(Worker.OBSERVER_COUNTS, numerical_calls=dict(module_load_state_dict=2,
            safetensors_load=2, optimizer_init=1, sgd_step=1, tensor_backward=1,
            autograd_backward=1, model_module_init=227))
        audit = dict(bytes=734579463, files=213,
            fixture_root=str(Lifecycle.ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture'),
            input_identity_file_sha256='34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
        payload = dict(schema='cho51_provenance_numerical_execution_v1', **binding,
            backend_attempt_file_sha256=backend_attempt, source_fixture=audit['fixture_root'],
            current_control_source=current, historical_source=WorkerRoute.HISTORICAL_SOURCE,
            current_executor_source=source, expected_numerical_budget=dict(Worker.EXPECTED_BUDGET),
            current_counter_ledger=dict(Worker.EXPECTED_BUDGET), independent_observer=observer,
            input_audit_before=clone(audit), input_audit_after=clone(audit), physical_outputs={},
            engineering_only=True, scientific_admission=False, measured_cells=0,
            native_closeout_status='pending_external_post_job')
        opaque = write_current(request, payload, target, restore)
        baseline = Worker.verify_current_execution(request, opaque)
        if given.state.mutate:
            given.state.mutate(payload, target, restore, request)
            opaque = write_current(request, payload, target, restore)
        given.state.last_request, given.state.baseline_proof = request, baseline
        return baseline if given.state.force_valid_proof else opaque

    def verifier(request, opaque):
        given.state.events.append('verifier')
        given.state.verifier_calls += 1
        with pytest.raises(RuntimeError, match='lock|reacquir'):
            given.recorder.claim(request.plan, worker='forbidden-reentry')
        if given.state.fail == 'verifier':
            raise ValueError('injected independent composed verifier failure')
        if given.state.second_change and given.state.verifier_calls == 2:
            given.state.second_change(request)
        if given.state.force_valid_proof:
            return given.state.baseline_proof
        return Worker.verify_current_execution(request, opaque)

    given.backend, given.verifier, given.write_current = backend, verifier, write_current
    given.extra_source = extra_source
    return given


def run(given, **changes):
    arguments = dict(recorder=given.recorder, plan=given.plan, context=given.context,
        route=given.route, workspace=given.parent / 'cases' / given.plan.case_id,
        origin_contract_path=given.origin_contract_path,
        origin_contract_file_sha256=given.origin_contract_file_sha256,
        factory_template=given.factory_template, backend=given.backend, verifier=given.verifier)
    arguments.update(changes)
    return pipeline.run_parent_pipeline(**arguments)


def failures(given):
    return list((given.recorder.output_root / 'attempts').glob('*.failure.json'))


def recovery_args(given):
    workspace = given.parent / 'cases' / given.plan.case_id
    return dict(recorder=given.recorder, context=given.context, route=given.route,
        request_path=workspace / 'request.json', expected_request_sha256=digest((workspace / 'request.json').read_bytes()),
        expected_attestation_sha256=digest((workspace / 'parent-attestation.json').read_bytes()), verifier=given.verifier)


def test_parent_composes_both_requests_under_actual_lock_and_one_outer_terminal(fixture):
    completed = run(fixture)
    assert fixture.state.events == ['backend', 'verifier', 'verifier']
    assert completed.request.sha256 != completed.request.factory_request.sha256
    assert completed.request.factory_request.claim_sha256 == completed.request.historical_binding.claim_file_sha256
    assert completed.request.factory_request_path.read_bytes()[-1:] != b'\n'
    assert completed.request_path.read_bytes()[-1:] == b'\n'
    assert fixture.recorder.completion((fixture.plan,))['engineering_success'] == 1
    assert fixture.recorder.completion((fixture.plan,))['measured'] == 0
    assert not (fixture.recorder.output_root / 'cells').exists()
    assert not failures(fixture)


def test_returned_payload_cannot_mutate_the_immutable_request_or_budgets(fixture):
    completed = run(fixture)
    request = completed.request
    expected = clone(request.payload())
    original_sha256 = request.sha256
    returned = request.payload()
    returned['expected_numerical_budget']['support_updates'] = 999
    returned['expected_observer_counts']['npz_loads'] = 999
    assert request.payload() == expected
    assert request.sha256 == original_sha256
    assert Worker.EXPECTED_BUDGET['support_updates'] == 1
    assert Worker.OBSERVER_COUNTS['npz_loads'] == 6


@pytest.mark.parametrize('field,value', [('restore_count', 2), ('source_updates', 1),
    ('support_updates', 0), ('gradient_updates', True), ('target_inference_calls', 2),
    ('query_count', 3), ('model_constructions', 0), ('measured_cells', True)])
def test_aggregate_counts_reject_after_valid_baseline(fixture, field, value):
    fixture.state.mutate = lambda payload, target, restore, request: payload['current_counter_ledger'].__setitem__(field, value)
    with pytest.raises(ValueError):
        run(fixture)


@pytest.mark.parametrize('field,value', [('source_updates', 1), ('support_updates', 1),
    ('query_calls', 1), ('selected_restores', True), ('maximum_weights_bytes', 67108865),
    ('tensor_count', 222), ('safe_decodes', 1)])
def test_factory_local_counts_cannot_be_relabelled_as_target_work(fixture, field, value):
    fixture.state.mutate = lambda payload, target, restore, request: restore.__setitem__(field, value)
    with pytest.raises(ValueError, match='factory-local'):
        run(fixture)


@pytest.mark.parametrize('field', ['factory_restore_returns', 'factory_restore_calls', 'profile_a_loads',
    'profile_b_loads', 'npz_loads', 'clone_reinitializations', 'constructor_dummy_forward_calls'])
def test_independent_observer_budget_refused_after_valid_baseline(fixture, field):
    fixture.state.mutate = lambda payload, target, restore, request: payload['independent_observer'].__setitem__(field, 0)
    with pytest.raises(ValueError, match='observer'):
        run(fixture)


@pytest.mark.parametrize('field', ['safetensors_load', 'sgd_step', 'tensor_backward'])
def test_independent_numerical_calls_cannot_be_replaced_by_ledger(fixture, field):
    fixture.state.mutate = lambda payload, target, restore, request: payload['independent_observer']['numerical_calls'].__setitem__(field, 0)
    with pytest.raises(ValueError, match='runtime numerical'):
        run(fixture)


@pytest.mark.parametrize('where', ['outer', 'target', 'factory'])
def test_stale_outer_binding_refused_on_each_witness(fixture, where):
    def mutate(payload, target, restore, request):
        selected = payload if where == 'outer' else (target if where == 'target' else restore)['current_worker_binding']
        selected['request_sha256'] = 'f' * 64
    fixture.state.mutate = mutate
    with pytest.raises(ValueError):
        run(fixture)


@pytest.mark.parametrize('field', ['request_sha256', 'claim_sha256', 'pins_sha256', 'model_state_sha256',
    'model_recipe_sha256', 'restore_attempt_sha256'])
def test_factory_subrequest_and_artifact_bindings_rejected(fixture, field):
    fixture.state.mutate = lambda payload, target, restore, request: restore.__setitem__(field, 'f' * 64)
    with pytest.raises(ValueError):
        run(fixture)


@pytest.mark.parametrize('kind', ['backbone', 'head_unchanged', 'missing_tensor', 'gradient', 'labels', 'nonfinite', 'score'])
def test_complete_state_gradients_and_finite_metrics_rederived(fixture, kind):
    def mutate(payload, target, restore, request):
        if kind == 'backbone':
            target['witnesses']['after_state_tensors']['backbone_000'] = 'f' * 64
        elif kind == 'head_unchanged':
            target['witnesses']['after_state_tensors']['head.bias'] = target['source_state_tensors']['head.bias']
        elif kind == 'missing_tensor':
            target['witnesses']['after_state_tensors'].pop('backbone_000')
        elif kind == 'gradient':
            target['witnesses']['gradient_norms']['head.bias'] = 0
        elif kind == 'labels':
            target['query_targets'] = [1, 0]
        elif kind == 'nonfinite':
            target['query_logits'][0][0] = float('nan')
        else:
            target['balanced_accuracy'] = [0, 1]
    fixture.state.mutate = mutate
    with pytest.raises(ValueError):
        run(fixture)


def test_wrong_fresh_predictions_remain_honest_engineering_results(fixture):
    def mutate(payload, target, restore, request):
        target.update(query_logits=[[0, 1], [1, 0]], confusion_matrix=[[0, 1], [1, 0]], balanced_accuracy=[0, 1])
    fixture.state.mutate = mutate
    proof = run(fixture).proof
    assert json.loads(proof.metrics_json)['correct_query_predictions'] == 0
    assert proof.measured_cells == 0 and proof.scientific_admission is False


@pytest.mark.parametrize('filename', ['request.json', 'target-witness.json', 'restore-witness.json',
    'factory/request.json', 'factory/restore-attempt.json', 'backend-attempt.json'])
def test_same_byte_file_replacement_between_verifiers_refused(fixture, filename):
    def changed(request):
        path = request.workspace / filename
        temporary = path.with_name(path.name + '.replacement')
        temporary.write_bytes(path.read_bytes())
        temporary.replace(path)
    fixture.state.second_change = changed
    with pytest.raises(ValueError):
        run(fixture)


@pytest.mark.parametrize('filename', ['pins', 'executor_source'])
def test_source_or_pins_drift_is_refused(fixture, filename):
    def changed(request):
        path = request.historical_binding.pins_path if filename == 'pins' else fixture.extra_source
        path.write_bytes(path.read_bytes() + b' ')
    fixture.state.second_change = changed
    with pytest.raises(ValueError):
        run(fixture)


@pytest.mark.parametrize('kind', ['backend', 'verifier'])
def test_backend_entered_failure_preserves_unknown_counts_and_no_replay(fixture, kind):
    fixture.state.fail = kind
    with pytest.raises(ValueError, match='injected'):
        run(fixture)
    reason = json.loads(failures(fixture)[0].read_bytes())['payload']['reason']
    assert reason['observed_numerical_counts'] is None
    assert reason['numerical_execution_status'] == 'incomplete_unknown'
    assert reason['replay_permitted'] is False
    with pytest.raises((ValueError, FileExistsError)):
        run(fixture)
    assert fixture.state.events.count('backend') == 1


def test_apparently_valid_callback_proof_does_not_bypass_physical_verification(fixture):
    fixture.state.force_valid_proof = True
    fixture.state.mutate = lambda payload, target, restore, request: restore.__setitem__('query_calls', 1)
    with pytest.raises(ValueError):
        run(fixture)


def test_native_closeout_cannot_be_self_attested(fixture):
    fixture.state.mutate = lambda payload, target, restore, request: payload.__setitem__('native_closeout_status', 'closed')
    with pytest.raises(ValueError, match='self-attest'):
        run(fixture)


def test_recovery_replays_existing_intent_without_factory_or_backend(fixture, monkeypatch):
    done = run(fixture)
    from docs.phase2.cho51_provenance_restore_v1.factory import ProvenanceRestoreFactory
    def forbidden(*args, **kwargs):
        raise AssertionError('recovery must never call the numerical backend or factory')
    monkeypatch.setattr(ProvenanceRestoreFactory, 'authenticate', forbidden)
    monkeypatch.setattr(ProvenanceRestoreFactory, 'restore', forbidden)
    fixture.backend = forbidden
    pipeline.recover_parent_pipeline(**recovery_args(fixture))
    assert fixture.state.events.count('backend') == 1
    assert done.engineering_receipt.is_file()


def test_durable_attestation_quarantines_without_fabricating_missing_intent(fixture, monkeypatch):
    original = Lifecycle._write_json_once
    def interrupted(path, payload):
        result = original(path, payload)
        if path.name == 'parent-attestation.json':
            raise RuntimeError('interrupted after durable outer attestation')
        return result
    monkeypatch.setattr(Lifecycle, '_write_json_once', interrupted)
    with pytest.raises(Worker.RecoveryRequired):
        run(fixture)
    monkeypatch.setattr(Lifecycle, '_write_json_once', original)
    assert not failures(fixture)
    with pytest.raises(ValueError, match='intent'):
        pipeline.recover_parent_pipeline(**recovery_args(fixture))
    assert fixture.state.events.count('backend') == 1


def test_missing_or_mixed_adopted_route_refused_before_claim(fixture):
    with pytest.raises(ValueError):
        changed = replace(fixture.route, contract=replace(fixture.route.contract, plans=()))
        run(fixture, route=changed)
    assert fixture.state.events == []
    assert not fixture.recorder.output_root.exists()


def test_before_backend_failure_records_zero_and_does_not_retry(fixture, monkeypatch):
    def fail_before_backend(path, request):
        raise ValueError('injected durable subrequest refusal before backend')
    monkeypatch.setattr(Worker, '_write_factory_request', fail_before_backend)
    with pytest.raises(ValueError, match='before backend'):
        run(fixture)
    reason = json.loads(failures(fixture)[0].read_bytes())['payload']['reason']
    assert reason['backend_started'] is False
    assert reason['numerical_execution_status'] == 'not_started'
    assert reason['observed_numerical_counts'] == {name: 0 for name in Worker.EXPECTED_BUDGET}
    assert fixture.state.events == []


def test_noop_lock_callback_rejected_by_reusable_backend_after_valid_parent_baseline(fixture):
    from contextlib import nullcontext
    from docs.phase2.cho51_provenance_numerical_worker_v2.backend import FactoryNumericalBackend
    completed = run(fixture)
    backend = FactoryNumericalBackend(route=fixture.route, source_fixture=fixture.root,
        method_config={}, protocol_config={}, input_audit=lambda: {}, observer_snapshot=lambda: {},
        execution_scope=lambda *args: nullcontext())
    with pytest.raises(ValueError, match='actual canonical live lock'):
        backend(completed.request, completed.request_path, completed.request.sha256, lambda: None)


def test_completed_parent_cannot_replay_backend_or_create_another_terminal(fixture):
    run(fixture)
    with pytest.raises((ValueError, FileExistsError)):
        run(fixture)
    assert fixture.state.events.count('backend') == 1
    assert fixture.recorder.completion((fixture.plan,))['engineering_success'] == 1


def test_independent_input_inventory_is_rechecked_after_numerical_work(fixture):
    fixture.state.mutate = lambda payload, target, restore, request: payload['input_audit_after'].__setitem__('files', 212)
    with pytest.raises(ValueError, match='input audit'):
        run(fixture)
