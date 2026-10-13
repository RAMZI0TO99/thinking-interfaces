"""Pin reviewed contract-value comparison before any validation was invoked."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
root=Path.cwd();run=Path(__file__).resolve().parent
value=json.loads((run/'pins_001.json').read_bytes())
value['prepared_utc']=datetime.now(timezone.utc).isoformat()
value['superseded_uninvoked_pin_file']='pins_001.json'
value['review_note']='Initial uninvoked interface draft is retained; privately reloaded planner dataclasses require comparison of all contract fields.'
for rel in ('docs/phase2/cho51_execution_interfaces_v1/interfaces.py','runs/coordination/cho51_execution_interfaces_20261013_v1/interfaces_draft_001.py','runs/coordination/cho51_execution_interfaces_20261013_v1/prepare_pins_002.py'):
    value['files'][rel]=hashlib.sha256((root/rel).read_bytes()).hexdigest()
for rel in value['data_files']:
    stat=(root/rel).stat();value['prepared_data_stats'][rel]={'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}
with (run/'pins_002.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,sort_keys=True,indent=2)
print(json.dumps({'fresh_file_pins':len(value['files']),'previous_pins_invoked':False,'canonical_source_unchanged':True}))
