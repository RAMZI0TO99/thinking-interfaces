"""Pin current source/runtime for finite synthetic checks; no arrays/models read."""
import ast
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import source_check

canonical = source_check(ROOT)
prior = json.loads((ROOT / 'runs/coordination/cho51_real_collection_20261015_v1/pins.json').read_bytes())
files = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in prior['files']}
for path in [*(ROOT / 'docs/phase2/cho51_publication_collection_v1').glob('*'),
             *RUN.glob('*.py'), *RUN.glob('*.ps1')]:
    if path.is_file():
        files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()

def cases(path, excluded=()):
    nodes = []
    for node in ast.parse(path.read_bytes()).body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith('test_') or node.name in excluded:
            continue
        count = 1
        for mark in node.decorator_list:
            if isinstance(mark, ast.Call) and isinstance(mark.func, ast.Attribute) and mark.func.attr == 'parametrize':
                count *= len(ast.literal_eval(mark.args[1]))
        nodes.append((path.relative_to(ROOT).as_posix() + '::' + node.name, count))
    return nodes

boundary = cases(ROOT / 'docs/phase2/cho51_publication_collection_v1/test_collection.py')
hybrid = [row for row in boundary if row[0].endswith('::test_one_real_byte_verifier_composes_with_mocked_input_and_selection')]
physical = cases(ROOT / 'tests/test_phase2_cho_selected_manifest_bridge.py', {
    'test_accepts_store_published_tiny_model', 'test_rejects_symlinked_weights_if_supported',
})
if not boundary or sum(row[1] for row in physical) != 25 or sum(row[1] for row in hybrid) != 2:
    raise ValueError('explicit composition suite,2 hybrid and25 physical-byte cases required')
runtime = {}
for path in (Path(sys.executable), Path(sys.base_prefix) / 'python.exe',
             Path(sys.base_prefix) / 'python312.dll', Path(sys.base_prefix) / 'python3.dll'):
    if path.is_file():
        runtime[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
pins = {
    'schema': 'cho51_publication_synthetic_fresh_pins_v1',
    'prepared_utc': datetime.now(timezone.utc).isoformat(),
    'files': files, 'runtime': runtime, 'canonical_source_sha256': canonical,
    'test_nodes': [row[0] for row in boundary + physical],
    'boundary_cases': sum(row[1] for row in boundary),
    'dependency_mocked_boundaries': sum(row[1] for row in boundary) - 2,
    'hybrid_composition_cases': 2,
    'publication_byte_cases': 25,
    'expected_cases': sum(row[1] for row in boundary + physical),
    'seconds': 600, 'process_mib': 2048, 'job_mib': 3072,
    'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
    'threads': 1, 'scientific_admission': False, 'selected_tensors_verified': False,
    'actual_inputs_or_weights_read': False, 'original_case_attempts_remaining': 0,
}
with (RUN / 'pins.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'source_files': len(files), 'runtime_files': len(runtime),
                  'boundary_cases': pins['boundary_cases'], 'publication_byte_cases':25,
                  'expected_cases': pins['expected_cases'], 'launched': False}))
