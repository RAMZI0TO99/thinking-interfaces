"""Read-only authentication of the two completed, independently guarded stages.

Only frozen standard-library metadata helpers are imported. No model, array,
recorder, process launcher, or numerical implementation is imported or executed.
The failed original transaction remains immutable and unsuccessful.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path, PurePosixPath

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
STAGE = ROOT / 'runs/coordination/cho51_staged_restore_20261015_v1'
RESTORE_PINS_SHA = 'ebd67a1d9bc2807ada7bd73689e41b14fd393b4410f30b00c08af8b26c69332f'
RESTORE_CONTRACT_SHA = '0736f8f40446ea32c6727f9a8e6cd68e29457774b63ce8b9fc56d5fcb51b7b66'
RESTORE_FINAL_SHA = '7bf523c6c7b6a644839a139ba9bf19fefcd0d280634e2ccf5fe5f2ea0a49d370'
RESTORE_NATIVE = ROOT / 'runs/migration/20261015T134051Z_91181dffde'
ARCHIVE = ROOT / 'evidence/cho51-staged-eegnet-restore-20261015'
ARCHIVE_MANIFEST_SHA = '37183638171c59f4f3bcacf02421ddd1b0426c7d13a5dcf062657cc29a7858a5'
ARCHIVE_SUMMARY_SHA = '7abe328c7a2880e197e48e1d0fdcef539810dc7cd2377e3cc4060da984e6cf87'


def _load_metadata():
    name = '_cho51_staged_recorder_frozen_origin_metadata'
    spec = importlib.util.spec_from_file_location(name, STAGE / 'metadata.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


M = _load_metadata()


def _relative(base, value):
    path = PurePosixPath(value)
    if (type(value) is not str or path.is_absolute() or '..' in path.parts
            or '\\' in value or path.as_posix() != value):
        raise ValueError('direct canonical relative archive path required')
    return base.joinpath(*path.parts)


def _compact_files(observed):
    files = {}
    for value, expected in observed.items():
        path = Path(value)
        if path.suffix.lower() in {'.npz', '.npy', '.mat'}:
            continue
        _, pin = M.old.inspect(path, compact=True)
        if pin[-1] != expected:
            raise ValueError('origin compact evidence changed: ' + str(path))
        files[str(path)] = expected
    return dict(sorted(files.items()))


def verify_origin_stages():
    """Authenticate completed source and restore stages without replaying them.

    The returned map binds compact single-link proof files, including actual
    weights. Large synthetic arrays are rehashed by the frozen origin verifier
    but excluded from the returned contract. Its summary is the complete static
    backend result; callers must compare both returned maps exactly.
    """
    origin = M.verify_origin()
    pins, pins_sha = M.document(STAGE / 'pins.json', expected=RESTORE_PINS_SHA)
    if len(pins['files']) != 798 or len(pins['runtime']) != 5:
        raise ValueError('exact staged 798 source and five runtime pins required')
    M.old.fields(pins, {'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
        'threads': 1, 'gpu_hidden': True, 'seconds': 90, 'process_mib': 2048,
        'job_mib': 3072, 'scientific_admission': False})
    M.verify_pin_map(pins)
    contract, contract_sha = M.document(STAGE / 'stage-contract.json', expected=RESTORE_CONTRACT_SHA)
    M.old.fields(pins, {'stage_contract_sha256': contract_sha})
    M.check_contract(contract, origin)
    review, _ = M.document(STAGE / 'source-review.json', expected=pins['source_review_sha256'])
    M.old.fields(review, {'schema': 'cho51_staged_eegnet_restore_source_review_v1',
        'source_only': True, 'runtime_verified': False, 'remaining_actionable_findings': [],
        'scientific_admission': False, 'source_training_replayed': False,
        'parent_transaction_qualified': False, 'engineering_successes': 0, 'measured_cells': 0,
        'original_case_attempts_remaining': 0})
    for relative, expected in review['files'].items():
        M.remember(_relative(ROOT, relative), expected=expected, compact=True)
    final, _ = M.document(STAGE / 'final-review.json', expected=RESTORE_FINAL_SHA)
    M.old.fields(final, {'metadata_only': True, 'historical_failed_case_unchanged': True,
        'actual_public_restore_limits_bytes': [1048576, 1048576], 'actual_safetensors_loads': 2,
        'actual_strict_state_loads': 2, 'all_tensors_equal': True,
        'archive_source_pairs_rechecked': 189, 'fresh_loaded_modules_rechecked': 3936,
        'historical_source_gradient_updates': 5253, 'current_gradient_updates': 0,
        'fresh_source_runtime_pins_rechecked': [798, 5], 'engineering_successes': 0, 'measured_cells': 0})
    # Document heads legitimately advance. Authenticate this frozen review file,
    # but do not compare its historical document-hash map to current documents.
    for binding in final['evidence'].values():
        M.remember(_relative(ROOT, binding['path']), expected=binding['sha256'], compact=True)
    dispatch, _ = M.document(STAGE / 'dispatch_001.json')
    dispatched, _ = M.document(STAGE / 'dispatch_result_001.json')
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(STAGE / 'verify_child.py'),
        '--pins', str(STAGE / 'pins.json'), '--expect-pins', pins_sha,
        '--contract', str(STAGE / 'stage-contract.json'), '--expect-contract', contract_sha]
    for value in (dispatch, dispatched):
        M.old.fields(value, {'pins_sha256': pins_sha, 'stage_contract_sha256': contract_sha,
            'child_command': command, 'expected_output': str(STAGE / 'verification_001'),
            'source_training_replayed': False, 'scientific_admission': False})
    M.old.fields(dispatched, {'guard_exit_code': 0, 'native_directory': str(RESTORE_NATIVE)})
    operations, runtimes = M.native_pins(pins)
    native = M.old.verify_native(RESTORE_NATIVE, command, 90, 2048, 3072,
        operations=operations, runtimes=runtimes, document=M.document, remember=M.remember, launcher=M.launcher)
    output = STAGE / 'verification_001'
    q, q_sha = M.document(output / 'qualification.json', canonical_raw=True)
    result, result_sha = M.document(output / 'detached-result.json', canonical_raw=True)
    M.old.fields(q, {'schema': 'cho51_staged_eegnet_restore_qualification_v1', 'passed': True,
        'pins_sha256': pins_sha, 'stage_contract_sha256': contract_sha,
        'origin_request_sha256': origin['request_sha'], 'source_publication_reused': True,
        'source_training_replayed': False, 'parent_transaction_qualified': False,
        'engineering_successes': 0, 'measured_cells': 0, 'result': result,
        'source_pins_rechecked': 798, 'runtime_pins_rechecked': 5,
        'source_review_sha256': pins['source_review_sha256'],
        'source_updates': 0, 'support_updates': 0, 'torch_threads': 1, 'torch_interop_threads': 1,
        'gpu_hidden': True, 'unexpected_denials': 0, 'expected_blocked_ipv6_probes': 1,
        'protected_target_read_attempts': [], 'scientific_admission': False,
        'original_case_attempts_remaining': 0})
    calls = q['observed_numerical_calls']
    for key in ('optimizer_init', 'sgd_step', 'tensor_backward', 'autograd_backward', 'autograd_grad'):
        if calls.get(key, 0) != 0:
            raise ValueError('restoration evidence contains fitting')
    if calls.get('safetensors_load') != 2 or calls.get('module_load_state_dict') != 2:
        raise ValueError('both actual public full-state restores required')
    old_result = origin['result']
    M.old.fields(result, {'schema': 'cho51_complete_eegnet_detached_result_v1', 'passed': True,
        'request_sha256': origin['request_sha'], 'pins_sha256': M.ORIGIN_PINS_SHA,
        'claim_file_sha256': origin['request']['claim_file_sha256'],
        'source_result_path': str(origin['result_path']), 'source_result_file_sha256': origin['result_sha'],
        'publication': old_result['publication'], 'publication_files': old_result['publication_files'],
        'publication_witness': old_result['publication_witness'],
        'selected_candidate': old_result['selected_candidate'], 'model_state_sha256': old_result['model_state_sha256'],
        'selection_evidence_sha256': old_result['selection_evidence_sha256'],
        'all_tensors_equal': True, 'full_state_digest_matches': True, 'tensor_count': 21,
        'initial_lineage_reconstructed': True, 'public_restore_adapter_released': True,
        'detached_tensor_verified': True, 'actual_gradient_updates': 0,
        'verified_source_gradient_updates': 5253, 'verified_source_updates': 5151,
        'verified_support_updates': 102, 'verified_fold_count': 102, 'verified_final_source_subjects': 51,
        'all_physical_inputs_rehashed_unchanged': True, 'fixture_source_context_unchanged': True,
        'torch_numpy_python_rng_unchanged': True, 'target_prediction_performed': False,
        'recorder_used': False, 'publication_performed': False, 'measured_cells': 0,
        'actual_study_data_loaded': False, 'pretrained_weights_loaded': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    M.old.fields(result['bounded_store'], {'maximum_weights_bytes': 1048576,
        'actual_weights_bytes': 12664, 'restore_limits_bytes': [1048576, 1048576],
        'generic_restore_default_avoided': True, 'canonical_restore_delegated': True,
        'public_factory_store_injection': True})
    target_paths = [str(Path(origin['request']['fixture_root']) / name) for name in (
        'data/processed/cho2017/profile_a/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
        'data/raw/moabb/cho2017/subject_02.mat')]
    expected_denial = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
        'source_file': str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
        'source_sha256': pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py']}
    M.old.fields(q, {'protected_target_transitions': [{'enabled': enabled, 'paths': target_paths} for enabled in (True, False)],
        'denied_operations': [expected_denial]})
    if any(q['fixture_input_read_phases'].get(path, {}).get('during_computation', 0) != 0 for path in target_paths):
        raise ValueError('protected outer target read during restoration')
    if len(q['observed_loaded_module_hashes']) != 3936:
        raise ValueError('exact 3936 fresh restore module hashes required')
    for path, sha in q['observed_loaded_module_hashes'].items():
        if M.old.inspect(Path(path), single_link=False)[1][-1] != sha:
            raise ValueError('fresh restore loaded module changed: ' + path)
    manifest, _ = M.document(ARCHIVE / 'manifest.json', expected=ARCHIVE_MANIFEST_SHA)
    summary, _ = M.document(ARCHIVE / 'summary.json', expected=ARCHIVE_SUMMARY_SHA)
    M.old.fields(manifest, {'schema': 'cho51_staged_restore_artifact_manifest_v1'})
    if len(manifest['artifacts']) != 189:
        raise ValueError('exact standalone 189 artifact archive required')
    M.old.fields(summary, {'schema': 'cho51_staged_eegnet_restore_summary_v1', 'passed': True,
        'pins_sha256': pins_sha, 'stage_contract_sha256': contract_sha,
        'fresh_native': native, 'origin_native': origin['native'], 'source_work_reused': True,
        'source_training_replayed': False, 'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
        'bounded_restore_runtime_verified': True, 'restore_limits_bytes': [1048576, 1048576],
        'weights_bytes': 12664, 'weights_sha256': old_result['publication']['weights_sha256'],
        'model_state_sha256': old_result['model_state_sha256'], 'tensor_count': 21,
        'all_tensors_equal': True, 'origin_module_files_rechecked': 4719,
        'fresh_module_files_rechecked': 3936, 'physical_input_files_rechecked': 213,
        'physical_input_bytes_rechecked': 734579463, 'parent_transaction_qualified': False,
        'engineering_successes': 0, 'measured_cells': 0, 'scientific_admission': False,
        'original_case_attempts_remaining': 0, 'artifacts': 189})
    for row in manifest['artifacts']:
        for path in (_relative(ROOT, row['source']), _relative(ARCHIVE, row['path'])):
            _, pin = M.remember(path, expected=row['sha256'], compact=True)
            if pin[2] != row['bytes']:
                raise ValueError('standalone archive/source byte count differs')
    observed = {path: pin[-1] for path, pin in M.observed.items()}
    # Revalidate the immutable original ledger and physical inputs at the end;
    # verify_origin clears M.observed, so preserve the staged observations first.
    origin_after = M.verify_origin()
    if origin_after['files'] != origin['files']:
        raise ValueError('origin proof inventory changed during staged verification')
    M.check_contract(contract, origin_after)
    M.verify_pin_map(pins)
    for path, pin in M.observed.items():
        previous = observed.setdefault(path, pin[-1])
        if previous != pin[-1]:
            raise ValueError('origin evidence changed during staged verification')
    files = _compact_files(observed)
    M.launcher._job_absent(native['job_name'])
    result_summary = {
        'engineering_only': True, 'source_work_reused': True, 'restore_work_reused': True,
        'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
        'source_updates': 5151, 'support_updates': 102, 'fold_count': 102, 'final_source_subjects': 51,
        'restore_limits': [1048576, 1048576], 'restored_tensors': 21,
        'selected_state_sha256': old_result['model_state_sha256'],
        'weights_file_sha256': old_result['publication']['weights_sha256'],
        'source_request_sha256': origin['request_sha'],
        'source_claim_file_sha256': origin['request']['claim_file_sha256'],
        'source_pins_sha256': M.ORIGIN_PINS_SHA, 'source_result_file_sha256': origin['result_sha'],
        'source_qualification_file_sha256': origin['q_sha'],
        'source_native_receipt_sha256': origin['native']['receipt_file_sha256'],
        'restore_contract_sha256': contract_sha, 'restore_pins_sha256': pins_sha,
        'restore_result_file_sha256': result_sha, 'restore_qualification_file_sha256': q_sha,
        'restore_native_receipt_sha256': native['receipt_file_sha256'],
        'origin_parent_transaction_qualified': False, 'scientific_admission': False,
        'measured_cells': 0, 'original_case_attempts_remaining': 0,
    }
    return {'files': files, 'summary': result_summary}
