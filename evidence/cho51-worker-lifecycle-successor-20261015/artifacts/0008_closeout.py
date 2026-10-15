"""Fail-closed compact archive of four accepted synthetic engineering lifecycles.

Standard-library source/receipt verification only; never import a numerical
module, restore a state blob, create a recorder or launch another process.
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
OUT = ROOT / 'evidence/cho51-worker-lifecycle-20261015'
VALIDATION = RUN / 'validation_001'
FIXTURE = VALIDATION / 'fixture'
RECORDER = FIXTURE / 'runs/phase2/lifecycle'
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

    def remember(path, *, compact=False, expected=None, single_link=True, archive=False):
        path = Path(path)
        raw, observed = inspect(path, compact=compact, single_link=single_link)
        if expected is not None and observed[-1] != sha(expected):
            raise ValueError('independent file digest differs: ' + str(path))
        previous = identities.setdefault(path, observed)
        if previous != observed:
            raise ValueError('validated physical identity drifted: ' + str(path))
        if archive:
            if not compact or not path.is_relative_to(ROOT):
                raise ValueError('only bounded owned compact artifacts can be archived')
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
        'schema': 'cho51_worker_lifecycle_fresh_pins_v1', 'canonical_source_sha256': CANONICAL,
        'canonical_files': 432, 'predecessor_files': 563, 'methods': list(METHODS),
        'outer_seconds': 600, 'process_mib': 4096, 'job_mib': 6144,
        'seconds_per_method': 300, 'startup_ram_gib': 10, 'active_ram_gib': 4,
        'disk_gib': 20, 'threads': 1, 'gpu_hidden': True,
        'gradient_steps_per_method': 8, 'candidate_rates_per_method': 2,
        'owner_decision_sha256': OWNER, 'random_initialization_only': True,
        'whole_numerical_worker_verified': False,
        'actual_study_inputs_or_pretrained_weights_permitted': False,
        'scientific_admission': False, 'original_case_attempts_remaining': 0,
        'method_limits': {method: {'process_mib': 3072 if method == 'labram_full' else 2048,
                                  'job_mib': 4096 if method == 'labram_full' else 3072}
                          for method in METHODS},
    })
    if (type(pins.get('files')) is not dict or not pins['files']
            or type(pins.get('runtime')) is not dict or len(pins['runtime']) != 5
            or type(pins.get('expected_tests')) is not int or pins['expected_tests'] < 1):
        raise ValueError('complete source/runtime/test inventories required')
    manifest, _ = document(ROOT / 'tools/migration/source-files.json', archive=False)
    if (manifest.get('source_sha256') != CANONICAL or len(manifest['files']) != 432
            or any(pins['files'].get(row['path']) != row['sha256'] for row in manifest['files'])):
        raise ValueError('all exact 432 canonical source file pins required')

    def current_pins():
        if source_check(ROOT) != CANONICAL:
            raise ValueError('canonical source changed')
        remember(pin_path, compact=True, expected=pins_sha)
        for relative, expected in pins['files'].items():
            if (type(relative) is not str or PurePosixPath(relative).is_absolute()
                    or PurePosixPath(relative).as_posix() != relative
                    or any(part in ('', '.', '..') for part in relative.split('/'))
                    or '\\' in relative or ':' in relative):
                raise ValueError('canonical project-relative source pin required')
            remember(ROOT / relative, expected=expected)
        for name, expected in pins['runtime'].items():
            path = Path(name)
            runtime_paths.add(path)
            remember(path, expected=expected, single_link=False)

    current_pins()
    review_path = RUN / 'source-review.json'
    fields(pins, {'source_review_path': str(review_path)})
    review, _ = document(review_path, expected=pins['source_review_sha256'])
    fields(review, {'source_only': True, 'remaining_actionable_findings': [], 'files': pins['reviewed_files']})
    reviewed = {p.relative_to(ROOT).as_posix() for p in (
        *(ROOT / 'docs/phase2/cho51_worker_lifecycle_v1').iterdir(), *RUN.glob('*.py'), *RUN.glob('*.ps1'))
        if p.is_file()}
    if set(pins['reviewed_files']) != reviewed:
        raise ValueError('review must cover every exact candidate/operational source')
    for relative, expected in pins['reviewed_files'].items():
        remember(ROOT / relative, compact=True, expected=expected, archive=True)
    for path in RUN.iterdir():
        if path.is_file() and path.suffix.lower() in {'.py', '.ps1', '.json'}:
            remember(path, compact=True, archive=True)
    launcher_path = ROOT / 'docs/phase2/cho51_tensor_verification_v1/launcher.py'
    remember(launcher_path, compact=True, expected=pins['files'][launcher_path.relative_to(ROOT).as_posix()], archive=True)
    spec = importlib.util.spec_from_file_location('_lifecycle_closeout_stdlib_helper', launcher_path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    view = {'files': {str(ROOT / name): digest for name, digest in pins['files'].items()}, 'runtime': pins['runtime']}
    operations = launcher._guard_operation_pins(view)
    runtimes = launcher._guard_runtime_pins(view)
    jobs = []

    def native(directory, command, seconds, process_mib, job_mib):
        directory = direct(Path(directory))
        if (directory.parent != ROOT / 'runs/migration'
                or re.fullmatch(r'\d{8}T\d{6}Z_[a-f0-9]{10}', directory.name) is None
                or any(job['native_directory'] == str(directory) for job in jobs)):
            raise ValueError('distinct direct newly dispatched native directory required')
        admission, _ = document(directory / 'admission.json')
        receipt, receipt_sha = document(directory / 'receipt.json')
        deadline_document, _ = document(directory / 'deadline.json')
        name = 'pro3_migration_' + directory.name
        fields(admission, {
            'schema': 'migration_admission_v1', 'source_sha256': CANONICAL, 'command': command,
            'operation_pins': operations, 'selected_runtime_pins': runtimes,
            'process_mib': process_mib, 'job_mib': job_mib, 'active_ram_gib': 4,
            'active_disk_gib': 20, 'native_threads': 1, 'peer_pause_file': str(PAUSE),
        })
        fields(receipt, {'schema': 'migration_guard_receipt_v1', 'accepted': True, 'error': None,
                         'job_name': name, 'job_absent': True, 'scientific_admission': False})
        state, result = receipt['native_state'], receipt['result']
        flags = ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified',
                 'atomic_job_assignment_requested', 'atomic_job_assignment_verified', 'assigned',
                 'membership_verified', 'resumed', 'job_empty_before_close', 'job_closed',
                 'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen')
        fields(state, dict.fromkeys(flags, True) | {'job_named': name, 'cleanup_errors': [],
            'peak_sampling_errors': [], 'process_limit_bytes': process_mib * 1024**2,
            'aggregate_limit_bytes': job_mib * 1024**2})
        fields(result, {'reason': 'normal', 'exit_code': 0})
        if type(state.get('peak_samples')) is not int or state['peak_samples'] < 1:
            raise ValueError('positive measured native peak sample count required')
        for field, result_field, limit in (
            ('peak_process_commit_bytes', 'peak_process_memory_bytes', process_mib * 1024**2),
            ('peak_job_commit_bytes', 'peak_job_memory_bytes', job_mib * 1024**2),
        ):
            if type(state.get(field)) is not int or not 0 < state[field] <= limit:
                raise ValueError('positive bounded native peak bytes required')
            fields(result, {result_field: state[field]})
        if state['peak_job_commit_bytes'] < state['peak_process_commit_bytes']:
            raise ValueError('native aggregate peak cannot be below process peak')
        samples = admission.get('startup_samples')
        if type(samples) is not list or len(samples) != 2 or receipt.get('startup_samples') != samples:
            raise ValueError('two identical fresh native startup samples required')
        for sample in samples:
            if (type(sample) is not dict or type(sample.get('available_ram_bytes')) is not int
                    or sample['available_ram_bytes'] < 10 * 1024**3
                    or type(sample.get('free_disk_bytes')) is not int or sample['free_disk_bytes'] < 20 * 1024**3):
                raise ValueError('fresh startup RAM10/disk20 floors required')
        start, deadline, end = (utc(value) for value in (
            admission['started_utc'], admission['deadline_utc'], receipt['completed_utc']))
        if (deadline - start).total_seconds() != seconds or not start <= end <= deadline:
            raise ValueError('exact timely finite UTC native interval required')
        fields(deadline_document, {'schema': 'phase2_supervision_deadlines_v1',
                                  'attempt_deadline_utc': admission['deadline_utc']})
        if (utc(deadline_document['session_deadline_utc']) - deadline).total_seconds() != 5:
            raise ValueError('native session deadline must retain exact five-second margin')
        for path in directory.iterdir():
            if path.is_file() and (path.name == 'deadline.json' or path.name.startswith('command')):
                remember(path, compact=True, archive=True)
        launcher._job_absent(name)
        summary = dict(native_directory=str(directory), job_name=name, seconds=seconds,
            process_mib=process_mib, job_mib=job_mib, started_utc=admission['started_utc'],
            completed_utc=receipt['completed_utc'], elapsed_native_seconds=(end - start).total_seconds(),
            peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes'],
            native_receipt_sha256=receipt_sha, native_job_closed_empty_freshly_absent=True)
        jobs.append(summary)
        return summary, start, end

    parent_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'parent.py'),
                      '--pins', str(pin_path), '--expect-pins', pins_sha, '--output', str(VALIDATION)]
    dispatch, _ = document(RUN / 'dispatch_001.json')
    dispatch_result, _ = document(RUN / 'dispatch_result_001.json')
    shared = {'pins_sha256': pins_sha, 'child_command': parent_command, 'expected_output': str(VALIDATION),
              'scientific_admission': False}
    fields(dispatch, shared | {'schema': 'cho51_worker_lifecycle_dispatch_v1'})
    fields(dispatch_result, shared | {'schema': 'cho51_worker_lifecycle_dispatch_result_v1', 'guard_exit_code': 0})
    outer, outer_start, outer_end = native(dispatch_result['native_directory'], parent_command, 600, 4096, 6144)
    if not utc(dispatch['observed_utc']) <= outer_start <= outer_end <= utc(dispatch_result['observed_utc']):
        raise ValueError('outer native interval differs from independent dispatch timestamps')
    q, _ = document(VALIDATION / 'qualification.json')
    fields(q, {
        'schema': 'cho51_worker_lifecycle_parent_qualification_v1', 'passed': True,
        'pins_sha256': pins_sha, 'pytest_exit': 0, 'collected_tests': pins['expected_tests'],
        'expected_tests': pins['expected_tests'], 'skipped_reports': [], 'engineering_completion': 4,
        'nested_windows_job_compatibility_verified': True, 'measured_cells': 0,
        'fixture_root': str(FIXTURE), 'recorder_root': str(RECORDER),
        'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
        'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
        'torch_threads': 1, 'torch_interop_threads': 1, 'gpu_hidden': True, 'unexpected_denials': 0,
        'actual_study_inputs_or_pretrained_weights_used': False, 'full_worker_verified': False,
        'scientific_admission': False, 'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
    })
    environment = sha(q['environment_sha256'])
    if not outer_start <= utc(q['observed_utc']) <= outer_end:
        raise ValueError('parent qualification UTC is outside admitted execution')
    reports = q.get('reports')
    if (type(reports) is not list or len(reports) != pins['expected_tests']
            or len({row.get('nodeid') for row in reports}) != len(reports)):
        raise ValueError('exact distinct collected/call-passed lifecycle tests required')
    for row in reports:
        fields(row, {'phase': 'call', 'outcome': 'passed'})
        if (type(row.get('nodeid')) is not str
                or not any(row['nodeid'] == node or row['nodeid'].startswith(node + '[') for node in pins['test_nodes'])):
            raise ValueError('test report lies outside independently pinned test nodes')

    def modules_and_audit(value, *, child=False):
        loaded = value.get('observed_loaded_module_hashes')
        if type(loaded) is not dict or not loaded or value.get('loaded_module_files') != len(loaded):
            raise ValueError('complete observed module file inventory required')
        for name, expected in loaded.items():
            remember(Path(name), expected=expected, single_link=Path(name) not in runtime_paths)
        expected_probe = {'event': 'socket.__new__', 'classification': 'blocked_optional_ipv6_import_probe',
                          'source_file': str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
                          'source_sha256': pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py']}
        denied = value.get('denied_operations')
        if type(denied) is not list or len(denied) > 1 or any(row != expected_probe for row in denied):
            raise ValueError('only exact blocked optional IPv6 probe is permitted')
        if child:
            fields(value, {'read_only_git_queries': 0, 'expected_blocked_ipv6_probes': len(denied)})

    modules_and_audit(q)
    for name in ('pytest.log', 'junit.xml'):
        remember(VALIDATION / name, compact=True, archive=True)
    results = q.get('results')
    if (type(results) is not list or len(results) != 4
            or [row.get('method') for row in results] != list(METHODS)):
        raise ValueError('exact ordered four-method parent result roster required')
    weights, case_ids, method_results = [], [], []
    fixture_source = None
    for row in results:
        method = row['method']
        plan = dict(dataset='cho2017', target_subject='subject_02', method=method,
                    shots_per_class=5, model_seed=11, repetition=1)
        case_id = hashlib.sha256(canonical(plan)).hexdigest()
        case_ids.append(case_id)
        workspace = VALIDATION / 'cases' / case_id
        request_path, attestation_path = workspace / 'request.json', workspace / 'parent-attestation.json'
        claim_path = RECORDER / 'claims' / (case_id + '.attempt1.claim.json')
        engineering_receipt = RECORDER / 'engineering_successes' / (case_id + '.success.json')
        limits = pins['method_limits'][method]
        fields(row, {'method': method, 'passed': True, 'request_path': str(request_path),
            'claim_path': str(claim_path), 'attestation_path': str(attestation_path),
            'engineering_receipt': str(engineering_receipt)})
        request, request_sha = document(request_path, expected=row['request_sha256'], canonical_raw=True)
        claim, claim_sha = document(claim_path, expected=row['claim_file_sha256'], canonical_raw=True)
        claim_payload = claim.get('payload')
        if type(claim_payload) is not dict or type(claim_payload.get('source')) is not dict:
            raise ValueError('complete canonical fixture claim source required')
        source = claim_payload['source']
        if (set(source) != {'git_commit', 'source_sha256', 'git_dirty'}
                or type(source['git_commit']) is not str or re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}', source['git_commit']) is None
                or type(source['git_dirty']) is not bool
                or source['source_sha256'] != hashlib.sha256(b'').hexdigest()):
            raise ValueError('empty isolated fixture provenance must remain distinct from real execution source')
        if fixture_source is None:
            fixture_source = source
        if fixture_source != source:
            raise ValueError('four claims must share the same independently bound fixture provenance')
        claim_expected = dict(purpose='pilot_case_claim', case=plan,
            worker='cho51_synthetic_numerical_engineering', attempt=1,
            environment_sha256=environment, source=source, engineering_only=True)

        def envelope(record, payload):
            expected = dict(schema_version=1, phase=2, kind='engineering_smoke', payload=payload)
            expected['sha256'] = hashlib.sha256(canonical(expected)).hexdigest()
            fields(record, expected, exact=True)

        envelope(claim, claim_expected)
        request_expected = dict(schema='cho51_worker_request_v1', case_id=case_id, plan=plan,
            fixture_root=str(FIXTURE), recorder_root=str(RECORDER), workspace=str(workspace),
            pins_path=str(pin_path), independent_pins_sha256=pins_sha, execution_source_sha256=CANONICAL,
            owner_decision_sha256=OWNER, claim_path=str(claim_path), claim_file_sha256=claim_sha,
            fixture_source_sha256=source['source_sha256'], environment_sha256=environment,
            attempt=1, seconds=300, **limits, engineering_only=True, scientific_admission=False,
            original_case_attempts_remaining=0)
        fields(request, request_expected, exact=True)
        inner_dispatch, _ = document(workspace / 'native-dispatch.json')
        child_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'child.py'),
                         '--request', str(request_path), '--expect-request', request_sha]
        fields(inner_dispatch, dict(schema='cho51_worker_lifecycle_inner_dispatch_v1', method=method,
            case_id=case_id, request_sha256=request_sha, claim_file_sha256=claim_sha,
            pins_sha256=pins_sha, child_command=child_command, guard_exit_code=0, scientific_admission=False))
        job, start, end = native(inner_dispatch['native_directory'], child_command, 300, **limits)
        if not outer_start <= start <= end <= outer_end:
            raise ValueError('nested numerical execution must lie inside admitted parent interval')
        qualification_path = workspace / 'child_output/qualification.json'
        child, child_sha = document(qualification_path)
        fields(child, {
            'schema': 'cho51_worker_lifecycle_child_qualification_v1', 'passed': True, 'method': method,
            'pins_sha256': pins_sha, 'request_sha256': request_sha, 'case_id': case_id,
            'claim_file_sha256': claim_sha, 'fixture_source_sha256': source['source_sha256'],
            'owner_decision_sha256': OWNER, 'execution_source_sha256': CANONICAL,
            'environment_sha256': environment, 'canonical_source_sha256': CANONICAL, 'canonical_files': 432,
            'source_pins_rechecked': len(pins['files']), 'runtime_pins_rechecked': len(pins['runtime']),
            'source_review_sha256': pins['source_review_sha256'], 'unexpected_denials': 0,
            'torch_threads': 1, 'torch_interop_threads': 1, 'gpu_hidden': True,
            'cache_runtime_routed_to_owned_output': True, 'actual_study_inputs_or_pretrained_weights_used': False,
            'whole_numerical_worker_verified': False, 'full_selector_history_verified': False,
            'real_recorder_or_original_attempt_used': False, 'selection_publication_tensor_verified': False,
            'scientific_admission': False, 'experiment_freeze_signed': False, 'original_case_attempts_remaining': 0,
        })
        if not start <= utc(child['observed_utc']) <= end:
            raise ValueError('numerical child qualification UTC is outside native interval')
        modules_and_audit(child, child=True)
        fields(child.get('observed_numerical_calls'), {'tensor_backward': 8, 'sgd_step': 8})
        probe = child.get('result')
        fields(probe, {
            'schema': 'cho51_numerical_probe_v1', 'method': method, 'passed': True,
            'rate_cases': 2, 'actual_gradient_updates': 8, 'source_gradient_updates': 4,
            'support_gradient_updates': 4, 'source_examples': 2, 'support_examples': 10,
            'query_examples': 2, 'channels': 64, 'samples': 512 if method == 'eegnet' else 800,
            'model_blocks': 0 if method == 'eegnet' else 12, 'random_initialization': True,
            'full_architecture_shape': True, 'baseline_checkpoint_used': False,
            'source_kernel_fixture_owned': True, 'fixture_rates_are_adopted_candidates': False,
            'public_source_fit_verified': False, 'canonical_source_selector_integration_verified': False,
            'source_cohort_or_selector_used': False, 'recorder_used': False, 'full_worker_verified': False,
            'full_5253_gradient_selection_executed': False, 'scientific_admission': False,
            'original_case_attempts_remaining': 0,
        })
        if type(probe.get('parameter_count')) is not int or probe['parameter_count'] <= 0:
            raise ValueError('positive model parameter count required')
        checks = probe.get('checks')
        if type(checks) is not list or len(checks) != 2:
            raise ValueError('two complete finite-rate witnesses required')
        positive = ('finite_logits', 'finite_losses', 'finite_selected_gradients', 'finite_parameters',
            'updates_nonempty_within_mask', 'frozen_state_unchanged', 'source_unchanged', 'rng_unchanged',
            'no_storage_alias', 'query_state_unchanged', 'exact_replay', 'state_roundtrip_exact',
            'query_roundtrip_exact', 'fixture_inputs_unchanged', 'changed_source_and_support_parameters_only_within_mask')
        for index, check in enumerate(checks, start=1):
            fields(check, dict.fromkeys(positive, True) | {'source_gradient_updates': 2,
                'support_gradient_updates': 2, 'actual_gradient_updates': 4})
            rate = check.get('rate')
            if type(rate) not in (int, float) or rate != (0.001, 0.0005)[index - 1]:
                raise ValueError('exact two fixture rates required')
            names = check.get('selected_parameter_names')
            if (type(names) is not list or not names or any(type(name) is not str or not name for name in names)
                    or len(set(names)) != len(names)):
                raise ValueError('distinct nonempty selected parameter mask required')
            losses = check.get('source_losses')
            if (type(losses) is not list or len(losses) != 2
                    or any(type(loss) not in (int, float) or not math.isfinite(loss)
                           for loss in [*losses, check.get('support_loss'), check.get('replay_support_loss')])):
                raise ValueError('complete finite numerical loss witnesses required')
            for key in ('source_state_sha256', 'adapted_state_sha256', 'weights_sha256'):
                sha(check.get(key))
            if method == 'labram_lora':
                fields(check, dict.fromkeys(('lora_initial_zero_b_effective_identity_verified',
                    'lora_source_and_support_both_matrices_updated', 'lora_source_and_support_effective_qkv_changed'), True))
            weight = workspace / f'child_output/rate_{index:02d}_fullstate.safetensors'
            _, weight_identity = remember(weight, expected=check['weights_sha256'])
            if (check.get('weights_file') != str(weight) or type(check.get('weights_bytes')) is not int
                    or not 0 < check['weights_bytes'] <= 25 * 1024**2 or check['weights_bytes'] != weight_identity[2]):
                raise ValueError('direct bounded unarchived full-state bytes differ')
            weights.append(dict(path=weight.relative_to(ROOT).as_posix(), sha256=weight_identity[-1],
                                bytes=weight_identity[2], archived=False))
        proof_expected = dict(request_sha256=request_sha, case_id=case_id, claim_file_sha256=claim_sha,
            execution_source_sha256=CANONICAL, independent_pins_sha256=pins_sha, owner_decision_sha256=OWNER,
            environment_sha256=environment, native_directory=job['native_directory'],
            native_receipt_file_sha256=job['native_receipt_sha256'], qualification_path=str(qualification_path),
            qualification_file_sha256=child_sha, peak_process_bytes=job['peak_process_bytes'],
            peak_job_bytes=job['peak_job_bytes'], actual_gradient_updates=8,
            native_job_closed_empty_absent=True, engineering_only=True, scientific_admission=False,
            original_case_attempts_remaining=0)
        fields(row.get('proof'), proof_expected, exact=True)
        attestation, attestation_sha = document(attestation_path, expected=row['attestation_file_sha256'], canonical_raw=True)
        fields(attestation, dict(schema='cho51_worker_parent_attestation_v1', request_sha256=request_sha,
            case_id=case_id, claim_file_sha256=claim_sha, proof=proof_expected, engineering_only=True,
            scientific_admission=False, original_case_attempts_remaining=0), exact=True)
        for directory, purpose, suffix in (
            ('engineering_intents', 'pilot_case_engineering_success_intent', '.intent.json'),
            ('engineering_successes', 'pilot_case_engineering_success', '.success.json'),
        ):
            record, _ = document(RECORDER / directory / (case_id + suffix), canonical_raw=True)
            envelope(record, dict(purpose=purpose, case=plan, attempt=1,
                                  attested_evidence_sha256=attestation_sha, engineering_only=True))
        for name in ('guard-stdout.txt', 'guard-stderr.txt'):
            remember(workspace / name, compact=True, archive=True)
        method_results.append(dict(method=method, case_id=case_id, request_sha256=request_sha,
            claim_file_sha256=claim_sha, parent_attestation_sha256=attestation_sha,
            qualification_sha256=child_sha, actual_gradient_updates=8, rate_cases=2, **job))

    def exact_inventories():
        for directory, suffix in (('claims', '.attempt1.claim.json'), ('engineering_intents', '.intent.json'),
                                  ('engineering_successes', '.success.json')):
            path = direct(RECORDER / directory)
            if {child.name for child in path.iterdir()} != {case + suffix for case in case_ids}:
                raise ValueError('exact four-case engineering recorder inventory required')
        for name in ('cells', 'successes', 'publication_intents', 'attempts'):
            path = RECORDER / name
            if path.exists() or path.is_symlink():
                direct(path)
                if not path.is_dir() or list(path.iterdir()):
                    raise ValueError('scientific/failure recorder directories must remain empty')
        if {child.name for child in direct(VALIDATION / 'cases').iterdir()} != set(case_ids):
            raise ValueError('exact four-request case workspace inventory required')

    exact_inventories()
    current_pins()
    artifacts = []
    for path in sorted(paths):
        raw, observed = remember(path, compact=True)
        artifacts.append((path, raw, observed))
    # Reserve the archive only after every independent proof has passed.
    OUT.mkdir(exist_ok=False)
    manifest_rows, copied_identities = [], {}
    for path, raw, observed in artifacts:
        target = OUT / 'artifacts' / path.relative_to(ROOT)
        io_path(target.parent).mkdir(parents=True, exist_ok=True)
        with io_path(target).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        copied_raw, copied_identity = inspect(target, compact=True)
        if copied_raw != raw or copied_identity[-1] != observed[-1]:
            raise ValueError('compact artifact copy differs')
        copied_identities[target] = copied_identity
        remember(path, compact=True)
        manifest_rows.append(dict(source=path.relative_to(ROOT).as_posix(),
            path=target.relative_to(OUT).as_posix(), bytes=len(raw), sha256=observed[-1]))
    current_pins()
    exact_inventories()
    for path, observed in tuple(identities.items()):
        if inspect(path, single_link=path not in runtime_paths)[1] != observed:
            raise ValueError('validated source/native/request/blob identity changed across archival')
    for path, observed in copied_identities.items():
        if inspect(path, compact=True)[1] != observed:
            raise ValueError('archived compact artifact identity changed before final manifest')
    for job in jobs:
        launcher._job_absent(job['job_name'])
    if len(jobs) != 5 or len(weights) != 8:
        raise ValueError('exact five supervised Jobs and eight persisted states required')
    summary = dict(schema='cho51_worker_lifecycle_closeout_v1', observed_utc=datetime.now(timezone.utc).isoformat(),
        passed=True, engineering_completion=4, measured_cells=0, methods=method_results, jobs=jobs,
        pins_sha256=pins_sha, canonical_source_sha256=CANONICAL, canonical_files=432,
        source_context_pins_rechecked=len(pins['files']), runtime_pins_rechecked=len(pins['runtime']),
        fixture_source=fixture_source, environment_sha256=environment, boundary_tests=pins['expected_tests'],
        claims=4, engineering_intents=4, engineering_successes=4, scientific_cells=0,
        scientific_successes=0, scientific_publication_intents=0, failures=0,
        actual_gradient_updates=32, persisted_full_states=8, unarchived_states=weights,
        unarchived_state_bytes=sum(row['bytes'] for row in weights), artifact_count=len(manifest_rows),
        nested_windows_job_compatibility_verified=True, actual_study_inputs_or_pretrained_weights_used=False,
        complete_1020_case_roster_verified=False, full_worker_verified=False,
        full_selector_history_verified=False, selection_publication_tensor_verified=False,
        canonical_source_selector_integration_verified=False, full_5253_gradient_selection_executed=False,
        experiment_freeze_signed=False, original_case_attempts_remaining=0, scientific_admission=False,
        peer_release_or_host_quiet_inferred=False)
    write(OUT / 'manifest.json', {'artifacts': manifest_rows})
    write(OUT / 'summary.json', summary)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
