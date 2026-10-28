"""Narrow confinement for one locked provenance-aware restoration transaction."""
from __future__ import annotations

import ctypes
import functools
import hashlib
import msvcrt
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(RUN))
import origin

digest, identity, read_json = origin.digest, origin.identity, origin.document
CANONICAL = origin.CANONICAL
SITE = ROOT / '.venv/Lib/site-packages'
CANDIDATE = ROOT / 'docs/phase2/cho51_provenance_restore_v1'
FACTORY = CANDIDATE / 'factory.py'
PAUSES = tuple(Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json'
               for day in ('20261007', '20261012', '20261013', '20261015', '20261025'))


def write_json(path, value):
    raw = origin.canonical(value)
    with Path(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def path_of(value):
    value = os.fsdecode(value)
    return Path(value[4:] if value.startswith('\\\\?\\') else value).resolve()


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
    def __init__(self, pins_path, pins_sha256, output):
        origin.need(pins_path == RUN / 'pins.json' and digest(pins_path) == pins_sha256,
                    'exact independently admitted fresh pins required')
        self.pins_path, self.pins_sha256, self.output = pins_path, pins_sha256, output
        self.pins = read_json(pins_path)
        expected = dict(schema='cho51_provenance_restore_pins_v1', canonical_source_sha256=CANONICAL,
                        canonical_files=432, seconds=600, process_mib=4096, job_mib=5120,
                        startup_ram_gib=4, active_ram_gib=4, disk_gib=20, threads=1, gpu_hidden=True,
                        previous_startup_ram_gib=10, historical_10gib_startup_pass_claimed=False,
                        current_restore_count=1, current_source_updates=0, current_support_updates=0,
                        current_gradient_updates=0, target_inference_calls=0, measured_cells=0,
                        scientific_admission=False, original_case_attempts_remaining=0)
        origin.need(all(type(self.pins.get(name)) is type(value) and self.pins[name] == value
                        for name, value in expected.items()), 'exact restoration-only admission required')
        origin.need(output == RUN / 'validation_001' and output.resolve() == output, 'unused direct output required')
        output.mkdir(exist_ok=False)
        self.contract = read_json(RUN / 'origin-contract.json')
        origin.need(self.contract['schema'] == 'cho51_provenance_restore_origin_v1', 'fresh origin contract required')
        self.origin_files = {Path(name): value for name, value in self.contract['files'].items()}
        _, self.fixture, inputs = origin.original_inventory()
        self.input_pins = {self.fixture / name: row['sha256'] for name, row in inputs.items()}
        self.baseline = Path(next(iter(self.pins['baseline'])))
        self.selected = Path(next(iter(self.pins['selected_weights'])))
        self.verify_pins()
        folders = {'TEMP': 'temp', 'TMP': 'temp', 'TMPDIR': 'temp', 'MPLCONFIGDIR': 'mpl', 'HF_HOME': 'hf',
                   '_MNE_FAKE_HOME_DIR': 'mne-home', 'HF_HUB_CACHE': 'hf/hub', 'HUGGINGFACE_HUB_CACHE': 'hf/hub',
                   'TRANSFORMERS_CACHE': 'hf/transformers', 'TORCH_HOME': 'torch', 'NUMBA_CACHE_DIR': 'numba',
                   'JOBLIB_TEMP_FOLDER': 'joblib', 'XDG_CACHE_HOME': 'cache'}
        for folder in sorted(set(folders.values()), key=lambda value: (value.count('/'), value)):
            (output / folder).mkdir()
        for name, folder in folders.items():
            os.environ[name] = str(output / folder)
        for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
            os.environ[name] = '1'
        os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                          PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
        sys.dont_write_bytecode = True
        sys.path[:0] = [str(ROOT), str(SITE)]
        self.git_command = shutil.which('git')
        self.git_path = Path(self.git_command).resolve() if self.git_command else None
        origin.need(self.git_path is not None and str(self.git_path) in self.pins['runtime'], 'freshly pinned Git required')
        self.active, self.locked, self.binding = False, None, None
        self.request_identity, self.claim_identity = None, None
        self.calls, self.denied, self.sensitive_reads = {}, [], {}
        self.model_constructions = self.constructor_dummy_forward_calls = self.lock_checks = 0
        self.git_queries = self.hostname_queries = self.existing_mkdir_refusals = 0
        self.connection = SITE / 'urllib3/util/connection.py'
        self.mne = Path(self.pins['mne_resource_path'])
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong]
        self.api.GetFinalPathNameByHandleW.restype = ctypes.c_ulong
        self.native_binding = self.bind_native()
        sys.addaudithook(self.audit)
        self.started = time.monotonic()
        pause_check()

    def bind_native(self):
        command = [str(Path(sys.executable).resolve()), '-I', '-S', '-B', str(RUN / 'parent.py'),
                   '--pins', str(self.pins_path), '--expect-pins', self.pins_sha256, '--output', str(self.output)]
        matches = []
        for directory in (ROOT / 'runs/migration').iterdir():
            admission_path = directory / 'admission.json'
            if directory.is_dir() and admission_path.is_file() and not (directory / 'receipt.json').exists():
                value = read_json(admission_path, maximum=1024**2)
                if value.get('command') == command:
                    matches.append((directory, admission_path, value))
        origin.need(len(matches) == 1, 'one fresh live native admission must bind exact child command')
        directory, admission_path, admission = matches[0]
        operations = {name: value for name, value in self.pins['files'].items()
                      if Path(name).parent == Path('tools/migration') and Path(name).suffix in {'.py', '.ps1', '.json', '.lock'}
                      or name == 'evaluation/phase2_supervision_primitives.py'
                      or name in self.pins['reviewed_files'] and Path(name).parent == RUN.relative_to(ROOT)}
        origin.need(admission['source_sha256'] == CANONICAL and admission['process_mib'] == 4096
                    and admission['job_mib'] == 5120 and admission['active_ram_gib'] == 4
                    and admission['active_disk_gib'] == 20 and admission['native_threads'] == 1
                    and admission['operation_pins'] == operations and admission['startup_ram_gib'] == 4
                    and admission['previous_startup_ram_gib'] == 10 and admission['historical_10gib_startup_pass_claimed'] is False
                    and admission['guard_policy_schema'] == 'cho51_provenance_restore_guard_v1'
                    and admission['owner_resource_amendment_path'] == self.pins['owner_resource_amendment_path']
                    and admission['owner_resource_amendment_sha256'] == self.pins['owner_resource_amendment_sha256']
                    and len(admission['startup_samples']) == 2 and all(
                        type(row['available_ram_bytes']) is int and row['available_ram_bytes'] >= 4 * 1024**3
                        and type(row['free_disk_bytes']) is int and row['free_disk_bytes'] >= 20 * 1024**3
                        for row in admission['startup_samples']), 'native admission differs from owner-amended fixed scope')
        self.root_admission_identity = identity(RUN / 'admission.json')
        dispatch = read_json(RUN / 'dispatch_001.json')
        root_admission = read_json(RUN / 'admission.json', dispatch['admission_sha256'])
        required = dict(schema='cho51_provenance_restore_admission_v1', pins_sha256=self.pins_sha256,
                        source_review_sha256=self.pins['source_review_sha256'], accepted=True,
                        scientific_admission=False, max_job_seconds=600, process_mib=4096, job_mib=5120,
                        startup_ram_gib=4, active_ram_gib=4, disk_gib=20,
                        owner_resource_amendment_path=self.pins['owner_resource_amendment_path'],
                        owner_resource_amendment_sha256=self.pins['owner_resource_amendment_sha256'])
        origin.need(all(type(root_admission.get(name)) is type(value) and root_admission[name] == value
                        for name, value in required.items()), 'fresh exact root admission differs')
        self.peer_release_path = Path(root_admission['peer_release_path'])
        self.peer_release_identity = identity(self.peer_release_path)
        peer_release = read_json(self.peer_release_path, root_admission['peer_release_sha256'])
        required_peer = dict(schema='pro2_pro3_compute_release_v1', scope='cho51_provenance_restore_20261025_v1',
                             released=True, pins_sha256=self.pins_sha256, maximum_jobs=1, max_job_seconds=600,
                             process_mib=4096, job_mib=5120, window_start_utc=root_admission['window_start_utc'],
                             window_end_utc=root_admission['window_end_utc'])
        origin.need(all(type(peer_release.get(name)) is type(value) and peer_release[name] == value
                        for name, value in required_peer.items()), 'explicit exact peer compute release differs')
        utc = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        self.peer_window_end = utc(root_admission['window_end_utc'])
        origin.need(utc(root_admission['window_start_utc']) <= utc(admission['started_utc']) <= now
                    <= utc(admission['deadline_utc']) <= self.peer_window_end,
                    'live child and fixed native deadline must remain within fresh explicit peer release')
        self.api.OpenJobObjectW.argtypes = [ctypes.c_ulong, ctypes.c_bool, ctypes.c_wchar_p]
        self.api.OpenJobObjectW.restype = ctypes.c_void_p
        self.api.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        self.api.IsProcessInJob.restype = ctypes.c_bool
        self.api.CloseHandle.argtypes = [ctypes.c_void_p]
        self.api.CloseHandle.restype = ctypes.c_bool
        job_name = 'pro3_migration_' + directory.name
        handle = self.api.OpenJobObjectW(0x0004, False, job_name)
        origin.need(bool(handle), 'fresh named native Job must exist')
        try:
            member = ctypes.c_int()
            origin.need(self.api.IsProcessInJob(ctypes.c_void_p(-1), handle, ctypes.byref(member))
                        and member.value == 1, 'restoration child must belong to exact admitted native Job')
        finally:
            origin.need(self.api.CloseHandle(handle), 'native membership-query handle must close')
        return dict(native_directory=str(directory), job_name=job_name, admission_path=str(admission_path),
                    admission_sha256=digest(admission_path), command=command, membership_verified=True,
                    root_admission_sha256=self.root_admission_identity[-1], peer_release_path=str(self.peer_release_path),
                    peer_release_sha256=self.peer_release_identity[-1], peer_window_end_utc=root_admission['window_end_utc'])

    def verify_pins(self):
        pause_check()
        if hasattr(self, 'root_admission_identity'):
            origin.need(identity(RUN / 'admission.json') == self.root_admission_identity
                        and identity(self.peer_release_path) == self.peer_release_identity
                        and datetime.now(timezone.utc) <= self.peer_window_end, 'live peer release or root admission changed or expired')
        origin.need(digest(self.pins_path) == self.pins_sha256, 'fresh pins changed')
        for name, value in self.pins['files'].items():
            origin.need(digest(ROOT / name) == value, 'current or historical source/context pin changed: ' + name)
        for group, count in (('runtime', 5), ('runtime_modules', 18), ('supporting_runtime_sources', 4)):
            origin.need(len(self.pins[group]) == count, 'exact admitted runtime inventory required')
            for path, value in self.pins[group].items():
                origin.need(digest(path) == value, 'fresh runtime changed: ' + path)
        review = read_json(RUN / 'source-review.json')
        origin.need(review['source_only'] is True and review['remaining_actionable_findings'] == []
                    and review['files'] == self.pins['reviewed_files'], 'settled source review changed')
        amendment_path = Path(self.pins['owner_resource_amendment_path'])
        origin.need(amendment_path == RUN / 'owner-resource-amendment.json', 'exact direct-owner amendment path required')
        amendment = read_json(amendment_path, self.pins['owner_resource_amendment_sha256'])
        expected_amendment = dict(schema='cho51_provenance_restore_owner_resource_amendment_v1',
                                 scope='cho51_provenance_restore_20261025_v1', previous_startup_ram_gib=10,
                                 owner_instruction_exact='work with the 4GiB ram you have for now. it will be enough.',
                                 startup_ram_gib=4, active_ram_gib=4, disk_gib=20, maximum_job_seconds=600,
                                 process_mib=4096, job_mib=5120, canonical_guard_modified=False,
                                 historical_receipts_requalified=False, scientific_admission=False)
        origin.need(all(type(amendment.get(name)) is type(value) and amendment[name] == value
                        for name, value in expected_amendment.items()), 'direct-owner startup-only amendment differs')

    def refuse(self, event, detail=None):
        self.denied.append(dict(event=event, detail=repr(detail)[:500]))
        raise PermissionError('restoration denied: ' + event)

    def fd_path(self, descriptor):
        if type(descriptor) is not int:
            return None
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            count = self.api.GetFinalPathNameByHandleW(msvcrt.get_osfhandle(descriptor), buffer, len(buffer), 0)
            return path_of(buffer.value) if 0 < count < len(buffer) else None
        except OSError:
            return None

    def audit(self, event, values):
        if event == 'socket.gethostname':
            self.hostname_queries += 1
        elif event.startswith('socket.'):
            if (event == 'socket.__new__' and values[1:] == (socket.AF_INET6, socket.SOCK_STREAM, 0)
                    and stack_has('_has_ipv6', self.connection)):
                self.denied.append(dict(event=event, classification='blocked_optional_ipv6_import_probe',
                                        source_file=str(self.connection),
                                        source_sha256=self.pins['files'][self.connection.relative_to(ROOT).as_posix()]))
                raise PermissionError('optional IPv6 import probe blocked')
            self.refuse(event, values)
        elif event == 'subprocess.Popen':
            executable, arguments, cwd, environment = values
            forms = [[self.git_command, '--no-optional-locks', *tail] for tail in
                     (['rev-parse', '--verify', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'])]
            allowed_cwd = cwd is not None and (path_of(cwd) in {ROOT, self.output / 'fixture'}
                          or path_of(cwd).is_relative_to(self.output / 't') and self.test_stack())
            if (any(arguments == form or arguments == subprocess.list2cmdline(form) for form in forms)
                    and (executable is None and os.name == 'nt' or isinstance(executable, (str, bytes, os.PathLike))
                         and path_of(executable) == self.git_path)
                    and allowed_cwd and environment is None
                    and stack_has('capture_source', ROOT / 'core/provenance.py')):
                self.git_queries += 1
            else:
                self.refuse(event, values)
        elif event in {'os.system', 'os.startfile', 'os.posix_spawn', 'os.fork', 'os.forkpty', 'pty.spawn'} or event.startswith(('os.exec', 'os.spawn')):
            self.refuse(event, values)
        elif event == 'open':
            mode, flags = values[1] if isinstance(values[1], str) else '', values[2] if isinstance(values[2], int) else 0
            writing = any(value in mode for value in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            path = path_of(values[0]) if isinstance(values[0], (str, bytes, os.PathLike)) else self.fd_path(values[0])
            if path is None:
                if writing:
                    self.refuse('unbound_descriptor_write', values)
                return
            if writing:
                if not path.is_relative_to(self.output):
                    self.refuse('outside_owned_write', path)
                return
            parts = tuple(part.lower() for part in path.parts)
            sensitive = (any(parts[index:index + 2] in {('data', 'raw'), ('data', 'processed'), ('data', 'interim')}
                             for index in range(len(parts) - 1)) or 'weights' in parts or 'checkpoints' in parts
                         or path.suffix.lower() in {'.npz', '.npy', '.mat', '.edf', '.gdf', '.fif', '.set', '.pt', '.pth', '.ckpt', '.safetensors'})
            if not sensitive:
                return
            if path == self.mne and path.stat().st_size == 260:
                return
            if path.suffix.lower() == '.pth' and path.is_relative_to(SITE):
                return
            test_read = (path.is_relative_to(self.output / 't') and path.suffix.lower() == '.safetensors'
                         and path.stat().st_size <= 1024**2 and self.test_stack())
            history_hash = (path in self.origin_files or path in self.input_pins) and any(
                stack_has(name, RUN / 'origin.py') for name in ('digest', 'verify_inputs', 'verify_origin_stages'))
            baseline = (path == self.baseline and self.active and self.lock_live()
                        and stack_has('restore', FACTORY) and any(stack_has(name, ROOT / 'evaluation/phase2_cho_source_restore.py')
                        for name in ('_new_model', 'prepare_cho_source_restore', '_check_labram_baseline')))
            selected = (path == self.selected and self.active and self.lock_live() and stack_has('restore', FACTORY))
            selected_metadata = path == self.selected and self.lock_live() and stack_has('authenticate', FACTORY)
            if test_read or history_hash or baseline or selected or selected_metadata:
                purpose = ('test_metadata' if test_read else 'history_hash' if history_hash else 'baseline_restore'
                           if baseline else 'selected_metadata_hash' if selected_metadata else 'selected_restore')
                row = self.sensitive_reads.setdefault(str(path), {})
                row[purpose] = row.get(purpose, 0) + 1
                return
            self.refuse('unbound_signal_or_weight_read', path)
        elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace', 'os.link', 'os.symlink', 'os.chmod', 'os.utime', 'os.truncate'}:
            count = 2 if event in {'os.rename', 'os.replace', 'os.link', 'os.symlink'} else 1
            for value in values[:count]:
                if not isinstance(value, (str, bytes, os.PathLike)):
                    self.refuse('unbound_mutation', values)
                path = path_of(value)
                if event == 'os.mkdir' and not path.is_relative_to(self.output) and path.is_dir():
                    self.existing_mkdir_refusals += 1
                    raise FileExistsError(17, 'existing outside directory creation refused', os.fsdecode(value))
                if not path.is_relative_to(self.output):
                    self.refuse('outside_owned_mutation', path)
        elif event == 'os.chdir' and not path_of(values[0]).is_relative_to(self.output):
            self.refuse(event, values)

    def lock_live(self):
        if self.locked is None or self.binding is None or not stack_has('locked_restore', RUN / 'parent.py'):
            return False
        self.locked._require_active()
        request_path, claim_path = Path(self.binding['request_path']), Path(self.binding['claim_path'])
        origin.need(identity(request_path) == self.request_identity and identity(claim_path) == self.claim_identity,
                    'live transaction request or claim changed')
        self.lock_checks += 1
        return True

    def test_stack(self):
        frame = sys._getframe(1)
        while frame:
            if path_of(frame.f_code.co_filename) == CANDIDATE / 'test_factory.py':
                return True
            frame = frame.f_back
        return False

    def numerical(self, name):
        if not self.active or not self.lock_live() or not stack_has('restore', FACTORY):
            self.refuse('numerics_outside_locked_factory', name)
        if name not in {'model_module_init', 'module_load_state_dict', 'safetensors_load'}:
            self.refuse('forbidden_training_or_query', name)
        if name == 'model_module_init' and not stack_has('_new_model', ROOT / 'evaluation/phase2_cho_source_restore.py'):
            self.refuse('unbound_model_constructor', name)
        self.calls[name] = self.calls.get(name, 0) + 1
        if name != 'model_module_init' and self.calls[name] > 2:
            self.refuse('restore_numerical_budget_exceeded', name)
        pause_check()

    def install_torch_guards(self):
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        def forbidden(*arguments, **keywords):
            self.refuse('pickle_remote_training_query_or_unbound_array', None)
        torch.load = torch.serialization.load = torch.jit.load = torch.hub.load = forbidden
        torch.save = torch.serialization.save = torch.autograd.grad = forbidden
        original_init = torch.nn.Module.__init__
        @functools.wraps(original_init)
        def module_init(module, *arguments, **keywords):
            self.numerical('model_module_init')
            if type(module).__name__ == 'Labram':
                self.model_constructions += 1
                if self.model_constructions > 1:
                    self.refuse('full_model_constructor_budget', None)
            return original_init(module, *arguments, **keywords)
        torch.nn.Module.__init__ = module_init
        original_state = torch.nn.Module.load_state_dict
        def strict_load(model, state, *arguments, **keywords):
            strict = arguments[0] if arguments else keywords.get('strict', True)
            assign = arguments[1] if len(arguments) > 1 else keywords.get('assign', False)
            if strict is not True or assign is not False or len(arguments) > 2 or not stack_has('restore', FACTORY):
                self.refuse('unbound_or_nonstrict_state_load', None)
            self.numerical('module_load_state_dict')
            return original_state(model, state, *arguments, **keywords)
        torch.nn.Module.load_state_dict = strict_load
        original_call = torch.nn.Module._call_impl
        def model_call(module, *arguments, **keywords):
            if self.active and self.lock_live() and stack_has('restore', FACTORY) and stack_has('_new_model', ROOT / 'evaluation/phase2_cho_source_restore.py'):
                frame, constructor, dummy = sys._getframe(1), None, None
                while frame:
                    if frame.f_code.co_name == '__init__' and path_of(frame.f_code.co_filename) == SITE / 'braindecode/models/labram.py':
                        constructor, dummy = frame.f_locals.get('self'), frame.f_locals.get('dummy')
                        break
                    frame = frame.f_back
                if (constructor is None or not hasattr(constructor, 'patch_embed')
                        or not any(module is member for member in constructor.patch_embed.modules())
                        or torch.is_grad_enabled() or not isinstance(dummy, torch.Tensor)
                        or tuple(dummy.shape) != (1, int(constructor.n_chans), 3000) or dummy.device.type != 'cpu'
                        or dummy.dtype != torch.float32 or dummy.requires_grad or torch.count_nonzero(dummy).item() != 0):
                    self.refuse('unbound_constructor_patch_probe', type(module).__name__)
                if module is constructor.patch_embed:
                    self.constructor_dummy_forward_calls += 1
                    if self.constructor_dummy_forward_calls > 1:
                        self.refuse('constructor_patch_probe_budget', None)
                return original_call(module, *arguments, **keywords)
            self.refuse('model_forward_or_query_forbidden', type(module).__name__)
        torch.nn.Module._call_impl = model_call
        torch.optim.Optimizer.__init__ = torch.optim.SGD.step = torch.Tensor.backward = torch.autograd.backward = forbidden
        import safetensors
        import safetensors.torch
        original_load, original_deserialize = safetensors.torch.load, safetensors.torch.deserialize
        def valid(raw):
            if type(raw) is not bytes:
                return False
            value = hashlib.sha256(raw).hexdigest()
            return (len(raw) == 23299672 and value == origin.BASELINE_SHA
                    and stack_has('_new_model', ROOT / 'evaluation/phase2_cho_source_restore.py')
                    or len(raw) == 23294624 and value == origin.WEIGHTS_SHA and stack_has('restore', FACTORY))
        def safe_load(raw):
            self.numerical('safetensors_load')
            if not valid(raw):
                self.refuse('unbound_safe_tensor_decode', None)
            return original_load(raw)
        def deserialize(raw):
            if not stack_has('safe_load', RUN / 'runtime.py') or not valid(raw):
                self.refuse('unbound_low_level_decode', None)
            return original_deserialize(raw)
        for name in ('serialize', 'serialize_file', 'deserialize', 'safe_open'):
            setattr(safetensors, name, forbidden)
        for name in ('save', 'save_file', 'save_model', 'load_file', 'load_model', 'safe_open', 'serialize', 'serialize_file'):
            setattr(safetensors.torch, name, forbidden)
        safetensors.torch.load, safetensors.torch.deserialize = safe_load, deserialize
        import numpy
        for name in ('load', 'save', 'savez', 'savez_compressed', 'fromfile', 'loadtxt', 'genfromtxt'):
            setattr(numpy, name, forbidden)
        from braindecode.models import EEGNet, Labram
        EEGNet.from_pretrained = Labram.from_pretrained = classmethod(forbidden)
        from huggingface_hub import PyTorchModelHubMixin
        PyTorchModelHubMixin.from_pretrained = classmethod(forbidden)
        import data.runtime as scientific_runtime
        original_runtime = scientific_runtime.configure_scientific_runtime
        scientific_runtime.configure_scientific_runtime = lambda project_root=self.output: original_runtime(self.output)
        from evaluation.phase2_runner import CaseRecorder
        original_recorder = CaseRecorder.__init__
        def isolated_recorder(recorder, root, *, output_root=None):
            actual = Path(root).resolve()
            destination = Path(output_root).resolve() if output_root is not None else actual / 'runs/phase2/recorder'
            production = actual == self.output / 'fixture' and destination == actual / 'runs/phase2/lifecycle'
            frame, test_stack = sys._getframe(1), False
            while frame:
                if path_of(frame.f_code.co_filename) == CANDIDATE / 'test_factory.py':
                    test_stack = True
                    break
                frame = frame.f_back
            isolated_test = (test_stack and actual.is_relative_to(self.output / 't')
                             and destination is not None and destination.is_relative_to(self.output / 't'))
            if self.active or not (production or isolated_test):
                self.refuse('shared_recorder_constructor', root)
            return original_recorder(recorder, root, output_root=output_root)
        CaseRecorder.__init__ = isolated_recorder
        CaseRecorder.record_cell = CaseRecorder._record_cell_locked = forbidden
        return torch

    def finish(self, result):
        import torch
        from tools.migration.common import source_check
        self.verify_pins()
        origin.need(source_check(ROOT) == CANONICAL and torch.get_num_threads() == torch.get_num_interop_threads() == 1
                    and os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not self.active, 'source or confinement changed')
        expected_probe = dict(event='socket.__new__', classification='blocked_optional_ipv6_import_probe',
                              source_file=str(self.connection),
                              source_sha256=self.pins['files'][self.connection.relative_to(ROOT).as_posix()])
        origin.need(self.denied in ([], [expected_probe]), 'unexpected audit denial')
        if result['passed']:
            origin.need(self.calls.get('module_load_state_dict') == self.calls.get('safetensors_load') == 2
                        and self.model_constructions == self.constructor_dummy_forward_calls == 1 and self.lock_checks > 0,
                        'exact actual restoration counters required')
        loaded = {}
        for module in tuple(sys.modules.values()):
            name = getattr(module, '__file__', None)
            if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(self.output):
                loaded[str(Path(name).resolve())] = digest(Path(name).resolve())
        qualification = dict(schema='cho51_provenance_restore_qualification_v1', passed=result['passed'],
                             result=result, observed_utc=datetime.now(timezone.utc).isoformat(),
                             elapsed_seconds=time.monotonic() - self.started, pins_sha256=self.pins_sha256,
                             canonical_files=432, canonical_source_sha256=CANONICAL,
                             observed_numerical_calls=self.calls, model_constructions=self.model_constructions,
                             constructor_dummy_forward_calls=self.constructor_dummy_forward_calls,
                             lock_checks=self.lock_checks, sensitive_reads=self.sensitive_reads,
                             denied_operations=self.denied, unexpected_denials=0,
                             observed_loaded_module_hashes=loaded, loaded_module_files=len(loaded),
                             source_pins_rechecked=len(self.pins['files']), runtime_pins_rechecked=5,
                             runtime_module_pins_rechecked=18, supporting_runtime_sources_rechecked=4,
                             torch_threads=1, torch_interop_threads=1, gpu_hidden=True,
                             current_source_updates=0, current_support_updates=0, current_gradient_updates=0,
                             target_inference_calls=0, numpy_load_count=0, measured_cells=0,
                             scientific_admission=False, native_closeout_status='pending_external_post_job')
        write_json(self.output / 'qualification.json', qualification)
        for path, value in loaded.items():
            origin.need(digest(path) == value, 'loaded module changed during qualification')
        return qualification
