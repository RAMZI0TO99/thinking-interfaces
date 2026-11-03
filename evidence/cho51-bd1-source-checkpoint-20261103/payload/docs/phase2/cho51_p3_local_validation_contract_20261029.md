# P3 project-local validation contract

29 October 2026, Asia/Riyadh. Version1. Engineering design, not run admission.
Author: project Root. The owner requested design and independent review for the
117 candidate tests and34 controls, followed by implementation of the next step.

## Decision and retained limits

Build new project-local preparation, loader-check, validation and closeout
sources. Preserve the six candidate files and all historical operations unchanged.
Do not invoke an old launcher, satisfy its retired scheduling fields, import its
operational main function or rewrite its results. New source may adapt reviewed
logic, with an explicit source comparison and new independent review.

This is a proposed scoped successor under the
[execution policy](../PROJECT_EXECUTION_POLICY.md). It extends the independent
operation approach of the [inventory contract](cho51_p3_inventory_contract_20261029.md)
to a fully declared, confined nonnumerical workload. It does not inherit v8's
runtime coverage or admission. It does not claim that the old process domain
ended, repair004, activate005, or satisfy the full-restart predicate in the
[custody design](cho51_p3_local_custody_design_20261028.md). The historical
UNRESOLVED disposition remains unchanged and is pinned as context, not a grant.

Upon independent design acceptance and an implementation-specific Root adoption,
this addendum replaces the policy's sentence beginning "Only a successful reviewed
successor observation" **solely for Q/P/L/V/C under this contract**. The accepted
v8 observation supplies a precedent for an independent current operation; it is
not the complete-runtime or historical-boundary prerequisite for these stages.
Instead Q qualifies the new mechanisms, P supplies the complete retained closure,
and L qualifies the declared loader before V. Every transition still requires
its own positive source/result review and admission. P's closure review is input
qualification, never an operational grant. This explicit scoped replacement does
not change the frozen policy bytes, full-restart predicate, historical custody
disposition, or any other workload's prerequisite. It takes effect for no
implementation until its adoption binds that implementation's accepted review.

The applicable owner amendment remains4GiB startup/active RAM and20GiB disk
for this nonnumerical phase. No new RAM approval is needed. Scientific cells
remain0/1020 and the final freeze unsigned. No model construction, training,
restoration, inference, raw/processed EEG or weight access is authorized.

## Exact test and control identity

The [test roster](cho51_p3_local_validation_v1/test-roster.json) binds the unchanged
candidate sources and25 function multiplicities:39 mapping and78 telemetry
cases. These are static expectations, not collected node IDs or passing tests.
The loader-check must collect exactly117 unique full node IDs, with the exact
per-function/module counts, no extras, omissions or deselection. It saves that
ordered roster and digest. Validation must collect the same complete roster
under the same source, dependency and configuration pins; a changed parameter
ID or collection order requires review, not a count-only pass.

The [control roster](cho51_p3_local_validation_v1/control-roster.json) identifies
34 successor controls and maps each to its historical counterpart. Thirty-two
preserve the original purpose. `local_full_window` and `local_short_window`
explicitly replace the retired965-second shared-window checks with sufficient
and insufficient complete local validation windows. They test600 versus599
seconds in the pure predicate; they do not sleep or create admissions.
Do not label these as execution of the unchanged historical34 controls.
That predicate evaluates a newly proposed V caller window at its origin; it is
not a demand for another600 seconds remaining later during the same operation.

Validation runs all34 controls and all117 candidate cases in one fresh owned
Job. Every control is an exact Boolean true with a unique expected name.
Require pytest exit0,117 passed, zero failed/error/skipped/xfail/xpass/deselected,
and351 successful setup/call/teardown phase reports, exactly three per node.
The bounded physical JUnit file must independently agree on117 unique cases,
classes/names and outcomes. A fabricated result JSON, console footer or an
empty successful test invocation is insufficient. Harness qualification cases
are counted separately; see the [acceptance matrix](cho51_p3_local_validation_v1/acceptance-cases.json).

## Stages and independent gates

| Stage | Allowed work | Required acceptance before the next stage |
| --- | --- | --- |
|Q: implementation qualification | New harness's injected and owned-fixture controls; no candidate/third-party imports | Exact implementation source review, separately admitted tests, actual review and Root adoption |
|P: dependency preparation | Bounded file-only enumeration and retained byte/identity checks; no package/candidate imports or compilation | Complete proposed closure manifest, actual owned cleanup/caller evidence, independent pin/coverage review and Root adoption |
|L: loader and collection check | Reviewed third-party initialization, guard installation, canonical imports and guarded collect-only of the two candidate modules; no fixture execution | Loader origins/coverage, guards, exact117 roster, no disallowed effects and complete actual review |
|V: validation | Same reviewed initialization and guard order,34 successor controls, then all117 unchanged candidate cases | Full test/control/guard reports, input/output identity, Job/caller closure and independent actual-result review |
|C: external closeout | A new stdlib-only auditor reads accepted P/L/V and their complete control chain, creates a bounded evidence export | Actual caller closure, independent archive/completeness review and final Root qualification |

Every stage has separate review-bound inputs, a new UUID, request/admission,
once-only claim, output namespace and actual tool evidence. Q is not34 and is
not117. L collection executes import code and therefore needs an execution
admission; it is not static work. A successful P does not authorize L. Source
review alone permits implementation/pinning work only. This design creates no
request, positive operational disposition or launch permission.

## Dependency and loader closure

[dependency-plan.json](cho51_p3_local_validation_v1/dependency-plan.json) lists
source-time seed paths, metadata assets, preimports and blocked APIs. It is a
recipe requiring expansion and independent review, not a complete physical map.
P must freshly cover:

- Observer/supervisor/guard/report code and their bootstrap runtime; the selected
  Python executable, DLLs, standard library, extensions, explicit search paths
  and interpreter metadata. Do not use the stale `.venv` executable merely
  because its package directories exist. Version/ABI compatibility needs L.
- Third-party source, extension modules, dependent DLLs, package metadata and
  import-time resources for pytest, NumPy, PyTorch and all transitive imports.
  Include distributions queried by `environment_digest`, not just imported names.
  The specific MNE fiducial resource is import data, never an EEG/weight wildcard.
- All canonical/imported/dynamically compiled project code, namespace/package
  initializers, route-contract pins, the full live `capture_source` census and
  its selected root/hook metadata. The historical432-file count is not a fresh
  census. Bound enumeration, detect added/missing/changed paths and preserve
  the source identity actually observed, including dirty working-tree state.
- All declared configuration/anchor/synthetic-identity JSON/TOML, Git executable
  and required runtime/configuration dependencies, repository identity inputs,
  and the current policy/design/adoption/reviews. Never open data or weights
  referenced only as historical digest strings.

P retains native identities while streaming bounded hashes; opens use read
sharing only, refusing ordinary incompatible writers/deletion, reparse paths,
hardlinks, aliases, nonlocal/unsupported volumes and ambiguous identities.
Files, ancestors and any roster-defining directory state are checked again.
Directory handles do not freeze membership. Each later operation re-enumerates
its bounded recipe and retains the exact accepted files through use and final
publication; added or missing entries refuse. No freshness claim survives handle
release without new checks. Cap25,000 files,4GiB aggregate,2GiB per file, depth32;
64KiB hash chunks with cooperative checks. Cap exhaustion is refusal, never a
partial accepted closure or permission to increase the limits.

The source's proposed launch shape is an explicitly pinned Python executable
with `-I -S -B`, a fresh absent `-X pycache_prefix=<attempt-owned path>` and one
fixed entry point. No user/site startup, executable `.pth`, ambient PYTHONPATH,
unlisted zip importer or pyc execution. `-B` alone does not prevent reading pyc.
Install the reviewed import/read guard before admitting non-bootstrap code;
verify initial observer bytes against the externally bound request before
executing them, using those same bytes or retained identities. Audit hooks and
Python monkeypatches are defense in depth, not an OS security boundary.

L must qualify exact sys.path/import origins, namespace paths, plugins, package
versions, native loader/search configuration and loaded-image observations.
Unlisted project/third-party code, DLL/resource search directories or unexpected
loaded images refuse. Windows API sets/KnownDLLs and explicitly reviewed system
images form a stated platform trust base; they are not silently included in the
declared Python roster or called authenticated by a file hash. A full path to
one DLL does not fix where all its dependencies load. Source review must trace
the actual package loader before native imports; no unrestricted discovery run.
If static closure/search enforcement is insufficient, stop and review a new
bounded preparation recipe before any candidate import.

Use explicit pytest root/config/test paths, importlib mode, no conftest loading,
no entry-point plugin autoload, no ambient addopts/plugins, cache provider off,
and a pinned built-in/custom plugin allowlist. The fixture root must be a new
ordinary directory below the actual project attempt. Do not reuse or let pytest
clear an existing basetemp. Parent imports and child collection must not depend
on an unrelated current directory or a developer's personal configuration.

## Effects, guard order and containment

Initializers for the reviewed runtime packages are a separate, logged loader
phase: allow only traced initialization, no experiment entry points or model
construction. Set native library threads to1 and hide GPUs before child start;
verify Torch thread settings before the candidate phase. Do not claim zero
library-internal arithmetic merely because no scientific operation occurred.

Install confinement before bootstrap imports. Patch NumPy/Torch load, save,
model/state/backward/optimizer APIs before project imports; import and guard
safetensors **before** modules that bind its functions by value. After necessary
canonical initialization, block recorder/claim/recovery/publication/executor
entry points and numerical array/tensor constructors before candidate import.
Required attributes missing, stale imported aliases or unguarded equivalent
paths are refusal; `hasattr`-and-skip is not adequate. Tests must exercise alias
bindings and confirm denial precedes effects. Only allow the genuine metadata
planner/helper epoch and explicitly declared synthetic JSON construction.

The eight operation counters remain exact integer zero: source_updates,
restore_count, support_updates, gradient_updates, target_inference_calls,
query_count, model_constructions and measured_cells. Separate expected control
denials from candidate-phase violations without erasing either record. Any
unexpected denial or attempted forbidden candidate action fails the run, even
if pytest catches its exception. Scientific/compatibility authority remains false.

Ordinary writes are restricted to the attempt's bounded fixture/report tree:
temporary route/cohort/execution JSON (including the deliberate append/restore
case), pytest temporary files, control-once/tail files and bounded logs/JUnit.
No writes to candidate sources, canonical assets, environment, Git metadata,
shared caches or previous attempts. No network, external services, diagnostics,
model/data reads, new process except exact Git observations, or unrestricted
native-library loading. Reject ambiguous/outside paths before effects; do not
silently sanitize them. A failed fixture restoration remains in the consumed
attempt and cannot change a shared historical asset.

Launch the owned child suspended with atomic assignment to an unnamed,
noninherited kill-on-close Job before execution, verify membership/limits, then
resume. Keep original handles; never reopen/kill by PID. The child's explicitly
allowed Git calls are only the exact pinned executable and unchanged source
capture argument vectors (`["--no-optional-locks", "rev-parse", "--verify", "HEAD"]`
and `["--no-optional-locks", "status", "--porcelain", "--untracked-files=all"]`), exact
project cwd and controlled inherited environment; no shell, config overrides or
arbitrary commands. Bound each to10s, at most256 calls and one simultaneous Git
child, all inside the owned Job. Audit wrappers must reject alternate executable
spelling/arguments/environment/cwd tricks except reviewed Windows spelling
equivalence. Account for Git descendants in complete Job closure; no tree sweep.

Root and one same-project author/reviewer remain the collaboration limit.
Production child results travel through bounded owned streams/IPC or a reviewed
handoff with original native file identity. The supervisor must retain inputs
and final outputs through validation and publication. A pathname/UUID and a
later file hash alone do not authenticate a child's result. Parent-owned
outputs use create-new, exclusive write/delete protection, flush and same-handle
read-back. Child-owned artifacts need an explicit ownership/closure protocol
accepted in source review; no implementation may leave this as a placeholder.

## Time, resources and stop

| Stage | Whole caller ceiling | Work stops by | Process / Job MiB |
| --- | ---: | ---: | ---: |
|Q |90s |60s |512 /768 |
|P |300s |240s |4096 /5120 |
|L |300s |240s |4096 /5120 |
|V |600s |540s |4096 /5120 |
|C |300s |240s |4096 /5120 |

All stages require two fresh startup samples at least200ms apart,4GiB available
RAM at startup and while active,20GiB disk, one library/Torch worker and hidden
GPUs. The V600s ceiling includes initialization, controls, collection, fixtures,
reports, owned cleanup and publication; do not append a fresh600s child window.
At work stop cease effects and allow at most5s for owned termination/reap; the
remaining stage reserve is for bounded stream drain, audit and publication.
An independent parent watchdog covers stalled child/native work. Cleanup
uncertainty or late actual tool return prevents acceptance even after timeout
termination. No new30-hour session, deadline extension or silent retry.

The external caller records UTC and monotonic origin immediately before invoking
the supervisor. The whole-stage deadline is that origin plus the table's ceiling;
work-stop and cleanup deadlines share that origin. A fresh admission must cover
the complete proposed origin-to-deadline interval. At supervisor entry and every
later dispatch, require admission expiry at or after that original deadline and
enough remaining work/reserve time for the bounded action; never restart a full
stage clock at dispatch. Admission parsing, pinning and startup samples consume
the same caller budget. Refuse if the admitted window cannot cover the actual
caller origin. The independent caller return audit checks this original interval.

Strictly observe `runs/coordination/PROJECT_STOP.json`: PRESENT or UNKNOWN stops
owned work; absence requires an actual missing-path result under verified
ancestry. Check stop/UTC/monotonic deadlines at least every250ms and before each
effect, plus during chunked reads; blocked calls remain bounded by the watchdog.
Track resource minima, memory peaks and violations. Whole-caller guard coverage
must explicitly identify parent memory/IO exposure as well as the capped Job;
an uncapped supervisor is not described as covered by its child's Job cap.

Each stdout/stderr is at most1MiB, each JSON/report at most8MiB, total attempt
outputs at most64MiB/256 files. Fixture data are JSON-only with at most12 files/
16MiB per mapping assessment; preserve the stricter candidate-specific bounds.
JSON must reject duplicates/nonfinite values and bound depth32, nodes200,000,
exact integer fields and strings by the applicable field limit. Closeout export
retains the historical64-file/32MiB cap; inability to bind the complete new chain
within it refuses, not an incomplete archive relabelled complete.

## Record joins and acceptance

The implementation must define closed versioned schemas for: contract adoption,
per-stage request/admission, attempt claim/dispatch, preparation manifest, loader
assessment/collection roster, control/pytest report, resource/custody receipt,
external tool audit, independent actual review, Root qualification and export
manifest. No operational example with invented successful fields is supplied.

Every request/admission binds stage, UUID, exact command/roots, source and
dependency manifests, independent source-review digest, policy and this contract,
applicable resource amendment, all limits, predecessor qualification refs, UTC
window and explicit forbidden effects. A retained Root contract-adoption record
must bind the accepted design and exact implementation review before admission.
Each input ref has path/bytes/SHA256 and a declared identity/ownership role.
No record contains its own or a future output hash.

Required order is design review; implementation review; contract adoption;
request/admission; atomic claim; capture/dispatch; completed operation; genuine
external caller-return observation; different actual review; Root qualification;
next-stage request. P->L->V->C references bind exact preceding accepted outputs.
Each stage's new finite window must fit its own entire ceiling; no old shared
lease or an unissued future grant is consulted. Fresh scopes/pins are checked
again at dispatch. An artifact or child exit0 does not stand in for caller return.

Require factual attempted/unknown/started states, original process generation,
Job assignment and limits, all owned process exits, empty/closed Job, original
handle closure, bounded stream EOF where streams are used, verified publication
and actual return within both UTC and monotonic bounds. A failure never becomes
success through best-effort cleanup; missing/ambiguous custody remains unknown.
Retain failed claims and partial bytes. Pending flags remain immutable and are
resolved only by separate review/adoption, never rewritten in an old receipt.

## Trust and completion boundary

Trust the explicitly reviewed local Windows/filesystem/observer and immutable
source inputs; do not claim defense against a hostile same-account actor,
privileged/kernel compromise, injected observer or preexisting writable mapping.
Control/file/loader guards are engineering checks under that stated trust model.
No global machine quiet, complete historical log coverage or cryptographic
loaded-code attestation follows. A new ordinary writer/input change is still
detected or refused; missing guards cannot be waived by these assumptions.

Final acceptance means the exact newly reviewed nonnumerical implementation
and unchanged candidates satisfied their scoped controls under this runtime.
It does not qualify predictive performance, canonical measured-case execution,
checkpoint provenance, old cleanup, a scientific cell or final freeze. All
historical custody/release/retry and scientific authority stay false; permission
for a particular new engineering operation lives only in its separate admission.

Implementation is the next step after independent acceptance of this design.
Before P/L/V/C, independently review and qualify the new source and mechanisms
against the acceptance matrix. No part of this document is a runnable launcher.

## Platform references

The implementation must verify these against the pinned runtime as well as the
source behavior: [CPython isolated/site/bytecode flags](https://docs.python.org/3.12/using/cmdline.html),
[pytest plugin controls](https://docs.pytest.org/en/stable/how-to/plugins.html#disabling-plugins-from-autoloading),
and [Windows DLL dependency search](https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order).
They explain relevant mechanisms, not a guarantee that the current package
graph, native initialization or new runner is already qualified.
