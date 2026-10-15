"""Metadata-only final verification and flat archive of the linear recorder Job."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(RUN))
import origin

OUT = RUN / 'validation_001'
ARCHIVE = ROOT / 'evidence/cho51-linear-recorder-20261015'


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def write_once(path, raw):
    with Path(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def envelope(m, item, payload):
    expected = {'schema_version': 1, 'phase': 2, 'kind': 'engineering_smoke', 'payload': payload}
    expected['sha256'] = hashlib.sha256(m.canonical(expected)).hexdigest()
    m.old.fields(item, expected, exact=True)


def verify_pins(m, pins, sha):
    m.need(m.document(RUN / 'pins.json', expected=sha, canonical_raw=True)[0] == pins,
           'exact independent fresh pins required')
    prior, _ = m.document(origin.STAGE / 'pins.json', expected=origin.PINS_SHA, canonical_raw=True)
    m.need(all(pins['files'].get(name) == digest for name, digest in prior['files'].items())
           and all(pins[group] == prior[group] for group in ('runtime', 'baseline', 'selected_weights')),
           'complete1937/5/1/1 predecessor extension required')
    for name, expected in pins['files'].items():
        m._read(m.relative(ROOT, name), expected=expected, single_link=False)
    for name, expected in pins['runtime'].items():
        m._read(Path(name), expected=expected, single_link=False)
    review, _ = m.document(RUN / 'source-review.json', expected=pins['source_review_sha256'], canonical_raw=True)
    m.need(review['source_only'] is True and review['remaining_actionable_findings'] == []
           and review['files'] == pins['reviewed_files'], 'settled reviewed sources required')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-pins', required=True)
    args = parser.parse_args()
    if hashlib.sha256((RUN / 'pins.json').read_bytes()).hexdigest() != args.expect_pins:
        raise ValueError('external fresh pins SHA required before closeout imports')
    # A new process fully rehashes the213 physical inputs after the Job exits.
    stages = origin.verify_origin_stages()
    m = origin.metadata()
    pins, pins_sha = m.document(RUN / 'pins.json', canonical_raw=True)
    m.need(pins_sha == args.expect_pins, 'external closeout pin differs')
    verify_pins(m, pins, pins_sha)
    contract, contract_sha = m.document(RUN / 'origin-contract.json', expected=pins['origin_contract_file_sha256'], canonical_raw=True)
    m.need(contract == dict(schema='cho51_linear_recorder_origin_contract_v1', **stages),
           'independent historical metadata contract changed')
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'parent.py'),
        '--pins', str(RUN / 'pins.json'), '--expect-pins', pins_sha, '--output', str(OUT)]
    dispatch, _ = m.document(RUN / 'dispatch_001.json')
    dispatched, _ = m.document(RUN / 'dispatch_result_001.json')
    for item in (dispatch, dispatched):
        m.old.fields(item, {'pins_sha256': pins_sha, 'origin_contract_file_sha256': contract_sha,
            'child_command': command, 'expected_output': str(OUT),
            'source_training_replayed': False, 'scientific_admission': False})
    m.old.fields(dispatched, {'guard_exit_code': 0})
    native = m.verify_native(dispatched['native_directory'], command, pins, root=ROOT)
    q, q_sha = m.document(OUT / 'qualification.json', canonical_raw=True)
    m.old.fields(q, {'schema': 'cho51_linear_recorder_qualification_v1', 'passed': True,
        'pins_sha256': pins_sha, 'canonical_source_sha256': origin.CANONICAL, 'canonical_files': 432,
        'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': 5,
        'source_review_sha256': pins['source_review_sha256'], 'torch_threads': 1,
        'torch_interop_threads': 1, 'gpu_hidden': True, 'unexpected_denials': 0,
        'observed_numerical_calls': {}, 'model_constructions': 0, 'current_restore_count': 0,
        'target_inference_calls': 0, 'torch_metadata_dependency_imported': True,
        'numpy_metadata_dependency_imported': True, 'current_gradient_updates': 0,
        'historical_gradient_updates': 5253, 'scientific_admission': False,
        'actual_study_inputs_or_pretrained_weights_used': False, 'original_case_attempts_remaining': 0})
    result, _ = m.document(OUT / 'result.json', canonical_raw=True)
    m.need(q['result'] == result, 'persisted result differs from native qualification')
    m.old.fields(result, {'passed': True, 'tests_passed': True, 'pytest_exit': 0,
        'collected_tests': pins['expected_tests'], 'expected_tests': pins['expected_tests'],
        'skipped_reports': [], 'backend_calls': 1, 'verifier_calls': 2,
        'source_work_reused': True, 'restore_work_reused': True,
        'source_training_replayed': False, 'current_gradient_updates': 0, 'historical_gradient_updates': 5253,
        'original_scientific_case_qualified': False, 'historical_publication_qualified': True,
        'historical_detached_restoration_qualified': True, 'current_restore_count': 0,
        'target_inference_calls': 0, 'measured_cells': 0, 'scientific_admission': False,
        'original_case_attempts_remaining': 0})
    m.need(len(result['reports']) == pins['expected_tests'] and all(row['phase'] == 'call'
           and row['outcome'] == 'passed' for row in result['reports']), 'all exact tests must pass')
    m.old.fields(result['engineering_completion'], {'engineering_success': 1, 'measured': 0, 'failed': 0})
    fixture = OUT / 'fixture'
    recorder = fixture / 'runs/phase2/lifecycle'
    workspace = OUT / 'cases' / origin.CASE
    request_path = workspace / 'request.json'
    request, request_sha = m.document(request_path, expected=result['request_sha256'], canonical_raw=True)
    plan = {'dataset': 'cho2017', 'target_subject': 'subject_02', 'method': 'labram_linear',
        'shots_per_class': 5, 'model_seed': 11, 'repetition': 1}
    claim_path = recorder / 'claims' / (origin.CASE + '.attempt1.claim.json')
    claim, claim_sha = m.document(claim_path, expected=result['claim_file_sha256'], canonical_raw=True)
    m.old.fields(request, {'schema': 'cho51_linear_recorder_request_v1', 'case_id': origin.CASE,
        'plan': plan, 'fixture_root': str(fixture), 'recorder_root': str(recorder), 'workspace': str(workspace),
        'pins_path': str(RUN / 'pins.json'), 'independent_pins_sha256': pins_sha,
        'execution_source_sha256': origin.CANONICAL, 'owner_decision_sha256': pins['owner_decision_sha256'],
        'claim_path': str(claim_path), 'claim_file_sha256': claim_sha,
        'origin_contract_path': str(RUN / 'origin-contract.json'), 'origin_contract_file_sha256': contract_sha,
        'historical_case_id': origin.CASE, 'historical_git_commit': stages['summary']['historical_source']['git_commit'],
        'historical_source_sha256': stages['summary']['historical_source']['source_sha256'],
        'historical_git_dirty': True, 'fixture_git_commit': '277d7975ba400a9927bdd3e1495f6ade25ddea38',
        'fixture_git_dirty': True, 'attempt': 1})
    current_source = {'git_commit': request['fixture_git_commit'], 'source_sha256': request['fixture_source_sha256'],
                      'git_dirty': request['fixture_git_dirty']}
    m.need(current_source == result['fixture_source'] and stages['summary']['historical_source'] == result['historical_source']
           and current_source['git_commit'] != stages['summary']['historical_source']['git_commit'],
           'historical and current real Git contexts must be bound separately')
    payload = claim['payload']
    m.old.fields(payload, {'purpose': 'pilot_case_claim', 'case': plan,
        'worker': 'cho51_linear_staged_source_restore_engineering', 'attempt': 1,
        'environment_sha256': request['environment_sha256'], 'engineering_only': True, 'source': current_source})
    envelope(m, claim, payload)
    configs = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
        'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')
    m.need({p.relative_to(fixture).as_posix() for p in (fixture / 'configs').rglob('*') if p.is_file()} == set(configs)
           and not (fixture / 'data').exists() and not (fixture / '.git').exists(),
           'exact five-TOML control fixture without arrays or Git shadow required')
    for name in configs:
        m.remember(fixture / name, expected=pins['files'][name], compact=True)
    fingerprint = hashlib.sha256('\n'.join(f'{name}:{pins["files"][name]}' for name in sorted(configs)).encode()).hexdigest()
    m.need(fingerprint == request['fixture_source_sha256'], 'fresh configuration fingerprint changed')
    attestation_path = workspace / 'parent-attestation.json'
    attestation, attested_sha = m.document(attestation_path, expected=result['attestation_file_sha256'], canonical_raw=True)
    proof = result['proof']
    proof_expected = {'request_sha256': request_sha, 'case_id': origin.CASE,
        'claim_file_sha256': claim_sha, 'execution_source_sha256': origin.CANONICAL,
        'independent_pins_sha256': pins_sha, 'owner_decision_sha256': pins['owner_decision_sha256'],
        'environment_sha256': request['environment_sha256'], 'origin_contract_file_sha256': contract_sha,
        'verified_origin_files': len(stages['files'])}
    for name in ('fixture_source_sha256', 'fixture_git_commit', 'fixture_git_dirty', 'historical_case_id',
                 'historical_git_commit', 'historical_source_sha256', 'historical_git_dirty'):
        proof_expected[name] = request[name]
    for name, value in stages['summary'].items():
        if name in proof:
            proof_expected[name] = value
    m.old.fields(proof, proof_expected)
    m.old.fields(attestation, {'schema': 'cho51_linear_recorder_attestation_v1', 'request_sha256': request_sha,
        'case_id': origin.CASE, 'claim_file_sha256': claim_sha, 'proof': proof})
    intent_path = recorder / 'engineering_intents' / (origin.CASE + '.intent.json')
    success_path = recorder / 'engineering_successes' / (origin.CASE + '.success.json')
    for path, purpose in ((intent_path, 'pilot_case_engineering_success_intent'),
                          (success_path, 'pilot_case_engineering_success')):
        item, _ = m.document(path, canonical_raw=True)
        expected_payload = {'purpose': purpose, 'case': plan, 'attempt': 1,
            'attested_evidence_sha256': attested_sha, 'engineering_only': True}
        envelope(m, item, expected_payload)
    m.need(set(recorder.rglob('*.json')) == {claim_path, intent_path, success_path},
           'one claim, one durable intent and one engineering receipt required')
    for name in ('cells', 'successes', 'publication_intents'):
        m.need(not (recorder / name).exists(), 'scientific ledger artifact forbidden')
    m.need(q['protected_target_read_attempts'] == [] and q['denied_operations'] in ([], [{
        'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
        'source_file': str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
        'source_sha256': pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py']}]),
        'unexpected denied operation or target computational read')
    for path, sha in q['observed_loaded_module_hashes'].items():
        m._read(Path(path), expected=sha, single_link=False)
    m.launcher._job_absent(native['job_name'])
    m.need(not ARCHIVE.exists(), 'unused current metadata archive required')
    sources = {ROOT / name for name in pins['reviewed_files']}
    sources.update(RUN / name for name in ('pins.json', 'source-review.json', 'origin-contract.json',
        'dispatch_001.json', 'dispatch_result_001.json'))
    sources.update(RUN.glob('preflight*.json'))
    sources.update((OUT / 'qualification.json', OUT / 'result.json', OUT / 'junit.xml', OUT / 'pytest.log',
        request_path, claim_path, attestation_path, intent_path, success_path))
    sources.update(fixture / name for name in configs)
    sources.update(path for path in Path(native['native_directory']).iterdir() if path.is_file())
    publication = m.document(origin.STAGE / 'publication_001/publication-result.json', expected=origin.PUBLICATION_SHA)[0]
    sources.update(Path(publication[key]) for key in ('manifest_path', 'evidence_path'))
    payloads = []
    for path in sorted(sources):
        m.need(path.is_relative_to(ROOT) and path.suffix.lower() not in {'.npz', '.npy', '.mat', '.safetensors'},
               'flat current metadata archive excludes arrays, weights and ancestor packets')
        maximum = 32 * 1024**2 if path == Path(publication['evidence_path']) else 8 * 1024**2
        _, pin = m._read(path, expected=origin.EVIDENCE_SHA if path == Path(publication['evidence_path']) else None,
                        maximum=maximum, compact=True)
        raw, pin = origin._asset(path, pin[-1], maximum, compact=True)
        payloads.append((path, raw, pin))
    verify_pins(m, pins, pins_sha)
    ARCHIVE.mkdir()
    (ARCHIVE / 'artifacts').mkdir()
    rows = []
    for index, (path, raw, pin) in enumerate(payloads, 1):
        target = f'artifacts/a{index:04d}{path.suffix}'
        write_once(ARCHIVE / target, raw)
        origin._asset(path, pin[-1], max(len(raw), 1))
        origin._asset(ARCHIVE / target, pin[-1], max(len(raw), 1))
        rows.append({'source': path.relative_to(ROOT).as_posix(), 'path': target, 'bytes': len(raw), 'sha256': pin[-1]})
    summary = {'schema': 'cho51_linear_recorder_summary_v1', 'passed': True,
        'closed_utc': datetime.now(timezone.utc).isoformat(), 'pins_sha256': pins_sha,
        'origin_contract_file_sha256': contract_sha, 'source_context_files': len(pins['files']),
        'runtime_files': 5, 'tests_passed': pins['expected_tests'], 'native': native,
        'backend_calls': 1, 'verifier_calls': 2, 'engineering_successes': 1, 'measured_cells': 0,
        'staged_engineering_transaction_qualified': True, 'scientific_admission': False,
        'current_gradient_updates': 0, 'current_restore_count': 0, 'target_inference_calls': 0,
        'historical_gradient_updates': 5253, 'historical_case_id': origin.CASE, 'current_case_id': origin.CASE,
        'historical_source': stages['summary']['historical_source'], 'current_control_source': current_source,
        'request_sha256': request_sha, 'claim_file_sha256': claim_sha,
        'attestation_file_sha256': attested_sha, 'qualification_file_sha256': q_sha,
        'verified_origin_files': len(stages['files']), 'loaded_module_files': len(q['observed_loaded_module_hashes']),
        'physical_input_files_rechecked_after_job': 213, 'physical_input_bytes_rechecked_after_job': 734579463,
        'original_case_attempts_remaining': 0, 'artifacts': len(rows), 'origin_summary': stages['summary']}
    write_once(ARCHIVE / 'manifest.json', encoded({'schema': 'cho51_linear_recorder_manifest_v1', 'artifacts': rows}))
    write_once(ARCHIVE / 'summary.json', encoded(summary))
    write_once(ARCHIVE / 'README.md', ('# Linear staged recorder integration\n\n'
        'One fresh locked engineering transaction binds the accepted historical linear publication '
        'and detached restoration. One engineering receipt and zero measured cells; no fitting, '
        'restoration or target prediction replay. Historical and current Git contexts are distinct.\n').encode())
    m.launcher._job_absent(native['job_name'])
    print(json.dumps({'passed': True, 'archive': str(ARCHIVE), 'artifacts': len(rows),
        'manifest_sha256': hashlib.sha256((ARCHIVE / 'manifest.json').read_bytes()).hexdigest(),
        'summary_sha256': hashlib.sha256((ARCHIVE / 'summary.json').read_bytes()).hexdigest(),
        'engineering_successes': 1, 'measured_cells': 0}))


if __name__ == '__main__':
    main()
