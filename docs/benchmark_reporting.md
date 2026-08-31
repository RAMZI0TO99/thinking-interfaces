# Reading and regenerating the benchmark

The frozen primary table and diagnostic companion join on `dataset,method`.
Both use one independently audited snapshot of the exact source files. New runs
appearing during export do not change that snapshot; changed files abort export.
`runs/benchmark_status.json` records completeness, source fingerprint, and both
CSV file hashes. Incomplete tables are explicitly partial, not final deliverables.

Run `scripts/aggregate_benchmark.py` for both tables and
`scripts/regenerate_figures.py` for the figures. All scripts use the project-local
Python environment. The figure manifest records its own source fingerprint and
image hashes. Final completion requires table and figure snapshots to match the
complete current benchmark, not merely for the files to exist.

## Primary table

`runs/benchmark_table.csv` reports balanced accuracy averaged first across seeds
within subjects. `standard_deviation` is between-subject SD; the interval uses
subjects, never individual trials. `seed_mean_standard_deviation` is separate:
it measures variation of dataset means across seeds. Partial-grid comparisons
use only subjects shared across observed seeds and expose that count.

## Diagnostic companion

`runs/benchmark_diagnostics.csv` reports subject-weighted mean kappa, expected
calibration error, and coverage at the frozen 0.70 confidence threshold.
Selective accuracy is conditional on nonempty coverage: blank means unavailable,
not zero; contributing subject and record counts are included.

Class totals and confusion matrices pool all recorded query evaluations,
**including repeated seeds**. They describe scoring balance and errors, not an
independent sample size. Class order is included explicitly. The accuracy figures
show per-method pooled class percentages, subjects, and record counts.

Computed and reused records are distinguished. Deterministic seed copies add no
measured training time and are excluded from the denominator of amortized batch
prediction time. Batch prediction time per trial is **not** online end-to-end
latency; the real-time CPU/GPU latency evidence is in its separate run artifact.

## Cost and interpretation

`scripts/benchmark_cost_report.py` reports measured fit/prediction work from an
audited snapshot. It excludes preprocessing, cache construction, alignment
preparation, loading, cooldowns, earlier experiments, and auxiliary controls.
It is not total elapsed project time or an electricity-cost estimate.

All current benchmark plots and tables remain exploratory because Gate A is
unsigned. The seven-method sweep jointly fits source and support trials. The
separate 45-run EEGNet support-fine-tuning baseline is not mixed into that table
or used to inflate its record count.

## Plausibility review evidence

`scripts/prepare_plausibility_review.py` verifies the current processed-file
snapshot, re-audits benchmark records and cross-checks every saved support/query
count, query class count, and dataset rejection total against the independent
corpus audit. It publishes `runs/plausibility_packet.json` for a single fixed
record snapshot. Partial grids stay explicitly partial.

The packet includes every two-class subject/method case exceeding the frozen
78% review trigger in any seed, with each seed's class recall and record hash.
It does not automatically create the final plausibility review, clear high
scores, or claim scientific gate approval. Matching counts establish size and
class balance, not proof that model fitting respected all split boundaries.
Final review must consider all cases and retain unresolved acquisition,
preprocessing, chronology and pretraining-overlap limitations. Four-class BCI
results and the separate two-class support-fine-tuning protocol are distinguished.
