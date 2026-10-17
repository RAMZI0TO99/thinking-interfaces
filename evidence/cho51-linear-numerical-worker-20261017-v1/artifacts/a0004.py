"""Post-Job standard-library audit of fresh numerical worker evidence."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
from fractions import Fraction
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
OUT=RUN/'validation_001'
ARCHIVE=ROOT/'evidence/cho51-linear-numerical-worker-20261017-v1'
sys.path.insert(0,str(RUN))
import origin


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def fields(value,expected):
    origin.need(type(value) is dict and all(type(value.get(k)) is type(v) and value[k]==v for k,v in expected.items()),
        'required exact field values differ: '+','.join(expected))


def write_once(path,raw):
    with Path(path).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def envelope(item,payload):
    value={'schema_version':1,'phase':2,'kind':'engineering_smoke','payload':payload}
    value['sha256']=hashlib.sha256(origin.canonical(value).rstrip(b'\n')).hexdigest()
    origin.need(item==value,'exact engineering envelope required')


def native_tools():
    path=origin.TARGET/'closeout.py'
    origin.asset(path,'f47ee0bbff4abafc5cde27a8223fd736382ffb09d508a8c19d42bc03bf487854',1024**2)
    spec=importlib.util.spec_from_file_location('_worker_frozen_native_closeout',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def verify_pins(pins,pins_sha,contract):
    origin.need(digest(RUN/'pins.json')==pins_sha,'fresh worker pins changed')
    for name,sha in pins['files'].items():
        path=ROOT/name
        large=(sha==origin.EVIDENCE_SHA and contract['files'].get(str(path))==sha
            and contract['roles'].get(str(path))=='complete_evidence' and path.stat().st_size==23087023)
        origin.asset(path,sha,32*1024**2 if large else 8*1024**2)
    for group in ('runtime','runtime_modules'):
        for name,sha in pins[group].items():
            path=Path(name)
            if (path==Path('C:/Users/aladdin-alyanai/AppData/Local/Programs/Git/cmd/git.exe')
                    and sha=='da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f'):
                origin.need(path.resolve(strict=True)==path and path.stat().st_size==46480
                    and path.stat().st_nlink==2 and digest(path)==sha,'exact read-only two-link Git runtime required')
            else:origin.asset(path,sha,64*1024**2)
    verify_canonical(pins)
    for name,sha in pins['supporting_runtime_sources'].items():origin.asset(Path(name),sha,8*1024**2)
    origin.need(origin.document(Path(pins['runtime_transition_path']),pins['runtime_transition_sha256'])==pins['runtime_transition'],
        'fresh current transition witness differs')
    review=origin.document(RUN/'source-review.json',pins['source_review_sha256'])
    fields(review,{'source_only':True,'remaining_actionable_findings':[],'files':pins['reviewed_files']})


def verify_canonical(pins):
    path=ROOT/'tools/migration/source-files.json'
    manifest=origin.document(path,pins['files']['tools/migration/source-files.json'])
    rows=manifest['files'];origin.need(len(rows)==432,'exact canonical432 manifest required')
    aggregate=hashlib.sha256('\n'.join(f"{r['path']}:{r['sha256']}" for r in rows).encode()).hexdigest()
    origin.need(aggregate==manifest['source_sha256']==origin.CANONICAL,'canonical manifest aggregate differs')
    for row in rows:origin.asset(ROOT/row['path'],row['sha256'],8*1024**2)
    directories=('core','encoder','adaptation','data','realtime','evaluation','scripts','tests','configs')
    found=set()
    for directory in directories:
        for candidate in (ROOT/directory).rglob('*'):
            if candidate.is_file() and candidate.suffix.lower() in {'.py','.toml','.ps1'}:
                relative=candidate.relative_to(ROOT).as_posix()
                if not relative.startswith(('data/raw/','data/processed/','data/interim/')) and candidate.name!='local.toml':found.add(relative)
    found.update(row['path'] for row in rows if row['path'].split('/')[0] not in directories)
    origin.need(found=={row['path'] for row in rows},'added or removed canonical source detected')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--expect-pins',required=True)
    args=parser.parse_args();pins=origin.document(RUN/'pins.json',args.expect_pins)
    fields(pins,{'schema':'cho51_linear_numerical_worker_pins_v1','canonical_files':432,
        'canonical_source_sha256':origin.CANONICAL,'current_gradient_updates':1,'scientific_admission':False})
    contract=origin.document(RUN/'origin-contract.json',pins['origin_contract_file_sha256'])
    stages=origin.verify_origin_stages()
    origin.need(contract==dict(schema='cho51_linear_worker_origin_contract_v1',**stages),'fresh role-bound origin changed')
    verify_pins(pins,args.expect_pins,contract)
    command=[str(ROOT/'.venv/Scripts/python.exe'),'-I','-S','-B',str(RUN/'parent.py'),
        '--pins',str(RUN/'pins.json'),'--expect-pins',args.expect_pins,'--output',str(OUT)]
    dispatch=origin.document(RUN/'dispatch_001.json');dispatched=origin.document(RUN/'dispatch_result_001.json')
    for value in (dispatch,dispatched):fields(value,{'pins_sha256':args.expect_pins,
        'origin_contract_file_sha256':pins['origin_contract_file_sha256'],'source_training_replayed':False,
        'child_command':command,'expected_output':str(OUT),'scientific_admission':False})
    fields(dispatched,{'guard_exit_code':0})
    native_module=native_tools();native=native_module.verify_native(dispatched['native_directory'],command,pins)
    q=origin.document(OUT/'qualification.json');result=origin.document(OUT/'result.json')
    budget=dict(source_updates=0,restore_count=1,support_updates=1,gradient_updates=1,
        target_inference_calls=1,query_count=2,model_constructions=1,measured_cells=0)
    fields(q,{'schema':'cho51_linear_numerical_worker_qualification_v1','passed':True,'pins_sha256':args.expect_pins,
        'result':result,'canonical_source_sha256':origin.CANONICAL,'canonical_files':432,
        'source_pins_rechecked':len(pins['files']),'runtime_pins_rechecked':5,'runtime_module_pins_rechecked':18,
        'source_review_sha256':pins['source_review_sha256'],'torch_threads':1,'torch_interop_threads':1,
        'gpu_hidden':True,'unexpected_denials':0,'model_constructions':1,'constructor_dummy_forward_calls':1,
        'current_restore_count':1,'target_inference_calls':1,'current_gradient_updates':1,
        'current_source_updates':0,'current_support_updates':1,'current_counter_ledger':budget,
        'full_worker_verified':False,'scientific_admission':False,'measured_cells':0,'original_case_attempts_remaining':0,
        'classifier_forward_calls':2,'backbone_forward_calls':2,'empty_mask_container_count':2,
        'parameterless_clone_reinitialization_count':4,'numpy_load_count':6})
    fields(result,{'schema':'cho51_linear_numerical_worker_result_v1','passed':True,'tests_passed':True,'pytest_exit':0,
        'collected_tests':pins['expected_tests'],'expected_tests':pins['expected_tests'],'skipped_reports':[],
        'executed_test_calls':pins['expected_tests'],'pytest_maxfail':1,'backend_calls':1,'verifier_calls':2,
        'fresh_numerical_worker_engineering_qualified':True,'current_gradient_updates':1,'current_source_updates':0,
        'current_support_updates':1,'current_restore_count':1,'target_inference_calls':1,'query_count':2,
        'current_counter_ledger':budget,'native_closeout_status':'pending_external_post_job',
        'historical_gradient_updates':5253,'measured_cells':0,'scientific_admission':False})
    origin.need(type(q['worker_lock_checks']) is int and q['worker_lock_checks']>0,'fresh numerical operations must cross live canonical lock')
    origin.need(len(result['reports'])==pins['expected_tests'] and all(row['phase']=='call' and row['outcome']=='passed'
        for row in result['reports']),'all exact boundary tests must pass')
    suites=list(ET.parse(OUT/'junit.xml').getroot().iter('testsuite'))
    origin.need(sum(int(s.attrib['tests']) for s in suites)==pins['expected_tests'] and all(
        int(s.attrib.get(k,'0'))==0 for s in suites for k in ('failures','errors','skipped')),'independent JUnit exact counts required')
    fields(result['engineering_completion'],{'engineering_success':1,'measured':0,'failed':0})
    fixture=OUT/'fixture';recorder=fixture/'runs/phase2/lifecycle';workspace=OUT/'cases'/origin.CASE
    request_path=workspace/'request.json';claim_path=recorder/'claims'/(origin.CASE+'.attempt1.claim.json')
    attestation_path=workspace/'parent-attestation.json'
    request=origin.document(request_path,result['request_sha256']);historical=request['historical_binding']
    claim=origin.document(claim_path,result['claim_file_sha256']);attestation=origin.document(attestation_path,result['attestation_file_sha256'])
    plan={'dataset':'cho2017','target_subject':'subject_02','method':'labram_linear','shots_per_class':5,'model_seed':11,'repetition':1}
    fields(request,{'schema':'cho51_linear_numerical_worker_request_v1','expected_numerical_budget':budget,
        'engineering_only':True,'scientific_admission':False,'native_closeout_status':'pending_external_post_job'})
    fields(historical,{'schema':'cho51_linear_worker_request_v1','case_id':origin.CASE,'plan':plan,
        'fixture_root':str(fixture),'recorder_root':str(recorder),'workspace':str(workspace),
        'pins_path':str(RUN/'pins.json'),'independent_pins_sha256':args.expect_pins,'execution_source_sha256':origin.CANONICAL,
        'owner_decision_sha256':pins['owner_decision_sha256'],'origin_contract_path':str(RUN/'origin-contract.json'),
        'origin_contract_file_sha256':pins['origin_contract_file_sha256'],'claim_path':str(claim_path),
        'claim_file_sha256':result['claim_file_sha256'],'attempt':1})
    current={'git_commit':historical['fixture_git_commit'],'git_dirty':historical['fixture_git_dirty'],
        'source_sha256':historical['fixture_source_sha256']}
    origin.need(current==pins['expected_current_context']==result['fixture_source'],'fresh Git/TOML control context differs')
    fields(claim['payload'],{'purpose':'pilot_case_claim','case':plan,'worker':'cho51_linear_numerical_worker_engineering_v1',
        'attempt':1,'environment_sha256':historical['environment_sha256'],'engineering_only':True,'source':current})
    envelope(claim,claim['payload'])
    binding=dict(request_sha256=result['request_sha256'],claim_sha256=result['claim_file_sha256'],
        pins_sha256=args.expect_pins,workspace=str(workspace))
    fields(q,{'current_worker_binding':binding})
    execution_path=workspace/'current-execution.json'
    execution=origin.document(execution_path,result['current_execution_file_sha256']);payload=execution['payload']
    envelope(execution,payload)
    fields(payload,dict(schema='cho51_linear_numerical_execution_v1',**binding,expected_numerical_budget=budget,
        current_counter_ledger=budget,current_control_source=current,historical_source=stages['summary']['historical_source'],
        native_closeout_status='pending_external_post_job',engineering_only=True,scientific_admission=False,measured_cells=0))
    origin.need(payload==result['current_execution'],'result/current physical envelope differs')
    target_path=workspace/'target-witness.json';restore_path=workspace/'restore-witness.json'
    origin.need(set(payload['physical_outputs'])=={'target-witness.json','restore-witness.json'},'exact2 numerical outputs required')
    witnesses={}
    for path,key in ((target_path,'target_route_witness'),(restore_path,'restore_witness')):
        row=payload['physical_outputs'][path.name];value=origin.document(path,row['sha256'])
        origin.need(path.stat().st_size==row['bytes'] and value==payload[key],'embedded/physical output differs')
        fields(value,{'current_worker_binding':binding});witnesses[path.name]=value
    target=witnesses['target-witness.json'];restore=witnesses['restore-witness.json'];observed=target['witnesses']
    fields(target,{'accepted':True,'engineering_only':True,'scientific_admission':False,'measured_cells':0,
        'record_cell_calls':0,'source_updates':0,'support_updates':1,'gradient_updates':1,'current_restore_callback_calls':1,
        'target_inference_calls':1,'source_state_sha256':origin.MODEL_STATE,'query_count':2,
        'contract':stages['summary']['target_contract'],'profile_binding':stages['summary']['target_profile_binding'],
        'provenance':{'current':current,'historical':stages['summary']['historical_source']}})
    fields(restore,{'passed':True,'current_restore_count':1,'baseline_decodes':1,'selected_decodes':1,'strict_state_loads':2,
        'weights_file_sha256':origin.WEIGHTS_SHA,'weights_bytes':23294624,'selected_state_sha256':origin.MODEL_STATE,
        'tensor_count':223,'elements':5818138,'head_parameters':402,'new_explicit_two_root_staged_restore_verified':True,
        'unchanged_canonical_store_restore_verified':False,'unchanged_single_root_factory_verified':False,
        'current_control_source':current,'historical_source':stages['summary']['historical_source']})
    fields(observed,{'calls':{'adaptation':1,'support_forward':1,'backward':1,'sgd_step':1,'query_forward':1,'runner_prediction':1},
        'finite_gradients':True,'query_inference_mode':True,'all_modules_eval':True,'source_unchanged':True,
        'backbone_and_buffers_unchanged':True,'query_labels_used_for_adaptation':False,'unused_pool_used_for_adaptation':False})
    before=observed['before_state_tensors'];after=observed['after_state_tensors']
    origin.need(len(before)==223 and before==target['source_state_tensors'] and set(before)==set(after)
        and {n for n in before if before[n]!=after[n]}=={'head.weight','head.bias'},'exact frozen backbone and both head changes required')
    logits=target['query_logits'];labels=target['query_targets']
    origin.need(type(logits) is list and len(logits)==2 and all(type(row) is list and len(row)==2 for row in logits)
        and all(type(v) in (int,float) and math.isfinite(v) for row in logits for v in row)
        and labels==stages['summary']['target_contract']['query_labels'],'finite route-derived logits/labels required')
    predictions=[0 if row[0]>=row[1] else 1 for row in logits];confusion=[[0,0],[0,0]]
    for label,prediction in zip(labels,predictions,strict=True):confusion[label][prediction]+=1
    score=sum((Fraction(confusion[i][i],sum(confusion[i])) for i in range(2)),Fraction())/2
    origin.need(target['confusion_matrix']==confusion and target['balanced_accuracy']==[score.numerator,score.denominator],
        'pure current metric derivation differs')
    calls=q['observed_numerical_calls'];origin.need(payload['observed_numerical_calls']==calls,'authenticated runtime call map differs')
    origin.need(all(type(calls.get(k)) is int and calls[k]==v for k,v in dict(module_load_state_dict=2,safetensors_load=2,
        optimizer_init=1,sgd_step=1,tensor_backward=1,autograd_backward=1).items()) and calls.get('model_module_init',0)>0,
        'exact successful current runtime budget required')
    proof=result['proof'];fields(proof,{'request_sha256':result['request_sha256'],'case_id':origin.CASE,
        'claim_sha256':result['claim_file_sha256'],'pins_sha256':args.expect_pins,
        'execution_file_sha256':digest(execution_path),'target_witness_file_sha256':digest(target_path),
        'restore_witness_file_sha256':digest(restore_path),'verified_origin_files':len(stages['files']),
        'adapted_state_sha256':observed['adapted_state_sha256'],'native_closeout_status':'pending_external_post_job'})
    fields(attestation,{'schema':'cho51_linear_numerical_worker_attestation_v1','request_sha256':result['request_sha256'],
        'case_id':origin.CASE,'proof':proof,'native_closeout_status':'pending_external_post_job',
        'observed_numerical_counts':budget,'expected_numerical_budget':budget,'engineering_only':True,
        'scientific_admission':False,'measured_cells':0})
    intent_path=recorder/'engineering_intents'/(origin.CASE+'.intent.json')
    success_path=recorder/'engineering_successes'/(origin.CASE+'.success.json')
    for path,purpose in ((intent_path,'pilot_case_engineering_success_intent'),(success_path,'pilot_case_engineering_success')):
        envelope(origin.document(path),{'purpose':purpose,'case':plan,'attempt':1,
            'attested_evidence_sha256':result['attestation_file_sha256'],'engineering_only':True})
    origin.need(set(recorder.rglob('*.json'))=={claim_path,intent_path,success_path},'exact claim/intent/engineering receipt required')
    for name in ('cells','successes','publication_intents'):origin.need(not(recorder/name).exists(),'scientific ledger forbidden')
    configs=('configs/base.toml','configs/benchmark.toml','configs/phase2/protocol.toml',
        'configs/phase2/selection_ceiling.toml','configs/phase2/cho_profile_b_60hz.toml')
    origin.need({p.relative_to(fixture).as_posix() for p in (fixture/'configs').rglob('*') if p.is_file()}==set(configs)
        and not(fixture/'data').exists() and not(fixture/'.git').exists(),'isolated five-TOML control fixture required')
    for name in configs:origin.asset(fixture/name,pins['files'][name],1024**2)
    fingerprint=hashlib.sha256('\n'.join(f'{name}:{pins["files"][name]}' for name in sorted(configs)).encode()).hexdigest()
    origin.need(fingerprint==historical['fixture_source_sha256'],'five-TOML fingerprint changed')
    origin.need(payload['input_audit_before']==payload['input_audit_after']==result['input_audit_before']
        ==result['input_audit_after']==origin.verify_inputs(),'all213 inputs differ before/after/post-Job')
    expected={'event':'socket.__new__','classification':'blocked_optional_ipv6_import_probe',
        'source_file':str(ROOT/'.venv/Lib/site-packages/urllib3/util/connection.py'),
        'source_sha256':pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py']}
    origin.need(q['denied_operations'] in ([],[expected]),'unexpected audit denial')
    for path,sha in q['observed_loaded_module_hashes'].items():origin.asset(Path(path),sha,512*1024**2)
    native_module.job_absent(native['job_name']);origin.need(not ARCHIVE.exists(),'unused numerical worker archive required')
    sources={ROOT/name for name in pins['reviewed_files']}
    sources.update(RUN/name for name in ('pins.json','source-review.json','origin-contract.json','dispatch_001.json','dispatch_result_001.json'))
    sources.update(RUN.glob('preflight*.json'))
    sources.update((OUT/'qualification.json',OUT/'result.json',OUT/'junit.xml',OUT/'pytest.log',request_path,claim_path,
        attestation_path,intent_path,success_path,execution_path,target_path,restore_path))
    sources.update(fixture/name for name in configs)
    sources.update(path for path in Path(native['native_directory']).iterdir() if path.is_file())
    payloads=[]
    for path in sorted(sources):
        origin.need(path.is_relative_to(ROOT) and path.suffix.lower() not in {'.npz','.npy','.mat','.safetensors'},
            'archive excludes arrays, weights and ancestor packet copies')
        sha=digest(path);raw,pin=origin.asset(path,sha,8*1024**2,compact=True);payloads.append((path,raw,pin))
    verify_pins(pins,args.expect_pins,contract)
    ARCHIVE.mkdir();write_once(ARCHIVE/'.gitattributes',b'* -text\n');(ARCHIVE/'artifacts').mkdir();rows=[]
    for index,(path,raw,pin) in enumerate(payloads,1):
        relative=f'artifacts/a{index:04d}{path.suffix}';write_once(ARCHIVE/relative,raw)
        origin.asset(path,pin[-1],max(len(raw),1));origin.asset(ARCHIVE/relative,pin[-1],max(len(raw),1))
        rows.append({'source':path.relative_to(ROOT).as_posix(),'path':relative,'bytes':len(raw),'sha256':pin[-1]})
    summary={'schema':'cho51_linear_numerical_worker_summary_v1','passed':True,'closed_utc':datetime.now(timezone.utc).isoformat(),
        'pins_sha256':args.expect_pins,'origin_contract_file_sha256':pins['origin_contract_file_sha256'],
        'source_context_files':len(pins['files']),'runtime_files':5,'runtime_modules':18,'tests_passed':pins['expected_tests'],
        'native':native,'native_closeout_status':'verified_external_post_job','backend_calls':1,'verifier_calls':2,
        'engineering_successes':1,'measured_cells':0,'current_counter_ledger':budget,'observed_numerical_calls':calls,
        'fresh_numerical_worker_engineering_qualified':True,'scientific_admission':False,
        'unchanged_canonical_worker_verified':False,'full_worker_verified':False,'unchanged_single_root_factory_verified':False,
        'current_control_source':current,'historical_source':result['historical_source'],
        'request_sha256':result['request_sha256'],'claim_file_sha256':result['claim_file_sha256'],
        'attestation_file_sha256':result['attestation_file_sha256'],'current_execution_file_sha256':digest(execution_path),
        'qualification_file_sha256':digest(OUT/'qualification.json'),'verified_origin_files':len(stages['files']),
        'loaded_module_files':len(q['observed_loaded_module_hashes']),'physical_input_files_rechecked_after_job':213,
        'physical_input_bytes_rechecked_after_job':734579463,'original_case_attempts_remaining':0,'artifacts':len(rows),
        'query_logits':logits,'query_targets':labels,'query_predictions':predictions,'confusion_matrix':confusion,
        'balanced_accuracy':[score.numerator,score.denominator],
        'correct_query_predictions':sum(a==b for a,b in zip(labels,predictions,strict=True)),
        'scientific_predictive_performance_qualified':False,'adapted_state_sha256':observed['adapted_state_sha256']}
    write_once(ARCHIVE/'manifest.json',origin.canonical({'schema':'cho51_linear_numerical_worker_manifest_v1','artifacts':rows}))
    write_once(ARCHIVE/'summary.json',origin.canonical(summary))
    write_once(ARCHIVE/'README.md',b'# Fresh linear numerical worker engineering integration\n\nOne locked worker performs one selected-source restore, one support update and one two-trial query inference. Backend once and two metadata verifications produce one engineering success and zero measured cells. Original source training is reused. Native cleanup is qualified externally after process exit. Scientific execution remains pending.\n')
    native_module.job_absent(native['job_name'])
    print(json.dumps({'passed':True,'archive':str(ARCHIVE),'artifacts':len(rows),
        'manifest_sha256':digest(ARCHIVE/'manifest.json'),'summary_sha256':digest(ARCHIVE/'summary.json'),
        'engineering_successes':1,'measured_cells':0,'current_counter_ledger':budget}))


if __name__=='__main__':main()
