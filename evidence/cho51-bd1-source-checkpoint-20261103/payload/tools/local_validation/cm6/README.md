# CM6 supplied context and collection

Source-only contracts: `parse_expected_context` accepts raw Q/D, independent exact
pin tuples, and an operation UUID. `verify_collection` accepts full C plus those
same arguments, verifies all rows, and then builds Q and frozen H projections.
`reconcile_prior` accepts raw Q, prior/current D, prior/current C, independent Q,
prior D and current D pins, and prior/current operation UUIDs, in that order.
It verifies both full contexts and conserves prior module pins and debt tuples.
It reports supplied facts only; it does not establish original source custody,
predecessor adoption, historical truth, execution or debt discharge. Q is the
fixed adopted Q360; added tests must be held in entirely new modules. Hashes for
source/runtime/producer sets are shape-only. Runtime dispatch always refuses.
No producer, event, terminal or original collection runtime is implemented.
