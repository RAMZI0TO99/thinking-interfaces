# Linear staged recorder integration, 15 October 2026

Status: accepted engineering integration. Native Job
`20261015T181817Z_f414858df0` passed, and the fresh stdlib closeout passed at
18:27:58 UTC. All 73 tests passed; a real canonical CaseRecorder transaction
called the backend once and the independent verifier twice under its lock,
then wrote one engineering success. Measured cells, current training updates,
model construction, weight decoding, restoration and target inference were zero.
The completed docs/evidence checkpoint was pushed first as
`277d7975ba400a9927bdd3e1495f6ade25ddea38`; this recorder is the next completed step.

## Executed result

The [three-file core](cho51_linear_recorder_v1/README.md) connects exact accepted
historical linear publication/restoration proofs to a fresh request, parent
attestation, claim, engineering intent and engineering success. The actual plan
is Cho2017 / subject_02 / labram_linear / 5 shots per class / seed 11 / repetition 1.
Its case ID is
`9d3596b5e7653e1708eb208d6b150b86cae02227e6cd73a25e4358e675afc141`.
The isolated ledger has one planned and one engineering-success case; measured,
failed, pending, claimed-unmeasured and recovery-pending counts are all zero.
Original scientific case attempts remain zero.

The 73 parameterized tests (29 test functions) passed once in the accepted v2
Job, with no failures, errors or skips; JUnit reports 16.485 seconds. The full
native Job took 412.501637 seconds, from 18:18:17.241522 to 18:25:09.743159 UTC.
Peak process/Job memory was 1,650,561,024 / 1,684,840,448 bytes. Atomic assignment,
membership and limits were verified; the Job closed empty, all handles closed,
and a fresh query found it absent. Cleanup and peak-sampling error lists are empty.

Admission retained 600 seconds, 4,096/5,120 MiB process/Job, 10/4 GiB
startup/active RAM, 20 GiB disk, Torch threads 1/1, hidden GPUs and all four
genuine Pro2 pause paths. The fresh preflight observed 14,575,558,656 available
RAM bytes and 98,496,729,088 disk bytes, with all four pause files absent.
Necessary pinned Torch/NumPy dependency imports and environment queries were
allowed; 2,364 loaded module files were byte-verified. Observed numerical calls,
unexpected denials and computational target-input reads were empty.

## Preserved refusal and separately reviewed repair

The [v1 refusal packet](../../evidence/cho51-linear-recorder-preclaim-refusal-20261015/README.md)
preserves 23 source-identical metadata artifacts. All 73 tests passed in 16.51
seconds, then Job `20261015T180810Z_e981bcd65c` rejected exit 1 during pin hashing.
The reviewed code and ordered pins identify 52 inherited EEGNet manifest JSON
sidecars matching a broad data-path prohibition; the raw trace does not persist
the precise denied path. No production fixture, claim, backend, verifier or
terminal was created, and no result/qualification JSON exists. The Job closed
empty and was freshly absent. This first attempt remains unqualified and frozen.
Refusal manifest/summary SHA-256:
`304e219f41221f9f767869a4189f0a98b87f134e332d434083dacecb6df1321f` /
`30155d26cc0d96950f308ffbfa161275ae63952c02dc4261f5fc2d683d16e885`.

Only runtime.py and closeout.py changed in the separately versioned
`runs/coordination/cho51_linear_recorder_20261015_v2`. The other five operational
sources and all three core files retain their reviewed bytes. The bounded
exception authorizes exactly 52 historical manifest paths and frozen hashes,
54,539 bytes total, under three trusted metadata readers. All 52 have positive
pin, origin and transaction hash witnesses in the accepted qualification.
Ordinary metadata remains bounded at 8 MiB, with direct-path, single-link and
stable-identity checks. Array decoding and computational reads remain blocked.

Independent source review passed all ten settled sources with zero actionable
findings: eight Python AST checks, PowerShell parse and structural test inventory.
Source-review SHA-256:
`e44d6b369c72597053cfbe645c29af562592b82e99bf8650390c161da809ea6a`.
The external pins bind 2,045 source/context files, five runtime files, and
separate baseline/selected weights:
`82abad27bd40af689a81d99b8310402dc9d1b2f1ff14242d0236f71720fabbd7`.
The 2,004-file role-labelled origin contract SHA-256 is
`6cd400d6c24db1ca8de7576b97fa3925cb89ffa975c3ca03a95412ca600247b4`.

## Provenance, evidence and closure

Historical publication/restoration retains commit
`4491e2a68126d6b7293261f4954b88c11c29049d`, dirty=true. The actual recorder
control context separately captured
`277d7975ba400a9927bdd3e1495f6ade25ddea38`, dirty=true. Both retain the five-TOML
fingerprint `9c2e6ad444c44309f9d4becda2909fba0d2fe315f047560f9adbce56397c9299`.
The case ID derives from the plan tuple and is equal across these Git contexts.
The next publication commit becomes another historical boundary; frozen
launchers and source captures must never be rewritten or replayed to conceal it.

Historical work was authenticated without replay: 102 folds and 51 final-source
subjects, 5,253 updates (5,151 source plus 102 support), two detached restorations,
223 tensors / 5,818,138 elements and 402 head parameters. Unchanged single-root
factories and the original scientific case remain unqualified.
The earlier final audit and seven exact snapshots remain in the
[publication closeout export](../../evidence/cho51-linear-closeout-export-20261015/README.md).

The [accepted recorder packet](../../evidence/cho51-linear-recorder-20261015/README.md)
contains 37 byte-identical artifacts, including complete evidence and the real
request/attestation/claim/intent/success, with arrays and weights excluded.
Manifest SHA-256:
`23a93c2b4bfcecfdbc3dfe0fcd4113949f2ae65e1222c242be1e73e4b8fe4840`.
Summary SHA-256:
`38ba20b4bbf169fa788fd7c3630152c51a52b9dcc324c04b67f66e5c388f1a8b`.
Result SHA-256:
`6a24c49570e5b9dd42a18594d9611c4863710bf56606f412f9e451226ff631c7`.
Qualification SHA-256:
`2a8394630cf700b600d757d1af3523769d0300b8f529a2fc60ecebaef64e4b18`.

Fresh post-Job audits rehashed all 213 physical input files / 734,579,463 bytes
without decoding, plus baseline/selected weights. Canonical 432 source files
remain unchanged. Independent metadata review checks all 26 scoped native names
for fresh absence while preserving their actual mixed acceptance statuses.
Closure requires a passed write-once v2 final-review.json binding this report,
all six current resume heads, sources, proofs and archives. The
[recorder closeout export](../../evidence/cho51-linear-recorder-closeout-export-20261015/README.md)
preserves that review and its seven exact document snapshots so later docs can
advance without changing the accepted bindings.

## Next finite step and remaining gates

Next prepare separately versioned synthetic linear target-support adaptation
and query-route integration, then worker-route qualification. Start with source
contracts and independent review; any numerical execution needs fresh runtime
and Git pins, coordination, resource admission and a new bounded native Job.
The accepted engineering receipt does not authorize a scientific cell.

The unchanged single-root high-level factories, full 1,020-cell worker,
checkpoint cohort/prior-training lineage, final owner freeze and scientific
execution remain pending. Original case attempts remain zero. No new autonomous
window or peer release is inferred. Explicit recovery requires externally pinned
request/attestation digests and independent revalidation under the real lock;
it can replay only an existing intent and must never invoke the backend again.
Git exports metadata and candidate sources; it does not restore October 15
fixture arrays, trained weights, environments or caches on another machine.
