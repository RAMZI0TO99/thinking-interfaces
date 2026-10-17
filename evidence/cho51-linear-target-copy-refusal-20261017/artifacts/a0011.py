"""One fresh synthetic target-support/query route under the admitted native Job."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from runtime import ROOT,RUN,Runtime,digest,pause_check,read_json,write_json
import origin

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins',type=Path,required=True)
parser.add_argument('--expect-pins',required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
runtime=Runtime(args.pins,args.expect_pins,args.output)
torch=runtime.install_torch_guards()
import pytest
from core.config import config_digest,load_toml
from core.provenance import capture_source
from evaluation.phase2_runner import CasePlan
from evaluation.phase2_protocol import TrialCatalog,nested_episode,source_selection
from evaluation.phase2_profile_binding import CHO_CLASSES,ChoProfileAssets60Hz
from evaluation.phase2_records import envelope,verify_envelope
from docs.phase2.cho51_linear_target_route_v1.target_route import run_target_route


class Results:
    def __init__(self):self.items=0;self.calls=[];self.skipped=[]
    def pytest_collection_finish(self,session):self.items=len(session.items)
    def pytest_runtest_setup(self,item):pause_check()
    def pytest_runtest_logreport(self,report):
        if report.skipped:self.skipped.append({'nodeid':report.nodeid,'phase':report.when})
        if report.when=='call' or report.failed:
            self.calls.append({'nodeid':report.nodeid,'phase':report.when,'outcome':report.outcome})


OUT=args.output;pins=runtime.pins
reports=Results();os.chdir(OUT)
test_exit=pytest.main(['-q','-s','-p','no:cacheprovider','-o','addopts=',
    '--import-mode=importlib','--log-file',str(OUT/'pytest.log'),'--basetemp',str(OUT/'t'),
    '--junitxml',str(OUT/'junit.xml'),*[str(ROOT/node) for node in pins['test_nodes']]],plugins=[reports])
passed=(test_exit==0 and reports.items==pins['expected_tests'] and len(reports.calls)==pins['expected_tests']
        and not reports.skipped and all(r['phase']=='call' and r['outcome']=='passed' for r in reports.calls))
if runtime.numerical_calls:raise ValueError('metadata boundary tests performed numerical operations')
result={'schema':'cho51_linear_target_route_result_v1','passed':False,'tests_passed':passed,
    'pytest_exit':int(test_exit),'collected_tests':reports.items,'expected_tests':pins['expected_tests'],
    'reports':reports.calls,'skipped_reports':reports.skipped,'historical_gradient_updates':5253,
    'current_source_updates':0,'current_support_updates':0,'current_gradient_updates':0,'current_restore_count':0,
    'source_training_replayed':False,'source_work_reused':True,'measured_cells':0,
    'scientific_admission':False,'original_case_attempts_remaining':0,
    'unchanged_single_root_factory_verified':False,'unchanged_canonical_store_restore_verified':False}
restore_witness=None


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
    write_json(OUT/'restore-witness.json',restore_witness)
    return adapter


if passed:
    # Full213 before/after hashes use only streamed bytes; no source arrays are
    # decoded. The synthetic immutable identity authenticates metadata catalogs.
    input_before=origin.verify_inputs()
    fixture=runtime.fixture
    identity=origin.document(fixture/'synthetic-input-identity.json',
        '34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
    protocol=load_toml(fixture/'configs/phase2/protocol.toml')
    threshold=load_toml(fixture/'configs/benchmark.toml')['datasets']['cho2017']['artifact_threshold_volts']
    preprocessing=config_digest({'profile_identity':protocol['preparation']['profile_identity'],
        'threshold_config_sha256':identity['files']['configs/benchmark.toml']['sha256'],
        'dataset':'cho2017','threshold':threshold})
    ids=tuple(json.dumps(['synthetic_session','synthetic_run',i],separators=(',',':')) for i in range(42))
    labels=CHO_CLASSES*21;catalogs=[];assets={}
    for number in range(1,53):
        subject=f'subject_{number:02d}'
        a=f'data/processed/cho2017/profile_a/{subject}.npz'
        b=f'data/processed/cho2017/profile_b_60hz_v1/{subject}.npz'
        manifest=f'data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json'
        catalogs.append(TrialCatalog('cho2017',subject,ids,labels,CHO_CLASSES,identity['files'][a]['sha256'],preprocessing))
        assets[subject]=ChoProfileAssets60Hz(identity['files'][b]['sha256'],identity['files'][manifest]['sha256'],
            identity['files']['configs/phase2/cho_profile_b_60hz.toml']['sha256'])
    catalogs=tuple(catalogs);selection=source_selection(catalogs,target='subject_02')
    origin.need(selection.sha256==identity['source_selection_sha256'],'authenticated synthetic52catalog selection differs')
    target=next(c for c in catalogs if c.subject=='subject_02')
    episode=nested_episode(target,shots=(1,5,10,20),protocol_sha256=config_digest(protocol))
    current=asdict(capture_source(fixture))
    origin.need(current==pins['expected_current_context'],'actual new fixture Git context differs')
    plan=CasePlan('cho2017','subject_02','labram_linear',5,11,1)
    runtime.active=True
    try:
        witness=run_target_route(fixture_root=fixture,plan=plan,protocol_config=protocol,catalogs=catalogs,
            selection_record=envelope('source_selection',asdict(selection)),
            episode_record=envelope('episode_manifest',episode.payload()),assets=assets,
            current_context=current,expected_current_context=pins['expected_current_context'],
            historical_context={'git_commit':origin.HISTORICAL_COMMIT,'source_sha256':origin.SOURCE_CONTEXT,'git_dirty':True},
            expected_source_state_sha256=origin.MODEL_STATE,restore_adapter=restore_adapter)
    finally:runtime.active=False
    input_after=origin.verify_inputs()
    origin.need(input_before==input_after and asdict(capture_source(fixture))==current,
        'all213 input bytes or current source changed')
    write_json(OUT/'target-witness.json',witness)
    result.update(passed=True,target_route_witness=witness,restore_witness=restore_witness,
        input_audit_before=input_before,input_audit_after=input_after,current_control_source=current,
        historical_source={'git_commit':origin.HISTORICAL_COMMIT,'source_sha256':origin.SOURCE_CONTEXT,'git_dirty':True},
        recorder_control_source=runtime.contract['summary']['recorder_control_source'],
        current_restore_count=1,current_support_updates=1,current_gradient_updates=1,
        target_route_qualified=True,new_explicit_two_root_staged_restore_verified=True)
write_json(OUT/'result.json',result)
runtime.finish(result)
print(json.dumps({'passed':result['passed'],'engineering_only':True,'measured_cells':0,'scientific_admission':False}),flush=True)
raise SystemExit(0 if result['passed'] else 1)
