"""Owned synthetic data only. This module never reads candidate sources."""
import hashlib
from .protocol import roster_digest

def retained(path='D:/fixture/input.py',raw=b'pass\n',role='source'):
    return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),role=role,
        native_identity=dict(schema='cho51_lv_native_identity_v1',volume_serial='0000000000000001',
                             file_id='00000000000000000000000000000001',volume_kind='local_fixed',filesystem='NTFS'),
        owner='q_owned_fixture',sharing=dict(read=True,write=False,delete=False))

def collection_fixture():
    modules=['docs/phase2/cho51_p3_adapter_v1/test_mapping.py','docs/phase2/cho51_p3_adapter_v1/test_telemetry.py']
    counts=[[1]*6+[4,9,5,2,3,6,2,2],[1]*4+[34,19,5,4,4,4,4]]
    sources={m:retained('D:/fixture/'+m) for m in modules}
    functions=[]; rows=[]
    for module,numbers in zip(modules,counts):
        for index,count in enumerate(numbers):
            name='test_owned_'+str(index)
            functions.append(dict(module=module,node_prefix=module+'::'+name,expected_cases=count))
            for p in range(count):
                parameter=None if count==1 else 'owned-'+str(p)
                rows.append(dict(ordinal=len(rows),nodeid=module+'::'+name+('' if parameter is None else '['+parameter+']'),
                     module=module,original_function_name=name,parameter_id=parameter,source_ref=sources[module],
                     item_type='_pytest.python.Function',collection_sequence=len(rows)))
    static=dict(schema='cho51_p3_local_validation_test_roster_v1',expected_total=117,function_count=25,
                functions=functions,candidate_source_pins={m:{k:sources[m][k] for k in ('bytes','sha256')} for m in modules})
    summary=dict(pytest_exit_code=0,collection_errors=0,collection_skips=0,deselected=0,item_count=117,
       function_counts={r['node_prefix']:r['expected_cases'] for r in functions},
       ordered_roster_sha256=roster_digest([r['nodeid'] for r in rows]),fixture_setup_calls=0,runtest_protocol_calls=0,phase_report_calls=0)
    return static,sources,rows,summary
