# Startup diagnostic implementation and accepted observation

31 October 2026. Engineering only. The bounded startup diagnostic is implemented,
independently source-reviewed, qualified under fresh Q and independently accepted
after a separately admitted observation. The diagnostic prerequisite is complete;
physical P preparation for the new L sources is still unaccepted.

## Implementation and review

The accepted [startup design](cho51_p3_startup_diagnostic_design_20261031.md)
is implemented by the twelve frozen files in
[startup2](../../tools/local_validation/startup2/diagnostic.ps1).
The controller retains exact authority/source/runtime inputs, binds native file
identities, launches one fixed probe in an owned Job and preserves its original
monotonic clock. It records ordered stage markers without treating absent
markers as successful work. A five-second boundary initiates owned cleanup;
cleanup must complete by ten seconds and the whole operation by fifteen.
Independent native resource sampling, stop controls and final input/output
verification continue through closeout.

The accepted successor uses an exact thirteen-key child environment, including
`DOTNET_MultiCoreJitNoProfileGather=1`. It permits five named evidence files and
four exact, plain cache directories whose leaf must remain empty. Unexpected
files, reparse points, aliases or changed directory types cause refusal.
This internal runtime setting is pinned to the reviewed host; it is not a
portable promise about other PowerShell/.NET releases. The
[cache successor contract](cho51_p3_startup_cache_successor_contract_20261031.md)
records the source references and limits of that conclusion.

The [SQ3 runner](../../tools/local_validation/sq3/invoke_q.ps1) runs the eight
real controller cases sequentially before the supplied-data Python suite.
It reuses the previously qualified native helper solely for memory sampling,
with an unused empty sampler Job, and keeps all actual children in separate
bounded Q Jobs. The [scalar successor contract](cho51_p3_startup_scalar_successor_contract_20261031.md)
records the typed-array correction to the single-marker checker. Sources from
each earlier executed version remain frozen.

Source acceptance is recorded separately for
[STARTUP2](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_d2/source-review.json)
and [SQ3](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/source-review.json).
A different reviewer accepted the actual results. No source review alone is
treated as executed qualification.

## Fresh Q qualification

Operation `b91d4965-594c-4bc2-951c-26ddf7de9e61` completed in
**57.591645 seconds**, with actual tool exit code zero. It passed:

- **124 supplied-data methods**, with no failures, errors or skips:
  31 foundation, 30 native-reader, 15 Q-protocol and 48 startup methods.
- Eight UTC controls, two native fault controls and eight PowerShell syntax checks.
- Eight actual controller cases: `fast`, `stall`, `empty`, `malformed`,
  `reordered`, `partial`, `review_findings` and `review_identity`.

The positive fast/stall cases were observed successfully. Four malformed-output
cases refused while retaining evidence and cleanup; both review-authority cases
refused before native authority or output creation. The runner accepted all
eight expected outcomes. Nine outer operations, six inner probe lifecycles and
three Python children closed; the unused sampler Job and its watchdog closed.
Final retained-input verification completed. The independent review verified
59 source pins, 732 Python files, 169 compiler files, 307 host files and 3,967
preserved evidence pins.

Q retained the reviewed 90/60/5-second envelope, five-second bootstrap,
65-second hard stop, 512/768 MiB caller/Job limits, 4 GiB startup/active RAM
floors, 20 GiB disk floor, thread/GPU restrictions and stop/cleanup controls.
This observed duration is not a reliability distribution or broader time-budget
qualification.

See the [actual Q review](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/actual-review.json),
[Root qualification](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/root-qualification.json)
and [Root Q acceptance](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/root-acceptance.json).

## Separately admitted D observation

Operation `c5e325ba-83b6-471c-a40b-a452dd5e9421` used fresh exact source/runtime
pins, an unused output directory and the accepted Q qualification. The
[Root admission](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_d2/root-scope_c5e325ba-83b6-471c-a40b-a452dd5e9421.json)
retained 4 GiB startup/active RAM and 20 GiB disk floors, 4096/5120 MiB
process/Job caps and the original 5/10/15-second diagnostic boundaries.

It returned `observed_diagnostic_only` in **5.6520747 seconds**, actual tool
exit code zero. The three retained markers were:

| Marker | Seconds from the original controller clock |
| --- | ---: |
| `assembly_load_begin` | 2.2613589 |
| `assembly_load_end` | 2.4033779 |
| `counter_ctor_begin` | 2.4037645 |

No constructor-end, first-sample or dispose marker was observed before the
five-second boundary. Cancellation was observed at **5.0302214 seconds**.
The marker prefix was valid; no marker protocol error occurred. The probe's
exit code and termination cause remain unobserved, as recorded; they are not
inferred from the controller's successful return.

Owned lifecycle closure, cancellation-registration join, guard completion,
original-stream closure and final input/output verification all passed. Exactly
five retained files had matching hashes and distinct native identities; the
four plain cache directories had an empty leaf and no profile file appeared.
The independent [actual D review](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_d2/actual-review-revision1.json)
and [Root disposition](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_d2/root-disposition.json)
accept only this observed scope.

The last observed marker is emitted immediately before the PDH counter
constructor. This is evidence for replacing that startup dependency in a separately reviewed P
successor. It does **not** establish the cause, original process identity or
cleanup of the earlier P2 startup failure, nor prove that this constructor can
never complete.

Closeout identified two rounded Windows FILETIME values in the convenience
`external-return` JSON derivative; the first D review repeated one of them.
Original tool stdout and the original observation retained exact values.
The [integer-fidelity addendum](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_d2/integer-fidelity-addendum.json)
and revised D review use exact decimal identities and the new lossless stdout
copy. The earlier derivative and review remain preserved, with their rounded
identity fields excluded from authority. Q3 identity records passed the same
exact-integer check. This correction changes no execution outcome or admission.

## Preserved attempts and versioned corrections

| Consumed attempt | Accepted description of the failure |
| --- | --- |
| Q1 `eb74b8f9-df4a-42a0-ae65-71b05f384d38` | Missing plain namespace parent stopped dispatch before tests/probes. Its actual failure and closed owned scope were reviewed; correction received a new attempt. |
| Q1 `6e38cc79-b78c-45db-963a-03646152540b` | 118 methods and scoped preliminary controls passed; the first fast controller refused an unexpected PowerShell profile file. That file remains retained; its original native identity and exact producer are unproven. No complete Q qualification resulted. |
| Q2 `32761684-ba2c-48f1-bea5-aa7133bacb6d` | STARTUP2 fast/stall observations closed, but the parent single-marker checker failed on a scalar `Count`. Six remaining controller cases and the Python suite did not run. SQ3 is a separately reviewed successor. |

Each failure has an independent actual review and Root disposition in its
`failure_<operation_id>` directory under
[Q1](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_q1) or
[Q2](../../runs/coordination/cho51_p3_startup_diagnostic_20261031_q2).
No consumed attempt was silently retried or overwritten. Earlier L/P sources,
receipts and unknown closures retain their original meaning.

## Next bounded step and limits

Implement and independently review a versioned P caller successor using the
qualified native memory sensor for bootstrap. Retain exact authority and
dependency coverage, original-clock deadlines, process ownership, resource
limits, stop controls, retained input checks and complete cleanup evidence.
Qualify the changed mechanism under fresh Q as applicable, then refresh the
complete P coverage and admit a new physical preparation attempt. This result
does not authorize an unchanged P2 retry or grant P execution automatically.

The [earlier L checkpoint](cho51_p3_loader_implementation_20261031.md) remains
frozen: its Q2 accepted 356 methods and five native cases, but its reviewed
20,798-file P2 proposal did not become accepted physical preparation. Complete
the finite initialization/guard/ABI/plugin plan and remaining mechanism
qualification before separately admitted L collection. The **117 candidate
tests and 34 successor controls remain unexecuted**. These 124 startup Q methods
are a different suite. Bootstrap004 remains consumed, diagnostics005 held,
006 unadmitted and historical custody UNRESOLVED. Scientific cells remain
**0/1020**, and the final freeze remains unsigned.

The pre-step current pages are preserved in the
[fourteen-file documentation archive](../history/startup_diagnostic_20261031/manifest.json).
The frozen execution policy and prior milestone bytes remain unchanged. No Git
commit/push, environment migration, MLflow installation or scientific execution
was performed in this phase. The existing MLflow evaluation entry in the
[project plan](../where%20are%20we/PROJECT_PLAN.md#8-mlflow-evaluation) is preserved.
