# Separate outer S140 profile, collection and evidence binding

This specifies a future supplied-data successor. It neither edits frozen CM6
sources nor makes their Q360-only parser accept another cohort. All raw facts
remain unauthenticated, execution_accepted=False and unable to discharge debt.
Actual collection/dispatcher/observer behavior remains a separate qualification.

## Membership and full census

S is the canonical manifest in cohort.json: schema cho51_cm6s_cohort_v1,
name CM6-S140-20261103, count140, ordered unique ids and ids_sha256. Its raw pin is
11102 bytes /ceaa4cfa0f05f38de3b58d1806c2380fad7eb213d1023e6733909dceff68b154.
Its LF-terminated ordered identity digest is
746927e2bd26c698ab6a52f232db1c15c7bfb3a40e685b64ec0064c1b2f5b39c.
These are different digest domains. Only this exact S profile is proposed.

Q remains the exact adopted Q360 manifest:36161 bytes /
e654b35a3c8a969d60d8f602f75f967bdf0711b4fb71491d0d0094673ac40dde, identity digest
321e076ba18c3bb413d5c7f70f34b03e3780bce1712e5ff4f03fd7f6e4b60a08.
Q intersects S in zero identities; neither set is an alternative interpretation
of the other's integer indices. Outer case i means S.ids[i],0..139. Inner test
fixtures continue to mean Q.ids[i],0..359. Do not relabel one transcript as the
other, make a500-member union or automatically add future implementation tests.

The current full C is1016 identities/45 modules, digest
34e9e6957665ac22836969dc25345e6c69e6167710a23e1171bdd6658f02f9e2.
The supplemental successor must conserve all1016 identities and45 module pins,
not merely the older876/38 floor checked by frozen CM6. Every explicitly reviewed
later addition must also appear in D and full C with its existing debt kind/pin.
Independent adoption reconciles authentic predecessor/current source and census
evidence; a supplied hash or old baseline alone does not certify that history.

Q-oriented D remains cho51_cm6_expected_census_v1: Q rows COHORT, all656 current
held rows HELD. S membership is a separate proposed qualification view; do not
turn its140 held rows into COHORT in D, mark them skipped/deselected, or rebase
their NEW_TEST_UNQUALIFIED kind to BASELINE_HELD. Outside S are876 source rows
(Q360 plus516 other held); that is not an876-row held-debt claim. A negative S
transcript preserves its exact unstarted S suffix separately from all held debt.

## Independently expected inputs and acyclic contexts

All raw JSON is exact immutable ASCII canonical sorted-key compact JSON with LF.
Keep the original primitive, name, byte/depth/node/container limits. Independent
expected size/hash tuples P_Q,P_S,P_D,P_E and operation O come from the caller's
accepted source/admission boundary, never from observed reports or supplied Facts.
Their presence in a model gives no authenticity or admission authority.

New source input E is closed cho51_cm6s_expected_v1 with fields schema,profile,
anchor,supplement,descriptor,source_set,runtime_set,producer_set. profile is
CM6-S140-20261103; anchor/supplement/descriptor are exact raw pin objects
{bytes,sha256} for Q/S/D. The three manifest-reference hashes must equal D's
references to one combined expected source/runtime/producer input set. This
equality checks consistency only. Actual manifests, dependency/cycle/provenance
and complete original joins remain the CM6-08 open obligation.

Q/S and independent source manifests precede D; D precedes E. The source_set
manifest must exclude D, E, downstream reports and any admission/review artifact
whose pins depend on them. No source/test embeds its own pin. K_Q is the frozen
CM6 context of Q/D/O. K_S is the SHA256 of canonical closed fields:
domain='cho51_cm6s_context_v1',operation=O,anchor=Q.ids_sha256,
supplement=S.ids_sha256,census=D.census.ids_sha256,
expected={bytes:P_E.bytes,sha256:P_E.sha256}.
E pins Q/S/D, so K_S binds them transitively without output or self hashes.

The original full collection C stays cho51_cm6_supplied_collection_v1 with O and
K_Q. Verify all its module/test rows, including every held row, before Q, frozen
H or S projections. The successor must additionally check the current1016/45
conservation floor and independently adopted additions. Frozen CM6 verification
is necessary but insufficient for that newer floor. Reparse immutable C as needed
to form S rows from checked observed bytes, never expected-pin substitutions.

The derived in-memory S view is closed cho51_cm6s_collection_view_v1 with schema,
operation,context=K_S,baseline_context=K_Q,supplement=S.ids_sha256,modules,tests.
Module/test row shapes and exactFalse flags remain those of C. Order tests by S
and modules by ordinal ASCII; include exactly the owners required by S. Keep an
explicit S-to-C map, separate Q/H projections and separate raw/identity digests.
No extra projection file is allocated and full collection is never narrowed to
seven selected modules to avoid original discovery obligations.

## Proposed supplied producer and independent verifier

A future producer accepts raw Q,S,D,E,C,T, the four expected pins and O. Before
usable state or BEGIN it verifies independent inputs/profile, full C and all
required views, then canonical T. It accepts no prevalidated Facts, caller order,
callback, exception object or native handle in place of those checks.

T is closed cho51_cm6s_supplied_tables_v1 with schema,operation,context,codes,
fixtures. Retain CM6 code/slot/owner128/phase/aggregate limits. Fixture affected
indices must be exactly those S positions whose class/module equals the owner.
Q indices, full-C positions and held scheduling flags cannot substitute for them.

The new cho51_cm6s_event_v1 stream has the same thirteen fields as CM6 events:
schema,seq,op,context,event,case,sub,fixture,kind,code,line,count,prefix.
Only O/K_S, S140 header and S indices are valid. Preserve the complete existing
lifecycle, closed subcase/immediate trace, cleanup/duration, fixture/failfast,
restoration/input/footer grammar. Carry CM5-S01/S02 common footer-entry and
secondary-refusal accounting unchanged. Independently parse raw events; do not
use producer replay as the verifier. Unexpected extra/missing/duplicate/aliased
members, schema/context swaps or incomplete evidence refuse, without dropping debt.

Terminal is closed cho51_cm6s_supplied_terminal_v1 with schema,operation,context,
inputs,events,boundary,attempts,settled,in_flight,post_footer_attempts,first_refusal,
refused,producer_detached. inputs is closed anchor,supplement,descriptor,expected,
collection,tables, each the exact retained constructor raw pin object. events
pins the entire stream; boundary stays SUPPLIED_SEALED_CHANNEL_SNAPSHOT. Retain
all counter/latch/detachment conditions. Partial/overflow/secondary-failure state
cannot produce a completed terminal; all-PASS bytes with refused terminal stay
negative. A model seal is not authentic ingress cutoff or actual cleanup proof.

The final closed cho51_cm6s_supplied_join_v1 contains schema,operation,context,
anchor,supplement,descriptor,expected,collection,tables,events,terminal. It reparses
all nine raw inputs and compares all eight pins, retained constructor inputs and
whole events. No self pin, caller Facts or cross-profile alias is accepted.
Only complete S PASS/END with a nonrefused terminal can return
SUPPLIED_SUPPLEMENT_CONSISTENT; valid negative events or refused terminal return
SUPPLIED_NEGATIVE_SUPPLEMENT. These dispositions do not establish original
execution or discharge qualification debt. Operational dispatch remains refused.

## Execution and debt acceptance remain separate

Selecting S does not execute it. All140 methods and their656-row held ledger
remain unqualified in this design. Future actual acceptance needs a separately
reviewed original runner, source/runtime pins, unused attempt, all original
admission/resource/ownership/capture/cleanup controls and independent saved-result
review. A subsequent ledger may record only the exact scoped evidence accepted;
neither raw model agreement nor one cohort's success retires unrelated obligations.
Q regression and S qualification are distinct claims. New successor tests need
their own explicit accounting and later cohort decision; this profile is not
automatically extended to certify its own future implementation.
