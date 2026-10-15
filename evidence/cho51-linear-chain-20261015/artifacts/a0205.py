"""One pinned synthetic linear chain request with an exact dynamic numerical budget."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import msvcrt
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
SITE = ROOT / '.venv/Lib/site-packages'
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_chain_v1'
PREDECESSOR = ROOT / 'runs/coordination/cho51_linear_continuation_20261015_v1'
PREDECESSOR_SHA = '1e16577546807821112e58f671f0941e0ba3ab0c5980c82efa67d92b14e4a42b'
SNAPSHOT = ROOT / '.cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/0563b6c626e7b40d9a36653b763715db94d945d7'
BASELINE = SNAPSHOT / 'model.safetensors'
BASELINE_SHA = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
CONFIG = SNAPSHOT / 'config.json'
CONFIG_SHA = '813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
PAUSE = Path('D:/Aenv/pro2/WORK/resume-20261015-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json')
PAUSES = tuple(Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001' /
    'coordination/PRO2_REQUEST_PRO3_PAUSE.json'
    for day in ('20261007', '20261012', '20261013', '20261015'))


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def read_json(path, maximum=8 * 1024**2):
    path = Path(path)
    before = path.stat()
    if (path.resolve(strict=True) != path or path.is_symlink()
            or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
            or not 0 < before.st_size <= maximum):
        raise ValueError('bounded direct single-link JSON proof required')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(maximum + 1)
        finished = os.fstat(stream.fileno())
    after = path.stat()
    key = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if (key(before) != key(after) or key(opened) != key(finished)
            or key(before)[:4] != key(opened)[:4] or len(raw) != before.st_size):
        raise ValueError('physical JSON proof changed during bounded read')
    def unique(pairs):
        value = {}
        for name, item in pairs:
            if name in value:
                raise ValueError('duplicate JSON key')
            value[name] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda item: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def write_json(path, value):
    raw = (canonical(value) + '\n').encode('utf-8')
    with Path(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    path = Path(path)
    before = path.stat()
    if (path.resolve(strict=True) != path or path.is_symlink()
            or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1):
        raise ValueError('ordinary direct single-link proof required')
    value = digest(path)
    after = path.stat()
    key = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if key(before) != key(after):
        raise ValueError('proof identity changed during hashing')
    return (*key(after), value)


def path_of(value):
    value = os.fsdecode(value)
    if value.startswith('\\\\?\\'):
        value = value[4:]
    return Path(value).resolve()


def stack_has(name, path):
    frame = sys._getframe(1)
    while frame:
        if frame.f_code.co_name == name and path_of(frame.f_code.co_filename) == path:
            return True
        frame = frame.f_back
    return False


def pause_check():
    if any(path.exists() for path in PAUSES):
        raise RuntimeError('genuine peer pause requested')


class Runtime:
    def __init__(self, mode, pins_path, pins_sha256, output, request=None):
        if mode != 'probe' or type(request) is not tuple or len(request) != 2:
            raise ValueError('one exact immutable chain request required')
        self.mode, self.pins_path, self.pins_sha256 = mode, pins_path, pins_sha256
        if (pins_path != RUN / 'pins.json' or pins_path.resolve(strict=True) != pins_path
                or re.fullmatch('[a-f0-9]{64}', pins_sha256) is None
                or digest(pins_path) != pins_sha256):
            raise ValueError('exact independently pinned fresh bundle required')
        self.pins = read_json(pins_path)
        p = self.pins
        expected = {'schema': 'cho51_linear_chain_pins_v1',
            'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
            'predecessor_files': 1224, 'predecessor_pins_sha256': PREDECESSOR_SHA,
            'seconds': 600, 'process_mib': 4096, 'job_mib': 5120,
            'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
            'threads': 1, 'gpu_hidden': True,
            'required_selection_updates': 5253, 'pretrained_baseline_loaded': True,
            'cohort_lineage_verified': False, 'full_selector_verified': False,
            'full_worker_verified': False, 'scientific_admission': False,
            'original_case_attempts_remaining': 0, 'baseline_bytes': 23299672,
            'architecture_bytes': 4776, 'expected_tests': 36, 'expected_subtests': 0}
        if (any(type(p.get(key)) is not type(value) or p[key] != value for key, value in expected.items())
                or len(p.get('files', {})) <= 1224 or len(p.get('runtime', {})) != 5
                or p.get('baseline') != {str(BASELINE): BASELINE_SHA}
                or type(p.get('expected_tests')) is not int or p['expected_tests'] != 36):
            raise ValueError('exact immutable bounded generic chain bundle required')
        self.request_path, self.request_sha256 = request
        if (not isinstance(self.request_path, Path) or self.request_path.resolve(strict=True) != self.request_path
                or re.fullmatch('[a-f0-9]{64}', self.request_sha256) is None
                or digest(self.request_path) != self.request_sha256):
            raise ValueError('exact external physical request pin required')
        self.request = read_json(self.request_path)
        index = self.request.get('index')
        if (type(index) is not int or not 1 <= index <= 7
                or self.request_path != RUN / f'requests/fragment_{index:03d}.json'
                or self.request.get('pins_sha256') != pins_sha256
                or self.request.get('root_origin_sha256') != p['root_origin_file_sha256']
                or self.request.get('output_relative') != f'fragments/fragment_{index:03d}'
                or self.request.get('chain_relative') != f'chains/chain_{index - 1:03d}.json'):
            raise ValueError('exact independently pinned sequential fragment request required')
        self.root_origin = read_json(RUN / 'root-origin.json')
        self.chain_path = RUN / self.request['chain_relative']
        self.chain = read_json(self.chain_path)
        self.chain_identity = identity(self.chain_path)
        self.request_identity = identity(self.request_path)
        encoded_sha = lambda value: hashlib.sha256((canonical(value) + '\n').encode()).hexdigest()
        if (self.request_identity[-1] != self.request_sha256
                or encoded_sha(self.request) != self.request_sha256
                or encoded_sha(self.chain) != self.chain_identity[-1]
                or encoded_sha(self.root_origin) != p['root_origin_file_sha256']):
            raise ValueError('exact canonical physical request, parent chain and root origin required')
        self.verify_pins()
        plan_path = CANDIDATE / 'plan.py'
        sys.path.insert(0, str(ROOT))
        spec = importlib.util.spec_from_file_location('_cho51_linear_chain_runtime_plan_v1', plan_path)
        if spec is None or spec.loader is None:
            raise ValueError('exact pure metadata request planner required')
        plan = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = plan
        spec.loader.exec_module(plan)
        plan.validate_request(self.request, self.chain, pins_sha256=pins_sha256,
            root_origin_sha256=p['root_origin_file_sha256'])
        self.budget = plan.budget(self.request)
        self.output = output
        if output != RUN / self.request['output_relative'] or output.absolute() != output or output.resolve() != output:
            raise ValueError('one direct fresh request-owned fragment output required')
        output.mkdir(exist_ok=False)
        self.fixture = ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture'
        if (p.get('fixture_root') != str(self.fixture) or self.fixture.resolve(strict=True) != self.fixture
                or not self.fixture.is_dir()):
            raise ValueError('exact immutable accepted origin fixture required')
        directories = {'TEMP': 'temp', 'TMP': 'temp', 'TMPDIR': 'temp',
            'MPLCONFIGDIR': 'mpl', 'HF_HOME': 'hf', '_MNE_FAKE_HOME_DIR': 'mne-home',
            'HF_HUB_CACHE': 'hf/hub', 'HUGGINGFACE_HUB_CACHE': 'hf/hub',
            'TRANSFORMERS_CACHE': 'hf/transformers', 'TORCH_HOME': 'torch',
            'NUMBA_CACHE_DIR': 'numba', 'JOBLIB_TEMP_FOLDER': 'joblib', 'XDG_CACHE_HOME': 'cache'}
        for folder in sorted(set(directories.values()), key=lambda value: (value.count('/'), value)):
            (output / folder).mkdir()
        for name, folder in directories.items():
            os.environ[name] = str(output / folder)
        for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                     'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
            os.environ[name] = '1'
        os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
        sys.dont_write_bytecode = True
        sys.path[:0] = [str(ROOT), str(SITE)]
        from tools.migration.common import source_check
        if source_check(ROOT) != CANONICAL:
            raise ValueError('canonical source changed')
        self.git_command = shutil.which('git')
        if self.git_command is None or str(Path(self.git_command).resolve()) not in p['runtime']:
            raise ValueError('pinned installed Git runtime required')
        self.git_path = Path(self.git_command).resolve()
        self.connection = SITE / 'urllib3/util/connection.py'
        self.mne = SITE / 'mne/data/fsaverage/fsaverage-fiducials.fif'
        if (str(self.mne) != p['mne_resource_path'] or self.mne.stat().st_size != 260
                or digest(self.mne) != p['mne_resource_sha256']
                or p['mne_resource_sha256'] != '0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'):
            raise ValueError('exact pinned 260-byte MNE metadata required')
        self.pinned_files = {ROOT / relative: sha for relative, sha in p['files'].items()}
        self.denied = []
        self.hostname_queries = self.git_queries = self.existing_mkdir_refusals = 0
        self.numerical_calls = {}
        self.source_steps = self.support_steps = 0
        self.active = False
        self.protected = frozenset()
        self.protected_declared = ()
        self.protection_transitions = []
        self.target_reads = []
        self.read_phases = {}
        self.baseline_read_phases = {}
        self.context_hash_reads = {}
        self.checkpoint_pin = None
        self.checkpoint_identity = None
        self.serialization_active = False
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong]
        self.api.GetFinalPathNameByHandleW.restype = ctypes.c_ulong
        sys.addaudithook(self.audit)
        pause_check()
        self.started = time.monotonic()

    def verify_pins(self):
        pause_check()
        p = self.pins
        if digest(self.pins_path) != self.pins_sha256 or digest(PREDECESSOR / 'pins.json') != PREDECESSOR_SHA:
            raise ValueError('fresh or frozen predecessor pins changed')
        predecessor = read_json(PREDECESSOR / 'pins.json')
        if (len(predecessor.get('files', {})) != 1224 or len(predecessor.get('runtime', {})) != 5
                or any(p['files'].get(path) != sha for path, sha in predecessor['files'].items())
                or p['runtime'] != predecessor['runtime']):
            raise ValueError('exact 1224/5 frozen pin extension required')
        for relative, expected in p['files'].items():
            if digest(ROOT / relative) != expected:
                raise ValueError('source/library/context pin changed: ' + relative)
        for name, expected in p['runtime'].items():
            if digest(name) != expected:
                raise ValueError('runtime pin changed: ' + name)
        if (BASELINE.resolve(strict=True) != BASELINE or BASELINE.is_symlink()
                or BASELINE.stat().st_size != 23299672 or digest(BASELINE) != BASELINE_SHA
                or CONFIG.resolve(strict=True) != CONFIG or CONFIG.is_symlink()
                or CONFIG.stat().st_size != 4776 or digest(CONFIG) != CONFIG_SHA):
            raise ValueError('exact independently pinned baseline/architecture changed')
        review_path = Path(p['source_review_path'])
        review = read_json(review_path)
        if (review_path != RUN / 'source-review.json' or digest(review_path) != p['source_review_sha256']
                or review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
                or review.get('files') != p['reviewed_files']
                or review.get('lineage_assets') != p['lineage_assets']
                or review.get('method_config_file_sha256') != p['method_config_file_sha256']
                or review.get('root_origin_file_sha256') != p['root_origin_file_sha256']
                or digest(RUN / 'root-origin.json') != p['root_origin_file_sha256']
                or digest(RUN / 'method-config.json') != p['method_config_file_sha256']):
            raise ValueError('independent exact source/lineage/method review changed')
        pause_check()

    def refuse(self, event, detail=None):
        self.denied.append({'event': event, 'detail': repr(detail)[:500]})
        raise PermissionError('synthetic linear chain denied: ' + event)

    def fd_path(self, descriptor):
        if type(descriptor) is not int:
            return None
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            count = self.api.GetFinalPathNameByHandleW(msvcrt.get_osfhandle(descriptor), buffer, len(buffer), 0)
            return path_of(buffer.value) if 0 < count < len(buffer) else None
        except OSError:
            return None

    def writable(self, path):
        return path.is_relative_to(self.output)

    def audit(self, event, values):
        if event == 'socket.gethostname':
            self.hostname_queries += 1
        elif event.startswith('socket.'):
            if (event == 'socket.__new__' and values[1:] == (socket.AF_INET6, socket.SOCK_STREAM, 0)
                    and stack_has('_has_ipv6', self.connection)):
                self.denied.append({'event': event, 'classification': 'blocked_optional_ipv6_import_probe',
                    'source_file': str(self.connection),
                    'source_sha256': self.pins['files'][self.connection.relative_to(ROOT).as_posix()]})
                raise PermissionError('optional IPv6 import socket creation blocked')
            self.refuse(event, values)
        elif event == 'subprocess.Popen':
            executable, arguments, cwd, environment = values
            exact = lambda command: arguments == command or arguments == subprocess.list2cmdline(command)
            exe = lambda path: ((executable is None and os.name == 'nt') or
                isinstance(executable, (str, bytes, os.PathLike)) and path_of(executable) == path)
            git_forms = [[self.git_command, '--no-optional-locks', *tail] for tail in (
                ['rev-parse', '--verify', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'])]
            fixture_git = cwd is not None and path_of(cwd) == self.fixture
            lineage_git = (cwd is not None and path_of(cwd) == ROOT and self.active
                and stack_has('run_probe', CANDIDATE / 'executor.py')
                and stack_has('prepare_cho_source_restore', ROOT / 'evaluation/phase2_cho_source_restore.py'))
            if (any(exact(command) for command in git_forms) and exe(self.git_path)
                    and (fixture_git or lineage_git) and environment is None
                    and stack_has('capture_source', ROOT / 'core/provenance.py')):
                self.git_queries += 1
            else:
                self.refuse(event, values)
        elif (event in {'os.system', 'os.startfile', 'os.posix_spawn', 'os.fork', 'os.forkpty', 'pty.spawn'}
                or event.startswith(('os.exec', 'os.spawn'))):
            self.refuse(event, values)
        elif event == 'open':
            mode = values[1] if isinstance(values[1], str) else ''
            flags = values[2] if isinstance(values[2], int) else 0
            writing = any(char in mode for char in 'wax+') or bool(flags &
                (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            path = path_of(values[0]) if isinstance(values[0], (str, bytes, os.PathLike)) else self.fd_path(values[0])
            if path is None:
                if writing:
                    self.refuse('unbound_descriptor_write', values)
                return
            if writing:
                if not self.writable(path):
                    self.refuse('outside_owned_write', path)
            elif path in self.protected:
                row = {'event': 'protected_outer_target_read', 'path': str(path)}
                self.target_reads.append(row)
                self.denied.append(row)
                raise PermissionError('outer target content excluded from computation')
            elif path.is_relative_to(self.fixture):
                phase = 'during_computation' if self.protected else 'after_protection' if self.protected_declared else 'before_protection'
                counts = self.read_phases.setdefault(str(path), {
                    'before_protection': 0, 'during_computation': 0, 'after_protection': 0})
                counts[phase] += 1
            elif path == self.output / 'selected-source.safetensors':
                checkpoint_stat = path.stat()
                checkpoint_key = (checkpoint_stat.st_dev, checkpoint_stat.st_ino, checkpoint_stat.st_size,
                    checkpoint_stat.st_mtime_ns, checkpoint_stat.st_ctime_ns)
                owned_checkpoint = (self.request['mode'] == 'final'
                    and self.source_steps == 51 and self.support_steps == 0
                    and self.numerical_calls.get('safetensors_save') == 1
                    and 0 < checkpoint_stat.st_size <= 64 * 1024**2
                    and (self.checkpoint_identity is None or checkpoint_key == self.checkpoint_identity[:5]))
                active_save = (self.active and stack_has('run_probe', CANDIDATE / 'executor.py')
                    and stack_has('_save_selected', CANDIDATE / 'executor.py'))
                final_identity = (not self.active and self.checkpoint_pin is not None
                    and stack_has('finish', RUN / 'runtime.py') and stack_has('identity', RUN / 'runtime.py'))
                if not owned_checkpoint or not (active_save or final_identity):
                    self.refuse('unbound_owned_checkpoint_read', path)
            elif path == BASELINE:
                byte_hash = stack_has('verify_pins', RUN / 'runtime.py') and stack_has('digest', RUN / 'runtime.py')
                origin_hash = any(stack_has(entry, CANDIDATE / 'origin.py') for entry in ('build_root', 'verify_chain', 'authenticate_fragment', 'close_leaf'))
                lineage_read = self.active and stack_has('run_probe', CANDIDATE / 'executor.py')
                if not (byte_hash or origin_hash or lineage_read):
                    self.refuse('baseline_read_outside_exact_lineage_or_pin_hash', path)
                phase = 'pin_byte_hash' if byte_hash else 'origin_metadata_byte_hash' if origin_hash else 'initial_lineage_baseline_read'
                self.baseline_read_phases[phase] = self.baseline_read_phases.get(phase, 0) + 1
            else:
                parts = tuple(part.lower() for part in path.parts)
                data_path = any(parts[index:index + 2] in {('data', 'raw'), ('data', 'processed'), ('data', 'interim')}
                    for index in range(len(parts) - 1))
                if path == self.mne:
                    return
                metadata_pin_hash = (path in self.pinned_files
                    and path.suffix.lower() not in {'.npz', '.npy', '.mat', '.safetensors', '.pth', '.pt', '.ckpt'}
                    and ((stack_has('verify_pins', RUN / 'runtime.py') and stack_has('digest', RUN / 'runtime.py'))
                        or any(stack_has(entry, CANDIDATE / 'origin.py') for entry in ('build_root', 'verify_chain', 'authenticate_fragment', 'close_leaf'))))
                if metadata_pin_hash:
                    self.context_hash_reads[str(path)] = self.context_hash_reads.get(str(path), 0) + 1
                    return
                if (data_path or 'weights' in parts or 'checkpoints' in parts or
                        path.suffix.lower() in {'.npz', '.npy', '.mat', '.edf', '.gdf', '.fif', '.set', '.pt', '.pth', '.ckpt', '.safetensors'}):
                    if not (path.suffix.lower() == '.pth' and path.is_relative_to(SITE)):
                        self.refuse('actual_study_array_or_unpinned_checkpoint_read', path)
        elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace',
                       'os.link', 'os.symlink', 'os.chmod', 'os.utime', 'os.truncate'}:
            count = 2 if event in {'os.rename', 'os.replace', 'os.link', 'os.symlink'} else 1
            for value in values[:count]:
                if not isinstance(value, (str, bytes, os.PathLike)):
                    self.refuse('unbound_mutation', values)
                path = path_of(value)
                if event == 'os.mkdir' and not self.writable(path) and path.is_dir():
                    self.existing_mkdir_refusals += 1
                    raise FileExistsError(17, 'existing outside directory creation refused', os.fsdecode(value))
                if not self.writable(path):
                    self.refuse('outside_owned_mutation', path)
        elif event == 'os.chdir' and not self.writable(path_of(values[0])):
            self.refuse(event, values)

    def set_protected_inputs(self, paths, enabled=True):
        expected = tuple(self.fixture / relative for relative in (
            'data/processed/cho2017/profile_a/subject_02.npz',
            'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
            'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
            'data/raw/moabb/cho2017/subject_02.mat'))
        if (not self.active or not stack_has('run_probe', CANDIDATE / 'executor.py')
                or type(paths) is not tuple or paths != expected or type(enabled) is not bool
                or any(path.resolve(strict=True) != path or not path.is_file() or path.stat().st_nlink != 1 for path in paths)):
            self.refuse('unbound_protected_input_control', paths)
        if enabled:
            if self.protected or self.protected_declared:
                raise ValueError('target protection enabled exactly once')
            self.protected_declared, self.protected = paths, frozenset(paths)
        else:
            if not self.protected or paths != self.protected_declared:
                raise ValueError('only original protected paths may be released')
            self.protected = frozenset()
        self.protection_transitions.append({'enabled': enabled, 'paths': [str(path) for path in paths]})

    def numerical_allowed(self, name):
        if not self.active or not stack_has('run_probe', CANDIDATE / 'executor.py'):
            self.refuse('numerical_call_outside_exact_probe', name)
        allowed_safe = {'safetensors_load'}
        if self.request['mode'] == 'final':
            allowed_safe.add('safetensors_save')
        if name == 'autograd_grad' or name.startswith('safetensors_') and name not in allowed_safe:
            self.refuse('forbidden_numerical_or_serialization_api', name)
        pause_check()
        self.numerical_calls[name] = self.numerical_calls.get(name, 0) + 1
        limits = {'optimizer_init': self.budget['optimizer_init'],
            'sgd_step': self.budget['gradient_updates'], 'tensor_backward': self.budget['gradient_updates'],
            'autograd_backward': self.budget['gradient_updates'],
            'safetensors_load': self.budget['safetensors_load'],
            'safetensors_save': self.budget['safetensors_save'],
            'module_load_state_dict': self.budget['module_load_state_dict']}
        if name in limits and self.numerical_calls[name] > limits[name]:
            self.refuse('excess_exact_probe_budget', name)
        if name in {'optimizer_init', 'sgd_step', 'tensor_backward', 'autograd_backward'}:
            source = stack_has('_fit', ROOT / 'adaptation/labram_source.py')
            support = stack_has('_predict', ROOT / 'adaptation/labram_manifest.py')
            if not source and not support:
                self.refuse('optimization_outside_public_source_or_support', name)
            if name == 'sgd_step':
                if source:
                    self.source_steps += 1
                else:
                    self.support_steps += 1
                if self.source_steps > self.budget['source_updates'] or self.support_steps > self.budget['support_updates']:
                    self.refuse('excess_source_or_support_budget', None)

    def checkpoint_control(self, pin):
        if (self.request['mode'] != 'final' or not self.active or self.checkpoint_pin is not None
                or not stack_has('run_probe', CANDIDATE / 'executor.py')
                or not stack_has('_save_selected', CANDIDATE / 'executor.py')
                or self.source_steps != 51 or self.support_steps != 0
                or self.numerical_calls.get('safetensors_save') != 1
                or type(pin) is not dict or set(pin) != {'path', 'sha256', 'size_bytes'}
                or pin['path'] != str(self.output / 'selected-source.safetensors')
                or type(pin['size_bytes']) is not int or not 0 < pin['size_bytes'] <= 64 * 1024**2
                or type(pin['sha256']) is not str or re.fullmatch('[a-f0-9]{64}', pin['sha256']) is None):
            self.refuse('unbound_final_checkpoint_control', pin)
        path = self.output / 'selected-source.safetensors'
        observed = identity(path)
        if observed[2] != pin['size_bytes'] or observed[-1] != pin['sha256']:
            self.refuse('final_checkpoint_physical_bytes_differ', pin)
        self.checkpoint_pin, self.checkpoint_identity = dict(pin), observed

    def install_torch_guards(self):
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        def no_pickle(*args, **kwargs):
            self.refuse('pickle_or_pretrained_load_or_tensor_save', None)
        torch.load = torch.serialization.load = torch.jit.load = torch.hub.load = no_pickle
        torch.save = torch.serialization.save = no_pickle
        def guarded(name, original):
            def call(*args, **kwargs):
                self.numerical_allowed(name)
                return original(*args, **kwargs)
            return call
        optimizer_init = torch.optim.Optimizer.__init__
        def sgd_only(optimizer, parameters, defaults):
            self.numerical_allowed('optimizer_init')
            if type(optimizer) is not torch.optim.SGD or defaults.get('momentum', 0) != 0:
                self.refuse('optimizer_outside_stateless_sgd', type(optimizer).__name__)
            return optimizer_init(optimizer, parameters, defaults)
        torch.nn.Module.__init__ = guarded('model_module_init', torch.nn.Module.__init__)
        torch.nn.Module.load_state_dict = guarded('module_load_state_dict', torch.nn.Module.load_state_dict)
        torch.optim.Optimizer.__init__ = sgd_only
        torch.optim.SGD.step = guarded('sgd_step', torch.optim.SGD.step)
        torch.Tensor.backward = guarded('tensor_backward', torch.Tensor.backward)
        torch.autograd.backward = guarded('autograd_backward', torch.autograd.backward)
        torch.autograd.grad = guarded('autograd_grad', torch.autograd.grad)
        import safetensors
        import safetensors.torch
        safetensors.safe_open = guarded('safetensors_safe_open', safetensors.safe_open)
        safetensors.torch.safe_open = guarded('safetensors_torch_safe_open', safetensors.torch.safe_open)
        for name in ('serialize', 'serialize_file', 'deserialize'):
            setattr(safetensors, name, guarded('safetensors_' + name, getattr(safetensors, name)))
        safetensors.torch.serialize_file = guarded('safetensors_serialize_file', safetensors.torch.serialize_file)
        for name in ('save_file', 'save_model', 'load_file', 'load_model'):
            setattr(safetensors.torch, name, guarded('safetensors_' + name, getattr(safetensors.torch, name)))
        original_load = safetensors.torch.load
        original_deserialize = safetensors.torch.deserialize
        original_save = safetensors.torch.save
        original_serialize = safetensors.torch.serialize
        def valid_decode(raw):
            if type(raw) is not bytes:
                return False
            count = self.numerical_calls.get('safetensors_load', 0)
            if count in (1, 2):
                return len(raw) == 23299672 and hashlib.sha256(raw).hexdigest() == BASELINE_SHA
            return (count == 3 and self.request['mode'] == 'final' and self.checkpoint_pin is not None
                and stack_has('_save_selected', CANDIDATE / 'executor.py')
                and len(raw) == self.checkpoint_pin['size_bytes']
                and hashlib.sha256(raw).hexdigest() == self.checkpoint_pin['sha256'])
        def deserialize_pinned(raw):
            if (not self.active or not stack_has('run_probe', CANDIDATE / 'executor.py')
                    or not stack_has('load_pinned', RUN / 'runtime.py')
                    or not stack_has('load', SITE / 'safetensors/torch.py')
                    or not valid_decode(raw)):
                self.refuse('unbound_low_level_safetensors_decode', None)
            return original_deserialize(raw)
        safetensors.torch.deserialize = deserialize_pinned
        def load_pinned(raw):
            self.numerical_allowed('safetensors_load')
            if not valid_decode(raw):
                self.refuse('unbound_safetensors_decode', None)
            return original_load(raw)
        safetensors.torch.load = load_pinned
        def serialize_selected(*args, **kwargs):
            if (self.request['mode'] != 'final' or not self.active or not self.serialization_active
                    or not stack_has('run_probe', CANDIDATE / 'executor.py')
                    or not stack_has('_save_selected', CANDIDATE / 'executor.py')
                    or not stack_has('save_selected', RUN / 'runtime.py')
                    or not stack_has('save', SITE / 'safetensors/torch.py')
                    or self.source_steps != 51 or self.support_steps != 0
                    or self.numerical_calls.get('safetensors_save') != 1):
                self.refuse('unbound_final_safetensors_serialize', None)
            return original_serialize(*args, **kwargs)
        safetensors.torch.serialize = serialize_selected
        def save_selected(state):
            if (self.request['mode'] != 'final' or not stack_has('_save_selected', CANDIDATE / 'executor.py')
                    or self.source_steps != 51 or self.support_steps != 0 or self.serialization_active
                    or type(state) is not dict or len(state) != 223
                    or any(type(name) is not str or not isinstance(tensor, torch.Tensor)
                        or tensor.device.type != 'cpu' or tensor.dtype != torch.float32
                        for name, tensor in state.items())):
                self.refuse('unbound_final_safetensors_save', None)
            self.numerical_allowed('safetensors_save')
            self.serialization_active = True
            try:
                raw = original_save(state)
            finally:
                self.serialization_active = False
            if type(raw) is not bytes or not 0 < len(raw) <= 64 * 1024**2:
                self.refuse('final_safetensors_serialization_size', None)
            return raw
        safetensors.torch.save = save_selected
        import data.runtime as runtime
        original = runtime.configure_scientific_runtime
        runtime.configure_scientific_runtime = lambda project_root=self.output: original(self.output)
        from braindecode.models import EEGNet, Labram
        EEGNet.from_pretrained = classmethod(no_pickle)
        Labram.from_pretrained = classmethod(no_pickle)
        from huggingface_hub import PyTorchModelHubMixin
        PyTorchModelHubMixin.from_pretrained = classmethod(no_pickle)
        from evaluation.phase2_runner import CaseRecorder
        CaseRecorder.__init__ = lambda *args, **kwargs: self.refuse('recorder_constructor_forbidden', None)
        return torch

    def clean(self):
        expected = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
            'source_file': str(self.connection),
            'source_sha256': self.pins['files'][self.connection.relative_to(ROOT).as_posix()]}
        if self.denied != [expected] or self.target_reads or self.protected or self.active or self.serialization_active:
            raise RuntimeError('unexpected audit denial or unfinished target/numerical scope')

    def finish(self, result):
        import torch
        from tools.migration.common import source_check
        from evaluation.phase2_runner import environment_digest
        pause_check()
        self.clean()
        self.verify_pins()
        if (identity(self.request_path) != self.request_identity
                or identity(self.chain_path) != self.chain_identity
                or self.checkpoint_identity is not None
                    and identity(self.output / 'selected-source.safetensors') != self.checkpoint_identity):
            raise ValueError('immutable request, parent chain or owned checkpoint changed')
        if (source_check(ROOT) != CANONICAL or torch.get_num_threads() != 1
                or torch.get_num_interop_threads() != 1 or os.environ.get('CUDA_VISIBLE_DEVICES') != ''):
            raise ValueError('canonical code or CPU controls changed')
        loaded = {}
        for module in tuple(sys.modules.values()):
            name = getattr(module, '__file__', None)
            if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(self.output):
                loaded[str(Path(name).resolve())] = digest(name)
        q = {'schema': 'cho51_linear_chain_qualification_v1',
            'passed': result.get('passed') is True, 'pins_sha256': self.pins_sha256, 'result': result,
            'observed_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.monotonic() - self.started,
            'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
            'source_pins_rechecked': len(self.pins['files']), 'runtime_pins_rechecked': len(self.pins['runtime']),
            'baseline_pins_rechecked': 1, 'baseline_file_sha256': BASELINE_SHA,
            'source_review_sha256': self.pins['source_review_sha256'],
            'request_sha256': self.request_sha256, 'request_path': str(self.request_path),
            'request_index': self.request['index'], 'mode': self.request['mode'],
            'root_origin_sha256': self.pins['root_origin_file_sha256'],
            'chain_sha256': self.request['chain_sha256'], 'chain_file_sha256': self.chain_identity[-1],
            'parent_head_sha256': self.request['parent_head_sha256'],
            'budget': self.budget,
            'observed_loaded_module_hashes': loaded, 'loaded_module_files': len(loaded),
            'environment_sha256': environment_digest(), 'torch_threads': 1, 'torch_interop_threads': 1,
            'gpu_hidden': True, 'read_only_git_queries': self.git_queries,
            'hostname_metadata_queries': self.hostname_queries,
            'existing_directory_mkdir_refusals': self.existing_mkdir_refusals,
            'denied_operations': self.denied, 'unexpected_denials': 0, 'expected_blocked_ipv6_probes': 1,
            'observed_numerical_calls': self.numerical_calls,
            'source_updates': self.source_steps, 'support_updates': self.support_steps,
            'actual_gradient_updates': self.source_steps + self.support_steps,
            'historical_gradient_updates': self.request['prior_folds'] * 51,
            'adopted_historical_folds': self.request['prior_folds'],
            'combined_folds': self.request['prior_folds'] + len(self.request['pairs']),
            'pending_folds': 102 - self.request['prior_folds'] - len(self.request['pairs']),
            'combined_described_gradient_updates': self.request['prior_folds'] * 51 + self.source_steps + self.support_steps,
            'tests_executed': result['tests_executed'], 'tests_reused': result['tests_reused'],
            'tests_passed': result['tests_passed'],
            'tests_reused_from_leaf_sha256': result['tests_reused_from_leaf_sha256'],
            'checkpoint': self.checkpoint_pin,
            'baseline_read_phases': self.baseline_read_phases, 'context_metadata_hash_reads': self.context_hash_reads,
            'protected_target_transitions': self.protection_transitions,
            'protected_target_read_attempts': self.target_reads, 'fixture_input_read_phases': self.read_phases,
            'pretrained_baseline_loaded': result.get('pretrained_baseline_loaded') is True,
            'actual_study_data_used': False,
            'cohort_lineage_verified': False, 'full_selector_verified': result.get('full_selector_verified') is True,
            'full_worker_verified': False, 'scientific_admission': False,
            'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0}
        write_json(self.output / 'qualification.json', q)
        for path, expected in loaded.items():
            if digest(path) != expected:
                raise ValueError('loaded module changed during qualification')
        self.clean()
        return q
