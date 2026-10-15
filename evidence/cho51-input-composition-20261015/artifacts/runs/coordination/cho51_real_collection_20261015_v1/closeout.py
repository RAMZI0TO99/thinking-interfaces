"""Archive only compact proof of actual-input/fabricated-record composition."""
import ctypes
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = ROOT / 'evidence/cho51-input-composition-20261015'
q_path = RUN / 'validation_001/qualification.json'
q = json.loads(q_path.read_bytes())
if not (q['passed'] and q['collected_cases'] == 28
        and len(q['actual_data_files_verified']) == 156
        and q['actual_input_loader_replaced'] is False
        and q['actual_recorder_history_verified'] is False):
    raise ValueError('complete hybrid-scope passing qualification required')
matches = []
for candidate in (ROOT / 'runs/migration').glob('20261015T*'):
    admission = candidate / 'admission.json'
    receipt = candidate / 'receipt.json'
    if not admission.is_file() or not receipt.is_file():
        continue
    if RUN.name not in json.dumps(json.loads(admission.read_bytes())['command']):
        continue
    matches.append(candidate)
if len(matches) != 1:
    raise ValueError('expected one fresh native attempt for this phase')
native = matches[0]
receipt = json.loads((native / 'receipt.json').read_bytes())
state = receipt['native_state']
if not (receipt['accepted'] and receipt['job_absent'] and state['job_closed']
        and state['job_empty_before_close'] and not state['cleanup_errors']
        and not state['peak_sampling_errors']):
    raise ValueError('successful native receipt and cleanup required')
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
    raise ValueError('owned Job absence not confirmed')
pins = json.loads((RUN / 'pins.json').read_bytes())
for rel, expected in pins['files'].items():
    if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected:
        raise ValueError('tested input/source changed before archival: ' + rel)
fixture = ROOT / pins['synthetic_recorder_relative']
scope = json.loads((fixture / 'FIXTURE_SCOPE.json').read_bytes())
if scope['scientific_result'] or scope['prediction_or_fit_performed']:
    raise ValueError('fixture scope must remain explicitly fabricated')
paths = [path for path in RUN.iterdir() if path.is_file() and path.suffix in {'.py', '.json'}]
paths += [q_path, RUN / 'validation_001/junit.xml', RUN / 'validation_001/pytest.log', fixture / 'FIXTURE_SCOPE.json']
paths += [path for path in (ROOT / 'docs/phase2/cho51_input_collection_v1').iterdir()
          if path.is_file() and path.suffix in {'.py', '.md'}]
paths += [native / name for name in ('admission.json', 'receipt.json', 'deadline.json', 'command.log', 'command-result.json')]
OUT.mkdir(exist_ok=False)
artifacts = []
for path in sorted(set(paths)):
    if not path.is_file() or path.stat().st_size > 8 * 1024**2:
        raise ValueError('absent or unexpectedly large artifact: ' + str(path))
    target = OUT / 'artifacts' / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    raw = target.read_bytes()
    artifacts.append({'source': path.relative_to(ROOT).as_posix(),
                      'path': target.relative_to(OUT).as_posix(), 'bytes': len(raw),
                      'sha256': hashlib.sha256(raw).hexdigest()})
summary = {
    'schema': 'cho51_input_fabricated_record_composition_closeout_v1',
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'passed_checks': 28, 'dependency_mocked_boundaries': 24,
    'actual_input_fabricated_record_checks': 4,
    'actual_input_files_verified_before_and_after': 156,
    'actual_input_bytes': sum(row['bytes'] for row in q['actual_data_files_verified'].values()),
    'actual_input_loader_replaced': False,
    'retained_B_bindings_referenced_not_redecoded': True,
    'actual_recorder_history_verified': False,
    'fabricated_records': 1020, 'actual_available_subjects': 52, 'evaluation_targets': 51,
    'native_directory': native.relative_to(ROOT).as_posix(),
    'native_job_closed_empty_absent': True, 'fresh_named_job_absence_verified': True,
    'native_completed_utc': receipt['completed_utc'],
    'peak_process_bytes': state['peak_process_commit_bytes'],
    'peak_job_bytes': state['peak_job_commit_bytes'],
    'source_pins_rechecked': q['input_pins_rechecked'],
    'canonical_source_sha256': pins['canonical_source_sha256'],
    'independent_static_review': '/root/review_real_composition',
    'artifact_count': len(artifacts), 'scientific_admission': False,
    'selected_publication_or_tensor_verified': False,
    'full_selector_evidence_verified': False,
    'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
}
for name, value in (('manifest.json', {'artifacts': artifacts}), ('summary.json', summary)):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
print(json.dumps(summary))
