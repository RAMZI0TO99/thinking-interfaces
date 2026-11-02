# L implementation, mechanism qualification and refreshed preparation

29 October 2026. This implementation-specific supplement preserves the
[local contract](cho51_p3_local_validation_contract_20261029.md) and the
[accepted L design](cho51_p3_loader_design_20261029.md). Independent source
review, fresh admission and actual result acceptance are separate gates.
The current owner request covers implementation/review, fresh Q and refreshed
P. It does not admit an L collection, candidate execution, V controls or study.

## Sources and authority

New sources live in `tools/local_validation/l1`, `lhost1`, `lplan1`, `lq1`
and `lp1`. Frozen Q10/P10 and earlier attempts remain unchanged. Root owns
Q/P integration and records; the implementation author owns L/host/plan sources.
One separate reviewer examines the final exact source set. A different reviewer
examines original saved results. No external scheduling or acknowledgement is
required. No Git operation is part of this phase.

LQ1 and LP1 are explicit successors, not permissions to replay old launchers.
The existing scoped policy replacement applies only through new exact
implementation adoption. Historical custody, cleanup and full-restart claims
remain unchanged. Candidate tests remain117, successor controls34 and scientific
cells0/1020; static mechanism fixtures do not execute those cases.

## Qualification boundaries

Q retains its90-second ceiling,60-second original-caller work limit and5-second
cleanup limit,512 MiB caller/process and768 MiB Job caps. P retains300/240/5
seconds and4096/5120 MiB process/Job caps. Both retain4 GiB startup/active RAM,
20 GiB free disk, one configured CPU-library thread, hidden GPUs, local stop,
original process/Job ownership, strict EOF, bounded reports and original-handle
cleanup. No clock is reset between compiler children, test children or controls.
Each actual attempt uses a fresh UUID and fresh pins. A failure consumes it.

The Q suite contains inherited foundation/reader/P mechanisms plus L supplied
data tests, host tests, plan-compiler tests and binary transport/PE controls.
Its exact method roster is frozen before review and checked against actual
ordered unittest IDs. Test output uses compact verbosity; the full IDs and
outcomes remain in the bounded report. Existing eight UTC controls, two actual
malformed-frame/timeout controls and three sharing controls are retained.
Five additional fresh owned children exercise a production observer's transient
DLL load/unload and an explicitly separate fixture observer's overflow,
invalid reason, invalid UTF16 and path bound. Fixture faults are positive
refusal tests; they are not successful production observations.

The fresh managed PNative binary retains a one-process P default and adds an
explicit two-process L mode for parent plus collection child. All other caps
and cleanup behavior remain identical. Q observes both exact queried limits
and empty-Job closure, and verifies that a third process-count option is refused.
These empty-Job controls do not claim an executed L parent/child operation.

The40 accepted design scenarios remain an obligation-level matrix, distinct
from the number of test methods. Qualification claims must identify executed
coverage and gaps. No method-count arithmetic establishes the full matrix.

## Native observer build and custody

Q compiles only the reviewed local closed-header C observer and benign fixture.
Pinned Clang `-cc1` uses the explicit Windows x64 target, freestanding/no-builtin
and no system/builtin headers. Pinned lld-link uses the exact generated COFF,
exact kernel32 import library, no default libraries or import-library output,
one linker thread and binary stdout. Pinned llvm-objdump supplies generated
callback disassembly. Tool arguments are fixed in `build_l_native.ps1`.
The installed toolchain's behavior must succeed under Q; source review is not
a compiler or binary-stream qualification.

The stdout route is supported by the inspected upstream
[COFF output selection](https://raw.githubusercontent.com/llvm/llvm-project/main/lld/COFF/Driver.cpp),
[file-creation handling](https://raw.githubusercontent.com/llvm/llvm-project/main/lld/Common/Filesystem.cpp)
and [output-buffer implementation](https://raw.githubusercontent.com/llvm/llvm-project/main/llvm/lib/Support/FileOutputBuffer.cpp).
These sources explain the proposed mechanism; they do not attest the installed
compiler version or replace the fresh binary/pipe qualification.

The compiler dependency role has a separate finite recipe: three exact tools,
their sibling DLL census and one exact import library, at most128 files,
256 MiB/file and2 GiB aggregate. These are read-only streaming input limits,
not increases to process/Job, source, Roslyn or bootstrap-runtime limits.
Every file remains on a strict original read handle with byte/native identity
rechecks; ordinary single-link files and non-reparse ancestry are required.
Original directory handles deny ancestor deletion/rename throughout compilation
and consumer use, including local C/header, toolchain and output ancestry.
The local Windows loader/system runtime remains the explicit platform trust.
No assertion of compiler loaded-image attestation is made.

Each compiler is a sequential original-handle child of a verified Q Job.
Binary stdout and stderr use the existing1 MiB-per-stream bounded capture.
The parent creates COFF/DLL/disassembly outputs from the original pipe bytes;
it does not certify a compiler-created file by reopening its path. It records
each command, exit, original identity, Job/process/pipe closure and resource
observations, including failed work. Generated PE grammar rejects wrong machine,
unexpected exports, ordinal-only exports, forwarders and TLS callbacks.
Production has exactly five observer exports; the injection export exists only
in the separate Q fixture. Callback disassembly must contain the actual named
function and no external calls or unknown relocation targets. Actual review
must inspect the retained generated instructions; a source comment is not proof.

New C artifacts require a reviewed writer-to-reader custody transition because
the loader needs read-compatible file sharing. Parent create-new writer
flush/hash/identity is followed by a read anchor that denies deletion while the
writer is still held. After writer closure, a strict read-only/share-read receiver
must acquire the same native identity and rehash the exact bytes before releasing
the anchor. The strict receiver stays live through all consumers and final
verification. Ordinary changes cause refusal. This local continuity protocol
does not claim protection against a malicious same-user writer. The three
inherited managed-helper/mapping/diagnostic artifacts retain their original
writer-through-consumer contract unchanged.

The native bundle's exact path, hash, length and native identity are passed by
the original caller to each owned supervisor/child. Its closed artifact roles
and UUID paths are validated before native loading. A path in JSON alone is
not authority. Each native case obtains and releases only its exact owned
LoadLibrary reference; the encompassing process/Job lifecycle must also close.

## P coverage and inert plan construction

LP1 retains the complete physical recipe, strict file reader, fresh byte/native
identities, directory/absence censuses, native dependency-edge observation and
full final verification from the accepted P10 design. Its selectors add all
new L/host/plan sources, C/header inputs, accepted L design files and this
supplement. Extra paths include the actual fresh Q-generated native inputs
and reviewed plan specification. Toolchain build inputs are Q dependencies;
they are not added as executable L dependencies.

P additionally invokes the reviewed file-only `lplan1` compiler on exact retained
Python text. A narrow active audit scope permits AST parsing only when filename,
length and hash match the retained physical pin. The execution/import audit
remains unchanged: inspected candidate or installed-library code is never
executed. The plan compiler records source-hash/line/column decisions and all
unresolved imports, branches, resource/native effects and ABI/plugin bindings.
Its paged outputs use the original P retained output writer and unchanged
output limits. Full physical input verification occurs after derivation.

The installed-code superset is physical coverage only. It never becomes an
import allowlist. Missing or stale decisions produce `INCOMPLETE_REFUSED`,
which may coexist with successful physical preparation. Such an outcome is
retained evidence of the remaining design work, not an accepted L execution
plan. A complete output still requires independent review and a separate exact
`ACCEPTED_COMPLETE_L_PLAN` record before L. No future hashes, native identities,
117 ordered node IDs, ABI success or resource observations are invented.

## Acceptance records

Q source status is `ACCEPTED_SOURCE_LQ1`; actual acceptance is
`ACCEPTED_LQ1_TESTED_SCOPE`, followed by Root
`QUALIFIED_LQ1_MECHANISMS_ONLY`. P uses `ACCEPTED_SOURCE_LP1`, a fresh proposed
coverage review, separate admission and actual review, followed by Root
`QUALIFIED_LP1_PHYSICAL_ONLY` only on complete physical verification and closure.
Q's exact five native case outcomes and original bundle identity are joined
into P's qualification chain. P Root acceptance names `accepted_result` and
`accepted_index` for the later L host. The original provisional output flags
are preserved; later records resolve them without rewriting the originals.

The future L source review uses `ACCEPTED_SOURCE_L1` with exact `sources` and
an exact `runtime_manifest` reference. Both the external caller and parent
join those pins before bootstrap or child dispatch. Q source coverage must
include those same implementation bytes. L additionally verifies the accepted
design and its source pins, separate Q/P source and actual reviews, P's exact
Q reference, review ordering, final physical verification and accepted outputs.
The new P actual review status is `ACCEPTED_LP1_PHYSICAL_ONLY`.

L uses the fixed project root and a closed `roots` map (`project`, `runtime`,
`site`). Its executable is the reviewed runtime's `python.exe`; its sole child
entry is `lhost1/bootstrap.py child` with the exact isolated flags, cache option
and nine typed substitution slots. No extra Python switch, script or mode is
admissible. Fresh attempt and cache paths are under
`runs/coordination/cho51_p3_loader_collection_l1/{attempts,disabled-bytecode}`
with the operation UUID; this namespace statement is not an L admission.

Complete-plan acceptance is a closed `cho51_l_complete_plan_acceptance_v1`
record with `schema, author, status, created_utc, plan, derivation, review,
safety`. Its independent `cho51_l_complete_plan_review_v1` has `schema, status,
reviewer, authors, created_utc, plan, derivation, findings, checks, limitations,
safety`, status `ACCEPTED_COMPLETE_L_PLAN_SOURCE`, no findings and a reviewer
outside the authors. Exact plan/derivation pins and review-before-acceptance
ordering are required. The retained derivation must be complete, have no refusal
pages and report no input-code execution. Normal and enriched retained JSON
references have distinct validated shapes; enrichment never discards the byte
or native-identity checks at recipe/roster reads.

If source review or execution refuses, preserve that result and revise only
unfrozen drafts or a new versioned successor as applicable. Never increase
resource caps or omit controls to obtain a passing outcome. Actual L/V/C remain
separate reviewed admissions; the original48-case and26-scenario matrices are
not automatically completed by this step.
