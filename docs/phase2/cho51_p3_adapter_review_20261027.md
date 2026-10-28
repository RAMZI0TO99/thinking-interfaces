# P3 adapter design: static review and handoff

27 October 2026, Asia/Riyadh. **Static engineering design review complete;
zero remaining actionable findings.** No P3 implementation, runtime validation,
profiling, fixture preparation, model episode or scientific result is claimed.

## 1. Reviewed artifacts and responsibilities

Root authored the [adapter design](cho51_p3_adapter_design_20261027.md) and
[timing/telemetry design](cho51_p3_telemetry_design_20261027.md).
Read-only subagent `/root/p3_interfaces` independently mapped the relevant source
interfaces, reviewed both drafts, reported three actionable design findings and
rechecked the corrections. The child made no file edits and returned inactive.
This is independent subagent **static engineering review**, not external
scientific sign-off or executed validation.

The final two design documents are bound by the reviewer's native byte/hash
readback:

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `cho51_p3_adapter_design_20261027.md` | 23,921 | `a4490460aa2db4548f6a8f447e33cc8eac1d9be8abdb83ef26b2dc085a99c8b5` |
| `cho51_p3_telemetry_design_20261027.md` | 16,623 | `38a092c3d3a6c067125da92e4631ec5c48e1a0f9434284587ee17687c1fffe2b` |

This report does not hash itself, future handoff heads or nonexistent runtime
outputs. The two reviewed designs describe proposed code namespaces only; no
P3 Python package, operations bundle, pins, admission or launcher was created.

## 2. Accepted design conclusions

- A call-through wrapper cannot directly add terminal-bound adapter evidence to
  the accepted parent. Its real worker owns the lock and terminal internally;
  there is no already-locked adapter hook.
- The selected new P3 controller owns one lock/transaction and a new outer
  attestation. Exactly one honest **v2 numerical-worker claim** is retained so
  the unchanged inner request/backend/verifier remain mechanically compatible.
  Controller identity and fresh source pins are explicit and separate. A
  distinctly named P3 claim would require another numerical-contract successor.
- The real canonical engineering terminal receives the **new outer adapter
  attestation digest**. No nested accepted parent session, detached sidecar-only
  acceptance, second inner terminal, `record_cell` or measured1 relabeling is
  permitted.
- Metadata cohort origin, actual synthetic input lineage, separate selected/
  baseline weights, canonical executor, isolated current recorder and historical
  producer remain separate proof domains. Equal copied configuration bytes do
  not resolve input-lineage or source-role differences.
- The acyclic intent/request/binding/proof/attestation/terminal/closeout graph
  explicitly authenticates adapter files that old v2 stability checks do not
  know about. Recovery requires external P3 pins and an existing outer intent;
  it cannot call the old recovery API or enter numerical work.
- Telemetry is bounded observation only. Exact existing observer chaining must
  be tested in a future phase; native/caller timing remains authoritative for
  final writes, process exit and full custody. No mandatory audit is moved or
  cached by this design.

## 3. Findings retained and corrected

| Finding | Correction checked by the independent reviewer |
| --- | --- |
| P2: recovery referred to an undefined P3 request artifact | The immutable preclaim `adapter-intent.json` is explicitly the P3 controller request. Recovery names external expected intent, binding and outer-attestation SHA256 values and direct paths; old inner `request.json` is distinct. |
| P2: a “post-terminal” trace tail left attestation/terminal timing without a segment | The finalization-tail buffer starts when the prefix event buffer freezes, before prefix sealing, attestation and terminal. The prefix carries a bounded open-span cut. Both immutable segments are joined externally; the final tail write/exit remain native-covered residual. |
| P2: 213-input accounting was described as including weight roles | The 213 files /734,579,463 bytes concern the preserved synthetic input fixture and five configurations. Selected/baseline weights and historical evidence are separately authenticated and excluded from that total. |

The fix recheck also confirms that the new controller needs its own actual
call-site/runtime allowlist qualification; old v7 stack acceptance is not reused.
Combined telemetry limits are512KiB/528records across both segments, including
the16KiB failure reserve. A result never has to hash a future tail recording its
own write; the external closeout binds the final tail, result and prefix.

## 4. Source basis and limited native bindings

The design was checked against the accepted boundary, factory, numerical worker,
target route/lifecycle and canonical recorder call map. Native size/SHA256 reads
below identify the source files used, not a fresh execution/runtime certificate
or a replay of all432 canonical sources and their transitive dependencies.

| Source | Bytes | SHA256 |
| --- | ---: | --- |
| `core/provenance.py` | 3,426 | `14ac6a25bdb950d4853efd7533c323d20759c3ca57a0a8676e547e4d45155758` |
| `evaluation/phase2_runner.py` | 56,443 | `ed57009e13e6040e86c22b10d98aeb71815ee19212313b63d2576be813a4d428` |
| `evaluation/phase2_cho_execution.py` | 55,925 | `d7d594489bb2c228d2998653bab9d99f9ec437f84c0946dc94d38b54feeeaf86` |
| `evaluation/phase2_cho_sweep.py` | 36,869 | `21e7f4138aeebeec06bda9d5f735fbe99896dbaf21f4f72e24b7b104186b5d7d` |
| `evaluation/phase2_cho_source_restore.py` | 30,628 | `78adfbb75704dfa5dda6a2853bb68b33e2b187cd69a14f844f00e9c0219bad78` |
| `cho51_canonical_boundary_v1/boundary.py` | 37,279 | `6101f5b722958f2d08c87f6d8d305f27c473253a8015cc4c1d79e4d3b0d212cf` |
| `cho51_provenance_numerical_worker_v2/pipeline.py` | 1,399 | `4ae4db7430f5f464ac604535ef98076c0db2eb643829a2ef7cabe11449ca4700` |
| `cho51_provenance_numerical_worker_v2/numerical_worker.py` | 33,447 | `34de6ce42ca9bdc39a7f1b03fdaa8588c1fa3324197fc4ba339240081d2291a7` |
| `cho51_provenance_numerical_worker_v2/backend.py` | 7,766 | `2e93e2b4cc300f04fe70f909e26a0c470b37fbf245606d709d309bd82b4bf76b` |
| `cho51_provenance_restore_v1/factory.py` | 32,278 | `6c508a1cbbbd5f9f4e74f983a35233a651ea9854be8f1f5f3b7e8b7a06571d78` |
| `cho51_linear_worker_route_v3/worker_route.py` | 44,500 | `141134562e22e1d94c1c0ebea05039da1b8e31a692474f182d0e32726537e94c` |
| `cho51_worker_lifecycle_v1/lifecycle.py` | 25,495 | `551f939f1babb5f04ad9adf47e363cddc9226fb89170c6c83edcc2d516777756` |
| `cho51_linear_target_route_v1/target_route.py` | 27,669 | `80468b32ef18c9efa58502077797f2e02925ba13cfbe5d83ce0b33b62c042500` |
| `v7/parent.py` | 22,416 | `9722658891387365bc29355a068a5b50b63e9707ee082c2fdf324282e5c986b2` |
| `v7/runtime.py` | 62,600 | `9a04cf96af576b1be925b965a2dc4a0ce2f19c490776692219fa59d1b82a4ada` |

Unprefixed candidate paths in this table are relative to `docs/phase2/`;
`v7/` means
`runs/coordination/cho51_provenance_numerical_worker_20261025_v7/`.
No raw, weight or runtime-binary inventory was read for this design. Existing
qualification/review receipts remain historical evidence for their own scopes.

## 5. Fresh coordination and authority disposition

A new message was sent to the previously human-authorized Pro2 chat
`01a171ad-1bad-7212-a419-d195a4a30955` at approximately12:41UTC27October,
stating exact documentation-only scope, Root+one<=2, no compute request, no old
Source006 reuse and no shared-process/cache changes. Compact app snapshots show
that chat active on its own work. **No fresh Pro2 response, Source contract,
compute release or reservation disposition has been received as of
12:59:15UTC /15:59:15Asia/Riyadh.** No peer ACK, release, host quiet or compatible
compute window is inferred. Native absence observations for five pause paths
are not a release.

The user's current request authorizes this bounded documentation/source design,
not executable preparation or a diagnostic. Future implementation validation
and execution remain held pending their own exact scope, fresh peer/resource
information, source/runtime pins, actual admission and unused attempt. If a
genuine pause/resource request arrives, honor it; old intervals never resume
automatically. No current compute lease has been consumed by this design.

## 6. Handoff and remaining action

Design complete means a source-supported architecture and prospective gates are
ready for review/use in a **separate next authorization**. It is not approval to
create a runnable transaction. Recommended next bounded scope: metadata/profile
mapping and telemetry-contract implementation with nonnumerical tests, followed
only after separate admission by the timing diagnostic. The prospective30s
headroom target remains a proposal requiring explicit adoption before that
diagnostic; it does not alter600s or retroactively fail the accepted v7 pass.

Current numerical work performed for this task: none. Accepted real-data cases
and scientific study cells added: none. Targets02–52/source52, original target01
attempts0, narrow retrospective Gate A, unresolved checkpoint exposure and the
unsigned final freeze remain unchanged. No new autonomous window or scientific
decision is signed.

Root's document consistency checks cover the new local links, UTF-8/whitespace,
reviewed design hashes and selected unchanged source bindings only. Handoff and
coordination heads are intentionally advanced with a dated design-only block;
old final-review hashes still bind their exact archived25October document
snapshots, not these later mutable heads. Accepted evidence packets, raw data,
weights and implementation bytes are preserved.
