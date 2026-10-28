"""Authenticate immutable accepted history without executing used launchers."""
from __future__ import annotations

import hashlib
import ctypes
import importlib.util
import json
import os
import stat
import sys
from datetime import datetime, timezone
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


def preserve_v5_history(include):
    previous = ROOT / 'runs/coordination/cho51_provenance_numerical_worker_20261025_v5'
    pins_sha = 'bc7da9b7694202c42b0090d2e819ce302f638466d9ed9e1bcc1a79d71be59223'
    pins = document(previous / 'pins.json', pins_sha)
    include(previous / 'pins.json', pins_sha)
    need(len(pins['reviewed_files']) == 13 and pins['expected_tests'] == 63,
         'exact frozen v5 thirteen-source metadata validation inventory required')
    for name, expected in pins['reviewed_files'].items():
        include(ROOT / name, expected)
    controls = (
        ('closeout-tests-result.json', 'de5e1bb8c1704bc4c200d68208066ac25ec2d1263a10a5560ef928c4f6ae64bf'),
        ('tests-final-review.json', '43709f479724cfce9f88b257bc720450fdc1d6e94eb1bb2bdba94eb04b3dad8a'),
        ('lease-closeout_tests_001.json', '7e83878e995087c91ca398058e1a7be758c42a2f55b8c588a2491412ec57eefe'))
    values = {}
    for name, expected in controls:
        values[name] = document(previous / name, expected)
        include(previous / name, expected)
    unit, review, lease = (values[name] for name, _ in controls)
    exact_fields(unit, dict(schema='cho51_provenance_numerical_worker_tests_closeout_v1', phase='tests', passed=True,
        tests=63, pins_sha256=pins_sha, current_counter_ledger=ZERO_BUDGET, backend_calls=0, verifier_calls=0,
        scientific_admission=False, native_closeout_status='verified_external_post_job'), 'accepted v5 unit-only closeout differs')
    exact_fields(review, dict(schema='cho51_provenance_numerical_worker_tests_final_review_v1', passed=True,
        tests=63, pins_sha256=pins_sha, remaining_actionable_findings=[], tests_custody_released=True,
        tests_closeout_sha256=controls[0][1], lease_closeout_sha256=controls[2][1], scientific_admission=False),
        'accepted v5 unit-only independent review differs')
    exact_fields(lease, dict(schema='cho51_provenance_numerical_worker_lease_closeout_v1', phase='tests', accepted=True,
        closed=True, custody_released=True, outstanding_owned_children=0, guard_and_launcher_reaped=True,
        external_closeout_reaped=True, full_compute_custody_explicitly_released=True,
        pins_sha256=pins_sha, integration_admitted=False, scientific_admission=False), 'accepted v5 unit custody differs')
    archive = ROOT / 'evidence/cho51-provenance-numerical-worker-tests-20261025-v5'
    manifest_sha = '66a17996011f88221b04c447f1cc36b5012f338a9b46658ae43852dab135b4f2'
    manifest = document(archive / 'manifest.json', manifest_sha)
    include(archive / 'manifest.json', manifest_sha)
    need(unit['archive_manifest_sha256'] == manifest_sha and len(manifest['artifacts']) == 32
         and sum(row['bytes'] for row in manifest['artifacts']) == 2402241, 'exact accepted v5 unit archive required')
    inventory = {'.gitattributes', 'README.md', 'manifest.json', 'summary.json'}
    for row in manifest['artifacts']:
        source, copied = ROOT / row['source'], archive / row['path']
        need(source.resolve(strict=True).is_relative_to(ROOT) and copied.resolve(strict=True).is_relative_to(archive)
             and row['path'] not in inventory and type(row['bytes']) is int and 0 <= row['bytes'] <= 8 * 1024**2,
             'bounded direct accepted v5 unit archive pair required')
        include(source, row['sha256'], row['bytes'])
        include(copied, row['sha256'], row['bytes'])
        inventory.add(row['path'])
    include(archive / 'summary.json', controls[0][1])
    include(archive / 'README.md', '02d5de08e98ec201ce3231c0da5e72658aa81427c600734fe86831d4ca04cf32')
    include(archive / '.gitattributes', '705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da')
    need({path.relative_to(archive).as_posix() for path in archive.rglob('*') if path.is_file()} == inventory,
         'exact accepted v5 unit archive inventory differs')
    result = document(previous / 't1/result.json', unit['tests_result_sha256'])
    qualification = document(previous / 't1/qualification.json', unit['tests_qualification_sha256'])
    zero_observer = dict.fromkeys(OBSERVER_COUNTS, 0) | {'numerical_calls': {}}
    exact_fields(result, dict(phase='tests', passed=True, tests_passed=True, collected_tests=63, expected_tests=63,
        backend_calls=0, verifier_calls=0, current_counter_ledger=ZERO_BUDGET, independent_observer=zero_observer,
        scientific_admission=False), 'v5 accepted metadata tests cannot be relabelled as numerical work')
    need(qualification['result'] == result and qualification['independent_observer'] == unit['independent_observer'] == zero_observer
         and not (previous / 't1/fixture').exists() and not (previous / 't1/cases').exists(),
         'accepted v5 unit observer and production absence differ')
    native = unit['native']
    exact_fields(native, dict(accepted=True, closed_empty_handles_closed_freshly_absent=True,
        native_directory=str(ROOT / 'runs/migration/20261025T102744Z_96d3f1f247'),
        job_name='pro3_migration_20261025T102744Z_96d3f1f247',
        receipt_sha256='b4492d48e27be5d1f390e28250569cb83c78586893a7b02cc31e79fbf83dc1c2'),
        'exact accepted v5 unit native proof differs')
    receipt = document(Path(native['native_directory']) / 'receipt.json', native['receipt_sha256'])
    exact_fields(receipt, dict(accepted=True, job_absent=True, scientific_admission=False, error=None),
                 'accepted v5 unit native receipt differs')
    exact_fields(receipt['result'], dict(reason='normal', exit_code=0), 'accepted v5 unit normal exit required')
    audits = (
        ('failed-attempt-native-audit_integration_001.json', 'e92080155a3025ee494821c0c85305f5f72e753318a6a6e2771e95c699919808'),
        ('failed-attempt-native-audit_integration_002.json', 'dce47e9e9a2334489fab9830befd306e10e69d4718d8a058c72f7de19ebcfd41'))
    failed = []
    for name, expected in audits:
        record = document(previous / name, expected)
        include(previous / name, expected)
        for path, row in record['exact_bindings'].items():
            include(path, row['sha256'], row['bytes'])
        failed.append(record)
    exact_fields(failed[0], dict(result_accepted=False, failure_preserved=True, phase='integration', reason='attempt_deadline',
        actual_current_counter_ledger=None, counter_status='incomplete_unknown_after_backend_entry',
        production_numerical_work_reached=True, job_empty_closed_handles_closed=True, fresh_absence_error=2,
        integration_result_exists=False, integration_qualification_exists=False, scientific_admission=False),
        'v5 deadline failure must remain failed with incomplete unknown counters')
    exact_fields(failed[1], dict(prior_audit_sha256=audits[0][1], native_job_accepted=False,
        physical_engineering_intent_present=True, physical_engineering_terminal_present=True,
        backend_or_recovery_replay_permitted=False, actual_current_counter_ledger=None, scientific_admission=False),
        'v5 physical terminal remains quarantined partial metadata, not accepted numerical evidence')
    failed_lease_sha = 'f5f59bef7eccd31c272fc4ffbdf7caa573402a662fbb597805b6cbc4933af870'
    failed_lease = document(previous / 'lease-closeout_integration_001.json', failed_lease_sha)
    include(previous / 'lease-closeout_integration_001.json', failed_lease_sha)
    exact_fields(failed_lease, dict(closed=True, custody_released=True, result_accepted=False, pins_sha256=pins_sha,
        native_job_name='pro3_migration_20261025T105030Z_3e3ac9171a', outstanding_owned_children=0,
        guard_and_launcher_reaped=True, full_compute_custody_explicitly_released=True,
        actual_current_counter_ledger=None, automatic_retry_permitted=False, scientific_admission=False),
        'failed v5 integration custody or unknown counter preservation differs')
    failed_receipt = document(ROOT / 'runs/migration/20261025T105030Z_3e3ac9171a/receipt.json')
    need(str(ROOT / 'runs/migration/20261025T105030Z_3e3ac9171a/receipt.json') in failed[0]['exact_bindings'],
         'actual v5 native failure receipt must be physically bound in preserved failure audit')
    exact_fields(failed_receipt, dict(accepted=False, job_absent=True, scientific_admission=False),
                 'actual v5 integration native failure must remain failed')
    exact_fields(failed_receipt['result'], dict(reason='attempt_deadline', exit_code=1), 'actual v5 deadline failure differs')
    need(not (previous / 'i1/result.json').exists() and not (previous / 'i1/qualification.json').exists()
         and not (previous / 'closeout-integration-result.json').exists(), 'failed v5 integration cannot acquire acceptance')
    return dict(accepted_unit_v5=dict(pins_sha256=pins_sha, tests=63, numerical_work=ZERO_BUDGET,
        closeout_sha256=controls[0][1], review_sha256=controls[1][1], lease_closeout_sha256=controls[2][1],
        integration_accepted=False, scientific_admission=False), preserved_failed_integration_v5=dict(
        pins_sha256=pins_sha, native_audit_sha256=audits[0][1], native_audit_supplement_sha256=audits[1][1],
        lease_closeout_sha256=failed_lease_sha, accepted=False, actual_current_counter_ledger=None,
        numerical_execution_status='incomplete_unknown', physical_engineering_terminal_present=True,
        backend_or_recovery_replay_permitted=False, measured_cells=0))


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
    failed_run = ROOT / 'runs/coordination/cho51_provenance_numerical_worker_20261025_v1'
    failed_audit_sha = 'c3145c740680fe1e1b36b3af1dee1a91efa1cc7db50b83af3fba147940e61fd9'
    failed_audit = document(failed_run / 'failed-attempt-native-audit_001.json', failed_audit_sha)
    need(failed_audit['result_accepted'] is False and failed_audit['failure_preserved'] is True
         and failed_audit['tests_executed'] == failed_audit['backend_calls'] == failed_audit['verifier_calls'] == 0
         and failed_audit['job_empty_closed_handles_closed'] is True
         and failed_audit['fresh_absence_error'] == 2 and failed_audit['scientific_admission'] is False,
         'failed integration must remain failed, inert and closed')
    include(failed_run / 'failed-attempt-native-audit_001.json', failed_audit_sha)
    for path, row in failed_audit['exact_bindings'].items():
        include(path, row['sha256'], row['bytes'])
    failed_pins = document(failed_run / 'pins.json', '45ba9bfe30762d5cde74475e53424e217e213bf2c523d7a61ced08b3930ed319')
    for name, value in failed_pins['reviewed_files'].items():
        include(ROOT / name, value)
    failed_second_run = ROOT / 'runs/coordination/cho51_provenance_numerical_worker_20261025_v2'
    failed_second_sha = 'ca1a34055c78576bddf5c2be5b5089987b04329d32ece5d8047c0b2e12c1c53c'
    failed_second = document(failed_second_run / 'failed-attempt-native-audit_001.json', failed_second_sha)
    need(failed_second['result_accepted'] is False and failed_second['failure_preserved'] is True
         and failed_second['tests_collected'] == 63 and failed_second['tests_executed'] == failed_second['tests_failed'] == 1
         and failed_second['tests_passed'] == failed_second['backend_calls'] == failed_second['verifier_calls'] == 0
         and failed_second['job_empty_closed_handles_closed'] is True
         and failed_second['fresh_absence_error'] == 2 and failed_second['scientific_admission'] is False,
         'second failed integration must remain failed, pre-numerical and closed')
    include(failed_second_run / 'failed-attempt-native-audit_001.json', failed_second_sha)
    for path, row in failed_second['exact_bindings'].items():
        include(path, row['sha256'], row['bytes'])
    second_pins = document(failed_second_run / 'pins.json', '9ffcec187273093bc8410f76e328f2e9697e56c75e31dfa3d449206afda18297')
    for name, value in second_pins['reviewed_files'].items():
        include(ROOT / name, value)
    failed_third_run = ROOT / 'runs/coordination/cho51_provenance_numerical_worker_20261025_v3'
    failed_third_sha = '0084f49e7cf40ff0eb9cab674bb17ed5bf7a9cc5a0307160ade051c85a1698a2'
    failed_third = document(failed_third_run / 'failed-attempt-native-audit_001.json', failed_third_sha)
    need(failed_third['result_accepted'] is False and failed_third['failure_preserved'] is True
         and failed_third['tests_collected'] == failed_third['tests_executed'] == failed_third['tests_passed'] == 63
         and failed_third['tests_failed'] == failed_third['verifier_calls'] == 0 and failed_third['backend_calls'] == 1
         and failed_third['current_counter_ledger'] is None and failed_third['numerical_execution_status'] == 'incomplete_unknown'
         and failed_third['independent_success_observer_available'] is False
         and failed_third['failure_site_before_first_npz_factory_restore_or_model'] is True
         and failed_third['backend_marker_consumed'] is True and failed_third['factory_marker_present'] is False
         and failed_third['engineering_terminal_present'] is False
         and failed_third['job_empty_closed_handles_closed'] is True and failed_third['fresh_absence_error'] == 2
         and failed_third['scientific_admission'] is False, 'third failed integration remains failed with unknown counters')
    include(failed_third_run / 'failed-attempt-native-audit_001.json', failed_third_sha)
    for path, row in failed_third['exact_bindings'].items():
        include(path, row['sha256'], row['bytes'])
    third_pins = document(failed_third_run / 'pins.json', 'fbac25ba87bc80ed828403693200e3c85b42b10dd6356fb1cb7ca6e110706c4e')
    for name, value in third_pins['reviewed_files'].items():
        include(ROOT / name, value)
    failed_unit_run = ROOT / 'runs/coordination/cho51_provenance_numerical_worker_20261025_v4'
    failed_unit_sha = '29b0e8a41b3acdf2c0abd8ef992c53fc5bbb56332928f64c0a3fc899dcc4b393'
    failed_unit = document(failed_unit_run / 'failed-attempt-native-audit_tests_001.json', failed_unit_sha)
    need(failed_unit['result_accepted'] is False and failed_unit['failure_preserved'] is True
         and failed_unit['phase'] == 'tests' and failed_unit['tests_collected'] == 63
         and failed_unit['tests_failed'] == failed_unit['tests_executed'] == 1
         and failed_unit['backend_calls'] == failed_unit['verifier_calls'] == 0
         and failed_unit['original_fixture_source_capture_passed'] is True
         and failed_unit['production_numerical_work_reached'] is False
         and failed_unit['job_empty_closed_handles_closed'] is True and failed_unit['fresh_absence_error'] == 2,
         'failed long-path metadata attempt must remain failed, non-numerical and closed')
    include(failed_unit_run / 'failed-attempt-native-audit_tests_001.json', failed_unit_sha)
    for path, row in failed_unit['exact_bindings'].items():
        include(path, row['sha256'], row['bytes'])
    unit_pins = document(failed_unit_run / 'pins.json', 'df596855933c74864f92b087d65e43d59546f059c42daf094ee73ddf65ca54e8')
    for name, value in unit_pins['reviewed_files'].items():
        include(ROOT / name, value)
    v5_history = preserve_v5_history(include)
    summary = dict(base['summary'], **v5_history, preserved_failed_metadata_v4={
        'pins_sha256': 'df596855933c74864f92b087d65e43d59546f059c42daf094ee73ddf65ca54e8',
        'native_audit_sha256': failed_unit_sha, 'accepted': False, 'tests_collected': 63, 'tests_failed': 1,
        'backend_calls': 0, 'original_fixture_source_capture_passed': True,
        'production_numerical_work_reached': False, 'grant006_consumed_closed': True,
        'replay_permitted': False}, preserved_failed_integration_v3={
        'pins_sha256': 'fbac25ba87bc80ed828403693200e3c85b42b10dd6356fb1cb7ca6e110706c4e',
        'native_audit_sha256': failed_third_sha, 'accepted': False, 'tests_passed': 63,
        'backend_calls': 1, 'verifier_calls': 0, 'current_counter_ledger': None,
        'numerical_execution_status': 'incomplete_unknown', 'measured_cells': 0,
        'grant005_consumed_closed': True, 'replay_permitted': False}, preserved_failed_integration_v2={
        'pins_sha256': '9ffcec187273093bc8410f76e328f2e9697e56c75e31dfa3d449206afda18297',
        'native_audit_sha256': failed_second_sha, 'accepted': False, 'tests_collected': 63,
        'tests_failed': 1, 'backend_calls': 0, 'numerical_execution_status': 'not_started',
        'measured_cells': 0, 'grant004_consumed_closed': True, 'replay_permitted': False}, preserved_failed_integration={
        'pins_sha256': '45ba9bfe30762d5cde74475e53424e217e213bf2c523d7a61ced08b3930ed319',
        'native_audit_sha256': failed_audit_sha, 'accepted': False, 'tests_executed': 0,
        'backend_calls': 0, 'numerical_execution_status': 'not_started', 'measured_cells': 0,
        'grant003_consumed_closed': True, 'replay_permitted': False}, accepted_factory={
        'final_review_sha256': PREVIOUS_FINAL_SHA, 'pins_sha256': PREVIOUS_PINS_SHA,
        'tests': 65, 'restore_count': 1, 'support_updates': 0, 'query_invocations': 0,
        'source_updates': 0, 'measured_cells': 0, 'archive_artifacts': 44,
        'closeout_export_artifacts': 45, 'historical_document_snapshots': 7,
        'runtime_transitions_from_17_october': 21},
        native_names=[*base['summary']['native_names'], '20261025T073014Z_e44f1ff4e4', '20261025T085042Z_fbd27f761e', '20261025T090357Z_55109ccb5d', '20261025T092353Z_9a8f323399', '20261025T101329Z_8403e0175f', '20261025T102744Z_96d3f1f247', '20261025T105030Z_3e3ac9171a'])
    return {'files': dict(sorted(files.items())), 'roles': dict(sorted(roles.items())), 'summary': summary}




PHASES = ('tests', 'integration')
BASE_SCOPE = 'cho51_provenance_numerical_worker_20261025_v6'
FULL_BUDGET = dict(source_updates=0, restore_count=1, support_updates=1, gradient_updates=1,
                   target_inference_calls=1, query_count=2, model_constructions=1, measured_cells=0)
ZERO_BUDGET = dict.fromkeys(FULL_BUDGET, 0)
OBSERVER_COUNTS = dict(model_constructions=1, constructor_dummy_forward_calls=1, classifier_forward_calls=2,
                      backbone_forward_calls=2, profile_a_loads=4, profile_b_loads=2, npz_loads=6,
                      clone_reinitializations=4, empty_mask_containers=2, factory_restore_calls=1, factory_restore_returns=1)
CODE_CLASSIFICATION_POLICY = dict(schema='cho51_pinned_code_classification_policy_v1', actual_code_objects=True,
    exact_pinned_absolute_filenames=True, current_physical_identity_each_hit=True,
    direct_non_reparse_ancestors_each_hit=True, content_hashes_cached=False,
    authorization_decisions_cached=False, physical_hash_checks_unchanged=True)
CODE_CLASSIFICATION_CASES = ('canonical_hit_rechecks_identity', 'foreign_code_is_not_authorized',
    'relative_and_alias_are_not_authorized', 'non_code_object_refused', 'duplicate_canonical_path_refused',
    'same_bytes_replacement_refused', 'growing_file_refused', 'multiple_links_refused', 'file_reparse_refused',
    'ancestor_reparse_refused', 'ancestor_symlink_refused')


def phase_from_output(output):
    for phase in PHASES:
        if Path(output) == RUN / ({'tests': 't1', 'integration': 'i1'}[phase]):
            return phase
    raise ValueError('only the two exact once-only phase outputs are admitted')


def phase_paths(phase):
    need(phase in PHASES, 'exact tests or integration phase required')
    return dict(output=RUN / ({'tests': 't1', 'integration': 'i1'}[phase]),
                admission=RUN / ('admission_' + phase + '.json'),
                dispatch=RUN / ('dispatch_' + phase + '_001.json'),
                dispatched=RUN / ('dispatch_result_' + phase + '_001.json'),
                closeout=RUN / ('closeout-' + phase + '-result.json'),
                scope=BASE_SCOPE + '_' + phase)


def exact_fields(value, expected, label):
    need(type(value) is dict and all(type(value.get(name)) is type(item) and canonical(value[name]) == canonical(item)
         for name, item in expected.items()), label)


def verify_tests_join(admission, pins, pins_sha256):
    specifications = (
        ('accepted_tests_closeout', RUN / 'closeout-tests-result.json'),
        ('accepted_tests_review', RUN / 'tests-final-review.json'),
        ('accepted_tests_lease_closeout', RUN / 'lease-closeout_tests_001.json'))
    values, bindings = {}, {}
    for prefix, expected_path in specifications:
        need(admission.get(prefix + '_path') == str(expected_path), 'fixed accepted tests join path required')
        expected_sha = admission.get(prefix + '_sha256')
        need(type(expected_sha) is str and len(expected_sha) == 64, 'external accepted tests SHA required')
        values[prefix] = document(expected_path, expected_sha)
        bindings[str(expected_path)] = expected_sha
    summary, review, lease = (values[prefix] for prefix, _ in specifications)
    exact_fields(summary, dict(schema='cho51_provenance_numerical_worker_tests_closeout_v1', phase='tests', passed=True,
        pins_sha256=pins_sha256, source_review_sha256=pins['source_review_sha256'], tests=63,
        current_counter_ledger=ZERO_BUDGET, scientific_admission=False,
        native_closeout_status='verified_external_post_job'), 'accepted exact unit closeout required')
    exact_fields(review, dict(schema='cho51_provenance_numerical_worker_tests_final_review_v1', passed=True,
        remaining_actionable_findings=[], pins_sha256=pins_sha256, source_review_sha256=pins['source_review_sha256'],
        tests=63, tests_closeout_path=str(RUN / 'closeout-tests-result.json'),
        tests_closeout_sha256=admission['accepted_tests_closeout_sha256'],
        lease_closeout_path=str(RUN / 'lease-closeout_tests_001.json'),
        lease_closeout_sha256=admission['accepted_tests_lease_closeout_sha256'],
        tests_custody_released=True, scientific_admission=False), 'independent exact unit final review required')
    native = summary['native']
    exact_fields(native, dict(accepted=True, closed_empty_handles_closed_freshly_absent=True),
                 'unit native closure must be accepted')
    exact_fields(review, dict(tests_native_directory=native['native_directory'], tests_native_job_name=native['job_name'],
        tests_native_receipt_sha256=native['receipt_sha256']), 'review must bind actual unit native proof')
    exact_fields(lease, dict(schema='cho51_provenance_numerical_worker_lease_closeout_v1', phase='tests',
        pins_sha256=pins_sha256, closed=True, custody_released=True, native_job_name=native['job_name'],
        outstanding_owned_children=0, guard_and_launcher_reaped=True, external_closeout_reaped=True,
        full_compute_custody_explicitly_released=True, scientific_admission=False), 'unit compute custody must be released')
    output = RUN / 't1'
    need(not (output / 'fixture').exists() and not (output / 'cases').exists(), 'unit phase must remain free of production workspaces')
    result = document(output / 'result.json', summary['tests_result_sha256'])
    qualification = document(output / 'qualification.json', summary['tests_qualification_sha256'])
    exact_fields(result, dict(phase='tests', passed=True, tests_passed=True, collected_tests=63, expected_tests=63,
        backend_calls=0, verifier_calls=0, current_counter_ledger=ZERO_BUDGET, scientific_admission=False),
        'accepted tests result differs')
    zero_observer = dict.fromkeys(OBSERVER_COUNTS, 0) | {'numerical_calls': {}}
    exact_fields(qualification['independent_observer'], zero_observer, 'unit observer must remain entirely zero')
    exact_fields(result['independent_observer'], zero_observer, 'unit result observer must remain entirely zero')
    exact_fields(summary['independent_observer'], zero_observer, 'unit closeout observer must remain entirely zero')
    need(all(canonical(value) == canonical(zero_observer) for value in
             (qualification['independent_observer'], result['independent_observer'], summary['independent_observer'])),
         'unit observers must have exactly the all-zero counter taxonomy')
    need(qualification['result'] == result and qualification['pins_sha256'] == pins_sha256,
         'unit qualification must bind its exact result and pins')
    for group in ('runtime', 'runtime_modules', 'supporting_runtime_sources'):
        need(summary[group] == pins[group], 'accepted unit and integration runtime inventories differ')
    need(summary['reviewed_files'] == pins['reviewed_files'], 'accepted unit and integration source maps differ')
    native_path = Path(native['native_directory'])
    need(native_path.resolve(strict=True) == native_path and native_path.parent == ROOT / 'runs/migration',
         'accepted unit native directory must be direct')
    unit_archive = ROOT / 'evidence/cho51-provenance-numerical-worker-tests-20261025-v6'
    unit_manifest = document(unit_archive / 'manifest.json', summary['archive_manifest_sha256'])
    rows = unit_manifest['artifacts']
    need(0 < len(rows) <= 128 and sum(row['bytes'] for row in rows) <= 64 * 1024**2,
         'bounded accepted unit archive required')
    expected_inventory = {'.gitattributes', 'README.md', 'manifest.json', 'summary.json'}
    for row in rows:
        source, copied = ROOT / row['source'], unit_archive / row['path']
        need(source.resolve(strict=True).is_relative_to(ROOT) and copied.resolve(strict=True).is_relative_to(unit_archive)
             and source.suffix.lower() not in {'.npz', '.npy', '.mat', '.safetensors', '.pt', '.pth', '.env'}
             and type(row['bytes']) is int and 0 <= row['bytes'] <= 8 * 1024**2
             and source.stat().st_size == copied.stat().st_size == row['bytes']
             and digest(source) == digest(copied) == row['sha256'], 'accepted unit archive byte pair differs')
        need(row['path'] not in expected_inventory, 'duplicate unit archive path')
        expected_inventory.add(row['path'])
        bindings[str(source)] = row['sha256']
        bindings[str(copied)] = row['sha256']
    need({path.relative_to(unit_archive).as_posix() for path in unit_archive.rglob('*') if path.is_file()} == expected_inventory
         and digest(unit_archive / '.gitattributes') == '705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da'
         and digest(unit_archive / 'summary.json') == admission['accepted_tests_closeout_sha256'],
         'exact accepted unit archive inventory, byte attributes and summary required')
    bindings[str(unit_archive / 'manifest.json')] = summary['archive_manifest_sha256']
    bindings[str(unit_archive / 'summary.json')] = admission['accepted_tests_closeout_sha256']
    for filename in ('.gitattributes', 'README.md'):
        bindings[str(unit_archive / filename)] = digest(unit_archive / filename)
    manifest_rows = {str(ROOT / row['source']): row for row in unit_manifest['artifacts']}
    need(len(manifest_rows) == len(rows), 'duplicate accepted unit source binding')

    def archived_document(path):
        path = Path(path)
        need(str(path) in manifest_rows, 'required accepted unit control proof absent from archive')
        expected = manifest_rows[str(path)]['sha256']
        bindings[str(path)] = expected
        return document(path, expected)

    for filename in ('admission.json', 'deadline.json', 'command-result.json'):
        path = native_path / filename
        need(str(path) in manifest_rows, 'accepted unit native proof absent from authenticated archive')
        row = manifest_rows[str(path)]
        need(path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'accepted unit native proof changed')
        bindings[str(path)] = row['sha256']
    unit_admission = document(native_path / 'admission.json', bindings[str(native_path / 'admission.json')])
    unit_command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'parent.py'),
                    '--pins', str(RUN / 'pins.json'), '--expect-pins', pins_sha256, '--output', str(output)]
    exact_fields(unit_admission, dict(phase='tests', command=unit_command, expected_numerical_budget=ZERO_BUDGET,
        source_sha256=CANONICAL, process_mib=4096, job_mib=5120, startup_ram_gib=4, active_ram_gib=4,
        active_disk_gib=20, native_threads=1, owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256']),
        'accepted unit native phase/source/resource binding differs')
    operations = {name: value for name, value in pins['files'].items()
                  if Path(name).parent == Path('tools/migration') and Path(name).suffix in {'.py', '.ps1', '.json', '.lock'}
                  or name == 'evaluation/phase2_supervision_primitives.py'
                  or name in pins['reviewed_files'] and Path(name).parent == RUN.relative_to(ROOT)}
    selected_runtime = {name: value for name, value in pins['runtime'].items()
                        if Path(name) == ROOT / '.venv/Scripts/python.exe' or Path(name).name in {'python312.dll', 'python3.dll'}}
    exact_fields(unit_admission, dict(schema='migration_admission_v1', operation_pins=operations,
        selected_runtime_pins=selected_runtime, guard_policy_schema='cho51_provenance_numerical_worker_guard_v1',
        previous_startup_ram_gib=10, historical_10gib_startup_pass_claimed=False,
        owner_resource_amendment_path=pins['owner_resource_amendment_path'],
        peer_pause_file='D:\\Aenv\\pro2\\WORK\\resume-20261025-001\\coordination\\PRO2_REQUEST_PRO3_PAUSE.json'),
        'accepted unit native operation/runtime/pause bindings differ')
    unit_root = archived_document(RUN / 'admission_tests.json')
    exact_fields(unit_root, dict(schema='cho51_provenance_numerical_worker_admission_v1', phase='tests', accepted=True,
        pins_sha256=pins_sha256, source_review_sha256=pins['source_review_sha256'], expected_numerical_budget=ZERO_BUDGET,
        max_job_seconds=600, process_mib=4096, job_mib=5120, startup_ram_gib=4, active_ram_gib=4, disk_gib=20,
        owner_resource_amendment_path=pins['owner_resource_amendment_path'],
        owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256'], scientific_admission=False),
        'accepted unit Root admission differs')
    portable_peer = RUN / 'peer-release-authenticated_tests.json'
    unit_peer = archived_document(portable_peer)
    need(digest(portable_peer) == unit_root['peer_release_sha256'], 'portable unit grant differs from Root admission')
    exact_fields(unit_peer, dict(schema='pro2_pro3_compute_release_v1', scope=BASE_SCOPE + '_tests', released=True,
        pins_sha256=pins_sha256, maximum_jobs=1, max_job_seconds=600, process_mib=4096, job_mib=5120,
        startup_ram_gib=4, active_ram_gib=4, disk_gib=20, scientific_admission=False,
        owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256'],
        window_start_utc=unit_root['window_start_utc'], window_end_utc=unit_root['window_end_utc']),
        'accepted unit historical peer grant differs')
    unit_controls = {}
    for path, schema in ((RUN / 'dispatch_tests_001.json', 'cho51_provenance_numerical_worker_dispatch_v1'),
                         (RUN / 'dispatch_result_tests_001.json', 'cho51_provenance_numerical_worker_dispatch_result_v1')):
        control = archived_document(path)
        unit_controls[path.name] = control
        exact_fields(control, dict(schema=schema, phase='tests', pins_sha256=pins_sha256,
            origin_contract_file_sha256=pins['origin_contract_file_sha256'], child_command=unit_command,
            expected_output=str(output), expected_numerical_budget=ZERO_BUDGET, actual_current_counter_ledger=None,
            admission_sha256=digest(RUN / 'admission_tests.json'), peer_release_path=unit_root['peer_release_path'],
            peer_release_sha256=unit_root['peer_release_sha256'], window_start_utc=unit_root['window_start_utc'],
            window_end_utc=unit_root['window_end_utc'], scientific_admission=False), 'accepted unit dispatch binding differs')
        if schema.endswith('dispatch_result_v1'):
            exact_fields(control, dict(native_directory=str(native_path), guard_exit_code=0), 'accepted unit dispatch failed')
    exact_fields(archived_document(native_path / 'command-result.json'), dict(returncode=0), 'unit child command did not pass')
    receipt = document(native_path / 'receipt.json', native['receipt_sha256'])
    exact_fields(receipt, dict(accepted=True, job_name=native['job_name'], job_absent=True,
        scientific_admission=False, error=None), 'actual accepted unit native receipt differs')
    exact_fields(receipt['result'], dict(reason='normal', exit_code=0), 'unit native must exit normally with zero')
    for flag in ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified', 'atomic_job_assignment_requested',
                 'atomic_job_assignment_verified', 'assigned', 'membership_verified', 'resumed', 'job_empty_before_close',
                 'job_closed', 'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen',
                 'attribute_cleanup_confirmed'):
        need(receipt['native_state'].get(flag) is True, 'unit native closure flag missing')
    need(receipt['native_state']['cleanup_errors'] == receipt['native_state']['peak_sampling_errors'] == [],
         'unit native cleanup or sampling error')
    state = receipt['native_state']
    exact_fields(state, dict(job_named=native['job_name'], process_limit_bytes=4096 * 1024**2,
        aggregate_limit_bytes=5120 * 1024**2), 'unit queried native limits differ')
    need(type(state['peak_samples']) is int and state['peak_samples'] > 0, 'unit native samples missing')
    for key, other, maximum in (('peak_process_commit_bytes', 'peak_process_memory_bytes', 4096 * 1024**2),
                                ('peak_job_commit_bytes', 'peak_job_memory_bytes', 5120 * 1024**2)):
        need(type(state[key]) is int and 0 < state[key] <= maximum and state[key] == receipt['result'][other],
             'unit sampled native peak differs or exceeds cap')
    samples = unit_admission['startup_samples']
    need(len(samples) == 2 and canonical(samples) == canonical(receipt['startup_samples']) and all(
        type(sample['available_ram_bytes']) is int and sample['available_ram_bytes'] >= 4 * 1024**3
        and type(sample['free_disk_bytes']) is int and sample['free_disk_bytes'] >= 20 * 1024**3 for sample in samples),
        'unit native startup resource samples differ')

    def utc(value):
        need(type(value) is str, 'unit UTC timestamp must retain string identity')
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        need(parsed.utcoffset() is not None, 'unit UTC timestamp must be timezone-aware')
        return parsed.astimezone(timezone.utc)

    started, ended, limit = map(utc, (unit_admission['started_utc'], receipt['completed_utc'], unit_admission['deadline_utc']))
    window_start, window_end = map(utc, (unit_root['window_start_utc'], unit_root['window_end_utc']))
    need((limit - started).total_seconds() == 600 and window_start <= started <= ended <= limit <= window_end,
         'accepted unit Job must fit exact historical grant and600-second deadline')
    need(window_start <= utc(unit_root['observed_utc']) <= utc(unit_controls['dispatch_tests_001.json']['observed_utc']) <= started
         and ended <= utc(unit_controls['dispatch_result_tests_001.json']['observed_utc']) <= window_end,
         'unit Root admission and dispatch timestamps must fit their historical grant')
    deadline = archived_document(native_path / 'deadline.json')
    exact_fields(deadline, dict(schema='phase2_supervision_deadlines_v1', attempt_deadline_utc=unit_admission['deadline_utc']),
                 'unit attempt deadline differs')
    need((utc(deadline['session_deadline_utc']) - limit).total_seconds() == 5, 'unit supervisor margin must be exactly5seconds')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.OpenJobObjectW.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_wchar_p]
    api.OpenJobObjectW.restype = ctypes.c_void_p
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    ctypes.set_last_error(0)
    handle = api.OpenJobObjectW(4, False, native['job_name'])
    native_error = ctypes.get_last_error()
    if handle:
        api.CloseHandle(handle)
    need(not handle and native_error == 2, 'accepted unit native Job must remain freshly absent')
    for path, expected_sha in ((output / 'result.json', summary['tests_result_sha256']),
                               (output / 'qualification.json', summary['tests_qualification_sha256']),
                               (output / 'junit.xml', summary['tests_junit_sha256']),
                               (native_path / 'receipt.json', native['receipt_sha256'])):
        need(digest(path) == expected_sha, 'accepted unit evidence changed')
        bindings[str(path)] = expected_sha
    for path, expected_sha in pins['files'].items():
        need(digest(ROOT / path) == expected_sha, 'current source/context differs from common phase pins')
    for group in ('runtime', 'runtime_modules', 'supporting_runtime_sources'):
        for path, expected_sha in pins[group].items():
            need(digest(path) == expected_sha, 'current runtime differs from accepted unit pins')
    return dict(summary=summary, review=review, lease=lease, bindings=bindings)



