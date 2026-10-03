# Cho selected-source tensor reconstruction plan

30 September update: the [tensor-state engineering review](cho_selected_tensor_state_review_20260930.md)
describes the implemented read-only helper, bounded store reads and composer
integration. The original design below remains a record of the proposed
checks. Its isolated-child and measured peak-memory requirements are still
open for a real 1,040-case analysis sweep.

28 September 2026. **Engineering design only; no tensor reconstruction was
added to the analysis composer by this note.** The current
[paired-input composer](../../evaluation/phase2_cho_analysis_preparation.py)
checks independently pinned selection, manifest, evidence-copy and weights
bytes before score extraction. Its
[physical manifest bridge](../../evaluation/phase2_cho_selected_manifest_bridge.py)
streams the weights hash but does not decode safetensors or compare tensors to
an independently rebuilt model. This plan closes that prospective analysis
check without treating a recorded `complete` flag as proof of the selector.

## Proposed bounded path

1. Extend the composer's independent inputs with an exact four-method map of
   **full static method configuration objects**, not just the existing digest
   map. Require keys `labram_linear`, `labram_lora`, `labram_full`, and
   `eegnet`; compare each object's `method_configuration` digest with the
   separately reviewed `method_config_sha256` pin. Reject missing, extra or
   changed configurations before any recorder read. Retain the external
   per-case `ChoSelectedSourcePin`, source, protocol, cell, route and case-input
   pins. Derive a case's winner from its already verified selection claim,
   never from the selected-source manifest alone.
2. After the current selection-file and physical-manifest checks, and before
   `verified_score_rows`, reconstruct one case at a time. Factor a read-only
   tensor verifier from
   [Cho source restoration](../../evaluation/phase2_cho_source_restore.py):
   use `prepare_cho_source_restore` with the caller's plan, full method object,
   independent method digest and selected candidate; read the pinned evidence
   before constructing a model; enforce its constructor dependency/runtime
   checks and seeded initial-state lineage; then call
   [`SelectedSourceStore.restore`](../../evaluation/phase2_selected_source_store.py)
   with that freshly constructed model, the independent evidence/manifest
   digests, route protocol object and derived recipe. The store already checks
   manifest context, exact safetensors names, shapes, dtypes, finite values,
   complete reconstructed model-state digest and strict state loading. Compare
   the restored publication and `state_digest(model)` with the external
   `ChoSelectedSourcePin` and cell checkpoint digest. Recheck the baseline
   files, source and runtime before accepting the per-case tensor witness.
3. The helper should return a small immutable digest/witness, **not an adapter
   or model**, and must not run target inference. Preserve the existing
   [`restore_cho_selected_source`](../../evaluation/phase2_cho_source_restore.py)
   path and its full `verify_cho_selection_evidence` requirement for an actual
   adapter. After all 1,040 tensor witnesses pass, read exact score rows and
   construct paired inputs. Recheck the existing physical selection/manifest/
   evidence/weights witnesses after aggregation. If any case fails or a file
   changes, return no paired input.

The current [publication hook](../../evaluation/phase2_cho_publication_gate.py)
requests `full_v1` weights. Require that format for this tranche; a sparse
selected-source format would need its own analysis review and memory envelope.
The store's generic 4 GiB manifest-bridge weights limit is too large for a
shared 8 GiB host. Before the store can allocate, require a direct, pinned
regular weights file and a tighter per-case limit: at most 64 MiB for LaBraM
and 1 MiB for EEGNet. The [architecture sizing probe](cho_selected_source_storage_review_20260923.md)
measured about 23.3 MB and 12.7 KB respectively. Admit a tensor case only
with at least 6 GiB *currently available* host RAM, stop if availability
falls below 4 GiB, and process only one case at a time in an isolated child
so decoded evidence, tensor blobs and PyTorch state are released between
cases. These proposed RAM limits require a measured peak-memory test before
they become an execution policy; a failed guard defers the whole analysis
preparation and never admits a partial roster.

## Verification before implementation is considered complete

- Add a real EEGNet store round trip using coherent synthetic evidence and
  a freshly seeded constructor. Mutate valid safetensors tensor content while
  updating its file hash and manifest; require reconstructed model-state or
  schema refusal. Also reject wrong static method object/digest, winner,
  recipe, initial-state digest, source, external checkpoint digest, oversize
  file and changed file identity. Exercise late baseline changes for a
  LaBraM case without a full 1,040-case fit.
- Extend the current [1,040-case composer test](../../tests/test_phase2_cho_analysis_preparation.py)
  with a **mock only at the new tensor-verifier boundary**. Assert exact
  case coverage, one-at-a-time calls, failure before score extraction,
  all-or-nothing output and post-score witness checks. That test's current
  `synthetic-selected-source-weights-v1` bytes are deliberately not real
  safetensors, so it cannot itself establish tensor reconstruction. Keep a
  separate real store test in
  [source-restore tests](../../tests/test_phase2_cho_source_restore.py)
  for actual decoding and state comparison, plus memory guard tests without
  allocating a giant blob.

This would prove that the **present** published selected weights restore into
the independently specified architecture and match the pinned state digest.
It would not prove that historical target predictions used those weights,
replay inference, verify every selector fold or gradient, ratify the method
template, sign Gate A or enact the scientific freeze. The
[publication and manifest review](cho_selected_source_publication_and_manifest_review_20260928.md)
and [analysis execution contract](cho_analysis_execution_contract_20260924.md)
keep those admission boundaries separate.
