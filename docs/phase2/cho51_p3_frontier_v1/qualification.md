# Planned nonnumerical qualification

These are unexecuted design scenarios. Implementation maps every scenario to
named methods and explicitly records splits/merges. They supplement all424
inherited/resolver methods and mandatory controls; they do not replace the117
candidate cases,34 V controls,26 local qualification scenarios or remaining L
qualification obligations.

| ID | Required observable assertion |
|---|---|
| FC01 | Closed top-level and nested schemas reject unknown/missing fields |
| FC02 | Exact types reject bool-as-int, floats, invalid identifiers/hashes |
| FC03 | Duplicate/case-colliding modules, seeds, IDs and edges refuse |
| FC04 | Content-derived IDs and all references are recomputed and checked |
| FC05 | Expected source/runtime/spec/root/predecessor binding drift refuses |
| FC06 | Seed package prefixes retain the original requester and phase |
| FC07 | Late L4 context through previously seen L2 module reaches descendants |
| FC08 | Same-phase distinct seeds retain distinct requester facts |
| FC09 | Diamond retains both incoming provenance links without duplicate fact |
| FC10 | Cycles terminate without path expansion; late context crosses cycle |
| FC11 | Deferred/conditional edges propagate may-reach with flags unchanged |
| FC12 | Missing origin stays explicitly blocked and prevents saturation |
| FC13 | Dynamic/native/export/binding/effect obligations never disappear |
| FC14 | Empty worklist cannot set G2/capability/launch acceptance |
| FC15 | One-step continuation equals a single bounded run on a finite graph |
| FC16 | Every commit boundary conserves all input obligation payloads/IDs |
| FC17 | Over-cap atomic transition leaves input snapshot and cursor unchanged |
| FC18 | Rows include source/origin/seed/edge/debt/fact/link/work/history |
| FC19 | Modules/source bytes/module bytes/nodes/depth caps cannot reset |
| FC20 | Edges/pages/output bytes/per-file limits refuse at exact boundaries |
| FC21 | Snapshot count and cumulative byte caps refuse infinite chains |
| FC22 | Invalid cursor, skipped edge, fabricated done fact or link refuses |
| FC23 | Missing/extra pending fact and reordered/noncanonical work refuse |
| FC24 | Predecessor mismatch, sequence regression and changed immutable graph refuse |
| FC25 | Stop/checkpoint refusal at every transition commits nothing |
| FC26 | Deterministic canonical bytes, digests and repeated pure evaluation |
| FC27 | No file/network/import/parse/exec surface in the supplied-state kernel |
| FC28 | No mutation/aliasing of caller input, including nested payloads |
| FC29 | Full input/output history accounting; reference-only debt refused |
| FC30 | Oversized single module/edge fanout yields explicit finite refusal |
| FC31 | Zero-edge modules complete exactly once; missing modules never do |
| FC32 | False capability flags/status cannot be injected into a snapshot |

Later producer/P-specific scenarios (not claims of the first kernel Q):

| ID | Required evidence before producer acceptance |
|---|---|
| FP01 | All74 predecessor pages,18,793 rows, embedded binding/effects joined |
| FP02 | Deleted/duplicated/reordered page or row, pin/span mismatch refuses |
| FP03 | All36 seeds and source-prefix contexts reconstructed; loss detected |
| FP04 | Complete old-to-new obligations join; no sampling/digest substitution |
| FP05 | Fresh retained source/runtime/census identity; drift cannot resume |
| FP06 | Scoped AST allowance removed on every exit; no input execution |
| FP07 | Shared P budgets include snapshots/index/descriptors/history |
| FP08 | Partial writer/index/stop failure cannot publish accepted checkpoint |
| FP09 | Cross-round exports/member candidates conserved with explicit unknowns |
| FP10 | Original handles reverified, owned cleanup and exact caller return |
| FP11 | Graph saturation does not approve unresolved effects or Lhost |
| FP12 | Over-cap real reconstruction reports full refusal without omission |
