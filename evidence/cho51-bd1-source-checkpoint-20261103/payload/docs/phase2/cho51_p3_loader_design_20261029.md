# L loader, resource and ABI observation with exact test collection

29 October 2026, Asia/Riyadh. Version 1. Author: project Root, informed by a
separate read-only candidate/package analysis. **Design only.** Independent
acceptance is recorded separately; this document grants no execution admission.

## Scope and predecessor

Implement a new L supervisor, native observation helper, guarded Python entry
point and collect-only pytest plugin. Preserve all previous sources and receipts.
The [local validation contract](cho51_p3_local_validation_contract_20261029.md)
remains controlling, including its scoped policy replacement and Q/P/L/V/C gates.
The [accepted P10 preparation](cho51_p3_dependency_preparation_20261029.md) supplies
the reference physical graph: 20,406 files, 888 PE images and 4,843 native edges.
Its owned lifecycle and final verification were accepted for that operation.
Released handles, a code-file superset and PE edges are not current execution
permissions, exact loader choices or proof of binary compatibility.

L observes the declared initialization and collects the two unchanged modules.
It executes no fixture, test body, 34-control V suite, experiment, model, tensor
workload, restoration, training or inference. Reviewed library initialization can
perform internal arithmetic; do not describe that as zero numerical instructions.
All eight scientific operation counters remain exact integer zero.

The deliverables are this contract, [record definitions](cho51_p3_loader_design_v1/record-contract.md),
[static source trace](cho51_p3_loader_design_v1/source-trace.md), and
[qualification scenarios](cho51_p3_loader_design_v1/acceptance-cases.json).
These specify implementation obligations, not passing implementation tests.

## Required sequence before L

1. Implement new versioned sources, with an explicit comparison to Q10/P10
   reader, guard, native caller, protocol and retained-output ownership logic.
   Do not launch or modify a frozen runner. Assign implementation file ownership.
2. Independently review the exact source and the finite initialization plan.
   Qualify new mechanisms in fresh Q admissions using injected records and
   owned fixtures, without candidate or third-party imports. New native helper
   construction belongs in that reviewed Q workflow, never inside L.
3. Obtain a separately reviewed/admitted fresh P successor covering the new
   observer/helper/configuration and every declared execution dependency. Bind
   accepted P10 as provenance, compare additions/removals/changed identities,
   and retain a new complete map. New L code cannot be an unreviewed overlay on
   P10. Current design/policy/review/adoption records are explicit control inputs,
   outside the physical map's self-reference cycle, with the same reader checks.
4. Root adopts the exact accepted design, implementation review, Q qualification
   and fresh P result. Only then create a fresh L request/admission and unused
   UUID, followed by actual result review by a different reviewer and Root
   qualification. Design acceptance alone does not create any of these grants.

P10 is still the accepted reference even if the future environment has changed.
Any dependency drift, missing resource, ambiguous DLL choice, new loader branch
or insufficient static trace returns to preparation/review; it is not permission
to run an unrestricted discovery import or install/upgrade packages automatically.

## Finite execution plan

Implementation must supply a closed, review-pinned plan containing exact files,
module names, namespace paths, package/distribution metadata, order and allowed
effects for every initialization group. It also lists exact DLL search paths,
missing optional paths, per-importer native choices, resource call sites,
bootstrap imports, required guard symbols and retained aliases. The physical
superset is never used as an import allowlist. Package test directories, unrelated
entry points and optional dormant modules are excluded from execution.

Use the retained, freshly pinned Python executable rather than the stale .venv
launcher. Its command has `-I -S -B`, a new absent attempt-owned pycache prefix,
and exactly one externally pinned entry point. Verify the bootstrap bytes before
execution, then execute those bytes or protect and recheck the same file identity.
The executable, Python DLL, startup stdlib/extension imports and native observer
are an explicit bootstrap trust set, observed before third-party initialization.
No import can precede the gate that authorizes its phase.

Environment construction is allowlist-based before child start: controlled cwd,
HOME/USERPROFILE/XDG, locale, temp/config/cache locations, PATH, native-library
thread limits of one, hidden GPUs, disabled pytest plugin autoload and no ambient
Python/pytest/Git overrides. Keep required Windows runtime variables explicit.
Do not clear system configuration globally or alter machine DLL search policy.
Any required temporary/config write must be an exact bounded attempt path;
otherwise refuse. Existing shared caches are neither read as authority nor cleared.

The child's sys.path is the ordered, exact runtime stdlib/extensions, site root
and project root from the request; no cwd insertion, user site, executable .pth,
zip importer, pyc read or alternate finder. Namespace paths are exact ordered
lists. A reviewed finder/loader checks names, origins, type, suffix and retained
file identity before execution. Source comes from retained verified bytes;
extension loading uses exact retained files plus the native plan. Reject unknown
meta/path hooks, loader substitution, syspath mutation and unexpected sys.modules
entries; reconcile before/after every initialization group and collection.

## Phase machine and guard order

| State | Allowed effects and required exit evidence |
| --- | --- |
| L0: retained preflight | Validate full authority chain, original clocks, two resource samples and once-only claim; reacquire fresh P files/control inputs and census; no package imports |
| L1: owned bootstrap | Atomic suspended child/Job assignment; bootstrap origin and loaded-image baseline; native notification observer active; read/write/network/process/import guards active |
| L2: dependency initialization | Execute only the ordered reviewed dependency groups, reconciling imports, images, search paths and resources after each; install package API guards before canonical binding |
| L3: canonical initialization | Import exact canonical preimports; required blocker/alias census; prohibit recorder/claim/recovery/publication/executor effects; finish strict numerical-constructor guards |
| L4: collection | Exact pytest configuration and plugin set; collect two modules; retain ordered 117 IDs and 25 function counts; no fixtures or test phases |
| L5: final verification | Freeze collection result; reconcile all imports/native events/resources/guards/counters; complete original-handle rehash/identity/census and retained outputs before release |
| L6: custody and review | Reap every owned process, verify empty Job and streams/handles/observer closure, obtain genuine caller return; independent actual review, then Root qualification |

Any failure is sticky. No later success, caught exception, cleanup or result flag
can erase a refusal. Dispatch into the next state requires enough remaining time
for that action and final verification under the original caller clock.

At L1 install import/read/write/process/network and dynamic-code gates before
non-bootstrap imports. At L2 allow only explicitly traced library initialization;
deny data/model APIs as soon as their defining package exists and before any
canonical alias is bound. Import safetensors.torch and guard `load`, `save`,
`load_file`, `save_file`, plus reviewed equivalent entry points, before project
modules import them. Guard NumPy/Torch load/save, state restoration, model
construction, backward and optimizer entry points; an absent required symbol
refuses rather than being skipped. Blocker installation must not accidentally
invoke a property or arbitrary callback to discover an attribute.

Some library initializers allocate arrays internally. Their narrow pre-candidate
epoch is source-reviewed, logged and closed before L4; it permits no project
model/data work. At L3 install the full reviewed constructor/function/method
blocker set, and verify canonical by-value aliases by object identity. Any
unresolved early canonical initializer needing numerical constructors requires
a source-reviewed exact initialization entry, not a blanket exemption. The
genuine metadata planner's dynamic compilation is separately identified by
retained source hash and phase; L collection must not exercise its V fixture.
Audit hooks and Python wrappers are defense in depth under the existing trust
model, not a security sandbox against arbitrary native or hostile same-user code.

Use separate logs for Q fixture denials, L mechanism sentinel checks, ordinary
initialization and candidate collection. Any unplanned L denial or forbidden
candidate attempt refuses even if pytest catches the exception. A sentinel uses
a reviewed effect-free argument and must be denied before its underlying API;
it does not run a candidate or count as one of V's 34 controls. Never call an
unguarded real model/data API merely to check whether it is blocked.

## Native search and image observation

A separately Q-qualified native helper records loaded and unloaded images from
before L2 through final reconciliation. The proposed backend uses
`LdrRegisterDllNotification` plus baseline/final `K32EnumProcessModulesEx`
snapshots. Registration failure, unavailable API, overflow or lost/ambiguous
events refuses. There is no polling-only fallback that silently misses transient
loads. The helper is native code, not a Python/managed callback under loader lock.

The callback only copies bounded event data into preallocated memory and latches
fault/overflow state using reviewed in-module operations. It calls no external
module, allocator, Python, filesystem, logger or blocking lock. Copy notification
strings before returning; validate UTF-16 lengths, pointers and size bounds.
The implementation review must inspect generated helper dependencies, including
compiler-inserted calls, and Q must exercise load/unload, overflow and shutdown.
Drain and validate outside the callback. Bound 4,096 image slots, 8,192 events,
and 1,024 UTF-16 code units per copied full path; exhaustion refuses. Retained
handles and offsets never become acceptance merely through a matching basename.

Record sequence, load/unload, base, image size, exact normalized path, phase and
observation provenance. Join each file-backed image to the retained native ID,
size/hash and approved importer/search choice, or an exact reviewed Windows
platform-trust entry. Do not call a path/hash join in-memory code attestation.
Reconcile two bounded stable snapshots (up to three attempts inside the same
deadline) with the event stream; gaps, unstable snapshots, unbalanced events or
unknown image choices refuse. Snapshot handles are observations, not owned module
references to close. If extra references are acquired, count/release each one.
Unregister the observer and close its resources only after final event drain;
unknown unregister/callback completion prevents acceptance. Bootstrap loads
before registration belong to the explicit bootstrap baseline, not claimed
notification coverage. Native resource/datafile mappings need their separate
resource evidence; module enumeration does not cover them.

Before L2, set a reviewed process-local restricted DLL search policy and verify
each planned add/remove-directory action. Windows USER_DIRS order is unspecified:
multiple directories must not introduce competing basenames without a reviewed
unique resolution. Match Torch's exact directory probes and DLL glob to the
prepared census. Permit only the exact flags/paths/library names enumerated in
the initialization plan. Intercept Python-visible ctypes/os/torch loader entry
points before their use; a native equivalent must be statically traced and
covered by the loaded-image observer. Unknown native loading is a failed run,
not proof that the observer prevented its initializer from executing.

For this first L implementation, Torch's legacy PATH-mutation/LoadLibraryW
fallback is refused before that branch's effect. It is not needed to claim a
successful import: if the reviewed flags path cannot load, the attempt fails
and requires separate design/preparation review. A wrapper must allow reviewed
ctypes signature assignments without handing out the original unguarded callable.
Any added search directory, broad discovery or environment mutation outside the
finite plan refuses. No process-wide detour/injection or machine policy change
is authorized by this design. If source tracing and these gates cannot establish
the required restriction for a loader branch, stop before importing it.

An API-set observation from Q10 is scoped evidence for its exact resident
contracts, not blanket API-set or KnownDLL qualification. Bind refreshed OS,
API namespace and system-image evidence; preserve ambiguity and stated platform
trust. No filename-prefix or version-family guesses may select native targets.

## Resources and ABI assessment

Resource policy distinguishes code, declared import resources, metadata and
forbidden scientific assets. The exact MNE fiducial file, permitted mpl-data
subset, tzdata, certifi and declared Torch metadata remain finite P inputs.
No `.fif`, weight, data-root or package-resource wildcard is an access grant.
Retain and log exact resource path/role/ID/hash, phase, call site, mode and
successful byte count. Guard builtin/io/os/pathlib/resource APIs and early aliases;
deny unknown reads before effects. Python-level coverage does not prove native
file-I/O coverage. Each planned native resource read must have a reviewed
mediated call site and operation-specific evidence; otherwise refuse that
initialization branch before use. Platform-only configuration reads must be
explicit trust entries with reasons, never relabelled observed resource reads.

L declares no subprocess, Git observation, network, diagnostic capture, model
or data access. Collection needs no source-capture fixture. Later V may use the
two exact Git vectors under its own reviewed bounded child protocol; L does not
qualify that protocol or report its controls passed. All L writes are bounded
attempt-owned logs/configuration/report files. No existing pytest basetemp can
be supplied or cleaned. HOME/temp/cache path redirects do not authorize package
downloads or invented resources.

Before imports, compare the exact interpreter architecture/version/extension
suffix, PE machine type and required module initializers/export metadata. Use
bounded parsing; do not invoke arbitrary exports as probes. The plan must name
the exact noncomputational version/ABI getters and required native symbols,
including forwarder/delay-import policy, before implementation review. After
each selected extension initializes, reconcile the actual module/image origins,
metadata versions and those safe queries. Native initialization failure, missing
symbols or incompatible metadata refuses before canonical/candidate import.

The installed Torch 2.13.0+cu130 / torchaudio 2.11.0 pair is an open compatibility
risk; neither a version string nor torchaudio's CUDA-version check certifies its
full ABI. No package change is authorized here. The L claim is **observed
initialization and required-symbol compatibility for the exact declared path**;
dormant exports, numerical kernels, GPU operation and general package ABI remain
unqualified. The report must state that limit, including unexercised delay imports.

## Exact collection contract

Use a pinned attempt-owned pytest configuration, explicit project root and the
two absolute candidate paths in mapping-then-telemetry order. Required options
include collect-only, importlib import mode, no conftest, plain assertions, no
cacheprovider/stepwise, and no ambient addopts, plugins, `-k` or `-m` filtering.
Disable entry-point autoload and enforce the complete built-in/custom plugin
identity allowlist at registration, not only afterward. Reject unknown options,
entry points and hook wrappers. The implementation must enumerate the exact
built-in list for the pinned pytest version; a version-independent list inferred
from documentation is insufficient. Fixtures may be defined but not resolved.

The runner owns pytest invocation once, and the plugin captures collection
reports, item identities and final session status through owned bounded IPC.
Hook `pytest_fixture_setup`, `pytest_runtest_protocol` and phase-report paths
with pre-effect refusal sentinels; L requires zero fixture setups, test protocols
and setup/call/teardown reports. No JUnit passing-test report is created for L.
Zero test execution is explicit in the record, not inferred from console output.

Require pytest exit 0, no collection error/skip/deselection, and exactly 117
unique full node IDs across the [25 pinned function multiplicities](cho51_p3_local_validation_v1/test-roster.json):
39 mapping and 78 telemetry. Compare each item's original function name, source
module/origin and parameter identity with the static roster; do not split an
arbitrary node ID at `[` and assume the result. Retain the actual ordered IDs and
raw parameter IDs, including escaping/pytest collision suffixes. Reject duplicate,
missing, extra, malformed or reordered items within the observed stream. Static
counts are not an invented expected list of full IDs.

Define `ordered_roster_sha256` as SHA256 of UTF-8 JSON encoding of the ordered
string array, `ensure_ascii=False`, separators comma/colon, no trailing newline;
reject lone surrogates and duplicate IDs before encoding. Bound each node ID to
2,048 UTF-8 bytes and each parameter ID to 1,024. Parent independently computes
the digest and per-function counts from its authenticated received rows. The
first accepted L roster becomes the exact expected roster for V, which must
recollect it unchanged under the same workload/runtime/guard/configuration pins.
No sorting, count-only comparison, or edited test source can repair a mismatch.

## Custody, budgets and output ownership

Keep the local contract's L whole ceiling 300s, work stop 240s, cleanup at most
5s; process/caller 4,096 MiB, Job 5,120 MiB; startup/active available RAM 4 GiB,
disk 20 GiB, one library/Torch worker and hidden GPUs. Two startup samples are
at least 200ms apart. One external UTC/monotonic origin governs preflight,
hashing, initialization, collection, final full verification, cleanup, drain and
actual caller return. Admission must cover that complete original interval.
Check stop/resources/deadlines at least every 250ms and before effects, with an
independent parent watchdog and explicit caller memory/IO coverage. Do not borrow
a fresh window for final rehash or raise a cap after a slow import.

Retain the 25,000-file/4GiB/2GiB/depth32 input limits and 64KiB hash chunks;
stdout/stderr each 1MiB; JSON/report 8MiB, depth32, 200,000 nodes; all attempt
outputs including configuration and logs 64MiB/256 files. Native events and
module/resource rows are byte/node-bounded pages, not a single overlarge JSON.
All counters are exact integers; reject duplicates, nonfinite numbers and
unknown record keys. Limit violations refuse; never truncate an accepted roster
or silently discard native/resource evidence.

Use suspended creation with atomic Job assignment, noninherited unnamed
kill-on-close Job, verified limits/membership and original process handles.
Never reopen/kill by PID. The child has exactly the inherited owned IPC endpoints;
unrelated handles are excluded. Parent authenticates stream ownership at creation
and sequences bounded length-prefixed UTF-8 records; child paths are not result
authority. Use a dedicated report pipe separate from stdout/stderr, with 8MiB
per-frame and 64MiB whole-output accounting; one sequential frame, bounded queue
and backpressure/watchdog. Missing/duplicate/truncated/out-of-order/after-final
frames refuse. The parent publishes create-new outputs, retains original writer
handles, flushes and same-handle rechecks bytes/ID through final acceptance.
No child-created JSON report is accepted by reopening an arbitrary pathname.

Parent retains all input handles and final re-enumeration obligations through
child completion and publication. Rehash every retained input and recheck native
identity, type/link/ancestry, absences and census before release. Parent output
receivers use the already-reviewed explicit sharing capability protocol only
where necessary; strict ordinary reader sharing remains unchanged. Ownership
receipt binds final child exit, observer shutdown, empty Job, EOF, every original
handle release, final verification and original caller interval. Unknown cleanup
prevents acceptance and stays unknown; preserve partial bytes and consumed UUID.

## Acceptance and next implementation boundary

Independent design review checks implementability, source trace, all joins,
guard order, denial-before-effect paths, bounded outputs and failure handling.
Implementation Q cases are separate from the original 26-scenario matrix, the
117 candidates and V's 34 controls; each matrix row records which original
obligations it exercises without claiming those entire matrices complete.

After actual L acceptance, Root may qualify only its exact initialization,
resource and ordered-collection observations. V must reproduce the workload
configuration, package/native/resource choices and roster, with explicitly
reviewed stage-specific control inputs; it needs its own fresh admission. C
remains a later independent external closeout. The old 004 failure, 005 hold,
006 unadmitted status, Q1/other unknown cleanup and UNRESOLVED custody remain.
Scientific cells stay 0/1020 and the final freeze unsigned.

## Platform references and limits

Microsoft documents [process DLL search configuration](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-setdefaultdlldirectories)
and its override behavior; [module snapshots](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-enumprocessmodulesex)
can race and omit datafile mappings. The proposed
[notification API](https://learn.microsoft.com/en-us/windows/win32/devnotes/ldrregisterdllnotification)
may change, and its [callback restrictions](https://learn.microsoft.com/en-us/windows/win32/devnotes/ldrdllnotification)
exclude calls to other modules. These sources informed the bounded design;
they do not qualify this machine or the unimplemented helper. Pinned installed
Python/package sources control version-specific behavior. No native API was
called during design.
