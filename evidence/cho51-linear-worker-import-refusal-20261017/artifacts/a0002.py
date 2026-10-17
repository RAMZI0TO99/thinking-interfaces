"""Real recorder/locks with explicitly fabricated metadata verifier callbacks.

No selector, model, restoration, array fixture or study case runs. The real
recorder imports its pinned numerical dependencies; these tests use metadata
only. Source capture, tiny artifact-role pins and stage verification are mocked.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import fields, replace, asdict
from pathlib import Path
from core.config import config_digest, load_toml, canonical_config_json
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_profile_binding import CHO_CLASSES, CHO_CHANNELS, ChoProfileAssets60Hz, ChoProfileBinding60Hz
from evaluation.phase2_records import envelope
from types import SimpleNamespace

import pytest

from core.provenance import SourceProvenance
from docs.phase2.cho51_linear_worker_route_v1 import worker_route as T

L = T.L


def sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


def unchecked(value, **changes):
    result = object.__new__(type(value))
    for item in fields(value):
        object.__setattr__(result, item.name, changes.get(item.name, getattr(value, item.name)))
    return result


def fabricated_route(context, plan):
    protocol = load_toml(Path(__file__).resolve().parents[3] / 'configs/phase2/protocol.toml')
    catalogs = tuple(TrialCatalog('cho2017', subject, T.TARGET.TRIAL_IDS, CHO_CLASSES * 21,
        CHO_CLASSES, f'{i:064x}', 'a' * 64) for i,subject in enumerate(T.TARGET.SUBJECTS,1))
    selection = envelope('source_selection', asdict(source_selection(catalogs,target='subject_02')))
    episode = envelope('episode_manifest', nested_episode(catalogs[1], shots=(1,5,10,20),
        protocol_sha256=config_digest(protocol)).payload())
    assets = {subject:ChoProfileAssets60Hz('b'*64,'c'*64,'d'*64) for subject in T.TARGET.SUBJECTS}
    plans = tuple(T.CasePlan('cho2017',subject,method,5,seed,1) for subject in T.TARGET.SUBJECTS
        for method in ('labram_linear','labram_lora','labram_full','eegnet') for seed in L.SEEDS)
    full = T.ChoFirstTrancheRoute(plans,catalogs,assets,canonical_config_json(protocol),
        {subject:canonical_config_json(selection) for subject in T.TARGET.SUBJECTS},
        {subject:canonical_config_json(episode) for subject in T.TARGET.SUBJECTS})
    decisions = tuple(T.PLANNER._json(T.PLANNER._bytes(L.ROOT, name)) for name in (
        'evidence/cho51-adoption-route-20261013/owner/adoption.json',
        'evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json',
        'evidence/phase2-readiness-20261012/worker/roster.json'))
    declared = T.PLANNER.prepare_route_contract((*decisions,T.PROTOCOL,T.CasePlan),catalogs)
    route = T.Cho51WorkerRoute(declared,full)
    contract = T.TARGET.prepare_target_contract(plan=plan,protocol_config=protocol,catalogs=catalogs,
        selection_record=selection,episode_record=episode,assets=assets)
    binding = ChoProfileBinding60Hz('cho2017','subject_02',5,CHO_CLASSES,CHO_CHANNELS,
        contract['protocol_sha256'],contract['episode_sha256'],catalogs[1].artifact_sha256,
        'b'*64,'c'*64,'a'*64,'e'*64,'f'*64,tuple(contract['support_trial_ids']),
        tuple(contract['query_trial_ids']),tuple(contract['support_indices']),tuple(contract['query_indices']),42,0,
        variant_config_sha256='d'*64,source_file='data/raw/moabb/cho2017/subject_02.mat',source_sha256='1'*64)
    return route,contract,binding


@pytest.fixture(scope='module')
def adopted():
    return tuple(T.CasePlan('cho2017', f'subject_{s:02d}', method, 5, seed, 1)
        for s in range(2, 53) for method in L.METHODS for seed in L.SEEDS)


@pytest.fixture
def fixture(tmp_path, monkeypatch, adopted):
    parent = tmp_path / 'p'
    root = parent / 'fixture'
    root.mkdir(parents=True)
    source = SourceProvenance('a' * 40, T.HISTORICAL_SOURCE['source_sha256'], True)
    monkeypatch.setattr(L.recorder_module, 'capture_source', lambda path: source)
    environment = L.recorder_module.environment_digest()
    owner = 'ae3295c2aa5acdfad2c9b2d7ffb602ec8b0daddb07b3d433d15dcaf9fd002709'
    pins_path = tmp_path / 'pins.json'
    pins_sha = L._write_json_once(pins_path, dict(canonical_source_sha256=L.CANONICAL_SOURCE_SHA256,
        owner_decision_sha256=owner))
    context = T.WorkerContext(parent, root, root / 'runs/phase2/lifecycle', pins_path,
        pins_sha, L.CANONICAL_SOURCE_SHA256, owner, adopted, source, environment)
    origin = tmp_path / 'origin'
    origin.mkdir()
    origin_ledger = origin / 'original-case-ledger.json'
    L._write_json_once(origin_ledger, dict(original_case_attempts_remaining=0, historical_gradient_updates=5253))
    ledger_bytes = origin_ledger.read_bytes()
    weights = origin / 'fabricated-weights.safetensors'
    weights.write_bytes(b'fabricated test bytes; no tensors')
    weights_sha = hashlib.sha256(weights.read_bytes()).hexdigest()
    baseline = origin / 'fabricated-baseline.safetensors'
    baseline.write_bytes(b'fabricated baseline bytes; invalid safe header')
    complete = origin / 'fabricated-evidence.json'
    complete.write_bytes(b'{"fabricated":true}')
    # Role plumbing is exercised with tiny, explicitly fabricated bytes. These
    # replacements do not qualify real checkpoints or accepted history.
    role_files = dict(selected_weights=weights, baseline_weights=baseline, complete_evidence=complete)
    monkeypatch.setattr(T.R, '_ROLE_SPECS', {name: (T._ROLE_SPECS[name][0], path.stat().st_size,
        hashlib.sha256(path.read_bytes()).hexdigest(), path.suffix) for name, path in role_files.items()})
    receipt = origin / 'fabricated-stage-receipt.json'
    receipt_sha = L._write_json_once(receipt, dict(fabricated=True, accepted=True))
    summary = dict(**{key: value for key, value in T._INTS.items() if key != 'attempt'},
        **T._FLAGS, restore_limits=[67108864, 67108864],
        selected_state_sha256=T.TARGET.SELECTED_STATE_SHA256, weights_file_sha256=weights_sha,
        manifest_sha256=sha('fabricated-manifest'), complete_evidence_sha256=sha('fabricated-evidence-logical'),
        recipe_sha256=sha('fabricated-recipe'), historical_case_id=T.HISTORICAL_CASE_ID,
        historical_source=dict(T.HISTORICAL_SOURCE),
        historical_plan=dict(dataset='cho2017',target_subject='subject_02',method='labram_linear',
            shots_per_class=5,model_seed=11,repetition=1))
    route, target_contract, target_binding = fabricated_route(context, plan=T.TARGET.PLAN)
    target_metrics = dict(query_logits=[[0.7, 1.4], [1.6, 0.5]], query_targets=[0, 1],
        query_predictions=[1, 0], confusion_matrix=[[0, 1], [1, 0]], balanced_accuracy=[0, 1],
        query_count=2, correct_query_predictions=0, scientific_predictive_performance_qualified=False)
    target_witness = dict(schema='cho51-linear-target-route-engineering-v1', accepted=True,
        engineering_only=True, scientific_admission=False, measured_cells=0, contract=target_contract,
        profile_binding=asdict(target_binding), profile_binding_sha256=target_binding.sha256,
        source_state_sha256=T.TARGET.SELECTED_STATE_SHA256, source_updates=0, support_updates=1,
        gradient_updates=1,current_restore_callback_calls=1,target_inference_calls=1,record_cell_calls=0,
        witnesses=dict(adapted_state_sha256='5bd88f2afb0a2e667e3576bb82c037e3314cce0e8cfb4383ee7439fee57787dd'),
        **{k:target_metrics[k] for k in ('query_logits','query_targets','confusion_matrix','balanced_accuracy','query_count')})
    target_files = {}
    for name in T._TARGET_FILE_DIGESTS:
        path = origin / (name + '.json')
        payload = target_witness if name == 'target_witness_file_sha256' else dict(fabricated=True, passed=True)
        summary[name] = L._write_json_once(path, payload)
        target_files[name] = str(path)
    summary.update(target_contract=target_contract,target_metrics=target_metrics,target_proof_paths=target_files,
        target_assets={s:asdict(a) for s,a in route.labram_assets.items()},target_profile_binding=asdict(target_binding),
        target_contract_sha256=config_digest(target_contract),target_metrics_sha256=config_digest(target_metrics),
        target_profile_binding_sha256=target_binding.sha256,target_source_state_sha256=T.TARGET.SELECTED_STATE_SHA256,
        target_adapted_state_sha256=target_witness['witnesses']['adapted_state_sha256'],
        worker_route_sha256=T._route_contract(route,T.TARGET.PLAN,context)[1])
    contract_path = origin / 'contract.json'
    contract = dict(schema='cho51_linear_worker_origin_contract_v1',
        files={**{str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in role_files.values()},
            str(receipt): receipt_sha, **{path:summary[name] for name,path in target_files.items()}},
        roles={**{str(path): name for name, path in role_files.items()}, str(receipt): 'metadata', **{path:'metadata' for path in target_files.values()}},
        summary=summary)
    contract_sha = L._write_json_once(contract_path, contract)
    recorder = T.CaseRecorder(root, output_root=context.recorder_root)
    plan = T.CasePlan('cho2017', 'subject_02', 'labram_linear', 5, 11, 1)
    state = SimpleNamespace(events=[], fail=None, proof_change=None, backend_change=None,
        verifier_calls=0, verifier_change=None)

    def assert_locked(request):
        with pytest.raises(RuntimeError, match='lock|reacquir'):
            recorder.claim(request.plan, worker='reentrant-forbidden', attempt=1)

    def backend(request, request_path, request_sha):
        state.events.append('backend')
        assert_locked(request)
        assert request_sha == request.sha256 == hashlib.sha256(request_path.read_bytes()).hexdigest()
        assert T.load_worker_request(json.loads(request_path.read_bytes())) == request
        if state.fail == 'backend':
            raise ValueError('injected backend failure')
        values = dict(request_sha256=request.sha256, case_id=request.plan.case_id,
            verified_origin_files=len(contract['files']), selected_state_sha256=summary['selected_state_sha256'],
            weights_file_sha256=summary['weights_file_sha256'])
        values.update({name: summary[name] for name in T._PROOF_DIGESTS})
        values.update({name: getattr(request, name) for name in T._BINDINGS})
        proof = T.VerifiedWorkerProof(**values)
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

    return SimpleNamespace(parent=parent, root=root, context=context, recorder=recorder, route=route,
        plan=plan, state=state, backend=backend, verifier=verifier, weights=weights,
        receipt=receipt, contract=contract, origin_contract_path=contract_path,
        origin_contract_file_sha256=contract_sha, origin_ledger=origin_ledger, ledger_bytes=ledger_bytes)


def run(f, **changes):
    args = dict(recorder=f.recorder, plan=f.plan, context=f.context, route=f.route,
        workspace=f.parent / 'cases' / f.plan.case_id, backend=f.backend, verifier=f.verifier,
        origin_contract_path=f.origin_contract_path,
        origin_contract_file_sha256=f.origin_contract_file_sha256)
    args.update(changes)
    return T.run_worker_case(**args)


def failures(f):
    return list((f.recorder.output_root / 'attempts').glob('*.failure.json'))


def no_science(f):
    assert not (f.recorder.output_root / 'cells').exists()
    assert not (f.recorder.output_root / 'successes').exists()
    assert not (f.recorder.output_root / 'publication_intents').exists()
    assert f.origin_ledger.read_bytes() == f.ledger_bytes


def recovery_args(f):
    workspace = f.parent / 'cases' / f.plan.case_id
    return dict(recorder=f.recorder, context=f.context, route=f.route, request_path=workspace / 'request.json',
        expected_request_sha256=hashlib.sha256((workspace / 'request.json').read_bytes()).hexdigest(),
        expected_attestation_sha256=hashlib.sha256((workspace / 'parent-attestation.json').read_bytes()).hexdigest(),
        verifier=f.verifier)


def test_staged_success_holds_real_lock_preserves_origin_and_zero_measured(fixture):
    f = fixture
    done = run(f)
    assert f.state.events == ['backend', 'verifier', 'verifier']
    assert done.request.historical_gradient_updates == 5253 and done.proof.current_gradient_updates == 0
    assert done.request.source_work_reused is done.proof.restore_work_reused is True
    assert done.proof.original_scientific_case_qualified is False
    assert done.engineering_receipt.is_file() and failures(f) == []
    claim = json.loads(done.request.claim_path.read_bytes())['payload']
    assert claim['worker'] == T.WORKER
    assert f.recorder.completion((f.plan,))['engineering_success'] == 1
    assert f.recorder.completion((f.plan,))['measured'] == 0
    no_science(f)


@pytest.mark.parametrize('field,value', [('target_subject', 'subject_01'), ('method', 'eegnet'), ('model_seed', 23)])
def test_other_case_scope_refuses_before_claim(fixture, field, value):
    f = fixture
    plan = replace(f.plan, **{field: value})
    with pytest.raises(ValueError):
        run(f, plan=plan, workspace=f.parent / 'cases' / plan.case_id)
    assert f.state.events == [] and not f.recorder.output_root.exists()


@pytest.mark.parametrize('field,value', [('current_gradient_updates', 1), ('historical_gradient_updates', 8),
    ('source_work_reused', False), ('current_gradient_updates', False), ('original_scientific_case_qualified', True), ('restored_tensors', 21),
    ('restored_elements', 5818139), ('head_parameters', 401), ('current_restore_count', 1),
    ('historical_restore_count', 1), ('current_target_inference_calls', 1),
    ('unchanged_single_root_factory_verified', True)])
def test_request_rejects_old_or_numerical_scope_and_bool_counts(fixture, field, value):
    payload = run(fixture).request.payload()
    payload[field] = value
    with pytest.raises(ValueError):
        T.load_worker_request(payload)


@pytest.mark.parametrize('kind', ['summary', 'contract_pin', 'inside_output'])
def test_malformed_or_unbound_origin_refuses_before_claim(fixture, kind):
    f = fixture
    args = {}
    if kind == 'summary':
        f.contract['summary']['restore_limits'] = [67108864, 4294967296]
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
    assert payload['reason']['original_scientific_case_qualified'] is False
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
    receipt = T.recover_worker_case(**args)
    assert T.recover_worker_case(**args) == receipt
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
        T.recover_worker_case(**args)
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


def test_proof_cannot_claim_current_training_or_qualified_scientific_case(fixture):
    f = fixture
    f.state.proof_change = lambda proof: unchecked(proof, current_gradient_updates=True,
        original_scientific_case_qualified=True)
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
        T.recover_worker_case(**args)
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
        T.recover_worker_case(**recovery_args(f))
    assert failures(f) == [] and not (f.recorder.output_root / 'engineering_intents').exists()


def test_historical_source_and_live_claim_are_distinct_with_same_plan_identity(fixture):
    f = fixture
    done = run(f)
    request = done.request
    assert request.fixture_git_commit == 'a' * 40
    assert request.fixture_git_commit != request.historical_git_commit
    assert request.fixture_source_sha256 == request.historical_source_sha256
    assert request.historical_git_commit == T.HISTORICAL_SOURCE['git_commit']
    assert request.historical_case_id == request.plan.case_id == T.HISTORICAL_CASE_ID
    claim = json.loads(request.claim_path.read_bytes())['payload']
    assert claim['source']['git_commit'] == request.fixture_git_commit
    assert f.contract['summary']['historical_source'] == T.HISTORICAL_SOURCE
    assert done.proof.fixture_git_commit == request.fixture_git_commit
    no_science(f)


@pytest.mark.parametrize('field,value', [
    ('historical_git_commit', 'b' * 40), ('historical_git_dirty', False),
    ('historical_source_sha256', 'f' * 64), ('historical_case_id', 'f' * 64),
    ('fixture_git_commit', 'unversioned-workspace'), ('fixture_git_dirty', 1)])
def test_serialized_request_does_not_rewrite_historical_or_untyped_current_source(fixture, field, value):
    payload = run(fixture).request.payload()
    payload[field] = value
    with pytest.raises(ValueError):
        T.load_worker_request(payload)


def test_live_git_drift_refuses_while_historical_git_remains_accepted_history(fixture, monkeypatch):
    f = fixture
    def changed(request, proof):
        if f.state.verifier_calls == 2:
            monkeypatch.setattr(L.recorder_module, 'capture_source', lambda path:
                SourceProvenance('b' * 40, request.fixture_source_sha256, True))
    f.state.verifier_change = changed
    with pytest.raises(ValueError, match='live fixture source'):
        run(f)
    assert len(failures(f)) == 1
    assert f.contract['summary']['historical_source'] == T.HISTORICAL_SOURCE
    no_science(f)


@pytest.mark.parametrize('kind', ['unknown_role', 'missing_role', 'wrong_selected_role',
    'historical_git', 'historical_plan', 'restore_size'])
def test_role_or_historical_contract_drift_refuses_before_claim(fixture, kind):
    f = fixture
    if kind == 'unknown_role':
        f.contract['roles'][str(f.receipt)] = 'arbitrary_large_blob'
    elif kind == 'missing_role':
        del f.contract['roles'][str(f.receipt)]
    elif kind == 'wrong_selected_role':
        f.contract['roles'][str(f.weights)] = 'metadata'
    elif kind == 'historical_git':
        f.contract['summary']['historical_source'] = dict(T.HISTORICAL_SOURCE, git_commit='b' * 40)
    elif kind == 'historical_plan':
        f.contract['summary']['historical_plan']['shots_per_class'] = True
    else:
        f.contract['summary']['restore_limits'] = [67108864, 1048576]
    f.origin_contract_path.write_bytes(L._encoded(f.contract))
    with pytest.raises(ValueError):
        run(f, origin_contract_file_sha256=hashlib.sha256(f.origin_contract_path.read_bytes()).hexdigest())
    assert f.state.events == [] and not f.recorder.output_root.exists()


def test_origin_reader_rejects_oversized_ordinary_metadata(tmp_path):
    path = tmp_path / 'oversized.json'
    with path.open('wb') as stream:
        stream.truncate(8 * 1024**2 + 1)
    with pytest.raises(ValueError, match='bounded'):
        T._read_origin_file(path, 'a' * 64, 'metadata')


@pytest.mark.parametrize('suffix', ['.npy', '.npz', '.safetensors', '.bin'])
def test_data_or_weight_bytes_cannot_use_metadata_role(tmp_path, suffix):
    path = tmp_path / ('forbidden' + suffix)
    path.write_bytes(b'not a metadata role')
    with pytest.raises(ValueError, match='recognized metadata'):
        T._read_origin_file(path, hashlib.sha256(path.read_bytes()).hexdigest(), 'metadata')


@pytest.mark.parametrize('role', ['selected_weights', 'baseline_weights', 'complete_evidence'])
def test_large_role_requires_exact_digest_before_read(fixture, role):
    f = fixture
    name = next(name for name, value in f.contract['roles'].items() if value == role)
    with pytest.raises(ValueError, match='role-bound pin'):
        T._read_origin_file(T.Path(name), 'b' * 64, role)


@pytest.mark.parametrize('role', ['selected_weights', 'baseline_weights', 'complete_evidence'])
def test_large_role_requires_exact_size_before_hashing(fixture, role):
    f = fixture
    name = next(name for name, value in f.contract['roles'].items() if value == role)
    path = T.Path(name)
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError, match='exact role size'):
        T._read_origin_file(path, f.contract['files'][name], role)


def test_weight_reader_uses_streaming_hash_without_loading_or_parsing(fixture, monkeypatch):
    f = fixture
    expected = f.contract['files'][str(f.weights)]
    original = T.Path.read_bytes
    def no_bulk_read(path):
        if path == f.weights:
            raise AssertionError('bulk read/weight decoding forbidden')
        return original(path)
    monkeypatch.setattr(T.Path, 'read_bytes', no_bulk_read)
    monkeypatch.setattr(T.json, 'loads', lambda *args, **kwargs:
        (_ for _ in ()).throw(AssertionError('no weight JSON/header parsing')))
    identity = T._read_origin_file(f.weights, expected, 'selected_weights')
    assert identity[-1] == expected and identity[2] == f.weights.stat().st_size


def test_production_role_exceptions_are_exact_known_artifacts():
    assert T._ROLE_SPECS == {
        'complete_evidence': (33554432, 23087023,
            'e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3', '.json'),
        'selected_weights': (67108864, 23294624,
            '3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048', '.safetensors'),
        'baseline_weights': (67108864, 23299672,
            '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8', '.safetensors'),
    }


@pytest.mark.parametrize('role', ['metadata', 'selected_weights'])
def test_origin_reader_rejects_multiple_hardlinks(fixture, role):
    f = fixture
    path = f.receipt if role == 'metadata' else f.weights
    alias = path.with_name(path.name + '.hardlink')
    os.link(path, alias)
    with pytest.raises(ValueError, match='single-linked'):
        T._read_origin_file(path, f.contract['files'][str(path)], role)


def test_origin_reader_rejects_non_direct_parent_traversal(fixture):
    f = fixture
    path = f.receipt.parent / '..' / f.receipt.parent.name / f.receipt.name
    with pytest.raises(ValueError, match='direct absolute'):
        T._read_origin_file(path, f.contract['files'][str(f.receipt)], 'metadata')


def test_resealed_claim_cannot_substitute_historical_git_for_current_git(fixture):
    f = fixture
    def changed(request, proof):
        if f.state.verifier_calls == 1:
            claim = json.loads(request.claim_path.read_bytes())
            claim['payload']['source'] = dict(T.HISTORICAL_SOURCE)
            request.claim_path.write_bytes(L._encoded(
                L.recorder_module.envelope('engineering_smoke', claim['payload'])))
    f.state.verifier_change = changed
    with pytest.raises(ValueError, match='claim'):
        run(f)
    assert len(failures(f)) == 1
    no_science(f)


@pytest.mark.parametrize('kind', ['foreign', 'legacy_full', 'reordered', 'owner'])
def test_actual_adopted_typed_route_and_order_are_required_before_claim(fixture, kind):
    f = fixture
    if kind == 'foreign':
        route = SimpleNamespace(plans=f.route.plans,
            owner_decision_sha256=f.context.owner_decision_sha256)
    elif kind == 'legacy_full':
        route = f.route._full_route
    elif kind == 'reordered':
        route = replace(f.route, _full_route=replace(f.route._full_route,
            plans=tuple(reversed(f.route._full_route.plans))))
    else:
        route = replace(f.route, contract=SimpleNamespace(plans=f.route.plans,
            owner_decision_sha256=sha('wrong-owner')))
    with pytest.raises(ValueError):
        run(f, route=route)
    assert f.state.events == [] and not f.recorder.output_root.exists()


@pytest.mark.parametrize('field', ['profile_b_artifact_sha256', 'profile_b_manifest_sha256',
                                 'variant_config_sha256', 'other_subject'])
def test_full_asset_map_cannot_be_substituted_even_when_target_contract_is_unchanged(fixture, field):
    f = fixture
    assets = dict(f.route.labram_assets)
    subject = 'subject_03' if field == 'other_subject' else 'subject_02'
    name = 'profile_b_artifact_sha256' if field == 'other_subject' else field
    assets[subject] = replace(assets[subject], **{name:sha('foreign-asset')})
    route = replace(f.route, _full_route=replace(f.route._full_route, labram_assets=assets))
    with pytest.raises(ValueError):
        run(f, route=route)
    assert f.state.events == []


@pytest.mark.parametrize('field,value', [('query_predictions', [0, 1]),
    ('confusion_matrix', [[1, 0], [0, 1]]), ('balanced_accuracy', [1, 1]),
    ('scientific_predictive_performance_qualified', True)])
def test_zero_of_two_target_result_cannot_be_upgraded(fixture, field, value):
    metrics = dict(fixture.contract['summary']['target_metrics'], **{field:value})
    with pytest.raises(ValueError):
        T.validate_target_metrics(metrics, fixture.contract['summary']['target_contract'])


@pytest.mark.parametrize('field,value', [('prior_target_support_updates', 0),
    ('prior_target_restore_count', True), ('prior_target_inference_calls', 2),
    ('prior_target_query_count', 3), ('current_support_updates', 1)])
def test_prior_target_work_is_distinct_from_zero_current_numerics(fixture, field, value):
    payload = run(fixture).request.payload()
    payload[field] = value
    with pytest.raises(ValueError):
        T.load_worker_request(payload)


def test_route_dispatch_is_executed_and_no_scientific_writer_is_used(fixture, monkeypatch):
    f = fixture
    original = T.Cho51WorkerRoute.inputs_for
    calls = []
    def dispatch(route, plan):
        calls.append(plan)
        return original(route, plan)
    def forbidden(*args, **kwargs):
        raise AssertionError('scientific cell publication is forbidden')
    monkeypatch.setattr(T.Cho51WorkerRoute, 'inputs_for', dispatch)
    monkeypatch.setattr(T.CaseRecorder, 'record_cell', forbidden)
    monkeypatch.setattr(T.L.recorder_module.LockedCase, 'record_cell', forbidden)
    done = run(f)
    assert calls and all(p == f.plan for p in calls)
    assert done.proof.prior_target_support_updates == 1
    assert done.proof.current_gradient_updates == done.proof.current_restore_count == 0
    assert done.proof.current_target_inference_calls == 0
    no_science(f)


def test_target_proof_replacement_is_detected_before_acceptance(fixture):
    f = fixture
    def change(request, proof):
        if f.state.verifier_calls == 1:
            path = Path(f.contract['summary']['target_proof_paths']['target_witness_file_sha256'])
            path.write_bytes(path.read_bytes() + b' ')
    f.state.verifier_change = change
    with pytest.raises(ValueError):
        run(f)
    assert len(failures(f)) == 1
    no_science(f)


def test_recovery_rechecks_actual_route_before_verifier(fixture):
    f = fixture
    run(f)
    args = recovery_args(f)
    assets = dict(f.route.labram_assets)
    assets['subject_02'] = replace(assets['subject_02'], profile_b_manifest_sha256=sha('changed'))
    args['route'] = replace(f.route, _full_route=replace(f.route._full_route, labram_assets=assets))
    events = list(f.state.events)
    with pytest.raises(ValueError):
        T.recover_worker_case(**args)
    assert f.state.events == events


@pytest.mark.parametrize('field', ['catalogs', 'selections', 'method_config_sha256'])
def test_declared_route_contract_cannot_drift_while_dispatch_inputs_stay_equal(fixture, field):
    f = fixture
    if field == 'catalogs':
        changed = tuple(reversed(f.route.contract.catalogs))
    elif field == 'selections':
        changed = dict(f.route.contract.selections)
        changed['subject_02'] = changed['subject_03']
    else:
        changed = dict(f.route.contract.method_config_sha256,labram_linear=sha('foreign-method-settings'))
    declared = replace(f.route.contract, **{field:changed})
    route = replace(f.route,contract=declared)
    assert route.inputs_for(f.plan) == f.route.inputs_for(f.plan)
    with pytest.raises(ValueError,match='five declared'):
        run(f,route=route)
    assert f.state.events == [] and not f.recorder.output_root.exists()
