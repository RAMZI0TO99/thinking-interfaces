"""Read-only byte authentication of accepted source, recorder and target stages.

This module uses only the standard library. Historical runtime hashes remain
historical; current runtime binaries are pinned separately by prepare.py.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import math
import sys
import tomllib
from pathlib import Path

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
TARGET=ROOT/'runs/coordination/cho51_linear_target_route_20261017_v3'
TARGET_ORIGIN_SHA='812f9e68fad693d611e7c0e84e1fcdb746db953d472e6d895e765490cc541cbb'
TARGET_PINS_SHA='759827205d2256e6c532bcb5cc056ec2683ad8d210dda4fce2b6b7e141fcb9e8'
FINAL_SHA='4e07f6d47c36b405ced3c24a714bbc9d332a6ed038fd128beca7d057828d2a03'
EXPORT=ROOT/'evidence/cho51-linear-target-closeout-export-20261017'
EXPORT_SHA='5434b3b2a05efbf8a4253545a8dd2762868699b0367abbb107547839c6aa3186'
CANONICAL='3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
CASE='9d3596b5e7653e1708eb208d6b150b86cae02227e6cd73a25e4358e675afc141'
WEIGHTS_SHA='3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048'
BASELINE_SHA='53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
EVIDENCE_SHA='e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3'
MODEL_STATE='8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01'
ADAPTED_STATE='5bd88f2afb0a2e667e3576bb82c037e3314cce0e8cfb4383ee7439fee57787dd'
M=None


def prior():
    global M
    if M is None:
        path=TARGET/'origin.py'
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=TARGET_ORIGIN_SHA:raise ValueError('frozen target origin changed')
        spec=importlib.util.spec_from_file_location('_linear_worker_target_origin',path)
        M=importlib.util.module_from_spec(spec);sys.modules[spec.name]=M
        exec(compile(raw,str(path),'exec',dont_inherit=True),M.__dict__)
    return M


def need(value,message):
    if not value:raise ValueError(message)


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')


def asset(path,expected,maximum,*,compact=False):
    return prior().asset(path,expected,maximum,compact=compact)


def document(path,expected=None):
    return prior().document(path,expected)


def verify_inputs():
    return prior().verify_inputs()


def original_inventory():
    return prior().original_inventory()


def target_metrics(witness):
    """Recompute the preserved two-query scores with plain Python only."""
    logits=witness['query_logits'];targets=witness['query_targets']
    need(type(logits) is list and len(logits)==2 and targets==[0,1], 'fixed two-query logits/labels required')
    for row in logits:
        need(type(row) is list and len(row)==2 and all(type(x) in (int,float) and math.isfinite(x) for x in row),
             'finite two-class query logit rows required')
    predictions=[max(range(2),key=lambda k:row[k]) for row in logits]
    confusion=[[sum(t==i and p==j for t,p in zip(targets,predictions)) for j in range(2)] for i in range(2)]
    correct=sum(t==p for t,p in zip(targets,predictions))
    need(predictions==[1,0] and confusion==[[0,1],[1,0]] and correct==0
         and witness['confusion_matrix']==confusion and witness['balanced_accuracy']==[0,1],
         'preserved unsuccessful synthetic predictions changed')
    return {'query_logits':logits,'query_targets':targets,'query_predictions':predictions,
        'query_count':2,'correct_query_predictions':correct,'confusion_matrix':confusion,
        'balanced_accuracy':[0,1],'scientific_predictive_performance_qualified':False}


def route_metadata(witness,pins):
    """Independently derive the full typed route's digest from pinned metadata."""
    _,fixture,_=original_inventory()
    identity=document(fixture/'synthetic-input-identity.json',
        '34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c')
    raw,_=asset(ROOT/'configs/phase2/protocol.toml',pins['files']['configs/phase2/protocol.toml'],1024**2,compact=True)
    protocol=tomllib.loads(raw.decode('utf-8'))
    raw,_=asset(ROOT/'configs/benchmark.toml',pins['files']['configs/benchmark.toml'],1024**2,compact=True)
    benchmark=tomllib.loads(raw.decode('utf-8'))
    cfg_hash=lambda value:hashlib.sha256(canonical(value).rstrip(b'\n')).hexdigest()
    preprocessing=cfg_hash({'profile_identity':protocol['preparation']['profile_identity'],
        'threshold_config_sha256':identity['files']['configs/benchmark.toml']['sha256'],
        'dataset':'cho2017','threshold':benchmark['datasets']['cho2017']['artifact_threshold_volts']})
    ids=[json.dumps(['synthetic_session','synthetic_run',i],separators=(',',':')) for i in range(42)]
    subjects=[f'subject_{i:02d}' for i in range(1,53)]
    classes=['left_hand','right_hand'];catalogs=[];assets={}
    for subject in subjects:
        a=f'data/processed/cho2017/profile_a/{subject}.npz'
        b=f'data/processed/cho2017/profile_b_60hz_v1/{subject}.npz'
        manifest=f'data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json'
        catalogs.append(dict(dataset='cho2017',subject=subject,trial_ids=ids,labels=classes*21,
            classes=classes,artifact_sha256=identity['files'][a]['sha256'],preprocessing_sha256=preprocessing))
        assets[subject]=dict(profile_b_artifact_sha256=identity['files'][b]['sha256'],
            profile_b_manifest_sha256=identity['files'][manifest]['sha256'],
            variant_config_sha256=identity['files']['configs/phase2/cho_profile_b_60hz.toml']['sha256'])
    plans=[dict(dataset='cho2017',target_subject=subject,method=method,shots_per_class=5,model_seed=seed,repetition=1)
        for subject in subjects for method in ('labram_linear','labram_lora','labram_full','eegnet')
        for seed in (11,23,37,53,71)]
    proposal_path=ROOT/'evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json'
    proposal=document(proposal_path,'26edbf77961af89fdc31941cbf0425c97ebd81ed263dff706a21aac933e9b965')
    method_configs={}
    for row in proposal['proposed_case_rows']:
        expected=method_configs.setdefault(row['method'],row['method_config_sha256'])
        need(expected==row['method_config_sha256'],'adopted method config differs within roster')
    need(set(method_configs)=={'labram_linear','labram_lora','labram_full','eegnet'},'exact adopted four method templates required')
    payload=dict(plans=plans,adopted_case_ids=[cfg_hash(p) for p in plans if p['target_subject']!='subject_01'],
        owner_decision_sha256=pins['owner_decision_sha256'],catalogs=catalogs,assets=assets,
        protocol_config=protocol,target_contract=witness['contract'],method_config_sha256=method_configs)
    return assets,cfg_hash(payload)


def verify_origin_stages(*,verify_physical_inputs=True):
    m=prior();base=m.verify_origin_stages(verify_physical_inputs=verify_physical_inputs)
    final=document(TARGET/'final-review.json',FINAL_SHA)
    need(final['passed'] is True and final['remaining_actionable_findings']==[]
         and final['target_route_qualified'] is True and final['tests_passed_once_in_accepted_v3']==68
         and final['current_restore_count']==final['current_support_updates']==final['target_inference_calls']==1
         and final['current_source_updates']==final['measured_cells']==0
         and final['scientific_admission'] is False and final['correct_query_predictions']==0,
         'exact accepted target engineering audit required')
    pins=document(TARGET/'pins.json',TARGET_PINS_SHA)
    need(len(pins['files'])==2280 and len(pins['runtime'])==5 and len(pins['runtime_modules'])==18,
         'accepted2280/5/18 target pins required')
    files=dict(base['files']);roles=dict(base['roles'])
    # This exact package resource is a runtime dependency, not an origin proof.
    # The transaction's frozen role reader intentionally rejects all FIF files.
    mne=ROOT/'.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif'
    mne_sha='0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'
    need(mne.stat().st_size==260,'exact260-byte MNE metadata resource required')
    asset(mne,mne_sha,260)
    files.pop(str(mne),None);roles.pop(str(mne),None)
    def include(path,sha):
        path=Path(path);path=path if path.is_absolute() else ROOT/path
        size=path.stat().st_size
        if path==mne:
            need(sha==mne_sha and size==260,'exact MNE dependency pin changed')
            asset(path,sha,260)
            return
        role=('complete_evidence' if sha==EVIDENCE_SHA and size==23087023 else
              'selected_weights' if sha==WEIGHTS_SHA and size==23294624 else
              'baseline_weights' if sha==BASELINE_SHA and size==23299672 else 'metadata')
        need(path.suffix.lower() not in {'.npz','.npy','.mat','.fif'},'arrays excluded from worker origin')
        need(path.suffix.lower()!='.safetensors' or role!='metadata','unknown checkpoint refused')
        maximum={'metadata':8*1024**2,'complete_evidence':32*1024**2,
                 'selected_weights':64*1024**2,'baseline_weights':64*1024**2}[role]
        asset(path,sha,maximum)
        need(str(path) not in files or files[str(path)]==sha,'origin proof hash conflict')
        files[str(path)]=sha;roles[str(path)]=role
    for group in ('checked_compact_proofs','large_complete_evidence_proofs','current_own_proofs',
                  'current_archive_proofs','preserved_v1_own_proofs','preserved_v1_archive_proofs',
                  'preserved_v2_own_proofs','preserved_v2_archive_proofs'):
        for path,sha in final[group].items():include(path,sha)
    for path,sha in pins['files'].items():include(path,sha)
    for path,sha in final['origin_files'].items():include(path,sha)
    include(TARGET/'pins.json',TARGET_PINS_SHA);include(TARGET/'final-review.json',FINAL_SHA)
    export=document(EXPORT/'manifest.json',EXPORT_SHA)
    need(export['historical_review_sha256']==FINAL_SHA and len(export['artifacts'])==8
         and export['copied_payload_bytes']==2918001,'exact target review plus7snapshot export required')
    include(EXPORT/'manifest.json',EXPORT_SHA)
    for row in export['artifacts']:
        path=EXPORT/row['path']
        need(path.resolve(strict=True).is_relative_to(EXPORT) and path.stat().st_size==row['bytes'],
             'target snapshot location/size changed')
        include(path,row['sha256'])
        if row['document_binding_recorded_in_review']:
            need(final['document_bindings'][row['source']]==row['sha256'],'historical snapshot binding changed')
    need({p.relative_to(EXPORT).as_posix() for p in EXPORT.rglob('*') if p.is_file()}==set(export['exact_inventory']),
         'exact11 target export inventory required')
    result_path=TARGET/'validation_001/result.json';witness_path=TARGET/'validation_001/target-witness.json'
    qualification_path=TARGET/'validation_001/qualification.json'
    native_path=Path(final['native_directory'])/'receipt.json'
    proof_paths={'target_witness_file_sha256':str(witness_path),'target_result_file_sha256':str(result_path),
        'target_qualification_file_sha256':str(qualification_path),'target_native_receipt_file_sha256':str(native_path),
        'target_final_review_file_sha256':str(TARGET/'final-review.json')}
    proof_shas={key:files[path] for key,path in proof_paths.items()}
    result=document(result_path,proof_shas['target_result_file_sha256'])
    witness=document(witness_path,proof_shas['target_witness_file_sha256'])
    qualification=document(qualification_path,proof_shas['target_qualification_file_sha256'])
    native=document(native_path,proof_shas['target_native_receipt_file_sha256'])
    need(result['passed'] is True and result['target_route_witness']==witness
         and qualification['passed'] is True and qualification['result']==result
         and native['accepted'] is True and native['job_absent'] is True
         and native['result']['exit_code']==0 and native['native_state']['cleanup_errors']==[]
         and witness['accepted'] is True and witness['contract']['case_id']==CASE
         and witness['source_state_sha256']==MODEL_STATE and final['adapted_state_sha256']==ADAPTED_STATE,
         'accepted target result/witness/native linkage changed')
    metrics=target_metrics(witness)
    assets,route_sha=route_metadata(witness,pins)
    for key in ('query_logits','query_predictions','query_targets','confusion_matrix','balanced_accuracy','correct_query_predictions'):
        need(final[key]==metrics[key],'target review query metrics changed')
    summary=dict(base['summary'],**proof_shas,
        target_contract=witness['contract'],target_contract_sha256=hashlib.sha256(canonical(witness['contract']).rstrip(b'\n')).hexdigest(),
        target_profile_binding_sha256=witness['profile_binding_sha256'],target_source_state_sha256=MODEL_STATE,
        target_adapted_state_sha256=ADAPTED_STATE,target_metrics=metrics,
        target_metrics_sha256=hashlib.sha256(canonical(metrics).rstrip(b'\n')).hexdigest(),target_proof_paths=proof_paths,
        target_profile_binding=witness['profile_binding'],target_assets=assets,worker_route_sha256=route_sha,
        target_work_reused=True,historical_target_restore_count=1,historical_target_support_updates=1,
        historical_target_inference_calls=1,historical_target_query_count=2,
        target_route_qualified=True,target_export_manifest_sha256=EXPORT_SHA,
        accepted_target_pins_sha256=TARGET_PINS_SHA,native_names=final['all_29_scoped_native_job_names_freshly_absent'])
    summary.update(historical_source_updates=5151,historical_support_updates=102,
        current_source_updates=0,current_support_updates=0,current_gradient_updates=0,current_restore_count=0,
        current_target_inference_calls=0,prior_target_support_updates=1,prior_target_restore_count=1,
        prior_target_inference_calls=1,prior_target_query_count=2,prior_target_work_reused=True,
        prior_target_route_qualified=True,unchanged_canonical_worker_verified=False,full_worker_verified=False,
        excluded_exact_runtime_metadata_dependency={'path':str(mne),'sha256':mne_sha,'bytes':260,
            'role_bound_origin_file':False,'fresh_dependency_pin_retained':True})
    return {'files':dict(sorted(files.items())),'roles':dict(sorted(roles.items())),'summary':summary}
