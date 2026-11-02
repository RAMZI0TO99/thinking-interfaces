# Retained artifact reader and auxiliary provenance joins

28 October 2026, Asia/Riyadh. Engineering-only implementation and local validation.
This milestone follows the [negative verifier and bounded raw diagnostic](cho51_p3_boundary_implementation_20261028.md).
Current scheduling and admission follow the [project policy](../PROJECT_EXECUTION_POLICY.md).

The new [v3 package](../../tools/custody_boundary/v3/README.md) passed **45 tests**
and a separate retained read of **six pinned project artifacts**. This establishes
tested local byte integrity and record consistency. It does not authenticate a
historical machine, prove a complete restart or resolve bootstrap004 custody.
Positive boundary, launch and scientific authority remain false.

## Implementation

The [reader](../../tools/custody_boundary/v3/retained_reader.py) retains native
Windows handles to a fixed local NTFS drive, its directory chain and each file.
It rejects unsupported namespaces, aliases, reparse points, hard links and
changed byte counts/hashes. Reads and repeat checks use the retained handles.
Ordinary incompatible writer/delete opens are excluded while those handles are
held. Bounds are16MiB per artifact,64MiB aggregate,64 artifacts and2048 handles.
Release attempts every adopted handle; a refusal poisons the read set.

The [auxiliary layer](../../tools/custody_boundary/v3/auxiliary.py) checks five
closed record kinds: source review, runtime inventory, admission, actual caller
return and actual review. Exact references bind sources, policy, operation,
runtime metadata, raw observations and review artifacts. Types, accepted flags,
actor separation and chronological windows are checked. `assess_retained`
composes these joins with real retained file reads and repeat verification.
Auxiliary schema identifiers remain version2; the revised validation records
use version3. Actor strings and runtime-inventory metadata are not identity or
loaded-runtime attestation.

A coherent synthetic chain returns UNRESOLVED with verified local reads/joins.
Malformed required joins return REFUSED. No caller-supplied positive flag can
grant boundary qualification. The frozen v1 negative verifier is unchanged.

## Failed predecessor and correction

The [v2 source package](../../tools/custody_boundary/v2/README.md) remains frozen.
Attempt `8b18db89-9dbb-4044-9b91-b5bc4b356a26` ran44 methods:43 passed and one
errored in the directory-rename postcondition of the unsupported-volume test.
The runner and actual tool exited1. Saved new-Job/process closure was clean;
that is separate from passing tests and from old004 custody.

The constructor had already refused after opening only the drive root, before
opening the per-test directory. Renaming that directory did not isolate its
handle cleanup, and the parent runner separately retained the fixture directory.
The exact handle that blocked the rename was not logged and is not identified
as a proven cause. No reader handle leak is established by that error.

V3 replaces this assertion with observations of real successful native opens
and closes belonging to that constructor. A second case injects failure after
the last directory has opened and requires all owned handles to close. The
reader and auxiliary implementation bytes remain identical to v2, and all parent
containment locks remain. This is a new source review, admission and attempt,
not a retry of a consumed identity.

The v2 before/post-return observation spans231.1296018seconds because it includes
orchestration delay. It cannot qualify the90-second caller bound; its actual tool
wall time5.7186375seconds and runner time5.187seconds are retained separately.
The [independent predecessor review](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/predecessor-actual-review.json)
accepts the failed record only. No passing qualification is assigned to v2.

## Fresh validation

Root and one implementation author worked in separate file ownership scopes;
a different reviewer sealed the21 required source/fixture inputs. The
[source review](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/source-review.json)
SHA256 is `89e4c373c5dca857f2757be8d683a27dc10f274c46e8e5707a23df0429d1e7df`.
The266-file preservation baseline includes earlier design/implementation records,
all v2 sources and its failed attempt/fixtures. No old source or receipt changed.

The former app-managed Python path disappeared before v2 launch. The old `.venv`
points to that unavailable base. Root found and freshly pinned a retained
Python3.12.14 installation under the app runtime's
`codex-primary-runtime.previous-ca2c371f-2297-45d6-beb8-492c2b15e9cd` directory.
The exact732-file inventory is saved in
[runtime-pins.json](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/runtime-pins.json).
Nothing was installed, relocated or restored. This base/stdlib-only runtime is
not a qualification of the full numerical project environment.

Each mode received separate fresh admission and a new UUID. The
[reviewed runner protocol](../../tools/custody_boundary/v3/PROTOCOL.md) enforces
4GiB startup/active RAM,20GiB free disk,512MiB process/768MiB Job commit caps,
45seconds child/75seconds work/90seconds whole-caller limits,1MiB payloads,
one CPU/library worker and hidden GPUs. A parent watchdog is additional to the
worker. The local stop file, atomic unnamed-Job assignment, suspended creation,
original handles, empty-Job check and handle closure remain required. Parent
and child use isolated no-site/no-bytecode execution with a fresh absent cache
prefix. This envelope does not amend the future006 design's10GiB startup floor.

| Operation | Identity | Result | Runner seconds | External QPC bound seconds |
| --- | --- | --- | ---: | ---: |
| Tests | `4b3d1530-2a66-4425-895c-95009b8b34b1` | 45 run,0 failures,0 errors,0 skips; actual exit0 | 5.516 | 6.5440160 |
| Retained read | `a7c08aed-1c97-4ba1-9b54-9409073664d9` | Six pinned artifacts read; UNRESOLVED; actual exit0 | 4.125 | 5.2413575 |

The31 reader methods cover ordinary sharing, aliases, hard links, exact bounds,
repeated handles, release and injected native failures. The14 auxiliary methods
cover type/field/ref/actor/time tampering and a materialized synthetic chain.
Semantic tampering rebuilds downstream hashes so tests exercise the joins.
Reparse checks inject native attributes; actual junction/symlink creation is
not qualified. No tests are skipped to supply missing platform evidence.

The six-artifact operation reads the frozen v1 verifier, three exact004 failure
records and the two prior v1 payloads. Each witness records final path, volume/file
identity, size, link count, timestamps and hash from the retained handle. This
does not reexecute those artifacts, query providers or authenticate their author.

Both v3 operations report normal child exit, an empty Job, Job closure, original
process exit and process/thread handle closure, with no cleanup or sampling errors.
Actual tool chunks are `81755b` and `699349`. These new operations' closure does
not establish historical004 cleanup. Saved pending-review flags are immutable;
the separate actual review and Root adoption resolve them within this scope.

## Evidence and review

- [Test admission](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/tests-admission_001.json),
  [complete test payload](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/attempts/4b3d1530-2a66-4425-895c-95009b8b34b1/payload.json)
  and [actual caller audit](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/tests-external-audit_001.json)
- [Read admission](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/smoke-admission_001.json),
  [retained witnesses](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/attempts/a7c08aed-1c97-4ba1-9b54-9409073664d9/payload.json)
  and [actual caller audit](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/smoke-external-audit_001.json)
- [Independent actual-result review](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/actual-review.json)
- [Root adoption](../../runs/coordination/cho51_p3_retained_chain_20261028_v3/root-qualification.json)

The independent outcome is ACCEPTED_RETAINED_BYTE_AND_AUXILIARY_FIXTURE_RESULTS.
Actual-review SHA256 is
`d263e4c3d2bd0e2dc936f6c8a3a97d42b66b22e7b4d96655db1d0e49f506d0ef`.
Root adopted that exact review after rechecking142 evidence pins,21 source pins
and266 preserved predecessors. UTC caller bounds were6.5441127seconds for tests
and5.2418620seconds for the read operation; both UTC and QPC bounds are within90s.
No positive boundary or scientific authority follows.

## Remaining work

Next qualify focused Windows provider evidence and the historical operation's
host association, using the [provider assessment](cho51_p3_boundary_providers_20261028.md)
and [custody design](cho51_p3_local_custody_design_20261028.md). The earlier raw
query was truncated. Ordinary boot timestamps, later PID absence, local file
identity or matching actor names cannot prove a complete restart, cross-boot
clock ordering or persisted-domain exclusion. No restart is requested here.

The reader excludes ordinary incompatible sharing; it cannot promise an atomic
snapshot against preexisting writable mappings, privileged/kernel/filter/raw-volume
interference or hardware faults. A copied witness is not an unforgeable certificate.
Complete48-scenario design qualification, successor006 and positive controller
admission remain open. Bootstrap004 is FAILED_UNRELEASED_CONSUMED;005 is held.
The original117 candidate tests and34controls remain unexecuted. Scientific
cells remain0/1020, and the final freeze is unsigned. No numerical or scientific
workload ran. Changes remain uncommitted; no push occurred in this milestone.
