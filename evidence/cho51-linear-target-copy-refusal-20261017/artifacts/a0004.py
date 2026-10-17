"""Standard-library closeout of the exact fresh synthetic target Job."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import os
import re
import sys
from datetime import datetime,timezone
from pathlib import Path

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
sys.path.insert(0,str(RUN))
import origin

OUT=RUN/'validation_001'
ARCHIVE=ROOT/'evidence/cho51-linear-target-route-20261017'


def fields(value,expected):
    origin.need(type(value) is dict and all(type(value.get(k)) is type(v) and value[k]==v
        for k,v in expected.items()),'required exact field values differ: '+','.join(expected))


def write_once(path,raw):
    with Path(path).open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())


def job_absent(name):
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.OpenJobObjectW.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_wchar_p]
    api.OpenJobObjectW.restype=ctypes.c_void_p
    api.CloseHandle.argtypes=[ctypes.c_void_p]
    ctypes.set_last_error(0);handle=api.OpenJobObjectW(4,False,name);error=ctypes.get_last_error()
    if handle:api.CloseHandle(handle)
    origin.need(not handle and error==2,'fresh native Job absence unconfirmed')


def verify_native(directory,command,pins):
    directory=Path(directory)
    origin.need(directory.resolve(strict=True)==directory and directory.parent==ROOT/'runs/migration'
        and re.fullmatch(r'\d{8}T\d{6}Z_[a-f0-9]{10}',directory.name) is not None,
        'direct dispatched native directory required')
    admission=origin.document(directory/'admission.json')
    receipt=origin.document(directory/'receipt.json')
    deadline=origin.document(directory/'deadline.json')
    operations={name:sha for name,sha in pins['files'].items()
        if Path(name).parent==Path('tools/migration') and Path(name).suffix in {'.py','.ps1','.json','.lock'}
        or name=='evaluation/phase2_supervision_primitives.py'}
    runtimes={name:sha for name,sha in pins['runtime'].items()
        if Path(name)==ROOT/'.venv/Scripts/python.exe' or Path(name).name in {'python312.dll','python3.dll'}}
    name='pro3_migration_'+directory.name
    fields(admission,{'schema':'migration_admission_v1','source_sha256':origin.CANONICAL,'command':command,
        'operation_pins':operations,'selected_runtime_pins':runtimes,'process_mib':4096,'job_mib':5120,
        'active_ram_gib':4,'active_disk_gib':20,'native_threads':1,
        'peer_pause_file':'D:\\Aenv\\pro2\\WORK\\resume-20261015-001\\coordination\\PRO2_REQUEST_PRO3_PAUSE.json'})
    fields(receipt,{'schema':'migration_guard_receipt_v1','accepted':True,'job_name':name,
        'job_absent':True,'scientific_admission':False,'error':None})
    state=receipt['native_state'];result=receipt['result']
    flags=('job_created','created_suspended','limits_set','limits_query_verified','atomic_job_assignment_requested',
        'atomic_job_assignment_verified','assigned','membership_verified','resumed','job_empty_before_close','job_closed',
        'process_handle_closed','thread_handle_closed','root_exit_after_job_close','assignment_step_seen')
    fields(state,dict.fromkeys(flags,True)|{'job_named':name,'cleanup_errors':[],'peak_sampling_errors':[],
        'process_limit_bytes':4096*1024**2,'aggregate_limit_bytes':5120*1024**2})
    fields(result,{'reason':'normal','exit_code':0})
    origin.need(type(state['peak_samples']) is int and state['peak_samples']>0,'actual native peak samples required')
    for key,other,limit in (('peak_process_commit_bytes','peak_process_memory_bytes',4096*1024**2),
                          ('peak_job_commit_bytes','peak_job_memory_bytes',5120*1024**2)):
        origin.need(type(state[key]) is int and 0<state[key]<=limit and state[key]==result[other],
            'positive native peaks within fixed caps required')
    origin.need(state['peak_job_commit_bytes']>=state['peak_process_commit_bytes'],'Job peak below process peak')
    samples=admission['startup_samples']
    origin.need(len(samples)==2 and samples==receipt['startup_samples'] and all(
        type(s['available_ram_bytes']) is int and s['available_ram_bytes']>=10*1024**3
        and type(s['free_disk_bytes']) is int and s['free_disk_bytes']>=20*1024**3 for s in samples),
        'two genuine startup RAM10/disk20 samples required')
    utc=lambda value:datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(timezone.utc)
    start,end,limit=(utc(x) for x in (admission['started_utc'],receipt['completed_utc'],admission['deadline_utc']))
    origin.need((limit-start).total_seconds()==600 and start<=end<=limit,'exact600s native interval required')
    fields(deadline,{'schema':'phase2_supervision_deadlines_v1','attempt_deadline_utc':admission['deadline_utc']})
    origin.need((utc(deadline['session_deadline_utc'])-limit).total_seconds()==5,'exact5s margin required')
    job_absent(name)
    return {'native_directory':str(directory),'job_name':name,'accepted':True,'seconds':600,
        'process_mib':4096,'job_mib':5120,'started_utc':admission['started_utc'],
        'completed_utc':receipt['completed_utc'],'elapsed_native_seconds':(end-start).total_seconds(),
        'peak_process_bytes':state['peak_process_commit_bytes'],'peak_job_bytes':state['peak_job_commit_bytes'],
        'receipt_file_sha256':hashlib.sha256((directory/'receipt.json').read_bytes()).hexdigest(),
        'native_job_closed_empty_freshly_absent':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--expect-pins',required=True)
    args=parser.parse_args()
    pins=origin.document(RUN/'pins.json',args.expect_pins)
    origin.need(pins['schema']=='cho51_linear_target_route_pins_v1','fresh target pins required')
    for name,sha in pins['files'].items():origin.asset(ROOT/name,sha,8*1024**2)
    for group in ('runtime','runtime_modules'):
        for name,sha in pins.get(group,{}).items():
            path=Path(name)
            # Existing pinned Git executable has two hard links. This is the
            # sole exact read-only runtime exception, never a mutable data path.
            if path.name=='git.exe' and sha=='da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f':
                origin.need(path.resolve(strict=True)==path and path.stat().st_size==46480
                    and path.stat().st_nlink==2 and hashlib.sha256(path.read_bytes()).hexdigest()==sha,
                    'exact unchanged two-link Git runtime differs')
            else:origin.asset(path,sha,32*1024**2)
    review=origin.document(RUN/'source-review.json',pins['source_review_sha256'])
    fields(review,{'source_only':True,'remaining_actionable_findings':[],'files':pins['reviewed_files']})
    origin_before=origin.verify_origin_stages()
    contract=origin.document(RUN/'origin-contract.json',pins['origin_contract_file_sha256'])
    origin.need(contract==dict(schema='cho51_linear_target_route_origin_v1',**origin_before),
        'historical role-bound origin metadata changed')
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-I','-S','-B',str(RUN/'parent.py'),
        '--pins',str(RUN/'pins.json'),'--expect-pins',args.expect_pins,'--output',str(OUT)]
    dispatch=origin.document(RUN/'dispatch_001.json');dispatched=origin.document(RUN/'dispatch_result_001.json')
    for value in (dispatch,dispatched):fields(value,{'pins_sha256':args.expect_pins,
        'origin_contract_file_sha256':pins['origin_contract_file_sha256'],'source_training_replayed':False,
        'child_command':command,'expected_output':str(OUT),'scientific_admission':False})
    fields(dispatched,{'guard_exit_code':0})
    native=verify_native(dispatched['native_directory'],command,pins)
    q=origin.document(OUT/'qualification.json');result=origin.document(OUT/'result.json')
    fields(q,{'schema':'cho51_linear_target_route_qualification_v1','passed':True,'result':result,
        'pins_sha256':args.expect_pins,'canonical_files':432,'canonical_source_sha256':origin.CANONICAL,
        'runtime_pins_rechecked':5,'source_pins_rechecked':len(pins['files']),'unexpected_denials':0,
        'source_review_sha256':pins['source_review_sha256'],'constructor_dummy_forward_calls':1,
        'classifier_forward_calls':2,'backbone_forward_calls':2,'current_restore_count':1,
        'current_source_updates':0,'current_support_updates':1,'historical_gradient_updates':5253,
        'measured_cells':0,'scientific_admission':False,'torch_threads':1,'torch_interop_threads':1,'gpu_hidden':True})
    _,fixture,_=origin.original_inventory()
    fields(q,{'numpy_load_count':6,'numpy_loads':{
        str(fixture/'data/processed/cho2017/profile_a/subject_02.npz'):4,
        str(fixture/'data/processed/cho2017/profile_b_60hz_v1/subject_02.npz'):2}})
    fields(result,{'passed':True,'tests_passed':True,'pytest_exit':0,'collected_tests':pins['expected_tests'],
        'expected_tests':pins['expected_tests'],'skipped_reports':[],'historical_gradient_updates':5253,
        'current_source_updates':0,'current_support_updates':1,'current_restore_count':1,
        'source_training_replayed':False,'source_work_reused':True,'measured_cells':0,'scientific_admission':False,
        'unchanged_single_root_factory_verified':False,'unchanged_canonical_store_restore_verified':False})
    origin.need(len(result['reports'])==pins['expected_tests'] and all(row['phase']=='call'
        and row['outcome']=='passed' for row in result['reports']),'all focused boundary tests must pass')
    calls=q['observed_numerical_calls']
    origin.need(all(calls.get(k)==v for k,v in {'module_load_state_dict':2,'safetensors_load':2,'optimizer_init':1,
        'sgd_step':1,'tensor_backward':1,'autograd_backward':1}.items()),'exact numerical counter budget differs')
    target=origin.document(OUT/'target-witness.json');restore=origin.document(OUT/'restore-witness.json')
    origin.need(target==result['target_route_witness'] and restore==result['restore_witness'],'actual witnesses differ')
    fields(target,{'accepted':True,'engineering_only':True,'scientific_admission':False,'measured_cells':0,
        'record_cell_calls':0,'source_updates':0,'support_updates':1,'gradient_updates':1,
        'current_restore_callback_calls':1,'target_inference_calls':1,'source_state_sha256':origin.MODEL_STATE,
        'query_count':2,'unchanged_single_root_factory_verified':False})
    fields(restore,{'passed':True,'current_restore_count':1,'baseline_decodes':1,'selected_decodes':1,
        'strict_state_loads':2,'weights_file_sha256':origin.WEIGHTS_SHA,'weights_bytes':23294624,
        'selected_state_sha256':origin.MODEL_STATE,'tensor_count':223,'elements':5818138,'head_parameters':402,
        'new_explicit_two_root_staged_restore_verified':True,'unchanged_canonical_store_restore_verified':False})
    fields(target['witnesses'],{'calls':{'adaptation':1,'support_forward':1,'backward':1,'sgd_step':1,
        'query_forward':1,'runner_prediction':1},'finite_gradients':True,'query_inference_mode':True,
        'all_modules_eval':True,'source_unchanged':True,'backbone_and_buffers_unchanged':True,
        'query_labels_used_for_adaptation':False,'unused_pool_used_for_adaptation':False})
    origin.need(result['current_control_source']==pins['expected_current_context']
        and result['historical_source']['git_commit']==origin.HISTORICAL_COMMIT
        and result['recorder_control_source']['git_commit']=='277d7975ba400a9927bdd3e1495f6ade25ddea38',
        'three real Git contexts must remain separately bound')
    for name,sha in q['observed_loaded_module_hashes'].items():
        path=Path(name)
        origin.asset(path,sha,512*1024**2)
    original_inputs=origin.verify_inputs()
    origin.need(result['input_audit_before']==result['input_audit_after']==original_inputs,
        'before/after213 physical inputs differ')
    origin.need(not ARCHIVE.exists(),'unused target archive required')
    sources={ROOT/name for name in pins['reviewed_files']}
    sources.update(RUN/name for name in ('pins.json','origin-contract.json','source-review.json',
        'runtime-transition.json','dispatch_001.json','dispatch_result_001.json'))
    sources.update(RUN.glob('preflight*.json'))
    sources.update(OUT/name for name in ('qualification.json','result.json','target-witness.json','restore-witness.json','junit.xml','pytest.log'))
    sources.update(p for p in Path(native['native_directory']).iterdir() if p.is_file())
    original,_,_=origin.original_inventory()
    sources.add(Path(original['selection_evidence_path']))
    publication=origin.document(origin.PUBLICATION/'publication_001/publication-result.json',
        '86d8f400abc6345d18893fc4456152bba20115ac9946ddd1bcbf9109b1528f08')
    sources.add(Path(publication['manifest_path']))
    payloads=[]
    for path in sorted(sources):
        origin.need(path.is_relative_to(ROOT) and path.suffix.lower() not in {'.npz','.npy','.mat','.safetensors'},
            'archive must contain metadata only')
        maximum=32*1024**2 if path==Path(original['selection_evidence_path']) else 8*1024**2
        before=path.stat()
        origin.need(0<=before.st_size<=maximum,'archive payload exceeds role-bound limit')
        with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        raw,pin=origin.asset(path,sha,maximum,compact=True)
        payloads.append((path,raw,sha))
    ARCHIVE.mkdir();(ARCHIVE/'artifacts').mkdir();rows=[]
    for index,(path,raw,sha) in enumerate(payloads,1):
        relative=f'artifacts/a{index:04d}{path.suffix}'
        write_once(ARCHIVE/relative,raw);origin.asset(path,sha,max(1,len(raw)))
        origin.asset(ARCHIVE/relative,sha,max(1,len(raw)))
        rows.append({'source':path.relative_to(ROOT).as_posix(),'path':relative,'bytes':len(raw),'sha256':sha})
    summary={'schema':'cho51_linear_target_route_summary_v1','passed':True,'closed_utc':datetime.now(timezone.utc).isoformat(),
        'pins_sha256':args.expect_pins,'origin_contract_file_sha256':pins['origin_contract_file_sha256'],
        'source_context_files':len(pins['files']),'runtime_files':5,'runtime_module_files':len(pins.get('runtime_modules',{})),
        'tests_passed':pins['expected_tests'],'native':native,'current_restore_count':1,'current_source_updates':0,
        'current_support_updates':1,'current_gradient_updates':1,'historical_gradient_updates':5253,
        'engineering_only':True,'measured_cells':0,'scientific_admission':False,'original_case_attempts_remaining':0,
        'target_route_qualified':True,'new_explicit_two_root_staged_restore_verified':True,
        'unchanged_canonical_store_restore_verified':False,'unchanged_single_root_factory_verified':False,
        'physical_input_files_rechecked_after_job':213,'physical_input_bytes_rechecked_after_job':734579463,
        'current_control_source':result['current_control_source'],'historical_source':result['historical_source'],
        'recorder_control_source':result['recorder_control_source'],'loaded_module_files':len(q['observed_loaded_module_hashes']),
        'observed_numerical_calls':calls,'artifacts':len(rows)}
    write_once(ARCHIVE/'manifest.json',origin.canonical({'schema':'cho51_linear_target_route_manifest_v1','artifacts':rows}))
    write_once(ARCHIVE/'summary.json',origin.canonical(summary))
    write_once(ARCHIVE/'README.md',b'# Synthetic linear target route\n\nOne newly bounded staged source restoration, one head-only support SGD update and one two-row query inference batch. Historical 5,253 updates are reused without source replay. Engineering only; zero measured cells. Canonical single-root store/factories, full worker and scientific admission remain unqualified.\n')
    job_absent(native['job_name'])
    print(json.dumps({'passed':True,'archive':str(ARCHIVE),'artifacts':len(rows),
        'manifest_sha256':hashlib.sha256((ARCHIVE/'manifest.json').read_bytes()).hexdigest(),
        'summary_sha256':hashlib.sha256((ARCHIVE/'summary.json').read_bytes()).hexdigest()}))


if __name__=='__main__':main()
