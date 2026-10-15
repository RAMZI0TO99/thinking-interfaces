"""Archive compact qualified receipt/selector engineering proof, create once.

No project, numerical or test module is imported. Existing native Jobs are
queried for absence through the pinned standard-library tensor launcher.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = ROOT / 'evidence/cho51-receipt-selector-qualification-20261015'
VALIDATION = RUN / 'validation_001'
CANONICAL = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
MAXIMUM_BYTES = 8 * 1024**2
sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import io_path, source_check


def direct(path):
    if not isinstance(path, Path) or not path.is_absolute() or path.resolve(strict=True) != path:
        raise ValueError('direct absolute existing artifact required: ' + str(path))
    for candidate in (path, *path.parents):
        info = io_path(candidate).lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
            raise ValueError('linked/reparse artifact refused: ' + str(path))
    return path


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read(path, *, single_link=True, maximum=MAXIMUM_BYTES):
    direct(path)
    physical = io_path(path)
    before = physical.stat()
    if (not stat.S_ISREG(before.st_mode) or single_link and before.st_nlink != 1
            or not 0 <= before.st_size <= maximum):
        raise ValueError('bounded regular artifact required: ' + str(path))
    with physical.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(maximum + 1)
        closed = os.fstat(stream.fileno())
    after = physical.stat()
    if (len(raw) != before.st_size or any(identity(info) != identity(before) for info in (opened, closed, after))):
        raise ValueError('artifact changed during read: ' + str(path))
    return raw, (*identity(before), hashlib.sha256(raw).hexdigest())


def digest(path, *, single_link=True):
    direct(path)
    physical = io_path(path)
    before = physical.stat()
    if not stat.S_ISREG(before.st_mode) or single_link and before.st_nlink != 1:
        raise ValueError('regular pinned file required: ' + str(path))
    with physical.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        result = hashlib.file_digest(stream, 'sha256').hexdigest()
        closed = os.fstat(stream.fileno())
    if any(identity(info) != identity(before) for info in (opened, closed, physical.stat())):
        raise ValueError('pinned file changed while hashing: ' + str(path))
    return result


def decode(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON constant: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def json_file(path):
    return decode(read(path)[0])


def sha(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('plain lowercase SHA256 required')


def verify_current_inputs(pins, qualification):
    if source_check(ROOT) != CANONICAL:
        raise ValueError('canonical source changed')
    manifest = json_file(ROOT / 'tools/migration/source-files.json')
    if len(manifest['files']) != 432 or manifest['source_sha256'] != CANONICAL:
        raise ValueError('canonical source must remain exactly432 files')
    for relative, expected in pins['files'].items():
        sha(expected)
        path = ROOT / relative
        if not path.is_relative_to(ROOT) or '..' in path.parts or digest(path) != expected:
            raise ValueError('tested source/context changed: ' + relative)
    for name, expected in pins['runtime'].items():
        sha(expected)
        if digest(Path(name), single_link=False) != expected:
            raise ValueError('tested runtime changed: ' + name)
    loaded = qualification['observed_loaded_module_hashes']
    if (type(loaded) is not dict or not loaded
            or type(qualification['loaded_module_files']) is not int
            or len(loaded) != qualification['loaded_module_files']):
        raise ValueError('complete observed loaded-module hashes required')
    for name, expected in loaded.items():
        sha(expected)
        if digest(Path(name), single_link=False) != expected:
            raise ValueError('loaded module file changed: ' + name)


def write_json(path, value):
    with io_path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    pins_path, qualification_path = RUN / 'pins.json', VALIDATION / 'qualification.json'
    pins_raw, pins_identity = read(pins_path)
    pins_sha = pins_identity[-1]
    pins = decode(pins_raw)
    q_raw, q_identity = read(qualification_path)
    q = decode(q_raw)
    groups = {
        'mocked_tensor_receipt_cases': 122,
        'mocked_selector_collection_cases': 56,
        'actual_public_verifier_fabricated_record_cases': 24,
    }
    false_flags = (
        'actual_input_or_selected_study_weights_used', 'model_constructed_or_tensor_restore_performed',
        'optimizer_or_backward_performed', 'actual_1020_case_native_tensor_roster_verified',
        'actual_publication_or_selector_training_history_verified', 'real_recorder_or_original_attempt_used',
        'selection_publication_tensor_verified', 'scientific_admission', 'experiment_freeze_signed',
    )
    if (pins.get('schema') != 'cho51_receipt_selector_synthetic_fresh_pins_v1'
            or q.get('schema') != 'cho51_receipt_selector_synthetic_qualification_v1'
            or q.get('passed') is not True or type(q.get('pytest_exit')) is not int or q['pytest_exit'] != 0
            or type(q.get('collected_cases')) is not int or q['collected_cases'] != 202
            or pins.get('expected_cases') != 202 or q.get('pins_sha256') != pins_sha
            or any(type(q.get(k)) is not int or q[k] != v or pins.get(k) != v for k, v in groups.items())
            or q.get('canonical_source_sha256') != CANONICAL or pins.get('canonical_source_sha256') != CANONICAL
            or q.get('canonical_files') != 432 or pins.get('canonical_files') != 432
            or any(q.get(name) is not False for name in false_flags)
            or q.get('fabricated_publication_weight_bytes_not_deserialized') is not True
            or type(q.get('original_case_attempts_remaining')) is not int or q['original_case_attempts_remaining'] != 0
            or q.get('skipped_reports') != [] or q.get('unexpected_denials') != 0
            or q.get('torch_threads') != 1 or q.get('torch_interop_threads') != 1 or q.get('gpu_hidden') is not True
            or q.get('source_pins_rechecked') != len(pins['files'])
            or q.get('runtime_pins_rechecked') != len(pins['runtime'])
            or q.get('source_review_sha256') != pins.get('source_review_sha256')):
        raise ValueError('complete current202-case synthetic/public-metadata qualification required')
    source_review = Path(pins['source_review_path'])
    if source_review != RUN / 'source-review.json' or digest(source_review) != pins['source_review_sha256']:
        raise ValueError('current independent source review differs')
    review = json_file(source_review)
    if (review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
            or review.get('files') != pins['reviewed_files']):
        raise ValueError('settled current independent review required')
    reports = q['reports']
    if (type(reports) is not list or len(reports) != 202
            or any(type(r) is not dict or r.get('phase') != 'call' or r.get('outcome') != 'passed'
                   or type(r.get('nodeid')) is not str for r in reports)
            or len({r['nodeid'] for r in reports}) != 202):
        raise ValueError('exact202 distinct passing call reports required')
    observed_groups = {name: 0 for name in groups}
    public_positive, public_negative = 0, 0
    for report in reports:
        nodeid = report['nodeid'].replace('\\', '/')
        file_name, test_name = nodeid.split('::', 1)
        if file_name.endswith('docs/phase2/cho51_tensor_collection_v1/test_collection.py'):
            observed_groups['mocked_tensor_receipt_cases'] += 1
        elif file_name.endswith('docs/phase2/cho51_selector_collection_v1/test_collection.py'):
            observed_groups['mocked_selector_collection_cases'] += 1
        elif file_name.endswith(RUN.relative_to(ROOT).as_posix() + '/test_public_selector.py'):
            observed_groups['actual_public_verifier_fabricated_record_cases'] += 1
            if test_name.startswith('test_actual_public_selector_bridge_on_fabricated_complete_records['):
                public_positive += 1
            elif test_name.startswith('test_public_verifier_refuses_resealed_complete_record_tampering['):
                public_negative += 1
            else:
                raise ValueError('unreviewed public fixture report')
        else:
            raise ValueError('unreviewed test report: ' + nodeid)
    if observed_groups != groups or (public_positive, public_negative) != (8, 16):
        raise ValueError('expected122tensor+56selector+8public+16tamper exact report inventory')
    verify_current_inputs(pins, q)
    launcher_path = ROOT / 'docs/phase2/cho51_tensor_verification_v1/launcher.py'
    if pins['files'].get(launcher_path.relative_to(ROOT).as_posix()) != digest(launcher_path):
        raise ValueError('independently pinned standard-library native absence helper required')
    spec = importlib.util.spec_from_file_location('_receipt_selector_closeout_stdlib_launcher', launcher_path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    guard_pin_view = {
        'files': {str(ROOT / relative): expected for relative, expected in pins['files'].items()},
        'runtime': pins['runtime'],
    }
    expected_operation_pins = launcher._guard_operation_pins(guard_pin_view)
    expected_runtime_pins = launcher._guard_runtime_pins(guard_pin_view)

    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'validate.py'),
               '--pins', str(pins_path), '--expect-pins', pins_sha, '--output', str(VALIDATION)]
    paths = {path for path in RUN.iterdir() if path.is_file() and path.suffix in {'.py', '.ps1', '.json'}}
    for relative in ('docs/phase2/cho51_tensor_collection_v1', 'docs/phase2/cho51_selector_collection_v1'):
        paths.update(path for path in (ROOT / relative).iterdir() if path.is_file() and path.suffix in {'.py', '.md'})
    paths.update((qualification_path, VALIDATION / 'junit.xml', VALIDATION / 'pytest.log'))
    attempts, accepted = [], []
    native_proof_identities = {}
    for native in sorted((ROOT / 'runs/migration').iterdir()):
        admission_path, receipt_path = native / 'admission.json', native / 'receipt.json'
        if not native.is_dir() or not admission_path.is_file():
            continue
        admission_raw, admission_identity = read(admission_path)
        admission = decode(admission_raw)
        previous_command = admission.get('command')
        if (type(previous_command) is not list
                or not any(type(token) is str and token.startswith(str(RUN) + os.sep) for token in previous_command)):
            continue
        if not receipt_path.is_file():
            raise ValueError('owned native attempt is unfinished: ' + str(native))
        receipt_raw, receipt_identity = read(receipt_path)
        receipt = decode(receipt_raw)
        native_proof_identities.update({admission_path: admission_identity, receipt_path: receipt_identity})
        state = receipt.get('native_state')
        if type(state) is not dict or receipt.get('schema') != 'migration_guard_receipt_v1':
            raise ValueError('owned native receipt shape differs')
        created = state.get('job_created') is True
        absence = None
        if created:
            if (receipt.get('job_absent') is not True or state.get('job_empty_before_close') is not True
                    or state.get('job_closed') is not True or state.get('cleanup_errors') != []
                    or state.get('peak_sampling_errors') != []
                    or receipt.get('job_name') != 'pro3_migration_' + native.name
                    or state.get('job_named') != receipt['job_name']):
                raise ValueError('every created owned Job must have confirmed empty/closed cleanup')
            launcher._job_absent(receipt['job_name'])
            absence = True
        current = previous_command == command
        if current and receipt.get('accepted') is True:
            required_state = ('created_suspended', 'limits_set', 'atomic_job_assignment_requested',
                'atomic_job_assignment_verified', 'assigned', 'limits_query_verified', 'membership_verified',
                'resumed', 'root_exit_after_job_close', 'process_handle_closed', 'thread_handle_closed', 'assignment_step_seen')
            result = receipt.get('result')
            samples = admission.get('startup_samples')
            if (not created or absence is not True or admission.get('schema') != 'migration_admission_v1'
                    or admission.get('source_sha256') != CANONICAL or receipt.get('error') is not None
                    or admission.get('operation_pins') != expected_operation_pins
                    or admission.get('selected_runtime_pins') != expected_runtime_pins
                    or receipt.get('scientific_admission') is not False
                    or type(result) is not dict or result.get('reason') != 'normal' or type(result.get('exit_code')) is not int or result['exit_code'] != 0
                    or any(state.get(key) is not True for key in required_state)
                    or any(type(admission.get(k)) is not int or admission[k] != v for k, v in (
                        ('process_mib', 2048), ('job_mib', 3072), ('active_ram_gib', 4), ('active_disk_gib', 20), ('native_threads', 1)))
                    or admission.get('peer_pause_file') != 'D:\\Aenv\\pro2\\WORK\\resume-20261015-001\\coordination\\PRO2_REQUEST_PRO3_PAUSE.json'
                    or type(samples) is not list or len(samples) != 2 or receipt.get('startup_samples') != samples
                    or any(type(s.get('available_ram_bytes')) is not int or s['available_ram_bytes'] < 10 * 1024**3
                           or type(s.get('free_disk_bytes')) is not int or s['free_disk_bytes'] < 20 * 1024**3 for s in samples)):
                raise ValueError('exact current native acceptance/source/limits/startup/cleanup required')
            start, end, completed = (datetime.fromisoformat(value) for value in (
                admission['started_utc'], admission['deadline_utc'], receipt['completed_utc']))
            if (any(t.utcoffset() != timezone.utc.utcoffset(t) for t in (start, end, completed))
                    or (end - start).total_seconds() != 600 or not start <= completed <= end):
                raise ValueError('finite600-second UTC execution window required')
            for field, cap in (('peak_process_commit_bytes', 2048 * 1024**2), ('peak_job_commit_bytes', 3072 * 1024**2)):
                if type(state.get(field)) is not int or not 0 < state[field] <= cap:
                    raise ValueError('bounded measured native peaks required')
            if (state.get('process_limit_bytes') != 2048 * 1024**2 or state.get('aggregate_limit_bytes') != 3072 * 1024**2
                    or type(state.get('peak_samples')) is not int or state['peak_samples'] <= 0
                    or result.get('peak_process_memory_bytes') != state['peak_process_commit_bytes']
                    or result.get('peak_job_memory_bytes') != state['peak_job_commit_bytes']):
                raise ValueError('native measured limits/results differ')
            for relative, expected in admission['operation_pins'].items():
                path = ROOT / relative
                if ('..' in path.parts or not path.is_relative_to(ROOT)
                        or pins['files'].get(relative) != expected or digest(path) != expected):
                    raise ValueError('current native operation pin differs: ' + relative)
            for name, expected in admission['selected_runtime_pins'].items():
                if pins['runtime'].get(name) != expected or digest(Path(name), single_link=False) != expected:
                    raise ValueError('current native selected runtime pin differs: ' + name)
            accepted.append((native, admission, receipt))
        attempts.append(dict(directory=native.relative_to(ROOT).as_posix(), accepted=receipt.get('accepted') is True,
            exact_current_command=current, completed_utc=receipt.get('completed_utc'), job_created=created,
            fresh_named_job_absence_verified=absence,
            cleanup='closed_empty_freshly_absent' if created else 'not_applicable_no_job_created',
            peak_process_bytes=state.get('peak_process_commit_bytes'), peak_job_bytes=state.get('peak_job_commit_bytes')))
        paths.update((admission_path, receipt_path))
        paths.update(path for path in native.iterdir() if path.is_file()
                     and (path.name == 'deadline.json' or path.name.startswith('command')))
    if len(accepted) != 1:
        raise ValueError('exactly one accepted current-command native receipt required')
    native, admission, receipt = accepted[0]
    state = receipt['native_state']
    # Preflight every artifact before creating the create-once archive.
    artifacts = []
    for path in sorted(paths):
        if path.suffix.lower() in {'.safetensors', '.npz', '.npy', '.pt', '.pth', '.pkl'}:
            raise ValueError('weights/data/fabricated fixture payloads are not archival artifacts')
        raw, observed = read(path)
        if path in native_proof_identities and observed != native_proof_identities[path]:
            raise ValueError('native proof changed after validation: ' + str(path))
        artifacts.append((path, raw, observed))
    verify_current_inputs(pins, q)
    if read(pins_path)[1] != pins_identity or read(qualification_path)[1] != q_identity:
        raise ValueError('pins/qualification changed before archival')
    OUT.mkdir(exist_ok=False)
    manifest_rows = []
    for path, raw, observed in artifacts:
        target = OUT / 'artifacts' / path.relative_to(ROOT)
        io_path(target.parent).mkdir(parents=True, exist_ok=True)
        with io_path(target).open('xb') as stream:
            stream.write(raw)
        if read(path)[1] != observed or digest(target) != observed[-1]:
            raise ValueError('artifact changed during archival: ' + str(path))
        manifest_rows.append(dict(source=path.relative_to(ROOT).as_posix(), path=target.relative_to(OUT).as_posix(),
                                  bytes=len(raw), sha256=observed[-1]))
    verify_current_inputs(pins, q)
    for path, expected_identity in native_proof_identities.items():
        if read(path)[1] != expected_identity:
            raise ValueError('native proof changed across archival: ' + str(path))
    launcher._job_absent(receipt['job_name'])
    summary = dict(
        schema='cho51_receipt_selector_engineering_closeout_v1', observed_utc=datetime.now(timezone.utc).isoformat(),
        passed_checks=202, mocked_boundary_cases=178, mocked_tensor_receipt_cases=122, mocked_selector_collection_cases=56,
        actual_public_verifier_fabricated_record_cases=24, actual_canonical_factored_public_helper_cases=8,
        actual_public_verifier_tamper_negative_cases=16, all_public_selector_records_fabricated=True,
        canonical_source_sha256=CANONICAL, canonical_files=432, pins_sha256=pins_sha,
        source_pins_rechecked=len(pins['files']), runtime_pins_rechecked=len(pins['runtime']),
        loaded_module_files_rechecked=len(q['observed_loaded_module_hashes']),
        current_qualification_native=native.relative_to(ROOT).as_posix(), native_completed_utc=receipt['completed_utc'],
        native_job_closed_empty_freshly_absent=True, native_attempts=attempts,
        peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes'],
        actual_1020_case_native_tensor_roster_verified=False, actual_selected_study_tensor_proofs_verified=False,
        full_study_verified=False, full_selector_evidence_verified=False, actual_training_performed=False,
        actual_recording_prediction_performed=False, actual_input_or_selected_study_weights_used=False,
        actual_publication_or_selector_training_history_verified=False, selection_publication_tensor_verified=False,
        scientific_admission=False, experiment_freeze_signed=False, original_case_attempts_remaining=0,
        original_case_used=False, artifact_count=len(manifest_rows),
    )
    write_json(OUT / 'manifest.json', dict(artifacts=manifest_rows))
    write_json(OUT / 'summary.json', summary)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
