"""Pure closed validation of Q8 already-resident reference observations."""
import re
from ..v1 import records as r

PLAN='tools/local_validation/lp15/api_query_plan.json'
Q_PHASE='runs/coordination/cho51_p3_probe_20261101_q2'
BASELINES=['C:/Windows/System32/kernelbase.dll','C:/Windows/System32/kernel32.dll','C:/Windows/System32/ntdll.dll']
MODULE=BASELINES[0]
CONTROLS=('negative_lookup_refused','small_buffer_refused','invalid_length_refused','invalid_termination_refused','foreign_handle_refused')


def validate_plan(value):
    r.closed(value,('schema','exact_query_names','os_version','files','negative_query','baseline_modules','target_host_loading_authorized'))
    r.require(value['schema']=='cho51_p9_resident_reference_plan_v1' and value['baseline_modules']==BASELINES
        and value['negative_query']=='api-ms-win-codex-absent-l999-999-999.dll' and value['target_host_loading_authorized'] is False,'resident scope')
    names=value['exact_query_names']
    r.require(type(names) is list and len(names)==14 and names==sorted(set(names)),'exact14 names')
    for name in names:r.require(type(name) is str and re.fullmatch(r'api-ms-win-core-[a-z0-9-]+\.dll',name),'contract name')
    r.require(type(value['os_version']) is str and re.fullmatch(r'10\.0\.[0-9]+',value['os_version']),'OS version')
    files=value['files'];r.require(type(files) is list and len(files)==7,'seven OS pins')
    expected=set(BASELINES+['C:/Windows/System32/'+name for name in ('apisetschema.dll','cabinet.dll','fontsub.dll','mswsock.dll')])
    for item in files:
        r.closed(item,('path','bytes','sha256','file_version'));r.windows_path(item['path'],absolute=True)
        r.exact_int(item['bytes'],1,8*1024**2)
        r.require(type(item['sha256']) is str and r.HEX64.fullmatch(item['sha256']),'OS digest');r.exact_string(item['file_version'],256)
    r.require({item['path'] for item in files}==expected,'exact OS pin set')
    return value


def _identity(value):
    r.require(type(value) is str and re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',value),'native file identity')


def _ref(value,path):
    r.closed(value,('path','bytes','sha256'));r.require(value['path']==path,'exact artifact path')
    r.exact_int(value['bytes'],1,1048576);r.require(type(value['sha256']) is str and r.HEX64.fullmatch(value['sha256']),'artifact digest')


def validate_observation(value,plan,success_required=True):
    r.closed(value,('success','exception_type','exception_message','references','rows','controls','acquired_count','released_count',
        'all_owned_references_released','flags','buffer_wchars','small_buffer_return','small_buffer_error'))
    r.require(type(value['success']) is bool and value['flags']==0 and type(value['flags']) is int
        and type(value['buffer_wchars']) is int and value['buffer_wchars']==260,'flags/buffer')
    refs=value['references'];r.require(type(refs) is list and len(refs)<=18,'reference call cap')
    acquired=released=0
    for index,item in enumerate(refs):
        r.closed(item,('index','role','requested','handle','module_path','acquired','released','acquire_error','release_error','module_length'))
        r.require(type(item['index']) is int and item['index']==index and type(item['handle']) is str and re.fullmatch(r'[0-9a-f]{16}',item['handle']),'reference sequence/handle')
        r.require(type(item['acquired']) is bool and type(item['released']) is bool and (item['acquired'] or not item['released']),'reference state')
        for key in ('acquire_error','release_error','module_length'):r.exact_int(item[key],upper=2**32-1)
        r.exact_string(item['requested'],4096);r.exact_string(item['module_path'],4096)
        acquired+=int(item['acquired']);released+=int(item['released'])
    r.require(type(value['acquired_count']) is int and value['acquired_count']==acquired and type(value['released_count']) is int and value['released_count']==released
        and type(value['all_owned_references_released']) is bool and value['all_owned_references_released']==(acquired==released),'per-acquisition release accounting')
    rows=value['rows'];r.require(type(rows) is list and len(rows)<=14,'row cap')
    r.closed(value['controls'],CONTROLS)
    r.require(all(type(v) is bool for v in value['controls'].values()),'typed observation controls')
    if not value['success']:
        r.require(not success_required,'successful observation required')
        r.exact_string(value['exception_type'],1024);r.exact_string(value['exception_message'],1024)
        return {}
    r.require(value['exception_type'] is None and value['exception_message'] is None and acquired==released==17
        and len(refs)==18 and len(rows)==14 and all(value['controls'].values()),'complete observed references/controls')
    r.require(type(value['small_buffer_return']) is int and value['small_buffer_return']==1 and type(value['small_buffer_error']) is int
        and value['small_buffer_error']==122,'actual filename insufficient-buffer probe')
    handles=[]
    for index,path in enumerate(BASELINES):
        item=refs[index]
        r.require(item['role']=='baseline' and item['requested']==path.replace('/','\\') and item['module_path'].lower()==path.lower()
            and item['module_length']==len(path) and item['acquired'] is True and item['released'] is True and item['acquire_error']==item['release_error']==0,'resident baseline')
        handles.append(item['handle'])
    r.require(len(set(handles))==3 and '0000000000000000' not in handles,'distinct live baselines')
    result={}
    for index,(row,name) in enumerate(zip(rows,plan['exact_query_names'])):
        r.closed(row,('name','host','module_path','baseline_handle','lookup_success','reference_index','module_length'))
        item=refs[index+3]
        r.require(row['name']==name and row['lookup_success'] is True and type(row['reference_index']) is int and row['reference_index']==index+3
            and item['role']=='contract' and item['requested']==name and item['acquired'] is True and item['released'] is True and item['acquire_error']==item['release_error']==0
            and row['baseline_handle']==item['handle'] and item['handle'] in handles,'exact resident contract reference')
        path=BASELINES[handles.index(item['handle'])]
        r.require(row['module_path']==path and item['module_path'].lower()==path.lower() and row['host']==path.rsplit('/',1)[1]
            and type(row['module_length']) is int and row['module_length']==item['module_length']==len(path),'resident path/host/count')
        result[name]=[row['host']]
    negative=refs[-1]
    r.require(negative['role']=='negative' and negative['requested']==plan['negative_query'] and negative['acquired'] is False
        and negative['released'] is False and negative['handle']=='0000000000000000' and negative['acquire_error']>0,'negative contract observation')
    return result


def validate_diagnostic(value,plan,operation,helper,identity,plan_sha,success_required=False):
    validate_plan(plan);_identity(identity)
    r.closed(value,('schema','operation_id','plan_sha256','native_helper','native_helper_native_identity','artifact_native_identity','os_version','platform_files',
        'observation','target_modules_loaded','loader_qualified','scientific_admission'))
    r.require(value['schema']=='cho51_q9_native_diagnostic_v1' and value['operation_id']==operation and value['plan_sha256']==plan_sha
        and value['native_helper']==helper and value['artifact_native_identity']==identity and value['os_version']==plan['os_version']
        and value['platform_files']==plan['files'],'diagnostic pins/identity')
    _identity(value['native_helper_native_identity'])
    r.require(value['target_modules_loaded'] is False and value['loader_qualified'] is False and value['scientific_admission'] is False,'resident-only scope')
    return validate_observation(value['observation'],plan,success_required)


def validate_receipt(value,plan,operation,helper,identity,plan_sha):
    validate_plan(plan);_identity(identity)
    r.closed(helper,('path','bytes','sha256'));r.require(helper['path']==Q_PHASE+'/native-helper_'+operation+'.dll','emitted helper path')
    r.exact_int(helper['bytes'],1,8*1024**2);r.require(type(helper['sha256']) is str and r.HEX64.fullmatch(helper['sha256']),'helper pin')
    r.closed(value,('schema','operation_id','plan_sha256','native_helper','native_helper_native_identity','artifact_native_identity','os_version','platform_files','observation',
        'native_diagnostic','native_diagnostic_native_identity','target_modules_loaded','loader_qualified','scientific_admission'))
    _ref(value['native_diagnostic'],Q_PHASE+'/native-diagnostic_'+operation+'.json');_identity(value['native_diagnostic_native_identity'])
    diagnostic={k:v for k,v in value.items() if k not in ('native_diagnostic','native_diagnostic_native_identity')}
    r.require(value['schema']=='cho51_q9_api_mapping_v1','resident mapping schema')
    diagnostic['schema']='cho51_q9_native_diagnostic_v1'
    return validate_diagnostic(diagnostic,plan,operation,helper,identity,plan_sha,True)



