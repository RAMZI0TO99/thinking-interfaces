# TCPL checkpoint and prediction publication review

The twelfth bounded step adds `evaluation/tcpl_publication.py`. It publishes
immutable local engineering predictions from the audited TCPL manifest runner.
It does not complete P2 or admit scientific training.

## Interface and publication order

`publish_tcpl_engineering_prediction(runner, episode_record, shots_per_class=...,
query_batch_size=8, reported_model_seed=None)` accepts a final outer-target runner.
The runner reconstructs the episode and checks the actual artifact before inference.
The publisher snapshots finite CPU float32/float64 model tensors as safetensors,
strictly restores those bytes into an isolated model copy, and predicts from that
copy using frozen support prompts. It never accepts caller-supplied predictions.

Run identity binds Git HEAD and dirty state, the source fingerprint, checkpoint,
protocol, selection, episode, artifact, preprocessing, method configuration,
runtime environment, montage, classes, shot count, query batch size and reported
seed. Missing real Git identity is rejected. Source, model, configuration, runtime
and input stability are checked again before writing.

Checkpoint bytes are written through a flushed temporary file and atomic
no-clobber link, then the persisted hash is verified. Only afterward does the
existing immutable record writer publish the completion JSON. Outputs are under
`runs/phase2/tcpl_engineering_predictions/{checkpoints,predictions}/` and named
by checkpoint/run hashes. Shared identical checkpoints are reused.

A repeat call revalidates inputs and recomputes predictions. Exact existing bytes
are accepted without changing modification times; conflicting bytes are preserved
and rejected, even when altered predictions have a newly calculated envelope hash.
An interrupted record write may leave a complete checkpoint, which alone does not
mark a run complete. Retry can reuse it. Concurrent checkpoint writers are tested;
this is atomic publication, not a job-claim lock or prevention of duplicate compute.

## Evidence

Nine new tests and five subtests cover exact restoration, identity separation,
repeat preservation, rehashed prediction/label/scope tampering, checkpoint tampering,
interrupted writes, invalid inputs, source-context drift and concurrent publication.
Existing model weights, modes, gradients, RNG and optimizer state are preserved.

The initial focused run had one concurrency failure and eight passing tests.
On Windows, concurrently resolving the same directory produced ordinary drive
and extended-length path spellings. The containment comparison treated those
equivalent paths as different. `_path_identity` now normalizes only comparisons
to the extended Windows namespace, including UNC paths; physical I/O paths retain
their resolved spelling. The concurrent-write and actual escape-rejection test
passes after this fix. Overwrite protection and containment remain enforced.

The real-data check reconstructed all nine BCI catalogs and episode envelopes,
verified the outer-source selection, and published untrained subject-01 logits
for all 496 common queries with one support trial per class and batch size eight.
The first publication was new; the second reproduced identical files and retained
their modification times. All nine input artifact hashes and ten consumed audit
record hashes were preserved. There were zero real-data training steps.

Full lint passes; strict types pass for 149 source files. Regression output:

```text
428 passed, 3 warnings, 614 subtests passed in 23.64s
```

The warnings are the existing EEGNet deprecation and classification warnings.
All pre-existing source/config/test files retain their before-step hashes.
Validation source fingerprint:
`8f06f3f62df988711715169302feb3cac132755bdf254341e45d0160186fe34f`.
Git HEAD is `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.

Evidence directory: `runs/phase2/tcpl_publication_checks/20260908T143306356068Z/`.
It contains `receipt.json`, lint/type/test logs, `real_publication_check.py`, and
`real_publication_receipt.json` with complete input and output hashes.

- Run: `4193f9672eb28e645da0371a3bd07b71ce642510ffbcc0dd27a67a349c44ff31`.
- Checkpoint: `638aa174b3b819f6e8172326fdb6c87b6c891628abc5c38af785d63b0d33801d`.
- Prediction file: `e1a400217f63371f11c6660f9613aa7d49517461a8209bb5df0570084718256e`.

## Boundaries and next step

Records are always `engineering_smoke`, with scientific evaluation, author parity,
checkpoint training-history verification and seed verification explicitly false.
A weight hash cannot prove prior training subjects or the seed that created those
weights. The optional seed is reported metadata. The checkpoint contains model
weights only, without optimizer state or source-training resume support.

This check uses existing Profile A artifacts and an untrained local TCPL model.
It does not establish paper-faithful preprocessing, accuracy, source-selection
completion or author parity. Historical audit provenance remains unchanged.
The source-bound control bundle still needs refresh before a checked commit.

Next is the plan's integrated P2 readiness review and representative pilot
specification: consolidate remaining common-runner, preprocessing, source-episode
policy and E1 feasibility gaps before measured P3 work. Final free disk is 7.69 GiB,
below the unchanged 20 GiB training floor. Heavy training and scientific gate
approval remain deferred.
