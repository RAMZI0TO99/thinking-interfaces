"""Fresh source/runtime pins for one bounded synthetic recorder qualification."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent
manifest = json.loads((ROOT / 'tools/migration/source-files.json').read_bytes())
files = {}
for row in manifest['files']:
    actual = hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest()
    if actual != row['sha256']:
        raise ValueError('canonical source mismatch: ' + row['path'])
    files[row['path']] = actual
extra = [
    'docs/phase2/cho51_recorder_collection_v1/collector.py',
    'docs/phase2/cho51_recorder_collection_v1/test_collector.py',
    'docs/phase2/cho51_worker_bridge_v1/worker_bridge.py',
    'docs/phase2/cho51_execution_interfaces_v1/interfaces.py',
    'docs/phase2/cho51_route_candidate_v1/route_contract.py',
    'evidence/cho51-adoption-route-20261013/owner/adoption.json',
    'evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json',
    'evidence/phase2-readiness-20261012/worker/roster.json',
    '.venv/Lib/site-packages/urllib3/util/connection.py',
    '.venv/pyvenv.cfg',
    'runs/coordination/cho51_recorder_qualification_20261015_v1/prepare_pins.py',
    'runs/coordination/cho51_recorder_qualification_20261015_v1/validate.py',
]
for path in (ROOT / 'tools/migration').iterdir():
    if path.is_file() and path.suffix in {'.py', '.ps1', '.json', '.lock'}:
        extra.append(path.relative_to(ROOT).as_posix())
for rel in extra:
    files[rel] = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
runtime = {}
for path in (Path(sys.executable), Path(sys.base_prefix) / 'python.exe',
             Path(sys.base_prefix) / 'python312.dll', Path(sys.base_prefix) / 'python3.dll'):
    if path.is_file():
        runtime[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
pins = {
    'schema': 'cho51_recorder_synthetic_fresh_pins_v1',
    'prepared_utc': datetime.now(timezone.utc).isoformat(),
    'canonical_source_sha256': manifest['source_sha256'],
    'files': files, 'runtime': runtime,
    'scope': 'fabricated all52 metadata and1020 recorder cells; real asset loader replaced',
    'seconds': 600, 'process_mib': 2048, 'job_mib': 3072,
    'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
    'threads': 1, 'gpu_hidden': True, 'scientific_admission': False,
    'original_case_attempts_remaining': 0,
}
with (RUN / 'pins.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'fresh_files': len(files), 'runtime_files': len(runtime), 'tests_executed': False}))
