"""Pin settled tensor source/tests/runtime using only standard-library preparation."""
import ast
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / 'tools/migration'))
from common import source_check

canonical = source_check(ROOT)
previous = json.loads((ROOT / 'runs/coordination/cho51_publication_qualification_20261015_v1/pins.json').read_bytes())
files = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in previous['files']}
for path in [*(ROOT / 'docs/phase2/cho51_tensor_verification_v1').glob('*'), *RUN.glob('*.py'), *RUN.glob('*.ps1')]:
    if path.is_file():
        files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
probe = ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'
files[probe.relative_to(ROOT).as_posix()] = hashlib.sha256(probe.read_bytes()).hexdigest()
nodes, count = [], 0
contract_tree = ast.parse((ROOT / 'docs/phase2/cho51_tensor_verification_v1/contract.py').read_bytes())
symbols = {target.id: node.value for node in contract_tree.body if isinstance(node, ast.Assign)
           for target in node.targets if isinstance(target, ast.Name)}

def parameter_count(node):
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return sum(parameter_count(value.value) if isinstance(value, ast.Starred) else 1 for value in node.elts)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'C':
        return parameter_count(symbols[node.attr])
    if isinstance(node, ast.Name) and node.id in symbols:
        return parameter_count(symbols[node.id])
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'sorted', 'frozenset', 'tuple', 'list'}:
        return parameter_count(node.args[0])
    raise ValueError('unsupported static parameter roster: ' + ast.dump(node))

for path in (ROOT / 'docs/phase2/cho51_tensor_verification_v1').glob('test_*.py'):
    for node in ast.parse(path.read_bytes()).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            cases = 1
            for mark in node.decorator_list:
                if isinstance(mark, ast.Call) and isinstance(mark.func, ast.Attribute) and mark.func.attr == 'parametrize':
                    cases *= parameter_count(mark.args[1])
            nodes.append(path.relative_to(ROOT).as_posix() + '::' + node.name)
            count += cases
git_command_executable = shutil.which('git')
git = str(Path(git_command_executable).resolve())
runtime = {}
for path in (Path(sys.executable), Path(sys.base_prefix) / 'python.exe', Path(sys.base_prefix) / 'python312.dll', Path(sys.base_prefix) / 'python3.dll', Path(git)):
    if path.is_file():
        runtime[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
pins = dict(schema='cho51_tensor_contract_fixture_fresh_pins_v1', prepared_utc=datetime.now(timezone.utc).isoformat(),
    files=files, runtime=runtime, canonical_source_sha256=canonical, git_executable=git,
    git_command_executable=git_command_executable,
    test_nodes=nodes, expected_cases=count, seconds=600, process_mib=2048, job_mib=3072,
    startup_ram_gib=10, active_ram_gib=4, disk_gib=20, threads=1,
    fixture_model_is_untrained=True, scientific_admission=False, original_case_attempts_remaining=0)
with (RUN / 'pins_003.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'files':len(files), 'runtime':len(runtime), 'prepared_cases':count,
                  'pins_sha256':hashlib.sha256((RUN / 'pins_003.json').read_bytes()).hexdigest(), 'launched':False}))
