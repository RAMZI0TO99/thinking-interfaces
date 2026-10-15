"""Retain compact native receipts and tested sources, never fabricated temp trees."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'evidence/cho51-collection-qualification-20261015'
recorder = ROOT / 'runs/coordination/cho51_recorder_qualification_20261015_v1'
selection = ROOT / 'runs/coordination/cho51_selection_qualification_20261015_v1'
recorder_q = json.loads((recorder / 'validation_003/qualification.json').read_bytes())
selection_q = json.loads((selection / 'validation_003/qualification.json').read_bytes())
if not (recorder_q['passed'] and recorder_q['collected_cases'] == 20
        and selection_q['passed'] and selection_q['collected_cases'] == 43):
    raise ValueError('both fresh successful synthetic qualifications required')

sources = []
for run in (recorder, selection):
    sources.extend(path for path in run.iterdir()
                   if path.is_file() and path.suffix in {'.py', '.json'})
    for validation in run.glob('validation_*'):
        for name in ('qualification.json', 'junit.xml', 'pytest.log'):
            path = validation / name
            if path.is_file():
                sources.append(path)
for package in ('cho51_recorder_collection_v1', 'cho51_selection_files_v1'):
    sources.extend(path for path in (ROOT / 'docs/phase2' / package).iterdir()
                   if path.is_file() and path.suffix in {'.py', '.md'})
sources.append(Path(__file__))
native = []
for run in (ROOT / 'runs/migration').glob('20261015T*'):
    admission, receipt = run / 'admission.json', run / 'receipt.json'
    if not admission.is_file() or not receipt.is_file():
        continue
    admitted = json.loads(admission.read_bytes())
    command = json.dumps(admitted['command'])
    if not any(path.name in command for path in (recorder, selection)):
        continue
    observed = json.loads(receipt.read_bytes())
    state = observed['native_state']
    if not (observed['job_absent'] and state['job_closed'] and state['job_empty_before_close']
            and not state['cleanup_errors'] and not state['peak_sampling_errors']):
        raise ValueError('native cleanup not confirmed: ' + str(run))
    native.append({
        'directory': run.relative_to(ROOT).as_posix(),
        'accepted': observed['accepted'], 'job_name': observed['job_name'],
        'completed_utc': observed['completed_utc'],
        'peak_process_bytes': state['peak_process_commit_bytes'],
        'peak_job_bytes': state['peak_job_commit_bytes'],
        'job_closed_empty_absent': True,
    })
    for name in ('admission.json', 'receipt.json', 'deadline.json', 'command.log', 'command-result.json'):
        path = run / name
        if path.is_file():
            sources.append(path)
if len(native) != 6 or sum(row['accepted'] for row in native) != 2:
    raise ValueError('expected six fresh attempts and two successful native Jobs')
manifest = json.loads((ROOT / 'tools/migration/source-files.json').read_bytes())
for row in manifest['files']:
    if hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() != row['sha256']:
        raise ValueError('canonical file changed: ' + row['path'])
for run, name in ((recorder, 'pins_003.json'), (selection, 'pins_003.json')):
    pins = json.loads((run / name).read_bytes())
    for rel, expected in pins['files'].items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected:
            raise ValueError('tested source/input changed before archival: ' + rel)

OUT.mkdir(exist_ok=False)
index = []
for source in sorted(set(sources)):
    if source.stat().st_size > 8 * 1024**2:
        raise ValueError('unexpected large evidence artifact: ' + str(source))
    relative = source.relative_to(ROOT)
    target = OUT / 'artifacts' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    raw = target.read_bytes()
    index.append({'source': relative.as_posix(),
                  'path': target.relative_to(OUT).as_posix(), 'bytes': len(raw),
                  'sha256': hashlib.sha256(raw).hexdigest()})
summary = {
    'schema': 'cho51_collection_qualification_closeout_v1',
    'assembled_utc': datetime.now(timezone.utc).isoformat(),
    'recorder_cases_passed': 20, 'selection_cases_passed': 43, 'total_cases_passed': 63,
    'evidence_class': 'synthetic engineering qualification; no real result or selected tensor',
    'canonical_files_verified': len(manifest['files']),
    'canonical_source_sha256': manifest['source_sha256'],
    'native_attempts': native,
    'retained_prior_failures': ['pytest outside-output logging', 'owned stop of repeated fixture attempt',
                                'selection fixture list passed to mapping-only helper',
                                'selection fixture generated Windows paths beyond MAX_PATH'],
    'independent_static_reviewer': '/root/review_candidates',
    'independent_static_review_imported_or_executed_code': False,
    'root_review_of_fixture_successors': True,
    'original_case_attempts_remaining': 0, 'scientific_admission': False,
    'experiment_freeze_signed': False, 'real_input_composition_qualified': False,
    'selected_publication_or_tensor_qualified': False,
    'artifact_count': len(index),
}
for name, value in (('manifest.json', {'artifacts': index}), ('summary.json', summary)):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
print(json.dumps({'packet': str(OUT), 'artifacts': len(index), 'synthetic_cases_passed': 63,
                  'native_jobs_closed_empty_absent': len(native)}))
