"""Single-writer metadata controller for independently admitted linear fragments.

No process, model, test or numerical work is launched here. Final canonical
selection-evidence.json alone has a32MiB JSON read/copy ceiling; all other
compact proofs retain8MiB. Safetensors are streamed for identity/hash only.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import math
import msvcrt
import os
from pathlib import Path, PurePosixPath
import re
import sys
from datetime import datetime, timezone
import uuid

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_chain_v1'
PREDECESSOR = ROOT / 'runs/coordination/cho51_linear_continuation_20261015_v1/pins.json'
PREDECESSOR_SHA = '1e16577546807821112e58f671f0941e0ba3ab0c5980c82efa67d92b14e4a42b'
METADATA = ROOT / 'runs/coordination/cho51_staged_restore_20261015_v1/metadata.py'
METADATA_SHA = 'b6aa21ab7d56724c04c5c96d60259b5aed9f1174ca0c05ae82479716bfbf36df'
MAXIMUM_COMPACT = 8 * 1024**2
MAXIMUM_COMPLETE_JSON = 32 * 1024**2
BASELINE = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
FINAL_ARCHIVE = ROOT / 'evidence/cho51-linear-chain-20261015'


def load(name, path, expected):
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
            raise ValueError('independently pinned metadata source changed: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


M = load('_linear_chain_closeout_frozen_metadata', METADATA, METADATA_SHA)
sys.path.insert(0, str(ROOT))


def logical(value):
    return hashlib.sha256(M.old.canonical(value)).hexdigest()


def document(path, *, expected=None, canonical=True):
    return M.document(Path(path), expected=expected, canonical_raw=canonical)


def inspect_compact(path, *, final_evidence=None):
    path = Path(path)
    if final_evidence is None or path != final_evidence:
        return M.old.inspect(path, compact=True)
    # This exception is confined to one final canonical JSON record. The old
    # generic reader and every request, qualification, leaf and partial stay8MiB.
    M.old.direct(path)
    info = path.stat()
    before = M.old.signature(info)
    if not path.is_file() or info.st_nlink != 1 or not 0 < before[2] <= MAXIMUM_COMPLETE_JSON:
        raise ValueError('final complete canonical JSON exceeds its32MiB ceiling')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(MAXIMUM_COMPLETE_JSON + 1)
        finished = os.fstat(stream.fileno())
    key = M.old.signature
    after = key(path.stat())
    if (before != after or key(opened) != key(finished)
            or key(opened)[:4] != before[:4] or len(raw) != before[2]
            or len(raw) > MAXIMUM_COMPLETE_JSON):
        raise ValueError('final complete JSON identity changed during bounded read')
    value = M.old.decode(raw)
    if raw != M.old.canonical(value) + b'\n':
        raise ValueError('final complete JSON must retain canonical finite unique-key bytes')
    return raw, (*before, hashlib.sha256(raw).hexdigest())


def inspect_checkpoint(path):
    """Hash one direct full checkpoint through a strict64MiB streaming bound."""
    M.old.direct(path)
    info = path.stat()
    before = M.old.signature(info)
    if not path.is_file() or info.st_nlink != 1 or not 0 < before[2] <= 64 * 1024**2:
        raise ValueError('full selected checkpoint exceeds64MiB or aliases another file')
    digest = hashlib.sha256()
    total, remaining = 0, 64 * 1024**2 + 1
    with path.open('rb') as stream:
        opened = M.old.signature(os.fstat(stream.fileno()))
        while remaining:
            chunk = stream.read(min(1024**2, remaining))
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
            remaining -= len(chunk)
        finished = M.old.signature(os.fstat(stream.fileno()))
    if (M.old.signature(path.stat()) != before or opened != finished
            or opened[:4] != before[:4] or total != before[2] or total > 64 * 1024**2):
        raise ValueError('full selected checkpoint changed during its bounded streaming hash')
    return (*before, digest.hexdigest())


def write_once(path, value, *, atomic=False):
    path = Path(path)
    raw = M.old.canonical(value) + b'\n'
    if len(raw) > MAXIMUM_COMPACT:
        raise ValueError('controller metadata exceeds8MiB')
    if not atomic:
        with path.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        temporary = path.parent / ('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
        try:
            with temporary.open('xb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, path)  # Atomic, no-clobber publication on this volume.
        finally:
            if temporary.exists():
                temporary.unlink()
    pin = M.old.inspect(path, compact=True)[1]
    if pin[-1] != hashlib.sha256(raw).hexdigest() or pin[2] != len(raw):
        raise ValueError('durable controller metadata differs from intended bytes')
    return pin[-1]


@contextmanager
def writer_lock():
    path = RUN / '.chain-controller.lock'
    try:
        stream = path.open('x+b')
        stream.write(b'\0')
        stream.flush()
        os.fsync(stream.fileno())
    except FileExistsError:
        M.old.direct(path)
        stream = path.open('r+b')
    try:
        info = path.stat()
        opened = os.fstat(stream.fileno())
        if (info.st_size != 1 or info.st_nlink != 1 or path.resolve(strict=True) != path
                or M.old.signature(info)[:4] != M.old.signature(opened)[:4]):
            raise ValueError('direct single-link one-byte controller lock required')
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        stream.close()


def verify_catalog(archive, *, final_evidence_source=None):
    manifest, _ = document(archive / 'manifest.json')
    M.old.fields(manifest, {'schema': 'cho51_linear_chain_artifact_manifest_v1'})
    seen = set()
    destinations = set()
    for row in manifest['artifacts']:
        relative = PurePosixPath(row['source'])
        if relative.is_absolute() or '..' in relative.parts or '\\' in row['source'] or row['source'] in seen:
            raise ValueError('distinct direct source paths required in artifact catalog')
        seen.add(row['source'])
        if (set(row) != {'source', 'path', 'sha256', 'bytes'}
                or re.fullmatch(r'artifacts/a[0-9]{4}\.[a-z0-9]+', row['path']) is None
                or row['path'] in destinations or type(row['bytes']) is not int or row['bytes'] < 0):
            raise ValueError('exact flat unique bounded artifact rows required')
        M.old.sha(row['sha256'])
        destinations.add(row['path'])
        source = ROOT.joinpath(*relative.parts)
        copied = archive / row['path']
        for path in (source, copied):
            special = path if source == final_evidence_source else None
            _, pin = inspect_compact(path, final_evidence=special)
            if pin[-1] != row['sha256'] or pin[2] != row['bytes']:
                raise ValueError('compact source/archive byte identity differs')
    return manifest


def archive_once(archive, sources, summary, *, final_evidence=None):
    if archive.exists():
        raise ValueError('unused immutable archive required: ' + str(archive))
    forbidden = {'.npz', '.npy', '.mat', '.fif', '.edf', '.gdf', '.set', '.pt', '.pth', '.ckpt', '.safetensors'}
    payloads = []
    for path in sorted(set(sources)):
        path = Path(path)
        if not path.is_relative_to(ROOT) or path.suffix.lower() in forbidden:
            raise ValueError('only compact repository metadata may be archived')
        raw, pin = inspect_compact(path, final_evidence=final_evidence)
        payloads.append((path, raw, pin))
    archive.mkdir()
    (archive / 'artifacts').mkdir()
    rows = []
    for index, (path, raw, pin) in enumerate(payloads, 1):
        relative = f'artifacts/a{index:04d}' + (path.suffix.lower() or '.txt')
        with (archive / relative).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        rows.append({'source': path.relative_to(ROOT).as_posix(), 'path': relative,
            'sha256': pin[-1], 'bytes': len(raw)})
    write_once(archive / 'manifest.json', {'schema': 'cho51_linear_chain_artifact_manifest_v1', 'artifacts': rows})
    write_once(archive / 'summary.json', {**summary, 'artifacts': len(rows)})
    verify_catalog(archive, final_evidence_source=final_evidence)
    for path, _, before in payloads:
        if inspect_compact(path, final_evidence=final_evidence)[1] != before:
            raise ValueError('physical compact source identity changed while copying')
    return rows


def verify_bundle(pins, pins_sha):
    M.old.fields(pins, {'schema': 'cho51_linear_chain_pins_v1',
        'predecessor_files': 1224, 'predecessor_pins_sha256': PREDECESSOR_SHA,
        'canonical_files': 432, 'canonical_source_sha256': M.CANONICAL,
        'seconds': 600, 'process_mib': 4096, 'job_mib': 5120,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
        'threads': 1, 'gpu_hidden': True, 'required_selection_updates': 5253,
        'expected_tests': 36, 'expected_subtests': 0,
        'cohort_lineage_verified': False, 'full_worker_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    prior, _ = document(PREDECESSOR, expected=PREDECESSOR_SHA)
    if (len(prior['files']) != 1224 or pins['runtime'] != prior['runtime'] or len(pins['runtime']) != 5
            or any(pins['files'].get(path) != sha for path, sha in prior['files'].items())):
        raise ValueError('fixed bundle must preserve all predecessor source/runtime pins')
    M.verify_pin_map(pins)
    review, _ = document(RUN / 'source-review.json', expected=pins['source_review_sha256'], canonical=False)
    M.old.fields(review, {'source_only': True, 'remaining_actionable_findings': [], 'files': pins['reviewed_files']})
    if len(review['files']) != 12 or any(pins['files'].get(path) != sha for path, sha in review['files'].items()):
        raise ValueError('all twelve exact reviewed chain sources required')
    for path, sha in pins['baseline'].items():
        _, pin = M.remember(Path(path), expected=sha)
        if sha != BASELINE or pin[2] != 23299672:
            raise ValueError('exact safe baseline required, hashed without decoding')
    if len(pins['baseline']) != 1:
        raise ValueError('one exact baseline required')
    bundle = RUN / 'bundle'
    if bundle.exists():
        manifest = verify_catalog(bundle)
        summary, _ = document(bundle / 'summary.json')
        M.old.fields(summary, {'schema': 'cho51_linear_chain_bundle_summary_v1', 'pins_sha256': pins_sha,
            'root_origin_file_sha256': pins['root_origin_file_sha256']})
        expected_sources = {path for path in pins['reviewed_files']}
        expected_sources.update((RUN / name).relative_to(ROOT).as_posix()
            for name in ('pins.json', 'source-review.json', 'root-origin.json', 'method-config.json'))
        if {row['source'] for row in manifest['artifacts']} != expected_sources:
            raise ValueError('fixed source bundle artifact inventory differs')


def ensure_bundle(pins, pins_sha):
    bundle = RUN / 'bundle'
    if not bundle.exists():
        sources = {ROOT / path for path in pins['reviewed_files']}
        sources.update(RUN / name for name in ('pins.json', 'source-review.json', 'root-origin.json', 'method-config.json'))
        archive_once(bundle, sources, {'schema': 'cho51_linear_chain_bundle_summary_v1',
            'pins_sha256': pins_sha, 'root_origin_file_sha256': pins['root_origin_file_sha256'],
            'source_files': len(pins['files']), 'runtime_files': 5,
            'source_code_copied_once': True, 'scientific_admission': False})
    verify_bundle(pins, pins_sha)


def verify_current(request, request_sha, pins, pins_sha, plan):
    index, output = request['index'], RUN / request['output_relative']
    dispatch, _ = document(RUN / f'dispatch/fragment_{index:03d}.json', canonical=False)
    dispatched, _ = document(RUN / f'dispatch/fragment_{index:03d}_result.json', canonical=False)
    request_path = RUN / f'requests/fragment_{index:03d}.json'
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'child.py'),
        '--pins', str(RUN / 'pins.json'), '--expect-pins', pins_sha,
        '--request', str(request_path), '--expect-request', request_sha, '--output', str(output)]
    for value in (dispatch, dispatched):
        M.old.fields(value, {'pins_sha256': pins_sha, 'request_sha256': request_sha,
            'child_command': command, 'expected_output': str(output), 'scientific_admission': False})
    M.old.fields(dispatched, {'guard_exit_code': 0})
    operations, runtimes = M.native_pins(pins)
    native = M.old.verify_native(Path(dispatched['native_directory']), command, 600, 4096, 5120,
        operations=operations, runtimes=runtimes, document=M.document, remember=M.remember, launcher=M.launcher)
    q, _ = document(output / 'qualification.json')
    wrapper, _ = document(output / 'result.json')
    probe, _ = document(output / 'probe-result.json')
    budget = plan.budget(request)
    M.old.fields(q, {'schema': 'cho51_linear_chain_qualification_v1', 'passed': True,
        'pins_sha256': pins_sha, 'request_sha256': request_sha, 'request_index': index,
        'mode': request['mode'], 'root_origin_sha256': request['root_origin_sha256'],
        'chain_sha256': request['chain_sha256'], 'parent_head_sha256': request['parent_head_sha256'],
        'budget': budget, 'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': 5,
        'baseline_pins_rechecked': 1, 'baseline_file_sha256': BASELINE,
        'canonical_files': 432, 'canonical_source_sha256': M.CANONICAL,
        'source_review_sha256': pins['source_review_sha256'], 'torch_threads': 1,
        'torch_interop_threads': 1, 'gpu_hidden': True, 'unexpected_denials': 0,
        'source_updates': budget['source_updates'], 'support_updates': budget['support_updates'],
        'actual_gradient_updates': budget['gradient_updates'],
        'actual_study_data_used': False, 'full_worker_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    if q['result'] != wrapper or wrapper['probe'] != probe:
        raise ValueError('native qualification must bind actual persisted wrapper and probe')
    M.old.fields(wrapper, {'schema': 'cho51_linear_chain_child_result_v1', 'passed': True, 'tests_passed': True})
    for value in (wrapper, q):
        M.old.fields(value, {'tests_executed': index == 1, 'tests_reused': index != 1, 'tests_passed': True})
    if index == 1:
        M.old.fields(wrapper, {'pytest_exit': 0, 'collected_tests': 36, 'expected_tests': 36,
            'collected_subtests': 0, 'expected_subtests': 0, 'subtest_reports': [],
            'skipped_reports': [], 'unexpected_reports': [], 'tests_reused_from_leaf_sha256': None})
        if len(wrapper['reports']) != 36 or any(row['phase'] != 'call' or row['outcome'] != 'passed'
                for row in wrapper['reports']):
            raise ValueError('all36 first-fragment plan tests must pass')
    elif (wrapper['tests_reused_from_leaf_sha256'] != q['tests_reused_from_leaf_sha256']
            or wrapper['reports'] or wrapper['subtest_reports'] or wrapper['skipped_reports'] or wrapper['unexpected_reports']):
        raise ValueError('later fragments must carry the unchanged authenticated first-leaf test receipt')
    M.old.fields(probe, {'schema': 'cho51_linear_chain_probe_v1', 'passed': True,
        'index': index, 'mode': request['mode'], 'request_sha256': request_sha,
        'pins_sha256': pins_sha, 'root_origin_sha256': request['root_origin_sha256'],
        'parent_head_sha256': request['parent_head_sha256'], 'budget': budget,
        'actual_gradient_updates': budget['gradient_updates'],
        'source_gradient_updates': budget['source_updates'], 'support_gradient_updates': budget['support_updates'],
        'contract_sha256': plan.CONTRACT_SHA256, 'template_state_sha256': plan.TEMPLATE_SHA256,
        'initial_source_state_sha256': plan.TEMPLATE_SHA256,
        'input_file_count': 213, 'input_bytes': 734579463,
        'selected_parameter_names': ['head.weight', 'head.bias'], 'selected_parameter_count': 402,
        'selected_tensor_count': 2, 'full_backbone_blocks': 12, 'full_backbone_embed_dim': 200,
        'all_physical_inputs_rehashed_unchanged': True, 'source_backbone_and_buffers_unchanged': True,
        'torch_numpy_python_rng_unchanged': True, 'canonical_run_selection_invoked': False,
        'public_selected_source_restore_exercised': False, 'publication_performed': False,
        'recorder_used': False, 'measured_cells': 0, 'full_worker_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0})
    calls = q['observed_numerical_calls']
    expected_calls = {**{key: budget[key] for key in ('optimizer_init', 'safetensors_load',
        'module_load_state_dict', 'safetensors_save')}, 'tensor_backward': budget['gradient_updates'],
        'autograd_backward': budget['gradient_updates'], 'sgd_step': budget['gradient_updates']}
    for key, expected in expected_calls.items():
        if type(calls.get(key, 0)) is not int or calls.get(key, 0) != expected:
            raise ValueError('exact actual current numerical budget differs: ' + key)
    if calls.get('autograd_grad', 0) != 0:
        raise ValueError('undeclared gradient call')
    connection = '.venv/Lib/site-packages/urllib3/util/connection.py'
    M.old.fields(q, {'denied_operations': [{'event': 'socket.__new__',
        'classification': 'blocked_optional_ipv6_import_probe', 'source_file': str(ROOT / connection),
        'source_sha256': pins['files'][connection]}], 'expected_blocked_ipv6_probes': 1,
        'protected_target_read_attempts': []})
    protected = [str(Path(probe['fixture_root']) / relative) for relative in (
        'data/processed/cho2017/profile_a/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
        'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
        'data/raw/moabb/cho2017/subject_02.mat')]
    M.old.fields(q, {'protected_target_transitions': [{'enabled': enabled, 'paths': protected}
        for enabled in (True, False)]})
    if any(q.get('fixture_input_read_phases', {}).get(path, {}).get('during_computation', 0) != 0
            for path in protected):
        raise ValueError('outer-target contents were opened during protected computation')
    if q['loaded_module_files'] != len(q['observed_loaded_module_hashes']) or not q['loaded_module_files']:
        raise ValueError('complete nonempty current post-import module inventory required')
    for path, sha in q['observed_loaded_module_hashes'].items():
        if M.old.inspect(Path(path), single_link=False)[1][-1] != sha:
            raise ValueError('current observed module drift')
    final_evidence = output / 'selection-evidence.json' if request['mode'] == 'final' else None
    if final_evidence is not None:
        raw, pin = inspect_compact(final_evidence, final_evidence=final_evidence)
        record = M.old.decode(raw)
        M.old.fields(record['payload'], {'complete': True, 'outer_target_predictions_performed': False})
        M.old.fields(probe, {'complete': True, 'full_selector_verified': True,
            'total_verified_gradient_updates': 5253, 'final_source_updates': 51,
            'public_complete_evidence_verifier_passed': True,
            'complete_native_origins_capability_exercised': True, 'final_numerical_branch_qualified': True})
        M.old.fields(probe['selection_evidence'], {'path': str(final_evidence),
            'file_sha256': pin[-1], 'size_bytes': pin[2], 'evidence_sha256': record['sha256']})
        if record['sha256'] != logical({key: value for key, value in record.items() if key != 'sha256'}):
            raise ValueError('complete canonical engineering envelope digest differs')
        checkpoint = probe['checkpoint']
        checkpoint_path = output / 'selected-source.safetensors'
        weights = inspect_checkpoint(checkpoint_path)
        M.old.fields(checkpoint, {'path': str(checkpoint_path), 'file_sha256': weights[-1],
            'weights_sha256': weights[-1], 'size_bytes': weights[2], 'weights_format': 'full_v1',
            'tensor_count': 223, 'elements': 5818138, 'roundtrip_verified': True, 'published': False,
            'identity': list(weights[:-1]), 'read_limit_bytes': 64 * 1024**2})
        selected_recipe = probe['selected_model_recipe']
        selected_recipe_sha = logical(selected_recipe)
        if (selected_recipe != {**probe['model_recipe'], 'selected_candidate': probe['selected_candidate']}
                or selected_recipe_sha != probe['selected_model_recipe_sha256']
                or checkpoint['selected_model_recipe_sha256'] != selected_recipe_sha):
            raise ValueError('checkpoint architecture recipe differs from the actual selected candidate')
        M.old.fields(probe['verified_selection'], {'selected_candidate': probe['selected_candidate'],
            'evidence_sha256': record['sha256'], 'model_state_sha256': checkpoint['model_state_sha256'],
            'selected_model_recipe_sha256': selected_recipe_sha,
            'public_complete_evidence_verifier_passed': True, 'source_gradient_updates': 5151,
            'support_gradient_updates': 102, 'total_gradient_updates': 5253,
            'folds': 102, 'fresh_final_source_updates': 51})
        payload = record['payload']
        if (payload['selected_candidate'] != probe['selected_candidate']
                or payload['contract_sha256'] != plan.CONTRACT_SHA256
                or payload['final_source_fit']['fitted_state_sha256'] != checkpoint['model_state_sha256']):
            raise ValueError('complete public evidence differs from actual selected model/checkpoint state')
        schema_path = output / 'selected-state-schema.json'
        schema, schema_sha = document(schema_path, expected=checkpoint['schema_pin']['file_sha256'])
        M.old.fields(checkpoint['schema_pin'], {'path': str(schema_path), 'file_sha256': schema_sha,
            'size_bytes': M.old.inspect(schema_path)[1][2]})
        M.old.fields(schema, {'schema': 'cho51_linear_chain_full_state_schema_v1',
            'model_state_sha256': checkpoint['model_state_sha256'], 'weights_sha256': weights[-1],
            'weights_bytes': weights[2], 'tensor_count': 223, 'elements': 5818138,
            'roundtrip_verified': True, 'all_finite_cpu_float32': True, 'published': False,
            'selected_model_recipe_sha256': selected_recipe_sha})
        if len(schema['tensors']) != 223:
            raise ValueError('complete223-tensor checkpoint schema required')
        for row in schema['tensors'].values():
            if (row['dtype'] != 'torch.float32' or type(row['shape']) is not list
                    or any(type(value) is not int or value < 0 for value in row['shape'])
                    or type(row['elements']) is not int or math.prod(row['shape']) != row['elements']):
                raise ValueError('checkpoint tensor schema differs from its declared shape and dtype')
        if sum(row['elements'] for row in schema['tensors'].values()) != 5818138:
            raise ValueError('complete selected checkpoint element count differs')
    else:
        M.old.fields(probe, {'complete': False, 'selected_candidate': None,
            'full_selector_verified': False, 'final_source_updates': 0,
            'checkpoint': None, 'selection_evidence': None})
        if (output / 'selected-source.safetensors').exists():
            raise ValueError('fold fragment must not produce a selected checkpoint')
    return native, q, probe, final_evidence


def final_archive(pins, pins_sha, chain, origin_module, root_origin):
    origin_module.verify_chain(root_origin, chain, ROOT, pins_sha256=pins_sha)
    sources = {RUN / 'root-origin.json', RUN / 'pins.json', RUN / 'bundle/manifest.json', RUN / 'bundle/summary.json',
        RUN / 'chains/chain_007.json'}
    bundle = verify_catalog(RUN / 'bundle')
    sources.update(ROOT / row['source'] for row in bundle['artifacts'])
    final_evidence = RUN / 'fragments/fragment_007/selection-evidence.json'
    for index in range(1, 8):
        archive = RUN / f'fragments/fragment_{index:03d}/archive'
        catalog = verify_catalog(archive, final_evidence_source=final_evidence if index == 7 else None)
        sources.update(ROOT / row['source'] for row in catalog['artifacts'])
        sources.update((archive / 'manifest.json', archive / 'summary.json'))
    rows = archive_once(FINAL_ARCHIVE, sources, {'schema': 'cho51_linear_chain_summary_v1',
        'passed': True, 'closed_utc': datetime.now(timezone.utc).isoformat(), 'pins_sha256': pins_sha,
        'root_origin_file_sha256': pins['root_origin_file_sha256'], 'chain_head_sha256': chain['head_sha256'],
        'native_fragments': 7, 'historical_root_folds': 10, 'new_fold_fragments': [16, 16, 16, 16, 16, 12],
        'accepted_folds': 102, 'pending_folds': 0, 'all_fold_gradient_updates': 5202,
        'fresh_final_source_updates': 51, 'total_verified_gradient_updates': 5253,
        'full_selector_verified': True, 'canonical_run_selection_invoked': False,
        'complete': True, 'public_selected_source_restoration_performed': False,
        'publication_performed': False, 'recorder_used': False, 'measured_cells': 0,
        'full_worker_verified': False, 'cohort_lineage_verified': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0,
        'complete_evidence_json_limit_bytes': MAXIMUM_COMPLETE_JSON,
        'other_compact_proof_limit_bytes': MAXIMUM_COMPACT, 'checkpoint_blob_archived': False}, final_evidence=final_evidence)
    with (FINAL_ARCHIVE / 'README.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('# Authenticated linear selector fragment chain\n\n'
            'Six bounded native fragments completed92 new genuine folds; the ten authenticated root folds '
            'were not replayed. A seventh Job performed the fresh51-source winning fit and passed the '
            'canonical public complete-evidence verifier. Total verified updates:5253. '
            'The full safe checkpoint was byte-hashed and its guarded round-trip witness verified; '
            'the checkpoint blob and all input arrays are excluded. No publication, selected-source restoration, '
            'recorder, study cell or science is admitted.\n\n'
            'Only final selection-evidence.json uses the explicitly approved32MiB metadata exception; '
            'all other compact proofs retain8MiB. Each own fragment is archived once without recursively '
            'copying ancestor proof packages. [Summary](summary.json), [manifest](manifest.json).\n')
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--expect-request', required=True)
    parser.add_argument('--expect-pins', required=True)
    args = parser.parse_args()
    for value in (args.expect_request, args.expect_pins):
        M.old.sha(value)
    with writer_lock():
        pins, pins_sha = document(RUN / 'pins.json', expected=args.expect_pins)
        verify_bundle(pins, pins_sha)
        P = load('_linear_chain_closeout_plan', CANDIDATE / 'plan.py',
            pins['files'][(CANDIDATE / 'plan.py').relative_to(ROOT).as_posix()])
        O = load('_linear_chain_closeout_origin', CANDIDATE / 'origin.py',
            pins['files'][(CANDIDATE / 'origin.py').relative_to(ROOT).as_posix()])
        request, request_sha = document(args.request, expected=args.expect_request)
        index = request['index']
        if args.request != RUN / f'requests/fragment_{index:03d}.json':
            raise ValueError('exact current sequential request path required')
        chain_path = RUN / request['chain_relative']
        chain, _ = document(chain_path)
        root_origin, _ = document(RUN / 'root-origin.json', expected=pins['root_origin_file_sha256'])
        P.validate_request(request, chain, pins_sha256=pins_sha,
            root_origin_sha256=pins['root_origin_file_sha256'])
        snapshots = sorted((RUN / 'chains').glob('chain_*.json'))
        expected = [RUN / f'chains/chain_{number:03d}.json' for number in range(index)]
        if snapshots != expected or chain_path != snapshots[-1]:
            raise ValueError('the requested parent must be the sole latest chain head, with no fork')
        output = RUN / request['output_relative']
        if (output / 'leaf.json').exists() or (output / 'archive').exists():
            raise ValueError('current fragment already closed or quarantined; no automatic replay')
        history = O.verify_chain(root_origin, chain, ROOT, pins_sha256=pins_sha)
        native, q, probe, final_evidence = verify_current(request, request_sha, pins, pins_sha, P)
        ensure_bundle(pins, pins_sha)
        descriptor = O.close_leaf(history, request, {'native_directory': native['native_directory']}, ROOT)
        leaf_path = ROOT / descriptor['path']
        leaf, _ = document(leaf_path, expected=descriptor['sha256'])
        own_sources = {leaf_path}
        for relative, sha in leaf['proofs'].items():
            direct_relative = PurePosixPath(relative)
            if direct_relative.is_absolute() or '..' in direct_relative.parts or '\\' in relative:
                raise ValueError('direct own leaf proof path required')
            path = ROOT.joinpath(*direct_relative.parts)
            _, pin = inspect_compact(path, final_evidence=final_evidence)
            if pin[-1] != sha:
                raise ValueError('own leaf proof changed before compact archival')
            if path in (RUN / 'pins.json', RUN / 'root-origin.json'):
                continue  # Already copied exactly once in the immutable bundle.
            own_sources.add(path)
        archive_once(output / 'archive', own_sources, {'schema': 'cho51_linear_chain_fragment_summary_v1',
            'passed': True, 'index': index, 'mode': request['mode'], 'request_sha256': request_sha,
            'pins_sha256': pins_sha, 'root_origin_sha256': request['root_origin_sha256'],
            'parent_head_sha256': request['parent_head_sha256'], 'leaf_sha256': descriptor['sha256'],
            'native': native, 'current_gradient_updates': P.budget(request)['gradient_updates'],
            'accepted_folds': len(chain['accepted_pairs']) + len(request['pairs']),
            'scientific_admission': False, 'complete_json_limit_bytes': MAXIMUM_COMPLETE_JSON,
            'other_compact_limit_bytes': MAXIMUM_COMPACT}, final_evidence=final_evidence)
        next_chain = P.advance_chain(chain, descriptor)
        M.verify_pin_map(pins)
        for path, before in tuple(M.observed.items()):
            if M.old.inspect(Path(path))[1] != before:
                raise ValueError('current proof or baseline physical identity changed during closeout')
        for path, sha in q['observed_loaded_module_hashes'].items():
            if M.old.inspect(Path(path), single_link=False)[1][-1] != sha:
                raise ValueError('current observed module changed before chain advancement')
        if final_evidence is not None:
            expected_checkpoint = (*probe['checkpoint']['identity'], probe['checkpoint']['file_sha256'])
            if inspect_checkpoint(output / 'selected-source.safetensors') != expected_checkpoint:
                raise ValueError('current checkpoint physical identity changed before chain advancement')
        M.launcher._job_absent(native['job_name'])
        chain_sha = write_once(RUN / f'chains/chain_{index:03d}.json', next_chain, atomic=True)
        result = {'passed': True, 'index': index, 'mode': request['mode'],
            'leaf_sha256': descriptor['sha256'], 'chain_file_sha256': chain_sha,
            'accepted_folds': len(next_chain['accepted_pairs']), 'scientific_admission': False}
        if index == 7:
            result['final_archive_artifacts'] = final_archive(pins, pins_sha, next_chain, O, root_origin)
            result['final_archive'] = str(FINAL_ARCHIVE)
        M.launcher._job_absent(native['job_name'])
        print(json.dumps(result))


if __name__ == '__main__':
    main()
