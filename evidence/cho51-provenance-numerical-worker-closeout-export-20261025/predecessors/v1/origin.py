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
PREVIOUS = ROOT / 'runs/coordination/cho51_provenance_restore_20261025_v2'
PREVIOUS_PINS_SHA = '4ba8504b7ff1f91f26cdfc721813de8f643c245ab738b04927ca1ee0be0c12dc'
PREVIOUS_ORIGIN_SHA = '97d82f386d963a00d8ac233c1db856290f78de959a24ac04aa2e3c759067206e'
PREVIOUS_FINAL_SHA = '72b6f232d39b5b73e39ee8d56e77c0cba958a03a51854ae73e6863223e9ce627'
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
        spec = importlib.util.spec_from_file_location('_provenance_numerical_historical_origin', path)
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
    previous_pins = document(PREVIOUS / 'pins.json', PREVIOUS_PINS_SHA)
    final = document(PREVIOUS / 'final-review.json', PREVIOUS_FINAL_SHA)
    checks = final.get('executed_checks', {})
    native = final.get('native', {})
    boundary = final.get('accepted_boundary', {})
    need(final.get('passed') is True and final.get('remaining_actionable_findings') == []
         and checks.get('focused_tests') == 65 and checks.get('engineering_successes') == 1
         and checks.get('model_constructions') == checks.get('genuine_adapter_deliveries') == 1
         and checks.get('safe_decodes') == checks.get('strict_state_loads') == 2
         and checks.get('current_source_updates') == checks.get('current_support_updates')
             == checks.get('query_calls') == checks.get('measured_cells') == 0
         and native.get('accepted') is True and native.get('exit_code') == 0
         and native.get('job_closed') is True and native.get('empty_before_close') is True
         and native.get('external_stdlib_closeout_exit_code') == 0
         and native.get('external_stdlib_closeout_reaped') is True
         and boundary.get('g04_separately_versioned_linear_engineering_factory') is True
         and boundary.get('scientific_admission') is False,
         'accepted provenance-aware factory history differs')
    files, roles = dict(base['files']), dict(base['roles'])

    def include(path, expected, size=None):
        path = Path(path)
        path = path if path.is_absolute() else ROOT / path
        need(path.suffix.lower() not in {'.npz', '.npy', '.mat', '.fif', '.safetensors'}
             and path.stat().st_size <= 8 * 1024**2
             and (size is None or path.stat().st_size == size),
             'new factory history must contain bounded metadata only')
        need(digest(path) == expected and (str(path) not in files or files[str(path)] == expected),
             'accepted factory metadata changed or conflicts with an ancestor pin')
        files[str(path)], roles[str(path)] = expected, 'metadata'

    include(PREVIOUS / 'origin.py', PREVIOUS_ORIGIN_SHA)
    include(PREVIOUS / 'pins.json', PREVIOUS_PINS_SHA)
    include(PREVIOUS / 'final-review.json', PREVIOUS_FINAL_SHA)
    for name, row in final['physical_bindings'].items():
        include(ROOT / name, row['sha256'], row['bytes'])
    need(previous_pins['canonical_source_sha256'] == CANONICAL
         and previous_pins['factory_producer']['model_state_sha256'] == predecessor().MODEL_STATE,
         'accepted factory canonical source or selected state differs')

    archive = ROOT / 'evidence/cho51-provenance-restore-20261025-v2'
    manifest_sha = '04276e91f8fd003303246b2cc8e643477e8dd04cebe63d11a22cb13a7259d712'
    manifest = document(archive / 'manifest.json', manifest_sha)
    include(archive / 'manifest.json', manifest_sha)
    need(len(manifest['artifacts']) == 44, 'exact accepted factory execution inventory required')
    expected = {'.gitattributes', 'README.md', 'manifest.json', 'summary.json'}
    for row in manifest['artifacts']:
        source, copied = ROOT / row['source'], archive / row['path']
        need(copied.resolve(strict=True).is_relative_to(archive), 'factory archive path escaped')
        include(source, row['sha256'], row['bytes'])
        include(copied, row['sha256'], row['bytes'])
        expected.add(row['path'])
    include(archive / 'summary.json', 'fba2008d47040f1d22c12dfc610689a11003e8969755c7b8f685df6884b75c1f')
    include(archive / 'README.md', '97348beb7a5cf32d03a175c40f2032ed1ed6008aae401429956f9d065ffbd2a6')
    include(archive / '.gitattributes', '705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da')
    need({path.relative_to(archive).as_posix() for path in archive.rglob('*') if path.is_file()} == expected,
         'accepted factory archive has an unexpected file')

    export = ROOT / 'evidence/cho51-provenance-restore-closeout-export-20261025'
    exported_sha = '64293f61eb383c3fb92449b09a9cab96d70dfbad51740e1d4ee0f3543053e52c'
    exported = document(export / 'manifest.json', exported_sha)
    include(export / 'manifest.json', exported_sha)
    need(exported['final_review_sha256'] == PREVIOUS_FINAL_SHA and len(exported['artifacts']) == 45,
         'exact accepted factory closeout export required')
    expected, bindings = {'.gitattributes', 'README.md', 'manifest.json'}, {}
    for row in exported['artifacts']:
        copied = export / row['path']
        need(copied.resolve(strict=True).is_relative_to(export), 'factory snapshot path escaped')
        include(copied, row['sha256'], row['bytes'])
        expected.add(row['path'])
        if row['document_binding_recorded_in_review']:
            bindings[row['source']] = dict(sha256=row['sha256'], bytes=row['bytes'])
        else:
            include(ROOT / row['source'], row['sha256'], row['bytes'])
    need(bindings == final['documents'] and len(bindings) == 7
         and {path.relative_to(export).as_posix() for path in export.rglob('*') if path.is_file()} == expected
         and set(exported['exact_inventory']) == expected,
         'accepted factory document snapshots or export inventory differ')
    include(export / 'README.md', '6d3388f95a98fb04588760cfc2e50a94303776b9378b90a7e2edac28dce7dfe6')
    include(export / '.gitattributes', '705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da')
    summary = dict(base['summary'], accepted_factory={
        'final_review_sha256': PREVIOUS_FINAL_SHA, 'pins_sha256': PREVIOUS_PINS_SHA,
        'tests': 65, 'restore_count': 1, 'support_updates': 0, 'query_invocations': 0,
        'source_updates': 0, 'measured_cells': 0, 'archive_artifacts': 44,
        'closeout_export_artifacts': 45, 'historical_document_snapshots': 7,
        'runtime_transitions_from_17_october': 21},
        native_names=[*base['summary']['native_names'], '20261025T073014Z_e44f1ff4e4'])
    return {'files': dict(sorted(files.items())), 'roles': dict(sorted(roles.items())), 'summary': summary}
