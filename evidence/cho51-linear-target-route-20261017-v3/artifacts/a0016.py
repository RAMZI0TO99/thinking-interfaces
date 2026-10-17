"""Prepare reviewed target-route pins using only standard-library metadata."""
from __future__ import annotations
import ast
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
CANDIDATE = ROOT / 'docs/phase2/cho51_linear_target_route_v1'
sys.path.insert(0, str(RUN))
import origin


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_once(path, value):
    with Path(path).open('xb') as stream:
        stream.write(origin.canonical(value)); stream.flush(); os.fsync(stream.fileno())


def main():
    if any((RUN / name).exists() for name in ('pins.json','origin-contract.json','validation_001')):
        raise ValueError('unused target-route contracts/output required')
    names = ('target_route.py','test_target_route.py','README.md')
    candidates = {CANDIDATE / name for name in names}
    if set(CANDIDATE.iterdir()) != candidates:
        raise ValueError('exact three-file target-route candidate required')
    operations = {RUN / name for name in ('runtime.py','parent.py','prepare.py','origin.py',
        'observe.py','launch.ps1','closeout.py')}
    paths = candidates | operations
    for path in paths:
        if path.suffix == '.py': ast.parse(path.read_bytes(), filename=str(path))
    reviewed = {path.relative_to(ROOT).as_posix():digest(path) for path in sorted(paths)}
    review_path = RUN / 'source-review.json'
    review = origin.document(review_path)
    if (review.get('source_only') is not True or review.get('remaining_actionable_findings') != []
            or review.get('files') != reviewed):
        raise ValueError('independent exact ten-source settled review required')
    nodes, count = [], 0
    for node in ast.parse((CANDIDATE / 'test_target_route.py').read_bytes()).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            cases = 1
            for mark in node.decorator_list:
                if isinstance(mark,ast.Call) and isinstance(mark.func,ast.Attribute) and mark.func.attr=='parametrize':
                    if len(mark.args)<2 or not isinstance(mark.args[1],(ast.List,ast.Tuple)):
                        raise ValueError('literal test parameter inventory required')
                    cases *= len(mark.args[1].elts)
            nodes.append((CANDIDATE/'test_target_route.py').relative_to(ROOT).as_posix()+'::'+node.name)
            count += cases
    if not 10 <= count <= 100: raise ValueError('focused10..100 metadata tests required')
    verified = origin.verify_origin_stages()
    predecessor = origin.document(origin.RECORDER/'pins.json',origin.PINS_SHA)
    failed_pins = origin.document(origin.FAILED_V2/'pins.json',origin.FAILED_V2_PINS_SHA)
    contract = dict(schema='cho51_linear_target_route_origin_v3',**verified)
    contract_sha = hashlib.sha256(origin.canonical(contract)).hexdigest()
    files = dict(failed_pins['files'])
    files[(origin.FAILED_V2/'pins.json').relative_to(ROOT).as_posix()] = origin.FAILED_V2_PINS_SHA
    files.update(reviewed)
    files[review_path.relative_to(ROOT).as_posix()] = digest(review_path)
    files[(RUN/'origin-contract.json').relative_to(ROOT).as_posix()] = contract_sha
    files[(RUN/'runtime-transition.json').relative_to(ROOT).as_posix()] = origin.TRANSITION_SHA
    for path,sha in verified['files'].items():
        if verified['roles'][path]=='metadata' and Path(path).is_relative_to(ROOT):
            files[Path(path).relative_to(ROOT).as_posix()] = sha
    for path,sha in origin.CLONE_SOURCES.items():
        if Path(path).is_relative_to(ROOT):files[Path(path).relative_to(ROOT).as_posix()]=sha
    # Runtime packages may have changed since15October. Pin today's actual five
    # executables/DLLs separately; never rewrite the recorded historical hashes.
    runtime = {path:digest(path) for path in predecessor['runtime']}
    transition = origin.document(origin.TRANSITION,origin.TRANSITION_SHA)
    historical_q=origin.document(origin.RECORDER/'validation_001/qualification.json',
        '2a8394630cf700b600d757d1af3523769d0300b8f529a2fc60ecebaef64e4b18')
    old_union=dict(historical_q['observed_loaded_module_hashes']);old_union.update(predecessor['runtime'])
    runtime_modules={}
    expected_names={'DLLs/'+name+'.pyd' for name in ('_asyncio','_bz2','_ctypes','_decimal','_elementtree',
        '_hashlib','_lzma','_multiprocessing','_overlapped','_queue','_socket','_ssl','_uuid','_wmi','_zoneinfo',
        'pyexpat','select','unicodedata')}|{'python.exe','python3.dll','python312.dll'}
    if ({row['relative_runtime_path'] for row in transition['changed_files']}!=expected_names
            or len(transition['changed_files'])!=21):raise ValueError('exact21 observed runtime replacements required')
    for row in transition['changed_files']:
        path=Path(row['path'])
        if (not path.is_relative_to(Path(transition['runtime_base']))
                or old_union.get(str(path))!=row['historical_sha256']
                or path.stat().st_size!=row['current_bytes'] or digest(path)!=row['current_sha256']):
            raise ValueError('independent runtime transition bytes/history differ')
        if path.suffix=='.pyd':runtime_modules[str(path)]=row['current_sha256']
    actual = subprocess.run(['git','--no-optional-locks','rev-parse','--verify','HEAD'],
        cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    if actual != origin.CURRENT_COMMIT: raise ValueError('expected current actual Git HEAD differs')
    pins = {'schema':'cho51_linear_target_route_pins_v3','prepared_utc':datetime.now(timezone.utc).isoformat(),
        'files':files,'runtime':runtime,'historical_runtime':predecessor['runtime'],
        'supporting_runtime_sources':origin.CLONE_SOURCES,
        'runtime_modules':runtime_modules,'runtime_transition':transition,
        'runtime_transition_sha256':origin.TRANSITION_SHA,'baseline':predecessor['baseline'],
        'selected_weights':predecessor['selected_weights'],
        'canonical_files':432,'canonical_source_sha256':origin.CANONICAL,
        'predecessor_files':2230,'predecessor_pins_sha256':origin.FAILED_V2_PINS_SHA,
        'operational_version':3,'full_model_constructions':1,'parameterless_clone_reinitializations':4,
        'empty_mask_containers':2,
        'source_review_path':str(review_path),'source_review_sha256':digest(review_path),
        'reviewed_files':reviewed,'origin_contract_file_sha256':contract_sha,
        'owner_decision_sha256':predecessor['owner_decision_sha256'],
        'mne_resource_path':predecessor['mne_resource_path'],'mne_resource_sha256':predecessor['mne_resource_sha256'],
        'seconds':600,'process_mib':4096,'job_mib':5120,'startup_ram_gib':10,'active_ram_gib':4,'disk_gib':20,
        'threads':1,'gpu_hidden':True,'source_training_replayed':False,
        'current_source_updates':0,'current_support_updates':1,'current_gradient_updates':1,
        'historical_gradient_updates':5253,'expected_current_context':verified['summary']['expected_current_context'],
        'test_nodes':nodes,'expected_tests':count,'scientific_admission':False,'original_case_attempts_remaining':0}
    write_once(RUN/'runtime-transition.json',transition)
    write_once(RUN/'origin-contract.json',contract)
    write_once(RUN/'pins.json',pins)
    print(json.dumps({'source_context_files':len(files),'runtime_files':len(runtime),
        'runtime_transition_files':21,'expected_tests':count,'pins_sha256':digest(RUN/'pins.json'),
        'origin_contract_file_sha256':contract_sha,'origin_files':len(verified['files']),'launched':False}))


if __name__=='__main__': main()
