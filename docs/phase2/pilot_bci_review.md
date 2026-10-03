# Pilot BCI development-target cases

19 September 2026, milestone 41. The pilot's BCI coverage is complete: all
nine roster methods measured at both shot extremes on the nine-subject BCI
world (eight permitted sources, 22-channel four-class inputs, 496-query
pools) — 18 measured cases, every one inside the probe cap. Together with
milestones 38-40, 55 of the pilot's cases are now measured. All measurements
are engineering computation records under the documented below-floor
deviation; no scientific cell was published.

## Case totals (seconds)

| Method | 1 shot | 20 shots |
| --- | --- | --- |
| eegnet | 4.6 | 4.7 |
| ea_tangent_lr | 11.0 | 11.3 |
| labram_partial | 15.8 | 17.4 |
| labram_adapter | 16.4 | 17.6 |
| labram_lora | 16.5 | 17.5 |
| labram_linear | 18.3 | 19.5 |
| labram_support_prompt | 18.3 | 22.8 |
| tcpl | 21.9 | 21.7 |
| labram_full | 28.6 | 32.5 |

Reading: BCI cases cost roughly a third of their Cho counterparts across the
board — the eight-source cohort makes the dominant stage (source fitting)
cheap, and even the 496-query pools (3× Cho's 160) do not offset that. The
shot-flatness finding from milestone 40 replicates exactly on BCI (every
method within ~1-4 s between 1 and 20 shots). EA-tangent inverts its Cho
position: with only seven sources to refit classically it becomes the
second-cheapest method (11 s) instead of the most expensive (358 s) —
confirming that its cost scales with the source cohort, not with shots or
queries.

The three-dataset envelope picture is now two-thirds complete: BCI 4.6-32.5 s
per case, Cho 18-369 s per case, with only the MMIDB development target
remaining (109 sources — expected to exceed Cho's source-fit costs, with the
smallest query pools of the three).

## Evidence

Every case claimed atomically; immutable engineering records with per-stage
timings under `session_bci1/` and `session_bci20/`; the admission snapshot
again carries the honestly failing storage check (15.56 GiB free at session
start — the deviation remains necessary and recorded). The exact-source
quality bundle re-passed (unchanged source): **558 tests / 921 subtests**.
Evidence directory: `runs/phase2/pilot_bci_checks/20260919_step41/`. Current
source fingerprint (unchanged):
`74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9`.

## Next work

The MMIDB development-target cases (the last third of the pilot matrix),
then the source-cost throughput probes, then the scientific freeze of
candidate counts and budgets. Gate A remains unsigned; nothing is committed
or pushed; the RAM-deferred control refresh still gates commits.
