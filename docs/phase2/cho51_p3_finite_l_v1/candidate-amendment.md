# Proposed corrected candidate identity

The original local validation contract binds six immutable v1 files, 25 function
multiplicities and expected39 mapping/78 telemetry cases. It does not contain
collected full IDs. Both syntax defects are in frozen source. Editing it in place,
presenting a corrected copy as unchanged, or inventing old full IDs is prohibited.

The selected implementation design is a new
`docs/phase2/cho51_p3_adapter_v2/` package, with these exact allowed changes:

| File | Allowed successor delta |
| --- | --- |
| contracts.py, mapping.py, telemetry.py | Exact byte copies of v1; no production logic change |
| test_mapping.py | Only the two absolute imports of the v1 contracts/mapping package (original lines15–16) change to v2 |
| test_telemetry.py | Only the trailing colons on the two decorator closings (original lines114,157) are deleted; relative imports now resolve in v2 |
| README.md | New explicit provenance, migration scope and unexecuted-status documentation |

No v1 file or package alias is installed or overwritten. The successor's core
bytes match v1, but module identities differ; that distinction is intentional.
The v1 canonical boundary, worker bridge and other external dependencies remain
exact pinned inputs. The new plan substitutes the three v2 core preimports and
two v2 candidate modules; it must not import both generations accidentally.
The old test modules are not executable entries in the new import plan.

An implementation-specific amendment must bind a closed comparison record:
`schema, original_roster_ref, original_source_refs, successor_source_refs,
allowed_edits, function_map, control_roster_ref, independent_review, safety`.
Every Ref has exact path/bytes/SHA256. Each allowed edit has original/new source,
byte offsets and removed/inserted bytes; context must match exactly. Reject any
other byte change, automatic formatting, reordered parameter or import redirect.
The implementation derives all offsets from the pinned bytes; this design's
line labels do not substitute for that check.

`function_map` contains exactly25 rows with original module path/function prefix,
successor module path/function prefix and unchanged expected multiplicity. It
is one-to-one, totals117 and preserves39/78. No fabricated parameter IDs or
full node IDs appear in this record. The independently reviewed actual patch
must establish this mapping before Root adopts the successor for implementation.
Design acceptance alone does not adopt new executable bytes.

Future L collects exactly117 actual unique successor IDs with all25 expected
function counts, source and module origins, ordered parameter IDs and digest.
V must collect the identical successor roster under identical accepted pins;
zero skips/errors/xfails/xpasses/deselections and351 successful phase reports
remain required. Report these as validation of the explicitly mapped successor,
never execution of the unchanged original v1 cases. The 34 successor-control
names, meanings and exact roster bytes remain unchanged; changing a control
implementation requires its own reviewed new source and qualification.

The original117 cases remain unexecuted. The corrected117 expectations also
remain unexecuted until independently accepted L/V evidence exists. No candidate
parser, module import, collection or test was run for this design.
