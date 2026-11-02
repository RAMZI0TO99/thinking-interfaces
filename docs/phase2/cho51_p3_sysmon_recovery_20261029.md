# Local execution-log recovery

29 October 2026, Asia/Riyadh. Work began on28October; the v7 directory retains
that initial date. Engineering observation only.

The owner confirms that the failed27October bootstrap004 ran on this PC and
asked Root to locate the logs or establish a safe recovery path. Root found
the local Codex execution transcript and an existing Sysmon operational log.
The task-specific transcript extract records the original Invoke command,
request/admission hashes and failure. The application keeps the source file
open; its whole-file hash was unavailable due to a sharing conflict. The
selected original line is retained and hashed separately. Its application
process_id is not assumed to be a Windows PID, and it is not host authentication.

## Executed result

A new [v7 collector](../../tools/custody_boundary/v7/README.md) received independent
source review. Sixteen injected tests passed under a fresh bounded admission.
A separate admitted native read attempted six narrowly scoped Sysmon queries.
Every query returned **Windows error5, access denied** before opening a handle.
There were zero rows, zero exhausted queries and zero native handles opened.
This is an access failure, not evidence that the old process records are absent.

| Operation | Attempt | Actual tool result |
| --- | --- | --- |
|16 tests |af42f8c4-c3dc-4d94-9c3b-2de01e35b2fb |35f878, exit0,5.7478181s |
|Focused Sysmon read |2e75e998-5e5d-4418-8185-f897d936f7f5 |de2e5a, exit0,4.453514s |

The runner's zero exit accepts the bounded observation and its owned cleanup;
it does not mean the protected log was read successfully. Both owned Jobs
closed empty, root exits and original process/thread handle closure were
verified, and external caller-return records were retained. No elevation,
logging changes, restart, process kill outside the owned Job or old replay occurred.

The distinct [actual reviewer](../../runs/coordination/cho51_p3_sysmon_recovery_20261028_v7/actual-review.json)
accepted these observations with gaps. Root rechecked14 source inputs,732
runtime files and538 preserved predecessors and recorded
[qualification](../../runs/coordination/cho51_p3_sysmon_recovery_20261028_v7/root-qualification.json).
The source review, result review and Root adoption remain separate records.

## Consequence

Historical host association and cleanup remain unestablished. The existing
UNRESOLVED disposition stays unchanged;004 remains consumed and005 remains held.
Protected Sysmon content cannot be recovered under the current access token.
No positive restart or complete descendant claim follows from this capture.

The next engineering option is a separately reviewed, narrower present-byte
inventory contract with retained input/output identities and fresh containment.
It must not be presented as old-process extinction or as permission to run117
candidate tests/34 controls. Scientific cells remain0/1020; final freeze unsigned.
