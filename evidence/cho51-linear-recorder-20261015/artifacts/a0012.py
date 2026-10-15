"""Authenticate accepted linear publication/restoration without replaying either.

Only pinned standard-library readers are imported. Historical Git provenance is
recorded evidence; mutable resume heads are authenticated through their preserved
export snapshots, never recaptured as historical source authority.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import stat
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
STAGE = ROOT / 'runs/coordination/cho51_linear_publication_20261015_v1'
EXPORT = ROOT / 'evidence/cho51-linear-closeout-export-20261015'
ARCHIVE = ROOT / 'evidence/cho51-linear-publication-20261015'
PINS_SHA = '30130ec6a122323e2504d70645f86d07cc430f587c2bc109d8aae5f125bd99e9'
FINAL_SHA = '9422cb9ab3e660e415c293054f60d00ec9e85e6e82b0612225ba1a4500eccae9'
EXPORT_SHA = '90a29df94bf419f06b6206a5754e8e9d58a32da2691c938b86f6e4959072f04e'
PUBLICATION_SHA = '86d8f400abc6345d18893fc4456152bba20115ac9946ddd1bcbf9109b1528f08'
METADATA_SHA = '26bebd91100aabd504fc433d2574fb71dd76c1a283b37834a3d9ce4c924bde54'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
CASE = '9d3596b5e7653e1708eb208d6b150b86cae02227e6cd73a25e4358e675afc141'
WEIGHTS_SHA = '3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048'
BASELINE_SHA = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
EVIDENCE_SHA = 'e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3'
M = None


def metadata():
    global M
    if M is None:
        path = STAGE / 'metadata.py'
        if hashlib.sha256(path.read_bytes()).hexdigest() != METADATA_SHA:
            raise ValueError('frozen standard-library metadata source changed')
        spec = importlib.util.spec_from_file_location('_linear_recorder_metadata', path)
        M = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = M
        spec.loader.exec_module(M)
    return M


def _asset(path, expected, maximum, *, compact=False):
    """Stable direct single-link bounded byte hash; weights are always streamed."""
    path = Path(path)
    before = path.stat()
    key = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if (path.resolve(strict=True) != path or path.is_symlink() or not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1 or not 0 <= before.st_size <= maximum):
        raise ValueError('direct bounded single-link origin asset required: ' + str(path))
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
            raise ValueError('origin asset has a linked/reparse ancestor')
    hasher, raw, count = hashlib.sha256(), None, 0
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        if compact:
            raw = stream.read(maximum + 1)
            count = len(raw)
            hasher.update(raw)
        else:
            for block in iter(lambda: stream.read(1024**2), b''):
                count += len(block)
                if count > maximum or count > before.st_size:
                    raise ValueError('origin stream exceeded its fixed size/bound')
                hasher.update(block)
        finished = os.fstat(stream.fileno())
    if (key(before) != key(path.stat()) or key(opened) != key(finished)
            or key(before)[:4] != key(opened)[:4] or hasher.hexdigest() != expected
            or count != before.st_size
            or compact and len(raw) != before.st_size):
        raise ValueError('origin physical identity/hash changed: ' + str(path))
    return raw, (*key(before), expected)


def verify_origin_stages():
    """Return exact role-labelled proof inventory and historical reuse summary."""
    m = metadata()
    pins, _ = m.document(STAGE / 'pins.json', expected=PINS_SHA, canonical_raw=True)
    m.need(len(pins['files']) == 1937 and len(pins['runtime']) == 5
           and len(pins['baseline']) == len(pins['selected_weights']) == 1,
           'exact accepted1937/5/1/1 publication pins required')
    m.verify_pin_map(pins, root=ROOT)
    restored = m.verify_restoration_proof(pins, PUBLICATION_SHA, root=ROOT)
    # Detached verification includes an independent full publication audit.
    pub = m.verify_publication_proof(pins, PUBLICATION_SHA, root=ROOT)
    original = restored['origin']
    m.need(len(original['proofs']) == 886 and original['original_case_attempts'] == 0,
           'complete fixed historical chain and exhausted original ledger required')
    final, _ = m.document(STAGE / 'final-review.json', expected=FINAL_SHA, canonical_raw=True)
    m.old.fields(final, {'passed': True, 'metadata_only': True, 'remaining_actionable_findings': [],
        'current_gradient_updates': 0, 'historical_gradient_updates': 5253,
        'original_case_attempts': 0, 'all223_tensors_equal': True,
        'actual_adapter_released': True, 'actual_store_restores': 2,
        'new_staged_store_restore_verified': True, 'unchanged_single_root_factory_verified': False,
        'scientific_admission': False, 'measured_cells': 0})
    files, roles = {}, {}

    def include(path, expected):
        path = Path(path)
        size = path.stat().st_size
        if path.suffix.lower() in {'.npz', '.npy', '.mat', '.fif'}:
            return
        role = ('complete_evidence' if expected == EVIDENCE_SHA and size == 23087023 else
                'selected_weights' if expected == WEIGHTS_SHA and size == 23294624 else
                'baseline_weights' if expected == BASELINE_SHA and size == 23299672 else 'metadata')
        if path.suffix.lower() == '.safetensors' and role not in {'selected_weights', 'baseline_weights'}:
            raise ValueError('only exact accepted selected/baseline weights may be hashed')
        maximum = {'metadata': 8 * 1024**2, 'complete_evidence': 32 * 1024**2,
                   'selected_weights': 64 * 1024**2, 'baseline_weights': 64 * 1024**2}[role]
        _asset(path, expected, maximum)
        if size == 0:
            if path.suffix.lower() not in {'.log', '.txt'} or expected != hashlib.sha256(b'').hexdigest():
                raise ValueError('only verified empty diagnostic logs excluded from transaction')
            return
        name = str(path)
        if name in files and files[name] != expected:
            raise ValueError('origin proof hash conflict')
        files[name], roles[name] = expected, role

    for relative, sha in final['checked_compact_proofs'].items():
        m.need(relative not in m.MUTABLE_HEADS, 'current mutable resume head cannot be an origin hard proof')
        include(m.relative(ROOT, relative), sha)
    for relative, sha in pins['files'].items():
        include(m.relative(ROOT, relative), sha)
    for group in ('baseline', 'selected_weights'):
        for name, sha in pins[group].items():
            include(Path(name) if Path(name).is_absolute() else m.relative(ROOT, name), sha)
    for proof in (pub, restored):
        for name, sha in proof['proofs'].items():
            include(Path(name), sha)
    include(STAGE / 'pins.json', PINS_SHA)
    include(STAGE / 'final-review.json', FINAL_SHA)
    for mode, proof in (('publication', pub), ('restoration', restored)):
        receipt, receipt_sha = m.document(STAGE / (mode + '_001/stage-receipt.json'), canonical_raw=True)
        m.need(receipt['passed'] is True and receipt['pins_sha256'] == PINS_SHA
               and receipt['publication_result_file_sha256'] == PUBLICATION_SHA
               and receipt['native'] == proof['native'] and receipt['proofs'] == proof['proofs'],
               'exact accepted stage closeout receipt required')
        include(STAGE / (mode + '_001/stage-receipt.json'), receipt_sha)
    publication = pub['publication_result']
    for key, sha_key in (('weights_path', 'weights_file_sha256'), ('manifest_path', 'manifest_file_sha256'),
                         ('evidence_path', 'evidence_file_sha256')):
        include(Path(publication[key]), publication[sha_key])
    manifest, manifest_sha = m.document(ARCHIVE / 'manifest.json', canonical_raw=True)
    summary, summary_sha = m.document(ARCHIVE / 'summary.json', canonical_raw=True)
    m.need(len(manifest['artifacts']) == summary['artifacts'] == 51
           and final['artifact_archive']['manifest_sha256'] == manifest_sha
           and final['artifact_archive']['summary_sha256'] == summary_sha,
           'exact accepted flat51-artifact source/archive packet required')
    include(ARCHIVE / 'manifest.json', manifest_sha)
    include(ARCHIVE / 'summary.json', summary_sha)
    for row in manifest['artifacts']:
        for path in (m.relative(ROOT, row['source']), m.relative(ARCHIVE, row['path'])):
            m.need(path.stat().st_size == row['bytes'], 'accepted archive size changed')
            include(path, row['sha256'])
    export, _ = m.document(EXPORT / 'manifest.json', expected=EXPORT_SHA, canonical_raw=True)
    m.need(export['historical_review_sha256'] == FINAL_SHA and len(export['artifacts']) == 8,
           'exact byte-preserved historical review plus seven document snapshots required')
    include(EXPORT / 'manifest.json', EXPORT_SHA)
    for row in export['artifacts']:
        copied = m.relative(EXPORT, row['path'])
        m.need(copied.stat().st_size == row['bytes'], 'preserved document size changed')
        include(copied, row['sha256'])
        if row['document_binding_recorded_in_review']:
            m.need(final['document_bindings'][row['source']] == row['sha256'],
                   'preserved old document does not match accepted review binding')
    for job in final['all_24_scoped_native_jobs_freshly_absent']:
        m.launcher._job_absent(('pro3_migration_' + job) if isinstance(job, str) else job['job_name'])
    result_summary = {
        'engineering_only': True, 'source_work_reused': True, 'restore_work_reused': True,
        'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
        'source_updates': 5151, 'support_updates': 102, 'fold_count': 102, 'final_source_subjects': 51,
        'restore_limits': [64 * 1024**2, 64 * 1024**2], 'restored_tensors': 223,
        'restored_elements': 5818138, 'head_parameters': 402,
        'historical_restore_count': 2, 'current_restore_count': 0, 'target_inference_calls': 0,
        'selected_state_sha256': m.MODEL_STATE, 'weights_file_sha256': WEIGHTS_SHA,
        'manifest_sha256': publication['manifest_sha256'], 'complete_evidence_sha256': m.EVIDENCE,
        'recipe_sha256': m.RECIPE, 'historical_case_id': CASE,
        'historical_source': original['source'], 'historical_plan': original['plan'],
        'staged_two_root_provenance': True, 'unchanged_single_root_factory_verified': False,
        'original_scientific_case_qualified': False,
        'historical_publication_qualified': True, 'historical_detached_restoration_qualified': True,
        'scientific_admission': False,
        'measured_cells': 0, 'original_case_attempts_remaining': 0,
        'publication_result_file_sha256': PUBLICATION_SHA, 'restoration_result_file_sha256': restored['result_sha256'],
        'source_pins_sha256': PINS_SHA, 'accepted_final_review_sha256': FINAL_SHA,
        'historical_export_manifest_sha256': EXPORT_SHA,
    }
    return {'files': dict(sorted(files.items())), 'roles': dict(sorted(roles.items())), 'summary': result_summary}
