"""Create unused successors after the preserved installed-Git hardlink refusal."""
import ast
from pathlib import Path

RUN = Path(__file__).resolve().parent
variants = {
    'validate_002.py': (RUN / 'validate.py').read_text(encoding='utf-8').replace("RUN / 'case_001'", "RUN / 'case_002'"),
    'prepare_002.py': (RUN / 'prepare.py').read_text(encoding='utf-8').replace("RUN / 'pins.json'", "RUN / 'pins_002.json'"),
    'launch_002.ps1': (RUN / 'launch.ps1').read_text(encoding='utf-8').replace("'pins.json'", "'pins_002.json'").replace("'validation_001'", "'validation_002'").replace("'validate.py'", "'validate_002.py'"),
}
for name, value in variants.items():
    if name.endswith('.py'):
        ast.parse(value)
    with (RUN / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)
print('Fresh validation002/pins002/case002 launch prepared; no execution.')
