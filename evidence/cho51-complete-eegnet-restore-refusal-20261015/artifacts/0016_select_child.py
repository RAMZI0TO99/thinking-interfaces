"""Pinned CPU-only source selection child and shared audited runtime helpers."""
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
CANDIDATE = ROOT / 'docs/phase2/cho51_complete_eegnet_v1'
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
        if mode not in ('parent', 'source', 'detached'):
            raise ValueError('one exact audited runtime mode required')
        self.mode, self.pins_path, self.pins_sha256 = mode, pins_path, pins_sha256
        if (pins_path != RUN / 'pins.json' or pins_path.resolve(strict=True) != pins_path
                or re.fullmatch('[a-f0-9]{64}', pins_sha256) is None
                or digest(pins_path) != pins_sha256):
            raise ValueError('exact independently pinned fresh bundle required')
        self.pins = read_json(pins_path)
        p = self.pins
        expected = {'schema': 'cho51_complete_eegnet_fresh_pins_v1',
            'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
            'predecessor_files': 610,
            'predecessor_pins_sha256': '68f582bf8ccb75b2c07690175bcc4af8e11d067db9504d62afb7560331ddb037',
            'outer_seconds': 600, 'process_mib': 4096, 'job_mib': 6144,
            'source_seconds': 420, 'source_process_mib': 3072, 'source_job_mib': 4096,
            'detached_seconds': 90, 'detached_process_mib': 2048, 'detached_job_mib': 3072,
            'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
            'threads': 1, 'actual_gradient_updates': 5253, 'source_updates': 5151,
            'support_updates': 102, 'fold_count': 102, 'final_source_subjects': 51,
            'scientific_admission': False, 'original_case_attempts_remaining': 0}
        if (any(type(p.get(key)) is not type(value) or p[key] != value for key, value in expected.items())
                or len(p.get('files', {})) <= 610 or len(p.get('runtime', {})) != 5):
            raise ValueError('exact bounded complete synthetic EEGNet scope required')
        self.output = output
        expected_output = (RUN / 'validation_001' if mode == 'parent' else
            Path(request['selection_output' if mode == 'source' else 'detached_output']))
        if output != expected_output or output.absolute() != output or output.resolve() != output:
            raise ValueError('one direct unused owned output required')
        output.mkdir(exist_ok=False)
        self.fixture = RUN / 'validation_001/fixture' if request is None else Path(request['fixture_root'])
        self.request = request
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
        self.allowed_guard_command = None
        self.active = False
        self.protected = frozenset()
        self.protected_declared = ()
        self.protection_transitions = []
        self.target_reads = []
        self.read_phases = {}
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong]
        self.api.GetFinalPathNameByHandleW.restype = ctypes.c_ulong
        sys.addaudithook(self.audit)
        pause_check()
        self.started = time.monotonic()

    def verify_pins(self):
        p = self.pins
        if digest(self.pins_path) != self.pins_sha256:
            raise ValueError('fresh bundle changed')
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
            raise ValueError('exact independent source review changed')

    def refuse(self, event, detail=None):
        self.denied.append({'event': event, 'detail': repr(detail)[:500]})
        raise PermissionError('complete EEGNet child denied: ' + event)

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
        if path.is_relative_to(self.output):
            return True
        if (self.mode == 'source' and self.active
                and path == self.fixture / 'runs/phase2/.selected-source-publication.lock'
                and stack_has('run_selection', CANDIDATE / 'selection.py')
                and stack_has('_publication_lock', ROOT / 'evaluation/phase2_selected_source_store.py')):
            return True
        return self.mode == 'source' and any(path.is_relative_to(self.fixture / relative)
            for relative in ('runs/phase2/selection_evidence', 'runs/phase2/selected_sources'))

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
                    and cwd is not None and path_of(cwd).is_relative_to(self.output if self.mode == 'parent' else self.fixture)
                    and environment is None and stack_has('capture_source', ROOT / 'core/provenance.py')):
                if self.mode != 'parent' and path_of(cwd) != self.fixture:
                    self.refuse('unbound_git_fixture_root', cwd)
                self.git_queries += 1
            elif (self.mode == 'parent' and self.allowed_guard_command is not None
                    and exact(self.allowed_guard_command) and exe(Path(self.allowed_guard_command[0]).resolve())
                    and cwd is not None and path_of(cwd) == ROOT and environment is None
                    and stack_has('_launch', RUN / 'parent.py')):
                pass
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
        entry = 'run_selection' if self.mode == 'source' else 'verify_publication'
        if (self.mode == 'parent' or not self.active or not stack_has(entry, CANDIDATE / 'selection.py')
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
        if self.mode == 'parent':
            self.refuse('parent_numerical_call', name)
        if self.mode == 'source':
            permitted = self.active and stack_has('run_selection', CANDIDATE / 'selection.py')
        else:
            permitted = (self.active and stack_has('verify_publication', CANDIDATE / 'selection.py') and
                any(stack_has(entry, ROOT / 'evaluation/phase2_cho_source_restore.py') for entry in (
                    'verify_cho_selected_source_state', 'restore_cho_selected_source')))
            if name in {'optimizer_init', 'sgd_step', 'tensor_backward', 'autograd_backward', 'autograd_grad'}:
                permitted = False
        if not permitted:
            self.refuse('numerical_call_outside_exact_public_entry', name)
        pause_check()
        self.numerical_calls[name] = self.numerical_calls.get(name, 0) + 1
        if self.mode == 'source' and name == 'sgd_step':
            if stack_has('_fit', ROOT / 'adaptation/source_selection.py'):
                self.source_steps += 1
            elif stack_has('_predict', ROOT / 'adaptation/anchor_manifest.py'):
                self.support_steps += 1
            else:
                self.refuse('sgd_step_outside_public_source_or_support', None)
            count = self.numerical_calls['sgd_step']
            if count > 5253:
                self.refuse('excess_source_gradient_step', count)
            if count % 500 == 0:
                print(json.dumps({'observed_actual_sgd_updates': count}), flush=True)

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
        for name in ('save', 'save_file', 'save_model', 'load', 'load_file', 'load_model'):
            setattr(safetensors.torch, name, guarded('safetensors_' + name, getattr(safetensors.torch, name)))
        import data.runtime as runtime
        original = runtime.configure_scientific_runtime
        runtime.configure_scientific_runtime = lambda project_root=self.output: original(self.output)
        from braindecode.models import EEGNet, Labram
        EEGNet.from_pretrained = classmethod(no_pickle)
        Labram.from_pretrained = classmethod(no_pickle)
        from huggingface_hub import PyTorchModelHubMixin
        PyTorchModelHubMixin.from_pretrained = classmethod(no_pickle)
        return torch

    def clean(self):
        expected = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
            'source_file': str(self.connection),
            'source_sha256': self.pins['files'][self.connection.relative_to(ROOT).as_posix()]}
        if self.denied != [expected] or self.target_reads or self.protected:
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
        q = {'schema': 'cho51_complete_eegnet_' + self.mode + '_qualification_v1',
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
            'denied_operations': self.denied, 'unexpected_denials': 0, 'expected_blocked_ipv6_probes': 1,
            'observed_numerical_calls': self.numerical_calls,
            'source_updates': self.source_steps, 'support_updates': self.support_steps,
            'protected_target_transitions': self.protection_transitions,
            'protected_target_read_attempts': self.target_reads, 'fixture_input_read_phases': self.read_phases,
            'actual_study_inputs_or_pretrained_weights_used': False,
            'full_worker_verified': False, 'scientific_admission': False,
            'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0}
        if self.request is not None:
            q.update(request_sha256=request_sha256, case_id=self.request['case_id'],
                claim_file_sha256=self.request['claim_file_sha256'],
                fixture_source_sha256=self.request['fixture_source_sha256'],
                owner_decision_sha256=self.request['owner_decision_sha256'])
        write_json(self.output / 'qualification.json', q)
        for path, expected in loaded.items():
            if digest(path) != expected:
                raise ValueError('loaded module changed during qualification')
        self.clean()
        return q


def load_request(path, expected_sha256):
    if digest(path) != expected_sha256:
        raise ValueError('independently pinned claim request changed')
    request = read_json(path)
    if (request.get('schema') != 'cho51_complete_eegnet_request_v1'
            or request.get('scientific_admission') is not False
            or request.get('engineering_only') is not True
            or request.get('original_case_attempts_remaining') != 0
            or path != Path(request['workspace']) / 'request.json'
            or Path(request['fixture_root']) != RUN / 'validation_001/fixture'
            or Path(request['pins_path']) != RUN / 'pins.json'):
        raise ValueError('exact current owned complete engineering request required')
    if (digest(Path(request['claim_path'])) != request['claim_file_sha256']
            or digest(Path(request['pins_path'])) != request['independent_pins_sha256']):
        raise ValueError('independent request claim or bundle pins differ')
    return request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--expect-request', required=True)
    args = parser.parse_args()
    request = load_request(args.request, args.expect_request)
    before = {path: identity(path) for path in (args.request, Path(request['claim_path']))}
    runtime = Runtime('source', Path(request['pins_path']), request['independent_pins_sha256'],
        Path(request['selection_output']), request)
    runtime.install_torch_guards()
    from docs.phase2.cho51_complete_eegnet_v1.transaction import load_complete_request
    typed = load_complete_request(request)
    if typed.sha256 != args.expect_request:
        raise ValueError('exact typed independently pinned complete request required')
    from docs.phase2.cho51_complete_eegnet_v1.selection import run_selection
    runtime.active = True
    try:
        result = run_selection(request, set_protected_inputs=runtime.set_protected_inputs)
    finally:
        runtime.active = False
    if (result.get('schema') != 'cho51_complete_eegnet_source_result_v1' or result.get('passed') is not True
            or runtime.numerical_calls.get('tensor_backward') != 5253
            or runtime.numerical_calls.get('autograd_backward') != 5253
            or runtime.numerical_calls.get('autograd_grad', 0) != 0
            or runtime.numerical_calls.get('sgd_step') != 5253
            or runtime.source_steps != 5151 or runtime.support_steps != 102
            or [row['enabled'] for row in runtime.protection_transitions] != [True, False]):
        raise ValueError('actual complete public 5253-update EEGNet workload required')
    if any(identity(path) != pin for path, pin in before.items()):
        raise ValueError('claim or request changed across complete source work')
    runtime.finish(result, args.expect_request)
    print(json.dumps({'passed': True, 'actual_gradient_updates': 5253, 'scientific_admission': False}), flush=True)


if __name__ == '__main__':
    main()
