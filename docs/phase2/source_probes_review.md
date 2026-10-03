# Source-cost throughput probes

19 September 2026, milestone 43. The pilot specification's neural source-cost
probes are complete: for each of the six LaBraM methods, two warm-up
gradient steps followed by three blocks of twenty measured steps on one
fixed class-balanced eight-trial audited batch, on both the Cho2017 and BCI
worlds (twelve probes, sixty measured steps each, all inside the 100-step
cap). These are throughput measurements, not converged fits; they give the
per-step costs that convert the bounded-settings envelope into
scientific-settings forecasts once step counts freeze.

## Per-step costs (median seconds per gradient step)

| Method | Cho2017 | BCI IV 2a |
| --- | --- | --- |
| labram_linear | 0.221 | 0.061 |
| labram_adapter | 0.227 | 0.062 |
| labram_lora | 0.263 | 0.067 |
| labram_partial | 0.302 | 0.082 |
| labram_full | 0.778 | 0.212 |
| labram_support_prompt | 0.839 | 0.278 |

Reading: the per-step ordering is stable across datasets. Frozen-backbone
component methods (linear, adapter, LoRA) cluster at ~0.22 s on Cho and
~0.06 s on BCI; partial tuning costs ~37% more; full tuning and the
support-prompt episode (which re-encodes support features every call) cost
3-4× the linear probe. The Cho/BCI ratio (~3.4×) reflects input width
(64 vs 22 channels). Per-step maxima stayed within ~1.15× of medians —
stable throughput, no drift across blocks.

## The forecast key

With per-step costs measured, the scientific envelope is now a
multiplication away: a converged scientific fit at, say, 50 steps × 51
Cho sources ≈ 50 × 51 × per-step — e.g. linear ≈ 9.4 min, LoRA ≈ 11.2 min,
prompt ≈ 35.7 min per fit. Every earlier per-case measurement
(milestones 38-42) is explained by these numbers plus the fixed
episode-loading overhead, closing the loop between the case envelope and
its components. The freeze can now be costed precisely for any candidate
step count.

## Evidence

Each probe records per-step mean/median/min/max, per-block medians, the
class-balanced batch's exact trial IDs, trainable-name samples and measured
step counts, on the unchanged source. The probe script and its receipt are
under `runs/phase2/source_probes/20260919_step43/`; the exact-source
quality bundle re-passed at **558 tests / 921 subtests** with lint and
strict types (fingerprint unchanged:
`37dbc5e91a1581b56d7c59f46112f3939a6403646c32503c6a46f54c7e939d24`).
No source file changed this milestone. Gate A remains unsigned; nothing is
committed or pushed; the RAM-deferred control refresh still gates commits.

## Next work

The scientific freeze preparation now has every measured input the
specification requires from the pilot: per-case envelopes (three datasets),
per-step source costs, shot-flatness and the MMIDB episode-eligibility
policy question. The freeze itself — candidate counts, stopping rules,
budgets — is the owner's scientific-contract act on these numbers, together
with the register's open items.
