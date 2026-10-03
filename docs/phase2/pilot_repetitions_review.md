# Pilot repetitions and per-case cost summary

19 September 2026, milestone 39. The pilot specification's repetition
requirement is satisfied for the primary tranche: one cold repetition
(milestone 38) plus two warm-cache repetitions, with every repetition, its
median and its maximum reported — never only the fastest run. All
measurements remain engineering computation records under the documented
below-floor deviation; no scientific cell was published.

## Three-repetition summary (case totals, seconds)

| Method | Rep 1 (cold) | Rep 2 | Rep 3 | Median | Maximum |
| --- | --- | --- | --- | --- | --- |
| labram_linear | 40.7 | 46.6 | 54.5 | 46.6 | 54.5 |
| labram_full | 47.6 | 50.1 | 71.8 | 50.1 | 71.8 |
| labram_lora | 39.4 | 42.1 | 56.0 | 42.1 | 56.0 |
| eegnet | 17.5 | 18.2 | 21.4 | 18.2 | 21.4 |
| ea_tangent_lr | 248.0 | 357.9 | 300.1 | 300.1 | 357.9 |

Reading: the neural methods cluster at a 39-72 s per case with visible
warm-up spread (rep 3 ran while the machine was under the quality suite's
residual load); EA-tangent varies 248-358 s because its classical 51-source
refit is CPU-bound and competes with background load. The maximum, not the
median, is the conservative envelope input the specification asks for. At
these bounded settings, the full primary tranche (five methods × three
repetitions = fifteen measured cases) completes in roughly 25 minutes of
wall time; scaling first estimates for the scientific grid (52 targets × 5
methods × 5 seeds) fall in the tens of hours on this CPU-only path — the
exact figure awaits the remaining matrix and the source-cost probes.

## Evidence

Each repetition claimed its case atomically and wrote an immutable
engineering record with per-stage timings; the admission snapshot again
carries the honestly failing storage check under the recorded deviation.
The session receipt reports all ten warm measurements (five methods × two
repetitions) alongside the milestone-38 cold run. The exact-source quality
bundle re-passed (unchanged source): **558 tests / 921 subtests** with lint
and strict types. Evidence directory:
`runs/phase2/pilot_repetitions/20260919_step39/`. Current source fingerprint
(unchanged): `74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9`.

## Next work

The remaining pilot matrix (one/twenty-shot extremes, the BCI and MMIDB
development targets, TCPL and the remaining LaBraM methods), the
source-cost throughput probes (two warm-up plus three measured twenty-step
blocks per the specification), and then the scientific freeze of candidate
counts and budgets that these measurements inform. Gate A remains unsigned;
nothing is committed or pushed; the RAM-deferred control refresh still gates
commits.
