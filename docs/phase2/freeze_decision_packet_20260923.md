# Phase II freeze decision packet — 23 September 2026

The [compact review sheet](cho_four_method_freeze_review_sheet_20260924.md)
lists the exact owner choices and current execution gates in one place.
The later [28 September technical proposal](cho_four_method_freeze_technical_proposal_20260928.md)
specifies an unratified analysis decision rule and reconciles the complete
selection workload, cap, CPU proxy and storage scenarios for that review.
The subsequent [pure inference review](cho_pure_inference_review_20260928.md)
records the new source-bound quality, route and control checks; all earlier
source-bound receipts in this packet retain their dated historical scope.

**Current status, 24 September (Riyadh time):** The owner's four-method scope and 60 Hz
preprocessing choices are recorded. The [real 60 Hz cohort](cho_60hz_real_cohort_review_20260923.md)
passed its 52/52 engineering audit, and the [execution-readiness review](cho60hz_execution_readiness_review_20260923.md)
links verified inputs and routes for all 1,040 proposed cases. A
[current-source read-only check](../../runs/phase2/freeze_readiness/20260924_458be569_candidate_routes/run_receipt.json)
matched their candidate settings with no fit. The two-candidate template is
reviewable but unratified and outside committed
scientific configuration. The public evidence verifier refuses the complete
5,253-step Cho selection per case against the unchanged 256-step engineering
cap. The [write-once readiness handoff](../../runs/phase2/freeze_readiness/20260924_458be569_handoff/receipt.json)
pins the current quality and read-only evidence. No full scientific freeze,
scientific cell, Gate A sign-off, scientific
compute admission, commit or push is claimed. The corrected [freeze draft](scientific_freeze_draft.md)
and [decision register](decision_register.md) retain the open owner decisions.

**Later evidence addendum:** The proposed no-future pre-cue path had a
[real-data signal audit](real_pre_cue_no_future_all9_audit_20260923.md) across
9 subjects, 108 runs and 5,184 cues. Its [posthash receipt](../../runs/phase2/gate_a_diagnostics/20260923_no_future_all9_posthash/real_pre_cue_no_future_all9_posthash.json)
records 18 representative future-input perturbations whose proposed windows
remained exactly equal, with all 18 raw-file hashes verified again. It contains
no control-model result and does not sign
Gate A. The later [artifact-cohort receipt](../../runs/phase2/gate_a_diagnostics/20260923_no_future_artifact_pairs/receipt.json)
pins all nine saved proposed control subjects and 5,184 windows after fresh
raw recomputation; a separate 36-fit matched diagnostic remains unrun. Its
08:23 UTC [current-source read-only receipt](../../runs/phase2/gate_a_diagnostics/20260924_no_future_recorder_bridge_hardened_458be569/receipt.json)
rebuilt all nine raw inputs and found
0 valid / 36 missing fit records, no invalid records and no score (context
`172b6bc0cb198efcbc774549e9c699a25d1e3f5b948386dd60d87b34f6705f2c`).
Its child exit code 1 records incomplete controls, not a failed fit; the
wrapper verified that expected outcome. The separate
10 GiB RAM startup guard has deferred training. The audit's
`raw_files_verified = false` flag is set until all 36 fit records exist; the
pre-fit nine-subject writer check itself completed. The earlier `713fe95e`
and `0f679414` read-only receipts are historical.
The
[actual-model storage sizing](cho_selected_source_storage_review_20260923.md)
projects 16.928 GiB for one distinct final weight blob per planned case, a
5.531 GiB shortfall above the unchanged 20 GiB disk floor at the probe's
31.397 GiB free-space snapshot, before selection evidence or checkpoints.
The current [exact-source quality receipt](../../runs/phase2/quality_history/20260924_recorder_bridge_hardened_458be569.json)
passed lint, strict types, **783 tests, 1 skip and 1,009 subtests** for source
`458be5698b0c0a7a2dd79afc03c907e94fd51ef88fb19b53999cf744d7def727`
at 08:14 UTC on 24 September. The earlier 45 source-bound controls remain
stale. A [current-source wrapper](../../runs/phase2/control_refresh_checks/20260924_recorder_bridge_hardened_458be569/README.md)
is prepared; its [write-once read-only preflight](../../runs/phase2/control_refresh_checks/20260924_recorder_bridge_hardened_458be569/preflight_receipt.json)
deferred at 8.215 GiB available RAM against the unchanged 10 GiB startup
guard, with 26.627 GiB disk free and no fit. Earlier `713fe95e`, `0f679414`,
4a- and 8c-source wrappers are historical. Quality alone does not admit
scientific compute.
The [read-only current-source inventory](../../runs/phase2/control_refresh_checks/20260924_recorder_bridge_hardened_458be569/inventory_receipt.json)
verifies 0 valid / 45 missing controls under context
`400cf099deb83ae15799ffab0cf07b06b6d1e74d44b67cdca2c2b022862f5480`,
with no invalid or unexpected record.
The later [selection-evidence storage review](cho_selection_evidence_storage_review_20260923.md)
projects **25.551 GiB** for repeated source-identity maps alone under the
original uncompressed store. Alongside full final weights, that is **42.479 GiB**
before step histories and other evidence, versus **8.635 GiB** usable above
the 20 GiB floor at its later snapshot. This is a planning estimate, not
measured complete evidence.
The [opt-in factored evidence format](cho_evidence_storage_format_option_20260923.md)
now reconstructs repeated bindings from one table per case and checks the
exact logical evidence bytes. A separately opt-in sparse-weight format saves
only trained linear/LoRA tensors against a pinned initialization. Both have
bounded synthetic tests. A later [actual-architecture sparse store probe](../../runs/phase2/freeze_readiness/20260924_actual_sparse_store_probe/receipt.json)
constructed the pinned initialized Cho linear and LoRA models and round-tripped
synthetic trainable-only changes exactly, with 1,752 and 14,808 byte sparse
blobs respectively. Its disposable evidence had no complete public Cho
selection proof; it started no fits and measured no full-case evidence.
Factored tables plus full weights still exceed that snapshot's headroom
by at least **8.766 GiB**. Factored tables plus sparse weights have a
conditional **6.120 GiB** subtotal, leaving only **2.515 GiB** for all other
evidence, checkpoints and temporary storage at that snapshot. Neither is a
scientific compute admission.
At the [08:15 UTC current-source preflight](../../runs/phase2/control_refresh_checks/20260924_recorder_bridge_hardened_458be569/preflight_receipt.json),
disk free was 26.627 GiB: 6.627 GiB above the 20 GiB floor. Against that
dated snapshot, the conditional 6.120 GiB subtotal would leave about 0.507
GiB for every unmeasured whole-case artifact and temporary peak. Available
RAM was 8.215 GiB, below the unchanged 10 GiB control startup guard.

**Historical cohort checkpoint, 23 September:** The [real-cohort review](cho_60hz_real_cohort_review_20260923.md) records 52/52 versioned artifacts, historical-hash preservation, trial joins and real five-shot bindings. Subject 01 passed the predeclared 60 Hz signal diagnostic at 30.67 dB attenuation. At that checkpoint, the 17:10 UTC disk snapshot was 24.533 GiB free; the separate control refresh was held because available RAM was 7.98 GiB against its 10 GiB startup guard. The first-tranche scope and scientific admission boundaries below are unchanged.

**Earlier engineering follow-up, 23 September:** The Cho-only 60 Hz config,
write-once preparation entry point, versioned binding and bounded read-only
diagnostic were prepared. At that checkpoint no real EEG had been rebuilt. See the
[preparation review](cho_60hz_preparation_review_20260923.md) for tests and
the newer failing disk/RAM snapshot. The measurements and planning arithmetic
below retain their original decision-time context.

## Owner decision: four-method first tranche

The owner chose four neural methods for the **first exploratory Cho2017 five-shot tranche**: `labram_linear`, `labram_lora`, `labram_full`, and `eegnet`. `ea_tangent_lr` is deferred to a separately costed, predeclared comparison. EA remains in the nine-method research roster. This scope choice does not approve execution.

| Cho option | Planned target cells and complete selections | Corrected CPU no-reuse proxy, including 1.25 retry allowance | Assessment |
| --- | ---: | ---: | --- |
| Four neural methods | 1,040 | 1,893.4 hours | Selected first scope; still far beyond the current admitted work. |
| Add EA-tangent | 1,300 | 5,221.4 hours total, including 3,328.0 EA hours | Retains the classical anchor in the first tranche, with a large additional cost. |

The proxy uses maxima from three bounded Cho pilot repetitions. It is **a planning estimate, not a measured full selection, upper bound, funded budget, or completion date**. Both candidate settings were not timed in complete source selection, subjects vary, and startup, persistence, controls, cooling, and storage peaks are unpriced. The proposed candidate rates also differ from the LaBraM pilot rate. The full resource envelope is unknown.

The primary analysis remains Cho2017, five shots, LoRA minus linear probe in balanced accuracy, subjects as paired units after within-subject averaging over seeds 11/23/37/53/71. Secondary multiplicity families remain pending in `configs/phase2/analysis.toml`; choosing a first tranche does not freeze them.

### Decision recorded

The owner's response was "Four methods; defer EA (Recommended)." The
five-method row above is retained as a cost comparison, not the selected
first-tranche scope.

## Owner decision: prepare a 60 Hz Cho rebuild

Cho metadata declares a **60 Hz** line frequency in `configs/cho2017.toml`, while Profile B uses the shared **50 Hz** notch in `configs/base.toml`. The Cho preprocessing script applies that setting, and the Phase II profile binding pins it. The methodology draft describes origin-specific 50/60 Hz notches. I found no saved Cho comparison measuring the 50-versus-60 effect or explicit approval of the exception in the inspected repository evidence. This is a definite configuration mismatch; its effect size has not been measured.

The owner chose "Prepare 60 Hz rebuild (Recommended)." Prepare a newly
versioned Cho Profile B configuration, artifacts and binding-audit plan
for review. Existing 50 Hz config/artifacts and historical evidence remain
untouched. This choice does not admit preprocessing or ratify the full
experiment; a separate resource-admitted implementation and audit are needed.
The [60 Hz rebuild plan](cho_profile_b_60hz_rebuild_plan_20260923.md) names the
version boundary, affected code paths and acceptance checks.

The preceding paragraph records the decision-time instruction. The versioned
rebuild and its 52/52 audit were subsequently completed; the
[real-cohort review](cho_60hz_real_cohort_review_20260923.md) is the current
engineering evidence. This completion still does not ratify scientific use.

## Proposed first-tranche analysis-family choice for owner review

The [analysis execution contract](cho_analysis_execution_contract_20260924.md)
sets out the proposed 1,040-cell roster, subject-level aggregation, input
refusals and write-once report boundary for review. It is not executable or
ratified.

For the selected four-method Cho2017 five-shot tranche, the smallest
predeclared superiority family would contain only the configured primary
LoRA-minus-linear comparison. Declare the **secondary superiority family
empty** for this tranche. Report full tuning as the regularization reference
and EEGNet as the architecture anchor on matched subjects and seeds, with
paired descriptive differences and uncertainty, but no secondary superiority
p-values, method-winner claim or mechanism claim. Any later superiority claim
would need a prospective family and the already specified Holm adjustment
before that experiment; first-tranche results cannot be promoted afterward.

This is a recommendation, not an adopted analysis setting.
`configs/phase2/analysis.toml` still says
`secondary_families_status = "pending_before_experiment_freeze"` and must
record the owner's chosen family before scientific freeze. The configured
LoRA-linear TOST equivalence analysis is a **separate** prespecified question
with its frozen margin and 90% interval. Keeping it means LoRA-linear is the
sole primary *superiority* comparison, not the only inferential analysis. If
the owner wants only one inferential claim of any kind, TOST must be deferred
explicitly before freeze. The packet also needs to say whether a retained
TOST is a formal claim or a prespecified exploratory analysis; the present
draft names the test but does not settle that reporting status.

For ratification review, the conservative proposed wording is: retain the
frozen TOST margin and 90% interval as a **prespecified exploratory**
analysis, report its estimate and interval, and make no equivalence or
interchangeability claim from this first tranche. This matches the config's
description of the margin as a planning margin rather than clinical
interchangeability. If the owner instead wants a formal equivalence claim,
its reporting status and relationship to the primary superiority inference
must be declared before outcomes are available. Neither choice has been
written into `analysis.toml` or adopted by this packet.

The primary test still needs an explicit **direction and decision rule**.
`analysis.toml` names `paired_wilcoxon_pratt` and a 95% confidence level but
does not pin one- or two-sided testing or a primary superiority alpha. The
existing generic `evaluation/statistics.py` function calls SciPy Wilcoxon
without an explicit alternative argument; it is a Phase I helper, not an
implemented Phase II decision rule. A ratified analysis must state whether
the directional claim is LoRA greater than linear under a one-sided test, or
a two-sided difference with a separately specified positive-effect rule, and
pin the corresponding threshold before results are seen.

## Execution remains closed after these choices

- Complete Cho two-candidate LaBraM/EEGNet selection requires **5,253 gradient steps** before target adaptation, above the unchanged **256-step engineering ceiling**. TCPL needs 5,151; EA needs 102 inner classical fits. Splitting calls or raising the ceiling to evade admission is not approved.
- Executable candidate configurations and secondary families are unfinished. `configs/phase2/` is untracked; the standing rule requires committed executable configurations for experiments, while commit/push authorization remains reserved to the owner.
- The Phase II analysis configuration declares the primary paired test and TOST, but no Phase II result aggregation/reporting command consumes `configs/phase2/analysis.toml` yet. A pure exact-rational aggregation core and a [bounded recorder bridge](cho_analysis_execution_contract_20260924.md) now exist for externally pinned completed cells. The bridge checks recorder claims, retries, publication and exact scores; its caller still must verify scientific source, cohort, episode, selection evidence and configuration. It reads no real Cho score and makes no inference. The generic Phase I statistics functions are not the Phase II decision rule. Ratified test direction and threshold, family handling, full scientific admission and auditable report publication remain necessary before inferential results can be issued.
- An earlier 23 September decision-time snapshot had **8.76 GiB free disk** against the **20 GiB floor** and **5.36 GiB available RAM** against the separate **10 GiB startup guard for control refresh**. Those readings are historical; disk later recovered. Full-weight, uncompressed evidence remains far above measured headroom. The opt-in formats have not established a complete Cho disk envelope, and current resource admission is required before new heavy work.
- The real 1,040-case input route is checked. A Windows process-containment primitive and crash-replayable recorder publication are implemented. The [synthetic case transaction](cho_case_transaction_contract_20260924.md) now passes a bounded proposal through an owned child handle under a full-lifetime recorder case lock and writes a separate engineering receipt. It does not fit Cho, publish a scientific cell, or prove exact executable bytes at launch. No parent-owned end-to-end Cho target worker is admitted or connected. The current-source quality bundle passed; current-source controls, a full runtime, storage and checkpoint-retention envelope, and fresh resource admission remain required before scientific cells. Phase II has **zero admitted scientific cells**.

## Separate owner decisions

**Gate A:** Phase I's 75.66% reproduction versus the cited 77.15% reference has no owner-adopted acceptance rule. The historical pre-cue negative control passed its preset threshold at 24.8553%, but `data/pre_cue.py` applies zero-phase FIR filtering to the continuous run before cutting pre-cue windows. Post-cue samples can therefore influence those windows. The later [no-future proposal](pre_cue_no_future_v1_proposal_20260923.md) and all-subject signal audit above measure the signal-path difference and representative future-input invariance; they provide no matched control-model metric or Gate A approval. Review Gate A separately before treating it as accepted.

**MMIDB:** Subjects 079 and 100 are episode-ineligible under the current maximum-support/query policy. Their source-cohort treatment still needs the separate owner eligibility decision and implementation audit.

**Provenance:** No commit or push is authorized by this packet. Ratification of a later corrected freeze would still be distinct from commit authorization and compute admission. Every Phase II result remains exploratory until the relevant gates are explicitly met.
