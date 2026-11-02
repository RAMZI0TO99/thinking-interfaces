# Finite plan materialization contract

This is the design of a closed plan and its reviewer workflow, not a materialized
execution plan. Implement a versioned `lplan2` compiler and matching `l2` policy
consumer; keep lplan1/l1 frozen. Review architecture and exact implementation
before any admitted parser or Q/P work. Never promote the 21,115-file physical
superset or the 36 seed modules into a module allowlist.

## Record and decision model

Use closed, typed records, canonical JSON and SHA256, exact integer/Boolean
distinction, no duplicate keys or case aliases, bounded strings and paths. All
records have a schema version and status; unknown fields/versions refuse. All
evidence leaves name exact path/bytes/hash and role. Native identity is required
on typed retained physical descriptors; content-only authority refs join to
independently accepted descriptors as specified by the host adapter. A source
design has no invented native identity. Refer to paged immutable inputs instead of recursive
authority discovery. No record contains executable expressions or callback names
to resolve through globals/imports.

| Record | Required semantic fields in addition to schema/status |
| --- | --- |
| Plan input | exact candidate amendment/roster, source/runtime manifests, P map and recipe, ordered roots/environment, seed modules, bootstrap plan, limits and all policy-page refs |
| Node inventory | module/source Ref, lexical scope ID and parent, node kind, start/end UTF-8 byte coordinates, raw-span hash, AST-shape hash, context/evaluation epoch, binding uses/definitions, implicit effects and branch dependencies |
| Decision | node identity, disposition, phase/group, exact targets/effect IDs, binding proof or exclusion witness, dependency decision IDs, reviewer/rationale and source/environment applicability |
| Binding proof | lexical scope, exact defining source/span or trusted builtin identity, receiver/attribute resolution, alias/rebinding history, argument shape and typed effect summary; unresolved possibilities are explicit refusals |
| Exclusion witness | node/scope, applicable phases, controlling decision IDs, immutable environment facts or blocked entry capability, no-eager-effect evidence and invalidation dependencies |
| Effect certificate | exact callable/code Ref or native image/symbol, allowed phase/group/call sites, finite argument domains, reads/writes/imports/native choices/callbacks/return types/exception effects, preconditions and observable postconditions |
| Group | ordinal, phase, group ID, exact modules, predecessor groups, constructor epoch, effect IDs, installed guard epoch and postconditions |
| Materialized plan | ordered groups, complete import/native/resource/ABI/guard/plugin/bootstrap policies, candidate/config bindings, all dependency-page digests and exact implementation/runtime compatibility |
| Derivation index | input/decision/plan refs, sorted page refs and row totals, unresolved/stale/unbound counts, modules/edges/source-byte/AST/definition totals, duplicate/conflict checks and zero candidate/third-party imports or code execution |

Disposition is one of `include_import`, `mediate_effect`, `allow_bound_call`,
`exclude_proven`, `defer_guarded` or `refuse`. Empty targets/effects are legal
only when the disposition's grammar permits them. `allow_bound_call` requires
one resolved callable and a reviewed finite effect certificate; it is not the
old generic `include`. Effect-free builtins still need exact identity, operand
types and a proof that operator/descriptor/iteration callbacks cannot escape.
User-defined/native summaries must account for their reachable effects; merely
naming a function or reviewer is not a proof.

Lexical binding analysis distinguishes module/class/function/lambda/comprehension
scopes, closure cells, global/nonlocal declarations, import aliases, assignments,
deletes, exception/pattern targets and conditional rebindings. Unknown descriptors,
getattr, containers, monkeypatching, aliases, callbacks or dynamic dispatch refuse
unless reduced to exact reviewed identities and finite domains. Conservative
analysis may refuse supported Python; it must not infer safety for arbitrary
Python. The implementation accepts only its qualified subset and publishes every
unsupported construct as a refusal.

Definition bodies may be deferred, but decorators, defaults, annotations when
evaluated, bases, metaclasses and class bodies are eager. Account for both the
retained interpreter's annotation semantics and future-import flags. Loops,
comprehensions, operators, truth tests, with/async-with, exception handling,
generators/coroutines and callback registration contribute implicit effects.
An exclusion cannot hide eager work. `defer_guarded` identifies entry capabilities
blocked throughout L, including aliases, generators and registered callbacks;
the corresponding V work is separate. If an exclusion/deferral cannot be proved
and enforced under the current source/environment, the plan stays incomplete.

## Closed construction and review

1. Bind current pins and inspect syntax with the reviewed non-executing parser
   under fresh admission. Retain useful bounded diagnostics. Syntax failures
   do not create empty successful modules or suppress downstream obligations.
2. Generate inventories, never approvals. Reviewer decisions reference exact
   inventory nodes and hashes. Reusable review rules may expand only to a
   finite listed set of exact node IDs; no regex/package-directory grants,
   default exclusions or “all calls in tests are dormant” rules are executable.
3. Resolve literal imports, from-imports, executable parent packages, namespaces,
   builtin/frozen identities and exact tagged extension paths. Star imports
   require an exact statically established export/member mapping and binding
   effects; dynamic `__all__` or unresolved export behavior refuses. Dynamic
   imports require reviewed finite literal targets/argument shapes.
4. Iterate transitively over every included module until a fixed point. Each
   new module adds syntax, decisions, bindings, phases and effects. Derive and
   review strongly connected groups; a cycle does not grant arbitrary order.
   Previously initialized modules retain exact identity and completed phase.
   Pending imports must belong to the active group's exact closure.
5. Join every effect to an implemented capability and every native/resource/
   guard/ABI/plugin row to exact P-covered inputs. Reject dangling, conflicting,
   duplicated, unused or stale decisions and missing prerequisite/postcondition
   IDs. Regenerate invalidated transitive decisions after any relevant change.
6. Publish bounded inventory, decisions, binding, edges and refusal pages plus
   a content-addressed index. Failure or cap exhaustion remains refusal, never
   a truncated accepted page set. Reviewer validates independent completeness
   and semantics, not merely counts or a compiler's green flag.

Keep the existing bounds:25,000 modules,200,000 edges,4GiB source bytes,
2,000,000 aggregate AST nodes, depth128; input25,000 files/4GiB/2GiB per file,
path depth32,64KiB streaming chunks. New decision/inventory/effect rows share
the2,000,000-node aggregate ceiling, with at most256 rows/page and8MiB/page.
The entire operation still fits the caller's256-output-file/64MiB output caps;
that includes physical and native pages. A full closure may exceed this budget:
stop and separately redesign the bounded artifact plan, never discard rows,
increase caps automatically or claim completeness of a prefix.

## Initialization and effects

Keep L0–L6 and sticky failure. L0 reacquires complete accepted Q/P/source/runtime/
plan authority, fresh physical/census/absence identities and resources. L1 owns
the child, installs native observation and gates before any non-bootstrap code.
The bootstrap list is an exact version/role-pinned module set and initial native
image trust set, qualified with the actual isolated bootstrap under fresh Q.
Do not manufacture a live module list by importing installed packages to discover
what they do. An unexpected bootstrap member requires a reviewed successor.

L2 dependency groups are derived from closure and reviewed in prerequisite order:
pytest/pluggy/configuration, NumPy/SciPy and supporting runtime, PyTorch and
safetensors, then MNE/sklearn/braindecode/torchaudio as the actual dependency graph
requires. These are review work packages, not a fixed unsafe order or grants.
Cycles merge only with explicit order/guard proofs. No package name implies all
its modules are allowed. The initial 14 dependency seeds and 20 canonical seeds
remain inputs to review; reduction requires explicit rationale and closure proof.

Install package API guards immediately when their defining symbols become
available, before canonical aliases are captured. Safetensors' four data APIs
must be blocked before canonical imports. Constructor permissions are exact L2
group/call-site effect certificates with finite parameters and are closed before
L3 completion; they never permit project model construction, weights or EEG.
Library initialization may perform internal arithmetic; do not promise zero
numerical instructions. L3 canonical groups install and verify the full55-seed
blocker/alias obligations plus newly discovered equivalents. Guard discovery
must not invoke properties/descriptors. Unknown/missing symbols or early aliases
refuse. Every required postcondition and sentinel is implemented and bound.

Native rows bind requester and call-site context, mechanism, flags, ordered exact
directories, chosen retained image or explicit platform trust role, transitive
PE edges, delay policy and native initialization effects. Shared images may have
multiple importer edges but one retained identity. The observer joins a path to
the complete set of declared importer obligations; it must not assume one image
has one requester, accept an arbitrary first match, or infer requester from a
DLL-notification payload that does not report it. Pre-effect gates retain exact
requester choices; baseline/platform loads have their own reviewed roles.
Unused delay paths remain unqualified. Hidden GPUs do not prove that native
initializers avoid GPU/device work. Any required GPU initialization, unsafe
native resource branch or unbounded behavior refuses this engineering scope.

Resources bind exact retained files, caller source/span, phase, read-only mode,
maximum bytes and required/optional observation. Package metadata, MNE fiducial
data and configuration are finite inputs, not EEG/weight permission. The initial
write policy is deny-all except existing owned observer outputs. If a package
needs cache/config writes, stop for a separately reviewed finite capability and
qualification; do not clear shared caches or silently exempt a directory.
Native-origin resource reads need an implemented reviewed mediator or an explicit
fixed platform trust contract. Python wrappers alone do not prove their coverage.

Every extension has exact machine/tag/PyInit/export/forwarder requirements,
metadata and finite safe zero-argument noncomputational queries. A physical PE
edge or successful load is not numerical ABI compatibility. Optional unexercised
exports, GPU and numerical kernels remain unqualified.

L4 binds the exact pinned pytest version, config, argument vector and explicit
module/instance plugin identity map. Preserve collect-only/importlib/no-conftest/
plain-assertion, disabled plugin autoload/cacheprovider/stepwise and empty ambient
addopts. Validate all inherited28 builtin registrations against the pinned version,
including exact wrapper hooks and runtime Config/session instances. No ambient
plugin, fixture, test phase, skip, deselection or silently caught denial may pass.
The corrected candidate amendment supplies exact source origins and expected25
function counts; actual117 IDs are produced only by admitted L.

L5 rechecks all original inputs, complete census/absences, code/native/resource/
guard/plugin identity, counters and output descriptors before release. L6 proves
owned Job/process/pipe/observer/guard cleanup and genuine caller return before
independent actual acceptance. Audit hooks/wrappers remain defense in depth under
the project's existing trust model, not a sandbox against hostile native code.

## Readiness gate

Only a current, fully pinned derivation with zero syntax, unsupported, unresolved,
stale, unbound or conflicting obligations and a complete page/count digest may
be `COMPLETE_REQUIRES_INDEPENDENT_REVIEW`. “Reviewed design” and “reviewed
decisions” are not that status. Independent semantic review, Root complete-plan
acceptance, exact current Q/P and a fresh L-only admission are all still required.
This package's 7,873 existing findings remain unresolved for execution.
