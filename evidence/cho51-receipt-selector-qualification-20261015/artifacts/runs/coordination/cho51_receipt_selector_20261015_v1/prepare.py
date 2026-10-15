"""Prepare fresh source/runtime pins without importing project or test modules."""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
CANONICAL_SHA256 = '3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
CANDIDATES = (
    ROOT / 'docs/phase2/cho51_tensor_collection_v1',
    ROOT / 'docs/phase2/cho51_selector_collection_v1',
)
TEST_FILES = (
    CANDIDATES[0] / 'test_collection.py',
    CANDIDATES[1] / 'test_collection.py',
    RUN / 'test_public_selector.py',
)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def reviewed_files():
    paths = {path for directory in CANDIDATES for path in directory.iterdir() if path.is_file()}
    paths.update(RUN.glob('*.py'))
    paths.update(RUN.glob('*.ps1'))
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(paths)}


def test_nodes(path):
    """Count explicit top-level tests and literal parameter-list sizes by AST only."""
    nodes = []
    for node in ast.parse(path.read_bytes(), filename=str(path)).body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith('test_'):
            continue
        count = 1
        for mark in node.decorator_list:
            if isinstance(mark, ast.Call) and isinstance(mark.func, ast.Attribute) and mark.func.attr == 'parametrize':
                if len(mark.args) < 2 or not isinstance(mark.args[1], (ast.List, ast.Tuple)):
                    raise ValueError('only explicit literal AST parameter rosters are allowed')
                if any(isinstance(element, ast.Starred) for element in mark.args[1].elts):
                    raise ValueError('expanded AST parameter rosters require fresh review')
                count *= len(mark.args[1].elts)
        nodes.append((path.relative_to(ROOT).as_posix() + '::' + node.name, count))
    if not nodes:
        raise ValueError('explicit nonempty named test inventory required: ' + str(path))
    return nodes


sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import source_check

canonical = source_check(ROOT)
canonical_manifest = json.loads((ROOT / 'tools/migration/source-files.json').read_bytes())
if canonical != CANONICAL_SHA256 or len(canonical_manifest['files']) != 432:
    raise ValueError('unchanged canonical 432-file source required')
prior_path = ROOT / 'runs/coordination/cho51_tensor_qualification_20261015_v1/pins_005.json'
prior = json.loads(prior_path.read_bytes())
files = {relative: digest(ROOT / relative) for relative in prior['files']}
fresh_reviewed = reviewed_files()
review_path = RUN / 'source-review.json'
review = json.loads(review_path.read_bytes())
if (
    review.get('source_only') is not True
    or review.get('remaining_actionable_findings') != []
    or review.get('files') != fresh_reviewed
):
    raise ValueError('settled independent source review must name every exact current candidate/operational file')
files.update(fresh_reviewed)
files[review_path.relative_to(ROOT).as_posix()] = digest(review_path)
group_nodes = [test_nodes(path) for path in TEST_FILES]
groups = {
    'mocked_tensor_receipt_cases': sum(count for _, count in group_nodes[0]),
    'mocked_selector_collection_cases': sum(count for _, count in group_nodes[1]),
    'actual_public_verifier_fabricated_record_cases': sum(count for _, count in group_nodes[2]),
}
if groups['actual_public_verifier_fabricated_record_cases'] != 24:
    raise ValueError('eight canonical/factored bridge and sixteen tamper cases required')
git_command = shutil.which('git')
if git_command is None:
    raise ValueError('read-only provenance Git executable must be independently pinned')
git_path = Path(git_command).resolve(strict=True)
runtime_paths = (
    Path(sys.executable).resolve(strict=True),
    (Path(sys.base_prefix) / 'python.exe').resolve(strict=True),
    (Path(sys.base_prefix) / 'python312.dll').resolve(strict=True),
    (Path(sys.base_prefix) / 'python3.dll').resolve(strict=True),
    git_path,
)
if len(set(runtime_paths)) != 5 or any(not path.is_file() for path in runtime_paths):
    raise ValueError('exact five Python/base/DLL/Git runtime files required')
runtime = {str(path): digest(path) for path in runtime_paths}
pins = {
    'schema': 'cho51_receipt_selector_synthetic_fresh_pins_v1',
    'prepared_utc': datetime.now(timezone.utc).isoformat(),
    'files': files, 'runtime': runtime, 'canonical_source_sha256': canonical,
    'canonical_files': 432,
    'previous_pin_file_sha256': digest(prior_path),
    'source_review_path': str(review_path), 'source_review_sha256': digest(review_path),
    'reviewed_files': fresh_reviewed,
    'git_command_executable': git_command, 'git_executable': str(git_path),
    'test_nodes': [node for group in group_nodes for node, _ in group],
    'expected_cases': sum(groups.values()), **groups,
    'seconds': 600, 'process_mib': 2048, 'job_mib': 3072,
    'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
    'threads': 1, 'import_mode': 'importlib',
    'model_creation_or_tensor_restore_permitted': False,
    'actual_input_or_selected_study_weights_used': False,
    'scientific_admission': False, 'original_case_attempts_remaining': 0,
}
with (RUN / 'pins.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write('\n')
print(json.dumps({
    'source_files': len(files), 'runtime_files': len(runtime), **groups,
    'expected_cases': pins['expected_cases'], 'launched': False,
    'pins_sha256': digest(RUN / 'pins.json'),
}))
