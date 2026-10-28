"""Independent standard-library metadata unit closeout; never imports the candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata_common as control

README_BYTES = (b'# P3 metadata/profile and telemetry contract evidence\n\nFresh nonnumerical tests with genuine canonical types and historical synthetic input claims, not fresh physical signal verification. '
    b'No restoration, numerical episode, raw/weight verification, claim, measured publication, recovery or scientific admission. '
    b'Canonical parent/worker/single-root restoration and future runtime remain unqualified. '
    b'One freshly admitted complete nonnumerical metadata/profile and telemetry-contract test suite. '
    b'Independent external stdlib closeout; archived grants/launchers are consumed and inert.\n')


def verify_reports(collected, reports, expected_tests):
    control.need(len(collected) == len(set(collected)) == expected_tests, 'exact unique test inventory required')
    expected_phases = {(nodeid, phase) for nodeid in collected for phase in ('setup', 'call', 'teardown')}
    actual_phases = [(row['nodeid'], row['phase']) for row in reports]
    control.need(len(actual_phases) == len(set(actual_phases)) == len(expected_phases)
                 and set(actual_phases) == expected_phases and all(row['outcome'] == 'passed' for row in reports),
                 'exact unique complete three-phase reports must pass')


def verify_junit(raw, collected, expected_tests):
    junit = ET.fromstring(raw)
    suites = list(junit.iter('testsuite'))
    control.need(len(suites) == 1 and int(suites[0].get('tests', '-1')) == expected_tests
                 and all(int(suite.get(name, '0')) == 0 for suite in suites for name in ('failures', 'errors', 'skipped')),
                 'JUnit failure/error/skip counts must be zero')
    nodes = list(junit.iter('testcase'))
    expected = set()
    for nodeid in collected:
        module, name = nodeid.split('::', 1)
        control.need(module in {'docs/phase2/cho51_p3_adapter_v1/test_mapping.py',
                               'docs/phase2/cho51_p3_adapter_v1/test_telemetry.py'}, 'unreviewed test module')
        expected.add((module[:-3].replace('/', '.'), name))
    observed = [(node.get('classname'), node.get('name')) for node in nodes]
    control.need(len(collected) == len(set(collected)) == len(nodes) == len(set(observed)) == expected_tests
                 and set(observed) == expected
                 and not any(list(junit.iter(tag)) for tag in ('failure', 'error', 'skipped')),
                 'exact complete physical JUnit cases must pass')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-pins', required=True)
    parser.add_argument('--expect-external-admission', required=True)
    args = parser.parse_args()
    external = control.document(control.RUN / 'closeout-admission_001.json', args.expect_external_admission)
    control.need(external['schema'] == 'cho51_p3_contracts_external_admission_v1' and external['accepted'] is True
                 and external['pins_sha256'] == args.expect_pins and external['maximum_jobs'] == 0
                 and external['maximum_interpreter_invocations'] == 1 and external['maximum_seconds'] == 300
                 and external['scientific_admission'] is False, 'fresh exact external closeout admission required')
    pins = control.pins(args.expect_pins)
    control.verify_files(pins)
    root = control.document(control.RUN / 'admission.json')
    peer_path = Path(root['peer_release_path'])
    peer = control.document(peer_path, root['peer_release_sha256'])
    expected_root = dict(schema='cho51_p3_contracts_admission_v1', accepted=True,
        pins_sha256=args.expect_pins, source_review_sha256=pins['source_review_sha256'], scope=control.SCOPE,
        maximum_jobs=1, max_job_seconds=600, process_mib=4096, job_mib=5120, startup_ram_gib=pins['startup_ram_gib'],
        active_ram_gib=4, disk_gib=20, automatic_retry_permitted=False, scientific_admission=False)
    expected_root.update(expected_metadata_tests=pins['expected_tests'],
        expected_stdlib_controls=len(control.CONTROL_NAMES), external_stdlib_closeout_maximum_seconds=300)
    expected_peer = dict(schema='pro2_pro3_compute_release_v1', released=True, scope=control.SCOPE,
        pins_sha256=args.expect_pins, maximum_jobs=1, max_job_seconds=600, process_mib=4096,
        job_mib=5120, startup_ram_gib=pins['startup_ram_gib'], active_ram_gib=4, disk_gib=20,
        owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256'], scientific_admission=False)
    expected_peer.update(expected_metadata_tests=pins['expected_tests'],
        expected_stdlib_controls=len(control.CONTROL_NAMES), external_stdlib_closeout_maximum_seconds=300)
    for record, expected in ((root, expected_root), (peer, expected_peer)):
        control.need(all(type(record.get(field)) is type(value) and record[field] == value
                     for field, value in expected.items()), 'independent exact historical Root/peer admission required')
        control.need(control.zero_budget(record['expected_numerical_budget']), 'historical exact nonnumerical zero budget required')
    control.need(all(type(root[field]) is str and root[field] == peer[field]
                 for field in ('window_start_utc', 'window_end_utc')), 'historical UTC window strings required')
    amendment = control.document(control.RUN / 'owner-resource-amendment.json', pins['owner_resource_amendment_sha256'])
    control.need(amendment['scope'] == control.SCOPE and type(amendment['startup_ram_gib']) is int
                 and amendment['startup_ram_gib'] == pins['startup_ram_gib']
                 and amendment['active_ram_gib'] == 4 and amendment['disk_gib'] == 20
                 and amendment['canonical_guard_modified'] is False and amendment['scientific_admission'] is False
                 and amendment['applies_to'] == 'metadata_profile_mapping_and_telemetry_contract_tests_only',
                 'exact current-phase owner resource authority required')
    result = control.document(control.OUTPUT / 'result.json')
    control.need(result['passed'] is True and result['pins_sha256'] == args.expect_pins
                 and result['tests'] == pins['expected_tests'] and result['pytest_exit'] == 0
                 and control.zero_budget(result['current_counter_ledger']) and result['forbidden_calls'] == {}
                 and result['unexpected_denials'] == [] and result['scientific_admission'] is False
                 and result['native_closeout_status'] == 'pending_external_post_job', 'complete metadata-only result required')
    for name in ('raw_weight_reads', 'model_constructions', 'array_decodes', 'claims', 'locks', 'selectors', 'publications', 'recovery_calls'):
        control.need(type(result[name]) is int and result[name] == 0, 'integer-zero boundary observation required')
    resource = control.ROOT / '.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif'
    control.need(type(result['runtime_import_resource_reads']) is int and 0 <= result['runtime_import_resource_reads'] <= 16
                 and type(result['runtime_resource_hash_reads_before_result']) is int
                 and 0 <= result['runtime_resource_hash_reads_before_result'] <= 16
                 and result['runtime_import_resource_path'] == str(resource)
                 and result['runtime_import_resource_sha256'] == '0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3',
                 'separately labeled bounded library-import resource required')
    control.read(resource, result['runtime_import_resource_sha256'], 260, retain=False)
    control.need(type(result['pytest_alias_refusals']) is int and 0 <= result['pytest_alias_refusals'] <= 256,
                 'separately labeled bounded pytest current-link refusals required')
    control.need(control.windows_path_matches(result['git_executable_spelling'], str(control.GIT_PATH)),
                 'genuine pinned Windows Git spelling required')
    control.need(result['full_collection'] == result['collected'] and not result['deselected'], 'complete nondeselected unit suite required')
    from collections import Counter
    control.need(dict(Counter(nodeid.split('[', 1)[0] for nodeid in result['collected'])) == pins['test_function_counts']
                 and hashlib.sha256(control.canonical(result['collected'])).hexdigest() == result['full_collection_sha256'],
                 'independent exact function multiplicities and collection digest required')
    reports = result['reports']
    verify_reports(result['collected'], reports, pins['expected_tests'])
    verify_junit(control.read(control.OUTPUT / 'junit.xml')[0], result['collected'], pins['expected_tests'])
    controls = result['stdlib_controls']
    control.need(type(controls) is dict and set(controls) == set(control.CONTROL_NAMES)
                 and all(value is True for value in controls.values())
                 and type(result['stdlib_control_count']) is int
                 and result['stdlib_control_count'] == pins['expected_stdlib_controls'] == len(control.CONTROL_NAMES),
                 'all exact current stdlib guard controls must pass')
    native = Path(result['native_directory'])
    control.need(native.parent == control.ROOT / 'runs/migration' and result['job_name'] == 'pro3_migration_' + native.name, 'exact native path required')
    admission = control.document(native / 'admission.json', result['native_admission_sha256'])
    receipt = control.document(native / 'receipt.json')
    deadline = control.document(native / 'deadline.json')
    marker = control.document(control.RUN / 'guard-attempt_001.json', admission['guard_attempt_sha256'])
    control.need(marker['schema'] == 'cho51_p3_contracts_guard_attempt_v1'
                 and marker['pins_sha256'] == args.expect_pins and type(marker['maximum_jobs']) is int
                 and marker['maximum_jobs'] == 1 and marker['automatic_retry_permitted'] is False
                 and marker['root_admission_sha256'] == admission['root_admission_sha256']
                 and marker['dispatch_sha256'] == control.read(control.RUN / 'dispatch_001.json', retain=False)[0]
                 and marker['peer_release_sha256'] == root['peer_release_sha256'], 'independent consumed guard marker required')
    command = [str(control.ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(control.RUN / 'runner.py'),
               '--pins', str(control.RUN / 'pins.json'), '--expect-pins', args.expect_pins, '--output', str(control.OUTPUT)]
    control.need(admission['command'] == command and admission['pins_sha256'] == args.expect_pins
                 and admission['root_admission_sha256'] == control.read(control.RUN / 'admission.json', retain=False)[0]
                 and admission['startup_ram_gib'] == pins['startup_ram_gib'] and admission['active_ram_gib'] == 4
                 and admission['active_disk_gib'] == 20 and admission['process_mib'] == 4096
                 and admission['job_mib'] == 5120 and admission['native_threads'] == 1
                 and admission['source_sha256'] == control.CANONICAL, 'native command/resource bindings differ')
    operations = {str(path.relative_to(control.ROOT)).replace('\\', '/'): control.read(path, retain=False)[0]
        for path in (control.ROOT / 'tools/migration').iterdir()
        if path.is_file() and path.suffix in {'.py', '.ps1', '.json', '.lock'}}
    operations['evaluation/phase2_supervision_primitives.py'] = control.FROZEN['evaluation/phase2_supervision_primitives.py']
    control.need(admission['operation_pins'] == operations, 'exact native operation inventory differs')
    for relative, expected in operations.items():
        control.need(pins['files'].get(str(control.ROOT / relative)) == expected, 'native operation not freshly pinned')
    selected_runtime = {path: value for path, value in pins['runtime_files'].items()
        if Path(path) == control.ROOT / '.venv/Scripts/python.exe' or Path(path).name in {'python3.dll', 'python312.dll'}}
    control.need(len(selected_runtime) == 3 and admission['selected_runtime_pins'] == selected_runtime,
                 'exact native selected interpreter runtime inventory differs')
    state = receipt['native_state']
    control.need(receipt['accepted'] is True and receipt['result']['reason'] == 'normal' and receipt['result']['exit_code'] == 0
                 and receipt['job_name'] == result['job_name'] and receipt['job_absent'] is True
                 and receipt['error'] is None and receipt['scientific_admission'] is False, 'accepted normal-zero native receipt required')
    for name in ('created_suspended', 'atomic_job_assignment_verified', 'limits_set', 'limits_query_verified',
                 'membership_verified', 'job_empty_before_close', 'job_closed', 'process_handle_closed', 'thread_handle_closed'):
        control.need(state[name] is True, 'complete native assignment/closure required')
    control.need(state['cleanup_errors'] == state['peak_sampling_errors'] == []
                 and state['peak_process_commit_bytes'] <= 4096 * 1024**2
                 and state['peak_job_commit_bytes'] <= 5120 * 1024**2, 'native errors or memory cap')
    for field, expected in dict(process_limit_bytes=4096 * 1024**2, aggregate_limit_bytes=5120 * 1024**2, limit_flags=8960).items():
        control.need(type(state[field]) is int and state[field] == expected, 'actual queried native limit differs')
    start = datetime.fromisoformat(admission['started_utc']).astimezone(timezone.utc)
    end = datetime.fromisoformat(receipt['completed_utc']).astimezone(timezone.utc)
    attempt = datetime.fromisoformat(deadline['attempt_deadline_utc']).astimezone(timezone.utc)
    session = datetime.fromisoformat(deadline['session_deadline_utc']).astimezone(timezone.utc)
    control.need((attempt-start).total_seconds() == 600 and (session-attempt).total_seconds() == 5
                 and end <= attempt and start >= datetime.fromisoformat(peer['window_start_utc']).astimezone(timezone.utc)
                 and session <= datetime.fromisoformat(peer['window_end_utc']).astimezone(timezone.utc)
                 and end <= datetime.fromisoformat(peer['window_end_utc']).astimezone(timezone.utc), 'exact deadline or peer historical window differs')
    dispatch = control.document(control.RUN / 'dispatch_001.json')
    dispatched = control.document(control.RUN / 'dispatch-result_001.json')
    control.need(dispatch['command'] == command and dispatch['pins_sha256'] == args.expect_pins
                 and dispatched['pins_sha256'] == args.expect_pins and type(dispatched['exit_code']) is int
                 and dispatched['exit_code'] == 0, 'exact dispatch/result required')
    control.need(datetime.fromisoformat(root['observed_utc']).astimezone(timezone.utc)
                 <= datetime.fromisoformat(dispatch['observed_utc']).astimezone(timezone.utc)
                 <= datetime.fromisoformat(marker['observed_utc']).astimezone(timezone.utc) <= start
                 and end <= datetime.fromisoformat(dispatched['completed_utc']).astimezone(timezone.utc)
                 <= datetime.fromisoformat(peer['window_end_utc']).astimezone(timezone.utc), 'historical custody ordering differs')
    for sample in admission['startup_samples']:
        control.need(sample['available_ram_bytes'] >= pins['startup_ram_gib'] * 1024**3 and sample['free_disk_bytes'] >= 20 * 1024**3, 'startup floor differs')
    control.need(len(admission['startup_samples']) == 2, 'two startup samples required')
    for name, expected in result['loaded_module_hashes'].items():
        control.need(pins['files'].get(name) == expected, 'loaded module not externally pinned')
        control.read(Path(name), expected, 2 * 1024**3, retain=False)
    control.need(len(result['loaded_module_hashes']) == result['loaded_module_files'], 'loaded inventory count')
    control.job_absent(result['job_name'])
    control.pause_check()
    archive = control.ROOT / 'evidence/cho51-p3-contracts-20261027-v1'
    control.need(not archive.exists(), 'fresh unused metadata evidence archive required')
    sources = {control.ROOT / relative for relative in pins['reviewed_files']}
    sources.update(control.RUN / name for name in ('pins.json', 'source-review.json', 'owner-resource-amendment.json',
        'admission.json', 'dispatch_001.json', 'dispatch-result_001.json', 'guard-attempt_001.json', 'preflight_001.json', 'compute-request_001.json', 'pin-review.json', 'closeout-admission_001.json',
        'coordination-source-observation_001.json'))
    sources.update((control.OUTPUT / 'result.json', control.OUTPUT / 'junit.xml', peer_path))
    coordination = control.document(control.RUN / 'coordination-source-observation_001.json')
    for name in ('source_scope', 'source_adoption'):
        reference = coordination[name]
        control.read(Path(reference['path']), reference['sha256'])
        sources.add(Path(reference['path']))
    for relative in (
        'evidence/cho51-adoption-route-20261013/owner/adoption.json',
        'evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json',
        'evidence/phase2-readiness-20261012/worker/roster.json',
        'runs/coordination/cho51_provenance_numerical_worker_20261025_v7/origin-contract.json',
        'runs/coordination/cho51_provenance_numerical_worker_20261025_v7/final-review.json',
        'runs/coordination/cho51_provenance_restore_20261025_v2/final-review.json',
        'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture/synthetic-input-identity.json',
        'runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json',
        'docs/phase2/cho51_p3_adapter_design_20261027.md',
        'docs/phase2/cho51_p3_telemetry_design_20261027.md',
        'docs/phase2/cho51_p3_adapter_review_20261027.md',
        'docs/phase2/cho51_p3_contracts_implementation_20261027.md',
    ):
        sources.add(control.ROOT / relative)
    sources.update(path for path in native.iterdir() if path.is_file())
    control.need(len(sources) <= 64, 'bounded metadata-only archive required')
    rows, payloads, total = [], [], 0
    for index, path in enumerate(sorted(sources), 1):
        raw = control.read(path)[0]
        total += len(raw)
        control.need(total <= 32 * 1024**2 and path.suffix in {'.py', '.ps1', '.json', '.md', '.xml', '.log'}, 'metadata-only bounded archive required')
        relative = f'artifacts/a{index:04d}{path.suffix}'
        rows.append(dict(source=str(path), path=relative, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        payloads.append((relative, raw))
    archive.mkdir()
    (archive / 'artifacts').mkdir()
    with (archive / '.gitattributes').open('xb') as stream:
        stream.write(b'* -text\n')
    for relative, raw in payloads:
        with (archive / relative).open('xb') as stream:
            stream.write(raw)
            stream.flush()
    manifest_sha = control.write(archive / 'manifest.json', dict(schema='cho51_p3_contracts_archive_v1', artifacts=rows))
    summary = dict(schema='cho51_p3_contracts_closeout_v1', passed=True, closed_utc=datetime.now(timezone.utc).isoformat(),
        pins_sha256=args.expect_pins, source_review_sha256=pins['source_review_sha256'], tests=pins['expected_tests'],
        current_counter_ledger=dict(control.ZERO), native_directory=str(native), job_name=result['job_name'],
        native_receipt_sha256=control.read(native / 'receipt.json', retain=False)[0], normal_exit=0,
        native_elapsed_seconds=(end-start).total_seconds(), external_native_verified=True, child_flag_remains_pending=True,
        startup_ram_gib=pins['startup_ram_gib'], active_ram_gib=4, disk_gib=20, owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256'],
        archive_artifacts=len(rows), archive_payload_bytes=total, archive_manifest_sha256=manifest_sha,
        stdlib_guard_controls=len(control.CONTROL_NAMES), archive_readme_sha256=hashlib.sha256(README_BYTES).hexdigest(),
        loaded_module_files=result['loaded_module_files'], canonical_sources=432, source_sha256=control.CANONICAL,
        runtime_import_resource_reads=result['runtime_import_resource_reads'],
        runtime_resource_hash_reads_before_result=result['runtime_resource_hash_reads_before_result'],
        pytest_alias_refusals=result['pytest_alias_refusals'],
        pytest_aliases_created=0, git_executable_spelling=result['git_executable_spelling'],
        raw_inputs_verified=False, weights_verified=False, runtime_for_future_execution_qualified=False,
        unchanged_canonical_worker_qualified=False, unchanged_canonical_parent_qualified=False, single_root_factory_qualified=False,
        measured_cells=0, scientific_admission=False, experiment_freeze_signed=False)

    summary.update(full_collection_sha256=result['full_collection_sha256'],
                   full_suite_executed=True, deselected_tests=0)
    control.write(archive / 'summary.json', summary)
    with (archive / 'README.md').open('xb') as stream:
        stream.write(README_BYTES)
    for row in rows:
        control.read(Path(row['source']), row['sha256'])
        control.read(archive / row['path'], row['sha256'])
    expected_inventory = {row['path'] for row in rows} | {'.gitattributes', 'manifest.json', 'summary.json', 'README.md'}
    control.need({path.relative_to(archive).as_posix() for path in archive.rglob('*') if path.is_file()} == expected_inventory,
                 'exact metadata archive inventory required')
    control.read(archive / '.gitattributes', '705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da')
    control.need(control.document(archive / 'manifest.json', manifest_sha) == dict(schema='cho51_p3_contracts_archive_v1', artifacts=rows)
                 and control.document(archive / 'summary.json') == summary, 'generated archive manifest/summary binding differs')
    readme = control.read(archive / 'README.md')[0]
    control.need(readme == README_BYTES and hashlib.sha256(readme).hexdigest() == summary['archive_readme_sha256'],
                 'exact bounded engineering-only archive explanation required')
    control.verify_files(pins)
    control.job_absent(result['job_name'])
    control.write(control.RUN / 'closeout-result.json', summary)
    print(json.dumps(dict(passed=True, tests=pins['expected_tests'], artifacts=len(rows), archive=str(archive),
                          scientific_admission=False)), flush=True)


if __name__ == '__main__':
    main()
