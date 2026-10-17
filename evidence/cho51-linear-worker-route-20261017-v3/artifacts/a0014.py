"""Prepare exact reviewed metadata worker pins; no numerical imports or launch."""
from __future__ import annotations
import ast
import hashlib
import os
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
CANDIDATE=ROOT/'docs/phase2/cho51_linear_worker_route_v3'
sys.path.insert(0,str(RUN))
import origin


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def write_once(path,value):
    with Path(path).open('xb') as stream:
        stream.write(origin.canonical(value));stream.flush();os.fsync(stream.fileno())


def main():
    if any((RUN/name).exists() for name in ('pins.json','origin-contract.json','validation_001')):
        raise ValueError('unused worker contracts/output required')
    candidates={CANDIDATE/name for name in ('worker_route.py','test_worker_route.py','README.md')}
    if set(CANDIDATE.iterdir())!=candidates:raise ValueError('exact3candidate sources required')
    operations={RUN/name for name in ('runtime.py','parent.py','prepare.py','origin.py','observe.py','launch.ps1','closeout.py')}
    paths=candidates|operations
    for path in paths:
        if path.suffix=='.py':ast.parse(path.read_bytes(),filename=str(path))
    reviewed={path.relative_to(ROOT).as_posix():digest(path) for path in sorted(paths)}
    review_path=RUN/'source-review.json';review=origin.document(review_path)
    if (len(reviewed)!=10 or review.get('source_only') is not True
            or review.get('remaining_actionable_findings')!=[] or review.get('files')!=reviewed):
        raise ValueError('exact independent settled10-source review required')
    nodes=[];count=0;test=CANDIDATE/'test_worker_route.py'
    for node in ast.parse(test.read_bytes()).body:
        if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
            cases=1
            for mark in node.decorator_list:
                if isinstance(mark,ast.Call) and isinstance(mark.func,ast.Attribute) and mark.func.attr=='parametrize':
                    if len(mark.args)<2 or not isinstance(mark.args[1],(ast.List,ast.Tuple)):
                        raise ValueError('literal parameterized test inventory required')
                    cases*=len(mark.args[1].elts)
            nodes.append(test.relative_to(ROOT).as_posix()+'::'+node.name);count+=cases
    if not 10<=count<=100:raise ValueError('reviewed10..100 boundary cases required')
    verified=origin.verify_origin_stages()
    prior=origin.document(origin.PREVIOUS/'pins.json',origin.PREVIOUS_PINS_SHA)
    contract=dict(schema='cho51_linear_worker_origin_contract_v1',**verified)
    contract_sha=hashlib.sha256(origin.canonical(contract)).hexdigest()
    files=dict(prior['files']);files.update(reviewed)
    files[(origin.PREVIOUS/'pins.json').relative_to(ROOT).as_posix()]=origin.PREVIOUS_PINS_SHA
    files[review_path.relative_to(ROOT).as_posix()]=digest(review_path)
    files[(RUN/'origin-contract.json').relative_to(ROOT).as_posix()]=contract_sha
    for name,sha in verified['files'].items():
        path=Path(name)
        if verified['roles'][name]=='metadata' and path.is_relative_to(ROOT):files[path.relative_to(ROOT).as_posix()]=sha
    for group in ('runtime','runtime_modules'):
        for name,sha in prior[group].items():
            if digest(name)!=sha:raise ValueError('fresh target5/18 runtime changed: '+name)
    head=subprocess.run(['git','--no-optional-locks','rev-parse','--verify','HEAD'],cwd=ROOT,
        capture_output=True,text=True,check=True).stdout.strip()
    dirty=bool(subprocess.run(['git','--no-optional-locks','status','--porcelain','--untracked-files=all'],
        cwd=ROOT,capture_output=True,text=True,check=True).stdout)
    actual={'git_commit':head,'git_dirty':dirty,'source_sha256':origin.prior().SOURCE_CONTEXT}
    pins={'schema':'cho51_linear_worker_route_pins_v3','prepared_utc':datetime.now(timezone.utc).isoformat(),
        'files':files,'runtime':prior['runtime'],'runtime_modules':prior['runtime_modules'],
        'historical_runtime':prior['historical_runtime'],'runtime_transition_sha256':prior['runtime_transition_sha256'],
        'baseline':prior['baseline'],'selected_weights':prior['selected_weights'],'canonical_files':432,
        'canonical_source_sha256':origin.CANONICAL,'predecessor_files':2402,'predecessor_pins_sha256':origin.PREVIOUS_PINS_SHA,'operational_version':3,
        'source_review_path':str(review_path),'source_review_sha256':digest(review_path),'reviewed_files':reviewed,
        'origin_contract_file_sha256':contract_sha,'owner_decision_sha256':prior['owner_decision_sha256'],
        'mne_resource_path':prior['mne_resource_path'],'mne_resource_sha256':prior['mne_resource_sha256'],
        'seconds':600,'process_mib':4096,'job_mib':5120,'startup_ram_gib':10,'active_ram_gib':4,'disk_gib':20,
        'threads':1,'gpu_hidden':True,'source_training_replayed':False,'current_source_updates':0,
        'current_support_updates':0,'current_gradient_updates':0,'current_restore_count':0,'target_inference_calls':0,
        'historical_gradient_updates':5253,'historical_target_restore_count':1,'historical_target_support_updates':1,
        'historical_target_inference_calls':1,'historical_target_query_count':2,'expected_current_context':actual,
        'test_nodes':nodes,'expected_tests':count,'scientific_admission':False,'original_case_attempts_remaining':0}
    if origin.verify_origin_stages()!=verified:raise ValueError('origin changed during fresh pin preparation')
    write_once(RUN/'origin-contract.json',contract);write_once(RUN/'pins.json',pins)
    print({'source_context_files':len(files),'runtime_files':5,'runtime_modules':18,'expected_tests':count,
        'pins_sha256':digest(RUN/'pins.json'),'origin_contract_file_sha256':contract_sha,'origin_files':len(verified['files']),
        'launched':False})


if __name__=='__main__':main()
