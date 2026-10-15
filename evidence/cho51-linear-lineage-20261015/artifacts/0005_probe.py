"""Audited safe-baseline lineage and two real partial linear source folds.

Numerical imports and execution belong inside a fresh admitted native child.
This is neither complete source selection nor a selected-source restoration.
"""
from __future__ import annotations

import copy
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
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BASELINE_DIRECTORY = (
    '.cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/'
    '0563b6c626e7b40d9a36653b763715db94d945d7'
)
BASELINE_CONFIG_SHA256 = '813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b'
BASELINE_WEIGHTS_SHA256 = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
SUBJECTS = tuple(f'subject_{number:02d}' for number in range(1, 53))
TRAINING_SUBJECTS = SUBJECTS[2:]
OUTER_TARGET = 'subject_02'
INNER_VALIDATION = 'subject_01'
RATES = (0.001, 0.002)
NAMES = ('lr_1e-3', 'lr_2e-3')
PUBLIC_REFUSAL = 'selection evidence has missing or unexpected fields'


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _canonical(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(',', ':'))


def _write(path, value):
    raw = (_canonical(value) + '\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'path': str(path), 'file_sha256': hashlib.sha256(raw).hexdigest(),
            'size_bytes': len(raw)}


def _identity(path):
    info = path.stat(follow_symlinks=False)
    _need(path.is_absolute() and path.resolve(strict=True) == path
          and stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
          'baseline must be one ordinary direct single-link file')
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _read_baseline(path, *, maximum_bytes, expected_bytes, expected_sha256):
    """Bound before decoding and check path/descriptor identities separately."""
    before = _identity(path)
    _need(before[2] == expected_bytes and 0 < expected_bytes <= maximum_bytes,
          'audited baseline length exceeds the fixed bound or differs')
    with path.open('rb') as stream:
        info = os.fstat(stream.fileno())
        opened = info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
        _need(opened[:4] == before[:4] and stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
              'baseline opened descriptor differs')
        raw = stream.read(maximum_bytes + 1)
        info = os.fstat(stream.fileno())
        finished = info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
    _need(opened == finished and _identity(path) == before and len(raw) == expected_bytes
          and hashlib.sha256(raw).hexdigest() == expected_sha256,
          'audited baseline changed during its bounded read')
    return raw, {'path': str(path), 'file_sha256': expected_sha256,
                 'size_bytes': len(raw), 'identity': list(before),
                 'read_limit_bytes': maximum_bytes}


def _module(path, name):
    _need(name not in sys.modules, 'fresh pinned helper import required')
    spec = importlib.util.spec_from_file_location(name, path)
    _need(spec is not None and spec.loader is not None, 'pinned helper module required')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_probe(output: Path, method_config: dict, *, set_protected_inputs) -> dict:
    """Execute two declared candidate folds, with all four outer files denied.

    ``set_protected_inputs(paths, enabled)`` is supplied by the independent
    native child. It denies outer target reads throughout model construction,
    independent canonical lineage reconstruction, and both public folds.
    """
    _need(isinstance(output, Path) and output.is_absolute() and output.is_dir()
          and output.resolve(strict=True) == output, 'existing direct owned output required')
    _need(type(method_config) is dict and callable(set_protected_inputs),
          'detached adopted method configuration and input protection required')
    _need(all(not (output / name).exists() for name in (
        'fixture', 'fold_01.json', 'fold_02.json', 'partial-collection.json',
        'optimizer-observations.json', 'probe-result.json')), 'unused owned output required')

    import numpy as np
    import torch
    from braindecode.models import Labram
    from safetensors.torch import load
    from torch.nn.modules.module import register_module_forward_pre_hook
    from torch.optim.optimizer import register_optimizer_step_pre_hook, register_optimizer_step_post_hook
    from adaptation.labram_manifest import LaBraMTuningSettings
    from adaptation.labram_source import BCILaBraMSourceSelector, LaBraMSourceCandidate, LaBraMSourceSettings
    from core.config import canonical_config_json, config_digest, config_snapshot
    from core.provenance import source_fingerprint
    from encoder.labram import LaBraMClassifier, configure_pretrained_sequence
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_source_restore import prepare_cho_source_restore, _new_model
    from evaluation.phase2_profile_binding import CHO_CHANNELS
    from evaluation.phase2_protocol import nested_episode, source_selection
    from evaluation.phase2_records import verify_envelope
    from evaluation.phase2_runner import CasePlan, method_configuration
    from evaluation.phase2_selection_evidence_binding import verify_cho_selection_evidence

    _need(torch.get_num_threads() == torch.get_num_interop_threads() == 1
          and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'one-thread hidden-GPU child required')
    rng_before = (torch.random.get_rng_state().clone(), np.random.get_state(), random.getstate())
    fixture_module = _module(
        PROJECT_ROOT / 'docs/phase2/cho51_source_fold_probe_v1/fixture.py',
        '_cho51_linear_lineage_fixture_v1')
    fixture = fixture_module.build_fixture(output, 'labram_linear')
    inputs_before = fixture.verify_inputs()
    source_before = source_fingerprint(fixture.root)
    _need(tuple(c.subject for c in fixture.catalogs) == SUBJECTS
          and len(fixture.input_paths) == 213 and len(fixture.protected_outer_paths) == 4
          and sum(pin['size_bytes'] for pin in inputs_before['files'].values()) == 734579463
          and inputs_before['canonical_shot_levels'] == [1, 5, 10, 20]
          and inputs_before['profile_a_shape'] == [42, 64, 512]
          and inputs_before['profile_b_shape'] == [42, 64, 800],
          'unchanged complete 52-subject synthetic physical inventory required')
    expected_method = {
        'dataset': 'cho2017', 'method': 'labram_linear', 'input_profile': 'cho_profile_b_60hz_v1',
        'variant_config_sha256': fixture.assets[INNER_VALIDATION].variant_config_sha256,
        'source_seed_policy': 'none',
        'source_policy': 'all_non_target_subjects; inner_validation_also_excluded',
        'score': 'mean_subject_balanced_accuracy_exact_rational',
        'tie_break': 'first_in_declared_candidate_order', 'early_stopping': False,
        'candidates': [
            {'name': name,
             'source': {'method': 'linear', 'steps_per_subject': 1, 'batch_size': 2,
                        'learning_rate': rate, 'partial_depth': None},
             'support': {'method': 'linear', 'steps': 1, 'learning_rate': rate,
                         'partial_depth': None, 'query_batch_size': 8}}
            for name, rate in zip(NAMES, RATES, strict=True)],
    }
    _need(method_config == expected_method, 'exact adopted linear candidate configuration required')
    method_sha = method_configuration(method_config)
    candidates = tuple(LaBraMSourceCandidate(
        row['name'], LaBraMSourceSettings(**row['source']), LaBraMTuningSettings(**row['support']))
        for row in method_config['candidates'])
    selection = source_selection(fixture.catalogs, target=OUTER_TARGET)
    _need(selection.source_subjects == ('subject_01', *TRAINING_SUBJECTS)
          and len(selection.inner_folds) == 51, 'canonical all-source exclusion required')
    plan = CasePlan('cho2017', OUTER_TARGET, 'labram_linear', 5, 11, 1)
    records, fold_pins, timings, events = [], [], [], []
    pending, active_model, current = {}, {}, {}
    handles = []
    protected = False

    def model_digest(model, *, head_only=False):
        digest = hashlib.sha256()
        for name, value in model.state_dict().items():
            if head_only and not name.startswith('head.'):
                continue
            digest.update(name.encode('utf-8'))
            digest.update(str(tuple(value.shape)).encode('ascii'))
            digest.update(str(value.dtype).encode('ascii'))
            digest.update(value.detach().cpu().contiguous().numpy().tobytes())
        return digest.hexdigest()

    def selected_digest(parameters):
        digest = hashlib.sha256()
        for index, parameter in enumerate(parameters):
            digest.update(str(index).encode('ascii'))
            digest.update(str(tuple(parameter.shape)).encode('ascii'))
            digest.update(parameter.detach().cpu().contiguous().numpy().tobytes())
        return digest.hexdigest()

    def check_frozen(model):
        _need(tuple(name for name, p in model.named_parameters() if p.requires_grad)
              == ('head.weight', 'head.bias')
              and sum(p.numel() for p in model.parameters() if p.requires_grad) == 402
              and all(p.grad is None for name, p in model.named_parameters()
                      if name.startswith('backbone.'))
              and state_digest(model.backbone) == backbone_sha,
              'linear backbone, buffers, gradient exclusion or exact head mask changed')

    def before_forward(module, args):
        if isinstance(module, LaBraMClassifier):
            check_frozen(module)
            active_model['model'] = module

    def before_step(optimizer, args, kwargs):
        _need(type(optimizer) is torch.optim.SGD and not pending and len(events) < 102,
              'actual sequential bounded canonical SGD required')
        parameters = tuple(p for group in optimizer.param_groups for p in group['params'])
        model = active_model.get('model')
        _need(model is not None and tuple(id(p) for p in parameters)
              == tuple(id(p) for p in model.head.parameters())
              and len(parameters) == 2 and sum(p.numel() for p in parameters) == 402,
              'optimizer must select exactly current classifier head')
        check_frozen(model)
        _need(all(p.device.type == 'cpu' and p.dtype == torch.float32 and p.requires_grad
                  and p.grad is not None and torch.isfinite(p.grad).all().item()
                  and torch.isfinite(p).all().item() for p in parameters)
              and not optimizer.state and all(
                  group['lr'] == current['rate'] and group.get('momentum', 0) == 0
                  and group.get('weight_decay', 0) == 0 and not group.get('nesterov', False)
                  and not group.get('maximize', False) for group in optimizer.param_groups),
              'finite head-only gradients and exact fresh adopted learning rate required')
        pending.update(optimizer=optimizer, model=model, parameters=parameters,
                       before=selected_digest(parameters))

    def after_step(optimizer, args, kwargs):
        _need(pending.get('optimizer') is optimizer, 'optimizer post-step identity differs')
        parameters = pending['parameters']
        check_frozen(pending['model'])
        after = selected_digest(parameters)
        _need(after != pending['before'] and all(torch.isfinite(p).all().item() for p in parameters),
              'actual finite head SGD must change selected bytes')
        index = len(events) - current['offset']
        _need(0 <= index <= 50, 'exact 50-source/one-support per-fold bound required')
        events.append({
            'update': len(events) + 1, 'fold_update': index + 1,
            'candidate': current['name'], 'validation_subject': INNER_VALIDATION,
            'role': 'source' if index < 50 else 'inner_validation_support',
            'subject': TRAINING_SUBJECTS[index] if index < 50 else INNER_VALIDATION,
            'learning_rate': current['rate'], 'selected_parameters': 402, 'selected_tensors': 2,
            'selected_state_sha256_before': pending['before'],
            'selected_state_sha256_after': after, 'finite_selected_gradients': True,
            'finite_selected_parameters': True, 'frozen_backbone_and_buffers_unchanged': True,
        })
        pending.clear()

    try:
        set_protected_inputs(fixture.protected_outer_paths, True)
        protected = True
        setup_start = perf_counter()
        prepared = prepare_cho_source_restore(
            root=PROJECT_ROOT, plan=plan, method_config=method_config,
            expected_method_config_sha256=method_sha, selected_candidate=NAMES[0])
        _need(prepared.model_config_path == PROJECT_ROOT / BASELINE_DIRECTORY / 'config.json'
              and prepared.baseline_weights_path == PROJECT_ROOT / BASELINE_DIRECTORY / 'model.safetensors',
              'canonical recipe must resolve the exact audited safe baseline')
        config_raw, config_pin = _read_baseline(
            prepared.model_config_path, maximum_bytes=1024**2, expected_bytes=4776,
            expected_sha256=BASELINE_CONFIG_SHA256)
        weights_raw, weights_pin = _read_baseline(
            prepared.baseline_weights_path, maximum_bytes=32 * 1024**2, expected_bytes=23299672,
            expected_sha256=BASELINE_WEIGHTS_SHA256)
        settings = json.loads(config_raw.decode('utf-8'))
        _need(type(settings) is dict and settings.get('braindecode_version') == '1.3.2'
              and settings.get('n_times') == 3000 and settings.get('n_outputs') == 0,
              'audited complete 3000-sample pretrained architecture metadata required')
        safe_state = load(weights_raw)
        _need(type(safe_state) is dict and len(safe_state) == 221
              and sum(t.numel() for t in safe_state.values()) == 5819936
              and all(isinstance(t, torch.Tensor) and t.device.type == 'cpu'
                      and t.dtype == torch.float32 and torch.isfinite(t).all().item()
                      for t in safe_state.values()), 'all221 finite CPU float32 safe tensors required')
        safe_tensor_metadata = [
            {'name': name, 'shape': list(tensor.shape), 'dtype': str(tensor.dtype),
             'elements': tensor.numel()} for name, tensor in sorted(safe_state.items())]
        with torch.random.fork_rng(devices=[]):
            model_settings = copy.deepcopy(settings)
            model_settings.pop('braindecode_version')
            backbone = Labram(**model_settings)
            backbone.load_state_dict(safe_state, strict=True)
            del safe_state, weights_raw
            configure_pretrained_sequence(backbone, samples=800)
            torch.random.set_rng_state(torch.Generator(device='cpu').manual_seed(11).get_state())
            template = LaBraMClassifier(backbone, classes=2, channel_names=CHO_CHANNELS).cpu().float().eval()
            del backbone
        _need(len(template.backbone.blocks) == 12 and int(template.backbone.embed_dim) == 200
              and sum(p.numel() for p in template.parameters()) == 5818138
              and all(p.device.type == 'cpu' and p.dtype == torch.float32 for p in template.parameters()),
              'full12-block/embed200/5818138-parameter CPU classifier required')
        template_sha = state_digest(template)
        backbone_sha = state_digest(template.backbone)
        template_full_sha = model_digest(template)
        selector = BCILaBraMSourceSelector(
            fixture.root, fixture.protocol, fixture.catalogs, fixture.selection_record,
            template, fixture.assets, outer_target=OUTER_TARGET, template_state_sha256=template_sha,
            candidates=candidates, seed=11, shots_per_class=5, maximum_gradient_steps=5253,
            source_device='cpu', checkpoint_directory=None, operator_compute_admitted=False)
        contract = selector.contract
        initial = selector._initial  # Read-only ownership/lineage inspection; never a private fit call.
        initial_sha = state_digest(initial)
        _need(contract['template_state_sha256'] == template_sha
              and contract['initial_state_sha256'] == initial_sha
              and contract['prior_template_training_verified'] is False
              and contract['maximum_gradient_steps'] == 5253
              and 'source_execution' not in contract, 'canonical CPU lineage declaration differs')
        check_frozen(initial)
        reconstructed = _new_model(prepared, contract=contract)
        check_frozen(reconstructed)
        models = (template, initial, reconstructed)
        storages = [{value.untyped_storage().data_ptr() for value in model.state_dict().values()
                     if value.numel()} for model in models]
        _need(all(not storages[a] & storages[b] for a in range(3) for b in range(a + 1, 3))
              and state_digest(reconstructed) == initial_sha
              and model_digest(reconstructed) == model_digest(initial)
              and list(dict(reconstructed.named_buffers())) == list(dict(initial.named_buffers()))
              and state_digest(template.backbone) == state_digest(initial.backbone) == backbone_sha,
              'independent reconstruction must match owned initial lineage without shared storage')
        independent_sha = state_digest(reconstructed)
        del models, reconstructed, storages
        setup_seconds = perf_counter() - setup_start
        handles.append(register_module_forward_pre_hook(before_forward))
        handles.append(register_optimizer_step_pre_hook(before_step))
        handles.append(register_optimizer_step_post_hook(after_step))
        for index, (candidate, rate) in enumerate(zip(candidates, RATES, strict=True), 1):
            current.update(name=candidate.name, rate=rate, offset=len(events))
            active_model.clear()
            started = perf_counter()
            evidence = selector.run_fold(candidate_name=candidate.name,
                                         validation_subject=INNER_VALIDATION)
            timings.append(perf_counter() - started)
            _need(not pending and len(events) == index * 51
                  and selector.contract == contract
                  and state_digest(initial) == initial_sha and state_digest(template) == template_sha
                  and model_digest(template) == template_full_sha
                  and all(p.grad is None for p in template.parameters()),
                  'fold must perform exactly51 updates while preserving owned/template states')
            check_frozen(initial)
            record = evidence.record
            payload = record['payload']
            _need(verify_envelope(record, kind='engineering_smoke', expected_payload=payload)
                  and set(payload) == {'purpose', 'contract', 'contract_sha256', 'complete',
                                       'folds', 'selected_candidate'}
                  and payload['contract'] == contract and payload['contract_sha256'] == config_digest(contract)
                  and payload['complete'] is False and payload['selected_candidate'] is None
                  and len(payload['folds']) == 1, 'actual raw incomplete public fold envelope required')
            fold = payload['folds'][0]
            fit = fold['source_fit']
            _need(fold['candidate'] == candidate.name and fold['validation_subject'] == INNER_VALIDATION
                  and fit['candidate'] == candidate.name and fit['validation_subject'] == INNER_VALIDATION
                  and fit['training_subjects'] == list(TRAINING_SUBJECTS)
                  and set(fit['input_identities']) == set(TRAINING_SUBJECTS)
                  and fit['settings'] == config_snapshot(asdict(candidate.source))
                  and fit['initial_state_sha256'] == initial_sha
                  and len(fit['steps']) == 50 and fit['mask']['trainable_parameters'] == 402
                  and fit['mask']['trainable_names'] == ['head.weight', 'head.bias']
                  and fold['support_mask']['trainable_names'] == ['head.weight', 'head.bias']
                  and fold['support_mask']['trainable_parameters'] == 402,
                  'exact source subjects, adopted source settings and head masks required')
            catalogs = {catalog.subject: catalog for catalog in fixture.catalogs}
            prior = initial_sha
            for number, (subject, step) in enumerate(zip(TRAINING_SUBJECTS, fit['steps'], strict=True), 1):
                _need(step['step'] == number and step['subject'] == subject
                      and step['subject_step'] == 1 and step['iterator_wraps'] == 0
                      and len(step['trial_ids']) == len(set(step['trial_ids'])) == 2
                      and set(step['trial_ids']) <= set(catalogs[subject].trial_ids)
                      and type(step['loss']) in (int, float) and math.isfinite(step['loss'])
                      and step['state_sha256_after'] != prior, 'real finite two-trial source history differs')
                prior = step['state_sha256_after']
            episode = nested_episode(catalogs[INNER_VALIDATION], shots=(1, 5, 10, 20),
                                     protocol_sha256=config_digest(fixture.protocol))
            partition = episode.partition(5)
            support_ids = [episode.catalog.trial_ids[n] for n in partition.support_indices]
            query_ids = [episode.catalog.trial_ids[n] for n in partition.query_indices]
            losses = fold['support_losses']
            _need(prior == fit['fitted_state_sha256'] and prior != initial_sha
                  and fold['adapted_state_sha256'] != prior
                  and fold['binding']['subject'] == INNER_VALIDATION
                  and fold['binding']['support_trial_ids'] == support_ids
                  and fold['binding']['query_trial_ids'] == query_ids
                  and len(support_ids) == 10 and len(query_ids) == 2
                  and not set(support_ids) & set(query_ids)
                  and len(losses) == 1 and all(type(v) in (int, float) and math.isfinite(v) for v in losses),
                  'actual withheld support/query continuation and finite changed states required')
            confusion = fold['confusion_matrix']
            _need(type(confusion) is list and len(confusion) == 2
                  and all(type(row) is list and len(row) == 2 and sum(row) == 1
                          and all(type(v) is int and v >= 0 for v in row) for row in confusion),
                  'exact one-query-per-class confusion required')
            score = sum((Fraction(confusion[n][n], sum(confusion[n])) for n in range(2)), Fraction()) / 2
            _need(fold['balanced_accuracy'] == [score.numerator, score.denominator],
                  'independently recomputed exact rational score differs')
            evidence_path = output / f'fold_{index:02d}.json'
            evidence.write(evidence_path, output_root=output)
            raw = (canonical_config_json(record) + '\n').encode('utf-8')
            _need(evidence_path.read_bytes() == raw, 'persisted raw fold bytes differ')
            refusal = None
            try:
                verify_cho_selection_evidence(
                    record=record, evidence_sha256=record['sha256'], plan=plan,
                    protocol_config=fixture.protocol, catalogs=fixture.catalogs,
                    selection_record=fixture.selection_record, assets=fixture.assets, root=fixture.root,
                    adapter_model_state_sha256=fit['fitted_state_sha256'],
                    adapter_source_settings=contract['candidates'][index - 1]['source'],
                    adapter_support_settings=contract['candidates'][index - 1]['support'])
            except ValueError as error:
                refusal = str(error)
            _need(refusal == PUBLIC_REFUSAL, 'raw partial record must fail public complete-selector schema')
            fold_pins.append({'candidate': candidate.name, 'validation_subject': INNER_VALIDATION,
                              'path': str(evidence_path), 'evidence_sha256': record['sha256'],
                              'file_sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw),
                              'elapsed_seconds': timings[-1], 'public_refusal_reason': refusal,
                              'fitted_state_sha256': fit['fitted_state_sha256'],
                              'adapted_state_sha256': fold['adapted_state_sha256'],
                              'balanced_accuracy': fold['balanced_accuracy']})
            records.append(record)
            active_model.clear()
        final_config_raw, final_config_pin = _read_baseline(
            prepared.model_config_path, maximum_bytes=1024**2, expected_bytes=4776,
            expected_sha256=BASELINE_CONFIG_SHA256)
        final_weights_raw, final_weights_pin = _read_baseline(
            prepared.baseline_weights_path, maximum_bytes=32 * 1024**2, expected_bytes=23299672,
            expected_sha256=BASELINE_WEIGHTS_SHA256)
        _need(final_config_pin == config_pin and final_weights_pin == weights_pin,
              'audited baseline bytes or identity changed after folds')
        del final_config_raw, final_weights_raw
    finally:
        for handle in reversed(handles):
            handle.remove()
        if protected:
            set_protected_inputs(fixture.protected_outer_paths, False)

    _need(fixture.verify_inputs() == inputs_before
          and source_fingerprint(fixture.root) == source_before, 'all physical fixture inputs/context must remain exact')
    numpy_after = np.random.get_state()
    _need(torch.equal(torch.random.get_rng_state(), rng_before[0])
          and numpy_after[0] == rng_before[1][0] and np.array_equal(numpy_after[1], rng_before[1][1])
          and numpy_after[2:] == rng_before[1][2:] and random.getstate() == rng_before[2],
          'whole probe must preserve global Torch/NumPy/Python RNG')
    contract_module = _module(Path(__file__).with_name('contract.py'), '_cho51_linear_lineage_contract_v1')
    collection = contract_module.collect_partial(
        records, method_config, input_identity_sha256=inputs_before['sha256'],
        template_state_sha256=template_sha, initial_state_sha256=initial_sha,
        lineage_recipe_sha256=config_digest(prepared.model_recipe))
    collection_pin = _write(output / 'partial-collection.json', collection)
    observation_pin = _write(output / 'optimizer-observations.json', {
        'schema': 'cho51_linear_lineage_optimizer_observations_v1', 'events': events,
        'actual_gradient_updates': len(events), 'source_gradient_updates': 100,
        'support_gradient_updates': 2, 'frozen_backbone_sha256': backbone_sha,
        'head_parameter_count': 402, 'head_tensor_count': 2,
        'engineering_only': True, 'scientific_admission': False})
    result = {
        'schema': 'cho51_linear_lineage_probe_v1', 'passed': True, 'method': 'labram_linear',
        'case': asdict(plan), 'case_id': plan.case_id, 'fixture_root': str(fixture.root),
        'input_identity_path': str(fixture.identity_path), 'input_identity_sha256': inputs_before['sha256'],
        'input_identity_file_sha256': fixture.identity_file_sha256, 'input_file_count': 213,
        'input_files': inputs_before['files'], 'physical_inputs': fixture.physical_inputs,
        'input_bytes': 734579463, 'protected_outer_paths': [str(p) for p in fixture.protected_outer_paths],
        'fixture_source_sha256': source_before, 'source_subjects_available': 52,
        'adopted_evaluation_targets': 51, 'adopted_case_plan_count': 1020,
        'outer_target': OUTER_TARGET, 'inner_validation_subject': INNER_VALIDATION,
        'training_subjects': list(TRAINING_SUBJECTS), 'declared_candidates': contract['candidates'],
        'executed_candidates': list(NAMES), 'candidate_rates': list(RATES), 'method_config_sha256': method_sha,
        'diagnostic_folds': 2, 'required_complete_folds': 102, 'pending_folds': 100,
        'maximum_gradient_steps': 5253, 'required_selection_updates': 5253,
        'source_gradient_updates': 100, 'support_gradient_updates': 2, 'actual_gradient_updates': len(events),
        'optimizer_updates': events, 'optimizer_observations': observation_pin,
        'template_state_sha256': template_sha, 'initial_source_state_sha256': initial_sha,
        'independent_initial_state_sha256': independent_sha, 'backbone_state_sha256': backbone_sha,
        'template_parameter_count': 5818138, 'selected_parameter_names': ['head.weight', 'head.bias'],
        'selected_parameter_count': 402, 'selected_tensor_count': 2,
        'full_backbone_blocks': 12, 'full_backbone_embed_dim': 200,
        'model_recipe': prepared.model_recipe, 'model_recipe_sha256': config_digest(prepared.model_recipe),
        'baseline_config': config_pin, 'baseline_weights': weights_pin,
        'baseline_safe_tensor_count': 221, 'baseline_safe_elements': 5819936,
        'baseline_safe_tensor_metadata': safe_tensor_metadata,
        'one_time_setup_seconds': setup_seconds, 'fold_timings_seconds': timings,
        'fold_evidence': fold_pins, 'partial_collection': collection_pin,
        'contract_sha256': config_digest(contract), 'public_complete_selector_verifier_refused': True,
        'public_refusal_reason': PUBLIC_REFUSAL, 'refusal_boundary': 'raw_incomplete_diagnostic_payload_schema',
        'all_physical_inputs_rehashed_unchanged': True, 'supplied_template_unchanged': True,
        'source_backbone_and_buffers_unchanged': True, 'independent_lineage_verified': True,
        'independent_storage_verified': True, 'fixture_source_context_unchanged': True,
        'torch_numpy_python_rng_unchanged': True, 'finite_losses_gradients_parameters': True,
        'canonical_source_exclusion_verified': True, 'actual_public_run_fold': True,
        'pretrained_baseline_loaded': True, 'pretrained_weights_loaded': True,
        'cohort_lineage_verified': False, 'prior_template_training_verified': False,
        'canonical_private_lineage_constructor_exercised': True,
        'public_selected_source_restore_exercised': False, 'full_selection_attempted': False,
        'complete': False, 'selected_candidate': None, 'full_selector_verified': False,
        'full_worker_verified': False, 'publication_performed': False, 'recorder_used': False,
        'measured_cells': 0, 'synthetic': True, 'actual_study_data_loaded': False,
        'engineering_only': True, 'scientific_admission': False, 'original_case_attempts_remaining': 0,
    }
    _write(output / 'probe-result.json', result)
    return result
