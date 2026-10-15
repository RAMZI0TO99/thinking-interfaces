"""Pin a reviewed complete synthetic EEGNet lifecycle without importing numerical code."""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
CANDIDATE = ROOT / 'docs/phase2/cho51_complete_eegnet_v2'
PRIOR = ROOT / 'runs/coordination/cho51_complete_eegnet_20261015_v3/pins.json'
PRIOR_SHA256 = '5e551c2e90289eef299e96095c5f7c7fba4ed4629d5a895fbcad2ba58d36bc84'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
DESIGN = ROOT / 'docs/phase2/cho_design_decisions_20261012.json'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import source_check

if source_check(ROOT) != CANONICAL or digest(PRIOR) != PRIOR_SHA256:
    raise ValueError('unchanged canonical source and exact prior tested pins required')
prior = json.loads(PRIOR.read_bytes())
if len(prior['files']) != 620 or len(prior['runtime']) != 5:
    raise ValueError('exact 620-source/five-runtime predecessor required')
for relative, expected in prior['files'].items():
    if digest(ROOT / relative) != expected:
        raise ValueError('tested predecessor source changed: ' + relative)
paths = {CANDIDATE / name for name in ('inputs.py', 'transaction.py', 'test_transaction.py', 'selection.py', 'README.md')}
if set(CANDIDATE.iterdir()) != paths:
    raise ValueError('exact five-file reviewed candidate required')
paths.update(RUN.glob('*.py'))
paths.update(RUN.glob('*.ps1'))
reviewed = {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(paths)}
if len(reviewed) != 12 or not (RUN / 'closeout.py').is_file():
    raise ValueError('all five candidate and seven operational sources including closeout required')
review_path = RUN / 'source-review.json'
review = json.loads(review_path.read_bytes())
if (review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
        or review.get('files') != reviewed):
    raise ValueError('independent exact settled-source review required')
design = json.loads(DESIGN.read_bytes())
rows = [row for row in design['adopted_design']['candidate_template']['methods'] if row['method'] == 'eegnet']
if len(rows) != 1:
    raise ValueError('one owner-adopted EEGNet method row required')
method_config = rows[0]
expected_candidates = [{'name': name,
    'source': {'batch_size': 4, 'input_scale': 1000000.0, 'learning_rate': rate, 'steps_per_subject': 1},
    'support': {'input_scale': 1000000.0, 'learning_rate': rate, 'query_batch_size': 8, 'steps': 1}}
    for name, rate in (('lr_1e-3', 0.001), ('lr_2e-3', 0.002))]
if (method_config.get('dataset') != 'cho2017' or method_config.get('method') != 'eegnet'
        or method_config.get('input_profile') != 'cho_profile_a'
        or method_config.get('variant_config_sha256') is not None
        or method_config.get('candidates') != expected_candidates):
    raise ValueError('exact adopted EEGNet two-candidate settings required')
method_path = RUN / 'method-config.json'
method_raw = (canonical(method_config) + '\n').encode('utf-8')
if (review.get('expected_method_config_sha256') != hashlib.sha256(canonical(method_config).encode()).hexdigest()
        or review.get('expected_method_config_file_sha256') != hashlib.sha256(method_raw).hexdigest()
        or review.get('design_decision_sha256') != digest(DESIGN)):
    raise ValueError('independent review must bind exact adopted design and derived method configuration bytes')
with method_path.open('xb') as stream:
    stream.write(method_raw)
files = dict(prior['files'])
files.update(reviewed)
files[PRIOR.relative_to(ROOT).as_posix()] = PRIOR_SHA256
for path in (review_path, DESIGN, method_path):
    files[path.relative_to(ROOT).as_posix()] = digest(path)
git = shutil.which('git')
if git is None:
    raise ValueError('pinned installed Git required')
runtime = {str(path): digest(path) for path in (
    Path(sys.executable).resolve(strict=True), (Path(sys.base_prefix) / 'python.exe').resolve(strict=True),
    (Path(sys.base_prefix) / 'python312.dll').resolve(strict=True),
    (Path(sys.base_prefix) / 'python3.dll').resolve(strict=True), Path(git).resolve(strict=True))}
if runtime != prior['runtime'] or len(runtime) != 5:
    raise ValueError('tested runtime changed')
test_path = CANDIDATE / 'test_transaction.py'
test_nodes, expected_tests = [], 0
for node in ast.parse(test_path.read_bytes()).body:
    if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
        count = 1
        for mark in node.decorator_list:
            if isinstance(mark, ast.Call) and isinstance(mark.func, ast.Attribute) and mark.func.attr == 'parametrize':
                if not isinstance(mark.args[1], (ast.List, ast.Tuple)):
                    raise ValueError('literal test parameter inventory required')
                count *= len(mark.args[1].elts)
        test_nodes.append(test_path.relative_to(ROOT).as_posix() + '::' + node.name)
        expected_tests += count
if not test_nodes or not 20 <= expected_tests <= 35:
    raise ValueError('reviewed focused 20..35 boundary checks required')
pins = {'schema': 'cho51_complete_eegnet_fresh_pins_v1',
    'prepared_utc': datetime.now(timezone.utc).isoformat(), 'files': files, 'runtime': runtime,
    'canonical_files': 432, 'canonical_source_sha256': CANONICAL,
    'predecessor_files': 620, 'predecessor_pins_sha256': PRIOR_SHA256,
    'source_review_path': str(review_path), 'source_review_sha256': digest(review_path),
    'reviewed_files': reviewed, 'design_decision_path': str(DESIGN), 'design_decision_sha256': digest(DESIGN),
    'method_config_path': str(method_path), 'method_config_file_sha256': digest(method_path),
    'method_config_sha256': hashlib.sha256(canonical(method_config).encode()).hexdigest(),
    'owner_decision_sha256': prior['owner_decision_sha256'],
    'mne_resource_path': prior['mne_resource_path'], 'mne_resource_sha256': prior['mne_resource_sha256'],
    'mne_resource_bytes': 260, 'outer_seconds': 600, 'process_mib': 4096, 'job_mib': 6144,
    'source_seconds': 420, 'source_process_mib': 3072, 'source_job_mib': 4096,
    'detached_seconds': 90, 'detached_process_mib': 2048, 'detached_job_mib': 3072,
    'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20, 'threads': 1, 'gpu_hidden': True,
    'actual_gradient_updates': 5253, 'source_updates': 5151, 'support_updates': 102,
    'fold_count': 102, 'final_source_subjects': 51,
    'source_subjects_available': 52, 'channels': 64, 'samples': 512,
    'test_nodes': test_nodes, 'expected_tests': expected_tests,
    'full_scientific_worker_verified': False, 'scientific_admission': False,
    'original_case_attempts_remaining': 0}
with (RUN / 'pins.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
print(json.dumps({'source_files': len(files), 'runtime_files': len(runtime),
    'expected_tests': expected_tests, 'pins_sha256': digest(RUN / 'pins.json'), 'launched': False}))
