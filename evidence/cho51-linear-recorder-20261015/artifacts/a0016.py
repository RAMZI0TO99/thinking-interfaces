"""Create reviewed staged-recorder pins and a compact origin contract; no computation."""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_recorder_v1'
PRIOR = ROOT / 'runs/coordination/cho51_linear_publication_20261015_v1/pins.json'
PRIOR_SHA = '30130ec6a122323e2504d70645f86d07cc430f587c2bc109d8aae5f125bd99e9'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def write_once(path, raw):
    import os
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    if any((RUN / name).exists() for name in ('pins.json', 'origin-contract.json', 'validation_001')):
        raise ValueError('unused staged recorder output and contracts required')
    if digest(PRIOR) != PRIOR_SHA:
        raise ValueError('exact frozen predecessor pins required')
    prior = json.loads(PRIOR.read_bytes())
    if len(prior['files']) != 1937 or len(prior['runtime']) != 5:
        raise ValueError('exact frozen linear publication predecessor1937/5 required')
    for relative, sha in prior['files'].items():
        if digest(ROOT / relative) != sha:
            raise ValueError('frozen predecessor source/context changed: ' + relative)
    for path, sha in prior['runtime'].items():
        if digest(path) != sha:
            raise ValueError('frozen predecessor runtime changed: ' + path)
    candidates = {CANDIDATE / name for name in ('transaction.py', 'test_transaction.py', 'README.md')}
    if set(CANDIDATE.iterdir()) != candidates:
        raise ValueError('exact three-file staged recorder candidate required')
    operations = {RUN / name for name in ('runtime.py', 'parent.py', 'prepare.py', 'launch.ps1',
        'observe.py', 'origin.py', 'closeout.py')}
    paths = candidates | operations
    for path in paths:
        if path.suffix == '.py':
            ast.parse(path.read_bytes(), filename=str(path))
    reviewed = {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(paths)}
    if len(reviewed) != 10:
        raise ValueError('exact three candidate and seven operational sources required')
    review_path = RUN / 'source-review.json'
    review = json.loads(review_path.read_bytes())
    if (review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
            or review.get('files') != reviewed):
        raise ValueError('independent exact settled staged recorder source review required')
    test_path = CANDIDATE / 'test_transaction.py'
    test_nodes, expected_tests = [], 0
    for node in ast.parse(test_path.read_bytes()).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            count = 1
            for mark in node.decorator_list:
                if isinstance(mark, ast.Call) and isinstance(mark.func, ast.Attribute) and mark.func.attr == 'parametrize':
                    if len(mark.args) < 2 or not isinstance(mark.args[1], (ast.List, ast.Tuple)):
                        raise ValueError('literal test parameter inventory required')
                    count *= len(mark.args[1].elts)
            test_nodes.append(test_path.relative_to(ROOT).as_posix() + '::' + node.name)
            expected_tests += count
    if not test_nodes or not 20 <= expected_tests <= 80:
        raise ValueError('reviewed focused20..80 transaction boundary checks required')
    sys.path.insert(0, str(RUN))
    import origin
    verified = origin.verify_origin_stages()
    if set(verified) != {'files', 'roles', 'summary'}:
        raise ValueError('exact read-only origin stages result required')
    contract = dict(schema='cho51_linear_recorder_origin_contract_v1', **verified)
    contract_raw = encoded(contract)
    contract_sha = hashlib.sha256(contract_raw).hexdigest()
    contract_path = RUN / 'origin-contract.json'
    files = dict(prior['files'])
    files.update(reviewed)
    files[PRIOR.relative_to(ROOT).as_posix()] = PRIOR_SHA
    files[review_path.relative_to(ROOT).as_posix()] = digest(review_path)
    files[contract_path.relative_to(ROOT).as_posix()] = contract_sha
    for absolute, sha in verified['files'].items():
        path = Path(absolute)
        if verified['roles'][absolute] == 'metadata':
            files[path.relative_to(ROOT).as_posix()] = sha
    original_pins = json.loads((ROOT / 'runs/coordination/cho51_complete_eegnet_20261015_v4/pins.json').read_bytes())
    pins = {'schema': 'cho51_linear_recorder_pins_v1',
        'prepared_utc': datetime.now(timezone.utc).isoformat(),
        'files': files, 'runtime': prior['runtime'], 'baseline': prior['baseline'],
        'selected_weights': prior['selected_weights'],
        'canonical_files': 432, 'canonical_source_sha256': CANONICAL,
        'predecessor_files': 1937, 'predecessor_pins_sha256': PRIOR_SHA,
        'source_review_path': str(review_path), 'source_review_sha256': digest(review_path),
        'reviewed_files': reviewed, 'origin_contract_file_sha256': contract_sha,
        'owner_decision_sha256': original_pins['owner_decision_sha256'],
        'mne_resource_path': prior['mne_resource_path'], 'mne_resource_sha256': prior['mne_resource_sha256'],
        'seconds': 600, 'process_mib': 4096, 'job_mib': 5120,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20, 'threads': 1,
        'gpu_hidden': True, 'source_training_replayed': False,
        'current_gradient_updates': 0, 'historical_gradient_updates': 5253,
        'test_nodes': test_nodes, 'expected_tests': expected_tests,
        'scientific_admission': False, 'original_case_attempts_remaining': 0}
    if origin.verify_origin_stages() != verified:
        raise ValueError('origin metadata changed during independent contract construction')
    write_once(contract_path, contract_raw)
    write_once(RUN / 'pins.json', encoded(pins))
    print(json.dumps({'source_context_files': len(files), 'runtime_files': len(pins['runtime']),
        'expected_tests': expected_tests, 'pins_sha256': digest(RUN / 'pins.json'),
        'origin_contract_file_sha256': contract_sha, 'origin_compact_files': len(verified['files']),
        'launched': False}))


if __name__ == '__main__':
    main()
