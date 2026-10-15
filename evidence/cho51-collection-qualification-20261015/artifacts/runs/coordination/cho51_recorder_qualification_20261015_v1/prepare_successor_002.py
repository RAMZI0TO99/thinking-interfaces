"""Preserve failed runner and bind pytest logs/capture to the owned output."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
before = (RUN / 'validate.py').read_bytes()
old = b"    '-q', '-p', 'no:cacheprovider', '-o', 'addopts=',"
new = b"    '-q', '-s', '-p', 'no:cacheprovider', '-o', 'addopts=',\n    '--log-file', str(OUT / 'pytest.log'),"
if before.count(old) != 1:
    raise ValueError('unique reviewed pytest command required')
with (RUN / 'validate_002.py').open('xb') as stream:
    stream.write(before.replace(old, new))
pins = json.loads((RUN / 'pins.json').read_bytes())
pins['prepared_utc'] = datetime.now(timezone.utc).isoformat()
pins['predecessor_pins'] = 'pins.json'
pins['predecessor_failure'] = 'pytest logging attempted outside-output NUL before any tests'
for path in (RUN / 'validate_002.py', Path(__file__)):
    pins['files'][path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
with (RUN / 'pins_002.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'fresh_files': len(pins['files']), 'old_attempt_preserved': True}))
