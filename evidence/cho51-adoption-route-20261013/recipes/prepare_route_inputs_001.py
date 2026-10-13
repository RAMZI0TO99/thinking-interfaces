import hashlib
import json
from pathlib import Path

root=Path.cwd()
packet=root/'evidence/cho51-adoption-route-20261013'
packet.mkdir(exist_ok=False)
items={
    'owner/adoption.json':'docs/phase2/cho_51_target_amendment_adoption_20261013.json',
    'owner/adoption.md':'docs/phase2/cho_51_target_amendment_adoption_20261013.md',
    'owner/accepted-proposal.json':'docs/phase2/cho_51_target_amendment_proposal_20261012.json',
    'owner/accepted-proposal.md':'docs/phase2/cho_51_target_amendment_proposal_20261012.md',
    'owner/prior-gate-a-decision.json':'docs/phase2/gate_a_acceptance_20261012.json',
}
for destination,relative in items.items():
    path=packet/destination
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write((root/relative).read_bytes())
with (packet/'.gitattributes').open('xb') as stream:stream.write(b'* -text\n')
print(json.dumps({'owner_artifacts':len(items),'adoption_sha256':hashlib.sha256((packet/'owner/adoption.json').read_bytes()).hexdigest()}))
