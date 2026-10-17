"""Stream-authenticate accepted source, target and metadata worker history."""
from __future__ import annotations
import hashlib
import importlib.util
import sys
from pathlib import Path
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
PREVIOUS=ROOT/'runs/coordination/cho51_linear_worker_route_20261017_v3'
PREVIOUS_PINS_SHA='11043e38b5dc02318b80d091017450aaf12df13a78c520560abe63f06a800327'
PREVIOUS_ORIGIN_SHA='5a02d17ab766f47c42f7dbd112ec8ddba2b0dc11a7c37bf7db882e10fbcea59e'
PREVIOUS_REVIEW_SHA='6dacd5667ba08f417322b62ed88de7152de9ecbfc1abac29fe963026667d7fa4'
PREVIOUS_FINAL_SHA='b015de93f153eb12adf2edc1a0a50a6c3fe1c2591e15300c16b242c2dc8f8043'
TARGET=ROOT/'runs/coordination/cho51_linear_target_route_20261017_v3'
FINAL_SHA='4e07f6d47c36b405ced3c24a714bbc9d332a6ed038fd128beca7d057828d2a03'
TARGET_PINS_SHA='759827205d2256e6c532bcb5cc056ec2683ad8d210dda4fce2b6b7e141fcb9e8'
CANONICAL='3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
CASE='9d3596b5e7653e1708eb208d6b150b86cae02227e6cd73a25e4358e675afc141'
WEIGHTS_SHA='3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048'
BASELINE_SHA='53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
EVIDENCE_SHA='e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3'
ARCHIVE=ROOT/'evidence/cho51-linear-worker-route-20261017-v3'
ARCHIVE_MANIFEST_SHA='669c9224a682d574d38397bbed341982393fa0b16de0b26efb97c01005077a48'
ARCHIVE_SUMMARY_SHA='d77a731235dc3443dfff30f1b435c035337ec150a67c52535043d5c64b9c9dd7'
EXPORT=ROOT/'evidence/cho51-linear-worker-closeout-export-20261017'
EXPORT_MANIFEST_SHA='a30ff62c7a3a8dc68201625cd447357c4726c25124fd0853b11f9da8d60ba251'
M=None


def predecessor():
    global M
    if M is None:
        path=PREVIOUS/'origin.py';raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=PREVIOUS_ORIGIN_SHA:raise ValueError('frozen accepted worker origin changed')
        spec=importlib.util.spec_from_file_location('_numerical_worker_historical_origin',path)
        M=importlib.util.module_from_spec(spec);sys.modules[spec.name]=M
        exec(compile(raw,str(path),'exec',dont_inherit=True),M.__dict__)
    return M


def prior():return predecessor().prior()
def __getattr__(name):return getattr(prior(),name)
def need(condition,message):return predecessor().need(condition,message)
def canonical(value):return predecessor().canonical(value)
def asset(path,expected,maximum,*,compact=False):return predecessor().asset(path,expected,maximum,compact=compact)
def document(path,expected=None):return predecessor().document(path,expected)
def original_inventory():return predecessor().original_inventory()
def verify_inputs():return predecessor().verify_inputs()


def verify_origin_stages(*,verify_physical_inputs=True):
    # Existing historical schemas/counters stay unchanged for W's historical
    # binding. The separately named accepted stage is appended as history only.
    base=predecessor().verify_origin_stages(verify_physical_inputs=verify_physical_inputs)
    pins=document(PREVIOUS/'pins.json',PREVIOUS_PINS_SHA)
    review=document(PREVIOUS/'source-review.json',PREVIOUS_REVIEW_SHA)
    final=document(PREVIOUS/'final-review.json',PREVIOUS_FINAL_SHA)
    need((PREVIOUS/'final-review.json').stat().st_size==1777139
        and final['passed'] is True and final['remaining_actionable_findings']==[]
        and final['metadata_only'] is True and final['engineering_successes']==1
        and final['measured_cells']==final['model_constructions']==final['current_gradient_updates']==0
        and len(pins['files'])==2458 and len(pins['runtime'])==5 and len(pins['runtime_modules'])==18
        and pins['expected_tests']==100 and review['files']==pins['reviewed_files']
        and review['remaining_actionable_findings']==[],'accepted metadata worker history differs')
    files=dict(base['files']);roles=dict(base['roles'])
    def include(path,sha):
        path=Path(path);path=path if path.is_absolute() else ROOT/path
        if path==ROOT/'.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif':
            need(path.stat().st_size==260 and sha=='0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3',
                'exact separate MNE resource required');asset(path,sha,260);return
        large=(sha==EVIDENCE_SHA and base['roles'].get(str(path))=='complete_evidence'
            and base['files'].get(str(path))==sha and path.stat().st_size==23087023)
        need(path.suffix.lower() not in {'.npz','.npy','.mat','.fif','.safetensors'},'new history stage is metadata only')
        asset(path,sha,32*1024**2 if large else 8*1024**2)
        need(str(path) not in files or files[str(path)]==sha,'accepted history pin conflict')
        files[str(path)]=sha;roles[str(path)]='complete_evidence' if large else 'metadata'
    for name,sha in pins['files'].items():include(name,sha)
    include(PREVIOUS/'final-review.json',PREVIOUS_FINAL_SHA)
    for name,sha in final['current_own_proofs'].items():include(name,sha)
    for name,sha in final['current_archive_proofs'].items():include(name,sha)
    manifest=document(ARCHIVE/'manifest.json',ARCHIVE_MANIFEST_SHA)
    summary=document(ARCHIVE/'summary.json',ARCHIVE_SUMMARY_SHA)
    need(len(manifest['artifacts'])==summary['artifacts']==35
        and sum(row['bytes'] for row in manifest['artifacts'])==1831889
        and {p.relative_to(ARCHIVE).as_posix() for p in ARCHIVE.rglob('*') if p.is_file()}
            =={'manifest.json','summary.json','README.md','.gitattributes',*[r['path'] for r in manifest['artifacts']]},
        'exact accepted35-pair archive inventory required')
    for row in manifest['artifacts']:
        a=ROOT/row['source'];b=ARCHIVE/row['path']
        need(a.stat().st_size==b.stat().st_size==row['bytes'],'accepted archive size differs')
        include(a,row['sha256']);include(b,row['sha256'])
    exported=document(EXPORT/'manifest.json',EXPORT_MANIFEST_SHA)
    need(exported['copied_artifact_count']==8 and len(exported['artifacts'])==8
        and exported['historical_review_sha256']==PREVIOUS_FINAL_SHA
        and exported['historical_review_bytes']==1777139
        and final['document_bindings']==final['documents'] and len(final['documents'])==7,
        'accepted exact8-copy documentation export required')
    expected={'manifest.json','README.md','.gitattributes'};documents={}
    include(EXPORT/'manifest.json',EXPORT_MANIFEST_SHA)
    for row in exported['artifacts']:
        copied=EXPORT/row['path'];expected.add(row['path'])
        need(copied.resolve(strict=True).is_relative_to(EXPORT) and copied.stat().st_size==row['bytes'],
            'historical documentation copy path/size differs')
        include(copied,row['sha256'])
        if row['document_binding_recorded_in_review']:
            documents[row['source']]=row['sha256']
    need(documents==final['documents'] and len(expected)==11
        and {p.relative_to(EXPORT).as_posix() for p in EXPORT.rglob('*') if p.is_file()}==expected,
        'historical document copies must match frozen review bindings')
    readme=exported['explanatory_readme']
    need(readme['path']=='README.md' and (EXPORT/'README.md').stat().st_size==readme['bytes'],
        'exact manifest-bound historical export README required')
    include(EXPORT/'README.md',readme['sha256'])
    include(EXPORT/'.gitattributes','705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da')
    need((EXPORT/'.gitattributes').read_bytes()==b'* -text\n','export byte-preservation attributes required')
    summary=dict(base['summary'],accepted_metadata_worker_v3={'final_review_sha256':PREVIOUS_FINAL_SHA,
        'pins_sha256':PREVIOUS_PINS_SHA,'source_review_sha256':PREVIOUS_REVIEW_SHA,
        'archive_pairs':35,'archive_payload_bytes':1831889,'export_copies':8,'export_inventory':11,
        'export_manifest_sha256':EXPORT_MANIFEST_SHA,'tests_passed':100,'engineering_successes':1,
        'current_restore_count':0,'current_gradient_updates':0,'measured_cells':0},
        native_names=[*base['summary']['native_names'],'20261017T092310Z_e65bc049c9'])
    return {'files':dict(sorted(files.items())),'roles':dict(sorted(roles.items())),'summary':summary}
