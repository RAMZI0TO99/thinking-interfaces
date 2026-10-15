"""One guarded zero-training source publication or detached restoration stage."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime import ROOT, RUN, Runtime, read_json, write_json, pause_check

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mode', choices=('publication', 'restoration'), required=True)
parser.add_argument('--pins', type=Path, required=True)
parser.add_argument('--expect-pins', required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--publication-result', type=Path)
parser.add_argument('--expect-publication-result')
args = parser.parse_args()
if ((args.mode == 'restoration' and (args.publication_result is None or args.expect_publication_result is None))
        or (args.mode == 'publication' and (args.publication_result is not None or args.expect_publication_result is not None))):
    parser.error('restoration requires the exact independently pinned publication result')
runtime = Runtime(args.mode, args.pins, args.expect_pins, args.output,
    publication_result=None if args.mode == 'publication' else (args.publication_result, args.expect_publication_result))
runtime.install_torch_guards()
import metadata
from docs.phase2.cho51_linear_publication_v1.contract import validate_stage_contract

OUT, pins = args.output, runtime.pins
os.chdir(OUT)
origin = read_json(RUN / 'origin-contract.json')
contract = read_json(RUN / 'stage-contract.json')
validate_stage_contract(contract)
metadata.verify_stage_contract(contract, origin, ROOT)
reports, subreports, skipped, unexpected = [], [], [], []
collected, pytest_exit = 0, None
tests_executed = args.mode == 'publication'
if tests_executed:
    import pytest
    from _pytest.reports import TestReport
    from _pytest.subtests import SubtestReport
    class Results:
        def pytest_collection_finish(self, session):
            global collected
            collected = len(session.items)
        def pytest_runtest_setup(self, item):
            pause_check()
        def pytest_runtest_logreport(self, report):
            row = {'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome}
            if report.skipped:
                skipped.append(row)
            if type(report) is SubtestReport:
                subreports.append(row)
            elif type(report) is TestReport:
                if report.when == 'call' or report.failed:
                    reports.append(row)
            else:
                unexpected.append(row)
    pytest_exit = int(pytest.main(['-q', '-s', '-p', 'no:cacheprovider', '-o', 'addopts=',
        '--import-mode=importlib', '--log-file', str(OUT / 'pytest.log'), '--basetemp', str(OUT / 't'),
        '--junitxml', str(OUT / 'junit.xml'), *[str(ROOT / node) for node in pins['test_nodes']]], plugins=[Results()]))
    tests_passed = (pytest_exit == 0 and collected == 20 and len(reports) == 20
        and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in reports)
        and not subreports and not skipped and not unexpected and runtime.numerical_calls == {})
else:
    metadata.verify_publication_proof(pins, args.expect_publication_result, root=ROOT)
    receipt = read_json(RUN / 'publication_001/stage-receipt.json')
    if receipt.get('publication_result_file_sha256') != args.expect_publication_result or receipt.get('passed') is not True:
        raise ValueError('accepted publication stage receipt required before detached restoration')
    tests_passed = runtime.numerical_calls == {}

result = {'schema': 'cho51_linear_' + args.mode + '_child_result_v1', 'passed': False,
    'mode': args.mode, 'tests_executed': tests_executed, 'tests_reused': not tests_executed,
    'tests_reused_from_publication_result_sha256': args.expect_publication_result,
    'tests_passed': tests_passed, 'pytest_exit': pytest_exit, 'expected_tests': 20,
    'collected_tests': collected, 'expected_subtests': 0, 'collected_subtests': len(subreports),
    'reports': reports, 'subtest_reports': subreports, 'skipped_reports': skipped,
    'unexpected_reports': unexpected, 'bridge_result': None, 'actual_gradient_updates': 0,
    'pretrained_baseline_loaded': False, 'cohort_lineage_verified': False,
    'scientific_admission': False, 'original_case_attempts_remaining': 0}
if tests_passed:
    runtime.verify_pins()
    from docs.phase2.cho51_linear_publication_v1.bridge import publish_source, verify_publication
    runtime.active = True
    try:
        if args.mode == 'publication':
            value = publish_source(OUT, contract, set_protected_inputs=runtime.set_protected_inputs)
        else:
            value = verify_publication(OUT, contract, runtime.publication_result,
                expected_publication_result_sha256=args.expect_publication_result,
                set_protected_inputs=runtime.set_protected_inputs)
    finally:
        runtime.active = False
    expected = {'passed': True, 'actual_gradient_updates': 0, 'current_gradient_updates': 0,
        'source_gradient_updates': 0, 'support_gradient_updates': 0, 'full_worker_verified': False,
        'recorder_used': False, 'measured_cells': 0, 'scientific_admission': False}
    calls = runtime.numerical_calls
    load_count, strict_count, save_count = (3, 2, 1) if tests_executed else (4, 4, 0)
    if (any(type(value.get(key)) is not type(expected_value) or value[key] != expected_value
            for key, expected_value in expected.items())
            or calls.get('safetensors_load') != load_count
            or calls.get('module_load_state_dict') != strict_count
            or calls.get('module_strict_load') != strict_count
            or calls.get('safetensors_save', 0) != save_count
            or [row['enabled'] for row in runtime.protection_transitions] != [True, False]):
        raise ValueError('exact zero-training staged publication/restoration work required')
    result.update(passed=True, bridge_result=value, pretrained_baseline_loaded=True)
write_json(OUT / 'result.json', result)
runtime.finish(result)
print(json.dumps({'passed': result['passed'], 'mode': args.mode, 'actual_gradient_updates': 0,
    'scientific_admission': False}), flush=True)
raise SystemExit(0 if result['passed'] else 1)
