# Synthetic linear target route qualification, 17 October 2026

Status: accepted engineering target route. Native Job
`20261017T082815Z_a8741452ca` passed, followed by the reviewed stdlib closeout.
All 68 tests passed; the real canonical adapter completed one head-only support
update and one two-trial query batch. Source updates, record_cell calls,
measured cells and original scientific attempts were zero. The two preceding
guard refusals are preserved separately; their component successes did not
qualify the full route.

## Executed target case

The [unchanged three-file candidate](cho51_linear_target_route_v1/README.md)
uses the real LaBraMTunedAdapter and LaBraMTuningManifestRunner for Cho2017 /
subject_02 / labram_linear / five shots per class / seed 11 / repetition 1.
The 42-trial synthetic episode has support rows 0-9, query rows 40-41 and unused
maximum-support-pool rows 10-39. Target Profile B inputs were (10,64,800) for
support and (2,64,800) for query. Two independent canonical bindings produced
exactly six NPZ loads: target Profile A four and B two. The other subjects'
arrays were not decoded; their catalogues were reconstructed from authenticated
historical synthetic metadata and checked against the accepted selection.

The actual selected settings were linear, one support step, learning rate 0.001,
no partial depth and query batch size eight. SGD updated only head.weight and
head.bias (402 parameters); gradients and support loss were finite. Both head
tensors changed. The other 221 state tensors, backbone/buffers and all 223
source tensors remained exact. Caller source, runner-owned source and adapted
copy had disjoint storage. The classifier and its backbone were in eval mode during the support/query
forwards. The query forward ran in inference mode, with adapted and source
state unchanged through inference.
Query labels and unused pool rows were excluded from adaptation.

One constructor performed the canonical no-gradient (1,128,3000) patcher shape
probe. Baseline initialization and selected-state restoration each required one
safe decode and one strict state load, two of each total; selected restore count
was one in this accepted Job. There were two classifier/backbone forwards,
one Tensor backward, one autograd backward, one optimizer and one SGD step.
Four parameterless Rearrange reconstructions and two empty zero-depth ModuleList
containers outside baseline construction were separately bounded and witnessed. These structural operations
were distinct from full model construction. The canonical parameterless loss
criterion was allowed; its constructor was not separately counted at runtime.

Selected source state SHA-256 remains
`8de802bc0577864edcfc857fa93cf24db527b09ecf0eded0b3e980a82a7b4c01`;
adapted clone state SHA-256 is
`5bd88f2afb0a2e667e3576bb82c037e3314cce0e8cfb4383ee7439fee57787dd`.
The support loss was 1.113249659538269. Query predictions were [1,0] against
labels [0,1], with confusion matrix [[0,1],[1,0]]: both predictions were
incorrect. This checkpoint validates execution and isolation on the synthetic
fixture. Scientific predictive performance remains unqualified; no settings
were retuned using those query labels. A second numerical label-swap experiment
was outside the one-support-update budget; metadata leakage boundaries and the
actual support inputs were checked in the accepted run.

## Native execution and tests

All 68 parameterized metadata boundary cases (17 test functions) passed once
in v3, with zero failures, errors or skips. JUnit reports 1.457 seconds
(terminal 1.46). Failed v1/v2 each also passed 68 tests; those receipts are
separate historical attempts, not additional accepted cases or tests in this run.

The accepted Job ran from 08:28:15.740029 to 08:29:00.290700 UTC,
44.550671 seconds. Peak process/Job memory was 1,486,721,024 / 1,524,404,224 bytes.
Atomic assignment, membership and configured limits were verified. It closed
empty with every handle closed and a fresh native query confirmed absence;
cleanup and peak-sampling error lists were empty.

Admission retained 600 seconds, process/Job 4,096/5,120 MiB, startup/active RAM
10/4 GiB, disk 20 GiB, Torch threads 1/1, hidden GPUs and all four genuine pause
paths. The immediate observation at 08:28:11 UTC found 15,736,700,928 available
RAM bytes and 68,122,771,456 disk bytes, with all four pauses absent. The runtime
verified 4,818 loaded module files and recorded zero unexpected denials. No peer
release or new autonomous window was inferred.

## Preserved refusals and scoped repairs

[V1 model-copy refusal](../../evidence/cho51-linear-target-copy-refusal-20261017/README.md):
Job `20261017T081058Z_9432a219d7` passed 68 tests (JUnit 1.546 seconds) and
persisted a selected-restoration component witness, then blocked the first
canonical deepcopy at einops RearrangeMixin.__setstate__ reinitialization.
It exited 1 in 22.953775 seconds and closed empty/freshly absent.
The packet preserves 25 source-identical artifacts / 1,045,895 bytes, 29 files.
Manifest/summary SHA-256:
`3baff57859c5fd9ede1c4982eb4a0b3538714ada22e044a611e1ed86d971e91b` /
`fcc9bf823004b600d68270778466326db879ab4dc76355fbdac3f698d44867c7`.

[V2 empty-container refusal](../../evidence/cho51-linear-target-empty-container-refusal-20261017/README.md):
Job `20261017T082008Z_1662de273b` passed 68 tests (JUnit 2.485 seconds), restored
selected state and returned from the first deepcopy. Canonical zero-depth
masking then formed an empty ModuleList and the guard refused its initialization.
It exited 1 in 30.058916 seconds and closed empty/freshly absent.
The packet preserves 25 source-identical artifacts / 1,080,294 bytes, 29 files.
Manifest/summary SHA-256:
`45a6e21f0583412edc38784249677856952e9479bf3f8d37e557b970a06d6f7c` /
`7479b2cb916e813f98c98cd16f781601e2e84049881c568b640eef31a703416f`.

Neither failed attempt has result, qualification or target-witness JSON. Their
trace/source order stops before support adaptation and query inference. The
restoration and clone components do not establish whole-route qualification.
Both attempts' code and output bytes remain frozen. V3 reuses all three core
files unchanged, pins four library implementation sources, and permits only
exact class/pattern/state/caller-bound parameterless clone operations and empty
depth-zero containers. The complete remaining path, including 397 Torch files,
was statically inspected before the independently admitted v3 Job.

## Provenance, runtime and evidence

Historical source commit remains
`4491e2a68126d6b7293261f4954b88c11c29049d`, dirty=true; historical recorder context
is `277d7975ba400a9927bdd3e1495f6ade25ddea38`, dirty=true. This target route
captured actual current commit `3ef0c395d6bc4abf82633cf746708434a79c18b4`, dirty=true.
All retain five-TOML fingerprint
`9c2e6ad444c44309f9d4becda2909fba0d2fe315f047560f9adbce56397c9299`.
The new explicit two-root restoration authenticated recorded complete-source
proofs, derived canonical architecture, strictly loaded the exact selected state
and returned the real adapter. It did not run the unchanged canonical-store
restoration, single-root factories or public complete-evidence verifier under
new Git. These routes remain unqualified; historical provenance was not rewritten.

Observed runtime replacements affected exactly 21 binaries across 2,369 checked
paths: three interpreter binaries and 18 standard-library .pyd files, all under
the bundled Python base. The other 2,348 mapped paths were unchanged and none
was missing. Both recorded short Python versions are 3.12.14; replacement cause
and ABI equivalence were not inferred. Fresh current runtime qualification uses
five executable/DLL pins, 18 extension pins and four supporting implementation
pins. Transition receipt SHA-256:
`a6ebb4269219d023f28e79c07870b6979b466e7c2f978bcfa4c7983603c9e5d4`.
The unchanged exact-hash Git executable is the sole admitted two-hard-link
runtime exception. Ordinary proofs and weights retain single-link checks.

Independent source review covered ten settled sources, eight Python AST checks
and clean PowerShell parsing, with zero remaining findings. V3 review SHA-256:
`a7c25b2f80f8babb74dd710309cb4290af7c5d31af514f7cfca5025e2f16e09d`.
The frozen bundle pins 2,280 source/context files and a 2,275-file role-labelled
origin contract. Pins SHA-256:
`759827205d2256e6c532bcb5cc056ec2683ad8d210dda4fce2b6b7e141fcb9e8`.
Origin-contract SHA-256:
`cf258567cca57a3865cd349201680bced0e529c681146ff0345d520e8a362d4e`.
Ordinary metadata stays at 8 MiB, exact complete evidence at 32 MiB, exact safe
weights at 64 MiB. Off-Job checks stream-hash arrays/weights without decoding;
all numerical execution and tests stayed inside fresh native Jobs.

The [accepted packet](../../evidence/cho51-linear-target-route-20261017-v3/README.md)
preserves 30 source-identical artifacts / 25,239,603 bytes, with 34 total files
including wrappers and its own byte-preserving Git attributes. Arrays, weights,
caches and live run trees are excluded. Manifest/summary SHA-256:
`5774bfdd46f19481003fb5637ae16cb697d35d4f4954370f623e330ac6de01a7` /
`d51324337406c76c792ef6cbb10bd2176e2a6a0e3dbb6f0893d4d9f07cdbcc58`.
Result/qualification SHA-256:
`d1e7d92bf1fe52e127fc7b33f1ec4b2800e54c2643f0335beb46f169730ab2f5` /
`81277c4f86420ba19b081675df59883b63179a0c0e3eb9b9301f052dfdbd1acf`.
Target-witness SHA-256:
`21db3a9533e7feea7e95acb0397a7d16f86bfb4a0bfd8c600a9bd59472ae27e0`.

Fresh full audits matched canonical 432 sources, both exact weight files and
all 213 original inputs / 734,579,463 bytes, before/after computation. The final
independent audit checks 29 scoped native names for fresh absence, preserving
actual mixed acceptance statuses. Closure requires the write-once passed v3
final-review.json binding this report and six resume heads, sources, actual
witnesses and all three target packets. Its review and seven exact document
snapshots are preserved in the
[target closeout export](../../evidence/cho51-linear-target-closeout-export-20261017/README.md)
so future docs can advance without rewriting these bindings.

## Next finite step and remaining gates

Next prepare separately versioned worker-route engineering integration using
these accepted source, recorder and target witnesses. The canonical worker
input verifier requires a measured cell/success receipt; an engineering bridge
needs its own reviewed contract and cannot claim that unchanged route passes.
Any later numerical work requires fresh pins, coordination, resources and a new
bounded Job. Historical 102-fold/51-source fitting totals remain 5,253 updates,
with zero replayed source updates here and one new outer-target support update.

Full worker-route qualification, the 1,020-cell worker, unchanged single-root
factories, checkpoint cohort/prior-training lineage, final owner freeze and
scientific execution remain pending. Original scientific attempts remain zero.
No autonomous window, peer release or scientific decision is inferred. Git
metadata exports do not restore the October 17 fixture arrays, weights or runtime
on another device; those assets and fresh admission remain necessary.
