"""Create fresh exact source/runtime pins for bounded public synthetic folds."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
CANDIDATE = ROOT / 'docs/phase2/cho51_source_fold_probe_v1'
PRIOR = ROOT / 'runs/coordination/cho51_worker_lifecycle_20261015_v1/pins.json'
PRIOR_SHA256 = '20a808c269e6de2c6fd7355749438c80f7198e48946753d0db63308a1a72d3a1'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
METHODS = ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import source_check

if source_check(ROOT) != CANONICAL:
    raise ValueError('unchanged canonical source required')
manifest = json.loads((ROOT / 'tools/migration/source-files.json').read_bytes())
if len(manifest['files']) != 432 or digest(PRIOR) != PRIOR_SHA256:
    raise ValueError('exact canonical manifest and tested lifecycle predecessor required')
prior = json.loads(PRIOR.read_bytes())
if len(prior.get('files', {})) != 574 or len(prior.get('runtime', {})) != 5:
    raise ValueError('exact 574-source/five-runtime predecessor required')
for relative, expected in prior['files'].items():
    if digest(ROOT / relative) != expected:
        raise ValueError('tested predecessor source changed: ' + relative)
candidate_paths = {CANDIDATE / name for name in ('fixture.py', 'probe.py', 'README.md')}
if set(CANDIDATE.iterdir()) != candidate_paths:
    raise ValueError('exact three-file source-fold candidate required')
owned = candidate_paths | set(RUN.glob('*.py')) | set(RUN.glob('*.ps1'))
if not (RUN / 'closeout.py').is_file():
    raise ValueError('reviewed closeout source must precede pin creation')
reviewed = {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(owned)}
review_path = RUN / 'source-review.json'
review = json.loads(review_path.read_bytes())
if (review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
        or review.get('files') != reviewed):
    raise ValueError('independent exact settled-source review required')
files = dict(prior['files'])
files.update(reviewed)
files[PRIOR.relative_to(ROOT).as_posix()] = PRIOR_SHA256
files[review_path.relative_to(ROOT).as_posix()] = digest(review_path)
git_command = shutil.which('git')
if git_command is None:
    raise ValueError('pinned installed Git required for owned fixture provenance')
runtime_paths = (
    Path(sys.executable).resolve(strict=True),
    (Path(sys.base_prefix) / 'python.exe').resolve(strict=True),
    (Path(sys.base_prefix) / 'python312.dll').resolve(strict=True),
    (Path(sys.base_prefix) / 'python3.dll').resolve(strict=True),
    Path(git_command).resolve(strict=True),
)
runtime = {str(path): digest(path) for path in runtime_paths}
if len(runtime) != 5 or runtime != prior['runtime']:
    raise ValueError('tested Python/base/DLL/Git runtime changed')
pins = {
    'schema': 'cho51_source_fold_fresh_pins_v1',
    'prepared_utc': datetime.now(timezone.utc).isoformat(),
    'files': files, 'runtime': runtime, 'canonical_files': 432,
    'canonical_source_sha256': CANONICAL, 'predecessor_files': 574,
    'predecessor_pins_sha256': PRIOR_SHA256,
    'source_review_path': str(review_path), 'source_review_sha256': digest(review_path),
    'reviewed_files': reviewed,
    'model_config_path': prior['model_config_path'],
    'model_config_sha256': prior['model_config_sha256'],
    'model_config_bytes': prior['model_config_bytes'],
    'mne_resource_path': prior['mne_resource_path'],
    'mne_resource_sha256': prior['mne_resource_sha256'], 'mne_resource_bytes': 260,
    'methods': list(METHODS), 'seconds_per_method': 600,
    'process_mib': 4096, 'job_mib': 5120,
    'owner_decision_sha256': prior['owner_decision_sha256'],
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
with (RUN / 'pins.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
print(json.dumps({'source_files': len(files), 'runtime_files': len(runtime),
    'methods': list(METHODS), 'gradient_steps_per_method': 51,
    'pins_sha256': digest(RUN / 'pins.json'), 'launched': False}))
