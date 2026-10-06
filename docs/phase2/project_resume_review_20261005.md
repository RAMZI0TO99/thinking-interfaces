# Project review and engineering resume, 5 October 2026

Current update, 6 October 06:00 UTC: the package milestone completed and was
published as `ee5c278`; root closeout and explicit scope release are linked in
[HANDOFF.md](../../HANDOFF.md). Source hashing rechecked `b7452847`/431 files.
The v3 deadline, 5 October 22:40 UTC, is expired; new deadline/peer bindings,
fresh operation review and compute coordination are required. The RAM sample
was 3.23 GiB against the unchanged 10 GiB heavy startup floor. No new controls,
raw verification, measured environment, full interoperability or real LaBraM
case is accepted. The review below retains the 5 October evidence boundaries.

Thinking Interfaces is a substantial EEG decoding and adaptation research
harness. The core question is whether pretrained LaBraM with controlled
target-support adaptation improves cross-subject motor-imagery decoding.
Cho2017 is primary; BCI IV 2a and MMIDB are secondary. A separate live/replay
interface uses causal buffering, confidence gates and visible output frames.

Five parallel reviews covered architecture, local evidence, Windows launcher
contracts, scientific readiness and regression coverage. The findings below
come from current source and local receipts, not an external literature review.

## Implemented flows and evidence boundaries

| Flow | Current implementation | Accepted boundary |
|---|---|---|
| Data | Loaders, channel identities, artifact rejection, immutable Profile A/B inputs | Raw verification exists for the 4 October source; new sources need matching evidence |
| Protocol | Nested 1/5/10/20-shot support, common query pool, source/target exclusion, source-only selection | Tested protocol; scientific freeze remains unsigned |
| Methods | LaBraM linear/partial/full tuning, QKV LoRA, adapters, prompts; local TCPL; EEGNet and classical anchors | Source/test integration exceeds real-case evidence |
| Cho execution | Selection, verified source publication, target adaptation, immutable cell recorder, supervised Windows Jobs | One accepted EEGNet engineering case |
| Analysis | Complete-roster paired-analysis preparation and pure statistical calculations | Proposed 1,040-cell comparison remains unstarted |
| Interface | LSL/replay input, causal buffers/windows and confidence/accumulation gates | Buffer causality does not certify complete causal preprocessing or hardware deployment |

Useful implementation entry points are `evaluation/phase2_protocol.py`,
`evaluation/phase2_cho_sweep.py`, `evaluation/phase2_cho_execution.py`,
`evaluation/phase2_runner.py`, the `adaptation/` and `encoder/` packages,
and `realtime/`. Current integration includes modules older September draft
reviews called unimplemented; those drafts remain historical.

The 4 October source `62536382` has guarded quality evidence: lint/types pass,
1,041 tests pass, three Windows symlink-privilege skips, and 1,121 subtests pass.
Its controls passed 45/45 and 36/36; 52 raw sources were verified. The sole
accepted real case is EEGNet / subject_01 / seed 11 / five shots / repetition 1,
balanced accuracy 79/160 = 0.49375. That case used short engineering updates and
declared `engineering_only=true`, `scientific_evaluation=false`. It establishes
execution integrity; it cannot establish convergence, population performance
or comparative benefit. New named-Job tests change the source fingerprint, so
the historical quality/controls/environment chain is not certification of the
new tree. The new source `b7452847` now has its own independently audited
guarded quality pass: lint/types exit 0, 1,048 tests passed, three skips and
1,121 subtests passed. Controls, raw and measured-environment evidence still
need refresh on this source before the next case.

## Scientific decisions still required

Scientific Gate A has audited reproduction evidence, but no prospectively
adopted acceptance tolerance. A descriptive published standard deviation is
not an acceptance threshold. The historical environment correspondence has
remaining uncertainty; see [Gate A status](../gate_a_status.md).

The scientific protocol and experiment freeze remain unsigned. The proposed
primary comparison is LoRA minus linear at five shots, using per-subject means
over five seeds. The proposed first tranche contains 52 subjects, four methods
and five seeds: 1,040 cells. Scientific interpretation and search/inference
families require owner decisions; engineering delegation signs neither gate.

The current committed selection ceiling is 5,253 gradient steps. Older
256-step blockers are superseded historical statements, not current readiness
findings. TCPL remains a local reconstruction with unresolved author-model
correspondence; E1 tokenizer/masked-loss feasibility and causal E3/hardware E4
evidence remain separate unfinished work.

Static tracing of LaBraM linear found no concrete route leakage or identity
defect: the outer target is excluded from 51 source subjects, each inner
held-out source is excluded from training, support/query are disjoint, and
the 102 candidate/fold pairs bind the winner, settings and model digest.
This is source review, not execution. The pretrained checkpoint declares
`prior_template_training_verified=false`; its training cohort is unverified
and scientific independence from Cho cannot be inferred.

## Repairs completed in this bounded phase

The V10 native launcher checked `completion.measured_cases`, while the recorder
emits `completion.measured`. A fresh V11 historical-baseline template corrects
that field, two stale cap descriptions, and four bounded staging deadline
sites. Fifteen tests evaluate the actual extracted PowerShell predicate;
independent review verifies exact reversible substitutions and accepts only
static/native contract scope. V10, its native failure and the accepted recorder
cell remain intact. [Build and validation instructions](native_launcher_contract/README.md)
are tracked; the historical runtime inputs remain local and ignored.

Seven named-Job regression cases protect per-instance `create_job` injection,
restoration on success and exception, default dispatch using the contract name,
missing-name refusal and explicit custom supervision. Production implementation
is unchanged. Static review and native Ruff pass; all seven cases passed in
the guarded full suite. Its 1,737.11-second run retained the exact source,
minimum available RAM 10.188 GiB and disk 239.424 GiB; native physical exit,
independent audit, scoped process cleanup and peer release are recorded in
the current handoff. The interrupted first full attempt and three failed or
refused focused attempts remain intact, without inferred passes.

The old case witness map has 116 entries; 115 currently match. Its mutable
session ledger changed during closeout. Historical acceptance was contemporaneous,
but the complete chain cannot now be replayed from the live ledger. Future
boards should bind immutable writer-execution receipts. The old audit's count
of 130 has no located corresponding map and should not be repeated as the
child-map count. Its actual memory caps are 6 GiB per process and 7.5 GiB aggregate,
despite preserved stale prose in the old completion receipt.

## Ordered engineering continuation

1. The [separate LaBraM linear supervisor](labram_linear_supervisor/README.md)
   is now built for subject_01 / seed11 / five shots / repetition1. It passed
   131 native checks, including 72 extracted-predicate fixtures, and isolated
   syntax compilation of generated parent/child/raw-verifier code. Independent
   review accepts static/bounded fixture evidence, zero blockers; real process
   interoperability remains unexecuted.
   V11 stays fixed to the historical EEGNet case.
   The v3 deadline has now expired. Before continuation, rebuild in a fresh
   directory with current finite deadline/peer/source bindings and independently
   validate/audit the exact new operations under fresh coordination.
2. Refresh source-bound controls, raw verification, measured environment and
   immutable prerequisite audits on the settled source/Git state. Obtain a new
   scoped release and fresh attempt paths; no old board or grant can be reused.
3. Measure the LaBraM runtime/memory envelope within reviewed limits before any
   expansion. EEGNet's measured envelope is not a LaBraM measurement. A matched
   LoRA engineering case can follow after its own admission.
4. Resolve scientific Gate A/freeze and checkpoint-cohort decisions before interpreting a broad
   comparison as research evidence.

The morning repair phase completed before its internal 10:00 UTC cap. The
evening continuation closed at 19:29 UTC on 5 October; its internal 22:40 UTC
preparation cap elapsed and was not a new owner window or compute lease. The
6 October RAM sample remains below the 10 GiB heavy startup floor; no fresh
heavy interval or case release has been obtained. Native checks and the
separate isolated syntax check completed under fresh exact peer responses,
physical witnesses and explicit releases. Current authority and receipts are
in [HANDOFF.md](../../HANDOFF.md) and
`runs/coordination/labram_linear_prep_20261005_v1/`. Historical receipts, raw data,
weights, peer edits, WSL and shared services remain preserved.
