"""Archive compact current native tensor evidence and preserved failed attempts."""
import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = ROOT / 'evidence/cho51-tensor-qualification-20261015'
sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import io_path, source_check

canonical = source_check(ROOT)
pins_raw = (RUN / 'pins_005.json').read_bytes()
pins_sha = hashlib.sha256(pins_raw).hexdigest()
pins = json.loads(pins_raw)
q_path = RUN / 'validation_005/qualification.json'
q = json.loads(q_path.read_bytes())
if not (q['passed'] and q['collected_cases'] == 270 and q['pins_sha256'] == pins_sha
        and q['unexpected_denials'] == 0 and q['tensor_restore_performed_in_this_job'] is False):
    raise ValueError('current complete270-case qualification required')
for rel, sha in pins['files'].items():
    if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != sha:
        raise ValueError('current tested source differs: ' + rel)
scope = json.loads((RUN / 'validation_005/fixture-scope.json').read_bytes())
bundle_path = RUN / 'case_005/bundle.json'
bundle_sha = scope['bundle_sha256']
bundle = json.loads(bundle_path.read_bytes())
native_result = json.loads((RUN / 'case_005/native-result.json').read_bytes())
module_path = ROOT / 'docs/phase2/cho51_tensor_verification_v1/launcher.py'
spec = importlib.util.spec_from_file_location('_closeout_stdlib_tensor_launcher', module_path)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
rechecked = launcher.admit_native_receipt(bundle, bundle_sha, Path(native_result['native_directory']))
if rechecked != native_result or not native_result['one_case_tensor_digest_verified']:
    raise ValueError('current actual one-case native proof differs')
if not (scope['gradient_steps_performed'] == 0 and scope['source_fit_and_complete_fields_are_fabricated']
        and scope['original_case_attempt_used'] is False and scope['scientific_admission'] is False):
    raise ValueError('untrained synthetic engineering fixture required')

paths = [path for path in RUN.iterdir() if path.is_file() and path.suffix in {'.py', '.ps1', '.json'}]
paths += [path for path in (ROOT / 'docs/phase2/cho51_tensor_verification_v1').iterdir()
          if path.is_file() and path.suffix in {'.py', '.md'}]
paths += [q_path, RUN / 'validation_005/junit.xml', RUN / 'validation_005/pytest.log', RUN / 'validation_005/fixture-scope.json']
paths += list((RUN / 'case_005').glob('*.json'))
for name in ('failed_001_source', 'failed_002_source', 'attempt_003_before_cache_fix', 'attempt_004_before_fiducial_fix'):
    paths += [path for path in (RUN / name).rglob('*') if path.is_file()]
attempts = []
current_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'validate_005.py'),
                   '--pins', str(RUN / 'pins_005.json'), '--expect-pins', pins_sha,
                   '--output', str(RUN / 'validation_005')]
current_qualification_native = None
for native in (ROOT / 'runs/migration').glob('20261015T*'):
    admission_path, receipt_path = native / 'admission.json', native / 'receipt.json'
    if not admission_path.is_file() or not receipt_path.is_file():
        continue
    admission = json.loads(admission_path.read_bytes())
    if RUN.name not in json.dumps(admission['command']):
        continue
    receipt = json.loads(receipt_path.read_bytes())
    state = receipt['native_state']
    if not (receipt['job_absent'] and state['job_empty_before_close'] and state['job_closed']
            and not state['cleanup_errors'] and not state['peak_sampling_errors']):
        raise ValueError('every created native Job must have confirmed cleanup')
    launcher._job_absent(receipt['job_name'])
    if admission['command'] == current_command:
        if not receipt['accepted'] or admission['source_sha256'] != canonical:
            raise ValueError('exact current qualification native acceptance required')
        current_qualification_native = native.relative_to(ROOT).as_posix()
    attempts.append(dict(directory=native.relative_to(ROOT).as_posix(), accepted=receipt['accepted'],
        completed_utc=receipt['completed_utc'], fresh_name_absence_verified=True,
        peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes']))
    paths += [native / name for name in ('admission.json', 'receipt.json', 'deadline.json', 'command.log', 'command-result.json')]
if current_qualification_native is None or not any(row['directory'] == Path(native_result['native_directory']).relative_to(ROOT).as_posix() and row['accepted'] for row in attempts):
    raise ValueError('both current boundary/fixture and actual tensor Jobs required')

OUT.mkdir(exist_ok=False)
artifacts = []
for path in sorted(set(paths)):
    if io_path(path).stat().st_size > 8 * 1024**2 or path.suffix.lower() == '.safetensors':
        raise ValueError('only compact non-weight artifacts are archived')
    target = OUT / 'artifacts' / path.relative_to(ROOT)
    physical_target = io_path(target)
    physical_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(io_path(path), physical_target)
    raw = physical_target.read_bytes()
    artifacts.append(dict(source=path.relative_to(ROOT).as_posix(), path=target.relative_to(OUT).as_posix(),
        sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
summary = dict(schema='cho51_tensor_engineering_closeout_v1', observed_utc=datetime.now(timezone.utc).isoformat(),
    boundary_checks_passed=270, contract_boundary_checks=120, mocked_native_boundary_checks=150,
    current_qualification_native=current_qualification_native, actual_tensor_native=native_result['native_directory'],
    actual_untrained_eegnet_cases_verified=1, actual_safetensors_bytes=scope['weights_bytes'],
    initial_and_restored_state_sha256=scope['initial_state_sha256'], source_fit_and_complete_claims_fabricated=True,
    full_roster_verified=False, full_selector_evidence_verified=False, scientific_admission=False,
    original_case_attempts_remaining=0, original_case_used=False, canonical_source_sha256=canonical,
    source_pins_rechecked=len(pins['files']), runtime_pins=len(pins['runtime']), native_attempts=attempts,
    artifact_count=len(artifacts), all_created_jobs_closed_empty_freshly_absent=True,
    actual_training_or_recording_prediction_performed=False)
for name, value in (('manifest.json', {'artifacts': artifacts}), ('summary.json', summary)):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
print(json.dumps(summary))
