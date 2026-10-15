"""Real public diagnostic source folds on separately owned synthetic Cho files.

This module executes run_fold and checks run_selection's pre-fit budget refusal.
It never calls private fitting, target inference, publication, or a recorder.
Its imports and numerical work
belong inside a freshly admitted native child with the caller's audit installed.
"""
from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import random
import sys

METHODS = ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
RATES = (0.001, 0.0005)
SUBJECTS = tuple(f'subject_{number:02d}' for number in range(1, 53))
TRAINING_SUBJECTS = SUBJECTS[2:]
OUTER_TARGET = 'subject_02'
INNER_VALIDATION = 'subject_01'
PUBLIC_REFUSAL = 'selection evidence has missing or unexpected fields'


def run_probe(output: Path, method: str, model_config: dict, *, set_protected_inputs) -> dict:
    """Run one actual 50-source/one-support fold from a two-candidate roster.

The callback enables or disables read denial for all four outer-subject files:
``set_protected_inputs(tuple_of_absolute_paths, enabled: bool)``. The child owns
the denial implementation and independent backward/SGD counters. Input hashes
are checked before enabling and after disabling that explicit source-fold scope.
    """
    def need(condition, message):
        if not condition:
            raise ValueError(message)

    need(type(method) is str and method in METHODS and type(model_config) is dict,
         'one exact method and detached metadata configuration required')
    need(isinstance(output, Path) and output.is_absolute() and output.is_dir()
         and output.resolve(strict=True) == output, 'direct existing owned output required')
    need(callable(set_protected_inputs), 'caller must install outer-target read protection')
    evidence_path = output / 'fold-evidence.json'
    result_path = output / 'probe-result.json'
    need(not evidence_path.exists() and not result_path.exists(), 'unused fold output paths required')

    import numpy as np
    import torch
    from braindecode.models import Labram
    from torch.optim.optimizer import register_optimizer_step_pre_hook, register_optimizer_step_post_hook
    from adaptation.anchor_manifest import EEGNetAnchorSettings
    from adaptation.labram_lora_trained import LoRAContinuationSettings, LoRASourceCandidate, LoRASourceSettings
    from adaptation.labram_manifest import LaBraMTuningSettings
    from adaptation.labram_source import BCILaBraMSourceSelector, LaBraMSourceCandidate, LaBraMSourceSettings
    from adaptation.source_selection import BCIEEGNetSourceSelector, EEGNetCandidate, EEGNetSourceSettings
    from core.config import canonical_config_json, config_digest, config_snapshot
    from core.provenance import source_fingerprint
    from encoder.labram import LaBraMClassifier, configure_pretrained_sequence
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_profile_binding import CHO_CHANNELS
    from evaluation.phase2_protocol import nested_episode, source_selection
    from evaluation.phase2_records import verify_envelope
    from evaluation.phase2_runner import CasePlan
    from evaluation.phase2_selection_evidence_binding import verify_cho_selection_evidence

    need(torch.get_num_threads() == 1 and torch.get_num_interop_threads() == 1,
         'one Torch/intraop thread required')
    need(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'GPU visibility must be empty')
    torch_rng = torch.random.get_rng_state().clone()
    numpy_rng = np.random.get_state()
    python_rng = random.getstate()

    spec = importlib.util.spec_from_file_location(
        '_cho51_source_fold_fixture_v1', Path(__file__).with_name('fixture.py'))
    need(spec is not None and spec.loader is not None, 'pinned adjacent fixture module required')
    fixture_module = importlib.util.module_from_spec(spec)
    need(spec.name not in sys.modules, 'fixture module must be loaded exactly once in fresh child')
    sys.modules[spec.name] = fixture_module
    spec.loader.exec_module(fixture_module)
    fixture = fixture_module.build_fixture(output, method)
    inputs_before = fixture.verify_inputs()
    source_before = source_fingerprint(fixture.root)
    need(tuple(c.subject for c in fixture.catalogs) == SUBJECTS,
         'all 52 physical synthetic Cho catalogs required in canonical order')
    need(len(fixture.input_paths) == 213 and len(fixture.protected_outer_paths) == 4,
         'exact five-config/52x4 physical inventory required')
    need(inputs_before['training_subjects'] == list(TRAINING_SUBJECTS)
         and inputs_before['canonical_shot_levels'] == [1, 5, 10, 20]
         and inputs_before['profile_a_shape'] == [42, 64, 512]
         and inputs_before['profile_b_shape'] == [42, 64, 800],
         'full-shape, complete-cohort fixture identity required')
    selection = source_selection(fixture.catalogs, target=OUTER_TARGET)
    need(selection.source_subjects == ('subject_01', *TRAINING_SUBJECTS)
         and len(selection.inner_folds) == 51, 'unchanged outer-target exclusion required')

    if method == 'eegnet':
        candidates = tuple(EEGNetCandidate(
            f'engineering_rate_{index}', EEGNetSourceSettings(1, 2, rate, 1_000_000.0),
            EEGNetAnchorSettings(1, rate, 1_000_000.0, query_batch_size=2))
            for index, rate in enumerate(RATES, 1))
    elif method == 'labram_lora':
        candidates = tuple(LoRASourceCandidate(
            f'engineering_rate_{index}',
            LoRASourceSettings(('backbone.blocks.11.attn.qkv',), 2, 4.0, 11, True, 1, 2, rate),
            LoRAContinuationSettings(True, 1, rate, query_batch_size=2))
            for index, rate in enumerate(RATES, 1))
    else:
        tuning = method.removeprefix('labram_')
        candidates = tuple(LaBraMSourceCandidate(
            f'engineering_rate_{index}', LaBraMSourceSettings(tuning, 1, 2, rate),
            LaBraMTuningSettings(tuning, 1, rate, query_batch_size=2))
            for index, rate in enumerate(RATES, 1))
    need(len(candidates) == 2, 'two explicit immutable engineering candidates required')
    if method == 'eegnet':
        need(all(candidate.source.input_scale == candidate.support.input_scale == 1_000_000.0
                 for candidate in candidates), 'explicit matched volts-to-microvolts EEGNet scaling required')

    template = None
    template_sha = None
    template_names = None
    template_parameters = None
    if method != 'eegnet':
        expected_keys = {'n_outputs', 'n_chans', 'n_times', 'input_window_seconds', 'sfreq',
                         'chs_info', 'braindecode_version'}
        need(set(model_config) == expected_keys and model_config['n_outputs'] == 0
             and model_config['n_chans'] is None and model_config['n_times'] == 3000
             and model_config['input_window_seconds'] is None and model_config['sfreq'] is None
             and model_config['braindecode_version'] == '1.3.2'
             and type(model_config['chs_info']) is list and len(model_config['chs_info']) == 128
             and all(type(info) is dict and set(info) == {'ch_name'}
                     and type(info['ch_name']) is str for info in model_config['chs_info'])
             and len({info['ch_name'] for info in model_config['chs_info']}) == 128,
             'pinned complete 128-channel/3000-sample baseline metadata required')
        with torch.random.fork_rng(devices=[]):
            torch.random.set_rng_state(torch.Generator(device='cpu').manual_seed(11).get_state())
            config = copy.deepcopy(model_config)
            config.pop('braindecode_version')
            backbone = Labram(**config)
            need(len(backbone.blocks) == 12 and int(backbone.embed_dim) == 200,
                 'full 12-block/embed200 backbone required')
            configure_pretrained_sequence(backbone, samples=800)
            template = LaBraMClassifier(backbone, classes=2, channel_names=CHO_CHANNELS).cpu().float().eval()
            del backbone
        need(all(p.device.type == 'cpu' and p.dtype == torch.float32 for p in template.parameters()),
             'random initialized CPU float32 template required')
        template_sha = state_digest(template)
        template_names = tuple(name for name, _ in template.named_parameters())
        template_parameters = sum(parameter.numel() for parameter in template.parameters())
        need(template_parameters == 5818138, 'complete installed full classifier parameter count required')

    def parameter_digest(parameters):
        digest = hashlib.sha256()
        for index, parameter in enumerate(parameters):
            digest.update(str(index).encode('ascii'))
            digest.update(str(tuple(parameter.shape)).encode('ascii'))
            digest.update(parameter.detach().cpu().contiguous().numpy().tobytes())
        return digest.hexdigest()

    events = []
    pending = {}

    def before_step(optimizer, args, kwargs):
        need(type(optimizer) is torch.optim.SGD, 'only real canonical fresh SGD permitted')
        need(not pending and len(events) < 51, 'strict sequential 51-update bound required')
        parameters = tuple(p for group in optimizer.param_groups for p in group['params'])
        need(bool(parameters) and len({id(p) for p in parameters}) == len(parameters),
             'unique nonempty selected optimizer parameters required')
        need(all(p.requires_grad and p.device.type == 'cpu' and p.dtype == torch.float32
                 and p.grad is not None and torch.isfinite(p.grad).all().item() for p in parameters),
             'finite selected CPU float32 gradients required')
        need(not optimizer.state and all(
            group['lr'] == RATES[0] and group.get('momentum', 0) == 0
            and group.get('weight_decay', 0) == 0 and not group.get('nesterov', False)
            and not group.get('maximize', False) for group in optimizer.param_groups),
            'fixed first-candidate fresh stateless SGD policy required')
        count = sum(parameter.numel() for parameter in parameters)
        expected_count = {'eegnet': 2642, 'labram_linear': 402,
                          'labram_lora': 2002, 'labram_full': 5818138}[method]
        need(count == expected_count, 'actual SGD parameter mask size differs')
        pending.update(optimizer=optimizer, parameters=parameters, before=parameter_digest(parameters),
                       count=count, tensors=len(parameters))

    def after_step(optimizer, args, kwargs):
        need(pending.get('optimizer') is optimizer, 'post-step optimizer identity differs')
        parameters = pending['parameters']
        need(all(torch.isfinite(p).all().item() for p in parameters),
             'nonfinite selected parameter after actual SGD')
        after = parameter_digest(parameters)
        need(after != pending['before'], 'actual SGD update must change selected parameter bytes')
        events.append({'update': len(events) + 1,
                       'role': 'source' if len(events) < 50 else 'inner_validation_support',
                       'selected_parameters': pending['count'], 'selected_tensors': pending['tensors'],
                       'selected_state_sha256_before': pending['before'],
                       'selected_state_sha256_after': after,
                       'finite_selected_gradients': True, 'finite_selected_parameters': True})
        pending.clear()

    protected = False
    pre_hook = None
    post_hook = None
    try:
        set_protected_inputs(fixture.protected_outer_paths, True)
        protected = True
        if method == 'eegnet':
            selector = BCIEEGNetSourceSelector(
                fixture.root, fixture.protocol, fixture.catalogs, fixture.selection_record, {},
                outer_target=OUTER_TARGET, candidates=candidates, seed=11,
                shots_per_class=5, maximum_gradient_steps=51)
        else:
            selector = BCILaBraMSourceSelector(
                fixture.root, fixture.protocol, fixture.catalogs, fixture.selection_record,
                template, fixture.assets, outer_target=OUTER_TARGET,
                template_state_sha256=template_sha, candidates=candidates, seed=11,
                shots_per_class=5, maximum_gradient_steps=51,
                source_device='cpu', checkpoint_directory=None, operator_compute_admitted=False)
        contract_before = selector.contract
        pre_hook = register_optimizer_step_pre_hook(before_step)
        post_hook = register_optimizer_step_post_hook(after_step)
        required_complete_updates = sum(
            len(selection.source_subjects)
            * ((len(selection.source_subjects) - 1) * candidate.source.steps_per_subject
               + candidate.support.steps)
            for candidate in candidates
        ) + len(selection.source_subjects) * max(candidate.source.steps_per_subject for candidate in candidates)
        need(required_complete_updates == 5253, 'unchanged complete-selector work must remain 5253 updates')
        selection_refusal = None
        try:
            selector.run_selection()
        except ValueError as error:
            selection_refusal = str(error)
        need(selection_refusal == 'requested work exceeds the declared gradient-step ceiling'
             and not events and not pending,
             'public complete selection must refuse its 5253 updates before any optimizer step')
        evidence = selector.run_fold(candidate_name=candidates[0].name,
                                     validation_subject=INNER_VALIDATION)
        need(not pending and len(events) == 51, 'exactly 50 source and one support SGD updates required')
        need(selector.contract == contract_before, 'public selector context changed during fold')
        if template is not None:
            need(state_digest(template) == template_sha and all(p.grad is None for p in template.parameters()),
                 'public selector mutated supplied immutable source template')
        record = evidence.record
    finally:
        if pre_hook is not None:
            pre_hook.remove()
        if post_hook is not None:
            post_hook.remove()
        if protected:
            set_protected_inputs(fixture.protected_outer_paths, False)

    need(fixture.verify_inputs() == inputs_before, 'all physical fixture inputs must remain byte exact')
    need(source_fingerprint(fixture.root) == source_before, 'fixture source/config fingerprint changed')
    need(torch.equal(torch.random.get_rng_state(), torch_rng), 'public fold changed global Torch CPU RNG')
    numpy_after = np.random.get_state()
    need(numpy_after[0] == numpy_rng[0] and np.array_equal(numpy_after[1], numpy_rng[1])
         and numpy_after[2:] == numpy_rng[2:], 'public fold changed global NumPy RNG')
    need(random.getstate() == python_rng, 'public fold changed global Python RNG')
    payload = record['payload']
    need(verify_envelope(record, kind='engineering_smoke', expected_payload=payload),
         'actual public fold engineering envelope differs')
    need(set(payload) == {'purpose', 'contract', 'contract_sha256', 'complete', 'folds', 'selected_candidate'}
         and payload['complete'] is False and payload['selected_candidate'] is None
         and type(payload['folds']) is list and len(payload['folds']) == 1,
         'one raw explicitly incomplete diagnostic and no selected winner required')
    contract = payload['contract']
    need(contract == contract_before and payload['contract_sha256'] == config_digest(contract)
         and contract['method'] == method and contract['dataset'] == 'cho2017'
         and contract['selection'] == config_snapshot(asdict(selection))
         and contract['protocol_sha256'] == config_digest(fixture.protocol)
         and contract['shots_per_class'] == 5 and contract['maximum_gradient_steps'] == 51
         and contract['engineering_only'] is True and contract['scientific_evaluation'] is False
         and contract['early_stopping'] is False and contract['runtime']['device'] == 'cpu'
         and (method == 'eegnet' or contract['runtime']['dtype'] == 'float32')
         and contract['runtime']['torch_threads'] == 1
         and contract['source']['source_sha256'] == source_before
         and 'source_execution' not in contract,
         'actual public source/config/runtime engineering contract differs')
    fold = payload['folds'][0]
    fit = fold['source_fit']
    need(fold['candidate'] == candidates[0].name and fold['validation_subject'] == INNER_VALIDATION
         and fit['candidate'] == candidates[0].name and fit['validation_subject'] == INNER_VALIDATION
         and fit['training_subjects'] == list(TRAINING_SUBJECTS)
         and set(fit['input_identities']) == set(TRAINING_SUBJECTS)
         and len(fit['steps']) == 50 and fit['engineering_only'] is True,
         'exact sequential 50-source fit and held-out validation required')
    prior_sha = fit['initial_state_sha256']
    catalog_by_subject = {catalog.subject: catalog for catalog in fixture.catalogs}
    for number, (subject, step) in enumerate(zip(TRAINING_SUBJECTS, fit['steps'], strict=True), 1):
        need(step['step'] == number and step['subject'] == subject and step['subject_step'] == 1
             and step['iterator_wraps'] == 0 and len(step['trial_ids']) == 2
             and len(set(step['trial_ids'])) == 2
             and set(step['trial_ids']) <= set(catalog_by_subject[subject].trial_ids)
             and type(step['loss']) in (int, float) and math.isfinite(step['loss'])
             and step['state_sha256_after'] != prior_sha,
             'source history must certify one real finite two-trial update per permitted subject')
        prior_sha = step['state_sha256_after']
    need(prior_sha == fit['fitted_state_sha256']
         and fit['fitted_state_sha256'] != fit['initial_state_sha256']
         and fold['adapted_state_sha256'] != fit['fitted_state_sha256'],
         'actual source and support states must change under the recorded updates')
    episode = nested_episode(catalog_by_subject[INNER_VALIDATION], shots=(1, 5, 10, 20),
                             protocol_sha256=config_digest(fixture.protocol))
    partition = episode.partition(5)
    support_ids = [episode.catalog.trial_ids[index] for index in partition.support_indices]
    query_ids = [episode.catalog.trial_ids[index] for index in partition.query_indices]
    need(len(support_ids) == 10 and len(query_ids) == 2 and not set(support_ids) & set(query_ids),
         'fixed maximum-pool withheld two-query/five-shot partition required')
    if method == 'eegnet':
        losses = fold['support_fit']['support_losses']
        selected_names = fold['support_fit']['trainable_names']
        need(fold['support_trial_ids'] == support_ids and fold['query_trial_ids'] == query_ids
             and set(fold['input_identities']) == {INNER_VALIDATION}
             and fold['support_fit']['source_fit_performed'] is False
             and fold['support_fit']['trainable_parameters'] == 2642,
             'actual EEGNet support/query binding differs')
    else:
        losses = fold['support_losses']
        selected_names = fold['support_mask']['trainable_names']
        need(fold['binding']['subject'] == INNER_VALIDATION
             and fold['binding']['support_trial_ids'] == support_ids
             and fold['binding']['query_trial_ids'] == query_ids
             and fit['mask']['trainable_names'] == selected_names,
             'actual LaBraM support/query binding or selected masks differ')
        if method == 'labram_linear':
            expected_names = {name for name in template_names if name.startswith('head.')}
        elif method == 'labram_full':
            expected_names = set(template_names)
        else:
            expected_names = {'head.weight', 'head.bias',
                'backbone.blocks.11.attn.qkv.parametrizations.weight.0.lora_a',
                'backbone.blocks.11.attn.qkv.parametrizations.weight.0.lora_b'}
            need(fold['component_policy'] == 'continue_source_trained_lora_without_reinitialization'
                 and fold['support_source_state_sha256'] == fit['fitted_state_sha256'],
                 'support must continue the actual learned source LoRA state')
        need(set(selected_names) == expected_names, 'full architecture method mask differs')
    need(len(losses) == 1 and all(type(loss) in (int, float) and math.isfinite(loss) for loss in losses),
         'one actual finite support update required')
    confusion = fold['confusion_matrix']
    need(type(confusion) is list and len(confusion) == 2
         and all(type(row) is list and len(row) == 2 and sum(row) == 1
                 and all(type(value) is int and value >= 0 for value in row) for row in confusion),
         'two fixed inner-validation query predictions required')
    from fractions import Fraction
    score = (Fraction(confusion[0][0], sum(confusion[0]))
             + Fraction(confusion[1][1], sum(confusion[1]))) / 2
    need(fold['balanced_accuracy'] == [score.numerator, score.denominator],
         'actual inner-validation exact rational score differs')

    # Preserve the real raw diagnostic. It intentionally lacks complete-selector
    # fields; do not manufacture them merely to enter a later refusal branch.
    evidence.write(evidence_path, output_root=output)
    evidence_raw = (canonical_config_json(record) + '\n').encode('utf-8')
    need(evidence_path.read_bytes() == evidence_raw, 'persisted raw diagnostic bytes differ')
    plan = CasePlan('cho2017', OUTER_TARGET, method, 5, 11, 1)
    refusal = None
    try:
        verify_cho_selection_evidence(
            record=record, evidence_sha256=record['sha256'], plan=plan,
            protocol_config=fixture.protocol, catalogs=fixture.catalogs,
            selection_record=fixture.selection_record,
            assets={} if method == 'eegnet' else fixture.assets, root=fixture.root,
            adapter_model_state_sha256=fit['fitted_state_sha256'],
            adapter_source_settings=contract['candidates'][0]['source'],
            adapter_support_settings=contract['candidates'][0]['support'])
    except ValueError as error:
        refusal = str(error)
    need(refusal == PUBLIC_REFUSAL, 'raw diagnostic must fail the actual public complete-selector verifier')
    need(fixture.verify_inputs() == inputs_before and source_fingerprint(fixture.root) == source_before,
         'public refusal changed synthetic source inputs/context')
    result = {
        'schema': 'cho51_public_source_fold_probe_v1', 'passed': True,
        'method': method, 'case': asdict(plan), 'case_id': plan.case_id,
        'fixture_root': str(fixture.root), 'input_identity_path': str(fixture.identity_path),
        'input_identity_sha256': inputs_before['sha256'],
        'input_identity_file_sha256': fixture.identity_file_sha256,
        'input_file_count': len(fixture.input_paths), 'input_files': inputs_before['files'],
        'physical_inputs': fixture.physical_inputs,
        'protected_outer_paths': [str(path) for path in fixture.protected_outer_paths],
        'fixture_source_sha256': source_before,
        'source_subjects_available': 52, 'adopted_evaluation_targets': 51,
        'adopted_case_plan_count': 1020, 'outer_target': OUTER_TARGET,
        'inner_validation_subject': INNER_VALIDATION,
        'training_subjects': list(TRAINING_SUBJECTS),
        'declared_candidates': list(contract['candidates']), 'executed_candidate': candidates[0].name,
        'candidate_rates': list(RATES), 'diagnostic_folds': 1,
        'maximum_gradient_steps': 51, 'source_gradient_updates': 50,
        'full_selection_refused_before_fit': True,
        'required_selection_updates': required_complete_updates,
        'full_selection_refusal_reason': selection_refusal,
        'support_gradient_updates': 1, 'actual_gradient_updates': len(events),
        'optimizer_updates': events, 'selected_parameter_names': list(selected_names),
        'initial_source_state_sha256': fit['initial_state_sha256'],
        'fitted_source_state_sha256': fit['fitted_state_sha256'],
        'adapted_state_sha256': fold['adapted_state_sha256'],
        'template_state_sha256': template_sha, 'template_parameter_count': template_parameters,
        'full_backbone_blocks': 12 if method != 'eegnet' else None,
        'full_backbone_embed_dim': 200 if method != 'eegnet' else None,
        'support_trials': 10, 'inner_query_trials': 2,
        'source_losses': [step['loss'] for step in fit['steps']], 'support_losses': list(losses),
        'confusion_matrix': confusion, 'balanced_accuracy': fold['balanced_accuracy'],
        'fold_evidence_path': str(evidence_path), 'fold_evidence_sha256': record['sha256'],
        'fold_evidence_file_sha256': hashlib.sha256(evidence_raw).hexdigest(),
        'fold_evidence_file_bytes': len(evidence_raw),
        'contract_sha256': payload['contract_sha256'],
        'public_complete_selector_verifier_refused': True, 'public_refusal_reason': refusal,
        'refusal_boundary': 'raw_incomplete_diagnostic_payload_schema',
        'all_physical_inputs_rehashed_unchanged': True,
        'supplied_template_unchanged': True, 'fixture_source_context_unchanged': True,
        'torch_numpy_python_rng_unchanged': True,
        'finite_losses_gradients_parameters': True, 'canonical_source_exclusion_verified': True,
        'actual_public_run_fold': True, 'complete': False, 'selected_candidate': None,
        'full_selector_verified': False, 'full_worker_verified': False,
        'publication_performed': False, 'recorder_used': False, 'measured_cells': 0,
        'synthetic': True, 'actual_study_data_loaded': False, 'pretrained_weights_loaded': False,
        'engineering_only': True, 'scientific_admission': False,
        'original_case_attempts_remaining': 0,
    }
    with result_path.open('xb') as stream:
        stream.write((canonical_config_json(result) + '\n').encode('utf-8'))
        stream.flush()
        os.fsync(stream.fileno())
    return result
