# Proposed linear target route

Preparation only, 15 October 2026. The accepted
[recorder](cho51_linear_recorder_qualification_20261015.md) has one engineering
success and zero measured cells. Its reused source work comprises 102 folds,
51 final-source subjects and 5,253 historical updates (5,151 source, 102 support).
Target adaptation/query inference remain unqualified.

## Proposed implementation

Create separately versioned `cho51_linear_target_route_v1` sources, tests and
coordination/runtime bundle; review exact bytes before launch. Reuse accepted
publication/restoration/recorder proofs by digest, with no source replay.
A fresh bounded restore needs its own counters and witness.

Admit only Cho2017 / subject_02 / labram_linear / five shots per class / seed 11 /
repetition 1, on the preserved synthetic fixture.
Reconstruct selection, catalog and episode through
[`source_selection`, `nested_episode`, `EpisodeManifest.partition`](../../evaluation/phase2_protocol.py)
and [`load_cho_profile_b_episode`](../../evaluation/phase2_profile_binding.py).
The 42-trial, two-class fixture with shot levels 1/5/10/20 yields ten support
trials, two fixed query trials and 30 unused maximum-support-pool trials.
Bind A/B hashes, rows, trial IDs, labels and 60 Hz manifest; reject overlap or
reordered IDs. Profile A is 64 x 512; Profile B is 64 x 800.

Use [`LaBraMTunedAdapter.predict_target`](../../evaluation/phase2_pilot.py) and
[`LaBraMTuningManifestRunner.predict_target`](../../adaptation/labram_manifest.py)
with the selected support settings: linear, one step,
learning rate 0.001, no partial depth, query batch size 8. The proposed budget is
zero source updates and exactly one support SGD update. Through
[`adapt_labram_tuning_support` / `configure_labram_tuning`](../../adaptation/labram_tuning.py),
clone the source, retain eval mode and train only `head.weight` and `head.bias`
(402 parameters). Require finite gradients and changed head; backbone, buffers
and immutable 223-tensor source remain exact.
Queries run in inference mode after adaptation; labels enter only evaluation,
never selection, loss, optimizer, stopping or hyperparameter choice. Unused
pool trials never enter adaptation.

## Admission and evidence

Historical provenance stays `4491e2a...`, dirty=true; the
accepted recorder separately records `277d7975...`, dirty=true. Capture and pin
the new actual Git context, source files, runtime, environment, baseline and
checkpoint separately from history. Preserve canonical 432 sources and prior
proofs. The two-root staged bridge does not qualify single-root factories.

Any later numerical attempt requires a fresh named Windows Job: 600 seconds,
4,096/5,120 MiB process/Job, 10/4 GiB startup/active available RAM, 20 GiB disk,
Torch threads 1/1 and hidden GPUs. Check all four genuine pause files under
`D:/Aenv/pro2/WORK/resume-{20261007,20261012,20261013,20261015}-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json`
before/during work. Retain write confinement, bounded loads, input hashes
before/after, numerical counters and empty/closed/absent Job proof. A refusal
requires separate repair before another attempt.

Test query-label leakage, wrong plan, partition tampering, frozen-state drift
and provenance separation; then require actual tensor/adapter witnesses under
the fresh guard. Engineering attestation only: measured cells and original
scientific attempts stay zero.
[`TargetCaseExecutor.run_case`](../../evaluation/phase2_pilot.py) calls
`record_cell`; do not call it unchanged for this engineering case.
Later inspect worker
[`prepare_cho51_worker_route` / `inputs_for`](cho51_worker_bridge_v1/worker_bridge.py)
and [`verify_case_target_inputs`](../../evaluation/phase2_cho_execution.py),
without expanding this case to the 1,020-cell worker.

Next: implement and review the target-route contract, tests and guard before
execution. Scientific admission, final owner freeze, cohort/prior-training
lineage and full worker qualification remain pending. No peer release or new
autonomous window is inferred.
