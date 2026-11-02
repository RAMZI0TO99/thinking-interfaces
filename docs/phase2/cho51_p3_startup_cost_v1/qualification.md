# SC1 implementation and qualification obligations

Design only. All SC scenarios below are unimplemented and unexecuted. Scenario
counts are not passing-test counts. Preserve the separate ten QD pure methods,
all36 T01–T36 diagnostic scenarios, all516 held Q methods and every cohort
control. None is discharged by reading sources or inspecting saved QD evidence.

| ID | Required evidence in a future reviewed successor |
| --- | --- |
| H01 | Empty input performs an actual EOF read with the original guard trace. |
| H02 | Length1,65,535,65,536,65,537 and exact maximum-file boundaries preserve hashes and bounded requests. |
| H03 | Many short positive reads, including one-byte reads, preserve bytes and every checkpoint. |
| H04 | Early EOF and one-byte growth both refuse; no stale tail enters a digest. |
| H05 | Returned count greater than request, failed ReadFile and failed rewind refuse with owned cleanup. |
| H06 | A pre-read or post-read live guard failure cannot yield a result or continue another read. |
| H07 | Counter poisoning is reset before each call; unused buffer tail poisoning cannot leak. |
| H08 | collect=False and collect=True yield exact independently owned immutable outputs without alias escape. |
| H09 | Nested invocations and independent readers have distinct scratch and fresh SHA state. |
| H10 | Exact file/aggregate caps, path/ancestry identities, strict sharing and three scoped handoffs stay enforced. |
| H11 | Repeated read_small and S14/S17 verify passes each actually rewind, read and hash; no result memoization. |
| H12 | Allocation failure at first scratch creation preserves the existing guard/cleanup/refusal semantics. |
| M01 | Admitted ABI has size64, alignment8, length/load offsets0/4, available-physical offset16 and all uint64 field widths. |
| M02 | Each sample passes length64 in fresh zeroed storage and receives actual new sensor values. |
| M03 | RAM/disk/private-memory thresholds and equality behavior match existing code exactly. |
| M04 | RAM, disk, process-memory and QPC failures retain the same refusal and fault paths. |
| M05 | Foreground/watchdog concurrency shares no mutable observation buffers and adds no sensor lock bottleneck. |
| M06 | Every existing checkpoint still performs fresh time/stop/cache/resource checks; no sample cache or cadence change. |
| M07 | Native bootstrap RAM sensor and two startup samples remain unchanged. |
| M08 | Layout mismatch refuses before first use; no unreviewed fallback. |
| O01 | Exactly16 paths/caps and in-memory reservations precede allocation-only CreateNew; original readback/close yields the ledger pin required by all subsequent roles. Bootstrap failure consumes charges and prohibits other creates/runtime. |
| O02 | Reviewer delegation is message-only; only Root publishes an exact role through the reviewed writer. |
| O03 | Independently attributable exact-byte source/actual confirmations fit their8,192-byte envelopes in contract_adoption/root_disposition before adoption; missing/mismatched/consumed/overflow cases refuse without another file. |
| O04 | An out-of-ledger path, temporary file, copy, fallback or sidecar causes refusal even with global headroom. |
| O05 | Pre-create ancestry/path/absence/authority/size/charge checks precede exclusive create; immediate original-handle disk-file/one-link/final-path/identity checks precede payload write for allocation and every role. Race/reparse/hardlink/alias/failure preserves charges and closes owned handles without overwrite. |
| O06 | Encoded size uses complete UTF-8 bytes and escaped transport/envelope overhead, including failure paths. |
| O07 | Short write/readback, changed original identity/length/hash or close failure retains charges and refuses. |
| O08 | Failed and unused reservations cannot be released, moved or borrowed;17/16 refuses. |
| O09 | Unsupported capture transport is detected before dispatch; no unreviewed post-run fallback. |
| O10 | Published slot immutability survives reviewer correction; insufficient remaining designated slot capacity refuses. |
| O11 | Raw chunks remain exact, native integers are not rounded, and raw capture is not native custody evidence. |
| O12 | Root disposition is separate from review; closed refusal is never clean-prefix/Q/P/science acceptance. |
| F01 | Full discovered roster partitions the unchanged516, additional10 QD methods and exact new SC methods with no omissions. |
| F02 | All eight modes and each cohort's required controls remain within one original clock; no split-control acceptance. |
| F03 | Original child55/work60/cleanup5/hard65/whole90 and tighter per-mode limits refuse on their boundaries. |
| F04 | Per-stage timing records distinguish nested/overlapping spans and include full final verification/publication/closure. |
| F05 | Unknown costs, source/runtime mismatch, incomplete qualification or unavailable margin prohibit full-Q admission. |
| F06 | Full output bounds include failure/provisional outputs and every metadata copy; no uncharged seventeenth file. |
| F07 | Partial probe passes and old accepted codec results cannot certify a changed successor or replace missing controls. |
| F08 | P remains disabled and all real-source/G2/candidate/scientific obligations retain their original status. |

There are40 SC scenarios (12 H,8 M,12 O,8 F). H/M pure injected checks can compare
exact call traces and values; they cannot establish real native sharing, I/O,
ABI, resource/stop failure or custody. O publication faults and H/M native claims
need actual qualified evidence through a separately reviewed bounded runner.
The current design does not supply or admit that runner. Preserve unexecuted
native cases explicitly rather than counting simulated success as qualification.

Implement the selected changes and metadata writer only in a new versioned
successor; review the exact sources and complete roster/cap/refusal map first.
Then design/review any missing finite qualification and measurement approach.
No second QD-prefix investigation is authorized here. Full Q remains held until
the complete stage/output budget and prerequisite evidence justify fresh admission.
Each admitted cohort later requires distinct actual review and complete closure;
none of these design stages activates P or science.
