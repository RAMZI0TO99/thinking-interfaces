"""One locked engineering worker with fresh restore, support and query execution."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import stat
import sys
from dataclasses import asdict,fields
from pathlib import Path
from types import MappingProxyType
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runtime import CANONICAL,ROOT,RUN,Runtime,digest,identity,pause_check,read_json,write_json
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins',type=Path,required=True);parser.add_argument('--expect-pins',required=True)
parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
runtime=Runtime(args.pins,args.expect_pins,args.output)
torch=runtime.install_torch_guards()
from evaluation.phase2_runner import CasePlan,CaseRecorder,environment_digest
from core.provenance import capture_source
from core.config import config_digest,canonical_config_json,load_toml
from evaluation.phase2_protocol import TrialCatalog,source_selection,nested_episode
from evaluation.phase2_profile_binding import CHO_CLASSES,ChoProfileAssets60Hz
from evaluation.phase2_records import envelope,verify_envelope
from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import from_verified_full_route,route_summary
from docs.phase2.cho51_linear_numerical_worker_v1.numerical_worker import (W,run_worker_case,verify_current_execution,build_current_binding,EXPECTED_BUDGET)
WorkerContext=W.WorkerContext
TARGET=W.TARGET
import origin
import pytest
OUT=args.output;pins=runtime.pins
class Results:
    def __init__(self):
        self.items, self.calls, self.skipped = 0, [], []
    def pytest_collection_finish(self, session):
        self.items = len(session.items)
    def pytest_runtest_setup(self, item):
        pause_check()
    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.skipped.append({'nodeid': report.nodeid, 'phase': report.when})
        if report.when == 'call' or report.failed:
            self.calls.append({'nodeid': report.nodeid, 'phase': report.when, 'outcome': report.outcome})


reports=Results();os.chdir(OUT)
pytest_exit=pytest.main(['-q','-s','--maxfail=1','-p','no:cacheprovider','-o','addopts=','--import-mode=importlib',
    '--log-file',str(OUT/'pytest.log'),'--basetemp',str(OUT/'t'),'--junitxml',str(OUT/'junit.xml'),
    *[str(ROOT/node) for node in pins['test_nodes']]],plugins=[reports])
tests_passed=(pytest_exit==0 and reports.items==pins['expected_tests'] and len(reports.calls)==pins['expected_tests']
    and not reports.skipped and all(r['phase']=='call' and r['outcome']=='passed' for r in reports.calls))
CONTRACT=RUN/'origin-contract.json';CONTRACT_SHA=pins['origin_contract_file_sha256']
expected_origin=read_json(CONTRACT);contract_identity=identity(CONTRACT)
callback_counts={'backend_calls':0,'verifier_calls':0}

def verify_origin(request):
    runtime.verify_pins();pause_check()
    historical=request.historical_binding
    if (historical.origin_contract_path!=CONTRACT or historical.origin_contract_file_sha256!=CONTRACT_SHA
            or identity(CONTRACT)!=contract_identity or digest(CONTRACT)!=CONTRACT_SHA):
        raise ValueError('exact fresh independent origin contract required')
    current=origin.verify_origin_stages()
    if dict(schema='cho51_linear_worker_origin_contract_v1',**current)!=expected_origin:
        raise ValueError('locked independent source/recorder/target proof differs from pinned origin')
    runtime.verify_pins();pause_check();return current


restore_witness=None
execution_workspace=None


def numerical_snapshot():
    return json.dumps({'calls':runtime.numerical_calls,'restore':runtime.current_restore_count,
        'model':runtime.model_constructions,'dummy':runtime.constructor_dummy_forward_calls,
        'classifier':runtime.classifier_forward_calls,'backbone':runtime.backbone_forward_calls,
        'numpy':runtime.numpy_loads,'clones':runtime.clone_reinitializations,
        'containers':runtime.empty_mask_containers},sort_keys=True,allow_nan=False)


def backend(request,request_path,request_sha256):
    global execution_workspace
    callback_counts['backend_calls']+=1
    if (callback_counts['backend_calls']!=1 or request_path!=request.workspace/'request.json'
            or request_sha256!=request.sha256 or digest(request_path)!=request_sha256):
        raise ValueError('one fresh numerical backend request required')
    verify_origin(request);input_before=origin.verify_inputs()
    execution_workspace=request.workspace
    runtime.worker_binding=build_current_binding(request)
    runtime.worker_claim_identity=identity(request.historical_binding.claim_path)
    runtime.worker_request_identity=identity(request_path)
    _,source_fixture,_=origin.original_inventory()
    full=route._full_route
    import json as json_module
    protocol=load_toml(request.fixture_root/'configs/phase2/protocol.toml')
    inputs=full.inputs_for(request.plan)
    if numerical_snapshot()!=zero_numerical_snapshot:raise ValueError('numerics preceded locked backend')
    from docs.phase2.cho51_linear_target_route_v1.target_route import run_target_route
    if numerical_snapshot()!=zero_numerical_snapshot:raise ValueError('model activity occurred during target import')
    runtime.active=True
    try:
        witness=run_target_route(fixture_root=source_fixture,plan=request.plan,protocol_config=protocol,
            catalogs=full.catalogs,selection_record=inputs.selection_record,
            episode_record=inputs.episode_record,assets=inputs.assets,
            current_context=pins['expected_current_context'],expected_current_context=pins['expected_current_context'],
            historical_context=expected_origin['summary']['historical_source'],
            expected_source_state_sha256=origin.MODEL_STATE,restore_adapter=restore_adapter)
    finally:runtime.active=False
    witness['current_worker_binding']=runtime.worker_binding
    W.L._write_json_once(execution_workspace/'target-witness.json',witness)
    input_after=origin.verify_inputs()
    if input_before!=input_after:raise ValueError('original213 inputs changed during worker execution')
    ledger={'source_updates':0,'restore_count':runtime.current_restore_count,
        'support_updates':runtime.numerical_calls.get('sgd_step',0),
        'gradient_updates':runtime.numerical_calls.get('tensor_backward',0),
        'target_inference_calls':witness['witnesses']['calls']['runner_prediction'],
        'query_count':witness['query_count'],'model_constructions':runtime.model_constructions,'measured_cells':0}
    if ledger!=EXPECTED_BUDGET:raise ValueError('actual current numerical ledger differs from request budget')
    outputs={name:{'sha256':digest(execution_workspace/name),'bytes':(execution_workspace/name).stat().st_size}
        for name in ('restore-witness.json','target-witness.json')}
    payload={'schema':'cho51_linear_numerical_execution_v1',**runtime.worker_binding,
        'source_fixture':str(source_fixture),'current_control_source':pins['expected_current_context'],
        'historical_source':expected_origin['summary']['historical_source'],
        'expected_numerical_budget':EXPECTED_BUDGET,'current_counter_ledger':ledger,
        'restore_witness':restore_witness,'target_route_witness':witness,
        'observed_numerical_calls':dict(runtime.numerical_calls),
        'input_audit_before':input_before,'input_audit_after':input_after,'physical_outputs':outputs,
        'native_closeout_status':'pending_external_post_job','engineering_only':True,
        'measured_cells':0,'scientific_admission':False}
    return W.L._write_json_once(execution_workspace/'current-execution.json',envelope('engineering_smoke',payload))


def verifier(request,opaque):
    callback_counts['verifier_calls']+=1
    if callback_counts['verifier_calls']>2 or runtime.active:raise ValueError('exact2 metadata-only verifiers required')
    before=numerical_snapshot();verify_origin(request)
    proof=verify_current_execution(request,opaque)
    if numerical_snapshot()!=before:raise ValueError('independent verifier performed fresh numerical operations')
    return proof

def build_route(fixture):
    previous,source_fixture,_=origin.original_inventory()
    identity=origin.document(source_fixture/'synthetic-input-identity.json',
        '34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
    protocol=load_toml(fixture/'configs/phase2/protocol.toml')
    threshold=load_toml(fixture/'configs/benchmark.toml')['datasets']['cho2017']['artifact_threshold_volts']
    preprocessing=config_digest({'profile_identity':protocol['preparation']['profile_identity'],
        'threshold_config_sha256':identity['files']['configs/benchmark.toml']['sha256'],
        'dataset':'cho2017','threshold':threshold})
    ids=tuple(json.dumps(['synthetic_session','synthetic_run',i],separators=(',',':')) for i in range(42))
    catalogs=[];assets={};selections={};episodes={}
    for number in range(1,53):
        subject=f'subject_{number:02d}'
        a=f'data/processed/cho2017/profile_a/{subject}.npz'
        b=f'data/processed/cho2017/profile_b_60hz_v1/{subject}.npz'
        manifest=f'data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json'
        catalogs.append(TrialCatalog('cho2017',subject,ids,CHO_CLASSES*21,CHO_CLASSES,identity['files'][a]['sha256'],preprocessing))
        assets[subject]=ChoProfileAssets60Hz(identity['files'][b]['sha256'],identity['files'][manifest]['sha256'],
            identity['files']['configs/phase2/cho_profile_b_60hz.toml']['sha256'])
    catalogs=tuple(catalogs)
    for catalog in catalogs:
        selection=source_selection(catalogs,target=catalog.subject)
        episode=nested_episode(catalog,shots=(1,5,10,20),protocol_sha256=config_digest(protocol))
        selections[catalog.subject]=canonical_config_json(envelope('source_selection',asdict(selection)))
        episodes[catalog.subject]=canonical_config_json(envelope('episode_manifest',episode.payload()))
        if catalog.subject=='subject_02' and selection.sha256!=identity['source_selection_sha256']:
            raise ValueError('independently reconstructed synthetic selection identity differs')
    plans=tuple(CasePlan('cho2017',f'subject_{s:02d}',m,5,k,1) for s in range(1,53)
        for m in ('labram_linear','labram_lora','labram_full','eegnet') for k in (11,23,37,53,71))
    full=ChoFirstTrancheRoute(plans,catalogs,MappingProxyType(assets),canonical_config_json(protocol),
        MappingProxyType(selections),MappingProxyType(episodes))
    return from_verified_full_route(ROOT,full)
def copy_config(relative, fixture):
    source = ROOT / relative
    expected_sha = pins['files'][relative]
    before = source.stat()
    if (source.resolve(strict=True) != source or source.is_symlink() or not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1 or not 0 < before.st_size <= 1048576):
        raise ValueError('direct bounded pinned canonical configuration required')
    with source.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(1048577)
        finished = os.fstat(stream.fileno())
    after = source.stat()
    key = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if (key(before) != key(after) or key(opened) != key(finished) or key(before)[:4] != key(opened)[:4]
            or len(raw) != before.st_size or hashlib.sha256(raw).hexdigest() != expected_sha):
        raise ValueError('canonical configuration changed during bounded byte copy')
    destination = fixture / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if digest(source) != expected_sha or digest(destination) != expected_sha:
        raise ValueError('fresh configuration copy differs from pinned source bytes')


def restore_adapter():
    """New two-root restoration; no historical Git recapture or store patching.

    Canonical SelectedSourceStore.restore requires liveGit==historical4491 and
    remains unqualified here. This explicitly versioned loader derives the real
    architecture through canonical _new_model, verifies the accepted complete
    record and selected tensor bytes, and returns the genuine target adapter.
    """
    global restore_witness
    if restore_witness is not None or runtime.current_restore_count:
        raise ValueError('once-only fresh selected-source restoration required')
    from safetensors.torch import load
    from evaluation.labram_parity import state_digest
    from evaluation.phase2_cho_source_restore import prepare_cho_source_restore,_new_model,_check_labram_baseline
    from evaluation.phase2_pilot import LaBraMTunedAdapter
    raw_origin=origin.document(origin.PUBLICATION/'origin-contract.json',
        '8bffd0d8be4f8ed2b87189ec0f36462303b88c627b1a8115c7651805a8a5c20b')
    method=origin.document(Path(raw_origin['method_config_path']),raw_origin['method_config_file_sha256'])
    record_raw,evidence_pin=origin.asset(Path(raw_origin['selection_evidence_path']),origin.EVIDENCE_SHA,
        32*1024**2,compact=True)
    record=json.loads(record_raw);payload=record['payload'];contract=payload['contract'];final_fit=payload['final_source_fit']
    historical={'git_commit':origin.HISTORICAL_COMMIT,'source_sha256':origin.SOURCE_CONTEXT,'git_dirty':True}
    origin.need(record_raw==origin.canonical(record) and verify_envelope(record,kind='engineering_smoke',expected_payload=payload)
        and record['sha256']==raw_origin['selection_evidence_sha256']
        and payload['complete'] is True and payload['outer_target_predictions_performed'] is False
        and payload['selected_candidate']=='lr_1e-3' and len(payload['folds'])==102
        and len(final_fit['steps'])==51 and contract['source']==historical
        and config_digest(contract)==raw_origin['contract_sha256'], 'authenticated complete historical selection differs')
    prepared=prepare_cho_source_restore(root=ROOT,plan=plan,method_config=method,
        expected_method_config_sha256=raw_origin['method_config_sha256'],selected_candidate='lr_1e-3')
    origin.need(config_digest(prepared.model_recipe)==raw_origin['model_recipe_sha256']
        == 'bdb40fd0f3becf87cc619e87a536ee4a921e72efa422fcaaf235c3573865a452'
        and asdict(prepared.support_settings)=={'method':'linear','steps':1,'learning_rate':0.001,
            'partial_depth':None,'query_batch_size':8},'canonical architecture or selected support settings differ')
    import platform
    import numpy as np
    from importlib.metadata import version
    recorded_runtime=contract['runtime']
    fresh_dependencies={'torch':str(torch.__version__),'numpy':np.__version__,'braindecode':version('braindecode')}
    origin.need(set(recorded_runtime)=={'python','torch','numpy','braindecode','device','dtype',
        'torch_threads','deterministic_algorithms'} and recorded_runtime['device']=='cpu'
        and recorded_runtime['dtype']=='float32' and type(recorded_runtime['torch_threads']) is int
        and recorded_runtime['torch_threads']>=1 and type(recorded_runtime['deterministic_algorithms']) is bool
        and sys.version==pins['runtime_transition']['current_python_version']
        and all(recorded_runtime[k]==v for k,v in fresh_dependencies.items()),
        'historical runtime schema or unchanged numerical dependencies differ')
    model=_new_model(prepared,contract=contract,final_fit=final_fit)
    backbone_before=state_digest(model.backbone)
    _check_labram_baseline(prepared)
    selected_raw,weight_pin=origin.asset(runtime.selected,origin.WEIGHTS_SHA,64*1024**2,compact=True)
    origin.need(len(selected_raw)==23294624,'exact selected full-safe weights size required')
    tensors=load(selected_raw);expected=model.state_dict()
    origin.need(set(tensors)==set(expected) and len(tensors)==223
        and sum(t.numel() for t in tensors.values())==5818138
        and all(t.device.type=='cpu' and t.dtype==torch.float32 and t.shape==expected[name].shape
            and torch.isfinite(t).all().item() for name,t in tensors.items()),'selected tensor schema/finite state differs')
    model.load_state_dict(tensors,strict=True)
    origin.need(state_digest(model)==origin.MODEL_STATE and state_digest(model.backbone)==backbone_before
        and len(model.backbone.blocks)==12 and int(model.backbone.embed_dim)==200
        and tuple(n for n,p in model.named_parameters() if p.requires_grad)==('head.weight','head.bias')
        and sum(p.numel() for p in model.parameters() if p.requires_grad)==402
        and not any(m.training for m in model.modules()) and all(p.grad is None for p in model.parameters()),
        'restored full source/mask/backbone differs')
    origin.asset(runtime.selected,origin.WEIGHTS_SHA,64*1024**2)
    origin.need(origin.asset(runtime.selected,origin.WEIGHTS_SHA,64*1024**2)[1]==weight_pin,
        'selected file physical identity changed during restoration')
    adapter=LaBraMTunedAdapter('labram_linear',model,prepared.support_settings)
    origin.need(type(adapter) is LaBraMTunedAdapter and adapter._model is model,'real canonical adapter required')
    runtime.current_restore_count=1
    restore_witness={'schema':'cho51_linear_target_staged_restore_v1','passed':True,
        'current_restore_count':1,'baseline_decodes':1,'selected_decodes':1,'strict_state_loads':2,
        'weights_file_sha256':origin.WEIGHTS_SHA,'weights_bytes':23294624,'weights_limit_bytes':64*1024**2,
        'selected_state_sha256':origin.MODEL_STATE,'tensor_count':223,'elements':5818138,'head_parameters':402,
        'model_recipe_sha256':config_digest(prepared.model_recipe),'source_backbone_unchanged':True,
        'historical_source':historical,'current_control_source':pins['expected_current_context'],
        'adapter_class':type(adapter).__module__+'.'+type(adapter).__qualname__,
        'historical_python_version':recorded_runtime['python'],'current_python_version':platform.python_version(),
        'numerical_dependency_versions':fresh_dependencies,'runtime_transition_sha256':pins['runtime_transition_sha256'],
        'new_explicit_two_root_staged_restore_verified':True,'unchanged_canonical_store_restore_verified':False,
        'unchanged_single_root_factory_verified':False,'complete_evidence_reused':True,
        'complete_evidence_file_sha256':origin.EVIDENCE_SHA,'complete_evidence_sha256':record['sha256'],
        'scientific_admission':False,'measured_cells':0}
    restore_witness['current_worker_binding']=runtime.worker_binding
    W.L._write_json_once(execution_workspace/'restore-witness.json',restore_witness)
    return adapter


zero_numerical_snapshot=numerical_snapshot()
result={'schema':'cho51_linear_numerical_worker_result_v1','passed':False,'tests_passed':tests_passed,
    'metadata_isolation':TARGET.metadata_isolation,
    'pytest_exit':int(pytest_exit),'collected_tests':reports.items,'expected_tests':pins['expected_tests'],
    'executed_test_calls':sum(row['phase']=='call' for row in reports.calls),'pytest_maxfail':1,
    'reports':reports.calls,'skipped_reports':reports.skipped,'backend_calls':0,'verifier_calls':0,
    'source_work_reused':True,'restore_work_reused':False,'prior_target_work_reused':True,
    'source_training_replayed':False,'current_gradient_updates':0,'current_source_updates':0,'current_support_updates':0,
    'current_restore_count':0,'current_target_inference_calls':0,'target_inference_calls':0,'historical_gradient_updates':5253,
    'prior_target_restore_count':1,'prior_target_support_updates':1,'prior_target_inference_calls':1,'prior_target_query_count':2,
    'measured_cells':0,'scientific_admission':False,'original_case_attempts_remaining':0,
    'unchanged_canonical_worker_verified':False,'full_worker_verified':False,'unchanged_single_root_factory_verified':False}
if tests_passed:
    runtime.verify_pins();input_before=origin.verify_inputs()
    fixture=OUT/'fixture';fixture.mkdir(exist_ok=False)
    configs=('configs/base.toml','configs/benchmark.toml','configs/phase2/protocol.toml',
        'configs/phase2/selection_ceiling.toml','configs/phase2/cho_profile_b_60hz.toml')
    for name in configs:copy_config(name,fixture)
    if {p.relative_to(fixture).as_posix() for p in fixture.rglob('*') if p.is_file()}!=set(configs):
        raise ValueError('five-config-only control fixture required')
    route=build_route(fixture)
    recorder_root=fixture/'runs/phase2/lifecycle';recorder=CaseRecorder(fixture,output_root=recorder_root)
    source=capture_source(fixture)
    if asdict(source)!=pins['expected_current_context']:raise ValueError('actual fresh fixture source differs')
    context=WorkerContext(OUT,fixture,recorder_root,args.pins,args.expect_pins,CANONICAL,
        pins['owner_decision_sha256'],route.plans,source,environment_digest())
    plan=CasePlan('cho2017','subject_02','labram_linear',5,11,1)
    (OUT/'cases').mkdir()
    completion=run_worker_case(recorder,plan,context=context,route=route,workspace=OUT/'cases'/plan.case_id,
        origin_contract_path=CONTRACT,origin_contract_file_sha256=CONTRACT_SHA,backend=backend,verifier=verifier)
    if callback_counts!={'backend_calls':1,'verifier_calls':2}:raise ValueError('backend1/verifier2 required')
    input_after=origin.verify_inputs()
    if input_before!=input_after or capture_source(fixture)!=source:raise ValueError('inputs or current context changed')
    proof={k:str(v) if isinstance(v,Path) else v for k,v in asdict(completion.proof).items()}
    request=completion.request.historical_binding
    execution=read_json(completion.request.workspace/'current-execution.json')['payload']
    result.update(passed=True,worker_route_engineering_qualified=True,fresh_numerical_worker_engineering_qualified=True,
        current_gradient_updates=1,current_support_updates=1,current_restore_count=1,
        current_target_inference_calls=1,target_inference_calls=1,query_count=2,
        current_counter_ledger=execution['current_counter_ledger'],current_execution=execution,
        current_execution_path=str(completion.request.workspace/'current-execution.json'),
        current_execution_file_sha256=digest(completion.request.workspace/'current-execution.json'),
        native_closeout_status='pending_external_post_job',engineering_completion=recorder.completion((plan,)),
        request_path=str(completion.request_path),request_sha256=completion.request.sha256,
        claim_path=str(request.claim_path),claim_file_sha256=request.claim_file_sha256,
        attestation_path=str(completion.attestation_path),attestation_file_sha256=completion.attestation_file_sha256,
        engineering_receipt=str(completion.engineering_receipt),engineering_receipt_file_sha256=digest(completion.engineering_receipt),
        proof=proof,origin_contract_file_sha256=CONTRACT_SHA,origin_compact_files=len(expected_origin['files']),
        fixture_source=asdict(source),historical_source=expected_origin['summary']['historical_source'],
        recorder_control_source=expected_origin['summary']['recorder_control_source'],
        target_control_source=origin.document(origin.TARGET/'final-review.json',origin.FINAL_SHA)['current_control_source'],
        historical_case_id=expected_origin['summary']['historical_case_id'],current_case_id=plan.case_id,
        worker_route_summary=route_summary(route),historical_target_metrics=expected_origin['summary']['target_metrics'],
        current_target_metrics=json.loads(completion.proof.metrics_json),
        input_audit_before=input_before,input_audit_after=input_after,**callback_counts)
write_json(OUT/'result.json',result);runtime.finish(result)
print(json.dumps({'passed':result['passed'],'engineering_only':True,'measured_cells':0,'scientific_admission':False}),flush=True)
raise SystemExit(0 if result['passed'] else 1)
