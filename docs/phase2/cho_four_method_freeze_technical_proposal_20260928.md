# Cho2017 four-method freeze: technical proposal for owner review

28 September 2026. **Unratified proposal; scientific execution budget is zero.**
This annex makes the remaining analysis and resource choices reviewable. It
does not change `configs/phase2/analysis.toml`, the 256-step engineering cap,
any machine guard, or the [24 September source-bound handoff](../../runs/phase2/freeze_readiness/20260924_458be569_handoff/receipt.json).
No complete selection, target cell, inferential report, Gate A sign-off,
commit, or push is claimed.

## Scope already chosen

The owner selected five-shot Cho2017 with `labram_linear`, `labram_lora`,
`labram_full`, and `eegnet`; EA is deferred. The proposed roster is 52
subjects × 4 methods × seeds `11/23/37/53/71` = **1,040 cells and 1,040
separate selections**. The LaBraM methods would use the independently audited
[60 Hz Profile B cohort](cho_60hz_real_cohort_review_20260923.md), and
EEGNet would use its matched Profile A route. The
[24 September candidate-route rehearsal](../../runs/phase2/freeze_readiness/20260924_458be569_candidate_routes/run_receipt.json)
matched 1,040/1,040 planned cases without fitting. The ordered
[two-candidate template](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json)
is proposed, not frozen or committed.

## Proposed primary decision rule

This entire section requires owner ratification and an independently tested
Phase II analysis implementation before any outcome is interpreted. The
[analysis config](../../configs/phase2/analysis.toml) currently names
`paired_wilcoxon_pratt` and a 95% confidence level, but leaves these
operational rules unspecified. The [analysis execution contract](cho_analysis_execution_contract_20260924.md)
defines the complete-cell admission and exact aggregation boundary.

1. Admit exactly the verified 1,040-cell roster. For each subject and method,
   take the exact-rational mean of the five fixed-seed balanced accuracies.
   Form 52 exact differences `d_i = mean_i(labram_lora) -
   mean_i(labram_linear)`. Missing, duplicate, stale, extra or unverified
   cells stop the complete-tranche analysis; no imputation or subject/seed
   substitution is allowed. Publish the exact subject inputs and roster
   digest with the report.
2. Test the **one-sided positive paired shift** with Wilcoxon signed ranks,
   Pratt zero convention, at **α = 0.05**. The alternative is LoRA greater
   than linear. Rank all 52 absolute differences with average ranks for
   ties; zeros participate in ranking and contribute no signed rank. Pin
   `alternative="greater"`, `zero_method="pratt"`,
   `method="asymptotic"`, and `correction=False` for the
   [locked SciPy 1.18.1](../../requirements-core.lock). Do not
   rely on `method="auto"` or an implicit two-sided default.
3. Preserve exact tie classes when calling SciPy: sort the distinct positive
   exact values of `|d_i|`, assign them integer levels `1, 2, ...`, and pass
   each subject's signed level (or zero) as the precomputed difference.
   Signed-rank statistics depend on signs and absolute rank/tie classes,
   so this encoding has the same ranks as the exact rational differences
   without floating-point subtraction changing a tie. If all 52 differences
   are zero, record `p = 1` and no superiority; do not publish SciPy's
   undefined asymptotic result. Any other non-finite result fails the
   analysis rather than becoming a claim.
4. A primary superiority statement requires the complete admitted roster,
   an **unrounded** `p < 0.05`, and a **strictly positive exact arithmetic
   mean** of the 52 differences. Report the p-value, Wilcoxon statistic,
   zero and absolute-tie counts, exact paired-mean estimate, and the
   decision condition. The
   Wilcoxon test concerns a directional shift under a symmetric-difference
   model; its p-value is not a test of the arithmetic mean.
5. Report a separate **two-sided 95% Student t interval for the paired
   arithmetic mean**: `mean(d) ± t_(0.975,51) × s(d)/sqrt(52)`, with sample
   standard deviation using denominator 51. If variance is zero, report the
   point interval `[mean(d), mean(d)]`. Label this as uncertainty for the
   mean under its own assumptions, not as an inversion of the Wilcoxon test
   or an additional superiority decision. Pin numeric precision and output
   formatting in the eventual executable analysis version.

The [SciPy Wilcoxon reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html)
specifies the Pratt zero convention, one-sided alternative, tie/zero limits
on exact p-values, and the float-subtraction warning that motivates passing
precomputed rank-preserving differences. The frozen analysis implementation
must be tested on zero, tie, opposite-sign, all-zero and complete-roster
fixtures before use. The t interval uses subjects, never seed rows, as its
52 independent units; its coverage and the signed-rank interpretation depend
on their respective statistical assumptions.

A later [pure numerical engineering implementation](cho_pure_inference_review_20260928.md)
now passes synthetic tests and exact-source quality for the proposed rule.
It has no verified-cell collector, scientific admission or report writer;
this proposal remains unratified.
The later [full-roster synthetic rehearsal](cho_full_roster_inference_synthetic_review_20260928.md)
checks the 1,040-row arithmetic-to-calculation handoff without real scores.
The subsequent [synthetic recorder bridge rehearsal](cho_full_roster_recorder_inference_synthetic_review_20260928.md)
checks canonical recorder-format fixture bytes and externally pinned synthetic
scores before that handoff. It does not establish real-cell authenticity or
ratify this proposal.

### Other comparisons and the frozen margin

Propose an **empty secondary superiority family** for this first tranche.
Full tuning is the regularization reference and EEGNet the architecture
anchor. Show their matched subject summaries; if a contrast table is
included, limit it to LoRA minus full and LoRA minus EEGNet. For each, use
the same 52 subject units after five-seed means and label its 95% paired-mean
t interval descriptive. Issue no secondary superiority p-value, winner or
mechanism claim. A later superiority family must be declared before seeing
that experiment's outcomes and use the configured Holm rule.

Propose a **prespecified exploratory** LoRA-minus-linear margin display at
the existing frozen `±0.05202907926797159` balanced-accuracy margin. Report
the paired-mean estimate and two-sided 90% Student t interval using
`mean(d) ± t_(0.95,51) × s(d)/sqrt(52)`. Identify the margin lines and
the configured α = 0.05. Do not output an
`equivalent` Boolean or make an equivalence/interchangeability claim for
this tranche. A formal TOST claim would need a separate prospective owner
decision and executable decision rule; this proposal does not change the
frozen margin.

## Selection workload and cap decision

The template has two ordered candidates, one source gradient update per
training subject and one support update per validation fold. For one Cho
target/seed/method, there are 51 inner folds, 50 training sources per fold,
and 51 subjects in the winner's fresh final source fit:

| Work per case | Arithmetic | Gradient steps |
| --- | ---: | ---: |
| Inner source | `2 × 51 × 50 × 1` | 5,100 |
| Inner support | `2 × 51 × 1` | 102 |
| Fresh final source | `51 × 1` | 51 |
| **Complete selection** | `2 × 51 × (50 + 1) + 51` | **5,253** |
| Target support after selection | `1` | 1 |

Across 1,040 separate cases this is **5,463,120 selection gradients** plus
1,040 target support gradients. The [arithmetic review](selector_arithmetic_review.md)
and [scientific freeze draft](scientific_freeze_draft.md) provide the
selector and dependency evidence. A one-candidate variant would still need
`51 × (50 + 1) + 51 = 2,652` selection steps, so simply dropping one
candidate would not fit the existing cap.

The current selector constructors and public evidence verifier hard-refuse
declared ceilings above **256**. Proposed decision: accept 5,253 as the
*planned complete workload*, while retaining 256 for the current engineering
path. A separate, versioned scientific selection/admission and verifier
contract would need an owner-approved per-case ceiling of at least 5,253,
an exact whole-case step ledger, independently measured resource bounds,
and the unchanged RAM, disk, GPU and cooling guards. Splitting a case into
calls or raising an argument to evade the current ceiling is not an
admission. Until the new contract and its budget are approved, scientific
execution admission remains **zero cases**.

## Runtime and storage decision table

The [draft's CPU proxy](scientific_freeze_draft.md) uses three bounded Cho
pilot maxima, 260 selections per method, 102 inner evaluations plus one
final/target stage, and a 1.25 planning allowance. It is a serial-work
estimate, **not** a full-case measurement, upper bound, reserved compute
budget or completion date. Candidate rates differ from the timed pilot
LaBraM rate; startup, persistence, checkpoints, controls, cooling and other
concurrent work are unpriced.

| Method | Cases | CPU-hour proxy including 1.25 allowance |
| --- | ---: | ---: |
| LaBraM linear | 260 | 506.4 |
| LaBraM LoRA | 260 | 520.5 |
| LaBraM full | 260 | 667.8 |
| EEGNet | 260 | 198.7 |
| **Four-method total** | **1,040** | **1,893.4** |

Storage projections below are **incomplete component subtotals**, not a
whole-case envelope. GiB values are rounded from the [full-weight probe](cho_selected_source_storage_review_20260923.md),
[inline-evidence probe](cho_selection_evidence_storage_review_20260923.md),
[factored-evidence option](cho_evidence_storage_format_option_20260923.md),
and [sparse-weight option](cho_selected_source_sparse_storage_option_20260923.md).
Factored and sparse formats are opt-in and have not been measured with a
completed real Cho selection.

| Physical scenario | Known/projected subtotal | Versus 14.919 GiB above floor at 28 Sep 05:51 UTC |
| --- | ---: | ---: |
| Full final weights + uncompressed repeated identity/binding values | 42.918 GiB | 27.999 GiB short, before all other files |
| Full final weights + conditional factored tables | 17.401 GiB | 2.482 GiB short, before all other files |
| Sparse linear/LoRA weights + conditional factored tables | 6.120 GiB | 8.799 GiB left for **every unmeasured component and peak** |

At that read-only snapshot D: had 34.919 GiB free and Windows reported
4.888 GiB available RAM. The 20 GiB disk floor leaves 14.919 GiB nominal
headroom, shared with the other project; no space is reserved. The RAM
reading does not meet the separate unchanged 10 GiB control-fit startup
guard. Recheck both immediately before any admitted work.

Proposed physical policy for review: use factored logical evidence with
exact-byte reconstruction and sparse frozen-initialization weights only for
linear/LoRA; retain full weights for full tuning/EEGNet. Require the existing
independent verifier, full-state digest check and same logical evidence
digest. Propose **no immutable per-source-step checkpointing** for the
scientific tranche; restart an interrupted selection under the declared
one-linked-retry policy after fresh admission. The alternative of retaining
every LaBraM step would imply at least **85.057 TiB** of model tensors alone
for this roster. Failed-attempt evidence and temporary files still consume
space and must be measured. This policy is proposed, not active.

Before any full-tranche budget, measure representative complete selections
under a separately approved guarded engineering contract, including all
four methods, both candidates, physical evidence and final weights, source
and target stages, peak RAM/VRAM, peak temporary disk, persistent bytes,
failed-attempt retention and elapsed time. Choose calibration targets from
predeclared input-size metadata, not observed model scores; retain their
evidence as engineering only. Publish per-case bounds and a concurrency
reservation that keeps the 20 GiB floor intact while the other project can
use the machine. A representative measurement supports a revised estimate;
it does not by itself establish a worst-case bound across 52 subjects.

## Decision sequence

1. Owner reviews the candidate settings, primary rule, empty secondary
   family, exploratory margin status, and proposed physical/checkpoint
   policy. Record exact approvals or revisions in the freeze and executable
   configuration **before outcomes**. Ratification does not start a fit.
2. Prepare and verify a distinct complete-work admission path with its
   5,253-step case ledger. Set a guarded, owner-approved calibration ceiling
   and budget only after the resource case is concrete. Keep the current
   256-step engineering path intact. Price the whole-case and full-tranche
   envelopes from guarded, write-once engineering evidence.
3. Require committed executable configuration and current-source quality,
   controls, cohort/selection provenance and fresh machine admission before
   any scientific case. The present 45 source-bound controls are 0 valid/45
   missing; the separate no-future matched controls are 0 valid/36 missing.
   [Gate A](cho_four_method_freeze_review_sheet_20260924.md) remains unsigned
   and its claim boundary stays separate. No first-tranche result can be
   represented as a gated Phase I result.

The source fingerprint at the proposal's initial drafting was
`458be5698b0c0a7a2dd79afc03c907e94fd51ef88fb19b53999cf744d7def727`;
the [archived quality bundle](../../runs/phase2/quality_history/20260924_recorder_bridge_hardened_458be569.json)
passed lint, strict types, 783 tests, 1 skip and 1,009 subtests. These facts
establish that dated source state, not scientific readiness. The later
[pure inference engineering review](cho_pure_inference_review_20260928.md)
records source `9bf0516c11aec1e3cda0635e79fc58a7cc3db5d2df4d496a2039ab661ad597b9`
and its exact-source quality without changing this unratified decision rule.

The later [pure paired-input builder](cho_paired_inputs_review_20260928.md)
now forms the exact 208 five-seed means and 52 LoRA-minus-linear subject
differences from caller-supplied verified rows. Its current source is
`ef8b3f82`; the [focused receipt](../../runs/phase2/analysis_pairing_checks/20260928_ef8b3f82_focused/receipt.json)
passes 37 tests with one skip, Ruff and strict mypy. Full current-source
quality and refreshed controls remain pending. The earlier
[`a7841e14` full-quality attempt](../../runs/phase2/quality_attempts/20260928_cho_paired_inputs_a7841e14_disk_floor/receipt.json)
was preserved as failed because four synthetic child tests encountered
the 20 GiB disk prelaunch floor; the test-only fixture now supplies a
deterministic sensor without changing production guards. This engineering
work does not ratify the proposal or admit an analysis result.
