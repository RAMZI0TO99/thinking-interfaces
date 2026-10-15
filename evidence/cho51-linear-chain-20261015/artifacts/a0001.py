"""Bounded public-fold fragments and a separately authenticated fresh final fit.

Import and execute project/model code only inside a newly admitted native Job.
All historical fixture inputs and accepted records are read-only dependencies.
"""
from __future__ import annotations

import copy
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import random
from time import perf_counter

ROOT = Path(__file__).resolve().parents[3]
SUBJECTS = tuple(f'subject_{number:02d}' for number in range(1, 53))
SOURCES = tuple(subject for subject in SUBJECTS if subject != 'subject_02')
INITIAL = '90a9d34ecba2aa96a942f7bd70724f63c2071042141935dbbcd78e0b373b89a7'
CONTRACT = '8397d34ee0a2280b406071e045988f98b1b73ce21fcecc0b9834518cd21993b1'
PUBLIC_REFUSAL = 'selection evidence has missing or unexpected fields'
FINAL_REFUSAL = 'all 102 distinct canonical folds are required before a fresh final source fit'
MAXIMUM_STATE_BYTES = 64 * 1024**2
MAXIMUM_EVIDENCE_BYTES = 32 * 1024**2


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _json(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(',', ':'))


def _physical_json(value):
    return hashlib.sha256((_json(value) + '\n').encode('utf-8')).hexdigest()


def _pin(path, raw, **fields):
    return {'path': str(path), 'file_sha256': hashlib.sha256(raw).hexdigest(),
            'size_bytes': len(raw), **fields}


def _state_digest(tensors):
    digest = hashlib.sha256()
    for name, value in sorted(tensors.items()):
        digest.update(name.encode())
        digest.update(str((tuple(value.shape), value.dtype)).encode())
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _save_selected(output, model, checkpoint_control, *, selected_model_recipe_sha256):
    """Store one complete owned safe checkpoint, then verify its exact round trip."""
    import torch
    from safetensors.torch import load, save
    from docs.phase2.cho51_linear_lineage_v1 import probe as P
    from evaluation.labram_parity import state_digest

    _need(callable(checkpoint_control), 'native checkpoint-byte authorization callback required')
    before = state_digest(model)
    tensors = {name: value.detach().cpu().contiguous().clone()
               for name, value in sorted(model.state_dict().items())}
    _need(len(tensors) == 223 and sum(value.numel() for value in tensors.values()) == 5818138
          and all(value.device.type == 'cpu' and value.dtype == torch.float32
                  and torch.isfinite(value).all().item() for value in tensors.values())
          and _state_digest(tensors) == before == state_digest(model),
          'complete finite stable223-tensor CPU float32 fitted state required')
    schema = {name: {'shape': list(value.shape), 'dtype': str(value.dtype),
                     'elements': value.numel()} for name, value in tensors.items()}
    raw = save(tensors)
    _need(type(raw) is bytes and 0 < len(raw) <= MAXIMUM_STATE_BYTES,
          'complete safe checkpoint exceeds the independent64MiB bound')
    path = output / 'selected-source.safetensors'
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    sha256 = hashlib.sha256(raw).hexdigest()
    checkpoint_control({'path': str(path), 'sha256': sha256, 'size_bytes': len(raw)})
    persisted, physical = P._read_baseline(path, maximum_bytes=MAXIMUM_STATE_BYTES,
        expected_bytes=len(raw), expected_sha256=sha256)
    _need(persisted == raw, 'persisted full-state bytes differ before safe round trip')
    decoded = load(persisted)
    _need(set(decoded) == set(tensors) and all(
        decoded[name].device.type == 'cpu' and decoded[name].dtype == value.dtype
        and decoded[name].shape == value.shape and torch.isfinite(decoded[name]).all().item()
        and torch.equal(decoded[name], value) for name, value in tensors.items())
        and _state_digest(decoded) == before == state_digest(model),
        'complete safe tensor round trip differs from the actual fitted state')
    schema_pin = P._write(output / 'selected-state-schema.json', {
        'schema': 'cho51_linear_chain_full_state_schema_v1', 'model_state_sha256': before,
        'selected_model_recipe_sha256': selected_model_recipe_sha256,
        'weights_sha256': sha256, 'weights_bytes': len(raw), 'tensor_count': 223,
        'elements': 5818138, 'tensors': schema, 'roundtrip_verified': True,
        'all_finite_cpu_float32': True, 'published': False})
    return {**physical, 'weights_sha256': sha256, 'weights_format': 'full_v1',
            'model_state_sha256': before, 'tensor_count': 223, 'elements': 5818138,
            'selected_model_recipe_sha256': selected_model_recipe_sha256,
            'schema_pin': schema_pin, 'roundtrip_verified': True, 'published': False}


def _validate_fold(record, candidate, validation, fixture, contract):
    """Independently check the genuine raw public history without reading arrays."""
    from core.config import config_digest, config_snapshot
    from evaluation.phase2_protocol import nested_episode
    from evaluation.phase2_records import verify_envelope

    payload = record['payload']
    _need(verify_envelope(record, kind='engineering_smoke', expected_payload=payload)
          and set(payload) == {'purpose', 'contract', 'contract_sha256', 'complete', 'folds', 'selected_candidate'}
          and payload['contract'] == contract and payload['contract_sha256'] == CONTRACT
          and payload['complete'] is False and payload['selected_candidate'] is None
          and len(payload['folds']) == 1, 'actual unchanged incomplete public envelope required')
    fold, training = payload['folds'][0], tuple(subject for subject in SOURCES if subject != validation)
    fit = fold['source_fit']
    _need(fold['candidate'] == candidate.name and fold['validation_subject'] == validation
          and fit['candidate'] == candidate.name and fit['validation_subject'] == validation
          and fit['training_subjects'] == list(training) and len(training) == 50
          and 'subject_02' not in training and validation not in training
          and set(fit['input_identities']) == set(training)
          and fit['settings'] == config_snapshot(asdict(candidate.source))
          and fit['initial_state_sha256'] == INITIAL and len(fit['steps']) == 50
          and fit['mask']['trainable_names'] == fold['support_mask']['trainable_names'] == ['head.weight', 'head.bias']
          and fit['mask']['trainable_parameters'] == fold['support_mask']['trainable_parameters'] == 402,
          'current held-out subject, sources, initial state, settings or head mask differ')
    catalogs, previous = {catalog.subject: catalog for catalog in fixture.catalogs}, INITIAL
    for number, (subject, step) in enumerate(zip(training, fit['steps'], strict=True), 1):
        _need(step['step'] == number and step['subject'] == subject and step['subject_step'] == 1
              and step['iterator_wraps'] == 0 and len(step['trial_ids']) == len(set(step['trial_ids'])) == 2
              and set(step['trial_ids']) <= set(catalogs[subject].trial_ids)
              and type(step['loss']) in (int, float) and math.isfinite(step['loss'])
              and step['state_sha256_after'] != previous, 'finite actual50-source SGD history differs')
        previous = step['state_sha256_after']
    episode = nested_episode(catalogs[validation], shots=(1, 5, 10, 20),
                             protocol_sha256=config_digest(fixture.protocol))
    partition = episode.partition(5)
    support = [episode.catalog.trial_ids[i] for i in partition.support_indices]
    query = [episode.catalog.trial_ids[i] for i in partition.query_indices]
    losses, confusion = fold['support_losses'], fold['confusion_matrix']
    _need(previous == fit['fitted_state_sha256'] and previous != INITIAL
          and fold['adapted_state_sha256'] != previous and fold['binding']['subject'] == validation
          and fold['binding']['support_trial_ids'] == support and fold['binding']['query_trial_ids'] == query
          and len(support) == 10 and len(query) == 2 and not set(support) & set(query)
          and len(losses) == 1 and all(type(v) in (int, float) and math.isfinite(v) for v in losses),
          'actual finite support/query continuation differs')
    _need(type(confusion) is list and len(confusion) == 2
          and all(type(row) is list and len(row) == 2 and sum(row) == 1
                  and all(type(v) is int and v >= 0 for v in row) for row in confusion),
          'exactly one withheld inner query per class required')
    score = sum((Fraction(confusion[i][i], sum(confusion[i])) for i in range(2)), Fraction()) / 2
    _need(fold['balanced_accuracy'] == [score.numerator, score.denominator], 'exact rational score differs')
    return fold


def run_probe(output: Path, method_config: dict, *, request: dict, origin: dict,
              chain: dict, set_protected_inputs, checkpoint_control=None) -> dict:
    """Execute exactly one externally pinned fold fragment or fresh-final request."""
    _need(isinstance(output, Path) and output.is_absolute() and output.is_dir()
          and output.resolve(strict=True) == output and type(method_config) is dict
          and type(request) is dict and type(origin) is dict and type(chain) is dict
          and callable(set_protected_inputs), 'exact detached request, native origins and owned output required')

    import numpy as np
    import torch
    from braindecode.models import Labram
    from safetensors.torch import load
    from torch.nn.modules.module import register_module_forward_pre_hook
    from torch.optim.optimizer import register_optimizer_step_pre_hook, register_optimizer_step_post_hook
    from adaptation.labram_manifest import LaBraMTuningSettings
    from adaptation.labram_source import LaBraMSourceCandidate, LaBraMSourceSettings
    from core.config import canonical_config_json, config_digest
    from core.provenance import source_fingerprint
    from docs.phase2.cho51_linear_lineage_v1 import probe as B
    from docs.phase2.cho51_linear_continuation_v1 import probe as P
    from docs.phase2.cho51_linear_continuation_v1.contract import collect_partial
    from docs.phase2.cho51_linear_chain_v1.selector import StagedLinearSourceSelector
    from docs.phase2.cho51_linear_chain_v1.origin import verify_chain, complete_origin_callback
    from docs.phase2.cho51_linear_chain_v1.plan import validate_request, budget
    from encoder.labram import LaBraMClassifier, configure_pretrained_sequence
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_source_restore import prepare_cho_source_restore, _new_model
    from evaluation.phase2_profile_binding import CHO_CHANNELS
    from evaluation.phase2_runner import CasePlan, method_configuration
    from evaluation.phase2_selection_evidence_binding import verify_cho_selection_evidence

    request, origin, chain = json.loads(_json(request)), json.loads(_json(origin)), json.loads(_json(chain))
    validate_request(request, chain, pins_sha256=request['pins_sha256'],
                     root_origin_sha256=request['root_origin_sha256'])
    limits, mode = budget(request), request['mode']
    pairs = [(row['candidate'], row['validation_subject']) for row in request['pairs']]
    _need(mode in ('folds', 'final') and ((mode == 'folds' and 1 <= len(pairs) <= 16)
          or (mode == 'final' and not pairs and callable(checkpoint_control))), 'one exact bounded fragment mode required')
    expected_output = ROOT / 'runs/coordination/cho51_linear_chain_20261015_v1' / request['output_relative']
    _need(output == expected_output, 'request output and owned fragment namespace differ')
    names = ['probe-result.json', 'partial-collection.json', 'optimizer-observations.json',
             'finalization-refusals.json', 'selection-evidence.json', 'selected-source.safetensors',
             'selected-state-schema.json', *(f'fold_{i:02d}.json' for i in range(1, len(pairs) + 1))]
    _need(all(not (output / name).exists() for name in names), 'all request artifact paths must be unused')
    _need(torch.get_num_threads() == torch.get_num_interop_threads() == 1
          and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'one-thread hidden-GPU child required')
    rng = torch.random.get_rng_state().clone(), np.random.get_state(), random.getstate()
    history = verify_chain(origin, chain, ROOT, pins_sha256=request['pins_sha256'])
    historical = json.loads(_json(history.records))
    _need(len(historical) == request['prior_folds']
          and history.head_sha256 == request['parent_head_sha256'], 'request history coverage or head differs')
    fixture = P._existing_fixture(origin['fixture_origin'])
    inputs_before, source_before = fixture.verify_inputs(), source_fingerprint(fixture.root)
    _need(inputs_before['sha256'] == origin['fixture_origin']['input_identity_sha256']
          and historical and historical[0]['payload']['contract_sha256'] == CONTRACT
          and historical[0]['payload']['contract']['template_state_sha256'] == INITIAL
          and historical[0]['payload']['contract']['initial_state_sha256'] == INITIAL,
          'exact authenticated input, contract and baseline lineage required')
    expected_method = {
        'dataset': 'cho2017', 'method': 'labram_linear', 'input_profile': 'cho_profile_b_60hz_v1',
        'variant_config_sha256': fixture.assets['subject_01'].variant_config_sha256,
        'source_seed_policy': 'none',
        'source_policy': 'all_non_target_subjects; inner_validation_also_excluded',
        'score': 'mean_subject_balanced_accuracy_exact_rational',
        'tie_break': 'first_in_declared_candidate_order', 'early_stopping': False,
        'candidates': [{'name': name,
            'source': {'method': 'linear', 'steps_per_subject': 1, 'batch_size': 2,
                       'learning_rate': rate, 'partial_depth': None},
            'support': {'method': 'linear', 'steps': 1, 'learning_rate': rate,
                        'partial_depth': None, 'query_batch_size': 8}}
            for name, rate in (('lr_1e-3', 0.001), ('lr_2e-3', 0.002))],
    }
    _need(method_config == expected_method, 'unchanged adopted linear method declaration required')
    candidates = tuple(LaBraMSourceCandidate(row['name'], LaBraMSourceSettings(**row['source']),
        LaBraMTuningSettings(**row['support'])) for row in method_config['candidates'])
    plan = CasePlan('cho2017', 'subject_02', 'labram_linear', 5, 11, 1)
    events, current, pending, active, handles = [], {}, {}, {}, []
    records, fold_pins, timings, refusals = [], [], [], []
    checkpoint = selected_evidence = verified_selection = None
    selected_recipe = selected_recipe_sha = None
    winner_name, final_seconds = None, None
    protected, selector = False, None

    def selected_digest(parameters):
        return _state_digest({str(i): value for i, value in enumerate(parameters)})

    def check_frozen(model):
        _need(tuple(name for name, p in model.named_parameters() if p.requires_grad)
              == ('head.weight', 'head.bias')
              and sum(p.numel() for p in model.parameters() if p.requires_grad) == 402
              and all(p.grad is None for name, p in model.named_parameters() if name.startswith('backbone.'))
              and state_digest(model.backbone) == backbone_sha, 'frozen backbone/buffers or exact402-head mask changed')

    def before_forward(module, args):
        if isinstance(module, LaBraMClassifier):
            check_frozen(module)
            active['model'] = module

    def before_step(optimizer, args, kwargs):
        _need(type(optimizer) is torch.optim.SGD and not pending
              and len(events) < limits['gradient_updates'], 'actual sequential exact-request SGD required')
        parameters = tuple(p for group in optimizer.param_groups for p in group['params'])
        model = active.get('model')
        _need(model is not None and tuple(id(p) for p in parameters)
              == tuple(id(p) for p in model.head.parameters())
              and len(parameters) == 2 and sum(p.numel() for p in parameters) == 402,
              'optimizer must select only the active classifier head')
        check_frozen(model)
        _need(all(p.device.type == 'cpu' and p.dtype == torch.float32 and p.requires_grad
                  and p.grad is not None and torch.isfinite(p.grad).all().item()
                  and torch.isfinite(p).all().item() for p in parameters)
              and not optimizer.state and all(group['lr'] == current['rate']
                  and group.get('momentum', 0) == 0 and group.get('weight_decay', 0) == 0
                  and not group.get('nesterov', False) and not group.get('maximize', False)
                  for group in optimizer.param_groups), 'finite head gradients and adopted stateless SGD required')
        pending.update(optimizer=optimizer, model=model, parameters=parameters,
                       before=selected_digest(parameters))

    def after_step(optimizer, args, kwargs):
        _need(pending.get('optimizer') is optimizer, 'optimizer post-step identity differs')
        check_frozen(pending['model'])
        after = selected_digest(pending['parameters'])
        _need(after != pending['before'] and all(torch.isfinite(p).all().item() for p in pending['parameters']),
              'actual finite head SGD must change selected bytes')
        index = len(events) - current['offset']
        source = index < len(current['training'])
        _need(0 <= index < len(current['training']) + (0 if current['final'] else 1),
              'request per-fit gradient bound differs')
        events.append({'update': len(events) + 1, 'fold_update': index + 1,
            'candidate': current['name'], 'validation_subject': current['validation'],
            'role': 'final_source' if current['final'] else 'source' if source else 'inner_validation_support',
            'subject': current['training'][index] if source else current['validation'],
            'learning_rate': current['rate'], 'selected_parameters': 402, 'selected_tensors': 2,
            'selected_state_sha256_before': pending['before'], 'selected_state_sha256_after': after,
            'finite_selected_gradients': True, 'finite_selected_parameters': True,
            'frozen_backbone_and_buffers_unchanged': True})
        pending.clear()

    def no_complete_origins(records, metadata):
        raise AssertionError('an incomplete roster must refuse before its complete-origin capability')

    def refuse_incomplete(raw_records, stage):
        _need(len(raw_records) < 102, 'do not manufacture an incomplete refusal for a complete roster')
        count, reason = len(events), None
        try:
            selector.complete_final_fit(raw_records, method_config,
                input_identity_sha256=inputs_before['sha256'], template_state_sha256=INITIAL,
                initial_state_sha256=INITIAL, lineage_recipe_sha256=recipe_sha,
                verify_origins=no_complete_origins)
        except ValueError as error:
            reason = str(error)
        _need(reason == FINAL_REFUSAL and len(events) == count and not pending
              and state_digest(selector._initial) == INITIAL, 'incomplete finalization must refuse before fitting')
        refusals.append({'stage': stage, 'records': len(raw_records), 'reason': reason,
            'observed_updates_before': count, 'observed_updates_after': len(events),
            'before_fit': True, 'origin_capability_called': False})

    try:
        set_protected_inputs(fixture.protected_outer_paths, True)
        protected = True
        setup_started = perf_counter()
        prepared = prepare_cho_source_restore(root=ROOT, plan=plan, method_config=method_config,
            expected_method_config_sha256=method_configuration(method_config), selected_candidate='lr_1e-3')
        recipe_sha = config_digest(prepared.model_recipe)
        _need(prepared.model_config_path == ROOT / B.BASELINE_DIRECTORY / 'config.json'
              and prepared.baseline_weights_path == ROOT / B.BASELINE_DIRECTORY / 'model.safetensors'
              and recipe_sha == origin['lineage_recipe_sha256'], 'exact authenticated baseline recipe required')
        config_raw, config_pin = B._read_baseline(prepared.model_config_path,
            maximum_bytes=1024**2, expected_bytes=4776, expected_sha256=B.BASELINE_CONFIG_SHA256)
        raw, weights_pin = B._read_baseline(prepared.baseline_weights_path,
            maximum_bytes=32 * 1024**2, expected_bytes=23299672, expected_sha256=B.BASELINE_WEIGHTS_SHA256)
        settings, safe_state = json.loads(config_raw), load(raw)
        _need(settings.get('n_times') == 3000 and settings.get('n_outputs') == 0
              and settings.get('braindecode_version') == '1.3.2'
              and type(safe_state) is dict and len(safe_state) == 221
              and sum(t.numel() for t in safe_state.values()) == 5819936
              and all(t.device.type == 'cpu' and t.dtype == torch.float32 and torch.isfinite(t).all().item()
                      for t in safe_state.values()), 'audited finite221-tensor baseline required')
        with torch.random.fork_rng(devices=[]):
            model_settings = copy.deepcopy(settings)
            model_settings.pop('braindecode_version')
            backbone = Labram(**model_settings)
            backbone.load_state_dict(safe_state, strict=True)
            del safe_state, raw
            configure_pretrained_sequence(backbone, samples=800)
            torch.random.set_rng_state(torch.Generator(device='cpu').manual_seed(11).get_state())
            template = LaBraMClassifier(backbone, classes=2, channel_names=CHO_CHANNELS).cpu().float().eval()
            del backbone
        _need(len(template.backbone.blocks) == 12 and int(template.backbone.embed_dim) == 200
              and sum(p.numel() for p in template.parameters()) == 5818138
              and state_digest(template) == INITIAL, 'exact full pretrained classifier lineage required')
        backbone_sha = state_digest(template.backbone)
        selector = StagedLinearSourceSelector(fixture.root, fixture.protocol, fixture.catalogs,
            fixture.selection_record, template, fixture.assets, outer_target='subject_02',
            template_state_sha256=INITIAL, candidates=candidates, seed=11, shots_per_class=5,
            maximum_gradient_steps=5253, source_device='cpu', checkpoint_directory=None,
            operator_compute_admitted=False)
        contract = selector.contract
        _need(state_digest(selector._initial) == INITIAL and selector.admit_complete_scope() == CONTRACT
              and all(record['payload']['contract'] == contract for record in historical),
              'fresh fragment must reproduce the entire accepted selector contract')
        check_frozen(selector._initial)
        reconstructed = _new_model(prepared, contract=contract)
        check_frozen(reconstructed)
        models = template, selector._initial, reconstructed
        storages = [{v.untyped_storage().data_ptr() for v in model.state_dict().values() if v.numel()}
                    for model in models]
        _need(state_digest(reconstructed) == INITIAL
              and all(not storages[a] & storages[b] for a in range(3) for b in range(a + 1, 3)),
              'independent canonical lineage must agree without shared storage')
        del models, storages, reconstructed
        setup_seconds = perf_counter() - setup_started
        if mode == 'folds':
            refuse_incomplete(historical, 'before_current_fragment')
        handles.append(register_module_forward_pre_hook(before_forward))
        handles.append(register_optimizer_step_pre_hook(before_step))
        handles.append(register_optimizer_step_post_hook(after_step))
        if mode == 'folds':
            for number, (name, validation) in enumerate(pairs, 1):
                candidate = next(candidate for candidate in candidates if candidate.name == name)
                current.update(name=name, validation=validation, final=False,
                    training=tuple(subject for subject in SOURCES if subject != validation),
                    rate=candidate.source.learning_rate, offset=len(events))
                active.clear()
                started = perf_counter()
                evidence = selector.run_fold(candidate_name=name, validation_subject=validation)
                timings.append(perf_counter() - started)
                _need(not pending and len(events) == number * 51 and selector.contract == contract
                      and state_digest(selector._initial) == state_digest(template) == INITIAL
                      and all(p.grad is None for p in template.parameters()),
                      'current public fold must perform exactly51 updates and preserve initialization')
                check_frozen(selector._initial)
                record = evidence.record
                fold = _validate_fold(record, candidate, validation, fixture, contract)
                path = output / f'fold_{number:02d}.json'
                evidence.write(path, output_root=output)
                raw = (canonical_config_json(record) + '\n').encode('utf-8')
                _need(path.read_bytes() == raw, 'persisted genuine raw fold bytes differ')
                reason, candidate_row = None, next(row for row in contract['candidates'] if row['name'] == name)
                try:
                    verify_cho_selection_evidence(record=record, evidence_sha256=record['sha256'], plan=plan,
                        protocol_config=fixture.protocol, catalogs=fixture.catalogs,
                        selection_record=fixture.selection_record, assets=fixture.assets, root=fixture.root,
                        adapter_model_state_sha256=fold['source_fit']['fitted_state_sha256'],
                        adapter_source_settings=candidate_row['source'], adapter_support_settings=candidate_row['support'])
                except ValueError as error:
                    reason = str(error)
                _need(reason == PUBLIC_REFUSAL, 'genuine raw partial fold must fail the complete-selector schema')
                fold_pins.append(_pin(path, raw, candidate=name, validation_subject=validation,
                    evidence_sha256=record['sha256'], elapsed_seconds=timings[-1], public_refusal_reason=reason,
                    fitted_state_sha256=fold['source_fit']['fitted_state_sha256'],
                    adapted_state_sha256=fold['adapted_state_sha256'], balanced_accuracy=fold['balanced_accuracy']))
                records.append(record)
                active.clear()
            combined = [*historical, *records]
            if len(combined) < 102:
                refuse_incomplete(combined, 'after_current_fragment')
        else:
            _need(len(historical) == 102, 'fresh final mode requires102 authenticated native-origin folds')
            combined = historical
            # The concrete capability authenticates native execution origins; pure
            # complete-roster metadata alone cannot release the final fit.
            capability = complete_origin_callback(history)
            from docs.phase2.cho51_linear_continuation_v1.contract import require_complete_folds
            complete_metadata = require_complete_folds(historical, method_config,
                input_identity_sha256=inputs_before['sha256'], template_state_sha256=INITIAL,
                initial_state_sha256=INITIAL, lineage_recipe_sha256=recipe_sha)
            winner_name = complete_metadata['winner_candidate']
            winner = next(candidate for candidate in candidates if candidate.name == winner_name)
            current.update(name=winner_name, validation=None, final=True, training=SOURCES,
                           rate=winner.source.learning_rate, offset=0)
            active.clear()
            started = perf_counter()
            try:
                selected = selector.complete_final_fit(historical, method_config,
                    input_identity_sha256=inputs_before['sha256'], template_state_sha256=INITIAL,
                    initial_state_sha256=INITIAL, lineage_recipe_sha256=recipe_sha,
                    verify_origins=capability)
            finally:
                selector._clear_cho_b_inputs()
            final_seconds = perf_counter() - started
            model, evidence = selected.source, selected.evidence
            record = evidence.record
            fit = record['payload']['final_source_fit']
            _need(not pending and len(events) == 51 and fit['training_subjects'] == list(SOURCES)
                  and fit['validation_subject'] is None and fit['initial_state_sha256'] == INITIAL
                  and len(fit['steps']) == 51 and fit['mask']['trainable_names'] == ['head.weight', 'head.bias']
                  and fit['mask']['trainable_parameters'] == 402
                  and fit['fitted_state_sha256'] == state_digest(model)
                  and record['payload']['selected_candidate'] == winner_name
                  and record['payload']['complete'] is True
                  and not any(module.training for module in model.modules())
                  and all(parameter.grad is None for parameter in model.parameters()),
                  'fresh all51-source actual fitted model and complete record differ')
            check_frozen(model)
            verified = verify_cho_selection_evidence(record=record, evidence_sha256=record['sha256'], plan=plan,
                protocol_config=fixture.protocol, catalogs=fixture.catalogs,
                selection_record=fixture.selection_record, assets=fixture.assets, root=fixture.root,
                adapter_model_state_sha256=state_digest(model), adapter_source_settings=asdict(winner.source),
                adapter_support_settings=asdict(winner.support))
            _need(verified.selected_candidate == winner_name and verified.evidence_sha256 == record['sha256'],
                  'actual fitted source must pass the canonical public complete-evidence verifier')
            selected_prepared = prepare_cho_source_restore(root=ROOT, plan=plan, method_config=method_config,
                expected_method_config_sha256=method_configuration(method_config), selected_candidate=winner_name)
            selected_recipe = selected_prepared.model_recipe
            _need(selected_recipe == {**prepared.model_recipe, 'selected_candidate': winner_name},
                  'actual selected model recipe differs from the authenticated linear baseline architecture')
            selected_recipe_sha = config_digest(selected_recipe)
            raw = (canonical_config_json(record) + '\n').encode('utf-8')
            _need(0 < len(raw) <= MAXIMUM_EVIDENCE_BYTES,
                  'complete source evidence exceeds the narrow32MiB JSON bound')
            path = output / 'selection-evidence.json'
            with path.open('xb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            persisted, _ = B._read_baseline(path, maximum_bytes=MAXIMUM_EVIDENCE_BYTES,
                expected_bytes=len(raw), expected_sha256=hashlib.sha256(raw).hexdigest())
            _need(persisted == raw, 'persisted complete source evidence differs')
            del persisted
            selected_evidence = _pin(path, raw, evidence_sha256=record['sha256'])
            verified_selection = {'selected_candidate': verified.selected_candidate,
                'evidence_sha256': verified.evidence_sha256, 'model_state_sha256': state_digest(model),
                'source_settings': asdict(winner.source), 'support_settings': asdict(winner.support),
                'selected_model_recipe_sha256': selected_recipe_sha,
                'public_complete_evidence_verifier_passed': True,
                'source_gradient_updates': 5151, 'support_gradient_updates': 102,
                'total_gradient_updates': 5253, 'folds': 102, 'fresh_final_source_updates': 51}
            checkpoint = _save_selected(output, model, checkpoint_control,
                                        selected_model_recipe_sha256=selected_recipe_sha)
            _need(checkpoint['model_state_sha256'] == verified_selection['model_state_sha256'],
                  'saved complete checkpoint differs from the publicly verified actual source')
        _need(len(events) == limits['gradient_updates'] and not pending
              and state_digest(selector._initial) == state_digest(template) == INITIAL
              and state_digest(template.backbone) == backbone_sha,
              'exact request budget and immutable baseline initialization required')
        config_final, config_after = B._read_baseline(prepared.model_config_path,
            maximum_bytes=1024**2, expected_bytes=4776, expected_sha256=B.BASELINE_CONFIG_SHA256)
        weights_final, weights_after = B._read_baseline(prepared.baseline_weights_path,
            maximum_bytes=32 * 1024**2, expected_bytes=23299672, expected_sha256=B.BASELINE_WEIGHTS_SHA256)
        _need(config_after == config_pin and weights_after == weights_pin, 'audited baseline changed during request')
        del config_final, weights_final
    finally:
        for handle in reversed(handles):
            handle.remove()
        if selector is not None:
            selector._clear_cho_b_inputs()
        if protected:
            set_protected_inputs(fixture.protected_outer_paths, False)

    _need(fixture.verify_inputs() == inputs_before and source_fingerprint(fixture.root) == source_before,
          'all original213 physical inputs and source context must remain unchanged')
    verified_after = verify_chain(origin, chain, ROOT, pins_sha256=request['pins_sha256'])
    _need(verified_after.head_sha256 == history.head_sha256
          and _json(verified_after.records) == _json(historical), 'immutable historical chain changed during request')
    after = np.random.get_state()
    _need(torch.equal(torch.random.get_rng_state(), rng[0]) and after[0] == rng[1][0]
          and np.array_equal(after[1], rng[1][1]) and after[2:] == rng[1][2:]
          and random.getstate() == rng[2], 'whole request must preserve global Torch/NumPy/Python RNG')
    collection = collect_partial(combined, method_config, input_identity_sha256=inputs_before['sha256'],
        template_state_sha256=INITIAL, initial_state_sha256=INITIAL, lineage_recipe_sha256=recipe_sha)
    _need(collection['accepted_folds'] == len(combined) and collection['pending_folds'] == 102 - len(combined),
          'combined distinct raw-fold coverage differs')
    collection_pin = B._write(output / 'partial-collection.json', collection)
    observation_pin = B._write(output / 'optimizer-observations.json', {
        'schema': 'cho51_linear_chain_optimizer_observations_v1', 'mode': mode, 'events': events,
        'actual_gradient_updates': len(events), 'source_gradient_updates': limits['source_updates'],
        'support_gradient_updates': limits['support_updates'], 'frozen_backbone_sha256': backbone_sha,
        'head_parameter_count': 402, 'head_tensor_count': 2,
        'engineering_only': True, 'scientific_admission': False})
    refusal_pin = B._write(output / 'finalization-refusals.json', {
        'schema': 'cho51_linear_chain_finalization_refusals_v1', 'mode': mode, 'refusals': refusals,
        'actual_final_source_updates': 51 if mode == 'final' else 0,
        'complete_native_origins_capability_exercised': mode == 'final',
        'final_numerical_branch_qualified': mode == 'final'})
    result = {
        'schema': 'cho51_linear_chain_probe_v1', 'passed': True, 'method': 'labram_linear',
        'index': request['index'], 'mode': mode, 'request_sha256': _physical_json(request),
        'root_origin_sha256': request['root_origin_sha256'], 'pins_sha256': request['pins_sha256'],
        'parent_head_sha256': request['parent_head_sha256'], 'case': asdict(plan), 'case_id': plan.case_id,
        'fixture_root': str(fixture.root), 'input_identity_path': str(fixture.identity_path),
        'input_identity_sha256': inputs_before['sha256'], 'input_identity_file_sha256': fixture.identity_file_sha256,
        'input_file_count': 213, 'input_bytes': 734579463, 'input_files': inputs_before['files'],
        'physical_inputs': fixture.physical_inputs, 'protected_outer_paths': [str(p) for p in fixture.protected_outer_paths],
        'fixture_source_sha256': source_before, 'source_subjects_available': 52,
        'adopted_evaluation_targets': 51, 'adopted_case_plan_count': 1020, 'outer_target': 'subject_02',
        'declared_candidates': contract['candidates'], 'current_pairs': request['pairs'],
        'method_config_sha256': method_configuration(method_config), 'diagnostic_folds': len(pairs),
        'adopted_historical_folds': len(historical), 'combined_folds': len(combined),
        'pending_folds': 102 - len(combined), 'combined_fold_gradient_updates': 51 * len(combined),
        'maximum_gradient_steps': 5253, 'required_selection_updates': 5253,
        'budget': limits, 'source_gradient_updates': limits['source_updates'],
        'support_gradient_updates': limits['support_updates'], 'actual_gradient_updates': len(events),
        'current_gradient_updates': len(events), 'final_source_updates': 51 if mode == 'final' else 0,
        'total_verified_gradient_updates': 5253 if mode == 'final' else None,
        'optimizer_updates': events, 'optimizer_observations': observation_pin,
        'template_state_sha256': INITIAL, 'initial_source_state_sha256': INITIAL,
        'backbone_state_sha256': backbone_sha, 'template_parameter_count': 5818138,
        'selected_parameter_names': ['head.weight', 'head.bias'], 'selected_parameter_count': 402,
        'selected_tensor_count': 2, 'full_backbone_blocks': 12, 'full_backbone_embed_dim': 200,
        'model_recipe': prepared.model_recipe, 'model_recipe_sha256': recipe_sha,
        'lineage_recipe_sha256': recipe_sha,
        'selected_model_recipe': selected_recipe, 'selected_model_recipe_sha256': selected_recipe_sha,
        'baseline_config': config_pin, 'baseline_weights': weights_pin,
        'baseline_safe_tensor_count': 221, 'baseline_safe_elements': 5819936,
        'one_time_setup_seconds': setup_seconds, 'fold_timings_seconds': timings,
        'final_fit_seconds': final_seconds, 'fold_evidence': fold_pins, 'partial_collection': collection_pin,
        'finalization_refusals': refusal_pin, 'incomplete_finalization_refusal_count': len(refusals),
        'complete_native_origins_capability_exercised': mode == 'final',
        'final_numerical_branch_qualified': mode == 'final', 'selection_evidence': selected_evidence,
        'checkpoint': checkpoint, 'verified_selection': verified_selection,
        'contract_sha256': CONTRACT, 'logical_complete_scope_checked': True,
        'public_complete_selector_verifier_refused': mode == 'folds',
        'public_complete_evidence_verifier_passed': mode == 'final',
        'public_refusal_reason': PUBLIC_REFUSAL if mode == 'folds' else None,
        'original_native_origin_verified': True, 'source_work_reused': True,
        'reused_historical_folds': len(historical), 'old_fixture_read_only': True,
        'all_physical_inputs_rehashed_unchanged': True, 'supplied_template_unchanged': True,
        'source_backbone_and_buffers_unchanged': True, 'independent_lineage_verified': True,
        'independent_storage_verified': True, 'fixture_source_context_unchanged': True,
        'torch_numpy_python_rng_unchanged': True, 'finite_losses_gradients_parameters': True,
        'canonical_source_exclusion_verified': True, 'actual_public_run_fold': mode == 'folds',
        'pretrained_baseline_loaded': True, 'pretrained_weights_loaded': True,
        'cohort_lineage_verified': False, 'prior_template_training_verified': False,
        'canonical_private_lineage_constructor_exercised': True,
        'canonical_run_selection_invoked': False, 'public_selected_source_restore_exercised': False,
        'complete': mode == 'final', 'selected_candidate': winner_name,
        'full_selector_verified': mode == 'final', 'full_worker_verified': False,
        'publication_performed': False, 'recorder_used': False, 'measured_cells': 0,
        'synthetic': True, 'actual_study_data_loaded': False, 'engineering_only': True,
        'scientific_admission': False, 'original_case_attempts_remaining': 0}
    B._write(output / 'probe-result.json', result)
    return result
