# Cho isolated tensor-case execution plan

30 September 2026. **Engineering design only; no supervision, composer or
measurement code changed by this note.** The [tensor-state review](cho_selected_tensor_state_review_20260930.md)
leaves three requirements open before a real 1,040-case analysis sweep:
a verified Job Object memory cap, a measured LaBraM peak commit, and a
one-case isolated process lifetime. This plan specifies those changes.
Implementation must wait until the pinned
[raw audit](../../runs/phase2/freeze_readiness/20260930_08751a39_raw_source_readonly/verify_raw_sources.py)
and [guarded quality](../../runs/phase2/quality_attempts/20260930_tensor_state_08751a39_guarded/run_guarded_quality.py)
runs complete for source `08751a39`, because any source edit repins both.

## Existing primitives

[Supervision primitives](../../evaluation/phase2_supervision_primitives.py)
already provide `run_supervised`: a suspended `CreateProcessW`, assignment to
a private Job Object carrying only `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`,
query-back verification of that flag, persisted
[deadline leases](../../evaluation/phase2_case_transaction.py) with attempt and
session caps, and live resource-floor guards before launch, before resume and
throughout supervision. The [synthetic case transaction](../../evaluation/phase2_case_transaction.py)
demonstrates an owned child result channel: the child publishes a witness
through exclusive-create writes that the parent verifies against pinned
digests. The composer currently calls the tensor helper sequentially in its
own process.

## Proposed design

1. **Verified process-memory cap.** Extend `run_supervised` with an optional
   `process_memory_limit_bytes`. When set, populate
   `BasicLimitInformation.ProcessMemoryLimit` and add
   `JOB_OBJECT_LIMIT_PROCESS_MEMORY` (`0x100`) to the flags, then require the
   post-set query-back to echo **both** the flag and the exact limit value,
   mirroring the existing kill-on-close verification. Refuse to launch on any
   readback mismatch, a zero or non-finite requested cap, or a cap the host
   cannot represent. A per-process bound is the correct first cap for a
   single-root child; `JOB_OBJECT_LIMIT_JOB_MEMORY` can bound a multi-process
   tree later if a case ever spawns helpers. A child that exceeds the cap sees
   commit failures, so any child error remains a whole-case refusal under the
   composer's existing all-or-nothing rule.

2. **Measured peak commit.** After a supervised child completes, query the
   job's `JOBOBJECT_EXTENDED_LIMIT_INFORMATION` for
   `PeakProcessMemoryUsed` and `PeakJobMemoryUsed` and record both in the
   supervision result. Measure a real LaBraM `full_v1` tensor case (the
   largest architecture in the tranche; the
   [sizing probe](cho_selected_source_storage_review_20260923.md) measured
   about 23.3 MB of LaBraM weights against 12.7 KB for EEGNet, but peak commit
   must also cover decoded evidence, safetensors buffers and runtime state),
   plus one case of each remaining method. Set the production cap above the
   highest observed peak with an explicit safety factor recorded in the
   analysis receipt, then confirm in a synthetic soak that the cap admits
   every healthy case. The host-side 6 GiB before / 4 GiB during floors stay
   unchanged.

3. **One case per child.** Replace the composer's in-process case loop with a
   per-case child: the project Python runs a small entrypoint that performs
   exactly one `verify_cho_selected_source_state` call and publishes the
   digest witness through an exclusive-create result file under a persisted
   deadline lease, the resource floor and the verified memory cap. The parent
   verifies each child's receipt schema, source stability and witness digest,
   requires a present measured peak under the cap, and treats any child
   failure, deadline expiry or cap breach as a roster-wide refusal. The
   measured per-method peaks are recorded by the measurement probe's receipt
   and by the future sweep runner's receipt, not threaded through the
   composer's return value. Cases stay strictly
   sequential; paired inputs are constructed only after all 1,040 child
   witnesses pass, and physical file witnesses are rechecked afterwards as
   today.

## Verification before implementation is considered complete

- Unit tests for cap validation and the query-back refusal path, including a
  mismatched echoed limit, without launching a child.
- A Windows-only integration test whose child allocates past a deliberately
  small cap and must fail, and whose well-behaved child must pass with
  recorded peaks not exceeding the cap; skipped on non-Windows hosts.
- Extend the composer test with a mock at the new child-invocation boundary:
  exact per-case commands, ordering before score extraction, all-or-nothing
  on child failure, and per-case peak recording. Reuse the existing real
  synthetic EEGNet publication as the child workload for one end-to-end
  supervised case.
- Full focused Ruff and strict mypy, then a fresh pinned raw-audit and
  guarded-quality pair for the new source fingerprint in new dated
  directories.

This design bounds each case's memory and lifetime without weakening any
guard, the 256-step selector cap or the all-or-nothing admission rule. It
does not run a real Cho fit, verify the complete selector, replay historical
inference, ratify the method template or scientific freeze, or sign Gate A.

## Prepared implementation detail (30 September, pre-implementation)

The existing `_ExtendedLimit` ctypes structure already declares
`ProcessMemoryLimit`, `JobMemoryLimit`, `PeakProcessMemoryUsed` and
`PeakJobMemoryUsed`, and both supervised runners already set and query back
`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. The verified-cap change is therefore:

1. New constant `JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100`.
2. `run_supervised` and `run_supervised_with_frame` accept
   `process_memory_limit_bytes: int | None = None`; validation requires a
   real `int` (bool rejected), finite, `0 < value` when supplied. The set-job
   flags become `KILL_ON_JOB_CLOSE | PROCESS_MEMORY` with
   `ProcessMemoryLimit` populated, and the existing single-flag equality
   check generalizes to expected flags plus an exact echoed-limit comparison;
   any mismatch refuses before the suspended child is created.
3. `SupervisionResult` and `FramedSupervisionResult` gain defaulted
   `peak_process_memory_bytes`/`peak_job_memory_bytes` fields, populated by a
   final job query after the owned tree completes; they stay `None` when no
   cap was requested (Windows tracks the peaks once a memory limit is set).
4. Tests follow the module's real-child pattern: invalid-cap validation
   refusals (zero, negative, bool), a small real child under a generous cap
   whose measured peak is reported and under the cap, an over-cap child that
   fails on commit (allocation error surfaced as a non-zero exit), and a
   monkeypatched query-back mismatch that must refuse without creating the
   child, mirroring `test_failed_job_assignment_never_runs_suspended_child`.

The peak fields feed the measured-commit receipt for item 2 of the proposed
design; nothing here alters deadlines, resource floors or stop reasons.

### Per-case child protocol (for the composer rewiring)

The child entrypoint is versioned source (``scripts/``), so the pin cycle
covers it. One child performs exactly one tensor-case verification:

- Input: a caller-written JSON file in a per-analysis scratch workspace,
  carrying the case id and every independent pin the in-process helper takes
  today (method config object, digests, candidate, manifest/evidence digests,
  protocol config, recipe and checkpoint digests) plus the workspace path.
- Work: call ``verify_cho_selected_source_state`` unchanged, so the helper's
  own 6 GiB-before / 4 GiB-during RAM checks and bounded reads still run.
- Output: an exclusive-create witness JSON in the same workspace: schema
  tag, case id, the frozen digest witness, and no adapter or model object.
- Parent: run under ``run_supervised`` with a per-case deadline lease, the
  live ``ResourceFloor``, and the measured cap; require exit 0, the exact
  witness schema, matching case id and digest, cap respected, and source
  stability after the roster. The composer treats any child failure, lease
  expiry or cap breach as a roster-wide refusal (all-or-nothing preserved).

The composer accepts an injectable case-executor callable so tests mock at
exactly this boundary, mirroring today's tensor-helper mock; one real
supervised EEGNet child end-to-end remains in the focused tests.

## Application runbook (after the `08751a39` pinned cycle concludes)

Drafts live in `runs/drafts/isolated_case/` and are verified there (see the
deviation log, 30 September). Apply only when the current source's pinned
raw audit and guarded quality are finished, because application repins:

1. Copy `phase2_supervision_primitives.py` over
   `evaluation/phase2_supervision_primitives.py`; move
   `run_cho_tensor_case_child.py` to `scripts/`; copy
   `phase2_cho_analysis_preparation.py` over
   `evaluation/phase2_cho_analysis_preparation.py`.
2. Move `test_job_memory_cap_draft.py` content to
   `tests/test_phase2_job_memory_cap.py` against the real module import;
   merge the composer-test edits: retarget the tensor mock to
   `run_cho_tensor_case_child`, add `case_workspace` (tmp dir) and a positive
   `case_memory_limit_bytes` at every composer call site, and add the new
   child/executor tests from `test_composer_child_draft.py`.
3. Gates, in order: Ruff over changed files, strict mypy over changed files,
   supervision tests, cap tests, restore/store focused tests, then the full
   composer suite. Record the new fingerprint.
4. Run the [peak-commit probe](../../runs/phase2/case_memory_measurements/20260930_peak_commit_probe/measure_peak_commit.py)
   and record its receipt; choose the production cap above the highest
   measured peak with an explicit recorded safety factor.
5. Prepare fresh dated pinned directories for the new fingerprint (raw
   audit, guarded quality, control inventory, no-future check) by copying the
   current wrappers and repinning `SOURCE`; never reuse a written directory.
6. Update the deviation log, tensor-state review, `PHASE2_START_HERE.md` and
   `HANDOFF.md` with the new fingerprint, receipts and boundaries.

## Application status (30 September, late)

Steps 1-3 of the runbook are complete at source
`cb6eb49a2ff0ec04557e58b5729e2df8af19e3218f246d631915e709d26eda44`:
Ruff, strict mypy, supervision/cap/child/transaction tests (51 passed,
1 symlink skip, including the real supervised EEGNet child), restore/store
focused tests (39/29) and the full composer suite (5 tests, 575 s) all
pass. The exact-source raw audit passed (52 sources,
10,704,036,837 bytes). Step 4's probe and the step-5 pinned wrappers for
this source follow the current guarded quality attempt. The child's input
accepts an optional `root` used only by the supervised-child tests; the
production executor always passes the reviewed project root, and the child
interpreter and entrypoint always come from the running project.

## Measured peaks and production cap (30 September)

The [probe receipts](../../runs/phase2/case_memory_measurements/20260930_peak_commit_probe_4542cc11/receipt.json)
measured, under the verified 8 GiB probe cap with every child exiting 0:
eegnet 2.545, labram_full 2.627, labram_linear 2.628 and labram_lora
2.657 GiB peak process commit at the settled source `4542cc11` (an earlier
`cb6eb49a` probe measured 2.545-2.667 GiB consistently). A production cap
of 5.5 GiB would carry a 2.07x explicit safety factor over the 2.657 GiB
maximum while remaining below the 6 GiB host-RAM-before-case floor the
tensor helper already enforces. This recommendation is engineering
guidance only; the sweep owner ratifies the cap in the sweep runner's
pinned configuration before any real case runs.
