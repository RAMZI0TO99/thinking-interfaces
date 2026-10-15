"""Read-only final verification and compact archive of the staged transaction."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(RUN))
import origin

M = origin.M
OUT = RUN / 'validation_001'
CASE = M.CASE


def envelope(value, payload):
    expected = {'schema_version': 1, 'phase': 2, 'kind': 'engineering_smoke', 'payload': payload}
    expected['sha256'] = hashlib.sha256(M.old.canonical(expected)).hexdigest()
    M.old.fields(value, expected, exact=True)


def main():
    stages = origin.verify_origin_stages()
    pins, pins_sha = M.document(RUN / 'pins.json')
    M.verify_pin_map(pins)
    contract, contract_sha = M.document(RUN / 'origin-contract.json', expected=pins['origin_contract_file_sha256'], canonical_raw=True)
    M.old.fields(contract, {'schema': 'cho51_staged_recorder_origin_contract_v1', **stages}, exact=True)
    dispatched, _ = M.document(RUN / 'dispatch_result_001.json')
    dispatch, _ = M.document(RUN / 'dispatch_001.json')
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'parent.py'),
        '--pins', str(RUN / 'pins.json'), '--expect-pins', pins_sha, '--output', str(OUT)]
    for value in (dispatch, dispatched):
        M.old.fields(value, {'pins_sha256': pins_sha, 'child_command': command,
            'expected_output': str(OUT), 'source_training_replayed': False, 'scientific_admission': False})
    M.old.fields(dispatched, {'guard_exit_code': 0})
    operations, runtimes = M.native_pins(pins)
    native = M.old.verify_native(Path(dispatched['native_directory']), command, 300, 4096, 5120,
        operations=operations, runtimes=runtimes, document=M.document, remember=M.remember, launcher=M.launcher)
    q_path = OUT / 'qualification.json'
    q, q_sha = M.document(q_path, canonical_raw=True)
    M.old.fields(q, {'schema': 'cho51_staged_recorder_qualification_v1', 'passed': True,
        'pins_sha256': pins_sha, 'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': 5,
        'source_review_sha256': pins['source_review_sha256'], 'canonical_source_sha256': M.CANONICAL,
        'canonical_files': 432, 'torch_threads': 1, 'torch_interop_threads': 1, 'gpu_hidden': True,
        'unexpected_denials': 0, 'observed_numerical_calls': {}, 'scientific_admission': False,
        'original_case_attempts_remaining': 0})
    result = q['result']
    persisted_result, _ = M.document(OUT / 'result.json', canonical_raw=True)
    if persisted_result != result:
        raise ValueError('persisted parent result differs from native qualification')
    M.old.fields(result, {'passed': True, 'tests_passed': True, 'pytest_exit': 0,
        'expected_tests': pins['expected_tests'], 'collected_tests': pins['expected_tests'],
        'skipped_reports': [], 'backend_calls': 1, 'verifier_calls': 2,
        'current_gradient_updates': 0, 'historical_gradient_updates': 5253,
        'source_work_reused': True, 'restore_work_reused': True,
        'origin_parent_transaction_qualified': False, 'measured_cells': 0,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    if (len(result['reports']) != pins['expected_tests'] or any(
            row['phase'] != 'call' or row['outcome'] != 'passed' for row in result['reports'])):
        raise ValueError('every exact staged boundary test must pass without skips')
    M.old.fields(result['engineering_completion'], {'engineering_success': 1, 'measured': 0, 'failed': 0})
    workspace = OUT / 'cases' / CASE
    request_path = workspace / 'request.json'
    request, request_sha = M.document(request_path, expected=result['request_sha256'], canonical_raw=True)
    fixture = OUT / 'fixture'
    recorder = fixture / 'runs/phase2/lifecycle'
    claim_path = recorder / 'claims' / (CASE + '.attempt1.claim.json')
    claim, claim_sha = M.document(claim_path, expected=result['claim_file_sha256'], canonical_raw=True)
    plan = {'dataset': 'cho2017', 'target_subject': 'subject_02', 'method': 'eegnet',
        'shots_per_class': 5, 'model_seed': 11, 'repetition': 1}
    M.old.fields(request, {'schema': 'cho51_staged_recorder_request_v1', 'case_id': CASE, 'plan': plan,
        'fixture_root': str(fixture), 'recorder_root': str(recorder), 'workspace': str(workspace),
        'pins_path': str(RUN / 'pins.json'), 'independent_pins_sha256': pins_sha,
        'execution_source_sha256': M.CANONICAL, 'owner_decision_sha256': pins['owner_decision_sha256'],
        'claim_path': str(claim_path), 'claim_file_sha256': claim_sha,
        'origin_contract_path': str(RUN / 'origin-contract.json'), 'origin_contract_file_sha256': contract_sha,
        'attempt': 1, 'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
        'source_work_reused': True, 'restore_work_reused': True, 'engineering_only': True,
        'origin_parent_transaction_qualified': False, 'scientific_admission': False,
        'original_case_attempts_remaining': 0})
    claim_payload = claim['payload']
    M.old.fields(claim_payload, {'purpose': 'pilot_case_claim', 'case': plan,
        'worker': 'cho51_staged_source_restore_engineering', 'attempt': 1,
        'environment_sha256': request['environment_sha256'], 'engineering_only': True})
    envelope(claim, claim_payload)
    if claim_payload['source']['source_sha256'] != request['fixture_source_sha256']:
        raise ValueError('fresh control fixture source differs from current claim')
    configs = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
        'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')
    actual_configs = {p.relative_to(fixture).as_posix() for p in (fixture / 'configs').rglob('*') if p.is_file()}
    if actual_configs != set(configs) or (fixture / 'data').exists():
        raise ValueError('fresh recorder fixture must contain only the exact five configuration copies')
    for relative in configs:
        M.remember(fixture / relative, expected=pins['files'][relative], compact=True)
    config_sha = hashlib.sha256('\n'.join(f'{name}:{pins["files"][name]}' for name in sorted(configs)).encode()).hexdigest()
    if config_sha != request['fixture_source_sha256']:
        raise ValueError('fresh control fixture configuration fingerprint differs')
    attestation_path = workspace / 'parent-attestation.json'
    attestation, attested_sha = M.document(attestation_path, expected=result['attestation_file_sha256'], canonical_raw=True)
    proof = result['proof']
    M.old.fields(proof, {'request_sha256': request_sha, 'case_id': CASE,
        'claim_file_sha256': claim_sha, 'execution_source_sha256': M.CANONICAL,
        'independent_pins_sha256': pins_sha, 'owner_decision_sha256': request['owner_decision_sha256'],
        'environment_sha256': request['environment_sha256'], 'origin_contract_file_sha256': contract_sha,
        'verified_origin_files': len(stages['files']),
        **{key: value for key, value in stages['summary'].items() if key in (
            'selected_state_sha256', 'weights_file_sha256', 'historical_gradient_updates',
            'current_gradient_updates', 'source_updates', 'support_updates', 'fold_count',
            'final_source_subjects', 'restored_tensors', 'source_work_reused', 'restore_work_reused',
            'engineering_only', 'scientific_admission', 'measured_cells',
            'original_case_attempts_remaining', 'origin_parent_transaction_qualified')}})
    M.old.fields(attestation, {'schema': 'cho51_staged_recorder_attestation_v1', 'request_sha256': request_sha,
        'case_id': CASE, 'claim_file_sha256': claim_sha, 'proof': proof,
        'source_work_reused': True, 'restore_work_reused': True, 'historical_gradient_updates': 5253,
        'current_gradient_updates': 0, 'engineering_only': True, 'scientific_admission': False,
        'measured_cells': 0, 'origin_parent_transaction_qualified': False, 'original_case_attempts_remaining': 0}, exact=True)
    intent_path = recorder / 'engineering_intents' / (CASE + '.intent.json')
    success_path = recorder / 'engineering_successes' / (CASE + '.success.json')
    intent, _ = M.document(intent_path, canonical_raw=True)
    success, _ = M.document(success_path, canonical_raw=True)
    M.old.fields(result, {'request_path': str(request_path), 'claim_path': str(claim_path),
        'attestation_path': str(attestation_path), 'engineering_receipt': str(success_path),
        'engineering_receipt_file_sha256': M.old.inspect(success_path)[1][-1],
        'origin_contract_file_sha256': contract_sha, 'origin_compact_files': len(stages['files'])})
    for value, purpose in ((intent, 'pilot_case_engineering_success_intent'), (success, 'pilot_case_engineering_success')):
        envelope(value, {'purpose': purpose, 'case': plan, 'attempt': 1,
            'attested_evidence_sha256': attested_sha, 'engineering_only': True})
    if set(recorder.rglob('*.json')) != {claim_path, intent_path, success_path}:
        raise ValueError('exact fresh one-claim/intent/engineering-receipt ledger required')
    for name in ('cells', 'successes', 'publication_intents'):
        if (recorder / name).exists():
            raise ValueError('scientific recorder artifact forbidden')
    expected_denial = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
        'source_file': str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
        'source_sha256': pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py']}
    M.old.fields(q, {'denied_operations': [expected_denial]})
    for path, sha in q['observed_loaded_module_hashes'].items():
        if M.old.inspect(Path(path), single_link=False)[1][-1] != sha:
            raise ValueError('fresh parent loaded module drift')
    if origin.verify_origin_stages() != stages:
        raise ValueError('historical source/restore stages changed across closeout')
    M.verify_pin_map(pins)
    M.launcher._job_absent(native['job_name'])
    archive = ROOT / 'evidence/cho51-staged-recorder-20261015'
    if archive.exists():
        raise ValueError('unused staged-recorder evidence archive required')
    sources = {ROOT / name for name in pins['reviewed_files']}
    sources.update(RUN / name for name in ('source-review.json', 'origin-contract.json', 'pins.json',
        'dispatch_001.json', 'dispatch_result_001.json'))
    sources.update(RUN.glob('preflight*.json'))
    sources.update((q_path, OUT / 'result.json', request_path, claim_path, attestation_path, intent_path, success_path,
        OUT / 'junit.xml', OUT / 'pytest.log'))
    sources.update(fixture / name for name in configs)
    sources.update(Path(path) for path in stages['files'] if Path(path).suffix.lower() != '.safetensors')
    sources.update(path for path in Path(native['native_directory']).iterdir() if path.is_file())
    payloads = [(path, *M.old.inspect(path, compact=True)) for path in sorted(sources)]
    archive.mkdir()
    (archive / 'artifacts').mkdir()
    rows = []
    for index, (path, raw, pin) in enumerate(payloads, 1):
        name = f'artifacts/{index:04d}_{path.name}'
        with (archive / name).open('xb') as stream:
            stream.write(raw)
        rows.append({'path': name, 'source': path.relative_to(ROOT).as_posix(), 'bytes': len(raw), 'sha256': pin[-1]})
    summary = {'schema': 'cho51_staged_recorder_summary_v1', 'passed': True,
        'closed_utc': datetime.now(timezone.utc).isoformat(), 'pins_sha256': pins_sha,
        'origin_contract_file_sha256': contract_sha, 'source_context_files': len(pins['files']), 'runtime_files': 5,
        'expected_tests': pins['expected_tests'], 'tests_passed': pins['expected_tests'],
        'native': native, 'backend_calls': 1, 'verifier_calls': 2,
        'request_sha256': request_sha, 'claim_file_sha256': claim_sha, 'attestation_file_sha256': attested_sha,
        'qualification_file_sha256': q_sha, 'verified_origin_files': len(stages['files']),
        'loaded_module_files': len(q['observed_loaded_module_hashes']),
        'staged_engineering_transaction_qualified': True, 'engineering_successes': 1,
        'current_gradient_updates': 0, 'historical_gradient_updates': 5253,
        'source_work_reused': True, 'restore_work_reused': True,
        'origin_parent_transaction_qualified': False, 'measured_cells': 0,
        'scientific_admission': False, 'original_case_attempts_remaining': 0,
        'artifacts': len(rows), 'origin_summary': stages['summary']}
    M.old.write(archive / 'manifest.json', {'schema': 'cho51_staged_recorder_manifest_v1', 'artifacts': rows})
    M.old.write(archive / 'summary.json', summary)
    with (archive / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('# Staged EEGNet recorder qualification\n\n'
            'A fresh claimed and locked engineering transaction explicitly binds the accepted historical '
            'source and standalone restoration stages. One engineering receipt and zero measured cells; '
            'no fitting or restoration replay. The failed v4 transaction remains failed.\n\n'
            'See [summary](summary.json), [manifest](manifest.json), and '
            '[report](../../docs/phase2/cho51_staged_recorder_qualification_20261015.md).\n')
    for row in rows:
        for path in (archive / row['path'], ROOT / row['source']):
            if M.old.inspect(path, compact=True)[1][-1] != row['sha256']:
                raise ValueError('staged recorder archive/source hash mismatch')
    print(json.dumps({'passed': True, 'archive': str(archive), 'artifacts': len(rows),
        'summary_sha256': M.old.inspect(archive / 'summary.json')[1][-1],
        'manifest_sha256': M.old.inspect(archive / 'manifest.json')[1][-1],
        'engineering_successes': 1, 'measured_cells': 0, 'scientific_admission': False}))


if __name__ == '__main__':
    main()
