"""One independently pinned chain fragment inside one fresh native Job."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime import ROOT, RUN, Runtime, pause_check, read_json, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins', type=Path, required=True)
parser.add_argument('--expect-pins', required=True)
parser.add_argument('--request', type=Path, required=True)
parser.add_argument('--expect-request', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
runtime = Runtime('probe', args.pins, args.expect_pins, args.output,
    request=(args.request, args.expect_request))
runtime.install_torch_guards()
from docs.phase2.cho51_linear_chain_v1.origin import verify_chain

OUT, pins, request = args.output, runtime.pins, runtime.request
os.chdir(OUT)
history = verify_chain(runtime.root_origin, runtime.chain, ROOT, pins_sha256=args.expect_pins)
tests_executed = request['index'] == 1
test_reports, subtest_reports, skipped_reports, unexpected_reports = [], [], [], []
collected_tests, collected_subtests, pytest_exit = 0, 0, None
reuse_sha = None
if tests_executed:
    import pytest
    from _pytest.reports import TestReport
    from _pytest.subtests import SubtestReport

    class Results:
        def pytest_collection_finish(self, session):
            global collected_tests
            collected_tests = len(session.items)
        def pytest_runtest_setup(self, item):
            pause_check()
        def pytest_runtest_logreport(self, report):
            row = {'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome}
            if report.skipped:
                skipped_reports.append(row)
            if type(report) is SubtestReport:
                subtest_reports.append(row)
            elif type(report) is TestReport:
                if report.when == 'call' or report.failed:
                    test_reports.append(row)
            else:
                row['report_type'] = type(report).__module__ + '.' + type(report).__qualname__
                unexpected_reports.append(row)

    pytest_exit = int(pytest.main(['-q', '-s', '-p', 'no:cacheprovider', '-o', 'addopts=',
        '--import-mode=importlib', '--log-file', str(OUT / 'pytest.log'), '--basetemp', str(OUT / 't'),
        '--junitxml', str(OUT / 'junit.xml'), *[str(ROOT / node) for node in pins['test_nodes']]], plugins=[Results()]))
    collected_subtests = len(subtest_reports)
    tests_passed = (pytest_exit == 0 and collected_tests == pins['expected_tests']
        and len(test_reports) == pins['expected_tests'] and not skipped_reports
        and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in test_reports)
        and collected_subtests == pins['expected_subtests'] and not unexpected_reports
        and runtime.numerical_calls == {})
else:
    # verify_chain has independently authenticated every prior native proof,
    # including the first leaf's exact successful tests under this fixed bundle.
    if not runtime.chain['leaves']:
        raise ValueError('later fragment requires an accepted first test leaf')
    reuse_sha = runtime.chain['leaves'][0]['sha256']
    tests_passed = runtime.numerical_calls == {}

result = {'schema': 'cho51_linear_chain_child_result_v1', 'passed': False,
    'request_sha256': args.expect_request, 'request_index': request['index'], 'mode': request['mode'],
    'tests_executed': tests_executed, 'tests_reused': not tests_executed,
    'tests_reused_from_leaf_sha256': reuse_sha, 'tests_passed': tests_passed,
    'pytest_exit': pytest_exit, 'collected_tests': collected_tests, 'expected_tests': pins['expected_tests'],
    'collected_subtests': collected_subtests, 'expected_subtests': pins['expected_subtests'],
    'reports': test_reports, 'subtest_reports': subtest_reports,
    'skipped_reports': skipped_reports, 'unexpected_reports': unexpected_reports, 'probe': None,
    'pretrained_baseline_loaded': False, 'cohort_lineage_verified': False,
    'full_selector_verified': False, 'full_worker_verified': False,
    'scientific_admission': False, 'original_case_attempts_remaining': 0}
if tests_passed:
    runtime.verify_pins()
    from docs.phase2.cho51_linear_chain_v1.executor import run_probe
    method = read_json(RUN / 'method-config.json')
    runtime.active = True
    try:
        probe = run_probe(OUT, method, request=request, origin=runtime.root_origin, chain=runtime.chain,
            set_protected_inputs=runtime.set_protected_inputs, checkpoint_control=runtime.checkpoint_control)
    finally:
        runtime.active = False
    budget = runtime.budget
    expected = {'passed': True, 'method': 'labram_linear',
        'actual_gradient_updates': budget['gradient_updates'],
        'source_gradient_updates': budget['source_updates'], 'support_gradient_updates': budget['support_updates'],
        'pretrained_baseline_loaded': True, 'cohort_lineage_verified': False,
        'full_selector_verified': request['mode'] == 'final',
        'full_worker_verified': False, 'publication_performed': False, 'recorder_used': False,
        'measured_cells': 0, 'scientific_admission': False}
    for key, expected_value in expected.items():
        if type(probe.get(key)) is not type(expected_value) or probe[key] != expected_value:
            raise ValueError('actual executor result differs: ' + key)
    calls = {'tensor_backward': budget['gradient_updates'], 'autograd_backward': budget['gradient_updates'],
        'sgd_step': budget['gradient_updates'], 'optimizer_init': budget['optimizer_init'],
        'safetensors_load': budget['safetensors_load'], 'module_load_state_dict': budget['module_load_state_dict'],
        'safetensors_save': budget['safetensors_save']}
    if (any(runtime.numerical_calls.get(key, 0) != value for key, value in calls.items())
            or runtime.numerical_calls.get('autograd_grad', 0) != 0
            or runtime.source_steps != budget['source_updates'] or runtime.support_steps != budget['support_updates']
            or [row['enabled'] for row in runtime.protection_transitions] != [True, False]
            or (runtime.checkpoint_pin is not None) != (request['mode'] == 'final')):
        raise ValueError('exact dynamic native fragment numerical budget required')
    result.update(passed=True, probe=probe, pretrained_baseline_loaded=True,
        full_selector_verified=probe['full_selector_verified'],
        actual_gradient_updates=budget['gradient_updates'], source_updates=budget['source_updates'],
        support_updates=budget['support_updates'], checkpoint=runtime.checkpoint_pin)
write_json(OUT / 'result.json', result)
runtime.finish(result)
print(json.dumps({'passed': result['passed'], 'request_index': request['index'], 'mode': request['mode'],
    'actual_gradient_updates': result.get('actual_gradient_updates', 0),
    'full_selector_verified': result['full_selector_verified'], 'scientific_admission': False}), flush=True)
raise SystemExit(0 if result['passed'] else 1)
