"""Production L parent/child composition over retained P inputs.

The external managed caller owns this supervisor. This source does not create
an admission, accept itself, launch old runners or execute candidate test bodies.
"""
import ctypes
import hashlib
import os
from pathlib import Path
import sys
import threading
import time
import types
from datetime import datetime,timedelta,timezone
from ..l1.protocol import need,closed,ref,encode,decode,FrameWriter,SAFETY,COUNTERS
from ..l1.plan import validate_groups,validate_policies
from ..l1.child_entry import VerifiedContext,run_child
from ..l1.native_bridge import NativeObserver
from ..l1.observation import ABI_SCOPE
from ..lp1.native_reader import RetainedReader,RetainedOutputs
from ..lp1.manifest import expand
from ..lp1.supervisor import Guard,absent
from .authority import validate,validate_chain,enrich,retain_chain,manifest_map,validate_plan_acceptance,evidence_ref
from .runtime import Runtime
from .transport import ObservationReceiver,new_state,install_transport,lifecycle_ok
from . import job_adapter

def scope_safety():
    return dict(zip(SAFETY,[False]*5+[0,0]))

def pinned_json(reader,reference):
    retained='native_identity' in reference
    ref(reference,retained=retained)
    pin={k:reference[k] for k in ('bytes','sha256')}
    if retained:
        need(reader.retain(reference['path'],pin)['native_identity']==reference['native_identity'],'plan JSON original retained identity before read')
    value=decode(reader.read_small(reference['path'],pin))
    if retained:
        need(reader.retain(reference['path'],pin)['native_identity']==reference['native_identity'],'plan JSON original retained identity after read')
    return value

def physical_inputs(reader,index):
    need(index['schema']=='cho51_p2_physical_index_v1','accepted physical index schema')
    files={};censuses=[];absences=[]
    for page in index['pages']:
        closed(page,'kind path bytes sha256 rows')
        need(page['kind'] in ('files','census','absences'),'P page kind')
        value=decode(reader.read_small(page['path'],{k:page[k] for k in ('bytes','sha256')}))
        closed(value,'schema rows')
        need(value['schema']=='cho51_p2_'+page['kind']+'_page_v1' and len(value['rows'])==page['rows'],'P page count/schema')
        if page['kind']=='files':
            for row in value['rows']:
                closed(row,'file selectors roles');descriptor=row['file'];path=descriptor['path']
                need(path not in files,'duplicate P physical input');files[path]=descriptor
        elif page['kind']=='census':censuses.extend(value['rows'])
        else:absences.extend(value['rows'])
    need(len(files)==index['files'] and sum(r['bytes'] for r in files.values())==index['total_bytes'],'P exact files/bytes')
    need(len(files)<=25000 and sum(r['bytes'] for r in files.values())<=4*1024**3,'P input envelope')
    return files,censuses,absences

def prepare(request,admission,origin,manifest,request_path,admission_path,request_pin,admission_pin):
    validate(request,admission,origin)
    plan_ref=request['plan']
    cache=Path(request['environment']['PYTHONPYCACHEPREFIX'])
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode
         and str(sys.pycache_prefix).replace('\\','/')==str(cache).replace('\\','/'),'isolated no-site no-bytecode bootstrap')
    guard=Guard(origin['utc'],origin['qpc'],origin['qpc_frequency'],cache)
    reader=RetainedReader(guard.checkpoint)
    try:
        # Ordinary reader retains every bootstrap source before admission chain
        # or plan-dependent child effects. No path-only code identity survives.
        for reference in manifest['files']:
            reader.retain(reference['path'],{k:reference[k] for k in ('bytes','sha256')})
        need(decode(reader.read_small(request_path,request_pin))==request and decode(reader.read_small(admission_path,admission_pin))==admission,
             'original request/admission retained bytes')
        need(admission['request']['path']==request_path and all(admission['request'][k]==request_pin[k] for k in ('bytes','sha256')),'actual request ref join')
        controls=retain_chain(request,admission,lambda reference:pinned_json(reader,reference))
        need(manifest_map(manifest)==manifest_map(controls[request['source_manifest']['path']]),'actually loaded bootstrap manifest equals retained control')
        validate_chain(request,admission,controls)
        runtime=controls[request['runtime_manifest']['path']]
        closed(runtime,'schema root executable files census')
        need(runtime['schema']=='cho51_l_runtime_manifest_v1' and runtime['executable']==Path(sys.executable).as_posix(),'current exact interpreter')
        for reference in runtime['files']:reader.retain(reference['path'],{k:reference[k] for k in ('bytes','sha256')})
        static=controls[plan_ref['path']]
        closed(static,'schema groups policies bindings')
        need(static['schema']=='cho51_l_static_execution_plan_v1','static implementation plan')
        accepted_plans=[r for r in request['control_inputs'] if r['role']=='plan_acceptance']
        need(len(accepted_plans)==1,'separate accepted complete plan required before L')
        acceptance=controls[accepted_plans[0]['path']]
        plan_review=pinned_json(reader,evidence_ref(acceptance['review']))
        derivation=pinned_json(reader,evidence_ref(acceptance['derivation']))
        validate_plan_acceptance(request,acceptance,plan_review,derivation)
        index=controls[request['preparation_index']['path']]
        physical,censuses,absences=physical_inputs(reader,index)
        plan=enrich(static,physical,reader,guard.checkpoint)
        validate_groups(plan['groups']);validate_policies(plan['policies'],plan['groups'])
        bindings=plan['bindings']
        recipe=pinned_json(reader,bindings['preparation_recipe'])
        selection=expand(recipe,reader,bindings['preparation_extra_paths'])
        need({row['path'] for row in selection.files.values()}==set(physical),'new P exact preparation recipe union')
        current_census=[dict(selector=selector,root=root,path=path,directory=directory)
                       for selector,root,rows in selection.censuses for path,directory in rows]
        need(current_census==censuses and list(selection.absences)==absences,'current complete P census/absence')
        for path,expected in physical.items():
            current=reader.retain(path,{k:expected[k] for k in ('bytes','sha256')})
            need(current==expected,'fresh full P physical identity')
        samples=[guard.sample()];time.sleep(.21);guard.checkpoint();samples.append(guard.sample())
        return guard,reader,controls,plan,physical,selection,samples
    except BaseException:
        guard.enter_cleanup();reader.checkpoint=lambda:True;reader.close();guard.stop_watchdog.set();guard.watchdog.join(.5)
        raise

def load_primitive(manifest,reader):
    root=manifest['project_root'];path=root+'/evaluation/phase2_supervision_primitives.py'
    references=[r for r in manifest['files'] if r['path']==path];need(len(references)==1,'pinned supervision primitive')
    raw=reader.read_small(path,{k:references[0][k] for k in ('bytes','sha256')})
    name='tools.local_validation.lhost1._primitive';module=types.ModuleType(name)
    module.__file__=path;module.__package__='tools.local_validation.lhost1';sys.modules[name]=module
    exec(compile(raw,path,'exec',dont_inherit=True),module.__dict__)
    return module

def parent(request,admission,origin,manifest,request_path,admission_path,request_pin,admission_pin,caller_identity):
    guard=reader=outputs=None;accepted=False;failure=None;state=new_state();closure={}
    receiver=None;operation=dict(stage='L',operation_id=request['operation_id'],request=admission['request'],
                                admission=dict(path=admission_path,**admission_pin,role='admission'),origin=origin)
    try:
        guard,reader,controls,plan,physical,selection,samples=prepare(request,admission,origin,manifest,request_path,admission_path,request_pin,admission_pin)
        path=Path(request['attempt_root']);need(path.name==request['operation_id'],'UUID attempt root')
        reader.retain_directory(path.parent);absent(path);os.mkdir(path);reader.retain_directory(path)
        outputs=RetainedOutputs(reader,path)
        outputs.write('claim.json',encode(dict(schema='cho51_l_claim_v1',operation=operation,created_utc=datetime.now(timezone.utc).isoformat(),
              original_caller_identity=caller_identity,attempt_root=request['attempt_root'],request_digest=admission['request']['sha256'])))
        static=pinned_json(reader,plan['bindings']['static_roster'])
        receiver=ObservationReceiver(operation,outputs,static,plan['bindings']['candidate_refs'],guard.checkpoint)
        primitive=load_primitive(manifest,reader)
        install_transport(primitive,state,receiver,request['environment'],guard.checkpoint,job_adapter)
        deadline=guard.origin+timedelta(seconds=240)
        outputs.write('deadline.json',encode(dict(schema='phase2_supervision_deadlines_v1',attempt_deadline_utc=deadline.isoformat(),session_deadline_utc=deadline.isoformat())))
        def sensor(path):guard.checkpoint();return primitive.live_resources(path)
        ticks=':'.join(str(value) for value in (origin['qpc'],origin['qpc_frequency'],caller_identity['process_id'],caller_identity['creation_filetime']))
        substitutions={'{request_path}':request_path,'{request_bytes}':str(request_pin['bytes']),'{request_sha256}':request_pin['sha256'],
                       '{admission_path}':admission_path,'{admission_bytes}':str(admission_pin['bytes']),'{admission_sha256}':admission_pin['sha256'],
                       '{origin_utc}':origin['utc'],'{origin_ticks}':ticks}
        command=[substitutions.get(argument,argument) for argument in request['command']]
        outputs.write('dispatch.json',encode(dict(schema='cho51_l_dispatch_v1',operation=operation,command_template=request['command'],
                      actual_command=command,caller_identity=caller_identity)))
        observed=primitive.run_supervised_with_frame(command,cwd=Path(request['cwd']),deadline_path=path/'deadline.json',
             floor=primitive.ResourceFloor(ram_bytes=4*1024**3,disk_bytes=20*1024**3),sensor=sensor,poll_seconds=.1,
             process_memory_limit_bytes=4096*1024**2,max_frame_bytes=8*1024**2)
        need(lifecycle_ok(state) and observed.result.exit_code==0,'owned L child lifecycle incomplete')
        selection.verify();reader.verify();outputs.verify();guard.checkpoint()
        for name in ('stdout','stderr'):
            raw=state.pop(name+'_bytes',b'');outputs.write(name+'.bin',raw)
        index=dict(schema='cho51_l_observation_index_v1',operation=operation,pages=receiver.pages,row_counts=receiver.rows,
                   ordered_roster_sha256=receiver.collection_summary['ordered_roster_sha256'],plan=request['plan'],
                   preparation_result=request['preparation_result'],publication_status='provisional',safety=scope_safety())
        index_descriptor=outputs.write('observation-index.json',encode(index))
        outputs.write('result.json',encode(dict(schema='cho51_l_result_v1',operation=operation,plan=request['plan'],
             preparation_result=request['preparation_result'],observation_index=index_descriptor,
             collection_summary=receiver.collection_summary,abi_scope=ABI_SCOPE,
             resource_coverage='exact observed rows in retained resource pages; native mappings remain separate',
             guard_coverage='exact guard rows and sentinel denials in retained pages',counters={k:0 for k in COUNTERS},
             failures=[],publication_status='provisional',safety=scope_safety())))
        selection.verify();outputs.verify();guard.checkpoint();accepted=True
    except BaseException as error:
        failure=type(error).__name__+': '+str(error)[:4000]
    finally:
        if guard is not None:guard.enter_cleanup()
        # Original-handle closure is reported honestly even after a refusal.
        if reader is not None:reader.checkpoint=lambda:True
        for name,owner in (('outputs',outputs),('inputs',reader)):
            try:
                if owner is not None:owner.close()
                closure[name]=True
            except BaseException as error:closure[name]=False;closure[name+'_error']=str(error)
        if guard is not None:
            guard.stop_watchdog.set();guard.watchdog.join(.5);closure['watchdog_joined']=not guard.watchdog.is_alive()
    accepted=accepted and all(v is True for k,v in closure.items() if not k.endswith('_error'))
    receipt=dict(schema='cho51_l_parent_return_v1',operation=operation,status='provisional-complete' if accepted else 'refused',
                 first_failure=failure,lifecycle=state,original_handle_closure=closure,whole_interval_valid=guard is not None and guard.elapsed()<300,
                 external_caller_return_pending=True,independent_actual_review_pending=True,safety=scope_safety())
    # Convert byte buffers on failure to digest facts; never serialize raw memory
    # as invented report paths or lose already observed partial byte accounting.
    for key in ('stdout_bytes','stderr_bytes'):
        if key in state:
            raw=state.pop(key);state[key]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    sys.stdout.buffer.write(encode(receipt)+b'\n');sys.stdout.buffer.flush()
    return 0 if accepted else 1

def child(request,admission,origin,manifest,request_path,admission_path,request_pin,admission_pin,caller_identity,report_handle):
    import msvcrt
    guard=reader=None;runtime=None
    try:
        guard,reader,controls,plan,physical,selection,samples=prepare(request,admission,origin,manifest,request_path,admission_path,request_pin,admission_pin)
        need(dict(os.environ)==request['environment'],'child exact constructed environment')
        handle=report_handle;need(type(handle) is int and handle>0,'original inherited report handle')
        fd=msvcrt.open_osfhandle(handle,os.O_WRONLY|os.O_BINARY)
        # Capture native writes before Python gates replace fd aliases.
        pipe=os.fdopen(fd,'wb',buffering=0)
        writer=FrameWriter(pipe.write,request['operation_id'],guard.checkpoint)
        phase=['L1']
        def emit(kind,payload):writer.emit(phase[0],kind,payload)
        runtime=Runtime(reader,physical,plan['policies'],plan['bindings'],guard.checkpoint,
                        lambda:dict(utc=datetime.now(timezone.utc).isoformat(),qpc=origin['qpc']+int(guard.elapsed()*origin['qpc_frequency']),
                                    qpc_frequency=origin['qpc_frequency'],elapsed_seconds=guard.elapsed()),emit)
        observer=NativeObserver(plan['bindings']['native_helper'],runtime.verify,guard.checkpoint,lambda:phase[0],1,
                                runtime.load_exact,runtime.release_exact)
        def dispatch(value):phase[0]=value;runtime.phase_dispatch(value)
        def mechanism(state,resources,registry):
            need(runtime.verify_native(plan['policies']['native_policy']) is True,'native guards')
        def final():selection.verify();reader.verify();return True
        static=pinned_json(reader,plan['bindings']['static_roster'])
        context=VerifiedContext(operation_id=request['operation_id'],groups=plan['groups'],policies=plan['policies'],
              static_roster=static,candidate_refs=plan['bindings']['candidate_refs'],writer=writer,
              checkpoint=guard.checkpoint,tick=runtime.tick,read_retained=runtime.read,publish=runtime.refuse_write,caller=runtime.caller,
              native_observer=observer,native_resolver=runtime.native_resolver,before_extension=runtime.before_extension,
              after_extension=runtime.after_extension,install_native_gates=runtime.install_native,verify_native_gates=runtime.verify_native,
              manager_gate=runtime.manager_gate,final_verify=final,mechanism_checkpoint=mechanism,phase_dispatch=dispatch,bind_emit=runtime.bind_emit,bind_effects=runtime.bind_effects,
              bootstrap_modules=tuple(plan['bindings']['bootstrap_modules']))
        try:run_child(context)
        finally:pipe.close()
        return 0
    finally:
        if guard is not None:guard.enter_cleanup()
        if reader is not None:reader.checkpoint=lambda:True;reader.close()
        if guard is not None:
            guard.stop_watchdog.set();guard.watchdog.join(.5)
            need(not guard.watchdog.is_alive(),'child guard thread unjoined')
