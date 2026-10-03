# First measured pilot session

19 September 2026, milestone 38. Following the user's instruction "ok do it
and then keep moving" — recorded as pilot compute admission plus a documented
below-floor disk deviation — the first measured pilot session executed all
five primary-tranche methods on the real Cho2017 cohort at the primary
five-shot configuration. Every case was claimed atomically, measured with
per-stage wall timings, and recorded as an engineering measurement record.
**No scientific cell was published**: provisional one-step weights produce
engineering records only, per the pilot specification.

## Operating mode

The executor's machine guard is unchanged and honestly failing: the admission
record carries the live snapshot with `storage_ok: false` (17.59 GiB free
against the unchanged 20 GiB floor). The user's explicit authorization is
recorded in the deviation log and decision register as the operating-mode
deviation the handoff allows — CPU-only bounded execution with small record
writes (this session wrote under 1 MB of records), no cohort reduction, no
deletion, and the session cap (two hours) and probe cap (ten minutes)
unchanged. GPU capacity passes and was not used; all runners are CPU-bound by
construction.

## Measurements

Target: Cho2017 `subject_01` (the pilot specification's development target),
five shots per class, model seed 23, one repetition, all 160 fixed common
queries predicted per case. Source fits are provisional single-candidate
one-step-per-subject fits over all 51 permitted sources (engineering
settings; not converged and not scientific defaults).

| Method | Source fit (s) | Target support+query (s) | Case total (s) | Queries |
| --- | --- | --- | --- | --- |
| labram_linear | 35.8 | 4.9 | 40.7 | 160 |
| labram_full | 41.9 | 5.7 | 47.6 | 160 |
| labram_lora | 34.0 | 5.4 | 39.4 | 160 |
| eegnet | 16.9 | 0.6 | 17.5 | 160 |
| ea_tangent_lr | — (classical refit inside the target stage) | 248.0 | 248.0 | 160 |

Reading: the three LaBraM neural methods cost ~35-48 s per case at this
bounded configuration, dominated by the 51-subject source fit (each subject:
episode load with hash verification plus one gradient step). EEGNet is
cheapest at 17.5 s. EA-tangent's 248 s includes its per-prediction classical
refit over all 51 source subjects (alignment + OAS covariance + tangent
logistic per fold), which the anchor contract performs inside the target
stage — consistent with its milestone-19+ design. Every case stayed far
inside the ten-minute probe cap, and the whole session (five cases plus
setup) ran well inside the two-hour session cap.

These are computation measurements, not accuracy results: the confusion
matrices recorded alongside the timings come from one-step provisional
weights and carry no performance meaning. They are the first inputs for the
scientific envelope forecast the pilot exists to produce.

## What this unblocks

With per-case costs measured for the primary tranche, the remaining pilot
work is repetition (the specification asks for three measured repetitions
after warm-up), the remaining 54-case matrix (one/twenty shots, BCI and
MMIDB development targets, TCPL and the remaining methods), and the
source-cost throughput probes — followed by the freeze of candidate counts
and budgets that the scientific E2 execution requires. Each next session
reuses this runner with a wider `--methods`/`--shots` roster.

## Verification

The session ran on the unchanged source (no source/config/test file changed
this milestone); the exact-source quality bundle was re-run and passes **558
tests / 921 subtests** with lint and strict types. Evidence directory:
`runs/phase2/pilot_session_checks/20260919_step38/` — the runner, the session
log, per-case engineering records under `session1/`, and the session receipt
with the failing-storage admission snapshot. Current source fingerprint
(unchanged): `74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9`.

## Unchanged limits

Gate A remains unsigned (milestone-37 decision); provisional weights produced
no scientific cell; the RAM-deferred control refresh still gates commits; and
nothing is pushed. P2 remains partial; P3 is now *in measured execution*
under the documented deviation, not yet complete.
