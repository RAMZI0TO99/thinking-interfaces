"""Native confinement and independent observation for one composed numerical case."""
from __future__ import annotations

import ctypes
import functools
import hashlib
import io
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
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_target_route_v1'
WORKER = ROOT / 'docs/phase2/cho51_provenance_numerical_worker_v2'
HISTORICAL_WORKER = ROOT / 'docs/phase2/cho51_linear_worker_route_v3'
LEGACY_WORKER = ROOT / 'docs/phase2/cho51_linear_numerical_worker_v1'
TARGET_ORIGIN = ROOT / 'runs/coordination/cho51_linear_target_route_20261017_v3/origin.py'
TRANSACTION = ROOT / 'docs/phase2/cho51_linear_recorder_v1/transaction.py'
FACTORY = ROOT / 'docs/phase2/cho51_provenance_restore_v1/factory.py'
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
        self.phase = origin.phase_from_output(output)
        self.phase_paths = origin.phase_paths(self.phase)
        self.tests_join = None
        expected = dict(schema='cho51_provenance_numerical_worker_pins_v1', canonical_source_sha256=CANONICAL,
                        canonical_files=432, seconds=600, process_mib=4096, job_mib=5120,
                        startup_ram_gib=4, active_ram_gib=4, disk_gib=20, threads=1, gpu_hidden=True,
                        previous_startup_ram_gib=10, historical_10gib_startup_pass_claimed=False,
                        current_restore_count=1, current_source_updates=0, current_support_updates=1,
                        current_gradient_updates=1, target_inference_calls=1, query_count=2, measured_cells=0,
                        scientific_admission=False, original_case_attempts_remaining=0)
        origin.need(all(type(self.pins.get(name)) is type(value) and self.pins[name] == value
                        for name, value in expected.items()), 'exact restoration-only admission required')
        origin.need(output == self.phase_paths['output'] and output.resolve() == output, 'unused direct output required')
        output.mkdir(exist_ok=False)
        self.contract = read_json(RUN / 'origin-contract.json')
        origin.need(self.contract['schema'] == 'cho51_linear_worker_origin_contract_v1', 'fresh origin contract required')
        self.origin_files = {Path(name): value for name, value in self.contract['files'].items()}
        _, self.fixture, inputs = origin.original_inventory()
        self.input_pins = {self.fixture / name: row['sha256'] for name, row in inputs.items()}
        self.input_sizes = {self.fixture / name: row['size_bytes'] for name, row in inputs.items()}
        self.target_paths = frozenset(self.fixture / name for name in (
            'data/processed/cho2017/profile_a/subject_02.npz',
            'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
            'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
            'data/raw/moabb/cho2017/subject_02.mat'))
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
        self.request_identity, self.factory_request_identity, self.claim_identity = None, None, None
        self.factory_request = None
        self.calls, self.denied, self.sensitive_reads = {}, [], {}
        self.model_constructions = self.constructor_dummy_forward_calls = self.lock_checks = 0
        self.classifier_forward_calls = self.backbone_forward_calls = 0
        self.clone_reinitializations, self.clone_reinitialization_details = {}, []
        self.empty_mask_containers, self.numpy_loads = {}, {}
        self.factory_restore_calls = self.factory_restore_returns = self.current_restore_count = 0
        self.git_queries = self.hostname_queries = self.existing_mkdir_refusals = 0
        self.connection = SITE / 'urllib3/util/connection.py'
        self.mne = Path(self.pins['mne_resource_path'])
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong]
        self.api.GetFinalPathNameByHandleW.restype = ctypes.c_ulong
        self.native_binding = self.bind_native()
        self.unit_proof_identities = {Path(path): identity(Path(path)) for path in self.tests_join['bindings']} if self.tests_join else {}
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
                    and admission['guard_policy_schema'] == 'cho51_provenance_numerical_worker_guard_v1'
                    and admission['phase'] == self.phase and admission['expected_numerical_budget'] == self.pins['phase_budgets'][self.phase]
                    and admission['owner_resource_amendment_path'] == self.pins['owner_resource_amendment_path']
                    and admission['owner_resource_amendment_sha256'] == self.pins['owner_resource_amendment_sha256']
                    and len(admission['startup_samples']) == 2 and all(
                        type(row['available_ram_bytes']) is int and row['available_ram_bytes'] >= 4 * 1024**3
                        and type(row['free_disk_bytes']) is int and row['free_disk_bytes'] >= 20 * 1024**3
                        for row in admission['startup_samples']), 'native admission differs from owner-amended fixed scope')
        self.root_admission_identity = identity(self.phase_paths['admission'])
        dispatch = read_json(self.phase_paths['dispatch'])
        root_admission = read_json(self.phase_paths['admission'], dispatch['admission_sha256'])
        required = dict(schema='cho51_provenance_numerical_worker_admission_v1', pins_sha256=self.pins_sha256,
                        source_review_sha256=self.pins['source_review_sha256'], accepted=True,
                        scientific_admission=False, max_job_seconds=600, process_mib=4096, job_mib=5120,
                        startup_ram_gib=4, active_ram_gib=4, disk_gib=20,
                        owner_resource_amendment_path=self.pins['owner_resource_amendment_path'],
                        owner_resource_amendment_sha256=self.pins['owner_resource_amendment_sha256'])
        origin.need(all(type(root_admission.get(name)) is type(value) and root_admission[name] == value
                        for name, value in required.items()), 'fresh exact root admission differs')
        origin.need(root_admission.get('phase') == self.phase
                    and root_admission.get('expected_numerical_budget') == self.pins['phase_budgets'][self.phase],
                    'exact admitted phase and budget required')
        if self.phase == 'integration':
            self.tests_join = origin.verify_tests_join(root_admission, self.pins, self.pins_sha256)
        self.peer_release_path = Path(root_admission['peer_release_path'])
        self.peer_release_identity = identity(self.peer_release_path)
        peer_release = read_json(self.peer_release_path, root_admission['peer_release_sha256'])
        required_peer = dict(schema='pro2_pro3_compute_release_v1', scope=self.phase_paths['scope'],
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
        if hasattr(self, 'unit_proof_identities'):
            for path, expected_identity in self.unit_proof_identities.items():
                origin.need(identity(path) == expected_identity, 'externally accepted unit proof identity changed')
        if hasattr(self, 'root_admission_identity'):
            origin.need(identity(self.phase_paths['admission']) == self.root_admission_identity
                        and identity(self.peer_release_path) == self.peer_release_identity
                        and datetime.now(timezone.utc) <= self.peer_window_end, 'live peer release or root admission changed or expired')
        origin.need(digest(self.pins_path) == self.pins_sha256, 'fresh pins changed')
        for name, value in self.pins['files'].items():
            origin.need(digest(ROOT / name) == value, 'current or historical source/context pin changed: ' + name)
        for group, count in (('runtime', 5), ('runtime_modules', 18), ('supporting_runtime_sources', 4)):
            origin.need(len(self.pins[group]) == count, 'exact admitted runtime inventory required')
            for path, value in self.pins[group].items():
                origin.need(digest(path) == value, 'fresh runtime changed: ' + path)
        expected_clone_sources = {
            str(SITE / 'einops/layers/__init__.py'): '8e28f0118d3b62bdeb071f0de73c19fb9a9f6e5f8a5f605c4432bc3491436960',
            str(SITE / 'einops/layers/torch.py'): '055f8fce3a228c653d44679ad47085b88331e3271c89ccfbebb3348c90c81fa5',
            str(SITE / 'torch/nn/modules/container.py'): 'd8c2b56bfa2204e8c2dc2466549a7b2299a14324c03a1d563e2b32072ced9a0b',
            str(Path(sys.base_prefix) / 'Lib/copy.py'): 'cbd25547933176fcf6bb05c2adc9f4796d15ac20b9b82dcf890daea7203daeab'}
        origin.need(self.pins['supporting_runtime_sources'] == expected_clone_sources,
                    'exact qualified four clone and container implementation sources required')
        origin.need(self.pins['phase_scopes'] == {phase: origin.phase_paths(phase)['scope'] for phase in origin.PHASES}
                    and self.pins['phase_budgets'] == dict(tests=origin.ZERO_BUDGET, integration=origin.FULL_BUDGET)
                    and self.pins['phase_outputs'] == {phase: str(origin.phase_paths(phase)['output']) for phase in origin.PHASES},
                    'one common source pin must bind only the two disjoint phase slots')
        origin.need(len(self.pins['reviewed_files']) == 13, 'exact thirteen current sources required')
        review = read_json(RUN / 'source-review.json')
        origin.need(review['source_only'] is True and review['remaining_actionable_findings'] == []
                    and review['files'] == self.pins['reviewed_files'], 'settled source review changed')
        amendment_path = Path(self.pins['owner_resource_amendment_path'])
        origin.need(amendment_path == RUN / 'owner-resource-amendment.json', 'exact direct-owner amendment path required')
        amendment = read_json(amendment_path, self.pins['owner_resource_amendment_sha256'])
        expected_amendment = dict(schema='cho51_provenance_numerical_worker_owner_resource_amendment_v1',
                                 scope='cho51_provenance_numerical_worker_20261025_v5', previous_startup_ram_gib=10,
                                 owner_instruction_exact='use the available ram now!',
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
            allowed_cwd = cwd is not None and (path_of(cwd) in {ROOT, self.output / 'fixture', self.fixture}
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
            unit_proofs = getattr(self, 'unit_proof_identities', {})
            protected_unit = (path.is_relative_to(RUN / 't1')
                              or path.is_relative_to(ROOT / 'evidence/cho51-provenance-numerical-worker-tests-20261025-v5')
                              or path in {RUN / 'closeout-tests-result.json', RUN / 'tests-final-review.json', RUN / 'lease-closeout_tests_001.json',
                                          RUN / 'admission_tests.json', RUN / 'dispatch_tests_001.json', RUN / 'dispatch_result_tests_001.json',
                                          RUN / 'peer-release-authenticated_tests.json'}
                              or self.tests_join is not None and path.parent == Path(self.tests_join['summary']['native']['native_directory']))
            if self.phase == 'integration' and protected_unit:
                origin_reader = any(stack_has(name, RUN / 'origin.py')
                                    for name in ('digest', 'document', 'verify_tests_join'))
                stability_reader = stack_has('verify_pins', RUN / 'runtime.py') and stack_has('identity', RUN / 'runtime.py')
                if path not in unit_proofs or not (origin_reader or stability_reader):
                    self.refuse('unbound_accepted_unit_proof_read', path)
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
            role_hash = (path in self.origin_files and stack_has('_read_origin_file', TRANSACTION)
                         and any(stack_has('_origin_assets', source) for source in
                                 (HISTORICAL_WORKER / 'worker_route.py', TRANSACTION)))
            baseline = (path == self.baseline and self.active and self.lock_live()
                        and stack_has('restore', FACTORY) and any(stack_has(name, ROOT / 'evaluation/phase2_cho_source_restore.py')
                        for name in ('_new_model', 'prepare_cho_source_restore', '_check_labram_baseline')))
            selected = (path == self.selected and self.active and self.lock_live() and stack_has('restore', FACTORY))
            selected_metadata = path == self.selected and self.lock_live() and stack_has('authenticate', FACTORY)
            target = (path in self.target_paths and self.active and self.lock_live()
                      and stack_has('run_target_route', CANDIDATE / 'target_route.py')
                      and stack_has('load_cho_profile_b_episode', ROOT / 'evaluation/phase2_profile_binding.py'))
            if test_read or history_hash or role_hash or baseline or selected or selected_metadata or target:
                purpose = ('test_metadata' if test_read else 'history_hash' if history_hash else 'baseline_restore'
                           if baseline else 'role_hash' if role_hash else 'selected_metadata_hash' if selected_metadata
                           else 'target_episode_loader' if target else 'selected_restore')
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
        if self.locked is None or self.binding is None:
            return False
        if (not stack_has('__call__', WORKER / 'backend.py')
                or not stack_has('run_worker_case', WORKER / 'numerical_worker.py')):
            return False
        from docs.phase2.cho51_provenance_numerical_worker_v2 import numerical_worker as Worker
        from evaluation.phase2_runner import LockedCase
        origin.need(type(self.locked) is LockedCase and type(self.factory_request) is Worker.Factory.RestoreRequest,
                    'actual canonical lock and typed factory request required')
        self.locked._require_active()
        request_path, claim_path = Path(self.binding['request_path']), Path(self.binding['claim_path'])
        origin.need(identity(request_path) == self.request_identity and identity(claim_path) == self.claim_identity
                    and identity(Path(self.factory_request.workspace) / 'request.json') == self.factory_request_identity
                    and self.factory_request.sha256 == self.binding['factory_request_sha256'],
                    'live current worker/factory requests or claim changed')
        self.lock_checks += 1
        return True

    def locked_worker(self):
        return self.lock_live()

    def test_stack(self):
        approved = {WORKER / 'test_integration.py', LEGACY_WORKER / 'test_numerical_worker.py',
                    HISTORICAL_WORKER / 'test_worker_route.py'}
        frame = sys._getframe(1)
        while frame:
            if path_of(frame.f_code.co_filename) in approved:
                return True
            frame = frame.f_back
        return False

    def numerical_allowed(self, name, module=None):
        if (self.phase != 'integration' or not self.active or not stack_has('run_target_route', CANDIDATE / 'target_route.py')
                or not self.lock_live()):
            self.refuse('numerics_outside_locked_composition', name)
        approved = {'model_module_init', 'module_load_state_dict', 'safetensors_load', 'optimizer_init',
                    'sgd_step', 'tensor_backward', 'autograd_backward'}
        if name not in approved:
            self.refuse('unbound_numerical_operation', name)
        if name == 'model_module_init' and not stack_has('_new_model', ROOT / 'evaluation/phase2_cho_source_restore.py'):
            import torch
            if (type(module) is not torch.nn.CrossEntropyLoss
                    or not stack_has('adapt_labram_tuning_support', ROOT / 'adaptation/labram_tuning.py')):
                self.refuse('unbound_model_constructor', name)
        if name in {'optimizer_init', 'sgd_step', 'tensor_backward', 'autograd_backward'} and not stack_has(
                'adapt_labram_tuning_support', ROOT / 'adaptation/labram_tuning.py'):
            self.refuse('source_fitting_or_unbound_training', name)
        self.calls[name] = self.calls.get(name, 0) + 1
        limits = dict(module_load_state_dict=2, safetensors_load=2, optimizer_init=1,
                      sgd_step=1, tensor_backward=1, autograd_backward=1)
        if name in limits and self.calls[name] > limits[name]:
            self.refuse('numerical_budget_exceeded', name)
        pause_check()

    def observer_snapshot(self):
        return dict(numerical_calls=dict(self.calls), model_constructions=self.model_constructions,
                    constructor_dummy_forward_calls=self.constructor_dummy_forward_calls,
                    classifier_forward_calls=self.classifier_forward_calls, backbone_forward_calls=self.backbone_forward_calls,
                    profile_a_loads=sum(count for name, count in self.numpy_loads.items() if Path(name).parent.name == 'profile_a'),
                    profile_b_loads=sum(count for name, count in self.numpy_loads.items() if Path(name).parent.name == 'profile_b_60hz_v1'),
                    npz_loads=sum(self.numpy_loads.values()), clone_reinitializations=sum(self.clone_reinitializations.values()),
                    empty_mask_containers=sum(self.empty_mask_containers.values()), factory_restore_calls=self.factory_restore_calls,
                    factory_restore_returns=self.factory_restore_returns)

    def install_torch_guards(self):
        import torch
        torch.set_num_threads(1);torch.set_num_interop_threads(1)
        def forbidden(*arguments,**keywords):self.refuse('pickle_serialization_remote_or_unbound_numerics',None)
        torch.load=torch.serialization.load=torch.jit.load=torch.hub.load=forbidden
        torch.save=torch.serialization.save=forbidden;torch.autograd.grad=forbidden
        original_init=torch.nn.Module.__init__
        from einops.layers.torch import Rearrange
        einops_mixin=SITE/'einops/layers/__init__.py'
        copy_source=Path(sys.base_prefix)/'Lib/copy.py'
        patterns=frozenset({'Batch chs npat spatch -> Batch () (chs npat) spatch',
                           'Batch C NA T -> Batch NA (T C)'})
        container_source=SITE/'torch/nn/modules/container.py'
        def empty_mask_container(module):
            if (not self.active or not stack_has('run_target_route',CANDIDATE/'target_route.py') or not self.locked_worker()
                    or type(module) is not torch.nn.ModuleList or module.__dict__!={}):
                self.refuse('empty_container_outside_exact_target_mask',None)
            init_frame=getitem_frame=depth_frame=phase_frame=None;phase=None
            frame=sys._getframe(1)
            while frame:
                name=frame.f_code.co_name;path=path_of(frame.f_code.co_filename)
                if path==container_source:
                    if name=='__init__' and frame.f_locals.get('self') is module:init_frame=frame
                    elif name=='__getitem__':getitem_frame=frame
                if path==ROOT/'encoder/labram.py' and name=='configure_trainable_depth':depth_frame=frame
                if path==ROOT/'adaptation/labram_manifest.py' and name=='__init__':
                    runner_type=getattr(sys.modules.get('adaptation.labram_manifest'),'LaBraMTuningManifestRunner',None)
                    if runner_type is not None and type(frame.f_locals.get('self')) is runner_type:
                        if phase is not None:self.refuse('nested_empty_container_scope',None)
                        phase,phase_frame='runner_owned_source',frame
                if path==ROOT/'adaptation/labram_tuning.py' and name=='adapt_labram_tuning_support':
                    if phase is not None:self.refuse('nested_empty_container_scope',None)
                    phase,phase_frame='support_adapted_model',frame
                frame=frame.f_back
            if None in (init_frame,getitem_frame,depth_frame,phase_frame):
                self.refuse('unbound_empty_mask_container',None)
            values=init_frame.f_locals.get('modules');idx=getitem_frame.f_locals.get('idx')
            blocks=getitem_frame.f_locals.get('self');local=depth_frame.f_locals;model=local.get('model')
            from encoder.labram import LaBraMClassifier
            from braindecode.models.labram import _WindowsAttentionBlock
            from evaluation.labram_parity import state_digest
            if (type(values) is not list or values!=[] or type(idx) is not slice
                    or (idx.start,idx.stop,idx.step)!=(12,None,None) or type(blocks) is not torch.nn.ModuleList
                    or len(blocks)!=12 or tuple(blocks._modules)!=tuple(str(block_index) for block_index in range(12))
                    or any(type(block) is not _WindowsAttentionBlock for block in blocks)
                    or local.get('blocks') is not blocks or type(local.get('depth')) is not int or local['depth']!=0
                    or type(local.get('selected')) is not int or local['selected']!=0
                    or local.get('include_non_blocks') is not False or type(model) is not LaBraMClassifier
                    or model.backbone.blocks is not blocks or state_digest(model)!=
                       '8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'
                    or not stack_has('configure_labram_tuning',ROOT/'adaptation/labram_tuning.py')):
                self.refuse('empty_mask_container_source_or_slice',None)
            expected_model=phase_frame.f_locals.get('owned' if phase=='runner_owned_source' else 'model')
            if expected_model is not model or phase in self.empty_mask_containers:
                self.refuse('empty_mask_container_scope_budget',None)
            pause_check();original_init(module)
            if (module._parameters!={} or module._buffers!={} or module._modules!={}
                    or tuple(module.parameters())!=() or tuple(module.buffers())!=() or len(module)!=0):
                self.refuse('empty_mask_container_acquired_state',None)
            self.empty_mask_containers[phase]=1
        def clone_reinitialization(module):
            if not self.active or not stack_has('run_target_route',CANDIDATE/'target_route.py') or not self.locked_worker():
                self.refuse('parameterless_clone_outside_route',None)
            init_frame=setstate_frame=reconstruct_frame=phase_frame=None
            phase=None;frames=[];frame=sys._getframe(1)
            while frame:
                frames.append(frame)
                name=frame.f_code.co_name;path=path_of(frame.f_code.co_filename)
                if path==einops_mixin and frame.f_locals.get('self') is module:
                    if name=='__init__':init_frame=frame
                    elif name=='__setstate__':setstate_frame=frame
                if path==copy_source and name=='_reconstruct' and frame.f_locals.get('y') is module:
                    reconstruct_frame=frame
                if path==ROOT/'adaptation/labram_manifest.py' and name=='__init__':
                    runner_module=sys.modules.get('adaptation.labram_manifest')
                    runner_type=getattr(runner_module,'LaBraMTuningManifestRunner',None)
                    if runner_type is not None and type(frame.f_locals.get('self')) is runner_type:
                        if phase is not None:self.refuse('nested_clone_scopes',None)
                        phase,phase_frame='runner_owned_source',frame
                if path==ROOT/'adaptation/labram_tuning.py' and name=='adapt_labram_tuning_support':
                    if phase is not None:self.refuse('nested_clone_scopes',None)
                    phase,phase_frame='support_adapted_model',frame
                frame=frame.f_back
            if (type(module) is not Rearrange or init_frame is None or setstate_frame is None
                    or reconstruct_frame is None or phase_frame is None or module.__dict__!={}):
                self.refuse('unbound_parameterless_reinitialization',None)
            state=setstate_frame.f_locals.get('state')
            pattern=init_frame.f_locals.get('pattern');axes=init_frame.f_locals.get('axes_lengths')
            old=reconstruct_frame.f_locals.get('x')
            source=phase_frame.f_locals.get('source_template' if phase=='runner_owned_source' else 'source_model')
            from encoder.labram import LaBraMClassifier
            from evaluation.labram_parity import state_digest
            if (pattern not in patterns or type(axes) is not dict or axes!={}
                    or type(state) is not dict or state!={'pattern':pattern,'axes_lengths':{}}
                    or reconstruct_frame.f_locals.get('state')!=state
                    or reconstruct_frame.f_locals.get('deep') is not True or type(old) is not Rearrange
                    or old.pattern!=pattern or old.axes_lengths!={} or old._axes_lengths!=()
                    or old._parameters!={} or old._buffers!={} or old._modules!={}
                    or tuple(old.parameters())!=() or tuple(old.buffers())!=() or old.training is not False
                    or type(source) is not LaBraMClassifier or state_digest(source)!=
                       '8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'
                    or not any(old is child for child in source.modules())
                    or not any(frame_item.f_code.co_name=='deepcopy' and path_of(frame_item.f_code.co_filename)==copy_source
                        and frame_item.f_locals.get('x') is source for frame_item in frames)):
                self.refuse('parameterless_clone_pattern_state_or_source',None)
            key=phase+'|'+pattern
            if key in self.clone_reinitializations:self.refuse('parameterless_clone_reinitialization_budget',key)
            pause_check()
            original_init(module)
            if (module._parameters!={} or module._buffers!={} or module._modules!={}
                    or tuple(module.parameters())!=() or tuple(module.buffers())!=()):
                self.refuse('parameterless_clone_acquired_tensor_state',None)
            self.clone_reinitializations[key]=1
            self.clone_reinitialization_details.append({'scope':phase,'class':'einops.layers.torch.Rearrange',
                'pattern':pattern,'axes_lengths':{},'parameters':0,'buffers':0,'child_modules':0,
                'original_layer_in_exact_source':True,'source_state_sha256':
                '8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'})
        @functools.wraps(original_init)
        def module_init(module,*arguments,**keywords):
            cloning=(type(module) is Rearrange and stack_has('__setstate__',einops_mixin))
            if cloning:
                if arguments or keywords:self.refuse('parameterless_clone_init_arguments',None)
                return clone_reinitialization(module)
            if (type(module) is torch.nn.ModuleList and stack_has('__getitem__',container_source)
                    and not stack_has('_new_model',ROOT/'evaluation/phase2_cho_source_restore.py')):
                if arguments or keywords:self.refuse('empty_mask_container_init_arguments',None)
                return empty_mask_container(module)
            self.numerical_allowed('model_module_init',module)
            if type(module).__name__=='Labram':
                self.model_constructions+=1
                if self.model_constructions>1:self.refuse('fresh_full_model_constructor_budget',None)
            return original_init(module,*arguments,**keywords)
        torch.nn.Module.__init__=module_init
        original_state=torch.nn.Module.load_state_dict
        def strict_load(model,state,*arguments,**keywords):
            strict=arguments[0] if arguments else keywords.get('strict',True);assign=arguments[1] if len(arguments)>1 else keywords.get('assign',False)
            if strict is not True or assign is not False or len(arguments)>2 or not stack_has('restore',FACTORY):
                self.refuse('unbound_nonstrict_state_load',None)
            self.numerical_allowed('module_load_state_dict');return original_state(model,state,*arguments,**keywords)
        torch.nn.Module.load_state_dict=strict_load
        original_call=torch.nn.Module._call_impl
        def model_call(module,*arguments,**keywords):
            if self.active and stack_has('run_target_route',CANDIDATE/'target_route.py') and self.locked_worker():
                if stack_has('_new_model',ROOT/'evaluation/phase2_cho_source_restore.py'):
                    frame=sys._getframe(1);constructor=dummy=None
                    while frame:
                        if frame.f_code.co_name=='__init__' and path_of(frame.f_code.co_filename)==SITE/'braindecode/models/labram.py':
                            constructor,dummy=frame.f_locals.get('self'),frame.f_locals.get('dummy');break
                        frame=frame.f_back
                    if (constructor is None or not hasattr(constructor,'patch_embed')
                            or not any(module is member for member in constructor.patch_embed.modules())
                            or torch.is_grad_enabled() or not isinstance(dummy,torch.Tensor)
                            or tuple(dummy.shape)!=(1,int(constructor.n_chans),3000)
                            or dummy.device.type!='cpu' or dummy.dtype!=torch.float32 or dummy.requires_grad
                            or torch.count_nonzero(dummy).item()!=0):self.refuse('unbound_constructor_forward',type(module).__name__)
                    if module is constructor.patch_embed:self.constructor_dummy_forward_calls+=1
                    return original_call(module,*arguments,**keywords)
                support=stack_has('adapt_labram_tuning_support',ROOT/'adaptation/labram_tuning.py')
                query=stack_has('_predict',ROOT/'adaptation/labram_manifest.py')
                if support or query:
                    pause_check()
                    if type(module).__name__=='LaBraMClassifier':
                        expected=(10,64,800) if support else (2,64,800)
                        if (not arguments or not isinstance(arguments[0],torch.Tensor) or tuple(arguments[0].shape)!=expected
                                or any(part.training for part in module.modules())
                                or (not support and (torch.is_grad_enabled() or not torch.is_inference_mode_enabled()))):
                            self.refuse('target_classifier_shape_or_mode',None)
                        self.classifier_forward_calls+=1
                        if self.classifier_forward_calls>2:self.refuse('target_classifier_budget',None)
                    if type(module).__name__=='Labram':self.backbone_forward_calls+=1
                    return original_call(module,*arguments,**keywords)
            self.refuse('unbound_model_forward',type(module).__name__)
        torch.nn.Module._call_impl=model_call
        original_optimizer=torch.optim.Optimizer.__init__
        @functools.wraps(original_optimizer)
        def sgd_only(optimizer,parameters,defaults):
            self.numerical_allowed('optimizer_init')
            if type(optimizer) is not torch.optim.SGD or defaults.get('momentum',0)!=0 or defaults.get('lr')!=0.001:
                self.refuse('optimizer_policy',None)
            return original_optimizer(optimizer,parameters,defaults)
        torch.optim.Optimizer.__init__=sgd_only
        def guarded(name,original):
            @functools.wraps(original)
            def call(*arguments,**keywords):self.numerical_allowed(name);return original(*arguments,**keywords)
            return call
        torch.optim.SGD.step=guarded('sgd_step',torch.optim.SGD.step)
        torch.Tensor.backward=guarded('tensor_backward',torch.Tensor.backward)
        torch.autograd.backward=guarded('autograd_backward',torch.autograd.backward)
        import safetensors
        import safetensors.torch
        original_load=safetensors.torch.load;original_deserialize=safetensors.torch.deserialize
        def valid(raw):
            if type(raw) is not bytes:return False
            sha=hashlib.sha256(raw).hexdigest()
            return ((len(raw)==23299672 and sha=='53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
                     and stack_has('_new_model',ROOT/'evaluation/phase2_cho_source_restore.py'))
                or (len(raw)==23294624 and sha=='3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048'
                    and stack_has('restore',FACTORY)))
        def load_checked(raw):
            self.numerical_allowed('safetensors_load')
            if not valid(raw):self.refuse('unbound_safe_tensor_decode',None)
            return original_load(raw)
        def deserialize_checked(raw):
            if not stack_has('load_checked',RUN/'runtime.py') or not valid(raw):self.refuse('unbound_low_level_decode',None)
            return original_deserialize(raw)
        for name in ('serialize','serialize_file','deserialize','safe_open'):setattr(safetensors,name,forbidden)
        for name in ('save','save_file','save_model','load_file','load_model','safe_open','serialize','serialize_file'):
            setattr(safetensors.torch,name,forbidden)
        safetensors.torch.load=load_checked;safetensors.torch.deserialize=deserialize_checked
        import numpy as np
        original_numpy_load=np.load
        @functools.wraps(original_numpy_load)
        def numpy_load(path,*arguments,**keywords):
            actual=path_of(path) if isinstance(path,(str,bytes,os.PathLike)) else None
            canonical_binding=stack_has('load_cho_profile_b_episode',ROOT/'evaluation/phase2_profile_binding.py')
            if type(path) is io.BytesIO:
                frame=sys._getframe(1);bound=None
                while frame:
                    if frame.f_code.co_name=='_read_artifact' and path_of(frame.f_code.co_filename)==ROOT/'evaluation/phase2_profile_binding.py':
                        bound=frame.f_locals;break
                    frame=frame.f_back
                if bound is not None and bound.get('source') is path and isinstance(bound.get('path'),Path):
                    actual=bound['path']
                    buffer=path.getbuffer()
                    try:
                        if (actual not in self.input_pins or actual not in self.target_paths
                                or actual.suffix!='.npz' or path.tell()!=0
                                or bound.get('expected_sha256')!=self.input_pins[actual]
                                or len(buffer)!=self.input_sizes[actual] or len(buffer)>16*1024**2
                                or hashlib.sha256(buffer).hexdigest()!=self.input_pins[actual]):
                            self.refuse('unbound_numpy_artifact_buffer',actual)
                    finally:buffer.release()
                else:self.refuse('numpy_buffer_outside_canonical_reader',None)
            elif not stack_has('read_catalog',ROOT/'scripts/audit_phase2_protocol.py'):
                self.refuse('numpy_path_outside_canonical_catalogue',actual)
            if (not self.active or not stack_has('run_target_route',CANDIDATE/'target_route.py') or not self.locked_worker()
                    or not canonical_binding or actual not in self.target_paths or actual.suffix!='.npz'
                    or arguments or keywords.get('allow_pickle') is not False or keywords.get('mmap_mode') is not None):
                self.refuse('unbound_numpy_signal_decode',actual)
            row=self.numpy_loads.setdefault(str(actual),0)+1;self.numpy_loads[str(actual)]=row
            limit=4 if actual.parent.name=='profile_a' else 2
            if row>limit:self.refuse('target_numpy_decode_budget',actual)
            pause_check();return original_numpy_load(path,*arguments,**keywords)
        np.load=numpy_load
        for name in ('save','savez','savez_compressed','fromfile','loadtxt','genfromtxt'):setattr(np,name,forbidden)
        from braindecode.models import EEGNet,Labram
        EEGNet.from_pretrained=Labram.from_pretrained=classmethod(forbidden)
        from huggingface_hub import PyTorchModelHubMixin
        PyTorchModelHubMixin.from_pretrained=classmethod(forbidden)
        import data.runtime as scientific_runtime
        original_runtime=scientific_runtime.configure_scientific_runtime
        scientific_runtime.configure_scientific_runtime=lambda project_root=self.output:original_runtime(self.output)
        from evaluation.phase2_runner import CaseRecorder, LockedCase
        original_recorder = CaseRecorder.__init__
        def isolated_recorder(recorder, root, *, output_root=None):
            actual = Path(root).resolve()
            destination = Path(output_root).resolve() if output_root is not None else actual / 'runs/phase2/recorder'
            production = actual == self.output / 'fixture' and destination == actual / 'runs/phase2/lifecycle'
            isolated_test = (self.test_stack() and actual.is_relative_to(self.output / 't')
                             and destination.is_relative_to(self.output / 't'))
            if self.active or not (production or isolated_test):
                self.refuse('shared_recorder_constructor', root)
            return original_recorder(recorder, root, output_root=output_root)
        CaseRecorder.__init__ = isolated_recorder
        CaseRecorder.record_cell = CaseRecorder._record_cell_locked = forbidden
        from docs.phase2.cho51_provenance_restore_v1 import factory as Factory
        original_restore = Factory.ProvenanceRestoreFactory.restore
        original_code = original_restore.__code__
        origin.need(path_of(original_code.co_filename) == FACTORY and original_code.co_name == 'restore',
                    'exact frozen factory restoration implementation required')
        def observed_factory_restore(instance, *arguments, **keywords):
            if (not self.active or not self.lock_live() or arguments
                    or not stack_has('restore_adapter', WORKER / 'backend.py')
                    or not stack_has('run_target_route', CANDIDATE / 'target_route.py')
                    or type(instance) is not Factory.ProvenanceRestoreFactory
                    or instance.request != self.factory_request
                    or instance.request_path != Path(self.factory_request.workspace) / 'request.json'
                    or instance.request_file_sha256 != self.factory_request.sha256
                    or getattr(instance.assert_live_lock, '__self__', None) is not self.locked
                    or getattr(instance.assert_live_lock, '__func__', None) is not LockedCase._require_active
                    or original_restore.__code__ is not original_code
                    or digest(FACTORY) != self.pins['files'][FACTORY.relative_to(ROOT).as_posix()]):
                self.refuse('unbound_or_substituted_factory_restore', None)
            self.factory_restore_calls += 1
            if self.factory_restore_calls != 1:
                self.refuse('factory_restore_entry_budget', None)
            restored = original_restore(instance, **keywords)
            if (type(restored) is not Factory.RestoredSource or restored.adapter._model is not restored.model
                    or restored.witness.get('request_sha256') != self.factory_request.sha256
                    or not self.lock_live()):
                self.refuse('unbound_factory_delivery', None)
            self.factory_restore_returns += 1
            self.current_restore_count = self.factory_restore_returns
            return restored
        Factory.ProvenanceRestoreFactory.restore = observed_factory_restore
        return torch

    def finish(self, result):
        import torch
        from tools.migration.common import source_check
        from docs.phase2.cho51_provenance_numerical_worker_v2 import numerical_worker as Worker
        self.verify_pins()
        origin.need(source_check(ROOT) == CANONICAL and torch.get_num_threads() == torch.get_num_interop_threads() == 1
                    and os.environ.get('CUDA_VISIBLE_DEVICES') == '' and not self.active, 'source or confinement changed')
        expected_probe = dict(event='socket.__new__', classification='blocked_optional_ipv6_import_probe',
                              source_file=str(self.connection),
                              source_sha256=self.pins['files'][self.connection.relative_to(ROOT).as_posix()])
        origin.need(self.denied in ([], [expected_probe]), 'unexpected audit denial')
        if result['passed'] and self.phase == 'tests':
            Worker.validate_observer(self.observer_snapshot(), zero=True)
            origin.need(self.calls == {} and self.clone_reinitializations == {} and self.empty_mask_containers == {}
                        and self.numpy_loads == {} and self.lock_checks == 0 and self.locked is None,
                        'unit phase must perform no actual numerical transaction')
        if result['passed'] and self.phase == 'integration':
            Worker.validate_observer(self.observer_snapshot())
            origin.need(self.lock_checks > 0, 'actual live-lock observations required')
            expected_clones = {phase + '|' + pattern: 1
                for phase in ('runner_owned_source', 'support_adapted_model')
                for pattern in ('Batch chs npat spatch -> Batch () (chs npat) spatch', 'Batch C NA T -> Batch NA (T C)')}
            origin.need(self.clone_reinitializations == expected_clones and len(self.clone_reinitialization_details) == 4
                        and self.empty_mask_containers == {'runner_owned_source': 1, 'support_adapted_model': 1},
                        'exact qualified parameterless clones and empty masks required')
        loaded = {}
        for module in tuple(sys.modules.values()):
            name = getattr(module, '__file__', None)
            if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(self.output):
                loaded[str(Path(name).resolve())] = digest(Path(name).resolve())
        qualification = dict(schema='cho51_provenance_numerical_worker_qualification_v1', phase=self.phase, passed=result['passed'],
                             result=result, observed_utc=datetime.now(timezone.utc).isoformat(),
                             elapsed_seconds=time.monotonic() - self.started, pins_sha256=self.pins_sha256,
                             canonical_files=432, canonical_source_sha256=CANONICAL,
                             independent_observer=self.observer_snapshot(), numerical_calls=dict(self.calls),
                             lock_checks=self.lock_checks, sensitive_reads=self.sensitive_reads,
                             clone_reinitializations=self.clone_reinitializations,
                             clone_reinitialization_details=self.clone_reinitialization_details,
                             empty_mask_containers=self.empty_mask_containers, numpy_loads=self.numpy_loads,
                             denied_operations=self.denied, unexpected_denials=0,
                             observed_loaded_module_hashes=loaded, loaded_module_files=len(loaded),
                             source_pins_rechecked=len(self.pins['files']), runtime_pins_rechecked=5,
                             runtime_module_pins_rechecked=18, supporting_runtime_sources_rechecked=4,
                             torch_threads=1, torch_interop_threads=1, gpu_hidden=True,
                             native_binding=self.native_binding, current_counter_ledger=result.get('current_counter_ledger'),
                             measured_cells=0, scientific_admission=False,
                             native_closeout_status='pending_external_post_job')
        write_json(self.output / 'qualification.json', qualification)
        for path, value in loaded.items():
            origin.need(digest(path) == value, 'loaded module changed during qualification')
        return qualification






