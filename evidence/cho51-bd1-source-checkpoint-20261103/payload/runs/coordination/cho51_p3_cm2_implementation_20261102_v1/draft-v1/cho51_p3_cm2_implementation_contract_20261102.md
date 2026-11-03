# CM2 supplied-adapter implementation and roster successor contract

2 November 2026. This source-only implementation follows the accepted
[CM2 design](cho51_p3_cm2_design_20261102.md). Root owns retained/registry/collection,
retained tests and documentation; cm2_callbacks_author owns callback implementation
and callback tests. The independent source reviewer and separate metadata reviewer
are message-only; Root alone publishes the predeclared phase records. Preserve
all predecessor code, designs, receipts and the exact 9,233-file baseline.

## Concrete supplied-data boundary

The new eight-file package is `tools/local_validation/cm2`. No program, Python
import/parser/AST/compiler/native call, tests or Git operation is executed in this
phase. These adapters consume supplied immutable bytes or primitive callbacks.
They cannot read a retained handle, attest a loaded object, execute a case, enforce
a live guard or publish an operational acceptance.

`retained.parse_manifest` accepts canonical cho51_cm2_retained_model_v1 JSON with
exact schema/modules/codes keys. A module row has exactly name,kind,pin,parent,
package_paths,phase,dependencies,object_token,loader_token,parent_token. Source
pins have path/bytes/sha256. Source/source_package/namespace only; all runtime
native/builtin/frozen routes are unavailable. Closed names, parent packages,
unique tokens/path spellings, exact package origin and dependency membership are
checked. The acyclic dependency model has at most 4,096 rows, 256 dependencies
per row and depth128; native INITIALIZING cycle witnesses are not implemented.

Code rows have exactly slot,module,parent_slot,qualname,token,lines. Slots are
ordered unique integers0..65535; parents precede children in the same source and
depth is at most128. There are at most4,096 supplied code rows and4,096 exact
code/line pairs in aggregate. Native code-object identity and compiler witness
extraction remain unavailable. The model intentionally uses the frozen HB1
1 MiB JSON/byte helpers rather than widening their caps to the future4 MiB slot.
Larger inputs/graphs refuse; their feasibility is not inferred.

verify_bytes hashes exact supplied source bytes against supplied pins. reconcile
reparses the original supplied manifest and checks exact before/after tokens,
paths, package and phase rows. Canonical byte comparison rejects bool/int aliases.
None of these tokens is a real loaded-module or retained-file identity. Results
are frozen/defensive and always unauthenticated, with execution acceptance false.

`CallbackModel` accepts one exact operation UUID, finite supplied code/location
and fixture tables, the literal successor selection and a supplied checkpoint.
The checkpoint is not native enforcement. Every mutator has a sticky refusal and
reentry latch. Valid negative callbacks may finish the already active cleanup/end
and suite closeout, but no new case or subcase may start after failfast. PASS
requires supplied method cleanup; later fixture failure remains sticky. Body
SKIP may be followed by actual ERROR callbacks before cleanup_done. Duplicate
duration and primary outcomes, post-PASS callbacks and premature ends refuse.

Duration is an optional exact bounded integer model route, never native time or
default unittest float handling. Trace tuples contain exact integer locations,
at most128 frames, all in the supplied table; no arbitrary object/exception/test
is formatted. Unsupported/unknown/nested routes refuse without fabricating a
completed traceback. Fixture slots each denote one declared callback; multiple
cleanup errors need distinct slots joined to the same selected owner/phase.
Fixture NONE/empty trace is a negative skip. Successful fixtures emit no event.

The event stream retains thirteen fields, canonical ASCII/LF encoding and all
original ceilings:4,096 records,512 bytes/record,2 MiB report. One record/512 bytes
is reserved for a footer. A group interrupted by cap/checkpoint failure remains
an incomplete prefix with sticky refusal, never a successful truncated report.
close_suite and footer are required even for complete supplied success. Every
fact remains unauthenticated and execution_accepted=False, and dispatch refuses.
The production case/suite boundary, independent event verifier and external
original-evidence aggregate remain separate implementation/qualification gates.

## Explicit immutable roster and protocol successor

The [roster artifact](cho51_p3_cm2_roster_successor_20261102.json) declares exactly
16 CM2RetainedTests and16 CM2CallbackTests, with their exact names and test pins.
The new complete source universe is764/32 modules; the proposed selected set is
248, and516 remain outside execution. This is an explicit source-level extension,
not permission to run or hide new tests from full collection. Any further test
addition or identity change needs another reviewed roster/budget successor.

All764 rows/pins/flags/order are checked before deriving the unchanged732/30
CM1 projection and then its unchanged700/28 HB1 projection. The raw and both
derived byte digests are retained. Source registry pins are external to tests;
the registry excludes its own digest. Frozen CM1/HB1 validators are not widened.

cho51_cm2_event_v1 is a new supplied-model schema, with full ordinals0..763 and
the exact248 selection, same thirteen fields/caps and a new literal roster digest.
No conversion of a CM1 raw event transcript or automatic wire compatibility is
claimed. Changing selection size grants no additional time, memory, disk or
output budget, and leaves all existing guard scenarios obligatory.

The 32 new methods contribute44 normal unittest subtest callbacks (44 retained,
zero callback tests). Combined with the predecessor210, conditional normal
mapping is248*3+254+2=1,000 records, at most512,000 bytes. The earlier860-record
result remains scoped to216 methods. These are source/model arithmetic only;
complete failure/trace/serializer/raw-capture sufficiency and runtime costs remain
NOT_ESTABLISHED. No test, actual discovery or new accepted engineering run occurs.

## Review and remaining gates

Records live in `runs/coordination/cho51_p3_cm2_implementation_20261102_v1`, with
candidate/review revisions, conditional exact draft archives, Root source
acceptance, static closeout and one separate closeout review. Prior active pages
are archived under `docs/history/cm2_implementation_20261102`. A finding triggers
preservation of affected frozen bytes before a new candidate. Both reviewers
confirm Root's exact saved message text; no extra review sidecars are created.

Next is the source-only independent event/collection evidence join and the
failure-domain/capture contract for a real case/suite boundary. A runtime loader
or producer cannot be admitted until recursive runtime/effect closure, actual
object/code/trace witnesses, native/provider custody, original transport, full
allocation, asynchronous lifecycle and original timing/memory reserves exist.
Do not replace those gates with successful supplied models. Keep whole90/work60/
cleanup5/hard65/child55, all original resource/stop/ownership/census/publication
guards and P disabled. Full Q32/100/384,117/V34 and science stay held. Historical
consumed attempts, UNKNOWN custody, QD17/16 refusal, open resolver/continuation
debt, G2 refusal and0/1020 scientific cells remain unchanged; freeze unsigned.
