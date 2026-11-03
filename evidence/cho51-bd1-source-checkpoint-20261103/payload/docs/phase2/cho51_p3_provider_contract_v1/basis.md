# Independent trust, driver and provider basis

## What is trusted, and who can establish it

Use the accepted acyclic order B0 -> B1 -> B2 -> B3 from the [whole-operation contract](../cho51_p3_whole_operation_v1/operation.md). B0 is an explicitly adopted original host/OS and enforcement/observation trust boundary. B1 is a bounded prerequisite driver using that boundary. B2 targets use only independently accepted earlier dependencies. B3 is the eventual complete fixed-profile operation. None is made available by this design.

Root must select and independently justify the actual B0 trusted computing base before operational use: exact host installation/session identity, OS primitives relied upon, original native observer/enforcer source and loaded image/runtime identity, acquisition of original process/parent/Job/pipe handles, monotonic clock, stop route, resources, capture and owned-close observations. The selection must state assumptions, access limitations, failure domains and why the candidate cannot alter or impersonate it. Root adoption is an explicit trust decision supported by source and original-boundary evidence; it is not evidence that an unobserved native mechanism works.

The foundational OS authority is a declared trust assumption, not an endlessly recursively tested project node. Every project-written component placed above it still needs independent review and appropriate bounded actual evidence under an already established basis. This package chooses no concrete available provider or executable B0; if that earlier basis cannot be independently established, stay source-only. No current tool session, prior Q/P receipt, file hash, JSON token, PID lookup or candidate-generated signature supplies it.

No component may supply the enforcement or completeness witness by which its own qualification is accepted. Testing a stop, clock, containment or capture component requires an already established independent enforcement/observation basis with sufficient coverage. If no such basis exists, describe that assumption or obstruction explicitly; do not run a self-qualifying target. Target functional correctness may be unknown only inside a pre-reviewed finite effect/failure/resource domain.

B1's future prerequisite manifest must pin its source/runtime/entry point, target and nonclaims, earlier accepted basis, finite commands and type/value domains, maximum calls/recursion/allocation, exact effects including failures, original guards, ownership/output map and complete capture/cleanup route. Unknown enforcement, reachable effects, resource bounds or custody refuse before effects. Distinct prerequisite attempts remain distinct; they cannot aggregate into a passing S140 or Q360 operation.

## Capability and inert projection

A native capability is an original, retained, non-forgeable authority within the accepted boundary. A PC1 witness is only a finite serialized projection of an observation. Parsing, equality, canonical encoding or a valid digest never upgrades a projection into authority.

Proposed binding projection B has the exact fields in packing.json. It binds original operation O (separate from metadata transaction M), an independently expected basis pin, source/runtime manifest pins, actor-map pin, clock-domain and acquisition ordinal. The actor map must independently bind creation identity, image, parent chain, Job membership, native handles and publisher role; a single digest merely references those bytes. The actor map uses the existing supervisor/input-manifest reservation, not a new file. Its actual schema, full contents and fit remain an open prerequisite.

A successful original join requires ALL of:
1. Independently accepted B0/B1 identities and bounded source/runtime/admission evidence, from earlier nodes.
2. Expected O, source/runtime and complete actor-map pins from independent admission inputs, not observed B or supplied Facts.
3. Original acquisition of retained handles and clock/stop/resource/capture capabilities before candidate/bootstrap effects, including pre-Job failure routes.
4. Complete native observations with provenance binding B to that acquisition and the exact operation interval.
5. Final source/runtime verification and independently observed owned closure, subject to the finite publication boundary below.

A supplied checker can check field domains and equality in items1–5's projections, but must always return native_authority=false, execution_authorized=false, debt_discharged=false and dispatch=REFUSED. Even a perfectly matched supplied bundle cannot establish the original predicates.

No native channel or OS API is invented here. Existing SC1 native_backend performs file ancestry/input/open/write/verify/close work; it is not an authenticated host, clock, ingress or capture provider. HB1 frames have an8-byte prefix, header<=4088, request payload<=4096/frame<=8192 and response payload<=131072/frame<=135168. These bounds and hash checks are an unauthenticated parser contract. They do not imply that an8192-byte PC1 projection fits a single4096-byte request; no fragmentation or extra frame is admitted.

## Native observation contract

The original observer/enforcer must operate outside tested mutable Python os/shutil/ctypes globals, mocks, callbacks and exception formatters. One sequential child and the existing outer caller/supervisor topology remain. An observer is a role in that topology, not an added process/service/thread. Every original handle, helper, native allocation, open and thread is explicitly owned and charged.

The observer records actual binding, guard start T0, exact resource observations, stop requests and outcomes, ingress cutoff/drain, stream EOF/error, process/Job return and final ownership. Required observations remain separate; a universal boolean success flag is not acceptable. A retained handle observation must state its interval and owner. A claim of no future activity requires actual capability revocation and closure, not quiet or a last timestamp.

Startup sampling retains the original two samples separated by **at least200ms** and freshness<=250ms. The200ms rule is not a fixed rate or a maximum interval. Existing supervisor checkpoint/watch paths can add samples. No450-record limit follows from90seconds/200ms. Define and prove an original sampling/checkpoint schedule and complete required population before execution; counters/minima alone cannot establish freshness or omitted samples.

All original clocks and resources remain: whole90/work60/cleanup5/hard65/child55/suite40/native12/fault2/startup5 seconds; child deadline min(T0+55,T0+60-F-M), with F/M unproved. Process512MiB, Job768MiB, available RAM4GiB/disk20GiB, one CPU/library thread, hidden GPUs and owned stop/cleanup remain. Every bootstrap, load/hash, observation, publication, failure and final verification cost belongs to the original clock. No paused review, preloaded compilation, invisible helper or other window supplies headroom.

## Acyclic publication and terminal boundary

Use these precedence edges, not an assertion of an implemented schedule:

| Boundary | What may be attested then | What it cannot attest |
| --- | --- | --- |
| Independent admission inputs precede O | Earlier source/runtime/basis and exact intended owners/roles | Its own later hash, later observed success or a future artifact |
| Original guard/binding precedes bootstrap | Acquired authority and guard interval start | Candidate behavior or future cleanup |
| Ingress cutoff and drain precede immutable event seal | All bounded admitted calls settled; revocation and final refusal state observed through cutoff | Closure of the observer while it is publishing |
| Terminal publication follows retained seal | Exact constructor/event pins and observed terminal snapshot | Its own writer's later termination |
| Caller raw join follows terminal | Exact raw inputs, terminal and projections; no invented suffix | Later caller/tool/publisher closure |
| External owned-return observation follows observed child/supervisor return and pipe closure | Actual observed actor/handle/EOF outcomes for named earlier writers | The external observer's own later closure |
| Final metadata and complete census | Account every charged write, including census/publication itself, through a specified finite boundary | A recursively self-signed proof of all future writes/termination |

The final two rows are deliberately **open implementation obligations**, not a completed finite protocol. A source contract cannot resolve them by setting a boolean, omitting the publisher, placing its own final hash in its preimage or starting an unbudgeted extra observer. The future accepted B0 must observe the last project-owned writer from outside its mutable domain. Its trusted OS observation may be the terminal authority only if that exact trust and retention boundary was independently adopted and its delivery/packing/closure is proved. Otherwise refuse.

SC1 current close() rechecks inputs and published refs, closes backend and re-censuses; it does not prove external process/pipe/tool termination. Its nonresumable transaction and postpublication independent confirmations remain. O and M stay distinct. All16 metadata roles are once-only; refusal/partial writes consume the transaction. There is no seventeenth recovery report and no uncharged review sidecar.