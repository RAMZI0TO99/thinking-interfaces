"""Supplied-record contract used by fresh Q and independent result readers.

The real execution path is diagnostic.ps1, exercised by Q's actual controls.
This module never launches a process, opens an artifact or probes a sensor.
"""
import json
import re
import uuid
import math
from datetime import datetime,timedelta

class Refusal(ValueError):pass
def need(value,message):
    if not value:raise Refusal(message)
def closed(value,keys):
    need(type(value) is dict and set(value)==set(keys.split()),'closed '+keys)
def integer(value,low,high):need(type(value) is int and low<=value<=high,'bounded integer')
def path(value):
    need(type(value) is str and len(value)<=32768 and re.fullmatch(r'[A-Z]:/[^\\\x00:*?"<>|]+',value) is not None,'canonical path')
    need(all(part not in ('','.','..') and not part.endswith(('.', ' ')) for part in value[3:].split('/')),'path components')
    return value
def pin(value):
    closed(value,'bytes sha256');integer(value['bytes'],0,64*1024**2)
    need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None,'sha256')
def reference(value):
    closed(value,'path bytes sha256');path(value['path']);pin({k:value[k] for k in ('bytes','sha256')})
def utc(value):
    need(type(value) is str and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,7})?(?:Z|\+00:00)',value) is not None,'UTC literal')
    result=datetime.fromisoformat(value.replace('Z','+00:00'));need(result.utcoffset()==timedelta(0),'UTC offset');return result
LIMITS=dict(startup_seconds=5,cleanup_deadline_seconds=10,whole_seconds=15,startup_ram_bytes=4*1024**3,
    active_ram_bytes=4*1024**3,disk_bytes=20*1024**3,process_mib=4096,job_mib=5120,sample_interval_ms=250)
SAFETY=dict(historical_custody_closed=False,historical_operation_released=False,historical_retry_allowed=False,
    restart_qualified=False,scientific_admission=False,candidate_tests_executed=0,successor_controls_executed=0)
SOURCE_LEAVES=('__init__.py','contract.py','diagnostic.ps1','pdh_probe.ps1','fast_probe.ps1','stall_probe.ps1','empty_probe.ps1','malformed_probe.ps1','reordered_probe.ps1','partial_probe.ps1','test_diagnostic.py','README.md')
CAPSULE_KEYS='schema issuer operation_id role probe created_utc expires_utc project_root stop_path output_root helper q2_qualification q2_actual_review source_review adoption qualification sources caller_runtime environment limits safety enclosing_q'
def exact(left,right):return json.dumps(left,sort_keys=True,separators=(',',':'))==json.dumps(right,sort_keys=True,separators=(',',':'))
def validate_capsule(value,original_utc):
    closed(value,CAPSULE_KEYS)
    need(value['schema']=='cho51_startup_capsule_v1' and value['issuer']=='project_root','capsule authority')
    need(type(value['operation_id']) is str and str(uuid.UUID(value['operation_id']))==value['operation_id'],'UUID')
    need(value['role'] in ('D','Q_STARTUP_CONTROL'),'role')
    need(value['probe'] in (('pdh',) if value['role']=='D' else ('fast','stall','empty','malformed','reordered','partial')),'role/probe boundary')
    need(value['project_root']=='D:/Aenv/pro3' and value['stop_path']=='D:/Aenv/pro3/runs/coordination/PROJECT_STOP.json','project scope')
    path(value['output_root']);need(value['output_root'].startswith('D:/Aenv/pro3/runs/coordination/') and value['output_root'].endswith('/'+value['operation_id']),'UUID output namespace')
    origin=utc(original_utc)
    need(utc(value['created_utc'])<=origin and origin+timedelta(seconds=15)<=utc(value['expires_utc']),'original whole interval')
    need(exact(value['limits'],LIMITS) and exact(value['safety'],SAFETY),'fixed limits/safety types')
    helper=value['helper'];closed(helper,'path bytes sha256 native_identity');reference({k:helper[k] for k in ('path','bytes','sha256')})
    need(re.fullmatch('[0-9a-f]{16}:[0-9a-f]{32}',helper['native_identity']) is not None,'native helper identity')
    for key in ('q2_qualification','q2_actual_review','source_review','adoption'):reference(value[key])
    expected={value['project_root']+'/tools/local_validation/startup1/'+leaf for leaf in SOURCE_LEAVES}
    need(type(value['sources']) is dict and set(value['sources'])==expected,'exact startup sources')
    for name,item in value['sources'].items():path(name);pin(item)
    runtime=value['caller_runtime'];closed(runtime,'executable version files');reference(runtime['executable'])
    need(type(runtime['version']) is str and type(runtime['files']) is list and 1<=len(runtime['files'])<=1024,'runtime closure')
    for item in runtime['files']:reference(item)
    need(len({r['path'] for r in runtime['files']})==len(runtime['files']) and runtime['executable'] in runtime['files'],'runtime executable membership')
    need(sum(r['bytes'] for r in runtime['files'])<=512*1024**2,'runtime aggregate')
    validate_environment(value['environment'])
    environment=value['environment']
    need(environment['SystemRoot']==environment['WINDIR']=='C:/Windows','Windows environment')
    need(environment['PATH']==runtime['executable']['path'].rsplit('/',1)[0]+';C:/Windows/System32','runtime PATH')
    for key in ('HOME','USERPROFILE','TEMP','TMP'):need(environment[key]==value['output_root'],'attempt-only environment')
    if value['role']=='D':
        reference(value['qualification']);need(value['enclosing_q'] is None,'D has no Q parent assertion')
    else:
        need(value['qualification'] is None,'no self qualification')
        enclosing=value['enclosing_q'];closed(enclosing,'operation_id admission limits');reference(enclosing['admission'])
        need(enclosing['operation_id']!=value['operation_id'] and exact(enclosing['limits'],dict(process_mib=512,job_mib=768)),'outer Q bounds')
    return value
def validate_environment(value):
    required={'SystemRoot','WINDIR','PATH','HOME','USERPROFILE','TEMP','TMP','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES','PYTEST_DISABLE_PLUGIN_AUTOLOAD'}
    need(type(value) is dict and set(value)==required,'closed environment')
    need(all(type(v) is str and v and '\0' not in v and len(v)<=32768 for v in value.values()),'environment values')
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','PYTEST_DISABLE_PLUGIN_AUTOLOAD'):need(value[key]=='1','fixed environment '+key)
    need(value['CUDA_VISIBLE_DEVICES']=='-1','hidden GPUs')
def parse(raw):
    need(type(raw) is bytes and len(raw)<=1024**2,'JSON byte cap')
    def pairs(rows):
        result={}
        for key,value in rows:need(key not in result,'duplicate JSON');result[key]=value
        return result
    value=json.loads(raw.decode('utf-8','strict'),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refusal('nonfinite JSON')))
    budget=[0]
    def visit(item,depth):
        budget[0]+=1;need(depth<=16 and budget[0]<=20000,'JSON structure bound')
        if type(item) is dict:
            for k,v in item.items():need(type(k) is str and '\0' not in k,'JSON key');visit(v,depth+1)
        elif type(item) is list:
            for v in item:visit(v,depth+1)
        elif type(item) is str:item.encode('utf-8','strict');need('\0' not in item,'JSON string')
        elif type(item) is float:need(math.isfinite(item),'finite JSON number')
    visit(value,0);return value
MARKERS={'pdh':['assembly_load_begin','assembly_load_end','counter_ctor_begin','counter_ctor_end','first_sample_begin','first_sample_end','counter_dispose_begin','counter_dispose_end'],
         'fast':['fixture_fast_begin','fixture_fast_end'],'stall':['fixture_stall_begin']}
def validate_markers(rows,probe,origin):
    closed(origin,'utc qpc frequency');utc(origin['utc']);integer(origin['qpc'],1,2**63-1);integer(origin['frequency'],1,2**63-1)
    need(type(rows) is list and 1<=len(rows)<=16,'nonempty marker count')
    protocol='fast' if probe in ('empty','malformed','reordered','partial') else probe
    seen=[];previous=origin['qpc']
    for index,row in enumerate(rows):
        closed(row,'schema sequence event origin_utc origin_qpc frequency qpc elapsed_seconds detail')
        need(row['schema']=='cho51_startup_probe_marker_v1' and row['sequence']==index and type(row['sequence']) is int,'marker sequence/schema')
        need(row['origin_utc']==origin['utc'] and row['origin_qpc']==origin['qpc'] and row['frequency']==origin['frequency'],'marker original origin')
        integer(row['origin_qpc'],origin['qpc'],origin['qpc']);integer(row['frequency'],origin['frequency'],origin['frequency'])
        integer(row['qpc'],previous,origin['qpc']+5*origin['frequency']);previous=row['qpc']
        need(type(row['elapsed_seconds']) in (int,float) and math.isfinite(row['elapsed_seconds']) and 0<=row['elapsed_seconds']<=5
             and abs(row['elapsed_seconds']-(row['qpc']-origin['qpc'])/origin['frequency'])<=.000001,'marker typed original clock')
        need(type(row['detail']) is str and len(row['detail'])<=1024,'marker detail')
        need(row['event'] in MARKERS[protocol],'marker event')
        seen.append(row['event']);need(seen==MARKERS[protocol][:len(seen)],'marker ordered prefix')
    if protocol in ('fast','stall'):need(seen==MARKERS[protocol],'complete fixture markers')
    return seen==MARKERS[protocol]

def validate_source_review(value,sources):
    closed(value,'schema status reviewer authors created_utc sources design design_acceptance findings checks limitations')
    need(value['schema']=='cho51_startup_source_review_v1' and value['status']=='ACCEPTED_SOURCE_STARTUP1','source review role/status')
    need(type(value['reviewer']) is str and re.fullmatch('[a-z][a-z0-9_-]{0,63}',value['reviewer']) is not None,'reviewer identity')
    need(type(value['authors']) is list and 1<=len(value['authors'])<=16,'author identities')
    for identity in value['authors']:need(type(identity) is str and re.fullmatch('[a-z][a-z0-9_-]{0,63}',identity) is not None,'author identity')
    need(len(set(value['authors']))==len(value['authors']) and value['reviewer'] not in value['authors'],'independent unique identities')
    need(type(value['findings']) is list and value['findings']==[],'unresolved findings')
    for key in ('checks','limitations'):need(type(value[key]) is list and len(value[key])<=256 and all(type(s) is str and len(s)<=4096 for s in value[key]),'review detail')
    need(exact(value['sources'],sources),'exact reviewed source pins');utc(value['created_utc'])
    reference(value['design']);reference(value['design_acceptance']);return value

CUSTODY_TRUE=('LimitsVerified','AtomicMembership','Resumed','Reaped','JobEmpty','JobClosed','ProcessClosed','ThreadClosed','InputClosed',
    'StdoutEof','StderrEof','StdoutReaderClosed','StderrReaderClosed','StdoutWriterClosed','StderrWriterClosed','StdoutThreadClosed','StderrThreadClosed','StdoutJoined','StderrJoined','WatchdogJoined')
def output_ref(value):
    closed(value,'path bytes sha256 native_identity');reference({k:value[k] for k in ('path','bytes','sha256')})
    need(type(value['native_identity']) is str and re.fullmatch('[0-9a-f]{16}:[0-9a-f]{32}',value['native_identity']) is not None,'original output identity')
def validate_external_return(value,capsule):
    """Validate supplied saved evidence; caller separately checks actual files/return."""
    closed(value,'schema operation_id role probe status failure origin caller elapsed_seconds authority_verified native_ids_bound dispose_registration_joined owned_lifecycle_closed custody original_streams_closed final_input_verification final_output_verification guard observation outputs actual_tool_return_pending exit_code termination_cause historical_custody_closed historical_operation_released historical_retry_allowed restart_qualified scientific_admission candidate_tests_executed successor_controls_executed')
    need(value['schema']=='cho51_startup_external_return_v1' and value['status']=='observed_diagnostic_only' and value['failure'] is None,'diagnostic result')
    for key in ('operation_id','role','probe'):need(value[key]==capsule[key],'capsule return join '+key)
    for key in ('authority_verified','native_ids_bound','dispose_registration_joined','owned_lifecycle_closed','original_streams_closed','final_input_verification','final_output_verification'):need(value[key] is True,'required result '+key)
    need(value['exit_code'] is None and value['termination_cause']=='unobserved' and value['actual_tool_return_pending'] is True,'honest diagnostic scope')
    need(type(value['elapsed_seconds']) in (int,float) and 0<=value['elapsed_seconds']<15,'original return interval')
    need(exact({k:value[k] for k in SAFETY},SAFETY),'return safety')
    closed(value['origin'],'utc qpc frequency');utc(value['origin']['utc']);integer(value['origin']['qpc'],1,2**63-1);integer(value['origin']['frequency'],1,2**63-1)
    closed(value['caller'],'pid creation_filetime');integer(value['caller']['pid'],1,2**32-1);integer(value['caller']['creation_filetime'],1,2**63-1)
    custody=value['custody'];closed(custody,' '.join(CUSTODY_TRUE)+' StdoutOverflow StderrOverflow Fault CleanupError StdoutError StderrError CreationFileTime Pid')
    for key in CUSTODY_TRUE:need(custody[key] is True,'custody '+key)
    for key in ('StdoutOverflow','StderrOverflow'):need(custody[key] is False,'capture overflow')
    for key in ('Fault','CleanupError','StdoutError','StderrError'):need(custody[key] is None,'custody error')
    integer(custody['CreationFileTime'],1,2**63-1);integer(custody['Pid'],1,2**32-1)
    guard=value['guard'];closed(guard,'ready stop done error last samples first second joined closed completion_wait_closed')
    for key in ('ready','stop','done','joined','closed','completion_wait_closed'):need(guard[key] is True,'guard '+key)
    need(guard['error'] is None,'guard fault');integer(guard['samples'],2,100000);integer(guard['last'],value['origin']['qpc'],2**63-1)
    first,second=guard['first'],guard['second']
    for sample in (first,second):
        closed(sample,'qpc_begin qpc_end ram_sample_bytes minimum_disk_bytes_so_far peak_caller_private_bytes_so_far managed_current_private_bytes native_predicates_passed')
        integer(sample['qpc_begin'],value['origin']['qpc'],value['origin']['qpc']+5*value['origin']['frequency'])
        integer(sample['qpc_end'],sample['qpc_begin'],value['origin']['qpc']+5*value['origin']['frequency'])
        need((sample['qpc_end']-sample['qpc_begin'])/value['origin']['frequency']<=.25 and sample['native_predicates_passed'] is True,'sample health')
        integer(sample['ram_sample_bytes'],4*1024**3,2**63-1);integer(sample['minimum_disk_bytes_so_far'],20*1024**3,2**63-1)
        cap=(512 if value['role']=='Q_STARTUP_CONTROL' else 4096)*1024**2
        integer(sample['managed_current_private_bytes'],0,cap);integer(sample['peak_caller_private_bytes_so_far'],0,4096*1024**2)
    need((second['qpc_begin']-first['qpc_end'])/value['origin']['frequency']>=.2,'sample spacing')
    output_ref(value['observation']);need(type(value['outputs']) is list and len(value['outputs'])==5,'five original output rows')
    for row in value['outputs']:output_ref(row);need(row['path'].startswith(capsule['output_root']+'/'),'output ownership')
    need(len({r['path'] for r in value['outputs']})==5 and value['observation'] in value['outputs'],'complete output manifest')
    need({r['path'].rsplit('/',1)[-1] for r in value['outputs']}=={'claim.json','stdout.bin','stderr.bin','observation.json','journal.json'},'finite output names')
    return value
