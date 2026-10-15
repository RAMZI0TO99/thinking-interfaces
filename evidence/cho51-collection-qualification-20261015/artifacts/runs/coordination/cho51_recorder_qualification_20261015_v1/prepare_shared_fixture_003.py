"""Preserve invoked tests; prepare identical cases with one restored module fixture."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
source = ROOT / 'docs/phase2/cho51_recorder_collection_v1/test_collector.py'
raw = source.read_text(encoding='utf-8')
start = raw.index('@pytest.fixture\ndef collect(')
end = raw.index('\n\ndef test_complete_', start)
fixture = raw[start:end]
split = fixture.index('    calls = []')
build = fixture[:split]
build = build.replace('@pytest.fixture\ndef collect(synthetic_inputs, monkeypatch):\n    f = synthetic_inputs',
    "@pytest.fixture(scope='module')\ndef prepared(tmp_path_factory):\n    fixture_patches = pytest.MonkeyPatch()\n    f = LEGACY.synthetic_inputs.__wrapped__(\n        tmp_path_factory.mktemp('shared_fabricated_recorder'), fixture_patches,\n    )")
build += '''    try:
        yield SimpleNamespace(f=f, root=root, route=route, methods=methods,
                              published=published, recorder=recorder)
    finally:
        fixture_patches.undo()


@pytest.fixture
def collect(prepared, monkeypatch):
    f, root, route = prepared.f, prepared.root, prepared.route
    methods, published, recorder = prepared.methods, prepared.published, prepared.recorder
    # Restore only the explicit mutation surfaces after every test. Assertions
    # and all1020 immutable independent pins are the same as the original suite.
    paths = [recorder.output_root / 'cells' / f'{pin.identity.sha256}.json'
             for method in ('eegnet', 'labram_linear', 'labram_lora', 'labram_full')
             for pin in [next(p for p in published if p.plan.method == method)]]
    paths += [recorder.output_root / 'successes' / f'{published[0].plan.case_id}.success.json',
              root / 'data/processed/cho2017/profile_b_60hz_v1/subject_01.manifest.json']
    original = {path: path.read_bytes() for path in paths}
'''
rest = fixture[split:]
return_start = rest.index('    return SimpleNamespace(')
rest = rest[:return_start] + '''    try:
        yield SimpleNamespace(invoke=invoke, calls=calls, f=f, pins=published,
                              recorder=recorder, root=root, methods=methods)
    finally:
        for path, before in original.items():
            if not path.exists() or path.read_bytes() != before:
                path.write_bytes(before)
        for name in ('claims', 'cells', 'successes', 'publication_intents'):
            path = recorder.output_root / name / 'unlisted-subject01.json'
            if path.exists():
                path.unlink()
'''
destination = source.with_name('test_collector_shared.py')
with destination.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(raw[:start] + build + rest + raw[end:])
validate = (RUN / 'validate_002.py').read_text(encoding='utf-8')
old = 'docs/phase2/cho51_recorder_collection_v1/test_collector.py'
new = 'docs/phase2/cho51_recorder_collection_v1/test_collector_shared.py'
if validate.count(old) != 1:
    raise ValueError('unique pinned test target required')
with (RUN / 'validate_003.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(validate.replace(old, new))
pins = json.loads((RUN / 'pins_002.json').read_bytes())
pins['prepared_utc'] = datetime.now(timezone.utc).isoformat()
pins['predecessor_pins'] = 'pins_002.json'
pins['preparation_note'] = 'Same20 assertions; build1020 fabricated records once and restore six mutation surfaces after every test.'
for path in (destination, RUN / 'validate_003.py', Path(__file__)):
    pins['files'][path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
with (RUN / 'pins_003.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pins, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'fresh_files': len(pins['files']), 'prior_tests_unchanged': True}))
