"""Eight genuine public linear folds on the accepted immutable fixture.

All project/model imports and execution belong inside a fresh admitted native
child. Historical folds retain their original bytes and native origins.
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

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = PROJECT_ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001'
SUBJECTS = tuple(f'subject_{number:02d}' for number in range(1, 53))
SOURCES = tuple(subject for subject in SUBJECTS if subject != 'subject_02')
NAMES = ('lr_1e-3', 'lr_2e-3')
RATES = (0.001, 0.002)
VALIDATIONS = ('subject_03', 'subject_04', 'subject_05', 'subject_06')
PAIRS = tuple((name, subject) for name in NAMES for subject in VALIDATIONS)
INITIAL_SHA256 = '90a9d34ecba2aa96a942f7bd70724f63c2071042141935dbbcd78e0b373b89a7'
CONTRACT_SHA256 = '8397d34ee0a2280b406071e045988f98b1b73ce21fcecc0b9834518cd21993b1'
PUBLIC_REFUSAL = 'selection evidence has missing or unexpected fields'
FINAL_REFUSAL = 'all 102 distinct canonical folds are required before a fresh final source fit'


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _read_original(path, expected_sha256, *, maximum_bytes=8 * 1024**2):
    from docs.phase2.cho51_linear_lineage_v1.probe import _read_baseline
    path = Path(path)
    _need(path.is_relative_to(ORIGINAL), 'original metadata must remain inside its accepted output')
    raw, pin = _read_baseline(path, maximum_bytes=maximum_bytes,
        expected_bytes=path.stat().st_size, expected_sha256=expected_sha256)
    value = json.loads(raw)
    _need(type(value) is dict, 'original finite JSON object required')
    return value, pin


def _existing_fixture(origin):
    """Authenticate existing files, reconstruct metadata, and never regenerate."""
    from core.config import config_digest, load_toml
    from docs.phase2.cho51_source_fold_probe_v1 import fixture as F
    from evaluation.phase2_protocol import nested_episode, source_selection
    from evaluation.phase2_records import envelope
    from scripts.audit_phase2_protocol import read_catalog, validate_protocol
    root = Path(origin['fixture_root'])
    identity_path = Path(origin['input_identity_path'])
    _need(root == ORIGINAL / 'fixture' and root.resolve(strict=True) == root
          and identity_path == root / 'synthetic-input-identity.json',
          'the exact original accepted physical fixture is required')
    identity, _ = _read_original(identity_path, origin['input_identity_file_sha256'])
    _need(identity['sha256'] == origin['input_identity_sha256']
          and config_digest({k: v for k, v in identity.items() if k != 'sha256'}) == identity['sha256']
          and identity['synthetic'] is True and identity['actual_study_data'] is False
          and identity['source_subjects_available'] == 52
          and identity['canonical_shot_levels'] == [1, 5, 10, 20]
          and identity['profile_a_shape'] == [42, 64, 512]
          and identity['profile_b_shape'] == [42, 64, 800], 'original full synthetic identity differs')
    paths = tuple(sorted(
        [root / relative for relative in F.CONFIGURATIONS]
        + [path for subject in F.SUBJECTS for path in F._subject_paths(root, subject)],
        key=lambda path: path.relative_to(root).as_posix()))
    _need(len(paths) == 213 and set(identity['files']) == {
        path.relative_to(root).as_posix() for path in paths}
        and sum(pin['size_bytes'] for pin in identity['files'].values()) == 734579463,
        'exact original213-input/734579463-byte inventory required')
    for path in paths:
        _need(F._input_pin(path) == identity['files'][path.relative_to(root).as_posix()],
              'original physical input bytes or identity changed')
    protocol = load_toml(root / 'configs/phase2/protocol.toml')
    _need(validate_protocol(protocol) == (1, 5, 10, 20)
          and protocol['datasets']['cho2017']['expected_subjects'] == 52
          and config_digest(protocol) == identity['protocol_sha256'], 'original protocol differs')
    threshold_path = root / 'configs/benchmark.toml'
    threshold = load_toml(threshold_path)['datasets']['cho2017']['artifact_threshold_volts']
    preprocessing = config_digest({
        'profile_identity': protocol['preparation']['profile_identity'],
        'threshold_config_sha256': identity['files']['configs/benchmark.toml']['sha256'],
        'dataset': 'cho2017', 'threshold': threshold})
    catalogs, assets, episodes = [], {}, {}
    for subject in SUBJECTS:
        a, b, manifest, _ = F._subject_paths(root, subject)
        catalog, metadata = read_catalog(a, dataset='cho2017', classes=F.CHO_CLASSES,
            threshold=threshold, preprocessing_sha256=preprocessing)
        _need(catalog.subject == subject and metadata['retained_trials'] == 42
              and metadata['rejected_trials'] == 0
              and metadata['retained_class_counts'] == {label: 21 for label in F.CHO_CLASSES},
              'original subject catalog or retained trials changed')
        catalogs.append(catalog)
        assets[subject] = F.ChoProfileAssets60Hz(
            identity['files'][b.relative_to(root).as_posix()]['sha256'],
            identity['files'][manifest.relative_to(root).as_posix()]['sha256'],
            identity['files']['configs/phase2/cho_profile_b_60hz.toml']['sha256'])
        episodes[subject] = envelope('episode_manifest', nested_episode(catalog,
            shots=(1, 5, 10, 20), protocol_sha256=config_digest(protocol)).payload())
    selection = source_selection(tuple(catalogs), target='subject_02')
    _need(selection.sha256 == identity['source_selection_sha256'], 'original source selection differs')
    fixture = F.Fixture(root, protocol, tuple(catalogs), envelope('source_selection', asdict(selection)),
        assets, episodes, identity, paths, F._subject_paths(root, 'subject_02'),
        'labram_linear', 'cho_profile_b_60hz_v1', identity_path, origin['input_identity_file_sha256'])
    fixture.verify_inputs()
    return fixture


def run_probe(output: Path, method_config: dict, *, origin: dict, set_protected_inputs) -> dict:
    """Run the next exact eight folds, retaining the two original raw records."""
    _need(isinstance(output, Path) and output.is_absolute() and output.is_dir()
          and output.resolve(strict=True) == output and type(method_config) is dict
          and type(origin) is dict and callable(set_protected_inputs),
          'direct unused output, adopted method, native origin and protection required')
    _need(all(not (output / name).exists() for name in (
        'probe-result.json', 'partial-collection.json', 'optimizer-observations.json',
        'finalization-refusals.json', *(f'fold_{i:02d}.json' for i in range(1, 9)))),
        'all current continuation artifact paths must be unused')

    import numpy as np
    import torch
    from braindecode.models import Labram
    from safetensors.torch import load
    from torch.nn.modules.module import register_module_forward_pre_hook
    from torch.optim.optimizer import register_optimizer_step_pre_hook, register_optimizer_step_post_hook
    from adaptation.labram_manifest import LaBraMTuningSettings
    from adaptation.labram_source import LaBraMSourceCandidate, LaBraMSourceSettings
    from core.config import canonical_config_json, config_digest, config_snapshot
    from core.provenance import source_fingerprint
    from docs.phase2.cho51_linear_lineage_v1 import probe as P
    from docs.phase2.cho51_linear_continuation_v1.contract import collect_partial
    from docs.phase2.cho51_linear_continuation_v1.origin import verify_origin
    from docs.phase2.cho51_linear_continuation_v1.selector import StagedLinearSourceSelector
    from encoder.labram import LaBraMClassifier, configure_pretrained_sequence
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_source_restore import prepare_cho_source_restore, _new_model
    from evaluation.phase2_profile_binding import CHO_CHANNELS
    from evaluation.phase2_protocol import nested_episode
    from evaluation.phase2_records import verify_envelope
    from evaluation.phase2_runner import CasePlan, method_configuration
    from evaluation.phase2_selection_evidence_binding import verify_cho_selection_evidence

    _need(torch.get_num_threads() == torch.get_num_interop_threads() == 1
          and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'one-thread hidden-GPU child required')
    rng = torch.random.get_rng_state().clone(), np.random.get_state(), random.getstate()
    verify_origin(origin, PROJECT_ROOT)
    fixture = _existing_fixture(origin)
    inputs_before = fixture.verify_inputs()
    source_before = source_fingerprint(fixture.root)
    _need(inputs_before['sha256'] == origin['input_identity_sha256']
          and origin['contract_sha256'] == origin['original_contract_sha256'] == CONTRACT_SHA256
          and origin['template_state_sha256'] == origin['initial_state_sha256'] == INITIAL_SHA256,
          'accepted predecessor input, contract and initial lineage pins required')
    expected_method = {
        'dataset': 'cho2017', 'method': 'labram_linear', 'input_profile': 'cho_profile_b_60hz_v1',
        'variant_config_sha256': fixture.assets['subject_01'].variant_config_sha256,
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
    _need(method_config == expected_method, 'exact unchanged adopted linear candidate configuration required')
    method_sha = method_configuration(method_config)
    old_records, old_pins = [], []
    for index, name in enumerate(NAMES):
        record, pin = _read_original(Path(origin['original_fold_paths'][index]),
                                    origin['original_fold_file_sha256'][index])
        _need(record['sha256'] == origin['original_fold_evidence_sha256'][index]
              and record['payload']['contract_sha256'] == CONTRACT_SHA256
              and record['payload']['complete'] is False
              and record['payload']['folds'][0]['candidate'] == name
              and record['payload']['folds'][0]['validation_subject'] == 'subject_01',
              'the two genuine predecessor partial records must retain their exact origins')
        old_records.append(record)
        old_pins.append(pin)
    candidates = tuple(LaBraMSourceCandidate(row['name'], LaBraMSourceSettings(**row['source']),
        LaBraMTuningSettings(**row['support'])) for row in method_config['candidates'])
    plan = CasePlan('cho2017', 'subject_02', 'labram_linear', 5, 11, 1)
    records, pins, timings, events, refusals = [], [], [], [], []
    current, pending, active_model = {}, {}, {}
    handles = []
    protected = False

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
              and all(p.grad is None for name, p in model.named_parameters() if name.startswith('backbone.'))
              and state_digest(model.backbone) == backbone_sha,
              'exact linear head mask or immutable frozen backbone/buffers changed')

    def before_forward(module, args):
        if isinstance(module, LaBraMClassifier):
            check_frozen(module)
            active_model['model'] = module

    def before_step(optimizer, args, kwargs):
        _need(type(optimizer) is torch.optim.SGD and not pending and len(events) < 408,
              'actual sequential bounded canonical SGD required')
        parameters = tuple(p for group in optimizer.param_groups for p in group['params'])
        model = active_model.get('model')
        _need(model is not None and tuple(id(p) for p in parameters)
              == tuple(id(p) for p in model.head.parameters())
              and len(parameters) == 2 and sum(p.numel() for p in parameters) == 402,
              'optimizer must select exactly the active classifier head')
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
        parameters = pending['parameters']
        check_frozen(pending['model'])
        after = selected_digest(parameters)
        _need(after != pending['before'] and all(torch.isfinite(p).all().item() for p in parameters),
              'actual finite head SGD must change selected bytes')
        index = len(events) - current['offset']
        _need(0 <= index <= 50, 'exact50-source/one-support per-fold bound required')
        events.append({
            'update': len(events) + 1, 'fold_update': index + 1,
            'candidate': current['name'], 'validation_subject': current['validation'],
            'role': 'source' if index < 50 else 'inner_validation_support',
            'subject': current['training'][index] if index < 50 else current['validation'],
            'learning_rate': current['rate'], 'selected_parameters': 402, 'selected_tensors': 2,
            'selected_state_sha256_before': pending['before'], 'selected_state_sha256_after': after,
            'finite_selected_gradients': True, 'finite_selected_parameters': True,
            'frozen_backbone_and_buffers_unchanged': True})
        pending.clear()

    def forbidden_origin_capability(records, metadata):
        raise AssertionError('incomplete finalization must refuse before asking for complete native origins')

    def refuse_incomplete(records, stage):
        count = len(events)
        reason = None
        try:
            selector.complete_final_fit(records, method_config,
                input_identity_sha256=inputs_before['sha256'], template_state_sha256=template_sha,
                initial_state_sha256=initial_sha, lineage_recipe_sha256=config_digest(prepared.model_recipe),
                verify_origins=forbidden_origin_capability)
        except ValueError as error:
            reason = str(error)
        _need(reason == FINAL_REFUSAL and len(events) == count and not pending
              and state_digest(selector._initial) == initial_sha,
              'incomplete staged finalization must refuse before any fitting or numerical update')
        refusals.append({'stage': stage, 'records': len(records), 'reason': reason,
                         'observed_updates_before': count, 'observed_updates_after': len(events),
                         'before_fit': True, 'origin_capability_called': False})

    try:
        set_protected_inputs(fixture.protected_outer_paths, True)
        protected = True
        started = perf_counter()
        prepared = prepare_cho_source_restore(root=PROJECT_ROOT, plan=plan, method_config=method_config,
            expected_method_config_sha256=method_sha, selected_candidate=NAMES[0])
        _need(prepared.model_config_path == PROJECT_ROOT / P.BASELINE_DIRECTORY / 'config.json'
              and prepared.baseline_weights_path == PROJECT_ROOT / P.BASELINE_DIRECTORY / 'model.safetensors'
              and config_digest(prepared.model_recipe) == origin['lineage_recipe_sha256'],
              'exact accepted baseline recipe is required')
        config_raw, config_pin = P._read_baseline(prepared.model_config_path,
            maximum_bytes=1024**2, expected_bytes=4776, expected_sha256=P.BASELINE_CONFIG_SHA256)
        weights_raw, weights_pin = P._read_baseline(prepared.baseline_weights_path,
            maximum_bytes=32 * 1024**2, expected_bytes=23299672, expected_sha256=P.BASELINE_WEIGHTS_SHA256)
        settings = json.loads(config_raw)
        _need(settings.get('n_times') == 3000 and settings.get('n_outputs') == 0
              and settings.get('braindecode_version') == '1.3.2', 'audited complete architecture metadata required')
        safe_state = load(weights_raw)
        _need(type(safe_state) is dict and len(safe_state) == 221
              and sum(t.numel() for t in safe_state.values()) == 5819936
              and all(isinstance(t, torch.Tensor) and t.device.type == 'cpu' and t.dtype == torch.float32
                      and torch.isfinite(t).all().item() for t in safe_state.values()),
              'all221 finite CPU float32 audited safe tensors required')
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
              and sum(p.numel() for p in template.parameters()) == 5818138,
              'full12-block/embed200 classifier required')
        template_sha = state_digest(template)
        backbone_sha = state_digest(template.backbone)
        selector = StagedLinearSourceSelector(fixture.root, fixture.protocol, fixture.catalogs,
            fixture.selection_record, template, fixture.assets, outer_target='subject_02',
            template_state_sha256=template_sha, candidates=candidates, seed=11, shots_per_class=5,
            maximum_gradient_steps=5253, source_device='cpu', checkpoint_directory=None,
            operator_compute_admitted=False)
        initial_sha = state_digest(selector._initial)
        contract = selector.contract
        _need(template_sha == initial_sha == INITIAL_SHA256
              and selector.admit_complete_scope() == CONTRACT_SHA256
              and contract == old_records[0]['payload']['contract'] == old_records[1]['payload']['contract'],
              'fresh continuation selector must reproduce the exact accepted contract and state')
        check_frozen(selector._initial)
        reconstructed = _new_model(prepared, contract=contract)
        check_frozen(reconstructed)
        models = (template, selector._initial, reconstructed)
        storages = [{v.untyped_storage().data_ptr() for v in model.state_dict().values() if v.numel()}
                    for model in models]
        _need(state_digest(reconstructed) == initial_sha
              and all(not storages[a] & storages[b] for a in range(3) for b in range(a + 1, 3)),
              'independent canonical reconstruction must match without shared tensor storage')
        del models, storages, reconstructed
        setup_seconds = perf_counter() - started
        refuse_incomplete(old_records, 'before_new_folds')
        handles.append(register_module_forward_pre_hook(before_forward))
        handles.append(register_optimizer_step_pre_hook(before_step))
        handles.append(register_optimizer_step_post_hook(after_step))
        catalogs = {catalog.subject: catalog for catalog in fixture.catalogs}
        for number, (name, validation) in enumerate(PAIRS, 1):
            candidate = next(candidate for candidate in candidates if candidate.name == name)
            training = tuple(subject for subject in SOURCES if subject != validation)
            current.update(name=name, validation=validation, training=training,
                           rate=candidate.source.learning_rate, offset=len(events))
            active_model.clear()
            started = perf_counter()
            evidence = selector.run_fold(candidate_name=name, validation_subject=validation)
            timings.append(perf_counter() - started)
            _need(not pending and len(events) == number * 51 and selector.contract == contract
                  and state_digest(selector._initial) == initial_sha
                  and state_digest(template) == template_sha and all(p.grad is None for p in template.parameters()),
                  'exact51-update public fold must preserve owned/template state')
            check_frozen(selector._initial)
            record = evidence.record
            payload = record['payload']
            _need(verify_envelope(record, kind='engineering_smoke', expected_payload=payload)
                  and set(payload) == {'purpose', 'contract', 'contract_sha256', 'complete', 'folds', 'selected_candidate'}
                  and payload['contract'] == contract and payload['contract_sha256'] == CONTRACT_SHA256
                  and payload['complete'] is False and payload['selected_candidate'] is None
                  and len(payload['folds']) == 1, 'actual unchanged raw incomplete public envelope required')
            fold = payload['folds'][0]
            fit = fold['source_fit']
            _need(fold['candidate'] == name and fold['validation_subject'] == validation
                  and fit['candidate'] == name and fit['validation_subject'] == validation
                  and fit['training_subjects'] == list(training)
                  and len(training) == 50 and 'subject_01' in training and 'subject_02' not in training
                  and set(fit['input_identities']) == set(training)
                  and fit['settings'] == config_snapshot(asdict(candidate.source))
                  and fit['initial_state_sha256'] == initial_sha and len(fit['steps']) == 50
                  and fit['mask']['trainable_names'] == fold['support_mask']['trainable_names'] == ['head.weight', 'head.bias']
                  and fit['mask']['trainable_parameters'] == fold['support_mask']['trainable_parameters'] == 402,
                  'current held-out subject, permitted sources, settings and exact masks differ')
            prior = initial_sha
            for step_number, (subject, step) in enumerate(zip(training, fit['steps'], strict=True), 1):
                _need(step['step'] == step_number and step['subject'] == subject and step['subject_step'] == 1
                      and step['iterator_wraps'] == 0 and len(step['trial_ids']) == len(set(step['trial_ids'])) == 2
                      and set(step['trial_ids']) <= set(catalogs[subject].trial_ids)
                      and type(step['loss']) in (int, float) and math.isfinite(step['loss'])
                      and step['state_sha256_after'] != prior, 'actual distinct finite source SGD history differs')
                prior = step['state_sha256_after']
            episode = nested_episode(catalogs[validation], shots=(1, 5, 10, 20),
                                     protocol_sha256=config_digest(fixture.protocol))
            partition = episode.partition(5)
            support_ids = [episode.catalog.trial_ids[n] for n in partition.support_indices]
            query_ids = [episode.catalog.trial_ids[n] for n in partition.query_indices]
            losses = fold['support_losses']
            _need(prior == fit['fitted_state_sha256'] and prior != initial_sha
                  and fold['adapted_state_sha256'] != prior and fold['binding']['subject'] == validation
                  and fold['binding']['support_trial_ids'] == support_ids
                  and fold['binding']['query_trial_ids'] == query_ids
                  and len(support_ids) == 10 and len(query_ids) == 2 and not set(support_ids) & set(query_ids)
                  and len(losses) == 1 and all(type(v) in (int, float) and math.isfinite(v) for v in losses),
                  'actual support/query continuation, loss and changed state differ')
            confusion = fold['confusion_matrix']
            _need(type(confusion) is list and len(confusion) == 2
                  and all(type(row) is list and len(row) == 2 and sum(row) == 1
                          and all(type(v) is int and v >= 0 for v in row) for row in confusion),
                  'exactly one withheld query prediction per class required')
            score = sum((Fraction(confusion[n][n], sum(confusion[n])) for n in range(2)), Fraction()) / 2
            _need(fold['balanced_accuracy'] == [score.numerator, score.denominator], 'exact rational score differs')
            path = output / f'fold_{number:02d}.json'
            evidence.write(path, output_root=output)
            raw = (canonical_config_json(record) + '\n').encode('utf-8')
            _need(path.read_bytes() == raw, 'current raw fold bytes differ after persistence')
            refusal = None
            row = next(row for row in contract['candidates'] if row['name'] == name)
            try:
                verify_cho_selection_evidence(record=record, evidence_sha256=record['sha256'], plan=plan,
                    protocol_config=fixture.protocol, catalogs=fixture.catalogs,
                    selection_record=fixture.selection_record, assets=fixture.assets, root=fixture.root,
                    adapter_model_state_sha256=fit['fitted_state_sha256'],
                    adapter_source_settings=row['source'], adapter_support_settings=row['support'])
            except ValueError as error:
                refusal = str(error)
            _need(refusal == PUBLIC_REFUSAL, 'current raw partial fold must fail the public completeness schema')
            pins.append({'candidate': name, 'validation_subject': validation, 'path': str(path),
                         'evidence_sha256': record['sha256'], 'file_sha256': hashlib.sha256(raw).hexdigest(),
                         'size_bytes': len(raw), 'elapsed_seconds': timings[-1],
                         'public_refusal_reason': refusal, 'balanced_accuracy': fold['balanced_accuracy'],
                         'fitted_state_sha256': fit['fitted_state_sha256'],
                         'adapted_state_sha256': fold['adapted_state_sha256']})
            records.append(record)
            active_model.clear()
        combined = [*old_records, *records]
        refuse_incomplete(combined, 'after_combined_ten_folds')
        config_final, config_final_pin = P._read_baseline(prepared.model_config_path,
            maximum_bytes=1024**2, expected_bytes=4776, expected_sha256=P.BASELINE_CONFIG_SHA256)
        weights_final, weights_final_pin = P._read_baseline(prepared.baseline_weights_path,
            maximum_bytes=32 * 1024**2, expected_bytes=23299672, expected_sha256=P.BASELINE_WEIGHTS_SHA256)
        _need(config_final_pin == config_pin and weights_final_pin == weights_pin,
              'audited baseline bytes and file identities changed after current folds')
        del config_final, weights_final
    finally:
        for handle in reversed(handles):
            handle.remove()
        if protected:
            set_protected_inputs(fixture.protected_outer_paths, False)

    _need(fixture.verify_inputs() == inputs_before and source_fingerprint(fixture.root) == source_before,
          'all original physical inputs and source context must remain unchanged')
    verify_origin(origin, PROJECT_ROOT)
    numpy_after = np.random.get_state()
    _need(torch.equal(torch.random.get_rng_state(), rng[0]) and numpy_after[0] == rng[1][0]
          and np.array_equal(numpy_after[1], rng[1][1]) and numpy_after[2:] == rng[1][2:]
          and random.getstate() == rng[2], 'whole continuation must preserve Torch/NumPy/Python global RNG')
    collection = collect_partial(combined, method_config, input_identity_sha256=inputs_before['sha256'],
        template_state_sha256=template_sha, initial_state_sha256=initial_sha,
        lineage_recipe_sha256=config_digest(prepared.model_recipe))
    _need(collection['accepted_folds'] == 10 and collection['pending_folds'] == 92
          and collection['executed_source_updates'] == 500 and collection['executed_support_updates'] == 10
          and collection['executed_gradient_updates'] == 510 and collection['complete'] is False
          and collection['selected_candidate'] is None and collection['final_fit_ready'] is False,
          'ten genuine distinct partial records must retain92 pending and no final-fit authority')
    collection_pin = P._write(output / 'partial-collection.json', collection)
    observations = P._write(output / 'optimizer-observations.json', {
        'schema': 'cho51_linear_continuation_optimizer_observations_v1', 'events': events,
        'actual_gradient_updates': len(events), 'source_gradient_updates': 400,
        'support_gradient_updates': 8, 'frozen_backbone_sha256': backbone_sha,
        'head_parameter_count': 402, 'head_tensor_count': 2,
        'engineering_only': True, 'scientific_admission': False})
    refusal_pin = P._write(output / 'finalization-refusals.json', {
        'schema': 'cho51_linear_continuation_finalization_refusals_v1', 'refusals': refusals,
        'actual_final_source_updates': 0, 'complete_native_origins_capability_exercised': False,
        'final_numerical_branch_qualified': False})
    result = {
        'schema': 'cho51_linear_continuation_probe_v1', 'passed': True, 'method': 'labram_linear',
        'case': asdict(plan), 'case_id': plan.case_id, 'fixture_root': str(fixture.root),
        'input_identity_path': str(fixture.identity_path), 'input_identity_sha256': inputs_before['sha256'],
        'input_identity_file_sha256': fixture.identity_file_sha256, 'input_file_count': 213,
        'input_files': inputs_before['files'], 'physical_inputs': fixture.physical_inputs,
        'input_bytes': 734579463, 'protected_outer_paths': [str(path) for path in fixture.protected_outer_paths],
        'fixture_source_sha256': source_before, 'source_subjects_available': 52,
        'adopted_evaluation_targets': 51, 'adopted_case_plan_count': 1020,
        'outer_target': 'subject_02', 'validation_subjects': list(VALIDATIONS),
        'declared_candidates': contract['candidates'], 'current_pairs': [list(pair) for pair in PAIRS],
        'method_config_sha256': method_sha, 'diagnostic_folds': 8,
        'adopted_historical_folds': 2, 'combined_folds': 10, 'pending_folds': 92,
        'historical_source_updates': 100, 'historical_support_updates': 2,
        'historical_gradient_updates': 102, 'combined_described_gradient_updates': 510,
        'maximum_gradient_steps': 5253, 'required_selection_updates': 5253,
        'source_gradient_updates': 400, 'support_gradient_updates': 8, 'actual_gradient_updates': len(events),
        'optimizer_updates': events, 'optimizer_observations': observations,
        'template_state_sha256': template_sha, 'initial_source_state_sha256': initial_sha,
        'backbone_state_sha256': backbone_sha, 'template_parameter_count': 5818138,
        'selected_parameter_names': ['head.weight', 'head.bias'], 'selected_parameter_count': 402,
        'selected_tensor_count': 2, 'full_backbone_blocks': 12, 'full_backbone_embed_dim': 200,
        'model_recipe': prepared.model_recipe, 'model_recipe_sha256': config_digest(prepared.model_recipe),
        'baseline_config': config_pin, 'baseline_weights': weights_pin,
        'baseline_safe_tensor_count': 221, 'baseline_safe_elements': 5819936,
        'one_time_setup_seconds': setup_seconds, 'fold_timings_seconds': timings,
        'fold_evidence': pins, 'original_fold_evidence': old_pins, 'partial_collection': collection_pin,
        'finalization_refusals': refusal_pin, 'incomplete_finalization_refused_before_fit': True,
        'incomplete_finalization_refusal_count': 2, 'final_source_updates': 0,
        'complete_native_origins_capability_exercised': False, 'final_numerical_branch_qualified': False,
        'contract_sha256': CONTRACT_SHA256, 'logical_complete_scope_checked': True,
        'public_complete_selector_verifier_refused': True, 'public_refusal_reason': PUBLIC_REFUSAL,
        'refusal_boundary': 'raw_incomplete_diagnostic_payload_schema',
        'origin_sha256': config_digest(origin), 'original_native_origin_verified': True,
        'source_work_reused': True, 'reused_historical_folds': 2,
        'old_fixture_read_only': True, 'all_physical_inputs_rehashed_unchanged': True,
        'supplied_template_unchanged': True, 'source_backbone_and_buffers_unchanged': True,
        'independent_lineage_verified': True, 'independent_storage_verified': True,
        'fixture_source_context_unchanged': True, 'torch_numpy_python_rng_unchanged': True,
        'finite_losses_gradients_parameters': True, 'canonical_source_exclusion_verified': True,
        'actual_public_run_fold': True, 'pretrained_baseline_loaded': True,
        'pretrained_weights_loaded': True, 'cohort_lineage_verified': False,
        'prior_template_training_verified': False, 'canonical_private_lineage_constructor_exercised': True,
        'public_selected_source_restore_exercised': False, 'full_selection_attempted': False,
        'complete': False, 'selected_candidate': None, 'full_selector_verified': False,
        'full_worker_verified': False, 'publication_performed': False, 'recorder_used': False,
        'measured_cells': 0, 'synthetic': True, 'actual_study_data_loaded': False,
        'engineering_only': True, 'scientific_admission': False, 'original_case_attempts_remaining': 0,
    }
    P._write(output / 'probe-result.json', result)
    return result
