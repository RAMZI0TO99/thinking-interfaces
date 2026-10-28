"""Prepare independently reviewed restoration pins after native binary pinning."""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import json
import os
import platform
import stat
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(RUN))
import origin


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def write_once(path, value):
    with path.open('xb') as stream:
        stream.write(origin.canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def source_tree(path, expected):
    before = origin.identity(path)
    origin.need(0 < before[2] <= 1024**2 and before[-1] == expected, 'bounded reviewed Python source required')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(before[2] + 1)
        finished = os.fstat(stream.fileno())
    key = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    origin.need(origin.identity(path) == before and key(opened) == key(finished)
                and key(opened)[:4] == before[:4] and len(raw) == before[2]
                and hashlib.sha256(raw).hexdigest() == expected, 'reviewed source changed during fixed bounded AST read')
    return ast.parse(raw, filename=str(path))


def classification_regression(tree):
    definitions = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'PinnedCodePaths']
    origin.need(len(definitions) == 1, 'one reviewed standalone code classifier required')
    namespace = dict(__name__='_reviewed_code_classification_regression', Path=Path, os=os, stat=stat, types=types)
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(RUN / 'runtime.py'), 'exec'), namespace)
    classifier_type = namespace['PinnedCodePaths']
    checked = {}

    def refused(name, operation):
        try:
            operation()
        except ValueError:
            checked[name] = True
        else:
            raise ValueError('code classification regression did not refuse: ' + name)

    with tempfile.TemporaryDirectory(prefix='classification-regression-', dir=RUN) as directory:
        folder = Path(directory)
        path, old = folder / 'reviewed.py', folder / 'replaced.py'
        raw = b'pass\n'
        with path.open('xb') as stream:
            stream.write(raw)
        classifier = classifier_type((path,))
        code = compile(raw, str(path), 'exec')
        origin.need(classifier.classify(code) == path and classifier.classify(code) == path,
                    'canonical actual-code cache hit differs')
        origin.need(classifier.snapshot()['hits'] == 1 and classifier.snapshot()['identity_checks'] == 2,
                    'each actual-code cache hit must recheck physical identity')
        checked['canonical_hit_rechecks_identity'] = True
        foreign = compile(raw, str(folder / 'foreign.py'), 'exec')
        origin.need(classifier.classify(foreign) is None and len(classifier.codes) == 1,
                    'unregistered foreign code must not inherit a structurally equal code cache hit')
        checked['foreign_code_is_not_authorized'] = True
        origin.need(classifier.classify(compile(raw, path.name, 'exec')) is None
                    and classifier.classify(compile(raw, str(folder) + '/./reviewed.py', 'exec')) is None,
                    'relative and aliased code filenames must not gain canonical classification')
        checked['relative_and_alias_are_not_authorized'] = True
        refused('non_code_object_refused', lambda: classifier.classify(object()))
        refused('duplicate_canonical_path_refused', lambda: classifier_type((path, path)))
        path.rename(old)
        with path.open('xb') as stream:
            stream.write(raw)
        refused('same_bytes_replacement_refused', lambda: classifier.classify(code))
        fresh = classifier_type((path,))
        origin.need(fresh.classify(code) == path, 'fresh regression classifier did not establish actual fixture identity')
        with path.open('ab') as stream:
            stream.write(b'pass\n')
        refused('growing_file_refused', lambda: fresh.classify(code))
        information = types.SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=1, st_dev=1, st_ino=1,
            st_size=5, st_mtime_ns=1, st_ctime_ns=1, st_file_attributes=0)
        classifier_type._file_key(information)
        information.st_nlink = 2
        refused('multiple_links_refused', lambda: classifier_type._file_key(information))
        information.st_nlink, information.st_file_attributes = 1, 1024
        refused('file_reparse_refused', lambda: classifier_type._file_key(information))
        information.st_mode = stat.S_IFDIR | 0o700
        refused('ancestor_reparse_refused', lambda: classifier_type._ancestor_key(information))
        information.st_file_attributes, information.st_mode = 0, stat.S_IFLNK | 0o700
        refused('ancestor_symlink_refused', lambda: classifier_type._ancestor_key(information))
    origin.need(set(checked) == set(origin.CODE_CLASSIFICATION_CASES) and all(checked.values()),
                'exact deterministic stdlib classification regression inventory required')
    return dict(schema='cho51_pinned_code_classification_regression_v1', passed=True, cases=checked,
                scientific_imports=False, content_hashes_cached=False, authorization_decisions_cached=False)


def main():
    longest_record = RUN / 't1/t' / ('x' * 32) / 'p/fixture/runs/phase2/lifecycle/engineering_successes' / ('f' * 64 + '.success.json')
    origin.need(len(str(longest_record)) < 260, 'short fixed unit output must keep canonical hard-link records below Windows MAX_PATH')
    origin.need(not any((RUN / name).exists() for name in ('pins.json', 'origin-contract.json', 't1', 'i1')),
                'unused fresh restoration preparation required')
    native = origin.document(RUN / 'native-runtime.json')
    previous = origin.document(origin.PREVIOUS / 'pins.json', origin.PREVIOUS_PINS_SHA)
    origin.need(native['schema'] == 'cho51_provenance_numerical_worker_native_runtime_v1'
                and native['historical_pins_sha256'] == origin.PREVIOUS_PINS_SHA and native['python_executed'] is False,
                'fresh native runtime observation required before Python')
    for group, count in (('runtime', 5), ('runtime_modules', 18), ('supporting_runtime_sources', 4)):
        origin.need(set(native[group]) == set(previous[group]) and len(native[group]) == count,
                    'fresh runtime paths differ from authenticated historical inventory')
        for path, value in native[group].items():
            origin.need(origin.digest(path) == value, 'fresh native runtime pin changed')
    origin.need(str(Path(sys.executable).resolve()) in native['runtime']
                and str(Path(sys._base_executable).resolve()) in native['runtime'], 'running interpreter is not natively pinned')
    candidate = ROOT / 'docs/phase2/cho51_provenance_numerical_worker_v2'
    candidate_names = {'numerical_worker.py', 'backend.py', 'pipeline.py', 'test_integration.py', 'README.md'}
    operation_names = {'prepare.py', 'parent.py', 'runtime.py', 'origin.py', 'native_pins.ps1', 'launch.ps1', 'closeout.py', 'guard.py'}
    origin.need({path.name for path in candidate.iterdir()} == candidate_names, 'exact five integration candidate sources required')
    paths = {candidate / name for name in candidate_names} | {RUN / name for name in operation_names}
    reviewed = {path.relative_to(ROOT).as_posix(): origin.digest(path) for path in sorted(paths)}
    trees = {path: source_tree(path, reviewed[path.relative_to(ROOT).as_posix()])
             for path in paths if path.suffix == '.py'}
    review_path = RUN / 'source-review.json'
    review = origin.document(review_path)
    origin.need(review.get('source_only') is True and review.get('remaining_actionable_findings') == []
                and review.get('files') == reviewed, 'exact independent settled thirteen-source review required')
    code_regression = classification_regression(trees[RUN / 'runtime.py'])
    nodes, count = [], 0
    test = candidate / 'test_integration.py'
    for node in trees[test].body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            cases = 1
            for mark in node.decorator_list:
                if isinstance(mark, ast.Call) and isinstance(mark.func, ast.Attribute) and mark.func.attr == 'parametrize':
                    origin.need(len(mark.args) >= 2 and isinstance(mark.args[1], (ast.List, ast.Tuple)),
                                'literal parameterized boundary inventory required')
                    cases *= len(mark.args[1].elts)
            nodes.append(test.relative_to(ROOT).as_posix() + '::' + node.name)
            count += cases
    origin.need(count == 63, 'exact sixty-three frozen candidate metadata cases required')
    verified = origin.verify_origin_stages()
    metadata_only = origin.verify_origin_stages(verify_physical_inputs=False)
    expected_metadata = dict(verified, summary=dict(verified['summary'], input_audit=None))
    origin.need(metadata_only == expected_metadata and verified['summary']['input_audit'] == origin.verify_inputs(),
                'metadata-only mode may omit only the separately reverified physical input audit')
    contract = dict(schema='cho51_linear_worker_origin_contract_v1', **verified)
    contract_sha = hashlib.sha256(origin.canonical(contract)).hexdigest()
    files = dict(previous['files'])
    files.update(reviewed)
    for path, value in verified['files'].items():
        physical = Path(path)
        if verified['roles'][path] == 'metadata' and physical.is_relative_to(ROOT):
            files[physical.relative_to(ROOT).as_posix()] = value
    files[review_path.relative_to(ROOT).as_posix()] = origin.digest(review_path)
    files[(RUN / 'native-runtime.json').relative_to(ROOT).as_posix()] = origin.digest(RUN / 'native-runtime.json')
    files[(RUN / 'origin-contract.json').relative_to(ROOT).as_posix()] = contract_sha
    amendment_path = RUN / 'owner-resource-amendment.json'
    amendment = origin.document(amendment_path)
    expected_amendment = dict(schema='cho51_provenance_numerical_worker_owner_resource_amendment_v1',
                             scope='cho51_provenance_numerical_worker_20261025_v6', previous_startup_ram_gib=10,
                             owner_instruction_exact='use the available ram now!',
                             startup_ram_gib=4, active_ram_gib=4, disk_gib=20, maximum_job_seconds=600,
                             process_mib=4096, job_mib=5120, threads=1, gpu_hidden=True,
                             canonical_guard_modified=False, historical_receipts_requalified=False, scientific_admission=False)
    origin.need(all(type(amendment.get(name)) is type(value) and amendment[name] == value
                    for name, value in expected_amendment.items()), 'exact direct-owner startup-only amendment required')
    amendment_sha = origin.digest(amendment_path)
    files[amendment_path.relative_to(ROOT).as_posix()] = amendment_sha
    publication_path = origin.PUBLICATION / 'publication_001/publication-result.json'
    publication = origin.document(publication_path, verified['files'][str(publication_path)])
    old_contract = origin.document(origin.PUBLICATION / 'origin-contract.json',
                                   '8bffd0d8be4f8ed2b87189ec0f36462303b88c627b1a8115c7651805a8a5c20b')
    producer = dict(source_json=compact(publication['source']), manifest_sha256=publication['manifest_sha256'],
                    manifest_file_sha256=publication['manifest_file_sha256'], evidence_sha256=publication['evidence_sha256'],
                    evidence_file_sha256=publication['evidence_file_sha256'], weights_sha256=publication['weights_file_sha256'],
                    model_state_sha256=publication['model_state_sha256'], model_recipe_sha256=publication['model_recipe_sha256'],
                    selection_contract_sha256=old_contract['contract_sha256'], selected_candidate=publication['selected_candidate'],
                    publication_path=str(publication_path), publication_file_sha256=origin.digest(publication_path))
    head = subprocess.run(['git', '--no-optional-locks', 'rev-parse', '--verify', 'HEAD'], cwd=ROOT,
                          capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    dirty = bool(subprocess.run(['git', '--no-optional-locks', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT,
                                capture_output=True, text=True, check=True, timeout=10).stdout)
    configs = ('configs/base.toml', 'configs/benchmark.toml', 'configs/phase2/protocol.toml',
               'configs/phase2/selection_ceiling.toml', 'configs/phase2/cho_profile_b_60hz.toml')
    source_sha = hashlib.sha256('\n'.join(f'{name}:{files[name]}' for name in sorted(configs)).encode()).hexdigest()
    source = dict(git_commit=head, git_dirty=dirty, source_sha256=origin.CANONICAL)
    fixture_source = dict(git_commit=head, git_dirty=dirty, source_sha256=source_sha)
    sys.path.insert(0, str(ROOT / '.venv/Lib/site-packages'))
    runtime = dict(python_full=sys.version, python=platform.python_version(), executable=str(Path(sys.executable).resolve()),
                   **{name: importlib.metadata.version(name) for name in ('torch', 'numpy', 'braindecode')})
    executor_sources = {str(ROOT / name): value for name, value in files.items()
                        if name in reviewed or name.endswith('.py') or name in configs}
    executor_runtime = {path: value for path, value in dict(native['runtime'], **native['runtime_modules']).items()
                        if Path(path).name.lower() != 'git.exe'}
    executor = dict(root=str(ROOT), source_json=compact(source), runtime_json=compact(runtime),
                    source_files_json=compact(dict(sorted(executor_sources.items()))),
                    runtime_files_json=compact(dict(sorted(executor_runtime.items()))))
    pins = dict(schema='cho51_provenance_numerical_worker_pins_v1', maximum_unit_record_path_characters=len(str(longest_record)),
                operational_scope=origin.BASE_SCOPE, phase_scopes={phase: origin.phase_paths(phase)['scope'] for phase in origin.PHASES},
                phase_outputs={phase: str(origin.phase_paths(phase)['output']) for phase in origin.PHASES},
                phase_budgets=dict(tests=dict(origin.ZERO_BUDGET), integration=dict(origin.FULL_BUDGET)),
                prospective_overall_numerical_budget=dict(origin.FULL_BUDGET), prepared_utc=datetime.now(timezone.utc).isoformat(),
                code_classification_policy=dict(origin.CODE_CLASSIFICATION_POLICY), code_classification_regression=code_regression,
                files=files, runtime=native['runtime'], runtime_modules=native['runtime_modules'],
                supporting_runtime_sources=native['supporting_runtime_sources'],
                native_runtime_sha256=origin.digest(RUN / 'native-runtime.json'), historical_pins_sha256=origin.PREVIOUS_PINS_SHA,
                baseline=previous['baseline'], selected_weights={publication['weights_path']: publication['weights_file_sha256']},
                factory_producer=producer, factory_executor=executor, store_root=str(Path(publication['manifest_path']).parents[1]),
                method_config_path=old_contract['method_config_path'], method_config_sha256=old_contract['method_config_sha256'],
                method_config_file_sha256=old_contract['method_config_file_sha256'],
                owner_decision_sha256=previous['owner_decision_sha256'], origin_contract_file_sha256=contract_sha,
                expected_current_context=source, expected_fixture_context=fixture_source,
                factory_claim=dict(recorder_root=str(RUN / 'i1/fixture'),
                                   output_root=str(RUN / 'i1/fixture/runs/phase2/lifecycle'),
                                   source=fixture_source, worker='cho51_provenance_numerical_worker_engineering_v2', attempt=1),
                reviewed_files=reviewed, source_review_path=str(review_path),
                source_review_sha256=origin.digest(review_path), canonical_files=432, canonical_source_sha256=origin.CANONICAL,
                seconds=600, process_mib=4096, job_mib=5120, startup_ram_gib=4, active_ram_gib=4, disk_gib=20,
                owner_resource_amendment_path=str(amendment_path), owner_resource_amendment_sha256=amendment_sha,
                previous_startup_ram_gib=10, historical_10gib_startup_pass_claimed=False,
                threads=1, gpu_hidden=True, current_restore_count=1, current_source_updates=0, current_support_updates=1,
                current_gradient_updates=1, target_inference_calls=1, query_count=2, measured_cells=0, scientific_admission=False,
                full_model_constructions=1, parameterless_clone_reinitializations=4, empty_mask_containers=2,
                expected_numerical_budget=dict(source_updates=0, restore_count=1, support_updates=1,
                    gradient_updates=1, target_inference_calls=1, query_count=2, model_constructions=1, measured_cells=0),
                original_case_attempts_remaining=0, test_nodes=nodes, expected_tests=count,
                mne_resource_path=previous['mne_resource_path'], mne_resource_sha256=previous['mne_resource_sha256'])
    for group in ('runtime', 'runtime_modules', 'supporting_runtime_sources'):
        for path, value in native[group].items():
            origin.need(origin.digest(path) == value, 'fresh runtime changed during preparation')
    origin.need(origin.verify_origin_stages() == verified, 'historical inputs changed during preparation')
    write_once(RUN / 'origin-contract.json', contract)
    write_once(RUN / 'pins.json', pins)
    print(json.dumps(dict(pins_sha256=origin.digest(RUN / 'pins.json'), source_files=len(files), tests=count,
                          origin_files=len(verified['files']), launched=False), sort_keys=True))


if __name__ == '__main__':
    main()






