"""Authenticate historical source/recorder bytes without recapturing historical Git.

This module is standard-library only. Every asset has an explicit role and byte
bound; checkpoint hashes stream bytes and never decode headers or tensors.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
RECORDER = ROOT / 'runs/coordination/cho51_linear_recorder_20261015_v2'
PUBLICATION = ROOT / 'runs/coordination/cho51_linear_publication_20261015_v1'
FINAL_SHA = 'c0015efe2be930cef2c147ebd69be53a42a69e91f30102fda6beba48fbae50eb'
PINS_SHA = '82abad27bd40af689a81d99b8310402dc9d1b2f1ff14242d0236f71720fabbd7'
ORIGIN_SHA = '6cd400d6c24db1ca8de7576b97fa3925cb89ffa975c3ca03a95412ca600247b4'
EXPORT = ROOT / 'evidence/cho51-linear-recorder-closeout-export-20261015'
EXPORT_SHA = '5c99a3b6c50780c61a30a3d4e64a4cc0aa0fac0b1659cbaf30ed5b2ca1f95e06'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
CASE = '9d3596b5e7653e1708eb208d6b150b86cae02227e6cd73a25e4358e675afc141'
WEIGHTS_SHA = '3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048'
BASELINE_SHA = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
EVIDENCE_SHA = 'e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3'
MODEL_STATE = '8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'
CURRENT_COMMIT = '3ef0c395d6bc4abf82633cf746708434a79c18b4'
SOURCE_CONTEXT = '9c2e6ad444c44309f9d4becda2909fba0d2fe315f047560f9adbce56397c9299'
HISTORICAL_COMMIT = '4491e2a68126d6b7293261f4954b88c11c29049d'
TRANSITION = ROOT / 'runs/coordination/cho51_linear_target_transition_20261017_v1/runtime-transition.json'
TRANSITION_SHA = 'a6ebb4269219d023f28e79c07870b6979b466e7c2f978bcfa4c7983603c9e5d4'
CONFIGS = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
           'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def asset(path, expected, maximum, *, compact=False):
    path = Path(path)
    before = path.stat()
    key = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    need(path.resolve(strict=True) == path and not path.is_symlink()
         and stat.S_ISREG(before.st_mode) and before.st_nlink == 1
         and 0 <= before.st_size <= maximum, 'direct bounded single-link origin asset required: ' + str(path))
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 1024,
             'linked/reparse asset ancestor refused')
    hasher, raw, count = hashlib.sha256(), None, 0
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        if compact:
            raw = stream.read(maximum + 1)
            count = len(raw)
            hasher.update(raw)
        else:
            while True:
                block = stream.read(min(1024**2, maximum + 1 - count))
                if not block:
                    break
                count += len(block)
                need(count <= maximum and count <= before.st_size, 'origin stream size exceeded')
                hasher.update(block)
        finished = os.fstat(stream.fileno())
    need(key(before) == key(path.stat()) and key(opened) == key(finished)
         and key(before)[:4] == key(opened)[:4] and count == before.st_size
         and hasher.hexdigest() == expected, 'origin physical bytes/identity changed: ' + str(path))
    return raw, (*key(before), expected)


def document(path, expected=None):
    path = Path(path)
    if expected is None:
        before = path.stat()
        need(path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode)
             and before.st_nlink == 1 and 0 < before.st_size <= 8*1024**2,
             'bounded observed JSON required')
        with path.open('rb') as stream:
            raw = stream.read(8*1024**2+1)
        need(len(raw) == before.st_size and len(raw) <= 8*1024**2,
             'observed JSON grew or shrank')
        expected = hashlib.sha256(raw).hexdigest()
    raw, pin = asset(path, expected, 8 * 1024**2, compact=True)
    def unique(rows):
        result = {}
        for name, value in rows:
            need(name not in result, 'duplicate JSON key')
            result[name] = value
        return result
    value = json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    need(type(value) is dict, 'JSON object required')
    return value


def original_inventory():
    previous = document(PUBLICATION / 'origin-contract.json',
        '8bffd0d8be4f8ed2b87189ec0f36462303b88c627b1a8115c7651805a8a5c20b')
    root = Path(previous['fixture_root'])
    need(root == ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture'
         and len(previous['original_input_files']) == 213, 'fixed original input root and213 inventory required')
    return previous, root, previous['original_input_files']


def verify_inputs():
    previous, fixture, inputs = original_inventory()
    actual = {path.relative_to(fixture).as_posix() for name in ('configs', 'data')
              for path in (fixture / name).rglob('*') if path.is_file()}
    need(actual == set(inputs) and sum(row['size_bytes'] for row in inputs.values()) == 734579463,
         'original exact213/734579463 input inventory required')
    for relative, row in inputs.items():
        path = fixture / relative
        need(path.stat().st_size == row['size_bytes'], 'original input size changed')
        asset(path, row['sha256'], 16 * 1024**2)
    return {'files': 213, 'bytes': 734579463, 'fixture_root': str(fixture),
            'input_identity_file_sha256': previous['input_identity_file_sha256']}


def verify_origin_stages(*, verify_physical_inputs=True):
    """Authenticate the complete accepted recorder audit and preserved documents.

    Frozen final review binds prior proof maps. Mutable heads are represented by
    preserved export snapshots, never compared with today's document bytes.
    """
    final = document(RECORDER / 'final-review.json', FINAL_SHA)
    need(final['passed'] is True and final['metadata_only'] is True
         and final['remaining_actionable_findings'] == [] and final['recorder_integration_qualified'] is True
         and final['tests_passed_once_in_accepted_v2'] == 73 and final['engineering_successes'] == 1
         and final['measured_cells'] == 0 and final['current_gradient_updates'] == 0
         and final['current_restore_count'] == 0 and final['target_inference_calls'] == 0
         and final['verified_origin_files'] == 2004, 'accepted frozen recorder final review required')
    pins = document(RECORDER / 'pins.json', PINS_SHA)
    contract = document(RECORDER / 'origin-contract.json', ORIGIN_SHA)
    need(len(pins['files']) == 2045 and len(pins['runtime']) == 5
         and contract['files'] == final['origin_files'] and contract['roles'] == final['origin_roles'],
         'exact2045/5 recorder pins and2004 role-bound origin required')
    files, roles = {}, {}
    def include(path, sha):
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        size = path.stat().st_size
        role = ('complete_evidence' if sha == EVIDENCE_SHA and size == 23087023 else
                'selected_weights' if sha == WEIGHTS_SHA and size == 23294624 else
                'baseline_weights' if sha == BASELINE_SHA and size == 23299672 else 'metadata')
        need(path.suffix.lower() not in {'.npz', '.npy', '.mat', '.fif'} or size == 260,
             'signal arrays excluded from metadata origin contract')
        need(path.suffix.lower() != '.safetensors' or role in {'selected_weights','baseline_weights'},
             'unknown checkpoint forbidden')
        maximum = {'metadata':8*1024**2,'complete_evidence':32*1024**2,
                   'selected_weights':64*1024**2,'baseline_weights':64*1024**2}[role]
        asset(path, sha, maximum)
        need(str(path) not in files or files[str(path)] == sha, 'origin hash conflict')
        files[str(path)], roles[str(path)] = sha, role
    # Every checked proof is authenticated once. No historical numerical replay.
    for group in ('checked_compact_proofs', 'large_complete_evidence_proofs', 'current_own_proofs',
                  'current_archive_proofs', 'preserved_v1_own_proofs', 'preserved_v1_archive_proofs',
                  'verified_empty_diagnostic_metadata'):
        for path, sha in final[group].items():
            include(path, sha)
    for path, sha in contract['files'].items():
        include(path, sha)
    for path, sha in pins['files'].items():
        include(path, sha)
    include(RECORDER / 'pins.json', PINS_SHA)
    include(RECORDER / 'origin-contract.json', ORIGIN_SHA)
    include(RECORDER / 'final-review.json', FINAL_SHA)
    transition = document(TRANSITION, TRANSITION_SHA)
    need(transition['changed_file_count']==21 and transition['historical_union_files']==2369
         and transition['historical_pins_sha256']==PINS_SHA
         and transition['historical_qualification_sha256']=='2a8394630cf700b600d757d1af3523769d0300b8f529a2fc60ecebaef64e4b18'
         and transition['historical_recorder_final_review_sha256']==FINAL_SHA
         and transition['replacement_cause_verified'] is False and transition['abi_compatibility_verified'] is False,
         'independent bounded observed runtime transition required')
    include(TRANSITION, TRANSITION_SHA)
    exported = document(EXPORT / 'manifest.json', EXPORT_SHA)
    need(exported['historical_review_sha256'] == FINAL_SHA and len(exported['artifacts']) == 8,
         'frozen recorder review and seven snapshots required')
    include(EXPORT / 'manifest.json', EXPORT_SHA)
    for row in exported['artifacts']:
        copied = EXPORT / row['path']
        need(copied.resolve(strict=True).is_relative_to(EXPORT) and copied.stat().st_size == row['bytes'],
             'recorder snapshot path/size changed')
        include(copied, row['sha256'])
        if row['document_binding_recorded_in_review']:
            need(final['document_bindings'][row['source']] == row['sha256'], 'snapshot review binding changed')
    accepted = final['accepted_archive']
    need(accepted['artifacts'] == 37 and accepted['manifest_sha256'] ==
         '23a93c2b4bfcecfdbc3dfe0fcd4113949f2ae65e1222c242be1e73e4b8fe4840', 'exact37 recorder archive required')
    previous, fixture, inventory = original_inventory()
    input_audit = verify_inputs() if verify_physical_inputs else None
    historical = {'git_commit':HISTORICAL_COMMIT,'source_sha256':SOURCE_CONTEXT,'git_dirty':True}
    current = {'git_commit':CURRENT_COMMIT,'source_sha256':SOURCE_CONTEXT,'git_dirty':True}
    need(previous['source'] == final['historical_source'] == historical
         and final['current_control_source']['git_commit'] == '277d7975ba400a9927bdd3e1495f6ade25ddea38',
         'source4491 and recorder277 contexts must remain distinct history')
    summary = dict(contract['summary'], accepted_recorder_final_review_sha256=FINAL_SHA,
        accepted_recorder_pins_sha256=PINS_SHA, accepted_recorder_origin_sha256=ORIGIN_SHA,
        accepted_recorder_engineering_successes=1, historical_source=historical,
        recorder_control_source=final['current_control_source'], expected_current_context=current,
        original_input_root=str(fixture), input_audit=input_audit,
        native_names=final['all_26_scoped_native_job_names_freshly_absent'])
    return {'files':dict(sorted(files.items())), 'roles':dict(sorted(roles.items())), 'summary':summary}
