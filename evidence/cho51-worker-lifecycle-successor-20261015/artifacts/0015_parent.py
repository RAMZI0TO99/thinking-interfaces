"""Guarded engineering recorder rehearsal with separately guarded numerical children."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import time
import msvcrt
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent
SITE = ROOT / '.venv/Lib/site-packages'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
METHODS = ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
PAUSE = Path('D:/Aenv/pro2/WORK/resume-20261015-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json')
PAUSES = tuple(Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001' /
               'coordination/PRO2_REQUEST_PRO3_PAUSE.json'
               for day in ('20261007', '20261012', '20261013', '20261015'))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins', required=True, type=Path)
parser.add_argument('--expect-pins', required=True)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


if args.pins.resolve(strict=True) != RUN / 'pins.json' or digest(args.pins) != args.expect_pins:
    raise ValueError('fresh independent parent pins required')
pins = json.loads(args.pins.read_bytes())
if (pins.get('schema') != 'cho51_worker_lifecycle_fresh_pins_v1'
        or pins.get('canonical_source_sha256') != CANONICAL or pins.get('predecessor_files') != 563
        or pins.get('methods') != list(METHODS)
        or any(pins.get(key) != value for key, value in {
            'outer_seconds': 600, 'process_mib': 4096, 'job_mib': 6144,
            'seconds_per_method': 300, 'startup_ram_gib': 10, 'active_ram_gib': 4,
            'disk_gib': 20, 'threads': 1,
        }.items())):
    raise ValueError('exact finite nested engineering scope required')
OUT = args.output.resolve()
if OUT != RUN / 'validation_001' or args.output.absolute() != OUT:
    raise ValueError('fresh direct owned lifecycle output required')
OUT.mkdir(exist_ok=False)
for variable, folder in {
    'TEMP': 'temp', 'TMP': 'temp', 'TMPDIR': 'temp', 'MPLCONFIGDIR': 'mpl',
    'HF_HOME': 'hf', '_MNE_FAKE_HOME_DIR': 'mne-home', 'XDG_CACHE_HOME': 'cache',
    'NUMBA_CACHE_DIR': 'numba', 'JOBLIB_TEMP_FOLDER': 'joblib',
}.items():
    (OUT / folder).mkdir(exist_ok=True)
    os.environ[variable] = str(OUT / folder)
for variable in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[variable] = '1'
os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                  PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(SITE)]
from tools.migration.common import source_check


def verify_pins():
    if digest(args.pins) != args.expect_pins or source_check(ROOT) != CANONICAL:
        raise ValueError('parent pins or canonical source changed')
    for relative, expected in pins['files'].items():
        if digest(ROOT / relative) != expected:
            raise ValueError('parent source/library pin changed: ' + relative)
    for name, expected in pins['runtime'].items():
        if digest(name) != expected:
            raise ValueError('parent runtime changed: ' + name)
    review = json.loads(Path(pins['source_review_path']).read_bytes())
    if (digest(Path(pins['source_review_path'])) != pins['source_review_sha256']
            or review.get('source_only') is not True
            or review.get('remaining_actionable_findings') != []
            or review.get('files') != pins['reviewed_files']):
        raise ValueError('independent exact lifecycle source review changed')


verify_pins()
if (Path(pins['mne_resource_path']) != SITE / 'mne/data/fsaverage/fsaverage-fiducials.fif'
        or pins.get('mne_resource_bytes') != 260
        or Path(pins['mne_resource_path']).stat().st_size != 260
        or pins.get('mne_resource_sha256') != '0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'
        or digest(Path(pins['mne_resource_path'])) != pins['mne_resource_sha256']):
    raise ValueError('only the exact independently pinned 260-byte MNE anatomical template is allowed')
git_command = shutil.which('git')
if git_command is None or str(Path(git_command).resolve()) not in pins['runtime']:
    raise ValueError('fixture provenance needs the independently pinned installed Git')
git_path = Path(git_command).resolve()
connection = SITE / 'urllib3/util/connection.py'
denied = []
hostname_queries = 0
git_queries = 0
allowed_guard_command = None
file_api = ctypes.WinDLL('kernel32', use_last_error=True)
file_api.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong]
file_api.GetFinalPathNameByHandleW.restype = ctypes.c_ulong


def descriptor_owned(descriptor):
    if type(descriptor) is not int:
        return False
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        length = file_api.GetFinalPathNameByHandleW(msvcrt.get_osfhandle(descriptor), buffer, len(buffer), 0)
        return 0 < length < len(buffer) and path_of(buffer.value).is_relative_to(OUT)
    except OSError:
        return False


def path_of(value):
    value = os.fsdecode(value)
    if value.startswith('\\\\?\\'):
        value = value[4:]
    return Path(value).resolve()


def refuse(event, value=None):
    denied.append({'event': event, 'detail': repr(value)[:500]})
    raise PermissionError('engineering parent denied: ' + event)


def stack_has(function, path):
    frame = sys._getframe(1)
    while frame:
        if frame.f_code.co_name == function and path_of(frame.f_code.co_filename) == path:
            return True
        frame = frame.f_back
    return False


def spawn(values):
    global git_queries
    executable, arguments, cwd, environment = values
    git_forms = [[git_command, '--no-optional-locks', *tail] for tail in (
        ['rev-parse', '--verify', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'])]
    exact = lambda command: arguments == command or arguments == subprocess.list2cmdline(command)
    executable_is = lambda path: ((executable is None and os.name == 'nt')
        or isinstance(executable, (str, bytes, os.PathLike)) and path_of(executable) == path)
    if (any(exact(command) for command in git_forms) and executable_is(git_path)
            and cwd is not None and path_of(cwd).is_relative_to(OUT) and environment is None
            and stack_has('capture_source', ROOT / 'core/provenance.py')):
        git_queries += 1
        return
    if (allowed_guard_command is not None and exact(allowed_guard_command)
            and executable_is(Path(allowed_guard_command[0]).resolve())
            and cwd is not None and path_of(cwd) == ROOT and environment is None
            and stack_has('_native_backend', Path(__file__).resolve())):
        return
    refuse('subprocess.Popen', values)


def audit(event, values):
    global hostname_queries
    if event == 'socket.gethostname':
        hostname_queries += 1
    elif event.startswith('socket.'):
        if event == 'socket.__new__' and values[1:] == (socket.AF_INET6, socket.SOCK_STREAM, 0) and stack_has('_has_ipv6', connection):
            denied.append({'event': event, 'classification': 'blocked_optional_ipv6_import_probe',
                           'source_file': str(connection), 'source_sha256': pins['files'][connection.relative_to(ROOT).as_posix()]})
            raise PermissionError('optional IPv6 import probe blocked before socket creation')
        refuse(event, values)
    elif event == 'subprocess.Popen':
        spawn(values)
    elif event in {'os.system', 'os.startfile', 'os.posix_spawn', 'os.fork', 'os.forkpty'} or event.startswith(('os.exec', 'os.spawn')):
        refuse(event, values)
    elif event == 'open':
        mode = values[1] if isinstance(values[1], str) else ''
        flags = values[2] if isinstance(values[2], int) else 0
        writing = any(char in mode for char in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if not isinstance(values[0], (str, bytes, os.PathLike)):
            if writing and not descriptor_owned(values[0]):
                refuse('unbound_write', values)
            return
        path = path_of(values[0])
        if writing and not path.is_relative_to(OUT):
            refuse('outside_output_write', path)
        if not writing and not path.is_relative_to(OUT):
            parts = tuple(part.lower() for part in path.parts)
            data_path = any(parts[i:i + 2] in {('data', 'raw'), ('data', 'processed'), ('data', 'interim')} for i in range(len(parts) - 1))
            if path == SITE / 'mne/data/fsaverage/fsaverage-fiducials.fif':
                return
            if data_path or 'weights' in parts or path.suffix.lower() in {'.npz', '.npy', '.mat', '.edf', '.gdf', '.fif', '.set', '.pt', '.pth', '.ckpt', '.safetensors'}:
                if not (path.suffix.lower() == '.pth' and path.is_relative_to(SITE)):
                    refuse('data_or_checkpoint_read', path)
    elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace', 'os.link', 'os.symlink', 'os.chmod', 'os.utime', 'os.truncate'}:
        for value in values[:2 if event in {'os.rename', 'os.replace', 'os.link', 'os.symlink'} else 1]:
            if isinstance(value, (str, bytes, os.PathLike)) and path_of(value).is_relative_to(OUT):
                continue
            if event == 'os.mkdir' and isinstance(value, (str, bytes, os.PathLike)) and path_of(value).is_dir():
                raise FileExistsError(17, 'existing shared directory creation refused', os.fsdecode(value))
            refuse('outside_output_mutation', value)


sys.addaudithook(audit)
started = time.monotonic()
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)


def no_model(*arguments, **keywords):
    refuse('parent_model_optimizer_or_backward_call')


torch.nn.Module.__init__ = no_model
torch.load = no_model
torch.serialization.load = no_model
torch.jit.load = no_model
torch.optim.Optimizer.__init__ = no_model
torch.Tensor.backward = no_model
torch.autograd.backward = no_model
torch.autograd.grad = no_model
import safetensors
import safetensors.torch

safetensors.safe_open = no_model
safetensors.torch.safe_open = no_model
for name in ('load', 'load_file', 'load_model', 'save', 'save_file', 'save_model'):
    setattr(safetensors.torch, name, no_model)
from evaluation.phase2_runner import CasePlan, CaseRecorder, environment_digest
from evaluation.phase2_cho_case_inputs import SELECTED_SEEDS
from core.provenance import source_fingerprint, capture_source
from docs.phase2.cho51_worker_lifecycle_v1.lifecycle import (
    WorkerContext, VerifiedWorkerProof, run_engineering_case,
)

original_recorder = CaseRecorder.__init__


def isolated_recorder(self, root, *, output_root=None):
    if (not Path(root).resolve().is_relative_to(OUT) or output_root is None
            or not Path(output_root).resolve().is_relative_to(OUT)):
        refuse('shared_recorder_constructor', root)
    original_recorder(self, root, output_root=output_root)


CaseRecorder.__init__ = isolated_recorder
import pytest


class Results:
    def __init__(self):
        self.items = 0
        self.calls = []
        self.skipped = []

    def pytest_collection_finish(self, session):
        self.items = len(session.items)

    def pytest_runtest_setup(self, item):
        if any(path.exists() for path in PAUSES):
            pytest.fail('genuine peer pause requested')

    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.skipped.append({'nodeid': report.nodeid, 'phase': report.when})
        if report.when == 'call' or report.failed:
            self.calls.append({'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome})


test_results = Results()
pytest_exit = pytest.main([
    '-q', '-s', '-p', 'no:cacheprovider', '-o', 'addopts=', '--import-mode=importlib',
    '--log-file', str(OUT / 'pytest.log'), '--basetemp', str(OUT / 't'),
    '--junitxml', str(OUT / 'junit.xml'), *[str(ROOT / node) for node in pins['test_nodes']],
], plugins=[test_results])
tests_passed = (pytest_exit == 0 and test_results.items == pins['expected_tests']
    and len(test_results.calls) == pins['expected_tests'] and not test_results.skipped
    and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in test_results.calls))

spec = importlib.util.spec_from_file_location('_lifecycle_native_helpers', ROOT / 'docs/phase2/cho51_tensor_verification_v1/launcher.py')
native_helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native_helpers)
view = {'files': {str(ROOT / relative): sha for relative, sha in pins['files'].items()}, 'runtime': pins['runtime']}
operation_pins = native_helpers._guard_operation_pins(view)
runtime_pins = native_helpers._guard_runtime_pins(view)


def identity(path):
    info = path.stat()
    if (path.resolve(strict=True) != path or path.is_symlink() or not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1):
        raise ValueError('direct single-link immutable proof file required')
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, digest(path))


def _native_backend(request, request_path, physical_sha):
    global allowed_guard_command
    verify_pins()
    if physical_sha != request.sha256 or digest(request_path) != physical_sha:
        raise ValueError('exact freshly claimed worker request required')
    child_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'child.py'),
                     '--request', str(request_path), '--expect-request', physical_sha]
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(ROOT / 'tools/migration/guard.py'),
        '--purpose', 'isolated claimed engineering lifecycle numerical child: ' + request.plan.method,
        '--seconds', '300', '--process-mib', str(request.process_mib), '--job-mib', str(request.job_mib),
        '--pause-file', str(PAUSE), '--', *child_command]
    before = {request_path: identity(request_path), request.claim_path: identity(request.claim_path)}
    allowed_guard_command = command
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=330, check=False)
    finally:
        allowed_guard_command = None
    with (request.workspace / 'guard-stdout.txt').open('x', encoding='utf-8') as stream:
        stream.write(completed.stdout)
    with (request.workspace / 'guard-stderr.txt').open('x', encoding='utf-8') as stream:
        stream.write(completed.stderr)
    lines = completed.stdout.splitlines()
    if not lines:
        raise ValueError('inner native guard returned no result directory')
    directory = Path(lines[0])
    if (not directory.is_absolute() or directory.resolve(strict=True) != directory
            or directory.parent != ROOT / 'runs/migration'):
        raise ValueError('inner guard result directory must be direct and independently dispatched')
    with (request.workspace / 'native-dispatch.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump({'schema': 'cho51_worker_lifecycle_inner_dispatch_v1',
            'method': request.plan.method, 'case_id': request.plan.case_id,
            'request_sha256': physical_sha, 'claim_file_sha256': request.claim_file_sha256,
            'pins_sha256': args.expect_pins, 'child_command': child_command,
            'native_directory': str(directory), 'guard_exit_code': completed.returncode,
            'scientific_admission': False}, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    return {'directory': directory, 'exit_code': completed.returncode,
            'child_command': child_command, 'initial_identities': before, 'verified_identities': None}


def _verify_native(request, dispatch):
    verify_pins()
    expected_child = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'child.py'),
                      '--request', str(request.workspace / 'request.json'), '--expect-request', request.sha256]
    if dispatch['child_command'] != expected_child:
        raise ValueError('exact independently reconstructed numerical child command required')
    directory = dispatch['directory']
    receipt_path, admission_path = directory / 'receipt.json', directory / 'admission.json'
    q_path = request.workspace / 'child_output/qualification.json'
    request_path = request.workspace / 'request.json'
    paths = [request_path, request.claim_path, receipt_path, admission_path, q_path]
    current = {path: identity(path) for path in paths}
    if any(current[path] != prior for path, prior in dispatch['initial_identities'].items()):
        raise ValueError('claim or request changed across native child')
    receipt = native_helpers.read_json(receipt_path)
    admission = native_helpers.read_json(admission_path)
    qualification = native_helpers.read_json(q_path, maximum_bytes=8 * 1024**2)
    state = receipt.get('native_state', {})
    required = ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified',
        'atomic_job_assignment_requested', 'atomic_job_assignment_verified', 'assigned',
        'membership_verified', 'resumed', 'job_empty_before_close', 'job_closed',
        'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen')
    name = 'pro3_migration_' + directory.name
    if (dispatch['exit_code'] != 0 or receipt.get('schema') != 'migration_guard_receipt_v1'
            or receipt.get('accepted') is not True or receipt.get('error') is not None
            or receipt.get('job_name') != name or state.get('job_named') != name
            or receipt.get('job_absent') is not True or any(state.get(key) is not True for key in required)
            or state.get('cleanup_errors') != [] or state.get('peak_sampling_errors') != []
            or receipt.get('scientific_admission') is not False
            or receipt.get('result', {}).get('reason') != 'normal'
            or type(receipt.get('result', {}).get('exit_code')) is not int or receipt['result']['exit_code'] != 0):
        raise ValueError('fresh nested native child did not exit normally and close its empty Job')
    if (admission.get('schema') != 'migration_admission_v1' or admission.get('source_sha256') != CANONICAL
            or admission.get('command') != dispatch['child_command']
            or admission.get('operation_pins') != operation_pins or admission.get('selected_runtime_pins') != runtime_pins
            or any(type(admission.get(key)) is not int or admission[key] != expected for key, expected in {
                'process_mib': request.process_mib, 'job_mib': request.job_mib,
                'active_ram_gib': 4, 'active_disk_gib': 20, 'native_threads': 1}.items())
            or admission.get('peer_pause_file') != str(PAUSE)):
        raise ValueError('nested native command/source/runtime/caps differ from independent request')
    samples = admission.get('startup_samples')
    if (type(samples) is not list or len(samples) != 2 or receipt.get('startup_samples') != samples
            or any(type(sample.get('available_ram_bytes')) is not int or sample['available_ram_bytes'] < 10 * 1024**3
                   or type(sample.get('free_disk_bytes')) is not int or sample['free_disk_bytes'] < 20 * 1024**3 for sample in samples)):
        raise ValueError('fresh nested startup floors required')
    start, deadline, end = [datetime.fromisoformat(value) for value in (admission['started_utc'], admission['deadline_utc'], receipt['completed_utc'])]
    if ((deadline - start).total_seconds() != 300 or not start <= end <= deadline
            or any(value.utcoffset() != timezone.utc.utcoffset(value) for value in (start, deadline, end))):
        raise ValueError('nested native execution exceeded exact finite time bound')
    for field, result_field, limit_field, limit in (
        ('peak_process_commit_bytes', 'peak_process_memory_bytes', 'process_limit_bytes', request.process_mib * 1024**2),
        ('peak_job_commit_bytes', 'peak_job_memory_bytes', 'aggregate_limit_bytes', request.job_mib * 1024**2),
    ):
        if (type(state.get(field)) is not int or not 0 < state[field] <= limit
                or state.get(limit_field) != limit or receipt['result'].get(result_field) != state[field]):
            raise ValueError('bounded measured nested native peaks required')
    if type(state.get('peak_samples')) is not int or state['peak_samples'] < 1:
        raise ValueError('positive measured native peak samples required')
    expected_q = {
        'schema': 'cho51_worker_lifecycle_child_qualification_v1', 'passed': True,
        'method': request.plan.method, 'pins_sha256': args.expect_pins,
        'request_sha256': request.sha256, 'case_id': request.plan.case_id,
        'claim_file_sha256': request.claim_file_sha256, 'fixture_source_sha256': request.fixture_source_sha256,
        'owner_decision_sha256': request.owner_decision_sha256, 'execution_source_sha256': CANONICAL,
        'environment_sha256': request.environment_sha256,
        'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
        'unexpected_denials': 0, 'torch_threads': 1, 'torch_interop_threads': 1, 'gpu_hidden': True,
        'actual_study_inputs_or_pretrained_weights_used': False, 'whole_numerical_worker_verified': False,
        'real_recorder_or_original_attempt_used': False, 'scientific_admission': False,
        'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
    }
    if any(type(qualification.get(key)) is not type(value) or qualification[key] != value for key, value in expected_q.items()):
        raise ValueError('nested numerical qualification differs from current pinned claim/request')
    result = qualification.get('result', {})
    expected_result = {'schema': 'cho51_numerical_probe_v1', 'method': request.plan.method,
        'passed': True, 'actual_gradient_updates': 8, 'rate_cases': 2, 'channels': 64,
        'source_examples': 2, 'support_examples': 10, 'query_examples': 2,
        'samples': 512 if request.plan.method == 'eegnet' else 800,
        'model_blocks': 0 if request.plan.method == 'eegnet' else 12,
        'random_initialization': True, 'full_architecture_shape': True, 'baseline_checkpoint_used': False,
        'public_source_fit_verified': False, 'full_worker_verified': False, 'scientific_admission': False}
    if any(type(result.get(key)) is not type(value) or result[key] != value for key, value in expected_result.items()):
        raise ValueError('exact eight-gradient full-shape synthetic numerical result required')
    calls = qualification.get('observed_numerical_calls', {})
    if type(calls.get('tensor_backward')) is not int or calls['tensor_backward'] != 8 or type(calls.get('sgd_step')) is not int or calls['sgd_step'] != 8:
        raise ValueError('observed numerical calls differ from eight real updates')
    checks = result.get('checks')
    if type(checks) is not list or len(checks) != 2:
        raise ValueError('both candidate-rate numerical witnesses required')
    positive = ('finite_logits', 'finite_losses', 'finite_selected_gradients', 'finite_parameters',
        'updates_nonempty_within_mask', 'frozen_state_unchanged', 'source_unchanged', 'rng_unchanged',
        'no_storage_alias', 'query_state_unchanged', 'exact_replay', 'state_roundtrip_exact',
        'query_roundtrip_exact', 'fixture_inputs_unchanged')
    for index, check in enumerate(checks, start=1):
        if any(check.get(key) is not True for key in positive) or check.get('actual_gradient_updates') != 4:
            raise ValueError('all per-rate numerical assertions must be literally true')
        weight = request.workspace / f'child_output/rate_{index:02d}_fullstate.safetensors'
        current[weight] = identity(weight)
        if (check.get('weights_file') != str(weight) or check.get('weights_sha256') != current[weight][-1]
                or type(check.get('weights_bytes')) is not int or check['weights_bytes'] != weight.stat().st_size
                or not 0 < check['weights_bytes'] <= 25 * 1024**2):
            raise ValueError('direct bounded persisted numerical state differs')
    for path, expected in qualification['observed_loaded_module_hashes'].items():
        if digest(path) != expected:
            raise ValueError('inner loaded module changed')
    native_helpers._job_absent(name)
    if any(identity(path) != value for path, value in current.items()):
        raise ValueError('native child proof changed during verification')
    if dispatch['verified_identities'] is not None and dispatch['verified_identities'] != current:
        raise ValueError('native child proof changed before parent attestation')
    dispatch['verified_identities'] = current
    verify_pins()
    return VerifiedWorkerProof(
        request_sha256=request.sha256, case_id=request.plan.case_id,
        claim_file_sha256=request.claim_file_sha256, execution_source_sha256=CANONICAL,
        independent_pins_sha256=args.expect_pins, owner_decision_sha256=request.owner_decision_sha256,
        environment_sha256=request.environment_sha256,
        native_directory=directory, native_receipt_file_sha256=current[receipt_path][-1],
        qualification_path=q_path, qualification_file_sha256=current[q_path][-1],
        peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes'],
    )


results = []
fixture = OUT / 'fixture'
recorder_root = fixture / 'runs/phase2/lifecycle'
if tests_passed:
    fixture.mkdir()
    recorder = CaseRecorder(fixture, output_root=recorder_root)
    fixture_source_sha = source_fingerprint(fixture)
    if fixture_source_sha == CANONICAL:
        raise ValueError('isolated fixture provenance must differ from execution code provenance')
    plans = tuple(CasePlan('cho2017', f'subject_{subject:02d}', method, 5, seed, 1)
                  for subject in range(2, 53) for method in METHODS for seed in SELECTED_SEEDS)
    context = WorkerContext(OUT, fixture, recorder_root, args.pins, args.expect_pins,
                            CANONICAL, pins['owner_decision_sha256'], plans,
                            capture_source(fixture), environment_digest())
    (OUT / 'cases').mkdir()
    for method in METHODS:
        if any(path.exists() for path in PAUSES):
            break
        plan = CasePlan('cho2017', 'subject_02', method, 5, 11, 1)
        try:
            completion = run_engineering_case(recorder, plan, context=context,
                workspace=OUT / 'cases' / plan.case_id, backend=_native_backend, verifier=_verify_native)
            proof = asdict(completion.proof)
            proof['native_directory'] = str(completion.proof.native_directory)
            proof['qualification_path'] = str(completion.proof.qualification_path)
            results.append({'method': method, 'passed': True, 'request_path': str(completion.request_path),
                'request_sha256': completion.request.sha256, 'claim_path': str(completion.request.claim_path),
                'claim_file_sha256': completion.request.claim_file_sha256,
                'attestation_path': str(completion.attestation_path),
                'attestation_file_sha256': completion.attestation_file_sha256,
                'engineering_receipt': str(completion.engineering_receipt), 'proof': proof})
        except Exception as error:
            workspace = OUT / 'cases' / plan.case_id
            results.append({'method': method, 'passed': False, 'workspace': str(workspace),
                'request_path': str(workspace / 'request.json'),
                'native_dispatch': str(workspace / 'native-dispatch.json'),
                'error': type(error).__name__ + ': ' + str(error)[:1000]})
            break
    if recorder.measured_identities():
        raise ValueError('engineering lifecycle rehearsal published measured cells')
    for name in ('cells', 'successes', 'publication_intents'):
        if list((recorder_root / name).glob('*')):
            raise ValueError('engineering rehearsal published a scientific terminal artifact')
verify_pins()
expected_probe = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
                  'source_file': str(connection), 'source_sha256': pins['files'][connection.relative_to(ROOT).as_posix()]}
unexpected = [row for row in denied if row != expected_probe]
environment_sha = environment_digest()
loaded = {str(Path(name).resolve()): digest(name) for module in tuple(sys.modules.values())
          if (name := getattr(module, '__file__', None)) and Path(name).is_file()
          and not Path(name).resolve().is_relative_to(OUT)}
passed = (tests_passed and len(results) == 4 and all(row['passed'] is True for row in results)
          and not unexpected and len(denied) <= 1 and not any(path.exists() for path in PAUSES)
          and torch.get_num_threads() == 1 and torch.get_num_interop_threads() == 1
          and os.environ.get('CUDA_VISIBLE_DEVICES') == '')
payload = {
    'schema': 'cho51_worker_lifecycle_parent_qualification_v1', 'passed': passed,
    'pins_sha256': args.expect_pins, 'pytest_exit': int(pytest_exit),
    'collected_tests': test_results.items, 'expected_tests': pins['expected_tests'],
    'reports': test_results.calls, 'skipped_reports': test_results.skipped,
    'results': results, 'engineering_completion': sum(row['passed'] is True for row in results),
    'nested_windows_job_compatibility_verified': passed,
    'measured_cells': 0, 'fixture_root': str(fixture), 'recorder_root': str(recorder_root),
    'elapsed_seconds': time.monotonic() - started, 'observed_utc': datetime.now(timezone.utc).isoformat(),
    'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
    'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
    'observed_loaded_module_hashes': loaded, 'loaded_module_files': len(loaded),
    'environment_sha256': environment_sha, 'torch_threads': torch.get_num_threads(),
    'torch_interop_threads': torch.get_num_interop_threads(), 'gpu_hidden': os.environ.get('CUDA_VISIBLE_DEVICES') == '',
    'hostname_metadata_queries': hostname_queries, 'read_only_git_queries': git_queries,
    'denied_operations': denied, 'unexpected_denials': len(unexpected),
    'actual_study_inputs_or_pretrained_weights_used': False, 'full_worker_verified': False,
    'scientific_admission': False, 'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
}
with (OUT / 'qualification.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
for path, expected in loaded.items():
    if digest(path) != expected:
        raise ValueError('loaded parent module changed')
print(json.dumps({'passed': passed, 'engineering_completion': payload['engineering_completion'], 'scientific_admission': False}))
raise SystemExit(0 if passed else 1)
