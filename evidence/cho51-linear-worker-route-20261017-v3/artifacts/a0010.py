"""Authenticate immutable history and the frozen metadata-test worker refusal."""
from __future__ import annotations
import hashlib
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
PREVIOUS=ROOT/'runs/coordination/cho51_linear_worker_route_20261017_v2'
PREVIOUS_PINS_SHA='38fb83fd3bb8ccb355305ee371bdd0c7eba0d99c9993cddc69243d6eef6d1f5a'
PREVIOUS_ORIGIN_SHA='4433dbd5a9bd9a11a916e00179834c60058aa9bb85bfc25828eb3097b4730474'
PREVIOUS_REVIEW_SHA='46077f27f52ea8eb70ce1e86b8ac38db259b1df69f78ec3e397f8542bca8bc92'
FAILED_NATIVE=ROOT/'runs/migration/20261017T091013Z_1c624adbe4'
FAILED_RECEIPT_SHA='b6464a60166e694a854b237b7ca774a72c09c73a2f409a65cf521f8c542449e9'
FAILED_ARCHIVE=ROOT/'evidence/cho51-linear-worker-test-refusal-20261017'
FAILED_MANIFEST_SHA='cb73d7fc2371109a32ce431ea068e8f84cd95574f6a990d599c49c094ea91799'
FAILED_SUMMARY_SHA='ab7d6d5dad3cec4cf7dd6ff29af36d3ffde8d025e5685bfb1065d3f44af0ddb9'
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
        if hashlib.sha256(raw).hexdigest()!=PREVIOUS_ORIGIN_SHA:raise ValueError('frozen worker V2 origin source changed')
        spec=importlib.util.spec_from_file_location('_linear_worker_v3_historical_origin',path)
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
    need(pins['schema']=='cho51_linear_worker_route_pins_v2' and pins['operational_version']==2
         and len(pins['files'])==2402 and len(pins['runtime'])==5 and len(pins['runtime_modules'])==18
         and pins['expected_tests']==99 and review['source_only'] is True
         and review['remaining_actionable_findings']==[] and review['files']==pins['reviewed_files'],
         'exact frozen99-case V2 pins and source review required')
    files=dict(base['files']);roles=dict(base['roles'])
    def include(path,sha):
        path=Path(path);path=path if path.is_absolute() else ROOT/path
        if path==ROOT/'.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif':
            need(sha=='0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'
                 and path.stat().st_size==260,'exact separate MNE runtime dependency required')
            asset(path,sha,260);return
        need(path.suffix.lower() not in {'.npz','.npy','.mat','.fif','.safetensors'},
             'V2 refusal origin excludes arrays and fabricated weights')
        complete=(sha==EVIDENCE_SHA and path.stat().st_size==23087023
            and base['files'].get(str(path))==sha and base['roles'].get(str(path))=='complete_evidence')
        asset(path,sha,32*1024**2 if complete else 8*1024**2)
        need(str(path) not in files or files[str(path)]==sha,'frozen V2 proof hash conflict')
        files[str(path)]=sha;roles[str(path)]='complete_evidence' if complete else 'metadata'
    for name,sha in pins['files'].items():include(ROOT/name,sha)
    fixed={'pins.json':PREVIOUS_PINS_SHA,'source-review.json':PREVIOUS_REVIEW_SHA,
        'origin-contract.json':'1ad5f878b34d1ae160f909496ce777492ea4cdfd68b763ac0f93cd6e596a2c9c',
        'dispatch_001.json':'fe47278549dfd1db4fa4611ef52ed41e1948e47237c33a5af532af8d781060ad',
        'dispatch_result_001.json':'5dcf233c72b949705f021be5739678f9ee3efc80eeb9e073343c036371aef07c',
        'preflight_001.json':'452b16f338eb325d6bec386cbf32bd378e917041c36083338b9ab0102c58130a'}
    for name,sha in fixed.items():include(PREVIOUS/name,sha)
    outputs={'result.json':'cdcbf0ddb11a06d2c39c1745b675b6ed673794ebee7448f87bcf7e9a2dd3a168',
        'qualification.json':'6582fb29e526c32362bf8257880b1a4b501789b40b3be2dca2328be9c30387fa',
        'junit.xml':'a36db065f92db01b9bf760056ab6a41eef259835c2fa5807000ef79fa4758b34',
        'pytest.log':'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
    output=PREVIOUS/'validation_001'
    for name,sha in outputs.items():include(output/name,sha)
    native_files={'admission.json':'4311391e34bbb53214d198fbe263371c0a1658904fa12abd7a87802c92b8eb19',
        'command-result.json':'64a1526b099d75eed9d9da41a5562dcc164b6ffddeb729dd371c4496bbcded05',
        'command.log':'1add9c0efde8b9486becac2e69d52a0b61215191a1312f7e7588a07ce1a4826c',
        'deadline.json':'b0926620abd797957c1495d6f84af421b551f7691c9b5a0ca8a0e5fa6130a4de',
        'receipt.json':FAILED_RECEIPT_SHA}
    need({p.name for p in FAILED_NATIVE.iterdir() if p.is_file()}==set(native_files),'exact frozen V2 native file inventory required')
    for name,sha in native_files.items():include(FAILED_NATIVE/name,sha)
    native=document(FAILED_NATIVE/'receipt.json',FAILED_RECEIPT_SHA)
    need(native['accepted'] is False and native['job_absent'] is True
         and native['job_name']=='pro3_migration_'+FAILED_NATIVE.name
         and native['result']['reason']=='normal' and native['result']['exit_code']==1
         and native['native_state']['cleanup_errors']==[] and native['native_state']['peak_sampling_errors']==[]
         and all(native['native_state'][name] is True for name in ('job_closed','job_empty_before_close',
             'process_handle_closed','thread_handle_closed','root_exit_after_job_close')),
         'frozen failed V2 native closure boundary changed')
    result=document(output/'result.json',outputs['result.json'])
    qualification=document(output/'qualification.json',outputs['qualification.json'])
    need(result['passed'] is False and result['tests_passed'] is False and result['pytest_exit']==1
         and result['collected_tests']==result['expected_tests']==99 and result['skipped_reports']==[]
         and result['backend_calls']==result['verifier_calls']==0
         and qualification['passed'] is False and qualification['result']==result
         and qualification['pins_sha256']==PREVIOUS_PINS_SHA
         and qualification['source_review_sha256']==PREVIOUS_REVIEW_SHA
         and qualification['observed_numerical_calls']=={} and qualification['denied_operations']==[]
         and qualification['forbidden_numerical_model_chain_imports']==[]
         and qualification['unexpected_denials']==0,'exact completed failed V2 metadata test result required')
    for name in ('current_gradient_updates','current_source_updates','current_support_updates','current_restore_count',
                 'target_inference_calls','measured_cells'):
        need(result[name]==qualification[name]==0 and type(result[name]) is type(qualification[name]) is int,
             'V2 numerical and scientific counters must remain exact zero')
    need(len(result['reports'])==99 and all(row['phase']=='call' for row in result['reports'])
         and sum(row['outcome']=='passed' for row in result['reports'])==43
         and sum(row['outcome']=='failed' for row in result['reports'])==56
         and not(output/'fixture').exists() and not(output/'cases').exists(),
         'V2 has43 passing56 failing tests and no actual case transaction')
    raw,_=asset(output/'junit.xml',outputs['junit.xml'],8*1024**2,compact=True)
    suites=list(ET.fromstring(raw).iter('testsuite'))
    need(sum(int(s.attrib['tests']) for s in suites)==99
         and sum(int(s.attrib['failures']) for s in suites)==56
         and all(int(s.attrib.get(key,'0'))==0 for s in suites for key in ('errors','skipped')),
         'independent failed V2 JUnit counts changed')
    manifest=document(FAILED_ARCHIVE/'manifest.json',FAILED_MANIFEST_SHA)
    packet_summary=document(FAILED_ARCHIVE/'summary.json',FAILED_SUMMARY_SHA)
    need(len(manifest['artifacts'])==packet_summary['artifacts']==26 and packet_summary['payload_bytes']==1872657
         and packet_summary['tests']['total']==99 and packet_summary['tests']['passed']==43
         and packet_summary['tests']['failed']==56 and packet_summary['actual_case_claims_created']==0
         and packet_summary['actual_fixture_created'] is False
         and packet_summary['fabricated_tests_and_caches_copied'] is False
         and packet_summary['native_receipt_sha256']==FAILED_RECEIPT_SHA
         and packet_summary['source_review_sha256']==PREVIOUS_REVIEW_SHA
         and packet_summary['source_files']==pins['reviewed_files'],
         'exact26-pair frozen metadata-test refusal packet required')
    include(FAILED_ARCHIVE/'manifest.json',FAILED_MANIFEST_SHA)
    include(FAILED_ARCHIVE/'summary.json',FAILED_SUMMARY_SHA)
    include(FAILED_ARCHIVE/'README.md','39224ebbd42df0543c9f2b449ca6691ebf0129438236b2be6b71754e7213c963')
    include(FAILED_ARCHIVE/'.gitattributes','705fd4d6451a31d36b3df7de96f83f30ac976c9b4a6d1e51671d8e2f33e2d0da')
    expected_names={'manifest.json','summary.json','README.md','.gitattributes'}
    for row in manifest['artifacts']:
        source=ROOT/row['source'];copied=FAILED_ARCHIVE/row['path']
        need(source.resolve(strict=True).is_relative_to(ROOT) and copied.resolve(strict=True).is_relative_to(FAILED_ARCHIVE)
             and source.stat().st_size==copied.stat().st_size==row['bytes'],'test-refusal source/archive path or size changed')
        include(source,row['sha256']);include(copied,row['sha256']);expected_names.add(row['path'])
    need(sum(row['bytes'] for row in manifest['artifacts'])==1872657
         and len(expected_names)==30
         and {p.relative_to(FAILED_ARCHIVE).as_posix() for p in FAILED_ARCHIVE.rglob('*') if p.is_file()}==expected_names,
         'exact30-file test-refusal packet inventory required')
    summary=dict(base['summary'],preserved_failed_worker_v2={'pins_sha256':PREVIOUS_PINS_SHA,
        'source_review_sha256':PREVIOUS_REVIEW_SHA,'native_directory':str(FAILED_NATIVE),
        'native_receipt_sha256':FAILED_RECEIPT_SHA,'accepted':False,'tests_executed':99,
        'tests_passed':43,'tests_failed':56,'actual_claims_created':False,'worker_route_qualified':False,
        'current_source_updates':0,'support_updates':0,'selected_restore_count':0,'query_inference_calls':0,
        'measured_cells':0,'archive_manifest_sha256':FAILED_MANIFEST_SHA,'archive_summary_sha256':FAILED_SUMMARY_SHA,
        'archive_pairs':26,'failure':'mapping-only JSON encoder rejected list/scalar metric roots in metadata tests'},
        native_names=[*base['summary']['native_names'],FAILED_NATIVE.name])
    return {'files':dict(sorted(files.items())),'roles':dict(sorted(roles.items())),'summary':summary}
