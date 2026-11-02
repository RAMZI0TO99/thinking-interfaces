# Review of retained L refusals

The accepted P operation is `e0014cf3-271a-472a-9070-cf9873d98e8c` under
`runs/coordination/cho51_p3_native_bootstrap_20261031_p2`. Its saved derivation
is `INCOMPLETE_REFUSED`: 36 source modules, 710,542 source bytes, 91,231 AST
nodes, 662 definitions and zero accepted import edges. No selected code was
executed and no candidate or third-party module was imported. Physical coverage
of 21,115 files is not a Python import allowlist.

The [inventory](refusal-inventory.json) rechecks the original page hashes and
source pins, accounts for every row and preserves module/phase provenance:

| Kind | Rows | Required treatment |
| --- | ---: | --- |
| call | 5,789 | Distinguish eager/deferred contexts and resolve exact callable bindings/effects; no blanket exclusion |
| branch | 1,346 | Bound both possible arms or prove a source/environment-bound exclusion; include implicit context-manager/protocol effects |
| from | 538 | Resolve literal package/member identity, parent initializers and star-export policy |
| import | 174 | Include exact target and all executable parent packages; no directory-wide grant |
| native-load | 11 | Bind requester, call site, flags, paths, PE choices and native initialization effects |
| dynamic-code | 7 | Bind exact code bytes, origin, phase and gate; a declaration does not authorize compilation/execution |
| resource | 5 | Bind retained read-only resource, exact caller, phase and byte cap |
| dynamic-import | 2 | Exact finite targets and argument form; no arbitrary expression evaluation |
| syntax | 1 | Preserve the reported failure and correct the candidate only through a versioned amendment |

Total: **7,873**. These are findings, not failed test cases or 7,873 independent
defects. The seed has **zero decisions, native rows, resource rows, ABI rows and
bootstrap modules**. Its 55 guard rows and two coarse initialization groups are
seeds, not complete observed policy. Most rows therefore record expected missing
decisions. The largest groups are torch830, phase2_runner804,
phase2_selected_source_store756, phase2_cho_execution684 and
phase2_selection_evidence_binding545. These counts are workload ordering only.

`lplan1/compiler.py` cannot become ready by mechanically inserting `include`:
it explicitly refuses active generic calls with unresolved targets. Whole-source
shadowing also makes a name unresolved even when the shadow belongs to another
scope. Conversely, a supplied `exclude` currently has no independently checked
reachability witness. Branch rows do not prune traversal; all child nodes are
still visited. Calls, imports and effects inside dormant functions are included
in the census. The successor must retain this conservative coverage while
representing lexical scope, eager definition work, deferred execution and
proof obligations explicitly. Merely counting down the refusals is unsafe.

The compiler has no complete handling for loop/comprehension iteration, truth
testing, descriptors, metaclass/decorator effects, operator protocols, star
imports or implicit exception/context-manager behavior. These must enter the
effect census or refuse; absence from the old nine categories is not permission.
New findings may increase the total. A Python dependency closure is not yet
known: approved imports expose further modules and further decisions, so 36 is
the observed seed population rather than a closure target.

## Syntax diagnosis

The original saved row names
`docs.phase2.cho51_p3_adapter_v1.test_telemetry` and `SyntaxError`, with null
line/column. It does not prove a location. Independent text inspection finds
two multiline `@pytest.mark.parametrize` decorators ending in `]):` instead of
`])`, at source lines **114 and157**. A decorator expression has no trailing
colon. The first is a plausible explanation of the recorded parse failure; the
second would remain after that correction. Neither diagnosis has been confirmed
by executing a parser in this design phase.

The source SHA256 is
`7ce9def4e6d89375970aee1d53e0ff4c9c05acdd43cafae9a6a65e71f94ecbee`, matching
the frozen roster pin. The compiler's catch at lines162–164 keeps only the
exception class, discarding its location. A compiler successor must retain a
bounded diagnostic: exception kind, sanitized message (maximum512 Unicode
characters), nullable start/end line and offset, source reference and record
identity. Offsets remain Python SyntaxError character offsets, distinct from
AST UTF-8 byte columns; preserve both conventions explicitly. No traceback,
locals or source text is published. Missing/unrepresentable location remains
null, never invented. SyntaxError, ValueError and RecursionError still refuse.

The [candidate amendment](candidate-amendment.md) handles the source/identity
change. This phase edits no candidate, compiler, host, frozen receipt or runtime.
