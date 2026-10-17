"""Metadata boundary tests; actual numerical work belongs to the one guarded route."""
from __future__ import annotations

import copy
import sys
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from core.config import config_digest, load_toml
from docs.phase2.cho51_linear_target_route_v1 import target_route as T
from evaluation.phase2_profile_binding import CHO_CHANNELS, CHO_CLASSES, ChoProfileAssets60Hz, ChoProfileBinding60Hz
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import envelope
from evaluation.phase2_runner import CasePlan


@pytest.fixture
def context():
    root = Path(__file__).resolve().parents[3]
    protocol = load_toml(root / 'configs/phase2/protocol.toml')
    catalogs = tuple(TrialCatalog('cho2017', subject, T.TRIAL_IDS, CHO_CLASSES * 21,
                                 CHO_CLASSES, f'{i:064x}', 'a' * 64)
                     for i, subject in enumerate(T.SUBJECTS, 1))
    selection = source_selection(catalogs, target='subject_02')
    episode = nested_episode(catalogs[1], shots=(1, 5, 10, 20), protocol_sha256=config_digest(protocol))
    return dict(plan=T.PLAN, protocol_config=protocol, catalogs=catalogs,
        selection_record=envelope('source_selection', asdict(selection)),
        episode_record=envelope('episode_manifest', episode.payload()),
        assets={subject: ChoProfileAssets60Hz('b' * 64, 'c' * 64, 'd' * 64)
                for subject in T.SUBJECTS})


def _contract(context):
    return T.prepare_target_contract(**context)


def _binding(contract, context):
    target, asset = context['catalogs'][1], context['assets']['subject_02']
    return ChoProfileBinding60Hz(
        'cho2017', 'subject_02', 5, CHO_CLASSES, CHO_CHANNELS,
        contract['protocol_sha256'], contract['episode_sha256'], target.artifact_sha256,
        asset.profile_b_artifact_sha256, asset.profile_b_manifest_sha256,
        target.preprocessing_sha256, 'e' * 64, 'f' * 64,
        tuple(contract['support_trial_ids']), tuple(contract['query_trial_ids']),
        tuple(contract['support_indices']), tuple(contract['query_indices']), 42, 0,
        variant_config_sha256=asset.variant_config_sha256,
        source_file='data/raw/moabb/cho2017/subject_02.mat', source_sha256='1' * 64)


def _check_binding(binding, contract, context):
    return T.validate_binding(binding, contract, context['catalogs'][1], context['assets']['subject_02'])


def _states():
    before = {**{f'backbone.layer.{i}': 'a' * 64 for i in range(221)},
              'head.weight': 'b' * 64, 'head.bias': 'c' * 64}
    after = {**before, 'head.weight': 'd' * 64}
    return before, after


def _transition(before, after, **options):
    arguments = dict(trainable_names=T.HEAD_NAMES, trainable_parameters=402,
                     gradients_finite=True, modules_eval=True)
    arguments.update(options)
    return T.validate_state_transition(before, after, **arguments)


def test_reconstructs_fixed_source_only_selection_and_episode(context):
    contract = _contract(context)
    assert contract['support_indices'] == list(range(10))
    assert contract['query_indices'] == [40, 41]
    assert contract['unused_pool_indices'] == list(range(10, 40))
    assert contract['support_labels'] == [0, 1] * 5
    assert contract['query_labels'] == [0, 1]
    assert len(contract['source_subjects']) == 51
    assert 'subject_02' not in contract['source_subjects']
    assert not set(contract['support_trial_ids']) & set(contract['query_trial_ids'])
    assert not set(contract['support_trial_ids']) & set(contract['unused_trial_ids'])


@pytest.mark.parametrize('field,value', [
    ('dataset', 'bci_iv_2a'), ('target_subject', 'subject_03'), ('method', 'labram_full'),
    ('shots_per_class', 1), ('model_seed', 12), ('repetition', 2),
])
def test_wrong_plan_refused_before_route(context, field, value):
    context['plan'] = replace(T.PLAN, **{field: value})
    with pytest.raises(ValueError, match='exact synthetic linear plan'):
        _contract(context)


@pytest.mark.parametrize('which', ['selection_record', 'episode_record'])
def test_self_consistent_foreign_envelope_is_refused(context, which):
    record = context[which]
    payload = copy.deepcopy(record['payload'])
    payload['foreign_identity'] = 'self-consistent but untrusted'
    context[which] = envelope(record['kind'], payload)
    with pytest.raises(ValueError, match='independently reconstructed'):
        _contract(context)


@pytest.mark.parametrize('role', ['support_indices', 'query_indices', 'unused_pool_indices'])
def test_rehashed_partition_tamper_refused(context, role):
    record = context['episode_record']
    payload = copy.deepcopy(record['payload'])
    row = next(row for row in payload['partitions'] if row['shots_per_class'] == 5)
    row[role] = list(reversed(row[role]))
    context['episode_record'] = envelope('episode_manifest', payload)
    with pytest.raises(ValueError, match='episode differs'):
        _contract(context)


@pytest.mark.parametrize('tamper', ['subject_order', 'trial_order', 'query_labels', 'unused_labels',
                                   'missing_subject', 'duplicate_subject'])
def test_catalog_order_and_label_leakage_tampering_refused(context, tamper):
    catalogs = list(context['catalogs'])
    if tamper == 'subject_order':
        catalogs[0], catalogs[1] = catalogs[1], catalogs[0]
    elif tamper == 'trial_order':
        catalogs[1] = replace(catalogs[1], trial_ids=tuple(reversed(T.TRIAL_IDS)))
    elif tamper in ('query_labels', 'unused_labels'):
        labels = list(catalogs[1].labels)
        index = 40 if tamper == 'query_labels' else 10
        labels[index] = CHO_CLASSES[1]
        catalogs[1] = replace(catalogs[1], labels=tuple(labels))
    elif tamper == 'missing_subject':
        catalogs.pop()
    else:
        catalogs[-1] = catalogs[0]
    context['catalogs'] = tuple(catalogs)
    with pytest.raises(ValueError, match='exact ordered synthetic'):
        _contract(context)


@pytest.mark.parametrize('tamper', ['missing', 'extra', 'mixed_variant'])
def test_asset_inventory_and_variant_refused(context, tamper):
    assets = context['assets']
    if tamper == 'missing':
        assets.pop('subject_52')
    elif tamper == 'extra':
        assets['subject_53'] = assets['subject_01']
    else:
        assets['subject_52'] = replace(assets['subject_52'], variant_config_sha256='e' * 64)
    with pytest.raises(ValueError):
        _contract(context)


def test_exact_60hz_binding_is_accepted(context):
    contract = _contract(context)
    _check_binding(_binding(contract, context), contract, context)


@pytest.mark.parametrize('field,value', [
    ('subject', 'subject_03'), ('shots_per_class', 10), ('sampling_rate_hz', 128),
    ('samples_per_trial', 512), ('patch_samples', 100), ('stored_unit_volts', 1.0),
    ('extra_input_scale', 10.0), ('target_transform_fit', 'query_fitted'),
    ('profile_a_artifact_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), ('profile_b_artifact_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
    ('profile_b_manifest_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), ('variant_config_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
    ('episode_sha256', '0000000000000000000000000000000000000000000000000000000000000000'), ('protocol_sha256', '0000000000000000000000000000000000000000000000000000000000000000'),
    ('profile_a_rejected_trials', 1), ('input_trials', 43),
    ('source_file', 'data/raw/moabb/cho2017/subject_03.mat'),
])
def test_binding_identity_hash_and_transform_tamper_refused(context, field, value):
    contract = _contract(context)
    binding = replace(_binding(contract, context), **{field: value})
    with pytest.raises(ValueError):
        _check_binding(binding, contract, context)


@pytest.mark.parametrize('field', ['support_trial_ids', 'query_trial_ids',
                                  'support_profile_b_rows', 'query_profile_b_rows'])
def test_binding_row_and_id_order_cannot_be_changed(context, field):
    contract = _contract(context)
    binding = _binding(contract, context)
    with pytest.raises(ValueError):
        _check_binding(replace(binding, **{field: tuple(reversed(getattr(binding, field)))}),
                       contract, context)


def test_support_cannot_include_a_query_or_unused_row(context):
    contract = _contract(context)
    binding = _binding(contract, context)
    for forbidden in (10, 40):
        rows = (forbidden, *binding.support_profile_b_rows[1:])
        with pytest.raises(ValueError):
            _check_binding(replace(binding, support_profile_b_rows=rows), contract, context)


def test_live_and_historical_git_remain_distinct():
    historical = dict(T.HISTORICAL_CONTEXT)
    current = {**historical, 'git_commit': '3' * 40}
    proof = T.validate_provenance(current, dict(current), historical)
    assert proof['current']['source_sha256'] == proof['historical']['source_sha256']
    assert proof['current']['git_commit'] != proof['historical']['git_commit']


@pytest.mark.parametrize('tamper', ['live_commit', 'live_fingerprint', 'live_dirty',
                                   'history_commit', 'history_fingerprint', 'history_dirty',
                                   'extra_field', 'missing_field', 'collapsed_git', 'invalid_revision'])
def test_provenance_substitution_cannot_be_accepted(tamper):
    historical = dict(T.HISTORICAL_CONTEXT)
    expected = {**historical, 'git_commit': '3' * 40}
    current = dict(expected)
    if tamper == 'live_commit':
        current['git_commit'] = '4' * 40
    elif tamper == 'live_fingerprint':
        current['source_sha256'] = 'f' * 64
    elif tamper == 'live_dirty':
        current['git_dirty'] = False
    elif tamper == 'history_commit':
        historical['git_commit'] = '4' * 40
    elif tamper == 'history_fingerprint':
        historical['source_sha256'] = 'f' * 64
    elif tamper == 'history_dirty':
        historical['git_dirty'] = False
    elif tamper == 'extra_field':
        current['untrusted'] = True
    elif tamper == 'missing_field':
        current.pop('git_dirty')
    elif tamper == 'collapsed_git':
        current = expected = dict(historical)
    else:
        current['git_commit'] = 'unknown'
    with pytest.raises(ValueError):
        T.validate_provenance(current, expected, historical)


def test_exact_head_change_is_accepted():
    before, after = _states()
    assert _transition(before, after) == ['head.weight']


@pytest.mark.parametrize('name', ['backbone.layer.0', 'backbone.layer.220'])
def test_frozen_backbone_or_buffer_drift_is_refused(name):
    before, after = _states()
    after[name] = 'e' * 64
    with pytest.raises(ValueError, match='backbone or buffer'):
        _transition(before, after)


@pytest.mark.parametrize('tamper', ['missing_tensor', 'added_tensor', 'nonfinite_digest',
                                   'wrong_names', 'wrong_count', 'nonfinite_gradients',
                                   'training_mode', 'unchanged_head'])
def test_incomplete_state_or_wrong_update_policy_refused(tamper):
    before, after = _states()
    kwargs = {}
    if tamper == 'missing_tensor':
        after.pop('backbone.layer.0')
    elif tamper == 'added_tensor':
        after['extra.buffer'] = 'e' * 64
    elif tamper == 'nonfinite_digest':
        after['head.weight'] = 'invalid'
    elif tamper == 'wrong_names':
        kwargs['trainable_names'] = ('head.weight', 'backbone.layer.0')
    elif tamper == 'wrong_count':
        kwargs['trainable_parameters'] = 403
    elif tamper == 'nonfinite_gradients':
        kwargs['gradients_finite'] = False
    elif tamper == 'training_mode':
        kwargs['modules_eval'] = False
    else:
        after = dict(before)
    with pytest.raises(ValueError):
        _transition(before, after, **kwargs)


def test_profiler_is_restored_when_target_work_fails():
    observer = T._CanonicalObserver(None, {}, T.SELECTED_STATE_SHA256)
    previous = sys.getprofile()
    with pytest.raises(RuntimeError, match='deliberate failure'):
        with observer:
            raise RuntimeError('deliberate failure')
    assert sys.getprofile() is previous


def test_profiler_chains_existing_observer_and_restores_it():
    calls = []
    previous = sys.getprofile()
    def outer(frame, event, arg):
        if frame.f_code is marker.__code__ and event == 'call':
            calls.append(event)
    def marker():
        return 'metadata-only'
    try:
        sys.setprofile(outer)
        with T._CanonicalObserver(None, {}, T.SELECTED_STATE_SHA256):
            assert marker() == 'metadata-only'
        assert sys.getprofile() is outer
        assert calls == ['call']
    finally:
        sys.setprofile(previous)
