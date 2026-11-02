# Native-memory bootstrap and refreshed preparation

31 October 2026. Engineering only. LP4/LQ4 are implemented and independently
source-reviewed. Fresh native-bootstrap Q2 and separately admitted P2 physical
preparation are independently accepted, with final verification and owned cleanup.

## Implementation and provenance

The [original contract](cho51_p3_native_memory_bootstrap_contract_20261031.md)
and [LP4/LQ4 successor](cho51_p3_native_memory_bootstrap_successor_20261031.md)
bind the shared native-memory bootstrap, exact current authority and fresh
preparation. Startup uses the accepted native `GlobalMemoryStatusEx` sensor
with two timely observations under the original five-second deadline.
Time, RAM, disk, stop, process/Job ownership, stream and final-verification
guards remain. Q uses 90/60/5 seconds and 512/768 MiB process/Job caps; P uses
300/240/5 seconds and 4096/5120 MiB. Both retain four GiB startup/active RAM,
twenty GiB free disk, one configured library thread and hidden GPUs.

The old qualified `PNative` image supplies only the bootstrap sensor, with an
unused empty Job. The fresh `PNative3` image has a distinct assembly identity
and supplies the qualified production owner. Source, actual-review, Root
qualification, bytes and recorded original native identity are checked before
helper use. Frozen Lhost1 still requires a separately reviewed compatibility
successor before it can consume this helper/current authority chain.

The first native-bootstrap Q attempt,
`1a07add9-5fac-40b2-8ff2-18d55e70c385`, reached native readiness but returned no
complete suite frame. Its [actual review](../../runs/coordination/cho51_p3_native_bootstrap_20261031_q1/failure_1a07add9-5fac-40b2-8ff2-18d55e70c385/actual-review.json)
and [Root disposition](../../runs/coordination/cho51_p3_native_bootstrap_20261031_q1/failure_1a07add9-5fac-40b2-8ff2-18d55e70c385/root-disposition.json)
preserve a consumed failure with known owned cleanup and no accepted method
results. [Static review](../../runs/coordination/cho51_p3_native_bootstrap_20261031_q1/failure_1a07add9-5fac-40b2-8ff2-18d55e70c385/static-import-review.json)
identified a stale LP2 import in the isolated LQ3 suite. LP4/LQ4 correct it in
new files and explicitly cover both source generations in the recipe. The
saved missing-frame evidence does not establish its historical cause.

## Accepted Q qualification

Operation `461e5aee-0e0e-41f0-91a1-89f0f4bef712` completed in **47.8957633
seconds**, with native readiness at **0.8586494 seconds**. Its exact 368 methods
passed without failures, errors or skips. Required controls also passed:
eight UTC cases, two native transport/timeout faults, three sharing checks,
five native observer cases and two actual P-bootstrap cases (`accepted` and
`bad_identity`). The identity-refusal case stopped before helper loading.

Independent acceptance checked the seven native build children, eight
supervised children, outer Python process and two bootstrap harness children,
plus original artifact custody, complete final verification and owned cleanup.
The 236 source pins, 1,320 runtime-role pins and 4,200 preserved files matched.
This is scoped mechanism qualification; it does not complete the full 40-scenario
L qualification matrix.

Evidence: [source review](../../runs/coordination/cho51_p3_native_bootstrap_20261031_q2/source-review.json),
[actual review](../../runs/coordination/cho51_p3_native_bootstrap_20261031_q2/actual-review.json),
[Root qualification](../../runs/coordination/cho51_p3_native_bootstrap_20261031_q2/root-qualification.json).
Original tool output and exact integer process identities are retained in the
same phase directory; provisional receipts were not rewritten.

## Refreshed P preparation

The [coverage review](../../runs/coordination/cho51_p3_native_bootstrap_20261031_p2/coverage-review.json)
independently re-enumerated and rehashed the full proposal: **21,115 files,
3,461,555,425 bytes, 11 pin pages and 12 absences**. Its 250 explicit extras
include every current source pin, current authority/artifacts and the old sensor
helper. The metadata-tool limit is 200,000 entries; the original scope record's
2,000,000 typo is explicitly corrected in the separate proposal result and
coverage review. No executable guard was changed.

Separately admitted operation `e0014cf3-271a-472a-9070-cf9873d98e8c` returned
successfully in **116.9565593 seconds**, with native readiness at **0.8812499
seconds**. Its saved result reports the complete selected map, **893 native
images and 4,847 dependency edges**. The caller verified the authenticated
handoff of **100 files / 27,025,901 bytes**, full final input verification and
owned cleanup. Final-verification completion is recorded after result
publication; the original provisional result flags remain preserved.

The [P actual review](../../runs/coordination/cho51_p3_native_bootstrap_20261031_p2/actual-review.json)
and [Root qualification](../../runs/coordination/cho51_p3_native_bootstrap_20261031_p2/root-qualification.json)
accept physical preparation for this operation. They do not qualify per-importer
loader resolution, ABI behavior or L execution.

Root created this milestone document after P returned. Independent review found
that one subsequent entry in the worktree-attributes metadata census; selected
input byte pins remained unchanged. The original final-census proof applies
at release, not to this later documentation state. Later consumers need fresh
census/coverage checks and applicable preparation before reuse.

## Remaining L work

The retained plan is **INCOMPLETE_REFUSED**. It inspected 36 modules, 710,542
source bytes, 91,231 AST nodes and 662 definitions, while deriving no accepted
import edges. It imported no candidate/third-party modules and executed no code
from the selected inputs. The [file-only refusal summary](../../runs/coordination/cho51_p3_native_bootstrap_20261031_p2/plan-refusal-summary.json)
records 7,873 rows: 5,789 calls, 1,346 branches, 538 from-imports, 174 imports,
11 native loads, seven dynamic-code cases, five resources, two dynamic imports
and one reported `SyntaxError` for `test_telemetry`. That diagnostic's cause
remains unestablished; it is not an accepted candidate-test result.

Next is a bounded review of these refusals and the finite initialization,
resource, ABI, guard and plugin decisions, including the syntax observation.
The Lhost consumer needs a versioned compatibility update. Changed mechanisms
then need applicable fresh qualification and refreshed P coverage before any
separately admitted L collection. The 117 candidate tests, 34 successor controls
and later closeout remain unexecuted.

Historical custody remains UNRESOLVED, Bootstrap004 consumed, diagnostics005
held and006 unadmitted. The earlier P startup failure and unknown closure are
unchanged. Scientific cells remain **0/1020** and the final freeze unsigned.
No Git operation or MLflow installation/execution occurred. The planned
separate review of a local MLflow exporter remains in the project plan.

The [pre-change archive](../history/native_memory_bootstrap_20261031/ARCHIVE_INDEX.md)
preserves fourteen exact document snapshots. Source/result acceptance and
current-document closeout are separate records.
