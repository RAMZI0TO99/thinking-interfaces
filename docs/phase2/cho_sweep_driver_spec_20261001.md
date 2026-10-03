# Cho first-tranche sweep driver specification

## Current implementation contract, 1 October 2026, 17:23 UTC

The user authorized the active 30-hour engineering session, ending
2 October 22:36 UTC. The [handoff](../../HANDOFF.md) records the current
audit/test state. Implementation is statically reviewed or under final
review; runtime verification and the first real case remain pending.

Actual execution uses `scripts/run_cho_first_tranche.py --mode execute`
and `evaluation/phase2_cho_execution.py`. Plan is the default, performs no
training and imports no tensor runtime. Execution requires independently
retained source/environment/route/configuration pins, a fresh affirmative
admission, an explicit bounded case roster, a new receipt and all limits.
The library sweep's strict verified resume is separate from the CLI, which
deliberately refuses implicit reuse. Attempt 2 requires a recorded failure
of attempt 1; partial durable parent attestations require deliberate recovery.

The complete route/selection/publication/target path runs in one supervised
Windows Job. A parent holds the canonical case lock, validates the staged
proposal against independent inputs and identities, and promotes a cell only
after normal timely child exit and full acceptance checks. Stopped attempts
retain their staged outputs and honest receipts. Shared guards and deadline
refusals stop the roster. Phase B analysis is a separate composer and is
explicitly unwired in this CLI.

The configured source-selection ceiling is 5,253 steps. The initial execution
probe accepts an explicit cap of at most 6 GiB **per-process committed memory**;
the Job peak is measured separately. This is an uncalibrated engineering
probe, not a ratified production training cap. The existing 5.5 GiB cap applies
to analysis children. Execution keeps the 10 GiB launch RAM, 4 GiB active RAM,
20 GiB disk, 600-second whole-case and 7,200-second session limits; no automatic
increase is allowed. Scientific freeze and Gate A remain open.

The historical design below preserves earlier assumptions. Its 256-step
ceiling, automatic failure advancement, analysis wiring and test assertions
do not describe the current execution path.

## Historical design snapshot

1 October 2026. **Design only; nothing here authorizes execution.** This
specifies the orchestration layer that turns the already-verified per-case
machinery into a resumable 1,040-case sweep driver. Every heavy component
exists and is tested: the route
([prepare_cho_first_tranche](../../evaluation/phase2_cho_case_inputs.py)),
the source selectors with their hard engineering ceilings
([BCIEEGNetSourceSelector](../../adaptation/source_selection.py) and the
LaBraM equivalents), the selected-source publication gate, the
[TargetCaseExecutor](../../evaluation/phase2_pilot.py) with its explicit
operator compute admission, the recorder's claim/retry/cell discipline, the
isolated per-case analysis children, and the paired-input composer with the
aggregation core.

## Hard gates the driver must preserve

1. **Operator admission.** `compute_admission(operator_admitted=...)`
   requires an explicit boolean plus live machine guards. The driver takes
   a persisted admission record (operator name, timestamp, admitted flag,
   cap values) written before the sweep starts; a sweep receipt without that
   record is refused. Building the driver does not create this record.
2. **Selector ceilings.** The engineering executors cap gradient steps at
   256 per fit and 32-trial batches. The declared candidates' full protocol
   sums to 5,253 steps per case; running that is an owner decision recorded
   in configuration, not a driver default. The driver runs whichever
   selector configuration it is given and records its digest.
3. **All-or-nothing analysis.** Cells are per-case and resumable; paired
   inputs are constructed only when every case's cell and selected-source
   witness verify, through the already-applied supervised child path under
   the ratified memory cap (5.5 GiB recommended, 2.07x over the measured
   2.657 GiB peak at `4542cc11`).

## Driver shape

- New module `evaluation/phase2_cho_sweep.py` plus an operator CLI
  `scripts/run_cho_first_tranche.py`; configuration pinned under
  `configs/phase2/` (admission-record path, selector configuration digest,
  case order, memory cap, attempt policy).
- Phase A, per case in canonical roster order: admission re-check, source
  selection under the configured executor, selected-source publication,
  then `TargetCaseExecutor.run_case`. The recorder's existing claim and
  retry accounting bounds attempts; completed cells short-circuit on
  resume. Failures record a reason and advance; the roster is not aborted
  by a single failed case, and the final receipt states the exact
  completed/failed partition.
- Phase B, once: the verified analysis composer over all 1,040 cells
  through the supervised children (cap from the pinned configuration),
  then the pure subject aggregation core. Phase B is all-or-nothing by
  construction.
- One write-once sweep receipt directory under `runs/phase2/sweeps/`:
  the admission record digest, per-case outcomes with cells or failure
  reasons, the analysis paired-input digest, per-case measured analysis
  peaks, and the explicit `scientific_claims_made` boundary fields.

## Verification before implementation is considered complete

- Unit tests with synthetic adapters and a fixture recorder: roster
  ordering, resume-after-interruption skipping completed cells, admission
  refusal without the record, failure-advance semantics, and receipt
  completeness. No test trains a real model.
- The driver's own quality cycle: Ruff, strict mypy, focused tests, then
  the standard pinned raw-audit + guarded-quality chain for the new
  source fingerprint.
- The scientific boundary: a completed engineering sweep under the 256-step
  ceilings is engineering evidence, not a ratified scientific result; the
  freeze, Gate A and any full-protocol selector run remain owner decisions.
