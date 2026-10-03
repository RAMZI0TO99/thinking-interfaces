# Cho2017 first-tranche execution-readiness review

23 September 2026, updated 24 September (Riyadh time). This review began as a read-only code and evidence trace after the
versioned 60 Hz Profile B cohort passed its [52-subject engineering audit](cho_60hz_real_cohort_review_20260923.md).
It now also records bounded source hardening for the selected four-method,
five-shot tranche. It does not freeze an experiment or admit a scientific fit.

**Current status, 24 September (Riyadh time):** the public Cho evidence verifier refuses the
complete proposed two-candidate selection because its 5,253 gradient steps
per case exceed the unchanged 256-step engineering cap. The earlier 45-fit
controls are stale for the present source. The current full
[exact-source quality bundle](../../runs/phase2/quality_history/20260924_recorder_bridge_hardened_458be569.json)
passed lint, strict types, 783 tests / 1 skipped / 1,009 subtests for source
`458be5698b0c0a7a2dd79afc03c907e94fd51ef88fb19b53999cf744d7def727`
at 08:14 UTC on 24 September;
its logs and source identity verified. No scientific cell, commit or push has
occurred.
The [pure exact-rational aggregation core](cho_analysis_execution_contract_20260924.md)
has a [preceding-source engineering receipt](../../runs/phase2/analysis_aggregation_checks/20260924_f2d4acdd/receipt.json).
It needs an externally verified complete cell roster and makes no inference
or report; the owner-pending analysis settings are unchanged.
The [current-source recorder bridge receipt](../../runs/phase2/analysis_aggregation_checks/20260924_recorder_bridge_hardened_458be569/bridge_receipt.json)
pins bounded synthetic admission checks with no real scores.

## What the four methods would read

| Selected method | Target and source signal path | Current condition |
| --- | --- | --- |
| `labram_linear` | Cho Profile B 60 Hz through `ChoProfileAssets60Hz` | Pinned case inputs and a pre-claim evidence gate exist; complete selection and a supervised execution worker remain open. |
| `labram_full` | Same 60 Hz Profile B path | Same execution boundary. |
| `labram_lora` | Same 60 Hz Profile B path through the trained LoRA runner | The pre-claim gate also validates actual LoRA structure and selected settings. |
| `eegnet` | Cho Profile A at 128 Hz | Its pinned route carries an empty Profile B map; complete selection and supervised execution remain open. |

The LaBraM manifest runner checks a complete cohort and rejects mixed 50/60 Hz
assets (`adaptation/labram_manifest.py:265-302`); the trained LoRA runner uses
that admission path (`adaptation/labram_lora_trained.py:259-331`). The binder
selects the versioned namespace and checks config, raw source, artifact and
trial identities (`evaluation/phase2_profile_binding.py:375-575`). EEGNet's
source and anchor paths use Profile A (`adaptation/source_selection.py:227-270`,
`adaptation/anchor_manifest.py:178-245`). The 52/52 cohort audit verifies
real versioned five-shot bindings, which is input evidence, not a scientific
method run.

## Pinned case route and remaining execution gap

`evaluation/phase2_cho_60hz_inventory.py` now constructs all 52
`ChoProfileAssets60Hz` values from caller-supplied audit and config pins.
The builder subsequently rehashed all 52 real subjects with reconstructed
Profile A catalogs under recovered disk headroom. The
[write-once real-inventory receipt](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/real_inventory_receipt.json)
records 52/52 verified inputs, catalog and inventory digests, and zero
scientific cells. `prepare_cho_first_tranche` now reconstructs the pinned A
catalogs, rehashes the versioned B inventory and supplies independent records
and method-correct assets for all 1,040 cases. The
[real-route receipt](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/real_case_route_receipt.json)
verified all 1,040 plans against the saved crosswalk, with 260 per method.
No production caller starts complete selection or target execution from this
route yet.

The saved [planning manifest](../../runs/phase2/freeze_reconciliation/20260919_step46/planning_manifest.json)
has 1,300 five-method cells, including deferred EA. It is labeled
`unratified_planning_only_not_executable`; its identities do not pin the new
60 Hz asset inventory. A new [selected-scope planning crosswalk](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/selected_planning_crosswalk.json)
joins its 1,040 four-method cells to the [cohort audit](../../runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json)
without reading EEG. The [write-once receipt](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/receipt.json)
pins both inputs and the output hash. Independent checks found 260 cells
per method, 52 subjects, five seeds, 52 versioned LaBraM subject bindings,
and no EA cell. EEGNet cells pin Profile A instead. This remains planning
evidence until the executable route and configurations are verified.

## Recorder provenance check before scientific use

`CellIdentity` declares dataset, protocol, selection, preprocessing and
checkpoint digests (`evaluation/phase2_records.py`). The pilot executor now
checks them against the case plan, configuration, reconstructed source cohort,
typed target catalog and returned checkpoint. It also reconstructs the
episode envelope before claim and checks the returned support/query identities,
query labels and count against its fixed partition before publication. The
TCPL and anchor adapters now normalize their internal payload digest to the
episode-envelope digest used by the cell identity. Focused Ruff and mypy checks
passed. The full pilot suite passed 8 tests / 15 subtests after disk space
recovered; the integrated pilot and recorder suite passed 17 tests / 41
subtests after the repetition fix. Those were earlier focused checks.
The expanded Cho route, pre-claim gate, selector verifier, selected-source
store, recorder and pilot focused bundle subsequently passed **45 tests / 57
subtests** on that review-stage source. The current full exact-source quality
bundle above covers later source changes.

The new per-case append-only success receipt also prevents one shared-identity
cell from counting every pilot repetition as measured. For the selected Cho
methods, `TargetCaseExecutor` now requires a canonical persisted selector
record in `runs/phase2`, verifies its complete 51-fold-per-candidate source
selection and the final model state before claim, and rechecks that evidence,
source identity and live machine admission after target work. The static method
configuration must match the selector roster, 60 Hz variant and actual target
adapter settings. The older BCI pilot path retains its engineering-only digest
interface. Later hardening verifies the persisted evidence envelope, replays
seeded source-batch trial order, checks the live model and adapter again after
target work, and requires verified failure records for failed claims. The
public verifier recomputes the whole selector workload and refuses 5,253
steps per case at the 256-step cap, so this guard is not a scientific
execution authorization.
The pilot's per-case time cap is checked after `predict_target` returns
(`evaluation/phase2_pilot.py:450-474`), so a production orchestrator also
needs an external timeout that can stop a stalled fit under the declared
resource policy.

The selector record remains separate from the source-cohort envelope.
`SelectedSourceStore` can preserve complete selector evidence and final
weights as append-only safetensors plus a source/config-bound completion
manifest, and rejects tampered restore bytes. Its opt-in factored evidence
format pins physical bytes, schema and size while reconstructing the exact
logical envelope; an opt-in sparse-weight format saves only trained tensors
for Cho linear/LoRA against a pinned initialization. The default canonical
JSON and full-weight formats remain readable. The
[selected-source restore design](cho_selected_source_restore_design_20260923.md)
describes a factory that reconstructs the four method recipes from pinned
baseline and static configuration, checks the restored LoRA structure and
requires the public complete-evidence verifier before returning an adapter.
No production case caller yet uses that factory, and the current cap prevents
any complete proposed Cho selection from passing it. The pilot's per-case
time cap remains retrospective. A tested Windows Job Object primitive can
stop its owned process tree, but an end-to-end case parent has not been wired
to the factory, execution contract and recorder. An
[isolated synthetic case transaction](cho_case_transaction_contract_20260924.md)
has a parent-held contract digest, supervised child proposal and parent-held
attestation digest. Its bounded tests establish only this synthetic file and
process boundary. It does not prove child authorship, execute a Cho fit or
cell, or call the recorder.

## Production inventory builder

`load_cho_60hz_assets` implements this contract. It requires operator-supplied
audit/config hashes, all 52 typed Cho Profile A catalogs, the passing cohort
audit and an exact versioned directory; it streams current artifact/manifest
hashes and checks manifest provenance without decoding EEG. The per-subject
binder subsequently rechecks raw source and A/B trial identities. Four focused
synthetic inventory tests and the real 52/52 inventory pass. The
1,040-cell crosswalk remains planning evidence, not this live check.

## Candidate rehearsal, freeze and resource boundaries

The [proposed candidate template](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json)
now names two ordered, typed source/support settings for each selected method,
with an explicit per-case LoRA source seed policy. Its
[read-only validator](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/verify_proposed_four_method_candidates.py)
materialized all 40 method/candidate/seed combinations. A current-source
[1,040-case receipt](../../runs/phase2/freeze_readiness/20260924_458be569_candidate_routes/proposed_candidate_case_route_receipt.json)
and [guarded run receipt](../../runs/phase2/freeze_readiness/20260924_458be569_candidate_routes/run_receipt.json)
matched the unchanged static roster to every live route under the real 52-subject
inventory. It recomputed 5,304,000 inner source steps, 53,040 final source
steps, 106,080 inner support steps and 1,040 target support steps. This is a
reviewable proposal, not a ratified or committed scientific configuration.
The previous 23 September candidate-route receipt pinned older runner and
gate code; its result remains historical.

- `configs/phase2/analysis.toml:13-15` still marks secondary families pending
  and `experiment_frozen = false`. The selected four-method scope and 60 Hz
  preprocessing choice do not resolve the complete scientific freeze.
- The candidate template makes proposed settings executable as typed inputs
  but remains under `runs/phase2/freeze_readiness`, outside committed
  scientific configuration. The [candidate review](cho_four_method_candidate_template_review_20260923.md)
  names the unmeasured values requiring ratification.
- Complete two-candidate Cho selection needs 5,253 gradient steps per
  LaBraM/EEGNet target case, above the unchanged 256-step engineering cap.
  The public evidence verifier now recomputes and enforces that refusal.
  The full runtime and cooling envelope is not measured or admitted.
- The [actual-model storage probe](cho_selected_source_storage_review_20260923.md)
  serialized the pinned plain LaBraM, trained LoRA and EEGNet state shapes
  without fitting. Its [write-once receipt](../../runs/phase2/freeze_readiness/20260923_storage_probe/receipt.json)
  projects **16.928 GiB** of final weight blobs for one distinct blob per
  1,040 cases. With **31.397 GiB** free at the receipt snapshot, retaining the
  unchanged 20 GiB project floor leaves a **5.531 GiB shortfall** for weights
  alone. The later [evidence review](cho_selection_evidence_storage_review_20260923.md)
  projects **25.551 GiB** for repeated inline source-identity maps under the
  original uncompressed store; full final weights plus those maps project to
  **42.479 GiB** before other evidence and checkpoints. No reuse is credited.
  The conditional retain-all
  checkpoint estimate in that review is not an enabled execution policy.
  The [opt-in factored evidence format](cho_evidence_storage_format_option_20260923.md)
  and [sparse-weight option](cho_selected_source_sparse_storage_option_20260923.md)
  are implemented and tested without complete Cho selection. Their conditional
  table-plus-sparse-weights subtotal is **6.120 GiB**, leaving only **2.515 GiB**
  for all other evidence, checkpoints and temporary space at the sizing
  snapshot. An [actual-architecture sparse store probe](../../runs/phase2/freeze_readiness/20260924_actual_sparse_store_probe/receipt.json)
  independently reconstructed the pinned initialized linear and LoRA models
  and restored synthetic trainable-only changes byte-exactly. The stored
  blobs were 1,752 and 14,808 bytes respectively, matching the earlier sizing
  receipt. Its disposable selector records did not pass complete Cho scientific
  selection verification; the probe started no fits, measured no full-case
  evidence and grants no disk or compute admission. The target-case
  [supervision design](cho_case_supervision_design_20260923.md) now has tested
  Windows containment, recorder publication recovery, and an owned child-result
  channel wired to a synthetic engineering case. The parent holds the recorder
  case lock through a separate engineering receipt. No integrated Cho target
  worker or ratified selection deadline exists.
- The source-bound 45-fit controls belong to earlier source identities. The
  [current-source wrapper](../../runs/phase2/control_refresh_checks/20260924_recorder_bridge_hardened_458be569/README.md)
  is pinned to `458be569`. Its [write-once 08:15 UTC preflight](../../runs/phase2/control_refresh_checks/20260924_recorder_bridge_hardened_458be569/preflight_receipt.json)
  deferred at 8.215 GiB available RAM against the unchanged 10 GiB startup
  guard; disk had 26.627 GiB free and no fit began. The `f2d4acdd`, `713fe95e`, `0f679414`, 4a- and 8c-source
  wrapper attempts are historical. Controls remain to be refreshed when
  both parent and worker guards admit them.
  A [read-only current-source inventory](../../runs/phase2/control_refresh_checks/20260924_recorder_bridge_hardened_458be569/inventory_receipt.json)
  verified context `400cf099deb83ae15799ffab0cf07b06b6d1e74d44b67cdca2c2b022862f5480`:
  0 valid / 45 missing controls, with no invalid or unexpected record.
- The 18:39 UTC disk shortage was temporary. At 19:30 UTC disk free was
  32.326 GiB, above the unchanged 20 GiB floor, while available RAM was
  8.711 GiB, below the separate 10 GiB control-refresh startup guard. The
  interrupted pilot test left about 77 MiB in `tmp/tmp3zu8p5br`; automatic
  policy rejected its removal. No scientific fit was attempted.
- A [synthetic diagnostic](pre_cue_post_cue_leakage_diagnostic_20260923.md)
  and [bounded real-run sensitivity](real_pre_cue_future_sensitivity_20260923.md)
  show that current full-run zero-phase filtering allows post-cue samples to
  affect pre-cue control windows. A [separate, unratified no-future
  proposal](pre_cue_no_future_v1_proposal_20260923.md) cuts raw input before
  each cue. Its [all-subject signal audit](real_pre_cue_no_future_all9_audit_20260923.md)
  compared 9 subjects, 108 runs and 5,184 cues and found exact invariance
  in 18 representative real-run future-input perturbations. The
  [posthash receipt](../../runs/phase2/gate_a_diagnostics/20260923_no_future_all9_posthash/real_pre_cue_no_future_all9_posthash.json)
  records the per-cue differences from the historical path. The later
  [artifact receipt](../../runs/phase2/gate_a_diagnostics/20260923_no_future_artifact_pairs/receipt.json)
  pins all nine saved proposed controls after raw recomputation. No matched
  control-model metric was produced. The [exact-source read-only matched receipt](../../runs/phase2/gate_a_diagnostics/20260924_no_future_recorder_bridge_hardened_458be569/receipt.json)
  recomputed all nine raw inputs at 08:23 UTC and found
  0 valid / 36 missing fits, no invalid records or score (context
  `172b6bc0cb198efcbc774549e9c699a25d1e3f5b948386dd60d87b34f6705f2c`); a
  separate earlier default runner deferred at the 10 GiB startup RAM guard. Gate A
  remains unsigned, with an independent owner decision still required.

## Ordered next work

1. Refresh the 45 source-bound controls through the prepared exact-source
   wrapper only when their unchanged disk, RAM and cooling guards admit it.
2. Define a complete-work compute, storage and checkpoint-retention envelope
   for the four-method scope; resolve the 5,253-step selector requirement
   without weakening the unchanged engineering guard by implication.
3. Prepare a supervised Cho case worker using the
   [parent-owned case design](cho_case_supervision_design_20260923.md), adapting the
   tested synthetic owned Job result channel to a real worker. It consumes the pinned route,
   complete source evidence and restored model, with a hard external timeout
   and live admission throughout each fit. It cannot launch scientific work
   under the current cap and unratified configuration.
4. Present the candidate configuration, primary test direction/threshold,
   secondary-family, TOST reporting status and full-freeze choices for owner
   review. Build a Phase II analysis command that consumes the ratified
   settings and publishes auditable subject/seed aggregation and inference;
   the current generic Phase I statistics helpers are not that command.
   Gate A needs saved no-future controls, matched model evaluation and its
   own owner decision; MMIDB remains separate.
   Scientific cells require committed configurations, owner ratification
   and complete-work admission.

Source and tests changed during bounded hardening; historical records,
scientific configuration and results were not changed. No scientific fit,
commit or push occurred.
