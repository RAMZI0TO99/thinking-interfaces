# Conditional selected-source storage option

23 September 2026, updated 24 September 2026 Riyadh time. **Engineering
option only.** `SelectedSourceStore` now has an opt-in versioned sparse format
for Cho `labram_linear` and `labram_lora`. Its default remains the original
complete-state format, and existing complete-state manifests still restore.
The sparse path has synthetic tests but no real Cho publication, source fit,
target prediction or scientific cell was started.

The [write-once probe receipt](../../runs/phase2/freeze_readiness/20260923_sparse_storage_probe/receipt.json)
was independently checked against its envelope SHA-256
`bde246030a4820fa744ab85e6324901accfd59be91fd0e3884a81304be2b1e77`
and file SHA-256
`a61edcfdbc46b847593ef25212ec0465b3fe77446c67da3cb9f049d7db1d0ff4`.
It reconstructed the proposed architectures on CPU, applied each method's
current trainable mask and serialized the selected tensor set with
`safetensors`. It used the 1,040-case, 260-per-method planning route and
performed no training. Its source fingerprint was
`2f93981d1814b27579206aecee7a8ebdb54998d62c970ee395649697d225b416`;
later source changes require a new exact-source probe before relying on its
identity, though the measured method and tensor counts are recorded.

| Method | Cases | Current full blob/case | Trainable blob/case | Conditional stored blob/case |
| --- | ---: | ---: | ---: | ---: |
| LaBraM linear | 260 | 23,294,624 B | 1,752 B (2 tensors) | 1,752 B |
| LaBraM LoRA | 260 | 23,307,704 B | 14,808 B (4 tensors) | 14,808 B |
| LaBraM full | 260 | 23,294,624 B | 23,294,624 B (223 tensors) | 23,294,624 B |
| EEGNet | 260 | 12,664 B | 11,608 B (12 tensors) | 12,664 B |

The original complete-state design projects **16.928 GiB** for one distinct
final source blob per case. If linear and LoRA saved only their trainable
tensors while full tuning and EEGNet retained complete blobs, the same
blob-only arithmetic would be **5.648 GiB**, a conditional difference of
**11.280 GiB**. The option is implemented but is not wired into a scientific
case runner or measured with the actual selected states. It receives no
storage credit in the freeze budget. The
[current storage review](cho_selected_source_storage_review_20260923.md)
also identifies a larger uncompressed selection-evidence cost.

Publication calls `SelectedSourceStore.publish(...,
weights_format="sparse_frozen_init_v2", initial_model=independently_built_model)`.
The supplied initial model must be a separate same-class object with no shared
tensor storage. Its exact initial state digest must match
`final_source_fit.initial_state_sha256`. The final-fit trainable names and
parameter count must match the fitted model's live `requires_grad` mask, and
the mask policy must match the selected Cho linear or LoRA candidate. Every
omitted parameter and buffer must be byte-identical to initialization. The
full final-state schema and digest are recorded along with the initial digest,
mask digest, stored and omitted names, sparse weights hash, evidence hash,
protocol, source and architecture recipe. The sparse safetensors are decoded
and byte-compared before the manifest-last, write-once publication. Both
storage formats hold one crash-releasing project-wide process lock while
calculating pending bytes, checking the disk floor and publishing files, so
selected-source output directories cannot each spend the same admitted free
space.

Restore uses the caller-provided initialized model, which the
[Cho restore design](cho_selected_source_restore_design_20260923.md) constructs
from pinned baseline files and case seeds. It checks the initial digest, full
schema, mask and all pinned context; overlays only stored tensors in memory;
then checks the **complete reconstructed state digest before strict loading**.
The model is rolled back to initialization if the load or postload check fails.
Malformed format fields, sparse names and sparse bytes are rejected. The
selected-source store still does not independently prove the scientific
selection history: the later Cho evidence verifier remains required before
adapter release. Likewise, the store cannot prove how a caller built its
initial model beyond its class, separate storage, source/recipe pins and exact
evidence-bound state digest.

Focused tiny-model tests cover v1 compatibility, both sparse methods,
initialization and mask mismatches, frozen parameter and buffer drift,
corruption, digest tampering, rollback and interrupted publication resume.
Actual Cho model round trips and a full storage accounting are still needed
before promoting this format into the freeze. The probe did not price
selection evidence, manifests, intermediate checkpoints, filesystem overhead
or temporary peak space.

At the probe snapshot, free D: space was about **28.966 GiB**, leaving about
**8.966 GiB** above the unchanged 20 GiB floor. Other work was consuming
the same volume, so that observation is not a future capacity reservation.
The unchanged 256-step cap still rejects the proposed complete two-candidate
Cho selection of 5,253 steps/case. Scientific freeze, complete resource
admission, Gate A and committed executable settings remain open.
