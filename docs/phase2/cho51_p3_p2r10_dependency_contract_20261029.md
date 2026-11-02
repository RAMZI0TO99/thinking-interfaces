# P2 revision10 fresh attribute guard and stage timings

29 October2026. New source proposal only. All R9/Q9/P9 sources and evidence are
frozen. Independent source review, fresh Q10/P10 source/runtime pins, unused
admissions, actual tool evidence and independent actual review remain required.
R9 cooperative writer custody, strict P reader, resident observations, raw
namespace/host policy and full preparation/verification obligations remain.

P9 operation `1d498286-518e-47e4-9cb5-be8f595dfb33` retained20,406 physical
files,888 PE observations and4,843 edges in58 provisional outputs. Its saved
result recorded162.116561 elapsed seconds and439,573 resource samples. The
original240-second work deadline was reached during mandatory final verification.
No caller/external closeout proves reaping, Job/pipe/handle/guard closure. Its
independent actual review and Root disposition are required source pins and
retain `FAILED_P2_P_CONSUMED_DEADLINE_CLOSURE_UNPROVED`. Nothing here accepts
those provisional files, retries that attempt or repairs its cleanup uncertainty.

## Equivalent fresh guard predicate

P9's repeated absence checks used full no-follow `os.stat` objects for each
ancestor and leaf, while needing only directory/reparse/device attributes and
presence/error. Source inspection identifies this as a repeated hot path, not
a measured allocation/syscall profile. R10 changes only that metadata API in
the P guard's checkpoint and independent watch loop. Every invocation still
queries every ancestor and then the exact leaf. Resource sampling, sample
freshness, original clocks, call sites and stop checks are not reduced.

`NativeAttributeQuery` binds `GetFileAttributesW` on the existing System32-only
kernel32 binding. Successful observations return fresh attributes; the invalid
attributes sentinel captures that call's last-error value immediately through
ctypes' thread-local last-error mechanism. The function reports a symlink's
own attributes. See [GetFileAttributesW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileattributesw).
No filesystem result is cached; only the already accepted bounded lexical
ancestor-string tuple cache remains. Shared validation code avoids allocating
a new nested validator closure per guard call.

Every ancestor must successfully report DIRECTORY0x10 and neither DEVICE0x40
nor REPARSE_POINT0x400. Missing ancestors and every access/sharing/unknown error
refuse. Only the leaf may establish absence from invalid attributes with error2
or3, after all ancestor observations succeeded. A present leaf always refuses,
regardless of its attributes. Invalid scalar/result shapes, invalid attributes
with last-error0, other leaf errors and unknown states refuse. There is no
network/device/path alias exception or cached missing/resource decision.

The guard uses the same exact short static STOP/cache paths; the new function
does not expand accepted path grammar. Full retained input hashes, native IDs,
NTFS/type/link/reparse/final-path guards, census/absence re-enumeration and final
full verification still use the existing strict reader/engine. No reader or
shared-artifact guard is replaced with attributes alone.

Old injected-stat predicate tests remain. Three added methods cover fresh
attribute/error observations and ancestor refusal, leaf missing-only/error/
present/type cases, and a real admitted native fixture with missing then present
JSON leaf and missing ancestor. They do not claim a real access-denied or
reparse fixture when those branches use injected results. The exact proposed
roster is198, retaining195 predecessor methods and three native sharing methods.
Only the roster bound changes195->198; no runtime result is asserted here.

## Bounded original-clock localization

Six create-new retained outputs record prepare/native/final-verify start and
completion: `timing-<stage>-<state>.json`. Each records the same operation and
original UTC/QPC/frequency, current UTC/QPC/elapsed time, actual resource-sample
count and false acceptance/launch/scientific fields. No clock is restarted.
Their descriptors are carried in provisional result/return `stage_timings`.
The result can reference only timings already published; the final return also
binds later timing descriptors through the existing exact output handoff.

Final-verify start is recorded after PE and result publication. The mandatory
complete `Prepared.verify` then rehashes every original retained input, checks
native facts/IDs and the complete initial/final census. Only after it returns
is final-verify completion written. All outputs, including that new completion
record, receive final original-handle verification before accepted observer
return. A stage marker or completed provisional phase never establishes map
acceptance, complete cleanup or permission for the next stage. Missing completion
is preserved as evidence, never fabricated at closeout.

The new timing schema is `cho51_p10_stage_timing_v1`; no admission, adoption or
qualification fields are added. Root's Q qualification/test counts become198;
eight timestamps, two native faults and three sharing controls remain distinct.
The six small records remain inside unchanged8MiB/200,000-node record and
64MiB/256-output caps and the exact existing original-writer/receiver protocol.

All Q90/60/5-second512/768MiB and P300/240/5-second4096/5120MiB envelopes,
4GiB available RAM,20GiB disk, original deadlines and independent guards,
stop/sample frequency, one thread, hidden GPUs, file/hash/census/JSON/output
limits remain. No verification is skipped and no old closure is inferred.
Actual performance improvement is unmeasured; this successor may still refuse
its unchanged deadline. Q10/P10 need their own review and admission.

Authorship used source/text/file metadata and official documentation only, with
no native/API probe, Python/import/AST/compiler/test/Git execution. Historical
custody stays UNRESOLVED; old P3/P9 and Q7 limitations remain explicit. No L/V/C,
Git/loader/export/ABI/scientific authority follows;117 tests/34 controls remain
unexecuted,004 consumed,005 held,006 unadmitted, cells0/1020 and freeze unsigned.
