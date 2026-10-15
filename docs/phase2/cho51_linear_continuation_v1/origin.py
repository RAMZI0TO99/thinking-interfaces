"""Authenticate the exact historical two-fold lineage for a new engineering adoption.

Only standard-library metadata and frozen byte/native proof readers are used.
The former partial collector remains unchanged and grants no reuse authority.
This new contract adopts precisely its two authenticated raw folds, never a
winner, a final fit, a scientific case, or canonical run_selection execution.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = 'runs/coordination/cho51_linear_lineage_20261015_v2'
REFUSED = 'runs/coordination/cho51_linear_lineage_20261015_v1'
PINS_SHA = '9d5c2da133dc1119304fe1e2219fef3d292d277fd4287bcceb019451f8cc30ca'
REVIEW_SHA = 'd9a19f916b7e2dd36f009208b278b17ce24c44bf50d89dcf399a5c98c98c3638'
FINAL_SHA = '76476364b8ead888716fa348faaeaf84a3ea58f5253aa6d9d616a21225c3851e'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
INITIAL = '90a9d34ecba2aa96a942f7bd70724f63c2071042141935dbbcd78e0b373b89a7'
CONTRACT = '8397d34ee0a2280b406071e045988f98b1b73ce21fcecc0b9834518cd21993b1'
BASELINE = '53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
MAXIMUM_PROOF_BYTES = 8 * 1024**2
HELPERS = {
    'runs/coordination/cho51_staged_restore_20261015_v1/metadata.py':
        'b6aa21ab7d56724c04c5c96d60259b5aed9f1174ca0c05ae82479716bfbf36df',
    'runs/coordination/cho51_complete_eegnet_20261015_v4/closeout.py':
        '7df8211707505209fcdb333530da4625f2c01a113dc449187831489c4570f62c',
    'docs/phase2/cho51_tensor_verification_v1/launcher.py':
        'ff9ab5dc5bef374c4a76f946a52cd412fd260d19ad88a6d9ea7828087d9b2f24',
    'tools/migration/common.py':
        'fe2790bc2703af17b930dffe109d8c750fb8d0abfa205fbd40245aec178936d5',
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _canonical(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _logical(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _bootstrap(path):
    """Bound the four immutable reader modules before executing their code."""
    before = path.stat(follow_symlinks=False)
    _need(path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode)
          and before.st_size <= MAXIMUM_PROOF_BYTES, 'direct bounded frozen helper required')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(MAXIMUM_PROOF_BYTES + 1)
        finished = os.fstat(stream.fileno())
    signature = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    _need(signature(before) == signature(path.stat(follow_symlinks=False))
          and signature(opened) == signature(finished)
          and signature(before)[:4] == signature(opened)[:4]
          and len(raw) == before.st_size, 'frozen helper changed during bounded read')
    return hashlib.sha256(raw).hexdigest()


def _metadata(root):
    for relative, expected in HELPERS.items():
        _need(_bootstrap(root / relative) == expected, 'frozen metadata helper drift: ' + relative)
    name = '_cho51_linear_continuation_origin_metadata_v1'
    spec = importlib.util.spec_from_file_location(name, root / next(iter(HELPERS)))
    _need(spec is not None and spec.loader is not None, 'frozen metadata loader unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_origin(root: Path) -> dict:
    """Revalidate all historical bytes/proofs and return a deterministic detached contract.

    Current hashes of the six mutable resume documents are deliberately excluded.
    Their historical digests remain inside the externally pinned final-review file.
    The exact original qualification report remains an immutable proof dependency.
    """
    _need(isinstance(root, Path) and root.is_absolute() and root == PROJECT_ROOT
          and root.resolve(strict=True) == root, 'exact direct project root required')
    M = _metadata(root)
    proofs = {}

    def relative_path(value):
        _need(type(value) is str, 'plain root-relative proof path required')
        relative = PurePosixPath(value)
        _need(not relative.is_absolute() and '..' not in relative.parts and '\\' not in value,
              'proof path escapes the project')
        path = root.joinpath(*relative.parts)
        _need(path.is_relative_to(root), 'proof path escapes the project')
        return path

    def remember(path, *, expected=None, compact=False, **ignored):
        path = Path(path)
        raw, pin = M.remember(path, expected=expected, compact=compact)
        if compact:
            relative = path.relative_to(root).as_posix()
            _need(relative_path(relative) == path, 'direct compact proof path required')
            previous = proofs.setdefault(relative, pin[-1])
            _need(previous == pin[-1], 'compact proof hash conflict')
        return raw, pin

    def document(path, *, expected=None, canonical_raw=False, **ignored):
        raw, pin = remember(path, expected=expected, compact=True)
        value = M.old.decode(raw)
        if canonical_raw:
            _need(raw == _canonical(value) + b'\n', 'canonical JSON proof required')
        return value, pin[-1]

    original, refused = root / ORIGINAL, root / REFUSED
    output = original / 'validation_001'
    pins, _ = document(original / 'pins.json', expected=PINS_SHA)
    _need(len(pins['files']) == 1047 and len(pins['runtime']) == 5
          and len(pins['baseline']) == 1, 'exact historical1047/5/1 pins required')
    M.verify_pin_map(pins)
    _need(M.old.source_check(root) == CANONICAL, 'canonical432 source drift')
    source_review, _ = document(original / 'source-review.json', expected=REVIEW_SHA)
    M.old.fields(source_review, {'source_only': True, 'remaining_actionable_findings': [],
                               'files': pins['reviewed_files']})
    final, _ = document(original / 'final-review.json', expected=FINAL_SHA)
    M.old.fields(final, {'passed': True, 'metadata_only': True, 'remaining_actionable_findings': [],
        'source_runtime_baseline_pins_rechecked': [1047, 5, 1], 'canonical_files': 432,
        'canonical_source_sha256': CANONICAL})
    report = 'docs/phase2/cho51_linear_lineage_qualification_20261015.md'
    remember(root / report, expected=final['documents'][report], compact=True)

    packets = (
        ('cho51-linear-lineage-20261015', 91,
         'a1d3360075f1ec3c384e6b30236e4404a13553d297a3145fb5da87ac4c95f245',
         '7749a225c3710c7c3bf46a041ed86d069b360e1858979645c6e340d4c3a73a97'),
        ('cho51-linear-lineage-reporting-refusal-20261015', 26,
         '426bae32b4ba07cb46ac54038d58f0a46954db94f7920c65a206ed9e2700f4f9',
         'f7f91654d332feb7d96f1da103de04cba3e8c2f13e1d607409545fe20fe7c3a1'),
    )
    summaries = []
    for name, count, manifest_sha, summary_sha in packets:
        packet = root / 'evidence' / name
        manifest, _ = document(packet / 'manifest.json', expected=manifest_sha)
        summary, _ = document(packet / 'summary.json', expected=summary_sha)
        remember(packet / 'README.md', compact=True)
        _need(len(manifest['artifacts']) == count and summary['artifacts'] == count,
              'exact preserved archive inventory required')
        for row in manifest['artifacts']:
            archived = relative_path(('evidence/' + name + '/' + row['path']))
            for path in (relative_path(row['source']), archived):
                _, actual = remember(path, expected=row['sha256'], compact=True)
                _need(actual[2] == row['bytes'], 'historical source/archive byte count drift')
        summaries.append(summary)
    summary, refusal_summary = summaries
    M.old.fields(summary, {'passed': True, 'actual_gradient_updates': 102, 'source_updates': 100,
        'support_updates': 2, 'diagnostic_folds': 2, 'pending_folds': 100, 'complete': False,
        'selected_candidate': None, 'full_selector_verified': False, 'scientific_admission': False})
    M.old.fields(refusal_summary, {'accepted': False, 'actual_gradient_updates': 0,
        'baseline_tensor_decodes': 0, 'synthetic_fixture_created': False,
        'main_tests_passed': 32, 'subtests_passed': 23})

    for path, expected in pins['baseline'].items():
        _, actual = remember(Path(path), expected=expected)
        _need(expected == BASELINE and actual[2] == 23299672, 'exact audited baseline required')
    for path, pin in source_review['lineage_assets'].items():
        _, actual = remember(Path(path), expected=pin['sha256'])
        _need(actual[2] == pin['bytes'], 'historical lineage asset size drift')

    q, _ = document(output / 'qualification.json', expected=summary['qualification_file_sha256'], canonical_raw=True)
    result, result_sha = document(output / 'probe-result.json', expected=summary['probe_result_file_sha256'], canonical_raw=True)
    child, _ = document(output / 'result.json', canonical_raw=True)
    _need(q['result'] == child and child['probe'] == result, 'actual qualification/wrapper/probe differ')
    M.old.fields(q, {'passed': True, 'pins_sha256': PINS_SHA, 'source_review_sha256': REVIEW_SHA,
        'source_pins_rechecked': 1047, 'runtime_pins_rechecked': 5, 'canonical_files': 432,
        'canonical_source_sha256': CANONICAL, 'source_updates': 100, 'support_updates': 2,
        'actual_gradient_updates': 102, 'unexpected_denials': 0, 'protected_target_read_attempts': [],
        'cohort_lineage_verified': False, 'full_selector_verified': False, 'scientific_admission': False})
    M.old.fields(child, {'passed': True, 'tests_passed': True, 'pytest_exit': 0,
        'collected_tests': 32, 'expected_tests': 32, 'collected_subtests': 23,
        'expected_subtests': 23, 'unexpected_reports': [], 'skipped_reports': []})
    for key, count in (('reports', 32), ('subtest_reports', 23)):
        _need(len(child[key]) == count and all(row['phase'] == 'call' and row['outcome'] == 'passed'
              for row in child[key]), 'all original main/subtest reports must pass')
    M.old.fields(q['observed_numerical_calls'], {'safetensors_load': 2, 'module_load_state_dict': 2,
        'tensor_backward': 102, 'autograd_backward': 102, 'sgd_step': 102, 'optimizer_init': 4})
    M.old.fields(result, {'passed': True, 'method': 'labram_linear', 'actual_gradient_updates': 102,
        'source_gradient_updates': 100, 'support_gradient_updates': 2, 'diagnostic_folds': 2,
        'required_complete_folds': 102, 'pending_folds': 100, 'required_selection_updates': 5253,
        'template_state_sha256': INITIAL, 'initial_source_state_sha256': INITIAL,
        'independent_initial_state_sha256': INITIAL, 'contract_sha256': CONTRACT,
        'selected_parameter_count': 402, 'selected_parameter_names': ['head.weight', 'head.bias'],
        'baseline_safe_tensor_count': 221, 'baseline_safe_elements': 5819936,
        'full_backbone_blocks': 12, 'independent_lineage_verified': True,
        'source_backbone_and_buffers_unchanged': True, 'torch_numpy_python_rng_unchanged': True,
        'pretrained_baseline_loaded': True, 'prior_template_training_verified': False,
        'complete': False, 'selected_candidate': None, 'cohort_lineage_verified': False,
        'full_selector_verified': False, 'full_worker_verified': False,
        'public_selected_source_restore_exercised': False, 'publication_performed': False,
        'recorder_used': False, 'measured_cells': 0, 'scientific_admission': False})
    _need([row['enabled'] for row in q['protected_target_transitions']] == [True, False]
          and all(row['paths'] == result['protected_outer_paths'] for row in q['protected_target_transitions'])
          and len(result['protected_outer_paths']) == 4, 'historical outer-target protection differs')
    modules = q['observed_loaded_module_hashes']
    _need(len(modules) == 4818, 'exact4818 historical module witnesses required')
    for path, expected in modules.items():
        _need(M.old.inspect(Path(path), single_link=False)[1][-1] == expected, 'historical observed module drift')

    fixture = output / 'fixture'
    identity_path = fixture / 'synthetic-input-identity.json'
    _need(result['fixture_root'] == str(fixture) and result['input_identity_path'] == str(identity_path),
          'exact original synthetic fixture required')
    identity, identity_sha = document(identity_path, expected=result['input_identity_file_sha256'], canonical_raw=True)
    identity_payload = dict(identity)
    _need(identity_payload.pop('sha256') == result['input_identity_sha256']
          and _logical(identity_payload) == result['input_identity_sha256']
          and len(identity['files']) == 213, 'exact physical synthetic input identity required')
    total = 0
    for relative, pin in identity['files'].items():
        lexical = PurePosixPath(relative)
        _need(not lexical.is_absolute() and '..' not in lexical.parts and '\\' not in relative,
              'direct synthetic relative input required')
        _, actual = remember(fixture.joinpath(*lexical.parts), expected=pin['sha256'])
        _need(actual[2] == pin['size_bytes'], 'original physical input size drift')
        total += actual[2]
    _need(total == 734579463 and result['input_files'] == identity['files'], 'original input inventory drift')

    fold_paths, fold_file_shas, fold_evidence_shas, adopted = [], [], [], []
    for index, name in enumerate(('lr_1e-3', 'lr_2e-3'), 1):
        path = output / f'fold_{index:02d}.json'
        witness = result['fold_evidence'][index - 1]
        _need(witness['path'] == str(path), 'historical fold path differs')
        record, file_sha = document(path, expected=witness['file_sha256'], canonical_raw=True)
        content = dict(record)
        evidence_sha = content.pop('sha256')
        _need(_logical(content) == evidence_sha == witness['evidence_sha256'], 'raw fold logical SHA drift')
        payload = record['payload']
        M.old.fields(payload, {'complete': False, 'selected_candidate': None, 'contract_sha256': CONTRACT})
        _need(_logical(payload['contract']) == CONTRACT and len(payload['folds']) == 1,
              'exact shared historical selector contract required')
        fold = payload['folds'][0]
        M.old.fields(fold, {'candidate': name, 'validation_subject': 'subject_01'})
        fit = fold['source_fit']
        _need(len(fit['steps']) == 50 and fit['initial_state_sha256'] == INITIAL
              and fit['training_subjects'] == [f'subject_{n:02d}' for n in range(3, 53)],
              'original fifty-source fold lineage differs')
        fold_paths.append(str(path)); fold_file_shas.append(file_sha); fold_evidence_shas.append(evidence_sha)
        adopted.append({'candidate': name, 'validation_subject': 'subject_01',
                        'path': str(path), 'file_sha256': file_sha, 'evidence_sha256': evidence_sha})
    partial_pin = result['partial_collection']
    partial, _ = document(Path(partial_pin['path']), expected=partial_pin['file_sha256'], canonical_raw=True)
    M.old.fields(partial, {'accepted_folds': 2, 'pending_folds': 100, 'complete': False,
        'selected_candidate': None, 'reuse_authorized': False, 'source_work_reused': False,
        'full_selector_qualified': False, 'final_fit_qualified': False, 'publication_qualified': False})
    observations_pin = result['optimizer_observations']
    observations, _ = document(Path(observations_pin['path']), expected=observations_pin['file_sha256'], canonical_raw=True)
    _need(len(observations['events']) == 102 and observations['events'] == result['optimizer_updates'],
          'original102 observed optimizer events differ')

    native_proofs = []
    for directory, native_name, pins_sha, failure in (
        (original, '20261015T144029Z_cd0a5f5142', PINS_SHA, False),
        (refused, '20261015T143319Z_0e097ec22e',
         '6e5b533fc1bc0c56c2ca287cc7f8d81849a3587d4737d718d39cdec091a35650', True),
    ):
        native_pins, _ = document(directory / 'pins.json', expected=pins_sha)
        operations, runtimes = M.native_pins(native_pins)
        command = [str(root / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(directory / 'child.py'),
                   '--pins', str(directory / 'pins.json'), '--expect-pins', pins_sha,
                   '--output', str(directory / 'validation_001')]
        dispatch, _ = document(directory / 'dispatch_001.json')
        dispatched, _ = document(directory / 'dispatch_result_001.json')
        for value in (dispatch, dispatched):
            M.old.fields(value, {'pins_sha256': pins_sha, 'child_command': command,
                'expected_output': str(directory / 'validation_001'), 'scientific_admission': False})
        M.old.fields(dispatched, {'native_directory': str(root / 'runs/migration' / native_name),
                                 'guard_exit_code': 1 if failure else 0})
        native_proofs.append(M.old.verify_native(root / 'runs/migration' / native_name, command,
            600, 4096, 5120, operations=operations, runtimes=runtimes, document=document,
            remember=remember, launcher=M.launcher, expected_failure=failure))
    _need(native_proofs[0]['elapsed_native_seconds'] == 69.131952,
          'exact accepted original native interval required')
    M.verify_pin_map(pins)
    for path, before in tuple(M.observed.items()):
        _need(M.old.inspect(Path(path))[1] == before, 'origin proof changed before adoption release')
    origin = {
        'schema': 'cho51_linear_continuation_origin_v1', 'fixture_root': str(fixture),
        'original_result_path': str(output / 'probe-result.json'),
        'original_result_file_sha256': result_sha,
        'original_fold_paths': fold_paths, 'original_fold_file_sha256': fold_file_shas,
        'original_fold_evidence_sha256': fold_evidence_shas,
        'input_identity_path': str(identity_path), 'input_identity_sha256': result['input_identity_sha256'],
        'input_identity_file_sha256': identity_sha, 'template_state_sha256': INITIAL,
        'initial_state_sha256': INITIAL, 'lineage_recipe_sha256': result['model_recipe_sha256'],
        'contract_sha256': CONTRACT, 'original_contract_sha256': CONTRACT,
        'source_pins_sha256': PINS_SHA, 'baseline_sha256': BASELINE,
        'proofs': dict(sorted(proofs.items())), 'adopted_folds': 2, 'adopted_fold_records': adopted,
        'historical_source_updates': 100, 'historical_support_updates': 2,
        'historical_gradient_updates': 102, 'current_gradient_updates': 0,
        'historical_partial_reuse_authorized': False,
        'historical_fold_adoption_authorized': True,
        'adoption_authority': 'this_new_versioned_engineering_origin_contract_only',
        'native_proofs': native_proofs, 'archive_source_pairs_verified': [91, 26],
        'source_runtime_baseline_pins_verified': [1047, 5, 1],
        'physical_input_files_verified': 213, 'physical_input_bytes_verified': total,
        'observed_loaded_modules_verified': 4818, 'canonical_files': 432,
        'canonical_source_sha256': CANONICAL, 'selected_candidate': None, 'complete': False,
        'full_selector_qualified': False, 'final_fit_authorized': False,
        'cohort_lineage_verified': False, 'scientific_admission': False, 'original_case_attempts': 0,
    }
    return json.loads(_canonical(origin))


def verify_origin(origin: dict, root: Path) -> None:
    """Fail closed unless every immutable origin dependency and contract field matches."""
    _need(type(origin) is dict, 'detached explicit origin contract required')
    _need(_canonical(origin) == _canonical(build_origin(root)),
          'new engineering adoption contract differs from its exact historical origin')
