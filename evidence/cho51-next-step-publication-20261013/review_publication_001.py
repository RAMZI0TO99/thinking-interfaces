"""Read-only metadata/hash/link review; no signal arrays or training execution."""
from datetime import datetime,timezone
import hashlib,json,re,sys
from pathlib import Path
root=Path.cwd();run=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'tools/migration'))
from common import digest,source_check
source=source_check(root)
assert source=='3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'
packets={}
for name,count in (('cho51-episode-bindings-20261013',18),('cho51-execution-interfaces-20261013',21)):
    packet=root/'evidence'/name;index=json.loads((packet/'index.json').read_bytes())
    assert len(index['files'])==count
    for row in index['files']:
        path=packet/row['path'];assert path.resolve()==path
        raw=path.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
        # Input/runtime pin bytes refer to reviewed current files, not uploaded data.
        if row['path']=='results/qualification.json':
            q=json.loads(raw);assert q['passed'] and q['unexpected_denials']==0
            assert not q['checkpoint_or_model_or_recorder_operation']
            for relative,sha in q['candidate_input_pins'].items():assert digest(root/relative)==sha,relative
        if row['path']=='guard/receipt.json':
            receipt=json.loads(raw);state=receipt['native_state']
            assert receipt['accepted'] and receipt['job_absent'] and state['job_closed'] and state['job_empty_before_close']
            assert not state['cleanup_errors'] and not state['peak_sampling_errors']
    packets[name]={'artifacts':count,'index_sha256':digest(packet/'index.json'),'artifact_bytes':sum(r['bytes'] for r in index['files'])}
docs=['HANDOFF.md','AGENT_COORDINATION.md','README.md','CONTINUE_HERE.md','WINDOWS_SETUP.md','docs/phase2/README.md','docs/phase2/cho51_episode_binding_qualification_20261013.md','docs/phase2/cho51_execution_interfaces_qualification_20261013.md','docs/phase2/cho51_episode_bindings_v1/README.md','docs/phase2/cho51_execution_interfaces_v1/README.md','evidence/cho51-episode-bindings-20261013/README.md','evidence/cho51-execution-interfaces-20261013/README.md']
links=[]
for rel in docs:
    path=root/rel
    # Older large status sections retain their bytes and previous dated facts.
    # Review this phase's leading block only for shared status documents.
    text=path.read_text(encoding='utf-8')
    if rel in docs[:6]:
        if rel=='WINDOWS_SETUP.md':text=text.split('Use **Windows x64**',1)[0]
        else:
            starts=[m.start() for m in re.finditer(r'^## ',text,re.M)]
            if len(starts)>1:text=text[:starts[1]]
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if '://' in target or target.startswith('#'):continue
        destination=(path.parent/target.split('#',1)[0]).resolve()
        assert destination.is_relative_to(root) and destination.exists(),(rel,target)
        links.append({'document':rel,'target':target})
    assert not re.search(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',text),rel
value={'schema':'cho51_two_phase_publication_metadata_review_v1','passed':True,'observed_utc':datetime.now(timezone.utc).isoformat(),'canonical_source_sha256':source,'canonical_files':432,'active_config_files':13,'packets':packets,'current_document_links_verified':len(links),'links':links,'no_new_arrays_or_model_or_recorder_executed':True,'candidate_guards_passed':2,'scientific_execution_budget_admitted':False,'experiment_freeze_signed':False,'original_case_attempts_remaining':0}
with (run/'review_001.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,sort_keys=True,indent=2)
packet=root/'evidence/cho51-next-step-publication-20261013';packet.mkdir(exist_ok=False)
files=[]
for name in ('review_publication_001.py','review_001.json'):
    raw=(run/name).read_bytes()
    with (packet/name).open('xb') as stream:stream.write(raw)
    files.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
with (packet/'index.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump({'schema':'cho51_publication_review_packet_v1','files':files,'passed':True,'referenced_packets':packets},stream,sort_keys=True,indent=2)
with (packet/'.gitattributes').open('xb') as stream:stream.write(b'* -text\n')
print(json.dumps({'passed':True,'artifact_hashes_verified':sum(v['artifacts'] for v in packets.values()),'live_source_context_pins_verified':445+446,'links_verified':len(links),'canonical_source':source,'new_signal_reads':0}))
