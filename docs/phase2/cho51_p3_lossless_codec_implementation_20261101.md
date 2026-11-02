# Supplied-data codec, replay/accounting verifier and fresh Q

Engineering milestone, 1 November 2026. This page records the implementation
successor to the [lossless design and capacity decision](cho51_p3_lossless_state_design_20261101.md).
LP13/LQ13/lplan10 have independent source acceptance and fresh Q acceptance for
484 distinct engineering methods: 384 inherited, 40 resolver, 32 frontier and
28 codec. Both cohorts passed every required control, final input verification
and owned cleanup. This qualifies supplied mechanisms only. Operational P remains
disabled, and every guard and open real-source obligation is preserved.

## Implementation and resolved findings

The supplied-data API packs exact raw evidence and complete state frames into
content-addressed assets, then verifies external pins, transport partition,
historical row joins and expanded replay/accounting. Packing and verification
require an explicit companion-output allocation ledger. This ledger is supplied
data, not physical custody. Repeated historical uses retain their order and
multiplicity; physical sharing never discounts expanded rows, intermediate
states, canonical prefix bytes or retained history.

The verifier returns `VERIFIED_SUPPLIED_STATE`, `INVALID_INPUT` or
`CAPACITY_REFUSED`, naming only completed checks. Live checkpoint failure raises
`LosslessCheckpointRefusal` without a returned result. Every authority flag stays
false. Inputs are supplied bytes/objects; the codec opens no supplied path and
does not parse candidate Python source, import candidates or publish native state.

The [independent findings](../../runs/coordination/cho51_p3_lossless_20261101_q1/source-findings-v1.json)
and [recorded resolutions](../../runs/coordination/cho51_p3_lossless_20261101_q1/source-resolution-v2.json)
remain preserved with the original draft:

| Finding | Resolution and retained limit |
| --- | --- |
| Generator expression effect mismatch | Retain the emitter's exact `generator_protocol` value; reject malformed alternatives. |
| Missing unresolved binding value | Preserve `multiple_bindings` as unresolved debt. |
| Historical resolver epoch mismatch | Retain `future_annotation_unknown` for historical nodes; inherited edge epochs remain unchanged. |
| Native origin incorrectly charged as source bytes | Validate extension-image descriptor sizes as exact nonnegative int64 metadata and matching descriptor/content pins; source/package, raw-asset, output and history limits are unchanged. |

LS10 supplies positive and malformed near-miss cases for all four corrections.
The first executed source then exposed a fixture defect: blind comma-to-CRLF
replacement corrupted a JSON string. The new fixture uses JSON-aware formatting
and converts only serializer-created layout newlines. LS03 checks the exact
comma-containing payload before roundtrip. The strict decoder was preserved.

The final [independent source review](../../runs/coordination/cho51_p3_lossless_20261101_q2/source-review.json)
accepted all 256 common source pins. The 43-file successor comparison found only
the fixture test and README substantive after namespace/contract substitutions;
`lplan10/compiler.py` is byte-identical to the reviewed, executed lplan9 compiler.
All 28 named codec methods remain present. Source authors are project_root,
codec_impl and codec_hardening; producer_review accepted source and
codec_actual_review separately reviews actual results. Root manages admission.

The [fixture qualification contract](cho51_p3_lossless_codec_fixture_contract_20261101.md),
[frozen API and coverage notes](../../tools/local_validation/lplan10/README.md)
and [implementation map](../../runs/coordination/cho51_p3_lossless_20261101_q2/implementation-map.json)
define the exact scope. Static/unexecuted wording in frozen source documents
describes their source-freeze time; subsequent actual acceptance belongs here
and in its separate original records. Executed source bytes are not rewritten
to update that narrative.

## Fresh qualification

Two distinct unused admissions select disjoint rosters under matching source
and runtime pins. Runtime inventory covers 1,320 role-file entries: 732 Python,
169 PowerShell/compiler, 112 native compiler and 307 host, plus the separately
pinned caller. Fresh local resource/stop checks and implementation-specific
contract adoption precede each operation. The exact
[runtime inventory](../../runs/coordination/cho51_p3_lossless_20261101_q2/runtime-refresh.json)
and [rosters](../../runs/coordination/cho51_p3_lossless_20261101_q2/expected-roster.json)
are retained.

| Cohort | Operation | Methods | Caller elapsed | Actual disposition |
| --- | --- | ---: | ---: | --- |
| Combined supplied mechanisms | `fd85198e-d81f-41e6-bf07-3c70b9344c5e` | 100: 40 resolver + 32 frontier + 28 codec | 54.9441466 s | Independently accepted |
| Inherited mechanisms | `0ad48608-22b1-49dd-93a4-43adfcba02ec` | 384 | 56.5019682 s | Independently accepted |

Both accepted operations completed final retained-input verification and owned
cleanup with no test errors, failures, omissions or skips. Each cohort passed
eight UTC controls, two actual native fault controls, five native observer
controls, two bootstrap controls and three sharing checks. The sharing methods
are already within the inherited 384; their
separate execution after the 100 does not increase the distinct-method union.
Bootstrap fixture controls are not operational P runs.

The [100-method actual review](../../runs/coordination/cho51_p3_lossless_20261101_q2/lossless-actual-review.json)
and [384-method actual review](../../runs/coordination/cho51_p3_lossless_20261101_q2/actual-review.json)
check original caller return, exact process generations, Job containment,
bounded streams, native builder/handoff evidence, final verification and closure.
The [Root aggregate](../../runs/coordination/cho51_p3_lossless_20261101_q2/qualification-aggregate.json)
accepts the exact disjoint 484-method union and matching cohort pins. Its status
is `ACCEPTED_Q_ONLY_COHORTS`; it grants no P, G2, launch or scientific authority.
Raw tool captures are retained; external JSON derivatives differ only in their
terminal line ending. FILETIME values remain exact int64, never floating-point
identities. Source review, actual Q acceptance and accepted real cases are
separate claims.

Q limits remain 90 whole / 60 work / 5 cleanup / 65 hard seconds, 512/768 MiB
process/Job memory, 4 GiB startup and active available RAM, 20 GiB free disk,
one CPU/Torch thread, hidden GPUs and the project-local stop control. No guard
or accounting change was adopted. No old launcher was replayed.

## Failed attempts remain consumed

| Attempt | Observed failure | Preserved disposition |
| --- | --- | --- |
| `fc2d8d19-df22-406f-86d3-d3226f5f04d9` (LP12/LQ12) | Persisted-frame deadline expired before test-child resume | Failed and consumed; original owned lifecycle independently closed |
| `e1140796-d8e9-45d4-a3ec-15a637d4c6fc` (LP12/LQ12) | 100 methods reported five fixture errors; strict JSON rejection was correct | Failed and consumed; original owned lifecycle independently closed; no passing subset qualifies the successor |
| `131bc595-d023-4e05-b414-4e7029500573` (LP13/LQ13) | 100 methods and separate sharing passed, but final verification hit the work deadline; tool exit 1 with no external return | Failed and consumed; outer/bootstrap custody remains **UNKNOWN** |

The first two [phase records](../../runs/coordination/cho51_p3_lossless_20261101_q1/phase-status.json)
and their separate
[first failure review](../../runs/coordination/cho51_p3_lossless_20261101_q1/failure-actual-review_fc2d8d19-df22-406f-86d3-d3226f5f04d9.json)
and [fixture failure review](../../runs/coordination/cho51_p3_lossless_20261101_q1/failure-actual-review_e1140796-d8e9-45d4-a3ec-15a637d4c6fc.json)
remain frozen. The third attempt's
[independent failure review](../../runs/coordination/cho51_p3_lossless_20261101_q2/failure-actual-review_131bc595-d023-4e05-b414-4e7029500573.json)
and [Root disposition](../../runs/coordination/cho51_p3_lossless_20261101_q2/root-disposition_131bc595-d023-4e05-b414-4e7029500573.json)
preserve the missing outer return. Positive inner-child records do not prove
that missing outer closure. No return was fabricated, no PID-absence inference
was used, and successful successor operations do not close this earlier custody.
Every later operation used a distinct identity and fresh admission under the
same limits; no failed identity was retried.

## Qualification limits and next decision

The 28 named codec methods exercise the disclosed supplied-data cases. They do
not exhaust all valid maximum-size combinations. The 24,000/24,001 row and
10,000/10,001 edge probes use lower-level counters; LS23's real-size lower-bound
probes use placeholder counts, not reconstructed real graphs. Some size tests
use reduced limits. An actual 8 MiB JSON-input boundary is not a valid maximum
graph/manifest witness. Callback tests do not independently qualify a future
native host's storage, publication or custody. The frozen coverage notes record
these distinctions and the bounded indivisible operations between guard samples.

Complete real continuation remains **INFEASIBLE_UNDER_CURRENT_GUARDS**: its first
successor needs at least 31,002 rows against 24,000. The combined-inventory
28,892-node and raw-byte capacity findings retain their conditional scope.
All 724 queued contexts, 1,782 import-frontier records, embedded binding/effect
debt and historical obligations remain open. G2 is `INCOMPLETE_REFUSED`.

Next is an explicit real-source contract/scope decision and independent review
of a justified feasible execution approach. This milestone adopts no guard or
accounting change and enables no real producer or operational P. Complete G2,
matching host capabilities and complete-plan acceptance remain before L.
The 117 candidate tests and 34 V controls remain unexecuted. Scientific cells
remain 0/1020; the final freeze is unsigned. Historical Bootstrap004 remains
consumed, diagnostics005 held, custody UNRESOLVED and 006 unadmitted.

The 12 preceding active documents are preserved in the
[documentation archive](../history/lossless_implementation_20261101/manifest.json).
The preservation baseline covers 7,423 predecessor files, including frozen
source, failure records and archive bytes. Closeout rechecks that baseline, the
256 current source files and 12 archived documents. Five codec Q attempts are
retained across the two source versions: two accepted and three failed/consumed.
The closeout metadata retains the single unresolved outer-custody attempt.
Metadata closeout helpers were updated to record these actual counts and this
limitation; their current bytes are included in the independent document review.
Current documentation does not refresh P custody or census. Raw data, weights
and frozen policy remain unchanged. No commit or push was performed.
