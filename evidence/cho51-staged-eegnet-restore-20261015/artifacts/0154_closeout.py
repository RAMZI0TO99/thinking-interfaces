"""Verify and archive the standalone restore; never execute models or a recorder."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata as M


def main():
    origin = M.verify_origin()
    pins, pins_sha = M.document(M.RUN / 'pins.json')
    M.verify_pin_map(pins)
    contract, contract_sha = M.document(M.RUN / 'stage-contract.json', expected=pins['stage_contract_sha256'])
    M.check_contract(contract, origin)
    dispatch, _ = M.document(M.RUN / 'dispatch_001.json')
    dispatched, _ = M.document(M.RUN / 'dispatch_result_001.json')
    command = [str(M.ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(M.RUN / 'verify_child.py'),
        '--pins', str(M.RUN / 'pins.json'), '--expect-pins', pins_sha,
        '--contract', str(M.RUN / 'stage-contract.json'), '--expect-contract', contract_sha]
    for value in (dispatch, dispatched):
        M.old.fields(value, {'pins_sha256': pins_sha, 'stage_contract_sha256': contract_sha,
            'child_command': command, 'expected_output': str(M.RUN / 'verification_001'),
            'source_training_replayed': False, 'scientific_admission': False})
    M.old.fields(dispatched, {'guard_exit_code': 0})
    operations, runtimes = M.native_pins(pins)
    native = M.old.verify_native(Path(dispatched['native_directory']), command, 90, 2048, 3072,
        operations=operations, runtimes=runtimes, document=M.document, remember=M.remember, launcher=M.launcher)
    output = M.RUN / 'verification_001'
    q, q_sha = M.document(output / 'qualification.json', canonical_raw=True)
    result, result_sha = M.document(output / 'detached-result.json', canonical_raw=True)
    M.old.fields(q, {'schema': 'cho51_staged_eegnet_restore_qualification_v1', 'passed': True,
        'pins_sha256': pins_sha, 'stage_contract_sha256': contract_sha,
        'origin_request_sha256': origin['request_sha'], 'source_publication_reused': True,
        'source_training_replayed': False, 'parent_transaction_qualified': False,
        'engineering_successes': 0, 'measured_cells': 0, 'result': result,
        'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': 5,
        'source_review_sha256': pins['source_review_sha256'],
        'source_updates': 0, 'support_updates': 0, 'torch_threads': 1, 'torch_interop_threads': 1,
        'gpu_hidden': True, 'unexpected_denials': 0, 'expected_blocked_ipv6_probes': 1,
        'protected_target_read_attempts': [], 'scientific_admission': False,
        'original_case_attempts_remaining': 0})
    for key in ('optimizer_init', 'sgd_step', 'tensor_backward', 'autograd_backward', 'autograd_grad'):
        if q['observed_numerical_calls'].get(key, 0) != 0:
            raise ValueError('standalone restore performed fitting')
    calls = q['observed_numerical_calls']
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
        'all_tensors_equal': True, 'full_state_digest_matches': True,
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
        'source_file': str(M.ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
        'source_sha256': pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py']}
    M.old.fields(q, {'protected_target_transitions': [{'enabled': enabled, 'paths': target_paths} for enabled in (True, False)],
        'denied_operations': [expected_denial]})
    if any(q['fixture_input_read_phases'].get(path, {}).get('during_computation', 0) != 0 for path in target_paths):
        raise ValueError('protected outer target read during restoration')
    for path, sha in q['observed_loaded_module_hashes'].items():
        if M.old.inspect(Path(path), single_link=False)[1][-1] != sha:
            raise ValueError('fresh restore loaded module drift')
    # Check all origin identities and current pins again before durable closeout.
    origin_after = M.verify_origin()
    M.check_contract(contract, origin_after)
    M.verify_pin_map(pins)
    for path, sha in ((output / 'qualification.json', q_sha), (output / 'detached-result.json', result_sha)):
        M.remember(path, expected=sha, compact=True)
    M.launcher._job_absent(native['job_name'])
    archive = M.ROOT / 'evidence/cho51-staged-eegnet-restore-20261015'
    if archive.exists():
        raise ValueError('unused staged evidence archive required')
    sources = {M.RUN / name for name in ('metadata.py', 'prepare.py', 'runtime.py', 'verify_child.py',
        'observe.py', 'launch.ps1', 'closeout.py', 'source-review.json', 'stage-contract.json', 'pins.json',
        'dispatch_001.json', 'dispatch_result_001.json')}
    sources.update(M.RUN.glob('preflight*.json'))
    sources.update((output / 'qualification.json', output / 'detached-result.json'))
    sources.update((M.ROOT / 'docs/phase2/cho51_staged_restore_v1').iterdir())
    for path in (Path(value) for value in origin_after['files']):
        if path.suffix.lower() not in {'.npz', '.npy', '.mat', '.safetensors'}:
            sources.add(path)
    sources.update(path for path in Path(native['native_directory']).iterdir() if path.is_file())
    # Capture source bytes before creating the archive. Numeric blobs are excluded.
    payloads = [(path, *M.old.inspect(path, compact=True)) for path in sorted(sources)]
    archive.mkdir()
    (archive / 'artifacts').mkdir()
    rows = []
    for index, (path, raw, pin) in enumerate(payloads, 1):
        name = f'artifacts/{index:04d}_{path.name}'
        with (archive / name).open('xb') as stream:
            stream.write(raw)
        rows.append({'path': name, 'source': path.relative_to(M.ROOT).as_posix(), 'bytes': len(raw), 'sha256': pin[-1]})
    summary = {'schema': 'cho51_staged_eegnet_restore_summary_v1', 'passed': True,
        'closed_utc': datetime.now(timezone.utc).isoformat(), 'pins_sha256': pins_sha,
        'stage_contract_sha256': contract_sha, 'source_context_files': len(pins['files']), 'runtime_files': 5,
        'origin_request_sha256': origin['request_sha'], 'origin_source_result_sha256': origin['result_sha'],
        'origin_source_qualification_sha256': origin['q_sha'], 'origin_native': origin['native'], 'fresh_native': native,
        'source_work_reused': True, 'source_training_replayed': False,
        'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
        'bounded_restore_runtime_verified': True, 'restore_limits_bytes': [1048576, 1048576],
        'weights_bytes': 12664, 'weights_sha256': old_result['publication']['weights_sha256'],
        'model_state_sha256': old_result['model_state_sha256'], 'tensor_count': result['tensor_count'],
        'all_tensors_equal': True, 'origin_module_files_rechecked': origin['module_files'],
        'fresh_module_files_rechecked': len(q['observed_loaded_module_hashes']),
        'physical_input_files_rechecked': 213, 'physical_input_bytes_rechecked': origin['input_bytes'],
        'parent_transaction_qualified': False, 'engineering_successes': 0, 'measured_cells': 0,
        'scientific_admission': False, 'original_case_attempts_remaining': 0, 'artifacts': len(rows)}
    M.old.write(archive / 'manifest.json', {'schema': 'cho51_staged_restore_artifact_manifest_v1', 'artifacts': rows})
    M.old.write(archive / 'summary.json', summary)
    with (archive / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('# Standalone staged EEGNet restoration\n\n'
            'Both actual public restore paths passed with explicit 1 MiB bounds. '
            'The accepted historical source publication is reused unchanged; no training was replayed. '
            'This qualifies detached restoration only. The original failed parent transaction stays failed; '
            'engineering successes and measured cells remain zero.\n\n'
            'See [summary](summary.json), [manifest](manifest.json), and '
            '[qualification report](../../docs/phase2/cho51_staged_restore_qualification_20261015.md).\n')
    for row in rows:
        for path in (archive / row['path'], M.ROOT / row['source']):
            if M.old.inspect(path, compact=True)[1][-1] != row['sha256']:
                raise ValueError('staged archived/source hash mismatch')
    print(json.dumps({'passed': True, 'archive': str(archive), 'artifacts': len(rows),
        'summary_sha256': M.old.inspect(archive / 'summary.json')[1][-1],
        'manifest_sha256': M.old.inspect(archive / 'manifest.json')[1][-1],
        'parent_transaction_qualified': False, 'scientific_admission': False}))


if __name__ == '__main__':
    main()
