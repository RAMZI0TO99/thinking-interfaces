# Bounded startup-timing diagnostic design

Engineering design, 1 November 2026. The
[independent review](../../runs/coordination/cho51_p3_startup_timing_design_20261101_v1/design-review-v2.json)
and [Root acceptance](../../runs/coordination/cho51_p3_startup_timing_design_20261101_v1/root-design-acceptance.json)
accept the exact [five-file design](cho51_p3_startup_timing_v1/README.md), with no
remaining findings. This is design-only acceptance. No source implementation,
runtime operation, test or scientific case was executed in this step.

The selected successor is a separate **QD startup-prefix investigation**. It
measures caller/bootstrap/native-build and supervisor source/runtime-retention
stages, stops immediately before the supervisor mode loop, and then requires
complete final retained-input verification and owned cleanup. It creates no
suite child and does not collect or execute the held probe32/100/384 cohorts.
The existing caller-side UTC/native/bootstrap checks stay in the prefix; their
outcomes cannot replace the missing full-Q controls. QD never qualifies Q or
unlocks P/L/V/C. Its admission and return schemas are disjoint from Q acceptance.

## What the diagnostic will record

The design maps29 caller and21 supervisor stages to exact pinned source locations.
Two parent-owned journals use at most128 contiguous records each,512 bytes per
record including newline, and65,536 bytes per file. All names, event fields,
stage IDs and outcome codes are fixed. Native timestamp identities use exact
integer representation. There is no arbitrary logging, source payload, per-file
event, child telemetry, extra pipe, writable handoff or timing text in result
streams. The pure supplied-byte probe remains unchanged.

The caller journal begins only after its original deadlines and identity checks
are armed. Supervisor events remain in bounded memory until the existing normal
authority chain succeeds. An early killed process may therefore leave those
events UNKNOWN; no timestamp is reconstructed. A new native append primitive
must retain its own original file and ancestry handles. The existing immutable
output writer cannot be used as an append API. Seal means ready for original
close; separate native caller/return evidence must prove actual closure.

One review finding, [F01](../../runs/coordination/cho51_p3_startup_timing_design_20261101_v1/findings-v1.json),
resolved an ambiguity between final-record capacity and sequence positions.
The final design reserves at most122 normal plus six final records, with one
contiguous sequence and no padding or borrowed capacity. Normal success has59
caller records and42 supervisor records, including each ready-to-close mark and
terminal. The [original five-file draft](../../runs/coordination/cho51_p3_startup_timing_design_20261101_v1/draft-v1/manifest.json)
and first candidate remain exact and preserved.

## Bounds and evidence limits

Both journals are charged within the unchanged caller40/20-MiB and
supervisor40/8-MiB partitions. QD's supervisor creates only claim, receipt and
timing journal, bounded at1,118,208 bytes. Including the conservative caller
bound and the entire unchanged fixture/closeout partitions gives a proposed
upper bound of199 files and55,906,304 bytes within256 files/64 MiB. This is static
allocation feasibility, not measured memory, execution time or physical custody.
Implementation must prove its actual complete ledger and source/runtime closure.

The original90 whole/60 work/5 cleanup/65 hard-second envelope, startup5,
two fresh startup samples,250ms guard freshness,512/768-MiB process/Job caps,
4-GiB available RAM,20-GiB disk, one CPU/library thread, hidden GPUs, local stop,
original handles and complete final verification all remain. Prospective tighter
QD watermarks are45/53/55 seconds from the same caller origin; equality refuses.
They reserve time rather than guarantee completion and add no time or new origin.
The original full-Q child55-second boundary remains unchanged for later Q.

The [timing diagnosis](../../runs/coordination/cho51_p3_probe_20261101_q4/closeout-refusal.json)
found that the latest suite began43.2992148 seconds after caller origin, versus
32.0767484 and33.3629039 in earlier accepted runs. The observed supervisor-to-suite
span grew to25.8938825 seconds. These generation intervals motivate the selected
prefix; they do not establish CPU/cache/I/O causality or a future upper bound.
More instrumentation itself has unmeasured cost. The design promises no fit.

There are36 planned acceptance scenarios, all unimplemented and unexecuted.
Source review, pure/injected qualification and actual native closure/fault checks
remain distinct. A first separately admitted QD investigation may establish only
its diagnostic prefix and owned lifecycle; it cannot certify its own unexecuted
adversarial qualification cases or advance beyond Q. A later full-Q successor
still needs exact probe32,100 and384 rosters, every required control, full final
verification and separate actual acceptance.

## Next step and preserved project state

Next is implementation and independent source review of the QD-only diagnostic,
including the native append/close state machine, early-initialization cleanup,
all original guard mappings, exact source/runtime closure and complete output
ledger. Only then may Root separately assess a fresh diagnostic-only admission.
Full Q remains held until a distinct reviewed successor has an evidence-based
complete-stage budget with margin. No unchanged-source retry or automatic
transition follows design or diagnostic acceptance. P stays disabled.

The [supplied-byte probe](cho51_p3_probe_implementation_20261101.md) remains
source-reviewed but unqualified: six attempts consumed, latest32 method passes,
three sharing passes and six exact artifacts provisional. The two new UNKNOWN
caller-custody outcomes8bf386d1 and6f9c898c, and earlier131bc595 UNKNOWN, remain
unchanged. A later closed operation cannot repair them.

All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,
1,786 binding loads and3,972 effects remain open. Complete continuation still
requires at least31,002 rows against24,000 and is INFEASIBLE_UNDER_CURRENT_GUARDS;
conditional node/raw-byte findings retain their scope. G2 is INCOMPLETE_REFUSED.
Bootstrap004 is consumed, diagnostics005 held, historical custody UNRESOLVED
and006 unadmitted. Candidate117/V34 and science are unexecuted; scientific cells
remain0/1020 and the freeze unsigned. No original-package-path custody, continued
state, obligation discharge, commit or push is established by this step.

The [pre-step archive](../history/startup_timing_design_20261101/manifest.json)
holds12 exact active documents. The preservation baseline covers8,323 frozen
files, including the probe sources, actual results and refusal closeout. File,
text, JSON and hash inspection is the only validation performed in this design
step; documentation does not refresh P census or custody.
