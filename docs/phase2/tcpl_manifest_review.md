# TCPL audited-manifest binding

Completed 8 September 2026. `adaptation/tcpl_manifest.py` adds
`TCPLManifestRunner`, a bounded bridge from the existing Phase II audit to the
TCPL source and target helpers. It verifies trial/subject permissions at this
entry point before forwarding data or taking a source step. It is not the full
scientific training, selection and result-publication runner.

## Boundaries and data binding

The constructor takes the project root, trusted protocol configuration, trusted
catalog cohort, saved selection envelope, source model template and explicit
channel order. It reconstructs `source_selection` from the catalogs and compares
the entire saved envelope against that expected content. It checks dataset,
class order, complete subject/file inventory, preprocessing identity, threshold
configuration and model dimensions before creating the owned source trainer.

An optional inner-validation subject is excluded from `training_subjects` along
with the outer target. `source_step` rejects either held-out subject before any
artifact binding or model step. Outer-target prediction is unavailable on an
inner-validation runner; `predict_validation` accepts the configured held-out
source's episode record. Final outer-target prediction uses a separate runner
without an inner-validation subject.

Each execution reconstructs the requested nested episode from the pinned catalog,
protocol digest and full shot schedule. It verifies the entire supplied episode
envelope, not just its own hash. The caller cannot supply replacement trial
indices, arbitrary signal tensors, new labels or a subset of the common query set.

The loader checks the artifact's SHA-256, re-runs the existing audit reader, and
compares its trial IDs, labels and ordered montage with the trusted context.
It translates retained catalog indices back to original NPZ row indices, loads
those exact support/query rows, then rechecks artifact and threshold hashes.
The maximum support pool stays excluded from every shot condition's query set.
Class targets follow the catalog's declared order. Signals are cast to the model
device/dtype without new filtering, normalization or unit conversion.

`source_step` returns the episode digest, support/query IDs and detached loss
components after one owned Adam update. Prediction returns subject role,
episode/selection digests, class order, complete query IDs, logits and targets.
Query targets are returned for later scoring and never passed to target inference.
The source model template's prior training provenance remains trusted input;
this API cannot infer its training subjects from weights.

## Verification

Nine new tests and five subtests use real synthetic NPZ files and the actual
model/helpers. They check retained-to-original row mapping after rejection,
label ordering, an effective source update, unchanged caller/target source state,
and common queries at one and twenty shots. Rehashed record tampering, wrong
subjects, changed artifact bytes, changed thresholds, forged catalog labels,
reordered channels and protocol/cohort mismatches are rejected. Mocks verify
that invalid records/roles do not reach model execution; a changed final artifact
digest is also rejected before the source step.

An additional read-only real-data check reconstructed all **nine BCI IV 2a
catalogs and saved episode envelopes**, then verified the saved outer-source
selection. The bound subject-01 path used one support trial per class and
produced finite `[496,4]` logits for its entire common query set, with batch size
eight. **Zero real-data training steps** occurred; source weights and optimizer
state were unchanged. All nine input artifacts and the ten consumed audit records
retained their hashes.

This uses existing **Profile A** artifacts and an untrained local TCPL model.
It verifies identities and forward integration, not decoding performance, the
paper's preprocessing, or an accuracy result. No scientific score was calculated.
The historical audit's `unversioned-workspace` provenance was preserved; the new
check has its own real Git/source identity and does not relabel that old receipt.

Full lint passes; strict types pass for 148 source files. Regression output:

```text
419 passed, 3 warnings, 609 subtests passed in 26.63s
```

The three warnings are the existing EEGNet deprecation and classification warning.
The focused tests passed initially. Line wraps and an unused import were corrected
before final validation; no behavior or comparison tolerance was changed.

Evidence under `runs/phase2/tcpl_manifest_checks/20260908T141905740856Z/`:

- `receipt.json` and adjacent lint/type/test logs bind the checks to current source.
- `real_artifact_receipt.json` records input/audit/prediction hashes and scope.
- `real_artifact_check.py` and `untrained_bci_predictions.json` retain the exact
  bounded check and its query IDs, logits and targets.

Validation source fingerprint:
`29f519c22dab8f41a9706ddfee4a9a4307dd88010f580363e25fa1e4d1834192`.
Git HEAD is `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
All pre-existing source/config/test files retain their before-step hashes.

## Remaining scope and next step

The wrapper currently takes one subject episode per source step and reuses the
audited fixed-pool partition. This is an engineering integration policy, not a
frozen scientific meta-batch schedule. Support-ineligible MMIDB subjects remain
in the declared source cohort: this path rejects an unavailable episode rather
than silently removing a subject or reducing the maximum support pool. A general
source-episode policy for those cases is still needed before training.

Scientific preprocessing readiness, complete inner-fold selection, schedules,
checkpoint provenance and result publication remain outstanding. The next bounded
step is to bind checkpoint/run identity and publish verified prediction records
with safe resume behavior, keeping untrained engineering results distinct from
scientific evaluation cells.

Final free disk is 9.26 GiB, below the unchanged 20 GiB training floor. No heavy
training, scientific gate approval, author parity or source-bound control refresh
is claimed.
