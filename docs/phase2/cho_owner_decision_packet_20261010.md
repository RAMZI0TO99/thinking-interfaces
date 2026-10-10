# Cho2017 owner decision packet, 10 October 2026

Prepared for review; unratified and inert. Scientific Gate A and the experiment
freeze remain unsigned. The [JSON packet](cho_owner_decision_packet_20261010.json)
pins the current inputs and records every owner response as undecided. This
packet makes the remaining decisions concrete; it does not admit execution.

## Current evidence and dated reconciliation

| Item | Verified status and limit |
| --- | --- |
| Current source | SHA-256 `3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`, 432 files; preparation Git `c867703e40a61e3b8f9bdb81812649bcc96301cd` |
| Engineering quality | Existing exact-source full-quality bundle verified; 1,055 tests passed. No full-suite replay in this phase. |
| Current original controls | 81 actual records passed: shuffle 9 mean 0.4876543209876543 < 0.60; original pre-cue 36 mean 0.24855324074074076 < 0.35; matched no-future 36 mean 0.24508101851851852 < 0.35. These EEGNet diagnostics do not qualify a full LaBraM selector. |
| Raw/environment prerequisites | Fresh 52 raw sources, catalogs/B assets and original control environment passed in the preceding phase; all-nine existing no-future artifacts verified. A real LaBraM worker environment/admission remains separate. |
| Current selection/resources | Committed ceiling 5,253 gradient steps; per-case analysis cap 5,905,580,032 bytes (5.5 GiB); configured attempt 480 seconds. Older 256-step and untracked-config references are historical. |
| Public release identity | Both local checkpoint files match the pinned public releases. Recording-level cohort/overlap evidence remains unresolved. |
| Historical Phase I | All 450 stored reference records retain their audited hashes. This preserves historical results; it does not recertify them against current source. |
| Original real case | Two attempts spent, zero remaining; no recoverable original publication or engineering intent. Owner gate decisions cannot reset those attempts. |

The [control execution report](cho_b_disk_cache/source_prerequisites_refresh_20261010.md)
and [new release provenance report](../checkpoint_release_provenance_20261010.md)
give the evidence scopes. Older review sheets retain their dated snapshots:
their missing 45/36 controls and 256-step cap no longer describe this source.
Their scientific choices remain unratified.

## Decisions for the scientific owner

| Decision | Concrete review position | Response |
| --- | --- | --- |
| Gate A acceptance rationale | Assess the historical protocol-matched reference and diagnostics using an explicit acceptance rationale or request more evidence. No numerical tolerance has been adopted. | Undecided: accept with documented rationale / revise evidence requirements / defer. |
| Checkpoint cohort and overlap | Obtain a checkpoint-bound manifest/log or attestation; assess actual recording and subject intersection for each evaluation dataset and state the eligible claim. | Undecided; provenance evidence absent. |
| Cho scope and candidate template | Review the previously selected five-shot, 52-subject, four-method, five-seed scope and the pinned two-candidate settings below. | Undecided: ratify exact version / specify revision / defer. |
| Primary analysis | Review the complete proposed rule below, including unit, ties/zeros, directional test, arithmetic mean condition and separate interval. | Undecided: ratify complete rule / specify prospective revision / defer. |
| Secondary superiority family | Proposed empty; full tuning and EEGNet are descriptive comparisons. A different family needs an exact prospective declaration and the configured Holm adjustment. | Undecided. |
| Margin interpretation | Proposed exploratory estimate and 90% interval at the existing frozen planning margin, with no formal equivalence claim. | Undecided. |
| Experiment freeze | Ratify a named protocol/candidate/analysis/provenance version only after its evidence and operational conditions are resolved. | Undecided; no scientific execution budget admitted. |

Gate A is a decision on already known historical outcomes. Any new acceptance
rationale is therefore retrospective and must be labelled that way; it cannot
be presented as a criterion chosen before those results. The future Cho tranche
rules must be settled before its outcomes are interpreted. The published
between-subject/session standard deviation is not an acceptance tolerance.

The historical reference-seed mean ROC-AUC is 0.7566061980347695, versus the
published mean 0.7715: difference -0.014893801965230491. The four repeat-seed
subject mean is 0.750191798941799 with its historical subject-based 95% interval
[0.5903977788629133, 0.9099858190206846] across nine subjects. There are 450
fit records, not 450 independent subjects. No pass criterion is inferred from
these estimates or from the published standard deviation 0.1933.

## Proposed future Cho tranche, unchanged and unratified

The selected scope is `labram_linear`, `labram_lora`, `labram_full`, `eegnet`;
shots per class 5; seeds 11, 23, 37, 53, 71; 52 subjects. This yields 1,040
planned cells and separate selections. LaBraM uses versioned 60 Hz Profile B;
EEGNet uses matched Profile A. EA remains deferred. This subset does not freeze
all methods, shots or datasets in the general protocol.

The [original candidate template](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json)
has ordered learning rates 0.001 and 0.002, one source step per subject and one
support step, exact mean-subject balanced-accuracy selection, first-declared
candidate tie breaking, and no early stopping. Source batches are 2 for LaBraM
and 4 for EEGNet; query batch size is 8. LoRA targets the last block's QKV
module with rank 4, alpha 1.0 and a trained head; its source seed is the case
model seed. The JSON packet retains the complete template and its exact hash,
including all method-specific details. Its status remains proposed. The
template's Profile B hash must match the current versioned configuration.

The [original technical proposal](cho_four_method_freeze_technical_proposal_20260928.md)
specifies the full analysis rule, retained here for owner review:

1. Admit the complete verified 1,040-cell roster. Form exact-rational five-seed
   means and 52 subject differences, LoRA minus linear. Missing, duplicate,
   stale, extra or unverified cells fail admission; no imputation or substitution.
2. Proposed primary test: one-sided Wilcoxon signed ranks, LoRA greater than
   linear, Pratt zeros, asymptotic p-value, `correction=False`, alpha 0.05.
   Encode signs and exact absolute tie classes as signed integer levels before
   the SciPy call. For an all-zero vector, p = 1 with no superiority; other
   non-finite results fail the analysis.
3. A superiority statement additionally requires an unrounded p < 0.05 and a
   strictly positive exact paired arithmetic mean. The signed-rank p-value is
   not a test of that arithmetic mean. Report all decision inputs and tie/zero
   counts under the proposal's statistical assumptions.
4. Separately display the two-sided 95% paired-mean Student t interval using
   52 subject units and 51 degrees of freedom, with sample variance denominator
   51. Zero variance gives a point interval. This interval is not an inversion
   of the signed-rank test or a second superiority criterion.
5. Proposed secondary superiority family is empty. Full tuning and EEGNet
   summaries and LoRA-minus-full/EEGNet contrasts are descriptive.
6. Display the existing planning margin +/-0.05202907926797159 with a two-sided
   90% paired-mean t interval as an exploratory estimate. No `equivalent`
   Boolean, formal TOST or clinical interchangeability claim is proposed.
   Formal equivalence would require a separate prospective owner decision.

Current analysis configuration still has `experiment_frozen=false` and
`secondary_families_status=pending_before_experiment_freeze`. The packet pins
all 13 current Phase II configuration files and the earlier proposal; it edits
none of them and performs no inference on scientific cells.

## Missing provenance input and future operation boundary

A sufficient provenance submission must identify the original checkpoint by
SHA-256; name the source and date of the statement; list dataset versions,
recording/subject identifiers or privacy-preserving mappings, relevant splits
and exclusions; and explain how the actual checkpoint training run maps to
that cohort. Dataset-level assurances alone cannot assess recording overlap.
Raw data redistribution is not requested. The [complete request draft](checkpoint_provenance_request_draft_20261010.md)
is prepared and unsent; no third party was contacted.

The paper names MMIDB in pretraining; actual evaluation-recording overlap is
unknown. Cho2017/IV-2a absence from its named list is not exclusion proof. Any
future claim must disclose established pretraining exposure and unresolved
intersection rather than presume an unseen-cohort result.

Full real cached-selector completion is unverified. Any allowed separate
engineering operation still needs a defined protocol, exact real worker/cache
path, event sink and runtime pins, measured worker environment, resource and
storage envelope, fresh admission and shared-machine coordination. This packet
provides none of that admission. It preserves the original 480/520/600-second
attempt/session/outer limits, startup 10/active 4 GiB RAM, disk 20 GiB and
process 6/Job 7.5 GiB guards. The committed 5.5 GiB analysis cap and 5,253-step
ceiling are engineering settings, not scientific ratification.

The original exhausted case remains immutable. No third attempt, reset,
relaunch or renamed equivalent case is supplied. Cache remains opt-in; no
default activation, new schedule, training or recorder operation occurred.
Pro2's genuine response reported no pause or ownership conflict; its Source
scheduling information is peer disclosure, not Pro3 numerical acceptance or
runtime authority. All decisions above remain with their authorized owners.
