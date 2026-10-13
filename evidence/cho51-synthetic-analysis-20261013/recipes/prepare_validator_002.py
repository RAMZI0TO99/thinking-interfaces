import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

root=Path.cwd()
folder=root/'docs/phase2/cho_51_target_analysis_candidate'
run=root/'runs/coordination/cho51_synthetic_analysis_20261013_v1'
source=(folder/'validate_analysis.py').read_text(encoding='utf-8')
source=source.replace('import time\n','import time\nimport traceback\nimport threading\n')
source=source.replace('denied = []\n', "denied = []\nexpected_denials = []\nplatform_path = Path(sys.base_prefix)/'Lib/platform.py'\nplatform_sha = 'f5ff83f15c841792be42709a6710dc8d7a9f72791c1ae4cad719b1fb0abe0a05'\nassert hashlib.sha256(platform_path.read_bytes()).hexdigest() == platform_sha\n")
source=source.replace("def audit(event, values):\n", '''def audit(event, values):
    if event == 'socket.gethostname':
        stack = traceback.extract_stack(limit=16)
        caller = stack[-2]
        record = {'event':event,'denied':True,'callsite':[{'file':f.filename,'line':f.lineno,'function':f.name} for f in stack],'caller_sha256':hashlib.sha256(Path(caller.filename).read_bytes()).hexdigest()}
        if not values and Path(caller.filename).resolve() == platform_path.resolve() and caller.name == '_node' and record['caller_sha256'] == platform_sha and not expected_denials:
            expected_denials.append(record)
        else:
            denied.append(record)
        raise PermissionError('all socket operations remain blocked')
    if event == 'import' and values[0].split('.')[0] in {'torch','mne','moabb','safetensors','encoder','adaptation','data'}:
        denied.append({'event':event,'module':values[0]})
        raise PermissionError('model or data import refused')
''')
source=source.replace("refused = refused or path.suffix.lower()", "if not writing and path.is_relative_to(ROOT) and not (path.is_relative_to(ROOT/'.venv/Lib/site-packages') or path.is_relative_to(OUT) or path in {ROOT/rel for rel in pins['files']}):\n            refused = True\n        refused = refused or path.suffix.lower()")
source=source.replace("{'os.remove','os.rmdir','os.mkdir','os.rename','os.replace'}", "{'os.remove','os.rmdir','os.mkdir','os.rename','os.replace','os.link','os.symlink','os.chmod','os.utime','os.truncate'}")
source=source.replace("{'os.rename','os.replace'} else", "{'os.rename','os.replace','os.link','os.symlink'} else")
source=source.replace("assert denied == []\nloaded={}", "assert denied == [] and len(expected_denials) == 1\nassert threading.active_count() == 1\nfrom threadpoolctl import threadpool_info\npools = threadpool_info()\nassert pools and all(item['num_threads'] == 1 for item in pools)\nloaded={}")
source=source.replace("'denied_operations':denied,", "'denied_operations':denied,'expected_blocked_local_hostname_probes':expected_denials,'actual_native_threadpools':pools,'active_python_threads':threading.active_count(),")
destination=folder/'validate_analysis_002.py'
compile(source,str(destination),'exec')
with destination.open('x',encoding='utf-8',newline='\n') as stream: stream.write(source)
pins=json.loads((run/'validation_pins_001.json').read_bytes())
pins['prepared_utc']=datetime.now(timezone.utc).isoformat()
pins['files'][destination.relative_to(root).as_posix()]=hashlib.sha256(destination.read_bytes()).hexdigest()
pins['expected_platform_source_sha256']='f5ff83f15c841792be42709a6710dc8d7a9f72791c1ae4cad719b1fb0abe0a05'
pins['prior_failed_validation_retained']='runs/migration/20261013T070950Z_49b65d2194'
with (run/'validation_pins_002.json').open('x',encoding='utf-8',newline='\n') as stream: json.dump(pins,stream,indent=2,sort_keys=True)
print(json.dumps({'validator':str(destination),'pinned_files':len(pins['files']),'all_sockets_remain_blocked':True}))
