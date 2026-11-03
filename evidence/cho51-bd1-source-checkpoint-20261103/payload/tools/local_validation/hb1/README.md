# HB1 supplied-data implementation

This package contains pure bounded frame parsing, parent-map/census conservation,
exact collection-report checks and an always-unavailable production-host interface.
It performs no file I/O, discovery, provider exchange, dispatch or admission.
The state machine is explicitly MODEL_ONLY. Every parsed or checked result is
unauthenticated; no SC1 positive projection exists.

The [implementation contract](../../../docs/phase2/cho51_p3_hb1_implementation_contract_20261102.md)
specifies the exact source-only scope. The accepted
[HB1 design](../../../docs/phase2/cho51_p3_host_binding_v1/README.md) is unchanged.
SC1, LP19/LQ19/lplan16 and all earlier sources remain frozen.

The literal roster preserves all580 existing method identities and source pins.
All new HB method identities/pins are added before source freeze. Supplied-report
verification is neither executed unittest collection nor test acceptance.
The120 new methods are written but unexecuted. No test command or reusable
launcher is supplied: a reviewed finite runner and fresh admission remain required.

Production binding, original provider witnesses, native cancellation/custody,
durable cross-session claims, complete census attribution, asynchronous review
lifecycle and capture/complete-Q feasibility remain unresolved. P is disabled.
