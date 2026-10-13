"""Assemble without overwriting after README creation reserved the packet folder."""
from pathlib import Path
original=Path(__file__).with_name('assemble_evidence_001.py')
code=original.read_text(encoding='utf-8')
before="packet=root/'evidence/cho51-episode-bindings-20261013';packet.mkdir(exist_ok=False)"
assert code.count(before)==1
code=code.replace(before,"packet=root/'evidence/cho51-episode-bindings-20261013';assert {p.name for p in packet.iterdir()}=={'README.md'}")
before="'pins_001.json','assemble_evidence_001.py'"
assert code.count(before)==1
code=code.replace(before,"'pins_001.json','assemble_evidence_001.py','assemble_evidence_002.py'")
exec(compile(code,str(original),'exec'),{'__file__':str(original),'__name__':'__main__'})
