"""Standard-library-only finite native launch and receipt binding for one case.

The unchanged migration guard owns the only compute Job. No injected executor
or caller-provided witness can stand in for its accepted execution receipt.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CANONICAL_SHA = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
PACKAGE = ROOT / 'docs/phase2/cho51_tensor_verification_v1'
PAUSE = Path('D:/Aenv/pro2/WORK/resume-20261015-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json')
GIB = 1024**3
DEPENDENCIES = (
    'docs/phase2/cho51_publication_collection_v1/collection.py',
    'docs/phase2/cho51_input_collection_v1/collection.py',
    'docs/phase2/cho51_selection_files_v1/selection_files.py',
    'docs/phase2/cho51_recorder_collection_v1/collector.py',
    'docs/phase2/cho51_execution_interfaces_v1/interfaces.py',
    'docs/phase2/cho51_worker_bridge_v1/worker_bridge.py',
    'docs/phase2/cho51_route_candidate_v1/route_contract.py',
    '.venv/Lib/site-packages/urllib3/util/connection.py',
    '.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif',
)


def digest(path: Path) -> str:
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('independent SHA256 required')


def _direct(path: Path) -> Path:
    if not isinstance(path, Path) or not path.is_absolute() or path.resolve(strict=True) != path:
        raise ValueError('direct absolute existing path required')
    for ancestor in (path, *path.parents):
        st = ancestor.lstat()
        if stat.S_ISLNK(st.st_mode) or getattr(st, 'st_file_attributes', 0) & 1024:
            raise ValueError('linked/reparse path refused')
    return path


def read_json(path: Path, maximum_bytes=1024**2, *, expected_sha256=None):
    _direct(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= maximum_bytes:
        raise ValueError('bounded single-linked regular JSON file required')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(maximum_bytes + 1)
        closed = os.fstat(stream.fileno())
    after = path.stat()
    identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)
    if identity(before) != identity(opened) or identity(before) != identity(closed) or identity(before) != identity(after) or len(raw) != before.st_size:
        raise ValueError('JSON changed while reading')
    if expected_sha256 is not None:
        _sha(expected_sha256)
        if hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise ValueError('independent JSON byte SHA differs')
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def _write(path: Path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def _payload_sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def verify_bundle_pins(bundle):
    for group in ('files', 'runtime', 'assets'):
        for name, expected in bundle[group].items():
            path = _direct(Path(name))
            # Installed runtime distributions can intentionally hardlink their
            # executables. Keep direct-path and byte pins for those binaries;
            # writable source/publication artifacts still require one link.
            if (group != 'runtime' and path.stat().st_nlink != 1) or digest(path) != expected:
                raise ValueError('pinned file changed: ' + name)
    if digest(Path(bundle['input_path'])) != bundle['input_file_sha256']:
        raise ValueError('pinned tensor input changed')


def load_bundle(path: Path, expected_sha256: str):
    _sha(expected_sha256)
    bundle = read_json(path, expected_sha256=expected_sha256)
    if digest(path) != expected_sha256:
        raise ValueError('independent bundle SHA differs')
    required = {'schema', 'source_root', 'workspace', 'input_path', 'input_file_sha256',
                'request_sha256', 'witness_path', 'files', 'runtime', 'assets', 'limits',
                'canonical_source_sha256', 'native_child_path', 'request_root', 'git_executable'}
    if type(bundle) is not dict or set(bundle) != required or bundle['schema'] != 'cho51_tensor_bundle_v1':
        raise ValueError('tensor bundle schema differs')
    workspace = Path(bundle['workspace'])
    _direct(workspace)
    if (path != workspace / 'bundle.json' or not workspace.is_relative_to(ROOT / 'runs/coordination')
            or workspace == ROOT / 'runs/coordination' or bundle['source_root'] != str(ROOT)
            or bundle['canonical_source_sha256'] != CANONICAL_SHA
            or bundle['input_path'] != str(workspace / 'input.json')
            or bundle['witness_path'] != str(workspace / 'witness.json')
            or bundle['native_child_path'] != str(PACKAGE / 'child.py')):
        raise ValueError('tensor bundle paths/source differ')
    _direct(Path(bundle['request_root']))
    for name in ('input_file_sha256', 'request_sha256'):
        _sha(bundle[name])
    limits = bundle['limits']
    if (type(limits) is not dict or set(limits) != {'seconds', 'process_mib', 'job_mib'}
            or type(limits['seconds']) is not int or not 10 <= limits['seconds'] <= 600
            or type(limits['process_mib']) is not int or limits['process_mib'] != 2048
            or type(limits['job_mib']) is not int or limits['job_mib'] != 3072):
        raise ValueError('finite reviewed tensor limits required')
    for group in ('files', 'runtime', 'assets'):
        if type(bundle[group]) is not dict or not bundle[group]:
            raise ValueError('complete independent pin groups required')
        for name, sha in bundle[group].items():
            _sha(sha)
            path_value = Path(name)
            if not path_value.is_absolute():
                raise ValueError('absolute pinned file required')
            if group == 'assets' and not path_value.is_relative_to(Path(bundle['request_root'])):
                raise ValueError('tensor asset escapes request root')
    manifest = read_json(ROOT / 'tools/migration/source-files.json')
    required_files = {str(ROOT / row['path']): row['sha256'] for row in manifest['files']}
    required_files.update({str(PACKAGE / name): digest(PACKAGE / name) for name in ('launcher.py', 'child.py', 'contract.py')})
    required_files.update({str(ROOT / name): digest(ROOT / name) for name in DEPENDENCIES})
    required_files.update({str(p): digest(p) for p in (ROOT / 'tools/migration').iterdir()
                           if p.is_file() and p.suffix in {'.py', '.ps1', '.json', '.lock'}})
    if (manifest['source_sha256'] != CANONICAL_SHA
            or any(bundle['files'].get(name) != sha for name, sha in required_files.items())
            or bundle['git_executable'] not in bundle['runtime']
            or str(ROOT / '.venv/Scripts/python.exe') not in bundle['runtime']):
        raise ValueError('complete current canonical/launcher/runtime pins required')
    payload = read_json(Path(bundle['input_path']), expected_sha256=bundle['input_file_sha256'])
    if payload.get('project_root') != bundle['request_root'] or _payload_sha(payload) != bundle['request_sha256']:
        raise ValueError('tensor request binding differs')
    return bundle


def prepare_tensor_bundle(payload, *, expected_request_sha256, workspace: Path, asset_pins, seconds=120):
    """Reserve one unused engineering workspace; caller independently supplies assets."""
    _sha(expected_request_sha256)
    if type(payload) is not dict or _payload_sha(payload) != expected_request_sha256:
        raise ValueError('independent tensor request digest differs')
    if (not workspace.is_absolute() or workspace.exists()
            or not workspace.is_relative_to(ROOT / 'runs/coordination')
            or workspace == ROOT / 'runs/coordination' or workspace.parent.resolve(strict=True) != workspace.parent):
        raise ValueError('unused direct owned tensor workspace required')
    project_root = _direct(Path(payload['project_root']))
    sys.path.insert(0, str(ROOT / 'tools/migration'))
    from common import source_check
    if source_check(ROOT) != CANONICAL_SHA:
        raise ValueError('canonical source changed')
    manifest = read_json(ROOT / 'tools/migration/source-files.json')
    files = {str(ROOT / row['path']): row['sha256'] for row in manifest['files']}
    for path in [*(PACKAGE / name for name in ('contract.py', 'launcher.py', 'child.py')),
                 *(ROOT / name for name in DEPENDENCIES),
                 *(p for p in (ROOT / 'tools/migration').iterdir() if p.is_file() and p.suffix in {'.py', '.ps1', '.json', '.lock'})]:
        files[str(path)] = digest(path)
    git = shutil.which('git')
    if git is None:
        raise ValueError('pinned read-only Git runtime required')
    git = str(Path(git).resolve(strict=True))
    runtime = {}
    for path in (ROOT / '.venv/Scripts/python.exe', Path(sys.base_prefix) / 'python.exe',
                 Path(sys.base_prefix) / 'python312.dll', Path(sys.base_prefix) / 'python3.dll', Path(git)):
        if path.is_file():
            runtime[str(path.resolve())] = digest(path)
    if type(asset_pins) is not dict or not asset_pins:
        raise ValueError('independently pinned publication assets required')
    assets = dict(asset_pins)
    for name, sha in assets.items():
        _sha(sha)
        path = _direct(Path(name))
        if not path.is_relative_to(project_root) or digest(path) != sha:
            raise ValueError('tensor asset differs from independent pin')
    workspace.mkdir(exist_ok=False)
    _write(workspace / 'input.json', payload)
    bundle = dict(schema='cho51_tensor_bundle_v1', source_root=str(ROOT), workspace=str(workspace),
                  input_path=str(workspace / 'input.json'), input_file_sha256=digest(workspace / 'input.json'),
                  request_sha256=expected_request_sha256, request_root=str(project_root),
                  witness_path=str(workspace / 'witness.json'), files=files, runtime=runtime, assets=assets,
                  limits=dict(seconds=seconds, process_mib=2048, job_mib=3072),
                  canonical_source_sha256=CANONICAL_SHA, native_child_path=str(PACKAGE / 'child.py'), git_executable=git)
    _write(workspace / 'bundle.json', bundle)
    sha = digest(workspace / 'bundle.json')
    load_bundle(workspace / 'bundle.json', sha)
    verify_bundle_pins(bundle)
    return sha


def _job_absent(name):
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.OpenJobObjectW.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_wchar_p]
    api.OpenJobObjectW.restype = ctypes.c_void_p
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    ctypes.set_last_error(0)
    handle = api.OpenJobObjectW(4, False, name)
    error = ctypes.get_last_error()
    if handle:
        api.CloseHandle(handle)
    if handle or error != 2:
        raise ValueError('fresh native Job absence unconfirmed')


def _guard_operation_pins(bundle):
    return {Path(name).relative_to(ROOT).as_posix(): sha for name, sha in bundle['files'].items()
            if (Path(name).parent == ROOT / 'tools/migration' and Path(name).suffix in {'.py', '.ps1', '.json', '.lock'})
            or Path(name) == ROOT / 'evaluation/phase2_supervision_primitives.py'}


def _guard_runtime_pins(bundle):
    return {name: sha for name, sha in bundle['runtime'].items()
            if Path(name) == ROOT / '.venv/Scripts/python.exe' or Path(name).name in {'python312.dll', 'python3.dll'}}


def admit_native_receipt(bundle, bundle_sha, native: Path):
    """Bind one actual guard receipt; this proves no full-roster/scientific result."""
    _sha(bundle_sha)
    if load_bundle(Path(bundle['workspace']) / 'bundle.json', bundle_sha) != bundle:
        raise ValueError('current tensor bundle differs from native request')
    _direct(native)
    if native.parent != ROOT / 'runs/migration':
        raise ValueError('native receipt must be in direct migration output')
    workspace = Path(bundle['workspace'])
    proof_paths = (native / 'admission.json', native / 'receipt.json',
                   Path(bundle['witness_path']), workspace / 'child-scope.json')
    def proof_identity(path):
        _direct(path)
        value = path.stat()
        return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, digest(path))
    proof_before = {path: proof_identity(path) for path in proof_paths}
    admission = read_json(native / 'admission.json')
    receipt = read_json(native / 'receipt.json')
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', bundle['native_child_path'],
               '--bundle', str(workspace / 'bundle.json'), '--expect-bundle', bundle_sha]
    state = receipt.get('native_state', {})
    limits = bundle['limits']
    if (admission.get('schema') != 'migration_admission_v1' or admission.get('command') != command
            or admission.get('source_sha256') != CANONICAL_SHA
            or any(type(admission.get(key)) is not int or admission[key] != value for key, value in (
                ('process_mib', 2048), ('job_mib', 3072), ('active_ram_gib', 4), ('active_disk_gib', 20), ('native_threads', 1)))
            or admission.get('peer_pause_file') != str(PAUSE)
            or admission.get('operation_pins') != _guard_operation_pins(bundle)
            or admission.get('selected_runtime_pins') != _guard_runtime_pins(bundle)
            or receipt.get('schema') != 'migration_guard_receipt_v1'
            or receipt.get('accepted') is not True or receipt.get('job_absent') is not True
            or receipt.get('scientific_admission') is not False or receipt.get('error') is not None
            or receipt.get('job_name') != 'pro3_migration_' + native.name
            or type(receipt.get('result')) is not dict or receipt['result'].get('reason') != 'normal'
            or type(receipt['result'].get('exit_code')) is not int or receipt['result']['exit_code'] != 0
            or any(state.get(key) is not True for key in ('job_created', 'created_suspended', 'limits_set',
                'atomic_job_assignment_requested', 'atomic_job_assignment_verified', 'assigned', 'limits_query_verified',
                'membership_verified', 'resumed', 'job_empty_before_close', 'job_closed', 'root_exit_after_job_close',
                'process_handle_closed', 'thread_handle_closed', 'assignment_step_seen'))
            or state.get('cleanup_errors') != [] or state.get('peak_sampling_errors') != []):
        raise ValueError('native guard admission/execution/cleanup binding differs')
    if (type(state.get('process_limit_bytes')) is not int or state['process_limit_bytes'] != 2048 * 1024**2
            or type(state.get('aggregate_limit_bytes')) is not int or state['aggregate_limit_bytes'] != 3072 * 1024**2
            or type(state.get('peak_samples')) is not int or state['peak_samples'] <= 0
            or state.get('job_named') != receipt['job_name']):
        raise ValueError('native measured limit values differ')
    for name, cap in (('peak_process_commit_bytes', 2048 * 1024**2), ('peak_job_commit_bytes', 3072 * 1024**2)):
        if type(state.get(name)) is not int or not 0 < state[name] <= cap:
            raise ValueError('measured native peak exceeds reviewed cap or is missing')
    if (receipt['result'].get('peak_process_memory_bytes') != state['peak_process_commit_bytes']
            or receipt['result'].get('peak_job_memory_bytes') != state['peak_job_commit_bytes']):
        raise ValueError('native peak result differs from observed Job state')
    start = datetime.fromisoformat(admission['started_utc'])
    deadline = datetime.fromisoformat(admission['deadline_utc'])
    completed = datetime.fromisoformat(receipt['completed_utc'])
    if (any(value.utcoffset() != timezone.utc.utcoffset(value) for value in (start, deadline, completed))
            or not (0 < (deadline - start).total_seconds() == limits['seconds'] and start <= completed <= deadline)):
        raise ValueError('finite native deadline/completion differs')
    samples = admission.get('startup_samples')
    if (type(samples) is not list or len(samples) != 2 or receipt.get('startup_samples') != samples
            or any(type(s.get('available_ram_bytes')) is not int or s['available_ram_bytes'] < 10 * GIB
                   or type(s.get('free_disk_bytes')) is not int or s['free_disk_bytes'] < 20 * GIB for s in samples)):
        raise ValueError('fresh two-sample native startup floors unconfirmed')
    verify_bundle_pins(bundle)
    _job_absent(receipt['job_name'])
    witness = read_json(Path(bundle['witness_path']))
    # Exact digest admission is implemented without importing project/model code
    # into this standard-library parent; the child independently uses contract.py.
    payload = read_json(Path(bundle['input_path']), expected_sha256=bundle['input_file_sha256'])
    pub = payload['publication']
    expected = dict(schema='cho51_tensor_child_witness_v1', request_sha256=bundle['request_sha256'],
                    case_id=pub['case_id'], training_performed=False,
                    **{key: pub[key] for key in ('manifest_sha256', 'evidence_sha256', 'selected_candidate',
                       'model_recipe_sha256', 'model_state_sha256', 'weights_sha256')})
    if type(witness) is not dict or set(witness) != set(expected) or witness != expected or witness['training_performed'] is not False:
        raise ValueError('exact tensor witness differs from admitted request')
    scope = read_json(workspace / 'child-scope.json')
    expected_probe = dict(event='socket.__new__', classification='blocked_optional_ipv6_import_probe',
        source_file=str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
        source_sha256=bundle['files'][str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py')])
    denials = scope.get('denied_operations')
    if (scope.get('schema') != 'cho51_tensor_child_scope_v1' or scope.get('status') != 'verified'
            or scope.get('error') is not None
            or any(scope.get(key) is not True for key in ('actual_tensor_restoration_performed',
                'canonical_tensor_verifier_unchanged', 'no_fitting_hooks_installed'))
            or scope.get('environment_sha256') != pub['environment_sha256']
            or scope.get('request_sha256') != bundle['request_sha256']
            or type(denials) is not list or len(denials) > 1 or any(row != expected_probe for row in denials)
            or type(scope.get('torch_threads')) is not int or scope['torch_threads'] != 1
            or type(scope.get('torch_interop_threads')) is not int or scope['torch_interop_threads'] != 1
            or scope.get('gpu_hidden') is not True):
        raise ValueError('tensor child execution scope differs')
    if digest(workspace / 'bundle.json') != bundle_sha:
        raise ValueError('tensor bundle changed during native receipt admission')
    verify_bundle_pins(bundle)
    if any(proof_identity(path) != prior for path, prior in proof_before.items()):
        raise ValueError('native execution proof changed during admission')
    return dict(schema='cho51_tensor_native_result_v1', request_sha256=bundle['request_sha256'],
                case_id=pub['case_id'], native_directory=str(native),
                receipt_file_sha256=digest(native / 'receipt.json'), witness_file_sha256=digest(Path(bundle['witness_path'])),
                bundle_sha256=bundle_sha, native_supervision_verified=True, one_case_tensor_digest_verified=True,
                full_roster_verified=False, full_selector_evidence_verified=False, scientific_admission=False,
                peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes'])


def launch_tensor_bundle(path: Path, expected_sha256: str):
    bundle = load_bundle(path, expected_sha256)
    workspace = Path(bundle['workspace'])
    if Path(bundle['witness_path']).exists() or (workspace / 'native-result.json').exists():
        raise ValueError('fresh one-case tensor output required')
    verify_bundle_pins(bundle)
    _write(workspace / 'launch-reservation.json', dict(bundle_sha256=expected_sha256, observed_utc=datetime.now(timezone.utc).isoformat()))
    python = str(ROOT / '.venv/Scripts/python.exe')
    command = [python, '-I', '-S', '-B', str(ROOT / 'tools/migration/guard.py'),
               '--purpose', 'one adopted51 selected tensor engineering verification; no fitting or science',
               '--seconds', str(bundle['limits']['seconds']), '--process-mib', '2048', '--job-mib', '3072',
               '--pause-file', str(PAUSE), '--', python, '-I', '-S', '-B', bundle['native_child_path'],
               '--bundle', str(path), '--expect-bundle', expected_sha256]
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    lines = process.stdout.splitlines()
    native = Path(lines[0]) if lines else None
    _write(workspace / 'launch-result.json', dict(returncode=process.returncode, stdout=process.stdout, stderr=process.stderr))
    if process.returncode or native is None:
        raise ValueError('finite tensor guard refused/failed; preserve launch-result and native receipt')
    result = admit_native_receipt(bundle, expected_sha256, native)
    _write(workspace / 'native-result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--expect-bundle', required=True)
    args = parser.parse_args()
    print(json.dumps(launch_tensor_bundle(args.bundle, args.expect_bundle), sort_keys=True))


if __name__ == '__main__':
    main()
