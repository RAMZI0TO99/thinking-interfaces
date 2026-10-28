"""Standard-library prelaunch refusal audit; no successful validation claim."""
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata_common as control

PINS_SHA = '344e9baf80fd3c7ae7763393e0b3ad811b7dc862218473686413e91092ede62d'
NATIVE = control.ROOT / 'runs/migration/20261025T170414Z_bd82341364'
JOB = 'pro3_migration_' + NATIVE.name


def main():
    pins = control.pins(PINS_SHA)
    control.verify_files(pins)
    root, peer = control.admission(pins, PINS_SHA)
    receipt = control.document(NATIVE / 'receipt.json')
    dispatch = control.document(control.RUN / 'dispatch_001.json')
    dispatched = control.document(control.RUN / 'dispatch-result_001.json')
    marker = control.document(control.RUN / 'guard-attempt_001.json')
    control.need(receipt['accepted'] is False and receipt['job_name'] == JOB
                 and receipt['job_absent'] is True and receipt['result'] is None
                 and receipt['error'] == 'startup requires 8 GiB available RAM and 20 GiB free disk'
                 and receipt['scientific_admission'] is False
                 and type(dispatched['exit_code']) is int and dispatched['exit_code'] == 1
                 and dispatched['pins_sha256'] == PINS_SHA, 'exact prelaunch refusal required')
    state = receipt['native_state']
    for field in ('job_created', 'created_suspended', 'assigned', 'atomic_job_assignment_requested',
                  'atomic_job_assignment_verified', 'limits_set', 'limits_query_verified',
                  'membership_verified', 'resumed', 'job_empty_before_close', 'job_closed',
                  'root_exit_after_job_close', 'process_handle_closed', 'thread_handle_closed',
                  'assignment_step_seen', 'owned_job_termination_called'):
        control.need(state[field] is False, 'no Job or child was created at refusal')
    control.need(state['cleanup_errors'] == state['peak_sampling_errors'] == []
                 and all(type(state[field]) is int and state[field] == 0
                     for field in ('peak_samples', 'peak_process_commit_bytes', 'peak_job_commit_bytes')),
                 'prelaunch counters must remain exact zero')
    samples = receipt['startup_samples']
    control.need(len(samples) == 1 and type(samples[0]['available_ram_bytes']) is int
                 and samples[0]['available_ram_bytes'] < 8 * 1024**3
                 and samples[0]['free_disk_bytes'] >= 20 * 1024**3, 'observed RAM refusal required')
    control.need(marker['pins_sha256'] == dispatch['pins_sha256'] == PINS_SHA
                 and marker['root_admission_sha256'] == control.read(control.RUN / 'admission.json', retain=False)[0]
                 and marker['dispatch_sha256'] == control.read(control.RUN / 'dispatch_001.json', retain=False)[0]
                 and marker['peer_release_sha256'] == root['peer_release_sha256']
                 and marker['maximum_jobs'] == 1 and marker['automatic_retry_permitted'] is False,
                 'consumed attempt and exact Root dispatch required')
    control.need(not control.OUTPUT.exists() and not (NATIVE / 'admission.json').exists()
                 and not (NATIVE / 'deadline.json').exists(), 'no admitted child/output/deadline at refusal')
    control.job_absent(JOB)
    summary = dict(schema='cho51_canonical_boundary_prelaunch_refusal_closeout_v1',
        observed_utc=datetime.now(timezone.utc).isoformat(), cleanup_verified=True,
        validation_passed=False, pins_sha256=PINS_SHA, job_name=JOB, job_created=False,
        jobs_executed=0, guard_attempt_consumed=True, startup_available_ram_bytes=samples[0]['available_ram_bytes'],
        native_receipt_sha256=control.read(NATIVE / 'receipt.json', retain=False)[0],
        peer_release_sha256=root['peer_release_sha256'], source_and_runtime_pins_unchanged=True,
        fresh_named_job_absent=True, candidate_imported=False, successful_test_evidence=False,
        automatic_retry_permitted=False, scientific_admission=False)
    control.write(control.RUN / 'refusal-closeout_001.json', summary)
    print(control.canonical(summary).decode(), flush=True)


if __name__ == '__main__':
    main()
