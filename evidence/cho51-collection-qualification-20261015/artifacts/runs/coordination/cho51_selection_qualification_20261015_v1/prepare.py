"""Prepare a fresh, separately pinned selection-file synthetic qualification."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
PRIOR = ROOT / 'runs/coordination/cho51_recorder_qualification_20261015_v1'
raw = (PRIOR / 'validate_003.py').read_text(encoding='utf-8')
changes = {
    'docs/phase2/cho51_recorder_collection_v1/test_collector_shared.py':
        'docs/phase2/cho51_selection_files_v1/test_selection_files.py',
    "results.items == 20": "results.items == 43",
    "'schema': 'cho51_recorder_synthetic_qualification_v1'":
        "'schema': 'cho51_selection_files_synthetic_qualification_v1'",
}
for old, new in changes.items():
    if raw.count(old) != 1:
        raise ValueError('ambiguous reviewed runner transform: ' + old)
    raw = raw.replace(old, new)
with (RUN / 'validate.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(raw)
pins = json.loads((PRIOR / 'pins_003.json').read_bytes())
pins['schema'] = 'cho51_selection_files_fresh_pins_v1'
pins['prepared_utc'] = datetime.now(timezone.utc).isoformat()
pins['scope'] = '43 fabricated policy and selection-file checks; no arrays, weights or numerical selector'
pins['preparation_note'] = 'Independently source-reviewed successor; exact1020 retained identities and independently pinned5253 policy.'
for path in [*sorted((ROOT / 'docs/phase2/cho51_selection_files_v1').glob('*')),
             RUN / 'validate.py', Path(__file__)]:
    if path.is_file():
        pins['files'][path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
for rel, expected in pins['files'].items():
    if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected:
        raise ValueError('source changed before preparation: ' + rel)
with (RUN / 'pins.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'fresh_files': len(pins['files']), 'prepared_cases': 43, 'tests_executed': False}))
