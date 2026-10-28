"""Standard-library failure cleanup audit; not successful unit qualification."""
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata_common as control

PINS_SHA = 'b4f12a1b2e4f3f10676932a0a7e0ec6051ed0d0e019ade899dfa0f0381599d19'
NATIVE = control.ROOT / 'runs/migration/20261025T163106Z_e0e0f64c37'
JOB = 'pro3_migration_' + NATIVE.name


def main():
    pins = control.pins(PINS_SHA)
    control.verify_files(pins)
    root, peer = control.admission(pins, PINS_SHA)
    receipt = control.document(NATIVE / 'receipt.json')
    admission = control.document(NATIVE / 'admission.json')
    failure = control.document(control.OUTPUT / 'failure.json')
    dispatched = control.document(control.RUN / 'dispatch-result_001.json')
    control.need(receipt['accepted'] is False and receipt['job_name'] == JOB
                 and receipt['job_absent'] is True and receipt['result']['reason'] == 'normal'
                 and type(receipt['result']['exit_code']) is int and receipt['result']['exit_code'] == 1
                 and dispatched['exit_code'] == 1 and dispatched['pins_sha256'] == PINS_SHA,
                 'exact failed native attempt required, never a successful suite')
    state = receipt['native_state']
    for field in ('created_suspended', 'atomic_job_assignment_verified', 'limits_query_verified',
                  'membership_verified', 'job_empty_before_close', 'job_closed',
                  'process_handle_closed', 'thread_handle_closed'):
        control.need(state[field] is True, 'native closure incomplete')
    control.need(state['cleanup_errors'] == state['peak_sampling_errors'] == []
                 and state['active_before_cleanup'] == 0 and state['limit_flags'] == 8960
                 and state['process_limit_bytes'] == 4096 * 1024**2
                 and state['aggregate_limit_bytes'] == 5120 * 1024**2
                 and state['peak_process_commit_bytes'] <= 4096 * 1024**2
                 and state['peak_job_commit_bytes'] <= 5120 * 1024**2, 'native cleanup/cap failure')
    control.need(admission['pins_sha256'] == PINS_SHA and admission['root_admission_sha256']
                 == control.read(control.RUN / 'admission.json', retain=False)[0], 'native source admission differs')
    control.need(failure['passed'] is False and failure['pins_sha256'] == PINS_SHA
                 and control.zero_budget(failure['current_counter_ledger'])
                 and failure['forbidden_calls'] == {} and failure['scientific_admission'] is False
                 and failure['unexpected_denials'] == [dict(detail=r'\\.\nul',
                     event='outside_normalized_mutation', phase='metadata_assessment')]
                 and not (control.OUTPUT / 'result.json').exists(), 'exact failed logging confinement required')
    marker = control.document(control.RUN / 'guard-attempt_001.json', admission['guard_attempt_sha256'])
    control.need(marker['pins_sha256'] == PINS_SHA and marker['maximum_jobs'] == 1
                 and marker['automatic_retry_permitted'] is False, 'consumed once-only marker required')
    control.job_absent(JOB)
    summary = dict(schema='cho51_canonical_boundary_failed_attempt_closeout_v1',
        observed_utc=datetime.now(timezone.utc).isoformat(), cleanup_verified=True,
        validation_passed=False, pins_sha256=PINS_SHA, job_name=JOB, normal_process_exit=1,
        native_receipt_sha256=control.read(NATIVE / 'receipt.json', retain=False)[0],
        failure_sha256=control.read(control.OUTPUT / 'failure.json', retain=False)[0],
        peer_release_sha256=root['peer_release_sha256'], source_and_runtime_pins_unchanged=True,
        fresh_native_job_absent=True, native_closed_empty=True, native_handles_closed=True,
        failed_case='pytest configuration attempted Windows null-device logging outside owned output',
        successful_test_evidence=False, automatic_retry_permitted=False, scientific_admission=False)
    control.write(control.RUN / 'failure-closeout_001.json', summary)
    print(control.canonical(summary).decode(), flush=True)


if __name__ == '__main__':
    main()
