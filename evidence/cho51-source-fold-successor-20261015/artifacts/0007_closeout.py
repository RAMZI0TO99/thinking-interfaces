"""Compact closeout of four independently guarded incomplete public source folds.

Only standard-library files/receipts are read here; never import a numerical
module, decode an array, restore a state, create a recorder or launch work.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = ROOT / 'evidence/cho51-source-fold-20261015'
CANDIDATE = ROOT / 'docs/phase2/cho51_source_fold_probe_v1'
PRIOR = ROOT / 'runs/coordination/cho51_worker_lifecycle_20261015_v1/pins.json'
PRIOR_SHA = '20a808c269e6de2c6fd7355749438c80f7198e48946753d0db63308a1a72d3a1'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
OWNER = 'ae3295c2aa5acdfad2c9b2d7ffb602ec8b0daddb07b3d433d15dcaf9fd002709'
METHODS = ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
PAUSE = Path('D:/Aenv/pro2/WORK/resume-20261015-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json')
MAXIMUM_COMPACT = 8 * 1024**2
sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import io_path, source_check


def signature(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def direct(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve(strict=True) != path:
        raise ValueError('direct absolute existing path required: ' + str(path))
    for ancestor in (path, *path.parents):
        info = io_path(ancestor).lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
            raise ValueError('linked/reparse artifact refused: ' + str(path))
    return path


def inspect(path, *, compact=False, single_link=True):
    path = direct(path)
    before = io_path(path).stat()
    if (not stat.S_ISREG(before.st_mode) or single_link and before.st_nlink != 1
            or compact and before.st_size > MAXIMUM_COMPACT):
        raise ValueError('bounded direct regular artifact required: ' + str(path))
    with io_path(path).open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(MAXIMUM_COMPACT + 1) if compact else None
        value = hashlib.sha256(raw).hexdigest() if compact else hashlib.file_digest(stream, 'sha256').hexdigest()
        closed = os.fstat(stream.fileno())
    # Windows path stat and fstat can disagree about ctime. Only compare it
    # within the same API; cross-API identity retains dev/ino/size/mtime.
    if (signature(io_path(path).stat()) != signature(before)
            or signature(opened) != signature(closed)
            or signature(opened)[:4] != signature(before)[:4]
            or compact and len(raw) != before.st_size):
        raise ValueError('physical artifact changed while reading: ' + str(path))
    return raw, (*signature(before), value)


def decode(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('nonfinite JSON: ' + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    if type(value) is not str or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError('plain SHA256 required')
    return value


def fields(value, expected, *, exact=False):
    if (type(value) is not dict or exact and set(value) != set(expected)
            or any(key not in value or type(value[key]) is not type(want)
                   or canonical(value[key]) != canonical(want) for key, want in expected.items())):
        raise ValueError('literal typed evidence fields differ: ' + ','.join(expected))


def utc(value):
    if type(value) is not str:
        raise ValueError('UTC timestamp required')
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError('explicit UTC timestamp required')
    return parsed


def write(path, value):
    with io_path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    identities, paths, runtime_paths = {}, set(), set()

    def remember(path, *, compact=False, expected=None, archive=False, single_link=True):
        path = Path(path)
        raw, observed = inspect(path, compact=compact, single_link=single_link)
        if expected is not None and observed[-1] != sha(expected):
            raise ValueError('independent physical digest differs: ' + str(path))
        if identities.setdefault(path, observed) != observed:
            raise ValueError('physical identity changed across verification: ' + str(path))
        if archive:
            if not compact or not path.is_relative_to(ROOT):
                raise ValueError('only bounded owned compact artifacts may be archived')
            paths.add(path)
        return raw, observed

    def document(path, *, expected=None, archive=True, canonical_raw=False):
        raw, observed = remember(path, compact=True, expected=expected, archive=archive)
        value = decode(raw)
        if type(value) is not dict or canonical_raw and raw != canonical(value) + b'\n':
            raise ValueError('exact canonical JSON object required: ' + str(path))
        return value, observed[-1]

    pin_path = RUN / 'pins.json'
    pins, pins_sha = document(pin_path)
    fields(pins, {
        'schema': 'cho51_source_fold_fresh_pins_v1', 'canonical_source_sha256': CANONICAL,
        'canonical_files': 432, 'predecessor_files': 574, 'predecessor_pins_sha256': PRIOR_SHA,
        'methods': list(METHODS), 'seconds_per_method': 600, 'process_mib': 4096, 'job_mib': 5120,
        'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20, 'threads': 1,
        'gpu_hidden': True, 'random_initialization_only': True, 'gradient_steps_per_method': 51,
        'source_gradient_updates': 50, 'support_gradient_updates': 1, 'source_subject_count': 52,
        'training_subject_count': 50, 'validation_subject': 'subject_01', 'target_subject': 'subject_02',
        'owner_decision_sha256': OWNER, 'source_fold_only': True,
        'full_5253_gradient_selection_executed': False, 'whole_numerical_worker_verified': False,
        'actual_study_inputs_or_pretrained_weights_permitted': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0,
    })
    if type(pins.get('files')) is not dict or type(pins.get('runtime')) is not dict or len(pins['runtime']) != 5:
        raise ValueError('complete independent source and five-runtime maps required')
    prior, _ = document(PRIOR, expected=PRIOR_SHA, archive=False)
    if (len(prior['files']) != 574 or prior['runtime'] != pins['runtime']
            or any(pins['files'].get(name) != digest for name, digest in prior['files'].items())):
        raise ValueError('all original 574 source and five runtime pins must remain exact')
    manifest, _ = document(ROOT / 'tools/migration/source-files.json', archive=False)
    if (manifest.get('source_sha256') != CANONICAL or len(manifest['files']) != 432
            or any(pins['files'].get(row['path']) != row['sha256'] for row in manifest['files'])):
        raise ValueError('all exact 432 canonical file pins required')

    def relative_path(relative):
        if (type(relative) is not str or PurePosixPath(relative).is_absolute()
                or PurePosixPath(relative).as_posix() != relative
                or any(part in ('', '.', '..') or part.endswith(('.', ' ')) for part in relative.split('/'))
                or re.search(r'[<>:"\\|?*\x00-\x1f]', relative)):
            raise ValueError('safe canonical project-relative path required')
        return PurePosixPath(relative)

    def current_pins():
        if source_check(ROOT) != CANONICAL:
            raise ValueError('canonical source changed')
        remember(pin_path, compact=True, expected=pins_sha)
        for relative, expected in pins['files'].items():
            remember(ROOT.joinpath(*relative_path(relative).parts), expected=expected)
        for name, expected in pins['runtime'].items():
            runtime_paths.add(Path(name))
            remember(Path(name), expected=expected, single_link=False)

    current_pins()
    review_path = RUN / 'source-review.json'
    fields(pins, {'source_review_path': str(review_path)})
    review, _ = document(review_path, expected=pins['source_review_sha256'])
    fields(review, {'source_only': True, 'remaining_actionable_findings': [], 'files': pins['reviewed_files']})
    reviewed = {p.relative_to(ROOT).as_posix() for p in (
        *(CANDIDATE / name for name in ('fixture.py', 'probe.py', 'README.md')),
        *(RUN / name for name in ('child.py', 'closeout.py', 'prepare.py', 'observe.py', 'launch.ps1')))}
    if (set(pins['reviewed_files']) != reviewed
            or set(CANDIDATE.iterdir()) != {CANDIDATE / name for name in ('fixture.py', 'probe.py', 'README.md')}):
        raise ValueError('exact eight reviewed candidate/operational sources required')
    for relative, expected in pins['reviewed_files'].items():
        remember(ROOT / relative, compact=True, expected=expected, archive=True)
    for path in RUN.iterdir():
        if path.is_file() and path.suffix.lower() in {'.py', '.ps1', '.json'}:
            remember(path, compact=True, archive=True)
    launcher_path = ROOT / 'docs/phase2/cho51_tensor_verification_v1/launcher.py'
    remember(launcher_path, expected=pins['files'][launcher_path.relative_to(ROOT).as_posix()])
    spec = importlib.util.spec_from_file_location('_source_fold_closeout_stdlib', launcher_path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    view = {'files': {str(ROOT / name): value for name, value in pins['files'].items()}, 'runtime': pins['runtime']}
    operation_pins, runtime_pins = launcher._guard_operation_pins(view), launcher._guard_runtime_pins(view)
    jobs = []

    def native(directory, command):
        directory = direct(Path(directory))
        if (directory.parent != ROOT / 'runs/migration'
                or re.fullmatch(r'\d{8}T\d{6}Z_[a-f0-9]{10}', directory.name) is None
                or any(row['native_directory'] == str(directory) for row in jobs)):
            raise ValueError('distinct direct independently dispatched native directory required')
        admission, _ = document(directory / 'admission.json')
        receipt, receipt_sha = document(directory / 'receipt.json')
        deadline_document, _ = document(directory / 'deadline.json')
        name = 'pro3_migration_' + directory.name
        fields(admission, {
            'schema': 'migration_admission_v1', 'source_sha256': CANONICAL, 'command': command,
            'operation_pins': operation_pins, 'selected_runtime_pins': runtime_pins,
            'process_mib': 4096, 'job_mib': 5120, 'active_ram_gib': 4, 'active_disk_gib': 20,
            'native_threads': 1, 'peer_pause_file': str(PAUSE),
        })
        fields(receipt, {'schema': 'migration_guard_receipt_v1', 'accepted': True, 'error': None,
            'job_name': name, 'job_absent': True, 'scientific_admission': False})
        state, result = receipt['native_state'], receipt['result']
        flags = ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified',
                 'atomic_job_assignment_requested', 'atomic_job_assignment_verified', 'assigned',
                 'membership_verified', 'resumed', 'job_empty_before_close', 'job_closed',
                 'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen')
        fields(state, dict.fromkeys(flags, True) | {'job_named': name, 'cleanup_errors': [],
            'peak_sampling_errors': [], 'process_limit_bytes': 4096 * 1024**2,
            'aggregate_limit_bytes': 5120 * 1024**2})
        fields(result, {'reason': 'normal', 'exit_code': 0})
        if type(state.get('peak_samples')) is not int or state['peak_samples'] < 1:
            raise ValueError('positive measured native peak sample count required')
        for key, result_key, limit in (
            ('peak_process_commit_bytes', 'peak_process_memory_bytes', 4096 * 1024**2),
            ('peak_job_commit_bytes', 'peak_job_memory_bytes', 5120 * 1024**2),
        ):
            if type(state.get(key)) is not int or not 0 < state[key] <= limit:
                raise ValueError('positive bounded native memory peaks required')
            fields(result, {result_key: state[key]})
        if state['peak_job_commit_bytes'] < state['peak_process_commit_bytes']:
            raise ValueError('native aggregate peak cannot be below process peak')
        samples = admission.get('startup_samples')
        if type(samples) is not list or len(samples) != 2 or receipt.get('startup_samples') != samples:
            raise ValueError('two identical fresh native startup samples required')
        for sample in samples:
            if (type(sample) is not dict or type(sample.get('available_ram_bytes')) is not int
                    or sample['available_ram_bytes'] < 10 * 1024**3
                    or type(sample.get('free_disk_bytes')) is not int or sample['free_disk_bytes'] < 20 * 1024**3):
                raise ValueError('startup RAM10/disk20 floors required')
        start, deadline, end = (utc(value) for value in (
            admission['started_utc'], admission['deadline_utc'], receipt['completed_utc']))
        if (deadline - start).total_seconds() != 600 or not start <= end <= deadline:
            raise ValueError('exact timely 600-second UTC native interval required')
        fields(deadline_document, {'schema': 'phase2_supervision_deadlines_v1',
                                  'attempt_deadline_utc': admission['deadline_utc']})
        if (utc(deadline_document['session_deadline_utc']) - deadline).total_seconds() != 5:
            raise ValueError('exact five-second native session margin required')
        for path in directory.iterdir():
            if path.is_file() and path.name.startswith('command'):
                remember(path, compact=True, archive=True)
        launcher._job_absent(name)
        summary = dict(native_directory=str(directory), job_name=name, seconds=600,
            process_mib=4096, job_mib=5120, started_utc=admission['started_utc'],
            completed_utc=receipt['completed_utc'], elapsed_native_seconds=(end - start).total_seconds(),
            peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes'],
            receipt_sha256=receipt_sha, native_job_closed_empty_freshly_absent=True)
        jobs.append(summary)
        return summary, start, end

    def fixture_inputs(output, result):
        root = output / 'fixture'
        identity, identity_sha = document(root / 'synthetic-input-identity.json', canonical_raw=True)
        fields(identity, {
            'schema': 'cho51_owned_synthetic_fold_inputs_v1', 'synthetic': True,
            'actual_study_data': False, 'scientific_admission': False, 'original_case_attempts_remaining': 0,
            'source_subjects_available': 52, 'adopted_evaluation_targets': 51, 'adopted_case_plan_count': 1020,
            'outer_target': 'subject_02', 'inner_validation_subject': 'subject_01',
            'training_subjects': [f'subject_{subject:02d}' for subject in range(3, 53)],
            'shots_per_class': 5, 'canonical_shot_levels': [1, 5, 10, 20],
            'trials_per_subject': 42, 'trials_per_class': 21,
            'profile_a_shape': [42, 64, 512], 'profile_b_shape': [42, 64, 800],
        })
        logical = dict(identity)
        expected_logical = logical.pop('sha256')
        if hashlib.sha256(canonical(logical)).hexdigest() != sha(expected_logical):
            raise ValueError('synthetic input identity logical digest differs')
        files = identity.get('files')
        if type(files) is not dict or len(files) != 213:
            raise ValueError('exact 213 synthetic input-file inventory required')
        configurations = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
                          'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')
        expected_relative = set(configurations)
        for subject in range(1, 53):
            expected_relative.update((
                f'data/processed/cho2017/profile_a/subject_{subject:02d}.npz',
                f'data/processed/cho2017/profile_b_60hz_v1/subject_{subject:02d}.npz',
                f'data/processed/cho2017/profile_b_60hz_v1/subject_{subject:02d}.manifest.json',
                f'data/raw/moabb/cho2017/subject_{subject:02d}.mat'))
        if set(files) != expected_relative:
            raise ValueError('all52 exact synthetic A/B/manifest/raw-marker paths required')
        fields(result, {'fixture_root': str(root), 'input_identity_path': str(root / 'synthetic-input-identity.json'),
            'input_identity_sha256': expected_logical, 'input_identity_file_sha256': identity_sha,
            'input_file_count': 213, 'input_files': files,
            'physical_inputs': {relative: str(root.joinpath(*PurePosixPath(relative).parts)) for relative in files}})
        fixture_source = hashlib.sha256('\n'.join(
            f'{relative}:{files[relative]["sha256"]}' for relative in sorted(configurations)).encode()).hexdigest()
        fields(result, {'fixture_source_sha256': fixture_source})
        if any(files[relative]['sha256'] != pins['files'][relative] for relative in configurations):
            raise ValueError('fixture must preserve unchanged independently pinned configurations')
        expected_paths, total = set(), 0
        for relative, pin in files.items():
            path = root.joinpath(*relative_path(relative).parts)
            if type(pin) is not dict or set(pin) != {'sha256', 'size_bytes'}:
                raise ValueError('exact physical input size/hash fields required')
            if type(pin['size_bytes']) is not int or not 0 <= pin['size_bytes'] <= 16 * 1024**2:
                raise ValueError('bounded declared synthetic input size required')
            _, observed = remember(path, expected=pin['sha256'])
            if observed[2] != pin['size_bytes']:
                raise ValueError('synthetic input bytes differ')
            expected_paths.add(path)
            total += observed[2]
        fixture_snapshots.append((root, expected_paths))
        return dict(files=len(files), bytes=total, identity_file_sha256=identity_sha,
                    identity_sha256=expected_logical, fixture_source_sha256=fixture_source,
                    protocol_sha256=identity['protocol_sha256'])

    fixture_snapshots, results = [], []
    for method in METHODS:
        output = RUN / f'output_{method}_001'
        command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'child.py'),
                   '--pins', str(pin_path), '--expect-pins', pins_sha, '--output', str(output), '--method', method]
        dispatch, _ = document(RUN / f'dispatch_{method}_001.json')
        dispatch_result, _ = document(RUN / f'dispatch_result_{method}_001.json')
        common = dict(pins_sha256=pins_sha, method=method, child_command=command,
                      expected_output=str(output), scientific_admission=False)
        fields(dispatch, common | {'schema': 'cho51_source_fold_dispatch_v1'})
        fields(dispatch_result, common | {'schema': 'cho51_source_fold_dispatch_result_v1', 'guard_exit_code': 0})
        job, start, end = native(dispatch_result['native_directory'], command)
        if not utc(dispatch['observed_utc']) <= start <= end <= utc(dispatch_result['observed_utc']):
            raise ValueError('independent dispatch UTC timestamps do not bracket native execution')
        q, q_sha = document(output / 'qualification.json')
        fields(q, {
            'schema': 'cho51_source_fold_qualification_v1', 'passed': True, 'method': method,
            'pins_sha256': pins_sha, 'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
            'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
            'source_review_sha256': pins['source_review_sha256'], 'torch_threads': 1, 'torch_interop_threads': 1,
            'gpu_hidden': True, 'unexpected_denials': 0, 'expected_blocked_ipv6_probes': 1,
            'cache_runtime_routed_to_owned_output': True, 'actual_study_inputs_or_pretrained_weights_used': False,
            'whole_numerical_worker_verified': False, 'full_selector_history_verified': False,
            'real_recorder_or_original_attempt_used': False, 'selection_publication_tensor_verified': False,
            'scientific_admission': False, 'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
            'protected_target_fold_read_attempts': [],
            'source_subjects_available': 52, 'training_subject_count': 50,
            'inner_validation_subject': 'subject_01', 'outer_target': 'subject_02',
            'actual_gradient_updates': 51, 'complete': False, 'public_complete_selector_verifier_refused': True,
        })
        if not start <= utc(q['observed_utc']) <= end:
            raise ValueError('qualification UTC timestamp is outside exact admitted execution')
        sha(q['environment_sha256'])
        fields(q.get('observed_numerical_calls'), {'tensor_backward': 51, 'sgd_step': 51})
        expected_probe = dict(event='socket.__new__', classification='blocked_optional_ipv6_import_probe',
            source_file=str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
            source_sha256=pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py'])
        fields(q, {'denied_operations': [expected_probe]})
        loaded = q.get('observed_loaded_module_hashes')
        if type(loaded) is not dict or not loaded or q.get('loaded_module_files') != len(loaded):
            raise ValueError('complete observed post-import module hash inventory required')
        for name, expected in loaded.items():
            remember(Path(name), expected=expected, single_link=Path(name) not in runtime_paths)
        result = q.get('result')
        plan = dict(dataset='cho2017', target_subject='subject_02', method=method,
                    shots_per_class=5, model_seed=11, repetition=1)
        case_id = hashlib.sha256(canonical(plan)).hexdigest()
        fields(result, {
            'schema': 'cho51_public_source_fold_probe_v1', 'passed': True, 'method': method, 'case': plan,
            'case_id': case_id, 'source_subjects_available': 52, 'adopted_evaluation_targets': 51,
            'adopted_case_plan_count': 1020, 'outer_target': 'subject_02', 'inner_validation_subject': 'subject_01',
            'training_subjects': [f'subject_{subject:02d}' for subject in range(3, 53)],
            'candidate_rates': [0.001, 0.0005], 'diagnostic_folds': 1, 'maximum_gradient_steps': 51,
            'source_gradient_updates': 50, 'support_gradient_updates': 1, 'actual_gradient_updates': 51,
            'support_trials': 10, 'inner_query_trials': 2,
            'full_backbone_blocks': None if method == 'eegnet' else 12,
            'full_backbone_embed_dim': None if method == 'eegnet' else 200,
            'public_complete_selector_verifier_refused': True,
            'public_refusal_reason': 'selection evidence has missing or unexpected fields',
            'refusal_boundary': 'raw_incomplete_diagnostic_payload_schema',
            'full_selection_refused_before_fit': True, 'required_selection_updates': 5253,
            'full_selection_refusal_reason': 'requested work exceeds the declared gradient-step ceiling',
            'all_physical_inputs_rehashed_unchanged': True, 'supplied_template_unchanged': True,
            'fixture_source_context_unchanged': True, 'torch_numpy_python_rng_unchanged': True,
            'finite_losses_gradients_parameters': True, 'canonical_source_exclusion_verified': True,
            'actual_public_run_fold': True, 'complete': False, 'selected_candidate': None,
            'full_selector_verified': False, 'full_worker_verified': False, 'publication_performed': False,
            'recorder_used': False, 'measured_cells': 0, 'synthetic': True, 'actual_study_data_loaded': False,
            'pretrained_weights_loaded': False, 'engineering_only': True,
            'scientific_admission': False, 'original_case_attempts_remaining': 0,
        })
        probe_result, _ = document(output / 'probe-result.json', canonical_raw=True)
        if canonical(probe_result) != canonical(result):
            raise ValueError('persisted probe result differs from native child qualification')
        inputs = fixture_inputs(output, result)
        protected = [str(output / 'fixture' / relative) for relative in (
            'data/processed/cho2017/profile_a/subject_02.npz',
            'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz',
            'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json',
            'data/raw/moabb/cho2017/subject_02.mat')]
        fields(result, {'protected_outer_paths': protected})
        fields(q, {'protected_target_input_paths': protected,
            'protected_target_planned_negative_checks': [dict(event='protected_outer_target_read', path=path,
                                                             planned_negative_check=True) for path in protected[:2]]})
        transitions = q.get('protected_target_transitions')
        if type(transitions) is not list or len(transitions) != 2 or [row.get('enabled') for row in transitions] != [True, False]:
            raise ValueError('exact enable/disable outer target protection transitions required')
        for transition in transitions:
            if type(transition.get('enabled')) is not bool:
                raise ValueError('literal protection transition flag required')
        phases = q.get('fixture_input_read_phases')
        if type(phases) is not dict or any(path not in phases for path in protected):
            raise ValueError('complete protected-target phase read counters required')
        for name, counts in phases.items():
            if (not Path(name).is_relative_to(output / 'fixture') or type(counts) is not dict
                    or set(counts) != {'before_protection', 'during_fold', 'after_protection'}
                    or any(type(count) is not int or count < 0 for count in counts.values())):
                raise ValueError('owned literal nonnegative fixture read counters required')
        if any(phases[path]['during_fold'] != 0 for path in protected):
            raise ValueError('outer target was read during public source fold')
        updates = result.get('optimizer_updates')
        if type(updates) is not list or len(updates) != 51:
            raise ValueError('exact 51 actual optimizer update witnesses required')
        for index, update in enumerate(updates, start=1):
            fields(update, dict(update=index, role='source' if index <= 50 else 'inner_validation_support',
                selected_parameters={'eegnet': 2642, 'labram_linear': 402, 'labram_lora': 2002, 'labram_full': 5818138}[method],
                finite_selected_gradients=True, finite_selected_parameters=True))
            if (sha(update['selected_state_sha256_before']) == sha(update['selected_state_sha256_after'])
                    or type(update.get('selected_tensors')) is not int or update['selected_tensors'] <= 0):
                raise ValueError('nonempty finite actual optimizer state update required')
        evidence_path = output / 'fold-evidence.json'
        fields(result, {'fold_evidence_path': str(evidence_path)})
        record, evidence_file_sha = document(evidence_path, expected=result['fold_evidence_file_sha256'], canonical_raw=True)
        if identities[evidence_path][2] != result['fold_evidence_file_bytes']:
            raise ValueError('raw public incomplete fold physical byte count differs')
        payload = record.get('payload')
        envelope = dict(schema_version=1, phase=2, kind='engineering_smoke', payload=payload)
        envelope['sha256'] = hashlib.sha256(canonical(envelope)).hexdigest()
        fields(record, envelope, exact=True)
        if record['sha256'] != result['fold_evidence_sha256']:
            raise ValueError('raw public fold envelope digest differs')
        if type(payload) is not dict or set(payload) != {'purpose', 'contract', 'contract_sha256', 'complete', 'folds', 'selected_candidate'}:
            raise ValueError('raw incomplete diagnostic payload schema must stay unmodified')
        fields(payload, dict(purpose='bounded_eegnet_source_selection' if method == 'eegnet' else 'bounded_labram_source_selection',
                             complete=False, selected_candidate=None, contract_sha256=result['contract_sha256']))
        contract = payload['contract']
        if hashlib.sha256(canonical(contract)).hexdigest() != result['contract_sha256']:
            raise ValueError('raw public fold contract digest differs')
        fields(contract, dict(method=method, dataset='cho2017', outer_target='subject_02', shots_per_class=5,
            maximum_gradient_steps=51, engineering_only=True, scientific_evaluation=False, early_stopping=False,
            protocol_sha256=inputs['protocol_sha256'], candidates=result['declared_candidates']))
        fields(contract.get('source'), {'source_sha256': inputs['fixture_source_sha256']})
        fields(contract.get('runtime'), dict(device='cpu', torch_threads=1))
        if method != 'eegnet':
            fields(contract.get('runtime'), dict(dtype='float32'))
        if 'source_execution' in contract or type(payload['folds']) is not list or len(payload['folds']) != 1:
            raise ValueError('one CPU diagnostic fold without public source execution claim required')
        fold = payload['folds'][0]
        fields(fold, dict(candidate=result['executed_candidate'], validation_subject='subject_01',
                         adapted_state_sha256=result['adapted_state_sha256'],
                         confusion_matrix=result['confusion_matrix'], balanced_accuracy=result['balanced_accuracy']))
        fit = fold['source_fit']
        fields(fit, dict(candidate=result['executed_candidate'], validation_subject='subject_01',
            training_subjects=result['training_subjects'], engineering_only=True,
            initial_state_sha256=result['initial_source_state_sha256'], fitted_state_sha256=result['fitted_source_state_sha256']))
        if type(fit.get('input_identities')) is not dict or set(fit['input_identities']) != set(result['training_subjects']):
            raise ValueError('raw source fit must bind all 50 training inputs and exclude target/validation')
        steps = fit.get('steps')
        if type(steps) is not list or len(steps) != 50:
            raise ValueError('exact 50-source raw public fit steps required')
        previous = sha(fit['initial_state_sha256'])
        for index, (subject, step) in enumerate(zip(result['training_subjects'], steps, strict=True), start=1):
            fields(step, dict(step=index, subject=subject, subject_step=1, iterator_wraps=0))
            if (type(step.get('loss')) not in (int, float) or not math.isfinite(step['loss'])
                    or sha(step['state_sha256_after']) == previous
                    or type(step.get('trial_ids')) is not list or len(step['trial_ids']) != 2
                    or any(type(trial) is not str for trial in step['trial_ids']) or len(set(step['trial_ids'])) != 2):
                raise ValueError('finite distinct source-step state/trial witnesses required')
            previous = step['state_sha256_after']
        if previous != fit['fitted_state_sha256'] or sha(fold['adapted_state_sha256']) == previous:
            raise ValueError('raw actual source/support state transitions differ')
        results.append(dict(method=method, case_id=case_id, qualification_sha256=q_sha,
            fold_evidence_sha256=record['sha256'], fold_evidence_file_sha256=evidence_file_sha,
            inputs=inputs, actual_gradient_updates=51, source_gradient_updates=50, support_gradient_updates=1,
            diagnostic_folds=1, complete=False, selected_candidate=None, **job))

    def exact_input_inventories():
        for root, expected in fixture_snapshots:
            observed = set()
            for folder in (root / 'configs', root / 'data'):
                direct(folder)
                for path in folder.rglob('*'):
                    info = path.lstat()
                    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                        raise ValueError('linked/reparse synthetic input path refused')
                    if stat.S_ISREG(info.st_mode):
                        observed.add(path)
                    elif not stat.S_ISDIR(info.st_mode):
                        raise ValueError('nonregular synthetic fixture entry refused')
            if observed != expected:
                raise ValueError('synthetic input file set changed across public source fold closeout')

    exact_input_inventories()
    current_pins()
    artifacts = [(path, *remember(path, compact=True)) for path in sorted(paths)]
    OUT.mkdir(exist_ok=False)
    manifest_rows, copied = [], {}
    for index, (path, raw, observed) in enumerate(artifacts, start=1):
        target = OUT / 'artifacts' / f'{index:04d}_{path.name}'
        target.parent.mkdir(exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        copied_raw, copied_identity = inspect(target, compact=True)
        if copied_raw != raw or copied_identity[-1] != observed[-1]:
            raise ValueError('short-named compact archive copy differs')
        copied[target] = copied_identity
        remember(path, compact=True)
        manifest_rows.append(dict(source=path.relative_to(ROOT).as_posix(), path=target.relative_to(OUT).as_posix(),
                                  bytes=len(raw), sha256=observed[-1]))
    current_pins()
    exact_input_inventories()
    for path, observed in tuple(identities.items()):
        if inspect(path, single_link=path not in runtime_paths)[1] != observed:
            raise ValueError('validated source/input/native/fold proof changed across archive')
    for path, observed in copied.items():
        if inspect(path, compact=True)[1] != observed:
            raise ValueError('compact archived copy changed before final manifest')
    for job in jobs:
        launcher._job_absent(job['job_name'])
    if len(jobs) != 4 or len(results) != 4:
        raise ValueError('all four independent public-fold native proofs required')
    summary = dict(schema='cho51_source_fold_closeout_v1', observed_utc=datetime.now(timezone.utc).isoformat(),
        passed=True, methods=results, canonical_source_sha256=CANONICAL, canonical_files=432,
        pins_sha256=pins_sha, source_context_pins_rechecked=len(pins['files']), runtime_pins_rechecked=len(pins['runtime']),
        actual_public_run_fold=True, actual_gradient_updates=204, source_gradient_updates=200, support_gradient_updates=4,
        source_subjects_available=52, adopted_evaluation_targets=51, adopted_case_plan_count=1020,
        outer_target='subject_02', inner_validation_subject='subject_01', training_subject_count=50,
        physical_input_files=sum(row['inputs']['files'] for row in results),
        physical_input_bytes=sum(row['inputs']['bytes'] for row in results), input_blobs_archived=False,
        full_architecture_shapes_retained=True, all_four_native_jobs_closed_empty_freshly_absent=True,
        complete=False, selected_candidate=None, full_selector_verified=False, full_worker_verified=False,
        full_5253_gradient_selection_executed=False, selection_publication_tensor_verified=False,
        publication_performed=False, recorder_used=False, measured_cells=0, actual_study_data_loaded=False,
        pretrained_weights_loaded=False, experiment_freeze_signed=False, original_case_attempts_remaining=0,
        scientific_admission=False, peer_release_or_host_quiet_inferred=False, artifact_count=len(manifest_rows))
    write(OUT / 'manifest.json', {'artifacts': manifest_rows})
    write(OUT / 'summary.json', summary)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
