# Thinking Interfaces

Phase I builds a reproducible EEG-decoding harness and a working real-time demonstration. Research claims begin only in Phase II.

Current engineering status (7 October 2026): source `b7452847…` remains unchanged across 431 canonical files, with the independently audited 5 October quality pass: lint, strict types, 1,048 tests and 1,121 subtests. The sole accepted real case remains the historical EEGNet engineering case on `62536382…`. Scientific Gate A and the experiment freeze are unsigned. See [HANDOFF.md](HANDOFF.md) for the current evidence and next steps.

The original full45 controls now passed on the current source, and root
accepted the independent 2,557-check saved-results review. The separate full36
attempt reached its new external500-second deadline during the required raw
writer check. Its owned processes were reaped and its private Job closed;
available RAM stayed above14.704 GiB. The spent attempt produced no accepted
36-control result. A fresh reviewed whole-cohort runner must account for the
original writer1800/matched7200 ceilings. No automatic retry is admitted.

The [LaBraM linear supervisor recipe](docs/phase2/labram_linear_supervisor/README.md)
has prepared a new v2 case package with a finite16:20 UTC cap. Its package and
v3 validation watchers passed2,148 independent source checks. Current native
fixtures, isolated compilation, immutable writer evidence, raw52 verification,
final measured environment, the complete board and a separately released
LaBraM engineering case remain outstanding. These source checks certify no
LaBraM result. See [HANDOFF.md](HANDOFF.md) for exact evidence and peer scopes.

Historical 7 October11:07 preparation: the earlier v1 package passed131 native
checks/72 acceptance fixtures and isolated compilation of three targets, with
394 package and40 syntax-result review checks. Its14:30 UTC cap has expired.
Those receipts certify only that earlier package. Historical packages and
the accepted EEGNet cell remain preserved.

The project repository is [RAMZI0TO99/thinking-interfaces](https://github.com/RAMZI0TO99/thinking-interfaces), created as a private repository on 3 October 2026. It preserves the local Git history and publishes the source, configurations, tests and project documentation. Read [HANDOFF.md](HANDOFF.md) for the current validation limits.

Links into `runs/`, `artifacts/`, data caches and checkpoints refer to local evidence or external inputs. These files are intentionally excluded from Git; the repository alone does not contain the runtime receipts, EEG datasets or model weights needed to reproduce every historical run. Historical passing records do not certify the current source. No new validation or experiment is authorized by repository publication.

The day-by-day and v2 research plans are historical/proposed documents. Their inclusion does not sign Gate A or the experiment freeze; use the current handoff to distinguish plans from executed and accepted evidence.

## Phase I lanes

| Lane | Directory | Responsibility |
|---|---|---|
| Lead | `core/`, `configs/` | Contracts, run records, configuration, metrics, CI, gates |
| Encoder | `encoder/` | LaBraM loading, electrode mapping, depth controls |
| Adaptation | `adaptation/` | Episodic protocol, LoRA, adapters, prompt generator |
| Data | `data/` | Dataset loaders, channel canonicalisation, preprocessing |
| Real-time | `realtime/` | LSL, causal buffering, gating, interface |
| Shared evaluation | `evaluation/` | Baselines, leakage tests, statistics, figures |

## Non-negotiable rules

- Every experimental parameter comes from a committed configuration file.
- Every result is associated with a `RunRecord` containing its configuration, seed, Git commit, dataset, fold, metrics, and timestamp.
- Raw data, processed data, credentials, weights, and run outputs are never committed.
- Source and target subjects must be disjoint in every cross-subject split.
- Support data may change a model; query data may only evaluate it.
- Phase I Gate A must pass before later results are treated as interpretable.

The local Git history begins at `bf78379b6ec67a6fef3db83d8e3c34f37b35299b`.
Runs made before versioning keep their original explicit unversioned identity;
they are not retroactively attributed to this commit. New benchmark runs capture
the current commit, a source/configuration fingerprint and dirty-state flag.
Reused deterministic fits keep the original fit's provenance. These source
changes were created by the assistant and retain their original local history. Most snapshots
use `Codex <codex@localhost>`; commit `659949a` inherited Git's automatic local
identity. Commit metadata is not evidence of manual user review or gate approval.
The final plausibility audit retains 1,051 legacy unversioned records and 4,899
records with source fingerprints; it does not rewrite either group. A separate
45/45 control bundle verifies the historical Phase I source snapshot.
Milestone 51 supplied a matching 45/45 bundle for its Phase II source snapshot.
The later Cho 60 Hz source/config/test edits require another matching refresh.

## Current status

**8 October 2026, resumed prerequisite validation.** The original full45
cohort passed on current source `b7452847`; the accepted 5 October quality
pointer remains unchanged. Full36 has no accepted current-source result:
one attempt reached its initial deadline, one lost its controller during a
daemon restart, and one exceeded its revised deadline during overnight host
sleep. All recorded PIDs are absent; the independent saved review accepts
refusal evidence only and discloses missing cleanup certifications. Historical
LaBraM package preparation passed native131/72 checks and three-target isolated
compilation; its runtime deadline expired. Fresh source preparation is admitted
through 8 October10:00 UTC, with separate coordination and resource admission
required for full36, immutable all9 writer, raw52 and the eventual single
LaBraM engineering probe. No LaBraM result is claimed. The sole accepted
EEGNet case remains79/160; Gate A and the scientific freeze are unsigned.
See [HANDOFF.md](HANDOFF.md) for exact receipts and current next steps.

**5 October 2026 — engineering repairs validated.**
Five parallel reviews confirmed the accepted 4 October EEGNet engineering
case. A reversible V11 launcher repair template is independently accepted for
static/native contract scope, with 15/15 predicate checks. The guarded full
suite passed on the changed test-inclusive source `b7452847`: lint/types exit 0,
1,048 tests passed, three Windows privilege skips and 1,121 subtests passed.
Independent audit accepted the quality result and physical cleanup is confirmed.
The V11 template remains unadmitted and is not a next-case runner. See [HANDOFF.md](HANDOFF.md)
and the [repair recipe](docs/phase2/native_launcher_contract/README.md).
The accepted case remains 79/160; Gate A and the scientific freeze are unsigned.

The 14:25 checkpoint below is historical; its staged chain completed that evening.

**4 October 2026, 14:25 UTC — qualification PASSED, source repaired (`62536382`), first case staged behind one RAM window.** The Windows-qualification ceremony passed all three scenarios (root-accepted, audited zero blockers), the Torch environment pin was measured and audited, and the first real Cho engineering case ran its full supervision chain to the innermost child — exposing the same host-Job defect in project source, now repaired with the twice-proven named-Job pattern, verified live and re-audited (`ACCEPTED_SOURCE_REPAIR_VERIFIED`). The remaining chain (quality pass on the new pin → fresh env pin → prerequisite board → case relaunch) is fully staged; a patient auto-retry fires the moment the machine's interactive WSL session stays down for a minute with the 10 GiB floor clear. Gate A and the experiment freeze remain unsigned; no scientific result is claimed. See the [session ledger](runs/coordination/session_20261004_next.json) and [HANDOFF.md](HANDOFF.md).

**Historical 3 October 2026, 23:40 UTC — validation chain green on `88de6af5`; qualification blocked by a now-isolated host-Job defect.** In the user's 12-hour window: guarded full-quality pass (lint 0 / strict types 0 / 1041 tests, [audited](runs/coordination/next_step_20261003_quality/quality_pass_audit_001.json), pointer published), 45/45 source-bound controls, 36/36 no-future controls (0.2451 < 0.35), and the current-source raw audit all completed and are pushed. The sealed Windows-qualification V3 package executed twice and failed for a genuine environment reason: this host jobs every process (0x3000) and the frozen ceremony's child-side NULL-handle Job query returns the host Job, so its verification can never pass — [root cause + validated named-Job repair](runs/coordination/windows_qualification_20261003_v3/host_job_conflict_root_cause_001.md) (also explains TYPE001). Next session: V4 repair, then the first-case chain. See [HANDOFF.md](HANDOFF.md).

**Historical 3 October 2026, 18:11 UTC — stopped:** The final TYPE005 attempt hit its session deadline and produced no completed mypy result. Its native command exited 1 in 96.922 seconds, within the 120-second limit; scoped cleanup and peer release are confirmed. The [independent failure audit](runs/coordination/next_step_20261003_types5/type_execution_audit_001.json) and [root closeout](runs/coordination/next_step_20261003_types5/root_manual_failure_review_001.json) accept failure evidence only; no new component, type or runtime pass is claimed. Work is stopped at the user's request, with no retry or next phase queued. The original goal is already complete and no active goal remains. Full QA/Windows, the failed quality pointer, 10 GiB floors and unsigned scientific gates remain unchanged. See [HANDOFF.md](HANDOFF.md).


**Historical 17:41 UTC TYPE005 static readiness:** The [three static reviews and root readiness](runs/coordination/next_step_20261003_types5/preparation_ready_001.json) accept the repaired package with all 16 artifact pins verified. Root requested a fresh 17:45–18:00 peer grant; no grant, admission or attempt005 exists yet. Physical admission and fresh resource/time checks remain required. The unchanged source is `423faa13`; actual TYPE004 mypy exit 0 for 205 files remains qualified by its native gate failure. Full QA/Windows and science gates remain pending. See [HANDOFF.md](HANDOFF.md).


**Historical 17:30 UTC preparation checkpoint:** TYPE005 is preparing the reviewed native deadline precision
repair under its [new finite phase](runs/coordination/next_step_20261003_types5/phase_plan.json),
with an internal 18:30 UTC cap. The [TYPE004 actual audit](runs/coordination/next_step_20261003_types4/type_execution_audit_001.json)
and [root manual review](runs/coordination/next_step_20261003_types4/root_manual_failure_review_001.json)
confirm the 800 ns witness mismatch and preserve mypy exit 0 for 205 files versus
native exit1/full component unaccepted. The project source remains unchanged at `423faa13`.
The [independent native patch review](runs/coordination/next_step_20261003_types5/native_deadline_patch_audit_001.json)
accepts static evidence only: flooring to microseconds advances the deadline
0 to 900 ns earlier, while retaining exact equality and all limits.
New package, candidate and helper reviews, a genuine grant005 and actual admission
are still required. No attempt005, Python, mypy or Job has launched. The failed
quality pointer, heavy 10 GiB floors, unsigned scientific gates and zero accepted
real cases remain; no renewed 30-hour session or compute lease is inferred.
See [HANDOFF.md](HANDOFF.md).

**Historical17:00 UTC TYPE004 checkpoint:** TYPE004's actual mypy API returned 0:
[no issues in 205 source files](runs/phase2/type_validation/pro3_types_20261003_004/mypy.stdout.log).
The [child result](runs/phase2/type_validation/pro3_types_20261003_004/result.json)
records matching `423faa13` before/after source pins and valid private-Job
membership. The native wrapper nevertheless exited 1 on a deadline-witness
comparison; the full guarded component is not accepted. Its
[physical attempt](runs/coordination/next_step_20261003_types4/root_type_physical_witness_001.json)
took 86.412 seconds, within 120 seconds and both deadlines.

[Scoped cleanup](runs/coordination/next_step_20261003_types4/root_failed_type_cleanup_closeout_001.json)
confirmed owned PIDs absent and the private Job empty/closed. The native
failed-candidate cleanup=false qualification remains preserved. Root
[explicitly released the peer hold](runs/coordination/next_step_20261003_types4/root_type_peer_release_closeout_001.json)
after cleanup; the exact message-completion time was not measured.
Independent actual audit and a future repair proposal are pending.
Attempt004/grant004 are spent, with no automatic retry. The internal
17:00 UTC cap is unchanged. The older failed quality pointer, pending
Windows/full QA with 10 GiB startup, unsigned Gate A/freeze and zero
accepted real cases remain unchanged. No new 30-hour window or lease is
inferred. See [HANDOFF.md](HANDOFF.md).

**Historical 16:37 UTC source-pin checkpoint:** The narrow typing correction has an accepted
[static patch audit](runs/coordination/next_step_20261003_source_fix/source_fix_audit_001.json).
The new [source manifest](runs/coordination/next_step_20261003_source_fix/source_manifest.json)
and [native source audit](runs/coordination/next_step_20261003_source_fix/source_pin_audit.json)
pin canonical `423faa13`: 430 selected paths, the reviewed module as the sole
changed hash, and 429 unchanged baseline files. No post-fix mypy or runtime
pass is established. Prior `9d32cb1a` results remain historical.

[TYPE004](runs/coordination/next_step_20261003_types4/phase_plan.json) is preparing
V4 operations and independent reviews, with internal cap 17:00 UTC. Fresh
static readiness, genuine peer grant and actual guarded admission are still
required before revalidation. The peer's separate checker28 ACK002 hold was
explicitly released after its GO writer refused for insufficient reserve,
before any GO or parent entry; it supplies no pro3 compute grant or test pass.
The failed global quality pointer, Windows/full-QA 10 GiB startup floors,
unsigned Gate A/freeze and zero accepted real cases remain unchanged.
No new 30-hour window is inferred. See [HANDOFF.md](HANDOFF.md).

**Historical 16:00 UTC source-correction checkpoint:** TYPE003 actually reached mypy and returned 1:
four errors in one file among 205 checked files, in a 56.482-second physical
attempt. The [failure audit](runs/coordination/next_step_20261003_types3/type_execution_audit_001.json)
accepts failure evidence only. The exact selected-Job/actual-leaf gate worked;
cleanup remains qualified and final source/runtime checks were incomplete.
Root's [manual review](runs/coordination/next_step_20261003_types3/root_manual_failure_review_001.json)
verified 38 pins and authorized a typing-only correction solely in
`evaluation/phase2_cho_execution.py`.

The [four-replacement proof](runs/coordination/next_step_20261003_source_fix/source_fix_proof_001.json)
reverses to the original bytes; the new file is frozen at `d4073a28` and
native file-only Ruff passed. Independent patch review and a fresh full
430-file canonical source pin are pending. Prior `9d32cb1a` receipts and
candidates cannot admit this modified source. The [source-fix phase](runs/coordination/next_step_20261003_source_fix/phase_plan.json)
has internal 17:00 UTC cap, not a lease or new 30-hour session. A fresh
TYPE004 guard/reviews/grant/admission is required before revalidation; no
post-fix Python/mypy/test pass or new grant is established. The failed quality
pointer, heavy 10 GiB floors, unsigned Gate A/freeze and zero accepted real
cases remain unchanged. See [HANDOFF.md](HANDOFF.md).

**Historical 15:10 UTC TYPE003 static-readiness checkpoint:** TYPE003 is statically ready under the [distinct preparation phase](runs/coordination/next_step_20261003_types3/phase_plan.json)
under the user's keep-working instruction, with internal cap 15:45 UTC.
New V3 copies, IDs and attempt003 must preserve the reviewed gate, source,
runtime, targets, environment and limits. All three independent reviews are
accepted; [root readiness](runs/coordination/next_step_20261003_types3/preparation_ready_001.json)
verifies 13 sealed pins and held bindings, with execution/runtime false.
Root requested a genuine 15:15-15:30 UTC window with explicit peer holds;
the request remains pending, with no grant, hold, admission or attempt003.
RAM at 15:07 UTC was about 5.51 GiB, above the component's 5 GiB floor but
below heavy work's 10 GiB; this observation is not admission. No lease,
replay or new 30-hour window is inferred.

TYPE002's [final static readiness](runs/coordination/next_step_20261003_types2/preparation_ready_001.json)
verifies three accepted reviews and 16 sealed artifacts; its
[expired closeout](runs/coordination/next_step_20261003_types2/root_phase_closeout_001.json)
remains held with no runtime pass. Attempt001 remains failed before mypy,
31.959 seconds/exit 1, unknown cause and no established source type errors.
Source binding `9d32cb1a`, the failed older-source quality pointer and
Windows/full-QA 10 GiB startup floors remain unchanged. Native Rust lint
remains accepted only; Gate A/freeze remain unsigned and zero real cases
are accepted. See [HANDOFF.md](HANDOFF.md) for current coordination.

**Historical 14:39 UTC TYPE002 closeout checkpoint:** TYPE002 is [closed to execution](runs/coordination/next_step_20261003_types2/root_phase_closeout_001.json).
Its internal 14:30 UTC cap expired before sealing, admission or any new grant.
V2 is [sealed and held](runs/coordination/type_component_20261003_v2/preparation_manifest_20261003.json);
independent static reviews are finishing. Native preparation passed only
parse/lint/plan/runtime-hash checks; no grant, admission, Python/Job/mypy or
attempt002 occurred. The post-cap timestamps are preserved, not retimed.

Future execution needs a distinct phase/cap, reviewed candidate and genuine
fresh peer grant; no new phase or 30-hour window is inferred. Attempt001
remains failed before mypy, exit 1 in 31.959 seconds with unknown cause and
no established source type errors. Source binding `9d32cb1a`, the failed
older-source quality pointer and Windows/full-QA 10 GiB startup floors remain
unchanged. Native Rust lint remains accepted only; zero real cases are
accepted and Gate A/freeze remain unsigned. See [HANDOFF.md](HANDOFF.md).

**Historical 14:05 UTC failure-review/V2-preparation checkpoint:** The [independent failure audit](runs/coordination/next_step_20261003_types/type_execution_audit_001.json)
is complete and accepts review only; the failed type/runtime result remains
unaccepted. Root's [manual review](runs/coordination/next_step_20261003_types/root_manual_failure_review_001.json)
permits preparation of a [distinct V2 package](runs/coordination/next_step_20261003_types2/phase_plan.json).
Authors are preparing new copies and independent static review. No new peer
grant has been requested, and no successor Python/mypy/Job launch or retry
is authorized by these records.

Attempt001 remains failed: physical exit 1 in 31.959 seconds before mypy,
unknown cause, no mypy result or established project type errors. Its spent
grant and failed evidence stay preserved. V2 needs all new static reviews,
a fresh attempt and fresh genuine peer grant; the internal 14:30 UTC cap and
resource limits are unchanged. Native Rust lint remains accepted for lint
only; source pin `9d32cb1a`, the failed older-source quality pointer and queued
Windows/full-QA 10 GiB startup floors remain unchanged. Gate A/freeze remain
unsigned and zero real cases are accepted. See [HANDOFF.md](HANDOFF.md).

**Historical 13:51 UTC failed-type checkpoint:** Type attempt001 failed before mypy ran.
The [physical witness](runs/coordination/next_step_20261003_types/root_type_physical_witness_001.json)
records exit 1 in 31.959 seconds. The child refused its current Job-cap check
before the leaf handshake or mypy API; observed mismatch values were not
retained, so the cause is unresolved. No type check, type pass or project
type errors are established.

Root recorded [scoped cleanup](runs/coordination/next_step_20261003_types/root_failed_type_cleanup_closeout_001.json)
and [explicit peer release](runs/coordination/next_step_20261003_types/root_type_peer_release_closeout_001.json)
at 13:46:45 UTC. The failed attempt and native cleanup field remain preserved;
independent actual audit is pending. The grant is consumed: no retry or replay.
A new diagnostic version needs manual failure review, independent static
reviews, a fresh attempt and a fresh peer grant.

Source remains `9d32cb1a`; native Rust lint remains accepted for lint only.
The failed older-source quality pointer and Windows/full-QA 10 GiB startup
floors are unchanged. Zero real cases are accepted; Gate A/freeze remain
unsigned. See [HANDOFF.md](HANDOFF.md) for current evidence and coordination.

**Historical 13:15 UTC type static-readiness checkpoint:** The separate mypy component is statically ready.
Independent package, held-candidate and admission-helper reviews are accepted;
[root readiness](runs/coordination/next_step_20261003_types/preparation_ready_001.json)
binds their exact pins to source `9d32cb1a`. A fresh type-specific window has
been requested only: no grant, admission, Python/Job launch or type pass is
established. The selected normal-site inventory covers 3,142 runtime files
and 765 absences, not the entire third-party type-input dependency closure.

The [type phase](runs/coordination/next_step_20261003_types/phase_plan.json)
requires two 5 GiB startup samples at least one second apart, 4 GiB active
RAM/20 GiB disk, both Job caps of 1 GiB and complete physical exit within
120 seconds. Its 14:30 UTC cap is internal, not a lease or new 30-hour session.
Queued Windows qualification and full quality retain their 10 GiB startup
floors. [Native Rust lint](runs/coordination/next_step_20261003_windows/root_native_lint_acceptance_001.json)
remains accepted for lint only; the failed older-source quality pointer is
unchanged. Zero real cases are accepted; Gate A/freeze remain unsigned.
See [HANDOFF.md](HANDOFF.md) for fresh admission and actual evidence requirements.

**Historical 12:30 UTC native lint/type-preparation checkpoint:** Root [accepted one native lint check](runs/coordination/next_step_20261003_windows/root_native_lint_acceptance_001.json):
Rust Ruff covered the eight quality source roots with `--no-cache`, exit 0
in 0.173 seconds. Fresh native checks before and after matched all 430 files
to `9d32cb1a`. Acceptance covers lint only; the full-quality pointer remains
failed for older `25ab4f3d`.

A [separate mypy-only phase](runs/coordination/next_step_20261003_types/phase_plan.json)
is being prepared with 1 GiB process and aggregate Job caps, two 5 GiB startup
samples and a 120-second physical limit. It needs all static reviews, a fresh
type-specific peer window and an independent actual audit; no mypy launch
is established at this checkpoint. Windows qualification remains statically
ready and queued. Its 10 GiB startup floor and the separate full-quality
10 GiB floor are unchanged; RAM at 11:54 UTC was about 7.91 GiB. The
[full-quality activation map](runs/coordination/next_step_20261003_windows/full_quality_activation_map_001.md)
also requires a separate grant covering Torch synthetic engineering fits.
The 14:30 UTC cap is internal, not a lease or new 30-hour session. Zero real
cases are accepted; Gate A/freeze remain unsigned. See [HANDOFF.md](HANDOFF.md).

**Historical 11:28 UTC Windows static-readiness checkpoint:** preparation is statically
ready. Independent package, held-candidate and admission-helper reviews are
accepted, and the [root readiness record](runs/coordination/next_step_20261003_windows/preparation_ready.json)
binds their decisions and exact pins. No qualification launch, compute lease
or admission exists. RAM at 11:25 UTC was about 9.24 GiB, below the unchanged
10 GiB startup floor; waiting continues without cache or service changes.
Source `9d32cb1a` and all 430 selected file pins remain matched. The 14:30 UTC
cap is an internal guard, not an owner expiry or lease. Full quality remains
unpassed for this source, zero real cases are accepted, and Gate A/freeze
remain unsigned. See [HANDOFF.md](HANDOFF.md) for actual entry requirements.

**Historical 11:12 UTC Windows preparation checkpoint:** the
[no-fit Windows qualification phase](runs/coordination/next_step_20261003_windows/phase_plan.json)
is preparing normal exit, descendant cancellation and a small memory-denial
check. The [new package](runs/coordination/windows_qualification_20261003_v2/preparation_manifest_20261003.json)
is sealed, but independent preparation/candidate/admission reviews remain
pending; no qualification launch or lease exists. The
[native source audit](runs/coordination/next_step_20261003_windows/source_pin_audit_v2.json)
matches all 430 files to `9d32cb1a`. Two 11:03 UTC RAM observations exceeded
10 GiB; these are readiness, not admission. The 14:30 UTC cap is an internal
guard, not an owner expiry or lease. The earlier accepted component covers
only its 25 tests and normal Job path. Full quality remains failed for older
source; zero real cases are accepted and Gate A/freeze remain unsigned.
See [HANDOFF.md](HANDOFF.md) for current coordination.

**Retained accepted component, 3 October 2026, 09:38 UTC:** component004's **25/25 guarded-quality tests**
are [independently audited](runs/coordination/next_step_20261003_phase2/execution_audit_004.json)
and [accepted by root](runs/coordination/next_step_20261003_phase2/component_acceptance_004.json),
with zero errors, failures or skips. The
[root execution witness](runs/coordination/next_step_20261003_phase2/root_execution_witness_004.json)
records complete physical exit with code 0 in 9.364 seconds; native receipts record
atomic private-Job assignment, 1 GiB process/aggregate limits and closed
handles after an empty Job. The precise venv-launcher to interpreter edge
remains inferred. Acceptance covers this component and normal launch/cleanup only. Source
`9d32cb1a` and selected runtime `a439111c` stayed stable; the full-quality
pointer remains failed for older source `25ab4f3d`. No Torch, model fits or
real cells ran in this component. Full quality and broader Windows qualification
remain pending; Gate A and the scientific freeze remain unsigned.
See [HANDOFF.md](HANDOFF.md) for current state.

**Historical 08:50 UTC preparation checkpoint:** preparation is complete for the
[current bounded component phase](runs/coordination/next_step_20261003_phase2/phase_plan.json).
The sealed v3 wrapper, held candidate004 and native admission helper passed
independent static reviews with no blocking findings. The
[preparation audit](runs/coordination/next_step_20261003_phase2/preparation_audit.json)
establishes preparation only: no actual compute lease, test entry or runtime
pass is established at this checkpoint. The 10:30 UTC cap is an internal
operational guard, not an owner expiry or a lease. The user directed waiting
for memory or continuing light work; this step altered no shared cache or
service. Gate A and the scientific freeze remain unsigned. See
[HANDOFF.md](HANDOFF.md) for admission and execution state.

**Historical 06:18-08:20 UTC next-step checkpoint:**

The user authorized the next engineering step on 3 October at 06:18 UTC.
The [new bounded phase](runs/coordination/next_step_20261003/phase_plan.json)
prepares one 25-test guarded-quality component check under a fresh reviewed
wrapper and explicit peer release. Its internal phase has now ended with
zero tests entered: startup RAM and a later insufficient execution window
prevented admission. Preparation and fresh request copies passed static review.
The user directed waiting for memory or continuing light work; shared WSL
cache remains intact. Current source
remains frozen; no new runtime pass or real case is claimed. See [HANDOFF.md](HANDOFF.md) for the
current preparation and execution checkpoint. The earlier closeout below
is preserved as history and does not restrict this newer authorized step.

**Historical closeout, 3 October 2026, 05:49 UTC:** the original 30-hour session has ended.
The user selected **audit and handoff closeout only**. The
[fresh source audit](runs/coordination/20261003_source_drift_audit_0543.json)
found no drift across the 430 frozen selected files; the
[runtime inventory](runs/coordination/20261003_runtime_readiness_inventory_0542.json)
found no new current-source validation or real Cho case in its inspected scope.
The current quality pointer remains failed for older source `25ab4f3d`.
The engineering objective is incomplete, and old admission, wrapper deadlines
and held proposals do not authorize further execution. See the
[handoff](HANDOFF.md) for pending checks and future-session prerequisites.
Scientific Gate A and the experiment freeze remain unsigned.

**Preserved 1 October, 22:49 UTC checkpoint:** Phase I local engineering evidence is
complete and Phase II is preparing its first real Cho engineering case.
The [Phase II start page](PHASE2_START_HERE.md) and [handoff](HANDOFF.md)
carry the current milestone and verification state. The baseline source
for the new 30-hour work session is `6566e348`; implemented source fixes are
frozen pending validation, so the live tree has not passed new full quality.
The current canonical fingerprint is `9d32cb1a`, with 430 source/configuration
files independently verified in the [source identity audit](runs/coordination/20261001_m3c_source_pin_audit.json).
A fresh raw verifier has passed
[preparation review](runs/coordination/20261001_m3d_raw_preparation_audit.json)
and native lint; it has not run.

At that baseline the raw audit passed, but full quality stopped on the
unchanged 4 GiB active RAM floor. The 925-test quality pass, 45 passing
controls and 36 passing no-future controls belong to historical source
`6523283e`, not the newer tree. The Cho selection ceiling is now 5,253;
the persisted engineering admission and 5.5 GiB analysis-cap configuration
exist. Sweep repairs and a supervised CLI have passed independent static
review; their latest runtime checks remain pending. The bounded Cho input snapshot has passed static review
and nine lightweight tests; training-equivalence verification remains pending.
An earlier guarded-quality version passed independent review and 20 lightweight
tests. Its latest shorter lease limit has passed static review; all 25 focused
tests and latest type checks remain pending. Standalone native Ruff passes
for all 17 changed files after independently reviewed CLI layout fixes.
An independently reviewed operational runner is prepared for the 25 focused
tests, with atomic Job containment and explicit time/memory limits. It has not
run; shared-machine memory and release requirements still hold.
A separate [whole-CLI supervisor preparation audit](runs/coordination/20261001_m4b_first_case_supervision_audit_v2.json)
now accepts the fixed first-case wrapper statically. Native lint, parse and
default-plan checks pass; no Python or case ran. Actual Windows containment,
current validation, measured environment and explicit heavy release remain pending.
A separate [Windows no-fit qualification preparation](runs/coordination/20261001_m4c_windows_qualification_audit.json)
has passed independent static review and native checks. It will check nested
exit/cancellation and a small memory limit under a fresh release; it has not
executed. RAM was 0.9733 GiB at 22:34 UTC and both compute leases remain held.
This does not certify the
full source tree. Scientific freeze and
Gate A remain open; no completed real Cho evaluation cell is established.

The source-fit-only Cho 60 Hz LaBraM cache also passed independent static
review. Its 2 GiB immutable residency and final live-input hashes are implemented;
10 lightweight and six training-equivalence tests remain unrun. All source
changes are frozen pending sufficient RAM and the coordinated validation lease.

The following records describe the preserved Phase I results.

All 170 public subjects are downloaded and structurally audited: BCI Competition
IV 2a (9), Cho2017 (52), and MMIDB (109). Profile A, Profile B, label-blind frozen
artifact thresholds, leakage controls, seven benchmark variants, safe LaBraM
loading, LoRA/adapters/prompts, LSL streaming, confidence gating, accumulated
evidence, CPU/GPU latency, and the held-out replay demonstrator are operational.
The final configuration-hash benchmark sweep is complete: 5,950/5,950 records
across 170 subjects, seven methods and five seeds independently pass the record
audit. Its snapshot is
`ff7076b53efd77569d35b6b4d9460be3505376dd174cd690e22c6dee3cfe461a`.
The 21-row primary table, diagnostic table and three snapshot-bound figures were
regenerated and visually checked. These remain exploratory results.

A native Windows demonstration now connects actual true-rate LSL replay to
causal windows, CPU EEGNet, confidence gating and an on-screen command grid.
The visible A09 rehearsal received all 6,144 samples and displayed all 12 windows;
training used the other eight subjects only. All decisions abstained, so this
verifies the integration, not useful decoding accuracy. See
`docs/realtime_system.md` for the one-command rehearsal and its limitations.

Run `scripts/verify_phase1_quality.py` with the project Python to record lint,
type checks and tests for the exact source snapshot. The final completion checker
also verifies report hashes, benchmark completeness and the native display receipt.

Gate A remains unsigned. MOABB does publish an EEGNet reference for this dataset;
the earlier statement that it was absent was incorrect. Its within-session
five-fold protocol and scoring differ from the existing cross-session attempts,
so those attempts do not establish reproduction. The separate protocol-matched
grid is now complete at 450/450 valid fits, and an independent raw-input audit
matched every fit. The seed-42 mean ROC-AUC is 75.66% versus the published 77.15%;
the four declared repeat seeds average 75.02%. No acceptance tolerance or approval
has been adopted, so this descriptive comparison does not sign Gate A.
The user explicitly authorized later Phase I work as exploratory; no downstream
result is represented as resolving Gate A. See `docs/gate_a_status.md` and
`docs/deviation_log.md`.

## Local setup

The project targets Python 3.12. A project-local `.venv` is used; no system-wide packages are required.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pip install -r requirements.lock
.\.venv\Scripts\python -m pytest
```

Install the heavier EEG and GPU dependencies only after the foundation tests pass.

## Subject 1 EEGNet baseline

The training session is split into training and validation subsets. The evaluation
session remains untouched until final scoring.

```powershell
.\.venv\Scripts\python -m pip install -r requirements-data.lock
.\.venv\Scripts\python -m pip install -r requirements-ml.lock
.\.venv\Scripts\python scripts\run_eegnet_baseline.py --smoke
.\.venv\Scripts\python scripts\run_eegnet_baseline.py
```
