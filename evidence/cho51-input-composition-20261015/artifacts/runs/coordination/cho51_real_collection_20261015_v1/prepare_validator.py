"""Prepare a fresh actual-input/fabricated-record guard child from reviewed runner."""
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
raw = (ROOT / 'runs/coordination/cho51_recorder_qualification_20261015_v1/validate_003.py').read_text(encoding='utf-8')

def change(old, new, count=1):
    global raw
    if raw.count(old) != count:
        raise ValueError('ambiguous reviewed runner change: ' + old[:80])
    raw = raw.replace(old, new)

change('OUT.mkdir(exist_ok=False)', '''OUT.mkdir(exist_ok=False)
FIXTURE = (ROOT / pins['synthetic_recorder_relative']).resolve()
if FIXTURE != ROOT / 'runs/phase2/fabricated_cho51_input_20261015_v1' or FIXTURE.exists():
    raise ValueError('unused exact synthetic recorder root required')
FIXTURE.mkdir(parents=True, exist_ok=False)
allowed_data = {ROOT / rel for rel in pins['data_files']}''')
change("if writing and not path.is_relative_to(OUT):",
       "if writing and not (path.is_relative_to(OUT) or path.is_relative_to(FIXTURE)):")
change("if not writing and not path.is_relative_to(OUT):",
       "if not writing and not (path.is_relative_to(OUT) or path.is_relative_to(FIXTURE) or path in allowed_data):")
change("if not path.is_relative_to(OUT) and not (event == 'os.mkdir' and path.is_dir()):",
       "if not (path.is_relative_to(OUT) or path.is_relative_to(FIXTURE)) and not (event == 'os.mkdir' and path.is_dir()):")
old = '''    if not Path(root).resolve().is_relative_to(OUT):
        refuse('real_recorder_constructor', root)
    if output_root is not None and not Path(output_root).resolve().is_relative_to(OUT):
        refuse('real_recorder_constructor', output_root)'''
new = '''    root_path = Path(root).resolve()
    output_path = None if output_root is None else Path(output_root).resolve()
    controlled = root_path == ROOT and output_path == FIXTURE
    temporary = root_path.is_relative_to(OUT) and (output_path is None or output_path.is_relative_to(OUT))
    if not (controlled or temporary):
        refuse('nonfixture_recorder_constructor', root)'''
change(old, new)
change('import pytest\n', '''verified_data = {}
for rel, expected in pins['data_files'].items():
    path = ROOT / rel
    stat = path.stat()
    if {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns} != pins['prepared_data_stats'][rel]:
        raise ValueError('actual input stat changed: ' + rel)
    if digest(path) != expected:
        raise ValueError('actual input hash changed: ' + rel)
    verified_data[rel] = {'sha256': expected, 'bytes': stat.st_size}
print('All156 current actual input hashes matched; running24 boundary and4 hybrid cases.', flush=True)
import pytest
''')
change("str(ROOT / 'docs/phase2/cho51_recorder_collection_v1/test_collector_shared.py'),",
       "str(ROOT / 'docs/phase2/cho51_input_collection_v1/test_collection.py'),\n    str(RUN / 'test_real_inputs.py'),")
change('results.items == 20', 'results.items == 28')
change("'schema': 'cho51_recorder_synthetic_qualification_v1'",
       "'schema': 'cho51_actual_input_fabricated_record_composition_qualification_v1'")
change("'fixture_asset_loader_replaced': True, 'real_input_composition_qualified': False,",
       "'actual_input_loader_replaced': False, 'actual_input_fabricated_record_composition_qualified': qualified,\n    'actual_recorder_history_verified': False, 'retained_B_bindings_referenced_not_redecoded': True,\n    'actual_data_files_verified': verified_data, 'fabricated_metrics_not_scientific_results': True,")
change('loaded = {}', '''for rel, expected in pins['data_files'].items():
    path = ROOT / rel
    stat = path.stat()
    if {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns} != pins['prepared_data_stats'][rel] or digest(path) != expected:
        raise ValueError('actual input changed across composition: ' + rel)
loaded = {}''')
raw = raw.replace('synthetic qualification denied:', 'actual-input composition qualification denied:')
with (RUN / 'validate.py').open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(raw)
print('Prepared new actual-input validator; no tests or input decoding executed.')
