# Cho selected-source restoration boundary

`evaluation/phase2_cho_source_restore.py` provides a prospective restoration
path for the first Cho2017 five-shot tranche: LaBraM linear, source-trained
LaBraM LoRA, LaBraM full, and EEGNet. It performs no fitting or target work.

`prepare_cho_source_restore` accepts a caller-pinned hash of the static method
configuration and a selected candidate name. It derives a model recipe without
reading any selected-source manifest. EEGNet's architecture follows the source
selector's fixed 64-channel, 512-sample, 128 Hz constructor. LaBraM's recipe
uses the reviewed forward-parity model-config hash, the audited safe baseline
checkpoint hash, 800 samples and the Cho channel order. Both baseline files are
rehash-checked before construction; construction and final adapter release recheck
them. These baseline files sit outside the source fingerprint, so the final
rehash detects a late change to either file. LoRA's QKV
targets, rank, alpha, seed and head policy come from the static candidate after
substituting the planned case seed. The real injected parametrization and its
non-tensor scaling are checked with `validate_trained_lora` after restore.

The factory resolves the physical evidence path through the pinned store
manifest and reads the canonical logical selection envelope before loading
any selected weights. The physical file may be canonical JSON or the opt-in
factored format; the store verifies its format, schema, size and bytes and
reconstructs the same logical envelope. The factory requires the recorded
Python, PyTorch, NumPy and
Braindecode versions to match the live constructor dependencies. EEGNet is
rebuilt under the recorded case seed and its pristine state digest must equal
the final source fit's recorded initial digest. LaBraM uses the same seed for a
fresh classifier head, then compares the full reconstructed template digest to
`contract.template_state_sha256`. It resets the head under the source selector's
seed and compares `contract.initial_state_sha256`, applies the selected plain or
LoRA source initialization, and compares the final fit's initial-state digest.
Any mismatch refuses restoration before selected weights overwrite the model.
After the store reloads the evidence, the factory requires the exact same
record as the pre-restore read. It rechecks runtime versions, source identity,
model state, LoRA structure and the pinned LaBraM baseline files immediately
before releasing the adapter. The recorded source runtime must also have a
valid float32, CPU or CUDA:0, positive-thread schema, including CUDA metadata
when CUDA was used. A CUDA source fit may be restored for CPU target support:
source device and thread count are recorded and validated without requiring
them to equal the target runtime. The target environment is separately bound
by `CellIdentity.environment_sha256` and `TargetCaseExecutor` pre/post checks.

`restore_cho_selected_source` constructs the model from that recipe, lets
`SelectedSourceStore.restore` verify the manifest, evidence and safetensors
against it, checks the selected candidate against the method roster, then runs
the full `verify_cho_selection_evidence` before returning an adapter. It does
not return an adapter on a failed check. The ordinary preclaim and posttarget
gates remain required where the adapter is later used.

The current two-candidate 52-subject Cho selection needs at least 5,253
pre-target gradient steps per case, above the unchanged 256-step engineering
selector ceiling. Thus no complete current selection evidence can pass this
factory. The focused tests exercise all four recipe derivations, a real LoRA
parametrization, immutable EEGNet store restoration, wrong constructor versions,
malformed runtime metadata, wrong pristine-state lineage, post-verification model
mutation, late baseline-file mutation, and explicit
refusal of incomplete cohort evidence. They do not fabricate a complete scientific
selection, claim a target cell, or endorse the unratified candidate draft.

This checks consistency with recorded digests and the pinned baseline. It does
not prove that a future source producer used this deterministic LaBraM template
construction: the current source selector accepts a caller-supplied template,
whose head initialization is not otherwise specified. A completed producer must
use the same seeded template recipe and retain its construction receipt before
its selection record can pass this factory. No current 52-subject final source
fit or selected weights exist to validate that end-to-end lineage.
