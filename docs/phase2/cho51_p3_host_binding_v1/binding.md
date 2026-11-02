# HB1 binding contract

## Scope and trust root

This is a design for a new bridge/verifier, not a patch to frozen SC1.
The existing three host method signatures and their SC1 projections remain.
A future reviewed successor must supply the bridge, its bounded native channel
handling and any necessary lifecycle integration. No current entry point opens.

Use the accepted local-validation trust model: explicitly reviewed local
Windows/filesystem/observer and immutable inputs; no defense claim against a
hostile same-account actor, privileged/kernel compromise, injected observer or
preexisting writable mapping. Ordinary new writers, changes, copies and missing
events still require detection or refusal. Python audit hooks are not an OS
boundary. No global machine quiet or cryptographic loaded-code attestation is
inferred.

Three separately evidenced layers are required:

1. An original provider integration authenticates Root and delegated peers,
   provides durable atomic operation consumption and a complete attributed
   operation event domain. Its actual interface, retention, failure behavior,
   accounting and resource costs must be documented and independently accepted.
2. A reviewed native bridge owns the original channel, authenticates the
   provider endpoint/process generation under that integration, binds the
   session/operation and supplies bounded cancellable exchanges. The provider
   process is not an unrelated process that this project may kill.
3. A project-side verifier validates bounded frames and exact joins, then
   returns only SC1's closed projections. Pure frame tests qualify this layer's
   checks, never the authenticity, durability or completeness of layer1.

There is no discovered production layer1 or layer2 implementation in this
project. No existing app API, signed export, durable database or event observer
is asserted to have these capabilities. A future provider integration must be
identified by exact implementation/protocol pins, not by the word trusted.
Absent evidence selects UNAVAILABLE and permits no positive host projection.

## Establishment before claim

Provider onboarding and independent source authorization are predecessor inputs.
They cannot depend on this publisher's allocation, review, adoption or result
files: initialize claims before peer lookup and allocation. The source reviewer
must authenticate the exact source/capture/phase authorization independently
before the operation starts. Actual-result authorization cannot exist yet.

The original native channel and authenticated endpoint must be bound to the
project Root, provider epoch, canonical operation UUID, exact authority pin,
reviewed writer/bridge/source/runtime closure, original clock domain and complete
producer/write-domain manifest before claim. Session construction is not proof
that the supplied files were actually loaded. Retained exact-byte loading,
namespace/import paths, bootstrap dependencies, reviewed system images and
before/after-use observations remain necessary under the stated trust model.
Use the existing retained module_bytes/load_source patterns only after a new
implementation-specific source review; do not replay the old launcher.

An endpoint name, PID, JSON field, nonce, file hash, local signature fabricated
by Root, or reread chat transcript alone cannot authenticate that binding.
Native process generation/channel custody and original platform peer provenance
must have independent witnesses. Existing conversation messages may be original
inputs only if the provider actually exposes their exact authenticated identity
and persistence; the currently available collaboration messages do not by
themselves establish the complete production protocol.

## Closed bounded exchange

The proposed bridge uses one sequential request at a time on its original owned
channel. It spawns no extra project worker/service or parallel computation. A
provider that requires such resources needs a separately reviewed compatible
successor; it cannot hide them in external infrastructure. All operation-owned
buffers, work and channel time count under the applicable existing limits.

Each exchange has exactly an8-byte prefix, header bytes, then raw payload, with
no secondary escaping, compression, object serialization or arbitrary endpoint.
Prefix bytes0..3 are an unsigned32 little-endian header length H; bytes4..7 are
an unsigned32 little-endian payload length P. Read all8 bytes before allocating
from either length; a torn prefix refuses. Validate1<=H<=4,088 and the applicable
request/response P cap before reading or allocating the body. Compute8+H+P only
after those checks, with exact non-wrapping arithmetic. The supplied complete
frame must have exactly that length: no omitted bytes, padding or extra tail.
The header is strict UTF-8 JSON, at most4,088 bytes, with exactly these fields:
schema, session_id, provider_epoch, operation_id, authority_sha256, request_id,
sequence, method, direction, status, payload_bytes, payload_sha256, clock_domain,
deadline_qpc. Schema is cho51_hb1_exchange_v1. UUIDs use canonical lowercase
spelling; epoch/clock-domain are independently bound opaque tokens up to128
ASCII characters. sequence is an exact integer1..4096, never Boolean; request_id
is a fresh canonical UUID. direction is request or response. status is REQUEST,
OK or REFUSED. No duplicate keys, floats, nonfinite values or unknown fields.
deadline_qpc is canonical unsigned64 decimal text; arithmetic is exact integer.
SHA256 fields are64 lowercase hex characters. Tokens/nonces provide correlation,
not authentication. Responses must match every request join and original channel.

Request payloads are at most4,096 bytes, making the complete request at most8,192
bytes. Response payloads are at most131,072 bytes; prefix+header+payload is at
most135,168 bytes (8+4,088+131,072). Header payload_bytes must equal prefix P;
payload_sha256 covers exactly those P bytes. The native exchange must enforce
the same lengths and reject truncation, extra frames/tails and mismatched joins;
a prefix declaration alone is not proof of complete transport. Peer messages use original
raw UTF-8 bytes, not an escaped JSON copy. Census and claim payloads are strict
closed JSON. At most64KiB is transferred between live checkpoints; no allocation
uses an unvalidated length. The encoder/parser also bounds depth24,100,000 nodes,
4,096 elements per container and exact integers to signed64 unless the field is
explicit native decimal/hex text. Any truncation, extra frame/tail, sequence gap,
wrong session, duplicate response, unavailable payload or digest mismatch refuses.
REFUSED carries only a fixed reason code and bounded diagnostic text up to512
UTF-8 bytes; no runtime/admission authority. It is not converted to empty success.
Its closed payload has reason and detail only. Allowed reasons are UNAVAILABLE,
AUTHORITY, IDENTITY, CLAIM_DUPLICATE, CLAIM_UNKNOWN, MESSAGE, CENSUS_UNKNOWN,
ACCOUNTING, TRANSPORT, DEADLINE, CUSTODY, OUTPUT and SCHEMA.

The4,096-exchange limit is a refusal ceiling, not a runtime allowance. Each
concrete operation must precompute its exact finite call graph and byte maxima
and prove the total within its original budget. Before/after checkpoints alone
cannot bound a blocked synchronous host call.

## Methods and state transitions

| SC1 method | Verified provider evidence before returning | Exact SC1 projection |
| --- | --- | --- |
| claim_operation(op, authority_pin) | Authenticated Root/operation/source session; atomic durable first consumption tied to authority pin and provider epoch; no duplicate or uncertain outcome; accounting proof for the authoritative event | operation_id, authority_sha256, publisher="project_root", claim="CONSUMED_METADATA_ONLY" |
| peer_message(peer, message_id) | Original immutable message identity/bytes, authenticated peer and Root delegation, exact operation/phase/role/pin context, independent authorship, valid publication order where applicable | The original message bytes, at most131,072; SC1 rechecks its closed authorization/review/confirmation schema |
| operation_artifacts(op) | Complete gap-free attributed domain through a fresh barrier, producer/census closure state, all partial/off-directory artifacts, no unknown producer/event/path or accounting overflow | operation_id, paths; exact canonical paths, no duplicates, at most16 |

Method-specific requests also bind the session authority: claim has operation_id
and authority_pin; peer lookup has reviewer and message_id; census has
operation_id. The verified provider body contains the full evidence reference
and bound method result; projection is permitted only after checking both.
Provider evidence reference means an original authenticated event ID in the
qualified provider domain, not a new uncharged project evidence file. Exact
method evidence schemas and native-channel identities must be frozen with the
actual provider integration before positive use; HB1 deliberately has no
generic JSON-to-trust conversion when that provider schema is unavailable.
The standalone supplied-frame parser returns UNAUTHENTICATED parsed data or a
refusal. It cannot mint a production witness or call the publisher projection.
Model tests use a visibly separate model-result type and never install a fake
transport as the production bridge. Positive projection requires the actual
qualified original-channel witness and provider-specific evidence schema.

Bridge state is UNAVAILABLE, ESTABLISHED, CLAIM_SENT, CLAIM_CONFIRMED,
FAILED_CONSUMED or CLOSED. One operation has at most one mutating claim request.
Set CLAIM_SENT before sending any byte that may commit it. After timeout,
disconnect, partial send/reply, provider restart, malformed evidence or uncertain
durability, mark FAILED_CONSUMED with claim outcome UNKNOWN. Never retry/reissue,
release/rearm, substitute another pathname or treat a later absence as unused.
A separately bounded read-only diagnosis may clarify history; it never changes
the consumed disposition or permits reuse. A provider must reject the same UUID
across bridge instances/sessions and after restart, regardless of authority pin.

SC1's failure path may request consumption after the ordinary work guard has
already refused. Only a pre-established, bounded bookkeeping exchange may then
run under the remaining original cleanup allowance: no source load, native
preparation, output create, runtime dispatch or new channel establishment. If
the claim cannot be completed in the remaining allowance, return UNKNOWN and
close owned transport; do not delay cleanup to prove consumption. The provider's
durability behavior must establish that uncertainty can never become a retry.

## Accounting and complete attribution

Retain all16 SC1 roles and3,293,184 reserved bytes within16 files/4MiB. The
allocation-only bootstrap, fixed paths, full failed/unused charges and original
handle publication rules remain. No adapter may create a claim database, lock,
cache, audit export, signature sidecar, transcript copy or temporary file outside
that ledger. Existing create-new claim helpers produce separate artifacts and
are not a compatible host binding.

An authoritative original provider event may be a provenance input; declaring a
new database or journal to be infrastructure does not exempt its writes/copies.
Before binding, the provider accounting contract must distinguish original
platform inputs from every operation-generated file/export/replica and establish
the durable claim without an uncharged seventeenth artifact. If it cannot do so,
the existing SC1 binding is unavailable. Only a separately reviewed accounting/
bootstrap successor within unchanged guards could resolve that incompatibility;
HB1 does not adopt one or mutate the frozen ledger.

The exact producer domain includes Root's publication/capture tools, the owned
caller/supervisor/children/native helpers, and any provider-generated operation
exports. Reviewers are message-only; their accidental file becomes a charged
artifact/refusal, not an exemption. Register exact native process generations,
allowed commands/roots and operation tags before effects. Ordinary new writers
must be detected/refused. A source manifest, directory listing, Python audit log
or publisher-maintained path list alone is insufficient.

The provider must establish complete event capture or complete effect mediation
for that finite governed domain. Cross-directory copies and partial creates count.
Missing provenance, unknown actors, overflow/loss, reset sequence/epoch, ambiguous
alias, unjoined late event or unbounded writer scope refuses completeness. It
does not require scanning arbitrary machine history or claiming kernel security.
Operation-owned domain closure/barrier must prevent unaccounted later writes
from being retrospectively accepted; a plain snapshot is not a producer seal.
Preserve SC1's census before/after creates, before final verification and after
successful backend closure. The channel/provider must remain valid through the
last census and its closure evidence. A foreign-process PID is never killed.

## Parent operation and metadata partition join

Frozen SC1 expects its complete operation census to equal only its published
metadata paths. It has no parent-operation or partition fields. Using Q's UUID
would therefore reject ordinary caller/supervisor/fixture outputs; simply
filtering them out would weaken complete attribution. A different UUID alone
does not solve the accounting join. Positive integration requires a new reviewed
successor that explicitly adopts the following typed design; SC1 is unchanged.

A proposed immutable cho51_hb1_parent_join_v1 has exactly schema,
parent_operation_id, metadata_transaction_id, stage, authority_sha256,
producer_domain_sha256, partitions, fixture_publication and reservations. The
parent and main metadata UUIDs are canonical, distinct and once-only; stage is
COMPONENT_MODEL, COMPONENT_NATIVE or Q, never P.
partitions contains exactly fixtures/supervisor/caller/closeout with the existing
file/byte caps. reservations is the complete finite pre-effect list, at most256
entries; each has exactly path, partition, reserved_bytes, publisher_role and
transaction_id. Every canonical path occurs once, every byte/count charge belongs
to exactly one partition, and all16 closeout roles retain their full fixed caps.
For closeout, publisher_role is one of the16 SC1 names and transaction_id is the
main metadata UUID. Ordinary caller/supervisor/fixture entries have null
publisher_role and parent transaction_id, except the one explicit fixture case
below. reserved_bytes is an exact non-Boolean positive integer within its
partition and original per-file cap; sums/counts retain every full reservation.

fixture_publication is null except an optional single COMPONENT_NATIVE object
with exactly transaction_id, scenario_id and roles. Its canonical once-only UUID
differs from both parent and main metadata UUIDs; scenario_id names the exact
reviewed native HB/SC scenario. roles contains exactly the16 SC1 role names;
each has exactly path and reserved_bytes, with the unchanged role cap. Every
role must match exactly one fixtures reservation with that fixture UUID and
publisher_role, in the reviewed fixed case namespace. No role/path/cap may be
missing, duplicated, shared with another ledger or assigned to closeout. The
inner ledger charges all16 slots/3,293,184 bytes to fixtures; at most16 auxiliary
fixture entries retain parent UUID/null role and at most901,120 bytes. Their
combined32 files/4MiB remain within fixtures160/32MiB and the complete parent.

Derive an inner fixture view only after complete parent-census conservation and
that exact typed correspondence, with purpose NATIVE_FIXTURE and its scenario
pin. It cannot become the production metadata view or a runtime/qualification
grant. COMPONENT_MODEL and Q cannot populate fixture_publication. The
main closeout view, optional fixture view and all remaining parent artifacts
must form disjoint accounted sets; no UUID change or filtered view drops a
partial/failed/copy charge or counts a physical artifact twice.

The exact join/source/producer-domain pins must be independently approved before
claim and effects. Bind the complete join to the immutable allocation, not opaque
scope text. Its lossless representation and all references must fit the existing
allocation/admission envelopes; if they do not, no integration is admitted.
Keep the pin graph acyclic: authority_sha256 names the preexisting authority
body, which contains no digest of this join. A separate original authenticated
preclaim approval binds both exact authority and complete join pins. The later
allocation records those approved references without a self-hash. Missing that
independent two-pin approval refuses; no caller-created approval can substitute.
No new map file, count exemption, duplicate registration, role transfer or
unaccounted provider export is introduced by this design.

The successor's provider interface must authenticate a fresh COMPLETE_PARENT
census for the full governed parent domain, match every artifact or failed
reservation to the immutable map, check all four partitions and overall caps,
and verify no omitted/cross-partition/unknown path or copy. Only then may it
derive the exact metadata transaction view and compare its16 roles to the
publisher state. Both the parent barrier/evidence and derived-view digest must
be joined; a metadata-only listing cannot certify parent completeness. Actual
bytes, failed/partial reservations and all copies remain accounted without
double-counting a file or releasing an unused charge. An unplanned file consumes
and refuses even if the sum is below256. Complete census frames must fit the
unchanged HB exchange cap; oversized parent proof refuses rather than paging
away obligations or returning a prefix. This is a proposed successor interface,
not a narrower interpretation of SC1's existing operation_artifacts method.

## Call deadlines, reviews and lifecycle gate

Proposed per-call ceiling is200ms of the original monotonic clock, further
limited by remaining live work or the permitted cleanup allowance. It is a
design ceiling, not a measured provider latency or permission to extend work.
It includes framing, transfer and response validation, not just the blocking
system call. Cancellation and original-channel closure must also fit the
remaining original cleanup/hard limits; an elapsed deadline is never success.
Maintain the independent watchdog and freshness/stop/resource checks. The
native bridge must support bounded cancellation and original-channel closure;
a Python thread timeout or daemon worker does not prove that a blocked call has
stopped. Failure to prove cancellation/closure remains UNKNOWN. No retry is
hidden inside transport. Clock mismatch/rollback/equality at deadline refuses.

Source authorization is ready before claim. Postpublication confirmations and
actual reviews are new independent messages and cannot be fabricated in advance.
Do not wait for a human/model review inside a bounded runtime child, pause its
clock, refresh its origin, move required verification out of its window, or
precompile/retain runtime work before the clock to manufacture headroom.

Frozen SC1 is a non-resumable in-memory publication transaction. It does not
provide a qualified durable handoff across asynchronous review waits or a
multi-window metadata controller. HB1 identifies this as a lifecycle prerequisite,
not something a host shim may silently fix. Before production integration, a
separately reviewed finite lifecycle must place every publication, confirmation,
original handle/channel closure and original runtime deadline explicitly. It
must preserve failed-transaction no-resume and independent postpublication
confirmation, with no new operational clock or split-Q acceptance inferred.
If the exact unmodified transaction cannot fit, refuse. Local contract C is the
separate P/L/V export stage, not a blanket extension for Q or publisher waits.

Therefore this design can support implementation/review of a bounded supplied-
frame verifier and negative binding path now. It cannot honestly supply positive
production authentication, census, durability, lifecycle or admission today.
