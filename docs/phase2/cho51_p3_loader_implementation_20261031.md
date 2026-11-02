# L observer and collection implementation checkpoint

31 October 2026. Engineering only. The observer, collection runner, authority
checks and file-only plan compiler are implemented and independently reviewed.
Fresh Q2 qualification is accepted. Fresh P2 physical preparation is **not**
accepted: its caller stopped during startup, before authority or child dispatch.
Actual L collection, the 117 candidate tests and 34 successor controls remain
unexecuted. Scientific cells remain **0/1020**.

## Implemented and reviewed

The frozen `tools/local_validation/l1` sources implement collection gating,
import/resource/native guards, the native notification observer and event ledger.
`lhost1` supplies the bounded caller, supervisor, inherited transport, exact
authority joins and closed ABI observations. `lplan1` derives an inert finite
plan from retained source text and explicit reviewed decisions; missing or
unresolved decisions refuse completeness. No installed-code superset becomes
an execution allowlist.

Independent source review resolved ten findings across five revisions, including
indirect-call completeness, startup snapshot/event reconciliation, exact writer
inheritance, typed ABI results, the fixed child vector, source/runtime/Q/P joins,
pre-effect native loading checks, retained JSON identities, independent complete
plan acceptance and compatibility with the actual P descriptor shape.

The [implementation contract](cho51_p3_l_implementation_contract_20261029.md)
and [LQ2/LP2 successor contract](cho51_p3_lq2_array_contract_20261031.md) define
the scope. Original LQ1 failed on a PowerShell tool-path array construction before
native compilation or tests. The reviewed successor corrects that construction
and preserves the old sources and failed attempt. It does not increase limits.

## Accepted Q2 evidence

Operation `611baed2-cdb9-4ac5-aa67-091058962ec3` completed in **51.0094698 seconds**,
with tool exit zero, full final input checks and accepted owned cleanup:

- 356 exact methods passed, with no failures, errors or skips.
- Eight UTC controls, two actual transport/timeout fault controls and three
  sharing controls passed.
- Five native observer cases passed: transient load/unload, overflow, invalid
  reason, malformed UTF-16 and path bound.
- Seven native build children and eight supervised qualification children
  closed. Independent review inspected the generated callback instructions.
- Source pins (171), bootstrap runtime files (732), compiler inputs and the
  3,474-file preservation baseline were rechecked without drift.

The [independent Q actual review](../../runs/coordination/cho51_p3_loader_implementation_20261031_q2/actual-review.json)
and [Root qualification](../../runs/coordination/cho51_p3_loader_implementation_20261031_q2/root-qualification.json)
accept this exact tested scope. The frozen source qualification map describes
40 mechanism scenarios; these subset results do **not** complete that matrix.
Real startup races, host fault injections, additional loader permutations and
the complete real-package plan remain separate work.

The earlier Q2 startup attempt `0a56af13-c1f2-47e7-b521-c9ad09123712` remains
consumed with explicit caller/guard/journal closure unproven. The later success
does not repair that history.

## P2 coverage and startup failure

The independently reviewed proposal covers **20,798 files / 3,458,551,105 bytes**,
with 11 pin pages and 13 explicit extra inputs. It includes both frozen and
successor implementation libraries, the newly generated native artifacts and
the plan specification. Independent metadata recensus and all current byte pins
matched. This [coverage review](../../runs/coordination/cho51_p3_loader_implementation_20261031_p2/coverage-review.json)
accepts a proposal, not native retained physical preparation.

Fresh P operation `a29c2264-da0e-4306-9bc8-f7c1fea976af` returned tool exit one
after 5.553409 seconds. Its five-event journal ends at `assembly_loaded`, directly
before the memory-counter constructor. No counter-ready, authority, Job or Python
child dispatch is recorded. The constructor or startup deadline is a possible
explanation, not a proven cause. Explicit caller, guard and journal closure
remain **UNPROVEN**. No physical result or plan derivation was produced.

The [independent failure review](../../runs/coordination/cho51_p3_loader_implementation_20261031_p2/failure_a29c2264-da0e-4306-9bc8-f7c1fea976af/actual-review.json)
verified source/runtime/control joins and no drift against 3,707 preserved files.
The [Root disposition](../../runs/coordination/cho51_p3_loader_implementation_20261031_p2/failure_a29c2264-da0e-4306-9bc8-f7c1fea976af/root-disposition.json)
consumes this attempt and holds another unchanged P admission pending a separately
reviewed bounded startup diagnostic or successor. All existing limits remain.

The plan specification is intentionally incomplete. Empty source decisions and
missing initialization/native/ABI bindings would require `INCOMPLETE_REFUSED`
even if physical preparation succeeds. No complete plan or L authority is
inferred from the seed or its metadata review. The earlier malformed, unadmitted
specification draft is preserved separately; revision2 is the reviewed proposal.

## Remaining sequence

1. Review and qualify a bounded startup diagnostic or successor with durable
   termination evidence and original-handle cleanup; preserve all failed records.
2. Obtain fresh P coverage/admission and complete retained physical preparation,
   full final verification and independent result acceptance.
3. Resolve and independently review the finite initialization, guards, native
   choices, resources, ABI and plugin plan; close applicable qualification gaps.
4. Separately admit L collection. Only after accepted L may V execute the 117
   candidates and 34 successor controls, followed by closeout.

MLflow is planned for evaluation after the current Q/P work and before larger
experiments, initially through an exporter of accepted records into a local
tracking store. No MLflow dependency or runtime was installed or admitted.

Q10/P10 remain the last accepted physical-preparation foundation (20,406 files,
888 native images and 4,843 edges); their pins do not cover the new implementation.
Bootstrap004 remains consumed, diagnostics005 held, custody UNRESOLVED and006
unadmitted. The original 48-case and 26-scenario matrices remain incomplete.
The final scientific freeze is unsigned. No Git commit or push occurred here.
