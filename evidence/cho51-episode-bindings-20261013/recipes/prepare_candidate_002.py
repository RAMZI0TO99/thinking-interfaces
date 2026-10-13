"""Finish pin preparation after the first recipe's ambiguous text-match refusal."""
from pathlib import Path

original=Path(__file__).with_name('prepare_candidate_001.py')
code=original.read_text(encoding='utf-8')
before="candidate.mkdir(exist_ok=False)"
assert code.count(before)==1
code=code.replace(before,"assert candidate.is_dir()")
before="with (candidate/'validate_bindings.py').open('x',encoding='utf-8',newline='\\n') as stream:stream.write(code)"
assert code.count(before)==1
code=code.replace(before,"assert (candidate/'validate_bindings.py').read_bytes()==code.encode('utf-8')")
before='prep = change(prep, "\'sample_raw_source\':raw_rel", "\'raw_sources\':raw_sources,\'sample_raw_source\':raw_rel")'
assert code.count(before)==1
code=code.replace(before,'prep = change(prep, "\'sample_raw_source\':raw_rel,\'sample_raw_source_sha256\'", "\'raw_sources\':raw_sources,\'sample_raw_source\':raw_rel,\'sample_raw_source_sha256\'")')
before="'runs/coordination/cho51_episode_bindings_20261013_v1/prepare_pins_001.py','evidence/"
assert code.count(before)==1
code=code.replace(before,"'runs/coordination/cho51_episode_bindings_20261013_v1/prepare_pins_001.py','runs/coordination/cho51_episode_bindings_20261013_v1/prepare_candidate_002.py','evidence/")
exec(compile(code,str(original),'exec'),{'__file__':str(original),'__name__':'__main__'})
