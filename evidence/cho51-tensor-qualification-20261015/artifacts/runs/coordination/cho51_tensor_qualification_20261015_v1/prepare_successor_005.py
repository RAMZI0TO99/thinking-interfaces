"""Prepare untouched005 paths with the exact installed MNE template pinned."""
import ast
from pathlib import Path

RUN = Path(__file__).resolve().parent
preparation = (RUN / 'prepare_004.py').read_text(encoding='utf-8').replace('pins_004.json', 'pins_005.json')
preparation = preparation.replace('nodes, count = [], 0', "fiducials = ROOT / '.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif'\nfiles[fiducials.relative_to(ROOT).as_posix()] = hashlib.sha256(fiducials.read_bytes()).hexdigest()\nnodes, count = [], 0")
variants = {
    'validate_005.py': (RUN / 'validate_004.py').read_text(encoding='utf-8').replace("RUN / 'case_004'", "RUN / 'case_005'"),
    'prepare_005.py': preparation,
    'launch_005.ps1': (RUN / 'launch_004.ps1').read_text(encoding='utf-8').replace('pins_004.json', 'pins_005.json').replace('validation_004', 'validation_005').replace('validate_004.py', 'validate_005.py'),
}
for name, text in variants.items():
    if name.endswith('.py'):
        ast.parse(text)
    with (RUN / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
print('Fresh005 source/pins/output/case paths prepared; no launch.')
