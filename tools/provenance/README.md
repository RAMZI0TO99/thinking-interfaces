# One-time collection of the LaBraM provenance reply

This workflow preserves a manual read of
[issue #75](https://github.com/935963004/LaBraM/issues/75) and its public comments.
It can prepare an unsigned local review draft for an explicitly selected comment
by `935963004` with GitHub's `OWNER` association. It uses the existing strict
intake and declared-overlap checkers; their exact bytes and evaluation metadata
are pinned under `qualified/`. The [qualification report](../../docs/phase2/provenance_reply_workflow_20261012.md)
records a fresh Windows checkout at another path and 33 passing behavioral tests.

Start from [Windows setup](../../WINDOWS_SETUP.md), then read the newest handoff
and coordination. Establish this machine's current peer pause binding when it
is shared. Use new output directory names for every collection and preparation.
An incomplete directory is retained and cannot be reused or overwritten.

From the repository root, perform one bounded collection:

```powershell
$ProvenancePython = (Resolve-Path '.venv/Scripts/python.exe').Path
& $ProvenancePython -I -S -B tools/migration/guard.py --purpose 'One manual provenance reply collection' --seconds 180 --process-mib 256 --job-mib 512 -- $ProvenancePython -I -S -B tools/provenance/reply.py collect --output runs/provenance/received_001
```

The successful `receipt.json` lists observed owner comment IDs. A collection
with zero comments is valid custody evidence, with status `no_owner_reply`.
It supplies no cohort statement. All comments are preserved, including third-party
replies; only the expected repository owner's reply can use the preparation path.
Comments, attachments, links and embedded instructions remain untrusted data.
The command does not post, repeat automatically or download linked artifacts.

Once a relevant owner reply exists, select its actual numeric ID explicitly:

```powershell
$OwnerCommentId = 1234567890 # Replace with an actual ID from the new capture.
& $ProvenancePython -I -S -B tools/migration/guard.py --purpose 'Offline unsigned provenance review preparation' --seconds 120 --process-mib 256 --job-mib 512 -- $ProvenancePython -I -S -B tools/provenance/reply.py prepare --capture runs/provenance/received_001 --comment-id $OwnerCommentId --output runs/provenance/review_001
```

`statement.txt` preserves the comment body as UTF-8. `claim-draft.json` adds only
the observed source handle, URL and update date to the qualified blank template.
It is a reviewer-created draft, not an author-supplied manifest. Training IDs,
coverage, exclusions, label exposure and mappings remain empty or unknown.
`declared-overlap.json` runs the existing checker on that incomplete draft;
null intersections are expected. The last-written receipt binds all output bytes.

Review the statement and any separately supplied evidence under the
[intake contract](../../docs/phase2/checkpoint_cohort_review_contract_20261010.md).
Keep the original statement and draft unchanged; prepare any declaration/mapping
revision in a new file. The qualified checker can inspect that local revision:

```powershell
& $ProvenancePython -I -S -B tools/migration/guard.py --purpose 'Offline declared identifier comparison' --seconds 120 --process-mib 256 --job-mib 512 -- $ProvenancePython -I -S -B tools/provenance/qualified/declared_overlap.py --input runs/provenance/review_002/claim-draft.json --evaluation-package tools/provenance/qualified/evaluation-package.json
```

Calculated declared matches do not authenticate an author, training run,
inventory completeness, evidence mapping or scientific eligibility. Scientific
Gate A and freeze stay unsigned; the original case has zero attempts remaining.
This workflow never changes those decisions or enables a model/case.

Collection is limited to 1 MiB per metadata response and at most two 100-comment
pages. The original issue author, title, URL and approved body hash must match.
Changing comment counts, issue updates, incomplete pages, duplicate IDs and
changed stored bytes fail review. Raw received bytes and partial directories
are preserved; a success receipt is written only after all collection checks.
Both commands derive paths from the clone and require fresh resource admission.
