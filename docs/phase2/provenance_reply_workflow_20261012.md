# Provenance reply workflow: executed engineering qualification

12 October 2026 UTC. The new
[one-time collector and offline review preparation](../../tools/provenance/README.md)
connects the existing strict cohort intake and declared-overlap checkers to the
actual public request. It preserves received bytes, source dates and exact
file identities, then creates an unsigned review draft only for an explicitly
selected reply from the expected repository owner. No training IDs, exclusions
or exposure claims are extracted automatically from prose.

## Live collection result

At **12:35:22.563519 UTC**, a guarded, one-time read of
[LaBraM issue #75](https://github.com/935963004/LaBraM/issues/75) found **zero
comments**. The exact original request author, title, URL and body hash still
matched. Issue metadata before and after the comment read agreed; the complete
comment page was empty. The captured raw responses and success receipt are in
[portable evidence](../../evidence/provenance-reply-workflow-20261012/README.md).
No real reply was prepared as a cohort submission. This is a dated observation,
not a promise about later comments. No further message or automatic poll occurred.

## Executed qualification

The initial implementation passed **31 behavioral tests** in a guarded native
Job, in 38.778 seconds. Its exact executed recipe bytes are preserved as history.
The final version adds byte-identical copies of the previously qualified
metadata dependencies with `* -text` attributes, so Windows checkout line endings
cannot invalidate their pinned hashes. The original checker files and evaluation
package remain unchanged.

A fresh checkout of the staged candidate used `core.autocrlf=true`,
`core.eol=crlf` and the different path `tmp/Provenance Windows checkout 001`.
The existing source normalizer restored the pinned 432-file source in that
isolated folder. All four metadata dependency hashes matched their originals.
The final **33 behavioral tests passed in 37.135 seconds** from that folder,
including successful collection and preparation CLI paths and rejected preparation.
Candidate index tree: `46e710a593282a01d577fbc5ee0bad99f1cfd1d1`.
This was a fresh local Windows checkout on this host, not a second device runtime.

Cases cover no reply, an observed owner reply without acceptance, third-party
comments, wrong owner association, UTF-8 statement custody, ignored executable
prose and links, untouched training fields, issue/body/count drift, duplicate IDs,
wrong issue URLs, complete two-page capture, refused partial pagination,
missing/empty selected comments, altered captured bytes, attempted original-case
resets, forged admission, traversal, output reuse, dependency drift, duplicate
JSON keys, invalid UTF-8/non-finite/oversized metadata, UTC/date ordering and safe
CLI summaries. Synthetic replies are labelled as fixtures; no actual owner
training statement or cohort evidence was authenticated.

The three operations used separate guarded native Jobs:

| Operation | Job | Result |
| --- | --- | --- |
| Initial 31 synthetic cases | `20261012T123202Z_fd1de22245` | Passed |
| Live read-only issue/comment collection | `20261012T123518Z_9e4530553f` | Passed; zero comments |
| Different-path Windows checkout and final 33 cases | `20261012T123726Z_39f3043012` | Passed |

Each used fresh source/operations/runtime pins, a 180-second outer bound,
startup RAM10 GiB, active RAM4 GiB, disk20 GiB, process256 MiB, Job512 MiB and
one native thread. The final checkout Job's peak aggregate commit was
79,323,136 bytes. Native receipts confirm atomic Job membership, normal exit,
empty/closed Job, closed handles and physical absence. Portable evidence keeps
the admissions, logs, receipts, checkout recipe, final code identities and live
response bytes. A preliminary lint failure was fixed before the first Job;
current owned workflow code passes Ruff without exclusions.

## Current boundary and next inputs

Canonical Source remains **432 files /
`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`**.
Historical quality SHA remains
`4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357`;
its full suite was not replayed. Original owner packet SHA remains
`2a890980541120b4d311078436fe85aac13e77f3f33871739ab62347320ff400`.
The workflow adds separate metadata tooling; no frozen implementation,
checkpoint, raw EEG, cache, model, fit, recorder or original case was changed or
executed. Original attempts remain **two spent/zero left**. Actual checkpoint
recording coverage and evaluation overlap remain unknown. Gate A, the seven
owner decisions and experiment freeze remain unsigned at this step's capture.

The four design decisions are now presented to the owner for explicit
ratification of the already pinned scope/candidates, primary rule, empty secondary
superiority family and exploratory margin interpretation. No answer is inferred
from this engineering work. Gate A rationale, checkpoint-cohort evidence/review
and the final freeze remain separate outstanding decisions even if those four
design choices are ratified. An owner decision cannot reset the original case.

When an authentic relevant reply arrives, collect it in a fresh directory,
select its actual comment ID, preserve the resulting unsigned draft, and review
checkpoint/run linkage, coverage completeness and mappings against the fixed
170-subject/397-recording inventory. A statement that the mapping is unavailable
needs an explicit recorded limitation and owner claim decision. A successful
collector/checker alone never admits scientific execution. Subsequent operations
require fresh finite scope, resource admission and current coordination.
