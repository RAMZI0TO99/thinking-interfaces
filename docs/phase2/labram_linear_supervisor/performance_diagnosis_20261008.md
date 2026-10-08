# LaBraM engineering performance diagnosis, 8 October 2026

The next operational checkpoint passed15 source-scope/cleanup checks and36
hardened feature checks. Exact selector evidence/model/RNG, fit/fold progress,
state restoration and global-hook callbacks were verified. Actual deadline and
local-stop fixtures proved owned Job release and registered-file cleanup. An
initial uncaught sensor failure remains preserved with separate later recovery;
the fixed guard saves failure evidence and performs cleanup. Root's160-check
self-review admits engineering/release evidence only. The hardened real source
no-fit trace again preserved exact logits/state/RNG. Next is a complete source
query-batch no-fit trace, rather than inferring full-case runtime from two small
representative batches. Frozen production and both spent attempts are unchanged.

The next feature checkpoint is now executed. A bounded32MiB feature prototype
passed35 synthetic input/disk/feature checks, including exact original linear/
full/LoRA selector model/history/evidence/RNG, invalidation and scope cleanup.
Pinned real source-only forwards averaged81.337ms original versus1.269ms cached
for batch2 and353.340ms versus2.068ms for batch8. Both first misses and22 hits/
copy reuses had bitwise logits, unchanged model/RNG and final cleanup. Whole-
model state hashing measured about12ms per call. The169-check root self-review
accepts diagnostic/resource-release evidence only. Production remains frozen;
no real training, target inputs, accuracy or new case attempt occurred. Continue
with operational integration/progress and interruption handling. The earlier
checkpoints below are retained; sampled forward speed does not establish a
complete selector's runtime.

Later cache work executed the proposed full-roster loading trace and validated
a [private file-cache prototype](../cho_b_disk_cache/README.md). The original
two loading orders produced100 misses/88 evictions in105.4028s. Exact prototype
orders took65.6483s, followed by a fully warmed50-subject order in0.5370s.
Twenty-three fixture checks and the145-check root milestone review passed;
these are engineering self-reviews. A pinned source-only encoder diagnostic
measured batch2 about0.09s and batch8 about0.36-0.40s, with unchanged model/RNG
and exact frozen-feature/head logits on those batches. A feature-reuse prototype
is the next work. Production remains frozen; the analysis below preserves the
earlier checkpoint. No accepted LaBraM case or scientific approval is inferred.

The prerequisite pipeline passed, but the first LaBraM engineering case has
no accepted result. This document records the two actual attempts and the
performance work needed next. It is a root self-review and implementation
plan; it signs neither scientific Gate A nor the experiment freeze.

## Executed evidence

The case is Cho2017 / LaBraM linear / subject_01 / seed11 / five shots /
repetition1. Canonical source remained `b7452847` across431 files. The latest
attempt used clean Git `8092860`, actual CPU/Torch1/deterministic environment
`1bc12a28`, unchanged data/checkpoint/candidate identities, and480/520/600-second
attempt/session/native bounds with6GiB process and7.5GiB aggregate caps.

| Evidence | Actual outcome | Limit on interpretation |
|---|---|---|
| Full45 controls | 45/45; accepted different-reviewer audit | Engineering control evidence |
| Fresh full36 | 36/36; mean0.2450810185 below0.35 | Root execution self-review |
| Immutable all9 writer | All9 verified; stdout matches36 context | Original raw recomputation/check |
| Raw52 | 52 sources;1040 planned identities;10,704,036,837 raw bytes | No model fits |
| LaBraM attempt1 | Allocation of39.1MiB failed; native exit1 at117.692s | Outer measured aggregate exceeded7.5GiB; no cell |
| Cache mitigation validation | 16 existing tests passed under512MiB policy | Exact model/history/evidence/RNG fixture equivalence; no real-case score |
| Final environment2 | Native exit0 at11.520s | Environment preparation only |
| LaBraM attempt2 | Attempt deadline; session480.109s; native exit1 at500.383s | Zero completed cases and accepted cells |
| No-fit source-loader benchmark | Native exit0 at18.087s; exact arrays/binding equality across3 stages | One source subject; no model, training or case claim |

Attempt2's outer Job peak was6,580,506,624 bytes and process peak3,762,991,104
bytes. The inner Job separately measured3,776,118,784 bytes. These measured
peaks stayed within their limits before termination. No allocation exception
was recorded in attempt2; completion of the full workload under the caps is
unproven. Real engineering training was invoked, but completed fit count is
unknown. The zero formal scientific fit count is not a count of engineering
work already performed.

The parent completion records an empty/closed private Job, closed process/thread
handles and no cleanup errors. Eight known case/environment PIDs were freshly
absent. Failed native candidate cleanupFalse remains preserved. Successful
runtime source-after/operations checks were not completed on the failure path;
a later separate observation verified unchanged source, clean execution Git,
operation files,33 selected runtime files and the quality pointer. The root
closeout observation passed103 checks and admits failure/resource-release
evidence only. Both recorder claims/failures remain immutable. The existing
maximum of two attempts is exhausted; no third attempt is available in this
case ledger.

## What the current implementation does

`adaptation/labram_source.py` runs every declared candidate against every inner
source-validation fold, then fits the selected candidate on all permitted
sources. For this52-subject cohort, the target is excluded:51 source subjects,
two candidates,51 inner folds per candidate,50 source steps and one support
step per fold, then51 final source steps. That is the declared **5253 selection
gradient-step ceiling**, rather than the historical256 smoke ceiling. These
are planned operations, not a measured completed-step count for attempt2.

`evaluation/phase2_cho_b_input_snapshot.py` keeps a per-selector LRU of immutable
maximum-shot source episodes, retaining file identity pins after eviction.
The retry bootstrap reduced its supported retained-byte limit from2GiB to
512MiB. It changed no frozen implementation or scientific setting. The cache
uses the original verified loader on misses. That loader reads and validates
Profile A/B arrays, checks raw provenance, copies support/query arrays and
checks hashes again. Selection also copies models, clones frozen state, runs
the encoder and optimizes the head. Successful cache reduction therefore does
not establish which operation dominates runtime.

Read-only ZIP central-directory inspection found52 versioned Profile B files;
the51 non-target `signals.npy` payloads total **1.968389869GiB**, including NPY
headers. Individual payloads range39.063 to46.875MiB. This exceeds512MiB, so the
cache cannot retain all full source signals simultaneously. These header sizes
are not exact retained-episode byte counts. Repeated eviction/reloading is a
plausible bottleneck under the ordered full-cohort iteration, but no actual
miss count, load duration, encoder duration or completed-fold count was saved.
The deadline alone cannot distinguish loader cost from model computation.

## Executed loader diagnostic

A new operational benchmark used the original52-subject route preparation,
excluded subject01 from the source cache and timed subject02 under the512MiB
cache policy. It constructed no model, invoked no training and made no recorder
claim. The original loader returns were preserved; wrappers timed original
function calls, then restored them. Array hashes and binding objects matched
exactly across all three stages. Final unconditional touched-file verification
and source/Git-before/after comparison passed.

| Stage | Actual elapsed | Artifact decodes | Loader file-digest calls |
|---|---:|---:|---:|
| First load | 1.074757s | 2 | 16 |
| Cache hit | 0.0046535s | 0 | 0 |
| Reload after explicit cache clear | 0.903456s | 2 | 16 |

Route preparation took10.203440s and final touched-file verification0.196943s.
The episode retained40,756,792 bytes. Decode timing was0.303/0.305s and
loader file-digest timing0.384/0.385s for first/reload stages. Timing categories
can overlap and must not be summed. Array hashing occurred outside the timed
`snapshot.load` call. Cache hits still perform the original configuration and
file-metadata checks; zero loader digest calls does not mean provenance checks
were skipped.

The diagnostic's private Job had180 seconds and native guard200 seconds.
Actual guarded elapsed17.899s/native18.087s, normal exit0, no watchdog kill,
aggregate peak2,729,717,760 bytes (2.542GiB). Job/owned handles closed, both
known native/Job PIDs were freshly absent and the temporary awake request was
reset. The17-check root acceptance is explicitly self-review. The saved Git
dirty flag is true because milestone documentation was being edited; canonical
source remained unchanged. This diagnostic did not spend another case attempt.

This confirms that a cache hit is much cheaper than reloading this subject.
It supports measuring actual full-roster misses before optimizing the loader.
It does not establish full-case runtime, completed fold count, model cost or
that a particular optimization will meet the480-second cap.

## Next implementation work

1. Prepare new operational progress instrumentation around loader entry/return,
   cache hit/miss/eviction, model copy, source fit, support adaptation, query
   prediction and fold completion. Emit bounded, flushed timing/counter records
   with source/operation/input identities and monotonic elapsed time, without
   signal arrays, predictions or target-query access. Validate wrappers on
   fixtures before any real-data timing operation. Instrumentation must preserve
   return values, exception behavior, argument order, RNG and model state.
2. Extend the completed one-source diagnostic to a bounded source-only LRU
   workload with actual hit/miss/eviction counts. Its one-subject reload after
   explicit clear is not an observed full-roster eviction trace. Keep explicit
   process/aggregate caps, resource floors and physical cleanup; avoid model fits
   or recorder claims during this measurement.
3. Select an optimization from measured costs. Potential directions include
   reducing transient array copies, retaining only source inputs actually needed
   for training, or using frozen-encoder features for the linear route. Each needs
   a design review for source-only isolation, exact trial identities, numerical
   precision/order, cache lifetime, byte budgets, tamper checks and RNG behavior.
   No direction is implemented or claimed equivalent by this static review.
4. Coordinate ownership before editing frozen production files. Preserve other
   edits, raw data, weights, all attempted-case artifacts and the historical
   EEGNet79/160 cell. Validate exact cached/uncached model state, losses, selection
   evidence, predictions, rational metrics, RNG, eviction and tamper behavior on
   meaningful fixtures. A changed canonical source requires a fresh matching
   quality pass and source-bound controls/prerequisites.
5. Review recorder recovery and a new bounded engineering phase explicitly
   before another real case. Do not clear spent claims, invent attempt3, relabel
   the same case, reduce the cohort/candidates, enlarge caps or infer scientific
   approval to obtain a passing score. Direct user authorization permits
   independent engineering preparation; shared-machine coordination responds to
   actual peer resource needs.

## Local evidence references

The runtime evidence is intentionally excluded from Git; these paths refer to
the workspace receipts, not files distributed with the repository.

- [Final environment acceptance](../../../runs/coordination/session_20261008_resume/environment_cache_bound_root_acceptance_002.json)
- [Actual case2 inner receipt](../../../runs/phase2/sweeps/labaut10_002.session/case_0001/receipt.json)
- [Actual case2 native receipt](../../../runs/phase2/first_case_supervision_launches/labaut10_002/receipt.json)
- [Actual case2 parent completion](../../../runs/phase2/first_case_supervision/labaut10_002/completion.json)
- [Fresh103-check closeout observation](../../../runs/coordination/session_20261008_resume/labram_attempt2_fresh_closeout_observation_001.json)
- [Root deadline failure review](../../../runs/coordination/session_20261008_resume/labram_attempt2_deadline_root_review_001.json)
- [Explicit scope release](../../../runs/coordination/session_20261008_resume/labram_autonomous_case_scope_release_002.json)
- [Read-only ZIP header observation002](../../../runs/coordination/session_20261008_resume/cho_b_zip_header_observation_002.json)
- [Actual no-fit loader benchmark](../../../runs/coordination/session_20261008_resume/cho_source_loader_benchmark_result_001.json)
- [Loader diagnostic private Job witness](../../../runs/coordination/session_20261008_resume/source_loader_diagnostic_guard_001.json)
- [Loader diagnostic native exit](../../../runs/coordination/session_20261008_resume/source_loader_diagnostic_native_exit_001.json)
- [17-check benchmark root acceptance](../../../runs/coordination/session_20261008_resume/source_loader_diagnostic_root_acceptance_001.json)

The invalid PowerShell aggregation in header observation001 is retained and
superseded by002. Its null total is not used in this diagnosis. Historical
passing receipts certify only their recorded source/operations and review scope.
