# PC1 supplied projection implementation contract

3 November 2026. This source-only successor implements the accepted
[PC1 design](cho51_p3_provider_contract_design_20261103.md) in a new
[pc1 package](../../tools/local_validation/pc1/README.md). Frozen provider design,
CM6/CM6i/CM6S, SC1 and HB1 sources remain unchanged. Package authorship and independent
source/metadata acceptance are separate; Root publishes the source ledger and
current documentation. No runtime is admitted.

## Exact supplied boundary

The public join consumes three exact canonical ASCII JSON byte strings for
B (binding), I (ingress snapshot) and C (capture summary), an independently
supplied expected operation and a fourth canonical byte string containing the
independently expected B fields. Each byte string is at most8192 bytes, including
its single final LF. Parsing the expected B through the same closed grammar
bounds and checks its fields; it cannot authenticate the independence or origin
of those expectations.

The implementation must reject duplicate/extra/missing fields, noncanonical
encoding, trailing material, invalid exact primitive types, integer booleans,
invalid pins/UUIDs/enums and graph/domain violations. Expected B is never derived
from observed projections. Common operation equality and every expected B field
must match. Both I.binding and C.binding must equal the pin of all canonical B
bytes, including LF. Frozen PC-D01/PC-D02 remain mandatory: BOUND has zero
activity/event bytes and cutoff/late zero; it may retain a binding-stage fault.
Cutoff is independent of model invocation counters; late remains disjoint.

An empty stream/event prefix pin must carry the digest of empty bytes. Nonempty
pins, EOF booleans, counters, state and witness references are supplied claims.
This API does not consume or verify raw events/streams, invocation/capture ledgers,
actor-map/native handles, suite cleanup or original source/runtime provenance.
FROZEN/TERMINAL require a nonempty event reference and nonzero record count as a necessary supplied condition. Nonempty references and those state labels cannot establish actual event count, the missing original grammar or closure.

Results are immutable supplied facts with unconditional false native,
execution and debt authority. A consistent bundle is CONSISTENT_SUPPLIED only.
Refusal classification catches only the dedicated input-contract refusal family.
Unexpected programming errors, allocation failure and cancellation must not be
converted into an accepted negative or consistency result. No caller object is
formatted through arbitrary repr/str for a refusal reason. Original dispatch
always refuses; no native provider, subprocess, file writer or runner is added.

## Cohort and debt conservation

The accompanying roster and debt ledger extend the actual1062/49 source snapshot
only with this package's explicitly named test methods and module pins. Q360 and
S140 remain byte-for-byte fixed and disjoint; S140 remains part of held debt.
Every new method is NEW_TEST_UNQUALIFIED, HELD and unexecuted outside both cohorts.
All702 preceding held rows retain their exact identities, pins, kinds and fields.
The46 CM6S methods remain outside both profiles and separately unqualified.

The registry extension describes source identities; it is not executed discovery,
a runtime manifest, qualification or a new profile. Frozen inner fixtures keep
their own historical census. No new Q/S manifest, replacement predecessor
descriptor, scientific cell or old attempt release is inferred.

## Budgets and checking limits

Four raw projection ceilings total32768 bytes. That is a representation bound,
not peak allocation, elapsed time or a reserved output file. Parsing, duplicate
checking, graph validation, canonical serialization, string encoding, hashing,
immutable result construction, exception unwinding and test/import failure paths
still require whole-operation effect/liveness/timing evidence before runtime.

The separate budget ledger preserves all33 report slots/18890752 bytes and16
fixed closeout roles/3293184 reserved bytes. No operational slot or role is
introduced or transferred. Proposed single-extra-escape summary bounds remain
two8192-byte projections*6+32768=131072 for the guard role, and8192*6+16384=65536
for the caller return. Mandatory future wrappers must fit the stated remainder;
complete actor/sample/ingress/capture/transport populations and final closure
remain unproved.

The original whole90/work60/cleanup5/hard65/child55/suite40/native12/fault2/startup5
seconds, process512MiB/Job768MiB, RAM4GiB/disk20GiB, one CPU/library thread,
hidden GPUs, original stop/cleanup and all file/output caps remain. The200ms
startup rule is minimum separation of two samples, with250ms freshness, not a
bound on the total sample population. F/M and complete peak/time remain open.

Source checks use text, JSON, file pins, link checks and arithmetic. Test bodies
are reviewed but not imported or executed; no Python, project parser/AST,
compiler, native call, runtime test or Git operation is part of this phase.
All32 PC1 design scenarios and earlier32 whole-operation,32 CM6 and24 S140
scenarios remain unqualified; partial supplied examples do not close original
requirements.

Complete original B0/B1 authority/driver, dispatcher/capture/EOF/tool return,
full population packing, last-writer/census/closure, effect and resource
feasibility remain NOT_ESTABLISHED. All seven whole-operation gates remain open.
P, full Q probe,117/V34 and science remain held; all consumed failures,
UNKNOWN custody and prior resolver/continuation obligations retain scope.