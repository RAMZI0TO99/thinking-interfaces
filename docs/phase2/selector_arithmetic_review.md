# Selector cohort arithmetic repair

19 September 2026, milestone 47. The owner's "next step" authorizes the
bounded repair of the actual defects identified at milestone 46. The
production change is confined to three selector files; every constructor
ceiling, resource check, fit algorithm, split, seed and scientific choice
is retained. The full Cho scientific selection is still not admitted.

## What changed and why

- LaBraM now divides each candidate's sum by its actual inner-fold count.
  BCI still divides by eight; a 51-fold Cho mean now divides by 51. The
  former shared positive divisor did not change ranking within one run,
  but it mislabeled the reported mean. No historical score is rewritten.
- EEGNet counts a diagnostic fold as (sources - 1) x source steps plus
  support steps. Complete selection sums this work over every inner fold
  and candidate, then reserves all source subjects x the largest candidate
  source-step budget for the fresh final fit. Reservation is made before
  fitting, independently of which candidate wins.
- EA counts candidates x actual inner folds. It has no separate final
  source fit; the target recipe refit remains a separate future operation.
- New EEGNet/EA contracts name the actual dataset. All three source-policy
  labels describe all permitted non-target subjects rather than claiming
  eight for every dataset. Corresponding stale cohort docstrings are
  corrected. Numeric BCI behavior and dataset eligibility are unchanged.

For the proposed two-candidate/one-step Cho selection, LaBraM and EEGNet
request 5,253 steps before target adaptation; both exceed the unchanged
256-step ceiling. TCPL remains unchanged at 5,151 steps and is also
blocked. EA requires 102 inner fits: 101 refuses before fitting and 102 is
the exact arithmetic boundary. That boundary alone grants no compute
admission, scientific ratification or authorization to launch the fits.

## Verification and discriminators

Before production edits, the new checks failed on the old implementation
with seven failed outcomes (including metadata subtests), while the BCI
boundary check passed. The failed log is preserved as `before_fix_tests.log`.
The LaBraM regression recomputes the candidate mean independently from
actual confusion matrices in the existing three-subject synthetic Cho
integration test; simply retaining the winning candidate cannot satisfy it.

Six new tests exercise unreadable synthetic artifact placeholders and real
selector admission. They check full Cho refusal before any fold/final fit;
the 50/51-step single-fold boundary; a small cohort with mixed candidate
budgets, counting 16 actual work units including the larger winner's final
fit; the EA 101/102-fit boundary and declared-order ties; unchanged BCI
135/136-step and 16-fit behavior; and dataset metadata plus rejection of
0, 257 and boolean ceilings. Permitted fold work is stubbed for arithmetic
tests; those stubs are not scientific fits.

Focused checks pass **10 tests / 4 subtests**. The required full quality
bundle's final result is recorded in this milestone's receipt. Full BCI
regressions remain part of that bundle; no test or tolerance was relaxed.

The separate real-data check rebuilt all 52 Cho catalogs from Profile A
and reconstructed their saved audited episode envelopes, verified the
real outer-target source-selection record, hashed all Profile A/Profile B
inputs and Profile B manifests before and after the check, and initialized
LaBraM from the pinned safe checkpoint. Actual selectors requested
LaBraM=5,253, EEGNet=5,253 and EA=102 and refused before fitting at limits
256, 256 and 101 respectively. Caller model state was preserved.
**Zero real-data source steps, target predictions or scientific cells**
were produced. This validates admission, not a completed Cho selection
or a fresh raw-preprocessing/binding audit.

## Scope, provenance and remaining work

Adopted execution decisions are logged as deviations: repair the cohort
arithmetic and truthful metadata; retain every cap; use before-fit refusal
as the real-data discriminator; and leave complete scientific selection
unadmitted. No model-setting, candidate-budget, MMIDB policy, Gate A,
freeze, commit or push decision is made for the owner.

Source fingerprint: `1e79dfc779b0cf616243c3e33f2f8a0893397bf41e02ebdf36b0e29e7bdf05f9`.
Historical quality and controls do not certify this changed source. The
fresh quality bundle is required here; the separate RAM-dependent 45-fit
control refresh stays deferred and continues to gate a checked commit.

Evidence: `runs/phase2/selector_arithmetic_checks/20260919_step47/`, including
baseline source/doc snapshots; saved code diffs; failing and passing
focused logs; `real_admission_check.py` and its receipt; full quality
logs/status; and final `receipt.json` / `documentation_receipt.json`.
An initial edit helper assumed CRLF and asserted before writing any file;
the preserved note records its retry using actual line endings.

Frozen Phase I records, the H2 margin, original artifacts, earlier
milestone evidence and append-only documentation history are preserved.
The corrected working draft and current status distinguish these repaired
defects from the remaining 256-step execution limit, unratified scientific
settings, incomplete full resource envelope, committed-configuration
prerequisite and owner decisions. No private-helper workaround, cap
increase, scientific experiment, control refresh, commit or push occurred.

Finalization incident: the first finalizer assumed UTF-8 for PowerShell
logs that carry UTF-16 BOMs and stopped before publishing receipts. Its
script/log are retained; `finalize_evidence_v2.py` reads the declared BOM
without changing assertions or evidence. Source and passing quality remain
unchanged.
