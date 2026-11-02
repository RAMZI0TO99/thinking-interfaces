# Candidate-v2 migration and bounded inventory

31 October 2026. Engineering only. This milestone follows the
[accepted finite L/Lhost design](cho51_p3_finite_l_design_20261031.md).
It does not admit L collection, candidate validation or scientific work.

## Implemented scope

The six-file candidate-v2 directory preserves the three production modules
byte-for-byte. Its mapping test has exactly two v1-to-v2 import-prefix changes;
its telemetry test has exactly two trailing decorator-colon deletions. The old
v1 directory is unchanged. The comparison binds the original rosters, exact
byte edits and 25 function mappings representing 39 + 78 = 117 expected cases. These
are expectations, not collected IDs or executed cases.

The current implementation is LP8/LQ8/lplan5. The bounded inventory parses
only five explicitly pinned candidate-v2 modules from retained bytes. It emits
deterministic AST occurrence records with source/span/shape identity, conservative
scope/epoch annotations, bounded pages and sanitized syntax diagnostics. It does
not import or execute candidate code. All effects, bindings, closure and decisions
remain unresolved; the index deliberately reports `INCOMPLETE_REFUSED`.

LP8 independently joins the comparison and both rosters to current reviewed
source pins and physical coverage before publishing its migration observation.
The parser audit gate accepts only the five exact retained byte strings and
filenames. Shared P output limits and the compiler's lower budget both apply.
No complete-plan or host-compatibility implementation is claimed.

## Review and execution

The [implementation contract](cho51_p3_candidate_inventory_contract_20261031.md)
and [preload successor](cho51_p3_candidate_inventory_preload_successor_20261031.md)
retain the original resource, process ownership, cleanup, deadline and stop
controls. Independent source review accepted the LP8/LQ8/lplan5 set of 256 common source
inputs. Q qualification and P physical preparation have separate admissions
and different source/result reviewers.

Q3 operation `98ac9239-4c15-4104-a525-bc31f2bee97b` returned exit 0 in 48.3894824
seconds. Its saved report has 384 successful methods (368 inherited, 16 new),
eight UTC controls, two native fault controls, three sharing checks, five native
observer cases and both actual P-bootstrap controls. The caller reports full
final input verification and owned closure. Independent actual review accepted
that tested scope; Root recorded Q-only qualification. The descriptive scope
discrepancy below is explicitly assessed in that acceptance.

That Q3 source was superseded after the P3 refusal below. Q4 operation
`4ec8d763-240e-4807-8bdc-3152e6d7c0df` returned exit 0 in 49.5483831 seconds with
384 successful methods and accepted final verification/owned closure. Its
source adds pinned ast/tokenize bootstrap initialization, readiness checks and
audit callback regression subcases; all method counts, controls and limits stay
unchanged. Independent Q4 actual review and Root qualification are accepted.

Separately admitted P4 operation `5d00a750-bbae-4f26-b2b4-e948c9fe1ba5`
returned exit 0 in 104.1375345 seconds. It reported:

- 21,425 retained files / 3,465,698,117 bytes, 893 native images and 4,847 edges.
- Exact migration observation for 25 functions and 117 expected cases, with
  zero collected IDs, candidate imports or executed candidate code.
- 13,406 AST occurrences in 53 pages across five pinned modules, with zero
  syntax diagnostics. All effect, binding, closure and decision states remain
  unresolved; `INCOMPLETE_REFUSED` is the intended inventory status.
- Full final input/output verification and owned cleanup; 123 output artifacts
  totaling 35,841,310 bytes, within the 256-file / 64 MiB aggregate budget.

Independent P review accepted the physical, migration and bounded syntax inventory scope. The reviewer completed a fresh
rehash of every input and output and all 196 nonempty directory census groups
(53,542 members), plus 12 absence checks, before current-document edits began.
That evidence describes the original release-time bytes and census. Later docs
are deliberately outside it; future runtime work requires fresh coverage and
applicable preparation.

## Preserved failures and limits

- Q1 `4125e317-3757-429f-8d6f-dbb4c7684ca3` refused before tests. Static review
  found a missing allowed namespace. Root also accidentally replaced that
  attempt's original caller receipt while extracting external output. The
  replacement is explicitly a derivative; the original receipt and 706-byte
  stderr content are unavailable. Intact tool output, journal and native records
  support only the independently reviewed failure scope. No cause or missing
  historical bytes are reconstructed.
- Q2 `2b9c40f4-87d7-46e2-9db6-e6c2a906f60e` refused before tests because an
  empty required cache parent was absent. Its original records are intact.
- Q2 `7c7312c7-f2f5-4acc-b9e6-75d0f8043a08` passed 384 methods but refused the
  second bootstrap-control constructor at the original 45-second launch bound.
  Final caller verification did not complete, so it remains unqualified.
  LQ7 moves both controls before the main supervisor without changing clocks
  or limits. Q3 observed their starts at about 10.02 and 11.60 seconds.
- P3 `b8a63867-4de2-42a0-9176-d13c9b60d37a` refused during compiler startup:
  the strict audit rejected compilation. Its 64 partial outputs cover a
  provisional 21,378-file map and 893 native images / 4,847 edges, but no migration
  observation, inventory or final verification was completed. Independent
  review accepted failure disposition and applicable owned cleanup only.
  The tokenize/namedtuple/eval cold-start path is a static inference; the rejected
  filename was not retained. LP8 initializes the pinned dependencies before the
  unchanged audit; its fresh Q4/P4 acceptance is summarized above.

Q3's descriptive scope note retained a stale Q2 command summary. Its current
executable admission, source review, Root adoption and actual launch bind the
Q3 UUID and sources. The discrepancy is saved separately, and the original
note is unchanged. Independent review accepted the precise pre-existing Q3
admission/review/adoption bindings while explicitly disclosing the stale summary;
no retrospective command-summary correction is presented as prelaunch evidence.

Earlier sources, admissions, refusals, review findings and receipts remain
frozen. The latest preservation baseline covers 5,339 prior files. Source and
document checks are distinct from runtime validation. The original candidate
117 cases and 34 V controls remain unexecuted; the full 40-scenario L mechanism
qualification remains incomplete. Bootstrap004 remains consumed, diagnostics005
held, custody UNRESOLVED and006 unadmitted. Science remains 0/1020, with the final
freeze unsigned.

## Next bounded step

Build and review provisional source-level decision closure from the bounded
inventory. Resolve finite initialization, resource, ABI, plugin and guard
obligations while keeping unimplemented capabilities unresolved. Implement the
matching Lhost/observer/reader successors, qualify them and refresh applicable
Q/P before final complete-plan acceptance. Separately admitted L collection,
V's 117 expectations / 34 controls and C closeout follow those gates.

The [Q4 actual review](../../runs/coordination/cho51_p3_candidate_inventory_20261031_q4/actual-review.json), [Q4 qualification](../../runs/coordination/cho51_p3_candidate_inventory_20261031_q4/root-qualification.json), [P4 actual review](../../runs/coordination/cho51_p3_candidate_inventory_20261031_p4/actual-review.json) and [Root P4 acceptance](../../runs/coordination/cho51_p3_candidate_inventory_20261031_p4/root-qualification.json) bind the accepted scope.

Phase evidence lives in
`runs/coordination/cho51_p3_candidate_inventory_20261031_q4` and
`runs/coordination/cho51_p3_candidate_inventory_20261031_p4`.
The [pre-step archive](../history/candidate_inventory_20261031/manifest.json)
preserves 13 exact documentation snapshots. No commit, push or scientific
execution is included in this step.
