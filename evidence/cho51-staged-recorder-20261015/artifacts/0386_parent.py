"""Fresh locked recorder integration of immutable completed source and restore stages."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime import CANONICAL, ROOT, RUN, Runtime, digest, identity, pause_check, read_json, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins', type=Path, required=True)
parser.add_argument('--expect-pins', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
runtime = Runtime('parent', args.pins, args.expect_pins, args.output)
runtime.install_torch_guards()
from evaluation.phase2_runner import CasePlan, CaseRecorder, environment_digest
from evaluation.phase2_cho_case_inputs import SELECTED_SEEDS
from core.provenance import capture_source
from docs.phase2.cho51_staged_recorder_v1.transaction import WorkerContext, VerifiedStagedProof, run_staged_case, _origin_assets
import origin
import pytest

OUT = args.output
pins = runtime.pins
original_recorder = CaseRecorder.__init__


def isolated_recorder(self, root, *, output_root=None):
    if (not Path(root).resolve().is_relative_to(OUT) or output_root is None
            or not Path(output_root).resolve().is_relative_to(OUT)):
        runtime.refuse('shared_recorder_constructor', root)
    original_recorder(self, root, output_root=output_root)


CaseRecorder.__init__ = isolated_recorder


class Results:
    def __init__(self):
        self.items, self.calls, self.skipped = 0, [], []
    def pytest_collection_finish(self, session):
        self.items = len(session.items)
    def pytest_runtest_setup(self, item):
        pause_check()
    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.skipped.append({'nodeid': report.nodeid, 'phase': report.when})
        if report.when == 'call' or report.failed:
            self.calls.append({'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome})


reports = Results()
os.chdir(OUT)
pytest_exit = pytest.main(['-q', '-s', '-p', 'no:cacheprovider', '-o', 'addopts=',
    '--import-mode=importlib', '--log-file', str(OUT / 'pytest.log'), '--basetemp', str(OUT / 't'),
    '--junitxml', str(OUT / 'junit.xml'), *[str(ROOT / node) for node in pins['test_nodes']]], plugins=[reports])
tests_passed = (pytest_exit == 0 and reports.items == pins['expected_tests']
    and len(reports.calls) == pins['expected_tests'] and not reports.skipped
    and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in reports.calls))

CONTRACT = RUN / 'origin-contract.json'
CONTRACT_SHA = pins['origin_contract_file_sha256']
expected_origin = read_json(CONTRACT)
origin_contract_identity = identity(CONTRACT)
callback_counts = {'backend_calls': 0, 'verifier_calls': 0}
verified_origin_identities = None


def verify_origin(request):
    global verified_origin_identities
    runtime.verify_pins()
    pause_check()
    if (request.origin_contract_path != CONTRACT or request.origin_contract_file_sha256 != CONTRACT_SHA
            or digest(CONTRACT) != CONTRACT_SHA or identity(CONTRACT) != origin_contract_identity):
        raise ValueError('fresh request must bind the independent immutable origin contract')
    current = origin.verify_origin_stages()
    if dict(schema='cho51_staged_recorder_origin_contract_v1', **current) != expected_origin:
        raise ValueError('current independent metadata proof differs from exact pinned origin contract')
    checked_contract, physical = _origin_assets(request)
    if checked_contract != expected_origin:
        raise ValueError('origin proof physical byte identities changed')
    if verified_origin_identities is not None and physical != verified_origin_identities:
        raise ValueError('origin physical proof changed between locked callback verifications')
    verified_origin_identities = physical
    runtime.verify_pins()
    pause_check()
    return current


def backend(request, request_path, request_sha256):
    callback_counts['backend_calls'] += 1
    if (callback_counts['backend_calls'] != 1 or request_path != request.workspace / 'request.json'
            or request_sha256 != request.sha256 or digest(request_path) != request_sha256):
        raise ValueError('exact fresh once-only staged backend request required')
    return verify_origin(request)


def verifier(request, opaque):
    callback_counts['verifier_calls'] += 1
    if callback_counts['verifier_calls'] > 2:
        raise ValueError('exactly two locked independent staged proof checks required')
    current = verify_origin(request)
    if opaque != current:
        raise ValueError('staged backend metadata differs from independent locked verification')
    summary = current['summary']
    return VerifiedStagedProof(request_sha256=request.sha256, case_id=request.plan.case_id,
        claim_file_sha256=request.claim_file_sha256, execution_source_sha256=CANONICAL,
        independent_pins_sha256=args.expect_pins, owner_decision_sha256=request.owner_decision_sha256,
        environment_sha256=request.environment_sha256, origin_contract_file_sha256=CONTRACT_SHA,
        verified_origin_files=len(current['files']), selected_state_sha256=summary['selected_state_sha256'],
        weights_file_sha256=summary['weights_file_sha256'])


def copy_config(relative, fixture):
    source = ROOT / relative
    expected_sha = pins['files'][relative]
    before = source.stat()
    if (source.resolve(strict=True) != source or source.is_symlink() or not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1 or not 0 < before.st_size <= 1048576):
        raise ValueError('direct bounded pinned canonical configuration required')
    with source.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(1048577)
        finished = os.fstat(stream.fileno())
    after = source.stat()
    key = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if (key(before) != key(after) or key(opened) != key(finished) or key(before)[:4] != key(opened)[:4]
            or len(raw) != before.st_size or hashlib.sha256(raw).hexdigest() != expected_sha):
        raise ValueError('canonical configuration changed during bounded byte copy')
    destination = fixture / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if digest(source) != expected_sha or digest(destination) != expected_sha:
        raise ValueError('fresh configuration copy differs from pinned source bytes')


result = {'schema': 'cho51_staged_recorder_result_v1', 'passed': False,
    'tests_passed': tests_passed, 'pytest_exit': int(pytest_exit),
    'collected_tests': reports.items, 'expected_tests': pins['expected_tests'],
    'reports': reports.calls, 'skipped_reports': reports.skipped,
    'backend_calls': 0, 'verifier_calls': 0, 'engineering_completion': None,
    'source_work_reused': True, 'restore_work_reused': True,
    'source_training_replayed': False, 'current_gradient_updates': 0, 'historical_gradient_updates': 5253,
    'origin_parent_transaction_qualified': False, 'measured_cells': 0,
    'scientific_admission': False, 'original_case_attempts_remaining': 0}
if tests_passed:
    runtime.verify_pins()
    fixture = OUT / 'fixture'
    fixture.mkdir(exist_ok=False)
    config_paths = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
        'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')
    for relative in config_paths:
        copy_config(relative, fixture)
    if {path.relative_to(fixture).as_posix() for path in fixture.rglob('*') if path.is_file()} != set(config_paths):
        raise ValueError('fresh recorder fixture must contain only five canonical configuration files')
    recorder_root = fixture / 'runs/phase2/lifecycle'
    recorder = CaseRecorder(fixture, output_root=recorder_root)
    plans = tuple(CasePlan('cho2017', f'subject_{subject:02d}', method, 5, seed, 1)
        for subject in range(2, 53) for method in ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
        for seed in SELECTED_SEEDS)
    context = WorkerContext(OUT, fixture, recorder_root, args.pins, args.expect_pins,
        CANONICAL, pins['owner_decision_sha256'], plans, capture_source(fixture), environment_digest())
    plan = CasePlan('cho2017', 'subject_02', 'eegnet', 5, 11, 1)
    (OUT / 'cases').mkdir()
    completion = run_staged_case(recorder, plan, context=context, workspace=OUT / 'cases' / plan.case_id,
        origin_contract_path=CONTRACT, origin_contract_file_sha256=CONTRACT_SHA,
        backend=backend, verifier=verifier)
    if callback_counts != {'backend_calls': 1, 'verifier_calls': 2}:
        raise ValueError('fresh transaction must call backend once and independent verifier twice')
    proof = {key: str(value) if isinstance(value, Path) else value for key, value in asdict(completion.proof).items()}
    result.update(passed=True, engineering_completion=recorder.completion((plan,)),
        request_path=str(completion.request_path), request_sha256=completion.request.sha256,
        claim_path=str(completion.request.claim_path), claim_file_sha256=completion.request.claim_file_sha256,
        attestation_path=str(completion.attestation_path), attestation_file_sha256=completion.attestation_file_sha256,
        engineering_receipt=str(completion.engineering_receipt),
        engineering_receipt_file_sha256=digest(completion.engineering_receipt), proof=proof,
        origin_contract_file_sha256=CONTRACT_SHA, origin_compact_files=len(expected_origin['files']),
        **callback_counts)
write_json(OUT / 'result.json', result)
runtime.finish(result)
print(json.dumps({'passed': result['passed'], 'engineering_only': True, 'scientific_admission': False}), flush=True)
raise SystemExit(0 if result['passed'] else 1)
