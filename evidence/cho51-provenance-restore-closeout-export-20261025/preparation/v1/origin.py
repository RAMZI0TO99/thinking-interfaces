"""Authenticate immutable accepted history without executing used launchers."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
PREVIOUS = ROOT / 'runs/coordination/cho51_linear_numerical_worker_20261017_v1'
PREVIOUS_PINS_SHA = '79282282a386d23cd13bf757642631719dfffd38b6eb75f44f6628f552046fa7'
PREVIOUS_ORIGIN_SHA = 'eef311844ab74d7479da439679922e59d664f6a45d8beedc4d79078667a0fd86'
PREVIOUS_FINAL_SHA = '552ccba9a3a03db99be81f21093c6c3ceb8dd21ae1c91767619f9c97063f4fd1'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
MODULE = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(path):
    path = Path(path)
    before = path.stat()
    key = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    git_exception = path == Path('C:/Users/aladdin-alyanai/AppData/Local/Programs/Git/cmd/git.exe') and before.st_nlink == 2 and before.st_size == 46480
    need(path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode) and (before.st_nlink == 1 or git_exception)
         and 0 <= before.st_size <= 512 * 1024**2, 'direct bounded pinned file required')
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 1024,
             'linked pinned-file ancestor refused')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        hasher, count = hashlib.sha256(), 0
        while True:
            chunk = stream.read(min(1024**2, before.st_size + 1 - count))
            if not chunk:
                break
            count += len(chunk)
            need(count <= before.st_size, 'pinned file exceeded fixed read bound')
            hasher.update(chunk)
        value = hasher.hexdigest()
        finished = os.fstat(stream.fileno())
    need(count == before.st_size and key(before) == key(path.stat()) and key(opened) == key(finished) and key(before)[:4] == key(opened)[:4],
         'physical pinned identity changed')
    need(not git_exception or value == 'da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f',
         'exact unchanged two-link Git exception differs')
    return value


def identity(path):
    path = Path(path)
    before = path.stat()
    value = digest(path)
    after = path.stat()
    key = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    need(key(before) == key(after), 'physical proof changed')
    return (*key(after), value)


def document(path, expected=None, maximum=8 * 1024**2):
    path = Path(path)
    before = identity(path)
    need(before[2] <= maximum and (expected is None or before[-1] == expected), 'bounded JSON hash differs')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(before[2] + 1)
        finished = os.fstat(stream.fileno())
    key = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    need(key(opened) == key(finished) and key(opened)[:4] == before[:4], 'JSON handle identity changed')
    need(identity(path) == before and len(raw) == before[2] and hashlib.sha256(raw).hexdigest() == before[-1],
         'JSON changed during bounded read')
    def unique(rows):
        value = {}
        for name, item in rows:
            need(name not in value, 'duplicate JSON key')
            value[name] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def predecessor():
    global MODULE
    if MODULE is None:
        path = PREVIOUS / 'origin.py'
        need(digest(path) == PREVIOUS_ORIGIN_SHA, 'accepted origin changed')
        with path.open('rb') as stream:
            raw = stream.read(1024**2 + 1)
        need(len(raw) <= 1024**2, 'historical origin source exceeds fixed read bound')
        need(hashlib.sha256(raw).hexdigest() == PREVIOUS_ORIGIN_SHA, 'accepted origin read changed')
        spec = importlib.util.spec_from_file_location('_provenance_factory_historical_origin', path)
        MODULE = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = MODULE
        exec(compile(raw, str(path), 'exec', dont_inherit=True), MODULE.__dict__)
    return MODULE


def __getattr__(name):
    return getattr(predecessor(), name)


def original_inventory():
    return predecessor().original_inventory()


def verify_inputs():
    return predecessor().verify_inputs()


def verify_origin_stages(*, verify_physical_inputs=True):
    base = predecessor().verify_origin_stages(verify_physical_inputs=verify_physical_inputs)
    pins = document(PREVIOUS / 'pins.json', PREVIOUS_PINS_SHA)
    final = document(PREVIOUS / 'final-review.json', PREVIOUS_FINAL_SHA)
    need(final['passed'] is True and final['remaining_actionable_findings'] == []
         and final['engineering_successes'] == final['current_restore_count'] == final['current_support_updates'] == 1
         and final['measured_cells'] == final['current_source_updates'] == 0
         and final['tests_passed_once_in_accepted_worker'] == 38,
         'accepted numerical-worker history differs')
    files, roles = dict(base['files']), dict(base['roles'])
    def include(path, value):
        path = Path(path)
        path = path if path.is_absolute() else ROOT / path
        need(path.suffix.lower() not in {'.npz', '.npy', '.mat', '.fif', '.safetensors'},
             'new numerical history stage is metadata only')
        need(digest(path) == value and (str(path) not in files or files[str(path)] == value),
             'accepted historical metadata changed')
        files[str(path)], roles[str(path)] = value, 'metadata'
    include(PREVIOUS / 'final-review.json', PREVIOUS_FINAL_SHA)
    include(PREVIOUS / 'pins.json', PREVIOUS_PINS_SHA)
    for group in ('current_own_proofs', 'current_archive_proofs'):
        for path, value in final[group].items():
            include(path, value)
    archive = ROOT / 'evidence/cho51-linear-numerical-worker-20261017-v1'
    manifest = document(archive / 'manifest.json', '668fc8e30887fa045e113ed6e12e31e7cf0c3d6934182c6682d09268750de2b4')
    expected = {'.gitattributes', 'README.md', 'manifest.json', 'summary.json'}
    need(len(manifest['artifacts']) == 39, 'exact numerical historical archive inventory required')
    for row in manifest['artifacts']:
        first, second = ROOT / row['source'], archive / row['path']
        need(first.stat().st_size == second.stat().st_size == row['bytes'], 'historical archive size differs')
        include(first, row['sha256'])
        include(second, row['sha256'])
        expected.add(row['path'])
    need({path.relative_to(archive).as_posix() for path in archive.rglob('*') if path.is_file()} == expected,
         'unexpected accepted numerical archive artifact')
    export = ROOT / 'evidence/cho51-linear-numerical-worker-closeout-export-20261017'
    export_sha = 'd3e479dd3c6bceac485c4bdf9f5217ae3cfb3957a166343817796fc6424acabc'
    exported = document(export / 'manifest.json', export_sha)
    include(export / 'manifest.json', export_sha)
    need(exported['historical_review_sha256'] == PREVIOUS_FINAL_SHA and len(exported['artifacts']) == 8,
         'exact accepted numerical documentation export required')
    expected, bindings = {'.gitattributes', 'README.md', 'manifest.json'}, {}
    for row in exported['artifacts']:
        path = export / row['path']
        need(path.resolve(strict=True).is_relative_to(export) and path.stat().st_size == row['bytes'],
             'historical documentation path or size differs')
        include(path, row['sha256'])
        expected.add(row['path'])
        if row['document_binding_recorded_in_review']:
            bindings[row['source']] = row['sha256']
    need(bindings == final['documents'] == final['document_bindings'] and len(bindings) == 7
         and {path.relative_to(export).as_posix() for path in export.rglob('*') if path.is_file()} == expected,
         'historical snapshot bindings differ')
    include(export / 'README.md', exported['explanatory_readme']['sha256'])
    include(export / '.gitattributes', '705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da')
    summary = dict(base['summary'], accepted_numerical_worker={
        'final_review_sha256': PREVIOUS_FINAL_SHA, 'pins_sha256': PREVIOUS_PINS_SHA,
        'tests': 38, 'restore_count': 1, 'support_updates': 1, 'query_invocations': 1, 'query_trials': 2,
        'source_updates': 0, 'measured_cells': 0, 'archive_artifacts': 39, 'historical_document_snapshots': 7},
        native_names=[*base['summary']['native_names'], '20261017T123933Z_55987a07c7'])
    return {'files': dict(sorted(files.items())), 'roles': dict(sorted(roles.items())), 'summary': summary}
