# CM6 expected context, collection and supplied reconciliation

3 November 2026. Source-only implementation of the accepted
[CM6 design](cho51_p3_cm6_cohort_design_20261103.md). One author owns the three
contracts and their tests; Root owns the registry, source census, debt ledger,
documents and records. A different peer reviews source; another reviews metadata
closeout. Preserve all9,503 predecessor inputs and12 archived preceding pages.

## Raw expected-context and collection boundary

parse_expected_context(raw_q,raw_d,expected_q_pin,expected_d_pin,operation)
requires exact immutable raw bytes and separate exact size/hash pin tuples.
Q remains the canonical adopted360-member manifest; its raw pin and ordered
identity digest are different. Independently expected pins are inputs to supplied
checking, not authentic admission. D checks closed schema, canonical encoding,
types/names, ordered full census/module ownership, baseline876 identities/38
unchanged module pins, complete Q/HELD partition and exact held debt tokens.
Added test identities must belong to new modules. Context K retains the accepted
acyclic binding of operation, Q identity digest, C identity digest and D raw pin.
Source/runtime/producer manifest hashes remain supplied references, not verified
original manifests or actual source/runtime custody.

verify_collection(raw_c,raw_q,raw_d,expected_q_pin,expected_d_pin,operation)
reparses expected inputs. It checks all current supplied module/test rows,
including every held row and its exactFalse eligibility flags, before any view.
It then builds a stable Q view and the exact frozen H836 projection from checked
observed rows, independently invoking CM4's raw collection verifier and retaining
the distinct CM2/CM1/HB1 projection hashes. It never substitutes expected fields
to make a historical view pass. Q/C/H ordinals, identity digests and raw report
digests are separately named; a supplied full census is not original discovery.

Facts are frozen defensive values with unconditional authenticated=False and
execution_accepted=False. Internal fixed checkpoints are model mechanics, not
resource guards. There is no original loader, dispatcher, writer or native observer.
CM6 producer/events/tables/terminal/join implementation remains a later step.
Operational dispatch refuses. Frozen CM4/CM5 code and evidence remain unchanged.

## Conservative predecessor comparison

The accepted design explicitly did not claim that a validator receiving only
current D could certify a transition from a predecessor it never received.
reconcile_prior(raw_q,prior_d,current_d,prior_c,current_c,expected_q_pin,
expected_prior_d_pin,expected_current_d_pin,prior_operation,current_operation)
is a separate supplied-data helper for that comparison. It reparses both full
collections/contexts from raw bytes and independently provided expected pins.

The helper accepts only an additive transition: every prior identity, module pin,
schedule and obligation remains exact; additions are held, unqualified tests in
entirely new modules. Removing/renaming prior tests, changing a prior module pin,
promoting tests, clearing debt or silently appending a test to an existing module
refuses. No policy for legitimate removals, code replacements or cohort changes
is inferred; those require a separately reviewed successor. Manifest-reference
hashes may differ as explicitly pinned current inputs; their contents and actual
dependency effects are not authenticated by this helper.

Returned pins and preserved/new/held rows are immutable supplied comparison
facts. They do not certify the caller chose the authentic prior descriptor,
that either collection was observed, that current source contains exactly those
methods, or that all intervening history is accounted for. Independent adoption
review must still reconcile actual prior source/descriptor/census evidence and
current source. No supplied comparison discharges any debt, admits execution or
changes the fixed cohort. Missing prior evidence is never repaired by constructing
a convenient synthetic predecessor.

The [source-phase debt ledger](cho51_p3_cm6_held_reconciliation_20261103.json)
records this step's real static lineage from the pinned preceding source roster
and design adoption. There was no original CM6 runtime descriptor/collection in
the predecessor phase. This first implementation therefore records source-level
baseline conservation, not an invented retained runtime transition. Test-generated
raw descriptors/collections remain explicitly synthetic fixtures only.

## Exact test and budget accounting

The [roster successor](cho51_p3_cm6_roster_successor_20261103.json) adds60 explicit
unexecuted methods:20 context,20 collection and20 reconciliation, in three new
modules. Current source becomes **936 identities /41 modules**. Q stays exactly
**360**, with **576 held**: the prior516 plus60 NEW_TEST_UNQUALIFIED additions.
All prior held identities/module pins/debt tokens are conserved. No supplemental
cohort is adopted; Q360 regression scope cannot qualify these unselected new tests.

Zero new unittest subTest contexts are added. Q conditional arithmetic remains
5*360+3*254+6 =2568 events /1,314,816 bytes /2567 attempts. CM6 event production is
still unimplemented; CM5's actual supplied target remains H2368 events /1,212,416
bytes /2367 attempts. Inner synthetic collection rows and ordinary test loops do
not add outer callback outcomes. A hypothetical future60-test supplemental cohort
needs its own concrete membership/profile/effect/budget review and admission;
no such cohort is approved by this implementation or by recording the new methods.

Q<=64KiB; each D and collection<=1MiB. Current-context/collection input caps sum
2,162,688 bytes (Q+D+C). Pair reconciliation's five distinct raw caps sum4,259,840
bytes (Q+two D+two C). Each input retains graph depth24/nodes100000/container4096;
counts876..4096 and modules38..256 still require aggregate byte/graph fit. Q/H
projection buffers retain1MiB each; nested historical projections, copies, parsed
graphs, hashing and immutable result tuples add chargeable memory. None of these
input sums proves peak memory or whole-operation feasibility.

The accepted future seven-input integration cap sum5,439,488 and closed schema
line346/terminal888/join792 arithmetic retain their design-only scopes. The
unchanged report proposal is33 files/18,890,752 bytes: caller10/10,878,976,
supervisor7/4,718,592 and closeout16/3,293,184. This phase creates no operational
input descriptor, source admission, publisher, runtime output slot or per-debt
sidecar. Future staging/copy/failure writes require original parent accounting.

Keep global256 files/64MiB, fixtures160/32MiB, supervisor40/8MiB, caller40/20MiB,
closeout16/4MiB, per-file8MiB and fixed role caps. Retain whole90/work60/cleanup5/
hard65/child55 seconds; suite40/native12/fault2, startup5; sampling gap200ms/
freshness250ms; process512MiB/Job768MiB; RAM4GiB/disk20GiB; one CPU/library thread,
hidden GPUs and original owned stop/cleanup. No clock reset or outside-clock work.
Child deadline min(T0+55,T0+60-F-M) still needs unproved final-work/margin reserves.
Raw stdout/stderr/tool-return1MiB and external-return64KiB remain; escaped capture,
finite asynchronous closeout, original native custody and complete allocation
are not qualified by supplied parsing or additive comparisons.

## Source evidence and remaining work

The [source/scenario index](cho51_p3_cm6_source_coverage_20261103.json) preserves360
prior anchor method rows and adds60 held method rows, with exact source pins and
direct textual declarations/imports. These420 accounted rows are not420 selected
methods. Pure helper/library/unittest/import and failure-formatting effects remain
open; the index is not exhaustive recursive effects or actual runtime coverage.
All32 CM6 scenarios remain unqualified, including those with new source examples.

Only source edits and file/text/JSON/hash/link/arithmetic checks occur. No Python,
imports, project parser/AST/compiler, native calls, tests or Git. Source acceptance
does not establish executable syntax or test success. Root alone publishes the
predeclared phase records; exact frozen candidates are archived before correction.
Reviewers send exact message-only verdicts and verify saved bytes; final closeout
confirmation remains conversation-only.

P stays disabled. Full Q32/100/384, candidate117/V34 and original runtime/science
remain held. QD a1f12701 is INCOMPLETE_REFUSED17/16; spent failures and UNKNOWN
custody remain unchanged. All18,793 resolver rows,13,406 inventory occurrences,
724 queues,1782 frontiers,1786 loads and3972 effects remain open. Continuation
is still infeasible at least31,002 rows against24,000; G2 refused. Science0/1020,
freeze unsigned. Next is the separately reviewed source-only CM6
producer/verifier/terminal integration, retaining the stable Q and held-test debts.
