"""Prepare untouched004 paths after preserving the isolated-child cache refusal."""
import ast
from pathlib import Path

RUN = Path(__file__).resolve().parent
variants = {
    'validate_004.py': (RUN / 'validate_003.py').read_text(encoding='utf-8').replace("RUN / 'case_003'", "RUN / 'case_004'"),
    'prepare_004.py': (RUN / 'prepare_003.py').read_text(encoding='utf-8').replace("RUN / 'pins_003.json'", "RUN / 'pins_004.json'"),
    'launch_004.ps1': (RUN / 'launch_003.ps1').read_text(encoding='utf-8').replace('pins_003.json', 'pins_004.json').replace('validation_003', 'validation_004').replace('validate_003.py', 'validate_004.py'),
}
for name, text in variants.items():
    if name.endswith('.py'):
        ast.parse(text)
    with (RUN / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
print('Fresh004 source/pins/output/case paths prepared; no launch.')
