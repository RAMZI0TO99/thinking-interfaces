"""Archive four completed synthetic probes without interpreting them as science."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = ROOT / 'evidence/cho51-numerical-probes-20261015'
METHODS = ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import io_path, source_check


def signature(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def digest(path):
    path = Path(path)
    before = path.stat()
    with io_path(path).open('rb') as stream:
        opened = os.fstat(stream.fileno())
        value = hashlib.file_digest(stream, 'sha256').hexdigest()
        closed = os.fstat(stream.fileno())
    if (signature(path.stat()) != signature(before) or signature(opened) != signature(closed)
            or signature(opened)[:4] != signature(before)[:4]):
        raise ValueError('file changed while hashing: ' + str(path))
    return value


def read(path):
    path = Path(path)
    if path.resolve(strict=True) != path or any(
        stat.S_ISLNK(p.lstat().st_mode) or getattr(p.lstat(), 'st_file_attributes', 0) & 1024
        for p in (path, *path.parents)
    ):
        raise ValueError('direct artifact paths required')
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 8 * 1024**2:
        raise ValueError('compact single-link regular artifact required')
    with io_path(path).open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(8 * 1024**2 + 1)
        closed = os.fstat(stream.fileno())
    observed = (*signature(before), hashlib.sha256(raw).hexdigest())
    if (signature(path.stat()) != signature(before) or len(raw) != before.st_size
            or signature(opened) != signature(closed) or signature(opened)[:4] != signature(before)[:4]):
        raise ValueError('artifact changed while reading: ' + str(path))
    return raw, observed


def decode(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError('nonfinite JSON: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def write(path, value):
    with io_path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def main():
    pin_path = RUN / 'pins.json'
    pin_raw, pin_identity = read(pin_path)
    pins, pins_sha = decode(pin_raw), pin_identity[-1]
    if source_check(ROOT) != CANONICAL:
        raise ValueError('canonical source changed')

    def current_pins():
        if source_check(ROOT) != CANONICAL or read(pin_path)[1] != pin_identity:
            raise ValueError('tested canonical source or pins changed')
        for rel, expected in pins['files'].items():
            if digest(ROOT / rel) != expected:
                raise ValueError('tested source/context changed: ' + rel)
        for name, expected in pins['runtime'].items():
            if digest(Path(name)) != expected:
                raise ValueError('runtime changed: ' + name)

    current_pins()
    launcher_path = ROOT / 'docs/phase2/cho51_tensor_verification_v1/launcher.py'
    if pins['files'].get(launcher_path.relative_to(ROOT).as_posix()) != digest(launcher_path):
        raise ValueError('pinned standard-library absence helper required')
    spec = importlib.util.spec_from_file_location('_numerical_closeout_stdlib_launcher', launcher_path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    view = {'files': {str(ROOT / rel): sha for rel, sha in pins['files'].items()}, 'runtime': pins['runtime']}
    operations = launcher._guard_operation_pins(view)
    runtimes = launcher._guard_runtime_pins(view)
    commands = {method: [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'child.py'),
        '--pins', str(pin_path), '--expect-pins', pins_sha, '--output', str(RUN / f'output_{method}_001'),
        '--method', method] for method in METHODS}
    paths = {path for path in RUN.iterdir() if path.is_file() and path.suffix in {'.py', '.ps1', '.json'}}
    candidate = ROOT / 'docs/phase2/cho51_numerical_probe_v1'
    paths.update(path for path in candidate.iterdir() if path.is_file() and path.suffix in {'.py', '.md'})
    validated_identities = {pin_path: pin_identity}
    results = {}

    def dispatch_for(method):
        path = RUN / f'dispatch_result_{method}_001.json'
        raw, observed = read(path)
        dispatch = decode(raw)
        if (dispatch.get('method') != method or dispatch.get('pins_sha256') != pins_sha
                or dispatch.get('child_command') != commands[method]
                or type(dispatch.get('guard_exit_code')) is not int):
            raise ValueError('exact independently recorded launch dispatch required')
        directory = Path(dispatch['native_directory'])
        if (not directory.is_absolute() or directory.resolve(strict=True) != directory
                or directory.parent != ROOT / 'runs/migration'):
            raise ValueError('direct dispatched native directory required')
        validated_identities[path] = observed
        return dispatch, directory

    for directory in sorted((ROOT / 'runs/migration').iterdir()):
        admission_path = directory / 'admission.json'
        if not directory.is_dir() or not admission_path.is_file():
            continue
        admission_raw, admission_identity = read(admission_path)
        admission = decode(admission_raw)
        method = next((m for m in METHODS if admission.get('command') == commands[m]), None)
        if method is None:
            continue
        if method in results:
            raise ValueError('one fresh native attempt per method required')
        dispatch, dispatched_directory = dispatch_for(method)
        if dispatched_directory != directory:
            raise ValueError('native admission differs from recorded launch dispatch')
        receipt_path = directory / 'receipt.json'
        receipt_raw, receipt_identity = read(receipt_path)
        receipt = decode(receipt_raw)
        validated_identities.update({admission_path: admission_identity, receipt_path: receipt_identity})
        state = receipt['native_state']
        required = ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified',
            'atomic_job_assignment_requested', 'atomic_job_assignment_verified', 'assigned',
            'membership_verified', 'resumed', 'job_empty_before_close', 'job_closed',
            'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen')
        if (receipt.get('schema') != 'migration_guard_receipt_v1'
                or receipt.get('job_name') != 'pro3_migration_' + directory.name
                or state.get('job_named') != receipt['job_name'] or receipt.get('job_absent') is not True
                or (receipt.get('accepted') is True and any(state.get(key) is not True for key in required))
                or state.get('job_created') is not True or state.get('job_empty_before_close') is not True
                or state.get('job_closed') is not True
                or state.get('cleanup_errors') != [] or state.get('peak_sampling_errors') != []
                or receipt.get('scientific_admission') is not False
                or admission.get('schema') != 'migration_admission_v1'
                or admission.get('source_sha256') != CANONICAL
                or admission.get('operation_pins') != operations or admission.get('selected_runtime_pins') != runtimes
                or any(type(admission.get(key)) is not int or admission[key] != expected for key, expected in (
                    ('process_mib', 2048), ('job_mib', 3072), ('active_ram_gib', 4), ('active_disk_gib', 20), ('native_threads', 1)))
                or admission.get('peer_pause_file') != 'D:\\Aenv\\pro2\\WORK\\resume-20261015-001\\coordination\\PRO2_REQUEST_PRO3_PAUSE.json'):
            raise ValueError('exact native supervision/source/cleanup required: ' + method)
        samples = admission['startup_samples']
        if (len(samples) != 2 or receipt.get('startup_samples') != samples
                or any(s['available_ram_bytes'] < 10 * 1024**3 or s['free_disk_bytes'] < 20 * 1024**3 for s in samples)):
            raise ValueError('unchanged fresh startup floors required')
        start, deadline, end = (datetime.fromisoformat(value) for value in (
            admission['started_utc'], admission['deadline_utc'], receipt['completed_utc']))
        if ((deadline - start).total_seconds() != 300 or end < start
                or (receipt.get('accepted') is True and end > deadline)
                or any(value.utcoffset() != timezone.utc.utcoffset(value) for value in (start, deadline, end))):
            raise ValueError('finite current300-second native execution required')
        if (state.get('process_limit_bytes') != 2048 * 1024**2 or state.get('aggregate_limit_bytes') != 3072 * 1024**2
                or type(state.get('peak_samples')) is not int or state['peak_samples'] < 1):
            raise ValueError('measured native memory limits required')
        launcher._job_absent(receipt['job_name'])
        output = RUN / f'output_{method}_001'
        qualification = None
        q_path = output / 'qualification.json'
        if q_path.is_file():
            q_raw, q_identity = read(q_path)
            qualification = decode(q_raw)
            validated_identities[q_path] = q_identity
            if qualification.get('pins_sha256') != pins_sha or qualification.get('method') != method:
                raise ValueError('child qualification differs from independent dispatch')
            for name, expected in qualification['observed_loaded_module_hashes'].items():
                if digest(Path(name)) != expected:
                    raise ValueError('observed loaded module changed')
        numerical_passed = receipt.get('accepted') is True
        if dispatch['guard_exit_code'] != (0 if numerical_passed else 1):
            raise ValueError('recorded launch exit differs from native acceptance')
        if numerical_passed:
            if (receipt.get('error') is not None or receipt['result'].get('reason') != 'normal'
                    or type(receipt['result'].get('exit_code')) is not int or receipt['result']['exit_code'] != 0
                    or not qualification or qualification.get('passed') is not True
                    or qualification.get('unexpected_denials') != 0
                    or qualification.get('torch_threads') != 1 or qualification.get('torch_interop_threads') != 1
                    or qualification.get('gpu_hidden') is not True):
                raise ValueError('accepted numerical probe requires exact complete child proof')
            for field, result_field, cap in (
                ('peak_process_commit_bytes', 'peak_process_memory_bytes', 2048 * 1024**2),
                ('peak_job_commit_bytes', 'peak_job_memory_bytes', 3072 * 1024**2)):
                if (type(state.get(field)) is not int or not 0 < state[field] <= cap
                        or receipt['result'].get(result_field) != state[field]):
                    raise ValueError('bounded measured native peaks required')
        paths.update((admission_path, receipt_path))
        paths.update(p for p in directory.iterdir() if p.is_file() and (p.name == 'deadline.json' or p.name.startswith('command')))
        if output.is_dir():
            paths.update(output.glob('*.json'))
        results[method] = dict(method=method, passed=numerical_passed,
            native_directory=directory.relative_to(ROOT).as_posix(), job_name=receipt['job_name'],
            native_error=receipt.get('error'), native_result=receipt.get('result'), completed_utc=receipt['completed_utc'],
            elapsed_native_seconds=(end-start).total_seconds(),
            peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes'],
            job_created=True,
            native_job_closed_empty_freshly_absent=True,
            probe_result=None if qualification is None else qualification.get('result'))
    for method in METHODS:
        if method in results:
            continue
        dispatch, directory = dispatch_for(method)
        if (directory / 'admission.json').exists():
            raise ValueError('an unmatched native admission cannot be treated as startup refusal')
        path = directory / 'receipt.json'
        raw, observed = read(path)
        receipt = decode(raw)
        state = receipt['native_state']
        expected_name = 'pro3_migration_' + directory.name
        if (receipt.get('schema') != 'migration_guard_receipt_v1' or receipt.get('accepted') is not False
                or receipt.get('job_name') != expected_name or receipt.get('job_absent') is not True
                or receipt.get('scientific_admission') is not False or state.get('job_created') is not False
                or receipt.get('result') is not None or dispatch['guard_exit_code'] != 1
                or type(receipt.get('error')) is not str or not receipt['error']):
            raise ValueError('exact no-Job startup refusal required')
        launcher._job_absent(expected_name)
        validated_identities[path] = observed
        paths.add(path)
        results[method] = dict(method=method, passed=False, native_directory=directory.relative_to(ROOT).as_posix(),
            job_name=expected_name, native_error=receipt['error'], native_result=None,
            completed_utc=receipt['completed_utc'], elapsed_native_seconds=None,
            job_created=False, native_job_closed_empty_freshly_absent=None,
            cleanup='not_applicable_no_job_created', peak_process_bytes=None, peak_job_bytes=None, probe_result=None)
    if set(results) != set(METHODS):
        raise ValueError('four completed exact-command probes required')
    current_pins()
    artifacts = []
    for path in sorted(paths):
        raw, observed = read(path)
        if path in validated_identities and observed != validated_identities[path]:
            raise ValueError('validated proof changed before archival')
        artifacts.append((path, raw, observed))
    OUT.mkdir(exist_ok=False)
    manifest = []
    for path, raw, observed in artifacts:
        target = OUT / 'artifacts' / path.relative_to(ROOT)
        io_path(target.parent).mkdir(parents=True, exist_ok=True)
        with io_path(target).open('xb') as stream:
            stream.write(raw)
        if read(path)[1] != observed or digest(target) != observed[-1]:
            raise ValueError('artifact changed across archival')
        manifest.append(dict(source=path.relative_to(ROOT).as_posix(), path=target.relative_to(OUT).as_posix(),
            bytes=len(raw), sha256=observed[-1]))
    current_pins()
    for path, expected in validated_identities.items():
        if read(path)[1] != expected:
            raise ValueError('native/child proof changed across archival')
    for result in results.values():
        launcher._job_absent(result['job_name'])
    summary = dict(schema='cho51_four_method_numerical_closeout_v1', observed_utc=datetime.now(timezone.utc).isoformat(),
        all_four_probes_passed=all(r['passed'] for r in results.values()), methods=[results[m] for m in METHODS],
        pins_sha256=pins_sha, canonical_source_sha256=CANONICAL, canonical_files=432,
        source_context_pins_rechecked=len(pins['files']), runtime_pins_rechecked=len(pins['runtime']),
        artifact_count=len(manifest), study_data_or_pretrained_weights_used=False,
        full_selector_or_worker_resource_bound_established=False, complete_1020_case_roster_verified=False,
        original_case_attempts_remaining=0, scientific_admission=False)
    write(OUT / 'manifest.json', {'artifacts': manifest})
    write(OUT / 'summary.json', summary)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
