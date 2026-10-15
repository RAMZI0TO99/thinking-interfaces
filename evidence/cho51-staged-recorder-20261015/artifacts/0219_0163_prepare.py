"""Create fresh pins and explicit origin contract; never launch computation."""
from __future__ import annotations

import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata as M

RUN, ROOT = M.RUN, M.ROOT
CANDIDATE = ROOT / 'docs/phase2/cho51_staged_restore_v1'


def main():
    if (RUN / 'pins.json').exists() or (RUN / 'stage-contract.json').exists() or (RUN / 'verification_001').exists():
        raise ValueError('unused stage, contract and pins required')
    origin = M.verify_origin()
    paths = {CANDIDATE / 'restore.py', CANDIDATE / 'README.md'}
    if set(CANDIDATE.iterdir()) != paths:
        raise ValueError('exact staged restore candidate required')
    paths.update(RUN / name for name in ('metadata.py', 'prepare.py', 'runtime.py', 'verify_child.py',
        'observe.py', 'launch.ps1', 'closeout.py'))
    for path in paths:
        if path.suffix == '.py':
            ast.parse(path.read_bytes(), filename=str(path))
    reviewed = {path.relative_to(ROOT).as_posix(): M.old.inspect(path)[1][-1] for path in sorted(paths)}
    review_path = RUN / 'source-review.json'
    review, review_sha = M.document(review_path)
    M.old.fields(review, {'source_only': True, 'files': reviewed, 'remaining_actionable_findings': []})
    contract = M.make_contract(origin)
    M.old.write(RUN / 'stage-contract.json', contract)
    contract_sha = M.old.inspect(RUN / 'stage-contract.json')[1][-1]
    files = dict(origin['pins']['files'])
    files.update(reviewed)
    files[review_path.relative_to(ROOT).as_posix()] = review_sha
    files[(RUN / 'stage-contract.json').relative_to(ROOT).as_posix()] = contract_sha
    # All origin artifacts, including arrays, stay read only and are pinned by
    # the explicit contract. Runtime rehashes them through the frozen verifier.
    for path, sha in origin['files'].items():
        if Path(path).suffix.lower() not in {'.npz', '.npy', '.mat', '.safetensors'}:
            files[Path(path).relative_to(ROOT).as_posix()] = sha
    pins = {'schema': 'cho51_staged_eegnet_restore_pins_v1',
        'prepared_utc': datetime.now(timezone.utc).isoformat(),
        'files': files, 'runtime': origin['pins']['runtime'],
        'canonical_files': 432, 'canonical_source_sha256': M.CANONICAL,
        'predecessor_files': 635, 'predecessor_pins_sha256': M.ORIGIN_PINS_SHA,
        'source_review_path': str(review_path), 'source_review_sha256': review_sha,
        'reviewed_files': reviewed, 'stage_contract_sha256': contract_sha,
        'mne_resource_path': origin['pins']['mne_resource_path'],
        'mne_resource_sha256': origin['pins']['mne_resource_sha256'],
        'seconds': 90, 'process_mib': 2048, 'job_mib': 3072,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20, 'threads': 1,
        'gpu_hidden': True, 'source_training_replayed': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0}
    M.verify_pin_map(pins)
    M.old.write(RUN / 'pins.json', pins)
    print(json.dumps({'source_context_files': len(files), 'runtime_files': len(pins['runtime']),
        'pins_sha256': M.old.inspect(RUN / 'pins.json')[1][-1],
        'stage_contract_sha256': contract_sha, 'origin_input_files': origin['input_files'],
        'origin_modules_rechecked': origin['module_files'], 'launched': False}))


if __name__ == '__main__':
    main()
