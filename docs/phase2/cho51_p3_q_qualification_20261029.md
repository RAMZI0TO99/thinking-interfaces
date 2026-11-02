# Q supervisor and native retained reader

29 October 2026. Engineering-only Q4 qualification accepted.

Q4 passed **73 test methods, eight timestamp controls and two native supervision
fault controls** under a fresh, single-use admission. The methods comprise
31 preparation-foundation,30 retained-reader and12 protocol tests, with no
failures,errors or skips. The tool returned exit0 in12.8052561 seconds, and the
new operation's owned process,Job,thread,pipe,file and guard lifecycle closed.

The independent [source review](../../runs/coordination/cho51_p3_q_qualification_20261029_q4/source-review.json)
and separate [actual-result review](../../runs/coordination/cho51_p3_q_qualification_20261029_q4/actual-review.json)
have no outstanding findings. [Root qualification](../../runs/coordination/cho51_p3_q_qualification_20261029_q4/root-qualification.json)
adopts this tested scope only. Q1's cause and cleanup remain unproved.

## Implementation and exact scope

The frozen [Q4 implementation](../../tools/local_validation/q4/README.md)
contains the native retained reader,protocol,child entry,supervisor,Job adapter,
PowerShell caller,in-memory C# helper and tests. It composes the unchanged
[preparation foundation](cho51_p3_validation_foundation_20261029.md).
The foundation's original static report retains its then-unexecuted status;
the later Q4 result establishes the31 passing methods.

The reader retains original file and ancestor handles,verifies native file
identity and spelling,refuses hardlinks and reparse/device paths,and performs
bounded streamed reads,hashes and create-new output readback. Q4 uses full
no-follow `os.stat` metadata during enumeration because Windows
`DirEntry.stat` does not populate link counts. Its new real hardlink regression
also covers a file outside the selected suffix. The strict single-link predicate
is unchanged. See the [Q4 reader supplement](cho51_p3_q4_reader_contract_20261029.md).

The caller starts original-clock deadlines and independent watchdogs before
bootstrap evidence writes. A bounded retained journal captures startup stages.
Explicit UTC strings and invariant parsing prevent PowerShell DateTime
conversion from changing an admission window. Eight actual caller controls
exercise UTC acceptance/refusal,expiry,coverage and alternate culture. See the
[Q2 bootstrap supplement](cho51_p3_q2_bootstrap_contract_20261029.md) and
[Q3 timestamp supplement](cho51_p3_q3_utc_contract_20261029.md).

Outer and inner Jobs establish atomic containment before child execution.
Original handles,bounded pipe readers,framed EOF,deadlines,resource limits,
local stop controls and bounded cleanup remain active. The two separate fault
Jobs correctly refused extra frame bytes and a stalled frame; each terminated
its owned Job and completed closure.

This qualifies the tested local scope. It does not complete all26 qualification
scenarios or the original48-case custody matrix. A real reparse-point fixture
was not exercised; instrumented attribute refusals have narrower coverage.
The declared PowerShell/.NET/PDH trust exception is not full loaded-image
attestation or complete dependency closure.

## Fresh admission and actual evidence

Operation: `601d386f-b376-4d35-85fb-617d01579fd9`.
The [admission](../../runs/coordination/cho51_p3_q_qualification_20261029_q4/admission_601d386f-b376-4d35-85fb-617d01579fd9.json)
bound28 exact inputs,732 freshly pinned Python runtime files,and an unused
attempt. The actual review rechecked those pins and782 preserved files with no
mismatches. Tests used35 tiny fixture files totaling601 bytes.

The retained [test report](../../runs/coordination/cho51_p3_q_qualification_20261029_q4/attempts/601d386f-b376-4d35-85fb-617d01579fd9/test-report.json),
[payload](../../runs/coordination/cho51_p3_q_qualification_20261029_q4/attempts/601d386f-b376-4d35-85fb-617d01579fd9/payload.json),
[timestamp controls](../../runs/coordination/cho51_p3_q_qualification_20261029_q4/timestamp-controls_601d386f-b376-4d35-85fb-617d01579fd9.json)
and [external tool record](../../runs/coordination/cho51_p3_q_qualification_20261029_q4/external-audit.json)
are bound by the actual review. Original pending-review flags remain frozen;
the separate actual review and Root adoption resolve those obligations.

The runtime was the admitted local Python3.12.14 and PowerShell7.6.5.
These receipts do not certify changed sources or a different machine/runtime.

| Limit or observation | Q4 result |
| --- | --- |
| Whole/work/cleanup limits |90s /60s /5s; unchanged |
| Actual tool boundary |12.8052561s; successful exit0 |
| Process/Job caps |512MiB /768MiB; caller cap512MiB |
| Peak caller private memory |134,057,984 bytes |
| Peak outer Job memory |82,042,880 bytes |
| Minimum observed outer available RAM |10,971,820,032 bytes; floor4GiB |
| Minimum observed outer free disk |79,303,475,200 bytes; floor20GiB |
| Library threads and devices |One thread; GPUs hidden |
| Owned closure |Outer Job and all three sequential inner Jobs closed; original processes reaped,threads/pipes/files/guard closed |

## Consumed predecessors remain unchanged

| Version | Actual disposition | Accepted evidence and limit |
| --- | --- | --- |
| Q1 |FAILED_CONSUMED_CUSTODY_UNKNOWN |Tool exit-1; no complete caller return or test report; cause,no-child claim and cleanup unproved |
| Q2 |FAILED_CONSUMED_PRECOMPILER_BOOTSTRAP_CLOSED |Guard/journal closure before compiler or child; original-window refusal; no tests passed |
| Q3 |FAILED_CONSUMED_SUITE_ERRORS_OWNED_LIFECYCLE_CLOSED |69/72 methods passed,three native enumeration errors; eight timestamp controls passed; owned lifecycle closed; neither fault Job dispatched |
| Q4 |QUALIFIED_Q4_TESTED_SCOPE |73/73 methods,eight timestamp controls and both fault Jobs passed with owned closure |

Q1's [actual review](../../runs/coordination/cho51_p3_q_qualification_20261029_q1/actual-review.json),
Q2's [actual review](../../runs/coordination/cho51_p3_q_qualification_20261029_q2/actual-review.json)
and Q3's [actual review](../../runs/coordination/cho51_p3_q_qualification_20261029_q3/actual-review.json)
preserve their distinct outcomes. Q2's timezone mechanism is supported by later
metadata analysis; contemporaneous converted operands were not captured.
Q3 exposed the Windows link-count metadata defect repaired in Q4. All four
source versions and spent attempts remain frozen and must not be replayed.

## Next bounded step

Implement and independently review **P dependency-closure preparation**, using
the qualified Q components under an implementation-specific successor contract.
Actual P preparation,loader/collection (L),117-case and34-control validation (V),
and closeout (C) each need their applicable fresh admission and actual review.
The accepted Q4 result is not authority to launch those stages.

The117 candidates and34 successor controls remain unexecuted. Bootstrap004
remains consumed,diagnostics005 held,006 unadmitted and historical custody
UNRESOLVED. Restart,boundary,complete-dependency and scientific claims remain
false. Scientific cells remain0/1020 and the final freeze unsigned.

The12 preceding active documents are preserved in the
[Q-step archive](../history/q_qualification_20261029/ARCHIVE_INDEX.md).
No raw data,weights,historical receipt or frozen source was changed. No commit
or push is part of this step.
