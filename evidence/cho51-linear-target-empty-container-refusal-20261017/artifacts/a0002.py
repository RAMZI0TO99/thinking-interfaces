"""One synthetic linear target episode through the unchanged canonical adapter.

This candidate publishes an engineering witness only. Its caller authenticates
historical proof bytes and supplies an explicitly admitted fresh restore. No
scientific executor, source fitting, claim or evaluation-cell writer is used.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import math
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict
from pathlib import Path

import torch

from adaptation.labram_manifest import (
    LaBraMTuningManifestRunner, LaBraMTuningPrediction, LaBraMTuningSettings,
)
from adaptation.labram_tuning import adapt_labram_tuning_support
from core.config import config_digest, config_snapshot
from core.provenance import capture_source
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_pilot import LaBraMTunedAdapter, _metrics
from evaluation.phase2_profile_binding import (
    CHO_CHANNELS, CHO_CLASSES, ChoProfileAssets60Hz, ChoProfileBinding60Hz,
    load_cho_profile_b_episode,
)
from evaluation.phase2_protocol import (
    TrialCatalog, nested_episode, require_digest, source_selection,
)
from evaluation.phase2_records import verify_envelope
from evaluation.phase2_runner import CasePlan
from scripts.audit_phase2_protocol import validate_protocol

PLAN = CasePlan('cho2017', 'subject_02', 'labram_linear', 5, 11, 1)
HISTORICAL_CONTEXT = {
    'git_commit': '4491e2a68126d6b7293261f4954b88c11c29049d',
    'source_sha256': '9c2e6ad444c44309f9d4becda2909fba0d2fe315f047560f9adbce56397c9299',
    'git_dirty': True,
}
SELECTED_STATE_SHA256 = '8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'
SETTINGS = LaBraMTuningSettings('linear', 1, 0.001, None, 8)
HEAD_NAMES = ('head.weight', 'head.bias')
SUBJECTS = tuple(f'subject_{i:02d}' for i in range(1, 53))
TRIAL_IDS = tuple(json.dumps(['synthetic_session', 'synthetic_run', i], separators=(',', ':'))
                  for i in range(42))


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def validate_provenance(current, expected_current, historical):
    """A shared five-TOML fingerprint never collapses the distinct Git contexts."""
    keys = {'git_commit', 'source_sha256', 'git_dirty'}
    for context in (current, expected_current, historical):
        _need(isinstance(context, Mapping) and set(context) == keys,
              'an exact three-field provenance mapping is required')
        require_digest(context['source_sha256'], 'source fingerprint')
        revision = context['git_commit']
        _need(type(revision) is str and len(revision) in (40, 64)
              and all(c in '0123456789abcdef' for c in revision)
              and type(context['git_dirty']) is bool, 'explicit real Git provenance required')
    _need(dict(historical) == HISTORICAL_CONTEXT, 'historical source provenance changed')
    _need(dict(current) == dict(expected_current), 'current source differs from external pins')
    _need(current['git_commit'] != historical['git_commit']
          and current['source_sha256'] == historical['source_sha256'],
          'new Git context and unchanged five-TOML source must be recorded separately')
    return {'current': dict(current), 'historical': dict(historical)}


def prepare_target_contract(*, plan, protocol_config, catalogs, selection_record, episode_record,
                            assets):
    """Reconstruct permissions before calling a restore callback or numerical route."""
    _need(type(plan) is CasePlan and plan == PLAN, 'only the exact synthetic linear plan is admitted')
    config = config_snapshot(protocol_config)
    _need(validate_protocol(config) == (1, 5, 10, 20), 'fixed nested shot levels required')
    _need(type(catalogs) is tuple and len(catalogs) == 52
          and all(type(c) is TrialCatalog for c in catalogs)
          and tuple(c.subject for c in catalogs) == SUBJECTS
          and all(c.dataset == 'cho2017'
                  and c.classes == CHO_CLASSES and c.trial_ids == TRIAL_IDS
                  and c.labels == CHO_CLASSES * 21 for c in catalogs),
          'exact ordered synthetic 52-subject, 42-trial catalogs required')
    selection = source_selection(catalogs, target=plan.target_subject)
    _need(verify_envelope(selection_record, kind='source_selection',
                          expected_payload=asdict(selection)),
          'selection differs from independently reconstructed source-only cohort')
    _need(len(selection.source_subjects) == 51 and plan.target_subject not in selection.source_subjects
          and len(selection.inner_folds) == 51
          and all(plan.target_subject not in fold.training_subjects
                  and fold.validation_subject != plan.target_subject for fold in selection.inner_folds),
          'outer target leaked into historical source selection')
    target = catalogs[1]
    episode = nested_episode(target, shots=(1, 5, 10, 20), protocol_sha256=config_digest(config))
    _need(verify_envelope(episode_record, kind='episode_manifest', expected_payload=episode.payload()),
          'episode differs from independently reconstructed fixed partition')
    partition = episode.partition(plan.shots_per_class)
    _need(tuple(map(len, (partition.support_indices, partition.query_indices,
                         partition.unused_pool_indices))) == (10, 2, 30),
          'exact ten support, two query and thirty unused trials required')
    _need(isinstance(assets, Mapping) and set(assets) == set(SUBJECTS)
          and all(type(asset) is ChoProfileAssets60Hz for asset in assets.values()),
          'complete exact Cho 60 Hz asset pins required')
    _need(len({asset.variant_config_sha256 for asset in assets.values()}) == 1,
          'the same fixed 60 Hz variant is required for every subject')
    return {
        'plan': asdict(plan), 'case_id': plan.case_id,
        'protocol_sha256': config_digest(config), 'selection_sha256': selection.sha256,
        'selection_record_sha256': selection_record['sha256'], 'episode_sha256': episode.sha256,
        'episode_record_sha256': episode_record['sha256'],
        'target_catalog_sha256': target.sha256, 'source_subjects': list(selection.source_subjects),
        'support_indices': list(partition.support_indices),
        'query_indices': list(partition.query_indices),
        'unused_pool_indices': list(partition.unused_pool_indices),
        'support_trial_ids': [target.trial_ids[i] for i in partition.support_indices],
        'query_trial_ids': [target.trial_ids[i] for i in partition.query_indices],
        'unused_trial_ids': [target.trial_ids[i] for i in partition.unused_pool_indices],
        'support_labels': [target.classes.index(target.labels[i]) for i in partition.support_indices],
        'query_labels': [target.classes.index(target.labels[i]) for i in partition.query_indices],
        'settings': asdict(SETTINGS), 'settings_sha256': SETTINGS.sha256,
    }


def validate_binding(binding, contract, target, asset):
    _need(type(binding) is ChoProfileBinding60Hz
          and binding.dataset == 'cho2017' and binding.subject == 'subject_02'
          and binding.classes == CHO_CLASSES and binding.channel_names == CHO_CHANNELS
          and binding.shots_per_class == 5 and binding.schema == 'cho-a-to-b-episode-60hz-v1'
          and binding.protocol_sha256 == contract['protocol_sha256']
          and binding.episode_sha256 == contract['episode_sha256']
          and binding.profile_a_artifact_sha256 == target.artifact_sha256
          and binding.profile_a_preprocessing_sha256 == target.preprocessing_sha256
          and binding.profile_b_artifact_sha256 == asset.profile_b_artifact_sha256
          and binding.profile_b_manifest_sha256 == asset.profile_b_manifest_sha256
          and binding.variant_config_sha256 == asset.variant_config_sha256
          and binding.support_trial_ids == tuple(contract['support_trial_ids'])
          and binding.query_trial_ids == tuple(contract['query_trial_ids'])
          and binding.input_trials == 42 and binding.profile_a_rejected_trials == 0
          and binding.sampling_rate_hz == 200 and binding.samples_per_trial == 800
          and binding.patch_samples == 200 and binding.stored_unit_volts == 0.0001
          and binding.extra_input_scale == 1.0 and binding.target_transform_fit == 'none'
          and binding.rejection_policy == 'profile_a_frozen_threshold_only'
          and binding.profile_a_sidecar_manifests == 'absent_cho_identity_is_the_audited_catalog_hash',
          'actual target binding differs from the pinned episode, assets or fixed transform policy')
    rows = binding.support_profile_b_rows + binding.query_profile_b_rows
    _need(len(binding.support_profile_b_rows) == 10 and len(binding.query_profile_b_rows) == 2
          and len(set(rows)) == 12 and all(type(row) is int and 0 <= row < 42 for row in rows),
          'bound support/query rows overlap, reorder or escape the actual profile')
    _need(binding.support_profile_b_rows == tuple(contract['support_indices'])
          and binding.query_profile_b_rows == tuple(contract['query_indices']),
          'synthetic Profile B row order differs from the frozen original trial order')
    require_digest(binding.source_sha256, 'raw source')
    _need(binding.source_file == 'data/raw/moabb/cho2017/subject_02.mat',
          'exact synthetic target raw-source identity required')


def validate_state_transition(before, after, *, trainable_names, trainable_parameters,
                              gradients_finite, modules_eval, changed_required=True):
    """Validate per-tensor witnesses; all unselected state, including buffers, is frozen."""
    _need(isinstance(before, Mapping) and isinstance(after, Mapping)
          and set(before) == set(after) and len(before) == 223,
          'complete unchanged 223-tensor state inventory required')
    for values in (before, after):
        for name, digest in values.items():
            _need(type(name) is str, 'state names must be plain strings')
            require_digest(digest, 'state tensor')
    _need(tuple(trainable_names) == HEAD_NAMES and type(trainable_parameters) is int
          and trainable_parameters == 402 and gradients_finite is True and modules_eval is True,
          'exact finite-gradient 402-parameter linear head and eval policy required')
    changed = tuple(name for name in before if before[name] != after[name])
    _need(not (set(changed) - set(HEAD_NAMES)), 'backbone or buffer state drifted')
    _need(not changed_required or bool(changed), 'support update did not change the head')
    return list(changed)


def _tensor_digest(tensor):
    owned = tensor.detach().cpu().contiguous()
    return hashlib.sha256(owned.numpy().tobytes()).hexdigest()


def _state(model):
    values = model.state_dict()
    _need(len(values) == 223 and sum(v.numel() for v in values.values()) == 5818138
          and all(v.device.type == 'cpu' and v.dtype == torch.float32
                  and torch.isfinite(v).all().item() for v in values.values()),
          'complete finite CPU float32 selected state required')
    return {name: _tensor_digest(value) for name, value in values.items()}


def _eval(model):
    return not any(module.training for module in model.modules())


def _disjoint_state(first, second):
    _need(first is not second, 'source and adapted model objects must be distinct')
    left = {value.untyped_storage().data_ptr() for value in first.state_dict().values()}
    right = {value.untyped_storage().data_ptr() for value in second.state_dict().values()}
    _need(not left & right, 'source and adapted state must have disjoint storage')


def _same_tensor(actual, expected, name):
    _need(type(actual) is torch.Tensor and actual.device.type == 'cpu'
          and actual.dtype == expected.dtype and actual.shape == expected.shape
          and torch.equal(actual.detach(), expected), f'{name} differs from the exact bound rows')


class _CanonicalObserver:
    """Read-only Python profiling witnesses; canonical implementation bytes stay intact.

    No source/global function is replaced. Profiling is restored in a finally
    block even if a bound input, gradient, mode or tensor witness is refused.
    This observer is for this single-threaded, one-episode admitted candidate.
    """
    def __init__(self, episode, contract, source_sha):
        self.episode, self.contract, self.source_sha = episode, contract, source_sha
        self.previous = None
        self.active = None
        self.source = self.model = self.prediction = None
        self.before = self.after = None
        self.calls = dict(adaptation=0, support_forward=0, backward=0, sgd_step=0,
                          query_forward=0, runner_prediction=0)
        self.gradients = {}
        self.gradient_norms = {}
        self.forward_shapes = []
        self.changed = []
        self._codes = {
            inspect.unwrap(adapt_labram_tuning_support).__code__: 'adaptation',
            inspect.unwrap(torch.optim.SGD.step).__code__: 'sgd_step',
            inspect.unwrap(torch.Tensor.backward).__code__: 'backward',
            inspect.unwrap(LaBraMClassifier.forward).__code__: 'forward',
            inspect.unwrap(LaBraMTuningManifestRunner._predict).__code__: 'runner_prediction',
        }

    def __enter__(self):
        self.previous = sys.getprofile()
        sys.setprofile(self._profile)
        return self

    def __exit__(self, *unused):
        sys.setprofile(self.previous)

    def _profile(self, frame, event, arg):
        if self.previous is not None:
            self.previous(frame, event, arg)
        kind = self._codes.get(frame.f_code)
        if kind is None or event not in ('call', 'return'):
            return
        if event == 'call':
            self._call(kind, frame)
        else:
            self._return(kind, frame, arg)

    def _call(self, kind, frame):
        local = frame.f_locals
        if kind == 'adaptation':
            self.calls[kind] += 1
            _need(self.calls[kind] == 1 and self.active is None,
                  'exactly one nonnested canonical support adaptation required')
            _need(local['method'] == 'linear' and local['partial_depth'] is None
                  and local['steps'] == 1 and local['learning_rate'] == 0.001,
                  'canonical support call differs from selected settings')
            _same_tensor(local['support_inputs'], torch.from_numpy(self.episode.support_signals),
                         'actual adaptation support signals')
            _same_tensor(local['support_targets'], torch.from_numpy(self.episode.support_labels),
                         'actual adaptation support labels')
            self.source = local['source_model']
            _need(state_digest(self.source) == self.source_sha and _eval(self.source),
                  'owned immutable source differs before support adaptation')
            self.active = frame
        elif kind == 'forward':
            model, inputs = local['self'], local['inputs']
            if self.active is not None:
                self.calls['support_forward'] += 1
                _need(self.calls['support_forward'] == 1
                      and model is self.active.f_locals.get('model')
                      and torch.is_grad_enabled() and not torch.is_inference_mode_enabled()
                      and _eval(model), 'one eval-mode gradient-enabled support forward required')
                _same_tensor(inputs, torch.from_numpy(self.episode.support_signals),
                             'actual classifier support inputs')
            else:
                self.calls['query_forward'] += 1
                _need(self.calls['query_forward'] == 1 and model is self.model
                      and not torch.is_grad_enabled() and torch.is_inference_mode_enabled()
                      and _eval(model), 'one frozen inference-mode query forward required')
                _same_tensor(inputs, torch.from_numpy(self.episode.query_signals),
                             'actual classifier query inputs')
            self.forward_shapes.append(list(inputs.shape))
        elif kind == 'backward':
            self.calls[kind] += 1
            _need(self.active is not None and self.calls[kind] == 1
                  and local['self'].numel() == 1 and torch.isfinite(local['self']).all().item(),
                  'exactly one finite canonical support backward required')
        elif kind == 'sgd_step':
            self.calls[kind] += 1
            _need(self.active is not None and self.calls[kind] == 1,
                  'exactly one support SGD step required')
            self.model = self.active.f_locals['model']
            _disjoint_state(self.source, self.model)
            optimizer = local['self']
            selected = [(name, p) for name, p in self.model.named_parameters() if p.requires_grad]
            _need(type(optimizer) is torch.optim.SGD and len(optimizer.param_groups) == 1,
                  'fresh plain single-group SGD required')
            group = optimizer.param_groups[0]
            _need(tuple(name for name, _ in selected) == HEAD_NAMES
                  and sum(p.numel() for _, p in selected) == 402
                  and tuple(id(p) for p in group['params']) == tuple(id(p) for _, p in selected)
                  and group['lr'] == 0.001 and group['momentum'] == 0
                  and group['weight_decay'] == 0 and group['dampening'] == 0
                  and group['nesterov'] is False and group['maximize'] is False,
                  'SGD must update only the exact selected 402 head parameters')
            _need(all(p.grad is not None and torch.isfinite(p.grad).all().item()
                      for _, p in selected)
                  and all(p.grad is None for p in self.model.parameters() if not p.requires_grad)
                  and all(p.grad is None for p in self.source.parameters()),
                  'selected finite gradients and absent frozen/source gradients required')
            self.gradients = {name: _tensor_digest(p.grad) for name, p in selected}
            self.gradient_norms = {name: float(p.grad.norm().item()) for name, p in selected}
            self.before = _state(self.model)
            _need(state_digest(self.model) == self.source_sha and _eval(self.model),
                  'the adapted clone must begin at the exact source in eval mode')
        elif kind == 'runner_prediction':
            self.calls[kind] += 1
            _need(self.calls[kind] == 1 and local['subject'] == 'subject_02'
                  and local['role'] == 'outer_target' and local['shots'] == 5
                  and local['settings'] == SETTINGS, 'exact canonical target runner required')

    def _return(self, kind, frame, result):
        if kind == 'sgd_step':
            self.after = _state(self.model)
            self.changed = validate_state_transition(
                self.before, self.after, trainable_names=HEAD_NAMES, trainable_parameters=402,
                gradients_finite=True, modules_eval=_eval(self.model))
        elif kind == 'adaptation':
            _need(frame is self.active and result is not None and result.model is self.model
                  and result.mask.trainable_names == HEAD_NAMES
                  and result.mask.trainable_parameters == 402 and result.mask.method == 'linear'
                  and result.mask.depth == 0 and result.mask.selected_blocks == ()
                  and len(result.losses) == 1 and math.isfinite(result.losses[0])
                  and all(p.grad is None for p in result.model.parameters())
                  and state_digest(self.source) == self.source_sha,
                  'canonical support completion or immutable source witness differs')
            self.losses = list(result.losses)
            self.mask = asdict(result.mask)
            self.active = None
        elif kind == 'runner_prediction':
            _need(type(result) is LaBraMTuningPrediction and result.role == 'outer_target'
                  and result.source_state_sha256 == self.source_sha and result.settings == SETTINGS
                  and result.selection_sha256 == self.contract['selection_sha256']
                  and result.binding == self.episode.binding
                  and result.engineering_only is True
                  and result.source_training_history_verified is False,
                  'actual canonical prediction differs from the independently bound target')
            self.prediction = result

    def finish(self):
        _need(self.calls == dict(adaptation=1, support_forward=1, backward=1, sgd_step=1,
                                 query_forward=1, runner_prediction=1)
              and self.prediction is not None and self.active is None,
              'canonical one-update/one-query call witnesses are incomplete')
        _need(self.after == _state(self.model) and state_digest(self.source) == self.source_sha,
              'query inference changed adapted or immutable source state')
        _need(not self.prediction.logits.requires_grad
              and self.prediction.logits.shape == (2, 2)
              and torch.isfinite(self.prediction.logits).all().item(),
              'finite detached two-row/two-class query logits required')
        return {
            'calls': dict(self.calls), 'support_losses': self.losses, 'mask': self.mask,
            'gradient_sha256': self.gradients, 'gradient_norms': self.gradient_norms,
            'finite_gradients': True, 'changed_state_names': self.changed,
            'before_state_tensors': self.before, 'after_state_tensors': self.after,
            'adapted_state_sha256': self.prediction.adapted_state_sha256,
            'classifier_input_shapes': self.forward_shapes,
            'query_inference_mode': True, 'all_modules_eval': True,
            'source_unchanged': True, 'backbone_and_buffers_unchanged': True,
            'owned_source_and_adapted_storage_disjoint': True,
            'query_labels_used_for_adaptation': False, 'unused_pool_used_for_adaptation': False,
        }


def run_target_route(*, fixture_root: Path, plan, protocol_config, catalogs, selection_record,
                     episode_record, assets, current_context, expected_current_context,
                     historical_context, expected_source_state_sha256: str,
                     restore_adapter: Callable[[], LaBraMTunedAdapter]):
    """Execute once after caller's exact source/runtime/native admission.

    ``restore_adapter`` authenticates prior publication/recorder proofs and
    performs one newly counted bounded restore. Reusing old metadata does not
    requalify the unchanged single-root store, restore factory or scientific
    executor under the new Git context. This function writes nothing.
    """
    _need(isinstance(fixture_root, Path) and fixture_root.is_dir()
          and fixture_root.resolve(strict=True) == fixture_root,
          'absolute direct preserved synthetic fixture required')
    provenance = validate_provenance(current_context, expected_current_context, historical_context)
    _need(asdict(capture_source(fixture_root)) == dict(current_context),
          'live current fixture source differs before target work')
    _need(expected_source_state_sha256 == SELECTED_STATE_SHA256,
          'exact accepted selected source state required')
    contract = prepare_target_contract(plan=plan, protocol_config=protocol_config,
        catalogs=catalogs, selection_record=selection_record, episode_record=episode_record, assets=assets)
    target, asset = catalogs[1], assets['subject_02']
    episode = load_cho_profile_b_episode(fixture_root, protocol_config, target, episode_record,
                                       shots_per_class=5, **asdict(asset))
    validate_binding(episode.binding, contract, target, asset)
    _need(episode.support_signals.shape == (10, 64, 800)
          and episode.query_signals.shape == (2, 64, 800)
          and episode.support_labels.tolist() == contract['support_labels']
          and episode.query_labels.tolist() == contract['query_labels'],
          'bound signal/label rows differ from reconstructed partition')
    _need(callable(restore_adapter), 'explicit newly admitted restore callback required')
    adapter = restore_adapter()
    _need(type(adapter) is LaBraMTunedAdapter and adapter.method == 'labram_linear'
          and adapter._support == SETTINGS and type(adapter._model) is LaBraMClassifier
          and state_digest(adapter._model) == expected_source_state_sha256
          and _eval(adapter._model), 'actual canonical adapter with exact restored state required')
    source_before = _state(adapter._model)
    observer = _CanonicalObserver(episode, contract, expected_source_state_sha256)
    with observer:
        outcome = adapter.predict_target(fixture_root, protocol_config, catalogs, selection_record,
            assets, episode_record, outer_target=plan.target_subject, shots_per_class=5)
    witnesses = observer.finish()
    _disjoint_state(adapter._model, observer.source)
    _disjoint_state(adapter._model, observer.model)
    _need(_state(adapter._model) == source_before
          and state_digest(adapter._model) == expected_source_state_sha256
          and all(p.grad is None for p in adapter._model.parameters()),
          'caller-owned selected source changed during target work')
    _need(outcome.episode_sha256 == contract['episode_record_sha256']
          and outcome.checkpoint_sha256 == expected_source_state_sha256
          and outcome.support_trial_ids == tuple(contract['support_trial_ids'])
          and outcome.query_trial_ids == tuple(contract['query_trial_ids'])
          and outcome.cho_profile_binding == episode.binding
          and outcome.targets.tolist() == contract['query_labels']
          and torch.equal(outcome.logits, observer.prediction.logits),
          'actual adapter output differs from the runner and immutable episode')
    _need(asdict(capture_source(fixture_root)) == dict(current_context),
          'live current fixture source changed during target work')
    confusion, rational, count = _metrics(outcome)
    return {
        'schema': 'cho51-linear-target-route-engineering-v1', 'accepted': True,
        'engineering_only': True, 'scientific_admission': False, 'measured_cells': 0,
        'record_cell_calls': 0, 'original_case_attempts_remaining': 0,
        'source_updates': 0, 'support_updates': 1, 'gradient_updates': 1,
        'current_restore_callback_calls': 1, 'target_inference_calls': 1,
        'historical_gradient_updates': 5253, 'historical_source_updates': 5151,
        'historical_support_updates': 102, 'historical_fold_count': 102,
        'historical_final_source_subjects': 51,
        'historical_source_and_recorder_proofs_reused': True,
        'new_complete_evidence_verification': False,
        'unchanged_single_root_factory_verified': False,
        'contract': contract, 'provenance': provenance,
        'profile_binding': asdict(episode.binding), 'profile_binding_sha256': episode.binding.sha256,
        'source_state_sha256': expected_source_state_sha256,
        'source_state_tensors': source_before, 'witnesses': witnesses,
        'caller_source_runner_source_and_adapted_storage_disjoint': True,
        'query_logits': outcome.logits.tolist(), 'query_targets': outcome.targets.tolist(),
        'confusion_matrix': confusion, 'balanced_accuracy': [rational.numerator, rational.denominator],
        'query_count': count, 'stage_timings_s': list(outcome.stage_timings_s),
    }
