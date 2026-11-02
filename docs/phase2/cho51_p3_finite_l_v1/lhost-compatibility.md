# Lhost compatibility successor

Implement `lhost2`, `l2` and `lplan2` as reviewed successors. Keep lhost1, l1,
lplan1, LP4/LQ4 and all receipts unchanged. The design below is not a runnable
launcher or permission to exercise installed packages. Source findings are
bound by [source-trace.json](source-trace.json); future Q/P must cover the actual
successor's complete executed dependency closure.

## Incompatibilities and selected changes

| Retained source finding | Required successor behavior |
| --- | --- |
| lhost1/invoke_l.ps1 uses PerformanceCounter at startup and PNative for the production owner | Adapt the accepted native sampling architecture to an L-specific bootstrap contract; use the exact fresh PNative3 helper and qualified two-process owner |
| authority.py requires P Root field `accepted_index`; current LP4 Root publishes `accepted_physical_index` | Validate an explicit versioned LP4 record adapter with the actual field and exact authority chain; no optional-key fallback |
| bootstrap and supervisor hard-code lp1/l1/lhost1 imports and ordering | Publish an exact reviewed successor module-order/dependency manifest; no stale module aliases or old CLI dispatch |
| runtime.read/verify buffers native files with a64MiB ceiling;12 prepared native images exceed it | Hash retained handles in64KiB chunks and parse bounded PE ranges; never enlarge the whole-image buffer to match the largest DLL |
| native_resolver requires one matching policy row per path | Separate retained image identity from all importer-edge obligations and pre-effect choices |
| caller-frame attribution excludes directory/name prefixes | Bind observer frame exclusions to exact declared code identities and roles |
| resource policy can name a native mediator that the runtime cannot execute | Reject every unimplemented capability during plan materialization and host preflight |

The large-image finding concerns the physical map, not proof that any image was
loaded. Existing368-method Q evidence and successful P preparation certify their
original scope and bytes; neither establishes this new host's operation.

## Bootstrap and ownership

An L-specific bootstrap record binds request/admission refs, source/runtime refs,
implementation review/adoption, current Q root/source/actual records, exact
sensor and production-helper roles, original caller UTC/QPC and stop path.
Use closed schemas and a finite pinned chain. The accepted LP4 bootstrap loader
recognizes Q/P, so do not pass an L request through it or relax its parser. New
L bootstrap code must be reviewed and qualified under fresh Q.

The historical PNative sensor role supplies memory samples only, with an unused
empty Job and no Start capability. Its exact accepted provenance is pinned;
it does not grant current production execution. The current PNative3 helper is
loaded from exact independently accepted fresh-Q bytes and a distinct assembly
identity. Verify exported type/signature identity before constructing it. Never
fall back to whichever PNative/PNative3 type is already loaded.

The production owner uses the reviewed explicit two-process constructor for the
parent and one child, preserving the outer Job and nested ownership requirements.
Querying the Job's limit alone is insufficient: fresh Q must exercise actual
owned parent/child start, stop, refused start and complete closure using benign
project fixtures. No third-party or candidate module is imported by these tests.
Do not create more processes to recover a missing frame or lost child.

Retain the original five-second startup boundary, two good native memory samples
separated by at least0.2s, sample age at most250ms and100ms independent guard.
QPC/UTC origins are captured before bootstrap and never reset. L retains240s
work,5s cleanup,245s caller hard stop within its300s operation ceiling,
4096/5120MiB process/Job caps,4GiB startup/active RAM and20GiB free disk, one CPU
and Torch thread and hidden GPUs. Every bootstrap failure is sticky and invokes
owned cleanup; absent closure evidence stays unknown. No unrelated process is
terminated. Fresh actual availability and the local stop control remain required.

## Authority adapter and source coverage

The adapter explicitly supports `cho51_lp4_root_qualification_v1` with status
`QUALIFIED_LP1_PHYSICAL_ONLY`, `accepted_result` and
`accepted_physical_index`. Validate its complete typed reference chain, including
source/coverage/actual reviews, current Q, exact operation and authority origins.
Match physical actual status `ACCEPTED_LP1_PHYSICAL_ONLY` and the current Q
qualification's exact compatible schema/status. A changed Q/P schema needs a
reviewed adapter version, never generic success-string matching.

Preserve source-versus-actual reviewer independence, exact same-Q relationships,
source/runtime/recipe equality, complete final verification before release,
genuine caller return and owned closure. Original provisional result flags do
not become acceptance by themselves. Root/actual `accepted_result` and
`accepted_physical_index` are content-only refs (path/bytes/SHA256); preserve
that schema. Compare them exactly, then join each to its unique closed
`cho51_lv_file_descriptor_v1` output descriptor in the authenticated caller-return
stdout pinned by Root and verified by the independent actual review. Require
the same operation, accepted handoff and complete output-audit chain. Compare
the joined descriptor's content and native identity to the newly retained
current descriptor. Reject missing, duplicate, malformed, identity-less or
mismatched descriptors; do not treat a content-only ref as an identity check.
Validate exact integer/native identity types without floating-point loss.

For the retained P2 evidence, Root's `references.caller_return` pins
`caller-return_e0014cf3-271a-472a-9070-cf9873d98e8c.json` with SHA256
`953bb313ec067a238aa78434b23ec78cfa09e3e2affa13b723e67da1728a6816`.
Its100 output descriptors include the result and physical index. This is the
concrete compatibility witness; future preparations must supply their own
accepted exact chain. Never add fields to frozen refs or bypass the descriptor
join through an optional-identity `same_ref` fallback.

Plan acceptance additionally binds every derivation input, complete page digest,
counts, decision/effect closure and independent semantic review. A hand-edited
green index or empty refusal array is insufficient. Reacquire the entire declared
census and absences at L0 and final verification; later documents cannot be
ignored to make old P reusable. Any changed member needs fresh preparation.

Keep finite authority limits: at most300 chain records,2000 source entries and
2000 runtime entries at the host. The current Q/P source manifest has a stricter
256-entry limit. Before freezing implementation, budget the exact active
transitive source closure within each consumer's limit. Historical preservation
manifests are distinct from active code authority. Do not omit an executed source
or required review to fit a cap. An over-budget closure refuses and needs a
separately reviewed bounded successor; this design does not raise those limits.

## Retained streaming and ABI interface

Introduce a project-owned `lstore1` library with no CLI or execution entrypoint,
or an equivalent explicitly reviewed versioned retained-reader interface.
Select one interface during implementation review; do not mutate frozen LP4.
The public capability is scoped to a previously admitted exact Ref and its
retained handle. Raw handles and path-open functions are not given to candidates
or serialized policy records. The host continues to own all descriptors.

- `verify_retained(ref)` streams the entire original retained handle, checks
  hash/bytes and native facts before/after, and returns a typed verification
  result. It does not reopen by path or buffer the image.
- `read_code(ref)` remains bounded to the existing8MiB code/record limit and
  verifies the exact retained bytes before compile/parse.
- `read_range(ref, offset, count)` accepts exact nonnegative integers, checked
  overflow and end-of-file arithmetic, count at most65536, and verifies retained
  identity at required checkpoints. It is available only after full verification
  and cannot be treated as proof of a complete file hash.

The ABI parser consumes this capability, not a whole DLL byte string. Set an
8MiB aggregate range-cache cap and64MiB cumulative range-read cap per image,
including repeated reads. Preserve existing structural limits:96 sections,
4096 optional-header bytes,65536 function slots,4096 export names,512-byte
strings and16MiB export directory. Validate every RVA/range/forwarder before
reading; unsupported layouts and cap exhaustion refuse. The existing physical
limits2GiB/file and4GiB aggregate and original time/RAM caps still apply. Full
stream verification has its own file-byte accounting; range reads cannot evade
the original operation deadline. A malformed huge export table cannot allocate
according to untrusted sizes. Qualified synthetic large-image fixtures prove
these mechanisms only; actual installed-image ABI observations remain L work.

Final input verification repeats the whole-handle checks and all census/absence
checks before release, including files that were only range-read. No accepted
digest or earlier P observation substitutes for current retained verification.

## Runtime joins and guard coverage

Create one exact image capability per path/native identity and a finite set of
importer-edge obligations. A DLL notification supplies image observation, not a
requester. Join it to all declared applicable obligations and the separately
observed pre-effect import/search choices. Reject ambiguous or missing choices;
do not require duplicate DLL loads or choose an arbitrary matching importer.
Baseline/platform images have explicit trust roles and reconciliation rules.

Caller attribution uses exact observer code identities and declared frames;
unknown or ambiguous frames refuse. Native/resource mediators are an enumerated
implemented capability set tested before admission. Keep writes denied except
the existing owned observer outputs. Any newly required cache, native read or
external callback capability requires explicit design and qualification.

The L2/L3 epoch transition cannot occur until all required guarded symbols and
aliases are installed and postconditions/sentinels verified. The pytest manager
and its module/instance registration hooks are wrapped before the first relevant
registration; record exact identities without permitting arbitrary plugin code.
Collection emits only actual successor IDs under the candidate amendment.
Preserve bounded transport, schema checking, monotonic state, output retention,
sticky failure, final verification and owned cleanup from the prior design.

## Implementation and evidence boundary

The [qualification plan](qualification-plan.json) adds targeted scenarios to
the existing40 obligations. Supplied-data tests do not discharge real lifecycle,
loader, ABI, plugin or117-collection obligations. All new scenarios are unexecuted.
Independent source review precedes new Q; independent actual review follows it.
Fresh current coverage/P and complete-plan acceptance precede a separate L-only
admission. V controls/tests and external closeout retain their own admissions.
