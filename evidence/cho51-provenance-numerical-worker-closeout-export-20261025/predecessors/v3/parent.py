"""Guarded engineering parent over the full adopted route and actual factory backend."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from types import MappingProxyType

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime import CANONICAL, ROOT, RUN, Runtime, digest, identity, pause_check, read_json, write_json
import origin


class Results:
    def __init__(self):
        self.items, self.calls, self.skipped = 0, [], []

    def pytest_collection_finish(self, session):
        self.items = len(session.items)

    def pytest_runtest_setup(self, item):
        pause_check()

    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.skipped.append(dict(nodeid=report.nodeid, phase=report.when))
        if report.when == 'call' or report.failed:
            self.calls.append(dict(nodeid=report.nodeid, phase=report.when, outcome=report.outcome))


def copy_config(relative, fixture, pins):
    source = ROOT / relative
    before = identity(source)
    origin.need(before[-1] == pins['files'][relative] and 0 < before[2] <= 1024**2, 'bounded canonical config pin required')
    with source.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(before[2] + 1)
        finished = os.fstat(stream.fileno())
    key = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    origin.need(identity(source) == before and key(opened) == key(finished) and key(opened)[:4] == before[:4]
                and len(raw) == before[2] and hashlib.sha256(raw).hexdigest() == before[-1], 'canonical config changed during bounded copy')
    destination = fixture / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    origin.need(digest(destination) == before[-1], 'fresh configuration copy differs')


def build_route(fixture):
    from core.config import canonical_config_json, config_digest, load_toml
    from evaluation.phase2_runner import CasePlan
    from evaluation.phase2_protocol import TrialCatalog, source_selection, nested_episode
    from evaluation.phase2_profile_binding import CHO_CLASSES, ChoProfileAssets60Hz
    from evaluation.phase2_records import envelope
    from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute
    from docs.phase2.cho51_worker_bridge_v1.worker_bridge import from_verified_full_route
    _, source_fixture, _ = origin.original_inventory()
    manifest = origin.document(source_fixture / 'synthetic-input-identity.json',
                               '34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
    protocol = load_toml(fixture / 'configs/phase2/protocol.toml')
    threshold = load_toml(fixture / 'configs/benchmark.toml')['datasets']['cho2017']['artifact_threshold_volts']
    preprocessing = config_digest(dict(profile_identity=protocol['preparation']['profile_identity'],
                                      threshold_config_sha256=manifest['files']['configs/benchmark.toml']['sha256'],
                                      dataset='cho2017', threshold=threshold))
    trial_ids = tuple(json.dumps(['synthetic_session', 'synthetic_run', number], separators=(',', ':')) for number in range(42))
    catalogs, assets, selections, episodes = [], {}, {}, {}
    for number in range(1, 53):
        subject = f'subject_{number:02d}'
        first = f'data/processed/cho2017/profile_a/{subject}.npz'
        second = f'data/processed/cho2017/profile_b_60hz_v1/{subject}.npz'
        record = f'data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json'
        catalogs.append(TrialCatalog('cho2017', subject, trial_ids, CHO_CLASSES * 21, CHO_CLASSES,
                                     manifest['files'][first]['sha256'], preprocessing))
        assets[subject] = ChoProfileAssets60Hz(manifest['files'][second]['sha256'], manifest['files'][record]['sha256'],
                                             manifest['files']['configs/phase2/cho_profile_b_60hz.toml']['sha256'])
    catalogs = tuple(catalogs)
    for catalog in catalogs:
        selected = source_selection(catalogs, target=catalog.subject)
        episode = nested_episode(catalog, shots=(1, 5, 10, 20), protocol_sha256=config_digest(protocol))
        selections[catalog.subject] = canonical_config_json(envelope('source_selection', asdict(selected)))
        episodes[catalog.subject] = canonical_config_json(envelope('episode_manifest', episode.payload()))
        if catalog.subject == 'subject_02':
            origin.need(selected.sha256 == manifest['source_selection_sha256'], 'reconstructed synthetic selection differs')
    plans = tuple(CasePlan('cho2017', f'subject_{number:02d}', method, 5, seed, 1) for number in range(1, 53)
                  for method in ('labram_linear', 'labram_lora', 'labram_full', 'eegnet') for seed in (11, 23, 37, 53, 71))
    full = ChoFirstTrancheRoute(plans, catalogs, MappingProxyType(assets), canonical_config_json(protocol),
                               MappingProxyType(selections), MappingProxyType(episodes))
    return from_verified_full_route(ROOT, full)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--expect-pins', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    runtime = Runtime(args.pins, args.expect_pins, args.output)
    runtime.install_torch_guards()
    import pytest
    from core.config import config_digest, load_toml
    from core.provenance import capture_source
    from evaluation.phase2_runner import CasePlan, CaseRecorder, LockedCase, environment_digest
    from tools.migration.common import source_check
    from docs.phase2.cho51_provenance_numerical_worker_v2 import numerical_worker as Worker
    from docs.phase2.cho51_provenance_numerical_worker_v2.backend import FactoryNumericalBackend
    from docs.phase2.cho51_provenance_numerical_worker_v2.pipeline import run_parent_pipeline
    from docs.phase2.cho51_worker_bridge_v1.worker_bridge import route_summary
    pins, output = runtime.pins, args.output
    contract_path = RUN / 'origin-contract.json'
    expected_contract = read_json(contract_path, pins['origin_contract_file_sha256'])
    contract_identity = identity(contract_path)
    callbacks = dict(backend_calls=0, verifier_calls=0)
    result = dict(schema='cho51_provenance_numerical_worker_result_v1', passed=False,
                  tests_passed=False, backend_calls=0, verifier_calls=0,
                  current_counter_ledger={name: 0 for name in Worker.EXPECTED_BUDGET},
                  numerical_execution_status='not_started', engineering_only=True, measured_cells=0,
                  scientific_admission=False, original_case_attempts_remaining=0,
                  native_closeout_status='pending_external_post_job')

    def verify_origin(request=None):
        runtime.verify_pins()
        pause_check()
        origin.need(identity(contract_path) == contract_identity and source_check(ROOT) == CANONICAL,
                    'current source or historical origin identity changed')
        checked = origin.verify_origin_stages()
        origin.need(dict(schema='cho51_linear_worker_origin_contract_v1', **checked) == expected_contract,
                    'authenticated ancestor stages differ from fresh contract')
        if request is not None:
            historical = request.historical_binding
            origin.need(historical.origin_contract_path == contract_path
                        and historical.origin_contract_file_sha256 == pins['origin_contract_file_sha256'],
                        'actual worker uses another historical contract')
        return checked

    @contextmanager
    def execution_scope(request, request_path, request_sha256, live_method):
        Worker.validate_observer(runtime.observer_snapshot(), zero=True)
        origin.need(not runtime.active and type(getattr(live_method, '__self__', None)) is LockedCase
                    and getattr(live_method, '__func__', None) is LockedCase._require_active
                    and live_method.__self__.plan == request.plan, 'actual same-case live lock required for numerical scope')
        live_method()
        Worker._request_files(request)
        origin.need(request_path == request.workspace / 'request.json' and request_sha256 == request.sha256,
                    'exact current outer request required')
        verify_origin(request)
        runtime.locked, runtime.factory_request = live_method.__self__, request.factory_request
        runtime.request_identity, runtime.factory_request_identity = identity(request_path), identity(request.factory_request_path)
        runtime.claim_identity = identity(request.historical_binding.claim_path)
        runtime.binding = dict(Worker.build_current_binding(request), request_path=str(request_path),
                               claim_path=str(request.historical_binding.claim_path), native=runtime.native_binding)
        write_json(request.workspace / 'parent-binding.json', runtime.binding)
        runtime.active = True
        try:
            yield
        finally:
            runtime.active = False
            live_method()

    def input_audit():
        runtime.verify_pins()
        return origin.verify_inputs()

    def backend(request, request_path, request_sha256, live_method):
        callbacks['backend_calls'] += 1
        result.update(current_counter_ledger=None, numerical_execution_status='incomplete_unknown', **callbacks)
        origin.need(callbacks['backend_calls'] == 1, 'one backend invocation and no automatic replay required')
        verify_origin(request)
        return numerical_backend(request, request_path, request_sha256, live_method)

    def verifier(request, opaque):
        callbacks['verifier_calls'] += 1
        origin.need(callbacks['verifier_calls'] <= 2 and not runtime.active, 'two read-only verifier callbacks required')
        before = runtime.observer_snapshot()
        verify_origin(request)
        proof = Worker.verify_current_execution(request, opaque)
        origin.need(runtime.observer_snapshot() == before, 'physical verifier performed fresh numerical work')
        return proof

    try:
        verify_origin()
        before_inputs = origin.verify_inputs()
        reports = Results()
        os.chdir(output)
        pytest_exit = pytest.main(['-q', '-s', '--maxfail=1', '-p', 'no:cacheprovider', '-o', 'addopts=',
                                  '--import-mode=importlib', '--log-file', str(output / 'pytest.log'),
                                  '--basetemp', str(output / 't'), '--junitxml', str(output / 'junit.xml'),
                                  *[str(ROOT / node) for node in pins['test_nodes']]], plugins=[reports])
        tests_passed = (pytest_exit == 0 and reports.items == len(reports.calls) == pins['expected_tests']
                        and not reports.skipped and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in reports.calls))
        result.update(tests_passed=tests_passed, pytest_exit=int(pytest_exit), collected_tests=reports.items,
                      expected_tests=pins['expected_tests'], reports=reports.calls, skipped_reports=reports.skipped)
        origin.need(tests_passed, 'all exact focused metadata cases must pass before numerical backend')
        Worker.validate_observer(runtime.observer_snapshot(), zero=True)
        fixture = output / 'fixture'
        fixture.mkdir()
        configurations = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
                          'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')
        for name in configurations:
            copy_config(name, fixture, pins)
        route = build_route(fixture)
        recorder_root = fixture / 'runs/phase2/lifecycle'
        recorder = CaseRecorder(fixture, output_root=recorder_root)
        fixture_source = capture_source(fixture)
        origin.need(asdict(fixture_source) == pins['expected_fixture_context']
                    and asdict(capture_source(ROOT)) == pins['expected_current_context'], 'actual current source roles differ')
        context = Worker.WorkerRoute.WorkerContext(output, fixture, recorder_root, args.pins, args.expect_pins, CANONICAL,
                    pins['owner_decision_sha256'], route.plans, fixture_source, environment_digest())
        plan = CasePlan('cho2017', 'subject_02', 'labram_linear', 5, 11, 1)
        workspace = output / 'cases' / plan.case_id
        (output / 'cases').mkdir()
        protocol = load_toml(fixture / 'configs/phase2/protocol.toml')
        method = origin.document(Path(pins['method_config_path']), pins['method_config_file_sha256'])
        origin.need(config_digest(method) == pins['method_config_sha256'], 'admitted method settings differ')
        template = Worker.Factory.RestoreRequest(Worker.Factory.HistoricalProducer(**pins['factory_producer']),
                    Worker.Factory.ExecutorContext(**pins['factory_executor']), Worker.Factory.canonical(asdict(plan)),
                    pins['store_root'], str(workspace / 'factory'),
                    str(recorder_root / 'claims' / (plan.case_id + '.attempt1.claim.json')), '0' * 64,
                    str(args.pins), args.expect_pins, config_digest(method), config_digest(protocol))
        _, source_fixture, _ = origin.original_inventory()
        numerical_backend = FactoryNumericalBackend(route=route, source_fixture=source_fixture,
                            method_config=method, protocol_config=protocol, input_audit=input_audit,
                            observer_snapshot=runtime.observer_snapshot, execution_scope=execution_scope)
        completion = run_parent_pipeline(recorder, plan, context=context, route=route, workspace=workspace,
                        origin_contract_path=contract_path, origin_contract_file_sha256=pins['origin_contract_file_sha256'],
                        factory_template=template, backend=backend, verifier=verifier)
        origin.need(callbacks == dict(backend_calls=1, verifier_calls=2), 'backend once and verifiers twice required')
        after_inputs = origin.verify_inputs()
        verify_origin(completion.request)
        origin.need(before_inputs == after_inputs and capture_source(fixture) == fixture_source,
                    'original213 inputs or current fixture source changed')
        proof = asdict(completion.proof)
        execution = read_json(workspace / 'current-execution.json', completion.proof.execution_file_sha256)['payload']
        Worker.validate_observer(runtime.observer_snapshot())
        origin.need(execution['independent_observer'] == runtime.observer_snapshot(), 'physical execution and runtime observer differ')
        result.update(passed=True, current_counter_ledger=dict(Worker.EXPECTED_BUDGET),
                      numerical_execution_status='completed_observed', independent_observer=runtime.observer_snapshot(),
                      current_execution=execution, current_execution_file_sha256=completion.proof.execution_file_sha256,
                      proof=proof, request_path=str(completion.request_path), request_sha256=completion.request.sha256,
                      factory_request_path=str(completion.request.factory_request_path),
                      factory_request_sha256=completion.request.factory_request.sha256,
                      claim_path=str(completion.request.historical_binding.claim_path), claim_sha256=completion.proof.claim_sha256,
                      attestation_path=str(completion.attestation_path), attestation_sha256=completion.attestation_file_sha256,
                      engineering_receipt_path=str(completion.engineering_receipt), engineering_receipt_sha256=digest(completion.engineering_receipt),
                      engineering_completion=recorder.completion((plan,)), input_audit_before=before_inputs, input_audit_after=after_inputs,
                      historical_source=expected_contract['summary']['historical_source'],
                      current_executor_source=pins['expected_current_context'], current_fixture_source=pins['expected_fixture_context'],
                      worker_route_summary=route_summary(route), current_target_metrics=json.loads(completion.proof.metrics_json),
                      native_binding=runtime.native_binding, origin_files=len(expected_contract['files']), **callbacks)
    except BaseException as error:
        result.update(failure=dict(type=type(error).__name__, message=str(error)[:2000]), **callbacks)
        write_json(output / 'result.json', result)
        raise
    write_json(output / 'result.json', result)
    runtime.finish(result)
    print(json.dumps(dict(passed=True, current_counter_ledger=result['current_counter_ledger'],
                          measured_cells=0, scientific_admission=False)), flush=True)


if __name__ == '__main__':
    main()


