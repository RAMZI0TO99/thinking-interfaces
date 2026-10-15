"""Preserve failed Windows long-path fixture and prepare compact owned names."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
source = ROOT / 'docs/phase2/cho51_selection_files_v1/test_selection_files_002.py'
raw = source.read_text(encoding='utf-8')
changes = {
    'mktemp("fabricated_cho51_selection")': 'mktemp("s")',
    '("fabricated-" + uuid4().hex)': '("r" + uuid4().hex[:12])',
    '("fabricated-store-" + uuid4().hex)': '("f" + uuid4().hex[:12])',
}
for old, new in changes.items():
    if raw.count(old) != 1:
        raise ValueError('unique synthetic name transform required: ' + old)
    raw = raw.replace(old, new)
successor = source.with_name('test_selection_files_003.py')
with successor.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(raw)
validator = (RUN / 'validate_002.py').read_text(encoding='utf-8')
old = 'docs/phase2/cho51_selection_files_v1/test_selection_files_002.py'
new = 'docs/phase2/cho51_selection_files_v1/test_selection_files_003.py'
if validator.count(old) != 1:
    raise ValueError('unique test target required')
validator = validator.replace(old, new).replace("str(OUT / 'pytest-temp')", "str(OUT / 't')")
with (RUN / 'validate_003.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(validator)
pins = json.loads((RUN / 'pins_002.json').read_bytes())
pins['prepared_utc'] = datetime.now(timezone.utc).isoformat()
pins['predecessor_pins'] = 'pins_002.json'
pins['preparation_note'] = 'Compact generated fixture names stay below Windows MAX_PATH; same43 assertions and unchanged implementation/policy.'
for path in (successor, RUN / 'validate_003.py', Path(__file__)):
    pins['files'][path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
with (RUN / 'pins_003.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'fresh_files': len(pins['files']), 'old_fixture_receipts_preserved': True}))
