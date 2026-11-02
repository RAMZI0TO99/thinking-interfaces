# V7 bounded local Sysmon recovery protocol

Root owns the runner, entry and documentation; a separate implementation agent
authored the collector and tests. A different source reviewer must accept the
entire exact pinned source set. A third actor reviews actual saved outcomes.

## Fixed read scope

Only the local Microsoft-Windows-Sysmon/Operational channel and named Sysmon
provider are queried. The seed selects Event1 PID302124 or parentPID302124 in
27October2026 17:04:50Z through17:05:15Z. The old command's script and request
hash are compared as candidate hints, never treated as proof of executed bytes.
At most8 observed GUIDs receive Event1/5 followups from that start through the
capture cutoff, with at most16 records plus a sentinel per query. GUIDs require
strict UUID syntax and retain their observed spelling for XPath equality;
case-insensitive identity deduplication prevents duplicate budget use. When
only a child seed matches parentPID302124, its observed parent GUID is also
queued within the same eight-GUID cap.

Event4 service,16 configuration and255 error queries retain at most4 rows each.
Two endpoint queries retain one oldest/newest selected-family row each to
diagnose retention coverage; they are deliberately not exhaustive. Endpoint
records can contain unrelated command details and stay in local evidence only.
No raw log or unrelated command is published or printed to the user.

Every raw XML row has a byte/hash pin. The frozen v5 decoder checks selected
provider/channel/time/ID, XML structure and duplicate fields; GUID/PID link
membership is rechecked. Unsupported rows remain raw with explicit refusal.
This is candidate decoding, not native manifest qualification. Raw XML totals
are capped at384KiB, each at64KiB, with a20s cooperative capture deadline.
Every adopted native event/query handle is closed; failed closure is sticky.
Query access denial, empty results, truncation and errors remain explicit;
they never establish absence of an old process or complete descendant coverage.

## Admission, custody and resources

Each mode requires exact source/runtime hashes, independently accepted source
review, a new UUID and unused output namespace, a10-minute admission and two
startup observations. The explicit small diagnostic envelope is4GiB startup
and active available RAM,20GiB disk,512/768MiB process/Job commit,45s child,
75s work and90s whole runner,1MiB payload, one library worker and hidden GPUs.
These caps do not amend successor006 or admit the117 tests/34 controls.

The new runner retains source/runtime files and ancestor directories, rejects
reparse/hardlink/path changes, uses a fresh absent bytecode prefix and isolated
Python, and atomically assigns its suspended child to an unnamed kill-on-close
Job before resume. The local stop is runs/coordination/PROJECT_STOP.json;
presence or uncertainty refuses/stops owned work. Only the owned Job may be
terminated. EOF, reap, empty/closed Job and original handle closure must pass.
Genuine external tool results and before/after UTC/QPC bound caller return.
Failure consumes that identity. No automatic retry, elevation, configuration
changes, auditing changes, restart, process-table sweep or remote access.

This trusts the existing local Windows API/runtime for an observation. It does
not authenticate historical machine identity, prove logging completeness,
repair original004 custody or issue a positive boundary disposition. Actual
receipt pending flags remain immutable; independent review and Root adoption
are separate records. All launch/scientific authority fields remain false.

## Semantic source

[Microsoft Sysmon documentation](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon)
describes Event1 process creation/ProcessGuid correlation, Event5 termination,
Event4 service state, Event16 configuration changes and Event255 errors.
Process GUID correlation is distinct from a cryptographic host attestation.
