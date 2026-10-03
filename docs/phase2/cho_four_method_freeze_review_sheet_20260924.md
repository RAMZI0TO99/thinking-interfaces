# Cho2017 four-method freeze review sheet — unratified

Prepared 24 September 2026 for an owner decision. This sheet records proposed
choices and evidence; no box is selected, no gate is signed, and no scientific
cell is admitted. The detailed [decision packet](freeze_decision_packet_20260923.md)
and [scientific freeze draft](scientific_freeze_draft.md) control the full text.
The [28 September technical proposal](cho_four_method_freeze_technical_proposal_20260928.md)
now supplies exact proposed analysis rules and a dated runtime/storage
decision table. It is unratified and does not alter this sheet's gates.
A later [pure inference engineering review](cho_pure_inference_review_20260928.md)
pins the new `9bf0516c` source, 796-test quality bundle, 1,040/1,040
read-only routes and 0 valid / 45 missing controls. The 24 September
source-bound snapshots below are historical; the owner choices are unchanged.

## Choices already given by the owner

- First exploratory five-shot Cho2017 tranche: `labram_linear`, `labram_lora`,
  `labram_full`, and `eegnet`; EA is deferred to a separately declared and
  costed comparison. The roster is 52 subjects × 4 methods × 5 seeds = 1,040
  planned cells and selections. The 1,893.4 CPU-hour figure is a planning
  proxy with 1.25 allowance, not admitted compute.
- Prepare a separate 60 Hz Profile B cohort. The [52/52 real-asset audit](cho_60hz_real_cohort_review_20260923.md)
  passed. Existing 50 Hz assets and configuration remain historical.

These choices selected scope and preprocessing policy. They did not ratify
the full scientific experiment, Gate A, a selection workload, or a commit.

## Owner decisions still needed for a full freeze

| Decision | Proposed review wording | Owner response |
| --- | --- | --- |
| Cohort and candidate settings | Use versioned 60 Hz Profile B for the LaBraM methods, matched Profile A for EEGNet, and the [two-candidate four-method template](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json), after review and committed configuration. The [current-source route rehearsal](../../runs/phase2/freeze_readiness/20260924_458be569_candidate_routes/run_receipt.json) matched all 1,040 settings without fitting. | Approve / revise / defer; record exact revision. |
| Primary superiority analysis | [28 September proposal](cho_four_method_freeze_technical_proposal_20260928.md): 52 exact paired subject means from seeds 11/23/37/53/71; one-sided LoRA > linear Wilcoxon–Pratt, asymptotic p, α = 0.05, exact tie classes, positive paired mean, and a separate 95% paired-mean t interval. | Approve the complete rule / record an exact revision before outcomes. |
| Secondary superiority family | Proposed empty for this first tranche. Report full tuning and EEGNet descriptively on matched subjects and seeds, without secondary superiority claims. | Approve empty family / provide a prospective family. |
| LoRA-linear TOST status | Proposed prespecified exploratory estimate and 90% interval at the frozen ±0.05202907926797159 margin, without an equivalence or interchangeability claim. | Approve exploratory status / specify formal status and claim rule / defer. |
| Selection, storage and full scientific freeze | Review the [5,253-step cap and resource path](cho_four_method_freeze_technical_proposal_20260928.md). Adopt only after complete executable configuration, inference rules, provenance, measured runtime/storage envelope and owner decisions above are fixed. | Approve or revise the proposed path; ratify a named version only when its gates are satisfied. |

The [analysis execution contract](cho_analysis_execution_contract_20260924.md)
describes complete-cell input admission. A pure exact-rational aggregation
core passed a [1,040-row synthetic rehearsal](../../runs/phase2/analysis_aggregation_checks/20260924_f2d4acdd/full_roster_synthetic_receipt.json).
The [current-source recorder bridge](../../runs/phase2/analysis_aggregation_checks/20260924_recorder_bridge_hardened_458be569/bridge_receipt.json)
checks pinned record bytes and exact case inventories before aggregation. Both
checks read no real cells and produce no inferential report.

## Separate gates and execution conditions

- **Gate A remains unsigned.** The current-source [no-future audit](../../runs/phase2/gate_a_diagnostics/20260924_no_future_recorder_bridge_hardened_458be569/receipt.json)
  recomputed all nine raw inputs and found 0 valid / 36 missing matched fits.
  The 75.66% versus 77.15% reproduction gap still needs an owner-adopted
  acceptance rationale. This sheet cannot sign it.
- **The current 45 source-bound controls are incomplete.** The [read-only inventory](../../runs/phase2/control_refresh_checks/20260924_recorder_bridge_hardened_458be569/inventory_receipt.json)
  found 0 valid / 45 missing. The [fit preflight](../../runs/phase2/control_refresh_checks/20260924_recorder_bridge_hardened_458be569/preflight_receipt.json)
  deferred at 8.215 GiB available RAM below the unchanged 10 GiB startup
  guard; disk had 26.627 GiB free. No fit started. The owner allocated 8 GiB
  for current work, so this fit remains deferred.
  An earlier preceding-source [five-minute read-only watch](../../runs/phase2/control_refresh_checks/20260924_subject_aggregation_f2d4acdd/resource_window_receipt.json)
  sampled 9.264–9.744 GiB available RAM and never reached a stable 10.5 GiB
  operational launch margin.
- **Selection and case execution remain closed.** The proposed complete
  two-candidate selection needs 5,253 gradient steps per case, above the
  unchanged 256-step engineering cap. A [synthetic Windows case transaction](cho_case_transaction_contract_20260924.md)
  exists; no supervised real Cho target worker or complete-selection admission
  exists. Do not split the work to evade the cap.
- **Storage is not admitted.** At the 08:15 UTC disk snapshot, the conditional
  6.120 GiB factored-evidence/sparse-weight subtotal left about 0.507 GiB
  above the 20 GiB floor for all unmeasured whole-case evidence, checkpoints
  and temporary peaks. The [storage review](cho_selected_source_storage_review_20260923.md)
  does not measure a complete case. A later 28 September 05:51 UTC snapshot
  had 34.919 GiB free, leaving 8.799 GiB above the floor after that same
  conditional subtotal; this is still no full-case storage admission.
- **Committed executable configuration and provenance remain required.**
  `configs/phase2/` is untracked. No commit or push is authorized by this
  sheet. Ratification would not itself start compute.
- **MMIDB eligibility is separate.** Subjects 079 and 100 are episode
  ineligible under the current maximum-support/query policy; their source
  cohort treatment still needs the owner's decision.

The source at this sheet's 24 September checkpoint was
`458be5698b0c0a7a2dd79afc03c907e94fd51ef88fb19b53999cf744d7def727`.
Its [archived quality bundle](../../runs/phase2/quality_history/20260924_recorder_bridge_hardened_458be569.json)
passed lint, strict types, 783 tests, 1 skip and 1,009 subtests. Quality
verifies this code state; it does not resolve the decisions or admission
conditions above.
The [write-once readiness handoff](../../runs/phase2/freeze_readiness/20260924_458be569_handoff/receipt.json)
pins the current read-only receipts and records 0/45 source-bound controls,
0/36 no-future matched fits, no scientific cell and unsigned Gate A.
