"""Frozen split contract and independently coordinated metadata-only aggregate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
FAMILY = 'cho51_canonical_boundary_20261025_v5'
SCOPE = FAMILY + '_aggregate'
PLAN = ROOT / 'docs/phase2/cho51_canonical_boundary_batch_plan_20261025.json'
PLAN_SHA = 'd1467ae85739115f2f65ab1ca23a8f6624b1a09d1a6b40384f64c07eab62497f'
SCOPE_DOCUMENT = ROOT / 'docs/phase2/cho51_canonical_boundary_split_validation_20261025.md'
DOCUMENT_SHA = 'e792de74461fe54269714c0e3a175ee6ee357ed99943ac345a54c7b6f48bb55b'
PREFIX = 'docs/phase2/cho51_canonical_boundary_v1/test_boundary.py::'
BATCH_COUNTS = {'a': 36, 'b': 44, 'c': 53}
OPERATIONS = ('metadata_common.py', 'guard.py', 'runner.py', 'closeout.py', 'prepare.ps1', 'launch.ps1')
CONTROL_NAMES = ('finite_json', 'duplicate_json', 'nan_json', 'overflow_json', 'nested_json',
    'zero_budget', 'boolean_budget', 'owned_path', 'escaped_path', 'first_create', 'duplicate_create',
    'bounded_tail', 'full_window', 'short_window', 'junit_baseline', 'junit_duplicate',
    'junit_failure', 'junit_class', 'reports_baseline', 'reports_missing', 'reports_duplicate',
    'git_actual_spelling_list', 'git_actual_spelling_cmdline', 'git_status_tail', 'git_explicit_case_spelling',
    'git_alternate_executable', 'git_alternate_argument_executable', 'git_invalid_tail',
    'git_explicit_environment', 'git_descendant_cwd', 'git_relative_cwd',
    'pytest_alias_owned_paths', 'pytest_alias_outside_paths', 'pytest_alias_outside_destination')
ZERO = dict(source_updates=0, restore_count=0, support_updates=0, gradient_updates=0,
            target_inference_calls=0, query_count=0, model_constructions=0, measured_cells=0)
PAUSES = tuple(Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json'
               for day in ('20261007', '20261012', '20261013', '20261015', '20261025'))


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def parse(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate metadata key')
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite metadata')))
    canonical(value)
    return value


def key(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def direct(path, *, existing=True):
    need(type(path) is type(ROOT) and path.is_absolute() and path.resolve(strict=existing) == path,
         'direct absolute metadata path required')
    identities = []
    for ancestor in (path, *path.parents):
        try:
            info = ancestor.lstat()
        except FileNotFoundError:
            need(not existing and ancestor == path, 'metadata ancestor is missing')
            continue
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 1024,
             'metadata reparse path refused')
        if ancestor != path:
            need(stat.S_ISDIR(info.st_mode), 'regular metadata directory ancestor required')
            identities.append((str(ancestor), info.st_dev, info.st_ino, info.st_ctime_ns))
    return tuple(identities)


def read(path, expected=None):
    ancestors = direct(path)
    before = path.stat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 <= before.st_size <= 8 * 1024**2,
         'bounded single-link regular metadata required')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(8 * 1024**2 + 1)
        finished = os.fstat(stream.fileno())
    after = path.stat()
    need(direct(path) == ancestors, 'metadata ancestor identity changed')
    need(key(before) == key(after) and key(opened) == key(finished) and key(before)[:4] == key(opened)[:4]
         and opened.st_nlink == finished.st_nlink == 1 and len(raw) == before.st_size,
         'metadata physical identity changed')
    digest = hashlib.sha256(raw).hexdigest()
    need(expected is None or digest == expected, 'external metadata byte pin differs')
    return raw


def document(path, expected=None):
    return parse(read(path, expected))


def plan():
    value = document(PLAN, PLAN_SHA)
    read(SCOPE_DOCUMENT, DOCUMENT_SHA)
    need(value['schema'] == 'cho51_canonical_boundary_batch_plan_v1' and value['family'] == FAMILY
         and value['batch_order'] == list(BATCH_COUNTS) and value['expected_full_tests'] == 133
         and value['expected_definitions'] == 29 and value['expected_stdlib_controls_per_batch'] == 34
         and value['scientific_admission'] is False, 'exact frozen split plan required')
    names = []
    for batch, count in BATCH_COUNTS.items():
        row = value['batches'][batch]
        need(type(row['expected_tests']) is int and row['expected_tests'] == count
             and row['scope'] == FAMILY + '_' + batch + '_tests'
             and type(row['function_counts']) is dict
             and all(type(member) is int and member > 0 for member in row['function_counts'].values())
             and sum(row['function_counts'].values()) == count, 'exact complementary batch required')
        names.extend(row['function_counts'])
    need(len(names) == len(set(names)) == 29, 'disjoint complete function roster required')
    return value


def header(batch):
    value = plan()['batches'][batch]
    return dict(batch_id=batch, batch_plan_sha256=PLAN_SHA, expected_full_tests=133,
                batch_functions=list(value['function_counts']), batch_function_counts=value['function_counts'])


def header_matches(record, batch):
    expected = header(batch)
    return canonical({name: record.get(name) for name in expected}) == canonical(expected)


def source_relatives():
    value = plan()
    paths = list(value['candidate_files'])
    paths.extend(f'runs/coordination/{FAMILY}_{batch}/{name}' for batch in BATCH_COUNTS for name in OPERATIONS)
    paths.append(f'runs/coordination/{FAMILY}_aggregate/aggregate.py')
    return tuple(paths)


def split_collection(full, batch):
    value = plan()
    need(type(full) is list and len(full) == 133 and all(type(node) is str and node.startswith(PREFIX) for node in full)
         and len(set(full)) == 133, 'genuine complete unique133 collection required')
    functions = {name: count for row in value['batches'].values() for name, count in row['function_counts'].items()}
    actual = Counter(node[len(PREFIX):].split('[', 1)[0] for node in full)
    need(dict(actual) == functions, 'all29 full-collection function multiplicities must match the plan')
    allowed = value['batches'][batch]['function_counts']
    selected = [node for node in full if node[len(PREFIX):].split('[', 1)[0] in allowed]
    deselected = [node for node in full if node[len(PREFIX):].split('[', 1)[0] not in allowed]
    need(len(selected) == BATCH_COUNTS[batch] and len(deselected) == 133 - BATCH_COUNTS[batch],
         'exact planned selected/deselected counts required')
    return selected, deselected


def verify_split(result, batch):
    need(header_matches(result, batch), 'result batch contract differs')
    selected, deselected = split_collection(result['full_collection'], batch)
    need(result['collected'] == selected and result['deselected'] == deselected
         and result['full_collection_sha256'] == hashlib.sha256(canonical(result['full_collection'])).hexdigest(),
         'exact ordered full/selected/complementary inventories required')


def zero(value):
    return type(value) is dict and set(value) == set(ZERO) and all(type(member) is int and member == 0 for member in value.values())


def reports_and_junit(result, raw, count):
    ids = result['collected']
    need(len(ids) == len(set(ids)) == count, 'exact selected inventory required')
    expected = {(node, phase) for node in ids for phase in ('setup', 'call', 'teardown')}
    rows = result['reports']
    actual = [(row['nodeid'], row['phase']) for row in rows]
    need(len(actual) == len(set(actual)) == len(expected) and set(actual) == expected
         and all(row['outcome'] == 'passed' for row in rows), 'all selected three-phase reports must pass')
    xml = ET.fromstring(raw)
    suites = list(xml.iter('testsuite'))
    cases = [(node.attrib.get('classname'), node.attrib.get('name')) for node in xml.iter('testcase')]
    expected_cases = {('docs.phase2.cho51_canonical_boundary_v1.test_boundary', node[len(PREFIX):]) for node in ids}
    need(sum(int(node.attrib['tests']) for node in suites) == count
         and all(int(node.attrib.get(field, '0')) == 0 for node in suites for field in ('failures', 'errors', 'skipped'))
         and len(cases) == len(set(cases)) == count and set(cases) == expected_cases
         and not any(list(xml.iter(tag)) for tag in ('failure', 'error', 'skipped')), 'physical selected JUnit agreement required')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-proofs', required=True)
    parser.add_argument('--expect-admission', required=True)
    arguments = parser.parse_args()
    need(not any(path.exists() for path in PAUSES), 'genuine peer pause requested')
    need(not (RUN / 'result.json').exists() and not (RUN / 'attempt_001.json').exists(), 'aggregate is once-only')
    approved = document(RUN / 'admission.json', arguments.expect_admission)
    request = document(RUN / 'proofs.json', arguments.expect_proofs)
    expected_admission = dict(schema='cho51_canonical_boundary_aggregate_admission_v1', accepted=True,
        scope=SCOPE, proofs_sha256=arguments.expect_proofs, batch_plan_sha256=PLAN_SHA,
        maximum_jobs=0, maximum_interpreter_invocations=1, maximum_seconds=300,
        expected_historical_metadata_tests=133, expected_batches=3, expected_controls_per_batch=34,
        startup_ram_gib=4, active_ram_gib=4, disk_gib=20, automatic_retry_permitted=False, scientific_admission=False)
    need(all(type(approved.get(name)) is type(member) and approved[name] == member for name, member in expected_admission.items())
         and zero(approved['expected_numerical_budget']), 'fresh exact bounded aggregate admission required')
    read(Path(__file__).resolve(), approved['aggregate_source_sha256'])
    peer = document(Path(approved['peer_release_path']), approved['peer_release_sha256'])
    expected_peer = {name: member for name, member in expected_admission.items() if name not in ('schema', 'accepted')}
    expected_peer.update(schema='pro2_pro3_compute_release_v1', released=True)
    need(all(type(peer.get(name)) is type(member) and peer[name] == member for name, member in expected_peer.items())
         and zero(peer['expected_numerical_budget']), 'fresh explicitly scoped zero-Job aggregate peer grant required')
    now = datetime.now(timezone.utc)
    need(type(approved.get('observed_utc')) is str, 'aggregate admission UTC observation required')
    approved_time = datetime.fromisoformat(approved['observed_utc']).astimezone(timezone.utc)
    need(approved_time <= now, 'aggregate admission cannot be future dated')
    need(all(type(approved[name]) is str and approved[name] == peer[name] for name in ('window_start_utc', 'window_end_utc'))
         and datetime.fromisoformat(peer['window_start_utc']).astimezone(timezone.utc) <= now
         <= datetime.fromisoformat(peer['window_end_utc']).astimezone(timezone.utc), 'live exact aggregate custody window required')
    deadline = datetime.fromisoformat(approved['deadline_utc']).astimezone(timezone.utc)
    need(now < deadline <= now + timedelta(seconds=300)
         and deadline <= datetime.fromisoformat(peer['window_end_utc']).astimezone(timezone.utc), 'bounded aggregate deadline required')
    direct(RUN / 'attempt_001.json', existing=False)
    with (RUN / 'attempt_001.json').open('xb') as stream:
        stream.write(canonical(dict(schema='cho51_canonical_boundary_aggregate_attempt_v1',
            observed_utc=now.isoformat(), admission_sha256=arguments.expect_admission,
            proofs_sha256=arguments.expect_proofs, batch_plan_sha256=PLAN_SHA,
            maximum_jobs=0, maximum_interpreter_invocations=1, automatic_retry_permitted=False,
            scientific_admission=False)))
        stream.flush()
        os.fsync(stream.fileno())
    need(type(request) is dict and set(request) == {'schema', 'batch_plan_sha256', 'batches'}
         and request['schema'] == 'cho51_canonical_boundary_aggregate_proofs_v1'
         and request['batch_plan_sha256'] == PLAN_SHA and set(request['batches']) == set(BATCH_COUNTS),
         'exact externally pinned three-batch proof manifest required')
    total_bytes, reads = 0, 0

    def checked(path, digest):
        nonlocal total_bytes, reads
        need(datetime.now(timezone.utc) < deadline and not any(item.exists() for item in PAUSES), 'aggregate deadline or pause')
        raw = read(path, digest)
        reads += 1
        total_bytes += len(raw)
        need(reads <= 256 and total_bytes <= 64 * 1024**2, 'bounded three-archive metadata verification required')
        return raw

    def proof(specification, expected_path=None, *, authenticated_peer=False):
        need(type(specification) is dict and set(specification) == {'path', 'sha256'}
             and type(specification['path']) is str and type(specification['sha256']) is str
             and re.fullmatch('[0-9a-f]{64}', specification['sha256']) is not None,
             'external proof path/hash required')
        path = Path(specification['path'])
        need((path.is_relative_to(ROOT) or authenticated_peer and expected_path is not None)
             and (expected_path is None or path == expected_path), 'proof path substitution refused')
        return checked(path, specification['sha256'])

    common_files, common_runtime, common_sources, common_full = None, None, None, None
    selected_union = set()
    accepted = {}
    previous_release = None
    for batch, count in BATCH_COUNTS.items():
        current = request['batches'][batch]
        need(set(current) == {'pins', 'result', 'closeout', 'lease', 'junit', 'native_receipt', 'native_admission',
                             'native_deadline', 'root_admission', 'peer_grant', 'external_supervision', 'archive_manifest'},
             'complete exact per-batch proof references required')
        run = ROOT / f'runs/coordination/{FAMILY}_{batch}'
        pins = parse(proof(current['pins'], run / 'pins.json'))
        result = parse(proof(current['result'], run / 't1/result.json'))
        closed = parse(proof(current['closeout'], run / 'closeout-result.json'))
        lease = parse(proof(current['lease'], run / 'lease-closeout_001.json'))
        supervision = parse(proof(current['external_supervision'], run / 'closeout-supervision_001.json'))
        root_admission = parse(proof(current['root_admission'], run / 'admission.json'))
        need(header_matches(pins, batch) and header_matches(result, batch) and header_matches(closed, batch)
             and pins['expected_tests'] == count and pins['expected_stdlib_controls'] == 34
             and result['pins_sha256'] == closed['pins_sha256'] == lease['pins_sha256'] == current['pins']['sha256']
             and closed['source_review_sha256'] == pins['source_review_sha256'],
             'exact batch/source pins and closed proof joins required')
        need(set(pins['reviewed_files']) == set(source_relatives()), 'complete frozen family source inventory required')
        source_review = parse(checked(run / 'source-review.json', pins['source_review_sha256']))
        need(source_review['source_only'] is True and source_review['remaining_actionable_findings'] == []
             and source_review['files'] == pins['reviewed_files'] and header_matches(source_review, batch),
             'accepted frozen family source review required')
        if common_files is None:
            common_files, common_runtime, common_sources = pins['files'], pins['runtime_files'], pins['reviewed_files']
            for relative, digest in common_sources.items():
                checked(ROOT / relative, digest)
            need(all(common_sources[relative] == digest for relative, digest in plan()['candidate_files'].items()),
                 'unchanged accepted candidate3 bytes required')
        need(pins['files'] == common_files and pins['runtime_files'] == common_runtime
             and pins['reviewed_files'] == common_sources and len(common_runtime) == 27,
             'identical whole installed-source/runtime/family pin maps required')
        verify_split(result, batch)
        need(common_full is None or result['full_collection'] == common_full, 'identical ordered genuine full133 collections required')
        common_full = result['full_collection']
        need(not selected_union.intersection(result['collected']), 'complementary selected batches cannot overlap')
        selected_union.update(result['collected'])
        reports_and_junit(result, proof(current['junit'], run / 't1/junit.xml'), count)
        controls = result['stdlib_controls']
        need(result['passed'] is True and result['pytest_exit'] == 0 and zero(result['current_counter_ledger'])
             and result['forbidden_calls'] == {} and result['unexpected_denials'] == []
             and type(controls) is dict and set(controls) == set(CONTROL_NAMES)
             and len(controls) == result['stdlib_control_count'] == 34
             and all(member is True for member in controls.values()), 'complete selected pass and34 controls per batch required')
        need(closed['passed'] is True and closed['tests'] == count and closed['stdlib_guard_controls'] == 34
             and zero(closed['current_counter_ledger']) and closed['normal_exit'] == 0
             and closed['scientific_admission'] is False and closed['raw_inputs_verified'] is False
             and closed['weights_verified'] is False and closed['runtime_for_future_execution_qualified'] is False
             and closed['external_native_verified'] is True and closed['child_flag_remains_pending'] is True
             and result['native_closeout_status'] == 'pending_external_post_job'
             and closed['canonical_sources'] == 432 and closed['source_sha256'] == plan()['canonical_sha256'],
             'accepted external metadata-only closeout required')
        native = Path(closed['native_directory'])
        need(native.parent == ROOT / 'runs/migration' and re.fullmatch(r'\d{8}T\d{6}Z_[0-9a-f]{10}', native.name) is not None,
             'exact historical native directory required')
        receipt = parse(proof(current['native_receipt'], native / 'receipt.json'))
        admission = parse(proof(current['native_admission'], native / 'admission.json'))
        native_deadline = parse(proof(current['native_deadline'], native / 'deadline.json'))
        peer_record = parse(proof(current['peer_grant'], Path(root_admission['peer_release_path']), authenticated_peer=True))
        need(current['peer_grant']['path'] == root_admission['peer_release_path']
             and current['peer_grant']['sha256'] == root_admission['peer_release_sha256'] == lease['peer_release_sha256']
             and peer_record['scope'] == root_admission['scope'] == lease['scope'] == FAMILY + '_' + batch + '_tests'
             and header_matches(root_admission, batch) and header_matches(peer_record, batch), 'exact historical peer/Root batch joins required')
        expected_phase = dict(scope=FAMILY + '_' + batch + '_tests', pins_sha256=current['pins']['sha256'],
            maximum_jobs=1, max_job_seconds=600, process_mib=4096, job_mib=5120, startup_ram_gib=4,
            active_ram_gib=4, disk_gib=20, expected_metadata_tests=count, expected_stdlib_controls=34,
            external_stdlib_closeout_maximum_seconds=300, threads=1, torch_threads=1, gpu_hidden=True,
            source_review_sha256=pins['source_review_sha256'],
            owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256'],
            automatic_retry_permitted=False, scientific_admission=False)
        for record in (root_admission, peer_record):
            need(all(type(record.get(name)) is type(member) and record[name] == member for name, member in expected_phase.items())
                 and zero(record['expected_numerical_budget']), 'exact typed historical phase admission and caps required')
        need(root_admission['schema'] == 'cho51_canonical_boundary_admission_v1'
             and peer_record['schema'] == 'pro2_pro3_compute_release_v1'
             and root_admission['accepted'] is True and peer_record['released'] is True
             and root_admission['automatic_retry_permitted'] is False
             and admission['pins_sha256'] == current['pins']['sha256']
             and admission['root_admission_sha256'] == current['root_admission']['sha256']
             and result['root_admission_sha256'] == current['root_admission']['sha256']
             and result['native_admission_sha256'] == current['native_admission']['sha256']
             and admission['peer_release_sha256'] == result['peer_release_sha256'] == current['peer_grant']['sha256'],
             'native/child/Root/peer byte joins required')
        amendment_path = run / 'owner-resource-amendment.json'
        need(root_admission['owner_resource_amendment_path'] == str(amendment_path)
             and pins['files'].get(str(amendment_path)) == pins['owner_resource_amendment_sha256'],
             'historical owner amendment path and full-pin binding required')
        amendment = parse(checked(amendment_path, pins['owner_resource_amendment_sha256']))
        need(amendment['scope'] == expected_phase['scope']
             and amendment['owner_instruction_exact'] == 'use what you have . i have freed the ram you have more now!'
             and amendment['startup_ram_gib'] == amendment['active_ram_gib'] == 4
             and amendment['canonical_guard_modified'] is False and amendment['scientific_admission'] is False,
             'same bounded owner resource authority required')
        command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(run / 'runner.py'),
                   '--pins', str(run / 'pins.json'), '--expect-pins', current['pins']['sha256'],
                   '--output', str(run / 't1')]
        selected_runtime = {path: digest for path, digest in pins['runtime_files'].items()
            if Path(path) == ROOT / '.venv/Scripts/python.exe' or Path(path).name in {'python3.dll', 'python312.dll'}}
        operations = {Path(path).relative_to(ROOT).as_posix(): digest for path, digest in pins['files'].items()
            if Path(path).parent == ROOT / 'tools/migration' and Path(path).suffix in {'.py', '.ps1', '.json', '.lock'}}
        primitive = 'evaluation/phase2_supervision_primitives.py'
        operations[primitive] = pins['files'][str(ROOT / primitive)]
        need(admission['command'] == command and admission['source_sha256'] == result['source_sha256'] == plan()['canonical_sha256']
             and len(selected_runtime) == 3 and admission['selected_runtime_pins'] == selected_runtime
             and admission['operation_pins'] == operations, 'actual native command/source/runtime/operation bindings required')
        need(receipt['accepted'] is True and receipt['result']['reason'] == 'normal' and receipt['result']['exit_code'] == 0
             and receipt['error'] is None and receipt['job_absent'] is True
             and receipt['job_name'] == result['job_name'] == closed['job_name'] == lease['native_job_name'] == 'pro3_migration_' + native.name
             and closed['native_receipt_sha256'] == lease['native_receipt_sha256'] == current['native_receipt']['sha256'],
             'historical accepted normal-zero native receipt required')
        state = receipt['native_state']
        for name in ('created_suspended', 'atomic_job_assignment_verified', 'limits_set', 'limits_query_verified', 'membership_verified',
                     'job_empty_before_close', 'job_closed', 'process_handle_closed', 'thread_handle_closed'):
            need(state[name] is True, 'complete native assignment and closure required')
        need(state['cleanup_errors'] == state['peak_sampling_errors'] == []
             and type(state['limit_flags']) is int and state['limit_flags'] == 8960
             and state['process_limit_bytes'] == 4096 * 1024**2 and state['aggregate_limit_bytes'] == 5120 * 1024**2
             and state['peak_process_commit_bytes'] <= 4096 * 1024**2 and state['peak_job_commit_bytes'] <= 5120 * 1024**2,
             'unchanged queried native caps and clean closure required')
        started = datetime.fromisoformat(admission['started_utc']).astimezone(timezone.utc)
        ended = datetime.fromisoformat(receipt['completed_utc']).astimezone(timezone.utc)
        attempt = datetime.fromisoformat(native_deadline['attempt_deadline_utc']).astimezone(timezone.utc)
        session = datetime.fromisoformat(native_deadline['session_deadline_utc']).astimezone(timezone.utc)
        need((attempt - started).total_seconds() == 600 and (session - attempt).total_seconds() == 5 and started <= ended <= attempt
             and started >= datetime.fromisoformat(peer_record['window_start_utc']).astimezone(timezone.utc)
             and session <= datetime.fromisoformat(peer_record['window_end_utc']).astimezone(timezone.utc), 'historical native600-second custody required')
        need(len(admission['startup_samples']) == 2 and admission['startup_ram_gib'] == admission['active_ram_gib'] == 4
             and admission['active_disk_gib'] == 20 and admission['native_threads'] == 1,
             'unchanged native startup/active/thread settings required')
        for sample in admission['startup_samples']:
            need(type(sample['available_ram_bytes']) is int and sample['available_ram_bytes'] >= 4 * 1024**3
                 and type(sample['free_disk_bytes']) is int and sample['free_disk_bytes'] >= 20 * 1024**3,
                 'two genuine admitted native resource samples required')
        need(supervision['exit_code'] == 0 and supervision['limit_seconds'] == 300
             and 0 <= supervision['elapsed_seconds'] <= 300 and supervision['timed_out'] is False
             and supervision['owned_tree_reaped'] is True and supervision['stdout_eof'] is True and supervision['stderr_eof'] is True,
             'actual external supervised closeout and reaping required')
        external_start = datetime.fromisoformat(supervision['started_utc']).astimezone(timezone.utc)
        external_end = datetime.fromisoformat(supervision['ended_utc']).astimezone(timezone.utc)
        released = datetime.fromisoformat(lease['released_utc']).astimezone(timezone.utc)
        need((previous_release is None or previous_release <= started)
             and ended <= external_start <= external_end <= released <= approved_time <= now,
             'serialized batches and aggregate admission only after every full release required')
        previous_release = released
        need(lease['validation_passed'] is True and lease['full_compute_custody_released'] is True
             and all(type(lease[name]) is int for name in ('guard_attempts_consumed', 'jobs_created', 'jobs_executed'))
             and lease['guard_attempts_consumed'] == lease['jobs_created'] == lease['jobs_executed'] == 1
             and lease['external_closeout_sha256'] == current['closeout']['sha256']
             and lease['external_supervision_sha256'] == current['external_supervision']['sha256']
             and lease['external_exit_code'] == 0 and lease['external_owned_tree_reaped'] is True
             and lease['external_stdout_eof'] is True and lease['external_stderr_eof'] is True
             and datetime.fromisoformat(supervision['started_utc']).astimezone(timezone.utc) >= ended
             and datetime.fromisoformat(lease['released_utc']).astimezone(timezone.utc)
                 >= datetime.fromisoformat(supervision['ended_utc']).astimezone(timezone.utc)
             and datetime.fromisoformat(lease['released_utc']).astimezone(timezone.utc)
                 <= datetime.fromisoformat(peer_record['window_end_utc']).astimezone(timezone.utc),
             'all three explicit full custody releases required')
        archive = ROOT / f'evidence/cho51-canonical-boundary-20261025-v5_{batch}'
        manifest = parse(proof(current['archive_manifest'], archive / 'manifest.json'))
        need(closed['archive_manifest_sha256'] == current['archive_manifest']['sha256']
             and manifest['schema'] == 'cho51_canonical_boundary_archive_v1' and len(manifest['artifacts']) <= 64,
             'accepted exact per-batch archive manifest required')
        expected_inventory = {'.gitattributes', 'manifest.json', 'summary.json', 'README.md'}
        run_controls = ('pins.json', 'source-review.json', 'owner-resource-amendment.json', 'admission.json',
                        'dispatch_001.json', 'dispatch-result_001.json', 'guard-attempt_001.json',
                        'preflight_001.json', 'compute-request_001.json')
        native_controls = ('admission.json', 'command-result.json', 'command.log', 'deadline.json', 'receipt.json')
        expected_sources = {str(ROOT / relative) for relative in source_relatives()}
        expected_sources.update(str(run / name) for name in run_controls)
        expected_sources.update(str(native / name) for name in native_controls)
        expected_sources.update((str(run / 't1/result.json'), str(run / 't1/junit.xml'),
                                 current['peer_grant']['path'], str(PLAN), str(SCOPE_DOCUMENT)))
        need(len(expected_sources) == len(manifest['artifacts']) == 41, 'exact producer41-source archive required')
        payload_bytes = 0
        bindings = {}
        retained_controls = {}
        for artifact in manifest['artifacts']:
            relative = artifact['path']
            need(type(relative) is str and re.fullmatch(r'artifacts/a\d{4}\.(py|ps1|json|md|xml|log)', relative) is not None
                 and relative not in expected_inventory and type(artifact['bytes']) is int and 0 <= artifact['bytes'] <= 8 * 1024**2,
                 'bounded direct archive artifact required')
            expected_inventory.add(relative)
            need(artifact['source'] not in bindings, 'unique archive original sources required')
            bindings[artifact['source']] = artifact['sha256']
            raw = checked(archive / relative, artifact['sha256'])
            need(len(raw) == artifact['bytes'], 'archive artifact size changed')
            payload_bytes += len(raw)
            if artifact['source'] in {str(run / name) for name in run_controls} | {str(native / 'command-result.json')}:
                retained_controls[artifact['source']] = raw
        need(set(bindings) == expected_sources, 'archive source inventory differs from the exact producer')
        need(all(bindings[str(ROOT / relative)] == digest for relative, digest in common_sources.items())
             and bindings[str(PLAN)] == PLAN_SHA and bindings[str(SCOPE_DOCUMENT)] == DOCUMENT_SHA
             and bindings[str(run / 'source-review.json')] == pins['source_review_sha256']
             and bindings[str(amendment_path)] == pins['owner_resource_amendment_sha256'],
             'archive family/plan/review/owner byte joins required')
        archived = {name: parse(retained_controls[str(run / name)]) for name in run_controls}
        dispatched = archived['dispatch_001.json']
        dispatch_result = archived['dispatch-result_001.json']
        marker = archived['guard-attempt_001.json']
        preflight = archived['preflight_001.json']
        compute_request = archived['compute-request_001.json']
        need(dispatched['schema'] == 'cho51_canonical_boundary_dispatch_v1'
             and dispatched['command'] == command and dispatched['pins_sha256'] == current['pins']['sha256']
             and dispatched['root_admission_sha256'] == current['root_admission']['sha256']
             and dispatched['peer_release_sha256'] == current['peer_grant']['sha256']
             and zero(dispatched['expected_numerical_budget']) and dispatched['scientific_admission'] is False,
             'exact archived dispatch command and authority required')
        need(dispatch_result['schema'] == 'cho51_canonical_boundary_dispatch_result_v1'
             and type(dispatch_result['exit_code']) is int and dispatch_result['exit_code'] == 0
             and dispatch_result['pins_sha256'] == current['pins']['sha256']
             and marker['schema'] == 'cho51_canonical_boundary_guard_attempt_v1'
             and type(marker['maximum_jobs']) is int and marker['maximum_jobs'] == 1
             and marker['automatic_retry_permitted'] is False
             and marker['pins_sha256'] == current['pins']['sha256']
             and marker['root_admission_sha256'] == current['root_admission']['sha256']
             and marker['dispatch_sha256'] == bindings[str(run / 'dispatch_001.json')]
             and marker['peer_release_sha256'] == current['peer_grant']['sha256']
             and admission['guard_attempt_sha256'] == bindings[str(run / 'guard-attempt_001.json')],
             'archived once-only marker/dispatch/native joins required')
        need(preflight['schema'] == 'cho51_canonical_boundary_root_preflight_v1'
             and preflight['passed'] is True and preflight['source_only'] is True and preflight['unused_attempt'] is True
             and preflight['pins_sha256'] == current['pins']['sha256']
             and preflight['source_review_sha256'] == pins['source_review_sha256']
             and preflight['peer_release_sha256'] == current['peer_grant']['sha256']
             and root_admission['preflight_sha256'] == bindings[str(run / 'preflight_001.json')]
             and header_matches(preflight, batch), 'archived fresh Root preflight required')
        need(compute_request['schema'] == 'pro3_compute_window_request_v1'
             and compute_request['scope'] == expected_phase['scope']
             and compute_request['pins_sha256'] == current['pins']['sha256']
             and compute_request['source_review_sha256'] == pins['source_review_sha256']
             and compute_request['owner_resource_amendment_sha256'] == pins['owner_resource_amendment_sha256']
             and header_matches(compute_request, batch), 'exact complementary compute request required')
        command_result = parse(retained_controls[str(native / 'command-result.json')])
        need(type(command_result['returncode']) is int and command_result['returncode'] == 0,
             'archived native command result must be zero')
        need(datetime.fromisoformat(compute_request['requested_utc']).astimezone(timezone.utc)
                 <= datetime.fromisoformat(preflight['observed_utc']).astimezone(timezone.utc)
                 <= datetime.fromisoformat(root_admission['observed_utc']).astimezone(timezone.utc)
                 <= datetime.fromisoformat(dispatched['observed_utc']).astimezone(timezone.utc)
                 <= datetime.fromisoformat(marker['observed_utc']).astimezone(timezone.utc) <= started
             and ended <= datetime.fromisoformat(dispatch_result['completed_utc']).astimezone(timezone.utc) <= external_start,
             'archived once-only custody ordering required')
        need(payload_bytes == closed['archive_payload_bytes'] <= 32 * 1024**2
             and len(manifest['artifacts']) == closed['archive_artifacts'], 'archive payload/count agreement required')
        for name in ('pins', 'result', 'junit', 'native_receipt', 'native_admission', 'native_deadline', 'root_admission', 'peer_grant'):
            need(bindings.get(current[name]['path']) == current[name]['sha256'], 'archive original/proof hash join differs')
        need(parse(checked(archive / 'summary.json', current['closeout']['sha256'])) == closed,
             'archive and external closeout summaries differ')
        checked(archive / 'README.md', closed['archive_readme_sha256'])
        actual_inventory = set()
        pending = [archive]
        while pending:
            directory = pending.pop()
            direct(directory)
            for child in directory.iterdir():
                direct(child)
                if child.is_dir():
                    pending.append(child)
                else:
                    actual_inventory.add(child.relative_to(archive).as_posix())
        need(actual_inventory == expected_inventory, 'exact archive inventory required')
        checked(archive / '.gitattributes', '705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da')
        accepted[batch] = dict(tests=count, controls=34, pins_sha256=current['pins']['sha256'],
            closeout_sha256=current['closeout']['sha256'], lease_sha256=current['lease']['sha256'],
            archive_manifest_sha256=current['archive_manifest']['sha256'])
    need(len(selected_union) == 133 and selected_union == set(common_full), 'complete pairwise-disjoint133 union required')
    need(datetime.now(timezone.utc) < deadline and not any(path.exists() for path in PAUSES), 'aggregate deadline or pause before result')
    result = dict(schema='cho51_canonical_boundary_aggregate_result_v1', passed=True,
        status='metadata_validation_complementary_coverage_only', observed_utc=datetime.now(timezone.utc).isoformat(),
        batch_plan_sha256=PLAN_SHA, proofs_sha256=arguments.expect_proofs, full_collection=common_full,
        tests=133, batches=accepted, distinct_stdlib_controls=34, stdlib_control_instances=102,
        current_numerical_ledger=dict(ZERO), execution_admitted=False, measured_publication_allowed=False,
        raw_input_verification_performed=False, weight_verification_performed=False,
        unchanged_canonical_worker_qualified=False, unchanged_canonical_parent_qualified=False,
        single_root_factory_qualified=False, runtime_for_future_execution_qualified=False,
        current_runtime_physical_reverification_performed=False,
        scientific_admission=False, experiment_freeze_signed=False,
        external_aggregate_supervision_status='pending_independent_supervision_and_custody_closeout',
        metadata_proof_reads=reads, metadata_proof_bytes=total_bytes)
    direct(RUN / 'result.json', existing=False)
    raw = canonical(result)
    need(len(raw) <= 1024**2, 'bounded aggregate output required')
    with (RUN / 'result.json').open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(dict(passed=True, tests=133, batches=3, controls_per_batch=34, scientific_admission=False)), flush=True)


if __name__ == '__main__':
    main()
