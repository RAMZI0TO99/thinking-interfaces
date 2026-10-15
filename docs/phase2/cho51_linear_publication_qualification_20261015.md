# Linear publication and staged detached restoration, 15 October 2026

Both fresh native Jobs passed. The accepted LaBraM linear source was published
through the unchanged canonical `SelectedSourceStore`, then restored twice in a
separate Job. All 223 tensors matched, the two models had disjoint storage, and
the second restoration returned the actual `LaBraMTunedAdapter`. This phase
performed **zero new training updates**, zero target predictions and zero
scientific cells. All 5,253 accepted fitting updates remain historical.

Metadata closeout passed. Closure requires the passed
[final independent review](../../runs/coordination/cho51_linear_publication_20261015_v1/final-review.json)
and matching bindings for this report and all six resume heads. The numerical
Jobs are finished; neither used output may be replayed or reset.

## Exact scope and provenance

The separately versioned implementation is
[`cho51_linear_publication_v1`](cho51_linear_publication_v1/README.md), with
operational sources and receipts in
[`cho51_linear_publication_20261015_v1`](../../runs/coordination/cho51_linear_publication_20261015_v1).
Its origin authenticates the accepted
[complete linear chain](cho51_linear_chain_qualification_20261015.md), including
102 source folds, the winning `lr_1e-3` candidate and its fresh 51-source fit.
The prior exact selection means, 8/17 versus 22/51, are historical evidence;
selection and fitting were not repeated here.

An explicit staged bridge uses two roots. Architecture and canonical baseline
construction come from the project. Evidence and the local canonical store use
a fresh mirror containing exactly the original fixture's five TOMLs, marked
read-only. That mirror reproduces the accepted source fingerprint and Git
context. Arrays and baseline weights remain at their authenticated origins.
No extra architecture TOMLs were added to the frozen fixture or mirror.

The unchanged high-level single-root Cho publication/restoration factories
remain **unqualified**: their one-root interface does not represent this
accepted fixture's separate provenance and architecture roots. The new staged
digest checker and adapter factory invoke the unchanged public canonical
store APIs, canonical complete-evidence verifier, strict state loading and
manifest byte verification. This qualifies the explicit staged route only.

## Executed validation

| Observation | Publication | Detached restoration |
| --- | ---: | ---: |
| Native Job | `20261015T171419Z_8541ad2a1b` | `20261015T171853Z_68af8454b0` |
| Native elapsed seconds | 135.997071 | 271.810105 |
| Safe tensor decodes | 3 | 4 |
| Strict state loads | 2 | 4 |
| Safe tensor saves | 1 | 0 |
| Loaded module files rehashed | 4,048 | 3,945 |
| Constructor dummy forward calls | 14 | 28 |
| New source/support updates | 0 / 0 | 0 / 0 |
| Target or classifier inference calls | 0 | 0 |
| Protected target read attempts | 0 | 0 |

The publication Job passed 20 literal boundary tests, with zero subtests,
skips or unexpected outcomes. The detached Job authenticated and reused that
exact test receipt without rerunning tests. Both native receipts accepted
exit 0, normal completion, empty Jobs before closure and fresh named-Job
absence. Cleanup and peak-sampling error lists are empty. Native elapsed time
totals 407.807176 seconds across the two Jobs.

Publication peak process/Job commit was 1,898,426,368 / 1,929,728,000 bytes;
detached restoration peaked at 1,946,611,712 / 1,976,614,912 bytes. Each retained
the 600-second deadline, 4,096/5,120 MiB process/Job limits, 10 GiB startup and
4 GiB continuing RAM floors, 20 GiB disk floor, Torch threads 1/1, hidden GPUs
and four genuine peer pause paths. The canonical baseline construction checks
also retained their 6 GiB pre-restore and 4 GiB continuing RAM floors.

The accepted canonical constructor's zero-input patch-shape probe is permitted
only in its pinned construction subtree under `no_grad` and is counted above.
It is not target or classifier inference. Optimizer and backward calls stayed
at zero. Torch, NumPy and Python RNG state remained unchanged. Each Job blocked
one expected optional IPv6 import probe; unexpected denials remained zero.

The detached result externally binds the publication result's physical SHA,
not a newly inferred path. It performs two independent canonical-store
restorations with separate baseline construction: one digest check and one
actual adapter factory. Both verify 223 finite CPU float32 tensors comprising
5,818,138 elements, including 402 head parameters, and the same accepted
model state and recipe. The adapter is released only after these checks pass.

## Frozen identities and retained evidence

| Artifact | SHA-256 |
| --- | --- |
| Origin contract | `8bffd0d8be4f8ed2b87189ec0f36462303b88c627b1a8115c7651805a8a5c20b` |
| Stage contract file | `44be46161ac332f3195dd3f412998a4c90b767b306e6aadd25df2a59e558b422` |
| Reviewed source record | `5d5a31365a29c7392ff19a2844e8f79bcd90f654b94120408f017d8fc55f648f` |
| Immutable pin inventory | `30130ec6a122323e2504d70645f86d07cc430f587c2bc109d8aae5f125bd99e9` |
| Publication result | `86d8f400abc6345d18893fc4456152bba20115ac9946ddd1bcbf9109b1528f08` |
| Detached restoration result | `4c51e47f3c3e08d7c8c3a666a41676d2bc2ed5af0c24af5a5d7f56bb737805ab` |
| Canonical manifest logical digest | `67a77b1f88d68a7c4ac9bce8705c74c96451cca13a0af479b1ffebb808952fd1` |
| Original and published safe weights | `3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048` |
| Full model state | `8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01` |
| Actual winning model recipe | `bdb40fd0f3becf87cc619e87a536ee4a921e72efa422fcaaf235c3573865a452` |
| Complete evidence physical file | `e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3` |
| Complete evidence logical envelope | `1c19664276cc05d5252631513001871b532dc5362f93dfabf38e48acc9ca904a` |
| Tensor witness | `be62b3fc4c7faf0c0b3f8b9752a195d2b65173dbbd5d450d93dbffa15892dca9` |
| Adapter witness | `785715751732145c56f59b72a33a43133a7e90119a2c72bcd344f12eb6c5136b` |

The inventory binds 1,937 source/context files, five runtime files, one baseline
weight file and the original selected checkpoint as a separate hash-only group.
All 11 new source files were reviewed before launch; nine Python AST checks and
the PowerShell parse passed. The origin retains 886 hard proof bindings.
Canonical 432-file source fingerprint remains
`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`.

Selected weights are 23,294,624 bytes; complete canonical evidence is
23,087,023 bytes. Ordinary metadata retains an 8 MiB limit, with a narrow
32 MiB exception for the exact complete-evidence copies and a 64 MiB limit for
the exact safe weights inside native restoration. Outside numerical Jobs,
weights are streamed for hashes only. The canonical generic manifest-byte
hashing ceiling remains unchanged; staged exact-file size and identity guards
apply before and after it. Archives exclude weights and arrays.

The [51-artifact metadata packet](../../evidence/cho51-linear-publication-20261015/README.md)
contains 25,643,330 bytes of source-identical artifacts. Its manifest SHA is
`b084c34bc8248dddad1244ff30e1b5ecc70c2f1dade2ba557541a500b67877d3`;
summary SHA is
`2ff724c7fb31a140f1e470611c0b5500b8c81d84ea4ce1085a0e3edc7e8c3268`.
Exactly one archived artifact exceeds 8 MiB: the authenticated complete-evidence
copy under its narrow 32 MiB bound. All other artifacts retain 8 MiB.

Independent read-only metadata review found no actionable issues. After both
Jobs finished, all 213 original input files, totaling 734,579,463 bytes, were
stream-hashed and matched their accepted sizes and hashes. Original inputs,
checkpoint, baseline and canonical source remain unchanged. All 24 referenced
named Jobs (22 historical and two fresh) were freshly absent; this makes no
claim about unrelated migration directories. Current module maps cover 4,048
unique files, with the detached 3,945 a subset, and were rehashed without drift.
The separate expanded audit of 14 historical qualification maps covers 4,838
unique files; the historical/current union is 4,846, without hash conflicts or
drift. These scopes do not replace older reports' narrower historical counts.

The independent final review binds the packet, this report and all six current
resume heads. The packet itself contains the frozen sources and operational
proofs; report/head settlement is a separate final-review binding. Older reports,
packets, source evidence and receipts remain preserved.

## Next bounded step

Prepare separately versioned **linear staged recorder integration**, consuming
these exact accepted publication and detached-restoration proofs. The older
EEGNet recorder has different tensor, method and byte limits and cannot certify
this linear source unchanged. Preserve original artifacts and create fresh
pins, output paths, admission and native receipts for any future execution.

Recorder integration, unchanged single-root factory compatibility, the full
1,020-cell worker, cohort and prior-training lineage, the owner's final freeze
and scientific execution remain pending. Original case attempts remain zero;
measured scientific cells remain zero. This finite two-Job phase creates no new
30-hour window, peer release, Source030 renewal or obsolete watcher authority.
