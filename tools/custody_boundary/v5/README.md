# Saved provider evidence decoder v5

Engineering-only successor to [v4](../v4/README.md), admitted only under
[PROTOCOL.md](PROTOCOL.md). V4 passed57 synthetic/injected methods but its actual
six event rows exposed a namespace defect: Event XML uses the /events/event
namespace; provider templates use /events. The v4 sources and actual failure
remain immutable. This package separates these namespaces and independently
tests the observed structures.

V5 has two fixed modes: tests and redecode. The latter reinterprets one
exact53785-byte saved v4 payload, SHA256
7df7f2a813f32588a08cfaa3c1100e905d935f283c28292e9bad62e9371ab906.
It is a new offline operation with a new admission and UUID. It does not query
Windows logs again, replay004/005, or create new historical evidence. The copied
collector is used only by injected controls in this runner; no collection mode
is admitted here. Original raw bytes, template pins, query gaps and capture
provenance stay unchanged.

The generic qualify_event path requires properly bound template QNames.
The separate qualify_native_event path handles the observed native API fragment
format with an explicit built-in type vocabulary and compatible scalar rendering
pairs. Missing native win/xs declarations are interpreted under this declared
format; explicit conflicting bindings, unknown types, arrays and structures
refuse. This is not a repair of generic XML or a claim that its namespaces were
present. Only the pinned capture's retained EventMetadataEventTemplate values
are passed to that path by redecode. Result status distinguishes
MATCHED_NATIVE_TEMPLATE_FRAGMENT from generic template matches. String values
are already rendered text; original ANSI byte recovery is not claimed.

The fixed saved input contains four named-field records and two unsupported
classic Binary payloads. Expected decoding success is four supported rows;
unsupported rows and Security-log access denial stay explicit. The native
capture's1,315 handle closures belong to v4; v5 has separately supervised
process/Job/input-handle custody. Decoding does not observe a new restart or
establish historical host identity, clock ordering, persisted-domain exclusion
or old cleanup. All such authority flags remain false.

Microsoft documents the [event schema](https://learn.microsoft.com/en-us/windows/desktop/WES/eventschema-schema),
[template metadata property](https://learn.microsoft.com/en-us/windows/win32/api/winevt/ne-winevt-evt_event_metadata_property_id),
[manifest namespace declarations](https://learn.microsoft.com/en-us/windows/win32/wes/defining-events)
and [input/output scalar pairs](https://learn.microsoft.com/en-us/windows/desktop/WES/eventmanifestschema-inputtype-complextype).
The omitted declarations are an observation of this retained local API output,
not a universal guarantee about all Windows versions. Unsupported representations
fail closed. These sources describe data formats, not historical authentication.

Bootstrap004 stays failed/unreleased/consumed, diagnostics005 stays held,
successor006 is not admitted, the117 candidate tests/34controls stay unexecuted,
and scientific cells remain0/1020 with the final freeze unsigned.
