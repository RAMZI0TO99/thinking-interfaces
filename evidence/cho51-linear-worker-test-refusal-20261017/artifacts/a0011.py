"""One metadata-only adopted worker dispatch with locked reused target evidence."""
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
runtime=Runtime('parent',args.pins,args.expect_pins,args.output)
runtime.install_torch_guards()
from evaluation.phase2_runner import CasePlan,CaseRecorder,environment_digest
from core.provenance import capture_source
from core.config import config_digest,canonical_config_json,load_toml
from evaluation.phase2_protocol import TrialCatalog,source_selection,nested_episode
from evaluation.phase2_profile_binding import CHO_CLASSES,ChoProfileAssets60Hz
from evaluation.phase2_records import envelope
from evaluation.phase2_cho_case_inputs import ChoFirstTrancheRoute
from docs.phase2.cho51_worker_bridge_v1.worker_bridge import from_verified_full_route,route_summary
from docs.phase2.cho51_linear_worker_route_v2.worker_route import TARGET,WorkerContext,VerifiedWorkerProof,run_worker_case
import origin
import pytest
OUT=args.output;pins=runtime.pins
original_recorder=CaseRecorder.__init__
def isolated_recorder(self,root,*,output_root=None):
    if not Path(root).resolve().is_relative_to(OUT) or output_root is None or not Path(output_root).resolve().is_relative_to(OUT):
        runtime.refuse('shared_recorder_constructor',root)
    original_recorder(self,root,output_root=output_root)
CaseRecorder.__init__=isolated_recorder
def forbid_record_cell(*a,**k):runtime.refuse('scientific_record_cell',None)
CaseRecorder.record_cell=forbid_record_cell
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
pytest_exit=pytest.main(['-q','-s','-p','no:cacheprovider','-o','addopts=','--import-mode=importlib',
    '--log-file',str(OUT/'pytest.log'),'--basetemp',str(OUT/'t'),'--junitxml',str(OUT/'junit.xml'),
    *[str(ROOT/node) for node in pins['test_nodes']]],plugins=[reports])
tests_passed=(pytest_exit==0 and reports.items==pins['expected_tests'] and len(reports.calls)==pins['expected_tests']
    and not reports.skipped and all(r['phase']=='call' and r['outcome']=='passed' for r in reports.calls))
CONTRACT=RUN/'origin-contract.json';CONTRACT_SHA=pins['origin_contract_file_sha256']
expected_origin=read_json(CONTRACT);contract_identity=identity(CONTRACT)
callback_counts={'backend_calls':0,'verifier_calls':0}

def verify_origin(request):
    runtime.verify_pins();pause_check()
    if (request.origin_contract_path!=CONTRACT or request.origin_contract_file_sha256!=CONTRACT_SHA
            or identity(CONTRACT)!=contract_identity or digest(CONTRACT)!=CONTRACT_SHA):
        raise ValueError('exact fresh independent origin contract required')
    current=origin.verify_origin_stages()
    if dict(schema='cho51_linear_worker_origin_contract_v1',**current)!=expected_origin:
        raise ValueError('locked independent source/recorder/target proof differs from pinned origin')
    runtime.verify_pins();pause_check();return current

def backend(request,request_path,request_sha256):
    callback_counts['backend_calls']+=1
    if (callback_counts['backend_calls']!=1 or request_path!=request.workspace/'request.json'
            or request_sha256!=request.sha256 or digest(request_path)!=request_sha256):
        raise ValueError('one fresh worker backend request required')
    return verify_origin(request)

def verifier(request,opaque):
    callback_counts['verifier_calls']+=1
    if callback_counts['verifier_calls']>2:raise ValueError('exactly2 locked worker proof checks required')
    current=verify_origin(request)
    if opaque!=current:raise ValueError('backend proof differs from independent verification')
    summary=current['summary']
    kwargs={f.name:getattr(request,f.name) for f in fields(VerifiedWorkerProof) if hasattr(request,f.name)}
    for f in fields(VerifiedWorkerProof):
        if f.name in summary:kwargs[f.name]=summary[f.name]
    kwargs.update(request_sha256=request.sha256,case_id=request.plan.case_id,
        verified_origin_files=len(current['files']),origin_contract_file_sha256=CONTRACT_SHA)
    return VerifiedWorkerProof(**kwargs)

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


result={'schema':'cho51_linear_worker_route_result_v2','passed':False,'tests_passed':tests_passed,
    'metadata_isolation':TARGET.metadata_isolation,
    'pytest_exit':int(pytest_exit),'collected_tests':reports.items,'expected_tests':pins['expected_tests'],
    'reports':reports.calls,'skipped_reports':reports.skipped,'backend_calls':0,'verifier_calls':0,
    'source_work_reused':True,'restore_work_reused':True,'prior_target_work_reused':True,
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
    result.update(passed=True,worker_route_engineering_qualified=True,engineering_completion=recorder.completion((plan,)),
        request_path=str(completion.request_path),request_sha256=completion.request.sha256,
        claim_path=str(completion.request.claim_path),claim_file_sha256=completion.request.claim_file_sha256,
        attestation_path=str(completion.attestation_path),attestation_file_sha256=completion.attestation_file_sha256,
        engineering_receipt=str(completion.engineering_receipt),engineering_receipt_file_sha256=digest(completion.engineering_receipt),
        proof=proof,origin_contract_file_sha256=CONTRACT_SHA,origin_compact_files=len(expected_origin['files']),
        fixture_source=asdict(source),historical_source=expected_origin['summary']['historical_source'],
        recorder_control_source=expected_origin['summary']['recorder_control_source'],
        target_control_source=origin.document(origin.TARGET/'final-review.json',origin.FINAL_SHA)['current_control_source'],
        historical_case_id=expected_origin['summary']['historical_case_id'],current_case_id=plan.case_id,
        worker_route_summary=route_summary(route),target_metrics=expected_origin['summary']['target_metrics'],
        input_audit_before=input_before,input_audit_after=input_after,**callback_counts)
write_json(OUT/'result.json',result);runtime.finish(result)
print(json.dumps({'passed':result['passed'],'engineering_only':True,'measured_cells':0,'scientific_admission':False}),flush=True)
raise SystemExit(0 if result['passed'] else 1)
