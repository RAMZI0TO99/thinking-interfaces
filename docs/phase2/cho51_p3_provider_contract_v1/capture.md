# Complete capture and fixed-slot feasibility

## Preserve original contents and ordering

Existing caller/stdout.raw and caller/stderr.raw retain exact original stream bytes, each<=1048576. Stream byte identity alone does not preserve actual chunk boundaries, observed cross-stream merge order, EOF/error, cancellation, pipe ownership or complete tool return. Do not infer a total execution order from stdout/stderr timestamps: distinguish per-stream byte order, original observer's read/merge order and any unavailable cross-thread causality.

The original capture contract requires, for each source: owner/retained handle identity, operation/clock domain, ordered chunk source/ordinal/offset/length and error status, exact content range, complete EOF observation or explicit incomplete termination, observed merge index, and the retained original raw tool/external response. A zero-byte source still requires original EOF/error evidence. Read coalescing or replay cannot silently replace original chunk/merge structure.

A capture projection C in packing.json only summarizes independently referenced raw slots and a complete capture-ledger reference. Exact per-source lengths and raw pins can be checked on supplied bytes; eof booleans do not prove native EOF. The actual ledger and native witnesses remain compulsory and their complete packing is OPEN. Arbitrarily many small reads are not bounded by a total byte cap when zero-length/status/transport events are possible. Even positive one-byte reads may yield populations far exceeding a small journal.

## Frozen capture behavior is not a free binary slot

SC1 publisher.py encodes canonical ASCII JSON plus LF. Its envelope contains body, schema, operation, publisher and false runtime/qualification/P/scientific admission flags. publish_record puts text inside body: structured text is escaped again. publish_capture instead stores the complete original response text chunks (1..64) and complete external text, pre-encoding both envelopes before either create. Failure of the second create preserves the first and consumes the transaction.

The raw_tool_return cap1048576 and external_return cap65536 constrain the **whole encoded envelope**, not that much raw text plus metadata. For a1MiB text of control characters, JSON payload alone can be6291456 bytes, before quotes, chunk lists or envelope. Two such source streams could expand to12582912, but they are distinct from the raw tool return and cannot be substituted for it. Even1MiB printable raw tool text leaves no room for positive envelope overhead in the1MiB role. Base64 expands arbitrary binary by roughly4/3; compression gives no universal fit. No truncation, omitted error or hash-only substitution establishes complete capture.

A future transport may have a reviewed finite exact return grammar with bounded complete contents, source chunks and status routes. Such a grammar must be established from the actual provider/transport, including cancellation, native errors and framing. It is not a permission to reduce required capture or silently impose a smaller tolerated original failure domain. Any narrowed domain needs an explicit source scope decision, preserved obligations outside it and a separate admission; full-profile acceptance still requires all original controls.

There is currently no dedicated raw binary tool-return slot. Existing stdout/stderr slots have different owners and contents; the16 fixed closeout roles cannot be pooled, swapped or reused. A reference-based alternative is only a design option until exact retained contents, provenance, source/merge/chunk/EOF/cancel populations, ownership and total encoded size are proved in existing roles.

## What PC1 packing does establish

packing.json defines three closed summary projections B/I/C, each<=8192 canonical ASCII JSON bytes including LF, and their existing caller-role assignments. It uses a deliberately conservative one-extra-JSON-escape bound of6 times the entire inner bytes. This bound includes only summary representation; native ledger populations, actor-map, resource samples and original raw returns remain separately open.

- caller/guard-closure.json reserves up to2*8192*6=98304 bytes for serialized B/I projections and32768 for its remaining proposed envelope/schema fields, totaling131072.
- caller/return.json reserves8192*6=49152 for C and16384 for its remaining proposed envelope/schema fields, totaling65536.

These budgets are conditional on **exactly one additional escaping layer** and a reviewed future wrapper respecting both sub-budgets. Unescaped structured bodies could be smaller; another escaping layer needs a new bound. The rest is not an unspecified free area into which full logs may be placed. Existing mandatory guard/return fields must fit their remainder without omission, under a complete closed successor schema; that has not been established. These are reservations for future successor adoption, not edits to frozen schemas or authorization to emit PC1 inside current runtime reports.

All33 original report slots, capacities, owners and partitions are copied exactly. No extra projection file is introduced at runtime. PC1 design files are source artifacts, not operation report reservations. Input-manifest stores any future independently adopted actor-map under its existing4MiB cap. Its full source/runtime population and remaining space must be proved. Caller journal already has duties and its128KiB is not an extra capacity for arbitrary complete ingress/sample/capture records.

Exact admission checks ultimately require the full encoded role envelope<=its cap, sum of all original writes/files within their own partitions, partial/temp/failed writes charged, process/Job peak allocation within limits, and original timing including encoding/verification and independent confirmation. Raw input caps, our summary arithmetic or a fitting normal example cannot establish these conditions.

## Independent confirmations and finite endpoint

SC1 reserves<=8192 encoded bytes for each independent confirmation. The source_review confirmation is inside contract_adoption (16384 total) and actual_review confirmation inside root_disposition (131072 total). The separately encoded remainder must fit destination cap-8192 and the complete destination envelope must also fit. Review text cannot be arbitrarily placed in a reserve; exact expected postpublication pin and reviewer identity remain required.

The capture and census endpoint must account for all actual writes through the original finite boundary, including publication, verification and failure paths. A report can list its own fixed role/reservation but cannot contain its own final digest or prove its own later writer termination. The final externally observed closure/return and16-slot publication dependency graph remains unimplemented. It cannot be solved with an extra report, recursive confirmations or a paused human-review interval.

## Feasibility decision

**Summary reservation arithmetic is established for the stated two nesting conditions. Complete original evidence packing and whole-operation feasibility are NOT_ESTABLISHED.** Universal inline raw-tool-return packing is infeasible for the explicit permitted-size counterexamples above; this is not a proof that every possible finite successor is infeasible.

Original ingress-to-model mapping, full sample schedule/population, full capture chunk/merge/EOF/transport ledger, actual actor-map and guard/return wrapper fields, final publication/closure delivery, complete memory liveness and worst-case costs/F/M remain open. Any foreseeable unknown blocks original admission. Source-only supplied projection parsing/refusal work can proceed after independent design acceptance without claiming those original obligations have been solved.