"""Focused rejections followed by one real locked factory restoration."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime import CANONICAL, ROOT, RUN, Runtime, digest, identity, pause_check, read_json, write_json
import origin


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


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


def copied_config(relative, fixture, pins):
    source = ROOT / relative
    before = identity(source)
    origin.need(before[-1] == pins['files'][relative] and 0 < before[2] <= 1024**2, 'bounded canonical config pin required')
    with source.open('rb') as stream:
        raw = stream.read(before[2] + 1)
    origin.need(identity(source) == before and len(raw) == before[2] and hashlib.sha256(raw).hexdigest() == before[-1],
                'configuration changed during fixed-bound copy')
    destination = fixture / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    origin.need(digest(destination) == before[-1], 'fresh configuration copy differs')


def route_inputs(protocol):
    from core.config import config_digest, load_toml
    from evaluation.phase2_protocol import TrialCatalog, source_selection
    from evaluation.phase2_profile_binding import CHO_CLASSES, ChoProfileAssets60Hz
    _, fixture, _ = origin.original_inventory()
    manifest = origin.document(fixture / 'synthetic-input-identity.json',
                               '34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
    threshold = load_toml(ROOT / 'configs/benchmark.toml')['datasets']['cho2017']['artifact_threshold_volts']
    preprocessing = config_digest(dict(profile_identity=protocol['preparation']['profile_identity'],
                                      threshold_config_sha256=manifest['files']['configs/benchmark.toml']['sha256'],
                                      dataset='cho2017', threshold=threshold))
    trial_ids = tuple(json.dumps(['synthetic_session', 'synthetic_run', number], separators=(',', ':')) for number in range(42))
    catalogs, assets = [], {}
    for number in range(1, 53):
        subject = f'subject_{number:02d}'
        first = f'data/processed/cho2017/profile_a/{subject}.npz'
        second = f'data/processed/cho2017/profile_b_60hz_v1/{subject}.npz'
        record = f'data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json'
        catalogs.append(TrialCatalog('cho2017', subject, trial_ids, CHO_CLASSES * 21, CHO_CLASSES,
                                     manifest['files'][first]['sha256'], preprocessing))
        assets[subject] = ChoProfileAssets60Hz(manifest['files'][second]['sha256'], manifest['files'][record]['sha256'],
                                             manifest['files']['configs/phase2/cho_profile_b_60hz.toml']['sha256'])
    from evaluation.phase2_records import envelope
    selection = source_selection(tuple(catalogs), target='subject_02')
    origin.need(selection.sha256 == manifest['source_selection_sha256'], 'reconstructed source selection identity differs')
    return tuple(catalogs), envelope('source_selection', asdict(selection)), assets


def locked_restore(runtime, request, request_path, locked, *, method, protocol, catalogs, selection, assets):
    from docs.phase2.cho51_provenance_restore_v1.factory import ProvenanceRestoreFactory
    runtime.locked = locked
    runtime.binding = dict(request_path=str(request_path), request_sha256=request.sha256,
                           claim_path=request.claim_path, claim_sha256=request.claim_sha256,
                           pins_sha256=request.pins_sha256, workspace=request.workspace,
                           native=runtime.native_binding)
    runtime.request_identity = identity(request_path)
    runtime.claim_identity = identity(request.claim_path)
    write_json(Path(request.workspace) / 'parent-binding.json', runtime.binding)
    factory = ProvenanceRestoreFactory(request, request_path, request.sha256, locked._require_active)
    factory.authenticate()
    origin.need(runtime.calls == {}, 'numerical calls preceded explicit factory restoration')
    runtime.verify_pins()
    runtime.active = True
    try:
        restored = factory.restore(method_config=method, protocol_config=protocol, catalogs=catalogs,
                                   selection_record=selection, assets=assets)
    finally:
        runtime.active = False
    from evaluation.phase2_pilot import LaBraMTunedAdapter
    from encoder.labram import LaBraMClassifier
    from evaluation.labram_parity import state_digest
    origin.need(type(restored.adapter) is LaBraMTunedAdapter and type(restored.model) is LaBraMClassifier
                and restored.adapter._model is restored.model
                and state_digest(restored.model) == request.producer.model_state_sha256,
                'actual genuine canonical adapter and restored model must be delivered')
    runtime.verify_pins()
    locked._require_active()
    witness_path = Path(request.workspace) / 'restore-witness.json'
    witness_sha = write_json(witness_path, restored.witness)
    before = dict(runtime.calls)
    for _ in range(2):
        locked._require_active()
        origin.need(identity(request_path) == runtime.request_identity and identity(request.claim_path) == runtime.claim_identity
                    and digest(runtime.pins_path) == runtime.pins_sha256, 'current locked proof identity changed')
        physical = read_json(witness_path, witness_sha)
        expected = dict(request_sha256=request.sha256, claim_sha256=request.claim_sha256,
                        pins_sha256=request.pins_sha256, workspace=request.workspace,
                        historical_source=json.loads(request.producer.source_json),
                        current_executor_source=json.loads(request.executor.source_json),
                        selected_restores=1, model_constructions=1, safe_decodes=2, strict_state_loads=2,
                        source_updates=0, support_updates=0, query_calls=0, measured_cells=0,
                        engineering_only=True, scientific_admission=False, native_closeout_status='pending_external_post_job')
        origin.need(physical == restored.witness and all(type(physical.get(name)) is type(value) and physical[name] == value
                    for name, value in expected.items()) and runtime.calls == before,
                    'independent metadata verification differs or performed numerical work')
    attestation = dict(schema='cho51_provenance_restore_attestation_v1', request_sha256=request.sha256,
                       claim_sha256=request.claim_sha256, pins_sha256=request.pins_sha256,
                       restore_witness_sha256=witness_sha, parent_binding_sha256=digest(Path(request.workspace) / 'parent-binding.json'),
                       backend_calls=1, verifier_calls=2, observed_numerical_calls=dict(runtime.calls),
                       current_counts=dict(selected_restores=1, source_updates=0, support_updates=0, gradient_updates=0,
                                           query_calls=0, measured_cells=0),
                       native_closeout_status='pending_external_post_job', engineering_only=True, scientific_admission=False)
    attestation_path = Path(request.workspace) / 'parent-attestation.json'
    attestation_sha = write_json(attestation_path, attestation)
    receipt = locked.record_engineering_success(attempt=1, attested_evidence_sha256=attestation_sha)
    locked._require_active()
    return dict(witness=restored.witness, restore_witness_path=str(witness_path), restore_witness_sha256=witness_sha,
                attestation_path=str(attestation_path), attestation_sha256=attestation_sha,
                engineering_receipt_path=str(receipt), engineering_receipt_sha256=digest(receipt), backend_calls=1, verifier_calls=2)


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
    from evaluation.phase2_runner import CasePlan, CaseRecorder
    from docs.phase2.cho51_provenance_restore_v1.factory import ExecutorContext, HistoricalProducer, RestoreRequest
    from tools.migration.common import source_check
    pins, output = runtime.pins, args.output
    result = dict(schema='cho51_provenance_restore_result_v1', passed=False, engineering_only=True,
                  current_restore_count=0, current_source_updates=0, current_support_updates=0,
                  current_gradient_updates=0, target_inference_calls=0, measured_cells=0,
                  scientific_admission=False, original_case_attempts_remaining=0,
                  backend_calls=0, verifier_calls=0, native_closeout_status='pending_external_post_job')
    try:
        origin.need(source_check(ROOT) == CANONICAL, 'canonical source differs before validation')
        before_origin = origin.verify_origin_stages()
        origin.need(dict(schema='cho51_provenance_restore_origin_v1', **before_origin) == runtime.contract,
                    'fresh historical contract differs before validation')
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
        origin.need(tests_passed, 'all exact focused metadata rejection tests must pass before factory execution')
        origin.need(runtime.calls == {} and runtime.model_constructions == 0, 'metadata tests performed numerical work')
        fixture = output / 'fixture'
        fixture.mkdir()
        for name in ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
                     'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml'):
            copied_config(name, fixture, pins)
        origin.need(asdict(capture_source(ROOT)) == pins['expected_current_context']
                    and asdict(capture_source(fixture)) == pins['expected_fixture_context'], 'actual current executor or recorder source differs')
        protocol = load_toml(fixture / 'configs/phase2/protocol.toml')
        method = origin.document(Path(pins['method_config_path']), pins['method_config_file_sha256'])
        origin.need(config_digest(method) == pins['method_config_sha256'], 'actual method configuration differs')
        catalogs, selection, assets = route_inputs(protocol)
        plan = CasePlan('cho2017', 'subject_02', 'labram_linear', 5, 11, 1)
        recorder = CaseRecorder(fixture, output_root=fixture / 'runs/phase2/lifecycle')
        workspace = output / 'cases' / plan.case_id
        workspace.mkdir(parents=True)
        with recorder.case_session(plan) as locked:
            claim = locked.claim_new(worker='cho51_provenance_restore_engineering_v1', attempt=1)
            request = RestoreRequest(HistoricalProducer(**pins['factory_producer']), ExecutorContext(**pins['factory_executor']),
                                     compact(asdict(plan)), pins['store_root'], str(workspace), str(claim), digest(claim),
                                     str(args.pins), args.expect_pins, config_digest(method), config_digest(protocol))
            request_path = workspace / 'request.json'
            raw = compact(request.payload()).encode()
            with request_path.open('xb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            origin.need(digest(request_path) == request.sha256, 'durable canonical request digest differs')
            result.update(current_restore_count=None, restoration_attempted=True,
                          request_path=str(request_path), request_sha256=request.sha256,
                          claim_path=str(claim), claim_sha256=digest(claim))
            completed = locked_restore(runtime, request, request_path, locked, method=method, protocol=protocol,
                                       catalogs=catalogs, selection=selection, assets=assets)
            result.update(completed, current_restore_count=1)
        after_inputs = origin.verify_inputs()
        after_origin = origin.verify_origin_stages()
        origin.need(before_inputs == after_inputs and before_origin == after_origin
                    and source_check(ROOT) == CANONICAL, 'original inputs, historical evidence or canonical sources changed')
        origin.need(asdict(capture_source(ROOT)) == pins['expected_current_context']
                    and asdict(capture_source(fixture)) == pins['expected_fixture_context'], 'current source changed at adapter release')
        completion = recorder.completion((plan,))
        origin.need(completion['engineering_success'] == 1 and completion['measured'] == completion['failed'] == 0,
                    'one engineering success and zero measured cases required')
        result.update(passed=True, engineering_completion=completion,
                      input_audit_before=before_inputs, input_audit_after=after_inputs,
                      origin_files=len(before_origin['files']), native_binding=runtime.native_binding,
                      actual_executor_source=pins['expected_current_context'], actual_recorder_source=pins['expected_fixture_context'],
                      historical_source=before_origin['summary']['historical_source'])
    except BaseException as error:
        result['failure'] = dict(type=type(error).__name__, message=str(error)[:2000])
        write_json(output / 'result.json', result)
        raise
    write_json(output / 'result.json', result)
    runtime.finish(result)
    print(json.dumps(dict(passed=True, selected_restores=1, source_updates=0, support_updates=0,
                          query_calls=0, measured_cells=0, scientific_admission=False)), flush=True)


if __name__ == '__main__':
    main()
