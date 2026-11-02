# Documentary record contract

Status: PROVISIONAL_BLOCKED. G2 complete: false. Launch authority: false.

## Identity and coverage

This documentary schema is deliberately distinct from the executable decision
schema in the accepted finite-plan contract. It cannot be consumed as an L plan.
The authoritative input is the accepted P4 inventory index, its 53 exact page
refs and five source pins. Each accounting row names one existing node ID,
kind, conservative inventory epoch, phase and reason rule. It also carries
the nearest source span (its own, or an identified ancestor for structural
nodes), a bounded display excerpt and any explicit manual annotation IDs.
A display excerpt can be truncated; its full raw-span hash and original
inventory coordinates are authoritative. No prefix is presented as full source.

Rules are a finite documentation taxonomy. They expand only into the exact
listed rows; they confer no wildcard permission. All effect/binding/control/
definition rows have disposition `refuse`. Structural rows have a null
disposition and delegate semantics to their enclosing node; this is not
`exclude_proven`. Literal rows also retain refusal of contextual use: a
literal's existence does not prove its consumer safe. No `allow_bound_call`,
`defer_guarded`, `include_import` or `mediate_effect` is approved.

The builder reads saved JSON, source bytes and text only. It does not parse
Python. It verifies page and source hashes, unique IDs, parent/scope membership,
all non-null UTF-8 span hashes and exact row coverage. It refuses unknown kinds
instead of assigning a default safe category. Definition headers and literal
import proposals are documentary text observations, not lexical proofs.
Shape hashes and scope labels cannot recover missing binding/effect fields.

## Manual observations and frontier

Every one of the 46 import sites has a manually supplied source-line join,
literal module proposal, imported member spellings, relative level and explicit
unresolved origin/export/parent/initialization obligations. A from-import member
may be an attribute or submodule: that choice is not silently resolved by its
spelling. Known project file refs are intended-source observations only.
Ordered runtime roots, namespaces, builtins/frozen modules, tagged extensions,
conditional imports and rebinding all need the future resolver and fresh P.

All 79 class/function definitions are enumerated, including nested definitions,
with exact node identities, headers and header-child roles. An apparent
deferred body is not excluded: alias/callback/descriptor entry controls remain
unimplemented. Decorators/defaults/bases/class bodies remain review obligations.
Four modules declare future annotations; test_telemetry does not. The package
does not upgrade the inventory's unknown annotation epochs to verified runtime
semantics.

Manual findings overlap deliberately. They annotate precisely listed affected
IDs and pin full sources plus line spans; they neither replace accounting rows
nor assert all other sites are safe. First-hop dependency findings are bounded
text observations without invented inventory IDs. Historical seed rows retain
their original source refs and refusal counts, with five v1-to-v2 prospective
mappings backed by the accepted migration. No old finding is marked resolved.
The frontier is finite *as recorded*, but not transitively complete.

## Review, serialization and invalidation

Root authors; an independent source reviewer judges semantic scope and a
different result reviewer checks the saved artifacts and identity accounting.
Review records have new filenames for each revision; never overwrite findings.
Each JSON file uses UTF-8 without BOM, stable ordered fields and LF termination.
Hashes bind exact saved bytes; this documentary serializer is not adoption of
an executable plan's canonical-JSON contract. Unknown fields or versions require
a successor review before any future consumer is implemented.

Inputs, outputs and page counts are indexed. At most 256 rows/page and 8 MiB/page
are used; this package has a 128-file/16 MiB authoring bound. These are lower
document bounds, not a new P admission. Future P must account for all physical,
inventory, decision and native outputs under its original 256-file/64 MiB
aggregate limits. Current counts cannot reserve capacity or certify future fit.

Any candidate/source/inventory change invalidates its rows and dependent manual
observations. Changed runtime, roots, exports, environment, capabilities or
plugin configuration invalidate prospective bindings and effects. Current P
acceptance covers release-time bytes only. No current census or physical custody
is inferred from ordinary hash inspection. Final transitive fixed point, exact
implemented/qualified capability joins, current Q/P and independent G4 acceptance
are required before separate L admission.
