# Raw collection, event and reference-table join

## Closed supplied descriptor

Proposed join_supplied(descriptor_raw, collection_raw, events_raw, tables_raw,
*, check) accepts four exact immutable byte inputs. Descriptor is canonical
ASCII/LF JSON at most 65,536 bytes, depth/container/node limits no larger than
frozen HB1 helpers. It has exactly these fields:

| Field | Exact supplied value |
| --- | --- |
| schema | cho51_cm3_supplied_evidence_join_v1 |
| operation | Canonical nonzero UUID; matches every raw event op |
| roster | ef626570e8ba7c74e42d8229edafba76c2b27ba8fe9955cdca7e58e5f5f22a11 |
| selection | d9789f9cbe7c6b19252917987b56982ae49a5d964aeb24719fd7161bfca21a6c |
| source_set, runtime_set, producer_set | Each a canonical lowercase 64-hex supplied context digest; opaque, never native authority |
| collection, events, tables | Each an exact object with bytes and sha256 only; positive exact size and lowercase 64-hex digest of the corresponding original input |

Require collection and tables at most 1,048,576 bytes each; events at most
2,097,152 bytes. Total supplied input maxima including descriptor are 4,259,840
bytes. This is input-envelope arithmetic, not peak-memory or operation allocation.
Existing decoded graphs/copies/hash scratch remain chargeable; no runtime
feasibility follows. No filesystem, environment lookup, retained handle or
dynamic import is part of this model API.

Preflight exact primitive types and byte ceilings; parse descriptor and validate
all declared hashes. Then verify the *complete* raw CM2 collection before any
selection/projection/event view. Invoke its pinned raw verifier or equivalent
independent checks, never accept a caller-constructed CollectionFacts. All 764
ordered identities, 32 module pins, false eligibility flags, code owners and
complete report are required. Only afterward retain separate raw CM2, derived
CM1 732/30 and derived HB1 700/28 digests. Do not overwrite original bytes or
describe a projection hash as the observed report hash.

CM2 collection JSON has no operation field. The descriptor binds its raw digest
to a supplied operation context; that does not prove who collected it or when.
The independent join cannot authenticate reused reports, real runtime pins or
original same-operation production from matching strings alone.

## Closed reference tables

tables_raw is canonical JSON with exactly schema,codes,fixtures; schema is
cho51_cm3_supplied_tables_v1. codes is a list of at most 4,096 two-element lists,
sorted lexicographically by exact integer code/line and unique. Bounds are code
0..65,535 and line 1..2,147,483,647. fixtures is a list of at most 4,096 objects
with exactly slot,owner,phase,affected, ordered by unique increasing slot.

slot is exact integer 0..4,095; owner is a safe ASCII HB1 token (1..128 characters)
equal to a selected module or class owner, never an arbitrary prefix. phase is
exactly setup,teardown,cleanup. affected is the complete nonempty ordered list
of selected full-roster ordinals belonging to that exact owner, at most 248;
no duplicates, bools, extras or omissions. Different slots may share owner and
phase. Empty tables are permitted only when the transcript never references them.

Use the exact raw table hash from the descriptor, validate all rows before any
filtering, and create immutable primitive tuples for the independent event
parser. Aggregate row/byte/node limits all apply simultaneously; maximum row
counts do not promise all maximum-sized rows fit 1 MiB. Code tables are supplied
locations, not compiler/code-object witnesses. Fixture tables assert boundaries,
not actual execution. Sorted schema requirements are new supplied-table rules;
they do not change frozen CallbackModel's in-memory input contract.

## Deterministic joining and conservative output

After full collection and table checks, independently parse exact original event
bytes under [event-verifier.md](event-verifier.md). Recompute every hash; never
join on counts alone, accept mutable Facts or cache an earlier successful parse.
Return descriptor/collection/event/table whole hashes, both distinct projection
hashes, exact roster/selection and opaque context digests, observable event facts
and immutable unavailable-evidence labels. Preserve negative transcript status;
never turn a successful collection into successful test execution.

All results are supplied and unauthenticated, with execution_accepted=False.
No bool or supplied native-looking identity can select an accepting runtime
branch. A separate operational entry always refuses. Full collection of a later
checkout with additional verifier tests requires explicit successor roster,
budget and schema adoption; this historical CM2 target is not that current census.

## Original evidence required outside this model

Operational COMPONENT_MODEL_ONLY acceptance remains impossible here. A future
external verifier must join original unused authority, source/runtime identity,
native retained-handle/code witnesses, actual full current collection/selection,
complete original raw events plus actual subcase/lifecycle and final refusal
evidence, final input verification and restoration, original stdout/stderr/tool
capture, full parent census before projection, and original owned process/Job/
pipe/handle closure. Independent actual review must fit the original finite
lifecycle. Missing or ambiguous items refuse; no injected supplied object is a
live capability. This document defines no new lifecycle wire format or sidecar.
