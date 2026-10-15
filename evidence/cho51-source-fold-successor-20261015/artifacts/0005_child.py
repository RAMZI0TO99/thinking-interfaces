"""One finite public source-selector fold over an isolated all52 synthetic cohort."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import msvcrt
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent
SITE = ROOT / '.venv/Lib/site-packages'
PROBE_PATH = ROOT / 'docs/phase2/cho51_source_fold_probe_v1/probe.py'
FIXTURE_PATH = ROOT / 'docs/phase2/cho51_source_fold_probe_v1/fixture.py'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
METHODS = ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
PAUSES = tuple(Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001' /
    'coordination/PRO2_REQUEST_PRO3_PAUSE.json'
    for day in ('20261007', '20261012', '20261013', '20261015'))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins', type=Path, required=True)
parser.add_argument('--expect-pins', required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--method', choices=METHODS, required=True)
args = parser.parse_args()


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


if (args.pins.resolve(strict=True) != RUN / 'pins.json'
        or re.fullmatch('[a-f0-9]{64}', args.expect_pins) is None
        or digest(args.pins) != args.expect_pins):
    raise ValueError('independently supplied exact fresh source-fold pins required')
pins = json.loads(args.pins.read_bytes())
expected_config = {
    'schema': 'cho51_source_fold_fresh_pins_v1',
    'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
    'predecessor_files': 574,
    'predecessor_pins_sha256': '20a808c269e6de2c6fd7355749438c80f7198e48946753d0db63308a1a72d3a1',
    'seconds_per_method': 600, 'process_mib': 4096, 'job_mib': 5120,
    'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
    'threads': 1, 'gpu_hidden': True, 'random_initialization_only': True,
    'gradient_steps_per_method': 51, 'source_gradient_updates': 50,
    'support_gradient_updates': 1, 'source_subject_count': 52,
    'training_subject_count': 50, 'validation_subject': 'subject_01',
    'target_subject': 'subject_02', 'channels': 64,
    'eegnet_samples': 512, 'labram_samples': 800, 'labram_layers': 12,
    'source_fold_only': True, 'full_5253_gradient_selection_executed': False,
    'whole_numerical_worker_verified': False,
    'actual_study_inputs_or_pretrained_weights_permitted': False,
    'scientific_admission': False, 'original_case_attempts_remaining': 0,
}
if (type(pins) is not dict or any(type(pins.get(key)) is not type(want) or pins[key] != want
        for key, want in expected_config.items())
        or pins.get('methods') != list(METHODS)
        or len(pins.get('files', {})) <= 574 or len(pins.get('runtime', {})) != 5):
    raise ValueError('exact reviewed synthetic fold scope and finite limits required')
OUT = args.output.resolve()
if OUT != RUN / ('output_' + args.method + '_001') or args.output.absolute() != OUT:
    raise ValueError('direct unused method-specific owned output required')
OUT.mkdir(exist_ok=False)


def verify_pins():
    if digest(args.pins) != args.expect_pins:
        raise ValueError('fresh pins changed during execution')
    for relative, expected in pins['files'].items():
        if digest(ROOT / relative) != expected:
            raise ValueError('source/library pin changed: ' + relative)
    for path, expected in pins['runtime'].items():
        if digest(path) != expected:
            raise ValueError('runtime pin changed: ' + path)
    review_path = Path(pins['source_review_path'])
    review = json.loads(review_path.read_bytes())
    if (review_path != RUN / 'source-review.json'
            or digest(review_path) != pins['source_review_sha256']
            or review.get('source_only') is not True
            or review.get('remaining_actionable_findings') != []
            or review.get('files') != pins['reviewed_files']
            or any(digest(ROOT / relative) != expected for relative, expected in review['files'].items())):
        raise ValueError('exact independent settled-source review changed')


verify_pins()
directories = {
    'TEMP': 'temp', 'TMP': 'temp', 'TMPDIR': 'temp',
    'MPLCONFIGDIR': 'mpl', 'HF_HOME': 'hf', '_MNE_FAKE_HOME_DIR': 'mne-home',
    'HF_HUB_CACHE': 'hf/hub', 'HUGGINGFACE_HUB_CACHE': 'hf/hub',
    'TRANSFORMERS_CACHE': 'hf/transformers', 'TORCH_HOME': 'torch',
    'NUMBA_CACHE_DIR': 'numba', 'JOBLIB_TEMP_FOLDER': 'joblib', 'XDG_CACHE_HOME': 'cache',
}
for folder in sorted(set(directories.values()), key=lambda name: (name.count('/'), name)):
    (OUT / folder).mkdir()
for name, folder in directories.items():
    os.environ[name] = str(OUT / folder)
for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
             'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
    PYTHONDONTWRITEBYTECODE='1', TOKENIZERS_PARALLELISM='false')
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(SITE)]
from tools.migration.common import source_check

if source_check(ROOT) != CANONICAL:
    raise ValueError('canonical source changed before source fold')
MNE_RESOURCE = Path(pins['mne_resource_path'])
CONNECTION = SITE / 'urllib3/util/connection.py'
if (MNE_RESOURCE != SITE / 'mne/data/fsaverage/fsaverage-fiducials.fif'
        or pins.get('mne_resource_bytes') != 260 or MNE_RESOURCE.stat().st_size != 260
        or digest(MNE_RESOURCE) != pins['mne_resource_sha256']
        or pins['mne_resource_sha256'] != '0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'):
    raise ValueError('only exact independently pinned installed MNE metadata is allowed')
git_command = shutil.which('git')
if git_command is None or str(Path(git_command).resolve()) not in pins['runtime']:
    raise ValueError('owned fixture provenance requires pinned installed Git')
GIT_PATH = Path(git_command).resolve()


def pause_check():
    if any(path.exists() for path in PAUSES):
        raise RuntimeError('genuine peer pause requested')


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


file_api = ctypes.WinDLL('kernel32', use_last_error=True)
file_api.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong]
file_api.GetFinalPathNameByHandleW.restype = ctypes.c_ulong


def descriptor_path(descriptor):
    if type(descriptor) is not int:
        return None
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        length = file_api.GetFinalPathNameByHandleW(msvcrt.get_osfhandle(descriptor), buffer, len(buffer), 0)
        return path_of(buffer.value) if 0 < length < len(buffer) else None
    except OSError:
        return None


denied = []
hostname_queries = 0
git_queries = 0
existing_mkdir_refusals = 0
probe_active = False
numerical_calls = {}
protected_inputs = frozenset()
protected_declared = ()
protection_transitions = []
planned_target_check = False
protected_negative_checks = []
protected_fold_read_attempts = []
fixture_read_phases = {}
EXPECTED_IPV6 = {
    'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
    'source_file': str(CONNECTION),
    'source_sha256': pins['files'][CONNECTION.relative_to(ROOT).as_posix()],
}


def refuse(event, detail=None):
    denied.append({'event': event, 'detail': repr(detail)[:500]})
    raise PermissionError('public source-fold child denied: ' + event)


def inside_write(value):
    if not isinstance(value, (str, bytes, os.PathLike)) or not path_of(value).is_relative_to(OUT):
        refuse('outside_or_unbound_output_write', value)


def allow_numerical(name):
    # Every permitted numerical call must descend from the pinned public-fold probe.
    if not probe_active or not stack_has('run_probe', PROBE_PATH):
        refuse('numerical_call_outside_pinned_public_fold', name)
    pause_check()
    numerical_calls[name] = numerical_calls.get(name, 0) + 1


def protected_read(path):
    if path in protected_inputs:
        row = {'event': 'protected_outer_target_read', 'path': str(path),
               'planned_negative_check': planned_target_check}
        if planned_target_check:
            protected_negative_checks.append(row)
        else:
            protected_fold_read_attempts.append(row)
            denied.append(row)
        raise PermissionError('outer target contents excluded from source fold')


def record_fixture_read(path):
    if path.is_relative_to(OUT / 'fixture') and not planned_target_check:
        phase = ('during_fold' if protected_inputs else
                 'after_protection' if protected_declared else 'before_protection')
        counts = fixture_read_phases.setdefault(str(path), {
            'before_protection': 0, 'during_fold': 0, 'after_protection': 0})
        counts[phase] += 1


def spawn(values):
    global git_queries
    executable, arguments, cwd, environment = values
    forms = [[git_command, '--no-optional-locks', *tail] for tail in (
        ['rev-parse', '--verify', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'])]
    executable_matches = ((executable is None and os.name == 'nt') or
        isinstance(executable, (str, bytes, os.PathLike)) and path_of(executable) == GIT_PATH)
    if (any(arguments == command or arguments == subprocess.list2cmdline(command) for command in forms)
            and executable_matches and cwd is not None and path_of(cwd) == OUT / 'fixture'
            and environment is None and stack_has('capture_source', ROOT / 'core/provenance.py')
            and stack_has('run_probe', PROBE_PATH)):
        git_queries += 1
        return
    refuse('subprocess.Popen', values)


def audit(event, values):
    global hostname_queries, existing_mkdir_refusals
    if event == 'socket.gethostname':
        hostname_queries += 1
    elif event.startswith('socket.'):
        if (event == 'socket.__new__' and values[1:] == (socket.AF_INET6, socket.SOCK_STREAM, 0)
                and stack_has('_has_ipv6', CONNECTION)):
            denied.append(dict(EXPECTED_IPV6))
            raise PermissionError('optional IPv6 import probe blocked before socket creation')
        refuse(event, values)
    elif event == 'subprocess.Popen':
        spawn(values)
    elif (event in {'os.system', 'os.startfile', 'os.posix_spawn', 'os.fork', 'os.forkpty', 'pty.spawn'}
            or event.startswith(('os.exec', 'os.spawn'))):
        refuse(event, values)
    elif event == 'open':
        mode = values[1] if isinstance(values[1], str) else ''
        flags = values[2] if isinstance(values[2], int) else 0
        writing = any(char in mode for char in 'wax+') or bool(
            flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if not isinstance(values[0], (str, bytes, os.PathLike)):
            path = descriptor_path(values[0])
            if path is None:
                if writing:
                    refuse('unbound_descriptor_write', values)
                return
        else:
            path = path_of(values[0])
        if writing:
            inside_write(path)
        else:
            protected_read(path)
            record_fixture_read(path)
            if not path.is_relative_to(OUT):
                parts = tuple(part.lower() for part in path.parts)
                data_path = any(parts[index:index + 2] in {
                    ('data', 'raw'), ('data', 'processed'), ('data', 'interim'),
                } for index in range(len(parts) - 1))
                if path == MNE_RESOURCE:
                    return
                if (data_path or 'weights' in parts or 'checkpoints' in parts
                        or path.suffix.lower() in {'.npz', '.npy', '.mat', '.edf', '.gdf', '.fif', '.set', '.pt', '.pth', '.ckpt', '.safetensors'}):
                    if not (path.suffix.lower() == '.pth' and path.is_relative_to(SITE)):
                        refuse('actual_study_array_or_checkpoint_read', path)
    elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace',
                   'os.link', 'os.symlink', 'os.chmod', 'os.utime', 'os.truncate'}:
        count = 2 if event in {'os.rename', 'os.replace', 'os.link', 'os.symlink'} else 1
        for value in values[:count]:
            if (event == 'os.mkdir' and isinstance(value, (str, bytes, os.PathLike))
                    and not path_of(value).is_relative_to(OUT) and path_of(value).is_dir()):
                existing_mkdir_refusals += 1
                raise FileExistsError(17, 'existing shared directory creation refused', os.fsdecode(value))
            inside_write(value)
    elif event == 'os.chdir':
        inside_write(values[0])


def clean_audit():
    if denied != [EXPECTED_IPV6] or protected_fold_read_attempts:
        raise RuntimeError('public source fold observed an unexpected audit denial')


def set_protected_inputs(paths, enabled=True):
    global protected_inputs, protected_declared, planned_target_check
    if not stack_has('run_probe', PROBE_PATH) or type(enabled) is not bool:
        refuse('unbound_protected_input_control', None)
    if type(paths) is not tuple or not paths or any(not isinstance(path, Path) for path in paths):
        raise ValueError('nonempty physical target input path tuple required')
    resolved = tuple(path.resolve(strict=True) for path in paths)
    expected_paths = (
        OUT / 'fixture/data/processed/cho2017/profile_a/subject_02.npz',
        OUT / 'fixture/data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
        OUT / 'fixture/data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
        OUT / 'fixture/data/raw/moabb/cho2017/subject_02.mat',
    )
    if (len(set(resolved)) != len(resolved) or any(not path.is_relative_to(OUT / 'fixture')
            or not path.is_file() or path.stat().st_nlink != 1 for path in resolved)):
        raise ValueError('distinct direct owned physical target inputs required')
    if resolved != expected_paths or tuple(paths) != resolved:
        raise ValueError('exact four direct physical subject02 data/metadata paths required')
    if enabled:
        if protected_inputs or protected_declared:
            raise ValueError('target-input protection is enabled exactly once')
        protected_declared = resolved
        protected_inputs = frozenset(resolved)
        planned_target_check = True
        try:
            for path in resolved[:2]:
                try:
                    with path.open('rb') as stream:
                        stream.read(1)
                except PermissionError:
                    pass
                else:
                    raise RuntimeError('protected target negative read was allowed')
        finally:
            planned_target_check = False
    else:
        if tuple(resolved) != protected_declared or not protected_inputs:
            raise ValueError('only original protected target paths may be released')
        protected_inputs = frozenset()
    protection_transitions.append({'enabled': enabled, 'paths': [str(path) for path in resolved]})


sys.addaudithook(audit)
pause_check()
started = time.monotonic()
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)


def no_checkpoint(*arguments, **keywords):
    refuse('pickle_checkpoint_or_pretrained_load', None)


torch.load = no_checkpoint
torch.serialization.load = no_checkpoint
torch.jit.load = no_checkpoint
torch.hub.load = no_checkpoint


def guarded(name, original):
    def call(*arguments, **keywords):
        allow_numerical(name)
        return original(*arguments, **keywords)
    return call


original_optimizer = torch.optim.Optimizer.__init__


def sgd_only(self, parameters, defaults):
    allow_numerical('optimizer_init')
    if type(self) is not torch.optim.SGD or defaults.get('momentum', 0) != 0:
        refuse('optimizer_outside_momentum_free_sgd', type(self).__name__)
    return original_optimizer(self, parameters, defaults)


torch.nn.Module.__init__ = guarded('model_module_init', torch.nn.Module.__init__)
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

original_runtime = runtime.configure_scientific_runtime


def owned_runtime(project_root=OUT):
    return original_runtime(OUT)


runtime.configure_scientific_runtime = owned_runtime
from braindecode.models import EEGNet, Labram

EEGNet.from_pretrained = classmethod(no_checkpoint)
Labram.from_pretrained = classmethod(no_checkpoint)
from huggingface_hub import PyTorchModelHubMixin

PyTorchModelHubMixin.from_pretrained = classmethod(no_checkpoint)
from docs.phase2.cho51_source_fold_probe_v1 import probe

config_path = Path(pins['model_config_path'])
if (config_path != ROOT / '.cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/0563b6c626e7b40d9a36653b763715db94d945d7/config.json'
        or digest(config_path) != pins['model_config_sha256']
        or config_path.stat().st_size != pins['model_config_bytes']
        or pins['model_config_sha256'] != '813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b'):
    raise ValueError('independently pinned baseline architecture JSON differs')
config = json.loads(config_path.read_bytes())
if type(config) is not dict:
    raise ValueError('baseline architecture configuration must be an object')
pause_check()
clean_audit()
probe_active = True
try:
    result = probe.run_probe(OUT, args.method, config, set_protected_inputs=set_protected_inputs)
finally:
    probe_active = False


def validate_result(value):
    if type(value) is not dict:
        raise ValueError('actual public-fold result object required')
    if numerical_calls.get('tensor_backward') != 51 or numerical_calls.get('sgd_step') != 51:
        raise ValueError('exactly 51 observed backward/SGD updates required')
    if (protected_inputs or len(protection_transitions) != 2
            or [row['enabled'] for row in protection_transitions] != [True, False]
            or len(protected_negative_checks) != 2 or protected_fold_read_attempts):
        raise ValueError('complete protected-target lifecycle and two explicit negative checks required')
    if value.get('method') != args.method or value.get('passed') is not True:
        raise ValueError('exact successful method result required')
    expected = {
        'schema': 'cho51_public_source_fold_probe_v1', 'source_subjects_available': 52,
        'adopted_evaluation_targets': 51, 'adopted_case_plan_count': 1020,
        'outer_target': 'subject_02', 'inner_validation_subject': 'subject_01',
        'diagnostic_folds': 1, 'maximum_gradient_steps': 51,
        'source_gradient_updates': 50, 'support_gradient_updates': 1,
        'actual_gradient_updates': 51, 'full_selection_refused_before_fit': True,
        'required_selection_updates': 5253,
        'full_selection_refusal_reason': 'requested work exceeds the declared gradient-step ceiling',
        'support_trials': 10, 'inner_query_trials': 2,
        'public_complete_selector_verifier_refused': True,
        'public_refusal_reason': 'selection evidence has missing or unexpected fields',
        'refusal_boundary': 'raw_incomplete_diagnostic_payload_schema',
        'all_physical_inputs_rehashed_unchanged': True, 'supplied_template_unchanged': True,
        'fixture_source_context_unchanged': True, 'torch_numpy_python_rng_unchanged': True,
        'finite_losses_gradients_parameters': True, 'canonical_source_exclusion_verified': True,
        'actual_public_run_fold': True, 'complete': False, 'selected_candidate': None,
        'full_selector_verified': False, 'full_worker_verified': False,
        'publication_performed': False, 'recorder_used': False, 'measured_cells': 0,
        'synthetic': True, 'actual_study_data_loaded': False, 'pretrained_weights_loaded': False,
        'engineering_only': True, 'scientific_admission': False,
        'original_case_attempts_remaining': 0, 'input_file_count': 213,
    }
    if any(type(value.get(key)) is not type(want) or value[key] != want for key, want in expected.items()):
        raise ValueError('exact actual public-fold scope/refusal/isolation result required')
    if (value.get('training_subjects') != [f'subject_{index:02d}' for index in range(3, 53)]
            or value.get('candidate_rates') != [0.001, 0.0005]
            or value.get('executed_candidate') != 'engineering_rate_1'
            or type(value.get('declared_candidates')) is not list or len(value['declared_candidates']) != 2):
        raise ValueError('unchanged 50-subject fit and two-candidate declared roster required')
    if args.method == 'eegnet':
        if any(value.get(key) is not None for key in (
                'template_state_sha256', 'template_parameter_count', 'full_backbone_blocks', 'full_backbone_embed_dim')):
            raise ValueError('EEGNet must not claim a LaBraM template')
    elif (value.get('template_parameter_count') != 5818138
            or value.get('full_backbone_blocks') != 12 or value.get('full_backbone_embed_dim') != 200):
        raise ValueError('complete 12-block full-shape random initialized LaBraM template required')
    for key in ('initial_source_state_sha256', 'fitted_source_state_sha256',
                'adapted_state_sha256', 'fixture_source_sha256', 'input_identity_sha256',
                'input_identity_file_sha256',
                'fold_evidence_sha256', 'fold_evidence_file_sha256', 'contract_sha256'):
        if type(value.get(key)) is not str or re.fullmatch('[a-f0-9]{64}', value[key]) is None:
            raise ValueError('explicit state/input/contract/file digests required')
    if len({value[key] for key in (
            'initial_source_state_sha256', 'fitted_source_state_sha256', 'adapted_state_sha256')}) != 3:
        raise ValueError('actual distinct initial, fitted-source and support-adapted states required')
    selected = value.get('selected_parameter_names')
    if (type(selected) is not list or not selected or len(set(selected)) != len(selected)
            or any(type(name) is not str or not name for name in selected)):
        raise ValueError('exact distinct selected parameter-name list required')
    updates = value.get('optimizer_updates')
    expected_parameters = {'eegnet': 2642, 'labram_linear': 402,
                           'labram_lora': 2002, 'labram_full': 5818138}[args.method]
    if type(updates) is not list or len(updates) != 51:
        raise ValueError('51 actual optimizer-hook records required')
    for index, row in enumerate(updates, 1):
        if (type(row) is not dict or row.get('update') != index
                or row.get('role') != ('source' if index <= 50 else 'inner_validation_support')
                or row.get('selected_parameters') != expected_parameters
                or row.get('selected_tensors') != len(selected)
                or row.get('finite_selected_gradients') is not True
                or row.get('finite_selected_parameters') is not True):
            raise ValueError('actual finite correctly masked optimizer update record required')
        for key in ('selected_state_sha256_before', 'selected_state_sha256_after'):
            if type(row.get(key)) is not str or re.fullmatch('[a-f0-9]{64}', row[key]) is None:
                raise ValueError('actual optimizer selected-state byte digests required')
        if row['selected_state_sha256_before'] == row['selected_state_sha256_after']:
            raise ValueError('each actual SGD update must change selected state bytes')
    for key, count in (('source_losses', 50), ('support_losses', 1)):
        losses = value.get(key)
        if (type(losses) is not list or len(losses) != count or any(
                type(loss) not in (int, float) or not math.isfinite(loss) for loss in losses)):
            raise ValueError('complete finite source/support loss history required')

    def bounded_json(path, maximum=4 * 1024**2):
        if (path.resolve(strict=True) != path or not path.is_file()
                or path.stat().st_nlink != 1 or not 0 < path.stat().st_size <= maximum):
            raise ValueError('bounded ordinary direct single-link JSON required')
        with path.open('rb') as stream:
            raw = stream.read(maximum + 1)
        if len(raw) > maximum:
            raise ValueError('bounded JSON exceeded declared maximum')
        return raw, json.loads(raw)

    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

    fixture = OUT / 'fixture'
    identity_path = fixture / 'synthetic-input-identity.json'
    if value.get('fixture_root') != str(fixture) or value.get('input_identity_path') != str(identity_path):
        raise ValueError('one exact owned synthetic fixture identity required')
    identity_raw, identity = bounded_json(identity_path)
    identity_content = {key: item for key, item in identity.items() if key != 'sha256'}
    if (identity.get('sha256') != value['input_identity_sha256']
            or hashlib.sha256(identity_raw).hexdigest() != value['input_identity_file_sha256']
            or hashlib.sha256(canonical(identity_content).encode()).hexdigest() != identity['sha256']
            or identity_raw != (canonical(identity) + '\n').encode()
            or identity.get('files') != value.get('input_files')):
        raise ValueError('exact canonical synthetic identity and complete file map required')
    physical = value.get('physical_inputs')
    if type(physical) is not dict or set(physical) != set(identity['files']) or len(physical) != 213:
        raise ValueError('complete 213-path physical input mapping required')
    actual = {path.relative_to(fixture).as_posix()
        for directory in (fixture / 'configs', fixture / 'data')
        for path in directory.rglob('*') if path.is_file() or path.is_symlink()}
    if actual != set(physical):
        raise ValueError('physical synthetic input inventory differs')
    for relative, pin in identity['files'].items():
        path = fixture / relative
        if (Path(relative).is_absolute() or '..' in Path(relative).parts
                or physical[relative] != str(path) or path.resolve(strict=True) != path
                or not path.is_file() or path.stat().st_nlink != 1
                or type(pin) is not dict or set(pin) != {'sha256', 'size_bytes'}
                or type(pin['size_bytes']) is not int or not 0 < pin['size_bytes'] <= 16 * 1024**2
                or path.stat().st_size != pin['size_bytes'] or digest(path) != pin['sha256']):
            raise ValueError('exact bounded physical synthetic input file changed: ' + relative)
    if value.get('protected_outer_paths') != [str(path) for path in protected_declared]:
        raise ValueError('reported protected outer-target paths differ from enforced paths')
    if any(fixture_read_phases.get(str(path), {}).get('during_fold', 0) != 0 for path in protected_declared):
        raise ValueError('outer-target input contents were opened during public fitting')
    evidence_path = OUT / 'fold-evidence.json'
    if value.get('fold_evidence_path') != str(evidence_path):
        raise ValueError('exact direct raw fold evidence path required')
    evidence_raw, evidence = bounded_json(evidence_path)
    envelope_content = {key: item for key, item in evidence.items() if key != 'sha256'}
    if (len(evidence_raw) != value.get('fold_evidence_file_bytes')
            or hashlib.sha256(evidence_raw).hexdigest() != value['fold_evidence_file_sha256']
            or evidence.get('sha256') != value['fold_evidence_sha256']
            or hashlib.sha256(canonical(envelope_content).encode()).hexdigest() != evidence['sha256']
            or evidence_raw != (canonical(evidence) + '\n').encode()
            or evidence.get('kind') != 'engineering_smoke' or evidence.get('phase') != 2
            or evidence.get('schema_version') != 1):
        raise ValueError('actual unchanged canonical engineering fold envelope required')
    diagnostic = evidence.get('payload')
    if (type(diagnostic) is not dict
            or set(diagnostic) != {'purpose', 'contract', 'contract_sha256', 'complete', 'folds', 'selected_candidate'}
            or diagnostic['complete'] is not False or diagnostic['selected_candidate'] is not None
            or type(diagnostic['folds']) is not list or len(diagnostic['folds']) != 1
            or diagnostic['contract_sha256'] != value['contract_sha256']
            or diagnostic['contract']['method'] != args.method):
        raise ValueError('raw diagnostic must retain exact incomplete payload without fabricated selector fields')
    result_raw, persisted_result = bounded_json(OUT / 'probe-result.json')
    if persisted_result != value or result_raw != (canonical(value) + '\n').encode():
        raise ValueError('persisted create-once full probe result differs')


validate_result(result)
pause_check()
clean_audit()
verify_pins()
if source_check(ROOT) != CANONICAL:
    raise ValueError('canonical source changed during public synthetic fold')
if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1 or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
    raise ValueError('reviewed CPU/thread/GPU controls changed')
from evaluation.phase2_runner import environment_digest

environment_sha256 = environment_digest()
loaded = {}
for module in tuple(sys.modules.values()):
    name = getattr(module, '__file__', None)
    if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(OUT):
        loaded[str(Path(name).resolve())] = digest(name)
payload = {
    'schema': 'cho51_source_fold_qualification_v1', 'passed': True,
    'method': args.method, 'pins_sha256': args.expect_pins, 'result': result,
    'source_subjects_available': 52, 'training_subject_count': 50,
    'inner_validation_subject': 'subject_01', 'outer_target': 'subject_02',
    'actual_gradient_updates': 51, 'complete': False,
    'public_complete_selector_verifier_refused': True,
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'elapsed_seconds': time.monotonic() - started,
    'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
    'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
    'source_review_sha256': pins['source_review_sha256'],
    'observed_loaded_module_hashes': loaded, 'loaded_module_files': len(loaded),
    'environment_sha256': environment_sha256,
    'torch_threads': torch.get_num_threads(), 'torch_interop_threads': torch.get_num_interop_threads(),
    'gpu_hidden': os.environ.get('CUDA_VISIBLE_DEVICES') == '',
    'hostname_metadata_queries': hostname_queries, 'read_only_git_queries': git_queries,
    'existing_directory_mkdir_refusals': existing_mkdir_refusals,
    'denied_operations': denied, 'unexpected_denials': 0,
    'expected_blocked_ipv6_probes': 1, 'observed_numerical_calls': numerical_calls,
    'protected_target_input_paths': [str(path) for path in protected_declared],
    'protected_target_transitions': protection_transitions,
    'protected_target_planned_negative_checks': protected_negative_checks,
    'protected_target_fold_read_attempts': protected_fold_read_attempts,
    'fixture_input_read_phases': fixture_read_phases,
    'cache_runtime_routed_to_owned_output': True,
    'actual_study_inputs_or_pretrained_weights_used': False,
    'whole_numerical_worker_verified': False, 'full_selector_history_verified': False,
    'real_recorder_or_original_attempt_used': False,
    'selection_publication_tensor_verified': False, 'scientific_admission': False,
    'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
}
with (OUT / 'qualification.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
for name, expected in loaded.items():
    if digest(name) != expected:
        raise ValueError('loaded module changed during qualification: ' + name)
clean_audit()
print(json.dumps({'passed': True, 'method': args.method,
    'actual_gradient_updates': 51, 'scientific_admission': False}))
