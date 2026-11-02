"""New present-byte inventory runner. Requires independent review and admission."""
import ctypes
import dataclasses
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid
import hashlib
import types
import shutil
from datetime import UTC, datetime, timedelta

ROOT = Path(__file__).absolute().parents[3]
HERE = Path(__file__).absolute().parent
BASE = ROOT / 'runs/coordination/cho51_p3_inventory_observation_20261029_v8'
STOP = ROOT / 'runs/coordination/PROJECT_STOP.json'
REQUIRED = [
    'tools/custody_boundary/v8/inventory.py',
    'tools/custody_boundary/v8/test_inventory.py',
    'tools/custody_boundary/v8/child_entry.py',
    'tools/custody_boundary/v8/validation_runner.py',
    'tools/custody_boundary/v8/README.md',
    'tools/custody_boundary/v8/PROTOCOL.md',
    'evaluation/phase2_supervision_primitives.py',
    'tools/migration/job_adapter.py',
    'docs/PROJECT_EXECUTION_POLICY.md',
    'docs/phase2/cho51_p3_inventory_contract_20261029.md',
]
LIMITS = {'startup_ram_gib': 4, 'active_ram_gib': 4, 'disk_gib': 20,
          'process_mib': 512, 'job_mib': 768, 'child_seconds': 45,
          'work_seconds': 75, 'whole_seconds': 90, 'payload_bytes': 1048576,
          'threads': 1, 'gpu_visible': False}
FALSES = {'historical_custody_closed': False, 'historical_operation_released': False,
          'historical_retry_allowed': False, 'boundary_qualified': False,
          'launch_authorized': False, 'scientific_admission': False}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def strict(raw):
    if len(raw) > 1048576:
        raise ValueError('record exceeds limit')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate field')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))


def encoded(value):
    raw = (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    if len(raw) > 1048576:
        raise ValueError('record exceeds limit')
    return raw


def load_pinned_inventory(request_raw, caller_digest, source_raw):
    if len(request_raw) > 1048576 or hashlib.sha256(request_raw).hexdigest() != caller_digest:
        raise ValueError('bootstrap admission hash/bound')
    request = strict(request_raw)
    pin = request['sources']['tools/custody_boundary/v8/inventory.py']
    if len(source_raw) > 1048576 or pin != {'bytes': len(source_raw), 'sha256': hashlib.sha256(source_raw).hexdigest()}:
        raise ValueError('bootstrap inventory source hash/bound')
    module = types.ModuleType('_inventory_v8')
    module.__file__ = str(HERE / 'inventory.py')
    # Execute exactly the verified in-memory bytes, never reopen this path to import.
    exec(compile(source_raw, module.__file__, 'exec'), module.__dict__)
    return module


def bounded_read(path):
    with path.open('rb') as stream:
        raw = stream.read(1048577)
    if len(raw) > 1048576:
        raise ValueError('bootstrap file exceeds1MiB')
    return raw


def main():
    began = time.monotonic()
    if sys.platform != 'win32' or len(sys.argv) != 3:
        raise ValueError('Windows, admission path and caller digest required')
    def watchdog():
        while time.monotonic() - began < 90:
            time.sleep(.05)
        os._exit(124)
    threading.Thread(target=watchdog, daemon=True).start()
    admission_path = Path(sys.argv[1])
    if admission_path.parent != BASE or not admission_path.name.startswith('admission_'):
        raise ValueError('admission location refused')
    mod = load_pinned_inventory(bounded_read(admission_path), sys.argv[2], bounded_read(HERE / 'inventory.py'))
    pins = mod.RetainedInventory()
    outputs = None
    out = None
    result = None
    state = {}
    samples = []
    accepted = False
    error = None
    end = None
    next_resource_check = 0.0
    memory = ctypes.create_string_buffer(64)
    kernel = ctypes.WinDLL('kernel32.dll', use_last_error=True, winmode=0x800)
    kernel.GlobalMemoryStatusEx.argtypes = [ctypes.c_void_p]
    kernel.GlobalMemoryStatusEx.restype = ctypes.c_int
    def checkpoint():
        nonlocal next_resource_check
        if time.monotonic() - began >= 75 or (end is not None and datetime.now(UTC) >= end):
            raise RuntimeError('observation work/admission expired')
        mod.checked_path(STOP.parent)
        try:
            STOP.lstat()
        except FileNotFoundError:
            pass
        else:
            raise RuntimeError('local stop present')
        if time.monotonic() >= next_resource_check:
            ctypes.c_uint32.from_buffer(memory).value = 64
            if not kernel.GlobalMemoryStatusEx(memory):
                raise OSError(ctypes.get_last_error(), 'memory observation')
            available = ctypes.c_uint64.from_buffer(memory, 16).value
            if available < 4 * 1024**3 or shutil.disk_usage(ROOT).free < 20 * 1024**3:
                raise RuntimeError('observation resource floor')
            next_resource_check = time.monotonic() + .2
    pins.checkpoint = checkpoint
    try:
        admission_path = Path(sys.argv[1])
        if admission_path.parent != BASE or not admission_path.name.startswith('admission_'):
            raise ValueError('admission location refused')
        raw = pins.read(admission_path)
        if mod.digest(raw) != sys.argv[2]:
            raise ValueError('caller admission digest mismatch')
        request = strict(raw)
        fields = {'schema', 'operation_id', 'mode', 'created_utc', 'expires_utc',
                  'sources', 'runtime', 'review', 'contract_adoption', 'limits', 'scientific_admission'}
        if set(request) != fields or request['schema'] != 'cho51_p3_inventory_admission_v8' or request['scientific_admission'] is not False:
            raise ValueError('admission schema refused')
        operation = str(uuid.UUID(request['operation_id']))
        if operation != request['operation_id'] or request['mode'] not in {'tests', 'inventory'}:
            raise ValueError('operation identity refused')
        start, end = (datetime.fromisoformat(request[k].replace('Z', '+00:00')) for k in ('created_utc', 'expires_utc'))
        now = datetime.now(UTC)
        if start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0) or not start <= now < end or not 0 < (end-start).total_seconds() <= 900:
            raise ValueError('admission window refused')
        if type(request['limits']) is not dict or set(request['limits']) != set(LIMITS) or any(type(request['limits'][k]) is not type(v) or request['limits'][k] != v for k, v in LIMITS.items()):
            raise ValueError('limits mismatch')
        if type(request['sources']) is not dict or set(request['sources']) != set(REQUIRED):
            raise ValueError('exact source map required')
        for name, pin in request['sources'].items():
            pins.read(ROOT / name, pin)
        review_ref = request['review']
        if set(review_ref) != {'path', 'bytes', 'sha256'} or review_ref['path'] != 'source-review.json':
            raise ValueError('review reference refused')
        review = strict(pins.read(BASE / review_ref['path'], {k: review_ref[k] for k in ('bytes', 'sha256')}))
        if review['status'] != 'ACCEPTED_SOURCE' or review['sources'] != request['sources'] or review['reviewer'] in review['authors']:
            raise ValueError('independent source review required')
        adoption_ref = request['contract_adoption']
        if (type(adoption_ref) is not dict or set(adoption_ref) != {'path', 'bytes', 'sha256'}
                or adoption_ref['path'] != 'contract-adoption.json'):
            raise ValueError('contract adoption reference refused')
        adoption = strict(pins.read(BASE / adoption_ref['path'], {k: adoption_ref[k] for k in ('bytes', 'sha256')}))
        if (set(adoption) != {'schema', 'author', 'status', 'created_utc', 'contract_sha256', 'source_review_sha256', *FALSES}
                or adoption['schema'] != 'cho51_p3_inventory_contract_adoption_v8'
                or adoption['author'] != 'project_root' or adoption['status'] != 'ADOPTED_SCOPED_INVENTORY_ONLY'
                or adoption['contract_sha256'] != request['sources']['docs/phase2/cho51_p3_inventory_contract_20261029.md']['sha256']
                or adoption['source_review_sha256'] != review_ref['sha256']
                or any(adoption[k] is not False for k in FALSES)):
            raise ValueError('exact reviewed contract adoption required')
        adoption_time = datetime.fromisoformat(adoption['created_utc'].replace('Z', '+00:00'))
        if adoption_time.utcoffset() != timedelta(0) or adoption_time > start:
            raise ValueError('contract adoption must precede admission')
        runtime = request['runtime']
        python_root = Path(sys.base_prefix).resolve()
        if type(runtime) is not dict or not runtime or Path(sys.executable).resolve() != python_root / 'python.exe':
            raise ValueError('runtime root refused')
        if str(python_root / 'python.exe') not in runtime:
            raise ValueError('executable pin required')
        for name, pin in runtime.items():
            path = Path(name)
            if not path.is_absolute() or not path.is_relative_to(python_root):
                raise ValueError('runtime scope refused')
            pins.read(path, pin)
        roster = {str(ROOT / name) for name in REQUIRED} | set(runtime)
        cache = BASE / 'disabled-bytecode' / operation
        if sys.pycache_prefix != str(cache):
            raise ValueError('fresh bytecode prefix required')
        def no_stop():
            mod.checked_path(STOP.parent)
            try:
                STOP.lstat()
            except FileNotFoundError:
                return
            raise RuntimeError('local stop present or unknown')
        def no_cache():
            mod.checked_path(cache.parent)
            try:
                cache.lstat()
            except FileNotFoundError:
                return
            raise RuntimeError('cache exists or unknown')
        no_stop()
        no_cache()
        attempts = BASE / 'attempts'
        for directory in [*reversed(attempts.parents), attempts]:
            pins.retain_directory(directory)
        out = attempts / operation
        out.mkdir()
        pins.retain_directory(out)
        outputs = mod.Outputs(pins, out)
        outputs.write('claim.json', encoded({'operation_id': operation, 'admission_sha256': mod.digest(raw), 'created_utc': now.isoformat()}))
        primitive = load('_inventory_supervision', ROOT / 'evaluation/phase2_supervision_primitives.py')
        adapter = load('_inventory_job_adapter', ROOT / 'tools/migration/job_adapter.py')
        adapter.MEMORY_LIMIT_BYTES = 512 * 1024**2
        adapter.AGGREGATE_LIMIT_BYTES = 768 * 1024**2
        state = {key: False for key in ('limits_set', 'limits_query_verified', 'job_created', 'created_suspended',
            'atomic_job_assignment_requested', 'atomic_job_assignment_verified', 'assigned', 'membership_verified',
            'resumed', 'job_empty_before_close', 'job_closed', 'root_exit_after_job_close', 'process_handle_closed',
            'thread_handle_closed', 'assignment_step_seen', 'owned_job_termination_called')}
        state.update(peak_samples=0, peak_process_commit_bytes=0, peak_job_commit_bytes=0,
                     cleanup_errors=[], peak_sampling_errors=[])
        adapter.install_job_adapter(primitive, state, None)
        def sensor(path):
            no_stop()
            no_cache()
            if time.monotonic() - began >= 75 or datetime.now(UTC) >= end:
                raise RuntimeError('work bound expired')
            return primitive.live_resources(path)
        for _ in range(2):
            sample = sensor(ROOT)
            samples.append(dataclasses.asdict(sample))
            if sample.available_ram_bytes < 4 * 1024**3 or sample.free_disk_bytes < 20 * 1024**3:
                raise RuntimeError('resource floor')
            time.sleep(.2)
        for key in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONUSERBASE'):
            os.environ.pop(key, None)
        for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            os.environ[key] = '1'
        os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
        deadline = min(end, datetime.now(UTC) + timedelta(seconds=45))
        outputs.write('deadline.json', (json.dumps({'schema': 'phase2_supervision_deadlines_v1',
            'attempt_deadline_utc': deadline.isoformat(), 'session_deadline_utc': deadline.isoformat()},
            sort_keys=True, separators=(',', ':')) + '\n').encode())
        command = [sys.executable, '-I', '-S', '-B', '-X', 'pycache_prefix=' + str(cache),
                   str(HERE / 'child_entry.py'), request['mode'], str(out)]
        outputs.write('dispatch.json', encoded({'command': command, 'start_attempted': True,
            'custody_known_before_native_call': False, 'startup_samples': samples}))
        result = primitive.run_supervised(command, cwd=ROOT, deadline_path=out / 'deadline.json',
            sensor=sensor, poll_seconds=.1, process_memory_limit_bytes=adapter.MEMORY_LIMIT_BYTES)
        needed = ('atomic_job_assignment_verified', 'limits_query_verified', 'job_empty_before_close',
                  'job_closed', 'root_exit_after_job_close', 'process_handle_closed', 'thread_handle_closed')
        if result.exit_code != 0 or result.reason != 'normal' or not all(state[k] for k in needed) or state['cleanup_errors'] or state['peak_sampling_errors']:
            raise RuntimeError('child lifecycle or cleanup refused')
        if request['mode'] == 'inventory' and {p.name for p in out.iterdir()} != {'claim.json', 'dispatch.json', 'deadline.json'}:
            raise ValueError('probe created unexpected artifact')
        test_report = None
        if request['mode'] == 'tests':
            test_report = strict(pins.read(out / 'test-report.json'))
            if (set(test_report) != {'successful', 'tests_run', 'failures', 'errors', 'skipped', 'report', 'launch_authorized', 'scientific_admission'}
                    or test_report.get('successful') is not True
                    or type(test_report.get('tests_run')) is not int or test_report['tests_run'] != 19
                    or any(type(test_report.get(k)) is not int or test_report[k] != 0 for k in ('failures', 'errors', 'skipped'))
                    or type(test_report.get('report')) is not str or len(test_report['report']) > 65536
                    or test_report.get('launch_authorized') is not False or test_report.get('scientific_admission') is not False):
                raise ValueError('test report refused')
        witnesses = [w for w in pins.verify() if w['path'] in roster]
        if len(witnesses) != len(roster):
            raise ValueError('closed roster mismatch')
        outputs.verify()
        no_stop()
        no_cache()
        sample = sensor(ROOT)
        if sample.available_ram_bytes < 4 * 1024**3 or sample.free_disk_bytes < 20 * 1024**3:
            raise RuntimeError('final resource floor')
        payload = {'schema': 'cho51_p3_inventory_payload_v8', 'mode': request['mode'],
            'scope': 'exact declared source and runtime roster; not all installed files or loaded images',
            'trust_assumptions': 'ordinary local Windows kernel, filesystem and observer; excludes privileged compromise, injected observer and preexisting writable mappings',
            'file_count': len(witnesses), 'total_bytes': sum(w['bytes'] for w in witnesses),
            'test_report': test_report,
            'witnesses': witnesses, 'probe_provides_no_inventory_claims': True, **FALSES}
        outputs.write('payload.json', encoded(payload))
        pins.verify()
        outputs.verify()
        no_stop()
        no_cache()
        if time.monotonic() - began >= 75 or datetime.now(UTC) >= end:
            raise RuntimeError('publication work bound expired')
        accepted = True
    except Exception as exc:
        error = type(exc).__name__ + ': ' + str(exc)[:512]
        # Stop/work failures forbid further observation, but permit bounded owned
        # failure publication and handle closure within the hard90s watchdog.
        pins.checkpoint = lambda: None
    receipt = {'schema': 'cho51_p3_inventory_receipt_v8', 'accepted_by_runner': accepted, 'error': error,
        'native_state': state, 'startup_samples': samples, 'result': None if result is None else dataclasses.asdict(result),
        'completed_utc': datetime.now(UTC).isoformat(), 'elapsed_seconds': time.monotonic()-began,
        'actual_external_caller_return_pending': True, 'independent_result_review_pending': True, **FALSES}
    try:
        if outputs is not None:
            outputs.write('receipt.json', encoded(receipt))
            outputs.verify()
            pins.verify()
        print(json.dumps({'attempt': None if out is None else str(out), 'accepted_by_runner': accepted, 'error': error}))
    finally:
        try:
            if outputs is not None:
                outputs.close()
        finally:
            pins.close()
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())

