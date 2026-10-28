"""Standard-library timeout cleanup only; incomplete tests are not accepted."""
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata_common as control

PINS_SHA = '9d195ef2d32f7932788490a01395cbeac16a750cc9a33a2be516a352d4a35f95'
NATIVE = control.ROOT / 'runs/migration/20261025T182023Z_be9e746d5e'
JOB = 'pro3_migration_' + NATIVE.name


def main():
    pins = control.pins(PINS_SHA)
    control.verify_files(pins)
    root, peer = control.admission(pins, PINS_SHA)
    receipt = control.document(NATIVE / 'receipt.json')
    admission = control.document(NATIVE / 'admission.json')
    deadline = control.document(NATIVE / 'deadline.json')
    dispatched = control.document(control.RUN / 'dispatch-result_001.json')
    control.need(receipt['accepted'] is False and receipt['job_name'] == JOB
                 and receipt['job_absent'] is True and receipt['result']['reason'] == 'attempt_deadline'
                 and type(receipt['result']['exit_code']) is int and receipt['result']['exit_code'] == 1
                 and dispatched['exit_code'] == 1 and dispatched['pins_sha256'] == PINS_SHA,
                 'exact incomplete deadline attempt required')
    state = receipt['native_state']
    for field in ('created_suspended', 'atomic_job_assignment_verified', 'limits_query_verified',
                  'membership_verified', 'owned_job_termination_called', 'job_empty_before_close',
                  'job_closed', 'process_handle_closed', 'thread_handle_closed'):
        control.need(state[field] is True, 'native timeout cleanup incomplete')
    control.need(state['cleanup_errors'] == state['peak_sampling_errors'] == []
                 and state['active_before_cleanup'] == 0 and state['limit_flags'] == 8960
                 and state['process_limit_bytes'] == 4096 * 1024**2
                 and state['aggregate_limit_bytes'] == 5120 * 1024**2
                 and state['peak_process_commit_bytes'] <= 4096 * 1024**2
                 and state['peak_job_commit_bytes'] <= 5120 * 1024**2, 'native cleanup or cap failure')
    control.need(admission['pins_sha256'] == PINS_SHA and admission['root_admission_sha256']
                 == control.read(control.RUN / 'admission.json', retain=False)[0], 'native admission differs')
    start = datetime.fromisoformat(admission['started_utc'])
    attempt = datetime.fromisoformat(deadline['attempt_deadline_utc'])
    session = datetime.fromisoformat(deadline['session_deadline_utc'])
    completed = datetime.fromisoformat(receipt['completed_utc'])
    control.need((attempt-start).total_seconds() == 600 and (session-attempt).total_seconds() == 5
                 and attempt <= completed <= session, 'unchanged deadline cleanup required')
    control.need(not any((control.OUTPUT / name).exists() for name in ('result.json', 'failure.json', 'junit.xml')),
                 'incomplete attempt has no complete result or JUnit')
    marker = control.document(control.RUN / 'guard-attempt_001.json', admission['guard_attempt_sha256'])
    control.need(marker['pins_sha256'] == PINS_SHA and marker['maximum_jobs'] == 1
                 and marker['automatic_retry_permitted'] is False, 'consumed marker required')
    control.job_absent(JOB)
    summary = dict(schema='cho51_canonical_boundary_timeout_closeout_v1',
        observed_utc=datetime.now(timezone.utc).isoformat(), cleanup_verified=True,
        validation_passed=False, pins_sha256=PINS_SHA, job_name=JOB, exit_code=1,
        reason='attempt_deadline', expected_numerical_budget=dict(control.ZERO),
        complete_runtime_counter_report_available=False, successful_test_evidence=False,
        native_receipt_sha256=control.read(NATIVE / 'receipt.json', retain=False)[0],
        peer_release_sha256=root['peer_release_sha256'], source_and_runtime_pins_unchanged=True,
        fresh_native_job_absent=True, native_closed_empty=True, native_handles_closed=True,
        automatic_retry_permitted=False, scientific_admission=False)
    control.write(control.RUN / 'timeout-closeout_001.json', summary)
    print(control.canonical(summary).decode(), flush=True)


if __name__ == '__main__':
    main()
