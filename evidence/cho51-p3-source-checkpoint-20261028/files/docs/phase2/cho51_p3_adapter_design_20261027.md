# P3 canonical-facing adapter design — 27 October 2026

## 1. Status, ownership and scope

**Design only; engineering only. No P3 implementation or executed qualification.**
The owner requested this design on 27 October 2026, Asia/Riyadh. It follows the
accepted [P1/P2 metadata boundary](cho51_canonical_boundary_qualification_20261025.md),
[interface audit](cho51_canonical_pipeline_interface_audit_20261025.md) and
[P3 hard stop](cho51_canonical_boundary_plan_20261025.md#p3-hard-stop-before-executable-canonical-facing-work).
Root owns these new design/telemetry/review documents and dated handoff updates.
One read-only explorer maps exact interfaces and then independently reviews the
design. Pro3 stays Root+one<=2. No frozen implementation ownership is acquired.

Permitted current work: bounded native source/metadata reading, document writing
and document consistency checks. No Python/imports, fixture preparation, tests,
profiling, signal/weight verification, model, inference, native Job, launcher,
admission, compute grant or scientific execution is created. All older grants,
Source intervals and operations are inert; a fresh peer coordination request was
sent for this design, without requesting compute. Current coordination disposition
is recorded in the [static review](cho51_p3_adapter_review_20261027.md).

The design selects a **new versioned terminal-owning engineering controller**,
not a call-through production runner. Its prospective numerical scope remains
one subject02 / `labram_linear` / five-shot / seed11 / repetition1 **synthetic
engineering** episode, only under a future separately authorized phase. All
1,040 original / 1,020 adopted route identities and 52 sources are context, not
permission to execute the roster. Measured scientific cells remain0. Target01's
original retry budget remains0; checkpoint-cohort review and final owner freeze
remain outstanding.

## 2. What P3 adds, and why a wrapper is insufficient

The existing [parent entry](cho51_provenance_numerical_worker_v2/pipeline.py#L7)
only validates and delegates to
[run_worker_case](cho51_provenance_numerical_worker_v2/numerical_worker.py#L400).
That worker owns the real recorder session, claim, both requests, backend,
verifiers, attestation and engineering terminal. It exposes no already-locked
transaction hook. Its request/proof/attestation schemas contain no P3 binding.
A new sidecar beside that call is not automatically authenticated by its terminal.

The selected P3 addition is substantive:

1. Independently connect the canonical metadata request/assessment to the exact
   typed numerical route, configurations, source domains and historical input
   lineage, with explicit unperformed obligations.
2. Own one real identity-lock transaction and a new immutable adapter binding.
3. Bind that new evidence, the actual numerical requests/proof and controller
   source into a **new outer adapter attestation**.
4. Give the real canonical engineering terminal that outer attestation's digest,
   not a detached sidecar or the old inner-only attestation digest.
5. Keep compute admission, physical verification and science authority outside
   the compatibility report. No measured-cell contract is intercepted.

The unchanged canonical parent calls `record_cell` after requiring a measured1
proposal. `ProductionChoCaseRunner` performs source selection/publication, and
`TargetCaseExecutor.run_case` ultimately writes a measured cell. None is a P3
entry point. Their names containing “engineering” do not change their behavior.
See the [source-linked call map](cho51_canonical_pipeline_interface_audit_20261025.md#canonical-call-map).

## 3. Architecture decision: controller identity versus claim identity

**Selected design:** retain exactly one honest numerical-worker claim with
worker `cho51_provenance_numerical_worker_engineering_v2`; separately identify
the new controller as `cho51_canonical_adapter_controller_v1` in its own request,
binding, attestation and fresh source pins.

This distinction is necessary for unchanged backend/verifier reuse. The
[v2 worker constant](cho51_provenance_numerical_worker_v2/numerical_worker.py#L15),
[_request_files](cho51_provenance_numerical_worker_v2/numerical_worker.py#L128)
and [_claim](cho51_provenance_numerical_worker_v2/numerical_worker.py#L346)
physically require that exact numerical claim identity. There is no worker
override in `NumericalWorkerRequest`. P3 must not rename the claim, monkeypatch
`WORKER`, fabricate a v2 proof for a different worker, or present its new
orchestration as the already-qualified v2 parent.

The numerical claim identifies the reused numerical worker contract; fresh P3
pins separately identify the new controller's code and all transaction behavior.
The canonical recorder remains unchanged. Its
[engineering terminal](../../evaluation/phase2_runner.py#L723) accepts a verified
attestation digest rather than imposing the old v2 attestation schema, enabling
the explicitly versioned outer proof. This mechanical compatibility is **not**
executed P3 qualification.

If a distinctly named P3 **claim worker** is later required, stop this reuse
profile and separately version the numerical request/backend/verifier ownership.
That is an alternative project step, not a flag on this design. The unchanged
factory is more general, but that does not make the v2 numerical verifier general.

## 4. Proposed source ownership and API

The following namespace is proposed, **not created by this task**:

`docs/phase2/cho51_p3_adapter_v1/`

| Proposed file | Responsibility |
| --- | --- |
| `contracts.py` | Strict immutable intent/binding/completion schemas; finite canonical bytes and independent digests |
| `mapping.py` | Genuine canonical type snapshots, full/adopted-route reconstruction and explicit context/input-lineage joins |
| `transaction.py` | One-lock terminal owner; honest v2 claim; actual inner requests/backend; new outer attestation; quarantine semantics |
| `verification.py` | Independent physical derivation of adapter binding/outer attestation plus genuine inner numerical verification; read-only recovery checks |
| `adapter.py` | Public metadata and engineering-controller entry points, with no implicit dispatch |
| `test_adapter.py`, `README.md` | Focused nonnumerical contract tests and exact scope/API documentation |

Root would own fresh operations/guard/custody sources; an assigned child would
own only an explicitly delegated new package. Independent review is serialized
under Root+one<=2. Canonical432, accepted boundary/factory/v2 worker/target route,
used operations, receipts, raw data and weights remain unchanged.

Proposed API names, not implemented signatures:

- `assess_adapter_intent(...) -> AdapterCompatibility`: metadata only; no
  output/claim/lock/backend capability. Positive status means compatible intent,
  with all execution/scientific authority false.
- `run_adapter_engineering_case(...) -> AdapterCompletion`: a separate explicit
  admitted transaction, supplied the real recorder/context, independently pinned
  immutable intent, genuine full/adopted route and exact v2 backend/verifier.
- `recover_adapter_intent(...)`: a separately scoped **read-only-evidence** path
  for an existing outer adapter intent, with external request/attestation pins;
  no backend parameter. It cannot be substituted by either old recovery API.

Never call `run_parent_pipeline` or `run_worker_case` from inside a P3-held
`case_session`: that opens a second session and conflicts with actual
[lock ownership](../../evaluation/phase2_runner.py#L298). The new transaction
must explicitly implement and qualify its own orchestration. Reuse of pinned
private v2 helpers, if needed, must be enumerated and tested as dependencies;
they are not a stable public already-locked API.

## 5. Compatibility profile and genuine mismatches

Profile `cho51_p3_synthetic_linear_v1` is fixed to the accepted synthetic input
lineage, not a real-cohort bridge or generic four-method adapter.

### Configuration agreement is possible; evidence is not interchangeable

V7 [copied five canonical TOMLs](../../runs/coordination/cho51_provenance_numerical_worker_20261025_v7/parent.py#L62)
into its isolated fixture. Its selected linear method settings structurally
match the canonical candidate row. Do not invent a protocol/settings mismatch.
Instead, independently compare actual paths, bytes and structural digests under
their declared domains, rather than assuming a match from those old observations.

The real incompatibility is input/proof scope:

- The metadata boundary requires `cho51_canonical_metadata_cohort_origin_v1`,
  explicitly `raw_input_bytes_verified=false`; its cohort pin is a **metadata
  origin**, not a numerical input audit.
- The numerical verifier requires the preserved exact synthetic source fixture
  and **213 original inputs / 734,579,463 bytes**. Historical evidence and
  selected/baseline weight roles are authenticated separately, outside that
  213-file input-audit total. The full verifier is not metadata-only even when
  no tensor is restored.
- The accepted target route requires all52 synthetic catalogs, each42 trials,
  with exactly ten support/two query/thirty unused trials for the fixed case.
  The P1/P2 test fixture's arbitrary unverified trial strings and fabricated
  hashes do not match those numerical inputs.

Future preparation may derive an **externally supplied but still unverified**
metadata package from the authenticated historical manifest's declared catalog
and asset identities. It must preserve the real synthetic trial ordering and
file digests; it cannot mark them freshly physically verified by copying a
historical assertion. Fresh physical audits remain a separate execution-stage
obligation. No NPZ builder or weight verifier is called by metadata preflight.

### Required independent joins

| Domain | Required check | Forbidden shortcut |
| --- | --- | --- |
| Canonical route | Genuine full1040/adopted1020 types; exact case IDs, order, method rows, seeds,52 catalogs/assets, selections and nested episodes | Passing counts or a caller's summary only |
| Selected plan | Exact subject02/linear/5/11/repetition1 and membership in both appropriate rosters | Dispatching all retained cases or another method |
| Metadata provenance | Actual boundary request bytes/report digest, fixed anchors, all authorityfalse and current ledger0 | Accepting a caller-constructed `BoundaryAssessment` solely by class/hash |
| Numerical lineage | Every route/catalog/asset/episode claim rederived against the exact independent historical origin and later physical audits | Reusing the metadata cohort pin as a raw-input or selected-weight witness |
| Producer | Historical selection/publication/evidence/recipe/state identities from accepted origin | Substituting current executor source |
| Executor | Actual project root, canonical source domain, fresh controller/operations source manifest and exact current runtime-byte inventory | Equating version strings or carrying old runtime qualification forward |
| Recorder | Fresh isolated fixture under owned output; recorder at `fixture/runs/phase2/lifecycle`; its actual source fingerprint | Replacing fixture provenance with canonical432 or the metadata report's recorder role |
| Settings | Exact canonical and copied fixture bytes, method/protocol logical digests and owner adoption | Treating equal logical settings as proof of raw-input lineage |

The boundary's “recorder” role uses the current **project** source plus a
historical worker-review evidence tag. It is not the future isolated recorder's
five-TOML fingerprint. Preserve both with explicit role/domain labels. The
historical recorder identity in accepted origin is a third dated fact, not the
new recorder's source. No false single-root `CellIdentity.source` is created.

Build owned genuine dataclasses from strict bounded primitives before comparing
or serializing; reject custom accessors/subclasses/proxies/cycles. Preserve the
full/adopted shared-route relationship. Respect the genuine planner helper's
module/class epoch: no stale contracts after a reload, fabricated class,
AST-shadowed helper or monkeypatched source capture. Reconstruct and re-assess
the whole owned graph if a legitimate helper epoch changes; never bypass checks.

## 6. Acyclic immutable artifact graph

All names below are **proposed new schemas**; accepted inner schemas stay exact.
They require duplicate-key/nonfinite/unknown-field rejection, exact integer and
Boolean types, normalized direct paths and bounded defensive data.

1. **`cho51_p3_adapter_intent_v1`**, preclaim: controller/numerical-worker IDs,
   fixed profile/plan, boundary request and expected assessment pins, full/adopted
   metadata digests, config/owner/origin pins, source-role domains and outstanding
   obligations. It contains no future claim, its own hash, final attestation or
   operations-pins hash. This immutable intent **is the P3 controller request**,
   stored as `adapter-intent.json`; there is no additional unnamed P3 request.
   The accepted inner `request.json` remains a different artifact/schema.
2. **Fresh operations pins**, independently prepared/reviewed: bind intent,
   boundary inputs and expected report, exact new package/operations source
   files, accepted dependency files, actual runtime bytes and finite scope.
   Fresh compute/native admission references these pins; it is not inside the
   boundary assessment.
3. **Real claim and unchanged inner requests**, under the lock: genuine v2
   numerical claim; compact factory request first, newline-canonical outer
   numerical request second. Their distinct original encodings and hashes remain.
4. **`cho51_p3_adapter_binding_v1`**, under the same lock: immutable intent/pins/
   admission/context/claim identities, both actual inner request digests, all
   independently derived mapping joins and fresh assessment digest. Persist
   create-once and fsync **before backend entry**. It does not include an outer
   attestation hash or any future output hash.
5. **Verified inner numerical proof**, after the single backend: original
   request/proof semantics, both real verifier observations, consumed markers,
   physical tensors/state/input proofs and honest metrics, never opaque callback
   returns as evidence.
6. **`cho51_p3_adapter_attestation_v1`**, under lock: binding file/hash and all
   earlier pins, exact verified inner proof/request/witness/marker digests,
   controller provenance, observed numerical ledger and explicit measured0 /
   scientific_admission=false. It has no self hash or future terminal digest.
7. **One canonical engineering intent/success**, using the **outer P3
   attestation file digest**. No separate inner v2 terminal is written.
8. **External closeout**, after native closure: independently binds all prior
   physical proofs, final trace, result/native receipts, owned-child custody and
   accepted review. It does not rewrite child pending-native flags.

The binding and its authoritative dependencies are revalidated after each
verifier and immediately before terminal, including same-byte physical
replacement. The final built-in v2 `_proof_files` does not inspect new adapter
files: P3 verification must do that explicitly. No sidecar is claimed protected
by an unchanged v2 stability callback that does not know it exists.

Proposed new-control limits: intent64KiB; binding256KiB; outer attestation1MiB;
at most16 new control files and4MiB aggregate new control bytes, excluding the
separately specified bounded trace. Existing boundary8MiB/file,32files/32MiB,
1MiB report and accepted factory/evidence/weight bounds are unchanged. These
are separate accounting domains, not an excuse to omit dependencies from a
reviewed whole-phase input/output budget. Reject aliases, reparse ancestors,
hardlinks or unbounded inventories; retain the exact reviewed Git-binary
exception only in runtime verification, not ordinary control files.

## 7. Proposed transaction and failure state machine

| State | Required action before advancing |
| --- | --- |
| `intent_checked` | Independently pin/strict-read controls and fresh runtime/compute admission; reconstruct genuine route; run genuine metadata assessment and all profile joins; no lock or numerical work yet |
| `claim_held` | Acquire one real session; fresh attempt1 claim with the honest v2 identity; establish actual bound live-lock capability; create both inner requests and adapter binding |
| `backend_entered` | Consume existing backend/factory once-only markers under the accepted policies; enable only the precise admitted numerical scope; no source fitting |
| `proof_verified` | Backend exactlyonce; two admitted independent verifier callback invocations plus every mandatory internal physical proof rederivation; separately authenticate adapter bindings/physical identities around both callbacks; require full observed budgets and current genuine metrics |
| `outer_attested` | Create-once/fsync outer P3 attestation; retain/revalidate it and all authoritative inputs under live lock |
| `engineering_terminal` | Canonical engineering success exactlyonce with outer digest; verify engineering1/measured0 and no evaluation-cell/publication intent |
| `external_complete` | Separate native receipt, closeout, pipe EOF/reaping, explicit full release and independent actual review accept the exact evidence |

Reused `FactoryNumericalBackend`, real factory, target route and verifier keep
their actual physical work. The prospective aggregate vector is source0 /
restore1 / support1 / gradient1 / query-invocation1 / query-trials2 / model1 /
measured0; factory-local support/query remain0. Detailed constructor, decode,
state-load, clone and observer counts stay equal to the accepted v2 contract.
No old predictions are substituted; any fresh wrong predictions remain wrong.
The new operations runtime must independently qualify the controller's actual
call sites, execution-scope context and observer stack against a narrow reviewed
allowlist. Old v7 guard stack/path assumptions do not automatically admit a new
terminal owner. Never spoof a stack, widen an allowlist to arbitrary callers or
reuse old guard acceptance as new-controller qualification.

Failure before backend records observed zero numerical work only when the guard
actually observed that state. After backend entry, partial counts remain
unknown/incomplete unless independently complete; never infer zero from a failed
receipt. Consumed markers cannot be reset. Failure after durable attestation or
intent is quarantined as recovery-required, not retried with a new wrapper.
Preserve every failed source/version/output and actual native closure.

Recovery requires explicit external `expected_intent_sha256`,
`expected_binding_sha256` and `expected_adapter_attestation_sha256` for the
**P3** intent/request, binding and outer attestation, plus their direct paths and
the exact already-existing engineering intent. It must not guess that the old
inner `request.json` is the P3 request. Reacquire the real identity lock,
rederive all physical adapter and inner proof joins and replay only that intent's
terminal. No factory authentication/restoration, numerical backend, NPZ loading,
optimizer, model, inference or new attempt is allowed. Existing
`recover_parent_pipeline` binds the old attestation schema and cannot recover a
P3 outer intent. Ambiguous/missing proof or already-terminal disagreement refuses.
Recovery implementation/validation is a separately named future subphase; it is
not an automatic action after a failed diagnostic.

## 8. Planned validation and implementation gates

No test count below is an executed or inherited passing count. Enumerate actual
tests only after the new source is settled and reviewed.

| Group | Positive baseline and required refusals |
| --- | --- |
| Metadata/profile | Genuine compatible synthetic lineage first; forged/stale assessment, authority escalation, wrong metadata-vs-physical cohort, altered settings/origin/roles and stale helper epoch refuse |
| Roster/type safety | Exact1040/1020/52 graph; reordered/missing/duplicate plans/assets, target01, wrong method/seed, callback-bearing objects and changed pool/query identities refuse |
| Claim/controller identity | Honest v2 claim plus independently pinned P3 controller; distinct substituted claim worker, nested sessions, no-op/foreign/stale lock and wrong fixture root refuse |
| Durable binding | Positive complete acyclic graph; omitted binding, swapped inner/outer attestations, malformed/extra fields, changed bytes, same-byte replacement, hardlink/reparse/path escape and reused workspace refuse |
| Physical verification | Real verifier contract with fabricated unit witnesses first; callback-only “proof,” missing actual revalidation, changed consumed markers and extra backend/restore entry refuse |
| Terminal/failure | Exactly one outer engineering terminal/measured0; inner double terminal, `record_cell`, measured publication and post-entry false-zero/retry refuse |
| Telemetry/recovery | Complete bounded traces and authorized observer chaining; truncation, clock/identity disagreement, observer suppression, missing external recovery pins or numerical reentry refuse |

First implement **only** a separately authorized metadata/profile and telemetry
unit with zero numerical work. Do not implement a runnable P3 transaction simply
because this design describes one. Before an executable successor, complete the
[timing design](cho51_p3_telemetry_design_20261027.md), qualify observational
instrumentation in new sources and separately admit a timing diagnostic of the
existing numerical contract. A diagnostic is not already authorized here.

New controller orchestration, actual numerical integration and read-only recovery
then need their own named source review, focused nonnumerical tests, distinct
admission/unused attempt, exact limits and complete actual closeout. A split
metadata test suite may be proposed if needed; never split one numerical episode
to evade its cap. Old133/65/63 test receipts do not qualify the new composition.

## 9. Resource authority and hard holds

No old4GiB startup allowance carries into this phase. A future phase defaults to
startup10GiB / active4GiB / disk20GiB unless the owner explicitly supplies a
fresh applicable amendment. Preserve600s native work, existing5s cleanup policy,
4096MiB process/5120MiB Job, CPU/Torch1/1, hidden GPUs and two startup samples
for any subsequently proposed matching envelope; independently supervised
external stdlib closeout is at most300s inclusive of actual caller completion,
final writes, EOF/reap and full release. A new scope/grant must state its exact
bounds, reserve and window; none is allocated now.

Honor all genuine pause paths under
`D:/Aenv/pro2/WORK/resume-{20261007,20261012,20261013,20261015,20261025}-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json`.
An absent pause is not peer release. Do not kill shared processes, clear caches,
reuse consumed grants, rearm the obsolete watcher or infer a new30-hour window.

This design does not qualify unchanged canonical production parent/worker or
single-root factories, current real-data execution, the other three method
chains, future runtime/device, the1,020-cell study or predictive performance.
Gate A keeps its exact narrow retrospective acceptance; its stronger numerical
claim remains unestablished. Targets02–52/source52, zero original-case retries,
unresolved checkpoint overlap and the unsigned final freeze are unchanged.

**Design completion** means the interfaces, selected identity model, acyclic
proof graph, safe terminal owner, failure/recovery boundaries and timing gates
have been statically reviewed. It means neither implementation nor execution
is complete. See the [design review](cho51_p3_adapter_review_20261027.md).
