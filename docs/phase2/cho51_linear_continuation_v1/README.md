# Eight-fold continuation on the accepted linear fixture

This separately versioned candidate executes eight new inherited public
`run_fold` calls: `lr_1e-3` with validation subjects 03, 04, 05 and 06, then
`lr_2e-3` with the same four validation subjects. Every fold trains on all 50
remaining source subjects, including subject 01, while excluding outer target
02 and that fold's validation subject. Current work is exactly 400 source and
eight support updates, 408 in total. Each update selects only the 402 parameters
in `head.weight` and `head.bias`, using the unchanged adopted rates and batches.

The two earlier subject-01 folds are explicitly adopted from their accepted
native origin. Their raw files and input fixture remain untouched. The combined
partial collection therefore contains ten of 102 distinct folds, with 92 still
pending, describing 500 source and ten support updates. Historical updates are
separate from the 408 updates performed in this new child.

`origin.py` independently verifies the original accepted metadata, source pins,
native receipt, qualification and raw folds. The probe reconstructs metadata
for the existing immutable 213-file, 734,579,463-byte synthetic fixture at
`runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture`.
It never calls the fixture builder, regenerates arrays, adds fixture files or
writes into that directory. All 52 catalogs, 64 channels, 800-sample Profile B,
512-sample Profile A, four shot levels and withheld query partitions remain
unchanged. All four outer-target paths are denied throughout model construction,
independent lineage reconstruction and all eight folds.

The exact audited safe baseline is decoded using the frozen bounded baseline
reader: 23,299,672-byte weights with SHA-256
`53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`,
4,776-byte configuration with SHA-256
`813073071865e6799f00f2c7ade117cb86238dd931c1b5f81e97ca68db00188b`,
32 MiB/1 MiB read ceilings, 221 finite CPU float32 tensors and 5,819,936 elements.
The full 12-block/embed-200 classifier contains 5,818,138 parameters. Manual
strict construction and independent canonical `_new_model` reconstruction must
reproduce the accepted template and initial state
`90a9d34ecba2aa96a942f7bd70724f63c2071042141935dbbcd78e0b373b89a7`,
without shared storage. The exact selector contract remains
`8397d34ee0a2280b406071e045988f98b1b73ce21fcecc0b9834518cd21993b1`.
No pickle, network access, pretrained download or canonical fitting/loader patch
is used. The earlier pretrained cohort provenance remains unverified.

The call is `run_probe(output, method_config, origin=origin,
set_protected_inputs=callback)` inside a freshly admitted native Job. Limits
remain 600 seconds, 4,096 MiB process and 5,120 MiB Job memory, 10 GiB available
host RAM at startup and 4 GiB while active, 20 GiB free disk, one Torch intraop
and interop thread and hidden GPUs. All genuine peer pauses and source/runtime
pins remain mandatory. The inherited public fold boundary releases canonical
resident input arrays after each fold; this candidate does not bypass that
verification or clearing behavior. Each fold has its own measured elapsed time.

`selector.py` adds an explicit `complete_final_fit` entry point. It first calls
the strict complete-roster metadata gate. Only after all 102 raw folds pass may
a required trusted caller capability verify their independently pinned native
origins. It must return the exact complete origin-chain receipt bound to all
record hashes, the collection digest and selector contract. Metadata alone never
grants numerical authority. The future branch then checks the logical complete
scope, performs a fresh canonical all-51-source fit, and emits the complete
canonical payload. That numerical branch and its trusted capability are
unqualified here. This probe only exercises the incomplete refusal before the
eight new folds and again after ten combined folds; neither call may reach the
origin capability or perform a final-fit update.

Nonmutating forward and optimizer observers independently check finite gradients,
changed head bytes, the exact adopted rate and stateless SGD, and unchanged
frozen backbone and buffers for all 408 updates. Canonical source histories,
support/query bindings and exact rational scores are checked separately. Physical
inputs, baseline bytes, original origin metadata and global Torch, NumPy and
Python RNG states must remain unchanged.

The eight create-once raw files `fold_01.json` through `fold_08.json` remain
incomplete public engineering envelopes and must fail the public completeness
schema. `partial-collection.json` binds the two original and eight current
records. `optimizer-observations.json`, `finalization-refusals.json` and
`probe-result.json` preserve current execution and its precise limits. There is
no winner, fresh final fit, selected-source weight publication, recorder, study
cell, scientific admission or original-case attempt. Completing this engineering
selector requires the remaining 92 genuine folds and a separately qualified
fresh final-fit and native-origin stage.
