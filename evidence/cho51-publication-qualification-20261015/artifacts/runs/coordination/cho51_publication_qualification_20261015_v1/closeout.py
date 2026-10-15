"""Archive compact synthetic publication proof only after accepted native cleanup."""
import ctypes
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = ROOT / 'evidence/cho51-publication-qualification-20261015'
pins_raw = (RUN / 'pins.json').read_bytes()
pins_sha = hashlib.sha256(pins_raw).hexdigest()
pins = json.loads(pins_raw)
q_path = RUN / 'validation_001/qualification.json'
q = json.loads(q_path.read_bytes())
if not (q['passed'] and q['collected_cases'] == pins['expected_cases']
        and q['pins_sha256'] == pins_sha
        and q['canonical_source_sha256'] == pins['canonical_source_sha256']
        and q['actual_asset_loader_invoked'] is False
        and q['actual_publication_history_verified'] is False
        and q['selected_tensors_verified'] is False):
    raise ValueError('passing complete synthetic publication qualification required')
matches = []
for path in (ROOT / 'runs/migration').glob('20261015T*'):
    admission, receipt_path = path / 'admission.json', path / 'receipt.json'
    if admission.is_file() and receipt_path.is_file() and RUN.name in json.dumps(json.loads(admission.read_bytes())['command']):
        matches.append(path)
if len(matches) != 1:
    raise ValueError('one fresh native attempt required for this closeout')
native = matches[0]
admission = json.loads((native / 'admission.json').read_bytes())
expected_command = [
    str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'validate.py'),
    '--pins', str(RUN / 'pins.json'), '--expect-pins', pins_sha,
    '--output', str(RUN / 'validation_001'),
]
if (admission['command'] != expected_command
        or admission['source_sha256'] != pins['canonical_source_sha256']):
    raise ValueError('native admission differs from the exact validator/output/current pin bytes')
receipt = json.loads((native / 'receipt.json').read_bytes())
state = receipt['native_state']
if not (receipt['accepted'] and receipt['job_absent'] and state['job_closed']
        and state['job_empty_before_close'] and not state['cleanup_errors']
        and not state['peak_sampling_errors']):
    raise ValueError('accepted native receipt and confirmed cleanup required')
api = ctypes.WinDLL('kernel32', use_last_error=True)
api.OpenJobObjectW.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_wchar_p]
api.OpenJobObjectW.restype = ctypes.c_void_p
api.CloseHandle.argtypes = [ctypes.c_void_p]
ctypes.set_last_error(0)
handle = api.OpenJobObjectW(4, False, receipt['job_name'])
error = ctypes.get_last_error()
if handle:
    api.CloseHandle(handle)
    raise ValueError('owned Job name still exists')
if error != 2:
    raise ValueError('fresh native named-Job absence not confirmed')
for rel, expected in pins['files'].items():
    if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected:
        raise ValueError('pinned file changed before archival: ' + rel)
paths = [path for path in RUN.iterdir() if path.is_file() and path.suffix in {'.py', '.ps1', '.json'}]
paths += [q_path, RUN / 'validation_001/junit.xml', RUN / 'validation_001/pytest.log']
paths += [path for path in (ROOT / 'docs/phase2/cho51_publication_collection_v1').iterdir()
          if path.is_file() and path.suffix in {'.py', '.md'}]
paths += [native / name for name in ('admission.json', 'receipt.json', 'deadline.json', 'command.log', 'command-result.json')]
OUT.mkdir(exist_ok=False)
artifacts = []
for path in sorted(set(paths)):
    if not path.is_file() or path.stat().st_size > 8 * 1024**2:
        raise ValueError('absent or oversized artifact: ' + str(path))
    target = OUT / 'artifacts' / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    raw = target.read_bytes()
    artifacts.append({'source': path.relative_to(ROOT).as_posix(),
                      'path': target.relative_to(OUT).as_posix(), 'bytes': len(raw),
                      'sha256': hashlib.sha256(raw).hexdigest()})
summary = {
    'schema': 'cho51_publication_synthetic_closeout_v1',
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'passed_checks': q['collected_cases'],
    'dependency_mocked_boundaries': pins['dependency_mocked_boundaries'],
    'hybrid_composition_cases': pins['hybrid_composition_cases'],
    'fabricated_publication_byte_checks': pins['publication_byte_cases'],
    'actual_input_or_publication_history_verified': False,
    'selected_tensors_verified': False, 'full_selector_evidence_verified': False,
    'native_directory': native.relative_to(ROOT).as_posix(),
    'native_completed_utc': receipt['completed_utc'],
    'native_job_closed_empty_absent': True, 'fresh_named_job_absence_verified': True,
    'peak_process_bytes': state['peak_process_commit_bytes'],
    'peak_job_bytes': state['peak_job_commit_bytes'],
    'source_pins_rechecked': q['input_pins_rechecked'],
    'canonical_source_sha256': pins['canonical_source_sha256'],
    'pins_sha256': pins_sha,
    'artifact_count': len(artifacts), 'scientific_admission': False,
    'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
}
for name, value in (('manifest.json', {'artifacts': artifacts}), ('summary.json', summary)):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
print(json.dumps(summary))
