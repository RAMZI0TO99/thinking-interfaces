# Canonical pipeline interface audit, 25 October 2026

## Status and authority

Static source audit only, opened15:03UTC. The owner accepted the proposal to
start an interface audit and bounded implementation plan. This is not authority
to implement a numerical bridge, invoke a canonical worker, publish a measured
cell, repeat a previous episode, or start the study. No Python/interpreter
imports, tests, models, signal/weight reads, numerical work or Jobs execute in
this phase. Native source/metadata inspection and document-format checks are
separate from executed validation.

Root owns this report, the [bounded plan](cho51_canonical_boundary_plan_20261025.md)
and current handoff/coordination updates. One serialized explorer maps canonical
interfaces; independent static document review follows. Pro2 confirmed compatible
Source-only ownership/allocation: Pro3 Root+one at most2, Pro2 at most3/shared5.
There is no new compute grant. Preserve canonical432, both accepted packages,
all used operations, raw data, weights, failures and accepted evidence.

The accepted previous milestone remains the separately versioned numerical
composition, not unchanged canonical production qualification. Its final review
SHA256 is `0773288c76842602f42ea8e79eb60e973ae5dee7d681c0bee18f23a764a91e18`;
its128-artifact closeout export manifest is
`009a52ab2ea84e0b603d145e6266f484748a821ab3c28f43c273a51622c06060`.
Historical seven-document bindings authenticate that export's snapshots, not
later mutable resume heads.

## Canonical call map

| Surface | Interface and consequential behavior | Static source |
| --- | --- | --- |
| Front door | `main(argv: Sequence[str] \| None = None)` distinguishes plan from execution. Plan checks pins, not route tensors or runtime qualification. | [run_cho_first_tranche.py](../../scripts/run_cho_first_tranche.py#L68) |
| Parent | `execute_engineering_cases(*, root, pins_path, pins_sha256, admission_path, receipt_path, cases, limits, worker, attempt=1)`; owns final-recorder lock across claim, supervised child and acceptance. | [phase2_cho_execution.py:877](../../evaluation/phase2_cho_execution.py#L877), [lock:977](../../evaluation/phase2_cho_execution.py#L977) |
| Child CLI | `main()` requires contract path/hash beneath `runs/phase2/sweeps`. | [run_cho_execution_child.py:21](../../scripts/run_cho_execution_child.py#L21) |
| Child implementation | `run_cho_execution_child(root, contract_path, contract_sha256)` validates quarantine/native/pins/runtime/admission/route and dispatches production runner with staging recorder. | [phase2_cho_execution.py:451](../../evaluation/phase2_cho_execution.py#L451) |
| Production runner | `ProductionChoCaseRunner.__call__(*, plan, executor, route, method_config)` runs source selection, persists evidence and publishes selected source before target execution. It is not restoration-only. | [phase2_cho_sweep.py:653](../../evaluation/phase2_cho_sweep.py#L653), [selection:698](../../evaluation/phase2_cho_sweep.py#L698), [publication:751](../../evaluation/phase2_cho_sweep.py#L751) |
| Target executor | `TargetCaseExecutor.run_case(plan, *, adapter, identity, method_config, selection_evidence_sha256, ..., protocol_config, catalogs, selection_record, episode_record, assets)` eventually invokes `record_cell`. | [phase2_pilot.py:601](../../evaluation/phase2_pilot.py#L601), [cell:832](../../evaluation/phase2_pilot.py#L832) |
| Parent verifier | `verify_staged_proposal(root, contract, contract_sha256)` requires staging measured==1 and an evaluation-cell envelope; accepted parent then calls `owned_locked.record_cell`. | [phase2_cho_execution.py:555](../../evaluation/phase2_cho_execution.py#L555), [measured:595](../../evaluation/phase2_cho_execution.py#L595), [promotion:1024](../../evaluation/phase2_cho_execution.py#L1024) |

These are hard scope boundaries, not merely mismatched callback signatures.
The canonical execution module calls this engineering and retains false
scientific-freeze flags while recording measured cells. Thus a measured record
does not itself prove scientific authorization, and an unsigned freeze must not
be misrepresented as an automatically enforced API refusal. Nevertheless,
current measured0/source-fitting0 scope excludes these entry points.
`SweepAdmission` is compute/resource admission, not the owner's scientific
freeze signature ([phase2_cho_sweep.py:274](../../evaluation/phase2_cho_sweep.py#L274)).

## Single-root versus independent provenance

The public
[`restore_cho_selected_source`](../../evaluation/phase2_cho_source_restore.py#L584)
accepts root, plan, method/config pins, selected candidate, manifest/evidence
pins, protocol/catalog/selection/assets and optional store. Its supplied store
must share root (:600). [Store restoration](../../evaluation/phase2_selected_source_store.py#L827)
captures that root and compares the producer source to current source (:847–865).
The [full selector verifier](../../evaluation/phase2_selection_evidence_binding.py#L450)
and [publication gate](../../evaluation/phase2_cho_publication_gate.py#L125)
also require the historical contract's source to match freshly captured root.
Final [adapter release](../../evaluation/phase2_cho_source_restore.py#L653)
rechecks the same source equality.

These deliberate checks cannot represent historical producer4491e2a and current
executorc177d00 as independent roles. Changing only the store argument does not
solve selector/publication/final-release comparisons. Do not weaken comparisons,
spoof Git, monkeypatch capture_source, rewrite historical envelopes or flatten
producer/executor/recorder into a false CellIdentity.source.

The accepted [factory](cho51_provenance_restore_v1/factory.py#L274) instead
requires the actual bound LockedCase._require_active and independently pinned
producer/executor roles. It reuses canonical model preparation and leaf checks
with a separately versioned [producer-explicit complete verifier](cho51_provenance_restore_v1/selection.py#L28).
The accepted [worker](cho51_provenance_numerical_worker_v2/numerical_worker.py#L400)
holds the real lock across one backend/two verifiers, writes an outer attestation,
uses record_engineering_success and verifies measured0 (:451–462).
Its [recovery](cho51_provenance_numerical_worker_v2/numerical_worker.py#L481)
authenticates external request/attestation pins and replays only existing
engineering intent; it does not authorize canonical measured-cell recovery.

## Reuse matrix for the first metadata-only boundary

- Reuse the actual canonical CasePlan, TrialCatalog, ChoCaseInputPins and full
  route types; independently check exact supplied identities and metadata.
  Preserve original1040 and adopted1020 as separate contracts, with52 available
  catalogs/assets and only subjects02–52 as evaluation targets.
- [load_execution_pins](../../evaluation/phase2_cho_execution.py#L210) is a useful
  read-only pin/config verifier, not execution admission. It reads pinned config
  metadata and captures current source. The new boundary must strict-parse and
  physically bound bytes independently before calling it; its json.loads alone
  does not provide the proposed duplicate-key/nonfinite/extra-type policy.
- Do not call [prepare_cho_first_tranche](../../evaluation/phase2_cho_case_inputs.py#L96)
  in this metadata-only unit: it calls read_catalog on52 Profile A NPZs (:139)
  and loads/rechecks Profile B assets. The
  [prepare_cho51_worker_route](cho51_worker_bridge_v1/worker_bridge.py#L72)
  convenience function delegates this numerical-input preparation.
- Do not call [verify_cho_selected_manifest_files](../../evaluation/phase2_cho_selected_manifest_bridge.py#L254)
  in the metadata-only unit: despite no tensor restoration, it streams weight
  bytes (:363) and verifies the returned physical witness (:372).
  A non-Torch API is not automatically metadata-only.
- Supplied typed route/catalog/asset metadata must have external independently
  pinned origin evidence and full structural rederivation. A class match or
  matching metadata SHA is not fresh physical signal/weight authentication.
  The report must explicitly retain those unperformed obligations. Do not
  fabricate an existing manifest witness or label an unchecked route verified.
- Do not invoke selector dispatch, TargetCaseExecutor, ProductionChoCaseRunner,
  canonical child/parent execution, record_cell, or either recovery API.
  A noop recorder proxy or synthetic measured==1 proposal is not a bridge.

## Timing evidence and uncertainty

The accepted actual native Job took590.082323s under600s: arithmetic headroom
is9.917677s. This is one observed pass, not a reliability distribution or a
production-ready margin. Internal qualification reports573.828s using a
different timer boundary; do not subtract or interpret it as a phase profile.
V5/v6 actual hard600 failures remain failed/quarantined, not timing samples
from this unchanged source. Unitv7 normal0 was531.109877s; external actual
stdlib closeout was62.763709s under its separate300s limit.

Source inspection identifies repeated full source/origin/input checks in
[verify_origin and callbacks](../../runs/coordination/cho51_provenance_numerical_worker_20261025_v7/parent.py#L156)
and loaded-module hashing/recheck in
[Runtime.finish](../../runs/coordination/cho51_provenance_numerical_worker_20261025_v7/runtime.py#L820).
It does not identify measured bottleneck shares. Artifact timestamps only
order milestones; their differences are not CPU time or exclusive phase cost.
V7 already moved only duplicate post-terminal parent sweeps to mandatory
external full-origin/input closeout. Both genuine backend input audits, both
complete verifiers, final contract/fixture checks and Runtime.finish remain
inside600s. Do not move additional obligations or cache hashes/authorization
based on this audit.

Before a later executable bridge, propose independently reviewed bounded
monotonic telemetry at admission/import/pin/origin/input/route/restore/support/
query/verifier/terminal/loaded-module phases, recording nesting and inclusive
versus exclusive semantics. Diagnostic events never grant authorization;
failure tails must remain bounded and null/unknown after numerical entry.
No current frozen source is instrumented or rerun by this plan.

## Conclusion

The next meaningful unit is a separately versioned canonical-facing metadata
preflight/schema boundary, not a direct production call-through wrapper.
It can establish input-contract compatibility and explicit outstanding gaps;
it cannot qualify unchanged canonical workers, single-root factories, real
inputs, measured publication, current runtime, performance or science.

The [bounded implementation plan](cho51_canonical_boundary_plan_20261025.md)
defines that first unit and hard stops before any executable successor.
No current implementation or new executed validation is claimed.
