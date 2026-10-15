"""One native-guarded two-fold synthetic linear lineage qualification."""
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
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
runtime = Runtime('probe', args.pins, args.expect_pins, args.output)
runtime.install_torch_guards()
import pytest
from _pytest.reports import TestReport
from _pytest.subtests import SubtestReport


class Results:
    def __init__(self):
        self.items, self.calls, self.subtest_reports, self.skipped = 0, [], [], []
        self.unexpected_reports = []
    def pytest_collection_finish(self, session):
        self.items = len(session.items)
    def pytest_runtest_setup(self, item):
        pause_check()
    def pytest_runtest_logreport(self, report):
        row = {'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome}
        if report.skipped:
            self.skipped.append({'nodeid': report.nodeid, 'phase': report.when})
        if type(report) is SubtestReport:
            row['context'] = repr(report.context)[:500]
            self.subtest_reports.append(row)
        elif type(report) is TestReport:
            if report.when == 'call' or report.failed:
                self.calls.append(row)
        else:
            row['report_type'] = type(report).__module__ + '.' + type(report).__qualname__
            self.unexpected_reports.append(row)


reports = Results()
OUT, pins = args.output, runtime.pins
os.chdir(OUT)
pytest_exit = pytest.main(['-q', '-s', '-p', 'no:cacheprovider', '-o', 'addopts=',
    '--import-mode=importlib', '--log-file', str(OUT / 'pytest.log'), '--basetemp', str(OUT / 't'),
    '--junitxml', str(OUT / 'junit.xml'), *[str(ROOT / node) for node in pins['test_nodes']]], plugins=[reports])
tests_passed = (pytest_exit == 0 and reports.items == pins['expected_tests']
    and len(reports.calls) == pins['expected_tests'] and not reports.skipped
    and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in reports.calls)
    and len(reports.subtest_reports) == pins['expected_subtests']
    and all(row['phase'] == 'call' and row['outcome'] == 'passed' for row in reports.subtest_reports)
    and not reports.unexpected_reports
    and runtime.numerical_calls == {})
result = {'schema': 'cho51_linear_lineage_child_result_v1', 'passed': False,
    'tests_passed': tests_passed, 'pytest_exit': int(pytest_exit),
    'collected_tests': reports.items, 'expected_tests': pins['expected_tests'],
    'reports': reports.calls, 'skipped_reports': reports.skipped, 'probe': None,
    'expected_subtests': pins['expected_subtests'], 'collected_subtests': len(reports.subtest_reports),
    'subtest_reports': reports.subtest_reports, 'unexpected_reports': reports.unexpected_reports,
    'pretrained_baseline_loaded': False, 'cohort_lineage_verified': False,
    'full_selector_verified': False, 'full_worker_verified': False,
    'scientific_admission': False, 'original_case_attempts_remaining': 0}
if tests_passed:
    runtime.verify_pins()
    from docs.phase2.cho51_linear_lineage_v1.probe import run_probe
    method = read_json(RUN / 'method-config.json')
    runtime.active = True
    try:
        probe = run_probe(OUT, method, set_protected_inputs=runtime.set_protected_inputs)
    finally:
        runtime.active = False
    expected = {'passed': True, 'method': 'labram_linear', 'actual_gradient_updates': 102,
        'source_gradient_updates': 100, 'support_gradient_updates': 2, 'diagnostic_folds': 2,
        'required_selection_updates': 5253, 'pretrained_baseline_loaded': True,
        'cohort_lineage_verified': False, 'complete': False, 'selected_candidate': None,
        'full_selector_verified': False, 'publication_performed': False, 'recorder_used': False,
        'measured_cells': 0, 'source_backbone_and_buffers_unchanged': True,
        'all_physical_inputs_rehashed_unchanged': True, 'torch_numpy_python_rng_unchanged': True}
    if (any(type(probe.get(key)) is not type(value) or probe[key] != value for key, value in expected.items())
            or runtime.numerical_calls.get('tensor_backward') != 102
            or runtime.numerical_calls.get('autograd_backward') != 102
            or runtime.numerical_calls.get('autograd_grad', 0) != 0
            or runtime.numerical_calls.get('sgd_step') != 102
            or runtime.numerical_calls.get('optimizer_init') != 4
            or runtime.numerical_calls.get('safetensors_load') != 2
            or runtime.source_steps != 100 or runtime.support_steps != 2
            or [row['enabled'] for row in runtime.protection_transitions] != [True, False]
            or type(probe.get('fold_timings_seconds')) is not list or len(probe['fold_timings_seconds']) != 2):
        raise ValueError('exact genuine pretrained-baseline two-fold linear workload required')
    result.update(passed=True, probe=probe, pretrained_baseline_loaded=True,
        actual_gradient_updates=102, source_updates=100, support_updates=2,
        diagnostic_folds=2, required_selection_updates=5253,
        fold_timings_seconds=probe['fold_timings_seconds'])
write_json(OUT / 'result.json', result)
runtime.finish(result)
print(json.dumps({'passed': result['passed'], 'actual_gradient_updates': result.get('actual_gradient_updates', 0),
    'full_selector_verified': False, 'scientific_admission': False}), flush=True)
raise SystemExit(0 if result['passed'] else 1)
