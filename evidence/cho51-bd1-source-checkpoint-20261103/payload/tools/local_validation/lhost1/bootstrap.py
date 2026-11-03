"""Single isolated L bootstrap entry; source bytes must be pinned by caller.

Only standard-library bootstrap modules load before retained-reader protection.
All project sources execute verified bytes, never an import-path rediscovery.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import types

def raw_json(path,pin):
    with open(path,'rb') as stream:raw=stream.read(8*1024**2+1)
    if len(raw)>8*1024**2 or len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
        raise ValueError('bootstrap exact retained-reference bytes')
    def pairs(rows):
        value={}
        for key,item in rows:
            if key in value:raise ValueError('bootstrap duplicate JSON')
            value[key]=item
        return value
    return json.loads(raw.decode('utf-8','strict'),object_pairs_hook=pairs,
                      parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite bootstrap JSON')))

ORDER=(
 ('tools.local_validation.v1.records','tools/local_validation/v1/records.py'),
 ('tools.local_validation.l1.protocol','tools/local_validation/l1/protocol.py'),
 ('tools.local_validation.lp1.native_reader','tools/local_validation/lp1/native_reader.py'),
 ('tools.local_validation.lp1.manifest','tools/local_validation/lp1/manifest.py'),
 ('tools.local_validation.lp1.supervisor','tools/local_validation/lp1/supervisor.py'),
 ('tools.local_validation.l1.observation','tools/local_validation/l1/observation.py'),
 ('tools.local_validation.l1.guards','tools/local_validation/l1/guards.py'),
 ('tools.local_validation.l1.imports','tools/local_validation/l1/imports.py'),
 ('tools.local_validation.l1.collection','tools/local_validation/l1/collection.py'),
 ('tools.local_validation.l1.plan','tools/local_validation/l1/plan.py'),
 ('tools.local_validation.l1.native_bridge','tools/local_validation/l1/native_bridge.py'),
 ('tools.local_validation.l1.child_entry','tools/local_validation/l1/child_entry.py'),
 ('tools.local_validation.lhost1.authority','tools/local_validation/lhost1/authority.py'),
 ('tools.local_validation.lhost1.abi','tools/local_validation/lhost1/abi.py'),
 ('tools.local_validation.lhost1.runtime','tools/local_validation/lhost1/runtime.py'),
 ('tools.local_validation.lhost1.job_adapter','tools/local_validation/lhost1/job_adapter.py'),
 ('tools.local_validation.lhost1.transport','tools/local_validation/lhost1/transport.py'),
 ('tools.local_validation.lhost1.supervisor','tools/local_validation/lhost1/supervisor.py'),
)

def load(name,path,pin):
    with open(path,'rb') as stream:raw=stream.read(8*1024**2+1)
    if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
        raise ValueError('project bootstrap bytes differ')
    module=types.ModuleType(name);module.__file__=str(path);module.__package__=name.rpartition('.')[0]
    sys.modules[name]=module
    exec(compile(raw,str(path),'exec',dont_inherit=True),module.__dict__)
    parent,_,leaf=name.rpartition('.')
    setattr(sys.modules[parent],leaf,module)
    return module

def main():
    if len(sys.argv) not in (10,11) or sys.argv[1] not in ('parent','child'):
        raise ValueError('fixed L bootstrap vector')
    mode,request_path,request_size,request_sha,admission_path,admission_size,admission_sha,origin_utc,origin_ticks=sys.argv[1:10]
    # QPC/frequency are a single exact decimal pair, no new clock origin.
    qpc,frequency,caller_pid,caller_creation=map(int,origin_ticks.split(':'))
    request=raw_json(request_path,dict(bytes=int(request_size),sha256=request_sha))
    admission=raw_json(admission_path,dict(bytes=int(admission_size),sha256=admission_sha))
    manifest=raw_json(request['source_manifest']['path'],request['source_manifest'])
    if set(manifest)!={'schema','project_root','files'} or manifest['schema']!='cho51_l_source_manifest_v1':
        raise ValueError('closed source manifest')
    root=Path(manifest['project_root']);pins={r['path']:r for r in manifest['files']}
    if len(pins)!=len(manifest['files']):raise ValueError('source alias/duplicate')
    for name in ('tools','tools.local_validation','tools.local_validation.v1','tools.local_validation.lp1',
                 'tools.local_validation.l1','tools.local_validation.lhost1'):
        module=types.ModuleType(name);module.__package__=name;module.__path__=[];sys.modules[name]=module
        parent,_,leaf=name.rpartition('.')
        if parent:setattr(sys.modules[parent],leaf,module)
    for name,relative in ORDER:
        path=root/relative;load(name,path,pins[path.as_posix()])
    supervisor=sys.modules['tools.local_validation.lhost1.supervisor']
    origin=dict(utc=origin_utc,qpc=qpc,qpc_frequency=frequency)
    arguments=dict(request=request,admission=admission,origin=origin,manifest=manifest,
                   request_path=request_path,admission_path=admission_path,
                   admission_pin=dict(bytes=int(admission_size),sha256=admission_sha),
                   request_pin=dict(bytes=int(request_size),sha256=request_sha),
                   caller_identity=dict(process_id=caller_pid,creation_filetime=caller_creation))
    if mode=='parent':
        if len(sys.argv)!=10:raise ValueError('parent has no inherited report handle')
        return supervisor.parent(**arguments)
    if len(sys.argv)!=11:raise ValueError('child original report handle absent')
    return supervisor.child(report_handle=int(sys.argv[10]),**arguments)

if __name__=='__main__':raise SystemExit(main())
