"""Actual complete synthetic EEGNet selection and detached publication checking.

All numerical imports and calls belong to the caller's freshly admitted native
child. This module does not launch processes, use a recorder, execute a target
case, or admit scientific work. The source and detached processes have separate
write scopes and independently pinned results.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import stat
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SUBJECTS = tuple(f'subject_{number:02d}' for number in range(1, 53))
OUTER_TARGET = 'subject_02'
SOURCE_SUBJECTS = tuple(subject for subject in SUBJECTS if subject != OUTER_TARGET)
TOTAL_UPDATES = 5253
SOURCE_UPDATES = 5151
SUPPORT_UPDATES = 102
MAXIMUM_JSON_BYTES = 8 * 1024**2
MAXIMUM_WEIGHTS_BYTES = 1024**2


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _canonical(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(',', ':'))


def _request_sha256(request):
    return hashlib.sha256((_canonical(request) + '\n').encode('utf-8')).hexdigest()


def _path_identity(path):
    status = path.stat(follow_symlinks=False)
    _need(path.is_absolute() and path.resolve(strict=True) == path
          and stat.S_ISREG(status.st_mode) and status.st_nlink == 1,
          'ordinary direct single-link file required')
    return status.st_dev, status.st_ino, status.st_size, status.st_mtime_ns, status.st_ctime_ns


def _read(path, maximum_bytes=MAXIMUM_JSON_BYTES):
    path = Path(path)
    before = _path_identity(path)
    _need(0 < before[2] <= maximum_bytes, 'file exceeds the independently fixed byte bound')
    with path.open('rb') as stream:
        opened_info = os.fstat(stream.fileno())
        opened = (opened_info.st_dev, opened_info.st_ino, opened_info.st_size,
                  opened_info.st_mtime_ns, opened_info.st_ctime_ns)
        _need(opened[:4] == before[:4] and stat.S_ISREG(opened_info.st_mode)
              and opened_info.st_nlink == 1, 'opened file identity differs')
        raw = stream.read(maximum_bytes + 1)
        finished_info = os.fstat(stream.fileno())
        finished = (finished_info.st_dev, finished_info.st_ino, finished_info.st_size,
                    finished_info.st_mtime_ns, finished_info.st_ctime_ns)
    _need(opened == finished and _path_identity(path) == before
          and len(raw) == before[2] and len(raw) <= maximum_bytes,
          'file changed during its bounded read')
    return raw, {'path': str(path), 'file_sha256': hashlib.sha256(raw).hexdigest(),
                 'size_bytes': len(raw), 'identity': list(before)}


def _object(path, maximum_bytes=MAXIMUM_JSON_BYTES):
    def pairs(rows):
        result = {}
        for key, value in rows:
            _need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result

    def invalid(value):
        raise ValueError('nonfinite JSON constant')

    raw, pin = _read(path, maximum_bytes)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    _need(type(value) is dict and raw == (_canonical(value) + '\n').encode('utf-8'),
          'canonical finite JSON object and newline required')
    return value, pin


def _write(path, value):
    with path.open('xb') as stream:
        stream.write((_canonical(value) + '\n').encode('utf-8'))
        stream.flush()
        os.fsync(stream.fileno())


def _plain(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _inputs(request):
    name = '_cho51_complete_eegnet_inputs_v1'
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name('inputs.py'))
        _need(spec is not None and spec.loader is not None, 'pinned adjacent input helper required')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module.load_existing_fixture(request)


def _method_config(request):
    from evaluation.phase2_runner import method_configuration

    config, pin = _object(Path(request['method_config_path']), 1024**2)
    _need(pin['file_sha256'] == request['method_config_file_sha256']
          and method_configuration(config) == request['method_config_sha256'],
          'independently pre-pinned adopted method configuration differs')
    expected = {
        'dataset': 'cho2017', 'method': 'eegnet', 'input_profile': 'cho_profile_a',
        'variant_config_sha256': None, 'source_seed_policy': 'none',
        'source_policy': 'all_non_target_subjects; inner_validation_also_excluded',
        'score': 'mean_subject_balanced_accuracy_exact_rational',
        'tie_break': 'first_in_declared_candidate_order', 'early_stopping': False,
        'candidates': [
            {'name': name,
             'source': {'steps_per_subject': 1, 'batch_size': 4,
                        'learning_rate': rate, 'input_scale': 1_000_000.0},
             'support': {'steps': 1, 'learning_rate': rate,
                         'input_scale': 1_000_000.0, 'query_batch_size': 8}}
            for name, rate in (('lr_1e-3', 0.001), ('lr_2e-3', 0.002))
        ],
    }
    _need(config == expected, 'exact adopted EEGNet candidate template required')
    return config, pin


def _context(request):
    import torch
    from core.provenance import capture_source
    from evaluation.phase2_runner import CasePlan, environment_digest

    _need(type(request) is dict and request.get('schema') == 'cho51_complete_eegnet_request_v1',
          'one independently pinned complete EEGNet request required')
    plan = CasePlan(**request['plan'])
    _need(asdict(plan) == {'dataset': 'cho2017', 'target_subject': OUTER_TARGET,
          'method': 'eegnet', 'shots_per_class': 5, 'model_seed': 11, 'repetition': 1}
          and plan.case_id == request['case_id'], 'one exact adopted engineering case required')
    _need(request.get('engineering_only') is True and request.get('scientific_admission') is False
          and request.get('original_case_attempts_remaining') == 0,
          'engineering-only request with zero original attempts required')
    _need(torch.get_num_threads() == torch.get_num_interop_threads() == 1
          and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'one-thread hidden-GPU execution required')
    _need(environment_digest() == request['environment_sha256'], 'request runtime context differs')
    config, config_pin = _method_config(request)
    fixture = _inputs(request)
    inputs = fixture.verify_inputs()
    _need(tuple(c.subject for c in fixture.catalogs) == SUBJECTS
          and len(fixture.input_paths) == 213 and len(fixture.protected_outer_paths) == 4,
          'all52 physical synthetic subjects and exact213-input inventory required')
    _need(inputs['sha256'] == request['fixture_identity_sha256']
          and fixture.identity_file_sha256 == request['fixture_identity_file_sha256']
          and str(fixture.identity_path) == request['fixture_identity_path'],
          'physical and logical input identity pins differ')
    source = capture_source(fixture.root)
    _need(source.source_sha256 == request['fixture_source_sha256']
          and type(source.git_dirty) is bool and source.git_commit != 'unversioned-workspace',
          'fixture source provenance differs from the fresh request')
    return plan, config, config_pin, fixture, inputs, source


def _rng_snapshot():
    import numpy as np
    import torch
    return torch.random.get_rng_state().clone(), np.random.get_state(), random.getstate()


def _rng_unchanged(before):
    import numpy as np
    import torch
    current = np.random.get_state()
    return (torch.equal(torch.random.get_rng_state(), before[0])
            and current[0] == before[1][0] and np.array_equal(current[1], before[1][1])
            and current[2:] == before[1][2:] and random.getstate() == before[2])


def _history_summary(record):
    """Independently count actual complete histories and recompute rational winner."""
    from evaluation.phase2_records import verify_envelope

    payload = record['payload']
    _need(verify_envelope(record, kind='engineering_smoke', expected_payload=payload)
          and payload['complete'] is True and payload['outer_target_predictions_performed'] is False,
          'actual complete public engineering envelope required')
    contract = payload['contract']
    candidate_names = ('lr_1e-3', 'lr_2e-3')
    _need(tuple(row['name'] for row in contract['candidates']) == candidate_names
          and contract['selection']['source_subjects'] == list(SOURCE_SUBJECTS)
          and contract['maximum_gradient_steps'] == TOTAL_UPDATES
          and len(payload['folds']) == 102,
          'complete two-candidate/51-source declaration and102 folds required')
    expected_pairs = [(candidate, subject) for candidate in candidate_names for subject in SOURCE_SUBJECTS]
    actual_pairs = [(fold['candidate'], fold['validation_subject']) for fold in payload['folds']]
    _need(actual_pairs == expected_pairs, 'actual complete fold order differs from the public roster')
    trace = []
    means = {}
    losses = []
    for candidate in candidate_names:
        scores = []
        for fold in (row for row in payload['folds'] if row['candidate'] == candidate):
            validation = fold['validation_subject']
            expected_sources = tuple(subject for subject in SOURCE_SUBJECTS if subject != validation)
            fit = fold['source_fit']
            _need(fit['training_subjects'] == list(expected_sources) and len(fit['steps']) == 50,
                  'every actual inner source fit must use its exact50 permitted subjects')
            prior = fit['initial_state_sha256']
            for number, (subject, step) in enumerate(zip(expected_sources, fit['steps'], strict=True), 1):
                _need(step['step'] == number and step['subject'] == subject
                      and step['subject_step'] == 1 and len(step['trial_ids']) == 4
                      and math.isfinite(step['loss']) and step['state_sha256_after'] != prior,
                      'real sequential four-trial source update history differs')
                trace.append(('source', candidate, validation, subject, number))
                losses.append(step['loss'])
                prior = step['state_sha256_after']
            _need(prior == fit['fitted_state_sha256']
                  and fit['initial_state_sha256'] != fit['fitted_state_sha256'],
                  'actual source fit must end at its recorded changed state')
            support_losses = fold['support_fit']['support_losses']
            _need(len(support_losses) == 1 and math.isfinite(support_losses[0])
                  and len(fold['support_trial_ids']) == 10 and len(fold['query_trial_ids']) == 2,
                  'one actual five-shot support update and two fixed inner queries required')
            trace.append(('inner_validation_support', candidate, validation, validation, 1))
            losses.extend(support_losses)
            confusion = fold['confusion_matrix']
            _need(len(confusion) == 2 and all(len(row) == 2 and sum(row) == 1
                  and all(type(value) is int and value >= 0 for value in row) for row in confusion),
                  'two inner validation query predictions required')
            score = (Fraction(confusion[0][0], sum(confusion[0]))
                     + Fraction(confusion[1][1], sum(confusion[1]))) / 2
            _need(fold['balanced_accuracy'] == [score.numerator, score.denominator],
                  'recorded fold score differs from actual confusion matrix')
            scores.append(score)
        means[candidate] = sum(scores, start=Fraction()) / 51
    winner = max(candidate_names, key=lambda candidate: means[candidate])
    _need(payload['selected_candidate'] == winner, 'exact-rational first-in-roster winner differs')
    for candidate, row in zip(candidate_names, payload['scores'], strict=True):
        _need(row == {'candidate': candidate,
              'mean_balanced_accuracy': [means[candidate].numerator, means[candidate].denominator]},
              'actual candidate mean differs from the102 observed folds')
    final_fit = payload['final_source_fit']
    _need(final_fit['candidate'] == winner and final_fit['validation_subject'] is None
          and final_fit['training_subjects'] == list(SOURCE_SUBJECTS)
          and len(final_fit['steps']) == 51,
          'fresh winning fit must include all51 non-target sources')
    prior = final_fit['initial_state_sha256']
    for number, (subject, step) in enumerate(zip(SOURCE_SUBJECTS, final_fit['steps'], strict=True), 1):
        _need(step['step'] == number and step['subject'] == subject and step['subject_step'] == 1
              and len(step['trial_ids']) == 4 and math.isfinite(step['loss'])
              and step['state_sha256_after'] != prior, 'actual fresh winning source update differs')
        trace.append(('source', winner, None, subject, number))
        losses.append(step['loss'])
        prior = step['state_sha256_after']
    _need(prior == final_fit['fitted_state_sha256'] and len(trace) == TOTAL_UPDATES,
          'complete actual histories must total5253 updates')
    counts = Counter(row[0] for row in trace)
    _need(counts == {'source': SOURCE_UPDATES, 'inner_validation_support': SUPPORT_UPDATES},
          'actual complete source/support work differs from5151/102')
    return {'fold_count': 102, 'final_source_subjects': 51, 'source_updates': SOURCE_UPDATES,
            'support_updates': SUPPORT_UPDATES, 'actual_gradient_updates': TOTAL_UPDATES,
            'selected_candidate': winner, 'scores': payload['scores'],
            'minimum_loss': min(losses), 'maximum_loss': max(losses),
            'fitted_state_sha256': final_fit['fitted_state_sha256']}, trace


def _publication_pins(publication, original_evidence_path):
    def path(name):
        return Path(publication[name]) if isinstance(publication, dict) else getattr(publication, name)

    result = {}
    for name, source in (('manifest', path('manifest_path')), ('evidence', path('evidence_path')),
                         ('weights', path('weights_path')), ('selector_evidence', original_evidence_path)):
        _, result[name] = _read(source, MAXIMUM_WEIGHTS_BYTES if name == 'weights' else MAXIMUM_JSON_BYTES)
    return result


def run_selection(request, *, set_protected_inputs):
    """Execute the actual complete EEGNet selector and publish its real fitted source."""
    import torch
    from torch.optim.optimizer import register_optimizer_step_pre_hook, register_optimizer_step_post_hook
    from adaptation.source_selection import BCIEEGNetSourceSelector
    from core.config import config_digest
    from core.provenance import capture_source
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_method_template import derive_cho_method_template
    from evaluation.phase2_cho_publication_gate import publish_verified_cho_source
    from evaluation.phase2_cho_sweep import materialize_cho_candidates, sweep_cell_identity
    from evaluation.phase2_pilot import AnchorAdapter
    from evaluation.phase2_runner import method_configuration
    from evaluation.phase2_selection_evidence_binding import verify_cho_selection_evidence

    rng = _rng_snapshot()
    plan, method_config, method_pin, fixture, initial_inputs, initial_source = _context(request)
    output = Path(request['selection_output'])
    _need(output.is_dir() and output.resolve(strict=True) == output
          and not (output / 'source-result.json').exists()
          and not (fixture.root / 'runs/phase2/selection_evidence').exists()
          and not (fixture.root / 'runs/phase2/selected_sources').exists(),
          'fresh source output and actual publication namespaces required')
    candidates = materialize_cho_candidates('eegnet', method_config, plan.model_seed)
    _need([asdict(candidate) for candidate in candidates] == method_config['candidates'],
          'public typed materialization differs from the independent adopted template')
    source_file = os.path.normcase(str(PROJECT_ROOT / 'adaptation/source_selection.py'))
    support_file = os.path.normcase(str(PROJECT_ROOT / 'adaptation/anchor_manifest.py'))
    events = []
    pending = {}

    def phase():
        frame = sys._getframe(1)
        support = None
        fold = None
        try:
            while frame is not None:
                filename = os.path.normcase(os.path.abspath(frame.f_code.co_filename))
                if filename == source_file and frame.f_code.co_name == '_fit':
                    local = frame.f_locals
                    return ('source', local['candidate'].name, local['validation_subject'],
                            local['subject'], len(local['history']) + 1)
                if filename == support_file and frame.f_code.co_name == '_predict':
                    local = frame.f_locals
                    _need(local['role'] == 'inner_validation', 'no outer-target support optimization permitted')
                    support = local['subject']
                if filename == source_file and frame.f_code.co_name == '_fold':
                    local = frame.f_locals
                    fold = local['candidate'].name, local['subject']
                frame = frame.f_back
            _need(support is not None and fold is not None and support == fold[1],
                  'SGD call must belong to the real canonical source/support fold')
            return 'inner_validation_support', fold[0], fold[1], support, 1
        finally:
            del frame

    def digest(parameters):
        result = hashlib.sha256()
        for index, parameter in enumerate(parameters):
            result.update(str(index).encode('ascii'))
            result.update(str(tuple(parameter.shape)).encode('ascii'))
            result.update(parameter.detach().cpu().contiguous().numpy().tobytes())
        return result.hexdigest()

    def before_step(optimizer, args, kwargs):
        _need(type(optimizer) is torch.optim.SGD and not pending and len(events) < TOTAL_UPDATES,
              'strict sequential bounded canonical SGD required')
        current = phase()
        parameters = tuple(parameter for group in optimizer.param_groups for parameter in group['params'])
        _need(sum(parameter.numel() for parameter in parameters) == 2642
              and len({id(parameter) for parameter in parameters}) == len(parameters)
              and all(parameter.requires_grad and parameter.dtype == torch.float32
                      and parameter.device.type == 'cpu' and parameter.grad is not None
                      and torch.isfinite(parameter.grad).all().item() for parameter in parameters),
              'actual complete EEGNet2642-parameter finite gradient mask required')
        rate = {'lr_1e-3': 0.001, 'lr_2e-3': 0.002}[current[1]]
        _need(not optimizer.state and all(group['lr'] == rate and group.get('momentum', 0) == 0
              and group.get('weight_decay', 0) == 0 and not group.get('nesterov', False)
              and not group.get('maximize', False) for group in optimizer.param_groups),
              'adopted fixed stateless source/support SGD required')
        pending.update(optimizer=optimizer, phase=current, parameters=parameters, before=digest(parameters))

    def after_step(optimizer, args, kwargs):
        _need(pending.get('optimizer') is optimizer and phase() == pending['phase'],
              'actual SGD post-step identity or role differs')
        _need(all(torch.isfinite(parameter).all().item() for parameter in pending['parameters']),
              'nonfinite actual selected parameters after SGD')
        after = digest(pending['parameters'])
        _need(after != pending['before'], 'each actual SGD update must change parameter bytes')
        events.append({'update': len(events) + 1, 'phase': list(pending['phase']),
                       'selected_parameters': 2642,
                       'selected_state_sha256_before': pending['before'],
                       'selected_state_sha256_after': after,
                       'finite_selected_gradients': True, 'finite_selected_parameters': True})
        pending.clear()

    pre_hook = post_hook = None
    protected = False
    try:
        set_protected_inputs(fixture.protected_outer_paths, True)
        protected = True
        selector = BCIEEGNetSourceSelector(
            fixture.root, fixture.protocol, fixture.catalogs, fixture.selection_record, {},
            outer_target=OUTER_TARGET, candidates=candidates, seed=11,
            shots_per_class=5, maximum_gradient_steps=TOTAL_UPDATES)
        contract_before = selector.contract
        _need(derive_cho_method_template(plan, contract_before, {}) == method_config
              and method_configuration(method_config) == request['method_config_sha256'],
              'actual public selector contract differs from the independent adopted configuration')
        pre_hook = register_optimizer_step_pre_hook(before_step)
        post_hook = register_optimizer_step_post_hook(after_step)
        selected = selector.run_selection()
        pre_hook.remove()
        post_hook.remove()
        pre_hook = post_hook = None
        record = selected.evidence.record
        summary, expected_trace = _history_summary(record)
        _need(not pending and len(events) == TOTAL_UPDATES
              and [tuple(event['phase']) for event in events] == expected_trace,
              'actual5253 optimizer observations differ from complete public source/support histories')
        _need(selector.contract == contract_before and record['payload']['contract'] == contract_before,
              'source selection context changed')
        model = selected.source
        _need(sum(parameter.numel() for parameter in model.parameters()) == 2642
              and model.n_chans == 64 and model.n_outputs == 2 and model.n_times == 512
              and model.sfreq == 128 and not any(module.training for module in model.modules())
              and all(parameter.grad is None for parameter in model.parameters())
              and all(torch.isfinite(value).all().item() for value in model.state_dict().values())
              and state_digest(model) == summary['fitted_state_sha256'],
              'actual complete constrained64/2/512/128 fitted EEGNet source differs')
        evidence_sha = record['sha256']
        evidence_path = fixture.root / 'runs/phase2/selection_evidence' / f'{evidence_sha}.json'
        selected.evidence.write(evidence_path, output_root=fixture.root / 'runs/phase2')
        winner = next(candidate for candidate in candidates if candidate.name == summary['selected_candidate'])
        verified = verify_cho_selection_evidence(
            record=record, evidence_sha256=evidence_sha, plan=plan,
            protocol_config=fixture.protocol, catalogs=fixture.catalogs,
            selection_record=fixture.selection_record, assets={}, root=fixture.root,
            adapter_model_state_sha256=state_digest(model),
            adapter_source_settings=asdict(winner.source), adapter_support_settings=asdict(winner.support))
        _need(verified.selected_candidate == winner.name and verified.evidence_sha256 == evidence_sha,
              'actual public complete-selector verification differs')
        adapter = AnchorAdapter('eegnet', winner.support, model)
        target = next(catalog for catalog in fixture.catalogs if catalog.subject == OUTER_TARGET)
        identity = sweep_cell_identity(
            root=fixture.root, plan=plan, method_config=method_config,
            protocol_sha256=config_digest(fixture.protocol),
            episode_sha256=fixture.episode_records[OUTER_TARGET]['sha256'],
            selection_sha256=fixture.selection_record['sha256'],
            preprocessing_sha256=target.preprocessing_sha256, checkpoint_sha256=state_digest(model))
        published = publish_verified_cho_source(
            root=fixture.root, plan=plan, adapter=adapter, identity=identity,
            method_config=method_config, protocol_config=fixture.protocol,
            evidence_path=evidence_path, selection=verified)
        published.witness.verify_stable()
        _need(not published.publication.resumed and published.publication.weights_format == 'full_v1'
              and published.publication.evidence_format == 'canonical_json_v1'
              and state_digest(model) == summary['fitted_state_sha256'],
              'fresh actual full-state publication must preserve the live selected source')
        publication_files = _publication_pins(published.publication, evidence_path)
    finally:
        if pre_hook is not None:
            pre_hook.remove()
        if post_hook is not None:
            post_hook.remove()
        if protected:
            set_protected_inputs(fixture.protected_outer_paths, False)

    _need(fixture.verify_inputs() == initial_inputs and capture_source(fixture.root) == initial_source,
          'complete selection/publication changed physical inputs or fixture source provenance')
    _need(_method_config(request)[1] == method_pin and _rng_unchanged(rng),
          'independent method pin or global Torch/NumPy/Python RNG changed')
    published.witness.verify_stable()
    _need(_publication_pins(published.publication, evidence_path) == publication_files,
          'actual publication physical identity changed after verification')
    trace_path = output / 'optimizer-observations.json'
    _write(trace_path, {'schema': 'cho51_complete_eegnet_optimizer_observations_v1',
                       'actual_gradient_updates': TOTAL_UPDATES, 'events': events})
    _, trace_pin = _read(trace_path)
    result = {
        'schema': 'cho51_complete_eegnet_source_result_v1', 'passed': True,
        'request_sha256': _request_sha256(request), 'case': asdict(plan), 'case_id': plan.case_id,
        'claim_file_sha256': request['claim_file_sha256'],
        'pins_sha256': request['independent_pins_sha256'],
        'execution_source_sha256': request['execution_source_sha256'],
        'fixture_root': str(fixture.root), 'fixture_source': asdict(initial_source),
        'fixture_identity_path': str(fixture.identity_path),
        'fixture_identity_file_sha256': fixture.identity_file_sha256,
        'fixture_identity_sha256': initial_inputs['sha256'],
        'method_config_path': request['method_config_path'],
        'method_config_file_sha256': request['method_config_file_sha256'],
        'method_config_sha256': request['method_config_sha256'],
        'source_subjects_available': 52, 'source_subjects': list(SOURCE_SUBJECTS),
        'adopted_evaluation_targets': 51, 'adopted_case_plan_count': 1020,
        'outer_target': OUTER_TARGET, 'input_file_count': 213,
        'input_files': initial_inputs['files'], 'physical_inputs': fixture.physical_inputs,
        'protected_outer_paths': [str(path) for path in fixture.protected_outer_paths],
        'selection_evidence_path': str(evidence_path), 'selection_evidence_sha256': evidence_sha,
        'selection_contract_sha256': record['payload']['contract_sha256'],
        'model_state_sha256': summary['fitted_state_sha256'],
        'model_recipe_sha256': config_digest(
            _object(published.publication.manifest_path)[0]['payload']['model_recipe']),
        'initial_winning_source_state_sha256': record['payload']['final_source_fit']['initial_state_sha256'],
        'publication': _plain(asdict(published.publication)),
        'publication_witness': _plain(asdict(published.witness)), 'publication_files': publication_files,
        'identity_metadata': asdict(identity), 'optimizer_trace_path': str(trace_path),
        'optimizer_trace_file_sha256': trace_pin['file_sha256'],
        'optimizer_trace_file_bytes': trace_pin['size_bytes'],
        **summary,
        'source_gradient_updates': SOURCE_UPDATES, 'support_gradient_updates': SUPPORT_UPDATES,
        'maximum_gradient_steps': TOTAL_UPDATES, 'selected_parameters': 2642,
        'public_run_selection_completed': True, 'public_selection_verifier_passed': True,
        'complete': True, 'full_selector_verified': True,
        'all_physical_inputs_rehashed_unchanged': True, 'fixture_source_context_unchanged': True,
        'torch_numpy_python_rng_unchanged': True, 'finite_losses_gradients_parameters': True,
        'canonical_source_exclusion_verified': True, 'publication_performed': True,
        'detached_tensor_verified': False, 'full_worker_verified': False,
        'target_prediction_performed': False, 'recorder_used': False, 'measured_cells': 0,
        'synthetic': True, 'actual_study_data_loaded': False, 'pretrained_weights_loaded': False,
        'engineering_only': True, 'scientific_admission': False,
        'original_case_attempts_remaining': 0,
    }
    _write(output / 'source-result.json', result)
    return result


def verify_publication(request, source_result, *, expected_source_result_file_sha256,
                       set_protected_inputs):
    """Read-only detached reconstruction from the parent's external source-result pin.

The source child never calls this function. The caller carries the exact file
SHA from the accepted fresh source Job into this independently guarded process.
No optimizer, fitting call, target inference, or publication occurs here.
    """
    import torch
    from core.config import config_digest
    from core.provenance import capture_source
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_method_template import derive_cho_method_template
    from evaluation.phase2_cho_selected_manifest_bridge import verify_cho_selected_manifest_files
    from evaluation.phase2_cho_source_restore import (
        prepare_cho_source_restore, restore_cho_selected_source, verify_cho_selected_source_state,
    )
    from evaluation.phase2_pilot import AnchorAdapter
    from evaluation.phase2_protocol import require_digest
    from evaluation.phase2_selected_source_store import SelectedSourceStore

    rng = _rng_snapshot()
    require_digest(expected_source_result_file_sha256, 'external source-result file pin')
    plan, method_config, method_pin, fixture, initial_inputs, initial_source = _context(request)
    output = Path(request['detached_output'])
    _need(output.is_dir() and output.resolve(strict=True) == output
          and not (output / 'detached-result.json').exists(), 'fresh detached output required')
    source_result_path = Path(request['selection_output']) / 'source-result.json'
    observed_result, source_pin = _object(source_result_path)
    _need(source_pin['file_sha256'] == expected_source_result_file_sha256
          and type(source_result) is dict and observed_result == source_result,
          'source result differs from the independently supplied physical file pin')
    _need(source_result.get('schema') == 'cho51_complete_eegnet_source_result_v1'
          and source_result.get('passed') is True
          and source_result.get('request_sha256') == _request_sha256(request)
          and source_result.get('case') == asdict(plan) and source_result.get('case_id') == plan.case_id
          and source_result.get('claim_file_sha256') == request['claim_file_sha256']
          and source_result.get('pins_sha256') == request['independent_pins_sha256']
          and source_result.get('execution_source_sha256') == request['execution_source_sha256']
          and source_result.get('method_config_sha256') == request['method_config_sha256']
          and source_result.get('method_config_file_sha256') == request['method_config_file_sha256']
          and source_result.get('fixture_source') == asdict(initial_source)
          and source_result.get('fixture_identity_sha256') == request['fixture_identity_sha256']
          and source_result.get('fixture_identity_file_sha256') == request['fixture_identity_file_sha256'],
          'actual source result request, adopted method or fixture context differs')
    _need(source_result.get('complete') is True and source_result.get('full_selector_verified') is True
          and source_result.get('public_selection_verifier_passed') is True
          and source_result.get('publication_performed') is True
          and source_result.get('actual_gradient_updates') == TOTAL_UPDATES
          and source_result.get('source_updates') == SOURCE_UPDATES
          and source_result.get('support_updates') == SUPPORT_UPDATES
          and source_result.get('fold_count') == 102 and source_result.get('final_source_subjects') == 51
          and source_result.get('engineering_only') is True
          and source_result.get('scientific_admission') is False
          and source_result.get('original_case_attempts_remaining') == 0
          and source_result.get('measured_cells') == 0
          and source_result.get('target_prediction_performed') is False,
          'source result must describe exactly one complete synthetic engineering selector')
    publication = source_result['publication']
    for key in ('manifest_sha256', 'evidence_sha256', 'model_state_sha256', 'weights_sha256'):
        require_digest(publication[key], f'source publication {key}')
    _need(publication['manifest_path'] == str(fixture.root / 'runs/phase2/selected_sources/manifests'
                / f"{publication['manifest_sha256']}.json")
          and publication['evidence_path'] == str(fixture.root / 'runs/phase2/selected_sources/evidence'
                / f"{publication['evidence_sha256']}.json")
          and publication['weights_path'] == str(fixture.root / 'runs/phase2/selected_sources/weights'
                / f"{publication['weights_sha256']}.safetensors")
          and publication['resumed'] is False and publication['weights_format'] == 'full_v1'
          and publication['evidence_format'] == 'canonical_json_v1'
          and publication['evidence_sha256'] == source_result['selection_evidence_sha256']
          and publication['model_state_sha256'] == source_result['model_state_sha256']
          and publication['selected_candidate'] == source_result['selected_candidate'],
          'source publication must use its direct canonical content-addressed paths')
    evidence_path = fixture.root / 'runs/phase2/selection_evidence' / f"{publication['evidence_sha256']}.json"
    _need(str(evidence_path) == source_result['selection_evidence_path'],
          'original selector evidence path differs from its logical pin')
    protected = False
    try:
        set_protected_inputs(fixture.protected_outer_paths, True)
        protected = True
        record, _ = _object(evidence_path)
        summary, expected_trace = _history_summary(record)
        _need(record['sha256'] == publication['evidence_sha256']
              and record['payload']['contract_sha256'] == source_result['selection_contract_sha256']
              and derive_cho_method_template(plan, record['payload']['contract'], {}) == method_config
              and summary['fitted_state_sha256'] == publication['model_state_sha256']
              and summary['selected_candidate'] == publication['selected_candidate'],
              'detached actual complete evidence differs from independent source publication pins')
        for key, value in summary.items():
            _need(source_result.get(key) == value, 'source summary differs from detached complete-history reconstruction')
        trace_path = Path(request['selection_output']) / 'optimizer-observations.json'
        trace, trace_pin = _object(trace_path)
        _need(source_result['optimizer_trace_path'] == str(trace_path)
              and trace_pin['file_sha256'] == source_result['optimizer_trace_file_sha256']
              and trace_pin['size_bytes'] == source_result['optimizer_trace_file_bytes']
              and trace.get('schema') == 'cho51_complete_eegnet_optimizer_observations_v1'
              and trace.get('actual_gradient_updates') == TOTAL_UPDATES
              and len(trace['events']) == TOTAL_UPDATES,
              'real source optimizer observation transcript differs from its external pin')
        for number, (event, phase) in enumerate(zip(trace['events'], expected_trace, strict=True), 1):
            _need(event['update'] == number and event['phase'] == list(phase)
                  and event['selected_parameters'] == 2642
                  and event['finite_selected_gradients'] is True
                  and event['finite_selected_parameters'] is True
                  and event['selected_state_sha256_before'] != event['selected_state_sha256_after'],
                  'detached source update observations differ from actual complete histories')
        prepared = prepare_cho_source_restore(
            root=fixture.root, plan=plan, method_config=method_config,
            expected_method_config_sha256=request['method_config_sha256'],
            selected_candidate=publication['selected_candidate'])
        _need(prepared.model_config_path is None and prepared.baseline_weights_path is None
              and config_digest(prepared.model_recipe) == source_result['model_recipe_sha256'],
              'independently derived EEGNet recipe must require no external baseline')
        witness = verify_cho_selected_manifest_files(
            fixture.root, Path(publication['manifest_path']),
            manifest_sha256=publication['manifest_sha256'], evidence_sha256=publication['evidence_sha256'],
            selection_contract_sha256=source_result['selection_contract_sha256'],
            selected_candidate=publication['selected_candidate'],
            protocol_config_sha256=config_digest(fixture.protocol), expected_source=initial_source,
            model_recipe_sha256=source_result['model_recipe_sha256'],
            model_state_sha256=publication['model_state_sha256'])
        actual_files = _publication_pins(publication, evidence_path)
        _need(actual_files == source_result['publication_files'],
              'source publication physical bytes or identities changed before detached restoration')
        _need(type(actual_files['weights']['size_bytes']) is int
              and 0 < actual_files['weights']['size_bytes'] <= MAXIMUM_WEIGHTS_BYTES,
              'independently pinned EEGNet full-state file must fit the fixed one-MiB bound')
        restore_limits = []

        class BoundedEEGNetStore(SelectedSourceStore):
            """Inject only the EEGNet byte ceiling into unchanged public restoration."""

            def restore(self, manifest_sha256, model, *, expected_evidence_sha256,
                        protocol_config, model_recipe,
                        maximum_weights_bytes=MAXIMUM_WEIGHTS_BYTES):
                _need(type(maximum_weights_bytes) is int
                      and 0 < maximum_weights_bytes <= MAXIMUM_WEIGHTS_BYTES,
                      'EEGNet restore requires a positive integer byte limit no greater than one MiB')
                restore_limits.append(maximum_weights_bytes)
                return super().restore(
                    manifest_sha256, model,
                    expected_evidence_sha256=expected_evidence_sha256,
                    protocol_config=protocol_config, model_recipe=model_recipe,
                    maximum_weights_bytes=maximum_weights_bytes)

        store = BoundedEEGNetStore(fixture.root)
        # The actual public tensor checker retains its unmodified six/four GiB
        # host-RAM checks and independently reconstructs the seeded full model.
        tensor_witness = verify_cho_selected_source_state(
            root=fixture.root, plan=plan, method_config=method_config,
            expected_method_config_sha256=request['method_config_sha256'],
            selected_candidate=publication['selected_candidate'],
            manifest_sha256=publication['manifest_sha256'], evidence_sha256=publication['evidence_sha256'],
            protocol_config=fixture.protocol,
            expected_model_recipe_sha256=source_result['model_recipe_sha256'],
            expected_model_state_sha256=publication['model_state_sha256'], store=store)
        restored = restore_cho_selected_source(
            root=fixture.root, plan=plan, method_config=method_config,
            expected_method_config_sha256=request['method_config_sha256'],
            selected_candidate=publication['selected_candidate'],
            manifest_sha256=publication['manifest_sha256'], evidence_sha256=publication['evidence_sha256'],
            protocol_config=fixture.protocol, catalogs=fixture.catalogs,
            selection_record=fixture.selection_record, assets={}, store=store)
        _need(restore_limits == [MAXIMUM_WEIGHTS_BYTES, MAXIMUM_WEIGHTS_BYTES],
              'both actual public restore paths must delegate with the fixed one-MiB EEGNet limit')
        model = restored.restored.model
        _need(type(restored.adapter) is AnchorAdapter and restored.adapter.method == 'eegnet'
              and restored.adapter._model is model
              and restored.selection.selected_candidate == publication['selected_candidate']
              and restored.selection.evidence_sha256 == publication['evidence_sha256']
              and restored.restored.evidence_record == record
              and restored.model_recipe == prepared.model_recipe
              and state_digest(model) == publication['model_state_sha256']
              and sum(parameter.numel() for parameter in model.parameters()) == 2642
              and all(parameter.grad is None for parameter in model.parameters()),
              'actual detached public restore must release the exact fitted full-source adapter')
        manifest, _ = _object(Path(publication['manifest_path']))
        schema = manifest['payload']['tensor_schema']
        expected_state = model.state_dict()
        _need(set(schema) == set(expected_state) and all(
            list(value.shape) == schema[name]['shape'] and str(value.dtype) == schema[name]['dtype']
            and torch.isfinite(value).all().item() for name, value in expected_state.items()),
            'every publicly restored tensor must match the complete pinned finite schema')
        _need(asdict(tensor_witness) == {
            'manifest_sha256': publication['manifest_sha256'],
            'evidence_sha256': publication['evidence_sha256'],
            'selected_candidate': publication['selected_candidate'],
            'model_recipe_sha256': source_result['model_recipe_sha256'],
            'model_state_sha256': publication['model_state_sha256'],
            'weights_sha256': publication['weights_sha256']},
            'actual public independent tensor witness differs from external source pins')
        witness.verify_stable()
        _need(_publication_pins(restored.restored.publication, evidence_path) == actual_files,
              'publication changed during detached tensor reconstruction')
        # Both public paths decode full_v1 only inside their trusted restore
        # stacks, verify every tensor's schema/finite bytes, strictly load the
        # complete state and compare its full byte digest with the external pin.
        # No second decoder is called outside those public gates.
        tensor_count = len(expected_state)
        restored_publication = _plain(asdict(restored.restored.publication))
    finally:
        if protected:
            set_protected_inputs(fixture.protected_outer_paths, False)

    _need(fixture.verify_inputs() == initial_inputs and capture_source(fixture.root) == initial_source
          and _method_config(request)[1] == method_pin and _rng_unchanged(rng),
          'detached verification changed physical inputs, source context, method pins or global RNG')
    _need(_object(source_result_path)[1] == source_pin and _object(trace_path)[1] == trace_pin,
          'external source-result or optimizer transcript changed during detached verification')
    witness.verify_stable()
    result = {
        'schema': 'cho51_complete_eegnet_detached_result_v1', 'passed': True,
        'request_sha256': _request_sha256(request), 'case': asdict(plan), 'case_id': plan.case_id,
        'claim_file_sha256': request['claim_file_sha256'],
        'pins_sha256': request['independent_pins_sha256'],
        'execution_source_sha256': request['execution_source_sha256'],
        'fixture_root': str(fixture.root), 'fixture_source': asdict(initial_source),
        'fixture_identity_sha256': initial_inputs['sha256'],
        'fixture_identity_file_sha256': fixture.identity_file_sha256,
        'method_config_sha256': request['method_config_sha256'],
        'method_config_file_sha256': request['method_config_file_sha256'],
        'source_result_path': str(source_result_path),
        'source_result_file_sha256': expected_source_result_file_sha256,
        'source_result_identity': source_pin['identity'],
        'selected_candidate': publication['selected_candidate'],
        'selection_evidence_sha256': publication['evidence_sha256'],
        'selection_contract_sha256': source_result['selection_contract_sha256'],
        'model_state_sha256': publication['model_state_sha256'],
        'model_recipe_sha256': source_result['model_recipe_sha256'],
        'publication': publication, 'publication_files': actual_files,
        'restored_publication': restored_publication,
        'publication_witness': _plain(asdict(witness)), 'tensor_witness': asdict(tensor_witness),
        'tensor_count': tensor_count, 'all_tensors_equal': True,
        'full_state_digest_matches': True,
        'tensor_equality_boundary': 'two_public_full_state_restores_and_external_full_state_digest',
        'bounded_store': {
            'schema': 'cho51_eegnet_full_state_bound_v1',
            'base_class': 'evaluation.phase2_selected_source_store.SelectedSourceStore',
            'maximum_weights_bytes': MAXIMUM_WEIGHTS_BYTES,
            'actual_weights_bytes': actual_files['weights']['size_bytes'],
            'restore_limits_bytes': restore_limits,
            'generic_restore_default_bytes': 4 * 1024**3,
            'generic_restore_default_avoided': True,
            'canonical_restore_delegated': True,
            'public_factory_store_injection': True,
        },
        'initial_lineage_reconstructed': True, 'public_restore_adapter_released': True,
        'public_selection_verifier_passed': True, 'full_selector_verified': True,
        'verified_source_gradient_updates': TOTAL_UPDATES,
        'verified_source_updates': SOURCE_UPDATES, 'verified_support_updates': SUPPORT_UPDATES,
        'verified_fold_count': 102, 'verified_final_source_subjects': 51,
        'actual_gradient_updates': 0, 'detached_tensor_verified': True,
        'all_physical_inputs_rehashed_unchanged': True, 'fixture_source_context_unchanged': True,
        'torch_numpy_python_rng_unchanged': True,
        'full_worker_verified': False, 'target_prediction_performed': False,
        'publication_performed': False, 'recorder_used': False, 'measured_cells': 0,
        'synthetic': True, 'actual_study_data_loaded': False, 'pretrained_weights_loaded': False,
        'engineering_only': True, 'scientific_admission': False,
        'original_case_attempts_remaining': 0,
    }
    _write(output / 'detached-result.json', result)
    return result
