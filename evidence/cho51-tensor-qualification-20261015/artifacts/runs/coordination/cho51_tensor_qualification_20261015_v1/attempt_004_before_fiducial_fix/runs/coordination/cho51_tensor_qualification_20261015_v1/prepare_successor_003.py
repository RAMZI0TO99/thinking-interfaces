"""Prepare fresh attempt003; preserve the blocked IPv6 import-probe refusal."""
import ast
from pathlib import Path

RUN = Path(__file__).resolve().parent
validator = (RUN / 'validate_002.py').read_text(encoding='utf-8').replace("RUN / 'case_002'", "RUN / 'case_003'")
old = '''expected_denials = [d for d in denied if d['event'] == 'socket.bind'
                   and "'::1', 0" in d['detail'] and any(
                       f['function'] == '_has_ipv6' and Path(f['file']).resolve() == connection
                       for f in d['frames'])]'''
new = '''expected_denials = [d for d in denied if d['event'] == 'socket.__new__'
                   and ', 23, 1, 0)' in d['detail'] and any(
                       f['function'] == '_has_ipv6' and Path(f['file']).resolve() == connection
                       for f in d['frames'])]'''
if validator.count(old) != 1:
    raise ValueError('exact pinned optional probe classification predecessor required')
validator = validator.replace(old, new)
validator = validator.replace('and fixture_scope is not None and not denied and not unexpected',
                               'and fixture_scope is not None and not unexpected')
preparation = (RUN / 'prepare_002.py').read_text(encoding='utf-8').replace("RUN / 'pins_002.json'", "RUN / 'pins_003.json'")
preparation = preparation.replace("nodes, count = [], 0", "probe = ROOT / '.venv/Lib/site-packages/urllib3/util/connection.py'\nfiles[probe.relative_to(ROOT).as_posix()] = hashlib.sha256(probe.read_bytes()).hexdigest()\nnodes, count = [], 0")
launch = (RUN / 'launch_002.ps1').read_text(encoding='utf-8').replace('pins_002.json', 'pins_003.json').replace('validation_002', 'validation_003').replace('validate_002.py', 'validate_003.py')
for name, text in {'validate_003.py': validator, 'prepare_003.py': preparation, 'launch_003.ps1': launch}.items():
    if name.endswith('.py'):
        ast.parse(text)
    with (RUN / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
print('Fresh003 source/pins/output/case paths prepared; no launch.')
