import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

root=Path.cwd();run=Path(__file__).resolve().parent
folder=root/'docs/phase2/cho51_worker_bridge_v1'
source=(folder/'validate_bridge.py').read_text(encoding='utf-8')
source=source.replace("def audit(event,values):\n", '''def normalize_path(value):
    text=os.fsdecode(value)
    if text.startswith('\\\\\\\\?\\\\') and len(text)>6 and text[4].isalpha() and text[5]==':' and text[6]=='\\\\':
        text=text[4:]
    return Path(text).resolve()

def audit(event,values):
''')
source=source.replace('Path(os.fsdecode(values[0])).resolve()','normalize_path(values[0])')
source=source.replace('Path(os.fsdecode(value)).resolve()','normalize_path(value)')
source=source.replace("sys.addaudithook(audit)\n", "assert normalize_path('\\\\\\\\?\\\\'+str(ROOT))==ROOT.resolve()\nsys.addaudithook(audit)\n")
destination=folder/'validate_bridge_002.py'
compile(source,str(destination),'exec')
with destination.open('x',encoding='utf-8',newline='\n') as stream:stream.write(source)
pins=json.loads((run/'pins_001.json').read_bytes())
pins['prepared_utc']=datetime.now(timezone.utc).isoformat()
pins['files'][destination.relative_to(root).as_posix()]=hashlib.sha256(destination.read_bytes()).hexdigest()
pins['prior_failed_guard']='runs/migration/20261013T081749Z_c1c75145d6'
pins['scope_unchanged_extended_local_drive_prefix_normalized']=True
with (run/'pins_002.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(pins,stream,sort_keys=True,indent=2)
print(json.dumps({'successor':str(destination),'data_paths':len(pins['data_files']),'file_pins':len(pins['files']),'new_allowed_data_paths':0}))
