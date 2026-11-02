"""Closed L request/admission chain and current physical-reference enrichment."""
from datetime import datetime,timedelta,timezone
from ..l1.protocol import need,closed,ref,integer,string,canonical_uuid,safety,encode
from ..v1.records import windows_path,validate_file_descriptor

PROJECT='D:/Aenv/pro3'
L_PHASE=PROJECT+'/runs/coordination/cho51_p3_loader_collection_l1'
BOOTSTRAP=PROJECT+'/tools/local_validation/lhost1/bootstrap.py'
CHILD_ARGUMENTS=['{request_path}','{request_bytes}','{request_sha256}',
                 '{admission_path}','{admission_bytes}','{admission_sha256}',
                 '{origin_utc}','{origin_ticks}','{result_handle}']

def fixed_command(request):
    roots=request['roots'];closed(roots,'project runtime site')
    need(roots['project']==PROJECT and roots['site']==PROJECT+'/.venv/Lib/site-packages','fixed project/site roots')
    windows_path(roots['runtime'],absolute=True)
    need(len(roots['runtime'])>3,'finite runtime root')
    need(request['cwd']==PROJECT and request['stop_path']==PROJECT+'/runs/coordination/PROJECT_STOP.json','fixed cwd/stop')
    need(request['attempt_root']==L_PHASE+'/attempts/'+request['operation_id'],'fixed L attempt root')
    cache=L_PHASE+'/disabled-bytecode/'+request['operation_id']
    need(request['environment']['PYTHONPYCACHEPREFIX']==cache,'fixed absent L bytecode root')
    return [roots['runtime']+'/python.exe','-I','-S','-B','-X','pycache_prefix='+cache,BOOTSTRAP,'child',*CHILD_ARGUMENTS]

def evidence_ref(value,role='chain_evidence'):
    """Normalize historical three-field refs without discarding byte identity."""
    if type(value) is dict and value.get('schema')=='cho51_lv_file_descriptor_v1':
        descriptor=validate_file_descriptor(value)
        value={k:descriptor[k] for k in ('path','bytes','sha256','native_identity')}
    need(type(value) is dict and {'path','bytes','sha256'}<=set(value)<=
         {'path','bytes','sha256','role','native_identity'},'evidence reference fields')
    path=value['path'];string(path)
    if not (len(path)>2 and path[1:3]==':/'):
        windows_path(path);path=PROJECT+'/'+path
    result=dict(path=path,bytes=value['bytes'],sha256=value['sha256'],role=value.get('role',role))
    if 'native_identity' in value:
        validate_file_descriptor(dict(schema='cho51_lv_file_descriptor_v1',path=path,
            bytes=value['bytes'],sha256=value['sha256'],native_identity=value['native_identity'],
            file_type='regular',reparse_point=False,link_count=1))
    ref(result);return result

def same_ref(left,right):
    a,b=evidence_ref(left),evidence_ref(right)
    return all(a[k]==b[k] for k in ('path','bytes','sha256')) and (
        'native_identity' not in left or 'native_identity' not in right or left['native_identity']==right['native_identity'])

def source_map(sources):
    need(type(sources) is dict and 1<=len(sources)<=2000,'finite reviewed source map')
    result={}
    for path,pin in sources.items():
        closed(pin,'bytes sha256');row=evidence_ref(dict(path=path,**pin))
        need(row['path'].startswith(PROJECT+'/') and row['path'].lower() not in {p.lower() for p in result},'review source scope/alias')
        result[row['path']]={k:row[k] for k in ('bytes','sha256')}
    return result

def manifest_map(manifest):
    closed(manifest,'schema project_root files')
    need(manifest['schema']=='cho51_l_source_manifest_v1' and manifest['project_root']==PROJECT,'exact source manifest root/schema')
    need(type(manifest['files']) is list and 1<=len(manifest['files'])<=2000,'finite manifest sources')
    result={}
    for row in manifest['files']:
        ref(row);path=row['path']
        need(path.startswith(PROJECT+'/') and path.lower() not in {p.lower() for p in result},'manifest scope/alias')
        result[path]={k:row[k] for k in ('bytes','sha256')}
    need(BOOTSTRAP in result and PROJECT+'/tools/local_validation/lhost1/invoke_l.ps1' in result,'reviewed bootstrap and caller required')
    return result

def accepted_review(value,status):
    need(value['status']==status and type(value['authors']) is list and bool(value['authors'])
         and type(value['reviewer']) is str and bool(value['reviewer']) and value['reviewer'] not in value['authors']
         and value['findings']==[],'independent positive review')
    utc(value['created_utc']);return value

def retain_chain(request,admission,read):
    """Read finite typed chain edges before validation; no recursive authority discovery."""
    records={};pins={}
    def take(item):
        item=evidence_ref(item);path=item['path'];pin={k:item[k] for k in ('bytes','sha256')}
        need(path not in pins or pins[path]==pin,'conflicting control references')
        if path not in records:
            need(len(records)<300,'finite chain record cap');records[path]=read(item);pins[path]=pin
        return records[path]
    for item in [request[k] for k in ('adoption','plan','source_manifest','runtime_manifest','preparation_p','preparation_index','preparation_result')]+request['predecessor_reviews']+request['control_inputs']+[admission['implementation_review']]:take(item)
    adoption=take(request['adoption'])
    design=take(adoption['design']);take(design['review'])
    q=take(adoption['qualification_q']);p=take(adoption['preparation_p'])
    for key in ('source_review','actual_review'):take(q[key]);take(p['references'][key])
    take(p['references']['coverage_review'])
    return records

LIMITS=dict(whole_seconds=300,work_seconds=240,cleanup_seconds=5,process_mib=4096,job_mib=5120,
           parent_mib=4096,startup_ram_gib=4,active_ram_gib=4,disk_gib=20,threads=1,gpu_visible=False,
           frame_bytes=8*1024**2,stream_bytes=1024**2,output_bytes=64*1024**2,output_files=256,
           input_files=25000,input_bytes=4*1024**3,input_file_bytes=2*1024**3,depth=32,hash_chunk_bytes=65536)

ENVIRONMENT_REQUIRED=('SystemRoot','WINDIR','TEMP','TMP','HOME','USERPROFILE','PATH','XDG_CONFIG_HOME',
                      'XDG_CACHE_HOME','MPLCONFIGDIR','PYTHONPYCACHEPREFIX')
ENVIRONMENT_FIXED={'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
                   'OPENBLAS_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','CUDA_VISIBLE_DEVICES':'-1',
                   'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}
ENVIRONMENT_OPTIONAL=('COMSPEC','PATHEXT','SystemDrive','LOCALAPPDATA','APPDATA','LANG','LC_ALL','TZ')

def validate_environment(environment):
    need(type(environment) is dict and len(environment)<=128,'explicit bounded environment')
    need(all(type(k) is str and type(v) is str for k,v in environment.items()),'environment string fields')
    need(len({k.upper() for k in environment})==len(environment),'environment case aliases')
    need(set(environment)<=set(ENVIRONMENT_REQUIRED)|set(ENVIRONMENT_FIXED)|set(ENVIRONMENT_OPTIONAL),'environment outside allowlist')
    for key in ENVIRONMENT_REQUIRED:string(environment.get(key),32768)
    for key,value in ENVIRONMENT_FIXED.items():need(environment.get(key)==value,'controlled environment '+key)
    for key,value in environment.items():
        need('=' not in key,'environment name');string(value,32768)
    return environment

def utc(value):
    string(value,64)
    try: result=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as error:raise ValueError('UTC format') from error
    need(result.utcoffset()==timedelta(0),'explicit UTC')
    return result

def validate(request,admission,origin):
    closed(request,'schema stage operation_id created_utc adoption plan source_manifest runtime_manifest preparation_p preparation_index preparation_result predecessor_reviews command cwd roots control_inputs attempt_root stop_path environment limits forbidden_effects requested_window safety')
    closed(admission,'schema issuer created_utc stage operation_id request implementation_review adoption admitted_window resource_observation limits permitted_command attempt_root stop_path authorized_new_l_only safety')
    need(request['schema']=='cho51_l_request_v1' and admission['schema']=='cho51_l_admission_v1'
         and request['stage']==admission['stage']=='L','L-only records')
    canonical_uuid(request['operation_id']);need(admission['operation_id']==request['operation_id'],'operation join')
    need(admission['issuer']=='project_root' and admission['authorized_new_l_only'] is True,'Root scoped L admission')
    safety(request['safety']);safety(admission['safety'])
    need(encode(request['limits'])==encode(LIMITS)==encode(admission['limits']),'exact L limits/types')
    for key in ('command','attempt_root','stop_path','adoption'):
        need(request[key]==admission['permitted_command' if key=='command' else key],'request/admission '+key)
    for key in ('adoption','plan','source_manifest','runtime_manifest','preparation_p','preparation_index','preparation_result'):
        ref(request[key])
    ref(admission['request']);ref(admission['implementation_review'])
    need(type(request['predecessor_reviews']) is list and len(request['predecessor_reviews'])>=4,'independent Q/P/source review chain')
    need(type(request['control_inputs']) is list,'complete finite control refs')
    for row in request['predecessor_reviews']+request['control_inputs']:ref(row)
    validate_environment(request['environment'])
    for window in (request['requested_window'],admission['admitted_window']):
        closed(window,'starts_utc expires_utc')
        start,end=utc(window['starts_utc']),utc(window['expires_utc'])
        need(start<=utc(origin['utc']) and utc(origin['utc'])+timedelta(seconds=300)<=end,'whole original caller window')
    need(utc(request['created_utc'])<=utc(admission['created_utc'])<=utc(origin['utc']),'admission order')
    need(request['command']==fixed_command(request),'exact isolated child command template')
    need(set(request['forbidden_effects'])=={'candidate_execution','fixtures','subprocess','network','git','data','weights','model','GPU','scientific_admission'},'forbidden L effects')
    return request

def validate_chain(request,admission,records):
    adoption=records[request['adoption']['path']]
    closed(adoption,'schema author created_utc design implementation_review qualification_q preparation_p plan scoped_policy_replacement safety')
    need(adoption['schema']=='cho51_l_adoption_v1' and adoption['author']=='project_root','Root implementation adoption')
    safety(adoption['safety'])
    need(adoption['implementation_review']==admission['implementation_review'] and adoption['preparation_p']==request['preparation_p']
         and adoption['plan']==request['plan'],'adoption exact source/Q/P/plan joins')
    need(adoption['scoped_policy_replacement']=='local-contract-only; original-full-restart-claim-unchanged','scoped replacement')
    def get(item):return records[evidence_ref(item)['path']]
    review=accepted_review(get(admission['implementation_review']),'ACCEPTED_SOURCE_L1')
    sources=manifest_map(get(request['source_manifest']))
    need(sources==source_map(review['sources']),'exact L implementation source review/manifest join')
    need(same_ref(review['runtime_manifest'],request['runtime_manifest']),'reviewed runtime manifest join before interpreter dispatch')
    need(utc(review['created_utc'])<=utc(adoption['created_utc'])<=utc(request['created_utc']),'source/adoption/request order')
    runtime=get(request['runtime_manifest']);closed(runtime,'schema root executable files census')
    need(runtime['schema']=='cho51_l_runtime_manifest_v1' and runtime['root']==request['roots']['runtime']
         and runtime['executable']==request['command'][0],'command pinned runtime/root join')
    need(type(runtime['files']) is list and 1<=len(runtime['files'])<=2000,'finite runtime pins')
    runtime_paths=set()
    for item in runtime['files']:
        ref(item);need(item['path'].startswith(runtime['root']+'/') and item['path'].lower() not in runtime_paths,'runtime scope/alias')
        runtime_paths.add(item['path'].lower())
    need(runtime['executable'].lower() in runtime_paths,'exact executable pin')
    design=get(adoption['design']);design_review=accepted_review(get(design['review']),'ACCEPTED_DESIGN_ONLY')
    need(design['schema']=='cho51_l_root_design_acceptance_v1' and design['author']=='project_root'
         and design['status']=='ACCEPTED_DESIGN_ONLY' and design['design_files']==design_review['design_files'],'accepted exact L design')
    need(all(sources.get(path)==pin for path,pin in source_map(design['design_files']).items()),'design bytes present in reviewed implementation')
    need(utc(design_review['created_utc'])<=utc(design['created_utc'])<=utc(review['created_utc']),'design review/adoption order')
    q,p=get(adoption['qualification_q']),get(adoption['preparation_p'])
    for value,status in ((q,'QUALIFIED_LQ1_MECHANISMS_ONLY'),(p,'QUALIFIED_LP1_PHYSICAL_ONLY')):
        need(value['author']=='project_root' and value['status']==status,'Q/P exact qualification roles')
        canonical_uuid(value['operation_id']);need(value['operation_id']!=request['operation_id'],'fresh L operation')
        need(utc(value['created_utc'])<=utc(adoption['created_utc']),'qualification precedes L adoption')
    need(q['operation_id']!=p['operation_id'],'distinct Q/P operations')
    need(same_ref(p['references']['q_qualification'],adoption['qualification_q']),'P qualified the same Q')
    qsource=accepted_review(get(q['source_review']),'ACCEPTED_SOURCE_LQ1')
    qactual=accepted_review(get(q['actual_review']),'ACCEPTED_LQ1_TESTED_SCOPE')
    psource=accepted_review(get(p['references']['source_review']),'ACCEPTED_SOURCE_LP1')
    pactual=accepted_review(get(p['references']['actual_review']),'ACCEPTED_LP1_PHYSICAL_ONLY')
    coverage=accepted_review(get(p['references']['coverage_review']),'ACCEPTED_PROPOSED_P2_PHYSICAL_COVERAGE')
    qpins=source_map(qsource['sources']);ppins=source_map(psource['sources'])
    need(all(qpins.get(path)==pin for path,pin in sources.items()),'fresh Q covers exact L sources')
    need(all(qpins.get(path)==pin for path,pin in ppins.items()),'Q/P exact source coverage')
    expected_reviews=[q['source_review'],q['actual_review'],p['references']['source_review'],p['references']['actual_review']]
    need(len(request['predecessor_reviews'])==4 and all(any(same_ref(item,expected) for item in request['predecessor_reviews']) for expected in expected_reviews),'exact Q/P predecessor review roles')
    for qualified,src,actual,src_ref in ((q,qsource,qactual,q['source_review']),(p,psource,pactual,p['references']['source_review'])):
        need(actual['operation_id']==qualified['operation_id'] and actual['source_review_sha256']==src_ref['sha256'],'actual operation/source join')
        need(actual['reviewer']!=src['reviewer'] and actual['reviewer'] not in review['authors'],'separate actual/source acceptance roles')
        need(type(actual['actual_tool_exit_code']) is int and actual['actual_tool_exit_code']==0
             and actual['new_operation_owned_lifecycle_closed'] is True,'accepted actual caller/closure')
        need(utc(src['created_utc'])<=utc(actual['created_utc'])<=utc(qualified['created_utc']),'source/actual/Root ordering')
    need(pactual['coverage_review_sha256']==p['references']['coverage_review']['sha256']
         and utc(coverage['created_utc'])<=utc(pactual['created_utc']),'physical coverage review join/order')
    for flag in ('final_full_input_verification_completed_before_release','input_identity_verified_before_release','output_identity_verified_before_release'):
        need(pactual[flag] is True,'complete accepted P verification')
    for key,actual_key in (('accepted_result','accepted_result'),('accepted_index','accepted_physical_index')):
        need(same_ref(p[key],request['preparation_result' if key=='accepted_result' else 'preparation_index'])
             and same_ref(p[key],pactual[actual_key]),'P result/index exact accepted identity')

def validate_plan_acceptance(request,acceptance,review,derivation):
    closed(acceptance,'schema author status created_utc plan derivation review safety')
    need(acceptance['schema']=='cho51_l_complete_plan_acceptance_v1' and acceptance['author']=='project_root'
         and acceptance['status']=='ACCEPTED_COMPLETE_L_PLAN','Root complete-plan record')
    safety(acceptance['safety'])
    closed(review,'schema status reviewer authors created_utc plan derivation findings checks limitations safety')
    need(review['schema']=='cho51_l_complete_plan_review_v1','independent complete-plan review schema')
    accepted_review(review,'ACCEPTED_COMPLETE_L_PLAN_SOURCE');safety(review['safety'])
    need(same_ref(acceptance['plan'],request['plan']) and same_ref(review['plan'],request['plan'])
         and same_ref(review['derivation'],acceptance['derivation']),'exact reviewed complete plan/derivation')
    need(utc(review['created_utc'])<=utc(acceptance['created_utc'])<=utc(request['created_utc']),'plan review before Root acceptance/request')
    need(derivation['schema']=='cho51_l_plan_derivation_v1' and derivation['status']=='COMPLETE_REQUIRES_INDEPENDENT_REVIEW'
         and same_ref(derivation['plan_ref'],request['plan']),'complete source-derived plan identity')
    need(type(derivation['pages']) is list and not any(row['kind']=='refusals' for row in derivation['pages']),'no unresolved derivation pages')
    for key in ('candidate_imports','third_party_imports','executed_code_from_inputs'):integer(derivation[key],0,0)
    need(derivation['launch_authorized'] is False,'derivation conveys no launch authority')

def enrich(value,physical,reader,checkpoint):
    """Replace normal Ref leaves only with fresh same-handle retained facts."""
    if type(value) is list:return [enrich(v,physical,reader,checkpoint) for v in value]
    if type(value) is not dict:return value
    if set(value)=={'path','bytes','sha256','role'}:
        ref(value);need(checkpoint() is True,'enrichment checkpoint')
        need(value['path'] in physical,'plan input absent from new P')
        expected=physical[value['path']]
        need(all(expected[k]==value[k] for k in ('bytes','sha256')),'P/current source pin')
        descriptor=reader.retain(value['path'],{k:value[k] for k in ('bytes','sha256')})
        need(descriptor['native_identity']==expected['native_identity'],'P/current file identity')
        return dict(value,native_identity=descriptor['native_identity'],owner='l_parent_retained',
                    sharing=dict(read=True,write=False,delete=False))
    return {k:enrich(v,physical,reader,checkpoint) for k,v in value.items()}
