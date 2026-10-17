# Fresh linear numerical worker, version 1

This candidate performs one fresh engineering restore, support update and query
inside a real canonical `CaseRecorder.case_session` identity lock. It owns only
the Cho2017 / subject_02 / labram_linear / five-shot / seed11 / repetition1 plan.
The unchanged scientific worker, `record_cell`, measured-cell verification,
1,020-case execution, scientific admission and owner final freeze remain pending.

`numerical_worker.py` imports the frozen version3 metadata worker as `W` and
reuses its typed adopted route, complete1,040/original and1,020/adopted plan checks,
52 catalogs/assets, reconstructed route contract, role-bound physical origin
reader and canonical recorder. No historical implementation or proof is edited.

The new `NumericalWorkerRequest.historical_binding` is an exact frozen
`W.WorkerRequest`. Its zero current counters describe that historical metadata
binding. They are not fresh observed numerical results. The new separately
versioned request carries an explicit expected numerical budget: source updates0,
restore1, support update1, gradient update1, target inference1, query predictions2,
model constructions1 and measured cells0. Expected permissions and observed
counts are recorded separately. Historical source5,253 updates and prior target
support1/restore1/query1 remain history, including its wrong0/2 predictions.

`run_worker_case(recorder, plan, *, context, route, workspace,
origin_contract_path, origin_contract_file_sha256, backend, verifier)` validates
the origin and actual route before a claim. Under the identity lock it creates a
fresh distinct worker claim, writes a durable request once, calls the backend
once, calls the read-only verifier twice with intervening physical stability
checks, writes a durable parent attestation, checks stability again and publishes
only an engineering success. Every callback remains inside the real lock.
No success is published without independently revalidating physical evidence,
even when a supplied verifier returns an apparently valid typed object.

The backend API is `(request, request_path, request_sha256)`. It writes exactly
the current request-bound `restore-witness.json`, `target-witness.json` and
`current-execution.json` under the unused workspace. The opaque result is the
execution file SHA-256. The verifier API is `(request, opaque)` and calls
`verify_current_execution`. Recovery passes an existing `VerifiedNumericalProof`
instead of the opaque SHA and uses the same read-only verifier.

Both numerical witnesses contain `current_worker_binding`, produced by
`build_current_binding(request)`: fresh request SHA, claim SHA, independent pins
SHA and absolute workspace. The physical execution file is a canonical
`engineering_smoke` envelope with schema
`cho51_linear_numerical_execution_v1`. It binds those same fields, physical
hashes and byte sizes for both witnesses, their exact embedded copies, observed
runtime calls, expected budget, current counter ledger, input audit before/after,
distinct current/historical source contexts and engineering-only flags. A prior
valid numerical witness cannot satisfy a new claim/request binding.

The independent metadata verifier requires observed state loads2, safetensors
loads2, optimizer initializations1, SGD steps1, tensor backward1, autograd
backward1 and positive model-module construction observations. It checks the
ledger against the exact admitted numerical budget and both unchanged213-file,
734,579,463-byte original-input audits. Native qualification supplies the actual
runtime instrumentation and original-byte audit; JSON counter assertions alone
do not qualify those observations. The current execution proof has
`native_closeout_status="pending_external_post_job"`. This process cannot attest
that its own native Job has exited or closed. Independent post-Job closeout is
required before accepting the complete engineering phase.

The target witness remains the canonical target candidate's numerical output,
with the new current worker binding added. Its source tensor map must exactly
match the authenticated historical selected-source tensor map and all223 names.
Before/source maps match; exactly the two head tensors change and the other221
backbone/buffer tensors remain unchanged. The finite402-parameter head mask,
gradient hashes/norms, one finite loss, one adaptation/backward/SGD/query observer
call, eval/inference policy, excluded query/unused rows and disjoint storage
flags are verified. `adapted_state_sha256` is an authenticated fresh raw-tensor
observer result. It cannot be independently reconstructed from per-tensor
digests. Deterministic fresh execution may legitimately reproduce an older
adapted digest; freshness derives from the newly bound execution and runtime
observations, not a requirement that hashes differ.

Fresh finite query logits are independently reduced with Python argmax
(class0 wins ties), a2x2 confusion matrix and exact `Fraction` balanced accuracy
against the route-derived two query labels. A fresh result can be correct or
wrong and is recorded honestly. There is no accuracy acceptance threshold and
no forced match to the prior wrong predictions. The frozen metadata worker's
historical hardcoded0/2 validator is used only for historical origin verification.

The frozen worker's AST-derived private settings class remains metadata-only.
Fresh numerical operations use the target candidate's actual canonical imported
settings/model/adapter classes inside the admitted native guard. This candidate
does not claim that the private metadata class has canonical numerical type
identity, or that an unchanged single-root factory is qualified.

A failure after the backend starts records `incomplete_unknown` and null
observed counts, because numerical work may already have occurred. It consumes
the attempt and cannot trigger a numerical retry. A pre-backend failure may
truthfully record no numerical work. A durable attestation interruption raises
`RecoveryRequired` and preserves evidence. `recover_worker_case` requires
external request/attestation SHA pins, revalidates origin/current physical
witnesses and claim under the same real lock, and replays only an existing
engineering intent. It has no backend parameter and cannot invent a missing
intent, restore, adapt or infer again.

`test_numerical_worker.py` contains17 test functions /38 parameterized metadata
cases using fabricated
tiny origin assets and fabricated current numerical witnesses. Every negative
mutation first passes a valid physical proof through the independent verifier.
They cover real lock ownership, engineering1/measured0, honest arbitrary
accuracy, replay bindings, false counters, foreign223-key source maps, backbone
drift, nonfinite/false metrics, runtime observer mismatch, proof/context drift,
partial execution failure and externally pinned read-only recovery. These tests
do not execute numerical operations. They are intended to run only in the
separately reviewed native Job, followed once by the actual numerical backend.
Source parsing is preparation; it is not runtime qualification.
