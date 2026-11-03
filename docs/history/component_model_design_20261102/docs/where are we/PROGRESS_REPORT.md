# What has been done so far?

Updated **2 November 2026 (Asia/Riyadh)**. This report distinguishes executed
engineering qualifications from static implementation and final scientific
results. The current workflow is owned within this project under the
[project execution policy](../PROJECT_EXECUTION_POLICY.md). Source records are
indexed in [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md).

## 1. Current position

The research platform and several linear engineering components are qualified.
The P3 adapter designs and metadata/telemetry contracts are implemented or
statically reviewed, but their runtime validation is incomplete. The final
scientific study has not been executed.

| Area | Retained status |
| --- | --- |
| Historical main benchmark | 5,950 records across 170 participants, seven baseline variants and five seed labels |
| Gate A reference grid | 450 retained fits; exact retrospective amendment accepted on 12 October |
| Adopted Phase II tranche | 51 Cho evaluation targets, four methods, five seeds and five shots/class: 1,020 cells |
| Provenance-aware linear factory | 65 focused tests and one genuine locked restoration accepted |
| Provenance-aware linear parent/worker | 63 focused cases, 27 guard controls and one synthetic engineering episode accepted |
| Canonical metadata boundary | 133 distinct cases, 399 phase reports and 34 distinct controls / 102 instances accepted |
| P3 designs and contract sources | Independent static reviews complete; 117 candidate tests and 34 controls unexecuted |
| Bootstrap004 | FAILED_UNRELEASED_CONSUMED; the original attempt is spent |
| Diagnostics005 | Three sources statically reviewed; deliberate prelaunch hold and no runtime exercise |
| Local custody design/contracts | Six files independently reviewed; three schemas and48 acceptance scenarios; full matrix and actual boundary remain unqualified |
| Boundary implementation | 25 adversarial subset tests passed; bounded raw capture retained32events with explicit truncation and UNRESOLVED boundary |
| Retained reader and auxiliary joins | 45 tests passed and six pinned artifacts read under retained handles; failed v2 test attempt preserved; boundary remains UNRESOLVED |
| Focused provider capture and decoding | 73 passing v5 tests; four supported records decoded from six saved rows; two classic payloads unsupported; historical host association unresolved |
| Custody evidence intake | 25 passing v6 tests; nine retained inputs; explicit UNRESOLVED disposition; no historical host or launch authority |
| Local log recovery |16 passing tests; original command transcript recovered; six Sysmon queries denied |
| Current-byte inventory |19 passing tests; separate accepted742-file retained observation; no historical or launch authority |
| Local validation contract | Independently accepted design;117 candidates and34 successor controls unexecuted; full26 qualification matrix incomplete |
| Preparation foundation | Four supplied-data sources accepted; all 31 methods passed within Q4; later P10 physical preparation accepted |
| Q supervisor and native reader | Q4 accepted: 73 methods, eight timestamp controls and two native fault controls; complete owned lifecycle for this operation |
| P1 preparation engine | Q-only qualification accepted:108 methods including35 new preparation methods, eight timestamp controls and two fault controls; synthetic physical maps only |
| P2 dependency map and file-only caller | Q10: 198 methods/eight UTC/two faults/three sharing checks; P10 accepted 20,406 files, 888 native images, 4,843 edges and owned cleanup in 105.32 seconds |
| L loader/resource/ABI and collection implementation | Source-reviewed; native-bootstrap Q2 accepted 368 methods and required controls; finite plan remains INCOMPLETE_REFUSED; no L collection |
| Startup diagnostic | Source-reviewed; SQ3 accepted 124 methods and required controls; separate D2 accepted with final verification and owned cleanup; last marker is counter-constructor entry |
| Native-memory bootstrap and fresh P | LP4/LQ4 source-reviewed; Q2 accepted 368 methods; P2 returned 21,115 files, 893 native images, 4,847 edges and owned cleanup; physical preparation accepted |
| Accepted final scientific cells | **0/1020** |
| Checkpoint cohort/overlap review | Unresolved in the retained evidence |
| Final named experiment freeze | Unsigned |

Test counts from separate packages are not a scientific completion score.
Each result applies to its exact source, runtime, scope and attempt. An older
pass does not qualify a changed source or a new machine.

## 2. Phase I: research platform and baseline evidence

### Data and preprocessing

Three public datasets were ingested into a unified representation with channel
canonicalization, trial identities, support/query partitions and artifact policy:

| Dataset | Participants | Stored Profile A epochs before the benchmark artifact exclusions |
| --- | ---: | ---: |
| BCI Competition IV 2a | 9 | 5,184 |
| Cho2017 | 52 | 10,520 |
| MMIDB | 109 | 4,917 |
| Total | **170** | **20,621** |

The frozen benchmark artifact rule removes 22 trials, leaving **20,599** retained
trials. Profile A is the narrow-band baseline path. Profile B is the
LaBraM-compatible wider-band, 200 Hz, one-second-patch path; the separately
versioned Cho 60 Hz processing view has all 52 subjects. Two processing views of
one participant are not two independent participants.

Subsequent reconstruction work checked the caches against pinned recordings.
The gap assessment records exact reconstruction for all 170 Profile A subjects;
the BCI and MMIDB reports explicitly document 9/9 and 109/109 subjects. These are
processing-reproducibility results, not proof of who originally generated every
artifact or which recordings trained the pretrained checkpoint. Cho's available
within-class order does not recover global acquisition chronology.

### Evaluation and baseline harness

The platform includes typed data/episode/run contracts, deterministic
configuration, atomic records, grouped/leave-one-subject-out splitting,
support/query isolation, metrics, subject-level summaries, completeness checks,
resume behavior and reporting utilities.

The main Phase I benchmark ran seven variants:

- EEGNet, ShallowFBCSPNet and Deep4Net;
- filter-bank CSP and Riemannian tangent-space logistic regression;
- Euclidean-aligned EEGNet and Euclidean-aligned tangent-space logistic
  regression.

The retained grid contains **315 BCI + 1,820 Cho + 3,815 MMIDB = 5,950 records**.
It reports seed means within participants and subject-level intervals. For
deterministic classical fits, compatible outputs were explicitly reused across
seed-labelled records; these are not five independent fits or support draws.

The main historical matrix fits source and target-support data jointly. A
separate 45-run two-class BCI EEGNet experiment fits sources first and then
fine-tunes on support. Neither is interchangeable with the later Phase II
source-selection/restore/target-adaptation protocol.

### Controls, plausibility and gate interpretation

The retained records include shuffled-label, pre-cue and matched no-future
controls, subject-disjointness checks, exact-copy auditing and high-score
plausibility reviews. The later gap assessment records all **81 original EEGNet
controls** as completed; earlier “remaining 45/36” descriptions are superseded.
The complete-cohort exact-copy audit found no exact copies across 170 subjects
and 20,599 retained trials. This does not rule out every leakage mechanism,
preprocessing confound or checkpoint-exposure concern.

The separate Gate A reference grid contains **450 retained fits**. A 12 October
saved-record audit checked their hashes, split/history fields and retained
ROC-AUC arithmetic without new fitting. The owner accepted Gate A that day
under an exact **retrospective process-based amendment**. Retained seed42
ROC-AUC is **75.6606%**, versus the published **77.15%**. Exact numerical
reproduction, numerical equivalence and a pre-existing acceptance tolerance
remain unestablished. This is not balanced accuracy and should not be mixed
with the Phase II endpoint.

Gate B has documented local deliverables. That fact and the later Gate A
amendment are not a new final scientific Gate B/C sign-off; this review does not
issue one. The old completion matrix contains dated unsigned-Gate-A wording,
which the exact successor acceptance supersedes only within its stated scope.

### Real-time/interface lane

The project implemented LSL replay, a causal received-sample buffer, windowing,
probability-to-decision gating, explicit neutral output, evidence accumulation
and a native command display. A 60-second loopback delivered **7,680/7,680
samples**. The visible held-out replay delivered **6,144/6,144 samples** and
displayed **12/12 windows** over roughly 48 seconds.

All visible-demo decisions were neutral, so **no command was issued**. Saved
epochs had been preprocessed offline. This validates transport, gating and
display behavior for that replay, not useful live brain control or a complete
causal raw-EEG pipeline. The reported processing p95 of about 5.245 ms excludes
four-second acquisition, file handoff and screen paint. CPU fallback was on the
same laptop, not a second physical machine.

## 3. Encoder and adaptation foundation

The project safely extracted and checked retained LaBraM encoder tensors,
implemented named-electrode mappings and patch/shape handling, and reviewed the
local implementation against the reference. A bounded 5 September forward
comparison records **119 exact float32 stage comparisons across seven cases**.
This applies to the tested forward path, not full training parity or a
TUAB/TUEV downstream reproduction. The separate strict float32 joint-permutation
test had a failure; later float64 diagnosis does not erase it.

Linear heads, full/partial tuning, LoRA, bottleneck adapters and support-prompt
mechanisms have implementation and varying levels of integration evidence.
Generic adaptation smoke tests and local prompt prototypes are not faithful
TCPL reproductions. The pretrained checkpoint's actual training-recording
coverage remains a distinct unanswered question even when its tensor bytes
match.

## 4. The adopted 51-target engineering work

After the 13 October owner amendment, separately versioned route, episode,
worker, recorder, selector, publication, tensor and analysis components were
prepared and qualified to varying bounded scopes. They preserve the old
52-target implementation and all 52 source catalogs while retaining only
subjects02–52 for evaluation.

Examples of established component evidence include:

- A recorder collection stage with **20 synthetic cases** and a selection-file
  stage with **43 synthetic cases**, checking the retained 1,020 identities and
  the revised 5,253-step policy. Fabricated complete histories are not measured
  results.
- Four actual synthetic method lifecycles with **69 boundary checks**: four
  claims/intents/engineering successes and **32 observed updates** in total,
  with zero measured scientific cells.
- A staged LaBraM linear source selection: **102 distinct inner folds** plus a
  fresh winning fit, totaling **5,253 updates = 5,151 source + 102 inner-support**.
  Subsequent publication, detached restoration, route and worker qualifications
  extend that chain under their own exact evidence.
- EEGNet complete synthetic selection and genuine source publication, also
  totaling 5,253 updates. Its complete-parent transaction did **not** pass;
  a later separately bounded successful restore does not rewrite that failure.

### Method coverage is uneven

| Method | Established bounded engineering work | What must not be claimed complete |
| --- | --- | --- |
| LaBraM linear | Numerical probes, source folds, complete staged selection, publication/restoration, fresh provenance-aware factory and engineering parent/worker | Current canonical measured-cell parent, real-data whole-case throughput, final study roster and scientific effect |
| EEGNet | Numerical/source-fold/lifecycle work, complete synthetic source selection/publication, later separate restore evidence | Fresh composed current restore/target/recorder/parent chain and accepted study results |
| LaBraM LoRA | Numerical updates, effective QKV change and round-trip checks, source-fold and lifecycle work | Complete current selection/publication/restoration/target/parent chain and study-scale resources |
| LaBraM full tuning | Numerical/trainable-mask/round-trip checks, source-fold and lifecycle work | Complete current source-artifact/target/parent chain, real-data resource envelope and study results |

These methods do not need to be implemented from nothing. They do need missing
stages and their current composition to be demonstrated rather than inferred
from isolated tests.

## 5. Executed engineering qualifications: 25 October

### A. Provenance-aware restoration factory

The new linear factory separates the **historical producer** of selected-source
artifacts from the **current executor** and actual recorder context. It avoids
spoofing Git identity, rewriting historical evidence or weakening source checks.
The historical producer is `4491e2a…`; the accepted current executor/recorder
context is `c177d00…`, with distinct role-specific source bindings.

It passed **65 focused tests** and one genuine identity-locked restoration and
delivery of the actual canonical `LaBraMTunedAdapter`. The successful transaction
strictly restored the selected state with two safe decodes/state loads and two
read-only verifier calls. It did **no source fitting, support update, query or
measured evaluation**. Independent external closeout and the final document
review passed.

This closes the bounded linear factory compatibility problem, not unchanged
canonical single-root factories or all four method chains. The original
17 October gap assessment predates this closure and must be read with this
successor evidence.

### B. Provenance-aware numerical worker and parent

The separately versioned composition passed **63 focused cases** and **27 stdlib
guard regressions**, then one separately admitted actual synthetic engineering
episode: subject02 / linear / seed11 / five shots per class.

One real identity lock spans the backend, factory, two full verifiers, durable
attestation and engineering terminal. Observed work was:

| Operation | Accepted episode |
| --- | ---: |
| Source fitting | 0 |
| Selected restoration / full model construction | 1 / 1 |
| Support trials | 10 |
| Head-only support/gradient updates | 1 |
| Query inference invocations / trials | 1 / 2 |
| Measured scientific cells | **0** |

The synthetic predictions were **[1,0] against [0,1]: 0/2 correct**. This is
honestly reported and is not a real-data performance estimate or evidence of
general model failure. Engineering acceptance was not based on an accuracy
threshold.

The accepted native Job took **590.082323 seconds under a 600-second cap**.
Both physical input audits and full verifiers stayed inside it; only duplicate
post-terminal parent sweeps moved to mandatory separately supervised external
closeout. That closeout, native closure, custody release and final review passed.
Earlier failed and hard-timeout attempts remain preserved and unaccepted.

### C. Canonical-facing read-only metadata boundary

The P1/P2 boundary authenticates genuine canonical types and pinned metadata,
rederives the **1,040 original / 1,020 adopted** route identities, retains all
**52** source catalogs/assets and keeps producer, executor and recorder roles
separate. It returns an immutable compatibility assessment with every execution
and scientific authority flag false.

The unchanged 133-case suite passed in complementary guarded selections:
**A=36, B=44, C=53**. All batches collected the same full ordered set; selected
sets are disjoint and cover all 133 cases. There are **399 passing
setup/call/teardown phase reports** and **133 unique JUnit cases**, not 399 tests.
Each batch passed the same **34 distinct controls**: **102 instances**, not
102 distinct controls.

No production signal/weight verification, array decoding, model restoration,
training, query, physical selection, case claim or measured publication was
performed in the boundary phase. Its numerical ledger is zero. Small dependency
bootstrap-resource reads are separately identified; “metadata only” does not
claim all interpreter initialization is allocation-free.

A separate admitted standard-library aggregate accepted the coverage and custody
joins. Independent batch, aggregate, document and final export-copy reviews
passed. The final metadata export has **505 files / 46,446,590 bytes**, with no
raw EEG, weights or runtime binaries. Its outside-packet copy audit is accepted
with zero findings. This is evidence custody, not a standalone runnable model
distribution or a new runtime qualification.

### D. Problems found and retained rather than hidden

The metadata phase preserved a logging-device refusal, a low-RAM refusal before
any Job, a Windows Git-spelling/pytest-housekeeping failure and a hard 600-second
timeout without complete test results. A static PID-ownership risk in an
unadmitted aggregate supervisor was corrected in a separately reviewed successor;
no actual PID-reuse incident is asserted. An ordinary export-copy suffix bug
also has its preserved partial copy and narrow correction.

These histories explain why attempts, exact source versions, complete results
and custody reviews matter. Progress dots, partial terminals and successful
cleanup alone were not promoted into passing validation.

## 6. P3 designs, contracts and diagnostics: 27–28 October

The P3 adapter and bounded timing-telemetry designs were completed and
independently statically reviewed. The metadata/profile mapping and
supplied-telemetry implementation followed: six candidate files plus eight
operation sources, with **117 candidate cases across 25 test functions** and
**34 guard controls**. These tests remain unexecuted.

A once-only bootstrap004 attempt actually ran on 27 October and refused an
unexpected descendant. The saved record says the child started but was not
reaped; both pipes reached EOF, while custody and operation release remained
false. Its complete caller-return upper bound was 11.1606095 seconds. Timing
within a bound is not successful cleanup. The exact refused row and secondary
cleanup exception were not retained and remain unknown. Independent review
accepted the failure record as **FAILED_UNRELEASED_CONSUMED**, not a passing
bootstrap or a reusable attempt.

Diagnostics005 adds bounded controller/helper identity, query-call ordinal,
first-refused-row and cleanup-stage/exception metadata. Four review findings
were corrected and independently rechecked. Both PowerShell sources parsed
with zero errors, and all 75 predecessor files matched their preserved hashes.
This was static review only: no diagnostics005 function, helper, controller or
test ran. Its deliberate prelaunch hold remains.

The [local custody design](../phase2/cho51_p3_local_custody_design_20261028.md)
and three machine-readable schemas now have a clean independent static review.
The reviewer identified and Root fixed process/Job memory caps, bounded exact
clock counters and strict attempt identities/cross-file joins. All80 predecessor
files remained exact. The48 acceptance scenarios were specified at that design
milestone; later subset tests do not complete the matrix or qualify a current
machine boundary. The proposed full-restart path still requires authoritative provider
qualification and actual evidence, including the missing event-to-host binding.

The [subsequent boundary implementation](../phase2/cho51_p3_boundary_implementation_20261028.md)
adds25 passing adversarial byte-verifier tests and a separate bounded raw Windows
capture. That capture retained32events, hit its cap and reports UNRESOLVED.
Both new operations recorded normal exit and owned Job/process closure. Their
independent source and actual-result reviews are separate;88 predecessors remain
unchanged. This does not execute all48 original design cases or the 117 candidate
tests/34controls, and it does not repair old004 custody.

The [retained-reader milestone](../phase2/cho51_p3_retained_chain_20261028.md)
adds45 passing tests (31 reader,14 auxiliary) and a separate read of six pinned
project artifacts. A first v2 attempt ran44 methods with one error in a directory
rename postcondition; it remains failed and consumed. V3 replaced that nonisolating
postcondition with real constructor-handle closure checks and added a late-failure
case, keeping the reader, auxiliary implementation and guards unchanged. The
266 preserved predecessors include that failed attempt. This establishes only
current local bytes and structural record joins, not actors or a historical host.

The [focused provider milestone](../phase2/cho51_p3_provider_qualification_20261028.md)
adds a seven-family passive capture: six event rows and 1,315 closed native
handles. V4 passed 57 synthetic tests but refused all actual rows because it
confused event and template namespaces. Its source and outcomes remain exact.
V5 separates those namespaces and adds an explicit native-template-fragment
adapter; all 73 tests passed. A separately admitted offline check decoded four
supported records and preserved two classic Binary refusals. Generic template
matching remains strict; Security-log access denial is retained as a gap.
All 458 predecessors remain exact. Source and actual reviews use different reviewers.

The [custody intake milestone](../phase2/cho51_p3_custody_intake_20261028.md)
adds 25 passing tests and an independently accepted nine-artifact retained
assessment. Root issued an UNRESOLVED disposition under the existing schema.
The checker rejects inconsistent inputs and attempts to upgrade authority;
it has no positive execution path. All 499 predecessors remain unchanged.
The [local validation contract](../phase2/cho51_p3_local_validation_contract_20261029.md)
has independent design acceptance. It binds 117 candidate cases, 34 successor
controls and 26 qualification scenarios to separate qualification, preparation,
loader/collection, validation and closeout stages. The two retired shared-window
controls are explicitly replaced by local-window controls.

The [P2 dependency map and file-only caller](../phase2/cho51_p3_dependency_preparation_20261029.md) have accepted Q10 qualification (198 methods, eight UTC controls, two native fault controls and three sharing checks) and accepted P10 physical preparation: 20,406 files, 888 native images and 4,843 dependency edges. The 105.32-second run completed full final input verification and owned cleanup. Earlier failures and unknown cleanup remain frozen; physical preparation does not qualify loader/ABI behavior.

The [native-memory bootstrap and refreshed preparation](../phase2/cho51_p3_native_memory_bootstrap_20261031.md) are implemented and source-reviewed. Fresh native-bootstrap Q2 accepted 368 methods and all required controls, including two actual P-bootstrap cases. Separately admitted P2 returned successfully in 116.96 seconds, reporting 21,115 files, 893 native images and 4,847 dependency edges, full final verification and owned cleanup. P physical preparation is independently accepted for this operation.

The [HB1 verifier/refusal/collection implementation](../phase2/cho51_p3_hb1_implementation_20261102.md) is independently accepted for source only. Its13-file package checks supplied frames, complete parent accounting and exact collection reports; the production host always refuses. All120 new methods remain unexecuted. The literal roster preserves580 existing plus120 new=700 identities across28 modules; the proposed verifier selection is184. Two pre-freeze review observations were resolved. No actual provider, durable claim, native custody, loaded-code witness, complete attributed census, asynchronous review lifecycle, capture bound or runtime feasibility is established. Next is design/review of the finite component-model runner and exact loading/collection/capture/accounting prerequisites. No admission follows; P stays disabled.

The [bounded resolver](../phase2/cho51_p3_bounded_resolver_20261031.md) and [supplied-data codec](../phase2/cho51_p3_lossless_codec_implementation_20261101.md) retain their accepted scoped evidence. The [fixed probe](../phase2/cho51_p3_probe_implementation_20261101.md) remains source-reviewed but fresh Q is NOT ACCEPTED: six consumed attempts, latest32 method and three sharing passes followed by a later control deadline and incomplete final verification. Latest owned cleanup is established;8bf386d1 final caller,6f9c898c final caller/outer/bootstrap and131bc595 outer/bootstrap custody remain UNKNOWN. Historical [QD a1f12701](../phase2/cho51_p3_qd_execution_20261102.md) retains59/42 timing records,37.7609334s prefix,45.4523028s external return, final verification and owned closure, but overall INCOMPLETE_REFUSED for17/16 closeout accounting. No repair, retry or second QD is inferred. [SC1](../phase2/cho51_p3_sc1_implementation_20261102.md) and the [HB1 design](../phase2/cho51_p3_host_binding_design_20261102.md) remain frozen source/design predecessors;54 SC1 and10 QD methods,24 HB/40 SC/36 diagnostic scenarios remain unqualified. Complete-Q timing/output feasibility is NOT_ESTABLISHED.

Full Q probe32/100/384 and every control remain held; all guards remain. No original-package-path custody, continuation or debt discharge is established. All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,1,786 binding loads and3,972 effects remain open. Complete continuation is INFEASIBLE_UNDER_CURRENT_GUARDS: at least31,002 rows against24,000; conditional node/raw-byte findings retain scope. G2 is INCOMPLETE_REFUSED; candidate117/V34 and science remain unexecuted. Old failures stay consumed; documentation does not refresh P custody or census.

The [accepted v8 inventory](../phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain 0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

No old failure is repaired by the scoped inventory. Its result is limited to
current bytes under retained handles; source/review/admission/caller joins and
572 preserved predecessors were checked independently.

The [2 November publication checkpoint](../phase2/cho51_push_checkpoint_20261102.md)
collects the accumulated boundary/reader/provider/intake/inventory/local-validation
source, designs and documentation through HB1, superseding c0cf850. A selected
323-file inert packet preserves exact source/metadata, and12 active pages are
archived before publication-status updates. Other live run evidence and runtime
assets remain local. Publication adds no runtime validation; historical sources
and receipts retain their original identities.

## 7. What remains open

1. **Current executable P3 composition.** The local validation design and
   LP4/LQ4 native-memory bootstrap are implemented and source-reviewed.
   Fresh Q2 accepted 368 methods; fresh P2 returned successfully with complete
   retained verification and owned cleanup, independently accepted.
   The candidate-v2 migration and bounded compiler are implemented. Fresh Q4
   is accepted and P4 returned successfully. Provisional five-source accounting
   is built. The supplied-data lossless codec/verifier has accepted fresh Q384+100, with P disabled. The fixed supplied-byte probe is implemented and independently source-reviewed. Latest32 passing methods and exact artifacts remain provisional: full Q failed a later control deadline. One fresh QD attempt has independently reviewed timing, final verification and owned cleanup facts, but overall INCOMPLETE_REFUSED disposition for17/16 closeout reservations. SC1's startup-cost changes and fixed-slot publisher are implemented and independently source-reviewed;54 new methods remain unexecuted. HB1 design and its supplied-data verifier/refusal/collection implementation are independently accepted for source only;120 new methods remain unexecuted. Next is finite component-model runner design/review and exact loading/capture/accounting prerequisites. Complete-Q timing/output feasibility remains NOT_ESTABLISHED; no clean diagnostic acceptance, full-Q qualification or retry is inferred. The full real continuation is infeasible under unchanged guards;
   an explicit later contract/scope decision and a justified feasible plan must
   precede real producer/P integration. Transitive G2 closure, host implementation,
   final capability joins, complete-plan acceptance and remaining qualification
   and preparation still precede L.
   L, 117/34 validation and closeout need separate admission and actual review.
   Earlier unknown custody remains unresolved; canonical measured-cell
   composition is unqualified.
2. **Method-chain completeness.** EEGNet, LoRA and full tuning need their
   missing current composition stages. The latest accepted composition is
   linear-only.
3. **Checkpoint-specific scientific eligibility.** An authenticated complete
   training-recording/cohort mapping resolving evaluation overlap has not been
   established. No fresh private correspondence check is implied here.
4. **Final scientific freeze.** The narrow Gate A and 51-target decisions retain
   their exact scope. Cohort treatment and the final named freeze remain open.
5. **Study-scale operating feasibility.** A small synthetic episode close to its
   time cap is not a measured complete-case budget. Selection, storage, recovery
   and all 1,020 cases need a viable plan.
6. **Scientific results and analysis.** No accepted final study cells, paired
   LoRA advantage or study-wide predictive conclusion exist yet.
7. **Wider research and interface evidence.** E1 checkpoint probes, wider
   methods/datasets/shots, E3 causal decoding and E4 hardware-reduction work
   remain separate. Useful live brain control is not established by transport
   demonstrations.

## 8. Historical evidence and current rules

Older reports retain earlier populations, pending states, failures and policy
bindings. The adopted population is 51 evaluation targets and 52 available
source subjects. Gate A remains the narrow retrospective acceptance, and the
exploratory margin is not a formal equivalence decision.

Current workflow requirements come from the active
[project execution policy](../PROJECT_EXECUTION_POLICY.md). Historical reports
remain evidence of their original scope and cannot override that policy or
certify a successor. In engineering reports, external closeout means verification
outside the test Job; it remains owned by this project.

The pre-update documentation is preserved in the
[history manifest](../history/project_focus_20261028/manifest.json). The
[project plan](PROJECT_PLAN.md) gives the route forward.
