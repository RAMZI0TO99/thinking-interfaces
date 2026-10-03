# Pilot matrix: full roster and shot extremes on Cho2017

19 September 2026, milestone 40. The pilot's Cho2017 coverage is complete:
all nine roster methods measured at the primary five-shot configuration, and
the full nine-method matrix at both shot extremes (one and twenty shots) —
23 measured cases on this dataset, every one inside the probe cap. All
measurements are engineering computation records under the documented
below-floor deviation; no scientific cell was published.

## Full-roster primary configuration (five shots, case totals)

| Method | Source fit (s) | Target (s) | Case total (s) |
| --- | --- | --- | --- |
| labram_linear | 35.8 | 4.9 | 40.7 |
| labram_full | 41.9 | 5.7 | 47.6 |
| labram_partial | 49.1 | 11.4 | 60.5 |
| labram_lora | 34.0 | 5.4 | 39.4 |
| labram_adapter | 44.0 | 11.7 | 55.7 |
| labram_support_prompt | 58.7 | 13.4 | 72.1 |
| tcpl | 41.4 | 4.0 | 45.4 |
| eegnet | 16.9 | 0.6 | 17.5 |
| ea_tangent_lr | — | 248.0 | 248.0 |

## Shot extremes (case totals, seconds)

| Method | 1 shot | 20 shots |
| --- | --- | --- |
| labram_linear | 56.7 | 54.5 |
| labram_full | 71.5 | 78.7 |
| labram_partial | 54.7 | 58.4 |
| labram_lora | 54.0 | 51.1 |
| labram_adapter | 76.6 | 56.2 |
| labram_support_prompt | 70.2 | 73.2 |
| tcpl | 45.9 | 45.6 |
| eegnet | 20.9 | 20.7 |
| ea_tangent_lr | 359.4 | 369.0 |

Reading: the shot level barely moves case cost — the source fit (51 subjects)
dominates and is shot-independent, and the target stage's support-size
variation (2 vs 40 trials) is small next to the fixed 160-query inference.
This is the most important envelope fact so far: **per-case cost is
approximately flat in shots**, so the scientific grid's cost scales with
targets × methods × seeds, not with the shot axis. The run-to-run spread
(visible between the extremes and the earlier repetitions, e.g. linear
40.7-56.7 s) reflects background load rather than shot effects.

Combined with milestone 39's medians, the per-case envelope on this
CPU-only path is: neural methods 39-79 s, TCPL ~46 s, EEGNet ~18-21 s,
EA-tangent 248-369 s. A full Cho five-shot scientific tranche (52 targets ×
5 methods × 5 seeds) at these bounded settings extrapolates to roughly 15-25
hours — the converged scientific settings will add source-fit steps, so the
scientific freeze must scale these numbers by the measured per-step source
costs from the remaining throughput probes.

## Evidence

Every case claimed atomically; immutable engineering records with per-stage
timings under `session_roster/`, `session_shots1/` and `session_shots20/`;
the admission snapshot carries the honestly failing storage check. The
exact-source quality bundle re-passed (unchanged source): **558 tests / 921
subtests**. Evidence directory: `runs/phase2/pilot_matrix_checks/20260919_step40/`.
Current source fingerprint (unchanged):
`74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9`.

## Next work

The BCI and MMIDB development targets (the remaining two-thirds of the
pilot's 59-case matrix), the source-cost throughput probes (two warm-up plus
three measured twenty-step blocks per the specification), and then the
scientific freeze. Gate A remains unsigned; nothing is committed or pushed;
the RAM-deferred control refresh still gates commits.
