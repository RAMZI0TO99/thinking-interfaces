"""Hold one real engineering claim across complete selection and detached verification."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_child import (CANONICAL, ROOT, RUN, PAUSE, Runtime, digest,
                         canonical, identity, pause_check, read_json, write_json)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins', type=Path, required=True)
parser.add_argument('--expect-pins', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
runtime = Runtime('parent', args.pins, args.expect_pins, args.output)
torch = runtime.install_torch_guards()
from evaluation.phase2_runner import CasePlan, CaseRecorder, environment_digest
from evaluation.phase2_cho_case_inputs import SELECTED_SEEDS
from core.provenance import capture_source
from docs.phase2.cho51_worker_lifecycle_v1.lifecycle import WorkerContext
from docs.phase2.cho51_complete_eegnet_v1.transaction import (
    VerifiedCompleteProof, run_complete_case)
import pytest

OUT = args.output
pins = runtime.pins
original_recorder = CaseRecorder.__init__


def isolated_recorder(self, root, *, output_root=None):
    if (not Path(root).resolve().is_relative_to(OUT) or output_root is None
            or not Path(output_root).resolve().is_relative_to(OUT)):
        runtime.refuse('shared_recorder_constructor', root)
    original_recorder(self, root, output_root=output_root)


CaseRecorder.__init__ = isolated_recorder


class Results:
    def __init__(self):
        self.items, self.calls, self.skipped = 0, [], []
    def pytest_collection_finish(self, session):
        self.items = len(session.items)
    def pytest_runtest_setup(self, item):
        pause_check()
    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.skipped.append({'nodeid': report.nodeid, 'phase': report.when})
        if report.when == 'call' or report.failed:
            self.calls.append({'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome})


reports = Results()
os.chdir(OUT)
pytest_exit = pytest.main(['-q', '-s', '-p', 'no:cacheprovider', '-o', 'addopts=',
    '--import-mode=importlib', '--log-file', str(OUT / 'pytest.log'), '--basetemp', str(OUT / 't'),
    '--junitxml', str(OUT / 'junit.xml'), *[str(ROOT / node) for node in pins['test_nodes']]], plugins=[reports])
tests_passed = (pytest_exit == 0 and reports.items == pins['expected_tests']
    and len(reports.calls) == pins['expected_tests'] and not reports.skipped
    and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in reports.calls))

spec = importlib.util.spec_from_file_location('_complete_native_helpers',
    ROOT / 'docs/phase2/cho51_tensor_verification_v1/launcher.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
view = {'files': {str(ROOT / relative): sha for relative, sha in pins['files'].items()}, 'runtime': pins['runtime']}
operation_pins = native._guard_operation_pins(view)
runtime_pins = native._guard_runtime_pins(view)


def _child_command(request, kind, source_result_sha256=None):
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B',
        str(RUN / ('select_child.py' if kind == 'source' else 'verify_child.py')),
        '--request', str(request.workspace / 'request.json'), '--expect-request', request.sha256]
    if kind == 'detached':
        command += ['--source-result', str(request.selection_output / 'source-result.json'),
                    '--expect-source-result', source_result_sha256]
    return command


def _launch(request, kind, source_result_sha256=None):
    runtime.verify_pins()
    pause_check()
    child = _child_command(request, kind, source_result_sha256)
    seconds, process, job = [getattr(request, kind + suffix) for suffix in ('_seconds', '_process_mib', '_job_mib')]
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(ROOT / 'tools/migration/guard.py'),
        '--purpose', 'isolated claimed complete synthetic EEGNet ' + kind + ', no study arrays or measured cells',
        '--seconds', str(seconds), '--process-mib', str(process), '--job-mib', str(job),
        '--pause-file', str(PAUSE), '--', *child]
    before = {path: identity(path) for path in (request.workspace / 'request.json', request.claim_path,
        request.fixture_identity_path, request.method_config_path)}
    runtime.allowed_guard_command = command
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
            timeout=seconds + 20, check=False)
    finally:
        runtime.allowed_guard_command = None
    for suffix, value in (('stdout', completed.stdout), ('stderr', completed.stderr)):
        with (request.workspace / (kind + '-guard-' + suffix + '.txt')).open('x', encoding='utf-8') as stream:
            stream.write(value)
    lines = completed.stdout.splitlines()
    if not lines:
        raise ValueError('fresh native guard returned no directory')
    directory = Path(lines[0])
    if (not directory.is_absolute() or directory.resolve(strict=True) != directory
            or directory.parent != ROOT / 'runs/migration'):
        raise ValueError('direct fresh native migration directory required')
    dispatch = {'schema': 'cho51_complete_eegnet_inner_dispatch_v1', 'kind': kind,
        'request_sha256': request.sha256, 'case_id': request.plan.case_id,
        'pins_sha256': args.expect_pins, 'child_command': child,
        'native_directory': str(directory), 'guard_exit_code': completed.returncode,
        'source_result_file_sha256': source_result_sha256, 'scientific_admission': False}
    write_json(request.workspace / (kind + '-native-dispatch.json'), dispatch)
    return {'dispatch': dispatch, 'initial_identities': before, 'verified_identities': None}


def _verify_native(request, kind, opaque, source_result_sha256=None):
    runtime.verify_pins()
    dispatch = opaque['dispatch']
    expected_child = _child_command(request, kind, source_result_sha256)
    if (dispatch['child_command'] != expected_child or dispatch['kind'] != kind
            or dispatch['request_sha256'] != request.sha256
            or dispatch['pins_sha256'] != args.expect_pins):
        raise ValueError('independently reconstructed native command/request required')
    directory = Path(dispatch['native_directory'])
    output = request.selection_output if kind == 'source' else request.detached_output
    q_path = output / 'qualification.json'
    paths = [directory / 'receipt.json', directory / 'admission.json', q_path,
        request.workspace / 'request.json', request.claim_path,
        request.fixture_identity_path, request.method_config_path]
    current = {path: identity(path) for path in paths}
    if any(current[path] != pin for path, pin in opaque['initial_identities'].items()):
        raise ValueError('claim/request/input/method pin changed across native work')
    receipt, admission, q = [read_json(path) for path in paths[:3]]
    state = receipt.get('native_state', {})
    required = ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified',
        'atomic_job_assignment_requested', 'atomic_job_assignment_verified', 'assigned',
        'membership_verified', 'resumed', 'job_empty_before_close', 'job_closed',
        'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen')
    name = 'pro3_migration_' + directory.name
    if (dispatch['guard_exit_code'] != 0 or receipt.get('schema') != 'migration_guard_receipt_v1'
            or receipt.get('accepted') is not True or receipt.get('error') is not None
            or receipt.get('job_name') != name or state.get('job_named') != name
            or receipt.get('job_absent') is not True or any(state.get(key) is not True for key in required)
            or state.get('cleanup_errors') != [] or state.get('peak_sampling_errors') != []
            or receipt.get('scientific_admission') is not False
            or receipt.get('result', {}).get('reason') != 'normal'
            or type(receipt.get('result', {}).get('exit_code')) is not int or receipt['result']['exit_code'] != 0):
        raise ValueError('fresh inner native Job did not complete and close cleanly')
    seconds, process, job = [getattr(request, kind + suffix) for suffix in ('_seconds', '_process_mib', '_job_mib')]
    if (admission.get('schema') != 'migration_admission_v1' or admission.get('source_sha256') != CANONICAL
            or admission.get('command') != expected_child or admission.get('operation_pins') != operation_pins
            or admission.get('selected_runtime_pins') != runtime_pins
            or any(type(admission.get(key)) is not int or admission[key] != value for key, value in {
                'process_mib': process, 'job_mib': job, 'active_ram_gib': 4,
                'active_disk_gib': 20, 'native_threads': 1}.items())
            or admission.get('peer_pause_file') != str(PAUSE)):
        raise ValueError('exact inner native admission pins/caps/floors required')
    samples = admission.get('startup_samples')
    if (type(samples) is not list or len(samples) != 2 or receipt.get('startup_samples') != samples
            or any(type(sample.get('available_ram_bytes')) is not int or sample['available_ram_bytes'] < 10 * 1024**3
                or type(sample.get('free_disk_bytes')) is not int or sample['free_disk_bytes'] < 20 * 1024**3 for sample in samples)):
        raise ValueError('fresh inner startup RAM/disk floors required')
    start, deadline, end = [datetime.fromisoformat(value) for value in (
        admission['started_utc'], admission['deadline_utc'], receipt['completed_utc'])]
    if ((deadline - start).total_seconds() != seconds or not start <= end <= deadline
            or any(value.utcoffset() != timezone.utc.utcoffset(value) for value in (start, deadline, end))):
        raise ValueError('exact finite inner deadline required')
    for field, result_field, limit_field, limit in (
        ('peak_process_commit_bytes', 'peak_process_memory_bytes', 'process_limit_bytes', process * 1024**2),
        ('peak_job_commit_bytes', 'peak_job_memory_bytes', 'aggregate_limit_bytes', job * 1024**2)):
        if (type(state.get(field)) is not int or not 0 < state[field] <= limit
                or state.get(limit_field) != limit or receipt['result'].get(result_field) != state[field]):
            raise ValueError('positive measured peaks within exact inner limits required')
    if type(state.get('peak_samples')) is not int or state['peak_samples'] < 1:
        raise ValueError('actual positive peak-sampling count required')
    expected = {'schema': 'cho51_complete_eegnet_' + kind + '_qualification_v1', 'passed': True,
        'pins_sha256': args.expect_pins, 'request_sha256': request.sha256,
        'case_id': request.plan.case_id, 'claim_file_sha256': request.claim_file_sha256,
        'fixture_source_sha256': request.fixture_source_sha256,
        'owner_decision_sha256': request.owner_decision_sha256,
        'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
        'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
        'source_review_sha256': pins['source_review_sha256'],
        'environment_sha256': request.environment_sha256,
        'unexpected_denials': 0, 'torch_threads': 1, 'torch_interop_threads': 1,
        'gpu_hidden': True, 'scientific_admission': False,
        'actual_study_inputs_or_pretrained_weights_used': False, 'original_case_attempts_remaining': 0}
    if any(type(q.get(key)) is not type(value) or q[key] != value for key, value in expected.items()):
        raise ValueError('fresh inner qualification differs from exact claim/source/runtime context')
    calls = q.get('observed_numerical_calls', {})
    if kind == 'source':
        if (calls.get('tensor_backward') != 5253 or calls.get('autograd_backward') != 5253
                or calls.get('autograd_grad', 0) != 0 or calls.get('sgd_step') != 5253
                or q.get('source_updates') != 5151 or q.get('support_updates') != 102):
            raise ValueError('actual complete source/support gradient observations required')
    elif any(calls.get(key, 0) != 0 for key in (
            'optimizer_init', 'sgd_step', 'tensor_backward', 'autograd_backward', 'autograd_grad')):
        raise ValueError('detached verifier performed forbidden fitting')
    protected_paths = [str(request.fixture_root / relative) for relative in (
        'data/processed/cho2017/profile_a/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
        'data/raw/moabb/cho2017/subject_02.mat')]
    if (q.get('protected_target_transitions') != [
            {'enabled': value, 'paths': protected_paths} for value in (True, False)]
            or q.get('protected_target_read_attempts') != []):
        raise ValueError('closed target protection and zero computation target reads required')
    expected_denial = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
        'source_file': str(runtime.connection),
        'source_sha256': pins['files'][runtime.connection.relative_to(ROOT).as_posix()]}
    if q.get('denied_operations') != [expected_denial] or q.get('expected_blocked_ipv6_probes') != 1:
        raise ValueError('exact one independently pinned optional IPv6 denial required')
    if any(q.get('fixture_input_read_phases', {}).get(path, {}).get('during_computation', 0) != 0
            for path in protected_paths):
        raise ValueError('outer target physical contents were read during computation')
    result_path = output / ('source-result.json' if kind == 'source' else 'detached-result.json')
    current[result_path] = identity(result_path)
    result = read_json(result_path)
    if (result != q.get('result') or result.get('schema') != 'cho51_complete_eegnet_' + kind + '_result_v1'
            or result.get('passed') is not True):
        raise ValueError('persisted actual complete result differs from native qualification')
    for path, expected_sha in q['observed_loaded_module_hashes'].items():
        if digest(path) != expected_sha:
            raise ValueError('observed inner module changed')
    native._job_absent(name)
    if any(identity(path) != pin for path, pin in current.items()):
        raise ValueError('native proof changed during independent verification')
    if opaque['verified_identities'] is not None and opaque['verified_identities'] != current:
        raise ValueError('native proof changed before durable parent attestation')
    opaque['verified_identities'] = current
    return {'directory': directory, 'receipt_path': paths[0], 'q_path': q_path, 'result_path': result_path,
        'result': result, 'identities': current, 'state': state}


def backend(request, request_path, request_sha256):
    if request_path != request.workspace / 'request.json' or digest(request_path) != request_sha256 or request.sha256 != request_sha256:
        raise ValueError('exact current claimed source request required')
    source = _launch(request, 'source')
    accepted = _verify_native(request, 'source', source)
    result_sha = accepted['identities'][accepted['result_path']][-1]
    detached = _launch(request, 'detached', result_sha)
    return {'source': source, 'detached': detached, 'source_result_sha256': result_sha}


def verifier(request, opaque):
    source = _verify_native(request, 'source', opaque['source'])
    source_sha = source['identities'][source['result_path']][-1]
    if source_sha != opaque['source_result_sha256']:
        raise ValueError('accepted source result changed before detached proof')
    detached = _verify_native(request, 'detached', opaque['detached'], source_sha)
    result, detached_result = source['result'], detached['result']
    publication = result['publication']
    files = result['publication_files']
    from docs.phase2.cho51_complete_eegnet_v1.selection import _history_summary
    shared = {'request_sha256': request.sha256, 'case_id': request.plan.case_id,
        'claim_file_sha256': request.claim_file_sha256, 'pins_sha256': args.expect_pins,
        'execution_source_sha256': CANONICAL, 'method_config_sha256': request.method_config_sha256,
        'method_config_file_sha256': request.method_config_file_sha256,
        'fixture_identity_sha256': request.fixture_identity_sha256,
        'fixture_identity_file_sha256': request.fixture_identity_file_sha256,
        'selected_candidate': publication['selected_candidate'],
        'selection_evidence_sha256': publication['evidence_sha256'],
        'model_state_sha256': publication['model_state_sha256'],
        'full_selector_verified': True, 'public_selection_verifier_passed': True,
        'engineering_only': True, 'scientific_admission': False,
        'target_prediction_performed': False, 'recorder_used': False,
        'measured_cells': 0, 'actual_study_data_loaded': False,
        'pretrained_weights_loaded': False, 'original_case_attempts_remaining': 0}
    for data in (result, detached_result):
        if any(type(data.get(key)) is not type(value) or data[key] != value for key, value in shared.items()):
            raise ValueError('source and detached proof differ from independent complete request and publication')
    if (result.get('actual_gradient_updates') != 5253 or result.get('source_updates') != 5151
            or result.get('support_updates') != 102 or result.get('fold_count') != 102
            or result.get('final_source_subjects') != 51 or result.get('complete') is not True
            or result.get('public_run_selection_completed') is not True
            or result.get('publication_performed') is not True
            or detached_result.get('source_result_path') != str(source['result_path'])
            or detached_result.get('source_result_file_sha256') != source_sha
            or detached_result.get('publication') != publication
            or detached_result.get('publication_files') != files
            or detached_result.get('publication_witness') != result.get('publication_witness')
            or detached_result.get('model_recipe_sha256') != result.get('model_recipe_sha256')
            or detached_result.get('actual_gradient_updates') != 0
            or detached_result.get('detached_tensor_verified') is not True
            or detached_result.get('all_tensors_equal') is not True
            or detached_result.get('initial_lineage_reconstructed') is not True
            or detached_result.get('public_restore_adapter_released') is not True
            or detached_result.get('publication_performed') is not False
            or detached_result.get('verified_source_gradient_updates') != 5253
            or detached_result.get('verified_source_updates') != 5151
            or detached_result.get('verified_support_updates') != 102
            or detached_result.get('verified_fold_count') != 102
            or detached_result.get('verified_final_source_subjects') != 51):
        raise ValueError('complete source work or independent detached restoration was not established')
    if detached_result.get('restored_publication') != {**publication, 'resumed': True}:
        raise ValueError('detached canonical restored publication differs from exact selected source')
    if set(files) != {'manifest', 'evidence', 'weights', 'selector_evidence'}:
        raise ValueError('exact four immutable publication/evidence file roles required')
    artifact_paths = {name: Path(publication[name]) for name in ('manifest_path', 'evidence_path', 'weights_path')}
    artifact_pins = {name: identity(path) for name, path in artifact_paths.items()}
    for name, path in artifact_paths.items():
        role = name.removesuffix('_path')
        if (not path.is_relative_to(request.fixture_root / 'runs/phase2/selected_sources')
                or files[role]['path'] != str(path) or files[role]['file_sha256'] != artifact_pins[name][-1]
                or files[role]['size_bytes'] != artifact_pins[name][2]
                or files[role]['identity'] != list(artifact_pins[name][:5])):
            raise ValueError('published selected source file differs from accepted source result')
    evidence = read_json(artifact_paths['evidence_path'])
    summary, trace = _history_summary(evidence)
    if any(result.get(key) != value for key, value in summary.items()):
        raise ValueError('source summary differs from independently read complete physical histories')
    manifest = read_json(artifact_paths['manifest_path'])
    m = manifest['payload']
    if detached_result.get('tensor_count') != len(m.get('tensor_schema', {})) or not m.get('tensor_schema'):
        raise ValueError('detached complete restored tensor count differs from the canonical manifest schema')
    for record in (manifest, evidence):
        if record.get('sha256') != hashlib.sha256(canonical(
                {key: value for key, value in record.items() if key != 'sha256'}).encode()).hexdigest():
            raise ValueError('canonical selected source envelope digest differs from physical content')
    if (manifest['sha256'] != publication['manifest_sha256']
            or evidence['sha256'] != publication['evidence_sha256']
            or publication['weights_sha256'] != artifact_pins['weights_path'][-1]
            or m.get('model_state_sha256') != publication['model_state_sha256']
            or m.get('model_recipe_sha256') != result['model_recipe_sha256']
            or m.get('evidence_sha256') != publication['evidence_sha256']
            or m.get('weights_sha256') != publication['weights_sha256']
            or m.get('selected_candidate') != publication['selected_candidate']
            or m.get('source') != result['fixture_source']
            or publication.get('resumed') is not False or publication.get('weights_format') != 'full_v1'
            or publication.get('evidence_format') != 'canonical_json_v1'):
        raise ValueError('actual canonical manifest/evidence/state/recipe digests differ from the two native proofs')
    original_path = request.fixture_root / 'runs/phase2/selection_evidence' / (publication['evidence_sha256'] + '.json')
    original_pin = identity(original_path)
    if (result.get('selection_evidence_path') != str(original_path)
            or files['selector_evidence']['path'] != str(original_path)
            or files['selector_evidence']['file_sha256'] != original_pin[-1]
            or files['selector_evidence']['size_bytes'] != original_pin[2]
            or files['selector_evidence']['identity'] != list(original_pin[:5])
            or read_json(original_path) != evidence):
        raise ValueError('original public selector evidence differs from persisted canonical publication')
    expected_tensor_witness = {key: publication[key] for key in (
        'manifest_sha256', 'evidence_sha256', 'selected_candidate', 'model_state_sha256', 'weights_sha256')}
    expected_tensor_witness['model_recipe_sha256'] = result['model_recipe_sha256']
    if detached_result.get('tensor_witness') != expected_tensor_witness:
        raise ValueError('independent actual canonical tensor witness differs from parent pins')
    transcript_path = request.selection_output / 'optimizer-observations.json'
    transcript = read_json(transcript_path)
    if (result.get('optimizer_trace_path') != str(transcript_path)
            or result.get('optimizer_trace_file_sha256') != digest(transcript_path)
            or transcript.get('actual_gradient_updates') != 5253
            or len(transcript.get('events', [])) != 5253):
        raise ValueError('actual complete optimizer transcript differs from native source observations')
    for index, (event, expected_phase) in enumerate(zip(transcript['events'], trace, strict=True), 1):
        if (event.get('update') != index or event.get('phase') != list(expected_phase)
                or event.get('selected_parameters') != 2642
                or event.get('finite_selected_gradients') is not True
                or event.get('finite_selected_parameters') is not True
                or event.get('selected_state_sha256_before') == event.get('selected_state_sha256_after')):
            raise ValueError('observed actual numerical update differs from canonical full history')
    input_identity = read_json(request.fixture_identity_path)
    if (input_identity.get('sha256') != request.fixture_identity_sha256
            or digest(request.fixture_identity_path) != request.fixture_identity_file_sha256
            or len(input_identity.get('files', {})) != 213):
        raise ValueError('independent full synthetic input identity differs')
    actual_inputs = {path.relative_to(request.fixture_root).as_posix()
        for directory in (request.fixture_root / 'configs', request.fixture_root / 'data')
        for path in directory.rglob('*') if path.is_file() or path.is_symlink()}
    if actual_inputs != set(input_identity['files']):
        raise ValueError('full physical synthetic input inventory changed')
    for relative, expected_pin in input_identity['files'].items():
        if fixture_module._input_pin(request.fixture_root / relative) != expected_pin:
            raise ValueError('physical synthetic input bytes changed before parent attestation')
    return VerifiedCompleteProof(request_sha256=request.sha256, case_id=request.plan.case_id,
        claim_file_sha256=request.claim_file_sha256, execution_source_sha256=CANONICAL,
        independent_pins_sha256=args.expect_pins, owner_decision_sha256=request.owner_decision_sha256,
        environment_sha256=request.environment_sha256,
        source_native_directory=source['directory'], source_native_receipt_file_sha256=source['identities'][source['receipt_path']][-1],
        source_qualification_path=source['q_path'], source_qualification_file_sha256=source['identities'][source['q_path']][-1],
        detached_native_directory=detached['directory'], detached_native_receipt_file_sha256=detached['identities'][detached['receipt_path']][-1],
        detached_qualification_path=detached['q_path'], detached_qualification_file_sha256=detached['identities'][detached['q_path']][-1],
        source_result_path=source['result_path'], source_result_file_sha256=source_sha,
        detached_result_path=detached['result_path'], detached_result_file_sha256=detached['identities'][detached['result_path']][-1],
        manifest_path=artifact_paths['manifest_path'], manifest_file_sha256=artifact_pins['manifest_path'][-1],
        evidence_path=artifact_paths['evidence_path'], evidence_file_sha256=artifact_pins['evidence_path'][-1],
        evidence_sha256=publication['evidence_sha256'], weights_path=artifact_paths['weights_path'],
        weights_file_sha256=artifact_pins['weights_path'][-1], selected_state_sha256=publication['model_state_sha256'],
        source_peak_process_bytes=source['state']['peak_process_commit_bytes'],
        source_peak_job_bytes=source['state']['peak_job_commit_bytes'],
        detached_peak_process_bytes=detached['state']['peak_process_commit_bytes'],
        detached_peak_job_bytes=detached['state']['peak_job_commit_bytes'])


result = {'passed': False, 'tests_passed': tests_passed, 'pytest_exit': int(pytest_exit),
    'collected_tests': reports.items, 'expected_tests': pins['expected_tests'],
    'reports': reports.calls, 'skipped_reports': reports.skipped,
    'engineering_completion': None, 'measured_cells': 0,
    'scientific_admission': False, 'original_case_attempts_remaining': 0}
if tests_passed:
    spec = importlib.util.spec_from_file_location('_complete_fixture_parent_v1',
        ROOT / 'docs/phase2/cho51_source_fold_probe_v1/fixture.py')
    fixture_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = fixture_module
    spec.loader.exec_module(fixture_module)
    fixture = fixture_module.build_fixture(OUT, 'eegnet')
    fixture.verify_inputs()
    recorder_root = fixture.root / 'runs/phase2/lifecycle'
    recorder = CaseRecorder(fixture.root, output_root=recorder_root)
    plans = tuple(CasePlan('cho2017', f'subject_{subject:02d}', method, 5, seed, 1)
        for subject in range(2, 53) for method in ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
        for seed in SELECTED_SEEDS)
    context = WorkerContext(OUT, fixture.root, recorder_root, args.pins, args.expect_pins,
        CANONICAL, pins['owner_decision_sha256'], plans, capture_source(fixture.root), environment_digest())
    plan = CasePlan('cho2017', 'subject_02', 'eegnet', 5, 11, 1)
    (OUT / 'cases').mkdir()
    completion = run_complete_case(recorder, plan, context=context, workspace=OUT / 'cases' / plan.case_id,
        fixture_identity_path=fixture.identity_path, fixture_identity_file_sha256=fixture.identity_file_sha256,
        fixture_identity_sha256=fixture.input_identity['sha256'],
        method_config_path=Path(pins['method_config_path']), method_config_file_sha256=pins['method_config_file_sha256'],
        method_config_sha256=pins['method_config_sha256'], backend=backend, verifier=verifier)
    proof = {key: str(value) if isinstance(value, Path) else value for key, value in asdict(completion.proof).items()}
    result.update(passed=True, engineering_completion=recorder.completion((plan,)),
        request_path=str(completion.request_path), request_sha256=completion.request.sha256,
        claim_path=str(completion.request.claim_path), claim_file_sha256=completion.request.claim_file_sha256,
        attestation_path=str(completion.attestation_path), attestation_file_sha256=completion.attestation_file_sha256,
        engineering_receipt=str(completion.engineering_receipt), proof=proof)
runtime.finish(result)
print(json.dumps({'passed': result['passed'], 'engineering_only': True, 'scientific_admission': False}), flush=True)
raise SystemExit(0 if result['passed'] else 1)
