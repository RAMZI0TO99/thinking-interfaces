"""Standard-library authentication of the composed numerical worker and native closure."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
from fractions import Fraction
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
OUT = RUN / 'validation_001'
ARCHIVE = ROOT / 'evidence/cho51-provenance-numerical-worker-20261025-v3'
sys.path.insert(0, str(RUN))
import origin


def fields(value, expected):
    origin.need(type(value) is dict and all(type(value.get(name)) is type(item) and value[name] == item
                for name, item in expected.items()), 'exact fields differ: ' + ', '.join(expected))


def write_once(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def envelope(value, payload):
    expected = dict(schema_version=1, phase=2, kind='engineering_smoke', payload=payload)
    expected['sha256'] = hashlib.sha256(origin.canonical(expected).rstrip(b'\n')).hexdigest()
    origin.need(value == expected, 'exact engineering envelope differs')


def job_absent(name):
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.OpenJobObjectW.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_wchar_p]
    api.OpenJobObjectW.restype = ctypes.c_void_p
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    ctypes.set_last_error(0)
    handle = api.OpenJobObjectW(4, False, name)
    error = ctypes.get_last_error()
    if handle:
        api.CloseHandle(handle)
    origin.need(not handle and error == 2, 'fresh named native Job absence unconfirmed')


def verify_native(directory, command, pins):
    directory = Path(directory)
    origin.need(directory.resolve(strict=True) == directory and directory.parent == ROOT / 'runs/migration'
                and re.fullmatch(r'\d{8}T\d{6}Z_[a-f0-9]{10}', directory.name), 'direct dispatched native directory required')
    admission = origin.document(directory / 'admission.json')
    receipt = origin.document(directory / 'receipt.json')
    deadline = origin.document(directory / 'deadline.json')
    operations = {name: value for name, value in pins['files'].items()
                  if Path(name).parent == Path('tools/migration') and Path(name).suffix in {'.py', '.ps1', '.json', '.lock'}
                  or name == 'evaluation/phase2_supervision_primitives.py'
                  or name in pins['reviewed_files'] and Path(name).parent == RUN.relative_to(ROOT)}
    runtime = {name: value for name, value in pins['runtime'].items()
               if Path(name) == ROOT / '.venv/Scripts/python.exe' or Path(name).name in {'python312.dll', 'python3.dll'}}
    job_name = 'pro3_migration_' + directory.name
    fields(admission, dict(schema='migration_admission_v1', source_sha256=origin.CANONICAL, command=command,
                          operation_pins=operations, selected_runtime_pins=runtime, process_mib=4096, job_mib=5120,
                          guard_policy_schema='cho51_provenance_numerical_worker_guard_v1', startup_ram_gib=4,
                          previous_startup_ram_gib=10, historical_10gib_startup_pass_claimed=False,
                          owner_resource_amendment_path=pins['owner_resource_amendment_path'],
                          owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256'],
                          active_ram_gib=4, active_disk_gib=20, native_threads=1,
                          peer_pause_file='D:\\Aenv\\pro2\\WORK\\resume-20261025-001\\coordination\\PRO2_REQUEST_PRO3_PAUSE.json'))
    fields(receipt, dict(schema='migration_guard_receipt_v1', accepted=True, job_name=job_name,
                        job_absent=True, scientific_admission=False, error=None))
    state, result = receipt['native_state'], receipt['result']
    flags = ('job_created', 'created_suspended', 'limits_set', 'limits_query_verified', 'atomic_job_assignment_requested',
             'atomic_job_assignment_verified', 'assigned', 'membership_verified', 'resumed', 'job_empty_before_close',
             'job_closed', 'process_handle_closed', 'thread_handle_closed', 'root_exit_after_job_close', 'assignment_step_seen')
    fields(state, dict.fromkeys(flags, True) | dict(job_named=job_name, cleanup_errors=[], peak_sampling_errors=[],
                                                  process_limit_bytes=4096 * 1024**2, aggregate_limit_bytes=5120 * 1024**2))
    fields(result, dict(reason='normal', exit_code=0))
    origin.need(type(state['peak_samples']) is int and state['peak_samples'] > 0, 'actual native samples required')
    for key, other, maximum in (('peak_process_commit_bytes', 'peak_process_memory_bytes', 4096 * 1024**2),
                                ('peak_job_commit_bytes', 'peak_job_memory_bytes', 5120 * 1024**2)):
        origin.need(type(state[key]) is int and 0 < state[key] <= maximum and state[key] == result[other],
                    'positive native peaks within fixed caps required')
    origin.need(state['peak_job_commit_bytes'] >= state['peak_process_commit_bytes'], 'native aggregate peak below process peak')
    samples = admission['startup_samples']
    origin.need(len(samples) == 2 and samples == receipt['startup_samples'] and all(
        type(row['available_ram_bytes']) is int and row['available_ram_bytes'] >= 4 * 1024**3
        and type(row['free_disk_bytes']) is int and row['free_disk_bytes'] >= 20 * 1024**3 for row in samples),
        'two genuine owner-amended RAM4 GiB and disk20 GiB startup samples required')
    utc = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    started, ended, limit = (utc(value) for value in (admission['started_utc'], receipt['completed_utc'], admission['deadline_utc']))
    origin.need((limit - started).total_seconds() == 600 and started <= ended <= limit, 'exact finite600 second Job required')
    fields(deadline, dict(schema='phase2_supervision_deadlines_v1', attempt_deadline_utc=admission['deadline_utc']))
    origin.need((utc(deadline['session_deadline_utc']) - limit).total_seconds() == 5, 'exact five second supervisor margin required')
    job_absent(job_name)
    return dict(native_directory=str(directory), job_name=job_name, accepted=True,
                receipt_sha256=origin.digest(directory / 'receipt.json'), started_utc=admission['started_utc'],
                completed_utc=receipt['completed_utc'], elapsed_seconds=(ended - started).total_seconds(),
                peak_process_bytes=state['peak_process_commit_bytes'], peak_job_bytes=state['peak_job_commit_bytes'],
                closed_empty_handles_closed_freshly_absent=True)


def verify_canonical(pins):
    manifest = origin.document(ROOT / 'tools/migration/source-files.json', pins['files']['tools/migration/source-files.json'])
    rows = manifest['files']
    origin.need(len(rows) == 432, 'exact canonical432 manifest required')
    aggregate = hashlib.sha256('\n'.join(f"{row['path']}:{row['sha256']}" for row in rows).encode()).hexdigest()
    origin.need(aggregate == manifest['source_sha256'] == origin.CANONICAL, 'canonical manifest aggregate differs')
    for row in rows:
        origin.need(origin.digest(ROOT / row['path']) == row['sha256'], 'canonical source changed')
    directories = ('core', 'encoder', 'adaptation', 'data', 'realtime', 'evaluation', 'scripts', 'tests', 'configs')
    found = set()
    for directory in directories:
        for path in (ROOT / directory).rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.py', '.toml', '.ps1'}:
                relative = path.relative_to(ROOT).as_posix()
                if not relative.startswith(('data/raw/', 'data/processed/', 'data/interim/')) and path.name != 'local.toml':
                    found.add(relative)
    found.update(row['path'] for row in rows if row['path'].split('/')[0] not in directories)
    origin.need(found == {row['path'] for row in rows}, 'canonical added or removed source detected')


def verify_pins(pins, expected):
    origin.need(origin.digest(RUN / 'pins.json') == expected, 'fresh pins changed')
    for name, value in pins['files'].items():
        origin.need(origin.digest(ROOT / name) == value, 'source/context pin changed')
    for group in ('runtime', 'runtime_modules', 'supporting_runtime_sources'):
        for name, value in pins[group].items():
            origin.need(origin.digest(name) == value, 'fresh current runtime changed')
    fields(origin.document(RUN / 'source-review.json', pins['source_review_sha256']),
           dict(source_only=True, remaining_actionable_findings=[], files=pins['reviewed_files']))
    amendment_path = Path(pins['owner_resource_amendment_path'])
    origin.need(amendment_path == RUN / 'owner-resource-amendment.json', 'exact owner amendment path required')
    fields(origin.document(amendment_path, pins['owner_resource_amendment_sha256']),
           dict(schema='cho51_provenance_numerical_worker_owner_resource_amendment_v1',
                scope='cho51_provenance_numerical_worker_20261025_v3', previous_startup_ram_gib=10,
                owner_instruction_exact='use the available ram now!',
                startup_ram_gib=4, active_ram_gib=4, disk_gib=20, maximum_job_seconds=600,
                process_mib=4096, job_mib=5120, threads=1, gpu_hidden=True,
                canonical_guard_modified=False, historical_receipts_requalified=False, scientific_admission=False))
    origin.need(origin.digest(RUN / 'native-runtime.json') == pins['native_runtime_sha256'], 'native transition observation changed')
    verify_canonical(pins)


BUDGET = dict(source_updates=0, restore_count=1, support_updates=1, gradient_updates=1,
              target_inference_calls=1, query_count=2, model_constructions=1, measured_cells=0)
OBSERVER = dict(model_constructions=1, constructor_dummy_forward_calls=1, classifier_forward_calls=2,
                backbone_forward_calls=2, profile_a_loads=4, profile_b_loads=2, npz_loads=6,
                clone_reinitializations=4, empty_mask_containers=2, factory_restore_calls=1, factory_restore_returns=1)
PAUSES = tuple(Path('D:/Aenv/pro2/WORK') / f'resume-{day}-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json'
               for day in ('20261007', '20261012', '20261013', '20261015', '20261025'))


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def same(value, expected, label):
    origin.need(origin.canonical(value) == origin.canonical(expected), label + ' differs')


def sha(value):
    origin.need(type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None, 'plain exact SHA256 required')
    return value


def counts(value, expected, label):
    origin.need(type(value) is dict and set(value) == set(expected)
                and all(type(value[name]) is int and value[name] == count for name, count in expected.items()),
                label + ' requires exact plain integer counts')


def bounded_bytes(path, maximum=8 * 1024**2, expected=None):
    before = origin.identity(path)
    origin.need(0 <= before[2] <= maximum and (expected is None or before[-1] == expected), 'bounded physical file required')
    with Path(path).open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(before[2] + 1)
        finished = os.fstat(stream.fileno())
    key = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    origin.need(len(raw) == before[2] and key(opened) == key(finished) and key(opened)[:4] == before[:4]
                and origin.identity(path) == before and hashlib.sha256(raw).hexdigest() == before[-1],
                'physical bytes changed during fixed bounded read')
    return raw


def canonical_document(path, expected=None, *, newline=True):
    value = origin.document(path, expected)
    expected_raw = origin.canonical(value) if newline else compact(value).encode()
    origin.need(bounded_bytes(path, expected=expected) == expected_raw, 'exact canonical physical JSON bytes required')
    return value


def verify_observer(value):
    origin.need(type(value) is dict and set(value) == set(OBSERVER) | {'numerical_calls'}, 'exact independent observer schema required')
    fields(value, OBSERVER)
    calls = value['numerical_calls']
    required = dict(module_load_state_dict=2, safetensors_load=2, optimizer_init=1,
                    sgd_step=1, tensor_backward=1, autograd_backward=1)
    origin.need(type(calls) is dict and set(calls) == set(required) | {'model_module_init'}, 'exact seven observed numerical operations required')
    fields(calls, required)
    origin.need(type(calls['model_module_init']) is int and calls['model_module_init'] > 0, 'actual observed model-module construction required')
    return calls


def verify_target(target, summary, historical, current):
    fields(target, dict(schema='cho51-linear-target-route-engineering-v1', accepted=True, engineering_only=True,
                        scientific_admission=False, measured_cells=0, record_cell_calls=0, source_updates=0,
                        support_updates=1, gradient_updates=1, current_restore_callback_calls=1, target_inference_calls=1,
                        query_count=2, original_case_attempts_remaining=0,
                        source_state_sha256=summary['selected_state_sha256'], contract=summary['target_contract'],
                        profile_binding=summary['target_profile_binding'],
                        profile_binding_sha256=historical['target_profile_binding_sha256'],
                        provenance=dict(current=current, historical=summary['historical_source']),
                        caller_source_runner_source_and_adapted_storage_disjoint=True))
    observed = target['witnesses']
    fields(observed, dict(calls=dict(adaptation=1, support_forward=1, backward=1, sgd_step=1, query_forward=1, runner_prediction=1),
                          finite_gradients=True, query_inference_mode=True, all_modules_eval=True, source_unchanged=True,
                          backbone_and_buffers_unchanged=True, owned_source_and_adapted_storage_disjoint=True,
                          query_labels_used_for_adaptation=False, unused_pool_used_for_adaptation=False,
                          classifier_input_shapes=[[10, 64, 800], [2, 64, 800]]))
    heads = {'head.weight', 'head.bias'}
    before, after = observed['before_state_tensors'], observed['after_state_tensors']
    source = target['source_state_tensors']
    origin.need(type(source) is dict and type(before) is dict and type(after) is dict and len(before) == 223
                and set(source) == set(before) == set(after) and before == source
                and {name for name in before if before[name] != after[name]} == heads,
                'all223 source tensors and only both changed head tensors required')
    prior_path = Path(summary['target_proof_paths']['target_witness_file_sha256'])
    prior = origin.document(prior_path, historical['target_witness_file_sha256'])
    same(source, prior['source_state_tensors'], 'authenticated selected source tensor inventory')
    for inventory in (source, before, after):
        for name, value in inventory.items():
            origin.need(type(name) is str, 'plain tensor name required')
            sha(value)
    origin.need(type(observed['changed_state_names']) is list and len(observed['changed_state_names']) == 2
                and set(observed['changed_state_names']) == heads, 'exact head change names required')
    fields(observed['mask'], dict(method='linear', trainable_parameters=402, trainable_names=['head.weight', 'head.bias'],
                                 depth=0, selected_blocks=[]))
    gradients, norms = observed['gradient_sha256'], observed['gradient_norms']
    origin.need(type(gradients) is dict and type(norms) is dict and set(gradients) == set(norms) == heads,
                'both head gradient observations required')
    for name in heads:
        sha(gradients[name])
        origin.need(type(norms[name]) in (int, float) and math.isfinite(norms[name]) and norms[name] > 0,
                    'finite positive head gradient norm required')
    losses = observed['support_losses']
    origin.need(type(losses) is list and len(losses) == 1 and type(losses[0]) in (int, float) and math.isfinite(losses[0]),
                'one finite support loss required')
    adapted = sha(observed['adapted_state_sha256'])
    logits, labels = target['query_logits'], target['query_targets']
    origin.need(type(logits) is list and len(logits) == 2 and all(type(row) is list and len(row) == 2 for row in logits)
                and all(type(number) in (int, float) and math.isfinite(number) for row in logits for number in row)
                and type(labels) is list and all(type(label) is int and label in (0, 1) for label in labels)
                and labels == summary['target_contract']['query_labels'] and sorted(labels) == [0, 1],
                'finite two-row logits and route-derived labels required')
    predictions = [0 if row[0] >= row[1] else 1 for row in logits]
    confusion = [[0, 0], [0, 0]]
    for label, prediction in zip(labels, predictions, strict=True):
        confusion[label][prediction] += 1
    score = sum((Fraction(confusion[index][index], sum(confusion[index])) for index in range(2)), Fraction()) / 2
    metrics = dict(query_logits=logits, query_targets=labels, query_predictions=predictions,
                   confusion_matrix=confusion, balanced_accuracy=[score.numerator, score.denominator], query_count=2,
                   correct_query_predictions=sum(label == prediction for label, prediction in zip(labels, predictions, strict=True)),
                   scientific_predictive_performance_qualified=False)
    fields(target, {name: metrics[name] for name in ('confusion_matrix', 'balanced_accuracy', 'query_count')})
    return adapted, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-pins', required=True)
    args = parser.parse_args()
    pins = origin.document(RUN / 'pins.json', args.expect_pins)
    fields(pins, dict(schema='cho51_provenance_numerical_worker_pins_v1', scientific_admission=False,
                      expected_numerical_budget=BUDGET, startup_ram_gib=4, active_ram_gib=4, disk_gib=20,
                      previous_startup_ram_gib=10, historical_10gib_startup_pass_claimed=False))
    counts(pins['expected_numerical_budget'], BUDGET, 'admitted numerical budget')
    origin.need(len(pins['reviewed_files']) == 13 and len(pins['runtime']) == 5 and len(pins['runtime_modules']) == 18
                and len(pins['supporting_runtime_sources']) == 4, 'exact13 source and5/18/4 runtime inventories required')
    verify_pins(pins, args.expect_pins)
    origin.need(not any(path.exists() for path in PAUSES), 'genuine peer pause is active at closeout')
    stages = origin.verify_origin_stages()
    contract = origin.document(RUN / 'origin-contract.json', pins['origin_contract_file_sha256'])
    same(contract, dict(schema='cho51_linear_worker_origin_contract_v1', **stages), 'fresh authenticated ancestor contract')
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'parent.py'),
               '--pins', str(RUN / 'pins.json'), '--expect-pins', args.expect_pins, '--output', str(OUT)]
    dispatch, dispatched = origin.document(RUN / 'dispatch_001.json'), origin.document(RUN / 'dispatch_result_001.json')
    for value in (dispatch, dispatched):
        fields(value, dict(pins_sha256=args.expect_pins, origin_contract_file_sha256=pins['origin_contract_file_sha256'],
                           child_command=command, expected_output=str(OUT), expected_numerical_budget=BUDGET,
                           actual_current_counter_ledger=None, scientific_admission=False))
    fields(dispatched, dict(guard_exit_code=0))
    native = verify_native(dispatched['native_directory'], command, pins)
    admission = origin.document(RUN / 'admission.json', dispatch['admission_sha256'])
    fields(admission, dict(schema='cho51_provenance_numerical_worker_admission_v1', pins_sha256=args.expect_pins,
                           source_review_sha256=pins['source_review_sha256'], accepted=True, scientific_admission=False,
                           max_job_seconds=600, process_mib=4096, job_mib=5120, startup_ram_gib=4, active_ram_gib=4, disk_gib=20,
                           owner_resource_amendment_path=pins['owner_resource_amendment_path'],
                           owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256']))
    peer_path = Path(admission['peer_release_path'])
    peer_release = origin.document(peer_path, admission['peer_release_sha256'])
    fields(peer_release, dict(schema='pro2_pro3_compute_release_v1', scope='cho51_provenance_numerical_worker_20261025_v3',
                              released=True, pins_sha256=args.expect_pins, maximum_jobs=1, max_job_seconds=600,
                              process_mib=4096, job_mib=5120, window_start_utc=admission['window_start_utc'],
                              window_end_utc=admission['window_end_utc']))
    utc = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    origin.need(utc(admission['window_start_utc']) <= utc(native['started_utc']) <= utc(native['completed_utc'])
                <= utc(admission['window_end_utc']), 'actual native Job outside explicit single-use peer window')
    for value in (dispatch, dispatched):
        fields(value, dict(admission_sha256=origin.digest(RUN / 'admission.json'), peer_release_path=str(peer_path),
                           peer_release_sha256=admission['peer_release_sha256'], window_start_utc=admission['window_start_utc'],
                           window_end_utc=admission['window_end_utc']))
    result, qualification = origin.document(OUT / 'result.json'), origin.document(OUT / 'qualification.json')
    fields(result, dict(schema='cho51_provenance_numerical_worker_result_v1', passed=True, tests_passed=True, pytest_exit=0,
                        collected_tests=pins['expected_tests'], expected_tests=pins['expected_tests'], skipped_reports=[],
                        backend_calls=1, verifier_calls=2, current_counter_ledger=BUDGET,
                        numerical_execution_status='completed_observed', measured_cells=0, scientific_admission=False,
                        current_executor_source=pins['expected_current_context'], current_fixture_source=pins['expected_fixture_context']))
    counts(result['current_counter_ledger'], BUDGET, 'actual aggregate ledger')
    route = result['worker_route_summary']
    expected_plans = [dict(dataset='cho2017', target_subject=f'subject_{number:02d}', method=method,
                           shots_per_class=5, model_seed=seed, repetition=1)
                      for number in range(2, 53) for method in ('labram_linear', 'labram_lora', 'labram_full', 'eegnet')
                      for seed in (11, 23, 37, 53, 71)]
    fields(route, dict(schema='cho51_actual_worker_input_route_v1', planned_cases=1020, available_catalogs=52,
                       available_labram_assets=52, evaluation_targets=[f'subject_{number:02d}' for number in range(2, 53)],
                       actual_worker_CasePlan_class='evaluation.phase2_runner.CasePlan',
                       actual_worker_TrialCatalog_class='evaluation.phase2_protocol.TrialCatalog',
                       owner_decision_sha256=pins['owner_decision_sha256'], legacy1040_sweep_or_collector_compatible=False,
                       scientific_execution_budget_admitted=False, experiment_freeze_signed=False, original_case_attempts_remaining=0))
    expected_case_ids = [hashlib.sha256(compact(plan).encode()).hexdigest() for plan in expected_plans]
    same(route['case_ids'], expected_case_ids, 'all1020 adopted case identities')
    origin.need(len(set(expected_case_ids)) == 1020 and type(route['method_configuration_sha256']) is dict
                and set(route['method_configuration_sha256']) == {'labram_linear', 'labram_lora', 'labram_full', 'eegnet'},
                'unique full adopted route and all four declared methods required')
    for value in route['method_configuration_sha256'].values():
        sha(value)
    origin.need(len(result['reports']) == pins['expected_tests'] and all(row['phase'] == 'call' and row['outcome'] == 'passed'
                for row in result['reports']), 'all focused test calls must pass')
    junit = bounded_bytes(OUT / 'junit.xml')
    origin.need(b'<!DOCTYPE' not in junit.upper() and b'<!ENTITY' not in junit.upper(), 'JUnit entities forbidden')
    suites = list(ET.fromstring(junit).iter('testsuite'))
    origin.need(sum(int(suite.attrib['tests']) for suite in suites) == pins['expected_tests'] and all(
        int(suite.attrib.get(name, '0')) == 0 for suite in suites for name in ('failures', 'errors', 'skipped')),
        'independent exact passing JUnit inventory required')
    fields(qualification, dict(schema='cho51_provenance_numerical_worker_qualification_v1', passed=True, result=result,
                              pins_sha256=args.expect_pins, canonical_files=432, canonical_source_sha256=origin.CANONICAL,
                              runtime_pins_rechecked=5, runtime_module_pins_rechecked=18, supporting_runtime_sources_rechecked=4,
                              unexpected_denials=0, torch_threads=1, torch_interop_threads=1, gpu_hidden=True,
                              current_counter_ledger=BUDGET, measured_cells=0, scientific_admission=False,
                              native_closeout_status='pending_external_post_job'))
    observer = qualification['independent_observer']
    calls = verify_observer(observer)
    same(observer, result['independent_observer'], 'runtime/result independent observer')
    same(calls, qualification['numerical_calls'], 'runtime numerical operation map')
    origin.need(type(qualification['lock_checks']) is int and qualification['lock_checks'] > 0, 'actual canonical lock checks required')
    expected_clones = {phase + '|' + pattern: 1 for phase in ('runner_owned_source', 'support_adapted_model')
                       for pattern in ('Batch chs npat spatch -> Batch () (chs npat) spatch', 'Batch C NA T -> Batch NA (T C)')}
    same(qualification['clone_reinitializations'], expected_clones, 'qualified clone budgets')
    same(qualification['empty_mask_containers'], dict(runner_owned_source=1, support_adapted_model=1), 'qualified empty-container budgets')
    origin.need(len(qualification['clone_reinitialization_details']) == 4, 'four parameterless clone observations required')
    source_fixture = str(ROOT / 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture')
    expected_loads = {str(Path(source_fixture) / 'data/processed/cho2017/profile_a/subject_02.npz'): 4,
                      str(Path(source_fixture) / 'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz'): 2}
    same(qualification['numpy_loads'], expected_loads, 'exact six target-only NPZ loads')
    request_path = Path(result['request_path'])
    request = canonical_document(request_path, result['request_sha256'])
    historical = request['historical_binding']
    workspace, fixture = request_path.parent, OUT / 'fixture'
    recorder = fixture / 'runs/phase2/lifecycle'
    plan = dict(dataset='cho2017', target_subject='subject_02', method='labram_linear', shots_per_class=5, model_seed=11, repetition=1)
    case_id = hashlib.sha256(compact(plan).encode()).hexdigest()
    claim_path = recorder / 'claims' / (case_id + '.attempt1.claim.json')
    origin.need(workspace == OUT / 'cases' / case_id and claim_path == Path(result['claim_path']), 'exact current workspace and claim required')
    factory_path = workspace / 'factory/request.json'
    inner = canonical_document(factory_path, result['factory_request_sha256'], newline=False)
    same(request['factory_request'], inner, 'outer/physical factory subrequest')
    fields(request, dict(schema='cho51_provenance_numerical_worker_request_v1', factory_request_sha256=result['factory_request_sha256'],
                         expected_numerical_budget=BUDGET, expected_observer_counts=OBSERVER,
                         engineering_only=True, scientific_admission=False, native_closeout_status='pending_external_post_job'))
    fields(inner, dict(schema='cho51_provenance_restore_request_v1', producer=pins['factory_producer'], executor=pins['factory_executor'], plan_json=compact(plan),
                       store_root=pins['store_root'], workspace=str(workspace / 'factory'), claim_path=str(claim_path),
                       claim_sha256=result['claim_sha256'], pins_path=str(RUN / 'pins.json'), pins_sha256=args.expect_pins,
                       method_config_sha256=pins['method_config_sha256'], protocol_config_sha256=stages['summary']['target_contract']['protocol_sha256'],
                       engineering_only=True, scientific_admission=False, maximum_weights_bytes=64 * 1024**2,
                       expected_counts=dict(source_updates=0, support_updates=0, query_calls=0, selected_restores=1, measured_cells=0)))
    counts(inner['expected_counts'], dict(source_updates=0, support_updates=0, query_calls=0, selected_restores=1, measured_cells=0),
           'factory-local admitted budget')
    fields(historical, dict(schema='cho51_linear_worker_request_v1', case_id=case_id, plan=plan, fixture_root=str(fixture),
                            recorder_root=str(recorder), workspace=str(workspace), pins_path=str(RUN / 'pins.json'),
                            independent_pins_sha256=args.expect_pins, execution_source_sha256=origin.CANONICAL,
                            owner_decision_sha256=pins['owner_decision_sha256'], origin_contract_path=str(RUN / 'origin-contract.json'),
                            origin_contract_file_sha256=pins['origin_contract_file_sha256'], claim_path=str(claim_path),
                            claim_file_sha256=result['claim_sha256'], attempt=1,
                            fixture_git_commit=pins['expected_fixture_context']['git_commit'],
                            fixture_git_dirty=pins['expected_fixture_context']['git_dirty'],
                            fixture_source_sha256=pins['expected_fixture_context']['source_sha256']))
    fields(historical, dict(target_source_state_sha256=pins['factory_producer']['model_state_sha256'],
                            target_profile_binding_sha256=hashlib.sha256(compact(stages['summary']['target_profile_binding']).encode()).hexdigest()))
    claim = canonical_document(claim_path, result['claim_sha256'])
    envelope(claim, dict(purpose='pilot_case_claim', case=plan, worker='cho51_provenance_numerical_worker_engineering_v2',
                         attempt=1, environment_sha256=historical['environment_sha256'],
                         source=pins['expected_fixture_context'], engineering_only=True))
    binding = dict(request_sha256=result['request_sha256'], factory_request_sha256=result['factory_request_sha256'],
                   claim_sha256=result['claim_sha256'], pins_sha256=args.expect_pins, workspace=str(workspace))
    execution_path = workspace / 'current-execution.json'
    execution = canonical_document(execution_path, result['current_execution_file_sha256'])
    payload = execution['payload']
    envelope(execution, payload)
    fields(payload, dict(schema='cho51_provenance_numerical_execution_v1', **binding, expected_numerical_budget=BUDGET,
                         current_counter_ledger=BUDGET, independent_observer=observer, source_fixture=source_fixture,
                         current_control_source=pins['expected_fixture_context'], current_executor_source=pins['expected_current_context'],
                         historical_source=stages['summary']['historical_source'], engineering_only=True, measured_cells=0,
                         scientific_admission=False, native_closeout_status='pending_external_post_job'))
    same(payload, result['current_execution'], 'physical/result current execution')
    counts(payload['current_counter_ledger'], BUDGET, 'physical aggregate ledger')
    counts(payload['expected_numerical_budget'], BUDGET, 'physical admitted aggregate budget')
    backend_path = workspace / 'backend-attempt.json'
    backend_marker = canonical_document(backend_path, payload['backend_attempt_file_sha256'])
    same(backend_marker, dict(schema='cho51_provenance_numerical_backend_attempt_v1', **binding,
                              engineering_only=True, scientific_admission=False), 'consumed backend marker')
    origin.need(set(payload['physical_outputs']) == {'restore-witness.json', 'target-witness.json'}, 'exact two physical witness outputs required')
    witnesses = {}
    for filename, embedded in (('restore-witness.json', 'restore_witness'), ('target-witness.json', 'target_route_witness')):
        entry = payload['physical_outputs'][filename]
        origin.need(type(entry) is dict and set(entry) == {'sha256', 'bytes'} and type(entry['bytes']) is int
                    and 0 < entry['bytes'] <= 8 * 1024**2, 'bounded physical witness declaration required')
        physical = canonical_document(workspace / filename, entry['sha256'])
        origin.need((workspace / filename).stat().st_size == entry['bytes'], 'declared physical witness size differs')
        same(physical, payload[embedded], 'embedded/physical witness')
        fields(physical, dict(current_worker_binding=binding))
        witnesses[filename] = physical
    target, restored = witnesses['target-witness.json'], witnesses['restore-witness.json']
    fields(restored, dict(schema='cho51_provenance_restored_source_v1', passed=True,
                          request_sha256=result['factory_request_sha256'], claim_sha256=result['claim_sha256'],
                          pins_sha256=args.expect_pins, workspace=str(workspace / 'factory'), store_root=pins['store_root'],
                          historical_source=json.loads(pins['factory_producer']['source_json']), current_executor_source=pins['expected_current_context'],
                          current_executor_runtime=json.loads(pins['factory_executor']['runtime_json']), complete_metadata_verified=True,
                          adapter_class='evaluation.phase2_pilot.LaBraMTunedAdapter', selected_restores=1, model_constructions=1,
                          safe_decodes=2, strict_state_loads=2, tensor_count=223, elements=5818138,
                          source_updates=0, support_updates=0, query_calls=0, measured_cells=0,
                          maximum_weights_bytes=64 * 1024**2, weights_bytes=23294624, engineering_only=True,
                          scientific_admission=False, native_closeout_status='pending_external_post_job'))
    producer = pins['factory_producer']
    for name, expected in dict(manifest_sha256=producer['manifest_sha256'], manifest_file_sha256=producer['manifest_file_sha256'],
                              complete_evidence_sha256=producer['evidence_sha256'], complete_evidence_file_sha256=producer['evidence_file_sha256'],
                              selection_contract_sha256=producer['selection_contract_sha256'], model_recipe_sha256=producer['model_recipe_sha256'],
                              model_state_sha256=producer['model_state_sha256'], weights_sha256=producer['weights_sha256'],
                              historical_publication_file_sha256=producer['publication_file_sha256']).items():
        same(restored[name], expected, 'authenticated historical factory binding ' + name)
    factory_marker_path = workspace / 'factory/restore-attempt.json'
    marker = canonical_document(factory_marker_path, restored['restore_attempt_sha256'])
    same(marker, dict(schema='cho51_provenance_restore_attempt_v1', request_sha256=result['factory_request_sha256'],
                      claim_sha256=result['claim_sha256'], pins_sha256=args.expect_pins, scientific_admission=False), 'consumed factory marker')
    adapted, metrics = verify_target(target, stages['summary'], historical, pins['expected_fixture_context'])
    same(metrics, result['current_target_metrics'], 'independently derived current query metrics')
    audit = dict(bytes=734579463, files=213, fixture_root=source_fixture,
                 input_identity_file_sha256='34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
    for value in (payload['input_audit_before'], payload['input_audit_after'], result['input_audit_before'], result['input_audit_after'], origin.verify_inputs()):
        same(value, audit, 'complete preserved213-input audit')
    proof = dict(request_sha256=result['request_sha256'], factory_request_sha256=result['factory_request_sha256'], case_id=case_id,
                 claim_sha256=result['claim_sha256'], pins_sha256=args.expect_pins,
                 execution_file_sha256=origin.digest(execution_path), target_witness_file_sha256=origin.digest(workspace / 'target-witness.json'),
                 restore_witness_file_sha256=origin.digest(workspace / 'restore-witness.json'),
                 factory_attempt_file_sha256=origin.digest(factory_marker_path), backend_attempt_file_sha256=origin.digest(backend_path),
                 adapted_state_sha256=adapted, metrics_json=compact(metrics), observed_counts_json=compact(BUDGET), observer_json=compact(observer),
                 verified_origin_files=len(stages['files']), native_closeout_status='pending_external_post_job',
                 engineering_only=True, scientific_admission=False, measured_cells=0)
    same(proof, result['proof'], 'independently reconstructed immutable proof')
    attestation_path = Path(result['attestation_path'])
    origin.need(attestation_path == workspace / 'parent-attestation.json', 'exact outer attestation path required')
    attestation = canonical_document(attestation_path, result['attestation_sha256'])
    same(attestation, dict(schema='cho51_provenance_numerical_attestation_v1', request_sha256=result['request_sha256'],
                           factory_request_sha256=result['factory_request_sha256'], case_id=case_id, proof=proof,
                           expected_numerical_budget=BUDGET, engineering_only=True, scientific_admission=False, measured_cells=0,
                           unchanged_canonical_worker_verified=False, full_worker_verified=False,
                           native_closeout_status='pending_external_post_job'), 'outer durable attestation')
    intent, success = recorder / 'engineering_intents' / (case_id + '.intent.json'), recorder / 'engineering_successes' / (case_id + '.success.json')
    for path, purpose in ((intent, 'pilot_case_engineering_success_intent'), (success, 'pilot_case_engineering_success')):
        envelope(canonical_document(path), dict(purpose=purpose, case=plan, attempt=1,
                                              attested_evidence_sha256=result['attestation_sha256'], engineering_only=True))
    origin.need(str(success) == result['engineering_receipt_path'] and origin.digest(success) == result['engineering_receipt_sha256']
                and set(recorder.rglob('*.json')) == {claim_path, intent, success}, 'one outer engineering terminal only required')
    fields(result['engineering_completion'], dict(engineering_success=1, failed=0, measured=0))
    for directory in ('cells', 'successes', 'publication_intents'):
        origin.need(not (recorder / directory).exists(), 'scientific publication forbidden')
    parent_binding = canonical_document(workspace / 'parent-binding.json')
    fields(parent_binding, dict(**binding, request_path=str(request_path), claim_path=str(claim_path)))
    fields(parent_binding['native'], dict(native_directory=native['native_directory'], job_name=native['job_name'], command=command,
                                          admission_path=str(Path(native['native_directory']) / 'admission.json'),
                                          admission_sha256=origin.digest(Path(native['native_directory']) / 'admission.json'), membership_verified=True,
                                          root_admission_sha256=origin.digest(RUN / 'admission.json'), peer_release_path=str(peer_path),
                                          peer_release_sha256=admission['peer_release_sha256'], peer_window_end_utc=admission['window_end_utc']))
    same(parent_binding['native'], result['native_binding'], 'request/result live native binding')
    same(parent_binding['native'], qualification['native_binding'], 'request/observer live native binding')
    configs = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
               'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')
    origin.need({path.relative_to(fixture).as_posix() for path in (fixture / 'configs').rglob('*') if path.is_file()} == set(configs)
                and not (fixture / 'data').exists() and not (fixture / '.git').exists(), 'isolated five-configuration fixture required')
    for name in configs:
        origin.need(origin.digest(fixture / name) == pins['files'][name], 'current isolated config changed')
    fingerprint = hashlib.sha256('\n'.join(f'{name}:{pins["files"][name]}' for name in sorted(configs)).encode()).hexdigest()
    origin.need(fingerprint == pins['expected_fixture_context']['source_sha256'], 'truthful isolated fixture fingerprint differs')
    for path, expected in qualification['observed_loaded_module_hashes'].items():
        origin.need(origin.digest(path) == expected, 'actual loaded module changed at external closeout')
    expected_probe = dict(event='socket.__new__', classification='blocked_optional_ipv6_import_probe',
                          source_file=str(ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'),
                          source_sha256=pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py'])
    origin.need(qualification['denied_operations'] in ([], [expected_probe]), 'unexpected guarded operation refusal')
    scoped_names = sorted(set([*stages['summary']['native_names'], native['job_name']]))
    for name in scoped_names:
        job_absent(name if name.startswith('pro3_migration_') else 'pro3_migration_' + name)
    origin.need(not ARCHIVE.exists(), 'fresh unused numerical evidence archive required')
    peer_copy = RUN / 'peer-release-authenticated.json'
    write_once(peer_copy, bounded_bytes(peer_path, expected=admission['peer_release_sha256']))
    sources = {ROOT / name for name in pins['reviewed_files']}
    sources.update(RUN / name for name in ('pins.json', 'source-review.json', 'native-runtime.json', 'origin-contract.json',
                                          'admission.json', 'dispatch_001.json', 'dispatch_result_001.json', 'owner-resource-amendment.json'))
    sources.add(peer_copy)
    sources.update(RUN.glob('preflight*.json'))
    sources.update(path for path in OUT.glob('*') if path.is_file() and path.suffix in {'.json', '.xml', '.log'})
    sources.update(path for path in workspace.rglob('*') if path.is_file())
    sources.update((claim_path, intent, success))
    sources.update(fixture / name for name in configs)
    sources.update(path for path in Path(native['native_directory']).iterdir() if path.is_file())
    origin.need(len(sources) <= 128, 'bounded128-artifact archive inventory required')
    rows, payloads, archive_bytes = [], [], 0
    forbidden = {'.npz', '.npy', '.mat', '.safetensors', '.pt', '.pth', '.ckpt', '.pkl', '.env'}
    for index, path in enumerate(sorted(sources), 1):
        origin.need(path.is_relative_to(ROOT) and path.suffix.lower() not in forbidden, 'metadata-only archive source required')
        raw = bounded_bytes(path)
        archive_bytes += len(raw)
        origin.need(archive_bytes <= 64 * 1024**2, 'complete metadata archive exceeds64MiB')
        relative = f'artifacts/a{index:04d}{path.suffix}'
        rows.append(dict(source=path.relative_to(ROOT).as_posix(), path=relative, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        payloads.append((relative, raw))
    verify_pins(pins, args.expect_pins)
    ARCHIVE.mkdir()
    (ARCHIVE / 'artifacts').mkdir()
    write_once(ARCHIVE / '.gitattributes', b'* -text\n')
    for relative, raw in payloads:
        write_once(ARCHIVE / relative, raw)
    write_once(ARCHIVE / 'manifest.json', origin.canonical(dict(schema='cho51_provenance_numerical_worker_archive_v1', artifacts=rows)))
    summary = dict(schema='cho51_provenance_numerical_worker_closeout_v1', passed=True, closed_utc=datetime.now(timezone.utc).isoformat(),
                   pins_sha256=args.expect_pins, source_review_sha256=pins['source_review_sha256'], origin_files=len(stages['files']),
                   original_inputs=213, original_input_bytes=734579463, canonical_sources=432, tests=pins['expected_tests'],
                   historical_source=stages['summary']['historical_source'], current_executor_source=pins['expected_current_context'],
                   current_fixture_source=pins['expected_fixture_context'], native=native, independent_observer=observer,
                   scoped_native_names_freshly_absent=len(scoped_names), engineering_successes=1, backend_calls=1, verifier_calls=2,
                   current_counter_ledger=BUDGET, factory_local_counts=dict(selected_restores=1, source_updates=0, support_updates=0, query_calls=0),
                   measured_cells=0, scientific_admission=False, experiment_freeze_signed=False, startup_ram_gib=4, active_ram_gib=4,
                   historical_10gib_startup_pass_claimed=False, owner_resource_amendment_sha256=pins['owner_resource_amendment_sha256'],
                   archive_artifacts=len(rows), archive_payload_bytes=archive_bytes, proof=proof, metrics=metrics,
                   peer_release=dict(original_path=str(peer_path), file_sha256=admission['peer_release_sha256'], authenticated_copy=peer_copy.relative_to(ROOT).as_posix()),
                   native_closeout_status='verified_external_post_job', child_native_flag_remains_pending=True)
    write_once(ARCHIVE / 'summary.json', origin.canonical(summary))
    write_once(ARCHIVE / 'README.md', ('# Provenance-aware numerical worker evidence\n\n'
               'One real parent/worker/factory transaction restores selected historical weights, performs one head support update '
               'and queries two synthetic trials under the same live CaseRecorder identity lock. One backend and two read-only '
               'verifier callbacks produce one outer engineering success and zero measured cells. Factory-local support/query '
               'counts stay zero; aggregate support/query counts are one. Fresh native closure is authenticated externally; '
               'the child pending-native flag remains unchanged. Arrays, weights and environment dumps are excluded. '
               'Independent final review and qualification documentation remain separate requirements.\n').encode())
    for row in rows:
        origin.need(origin.digest(ROOT / row['source']) == origin.digest(ARCHIVE / row['path']) == row['sha256'], 'archive exact byte pair changed')
    verify_pins(pins, args.expect_pins)
    job_absent(native['job_name'])
    write_once(RUN / 'closeout-result.json', origin.canonical(summary))
    print(json.dumps(dict(passed=True, archive=str(ARCHIVE), artifacts=len(rows), current_counter_ledger=BUDGET,
                          measured_cells=0, scientific_admission=False)), flush=True)


if __name__ == '__main__':
    main()





