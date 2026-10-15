"""Strict metadata-only closeout for eight new, explicitly adopted linear folds."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = RUN / 'validation_001'
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_continuation_v1'
PRIOR = ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2'
PRIOR_SHA256 = '9d5c2da133dc1119304fe1e2219fef3d292d277fd4287bcceb019451f8cc30ca'
METADATA = ROOT / 'runs/coordination/cho51_staged_restore_20261015_v1/metadata.py'
METADATA_SHA256 = 'b6aa21ab7d56724c04c5c96d60259b5aed9f1174ca0c05ae82479716bfbf36df'
ARCHIVE = ROOT / 'evidence/cho51-linear-continuation-20261015'
TEMPLATE = '90a9d34ecba2aa96a942f7bd70724f63c2071042141935dbbcd78e0b373b89a7'
CONTRACT = '8397d34ee0a2280b406071e045988f98b1b73ce21fcecc0b9834518cd21993b1'
RECIPE = 'bdb40fd0f3becf87cc619e87a536ee4a921e72efa422fcaaf235c3573865a452'
INPUT = '4abdfea1f6f9ee8a29782b30723e288bf490ffcb7a8c02bf962704bb68d5b1c0'
BASELINE = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
PAIRS = tuple((candidate, f'subject_{number:02d}')
    for candidate in ('lr_1e-3', 'lr_2e-3') for number in range(3, 7))


def load(name, path, expected_sha256):
    with path.open('rb') as stream:
        observed = hashlib.file_digest(stream, 'sha256').hexdigest()
    if observed != expected_sha256:
        raise ValueError('independently pinned metadata source changed: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


M = load('_linear_continuation_frozen_metadata', METADATA, METADATA_SHA256)


def logical(value):
    return hashlib.sha256(M.old.canonical(value)).hexdigest()


def pinned_document(path, *, expected=None, canonical=True):
    return M.document(Path(path), expected=expected, canonical_raw=canonical)


def validate_observations(value, result):
    M.old.fields(value, {'schema': 'cho51_linear_continuation_optimizer_observations_v1',
        'actual_gradient_updates': 408,
        'source_gradient_updates': 400, 'support_gradient_updates': 8,
        'head_parameter_count': 402, 'head_tensor_count': 2,
        'frozen_backbone_sha256': result['backbone_state_sha256'],
        'engineering_only': True, 'scientific_admission': False})
    events = value.get('events')
    if type(events) is not list or len(events) != 408 or events != result['optimizer_updates']:
        raise ValueError('actual 408-event numerical transcript differs from the persisted probe')
    for fold_index, (candidate, validation) in enumerate(PAIRS):
        training = [f'subject_{number:02d}' for number in range(1, 53)
            if number != 2 and f'subject_{number:02d}' != validation]
        if len(training) != 50 or 'subject_01' not in training:
            raise ValueError('complete permitted source roster required')
        for local_index, subject in enumerate((*training, validation), 1):
            index = fold_index * 51 + local_index
            row = events[index - 1]
            M.old.fields(row, {'update': index, 'fold_update': local_index,
                'candidate': candidate, 'validation_subject': validation, 'subject': subject,
                'role': 'source' if local_index <= 50 else 'inner_validation_support',
                'selected_parameters': 402, 'selected_tensors': 2,
                'learning_rate': .001 if candidate == 'lr_1e-3' else .002,
                'finite_selected_gradients': True, 'finite_selected_parameters': True,
                'frozen_backbone_and_buffers_unchanged': True})
            before, after = row['selected_state_sha256_before'], row['selected_state_sha256_after']
            M.old.sha(before)
            M.old.sha(after)
            if before == after:
                raise ValueError('every actual selected SGD update must change head bytes')


def verify_inputs(result):
    fixture = PRIOR / 'validation_001/fixture'
    if result['fixture_root'] != str(fixture):
        raise ValueError('only the exact accepted read-only synthetic fixture may be used')
    path = fixture / 'synthetic-input-identity.json'
    identity, _ = pinned_document(path, expected=result['input_identity_file_sha256'])
    content = dict(identity)
    declared = content.pop('sha256')
    if declared != INPUT or logical(content) != INPUT or result['input_identity_sha256'] != INPUT:
        raise ValueError('exact external synthetic logical identity required')
    if len(identity.get('files', {})) != 213:
        raise ValueError('exact 213-file physical synthetic input map required')
    actual_paths = {path.relative_to(fixture).as_posix()
        for directory in (fixture / 'configs', fixture / 'data')
        for path in directory.rglob('*') if path.is_file() or path.is_symlink()}
    if actual_paths != set(identity['files']):
        raise ValueError('read-only fixture physical input inventory changed')
    total = 0
    for relative, pin in identity['files'].items():
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or '..' in relative_path.parts or '\\' in relative:
            raise ValueError('direct synthetic relative input path required')
        _, actual = M.remember(fixture.joinpath(*relative_path.parts), expected=pin['sha256'])
        if actual[2] != pin['size_bytes']:
            raise ValueError('read-only synthetic input byte count differs')
        total += actual[2]
    if total != 734579463:
        raise ValueError('full-shape synthetic input bytes changed')
    return fixture, identity, total


def main():
    if ARCHIVE.exists():
        raise ValueError('unused continuation evidence directory required')
    if M.old.source_check(ROOT) != M.CANONICAL:
        raise ValueError('canonical source changed')
    pins, pins_sha = pinned_document(RUN / 'pins.json')
    prior, _ = pinned_document(PRIOR / 'pins.json', expected=PRIOR_SHA256)
    M.old.fields(pins, {'schema': 'cho51_linear_continuation_pins_v1',
        'canonical_source_sha256': M.CANONICAL, 'canonical_files': 432,
        'predecessor_files': 1047, 'predecessor_pins_sha256': PRIOR_SHA256,
        'seconds': 600, 'process_mib': 4096, 'job_mib': 5120,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20, 'threads': 1,
        'actual_gradient_updates': 408, 'source_updates': 400, 'support_updates': 8,
        'diagnostic_folds': 8, 'historical_gradient_updates': 102,
        'adopted_historical_folds': 2, 'combined_folds': 10, 'pending_folds': 92,
        'combined_described_gradient_updates': 510, 'required_selection_updates': 5253,
        'expected_tests': 37, 'expected_subtests': 23,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    if (len(prior['files']) != 1047 or len(prior['runtime']) != 5
            or pins['runtime'] != prior['runtime'] or len(pins['runtime']) != 5
            or any(pins['files'].get(path) != sha for path, sha in prior['files'].items())):
        raise ValueError('all exact accepted predecessor source/runtime pins must remain unchanged')
    M.verify_pin_map(pins)
    for path, sha in pins['baseline'].items():
        _, pin = M.remember(Path(path), expected=sha)
        if sha != BASELINE or pin[2] != 23299672:
            raise ValueError('exact audited safe baseline required, hashed without decoding')
    if len(pins['baseline']) != 1:
        raise ValueError('one exact audited safe baseline required')
    review, _ = pinned_document(RUN / 'source-review.json', expected=pins['source_review_sha256'], canonical=False)
    M.old.fields(review, {'source_only': True, 'remaining_actionable_findings': [], 'files': pins['reviewed_files']})
    if len(review['files']) != 12:
        raise ValueError('all twelve reviewed continuation sources required')
    for relative, sha in review['files'].items():
        if pins['files'].get(relative) != sha:
            raise ValueError('reviewed source is absent from fresh exact pins')
    origin, origin_sha = pinned_document(RUN / 'origin-contract.json', expected=pins['origin_contract_file_sha256'], canonical=False)
    origin_module = load('_linear_continuation_origin_closeout', CANDIDATE / 'origin.py',
        pins['files'][(CANDIDATE / 'origin.py').relative_to(ROOT).as_posix()])
    origin_module.verify_origin(origin, ROOT)
    C = load('_linear_continuation_contract_closeout', CANDIDATE / 'contract.py',
        pins['files'][(CANDIDATE / 'contract.py').relative_to(ROOT).as_posix()])
    method, _ = pinned_document(RUN / 'method-config.json', expected=pins['method_config_file_sha256'])
    previous_method, _ = pinned_document(PRIOR / 'method-config.json')
    if method != previous_method:
        raise ValueError('unchanged adopted linear method configuration required')
    dispatch, _ = pinned_document(RUN / 'dispatch_001.json', canonical=False)
    dispatched, _ = pinned_document(RUN / 'dispatch_result_001.json', canonical=False)
    M.old.fields(dispatch, {'schema': 'cho51_linear_continuation_dispatch_v1'})
    M.old.fields(dispatched, {'schema': 'cho51_linear_continuation_dispatch_result_v1'})
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'child.py'),
        '--pins', str(RUN / 'pins.json'), '--expect-pins', pins_sha, '--output', str(OUT)]
    for value in (dispatch, dispatched):
        M.old.fields(value, {'pins_sha256': pins_sha, 'child_command': command,
            'expected_output': str(OUT), 'scientific_admission': False})
    M.old.fields(dispatched, {'guard_exit_code': 0})
    operations, runtimes = M.native_pins(pins)
    native = M.old.verify_native(Path(dispatched['native_directory']), command, 600, 4096, 5120,
        operations=operations, runtimes=runtimes, document=M.document, remember=M.remember, launcher=M.launcher)
    q, q_sha = pinned_document(OUT / 'qualification.json')
    M.old.fields(q, {'schema': 'cho51_linear_continuation_qualification_v1', 'passed': True,
        'pins_sha256': pins_sha, 'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': 5,
        'canonical_source_sha256': M.CANONICAL, 'canonical_files': 432,
        'source_review_sha256': pins['source_review_sha256'], 'torch_threads': 1,
        'torch_interop_threads': 1, 'gpu_hidden': True, 'unexpected_denials': 0,
        'source_updates': 400, 'support_updates': 8, 'actual_gradient_updates': 408,
        'historical_gradient_updates': 102, 'adopted_historical_folds': 2,
        'combined_folds': 10, 'pending_folds': 92, 'combined_described_gradient_updates': 510,
        'baseline_pins_rechecked': 1, 'baseline_file_sha256': BASELINE,
        'actual_study_data_used': False, 'cohort_lineage_verified': False,
        'full_selector_verified': False, 'full_worker_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    result, result_sha = pinned_document(OUT / 'probe-result.json')
    child, _ = pinned_document(OUT / 'result.json')
    if q['result'] != child or child['probe'] != result:
        raise ValueError('native qualification must bind both persisted actual wrapper and probe')
    M.old.fields(child, {'schema': 'cho51_linear_continuation_child_result_v1', 'passed': True,
        'tests_passed': True, 'pytest_exit': 0, 'collected_tests': 37, 'expected_tests': 37,
        'skipped_reports': [], 'unexpected_reports': [],
        'expected_subtests': 23, 'collected_subtests': 23,
        'actual_gradient_updates': 408, 'source_updates': 400, 'support_updates': 8,
        'diagnostic_folds': 8, 'historical_gradient_updates': 102,
        'adopted_historical_folds': 2, 'combined_folds': 10, 'pending_folds': 92,
        'combined_described_gradient_updates': 510, 'required_selection_updates': 5253,
        'pretrained_baseline_loaded': True, 'cohort_lineage_verified': False,
        'full_selector_verified': False, 'full_worker_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    for field, count in (('reports', 37), ('subtest_reports', 23)):
        if len(child[field]) != count or any(row['phase'] != 'call' or row['outcome'] != 'passed' for row in child[field]):
            raise ValueError('all exact parent and subtest reports must separately pass')
    M.old.fields(result, {'schema': 'cho51_linear_continuation_probe_v1', 'passed': True,
        'method': 'labram_linear', 'actual_gradient_updates': 408,
        'source_gradient_updates': 400, 'support_gradient_updates': 8,
        'diagnostic_folds': 8, 'adopted_historical_folds': 2, 'combined_folds': 10,
        'pending_folds': 92, 'combined_described_gradient_updates': 510,
        'required_selection_updates': 5253, 'input_file_count': 213, 'input_bytes': 734579463,
        'method_config_sha256': logical(method), 'contract_sha256': CONTRACT,
        'template_state_sha256': TEMPLATE, 'initial_source_state_sha256': TEMPLATE,
        'model_recipe_sha256': RECIPE, 'input_identity_sha256': INPUT,
        'pretrained_baseline_loaded': True, 'cohort_lineage_verified': False,
        'source_subjects_available': 52, 'adopted_evaluation_targets': 51, 'adopted_case_plan_count': 1020,
        'outer_target': 'subject_02', 'validation_subjects': [f'subject_{number:02d}' for number in range(3, 7)],
        'current_pairs': [list(pair) for pair in PAIRS], 'historical_source_updates': 100,
        'historical_support_updates': 2, 'historical_gradient_updates': 102,
        'template_parameter_count': 5818138, 'selected_parameter_names': ['head.weight', 'head.bias'],
        'selected_parameter_count': 402, 'selected_tensor_count': 2,
        'full_backbone_blocks': 12, 'full_backbone_embed_dim': 200,
        'baseline_safe_tensor_count': 221, 'baseline_safe_elements': 5819936,
        'independent_lineage_verified': True, 'independent_storage_verified': True,
        'supplied_template_unchanged': True, 'fixture_source_context_unchanged': True,
        'finite_losses_gradients_parameters': True, 'canonical_source_exclusion_verified': True,
        'actual_public_run_fold': True, 'pretrained_weights_loaded': True,
        'prior_template_training_verified': False, 'canonical_private_lineage_constructor_exercised': True,
        'public_selected_source_restore_exercised': False, 'full_selection_attempted': False,
        'origin_sha256': logical(origin), 'original_native_origin_verified': True,
        'source_work_reused': True, 'reused_historical_folds': 2, 'old_fixture_read_only': True,
        'incomplete_finalization_refused_before_fit': True, 'incomplete_finalization_refusal_count': 2,
        'final_source_updates': 0, 'complete_native_origins_capability_exercised': False,
        'final_numerical_branch_qualified': False, 'logical_complete_scope_checked': True,
        'public_complete_selector_verifier_refused': True,
        'public_refusal_reason': 'selection evidence has missing or unexpected fields',
        'refusal_boundary': 'raw_incomplete_diagnostic_payload_schema',
        'all_physical_inputs_rehashed_unchanged': True, 'source_backbone_and_buffers_unchanged': True,
        'torch_numpy_python_rng_unchanged': True, 'complete': False, 'selected_candidate': None,
        'full_selector_verified': False, 'full_worker_verified': False,
        'publication_performed': False, 'recorder_used': False, 'measured_cells': 0,
        'synthetic': True, 'actual_study_data_loaded': False,
        'engineering_only': True, 'scientific_admission': False, 'original_case_attempts_remaining': 0})
    calls = q['observed_numerical_calls']
    for key, count in {'tensor_backward': 408, 'autograd_backward': 408, 'sgd_step': 408,
            'optimizer_init': 16, 'safetensors_load': 2, 'module_load_state_dict': 2}.items():
        if type(calls.get(key)) is not int or calls[key] != count:
            raise ValueError('exact current numerical calls required: ' + key)
    if calls.get('autograd_grad', 0) != 0 or any(calls.get(key, 0) for key in (
            'safetensors_save', 'safetensors_save_file', 'safetensors_serialize', 'safetensors_serialize_file')):
        raise ValueError('no undeclared gradient or serialized state work permitted')
    raw_records = []
    fold_sources = []
    timings = result['fold_timings_seconds']
    if (type(timings) is not list or len(timings) != 8
            or any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0 for value in timings)
            or type(result['one_time_setup_seconds']) not in (int, float)
            or not math.isfinite(result['one_time_setup_seconds']) or result['one_time_setup_seconds'] <= 0):
        raise ValueError('eight finite positive measured fold intervals and setup interval required')
    if len(result.get('fold_evidence', [])) != 8:
        raise ValueError('eight physical raw fold witnesses required')
    for index, pair in enumerate(PAIRS, 1):
        path = OUT / f'fold_{index:02d}.json'
        record, file_sha = pinned_document(path)
        fold = record['payload']['folds'][0]
        if (fold['candidate'], fold['validation_subject']) != pair:
            raise ValueError('exact new eight-fold candidate/validation execution order required')
        raw_records.append(record)
        fold_sources.append(path)
        pin = result['fold_evidence'][index - 1]
        M.old.fields(pin, {'candidate': pair[0], 'validation_subject': pair[1],
            'path': str(path), 'file_sha256': file_sha, 'evidence_sha256': record['sha256'],
            'public_refusal_reason': 'selection evidence has missing or unexpected fields'})
        if pin['size_bytes'] != M.old.inspect(path)[1][2] or pin['elapsed_seconds'] != timings[index - 1]:
            raise ValueError('raw fold size or measured interval differs from its physical witness')
    old_records = [pinned_document(PRIOR / f'validation_001/fold_{index:02d}.json')[0] for index in (1, 2)]
    combined = C.collect_partial((*old_records, *raw_records), method,
        input_identity_sha256=INPUT, template_state_sha256=TEMPLATE,
        initial_state_sha256=TEMPLATE, lineage_recipe_sha256=RECIPE)
    collection, collection_sha = pinned_document(OUT / 'partial-collection.json')
    if combined != collection:
        raise ValueError('combined ten-fold manifest differs from complete independent raw-fold validation')
    M.old.fields(collection, {'expected_folds': 102, 'accepted_folds': 10, 'pending_folds': 92,
        'executed_source_updates': 500, 'executed_support_updates': 10, 'executed_gradient_updates': 510,
        'fresh_final_source_updates_required': 51, 'complete': False, 'selected_candidate': None,
        'final_fit_ready': False, 'full_selector_qualified': False,
        'final_fit_qualified': False, 'publication_qualified': False,
        'reuse_authorized': False, 'origin_reuse_verified': False,
        'contract_sha256': CONTRACT, 'template_state_sha256': TEMPLATE, 'initial_state_sha256': TEMPLATE})
    observations, _ = pinned_document(OUT / 'optimizer-observations.json')
    validate_observations(observations, result)
    for field, filename in (('partial_collection', 'partial-collection.json'),
            ('optimizer_observations', 'optimizer-observations.json'),
            ('finalization_refusals', 'finalization-refusals.json')):
        path = OUT / filename
        _, actual = M.remember(path, compact=True)
        M.old.fields(result[field], {'path': str(path), 'file_sha256': actual[-1], 'size_bytes': actual[2]})
    refusals, refusal_sha = pinned_document(OUT / 'finalization-refusals.json')
    expected_refusals = [{'stage': stage, 'records': records,
        'reason': 'all 102 distinct canonical folds are required before a fresh final source fit',
        'observed_updates_before': updates, 'observed_updates_after': updates,
        'before_fit': True, 'origin_capability_called': False}
        for stage, records, updates in (('before_new_folds', 2, 0), ('after_combined_ten_folds', 10, 408))]
    M.old.fields(refusals, {'schema': 'cho51_linear_continuation_finalization_refusals_v1',
        'refusals': expected_refusals, 'actual_final_source_updates': 0,
        'complete_native_origins_capability_exercised': False, 'final_numerical_branch_qualified': False}, exact=True)
    if len(result.get('original_fold_evidence', [])) != 2:
        raise ValueError('two distinct independently authenticated historical fold witnesses required')
    for index, pin in enumerate(result['original_fold_evidence']):
        path = PRIOR / f'validation_001/fold_{index + 1:02d}.json'
        _, actual = M.remember(path, expected=origin['original_fold_file_sha256'][index], compact=True)
        M.old.fields(pin, {'path': str(path), 'file_sha256': actual[-1], 'size_bytes': actual[2],
            'identity': list(actual[:-1]), 'read_limit_bytes': 8 * 1024**2})
    for field, size, limit in (('baseline_config', 4776, 1024**2),
            ('baseline_weights', 23299672, 32 * 1024**2)):
        pin = result[field]
        path = Path(pin['path'])
        _, actual = M.remember(path, expected=pin['file_sha256'])
        M.old.fields(pin, {'size_bytes': size, 'read_limit_bytes': limit, 'identity': list(actual[:-1])})
        if pins['lineage_assets'][str(path)] != {'bytes': size, 'sha256': actual[-1]}:
            raise ValueError('actual bounded baseline witness differs from current independent asset pins')
    fixture, identity, input_bytes = verify_inputs(result)
    protected = [str(fixture / relative) for relative in (
        'data/processed/cho2017/profile_a/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
        'data/raw/moabb/cho2017/subject_02.mat')]
    M.old.fields(q, {'protected_target_transitions': [{'enabled': value, 'paths': protected} for value in (True, False)],
        'protected_target_read_attempts': []})
    for path in protected:
        if q.get('fixture_input_read_phases', {}).get(path, {}).get('during_computation', 0) != 0:
            raise ValueError('outer target contents read during protected computation')
    connection = '.venv/Lib/site-packages/urllib3/util/connection.py'
    expected_denial = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
        'source_file': str(ROOT / connection), 'source_sha256': pins['files'][connection]}
    M.old.fields(q, {'denied_operations': [expected_denial], 'expected_blocked_ipv6_probes': 1})
    if type(q.get('observed_loaded_module_hashes')) is not dict or not q['observed_loaded_module_hashes']:
        raise ValueError('nonempty post-import module hash observations required')
    if q['loaded_module_files'] != len(q['observed_loaded_module_hashes']):
        raise ValueError('observed current module inventory count differs')
    for path, sha in q['observed_loaded_module_hashes'].items():
        if M.old.inspect(Path(path), single_link=False)[1][-1] != sha:
            raise ValueError('observed current module byte drift')
    sources = {ROOT / name for name in pins['reviewed_files']}
    sources.update(RUN / name for name in ('pins.json', 'source-review.json', 'method-config.json',
        'origin-contract.json', 'dispatch_001.json', 'dispatch_result_001.json'))
    sources.update(RUN.glob('preflight*.json'))
    sources.update(OUT / name for name in ('qualification.json', 'result.json', 'probe-result.json',
        'partial-collection.json', 'optimizer-observations.json', 'finalization-refusals.json',
        'junit.xml', 'pytest.log'))
    sources.update(fold_sources)
    sources.add(fixture / 'synthetic-input-identity.json')
    for relative, sha in origin['proofs'].items():
        path = ROOT.joinpath(*PurePosixPath(relative).parts)
        M.remember(path, expected=sha, compact=True)
        sources.add(path)
    sources.update(Path(path) for path in pins['lineage_assets'] if Path(path).suffix.lower() != '.safetensors')
    sources.update(path for path in Path(native['native_directory']).iterdir() if path.is_file())
    forbidden = {'.npz', '.npy', '.mat', '.edf', '.gdf', '.fif', '.set', '.pt', '.pth', '.ckpt', '.safetensors'}
    payloads = []
    for path in sorted(sources):
        if not path.is_relative_to(ROOT) or path.suffix.lower() in forbidden:
            raise ValueError('archive accepts compact repository metadata only, never arrays or weights')
        raw, pin = M.remember(path, compact=True)
        payloads.append((path, raw, pin))
    M.verify_pin_map(pins)
    origin_module.verify_origin(origin, ROOT)
    M.launcher._job_absent(native['job_name'])
    for path, _, pin in payloads:
        if M.old.inspect(path, compact=True)[1] != pin:
            raise ValueError('compact source proof identity changed before archival')
    ARCHIVE.mkdir()
    (ARCHIVE / 'artifacts').mkdir()
    rows = []
    for index, (path, raw, pin) in enumerate(payloads, 1):
        suffix = path.suffix.lower() if path.suffix else '.txt'
        relative = f'artifacts/a{index:04d}{suffix}'
        with (ARCHIVE / relative).open('xb') as stream:
            stream.write(raw)
        rows.append({'source': path.relative_to(ROOT).as_posix(), 'path': relative,
            'bytes': len(raw), 'sha256': pin[-1]})
    summary = {'schema': 'cho51_linear_continuation_summary_v1', 'passed': True,
        'closed_utc': datetime.now(timezone.utc).isoformat(), 'pins_sha256': pins_sha,
        'source_context_files': len(pins['files']), 'runtime_files': 5, 'reviewed_sources': 12,
        'predecessor_pins_sha256': PRIOR_SHA256, 'origin_contract_file_sha256': origin_sha,
        'native': native, 'qualification_file_sha256': q_sha, 'probe_result_file_sha256': result_sha,
        'partial_collection_file_sha256': collection_sha,
        'finalization_refusals_file_sha256': refusal_sha,
        'main_tests_passed': 37, 'subtests_passed': 23,
        'current_folds': 8, 'current_source_updates': 400, 'current_support_updates': 8,
        'current_gradient_updates': 408, 'historical_folds_adopted': 2,
        'historical_gradient_updates': 102, 'combined_folds': 10,
        'combined_described_gradient_updates': 510, 'complete_folds_required': 102,
        'pending_folds': 92, 'fresh_final_source_updates_required': 51,
        'full_updates_required': 5253, 'baseline_sha256': BASELINE, 'baseline_bytes': 23299672,
        'fold_timings_seconds': timings, 'one_time_setup_seconds': result['one_time_setup_seconds'],
        'incomplete_finalization_refusals': 2, 'additional_finalization_gradient_updates': 0,
        'actual_complete_origin_capability_exercised': False, 'final_numerical_branch_qualified': False,
        'template_state_sha256': TEMPLATE, 'initial_state_sha256': TEMPLATE,
        'contract_sha256': CONTRACT, 'model_recipe_sha256': RECIPE,
        'physical_input_files': 213, 'physical_input_bytes': input_bytes,
        'historical_loaded_module_files_verified': 4818,
        'current_loaded_module_files_verified': len(q['observed_loaded_module_hashes']),
        'historical_origins_independently_authenticated': True,
        'historical_archive_source_pairs_verified': [91, 26],
        'historical_native_proofs': origin['native_proofs'],
        'historical_gradient_updates_executed_in_current_child': 0,
        'partial_manifest_reuse_authorized': False, 'complete': False, 'selected_candidate': None,
        'actual_final_fit_executed': False, 'full_selector_verified': False,
        'full_worker_verified': False, 'publication_performed': False, 'recorder_used': False,
        'cohort_lineage_verified': False, 'measured_cells': 0,
        'scientific_admission': False, 'original_case_attempts_remaining': 0,
        'artifacts': len(rows)}
    M.old.write(ARCHIVE / 'manifest.json', {'schema': 'cho51_linear_continuation_manifest_v1', 'artifacts': rows})
    M.old.write(ARCHIVE / 'summary.json', summary)
    with (ARCHIVE / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('# Bounded LaBraM linear continuation qualification\n\n'
            'Eight new genuine public folds performed400 source and8 support updates. '
            'The separately authenticated two historical folds account for102 earlier updates. '
            'Combined coverage is10/102 folds with92 pending. Incomplete finalization refused '
            'before any additional fitting; no final source model, winner, publication or measured cell exists. '
            'Future chunks and a fresh51-source final fit require independent admission and full native origins.\n\n'
            '[Summary](summary.json), [manifest](manifest.json), '
            '[report](../../docs/phase2/cho51_linear_continuation_qualification_20261015.md).\n')
    for row in rows:
        for path in (ARCHIVE / row['path'], ROOT / row['source']):
            pin = M.old.inspect(path, compact=True)[1]
            if pin[-1] != row['sha256'] or pin[2] != row['bytes']:
                raise ValueError('archived/source compact proof bytes changed')
    for path, before in tuple(M.observed.items()):
        if M.old.inspect(Path(path))[1] != before:
            raise ValueError('physical input, baseline or proof identity changed during closeout')
    for path, sha in q['observed_loaded_module_hashes'].items():
        if M.old.inspect(Path(path), single_link=False)[1][-1] != sha:
            raise ValueError('observed current module changed during closeout')
    M.verify_pin_map(pins)
    M.launcher._job_absent(native['job_name'])
    print(json.dumps({'passed': True, 'archive': str(ARCHIVE), 'artifacts': len(rows),
        'manifest_sha256': M.old.inspect(ARCHIVE / 'manifest.json')[1][-1],
        'summary_sha256': M.old.inspect(ARCHIVE / 'summary.json')[1][-1]}))


if __name__ == '__main__':
    main()
