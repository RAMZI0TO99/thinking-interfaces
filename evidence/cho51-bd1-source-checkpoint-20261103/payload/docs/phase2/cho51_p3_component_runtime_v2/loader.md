# Retained loader and exact collector contract

## Fixed identity and phase separation

Keep all 732 CM1 identities, 30 test modules and the exact 216 selection. There is
no namespace renaming, helper-module duplication or prefix exclusion. The
72-module project skeleton and 14 parents are only the starting graph: bootstrap,
stdlib, extensions, frozen/builtin modules, their native images and deferred
project edges must be joined before any runtime admission. Preserve the
unselected lhost1.test_authority -> lhost1.supervisor -> lp1 obligation.

A future immutable manifest has closed rows for name, kind, source pin or exact
builtin/frozen/native identity, parent, package kind/path tuple, permitted phase,
initializer/code witness and dependency row IDs. No search directory or wildcard
authorizes extra imports. Its aggregate serialization must fit the original
4 MiB retained-input slot; proposed parser ceilings are 4,096 module rows and
256 direct dependency references per row. These ceilings are conservative parser
limits, not a claim that the uncompleted runtime graph fits. Every row needs
exact source/native custody and a complete typed dependency disposition.

Phases are ORIGINAL_GUARD_READY, RETAINED_BOOTSTRAP, SOURCE_LOAD, OBJECT_CHECK,
FULL_COLLECTION, SELECTED_EXECUTION, SUITE_CLOSEOUT, FINAL_VERIFY, OWNED_CLOSED.
Bootstrap starts inside the original clock and containment. No Python, compile,
import, test construction or discovery is moved outside admission to populate
this manifest. Bootstrap modules are reconciled by original native loaded-code
witnesses, not by checking present file hashes after import.

## Loader requirements

The proposed importer is new code. LQ19's ModuleType/exec helper lacks complete
spec, loader, package and parent bindings. L1's retained finder is useful source
precedent but its sticky wrapper formats str(error), and its old policy is not
adopted. Do not patch or invoke either frozen path.

1. Retain original handles/bytes under the independent native owner; bind
   volume/file identity, ancestry, sharing/links/reparse facts and exact hash.
   Recheck before compilation, after execution and at final verification. No
   ordinary-read fallback, pyc/cache write, implicit namespace search or reload.
2. Admit source, source-package, explicit namespace, frozen, builtin or extension
   only by its exact row and phase. Execute retained package initializers once;
   empty closed namespaces have explicit specs and no filesystem fallback.
   Extensions require separate before/after native loaded-image proof; their
   create/exec phases are effects, never supplied-data simulation.
3. Construct exact ModuleType/spec/loader objects using retained bootstrap
   primitives. Record sys.modules identity, __spec__, origin, __file__, __package__,
   __path__, loader identity and the exact parent's child dictionary binding.
   Cycles may use only manifest-declared INITIALIZING edges owned by the same
   bounded import operation. Unknown cycles, substitutions or reentry refuse.
4. Install only the reviewed finder and explicitly approved frozen/builtin
   routes; pin sys.path, path_hooks, importer cache, meta_path and bootstrap
   modules. Reconcile exact dictionaries and object identities at boundaries.
   Do not call user getattr, descriptors or repr to inspect these bindings.
5. Compile only retained bytes with pinned interpreter/compiler flags, origin
   filename and optimize/dont_inherit settings. Build code-object witnesses from
   the returned graph with pre-append limits (proposed 65,536 nodes, depth128),
   source/hash joins and exact identities. These limits do not certify compiler
   allocation or timing; those remain original-guard obligations. No arbitrary
   code object or self-reported filename counts as retained-source provenance.
6. Refusal is sticky and uses bounded primitive codes. Partial imports remain
   charged and in the final census; do not repair sys.modules and continue as
   successful, silently retry, or format the exception for diagnostics.

## Object checks before standard loader calls

The pinned reference TestLoader calls dir/getattr on every module and class,
including imported classes, and constructs instances before calling load_tests.
Thus checking reported ID strings afterward is too late.

Require exact ModuleType and approved ordinary type metaclasses; inspect native
dictionaries/mapping proxies with prebound primitives. Reject module __getattr__,
__dir__, load_tests, class aliases, custom descriptors, custom constructors/run/
id/__call__/attribute interception, unreviewed inherited methods and dynamic
loader behavior before any loader call. Bind every allowed TestCase subclass,
its bases, method function/descriptor/code object, defaults/closure policy,
module/qualname/origin and skip/xfail flags against exact source witnesses.
Imported helper classes must either be non-TestCase objects or exact reviewed
aliases whose discovery effect is explicitly absent; no automatic alias waiver.

The text scan found all declared test classes directly inherit unittest.TestCase
and no targeted custom TestCase lifecycle/identity hooks. That is an observation
to verify at runtime, not a dynamic absence certificate. Standard TestCase
construction itself accesses methods and docstrings and must be reviewed/pinned.

Only then use the exact loadTestsFromModule implementation with fixed prefix,
ordering, pattern=None, standard suite class and no loader errors/_FailedTest.
Never use discover, loadTestsFromName, callable factories or directory search.
Traverse exact approved suite/instance structures with pre-append limits of
4,096 nodes and depth32, and count all 732 instances. A larger actual shape
requires a reviewed successor, never silent relaxation. Do not call custom
id()/str() for identity.
Compare object-derived rows with the full CM1 report; verify all 732/30 before
deriving the unchanged 700/28 projection or choosing 216.

## Fixtures and execution partition

Collection constructs instances but must not run any setup, teardown or cleanup.
Build a fresh selected-only suite from the already checked 216 exact instances;
do not run an all-732 suite with 516 marked skipped/deselected. Class/module
fixture ownership is derived from selected instances only. In particular, the
native setUpClass paths in lq19.test_native_reader, p1.test_preparation and
lplan16.test_compiler stay unselected and cannot run during discovery/selection.
The selected direct-body inventory contains no own unittest setup/teardown or
cleanup registration; inherited lifecycle still needs runtime reconciliation.

Before and after each complete selected case, compare all eight shared patch
surfaces, their original absence where relevant, importer and namespace state.
Do not repair and continue on mismatch. Continuous RAM/disk/time/stop/custody
enforcement stays in the independent original native boundary outside the mocked
interpreter. A supplied token or a Python callback never establishes that guard.
