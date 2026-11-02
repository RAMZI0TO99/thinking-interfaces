# Bounded frontier continuation and phase propagation

Engineering design, 31 October 2026. Root authors this package; an independent
reviewer must accept its exact bytes before implementation. It supplements the
[resolver contract](../cho51_p3_resolver_bootstrap_contract_20261031.md) and
[local validation contract](../cho51_p3_local_validation_contract_20261029.md).
It does not admit execution or establish G2 completeness.

The accepted P2 contains 18,793 rows: 15,501 origin/node rows, 786 import edges,
1,782 import-frontier rows and 724 queued contexts. Embedded node records also
retain 1,786 unresolved binding loads and 3,972 effects. These are overlapping
categories, not additional independent nodes. All remain obligations.

P2 is not a resumable checkpoint. Its exports and pending-member state are not
fully serialized; a later `(module, phase, via)` context is discarded once that
module is seen. Historical observations remain valid for their bounded scope,
but their queue cannot certify complete phase propagation. The successor must
reconstruct from fresh retained bytes and reconcile the old evidence explicitly.

This package contains the [state and algorithm contract](state-contract.md),
[admission and migration contract](integration-contract.md), and
[qualification scenarios](qualification.md). No source, AST, runtime, test,
candidate or scientific operation is executed by this design step.

Implementation is deliberately staged. Next is a supplied-state continuation
kernel: closed data validation, conservative context propagation, complete debt
conservation and bounded transactional snapshots. Fresh Q tests its mechanisms.
It has no source reader/parser or P entry point. A later producer integration
must reconstruct and reconcile real retained source observations, undergo source
review, fresh Q and separately admitted P. Kernel qualification alone cannot
make P2 resumable, close its frontier, or qualify current project source behavior.

Then complete decision accounting and matching Lhost capabilities must receive
independent complete-plan acceptance before separately admitted L. The 117
candidates, 34 V controls, science 0/1020 and unsigned final freeze are unchanged.
