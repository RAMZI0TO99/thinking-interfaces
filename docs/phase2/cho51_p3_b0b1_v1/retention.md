# Witness retention, capture and the finite closure boundary

## Original observations and their owners

H0/G0/S0 must keep producer, recorder and executor identities distinct. A native
capability is an original retained object in the independently adopted host;
B/I/C JSON, binary rows, pins and base64 are only supplied representations.
PC1 remains unchanged and non-authoritative. Every original join needs the
independent native provenance and complete population, not just a fitting row.

For E1, G0 observes S0's two stdout/stderr handles and stores their exact bytes
in the existing caller/stdout.raw and caller/stderr.raw roles. It records every
positive read's stream, ordinal, offset, length, QPC/order and status, plus the
required EOF/error/cancel transitions. Per-stream byte order and observed read
merge order are retained; no cross-thread execution causality is inferred.

H0 separately observes G0's own stdout/stderr, original tool response chunks and
external return. These are different sources from S0's streams. Their full
contents belong to the existing closeout/raw_tool_return and external_return
capture envelopes, with their actual read/chunk/order/EOF/error witnesses in
the existing journal_analysis role. Neither source can substitute for another.

The bounds in packing.json require source/transport proof: S0 contributes<=128
bytes per stream; G0<=256/128; no unbounded zero-byte/status loop; each channel
has a finite declared pending/EOF/error/cancel route. Positive reads are bounded
by their positive byte counts, but statuses need their own explicit bounds.
If the actual channel can violate those populations, admission refuses. Do not
coalesce, omit or relabel read chunks to make the ledger fit.

## Exact lossless record choices

The resource record is80 bytes, with fixed offsets/widths for sequence/kind/actor,
presence/status flags, failing-call identity, begin/end QPC, available RAM/disk,
three process-private values, Job aggregate, native status and ordinal. Unused
reserved bits must be zero. Presence flags distinguish absent/not-yet-created
actors or unqueried values from measured zero. First-failure short-circuit
semantics preserve every query actually made; no subsequent failed call is
silently discarded.

The capture/control record is64 bytes: sequence/kind/actor/channel, ordinal,
presence flags, begin/end QPC, offset/length, native status/auxiliary code,
related invocation and reserved zero bytes. Its offset/length selects exact
retained bytes in the independently expected named role/source; no dynamic path
is supplied. Tables and flags must be closed and versioned. Counters are original
native invocation/read domains, not CM6 model apply counters.

Canonical base64 retains the exact fixed bytes with padding and unused bits
checked by decode/re-encode equality. It does not authenticate their origin.
In a direct JSON array an80-byte row needs108 base64 characters and at most111
bytes with quotes plus row separator; reserve112. A64-byte row needs88 characters;
reserve96 for its complete line and the declared one extra metadata escaping
layer where applicable. Extra wrappers/layers require fresh accounting.

These codecs are design-only and unimplemented. Field meanings, exact width
arithmetic and original population limits are all required; a binary hash alone
cannot prove that observations were complete or native.

## Existing-role packing and limitations

The frozen PC1 field/type domains provide tighter valid-object width bounds
than their8192 input ceilings: B<=688, I<=684 and C<=833 bytes, including LF,
using fieldwise maxima (not necessarily a semantically consistent example).
The derivation counts fixed keys/punctuation, maximal exact UUID/digest/pin/
enum/integer fields and ASCII canonical encoding. Each is conservatively
reserved at1024; input guards remain8192. This does not restrict the accepted
PC1 domain or modify frozen parsers.

E1 does not invent collection/events or a CM terminal. An I projection can only describe a BOUND/REVOKED/DRAINED prefix here; FROZEN/TERMINAL requires nonempty full event grammar, which E1 does not produce. G0's pre-exit C remains INCOMPLETE and cannot claim its own future host/tool/M closure. The existing caller/return.json C summary allowance remains conditional and unchanged; no original complete PC1 terminal join is asserted.

The proposed E1 guard envelope uses the existing caller/guard-closure.json:
up to1024 resource rows at112 bytes, B/I text at one extra6x escaping layer
of1024 each, and4096 bytes of closed wrapper fields; total131072.
No resource row is encoded as an arbitrary doubly escaped JSON dump.
The exact wrapper must use only the named fixed fields, pins, counters and
status enums in packing.json; runtime/schema qualification remains mandatory.

Caller journal reserves384 control/capture rows at96 bytes plus4096 header
bytes=40960, within its131072 cap. Host journal_analysis reserves528 rows
at96 plus32768 wrapper/analysis bytes=83456, within131072. The metadata timing
join reserves320 resource rows at128 bytes (one extra escaping layer) plus24576
wrapper bytes=65536. Those wrapper allowances are upper budgets, not proof that
every existing required field already has a complete compatible implementation.

Complete H0 tool-return text<=8192 in at most64 chunks costs at most49152
escaped payload bytes plus256 chunk syntax and4096 envelope reserve=53504,
within1048576. External text<=4096 costs24576 plus4096=28672, within65536.
These are **E1-specific conditional source/transport bounds**, not a solution for
arbitrary original1MiB output: the frozen6291456-byte control-character
counterexample remains. Unknown actual host wrapping/error/cancel behavior
prevents entry. All33 reservations/owners and16 once-only metadata roles remain.

Source/runtime/actor/input manifests retain their existing roles/caps and full
verification requirements. Their complete current populations and dependencies
are still open. Reserved-unused collection/event/table/terminal roles must be
explicitly absent in E1, not populated with fabricated Q/S discovery/results.
No report space is pooled or borrowed, and every partial/temp/failed write is
charged. Representation arithmetic is not a peak-memory or runtime proof.

## Noncircular closure and retention decision

The required precedence is:
independent H0/source/admission -> native guard/T0 -> original G0/S0 observations
-> revoke/drain -> G0/S0 return/EOF -> externally frozen complete O response
-> exact16-role M publication/review -> original external M finalization.

O and M have distinct identities and scopes. raw_tool_return/external_return
must contain the complete original O response; a later M finalization cannot
be silently appended to, or substituted for, the captured O response. Conversely,
O's complete capture says nothing about M's final writer/handle/census closure.

The last M write cannot contain its own final hash or evidence that its writer
has subsequently stopped. H0 must provide an independently retained original
finalization witness after the last charged write, covering closed file/pipe/
process ownership, full census and the final transport result. The witness's
actual native acquisition, bounded delivery and retention must be demonstrated
without a seventeenth report, hidden sidecar, out-of-clock helper or recursive
self-closure chain. A live host assertion with no accepted retention route is
insufficient for later file-only custody claims.

**This final retention/delivery route is not established by current sources or
by the conditional slot arithmetic.** BD1 names it as the explicit H0
finalize_metadata prerequisite; it does not declare a new authority to make it
true. If the provider cannot meet it in the original budget, complete E1 acceptance
remains refused even when all prefix records fit. Lost original final evidence
stays UNKNOWN/INCOMPLETE_REFUSED as applicable.

A subsequent design/implementation must close this boundary with the actual host,
or return a concrete infeasibility/scope decision preserving the original
obligations. No supplied parser, signed-looking token, conversation, quiet period,
current tool session or successful exit alone establishes the missing witness.

## Qualification and disposition

Original H0 isolation, enforcement, binding, full effects, timer/I/O behavior,
sample schedule, native failure capture and final retention need independent
qualification/adoption before they can support a target experiment. G0/S0 source
review and a correct decoder are separate claims. A possible failed experiment
consumes its attempt and preserves its actual prefix; only independently complete
evidence may qualify its scoped functional outcome.

All765 held rows and the original resolver/continuation/117/V34/science obligations
remain exact. This design offers a concrete native entry and conditional
representation plan; **end-to-end capture/closure packing and whole-operation
feasibility remain NOT_ESTABLISHED**. P stays disabled.