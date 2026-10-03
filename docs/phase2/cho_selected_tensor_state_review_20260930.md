# Cho selected-source tensor-state analysis review

30 September 2026. This is an **engineering analysis check**, not a Cho
scientific result. The [paired-input composer](../../evaluation/phase2_cho_analysis_preparation.py)
now asks for an independently supplied full static configuration object for
each of `labram_linear`, `labram_lora`, `labram_full` and `eegnet`, as well as
the separate method digest map. It checks the exact four keys and each
`method_configuration` digest before reading recorder claims. The caller must
also supply the pinned route inputs, source provenance, base configuration,
case cells and per-case selected-source publication pins. A cell's checkpoint
digest and the publication's manifest, recipe and environment digests remain
independent of the recorded selection claim.

The composer first rederives the 1,040-case route and checks target-input
attestations, recorded selection files and physical selected-source manifest,
evidence-copy and weights files. For each recorded winner, it then calls
[`verify_cho_selected_source_state`](../../evaluation/phase2_cho_source_restore.py)
with the pinned plan, full method object, selected candidate, evidence and
manifest digests, route protocol, recipe digest and cell checkpoint digest.
The helper derives the architecture without trusting the publication manifest,
checks the persisted selection contract and runtime, constructs a fresh seeded
model, and restores the published `full_v1` tensor state through
[`SelectedSourceStore`](../../evaluation/phase2_selected_source_store.py).
The store checks the exact safetensors tensor names, shapes, dtypes, finite
values and complete model-state digest before strict loading. The helper
returns only a frozen digest witness; it releases no target adapter. Score
rows are read only after every case passes. Selection and physical-manifest
file witnesses are checked again after paired-input construction, so a late
change refuses the result.

## Bounded reads and memory

The store's manifest, canonical evidence and weights reads enforce byte
limits on the **opened descriptor**, with path and file identity rechecked
after the read. The factored evidence path retains its bounded read. The Cho
helper requires a direct regular `full_v1` weights file of at most **64 MiB
for LaBraM** or **1 MiB for EEGNet**, checks its identity before and after
restore, requires **6 GiB currently available host RAM** before the case,
and refuses to continue below **4 GiB** during or after reconstruction.
LaBraM baseline construction also decodes only verified bytes from a bounded
opened descriptor: at most **1 MiB** for its model JSON and **64 MiB** for
its safetensors checkpoint. The baseline paths and digests are rechecked
after model construction.
Cases were originally invoked sequentially in the composer process; the
[isolated-case execution plan](cho_isolated_case_execution_plan_20260930.md)
has since been applied, and the composer now verifies each case in an owned
supervised child under a query-back-verified Job commit cap with polled
peak accumulation. Measured per-method peak commit and the real 1,040-case
reconstruction remain open; a historical record of the sequential design is
preserved in the [earlier execution
plan](cho_selected_tensor_restore_plan_20260928.md).

## Verification and boundary

The [source-restore tests](../../tests/test_phase2_cho_source_restore.py)
exercise a real synthetic EEGNet publication and fresh model restoration,
including the helper's weights-size, RAM and file-identity refusals. They
also reject oversized or replaced LaBraM baseline files before decoding. The
[store tests](../../tests/test_phase2_selected_source_store.py) cover
bounded preliminary manifest and canonical evidence reads, weights limits,
and opened-descriptor growth and replacement. The
[composer tests](../../tests/test_phase2_cho_analysis_preparation.py) use a
mock at the narrow tensor-helper boundary for 1,040 synthetic cases, because
that fixture's weights are not safetensors. The mock checks case coverage,
ordering before score extraction and failure without paired output. These
tests establish the engineering checks, not that 1,040 real selected sources
exist or have been reconstructed.

At source `08751a3919971f47c65f0dd14bd4061dc0dd7f070b07908023374a89361e6387`,
focused restore tests passed **39 tests and 29 subtests**, all five composer
tests passed individually, and focused Ruff and strict mypy passed. The
[read-only method-template revalidation](../../runs/phase2/freeze_readiness/20260930_08751a39_method_template_readonly/receipt.json)
passed without fitting and remains unratified. The
[guarded full-quality runner](../../runs/phase2/quality_attempts/20260930_tensor_state_08751a39_guarded/run_guarded_quality.py)
has not started below its 9 GiB disk floor. The
[historical `90d822aa` full-quality archive](../../runs/phase2/quality_history/20260928_quality_timeout_90d822aa.json)
passed for its exact earlier source and does not attest this changed source.
Successful reconstruction would establish that the **present** selected
weights match the independently specified architecture and pinned state
digest. It cannot prove which model produced historical target predictions,
replay inference, verify the complete selector or its 5,253 gradient steps
per case, satisfy the missing no-future and control evidence, ratify the
method template, sign Gate A or enact the scientific freeze. See the
[analysis execution contract](cho_analysis_execution_contract_20260924.md)
for those admission boundaries.
