"""Pure validators for exact Q-only running-schema observations. No fallback."""
from ..v1 import records as r
from .pe import host_basename

PLAN = 'tools/local_validation/p2r7/api_query_plan.json'
MODULE = 'C:/Windows/System32/kernelbase.dll'
Q_PHASE = 'runs/coordination/cho51_p3_dependency_prepare_20261029_q7'


def validate_plan(value):
    r.closed(value, ('schema','exact_query_names','os_version','files','negative_query',
                     'query_contract','target_host_loading_authorized'))
    r.require(value['schema']=='cho51_p7_api_query_plan_v1' and
        value['query_contract']=='api-ms-win-core-apiquery-l2-1-1' and
        value['negative_query']=='api-ms-win-codex-absent-l999-999-999.dll' and
        value['target_host_loading_authorized'] is False, 'exact API query scope')
    names=value['exact_query_names']
    r.require(type(names) is list and len(names)==14 and names==sorted(set(names)), 'exact14 query names')
    for name in names:
        r.require(type(name) is str and r.re.fullmatch(r'api-ms-win-core-[a-z0-9-]+\.dll',name), 'API query name')
    r.require(type(value['os_version']) is str and r.re.fullmatch(r'10\.0\.[0-9]+',value['os_version']), 'OS version')
    r.require(type(value['files']) is list and len(value['files'])==5, 'query platform pin count')
    expected={MODULE,'C:/Windows/System32/apisetschema.dll','C:/Windows/System32/cabinet.dll',
              'C:/Windows/System32/fontsub.dll','C:/Windows/System32/mswsock.dll'}
    r.require({p['path'] for p in value['files']}==expected, 'exact query platform pin scope')
    for item in value['files']:
        r.closed(item, ('path','bytes','sha256','file_version'))
        r.windows_path(item['path'],absolute=True)
        r.exact_int(item['bytes'],1,8*1024**2)
        r.require(type(item['sha256']) is str and r.HEX64.fullmatch(item['sha256']), 'platform digest')
        r.exact_string(item['file_version'],256)
    return value


def validate_receipt(value, plan, operation, helper, identity, plan_sha):
    validate_plan(plan)
    r.closed(helper, ('path','bytes','sha256'))
    r.require(helper['path']==Q_PHASE+'/native-helper_'+operation+'.dll', 'mapping emitted helper reference')
    r.exact_int(helper['bytes'],1,8*1024**2)
    r.require(type(helper['sha256']) is str and r.HEX64.fullmatch(helper['sha256']), 'mapping helper digest')
    r.closed(value, ('schema','operation_id','plan_sha256','native_helper','artifact_native_identity',
        'os_version','platform_files','query','controls','rows','target_hosts_loaded','loader_qualified','scientific_admission'))
    r.require(value['schema']=='cho51_q7_api_mapping_v1' and value['operation_id']==operation and
        value['plan_sha256']==plan_sha and value['native_helper']==helper and
        value['artifact_native_identity']==identity and type(identity) is str and
        r.re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',identity), 'mapping identity joins')
    r.require(value['os_version']==plan['os_version'] and value['platform_files']==plan['files'], 'exact OS/schema pins')
    q=value['query']
    r.closed(q, ('availability_gate','bootstrap_module','query_module','bootstrap_reference_released',
                'query_reference_released','buffer_wchars','negative_implemented','negative_hresult','negative_length',
                'small_buffer_hresult','small_buffer_length'))
    r.require(q['availability_gate'] is True and q['bootstrap_module']==MODULE and q['query_module']==MODULE
        and q['bootstrap_reference_released'] is True and q['query_reference_released'] is True
        and type(q['buffer_wchars']) is int and q['buffer_wchars']==260, 'owned schema query binding/closure')
    r.require(q['negative_implemented'] is False and type(q['negative_hresult']) is int
        and q['negative_hresult']<0 and type(q['negative_length']) is int and 0<=q['negative_length']<=260,
        'distinct observed negative availability/query results')
    r.require(type(q['small_buffer_hresult']) is int and q['small_buffer_hresult']==-2147024774
        and type(q['small_buffer_length']) is int and 1<q['small_buffer_length']<=260, 'observed insufficient-buffer result')
    r.closed(value['controls'], ('negative_lookup_recorded','small_buffer_refused','invalid_hresult_refused',
        'invalid_length_refused','invalid_termination_refused'))
    r.require(all(v is True for v in value['controls'].values()), 'query controls')
    rows=value['rows']
    r.require(type(rows) is list and len(rows)==14 and [x['name'] for x in rows]==plan['exact_query_names'], 'mapping exact roster')
    mapping={}
    for row in rows:
        r.closed(row, ('name','hresult','actual_length','host'))
        host_basename(row['host'])
        r.require(type(row['hresult']) is int and row['hresult']==0 and type(row['actual_length']) is int
            and row['actual_length']==len(row['host'])+1 and 1<row['actual_length']<=260, 'query result/length')
        mapping[row['name']]=[row['host']]
    r.require(value['target_hosts_loaded'] is False and value['loader_qualified'] is False
        and value['scientific_admission'] is False, 'mapping is schema-only')
    return mapping
