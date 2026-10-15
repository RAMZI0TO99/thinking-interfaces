"""Pin settled numerical probe sources/runtime with standard-library reads only."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
CANONICAL_SHA256 = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
CONFIG_RELATIVE = '.cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/0563b6c626e7b40d9a36653b763715db94d945d7/config.json'
CONFIG_SHA256 = '813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b'
MNE_RELATIVE = '.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif'
MNE_SHA256 = '0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'
PROBE = ROOT / 'docs/phase2/cho51_numerical_probe_v1'
METHODS = ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import source_check

canonical = source_check(ROOT)
manifest = json.loads((ROOT / 'tools/migration/source-files.json').read_bytes())
if canonical != CANONICAL_SHA256 or len(manifest['files']) != 432:
    raise ValueError('unchanged 432 canonical files required')
prior_path = ROOT / 'runs/coordination/cho51_receipt_selector_20261015_v1/pins.json'
prior = json.loads(prior_path.read_bytes())
if len(prior['files']) != 545:
    raise ValueError('qualified 545-file receipt/selector predecessor required')
files = {relative: digest(ROOT / relative) for relative in prior['files']}
owned = {path for path in PROBE.iterdir() if path.is_file()}
owned.update(RUN.glob('*.py'))
owned.update(RUN.glob('*.ps1'))
reviewed = {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(owned)}
review_path = RUN / 'source-review.json'
review = json.loads(review_path.read_bytes())
if (review.get('source_only') is not True
        or review.get('remaining_actionable_findings') != [] or review.get('files') != reviewed):
    raise ValueError('independent source review must bind every exact settled probe/operational file')
files.update(reviewed)
for relative in (
    '.venv/Lib/site-packages/braindecode/models/labram.py',
    '.venv/Lib/site-packages/braindecode/models/eegnet.py',
    '.venv/Lib/site-packages/urllib3/util/connection.py', CONFIG_RELATIVE, MNE_RELATIVE,
):
    files[relative] = digest(ROOT / relative)
if files[CONFIG_RELATIVE] != CONFIG_SHA256 or files[MNE_RELATIVE] != MNE_SHA256:
    raise ValueError('baseline model configuration or MNE library metadata differs')
if (ROOT / MNE_RELATIVE).stat().st_size != 260:
    raise ValueError('exact 260-byte installed MNE anatomical template required')
files[review_path.relative_to(ROOT).as_posix()] = digest(review_path)
git_command = shutil.which('git')
if git_command is None:
    raise ValueError('pinned installed Git runtime required, although no child Git commands are permitted')
runtime_paths = (
    Path(sys.executable).resolve(strict=True),
    (Path(sys.base_prefix) / 'python.exe').resolve(strict=True),
    (Path(sys.base_prefix) / 'python312.dll').resolve(strict=True),
    (Path(sys.base_prefix) / 'python3.dll').resolve(strict=True),
    Path(git_command).resolve(strict=True),
)
if len(set(runtime_paths)) != 5:
    raise ValueError('five distinct Python/base/DLL/Git runtime paths required')
runtime = {str(path): digest(path) for path in runtime_paths}
pins = {
    'schema': 'cho51_numerical_probe_fresh_pins_v1',
    'prepared_utc': datetime.now(timezone.utc).isoformat(),
    'files': files, 'runtime': runtime, 'canonical_files': 432,
    'canonical_source_sha256': canonical, 'predecessor_files': 545,
    'predecessor_pins_sha256': digest(prior_path),
    'source_review_path': str(review_path), 'source_review_sha256': digest(review_path),
    'reviewed_files': reviewed,
    'model_config_path': str(ROOT / CONFIG_RELATIVE), 'model_config_sha256': CONFIG_SHA256,
    'model_config_bytes': (ROOT / CONFIG_RELATIVE).stat().st_size,
    'mne_resource_path': str(ROOT / MNE_RELATIVE), 'mne_resource_sha256': MNE_SHA256,
    'mne_resource_bytes': 260, 'methods': list(METHODS),
    'seconds_per_method': 300, 'process_mib': 2048, 'job_mib': 3072,
    'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
    'threads': 1, 'gpu_hidden': True, 'random_initialization_only': True,
    'gradient_steps_per_method': 8, 'candidate_rates_per_method': 2,
    'source_batch': 2, 'support_batch': 10, 'query_batch': 2,
    'channels': 64, 'eegnet_samples': 512, 'labram_samples': 800,
    'labram_layers': 12,
    'whole_numerical_worker_verified': False,
    'actual_study_inputs_or_pretrained_weights_permitted': False,
    'scientific_admission': False, 'original_case_attempts_remaining': 0,
}
with (RUN / 'pins.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
print(json.dumps({
    'source_files': len(files), 'runtime_files': len(runtime), 'methods': list(METHODS),
    'gradient_steps_per_method': 8, 'pins_sha256': digest(RUN / 'pins.json'), 'launched': False,
}))
