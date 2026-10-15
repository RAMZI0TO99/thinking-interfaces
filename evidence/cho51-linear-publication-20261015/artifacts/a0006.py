"""Authenticate and preserve each zero-training stage; archive only current metadata."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(RUN))
sys.path.insert(0, str(ROOT))
import metadata as M


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_once(path, value):
    raw = encoded(value)
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('publication', 'restoration'), required=True)
    parser.add_argument('--expect-pins', required=True)
    parser.add_argument('--expect-publication-result', required=True)
    args = parser.parse_args()
    pins_path = RUN / 'pins.json'
    if digest(pins_path) != args.expect_pins:
        raise ValueError('exact independent staged bundle pin required')
    pins = json.loads(pins_path.read_bytes())
    M.verify_pin_map(pins, root=ROOT)
    pub = M.verify_publication_proof(pins, args.expect_publication_result, root=ROOT)
    publication_path = RUN / 'publication_001/publication-result.json'
    result = json.loads(publication_path.read_bytes())
    receipt_path = RUN / 'publication_001/stage-receipt.json'
    if args.stage == 'publication':
        receipt = {'schema': 'cho51_linear_publication_stage_receipt_v1', 'passed': True,
            'pins_sha256': args.expect_pins, 'publication_result_file_sha256': args.expect_publication_result,
            'qualification_file_sha256': digest(RUN / 'publication_001/qualification.json'),
            'native': pub['native'], 'proofs': pub['proofs'],
            'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
            'publication_qualified': True, 'detached_stage_qualified': False,
            'scientific_admission': False, 'original_case_attempts_remaining': 0}
        receipt_sha = write_once(receipt_path, receipt)
        print(json.dumps({'passed': True, 'stage': args.stage, 'receipt': str(receipt_path), 'receipt_sha256': receipt_sha}))
        return
    receipt = json.loads(receipt_path.read_bytes())
    if (receipt.get('passed') is not True or receipt.get('pins_sha256') != args.expect_pins
            or receipt.get('publication_result_file_sha256') != args.expect_publication_result
            or receipt.get('proofs') != pub['proofs'] or receipt.get('native') != pub['native']):
        raise ValueError('exact accepted publication closeout required before detached closeout')
    restored = M.verify_restoration_proof(pins, args.expect_publication_result, root=ROOT)
    rest_receipt_path = RUN / 'restoration_001/stage-receipt.json'
    write_once(rest_receipt_path, {'schema': 'cho51_linear_restoration_stage_receipt_v1',
        'passed': True, 'pins_sha256': args.expect_pins,
        'publication_result_file_sha256': args.expect_publication_result,
        'publication_stage_receipt_file_sha256': digest(receipt_path),
        'native': restored['native'], 'proofs': restored['proofs'],
        'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
        'new_staged_store_restore_verified': True, 'unchanged_single_root_factory_verified': False,
        'full_worker_verified': False, 'scientific_admission': False, 'original_case_attempts_remaining': 0})
    archive = ROOT / 'evidence/cho51-linear-publication-20261015'
    if archive.exists():
        raise ValueError('unused current-stage archive required')
    sources = {ROOT / name for name in pins['reviewed_files']}
    sources.update(RUN / name for name in ('pins.json', 'source-review.json', 'origin-contract.json',
        'stage-contract.json', 'method-config.json'))
    sources.update(RUN.glob('preflight*.json'))
    sources.update(RUN.glob('dispatch*.json'))
    for directory in (RUN / 'publication_001', RUN / 'restoration_001'):
        sources.update(path for path in directory.iterdir() if path.is_file() and path.suffix != '.safetensors')
    sources.update(Path(result[key]) for key in ('manifest_path', 'evidence_path'))
    sources.update(RUN / 'publication_001/project' / relative for relative in pub['origin']['five_tomls'])
    for proof in (pub, restored):
        native = Path(proof['native']['native_directory'])
        sources.update(path for path in native.iterdir() if path.is_file())
        for relative, sha in proof['proofs'].items():
            path = ROOT / relative
            if (path.is_relative_to(RUN) or path.parent == native) and path.suffix != '.safetensors':
                if digest(path) != sha:
                    raise ValueError('own proof bytes changed before archival')
                sources.add(path)
    forbidden = {'.npz', '.npy', '.mat', '.safetensors', '.pt', '.pth', '.ckpt', '.edf', '.gdf', '.fif', '.set'}
    payloads = []
    large_evidence = Path(result['evidence_path'])
    for path in sorted(sources):
        if not path.is_relative_to(ROOT) or path.resolve(strict=True) != path or path.suffix.lower() in forbidden:
            raise ValueError('archive permits direct current metadata only')
        maximum = 32 * 1024**2 if path == large_evidence else 8 * 1024**2
        before = path.stat()
        if before.st_nlink != 1 or before.st_size > maximum:
            raise ValueError('ordinary compact metadata or exact bounded published evidence required')
        with path.open('rb') as stream:
            opened = os.fstat(stream.fileno())
            raw = stream.read(maximum + 1)
            finished = os.fstat(stream.fileno())
        after = path.stat()
        signature = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
        if (signature(before) != signature(after) or signature(opened) != signature(finished)
                or signature(before)[:4] != signature(opened)[:4] or len(raw) != before.st_size):
            raise ValueError('source metadata changed during bounded archival read')
        payloads.append((path, raw, hashlib.sha256(raw).hexdigest(), signature(before)))
    M.verify_pin_map(pins, root=ROOT)
    M.verify_publication_proof(pins, args.expect_publication_result, root=ROOT)
    M.verify_restoration_proof(pins, args.expect_publication_result, root=ROOT)
    archive.mkdir(); (archive / 'artifacts').mkdir()
    rows = []
    for index, (path, raw, sha, signature_before) in enumerate(payloads, 1):
        target = f'artifacts/a{index:04d}{path.suffix or ".txt"}'
        with (archive / target).open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        if digest(path) != sha or digest(archive / target) != sha:
            raise ValueError('current source/archive bytes differ')
        info = path.stat()
        if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) != signature_before:
            raise ValueError('current source identity changed during archival')
        rows.append({'source': path.relative_to(ROOT).as_posix(), 'path': target, 'bytes': len(raw), 'sha256': sha})
    summary = {'schema': 'cho51_linear_publication_summary_v1', 'passed': True,
        'closed_utc': datetime.now(timezone.utc).isoformat(), 'pins_sha256': args.expect_pins,
        'artifacts': len(rows), 'publication_result_file_sha256': args.expect_publication_result,
        'source_context_files': len(pins['files']), 'runtime_files': 5,
        'publication_native': pub['native'], 'restoration_native': restored['native'],
        'historical_gradient_updates': 5253, 'current_gradient_updates': 0,
        'main_tests_passed': 20, 'subtests_passed': 0, 'tests_replayed_in_detached_stage': False,
        'publication_qualified': True, 'new_staged_store_restore_verified': True,
        'unchanged_single_root_factory_verified': False, 'full_worker_verified': False,
        'cohort_lineage_verified': False, 'scientific_admission': False, 'original_case_attempts_remaining': 0}
    write_once(archive / 'manifest.json', {'schema': 'cho51_linear_publication_manifest_v1', 'artifacts': rows})
    write_once(archive / 'summary.json', summary)
    with (archive / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('# Explicit staged linear publication and restoration\n\n'
            'Two fresh native stages publish and restore the accepted full source state. '
            'All 5,253 fitting updates are historical; these stages perform zero training. '
            'The unchanged single-root Cho factories remain unqualified. '
            'The packet contains current metadata and the bounded canonical evidence copy; '
            'arrays, weights and ancestor packets remain at their authenticated origins.\n\n'
            '[Summary](summary.json), [manifest](manifest.json).\n')
    M.verify_pin_map(pins, root=ROOT)
    M.verify_restoration_proof(pins, args.expect_publication_result, root=ROOT)
    print(json.dumps({'passed': True, 'stage': args.stage, 'archive': str(archive), 'artifacts': len(rows),
        'manifest_sha256': digest(archive / 'manifest.json'), 'summary_sha256': digest(archive / 'summary.json')}))


if __name__ == '__main__':
    main()
