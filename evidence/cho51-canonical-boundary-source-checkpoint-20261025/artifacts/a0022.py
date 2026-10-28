"""One guarded metadata-only pytest phase; real types, no execution capability."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib
import inspect
import json
import os
import stat
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata_common as control

ROOT, RUN, OUTPUT = control.ROOT, control.RUN, control.OUTPUT
CANDIDATE = ROOT / 'docs/phase2/cho51_canonical_boundary_v1'
SITE = ROOT / '.venv/Lib/site-packages'


class Audit:
    def __init__(self, pins):
        self.pins = pins
        self.denied = []
        self.optional_ipv6 = 0
        self.bytecode_refusals = 0
        self.import_resource_reads = 0
        self.resource_hash_reads = 0
        self.forbidden = {}
        self.git_queries = 0
        self.phase = 'runtime_bootstrap'
        self.git = next(Path(path) for path in pins['files'] if Path(path).name == 'git.exe')

    @staticmethod
    def caller(path, name=None):
        frame = sys._getframe(1)
        while frame:
            if Path(frame.f_code.co_filename).absolute() == path and (name is None or frame.f_code.co_name == name):
                return True
            frame = frame.f_back
        return False

    def reject(self, name, detail=None):
        self.denied.append(dict(event=name, detail=str(detail)[:300], phase=self.phase))
        raise PermissionError('metadata confinement: ' + name)

    @staticmethod
    def boundary_origin():
        frame = sys._getframe(1)
        while frame:
            path = Path(frame.f_code.co_filename).absolute()
            if path in {CANDIDATE / 'boundary.py', CANDIDATE / 'test_boundary.py'}:
                return path == CANDIDATE / 'boundary.py'
            frame = frame.f_back
        return False

    def blocked(self, name):
        def refuse(*arguments, **keywords):
            self.forbidden[name] = self.forbidden.get(name, 0) + 1
            self.reject(name)
        return refuse

    def patch(self, owner, name, label=None):
        if hasattr(owner, name):
            setattr(owner, name, self.blocked(label or name))

    @staticmethod
    def normalized(value):
        return Path(os.path.abspath(os.fsdecode(value)))

    def owned_mutation(self, value):
        path = self.normalized(value)
        if not path.is_relative_to(OUTPUT):
            self.reject('outside_normalized_mutation', path)
        for ancestor in (path, *path.parents):
            try:
                info = ancestor.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 1024:
                self.reject('reparse_mutation_path', path)
        return path

    def hook(self, event, values):
        if event == 'open':
            mode = values[1] if isinstance(values[1], str) else ''
            flags = values[2] if isinstance(values[2], int) else 0
            writing = any(flag in mode for flag in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if not isinstance(values[0], (str, bytes, os.PathLike)):
                if writing and type(values[0]) is int:
                    control.need(stat.S_ISFIFO(os.fstat(values[0]).st_mode), 'unbound descriptor write refused')
                return
            path = self.normalized(values[0])
            if writing:
                self.owned_mutation(values[0])
                if not path.is_relative_to(OUTPUT) or self.boundary_origin():
                    self.reject('boundary_or_outside_write', path)
                return
            if path.suffix.lower() == '.pyc' and not path.is_relative_to(OUTPUT):
                self.bytecode_refusals += 1
                raise PermissionError('fresh pinned source imports only')
            if path.suffix.lower() in {'.npz', '.npy', '.mat', '.fif', '.edf', '.gdf', '.set', '.pt', '.pth', '.ckpt', '.safetensors'}:
                resource = SITE / 'mne/data/fsaverage/fsaverage-fiducials.fif'
                if (path == resource and path.stat().st_size == 260
                        and self.pins['files'].get(str(resource)) == '0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'):
                    if (not self.boundary_origin() and self.caller(RUN / 'metadata_common.py', 'verify_files')
                            and self.caller(RUN / 'metadata_common.py', 'read')):
                        self.resource_hash_reads += 1
                        control.need(self.resource_hash_reads <= 16, 'bounded independent runtime-resource hash reads required')
                        return
                    if self.phase == 'runtime_bootstrap':
                        self.import_resource_reads += 1
                        control.need(self.import_resource_reads <= 16, 'bounded runtime fiducial import reads required')
                        return
                if not (path.suffix.lower() == '.pth' and path.is_relative_to(SITE)):
                    self.reject('signal_or_weight_read', path)
            if path.is_relative_to(ROOT) and any(path.is_relative_to(ROOT / relative) for relative in ('data/raw', 'data/processed', 'data/interim')):
                self.reject('production_signal_read', path)
            if path.suffix.lower() in {'.py', '.pyd'} and str(path) not in self.pins['files']:
                self.reject('unpinned_code_read', path)
        elif event == 'subprocess.Popen':
            executable, arguments, cwd, environment = values
            forms = [[str(self.git), '--no-optional-locks', *tail] for tail in
                     (['rev-parse', '--verify', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'])]
            allowed = any(arguments == form or arguments == __import__('subprocess').list2cmdline(form) for form in forms)
            if (not allowed or environment is not None or cwd is None
                    or not Path(cwd).absolute().is_relative_to(ROOT)
                    or not self.caller(ROOT / 'core/provenance.py', 'capture_source')):
                self.reject(event, arguments)
            self.git_queries += 1
        elif event.startswith('socket.') and event != 'socket.gethostname':
            connection = SITE / 'urllib3/util/connection.py'
            if event == 'socket.__new__' and self.caller(connection, '_has_ipv6'):
                self.optional_ipv6 += 1
                raise PermissionError('optional import IPv6 probe refused')
            self.reject(event)
        elif event in {'os.system', 'os.startfile', 'os.posix_spawn', 'os.fork', 'os.forkpty', 'pty.spawn'} or event.startswith(('os.exec', 'os.spawn')):
            self.reject(event)
        elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.replace', 'os.link', 'os.symlink', 'os.chmod', 'os.utime', 'os.truncate'}:
            if event == 'os.symlink':
                self.reject('alias_creation_forbidden')
            count = 2 if event in {'os.rename', 'os.replace', 'os.link', 'os.symlink'} else 1
            for value in values[:count]:
                if not isinstance(value, (str, bytes, os.PathLike)):
                    self.reject('unbound_mutation', event)
                path = self.normalized(value)
                if event == 'os.mkdir' and not path.is_relative_to(OUTPUT) and path.is_dir():
                    raise FileExistsError(17, 'outside existing directory creation refused', str(path))
                self.owned_mutation(value)
                if not path.is_relative_to(OUTPUT) or self.boundary_origin():
                    self.reject('boundary_or_outside_mutation', path)
        elif event == 'os.chdir' and not self.normalized(values[0]).is_relative_to(OUTPUT):
            self.reject(event, values)


class Reports:
    def __init__(self):
        self.collected = []
        self.reports = []

    def pytest_collection_finish(self, session):
        self.collected = [item.nodeid for item in session.items]

    def pytest_runtest_setup(self, item):
        control.pause_check()

    def pytest_runtest_logreport(self, report):
        self.reports.append(dict(nodeid=report.nodeid, phase=report.when, outcome=report.outcome))


def guard_modules(audit):
    import numpy
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    for owner, name, label in (
        (numpy, 'load', 'numpy.load'), (numpy, 'save', 'numpy.save'), (numpy, 'savez', 'numpy.savez'),
        (torch.nn.Module, '__init__', 'model_construction'), (torch.nn.Module, 'load_state_dict', 'state_load'),
        (torch, 'load', 'torch.load'), (torch, 'save', 'torch.save'),
        (torch.Tensor, 'backward', 'tensor_backward'), (torch.autograd, 'backward', 'autograd_backward'),
        (torch.optim.Optimizer, '__init__', 'optimizer_construction'),
    ):
        audit.patch(owner, name, label)
    modules = {name: importlib.import_module(name) for name in (
        'evaluation.phase2_runner', 'evaluation.phase2_cho_case_inputs', 'evaluation.phase2_profile_binding',
        'evaluation.phase2_cho_execution', 'evaluation.phase2_pilot', 'evaluation.phase2_cho_sweep',
        'evaluation.phase2_cho_source_restore', 'evaluation.phase2_cho_selected_manifest_bridge',
        'evaluation.phase2_selected_source_store', 'evaluation.phase2_selection_evidence_binding',
        'docs.phase2.cho51_worker_bridge_v1.worker_bridge',
    )}
    runner = modules['evaluation.phase2_runner']
    for owner, names in (
        (runner.CaseRecorder, ('__init__', 'case_session')),
        (runner.LockedCase, ('__enter__', 'record_cell', 'record_engineering_success', 'recover_cell', 'recover_engineering_success')),
        (modules['evaluation.phase2_pilot'].TargetCaseExecutor, ('__init__', 'run_case')),
        (modules['evaluation.phase2_cho_sweep'].ProductionChoCaseRunner, ('__init__', '__call__')),
    ):
        for name in names:
            audit.patch(owner, name, owner.__name__ + '.' + name)
    unsafe = {
        'evaluation.phase2_cho_case_inputs': ('prepare_cho_first_tranche',),
        'evaluation.phase2_cho_execution': ('execute_engineering_cases', 'run_cho_execution_child', 'verify_staged_proposal'),
        'evaluation.phase2_cho_source_restore': ('prepare_cho_source_restore', 'restore_cho_selected_source', '_new_model'),
        'evaluation.phase2_cho_selected_manifest_bridge': ('verify_cho_selected_manifest_files',),
        'evaluation.phase2_selection_evidence_binding': ('verify_complete_cho_selection_evidence',),
        'docs.phase2.cho51_worker_bridge_v1.worker_bridge': ('prepare_cho51_worker_route',),
    }
    for module_name, names in unsafe.items():
        for name in names:
            audit.patch(modules[module_name], name, module_name + '.' + name)
    for name in ('array', 'asarray', 'zeros', 'ones', 'empty', 'full', 'arange', 'linspace', 'frombuffer', 'fromfile'):
        audit.patch(numpy, name, 'numpy.' + name)
    for name in ('tensor', 'as_tensor', 'from_numpy', 'zeros', 'ones', 'empty', 'full', 'arange', 'rand', 'randn'):
        audit.patch(torch, name, 'torch.' + name)
    try:
        import safetensors.torch
        audit.patch(safetensors.torch, 'load_file', 'safetensors.load_file')
    except ImportError:
        pass
    audit.phase = 'metadata_assessment'
    return numpy, torch


def loaded_files(pins):
    result = {}
    for module in tuple(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name and Path(name).is_file():
            path = Path(name).resolve(strict=True)
            control.need(not path.is_relative_to(OUTPUT) and str(path) in pins['files'], 'all loaded modules need fresh external pins: ' + str(path))
            result[str(path)] = control.read(path, pins['files'][str(path)], 2 * 1024**3, retain=False)[0]
    return result


def stdlib_controls(pins):
    from closeout import verify_junit, verify_reports
    from datetime import timedelta
    results = {}

    def refused(name, callback, expected=ValueError):
        try:
            callback()
        except expected:
            results[name] = True
        else:
            raise ValueError('guard control failed to refuse: ' + name)

    results['finite_json'] = control.parse(b'{"nested":[1,false,null,0.5]}') == {'nested': [1, False, None, 0.5]}
    refused('duplicate_json', lambda: control.parse(b'{"key":1,"key":2}'))
    refused('nan_json', lambda: control.parse(b'{"value":NaN}'))
    refused('overflow_json', lambda: control.parse(b'{"value":1e999}'))
    refused('nested_json', lambda: control.parse(('[' * 81 + '0' + ']' * 81).encode()))
    results['zero_budget'] = control.zero_budget(dict(control.ZERO))
    refused('boolean_budget', lambda: control.need(control.zero_budget(dict(control.ZERO, source_updates=False)), 'Boolean zero refused'))
    probe = Audit(pins)
    results['owned_path'] = probe.owned_mutation(OUTPUT / 'absent' / '..' / 'owned.json') == OUTPUT / 'owned.json'
    refused('escaped_path', lambda: probe.owned_mutation(OUTPUT / '..' / 'outside.json'), PermissionError)
    path = OUTPUT / 'control-once.json'
    control.write(path, {'control': True})
    results['first_create'] = control.document(path) == {'control': True}
    refused('duplicate_create', lambda: control.write(path, {'control': True}), FileExistsError)
    log = OUTPUT / 'control-tail.log'
    with log.open('wb') as stream:
        stream.write(b'0123456789')
    results['bounded_tail'] = control.tail(log, 4) == '6789'
    start = datetime.now(timezone.utc)
    results['full_window'] = control.lease_fits(start, start + timedelta(seconds=605))
    results['short_window'] = not control.lease_fits(start, start + timedelta(seconds=604))
    nodeid = 'docs/phase2/cho51_canonical_boundary_v1/test_boundary.py::test_control'
    collected = [nodeid]
    xml = (b'<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0">'
           b'<testcase classname="docs.phase2.cho51_canonical_boundary_v1.test_boundary" name="test_control"/>'
           b'</testsuite></testsuites>')
    verify_junit(xml, collected, 1)
    results['junit_baseline'] = True
    duplicate = xml.replace(b'</testsuite>', b'<testcase classname="docs.phase2.cho51_canonical_boundary_v1.test_boundary" name="test_control"/></testsuite>')
    refused('junit_duplicate', lambda: verify_junit(duplicate, collected, 1))
    failed = xml.replace(b'name="test_control"/>', b'name="test_control"><failure/></testcase>')
    refused('junit_failure', lambda: verify_junit(failed, collected, 1))
    refused('junit_class', lambda: verify_junit(xml.replace(b'classname="docs.', b'classname="wrong.docs.'), collected, 1))
    reports = [dict(nodeid=nodeid, phase=phase, outcome='passed') for phase in ('setup', 'call', 'teardown')]
    verify_reports(collected, reports, 1)
    results['reports_baseline'] = True
    refused('reports_missing', lambda: verify_reports(collected, reports[:-1], 1))
    refused('reports_duplicate', lambda: verify_reports(collected, reports + reports[:1], 1))
    control.need(set(results) == set(control.CONTROL_NAMES) and all(value is True for value in results.values()),
                 'all exact native metadata controls must pass')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--expect-pins', required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    control.need(arguments.pins == RUN / 'pins.json' and arguments.output == OUTPUT and not OUTPUT.exists(), 'fixed fresh output required')
    pins = control.pins(arguments.expect_pins)
    control.verify_files(pins)
    admission, peer = control.admission(pins, arguments.expect_pins)
    native = Path(os.environ['PRO3_BOUNDARY_NATIVE'])
    name = os.environ['PRO3_BOUNDARY_JOB']
    control.need(native.parent == ROOT / 'runs/migration' and name == 'pro3_migration_' + native.name, 'actual owned native path required')
    control.membership(name)
    native_admission = control.document(native / 'admission.json')
    control.need(native_admission['pins_sha256'] == arguments.expect_pins
                 and native_admission['root_admission_sha256'] == control.read(RUN / 'admission.json', retain=False)[0]
                 and native_admission['command'] == [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'runner.py'),
                    '--pins', str(RUN / 'pins.json'), '--expect-pins', arguments.expect_pins, '--output', str(OUTPUT)],
                 'exact live native command and admission binding required')
    attempt = control.document(RUN / 'guard-attempt_001.json', native_admission['guard_attempt_sha256'])
    control.need(attempt['pins_sha256'] == arguments.expect_pins and attempt['maximum_jobs'] == 1
                 and attempt['automatic_retry_permitted'] is False, 'durable once-only guard marker required')
    deadlines = control.document(native / 'deadline.json')
    control.need(datetime.fromisoformat(deadlines['session_deadline_utc']).astimezone(timezone.utc)
                 <= datetime.fromisoformat(peer['window_end_utc']).astimezone(timezone.utc),
                 'full current Job and cleanup deadline must fit peer window')
    OUTPUT.mkdir()
    temporary = OUTPUT / 'tmp'
    temporary.mkdir()
    for directory in (temporary / 'mne', temporary / 'mpl'):
        directory.mkdir()
    os.environ.update(TEMP=str(temporary), TMP=str(temporary), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                      PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
                      _MNE_FAKE_HOME_DIR=str(temporary / 'mne'), MPLCONFIGDIR=str(temporary / 'mpl'))
    os.environ.pop('PYTEST_ADDOPTS', None)
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(SITE))
    audit = Audit(pins)
    sys.addaudithook(audit.hook)
    started = time.monotonic()
    result = dict(schema='cho51_canonical_boundary_test_result_v1', passed=False, pins_sha256=arguments.expect_pins,
                  current_counter_ledger=dict(control.ZERO), scientific_admission=False, runtime_bootstrap='genuine canonical dependencies',
                  no_current_raw_weight_verification=True, native_closeout_status='pending_external_post_job')
    try:
        import pytest
        numpy, torch = guard_modules(audit)
        controls = stdlib_controls(pins)
        reports = Reports()
        os.chdir(OUTPUT)
        status = pytest.main(['-q', '-s', '--maxfail=1', '-p', 'no:cacheprovider', '-o', 'addopts=',
            '--import-mode=importlib', '--basetemp', str(OUTPUT / 't'), '--junitxml', str(OUTPUT / 'junit.xml'),
            str(CANDIDATE / 'test_boundary.py')], plugins=[reports])
        cases = [row for row in reports.reports if row['phase'] == 'call']
        passed = (status == 0 and len(reports.collected) == len(set(reports.collected)) == len(cases) == pins['expected_tests']
                  and all(row['outcome'] == 'passed' for row in reports.reports) and not audit.denied and not audit.forbidden)
        control.need(passed, 'all exact metadata cases and zero forbidden calls required')
        control.need(torch.get_num_threads() == torch.get_num_interop_threads() == 1
                     and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU/thread confinement changed')
        control.verify_files(pins)
        from tools.migration.common import source_check
        control.need(source_check(ROOT) == control.CANONICAL, 'canonical source changed')
        loaded = loaded_files(pins)
        control.membership(name)
        result.update(passed=True, tests=pins['expected_tests'], collected=reports.collected, reports=reports.reports,
                      stdlib_controls=controls,
                      pytest_exit=int(status), elapsed_seconds=time.monotonic()-started,
                      forbidden_calls=dict(audit.forbidden), unexpected_denials=list(audit.denied),
                      optional_ipv6_probes_blocked=audit.optional_ipv6, bytecode_reads_refused=audit.bytecode_refusals,
                      runtime_import_resource_reads=audit.import_resource_reads,
                      runtime_resource_hash_reads_before_result=audit.resource_hash_reads,
                      runtime_import_resource_path=str(SITE / 'mne/data/fsaverage/fsaverage-fiducials.fif'),
                      runtime_import_resource_sha256='0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3',
                      git_queries=audit.git_queries, torch_threads=1, torch_interop_threads=1,
                      native_directory=str(native), job_name=name, native_admission_sha256=control.read(native / 'admission.json', retain=False)[0],
                      root_admission_sha256=control.read(RUN / 'admission.json', retain=False)[0],
                      peer_release_sha256=admission['peer_release_sha256'],
                      loaded_module_hashes=loaded, loaded_module_files=len(loaded),
                      raw_weight_reads=0, model_constructions=0, array_decodes=0, claims=0, locks=0,
                      selectors=0, publications=0, recovery_calls=0,
                      observer_scope='genuine runtime imports; guarded bootstrap model/state/decoder calls and complete metadata-phase API confinement; selectors counts forbidden physical execution selectors, not canonical metadata partition reconstruction',
                      source_sha256=control.CANONICAL, runtime_qualification_of_future_execution=False)
        control.write(OUTPUT / 'result.json', result)
        control.verify_files(pins)
        print(json.dumps(dict(passed=True, tests=pins['expected_tests'], loaded_module_files=len(loaded),
                              current_counter_ledger=control.ZERO, scientific_admission=False)), flush=True)
    except BaseException as error:
        result.update(failure=dict(type=type(error).__name__, message=str(error)[:2000]),
                      forbidden_calls=dict(audit.forbidden), unexpected_denials=list(audit.denied))
        control.write(OUTPUT / 'failure.json', result)
        raise


if __name__ == '__main__':
    main()
