"""Closed file-only P stage records; source and coverage are separate gates."""
from datetime import datetime, timedelta
import hashlib
import re
import uuid
from ..v1 import records as r
from . import api_mapping as am

PHASE = 'runs/coordination/cho51_p3_dependency_prepare_20261029_p9'
Q_PHASE = 'runs/coordination/cho51_p3_dependency_prepare_20261029_q9'
CONTRACT = 'docs/phase2/cho51_p3_local_validation_contract_20261029.md'
SUPPLEMENT = 'docs/phase2/cho51_p3_p2r9_dependency_contract_20261029.md'
DESIGN_REVIEW = 'runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json'
REQUIRED = (
    'runs/coordination/cho51_p3_dependency_prepare_20261029_q8/failure_7c2de01e-6143-4421-a750-b686b69dc2d4/actual-review.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_q8/failure_7c2de01e-6143-4421-a750-b686b69dc2d4/root-disposition.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_q7/failure_6451d9c4-0c30-42fc-8a47-caa520b2043d/actual-review.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_q7/failure_6451d9c4-0c30-42fc-8a47-caa520b2043d/root-disposition.json',
    'tools/local_validation/p2r9/api_mapping.py', 'tools/local_validation/p2r9/api_query_plan.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p6/actual-review.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p6/root-disposition.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p6/static-missing-native.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p6/static-api-query-scope.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p5/actual-review.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p5/root-disposition.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p5/static-pe-descriptor-diagnosis.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p4/actual-review.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p4/root-disposition.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p4/static-api-host-diagnosis.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p3/actual-review.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p3/root-disposition.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p2/actual-review.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p2/root-disposition.json',
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p2/static-path-diagnosis.json',
    'tools/local_validation/p2r9/protocol.py', 'tools/local_validation/p2r9/supervisor.py',
    'tools/local_validation/p2r9/invoke_p.ps1', 'tools/local_validation/p2r9/caller_native.cs',
    'tools/local_validation/p2r9/manifest.py', 'tools/local_validation/p2r9/pe.py',
    'tools/local_validation/p2r9/dependency_recipe.json', 'tools/local_validation/p2r9/dependency_coverage.md',
    'tools/local_validation/p2r9/native_policy.json',
    'tools/local_validation/p2r9/README.md', 'tools/local_validation/p2r9/native_reader.py',
    'tools/local_validation/v1/records.py', 'docs/PROJECT_EXECUTION_POLICY.md',
    'docs/phase2/cho51_p3_local_validation_v1/dependency-plan.json',
    'runs/coordination/cho51_p3_preparation_engine_20261029_p1q/root-qualification.json',
    CONTRACT, SUPPLEMENT, DESIGN_REVIEW,
    "runs/coordination/cho51_p3_git_materialization_20261029_r1/root-qualification.json",
    "runs/coordination/cho51_p3_git_materialization_20261029_r1/actual-review.json",
    "runs/coordination/cho51_p3_git_materialization_20261029_r1/seal_49b1f44d-46ef-446e-a8fd-85a3ddb7ce36.json",
    "docs/phase2/cho51_p3_p2_dependency_contract_20261029.md",
)
LIMITS = {'whole_seconds':300, 'work_seconds':240, 'cleanup_seconds':5,
          'process_mib':4096, 'job_mib':5120, 'parent_mib':4096,
          'startup_ram_gib':4, 'active_ram_gib':4, 'disk_gib':20,
          'stream_bytes':1048576, 'threads':1, 'gpu_visible':False}
FALSES = {'historical_custody_closed':False, 'historical_operation_released':False,
          'historical_retry_allowed':False, 'restart_qualified':False, 'boundary_qualified':False,
          'complete_dependency_closure':False, 'launch_authorized':False, 'scientific_admission':False}
FORBIDDEN = ['candidate_imports','third_party_imports','compilation_of_dependency_sources',
             'native_source_compilation','numerical_work','data_or_weights','network','git',
             'unowned_processes','historical_launcher_replay']
EXPECTED_Q_TESTS = 195
BUILDER_TRUE_KEYS = ('emitted_pe_verified','original_output_identity_retained',
    'loaded_same_pe_bytes','p_limits_query_verified','empty_job_closed')


def pin(value, cap=8*1024**2):
    r.closed(value, ('bytes','sha256'))
    r.exact_int(value['bytes'], upper=cap)
    r.require(type(value['sha256']) is str and r.HEX64.fullmatch(value['sha256']), 'pin digest')
    return value


def utc(text):
    r.exact_string(text,64)
    value=datetime.fromisoformat(text.replace('Z','+00:00'))
    r.require(value.utcoffset()==timedelta(0),'explicit UTC')
    return value


def validate(value, root, origin):
    value=r.defensive_copy(value)
    r.closed(value, ('schema','stage','operation_id','created_utc','expires_utc','root',
        'python','runtime','caller_runtime','sources','review','adoption','qualification',
        'native_helper','map_index','coverage_review','extra_paths','limits','forbidden','scientific_admission','api_mapping','native_diagnostic'))
    r.require(value['schema']=='cho51_p_admission_v1' and value['stage']=='P','P-only admission')
    r.require(value['operation_id']==str(uuid.UUID(value['operation_id'])),'canonical UUID')
    r.require(value['root']==root,'exact project root')
    start,end,origin=map(utc,(value['created_utc'],value['expires_utc'],origin))
    r.require(start<=origin and origin+timedelta(seconds=300)<=end and
              300<=(end-start).total_seconds()<=900,'original complete P window')
    r.require(r.canonical_bytes(value['limits'])==r.canonical_bytes(LIMITS),'P exact limits')
    r.require(value['forbidden']==FORBIDDEN and value['scientific_admission'] is False,'P effects')
    r.require(type(value['sources']) is dict and set(value['sources'])==set(REQUIRED),'exact P sources')
    for item in value['sources'].values(): pin(item)
    r.closed(value['caller_runtime'],('path','bytes','sha256','version'))
    r.windows_path(value['caller_runtime']['path'],absolute=True)
    pin({k:value['caller_runtime'][k] for k in ('bytes','sha256')})
    r.require(value['caller_runtime']['version'].startswith('7.'),'PowerShell7 caller')
    runtime=value['runtime']
    r.closed(runtime,('root','files','recipe','platform_trust'))
    r.windows_path(runtime['root'],absolute=True)
    r.require(runtime['recipe']=='python.exe+root-dll+Lib-py-without-site-packages-or-pycache+DLLs-pyd-dll'
        and runtime['platform_trust']=='reviewed-local-Windows-and-PowerShell-host-no-loaded-code-attestation',
        'bootstrap runtime recipe/trust')
    r.require(value['python']==runtime['root']+'/python.exe' and value['python'] in runtime['files'], 'Python path')
    r.require(type(runtime['files']) is dict and 1<=len(runtime['files'])<=2000,'bootstrap runtime count')
    total=0;seen=set()
    for path,item in runtime['files'].items():
        r.windows_path(path,absolute=True)
        r.require(path.startswith(runtime['root']+'/') and path.lower() not in seen,'runtime scope/alias')
        seen.add(path.lower())
        pin(item,64*1024**2);total+=item['bytes']
    r.require(total<=64*1024**2,'bootstrap runtime bytes')
    expected={'review':PHASE+'/source-review.json','adoption':PHASE+'/contract-adoption.json',
        'qualification':Q_PHASE+'/root-qualification.json','map_index':PHASE+'/pin-index.json',
        'coverage_review':PHASE+'/coverage-review.json'}
    for key in (*expected,'native_helper'):
        ref=value[key];r.closed(ref,('path','bytes','sha256'));r.windows_path(ref['path'])
        if key in expected:r.require(ref['path']==expected[key],'exact control reference')
        else:r.require(ref['path'].startswith(Q_PHASE+'/native-helper_') and ref['path'].endswith('.dll'),'qualified native artifact')
        pin({k:ref[k] for k in ('bytes','sha256')})
    r.require(type(value['extra_paths']) is list and len(value['extra_paths'])<=256,'extra input count')
    for path in value['extra_paths']:r.windows_path(path,absolute=True)
    r.require(len({p.lower() for p in value['extra_paths']})==len(value['extra_paths']),'duplicate/case-alias extra input')
    ref=value['api_mapping'];r.closed(ref,('path','bytes','sha256'))
    r.windows_path(ref['path'])
    r.require(re.fullmatch(re.escape(Q_PHASE)+r'/api-mapping_[0-9a-f-]{36}\.json',ref['path']), 'Q mapping reference')
    pin({k:ref[k] for k in ('bytes','sha256')})
    ref=value['native_diagnostic'];r.closed(ref,('path','bytes','sha256'));r.windows_path(ref['path'])
    r.require(re.fullmatch(re.escape(Q_PHASE)+r'/native-diagnostic_[0-9a-f-]{36}\.json',ref['path']), 'Q diagnostic reference')
    pin({k:ref[k] for k in ('bytes','sha256')})
    return value


def _accepted_review(value, status):
    """Validate core fields of a separately versioned full evidence record."""
    value=r.defensive_copy(value)
    r.require(type(value) is dict and all(k in value for k in
        ('schema','status','reviewer','authors','created_utc','findings','checks','limitations')),
        'accepted review core fields')
    r.require(type(value['schema']) is str and value['schema'].endswith('_v1')
        and value['status']==status,'versioned accepted review')
    authors=value['authors']
    r.require(type(authors) is list and 1<=len(authors)<=8 and
        all(type(a) is str and 0<len(a)<=128 for a in authors) and len(set(authors))==len(authors),
        'review author identities')
    r.require(type(value['reviewer']) is str and 0<len(value['reviewer'])<=128
        and value['reviewer'] not in authors,'independent review identity')
    r.require(type(value['findings']) is list and value['findings']==[],'no unresolved review findings')
    for field in ('checks','limitations'):
        r.require(type(value[field]) is list and len(value[field])<=256 and
            all(type(s) is str and 0<len(s)<=4096 for s in value[field]),'typed review statements')
    utc(value['created_utc'])
    return value


def _builder(value):
    r.closed(value,(*BUILDER_TRUE_KEYS,'helper_identity'))
    r.require(all(value[k] is True for k in BUILDER_TRUE_KEYS) and
        type(value['helper_identity']) is str and
        re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',value['helper_identity']) is not None,
        'qualified native builder controls/identity')


def validate_chain(request, review, adoption, qualification, coverage,
                   q_source_review, q_actual_review, api_receipt, query_plan):
    r.closed(review,('schema','status','reviewer','authors','created_utc','sources','findings','checks','limitations'))
    r.require(review['schema']=='cho51_p2_source_review_v1' and
        type(review['authors']) is list and 1<=len(review['authors'])<=8 and
        all(type(a) is str and 0<len(a)<=128 for a in review['authors']) and
        type(review['reviewer']) is str and 0<len(review['reviewer'])<=128 and
        review['findings']==[],'closed independent source review identity')
    r.require(review['status']=='ACCEPTED_SOURCE_P2' and review['sources']==request['sources']
        and review['reviewer'] not in review['authors'],'P independent source review')
    r.closed(adoption,('schema','author','status','created_utc','contract_sha256','source_review_sha256',
        'design_review_sha256','supplement_sha256','qualification_sha256','coverage_review_sha256','api_mapping_sha256','native_diagnostic_sha256',*FALSES))
    r.require(adoption['schema']=='cho51_p_contract_adoption_v1' and adoption['status']=='ADOPTED_P_ONLY'
        and adoption['author']=='project_root','P adoption')
    joins={'contract_sha256':request['sources'][CONTRACT]['sha256'],
        'source_review_sha256':request['review']['sha256'],
        'design_review_sha256':request['sources'][DESIGN_REVIEW]['sha256'],
        'supplement_sha256':request['sources'][SUPPLEMENT]['sha256'],
        'qualification_sha256':request['qualification']['sha256'],
        'coverage_review_sha256':request['coverage_review']['sha256'], 'api_mapping_sha256':request['api_mapping']['sha256'],
        'native_diagnostic_sha256':request['native_diagnostic']['sha256']}
    r.require(all(adoption[k]==v for k,v in joins.items()) and all(adoption[k] is False for k in FALSES), 'adoption joins/flags')
    r.require(utc(adoption['created_utc'])<=utc(request['created_utc']),'adoption order')
    r.closed(qualification,('schema','status','author','created_utc','operation_id','source_review',
        'actual_review','native_helper','test_count','timestamp_controls','native_fault_controls',
        'native_builder_controls','api_mapping','api_mapping_native_identity','native_diagnostic','native_diagnostic_native_identity','artifact_handoff','sharing_controls',*FALSES))
    r.require(qualification['schema']=='cho51_p2q_root_qualification_v1' and
        qualification['author']=='project_root' and
        all(qualification[k] is False for k in FALSES),'Q qualification schema/authority')
    r.require(qualification['status']=='QUALIFIED_P2_Q_TESTED_SCOPE'
        and qualification['native_helper']==request['native_helper'],'qualified binary join')
    operation=qualification['operation_id']
    r.require(type(operation) is str and operation==str(uuid.UUID(operation)),'canonical Q operation UUID')
    for key,name in (('source_review','source-review.json'),('actual_review','actual-review.json')):
        ref=qualification[key]
        r.closed(ref,('path','bytes','sha256'))
        r.require(ref['path']==Q_PHASE+'/'+name,'exact Q review reference')
        pin({k:ref[k] for k in ('bytes','sha256')})
    r.require(operation in qualification['native_helper']['path'].rsplit('/',1)[-1],
        'native helper bound to Q operation')
    for field,expected in (('test_count',EXPECTED_Q_TESTS),('timestamp_controls',8),('native_fault_controls',2)):
        r.require(type(qualification[field]) is int and qualification[field]==expected,'qualified exact Q counts')
    _builder(qualification['native_builder_controls'])
    source=_accepted_review(q_source_review,'ACCEPTED_SOURCE_P2Q')
    actual=_accepted_review(q_actual_review,'ACCEPTED_P2Q_TESTED_SCOPE')
    r.require(type(source.get('sources')) is dict and 1<=len(source['sources'])<=256,
        'Q reviewed source pins')
    for path,item in source['sources'].items():
        r.windows_path(path)
        pin(item)
    r.require(all(source['sources'].get(path)==item for path,item in request['sources'].items()),
        'Q source review covers exact P sources')
    r.require(actual['reviewer']!=source['reviewer'] and actual['reviewer'] not in source['authors']
        and source['reviewer'] not in actual['authors'],'different Q source/actual reviewers')
    r.require(actual.get('operation_id')==operation and
        actual.get('source_review_sha256')==qualification['source_review']['sha256'],
        'Q actual operation/source-review join')
    for field,expected in (('tests_run',EXPECTED_Q_TESTS),('timestamp_controls_passed',8),
                           ('native_fault_controls_passed',2),('actual_tool_exit_code',0)):
        r.require(type(actual.get(field)) is int and actual[field]==expected,'actual exact Q counts/exit')
    r.require(actual.get('new_operation_owned_lifecycle_closed') is True and
        actual.get('native_helper')==qualification['native_helper'],'actual Q lifecycle/native artifact')
    _builder(actual.get('native_builder_controls'))
    r.require(actual['native_builder_controls']==qualification['native_builder_controls'],
        'native builder control join')
    r.require(qualification['api_mapping']==request['api_mapping'] and
        actual.get('api_mapping')==qualification['api_mapping'] and
        actual.get('api_mapping_native_identity')==qualification['api_mapping_native_identity'] and
        request['api_mapping']['path']==Q_PHASE+'/api-mapping_'+operation+'.json', 'accepted Q mapping receipt join')
    am.validate_receipt(api_receipt,query_plan,operation,qualification['native_helper'],
        qualification['api_mapping_native_identity'],request['sources'][am.PLAN]['sha256'])
    r.require(api_receipt['native_helper_native_identity']==qualification['native_builder_controls']['helper_identity'], 'emitted helper original native identity join')
    r.require(qualification['native_diagnostic']==request['native_diagnostic']==actual.get('native_diagnostic')==api_receipt['native_diagnostic']
        and qualification['native_diagnostic_native_identity']==actual.get('native_diagnostic_native_identity')==api_receipt['native_diagnostic_native_identity'], 'accepted diagnostic reference/identity join')
    handoff=qualification['artifact_handoff']
    r.closed(qualification['sharing_controls'],('cooperative_read_protected','ordinary_reader_strict','capability_authentication'))
    r.require(qualification['sharing_controls']==actual.get('sharing_controls') and all(v is True for v in qualification['sharing_controls'].values()),'accepted actual sharing controls')
    r.closed(handoff,('consumers_reaped','final_original_recheck','original_writers_held_through_consumers','artifacts'))
    r.require(handoff==actual.get('artifact_handoff') and all(handoff[k] is True for k in
        ('consumers_reaped','final_original_recheck','original_writers_held_through_consumers')),'accepted original-writer custody/return')
    expected_artifacts={'mapping':(request['api_mapping'],qualification['api_mapping_native_identity']),
        'diagnostic':(request['native_diagnostic'],qualification['native_diagnostic_native_identity']),
        'helper':(request['native_helper'],qualification['native_builder_controls']['helper_identity'])}
    items=handoff['artifacts']
    r.require(type(items) is list and len(items)==3 and {i['role'] for i in items}==set(expected_artifacts),'three qualified handoff artifacts')
    for item in items:
        r.closed(item,('role','reference','native_identity','writer_share'))
        ref,identity=expected_artifacts[item['role']]
        r.require(item['reference']==ref and item['native_identity']==identity and type(item['writer_share']) is int and item['writer_share']==1,'exact qualified original writer')
    r.require(utc(source['created_utc'])<=utc(actual['created_utc'])<=utc(qualification['created_utc'])
        <=utc(adoption['created_utc'])<=utc(request['created_utc']),'Q review/qualification/adoption order')
    r.closed(coverage,('schema','status','reviewer','authors','created_utc','recipe_sha256',
        'pin_index','findings','checks','limitations','launch_authorized','scientific_admission'))
    r.require(coverage['schema']=='cho51_p2_coverage_review_v1' and
        type(coverage['authors']) is list and 1<=len(coverage['authors'])<=8 and
        all(type(a) is str and 0<len(a)<=128 for a in coverage['authors']) and
        type(coverage['reviewer']) is str and coverage['reviewer'] not in coverage['authors']
        and coverage['findings']==[],'coverage independent identity')
    r.require(coverage['status']=='ACCEPTED_PROPOSED_P2_PHYSICAL_COVERAGE'
        and coverage['pin_index']==request['map_index'] and
        coverage['recipe_sha256']==request['sources']['tools/local_validation/p2r9/dependency_recipe.json']['sha256'],
        'coverage recipe/map join')
    r.require(coverage['launch_authorized'] is False and coverage['scientific_admission'] is False,'coverage no grant')









