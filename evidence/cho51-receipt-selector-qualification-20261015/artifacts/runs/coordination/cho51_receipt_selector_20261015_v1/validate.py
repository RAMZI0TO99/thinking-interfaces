"""Run only synthetic receipt boundaries and real public record-consistency checks.

No actual study inputs, tensors, model construction, fitting or attempts are
permitted. The native parent guard supplies finite Job/resource supervision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent
CANONICAL_SHA256 = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins', type=Path, required=True)
parser.add_argument('--expect-pins', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
raw = args.pins.read_bytes()
if hashlib.sha256(raw).hexdigest() != args.expect_pins:
    raise ValueError('fresh pins changed')
pins = json.loads(raw)
if (
    pins.get('schema') != 'cho51_receipt_selector_synthetic_fresh_pins_v1'
    or pins.get('canonical_source_sha256') != CANONICAL_SHA256
    or pins.get('canonical_files') != 432 or len(pins.get('runtime', {})) != 5
    or any(pins.get(name) != value for name, value in {
        'seconds': 600, 'process_mib': 2048, 'job_mib': 3072,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
        'threads': 1, 'import_mode': 'importlib',
    }.items())
):
    raise ValueError('reviewed synthetic qualification scope or resource limits differ')
OUT = args.output.resolve()
if not OUT.is_relative_to(RUN) or OUT == RUN:
    raise ValueError('unused owned output required')
OUT.mkdir(exist_ok=False)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_pins():
    for relative, expected in pins['files'].items():
        if digest(ROOT / relative) != expected:
            raise ValueError('source/input pin changed: ' + relative)
    for name, expected in pins['runtime'].items():
        if digest(name) != expected:
            raise ValueError('runtime pin changed: ' + name)
    review = json.loads(Path(pins['source_review_path']).read_bytes())
    if (
        digest(Path(pins['source_review_path'])) != pins['source_review_sha256']
        or review.get('source_only') is not True
        or review.get('remaining_actionable_findings') != []
        or review.get('files') != pins['reviewed_files']
        or any(digest(ROOT / relative) != expected for relative, expected in review['files'].items())
    ):
        raise ValueError('independent exact source review changed')


verify_pins()
# These must precede tempfile, numerical libraries and pytest imports so their
# default scratch directories stay inside this one fresh output directory.
for variable, folder in {
    'TMP': 'temp', 'TEMP': 'temp', 'TMPDIR': 'temp',
    'MPLCONFIGDIR': 'matplotlib', '_MNE_FAKE_HOME_DIR': 'mne-home', 'HF_HOME': 'huggingface',
}.items():
    path = OUT / folder
    path.mkdir(exist_ok=True)
    os.environ[variable] = str(path)
os.environ.update(
    PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1',
    CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
    NUMEXPR_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1',
)
sys.path[:0] = [str(ROOT), str(ROOT / '.venv/Lib/site-packages')]
from tools.migration.common import source_check

if source_check(ROOT) != CANONICAL_SHA256:
    raise ValueError('canonical source changed before synthetic qualification')
pause_paths = [Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001' /
               'coordination/PRO2_REQUEST_PRO3_PAUSE.json'
               for day in ('20261007', '20261012', '20261013', '20261015')]
if any(path.exists() for path in pause_paths):
    raise ValueError('genuine peer pause before synthetic qualification')
denied = []
hostname_queries = 0
git_queries = 0


def path_of(value):
    value = os.fsdecode(value)
    if value.startswith('\\\\?\\'):
        value = value[4:]
    return Path(value).resolve()


def refuse(event, detail):
    frames = []
    frame = sys._getframe(1)
    for _ in range(12):
        if frame is None:
            break
        frames.append({'file': frame.f_code.co_filename, 'function': frame.f_code.co_name})
        frame = frame.f_back
    denied.append({'event': event, 'detail': repr(detail)[:300], 'frames': frames})
    raise PermissionError('synthetic qualification denied: ' + event)


def provenance_git(values):
    """Permit only the two unchanged capture_source read commands under OUT."""
    global git_queries
    import subprocess
    executable, arguments, cwd, environment = values
    forms = [
        [pins['git_command_executable'], '--no-optional-locks', 'rev-parse', '--verify', 'HEAD'],
        [pins['git_command_executable'], '--no-optional-locks', 'status', '--porcelain', '--untracked-files=all'],
    ]
    match = (arguments in forms if isinstance(arguments, list)
             else arguments in [subprocess.list2cmdline(row) for row in forms])
    frame = sys._getframe(1)
    source_stack = False
    while frame:
        if (frame.f_code.co_name == 'capture_source'
                and Path(frame.f_code.co_filename).resolve() == ROOT / 'core/provenance.py'):
            source_stack = True
        frame = frame.f_back
    if (
        not match or not source_stack or environment is not None or cwd is None
        or not Path(cwd).resolve().is_relative_to(OUT)
        or (executable is None and os.name != 'nt')
        or (executable is not None and Path(executable).resolve() != Path(pins['git_executable']))
    ):
        refuse('subprocess.Popen', values)
    git_queries += 1


def audit(event, values):
    global hostname_queries
    if event == 'socket.gethostname':
        hostname_queries += 1
    elif event == 'subprocess.Popen':
        provenance_git(values)
    elif event.startswith('socket.') or event in {'os.system', 'os.startfile'}:
        refuse(event, values)
    elif event == 'open' and isinstance(values[0], (str, bytes, os.PathLike)):
        path = path_of(values[0])
        mode = values[1] if isinstance(values[1], str) else ''
        flags = values[2] if isinstance(values[2], int) else 0
        writing = any(char in mode for char in 'wax+') or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        if writing and not path.is_relative_to(OUT):
            refuse(event, path)
        if not writing and not path.is_relative_to(OUT):
            if (
                path.is_relative_to(ROOT / 'data/raw') or path.is_relative_to(ROOT / 'data/processed')
                or path.is_relative_to(ROOT / 'weights')
                or path.suffix.lower() in {'.npz', '.npy', '.mat', '.edf', '.gdf', '.pt', '.pth', '.ckpt', '.safetensors'}
            ):
                if path.suffix.lower() != '.pth' or not path.is_relative_to(ROOT / '.venv'):
                    refuse(event, path)
    elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace',
                   'os.link', 'os.symlink', 'os.chmod', 'os.utime', 'os.truncate'}:
        count = 2 if event in {'os.rename', 'os.replace', 'os.link', 'os.symlink'} else 1
        for value in values[:count]:
            if isinstance(value, (str, bytes, os.PathLike)):
                path = path_of(value)
                if not path.is_relative_to(OUT) and not (event == 'os.mkdir' and path.is_dir()):
                    refuse(event, path)


sys.addaudithook(audit)
started = time.monotonic()
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)


def no_model(*arguments, **keywords):
    refuse('forbidden_model_checkpoint_optimizer_or_backward_call', None)


torch.nn.Module.__init__ = no_model
torch.load = no_model
torch.serialization.load = no_model
torch.jit.load = no_model
torch.optim.Optimizer.__init__ = no_model
torch.Tensor.backward = no_model
torch.autograd.backward = no_model
torch.autograd.grad = no_model
import safetensors
import safetensors.torch

safetensors.safe_open = no_model
safetensors.torch.safe_open = no_model
safetensors.torch.load_file = no_model
safetensors.torch.load_model = no_model
safetensors.torch.load = no_model
from evaluation.phase2_runner import CaseRecorder, environment_digest


def no_recorder(*arguments, **keywords):
    refuse('recorder_constructor_or_attempt_used', None)


CaseRecorder.__init__ = no_recorder
import pytest


class Results:
    def __init__(self):
        self.items = 0
        self.calls = []
        self.skipped = []

    def pytest_collection_finish(self, session):
        self.items = len(session.items)

    def pytest_runtest_setup(self, item):
        if any(path.exists() for path in pause_paths):
            pytest.fail('genuine peer pause requested')

    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.skipped.append({'nodeid': report.nodeid, 'phase': report.when})
        if report.when == 'call' or report.failed:
            self.calls.append({'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome})


results = Results()
code = pytest.main([
    '-q', '-s', '-p', 'no:cacheprovider', '-o', 'addopts=', '--import-mode=importlib',
    '--log-file', str(OUT / 'pytest.log'), '--basetemp', str(OUT / 't'),
    '--junitxml', str(OUT / 'junit.xml'),
    *[str(ROOT / node) for node in pins['test_nodes']],
], plugins=[results])
# urllib3 catches this optional platform capability probe. The audit denies
# socket creation before it exists; its exact pinned caller is classified only.
connection = (ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py').resolve()
expected_denials = [item for item in denied if item['event'] == 'socket.__new__'
                   and ', 23, 1, 0)' in item['detail'] and any(
                       frame['function'] == '_has_ipv6' and Path(frame['file']).resolve() == connection
                       for frame in item['frames'])]
unexpected = [item for item in denied if item not in expected_denials]
verify_pins()
if source_check(ROOT) != CANONICAL_SHA256:
    raise ValueError('canonical source changed during synthetic qualification')
loaded = {}
for module in tuple(sys.modules.values()):
    name = getattr(module, '__file__', None)
    if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(OUT):
        loaded[str(Path(name).resolve())] = digest(name)
qualified = (
    code == 0 and results.items == pins['expected_cases']
    and len(results.calls) == pins['expected_cases'] and not results.skipped
    and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in results.calls)
    and len(expected_denials) <= 1 and not unexpected
    and not any(path.exists() for path in pause_paths)
    and torch.get_num_threads() == 1 and torch.get_num_interop_threads() == 1
    and os.environ['CUDA_VISIBLE_DEVICES'] == ''
)
payload = {
    'schema': 'cho51_receipt_selector_synthetic_qualification_v1',
    'passed': qualified, 'pytest_exit': int(code), 'collected_cases': results.items,
    'pins_sha256': args.expect_pins, 'reports': results.calls, 'skipped_reports': results.skipped,
    'elapsed_seconds': time.monotonic() - started,
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'canonical_source_sha256': CANONICAL_SHA256, 'canonical_files': 432,
    'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
    'source_review_sha256': pins['source_review_sha256'],
    'observed_loaded_module_hashes': loaded, 'loaded_module_files': len(loaded),
    'environment_sha256': environment_digest(), 'torch_threads': torch.get_num_threads(),
    'torch_interop_threads': torch.get_num_interop_threads(),
    'gpu_hidden': os.environ['CUDA_VISIBLE_DEVICES'] == '',
    'hostname_metadata_queries': hostname_queries, 'read_only_git_queries': git_queries,
    'denied_operations': denied, 'unexpected_denials': len(unexpected),
    'expected_blocked_ipv6_probes': len(expected_denials),
    **{name: pins[name] for name in (
        'mocked_tensor_receipt_cases', 'mocked_selector_collection_cases',
        'actual_public_verifier_fabricated_record_cases',
    )},
    'actual_input_or_selected_study_weights_used': False,
    'fabricated_publication_weight_bytes_not_deserialized': True,
    'model_constructed_or_tensor_restore_performed': False,
    'optimizer_or_backward_performed': False,
    'actual_1020_case_native_tensor_roster_verified': False,
    'actual_publication_or_selector_training_history_verified': False,
    'real_recorder_or_original_attempt_used': False,
    'selection_publication_tensor_verified': False, 'scientific_admission': False,
    'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
}
with (OUT / 'qualification.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
for name, expected in loaded.items():
    if digest(name) != expected:
        raise ValueError('loaded file changed: ' + name)
print(json.dumps({
    'passed': qualified, 'tests': results.items, 'skips': len(results.skipped),
    'unexpected_denials': len(unexpected), 'scientific_admission': False,
}))
raise SystemExit(0 if qualified else 1)
