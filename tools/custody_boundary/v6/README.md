# Offline custody evidence intake v6

This engineering package turns the accepted provider observations into an
explicit negative custody assessment and a candidate disposition under the
existing v1 contract. Run only under [PROTOCOL.md](PROTOCOL.md).

The fixed plan pins nine inputs: the three original004 failure records, v4 raw
capture, v5 decoded capture, independent provider actual review, Root adoption,
current policy and the immutable disposition schema. Current local bytes and
cross-record consistency are checked. Missing, contradictory or altered evidence
cannot yield an eligible boundary. This implementation has no positive path.

assessor.py exposes pure bounded byte-map checks and a negative disposition
builder. It does not authenticate labels, authors, a historical host or a restart.
The saved observations establish four supported native-template matches and two
unsupported classic payloads; Security query access was denied. These are
insufficient to bind the failed operation to an authenticated execution host.

The actual child retains all nine input file identities during assessment,
rechecks them before closing, and validates its candidate against the exact
frozen disposition schema. Root adoption is still pending in the child's
immutable payload. A different actual-result reviewer must accept the bounded
operation before Root issues a separate disposition with a fresh timestamp/UUID.
The Root disposition records UNRESOLVED and current_boundary=null. It is not
bootstrap admission or historical cleanup.

The source reviewer and result reviewer are different. Prior v1-v5 sources,
failed attempts and accepted records stay unchanged. Tests are nonnumerical;
no provider query, privilege change, system restart, model, native preparation,
old launcher or scientific workload is part of either fixed mode.

The six missing-evidence reasons remain separate: historical host association,
provider coverage, restart kind, clock order, persisted-domain exclusion and
incomplete raw observations. Removing a supported row, altering a hash or review
join, upgrading a false authority flag, or substituting another reviewed packet
must not silently become a qualified current boundary. An actual future evidence
provider or different execution path needs a separately reviewed contract.
