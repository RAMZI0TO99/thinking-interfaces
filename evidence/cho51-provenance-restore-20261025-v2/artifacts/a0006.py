"""Independent standard-library closeout of the one factory restoration Job."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = RUN / 'validation_001'
ARCHIVE = ROOT / 'evidence/cho51-provenance-restore-20261025-v2'
sys.path.insert(0, str(RUN))
import origin


def fields(value, expected):
    origin.need(type(value) is dict and all(type(value.get(name)) is type(item) and value[name] == item
                for name, item in expected.items()), 'exact fields differ: ' + ', '.join(expected))


def write_once(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def envelope(value, payload):
    expected = dict(schema_version=1, phase=2, kind='engineering_smoke', payload=payload)
    expected['sha256'] = hashlib.sha256(origin.canonical(expected).rstrip(b'\n')).hexdigest()
    origin.need(value == expected, 'exact engineering envelope differs')


def job_absent(name):
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.OpenJobObjectW.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_wchar_p]
    api.OpenJobObjectW.restype = ctypes.c_void_p
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    ctypes.set_last_error(0)
    handle = api.OpenJobObjectW(4, False, name)
    error = ctypes.get_last_error()
    if handle:
        api.CloseHandle(handle)
    origin.need(not handle and error == 2, 'fresh named native Job absence unconfirmed')


def verify_native(directory, command, pins):
    directory = Path(directory)
    origin.need(directory.resolve(strict=True) == directory and directory.parent == ROOT / 'runs/migration'
                and re.fullmatch(r'\d{8}T\d{6}Z_[a-f0-9]{10}', directory.name), 'direct dispatched native directory required')
    admission = origin.document(directory / 'admission.json')
    receipt = origin.document(directory / 'receipt.json')
    deadline = origin.document(directory / 'deadline.json')
    operations = {name: value for name, value in pins['files'].items()
                  if Path(name).parent == Path('tools/migration') and Path(name).suffix in {'.py', '.ps1', '.json', '.lock'}
                  or name == 'evaluation/phase2_supervision_primitives.py'
                  or name in pins['reviewed_files'] and Path(name).parent == RUN.relative_to(ROOT)}
    runtime = {name: value for name, value in pins['runtime'].items()
               if Path(name) == ROOT / '.venv/Scripts/python.exe' or Path(name).name in {'python312.dll', 'python3.dll'}}
    job_name = 'pro3_migration_' + directory.name
    fields(admission, dict(schema='migration_admission_v1', source_sha256=origin.CANONICAL, command=command,
                          operation_pins=operations, selected_runtime_pins=runtime, process_mib=4096, job_mib=5120,
                          guard_policy_schema='cho51_provenance_restore_guard_v1', startup_ram_gib=4,
                          previous_startup_ram_gib=10, historical_10gib_startup_pass_claimed=False,
                          owner_resource_amendment_path=pins['owner_resource_amendment_path'],
                          owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256'],
                          active_ram_gib=4, active_disk_gib=20, native_threads=1,
                          peer_pause_file='D:\\Aenv\\pro2\\WORK\\resume-20261025-001\\coordination\\PRO2_REQUEST_PRO3_PAUSE.json'))
    fields(receipt, dict(schema='migration_guard_receipt_v1', accepted=True, job_name=job_name,
                        job_absent=True, scientific_admission=False, error=None))
    state, result = receipt['native_state'], receipt['result']
    flags = ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified', 'atomic_job_assignment_requested',
             'atomic_job_assignment_verified', 'assigned', 'membership_verified', 'resumed', 'job_empty_before_close',
             'job_closed', 'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen')
    fields(state, dict.fromkeys(flags, True) | dict(job_named=job_name, cleanup_errors=[], peak_sampling_errors=[],
                                                  process_limit_bytes=4096 * 1024**2, aggregate_limit_bytes=5120 * 1024**2))
    fields(result, dict(reason='normal', exit_code=0))
    origin.need(type(state['peak_samples']) is int and state['peak_samples'] > 0, 'actual native samples required')
    for key, other, maximum in (('peak_process_commit_bytes', 'peak_process_memory_bytes', 4096 * 1024**2),
                                ('peak_job_commit_bytes', 'peak_job_memory_bytes', 5120 * 1024**2)):
        origin.need(type(state[key]) is int and 0 < state[key] <= maximum and state[key] == result[other],
                    'positive native peaks within fixed caps required')
    origin.need(state['peak_job_commit_bytes'] >= state['peak_process_commit_bytes'], 'native aggregate peak below process peak')
    samples = admission['startup_samples']
    origin.need(len(samples) == 2 and samples == receipt['startup_samples'] and all(
        type(row['available_ram_bytes']) is int and row['available_ram_bytes'] >= 4 * 1024**3
        and type(row['free_disk_bytes']) is int and row['free_disk_bytes'] >= 20 * 1024**3 for row in samples),
        'two genuine owner-amended RAM4 GiB and disk20 GiB startup samples required')
    utc = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    started, ended, limit = (utc(value) for value in (admission['started_utc'], receipt['completed_utc'], admission['deadline_utc']))
    origin.need((limit - started).total_seconds() == 600 and started <= ended <= limit, 'exact finite600 second Job required')
    fields(deadline, dict(schema='phase2_supervision_deadlines_v1', attempt_deadline_utc=admission['deadline_utc']))
    origin.need((utc(deadline['session_deadline_utc']) - limit).total_seconds() == 5, 'exact five second supervisor margin required')
    job_absent(job_name)
    return dict(native_directory=str(directory), job_name=job_name, accepted=True,
                receipt_sha256=origin.digest(directory / 'receipt.json'), started_utc=admission['started_utc'],
                completed_utc=receipt['completed_utc'], elapsed_seconds=(ended - started).total_seconds(),
                peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes'],
                closed_empty_handles_closed_freshly_absent=True)


def verify_canonical(pins):
    manifest = origin.document(ROOT / 'tools/migration/source-files.json', pins['files']['tools/migration/source-files.json'])
    rows = manifest['files']
    origin.need(len(rows) == 432, 'exact canonical432 manifest required')
    aggregate = hashlib.sha256('\n'.join(f"{row['path']}:{row['sha256']}" for row in rows).encode()).hexdigest()
    origin.need(aggregate == manifest['source_sha256'] == origin.CANONICAL, 'canonical manifest aggregate differs')
    for row in rows:
        origin.need(origin.digest(ROOT / row['path']) == row['sha256'], 'canonical source changed')
    directories = ('core', 'encoder', 'adaptation', 'data', 'realtime', 'evaluation', 'scripts', 'tests', 'configs')
    found = set()
    for directory in directories:
        for path in (ROOT / directory).rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.py', '.toml', '.ps1'}:
                relative = path.relative_to(ROOT).as_posix()
                if not relative.startswith(('data/raw/', 'data/processed/', 'data/interim/')) and path.name != 'local.toml':
                    found.add(relative)
    found.update(row['path'] for row in rows if row['path'].split('/')[0] not in directories)
    origin.need(found == {row['path'] for row in rows}, 'canonical added or removed source detected')


def verify_pins(pins, expected):
    origin.need(origin.digest(RUN / 'pins.json') == expected, 'fresh pins changed')
    for name, value in pins['files'].items():
        origin.need(origin.digest(ROOT / name) == value, 'source/context pin changed')
    for group in ('runtime', 'runtime_modules', 'supporting_runtime_sources'):
        for name, value in pins[group].items():
            origin.need(origin.digest(name) == value, 'fresh current runtime changed')
    fields(origin.document(RUN / 'source-review.json', pins['source_review_sha256']),
           dict(source_only=True, remaining_actionable_findings=[], files=pins['reviewed_files']))
    amendment_path = Path(pins['owner_resource_amendment_path'])
    origin.need(amendment_path == RUN / 'owner-resource-amendment.json', 'exact owner amendment path required')
    fields(origin.document(amendment_path, pins['owner_resource_amendment_sha256']),
           dict(schema='cho51_provenance_restore_owner_resource_amendment_v1',
                scope='cho51_provenance_restore_20261025_v2', previous_startup_ram_gib=10,
                owner_instruction_exact='work with the 4GiB ram you have for now. it will be enough.',
                startup_ram_gib=4, active_ram_gib=4, disk_gib=20, maximum_job_seconds=600,
                process_mib=4096, job_mib=5120, threads=1, gpu_hidden=True,
                canonical_guard_modified=False, historical_receipts_requalified=False, scientific_admission=False))
    origin.need(origin.digest(RUN / 'native-runtime.json') == pins['native_runtime_sha256'], 'native transition observation changed')
    verify_canonical(pins)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-pins', required=True)
    args = parser.parse_args()
    pins = origin.document(RUN / 'pins.json', args.expect_pins)
    fields(pins, dict(schema='cho51_provenance_restore_pins_v1', scientific_admission=False,
                      current_restore_count=1, current_source_updates=0, current_support_updates=0,
                      current_gradient_updates=0, target_inference_calls=0, measured_cells=0, canonical_files=432,
                      startup_ram_gib=4, active_ram_gib=4, previous_startup_ram_gib=10, historical_10gib_startup_pass_claimed=False))
    verify_pins(pins, args.expect_pins)
    stages = origin.verify_origin_stages()
    contract = origin.document(RUN / 'origin-contract.json', pins['origin_contract_file_sha256'])
    origin.need(contract == dict(schema='cho51_provenance_restore_origin_v1', **stages), 'historical origin contract changed at closeout')
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'parent.py'),
               '--pins', str(RUN / 'pins.json'), '--expect-pins', args.expect_pins, '--output', str(OUT)]
    dispatch = origin.document(RUN / 'dispatch_001.json')
    dispatched = origin.document(RUN / 'dispatch_result_001.json')
    for value in (dispatch, dispatched):
        fields(value, dict(pins_sha256=args.expect_pins, origin_contract_file_sha256=pins['origin_contract_file_sha256'],
                           child_command=command, expected_output=str(OUT), scientific_admission=False,
                           expected_selected_restores=1, actual_current_restore_count=None,
                           source_updates=0, support_updates=0, query_calls=0, measured_cells=0))
    fields(dispatched, dict(guard_exit_code=0))
    native = verify_native(dispatched['native_directory'], command, pins)
    admission = origin.document(RUN / 'admission.json', dispatch['admission_sha256'])
    peer_release = origin.document(Path(admission['peer_release_path']), admission['peer_release_sha256'])
    fields(admission, dict(schema='cho51_provenance_restore_admission_v1', pins_sha256=args.expect_pins,
                           source_review_sha256=pins['source_review_sha256'], accepted=True, scientific_admission=False,
                           max_job_seconds=600, process_mib=4096, job_mib=5120, startup_ram_gib=4, active_ram_gib=4, disk_gib=20,
                           owner_resource_amendment_path=pins['owner_resource_amendment_path'],
                           owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256']))
    fields(peer_release, dict(schema='pro2_pro3_compute_release_v1', scope='cho51_provenance_restore_20261025_v2',
                              released=True, pins_sha256=args.expect_pins, maximum_jobs=1, max_job_seconds=600,
                              process_mib=4096, job_mib=5120, window_start_utc=admission['window_start_utc'],
                              window_end_utc=admission['window_end_utc']))
    utc = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    origin.need(utc(admission['window_start_utc']) <= utc(native['started_utc']) <= utc(native['completed_utc'])
                <= utc(admission['window_end_utc']), 'actual native Job must stay inside explicit peer release interval')
    for value in (dispatch, dispatched):
        fields(value, dict(admission_sha256=origin.digest(RUN / 'admission.json'), peer_release_path=admission['peer_release_path'],
                           peer_release_sha256=admission['peer_release_sha256'], window_start_utc=admission['window_start_utc'],
                           window_end_utc=admission['window_end_utc']))
    result = origin.document(OUT / 'result.json')
    qualification = origin.document(OUT / 'qualification.json')
    fields(result, dict(schema='cho51_provenance_restore_result_v1', passed=True, tests_passed=True,
                        pytest_exit=0, collected_tests=pins['expected_tests'], expected_tests=pins['expected_tests'],
                        skipped_reports=[], backend_calls=1, verifier_calls=2, current_restore_count=1,
                        current_source_updates=0, current_support_updates=0, current_gradient_updates=0,
                        target_inference_calls=0, measured_cells=0, scientific_admission=False,
                        actual_executor_source=pins['expected_current_context'], actual_recorder_source=pins['expected_fixture_context']))
    origin.need(len(result['reports']) == pins['expected_tests'] and all(row['phase'] == 'call' and row['outcome'] == 'passed'
                for row in result['reports']), 'all exact focused tests must pass')
    junit_path = OUT / 'junit.xml'
    junit_identity = origin.identity(junit_path)
    origin.need(0 < junit_identity[2] <= 8 * 1024**2, 'bounded JUnit document required')
    with junit_path.open('rb') as stream:
        junit_raw = stream.read(junit_identity[2] + 1)
    origin.need(len(junit_raw) == junit_identity[2] and origin.identity(junit_path) == junit_identity
                and hashlib.sha256(junit_raw).hexdigest() == junit_identity[-1], 'JUnit bytes changed during bounded read')
    suites = list(ET.fromstring(junit_raw).iter('testsuite'))
    origin.need(sum(int(suite.attrib['tests']) for suite in suites) == pins['expected_tests']
                and all(int(suite.attrib.get(name, '0')) == 0 for suite in suites for name in ('failures', 'errors', 'skipped')),
                'independent exact JUnit tests required')
    fields(qualification, dict(schema='cho51_provenance_restore_qualification_v1', passed=True, result=result,
                              pins_sha256=args.expect_pins, canonical_files=432, canonical_source_sha256=origin.CANONICAL,
                              model_constructions=1, constructor_dummy_forward_calls=1, numpy_load_count=0,
                              current_source_updates=0, current_support_updates=0, current_gradient_updates=0,
                              target_inference_calls=0, measured_cells=0, scientific_admission=False,
                              unexpected_denials=0, torch_threads=1, torch_interop_threads=1, gpu_hidden=True,
                              runtime_pins_rechecked=5, runtime_module_pins_rechecked=18, supporting_runtime_sources_rechecked=4))
    calls = qualification['observed_numerical_calls']
    origin.need(set(calls) == {'model_module_init', 'module_load_state_dict', 'safetensors_load'}
                and type(calls['model_module_init']) is int and calls['model_module_init'] > 0
                and calls['module_load_state_dict'] == calls['safetensors_load'] == 2
                and type(qualification['lock_checks']) is int and qualification['lock_checks'] > 0,
                'exact narrow actual restoration observations required')
    request_path = Path(result['request_path'])
    request = origin.document(request_path, result['request_sha256'])
    workspace = request_path.parent
    plan = dict(dataset='cho2017', target_subject='subject_02', method='labram_linear', shots_per_class=5, model_seed=11, repetition=1)
    fields(request, dict(producer=pins['factory_producer'], executor=pins['factory_executor'], plan_json=json.dumps(plan, sort_keys=True, separators=(',', ':')),
                         store_root=pins['store_root'], workspace=str(workspace), claim_path=result['claim_path'], claim_sha256=result['claim_sha256'],
                         pins_path=str(RUN / 'pins.json'), pins_sha256=args.expect_pins, method_config_sha256=pins['method_config_sha256'],
                         engineering_only=True, scientific_admission=False, maximum_weights_bytes=64 * 1024**2))
    origin.need(hashlib.sha256(origin.canonical(request).rstrip(b'\n')).hexdigest() == result['request_sha256'],
                'durable request must have exact canonical physical bytes')
    fixture = OUT / 'fixture'
    recorder = fixture / 'runs/phase2/lifecycle'
    case_id = hashlib.sha256(origin.canonical(plan).rstrip(b'\n')).hexdigest()
    origin.need(workspace == OUT / 'cases' / case_id and Path(result['claim_path']) == recorder / 'claims' / (case_id + '.attempt1.claim.json'),
                'actual case workspace and claim paths differ')
    claim = origin.document(Path(result['claim_path']), result['claim_sha256'])
    fields(claim['payload'], dict(purpose='pilot_case_claim', case=plan, worker='cho51_provenance_restore_engineering_v1', attempt=1,
                                 source=pins['expected_fixture_context'], engineering_only=True))
    envelope(claim, claim['payload'])
    witness_path = Path(result['restore_witness_path'])
    witness = origin.document(witness_path, result['restore_witness_sha256'])
    fields(witness, dict(schema='cho51_provenance_restored_source_v1', passed=True, request_sha256=result['request_sha256'],
                         claim_sha256=result['claim_sha256'], pins_sha256=args.expect_pins, workspace=str(workspace),
                         historical_source=json.loads(pins['factory_producer']['source_json']),
                         current_executor_source=pins['expected_current_context'], tensor_count=223, elements=5818138,
                         adapter_class='evaluation.phase2_pilot.LaBraMTunedAdapter', complete_metadata_verified=True,
                         selected_restores=1, model_constructions=1, safe_decodes=2, strict_state_loads=2,
                         source_updates=0, support_updates=0, query_calls=0, measured_cells=0, scientific_admission=False))
    origin.need(witness == result['witness'], 'physical and embedded factory witness differ')
    fields(origin.document(workspace / 'restore-attempt.json', witness['restore_attempt_sha256']),
           dict(schema='cho51_provenance_restore_attempt_v1', request_sha256=result['request_sha256'],
                claim_sha256=result['claim_sha256'], pins_sha256=args.expect_pins, scientific_admission=False))
    for key in ('manifest_sha256', 'manifest_file_sha256', 'model_recipe_sha256', 'weights_sha256', 'model_state_sha256'):
        origin.need(witness[key] == pins['factory_producer'][key], 'historical factory witness binding differs')
    binding_path = workspace / 'parent-binding.json'
    binding = origin.document(binding_path)
    fields(binding, dict(request_path=str(request_path), request_sha256=result['request_sha256'], claim_path=result['claim_path'],
                         claim_sha256=result['claim_sha256'], pins_sha256=args.expect_pins, workspace=str(workspace)))
    fields(binding['native'], dict(native_directory=native['native_directory'], job_name=native['job_name'], command=command,
                                   admission_path=str(Path(native['native_directory']) / 'admission.json'),
                                   admission_sha256=origin.digest(Path(native['native_directory']) / 'admission.json'), membership_verified=True,
                                   root_admission_sha256=origin.digest(RUN / 'admission.json'), peer_release_path=admission['peer_release_path'],
                                   peer_release_sha256=admission['peer_release_sha256'], peer_window_end_utc=admission['window_end_utc']))
    origin.need(binding['native'] == result['native_binding'], 'request/native live-membership binding differs')
    attestation_path = Path(result['attestation_path'])
    attestation = origin.document(attestation_path, result['attestation_sha256'])
    fields(attestation, dict(schema='cho51_provenance_restore_attestation_v1', request_sha256=result['request_sha256'],
                             claim_sha256=result['claim_sha256'], pins_sha256=args.expect_pins,
                             restore_witness_sha256=result['restore_witness_sha256'], parent_binding_sha256=origin.digest(binding_path),
                             backend_calls=1, verifier_calls=2, observed_numerical_calls=calls,
                             current_counts=dict(selected_restores=1, source_updates=0, support_updates=0, gradient_updates=0, query_calls=0, measured_cells=0),
                             native_closeout_status='pending_external_post_job', engineering_only=True, scientific_admission=False))
    intent = recorder / 'engineering_intents' / (case_id + '.intent.json')
    success = Path(result['engineering_receipt_path'])
    origin.need(success == recorder / 'engineering_successes' / (case_id + '.success.json'), 'engineering receipt path differs')
    for path, purpose in ((intent, 'pilot_case_engineering_success_intent'), (success, 'pilot_case_engineering_success')):
        envelope(origin.document(path), dict(purpose=purpose, case=plan, attempt=1,
                                            attested_evidence_sha256=result['attestation_sha256'], engineering_only=True))
    origin.need(origin.digest(success) == result['engineering_receipt_sha256']
                and set(recorder.rglob('*.json')) == {Path(result['claim_path']), intent, success}, 'exact engineering-only recorder outputs required')
    for directory in ('cells', 'successes', 'publication_intents'):
        origin.need(not (recorder / directory).exists(), 'scientific recorder output forbidden')
    origin.need(result['input_audit_before'] == result['input_audit_after'] == origin.verify_inputs(), 'all213 original input files differ at closeout')
    for name, value in qualification['observed_loaded_module_hashes'].items():
        origin.need(origin.digest(name) == value, 'actual loaded module changed')
    expected_probe = dict(event='socket.__new__', classification='blocked_optional_ipv6_import_probe',
                          source_file=str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
                          source_sha256=pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py'])
    origin.need(qualification['denied_operations'] in ([], [expected_probe]), 'unexpected numerical or IO guard denial')
    scoped_names = sorted(set([*stages['summary']['native_names'], native['job_name']]))
    for name in scoped_names:
        job_absent(name if name.startswith('pro3_migration_') else 'pro3_migration_' + name)
    origin.need(not ARCHIVE.exists(), 'fresh unused evidence archive required')
    peer_path = Path(admission['peer_release_path'])
    peer_identity = origin.identity(peer_path)
    origin.need(0 < peer_identity[2] <= 8 * 1024**2 and peer_identity[-1] == admission['peer_release_sha256'],
                'bounded authenticated external peer release required')
    with peer_path.open('rb') as stream:
        peer_raw = stream.read(peer_identity[2] + 1)
    origin.need(len(peer_raw) == peer_identity[2] and origin.identity(peer_path) == peer_identity
                and hashlib.sha256(peer_raw).hexdigest() == admission['peer_release_sha256'],
                'external peer release changed during exact copy')
    peer_copy = RUN / 'peer-release-authenticated.json'
    write_once(peer_copy, peer_raw)
    origin.need(origin.digest(peer_copy) == admission['peer_release_sha256'], 'portable peer release copy differs')
    sources = {ROOT / name for name in pins['reviewed_files']}
    sources.update(RUN / name for name in ('pins.json', 'source-review.json', 'native-runtime.json', 'origin-contract.json',
                                          'admission.json', 'dispatch_001.json', 'dispatch_result_001.json', 'owner-resource-amendment.json'))
    sources.add(peer_copy)
    sources.update(RUN.glob('preflight*.json'))
    sources.update(path for path in OUT.glob('*') if path.is_file() and path.suffix in {'.json', '.xml', '.log'})
    sources.update(path for path in workspace.iterdir() if path.is_file())
    sources.update((Path(result['claim_path']), intent, success))
    sources.update(path for path in (fixture / 'configs').rglob('*') if path.is_file())
    sources.update(path for path in Path(native['native_directory']).iterdir() if path.is_file())
    origin.need(len(sources) <= 128, 'bounded archive artifact inventory required')
    rows, payloads, archive_bytes = [], [], 0
    for index, path in enumerate(sorted(sources), 1):
        before = origin.identity(path)
        origin.need(path.is_relative_to(ROOT) and path.suffix.lower() not in {'.npz', '.npy', '.mat', '.safetensors'}
                    and before[2] <= 8 * 1024**2, 'archive contains bounded metadata only')
        archive_bytes += before[2]
        origin.need(archive_bytes <= 64 * 1024**2, 'complete metadata archive exceeds aggregate byte bound')
        with path.open('rb') as stream:
            raw = stream.read(before[2] + 1)
        origin.need(len(raw) == before[2] and origin.identity(path) == before
                    and hashlib.sha256(raw).hexdigest() == before[-1], 'archive source changed during bounded read')
        relative = f'artifacts/a{index:04d}{path.suffix}'
        rows.append(dict(source=path.relative_to(ROOT).as_posix(), path=relative, bytes=len(raw), sha256=before[-1]))
        payloads.append((relative, raw))
    verify_pins(pins, args.expect_pins)
    ARCHIVE.mkdir()
    (ARCHIVE / 'artifacts').mkdir()
    write_once(ARCHIVE / '.gitattributes', b'* -text\n')
    for relative, raw in payloads:
        write_once(ARCHIVE / relative, raw)
    manifest = dict(schema='cho51_provenance_restore_archive_v1', artifacts=rows)
    write_once(ARCHIVE / 'manifest.json', origin.canonical(manifest))
    summary = dict(schema='cho51_provenance_restore_closeout_v1', passed=True, closed_utc=datetime.now(timezone.utc).isoformat(),
                   pins_sha256=args.expect_pins, source_review_sha256=pins['source_review_sha256'],
                   origin_files=len(stages['files']), original_inputs=213, canonical_sources=432, tests=pins['expected_tests'],
                   historical_source=json.loads(pins['factory_producer']['source_json']), current_executor_source=pins['expected_current_context'],
                   current_recorder_source=pins['expected_fixture_context'], native=native,
                   scoped_native_names_freshly_absent=len(scoped_names), engineering_successes=1, current_restore_count=1,
                   current_source_updates=0, current_support_updates=0, current_gradient_updates=0, target_inference_calls=0,
                   measured_cells=0, scientific_admission=False, experiment_freeze_signed=False,
                   startup_ram_gib=4, active_ram_gib=4, previous_startup_ram_gib=10,
                   historical_10gib_startup_pass_claimed=False,
                   owner_resource_amendment_path=pins['owner_resource_amendment_path'],
                   owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256'],
                   archive_artifacts=len(rows), request_sha256=result['request_sha256'], witness_sha256=result['restore_witness_sha256'],
                   native_closeout_status='verified_external_post_job', child_native_flag_remains_pending=True)
    summary['peer_release'] = dict(original_path=admission['peer_release_path'],
                                   file_sha256=admission['peer_release_sha256'],
                                   authenticated_copy=peer_copy.relative_to(ROOT).as_posix())
    write_once(ARCHIVE / 'summary.json', origin.canonical(summary))
    write_once(ARCHIVE / 'README.md', ('# Provenance-aware restoration evidence\n\n'
               'This packet preserves metadata for one separately versioned factory restoration, genuine adapter delivery, '
               'focused rejection tests and one locked engineering success. Source/support/query updates and measured cells are zero. '
               'The external closeout authenticates the accepted native Job and fresh absence; the child pending-native flag remains unchanged. '
               'Arrays, selected weights, baseline weights and ancestor packet copies are excluded. Final independent review and '
               'qualification documentation remain separate acceptance requirements.\n').encode())
    for row in rows:
        origin.need(origin.digest(ROOT / row['source']) == origin.digest(ARCHIVE / row['path']) == row['sha256'],
                    'archive exact source/copy pair changed')
    verify_pins(pins, args.expect_pins)
    job_absent(native['job_name'])
    write_once(RUN / 'closeout-result.json', origin.canonical(summary))
    print(json.dumps(dict(passed=True, archive=str(ARCHIVE), artifacts=len(rows), native_closed=True,
                          selected_restores=1, source_updates=0, support_updates=0, query_calls=0, measured_cells=0)))


if __name__ == '__main__':
    main()
