"""Actual input bytes plus explicitly fabricated recorder and selection records.

No model, real prediction, fitted selector, selected publication or original
attempt is executed. The actual input loader is never replaced by this fixture.
"""
import hashlib
import importlib.util
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from __main__ import ROOT, OUT, FIXTURE, pins as execution_pins
from core.config import canonical_config_json, config_digest
from core.provenance import SourceProvenance
from docs.phase2.cho51_input_collection_v1 import collection as M
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import prepare_cho51_worker_route
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell
from evaluation.phase2_cho_case_inputs import ChoCaseInputPins
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import CellIdentity, envelope
from evaluation.phase2_runner import CaseRecorder
from evaluation.phase2_subject_aggregation import ExpectedCell


def digest_label(label):
    return hashlib.sha256(label.encode()).hexdigest()


def write_record(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (canonical_config_json(record) + '\n').encode()
    path.write_bytes(raw)
    return raw


@pytest.fixture(scope='module')
def actual_inputs():
    input_pins = ChoCaseInputPins(**execution_pins['input_route_pins'])
    print('Reconstructing actual52 input route; no loader replacement.', flush=True)
    route = prepare_cho51_worker_route(ROOT, input_pins=input_pins)
    config = json.loads(route.protocol_config_json)
    protocol_sha = config_digest(config)
    methods = dict(route.contract.method_config_sha256)
    # These digests deliberately describe a fabricated fixture, not a model.
    source = SourceProvenance('f' * 40, digest_label('fabricated-fixture-not-model-source'), False)
    bindings = json.loads((ROOT / execution_pins['retained_bindings']).read_bytes())
    binding_by_subject = {row['subject']: row for row in bindings}
    catalogs = {c.subject: c for c in route.catalogs}
    selections = {s: source_selection(route.catalogs, target=s) for s in catalogs}
    episodes = {s: nested_episode(c, shots=tuple(config['protocol']['shots_per_class']),
                                   protocol_sha256=protocol_sha) for s, c in catalogs.items()}
    templates = json.loads((ROOT / execution_pins['candidate_templates']).read_bytes())
    templates = {row['method']: row for row in templates['methods']}
    assert {key: config_digest(value) for key, value in templates.items()} == methods
    pending = tuple(PinnedCaseCell(
        plan, ExpectedCell(*plan.identity_key), CellIdentity(
            *plan.identity_key, None, None, protocol_sha,
            json.loads(route._full_route.episode_records_json[plan.target_subject])['sha256'],
            json.loads(route._full_route.selection_records_json[plan.target_subject])['sha256'],
            methods[plan.method], catalogs[plan.target_subject].preprocessing_sha256,
            digest_label('fabricated-checkpoint-' + plan.case_id), source.source_sha256,
            digest_label('fabricated-environment-not-model-runtime'), source.git_commit, False,
        ), 1, digest_label('unpublished-cell'), digest_label('unpublished-success'),
        digest_label('unpublished-evidence'),
    ) for plan in route.plans)
    # Reuse only the qualified fabricated publisher. Its output-root dependency
    # is confined to the dedicated synthetic recorder, not a production store.
    path = ROOT / 'docs/phase2/cho51_selection_files_v1/test_selection_files_003.py'
    spec = importlib.util.spec_from_file_location('_real_input_fabricated_publisher', path)
    publisher = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = publisher
    spec.loader.exec_module(publisher)
    publisher.CaseRecorder = lambda root, output_root=None: CaseRecorder(ROOT, output_root=FIXTURE)
    context = SimpleNamespace(root=ROOT, route=route, templates=templates, methods=methods,
                              selections=selections, source=source, protocol_sha=protocol_sha)
    print('Publishing1020 explicitly fabricated selection/cell records.', flush=True)
    published = publisher._publish(context, pending)
    recorder = published.recorder
    base_sha = execution_pins['files']['configs/base.toml']
    final = []
    for pin in published.pins:
        plan, identity = pin.plan, pin.identity
        subject = plan.target_subject
        catalog, episode, selection = catalogs[subject], episodes[subject], selections[subject]
        partition = episode.partition(5)
        support_ids = tuple(catalog.trial_ids[i] for i in partition.support_indices)
        query_ids = tuple(catalog.trial_ids[i] for i in partition.query_indices)
        counts = [sum(catalog.labels[i] == label for i in partition.query_indices)
                  for label in catalog.classes]
        attestation = {'schema': 'cho2017-target-input-v1', 'method': plan.method,
                       'subject': subject, 'episode_record_sha256': identity.episode_sha256}
        if plan.method == 'eegnet':
            attestation.update(profile='cho_profile_a', anchor={
                'method': 'eegnet', 'subject': subject, 'role': 'outer_target',
                'episode_sha256': episode.sha256, 'selection_sha256': selection.sha256,
                'support_trial_ids': support_ids, 'query_trial_ids': query_ids,
                'source_subjects': selection.source_subjects,
                'input_identities': {subject: {
                    'catalog_sha256': catalog.sha256, 'artifact_sha256': catalog.artifact_sha256,
                    'manifest_sha256': catalog.artifact_sha256, 'base_config_sha256': base_sha,
                }},
            })
        else:
            retained = binding_by_subject[subject]
            assert config_digest(retained['binding']) == retained['binding_sha256']
            attestation.update(profile='cho_profile_b_60hz_v1',
                               binding_sha256=retained['binding_sha256'], binding=retained['binding'])
        path = recorder.output_root / 'cells' / f'{identity.sha256}.json'
        payload = json.loads(path.read_bytes())['payload']
        payload['metrics'].update(
            role='outer_target', confusion_matrix=[[counts[0], 0], [0, counts[1]]],
            balanced_accuracy=[1, 1], query_count=sum(counts), target_input_attestation=attestation,
            fixture_evidence_class='fabricated_predictions_on_actual_input_metadata',
        )
        cell = envelope('evaluation_cell', payload)
        write_record(path, cell)
        write_record(recorder.output_root / 'claims' / f'{plan.case_id}.attempt1.claim.json',
                     envelope('engineering_smoke', {
                         'purpose': 'pilot_case_claim', 'case': asdict(plan),
                         'worker': 'fabricated_only_no_model_execution', 'attempt': 1,
                         'environment_sha256': identity.environment_sha256,
                         'source': asdict(source), 'engineering_only': True,
                     }))
        write_record(recorder.output_root / 'publication_intents' / f'{plan.case_id}.intent.json',
                     envelope('engineering_smoke', {
                         'purpose': 'pilot_case_publication_intent', 'case': asdict(plan),
                         'attempt': 1, 'identity': asdict(identity), 'cell': cell,
                     }))
        success = write_record(recorder.output_root / 'successes' / f'{plan.case_id}.success.json',
                               envelope('engineering_smoke', {
                                   'purpose': 'pilot_case_success', 'case': asdict(plan),
                                   'attempt': 1, 'cell_sha256': cell['sha256'],
                               }))
        final.append(replace(pin, cell_sha256=cell['sha256'],
                             success_file_sha256=hashlib.sha256(success).hexdigest()))
    for name in ('attempts', 'engineering_intents', 'engineering_successes'):
        (FIXTURE / name).mkdir(exist_ok=True)
    write_record(FIXTURE / 'FIXTURE_SCOPE.json', {
        'schema': 'fabricated_records_on_actual_input_metadata_v1',
        'scientific_result': False, 'prediction_or_fit_performed': False,
        'actual_input_loader_replaced': False, 'actual_model_source_used': False,
        'retained_B_bindings_referenced_not_redecoded': True,
        'original_attempt_used': False,
    })
    print('Fabricated ledger complete; checking composed unmocked input path.', flush=True)
    return SimpleNamespace(route=route, recorder=recorder, pins=tuple(final), source=source,
                           input_pins=input_pins, methods=methods, bindings=bindings,
                           base_sha=base_sha, catalogs=catalogs, episodes=episodes)


def invoke(case, **changes):
    values = dict(
        project_root=ROOT, route=case.route, recorder=case.recorder, pins=case.pins,
        case_input_pins=case.input_pins, base_config_sha256=case.base_sha,
        method_config_sha256=case.methods, expected_source=case.source,
        selection_ceiling_config_sha256=execution_pins['files']['configs/phase2/selection_ceiling.toml'],
    )
    values.update(changes)
    return M.collect_cho51_input_selection(**values)


def test_actual_roster_and_retained_binding_declarations(actual_inputs):
    case = actual_inputs
    assert len(case.route.catalogs) == len(case.route.labram_assets) == 52
    assert len(case.route.plans) == len(case.pins) == 1020
    assert {p.plan.target_subject for p in case.pins} == {f'subject_{i:02d}' for i in range(2, 53)}
    assert len(case.bindings) == 52
    assert all(config_digest(row['binding']) == row['binding_sha256'] for row in case.bindings)
    assert sum(len(case.episodes[s].partition(5).query_indices)
               for s in case.catalogs if s != 'subject_01') == 8269


def test_unmocked_actual_input_and_fabricated_record_composition(actual_inputs):
    result = invoke(actual_inputs)
    assert len(result.rows) == len(result.selection_claims) == 1020
    assert result.scientific_result_admitted is False
    assert result.selected_publications_verified is False
    assert result.selected_tensors_verified is False
    assert result.full_selector_evidence_verified is False


def test_changed_independent_real_input_pin_refused(actual_inputs):
    changed = replace(actual_inputs.input_pins, protocol_config_sha256='0' * 64)
    with pytest.raises(ValueError):
        invoke(actual_inputs, case_input_pins=changed)


def test_excluded_target_pin_cannot_enter_composition(actual_inputs):
    first = actual_inputs.pins[0]
    plan = replace(first.plan, target_subject='subject_01')
    changed = replace(first, plan=plan, key=ExpectedCell(*plan.identity_key),
                      identity=replace(first.identity, target_subject='subject_01'))
    with pytest.raises(ValueError):
        invoke(actual_inputs, pins=(changed,) + actual_inputs.pins[1:])
