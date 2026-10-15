"""Finite synthetic numerical engineering child, with no study/checkpoint I/O."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent
SITE = ROOT / '.venv/Lib/site-packages'
PROBE_PATH = ROOT / 'docs/phase2/cho51_numerical_probe_v1/probe.py'
CANONICAL_SHA256 = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
METHODS = ('labram_full',)
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


if args.pins.resolve(strict=True) != RUN / 'pins.json' or digest(args.pins) != args.expect_pins:
    raise ValueError('independent fresh numerical pins differ')
pins = json.loads(args.pins.read_bytes())
if (
    pins.get('schema') != 'cho51_numerical_full_successor_fresh_pins_v1'
    or pins.get('canonical_source_sha256') != CANONICAL_SHA256
    or pins.get('canonical_files') != 432 or pins.get('predecessor_files') != 556
    or len(pins.get('runtime', {})) != 5 or pins.get('methods') != list(METHODS)
    or any(pins.get(key) != value for key, value in {
        'seconds_per_method': 300, 'process_mib': 3072, 'job_mib': 4096,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20, 'threads': 1,
        'gradient_steps_per_method': 8, 'candidate_rates_per_method': 2,
        'source_batch': 2, 'support_batch': 10, 'query_batch': 2,
        'channels': 64, 'eegnet_samples': 512, 'labram_samples': 800, 'labram_layers': 12,
    }.items())
):
    raise ValueError('reviewed numerical scope or finite limits differ')
OUT = args.output.resolve()
if OUT != RUN / ('output_' + args.method + '_001') or args.output.absolute() != OUT:
    raise ValueError('one direct unused method-specific output required')
OUT.mkdir(exist_ok=False)


def verify_pins():
    if digest(args.pins) != args.expect_pins:
        raise ValueError('numerical pins changed during execution')
    for relative, expected in pins['files'].items():
        if digest(ROOT / relative) != expected:
            raise ValueError('source/library pin changed: ' + relative)
    for path, expected in pins['runtime'].items():
        if digest(path) != expected:
            raise ValueError('runtime pin changed: ' + path)
    review_path = Path(pins['source_review_path'])
    review = json.loads(review_path.read_bytes())
    if (digest(review_path) != pins['source_review_sha256']
            or review.get('source_only') is not True
            or review.get('remaining_actionable_findings') != []
            or review.get('files') != pins['reviewed_files']
            or any(digest(ROOT / relative) != expected for relative, expected in review['files'].items())):
        raise ValueError('independent exact numerical source review changed')


verify_pins()
# Initialize every cache/temp route before importing tempfile or numerical code.
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

if source_check(ROOT) != CANONICAL_SHA256:
    raise ValueError('canonical source changed before numerical probe')
MNE_RESOURCE = Path(pins['mne_resource_path'])
CONNECTION = SITE / 'urllib3/util/connection.py'
if (MNE_RESOURCE != SITE / 'mne/data/fsaverage/fsaverage-fiducials.fif'
        or MNE_RESOURCE.stat().st_size != 260
        or digest(MNE_RESOURCE) != pins['mne_resource_sha256']
        or pins['mne_resource_sha256'] != '0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'):
    raise ValueError('exact independently pinned MNE anatomical template required')


def pause_check():
    if any(path.exists() for path in PAUSES):
        raise RuntimeError('genuine peer pause requested')


def path_of(value):
    value = os.fsdecode(value)
    if value.startswith('\\\\?\\'):
        value = value[4:]
    return Path(value).resolve()


denied = []
hostname_queries = 0
existing_mkdir_refusals = 0
probe_active = False
numerical_calls = {}
EXPECTED_PROBE = {
    'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
    'source_file': str(CONNECTION),
    'source_sha256': pins['files'][CONNECTION.relative_to(ROOT).as_posix()],
}


def refuse(event, detail=None):
    denied.append({'event': event, 'detail': repr(detail)[:500]})
    raise PermissionError('numerical engineering child denied: ' + event)


def inside_write(value):
    if not isinstance(value, (str, bytes, os.PathLike)) or not path_of(value).is_relative_to(OUT):
        refuse('outside_or_unbound_output_write', value)


def probe_stack():
    frame = sys._getframe(1)
    while frame:
        if frame.f_code.co_name == 'run_probe' and path_of(frame.f_code.co_filename) == PROBE_PATH:
            return True
        frame = frame.f_back
    return False


def allow_numerical(name):
    if not probe_active or not probe_stack():
        refuse('numerical_call_outside_pinned_probe', name)
    pause_check()
    numerical_calls[name] = numerical_calls.get(name, 0) + 1


def audit(event, values):
    global hostname_queries, existing_mkdir_refusals
    if event == 'socket.gethostname':
        hostname_queries += 1
    elif event.startswith('socket.'):
        if event == 'socket.__new__' and values[1:] == (socket.AF_INET6, socket.SOCK_STREAM, 0):
            frame = sys._getframe(1)
            while frame:
                if frame.f_code.co_name == '_has_ipv6' and path_of(frame.f_code.co_filename) == CONNECTION:
                    denied.append(dict(EXPECTED_PROBE))
                    raise PermissionError('optional IPv6 import probe blocked before socket creation')
                frame = frame.f_back
        refuse(event, values)
    elif (event in {'subprocess.Popen', 'os.system', 'os.startfile', 'os.posix_spawn',
                    'os.fork', 'os.forkpty', 'pty.spawn'}
          or event.startswith(('os.exec', 'os.spawn'))):
        refuse(event, values)
    elif event == 'open':
        mode = values[1] if isinstance(values[1], str) else ''
        flags = values[2] if isinstance(values[2], int) else 0
        writing = any(char in mode for char in 'wax+') or bool(
            flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if not isinstance(values[0], (str, bytes, os.PathLike)):
            if writing:
                inside_write(values[0])
            return
        path = path_of(values[0])
        if writing:
            inside_write(path)
        elif not path.is_relative_to(OUT):
            parts = tuple(part.lower() for part in path.parts)
            data_path = any(parts[index:index + 2] in {
                ('data', 'raw'), ('data', 'processed'), ('data', 'interim'),
            } for index in range(len(parts) - 1))
            if path == MNE_RESOURCE:
                return
            if (data_path or 'weights' in parts
                    or path.suffix.lower() in {'.npz', '.npy', '.mat', '.edf', '.gdf', '.fif', '.set', '.pt', '.pth', '.ckpt', '.safetensors'}):
                if not (path.suffix.lower() == '.pth' and path.is_relative_to(SITE)):
                    refuse('recording_processed_array_or_checkpoint_read', path)
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
    if len(denied) > 1 or any(row != EXPECTED_PROBE for row in denied):
        raise RuntimeError('numerical child observed an unexpected audit denial')


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
from docs.phase2.cho51_numerical_probe_v1 import probe

config_path = Path(pins['model_config_path'])
if (config_path != ROOT / '.cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/0563b6c626e7b40d9a36653b763715db94d945d7/config.json'
        or digest(config_path) != pins['model_config_sha256']
        or config_path.stat().st_size != pins['model_config_bytes']
        or pins['model_config_sha256'] != '813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b'):
    raise ValueError('independently pinned baseline architecture JSON differs')
config = json.loads(config_path.read_bytes())
if not isinstance(config, dict):
    raise ValueError('baseline architecture JSON must be an object')
pause_check()
clean_audit()
probe_active = True
try:
    result = probe.run_probe(OUT, args.method, config)
finally:
    probe_active = False


def validate_result(value):
    expected = {
        'schema': 'cho51_numerical_probe_v1', 'method': args.method, 'passed': True,
        'rate_cases': 2, 'actual_gradient_updates': 8,
        'source_gradient_updates': 4, 'support_gradient_updates': 4,
        'source_examples': 2, 'support_examples': 10, 'query_examples': 2,
        'channels': 64, 'samples': 512 if args.method == 'eegnet' else 800,
        'model_blocks': 0 if args.method == 'eegnet' else 12,
        'random_initialization': True, 'full_architecture_shape': True,
        'baseline_checkpoint_used': False, 'source_kernel_fixture_owned': True,
        'fixture_rates_are_adopted_candidates': False,
        'public_source_fit_verified': False, 'full_worker_verified': False,
        'canonical_source_selector_integration_verified': False,
        'source_cohort_or_selector_used': False, 'recorder_used': False,
        'full_5253_gradient_selection_executed': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0,
    }
    if type(value) is not dict or any(type(value.get(key)) is not type(want) or value[key] != want for key, want in expected.items()):
        raise ValueError('numerical probe did not establish the exact declared synthetic workload')
    if type(value.get('parameter_count')) is not int or value['parameter_count'] < 1:
        raise ValueError('actual positive model parameter count required')
    checks = value.get('checks')
    if not isinstance(checks, (list, tuple)) or len(checks) != 2 or any(type(row) is not dict for row in checks):
        raise ValueError('two independently checked candidate-rate results required')
    if numerical_calls.get('tensor_backward') != 8 or numerical_calls.get('sgd_step') != 8:
        raise ValueError('observed probe must perform exactly eight backward/SGD updates')
    boolean_checks = (
        'finite_logits', 'finite_losses', 'finite_selected_gradients', 'finite_parameters',
        'updates_nonempty_within_mask', 'frozen_state_unchanged', 'source_unchanged',
        'rng_unchanged', 'no_storage_alias', 'query_state_unchanged', 'exact_replay',
        'state_roundtrip_exact', 'query_roundtrip_exact', 'fixture_inputs_unchanged',
    )
    rates = []
    for index, row in enumerate(checks, start=1):
        if any(row.get(key) is not True for key in boolean_checks):
            raise ValueError('all finite/update/isolation/replay/roundtrip checks must pass literally')
        if row.get('changed_source_and_support_parameters_only_within_mask') is not True:
            raise ValueError('explicit selected-mask source/support updates required')
        selected_names = row.get('selected_parameter_names')
        if (type(selected_names) is not list or not selected_names
                or any(type(name) is not str or not name for name in selected_names)
                or len(set(selected_names)) != len(selected_names)):
            raise ValueError('distinct selected parameter-name inventory required')
        for key, count in {'source_gradient_updates': 2, 'support_gradient_updates': 2,
                           'actual_gradient_updates': 4}.items():
            if type(row.get(key)) is not int or row[key] != count:
                raise ValueError('each rate must contain exactly two source and two support/replay updates')
        rate = row.get('rate')
        if type(rate) not in (int, float) or not math.isfinite(rate) or rate <= 0:
            raise ValueError('candidate rates must be finite positive numbers')
        rates.append(rate)
        if rate != (0.001, 0.0005)[index - 1]:
            raise ValueError('exact two predeclared fixture learning rates required')
        losses = row.get('source_losses')
        if (not isinstance(losses, (list, tuple)) or len(losses) != 2
                or any(type(loss) not in (int, float) or not math.isfinite(loss)
                       for loss in [*losses, row.get('support_loss'), row.get('replay_support_loss')])):
            raise ValueError('finite two-step source and support/replay losses required')
        for key in ('source_state_sha256', 'adapted_state_sha256', 'weights_sha256'):
            if type(row.get(key)) is not str or re.fullmatch('[a-f0-9]{64}', row[key]) is None:
                raise ValueError('exact bounded state and saved-weight digests required')
        if type(row.get('weights_file')) is not str:
            raise ValueError('owned absolute full-state output path required')
        weights = Path(row['weights_file'])
        if (weights != OUT / f'rate_{index:02d}_fullstate.safetensors'
                or weights.resolve(strict=True) != weights or not weights.is_file()
                or weights.stat().st_nlink != 1
                or type(row.get('weights_bytes')) is not int
                or not 0 < row['weights_bytes'] <= 25 * 1024**2
                or weights.stat().st_size != row['weights_bytes']
                or digest(weights) != row['weights_sha256']):
            raise ValueError('bounded direct full-state file differs from probe persistence claims')
    if len(set(rates)) != 2:
        raise ValueError('two distinct candidate learning rates required')


validate_result(result)
pause_check()
clean_audit()
verify_pins()
if source_check(ROOT) != CANONICAL_SHA256:
    raise ValueError('canonical source changed during numerical probe')
if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1 or os.environ.get('CUDA_VISIBLE_DEVICES') != '':
    raise ValueError('numerical CPU/thread/GPU controls changed')
from evaluation.phase2_runner import environment_digest

environment_sha256 = environment_digest()
loaded = {}
for module in tuple(sys.modules.values()):
    name = getattr(module, '__file__', None)
    if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(OUT):
        loaded[str(Path(name).resolve())] = digest(name)
payload = {
    'schema': 'cho51_numerical_full_successor_qualification_v1', 'passed': True,
    'method': args.method, 'pins_sha256': args.expect_pins,
    'result': result, 'observed_utc': datetime.now(timezone.utc).isoformat(),
    'elapsed_seconds': time.monotonic() - started,
    'canonical_source_sha256': CANONICAL_SHA256, 'canonical_files': 432,
    'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
    'source_review_sha256': pins['source_review_sha256'],
    'observed_loaded_module_hashes': loaded, 'loaded_module_files': len(loaded),
    'environment_sha256': environment_sha256,
    'torch_threads': torch.get_num_threads(), 'torch_interop_threads': torch.get_num_interop_threads(),
    'gpu_hidden': os.environ.get('CUDA_VISIBLE_DEVICES') == '',
    'hostname_metadata_queries': hostname_queries, 'read_only_git_queries': 0,
    'existing_directory_mkdir_refusals': existing_mkdir_refusals,
    'denied_operations': denied, 'unexpected_denials': 0,
    'expected_blocked_ipv6_probes': len(denied), 'observed_numerical_calls': numerical_calls,
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
print(json.dumps({'passed': True, 'method': args.method, 'actual_gradient_updates': 8, 'scientific_admission': False}))
