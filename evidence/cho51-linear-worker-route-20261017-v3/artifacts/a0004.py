"""Standard-library audit and flat metadata archive of one fresh worker Job."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
OUT=RUN/'validation_001'
ARCHIVE=ROOT/'evidence/cho51-linear-worker-route-20261017-v3'
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
    review=origin.document(RUN/'source-review.json',pins['source_review_sha256'])
    fields(review,{'source_only':True,'remaining_actionable_findings':[],'files':pins['reviewed_files']})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--expect-pins',required=True)
    args=parser.parse_args();pins=origin.document(RUN/'pins.json',args.expect_pins)
    fields(pins,{'schema':'cho51_linear_worker_route_pins_v3','canonical_files':432,
        'canonical_source_sha256':origin.CANONICAL,'current_gradient_updates':0,'scientific_admission':False})
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
    isolated_sources={}
    for name,relative,sha,nodes in (
        ('settings','adaptation/labram_manifest.py','cd83efea8d7c2a67d49b9505625787f939b2bb47f206bc109ab0d362f41fd36a',
            ['LaBraMTuningSettings']),
        ('target','docs/phase2/cho51_linear_target_route_v1/target_route.py',
            '80468b32ef18c9efa58502077797f2e02925ba13cfbe5d83ce0b33b62c042500',
            ['PLAN','SELECTED_STATE_SHA256','SETTINGS','SUBJECTS','TRIAL_IDS','_need','prepare_target_contract','validate_binding'])):
        path=ROOT/relative;origin.asset(path,sha,8*1024**2)
        isolated_sources[name]={'path':str(path),'sha256':sha,'bytes':path.stat().st_size,'selected_nodes':nodes}
    isolated={'schema':'cho51_linear_worker_metadata_ast_v2','full_source_modules_imported':False,
        'numerical_imports_executed':False,'source_derived_settings_class':True,'sources':isolated_sources}
    origin.need(result['metadata_isolation']==isolated,'independent exact metadata AST receipt differs')
    fields(q,{'schema':'cho51_linear_worker_route_qualification_v3','passed':True,'pins_sha256':args.expect_pins,
        'metadata_isolation':result['metadata_isolation'],'forbidden_numerical_model_chain_imports':[],
        'result':result,'canonical_source_sha256':origin.CANONICAL,'canonical_files':432,
        'source_pins_rechecked':len(pins['files']),'runtime_pins_rechecked':5,'runtime_module_pins_rechecked':18,
        'source_review_sha256':pins['source_review_sha256'],'torch_threads':1,'torch_interop_threads':1,
        'gpu_hidden':True,'unexpected_denials':0,'observed_numerical_calls':{},'model_constructions':0,
        'current_restore_count':0,'target_inference_calls':0,'current_gradient_updates':0,
        'current_source_updates':0,'current_support_updates':0,'actual_study_arrays_decoded':False,
        'actual_weights_decoded':False,'full_worker_verified':False,'unchanged_canonical_worker_verified':False,
        'scientific_admission':False,'measured_cells':0,'original_case_attempts_remaining':0})
    fields(result,{'schema':'cho51_linear_worker_route_result_v3','passed':True,'tests_passed':True,'pytest_exit':0,
        'collected_tests':pins['expected_tests'],'expected_tests':pins['expected_tests'],'skipped_reports':[],
        'executed_test_calls':pins['expected_tests'],'pytest_maxfail':1,
        'backend_calls':1,'verifier_calls':2,'worker_route_engineering_qualified':True,
        'current_gradient_updates':0,'current_source_updates':0,'current_support_updates':0,
        'current_restore_count':0,'current_target_inference_calls':0,'historical_gradient_updates':5253,
        'prior_target_restore_count':1,'prior_target_support_updates':1,'prior_target_inference_calls':1,
        'prior_target_query_count':2,'measured_cells':0,'scientific_admission':False,'original_case_attempts_remaining':0})
    origin.need(len(result['reports'])==pins['expected_tests'] and all(row['phase']=='call' and row['outcome']=='passed'
        for row in result['reports']),'all exact boundary tests must pass')
    suites=list(ET.parse(OUT/'junit.xml').getroot().iter('testsuite'))
    origin.need(sum(int(s.attrib['tests']) for s in suites)==pins['expected_tests'] and all(
        int(s.attrib.get(k,'0'))==0 for s in suites for k in ('failures','errors','skipped')),
        'independent JUnit exact counts required')
    fields(result['engineering_completion'],{'engineering_success':1,'measured':0,'failed':0})
    fixture=OUT/'fixture';recorder=fixture/'runs/phase2/lifecycle';workspace=OUT/'cases'/origin.CASE
    request_path=workspace/'request.json';claim_path=recorder/'claims'/(origin.CASE+'.attempt1.claim.json')
    attestation_path=workspace/'parent-attestation.json'
    request=origin.document(request_path,result['request_sha256'])
    claim=origin.document(claim_path,result['claim_file_sha256'])
    attestation=origin.document(attestation_path,result['attestation_file_sha256'])
    plan={'dataset':'cho2017','target_subject':'subject_02','method':'labram_linear','shots_per_class':5,'model_seed':11,'repetition':1}
    fields(request,{'schema':'cho51_linear_worker_request_v1','case_id':origin.CASE,'plan':plan,
        'fixture_root':str(fixture),'recorder_root':str(recorder),'workspace':str(workspace),
        'pins_path':str(RUN/'pins.json'),'independent_pins_sha256':args.expect_pins,'execution_source_sha256':origin.CANONICAL,
        'owner_decision_sha256':pins['owner_decision_sha256'],'origin_contract_path':str(RUN/'origin-contract.json'),
        'origin_contract_file_sha256':pins['origin_contract_file_sha256'],'claim_path':str(claim_path),
        'claim_file_sha256':result['claim_file_sha256'],'attempt':1})
    current={'git_commit':request['fixture_git_commit'],'git_dirty':request['fixture_git_dirty'],
        'source_sha256':request['fixture_source_sha256']}
    origin.need(current==pins['expected_current_context']==result['fixture_source'],'actual fresh Git/TOML context differs')
    fields(claim['payload'],{'purpose':'pilot_case_claim','case':plan,'worker':'cho51_linear_worker_route_engineering',
        'attempt':1,'environment_sha256':request['environment_sha256'],'engineering_only':True,'source':current})
    envelope(claim,claim['payload'])
    proof=result['proof'];fields(proof,{'request_sha256':result['request_sha256'],'case_id':origin.CASE,
        'verified_origin_files':len(stages['files']),'claim_file_sha256':result['claim_file_sha256']})
    for key,value in stages['summary'].items():
        if key in proof:origin.need(type(proof[key]) is type(value) and proof[key]==value,'verified origin proof field changed: '+key)
    for key,value in request.items():
        if key in proof:origin.need(type(proof[key]) is type(value) and proof[key]==value,'request/proof field differs: '+key)
    fields(attestation,{'schema':'cho51_linear_worker_attestation_v1','request_sha256':result['request_sha256'],
        'case_id':origin.CASE,'claim_file_sha256':result['claim_file_sha256'],'proof':proof})
    intent_path=recorder/'engineering_intents'/(origin.CASE+'.intent.json')
    success_path=recorder/'engineering_successes'/(origin.CASE+'.success.json')
    for path,purpose in ((intent_path,'pilot_case_engineering_success_intent'),(success_path,'pilot_case_engineering_success')):
        item=origin.document(path)
        envelope(item,{'purpose':purpose,'case':plan,'attempt':1,'attested_evidence_sha256':result['attestation_file_sha256'],
            'engineering_only':True})
    origin.need(set(recorder.rglob('*.json'))=={claim_path,intent_path,success_path},'exact claim/intent/engineering receipt required')
    for name in ('cells','successes','publication_intents'):origin.need(not(recorder/name).exists(),'scientific ledger forbidden')
    configs=('configs/base.toml','configs/benchmark.toml','configs/phase2/protocol.toml',
        'configs/phase2/selection_ceiling.toml','configs/phase2/cho_profile_b_60hz.toml')
    origin.need({p.relative_to(fixture).as_posix() for p in (fixture/'configs').rglob('*') if p.is_file()}==set(configs)
        and not(fixture/'data').exists() and not(fixture/'.git').exists(),'isolated five-TOML-only control fixture required')
    for name in configs:origin.asset(fixture/name,pins['files'][name],1024**2)
    fingerprint=hashlib.sha256('\n'.join(f'{name}:{pins["files"][name]}' for name in sorted(configs)).encode()).hexdigest()
    origin.need(fingerprint==request['fixture_source_sha256'],'fresh five-TOML fingerprint changed')
    origin.need(result['input_audit_before']==result['input_audit_after']==origin.verify_inputs(),
        'all213 original inputs must match before/after/independent post-Job hashes')
    origin.need(result['target_metrics']==stages['summary']['target_metrics'],'historical zero-of-two outcome changed')
    expected={'event':'socket.__new__','classification':'blocked_optional_ipv6_import_probe',
        'source_file':str(ROOT/'.venv/Lib/site-packages/urllib3/util/connection.py'),
        'source_sha256':pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py']}
    origin.need(q['denied_operations'] in ([],[expected]),'unexpected audit denial')
    for path,sha in q['observed_loaded_module_hashes'].items():origin.asset(Path(path),sha,64*1024**2)
    native_module.job_absent(native['job_name'])
    origin.need(not ARCHIVE.exists(),'unused flat worker metadata archive required')
    sources={ROOT/name for name in pins['reviewed_files']}
    sources.update(RUN/name for name in ('pins.json','source-review.json','origin-contract.json','dispatch_001.json','dispatch_result_001.json'))
    sources.update(RUN.glob('preflight*.json'))
    sources.update((OUT/'qualification.json',OUT/'result.json',OUT/'junit.xml',OUT/'pytest.log',
        request_path,claim_path,attestation_path,intent_path,success_path))
    sources.update(fixture/name for name in configs)
    sources.update(path for path in Path(native['native_directory']).iterdir() if path.is_file())
    payloads=[]
    for path in sorted(sources):
        origin.need(path.is_relative_to(ROOT) and path.suffix.lower() not in {'.npz','.npy','.mat','.safetensors'},
            'archive excludes arrays, weights and ancestor packet copies')
        sha=digest(path);raw,pin=origin.asset(path,sha,8*1024**2,compact=True);payloads.append((path,raw,pin))
    verify_pins(pins,args.expect_pins,contract)
    ARCHIVE.mkdir();write_once(ARCHIVE/'.gitattributes',b'* -text\n')
    (ARCHIVE/'artifacts').mkdir();rows=[]
    for index,(path,raw,pin) in enumerate(payloads,1):
        target=f'artifacts/a{index:04d}{path.suffix}'
        write_once(ARCHIVE/target,raw);origin.asset(path,pin[-1],max(len(raw),1));origin.asset(ARCHIVE/target,pin[-1],max(len(raw),1))
        rows.append({'source':path.relative_to(ROOT).as_posix(),'path':target,'bytes':len(raw),'sha256':pin[-1]})
    summary={'schema':'cho51_linear_worker_route_summary_v3','passed':True,'closed_utc':datetime.now(timezone.utc).isoformat(),
        'pins_sha256':args.expect_pins,'origin_contract_file_sha256':pins['origin_contract_file_sha256'],
        'source_context_files':len(pins['files']),'runtime_files':5,'runtime_modules':18,'tests_passed':pins['expected_tests'],
        'native':native,'backend_calls':1,'verifier_calls':2,'engineering_successes':1,'measured_cells':0,
        'worker_route_engineering_qualified':True,'current_gradient_updates':0,'current_restore_count':0,
        'target_inference_calls':0,'current_source_updates':0,'current_support_updates':0,'historical_gradient_updates':5253,
        'prior_target_restore_count':1,'prior_target_support_updates':1,'prior_target_inference_calls':1,'prior_target_query_count':2,
        'scientific_admission':False,'unchanged_canonical_worker_verified':False,'full_worker_verified':False,
        'unchanged_single_root_factory_verified':False,'current_control_source':current,'historical_source':result['historical_source'],
        'target_metrics':result['target_metrics'],'request_sha256':result['request_sha256'],
        'claim_file_sha256':result['claim_file_sha256'],'attestation_file_sha256':result['attestation_file_sha256'],
        'qualification_file_sha256':digest(OUT/'qualification.json'),'verified_origin_files':len(stages['files']),
        'loaded_module_files':len(q['observed_loaded_module_hashes']),'physical_input_files_rechecked_after_job':213,
        'physical_input_bytes_rechecked_after_job':734579463,'original_case_attempts_remaining':0,'artifacts':len(rows)}
    write_once(ARCHIVE/'manifest.json',origin.canonical({'schema':'cho51_linear_worker_route_manifest_v3','artifacts':rows}))
    write_once(ARCHIVE/'summary.json',origin.canonical(summary))
    write_once(ARCHIVE/'README.md',b'# Linear worker route engineering integration\n\nOne metadata-only dispatch through the actual adopted route and locked recorder reuses accepted source, recorder and target proofs. Backend once, verifier twice; one engineering receipt and zero measured cells. No model, restore, support update, inference or array decoding was replayed. The historical synthetic predictions remain zero of two correct.\n')
    native_module.job_absent(native['job_name'])
    print(json.dumps({'passed':True,'archive':str(ARCHIVE),'artifacts':len(rows),
        'manifest_sha256':digest(ARCHIVE/'manifest.json'),'summary_sha256':digest(ARCHIVE/'summary.json'),
        'engineering_successes':1,'measured_cells':0}))


if __name__=='__main__':main()
