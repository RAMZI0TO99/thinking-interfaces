# Source findings and provisional decisions

The five accepted sources contain 13,406 AST occurrences: contracts 2,199,
mapping 1,874, telemetry 2,915, test_mapping 3,217 and test_telemetry 3,201.
There are 46 import sites, 736 explicit calls, 74 function definitions and five
class definitions. These are syntax counts, not reachable-effect counts.

## Eager initialization is still blocked

Contracts builds PLAN, LEDGER and AUTHORITY using MappingProxyType and dict
at lines 36–38. The values have finite literal inputs in this source, but
the exact imported/builtin callable identities, rebinding analysis and effect
certificates have not been established. These are plausible finite certificates
for the successor; they are not approved calls here.

Four dataclass decorator calls occur in contracts (203, 247) and telemetry
(143, 162). Constructor generation, slots, frozen assignment behavior,
descriptor creation and annotation handling need exact pinned dataclasses
semantics. Property decorators also run during class creation; property bodies
remain later entry points. Class and function creation cannot be replaced by a
blanket dormant-body exclusion. The nested CallbackProbe class in test_mapping
is created only if its enclosing test runs, but it still needs an entry barrier.

test_mapping line 25 constructs and resolves a Path from __file__, then
indexes parents. This is an eager path/metadata effect and requires an exact
filename, resolver semantics and read capability. It is not harmless string
construction. The fixture decorator at line 62 and 15 parametrization decorators
across the two test modules run at import time. Their arguments appear finite,
but pytest mark/fixture registration and descriptor/hook behavior remain pending.
No pytest code was imported to discover its behavior.

## Deferred bodies are not proven exclusions

mapping.assess_adapter_intent calls the canonical boundary before its own reads,
then defines a nested metadata reader and imports four canonical modules
inside the function. The nested reader has nominal limits of 12 files/16 MiB;
this does not establish an L resource grant or physical identity. Its aliases,
closures and callbacks need exact binding analysis and a qualified entry guard.

test_mapping's fixture can create directories, write metadata, read pinned
configuration/origin files, build catalog/route values, capture source identity
and call environment_digest. In core.provenance, capture_source can scan source
and launch bounded Git subprocesses. The worker bridge's _context reads the
pinned route planner, creates a module, mutates sys.modules and uses compile/exec.
These are deferred source paths; they are not observed executions. L must block
fixture/test/helper entries and their aliases before collection can reach them.
Future V requires its own finite file/process/dynamic-code admission.

The tests include temporary metadata mutation with finally restoration,
monkeypatch callbacks and custom __getattribute__/__eq__ methods. A successful
negative assertion in source is no proof that these callbacks are unreachable
during collection. Exception construction, context-manager entry/exit, attribute
lookup, comparison, iteration, comprehension and truth evaluation remain
explicit implicit-effect obligations.

Contracts has nested graph visitors and json pairs/constant callbacks.
Telemetry accepts supplied trace data; its functions perform sorting, interval
and validation operations if called. This step records those call/implicit
protocol sites without running them or qualifying numerical behavior.

## Transitive boundary and host work

Direct imports from test_mapping reach profile binding and the phase2 runner,
which import NumPy and PyTorch. The canonical boundary and protocol add eager
dataclass creation. Current physical P coverage does not certify initialization,
native ABI, resource effects or safe package order. The complete dependency
graph, executable parents, namespace/builtin/frozen/extension choices and SCCs
remain absent. No topological execution order can be derived from 46 local
import sites or the older zero-edge seed inventory.

The package retains all 36 original seeds (14 dependency and 22 project entries,
including two test modules) and all 7,873 historical refusal findings by reference.
Only five candidate identities are prospectively mapped to v2; there is no
one-to-one resolution claim between old findings and new occurrences.

Pending capability rows cover exact binding/effect resolution, entry barriers,
native requester/image joins, native resource mediation, finite ABI queries,
55 canonical blockers plus discovered equivalents, safetensors' four API guards,
28 pytest builtin registrations and Config/session instances, retained streaming,
L bootstrap/lifecycle, final census and output closure. An additional explicit
adapter obligation handles the current P4 root schema
cho51_candidate_inventory_p_root_qualification_v1: the older LP4-only host design
cannot silently accept it.

## Outcome

The accounting package can be reviewed as a finite, auditable record of why
execution remains refused. It does not satisfy G2's transitive closure requirement.
The next implementation must enrich the inventory with lexical definitions/uses,
explicit import target/export resolution and finite effect summaries, then iterate
to a bounded fixed point under reviewed file-only P. It must stop on unsupported
constructs or cap exhaustion and preserve useful refusals. New modules can add
obligations; they cannot inherit approval from package names or physical presence.
