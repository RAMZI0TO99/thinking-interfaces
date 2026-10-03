# Pilot MMIDB cases and the episode-eligibility finding

19 September 2026, milestone 42. The pilot's third dataset produced a
structural finding instead of a full case matrix — exactly what a pilot
exists to surface before the scientific run. EA-tangent measured on the full
audited MMIDB cohort; every episode-bound method (the six LaBraM paths,
EEGNet, TCPL) is blocked by a genuine cohort-policy gap that is a scientific
contract decision, not an engineering defect. Two real code gaps were also
found and fixed: the cohort helper's subject-name width (two-digit padding
broke MMIDB's three-digit names) and the LaBraM manifest runner's missing
MMIDB asset dispatch.

## The structural finding

The audit's source selection includes all 108 non-target MMIDB subjects —
including 079 and 100, which are target-ineligible but "can remain source
subjects under the explicit source-cohort policy." However, no audited
episode records exist for those two subjects, and none can exist: their
retained trial counts cannot supply the twenty-shot support pool plus a
query for every class. Episode-bound methods (everything whose source fit
consumes audited nested episodes) therefore cannot train on them — by
necessity, not by choice.

The admission guards correctly refuse every workaround: a 107-subject
catalog fails the never-silently-pruned completeness check, and the full
109-catalog world fails episode construction on 079/100. Resolving this
requires an explicit episode-eligible source-cohort policy — a scientific
contract amendment in the D02/D03 domain (e.g., "episode-bound methods use
the episode-eligible subset; the exclusion matches the audit's own
ineligability record"). That is an owner-level scientific-contract decision
this project's discipline forbids an agent from making silently, per the
milestone-37 decision resolution.

## What measured

EA-tangent needs no episodes (its classical refit consumes Profile A
directly) and measured cleanly over the full audited cohort: **125.6 s**
(one-shot) and **154.1 s** (twenty-shot) — the 108-source refit again
dominating, and shot-flatness holding. Combined with the earlier findings,
EA's cost scaling is now measured at three cohort sizes: 7 sources → 11 s,
51 → 248–369 s, 108 → 126–154 s (the sub-linear jump reflects MMIDB's much
smaller per-subject trial counts).

## Code fixes landed (both genuine gaps)

- `dataset_cohort` now derives subject-name width from the declared roster
  size (three-digit names for 100+ subjects); BCI and Cho behavior is
  unchanged and their suites pass unmodified.
- The LaBraM manifest runner now accepts `MMIDBProfileAssets` and dispatches
  to the MMIDB episode loader; the BCI and Cho paths are unchanged.

## Evidence

Sessions under `runs/phase2/pilot_mmidb_checks/20260919_step42/`: two
MMIDB sessions with every case's honest outcome recorded (EA measured with
immutable engineering records; the episode-bound methods' refusals recorded
as failure records with the exact guard messages), the derived runner, and
the quality bundle. The exact-source suite re-passed with the two fixes:
**558 tests / 921 subtests**, lint and strict types. Gate A remains
unsigned; nothing is committed or pushed.

## Next work

The episode-eligible cohort policy question goes to the owner alongside the
existing register items; with a decision, the eight blocked methods run
immediately. Independently of that decision, the source-cost throughput
probes (two warm-up plus three measured twenty-step blocks) can run on the
already-covered Cho and BCI worlds, and the scientific freeze preparation
continues from the measured envelope.
