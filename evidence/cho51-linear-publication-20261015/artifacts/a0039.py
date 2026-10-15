"""Zero-training staged source publication and detached restoration runtime."""
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
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_publication_v1'
PREDECESSOR = ROOT / 'runs/coordination/cho51_linear_chain_20261015_v1'
PREDECESSOR_SHA = '1e3776fd84c22fdba9d36c97113ca1fb90ec5912018cfdcdd0c4cfcaa264be2e'
SNAPSHOT = ROOT / '.cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/0563b6c626e7b40d9a36653b763715db94d945d7'
BASELINE = SNAPSHOT / 'model.safetensors'
BASELINE_SHA = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
CONFIG = SNAPSHOT / 'config.json'
CONFIG_SHA = '813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b'
SOURCE_CHECKPOINT = ROOT / 'runs/coordination/cho51_linear_chain_20261015_v1/fragments/fragment_007/selected-source.safetensors'
SOURCE_CHECKPOINT_SHA = '3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048'
FIXTURE = ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture'
MIRROR = RUN / 'publication_001/project'
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
    def __init__(self, mode, pins_path, pins_sha256, output, publication_result=None):
        if mode not in ('publication', 'restoration') or (mode == 'publication') != (publication_result is None):
            raise ValueError('one exact publication or detached restoration stage required')
        self.mode, self.pins_path, self.pins_sha256 = mode, pins_path, pins_sha256
        if (pins_path != RUN / 'pins.json' or pins_path.resolve(strict=True) != pins_path
                or re.fullmatch('[a-f0-9]{64}', pins_sha256) is None
                or digest(pins_path) != pins_sha256):
            raise ValueError('exact independently pinned fresh bundle required')
        self.pins = read_json(pins_path)
        p = self.pins
        expected = {'schema': 'cho51_linear_publication_pins_v1',
            'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
            'predecessor_files': 1710, 'predecessor_pins_sha256': PREDECESSOR_SHA,
            'seconds': 600, 'process_mib': 4096, 'job_mib': 5120,
            'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
            'threads': 1, 'gpu_hidden': True, 'actual_gradient_updates': 0,
            'source_updates': 0, 'support_updates': 0, 'historical_gradient_updates': 5253,
            'cohort_lineage_verified': False,
            'full_worker_verified': False, 'scientific_admission': False,
            'original_case_attempts_remaining': 0, 'baseline_bytes': 23299672,
            'architecture_bytes': 4776, 'expected_tests': 20, 'expected_subtests': 0}
        if (any(type(p.get(key)) is not type(value) or p[key] != value for key, value in expected.items())
                or len(p.get('files', {})) <= 1710 or len(p.get('runtime', {})) != 5
                or p.get('baseline') != {str(BASELINE): BASELINE_SHA}
                or p.get('selected_weights') != {str(SOURCE_CHECKPOINT): SOURCE_CHECKPOINT_SHA}):
            raise ValueError('exact bounded no-gradient two-stage source publication required')
        self.output = output
        if output != RUN / (mode + '_001') or output.absolute() != output or output.resolve() != output:
            raise ValueError('one exact fresh stage output required')
        output.mkdir(exist_ok=False)
        self.fixture = FIXTURE
        self.publication_result = None
        self.publication_result_sha256 = None
        self.published_weights = None
        self.published_weights_sha256 = None
        self.published_weights_bytes = None
        self.publication_blob = None
        if publication_result is not None:
            path, sha = publication_result
            if (path != RUN / 'publication_001/publication-result.json' or digest(path) != sha):
                raise ValueError('exact independently pinned accepted publication result required')
            self.publication_result = read_json(path)
            self.publication_result_sha256 = sha
            self.published_weights = Path(self.publication_result['weights_path'])
            self.published_weights_sha256 = self.publication_result['weights_file_sha256']
            self.published_weights_bytes = self.publication_result['weights_bytes']
            if (not self.published_weights.is_relative_to(MIRROR / 'runs/phase2/selected_sources')
                    or self.published_weights.suffix != '.safetensors'
                    or type(self.published_weights_bytes) is not int or not 0 < self.published_weights_bytes <= 64 * 1024**2
                    or digest(self.published_weights) != self.published_weights_sha256):
                raise ValueError('exact externally bound canonical store weights required')
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
        self.pinned_files = {ROOT / relative: sha for relative, sha in p['files'].items()}
        self.denied = []
        self.hostname_queries = self.git_queries = self.existing_mkdir_refusals = 0
        self.numerical_calls = {}
        self.source_steps = self.support_steps = 0
        self.constructor_dummy_forward_calls = 0
        self.active = False
        self.protected = frozenset()
        self.protected_declared = ()
        self.protection_transitions = []
        self.target_reads = []
        self.read_phases = {}
        self.baseline_read_phases = {}
        self.context_hash_reads = {}
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
        if (len(predecessor.get('files', {})) != 1710 or len(predecessor.get('runtime', {})) != 5
                or any(p['files'].get(path) != sha for path, sha in predecessor['files'].items())
                or p['runtime'] != predecessor['runtime']):
            raise ValueError('exact 1710/5 frozen pin extension required')
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
        if SOURCE_CHECKPOINT.stat().st_size != 23294624 or digest(SOURCE_CHECKPOINT) != SOURCE_CHECKPOINT_SHA:
            raise ValueError('exact accepted full selected source checkpoint changed')
        if self.mode == 'restoration' and (self.published_weights.stat().st_size != self.published_weights_bytes
                or digest(self.published_weights) != self.published_weights_sha256
                or digest(RUN / 'publication_001/publication-result.json') != self.publication_result_sha256):
            raise ValueError('externally bound publication bytes changed')
        review_path = Path(p['source_review_path'])
        review = read_json(review_path)
        if (review_path != RUN / 'source-review.json' or digest(review_path) != p['source_review_sha256']
                or review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
                or review.get('files') != p['reviewed_files']
                or review.get('lineage_assets') != p['lineage_assets']
                or review.get('method_config_file_sha256') != p['method_config_file_sha256']
                or review.get('origin_contract_file_sha256') != p['origin_contract_file_sha256']
                or review.get('stage_contract_file_sha256') != p['stage_contract_file_sha256']
                or digest(RUN / 'origin-contract.json') != p['origin_contract_file_sha256']
                or digest(RUN / 'stage-contract.json') != p['stage_contract_file_sha256']
                or digest(RUN / 'method-config.json') != p['method_config_file_sha256']):
            raise ValueError('independent exact source/lineage/method review changed')
        pause_check()

    def refuse(self, event, detail=None):
        self.denied.append({'event': event, 'detail': repr(detail)[:500]})
        raise PermissionError('synthetic linear lineage denied: ' + event)

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
            fixture_git = cwd is not None and path_of(cwd) in (self.fixture, MIRROR)
            lineage_git = (cwd is not None and path_of(cwd) == ROOT and self.active
                and stack_has(self.entry, CANDIDATE / 'bridge.py')
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
            elif path in (BASELINE, SOURCE_CHECKPOINT) or path == self.published_weights:
                byte_hash = stack_has('verify_pins', RUN / 'runtime.py') and stack_has('digest', RUN / 'runtime.py')
                metadata_hash = self.metadata_stack()
                source_load = (self.mode == 'publication' and self.active
                    and stack_has('publish_source', CANDIDATE / 'bridge.py')
                    and stack_has('_load_selected_checkpoint', CANDIDATE / 'bridge.py'))
                baseline_load = (path == BASELINE and self.active
                    and stack_has(self.entry, CANDIDATE / 'bridge.py')
                    and any(stack_has(name, ROOT / 'evaluation/phase2_cho_source_restore.py')
                        for name in ('_new_model', 'prepare_cho_source_restore', '_check_labram_baseline')))
                store_load = (path == self.published_weights and self.mode == 'restoration' and self.active
                    and stack_has('verify_publication', CANDIDATE / 'bridge.py')
                    and (stack_has('restore', ROOT / 'evaluation/phase2_selected_source_store.py')
                        or stack_has('_files', CANDIDATE / 'bridge.py')
                        or stack_has('_restore_once', CANDIDATE / 'bridge.py')))
                if not (byte_hash or metadata_hash or source_load or baseline_load or store_load):
                    self.refuse('baseline_read_outside_exact_lineage_or_pin_hash', path)
                phase = 'pin_byte_hash' if byte_hash else 'metadata_byte_hash' if metadata_hash else 'stage_model_asset_read'
                self.baseline_read_phases[phase] = self.baseline_read_phases.get(phase, 0) + 1
            elif (self.mode == 'publication' and self.active
                    and path.is_relative_to(MIRROR / 'runs/phase2/selected_sources')
                    and path.suffix == '.safetensors'
                    and stack_has('publish_source', CANDIDATE / 'bridge.py')
                    and self.publication_blob is not None):
                if path.stat().st_size != self.publication_blob['bytes']:
                    self.refuse('owned_published_weights_differ_from_actual_serialization', path)
            else:
                parts = tuple(part.lower() for part in path.parts)
                data_path = any(parts[index:index + 2] in {('data', 'raw'), ('data', 'processed'), ('data', 'interim')}
                    for index in range(len(parts) - 1))
                if path == self.mne:
                    return
                metadata_pin_hash = (path in self.pinned_files
                    and path.suffix.lower() not in {'.npz', '.npy', '.mat', '.safetensors', '.pth', '.pt', '.ckpt'}
                    and ((stack_has('verify_pins', RUN / 'runtime.py') and stack_has('digest', RUN / 'runtime.py'))
                        or self.metadata_stack()))
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
        if (not self.active or not stack_has(self.entry, CANDIDATE / 'bridge.py')
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

    @property
    def entry(self):
        return 'publish_source' if self.mode == 'publication' else 'verify_publication'

    def metadata_stack(self):
        return any(stack_has(name, RUN / 'metadata.py') for name in (
            'build_origin', 'verify_origin', 'verify_stage_contract', 'verify_publication_proof',
            'verify_restoration_proof', 'verify_pin_map', 'verify_source_context'))

    def numerical_allowed(self, name):
        if not self.active or not stack_has(self.entry, CANDIDATE / 'bridge.py'):
            self.refuse('numerical_call_outside_exact_stage', name)
        allowed = {'model_module_init', 'module_load_state_dict', 'safetensors_load'}
        if self.mode == 'publication':
            allowed.add('safetensors_save')
        if name not in allowed:
            self.refuse('training_inference_or_unbound_serialization_forbidden', name)
        if name == 'model_module_init' and not stack_has('_new_model', ROOT / 'evaluation/phase2_cho_source_restore.py'):
            self.refuse('model_construction_outside_pinned_lineage', name)
        pause_check()
        self.numerical_calls[name] = self.numerical_calls.get(name, 0) + 1
        limits = {'module_load_state_dict': 2 if self.mode == 'publication' else 4,
            'safetensors_load': 3 if self.mode == 'publication' else 4,
            'safetensors_save': 1 if self.mode == 'publication' else 0}
        if name in limits and self.numerical_calls[name] > limits[name]:
            self.refuse('excess_exact_stage_call_budget', name)

    def install_torch_guards(self):
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        def forbidden(*args, **kwargs):
            self.refuse('fit_inference_pickle_optimizer_or_remote_forbidden', None)
        torch.load = torch.serialization.load = torch.jit.load = torch.hub.load = forbidden
        torch.save = torch.serialization.save = forbidden
        def guarded(name, original):
            def call(*args, **kwargs):
                self.numerical_allowed(name)
                return original(*args, **kwargs)
            return call
        torch.nn.Module.__init__ = guarded('model_module_init', torch.nn.Module.__init__)
        original_state_load = torch.nn.Module.load_state_dict
        def strict_state_load(model, state, *args, **kwargs):
            strict = args[0] if args else kwargs.get('strict', True)
            assign = args[1] if len(args) > 1 else kwargs.get('assign', False)
            approved = (stack_has('_new_model', ROOT / 'evaluation/phase2_cho_source_restore.py')
                or self.mode == 'publication' and stack_has('_load_selected_checkpoint', CANDIDATE / 'bridge.py')
                or self.mode == 'restoration' and stack_has('restore', ROOT / 'evaluation/phase2_selected_source_store.py'))
            if strict is not True or assign is not False or not approved or len(args) > 2:
                self.refuse('unbound_or_nonstrict_state_load', None)
            self.numerical_allowed('module_load_state_dict')
            self.numerical_calls['module_strict_load'] = self.numerical_calls.get('module_strict_load', 0) + 1
            return original_state_load(model, state, *args, **kwargs)
        torch.nn.Module.load_state_dict = strict_state_load
        original_call = torch.nn.Module._call_impl
        def constructor_dummy_call(module, *args, **kwargs):
            frame = sys._getframe(1)
            constructor = dummy = None
            while frame:
                if (frame.f_code.co_name == '__init__'
                        and path_of(frame.f_code.co_filename) == SITE / 'braindecode/models/labram.py'):
                    constructor, dummy = frame.f_locals.get('self'), frame.f_locals.get('dummy')
                    break
                frame = frame.f_back
            if (not self.active or not stack_has(self.entry, CANDIDATE / 'bridge.py')
                    or not stack_has('_new_model', ROOT / 'evaluation/phase2_cho_source_restore.py')
                    or constructor is None or not hasattr(constructor, 'patch_embed')
                    or not any(module is member for member in constructor.patch_embed.modules())
                    or torch.is_grad_enabled() or not isinstance(dummy, torch.Tensor)
                    or tuple(dummy.shape) != (1, int(constructor.n_chans), 3000)
                    or dummy.device.type != 'cpu' or dummy.dtype != torch.float32
                    or dummy.requires_grad or torch.count_nonzero(dummy).item() != 0):
                self.refuse('data_or_classifier_inference_forbidden', None)
            self.constructor_dummy_forward_calls += 1
            return original_call(module, *args, **kwargs)
        torch.nn.Module._call_impl = constructor_dummy_call
        torch.optim.Optimizer.__init__ = forbidden
        torch.optim.SGD.step = forbidden
        torch.Tensor.backward = forbidden
        torch.autograd.backward = torch.autograd.grad = forbidden
        import safetensors
        import safetensors.torch
        original_load, original_save = safetensors.torch.load, safetensors.torch.save
        original_deserialize, original_serialize = safetensors.torch.deserialize, safetensors.torch.serialize
        def valid_decode(raw):
            if type(raw) is not bytes:
                return False
            sha = hashlib.sha256(raw).hexdigest()
            baseline = (len(raw) == 23299672 and sha == BASELINE_SHA
                and stack_has('_new_model', ROOT / 'evaluation/phase2_cho_source_restore.py'))
            selected = (self.mode == 'publication' and len(raw) == 23294624 and sha == SOURCE_CHECKPOINT_SHA
                and stack_has('_load_selected_checkpoint', CANDIDATE / 'bridge.py'))
            roundtrip = (self.mode == 'publication' and self.publication_blob is not None
                and len(raw) == self.publication_blob['bytes'] and sha == self.publication_blob['sha256']
                and stack_has('publish', ROOT / 'evaluation/phase2_selected_source_store.py'))
            restoration = (self.mode == 'restoration' and len(raw) == self.published_weights_bytes
                and sha == self.published_weights_sha256
                and stack_has('restore', ROOT / 'evaluation/phase2_selected_source_store.py'))
            return baseline or selected or roundtrip or restoration
        def load_checked(raw):
            self.numerical_allowed('safetensors_load')
            if not valid_decode(raw):
                self.refuse('unbound_safe_tensor_decode', None)
            return original_load(raw)
        def deserialize_checked(raw):
            if (not self.active or not stack_has('load_checked', RUN / 'runtime.py')
                    or not stack_has('load', SITE / 'safetensors/torch.py') or not valid_decode(raw)):
                self.refuse('unbound_low_level_safe_tensor_decode', None)
            return original_deserialize(raw)
        serialization_active = False
        def serialize_checked(*args, **kwargs):
            if (not serialization_active or not self.active or self.mode != 'publication'
                    or not stack_has('save_checked', RUN / 'runtime.py')
                    or not stack_has('save', SITE / 'safetensors/torch.py')
                    or not stack_has('publish', ROOT / 'evaluation/phase2_selected_source_store.py')
                    or not stack_has('publish_source', CANDIDATE / 'bridge.py')):
                self.refuse('unbound_store_tensor_serialization', None)
            return original_serialize(*args, **kwargs)
        def save_checked(state):
            nonlocal serialization_active
            if (self.mode != 'publication' or self.publication_blob is not None
                    or not stack_has('publish', ROOT / 'evaluation/phase2_selected_source_store.py')
                    or type(state) is not dict or len(state) != 223
                    or any(not isinstance(value, torch.Tensor) or value.device.type != 'cpu'
                        or value.dtype != torch.float32 for value in state.values())):
                self.refuse('unbound_store_safe_tensor_save', None)
            self.numerical_allowed('safetensors_save')
            serialization_active = True
            try:
                raw = original_save(state)
            finally:
                serialization_active = False
            if type(raw) is not bytes or not 0 < len(raw) <= 64 * 1024**2:
                self.refuse('store_safe_tensor_bound', None)
            self.publication_blob = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            return raw
        for name in ('serialize', 'serialize_file', 'deserialize', 'safe_open'):
            setattr(safetensors, name, forbidden)
        for name in ('serialize_file', 'save_file', 'save_model', 'load_file', 'load_model', 'safe_open'):
            setattr(safetensors.torch, name, forbidden)
        safetensors.torch.load, safetensors.torch.save = load_checked, save_checked
        safetensors.torch.deserialize, safetensors.torch.serialize = deserialize_checked, serialize_checked
        import evaluation.phase2_selected_source_store as store_module
        store_module.load, store_module.save = load_checked, save_checked
        import data.runtime as scientific_runtime
        original = scientific_runtime.configure_scientific_runtime
        scientific_runtime.configure_scientific_runtime = lambda project_root=self.output: original(self.output)
        from braindecode.models import EEGNet, Labram
        EEGNet.from_pretrained = classmethod(forbidden)
        Labram.from_pretrained = classmethod(forbidden)
        from huggingface_hub import PyTorchModelHubMixin
        PyTorchModelHubMixin.from_pretrained = classmethod(forbidden)
        from evaluation.phase2_runner import CaseRecorder
        CaseRecorder.__init__ = forbidden
        return torch

    def clean(self):
        expected = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
            'source_file': str(self.connection),
            'source_sha256': self.pins['files'][self.connection.relative_to(ROOT).as_posix()]}
        if self.denied != [expected] or self.target_reads or self.protected or self.active:
            raise RuntimeError('unexpected audit denial or unfinished target/numerical scope')

    def finish(self, result):
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
            if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(self.output):
                loaded[str(Path(name).resolve())] = digest(name)
        q = {'schema': 'cho51_linear_' + self.mode + '_qualification_v1', 'mode': self.mode,
            'passed': result.get('passed') is True, 'pins_sha256': self.pins_sha256, 'result': result,
            'observed_utc': datetime.now(timezone.utc).isoformat(), 'elapsed_seconds': time.monotonic() - self.started,
            'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
            'source_pins_rechecked': len(self.pins['files']), 'runtime_pins_rechecked': len(self.pins['runtime']),
            'baseline_pins_rechecked': 1, 'baseline_file_sha256': BASELINE_SHA,
            'source_review_sha256': self.pins['source_review_sha256'],
            'stage_contract_file_sha256': self.pins['stage_contract_file_sha256'],
            'origin_contract_file_sha256': self.pins['origin_contract_file_sha256'],
            'publication_result_file_sha256': self.publication_result_sha256,
            'tests_executed': result['tests_executed'], 'tests_reused': result['tests_reused'],
            'tests_passed': result['tests_passed'],
            'observed_loaded_module_hashes': loaded, 'loaded_module_files': len(loaded),
            'environment_sha256': environment_digest(), 'torch_threads': 1, 'torch_interop_threads': 1,
            'gpu_hidden': True, 'read_only_git_queries': self.git_queries,
            'hostname_metadata_queries': self.hostname_queries,
            'existing_directory_mkdir_refusals': self.existing_mkdir_refusals,
            'denied_operations': self.denied, 'unexpected_denials': 0, 'expected_blocked_ipv6_probes': 1,
            'observed_numerical_calls': self.numerical_calls,
            'constructor_dummy_forward_calls': self.constructor_dummy_forward_calls,
            'target_or_classifier_inference_calls': 0,
            'source_updates': self.source_steps, 'support_updates': self.support_steps,
            'actual_gradient_updates': self.source_steps + self.support_steps,
            'historical_gradient_updates': 5253,
            'baseline_read_phases': self.baseline_read_phases, 'context_metadata_hash_reads': self.context_hash_reads,
            'protected_target_transitions': self.protection_transitions,
            'protected_target_read_attempts': self.target_reads, 'fixture_input_read_phases': self.read_phases,
            'pretrained_baseline_loaded': result.get('pretrained_baseline_loaded') is True,
            'actual_study_data_used': False,
            'cohort_lineage_verified': False, 'full_selector_verified': False,
            'full_worker_verified': False, 'scientific_admission': False,
            'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0}
        write_json(self.output / 'qualification.json', q)
        for path, expected in loaded.items():
            if digest(path) != expected:
                raise ValueError('loaded module changed during qualification')
        self.clean()
        return q
