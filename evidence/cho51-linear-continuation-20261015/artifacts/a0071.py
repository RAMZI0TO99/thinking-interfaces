"""Archive a bounded two-fold lineage qualification using metadata only."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path, PurePosixPath

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = RUN / 'validation_001'
spec = importlib.util.spec_from_file_location('_linear_frozen_metadata',
    ROOT / 'runs/coordination/cho51_staged_restore_20261015_v1/metadata.py')
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)


def logical(value):
    return hashlib.sha256(M.old.canonical(value)).hexdigest()


def main():
    refusal = ROOT / 'evidence/cho51-linear-lineage-reporting-refusal-20261015'
    failure_manifest, _ = M.document(refusal / 'manifest.json', expected='426bae32b4ba07cb46ac54038d58f0a46954db94f7920c65a206ed9e2700f4f9')
    failure_summary, _ = M.document(refusal / 'summary.json', expected='f7f91654d332feb7d96f1da103de04cba3e8c2f13e1d607409545fe20fe7c3a1')
    M.old.fields(failure_summary, {'accepted': False, 'main_tests_passed': 32,
        'subtests_passed': 23, 'actual_gradient_updates': 0, 'baseline_tensor_decodes': 0,
        'synthetic_fixture_created': False, 'job_closed_empty_freshly_absent': True, 'artifacts': 26})
    refusal_sources = {refusal / 'manifest.json', refusal / 'summary.json', refusal / 'README.md'}
    for row in failure_manifest['artifacts']:
        for path in (ROOT / row['source'], refusal / row['path']):
            _, actual = M.remember(path, expected=row['sha256'], compact=True)
            if actual[2] != row['bytes']:
                raise ValueError('preserved reporting-refusal source/archive bytes differ')
            refusal_sources.add(path)
    M.launcher._job_absent('pro3_migration_20261015T143319Z_0e097ec22e')
    pins, pins_sha = M.document(RUN / 'pins.json')
    M.verify_pin_map(pins)
    for path, sha in pins['baseline'].items():
        _, identity = M.remember(Path(path), expected=sha)
        if identity[2] != 23299672:
            raise ValueError('exact audited safe baseline byte count required')
    review, _ = M.document(RUN / 'source-review.json', expected=pins['source_review_sha256'])
    M.old.fields(review, {'source_only': True, 'remaining_actionable_findings': [], 'files': pins['reviewed_files']})
    method, _ = M.document(RUN / 'method-config.json', expected=pins['method_config_file_sha256'], canonical_raw=True)
    dispatch, _ = M.document(RUN / 'dispatch_001.json')
    dispatched, _ = M.document(RUN / 'dispatch_result_001.json')
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'child.py'),
        '--pins', str(RUN / 'pins.json'), '--expect-pins', pins_sha, '--output', str(OUT)]
    for value in (dispatch, dispatched):
        M.old.fields(value, {'pins_sha256': pins_sha, 'child_command': command,
            'expected_output': str(OUT), 'scientific_admission': False})
    M.old.fields(dispatched, {'guard_exit_code': 0})
    operations, runtimes = M.native_pins(pins)
    native = M.old.verify_native(Path(dispatched['native_directory']), command, 600, 4096, 5120,
        operations=operations, runtimes=runtimes, document=M.document, remember=M.remember, launcher=M.launcher)
    q, q_sha = M.document(OUT / 'qualification.json', canonical_raw=True)
    M.old.fields(q, {'schema': 'cho51_linear_lineage_qualification_v1', 'passed': True,
        'pins_sha256': pins_sha, 'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': 5,
        'canonical_source_sha256': M.CANONICAL, 'canonical_files': 432,
        'source_review_sha256': pins['source_review_sha256'], 'torch_threads': 1,
        'torch_interop_threads': 1, 'gpu_hidden': True, 'unexpected_denials': 0,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    result, result_sha = M.document(OUT / 'probe-result.json', canonical_raw=True)
    child, _ = M.document(OUT / 'result.json', canonical_raw=True)
    if q['result'] != child or child['probe'] != result:
        raise ValueError('native qualification must bind the persisted child wrapper and actual probe result')
    M.old.fields(child, {'schema': 'cho51_linear_lineage_child_result_v1', 'passed': True,
        'tests_passed': True, 'pytest_exit': 0, 'collected_tests': pins['expected_tests'],
        'expected_tests': pins['expected_tests'], 'skipped_reports': [],
        'expected_subtests': 23, 'collected_subtests': 23,
        'actual_gradient_updates': 102, 'source_updates': 100, 'support_updates': 2,
        'diagnostic_folds': 2, 'required_selection_updates': 5253,
        'pretrained_baseline_loaded': True, 'cohort_lineage_verified': False,
        'full_selector_verified': False, 'full_worker_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    if len(child['reports']) != pins['expected_tests'] or any(
            row['phase'] != 'call' or row['outcome'] != 'passed' for row in child['reports']):
        raise ValueError('every exact partial-contract boundary test must pass without skips')
    if len(child['subtest_reports']) != 23 or any(
            row['phase'] != 'call' or row['outcome'] != 'passed' for row in child['subtest_reports']):
        raise ValueError('all 23 independently recorded subtests must pass without skips')
    M.old.fields(result, {'schema': 'cho51_linear_lineage_probe_v1', 'passed': True, 'method': 'labram_linear',
        'source_subjects_available': 52, 'adopted_evaluation_targets': 51, 'adopted_case_plan_count': 1020,
        'input_file_count': 213, 'input_bytes': 734579463, 'outer_target': 'subject_02',
        'inner_validation_subject': 'subject_01', 'executed_candidates': ['lr_1e-3', 'lr_2e-3'],
        'candidate_rates': [.001, .002], 'method_config_sha256': logical(method),
        'diagnostic_folds': 2, 'required_complete_folds': 102, 'pending_folds': 100,
        'maximum_gradient_steps': 5253, 'required_selection_updates': 5253,
        'source_gradient_updates': 100, 'support_gradient_updates': 2, 'actual_gradient_updates': 102,
        'template_parameter_count': 5818138, 'selected_parameter_names': ['head.weight', 'head.bias'],
        'selected_parameter_count': 402, 'selected_tensor_count': 2,
        'full_backbone_blocks': 12, 'full_backbone_embed_dim': 200,
        'baseline_safe_tensor_count': 221, 'baseline_safe_elements': 5819936,
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
        'engineering_only': True, 'scientific_admission': False, 'original_case_attempts_remaining': 0})
    calls = q['observed_numerical_calls']
    for key, expected in {'tensor_backward': 102, 'autograd_backward': 102, 'sgd_step': 102,
        'optimizer_init': 4, 'safetensors_load': 2, 'module_load_state_dict': 2}.items():
        if type(calls.get(key)) is not int or calls[key] != expected:
            raise ValueError('exact actual source, support and baseline decode observations required: ' + key)
    if calls.get('autograd_grad', 0) != 0 or any(calls.get(key, 0) for key in ('safetensors_save', 'safetensors_save_file')):
        raise ValueError('undeclared numerical or serialization call')
    if result['initial_source_state_sha256'] != result['independent_initial_state_sha256']:
        raise ValueError('canonical independently reconstructed seeded lineage differs')
    collection, _ = M.document(OUT / 'partial-collection.json', canonical_raw=True)
    content = dict(collection)
    collection_sha = content.pop('sha256')
    if logical(content) != collection_sha:
        raise ValueError('partial continuation logical SHA differs')
    M.old.fields(collection, {'expected_folds': 102, 'accepted_folds': 2, 'pending_folds': 100,
        'full_gradient_updates': 5253, 'full_source_updates': 5151, 'full_support_updates': 102,
        'executed_source_updates': 100, 'executed_support_updates': 2, 'executed_gradient_updates': 102,
        'fresh_final_source_updates_required': 51, 'complete': False, 'selected_candidate': None,
        'full_selector_qualified': False, 'final_fit_qualified': False, 'publication_qualified': False,
        'reuse_authorized': False, 'method_config_sha256': logical(method),
        'contract_sha256': result['contract_sha256'], 'template_state_sha256': result['template_state_sha256'],
        'initial_state_sha256': result['initial_source_state_sha256'],
        'input_identity_sha256': result['input_identity_sha256'], 'lineage_recipe_sha256': result['model_recipe_sha256']})
    if len(collection['full_roster']) != 102 or len({(row['candidate'], row['validation_subject']) for row in collection['full_roster']}) != 102:
        raise ValueError('exact complete distinct future fold roster required')
    for index, name in enumerate(('lr_1e-3', 'lr_2e-3'), 1):
        record, record_sha = M.document(OUT / f'fold_{index:02d}.json', canonical_raw=True)
        envelope = dict(record)
        declared_sha = envelope.pop('sha256')
        if logical(envelope) != declared_sha:
            raise ValueError('raw public fold envelope SHA differs')
        payload = record['payload']
        M.old.fields(payload, {'complete': False, 'selected_candidate': None,
            'contract_sha256': result['contract_sha256']})
        if logical(payload['contract']) != payload['contract_sha256'] or len(payload['folds']) != 1:
            raise ValueError('one genuine partial fold and matching selector contract required')
        fold = payload['folds'][0]
        fit = fold['source_fit']
        M.old.fields(fold, {'candidate': name, 'validation_subject': 'subject_01'})
        if (fit['training_subjects'] != [f'subject_{s:02d}' for s in range(3, 53)]
                or len(fit['steps']) != 50 or fit['initial_state_sha256'] != result['initial_source_state_sha256']):
            raise ValueError('50 permitted source subjects and exact fresh initialization required')
        previous = fit['initial_state_sha256']
        for number, (step, subject) in enumerate(zip(fit['steps'], fit['training_subjects'], strict=True), 1):
            if (step['step'] != number or step['subject'] != subject or step['subject_step'] != 1
                    or len(step['trial_ids']) != 2 or len(set(step['trial_ids'])) != 2
                    or not math.isfinite(step['loss']) or step['state_sha256_after'] == previous):
                raise ValueError('actual source history differs from the bounded ordered fit')
            previous = step['state_sha256_after']
        if previous != fit['fitted_state_sha256'] or fold['adapted_state_sha256'] == previous:
            raise ValueError('source and support state changes must be genuine')
        matrix = fold['confusion_matrix']
        score = sum((Fraction(matrix[n][n], sum(matrix[n])) for n in range(2)), Fraction()) / 2
        if fold['balanced_accuracy'] != [score.numerator, score.denominator]:
            raise ValueError('actual per-fold rational balanced accuracy differs')
        pin = result['fold_evidence'][index - 1]
        M.old.fields(pin, {'candidate': name, 'file_sha256': record_sha, 'evidence_sha256': declared_sha,
            'public_refusal_reason': 'selection evidence has missing or unexpected fields'})
    observations, _ = M.document(OUT / 'optimizer-observations.json', canonical_raw=True)
    if len(observations['events']) != 102 or observations['events'] != result['optimizer_updates']:
        raise ValueError('actual 102-update optimizer transcript differs')
    fixture = Path(result['fixture_root'])
    identity, _ = M.document(Path(result['input_identity_path']), expected=result['input_identity_file_sha256'], canonical_raw=True)
    if len(identity['files']) != 213:
        raise ValueError('exact 213 physical synthetic input identities required')
    total = 0
    for relative, pin in identity['files'].items():
        path = PurePosixPath(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('direct synthetic relative input path required')
        _, actual = M.remember(fixture.joinpath(*path.parts), expected=pin['sha256'])
        if actual[2] != pin['size_bytes']:
            raise ValueError('physical input byte count differs')
        total += actual[2]
    if total != 734579463:
        raise ValueError('exact full-shape synthetic input bytes required')
    protected = result['protected_outer_paths']
    M.old.fields(q, {'protected_target_transitions': [{'enabled': value, 'paths': protected} for value in (True, False)],
        'protected_target_read_attempts': []})
    for path, sha in q['observed_loaded_module_hashes'].items():
        if M.old.inspect(Path(path), single_link=False)[1][-1] != sha:
            raise ValueError('observed lineage module drift')
    M.verify_pin_map(pins)
    M.launcher._job_absent(native['job_name'])
    archive = ROOT / 'evidence/cho51-linear-lineage-20261015'
    if archive.exists():
        raise ValueError('unused linear lineage archive required')
    sources = {ROOT / name for name in pins['reviewed_files']}
    sources.update(refusal_sources)
    sources.update(RUN / name for name in ('source-review.json', 'pins.json', 'method-config.json',
        'dispatch_001.json', 'dispatch_result_001.json'))
    sources.update(RUN.glob('preflight*.json'))
    sources.update(OUT / name for name in ('qualification.json', 'result.json', 'probe-result.json', 'partial-collection.json',
        'optimizer-observations.json', 'fold_01.json', 'fold_02.json', 'junit.xml', 'pytest.log'))
    sources.add(Path(result['input_identity_path']))
    sources.update(fixture / name for name in ('configs/base.toml', 'configs/benchmark.toml',
        'configs/phase2/protocol.toml', 'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml'))
    sources.update(Path(path) for path in pins['lineage_assets'] if Path(path).suffix.lower() != '.safetensors')
    sources.update((ROOT / 'configs/phase2/forward_parity.toml', ROOT / 'configs/labram_checkpoint_audit.toml'))
    sources.update(path for path in Path(native['native_directory']).iterdir() if path.is_file())
    payloads = [(path, *M.old.inspect(path, compact=True)) for path in sorted(sources)]
    archive.mkdir()
    (archive / 'artifacts').mkdir()
    rows = []
    for index, (path, raw, pin) in enumerate(payloads, 1):
        relative = f'artifacts/{index:04d}_{path.name}'
        with (archive / relative).open('xb') as stream:
            stream.write(raw)
        rows.append({'source': path.relative_to(ROOT).as_posix(), 'path': relative,
            'bytes': len(raw), 'sha256': pin[-1]})
    summary = {'schema': 'cho51_linear_lineage_summary_v1', 'passed': True,
        'closed_utc': datetime.now(timezone.utc).isoformat(), 'pins_sha256': pins_sha,
        'source_context_files': len(pins['files']), 'runtime_files': 5, 'baseline_files': 1,
        'native': native, 'qualification_file_sha256': q_sha, 'probe_result_file_sha256': result_sha,
        'expected_tests': pins['expected_tests'], 'diagnostic_folds': 2,
        'subtests_passed': 23,
        'source_updates': 100, 'support_updates': 2, 'actual_gradient_updates': 102,
        'complete_folds_required': 102, 'pending_folds': 100, 'full_updates_required': 5253,
        'fold_timings_seconds': result['fold_timings_seconds'], 'one_time_setup_seconds': result['one_time_setup_seconds'],
        'baseline_sha256': next(iter(pins['baseline'].values())), 'baseline_bytes': 23299672,
        'baseline_safe_tensors': 221, 'template_state_sha256': result['template_state_sha256'],
        'initial_state_sha256': result['initial_source_state_sha256'], 'model_recipe_sha256': result['model_recipe_sha256'],
        'independent_lineage_verified': True, 'pretrained_baseline_loaded': True,
        'cohort_lineage_verified': False, 'full_selector_verified': False, 'complete': False,
        'selected_candidate': None, 'publication_performed': False, 'recorder_used': False,
        'physical_input_files': 213, 'physical_input_bytes': total,
        'loaded_module_files': len(q['observed_loaded_module_hashes']),
        'measured_cells': 0, 'scientific_admission': False, 'original_case_attempts_remaining': 0,
        'artifacts': len(rows)}
    summary['reporting_refusal_manifest_sha256'] = '426bae32b4ba07cb46ac54038d58f0a46954db94f7920c65a206ed9e2700f4f9'
    M.old.write(archive / 'manifest.json', {'schema': 'cho51_linear_lineage_manifest_v1', 'artifacts': rows})
    M.old.write(archive / 'summary.json', summary)
    with (archive / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('# LaBraM linear baseline lineage and two-fold qualification\n\n'
            'The audited safe baseline and seeded selector initialization match canonical reconstruction. '
            'Both adopted candidates completed one public fold each:100 source+2 support updates. '
            'Raw evidence remains incomplete, without winner, final fit, publication or recorder. '
            'Checkpoint cohort provenance and full selector qualification remain pending.\n\n'
            '[Summary](summary.json), [manifest](manifest.json), '
            '[report](../../docs/phase2/cho51_linear_lineage_qualification_20261015.md).\n')
    for row in rows:
        for path in (archive / row['path'], ROOT / row['source']):
            if M.old.inspect(path, compact=True)[1][-1] != row['sha256']:
                raise ValueError('linear archived/source bytes changed')
    print(json.dumps({'passed': True, 'archive': str(archive), 'artifacts': len(rows),
        'manifest_sha256': M.old.inspect(archive / 'manifest.json')[1][-1],
        'summary_sha256': M.old.inspect(archive / 'summary.json')[1][-1]}))


if __name__ == '__main__':
    main()
