"""Run only prepared synthetic collector cases inside a fresh native parent Job."""
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
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins', type=Path, required=True)
parser.add_argument('--expect-pins', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
raw = args.pins.read_bytes()
if hashlib.sha256(raw).hexdigest() != args.expect_pins:
    raise ValueError('fresh pins changed')
pins = json.loads(raw)
OUT = args.output.resolve()
if not OUT.is_relative_to(RUN) or OUT == RUN:
    raise ValueError('unused owned output required')
OUT.mkdir(exist_ok=False)

def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

for rel, expected in pins['files'].items():
    if digest(ROOT / rel) != expected:
        raise ValueError('source/input pin changed: ' + rel)
for name, expected in pins['runtime'].items():
    if digest(name) != expected:
        raise ValueError('runtime pin changed: ' + name)
for variable, folder in {
    'TMP': 'temp', 'TEMP': 'temp', 'TMPDIR': 'temp',
    'MPLCONFIGDIR': 'matplotlib', '_MNE_FAKE_HOME_DIR': 'mne-home', 'HF_HOME': 'huggingface',
}.items():
    path = OUT / folder
    path.mkdir(exist_ok=True)
    os.environ[variable] = str(path)
os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1',
                  CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
sys.path[:0] = [str(ROOT), str(ROOT / '.venv/Lib/site-packages')]
pause_paths = [Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001' /
               'coordination/PRO2_REQUEST_PRO3_PAUSE.json'
               for day in ('20261007', '20261012', '20261013', '20261015')]
denied = []
hostname_queries = 0

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

def audit(event, values):
    global hostname_queries
    if event == 'socket.gethostname':
        hostname_queries += 1
    elif event.startswith('socket.') or event in {'subprocess.Popen', 'os.system', 'os.startfile'}:
        refuse(event, values)
    elif event == 'open' and isinstance(values[0], (str, bytes, os.PathLike)):
        path = path_of(values[0])
        mode = values[1] if isinstance(values[1], str) else ''
        flags = values[2] if isinstance(values[2], int) else 0
        writing = any(c in mode for c in 'wax+') or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        if writing and not path.is_relative_to(OUT):
            refuse(event, path)
        if not writing and not path.is_relative_to(OUT):
            if (path.is_relative_to(ROOT / 'data/raw') or path.is_relative_to(ROOT / 'data/processed')
                    or path.is_relative_to(ROOT / 'weights')
                    or path.suffix.lower() in {'.npz', '.npy', '.mat', '.edf', '.gdf', '.pt', '.pth', '.ckpt', '.safetensors'}):
                # Site initialization reads .pth files; they are not model checkpoints.
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

def no_model(*args, **kwargs):
    refuse('forbidden_model_or_checkpoint_call', None)

torch.nn.Module.__init__ = no_model
torch.load = no_model
from evaluation.phase2_runner import CaseRecorder, environment_digest
original_recorder = CaseRecorder.__init__

def synthetic_recorder(self, root, *, output_root=None):
    if not Path(root).resolve().is_relative_to(OUT):
        refuse('real_recorder_constructor', root)
    if output_root is not None and not Path(output_root).resolve().is_relative_to(OUT):
        refuse('real_recorder_constructor', output_root)
    original_recorder(self, root, output_root=output_root)

CaseRecorder.__init__ = synthetic_recorder
import pytest

class Results:
    def __init__(self):
        self.items = 0
        self.calls = []

    def pytest_collection_finish(self, session):
        self.items = len(session.items)

    def pytest_runtest_setup(self, item):
        if any(path.exists() for path in pause_paths):
            pytest.fail('genuine peer pause requested')

    def pytest_runtest_logreport(self, report):
        if report.when == 'call' or report.failed:
            self.calls.append({'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome})

results = Results()
code = pytest.main([
    '-q', '-p', 'no:cacheprovider', '-o', 'addopts=',
    '--basetemp', str(OUT / 'pytest-temp'), '--junitxml', str(OUT / 'junit.xml'),
    str(ROOT / 'docs/phase2/cho51_recorder_collection_v1/test_collector.py'),
], plugins=[results])
connection = (ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py').resolve()
expected_denials = [d for d in denied if d['event'] == 'socket.bind'
                   and "'::1', 0" in d['detail'] and any(
                       f['function'] == '_has_ipv6' and Path(f['file']).resolve() == connection
                       for f in d['frames'])]
unexpected = [d for d in denied if d not in expected_denials]
for rel, expected in pins['files'].items():
    if digest(ROOT / rel) != expected:
        raise ValueError('source/input changed during qualification: ' + rel)
for name, expected in pins['runtime'].items():
    if digest(name) != expected:
        raise ValueError('runtime changed during qualification: ' + name)
loaded = {}
for module in tuple(sys.modules.values()):
    name = getattr(module, '__file__', None)
    if name and Path(name).is_file() and not Path(name).resolve().is_relative_to(OUT):
        loaded[str(Path(name).resolve())] = digest(name)
qualified = (code == 0 and results.items == 20 and len(expected_denials) <= 1
             and not unexpected and not any(path.exists() for path in pause_paths))
payload = {
    'schema': 'cho51_recorder_synthetic_qualification_v1',
    'passed': qualified, 'pytest_exit': int(code), 'collected_cases': results.items,
    'reports': results.calls, 'elapsed_seconds': time.monotonic() - started,
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'canonical_source_sha256': pins['canonical_source_sha256'],
    'input_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
    'observed_loaded_module_hashes': loaded, 'loaded_module_files': len(loaded),
    'environment_sha256': environment_digest(), 'torch_threads': torch.get_num_threads(),
    'torch_interop_threads': torch.get_num_interop_threads(), 'gpu_hidden': os.environ['CUDA_VISIBLE_DEVICES'] == '',
    'hostname_metadata_queries': hostname_queries, 'denied_operations': denied,
    'unexpected_denials': len(unexpected), 'expected_blocked_ipv6_probes': len(expected_denials),
    'fixture_asset_loader_replaced': True, 'real_input_composition_qualified': False,
    'real_recorder_or_original_attempt_used': False,
    'selection_publication_tensor_verified': False, 'scientific_admission': False,
    'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
}
with (OUT / 'qualification.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(payload, stream, indent=2, sort_keys=True)
    stream.write('\n')
for name, expected in loaded.items():
    if digest(name) != expected:
        raise ValueError('loaded file changed: ' + name)
print(json.dumps({'passed': qualified, 'tests': results.items,
                  'unexpected_denials': len(unexpected), 'scientific_admission': False}))
raise SystemExit(0 if qualified else 1)
