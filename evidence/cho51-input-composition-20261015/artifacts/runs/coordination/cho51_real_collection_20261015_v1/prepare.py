"""Pin current actual inputs by declared SHA/stat; actual hashes run inside guard."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
previous = json.loads((ROOT / 'runs/coordination/cho51_selection_qualification_20261015_v1/pins_003.json').read_bytes())
files = {}
source = json.loads((ROOT / 'tools/migration/source-files.json').read_bytes())
for row in source['files']:
    actual = hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest()
    if actual != row['sha256']:
        raise ValueError('canonical source changed: ' + row['path'])
    files[row['path']] = actual
for rel in previous['files']:
    # Recompute current preparation-time identities, rather than reusing a grant.
    path = ROOT / rel
    files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
cohort_rel = 'runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json'
cohort_raw = (ROOT / cohort_rel).read_bytes()
retained = json.loads((ROOT / 'runs/coordination/cho51_execution_interfaces_20261013_v1/pins_002.json').read_bytes())
if hashlib.sha256(cohort_raw).hexdigest() != retained['input_route_pins']['cohort_audit_sha256']:
    raise ValueError('retained cohort declaration changed')
data = {}
for row in json.loads(cohort_raw)['rows']:
    subject = row['subject']
    data[f'data/processed/cho2017/profile_a/{subject}.npz'] = row['profile_a_sha256']
    data[f'data/processed/cho2017/profile_b_60hz_v1/{subject}.npz'] = row['variant_artifact_sha256']
    data[f'data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json'] = row['variant_manifest_sha256']
if len(data) != 156:
    raise ValueError('exact52 A/B/manifest inventory required')
stats = {}
for rel in data:
    path = ROOT / rel
    if path.resolve() != path or not path.is_file():
        raise ValueError('actual input aliases another path')
    stat = path.stat()
    stats[rel] = {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
bindings = 'runs/coordination/cho51_episode_bindings_20261013_v1/validation_001/all_bindings.json'
templates = 'runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json'
for path in [*sorted((ROOT / 'docs/phase2/cho51_input_collection_v1').glob('*')),
             RUN / 'validate.py', RUN / 'test_real_inputs.py', RUN / 'prepare_validator.py', Path(__file__),
             ROOT / cohort_rel, ROOT / bindings, ROOT / templates]:
    if path.is_file():
        files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
runtime = {}
for path in (Path(sys.executable), Path(sys.base_prefix) / 'python.exe',
             Path(sys.base_prefix) / 'python312.dll', Path(sys.base_prefix) / 'python3.dll'):
    if path.is_file():
        runtime[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
pins = {
    'schema': 'cho51_actual_input_fabricated_record_fresh_pins_v1',
    'prepared_utc': datetime.now(timezone.utc).isoformat(),
    'files': files, 'runtime': runtime, 'canonical_source_sha256': source['source_sha256'],
    'data_files': data, 'prepared_data_stats': stats,
    'retained_bindings': bindings, 'candidate_templates': templates,
    'input_route_pins': {
        'protocol_config_sha256': files['configs/phase2/protocol.toml'],
        'threshold_config_sha256': files['configs/benchmark.toml'],
        'cohort_audit_sha256': files[cohort_rel],
        'variant_config_sha256': files['configs/phase2/cho_profile_b_60hz.toml'],
    },
    'synthetic_recorder_relative': 'runs/phase2/fabricated_cho51_input_20261015_v1',
    'actual_data_hashes_must_be_verified_inside_guard': True,
    'retained_B_bindings_referenced_not_redecoded': True,
    'seconds': 600, 'process_mib': 2048, 'job_mib': 3072,
    'startup_ram_gib': 10, 'active_ram_gib': 4, 'disk_gib': 20,
    'threads': 1, 'scientific_admission': False, 'original_case_attempts_remaining': 0,
}
if (ROOT / pins['synthetic_recorder_relative']).exists():
    raise ValueError('synthetic recorder scope must be unused')
with (RUN / 'pins.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'source_files': len(files), 'actual_data_files': len(data),
                  'declared_data_bytes': sum(row['bytes'] for row in stats.values()),
                  'large_inputs_hashed_during_preparation': False}))
