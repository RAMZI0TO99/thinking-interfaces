# Focused provider capture and supported decoding

28 October 2026, Asia/Riyadh. Engineering-only milestone under the
[project execution policy](../PROJECT_EXECUTION_POLICY.md).

The focused collector retained six Windows event rows across seven bounded
queries. V4's synthetic tests passed, but actual records exposed a namespace
defect. A separately versioned v5 correction passed 73 tests and a separate
offline check: four supported records decoded and matched their retained native
template fragments; two classic Binary payloads stayed unsupported. Historical
host association and the positive custody boundary remain unresolved.

## Implementation and review

Root authored the collector, injected native controls, fixed child/runner,
admission records and documentation. provider_decoder_impl authored the decoder
and decoder tests. Only Root plus one author or reviewer worked at a time.
provider_source_review accepted the exact sources; provider_actual_review,
a different agent, independently reviewed the saved actual outcomes.

The [v4 package](../../tools/custody_boundary/v4/README.md) partitions boot,
clock/lifecycle, power, resume, EventLog service, log-clear and historical process
creation queries. Each family has its own row quota, preventing later routine
events from crowding out the selected families. The collector retains raw XML,
provider GUIDs and versioned template definitions, tracks bounded native handles,
and preserves exhaustion, truncation and errors separately.

V4 passed 57 synthetic/injected methods. Its actual six rows all refused with
wrong event root/namespace: the implementation confused the event namespace
ending in /events/event with the template namespace ending in /events.
This defect was missed by synthetic fixtures and the initial source review.
The v4 source, test result and defective actual decoding remain immutable.

The [v5 package](../../tools/custody_boundary/v5/README.md) separates these
namespaces, adds independent literal-namespace regressions and an explicit
native-template-fragment adapter. The observed API templates omit win/xs
declarations; this is treated as a narrowly declared native format. Generic XML
qualification still rejects the unbound QNames. Native matching uses a closed
input/output scalar table, checks explicit namespace bindings, ordered field
names, provider GUID, event ID/version and original byte/hash pins. Unsupported
arrays, structures, mappings and types refuse. Rendered strings do not prove
recovery of the original ANSI bytes. No template match grants event truth,
historical host identity or restart semantics.

## Actual operations

Each row below has a separate fresh local admission and unused attempt identity.
All four returned actual exit0 with normal child exit, empty/closed unnamed Job,
closed process/thread handles and no cleanup or peak-sampling errors.

| Operation | Attempt UUID | Actual tool chunk | Result |
| --- | --- | --- | --- |
| V4 synthetic/injected tests | 0fb85f7f-5b8b-44ec-ae49-b3cf46d407e3 | d27668 | 57 passed; zero failures/errors/skips |
| V4 passive capture | 076a41b3-fcc1-4553-aa56-a75a7bfcfef1 | e2d8bf | Six raw rows; 1,315 native handles opened/closed; all six initial decodes refused |
| V5 synthetic/injected tests | 365940b5-cb9f-48d9-95ac-cbf7bfa29014 | 2ed012 | 73 passed: 53 decoder and 20 collector controls; zero failures/errors/skips |
| V5 offline decoding | 44283658-a348-4972-b16a-0e17af4aafc4 | 194700 | Four native-fragment matches; two explicit classic payload refusals; no new provider observation |

The v4 capture retained 4,426 UTF-8 event bytes and 27,161 template bytes.
The complete saved payload is 53,785 bytes, SHA256
`7df7f2a813f32588a08cfaa3c1100e905d935f283c28292e9bad62e9371ab906`.
V5 pins that exact payload under retained handles and checks its bytes/hash
again before offline decoding. It does not rerun a historical operation.

| Selected family | Saved event rows | Decoding and coverage |
| --- | ---: | --- |
| Kernel-Boot27 | 1 | ID27/version1 named fields decoded; native fragment matched |
| Kernel-General1/12/13 | 3 | ID12/v0, ID13/v0 and ID1/v4 decoded; native fragments matched |
| Kernel-Power41/42/107 | 0 | Selected query exhausted; no broad absence claim |
| Power-Troubleshooter1 | 0 | Selected query exhausted; no broad absence claim |
| EventLog6005/6006/6008 | 2 | ID6005/6006 classic Binary fields unsupported; metadata enumeration error2 |
| Microsoft-Windows-Eventlog104 | 0 | Selected query exhausted; intact log history not established |
| Security-Auditing4688 for old PID302124 | 0 | EvtQuery error5, access denied; query not exhausted |

System queries span the old external-return bound to the v4 capture cutoff.
The Security query uses the saved old external-entry/return window and three
explicit hexadecimal PID spellings. Clock shifts, other spellings, disabled
auditing, overwritten logs and access denial remain limitations. No elevation,
audit-policy change, system restart or process termination was performed by
this diagnostic phase. Current labels cannot authenticate the host of004.

## Admission, custody and evidence

Each phase used fresh source/runtime pins, a local stop control and a bounded
runner. The small nonnumerical envelope was 4 GiB startup/active RAM, 20 GiB
free disk, 512 MiB process/768 MiB Job commit, a 45-second child, 75-second work
bound and 90-second whole caller. One library worker ran with GPUs hidden;
the parent also had a deadline watchdog. This does not amend006's proposed limits.

The retained Python3.12.14 installation was freshly inventoried: 732 files,
37,294,833 bytes. It remains at the exact previous-runtime path recorded in
[runtime-pins.json](../../runs/coordination/cho51_p3_provider_qualification_20261028_v5/runtime-pins.json).
No environment was installed or moved; the old .venv base remains unavailable.
Source/runtime handles denied write/delete sharing; fresh absent UUID cache
prefixes and isolated Python startup were checked. Windows system libraries
remain the declared platform trust base.

V5 test and offline caller wall times were 5.0216853 and 4.5293258 seconds;
runner times were 4.484 and 3.969 seconds. Sampled child commit was at most
31,645,696 bytes and sampled Job commit at most 37,789,696 bytes across those
two runs. Preflight available RAM was about 9.23 and 9.31 GiB. These are scoped
observations, not a study-scale resource qualification.

| Acceptance record | SHA256 |
| --- | --- |
| [V5 source review](../../runs/coordination/cho51_p3_provider_qualification_20261028_v5/source-review.json) | `30d78398d5b7af02343a59f4e90ad3d00f80df5928eab5aed658d384e6f16b48` |
| [Independent actual review](../../runs/coordination/cho51_p3_provider_qualification_20261028_v5/actual-review.json) | `59a5a6154c28896c2541676cafa32dbc828323b3320465492effb5ce60457162` |
| [Root qualification](../../runs/coordination/cho51_p3_provider_qualification_20261028_v5/root-qualification.json) | `4ef0b2fb80219ad284813319f432cc6d703df1274f058fdc96f7a74fcb945e70` |

Root rechecked 28 evidence pins, 17 source pins, 732 runtime pins and all
458 preserved predecessor files before adopting the actual review. The review
accepts engineering observations with gaps, including v4's failed decoding.
Original provisional receipts retain pending flags; saved genuine external
tool returns and the later independent review resolve them without changing
their bytes. The PowerShell post-return summaries display some parsed times
at local+03; original receipt UTC strings and raw hashes are authoritative.

The previous 12 current documentation pages are retained in the
[pre-update archive](../history/provider_qualification_20261028/ARCHIVE_INDEX.md).
The latest published Git checkpoint remains c0cf850; this work is uncommitted
and no push was performed for this milestone.

## Remaining boundary and next step

The old operation still lacks an authenticated contemporaneous host/boot
association. The selected historical process query was denied, and even a
PID/time/name match would need independent provenance. A local boot-family row
and native template matches cannot establish a complete restart, trustworthy
cross-boot clock ordering or exclusion of persisted execution domains.

Next qualify those association and boundary facts. If the necessary evidence
is unavailable, retain an explicit unresolved disposition and independently
review any proposed change to the boundary contract before a different path.
No restart is requested or implied. Successor006 remains unimplemented and
unadmitted; bootstrap004 remains FAILED_UNRELEASED_CONSUMED, diagnostics005 held.
The117 candidate tests/34controls remain unexecuted, the original48-case design
matrix is not completed by these subset tests, scientific cells remain0/1020,
and the final scientific freeze remains unsigned.
