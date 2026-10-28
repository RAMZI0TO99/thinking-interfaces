"""Fabricated byte/contract boundaries; no tensor decoding or numerical execution.

Only the independently admitted integration qualifies a real restored adapter.
These tests do not create or modify historical artifacts or canonical sources.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import asdict, replace
from importlib.metadata import version
from pathlib import Path

import pytest

from core.config import config_digest
from core.provenance import capture_source
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan, CaseRecorder
from docs.phase2.cho51_provenance_restore_v1 import factory as F

ROOT = Path(__file__).resolve().parents[3]
PLAN = dict(dataset='cho2017', target_subject='subject_02', method='labram_linear',
    shots_per_class=5, model_seed=11, repetition=1)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = F.canonical(value).encode()
    path.write_bytes(raw)
    return digest(raw)


@pytest.fixture
def fabricated(tmp_path):
    store, workspace = tmp_path / 'store', tmp_path / 'case'
    workspace.mkdir()
    producer_source = dict(git_commit='a' * 40, git_dirty=True, source_sha256='b' * 64)
    protocol_sha = 'c' * 64
    recipe = dict(schema='fabricated_architecture', method='labram_linear')
    state_sha = 'd' * 64
    weights = b'fabricated metadata fixture; never decode'
    weights_sha = digest(weights)
    candidate = dict(name='lr_1e-3', source=dict(method='linear'), support=dict(method='linear'))
    contract = dict(source=producer_source, protocol_sha256=protocol_sha,
        candidates=[candidate], runtime=dict(python='historical'))
    evidence = envelope('engineering_smoke', dict(purpose='bounded_labram_source_selection',
        complete=True, outer_target_predictions_performed=False, contract=contract,
        contract_sha256=config_digest(contract), selected_candidate='lr_1e-3',
        folds=[], scores=[], final_source_fit=dict(candidate='lr_1e-3',
            candidate_sha256=config_digest(candidate), fitted_state_sha256=state_sha)))
    evidence_sha = evidence['sha256']
    evidence_path = store / 'evidence' / (evidence_sha + '.json')
    evidence_file_sha = write(evidence_path, evidence)
    weights_path = store / 'weights' / (weights_sha + '.safetensors')
    weights_path.parent.mkdir()
    weights_path.write_bytes(weights)
    manifest = envelope('engineering_smoke', dict(purpose='selected_source_snapshot',
        scope='engineering_only', scientific_evaluation=False, source=producer_source,
        selected_candidate='lr_1e-3', protocol_config_sha256=protocol_sha,
        selection_contract_sha256=config_digest(contract), evidence_sha256=evidence_sha,
        weights_sha256=weights_sha, model_state_sha256=state_sha, model_recipe=recipe,
        model_recipe_sha256=config_digest(recipe), model_class='encoder.labram.LaBraMClassifier',
        tensor_schema={}, weights_file='weights/' + weights_path.name,
        evidence_file='evidence/' + evidence_path.name))
    manifest_sha = manifest['sha256']
    manifest_path = store / 'manifests' / (manifest_sha + '.json')
    manifest_file_sha = write(manifest_path, manifest)
    publication_path = tmp_path / 'publication.json'
    publication = dict(schema='cho51_linear_staged_publication_v1', passed=True,
        engineering_only=True, scientific_admission=False, measured_cells=0,
        historical_full_selector_verified=True, source=producer_source, case=PLAN,
        manifest_sha256=manifest_sha, manifest_file_sha256=manifest_file_sha,
        evidence_sha256=evidence_sha, evidence_file_sha256=evidence_file_sha,
        weights_file_sha256=weights_sha, model_state_sha256=state_sha,
        model_recipe_sha256=config_digest(recipe), selected_candidate='lr_1e-3',
        manifest_path=str(manifest_path), evidence_path=str(evidence_path),
        weights_path=str(weights_path), weights_bytes=len(weights))
    publication_sha = write(publication_path, publication)
    producer = F.HistoricalProducer(F.canonical(producer_source), manifest_sha, manifest_file_sha,
        evidence_sha, evidence_file_sha, weights_sha, state_sha, config_digest(recipe),
        config_digest(contract), 'lr_1e-3', str(publication_path), publication_sha)
    runtime = dict(python_full=sys.version, python=platform.python_version(),
        executable=str(Path(sys.executable).resolve()),
        **{name: version(name) for name in ('torch', 'numpy', 'braindecode')})
    sources = {str(path): digest(path.read_bytes()) for path in (
        Path(F.__file__).absolute(), Path(F.__file__).with_name('selection.py').absolute())}
    marker = tmp_path / 'execution-source.txt'
    marker.write_bytes(b'independently pinned execution helper')
    sources[str(marker)] = digest(marker.read_bytes())
    binaries = {str(Path(path).resolve()): digest(Path(path).resolve().read_bytes())
        for path in (sys.executable, sys._base_executable)}
    executor = F.ExecutorContext(str(ROOT), F.canonical(asdict(capture_source(ROOT))),
        F.canonical(runtime), F.canonical(sources), F.canonical(binaries))
    recorder = CaseRecorder(tmp_path / 'fixture')
    session_context = recorder.case_session(CasePlan(**PLAN))
    session = session_context.__enter__()
    claim_path = session.claim_new(worker='fabricated_provenance_factory_test', attempt=1)
    claim_sha = digest(claim_path.read_bytes())
    pins_path = tmp_path / 'pins.json'
    pins_sha = write(pins_path, dict(factory_producer=asdict(producer), factory_executor=asdict(executor),
        factory_claim=dict(recorder_root=str(recorder._root), output_root=str(recorder.output_root),
            source=asdict(capture_source(recorder._root)), worker='fabricated_provenance_factory_test', attempt=1)))
    request = F.RestoreRequest(producer, executor, F.canonical(PLAN), str(store), str(workspace),
        str(claim_path), claim_sha, str(pins_path), pins_sha, 'e' * 64, protocol_sha)
    request_path = workspace / 'request.json'
    request_sha = write(request_path, request.payload())
    result = dict(request=request, request_path=request_path, request_sha=request_sha,
        locked=session._require_active, session=session, store=store, manifest=manifest, manifest_path=manifest_path,
        evidence=evidence, evidence_path=evidence_path, weights_path=weights_path,
        publication=publication, publication_path=publication_path, marker=marker,
        claim_path=claim_path, pins_path=pins_path)
    try:
        yield result
    finally:
        session_context.__exit__(None, None, None)


def factory(fabricated, request=None, locked=None):
    request = fabricated['request'] if request is None else request
    return F.ProvenanceRestoreFactory(request, fabricated['request_path'], request.sha256,
        fabricated['locked'] if locked is None else locked)


def rebind_manifest(fabricated, payload):
    manifest = envelope('engineering_smoke', payload)
    manifest_path = fabricated['store'] / 'manifests' / (manifest['sha256'] + '.json')
    manifest_file_sha = write(manifest_path, manifest)
    publication = dict(fabricated['publication'], manifest_sha256=manifest['sha256'],
        manifest_file_sha256=manifest_file_sha, manifest_path=str(manifest_path))
    publication_sha = write(fabricated['publication_path'], publication)
    producer = replace(fabricated['request'].producer, manifest_sha256=manifest['sha256'],
        manifest_file_sha256=manifest_file_sha, publication_file_sha256=publication_sha)
    pins = json.loads(fabricated['pins_path'].read_bytes())
    pins['factory_producer'] = asdict(producer)
    pins_sha = write(fabricated['pins_path'], pins)
    request = replace(fabricated['request'], producer=producer, pins_sha256=pins_sha)
    write(fabricated['request_path'], request.payload())
    return request


def test_metadata_authentication_keeps_roles_distinct_and_decodes_no_weights(fabricated):
    result = factory(fabricated).authenticate()
    assert result.weights_identity[2] == len(b'fabricated metadata fixture; never decode')
    assert result.manifest_json == F.canonical(fabricated['manifest'])
    assert result.evidence_json == F.canonical(fabricated['evidence'])
    assert F._source(fabricated['request'].producer.source_json) != F._source(fabricated['request'].executor.source_json)


def test_immutable_request_roundtrip_and_physical_digest(fabricated):
    request = fabricated['request']
    assert F.load_request(request.payload()) == request
    assert request.sha256 == fabricated['request_sha']
    with pytest.raises((AttributeError, TypeError)):
        request.producer.weights_sha256 = 'f' * 64


@pytest.mark.parametrize('name', ['manifest_path', 'evidence_path', 'weights_path',
    'publication_path', 'request_path', 'claim_path', 'pins_path', 'marker'])
def test_physical_tampering_is_rejected_before_any_decode(fabricated, name):
    path = fabricated[name]
    raw = path.read_bytes()
    path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
    with pytest.raises(ValueError):
        factory(fabricated).authenticate()


@pytest.mark.parametrize('name', ['weights_sha256', 'model_state_sha256', 'model_recipe_sha256',
    'selection_contract_sha256', 'evidence_sha256', 'manifest_sha256', 'publication_file_sha256'])
def test_substituted_ancestor_pins_cannot_rebind_admitted_request(fabricated, name):
    producer = replace(fabricated['request'].producer, **{name: 'f' * 64})
    changed = replace(fabricated['request'], producer=producer)
    write(fabricated['request_path'], changed.payload())
    with pytest.raises(ValueError, match='independently admitted pins'):
        factory(fabricated, changed).authenticate()


def test_self_consistent_foreign_producer_envelope_still_fails_admitted_pins(fabricated):
    source = F._source(fabricated['request'].producer.source_json)
    source['git_commit'] = 'f' * 40
    producer = replace(fabricated['request'].producer, source_json=F.canonical(source))
    changed = replace(fabricated['request'], producer=producer)
    write(fabricated['request_path'], changed.payload())
    with pytest.raises(ValueError, match='independently admitted pins'):
        factory(fabricated, changed).authenticate()


@pytest.mark.parametrize('field', ['claim_sha256', 'pins_sha256', 'method_config_sha256', 'protocol_config_sha256'])
def test_stale_request_bindings_refused_by_durable_request(fabricated, field):
    changed = replace(fabricated['request'], **{field: 'f' * 64})
    with pytest.raises(ValueError):
        factory(fabricated, changed).authenticate()


def test_live_lock_loss_prevents_reads(fabricated):
    with pytest.raises(ValueError, match='actual canonical LockedCase'):
        factory(fabricated, locked=lambda: False).authenticate()


def test_live_lock_loss_at_release_boundary_is_rejected(fabricated):
    given = factory(fabricated)
    fabricated['session']._closed = True
    with pytest.raises(RuntimeError, match='session is closed'):
        given.authenticate()


@pytest.mark.parametrize('field', ['source_json', 'runtime_json', 'source_files_json', 'runtime_files_json'])
def test_foreign_executor_cannot_rebind_independent_pins(fabricated, field):
    executor = fabricated['request'].executor
    value = F._json_field(getattr(executor, field))
    if field == 'source_json':
        value['git_commit'] = 'f' * 40
    elif field == 'runtime_json':
        value['python_full'] += ' foreign'
    else:
        value[next(iter(value))] = 'f' * 64
    changed = replace(fabricated['request'], executor=replace(executor, **{field: F.canonical(value)}))
    write(fabricated['request_path'], changed.payload())
    with pytest.raises(ValueError, match='independently admitted pins'):
        factory(fabricated, changed).authenticate()


@pytest.mark.parametrize('field,member', [('target_subject', 'subject_01'), ('method', 'labram_lora'),
    ('shots_per_class', True), ('repetition', 2), ('model_seed', 12)])
def test_unadopted_or_unqualified_case_refused(fabricated, field, member):
    plan = dict(PLAN)
    plan[field] = member
    with pytest.raises(ValueError, match='adopted linear'):
        replace(fabricated['request'], plan_json=F.canonical(plan))


@pytest.mark.parametrize('maximum', [True, 0, -1, 2 * 1024**3 + 1])
def test_every_direct_reader_requires_explicit_finite_bound(tmp_path, maximum):
    path = tmp_path / 'bytes'
    path.write_bytes(b'x')
    with pytest.raises(ValueError):
        F.read_pinned(path, digest(b'x'), maximum)


def test_oversized_file_refused_before_open(tmp_path):
    path = tmp_path / 'bytes'
    path.write_bytes(b'oversized')
    with pytest.raises(ValueError, match='byte bound'):
        F.read_pinned(path, digest(b'oversized'), 2)


def test_hardlinked_regular_file_is_rejected(tmp_path):
    import os
    path, alias = tmp_path / 'bytes', tmp_path / 'alias'
    path.write_bytes(b'x')
    os.link(path, alias)
    with pytest.raises(ValueError, match='single-link'):
        F.read_pinned(path, digest(b'x'), 2)


@pytest.mark.parametrize('value', ['{"a":1,"a":2}', '{"a":NaN}', '[1,2]'])
def test_noncanonical_or_ambiguous_json_is_rejected(value):
    with pytest.raises(ValueError):
        F._object(value)


@pytest.mark.parametrize('field', ['source_json', 'runtime_json', 'source_files_json', 'runtime_files_json'])
def test_mutable_or_noncanonical_context_maps_rejected(fabricated, field):
    with pytest.raises(ValueError):
        replace(fabricated['request'].executor, **{field: json.loads(getattr(fabricated['request'].executor, field))})


def test_request_path_and_digest_cannot_be_foreign(fabricated):
    with pytest.raises(ValueError):
        F.ProvenanceRestoreFactory(fabricated['request'], fabricated['publication_path'],
            fabricated['request_sha'], fabricated['locked'])
    with pytest.raises(ValueError):
        F.ProvenanceRestoreFactory(fabricated['request'], fabricated['request_path'],
            'f' * 64, fabricated['locked'])


@pytest.mark.parametrize('field,member', [
    ('weights_format', 'sparse_frozen_init_v2'), ('evidence_format', 'factored_json_v1'),
    ('purpose', 'foreign_snapshot'), ('scientific_evaluation', True),
    ('scope', 'scientific'), ('protocol_config_sha256', 'f' * 64),
    ('model_class', 'foreign.Model'), ('weights_file', '../foreign.safetensors'),
    ('evidence_file', 'evidence/foreign.json'), ('model_recipe', {'method': 'foreign'}),
    ('source', {'git_commit': 'f' * 40, 'git_dirty': True, 'source_sha256': 'f' * 64}),
    ('omitted_tensor_names', ['head.bias'])])
def test_self_consistent_manifest_bytes_do_not_bypass_semantic_contract(fabricated, field, member):
    payload = dict(fabricated['manifest']['payload'])
    payload[field] = member
    changed = rebind_manifest(fabricated, payload)
    with pytest.raises(ValueError):
        factory(fabricated, changed).authenticate()


def test_actual_foreign_locked_case_refused(fabricated):
    recorder = fabricated['session']._recorder
    other = CasePlan(**dict(PLAN, model_seed=23))
    with recorder.case_session(other) as session:
        given = F.ProvenanceRestoreFactory(fabricated['request'], fabricated['request_path'],
            fabricated['request_sha'], session._require_active)
        with pytest.raises(ValueError, match='another case'):
            given.authenticate()


def test_stale_current_context_refused_even_with_self_consistent_request_and_pins(fabricated):
    source = F._source(fabricated['request'].executor.source_json)
    source['git_commit'] = 'f' * 40
    executor = replace(fabricated['request'].executor, source_json=F.canonical(source))
    pins = json.loads(fabricated['pins_path'].read_bytes())
    pins['factory_executor'] = asdict(executor)
    pins_sha = write(fabricated['pins_path'], pins)
    request = replace(fabricated['request'], executor=executor, pins_sha256=pins_sha)
    write(fabricated['request_path'], request.payload())
    with pytest.raises(ValueError, match='actual current Git'):
        factory(fabricated, request).authenticate()


def test_stale_runtime_refused_even_with_self_consistent_request_and_pins(fabricated):
    runtime = F._json_field(fabricated['request'].executor.runtime_json)
    runtime['python_full'] += ' stale'
    executor = replace(fabricated['request'].executor, runtime_json=F.canonical(runtime))
    pins = json.loads(fabricated['pins_path'].read_bytes())
    pins['factory_executor'] = asdict(executor)
    pins_sha = write(fabricated['pins_path'], pins)
    request = replace(fabricated['request'], executor=executor, pins_sha256=pins_sha)
    write(fabricated['request_path'], request.payload())
    with pytest.raises(ValueError, match='interpreter/dependency'):
        factory(fabricated, request).authenticate()


def test_consumed_request_cannot_restart_in_a_new_factory(fabricated):
    first = factory(fabricated)
    first.begin_restoration()
    marker = fabricated['request_path'].parent / 'restore-attempt.json'
    before = marker.read_bytes()
    with pytest.raises(ValueError, match='once-only'):
        first.begin_restoration()
    with pytest.raises(FileExistsError):
        factory(fabricated).begin_restoration()
    assert marker.read_bytes() == before


def test_failed_case_cannot_reuse_its_claim_and_request(fabricated):
    fabricated['session'].record_failure(attempt=1, reason={'error': 'preserved engineering failure'})
    with pytest.raises(ValueError, match='failed or terminal case'):
        factory(fabricated).authenticate()


def test_consumption_marker_tampering_prevents_further_authentication(fabricated):
    given = factory(fabricated)
    given.begin_restoration()
    marker = fabricated['request_path'].parent / 'restore-attempt.json'
    marker.write_bytes(marker.read_bytes() + b'changed')
    with pytest.raises(ValueError):
        given.authenticate()
