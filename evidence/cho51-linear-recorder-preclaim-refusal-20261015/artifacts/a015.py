"""Pinned metadata recorder; model construction and guarded numerical paths refuse."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
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
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_recorder_v1'
PREDECESSOR = ROOT / 'runs/coordination/cho51_linear_publication_20261015_v1'
PREDECESSOR_SHA = '30130ec6a122323e2504d70645f86d07cc430f587c2bc109d8aae5f125bd99e9'
FROZEN_LIFECYCLE = ROOT / 'docs/phase2/cho51_worker_lifecycle_v1/lifecycle.py'
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


def stack_module(path):
    frame = sys._getframe(1)
    while frame:
        if path_of(frame.f_code.co_filename) == path:
            return True
        frame = frame.f_back
    return False


def pause_check():
    if any(path.exists() for path in PAUSES):
        raise RuntimeError('genuine peer pause requested')


class Runtime:
    def __init__(self, mode, pins_path, pins_sha256, output, request=None):
        if mode != 'parent' or request is not None:
            raise ValueError('one exact audited runtime mode required')
        self.mode, self.pins_path, self.pins_sha256 = mode, pins_path, pins_sha256
        if (pins_path != RUN / 'pins.json' or pins_path.resolve(strict=True) != pins_path
                or re.fullmatch('[a-f0-9]{64}', pins_sha256) is None
                or digest(pins_path) != pins_sha256):
            raise ValueError('exact independently pinned fresh bundle required')
        self.pins = read_json(pins_path)
        p = self.pins
        expected = {'schema': 'cho51_linear_recorder_pins_v1',
            'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
            'predecessor_files': 1937, 'predecessor_pins_sha256': PREDECESSOR_SHA,
            'seconds': 600, 'process_mib': 4096, 'job_mib': 5120,
            'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
            'threads': 1, 'gpu_hidden': True, 'source_training_replayed': False,
            'current_gradient_updates': 0, 'historical_gradient_updates': 5253,
            'scientific_admission': False, 'original_case_attempts_remaining': 0}
        if (any(type(p.get(key)) is not type(value) or p[key] != value for key, value in expected.items())
                or len(p.get('files', {})) <= 1937 or len(p.get('runtime', {})) != 5
                or type(p.get('expected_tests')) is not int or not 20 <= p['expected_tests'] <= 80):
            raise ValueError('exact bounded metadata-only staged recorder scope required')
        self.output = output
        if (output != RUN / 'validation_001' or output.absolute() != output
                or output.resolve() != output):
            raise ValueError('one direct unused staged recorder output required')
        output.mkdir(exist_ok=False)
        self.fixture = output / 'fixture'
        self.request = None
        self.verify_pins()
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
        contract = read_json(RUN / 'origin-contract.json')
        self.origin_contract = contract
        self.origin_hash_reads = {}
        self.fabricated_test_weight_hash_reads = 0
        self.origin_input_pins = {}
        stage_origin = read_json(PREDECESSOR / 'origin-contract.json')
        self.origin_fixture = Path(stage_origin['fixture_root'])
        for relative, item in stage_origin['original_input_files'].items():
            path = self.origin_fixture / relative
            if path.resolve(strict=True) != path:
                raise ValueError('direct fixed original synthetic input required')
            self.origin_input_pins[path] = item['sha256']
        if len(self.origin_input_pins) != 213:
            raise ValueError('exact213 physical input pins required')
        self.origin_weight_pins = {Path(name): sha for name, sha in contract['files'].items()
            if contract['roles'][name] in {'selected_weights', 'baseline_weights'}}
        if len(self.origin_weight_pins) != 3:
            raise ValueError('original selected, published CAS, baseline byte-hash pins required')
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong]
        self.api.GetFinalPathNameByHandleW.restype = ctypes.c_ulong
        sys.addaudithook(self.audit)
        pause_check()
        self.started = time.monotonic()

    def verify_pins(self):
        pause_check()
        p = self.pins
        if digest(self.pins_path) != self.pins_sha256:
            raise ValueError('fresh staged recorder bundle changed')
        if digest(PREDECESSOR / 'pins.json') != PREDECESSOR_SHA:
            raise ValueError('frozen staged restore predecessor bundle changed')
        predecessor = read_json(PREDECESSOR / 'pins.json')
        if (len(predecessor.get('files', {})) != 1937
                or len(predecessor.get('runtime', {})) != 5
                or any(p['files'].get(path) != sha for path, sha in predecessor['files'].items())
                or p['runtime'] != predecessor['runtime']
                or p['baseline'] != predecessor['baseline']
                or p['selected_weights'] != predecessor['selected_weights']):
            raise ValueError('exact frozen 1937/5 predecessor pin extension required')
        contract_path = RUN / 'origin-contract.json'
        contract_sha = p.get('origin_contract_file_sha256')
        if (type(contract_sha) is not str or re.fullmatch('[a-f0-9]{64}', contract_sha) is None
                or p['files'].get(contract_path.relative_to(ROOT).as_posix()) != contract_sha
                or digest(contract_path) != contract_sha):
            raise ValueError('exact independently pinned origin contract required')
        contract = read_json(contract_path)
        if (set(contract) != {'schema', 'files', 'roles', 'summary'}
                or contract['schema'] != 'cho51_linear_recorder_origin_contract_v1'
                or type(contract['files']) is not dict or type(contract['summary']) is not dict):
            raise ValueError('exact compact origin metadata contract schema required')
        for relative, expected in p['files'].items():
            if digest(ROOT / relative) != expected:
                raise ValueError('source/library pin changed: ' + relative)
        for name, expected in p['runtime'].items():
            if digest(name) != expected:
                raise ValueError('runtime pin changed: ' + name)
        review = read_json(Path(p['source_review_path']))
        if (Path(p['source_review_path']) != RUN / 'source-review.json'
                or digest(Path(p['source_review_path'])) != p['source_review_sha256']
                or review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
                or review.get('files') != p['reviewed_files']):
            raise ValueError('exact independent staged recorder source review changed')
        pause_check()

    def refuse(self, event, detail=None):
        self.denied.append({'event': event, 'detail': repr(detail)[:500]})
        raise PermissionError('staged recorder parent denied: ' + event)

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
            if (any(exact(command) for command in git_forms) and exe(self.git_path)
                    and cwd is not None and path_of(cwd).is_relative_to(self.output)
                    and environment is None and stack_has('capture_source', ROOT / 'core/provenance.py')):
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
            else:
                if path in self.protected:
                    row = {'event': 'protected_outer_target_read', 'path': str(path)}
                    self.target_reads.append(row)
                    self.denied.append(row)
                    raise PermissionError('outer target content excluded from computation')
                if path.is_relative_to(self.fixture):
                    phase = 'during_computation' if self.protected else 'after_protection' if self.protected_declared else 'before_protection'
                    counts = self.read_phases.setdefault(str(path), {
                        'before_protection': 0, 'during_computation': 0, 'after_protection': 0})
                    counts[phase] += 1
                else:
                    parts = tuple(part.lower() for part in path.parts)
                    data_path = any(parts[index:index + 2] in {('data', 'raw'), ('data', 'processed'), ('data', 'interim')}
                        for index in range(len(parts) - 1))
                    if path == self.mne:
                        return
                    if (path.is_relative_to(self.output / 't')
                            and path.name in {'fabricated-weights.safetensors', 'fabricated-baseline.safetensors',
                                              'forbidden.npy', 'forbidden.npz', 'forbidden.safetensors'}
                            and path.stat().st_size <= 256
                            and stack_module(CANDIDATE / 'test_transaction.py')):
                        self.fabricated_test_weight_hash_reads += 1
                        return
                    if (path.is_relative_to(self.output / 't')
                            and path.name in {'fabricated-weights.safetensors', 'fabricated-baseline.safetensors'}
                            and path.stat().st_size <= 256
                            and stack_has('_origin_assets', CANDIDATE / 'transaction.py')
                            and stack_has('_read_origin_file', CANDIDATE / 'transaction.py')):
                        self.fabricated_test_weight_hash_reads += 1
                        return
                    if path in self.origin_input_pins or path in self.origin_weight_pins:
                        origin_hash = (stack_has('verify_origin_stages', RUN / 'origin.py')
                            and (stack_has('inspect', ROOT / 'runs/coordination/cho51_complete_eegnet_20261015_v4/closeout.py')
                                 or stack_has('_read', PREDECESSOR / 'metadata.py')
                                 or stack_has('_asset', RUN / 'origin.py')))
                        # The transaction may hash exact accepted weight roles;
                        # it never receives a synthetic array path in its contract.
                        core_hash = (path in self.origin_weight_pins
                            and stack_has('_origin_assets', CANDIDATE / 'transaction.py')
                            and stack_has('_read_origin_file', CANDIDATE / 'transaction.py'))
                        pin_hash = (path in self.origin_input_pins
                            and path.suffix.lower() not in {'.npz', '.npy', '.mat'}
                            and stack_has('verify_pins', RUN / 'runtime.py')
                            and stack_has('digest', RUN / 'runtime.py'))
                        if origin_hash or core_hash or pin_hash:
                            purpose = ('historical_origin_metadata_byte_hash' if origin_hash else
                                'role_bound_weight_byte_hash' if core_hash else 'frozen_context_pin_byte_hash')
                            row = self.origin_hash_reads.setdefault(str(path), {})
                            row[purpose] = row.get(purpose, 0) + 1
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

    def numerical_allowed(self, name):
        self.refuse('parent_numerical_call', name)

    def install_torch_guards(self):
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        def no_pickle(*args, **kwargs):
            self.refuse('pickle_or_pretrained_load', None)
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
        for name in ('save', 'save_file', 'save_model', 'load', 'load_file', 'load_model'):
            setattr(safetensors.torch, name, guarded('safetensors_' + name, getattr(safetensors.torch, name)))
        # Importing the unchanged recorder needs Torch/NumPy metadata only.
        # Every constructor, restore, gradient and classifier route remains denied.
        for name in ('forward', '__call__'):
            setattr(torch.nn.Module, name, guarded('model_inference_' + name, getattr(torch.nn.Module, name)))
        for name in ('tensor', 'as_tensor', 'from_numpy', 'empty', 'zeros', 'ones', 'rand', 'randn', 'arange'):
            setattr(torch, name, guarded('torch_' + name, getattr(torch, name)))
        for name in ('__matmul__', 'matmul', 'mm', 'bmm', '__mul__', '__add__', '__sub__',
                     '__truediv__', 'sum', 'mean', 'softmax', 'argmax', 'numpy'):
            setattr(torch.Tensor, name, guarded('tensor_' + name, getattr(torch.Tensor, name)))
        for name in ('linear', 'conv1d', 'conv2d', 'softmax', 'relu', 'cross_entropy'):
            setattr(torch.nn.functional, name, guarded('functional_' + name, getattr(torch.nn.functional, name)))
        import numpy as np
        for name in ('load', 'save', 'savez', 'savez_compressed', 'fromfile', 'loadtxt', 'genfromtxt'):
            setattr(np, name, guarded('numpy_' + name, getattr(np, name)))
        return torch

    def clean(self):
        expected = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
            'source_file': str(self.connection),
            'source_sha256': self.pins['files'][self.connection.relative_to(ROOT).as_posix()]}
        if self.denied not in ([], [expected]) or self.target_reads or self.protected or self.numerical_calls:
            raise RuntimeError('unexpected audit denial or unfinished target protection')

    def finish(self, result, request_sha256=None):
        import torch
        from tools.migration.common import source_check
        from evaluation.phase2_runner import environment_digest
        pause_check()
        self.clean()
        self.verify_pins()
        if (source_check(ROOT) != CANONICAL or torch.get_num_threads() != 1
                or torch.get_num_interop_threads() != 1 or os.environ.get('CUDA_VISIBLE_DEVICES') != ''):
            raise ValueError('canonical code or CPU controls changed')
        loaded = {}
        for module in tuple(sys.modules.values()):
            name = getattr(module, '__file__', None)
            if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(RUN / 'validation_001'):
                loaded[str(Path(name).resolve())] = digest(name)
        q = {'schema': 'cho51_linear_recorder_qualification_v1',
            'passed': result.get('passed') is True, 'pins_sha256': self.pins_sha256, 'result': result,
            'observed_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.monotonic() - self.started,
            'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
            'source_pins_rechecked': len(self.pins['files']), 'runtime_pins_rechecked': len(self.pins['runtime']),
            'source_review_sha256': self.pins['source_review_sha256'],
            'observed_loaded_module_hashes': loaded, 'loaded_module_files': len(loaded),
            'environment_sha256': environment_digest(), 'torch_threads': 1, 'torch_interop_threads': 1,
            'gpu_hidden': True, 'read_only_git_queries': self.git_queries,
            'hostname_metadata_queries': self.hostname_queries,
            'existing_directory_mkdir_refusals': self.existing_mkdir_refusals,
            'denied_operations': self.denied, 'unexpected_denials': 0, 'expected_blocked_ipv6_probes': len(self.denied),
            'torch_metadata_dependency_imported': True, 'numpy_metadata_dependency_imported': True,
            'model_constructions': 0, 'current_restore_count': 0, 'target_inference_calls': 0,
            'observed_numerical_calls': self.numerical_calls,
            'current_gradient_updates': 0, 'historical_gradient_updates': 5253,
            'source_training_replayed': False, 'historical_origin_hash_reads': self.origin_hash_reads,
            'fabricated_test_weight_byte_hash_reads': self.fabricated_test_weight_hash_reads,
            'protected_target_transitions': self.protection_transitions,
            'protected_target_read_attempts': self.target_reads, 'fixture_input_read_phases': self.read_phases,
            'actual_study_inputs_or_pretrained_weights_used': False,
            'full_worker_verified': False, 'scientific_admission': False,
            'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0}
        write_json(self.output / 'qualification.json', q)
        for path, expected in loaded.items():
            if digest(path) != expected:
                raise ValueError('loaded module changed during qualification')
        self.clean()
        return q
