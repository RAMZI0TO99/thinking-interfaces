# Audited baseline lineage and two partial linear folds

This candidate reconstructs the full LaBraM classifier from the existing audited
safe baseline, then executes two genuine public `BCILaBraMSourceSelector.run_fold`
calls. Both use inner validation subject 01 and outer target 02, seed 11, five
shots, repetition 1. They use the adopted linear candidates `lr_1e-3` and
`lr_2e-3`, source batch two with one update per source subject, and one support
update with query batch eight. The complete declaration retains all 102 folds
and 5,253 updates. This candidate executes only 100 source and two support
updates. It does not call `run_selection` or fit a final selected source.

All imports, model construction, safe tensor decoding, fixture construction and
folds require a newly admitted native Job: at most 600 seconds, 4,096 MiB process
and 5,120 MiB Job memory, 10 GiB available host RAM at admission and 4 GiB while
active, 20 GiB free disk, one Torch intraop and interop thread, and no visible
GPU. Existing pause and source/runtime pin requirements remain in force. The
call is `run_probe(output, method_config, set_protected_inputs=callback)`; its
callback denies reads of all four outer-target files throughout construction,
lineage checks and the two folds. Source and runtime modules stay unchanged.

The frozen fixture helper creates exactly 213 synthetic input files totaling
734,579,463 bytes for 52 subjects, including 64-channel profiles A (512 samples)
and B (800 samples), all four canonical shot levels, and two held-out queries.
Only the original five fixture configurations are copied. Baseline declarations
are read from the real project, never inserted into the frozen fixture inventory.
There are no study arrays or real raw recordings in this fixture.

The sole accepted pretrained checkpoint is the existing 23,299,672-byte
`model.safetensors` at snapshot
`0563b6c626e7b40d9a36653b763715db94d945d7`, SHA-256
`53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`.
Its 4,776-byte configuration is pinned to
`813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b`.
The explicit baseline reader bounds weights to 32 MiB and configuration to
1 MiB, checks ordinary direct single-link files and stable path/descriptor
identities before and after reading, then requires 221 finite CPU float32 tensors
containing 5,819,936 elements. Strict loading into the full 12-block, embed-200
backbone precedes canonical cropping to 800 samples. Seed 11 is set immediately
before constructing the two-class, 64-channel classifier, inside `fork_rng`.
No pickle, `.pth`, `from_pretrained`, network access, or loader replacement is
used. The completed classifier contains 5,818,138 parameters.

`prepare_cho_source_restore` derives the canonical architecture recipe using the
adopted method configuration. The separately pinned private `_new_model` helper
is exercised only as an independent lineage reconstruction, using its unchanged
canonical baseline reader. Template, selector-owned initial state and rebuilt
state must agree as appropriate, have disjoint tensor storage, preserve buffers
and the frozen backbone, and expose exactly two head tensors with 402 trainable
parameters. This does not exercise the public selected-source restoration APIs.
The canonical `full_v1` baseline construction path is available for a future
complete selected-source proof; sparse selected-source storage is unsupported
by that public restoration contract and is not qualified here.

Nonmutating forward and optimizer hooks independently require the exact linear
head mask, finite gradients and parameters, changed head bytes, adopted rate,
fresh stateless SGD, and unchanged frozen backbone/buffers at every actual
update. Canonical histories are independently checked for all 50 permitted
source subjects and one held-out support update per fold. Exact rational scores
are recomputed from the two query outcomes. The one-time setup and each public
fold have separate elapsed times. All inputs and global Torch, NumPy and Python
RNG states must remain unchanged.

`fold_01.json` and `fold_02.json` preserve the actual raw incomplete engineering
envelopes. Each must be refused at the public complete-selector payload schema.
`contract.py` collects them into a separate explicitly partial manifest with all
102 expected pairs and 100 still pending; it neither synthesizes a complete
envelope nor chooses a winner. `optimizer-observations.json` records the actual
102 observed updates, and `probe-result.json` binds lineage, inputs and evidence.

Loading an audited pretrained baseline does not verify its earlier cohort
provenance. This remains synthetic engineering work: no selected weights,
publication, recorder, study cell, scientific admission, or original-case
attempt. A continuation needs a separately reviewed API/contract for completing
the full 102-fold roster and the fresh 51-source final fit; these two partial
records are not a substitute for complete public `run_selection` evidence.
