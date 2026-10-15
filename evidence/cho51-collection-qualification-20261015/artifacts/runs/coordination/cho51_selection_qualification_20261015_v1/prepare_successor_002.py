"""Preserve failed tests; detach the candidate list through its mapping parent."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
source = ROOT / 'docs/phase2/cho51_selection_files_v1/test_selection_files.py'
raw = source.read_text(encoding='utf-8')
old = 'json.loads(canonical_config_json(context.templates[plan.method]["candidates"]))'
new = 'config_snapshot(context.templates[plan.method])["candidates"]'
if raw.count(old) != 1:
    raise ValueError('unique fixture-only mapping correction required')
successor = source.with_name('test_selection_files_002.py')
with successor.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(raw.replace(old, new))
validator = (RUN / 'validate.py').read_text(encoding='utf-8')
before = 'docs/phase2/cho51_selection_files_v1/test_selection_files.py'
after = 'docs/phase2/cho51_selection_files_v1/test_selection_files_002.py'
if validator.count(before) != 1:
    raise ValueError('unique qualification test target required')
with (RUN / 'validate_002.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(validator.replace(before, after))
pins = json.loads((RUN / 'pins.json').read_bytes())
pins['prepared_utc'] = datetime.now(timezone.utc).isoformat()
pins['predecessor_pins'] = 'pins.json'
pins['preparation_note'] = 'Fixture copied a list with a mapping-only configuration helper; successor detaches the mapping parent. Implementation, guard and43 assertions unchanged.'
for path in (successor, RUN / 'validate_002.py', Path(__file__),
             ROOT / 'runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json'):
    pins['files'][path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
with (RUN / 'pins_002.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'fresh_files': len(pins['files']), 'failed_attempt_preserved': True}))
