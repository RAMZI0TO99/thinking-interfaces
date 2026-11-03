# CM5 supplied producer model

Source-only implementation of the [accepted design](../../../docs/phase2/cho51_p3_cm5_producer_design_20261103.md).
ProducerModel accepts exact supplied operation/tables, primitive command tuples
and five fixed fault enums. It emits canonical CM4 bytes, retains sticky refusal
and settled attempt accounting, and returns immutable diagnostic/sealed mappings.
seal returns raw bytes, either a raw terminal or None, and bounded failure facts.
A post-footer refusal can coexist with all-PASS event bytes. These supplied facts
are always unauthenticated and execution_accepted=False; dispatch_runtime refuses.

The producer and independent raw verification still target frozen CM4's836/36/320.
The separate registry records the expanded876/38/360 source census, including40
unexecuted tests. It is not a current-roster collector or producer. The
[implementation contract](../../../docs/phase2/cho51_p3_cm5_implementation_contract_20261103.md)
separates actual2368-event target accounting from the hypothetical expanded2568
normal envelope. No new outer subTest callbacks are added.

The model accepts no callbacks, hooks or threads. Its documented entry points
are constructor/apply/raw_prefix/facts/seal; direct attribute mutation, subclass
replacement and mocked internals in tests are privileged supplied setups, not a
security boundary or original ingress. Counter/record boundary setups do not
claim a valid4096-record transcript. Whole output and lifecycle changes are
prepared before one serial state replacement; this is not native atomicity.

Private mocked encoder/hash/refusal/seal failures are source examples only.
Independent CM4 parsers consume returned raw bytes, never producer facts.
No original lifecycle, ingress revocation, future absence, resource feasibility,
capture, cleanup or custody is established. Original dispatcher/observer,
complete recursive failure effects and all runtime gates remain held. P disabled.
