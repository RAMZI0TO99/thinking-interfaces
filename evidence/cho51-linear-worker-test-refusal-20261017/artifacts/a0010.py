"""Authenticate accepted history plus the frozen pre-test worker import refusal.

Only standard-library readers run here. The failed V1 sources, pins, native
receipt and partial output remain immutable; no used launcher is replayed.
"""
from __future__ import annotations
import hashlib
import importlib.util
import sys
from pathlib import Path
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
PREVIOUS=ROOT/'runs/coordination/cho51_linear_worker_route_20261017_v1'
PREVIOUS_PINS_SHA='a14287becc958cc9bcf189bc5603c251e123b8d61dfc64ccb2963bc21db25899'
PREVIOUS_ORIGIN_SHA='2225e1ba6f2304bf8d66423b8f7b5f00ccd91105cacb390615ba20b4b238bca2'
PREVIOUS_REVIEW_SHA='314c1711eaa6bad228ddc25b61a55773bcfa04c043f7fd22013ec24054143ab6'
FAILED_NATIVE=ROOT/'runs/migration/20261017T090027Z_9ce5db8d4b'
FAILED_RECEIPT_SHA='99e2a65c67c4712f98f7b8a11487f7c2d61ba221df3d9eda027c0bd54bffddf7'
FAILED_ARCHIVE=ROOT/'evidence/cho51-linear-worker-import-refusal-20261017'
FAILED_MANIFEST_SHA='c4de481081cf983c8f0389e5a898f34288329f4615c1cae6ff1b4905404314f0'
FAILED_SUMMARY_SHA='0f9c3a43ee4c3060a1aab6601baf1b6b37717cce6cc37a5203b67f8b8b922706'
TARGET=ROOT/'runs/coordination/cho51_linear_target_route_20261017_v3'
TARGET_PINS_SHA='759827205d2256e6c532bcb5cc056ec2683ad8d210dda4fce2b6b7e141fcb9e8'
FINAL_SHA='4e07f6d47c36b405ced3c24a714bbc9d332a6ed038fd128beca7d057828d2a03'
CANONICAL='3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
CASE='9d3596b5e7653e1708eb208d6b150b86cae02227e6cd73a25e4358e675afc141'
WEIGHTS_SHA='3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048'
BASELINE_SHA='53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8'
EVIDENCE_SHA='e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3'
M=None


def predecessor():
    global M
    if M is None:
        path=PREVIOUS/'origin.py';raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=PREVIOUS_ORIGIN_SHA:raise ValueError('frozen worker V1 origin source changed')
        spec=importlib.util.spec_from_file_location('_linear_worker_v2_historical_origin',path)
        M=importlib.util.module_from_spec(spec);sys.modules[spec.name]=M
        exec(compile(raw,str(path),'exec',dont_inherit=True),M.__dict__)
    return M


def prior():return predecessor().prior()
def need(condition,message):return predecessor().need(condition,message)
def canonical(value):return predecessor().canonical(value)
def asset(path,expected,maximum,*,compact=False):return predecessor().asset(path,expected,maximum,compact=compact)
def document(path,expected=None):return predecessor().document(path,expected)
def original_inventory():return predecessor().original_inventory()
def verify_inputs():return predecessor().verify_inputs()


def verify_origin_stages(*,verify_physical_inputs=True):
    base=predecessor().verify_origin_stages(verify_physical_inputs=verify_physical_inputs)
    pins=document(PREVIOUS/'pins.json',PREVIOUS_PINS_SHA)
    review=document(PREVIOUS/'source-review.json',PREVIOUS_REVIEW_SHA)
    need(pins['schema']=='cho51_linear_worker_route_pins_v1' and len(pins['files'])==2354
         and len(pins['runtime'])==5 and len(pins['runtime_modules'])==18 and pins['expected_tests']==96
         and review['source_only'] is True and review['remaining_actionable_findings']==[]
         and review['files']==pins['reviewed_files'],'exact frozen pre-test V1 pins and source review required')
    files=dict(base['files']);roles=dict(base['roles'])
    def include(path,sha):
        path=Path(path);path=path if path.is_absolute() else ROOT/path
        if path==ROOT/'.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif':
            need(sha=='0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'
                 and path.stat().st_size==260,'exact separate MNE runtime dependency required')
            asset(path,sha,260);return
        need(path.suffix.lower() not in {'.npz','.npy','.mat','.fif','.safetensors'},
             'V1 refusal metadata excludes arrays and weights')
        complete=(sha==EVIDENCE_SHA and path.stat().st_size==23087023
            and base['files'].get(str(path))==sha and base['roles'].get(str(path))=='complete_evidence')
        asset(path,sha,32*1024**2 if complete else 8*1024**2)
        need(str(path) not in files or files[str(path)]==sha,'frozen V1 proof hash conflict')
        files[str(path)]=sha;roles[str(path)]='complete_evidence' if complete else 'metadata'
    for name,sha in pins['files'].items():include(ROOT/name,sha)
    fixed={'pins.json':PREVIOUS_PINS_SHA,'source-review.json':PREVIOUS_REVIEW_SHA,
        'origin-contract.json':'d6254cb14084105f67645242c48ebd05ae1ffb19673696e364404144225b6639',
        'dispatch_001.json':'5601d73ff502ce3c5058d35360e811c2d57b10061bf2243cad55885ddecb934b',
        'dispatch_result_001.json':'2246b1af33b946619181587e7a1ac7edd9b01bbb36083df662c937ad454ed80f',
        'preflight_001.json':'c70b0bfe834c297b96cde0a7d9cbd9ddd3b3f8356bcb579dd4325d1a66d14597'}
    for name,sha in fixed.items():include(PREVIOUS/name,sha)
    native_files={'admission.json':'cb4e231ca132abcb234b4004056d680df89acf0a72aea1650419cac7f736155b',
        'command-result.json':'64a1526b099d75eed9d9da41a5562dcc164b6ffddeb729dd371c4496bbcded05',
        'command.log':'6ad47c4b3ecdc7b471596a5053c293c977e424cafec593ca456a33be8ca5e9f6',
        'deadline.json':'fe4768f726cc4071ad75d9b7422c6168a3b7c31ce11782534147e3157a8977fe',
        'receipt.json':FAILED_RECEIPT_SHA}
    need({p.name for p in FAILED_NATIVE.iterdir() if p.is_file()}==set(native_files),'exact frozen V1 native file inventory required')
    for name,sha in native_files.items():include(FAILED_NATIVE/name,sha)
    native=document(FAILED_NATIVE/'receipt.json',FAILED_RECEIPT_SHA)
    need(native['accepted'] is False and native['job_absent'] is True
         and native['job_name']=='pro3_migration_'+FAILED_NATIVE.name
         and native['result']['reason']=='normal' and native['result']['exit_code']==1
         and native['native_state']['cleanup_errors']==[] and native['native_state']['peak_sampling_errors']==[]
         and all(native['native_state'][name] is True for name in ('job_closed','job_empty_before_close',
             'process_handle_closed','thread_handle_closed','root_exit_after_job_close')),
         'frozen refused V1 native closure boundary changed')
    output=PREVIOUS/'validation_001'
    need({p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}=={'mpl/fontlist-v3.11.0.json'}
         and not(output/'result.json').exists() and not(output/'qualification.json').exists()
         and not(output/'junit.xml').exists() and not(output/'cases').exists() and not(output/'fixture').exists(),
         'V1 must remain a pre-test/pre-claim import refusal with no result or qualification')
    font=output/'mpl/fontlist-v3.11.0.json'
    include(font,'711fe51fd583dc3469082cefb4eaa1e4743a2e9346abc8d627f6d2cb9fcb02b4')
    manifest=document(FAILED_ARCHIVE/'manifest.json',FAILED_MANIFEST_SHA)
    packet_summary=document(FAILED_ARCHIVE/'summary.json',FAILED_SUMMARY_SHA)
    need(len(manifest['artifacts'])==packet_summary['artifacts']==22 and packet_summary['payload_bytes']==1253392
         and packet_summary['tests_executed']==packet_summary['claims_created']==0
         and packet_summary['native_receipt_sha256']==FAILED_RECEIPT_SHA
         and packet_summary['source_review_sha256']==PREVIOUS_REVIEW_SHA
         and packet_summary['source_files']==pins['reviewed_files'],
         'exact22-pair frozen worker import-refusal packet required')
    include(FAILED_ARCHIVE/'manifest.json',FAILED_MANIFEST_SHA)
    include(FAILED_ARCHIVE/'summary.json',FAILED_SUMMARY_SHA)
    include(FAILED_ARCHIVE/'README.md','e1dd35801f98329b8449a97d008f53d17a0f63c7e74df94e7a89c9615fccfd51')
    include(FAILED_ARCHIVE/'.gitattributes','705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da')
    expected_names={'manifest.json','summary.json','README.md','.gitattributes'}
    for row in manifest['artifacts']:
        source=ROOT/row['source'];copied=FAILED_ARCHIVE/row['path']
        need(source.resolve(strict=True).is_relative_to(ROOT) and copied.resolve(strict=True).is_relative_to(FAILED_ARCHIVE)
             and source.stat().st_size==copied.stat().st_size==row['bytes'],'refusal source/archive pair path or size changed')
        include(source,row['sha256']);include(copied,row['sha256']);expected_names.add(row['path'])
    need(sum(row['bytes'] for row in manifest['artifacts'])==1253392
         and len(expected_names)==26
         and {p.relative_to(FAILED_ARCHIVE).as_posix() for p in FAILED_ARCHIVE.rglob('*') if p.is_file()}==expected_names,
         'exact26-file refusal packet inventory required')
    summary=dict(base['summary'],preserved_failed_worker_v1={'pins_sha256':PREVIOUS_PINS_SHA,
        'source_review_sha256':PREVIOUS_REVIEW_SHA,'native_directory':str(FAILED_NATIVE),
        'native_receipt_sha256':FAILED_RECEIPT_SHA,'accepted':False,'tests_started':False,'claims_created':False,
        'worker_route_qualified':False,'support_updates':0,'selected_restore_count':0,'query_inference_calls':0,
        'measured_cells':0,'archive_manifest_sha256':FAILED_MANIFEST_SHA,'archive_summary_sha256':FAILED_SUMMARY_SHA,
        'archive_pairs':22,'failure':'guarded torch.tensor during full-target import before metadata tests'},
        native_names=[*base['summary']['native_names'],FAILED_NATIVE.name])
    return {'files':dict(sorted(files.items())),'roles':dict(sorted(roles.items())),'summary':summary}
