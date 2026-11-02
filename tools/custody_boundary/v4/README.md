# Focused provider observation and strict decoder v4

Engineering-only successor to the [retained reader](../v3/README.md) and
[raw diagnostic](../v1/README.md). Run only under [PROTOCOL.md](PROTOCOL.md).
Source, test results, observed local metadata and authenticated historical
custody are separate claims. This package never grants positive boundary or
launch authority.

The prior32-row raw capture contained only Kernel-General IDs15,16,24. It
therefore supplies no observed boot record. The new fixed plan partitions seven
queries: Kernel-Boot27; Kernel-General1/12/13; Kernel-Power41/42/107;
Power-Troubleshooter1; EventLog6005/6006/6008; Microsoft-Windows-Eventlog104;
and Security-Auditing4688 restricted to the saved PID302124 and old caller window.
These IDs select candidate diagnostic families; no ID or BootType value is
mapped to an accepted full-restart predicate.

Each System query spans the old return bound through the new capture's fixed
start UTC. The Security query spans the saved old external-entry/return bounds
and three explicit hexadecimal PID spellings. Its exhaustion does not cover
other spellings, clock offsets, missing/disabled audit records or overwritten
logs. Permission denial remains visible; this code neither elevates privileges
nor enables auditing. Raw local records may include computer labels and process
fields; they stay in the local attempt and are not printed by the runner.

`collector.py` uses local Windows Event Log handles to retain raw XML and current
registered publisher GUIDs/event definitions. Metadata and event enumeration
have independent exhaustion/truncation/error fields. System families each have
16 rows plus a sentinel; the historical query has4 plus a sentinel. Limits are
64KiB per XML,384KiB total events,192KiB templates,64 selected definitions per
publisher and2048 enumerated definitions per publisher. A20-second work check
and supervised45-second child deadline bound blocking native calls. Every
acquired handle is adopted before a later fallible operation and closure is
counted. A close failure prevents accepted collection.

`decoder.py` verifies raw byte/hash pins, bounded XML, exact selected provider/
channel/event ID/time/PID joins and unambiguous scalar fields. Supported flat
local templates must match provider GUID, event ID, version, ordered field names
and scalar types. Unknown forms remain explicitly unsupported. A match means
the event representation fits that observed local template; it does not prove
event truth, historical host identity, restart semantics or an unchanged OS.
Times retain up to9 fractional digits as integer nanoseconds. QPC counters are
used only within the new capture, never compared across boots.

Native variants are type-checked and pointers are checked against the returned
buffer before reading. The parent pins source/runtime files and retains their
handles. This phase does not change the frozen v1–v3 sources or old receipts.

The original004 record lacks a contemporaneous machine/boot identity. Even an
exact PID/time/name candidate in the current Security log would still require
independently supported historical host association. Copied workspace paths,
current computer labels and a valid schema cannot supply it. The original48
design cases and117 candidate tests/34controls are separate from this package.
Scientific cells remain0/1020 and the final freeze remains unsigned.

## Provider documentation

Microsoft's [provider metadata documentation](https://learn.microsoft.com/en-us/windows/win32/wes/getting-a-provider-s-metadata-)
describes local registered metadata and event definitions. The
[event metadata properties](https://learn.microsoft.com/en-us/windows/win32/api/winevt/ne-winevt-evt_event_metadata_property_id)
include numeric ID/version and XML template data; this API does not certify the
historical truth of an event. The [variant layout](https://learn.microsoft.com/en-us/windows/win32/api/winevt/ns-winevt-evt_variant)
specifies scalar/array types and pointers. Enumeration handles require
[EvtClose](https://learn.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtnexteventmetadata).
The [4688 documentation](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4688)
describes process IDs, images and optional command lines; audit coverage cannot
be inferred from an empty selected query. These documents support extraction
mechanics, not a qualified restart/clock/persistence predicate.
