# Freeze reconciliation review

19 September 2026, milestone 46. The owner authorized reconciliation for
review with "yes do what you have to and what you see fit" after the
fold/count and primary-roster contradictions were surfaced. This authorizes
the correction and analysis; it does not ratify the freeze or admit E2.

## Decisions adopted within the delegated scope

1. Retain full tuning in the proposed primary tranche. `analysis.toml`
   names it as the regularization reference; the pilot specification
   explicitly includes it. The contradictory exclusion is removed.
   EA inclusion remains the owner's choice; both counts are shown.
2. Interpret complete LOSO by the actual cohort: Cho 51 inner folds with
   50 training subjects, BCI 8 with 7. Every primary target/method/seed
   combination needs its own selection unless reuse is explicitly verified.
   Baseline accounting assumes no reuse and preserves every expected cell.
3. Retain the previous proposed candidate values, clarifying that each SGD
   candidate pairs its source/support learning rate. They remain proposals,
   not measured two-candidate results. Correct TCPL's target updates to zero
   and its Cho source episode to four trials under the eight-trial cap.
4. Replace the earlier hour claims with a reproducible, incomplete timing
   proxy. Use maximum measured stage costs and the 1.25 allowance; charge
   every candidate/fold and the final target case. Explicitly leave missing
   runtime, storage and retention costs unknown rather than inventing them.
5. Correct readiness claims: ratification is necessary but insufficient.
   Existing selector limits/defects, candidate and secondary-family
   specifications, committed-configuration provenance, and compute admission
   remain prerequisites. No guard, production code or config is changed.

Each adopted interpretation is recorded as a deviation in the append-only
log and decision register. Candidate values are retained without a new
accuracy-informed choice. Gate A, the frozen H2 margin, MMIDB source-policy
decision and publication/commit restrictions are unchanged.

## Checks and discriminators

The real-data check hashed all 52 Cho Profile A artifacts against their
saved audited catalogs, reconstructed all 52 episode envelopes and all 52
source-selection envelopes, and verified every inner source/validation/target
role. This distinguishes a real 51-fold cohort from a copied BCI narrative.
It does not redo preprocessing or fit a model.

The explicit planning manifest has 1,300 unique cells and 1,300 unique
selection dependency keys. Independent nested enumeration yields 132,600
candidate/fold evaluations, 106,080 neural inner fits, 1,040 neural final
fits and 26,780 EA classical fits. Removing EA alone leaves 1,040 cells.
This distinguishes per-method 260 selections from a whole-tranche count.

Fifteen saved five-shot pilot envelopes were checked by digest and their
timing fields used independently of decoding metrics. Maximum source/target
stages yield 1,893.4 neural hours and 3,328.0 EA hours after the allowance,
assuming no reuse. These are transfer estimates from one target and the
pilot's actual candidate settings; full selection, other candidates/subjects,
preparation, persistence, retention, controls and waits remain unmeasured.
The draft no longer treats those numbers as a complete resource envelope.

AST-extracted `run_selection` admission expressions were executed with a
sentinel that stops before any fold, without importing ML modules. Actual
source requests for the 52-subject/two-candidate case are LaBraM 5,253,
TCPL 5,151, EEGNet 136 and EA 16. The first two exceed 256; the latter two
undercount actual work (5,253 steps and 102 fits). The extracted LaBraM
aggregation reports 51/16 for 51 folds each scoring 1/2. Those reproducible
failures qualify earlier cohort-generic/execution-ready claims. They are
documented findings; no production fix or scientific workload ran.

The saved milestone-40 script also distinguishes actual pilot LaBraM lr
0.01 from proposed 0.001/0.002. Separate throughput probes use different
batch sizes, and the prompt probe times a support wrapper; neither exact
runtime transfer nor convergence follows from those measurements.

## Evidence and scope

Evidence lives under
`runs/phase2/freeze_reconciliation/20260919_step46/`:
`before.json` and original document/quality snapshots; `reconcile.py`;
`analysis.json`; `planning_manifest.json`; full quality logs/status; and
`receipt.json` / `documentation_receipt.json` produced by the finalizer.
Source fingerprint remains
`37dbc5e91a1581b56d7c59f46112f3939a6403646c32503c6a46f54c7e939d24`.

Baseline hashes cover every source/config/test file, all nonignored
workspace files, 1,502 pre-existing Phase II evidence files, the prior
quality logs and the frozen H2 receipt. Finalization checks those preserved
bytes and append-only history, plus the fresh exact-source full quality
bundle. The milestone receipt is the authoritative result of that check.

The original milestone-44/45 documents and receipts remain as history;
current status heads and the working draft are corrected. No production
source/config/test changes, control refresh, scientific experiment, commit
or push are part of this milestone. The documented selector findings are
real prerequisites, not an invented new experiment or permission to change
resource guards. The next owner review must use this revised draft, not
the superseded hours or one-sentence-implies-immediate-execution claim.
